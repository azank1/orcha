/**
 * MCP Tool: create_page
 * Create a new page in Notion under a specified parent (page or database).
 */
import { z } from "zod";
import type { CreatePageParameters } from "@notionhq/client/build/src/api-endpoints.js";
import { NotionClient } from "../notion/client.js";

export const createPageSchema = {
  parent_id: z.string().describe("ID of the parent page or database"),
  parent_type: z
    .enum(["page_id", "database_id"])
    .describe("Type of parent: 'page_id' for a page, 'database_id' for a database"),
  title: z.string().describe("Title for the new page"),
  content: z
    .string()
    .optional()
    .describe("Optional markdown-like text content for the page body"),
  properties: z
    .record(z.unknown())
    .optional()
    .describe("Additional Notion properties (for database-child pages)"),
} as const;

export async function createPage(
  notion: NotionClient,
  args: {
    parent_id: string;
    parent_type: "page_id" | "database_id";
    title: string;
    content?: string;
    properties?: Record<string, unknown>;
  }
) {
  const parent =
    args.parent_type === "database_id"
      ? { database_id: args.parent_id }
      : { page_id: args.parent_id };

  // Build properties with title
  const properties: Record<string, unknown> = {
    ...(args.properties ?? {}),
  };

  // For database children, use "Name" as the title property (common convention)
  // For page children, use "title"
  if (args.parent_type === "database_id") {
    properties["Name"] = {
      title: [{ text: { content: args.title } }],
    };
  } else {
    properties["title"] = {
      title: [{ text: { content: args.title } }],
    };
  }

  // Build children blocks if content is provided
  const children: Array<{
    object: "block";
    type: "paragraph";
    paragraph: { rich_text: Array<{ type: "text"; text: { content: string } }> };
  }> = [];

  if (args.content) {
    // Split content into paragraphs
    const paragraphs = args.content.split("\n\n").filter((p) => p.trim());
    for (const paragraph of paragraphs) {
      children.push({
        object: "block",
        type: "paragraph",
        paragraph: {
          rich_text: [{ type: "text", text: { content: paragraph.trim() } }],
        },
      });
    }
  }

  const createParams: Parameters<NotionClient["createPage"]>[0] = {
    parent: parent as { database_id: string } | { page_id: string },
    properties: properties as CreatePageParameters["properties"],
    ...(children.length > 0 ? { children } : {}),
  };

  const page = await notion.createPage(createParams);

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
              created_time: page.created_time,
            },
          },
          null,
          2
        ),
      },
    ],
  };
}
