#!/bin/bash
# Script to create test database in PostgreSQL

set -e

# Wait for PostgreSQL to be ready
until PGPASSWORD=crm_password psql -h db -U crm_user -d crm_db -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - creating test database"

# Create test database if it doesn't exist
PGPASSWORD=crm_password psql -h db -U crm_user -d crm_db <<-EOSQL
    SELECT 'CREATE DATABASE crm_test'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'crm_test')\gexec
EOSQL

echo "Test database ready"