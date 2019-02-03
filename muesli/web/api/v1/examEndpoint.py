from cornice.resource import resource

from muesli import models
from muesli.web import context

from sqlalchemy.orm import exc, joinedload, undefer
from sqlalchemy.sql.expression import desc


@resource(path='/exams/{exam_id}',
          factory=context.GeneralContext,
          permission='view')  # TODO Api specific permission
class Exam(object):
    def __init__(self, request, context=None):
        self.request = request
        self.db = request.db

    def get(self):  # TODO Check if Lecture Student maybe list all lecturestudents
        exam_id = self.request.matchdict["exam_id"]
        exam = self.request.db.query(models.Exam).get(exam_id)
        exer_schema = models.ExerciseSchema(many=True)
        exam_schema = models.ExamSchema()
        result = exam_schema.dump(exam)
        result.update({"exercises": exer_schema.dump(exam.exercises)})
        return result


