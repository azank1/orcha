import axios from "axios";

const PROXY_RPC_URL =
  process.env.PROXY_RPC_URL?.trim() || "http://127.0.0.1:8080/rpc";

export async function callProxyRpc(
  method: string,
  params: Record<string, unknown> | undefined,
  headers: Record<string, string> = {}
) {
  // JSON-RPC envelope to Proxy
  const body = {
    jsonrpc: "2.0",
    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    method,
    params: params ?? {},
  };

  const resp = await axios.post(PROXY_RPC_URL, body, {
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
    // keep Proxy error payloads visible (don’t throw on 4xx/5xx)
    validateStatus: () => true,
  });

  // Return full axios response (we need headers like X-Idempotency-Replay)
  return resp;
}