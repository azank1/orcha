-- AlterEnum
-- Adds COMPUTER_USE so the open computer-use bridge can register agents
-- (protocol.type: computer_use in emerge.yaml) the same way MCP/A2A do.
ALTER TYPE "ProtocolType" ADD VALUE 'COMPUTER_USE';
