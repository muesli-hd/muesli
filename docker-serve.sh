#!/usr/bin/env bash
sed 's/\/\/\//\/\/postgres@postgres\//' muesli.yml.example | sed 's/localhost/0.0.0.0/' > muesli.yml
sed 's/\/\/\//\/\/postgres@postgres\//' alembic.ini.example > alembic.ini
python3 -m smtpd -n -c DebuggingServer localhost:25 &
su -c /opt/muesli4/muesli-test muesli
