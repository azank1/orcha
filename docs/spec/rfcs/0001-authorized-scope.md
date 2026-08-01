# RFC 0001 — `authorized_scope` on emerge.yaml

- **Status:** Draft
- **Type:** Additive, backward-compatible — schema minor bump `1.0` → `1.1`
- **Issue:** spec-change

## Motivation

There is no machine-readable way to declare **what an agent is allowed to do** —
only what it *can* do (`skills`). Operators deploying agents under compliance or
budget controls — and any supervisor/verifier comparing declared intent against
observed behaviour — need a declared **authorised scope** on the manifest:
capabilities invoked, payment volume, counterparties paid, jurisdictions
touched.

This is the manifest-level foundation for:

- Verification findings (pass/fail vs declared scope)
- Payment-anomaly rules (counterparty / jurisdiction mismatch)
- Enforcement proposals gated by named-human approval

## Proposed schema delta

New **optional** root-level object `authorized_scope`:

```yaml
authorized_scope:
  allowed_capabilities: ["search_docs", "summarize"]
  spend_cap_usd: "5000.00"          # decimal as string, per payment.base_fee convention
  allowed_counterparties: ["did:orcha:agent:acme-billing", "acct:ops@example.com"]
  jurisdictions: ["GB", "EU"]
```

JSON Schema addition (root `properties`, root stays `additionalProperties: true`):

```json
"authorized_scope": {
  "type": "object",
  "description": "Optional declared limits on the agent's authorised behaviour (emerge/1.1). Consumed by supervisors/verifiers; absence means 'unspecified', not 'unrestricted'.",
  "additionalProperties": false,
  "properties": {
    "allowed_capabilities": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Capability/skill names the agent may invoke."
    },
    "spend_cap_usd": {
      "type": "string",
      "description": "Maximum machine-to-machine payment volume in scope, USD decimal as string."
    },
    "allowed_counterparties": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Allowed payee / counterparty identifiers."
    },
    "jurisdictions": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Authorised operating jurisdictions (ISO 3166-1 alpha-2 or regime codes)."
    }
  }
}
```

All four sub-fields are optional; an empty object is valid but meaningless and
SHOULD be omitted instead.

## Compatibility / migration

- **Fully additive.** Manifests without `authorized_scope` remain valid;
  absence is defined as *unspecified*, never as *unrestricted* (verifiers must
  not treat a missing block as a pass).
- Root `additionalProperties: true` is unchanged, so existing 1.0 tooling
  already tolerates the block; 1.1 tooling validates its shape.
- No existing field is renamed, removed, or tightened. No migration needed.
- `schema_version` bumps to `"1.1"` per `governance.md` versioning rules.
  Tooling MUST continue to accept omitted `schema_version` as `1.0`.

## Consumption points (informational)

- Registry persists the block into the Universal Manifest / DB (additive
  nullable field) and serves it on the agent manifest endpoint.
- Verifiers and supervisors compare `authorized_scope` against observed
  behaviour captured through the `ExecutionObserver` seam.
- Payment-rule engines use `allowed_counterparties` / `jurisdictions` /
  `spend_cap_usd` as rule inputs.

## Alternatives considered

- **Free-form `limits: {…}` map** — rejected: unverifiable shape; the four
  fields above are the minimum consumers actually need.
- **Scope in a separate signed policy document** — deferred: signed policy
  attestations can layer on later; the manifest block is the plain
  declared-intent baseline.
- **Enforcement in the runtime** (blocking out-of-scope calls) — out of scope
  for this RFC; 1.1 is declaration + verification only.

## Non-goals

- No runtime enforcement of scope (blocking) in this change.
- No change to billing semantics; `spend_cap_usd` is a supervisory limit, not
  a pricing field.
- No new required fields; no network-layer semantics.
