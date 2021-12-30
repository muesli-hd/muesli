#!/usr/bin/env bash
if [[ -v MUESLI_TESTMODE ]] && [[ ! -f muesli.yml ]]
then
    echo "Generating configs ... "
    sed "s/postgresql:\/\/\/muesli/postgresql:\/\/${MUESLI_DB_USER:-postgres}:${MUESLI_DB_PASSWORD}@${MUESLI_DB_HOST}\/${MUESLI_DB}/" muesli.yml.example | sed 's/production: True/production: False/' | sed 's/server: 0.0.0.0/server: mailcatcher:1025/' > muesli.yml
    sed "s/postgres:\/\/\/muesli/postgres:\/\/${MUESLI_DB_USER:-postgres}:${MUESLI_DB_PASSWORD}@${MUESLI_DB_HOST}\/${MUESLI_DB}/" alembic.ini.example > alembic.ini
    echo "Deploying JS and CSS libs"
    rsync -av /opt/muesli_static_libs/ muesli/web/static/
    echo "Waiting for database to start ..."; sleep 3;
    wait-for-it ${MUESLI_DB_HOST}:5432 -t 30 || exit 1
    python3 -m smtpd -n -c DebuggingServer localhost:25 &
    export PYRAMID_DEBUG_TEMPLATES=1
fi

echo "Running database upgrade ... "
alembic upgrade head
echo -n "IP-address: "
ip -4 addr show | grep -oP "(?<=inet ).*(?=/)" | grep -ve "127.0.0.1"

if [[ -v MUESLI_TESTMODE ]]
then
    # concatinate all filenames with --fs-reload
    FSRELOADLIST=$(find /opt/muesli4 -type d -not -path '*/.git*' -not -path '*/__pycache__*' -print \
     | sed -e ':a' -e 'N' -e '$!ba' -e 's/\n/ --fs-reload /g')
    uwsgi --http :8080 --wsgi-file muesli.wsgi --callable application \
          --uid muesli --disable-logging --fs-reload ${FSRELOADLIST}
else
    uwsgi --socket :8080 --wsgi-file muesli.wsgi --callable application \
          --master --processes 4 --threaded-logger --uid muesli --stats :8081 \
          --disable-logging --lazy-apps
fi
