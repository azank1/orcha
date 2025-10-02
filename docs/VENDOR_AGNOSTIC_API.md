# Target Vendor-Agnostic API Design

## Status: PLANNED (Not Implemented)

This document describes the **target** vendor-agnostic MCP tool API that will replace the current FoodTec-specific tools.

## Current State (FoodTec-Specific)

```typescript
// CURRENT - Tightly coupled to FoodTec
foodtec.export_menu(orderType) → { categories, items }
foodtec.validate_order({ category, item, size, price, customer }) → { canonical_price, ... }
foodtec.accept_order({ menuPrice, canonicalPrice, ... }) → { orderId, promiseTime }
```

**Problems:**
- Tool names include vendor identifier
- "Canonical price" is FoodTec terminology
- Two-step validate→accept flow is FoodTec-specific
- Adding Toast, Square, etc. requires new tool names
- UI/automation code needs vendor-specific logic

## Target State (Vendor-Agnostic)

### Tool: `orders.get_menu`

**Purpose:** Retrieve menu structure from the configured vendor.

```typescript
orders.get_menu({
  orderType: "Delivery" | "Pickup" | "DineIn"
}) → {
  categories: [{
    name: string,
    items: [{
      name: string,
      sizes: [{
        name: string,
        price: number
      }]
    }]
  }]
}
```

**Vendor Mapping:**
- FoodTec: Call `/api/v1/menu`
- Toast: Call `/orders/v2/menus`
- Square: Call `/v2/catalog/list`

---

### Tool: `orders.prepare_draft`

**Purpose:** Validate and prepare an order draft, returning the final price.

```typescript
orders.prepare_draft({
  item: {
    category: string,
    item: string,
    size: string
  },
  customer: {
    name: string,
    phone: string
  },
  type: "Delivery" | "Pickup" | "DineIn"
}) → {
  draftId: string,           // Opaque identifier for this draft
  itemPrice: number,         // Price without tax/fees
  finalPrice: number,        // Total price with tax/fees
  normalizedDraft: object    // Vendor-normalized draft data
}
```

**Vendor Mapping:**
- **FoodTec**: Call `POST /api/v1/order` (validation), extract `price` as finalPrice
- **Toast**: Call `POST /orders/v2/checks`, extract total
- **Square**: Call `POST /v2/orders`, extract `total_money`

**Key Concept:** 
- `itemPrice` = what user sees on menu (menuPrice in current code)
- `finalPrice` = what vendor charges (canonicalPrice in current code)
- Proxy layer translates between vendor terminology

---

### Tool: `orders.submit`

**Purpose:** Submit a prepared draft as a final order.

```typescript
orders.submit({
  draftId: string,           // From prepare_draft
  idem: string               // Idempotency key
}) → {
  orderId: string,
  promiseTime: string,       // ISO8601 timestamp
  finalPrice: number
}
```

**Vendor Mapping:**
- **FoodTec**: Convert draft to v2 format, call `POST /api/v2/order`
- **Toast**: Call `POST /orders/v2/checks/{checkId}/fire`
- **Square**: Call `PUT /v2/orders/{orderId}` with `state: OPEN`

**Key Concept:**
- Draft already validated, so submit is "fire and forget"
- No re-validation to avoid tax-on-tax issues
- Idempotency handled at MCP layer

---

## Implementation Strategy

### Phase 1: Keep FoodTec Tools, Add TODO Comments ✅
- **Status:** DONE
- Mark all FoodTec-specific code with `// TODO: Refactor to vendor-agnostic`
- Document target API (this file)
- Continue using `foodtec.*` tools in production

### Phase 2: Build Vendor Abstraction Layer
- **Status:** NOT STARTED
- Create `proxy/vendors/` directory
- Implement vendor adapters:
  - `proxy/vendors/foodtec.py`
  - `proxy/vendors/toast.py` (placeholder)
  - `proxy/vendors/square.py` (placeholder)
- Each adapter implements:
  ```python
  class VendorAdapter:
      def get_menu(self, order_type: str) -> Dict
      def prepare_draft(self, item: Dict, customer: Dict) -> Dict
      def submit_order(self, draft_id: str, idem: str) -> Dict
  ```

### Phase 3: Implement New MCP Tools Alongside Old
- **Status:** NOT STARTED
- Create `MCP/src/tools/orders/` directory
- Implement new tools:
  - `getMenuTool.ts`
  - `prepareDraftTool.ts`
  - `submitTool.ts`
- Keep `foodtec.*` tools for backward compatibility
- Proxy routes both old and new tool names

### Phase 4: Migrate UI and Automation
- **Status:** NOT STARTED
- Update UI to call `orders.*` tools
- Update automation workflows
- Test with FoodTec (should behave identically)

### Phase 5: Deprecate FoodTec-Specific Tools
- **Status:** NOT STARTED
- Mark `foodtec.*` tools as deprecated
- Remove after 30-day grace period
- Clean up proxy routing

---

## Benefits

### For Developers
- ✅ Add new vendors without changing MCP/UI code
- ✅ Vendor-specific quirks isolated in proxy layer
- ✅ Easier to test and maintain

### For Operations
- ✅ Swap vendors via configuration
- ✅ No deployment needed for new vendors
- ✅ Cleaner error messages

### For Business
- ✅ Faster vendor integration (days not weeks)
- ✅ Multi-vendor support for redundancy
- ✅ A/B test different vendors

---

## Example: Adding Toast Support

### Current Approach (FoodTec-Specific)
1. Create `toast.export_menu`, `toast.validate_order`, `toast.accept_order` tools
2. Update UI to detect vendor and call correct tools
3. Update automation to handle Toast-specific flows
4. **Result:** Vendor logic leaks into every layer

### Target Approach (Vendor-Agnostic)
1. Implement `proxy/vendors/toast.py` adapter
2. Configure proxy: `VENDOR=toast`
3. **Result:** UI and MCP unchanged, vendor logic contained

---

## Price Semantics (Vendor Translation)

| Concept      | MCP (Generic)     | FoodTec             | Toast            | Square           |
|--------------|-------------------|---------------------|------------------|------------------|
| Menu Price   | `itemPrice`       | `sellingPrice`      | `price`          | `base_price`     |
| Final Price  | `finalPrice`      | `canonical_price`   | `total`          | `total_money`    |
| Tax          | `finalPrice - itemPrice` | `tax`        | `tax_amount`     | `total_tax_money`|

**Key Insight:** Generic names hide vendor-specific terminology.

---

## Migration Checklist

- [ ] Create `proxy/vendors/` directory structure
- [ ] Implement `VendorAdapter` base class
- [ ] Port FoodTec logic to adapter
- [ ] Implement new MCP `orders.*` tools
- [ ] Update proxy to route both old and new tools
- [ ] Add integration tests for new tools
- [ ] Update UI to use new tools
- [ ] Deprecate `foodtec.*` tools
- [ ] Remove deprecated tools after grace period

---

## References

- Current Implementation: `proxy/handlers.py`, `MCP/src/tools/`
- Acceptance Fix: `docs/ACCEPTANCE_FIX.md`
- System Status: `SYSTEM_STATUS.md`

---

**Last Updated:** October 2, 2025  
**Status:** Documentation only - implementation pending
