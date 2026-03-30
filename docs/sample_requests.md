# Sample API Requests

## 1) Extract License PDF

```bash
curl -X POST "http://localhost:8001/api/v1/extractions" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@./samples/fssai-license.pdf" \
  -F "ocr_provider=pytesseract" \
  -F "document_type=fssai"
```

## 2) Upload Master Reference Excel

```bash
curl -X POST "http://localhost:8002/api/v1/references/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@./samples/reference-master.xlsx" \
  -F "reference_type=license_category" \
  -F "mode=reload"
```

## 3) Reindex Existing References

```bash
curl -X POST "http://localhost:8002/api/v1/references/reindex" \
  -H "Content-Type: application/json" \
  -d '{"reference_type": "location"}'
```

## 4) Validate Lookup Mapping

```bash
curl -X POST "http://localhost:8002/api/v1/references/validate" \
  -H "Content-Type: application/json" \
  -d '{"reference_type": "location", "value": "mumabi"}'
```
