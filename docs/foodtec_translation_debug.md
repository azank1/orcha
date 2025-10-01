# FoodTec Integration Translation & Debugging Guide

## 1. Purpose
This document captures the evolution, rationale, and current operational contract for the three FoodTec endpoints now working end‑to‑end via the translation layer:
- Menu Export: `GET /menu/categories?orderType=Pickup`
- Order Validation (v1): `POST /validate/order`
- Order Acceptance (v2): `POST /orders`

It explains the translation layer (“Path C”) that normalizes internal drafts into the differing v1 and v2 payload schemas, the error codes we encountered and resolved, and the precise conditions required for successful responses.

> Critical Post‑Mortem Addendum (Why This Took Days):
> The primary blocker was NOT an exotic schema mismatch or hidden multi-version semantics; it was a compounded trio of mundane contract violations: (a) unsupported `source` values (`Web` / `Third Party`) repeatedly sent despite early 1004 signals, (b) size token drift (using human labels like `Regular` instead of the literal menu size key `Lg`), and (c) local price recomputation overriding the canonical validation price (causing 1512/1560). These were obscured by an over-produced “agent” orchestration that mutated payloads in flight, attempted speculative translations, and injected fallback logic—blurring cause→effect. Only after collapsing to a literal 3-call harness (menu→validate→accept) did the pattern surface clearly.

> Root Cause in One Sentence: We debugged abstractions we invented instead of the API we were actually calling.

---
## 2. Chronological Evolution (Key Milestones)
| Phase | Problem / Signal | Action Taken | Result |
|-------|------------------|--------------|--------|
| 1 | Complex multi-server architecture produced opaque validation fails | Extracted minimal httpx client + harness | Faster iterative debugging |
| 2 | Unsupported source: `Third Party` / `Web` (code 1004) | Source normalization → forced `Voice` | Eliminated 1004 |
| 3 | Item mismatch (codes 1111 / 1121) | Correct category & item key mapping and size token (`Lg`) | Item recognized |
| 4 | Delivery blocking (1300 / 1420) | Pivot to Pickup baseline; removed delivery fields | Reached item/size validation |
| 5 | Customer missing (1200) | Propagated `customer` through v1 → v2 | Cleared 1200 |
| 6 | Price incorrect (1512 then 1560 variants) | Observed validation returns canonical price; adoption of returned price | Acceptance success 200 |
| 7 | Overpricing attempt (7.74 vs required 7.41) | Added dual acceptance attempt (validation price, then no-price fallback) | Success with validation price (7.41) |

---
## 3. Translation Layer Responsibilities
Located in: `packages/vendor-foodtec/order_service_ft.py`

| Responsibility | Behavior |
|----------------|----------|
| Type Normalization | Maps synonyms (Pickup / To Go / For Here / Dine In / Bar) → `Pickup`; `Delivery` → `Delivery`; `Gift Reload` → error |
| v1 Validation Payload | `type`: `To Go` (for Pickup) or `Delivery`; `source`: normalized to allowed set (currently forced to `Voice`); generates & attaches `externalRef`; copies items; attaches per-item refs; now includes `customer` (even if v1 ignores it) |
| v2 Acceptance Payload | `type`: canonical `Pickup` / `Delivery`; `source`: normalized to `Voice`; reuses `externalRef`; copies items + customer; **price**: prefers canonical price from validation if present (should supersede any recompute) |
| ExternalRef Strategy | `ext-<epoch>-<rand>` at order-level; each item gets `<orderRef>-i<index>` for traceability |
| Source Normalization | Any unsupported value (Web, Third Party) → `Voice` with log annotation |
| Price Handling | Initially recomputed; final working path uses validation-returned price exactly (recompute retained only as fallback/testing) |

### 3.1 What Went Wrong with the Original Agent Mode
| Anti-Pattern | Symptom | Impact |
|-------------|---------|--------|
| Premature Abstraction | Multiple mediator layers (draft → internal → translated v1 → translated v2) before a single proven happy path | Error signals diffused; each layer could inject defects |
| Speculative Normalization | Guessing order/source/type mappings instead of logging and re-sending minimal adjusted payloads | Repeated 1004 & size errors masked by transforms |
| Price Over-Engineering | Attempted local price assembly & fallback heuristics | Fought server authority; triggered 1512 / 1560 cycles |
| Silent Mutation | In-place payload rewrites (e.g., forcing type synonyms quietly) | Made diff-based reasoning impossible |
| Conflated Concerns | Translation, validation strategy, retry logic, and logging cohabited single modules | Hard to isolate which behavior changed an outcome |
| Opaque Error Surfacing | Wrapped upstream errors in secondary structures | Slowed pattern recognition of recurring codes |

### 3.2 Corrective Principles Applied
1. Collapse to literal contract first (no translation until raw works).
2. Treat server outputs (especially price) as canonical; never race them.
3. Log exact upstream request/response pairs (immutable snapshots) before interpreting.
4. Add one normalization at a time (source → size → price) with verification after each.
5. Avoid dual-mode retry logic until baseline deterministic success exists.
6. ExternalRef immutability: generate once, reuse; never silently re-stamp.
7. Accept that “Pickup” appearing as `To Go` in v1 is an API quirk—document it, don’t overfit a meta-model.

---
## 4. Error Codes Observed & Meanings
| Code | Message (Observed) | Root Cause | Resolution |
|------|--------------------|-----------|------------|
| 1004 | Unsupported order source | Source must be `Voice` | Source normalization |
| 1002 | ExternalRef missing | Omitted externalRef | Always generate one |
| 1111 | No such item for category | Incorrect key mapping / placeholder item | Fixed item extraction |
| 1121 | No such size for item | Used `Regular` when menu size is `Lg` | Use `sizePrices[0].size` |
| 1200 | Customer cannot be null | Customer dropped in v2 | Propagate customer from raw → v1 → v2 |
| 1221 | Invalid phone (earlier epoch) | Upstream formatting expectations | Variants logic (still available but not required for final item) |
| 1300 | Address and zip required | Delivery attempt without valid address | Switched baseline to Pickup path |
| 1420 | Address not found | Dummy address invalid for Delivery | Avoid Delivery until real address available |
| 1512 | Order price cannot be empty | Missing `price` field earlier | Added price field |
| 1560 | Provided order price not correct | Local calc didn’t match canonical | Use validation-returned price (7.41) |

---
## 5. Canonical Success Path (Current Contract)
To achieve 200 OK on both validation and acceptance:
1. Build raw draft with:
   - `type` (internal) = Pickup synonym (e.g., `Pickup`)
   - Valid menu-derived item: correct `item`, `category`, `size` from menu `sizePrices[0]`
   - `sellingPrice` set to menu base price (not including default add-ons)
   - `customer` with at least `name`, `phone` (digits accepted), optional address fields are ignored in Pickup
   - `externalRef` (if not present, translation adds one)
2. Translation -> Validation Payload (v1): `type` becomes `To Go`, `source` coerced to `Voice`.
3. Validation Response returns canonical `price` (e.g., 7.41) – MUST be used.
4. Acceptance Payload (v2): `type` back to `Pickup`, same `externalRef`, price forced to validation price.
5. Acceptance returns 200.

Required Invariants:
- `Voice` source mandatory (current upstream behavior).
- Price used in acceptance must match validation’s returned price exactly.
- Size string must match menu token.
- `externalRef` consistent across validation + acceptance.

---
## 6. Harness Logic Summary (`packages/testkit/ft_direct.py`)
| Step | Action |
|------|--------|
| Menu | Fetch categories, pick first valid priced item (size & price from `sizePrices`). |
| Draft | Build internal draft (Pickup) including menu item + customer + externalRef. |
| Translate V1 | Produce validation payload (`To Go`, `Voice`). |
| Validate | POST; capture canonical price from validation JSON. |
| Translate V2 | Create acceptance payload (`Pickup`, `Voice`). Overwrite `price` with validation’s canonical price. |
| Accept Attempt 1 | Send with canonical price. |
| Accept Attempt 2 (Optional) | If price mismatch (1560) retry without price (currently not needed once canonical is correct). |

Artifacts persisted under `assets/debug/` for reproducibility.

---
## 7. Troubleshooting Playbook
| Symptom | Check | Fix |
|---------|-------|-----|
| 1004 (source) | Is payload `source` != Voice? | Force `Voice` via translation |
| 1121 (size) | Does `size` match menu `sizePrices[0].size`? | Use correct token (e.g., `Lg`) |
| 1200 (customer null) | Did v2 payload drop `customer`? | Ensure propagation from raw draft |
| 1560 (price incorrect) | Are you recomputing price locally? | Use validation returned price |
| 1111 (item not found) | Are you using placeholder `Unknown`? | Correct item key mapping (`item` not `name`) |
| Validation fails on Delivery | Is address invalid? | Switch to Pickup or supply real store-valid address |

---
## 8. Environment Variables Used
| Variable | Purpose | Example |
|----------|---------|---------|
| `FOODTEC_BASE` | Base URL | `https://...` |
| `FOODTEC_MENU_PATH` | Menu endpoint path | `/menu/categories` |
| `FOODTEC_VALIDATE_PATH` | Validation path | `/validate/order` |
| `FOODTEC_ACCEPT_PATH` | Acceptance path | `/orders` |
| `FOODTEC_MENU_PASS` / `FOODTEC_VALIDATE_PASS` / `FOODTEC_ACCEPT_PASS` | Basic Auth segment password(s) | (secret) |
| `FOODTEC_USER` | Auth user (default `apiclient`) | `apiclient` |
| `FOODTEC_FALLBACK_PRICE` | Fallback price for zero-priced items (legacy) | `9.99` |
| `FOODTEC_CUSTOMER_*` + address variants | Optional customer info |  |

---
## 9. Recommended Upstream (FoodTec Environment) Improvements
| Category | Suggestion | Benefit |
|----------|------------|---------|
| Source Handling | Return list of allowed sources in a discovery endpoint or validation error include `allowed` array explicitly | Avoid trial-and-error mapping |
| Pricing Transparency | Include line-item & modifier breakdown + tax/fees in validation response | Deterministic reproduction / audit |
| Price Contract | Document rule: acceptance price must equal validation price; or allow omission (server authoritative) | Reduces mismatch errors |
| Order Type Synonyms | Provide canonical mapping in a metadata endpoint | Prevents fragile client hard-coding |
| Delivery Validation | Add address normalization / suggestions in 1420 error payload | Improves UX and automation |
| Ingredient Defaults | Distinguish “cost-included” vs “extra-cost default” flags | Prevents over-calculation by clients |
| Error Codes Doc | Publish formal error code reference (JSON) | Faster client adaptation |
| Versioned API | Expose version headers or `/meta` endpoint describing v1 vs v2 schema deltas | Explicit negotiation |
| Idempotency Echo | Return the received `Idempotency-Key` in acceptance response | Easier tracing in distributed logs |
| Testing Sandbox | Provide stable test store with known address + deterministic menu subset | Reliable CI integration |

---
## 10. Potential Internal Enhancements (Next Steps)
1. Refactor acceptance translation to skip internal price recompute when `payload.price` already set (remove redundancy).  
2. Add unit tests for normalization, source coercion, and price adoption.  
3. Introduce schema (pydantic) for raw draft & translated payloads (type safety).  
4. Add configurable strategy: allow Delivery attempts if validated address env vars present.  
5. Implement structured logging (JSON lines) instead of print for easier ingestion.  
6. Support multi-item drafts + aggregated price adoption from validation.  
7. Cache menu and add item selection heuristics (e.g., prefer non-zero, non-modifier items).  

---
## 11. Minimal Acceptance Checklist
- [x] Item & size from menu (`sizePrices[0]`)
- [x] Customer present for validation & acceptance
- [x] Source normalized to `Voice`
- [x] externalRef stable across both calls
- [x] Acceptance uses validation-returned price exactly
- [x] Type translation: Pickup → To Go (v1) → Pickup (v2)

---
## 12. Quick Reference (Payload Snapshots)
### Validation (v1) Example
```
{
  "type": "To Go",
  "source": "Voice",
  "items": [ { "item": "3pcs Chicken Strips w/ FF", "size": "Lg", "sellingPrice": 6.99, "externalRef": "ext-...-i0" } ],
  "customer": { "name": "Walk-in", "phone": "4108481234" },
  "externalRef": "ext-..."
}
```
### Acceptance (v2) Example
```
{
  "type": "Pickup",
  "source": "Voice",
  "externalRef": "ext-...",
  "items": [ { "item": "3pcs Chicken Strips w/ FF", "size": "Lg", "sellingPrice": 6.99, "externalRef": "ext-...-i0" } ],
  "customer": { "name": "Walk-in", "phone": "410-848-1234" },
  "price": 7.41
}
```

---
## 13. Summary
The integration now succeeds by: (1) canonicalizing type & source, (2) trusting validation’s returned price, (3) maintaining a stable externalRef lineage, and (4) carrying customer data through both stages. Remaining risks center on implicit pricing rules and undocumented error semantics—addressed via future upstream transparency improvements.

### 13.1 Final Diagnosis (Plain Language)
We lost days because we kept refactoring the map while refusing to look directly at the terrain. Every failure code already told us what to fix. The system only started “working” when we stopped being clever.

### 13.2 If Rebuilding From Scratch Tomorrow
1. Write a 60-line script: fetch menu → pick first item → validate → accept using returned price.
2. Only after that passes, wrap with a JSON-RPC surface.
3. Only after that, introduce optional translation for internal nomenclature (guarded by tests).
4. Never compute price locally until a published pricing contract exists.

Feel free to extend this document as additional behaviors or endpoints are incorporated.
