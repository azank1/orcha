# 🚨 Clarification & Punishment Document
**Title: Do Not Make Simple Things Hard**

---
## 1. What We Did Wrong
### Over-Engineered the Flow
We added abstraction before truth:
- Translated orderType values (e.g., `Pickup → To Go`) when a direct echo would have been fine.
- Invented/insisted on sources like `Third Party` even after the API explicitly rejected everything except `Voice`.
- Recomputed a price (6.99 → 7.74) instead of using the canonical price the validation endpoint returned (7.41).

### Distracted by “Versioning Ghosts”
We treated “validation” vs “acceptance” as incompatible API versions (“v1/v2”) instead of two steps of the *same* lifecycle. That created fake translation pressures.

### Misplaced Focus on Fallbacks & Mocks
We let mocks and fallback logic bleed into production thinking instead of deleting them once the real API was reachable. This polluted reasoning and slowed convergence.

### Schema Hallucination
We made things up:
- Added or renamed fields unnecessarily.
- Normalized fields that didn’t need normalizing.
- Assumed transformations the server never required.

---
## 2. Why This Was Dumb
| Impact | Description |
|--------|-------------|
| Time Waste | Chased phantom “schema unification” instead of shipping working calls. |
| Cognitive Burn | Increased mental load with invented layers. |
| Delay | Slower progression to real integration success (validation + acceptance). |
| Trust Erosion | Introduced confusion about what actually *was* required. |

**Principle Violated:** Informed Simplicity (earn complexity only after proving necessity).

---
## 3. The Simple Truth We Ignored
The working pipeline is literally:
1. GET `/menu/categories?orderType=Pickup`
2. POST `/validate/order` with the item as-is (correct size, item, source=Voice, externalRef).
3. Take `price` from validation response.
4. POST `/orders` reusing externalRef, customer, and the canonical price.

No schema bridging. No enrichment logic. No speculative transforms.

---
## 4. Punishment & Guardrails
### Permanent Record
This document exists to prevent recurrence. It is the scar tissue.

### Guardrails
| Rule | Enforcement |
|------|-------------|
| API Literalism First | Payloads must match *observed* server JSON before abstraction is proposed. |
| No Hallucination | All new fields/renames require citation (docs snippet or real response). |
| Mocks Are Ephemeral | Remove / quarantine mock logic once a live endpoint responds. |
| Diff Before Theory | If Postman works but code fails: binary diff payloads *before* hypothesizing systemic issues. |
| Validate → Accept Contract | Always prefer server-returned canonical values (e.g., price) over recompute. |
| Explicit Unsupported Cases | Only throw errors for cases the server actually rejects (e.g., unsupported sources). |

### Self-Imposed Penalty
Any future “translation” layer proposal must include:
- The unmodified raw payload
- The *actual* server-dictated difference (diff snippet)
- Justification that the transformation is **required**, not aesthetic

---
## 5. Acknowledgment
We:
- Wasted time chasing imaginary version boundaries.
- Ignored working examples in favor of unverified abstractions.
- Added fragility under the banner of “architecture”.

This was avoidable. It will not repeat.

**Final Sentence:** Simplicity is law. Obey the live contract until reality—not imagination—demands more.

---
## 6. Current Working Recipe (Reference Snapshot)
### Validation Payload (Good)
```json
{
  "type": "To Go",
  "source": "Voice",
  "items": [
    { "item": "3pcs Chicken Strips w/ FF", "size": "Lg", "sellingPrice": 6.99, "externalRef": "ext-...-i0" }
  ],
  "customer": { "name": "Walk-in", "phone": "4108481234" },
  "externalRef": "ext-..."
}
```
### Acceptance Payload (Good)
```json
{
  "type": "Pickup",
  "source": "Voice",
  "externalRef": "ext-...",
  "items": [
    { "item": "3pcs Chicken Strips w/ FF", "size": "Lg", "sellingPrice": 6.99, "externalRef": "ext-...-i0" }
  ],
  "customer": { "name": "Walk-in", "phone": "4108481234" },
  "price": 7.41
}
```

---
## 7. What To Do Next (Only If Needed)
| If You Need… | Do This |
|--------------|---------|
| Multi-item orders | Just replicate item objects; still reuse validation price (or sum if server returns aggregated value). |
| Delivery support | Confirm valid address formats *first*; don’t guess transformations. |
| Pricing clarity | Ask FoodTec for a breakdown (tax? included modifiers?) instead of reverse-engineering. |
| Extensibility | Add abstraction *after* multiple concrete payloads prove a pattern. |

---
## 8. Monitoring Checklist
Before merging any future change touching FoodTec:
- [ ] Does validation payload still match live working shape?
- [ ] Are we forcing `source=Voice` unless proven expanded?
- [ ] Is acceptance price sourced from validation?
- [ ] Are “translations” justified by server evidence?

If any box is unchecked: stop, collect real payloads, resume only with facts.

---
## 9. One-Line Mantra
> **Ship the literal contract. Refactor only after reality forces your hand.**

---
_Last updated: generated during corrective review._
