# -*- coding: utf-8 -*-
#
# muesli/web/viewsApi.py
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

import re
from collections import OrderedDict

from pyramid.view import view_config
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from pyramid_apispec.helpers import add_pyramid_paths
from muesli import models
from muesli.web.api.v1 import allowed_attributes



@view_config(route_name='openapi_spec', renderer='json')
def api_spec(request):
    """ Return something.
    ---
    get:
      description: "Outputs the Open-API specification with version 2.0.0. More information can be found on https://swagger.io/docs/specification/2-0/basic-structure/"
      operationId: "lecture_get"
      tags:
      - "Open API"
      produces:
        - "application/json"
    """
    spec = APISpec(
        title='MÜSLI-API',
        version='0.0.1',
        openapi_version='2.0.0',
        securityDefinitions={
            "Bearer": {
                "type": "apiKey",
                "in": "header",
                "name": "Authorization",
                "description": "JWT Tokens"
            },
            "Basic": {
                "type": "basic",
                "description": "Die regulären Zugangsdaten zum Müsli :)"
            }
        },
        plugins=[
            MarshmallowPlugin()
        ]
    )
    # Paths for API v1
    add_pyramid_paths(spec, 'collection_lecture', request=request)
    add_pyramid_paths(spec, 'lecture', request=request)

    add_pyramid_paths(spec, 'collection_tutorial', request=request)
    add_pyramid_paths(spec, 'tutorial', request=request)

    add_pyramid_paths(spec, 'collection_exercise', request=request)
    add_pyramid_paths(spec, 'exercise', request=request)

    add_pyramid_paths(spec, 'exam', request=request)

    add_pyramid_paths(spec, 'openapi_spec', request=request)

    # Be careful how the schemes are defined:
    #
    # If one (or its member) are instantiated as object and some are as class
    # they can cause weird behavior with double definitions of schemes in the
    # spec.

    spec.components.schema('User', schema=models.UserSchema(only=allowed_attributes.user()))

    spec.components.schema('Tutorial', schema=models.TutorialSchema(only=allowed_attributes.tutorial()))
    spec.components.schema('CollectionTutorial', schema=models.TutorialSchema(only=allowed_attributes.collection_tutorial()))

    spec.components.schema('Lecture', schema=models.LectureSchema(only=allowed_attributes.lecture()))
    spec.components.schema('CollectionLecture', schema=models.LectureSchema(only=allowed_attributes.collection_lecture()))

    spec.components.schema('ExerciseStudent', schema=models.ExerciseStudentSchema)
    spec.components.schema('Exercise', schema=models.ExerciseSchema)
    openapi_json = spec.to_dict()

    return remove_regex(openapi_json)


def remove_regex(openapi_json: dict) -> dict:
    """Docstring for remove_regex.

    :openapi_json: OpenAPI-Spec with version 2.0
    :returns: cleared up Spec

    Since the following block is hard to understand:
    The function removes all the regex from the paths such as

        "/api/exercises/{exercise_id:\d+}/{user_id:(\d+)+\/?}"

    is transformed to

        "/api/exercises/{exercise_id}/{user_id}"

    It is important to note that this function does not serve a "real" need,
    the output for the UI (or other documentation) is just nicer to look at.
    """
    cleared_paths = OrderedDict({})
    for path, description in openapi_json["paths"].items():
        if ":" in path:
            path_splitted = re.split("(/{)", path)
            for substr in path_splitted:
                if ":" in substr:
                    path_splitted = [e.replace(substr,
                                               (re.sub(r':.*[^}]', "", substr))
                                               ) for e in path_splitted]
            new_path = "".join(path_splitted)
            cleared_paths[new_path] = description
        else:
            cleared_paths[path] = description
    openapi_json["paths"] = cleared_paths
    return openapi_json
