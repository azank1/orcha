// src/tools/acceptTool.ts
import { ToolDefinition } from "../types.js";
import { callProxyRpc } from "../proxy/client.js";

// Tool metadata
export const acceptTool: ToolDefinition = {
  name: "foodtec.accept_order",
  description: "Accepts a validated FoodTec order",
  parameters: {
    type: "object",
    properties: {
      category: {
        type: "string",
        description: "Food category (e.g. Appetizer, Pizza)"
      },
      item: {
        type: "string", 
        description: "Item name"
      },
      size: {
        type: "string",
        description: "Size (e.g. Lg, Med, Sm)"
      },
      price: {
        type: "number",
        description: "Canonical price from validation"
      },
      customer: {
        type: "object",
        description: "Customer information"
      }
    },
    required: ["category", "item", "size", "price", "customer"]
  }
};

// Real handler that calls proxy
export async function handleAccept(params: any, headers: Record<string, string> = {}) {
  try {
    console.log(`[MCP] Calling proxy for foodtec.accept_order with params:`, params);
    
    const proxyResponse = await callProxyRpc("foodtec.accept_order", params, headers);
    
    console.log(`[MCP] Proxy response status:`, proxyResponse.status);
    
    if (proxyResponse.data && proxyResponse.data.result) {
      return proxyResponse.data.result;
    } else if (proxyResponse.data && proxyResponse.data.error) {
      throw new Error(`Proxy error: ${proxyResponse.data.error.message}`);
    } else {
      throw new Error(`Unexpected proxy response: ${JSON.stringify(proxyResponse.data)}`);
    }
  } catch (error: any) {
    console.error(`[MCP] Accept tool error:`, error.message);
    throw error;
  }
}