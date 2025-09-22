import express from "express";
import fetch from "node-fetch";
import { v4 as uuidv4 } from "uuid";

/**
 * MCP-style HTTP JSON-RPC server wrapping the Policy Proxy.
 * Tools:
 *  - foodtec.export_menu
 *  - foodtec.validate_order
 *  - foodtec.accept_order
 */
const app = express();
app.use(express.json({ limit: "1mb" }));

const PORT = Number(process.env.MCP_PORT ?? 9090);
const PROXY = process.env.PROXY_BASE ?? "http://127.0.0.1:8080/apiclient";

// ---- JSON-RPC helpers ----
type JsonRpcReq = { jsonrpc: "2.0"; id?: string | number | null; method: string; params?: any };
const rpcOk  = (id: any, result: any) => ({ jsonrpc: "2.0", id, result });
const rpcErr = (id: any, code: number, message: string, data?: any) =>
  ({ jsonrpc: "2.0", id, error: { code, message, data } });

// ---- expected API response type ----
interface ApiResponse {
  ok?: boolean;
  message?: string;
  [key: string]: any;
}

// ---- tool discovery ----
const tools = [
  { name: "foodtec.export_menu",   description: "Export menu JSON (proxy → /menu)",            params: { type: "object", properties: { store_id: { type: "string" } } } },
  { name: "foodtec.validate_order",description: "Validate order draft (proxy → /validateOrder)",params: { type: "object" } },
  { name: "foodtec.accept_order",  description: "Accept order (idempotent; proxy → /acceptOrder)",
    params: { type: "object", properties: { draft: { type: "object" }, idem: { type: "string" } } } }
];

app.get("/.well-known/mcp/tools", (_req, res) => res.json({ tools }));

// ---- JSON-RPC endpoint ----
app.post("/rpc", async (req, res) => {
  const r = req.body as JsonRpcReq | JsonRpcReq[];
  let replayHeader: string | null = null;

  const handle = async (one: JsonRpcReq) => {
    if (!one || one.jsonrpc !== "2.0" || !one.method) return rpcErr(null, -32600, "Invalid Request");
    try {
      switch (one.method) {
        case "foodtec.export_menu": {
          const store = one.params?.store_id ?? "default";
          const url = new URL(`${PROXY}/menu`);
          if (store) url.searchParams.set("store_id", String(store));
          const rr = await fetch(url);
          interface ApiResponse {
            ok?: boolean;
            message?: string;
            [key: string]: any;
          }
          const j = (await rr.json()) as unknown as ApiResponse;
          if (!rr.ok) return rpcErr(one.id, -32000, "UPSTREAM_ERROR", j);
          return rpcOk(one.id, j);
        }
        case "foodtec.validate_order": {
          const rr = await fetch(`${PROXY}/validateOrder`, {
            method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(one.params ?? {})
          });
          interface ApiResponse {
            ok?: boolean;
            message?: string;
            [key: string]: any;
          }
          const j = (await rr.json()) as unknown as ApiResponse;
          if (!rr.ok || j.ok === false) return rpcErr(one.id, -32000, j.message || "VALIDATION_ERROR", j);
          return rpcOk(one.id, j);
        }
        case "foodtec.accept_order": {
          const idem = one.params?.idem || uuidv4();
          const body = { ...(one.params?.draft || one.params || {}) };
          const rr = await fetch(`${PROXY}/acceptOrder`, {
            method: "POST",
            headers: { "content-type": "application/json", "Idempotency-Key": String(idem) },
            body: JSON.stringify(body)
          });
          // capture replay header if present
          const rh = rr.headers.get("x-idempotency-replay") || rr.headers.get("X-Idempotency-Replay");
          if (rh) replayHeader = rh;
          interface ApiResponse {
            ok?: boolean;
            message?: string;
            [key: string]: any;
          }
          const j = (await rr.json()) as unknown as ApiResponse;
          if (!rr.ok || j.ok === false) return rpcErr(one.id, -32000, j.message || "UPSTREAM_ERROR", j);
          return rpcOk(one.id, { idem, ...j });
        }
        default:
          return rpcErr(one.id, -32601, `Method not found: ${one.method}`);
      }
    } catch (e: any) {
      return rpcErr(one.id, -32098, e?.message || "Proxy failure");
    }
  };

  if (Array.isArray(r)) {
    const out = await Promise.all(r.map(handle));
    if (replayHeader) res.setHeader("X-Idempotency-Replay", replayHeader);
    res.json(out);
  } else {
    const out = await handle(r);
    if (replayHeader) res.setHeader("X-Idempotency-Replay", replayHeader);
    res.json(out);
  }
});

// health
app.get("/healthz", (_req, res) => res.json({ ok: true, mcp: true, proxy: PROXY }));
app.listen(PORT, () => console.log(`MCP server on :${PORT} → Proxy ${PROXY}`));
export {};
