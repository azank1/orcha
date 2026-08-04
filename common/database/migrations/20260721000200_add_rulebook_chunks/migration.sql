-- Enable pgvector extension (must exist before vector columns are created)
CREATE EXTENSION IF NOT EXISTS vector;

-- CreateTable
CREATE TABLE "rulebook_chunks" (
    "id" TEXT NOT NULL,
    "source_title" TEXT NOT NULL,
    "chunk_index" INTEGER NOT NULL,
    "content" TEXT NOT NULL,
    "embedding" vector(768),
    "metadata" JSONB,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "rulebook_chunks_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "rulebook_chunks_source_title_idx" ON "rulebook_chunks"("source_title");
