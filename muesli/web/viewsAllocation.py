# -*- coding: utf-8 -*-
#
# muesli/web/views.py
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

from muesli import models, utils, types
from muesli.web.context import GeneralContext, AllocationContext, AllocationCriterionContext
from muesli.web.forms import AllocationAdd, AllocationEdit, AllocationCriterionEdit, AllocationEmailStudents
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest, HTTPFound, HTTPForbidden
from muesli.types import TutorialTime
from muesli.mail import Message, sendMail
from muesli.web.viewsExam import MatplotlibView
from muesli.global_allocation import solve_allocation_problem, build_graph, apply_allocation_graph
import sqlalchemy as sa
from pyramid.response import Response
import io
import networkx as nx
from matplotlib import pyplot


def email_registration_opened(request, students=None):
    allocation = request.context.allocation

    if students is None:
        students = allocation.students()
    bcc = [s.email for s in students if not allocation.student_preferences_unnecessary(s)]
    message = Message(subject='[MÜSLI] Abgabe von Präferenzen für "{}" ist eröffnet'.format(allocation.name),
                      sender=request.config['contact']['email'],
                      to=[request.user.email],
                      bcc=bcc,
                      body='''Liebe Studierende,
                      
                      Sie haben sich für eine der Veranstaltungen des Zuteilungsverfahrens "{}" angemeldet. Bitte geben Sie nun Ihre Terminpräferenzen an:
                      
                      https://muesli.mathi.uni-heidelberg.de{}
                      
                      Ohne Angabe von Terminpräferenzen kann Ihnen zum Zeitpunkt der Auswertung keine Übungsgruppe zugewiesen werden.
                      
                      Mit freundlichen Grüßen
                      MÜSLI-Team
                      '''.format(allocation.name, request.route_path('allocation_view', allocation_id=allocation.id)))
    try:
        sendMail(message, request)
    except:
        pass
    else:
        request.session.flash('Ankündigungsmail über eröffnete Anmeldung mit Präferenzen wurde an alle bisher registrierten Studierende verschickt.', queue='messages')
        return HTTPFound(location=request.route_url('allocation_edit', allocation_id=allocation.id))


@view_config(route_name='allocation_list', renderer='muesli.web:templates/allocation/list.pt', context=GeneralContext, permission='admin')
def list_allocations(request):
    allocations = request.db.query(models.Allocation).order_by(models.Allocation.name)
    return {'allocations': allocations}


@view_config(route_name='allocation_add', renderer='muesli.web:templates/allocation/add.pt', context=GeneralContext, permission='admin')
class Add:
    def __init__(self, request):
        self.request = request
        self.db = self.request.db
    def __call__(self):
        form = AllocationAdd(self.request)
        if self.request.method == 'POST' and form.processPostData(self.request.POST):
            allocation = models.Allocation()
            form.obj = allocation
            form.saveValues()
            self.request.db.add(allocation)
            self.request.db.commit()
            return HTTPFound(self.request.route_url('allocation_edit', allocation_id=allocation.id))
        return {'form': form}


@view_config(route_name='allocation_edit', renderer='muesli.web:templates/allocation/edit.pt',
             context=AllocationContext, permission='edit')
class Edit:
    def __init__(self, request):
        self.request = request
        self.db = self.request.db
        self.allocation_id = request.matchdict['allocation_id']
    def __call__(self):
        allocation = self.db.query(models.Allocation).get(self.allocation_id)

        previous_state = allocation.state
        form = AllocationEdit(self.request, allocation)
        if self.request.method == 'POST' and form.processPostData(self.request.POST):
            form.saveValues()
            self.request.db.commit()
        if previous_state != 'open' and allocation.state == 'open':
            email_registration_opened(self.request)

        pref_subjects_by_lecture = allocation.pref_subjects_by_lecture()
        pref_count_by_lecture = dict()
        for lecture_id in pref_subjects_by_lecture.keys():
            pref_count_by_lecture[lecture_id] = sum([pref[0] for pref in pref_subjects_by_lecture[lecture_id]])
        times = allocation.times()
        times = sorted([t for t in times], key=lambda s:s['time'].value)
        return {'allocation': allocation,
                'pref_subjects_by_lecture': pref_subjects_by_lecture,
                'pref_count_by_lecture': pref_count_by_lecture,
                'times': times,
                'categories': utils.categories,
                'form': form}

@view_config(route_name='allocation_register', context=AllocationContext, permission='view')
def register(request):
    if request.method == 'POST':
        allocation = request.context.allocation

        available_lectures = set(allocation.lectures())
        selected_lectures = set()

        for lecture in available_lectures:
            if 'lecture-{}'.format(lecture.id) in request.POST:
                models.getOrCreate(models.AllocationStudent, request.db, (allocation.id, request.user.id, lecture.id))
                selected_lectures.add(lecture)
            else:
                request.db.query(models.AllocationStudent).filter(models.AllocationStudent.allocation == allocation).filter(
                    models.AllocationStudent.student == request.user).filter(
                    models.AllocationStudent.lecture == lecture).delete()

        for criterion in allocation.criteria:
            if 'criterion-{}'.format(criterion.id) in request.POST:
                student_criterion = models.getOrCreate(models.StudentAllocationCriterion, request.db, (criterion.id, request.user.id))
                student_criterion.option = request.db.query(models.AllocationCriterionOption).get(request.POST['criterion-{}'.format(criterion.id)])

        request.db.commit()
        request.session.flash('Anmeldung gespeichert.', queue='messages')
    return HTTPFound(location=request.route_url('allocation_view', allocation_id = allocation.id))

@view_config(route_name='allocation_set_preferences', context=AllocationContext, permission='view')
def set_preferences(request):
    allocation = request.context.allocation

    row = 1
    time_prefs = []
    while 'time-{}'.format(row) in request.POST:
        time = TutorialTime(request.POST['time-{}'.format(row)])
        tp = models.getOrCreate(models.AllocationTimePreference, request.db, (allocation.id, request.user.id, time))
        tp.penalty = int(request.POST['pref-{}'.format(row)])
        time_prefs.append(tp)
        row +=  1

    valid = True
    for lecture in request.user.allocation_registered_lectures(allocation):
        # Reduce selected preferences to times available in this lecture
        selected_time_prefs_lecture = [tp for tp in time_prefs if
                                       tp.time in {avail_tp['time'] for avail_tp in allocation.times(lecture=lecture)}]
        valid &= utils.pref_selection_valid(lecture, selected_time_prefs_lecture)

    if not valid:
        request.db.rollback()
        request.session.flash(
            'Fehler: Sie haben zu wenige Zeiten ausgewählt. Probieren Sie andere oder mehr Zeiten auszuwählen.',
            queue='errors')
    else:
        request.db.commit()
        request.session.flash('Präferenzen gespeichert.', queue='messages')
    return HTTPFound(location=request.route_url('allocation_view', allocation_id = allocation.id))


@view_config(route_name='allocation_view', renderer='muesli.web:templates/allocation/view.pt', context=AllocationContext, permission='view')
def view(request):
    times = request.context.allocation.times(user=request.user)
    registration_query = request.db.query(models.AllocationStudent).filter(models.AllocationStudent.student == request.user).filter(
        models.AllocationStudent.allocation == request.context.allocation)
    lecture_registrations = [registration.lecture.id for registration in registration_query]
    selected_options_query = request.db.query(models.StudentAllocationCriterion.criterion_id,
                          models.StudentAllocationCriterion.option_id).filter(
        models.StudentAllocationCriterion.student == request.user)
    selected_options = dict()
    for criterion in selected_options_query:
        selected_options[criterion[0]] = criterion[1]

    return {'allocation': request.context.allocation,
            'selected_options': selected_options,
            'lecture_registrations': lecture_registrations,
            'times': times,
            'prefs': utils.preferences}


@view_config(route_name='allocation_remove_preferences', context=AllocationContext, permission='view')
def remove_preferences(request):
    allocation = request.context.allocation
    request.db.query(models.AllocationTimePreference).filter(
        models.AllocationTimePreference.allocation == allocation).filter(
        models.AllocationTimePreference.student == request.user).delete()
    request.db.commit()
    request.session.flash('Präferenzen wurden entfernt.', queue='messages')
    return HTTPFound(location=request.route_url('allocation_view', allocation_id = allocation.id))


@view_config(route_name='allocation_preview', renderer='muesli.web:templates/allocation/preview.pt',
             context=AllocationContext, permission='allocate')
def preview(request):
    graph = solve_allocation_problem(request)

    criteria = request.context.allocation.criteria.all()

    return {
        'criteria': criteria,
        'graph': graph
    }

@view_config(route_name='allocation_graph', context=AllocationContext, permission='edit')
class AllocationGraph(MatplotlibView):
    def __init__(self, request):
        MatplotlibView.__init__(self)
        self.request=request
        self.graph = build_graph(self.request)

    def __call__(self):
        ax = self.fig.add_subplot(111)
        nx.draw(self.graph)
        ax.set_title('Allocation graph')
        return self.createResponse()

@view_config(route_name='allocation_do_allocation', renderer='muesli.web:templates/lecture/do_allocation.pt',
             context=AllocationContext, permission='allocate')
def do_allocation(request):
    request.context.allocation.state = 'closed'
    graph = solve_allocation_problem(request)
    apply_allocation_graph(graph)
    request.session.flash('Studierende wurden tutorien zugewiesen.', queue='messages')
    return HTTPFound(location=request.referrer)

@view_config(route_name='allocation_criterion_add', renderer='muesli.web:templates/allocation/add_criterion.pt', context=AllocationContext, permission='edit')
def add_criterion(request):
    form = AllocationCriterionEdit(request)
    if request.method == 'POST' and form.processPostData(request.POST):
        criterion = models.AllocationCriterion()
        criterion.allocation = request.context.allocation
        form.obj = criterion
        form.saveValues()
        request.db.add(criterion)
        request.db.commit()
        return HTTPFound(request.route_url('allocation_criterion_edit', criterion_id=criterion.id))
    return {'form': form,
            'allocation': request.context.allocation}


@view_config(route_name='allocation_criterion_edit', renderer='muesli.web:templates/allocation/edit_criterion.pt', context=AllocationCriterionContext, permission='edit')
def edit_criterion(request):
    form = AllocationCriterionEdit(request, request.context.criterion)
    if request.method == 'POST' and form.processPostData(request.POST):
        form.saveValues()
        request.db.commit()
        form.message = "Änderungen gespeichert"
    return {'criterion': request.context.criterion,
            'form': form,
            'allocation': request.context.allocation}


@view_config(route_name='allocation_criterion_delete', context=AllocationCriterionContext, permission='edit')
def delete_criterion(request):
    if request.method == 'POST':
        request.db.delete(request.context.criterion)
        request.db.commit()
    request.session.flash('Kriterium gelöscht.', queue='messages')
    return HTTPFound(request.route_url('allocation_edit', allocation_id=request.context.allocation.id))


@view_config(route_name='allocation_criterion_add_option', context=AllocationCriterionContext, permission='edit')
def add_criterion_option(request):
    if request.method == 'POST':
        if 'option-name' in request.POST and 'option-penalty' in request.POST:
            if not request.POST['option-penalty']:
                request.POST['option-penalty'] = 0
            # get highest existing option id
            order_number = 1
            for option in request.context.criterion.options:
                if option.order_number >= order_number:
                    order_number = option.order_number + 1
            option = models.AllocationCriterionOption(
                criterion=request.context.criterion,
                name=request.POST['option-name'],
                order_number=order_number,
                penalty=int(request.POST['option-penalty'])
            )
            request.db.add(option)
            request.db.commit()
            request.session.flash("Option hinzugefügt", queue='messages')
    return HTTPFound(request.route_url('allocation_criterion_edit', criterion_id=request.context.criterion.id))


@view_config(route_name='allocation_criterion_edit_option', context=AllocationCriterionContext, permission='edit')
def set_criterion_option_penalties(request):
    if request.method == 'POST':
        if request.POST["submit"] == 'Ändern':
            for option in request.context.criterion.options:
                if request.POST['option-id'] == str(option.id):
                    option.name = request.POST['option-name']
                    option.penalty = request.POST['option-penalty']
            request.db.commit()
            request.session.flash("Option geändert", queue='messages')
        elif request.POST["submit"] == 'Löschen':
            option = request.db.query(models.AllocationCriterionOption).get(request.POST['option-id'])
            request.db.delete(option)
            request.db.commit()
            request.session.flash("Option gelöscht", queue='messages')
        else:
            pass
    return HTTPFound(request.route_url('allocation_criterion_edit', criterion_id=request.context.criterion.id))


@view_config(route_name='allocation_email_students', renderer='muesli.web:templates/allocation/email_students.pt', context=AllocationContext, permission='edit')
def email_students(request):
    allocation = request.context.allocation
    form = AllocationEmailStudents(request)
    if request.method == 'POST' and form.processPostData(request.POST):
        students = request.db.query(models.User).join(models.AllocationStudent).filter(models.AllocationStudent.allocation == allocation)
        lecture = None
        if request.POST['lecture'] != 0:
            students = students.filter(models.AllocationStudent.lecture_id == request.POST['lecture'])
            lecture = request.db.query(models.Lecture).get(request.POST['lecture'])
        bcc = [s.email for s in students]
        subject = '[{}]{} {}'.format(
            allocation.name,
            '[{}]'.format(lecture.name) if lecture is not None else '',
            form['subject']
        )
        message = Message(subject=subject,
                          sender=request.user.email,
                          to=[assistant.email for assistant in allocation.assistants()],
                          bcc=bcc,
                          body=form['body'])
        if request.POST['attachments'] not in ['', None]:
            message.attach(request.POST['attachments'].filename, data=request.POST['attachments'].file)
        try:
            sendMail(message,request)
        except:
            pass
        else:
            request.session.flash('Die Email wurde an alle Studierenden der ausgewählten Gruppe verschickt.', queue='messages')
            return HTTPFound(location=request.route_url('allocation_edit', allocation_id=allocation.id))
    return {'allocation': allocation,
            'form': form}

@view_config(route_name='allocation_histogram', context=AllocationContext, permission='edit')
class PrefHistogram(MatplotlibView):
    def __init__(self, request):
        MatplotlibView.__init__(self)
        self.request=request
        allocation = self.request.context.allocation
        time = self.request.matchdict['time']
        preferences = self.request.db.query(sa.func.count(models.AllocationTimePreference.penalty),models.AllocationTimePreference.penalty).filter(models.AllocationTimePreference.allocation_id==allocation.id) \
            .filter(models.AllocationTimePreference.time==time).group_by(models.AllocationTimePreference.penalty).order_by(models.AllocationTimePreference.penalty).all()
        prefdict = {}
        for count, penalty in preferences:
            prefdict[penalty]=count
        self.bars = [prefdict.get(p['penalty'],0) for p in utils.preferences]
        self.inds = list(range(len(utils.preferences)))
        self.xticks = [p['name'] for p in utils.preferences]
        self.label=TutorialTime(time).__html__()
    def __call__(self):
        ax = self.fig.add_subplot(111)
        if self.bars:
            ax.bar(self.inds, self.bars, color='red')
            ax.set_xticks([i+0.4 for i in self.inds])
            ax.set_xticklabels(self.xticks)
        ax.set_title(self.label)
        return self.createResponse()
