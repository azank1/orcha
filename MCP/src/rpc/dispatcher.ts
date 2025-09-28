// orcha-1/mcp/src/rpc/dispatcher.ts
import type { Request, Response } from "express";
import { z } from "zod";
import type { JsonRpcRequest, JsonRpcResponse } from "../types.js";
import { callProxyRpc } from "../proxy/client.js";
import { listTools } from "../tools.js";
import { dispatchTool } from "../dispatcher.js";

// JSON-RPC request schema
const RpcRequestSchema = z.object({
  jsonrpc: z.literal("2.0"),
  id: z.union([z.string(), z.number()]),
  method: z.string(),
  params: z.record(z.string(), z.unknown()).optional(),
});

// Helper: JSON-RPC error envelope
function jerr(
  id: JsonRpcRequest["id"] | null,
  code: number,
  message: string,
  data?: unknown
): JsonRpcResponse {
  return { jsonrpc: "2.0", id, error: { code, message, data } };
}

// Core RPC handler function
export async function handleRpc(request: any, headers: Record<string, string> = {}) {
  if (request.method === "list_tools") {
    return { tools: listTools() };
  }
  
  // Tool call
  try {
    const result = await dispatchTool(request.method, request.params, headers);
    return { result };
  } catch (err: any) {
    return { error: err.message };
  }
}

// Optional: basic guardrail (allowed tool names)
const ALLOWED_METHODS = new Set([
  "list_tools",
  "foodtec.export_menu",
  "foodtec.validate_order",
  "foodtec.accept_order",
]);

export async function rpcHandler(req: Request, res: Response): Promise<void> {
  // Forward Idempotency-Key and Request-Id if present
  const fwdHeaders: Record<string, string> = {};
  const idem = req.header("Idempotency-Key");
  if (idem) fwdHeaders["Idempotency-Key"] = idem;
  const rid = req.header("X-Request-ID");
  if (rid) fwdHeaders["X-Request-ID"] = rid;

  // Require JSON body
  if (!req.is("application/json")) {
    res.status(200).json(jerr(null, -32600, "Invalid Request: expected application/json"));
    return;
  }

  // Parse JSON-RPC envelope
  const parsed = RpcRequestSchema.safeParse(req.body);
  if (!parsed.success) {
    res.status(200)
      .json(jerr(null, -32600, "Invalid Request", parsed.error.flatten()));
    return;
  }
  const r = parsed.data;

  // Method allowlist (prevent accidental exposure)
  if (!ALLOWED_METHODS.has(r.method)) {
  res.status(200).json(jerr(r.id, -32601, "Method not found"));
  return;
  }

  try {
    // Try local handler first for all our MCP tools
    if (r.method === "list_tools" || 
        r.method === "foodtec.export_menu" || 
        r.method === "foodtec.validate_order" || 
        r.method === "foodtec.accept_order") {
      const localResult = await handleRpc(r, fwdHeaders);
      if (localResult.error) {
        res.status(200).json(jerr(r.id, -32000, localResult.error));
        return;
      }
      res.status(200).json({ jsonrpc: "2.0", id: r.id, result: localResult.result || localResult });
      return;
    }
    
    // Call Proxy JSON-RPC (pass-through)
  const proxyResp = await callProxyRpc(r.method, (r.params ?? {}) as any, fwdHeaders);

    // Proxy should always return JSON-RPC envelope
    // We propagate Proxy’s result/error as-is (same jsonrpc/id semantics)
    const data = proxyResp.data;

    // Propagate Proxy idempotency replay header to MCP response (nice-to-have)
    const replay = proxyResp.headers["x-idempotency-replay"];
    if (replay) res.setHeader("X-Idempotency-Replay", String(replay));
    const proxyIdem = proxyResp.headers["idempotency-key"];
    if (proxyIdem) res.setHeader("Idempotency-Key", String(proxyIdem));

    // Defensive: if Proxy didn’t return a JSON-RPC envelope, wrap it
    if (!data || data.jsonrpc !== "2.0" || (data.result === undefined && data.error === undefined)) {
      res
        .status(200)
        .json(jerr(r.id, -32000, "Upstream returned non-JSON-RPC payload", { status: proxyResp.status, data }));
      return;
    }

    // Everything good → just pass it through
    res.status(200).json(data);
    return;
  } catch (e: any) {
    // Network/transport failure → implementation-defined error
    res.status(200).json(jerr(r.id, -32000, e?.message ?? "Proxy call failed"));
    return;
  }
}