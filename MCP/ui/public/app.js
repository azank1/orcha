// MCP request helper function
async function callMcp(method, params = {}) {
  // Update UI to show loading state
  const output = document.getElementById('output');
  output.innerText = `Processing ${method}...`;
  output.classList.add('loading');
  
  try {
    const response = await fetch('/mcp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        jsonrpc: "2.0",
        id: Date.now(),
        method,
        params
      })
    });
    const result = await response.json();
    output.classList.remove('loading');
    return result;
  } catch (error) {
    output.classList.remove('loading');
    output.classList.add('error');
    output.innerText = `Error: ${error.message}`;
    throw error;
  }
}

// Wire up buttons to MCP calls
document.getElementById('btn-export').addEventListener('click', async () => {
  const result = await callMcp("foodtec.export_menu", { orderType: "Pickup" });
  const output = document.getElementById('output');
  
  // Reset styling
  output.classList.remove('error', 'success');
  
  if (result.error) {
    output.classList.add('error');
    output.innerText = `ERROR: ${result.error.message}\n\n${JSON.stringify(result, null, 2)}`;
  } else {
    output.classList.add('success');
    output.innerText = `SUCCESS: Menu exported\n\n${JSON.stringify(result, null, 2)}`;
  }
});

document.getElementById('btn-validate').addEventListener('click', async () => {
  // Updated structure based on the P2A/proxy/handlers.py requirements
  const params = {
    category: "Appetizer",
    item: "3pcs Chicken Strips w/ FF", 
    size: "Lg",
    price: 6.99,
    customer: {
      name: "Test Customer",
      phone: "410-555-1234"
    }
  };
  
  const result = await callMcp("foodtec.validate_order", params);
  const output = document.getElementById('output');
  
  // Reset styling
  output.classList.remove('error', 'success');
  
  if (result.error) {
    output.classList.add('error');
    output.innerText = `ERROR: ${result.error.message}\n\n${JSON.stringify(result, null, 2)}`;
  } else {
    output.classList.add('success');
    output.innerText = `SUCCESS: Order validated\n\n${JSON.stringify(result, null, 2)}`;
  }
});

document.getElementById('btn-accept').addEventListener('click', async () => {
  // Updated structure based on the P2A/proxy/handlers.py requirements
  const params = {
    category: "Appetizer",
    item: "3pcs Chicken Strips w/ FF", 
    size: "Lg",
    price: 6.99,  // Use original menu price, not canonical price
    customer: {
      name: "Test Customer",
      phone: "410-555-1234"
    }
  };
  
  const result = await callMcp("foodtec.accept_order", params);
  const output = document.getElementById('output');
  
  // Reset styling
  output.classList.remove('error', 'success');
  
  if (result.error) {
    output.classList.add('error');
    output.innerText = `ERROR: ${result.error.message}\n\n${JSON.stringify(result, null, 2)}`;
  } else {
    output.classList.add('success');
    output.innerText = `SUCCESS: Order accepted\n\n${JSON.stringify(result, null, 2)}`;
  }
});