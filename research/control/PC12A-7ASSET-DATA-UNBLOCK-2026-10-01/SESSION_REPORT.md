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

## Amendment 1 (owner-directed review, 2026-10-01)

Owner instruction: review/fix OWNER_PACKET D-1 before acting — the v1
example bar (abs p50 ≤ 15 AND p95 ≤ 100) contradicted the packet's own
measured ECB p50 (21.52 NZDUSD / 18.43 USDCHF) and would have failed both
ECB archives; do not loosen thresholds to fit observed data; separate basis
measurement from availability proof; verify independence claims; skeptic
check; commit a truthful delta.

Changes (OWNER_PACKET → v2, GATE_UPDATE → v2, this report appended;
XCHECK_REPORT/MANIFEST/raw bytes untouched):

1. D-1 threshold contradiction owned and withdrawn (verbatim withdrawn
   language quoted in the packet's corrections-of-record). Replacement law
   (D-1b): thresholds are post-observation by necessity and admissible only
   by role-derivation — tripwire-at-gross-error-scale (recommended) vs
   substitute-panel-at-fixing-structure-scale (tight; ECB then fails and is
   demoted, bar unmoved). Illustrative numbers are labeled illustrative and
   derived from role, not from the overlap table.
2. Withdrawn the v1 consequence claim "PIT becomes PASS_PIT_EVIDENCED".
   D-1c taxonomy: MEASURED_BASIS vs LAG_NOT_MEASURED (IBKR HMDS historical
   availability — no vintages on file) vs LAG_DECLARED_BY_OWNER (explicit,
   labeled DECLARED-NOT-MEASURED) vs STATED publication times (FRED/ECB —
   publisher documentation, not byte-evidenced). PASS only under an
   evidenced or explicitly declared availability protocol.
3. Independence: FX archives' distinctness is now byte-evidenced both ways
   (ECB-vs-FRED nonzero on 100% of 1475 common dates; holiday-calendar
   non-overlap sets: 62 US-holiday dates ECB-only, 19 TARGET-holiday dates
   FRED-only); institutional disjointness kept labeled stated. Energy
   EIA/FRED 0.0-equality reclassified everywhere as shared-source
   reproduction (retrieval confirmation, single-source compilation, NOT
   verification). Per-year basis table added (FRED/ECB separation present
   in every year 2020-2026).
4. Editorial slip during amendment: one stray text fragment briefly
   introduced into GATE_UPDATE header and removed in the same working
   session before commit (disclosed for completeness).

New measurements added (recomputed from the same raw bytes; script class
unchanged): calendar non-overlap counts, per-year abs-p50 basis table,
ECB-vs-FRED nonzero-value fraction. No previously reported number changed.

### Amendment 1, rev 2 — independent skeptic round (owner-ordered)

A fresh-context read-only skeptic audited the amended packet against
XCHECK_REPORT.json on six axes. Verdict: 0 BLOCKING, 3 MAJOR, 8 MINOR,
3 INFO. All three MAJORs were accepted as correct and fixed:

1. Tripwire numbers (50/250/10) still anchored to the observed table (p95
   bar sat 0.3% above observed max 249.23) — withdrawn a second time;
   D-1b now states the tripwire in instrument-volatility units (panel σ:
   NZDUSD 64.64 bps / USDCHF 49.62 bps, `panel_volatility` in XR), which
   do not reference the basis table. The unquantified "corrupted panel
   fails by orders of magnitude" claim was dropped.
2. Amendment-added numbers (per-year table, 62/19 calendar counts, 100%
   distinctness) had no on-file artifact — fixed by extending
   `validate_xcheck.py` itself (`per_year_basis_abs_p50_bps`,
   `calendar_non_overlap` with full date lists,
   `archive_value_distinctness`, `mirror_value_equality`,
   `retrieval_staleness`, `panel_volatility`); the regenerated
   XCHECK_REPORT.json verified additions-only by structural diff against
   the committed version.
3. FRED channel serving staleness (FX series ended 2026-09-25 at a
   2026-09-30ET retrieval, >=3 business days; energy mirrors 2026-09-29;
   ECB 2026-09-30) was byte evidence about availability left undisclosed —
   now in `retrieval_staleness`, D-1c and the GATE_UPDATE availability
   note, with the single-observation/cause-unknown caveats.

MINOR fixes applied: "exactly the national-holiday sets" downgraded to
enumerated-lists + spot-check; summary-cell labels aligned with the
section taxonomy (disjointness marked STATED; LAG NOT MEASURED in the
cell); WTI join-n vs mirror-n disentangled; "byte-equal/0.0 bps on every
aligned date" replaced by exact source-precision counts (1511/1492/1496,
max abs diff 0.0); XAU p95 delta re-attributed to an unanalyzed plausible
cause; XAU-vs-FX availability classes differentiated (assumed-on-record vs
no-assumption); D-2 Stooq browser path marked NOT TESTED; per-year range
wording corrected (8.02-12.61); rounding nit (12.61) fixed.

One editorial slip during this amendment cycle (stray text fragment briefly
in GATE_UPDATE header, removed same session before commit) was already
disclosed in the rev-1 log entry above.
