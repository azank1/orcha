// Test menuTool functionality
import { menuTool, handleMenu } from '../src/tools/menuTool.js';

console.log('Testing Menu Tool...');
console.log('Tool name:', menuTool.name);
console.log('Tool description:', menuTool.description);
console.log('Required fields:', menuTool.parameters.required);

// Validate tool structure
if (menuTool.name === 'foodtec.export_menu') {
  console.log('✅ Menu tool name correct');
} else {
  console.log('❌ Menu tool name incorrect');
}

if (menuTool.parameters.required.includes('orderType')) {
  console.log('✅ Menu tool requires orderType');
} else {
  console.log('❌ Menu tool missing orderType requirement');
}

// Test the handler
async function testHandler() {
  console.log('\nTesting handler...');
  const testParams = { orderType: 'Delivery' };
  const result = await handleMenu(testParams);
  console.log('Handler result:', result);
  
  if (result.status === 'stub' && result.tool === 'foodtec.export_menu') {
    console.log('✅ Handler working correctly');
  } else {
    console.log('❌ Handler not working as expected');
  }
}

testHandler().catch(console.error);