# GATE_UPDATE_7ASSETS — what the 2026-10-01 unblocking session moved, per asset

Session `PC12A-7ASSET-DATA-UNBLOCK-2026-10-01` (owner-instructed data
unblocking; UNREGISTERED lane on branch `orca/pc12a-7asset-unblock-20261001`,
worktree `.worktrees/pc12a-7asset-unblock-20261001`). Baseline for every
"before" state: `GATE_TABLE_7ASSETS.md` (probe 2026-09-30). **No eligibility,
registry, GO, ledger or leg-status write happened here** — the amendment
footer law of the gate table is unchanged: admission only via plan amendment.

Raw evidence: 15 files under
`~/.my-quantitative-data/pc12a-7asset-data-unblock-2026-10-01/raw/`
(MANIFEST_RAW.json, sha256 per file); all numbers in
`XCHECK_REPORT.json`, recomputed from raw bytes by `validate_xcheck.py`.
IBKR side = the PC12A probe's DV-verified raw dir (`ibkr_acq_20260930/`,
131 files), parsed read-only.

Gate labels follow the mission invariant (`PASS`/`FAIL`/`NOT_RUN_*`;
nothing inferred).

## Summary table (moved vs unchanged)

| asset | gate rows moved 2026-10-01 | rows that remain owner-gated |
|---|---|---|
| NZDUSD | PIT: `NOT_RUN` → **MEASURED (2 independent archives)** | costs (statement export), PIT threshold freeze, M1 corpus, intraday scan, plan amendment |
| USDCHF | PIT: `NOT_RUN` → **MEASURED (2 independent archives)** | same |
| XAUUSD | TD overlap **re-reproduced** (p50 3.246 bps exact); GLD ETF proxy agreement measured (r 0.9857) as a second, proxy-class check | PIT threshold freeze + lag declaration (F-2 pin), costs, M1, amendment |
| XAGUSD | PIT: spot-level still **no reachable independent archive**; SLV ETF-proxy agreement **measured** (r 0.9827) | owner names the archive (or panel-of-record declaration); costs; M1; amendment |
| BRENT | signal side: **official EIA daily spot acquired + joined** (n=1511; FRED mirror byte-equal 0.0 bps) | chain/roll/entitlement (licensed source decision + subscription), costs, amendment |
| WTI | same (n=1494) | same |
| NATGAS | same — **first daily price archive on file for Henry Hub** (n=1496); the "BLOCKED_NO_PRICE_DATA" state for HH-cited signal legs is now data-addressable | same + AECO/TTF remain non-IBKR (owner-named hub sources) |

## NZDUSD — PIT gate detail

IBKR daily mid vs archive, 2020-10-02..2026-09-30, basis bps:

| archive | n | signed mean | signed median | abs p50 | abs p95 | abs max |
|---|---|---|---|---|---|---|
| FRED H.10 (`DEXUSNZ`, noon ET, USD-per-NZD — no transform) | 1491 | −2.29 | −1.79 | **9.38** | 36.16 | 155.10 |
| ECB eurofxref cross `EURUSD/EURNZD` (16:00 CET) | 1533 | −0.37 | −1.05 | **21.52** | 82.90 | 249.23 |
| ECB vs FRED (mutual, no IBKR) | 1475 | −1.54 | — | 20.65 | 72.38 | — |

Reading (descriptive, not a gate verdict): the two archives agree with each
other to ~20 bps p50 and with IBKR to 9–22 bps p50 — consistent with
fixing-time separation (H.10 noon ET / ECB 16:00 CET vs IBKR 17:00 ET
session close) on a ~0.59 price. Worst dates are high-volatility sessions
(2022-09-13, 2022-11-10, 2025-04-09, 2023-02-03). Both fixings occur before
the IBKR daily close, so same-day signal availability is *possible* under an
owner-frozen D1-close clock — that declaration is the owner's, not ours.

**Gate state change: PIT `NOT_RUN` → `MEASURED-BUT-UNFROZEN` (same class the
gate table already uses for XAUUSD).** Nothing else moved.

## USDCHF — PIT gate detail

| archive | n | signed mean | signed median | abs p50 | abs p95 | abs max |
|---|---|---|---|---|---|---|
| FRED H.10 (`DEXSZUS`, already USDCHF convention — see ERRATUM-1) | 1491 | +1.54 | +1.40 | **9.32** | 35.41 | 191.07 |
| ECB cross `EURCHF/EURUSD` | 1533 | −0.33 | +0.30 | **18.43** | 72.43 | 239.84 |
| ECB vs FRED (mutual) | 1475 | +1.86 | — | 16.21 | 60.09 | — |

Same class of result and same reading as NZDUSD. **PIT
`NOT_RUN` → `MEASURED-BUT-UNFROZEN`.**

## XAUUSD — re-verification + proxy second check

- TD archive overlap re-run from bytes: n=1531, signed mean **+1.64 bps**
  (+0.3359 USD), abs p50 **3.2462 bps** — p50 reproduces the
  IDENTITY_FREEZE_2026-09-30 value exactly; p95 26.55 vs frozen 26.51
  (percentile-interpolation method difference only).
- NEW second check (proxy class, not a spot archive): GLD.US (EODHD, owner
  entitlement) daily-return agreement vs IBKR mid — Pearson r **0.9857**,
  mean |Δreturn| 12.40 bps, p95 37.81 bps, n=1500 return pairs.
- Unchanged: thresholds unfrozen, lag assumed-not-measured (owner decision),
  archive canonical-location pin (F-2), costs, M1.

## XAGUSD — honest boundary

- Spot-level independent archive: **none reachable this session.** TwelveData
  XAG/USD is entitlement-blocked (`Grow or Venture plan` — free key covers
  XAU only); LBMA JSON 403; Stooq serves a JavaScript proof-of-work
  anti-bot challenge (not bypassed, per zero-circumvention law); RBNZ/Perth
  Mint 403; Bundesbank API empty-reply; Yahoo `SI=F` reachable but ToS
  prohibits automated access (`REJECTED_LICENSE`, not fetched).
- What IS now measured: SLV.US ETF-proxy agreement vs IBKR XAGUSD mid —
  Pearson r **0.9827**, mean |Δreturn| 24.25 bps, p95 65.67 bps (n=1501
  pairs). This is proxy-class evidence (trust NAV + NYSE close vs London
  spot), **not** a spot-level PIT archive. The gate row stays
  `NOT_RUN_PIT_NO_ARCHIVE` with the proxy measurement attached for the
  owner's naming decision.

## BRENT / WTI / NATGAS — signal side acquired; execution side unchanged

Acquired (official primary source, EIA v2 API under owner key; FRED mirrors
`DCOILBRENTEU`/`DCOILWTICO`/`DHHNGSP` are **byte-equal: 0.0 bps on every
aligned date**, so the two channels are one source for provenance purposes):

| series | n (window) | span | holes>5d |
|---|---|---|---|
| EIA RBRTE (Brent spot FOB) | 1512 | 2020-10-01..2026-09-29 | 0 |
| EIA RWTC (WTI Cushing) | 1494 | 2020-10-01..2026-09-29 | 0 |
| EIA RNGWHHD (Henry Hub) | 1496 | 2020-10-01..2026-09-29 | 0 |

Join vs IBKR CONTFUT 6Y TRADES (structural basis — **not** a PIT gate):

| asset | n | contfut−spot mean USD | abs p50 / p95 USD | sign agreement (all / nonzero-only) | flat synthetic share on aligned |
|---|---|---|---|---|---|
| BRENT | 1511 | −24.95 | 23.27 / 48.70 | 0.776 / 0.781 | 63.0% |
| WTI | 1494 | −19.99 | 18.44 / 43.51 | 0.843 / 0.849 | 60.7% |
| NATGAS | 1496 | −0.28 | 0.96 / 3.63 | 0.557 / 0.596 | 41.4% |

Backwardation-consistent futures-below-spot levels, majority-synthetic
aligned bars (per gate-table F-1) and gas's genuinely noisy spot/front
relation all disclosed. **Gate state change: none on chain/roll/entitlement
(those stay FAIL — licensed-source decision is the owner's). What changed is
that the signal-side daily price archive for all three — including Henry
Hub, which had nothing on file — now exists, is official, span-complete over
the cohort window, and cross-verified between two channels.**

## Boundary compliance (this session)

No registry/eligibility/GO/ledger write; S1 untouched; no scored
computation; no orders; no push/merge; no purchase or subscription; no
keyed signup; IBKR surfaces untouched (the sixsource session's
`DATA-FOUNDATION-SIXSOURCE-V1/ibkr_fx/` and its dirty files in the root
checkout were never read in write mode and are preserved); owner root
checkout dirty state preserved exactly as measured at intake.
