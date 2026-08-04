-- AlterTable
ALTER TABLE "user_secrets" ADD COLUMN     "agent_secret_id" TEXT;

-- CreateTable
CREATE TABLE "agent_secrets" (
    "id" TEXT NOT NULL,
    "agent_id" TEXT NOT NULL,
    "var_name" TEXT NOT NULL,
    "description" TEXT,
    "required" BOOLEAN NOT NULL DEFAULT true,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "agent_secrets_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "agent_secrets_agent_id_idx" ON "agent_secrets"("agent_id");

-- CreateIndex
CREATE UNIQUE INDEX "agent_secrets_agent_id_var_name_key" ON "agent_secrets"("agent_id", "var_name");

-- AddForeignKey
ALTER TABLE "user_secrets" ADD CONSTRAINT "user_secrets_agent_secret_id_fkey" FOREIGN KEY ("agent_secret_id") REFERENCES "agent_secrets"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "agent_secrets" ADD CONSTRAINT "agent_secrets_agent_id_fkey" FOREIGN KEY ("agent_id") REFERENCES "agents"("id") ON DELETE CASCADE ON UPDATE CASCADE;
