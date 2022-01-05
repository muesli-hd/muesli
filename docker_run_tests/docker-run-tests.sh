#!/usr/bin/env bash
echo "Waiting for database to start ..."; sleep 3;
wait-for-it "${MUESLI_DB_HOST}":5432 -t 30 || exit 1

echo "Generating configs ... "
sed "s/connection: \S\+/connection: postgresql:\/\/${MUESLI_DB_USER:-postgres}:${MUESLI_DB_PASSWORD}@${MUESLI_DB_HOST}\/${MUESLI_DB}/" muesli.yml.example | sed 's/production: \S\+/production: True/' | sed 's/server: \S\+/server: 0.0.0.0/' > muesli.yml
sed "s/sqlalchemy.url = \S\+/sqlalchemy.url = postgres:\/\/${MUESLI_DB_USER:-postgres}:${MUESLI_DB_PASSWORD}@${MUESLI_DB_HOST}\/${MUESLI_DB}test/" alembic.ini.example > alembic.ini

# The tests run with an empty database. Therefore we don't need to load and upgrade a database dump
# the init-db.sh script creates the necessary db.

echo "Starting dummy SMTP server"
python3 -m smtpd -n -c DebuggingServer localhost:25 &

echo "Starting the tests ..."
MUESLI_PATH=$(pwd) py.test --cov=muesli muesli/tests/*
# MUESLI_PATH=$(pwd) py.test --cov=muesli muesli/tests/api/v1/*
codecov
pylint --disable=R0801,R0903,C0103,C0301,C0111 muesli.web.api muesli.web.viewsApi muesli.tests.api
exit
