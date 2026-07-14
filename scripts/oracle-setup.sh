#!/usr/bin/env bash
# Run on the Oracle Cloud VM after SSH (Ubuntu).
# Usage: bash scripts/oracle-setup.sh
set -euo pipefail

echo "==> Installing Docker (Ubuntu)"
sudo apt-get update -y
sudo apt-get install -y ca-certificates curl git
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker "$USER" || true

echo "==> Opening host firewall for API (iptables)"
# Oracle Ubuntu images often need this in addition to the console Security List
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT || true
sudo netfilter-persistent save 2>/dev/null || sudo iptables-save | sudo tee /etc/iptables/rules.v4 >/dev/null || true

echo "==> Done. Log out and SSH back in so Docker group applies, then:"
echo "  cd ~/AutoScoring"
echo "  cp .env.example .env && nano .env"
echo "  docker compose -f docker-compose.oracle.yml --env-file .env up --build -d"
