# muesli/__init__.py
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

import os

from sqlalchemy import create_engine

from .utils import Configuration

config = Configuration(
    os.getenv('MUESLI_PATH', '/opt/muesli4') + '/muesli.yml')

import muesli.mail
muesli.mail.server = config['contact']['server']

databaseName = config['database']['connection']
PRODUCTION_INSTANCE = config.get("production", True)


def engine():
    if not PRODUCTION_INSTANCE:
        return create_engine(databaseName, max_overflow=-1)
    else:
        return create_engine(databaseName)


def testengine():
    if not PRODUCTION_INSTANCE:
        return create_engine(databaseName + "test", max_overflow=-1)
    else:
        return create_engine(databaseName + "test")
