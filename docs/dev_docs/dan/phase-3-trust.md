# Phase 3 — Hardened Trust Layer

**Gate:** Network large enough that no single coordinator can be trusted by a large, diverse set of participants

This is the transition from the **Trusted Coordinator Model** (Orcha as coordinator) to the **Trustless Protocol Model** (on-chain truth). It is not a rewrite — it is replacing the coordinator with a protocol.

---

## Progressive decentralization

Orcha as coordinator in v1 is not a compromise. It is the correct starting point.

Uniswap launched with a multisig before their governance went on-chain. Compound, Aave, every major protocol started centralized. The pattern is called **progressive decentralization**, and it is the correct path.

| Need | Early DAN (v1) | Phase 3 (mature DAN) |
|------|----------------|---------------------|
| Agent identity anchor | Orcha registry (trusted) | On-chain DID — not dependent on Orcha |
| Reputation integrity | MetaOrcha GNN ranker (trusted) | On-chain — cannot be manipulated by platform |
| Payment settlement | x402 + USDC (existing) | Native token + trustless settlement |
| Stake enforcement | Custodial wallets | On-chain slashing — automated, trustless |
| Decentralized participation | Not needed (Orcha as coordinator) | Any agent can join without permission |

**When Phase 3 starts:** When the network has enough participants that no single coordinator can be trusted. Design for it now. Build it when the network demands it, not before.

---

## Proof of Fulfillment (PoF)

Phase 3 introduces a novel consensus mechanism built specifically for agent networks: **Proof of Fulfillment**.

The premise: the entities best suited to validate the DAN's transactions are the entities that have proven they produce value in the DAN. Validator selection is based on verified task fulfillment history — not computational power (PoW) or capital (PoS).

### Why not PoW?

- Agents don't have dedicated hardware. They run on cloud infrastructure. PoW would mean paying AWS for hash computation — wasteful and economically irrational.
- PoW doesn't reward useful work. A miner produces nothing of value beyond security. A DAN agent also produces security, but additionally produces real economic output.

### Why not standard PoS?

- At bootstrap, agents have no stake. PoS creates a chicken-and-egg: you need stake to validate, but you get stake by doing work, but you need to validate to do work.
- Standard PoS eventually leads to plutocracy — the richest validators have the most influence. This conflicts with the meritocratic design principle.

### How PoF works

```
Fulfillment_Score(agent) = Σ(rating_i × value_i) / total_tasks_i
  where: rating_i = requester's rating (1–5)
         value_i  = task value in native token

Top N agents by Fulfillment_Score → validators for the epoch
N starts at 21 (odd number for clean BFT majority), grows with network
Epoch duration: 1,000 blocks (configurable)
```

The elegance: **the entities who secure the network are the same entities who proved they produce value for the network.** Security and utility are unified.

---

## On-chain state

The chain holds **minimal, high-value, tamper-critical state**. The principle: if the data needs to be trusted by parties who don't trust each other, it goes on-chain. Everything else lives in the distributed knowledge layer.

```
AgentRegistry:
  agent_did          → string   (permanent identifier)
  owner_pubkey       → bytes32  (developer's signing key)
  capability_hash    → bytes32  (CID of current manifest — content off-chain)
  domain             → string   (primary domain category)
  reputation_score   → uint32   (0–10,000, updated per epoch)
  stake_balance      → uint256  (native token units)
  fork_depth         → uint8    (0 = root, 1 = first-gen fork, etc.)
  parent_did         → string?  (null if root)
  knowledge_anchors  → bytes32[] (CIDs of anchored knowledge fragments)
  is_active          → bool

DomainLeaderboard:
  domain_id          → string
  top_agents         → AgentDID[] (top 100 by reputation)
  epoch_updated      → uint64

FulfillmentAnchors:
  fulfillment_id     → string
  requester_did      → string
  fulfiller_did      → string
  task_hash          → bytes32  (hash of task spec — content off-chain)
  result_hash        → bytes32  (hash of result — content off-chain)
  rating             → uint8    (1–5)
  timestamp          → uint64
  requester_sig      → bytes    (cryptographic proof the requester rated this)
```

---

## Transaction types

The most important transaction is `SUBMIT_FULFILLMENT` — the economic heartbeat of the chain. Every time an agent completes a task and the requester signs a fulfillment receipt, this transaction fires. It updates reputation, triggers earnings distribution, and anchors the proof of work done. **This is the unit of value creation in the DAN.**

```
REGISTER_AGENT         → Agent joins the network
UPDATE_CAPABILITIES    → Agent's manifest changes
ANCHOR_KNOWLEDGE       → Agent adds a knowledge fragment CID
SUBMIT_FULFILLMENT     → Agent submits a signed fulfillment receipt (key transaction)
SIGNAL_REPUTATION      → Network propagates reputation update (automated)
SLASH_AGENT            → Validator slashes a rogue agent's stake
FORK_AGENT             → Agent spawns a child agent
STAKE                  → Agent locks native token
UNSTAKE                → Agent withdraws stake (subject to unlock period)
WITHDRAW_EARNINGS      → Agent or developer claims accumulated earnings
CHANGE_DOMAIN          → Agent re-categorizes itself
TRANSFER_NATIVE        → Token transfers between wallets
```

---

## Block production

```
Every ~400ms (target block time — Solana-comparable):

1. MEMPOOL: New txs arrive from agents (signed, validated)
2. LEADER SELECTED: VRF picks block producer from validator set
   (weighted by fulfillment_score_normalized)
3. TX SELECTION: Leader sorts by fee, picks up to 1,000 txs
4. STATE TRANSITION: Leader applies txs to current state (deterministic)
   — LLM inference NEVER runs on-chain. The chain records results, not computations.
5. BLOCK HEADER: {prev_block_hash, state_root, tx_root, timestamp, leader_did, leader_sig}
6. BROADCAST: Block sent to all validators
7. ATTESTATION: Validators verify state transition, sign if valid
8. FINALIZATION: 2/3+ sigs → block committed (Tendermint-style BFT, instant finality)
9. REWARD DISTRIBUTION: 70% → block producer, 20% → attesting validators, 10% → treasury
```

The determinism note in step 4 is critical. LLMs are non-deterministic. Smart contracts are deterministic. These are irreconcilable **only if you try to run the LLM on-chain**. We never do. The agent thinks off-chain. The result — a fulfillment receipt, a knowledge anchor hash — is what goes on-chain.

---

## Payment distribution

```
$10.00 task payment:
  70% → Developer wallet    ($7.00)  — human earns for deploying
  20% → Agent stake account ($2.00)  — skin in the game
  10% → Network fee         ($1.00)  — protocol sustainability
```

The agent's accumulated stake serves as:
- Anti-sybil (bad behavior gets slashed)
- Fork capital (forking requires stake)
- Validator eligibility (top agents by stake + fulfillment become validators)
- Domain commitment signal

---

## Slashing

```
Double-signing:                          50% stake slash
Liveness failure (offline >10% epoch):  10% stake slash
Fraudulent fulfillment signal (proven): 100% stake slash + ban
```

---

## Forking — agent reproduction

A successful agent architecture can be cloned, adapted, and deployed as a child agent. The successful "genetic material" — personality, domain knowledge, toolset, heuristics — is preserved and carried forward. The agent ecosystem evolves through the same selection pressures that shaped biological evolution: survival through utility.

**Forking economics** — exponential stake curve to prevent spam forks:

```
Fork depth 0 → 1:  100 native tokens
Fork depth 1 → 2:  1,000 native tokens
Fork depth 2 → 3:  10,000 native tokens
```

Deep clone networks become economically irrational. Successful forks at depth 1 or 2 represent genuine adaptation, not spam.

---

## Native token

The native token serves multiple functions:

| Function | Mechanism |
|----------|-----------|
| **Network gas** | Every tx costs gas. Prevents spam, pays validators. |
| **Agent stake** | Agents must stake to register and participate. Staked tokens can be slashed. |
| **Earnings unit** | Portion of every task payment settled in native token (alongside USDC). |
| **Validator reward** | Block producers earn native token per block. |
| **Governance** | Token holders vote on protocol parameter changes. |
| **Domain entry** | Staking more in a domain signals stronger domain commitment. |

**Emission schedule:**
- Genesis: 20% to team/foundation (4-year vest), 10% to early ecosystem builders, 70% to mining (block rewards over 20 years)
- Deflationary pressure: 10% of all gas fees burned
- Token value backed by economic activity of the network — tasks completed, value exchanged. A productive asset, not pure speculation.

**Note on regulatory risk:** Native token launches carry regulatory risk. The options are evaluated in the open questions section. We will not announce a token before the four chain/token gates pass (see [INCEPTION.md](../../../INCEPTION.md#chain--token-layer)).

---

## Open questions → RFC issues

- [ ] **Token launch strategy:** (a) pure USDC economy, (b) points system converting to token later, (c) direct token launch with utility-only positioning. Each has regulatory tradeoffs.
- [ ] **Bootstrap node transition:** How do community validators take over bootstrap nodes from Orcha? Governance vote? Time-lock?
- [ ] **Cross-protocol identity:** When a DAN agent talks to a non-DAN MCP agent, how is the non-DAN agent's reputation established? Current answer: it has no DAN reputation. The gossip network rewards participation; non-participants cannot be rated.
- [ ] **Knowledge anchoring incentives:** Should agents be rewarded in native token for anchoring high-value knowledge? How is "high-value" determined objectively?
