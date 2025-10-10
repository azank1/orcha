#!/usr/bin/env python3
"""
Test Pydantic models work correctly with proper data structures
"""
import sys
sys.path.insert(0, 'mcp')

from models.base import (
    SizePrice, MenuItem, Category, Customer, 
    OrderItem, OrderDraft, OrderValidation
)

def test_pydantic_models():
    """Test all Pydantic models can be created and validated"""
    
    print("🧪 Testing Pydantic Model Validation...")
    
    # Test SizePrice
    try:
        size_price = SizePrice(size="Large", price=12.99)
        print(f"✅ SizePrice: {size_price.size} @ ${size_price.price}")
    except Exception as e:
        print(f"❌ SizePrice failed: {e}")
        return False
    
    # Test MenuItem
    try:
        menu_item = MenuItem(
            item="Margherita Pizza",
            category="Pizza",
            sizePrices=[
                SizePrice(size="12\"", price=14.99),
                SizePrice(size="16\"", price=18.99)
            ],
            choices=[]
        )
        print(f"✅ MenuItem: {menu_item.item} with {len(menu_item.sizePrices)} sizes")
    except Exception as e:
        print(f"❌ MenuItem failed: {e}")
        return False
    
    # Test Category
    try:
        category = Category(
            category="Pizza",
            items=[menu_item]
        )
        print(f"✅ Category: {category.category} with {len(category.items)} items")
    except Exception as e:
        print(f"❌ Category failed: {e}")
        return False
    
    # Test Customer
    try:
        customer = Customer(
            name="John Doe",
            phone="555-1234",
            email="john@example.com"
        )
        print(f"✅ Customer: {customer.name} ({customer.phone})")
    except Exception as e:
        print(f"❌ Customer failed: {e}")
        return False
    
    # Test OrderItem  
    try:
        order_item = OrderItem(
            item="Margherita Pizza",
            category="Pizza", 
            size="16\"",
            sellingPrice=18.99,
            quantity=2
        )
        print(f"✅ OrderItem: {order_item.quantity}x {order_item.item} @ ${order_item.sellingPrice}")
    except Exception as e:
        print(f"❌ OrderItem failed: {e}")
        return False
    
    # Test OrderDraft
    try:
        order_draft = OrderDraft(
            type="Pickup",
            source="API",
            customer=customer,
            items=[order_item]
        )
        print(f"✅ OrderDraft: {order_draft.type} order with {len(order_draft.items)} items")
    except Exception as e:
        print(f"❌ OrderDraft failed: {e}")
        return False
    
    # Test OrderValidation
    try:
        validation = OrderValidation(
            success=True,
            canonicalPrice=37.98,
            orderDraft=order_draft,
            validationErrors=[]
        )
        print(f"✅ OrderValidation: Success={validation.success}, Total=${validation.canonicalPrice}")
    except Exception as e:
        print(f"❌ OrderValidation failed: {e}")
        return False
    
    print("\n🎉 All Pydantic models validated successfully!")
    return True

if __name__ == "__main__":
    success = test_pydantic_models()
    if success:
        print("✅ Pydantic model layer is working correctly!")
    else:
        print("❌ Pydantic model validation failed!")
        sys.exit(1)