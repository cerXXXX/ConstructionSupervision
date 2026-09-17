#!/bin/bash
# Создание баз и ролей: по базе на сервис, роль имеет права только на свою базу.
# Так граница между сервисами защищена СУБД, а не договорённостью (ADR-0003).
# Скрипт выполняется образом postgres один раз, при первой инициализации тома.
set -euo pipefail

create_service_db() {
    local db="$1" user="$2" password="$3"

    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres <<-SQL
        CREATE ROLE ${user} WITH LOGIN PASSWORD '${password}';
        CREATE DATABASE ${db} OWNER ${user};
        REVOKE ALL ON DATABASE ${db} FROM PUBLIC;
        GRANT CONNECT, CREATE ON DATABASE ${db} TO ${user};
SQL

    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "${db}" <<-SQL
        CREATE EXTENSION IF NOT EXISTS pgcrypto;
        ALTER SCHEMA public OWNER TO ${user};
SQL

    echo "база ${db} и роль ${user} созданы"
}

create_service_db plandb     plan_user     "${PLAN_DB_PASSWORD}"
create_service_db sitedb     site_user     "${SITE_DB_PASSWORD}"
create_service_db analysisdb analysis_user "${ANALYSIS_DB_PASSWORD}"
