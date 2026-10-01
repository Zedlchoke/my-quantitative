# OWNER_PACKET — 7-asset data unblock, decisions at the gate (2026-10-01)

Prepared by session `PC12A-7ASSET-DATA-UNBLOCK-2026-10-01` (branch
`orca/pc12a-7asset-unblock-20261001`). Per the owner's instruction this
session did acquisition and validation only; **each item below is a gate the
owner alone can open.** Failing to decide keeps every current state
fail-closed — that is the default and it is safe. Evidence for every number:
`GATE_UPDATE_7ASSETS.md` + `XCHECK_REPORT.json` + `MANIFEST_RAW.json` in this
directory.

---

## D-1. Freeze PIT basis-acceptance thresholds + declare panels-of-record (NZDUSD, USDCHF)

Why repo evidence cannot decide it: the gate table law says a measured
overlap "does not pass gate 2" until numeric thresholds are frozen and the
availability lag is declared — measurement is ours, freezing is owner.

Measured basis available to freeze against (IBKR mid vs archive, 2020-10..2026-09):

| pair | FRED H.10 abs p50/p95/max bps | ECB cross abs p50/p95/max bps |
|---|---|---|
| NZDUSD | 9.38 / 36.16 / 155.10 | 21.52 / 82.90 / 249.23 |
| USDCHF | 9.32 / 35.41 / 191.07 | 18.43 / 72.43 / 239.84 |

- **Option A (recommended):** declare IBKR HMDS D1 BID/ASK the
  panel-of-record for execution-side simulation; declare FRED H.10
  (noon-ET fixing, same-day ~15:30 ET publication) + ECB eurofxref as
  CROSS_CHECK archives; freeze thresholds with headroom over the measured
  p95 (e.g. abs p50 ≤ 15 bps AND abs p95 ≤ 100 bps per archive; numbers are
  yours to set). Consequence: PIT for both pairs becomes
  `PASS_PIT_EVIDENCED` at the daily clock in a successor amendment.
- **Option B:** declare only one archive (FRED recommended — tighter and
  same-timezone). Consequence: simpler, one less calendar to maintain.
- Default if no decision: `MEASURED-BUT-UNFROZEN` (as XAUUSD is today).

One decision, one number pair per archive. Either option requires zero
further acquisition.

## D-2. Name the independent XAGUSD archive (or declare panel-of-record)

Why: silver is the only spot/metal with no reachable independent spot-level
archive from this environment. Measured today: SLV.US proxy r=0.9827
(proxy-class only).

- **Option A (recommended, zero cost, ~2 minutes):** open
  `https://stooq.com/q/d/l/?s=xagusd&i=d&d1=20190101&d2=20261001` in a
  normal browser (the anti-bot proof-of-work runs automatically in a
  browser; it is only scripts it blocks), save the CSV to
  `~/.my-quantitative-data/pc12a-7asset-data-unblock-2026-10-01/raw/owner_drop/`,
  and say "XAG archive dropped". This lane (or its successor) re-runs the
  frozen join contract on those bytes — no license ambiguity about *how*
  the bytes were obtained is being hidden: Stooq's free daily CSV is
  browser-downloadable and your download is a manual act.
- **Option B:** declare IBKR HMDS the panel-of-record for XAGUSD with
  next-business-day availability (same as Option A of D-1, no archive).
- **Option C (weakest):** accept the SLV ETF proxy as the cross-check
  archive (r 0.9827 / mean 24 bps return disagreement).
- Option D — licensed silver feed (LBMA shop etc.) — a purchase; **not
  authorized by today's instruction**, listed for completeness.

## D-3. Adopt EIA official spot dailies as the energy signal-side archive (BRENT, WTI, NATGAS)

Why: corpus rows that cite "WTI/Brent daily close (G-PIT-V3)" already ran on
a dossier archive; NATGAS signal legs had **nothing**. Today there are
official, span-complete (2020-10-01..2026-09-29, 0 holes>5d) daily series on
file for Brent spot (RBRTE), WTI Cushing (RWTC) and Henry Hub (RNGWHHD),
acquired from the primary source, with the FRED mirror verified byte-equal.

- **Option A (recommended):** in the successor plan amendment, admit the
  energy *signal-side* daily inputs from the EIA archives (manifest-pinned).
  Consequence: USDJPY-S065 (NATGAS+Brent), USDCAD-S090 (NATGAS/WTI ratio),
  EURUSD-S063 (Henry Hub leg) become data-addressable; TTF/AECO remain
  owner-named external sources.
- **Option B:** keep energy fully BLOCKED until a futures-chain source is
  also decided (single reopening, later).
- Note: **execution-side futures legs (short WTI, CL1–CL6 curve) stay
  BLOCKED regardless** — see D-4.

## D-4. Certified roll-chain source + ICE/NYMEX entitlement (futures execution legs)

Unchanged from `GATE_TABLE_7ASSETS.md` single-named actions; restated because
it is the only path that opens class-(d) rows: name the certified chain
source (licensed vendor / ICE-direct back-adjusted with documented roll, or
accept CONTFUT-with-synthetic-disclosure), and enable the ICE (IPE) and
NYMEX market-data subscriptions on the paper account. All purchases/actions
are owner-only. Nothing this session changed that calculus.

## D-5. IBKR Activity/Flex statement export (costs gate, 4 spot/metals at once)

Unchanged from the gate table (action P_A): export FX trades + Interest
Accruals to `~/.my-quantitative-data/ibkr_statement/`. One export covers
NZDUSD/USDCHF/XAUUSD/XAGUSD commission/swap measurement. (The sixsource
session's FX cost-band work is complementary, not a substitute — it measures
spreads, not the statement components.)

## D-6. XAU archive canonical-location pin (gate-table finding F-2)

One-line decision: pin
`.worktrees/forex-ng6/integration/.../p0/staging/XAUUSD_1day_full.json`
(sha `49c2684e…`, re-verified today) as canonical, or instruct a copy be
manifested under a `research/control/` data home. Recommended: pin + copy
with manifest (archive-then-reference; the worktree is historical evidence
and should not be a long-term data dependency).

## D-7. Successor cycle registration (the actual gate everything funnels into)

Admitting any corpus row still requires a PC12A-successor plan amendment (or
new cycle) registering the daily-clock cohort on the 4 spot/metals (+energy
signal side if D-3 accepted), with trial-ledger accounting per owner law. If
you instruct registration, this packet + GATE_UPDATE + the frozen manifests
are the preregistration inputs; a fresh GO would then be typed at that
cycle's own gate, not here.

---

### Incident disclosure (read before rotating anything)

**INC-1:** while diagnosing an EIA v2 curl error, the error text echoed the
request URL including the `EIA_API_KEY` value into the local session
transcript (one occurrence, local only, never committed anywhere). Per
security law it is disclosed here. **Recommended: rotate `EIA_API_KEY`** at
your convenience (free key, takes a minute). No other key was echoed;
EODHD/TwelveData URLs are recorded redacted everywhere.

**ERRATUM-1:** an early pass treated FRED `DEXSZUS` as needing inversion;
byte comparison vs IBKR (0.8286 vs 0.8278 on 2026-09-24) proved it is
already USDCHF convention. Corrected in-session; the manifest carries the
correction note; raw bytes untouched.
