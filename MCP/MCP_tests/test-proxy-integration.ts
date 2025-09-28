// Test MCP proxy integration
import { handleRpc } from '../src/rpc/dispatcher.js';

async function testProxyIntegration() {
  console.log('Testing MCP Proxy Integration...\n');
  
  // Test 1: Check all tools are now available
  console.log('1. Testing expanded tool list...');
  const listToolsRequest = {
    jsonrpc: "2.0",
    id: "test-1",
    method: "list_tools"
  };
  
  const listResult = await handleRpc(listToolsRequest);
  console.log('Available tools:', listResult.tools?.map(t => t.name));
  
  if (listResult.tools && listResult.tools.length === 3) {
    console.log('✅ All 3 tools available');
  } else {
    console.log('❌ Wrong number of tools');
  }
  
  // Test 2: Test menu tool (should work if proxy is running)
  console.log('\n2. Testing menu tool with proxy...');
  const menuRequest = {
    jsonrpc: "2.0",
    id: "test-2",
    method: "foodtec.export_menu",
    params: { orderType: "Delivery" }
  };
  
  try {
    const menuResult = await handleRpc(menuRequest);
    console.log('Menu result:', JSON.stringify(menuResult.result, null, 2).substring(0, 200) + '...');
    
    if (menuResult.result && menuResult.result.status === 200 && menuResult.result.success) {
      console.log('✅ Menu tool now calling real proxy - got real FoodTec data!');
      console.log(`   Found ${menuResult.result.data?.length || 0} menu categories`);
    } else if (menuResult.result && menuResult.result.status === 'stub') {
      console.log('⚠️  Still getting stub - proxy might not be running');
    } else if (menuResult.error) {
      console.log('❌ Menu tool error:', menuResult.error);
    } else {
      console.log('🤔 Unexpected result format:', menuResult);
    }
  } catch (error: any) {
    console.log('⚠️  Proxy call failed (proxy server not running?):', error.message);
  }
  
  console.log('\n3. Tool definitions check...');
  const tools = listResult.tools || [];
  tools.forEach(tool => {
    console.log(`- ${tool.name}: ${tool.description}`);
    console.log(`  Required params: ${tool.parameters.required.join(', ')}`);
  });
}

testProxyIntegration().catch(console.error);