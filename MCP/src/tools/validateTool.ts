// src/tools/validateTool.ts
import { ToolDefinition } from "../types.js";
import { callProxyRpc } from "../proxy/client.js";

// Tool metadata
export const validateTool: ToolDefinition = {
  name: "foodtec.validate_order",
  description: "Validates a FoodTec order draft",
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
        description: "Original price"
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
export async function handleValidate(params: any) {
  try {
    console.log(`[MCP] Calling proxy for foodtec.validate_order with params:`, params);
    
    const proxyResponse = await callProxyRpc("foodtec.validate_order", params);
    
    console.log(`[MCP] Proxy response status:`, proxyResponse.status);
    
    if (proxyResponse.data && proxyResponse.data.result) {
      return proxyResponse.data.result;
    } else if (proxyResponse.data && proxyResponse.data.error) {
      throw new Error(`Proxy error: ${proxyResponse.data.error.message}`);
    } else {
      throw new Error(`Unexpected proxy response: ${JSON.stringify(proxyResponse.data)}`);
    }
  } catch (error: any) {
    console.error(`[MCP] Validate tool error:`, error.message);
    throw error;
  }
}