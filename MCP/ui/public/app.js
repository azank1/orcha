// Global state for the application
const appState = {
  currentPayload: null,
  currentResponse: null,
  menuData: null,
  flowSteps: []
};

// MCP request helper function
async function callMcp(method, params = {}, showInFlow = true) {
  // Create payload
  const payload = {
    jsonrpc: "2.0",
    id: Date.now().toString(),
    method,
    params
  };
  
  // Update UI to show payload
  updateJsonPreview('payload', payload);
  appState.currentPayload = payload;
  
  if (showInFlow) {
    addFlowStep('tool-call', `Calling MCP method: ${method}`, {
      method,
      params: JSON.stringify(params, null, 2)
    });
  }
  
  try {
    const response = await fetch('/mcp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    
    const result = await response.json();
    
    // Update UI to show response
    updateJsonPreview('response', result);
    appState.currentResponse = result;
    
    if (showInFlow) {
      if (result.error) {
        addFlowStep('error', `Error: ${result.error.message}`, {
          error: JSON.stringify(result.error, null, 2)
        });
      } else {
        addFlowStep('response', `Success: ${method} completed`, {
          result: JSON.stringify(result.result, null, 2)
        });
      }
    }
    
    return result;
  } catch (error) {
    if (showInFlow) {
      addFlowStep('error', `API Error: ${error.message}`, {
        error: error.stack || error.message
      });
    }
    throw error;
  }
}

// UI helper functions
function updateJsonPreview(tabId, data) {
  const tab = document.getElementById(`${tabId}-tab`);
  if (tab) {
    tab.textContent = JSON.stringify(data, null, 2);
  }
}

function addFlowStep(type, title, content) {
  const flowSteps = document.getElementById('flow-steps');
  const timestamp = new Date().toLocaleTimeString();
  
  // Remove intro message if it exists
  const intro = flowSteps.querySelector('.console-intro');
  if (intro) {
    flowSteps.removeChild(intro);
  }
  
  // Create step element
  const stepElement = document.createElement('div');
  stepElement.className = `flow-step ${type}`;
  
  const headerElement = document.createElement('div');
  headerElement.className = 'step-header';
  headerElement.innerHTML = `<span>${title}</span><span class="step-time">${timestamp}</span>`;
  
  const contentElement = document.createElement('div');
  contentElement.className = 'step-content';
  
  // Handle different content types
  if (typeof content === 'string') {
    contentElement.textContent = content;
  } else if (typeof content === 'object') {
    let contentHtml = '';
    for (const [key, value] of Object.entries(content)) {
      contentHtml += `<strong>${key}:</strong>\n${value}\n\n`;
    }
    contentElement.innerHTML = contentHtml;
  }
  
  stepElement.appendChild(headerElement);
  stepElement.appendChild(contentElement);
  
  // Add to flow steps
  flowSteps.appendChild(stepElement);
  
  // Scroll to bottom
  flowSteps.scrollTop = flowSteps.scrollHeight;
  
  // Store in app state
  appState.flowSteps.push({
    type,
    title,
    content,
    timestamp
  });
}

// Handle tab switching
document.addEventListener('DOMContentLoaded', () => {
  const tabs = document.querySelectorAll('.tab');
  
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      // Remove active class from all tabs
      tabs.forEach(t => t.classList.remove('active'));
      
      // Add active class to clicked tab
      tab.classList.add('active');
      
      // Hide all tab content
      const tabContents = document.querySelectorAll('.tab-content pre');
      tabContents.forEach(content => content.classList.remove('active'));
      
      // Show selected tab content
      const targetId = tab.getAttribute('data-target');
      document.getElementById(targetId).classList.add('active');
    });
  });
  
  // Initialize menu item selection
  setupMenuItemSelection();
});

// Setup menu item click handlers
function setupMenuItemSelection() {
  const menuItems = document.querySelectorAll('.menu-item');
  
  menuItems.forEach(item => {
    item.addEventListener('click', () => {
      const category = item.getAttribute('data-category');
      const itemName = item.querySelector('.item-name').textContent;
      
      // Find the first size and price
      const sizePrice = item.querySelector('.size-price');
      const size = sizePrice ? sizePrice.getAttribute('data-size') : 'Reg';
      const price = sizePrice ? sizePrice.getAttribute('data-price') : '0.00';
      
      // Build the order payload
      const orderPayload = {
        draft: {
          type: "Pickup",
          source: "UI",
          externalRef: `ext-${Date.now()}`,
          customer: {
            name: "Test Customer",
            phone: "410-555-1234"
          },
          items: [
            {
              item: itemName,
              category,
              size,
              quantity: 1,
              externalRef: `ext-${Date.now()}-i1`,
              sellingPrice: parseFloat(price)
            }
          ]
        }
      };
      
      // Update the JSON preview
      updateJsonPreview('payload', orderPayload);
      appState.currentPayload = orderPayload;
      
      // Add to flow
      addFlowStep('user-input', 'Menu Item Selected', {
        category,
        item: itemName,
        size,
        price
      });
    });
  });
}

// Wire up UI buttons
document.getElementById('btn-export').addEventListener('click', async () => {
  try {
    addFlowStep('user-input', 'User Action: Export Menu', {
      action: 'Requesting menu export from FoodTec'
    });
    
    const result = await callMcp("foodtec.export_menu", { orderType: "Pickup" });
    
    if (!result.error) {
      // Store menu data in app state
      appState.menuData = result.result;
    }
  } catch (error) {
    console.error("Export menu failed:", error);
  }
});

document.getElementById('btn-validate').addEventListener('click', async () => {
  try {
    // Use the current payload from the preview
    if (!appState.currentPayload || !appState.currentPayload.draft) {
      addFlowStep('error', 'Validation Error', {
        message: 'No order selected. Please select a menu item first.'
      });
      return;
    }
    
    addFlowStep('user-input', 'User Action: Validate Order', {
      action: 'Sending order to FoodTec for validation',
      order: JSON.stringify(appState.currentPayload.draft, null, 2)
    });
    
    await callMcp("foodtec.validate_order", appState.currentPayload);
  } catch (error) {
    console.error("Validate order failed:", error);
  }
});

document.getElementById('btn-accept').addEventListener('click', async () => {
  try {
    // Use the current payload from the preview
    if (!appState.currentPayload || !appState.currentPayload.draft) {
      addFlowStep('error', 'Acceptance Error', {
        message: 'No order selected. Please select a menu item first.'
      });
      return;
    }
    
    // Add order idempotency key if not present
    if (!appState.currentPayload.idem) {
      appState.currentPayload.idem = `order-${Date.now()}`;
      updateJsonPreview('payload', appState.currentPayload);
    }
    
    addFlowStep('user-input', 'User Action: Accept Order', {
      action: 'Sending order to FoodTec for acceptance',
      order: JSON.stringify(appState.currentPayload, null, 2)
    });
    
    await callMcp("foodtec.accept_order", appState.currentPayload);
  } catch (error) {
    console.error("Accept order failed:", error);
  }
});

// Process natural language orders
document.getElementById('btn-process-order').addEventListener('click', async () => {
  const userInput = document.getElementById('user-input').value.trim();
  
  if (!userInput) {
    addFlowStep('error', 'Input Error', {
      message: 'Please enter an order description.'
    });
    return;
  }
  
  try {
    // Log the user input
    addFlowStep('user-input', 'Natural Language Order', {
      input: userInput
    });
    
    // Call the automation endpoint we created in server.ts
    addFlowStep('tool-call', 'Calling LLM Orchestrator', {
      action: 'Processing natural language with AI',
      input: userInput
    });
    
    // Call the automation API endpoint
    const response = await fetch('/api/automation/process-order', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: userInput })
    });
    
    if (!response.ok) {
      throw new Error(`Server returned ${response.status}: ${response.statusText}`);
    }
    
    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.error || 'Unknown error processing order');
    }
    
    // Process and display each step from the response
    if (result.steps && Array.isArray(result.steps)) {
      // Process each step sequentially with a delay between steps
      for (let i = 0; i < result.steps.length; i++) {
        const step = result.steps[i];
        await new Promise(resolve => setTimeout(resolve, 800)); // Delay between steps
        
        // Display the step in the flow console
        addFlowStep('response', step.title, {
          ...step.data
        });
        
        // If this is an extraction step, update the payload preview
        if (step.type === 'extraction' && step.data.items) {
          // Build draft order from extracted items
          const orderDraft = {
            draft: {
              type: "Pickup", // Default, could be extracted from LLM
              source: "Voice",
              externalRef: `ext-${Date.now()}`,
              customer: step.data.customerInfo || {
                name: "Test Customer",
                phone: "410-555-1234"
              },
              items: step.data.items.map((item, idx) => ({
                item: item.name,
                category: item.category || "Unknown",
                size: item.size || "Reg",
                quantity: item.quantity || 1,
                externalRef: `ext-${Date.now()}-i${idx+1}`,
                sellingPrice: item.price || 0.00,
                options: item.options || []
              }))
            }
          };
          
          // Update the UI with the extracted order
          updateJsonPreview('payload', orderDraft);
          appState.currentPayload = orderDraft;
        }
      }
      
      // Final success message
      addFlowStep('response', 'Order Processing Complete', {
        message: `Successfully processed order: "${userInput}"`
      });
    }
  } catch (error) {
    console.error("Process order failed:", error);
    addFlowStep('error', 'Processing Error', {
      message: error.message
    });
  }
});