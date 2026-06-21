# ParkSight Deployment

## Quick Start (any Ubuntu VPS)

Zero-cost production on Oracle Cloud Always Free, any VPS, or your own machine:

```bash
# 1. Clone and deploy (auto-installs Docker, builds images, seeds data)
git clone https://github.com/arpita-rathwa/Parking_sight.git
cd Parking_sight

# For a VPS with a domain:
export DOMAIN=parksight.example.com
export ACME_EMAIL=admin@example.com
bash deploy/deploy.sh

# Or for local-only demo (no domain, no HTTPS):
bash deploy/deploy.sh --local
```

Default logins after seeding:
- **Admin**: `admin@parksight.com` / `admin123`
- **Operator**: `operator@parksight.com` / `operator123`
- **Reviewer**: `reviewer@parksight.com` / `reviewer123`
- **Planner**: `planner@parksight.com` / `planner123`
- **Officer**: `officer1@parksight.com` / `officer123`

## Zero-Cost Stack (Free Tier)

ParkSight runs on **$0/mo** infrastructure using free tiers:

| Service | Free Provider | Limits |
|---------|--------------|--------|
| VM / Compute | Oracle Cloud Always Free (ARM, 4 OCPU, 24GB RAM) — or any free VPS trial | Always free |
| Database | Supabase (PostGIS) — 500MB | 2 projects free |
| Redis | Upstash — 10K commands/day | 1 free DB |
| Kafka | Upstash — 10K messages/day | 1 free cluster |
| Container Registry | GitHub Container Registry (GHCR) | Unlimited public |
| HTTPS | Let's Encrypt (via Traefik) | Free |

### Setup with Managed Services (Supabase + Upstash)

```bash
# 1. Sign up at supabase.com → create project → copy connection string
# 2. Sign up at upstash.com → create Redis + Kafka → copy URLs

# 3. Deploy with free-tier override:
export DATABASE_URL="postgresql+psycopg2://postgres:PASSWORD@db.XXXXX.supabase.co:5432/postgres"
export REDIS_URL="rediss://:PASSWORD@XXXXX.upstash.io:6379"
export KAFKA_BOOTSTRAP_SERVERS="XXXX-XXXXX.upstash.io:9092"
export DOMAIN=parksight.example.com
export ACME_EMAIL=admin@example.com

cd backend
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  -f ../deploy/docker-compose.free.yml \
  up -d --build

docker compose run --rm seed
```

### Oracle Cloud ARM VM Setup

1. Create a free Oracle Cloud account (no credit card needed in some regions)
2. Create an ARM VM (VM.Standard.A1.Flex — 4 OCPUs, 24GB RAM, up to 200GB storage)
3. Allow ingress ports 80, 443 in the security list
4. SSH in and run:

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker ubuntu

# Log out and back in, then:
git clone https://github.com/arpita-rathwa/Parking_sight.git
cd Parking_sight
bash deploy/deploy.sh
```

## Local Development

```bash
# 1. Start all services
cd backend
docker compose up -d

# 2. Seed demo data (zones, users, violations, congestion scores)
docker compose run --rm seed

# 3. Access at http://localhost (Traefik routes to frontend)
```

## Production (EC2 via docker-compose)

```bash
cp backend/.env.example backend/.env
# Edit .env — set JWT_SECRET_KEY, CORS_ORIGINS, DOMAIN, etc.

cd backend
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
docker compose run --rm seed
```

## Production (AWS ECS Fargate)

Requires: ECR images pushed, RDS PostgreSQL, ElastiCache Redis, MSK Kafka.

```bash
# 1. Build and push images (CI/CD handles this)
cd backend
docker build -f Dockerfile.base -t $ECR/parksight:latest-dispatch .
docker build -f services/detection/Dockerfile -t $ECR/parksight:latest-detection .
# ... repeat for all services

# 2. Register task definition
aws ecs register-task-definition --cli-input-json file://deploy/ecs/task-definition.json

# 3. Create service
aws ecs create-service \
  --cluster parksight \
  --service-name parksight \
  --task-definition parksight \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[...],securityGroups=[...],assignPublicIp=ENABLED}"
```

## Environment Variables

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `JWT_SECRET_KEY` | — | **Yes** | 256-bit hex key for JWT signing |
| `CORS_ORIGINS` | `*` | No | Comma-separated allowed origins |
| `DOMAIN` | `parksight.local` | No | Traefik routing domain |
| `DATABASE_URL` | `postgresql://parksight:parksight@postgres:5432/parksight` | No | PostGIS connection string |
| `REDIS_URL` | `redis://redis:6379/0` | No | Redis connection string |
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka:9092` | No | Kafka bootstrap servers |
| `SENTRY_DSN` | — | No | Sentry error tracking DSN |
| `ACME_EMAIL` | `admin@parksight.local` | No | Let's Encrypt notification email |
| `DATA_RETENTION_VIOLATIONS_DAYS` | `90` | No | Auto-purge violations after N days |
| `DATA_RETENTION_SCORES_DAYS` | `90` | No | Auto-purge congestion scores after N days |

## Key Design Decisions

- **Traefik** handles HTTPS termination (auto Let's Encrypt), path-based routing to microservices, and the API dashboard.
- **CORS** is configured via `CORS_ORIGINS` env var (comma-separated) — locked down in production.
- **Alembic** runs `upgrade head` on every service startup — safe, idempotent, no separate migration step needed.
- **Sentry** is initialized in every service if `SENTRY_DSN` is set.
- **Health checks** on all services at `/api/v1/health` with dependency status reporting.
- **Seed data** is a one-time command (`docker compose run --rm seed`) — never run in production against existing data (truncates all tables).
- **Data cleanup**: `python scripts/cleanup.py` purges old records. Run as a daily cron job.
- **Model versioning**: Detection service supports shadow mode (A/B comparison), champion promoted via Kafka event.
