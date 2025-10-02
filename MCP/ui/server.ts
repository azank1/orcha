import express from "express";
import path from "path";
import { fileURLToPath } from "url";
import { engine } from "express-handlebars";
import axios from "axios";

// Recreate __dirname in ESM
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

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
app.set("views", path.join(__dirname, "views"));

// Serve static files (CSS, JS)
app.use(express.static(path.join(__dirname, "public")));

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

// API Routes for automation
app.post("/api/automation/process-order", async (req, res) => {
  try {
    if (!AUTOMATION_ENABLED) {
      return res.status(403).json({ 
        success: false, 
        error: "Automation is disabled" 
      });
    }

    const { text } = req.body;
    if (!text || typeof text !== 'string') {
      return res.status(400).json({ 
        success: false, 
        error: "Missing or invalid 'text' parameter" 
      });
    }

    console.log("Processing natural language order:", text);

    /* INTEGRATION POINT
     * In production, this would use the actual automation component:
     * 
     * // When automation is integrated, replace this mock with:
     * import { processOrder } from "../../automation/orchestrator.js";
     * 
     * const result = await processOrder(text);
     * // Format result for UI consumption using server-integration.ts
     * const formattedResponse = formatResponseForUI(result);
     * res.json(formattedResponse);
     */
    
    // For demonstration, we'll use a simulated response
    // Simulate processing delay for better UX
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    const mockResult = {
      success: true,
      steps: [
        {
          type: 'extraction',
          title: 'Order Extraction',
          data: {
            items: [
              { 
                name: 'Pizza Margherita', 
                quantity: 1, 
                options: ['Extra cheese'] 
              },
              {
                name: 'Coca Cola',
                quantity: 2,
                options: ['Cold']
              }
            ],
            customerInfo: {
              name: 'Demo Customer',
              address: '123 Demo St',
              phone: '555-1234'
            }
          }
        },
        {
          type: 'validation',
          title: 'Order Validation',
          data: {
            valid: true,
            message: 'Order validated successfully',
            details: {
              estimatedDeliveryTime: '30-45 minutes',
              totalPrice: '$24.99'
            }
          }
        },
        {
          type: 'acceptance',
          title: 'Order Acceptance',
          data: {
            accepted: true,
            orderNumber: 'ORD-' + Math.floor(100000 + Math.random() * 900000),
            timestamp: new Date().toISOString()
          }
        }
      ]
    };
    
    res.json(mockResult);
  } catch (error) {
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