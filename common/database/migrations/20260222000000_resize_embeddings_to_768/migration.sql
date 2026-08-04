-- Resize all agent_embeddings vector columns from 1536 → 768 dims.
-- nomic-embed-text (the local Ollama embedding model) outputs 768-dimensional
-- vectors; the original schema assumed an OpenAI text-embedding-ada-002 (1536).
--
-- Drops any existing HNSW indices first (they are rebuilt by
-- 001_create_vector_indices.sql after migration).

DROP INDEX IF EXISTS idx_ae_embedding_hnsw;
DROP INDEX IF EXISTS idx_ae_name_embedding_hnsw;
DROP INDEX IF EXISTS idx_ae_description_embedding_hnsw;
DROP INDEX IF EXISTS idx_ae_capabilities_embedding_hnsw;

-- Truncate existing embeddings — dim mismatch means old rows are invalid anyway.
TRUNCATE TABLE agent_embeddings;

ALTER TABLE agent_embeddings
    ALTER COLUMN embedding              TYPE vector(768),
    ALTER COLUMN name_embedding         TYPE vector(768),
    ALTER COLUMN description_embedding  TYPE vector(768),
    ALTER COLUMN capabilities_embedding TYPE vector(768),
    ALTER COLUMN tags_embedding         TYPE vector(768);
