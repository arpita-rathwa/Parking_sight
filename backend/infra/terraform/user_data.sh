#!/bin/bash
set -e

apt update
apt install -y docker.io docker-compose-v2 git

cd /opt
git clone https://github.com/arpita-rathwa/Parking_sight.git
cd Parking_sight/backend

cat > .env << EOF
DATABASE_URL=${db_url}
REDIS_URL=${redis_url}
KAFKA_BOOTSTRAP_SERVERS=${kafka_servers}
SENTRY_DSN=${sentry_dsn}
JWT_SECRET_KEY=$(openssl rand -hex 32)
EOF

docker compose up -d
