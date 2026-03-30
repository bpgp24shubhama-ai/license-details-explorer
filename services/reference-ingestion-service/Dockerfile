FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY services/reference-ingestion-service/requirements.txt /app/services/reference-ingestion-service/requirements.txt
RUN pip install --no-cache-dir -r /app/services/reference-ingestion-service/requirements.txt

COPY shared /app/shared
COPY services/reference-ingestion-service /app/services/reference-ingestion-service

WORKDIR /app/services/reference-ingestion-service
ENV PYTHONPATH=/app

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${UVICORN_PORT:-8002}"]
