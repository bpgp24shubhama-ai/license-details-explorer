# Extensibility Notes

## Add a new OCR provider

1. Implement `OCRProvider` in `providers/ocr`.
2. Register provider in `OCRProviderFactory`.
3. Add provider name to request validation enum.

## Add new extraction fields

1. Extend shared extraction contract model.
2. Update extraction prompt in GPT provider.
3. Add mapping logic if field requires reference normalization.
4. Add tests for new field extraction and null behavior.

## Add new reference types

1. Upload with `reference_type` for the new master domain.
2. Define optional validation rules in ingestion service.
3. Use vector mapping by querying that `reference_type`.

## Scale-out recommendations

- Put both APIs behind API Gateway with auth and rate limits.
- Offload heavy PDF/OCR processing to worker queue (Celery/RQ/Kafka consumers).
- Partition audit/history tables by date for long-term retention.
- Add background job for periodic pgvector reindex and vacuum.
