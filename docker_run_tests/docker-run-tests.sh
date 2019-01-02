#!/usr/bin/env bash
sed 's/\/\/\//\/\/postgres@postgres\//' muesli.yml.example | sed 's/localhost/0.0.0.0/' > muesli.yml
sed 's/\/\/\//\/\/postgres@postgres\//' alembic.ini.example > alembic.ini
sleep 5;
sed -i '/^sqlalchemy.url = postgres:\/\/postgres@postgres\/muesli/ d' alembic.ini
sed -i 's/^\#sqlalchemy.url = postgres:\/\/postgres@postgres\/muesli/sqlalchemy.url = postgres:\/\/postgres@postgres\/muesli/' alembic.ini
alembic upgrade head
python3 -m smtpd -n -c DebuggingServer localhost:25 &
MUESLI_PATH=$(pwd) py.test --cov=muesli muesli/tests && exit
