import axios from 'axios';

async function testMcpCall() {
  try {
    // Test export_menu method
    const response = await axios.post('http://127.0.0.1:9090/rpc', {
      jsonrpc: '2.0',
      id: 'test-1',
      method: 'foodtec.export_menu',
      params: {
        orderType: 'Delivery'
      }
    }, {
      headers: {
        'Content-Type': 'application/json',
        'X-Request-ID': 'test-req-001'
      }
    });
    
    console.log('MCP Response:');
    
    // Check if we have a successful result with menu data
    if (response.data.result && response.data.result.menu) {
      const menu = response.data.result.menu;
      const categories = menu.map((cat: any) => cat.category);
      const totalItems = menu.reduce((sum: number, cat: any) => sum + cat.items.length, 0);
      
      console.log(`Successfully received menu with ${categories.length} categories and ${totalItems} total items`);
      console.log('Categories:', categories.join(', '));
      console.log('First few items:', menu[0].items.slice(0, 3).map((item: any) => item.item).join(', '));
    } else {
      // If there was an error or different response structure
      console.log(JSON.stringify(response.data, null, 2));
    }
    
    console.log('Response Status:', response.status);
    console.log('Content Length:', response.headers['content-length']);
    
  } catch (error: any) {
    console.error('Error calling MCP:');
    if (error.response) {
      // The request was made and the server responded with a status code
      console.error('Status:', error.response.status);
      console.error('Data:', error.response.data);
      console.error('Headers:', error.response.headers);
    } else if (error.request) {
      // The request was made but no response was received
      console.error('No response received:', error.request);
    } else {
      // Something happened in setting up the request
      console.error('Error message:', error.message);
    }
  }
}

// Run the test
testMcpCall().catch(console.error);