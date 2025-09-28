// src/dispatcher.ts
import { menuTool, handleMenu } from "./tools/menuTool.js";
import { validateTool, handleValidate } from "./tools/validateTool.js";
import { acceptTool, handleAccept } from "./tools/acceptTool.js";

export const tools = [menuTool, validateTool, acceptTool];

export async function dispatchTool(name: string, params: any, headers: Record<string, string> = {}) {
  switch (name) {
    case "foodtec.export_menu":
      return await handleMenu(params);
    case "foodtec.validate_order":
      return await handleValidate(params);
    case "foodtec.accept_order":
      return await handleAccept(params, headers);
    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}