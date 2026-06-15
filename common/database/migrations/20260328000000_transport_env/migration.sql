-- Add env column to transports for STDIO agent env-var templates
ALTER TABLE "transports" ADD COLUMN "env" JSONB;
