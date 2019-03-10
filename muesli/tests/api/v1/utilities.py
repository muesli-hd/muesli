# -*- coding: utf-8 -*-
#
# muesli/tests/lectureTests.py
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

from muesli.tests.api.v1 import URL, STATIC_HEADERS


def authenticate_testapp(testapp, username, password) -> dict:
    """A function to authenticate as a user and get the valid headers for this
    user.

    Args:
        username: A string with the username to authenticate as.
        password: The password for the respective user.

    Returns:
        A dictionary with the needed headers for authorization towards the v1
        Muesli API.

        example: (<TOKEN> is the corresponding JWT token)
            {
                'Authorization': 'Bearer <TOKEN>',
                'Accept': 'application/json'
            }

    """

    response = testapp.post(
        URL+'/login',
        {"email": username, "password": password},
        STATIC_HEADERS,
    )
    token = response.json.get("token", "")
    header_content = {'Authorization': 'Bearer '+token}
    header_content.update(STATIC_HEADERS)
    return header_content
