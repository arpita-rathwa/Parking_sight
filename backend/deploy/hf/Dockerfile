FROM node:20-alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    build-essential \
    postgresql-15 \
    postgresql-15-postgis-3 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "uvicorn[standard]==0.30.6"

COPY backend/requirements.common.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY backend/ /app/backend/
COPY frontend/dist /var/www/html

COPY backend/deploy/hf/nginx.conf /etc/nginx/sites-enabled/default

COPY backend/deploy/hf/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY backend/deploy/hf/start.sh /app/start.sh

RUN chmod +x /app/start.sh && \
    mkdir -p /data && \
    chown -R postgres:postgres /data

ENV PYTHONPATH=/app/backend

WORKDIR /app

EXPOSE 7860

CMD ["/app/start.sh"]
