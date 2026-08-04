/**
 * MCP Tool: update_page
 * Update properties of an existing Notion page.
 */
import { z } from "zod";
import { NotionClient } from "../notion/client.js";

export const updatePageSchema = {
  page_id: z.string().describe("ID of the page to update"),
  properties: z
    .record(z.unknown())
    .describe("Notion properties to update (same format as Notion API)"),
} as const;

export async function updatePage(
  notion: NotionClient,
  args: {
    page_id: string;
    properties: Record<string, unknown>;
  }
) {
  const page = await notion.updatePage(
    args.page_id,
    args.properties as Parameters<NotionClient["updatePage"]>[1]
  );

  return {
    content: [
      {
        type: "text" as const,
        text: JSON.stringify(
          {
            success: true,
            page: {
              id: page.id,
              url: page.url,
              title: page.title,
              last_edited_time: page.last_edited_time,
            },
          },
          null,
          2
        ),
      },
    ],
  };
}
