#!/bin/sh
# Миграции применяются на старте контейнера — так состояние схемы всегда
# соответствует коду. Отключается переменной RUN_MIGRATIONS=false.
set -e

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    echo "применяю миграции..."
    PYTHONPATH=. alembic upgrade head
fi

exec "$@"
