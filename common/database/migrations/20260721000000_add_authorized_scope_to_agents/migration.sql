-- Additive: declared authorised-scope limits from emerge.yaml (emerge/1.1, RFC 0001).
-- NULL means "unspecified", never "unrestricted".
ALTER TABLE "agents" ADD COLUMN "authorized_scope" JSONB;
