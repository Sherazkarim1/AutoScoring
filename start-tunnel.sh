#!/bin/sh
# Start the AutoScoring stack and expose the backend on a public HTTPS URL.
#
#   ./start-tunnel.sh
#
# Prints the public URL. Cloudflare quick tunnels pick a random hostname on every
# start, so update the VITE_API_URL environment variable in Vercel when it changes.
set -eu

cd "$(dirname "$0")"

CLOUDFLARED=".tools/cloudflared"
LOG=".tools/tunnel.log"
LOCAL_ORIGINS="http://localhost:5173,http://localhost:5174,http://localhost:3000"

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

# Start a fresh quick tunnel, replacing any previous one.
pkill -f "cloudflared tunnel" 2>/dev/null || true
sleep 1
: > "$LOG"
"$CLOUDFLARED" tunnel --url http://localhost:8000 --no-autoupdate >"$LOG" 2>&1 &
TUNNEL_PID=$!

URL=""
i=0
while [ "$i" -lt 30 ]; do
  URL=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$LOG" | head -1 || true)
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

# Keep CORS in sync with the new public frontend origin.
if [ -f .env ] && grep -q '^CORS_ORIGINS=' .env; then
  if ! grep -q 'auto-scoring-upyy.vercel.app' .env; then
    echo "Note: add your Vercel frontend origin to CORS_ORIGINS in .env if it changes."
  fi
fi

# Record the live URL so tooling (and you) can read it without scrolling logs.
printf '%s\n' "$URL" > .tools/tunnel-url

cat <<EOF

AutoScoring is live.

  Frontend (Vercel) : https://auto-scoring-upyy.vercel.app
  Backend API       : $URL
  API docs          : $URL/docs

ACTION REQUIRED: the Vercel frontend still points at the previous tunnel URL.
Open your Vercel project -> Settings -> Environment Variables, set

  VITE_API_URL=$URL/api

then redeploy the latest deployment (Deployments -> ... -> Redeploy).
Vite bakes this value in at build time, so saving the variable alone is not enough.

Press Ctrl+C to stop the tunnel (the backend keeps running).
EOF

wait "$TUNNEL_PID"
