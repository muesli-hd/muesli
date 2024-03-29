# -*- coding: utf-8 -*-
#
# api_tools/header.py
#
# This file is part of MUESLI.
#
# Copyright (C) 2019, Philipp Göldner  <pgoeldner (at) stud.uni-heidelberg.de>
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
"""
This module provides tooling to authenticate ageinst the Muesli API v1
"""

import json
import logging
from os import path, stat
from ast import literal_eval
import requests
import getpass

STATIC_HEADERS = {'Accept': 'application/json'}
MUESLI_URL = "https://muesli.mathi.uni-heidelberg.de"


def authenticate(username="", password="", save=False, url=MUESLI_URL) -> dict:
    """A function to authenticate as a user and get the valid headers for this
    user.
    Args:
        username: A string with the username to authenticate as.
        password: The password for the respective user.
        save:
            A bool that lets you decide whether you want to save the created
            header to a file. This is recommended if you plan to do many requests
            since the number of api tokens is limited.
    Returns:
        A dictionary with the needed headers for authorization towards the v1
        Muesli API.
        example: (<TOKEN> is the corresponding JWT token)
            {
                'Authorization': 'Bearer <TOKEN>',
                'Accept': 'application/json'
            }
    """
    if not username:
        username = input('Please enter your username: ')
    logging.debug("Username: %s", username)

    header_name = username
    if path.isfile(header_name) and stat(header_name).st_size != 0:
        with open(header_name, 'r') as header:
            header_content = literal_eval(header.read())
            logging.debug('Read header from file "%s"!', header_name)
    else:
        if not password:
            password = getpass.getpass(prompt='Password: ')

        r = requests.post(url + '/api/v1/login',
                          data={
                              "email": username,
                              "password": password
                          })
        token = r.json().get("token", "")
        logging.debug(json.dumps(r.json()))
        header_content = {'Authorization': 'Bearer ' + token}
        header_content.update(STATIC_HEADERS)
        if save:
            save_password(username, header_content)
    return header_content


def save_password(username, header_content):
    """ saves a header generated by authenticate() to a file. """
    header_name = username
    with open(header_name, 'w') as header:
        header.write("# This file was generated by: {}!\n".format(__file__))
        header.write(json.dumps(header_content))
        logging.info('Created header file for user "%s"!', header_name)
