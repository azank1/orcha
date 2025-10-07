import express from "express";
import path from "path";
import { fileURLToPath } from "url";
import { engine } from "express-handlebars";
import axios from "axios";

// Recreate __dirname in ESM
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Determine base directory (handles both src and dist)
const baseDir = __dirname.endsWith('dist') ? path.join(__dirname, '..') : __dirname;

// Configuration
const app = express();
const PORT = 3001; // UI runs here
const MCP_ENDPOINT = "http://127.0.0.1:9090/rpc"; // MCP JSON-RPC endpoint
const AUTOMATION_ENABLED = process.env.AUTOMATION_ENABLED !== "false"; // Enable/disable automation

// Import automation integration (to be replaced with actual import when ready)
// import { registerAutomationRoutes } from "../../automation/server-integration.js";

// Configure Handlebars
app.engine("hbs", engine({ extname: ".hbs", defaultLayout: false }));
app.set("view engine", "hbs");
app.set("views", path.join(baseDir, "views"));

// Serve static files (CSS, JS)
app.use(express.static(path.join(baseDir, "public")));

// Add JSON parsing middleware
app.use(express.json());

// Render menu - DO NOT call MCP on page load, let the button do it
app.get("/", async (req, res) => {
  // Just render empty page, let the Export Menu button populate it
  res.render("menu", { 
    categories: [],
    initialLoad: true
  });
});

// Add middleware to parse JSON requests
app.use(express.json());

// Add /mcp endpoint to proxy requests to MCP
app.post('/mcp', async (req, res) => {
  try {
    const response = await axios.post('http://127.0.0.1:9090/rpc', req.body, {
      headers: { 'Content-Type': 'application/json' }
    });
    const data = response.data;
    res.json(data);
  } catch (err: any) {
    console.error("Error calling MCP:", err);
    res.status(500).json({ error: "Failed to reach MCP", message: err.message });
  }
});

// API Routes for automation - Proxy to Python automation service
app.post("/api/automation/process-order", async (req, res) => {
  try {
    const { text } = req.body;
    if (!text || typeof text !== 'string') {
      return res.status(400).json({ 
        success: false, 
        error: "Missing or invalid 'text' parameter" 
      });
    }

    console.log("Processing natural language order:", text);

    // Set up SSE headers
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');

    try {
      // Forward to Python automation service
      const response = await axios.post('http://127.0.0.1:5000/process', 
        { text },
        { 
          responseType: 'stream',
          timeout: 60000
        }
      );

      // Pipe the stream
      response.data.pipe(res);
      
    } catch (error: any) {
      console.error('Automation service error:', error);
      res.write(`data: ${JSON.stringify({ 
        type: 'error', 
        content: error.message || 'Automation service unavailable. Make sure it is running on port 5000.',
        timestamp: Date.now()
      })}\n\n`);
      res.end();
    }
  } catch (error: any) {
    console.error('Automation API error:', error);
    res.status(500).json({
      success: false,
      error: 'Internal server error processing the order'
    });
  }
});

app.listen(PORT, () => {
  console.log(`MCP-UI running on http://127.0.0.1:${PORT}`);
});