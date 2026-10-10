#!/bin/sh
# Запуск контейнера: приложение слушает порт из PORT (по умолчанию 8000).
# Миграции и начальные данные включаются флагами: без БД контейнер всё равно стартует и отвечает на /health.
set -eu

PORT="${PORT:-8000}"

if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
  echo "Применяю миграции"
  alembic upgrade head
fi

if [ "${SEED_ON_START:-false}" = "true" ]; then
  # Типы событий создаются обычными запросами к уже запущенному серверу (повтор безопасен).
  (
    export API_URL="http://127.0.0.1:${PORT}"
    for _ in $(seq 1 30); do
      if python -m app.seed; then
        exit 0
      fi
      sleep 2
    done
    echo "Начальные данные не созданы" >&2
  ) &
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
