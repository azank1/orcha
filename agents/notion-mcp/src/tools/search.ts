/**
 * MCP Tool: search_notion
 * Search pages and databases in the connected Notion workspace.
 */
import { z } from "zod";
import { NotionClient } from "../notion/client.js";

export const searchNotionSchema = {
  query: z.string().describe("Search query text"),
  filter: z
    .enum(["page", "database"])
    .optional()
    .describe("Filter results by type: 'page' or 'database'"),
  page_size: z
    .number()
    .min(1)
    .max(100)
    .optional()
    .describe("Number of results to return (1-100, default 10)"),
} as const;

export async function searchNotion(
  notion: NotionClient,
  args: { query: string; filter?: "page" | "database"; page_size?: number }
) {
  const results = await notion.search(args.query, args.filter, args.page_size ?? 10);

  return {
    content: [
      {
        type: "text" as const,
        text: JSON.stringify(
          {
            total: results.length,
            results: results.map((r) => ({
              id: r.id,
              type: r.type,
              title: r.title,
              url: r.url,
              last_edited: r.last_edited_time,
            })),
          },
          null,
          2
        ),
      },
    ],
  };
}
