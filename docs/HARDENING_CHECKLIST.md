# Short-Term Hardening Checklist

## Status: In Progress

This checklist ensures the menuPrice/canonicalPrice fix is robust and prevents regression.

---

## ✅ Completed

### Schema Enforcement
- [x] Lock schemas in MCP for `accept_order` (strict properties)
- [x] Add `acceptOrderParamsSchema` with `additionalProperties: false`
- [x] Require `externalRef` and `idem` for idempotency
- [x] Phone format: `^[0-9]{3}-[0-9]{3}-[0-9]{4}$`

### Runtime Invariants
- [x] Proxy refuses `accept` if `canonicalPrice < menuPrice`
- [x] Proxy validates phone format (XXX-XXX-XXXX)
- [x] Proxy checks prices >= 0
- [x] Proxy never re-validates on accept (no tax-on-tax)

### Logging & Visibility
- [x] Log accept attempts with `itemPrice`, `orderPrice`, `externalRef`
- [x] No PII in logs (phone already validated upstream)
- [x] Event: `accept.submit` with structured data

### Code Organization
- [x] TODO comments added for vendor-agnostic refactor
- [x] Document target API in `VENDOR_AGNOSTIC_API.md`
- [x] Keep FoodTec tools for now (refactor later)

---

## 🔄 In Progress

### Regression Tests
- [x] PowerShell test: `scripts/test-accept.ps1`
  - Validates order with FoodTec
  - Accepts with correct price pairing
  - Verifies order data returned
- [x] TypeScript test: `MCP/MCP_tests/test-accept-invariants.ts`
  - Test 1: canonical < menu (should fail)
  - Test 2: invalid phone format (should fail)
  - Test 3: negative prices (should fail)
- [ ] Run tests to confirm they pass
- [ ] Add to CI/CD pipeline

### UI Enhancements
- [x] UI stores both `menuPrice` and `canonicalPrice` after validation
- [x] UI never recomputes prices (uses stored values)
- [x] UI sends `externalRef` and `idem` for idempotency
- [ ] Add UI error display for invariant violations
- [ ] Show price breakdown (item + tax) in UI

---

## 📋 TODO

### Additional Testing
- [ ] Add table test with different items (3-5 menu items)
  - Appetizer: "3pcs Chicken Strips w/ FF" @ Lg ($6.99 → $7.41)
  - Pizza: Different size/price points
  - Salad: Another category
  - Goal: Prove logic is item-agnostic
- [ ] Test edge cases:
  - [ ] Item with $0.00 price (free item)
  - [ ] Item with high price (>$100)
  - [ ] Item with decimal prices ($6.99 vs $7.00)
- [ ] Load test: 100 sequential accepts (check for race conditions)

### Error Handling
- [ ] Better error messages for users
  - "Price mismatch" → "The price changed. Please validate again."
  - "Invalid phone" → "Phone must be in format XXX-XXX-XXXX"
- [ ] Retry logic for network failures
- [ ] Exponential backoff for 429 (rate limit) errors

### Documentation
- [ ] Add troubleshooting guide
  - What to do if accept fails
  - How to check logs
  - Common error codes
- [ ] Update README with new flow
- [ ] Create runbook for operations team

### Monitoring
- [ ] Add metrics:
  - Accept success rate
  - Average canonical price vs menu price (tax %)
  - Time to accept (latency)
- [ ] Add alerts:
  - Accept failure rate > 5%
  - canonical < menu (should never happen)
  - Invalid phone format (user education needed)

### Security
- [ ] Rate limiting on accept endpoint (prevent abuse)
- [ ] Validate externalRef uniqueness (prevent duplicate orders)
- [ ] Add authentication for UI→MCP calls
- [ ] Encrypt sensitive data in logs

---

## 🚀 How to Run Tests

### Prerequisites
```powershell
# Ensure all services are running
# Terminal 1: Proxy
cd D:\dev\orcha-1\proxy
python main.py

# Terminal 2: MCP
cd D:\dev\orcha-1\MCP
npm run build && node dist/index.js

# Terminal 3: UI
cd D:\dev\orcha-1\MCP\ui
npm run build && node dist/server.js
```

### Run Regression Tests
```powershell
# PowerShell test (validate + accept flow)
cd D:\dev\orcha-1
powershell -ExecutionPolicy Bypass -File .\scripts\test-accept.ps1

# TypeScript test (invariant checks)
cd D:\dev\orcha-1\MCP\MCP_tests
npx ts-node test-accept-invariants.ts
```

### Expected Output
```
=== Testing Order Acceptance Flow ===
[1/3] Validating order...
✓ Validation successful: canonicalPrice = 7.41
[2/3] Accepting order...
✓ Acceptance successful with canonicalPrice=7.41
[3/3] Verifying order data...
=== All Tests Passed ✓ ===
```

---

## 🔐 Invariants to Maintain

These must **ALWAYS** be true:

1. **Price Ordering:** `canonicalPrice >= menuPrice`
   - Canonical includes tax/fees, so it must be >= menu price
   - Exception: Free items where both = $0.00

2. **No Re-Validation:** Accept handler NEVER calls `validate_order`
   - Re-validation causes tax-on-tax
   - Use canonical price from previous validation

3. **Price Pairing:** Accept payload must have:
   - `items[].sellingPrice = menuPrice` (no tax)
   - `price = canonicalPrice` (with tax)

4. **Phone Format:** `\d{3}-\d{3}-\d{4}`
   - FoodTec requires area code
   - Reject early to avoid backend errors

5. **Idempotency:** Each accept must have unique `externalRef` and `idem`
   - Prevents duplicate orders
   - Enables safe retries

---

## 📊 Success Criteria

- [ ] All regression tests pass
- [ ] Manual UI test: Export → Validate → Accept works end-to-end
- [ ] Logs show correct price pairing
- [ ] No FoodTec errors (400 or 500)
- [ ] Accept latency < 2 seconds (p95)
- [ ] Code review approved
- [ ] Documentation updated

---

## 🐛 Known Issues

None currently. This section will track any issues found during testing.

---

## 📅 Timeline

- **Week 1 (Oct 2-8, 2025):** Complete hardening checklist ✅
- **Week 2 (Oct 9-15, 2025):** Run regression tests, fix any issues
- **Week 3 (Oct 16-22, 2025):** Monitor production, gather metrics
- **Week 4 (Oct 23-29, 2025):** Begin vendor-agnostic refactor planning

---

**Last Updated:** October 2, 2025  
**Owner:** Development Team  
**Status:** Hardening in progress, acceptance flow working
