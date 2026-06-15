/**
 * Unit tests for MCP tools.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";

// Create mock notion client
function createMockNotionClient() {
  return {
    search: vi.fn(),
    getPage: vi.fn(),
    createPage: vi.fn(),
    updatePage: vi.fn(),
    queryDatabase: vi.fn(),
    getDatabase: vi.fn(),
    getBlockChildren: vi.fn(),
    appendBlocks: vi.fn(),
  };
}

import { searchNotion } from "../../src/tools/search.js";
import { getPage } from "../../src/tools/get-page.js";
import { createPage } from "../../src/tools/create-page.js";
import { updatePage } from "../../src/tools/update-page.js";
import { queryDatabase } from "../../src/tools/query-database.js";
import type { NotionClient } from "../../src/notion/client.js";

describe("MCP Tools", () => {
  let mockNotion: ReturnType<typeof createMockNotionClient>;

  beforeEach(() => {
    mockNotion = createMockNotionClient();
  });

  describe("searchNotion", () => {
    it("should return formatted search results", async () => {
      mockNotion.search.mockResolvedValueOnce([
        {
          id: "page-1",
          type: "page",
          title: "Test Page",
          url: "https://notion.so/page-1",
          last_edited_time: "2026-02-16T00:00:00.000Z",
        },
      ]);

      const result = await searchNotion(mockNotion as unknown as NotionClient, {
        query: "test",
      });

      expect(result.content).toHaveLength(1);
      const parsed = JSON.parse(result.content[0].text);
      expect(parsed.total).toBe(1);
      expect(parsed.results[0].title).toBe("Test Page");
    });

    it("should pass filter and page_size to client", async () => {
      mockNotion.search.mockResolvedValueOnce([]);

      await searchNotion(mockNotion as unknown as NotionClient, {
        query: "test",
        filter: "database",
        page_size: 5,
      });

      expect(mockNotion.search).toHaveBeenCalledWith("test", "database", 5);
    });
  });

  describe("getPage", () => {
    it("should return page data without content", async () => {
      mockNotion.getPage.mockResolvedValueOnce({
        id: "page-1",
        url: "https://notion.so/page-1",
        title: "Test",
        created_time: "2026-02-16T00:00:00.000Z",
        last_edited_time: "2026-02-16T00:00:00.000Z",
        properties: {},
      });

      const result = await getPage(mockNotion as unknown as NotionClient, {
        page_id: "page-1",
      });

      const parsed = JSON.parse(result.content[0].text);
      expect(parsed.page.id).toBe("page-1");
      expect(parsed.content_blocks).toBeUndefined();
    });

    it("should include content blocks when requested", async () => {
      mockNotion.getPage.mockResolvedValueOnce({
        id: "page-1",
        url: "https://notion.so/page-1",
        title: "Test",
        created_time: "2026-02-16T00:00:00.000Z",
        last_edited_time: "2026-02-16T00:00:00.000Z",
        properties: {},
      });
      mockNotion.getBlockChildren.mockResolvedValueOnce([
        {
          id: "block-1",
          type: "paragraph",
          paragraph: {
            rich_text: [{ plain_text: "Hello" }],
          },
        },
      ]);

      const result = await getPage(mockNotion as unknown as NotionClient, {
        page_id: "page-1",
        include_content: true,
      });

      const parsed = JSON.parse(result.content[0].text);
      expect(parsed.content_blocks).toHaveLength(1);
      expect(parsed.content_blocks[0].type).toBe("paragraph");
    });
  });

  describe("createPage", () => {
    it("should create a page under a parent page", async () => {
      mockNotion.createPage.mockResolvedValueOnce({
        id: "new-page",
        url: "https://notion.so/new-page",
        title: "New Page",
        created_time: "2026-02-16T00:00:00.000Z",
      });

      const result = await createPage(mockNotion as unknown as NotionClient, {
        parent_id: "parent-1",
        parent_type: "page_id",
        title: "New Page",
      });

      const parsed = JSON.parse(result.content[0].text);
      expect(parsed.success).toBe(true);
      expect(parsed.page.title).toBe("New Page");

      // Verify createPage was called with correct parent
      const callArgs = mockNotion.createPage.mock.calls[0][0];
      expect(callArgs.parent).toEqual({ page_id: "parent-1" });
    });

    it("should create a page in a database", async () => {
      mockNotion.createPage.mockResolvedValueOnce({
        id: "new-page",
        url: "https://notion.so/new-page",
        title: "DB Row",
        created_time: "2026-02-16T00:00:00.000Z",
      });

      const result = await createPage(mockNotion as unknown as NotionClient, {
        parent_id: "db-1",
        parent_type: "database_id",
        title: "DB Row",
      });

      const parsed = JSON.parse(result.content[0].text);
      expect(parsed.success).toBe(true);

      const callArgs = mockNotion.createPage.mock.calls[0][0];
      expect(callArgs.parent).toEqual({ database_id: "db-1" });
      expect(callArgs.properties.Name).toBeDefined();
    });

    it("should include content paragraphs when provided", async () => {
      mockNotion.createPage.mockResolvedValueOnce({
        id: "new-page",
        url: "https://notion.so/new-page",
        title: "With Content",
        created_time: "2026-02-16T00:00:00.000Z",
      });

      await createPage(mockNotion as unknown as NotionClient, {
        parent_id: "parent-1",
        parent_type: "page_id",
        title: "With Content",
        content: "First paragraph\n\nSecond paragraph",
      });

      const callArgs = mockNotion.createPage.mock.calls[0][0];
      expect(callArgs.children).toHaveLength(2);
      expect(callArgs.children[0].type).toBe("paragraph");
    });
  });

  describe("updatePage", () => {
    it("should update page properties", async () => {
      mockNotion.updatePage.mockResolvedValueOnce({
        id: "page-1",
        url: "https://notion.so/page-1",
        title: "Updated",
        last_edited_time: "2026-02-16T12:00:00.000Z",
      });

      const result = await updatePage(mockNotion as unknown as NotionClient, {
        page_id: "page-1",
        properties: { Status: { select: { name: "Done" } } },
      });

      const parsed = JSON.parse(result.content[0].text);
      expect(parsed.success).toBe(true);
      expect(parsed.page.title).toBe("Updated");
    });
  });

  describe("queryDatabase", () => {
    it("should query and return database rows", async () => {
      mockNotion.queryDatabase.mockResolvedValueOnce([
        {
          id: "row-1",
          url: "https://notion.so/row-1",
          title: "Row 1",
          last_edited_time: "2026-02-16T00:00:00.000Z",
          properties: { Name: "Row 1" },
        },
      ]);

      const result = await queryDatabase(
        mockNotion as unknown as NotionClient,
        { database_id: "db-1" }
      );

      const parsed = JSON.parse(result.content[0].text);
      expect(parsed.total).toBe(1);
      expect(parsed.database_id).toBe("db-1");
      expect(parsed.results[0].title).toBe("Row 1");
    });
  });
});
