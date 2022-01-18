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
from markdown import markdown

from sqlalchemy import create_engine
from sqlalchemy.dialects.sqlite.base import SQLiteDialect
from sqlalchemy.events import PoolEvents

from .utils import Configuration

config = Configuration(
    os.getenv('MUESLI_PATH', '/opt/muesli4') + '/muesli.yml')

import muesli.mail

testmode = False

muesli.mail.server = config['contact'].get('mailserver_host', os.environ.get('MUESLI_MAILSERVER_HOST', '127.0.0.1'))
muesli.mail.port = config['contact'].get('mailserver_port', os.environ.get('MUESLI_MAILSERVER_PORT', 25))
DEVELOPMENT_MODE = config.get("development", os.environ.get('MUESLI_DEVMODE', False))

database_connect_str = config.get('database', {}).get('connection', None)
if database_connect_str is None:
    database_connect_str = os.environ.get('MUESLI_DB_CONNECTION_STRING', 'postgresql:///muesli')

# Read in the dataprotection and changelog so they are static to the instance
dataprotection_path = os.path.join(os.path.dirname(__file__), "web", "static", "datenschutzerklaerung.md")
with open(dataprotection_path, 'r', encoding='UTF-8') as f:
    dataprotection = f.read()
DATAPROTECTION_HTML = markdown(dataprotection)

changelog_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "CHANGELOG.md"))
with open(changelog_path, 'r', encoding='UTF-8') as f:
    changelog = f.read()
CHANGELOG_HTML = markdown(changelog)

def engine():
    db_str = '{}{}'.format(database_connect_str, 'test' if testmode else '')
    if DEVELOPMENT_MODE:
        sa_engine = create_engine(db_str, max_overflow=-1, connect_args={'connect_timeout': 30})
    else:
        sa_engine = create_engine(db_str, connect_args={'connect_timeout': 30})
    # SQLite support:
    if isinstance(sa_engine.dialect, SQLiteDialect):
        class SQLiteConnectionListener(PoolEvents):
            def connect(self, con, rec):
                con.enable_load_extension(True)
                con.load_extension('./libsqlitefunctions.so')
                con.enable_load_extension(False)

        sa_engine.pool.add_listener(SQLiteConnectionListener())
    return sa_engine
