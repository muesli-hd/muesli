# Development Information
Muesli uses the pyramid framework for the webserver and the chameleon template
engine to serve the webpages. Alembic and sqlalchemy are used for the database.

## Locations

| Location | Used for |
|----------|-------------------|
| alembic | Database-handling |
| docker\_run\_tests | used for running tests in a docker container |
| muesli | contains actual ode for muesli |
| docker-serve.sh | This file is executed by the docker-container |
| muesli/tests | contains tests for the muesli code |
| muesli/web | contains most muesli code |
| muesli/models.py | contains all model-definition used in the database |
| muesli/web/static | contains JS and CSS |
| muesli/web/templates | contains the templates which define the appearance of the Website |
| muesli/web/templates/Fragments/main.pt | Is the main template used for elements to appear on all pages |
| muesli/web/\_\_init\_\_.py | Here Requests are prepared and routs defined |
| muesli/web/navigation\_tree.py | Definition and creation of the navigation tree |
| muesli/web/views\*.py | Contains the code to fill in the templates |

### Tests
At the moment tests are minimal, most pages of this site are only tested for
access-rights.

### Database changes
If you want to change the database use follow the instruction for alembic. Make
sure to adjust the definitions in muesli/models.py .

### Static web-content
Don't add JS-libraries to the repository, instead add a symlink pointing to the
install-location on Ubuntu.

### Page setup
To create or edit a page you can edit the template to change the visuals, to add
functions you edit the views\*.py file. In the pythonfile you can pass variables
to the template and write server-side logic.
Remember to add tests for all new pages!

For each class or function belonging to a page you need a decorator like this
one:

`@view_config(route_name='admin', renderer='muesli.web:templates/admin.pt', context=GeneralContext, permission='admin')`

You set a name matching the name given in \_\_init\_\_.py, the renderer is used
to set the corresponding templatefile. The context is important to control the
permissions and influences what is shown in the navigation. The permission
attribute is used to set the permission.

### Permissions
The permissions are granted in the context.py file using the \_\_acl\_\_ attribute.
When changing permissions update them in navigation\_tree.py and the API as
necessary.

This means you cannot get the permission of a page dynamically and if you want
to check for a permission you have to make sure the permission is granted in the
specific context.

### Navigation\_tree
The navigation\_tee is a tree-structure saved in the request object used for the
navigation the the right site. When editing this tree make sure not to create
any cycles, since these will crash the template-engine.
