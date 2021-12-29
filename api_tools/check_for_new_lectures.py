# -*- coding: utf-8 -*-
#
# api_tools/sample_requests.py
#
# This file is part of MUESLI.
#
# Copyright (C) 2021, Christian Heusel <christian (at) heusel.eu>
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

import threading
import logging
import requests
import coloredlogs

from header import authenticate, STATIC_HEADERS, MUESLI_URL

# This could be replaced by cmd input vars
WAIT_TIME_SECONDS = 60 * 60 # 1h
USERNAME = "test@example.com"
SEMESTER = "2021 SS"


def get(endpoint, header):
    endpoint = MUESLI_URL + endpoint
    request = requests.get(endpoint, headers=header)
    return request.json()


def get_lectures():
    headers = authenticate(username=USERNAME, save=True)
    endpoint = "/api/v1/lectures"
    return get(endpoint, headers)


def extract_lecture_titles(l):
    return [r["name"] for r in l if r["term"] == SEMESTER]


def run_event_loop():
    ticker = threading.Event()
    old = set(extract_lecture_titles(get_lectures()))

    while not ticker.wait(WAIT_TIME_SECONDS):
        lectures = get_lectures()
        current = set(extract_lecture_titles(lectures))
        if current.difference(old):
            logging.info("New lecture found: %s", current.difference(old))
        else:
            logging.info("No new lecture found!")
        old = current


def main():
    coloredlogs.install(level=logging.DEBUG, fmt='%(asctime)s → %(message)s')
    logging.info("Will check every %s seconds for new lectures on \"%s\"!",
                 WAIT_TIME_SECONDS, MUESLI_URL)
    run_event_loop()


if __name__ == "__main__":
    main()
