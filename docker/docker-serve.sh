#!/usr/bin/env bash

cp -n alembic.ini.example alembic.ini
cp -n muesli.yml.example muesli.yml
chmod 0666 muesli.yml alembic.ini

echo "Deploying JS and CSS libs"
rsync -rv /opt/muesli_static_libs/ muesli/web/static/
echo "Running database upgrade ... "
alembic upgrade head
echo -n "IP-address: "
ip -4 addr show | grep -oP "(?<=inet ).*(?=/)" | grep -ve "127.0.0.1"

if [[ -v MUESLI_DEVMODE ]]
then
    # concatenate all filenames with --fs-reload
    FSRELOADLIST=$(find /opt/muesli4 -type d -not -path '*/.git*' -not -path '*/__pycache__*' -print \
     | sed -e ':a' -e 'N' -e '$!ba' -e 's/\n/ --fs-reload /g')
    uwsgi --plugin python3 --ini-paste-logged development.ini --fs-reload ${FSRELOADLIST}
else
    uwsgi --plugin python3 --ini-paste-logged deployment/production.ini
fi
