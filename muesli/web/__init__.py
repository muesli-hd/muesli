# muesli/web/__init__.py
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

from pyramid.config import Configurator
from pyramid.events import subscriber, BeforeRender, NewRequest
from pyramid.renderers import get_renderer
from pyramid.authorization import ACLHelper, Authenticated, Everyone
import jwt
from sqlalchemy.orm import sessionmaker

from muesli.web.navigation_tree import create_navigation_tree
from muesli.web.context import *
from muesli.web.views import *
from muesli.web.viewsLecture import *
from muesli.web.viewsUser import *
from muesli.web.viewsTutorial import *
from muesli.web.viewsApi import *
from muesli.web.api.v1 import *
from muesli import utils
import muesli

import time
import numbers

import weakref

from sqlalchemy import event as saevent

@subscriber(NewRequest)
def add_request_attributes(event):
    # Add database session
    event.request.db = event.request.registry.db_maker()
    def callback(request):
        request.db.rollback()
    event.request.add_finished_callback(callback)

    # Add user objects
    event.request.user = None
    if event.request.identity is not None:
        event.request.user = event.request.identity['user']
    event.request.userInfo = utils.UserInfo(event.request.user)
    event.request.permissionInfo = utils.PermissionInfo(event.request)

    # Add Javascript and CSS
    event.request.javascript = list()
    event.request.css = list()

    # Add config
    event.request.config = muesli.config

@subscriber(BeforeRender)
def add_navigation_tree_to_request(event):
    # Add navigation tree
    if event['request']:
        event['navigation_tree'] = create_navigation_tree(event['request'])

@subscriber(BeforeRender)
def add_templates_to_renderer_globals(event):
    event['templates'] = lambda name: get_renderer('templates/{0}'.format(name)).implementation()



# This class was created using the documentation on migrations pyramid 1.x authentication systems to 2.x.
# https://docs.pylonsproject.org/projects/pyramid/en/latest/whatsnew-2.0.html#upgrading-auth-20
class MuesliSecurityPolicy:
    def __init__(self, jwt_key, jwt_expiration_days):
        self.jwt_key = jwt_key
        self.jwt_expiration_days = jwt_expiration_days
        self.authenticated_via_api = False

    def jwt_identify(self, request):
        try:
            if request.authorization is None:
                return None
        except ValueError:  # Invalid Authorization header
            return None
        auth_type, token = request.authorization
        if auth_type != "Bearer" or not token:
            return None
        try:
            identity = jwt.decode(token, self.jwt_key, algorithms=['HS512'], audience=None)
            if request.db.query(models.BearerToken).get(identity["jti"]).revoked:
                return None
            else:
                self.authenticated_via_api = True
                # rename the subject id into userid
                identity['userid'] = identity.pop('sub')
                return identity
        except jwt.InvalidTokenError:
            return None

    def identity(self, request):
        identity = None
        # Check if user authenticated using Session
        if 'auth.userid' in request.session:
            identity = {'userid': request.session['auth.userid']}
        # Maybe the user authenticated using JWT. Now check for JWT token.
        if identity is None:
            identity = self.jwt_identify(request)
        if identity is None:
            # Avoid a database request on empty user_id requests
            return None
        identity['user'] = request.db.query(User).get(identity['userid'])
        if identity['user'] is None:
            return None

        # Set default principals
        identity['principals'] = ['user:{0}'.format(identity['user'].id)]
        if identity['user'].is_admin:
            identity['principals'].append('group:administrators')

        return identity

    def authenticated_userid(self, request):
        # defer to the identity logic to determine if the user id logged in
        # and return None if they are not
        identity = request.identity
        if identity is not None:
            return identity['userid']

    def permits(self, request, context, permission):
        # use the identity to build a list of principals, and pass them
        # to the ACLHelper to determine allowed/denied
        identity = request.identity
        principals = {Everyone}
        if identity is not None:
            principals.add(Authenticated)
            principals.add(identity['userid'])
            principals.update(identity['principals'])
        return ACLHelper().permits(context, principals, permission)

    def remember(self, request, userid, **kw):
        if not self.authenticated_via_api:
            request.session['auth.userid'] = userid
        return []

    def forget(self, request, **kw):
        if not self.authenticated_via_api:
            if 'auth.userid' in request.session:
                del request.session['auth.userid']
        return []

def populate_config(config):
    config.set_security_policy(
        MuesliSecurityPolicy(muesli.config["api"]["JWT_SECRET_TOKEN"], muesli.config["api"]["KEY_EXPIRATION"]))

    config.add_static_view('static', 'muesli.web:static')

    config.add_route('start', '/start', factory = GeneralContext)
    config.add_route('overview', '/overview', factory = GeneralContext)
    config.add_route('contact', '/contact')
    config.add_route('changelog', '/changelog')
    config.add_route('admin', '/admin', factory = GeneralContext)
    config.add_route('test_exceptions', 'test_exception', factory=GeneralContext)
    config.add_route('index', '/')
    config.add_route('email_users', '/email_users', factory = GeneralContext)
    config.add_route('email_all_users','/email_all_users',factory = GeneralContext)

    config.add_route('user_update', '/user/update', factory = GeneralContext)
    config.add_route('user_check', '/user/check', factory = GeneralContext)
    config.add_route('user_change_email', '/user/change_email', factory = GeneralContext)
    config.add_route('user_change_password', '/user/change_password', factory = GeneralContext)
    config.add_route('user_logout', '/user/logout')
    config.add_route('user_login', '/user/login')
    config.add_route('user_list', '/user/list', factory = GeneralContext)
    config.add_route('user_edit', '/user/edit/{user_id}', factory = UserContext)
    config.add_route('user_delete', '/user/delete/{user_id}', factory = UserContext)
    config.add_route('user_delete_gdpr', '/user/delete_gdpr/{user_id}', factory = UserContext)
    config.add_route('user_delete_unconfirmed', '/user/delete_unconfirmed', factory = GeneralContext)
    config.add_route('user_doublets', '/user/doublets', factory = GeneralContext)
    config.add_route('user_resend_confirmation_mail', '/user/resend_confirmation_mail/{user_id}', factory = UserContext)
    config.add_route('user_list_subjects', '/user/list_subjects', factory = GeneralContext)
    config.add_route('user_list_subjects_by_term', '/user/list_subjects_by_term', factory = GeneralContext)
    config.add_route('user_register', '/user/register', factory=GeneralContext)
    config.add_route('user_register_other', '/user/register_other', factory=GeneralContext)
    config.add_route('user_wait_for_confirmation', '/user/wait_for_confirmation', factory=GeneralContext)
    config.add_route('user_change_email_wait_for_confirmation', '/user/change_email_wait_for_confirmation', factory=GeneralContext)
    config.add_route('user_confirm', '/user/confirm/{confirmation}', factory=ConfirmationContext)
    config.add_route('user_confirm_email', '/user/confirm_email/{confirmation}', factory=ConfirmationContext)
    config.add_route('user_reset_password', '/user/reset_password', factory=GeneralContext)
    config.add_route('user_reset_password2', '/user/reset_password2', factory=GeneralContext)
    config.add_route('user_reset_password3', '/user/reset_password3/{confirmation}', factory=ConfirmationContext)

    config.add_route('user_api_keys', '/user/api_keys', factory=GeneralContext)
    config.add_route('remove_api_key', '/user/remove_api_key/{key_id}',factory=GeneralContext)

    config.add_route('user_ajax_complete', '/user/ajax_complete/{lecture_id}/{tutorial_ids:[^/]*}', factory = TutorialContext)
    config.add_route('lecture_add', '/lecture/add', factory = GeneralContext)
    config.add_route('lecture_list', '/lecture/list', factory = GeneralContext)
    config.add_route('lecture_edit', '/lecture/edit/{lecture_id}', factory = LectureContext)
    config.add_route('lecture_delete', '/lecture/delete/{lecture_id}', factory = LectureContext)
    config.add_route('lecture_change_assistants', '/lecture/change_assistants/{lecture_id}', factory = LectureContext)
    config.add_route('lecture_preferences', '/lecture/preferences/{lecture_id}', factory = LectureContext)
    config.add_route('lecture_prefhistogram', '/lecture/prefhistogram/{lecture_id}/{time}', factory = LectureContext)
    config.add_route('lecture_remove_tutor', '/lecture/remove_tutor/{lecture_id}/{tutor_id}', factory = LectureContext)
    config.add_route('lecture_add_tutor', '/lecture/add_tutor/{lecture_id}', factory = LectureContext)
    config.add_route('lecture_do_allocation', '/lecture/do_allocation/{lecture_id}', factory = LectureContext)
    config.add_route('lecture_remove_allocation', '/lecture/remove_allocation/{lecture_id}', factory = LectureContext)
    config.add_route('lecture_email_students', '/lecture/email_students/{lecture_id}', factory = LectureContext)
    config.add_route('lecture_email_tutors', '/lecture/email_tutors/{lecture_id}', factory = LectureContext)
    config.add_route('lecture_view', '/lecture/view/{lecture_id}', factory = LectureContext)
    config.add_route('lecture_view_removed_students', '/lecture/view_removed_students/{lecture_id}', factory = LectureContext)
    config.add_route('lecture_set_preferences', '/lecture/set_preferences/{lecture_id}', factory=LectureContext)
    config.add_route('lecture_remove_preferences', '/lecture/remove_preferences/{lecture_id}', factory=LectureContext)
    config.add_route('lecture_add_exam', '/lecture/add_exam/{lecture_id}', factory = LectureContext)
    config.add_route('lecture_add_grading', '/lecture/add_grading/{lecture_id}', factory = LectureContext)
    config.add_route('lecture_add_student', '/lecture/add_student/{lecture_id}', factory = LectureContext)
    config.add_route('lecture_switch_students', '/lecture/switch_students/{lecture_id}', factory = LectureContext)
    config.add_route('lecture_export_students_html', '/lecture/export_students_html/{lecture_id}', factory = LectureContext)
    config.add_route('lecture_export_totals', '/lecture/export_totals/{lecture_id}', factory = LectureContext)
    config.add_route('lecture_export_yaml', '/lecture/export_yaml', factory = GeneralContext)
    config.add_route('lecture_export_yaml_details','/lecture/export_yaml_details',factory = GeneralContext) #Canh added
    config.add_route('lecture_export_yaml_emails', '/lecture/export_yaml_emails', factory = GeneralContext)
    config.add_route('lecture_export_excel','/lecture/export_excel/downloadDetailTutorials.xlsx',factory = GeneralContext)

    config.add_route('lecture_view_points', '/lecture/view_points/{lecture_id}', factory = LectureContext)


    config.add_route('tutorial_add', '/tutorial/add/{lecture_id}', factory=LectureContext)
    config.add_route('tutorial_duplicate', '/tutorial/duplicate/{lecture_id}/{tutorial_id}', factory=LectureContext)
    config.add_route('tutorial_delete', '/tutorial/delete/{tutorial_ids}', factory=TutorialContext)
    config.add_route('tutorial_view', '/tutorial/view/{tutorial_ids}', factory = TutorialContext)
    config.add_route('tutorial_results', '/tutorial/results/{lecture_id}/{tutorial_ids:[^/]*}', factory = TutorialContext)
    config.add_route('tutorial_email', '/tutorial/email/{tutorial_ids}', factory = TutorialContext)
    config.add_route('tutorial_email_preference', '/tutorial/email_preference/{tutorial_ids}', factory = TutorialContext)
    config.add_route('tutorial_resign_as_tutor', '/tutorial/resign_as_tutor/{tutorial_ids}', factory = TutorialContext)
    config.add_route('tutorial_assign_student', '/tutorial/assign_student', factory = AssignStudentContext)


    config.add_route('tutorial_edit', '/tutorial/edit/{tutorial_id}', factory=TutorialContext)
    config.add_route('tutorial_set_tutor', '/tutorial/set_tutor/{tutorial_id}')
    config.add_route('tutorial_take', '/tutorial/take/{tutorial_id}', factory=TutorialContext)
    config.add_route('tutorial_remove_student', '/tutorial/remove_student/{tutorial_ids}/{student_id}', factory=TutorialContext)
    config.add_route('tutorial_subscribe', '/tutorial/subscribe/{tutorial_id}', factory=TutorialContext)
    config.add_route('tutorial_unsubscribe', '/tutorial/unsubscribe/{tutorial_id}', factory=TutorialContext)
    config.add_route('tutorial_ajax_get_tutorial', '/tutorial/ajax_get_tutorial/{lecture_id}', factory=LectureContext)

    config.add_route('exam_auto_admit', '/exam/auto_admit/{exam_id}', factory = ExamContext)
    config.add_route('exam_interactive_admission', '/exam/interactive_admission/{exam_id}', factory = ExamContext)
    config.add_route('exam_add_or_edit_exercise', '/exam/add_or_edit_exercise/{exam_id}/{exercise_id:[^/]*}', factory=ExamContext)
    config.add_route('exam_delete_exercise', '/exam/delete_exercise/{exam_id}/{exercise_id}', factory=ExamContext)
    config.add_route('exam_edit', '/exam/edit/{exam_id}', factory=ExamContext)
    config.add_route('exam_delete', '/exam/delete/{exam_id}', factory=ExamContext)
    config.add_route('exam_admission', '/exam/admission/{exam_id}/{tutorial_ids:[^/]*}', factory=ExamContext)
    config.add_route('exam_statistics', '/exam/statistics/{exam_id}/{tutorial_ids:[^/]*}', factory=ExamContext)
    config.add_route('exam_statistics_bar', '/exam/statistics_bar/{max}/{lecture_points}/{tutorial_points:[^/]*}')
    config.add_route('exam_histogram_for_exercise', '/exam/histogram_for_exercise/{exercise_id}/{tutorial_ids:[^/]*}', factory=ExerciseContext)
    config.add_route('exam_histogram_for_exam', '/exam/histogram_for_exam/{exam_id}/{tutorial_ids:[^/]*}', factory=ExamContext)
    config.add_route('exam_correlation', '/exam/correlation', factory=CorrelationContext)
    config.add_route('exam_enter_points', '/exam/enter_points/{exam_id}/{tutorial_ids:[^/]*}', factory=ExamContext)
    config.add_route('exam_enter_points_raw', '/exam/enter_points_raw/{exam_id}/{tutorial_ids:[^/]*}', factory=ExamContext)
    config.add_route('exam_enter_points_single', '/exam/enter_points_single/{exam_id}/{tutorial_ids:[^/]*}', factory=ExamContext)
    config.add_route('exam_ajax_get_points', '/exam/ajax_get_points/{exam_id}/{tutorial_ids:[^/]*}', factory=ExamContext)
    config.add_route('exam_ajax_save_points', '/exam/ajax_save_points/{exam_id}/{tutorial_ids:[^/]*}', factory=ExamContext)
    config.add_route('exam_export', '/exam/export/{exam_id}/{tutorial_ids:[^/]*}', factory = ExamContext)

    config.add_route('grading_edit', '/grading/edit/{grading_id}', factory=GradingContext)
    config.add_route('grading_export', '/grading/export/{grading_id}.xlsx', factory=GradingContext)
    config.add_route('grading_associate_exam', '/grading/associate_exam/{grading_id}', factory=GradingContext)
    config.add_route('grading_delete_exam_association', '/grading/delete_exam_association/{grading_id}/{exam_id}', factory=GradingContext)
    config.add_route('grading_enter_grades', '/grading/enter_grades/{grading_id}', factory=GradingContext)
    config.add_route('grading_formula_histogram', '/grading/enter_grades/{grading_id}/formula_histogram', factory=GradingContext)
    config.add_route('grading_get_row', '/grading/get_row/{grading_id}', factory=GradingContext)

    # Begin: config for the API-Browser
    config.include('pyramid_apispec.views')
    config.add_route("openapi_spec", "/openapi.json")
    config.pyramid_apispec_add_explorer(spec_route_name='openapi_spec')
    # End: config for the API-Browser

    config.add_route('api_login', '/api/v1/login')
    config.include('pyramid_chameleon')
    # TODO: move the prefix addition into a seperate function for later
    # developed API's.
    config.route_prefix = 'api/v1'
    config.include('cornice')

    config.registry.engine = muesli.engine()
    config.registry.db_maker = sessionmaker(bind=config.registry.engine)

    config.scan()


def create_config(settings):
    settings.update(muesli.config['settings_override'])
    config = Configurator(settings=settings)
    populate_config(config)
    return config


def main(global_config=None, **settings):
    config = create_config(settings)
    return config.make_wsgi_app()
