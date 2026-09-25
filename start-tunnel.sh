#!/bin/sh
# Start the AutoScoring stack and expose the backend on a stable public HTTPS URL.
#
#   ./start-tunnel.sh
#
# The URL is fixed (see SUBDOMAIN below), so it survives restarts and the
# VITE_API_URL value in Vercel only has to be set once.
set -eu

cd "$(dirname "$0")"

# Claiming a fixed subdomain needs no account and no card. If someone else has
# already taken it, change SUBDOMAIN to any unused word.
SUBDOMAIN="autoscoring-kiu"
URL="https://${SUBDOMAIN}.loca.lt"
LOG=".tools/tunnel.log"

echo "Starting database and backend..."
docker compose up -d db backend

echo "Waiting for the API to become healthy..."
i=0
while [ "$i" -lt 40 ]; do
  if curl -sf -m 5 http://localhost:8000/api/health >/dev/null 2>&1; then
    break
  fi
  i=$((i + 1))
  sleep 3
done

if ! curl -sf -m 5 http://localhost:8000/api/health >/dev/null 2>&1; then
  echo "Backend did not become healthy. Check: docker compose logs backend" >&2
  exit 1
fi
echo "Backend is healthy."

# Start a fresh tunnel, replacing any previous one. Kill by the full command
# line: "localtunnel" also matches this script's own grep, and the old
# cloudflared must be gone before the subdomain can be re-registered.
pkill -f "cloudflared tunnel" 2>/dev/null || true
pkill -f "localtunnel --port" 2>/dev/null || true
sleep 3
: > "$LOG"
npx --yes localtunnel --port 8000 --subdomain "$SUBDOMAIN" >"$LOG" 2>&1 &
TUNNEL_PID=$!

i=0
while [ "$i" -lt 40 ]; do
  if curl -sf -m 5 "$URL/api/health" >/dev/null 2>&1; then
    break
  fi
  i=$((i + 1))
  sleep 2
done

if ! curl -sf -m 8 "$URL/api/health" >/dev/null 2>&1; then
  echo "Tunnel did not come up at $URL. See $LOG" >&2
  exit 1
fi

# Keep CORS in sync with the public frontend origin.
if [ -f .env ] && grep -q '^CORS_ORIGINS=' .env; then
  if ! grep -q 'auto-scoring-upyy.vercel.app' .env; then
    echo "Note: add your Vercel frontend origin to CORS_ORIGINS in .env if it changes."
  fi
fi

printf '%s\n' "$URL" > .tools/tunnel-url

cat <<EOF

AutoScoring is live.

  Frontend (Vercel) : https://auto-scoring-upyy.vercel.app
  Backend API       : $URL
  API docs          : $URL/docs

This URL is fixed. Vercel only needs VITE_API_URL=$URL/api set once.

Press Ctrl+C to stop the tunnel (the backend keeps running).
EOF

wait "$TUNNEL_PID"
