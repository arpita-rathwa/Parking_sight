FROM python:3.12-slim

RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .
RUN pip install --no-cache-dir -e ".[forecast]"

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8007"]
