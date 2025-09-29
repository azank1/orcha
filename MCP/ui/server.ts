import express from "express";
import path from "path";
import { fileURLToPath } from "url";
import { engine } from "express-handlebars";
import axios from "axios";

// Recreate __dirname in ESM
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = 3001; // UI runs here

// Configure Handlebars
app.engine("hbs", engine({ extname: ".hbs", defaultLayout: false }));
app.set("view engine", "hbs");
app.set("views", path.join(__dirname, "views"));

// Serve static files (CSS, JS)
app.use(express.static(path.join(__dirname, "public")));

// Add JSON parsing middleware
app.use(express.json());

// Render menu
app.get("/", async (req, res) => {
  // Just render the UI without loading menu data on initial page load
  // This makes the initial page load fast and prevents crashes
  res.render("menu", { 
    loadDataOnDemand: true,
    categories: []
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

app.listen(PORT, () => {
  console.log(`MCP-UI running on http://127.0.0.1:${PORT}`);
});