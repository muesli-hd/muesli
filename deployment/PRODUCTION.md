# Production deployment guide

## General Information:
Müsli is tested with postgresql as database backend. However, it should run without problems
with MySQL or SqLite as well. As Müsli uses sqlalchemy as abstraction layer above the database,
the database can be changed within one line (currently in muesli/__init__.py, in future
hopefully in some configuration file).

## Setup:

Müsli can be configured using a configuration file called `muesli.yml` in its main directory. It
is in the YAML format. You can find an example file called `muesli.yml.example`
included. If you do not provide your own `muesli.yml` file, the example will be copied on the first startup.


## Production setup:

If you want to deploy Müsli using Apache and Postgresql, you will first have to
create a database for the user www-data. You will need to execute these commands as user 'postgres':

    createuser -S -D -R www-data
    createdb -O www-data -E UTF8 muesli

In Apache, the module fastcgi has to be activated. This can be done using
the command

    a2enmod fastcgi

In the Apache config, you can enable Müsli with the following snippet:

    ProxyPass / uwsgi://localhost:8033/
    ProxyPassReverse / uwsgi://localhost:8033/

or some similar port.

You will also need to modify the `muesli.yml` file in order to configure other things like the mail server. You can look
at deployment directory for a `docker-compose.production.yml` and some other hints for a good production setup.
