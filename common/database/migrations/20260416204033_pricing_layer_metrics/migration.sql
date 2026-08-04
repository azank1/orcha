/*
  Warnings:

  - You are about to drop the column `x402_asset` on the `capabilities` table. All the data in the column will be lost.
  - You are about to drop the column `x402_price` on the `capabilities` table. All the data in the column will be lost.
  - You are about to drop the column `asset` on the `payment_configs` table. All the data in the column will be lost.
  - You are about to drop the column `chain_id` on the `payment_configs` table. All the data in the column will be lost.
  - You are about to drop the column `currency` on the `payment_configs` table. All the data in the column will be lost.
  - You are about to drop the column `default_price` on the `payment_configs` table. All the data in the column will be lost.
  - You are about to drop the column `facilitator_url` on the `payment_configs` table. All the data in the column will be lost.
  - You are about to drop the column `recipient_address` on the `payment_configs` table. All the data in the column will be lost.
  - You are about to drop the column `token_address` on the `payment_configs` table. All the data in the column will be lost.
  - You are about to drop the column `type` on the `payment_configs` table. All the data in the column will be lost.

*/
-- CreateEnum
CREATE TYPE "UserRole" AS ENUM ('USER', 'DEV');

-- CreateEnum
CREATE TYPE "InvocationStatus" AS ENUM ('SUCCESS', 'ERROR', 'TIMEOUT');

-- CreateEnum
CREATE TYPE "TxStatus" AS ENUM ('PENDING', 'SETTLED', 'FAILED');

-- AlterTable
ALTER TABLE "agents" ADD COLUMN     "execution_count" INTEGER NOT NULL DEFAULT 0,
ADD COLUMN     "p95_latency_ms" INTEGER NOT NULL DEFAULT 5000,
ADD COLUMN     "success_rate" DOUBLE PRECISION NOT NULL DEFAULT 0.70,
ADD COLUMN     "task_category" TEXT,
ADD COLUMN     "uptime_score" DOUBLE PRECISION NOT NULL DEFAULT 1.0;

-- AlterTable
ALTER TABLE "capabilities" DROP COLUMN "x402_asset",
DROP COLUMN "x402_price";

-- AlterTable
ALTER TABLE "payment_configs" DROP COLUMN "asset",
DROP COLUMN "chain_id",
DROP COLUMN "currency",
DROP COLUMN "default_price",
DROP COLUMN "facilitator_url",
DROP COLUMN "recipient_address",
DROP COLUMN "token_address",
DROP COLUMN "type",
ADD COLUMN     "base_fee" TEXT;

-- AlterTable
ALTER TABLE "session_transcript_entries" ADD COLUMN     "invocation_cost" DECIMAL(18,8);

-- AlterTable
ALTER TABLE "users" ADD COLUMN     "arrears_flag" BOOLEAN NOT NULL DEFAULT false,
ADD COLUMN     "arrears_usd" DOUBLE PRECISION NOT NULL DEFAULT 0,
ADD COLUMN     "privy_wallet_id" TEXT,
ADD COLUMN     "role" "UserRole" NOT NULL DEFAULT 'USER',
ADD COLUMN     "wallet_address" TEXT,
ADD COLUMN     "withdrawal_address" TEXT;

-- DropEnum
DROP TYPE "PaymentType";

-- CreateTable
CREATE TABLE "agent_invocations" (
    "id" TEXT NOT NULL,
    "session_id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "agent_id" TEXT NOT NULL,
    "call_id" TEXT NOT NULL,
    "status" "InvocationStatus" NOT NULL,
    "latency_ms" INTEGER,
    "base_fee" DECIMAL(18,8),
    "platform_tokens" INTEGER,
    "error_type" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "agent_invocations_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "transactions" (
    "id" TEXT NOT NULL,
    "session_id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "agent_id" TEXT NOT NULL,
    "call_id" TEXT NOT NULL,
    "base_fee" DECIMAL(18,8) NOT NULL,
    "platform_cut" DECIMAL(18,8) NOT NULL,
    "developer_payout" DECIMAL(18,8) NOT NULL,
    "latency_ms" INTEGER NOT NULL,
    "status" "TxStatus" NOT NULL DEFAULT 'PENDING',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "settled_at" TIMESTAMP(3),

    CONSTRAINT "transactions_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "registry_stats" (
    "id" TEXT NOT NULL,
    "task_category" TEXT NOT NULL,
    "median_base_fee_usd" DECIMAL(18,8),
    "median_latency_ms" DOUBLE PRECISION,
    "agent_count" INTEGER NOT NULL DEFAULT 0,
    "computed_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "registry_stats_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "agent_invocations_call_id_key" ON "agent_invocations"("call_id");

-- CreateIndex
CREATE INDEX "agent_invocations_agent_id_created_at_idx" ON "agent_invocations"("agent_id", "created_at");

-- CreateIndex
CREATE INDEX "agent_invocations_session_id_idx" ON "agent_invocations"("session_id");

-- CreateIndex
CREATE UNIQUE INDEX "transactions_call_id_key" ON "transactions"("call_id");

-- CreateIndex
CREATE INDEX "transactions_status_created_at_idx" ON "transactions"("status", "created_at");

-- CreateIndex
CREATE INDEX "transactions_agent_id_idx" ON "transactions"("agent_id");

-- CreateIndex
CREATE UNIQUE INDEX "registry_stats_task_category_key" ON "registry_stats"("task_category");

-- AddForeignKey
ALTER TABLE "agent_invocations" ADD CONSTRAINT "agent_invocations_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "transactions" ADD CONSTRAINT "transactions_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;
