# -*- coding: utf-8 -*-
#
# muesli/web/viewsApi.py
#
# This file is part of MUESLI.
#
# Copyright (C) 2018, Philipp Göldner  <pgoeldner (at) stud.uni-heidelberg.de>
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

import json
from os import path, stat
from ast import literal_eval
import requests

STATIC_HEADERS = {'Accept': 'application/json'}
MUESLI_URL = "http://localhost:8080"


def authenticate(header_name="header.txt") -> dict:
    """TODO: Docstring for function.

    :arg1: TODO
    :returns: TODO

    """
    if path.isfile(header_name) and stat(header_name).st_size != 0:
        with open(header_name, 'r') as header:
            header_content = literal_eval(header.read())
            print('Read header from {}!'.format(header_name))
            return header_content
    else:
        with open(header_name, 'w') as header:
            r = requests.post(
                MUESLI_URL+'/api/v1/login',
                data={"email": "test@test.de", "password": "1234"}
            )
            token = r.json().get("token", "")
            header_content = {'Authorization': 'JWT '+token}
            header_content.update(STATIC_HEADERS)
            header.write(json.dumps(header_content))
            print('Created {}!'.format(header_name))
            return header_content


def main():
    headers = authenticate()
    endpoint = MUESLI_URL + "/api/v1/lectures/20109"
    lecture = '{"term": 20181, "name": "Irgendwas", "lecturer": "Ich auch"}'
    r = requests.put(endpoint, data=lecture, headers=headers)
    # r = requests.get(endpoint, headers=headers)
    print(r, r.text)
    # print(r.json())


if __name__ == "__main__":
    main()
