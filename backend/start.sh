#!/bin/sh
set -eu

PORT="${PORT:-8000}"

if [ "${RENDER:-false}" = "true" ]; then
  : "${DATABASE_URL:?DATABASE_URL is required on Render}"
  : "${DATABASE_URL_UNPOOLED:?DATABASE_URL_UNPOOLED is required on Render}"
fi

python migrate.py
if [ "${SEED_DEMO_DATA:-false}" = "true" ]; then
  python seed.py
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
