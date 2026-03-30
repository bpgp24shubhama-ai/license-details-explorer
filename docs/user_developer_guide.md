# User and Developer Guide

This guide explains how to use and develop the BMLS platform in this repository.

## 1. What This Application Does

BMLS is a two-service FastAPI platform for:

- Extracting structured license data from PDF documents.
- Ingesting and validating reference master data from Excel.
- Using pgvector similarity search to map imperfect extracted values to canonical values.

## 2. Service Map

| Service | Port | Purpose |
| --- | --- | --- |
| `license-extraction-service` | 8001 | PDF text extraction, OCR fallback, translation, field extraction, vector mapping |
| `reference-ingestion-service` | 8002 | Excel ingestion, normalization, embedding generation, upsert/reload, validation |
| `postgres` (pgvector) | 5432 | Stores reference vectors, audit records, and extraction history |

## 3. End-to-End Flow

1. Upload reference masters (for example `location`, `license_category`) through the ingestion API.
2. The ingestion service normalizes values and stores embeddings in `reference_master`.
3. Upload a license PDF through extraction API.
4. Extraction pipeline:
   - Native PDF text extraction.
   - OCR fallback for pages with empty text.
   - Language detection and translation to English.
   - Structured field extraction.
   - Vector mapping against reference master data.
5. Response returns extracted fields, mapped values, similarity scores, and trace metadata.

## 4. Prerequisites

### Runtime

- Docker Desktop (recommended)
- Or Python 3.12+ for local service execution
- PostgreSQL 16+ with `pgvector`

### Local extraction-only requirement

- Tesseract OCR installed if you use `pytesseract` provider locally

## 5. Quick Start for Users (Docker)

1. From repository root, keep `.env.example` as-is for sandbox usage or copy to `.env` for your own values.
2. Start platform:

```bash
cd deployment
docker compose up --build
```

3. Open API docs:

- Extraction docs: http://localhost:8001/docs
- Ingestion docs: http://localhost:8002/docs

4. Check health endpoints:

- `GET http://localhost:8001/health`
- `GET http://localhost:8002/health`

## 6. Common User Operations

### 6.1 Upload reference master Excel

```bash
curl -X POST "http://localhost:8002/api/v1/references/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@./samples/reference-master.xlsx" \
  -F "reference_type=location" \
  -F "mode=reload"
```

### 6.2 Extract a license PDF

```bash
curl -X POST "http://localhost:8001/api/v1/extractions" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@./samples/fssai-license.pdf" \
  -F "ocr_provider=pytesseract" \
  -F "document_type=fssai"
```

### 6.3 Validate a noisy lookup value

```bash
curl -X POST "http://localhost:8002/api/v1/references/validate" \
  -H "Content-Type: application/json" \
  -d '{"reference_type": "location", "value": "mumabi"}'
```

## 7. API Contract Summary

### 7.1 Extraction API

- Endpoint: `POST /api/v1/extractions`
- Content type: `multipart/form-data`
- Form fields:
  - `file` (required, PDF)
  - `ocr_provider` (optional): `pytesseract`, `gpt-5-mini`, `gemma-3-4b`
  - `document_type` (optional)

Returns structured JSON including:

- Base fields: `license_number`, `license_name`, `license_category`, `location`, dates, status, etc.
- Mapping fields: `mapped_license_category`, `mapped_location`
- Similarity fields: `mapped_license_category_similarity`, `mapped_location_similarity`
- Trace fields: `request_id`, `ocr_used`, `ocr_provider`, `processing_time_ms`, `source_snippets`

### 7.2 Reference Ingestion API

- `POST /api/v1/references/upload`
  - Form fields: `file` (Excel), `reference_type`, `mode` (`reload` or `upsert`)
- `POST /api/v1/references/reindex`
  - Body: `{ "reference_type": "..." }`
- `POST /api/v1/references/validate`
  - Body: `{ "reference_type": "...", "value": "..." }`

## 8. Local Developer Setup (Without Docker for APIs)

You can run Postgres via Docker and run APIs directly on host for faster iteration.

### 8.1 Start only Postgres

```bash
cd deployment
docker compose up -d postgres
```

### 8.2 Configure environment variables

Minimum required variables:

- `DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/bmls`
- `OPENAI_API_KEY=` (optional in dev; see fallback notes)
- `SIMILARITY_THRESHOLD=0.70`

PowerShell example:

```powershell
$env:DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/bmls"
$env:OPENAI_API_KEY = ""
$env:SIMILARITY_THRESHOLD = "0.70"
```

If using local Tesseract on Windows:

```powershell
$env:TESSERACT_CMD = "C:\Program Files\Tesseract-OCR\tesseract.exe"
```

### 8.3 Run reference-ingestion-service

```powershell
cd services/reference-ingestion-service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PYTHONPATH = (Resolve-Path ../..).Path
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

### 8.4 Run license-extraction-service

```powershell
cd services/license-extraction-service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PYTHONPATH = (Resolve-Path ../..).Path
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

## 9. Environment Variables

Core settings come from shared `BaseServiceSettings`.

| Variable | Purpose | Default |
| --- | --- | --- |
| `ENV` | Runtime environment label | `dev` |
| `LOG_LEVEL` | Log verbosity | `INFO` |
| `DATABASE_URL` | Async SQLAlchemy DB URL | `postgresql+asyncpg://postgres:postgres@localhost:5432/bmls` |
| `SIMILARITY_THRESHOLD` | Minimum similarity for accepted mapping | `0.70` |
| `OPENAI_API_KEY` | Enables remote extraction/embedding/translation | empty |
| `OPENAI_BASE_URL` | OpenAI-compatible endpoint | `https://api.openai.com/v1` |
| `EXTRACTION_MODEL` | Chat model for structured extraction | `gpt-5-mini` |
| `OCR_MODEL` | Model for GPT OCR provider | `gpt-5-mini` |
| `TRANSLATION_MODEL` | Model for translation provider | `gpt-5-mini` |
| `EMBEDDING_MODEL` | Model for vector embeddings | `text-embedding-3-small` |
| `DEFAULT_OCR_PROVIDER` | Default OCR provider | `pytesseract` |
| `TESSERACT_CMD` | Path to Tesseract binary | `/usr/bin/tesseract` |

## 10. Database Schema (Operational)

Initialized by `deployment/db/001_init.sql`:

- `reference_master`
  - Canonical values plus embeddings (`VECTOR(1536)`)
  - Unique key: `(reference_type, normalized_value)`
- `processing_audit`
  - Request-level success/failure audit with payload
- `extraction_history`
  - Final extraction payload snapshots for traceability

## 11. Fallback Behavior in Dev Mode

If `OPENAI_API_KEY` is empty:

- Extraction provider uses regex fallback for a minimal field set.
- Embedding provider returns deterministic pseudo-embeddings (stable but not semantic).
- Translation provider returns original text unchanged.

This is useful for local tests but not for production quality extraction/mapping.

## 12. Testing Guide

Run tests per service:

```bash
cd services/license-extraction-service
pytest -q

cd ../reference-ingestion-service
pytest -q
```

Run targeted test groups:

```bash
pytest -q app/tests/unit
pytest -q app/tests/integration
```

Current test focus areas include:

- Extraction API response contract.
- OCR and translation behavior.
- LLM fallback extraction formatting.
- Excel parsing and validation.
- Ingestion API and lookup validation endpoints.

## 13. Error and Observability Conventions

### Error envelope

All services return standardized error JSON:

- `code`: machine-readable error code
- `detail`: human-readable detail
- `correlation_id`: request correlation ID

### Correlation IDs

- Incoming `X-Correlation-ID` is propagated.
- If missing, middleware generates one.
- Response always includes `X-Correlation-ID` header.
- JSON logs include `service` and `correlation_id` fields.

## 14. Extension Playbook

### Add a new OCR provider

1. Implement `OCRProvider` in `app/providers/ocr`.
2. Register in `OCRProviderFactory`.
3. Add value to `OCRProviderType` enum.
4. Add tests for provider selection and failure cases.

### Add new extraction fields

1. Extend shared extraction contract model.
2. Update extraction provider expected keys and prompt.
3. Update orchestrator mapping/response assembly.
4. Add or update unit/integration tests.

### Add new reference domains

1. Upload values using a new `reference_type`.
2. Use `/api/v1/references/validate` for that type.
3. Call mapping with same `reference_type` from extraction flow.

## 15. Troubleshooting

### 400 unsupported file type

- Extraction API accepts PDF only.
- Ingestion API accepts Excel MIME types only.

### 422 missing value column (ingestion)

- Excel must include one of: `value`, `name`, `category`, `location`, `master_value`.

### 503 OCR provider unavailable

- `gpt-5-mini` and `gemma-3-4b` OCR providers require `OPENAI_API_KEY`.
- Use `pytesseract` if key is unavailable.

### Mapping returns null

- Check if reference rows were ingested for the requested `reference_type`.
- Check `SIMILARITY_THRESHOLD` and candidate similarity.

### Import errors for `shared`

- Ensure `PYTHONPATH` points to repository root when running services locally.

## 16. Useful Repository Paths

- `deployment/docker-compose.yml`
- `deployment/db/001_init.sql`
- `services/license-extraction-service/app/main.py`
- `services/reference-ingestion-service/app/main.py`
- `shared/config/settings.py`
- `docs/sample_requests.md`
- `docs/extensibility_notes.md`
