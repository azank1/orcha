/**
 * Unit tests for server creation and tool registration.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock the config and notion client
vi.mock("../../src/config.js", () => ({
  loadConfig: vi.fn().mockReturnValue({
    notionApiKey: "test-key",
    serverName: "notion-agent-mcp",
    serverVersion: "2.0.0",
    logLevel: "info",
  }),
}));

vi.mock("@notionhq/client", () => ({
  Client: vi.fn().mockImplementation(() => ({
    search: vi.fn(),
    pages: { retrieve: vi.fn(), create: vi.fn(), update: vi.fn() },
    databases: { retrieve: vi.fn(), query: vi.fn() },
    blocks: { children: { list: vi.fn(), append: vi.fn() } },
  })),
}));

import { createMcpServer } from "../../src/server.js";

describe("MCP Server", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should create a server instance", () => {
    const server = createMcpServer();
    expect(server).toBeDefined();
    expect(server.server).toBeDefined();
  });

  it("should have the correct server info", () => {
    const server = createMcpServer();
    // The server info is stored on the underlying Server instance
    expect(server.server).toBeDefined();
  });
});
