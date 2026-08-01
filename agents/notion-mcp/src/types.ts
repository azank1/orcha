/**
 * Shared types for the Notion MCP Agent.
 */

/** Structured text content for Notion blocks */
export interface RichText {
  type: "text";
  text: { content: string; link?: { url: string } | null };
  plain_text: string;
}

/** Simplified page representation returned by tools */
export interface SimplifiedPage {
  id: string;
  url: string;
  title: string;
  created_time: string;
  last_edited_time: string;
  properties: Record<string, unknown>;
}

/** Simplified database representation */
export interface SimplifiedDatabase {
  id: string;
  url: string;
  title: string;
  description: string;
  properties: Record<string, { type: string; name: string }>;
}

/** Simplified search result */
export interface SearchResult {
  id: string;
  type: "page" | "database";
  title: string;
  url: string;
  last_edited_time: string;
}

/** Tool execution result */
export interface ToolResult {
  content: Array<{ type: "text"; text: string }>;
  isError?: boolean;
}
