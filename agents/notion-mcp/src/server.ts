/**
 * MCP Server for Notion Agent.
 * Registers all tools, resources, and prompts.
 */
import { McpServer, ResourceTemplate } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { NotionClient } from "./notion/client.js";
import { loadConfig } from "./config.js";

// Tools
import { searchNotionSchema, searchNotion } from "./tools/search.js";
import { createPageSchema, createPage } from "./tools/create-page.js";
import { updatePageSchema, updatePage } from "./tools/update-page.js";
import { queryDatabaseSchema, queryDatabase } from "./tools/query-database.js";
import { getPageSchema, getPage } from "./tools/get-page.js";

export function createMcpServer(): McpServer {
  const config = loadConfig();
  const notion = new NotionClient(config.notionApiKey);

  const server = new McpServer(
    {
      name: config.serverName,
      version: config.serverVersion,
    },
    {
      capabilities: {
        tools: {},
        resources: {},
        prompts: {},
      },
    }
  );

  // ── Tools ────────────────────────────────────────────────

  server.tool(
    "search_notion",
    "Search for pages and databases in the Notion workspace",
    searchNotionSchema,
    async (args) => searchNotion(notion, args)
  );

  server.tool(
    "get_page",
    "Retrieve a Notion page by ID with its properties and optional content",
    getPageSchema,
    async (args) => getPage(notion, args)
  );

  server.tool(
    "create_page",
    "Create a new page in Notion under a parent page or database",
    createPageSchema,
    async (args) => createPage(notion, args)
  );

  server.tool(
    "update_page",
    "Update properties of an existing Notion page",
    updatePageSchema,
    async (args) => updatePage(notion, args)
  );

  server.tool(
    "query_database",
    "Query a Notion database with optional filters and sorts",
    queryDatabaseSchema,
    async (args) => queryDatabase(notion, args)
  );

  // ── Resources ────────────────────────────────────────────

  server.resource(
    "page",
    new ResourceTemplate("notion://pages/{pageId}", { list: undefined }),
    {
      description: "A Notion page identified by its ID",
      mimeType: "application/json",
    },
    async (uri, variables) => {
      const pageId = variables.pageId as string;
      const page = await notion.getPage(pageId);
      return {
        contents: [
          {
            uri: uri.href,
            mimeType: "application/json",
            text: JSON.stringify(page, null, 2),
          },
        ],
      };
    }
  );

  server.resource(
    "database",
    new ResourceTemplate("notion://databases/{databaseId}", { list: undefined }),
    {
      description: "A Notion database identified by its ID",
      mimeType: "application/json",
    },
    async (uri, variables) => {
      const databaseId = variables.databaseId as string;
      const db = await notion.getDatabase(databaseId);
      return {
        contents: [
          {
            uri: uri.href,
            mimeType: "application/json",
            text: JSON.stringify(db, null, 2),
          },
        ],
      };
    }
  );

  // ── Prompts ──────────────────────────────────────────────

  server.prompt(
    "research_topic",
    "Generate a research plan and create a structured Notion page for a given topic",
    {
      topic: z.string().describe("The research topic to investigate"),
      depth: z.enum(["brief", "standard", "comprehensive"]).optional().describe("Research depth"),
    },
    async (args) => ({
      messages: [
        {
          role: "user" as const,
          content: {
            type: "text" as const,
            text: [
              `Research the following topic and create a structured Notion page: "${args.topic}"`,
              "",
              `Depth: ${args.depth || "standard"}`,
              "",
              "Steps:",
              "1. Use search_notion to check if we already have notes on this topic",
              "2. Research the topic thoroughly",
              "3. Use create_page to create a new page with:",
              "   - A clear title",
              "   - Executive summary",
              "   - Key findings organized by subtopic",
              "   - Sources and references",
              "   - Date of research",
              "",
              "Format the content with clear headings and bullet points.",
            ].join("\n"),
          },
        },
      ],
    })
  );

  server.prompt(
    "meeting_notes",
    "Create a structured meeting notes page in Notion",
    {
      meeting_title: z.string().describe("Title of the meeting"),
      attendees: z.string().optional().describe("Comma-separated list of attendees"),
      database_id: z.string().optional().describe("Optional database ID to store meeting notes in"),
    },
    async (args) => ({
      messages: [
        {
          role: "user" as const,
          content: {
            type: "text" as const,
            text: [
              `Create meeting notes in Notion for: "${args.meeting_title}"`,
              args.attendees ? `Attendees: ${args.attendees}` : "",
              "",
              "Use create_page with the following structure:",
              "- Meeting title as page title",
              "- Date and time",
              "- Attendees list",
              "- Agenda items",
              "- Discussion notes (placeholder sections)",
              "- Action items (with assignees)",
              "- Next steps",
              "",
              args.database_id
                ? `Store in database: ${args.database_id}`
                : "Create as a standalone page",
            ]
              .filter(Boolean)
              .join("\n"),
          },
        },
      ],
    })
  );

  return server;
}
