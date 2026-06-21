#!/bin/bash
set -e

PGVERSION=${PGVERSION:-16}
PGDATA=/data/postgres
PGUSER=postgres
PGPORT=5432

export PGDATA PGUSER PGPORT
export PATH="/usr/lib/postgresql/$PGVERSION/bin:$PATH"

init_pg() {
    echo "Initializing PostgreSQL $PGVERSION..."
    mkdir -p "$PGDATA"
    chown -R postgres:postgres "$PGDATA"

    if [ ! -f "$PGDATA/PG_VERSION" ]; then
        su - postgres -c "initdb -D $PGDATA"
        echo "host all all 127.0.0.1/32 trust" >> "$PGDATA/pg_hba.conf"
        echo "host all all ::1/128 trust" >> "$PGDATA/pg_hba.conf"
    fi
}

start_pg() {
    echo "Starting PostgreSQL..."
    su - postgres -c "pg_ctl -D $PGDATA -l /tmp/pg.log start"
    for i in $(seq 1 30); do
        if su - postgres -c "psql -c 'SELECT 1'" > /dev/null 2>&1; then
            echo "PostgreSQL is ready"
            return 0
        fi
        sleep 1
    done
    echo "PostgreSQL failed to start"
    exit 1
}

setup_db() {
    echo "Setting up database..."
    su - postgres -c "psql -tc \"SELECT 1 FROM pg_database WHERE datname='parksight'\" | grep -q 1 || psql -c 'CREATE DATABASE parksight'"
    su - postgres -c "psql -d parksight -c 'CREATE EXTENSION IF NOT EXISTS postgis'"
    su - postgres -c "psql -d parksight -c \"CREATE USER parksight WITH PASSWORD 'parksight'\" 2>/dev/null || true"
    su - postgres -c "psql -d parksight -c 'GRANT ALL PRIVILEGES ON DATABASE parksight TO parksight'"
    su - postgres -c "psql -d parksight -c 'GRANT ALL ON SCHEMA public TO parksight'"
}

run_migrations() {
    echo "Running migrations..."
    export DATABASE_URL="postgresql+psycopg2://parksight:parksight@localhost:5432/parksight"
    export PYTHONPATH="/app/backend"
    cd /app/backend
    python -c "
from shared.models.database import Base, get_engine
engine = get_engine()
Base.metadata.create_all(bind=engine)
from alembic.config import Config
from alembic import command
import os
alembic_cfg = Config('alembic.ini')
alembic_cfg.set_main_option('sqlalchemy.url', os.environ['DATABASE_URL'])
command.stamp(alembic_cfg, 'head')
print('Migrations complete')
"
}

seed_data() {
    echo "Seeding data..."
    export DATABASE_URL="postgresql+psycopg2://parksight:parksight@localhost:5432/parksight"
    export PYTHONPATH="/app/backend"
    cd /app/backend
    python scripts/seed.py
}

seed_marker=/data/.seed_done
if [ ! -f "$seed_marker" ]; then
    echo "First run — initializing database..."
    init_pg
    start_pg
    setup_db
    run_migrations
    seed_data
    touch "$seed_marker"
    echo "Seed complete"
    su - postgres -c "pg_ctl -D $PGDATA stop" || true
    sleep 2
fi

echo "Starting supervisord..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
