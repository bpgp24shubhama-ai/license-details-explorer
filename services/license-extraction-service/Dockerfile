FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY services/license-extraction-service/requirements.txt /app/services/license-extraction-service/requirements.txt
RUN pip install --no-cache-dir -r /app/services/license-extraction-service/requirements.txt

COPY shared /app/shared
COPY services/license-extraction-service /app/services/license-extraction-service

WORKDIR /app/services/license-extraction-service
ENV PYTHONPATH=/app

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${UVICORN_PORT:-8001}"]
