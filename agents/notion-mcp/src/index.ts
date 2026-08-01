#!/usr/bin/env node
/**
 * Entry point for the Notion MCP Agent.
 * Starts the MCP server with stdio transport.
 */
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { createMcpServer } from "./server.js";

async function main() {
  const server = createMcpServer();
  const transport = new StdioServerTransport();

  await server.connect(transport);

  // Log to stderr (stdout is used for MCP protocol messages)
  console.error("Notion MCP Agent started (stdio transport)");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
