#!/bin/sh
set -eu

PORT="${PORT:-8000}"

# Required in any hosted environment (Hugging Face Space, Render, etc.).
if [ -n "${HF_SPACE_ID:-}" ] || [ -n "${RENDER:-}" ] || [ "${REQUIRE_DB:-false}" = "true" ]; then
  : "${DATABASE_URL:?DATABASE_URL is required in hosted environments}"
fi

python migrate.py
if [ "${SEED_DEMO_DATA:-false}" = "true" ]; then
  python seed.py
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
