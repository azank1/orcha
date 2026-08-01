-- CreateEnum
CREATE TYPE "ProtocolType" AS ENUM ('MCP', 'A2A');

-- CreateEnum
CREATE TYPE "HealthStatus" AS ENUM ('HEALTHY', 'UNHEALTHY', 'UNKNOWN');

-- CreateEnum
CREATE TYPE "TransportType" AS ENUM ('SSE', 'STDIO', 'HTTP');

-- CreateEnum
CREATE TYPE "TLSType" AS ENUM ('TLS', 'MTLS', 'NONE');

-- CreateEnum
CREATE TYPE "AuthType" AS ENUM ('X_API_KEY', 'HTTP_BEARER', 'OAUTH2', 'OAUTH2_DCR');

-- CreateEnum
CREATE TYPE "PaymentType" AS ENUM ('X402', 'NONE');

-- CreateEnum
CREATE TYPE "CapabilityType" AS ENUM ('TOOL', 'RESOURCE', 'PROMPT');

-- CreateTable
CREATE TABLE "users" (
    "id" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "username" TEXT,
    "pat_token_hash" TEXT NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,
    "is_active" BOOLEAN NOT NULL DEFAULT true,

    CONSTRAINT "users_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "agents" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "version" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "provider" TEXT NOT NULL,
    "owner_contact" TEXT NOT NULL,
    "tags" TEXT[],
    "protocol_type" "ProtocolType" NOT NULL,
    "protocol_version" TEXT NOT NULL,
    "health_status" "HealthStatus" NOT NULL DEFAULT 'UNKNOWN',
    "health_endpoint" TEXT NOT NULL,
    "last_health_check" TIMESTAMP(3),
    "health_failures" INTEGER NOT NULL DEFAULT 0,
    "indexed_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,
    "is_active" BOOLEAN NOT NULL DEFAULT true,

    CONSTRAINT "agents_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "agent_versions" (
    "id" TEXT NOT NULL,
    "agent_id" TEXT NOT NULL,
    "version" TEXT NOT NULL,
    "manifest_snapshot" JSONB NOT NULL,
    "change_summary" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "agent_versions_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "transports" (
    "id" TEXT NOT NULL,
    "agent_id" TEXT NOT NULL,
    "type" "TransportType" NOT NULL,
    "endpoint" TEXT,
    "command" TEXT,
    "args" TEXT[],

    CONSTRAINT "transports_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "security_configs" (
    "id" TEXT NOT NULL,
    "agent_id" TEXT NOT NULL,
    "transport_layer_type" "TLSType" NOT NULL,
    "mtls_cert_vault_key" TEXT,
    "mtls_key_vault_key" TEXT,
    "mtls_ca_vault_key" TEXT,

    CONSTRAINT "security_configs_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "auth_strategies" (
    "id" TEXT NOT NULL,
    "security_id" TEXT NOT NULL,
    "capability_id" TEXT,
    "strategy_id" TEXT NOT NULL,
    "type" "AuthType" NOT NULL,
    "config" JSONB NOT NULL,

    CONSTRAINT "auth_strategies_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "payment_configs" (
    "id" TEXT NOT NULL,
    "agent_id" TEXT NOT NULL,
    "type" "PaymentType" NOT NULL DEFAULT 'NONE',
    "enabled" BOOLEAN NOT NULL DEFAULT false,
    "chain_id" TEXT,
    "recipient_address" TEXT,
    "asset" TEXT,
    "token_address" TEXT,
    "default_price" TEXT,
    "currency" TEXT,
    "facilitator_url" TEXT,

    CONSTRAINT "payment_configs_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "capabilities" (
    "id" TEXT NOT NULL,
    "agent_id" TEXT NOT NULL,
    "type" "CapabilityType" NOT NULL,
    "capability_id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "input_schema" JSONB,
    "output_schema" JSONB,
    "uri_template" TEXT,
    "mime_type" TEXT,
    "arguments" JSONB,
    "x402_price" TEXT,
    "x402_asset" TEXT,

    CONSTRAINT "capabilities_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "users_email_key" ON "users"("email");

-- CreateIndex
CREATE UNIQUE INDEX "users_username_key" ON "users"("username");

-- CreateIndex
CREATE INDEX "agents_user_id_idx" ON "agents"("user_id");

-- CreateIndex
CREATE INDEX "agents_protocol_type_idx" ON "agents"("protocol_type");

-- CreateIndex
CREATE INDEX "agents_health_status_idx" ON "agents"("health_status");

-- CreateIndex
CREATE UNIQUE INDEX "agents_user_id_name_version_key" ON "agents"("user_id", "name", "version");

-- CreateIndex
CREATE INDEX "agent_versions_agent_id_idx" ON "agent_versions"("agent_id");

-- CreateIndex
CREATE UNIQUE INDEX "agent_versions_agent_id_version_key" ON "agent_versions"("agent_id", "version");

-- CreateIndex
CREATE UNIQUE INDEX "transports_agent_id_key" ON "transports"("agent_id");

-- CreateIndex
CREATE UNIQUE INDEX "security_configs_agent_id_key" ON "security_configs"("agent_id");

-- CreateIndex
CREATE INDEX "auth_strategies_security_id_idx" ON "auth_strategies"("security_id");

-- CreateIndex
CREATE INDEX "auth_strategies_capability_id_idx" ON "auth_strategies"("capability_id");

-- CreateIndex
CREATE UNIQUE INDEX "payment_configs_agent_id_key" ON "payment_configs"("agent_id");

-- CreateIndex
CREATE INDEX "capabilities_agent_id_idx" ON "capabilities"("agent_id");

-- CreateIndex
CREATE INDEX "capabilities_type_idx" ON "capabilities"("type");

-- CreateIndex
CREATE UNIQUE INDEX "capabilities_agent_id_capability_id_key" ON "capabilities"("agent_id", "capability_id");

-- AddForeignKey
ALTER TABLE "agents" ADD CONSTRAINT "agents_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "agent_versions" ADD CONSTRAINT "agent_versions_agent_id_fkey" FOREIGN KEY ("agent_id") REFERENCES "agents"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "transports" ADD CONSTRAINT "transports_agent_id_fkey" FOREIGN KEY ("agent_id") REFERENCES "agents"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "security_configs" ADD CONSTRAINT "security_configs_agent_id_fkey" FOREIGN KEY ("agent_id") REFERENCES "agents"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "auth_strategies" ADD CONSTRAINT "auth_strategies_security_id_fkey" FOREIGN KEY ("security_id") REFERENCES "security_configs"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "auth_strategies" ADD CONSTRAINT "auth_strategies_capability_id_fkey" FOREIGN KEY ("capability_id") REFERENCES "capabilities"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "payment_configs" ADD CONSTRAINT "payment_configs_agent_id_fkey" FOREIGN KEY ("agent_id") REFERENCES "agents"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "capabilities" ADD CONSTRAINT "capabilities_agent_id_fkey" FOREIGN KEY ("agent_id") REFERENCES "agents"("id") ON DELETE CASCADE ON UPDATE CASCADE;
