// ------------------------------------------------
// Minimal MCP tool discovery payload
// https://modelcontextprotocol.io/docs/concepts/tools
// ------------------------------------------------
const tools = [
  {
    name: "foodtec.export_menu",
    description: "Export menu by order type",
    inputSchema: {
      type: "object",
      properties: { orderType: { type: "string" } },
      required: ["orderType"],
      additionalProperties: false
    }
  },
  {
    name: "foodtec.validate_order",
    description: "Validate an order draft",
    inputSchema: {
      type: "object",
      properties: { draft: { type: "object" } },
      required: ["draft"],
      additionalProperties: false
    }
  },
  {
    name: "foodtec.accept_order",
    description: "Accept an order (idempotent)",
    inputSchema: {
      type: "object",
      properties: {
        draft: { type: "object" },
        idem: { type: "string" }
      },
      required: ["draft"],
      additionalProperties: false
    }
  }
];

export { tools };
