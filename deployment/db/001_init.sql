CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS reference_master (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reference_type TEXT NOT NULL,
    raw_value TEXT NOT NULL,
    normalized_value TEXT NOT NULL,
    embedding VECTOR(1536) NOT NULL,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_reference_master_type_normalized UNIQUE (reference_type, normalized_value)
);

CREATE INDEX IF NOT EXISTS idx_reference_master_type ON reference_master (reference_type);
CREATE INDEX IF NOT EXISTS idx_reference_master_embedding
    ON reference_master
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE TABLE IF NOT EXISTS processing_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL,
    service_name TEXT NOT NULL,
    status TEXT NOT NULL,
    processing_time_ms INTEGER,
    payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_processing_audit_request_id ON processing_audit (request_id);
CREATE INDEX IF NOT EXISTS idx_processing_audit_service_name ON processing_audit (service_name);

CREATE TABLE IF NOT EXISTS extraction_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL,
    document_type TEXT,
    extracted_json JSONB NOT NULL,
    source_language TEXT,
    ocr_used BOOLEAN NOT NULL DEFAULT FALSE,
    ocr_provider TEXT,
    extraction_model TEXT,
    processing_time_ms INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_extraction_history_request_id ON extraction_history (request_id);
