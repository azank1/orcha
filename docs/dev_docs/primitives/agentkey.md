# AgentKey

**Per-action capability tokens for autonomous agents.**

> "OAuth was built for humans with browsers and consent screens. Agents have neither."

The current permission model for AI agents is broken in a predictable way: it grants session-level access. An agent with "Google Drive read" can read the entire Drive for the entire session. The agent thinks in seconds and acts in loops — but it holds a credential that a human designed for a 30-minute browser session.

AgentKey issues **Action Scope Tokens (ASTs)** — cryptographically scoped to a single action, a single resource, with a 30-second TTL and single-use enforcement.

---

## The problem, precisely

```
Current model (OAuth session tokens):
  SuperAgent gets: Google Drive read + write (session-scoped)
  Lead gen agent gets: Gmail compose (session-scoped)
  Risk: any compromised step can read/write the entire Drive for the session

AgentKey model (Action Scope Tokens):
  SuperAgent holds master credential
  Delegates to Lead Gen Agent: "compose one email to {address}" → 30s TTL → single use
  Lead Gen Agent cannot: read mail, access other addresses, compose a second email
  Delegation chain is auditable and cryptographically verifiable
```

---

## Design

### Action Scope Token (AST)

An AST is a signed, short-lived token encoding exactly one permitted action:

```json
{
  "iss": "did:orcha:system:superagent",
  "sub": "did:orcha:agent:lead-gen-agent",
  "aud": "https://gmail.googleapis.com",
  "act": "messages.send",
  "resource": "mailto:target@example.com",
  "iat": 1750000000,
  "exp": 1750000030,
  "jti": "uuid-single-use-nonce",
  "sig": "ed25519:..."
}
```

- `iss` — issuing agent DID (must be in delegation chain)
- `sub` — receiving agent DID
- `act` — single permitted action (capability ID from emerge.yaml)
- `resource` — specific resource URI (reduces blast radius)
- `exp` — 30 seconds from issuance (non-negotiable)
- `jti` — single-use nonce; enforced by the token registry

### Delegation chain

SuperAgent holds the root credential. It delegates scoped tokens to child agents. Child agents cannot delegate beyond what they were granted.

```
SuperAgent (master credential)
  └─► Lead Gen Agent: AST(act=messages.send, resource=mailto:target, ttl=30s)
        └─► ✗ CANNOT re-delegate to subagent
        └─► ✗ CANNOT compose a second email
        └─► ✗ CANNOT read inbox
```

---

## What exists today (the seed)

The current emerge.yaml schema already contains the conceptual precursor:

```yaml
security:
  auth_strategies:
    - id: strategy_gmail
      type: oauth2
      capability_ids: ["email_outreach", "full_pipeline"]  # ← per-capability scoping
```

`capability_ids[]` in auth strategies is the existing mechanism for scoping credentials to specific capabilities — not the full AgentKey spec, but the correct foundation. AgentKey formalizes this into cryptographic tokens with TTL enforcement.

---

## Migration path from today

| Today | With AgentKey |
|-------|--------------|
| OAuth session token granted to SuperAgent for session duration | AST issued per action, 30s TTL |
| `capability_ids[]` restricts which capabilities trigger auth | AST `act` field is cryptographic enforcement |
| In-memory grant cache (Redis, 24h TTL) | Token registry with single-use nonce table |
| Agent can re-use credential for entire session | Each use requires a new AST from parent |

---

## Status: Spec, `AGENTKEY_EXPERIMENTAL=true`

AgentKey is the most architecturally important primitive AND a standalone commercial product. We design it now. We build it when the ecosystem demands it.

The search trend for "per-action auth for autonomous agents" is 1,043% growth with no incumbent owning the standard. This is the OAuth 2.0 moment for agents.

**To contribute to the spec:** file an issue with `rfc` + `primitives` + `agentkey` labels. The open questions below are the active design decisions.

---

## Open questions → RFC issues

- [ ] **Token format:** Ed25519-signed JWT (familiar tooling) vs. Macaroon (nestable caveats, better for delegation chains) vs. custom binary format (minimal overhead)
- [ ] **Registry vs. stateless:** Single-use enforcement requires a nonce registry. Does that registry live in the SuperAgent process, in Redis, or on-chain (Phase 3)?
- [ ] **Revocation:** If a token is compromised before its 30s TTL, how is it revoked? On-chain revocation list? Or is 30s TTL short enough to not need revocation?
- [ ] **Cross-agent trust:** When an A2A agent delegates to a DAN-native agent, how does the non-DAN agent prove it honored the AST constraints?
- [ ] **Audit log:** Should all AST issuances be logged? Where? (Relevant for enterprise compliance)
