# -*- coding: utf-8 -*-
#
# muesli/web/api/v1/attributes.py
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
"""Collection of various attributes for the MarshmellowSchemas."""


def user():
    """ Allowed attributes for the UserSchema, used in various functions.
    Args:
    Returns:
        attributes: A list of unlocked attributes for the user.
    Raises:
    """
    attributes = ['id', 'first_name', 'last_name', 'email']
    return attributes


def collection_lecture():
    """ Allowed attributes for the lectureEndpoint.
    Args:
    Returns:
        attributes: A list of unlocked attributes for Lecture.collection_get().
    Raises:
    """
    attributes = [
        'id',
        'name',
        'lecturer',
        'assistants',
        'term',
    ]
    return attributes


def lecture():
    """ Allowed attributes for the lectureEndpoint.
    Args:
    Returns:
        attributes: A list of unlocked attributes for Lecture.get().
    Raises:
    """
    attributes = [
        'id',
        'name',
        'lecturer',
        'assistants',
        'term',
        'url',
        'tutorials',
    ]
    return attributes


def collection_tutorial():
    """ Allowed attributes for the tutorialEndpoint.
    Args:
    Returns:
        attributes: A list of unlocked attributes for Tutorial.collection_get().
    Raises:
    """
    attributes = [
        'comment',
        'place',
        'tutor',
        'max_students',
        'time',
        'student_count',
        'id',
        'lecture_id'
    ]
    return attributes


def tutorial():
    """ Allowed attributes for the tutorialEndpoint.
    Args:
    Returns:
        attributes: A list of unlocked attributes for Tutorial.get().
    Raises:
    """
    attributes = [
        'comment', 'place', 'tutor', 'max_students', 'time', 'student_count',
        'id', 'time', 'exams', 'lecture_id'
    ]
    return attributes
