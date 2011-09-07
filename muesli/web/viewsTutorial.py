# muesli/web/viewsTutorial.py
#
# This file is part of MUESLI.
#
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

from muesli import models
from muesli import utils
from muesli.web.context import *

from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest
from pyramid.url import route_url
from sqlalchemy.orm import exc
import sqlalchemy

import re
import os

import PIL.Image
import PIL.ImageDraw
import StringIO

@view_config(route_name='tutorial_occupancy_bar')
class OccupancyBar(object):
	def __init__(self, request):
		self.request = request
		self.count = int(request.matchdict['count'])
		self.max_count = int(request.matchdict['max_count'])
		self.max_count_total = int(request.matchdict['max_count_total'])
		self.width = 60
		self.height = 10
		self.color1 = (0,0,255)
		self.color2 = (140,140,255)
	def __call__(self):
		image = PIL.Image.new('RGB', (self.width,self.height),(255,255,255))
		draw = PIL.ImageDraw.Draw(image)
		draw.rectangle([(0,0),(float(self.width)*self.max_count/self.max_count_total,10)], fill=self.color2)
		draw.rectangle([(0,0),(float(self.width)*self.count/self.max_count_total,10)], fill=self.color1)
		output = StringIO.StringIO()
		image.save(output, format='PNG')
		response = Response()
		response.content_type = 'image/png'
		response.body = output.getvalue()
		output.close()
		return response

