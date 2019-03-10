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

from pyramid import security

import sqlalchemy
from sqlalchemy.orm import relationship, sessionmaker, backref, column_property, joinedload

class NavigationTree(object):
    def __init__(self, label, url=""):
        self.children = []
        self.label = label
        self.url = url

    def prepend(self, node):
        self.children.insert(0, node)

    def append(self, node):
        self.children.append(node)

    def __repr__(self, level=0):
        ret = "{}{}({})\n".format("+"*level, self.label, self.url)
        for child in self.children:
            ret += child.__repr__(level+1)
        return ret


def create_navigation_tree(request, user):
    """Create the default navigation tree containing all current tutorials and
    lectures the user is participating in.

    Returns:
        The root of the new navigation tree
    """
    # import inside function to prevent cyclic import
    from muesli.models import Tutorial, Lecture

    # create tree-root, this item is currently not shown
    root = NavigationTree("Übersicht", request.route_url('start'))

    if user is None:
        return root

    semesterlimit = utils.getSemesterLimit()

    tutorials_as_tutor = user.tutorials_as_tutor.options(joinedload(Tutorial.tutor), joinedload(Tutorial.lecture))
    tutorials = user.tutorials.options(joinedload(Tutorial.tutor), joinedload(Tutorial.lecture))
    lectures_as_assistant = user.lectures_as_assistant

    # add tutorials the user subsrcibed to
    tutorials = tutorials.filter(Lecture.term >= semesterlimit)
    tutorial_root_node = NavigationTree("Belegte Tutorials", request.route_url('start'))
    root.append(tutorial_root_node)
    for t in tutorials:
        tutorial_node = NavigationTree("{} ({}, {})".format(t.lecture.name,
            t.time.__html__(), t.tutor_name), request.route_url('lecture_view_points',
                lecture_id=t.lecture.id))
        tutorial_root_node.append(tutorial_node)


    # add tutorials the user tutors
    tutorials_as_tutor = tutorials_as_tutor.filter(Lecture.term >= semesterlimit)

    tutor_node = NavigationTree("Eigene Tutorials", request.route_url('start'))
    for t in tutorials_as_tutor:
        tutorial_node = NavigationTree("{} ({}, {})".format(t.lecture.name,
            t.time.__html__(), t.place),
            request.route_url('tutorial_view', tutorial_ids=t.id))
        tutor_node.append(tutorial_node)

    if tutor_node.children:
        root.append(tutor_node)

    # add lectures for which the user is assistant
    lectures_as_assistant = lectures_as_assistant.filter(Lecture.term >= semesterlimit)

    assistant_node = NavigationTree("Eigene Vorlesungen", request.route_url('start'))
    for l in lectures_as_assistant:
        lecture_node = NavigationTree(l.name,
            request.route_url('lecture_edit', lecture_id=l.id))
        assistant_node.append(lecture_node)

    if assistant_node.children:
        root.append(assistant_node)

    return root


def get_lecture_specific_nodes(request, context, lecture_id):
    """Create navigation tree, to append to the main navigation tree containing
    the default lecture specific links

    Returns:
        A list of subtrees
    """
    nodes = []

    data = [
        ("E-Mail an alle Übungsleiter schreiben", "lecture_email_tutors", "mail_tutors"),
        ("E-Mail an alle Studenten schreiben", "lecture_email_students", "edit"),
        ("Liste aller Teilnehmer", "lecture_export_students_html", "edit"),
        ("Student als Teilnehmer eintragen", "lecture_add_student", "edit"),
        ("Liste der abgemeldeten/entfernten Teilnehmer", "lecture_view_removed_students", "edit"),
        ("Punktzahlen exportieren", "lecture_export_totals", "edit"),
    ]

    for label, route, permission in data:
        if request.has_permission(permission, context):
            nodes.append(NavigationTree(label, request.route_path(route, lecture_id=lecture_id)))

    if request.has_permission('edit', context):
        NavigationTree("Liste der Ergebnisse", request.route_path('tutorial_results',
            lecture_id=lecture_id, tutorial_ids='')),

    return nodes

def get_tutorial_specific_nodes(request, context, tutorial_id, lecture_id):
    """Create navigation tree, to append to the main navigation tree containing
    the default tutorial specific links

    Returns:
        A list of subtrees
    """
    nodes = []

    if request.has_permission('edit', context):
        nodes.append(NavigationTree("Tutorial editieren",
            request.route_path('tutorial_edit', tutorial_id=tutorial_id)))

    if request.has_permission('viewAll', context):
        nodes.append(NavigationTree("Punkteübersicht",
            request.route_path('tutorial_results', lecture_id=lecture_id,
                tutorial_ids=tutorial_id)))

    if request.has_permission('sendMail', context):
        nodes.append(NavigationTree("E-Mail an Teilnehmer schreiben",
            request.route_path('tutorial_email', tutorial_ids=tutorial_id)))

    if request.has_permission('viewAll', context):
        nodes.append(NavigationTree("Status-Emails bestellen/ abbestellen",
            request.route_path('tutorial_email_preference', tutorial_ids=tutorial_id)))

    return nodes
