# OWNER_PACKET v2 — 7-asset data unblock, decisions at the gate (2026-10-01)

Prepared by session `PC12A-7ASSET-DATA-UNBLOCK-2026-10-01` (branch
`orca/pc12a-7asset-unblock-20261001`). Per the owner's instruction this
session did acquisition and validation only; **each item below is a gate the
owner alone can open.** Failing to decide keeps every current state
fail-closed — that is the default and it is safe. Evidence for every number:
`GATE_UPDATE_7ASSETS.md` (v2) + `XCHECK_REPORT.json` + `MANIFEST_RAW.json`.

## AMENDMENT 1 (owner-directed review 2026-10-01, rev 2 after skeptic round) — corrections of record

1. **D-1 threshold contradiction, withdrawn.** v1 Option A carried the
   example bar *"abs p50 ≤ 15 bps AND abs p95 ≤ 100 bps per archive"* while
   the same packet reported ECB p50 basis of 21.52 bps (NZDUSD) and 18.43 bps
   (USDCHF) — that example would **FAIL both ECB archives** as measured.
   Presenting it inside the recommended option was contradictory; it is
   withdrawn. The replacement (D-1b below) derives bars from the archive's
   ROLE, applies them as they fall, and treats "archive fails a tight bar" as
   a legitimate demotion outcome — never as a reason to move the bar.
2. **PIT consequence overclaim, withdrawn.** v1 Option A said freezing
   thresholds *"consequence: PIT for both pairs becomes PASS_PIT_EVIDENCED
   at the daily clock in a successor amendment."* Withdrawn: cross-source
   basis measurement is not evidence of historical availability timestamps.
   D-1c below separates the two legs and names the only conditions under
   which a PIT PASS label is honest.
3. **D-3 "cross-verified" energy wording corrected.** EIA-vs-FRED equality
   (exactly equal at source precision on 1511/1511, 1492/1492, 1496/1496
   aligned dates) is shared-source reproduction — both channels serve the
   same numbers — so it confirms retrieval integrity, not value
   correctness. See D-3.
4. **Second threshold correction (skeptic round).** The first amendment's
   replacement numbers (50/250/10) were themselves anchored too near the
   observed table (p95 bar 250 vs observed max 249.23) and are also
   withdrawn; D-1b now states the tripwire in instrument-volatility units
   (panel σ), which do not reference the basis table.
5. **Evidence artifact discipline (skeptic round).** Every number this
   packet cites that was added during amendment now lives in
   `XCHECK_REPORT.json` (`per_year_basis_abs_p50_bps`,
   `calendar_non_overlap` with full date lists,
   `archive_value_distinctness`, `mirror_value_equality`,
   `retrieval_staleness`, `panel_volatility`); the report re-run is
   additions-only (no previously reported number changed, verified by
   structural diff against the committed version).
6. **FRED channel staleness disclosed (skeptic round).** At retrieval the
   fredgraph FX series ended 2026-09-25 (≥3 business days stale) while ECB
   served 2026-09-30 — see D-1c.

No previously reported measured number changed in this amendment; the new
measurements added are enumerated in item 5.

---

## D-1. Freeze the cross-check gate law + availability declarations (NZDUSD, USDCHF)

Why repo evidence cannot decide it: measurement is ours; freezing thresholds
and declaring availability semantics is owner-only.

Measured basis available to freeze against (IBKR D1 mid vs archive,
2020-10..2026-09; full-window stats from `XCHECK_REPORT.json`):

| pair | FRED H.10 abs p50/p95/max bps | ECB cross abs p50/p95/max bps |
|---|---|---|
| NZDUSD | 9.38 / 36.16 / 155.10 | 21.52 / 82.90 / 249.23 |
| USDCHF | 9.32 / 35.41 / 191.07 | 18.43 / 72.43 / 239.84 |

Per-year abs-p50 (structural stability of the separation, bps):

| year | NZD FRED | NZD ECB | CHF FRED | CHF ECB |
|---|---|---|---|---|
| 2020 | 9.04 | 19.66 | 6.94 | 15.50 |
| 2021 | 9.03 | 22.36 | 7.27 | 16.86 |
| 2022 | 12.61 | 31.23 | 10.52 | 24.49 |
| 2023 | 10.21 | 21.95 | 10.56 | 18.81 |
| 2024 | 8.59 | 19.66 | 9.33 | 16.16 |
| 2025 | 8.02 | 19.74 | 9.41 | 17.73 |
| 2026 | 8.44 | 19.97 | 10.00 | 19.34 |

### D-1a. Options (structure unchanged; wording corrected)

- **Option A (recommended):** declare IBKR HMDS D1 BID/ASK the
  panel-of-record for execution-side simulation; FRED H.10 + ECB eurofxref
  as CROSS_CHECK archives (roles per D-1b); freeze the gate law per D-1b;
  declare availability semantics per D-1c.
- **Option B:** FRED only as the gated cross-check (one calendar to
  maintain); ECB demoted to disclosed-secondary.
- Default if no decision: `MEASURED_BASIS` with thresholds unfrozen and
  availability `LAG_NOT_MEASURED` (fail-closed).

### D-1b. Threshold law (replaces the withdrawn example numbers)

1. **Every threshold frozen now is post-observation by necessity** — the
   distributions above were measured and reported before any freeze. A bar is
   therefore admissible only if justified by the archive's ROLE and by
   instrument properties independent of the cross-source basis table, never
   by "the observed data passes it". Whichever bar is frozen, the freezing
   amendment must log the measured distribution beside it and state which
   archives pass/fail on the day of freezing (exclusion-zone logging), and
   name the corruption modes the bar is intended to catch (level/scale
   errors, stale-frozen panels, systematic offset).
2. **Tripwire derivation (recommended), stated in instrument-volatility
   units.** Correction of record (skeptic round): the first amendment's
   fixed illustrative numbers (p50 ≤ 50 AND p95 ≤ 250 AND |signed mean| ≤
   10) are ALSO withdrawn — the p95 component sat 0.3% above the largest
   observed single-day deviation (249.23), the same table-anchoring flaw in
   a milder form. Replacement: express the bar in units of the panel's own
   daily-return volatility σ (an instrument property measured from the IBKR
   panel, independent of the basis table):
   **abs p50 ≤ 1σ AND abs p95 ≤ 5σ AND |signed mean| ≤ 0.5σ**, with σ =
   full-window daily close-to-close return σ of the IBKR mid panel
   (`panel_volatility` in `XCHECK_REPORT.json`: NZDUSD 64.64 bps,
   USDCHF 49.62 bps). The multiplier choice (1/5/0.5) is a scale-separation
   judgement the owner may alter; it does not reference the basis table.
   Instantiated today it reads: NZDUSD p50 ≤ 64.6 / p95 ≤ 323.2 / |mean| ≤
   32.3; USDCHF p50 ≤ 49.6 / p95 ≤ 248.1 / |mean| ≤ 24.8. **Observed
   outcome under this bar (an observation, not an input): both FRED
   (p50 9.38/9.32, p95 36.16/35.41) and ECB (p50 21.52/18.43, p95
   82.90/72.43) pass all three legs with margin.**
3. **Substitute-panel derivation (stricter, only if an archive is to be used
   as a data source, not merely a cross-check).** The bar must be derived
   from fixing-time structure BEFORE consulting the overlap table, then
   applied as it falls. Honest application today: with any bar near the
   10–15 bps p50 scale, **FRED passes (9.38/9.32) and ECB fails (21.52/
   18.43)** — and the correct handling is to demote ECB to
   disclosed-secondary (calendar-coverage) archive, NOT to raise the bar.
   The per-year table shows no tight bar can admit both: the separation is
   structural (ECB ≥ 15.5 in every year; FRED ≤ 12.61 in every year), because
   an ECB cross is two compounded 16:00 CET fixings taken 6–7 hours before
   the IBKR 17:00 ET close, while H.10 noon is 5 hours before it.

### D-1c. Basis measurement ≠ availability proof (label taxonomy)

- `MEASURED_BASIS` — what this session produced: cross-source VALUE
  agreement vs IBKR D1 mids. It says nothing about when any series was, or
  becomes, available.
- Availability evidence actually on file:
  - **IBKR HMDS D1 historical bars: availability lag NOT_MEASURED.** One
    retrieval (2026-09-30), no vintages, no publish timestamps.
    "Next-business-day" is an assumption of exactly the class the XAU freeze
    already records as `ASSUMED_NEXT_BUSINESS_DAY / NOT_MEASURED`.
  - **FRED H.10 / ECB publication times: STATED, not byte-evidenced.** Our
    raw files carry observation dates only. "Same-day, pre-close
    publication" is publisher documentation, not a measured property.
  - **Measured channel serving lag at retrieval (skeptic finding, now in
    `retrieval_staleness`):** when this session pulled (2026-09-30 ET /
    2026-10-01 UTC), the FRED fredgraph FX series ended **2026-09-25** —
    ≥3 business days stale — while ECB served 2026-09-30 and the FRED
    energy mirrors served 2026-09-29. Single observation, cause not
    analyzed on file (series update cadence vs CDN caching are both
    possible). Consequence: any `LAG_DECLARED_BY_OWNER` for the FRED
    channel must account for this observed serving lag; the stated H.10
    release schedule is a property of the Fed's release, not of the
    fredgraph channel as served.
- Consequently: a PIT label of `PASS` for these legs is honest **only** if
  the successor protocol's observables have availability that is actually
  evidenced — i.e. the owner funds a vintage/publish-timestamp measurement,
  or explicitly declares a stated publication time as
  `LAG_DECLARED_BY_OWNER (DECLARED, NOT MEASURED)` and accepts that
  epistemic class. Absent either, the steady-state labels are
  **`MEASURED_BASIS + LAG_NOT_MEASURED`**, or `+ LAG_DECLARED_BY_OWNER`
  after a declaration. Fixing time (noon ET / 16:00 CET) is not publication
  time, and neither is evidence about IBKR's own bar availability.

### D-1d. Independence of the three FX sources (what is evidenced vs stated)

- Institutional disjointness is STATED (publisher documentation): H.10 is
  the Federal Reserve Bank of New York's dealer-rate collection; eurofxref
  is the Eurosystem 16:00 CET fixing; IBKR IDEALPRO is a venue book. No
  shared compilation chain between any two is evidenced on file; strong-form
  independence (no common upstream feed) cannot be proven from bytes and is
  not claimed.
- Byte-evidenced distinctness, both directions:
  1. ECB-vs-FRED values differ on **100% of 1475 common dates** (nonzero on
     1475/1475; `archive_value_distinctness` in XCHECK_REPORT.json) — they
     are not the same numbers being republished.
  2. Publication calendars differ, with the full non-overlap date lists
     enumerated on file (`calendar_non_overlap`): ECB publishes **62
     in-window dates** FRED lacks, FRED publishes **19 dates** ECB lacks.
     The enumerated dates are consistent on spot-check with US-federal vs
     TARGET holiday calendars (e.g. 2020-11-26 Thanksgiving and 2020-11-11
     Veterans Day ECB-only; 2021-04-02 Good Friday and 2022-04-18 Easter
     Monday FRED-only). An exhaustive day-by-day holiday classification was
     NOT performed — the counts and lists are the on-file evidence, not the
     "exactly national-holiday sets" characterization.
- Contrast (for calibration): the energy pair EIA/FRED is the degenerate
  case — values exactly equal at source precision on 1511/1511, 1492/1492,
  1496/1496 aligned dates, max abs diff 0.0 (`mirror_value_equality`) — the
  same numbers through two channels (D-3).

## D-2. Name the independent XAGUSD archive (or declare panel-of-record)

Unchanged from v1 (no overclaim found in review): silver has no reachable
independent spot-level archive from this environment; SLV.US proxy measured
r = 0.9827 is proxy-class only (trust NAV + NYSE close vs London spot).

- **Option A (recommended, zero cost, likely minutes):** browser-download
  Stooq XAGUSD daily CSV (free, no account) into
  `~/.my-quantitative-data/pc12a-7asset-data-unblock-2026-10-01/raw/owner_drop/`;
  say "XAG archive dropped"; this lane's successor re-runs the frozen join
  contract on those bytes. **Honesty note (skeptic finding):** this session
  measured only that SCRIPTED access is challenged by the proof-of-work
  gate; that a normal browser executes the challenge automatically is
  typical for such gates but was NOT TESTED here (no browser was used). If
  the browser path fails, Options B/C remain.
- **Option B:** declare IBKR HMDS the panel-of-record for XAGUSD — under the
  same D-1c availability taxonomy (LAG_NOT_MEASURED unless declared).
- **Option C (weakest):** accept the SLV proxy as the cross-check archive.
- Option D — licensed silver feed — a purchase; not authorized today,
  listed for completeness.

## D-3. Adopt EIA spot dailies as the energy signal-side archive (BRENT, WTI, NATGAS) — independence corrected

What is on file: official-channel daily series (RBRTE Brent, RWTC WTI,
RNGWHHD Henry Hub), span-complete 2020-10-01..2026-09-29, 0 holes >5d,
acquired from the EIA v2 API under the owner key, with the FRED mirror
(`DCOILBRENTEU`/`DCOILWTICO`/`DHHNGSP`) numerically identical.

**Correction of wording (Amendment 1):** the mirror equality is
**shared-source reproduction, not verification**. Measured precisely
(`mirror_value_equality` in XCHECK_REPORT.json): the two channels' values
are exactly equal at source precision on **1511/1511** aligned Brent dates,
**1492/1492** WTI dates and **1496/1496** Henry Hub dates (max abs diff 0.0)
— i.e. both channels serve the same numbers. FRED documents these series as
EIA/Thomson-Reuters-sourced. What the equality proves: retrieval integrity
through two distribution channels. What it does not prove: that the values
are correct — the underlying compilation is single-source (vendor
assessments republished by EIA; stated per publisher documentation, not
byte-evidenced). Independent energy verification remains owner-gated
(ICE/Platts-class = paid; estates blocked from this network).

- **Option A (recommended):** in the successor amendment, admit energy
  signal-side daily inputs from the EIA republication channel,
  manifest-pinned, labeled `SINGLE-SOURCE-COMPILATION,
  DUAL-CHANNEL-RETRIEVAL-CONFIRMED`. NATGAS signal legs (USDJPY-S065,
  USDCAD-S090, EURUSD-S063 Henry-Hub leg) become data-addressable; TTF/AECO
  remain owner-named external sources.
- **Option B:** keep energy fully BLOCKED until a futures-chain source is
  also decided.
- Execution-side futures legs (short WTI, CL1–CL6 curve) stay BLOCKED
  regardless — D-4.

## D-4. Certified roll-chain source + ICE/NYMEX entitlement (futures execution legs)

Unchanged from v1 / `GATE_TABLE_7ASSETS.md`: name the certified chain source
and enable the exchange subscriptions. Owner-only purchases/actions.

## D-5. IBKR Activity/Flex statement export (costs gate, 4 spot/metals at once)

Unchanged from v1 (action P_A): one export to
`~/.my-quantitative-data/ibkr_statement/` covers
NZDUSD/USDCHF/XAUUSD/XAGUSD commission/swap measurement.

## D-6. XAU archive canonical-location pin (gate-table finding F-2)

Unchanged from v1: pin the forex-ng6 staging path (sha `49c2684e…`,
re-verified today) as canonical, or instruct a manifested copy under a
`research/control/` data home. Recommended: pin + copy.

## D-7. Successor cycle registration (the gate everything funnels into)

Unchanged from v1: admitting any corpus row requires a successor plan
amendment registering the daily-clock cohort with trial-ledger accounting.
If you instruct registration, this packet (v2) + GATE_UPDATE (v2) + frozen
manifests are the preregistration inputs; any GO is typed at that cycle's
own gate, not here.

---

### Incident disclosure (read before rotating anything)

**INC-1:** while diagnosing an EIA v2 curl error, the error text echoed the
request URL including the `EIA_API_KEY` value into the local session
transcript (one occurrence, local only, never committed anywhere). Per
security law it is disclosed here. **Recommended: rotate `EIA_API_KEY`** at
your convenience (free key, takes a minute). No other key was echoed;
EODHD/TwelveData URLs are recorded redacted everywhere. (The key value is
intentionally not reproduced in any artifact of this session.)

**ERRATUM-1:** an early pass treated FRED `DEXSZUS` as needing inversion;
byte comparison vs IBKR (0.8286 vs 0.8278 on 2026-09-24) proved it is
already USDCHF convention. Corrected in-session; manifest carries the note;
raw bytes untouched.
