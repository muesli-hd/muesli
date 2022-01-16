#!/usr/bin/env bash
cp -n alembic.ini.example alembic.ini
cp -n muesli.yml.example muesli.yml

# The tests run with an empty database. Therefore we don't need to load and upgrade a database dump
# the init-db.sh script creates the necessary db.

echo "Starting the tests ..."
py.test --cov=muesli --cov-report=xml muesli/tests/*
TESTS_EXIT_CODE=$?
# py.test --cov=muesli muesli/tests/api/v1/*
cuv graph
pylint --disable=R0801,R0903,C0103,C0301,C0111 muesli.web.api muesli.web.viewsApi muesli.tests.api
exit ${TESTS_EXIT_CODE}
