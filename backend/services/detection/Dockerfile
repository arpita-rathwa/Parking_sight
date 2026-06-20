FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.base.txt requirements.detection.txt ./
RUN pip install --no-cache-dir -r requirements.base.txt -r requirements.detection.txt

COPY shared/ ./shared/
COPY services/detection/ ./services/detection/

CMD ["uvicorn", "services.detection.main:app", "--host", "0.0.0.0", "--port", "8001"]
