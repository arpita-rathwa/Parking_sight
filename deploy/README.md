# ParkSight Deployment

## Local Development

```bash
# 1. Start all services
cd backend
docker compose up -d

# 2. Seed demo data (zones, users, violations, congestion scores)
docker compose run --rm seed

# 3. Access at http://localhost (Traefik routes to frontend)
#    Or directly: http://localhost:5173 (Vite dev server)
```

## Production (EC2 via docker-compose)

```bash
# 1. Configure environment
cp backend/.env.example backend/.env
# Edit .env — set JWT_SECRET_KEY, CORS_ORIGINS, DOMAIN, etc.

# 2. Deploy (CI/CD handles this automatically on main branch push)
#    Or manually:
cd backend
docker compose -f docker-compose.yml -f deploy/docker-compose.prod.yml up -d

# 3. Seed once (if first deploy)
docker compose run --rm seed
```

## Production (AWS ECS Fargate)

Requires: ECR images pushed, RDS PostgreSQL, ElastiCache Redis, MSK Kafka.

```bash
# 1. Build and push images (CI/CD does this)
cd backend
docker build -f Dockerfile.shared -t $ECR/parksight:latest-queue .
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

# 4. Set JWT_SECRET_KEY in AWS Secrets Manager and reference in task definition
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

## Key Design Decisions

- **Traefik** handles HTTPS termination (auto Let's Encrypt), path-based routing to microservices, and the API dashboard.
- **CORS** is configured via `CORS_ORIGINS` env var (comma-separated) — locked down in production.
- **Alembic** runs `upgrade head` on every service startup — safe, idempotent, no separate migration step needed.
- **Sentry** is initialized in every service if `SENTRY_DSN` is set.
- **Health checks** on all services at `/api/v1/health`.
- **Seed data** is a one-time command (`docker compose run --rm seed`) — never run in production against existing data (truncates all tables).
