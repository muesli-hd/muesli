#!/usr/bin/env bash
sed 's/\/\/\//\/\/postgres@postgres\//' muesli.yml.example | sed 's/localhost/0.0.0.0/' > muesli.yml
sed 's/\/\/\//\/\/postgres@postgres\//' alembic.ini.example > alembic.ini
echo "Sleeping for 3s ..."; sleep 3;
echo "Generating configs ... "
alembic upgrade head
python3 -m smtpd -n -c DebuggingServer localhost:25 &
echo -n "IP-address: "
ip -4 addr show | grep -oP "(?<=inet ).*(?=/)" | grep -ve "127.0.0.1"
su -c /opt/muesli4/muesli-test muesli
