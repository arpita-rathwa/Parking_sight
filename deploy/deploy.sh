#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────
#  ParkSight — Zero-cost deploy script
#  Works on: Oracle Cloud (free ARM), any Ubuntu 22.04+ VPS
# ─────────────────────────────────────────────────────────────
#
# Usage:
#   export DOMAIN=parksight.example.com
#   export ACME_EMAIL=admin@example.com
#   bash deploy/deploy.sh
#
# Or for local-only demo (no domain):
#   bash deploy/deploy.sh --local
#
# Optional managed services (Supabase + Upstash):
#   export DATABASE_URL=postgresql://...
#   export REDIS_URL=rediss://...
#   export KAFKA_BOOTSTRAP_SERVERS=...
#   bash deploy/deploy.sh --free-tier
#

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[✗]${NC} $1"; }

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

# ── Parse args ──────────────────────────────────────────────
LOCAL_MODE=false
FREE_TIER=false
for arg in "$@"; do
  case "$arg" in
    --local) LOCAL_MODE=true ;;
    --free-tier) FREE_TIER=true ;;
  esac
done

# ── Pre-flight checks ───────────────────────────────────────
check_command() {
  if ! command -v "$1" &>/dev/null; then
    err "$1 is required but not installed."
    exit 1
  fi
}

check_command docker
check_command curl

# ── Install Docker Compose if missing ───────────────────────
if ! docker compose version &>/dev/null; then
  warn "Docker Compose v2 not found — installing..."
  DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
  mkdir -p "$DOCKER_CONFIG/cli-plugins"
  curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
    -o "$DOCKER_CONFIG/cli-plugins/docker-compose"
  chmod +x "$DOCKER_CONFIG/cli-plugins/docker-compose"
  log "Docker Compose installed"
fi

# ── Create .env if missing ───────────────────────────────────
if [ ! -f backend/.env ]; then
  cp backend/.env.example backend/.env
  JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || \
               openssl rand -hex 32)
  if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s/change-me-in-production/$JWT_SECRET/" backend/.env
  else
    sed -i "s/change-me-in-production/$JWT_SECRET/" backend/.env
  fi
  log ".env created with random JWT_SECRET_KEY"
else
  warn ".env already exists — skipping"
fi

# ── Configure domain ────────────────────────────────────────
if [ "$LOCAL_MODE" = true ]; then
  warn "Local mode — no HTTPS, accessible at http://$(curl -s ifconfig.me 2>/dev/null || echo 'localhost')"
elif [ -n "${DOMAIN:-}" ]; then
  log "Domain: $DOMAIN"
  if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s/parksight.local/$DOMAIN/g" backend/.env 2>/dev/null || true
  else
    sed -i "s/parksight.local/$DOMAIN/g" backend/.env 2>/dev/null || true
  fi
  if [ -n "${ACME_EMAIL:-}" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
      sed -i '' "s/admin@parksight.local/$ACME_EMAIL/g" backend/.env 2>/dev/null || true
    else
      sed -i "s/admin@parksight.local/$ACME_EMAIL/g" backend/.env 2>/dev/null || true
    fi
  fi
else
  warn "DOMAIN not set — using parksight.local (local access only)"
fi

# ── Build and start services ────────────────────────────────
cd backend

COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"
if [ "$FREE_TIER" = true ]; then
  COMPOSE_FILES="$COMPOSE_FILES -f ../deploy/docker-compose.free.yml"
fi

log "Building and starting ParkSight..."
docker compose $COMPOSE_FILES up -d --build

# ── Wait for services to be healthy ─────────────────────────
log "Waiting for services to be ready..."
sleep 10

# ── Seed data ───────────────────────────────────────────────
warn "About to seed demo data — this will truncate all existing data!"
read -rp "Continue? [y/N] " confirm
if [[ "$confirm" =~ ^[Yy]$ ]]; then
  log "Seeding demo data..."
  docker compose run --rm seed
  log "Seed complete"
fi

# ── Done ────────────────────────────────────────────────────
echo ""
log "ParkSight is running!"
if [ "$LOCAL_MODE" = true ]; then
  echo "   Frontend:  http://localhost"
elif [ -n "${DOMAIN:-}" ]; then
  echo "   Frontend:  https://$DOMAIN"
  echo "   Traefik:   https://traefik.$DOMAIN (dashboard)"
fi
echo ""
echo "Default logins:"
echo "   Admin:    admin@parksight.com / admin123"
echo "   Operator: operator@parksight.com / operator123"
echo "   Reviewer: reviewer@parksight.com / reviewer123"
echo "   Planner:  planner@parksight.com / planner123"
echo "   Officer:  officer1@parksight.com / officer123"
echo ""
echo "To stop:  docker compose -f backend/docker-compose.yml down"
echo "To view logs:  docker compose -f backend/docker-compose.yml logs -f"
