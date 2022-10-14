# -*- coding: utf-8 -*-
#
# muesli/web/api/v1/subjectEndpoint.py
#
# This file is part of MUESLI.
#
# Copyright (C) 2022, Tobias Wackenhut  <tobias (at) wackenhut.at>
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

from muesli import models
from muesli.web.context import GeneralContext
from muesli.web.api.v1 import allowed_attributes

from sqlalchemy import select, or_, distinct
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from cornice.resource import resource, view
from marshmallow.exceptions import ValidationError
from json import JSONDecodeError
from pyramid.httpexceptions import HTTPNotFound
from pyramid.httpexceptions import HTTPForbidden
from marshmallow import Schema, fields


class SubjectDeletionSchema(Schema):
    migrate = fields.Boolean(required=True)
    migration_target_id = fields.Integer()


@resource(collection_path='/subjects',
          path='/subjects/{subject_id}',
          factory=GeneralContext)
class Subject:
    def __init__(self, request, context=None):
        del context
        self.request = request
        self.db = request.db

    @view(permission="view_subjects")
    def collection_get(self):
        """
        ---
        get:
          security:
            - Bearer: [read]
            - Basic: [read]
          tags:
            - "v1"
          summary: "return all known subjects"
          description: "Regular users see their own and all curated subjects, all subjects are returned with extended permissions"
          operationId: "subject_collection_get"
          produces:
            - "application/json"
          responses:
            200:
              description: "response for 200 code"
              schema:
                $ref: "#/definitions/CollectionSubject"
        """
        if self.request.has_permission('curate_subjects'):
            # All subjects
            subjects_query = select(models.Subject)
        else:
            # All curated subjects and the users own.
            subjects_query = select(models.Subject).outerjoin(
                models.user_subjects_table).join(models.User).where(
                or_(models.User.id == self.request.user.id, models.Subject.curated == True)  # pylint: disable=C0121
            ).distinct()
        subjects = self.request.db.scalars(subjects_query).all()
        schema = models.SubjectSchema(many=True, only=allowed_attributes.collection_subject())
        return schema.dump(subjects)

    @view(permission="view_subjects")
    def get(self):
        """
        ---
        get:
          security:
            - Bearer: [read]
            - Basic: [read]
          tags:
            - "v1"
          summary: "return the requested subject"
          description: "Regular users can only request information on their own and all curated subjects. Extended permissions allow arbirtrary subjects to be queried."
          operationId: "subject_get"
          produces:
            - "application/json"
          responses:
            200:
              description: "response for 200 code"
              schema:
                $ref: "#/definitions/Subject"
            404:
              description: "HTTPNotFound: Subject with requested id not found"
              schema:
                type: object
                properties:
                  result:
                    type: string
                    example: "error"
                  description:
                    type: string
                    example: "Subject not found"
        """
        subject_id_str = self.request.matchdict['subject_id']
        try:
            subject_id = int(subject_id_str)
        except ValueError:
            self.request.errors.add('body', 'fail', 'Subject id must be an integer.')
            return {}
        subject = self.db.get(models.Subject, subject_id)

        # Permission check and filtering
        if not self.request.has_permission('curate_subjects'):
            # All curated subjects and the users own.
            if subject and not subject.curated and subject not in self.request.user.subjects:
                subject = None  # Simulate subject not found

            if not subject:
                return HTTPForbidden({'result': 'error',
                                      'description': 'Permission denied. You can only view your own and curated subjects.'})

        if not subject:
            return HTTPNotFound({'result': 'error', 'description': 'Subject not found.'})

        schema = models.SubjectSchema(only=allowed_attributes.collection_subject())
        return schema.dump(subject)

    @view(permission='curate_subjects')
    def collection_post(self):
        """
        ---
        post:
          security:
            - Bearer: [write]
            - Basic: [write]
          tags:
            - "v1"
          summary: "create a subject"
          operationId: "subject_collection_post"
          produces:
            - "application/json"
          consumes:
            - "application/json"
          parameters:
          - in: "body"
            name: "body"
            description: ""
            required: true
            schema:
              $ref: "#/definitions/Subject"
          responses:
            200:
              description: successful creation of a subject
              schema:
                type: object
                properties:
                  result:
                    type: string
                    example: ok
                  created:
                    $ref: "#/definitions/CollectionSubject"
            400:
              description: HTTPBadRequest (Example uses A bad attribute)
              schema:
                type: object
                properties:
                  result:
                    type: string
                    example: "error"
                  error:
                    type: array
                    example: [{'description': {'name': ['Missing data for required field.'], 'test123': ['Unknown field.']}, 'name': 'fail', 'location': 'body'}]
        """
        schema = models.SubjectSchema()
        schema.context['session'] = self.request.db
        try:
            result = schema.load(self.request.json_body)
        except ValidationError as e:
            self.request.errors.add('body', 'fail', e.messages)
            return {}
        except JSONDecodeError:
            self.request.errors.add('body', 'fail', 'Invalid JSON')
            return {}
        else:
            subject = models.Subject(**result)
            try:
                self.db.add(subject)
                self.db.commit()
            except IntegrityError:
                self.request.errors.add('body', 'fail', 'Subject cannot be added. Maybe there is a duplicate?')
                return {}
            return {'result': 'ok', 'created': schema.dump(subject)}

    @view(permission='curate_subjects')
    def put(self):
        """
        ---
        put:
          security:
            - Bearer: [write]
            - Basic: [write]
          tags:
            - "v1"
          summary: "modify a subject"
          operationId: "subject_put"
          produces:
            - "application/json"
          consumes:
            - "application/json"
          parameters:
          - in: "body"
            name: "body"
            description: ""
            required: true
            schema:
              $ref: "#/definitions/Subject"
          responses:
            200:
              description: successful update of a subject
              schema:
                type: object
                properties:
                  result:
                    type: string
                    example: ok
                  updated:
                    $ref: "#/definitions/Subject"
            400:
              description: HTTPBadRequest (Example uses A bad attribute)
              schema:
                type: object
                properties:
                  result:
                    type: string
                    example: "error"
                  error:
                    type: array
                    example: [{'description': {'name': ['Missing data for required field.'], 'test123': ['Unknown field.']}, 'name': 'fail', 'location': 'body'}]
        """
        subject_id = self.request.matchdict['subject_id']
        subject = self.db.get(models.Subject, subject_id)
        schema = models.SubjectSchema()
        # attatch db session to schema so it can be used during validation
        schema.context['session'] = self.request.db
        try:
            result = schema.load(self.request.json_body, partial=True)
        except ValidationError as e:
            self.request.errors.add('body', 'fail', e.messages)
            return {}
        except JSONDecodeError:
            self.request.errors.add('body', 'fail', 'Invalid JSON')
            return {}
        else:
            for k, v in result.items():
                setattr(subject, k, v)
            try:
                self.db.commit()
            except SQLAlchemyError as ex:
                self.db.rollback()
                self.request.errors.add('body', 'fail', str(ex))
                return {}
            else:
                return {'result': 'ok', 'update': schema.dump(subject)}

    @view(permission="curate_subjects")
    def delete(self):
        """
        ---
        delete:
          security:
            - Bearer: [read]
            - Basic: [read]
          tags:
            - "v1"
          summary: "Delete a subject and optionally merge its users into another."
          description: "Take the given subjects from_subject and to_subject, add all users having from_subject to to_subject and delete from_subject."
          operationId: "subject_delete"
          produces:
            - "application/json"
          consumes:
            - "application/json"
          parameters:
          - in: "body"
            name: "body"
            description: ""
            required: true
            schema:
              type: object
              properties:
                migrate:
                  type: boolean
                migration_target_id:
                  type: integer
              required:
                - migrate
          responses:
            200:
              description: successful update of a subject
              schema:
                type: object
                properties:
                  result:
                    type: string
                    example: ok
            400:
              description: HTTPBadRequest (Example uses A bad attribute)
              schema:
                type: object
                properties:
                  result:
                    type: string
                    example: "error"
                  error:
                    type: array
                    example: [{'description': {'migrate': ['Missing data for required field.'], 'test123': ['Unknown field.']}, 'id': 455}]
        """

        # Validate subject
        try:
            subject_id = int(self.request.matchdict['subject_id'])
        except ValueError:
            self.request.errors.add('body', 'fail', 'Invalid Subject id')
            return {}
        subject = self.db.get(models.Subject, subject_id)
        if not subject:
            self.request.errors.add('body', 'fail', 'Subject not found')
            return {}

        # Validate parameters by schema.
        schema = SubjectDeletionSchema()
        # attach db session to schema so it can be used during validation
        schema.context['session'] = self.request.db
        try:
            result = schema.load(self.request.json_body, partial=True)
        except ValidationError as e:
            self.request.errors.add('body', 'fail', e.messages)
            return {}
        except JSONDecodeError:
            self.request.errors.add('body', 'fail', 'Invalid JSON')
            return {}
        migration_target = None
        if result['migrate']:
            if not result['migration_target_id']:
                self.request.errors.add('body', 'fail', 'Migration requires target id.')
                return {}
            migration_target = self.db.get(models.Subject, result['migration_target_id'])
            if not migration_target:
                self.request.errors.add('body', 'fail', 'Migration target not found. Wrong ID?')
                return {}

        # At this stage all validation is done. Do actual deletion and migration.
        for student in subject.students:
            student.subjects.remove(subject)
            if result['migrate'] and migration_target not in student.subjects:
                student.subjects.append(migration_target)

        # Commit changes
        try:
            self.db.commit()
        except SQLAlchemyError as ex:
            self.db.rollback()
            self.request.errors.add('body', 'fail', str(ex))
            return {}
        else:
            return {'result': 'ok'}
