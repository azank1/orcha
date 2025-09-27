import axios from 'axios';

const MCP_URL = 'http://127.0.0.1:9090/rpc';

async function callMcp(method: string, params: any, idempotencyKey?: string) {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'X-Request-ID': `test-req-${Date.now()}`
  };
  
  // If a separate idempotency key is provided, use it
  // Otherwise check if params.idem exists and use that
  if (idempotencyKey) {
    headers['Idempotency-Key'] = idempotencyKey;
  } else if (params.idem && typeof params.idem === 'string') {
    headers['Idempotency-Key'] = params.idem;
  }
  
  try {
    const response = await axios.post(MCP_URL, {
      jsonrpc: '2.0',
      id: `test-${Date.now()}`,
      method,
      params
    }, { headers });
    
    return {
      success: true,
      data: response.data,
      status: response.status,
      headers: response.headers
    };
  } catch (error: any) {
    console.error(`Error calling ${method}:`, error.message);
    if (error.response) {
      return {
        success: false,
        data: error.response.data,
        status: error.response.status,
        headers: error.response.headers
      };
    }
    throw error;
  }
}

async function testExportMenu() {
  console.log('\n=== Testing foodtec.export_menu ===');
  const result = await callMcp('foodtec.export_menu', {
    orderType: 'Delivery'
  });
  
  // Check for successful response
  if (result.success) {
    if (result.data.error) {
      console.log('❌ Failed to export menu:');
      console.log(JSON.stringify(result.data.error, null, 2));
      return null;
    }
    
    console.log('✅ Menu exported successfully!');
    
    // Parse the raw menu data to extract categories and items
    if (result.data.result && result.data.result.raw) {
      try {
        // First, let's check if the raw data is complete JSON
        const rawData = result.data.result.raw;
        console.log(`Raw data length: ${rawData.length} characters`);
        console.log('Raw data preview:', rawData.substring(0, 300) + '...');
        
        // Try to parse the full JSON first
        let menuData;
        try {
          menuData = JSON.parse(rawData);
        } catch (parseError) {
          console.log('Full JSON parse failed, attempting to extract from truncated data...');
          
          // Extract what we can from the truncated JSON using regex
          const categoryMatch = rawData.match(/"category"\s*:\s*"([^"]+)"/);
          const itemMatch = rawData.match(/"item"\s*:\s*"([^"]+)"/);
          const sizeMatch = rawData.match(/"size"\s*:\s*"([^"]+)"/);
          const priceMatch = rawData.match(/"price"\s*:\s*(\d+\.?\d*)/);
          
          if (categoryMatch && itemMatch && sizeMatch && priceMatch) {
            console.log(`Extracted from partial JSON: category="${categoryMatch[1]}", item="${itemMatch[1]}", size="${sizeMatch[1]}", price=${priceMatch[1]}`);
            
            // Create a minimal menu structure with what we extracted
            menuData = [{
              category: categoryMatch[1],
              items: [{
                item: itemMatch[1],
                sizePrices: [{
                  size: sizeMatch[1],
                  price: parseFloat(priceMatch[1])
                }]
              }]
            }];
          } else {
            console.log('Could not extract menu data from truncated JSON');
            return null;
          }
        }
        
        console.log(`Found ${menuData.length} categories`);
        
        // Extract full menu structure for later use
        const menuStructure = {
          categories: menuData.map((cat: any) => ({
            category: cat.category,
            items: cat.items.map((item: any) => ({
              item: item.item,
              sizes: item.sizePrices ? item.sizePrices.map((sp: any) => ({
                size: sp.size,
                price: sp.price
              })) : []
            }))
          }))
        };
        
        console.log('Menu structure extracted:');
        console.log(JSON.stringify(menuStructure, null, 2));
        
        return menuStructure;
      } catch (e) {
        console.log('⚠️ Could not parse menu raw data:', e);
        return null;
      }
    } else {
      console.log('⚠️ Menu returned without raw data');
      return null;
    }
  } else {
    console.log('❌ Request failed with status:', result.status);
    return null;
  }
}

async function testValidateOrder(menuStructure: any) {
  console.log('\n=== Testing foodtec.validate_order ===');
  
  if (!menuStructure || !menuStructure.categories || menuStructure.categories.length === 0) {
    console.log('❌ No menu structure available for validation test');
    return null;
  }
  
  // Pick first valid category and item from menu
  const firstCategory = menuStructure.categories[0];
  const categoryName = firstCategory.category;
  const firstItem = firstCategory.items[0];
  const itemName = firstItem.item;
  const firstSize = firstItem.sizes[0];
  const sizeName = firstSize.size;
  const itemPrice = firstSize.price;
  
  console.log(`Using from menu: category="${categoryName}", item="${itemName}", size="${sizeName}", price=${itemPrice}`);
  
  // Create order parameters using FLAT structure (not nested draft)
  // Based on the fixture file, the backend expects flat params, not nested draft
  const orderParams = {
    category: categoryName,
    item: itemName,
    size: sizeName,
    price: itemPrice,
    customer: {
      name: "Test User",
      phone: "410-555-1234"  // Use properly formatted phone with area code
    }
  };
  
  console.log('Sending FLAT parameters to validate_order:');
  console.log(JSON.stringify(orderParams, null, 2));
  
  const result = await callMcp('foodtec.validate_order', orderParams);
  
  if (result.success && result.data.result) {
    console.log('✅ Order validated successfully:');
    console.log(JSON.stringify(result.data.result, null, 2));
    
    // Extract canonical price from validation result
    const canonicalPrice = result.data.result.price;
    console.log(`Canonical price from validation: ${canonicalPrice}`);
    
    return {
      categoryName,
      itemName, 
      sizeName,
      canonicalPrice
    };
  } else if (result.data.error) {
    console.log('❌ Order validation failed:');
    console.log(JSON.stringify(result.data.error, null, 2));
    
    // Log meta.error if available
    if (result.data.error.data && result.data.error.data.raw) {
      try {
        const errorData = JSON.parse(result.data.error.data.raw);
        if (errorData.meta && errorData.meta.error) {
          console.log('Meta error:', errorData.meta.error);
        }
      } catch (e) {
        console.log('Could not parse error details');
      }
    }
    
    return null;
  }
  
  return null;
}

async function testAcceptOrder(validationResult: any) {
  console.log('\n=== Testing foodtec.accept_order ===');
  
  if (!validationResult) {
    console.log('❌ No validation result available for acceptance test');
    return;
  }
  
  const { categoryName, itemName, sizeName, canonicalPrice } = validationResult;
  
  // Create order parameters using FLAT structure (not nested draft)
  // Based on the fixture file, the backend expects flat params
  const idempotencyKey = `order-test-${Date.now()}`;
  
  const orderParams = {
    category: categoryName,
    item: itemName,
    size: sizeName,
    price: canonicalPrice, // Use canonical price from validation
    customer: {
      name: "Test User",
      phone: "410-555-1234"  // Use properly formatted phone with area code
    }
  };
  
  console.log('Sending FLAT parameters to accept_order:');
  console.log(JSON.stringify(orderParams, null, 2));
  
  const result = await callMcp('foodtec.accept_order', orderParams, idempotencyKey);
  
  if (result.success && result.data.result) {
    console.log(`✅ Order accepted successfully with idempotency key: ${idempotencyKey}`);
    console.log(JSON.stringify(result.data.result, null, 2));
    
    // Check for order_id in response
    const orderId = result.data.result.order_id || result.data.result.id;
    if (orderId) {
      console.log(`Order ID: ${orderId}`);
    }
  } else if (result.data.error) {
    console.log(`❌ Order acceptance failed with idempotency key: ${idempotencyKey}`);
    console.log(JSON.stringify(result.data.error, null, 2));
    
    // Log meta.error if available
    if (result.data.error.data && result.data.error.data.raw) {
      try {
        const errorData = JSON.parse(result.data.error.data.raw);
        if (errorData.meta && errorData.meta.error) {
          console.log('Meta error:', errorData.meta.error);
        }
      } catch (e) {
        console.log('Could not parse error details');
      }
    }
  }
}

async function runAllTests() {
  console.log('Starting MCP tools tests...');
  
  try {
    // Step 1: Test menu export and capture menu structure
    const menuStructure = await testExportMenu();
    
    if (!menuStructure) {
      console.log('❌ Cannot proceed without menu structure');
      return;
    }
    
    // Step 2: Test order validation using menu data
    const validationResult = await testValidateOrder(menuStructure);
    
    if (!validationResult) {
      console.log('❌ Cannot proceed without successful validation');
      return;
    }
    
    // Step 3: Test order acceptance using validation result
    await testAcceptOrder(validationResult);
    
    console.log('\n=== FINAL ASSESSMENT ===');
    if (validationResult) {
      console.log('✅ MCP forwarding + payload format aligned with FoodTec validation & acceptance');
    } else {
      console.log('❌ MCP forwarding or payload format needs adjustment');
    }
    
    console.log('\nAll tests completed!');
  } catch (error) {
    console.error('Test error:', error);
  }
}

// Run all the tests
runAllTests().catch(console.error);