# RFC 0002 — AAC charter fields on `authorized_scope`

- **Status:** Draft
- **Type:** Additive, backward-compatible — schema minor bump `1.1` → `1.2`
- **Workstream:** Agentic Authorization Charter (AAC)
- **Issue:** spec-change (AAC registry & behavioral scope monitor)

## Motivation

RFC 0001 gave agents a declared **authorised scope** (capabilities, spend cap,
counterparties, jurisdictions). Downstream supervisory use cases need that
scope to evolve into an **Agentic Authorization Charter (AAC)**: a versioned,
machine-readable, signable statement of *who* authorised the agent, on *which
rails* it may act, *how far* it may delegate, and *when* the authorisation is
valid. The manifest block remains the plain declared-intent baseline that the
signed charter (`common/charter/`) is built from and verified against.

Four things are missing from the 1.1 block:

- **Principal identity** — the legal entity accountable for the agent, with a
  typed identifier usable across jurisdictions (CIN/GST/Aadhaar in India,
  CNPJ in Brazil, UEN in Singapore, LEI globally).
- **Rails** — which DPI payment/data rails (UPI, AccountAggregator, ULI, …)
  the authorisation covers.
- **Delegation** — whether the agent may issue sub-agent charters and to what
  depth (attenuation is enforced by the charter library, FR-3).
- **Validity window and approval threshold** — when the charter is in force
  and above what transaction value a named human must approve.

## Proposed schema delta

New **optional** sub-fields on the existing `authorized_scope` object
(`additionalProperties: false` at every level, unchanged):

```yaml
authorized_scope:
  # ... 1.1 fields unchanged ...
  principal:
    legal_name: "Example Finserv Pvt Ltd"
    identifier_type: "CIN"           # CIN | GST | Aadhaar | CNPJ | UEN | LEI
    identifier_value: "U72900MH2020PTC000000"
    regulator_license: "NBFC-2024-0000"   # optional
  rails: ["UPI", "AccountAggregator", "ULI"]
  delegation:
    allowed: true
    max_depth: 2
  human_approval_required_above: "1000.00"   # decimal as string, per spend_cap_usd convention
  validity:
    not_before: "2026-08-01T00:00:00Z"       # RFC 3339
    not_after: "2027-08-01T00:00:00Z"
```

JSON Schema additions under `authorized_scope.properties`:

```json
"principal": {
  "type": "object",
  "description": "Legal entity accountable for the agent (emerge/1.2, RFC 0002).",
  "additionalProperties": false,
  "required": ["legal_name", "identifier_type", "identifier_value"],
  "properties": {
    "legal_name": { "type": "string", "minLength": 1 },
    "identifier_type": {
      "type": "string",
      "enum": ["CIN", "GST", "Aadhaar", "CNPJ", "UEN", "LEI"]
    },
    "identifier_value": { "type": "string", "minLength": 1 },
    "regulator_license": { "type": "string" }
  }
},
"rails": {
  "type": "array",
  "items": { "type": "string" },
  "description": "DPI rails the authorisation covers, e.g. UPI, AccountAggregator, ULI."
},
"delegation": {
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "allowed": { "type": "boolean", "default": false },
    "max_depth": { "type": "integer", "minimum": 0, "default": 0 }
  }
},
"human_approval_required_above": {
  "type": "string",
  "description": "Transaction value above which a named human must approve, decimal as string."
},
"validity": {
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "not_before": { "type": "string", "format": "date-time" },
    "not_after": { "type": "string", "format": "date-time" }
  }
}
```

All sub-fields are optional; absence means *unspecified*, never *unrestricted*
(same rule as RFC 0001).

## Compatibility / migration

- **Fully additive.** Every new field is optional; manifests valid under 1.1
  remain valid under 1.2 byte-for-byte. No field is renamed, removed, or
  tightened. No migration needed.
- Absence of a sub-field is defined as *unspecified*: verifiers and the
  delegation-attenuation check (`common/charter/attenuation.py`) treat a
  missing scope dimension as a violation ("unspecified"), never as an
  implicit pass.
- `schema_version` bumps to `"1.2"` per `governance.md` versioning rules.
  Tooling MUST continue to accept omitted `schema_version` as `1.0`, and 1.0 /
  1.1 manifests unchanged.

## Consumption points (informational)

- **Charter signing/verification (FR-2)** — `common/charter/build.py` maps the
  manifest block into an `AACCharter`; `signing.py` canonicalises
  (sorted-key compact JSON, the `emerge_node.envelope` scheme), hashes
  (sha256), and Ed25519-signs it. Verification is offline.
- **Monotonic delegation (FR-3)** — `common/charter/attenuation.py` enforces
  that a child charter's scope is a strict attenuation of its parent's
  (rails/actions subsets, caps non-increasing, depth decreasing, validity
  within parent window), chained by `parent_charter_hash`.
- **Registry** persists the extended block into the existing
  `agents.authorized_scope` JSON column and serves it to the charter verify
  API (FR-4).

## Alternatives considered

- **Charter as a separate document only, not on the manifest** — rejected:
  the manifest is the declared-intent baseline every agent already ships;
  duplicating scope fields in a second unsigned file invites drift. The signed
  charter is *built from* this block, keeping one source of truth.
- **Free-form principal identifier (single string)** — rejected: typed
  `identifier_type` is what makes the charter checkable across jurisdictions
  without regex-per-country heuristics.
- **Delegation semantics in the runtime** — out of scope, as in RFC 0001;
  1.2 is declaration + verification only.

## Non-goals

- No runtime enforcement of charter scope (blocking) in this change.
- No revocation semantics on the manifest (FR-5 lives in the registry/verify
  API, not the manifest).
- No new required fields; no network-layer semantics.
