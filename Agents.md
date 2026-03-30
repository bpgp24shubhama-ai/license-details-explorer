# AGENTS.md

## Project overview
This repository contains an enterprise-grade Python FastAPI platform with two microservices:

1. `license-extraction-service`
2. `reference-ingestion-service`

The platform extracts structured data from commercial license PDFs and maps extracted values against reference data stored in PostgreSQL with pgvector.

## Core rules
- Use Python 3.12+
- Use FastAPI for all APIs
- Use Pydantic models for request/response validation
- Use PostgreSQL as the primary database
- Use pgvector for vector similarity search
- Use clean architecture and separation of concerns
- Keep business logic out of route handlers
- Prefer async endpoints where appropriate
- All final API outputs must be valid JSON
- All extracted output must be in English
- Return null instead of guessing missing values

## Microservices
### 1. license-extraction-service
Responsibilities:
- PDF upload
- native PDF text extraction
- OCR fallback
- translation to English
- GPT-5-mini structured extraction
- nearest-neighbor reference mapping
- JSON response generation

### 2. reference-ingestion-service
Responsibilities:
- Excel upload
- schema validation
- normalization of master values
- embedding generation
- PostgreSQL + pgvector indexing
- reload/upsert workflows

## Folder structure expectations
Use an enterprise-grade folder structure like:

services/
  license-extraction-service/
    app/
      api/
      routers/
      schemas/
      services/
      providers/
      repositories/
      db/
      core/
      middleware/
      utils/
      tests/
    Dockerfile

  reference-ingestion-service/
    app/
      api/
      routers/
      schemas/
      services/
      providers/
      repositories/
      db/
      core/
      middleware/
      utils/
      tests/
    Dockerfile

shared/
  contracts/
  logging/
  exceptions/
  config/

deployment/
  docker-compose.yml

## Coding conventions
- Use type hints everywhere
- Keep functions small and single-purpose
- Use dependency injection where useful
- Avoid hardcoded config values
- Use environment variables for secrets and endpoints
- Add structured logging
- Add centralized exception handling
- Add health endpoints
- Add request correlation IDs
- Add tests for all critical paths

## OCR requirements
Support pluggable OCR providers:
- pytesseract
- GPT-5-mini OCR
- Gemma 3 4B OCR

Behavior:
- If PDF contains readable text, extract directly
- If PDF is image-based, perform OCR
- OCR provider must be selectable
- Preserve raw extracted text for traceability

## Extraction requirements
Use GPT-5-mini as the default extraction model.

Required JSON fields:
- license_number
- license_name
- license_category
- mapped_license_category
- issuing_authority
- holder_name
- address
- location
- mapped_location
- issue_date
- expiry_date
- validity_status
- source_language
- translated_to_english
- confidence_score
- raw_text
- extraction_notes
- page_numbers
- source_snippets
- request_id
- ocr_used
- ocr_provider
- extraction_model
- processing_time_ms
- document_type

## Mapping requirements
- Read master data from Excel
- Store embeddings in PostgreSQL with pgvector
- Use vector similarity search to map OCR-imperfect values
- Return both extracted value and mapped value
- Include similarity/confidence score

## Testing requirements
Add:
- unit tests
- integration tests
- edge-case handling for unreadable PDFs, bad Excel files, unsupported file types, and missing fields

## Deliverables
Whenever implementing this project, return:
- full project structure
- production-ready code
- database schema
- Docker setup
- sample requests
- sample responses
- extension notes