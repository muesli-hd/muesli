from muesli import utils
from muesli.models import Tutorial, Lecture


import sqlalchemy
from sqlalchemy.orm import relationship, sessionmaker, backref, column_property, joinedload

Session = sessionmaker()

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
    root = NavigationTree("Übersicht", request.route_url('start'))

    if user is None:
        return root

    semesterlimit = utils.getSemesterLimit()

    tutorials_as_tutor = user.tutorials_as_tutor.options(joinedload(Tutorial.tutor), joinedload(Tutorial.lecture))
    tutorials = user.tutorials.options(joinedload(Tutorial.tutor), joinedload(Tutorial.lecture))
    lectures_as_assistant = user.lectures_as_assistant

    # add tutorials the user subsrcibed to
    tutorials = tutorials.filter(Lecture.term >= semesterlimit)
    for t in tutorials:
        lecture_node = NavigationTree(t.lecture.name, request.route_url('lecture_view', lecture_id=t.lecture.id))
        root.append(lecture_node)
        tutorial_node = NavigationTree("{} ({}, {})".format(t.lecture.name, str(t.time), t.tutor_name), request.route_url('tutorial_view', tutorial_ids=t.id))
        lecture_node.append(tutorial_node)


    # add tutorials the user tutors
    tutorials_as_tutor = tutorials_as_tutor.filter(Lecture.term >= semesterlimit)

    tutor_node = NavigationTree("Eigene Tutorials")
    for t in tutorials_as_tutor:
        tutorial_node = NavigationTree("{} ({}, {})".format(t.lecture.name, str(t.time), t.place),
            request.route_url('tutorial_view', tutorial_ids=t.id))
        tutor_node.append(tutorial_node)

    if tutor_node.children:
        root.append(tutor_node)

    # add lectures for which the user is assistant
    lectures_as_assistant = lectures_as_assistant.filter(Lecture.term >= semesterlimit)

    assistant_node = NavigationTree("Eigene Vorlesungen")
    for l in lectures_as_assistant:
        lecture_node = NavigationTree(l.name,
            request.route_url('lecture_view', lecture_id=l.id))
        assistant_node.append(lecture_node)

    if assistant_node.children:
        root.append(assistant_node)

    return root

def get_lecture_specific_nodes(request, context, lecture_id):
        nodes = []

        data = [
            ("E-Mail an alle Übungsleiter schreiben", "lecture_email_tutors"),
            ("E-Mail an alle Studenten schreiben", "lecture_email_students"),
            ("Liste aller Teilnehmer", "lecture_export_students_html"),
            ("Student als Teilnehmer eintragen", "lecture_add_student"),
            ("Liste der abgemeldeten/entfernten Teilnehmer", "lecture_view_removed_students"),
            ("Punkzahlen exportieren", "lecture_export_totals"),
        ]


        for label, route in data:
            if request.has_permission(route, context):
                nodes.append(NavigationTree(label, request.route_path(route, lecture_id=lecture_id)))

        if request.has_permission('tutorial_results', context):
            NavigationTree("Liste der Ergebnisse", request.route_path('tutorial_results', lecture_id=lecture_id, tutorial_ids='')),

        return nodes

def get_tutorial_specific_nodes(request, context, tutorial_id):
        nodes = []

        if request.has_permission('tutorial_edit', context):
            nodes.append(NavigationTree("Tutorial editieren", request.route_path('tutorial_edit', tutorial_id=tutorial_id)))



        return nodes
