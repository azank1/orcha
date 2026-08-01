-- Enable pgvector extension (must exist before vector columns are created)
CREATE EXTENSION IF NOT EXISTS vector;

-- CreateTable
CREATE TABLE "agent_embeddings" (
    "id" TEXT NOT NULL,
    "agent_id" TEXT NOT NULL,
    "templated_string" TEXT NOT NULL,
    "embedding" vector(768),
    "name_embedding" vector(768),
    "description_embedding" vector(768),
    "capabilities_embedding" vector(768),
    "tags_embedding" vector(768),
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "agent_embeddings_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "plan_executions" (
    "id" TEXT NOT NULL,
    "plan_hash" TEXT NOT NULL,
    "workflow_manifest" JSONB NOT NULL,
    "success" BOOLEAN NOT NULL,
    "error_message" TEXT,
    "execution_time_ms" INTEGER,
    "node_count" INTEGER NOT NULL,
    "edge_count" INTEGER NOT NULL,
    "max_depth" INTEGER NOT NULL,
    "parallel_width" INTEGER NOT NULL,
    "agent_reliability_mean" DOUBLE PRECISION NOT NULL,
    "agent_reliability_min" DOUBLE PRECISION NOT NULL,
    "has_loops" BOOLEAN NOT NULL,
    "has_conditionals" BOOLEAN NOT NULL,
    "conditional_depth" INTEGER NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "plan_executions_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "agent_embeddings_agent_id_key" ON "agent_embeddings"("agent_id");

-- CreateIndex
CREATE INDEX "agent_embeddings_agent_id_idx" ON "agent_embeddings"("agent_id");

-- CreateIndex
CREATE INDEX "plan_executions_plan_hash_idx" ON "plan_executions"("plan_hash");

-- CreateIndex
CREATE INDEX "plan_executions_success_idx" ON "plan_executions"("success");

-- CreateIndex
CREATE INDEX "plan_executions_created_at_idx" ON "plan_executions"("created_at");

-- AddForeignKey
ALTER TABLE "agent_embeddings" ADD CONSTRAINT "agent_embeddings_agent_id_fkey" FOREIGN KEY ("agent_id") REFERENCES "agents"("id") ON DELETE CASCADE ON UPDATE CASCADE;
