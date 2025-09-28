// ------------------------------------------------
// JSON-RPC types (per spec)
// https://modelcontextprotocol.io/specification/2025-03-26/basic
// ------------------------------------------------

export type JsonRpcId = string | number;
export type JsonRpcRequest = { jsonrpc: "2.0"; id: JsonRpcId; method: string; params?: Record<string, unknown>; };
export type JsonRpcResult = { jsonrpc: "2.0"; id: JsonRpcId; result: unknown; };
export type JsonRpcError = { jsonrpc: "2.0"; id: JsonRpcId | null; error: { code: number; message: string; data?: unknown } };
export type JsonRpcResponse = JsonRpcResult | JsonRpcError;

// ------------------------------------------------
// MCP Tool Definition types
// ------------------------------------------------

export interface ToolDefinition {
  name: string;
  description: string;
  parameters: {
    type: "object";
    properties: Record<string, {
      type: string;
      description?: string;
    }>;
    required: string[];
  };
}
