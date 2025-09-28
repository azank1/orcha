// src/tools/menuTool.ts
import { ToolDefinition } from "../types.js";
import { callProxyRpc } from "../proxy/client.js";

// Tool metadata
export const menuTool: ToolDefinition = {
  name: "foodtec.export_menu",
  description: "Exports the menu from FoodTec sandbox",
  parameters: {
    type: "object",
    properties: {
      orderType: {
        type: "string",
        description: "Type of order (Pickup, Delivery, etc.)"
      }
    },
    required: ["orderType"]
  }
};

// Real handler that calls proxy
export async function handleMenu(params: any) {
  try {
    console.log(`[MCP] Calling proxy for foodtec.export_menu with params:`, params);
    
    // Call proxy with the same method name
    const proxyResponse = await callProxyRpc("foodtec.export_menu", params);
    
    console.log(`[MCP] Proxy response status:`, proxyResponse.status);
    
    // Return the proxy's JSON-RPC result
    if (proxyResponse.data && proxyResponse.data.result) {
      return proxyResponse.data.result;
    } else if (proxyResponse.data && proxyResponse.data.error) {
      throw new Error(`Proxy error: ${proxyResponse.data.error.message}`);
    } else {
      throw new Error(`Unexpected proxy response: ${JSON.stringify(proxyResponse.data)}`);
    }
  } catch (error: any) {
    console.error(`[MCP] Menu tool error:`, error.message);
    throw error;
  }
}