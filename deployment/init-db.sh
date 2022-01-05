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
