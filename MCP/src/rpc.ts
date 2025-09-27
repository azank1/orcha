// ------------------------------------------------
// Minimal JSON-RPC router (stub handlers for now)
// MCP uses JSON-RPC 2.0 messages; either result or error.
// ------------------------------------------------
import type { Request, Response } from 'express';
import { z } from 'zod';
import type { JsonRpcRequest, JsonRpcResponse } from './types.js';

const RpcRequestSchema = z.object({
  jsonrpc: z.literal('2.0'),
  id: z.union([z.string(), z.number()]),
  method: z.string(),
  params: z.record(z.string(), z.unknown()).optional()
});

// Helper to emit JSON-RPC error
function jerr(id: JsonRpcRequest['id'] | null, code: number, message: string, data?: unknown): JsonRpcResponse {
  return { jsonrpc: '2.0', id, error: { code, message, data } } as any;
}

// Stub handlers (to be wired to Proxy later)
async function handleExportMenu(_params: any) {
  return { ok: true, note: 'stub export', categories: [] };
}
async function handleValidate(_params: any) {
  return { ok: true, note: 'stub validate' };
}
async function handleAccept(_params: any) {
  return { ok: true, note: 'stub accept', idem: 'demo' };
}

export async function rpcHandler(req: Request, res: Response) {
  try {
    const parsed = RpcRequestSchema.safeParse(req.body);
    if (!parsed.success) {
      const resp = jerr(null, -32600, 'Invalid Request', parsed.error.flatten());
      return res.status(200).json(resp);
    }
    const r = parsed.data;
    try {
      let result: unknown;
      switch (r.method) {
        case 'foodtec.export_menu':
          result = await handleExportMenu(r.params);
          break;
        case 'foodtec.validate_order':
          result = await handleValidate(r.params);
          break;
        case 'foodtec.accept_order':
          result = await handleAccept(r.params);
          break;
        default:
          return res.status(200).json(jerr(r.id, -32601, 'Method not found'));
      }
      const out: JsonRpcResponse = { jsonrpc: '2.0', id: r.id, result } as any;
      return res.status(200).json(out);
    } catch (e: any) {
      return res.status(200).json(jerr(r.id, -32000, e?.message ?? 'Server error'));
    }
  } catch (e: any) {
    return res.status(200).json(jerr(null, -32603, 'Internal error'));
  }
}
