# OI_DECISIONS_APPLIED — owner directives 2026-10-01 (post-b00f934e), executed by A1

Owner decisions verbatim-in-substance; no options re-asked. Execution
state measured this session.

## OI-1 — PIT availability law (EXECUTED as declaration)
- **Decision**: IBKR HMDS D1 BID/ASK = panel-of-record for NZDUSD,
  USDCHF, XAUUSD, XAGUSD; use ONLY closed bars from the NEXT business
  day; label `LAG_DECLARED_BY_OWNER (DECLARED, NOT MEASURED — historical
  lag not measured; point-1/point-2 presence evidence on file)`.
- σ tripwire FROZEN: 1σ/5σ/0.5σ per the lane's σ-law (tripwire in
  panel-volatility units; tight bars demote ECB; NEVER loosened to pass).
- Divergence note: this is the lane checklist's OI-1 option (a). Per the
  owner's own instruction, if any registered artifact specified
  otherwise → amend + independent review BEFORE admitting; the fresh
  skeptic below covers this application.

## OI-2 — measured costs (BLOCKER — NOT_RUN, statement ABSENT)
- Measured this session: `~/.my-quantitative-data/ibkr_statement/` does
  NOT exist; a read-only scan of ~/.my-quantitative-data found NO
  statement/flex/activity files anywhere.
- **Consequence (owner law)**: commission/swap/slippage = NOT_RUN ⇒
  **NO after-cost PASS and NO scored run** until the statement lands.
- Precise export instruction (account IDs/keys excluded by construction):
  In TWS/Portal: *Performance & Reports → Statements → Activity
  Statement* (or Flex Queries → Activity Flex Query), period = Last 365
  Calendar Days (or custom covering any FX trades + overnights), sections
  MUST include **Trades** (with Commission) and **Interest Accruals**;
  format XML or CSV; save into `~/.my-quantitative-data/ibkr_statement/`.
  Paper-account activity qualifies if it contains FX trades + overnight
  FX lines. The file lands machine-local only — never in chat/git.

## OI-3 — XAU archive pin (EXECUTED, verified)
- Pinned: `/Users/hoangminhlong/my-quantitative/.worktrees/forex-ng6/integration/research/control/forex_ng6_run/p0/staging/XAUUSD_1day_full.json`
- sha256 verified this session = `49c2684ebb045302acf0c452b5aa9a3b96dff73eb3bc6f5add1801d6817fb33d`
  (exact match to the twice-re-verified pin; 1,347,055 bytes).
- XAU PIT basis therefore MEASURED against a pinned archive; XAU-as-SIGNAL admissible; XAU-as-VEHICLE still cost-gated by OI-2.

## OI-4 — XAG (EXECUTED as the owner's own fallback: NOT_RUN)
- Decision: IBKR panel-of-record, no SLV proxy, no purchase. The lane's
  plan/skeptic REQUIRED an independent archive for XAG PIT — per the
  owner's instruction ("If current plan/skeptic still requires
  independent archive, keep XAG NOT_RUN; do not override FAIL by prose"):
  **XAGUSD remains NOT_RUN** (PIT-FAIL stands; disclosure: no
  independent spot archive exists; IBKR-only panel under OI-1 labels).

## OI-5 — EIA signal inputs (EXECUTED)
- RBRTE/RWTC/RNGWHHD adopted as DAILY SIGNAL-ONLY inputs, conservative
  declared lag (1bd serving), SINGLE-SOURCE label; never fill prices.
- BRENT/WTI/NATGAS execution: **FLAT/NOT_RUN** — no CONTFUT, no
  ADJUSTED_LAST, no EIA-spot fills; no subscriptions enabled; AECO/TTF
  corpus rows: **NOT_RUN**.

## M1-CAL = N1 (no-unseal); S1 SEALED — already operative in plan §3.4.
## M1-D — USDCAD/AUDUSD INTRADAY = NOT_RUN this cycle; their DAILY-clock
candidates (e.g. USDCAD-S090 with EIA signal) judged separately in the
DAILY successor.

## Resulting admission state (this session, measured)
- Signal-side admissible: NZDUSD, USDCHF (OI-1 panels), XAU (pinned
  archive), EIA dailies (OI-5). XAG: NOT_RUN (OI-4 fallback).
- Executable vehicles: FX-spot pairs only; energy execution FLAT.
- Costs: NOT_RUN_STATEMENT (OI-2) ⇒ registration of the scored DAILY
  successor is GATED until the statement lands.
