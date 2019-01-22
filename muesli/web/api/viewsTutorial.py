from cornice.resource import resource

from muesli import models
from muesli.web import context

from sqlalchemy.orm import exc, joinedload, undefer
from sqlalchemy.sql.expression import desc


@resource(collection_path='/api/tutorials',
          path='/api/tutorials/{tutorial_id}',
          factory=context.TutorialContext,
          permission='viewOverview')  # TODO Api specific permission
class Tutorial(object):
    def __init__(self, request, context=None):
        self.request = request
        self.db = request.db

    def collection_get(self):  # Done
        tutorials = self.request.user.tutorials.options(joinedload(models.Tutorial.tutor), joinedload(models.Tutorial.lecture))
        schema = models.TutorialSchema(many=True, exclude=["students"])
        return schema.dump(tutorials)

    def get(self):  # TODO Check if part of tutorial or allowed to view
        tutorial = self.request.user.tutorials.options(joinedload(models.Tutorial.tutor), joinedload(models.Tutorial.lecture)).filter(models.Tutorial.id==self.request.matchdict['tutorial_id']).one()
        exa = tutorial.lecture.exams.filter((models.Exam.results_hidden==False)|(models.Exam.results_hidden==None))
        if True:  # TODO CHECK IF TUTOR/ASSISTANT
            tut_schema = models.TutorialSchema()
        else:
            tut_schema = models.TutorialSchema(exclude=["students"])
        exam_schema = models.ExamSchema(many=True, only=["id", "name"])

        result = tut_schema.dump(tutorial)
        result.update({"exams": exam_schema.dump(exa)})
        return result

