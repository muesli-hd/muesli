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

from muesli.models import *
from muesli.web.views import *
from muesli.web.viewsLecture import *
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

@subscriber(BeforeRender)
def add_templates_to_renderer_globals(event):
	event['templates'] = lambda name: get_renderer('templates/{0}'.format(name)).implementation()

def main(global_config=None, **settings):
	#settings.update({
	#})

	session_factory = pyramid_beaker.session_factory_from_settings(settings)
	authentication_policy = SessionAuthenticationPolicy()
	authorization_policy = ACLAuthorizationPolicy()
	config = Configurator(
		authentication_policy=authentication_policy,
		authorization_policy=authorization_policy,
		session_factory=session_factory,
		settings=settings,
		)

	config.add_static_view('static', 'muesli.web:static')

	config.add_route('login', '/login')
	config.add_route('logout', '/logout')
	config.add_route('overview', '/')
	config.add_route('lecture_list', '/lecture/list')
	config.add_route('lecture_edit', '/lecture/edit')
	config.add_route('lecture_email_tutors', '/lecture/email_tutors')
	config.add_route('lecture_view', '/lecture/view/{lecture_id}')
	config.add_route('lecture_set_preferences', '/lecture/set_preferences/{lecture_id}')
	config.scan()

	return config.make_wsgi_app()
