-- New extension not present in prior migrations
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- CreateTable (new — not in prior migrations)
CREATE TABLE "workflow_templates" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "goal_template" TEXT NOT NULL,
    "parameters" JSONB NOT NULL DEFAULT '{}',
    "steps" JSONB NOT NULL,
    "agents_used" TEXT[] DEFAULT ARRAY[]::TEXT[],
    "created_from_session" TEXT,
    "schedule_cron" TEXT,
    "schedule_tz" TEXT NOT NULL DEFAULT 'UTC',
    "schedule_enabled" BOOLEAN NOT NULL DEFAULT false,
    "next_run_at" TIMESTAMP(3),
    "last_run_at" TIMESTAMP(3),
    "run_count" INTEGER NOT NULL DEFAULT 0,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "workflow_templates_pkey" PRIMARY KEY ("id")
);

-- CreateTable (new — not in prior migrations)
CREATE TABLE "user_secrets" (
    "user_id" TEXT NOT NULL,
    "key" TEXT NOT NULL,
    "encrypted_value" BYTEA NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "user_secrets_pkey" PRIMARY KEY ("user_id","key")
);

-- CreateTable (new — not in prior migrations)
CREATE TABLE "agent_registrations" (
    "agent_id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "client_id" TEXT NOT NULL,
    "encrypted_client_secret" BYTEA NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "agent_registrations_pkey" PRIMARY KEY ("agent_id","user_id")
);

-- CreateIndex
CREATE INDEX "workflow_templates_user_id_idx" ON "workflow_templates"("user_id");

-- CreateIndex
CREATE INDEX "workflow_templates_next_run_at_idx" ON "workflow_templates"("next_run_at");

-- AddForeignKey
ALTER TABLE "workflow_templates" ADD CONSTRAINT "workflow_templates_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "user_secrets" ADD CONSTRAINT "user_secrets_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "agent_registrations" ADD CONSTRAINT "agent_registrations_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;
