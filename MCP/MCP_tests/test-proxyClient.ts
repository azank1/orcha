// temp test-proxyclient.ts in mcp/src
import { callProxyRpc } from "./proxyClient.js";

(async () => {
  const resp = await callProxyRpc("foodtec.export_menu", { orderType: "Pickup" });
  console.log("Status:", resp.status);
  console.log("Data:", JSON.stringify(resp.data, null, 2));
})();