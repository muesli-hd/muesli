# -*- coding: utf-8 -*-
#
# muesli/tests/api/v1/__init__.py
#
# This file is part of MUESLI.
#
# Copyright (C) 2018, Philipp Göldner  <goeldner (at) stud.uni-heidelberg.de>
#                     Christian Heusel <christian (at) heusel.eu>
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

STATIC_HEADERS = {'Accept': 'application/json'}
URL = "/api/v1"

TESTUSERS = [
    ('admin@muesli.org', 'adminpassword'),
    ('user@muesli.org', 'userpassword'),
    ('user2@muesli.org', 'user2password'),
    ('user_without_lecture@muesli.org', 'user_without_lecturepassword'),
    ('unicodeuser@muesli.org', 'üüü'),
    ('tutor@muesli.org', 'tutorpassword'),
    ('tutor2@muesli.org', 'tutor2password'),
    ('assistant@muesli.org', 'assistantpassword'),
    ('assistant2@muesli.org', 'assistant2password'),
]
