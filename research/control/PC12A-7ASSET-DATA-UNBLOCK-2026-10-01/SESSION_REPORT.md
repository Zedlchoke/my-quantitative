# SESSION_REPORT — PC12A-7ASSET-DATA-UNBLOCK-2026-10-01

Owner instruction (verbatim anchor, task text 2026-10-01): "New separate
data-unblocking task … Owner asks you to make as many of these seven blocked
assets genuinely usable as possible: NZDUSD, USDCHF, XAUUSD, XAGUSD, BRENT,
WTI, NATGAS. Do practical acquisition and validation, not only a plan." —
with hard boundaries (preserve owner root + the other active ZCode chat;
separately owned worktree/data paths; no scored budget reuse, no S1, no
terminal-eligibility change, no orders, no push/merge, no purchases, no
competing for a held heavy lock; prepare the gate packet and stop there).

## Intake (measured 2026-10-01, before any write)

- Root: `main` @ `fc26adf155b159fe09451751c479afde05a74ec7`, dirty =
  OWNER_CHANGE / other-session files only (`DATA-FOUNDATION-SIXSOURCE-V1/ibkr_fx/sessions_index.jsonl`,
  `terminal_review_2026-10-01/DECISION_PACKET.md`, untracked SANDBOX/SLEEVE
  dirs) — preserved untouched, never staged.
- Heavy lock: `FREE_PROVEN` (no holder, no flock). No research python
  workers running. No lock acquired (all jobs are bounded HTTP fetches;
  PC12A-probe precedent).
- Registry: PC12A + EOSV2 TERMINAL (absorbing); no cycle registered for this
  session (unregistered owner-instructed lane, disclosed — precedent:
  `ibkr_capability_probe_2026-09-30`, `DATA-FOUNDATION-SIXSOURCE-V1`).
- Docs read in full: CLAUDE.md, HOW_TO_BE_A_LEAD_ENGINEER.md, AGENTS.md,
  CYCLE_REGISTRY.json (complete), GATE_TABLE_7ASSETS.md,
  LEG_RESOLUTION_MATRIX.md/.tsv, ERRATUM_LABELS_2026-09-30.md,
  ADDENDUM_SESSION_NOTES.md, IDENTITY_FREEZE_2026-09-30.json,
  ACQUISITION_REPORT/ADDENDUM provenance rows, sixsource INTAKE/FINAL_REPORT
  (scope check: their lanes are FX cost-band IBKR, crypto L2, rates/CME —
  disjoint from this session's surfaces).

## Lane (separately owned)

- Worktree `.worktrees/pc12a-7asset-unblock-20261001`, branch
  `orca/pc12a-7asset-unblock-20261001`, base `fc26adf155b159fe09451751c479afde05a74ec7`.
- Raw data: `~/.my-quantitative-data/pc12a-7asset-data-unblock-2026-10-01/raw/`
  (15 files, sha256 in `MANIFEST_RAW.json`).
- IBKR probe raw dir read read-only (never written).

## Reachability matrix (measured, not assumed)

| source estate | result |
|---|---|
| ecb.europa.eu (eurofxref-hist) | 200 OK |
| fred.stlouisfed.org (fredgraph.csv) | 200 OK — **UA-filtered CDN**: default curl UA passes; custom/Mozilla UA and python-requests TLS stack intermittently reset/timeout (measured 3 independent ways) |
| api.eia.gov v2 (owner key) | 200 OK after route fixes (`petroleum/pri/spt`, `natural-gas/pri/fut`; WTI id is `RWTC`) |
| www.eia.gov dnav hist_xls | RBRTEd.xls 200; RWTCLd/RNGWHHDd 404 (WTI/HH taken via v2 API) |
| eodhd.com /api/eod (owner key) | 200 OK (SLV 5138 rows, GLD 5500 rows) |
| Bank of England boeapps | HTTP 200 but body is an HTML error page → **UNAVAILABLE_FAIL_CLOSED** (reclassified; bytes kept) |
| TwelveData XAG/USD | entitlement-blocked: "available starting with the Grow or Venture plan" → **UNAVAILABLE_FAIL_CLOSED** (free key covers XAU only; no purchase permitted) |
| prices.lbma.org.uk, rbnz.govt.nz, perthmint.com | 403 → BLOCKED_NETWORK |
| api.bundesbank.de | empty reply → BLOCKED_NETWORK |
| stooq.com | JavaScript proof-of-work anti-bot → **BLOCKED_TRANSPORT, zero circumvention** (browser download is the owner path, see OWNER_PACKET D-2) |
| query1.finance.yahoo.com | reachable but ToS prohibits automated access → **REJECTED_LICENSE, not fetched** |
| api.snb.ch | 200 (not needed after ECB+FRED; not consumed) |

## Acquisitions (15 files; sha256 + license note + authority status per file in MANIFEST_RAW.json)

ECB eurofxref-hist zip+csv · FRED DEXUSNZ/DEXSZUS/DCOILBRENTEU/DCOILWTICO/DHHNGSP ·
EIA v2 RBRTE/RWTC/RNGWHHD daily JSON · EIA RBRTEd.xls (raw archive; no xls
parser in venv — numeric use is the v2 JSON / FRED mirror; disclosed) ·
EODHD SLV.US/GLD.US EOD JSON. Credential law: EODHD/EIA keys read from `.env`
inside the fetch processes; URLs logged redacted; TwelveData key attempted
once (entitlement-blocked), also redacted.

## Validation results (XCHECK_REPORT.json; all recomputed from raw bytes)

- NZDUSD vs FRED H.10: n=1491, abs p50 9.38 / p95 36.16 bps; vs ECB cross:
  n=1533, abs p50 21.52 / p95 82.90; ECB-vs-FRED mutual p50 20.65.
- USDCHF vs FRED: n=1491, abs p50 9.32 / p95 35.41; vs ECB: n=1533, abs
  p50 18.43 / p95 72.43.
- XAUUSD vs TD archive: reproduces IDENTITY_FREEZE (p50 3.2462 exact, signed
  mean +0.3359 USD); GLD proxy r 0.9857 / 12.4 bps mean |Δret|.
- XAGUSD: SLV proxy r 0.9827 / 24.3 bps; spot-level archive still missing.
- Energy: EIA official dailies span-complete 2020-10-01..2026-09-29, 0
  holes>5d; FRED mirrors byte-equal (0.0 bps all dates); contfut−spot joins
  and nonzero-only sign agreements per GATE_UPDATE table; synthetic flat-bar
  shares disclosed per gate-table F-1.

## Incidents

1. **INC-1 (security disclosure):** one EIA v2 curl diagnostic printed its
   error text including the keyed URL → `EIA_API_KEY` value appeared in the
   local session transcript. Not committed anywhere; local only. Rotation
   recommended to the owner (OWNER_PACKET). All later code paths suppress
   stderr/url echo.
2. **ERRATUM-1:** FRED DEXSZUS initially parsed with inversion; byte-check
   vs IBKR (0.8286 vs 0.8278) proved it is already USDCHF convention;
   corrected in-session (script + manifest note), raw bytes untouched.
3. **BoE reclassification:** 200-with-HTML-error-page initially landed as
   CSV; reclassified UNAVAILABLE_FAIL_CLOSED post-parse (manifest updated).
4. No hook denial occurred; no forbidden path touched; no circumvention of
   any anti-bot/PoW or SNI filter (Stooq/LBMA left blocked, documented).

## Boundary compliance checklist

- [x] No registry / eligibility / GO / ledger / FAMILY_FAILURES / MAP write
- [x] S1 untouched; zero scored computations; zero PnL; no orders
- [x] No push, no merge to main, no purchase, no keyed signup
- [x] Heavy lock never contested (FREE at start, free at close)
- [x] Owner root dirty files preserved; sixsource surfaces untouched
- [x] Historical/terminal artifacts (PC12A probe dir, forex-ng6 staging)
      read-only — XAU archive re-hashed, not moved (pin decision is D-6)

## Artifacts in this directory

`acquire_free_archives.py` · `acquire_addendum_entitled.py` ·
`validate_xcheck.py` · `MANIFEST_RAW.json` · `XCHECK_REPORT.json` ·
`GATE_UPDATE_7ASSETS.md` · `OWNER_PACKET.md` · `SESSION_REPORT.md` ·
`HANDOFF_7ASSET_UNBLOCK.json`

## Stopping point

Session stops at the gate as instructed: D-1..D-7 in OWNER_PACKET are owner
decisions; nothing further is executable without one of them (or a successor
cycle registration naming this packet as input).
