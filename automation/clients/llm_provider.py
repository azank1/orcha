"""
LLM Provider for natural language processing
Supports OpenAI, Anthropic, HuggingFace, and Ollama models
"""
import os
import json
from typing import Dict, Any, Optional, List
from openai import OpenAI
from anthropic import Anthropic
import requests


class LLMProvider:
    """
    LLM Provider that can use OpenAI, Anthropic, HuggingFace, or Ollama
    to interpret user intent and decide which tools to call
    """
    
    def __init__(self, provider: str = "openai", api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the LLM provider
        
        Args:
            provider: "openai", "anthropic", "huggingface", or "ollama"
            api_key: API key (if not provided, reads from environment)
            model: Model name (optional, uses defaults if not provided)
        """
        self.provider = provider.lower()
        
        if self.provider == "openai":
            api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment")
            self.client = OpenAI(api_key=api_key)
            self.model = model or "gpt-4o-mini"
            
        elif self.provider == "anthropic":
            api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment")
            self.client = Anthropic(api_key=api_key)
            self.model = model or "claude-3-5-sonnet-20241022"
            
        elif self.provider == "huggingface":
            api_key = api_key or os.getenv("HUGGINGFACE_API_KEY")
            if not api_key:
                raise ValueError("HUGGINGFACE_API_KEY not found in environment")
            self.api_key = api_key
            # Using HuggingChat API models (free access)
            self.model = model or "mistralai/Mistral-7B-Instruct-v0.2"
            self.api_url = "https://api-inference.huggingface.co/models/"
            
        elif self.provider == "ollama":
            # Ollama runs locally, no API key needed
            self.model = model or "gpt-oss:120b-cloud"
            self.api_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
            
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def chat(self, prompt: str, context: Optional[Dict[str, Any]] = None, 
             tools: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Send a chat request to the LLM
        
        Args:
            prompt: User's natural language input
            context: Optional context (menu data, previous results, etc.)
            tools: Optional tool definitions for function calling
            
        Returns:
            Dict with 'content' and optionally 'tool_calls'
        """
        if self.provider == "openai":
            return self._chat_openai(prompt, context, tools)
        elif self.provider == "anthropic":
            return self._chat_anthropic(prompt, context, tools)
        elif self.provider == "huggingface":
            return self._chat_huggingface(prompt, context, tools)
        else:
            return self._chat_ollama(prompt, context, tools)
    
    def _chat_openai(self, prompt: str, context: Optional[Dict], 
                     tools: Optional[List[Dict]]) -> Dict[str, Any]:
        """OpenAI chat implementation"""
        messages = [
            {
                "role": "system",
                "content": self._get_system_prompt()
            }
        ]
        
        # Add context if provided
        if context:
            messages.append({
                "role": "system",
                "content": f"Available context:\n{json.dumps(context, indent=2)}"
            })
        
        # Add user message
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        # Make request
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2
        }
        
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        
        response = self.client.chat.completions.create(**kwargs)
        
        # Parse response
        message = response.choices[0].message
        result = {
            "content": message.content or "",
            "tool_calls": []
        }
        
        if hasattr(message, 'tool_calls') and message.tool_calls:
            for tool_call in message.tool_calls:
                result["tool_calls"].append({
                    "id": tool_call.id,
                    "name": tool_call.function.name,
                    "arguments": json.loads(tool_call.function.arguments)
                })
        
        return result
    
    def _chat_anthropic(self, prompt: str, context: Optional[Dict],
                       tools: Optional[List[Dict]]) -> Dict[str, Any]:
        """Anthropic chat implementation"""
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        # Build system prompt
        system_content = self._get_system_prompt()
        if context:
            system_content += f"\n\nAvailable context:\n{json.dumps(context, indent=2)}"
        
        # Make request
        kwargs = {
            "model": self.model,
            "max_tokens": 4096,
            "system": system_content,
            "messages": messages,
            "temperature": 0.2
        }
        
        if tools:
            kwargs["tools"] = self._convert_tools_to_anthropic(tools)
        
        response = self.client.messages.create(**kwargs)
        
        # Parse response
        result = {
            "content": "",
            "tool_calls": []
        }
        
        for block in response.content:
            if block.type == "text":
                result["content"] += block.text
            elif block.type == "tool_use":
                result["tool_calls"].append({
                    "id": block.id,
                    "name": block.name,
                    "arguments": block.input
                })
        
        return result
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the LLM"""
        return """You are OrchaPOS, an intelligent restaurant ordering assistant.

Your role is to help users interact with the FoodTec POS system through natural language.

You have access to these tools:
- foodtec.export_menu: Get the restaurant menu (optionally filtered by category)
- foodtec.validate_order: Validate an order before acceptance
- foodtec.accept_order: Finalize and submit an order

When a user asks about menu items, use export_menu.
When a user wants to order something, follow this flow:
1. Export menu (if not already cached)
2. Find matching items
3. Validate the order
4. Accept the order with the canonical price

Always be helpful and confirm order details before finalizing."""
    
    def _chat_huggingface(self, prompt: str, context: Optional[Dict],
                          tools: Optional[List[Dict]]) -> Dict[str, Any]:
        """HuggingFace Inference API implementation"""
        # Build system prompt with tool descriptions
        system_content = self._get_system_prompt()
        if context:
            system_content += f"\n\nAvailable context:\n{json.dumps(context, indent=2)}"
        
        if tools:
            tool_descriptions = "\n\nAvailable tools:\n"
            for tool in tools:
                func = tool["function"]
                tool_descriptions += f"- {func['name']}: {func['description']}\n"
            system_content += tool_descriptions
            system_content += "\nTo use a tool, respond with JSON: {\"tool\": \"tool_name\", \"arguments\": {...}}"
        
        # Build messages
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": prompt}
        ]
        
        # Make request to HuggingFace
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": self._format_messages_for_hf(messages),
            "parameters": {
                "max_new_tokens": 1000,
                "temperature": 0.2,
                "return_full_text": False
            }
        }
        
        try:
            response = requests.post(
                f"{self.api_url}{self.model}",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result_data = response.json()
            
            # Extract generated text
            if isinstance(result_data, list) and len(result_data) > 0:
                generated_text = result_data[0].get("generated_text", "")
            else:
                generated_text = str(result_data)
            
            # Parse response for tool calls
            result = {
                "content": generated_text,
                "tool_calls": []
            }
            
            # Try to extract tool calls from JSON in response
            if tools and "{" in generated_text and "}" in generated_text:
                try:
                    # Find JSON in response
                    start = generated_text.find("{")
                    end = generated_text.rfind("}") + 1
                    json_str = generated_text[start:end]
                    tool_call = json.loads(json_str)
                    
                    if "tool" in tool_call and "arguments" in tool_call:
                        result["tool_calls"].append({
                            "id": "hf-tool-1",
                            "name": tool_call["tool"],
                            "arguments": tool_call["arguments"]
                        })
                        # Remove JSON from content
                        result["content"] = generated_text[:start].strip()
                except json.JSONDecodeError:
                    pass
            
            return result
            
        except Exception as e:
            print(f"HuggingFace API error: {e}")
            return {
                "content": f"Error calling HuggingFace API: {str(e)}",
                "tool_calls": []
            }
    
    def _format_messages_for_hf(self, messages: List[Dict]) -> str:
        """Format messages for HuggingFace chat format"""
        formatted = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                formatted += f"<|system|>\n{content}\n"
            elif role == "user":
                formatted += f"<|user|>\n{content}\n"
            elif role == "assistant":
                formatted += f"<|assistant|>\n{content}\n"
        formatted += "<|assistant|>\n"
        return formatted
    
    def _convert_tools_to_anthropic(self, openai_tools: List[Dict]) -> List[Dict]:
        """Convert OpenAI tool format to Anthropic format"""
        anthropic_tools = []
        for tool in openai_tools:
            if tool.get("type") == "function":
                func = tool["function"]
                anthropic_tools.append({
                    "name": func["name"],
                    "description": func["description"],
                    "input_schema": func["parameters"]
                })
        return anthropic_tools
    
    def _chat_ollama(self, prompt: str, context: Optional[Dict], 
                     tools: Optional[List[Dict]]) -> Dict[str, Any]:
        """Ollama chat implementation (local models)"""
        # Build the system message
        system_msg = """You are a helpful restaurant ordering assistant for OrchaPOS.

WORKFLOW for placing orders:
1. If user wants to ORDER something:
   Step 1: Call foodtec.export_menu to get the menu (if not already available in context)
   Step 2: Find the matching item in the menu and NOTE ITS PRICE
   Step 3: Call foodtec.validate_order with:
           - category (from menu)
           - item (exact name from menu)
           - size (from menu)
           - menuPrice (the price field from the menu item - REQUIRED!)
   Step 4: After validation succeeds, call foodtec.accept_order with:
           - category (from validation)
           - item (from validation)
           - size (from validation)
           - menuPrice (from validation)
           - canonicalPrice (from validation result)
           - customer: {name, phone}
           - externalRef (generate unique ID like "ORD-12345")
   
2. If user just browsing/asking questions (e.g., "What appetizers?", "How much is X?"):
   - Check context: If "menu" key exists with data → ANSWER IMMEDIATELY, no tools needed!
   - If NO "menu" in context → Call foodtec.export_menu ONCE only
   - After export_menu completes → ANSWER conversationally, do NOT call more tools!
   - NEVER call export_menu more than once for the same question!

CRITICAL RULES:
- If prompt contains "Now that you have the data" or "answer the user's question" → You MUST respond conversationally WITHOUT calling any tools!
- If "completed_actions" shows a tool was already called successfully → DO NOT call it again!
- NEVER call accept_order more than once - if it succeeded, just confirm to the user
- NEVER call validate_order without the menuPrice from the menu
- When validation succeeds, call accept_order ONCE, then stop
- Phone format must be XXX-XXX-XXXX
- If customer info is missing, ask for it

RESPONSE FORMATS:
- To call a tool: Use native Ollama tool calling (return tool_calls)
- To answer without tools: Respond conversationally with content field
- If prompt asks you to answer: DO NOT return tool_calls, just answer with text"""

        if context:
            system_msg += f"\n\nContext: {json.dumps(context)}"
        
        # Build the user message
        user_msg = prompt
        
        # Make request to Ollama API
        try:
            # Build request payload
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ],
                "stream": False
            }
            
            # Add tools if provided (Ollama supports native tool calling)
            if tools:
                payload["tools"] = tools
            
            response = requests.post(
                f"{self.api_url}/api/chat",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            print(f"🔍 Ollama raw response: {json.dumps(result, indent=2)[:500]}")
            message = result.get("message", {})
            content = message.get("content", "")
            
            # Check for native Ollama tool_calls first
            tool_calls = message.get("tool_calls", [])
            
            # If no native tool_calls, try to extract from text content
            if not tool_calls and content:
                try:
                    # Look for JSON in the response text
                    if "{" in content and "tool_calls" in content:
                        # Extract JSON from markdown code blocks if present
                        json_str = content
                        if "```json" in content:
                            json_str = content.split("```json")[1].split("```")[0].strip()
                        elif "```" in content:
                            json_str = content.split("```")[1].split("```")[0].strip()
                        
                        parsed = json.loads(json_str)
                        if "tool_calls" in parsed:
                            tool_calls = parsed["tool_calls"]
                            # Clear content since it was just the JSON
                            content = ""
                except json.JSONDecodeError:
                    pass
            
            # Convert Ollama's tool_calls format to our format if needed
            if tool_calls and isinstance(tool_calls, list):
                formatted_calls = []
                for call in tool_calls:
                    if isinstance(call, dict):
                        # Ollama format: {"function": {"name": "...", "arguments": {...}}}
                        if "function" in call:
                            formatted_calls.append({
                                "name": call["function"].get("name"),
                                "arguments": call["function"].get("arguments", {})
                            })
                        # Our format: {"name": "...", "arguments": {...}}
                        elif "name" in call:
                            formatted_calls.append(call)
                tool_calls = formatted_calls
            
            return {
                "content": content,
                "tool_calls": tool_calls
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Ollama API error: {str(e)}"
            print(error_msg)
            return {
                "content": f"Error calling Ollama API: {str(e)}",
                "tool_calls": []
            }


def get_foodtec_tools() -> List[Dict]:
    """
    Get tool definitions for FoodTec operations
    These match the MCP server's tool signatures
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "foodtec.export_menu",
                "description": "Export the restaurant menu. Returns categories with items, sizes, and prices.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "orderType": {
                            "type": "string",
                            "enum": ["Pickup", "Delivery", "Dine In"],
                            "description": "Type of order"
                        },
                        "category": {
                            "type": "string",
                            "description": "Optional: Filter by category name (e.g., 'Appetizer', 'Pizza')"
                        }
                    },
                    "required": ["orderType"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "foodtec.validate_order",
                "description": "Validate an order and get the canonical price (with tax). Must be called before accepting an order. Returns menuPrice and canonicalPrice.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "Item category from menu"
                        },
                        "item": {
                            "type": "string",
                            "description": "Exact item name from menu"
                        },
                        "size": {
                            "type": "string",
                            "description": "Size from menu (e.g., 'Sm', 'Reg', 'Lg')"
                        },
                        "menuPrice": {
                            "type": "number",
                            "description": "Base price from menu (optional - will be looked up if not provided)"
                        }
                    },
                    "required": ["category", "item", "size"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "foodtec.accept_order",
                "description": "Accept and finalize an order. MUST call validate_order first to get menuPrice and canonicalPrice.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "Item category from menu"
                        },
                        "item": {
                            "type": "string",
                            "description": "Exact item name from menu"
                        },
                        "size": {
                            "type": "string",
                            "description": "Item size from menu"
                        },
                        "menuPrice": {
                            "type": "number",
                            "description": "Original menu price WITHOUT tax (get from validation response)"
                        },
                        "canonicalPrice": {
                            "type": "number",
                            "description": "Final price WITH tax (get from validation response)"
                        },
                        "customer": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Customer full name"
                                },
                                "phone": {
                                    "type": "string",
                                    "description": "Phone in format XXX-XXX-XXXX"
                                }
                            },
                            "required": ["name", "phone"]
                        },
                        "externalRef": {
                            "type": "string",
                            "description": "Unique order reference ID (generate a random string like 'ORD-12345')"
                        }
                    },
                    "required": ["category", "item", "size", "menuPrice", "canonicalPrice", "customer", "externalRef"]
                }
            }
        }
    ]
