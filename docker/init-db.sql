-- Initialize PostgreSQL database with required extensions
-- This runs automatically when container first starts

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- Grant permissions (database name should match docker-compose.yml)
GRANT ALL PRIVILEGES ON DATABASE rag_db TO rag_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO rag_user;

-- Create tables
CREATE TABLE IF NOT EXISTS documents (
    doc_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    url TEXT,
    file_path TEXT NOT NULL UNIQUE,
    breadcrumb TEXT[],
    content_hash TEXT NOT NULL,
    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS document_sections (
    section_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_id UUID NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    title TEXT,
    content TEXT NOT NULL,
    embedding VECTOR(1024),  -- Matches multilingual-e5-large dimensions
    content_tsv TSVECTOR,
    section_order INTEGER,
    has_code BOOLEAN DEFAULT FALSE,
    has_images BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS image_cache (
    image_hash TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    model_version TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS document_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    section_id UUID NOT NULL REFERENCES document_sections(section_id) ON DELETE CASCADE,
    image_hash TEXT NOT NULL REFERENCES image_cache(image_hash),
    image_path TEXT NOT NULL,
    alt_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS query_traces (
    trace_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_text TEXT NOT NULL,
    user_id TEXT,
    confidence TEXT NOT NULL,
    embedding_model TEXT,
    reranker_model TEXT,
    llm_model TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trace_citations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trace_id UUID NOT NULL REFERENCES query_traces(trace_id) ON DELETE CASCADE,
    section_id UUID NOT NULL REFERENCES document_sections(section_id),
    citation_number INTEGER NOT NULL,
    relevance_score FLOAT,
    doc_title TEXT,
    section_title TEXT,
    url TEXT
);

CREATE TABLE IF NOT EXISTS trace_answers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trace_id UUID NOT NULL REFERENCES query_traces(trace_id) ON DELETE CASCADE,
    answer_text TEXT NOT NULL,
    generation_time_ms INTEGER,
    token_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trace_section_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trace_id UUID NOT NULL REFERENCES query_traces(trace_id) ON DELETE CASCADE,
    section_id UUID NOT NULL REFERENCES document_sections(section_id),
    content_snapshot TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_sections_doc_id ON document_sections(doc_id);
CREATE INDEX IF NOT EXISTS idx_sections_embedding ON document_sections USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_sections_content_tsv ON document_sections USING gin(content_tsv);
CREATE INDEX IF NOT EXISTS idx_images_section_id ON document_images(section_id);
CREATE INDEX IF NOT EXISTS idx_images_hash ON image_cache USING hash(image_hash);
CREATE INDEX IF NOT EXISTS idx_traces_timestamp ON query_traces(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_citations_trace_id ON trace_citations(trace_id);

-- Create trigger for updating content_tsv
CREATE OR REPLACE FUNCTION update_content_tsv()
RETURNS TRIGGER AS $$
BEGIN
    NEW.content_tsv := to_tsvector('english', COALESCE(NEW.title, '') || ' ' || NEW.content);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_content_tsv
    BEFORE INSERT OR UPDATE ON document_sections
    FOR EACH ROW
    EXECUTE FUNCTION update_content_tsv();

-- Grant all permissions to rag_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO rag_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO rag_user;