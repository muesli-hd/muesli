# muesli/web/__init__.py
#
# This file is part of MUESLI.
#
# Copyright (C) 2011, Ansgar Burchard <ansgar (at) 43-1.org>
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
from pyramid.events import subscriber, NewRequest

from muesli.models import Session
from muesli.web.views import *
from muesli.web.viewsLecture import *

@subscriber(NewRequest)
def add_session_to_request(event):
  event.request.session = Session()
  def callback(request):
    request.session.rollback()
  event.request.add_finished_callback(callback)

def main(global_config=None, **settings):
  #settings.update({
  #})

  config = Configurator(settings=settings)
  config.add_static_view('static', 'muesli.web:static')

  config.add_route('overview', '/')
  config.add_route('lecture_list', '/lecture/list')
  config.add_route('lecture_view', '/lecture/view/{lecture_id}')
  config.add_route('lecture_set_preferences', '/lecture/set_preferences/{lecture_id}')
  config.scan()

  return config.make_wsgi_app()
