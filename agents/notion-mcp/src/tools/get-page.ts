/**
 * MCP Tool: get_page
 * Retrieve a Notion page by ID with all its properties.
 */
import { z } from "zod";
import { NotionClient } from "../notion/client.js";

export const getPageSchema = {
  page_id: z.string().describe("ID of the page to retrieve"),
  include_content: z
    .boolean()
    .optional()
    .describe("If true, also fetch page content blocks (default: false)"),
} as const;

export async function getPage(
  notion: NotionClient,
  args: { page_id: string; include_content?: boolean }
) {
  const page = await notion.getPage(args.page_id);

  let blocks: unknown[] | undefined;
  if (args.include_content) {
    const rawBlocks = await notion.getBlockChildren(args.page_id);
    blocks = rawBlocks.map((b) => ({
      id: b.id,
      type: b.type,
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      content: (b as any)[b.type],
    }));
  }

  return {
    content: [
      {
        type: "text" as const,
        text: JSON.stringify(
          {
            page: {
              id: page.id,
              url: page.url,
              title: page.title,
              created_time: page.created_time,
              last_edited_time: page.last_edited_time,
              properties: page.properties,
            },
            ...(blocks ? { content_blocks: blocks } : {}),
          },
          null,
          2
        ),
      },
    ],
  };
}
