-- =============================================================================
-- Planning & Discovery — Vector index initialisation
--
-- Run AFTER `prisma migrate deploy` so the agents + agent_embeddings tables
-- already exist.
--
-- Idempotent: all statements use IF NOT EXISTS / DO $$ EXCEPTION blocks.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Extensions
-- ---------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- ---------------------------------------------------------------------------
-- Full-text search column on agents
-- Maintained by trigger (array_to_string is STABLE, not IMMUTABLE, so it
-- cannot appear in a GENERATED ALWAYS AS expression).
-- ---------------------------------------------------------------------------
ALTER TABLE agents
    ADD COLUMN IF NOT EXISTS search_vector tsvector;

CREATE OR REPLACE FUNCTION agents_search_vector_update()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', coalesce(NEW.name, '')),        'A') ||
        setweight(to_tsvector('english', coalesce(NEW.description, '')), 'B') ||
        setweight(to_tsvector('english', coalesce(array_to_string(NEW.tags, ' '), '')), 'C');
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_agents_search_vector ON agents;
CREATE TRIGGER trg_agents_search_vector
    BEFORE INSERT OR UPDATE ON agents
    FOR EACH ROW EXECUTE FUNCTION agents_search_vector_update();

-- Backfill any existing rows
UPDATE agents SET search_vector =
    setweight(to_tsvector('english', coalesce(name, '')),        'A') ||
    setweight(to_tsvector('english', coalesce(description, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(array_to_string(tags, ' '), '')), 'C')
WHERE search_vector IS NULL;

-- ---------------------------------------------------------------------------
-- GIN index on full-text search vector
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'agents' AND indexname = 'idx_agents_search_vector_gin'
    ) THEN
        CREATE INDEX idx_agents_search_vector_gin
            ON agents USING GIN (search_vector);
    END IF;
END $$;

-- ---------------------------------------------------------------------------
-- GIN index on agents.tags (array column)
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'agents' AND indexname = 'idx_agents_tags_gin'
    ) THEN
        CREATE INDEX idx_agents_tags_gin
            ON agents USING GIN (tags);
    END IF;
END $$;

-- ---------------------------------------------------------------------------
-- Composite B-tree partial index — active agents by protocol_type
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'agents' AND indexname = 'idx_agents_active_protocol'
    ) THEN
        CREATE INDEX idx_agents_active_protocol
            ON agents (protocol_type, health_status)
            WHERE is_active = TRUE;
    END IF;
END $$;

-- ---------------------------------------------------------------------------
-- HNSW index — combined embedding (primary semantic search)
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'agent_embeddings' AND indexname = 'idx_ae_embedding_hnsw'
    ) THEN
        CREATE INDEX idx_ae_embedding_hnsw
            ON agent_embeddings USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64);
    END IF;
END $$;

-- ---------------------------------------------------------------------------
-- HNSW index — name embedding
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'agent_embeddings' AND indexname = 'idx_ae_name_embedding_hnsw'
    ) THEN
        CREATE INDEX idx_ae_name_embedding_hnsw
            ON agent_embeddings USING hnsw (name_embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64);
    END IF;
END $$;

-- ---------------------------------------------------------------------------
-- HNSW index — description embedding
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'agent_embeddings' AND indexname = 'idx_ae_description_embedding_hnsw'
    ) THEN
        CREATE INDEX idx_ae_description_embedding_hnsw
            ON agent_embeddings USING hnsw (description_embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64);
    END IF;
END $$;

-- ---------------------------------------------------------------------------
-- HNSW index — capabilities embedding
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'agent_embeddings' AND indexname = 'idx_ae_capabilities_embedding_hnsw'
    ) THEN
        CREATE INDEX idx_ae_capabilities_embedding_hnsw
            ON agent_embeddings USING hnsw (capabilities_embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64);
    END IF;
END $$;

-- ---------------------------------------------------------------------------
-- B-tree index — agent_embeddings.agent_id (FK lookups)
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'agent_embeddings' AND indexname = 'idx_ae_agent_id'
    ) THEN
        CREATE INDEX idx_ae_agent_id ON agent_embeddings (agent_id);
    END IF;
END $$;

-- ---------------------------------------------------------------------------
-- B-tree indices on plan_executions (query patterns)
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'plan_executions' AND indexname = 'idx_pe_plan_hash'
    ) THEN
        CREATE INDEX idx_pe_plan_hash ON plan_executions (plan_hash);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'plan_executions' AND indexname = 'idx_pe_success_created'
    ) THEN
        CREATE INDEX idx_pe_success_created ON plan_executions (success, created_at DESC);
    END IF;
END $$;
