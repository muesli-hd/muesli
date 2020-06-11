# Copyright 2011, Ansgar Burchardt <ansgar@debian.org>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""
SQL helper functions for database maintainance.
"""

from muesli.exceptions import *

from sqlalchemy.sql import text

class DBUpdate:
    def __init__(self, schema_version, statements=None, callable=None):
        self.schema_version = schema_version
        self.statements = statements
        self.callable = callable
    def run(self, connection):
        print("Upgrading to schema version {0}".format(self.schema_version))
        with connection.begin():
            if self.schema_version != 1:
                old_version = connection.execute("SELECT value FROM config WHERE key = 'schema_version'").scalar()
                if int(old_version) + 1 != self.schema_version:
                    raise DatabaseError("Tried to update schema from {0} to {1}".format(old_version, self.schema_version))
            if self.statements:
                for s in self.statements:
                    connection.execute(s)
            if self.callable:
                self.callable(connection)
        connection.execute(text("UPDATE config SET value = :version WHERE key = 'schema_version'"), version=self.schema_version)

class DBUpdater:
    __shared = {'updates': {}}
    def __init__(self):
        self.__dict__ = self.__shared
    def add(self, schema_version, statements=None, callable=None):
        update = DBUpdate(schema_version, statements, callable=callable)
        self.updates[schema_version] = update
    def run(self, engine, create_database=False):
        connection = engine.connect()
        try:
            if create_database:
                old_version = 0
            else:
                old_version = int(connection.execute("SELECT value FROM config WHERE key = 'schema_version'").scalar())
            new_version = max(self.updates.keys())
            for v in range(old_version + 1, new_version + 1):
                self.updates[v].run(connection)
        finally:
            connection.close()

DBUpdater().add(1, statements=[
        """
        CREATE TABLE config (
          key TEXT PRIMARY KEY,
          value TEXT
        )""",
        """INSERT INTO config (key, value) VALUES ('schema_version', '1')""",
        ])
