"""
Simple Flask API for LLM orchestration
Exposes the natural_flow module as a REST endpoint
"""
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import sys
import os
import json
from typing import Generator

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workflows.natural_flow import NaturalFlow

app = Flask(__name__)
CORS(app)

# Initialize the flow with Ollama (no API key needed)
try:
    flow = NaturalFlow(llm_provider="ollama")
    print("✅ Initialized with Ollama")
except Exception as e:
    print(f"⚠️  Failed to initialize with Ollama: {e}")
    print("Trying OpenAI as fallback...")
    try:
        flow = NaturalFlow(llm_provider="openai")
        print("✅ Initialized with OpenAI")
    except:
        flow = None
        print("❌ No LLM available")

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'llm_available': flow is not None
    })

@app.route('/process', methods=['POST'])
def process_order():
    """Process natural language order with streaming"""
    if not flow:
        return jsonify({
            'success': False,
            'error': 'LLM not available'
        }), 503
    
    data = request.get_json()
    user_input = data.get('text', '')
    
    if not user_input:
        return jsonify({
            'success': False,
            'error': 'No text provided'
        }), 400
    
    def generate():
        """Generator for SSE streaming"""
        try:
            import time
            iteration = 0
            
            # Process the order with streaming
            results = flow.process(user_input)
            
            # Don't send initial LLM response if it contains raw JSON tool_calls
            # We'll send the final conversational response at the end
            
            # Send each action as it happens
            for action in results.get('actions', []):
                iteration += 1
                tool_name = action.get('tool', 'unknown')
                
                # Send tool call start
                yield f"data: {json.dumps({'type': 'tool_call', 'content': f'🔧 Calling {tool_name}...', 'timestamp': int(time.time() * 1000)})}\n\n"
                
                # Send result
                if action.get('success'):
                    # Create summary without full data to avoid crashes
                    summary = ''
                    if 'menu' in tool_name.lower():
                        summary = f"✅ Menu fetched successfully"
                    elif 'validate' in tool_name.lower():
                        canonical = action.get('canonical_price', 0)
                        summary = f"✅ Order validated: ${canonical:.2f}" if canonical else "✅ Order validated"
                    elif 'accept' in tool_name.lower():
                        # Extract order number from response
                        order_num = action.get('order_number', 'N/A')
                        summary = f"✅ Order accepted: #{order_num}" if order_num != 'N/A' else "✅ Order accepted"
                    else:
                        summary = f"✅ {tool_name} completed"
                    
                    yield f"data: {json.dumps({'type': 'result', 'content': summary, 'timestamp': int(time.time() * 1000)})}\n\n"
                else:
                    error_msg = action.get('error', 'Unknown error')
                    yield f"data: {json.dumps({'type': 'error', 'content': f'❌ {error_msg}', 'timestamp': int(time.time() * 1000)})}\n\n"
            
            # Send final LLM response (order confirmation message)
            if results.get('llm_response'):
                final_response = results['llm_response']
                # Send the LLM's final conversational response
                yield f"data: {json.dumps({'type': 'thinking', 'content': final_response, 'timestamp': int(time.time() * 1000)})}\n\n"
            
            # Send completion event
            yield f"data: {json.dumps({'type': 'complete', 'timestamp': int(time.time() * 1000)})}\n\n"
            
        except Exception as e:
            import traceback
            error_detail = str(e)[:200]  # Truncate to prevent crashes
            print(f"Error in SSE stream: {traceback.format_exc()}")
            yield f"data: {json.dumps({'type': 'error', 'content': f'Error: {error_detail}', 'timestamp': int(time.time() * 1000)})}\n\n"
            yield f"data: {json.dumps({'type': 'complete', 'timestamp': int(time.time() * 1000)})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    print("\n" + "="*50)
    print("  LLM Orchestration Service")
    print("="*50)
    print("Running on http://127.0.0.1:5000")
    print("Press Ctrl+C to stop")
    print("="*50 + "\n")
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)
