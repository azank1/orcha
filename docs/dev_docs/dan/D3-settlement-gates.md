# Phase D3 — Trustless settlement gates

Thesis reference: [`../EmergeOS-DAN.pdf`](../EmergeOS-DAN.pdf). Public summary: [`ROADMAP.md`](../../../ROADMAP.md).

## Policy

**No chain engineering and no token announcement** until all four gates pass.

Until then: USDC + trusted coordinator settlement (Gateway wallet code — hosted, out of OSS per [SECURITY.md](../../../SECURITY.md)).

## Gate criteria (all required)

| # | Criterion | Signal |
|---|---|---|
| G1 | Coordinator cannot be trusted by a large diverse network | Multiple independent coordinators + operator demand for neutrality |
| G2 | Stakes demand trustless settlement | Validator/agent disputes exceed mock ledger capacity |
| G3 | Third parties want permissionless entry | Operators blocked by KYC/coordinator allowlists |
| G4 | Community demands on-chain governance | RFC consensus on parameter changes fails off-chain |

## OSS vs hosted

| Layer | OSS repo | Hosted |
|---|---|---|
| Settlement interface | `settle_invocation`, fee split formulae | Privy wallets, on-chain USDC |
| Facilitator URL | Mock / documented interface | Production `PAYMENT_FACILITATOR_URL` |
| Token | Not present | Only if gates pass + public RFC |

## Mock → production path

1. D1 mock three-way split in Postgres `Transaction` rows
2. Hosted coordinator runs real USDC with same split math
3. When gates pass: escrow contract + validator stake (new repo / RFC)

## Review cadence

Re-evaluate gates at Day-90 post-D1 launch, not before D1 ships.
