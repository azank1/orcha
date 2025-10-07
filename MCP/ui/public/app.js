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
  
  // Update UI to show payload (but don't override currentPayload with RPC wrapper)
  updateJsonPreview('payload', params);
  // Don't override appState.currentPayload here - it contains the order data
  
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
    // Get all size-price options for this item
    const sizePrices = item.querySelectorAll('.size-price');
    
    // If no sizes found, log warning
    if (sizePrices.length === 0) {
      console.warn('No size-price elements found for item:', item.querySelector('.item-name').textContent);
      return;
    }
    
    // Add click handler to each size option
    sizePrices.forEach(sizePrice => {
      sizePrice.addEventListener('click', (e) => {
        e.stopPropagation(); // Prevent bubbling to parent
        
        const category = item.getAttribute('data-category');
        const itemName = item.querySelector('.item-name').textContent;
        const size = sizePrice.getAttribute('data-size');
        const priceStr = sizePrice.getAttribute('data-price');
        const price = parseFloat(priceStr) || 0;
        
        // Debug logging
        console.log('Size clicked:', {
          category,
          item: itemName,
          size,
          priceStr,
          price
        });
        
        if (price === 0) {
          addFlowStep('error', 'Price Error', {
            message: `Price is $0.00 for ${itemName} (${size}). Check menu data.`
          });
          return;
        }
        
        // Build the order payload using flat format expected by MCP tools
        const orderPayload = {
          category: category,
          item: itemName,
          size: size,
          price: price,
          customer: {
            name: "Test Customer",
            phone: "410-555-1234"
          }
        };
        
        // Update the JSON preview
        updateJsonPreview('payload', orderPayload);
        appState.currentPayload = orderPayload;
        
        // Add to flow
        addFlowStep('user-input', 'Menu Item Selected', {
          category: category,
          item: itemName,
          size: size,
          price: `$${price}`
        });
        
        // Visual feedback - highlight selected
        item.querySelectorAll('.size-price').forEach(sp => sp.classList.remove('selected'));
        sizePrice.classList.add('selected');
      });
      
      // Make size buttons look clickable
      sizePrice.style.cursor = 'pointer';
      sizePrice.style.padding = '4px 8px';
      sizePrice.style.margin = '0 4px';
      sizePrice.style.borderRadius = '4px';
      sizePrice.style.background = '#f0f0f0';
      sizePrice.style.display = 'inline-block';
      sizePrice.style.transition = 'background 0.2s';
      
      sizePrice.addEventListener('mouseenter', () => {
        sizePrice.style.background = '#e0e0e0';
      });
      
      sizePrice.addEventListener('mouseleave', () => {
        if (!sizePrice.classList.contains('selected')) {
          sizePrice.style.background = '#f0f0f0';
        }
      });
    });
  });
  
  // Add CSS for selected state
  const style = document.createElement('style');
  style.textContent = `
    .size-price.selected {
      background: #4CAF50 !important;
      color: white !important;
      font-weight: bold;
    }
  `;
  document.head.appendChild(style);
}

// Function to render menu in the UI (with limit to prevent timeout)
function renderMenu(menuData, maxCategories = 10) {
  // Find the menu panel
  let menuPanel = document.querySelector('.menu-panel');
  if (!menuPanel) {
    console.error('Menu panel element not found');
    return;
  }
  
  // Remove any "no data" message
  const noData = menuPanel.querySelector('.no-data');
  if (noData) {
    noData.remove();
  }
  
  // Find or create menu-list container
  let menuList = menuPanel.querySelector('.menu-list');
  if (!menuList) {
    menuList = document.createElement('div');
    menuList.className = 'menu-list';
    menuPanel.appendChild(menuList);
  }
  
  // Clear existing content
  menuList.innerHTML = '';
  
  console.log('renderMenu called with data:', menuData);
  
  const categories = menuData.data || [];
  const limitedCategories = categories.slice(0, maxCategories);
  
  console.log(`Rendering ${limitedCategories.length} of ${categories.length} categories`);
  
  limitedCategories.forEach(cat => {
    const categoryDiv = document.createElement('div');
    categoryDiv.className = 'menu-category';
    
    const categoryTitle = document.createElement('h3');
    categoryTitle.textContent = cat.category;
    categoryDiv.appendChild(categoryTitle);
    
    const itemsList = document.createElement('ul');
    
    // Limit items per category to prevent overload
    const items = (cat.items || []).slice(0, 20);
    
    items.forEach(item => {
      const itemLi = document.createElement('li');
      itemLi.className = 'menu-item';
      itemLi.setAttribute('data-category', cat.category);
      itemLi.setAttribute('data-item', item.item);
      
      const itemName = document.createElement('span');
      itemName.className = 'item-name';
      itemName.textContent = item.item;
      itemLi.appendChild(itemName);
      
      const itemSizes = document.createElement('span');
      itemSizes.className = 'item-sizes';
      
      const sizes = item.sizes || item.sizePrices || [];
      sizes.forEach(sizeData => {
        const sizeSpan = document.createElement('span');
        sizeSpan.className = 'size-price';
        sizeSpan.setAttribute('data-size', sizeData.size);
        sizeSpan.setAttribute('data-price', sizeData.price);
        sizeSpan.textContent = `${sizeData.size} ($${sizeData.price})`;
        itemSizes.appendChild(sizeSpan);
      });
      
      itemLi.appendChild(itemSizes);
      itemsList.appendChild(itemLi);
    });
    
    categoryDiv.appendChild(itemsList);
    menuList.appendChild(categoryDiv);
  });
  
  // Add info if we limited the display
  if (categories.length > maxCategories) {
    const infoDiv = document.createElement('div');
    infoDiv.style.padding = '10px';
    infoDiv.style.fontStyle = 'italic';
    infoDiv.style.color = '#666';
    infoDiv.textContent = `Showing ${maxCategories} of ${categories.length} categories (limited for performance)`;
    menuList.appendChild(infoDiv);
  }
  
  // Re-setup click handlers for newly added items
  setupMenuItemSelection();
}

// Wire up UI buttons
document.getElementById('btn-export').addEventListener('click', async () => {
  const button = document.getElementById('btn-export');
  const originalText = button.textContent;
  
  try {
    // Disable button and show loading
    button.disabled = true;
    button.textContent = 'Loading...';
    
    addFlowStep('user-input', 'User Action: Export Menu', {
      action: 'Requesting menu export from FoodTec (this may take a moment...)'
    });
    
    const result = await callMcp("foodtec.export_menu", { orderType: "Pickup" }, false);
    
    if (!result.error && result.result) {
      // Store menu data in app state
      appState.menuData = result.result;
      
      // Render the menu in the UI (limited to 10 categories)
      renderMenu(result.result, 10);
      
      const categoryCount = result.result.data ? result.result.data.length : 0;
      addFlowStep('response', 'Menu Loaded Successfully', {
        totalCategories: categoryCount,
        displayed: Math.min(categoryCount, 10),
        message: 'Click on any item size (e.g., "Lg ($6.99)") to select it.'
      });
    } else if (result.error) {
      addFlowStep('error', 'Export Menu Failed', {
        error: result.error.message
      });
    }
  } catch (error) {
    console.error("Export menu failed:", error);
    addFlowStep('error', 'Export Menu Error', {
      error: error.message
    });
  } finally {
    // Re-enable button
    button.disabled = false;
    button.textContent = originalText;
  }
});

document.getElementById('btn-validate').addEventListener('click', async () => {
  try {
    // Use the current payload from the preview
    if (!appState.currentPayload || !appState.currentPayload.category) {
      addFlowStep('error', 'Validation Error', {
        message: 'No order selected. Please select a menu item first.'
      });
      return;
    }
    
    // Store the original menu price before validation
    const originalPrice = appState.currentPayload.price;
    
    addFlowStep('user-input', 'User Action: Validate Order', {
      action: 'Sending order to FoodTec for validation',
      order: JSON.stringify(appState.currentPayload, null, 2)
    });
    
    const result = await callMcp("foodtec.validate_order", appState.currentPayload);
    
    // Store both prices for acceptance
    if (result && !result.error && result.result && result.result.data) {
      const canonicalPrice = result.result.data.price;
      if (canonicalPrice) {
        // Store both the original menu price and canonical price
        appState.currentPayload.menuPrice = originalPrice;
        appState.currentPayload.price = canonicalPrice;
        appState.currentPayload.validated = true;
        updateJsonPreview('payload', appState.currentPayload);
        addFlowStep('response', 'Price Updated', {
          menuPrice: `$${originalPrice}`,
          canonicalPrice: `$${canonicalPrice}`,
          tax: `$${(canonicalPrice - originalPrice).toFixed(2)}`,
          message: 'Order validated successfully'
        });
      }
    }
  } catch (error) {
    console.error("Validate order failed:", error);
  }
});

document.getElementById('btn-accept').addEventListener('click', async () => {
  try {
    // Use the current payload from the preview
    if (!appState.currentPayload || !appState.currentPayload.category) {
      addFlowStep('error', 'Acceptance Error', {
        message: 'No order selected. Please select a menu item first.'
      });
      return;
    }
    
    // Make sure we have validated first
    if (!appState.currentPayload.validated) {
      addFlowStep('error', 'Acceptance Error', {
        message: 'Please validate the order first before accepting.'
      });
      return;
    }
    
    // For acceptance, send BOTH prices:
    // - menuPrice: original price without tax (goes in item)
    // - canonicalPrice: price WITH tax from validation (goes at order level)
    // - externalRef: for idempotency tracking
    // - idem: idempotency key
    const timestamp = Date.now();
    const acceptPayload = {
      category: appState.currentPayload.category,
      item: appState.currentPayload.item,
      size: appState.currentPayload.size,
      menuPrice: appState.currentPayload.menuPrice,  // Original price without tax
      canonicalPrice: appState.currentPayload.price,  // Price WITH tax from validation
      customer: appState.currentPayload.customer,
      externalRef: `ext-ui-${timestamp}`,
      idem: `acc-${timestamp}`
    };
    
    addFlowStep('user-input', 'User Action: Accept Order', {
      action: 'Sending order to FoodTec for acceptance',
      menuPrice: `$${acceptPayload.menuPrice}`,
      canonicalPrice: `$${acceptPayload.canonicalPrice}`
    });
    
    await callMcp("foodtec.accept_order", acceptPayload);
  } catch (error) {
    console.error("Accept order failed:", error);
  }
});

// Process natural language orders with streaming
document.getElementById('btn-process-order').addEventListener('click', async () => {
  const userInput = document.getElementById('user-input').value.trim();
  const button = document.getElementById('btn-process-order');
  
  if (!userInput) {
    addFlowStep('error', 'Input Error', {
      message: 'Please enter an order description.'
    });
    return;
  }
  
  // Disable button during processing
  button.disabled = true;
  button.textContent = 'Processing...';
  
  try {
    // Log the user input
    addFlowStep('user-input', 'Natural Language Order', {
      input: userInput
    });
    
    // Add a thinking bar container
    const thinkingBar = createThinkingBar();
    document.querySelector('.flow-console').appendChild(thinkingBar);
    
    // Call the streaming automation API endpoint
    const response = await fetch('/api/automation/process-order', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: userInput })
    });
    
    if (!response.ok) {
      throw new Error(`Server returned ${response.status}: ${response.statusText}`);
    }
    
    // Set up SSE reader
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    
    // Process streaming responses
    while (true) {
      const { done, value } = await reader.read();
      
      if (done) {
        removeThinkingBar();
        break;
      }
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      
      // Process complete lines
      for (let i = 0; i < lines.length - 1; i++) {
        const line = lines[i].trim();
        
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          
          try {
            const step = JSON.parse(data);
            handleStreamingStep(step, thinkingBar);
          } catch (e) {
            console.error('Failed to parse SSE data:', e);
          }
        }
      }
      
      // Keep the last incomplete line in buffer
      buffer = lines[lines.length - 1];
    }
    
    // Clear input on success
    document.getElementById('user-input').value = '';
    
  } catch (error) {
    console.error("Process order failed:", error);
    removeThinkingBar();
    addFlowStep('error', 'Processing Error', {
      message: error.message
    });
  } finally {
    // Re-enable button
    button.disabled = false;
    button.textContent = 'Process Order';
  }
});

// Helper: Create thinking bar container
function createThinkingBar() {
  const container = document.createElement('div');
  container.id = 'thinking-bar';
  container.className = 'thinking-bar';
  
  const header = document.createElement('div');
  header.className = 'thinking-header';
  header.innerHTML = '<span>🧠 AI Agent Thinking...</span>';
  
  const content = document.createElement('div');
  content.className = 'thinking-content';
  content.id = 'thinking-content';
  
  container.appendChild(header);
  container.appendChild(content);
  
  return container;
}

// Helper: Remove thinking bar
function removeThinkingBar() {
  const thinkingBar = document.getElementById('thinking-bar');
  if (thinkingBar) {
    thinkingBar.remove();
  }
}

// Helper: Handle streaming step
function handleStreamingStep(step, thinkingBar) {
  const content = document.getElementById('thinking-content');
  if (!content) return;
  
  const timestamp = new Date(step.timestamp).toLocaleTimeString();
  
  if (step.type === 'complete') {
    // Processing complete - show summary
    const completeDiv = document.createElement('div');
    completeDiv.className = 'thinking-step complete';
    completeDiv.innerHTML = `
      <div class="step-header">
        <span class="step-icon">🎉</span>
        <span class="step-time">[${timestamp}]</span>
        <span class="step-content"><strong>Processing Complete!</strong></span>
      </div>
    `;
    content.appendChild(completeDiv);
    
    // Add a close button to the thinking bar
    const header = thinkingBar.querySelector('.thinking-header');
    if (header && !header.querySelector('.close-btn')) {
      const closeBtn = document.createElement('button');
      closeBtn.className = 'close-btn';
      closeBtn.textContent = '×';
      closeBtn.style.cssText = 'float: right; background: none; border: none; color: white; font-size: 24px; cursor: pointer; padding: 0 10px;';
      closeBtn.onclick = () => removeThinkingBar();
      header.appendChild(closeBtn);
    }
    
    // Change header text and style
    const headerSpan = header.querySelector('span');
    headerSpan.textContent = '✅ AI Agent Complete';
    headerSpan.style.fontWeight = 'bold';
    
    // Highlight the thinking bar
    thinkingBar.style.borderColor = '#4caf50';
    thinkingBar.style.boxShadow = '0 4px 20px rgba(76, 175, 80, 0.3)';
    
    // Don't auto-remove - let user dismiss manually
    return;
  }
  
  const stepDiv = document.createElement('div');
  stepDiv.className = `thinking-step ${step.type}`;
  
  let icon = '💭';
  if (step.type === 'tool_call') icon = '🔧';
  if (step.type === 'result') icon = '✅';
  if (step.type === 'error') icon = '❌';
  
  stepDiv.innerHTML = `
    <div class="step-header">
      <span class="step-icon">${icon}</span>
      <span class="step-time">[${timestamp}]</span>
      <span class="step-content">${step.content}</span>
    </div>
  `;
  
  // Add data if present
  if (step.data) {
    const dataDiv = document.createElement('div');
    dataDiv.className = 'step-data';
    dataDiv.textContent = JSON.stringify(step.data, null, 2);
    stepDiv.appendChild(dataDiv);
  }
  
  content.appendChild(stepDiv);
  
  // Auto-scroll to bottom
  thinkingBar.scrollTop = thinkingBar.scrollHeight;
  
  // Also add to flow console for permanent record
  if (step.type === 'thinking') {
    // Check if this is an order confirmation (contains order details)
    if (step.content.includes('order has been placed') || step.content.includes('Order #') || step.content.includes('🎉')) {
      // Create a special order confirmation card
      addFlowStep('order-confirmation', '🎉 Order Confirmed!', {
        message: step.content,
        timestamp: new Date().toLocaleTimeString()
      });
    } else {
      // Add LLM's thinking/response to flow console
      addFlowStep('llm-response', 'AI Response', {
        message: step.content
      });
    }
  } else if (step.type === 'result' || step.type === 'error') {
    addFlowStep(step.type === 'error' ? 'error' : 'response', step.content, step.data || {});
  }
}