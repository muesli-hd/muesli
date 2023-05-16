#!/bin/bash
set -e

# This is necessary for both tests and loading production database dumps. The tests run on an empty database with suffix
# test. To be as close to production as possible, we simply create a similar database layout here.

psql -v ON_ERROR_STOP=1 --username "postgres" --dbname "postgres" <<-EOSQL
  -- The DBMS has three users:
  -- - postgres: Superuser, this script runs as
  -- - muesli-admin: Owner of all tables and the muesli database. Alembic migrations use this
  -- - muesli: Application user with minimal permissions

  CREATE USER "muesli-admin" PASSWORD 'mueslipw';
  CREATE USER muesli PASSWORD 'mueslipw';

  CREATE DATABASE mueslitest OWNER "muesli-admin";
  CREATE DATABASE muesli OWNER "muesli-admin";

  GRANT CONNECT ON DATABASE muesli TO muesli;
EOSQL
psql -v ON_ERROR_STOP=1 --username "postgres" --dbname "muesli" <<-EOSQL
  GRANT USAGE ON SCHEMA public TO muesli;
  GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO muesli;
  GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO muesli;
  ALTER DEFAULT PRIVILEGES FOR USER "muesli-admin" IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO muesli;
  ALTER DEFAULT PRIVILEGES FOR USER "postgres" IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO muesli;
  ALTER DEFAULT PRIVILEGES FOR USER "muesli-admin" IN SCHEMA public GRANT USAGE ON SEQUENCES TO muesli;
  ALTER DEFAULT PRIVILEGES FOR USER "postgres" IN SCHEMA public GRANT USAGE ON SEQUENCES TO muesli;
EOSQL

# This allows restoring sql dumps in the compressed postgres format too
if [[ -f "/muesli.prod.sql" ]]; then
  echo "Loading production database dump"
  pg_restore -U "postgres" -d "muesli" -d muesli -n public -1 /muesli.prod.sql
else
  echo "Loading development database dump"
  psql -U "muesli-admin" -f /muesli.sql muesli
fi
