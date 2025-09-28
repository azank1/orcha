// src/tools.ts
import { tools } from "./dispatcher.js";
import { ToolDefinition } from "./types.js";

export function listTools(): ToolDefinition[] {
  return tools;
}

// Export tools array for compatibility
export { tools };
