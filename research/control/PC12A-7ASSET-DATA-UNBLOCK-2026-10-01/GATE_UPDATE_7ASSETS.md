# GATE_UPDATE_7ASSETS — what the 2026-10-01 unblocking session moved, per asset

Session `PC12A-7ASSET-DATA-UNBLOCK-2026-10-01` (owner-instructed data
unblocking; UNREGISTERED lane on branch `orca/pc12a-7asset-unblock-20261001`,
worktree `.worktrees/pc12a-7asset-unblock-20261001`). Baseline for every
"before" state: `GATE_TABLE_7ASSETS.md` (probe 2026-09-30). **No eligibility,
registry, GO, ledger or leg-status write happened here** — the amendment
footer law of the gate table is unchanged: admission only via plan amendment.

> **AMENDMENT 1 (owner-directed review 2026-10-01).** Three corrections, no
> measured number changed: (1) the sentence "Both fixings occur before the
> IBKR daily close, so same-day signal availability is *possible*…" is
> corrected to the fixing-time ≠ publication-time distinction — see the new
> "Availability vs basis" note; (2) "cross-verified between two channels"
> (energy) is corrected to "retrieval-confirmed, single-source compilation —
> NOT independent verification"; (3) summary-table wording "independent
> archives" is qualified (institutionally disjoint; distinctness
> byte-evidenced — see "Independence evidence"). The companion OWNER_PACKET
> v2 carries the full corrections-of-record, including the withdrawn
> threshold example and the withdrawn `PASS_PIT_EVIDENCED` consequence.
> **Rev 2 (after an independent skeptic round)** additionally: the first
> replacement tripwire numbers (50/250/10) were also withdrawn (p95 bar sat
> 0.3% above the observed max 249.23 — same anchoring flaw, milder form);
> D-1b in OWNER_PACKET v2 now states the tripwire in panel-volatility units;
> all amendment-added numbers are artifact-backed in XCHECK_REPORT.json v2;
> the FRED channel's measured serving staleness (FX series ended 2026-09-25
> at a 2026-09-30ET retrieval, >=3 business days) is disclosed in the
> availability note and D-1c.

Raw evidence: 15 files under
`~/.my-quantitative-data/pc12a-7asset-data-unblock-2026-10-01/raw/`
(MANIFEST_RAW.json, sha256 per file); all numbers in
`XCHECK_REPORT.json` (v2: original blocks + amendment-1 evidence blocks),
recomputed from raw bytes by `validate_xcheck.py`; the amendment re-run is
additions-only (structural diff vs the committed version: no previously
reported number changed). IBKR side = the PC12A probe's DV-verified raw dir
(`ibkr_acq_20260930/`, 131 files), parsed read-only.

Gate labels follow the mission invariant (`PASS`/`FAIL`/`NOT_RUN_*`;
nothing inferred).

## Summary table (moved vs unchanged)

| asset | gate rows moved 2026-10-01 | rows that remain owner-gated |
|---|---|---|
| NZDUSD | PIT: `NOT_RUN` → **MEASURED_BASIS (THRESHOLDS UNFROZEN, LAG NOT MEASURED)** against 2 archives (institutional disjointness STATED by publishers; value distinctness byte-evidenced — see Independence evidence) | costs (statement export), PIT threshold freeze + availability declaration, M1 corpus, intraday scan, plan amendment |
| USDCHF | same as NZDUSD | same |
| XAUUSD | TD overlap **re-reproduced** (p50 3.246 bps exact); GLD ETF proxy agreement measured (r 0.9857) as a second, proxy-class check | PIT threshold freeze + lag declaration (F-2 pin), costs, M1, amendment |
| XAGUSD | PIT: spot-level still **no reachable independent archive**; SLV ETF-proxy agreement **measured** (r 0.9827) | owner names the archive (or panel-of-record declaration); costs; M1; amendment |
| BRENT | signal side: **official EIA daily spot acquired + joined** (join n=1511; EIA-vs-FRED mirror alignment n=1511, exactly equal at source precision) | chain/roll/entitlement (licensed source decision + subscription), costs, amendment |
| WTI | same (contfut join n=1494; EIA-vs-FRED mirror alignment n=1492) | same |
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
(2022-09-13, 2022-11-10, 2025-04-09, 2023-02-03).

**Availability vs basis (Amendment 1 correction).** Fixing time is not
publication time, and neither is evidence about IBKR's own bar availability.
What is measured here is VALUE agreement only (`MEASURED_BASIS`). On file:
IBKR HMDS D1 historical-bar availability lag is **NOT_MEASURED** (one
retrieval, no vintages — same class as the XAU freeze's
`ASSUMED_NEXT_BUSINESS_DAY`); FRED/ECB publication times are **STATED by the
publishers, not byte-evidenced**. Additionally measured at retrieval
(`retrieval_staleness`): the FRED fredgraph FX series ended **2026-09-25**
(≥3 business days stale at the 2026-09-30ET retrieval) while ECB served
2026-09-30 — a channel serving-lag observation (single observation, cause
not analyzed on file) that any same-day availability premise for the FRED
channel must account for. A PIT `PASS` label would require an
evidenced availability protocol or an explicit owner declaration labeled
`LAG_DECLARED_BY_OWNER (DECLARED, NOT MEASURED)` — see OWNER_PACKET v2 D-1c.

**Gate state change: PIT `NOT_RUN` → `MEASURED_BASIS (THRESHOLDS UNFROZEN,
LAG NOT MEASURED)`** — the fail-closed pattern of the XAU freeze with one
difference kept explicit: the XAU freeze additionally carries an
ASSUMED_NEXT_BUSINESS_DAY assumption on record, while this FX state carries
no assumption at all. Nothing else moved.

## USDCHF — PIT gate detail

| archive | n | signed mean | signed median | abs p50 | abs p95 | abs max |
|---|---|---|---|---|---|---|
| FRED H.10 (`DEXSZUS`, already USDCHF convention — see ERRATUM-1) | 1491 | +1.54 | +1.40 | **9.32** | 35.41 | 191.07 |
| ECB cross `EURCHF/EURUSD` | 1533 | −0.33 | +0.30 | **18.43** | 72.43 | 239.84 |
| ECB vs FRED (mutual) | 1475 | +1.86 | — | 16.21 | 60.09 | — |

Same class of result and same reading as NZDUSD. **PIT `NOT_RUN` →
`MEASURED_BASIS (THRESHOLDS UNFROZEN, LAG NOT MEASURED)`** per the
Availability-vs-basis note above.

## Independence evidence (v2 addition; recomputed from the same raw bytes)

- **Distinctness, both directions (FX):** ECB-vs-FRED values are nonzero on
  **1475/1475 common dates** (`archive_value_distinctness`) — the two
  archives are not the same numbers republished. Publication calendars
  differ, with the full non-overlap date lists on file
  (`calendar_non_overlap`): **62 in-window dates** ECB-only (e.g.
  2020-11-26 Thanksgiving, 2020-11-11 Veterans Day) and **19 dates**
  FRED-only (e.g. 2021-04-02 Good Friday, 2022-04-18 Easter Monday) —
  consistent on spot-check with US-federal vs TARGET holiday calendars;
  exhaustive day-by-day holiday classification NOT performed. Institutional
  disjointness itself (FRBNY dealer collection / Eurosystem fixing / IBKR
  venue book) is stated by the publishers, not byte-evidenced; no
  strong-form independence claim is made.
- **Per-year abs-p50 basis (bps), structural stability:** NZD FRED
  8.02–12.61 across 2020-2026 (min 2025, peak 2022) vs ECB 19.66–31.23;
  CHF FRED 6.94–10.56 vs ECB 15.50–24.49 (ranges = per-year p50 min..max). The FRED/ECB separation is present in every
  year — structural (compounded 16:00 CET crosses, 6–7h before the IBKR
  close), not a regime artifact. Full table in OWNER_PACKET v2 D-1.
- **Degenerate contrast (energy):** EIA-vs-FRED values exactly equal at
  source precision on 1511/1511, 1492/1492, 1496/1496 aligned dates (max
  abs diff 0.0; `mirror_value_equality`) — the same numbers through two
  channels (shared-source reproduction; see energy section).

## XAUUSD — re-verification + proxy second check

- TD archive overlap re-run from bytes: n=1531, signed mean **+1.64 bps**
  (+0.3359 USD), abs p50 **3.2462 bps** — p50 reproduces the
  IDENTITY_FREEZE_2026-09-30 value exactly; p95 26.55 vs frozen 26.51
  (delta 0.04 bps; percentile-interpolation difference is the plausible
  cause, not analyzed on file).
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

Acquired (EIA v2 API under owner key — the official republication channel;
the underlying assessments are vendor-compiled per EIA/FRED documentation
(stated, not byte-evidenced). FRED mirrors
`DCOILBRENTEU`/`DCOILWTICO`/`DHHNGSP` are **exactly equal at source
precision on 1511/1511, 1492/1492 and 1496/1496 aligned dates (max abs diff
0.0; `mirror_value_equality`)**, so the two channels are one source for
provenance purposes — retrieval confirmation only, not independent
verification):

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
Hub, which had nothing on file — now exists via the official EIA
republication channel, span-complete over the cohort window, and
retrieval-confirmed by a FRED mirror that is exactly equal at source
precision on every aligned date (1511/1492/1496; max abs diff 0.0).
Amendment-1 correction: that mirror equality is shared-source reproduction
(single underlying compilation, EIA/Thomson-Reuters per publisher
documentation) — it proves retrieval integrity through two channels, NOT
value correctness; it is not independent verification.**

## Boundary compliance (this session)

No registry/eligibility/GO/ledger write; S1 untouched; no scored
computation; no orders; no push/merge; no purchase or subscription; no
keyed signup; IBKR surfaces untouched (the sixsource session's
`DATA-FOUNDATION-SIXSOURCE-V1/ibkr_fx/` and its dirty files in the root
checkout were never read in write mode and are preserved); owner root
checkout dirty state preserved exactly as measured at intake.
