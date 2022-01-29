# -*- coding: utf-8 -*-
#
# muesli/web/api/v1/helloEndpoint.py
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

from cornice.resource import resource, view

from muesli.web.context import NonLoginContext
from muesli.models import UserSchema
from muesli.web.api.v1 import allowed_attributes

@resource(path='/whoami', factory=NonLoginContext)
class Whoami:
    def __init__(self, request, context=None):
        del context
        self.request = request
        self.db = request.db

    @view(permission='view')
    def get(self):
        """
        ---
        get:
          security:
            - Bearer: [read]
            - Basic: [read]
          tags:
            - "v1"
          summary: "return my user"
          description: ""
          operationId: "whoami_get"
          produces:
            - "application/json"
          responses:
            200:
              description: "response for 200 code"
              schema:
                $ref: "#/definitions/User"
        """
        schema = UserSchema(only=allowed_attributes.user())
        if self.request.user:
            user = self.request.user

        else:
            user = None
        return schema.dump(user)
