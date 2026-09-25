#!/bin/sh
# Start the AutoScoring stack and expose the backend on a stable public HTTPS URL.
#
#   ./start-tunnel.sh
#
# The subdomain is fixed, so the URL survives restarts and VITE_API_URL in Vercel
# only has to be set once. The frontend sends a "bypass-tunnel-reminder" header
# (see frontend/src/api.ts) to skip localtunnel's browser interstitial.
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

# Replace any previous tunnel. Match the real command line: a leftover tunnel
# keeps the subdomain claimed and the new one then fails with "Tunnel not found".
pkill -f "cloudflared tunnel" 2>/dev/null || true
pkill -f "localtunnel --port" 2>/dev/null || true
sleep 2
: > "$LOG"
nohup npx --yes localtunnel --port 8000 --subdomain "$SUBDOMAIN" >"$LOG" 2>&1 &
TUNNEL_PID=$!

# Probe the way a browser would, including the interstitial bypass header.
i=0
while [ "$i" -lt 40 ]; do
  if curl -sf -m 5 -H "bypass-tunnel-reminder: true" "$URL/api/health" >/dev/null 2>&1; then
    break
  fi
  i=$((i + 1))
  sleep 2
done

if ! curl -sf -m 8 -H "bypass-tunnel-reminder: true" "$URL/api/health" >/dev/null 2>&1; then
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
