-- CreateEnum
CREATE TYPE "ArtifactSource" AS ENUM ('USER_UPLOAD', 'AGENT_OUTPUT');

-- CreateEnum
CREATE TYPE "ArtifactStatus" AS ENUM ('PENDING', 'READY', 'DELETED');

-- CreateTable
CREATE TABLE "artifacts" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "session_id" TEXT,
    "filename" TEXT NOT NULL,
    "mime_type" TEXT NOT NULL,
    "size_bytes" INTEGER NOT NULL,
    "source" "ArtifactSource" NOT NULL,
    "status" "ArtifactStatus" NOT NULL DEFAULT 'PENDING',
    "s3_bucket" TEXT NOT NULL,
    "s3_key" TEXT NOT NULL,
    "page_count" INTEGER,
    "word_count" INTEGER,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "expires_at" TIMESTAMP(3),

    CONSTRAINT "artifacts_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "artifacts_user_id_idx" ON "artifacts"("user_id");

-- CreateIndex
CREATE INDEX "artifacts_session_id_idx" ON "artifacts"("session_id");

-- CreateIndex
CREATE INDEX "artifacts_status_idx" ON "artifacts"("status");

-- AddForeignKey
ALTER TABLE "artifacts" ADD CONSTRAINT "artifacts_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "artifacts" ADD CONSTRAINT "artifacts_session_id_fkey" FOREIGN KEY ("session_id") REFERENCES "conversation_sessions"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AlterEnum: platform MCP manifests (web-search, web-scraper) persist AuthStrategy.type = PLATFORM_ENV
ALTER TYPE "AuthType" ADD VALUE 'PLATFORM_ENV';