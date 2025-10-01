# FoodTec Universal Truth (Repo Canonical Spec)

## 1. Required Fields

- `type`: Must be `"Pickup"` for acceptance, `"To Go"` for validation.
- `source`: Must be `"Voice"` (all others rejected).
- `externalRef`: Non-empty unique string for order.
- `customer`: Object with `name` and `phone`.
- `items`: Array of objects:
  - `item`: Exact menu string from `/menu/categories`
  - `size`: Exact size string from menu (e.g., `"Lg"`)
  - `sellingPrice`: Base price from menu
  - `externalRef`: Item-level reference
- `price`: **Canonical total price** returned by validation (must be reused in acceptance).

## 2. Translation Rules

- `"To Go"` → `"Pickup"`
- `source`: `"Voice"` only
- Price: Use value returned from validation (`meta.response.price`), not recomputed.

## 3. Request Flow

1. **Menu Export** → Fetch categories & items
2. **Draft Order** → Build payload with menu item & base price
3. **Validate Order** → POST `/validate/order`
   - Response includes canonical `price`
4. **Accept Order** → POST `/orders`
   - Must forward canonical `price` unchanged

## 4. Example Payloads

### Validation Request
```json
{
  "type": "To Go",
  "source": "Voice",
  "externalRef": "ext-123",
  "customer": {
    "name": "Walk-in",
    "phone": "4105551234"
  },
  "items": [
    {
      "item": "3pcs Chicken Strips w/ FF",
      "size": "Lg",
      "sellingPrice": 6.99,
      "externalRef": "ext-123-i0"
    }
  ]
}
```

### Validation Response
```json
{
  "status": 200,
  "meta": {},
  "response": {
    "price": 7.41
  }
}
```

### Acceptance Request
```json
{
  "type": "Pickup",
  "source": "Voice",
  "externalRef": "ext-123",
  "customer": {
    "name": "Walk-in",
    "phone": "4105551234"
  },
  "items": [
    {
      "item": "3pcs Chicken Strips w/ FF",
      "size": "Lg",
      "sellingPrice": 6.99,
      "externalRef": "ext-123-i0"
    }
  ],
  "price": 7.41
}
```

## 🔑 Success Criteria

- All code paths in P2A and Proxy use this doc's payload shape.
- All smoke/proxy tests import `payload_fixture.json` based on this schema.
- Any future vendor gets their own `UNIVERSAL.md` under `/docs`.

## 🎯 Implementation Status

✅ **P2A Package**: Implements exact payload structure  
✅ **Proxy Server**: JSON-RPC wrapper using P2A directly  
✅ **Fixture Alignment**: `P2A/tests/payload_fixture.json` matches this spec  
✅ **End-to-End Flow**: Menu → Validate → Accept working with real FoodTec API

## 📋 Validation Checklist

- [x] `type`: "Pickup" in acceptance, "To Go" in validation
- [x] `source`: Always "Voice"
- [x] `phone`: Format with area code (e.g., "410-555-1234")
- [x] `externalRef`: Consistent across validation and acceptance
- [x] `price`: Canonical value from validation used in acceptance
- [x] `sellingPrice`: Original menu price at item level
- [x] All menu strings exact matches from API response

This document is the **single source of truth** for FoodTec integration. All implementation must conform to these specifications.
