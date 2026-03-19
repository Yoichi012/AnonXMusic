#!/bin/bash
set -e

echo "========================================="
echo "  TASK 1: Fix Docker (RHEL 10 issue)"
echo "========================================="

sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "iptables": false,
  "ip6tables": false
}
EOF

echo "[OK] daemon.json written:"
sudo cat /etc/docker/daemon.json

sudo systemctl restart docker
echo "[OK] Docker restarted"

echo ""
echo "Docker containers:"
sudo docker ps
echo ""

echo "========================================="
echo "  TASK 2: Start Cobalt Docker container"
echo "========================================="

cd ~/AnonXMusic

# Ensure docker dir and compose file exist
mkdir -p docker
cat > docker/cobalt-compose.yml <<COMPEOF
version: "3.8"
services:
  cobalt-api:
    image: ghcr.io/imputnet/cobalt:10
    restart: unless-stopped
    ports:
      - "127.0.0.1:9000:9000"
    environment:
      API_URL: "http://127.0.0.1:9000"
      CORS_WILDCARD: "0"
COMPEOF

echo "[OK] cobalt-compose.yml created"
sudo docker compose -f docker/cobalt-compose.yml up -d
echo "[OK] Cobalt container started"

echo ""
echo "Docker containers:"
sudo docker ps
echo ""

echo "========================================="
echo "  TASK 3: Verify Cobalt working"
echo "========================================="
echo "Waiting 8 seconds for Cobalt to start..."
sleep 8

COBALT_RESP=$(curl -s -X POST http://127.0.0.1:9000/api/json \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"url":"https://youtu.be/dQw4w9WgXcQ","isAudioOnly":true}')

echo "Cobalt API response:"
echo "$COBALT_RESP"

if echo "$COBALT_RESP" | grep -q '"status"'; then
  echo "[OK] Cobalt is working!"
else
  echo "[WARN] Cobalt may not be ready yet. Response above."
fi
echo ""

echo "========================================="
echo "  TASK 4: Install Python dependencies"
echo "========================================="
cd ~/AnonXMusic
pip3 install -U pip 2>&1 | tail -3
pip3 install -U -r requirements.txt 2>&1 | tail -10
echo "[OK] Python dependencies installed"
echo ""

echo "========================================="
echo "  TASK 5: Setup .env file"
echo "========================================="
cd ~/AnonXMusic

if [ ! -f .env ]; then
  cp sample.env .env
  echo "[OK] Created .env from sample.env"
else
  echo "[OK] .env already exists"
fi

# Ensure COBALT_URL and JIOSAAVN_API_URL exist
if ! grep -q "COBALT_URL" .env; then
  echo "COBALT_URL=http://127.0.0.1:9000" >> .env
  echo "[OK] Added COBALT_URL to .env"
else
  echo "[OK] COBALT_URL already in .env"
fi

if ! grep -q "JIOSAAVN_API_URL" .env; then
  echo "JIOSAAVN_API_URL=https://saavn.dev" >> .env
  echo "[OK] Added JIOSAAVN_API_URL to .env"
else
  echo "[OK] JIOSAAVN_API_URL already in .env"
fi

echo ""
echo "Current .env contents:"
cat .env
echo ""

echo "========================================="
echo "  ALL TASKS (1-5) COMPLETE!"
echo "========================================="
echo "Next: Run 'screen -S anonxmusic' then 'bash start' to start the bot."
