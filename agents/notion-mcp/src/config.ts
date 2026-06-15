/**
 * Configuration for the Notion MCP Agent.
 * Reads from environment variables with sensible defaults.
 */
export interface Config {
  /** Notion integration token (Internal Integration Token) */
  notionApiKey: string;
  /** Default database ID for queries (optional) */
  defaultDatabaseId?: string;
  /** Server name reported in MCP handshake */
  serverName: string;
  /** Server version */
  serverVersion: string;
  /** Log level */
  logLevel: "debug" | "info" | "warn" | "error";
}

export function loadConfig(): Config {
  const notionApiKey = process.env.NOTION_API_KEY;

  if (!notionApiKey) {
    throw new Error(
      "NOTION_API_KEY environment variable is required. " +
        "Create an integration at https://www.notion.so/my-integrations"
    );
  }

  return {
    notionApiKey,
    defaultDatabaseId: process.env.NOTION_DATABASE_ID || undefined,
    serverName: "notion-agent-mcp",
    serverVersion: "2.0.0",
    logLevel: (process.env.LOG_LEVEL as Config["logLevel"]) || "info",
  };
}
