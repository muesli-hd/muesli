# -*- coding: utf-8 -*-
#
# muesli/web/viewsApi.py
#
# This file is part of MUESLI.
#
# Copyright (C) 2018, Christian Heusel <christian (at) heusel.eu>
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

from pyramid.view import view_config
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from pyramid_apispec.helpers import add_pyramid_paths
from muesli import models


@view_config(route_name='openapi_spec', renderer='json')
def api_spec(request):
    spec = APISpec(
        title='MÜSLI-API',
        version='1.0.0',
        openapi_version='3.0.0',
        plugins=[
            MarshmallowPlugin()
        ]
    )
    add_pyramid_paths(spec, 'collection_lecture', request=request)
    spec.components.schema('User', schema=models.UserSchema)
    return spec.to_dict()
