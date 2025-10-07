/**
 * Agent Orchestrator - Handles LLM-driven order processing
 * Uses Ollama to interpret natural language and orchestrate MCP tool calls
 */

import axios from 'axios';

interface LLMResponse {
  content: string;
  tool_calls?: Array<{
    id: string;
    name: string;
    arguments: any;
  }>;
}

interface ThinkingStep {
  type: 'thinking' | 'tool_call' | 'result' | 'error';
  content: string;
  data?: any;
  timestamp: number;
}

export class AgentOrchestrator {
  private mcpUrl: string;
  private ollamaUrl: string;
  private model: string;
  private menuCache: any = null;
  private lastValidation: any = null;

  constructor(mcpUrl = 'http://127.0.0.1:9090/rpc', ollamaUrl = 'http://127.0.0.1:11434', model = 'llama3.2') {
    this.mcpUrl = mcpUrl;
    this.ollamaUrl = ollamaUrl;
    this.model = model;
  }

  /**
   * Process a natural language order request
   * Yields thinking steps in real-time
   */
  async* processOrder(userInput: string): AsyncGenerator<ThinkingStep> {
    try {
      yield {
        type: 'thinking',
        content: `Processing: "${userInput}"`,
        timestamp: Date.now()
      };

      // Step 1: Get menu if not cached
      if (!this.menuCache) {
        yield {
          type: 'thinking',
          content: 'Fetching menu from FoodTec...',
          timestamp: Date.now()
        };

        const menuResult = await this.callMCPTool('foodtec.export_menu', {
          orderType: 'Pickup'
        });

        if (menuResult.success) {
          this.menuCache = menuResult.data.data;
          yield {
            type: 'tool_call',
            content: 'Menu exported successfully',
            data: { categories: menuResult.data.data.length },
            timestamp: Date.now()
          };
        } else {
          yield {
            type: 'error',
            content: 'Failed to export menu',
            data: menuResult.error,
            timestamp: Date.now()
          };
          return;
        }
      }

      // Step 2: Ask LLM to interpret the order
      yield {
        type: 'thinking',
        content: 'Analyzing your request with LLM...',
        timestamp: Date.now()
      };

      const llmResponse = await this.askOllama(userInput);
      
      yield {
        type: 'thinking',
        content: `LLM: ${llmResponse.content}`,
        timestamp: Date.now()
      };

      // Step 3: Extract order details from LLM response
      const orderDetails = await this.extractOrderDetails(userInput, llmResponse.content);
      
      if (!orderDetails) {
        yield {
          type: 'error',
          content: 'Could not understand the order. Please be more specific.',
          timestamp: Date.now()
        };
        return;
      }

      yield {
        type: 'result',
        content: `Identified: ${orderDetails.item} (${orderDetails.size}) from ${orderDetails.category}`,
        data: orderDetails,
        timestamp: Date.now()
      };

      // Step 4: Validate order
      yield {
        type: 'thinking',
        content: 'Validating order with FoodTec...',
        timestamp: Date.now()
      };

      const validationResult = await this.callMCPTool('foodtec.validate_order', {
        category: orderDetails.category,
        item: orderDetails.item,
        size: orderDetails.size,
        price: orderDetails.price,
        customer: orderDetails.customer
      });

      if (!validationResult.success) {
        yield {
          type: 'error',
          content: 'Validation failed',
          data: validationResult.error,
          timestamp: Date.now()
        };
        return;
      }

      const canonicalPrice = validationResult.data.canonical_price;
      
      yield {
        type: 'tool_call',
        content: `Validation successful - Total: $${canonicalPrice}`,
        data: { menuPrice: orderDetails.price, canonicalPrice },
        timestamp: Date.now()
      };

      // Step 5: Accept order
      yield {
        type: 'thinking',
        content: 'Submitting order to FoodTec...',
        timestamp: Date.now()
      };

      const acceptResult = await this.callMCPTool('foodtec.accept_order', {
        category: orderDetails.category,
        item: orderDetails.item,
        size: orderDetails.size,
        customer: orderDetails.customer,
        menuPrice: orderDetails.price,
        canonicalPrice: canonicalPrice,
        externalRef: `ai-${Date.now()}`,
        idem: `idem-${Date.now()}`
      });

      if (acceptResult.success) {
        yield {
          type: 'result',
          content: `✅ Order accepted! Order ID: ${acceptResult.data.data?.orderNum || 'Unknown'}`,
          data: acceptResult.data,
          timestamp: Date.now()
        };
      } else {
        yield {
          type: 'error',
          content: 'Order acceptance failed',
          data: acceptResult.error,
          timestamp: Date.now()
        };
      }

    } catch (error: any) {
      yield {
        type: 'error',
        content: `Error: ${error.message}`,
        timestamp: Date.now()
      };
    }
  }

  /**
   * Call Ollama LLM
   */
  private async askOllama(prompt: string): Promise<LLMResponse> {
    const systemPrompt = `You are an intelligent restaurant ordering assistant. 
You help parse customer orders for a food ordering system.

When given an order, extract:
- Item name (match to menu items)
- Size (Sm, Md, Lg, Reg, etc.)
- Quantity (default 1)
- Category (Appetizer, Pizza, Salad, etc.)

Available menu categories: ${this.menuCache?.map((c: any) => c.category).join(', ') || 'Loading...'}

Respond conversationally and confirm what you understood.`;

    try {
      const response = await axios.post(`${this.ollamaUrl}/api/chat`, {
        model: this.model,
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: prompt }
        ],
        stream: false
      }, {
        timeout: 30000
      });

      return {
        content: response.data.message?.content || 'No response',
        tool_calls: []
      };
    } catch (error: any) {
      console.error('Ollama error:', error.message);
      throw new Error(`Ollama not available. Make sure Ollama is running on ${this.ollamaUrl}`);
    }
  }

  /**
   * Extract structured order details from LLM conversation
   */
  private async extractOrderDetails(userInput: string, llmResponse: string): Promise<any> {
    // Simple parsing - match against menu items
    if (!this.menuCache) return null;

    // Default customer for now
    const customer = {
      name: 'AI Customer',
      phone: '410-555-1234'
    };

    // Try to find matching items
    for (const category of this.menuCache) {
      for (const item of category.items) {
        const itemNameLower = item.item.toLowerCase();
        const userInputLower = userInput.toLowerCase();
        
        // Simple matching: if user mentions item name
        if (userInputLower.includes(itemNameLower.split(' ')[0].toLowerCase())) {
          // Find size - default to first available
          const sizes = item.sizePrices || item.sizes || [];
          let selectedSize = sizes[0];
          
          // Try to match size from input
          if (userInputLower.includes('large') || userInputLower.includes('lg')) {
            selectedSize = sizes.find((s: any) => s.size === 'Lg') || selectedSize;
          } else if (userInputLower.includes('small') || userInputLower.includes('sm')) {
            selectedSize = sizes.find((s: any) => s.size === 'Sm') || selectedSize;
          } else if (userInputLower.includes('medium') || userInputLower.includes('md')) {
            selectedSize = sizes.find((s: any) => s.size === 'Md' || s.size === 'Reg') || selectedSize;
          }

          return {
            category: category.category,
            item: item.item,
            size: selectedSize.size,
            price: selectedSize.price,
            customer
          };
        }
      }
    }

    return null;
  }

  /**
   * Call MCP tool via JSON-RPC
   */
  private async callMCPTool(method: string, params: any): Promise<any> {
    try {
      const response = await axios.post(this.mcpUrl, {
        jsonrpc: '2.0',
        id: Date.now().toString(),
        method,
        params
      }, {
        timeout: 15000
      });

      if (response.data.error) {
        return {
          success: false,
          error: response.data.error
        };
      }

      return {
        success: true,
        data: response.data.result
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.message
      };
    }
  }
}
