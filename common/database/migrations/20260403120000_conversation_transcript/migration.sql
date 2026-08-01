-- CreateEnum
CREATE TYPE "TranscriptRole" AS ENUM ('USER', 'ASSISTANT', 'TOOL');

-- CreateTable
CREATE TABLE "conversation_sessions" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "persisted_message_count" INTEGER NOT NULL DEFAULT 0,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "conversation_sessions_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "session_transcript_entries" (
    "id" TEXT NOT NULL,
    "session_id" TEXT NOT NULL,
    "sequence_num" INTEGER NOT NULL,
    "role" "TranscriptRole" NOT NULL,
    "content" TEXT NOT NULL,
    "tool_calls" JSONB,
    "tool_call_id" TEXT,
    "tool_name" TEXT,
    "tool_inputs" JSONB,
    "tool_status" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "session_transcript_entries_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "session_transcript_entries_session_id_sequence_num_key" ON "session_transcript_entries"("session_id", "sequence_num");

-- CreateIndex
CREATE INDEX "session_transcript_entries_session_id_idx" ON "session_transcript_entries"("session_id");

-- CreateIndex
CREATE INDEX "conversation_sessions_user_id_idx" ON "conversation_sessions"("user_id");

-- CreateIndex
CREATE INDEX "conversation_sessions_user_id_updated_at_idx" ON "conversation_sessions"("user_id", "updated_at");

-- AddForeignKey
ALTER TABLE "conversation_sessions" ADD CONSTRAINT "conversation_sessions_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "session_transcript_entries" ADD CONSTRAINT "session_transcript_entries_session_id_fkey" FOREIGN KEY ("session_id") REFERENCES "conversation_sessions"("id") ON DELETE CASCADE ON UPDATE CASCADE;
