Needed Packages:
================

The following packages are needed in order to run Müsli:

    python-pyramid
    python-excelerator
    python-sqlalchemy (>=0.7, i.e. from backports, ...)
    libjs-jquery-tablesorter
    libjs-jquery-fancybox

For database-upgrade, the following packages is needed in addition:

    alembic

In order to run the tests, this package is needed:

    python-webtest

General Information:
====================

Müsli is tested with postgresql as database backend. However, it should run without problems
with MySQL or SqLite as well. As Müsli uses sqlalchemy as abstraction layer above the database,
the database can be changed within one line (currently in muesli/__init__.py, in future
hopefully in some configuration file).

Setup:
======

Müsli comes with a script to test it without the need to configure some
web server like Apache. If you want to use Müsli using Postgresql (the default),
just create a database called 'muesli' for it, e.g.:

    createuser -S -D -R username
    createdb -O username -E UTF8 muesli

This commands usually have to be started as user 'postgres'

Setting Up
----------

The database still has to be created. For this execute the script

    python setupDatabase.py

After you have registered yourself in Müsli with some mail adress, you
can give yourself administration rights by

    python setupDatabase.py mailadress

If you want to change something in the database by hand, you can
run the script "loadDatabase.py", e.g. from within ipython via

    %run loadDatabase.py

to get a sqlalchemy session in the database.

Testing
-------

Müsli comes with a script to test it without the need to configure some
web server like Apache.
You should be able to start the test installation from the Müsli directory by

    ./muesli-test

If you want to run the tests as well, you have to create another database 'mueslitest'.
then you can run the tests from the Müsli directory via

    python test.py



Productive:
-----------

If you want to deploy Müsli using Apache and Postgresql, again you have first to
create the database. But this time for the user 'www-data' (again, you may have
to execute the commands as user 'postgres':

    createuser -S -D -R www-data
    createdb -O www-data -E UTF8 muesli

In Apache, the module fastcgi has to be activated. This can be done using
the command

    a2enmod fastcgi

In the Apache config, you can enable Müsli with the following snippet:

    Alias /muesli/static/ /opt/muesli4/muesli/web/static/
    
    <Directory /opt/muesli/muesli/web/static>
      AllowOverride None
      Order allow,deny
      Allow from all
    </Directory>
    
    WSGIApplicationGroup muesli
    WSGIDaemonProcess muesli user=muesli processes=8 threads=1 python-path=/opt/muesli4 display-name="wsgi: muesli4"
    WSGIProcessGroup muesli
    WSGIScriptAlias /muesli /opt/muesli4/muesli.wsgi

Database upgrades
=================

Müsli uses alembic to manage its database revisions. To upgrade to the latest database revision, run the command

    alembic upgrade head

in the Müsli directory. At the moment, Müsli uses a single database setup for alembic. Thus, in order to update
the 'mueslitest' database as well, you have to adapt 'alembic.ini' and run 'alembic upgrade head' again. This
will be changed in the future.
