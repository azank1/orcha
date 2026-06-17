# ConnectKit

**Typed integration connectors with normalized schemas.**

The long-tail problem of agentic apps: Alpaca calls it `qty`. Coinbase calls it `amount`. Interactive Brokers calls it `shares`. The App sees three different fields for the same concept.

ConnectKit is the typed connector interface that normalizes data across integrations. Every connector maps its raw API response to a canonical schema — `FINANCIAL_POSITION.quantity` for all three. The app never knows or cares which brokerage it's talking to.

---

## The connector interface

Every ConnectKit connector implements a typed `DataConnector` interface:

```python
from typing import AsyncIterator
from connectkit import DataConnector, Schema, NormalizedRecord

class AlpacaConnector(DataConnector):
    schema = Schema.FINANCIAL_POSITION    # declares what this connector produces

    async def fetch(self, credentials: dict) -> AsyncIterator[NormalizedRecord]:
        positions = await self._alpaca_client.get_positions(credentials)
        for pos in positions:
            yield NormalizedRecord(
                schema=Schema.FINANCIAL_POSITION,
                data={
                    "symbol":   pos["symbol"],
                    "quantity": pos["qty"],          # ← normalized from "qty"
                    "value":    pos["market_value"],
                    "cost":     pos["avg_entry_price"],
                    "pnl_pct":  pos["unrealized_plpc"],
                }
            )
```

The App reads `FINANCIAL_POSITION.quantity` regardless of whether the connector is Alpaca, Coinbase, or Interactive Brokers.

---

## Canonical schemas

| Schema | What it describes | Connectors |
|--------|------------------|------------|
| `FINANCIAL_POSITION` | A held asset: symbol, qty, value, cost basis, P&L | Alpaca, Coinbase, IB |
| `BANK_TRANSACTION` | A bank/credit transaction: amount, merchant, category | Plaid |
| `MARKET_QUOTE` | Real-time price: symbol, price, change, volume | Yahoo Finance, Alpaca |
| `CRYPTO_BALANCE` | A crypto wallet balance: asset, amount, usd_value | Coinbase, Kraken |
| `CALENDAR_EVENT` | A calendar item: title, start, end, attendees | Google Calendar, Outlook |
| `EMAIL_MESSAGE` | An email: from, to, subject, body_preview, timestamp | Gmail, Outlook |
| `CRM_CONTACT` | A CRM record: name, email, company, stage | Salesforce, HubSpot |

---

## Connector Generator

When no pre-built connector exists, the Connector Generator agent produces one from an OpenAPI spec:

```bash
emerge generate-connector --spec https://api.example.com/openapi.json --schema FINANCIAL_POSITION
```

Output: a draft `DataConnector` subclass + `ConnectorManifest`. A human developer reviews and publishes it. Not fully automated — human review is the quality gate.

---

## Pre-built connectors (launch targets)

These are built by the core team before the Finance vertical launch. Community grows the long tail.

| Connector | Schema | Priority |
|-----------|--------|----------|
| Plaid | `BANK_TRANSACTION`, `BANK_BALANCE` | P0 |
| Alpaca | `FINANCIAL_POSITION`, `MARKET_QUOTE` | P0 |
| Coinbase | `CRYPTO_BALANCE`, `FINANCIAL_POSITION` | P0 |
| Yahoo Finance | `MARKET_QUOTE` | P0 |
| Gmail | `EMAIL_MESSAGE` | P1 |
| Google Calendar | `CALENDAR_EVENT` | P1 |
| Stripe | `PAYMENT_TRANSACTION` | P1 |
| GitHub | `PR_EVENT`, `ISSUE_EVENT` | P2 (community) |
| Slack | `SLACK_MESSAGE` | P2 (community) |

---

## Developer earning model

Each connector earns a **per-sync fee** when running in deployed apps:

- Every time the Alpaca connector syncs a user's portfolio → fee charged to app → 80% to connector developer
- A connector that serves 1,000 daily active apps at 1 sync/day → 30,000 syncs/month → meaningful passive income

---

## Open questions → RFC issues

- [ ] **Schema evolution:** If `FINANCIAL_POSITION` needs a new field (e.g., `options_delta`), how does that propagate to existing connectors? Major version bump? Optional field?
- [ ] **Auth delegation:** Connectors run with user credentials from the vault. AgentKey (see [agentkey.md](agentkey.md)) should scope connector access per-fetch. Design the delegation chain.
- [ ] **CSV fallback:** For long-tail integrations with no API (e.g., niche brokerages that only offer CSV export), how does ConnectKit handle file-based ingestion?
- [ ] **Rate limiting:** Different APIs have different rate limits. How does ConnectKit expose this so the App Runtime doesn't inadvertently hammer an API?
