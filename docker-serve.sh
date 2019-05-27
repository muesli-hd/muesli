#!/usr/bin/env bash
if [[ -v MUESLI_TESTMODE ]]
then
    sed 's/\/\/\//\/\/postgres@postgres\//' muesli.yml.example > muesli.yml
    sed 's/\/\/\//\/\/postgres@postgres\//' alembic.ini.example > alembic.ini
    echo "Sleeping for 3s ..."; sleep 3;
    echo "Generating configs ... "
    python3 -m smtpd -n -c DebuggingServer localhost:25 &
fi

echo "Running database upgrade ... "
alembic upgrade head
echo -n "IP-address: "
ip -4 addr show | grep -oP "(?<=inet ).*(?=/)" | grep -ve "127.0.0.1"

if [[ -v MUESLI_TESTMODE ]]
then
    uwsgi --http :8080 --wsgi-file muesli.wsgi --callable application --fs-reload /opt/muesli4 --uid muesli \
     --stats :8081 --disable-logging
else
    uwsgi --socket :8080 --wsgi-file muesli.wsgi --callable application --master --processes 4 --threads 2 \
    --threaded-logger --uid muesli --stats :8081 --disable-logging --lazy-apps
fi
