# DATACOST_cohort1_REPORT — ERP1-TRACKA-COHORT-1 data/cost critic lane

- Role: DATA/COST CRITIC (outcome-blind mechanism council, Track A cohort 1)
- Cycle: `ECONOMIC-ROBUSTNESS-PROGRAM-V1` (umbrella, ACTIVE_LIGHT) → child
  draft `plans/DRAFT_ERP1_TRACKA_COHORT_1.md` (binding contract for this
  report; §5 data authority, §6 cost book are this lane's sections to
  validate/harden)
- Measured HEAD at start (root `main`): `69ddc60447d223249319f82b71b21e26ab941203`
- Date: 2026-09-25. READ-ONLY except this report + its handoff JSON.
  No downloads, no backtests, no PnL computation, no scored outcomes read.

## 0. Signed disclosure (outcome-blindness)

This lane read ONLY: the draft plan, `CLAUDE.md`, `HOW_TO_BE_A_LEAD_ENGINEER.md`
(handoff schema section), `research/wayfinder/FAMILY_FAILURES.jsonl` (family
IDs + failure-class labels only; no adjudication numbers reproduced),
`plans/CYCLE_REGISTRY.json` (lifecycle), transport/census/cost-mechanics code
under `EURUSD-RANGEEXP-SCORED-V1/scripts/` (duka_lib.py, build_bars.py,
engine.py, scored_cells.py, and the H1Plane/v2_campaign loader lines that
define spread charging), the census JSON schema of
`EURUSD-RANGEEXP-SCORED-V1/data_local/derived/census.json`, and the EDQ1
license artifacts (`CYCLE_VERDICT.md`,
`owner_packet_source_survey_2026-09-22.md`).

FORBIDDEN files were NOT opened: `research/wayfinder/MAP.md`, `NOTES.md`,
`plans/PLAN_economic_robustness_program_v1.md`, all other `plans/PLAN_*`,
and the outcome namespaces of `EURUSD-OPEN-SEARCH-V1/V2`,
`EURUSD-RANGEEXP-SCORED-V1` (outcomes/), `FX-MAJORS-SEARCH-V1`,
`FX-RANGEFADE-2M-SHADOW-V1`, `PROSPECTIVE-SHADOW-V1`. No PnL, PF, win-rate,
trade-count, journal, dashboard or adjudication number appears in this
report. All numbers below are DATA/COST facts (file counts, spread-quantile
census values, coverage gates, sizing estimates).

---

## 1. Source/cost table for the cohort — validate + harden of draft §5/§6

### 1.1 Per pair-class: measured / declared / unmeasurable

| Pair class | MEASURED (sha-pinned) | DECLARED (no number permitted) | UNMEASURABLE on this corpus |
|---|---|---|---|
| EURUSD (ancestry pair; fixture + reference-curve use ONLY, never scored as evidence — draft §3.3) | M1 bid/ask day-file corpus 2021-01..2026-06; census `BUILD_PASS` (gates: midweek tradable share 0.98814 > 0.90; non-positive-spread minutes = 0 < 1%; 130,911 valid 15m bars > 100k); session spread curve p50 0.3 pips overall; rollover 21–22 p50 0.9 / p99 7.8 pips; Sunday-open 21–22 p50 3.0 pips | fee/commission buffer; slippage beyond spread; adverse selection (class: unmeasurable) | fill quality, queue position, depth, pick-off |
| GBPUSD, USDJPY (ancestry pairs; same restrictions) | same window, 4,014 files/pair, 0 missing; spread p50 0.8 / 0.5 pips; USDJPY 1e-3 price-scale probe-proven (never assume pip scale) | same | same |
| NEW pairs (≤2, Task-1 outcome-free surfaces) | NOTHING yet — entire column is `NOT_RUN` until the §2 data gate passes per pair | same | same |
| ALL classes | — | **fee buffer treatment (hardened):** commission/commercial markup is unmeasured program-wide; it is listed VERBATIM as a `DECLARED_UNMEASURED` line item in every cost table, carries no number, is never substituted or netted into any headline figure, and F-5 (cost-survivability ceiling) must be computed at the ×2.0-stressed measured cost so the ceiling is conservative w.r.t. the unmeasured component | swap points (structurally zeroed by fixture, not measured — see §1.3) |

Draft §5 table validated as stated; the three ancestry pairs' corpora are
real, sha-pinned and censused (schema and gate values verified in
`census.json`; manifest sha recorded inside it). No correction needed to the
pair/window/file-count facts.

### 1.2 Per-session spread curve spec (hardened)

The measured convention (validated against `build_bars.py` + the persisted
`census.json`) is binding for every new-pair census:

- **Buckets (fixed-UTC, from 15m bar-open spreads, pooled over the full
  window):** `asia_00_07`, `london_07_12`, `ny_overlap_12_16`,
  `ny_late_16_21`, `rollover_21_22`, `late_22_24`, plus special cells
  `friday_20_23_open` (weekend close) and `sunday_open_21_22` (weekend-open).
  This set covers the draft's Asia/London/NY/rollover/weekend-open list.
- **Quantiles persisted per bucket: exactly {p50, p75, p90, p95, p99}** in
  pips (3-decimal rounding as implemented), plus `overall_open`.
- **Granularity:** the AUTHORITY artifact is the per-pair `census.json`
  (bucket × quantile table + gates + `data_manifest.m1_manifest_sha256`).
  The EVENT-TIME artifact is the per-bar spread column on the execution
  plane: 15m bars carry `s_open`/`s_close`; the H1 plane derives
  `s_open = a_o − b_o`, `s_close = a_c − b_c` per H1 bar
  (`v2_lib.py:27-28`). Both are persisted per bar — the curve is never a
  substitute for the bar.

**HARDENING (three defects found in the existing builder, mandatory for the
new-pair port):**

1. **Persist per-bucket counts.** The current builder silently drops a
   session bucket below 100 samples (50 for the Friday/Sunday cells). A
   dropped bucket must instead be persisted as explicit `null` PLUS a
   `LOW_SAMPLE_BUCKET` gate flag — a silently missing rollover cell would
   hide exactly the regime where spreads are 3–10× normal.
2. **Persist close-spread quantiles too.** The census stores open-spread
   quantiles only, while the executor's exit charge uses the exit bar's
   close spread. Add `by_session_close` (same quantiles) to the census.
3. **Charging semantics stated precisely (corrects a draft ambiguity).**
   Draft §6.3 says the executor "charges the measured session/rollover
   spread curve at event time". As implemented — and as the binding spec —
   the executor charges the **fill bar's own measured spread** (`s_open` at
   entry/reversal bar open, `s_close` at exit bar close; day-close force-flat
   exits use the day-close bar's close spread) times k ∈ {1.0, 1.5, 2.0}
   (`engine.py` fill law: buy at `b_o + k·s_o`, sell at `a_o − k·s_o`; one
   spread crossing per side, round trip = entry + exit crossing). The
   session curve is the PERSISTED AUTHORITY used for: (i) per-regime stress
   floors and the frozen ×2.0 stress book, (ii) the F-5 cost-survivability
   ceiling, (iii) the §9.4 seam-band constant (median per-session spread
   cost × 10 round trips, logged at freeze with the actual number), (iv)
   the F-4 per-session decomposition tables. A reconcile test is REQUIRED:
   per-bar spread medians bucketed per session must equal the census p50
   within rounding (census-vs-executor agreement, both directions).

**Stress:** frozen pre-outcome at per-regime median ×2.0; **both ×1.5 and
×2.0 reported everywhere** (draft §6, umbrella §5.14) — matches the engine's
k set {1.0, 1.5, 2.0}. The ×1.0 tier is the measured spread itself.

### 1.3 Structural-zero financing — CONFIRMED, test design tightened

The draft's requirement (condition 2: flat-by-20:00 UTC and weekend-flat as
executor FIXTURES, not comments) is confirmed and is already materially
true in the code lineage: the H1 plane's `fill_ok = tradable & (hour ≤ 18)`
makes the 19:00 H1 bar the day-close (flat at its close, i.e. before
20:00 UTC), and no position can survive it by construction. The engine
variant note: the older 15m fixture flattens at the 21:00 rollover; the
cohort must pin ONE force-flat semantic — the draft §4.1 H1 law (no fills
on/after the 19:00 bar, flat before 20:00 UTC) — in its own fixture suite
and must not silently inherit the 15m variant's constant.

Required unit fixtures (fail the build, not a warning):

1. **No-position-after-flat assertion:** run the executor over the full
   plane; assert zero open positions at every bar with hour ≥ 20 UTC and
   across the Friday-close → Sunday-open boundary (also on synthetic
   DST-shifted calendars).
2. **Structural financing:** the financing/swap accrual code path either
   does not exist or raises if invoked; there is no "zero-rate" constant
   to accidentally flip. (Structural zero, not a numeric zero.)
3. **Mutation probe:** a synthetic day with a bar at 20:05 UTC must
   produce NO fill and NO carried position.
4. **Avoided-cost documentation, not credit:** because the law is flat
   before 20:00, the executor structurally never pays the `rollover_21_22`
   or `sunday_open_21_22` buckets (measured p50 0.9 and 3.0 pips on
   EURUSD). The census must still be built for all buckets — it is the
   evidence that the avoidance is real — but no arm may claim the avoided
   rollover spread as "saved cost" in any headline; it is a property of
   the law, reported once in the cost book.

### 1.4 Taker-fill cost model (restated verbatim-tight)

Entry/exit at the opposite quote + fill-bar measured spread × k; slippage
beyond spread = `DECLARED_UNMEASURED`, covered by stress only; no
assumed-fee substitution in any headline number (owner instruction
2026-09-25, binding). No marks-based or mid-price accounting anywhere in
the book.

---

## 2. New-pair data-gate spec (pre-outcome probe checklist)

Ordered gate; a pair advances to any outcome-bearing work ONLY after every
item is PASS and sha-recorded. Fail-closed everywhere; `NOT_RUN` is never
inferred `PASS`.

1. **Pre-gate (before bytes):** pair slate frozen at GO-1; registry +
   family-ledger check that the pair was never searched in any program
   cycle (outcome-free surface, draft §5.2) and its 2026-01..2026-06
   holdout is untouched.
2. **bi5 probe (bounded, ~7–14 days straddling a DST transition + a
   rollover):** decode the 24-byte M1 candle layout (`>5if`,
   `sec_offset_in_day` epoch-UTC semantics) against tick ground truth
   (20-byte `>5i` hour files); OHLC invariants + candle-vs-tick cross-check
   must pass or the caller exits fail-closed (the `len % 20` vs `len % 24`
   trap is documented in `duka_lib.py` — the port must keep the 24-byte
   invariant assertion).
3. **Pip-scale + level-band probe (never assumed):** derive the integer
   price scale from probe ticks (EURUSD 1e-5 points; JPY pairs 1e-3
   precedent) and the per-pair tradability band from observed price levels.
   **BLOCKING DEFECT TO FIX IN THE PORT:** `build_bars.py` hard-codes
   `PIP = 1e-4`, `PRICE_SCALE = 1e5` and the EURUSD price band
   `0.80 < bid < 1.35`; `engine.py` hard-codes `PIP = 1e4`. Copying these
   verbatim fail-closes on any JPY or bloc-diverse pair. The cohort engine
   must parametrize scale/pip/band per pair, proven by the probe, and add a
   fixture per pair-scale (USDJPY precedent is the template).
4. **Bounded full download:** 2021-01..2026-06 M1 BID+ASK day files per
   pair (4,014 files/pair = 2,007 calendar days × 2 sides — matches the
   ancestry precedent and the census `days = 2007`), keep-alive polite
   fetcher (429/5xx exponential backoff, 0.15–0.35 s pacing), bytes hashed
   sha256 into `m1_manifest.json` committed; raw bytes machine-local,
   gitignored; verify-on-read fail-closed on sha mismatch.
5. **Census build + gates** (§1.2 hardened schema): midweek tradable-minute
   share > 0.90; non-positive-spread minutes ≈ 0 (< 1% gate); valid 15m
   bars > 100k; `days_short_records` = 0 or explicitly enumerated;
   duplicate timestamps = 0 fail-closed.
6. **Gap census:** enumerated micro-gaps (EDQ1 probe-window precedent:
   99.542% minute coverage, 44 gaps of 1–3 min); weekend boundaries
   measured (Friday close → Sunday open, DST shift visible); fail-closed on
   coverage below ancestry standards.
7. **Session spread curve build** per §1.2 (both open and close quantiles,
   counts persisted, no silent drops) — this census IS the pair's cost
   authority artifact.
8. **DST/rollover calendar fixtures:** rollover bucket populated (count >
   0 asserted), Sunday-open cell present, DST-shift dates in the pair's
   session geography produce no force-flat or bucketing break.
9. **Engine parity + scale fixtures:** pip-parametrized engine passes the
   per-pair scale fixture; parity self-test against the frozen law on an
   ancestry pair is FIXTURE-only (never evidence).
10. **Gate verdict + sha chain:** `BUILD_PASS`/`BUILD_FAIL`; record manifest
    sha, census sha, code-freeze sha — all BEFORE any PnL-bearing
    computation anywhere in the cycle (ordering law).

**Download sizing estimate (anchored to the 4,014-files/pair precedent and
the ~11 KB/file bi5 observation in `duka_lib.py`):**

- M1 day files: 4,014 × ~11 KB ≈ **~44 MB compressed per pair** (both
  sides); ~139 MB decoded per pair.
- Tick ground-truth probe: ~264–528 hour files per pair (11 days × 24 h ×
  2 sides) ≈ **~10–30 MB per pair**.
- Census/derived parquet per pair: ≈ **~10–15 MB** machine-local.
- Two new pairs total: **≈ 110–150 MB download**, machine-local storage
  well under 1 GB. Wall-clock at the existing keep-alive pacing ≈ **35–70
  min per pair** of download — a bounded heavy job.

**Heavy-lock etiquette:** the download is a heavy job — global machine lock
via `researchctl.py locks inspect`; `NOT_RUN_RESOURCE_CONFLICT` if held;
never kill a foreign worker; declare the bounded window in the dispatch;
yield (pause + heartbeat + resume) rather than hold if the window exceeds
the declared bound.

---

## 3. Independent-source posture — BLOCKED bounding CONFIRMED

EDQ1 stands: `BLOCKED_SOURCE_LICENSE` — every technical gate of the probe
passed (schema, UTC timestamps, 99.542% coverage, bid/ask fields,
multi-year), the blocker is license only. Twelve Data is
internal-research-clear but has NO bid/ask → reconciliation-only, and even
a passing Twelve-Data-only coverage story ends at `BLOCKED_COST_AUTHORITY`
by EDQ1's own law. Track A children inherit the owner-directive paper-tier
posture and do not re-litigate it in-cycle (draft §5.1). Confirmed: **no
authorized independent historical bid/ask source exists today; the cost
authority of this cohort is single-vendor (Dukascopy) by necessity, and
that limitation is permanent for this cycle regardless of results.**

**Reconciliation-only panel design (Task-1b, what MAY run without owner
action):**

- Source: Twelve Data (or second-vendor closes) H1 close series per new
  pair, pulled only AFTER the primary panel's data gate passes.
- **Pre-registered tolerance method (frozen BEFORE vendor bytes are
  fetched):** per matched H1 close, the absolute difference |Δ| in pips is
  reported as a full distribution (median / p75 / p90 / p95 / max) against
  a tolerance band derived ONLY from the primary panel's measured spread
  scale (e.g. a fixed multiple of the pair's overall spread p50), fixed in
  the data-gate record. No calibration of one vendor to the other; no
  forcing agreement; no post-hoc band adjustment.
- **Verdicts it MAY support:** exactly one — a data-integrity statement:
  "primary panel level-consistency: CONSISTENT / INCONSISTENT with
  {vendor, frozen tolerance, distribution}" per pair. It may flag a
  suspect primary panel and thereby BLOCK (fail-closed).
- **Verdicts it may NOT support:** any cost-authority claim (no bid/ask →
  no spread measurement of any kind); any execution/fill-quality claim;
  closure of the marks-vs-fills seam (condition 5 — the TrueFX-indicative
  vs Dukascopy-bar seam stays disclosed, not resolved); any upgrade of
  Task-1b to a replication arm; any rescue of a failed primary coverage
  gate.

**Exact owner unblock actions that would upgrade Task-1b** (from the EDQ1
decision packet; owner picks, agent signup prohibited):

1. **TrueFX (Integral):** owner personally registers the free account,
   captures the verbatim license text at the historical-downloads page and
   pastes it into the cycle; if it permits storage for internal research +
   programmatic monthly-zip retrieval → new PRIMARY candidate; else discard
   at zero cost.
2. **Dukascopy written consent:** owner emails Dukascopy Bank SA for
   express written consent to automated bi5 retrieval for internal
   non-commercial research + derived-dataset retention; the consent letter
   becomes license authority; silence/decline → formally abandon.
3. **OANDA v20 practice:** owner personally registers the free practice
   account and accepts its terms; then read OANDA's API Terms (Legal Hub)
   for storage permission and run an empirical M1 depth probe. Runner-up:
   Polygon/Massive BBO (tier depth + storage terms to be read on an
   unrestricted network).

Upgrade mechanics: any cleared path requires a successor 7–14-day probe
FIRST, then a plan amendment + new GO before Task-1b runs as a full
independent-source replication arm; conclusion tiers relabelled in every
artifact.

---

## 4. Adverse-fill honesty block (mandatory)

**What M1 bid/ask corpora CAN say:** quoted spread at bar open/close
(measured, per session); tradability; coverage and gap structure; the cost
of a marketable taker fill AT the bar's opposite quote.

**What they CANNOT say (declared unmeasurable, in every verdict):** queue
position; order-book depth beyond the top-of-book implied by the quote;
pick-off/adverse selection at fill moments; partial fills, requotes,
last-look, rejects; slippage distribution beyond the spread; increment /
minimum-ticket constraints; commission (venue-specific, unmeasured).

**Wording ban list (binding for every artifact of this cycle):**

- NEVER "earning / capturing the market maker's spread" for taker fills —
  **the strategy PAYS the spread** on every entry and every exit.
- NEVER any maker-capture, rebate, or queue-rent claim — maker-capture
  requires queue-position evidence this corpus cannot produce.
- NEVER "fill at mid" / "zero slippage" — fills are at the opposite quote;
  slippage beyond spread is declared-unmeasured, stress-covered.
- NEVER "no transaction costs" — the honest statement is "no financing
  (structural fixture) and no measured commission; measured spread × k is
  charged".
- NEVER treat non-positive-spread minutes as opportunity — they are a data
  red flag gated to ≈ 0.
- NEVER "live-identical", "real-world fills", or any live-readiness claim
  (draft §1.2).

**Mandatory class label in every verdict:** `FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK;
cost model = taker at opposite quote + measured per-bar spread × k;
adverse selection stress-covered, never measured`.

---

## 5. Feasibility ceilings per arm class

| Arm class (per draft §7.2) | Minimum data | Cost components needed | Honestly costable in the paper-tier book? |
|---|---|---|---|
| R-ANCHOR (Task-1 replication anchor, per pair) | full gated corpus + census | measured per-bar spread ×k, both k=1.5/2.0 reported; F-5 ceiling from ×2.0 curve | YES |
| R-ORIG (diagnostic neighbour / PIT-seam probe) | identical to anchor | identical | YES (never selectable; seam band logged at freeze) |
| R-NEIGH (quantile support neighbour) | identical | identical | YES |
| Causal control (clock-only shadow) | identical plane | identical | YES — same taker cost law |
| Inverted control | identical | identical | YES |
| Baseline set: FLAT + day-session SHORT_ALWAYS + LONG_ALWAYS | identical | identical; day-session arms confine fills to day buckets, force-flat exit charged at day-close bar close spread | YES (these ARE the short-USD-beta controls; per-pair beta direction named by council) |
| Task-2 new mechanisms (≤2) | identical per home pair | identical | **CONDITIONAL — see flag below** |

- **Unfundable-arm flag (kill-first rule):** any Task-2 mechanism whose
  entry/exit geometry needs sub-M1 event timing, queue/depth conditions,
  maker fills, or tick-level fill sequencing is **NOT honestly costable on
  M1 bid/ask** and must be vetoed at proposal review (pre-PnL, falsifier
  class), because its cost book would contain an unmeasurable term larger
  than its claimed premium. M1-plane mechanisms are all costable.
- **Expected per-pair spread-curve build cost:** one census pass =
  decode 4,014 day files + bucket quantiles ≈ minutes of CPU per pair
  (the existing EURUSD build produced the full census in one pass);
  compute is NOT the constraint — the license-bounded download and the
  gate sequence are.
- **Pair count ceiling:** Task-1 = 2 new pairs × 6 arm classes = 12 cells;
  Task-2 = ≤2 mechanisms × 6 arms × 1 home pair = 12 cells; 24-cell cap
  observed in the ledger with holdout looks ledgered, not extra cells.

---

## 6. Five binding conditions checklist (applied verbatim)

1. **Verdict class bounded — CONFIRMED, no change.** Every output is at
   most `CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION`; no promotion toward
   real-money inference without `PASS_BROKER_COST_AUTHORITY` (FOREX-NG8
   closed). This is reinforced by §3 above: the single-vendor,
   license-disclosed cost authority makes the paper tier the structural
   ceiling, not just a label.
2. **Structural-zero financing enforced, not assumed — CONFIRMED,
   TIGHTENED.** Pin ONE force-flat semantic (draft §4.1 H1 law: no fills
   on/after the 19:00 bar, flat before 20:00 UTC — do not silently inherit
   the 15m variant's 21:00 constant); the four unit fixtures of §1.3
   (no-position-after-flat incl. synthetic DST calendars, structural
   financing path, 20:05 mutation probe, avoided-cost documentation) are
   the enforcement; a fixture failure fails the build pre-PnL.
3. **Per-session spread, not global p50 — CONFIRMED, TIGHTENED.** Add the
   §1.2 hardenings: persist bucket counts (no silent drops), close-spread
   quantiles, and the census-vs-executor reconcile test; state that
   event-time charging is the fill bar's own measured spread ×k (stronger
   than median substitution), with the curve as floor/ceiling/seam-band
   authority. Stress = per-regime median ×2.0 frozen pre-outcome; ×1.5 and
   ×2.0 both reported.
4. **Adverse selection declared unmeasurable — CONFIRMED, TIGHTENED.** The
   draft's taker/pays-the-spread sentence is retained verbatim and extended
   by the §4 wording ban list + the mandatory `FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK`
   class label in every verdict; maker-capture claims are structurally
   impossible without queue-position evidence this cycle cannot produce.
5. **Marks-vs-fills seam disclosed — CONFIRMED, TIGHTENED.** Name both
   sides explicitly: live/prospective marks would be TrueFX-indicative
   quotes; all historical evidence is Dukascopy-derived bars. The
   reconciliation panel (§3) cannot close this seam (mid closes only, no
   bid/ask); every live-mark comparison repeats the disclosure.

---

## 7. Kill-first honesty (strongest data/cost reasons for paper-tier-only or not opening)

1. **License:** the entire primary corpus rests on an owner-directive,
   risk-disclosed posture over an unresolved TCU (`BLOCKED_SOURCE_LICENSE`).
   No result this cycle produces can launder the bytes into a licensed
   dataset; paper-tier is the ceiling regardless of every gate passing.
2. **Commission unmeasured program-wide:** every net number omits a
   declared-unmeasured fee component that is bounded only by stress, never
   measured. Any conclusion robust only at ×1.0 is unfundable by this book.
3. **Single-vendor cost authority:** Dukascopy is the only bid/ask source;
   a vendor-level quote convention or spread-regime difference on a new
   pair is invisible until that pair's own census is built, and no
   independent cost replication exists (Twelve Data cannot provide it).
   The reconciliation panel bounds level drift only.
4. **Fill quality:** M1 corpora cannot see pick-off or queue effects; an
   edge concentrated at bar-edge fills (exactly where range-break fades
   execute) carries an unmeasurable adverse-selection term. Arms whose
   gross premium per round trip does not clear ~2× the stressed
   round-trip spread of their session mix die at F-5 before scoring
   (VOL-NG1-precedent class; the ceiling test is pre-PnL by the ordering
   law).
5. **Coverage fail-closed:** a new pair failing the 0.90 tradable-minute
   gate, the ≈0 non-positive-spread gate, or the gap census closes
   `BLOCKED_*` honestly under TIME-STOP — no assumed data, no
   interpolation, no substituted vendor. `REJECT_ALL`/`BLOCKED_*` are valid
   terminal states and are cheaper than an unfounded scored cell.

---

## 8. Verdict summary of this lane

- Draft §5 source table: **VALIDATED** (facts match the sha-pinned census
  evidence). Draft §6 cost book: **VALIDATED WITH THREE HARDENINGS**
  (charging semantics precision, census completeness: counts + close
  quantiles + reconcile test, structural-zero fixture pinning + §4 wording
  bans + §5 unfundable-arm veto).
- New-pair data gate: fully specified above; blocking defect identified in
  the hard-coded scale/pip/price-band constants of the existing
  builder/engine — parametrization with per-pair fixtures is mandatory
  before any new-pair build.
- Independent-source: BLOCKED bounding confirmed; reconciliation panel
  may support one verdict class only; the three owner unblock paths are
  restated with exact actions.
- The cohort is honest **only** as a paper-tier program. That bound is a
  feature of the evidence, not a limitation of ambition.

*Signed: DATA/COST CRITIC lane, outcome-blind council, 2026-09-25. Handoff:
`HANDOFF_tracka1_datacost.json` (same directory).*
