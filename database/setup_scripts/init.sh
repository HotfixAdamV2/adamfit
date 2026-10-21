#!/usr/bin/env bash
# Runs once, the first time the container starts with an empty data volume.
# Executes the SQL files in /shared_dir (bind-mounted from ./shared_dir) in order.
set -euo pipefail

SQL_DIR=/shared_dir

psql -v ON_ERROR_STOP=1 --username postgres --dbname postgres \
    -f "$SQL_DIR/01_create_database.sql"

psql -v ON_ERROR_STOP=1 --username postgres --dbname fitness \
    -f "$SQL_DIR/02_create_schema.sql"

psql -v ON_ERROR_STOP=1 --username postgres --dbname fitness \
    -v master_password="$MASTER_USR_PASSWORD" \
    -f "$SQL_DIR/03_create_roles_and_security.sql"
