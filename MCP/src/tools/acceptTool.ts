// src/tools/acceptTool.ts
import { ToolDefinition } from "../types.js";
import { callProxyRpc } from "../proxy/client.js";

// TODO: Refactor to vendor-agnostic orders.submit() once multi-vendor support is added
// Strict schema to prevent tax-on-tax regression
export const acceptOrderParamsSchema = {
  type: "object",
  additionalProperties: false,
  required: ["category", "item", "size", "customer", "menuPrice", "canonicalPrice", "externalRef"],
  properties: {
    category: { type: "string", minLength: 1 },
    item: { type: "string", minLength: 1 },
    size: { type: "string", minLength: 1 },
    customer: {
      type: "object",
      additionalProperties: false,
      required: ["name", "phone"],
      properties: {
        name: { type: "string", minLength: 1 },
        phone: { type: "string", pattern: "^[0-9]{3}-[0-9]{3}-[0-9]{4}$" }
      }
    },
    externalRef: { type: "string", minLength: 3 },
    menuPrice: { type: "number", minimum: 0 },      // item sellingPrice (no tax)
    canonicalPrice: { type: "number", minimum: 0 }, // order price (with tax)
    idem: { type: "string", minLength: 3 }
  }
};

// Tool metadata (keep FoodTec-specific for now)
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
      menuPrice: {
        type: "number",
        description: "Original menu price (without tax)"
      },
      canonicalPrice: {
        type: "number",
        description: "Canonical price from validation (with tax)"
      },
      customer: {
        type: "object",
        description: "Customer information with name and phone (format: XXX-XXX-XXXX)"
      },
      externalRef: {
        type: "string",
        description: "External reference ID for idempotency"
      },
      idem: {
        type: "string",
        description: "Idempotency key"
      }
    },
    required: ["category", "item", "size", "menuPrice", "canonicalPrice", "customer", "externalRef"]
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