from cornice.resource import resource

from muesli import models
from muesli.web import context
from muesli.web.api import allowed_attributes

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
        """
        ---
        get:
          tags:
            - "Muesli API"
          summary: "return all tutorials"
          description: ""
          operationId: "tutorial_collection_get"
          produces:
            - "application/json"
          responses:
            200:
              description: "response for 200 code"
              schema:
                $ref: "#/definitions/CollectionTutorial"
        """
        tutorials = self.request.user.tutorials.options(joinedload(models.Tutorial.tutor), joinedload(models.Tutorial.lecture))
        schema = models.TutorialSchema(many=True, only=allowed_attributes.collection_tutorial())
        return schema.dump(tutorials)

    def get(self):  # TODO Check if part of tutorial or allowed to view
        """
        ---
        get:
          tags:
            - "Muesli API"
          summary: "return a specific tutorial"
          description: ""
          operationId: "tutorial_get"
          produces:
            - "application/json"
          responses:
            200:
              description: "response for 200 code"
              schema:
                $ref: "#/definitions/Tutorial"
        """
        tutorial = self.request.user.tutorials.options(joinedload(models.Tutorial.tutor), joinedload(models.Tutorial.lecture)).filter(models.Tutorial.id==self.request.matchdict['tutorial_id']).one()
        exa = tutorial.lecture.exams.filter((models.Exam.results_hidden==False)|(models.Exam.results_hidden==None))
        if True:  # TODO CHECK IF TUTOR/ASSISTANT
            tut_schema = models.TutorialSchema()
        else:
            tut_schema = models.TutorialSchema(only=allowed_attributes.tutorial())
        exam_schema = models.ExamSchema(many=True, only=["id", "name"])

        result = tut_schema.dump(tutorial)
        result.update({"exams": exam_schema.dump(exa)})
        return result

