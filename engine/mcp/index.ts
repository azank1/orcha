/**
 * MCP Server with Schema Validation and Discovery
 * 
 * Provides JSON-RPC 2.0 interface with strict schema validation
 */

import express, { Request, Response } from 'express'
import { readFileSync } from 'fs'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'
import { validateToolRequest, ValidationError } from './validation.js'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

const app = express()
app.use(express.json({ limit: '1mb' }))

const PORT = Number(process.env.MCP_PORT ?? 9090)
const PROXY_BASE = process.env.PROXY_BASE ?? "http://127.0.0.1:8080/apiclient"

// JSON-RPC helpers
type JsonRpcRequest = { 
  jsonrpc: "2.0"
  id?: string | number | null
  method: string
  params?: any 
}

type JsonRpcResponse = {
  jsonrpc: "2.0"
  id: string | number | null
  result?: any
  error?: {
    code: number
    message: string
    data?: any
  }
}

const rpcSuccess = (id: any, result: any): JsonRpcResponse => ({ 
  jsonrpc: "2.0", 
  id, 
  result 
})

const rpcError = (id: any, code: number, message: string, data?: any): JsonRpcResponse => ({
  jsonrpc: "2.0", 
  id, 
  error: { code, message, data }
})

/**
 * Load compiled JSON schema for tool discovery
 */
function loadCompiledSchema(schemaFile: string): any {
  try {
    const schemaPath = join(__dirname, '..', 'schemas', 'json', schemaFile)
    const schemaContent = readFileSync(schemaPath, 'utf8')
    return JSON.parse(schemaContent)
  } catch (error) {
    console.error(`Failed to load schema ${schemaFile}:`, error)
    return null
  }
}

/**
 * Tool definitions for discovery
 */
const tools = [
  {
    name: "menu.export",
    description: "Export menu data with pagination and search capabilities",
    input_schema: loadCompiledSchema('menu.export.req.json'),
    output_schema: loadCompiledSchema('menu.export.res.json')
  },
  {
    name: "order.validate", 
    description: "Validate order draft and return pricing information",
    input_schema: loadCompiledSchema('order.validate.req.json'),
    output_schema: loadCompiledSchema('order.validate.res.json')
  },
  {
    name: "order.accept",
    description: "Accept validated order with idempotency support",
    input_schema: loadCompiledSchema('order.accept.req.json'),
    output_schema: loadCompiledSchema('order.accept.res.json')
  }
]

/**
 * Tool discovery endpoint
 */
app.get('/.well-known/mcp/tools', (_req: Request, res: Response) => {
  res.json({ tools })
})

/**
 * Health check endpoint
 */
app.get('/healthz', (_req: Request, res: Response) => {
  res.json({ 
    ok: true, 
    ts: Date.now(),
    service: "mcp-server",
    version: "1.0.0"
  })
})

/**
 * Mock tool implementations (replace with actual business logic)
 */
async function executeMenuExport(params: any): Promise<any> {
  // Mock menu data - replace with actual proxy call
  return {
    menu: {
      categories: [
        { id: "pizzas", name: "Pizzas" },
        { id: "drinks", name: "Beverages" }
      ],
      items: [
        {
          sku: "LARGE_PEP",
          name: "Large Pepperoni Pizza",
          desc: "Classic pepperoni with mozzarella cheese",
          price: { currency: "USD", amount: 1499 },
          available: true,
          tags: ["popular"],
          category: "pizzas"
        }
      ]
    },
    page: params.page || 1,
    page_size: params.page_size || 50,
    total: 1
  }
}

async function executeOrderValidate(params: any): Promise<any> {
  // Mock validation - replace with actual business logic
  return {
    ok: true,
    draft: {
      items: params.items,
      subtotal: { currency: "USD", amount: 1499 },
      taxes: [{ currency: "USD", amount: 150 }],
      fees: [],
      total: { currency: "USD", amount: 1649 }
    }
  }
}

async function executeOrderAccept(params: any): Promise<any> {
  // Mock acceptance - replace with actual business logic
  return {
    ok: true,
    order_id: `ORD-${Date.now()}`,
    eta: new Date(Date.now() + 30 * 60 * 1000).toISOString(),
    idem: params.idem || `auto-${Date.now()}`
  }
}

/**
 * JSON-RPC endpoint with validation
 */
app.post('/rpc', async (req: Request, res: Response) => {
  const requests = Array.isArray(req.body) ? req.body : [req.body]
  
  const handleRequest = async (request: JsonRpcRequest): Promise<JsonRpcResponse> => {
    // Validate JSON-RPC structure
    if (!request || request.jsonrpc !== "2.0" || !request.method) {
      return rpcError(request?.id || null, -32600, "Invalid Request")
    }

    try {
      // Validate request parameters against schema
      validateToolRequest(request.method, request.params || {})

      // Execute tool method
      let result: any
      switch (request.method) {
        case "menu.export":
          result = await executeMenuExport(request.params)
          break
          
        case "order.validate":
          result = await executeOrderValidate(request.params)
          break
          
        case "order.accept":
          result = await executeOrderAccept(request.params)
          break
          
        default:
          return rpcError(request.id, -32601, `Method not found: ${request.method}`)
      }

      return rpcSuccess(request.id, result)
      
    } catch (error: any) {
      console.error(`Error in ${request.method}:`, error)
      
      if (error instanceof ValidationError) {
        return rpcError(request.id, error.jsonRpcError.code, error.jsonRpcError.message, error.jsonRpcError.data)
      }
      
      return rpcError(request.id, -32603, error.message || "Internal error")
    }
  }

  const responses = await Promise.all(requests.map(handleRequest))
  
  if (Array.isArray(req.body)) {
    res.json(responses)
  } else {
    res.json(responses[0])
  }
})

// Start server
app.listen(PORT, () => {
  console.log(`🚀 MCP Server running on port ${PORT}`)
  console.log(`📋 Tool discovery: http://localhost:${PORT}/.well-known/mcp/tools`)
  console.log(`❤️  Health check: http://localhost:${PORT}/healthz`)
  console.log(`🔌 JSON-RPC endpoint: http://localhost:${PORT}/rpc`)
  console.log(`🔗 Proxy backend: ${PROXY_BASE}`)
})

export default app