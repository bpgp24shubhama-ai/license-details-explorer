# BMLS Platform

Enterprise-grade FastAPI platform for commercial license extraction and reference ingestion.

## Services

1. `license-extraction-service` (port 8001)
2. `reference-ingestion-service` (port 8002)

## Quick start

1. Copy `.env.example` to `.env` and set real API keys.
2. Start all services:

```bash
cd deployment
docker compose up --build
```

1. Open API docs:

- Extraction API: `http://localhost:8001/docs`
- Ingestion API: `http://localhost:8002/docs`

## Project structure

- `services/license-extraction-service` - PDF parsing, OCR fallback, translation, GPT extraction, vector mapping
- `services/reference-ingestion-service` - Excel validation, normalization, embeddings, pgvector indexing
- `shared` - shared contracts, logging, config, and exception handling
- `deployment` - compose setup and DB initialization scripts
- `docs` - sample API requests and sample extraction JSON

## Testing

Run tests per service:

```bash
cd services/license-extraction-service
pytest -q

cd ../reference-ingestion-service
pytest -q
```
