/**
 * Unit tests for Notion client wrapper.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock @notionhq/client before importing our module
vi.mock("@notionhq/client", () => ({
  Client: vi.fn().mockImplementation(() => ({
    search: vi.fn(),
    pages: {
      retrieve: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
    },
    databases: {
      retrieve: vi.fn(),
      query: vi.fn(),
    },
    blocks: {
      children: {
        list: vi.fn(),
        append: vi.fn(),
      },
    },
  })),
}));

import { NotionClient } from "../../src/notion/client.js";
import { Client } from "@notionhq/client";

describe("NotionClient", () => {
  let notionClient: NotionClient;
  let mockSdkClient: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.clearAllMocks();
    notionClient = new NotionClient("test-api-key");
    // Get the mock instance that was created
    mockSdkClient = (Client as unknown as ReturnType<typeof vi.fn>).mock.results[0].value;
  });

  describe("search", () => {
    it("should search pages and databases", async () => {
      mockSdkClient.search.mockResolvedValueOnce({
        results: [
          {
            object: "page",
            id: "page-1",
            url: "https://notion.so/page-1",
            last_edited_time: "2026-02-16T00:00:00.000Z",
            properties: {
              Name: {
                type: "title",
                title: [{ plain_text: "Test Page" }],
              },
            },
          },
          {
            object: "database",
            id: "db-1",
            url: "https://notion.so/db-1",
            last_edited_time: "2026-02-15T00:00:00.000Z",
            title: [{ plain_text: "Test DB" }],
          },
        ],
      });

      const results = await notionClient.search("test");

      expect(results).toHaveLength(2);
      expect(results[0]).toEqual({
        id: "page-1",
        type: "page",
        title: "Test Page",
        url: "https://notion.so/page-1",
        last_edited_time: "2026-02-16T00:00:00.000Z",
      });
      expect(results[1]).toEqual({
        id: "db-1",
        type: "database",
        title: "Test DB",
        url: "https://notion.so/db-1",
        last_edited_time: "2026-02-15T00:00:00.000Z",
      });
    });

    it("should pass filter when specified", async () => {
      mockSdkClient.search.mockResolvedValueOnce({ results: [] });

      await notionClient.search("query", "page", 5);

      expect(mockSdkClient.search).toHaveBeenCalledWith({
        query: "query",
        page_size: 5,
        filter: { value: "page", property: "object" },
      });
    });

    it("should not include filter when not specified", async () => {
      mockSdkClient.search.mockResolvedValueOnce({ results: [] });

      await notionClient.search("query");

      expect(mockSdkClient.search).toHaveBeenCalledWith({
        query: "query",
        page_size: 10,
      });
    });
  });

  describe("getPage", () => {
    it("should retrieve and simplify a page", async () => {
      mockSdkClient.pages.retrieve.mockResolvedValueOnce({
        id: "page-1",
        url: "https://notion.so/page-1",
        created_time: "2026-02-16T00:00:00.000Z",
        last_edited_time: "2026-02-16T12:00:00.000Z",
        properties: {
          Name: {
            type: "title",
            title: [{ plain_text: "My Page" }],
          },
        },
      });

      const page = await notionClient.getPage("page-1");

      expect(page.id).toBe("page-1");
      expect(page.title).toBe("My Page");
      expect(page.url).toBe("https://notion.so/page-1");
    });
  });

  describe("createPage", () => {
    it("should create a page with properties", async () => {
      const createParams = {
        parent: { page_id: "parent-1" },
        properties: {
          title: { title: [{ text: { content: "New Page" } }] },
        },
      };

      mockSdkClient.pages.create.mockResolvedValueOnce({
        id: "new-page-1",
        url: "https://notion.so/new-page-1",
        created_time: "2026-02-16T00:00:00.000Z",
        last_edited_time: "2026-02-16T00:00:00.000Z",
        properties: {
          title: {
            type: "title",
            title: [{ plain_text: "New Page" }],
          },
        },
      });

      const page = await notionClient.createPage(createParams);

      expect(page.id).toBe("new-page-1");
      expect(page.title).toBe("New Page");
      expect(mockSdkClient.pages.create).toHaveBeenCalledWith(createParams);
    });
  });

  describe("queryDatabase", () => {
    it("should query database and return simplified pages", async () => {
      mockSdkClient.databases.query.mockResolvedValueOnce({
        results: [
          {
            id: "row-1",
            url: "https://notion.so/row-1",
            created_time: "2026-02-16T00:00:00.000Z",
            last_edited_time: "2026-02-16T00:00:00.000Z",
            properties: {
              Name: {
                type: "title",
                title: [{ plain_text: "Row 1" }],
              },
              Status: {
                type: "select",
                select: { name: "Done" },
              },
            },
          },
        ],
      });

      const results = await notionClient.queryDatabase("db-1");

      expect(results).toHaveLength(1);
      expect(results[0].title).toBe("Row 1");
    });
  });

  describe("getDatabase", () => {
    it("should retrieve and simplify a database", async () => {
      mockSdkClient.databases.retrieve.mockResolvedValueOnce({
        id: "db-1",
        url: "https://notion.so/db-1",
        title: [{ plain_text: "My Database" }],
        description: [{ plain_text: "A test database" }],
        properties: {
          Name: { type: "title", name: "Name" },
          Status: { type: "select", name: "Status" },
        },
      });

      const db = await notionClient.getDatabase("db-1");

      expect(db.id).toBe("db-1");
      expect(db.title).toBe("My Database");
      expect(db.description).toBe("A test database");
      expect(db.properties.Name).toEqual({ type: "title", name: "Name" });
    });
  });
});
