# Workflow
Vorschläge zum GitHub Workflow: (wir sollen ja auch ein wenig SoftwareEngineering verwenden :wink: )
Die bereits definierten Userstories werden als Milestone realisiert, der dann die jeweils zugehörigen Issues bündelt und so in Logische einheiten gliedert.
Die Gruppenzugehörigkeit eines Issues wird über Labels markiert, ansonsten Labels wie  gehabt.
Pro in sich abgeschlossene Feature wird ein Featurebranch erstellt, der dann nach erfolgreicher Implementation gegen das "echte" Müsli gemerged wird.
Passt das? :smiley:
* Set up your system as described in the [`README.md`](./README.md).
* if you plan on contributing to muesli fork the repository and clone it:
```bash
$ git clone git@github.com:<your_username>/muesli.git
```
* create a branch for your changes
```
$ git checkout -b <your_very_special_branchname>
```
* push your changes
```bash
$ git push --set-upstream origin <your_very_special_branchname>
```
* create a pull request: [https://github.com/muesli-hd/muesli/new/pull](https://github.com/muesli-hd/muesli/new/pull)

# General Information about the Project

## Used programs & frameworks
Muesli uses the thie following frameworks and programs:

| Program                                                               | Used for                                       |
|-----------------------------------------------------------------------|------------------------------------------------|
| [pyramid_webframework](https://trypyramid.com/documentation.html)     | Access control, handling of HTTP requests      |
| [`alembic`](https://alembic.sqlalchemy.org/en/latest/index.html)      | Versioninig for the database                   |
| [SQLAlchemy](https://www.sqlalchemy.org/)                             | Managing the models and make changes to the DB |
| [`chameleon`](https://chameleon.readthedocs.io/en/latest/index.html)  | Templating language to fill the HTML sites     |
| [`marshmallow`](https://marshmallow.readthedocs.io/en/3.0/index.html) | Used to serialize object to JSON and back      |
| [`cornice`](https://cornice.readthedocs.io/en/latest/index.html)      | framework to represent the API                 |
| [`pyramid_apispec`](https://github.com/ergo/pyramid_apispec/)         | framework used to document the API             |

## Locations in the filetree

| Location                               | What's it good for?                                               |
|----------------------------------------|-------------------------------------------------------------------|
| alembic                                | Database-handling                                                 |
| docker\_run\_tests                     | used for running tests in a docker container                      |
| muesli                                 | contains actual code for muesli                                   |
| docker-serve.sh                        | This file is executed by the docker-container on startup          |
| muesli/tests                           | contains tests for the muesli code                                |
| muesli/web                             | contains most muesli code                                         |
| muesli/models.py                       | contains all model-definition used in the database                |
| muesli/web/static                      | contains JS and CSS                                               |
| muesli/web/templates                   | contains the templates which define the appearance of the Website |
| muesli/web/templates/Fragments/main.pt | Is the main template used for elements to appear on all pages     |
| muesli/web/\_\_init\_\_.py             | Here Requests are prepared and routs defined                      |
| muesli/web/navigation\_tree.py         | Definition and creation of the navigation tree                    |
| muesli/web/views\*.py                  | Contains the code to fill in the templates                        |
| muesli/web/api/\*                      | Contains the module which serves the API                          |

### Tests
At the moment tests are minimal, most pages of this site are only tested for
access-rights.

### Database changes
If you want to change the database use follow the instruction for `alembic`. Make
sure to adjust the definitions in `muesli/models.py` .
To upgrade to the latest version of the database:
```bash
$ alemic upgrade head
```
To create new revisions use:
```bash
$ alembic revision -m "Add a column"
```

### Static web-content
Don't add JS-libraries to the repository, instead add a symlink pointing to the
install-location on Ubuntu. You can install new dependencies with `apt` via the
`Dockerfile`.

### Page setup
To create or edit a page you can edit the template to change the visuals, to add
functions you edit the `views*.py` file. In the pythonfile you can pass variables
to the template and write server-side logic. You can also execute arbitrary python
commands in the templates, so dont underestimate their power.
Remember to add tests for all new pages!

For each class or function belonging to a page you need a decorator like this
one:

`@view_config(route_name='admin', renderer='muesli.web:templates/admin.pt', context=GeneralContext, permission='admin')`

You set a name matching the name given in `__init__.py`, the renderer is used
to set the corresponding template file. The context is important to control the
permissions and influences what is shown in the navigation. The permission
attribute is used to set the permission.

### Permissions
The permissions are granted in the `context.py` file using the `__acl__` attribute.
When changing permissions update them in `muesli/web/navigation_tree.py` and the API as
necessary. Keep in mind that the API uses its own contexts and update them accordingly.

This means you cannot get the permission of a page dynamically and if you want
to check for a permission you have to make sure the permission is granted in the
specific context.

### Navigation\_tree
The navigation\_tee is a tree-structure saved in the request object used for the
navigation the the right site. When editing this tree make sure not to create
any cycles, since these will crash the template-engine.

Happy Hacking and Godspeed!
