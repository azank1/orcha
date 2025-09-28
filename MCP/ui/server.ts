import express from "express";
import path from "path";
import { fileURLToPath } from "url";
import axios from "axios";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const MCP_URL = "http://127.0.0.1:9090/rpc";

// Setup view engine
app.set("view engine", "hbs");
app.set("views", path.join(__dirname, "views"));

// Static files (CSS/JS)
app.use(express.static(path.join(__dirname, "public")));

// Root route - simple landing page
app.get("/", (req, res) => {
  res.render("menu", { 
    message: "MCP-UI Ready",
    instructions: "Visit /menu to see agent's eye view"
  });
});

// Menu route - fetches real data from MCP
app.get("/menu", async (req, res) => {
  try {
    console.log("Calling MCP server at", MCP_URL);
    const response = await axios.post(MCP_URL, {
      jsonrpc: "2.0",
      id: "ui-menu-request",
      method: "foodtec.export_menu", 
      params: { orderType: "Pickup" }
    });
    
    console.log("MCP Response received, status:", response.status);
    const menu = response.data.result;
    
    res.render("menu", {
      message: "Agent's Eye: FoodTec Menu",
      menu: menu,
      categories: menu.data || [],
      status: menu.status,
      success: menu.success
    });
  } catch (error) {
    console.error("MCP Error:", error);
    res.render("menu", {
      message: "❌ MCP Connection Error",
      error: error instanceof Error ? error.message : String(error),
      helpText: "Make sure MCP server is running on :9090"
    });
  }
});

// Start server
app.listen(3000, () => {
  console.log("MCP-UI running at http://127.0.0.1:3000");
});
