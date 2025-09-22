// proxy/src/index.ts
import express from "express";
import { randomUUID } from "crypto";
import fetch from "node-fetch";

const app = express();
app.use(express.json());

// --- CONSTANTS ---
const MENU_TTL_MS = 600_000; // 10 minutes
const IDEMPOTENCY_TTL_MS = 600_000; // 10 minutes
const VERSION = "1.0.0";
const SERVICE_NAME = "orcha-proxy";
const P2A_BASE = process.env.P2A_BASE || "http://127.0.0.1:8000/rpc";

// --- STORAGE ---
const menuCache = new Map<string, { t: number; data: any }>();
const acceptLedger = new Map<string, {
  t: number; // timestamp for TTL
  requestId: string; 
  response: any;
}>();

// --- LOGGING ---
type LogLevel = "debug" | "info" | "warn" | "error";

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  service: string;
  requestId?: string;
  message: string;
  data?: any;
}

function log(level: LogLevel, message: string, requestId?: string, data?: any) {
  const entry: LogEntry = {
    timestamp: new Date().toISOString(),
    level,
    service: SERVICE_NAME,
    message
  };
  
  if (requestId) entry.requestId = requestId;
  if (data) entry.data = data;
  
  console.log(JSON.stringify(entry));
  return entry;
}

// ---- JSON-RPC types ----
type JsonRpcResp = {
  jsonrpc: "2.0";
  id?: any;
  result?: any;
  error?: { code: number; message: string; data?: any };
};

// --- MIDDLEWARE ---
app.use((req, res, next) => {
  // Extract or generate request ID
  const requestId = req.headers['x-request-id'] as string || randomUUID();
  res.setHeader('X-Request-ID', requestId);
  
  // Attach to request for logging
  (req as any).requestId = requestId;
  
  // Log request
  log('info', `${req.method} ${req.path}`, requestId, {
    query: req.query,
    headers: { 
      'content-type': req.headers['content-type'],
      'idempotency-key': req.headers['idempotency-key'],
      'x-request-id': requestId
    }
  });
  
  // Track response time
  const start = Date.now();
  res.on('finish', () => {
    const duration = Date.now() - start;
    log('info', `${req.method} ${req.path} ${res.statusCode} ${duration}ms`, requestId);
  });
  
  next();
});

// --- HELPERS ---
const ok = (res: any, data: any) => res.json({ ok: true, ...data });

const err = (res: any, code: string, msg: string, status = 400) => {
  log('warn', `Error: ${code} - ${msg}`, (res.req as any).requestId);
  return res.status(status).json({ 
    ok: false, 
    code, 
    message: msg, 
    meta: { status } 
  });
};

/**
 * GET /apiclient/menu
 * - Returns a cached mock menu for the store (if provided).
 * - Mirrors Ftg "Menu Export" behavior enough for orchestration tests.
 */
app.get("/apiclient/menu", async (req, res) => {
  const store = String(req.query.store_id ?? "default");
  const key = `menu:${store}`;
  const hit = menuCache.get(key);
  const now = Date.now();

  if (hit && now - hit.t < MENU_TTL_MS) return res.json(hit.data);

  // Forward to P2A /rpc: foodtec.export_menu
  try {
    const rpcBody = { jsonrpc: "2.0", id: randomUUID(), method: "foodtec.export_menu", params: { store_id: store } };
  const rr = await fetch(P2A_BASE, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(rpcBody) });
  const jj = (await rr.json()) as JsonRpcResp;
    if (jj?.error) {
      const code = 500;
      return err(res, "UPSTREAM", jj.error?.message || "P2A export error", code);
    }
    const data = { ok: true, store_id: store, ...(jj?.result || {}) };
    menuCache.set(key, { t: now, data });
    return res.json(data);
  } catch (e: any) {
    return err(res, "UPSTREAM", e?.message || "P2A export failure", 502);
  }
});

/**
 * POST /apiclient/validateOrder
 * - Validates a mock order draft.
 * - Returns VALIDATION error for bad/missing items (422).
 */
app.post("/apiclient/validateOrder", async (req, res) => {
  const draft = req.body || {};
  try {
    const rpcBody = { jsonrpc: "2.0", id: randomUUID(), method: "foodtec.validate_order", params: draft };
  const rr = await fetch(P2A_BASE, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(rpcBody) });
  const jj = (await rr.json()) as JsonRpcResp;
    if (jj?.error) {
      const message = jj.error?.message || "VALIDATION_ERROR";
      // Map validation errors to 422
      return err(res, "VALIDATION", message, 422);
    }
    const result = jj?.result || {};
    return res.json({ ok: true, ...result });
  } catch (e: any) {
    return err(res, "UPSTREAM", e?.message || "P2A validate failure", 502);
  }
});

/**
 * POST /apiclient/acceptOrder
 * - Requires Idempotency-Key to avoid duplicate orders.
 * - Returns a mock confirmation payload.
 * - Caches responses for 10 minutes.
 * - Sets X-Idempotent-Replayed header on replays.
 */
app.post("/apiclient/acceptOrder", async (req, res) => {
  const requestId = (req as any).requestId;
  const idem = req.header("Idempotency-Key");

  if (!idem) {
    return err(res, "MISSING_IDEM", "Idempotency-Key header is required", 400);
  }

  const now = Date.now();
  const entry = acceptLedger.get(idem);
  if (entry && (now - entry.t < IDEMPOTENCY_TTL_MS)) {
    res.setHeader("Idempotency-Key", idem);
    res.setHeader("X-Idempotency-Replay", "true");
    log('info', `Idempotent replay for key: ${idem}`, requestId, { originalRequestId: entry.requestId, age: now - entry.t });
    return res.json(entry.response);
  }

  const draft = req.body || {};
  try {
    const rpcBody = { jsonrpc: "2.0", id: randomUUID(), method: "foodtec.accept_order", params: { draft, idem } };
    const rr = await fetch(P2A_BASE, {
      method: "POST",
      headers: { "content-type": "application/json", "Idempotency-Key": String(idem) },
      body: JSON.stringify(rpcBody)
    });
    const jj = (await rr.json()) as JsonRpcResp;
    if (jj?.error) {
      const message = jj.error?.message || "ACCEPT_FAILED";
      return err(res, "UPSTREAM", message, 400);
    }
    const result = jj?.result || {};
    const confirmation = { ...result };
    // Cache it for idempotency
    acceptLedger.set(idem, { t: now, requestId, response: confirmation });
    res.setHeader("Idempotency-Key", idem);
    return res.json(confirmation);
  } catch (e: any) {
    return err(res, "UPSTREAM", e?.message || "P2A accept failure", 502);
  }
});

/**
 * GET /healthz - Health check endpoint
 * Returns service health status including:
 * - ok: boolean
 * - ts: timestamp
 * - service: service name
 * - version: service version
 * - uptime: server uptime in seconds
 */
app.get("/healthz", (req, res) => {
  const requestId = (req as any).requestId;
  log('debug', 'Health check requested', requestId);
  
  res.json({
    ok: true,
    ts: Date.now(),
    service: SERVICE_NAME,
    version: VERSION,
    uptime: process.uptime()
  });
});

/**
 * GET /metrics - Basic metrics endpoint
 * Returns simple metrics about cache sizes and request counts
 */
app.get("/metrics", (req, res) => {
  const requestId = (req as any).requestId;
  const metrics = {
    menuCacheSize: menuCache.size,
    acceptLedgerSize: acceptLedger.size,
    timestamp: Date.now()
  };
  
  log('debug', 'Metrics requested', requestId, metrics);
  res.json(metrics);
});

// Clean up expired entries periodically
setInterval(() => {
  const now = Date.now();
  
  // Clean idempotency cache
  let expiredCount = 0;
  for (const [key, entry] of acceptLedger.entries()) {
    if (now - entry.t > IDEMPOTENCY_TTL_MS) {
      acceptLedger.delete(key);
      expiredCount++;
    }
  }
  
  if (expiredCount > 0) {
    log('debug', `Cleaned up ${expiredCount} expired idempotency entries`);
  }
}, 60_000); // Run every minute

// Start server
const PORT = Number(process.env.PORT || 8080);
app.listen(PORT, () => {
  log('info', `Proxy server running on port ${PORT}`, undefined, {
    port: PORT,
    version: VERSION
  });
});

export {}; // keep TS module mode happy
