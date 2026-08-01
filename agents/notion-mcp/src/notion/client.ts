/**
 * Notion API client wrapper.
 * Uses @notionhq/client for all Notion operations.
 */
import { Client } from "@notionhq/client";
import type {
  SearchResponse,
  PageObjectResponse,
  DatabaseObjectResponse,
  BlockObjectResponse,
  CreatePageParameters,
  UpdatePageParameters,
  QueryDatabaseParameters,
} from "@notionhq/client/build/src/api-endpoints.js";
import type { SimplifiedPage, SimplifiedDatabase, SearchResult } from "../types.js";

export class NotionClient {
  private client: Client;

  constructor(apiKey: string) {
    this.client = new Client({ auth: apiKey });
  }

  // ── Search ─────────────────────────────────────────────────

  async search(query: string, filter?: "page" | "database", pageSize = 10): Promise<SearchResult[]> {
    const params: Parameters<Client["search"]>[0] = {
      query,
      page_size: pageSize,
    };

    if (filter) {
      params.filter = { value: filter, property: "object" };
    }

    const response: SearchResponse = await this.client.search(params);

    return response.results.map((result) => {
      if (result.object === "page") {
        const page = result as PageObjectResponse;
        return {
          id: page.id,
          type: "page" as const,
          title: this.extractPageTitle(page),
          url: page.url,
          last_edited_time: page.last_edited_time,
        };
      } else {
        const db = result as DatabaseObjectResponse;
        return {
          id: db.id,
          type: "database" as const,
          title: this.extractDatabaseTitle(db),
          url: db.url,
          last_edited_time: db.last_edited_time,
        };
      }
    });
  }

  // ── Pages ──────────────────────────────────────────────────

  async getPage(pageId: string): Promise<SimplifiedPage> {
    const page = (await this.client.pages.retrieve({
      page_id: pageId,
    })) as PageObjectResponse;

    return {
      id: page.id,
      url: page.url,
      title: this.extractPageTitle(page),
      created_time: page.created_time,
      last_edited_time: page.last_edited_time,
      properties: page.properties,
    };
  }

  async createPage(params: CreatePageParameters): Promise<SimplifiedPage> {
    const page = (await this.client.pages.create(params)) as PageObjectResponse;

    return {
      id: page.id,
      url: page.url,
      title: this.extractPageTitle(page),
      created_time: page.created_time,
      last_edited_time: page.last_edited_time,
      properties: page.properties,
    };
  }

  async updatePage(pageId: string, properties: UpdatePageParameters["properties"]): Promise<SimplifiedPage> {
    const page = (await this.client.pages.update({
      page_id: pageId,
      properties: properties ?? {},
    })) as PageObjectResponse;

    return {
      id: page.id,
      url: page.url,
      title: this.extractPageTitle(page),
      created_time: page.created_time,
      last_edited_time: page.last_edited_time,
      properties: page.properties,
    };
  }

  // ── Databases ──────────────────────────────────────────────

  async queryDatabase(
    databaseId: string,
    filter?: QueryDatabaseParameters["filter"],
    sorts?: QueryDatabaseParameters["sorts"],
    pageSize = 100
  ): Promise<SimplifiedPage[]> {
    const params: QueryDatabaseParameters = {
      database_id: databaseId,
      page_size: pageSize,
    };
    if (filter) params.filter = filter;
    if (sorts) params.sorts = sorts;

    const response = await this.client.databases.query(params);

    return response.results.map((result) => {
      const page = result as PageObjectResponse;
      return {
        id: page.id,
        url: page.url,
        title: this.extractPageTitle(page),
        created_time: page.created_time,
        last_edited_time: page.last_edited_time,
        properties: page.properties,
      };
    });
  }

  async getDatabase(databaseId: string): Promise<SimplifiedDatabase> {
    const db = (await this.client.databases.retrieve({
      database_id: databaseId,
    })) as DatabaseObjectResponse;

    const properties: Record<string, { type: string; name: string }> = {};
    for (const [key, value] of Object.entries(db.properties)) {
      properties[key] = { type: value.type, name: value.name };
    }

    return {
      id: db.id,
      url: db.url,
      title: this.extractDatabaseTitle(db),
      description: db.description.map((d) => d.plain_text).join(""),
      properties,
    };
  }

  // ── Blocks ─────────────────────────────────────────────────

  async getBlockChildren(blockId: string): Promise<BlockObjectResponse[]> {
    const response = await this.client.blocks.children.list({
      block_id: blockId,
      page_size: 100,
    });

    return response.results as BlockObjectResponse[];
  }

  async appendBlocks(
    blockId: string,
    children: Parameters<Client["blocks"]["children"]["append"]>[0]["children"]
  ): Promise<BlockObjectResponse[]> {
    const response = await this.client.blocks.children.append({
      block_id: blockId,
      children,
    });

    return response.results as BlockObjectResponse[];
  }

  // ── Helpers ────────────────────────────────────────────────

  private extractPageTitle(page: PageObjectResponse): string {
    for (const prop of Object.values(page.properties)) {
      if (prop.type === "title" && prop.title.length > 0) {
        return prop.title.map((t) => t.plain_text).join("");
      }
    }
    return "Untitled";
  }

  private extractDatabaseTitle(db: DatabaseObjectResponse): string {
    if (db.title.length > 0) {
      return db.title.map((t) => t.plain_text).join("");
    }
    return "Untitled Database";
  }
}
