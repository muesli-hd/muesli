#!/usr/bin/env bash
sed "s/\/\/\/muesli/\/\/postgres@postgres\/muesli/" muesli.yml.example | sed 's/localhost/0.0.0.0/' > muesli.yml
sed "s/\/\/\/muesli/\/\/postgres@postgres\/mueslitest/" alembic.ini.example > alembic.ini
echo "Sleeping for 3s ..."; sleep 3;
echo "Generating configs ..."
echo "Upgrading the databases ..."
alembic upgrade head
python3 -m smtpd -n -c DebuggingServer localhost:25 &
echo "Starting the tests ..."
MUESLI_PATH=$(pwd) py.test --cov=muesli muesli/tests/*
# MUESLI_PATH=$(pwd) py.test --cov=muesli muesli/tests/api/v1/*
codecov
pylint --disable=R0801,R0903,C0103,C0301,C0111 muesli.web.api muesli.web.viewsApi muesli.tests.api
exit
