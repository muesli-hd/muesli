#!/usr/bin/env bash
sed 's/\/\/\//\/\/postgres@postgres\//' muesli.yml.example | sed 's/localhost/0.0.0.0/' > muesli.yml
sed 's/\/\/\//\/\/postgres@postgres\//' alembic.ini.example > alembic.ini
echo "Sleeping for 3s ..."; sleep 3;
echo "Generating configs ..."
sed -i '/^sqlalchemy.url = postgres:\/\/postgres@postgres\/muesli/ d' alembic.ini
sed -i 's/^\#sqlalchemy.url = postgres:\/\/postgres@postgres\/muesli/sqlalchemy.url = postgres:\/\/postgres@postgres\/muesli/' alembic.ini
echo "Upgrading the databases ..."
alembic upgrade head
python3 -m smtpd -n -c DebuggingServer localhost:25 &
echo "Starting the tests ..."
MUESLI_PATH=$(pwd) py.test --cov=muesli muesli/tests/*
# MUESLI_PATH=$(pwd) py.test --cov=muesli muesli/tests/api/v1/*
codecov
pylint --disable=R0801,R0903,C0103,C0301,C0111 muesli.web.api muesli.web.viewsApi muesli.tests.api
exit
