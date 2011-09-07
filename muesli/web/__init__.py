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


from pyramid import security
from pyramid.config import Configurator
from pyramid.events import subscriber, BeforeRender, NewRequest
from pyramid.renderers import get_renderer
from pyramid.authentication import SessionAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
import pyramid_beaker
import beaker.ext.sqla
import tempfile

from muesli.web.context import *
from muesli.models import *
from muesli.web.views import *
from muesli.web.viewsLecture import *
from muesli.web.viewsUser import *
from muesli import utils

@subscriber(NewRequest)
def add_session_to_request(event):
	event.request.db = Session()
	def callback(request):
		request.db.rollback()
	event.request.add_finished_callback(callback)

	user_id = security.authenticated_userid(event.request)
	if user_id is not None:
		event.request.user = event.request.db.query(User).get(user_id)
	else:
		event.request.user = None
	event.request.userInfo = utils.UserInfo(event.request.user)
	event.request.permissionInfo = utils.PermissionInfo(event.request)

@subscriber(BeforeRender)
def add_templates_to_renderer_globals(event):
	event['templates'] = lambda name: get_renderer('templates/{0}'.format(name)).implementation()

def principals_for_user(user_id, request):
	user = request.db.query(User).get(user_id)
	principals = ['user:{0}'.format(user_id)]
	if user.is_admin:
		principals.append('group:administrators')
	return principals


def main(global_config=None, **settings):
	#settings.update({
	#})

	# XXX: ugly
	import sqlalchemy as sa
	beaker.ext.sqla.sa = sa
	session_table = beaker.ext.sqla.make_cache_table(Base.metadata)
	session_table.create(bind=engine, checkfirst=True)
	settings.update({
		'beaker.session.type': 'ext:sqla',
		'beaker.session.bind': engine,
		'beaker.session.table': session_table,
		'beaker.session.data_dir': tempfile.mkdtemp(),
	})
	session_factory = pyramid_beaker.session_factory_from_settings(settings)

	authentication_policy = SessionAuthenticationPolicy(callback=principals_for_user)

	authorization_policy = ACLAuthorizationPolicy()
	config = Configurator(
		authentication_policy=authentication_policy,
		authorization_policy=authorization_policy,
		session_factory=session_factory,
		settings=settings,
		)

	config.add_static_view('static', 'muesli.web:static')

	config.add_route('start', '/start')
	config.add_route('contact', '/contact')
	config.add_route('admin', '/admin')
	config.add_route('index', '/')
	config.add_route('user_update', '/user/update')
	config.add_route('user_change_email', '/user/change_email')
	config.add_route('user_change_password', '/user/change_password')
	config.add_route('user_logout', '/user/logout')
	config.add_route('user_login', '/user/login')
	config.add_route('user_register', '/user/register')
	config.add_route('user_reset_password', '/user/reset_password')

	config.add_route('overview', '/')
	config.add_route('lecture_add', '/lecture/add')
	config.add_route('lecture_list', '/lecture/list')
	config.add_route('lecture_edit', '/lecture/edit/{lecture_id}', factory = LectureContext)
	config.add_route('lecture_email_tutors', '/lecture/email_tutors')
	config.add_route('lecture_view', '/lecture/view/{lecture_id}', factory = LectureContext)
	config.add_route('lecture_set_preferences', '/lecture/set_preferences/{lecture_id}')
	config.add_route('lecture_remove_preferences', '/lecture/remove_preferences/{lecture_id}')

	config.add_route('tutorial_view', '/tutorial/view/{tutorial_id}')
	config.add_route('tutorial_set_tutor', '/tutorial/set_tutor/{tutorial_id}')
	config.add_route('tutorial_subscribe', '/tutorial/subscribe/{tutorial_id}')
	config.add_route('tutorial_unsubscribe', '/tutorial/unsubscribe/{tutorial_id}')
	config.add_route('tutorial_occupancy_bar', '/tutorial/occupancy_bar/{count}/{max_count}/{max_count_total}')

	config.add_route('exam_view_points', '/exam/view_points/{lecture_id}')


	config.scan()

	return config.make_wsgi_app()
