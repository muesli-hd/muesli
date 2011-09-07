# muesli/types.py
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

# -*- coding: utf-8 -*-

import muesli

from sqlalchemy import types

class WrappedColumn(object):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return self.value

def ColumnWrapper(type):
	class Wrapped(types.TypeDecorator):
		impl = types.Unicode
		def process_bind_param(self, value, dialect):
			if isinstance(value, type):
				return value.value
			return value
		def process_result_value(self, value, dialect):
			return type(value)
	return Wrapped

class Term(WrappedColumn):
	def __html__(self):
		return self.value[0:4]+' '+('SS' if self.value[4] == '1' else 'WS') if self.value else '-'

class TutorialTime(WrappedColumn):
	weekdays = {'0': 'Mo', '1': 'Di', '2': 'Mi',\
		            '3': 'Do', '4': 'Fr', '5': 'Sa', '6': 'So'}
	def time(self):
		return self.value[2:]
	def weekday(self):
		return self.value[0]
	def __html__(self):
		return self.weekdays[self.weekday()]+' '+self.time()