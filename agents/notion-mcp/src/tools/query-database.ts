/**
 * MCP Tool: query_database
 * Query a Notion database with optional filters and sorts.
 */
import { z } from "zod";
import { NotionClient } from "../notion/client.js";

export const queryDatabaseSchema = {
  database_id: z.string().describe("ID of the database to query"),
  filter: z
    .record(z.unknown())
    .optional()
    .describe("Notion filter object (see Notion API reference)"),
  sorts: z
    .array(z.record(z.unknown()))
    .optional()
    .describe("Array of sort objects (see Notion API reference)"),
  page_size: z
    .number()
    .min(1)
    .max(100)
    .optional()
    .describe("Number of results (1-100, default 100)"),
} as const;

export async function queryDatabase(
  notion: NotionClient,
  args: {
    database_id: string;
    filter?: Record<string, unknown>;
    sorts?: Array<Record<string, unknown>>;
    page_size?: number;
  }
) {
  const results = await notion.queryDatabase(
    args.database_id,
    args.filter as Parameters<NotionClient["queryDatabase"]>[1],
    args.sorts as Parameters<NotionClient["queryDatabase"]>[2],
    args.page_size
  );

  return {
    content: [
      {
        type: "text" as const,
        text: JSON.stringify(
          {
            total: results.length,
            database_id: args.database_id,
            results: results.map((page) => ({
              id: page.id,
              url: page.url,
              title: page.title,
              last_edited: page.last_edited_time,
              properties: page.properties,
            })),
          },
          null,
          2
        ),
      },
    ],
  };
}
