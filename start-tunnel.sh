#!/bin/sh
# Start the AutoScoring stack and expose the backend on a public HTTPS URL.
#
#   ./start-tunnel.sh
#
# Uses a Cloudflare quick tunnel. The hostname is random and changes on every
# start, so VITE_API_URL in Vercel has to be updated and redeployed each time.
# See the note printed at the end.
set -eu

cd "$(dirname "$0")"

CLOUDFLARED=".tools/cloudflared"
LOG=".tools/tunnel.log"

if [ ! -x "$CLOUDFLARED" ]; then
  echo "cloudflared not found. Downloading it..."
  mkdir -p .tools
  ARCH=$(uname -m)
  case "$ARCH" in
    arm64) CF_ARCH="darwin-arm64" ;;
    x86_64) CF_ARCH="darwin-amd64" ;;
    *) echo "Unsupported architecture: $ARCH" >&2; exit 1 ;;
  esac
  curl -fsSL -o .tools/cf.tgz \
    "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-${CF_ARCH}.tgz"
  tar -xzf .tools/cf.tgz -C .tools
  rm -f .tools/cf.tgz
  chmod +x "$CLOUDFLARED"
fi

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
# keeps the old hostname claimed and the new one then fails to register.
pkill -f "localtunnel --port" 2>/dev/null || true
pkill -f "cloudflared tunnel" 2>/dev/null || true
sleep 2
: > "$LOG"
nohup "$CLOUDFLARED" tunnel --url http://localhost:8000 --no-autoupdate >"$LOG" 2>&1 &
TUNNEL_PID=$!

URL=""
i=0
while [ "$i" -lt 40 ]; do
  URL=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$LOG" | grep -v '^https://api\.' | head -1 || true)
  if [ -n "$URL" ]; then
    break
  fi
  i=$((i + 1))
  sleep 1
done

if [ -z "$URL" ]; then
  echo "Could not determine the tunnel URL. See $LOG" >&2
  exit 1
fi

i=0
while [ "$i" -lt 20 ]; do
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

ACTION REQUIRED: quick tunnels get a random hostname on every start, and Vercel
bakes the API URL into the build. Set this in your Vercel project
(Settings -> Environment Variables, Type: Config), then redeploy:

  VITE_API_URL=$URL/api

This is the only manual step, and it is needed once per start.
EOF

wait "$TUNNEL_PID"
