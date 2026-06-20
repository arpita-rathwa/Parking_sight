FROM python:3.12-slim

RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.common.txt requirements.scoring.txt ./
RUN pip install --no-cache-dir -r requirements.common.txt -r requirements.scoring.txt

COPY shared/ ./shared/
COPY services/scoring/ ./services/scoring/

CMD ["uvicorn", "services.scoring.main:app", "--host", "0.0.0.0", "--port", "8002"]
