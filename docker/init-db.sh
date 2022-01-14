#!/bin/bash
set -e

# This is necessary for both tests and loading production database dumps. The tests run on an empty database with suffix
# test. To be as close to production as possible, we simply create a similar database layout here.

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER postgres PASSWORD 'muesli' SUPERUSER;
    CREATE ROLE "muesli-admin";
    GRANT "muesli-admin" TO "$POSTGRES_USER";

    CREATE DATABASE mueslitest OWNER muesli;
EOSQL

# This allows restoring sql dumps in the compressed postgres format too
if [[ -f "/muesli.prod.sql" ]]; then
  echo "Loading production database dump"
  pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" -d muesli -n public -1 /muesli.prod.sql
else
  echo "Loading development database dump"
  psql -U "$POSTGRES_USER" -f /muesli.sql muesli
fi
