// Test MCP server tool exposure functionality
import { handleRpc } from '../src/rpc/dispatcher.js';

async function testMcpToolExposure() {
  console.log('Testing MCP Tool Exposure...\n');
  
  // Test 1: list_tools
  console.log('1. Testing list_tools...');
  const listToolsRequest = {
    jsonrpc: "2.0",
    id: "test-1",
    method: "list_tools"
  };
  
  const listResult = await handleRpc(listToolsRequest);
  console.log('List tools result:', JSON.stringify(listResult, null, 2));
  
  if (listResult.tools && listResult.tools.length > 0) {
    console.log('✅ list_tools working correctly');
  } else {
    console.log('❌ list_tools not working');
  }
  
  // Test 2: Tool call
  console.log('\n2. Testing tool call...');
  const toolCallRequest = {
    jsonrpc: "2.0",
    id: "test-2", 
    method: "foodtec.export_menu",
    params: { orderType: "Pickup" }
  };
  
  const callResult = await handleRpc(toolCallRequest);
  console.log('Tool call result:', JSON.stringify(callResult, null, 2));
  
  if (callResult.result && callResult.result.status === 'stub') {
    console.log('✅ Tool call working correctly');
  } else {
    console.log('❌ Tool call not working');
  }
  
  // Test 3: Unknown tool
  console.log('\n3. Testing unknown tool...');
  const unknownRequest = {
    jsonrpc: "2.0",
    id: "test-3",
    method: "unknown.tool",
    params: {}
  };
  
  const unknownResult = await handleRpc(unknownRequest);
  console.log('Unknown tool result:', JSON.stringify(unknownResult, null, 2));
  
  if (unknownResult.error && unknownResult.error.includes('Unknown tool')) {
    console.log('✅ Error handling working correctly');
  } else {
    console.log('❌ Error handling not working');
  }
}

testMcpToolExposure().catch(console.error);