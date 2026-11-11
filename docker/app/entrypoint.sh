#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."
until nc -z postgres 5432; do
  sleep 1
done

python manage.py migrate_schemas --shared --noinput
python manage.py collectstatic --noinput
python manage.py bootstrap_public_tenant

exec "$@"

