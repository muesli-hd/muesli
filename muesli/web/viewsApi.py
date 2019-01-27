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
from muesli.web.api import allowed_attributes


@view_config(route_name='openapi_spec', renderer='json')
def api_spec(request):
    """ Return something.
    ---
    get:
      description: "Outputs the Open-API specification with version 2.0.0. More information can be found on https://swagger.io/docs/specification/2-0/basic-structure/"
      tags:
      - "Open API"
    """
    spec = APISpec(
        title='MÜSLI-API',
        version='0.0.1',
        openapi_version='2.0.0',
        plugins=[
            MarshmallowPlugin()
        ]
    )
    add_pyramid_paths(spec, 'collection_lecture', request=request)
    add_pyramid_paths(spec, 'lecture', request=request)

    add_pyramid_paths(spec, 'collection_tutorial', request=request)
    add_pyramid_paths(spec, 'tutorial', request=request)

    add_pyramid_paths(spec, 'collection_exercise', request=request)
    add_pyramid_paths(spec, 'exercise', request=request)

    add_pyramid_paths(spec, 'openapi_spec', request=request)

    spec.components.schema('User', schema=models.UserSchema(only=allowed_attributes.user()))

    spec.components.schema('Lecture', schema=models.LectureSchema(only=allowed_attributes.lecture()))
    spec.components.schema('CollectionLecture', schema=models.LectureSchema(only=allowed_attributes.collection_lecture()))

    spec.components.schema('Tutorial', schema=models.TutorialSchema(only=allowed_attributes.tutorial()))
    spec.components.schema('CollectionTutorial', schema=models.TutorialSchema(only=allowed_attributes.collection_tutorial()))

    spec.components.schema('ExerciseStudent', schema=models.ExerciseStudentSchema)
    spec.components.schema('Exercise', schema=models.ExerciseSchema)
    return spec.to_dict()
