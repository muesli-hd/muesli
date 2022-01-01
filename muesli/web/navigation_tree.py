# muesli/web/navigation_tree.py
#
# This file is part of MUESLI.
#
# Copyright (C) 2011, Ansgar Burchardt <ansgar (at) 43-1.org>
# Copyright (C) 2011, Matthias Kuemmerer <matthias (at) matthias-k.org>
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

from muesli import utils
from muesli.web.context import LectureContext, TutorialContext, ExamContext, GradingContext
from muesli.models import Tutorial, Lecture

import sqlalchemy
from sqlalchemy.orm import relationship, sessionmaker, backref, column_property, joinedload

class NavigationTree(object):
    def __init__(self, label, url="#"):
        self.children = []
        self.label = label
        self.url = url
        self.parent = None

    def prepend(self, node):
        node.parent = self
        self.children.insert(0, node)

    def append(self, node):
        node.parent = self
        self.children.append(node)

    def is_first_level(self):
        return self.parent is not None and self.parent.parent is None

    def __repr__(self, level=0):
        ret = "{}{}({})\n".format("+"*level, self.label, self.url)
        for child in self.children:
            ret += child.__repr__(level+1)
        return ret

def append_node_if_permitted(request, context, permission, route, label, matchdict, nodelist):
    if request.permissionInfo.has_permission_in_context(context, permission, matchdict):
        nodelist.append(NavigationTree(label, request.route_path(route, **matchdict)))

def owned_tutorials_in_lecture(user, lecture):
    return user.tutorials_as_tutor.filter(Tutorial.lecture_id == lecture.id).all()

def tutorial_str(tutorial):
    return "{}, {}".format(tutorial.time.__html__(), tutorial.tutor_name)

def create_navigation_tree(request):
    """Create the default navigation tree containing all current tutorials and
    lectures the user is participating in.

    Returns:
        The root of the new navigation tree
    """

    # create tree-root, this item is currently not shown
    root = NavigationTree("Übersicht", request.route_url('overview'))

    if request.user is None:
        return root

    semesterlimit = utils.getSemesterLimit()


    # add tutorials the user subscribed to
    tutorials = request.user.tutorials.options(joinedload(Tutorial.tutor), joinedload(Tutorial.lecture)).filter(Lecture.term >= semesterlimit)
    if tutorials.count() > 0:
        tutorials_node = NavigationTree("Belegte Übungsgruppen", request.route_url('overview'))
        for t in tutorials:
            t_node = NavigationTree(tutorial_str(t), request.route_url('lecture_view_points',
                    lecture_id=t.lecture.id))
            t_node.children = get_tutorial_specific_nodes(request, t)
            tutorials_node.append(t_node)
        root.append(tutorials_node)

    # add lectures for which the user is either assistant or tutor
    tutorials_as_tutor = request.user.tutorials_as_tutor.options(joinedload(Tutorial.tutor), joinedload(Tutorial.lecture)).filter(Lecture.term >= semesterlimit).all()
    lectures_as_assistant = request.user.lectures_as_assistant.filter(Lecture.term >= semesterlimit).all()
    lectures_involved_in = {t.lecture for t in tutorials_as_tutor}.union(lectures_as_assistant)
    if lectures_involved_in:
        involved_in_node = NavigationTree("Vorlesungsorganisation")
        for l in lectures_involved_in:
            lecture_node = NavigationTree(l.name,
                request.route_url('lecture_edit', lecture_id=l.id))
            lecture_node.children = get_lecture_specific_nodes(request, l)
            involved_in_node.append(lecture_node)
        root.append(involved_in_node)


    # add current lecture
    if hasattr(request.context, 'lecture') and request.context.lecture:
        lecture = request.context.lecture
        this_lecture_node = NavigationTree(lecture.name, request.route_url('lecture_view', lecture_id=lecture.id))
        this_lecture_node.children = get_lecture_specific_nodes(request, lecture)
        # Only add this top level menu field, if makes sense
        if this_lecture_node.children:
            root.append(this_lecture_node)

    return root


def get_lecture_specific_nodes(request, lecture):
    """Create navigation tree, to append to the main navigation tree containing
    the default lecture specific links

    Returns:
        A list of subtrees
    """
    nodes = []

    data = [
        ("Bearbeiten", "lecture_edit", "edit"),
        ("Anmeldeseite", "lecture_view", "view"),
        ("E-Mail an alle Übungsleiter schreiben", "lecture_email_tutors", "mail_tutors"),
        ("E-Mail an alle Studenten schreiben", "lecture_email_students", "edit"),
        ("Liste aller Teilnehmer", "lecture_export_students_html", "edit"),
        ("Student als Teilnehmer eintragen", "lecture_add_student", "edit"),
        ("Liste der abgemeldeten/entfernten Teilnehmer", "lecture_view_removed_students", "edit"),
        ("Punktzahlen exportieren", "lecture_export_totals", "edit"),
        ("Liste der Ergebnisse", "tutorial_results", "edit"),
    ]

    for label, route, permission in data:
        append_node_if_permitted(request, LectureContext, permission, route, label,
                                 {'lecture_id': lecture.id, 'tutorial_ids': ''}, nodes)

    # Add tutorials for this lecture
    tutorials_node = NavigationTree("Übungsgruppen")
    for tutorial in lecture.tutorials:
        t_node = NavigationTree(tutorial_str(tutorial), request.route_url('tutorial_view', tutorial_ids=tutorial.id))
        t_node.children = get_tutorial_specific_nodes(request, tutorial)
        if t_node.children:
            tutorials_node.children.append(t_node)
    if tutorials_node.children:
        nodes.insert(1, tutorials_node)

    # Add exams for this lecture
    exams_node = NavigationTree("Testate")
    for exam in lecture.exams:
        e_node = NavigationTree(exam.name, request.route_url('exam_edit', exam_id=exam.id))
        e_node.children = get_exam_specific_nodes(request, exam)
        if e_node.children:
            exams_node.children.append(e_node)
    if exams_node.children:
        nodes.insert(2, exams_node)

    if len(nodes) == 1 and nodes[0].label == "Anmeldeseite":
        return []

    return nodes

def get_tutorial_specific_nodes(request, tutorial):
    """Create navigation tree, to append to the main navigation tree containing
    the default tutorial specific links

    Returns:
        A list of subtrees
    """
    nodes = []

    data = [
        ("Übersicht", "tutorial_view", "viewOverview"),
        ("Ändern", "tutorial_edit", "edit"),
        ("Punkteübersicht", "tutorial_results", "viewAll"),
        ("E-Mail an Teilnehmer schreiben", "tutorial_email", "sendMail"),
        ("Status-Emails bestellen/ abbestellen", "tutorial_email_preference", "viewAll"),
    ]

    for label, route, permission in data:
        append_node_if_permitted(request, TutorialContext, permission, route, label,
                                 {'lecture_id': tutorial.lecture.id, 'tutorial_ids': tutorial.id,
                                  'tutorial_id': tutorial.id}, nodes)

    return nodes


def get_exam_specific_nodes(request, exam):
    """Create navigation tree with exam items

    Returns:
        A list of subtrees
    """
    nodes = []

    data = [
        ("Ändern", "exam_edit", "edit", True),
        ("Punkte manuell eintragen", "exam_enter_points", "view_points", False),
        ("Punkte interaktiv eintragen", "exam_enter_points_single", "view_points", False),
        ("Zulassungen/Anmeldungen/Atteste", "exam_admission", "view_points", False),
        ("Exportieren", "exam_export", "view_points", False),
        ("Statistiken", "exam_statistics", "view_points", False),
    ]

    for label, route, permission, generic in data:
        if generic:
            append_node_if_permitted(request, ExamContext, permission, route, label,
                                     {'exam_id': exam.id}, nodes)
        else:
            exam_node = NavigationTree(label)
            own_tutorials = owned_tutorials_in_lecture(request.user, exam.lecture)
            if own_tutorials:
                append_node_if_permitted(request, ExamContext, permission, route, "Eigene Übungsgruppen",
                                         {'exam_id': exam.id, 'tutorial_ids': ','.join([str(t.id) for t in own_tutorials])}, exam_node.children)
            if request.user in exam.lecture.assistants or request.user.is_admin:
                append_node_if_permitted(request, ExamContext, permission, route, "Alle Übungsgruppen",
                                         {'exam_id': exam.id,
                                          'tutorial_ids': ','.join([str(t.id) for t in exam.lecture.tutorials])},
                                         exam_node.children)
            for tutorial in exam.lecture.tutorials:
                append_node_if_permitted(request, ExamContext, permission, route, tutorial_str(tutorial),
                                         {'exam_id': exam.id,
                                          'tutorial_ids': str(tutorial.id)},
                                         exam_node.children)
            if exam_node.children:
                nodes.append(exam_node)

    return nodes