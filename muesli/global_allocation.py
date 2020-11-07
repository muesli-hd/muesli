# -*- coding: utf-8 -*-
#
# muesli/allocation.py
#
# This file is part of MUESLI.
#
# Copyright (C) 2020, Tobias Wackenhut <tobias (at) wackenhut.at>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import muesli
from muesli import utils, models
import random
#from graph_tool.all import *
import networkx as nx
from sqlalchemy import func
from sqlalchemy.orm import joinedload, contains_eager
from muesli import models as m
from muesli import utils
import math
from muesli.web import viewsTutorial

def students_matching_requirements(g, lecture, requirements):
    relevant_applicants = set()
    for student in g.graph["lecture_students"][lecture]:
        student_fulfills_requirements = True
        for criterion, min_penalty in requirements.items():
            if criterion is None:
                continue
            elif g.graph['student_criteria'][student][criterion.id] < min_penalty:
                student_fulfills_requirements = False
                break
        if student_fulfills_requirements:
            relevant_applicants.add(student)
    return relevant_applicants

def remove_lecture_student(g, lecture, student):
    g.remove_node((lecture, student))
    g.graph["lecture_students"][lecture].remove(student)
    if student in g.graph["student_lectures"]:
        g.graph["student_lectures"][student].remove(lecture)
        if not len(g.graph["student_lectures"][student]):
            del g.graph["student_lectures"][student]
            del g.graph["student_criteria"][student]
    if "student_tutorials" in g.graph and student in g.graph["student_tutorials"]:
        tutorial = g.graph["student_tutorials"][student]
        if tutorial in g.graph["tutorial_students"]:
            del g.graph["tutorial_students"][tutorial][student]
        del g.graph["student_tutorials"][student][tutorial]

def process_admission_priorities(g):
    for lecture in g.graph["lecture_students"].keys():
        avail_places = g.graph["database"].query(func.sum(m.Tutorial.max_students)) \
            .filter(m.Tutorial.lecture == lecture).filter(m.Tutorial.allocation == g.graph["allocation"]).scalar()
        processed_applicants = set()

        max_priority = max([x[0] for x in g.graph["admission_priorities"][lecture]])
        for priority in range(max_priority + 1):
            if avail_places <= 0:
                break

            requirements = dict()
            for admission_priority, criterion, min_penalty in g.graph["admission_priorities"][lecture]:
                if priority == admission_priority:
                    requirements[criterion] = min_penalty

            relevant_applicants = students_matching_requirements(g, lecture, requirements) - processed_applicants

            # Remove students not praying to lady fortuna
            student_remove_count = max(0, len(relevant_applicants) - avail_places)
            if student_remove_count > 0:
                print("Removing {} students from lecture {}".format(student_remove_count, lecture.name))
            for student in random.sample(list(relevant_applicants), student_remove_count):
                remove_lecture_student(g, lecture, student)

            processed_applicants |= relevant_applicants
            avail_places -= len(relevant_applicants)

    return g

# Build a graph containing all relevant database information
def build_graph(request):
    g = nx.DiGraph()

    # We store all problem specific information inside the graph itself.

    # The folowing node attributes exist
    # - type: one of "tutorial", "lecture_student"
    # - tutorial: Tutorial
    # - lecture : Lecture
    # - student: User
    # - criteria: dict(AllocationCategory.id, penalty)
    # - other_lectures: set(Lecture)
    # - admission_priorities: list((priority, criterion_id, min_priority))
    # - time_preferences: dict(time, penalty)

    # edge properties
    # - weight: int
    # - capacity: int
    # - contact_correction_share: int
    # - time_collision_correction_share: int

    # Some general information is stored as graph attributes
    g.graph["allocation"] = request.context.allocation
    g.graph["database"] = request.db
    g.graph["student_lectures"] = dict() # dict(User, set(Lecture))
    g.graph["lecture_students"] = dict() # dict(Lecture, set(User))
    g.graph["lecture_tutorials"] = dict() # dict(Lecture, set(Tutorial))
    g.graph["student_criteria"] = dict() # dict(User, dict(AllocationCriterion.id, AllocationCriterionOption.penalty))
    g.graph["criteria"] = request.context.allocation.criteria.all() # list(AllocationCriterion)
    g.graph["student_time_preferences"] = dict() # dict(User, dict(Time, penalty))

    # preparation steps

    # prepare a template for criteria
    allocation = request.context.allocation
    criteria = allocation.criteria.all()
    criteria_penalty_template = {criterion.id: 0 for criterion in criteria}


    # prepare dict for student -> set of lectures
    student_lecture_set = {}

    # Write lecture admission priorities to a graph attribute
    # dict(Lecture.id, list(tuple(LectureAllocationCriterion.priority, AllocationCriterion.id, LectureAllocationCriterion.min_penalty)))
    g.graph["admission_priorities"] = {}
    lectures = allocation.lectures().options(joinedload(m.Lecture.lecture_allocation_criteria))
    for lecture in lectures:
        g.graph["admission_priorities"][lecture] = []
        for lecture_criterion in lecture.lecture_allocation_criteria:
            g.graph["admission_priorities"][lecture].append((lecture_criterion.priority, lecture_criterion.criterion, lecture_criterion.min_penalty))
        # Add (100, None, 0) at last, since all students have the same priority at the end of the list
        g.graph["admission_priorities"][lecture].append((100, None, 0))


    # Now create the nodes
    g.add_node("source")
    g.add_node("target")

    # We add a ghost node to always have a solution. This can be necessary when there are not enough places in tutorials
    # available
    g.add_node("ghost")
    g.add_edge("ghost", "target", capacity=utils.ghostcapacity, weight=0)


    # tutorial vertices
    # Each tutorial gets a vertex and an edge to the target
    # weight is 0, capacity is the maximum number of students in the tutorial
    tutorials = request.db.query(m.Tutorial).filter(m.Tutorial.allocation == allocation).options(joinedload(m.Tutorial.tutorial_allocation_criteria), joinedload(m.Tutorial.lecture))
    for tutorial in tutorials:
        g.add_node(
            tutorial,
            type = "tutorial",
            tutorial = tutorial,
            criteria = criteria_penalty_template.copy()
        )
        for tutorial_criterion in tutorial.tutorial_allocation_criteria:
            g.nodes[tutorial]["criteria"][tutorial_criterion.criterion_id] = tutorial_criterion.penalty
        g.graph["lecture_tutorials"].setdefault(tutorial.lecture, set()).add(tutorial)

        # add edge to target
        g.add_edge(
            tutorial, "target",
            weight = 0,
            capacity = tutorial.max_students
        )


    # lecture student vertices
    #
    # Each student gets a vertex for each registered lecture. These "lecture student" vertices are connected to the
    # tutorials of the corresponding lecture with a calculated weight based on
    # - time preference
    # - time collisions with other tutorials
    # - contact with other students (pandemic)
    # Additionally each lecture student vertex is connected to the source with capacity 1 and weight 0.
    lecture_students = request.db.query(m.Lecture, m.User) \
        .filter(m.User.allocation_students.any(m.AllocationStudent.allocation == allocation)) \
        .filter(m.Lecture.allocation_students.any(m.AllocationStudent.student_id == m.User.id)) \
        .join(m.StudentAllocationCriterion.student, isouter=True) \
        .join(m.AllocationCriterionOption, m.AllocationCriterionOption.id == m.StudentAllocationCriterion.option_id) \
        .join(m.AllocationCriterion, m.AllocationCriterion.id == m.StudentAllocationCriterion.criterion_id) \
        .join(m.User.allocation_time_preferences, isouter=True) \
        .options(
            contains_eager(m.User.student_allocation_criteria).contains_eager(m.StudentAllocationCriterion.option),
            contains_eager(m.User.allocation_time_preferences)
        ) \

    for lecture, student in lecture_students:
        g.add_node(
            (lecture, student),
            type = "lecture_student",
            lecture = lecture,
            student = student,
        )
        g.graph["student_lectures"].setdefault(student, set()).add(lecture)
        g.graph["lecture_students"].setdefault(lecture, set()).add(student)
        if student not in g.graph["student_criteria"]:
            g.graph["student_criteria"][student] = criteria_penalty_template.copy()
            for student_criterion in student.student_allocation_criteria:
                g.graph["student_criteria"][student][student_criterion.criterion_id] = student_criterion.option.penalty
        if student not in g.graph["student_time_preferences"]:
            g.graph["student_time_preferences"][student] = {
                time_preference.time: time_preference.penalty
                for time_preference in student.allocation_time_preferences
            }

        # Edge from source
        g.add_edge(
            "source", (lecture, student),
            weight = 0,
            capacity = 1
        )

        # Edge to ghost node
        g.add_edge((lecture, student), "ghost", capacity=1, weight=utils.ghostpenalty)

        # Edge to each tutorial
        for tutorial, node_type in g.nodes(data="type"):
            if node_type == "tutorial" and tutorial.lecture == lecture:
                # We set the initial weight to the time preference penalty plus criterion bonus
                # Changes will be made during iteration
                # The default penalty for missing times is 100

                # The weight for criteria is a mean over all criterion relationships between student and tutorial
                criteria_weight = 0
                for criterion in g.graph["criteria"]:
                    student_penalty = g.graph["student_criteria"][student][criterion.id]
                    tutorial_penalty = g.nodes[tutorial]["criteria"][criterion.id]
                    if (tutorial_penalty >= 0) == (student_penalty >= 0):
                        criteria_weight = max(criteria_weight, student_penalty * tutorial_penalty / 100)
                    else:
                        criteria_weight = max(criteria_weight, (100 + student_penalty * tutorial_penalty) / 100)
                criteria_weight = int(criteria_weight)

                # The time preference is already stored inside the graph
                time_preference = g.graph["student_time_preferences"][student].get(tutorial.time, 100)
                weight_components = {
                    'time_preference': time_preference,
                    'criteria': criteria_weight
                }

                g.add_edge(
                    (lecture, student), tutorial,
                    capacity = 1,
                    weight_components = weight_components
                )

                calculate_edge_weight(g, ((lecture, student), tutorial))

    return g

def calculate_edge_weight(graph, edge):
    for component, max_influence in (('time_preference', 100), ('criteria', 90), ('contacts', 90), ('time_collision', 200)):
        # Each component is only allowed to set a score up to a certain value
        graph.edges[edge]['weight'] = max(graph.edges[edge].get('weight', 0), min(graph.edges[edge]['weight_components'].get(component, 0), max_influence))

def solve_min_cost_flow(graph):
    # Calculate demand
    demand = len([1 for _, node_type in graph.nodes(data="type") if node_type == 'lecture_student'])
    graph.nodes["source"]["demand"] = -demand
    graph.nodes["target"]["demand"] = demand

    # Solve the problem using a network simplex algorithm
    flow_cost, flow_dict = nx.network_simplex(graph)

    # Store the resulting flow in the graph
    graph.graph["student_unhappiness"] = {}
    graph.graph["tutorial_students"] = {}
    graph.graph["student_tutorials"] = {}
    for start in flow_dict.keys():
        for end in graph[start].keys():
            graph[start][end]["flow"] = flow_dict[start][end]

            # Calculate unhappiness for student (remove ghosts beforehand, since they only mean, the student has not
            # gotten a tutorial slot
            if graph.nodes[start].get('type', '') == "lecture_student" and end != "ghost":
                # Add the student to the tutorial
                lecture, student = start
                tutorial = end
                if graph[start][end]["flow"]:
                    if student not in graph.graph["student_lectures"].keys():
                        print("Student {} is not in student_lectures. Lecture: {} Tutorial {} {}".format(student.name(), lecture.name, tutorial.time, tutorial.place))
                    graph.graph["tutorial_students"].setdefault(tutorial, set()).add(student)
                    graph.graph["student_tutorials"].setdefault(student, set()).add(tutorial)

                # Calculate unhappiness
                if student not in graph.graph["student_unhappiness"]:
                    graph.graph["student_unhappiness"][student] = 0
                graph.graph["student_unhappiness"][student] += graph[start][end]["flow"] * graph[start][end]["weight"]

    graph.graph['flow_cost'] = flow_cost


def calculate_contact_weights(g):
    g.graph["student_contacts"] = dict() # dict(student, dict(Tutorial, count))
    for student in g.graph["student_tutorials"].keys():
        lecture_contacts = dict()
        for tutorial in g.graph["student_tutorials"][student]:
            lecture_contacts[tutorial.lecture] = set()

            if tutorial_online(g, tutorial):
                continue

            # Add all students to the set
            for fellow_student in g.graph["tutorial_students"][tutorial]:
                lecture_contacts[tutorial.lecture].add(fellow_student)

        current_contacts = set()
        for tutorial in g.graph["student_tutorials"][student]:
            current_contacts |= lecture_contacts[tutorial.lecture]
        g.graph['student_contacts'][student] = len(current_contacts)

        min_contact_difference = 0
        max_contact_difference = 0
        for lecture in g.graph["student_lectures"][student]:
            for tutorial in g.successors((lecture, student)):
                if tutorial != "ghost":
                    tutorial_contacts = set()
                    if tutorial in g.graph["tutorial_students"]:
                        if not tutorial_online(g, tutorial):
                            for fellow_student in g.graph["tutorial_students"][tutorial]:
                                tutorial_contacts.add(fellow_student)
                    contact_difference = len(current_contacts) - len((current_contacts - lecture_contacts[lecture]) | tutorial_contacts)

                    min_contact_difference = min(min_contact_difference, contact_difference)
                    max_contact_difference = max(max_contact_difference, contact_difference)
                    g[(lecture, student)][tutorial]['contact_difference'] = contact_difference
                    g[(lecture, student)][tutorial]['contacts'] = len((current_contacts - lecture_contacts[lecture]) | tutorial_contacts)

        for lecture in g.graph["student_lectures"][student]:
            for edge in g.out_edges((lecture, student)):
                if edge[1] != "ghost":
                    b = float(max_contact_difference)
                    a = float(min_contact_difference)
                    x = float(g.edges[edge]['contact_difference'])
                    if (b - a) > 0:
                        score = int(min(100 * ((x - a) / (b - a)), math.pow((b - a), 2)))
                    else:
                        score = 0
                    score = g.edges[edge]['contacts']
                    g.edges[edge]['weight_components']['contacts'] = score

def tutorial_online(g, tutorial):
    for criterion in g.graph["criteria"]:
        if criterion.indicates_online and g.nodes[tutorial]['criteria'][criterion.id] > 0:
            return True
    return False


def adjust_weights(graph):
    return graph

def calculate_edge_weights(g):
    for start in g.nodes():
        if g.nodes[start].get('type', '') == 'lecture_student':
            for end in g.successors(start):
                if end != "ghost":
                    calculate_edge_weight(g, (start, end))

def remove_students_with_external_allocation(g):
    for student in list(g.graph["student_criteria"].keys()).copy():
        for criterion in g.graph["criteria"]:
            if criterion.preferences_unnecessary and g.graph["student_criteria"][student][criterion.id] >= 100:
                for lecture in g.graph["student_lectures"][student].copy():
                    remove_lecture_student(g, lecture, student)

def solve_allocation_problem(request, dry_run=True):
    graph = build_graph(request)
    hacky_pre_processing(graph, dry_run)
    remove_students_with_external_allocation(graph)
    graph = process_admission_priorities(graph)
    iteration_nr = 1
    while not check_solution_okay(graph, iteration_nr):
        solve_min_cost_flow(graph)
        calculate_contact_weights(graph)
        detect_time_collisions(graph)
        calculate_edge_weights(graph)
        iteration_nr += 1

    if not dry_run:
        apply_allocation_graph(graph)

    return graph

def check_solution_okay(g, iteration_nr):
    if "time_collisions" in g.graph and g.graph["time_collisions"] == 0 and iteration_nr > 9:
        g.graph["solution_okay"] = True
        return True
    return False

def detect_time_collisions(g):
    n_collisions = 0
    for student in g.graph["student_tutorials"].keys():
        used_times = dict()
        for tutorial in g.graph["student_tutorials"][student]:
            if tutorial.time in used_times:
                # print("Detected time collision: Student: {}, Time: {}".format(student.name(), tutorial.time))
                n_collisions += 1
            used_times[tutorial.time] = tutorial

        if student not in g.graph["student_lectures"]:
            continue
        for lecture in g.graph["student_lectures"][student]:
            for tutorial in lecture.tutorials:
                if tutorial in g.nodes():
                    if tutorial.time in used_times.keys() and used_times[tutorial.time] != tutorial:
                        collision_weight = 200
                    else:
                        collision_weight = 0
                    g[(tutorial.lecture, student)][tutorial]['weight_components']['time_collision'] = collision_weight

    g.graph["time_collisions"] = n_collisions
    print("Collisions: {}".format(n_collisions))

def apply_allocation_graph(g):
    assert "solution_okay" in g.graph

    for tutorial in g.graph["tutorial_students"].keys():
        for old_student in tutorial.students:
            viewsTutorial.unsubscribe(user=old_student, tutorial=tutorial, db=g.graph["database"])

        for new_student in g.graph["tutorial_students"][tutorial]:
            viewsTutorial.subscribe(user=new_student, tutorial=tutorial, db=g.graph["database"])
    print("Zuteilung erfolgreich gespeichert")


def hacky_pre_processing(g, dry_run = True):
    # Covid 19 Allocation has special requirements
    if g.graph["allocation"].id == 1:
        # Einführung in die Praktische Informatik
        lecture = g.graph["database"].query(m.Lecture).get(1236)
        # Tutorial for students with existing programming skills
        tutorial = g.graph["database"].query(m.Tutorial).get(7279)
        criterion_id = 2

        # Empty this tutorial
        print("Emptying special IPI tutorial")
        for old_student in tutorial.students:
            if not dry_run:
                viewsTutorial.unsubscribe(user=old_student, tutorial=tutorial, db=g.graph["database"])

        special_student_counter = 0
        for student in g.graph["lecture_students"][lecture].copy():
            if g.graph["student_criteria"][student][criterion_id] == 100:
                special_student_counter += 1
                remove_lecture_student(g, lecture, student)
                if not dry_run:
                    viewsTutorial.subscribe(user=student, tutorial=tutorial, db=g.graph["database"])
        print("Adding {} students to special tutorial.".format(special_student_counter))
