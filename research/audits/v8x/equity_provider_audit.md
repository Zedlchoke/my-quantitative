# V8X Equity Provider Audit — A9 (equity-breadth)

- Agent: A9 (equity-breadth), worktree `a9-equity-breadth`, branch `orca/v8-a9-equity-breadth`
- Date: 2026-08-26 UTC
- Head at audit: `291a158e0220038ab3a9be66587f76c238e6ddea`
- Scope: PLAN.md §10.1 (two instrument modes), §10.2 (equity execution contract), gate X08
- Blind to V7/V8 results: yes — this audit touches only data dirs, environment presence checks, and universe snapshots.

## Verdict

```
DECISION: V8X_EQUITY_NOT_STARTED_PROVIDER_BLOCKED
MODE_A:   NOT_STARTED_DATA_MATURITY   (eligible_contracts = 0)
MODE_B:   PROVIDER_BLOCKED            (no credential / SDK / calendar / corporate-actions source)
```

## Mode A — `BINANCE_TRADFI_PERP_1Y` (measured, not assumed)

Definition used (from `data/universe.py`, matching PLAN §10.1): a tradFi perp is a Binance USD-M
contract with `contractType == TRADIFI_PERPETUAL` or `underlyingType ∈ {EQUITY, KR_EQUITY,
HK_EQUITY, CN_EQUITY, PREMARKET, COMMODITY}`. Eligibility additionally requires ≥365 days of
contract bars **and** funding.

Measurements:

| Check | Result |
|---|---|
| TradFi contracts listed on exchange (snapshot 2026-08-21) | 170 (160 equity-like) |
| TradFi contracts listed on exchange (snapshot 2026-08-23) | 170 (160 equity-like) |
| TradFi with onboard ≥365d (either snapshot) | **0** |
| Trading-status tradFi with onboard ≥365d | **0** |
| Max tradFi onboard days observed | 254.88 d (`XAUUSDT`) |
| Max equity-like onboard days observed | 206.62 d |
| On-disk tradFi bar/funding instruments across all primary + worktree catalog/data dirs | **0** |

On-disk inventory scanned (instrument directories): worktree `catalog/data` (4 instruments,
BTC/ETH only), primary `catalog/data` (4), `catalog_live_crypto/data` (40 instruments /
20 symbols), `derivatives_data/20260821` (7 crypto symbols), `funding_data/scan_2026`
(20 crypto symbols), `funding_data/20240820_20260821` (7 crypto symbols). Every instrument on
disk is a COIN-underlying USDT perpetual; cross-referenced against the 170-symbol tradFi set →
zero hits in bars and zero hits in funding.

Evidence snapshots (sha256):
- `research_snapshots/binance_tradfi_20260821.json` → `cd443a9b…ace0`
- `research_snapshots/binance_tradfi_20260823.json` → `36f2a37c…040`
- `research_snapshots/tradfi_history.csv` (72 rows tracking days-to-gate; all `ready_for_research=False`) → `9f2f0e6a…6ca`

**Conclusion:** the exchange does list stock/commodity perps, but the oldest is ~255 days onboard.
Zero contracts satisfy the 365-day bars+funding gate and none are downloaded. Measured eligible
count = **0**, confirming the PLAN §10.1 expectation. No backfill from underlying spot was
attempted or permitted.

## Mode B — `US_EQUITY_SPOT_1Y` provider readiness (presence-only, no secrets printed)

Environment credential check (presence booleans only; values never read, echoed, or committed):

- `ALPACA_API_KEY_ID`: absent · `ALPACA_API_SECRET_KEY`: absent · `ALPACA_API_SECRET`: absent
- alpaca-py aliases `APCA_API_KEY_ID` / `APCA_API_SECRET_KEY` / `APCA_API_SECRET`: all absent
- Any credential present: **NO**
- A `.env` file exists in both the primary repo and this worktree; existence noted only, file
  deliberately unread. Environment-only sourcing per PLAN §10.1 means this does not change the verdict.

Primary venv (`/Users/hoangminhlong/my-quantitative/.venv/bin/python`) package presence:

| Package | Importable | Version |
|---|---|---|
| alpaca-py | no | — |
| pandas-market-calendars | no | — |
| exchange-calendars | no | — |
| yfinance | no | — |
| polygon-api-client | no | — |
| pandas / numpy / pyarrow | yes | 3.0.5 / 2.5.2 / 25.0.1 |

Exchange calendar library available: **no** (PLAN §10.2 requires fail-closed official-session
handling — impossible without a calendar source). Corporate-actions source available: **no**
(no Alpaca corporate-actions endpoint client, no yfinance dividends/splits, no Polygon).
No network calls were made beyond importlib existence checks; nothing was downloaded.

## Decision rationale

Both modes fail independently:

1. Mode A cannot start — data maturity gate 0/10 (indeed 0/170) met; earliest possible maturity
   for today's oldest contract is ~110 days away per `tradfi_history.csv`.
2. Mode B cannot start — no approved provider credential in the environment, no provider SDK,
   no session calendar, and no corporate-actions feed. PLAN §10.1 forbids silent fallback to an
   undeclared source, so no substitute was attempted.

Per PLAN §11.1, an equity blocker must be surfaced, not hidden: equity trials
(`V8X-E-*`) remain unstarted; the crypto cohort may proceed one worker/wave without replacement
equity trials. This artifact satisfies gate X08's "machine blocker rõ ràng" branch.

Machine contract: `data/v8x_manifests/equity_provider_contract.json` (schema_version 1).

## What would flip each blocker

- Mode A: re-run the universe snapshot after ≥10 stock perps cross 365 onboard days AND download
  ≥365d contract bars + funding for them; then re-audit.
- Mode B (owner actions): export read-only Alpaca market-data keys into the environment
  (trading permission prohibited), install `alpaca-py` plus `pandas-market-calendars` or
  `exchange-calendars`, declare the corporate-actions source, freeze feed (SIP/IEX),
  adjustment mode, `asof`, and calendar version before any score.
