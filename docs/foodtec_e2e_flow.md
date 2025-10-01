# FoodTec E2E Reference (Menu -> Validate -> Accept)

This is the minimal, canonical sequence. All values shown are representative; adjust item/size to what your menu returns.

## 1. Menu Fetch
Request:
GET /menu/categories?orderType=Pickup
Headers: Authorization (Basic), Accept: application/json

Response (excerpt):
[
  {
    "category": "Chicken",
    "items": [
      {
        "item": "3pcs Chicken Strips w/ FF",
        "sizePrices": [ { "size": "Lg", "price": 6.99 } ]
      }
    ]
  }, ...
]

Selection:
item = "3pcs Chicken Strips w/ FF"
size = "Lg"
basePrice = 6.99

## 2. Validation
POST /validate/order
Payload (v1 style):
{
  "type": "To Go",              // For Pickup flows
  "source": "Voice",             // MUST be Voice
  "externalRef": "ext-1732669000-4821",
  "customer": { "firstName": "Test", "lastName": "User", "phone": "5551231234" },
  "items": [
    {
      "item": "3pcs Chicken Strips w/ FF",
      "size": "Lg",
      "quantity": 1,
      "externalRef": "ext-1732669000-4821-i1",
      "price": 6.99
    }
  ]
}

Validation Response (excerpt):
{
  "price": 7.41,           // Canonical total MUST be used in acceptance
  "items": [ { "item": "3pcs Chicken Strips w/ FF", "size": "Lg", "price": 7.41 } ],
  "errors": []
}

## 3. Acceptance
POST /orders
Payload (v2 style):
{
  "type": "Pickup",               // Back to canonical token
  "source": "Voice",
  "externalRef": "ext-1732669000-4821",   // SAME as validation
  "customer": { "firstName": "Test", "lastName": "User", "phone": "5551231234" },
  "items": [
    {
      "item": "3pcs Chicken Strips w/ FF",
      "size": "Lg",
      "quantity": 1,
      "externalRef": "ext-1732669000-4821-i1",
      "price": 7.41
    }
  ],
  "price": 7.41
}

Acceptance Response (excerpt):
{
  "id": "ORD-123456",
  "price": 7.41,
  "items": [ { "item": "3pcs Chicken Strips w/ FF", "size": "Lg", "price": 7.41 } ],
  "errors": []
}

## Invariants Checklist
- Source always Voice.
- Size exactly matches menu token.
- externalRef stable across validation & acceptance.
- Acceptance price == Validation price (canonical server number).

## Quick Run
Use PowerShell helper:
```
./scripts/run-all.ps1
```
It starts the JSON-RPC server and runs `test_foodtec_flow.py`.

## JSON-RPC Example Lines
```
{"id":1,"method":"foodtec.export_menu","params":{"orderType":"Pickup"}}
{"id":2,"method":"foodtec.validate_order","params":{"order":{...orderPayload...}}}
{"id":3,"method":"foodtec.accept_order","params":{"order":{...samePayloadWithUpdatedPrice...},"validation":{...validationResponse.data...}}}
{"id":99,"method":"exit","params":{}}
```

## Status of Proxy Policy & MCP Server
- Proxy Layer: Removed/simplified; no active proxy code in current repo (previous multi-hop architecture deprecated). All calls are direct via `FoodTecClient`.
- Policy/Idempotency: Acceptance currently uses a single request; `Idempotency-Key` header logic exists only in legacy `packages/vendor-foodtec/client.py` (not used by new minimal flow). If idempotency is required, port that header logic into `api_client_ft.py`.
- MCP Server: Legacy engine/mcp directories have been removed in the reset. No running MCP server now. To reintroduce MCP, a fresh minimal handler would wrap the three JSON-RPC methods already in `main.py`. Until requested, it remains intentionally absent to keep surface minimal.

## Next Optional Enhancements
1. Add Idempotency-Key header in acceptance for robustness.
2. Persist validation response to disk for offline replay.
3. Introduce lightweight schema validation (pydantic) for requests.
4. Reboot MCP server only if another system needs tool invocation abstraction.
