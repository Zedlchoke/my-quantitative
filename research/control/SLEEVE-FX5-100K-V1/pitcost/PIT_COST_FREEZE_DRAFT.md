# PIT_COST_FREEZE_DRAFT — SLEEVE-FX5-100K-V1 (Lane PC, pre-GO)

Program: **SLEEVE-FX5-100K-V1** (sleeve-only, 5 FX pairs of the 12-asset
universe; the other 7 assets stay FLAT by prior DATA_COST_MATRIX — no
substitute data may be sought for them). Cycle id: `SLEEVE-FX5-100K-V1-PREGO`.
Lane: **PC — PIT + COST AUTHORITY**. Status: **DRAFT proposed freeze** — the
owner freezes; this lane has no freeze authority. Session 2026-09-29:
READ-ONLY on all inputs, no git commands, no backtests, no signals, no orders,
0 workers. Owner's dirty tree preserved untouched.

Companion file: `COST_AUTHORITY_TABLE.md` (component x pair authority matrix).
Handoff: `../handoffs/PC_pit_cost.json`.

Standing law for this document: **measured beats stated; missing authority =
BLOCKED/NOT_RUN, never an optimistic assumption.** Owner directive 2026-09-29
(verbatim): the IBKR London-fix measurement is ONE DAY on a paper venue —
NOT edge evidence and NOT sufficient cost authority.

---

## 0. Inputs read (authority for everything below)

1. `.worktrees/portfolio-router-12assets-100k-v1/integration/research/pr12a100k/data_manifest_fx.json`
   (schema `pr12a100k.data_manifest_fx@1`, measured_at 2026-09-28) — the 5
   panels, digests, ranges, gap censuses, timezone evidence.
2. `.../pr12a100k/COVERAGE_NOTE.md` — per-panel measured ranges, 286-week
   5-pair intersection, gap character, DST verification, H1-vs-M1 ceiling.
3. `.../pr12a100k/loaders.py` — stamp conventions (close-time UTC), ANC
   open->close +1h shift, fail-closed loader API, resampler DST guard.
4. `research/control/PORTFOLIO-ROUTER-12ASSETS-100K-V1/cost/COST_ACCOUNTING_SPEC.md`
   — declared pessimistic bands U1–U18, per-fill cost kernel, swap/rollover
   rules (§1.1, §2.7, §3.2, §4).
5. `research/control/DATA-FOUNDATION-SIXSOURCE-V1/FINAL_REPORT.md` — six-source
   table (source-1 FX row), pilot budget, owner statement path.
6. `research/control/DATA-FOUNDATION-SIXSOURCE-V1/ibkr_fx/sessions_index.jsonl`
   + `sanitized_fix_window_20260928T145053Z.json` +
   `sanitized_rollover_window_20260928T211921Z.json` — the three new dirty
   OWNER/PROGRAM artifacts (read-only, unmodified; classified §4).
7. `research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/broker_cost_probe_FX_majors_2026-09/`
   — `VERDICT_session2.md` (V3 component table, stress 2.0 frozen),
   `EVIDENCE_sanitized_2026-09-26.json` (minTick declarations, empty weekend
   grid), `ERRATUM_2026-09-28_sixsource.md` (E1/E2).
8. Own bounded measurement, this lane, 2026-09-29 (method in §1/§3 and
   Appendix A; script kept out of the repo per write scope): spread
   distributions decoded directly from the staged panels. NOT a backtest —
   no signals, no PnL, no ordering.

---

## 1. Per-pair PIT rules for the sleeve cycle (deliverable a)

### 1.1 Panel identity (from inputs 1–3; nothing re-derived)

| pair | panel (read-only) | granularity | measured range (UTC, loader space) | signal ceiling |
|---|---|---|---|---|
| EURUSD | fx-rangefade-2m-shadow-v1 M1 .bi5 bid+ask, 2x2092 files, corpus digests `894ad9d6…`/`6ff596ec…` | M1 | 2021-01-03 22:00 → 2026-09-23 23:59 | **M1** (or coarser resamples) |
| GBPUSD | fx-majors-search-v1 M1 .bi5 bid+ask, 2x2092 files, `7894da0e…`/`ce87aded…` | M1 | 2021-01-03 22:00 → 2026-09-23 23:59 | **M1** |
| USDJPY | fx-majors-search-v1 M1 .bi5 bid+ask, 2x2092 files, `5821b22d…`/`e5f1f3de…` | M1 | 2021-01-03 22:00 → 2026-09-23 23:59 | **M1** |
| USDCAD | erp1-tracka-cohort-1 (repro_twin) bars1h_ANC_USDCAD.parquet, 30,386 rows, sha256 `335a6e2a…` | H1 | first/last ts 2021-01-03 23:00 → 2026-06-30 23:00 (open-stamps; close-stamped: 2021-01-04 00:00 → 2026-07-01 00:00) | **H1 only** |
| AUDUSD | bars1h_ANC_AUDUSD.parquet, 30,420 rows, sha256 `4e0ca174…` | H1 | → 2026-06-30 20:00 (close-stamped 2026-06-30 21:00) | **H1 only** |

### 1.2 PIT laws (binding for every lane of this cycle)

- **R1 — Stamp law.** All bar stamps are **close time, UTC**. A bar labeled T
  aggregates (T−rule, T] (`data_manifest_fx.json` `loader_layer.stamp_convention`;
  `loaders.py` module docstring). M1 minute record at `sec` covers [sec,
  sec+60) and is stamped sec+60. ANC source is open-stamped; `load_fx_h1`
  shifts +1h — **all downstream code must use the loader, never the raw
  parquet stamps.**
- **R2 — Completed bars only.** A signal evaluated at decision stamp T may
  read only bars stamped <= T. At T every bar stamped <= T is complete by
  construction — no partial-bar reads, no exceptions for "almost closed" bars.
- **R3 — Decision→fill ordering law (no same-bar signal+fill).** The signal
  computed on bars completed at t is executed at the **open of the NEXT bar**:
  buys at that bar's `ask_o`, sells at its `bid_o`, using the side actually
  quoted in the panel (never mid, never the signal bar's price). M1 pairs:
  next minute bar. H1 pairs: next **present** hourly bar — ANC panels are
  tradable-hours-only, so absent hours are real: the fill defers to the next
  present bar's open and the deferral is recorded as a first-class row
  (`fill_deferred: bars_skipped, hours_deferred`). Measured deferral
  frequency at the proposed Friday 20:00 UTC stamp (this lane, 286 sleeve
  Fridays): **USDCAD 39/286 (13.6%), AUDUSD 87/286 (30.4%)** of Fridays lack
  the 20:00-open bar, in which case the next present bar is the Sunday reopen
  — priced at the measured reopen spread (§3.4), not at Friday's.
- **R4 — Common decision stamp (validated default: Friday 20:00 UTC).**
  Winter Fridays' last completed bar closes 22:00 UTC, summer Fridays' 21:00
  (seasonal boundary test, `COVERAGE_NOTE.md`; re-measured per-month on all
  3 M1 panels this lane: winter months max Friday close 22.00, summer 21.00).
  A Friday **20:00 UTC** stamp is therefore <= the last completed bar in every
  season for all 5 pairs. Verified this lane: the minute bar closing exactly
  20:00 Friday exists and is tradable **286/286** sleeve Fridays on EURUSD,
  GBPUSD, USDJPY (and the [20:00,20:01) fill bar likewise 286/286); the ANC
  Friday 19:00-open bar (= bar closing 20:00) exists **USDCAD 276/286,
  AUDUSD 262/286** (holiday-shortened Fridays fall back to the latest
  completed bar <= stamp — the absence itself is information, not a gap to
  fill). The final stamp schedule is the signal lane's authority; this freeze
  fixes the LAW (R2+R3) and validates 20:00-Friday as the default that the
  calendar in §2 assumes.
- **R5 — Panel-truncation replay fixture (ERP-tracka law).** Signals must be
  recomputable from truncated panels: for every decision timestamp T in the
  fixture set (all 8 fold-start and fold-end stamps of §2, the OOS boundary,
  plus 20 uniformly spaced in-fold stamps), re-load each panel cut to bars
  stamped <= T and re-run the signal computation; outputs must be
  **byte-identical** to the run-time (incremental) computation. Any mismatch
  = the fold is NOT_RUN until fixed. The fixture is part of fold freeze
  evidence, not optional hygiene.
- **R6 — M1-vs-H1 ceiling.** EURUSD/GBPUSD/USDJPY: features may use M1 or
  coarser (H1/D1 via `resample_bars`). USDCAD/AUDUSD: **H1 ceiling only** —
  raw M1 for these pairs is not on disk (ERP1 worktree retained derived H1
  planes only, `COVERAGE_NOTE.md` §H1-vs-M1), and the ancestor convention
  applies: `bid_h`/`bid_l` are max/min of M1 **closes**, not intrabar
  extremes (range signals biased low vs the M1 pairs), and there is no ask
  H/L (spread dynamics at bar endpoints only). Cross-pair feature parity is
  achievable only at H1-or-coarser; a family that requires M1 parity across
  all 5 pairs is BLOCKED_DATA on USDCAD/AUDUSD by construction.
- **R7 — H1 end cap (folds must not extend past 2026-06-30).** The binding
  constraint is the ANC pair that ends first: AUDUSD last close-stamped bar
  2026-06-30 21:00; USDCAD 2026-07-01 00:00. **No fold, no OOS computation,
  no evaluation may reference any bar after 2026-06-30.** The last common
  Friday decision stamp is **2026-06-26**. The M1-only 12-week extension (to
  2026-09-23) is FORBIDDEN in this sleeve (5-pair parity law — using it for
  3 pairs would smuggle in an unpaired regime).
- **R8 — DST handling: inherited from loaders, unchanged.** Source stamps are
  UTC, verified two ways (`COVERAGE_NOTE.md` §Timezone): (i) DST switch days
  2021-03-14 / 2021-11-07 have 1440 records spanning sec 0..86340 (a
  local-time feed would show 1380/1500); (ii) the NY close shifts inside the
  files across seasons (21:59 vs 20:59 last tradable Friday minute). The
  resampler's 23/25-bucket DST unit test stays active (guards against a future
  local-time feed). No local-time conversion is permitted anywhere in this
  cycle. ANC absent-bar rule: **absence carries information** — an engine must
  never treat an absent H1 bar as zero return or stale-carry without an
  explicit declared rule.
- **R9 — Weekend/holiday gap character (declared once, from input 1/2).**
  M1 corpora: 0 missing days, 0 short files, weekends are flat zero-volume
  records flagged `tradable=False`; the only zero-tradable weekday in 5.7
  years is 2021-01-01; largest tradable-minute gap 4,321 min (~3 d, New Year
  2024). ANC: 17,711/17,674 hours absent vs full grid in ~2k runs —
  structural (weekends + ~21:00–22:00 rollover hour mostly absent), largest
  gap 75/76 h (holiday weekends). Fold boundaries in §2 are all ordinary
  Fridays; no fold starts or ends inside a declared holiday gap.

---

## 2. Calendar proposal inputs (deliverable b)

### 2.1 Usable window

**2021-01-08 → 2026-06-26, 286 Fridays** (first Friday after the 2021-01-03
22:00 weekly open; last Friday before the 2026-06-30 ANC end cap; count
verified by enumeration this lane: 286, matching COVERAGE_NOTE's 286
Mon-aligned weeks Mon 2021-01-04 … Sun 2026-06-28). Weeks are Mon-aligned and
indexed 1..286 by Friday decision stamp: week k = Friday 2021-01-08 + (k−1)·7 d.

### 2.2 Proposed walk-forward geometry

- **52w warmup** — weeks 1..52 (Fri 2021-01-08 → 2021-12-31); no test
  evaluation before week 53 (Fri 2022-01-07).
- **26w test folds, anchored-expanding train, 1w embargo** — fold k trains on
  weeks 1..(52+26(k−1)−1), embargo week (52+26(k−1)) is excluded from both
  train and test, test = weeks (53+26(k−1))..(78+26(k−1)).
- **Sealed one-time OOS** — final 26 weeks, weeks 261..286, **sealed until
  terminal**: no lane computes anything on these weeks before the terminal
  gate; one look, one direction, no iteration. Folds run only to week 260
  (nothing after 2025-12-29 is touched before terminal).

### 2.3 Fold table (arithmetic checked; every date verified a Friday)

| fold | train weeks | embargo | test weeks | test Fri stamps (UTC) |
|---|---|---|---|---|
| F1 | 1–51 | 52 | 53–78 | 2022-01-07 → 2022-07-01 |
| F2 | 1–77 | 78 | 79–104 | 2022-07-08 → 2022-12-30 |
| F3 | 1–103 | 104 | 105–130 | 2023-01-06 → 2023-06-30 |
| F4 | 1–129 | 130 | 131–156 | 2023-07-07 → 2023-12-29 |
| F5 | 1–155 | 156 | 157–182 | 2024-01-05 → 2024-06-28 |
| F6 | 1–181 | 182 | 183–208 | 2024-07-05 → 2024-12-27 |
| F7 | 1–207 | 208 | 209–234 | 2025-01-03 → 2025-06-27 |
| F8 | 1–233 | 234 | 235–260 | 2025-07-04 → 2025-12-26 |
| **OOS (sealed)** | 1–260 (all folds) | — | 261–286 | 2026-01-02 → 2026-06-26 |

**Resulting fold count: exactly 8** (weeks 53–260 = 208 = 8 × 26). Check:
52 warmup + 208 fold-test + 26 sealed OOS = 286. ✓

### 2.4 Arithmetic correction to the dispatch recommendation (honest note)

The dispatch suggested "final 26 weeks 2026-01-05 → 2026-06-26". Those two
constraints are **mutually exclusive**: 2026-01-05 (Mon) → 2026-06-26 (Fri)
is **25** Mon-aligned weeks (25 Friday stamps, 2026-01-09..2026-06-26),
whereas a full 26 weeks ending 2026-06-26 starts **Mon 2025-12-29** (Friday
stamps 2026-01-02..2026-06-26). Two clean resolutions:

- **Option A (recommended, adopted in §2.3):** OOS = weeks 261–286, Mon
  2025-12-29 → Fri 2026-06-26 — a full 26 weeks, symmetric with fold width;
  folds end Fri 2025-12-26 and nothing is computed after 2025-12-29 pre-terminal.
- **Option B:** calendar-year-clean start Mon 2026-01-05 — OOS = weeks
  262–286 = **25** weeks, plus one extra embargo week (Mon 2025-12-29..
  2026-01-04) that is exercised by no fold and no OOS computation.

The owner picks; the fold table is identical under both (8 folds, ending
2025-12-26). This freeze drafts Option A because the dispatch's primary
constraint was "26 weeks".

### 2.5 Calendar constraints already wired in

- All fold/OOS stamps are Fridays with decision bars verified present (§1.2
  R4: 286/286 on the M1 pairs; ANC holiday fallbacks covered by R4/R9).
- OOS end 2026-06-26 respects the USDCAD/AUDUSD 2026-06-30 end cap (R7) with
  one full week of margin.
- No fold boundary falls inside the 2021-01-01 zero-tradable day or the
  2024 New Year 4,321-minute gap (both are inside warmup/fold interiors and
  handled by the last-completed-bar rule).

---

## 3. Rollover treated as its own component (deliverable c)

### 3.1 Definition

The **21:00–22:00 UTC roll window** cost is a separate cost component, never
blended into the general spread schedule: `S_roll(pair, weekday)` replaces
`S(pair, bucket)` for any fill whose execution bar lies inside the window.
(Declared event window "rollover 21:00–23:00 UTC" in COST_ACCOUNTING_SPEC
U3 is wider; this freeze MEASURES the 21:00–22:00 core hour and keeps
22:00–23:00 at the declared schedule — measured beats stated where a
measurement exists, declared pessimism where none does.)

### 3.2 Measured basis — M1 pairs (per-minute, from the staged .bi5 bid/ask; this lane, 2026-09-29)

Spread (ask−bid) at minute close, minutes with close stamp in (21:00, 22:00],
pips, full panel 2021-01→2026-09:

| pair | Mon–Thu p50 / p90 | Fri p50 / p90 | (context: all-tradable minutes p50/p90) |
|---|---|---|---|
| EURUSD | 0.6 / 2.7 | 0.5 / 1.1 | 0.3 / 0.6 |
| GBPUSD | 1.4 / 5.8 | 1.2 / 2.3 | 0.9 / 1.4 |
| USDJPY | 1.0 / 4.9 | 0.8 / 1.8 | 0.6 / 1.0 |

Close-hour table (all days in sample) confirms hour 21 is the widest regular
hour: EURUSD 1.4/4.2, GBPUSD 3.1/9.0, USDJPY 2.3/8.3 (p50/p90). Method and
quantization: spreads computed as integer (ask−bid) price quanta = exactly
0.1 pip on all three pairs; percentiles exact from histograms; tradable =
volume>0 both sides; negative/invalid obs excluded (count recorded; 0 on all
three pairs to 4 significant events). Full per-UTC-hour p50/p90 tables for
all five pairs are in Appendix A and supersede COST_ACCOUNTING_SPEC U1's
"one measured bucket, double it elsewhere" rule **for the panel venue only**
(see §5 venue caveat).

### 3.3 Measured basis — H1 pairs (bar-endpoint, from the ANC parquets; this lane)

The 21:00-open weekday bar is **mostly absent** (structural, the ANC
tradable filter): USDCAD 431 of 30,043 weekday rows (1.4%), AUDUSD 320.
When present, s_open p50/p90: USDCAD 1.2 / 2.3 pips; AUDUSD 1.2 / 2.9 pips.
Pricing rule for H1 pairs: a fill inside the roll window (rare — the bar
itself is usually absent) uses `S_roll = max(measured endpoint p90, general
schedule p90)`; the absence itself must be surfaced, not smoothed over.

### 3.4 Sunday reopen (the other structural spread event; measured)

First tradable bar of the week, spread at its open, pips, sleeve window
2021-01-08→2026-06-26: EURUSD p50 5.9 / p90 9.0 (n=284); GBPUSD 13.4 / 23.8
(n=283); USDJPY 11.0 / 22.0 (n=284); USDCAD 5.0 / 9.7 (n=233); AUDUSD 2.8 /
6.3 (n=247). **Any fill that lands at Sunday reopen is charged at these
measured distributions — this includes the H1 Friday-deferral fills of R3.**
Engineering default recommended (signal lane's call): sleeves should avoid
Sunday-reopen entries unless the family declares them; the freeze only prices
them honestly.

### 3.5 Overnight holds — swap/financing (DECLARED, separate from rollover spread)

- Swap accrual clock: **DECLARED U5** — daily boundary 22:00 UTC; positions
  open at the boundary accrue that night (COST_ACCOUNTING_SPEC §2.7).
- Rate: **DECLARED U4** — 1.0 pip/night charged AGAINST the held position in
  both directions, **Wednesday ×3** (spot T+2 weekend-skip convention);
  **UNMEASURED**; pessimistic symmetry rule — no strategy may earn financing
  in the backtest until the owner statement unblocks real two-sided rates.
- **A sleeve whose PROFIT depends on receiving swap is BLOCKED_COST** until
  an owner statement (IBKR Activity/Flex `Interest Accruals` rows) provides
  real two-sided rates. This is a hard verdict, not a label.
- The 1-day paper rollover capture (§4.2) is corroborating single-day
  evidence for the roll-window SPREAD only; it says nothing about swap
  rates, the accrual clock, or Wednesday ×3.

---

## 4. The two new ibkr_fx window files — honest classification (owner artifacts, READ-ONLY)

These three files (sessions_index.jsonl entry + two sanitized windows) landed
2026-09-28 as OWNER/PROGRAM artifacts of DATA-FOUNDATION-SIXSOURCE-V1. This
lane did not create or modify them; raw ndjson stays outside the repo at
`~/.my-quantitative-data/sixsource-foundation-v1/ibkr_fx/` with sha256
`7e58af06…` (fix) / `961bafdb…` (rollover).

### 4.1 `sanitized_fix_window_20260928T145053Z.json` — London-fix window, n=1 day

One 25-minute two-sided paper-session capture, **2026-09-28 14:51–15:16 UTC**
(11:16 ET / 16:16 London), IDEALPRO CASH tickByTickBidAsk, read-only whitelist
(no order functions present; readonly guard 321 not fired; 0 subscription
errors). Valid obs per pair 20,870–38,111. Spread p50/p90 (pips): EURUSD
0.1/0.2; GBPUSD 0.3/0.5; AUDUSD 0.2/0.2; USDCAD 0.3/0.4; USDJPY 0.3/0.5
(max 0.3–0.8). Clock offsets (recv−server) 1.3/1.9 s; per-pair recv−tbt p50
0.88–0.96 s. **Authority classification: n=1 window, one day, paper venue —
corroborating evidence for the direction and rough magnitude of
liquid-hour spreads ONLY. It is NOT edge evidence and NOT sufficient cost
authority** (owner directive 2026-09-29). It also cannot be compared
naively to the panel venue: on the same day-class the Dukascopy panels'
14:00–15:00 hour medians are 0.3–0.8 pips — the paper IBKR book reads
tighter; the transfer between venues is unmeasured.

### 4.2 `sanitized_rollover_window_20260928T211921Z.json` — rollover window, n=1 day

One 30-minute capture, **2026-09-28 21:19–21:49 UTC** (inside the 21:00–22:00
roll window), same read-only paper session. Valid obs per pair only 389–600
in 30 min (vs 20k–38k in the fix window — the book is thin); max inter-event
gaps 79.9–274.9 s; recv−tbt p50 ~1.0 s (max 70.6 s on USDJPY). Spread
p50/p90 (pips): EURUSD 2.1/3.3; GBPUSD 5.4/6.1; AUDUSD 1.7/4.3; USDCAD
4.8/5.4; USDJPY 5.6/5.9 (max up to 8.0). **Same classification: n=1 window,
one day, paper venue — corroborating only.** Its value here is directional
cross-check: it independently corroborates the panel-measured widening of
the 21:00–22:00 hour (§3.2/§3.3) in both magnitude and pair ordering
(GBP/JPY worst, EUR best) — two unrelated venues agreeing on the shape,
one day apart in sample. That raises confidence in the SHAPE; it does not
convert either capture into cost authority.

### 4.3 `sessions_index.jsonl` (modified)

Now lists 3 runs: s0_verify (2026-09-28T02:03Z, DISCONNECTED_MID_STREAM
status-label cosmetic per L-FX handoff), fix_window COMPLETE, rollover_window
COMPLETE. Read, unmodified, used only to confirm run identity/sha256 above.

---

## 5. What this freeze does NOT establish

- **Commission, slippage-beyond-spread, swap LONG/SHORT rates, triple-swap
  calendar, rollover accrual clock, minimum size: UNMEASURED** (COST_ACCOUNTING_SPEC
  §4 U2–U6; VERDICT_session2 V3 rows 2–7; ERRATUM leaves them NOT_RUN).
  Declared pessimistic bands stand; see COST_AUTHORITY_TABLE.md for the
  per-component verdicts and the exact owner evidence that upgrades each.
- **Venue gap:** every panel-measured spread in this document is the
  **Dukascopy historical feed's** quoted spread (5.7 years, two-sided,
  per-minute or per-bar-endpoint). The only IBKR numbers are n=1-day paper
  windows (§4). Nothing measured here establishes that a live IBKR IDEALPRO
  book quotes these distributions; the two sources agree on shape (§4.2) at
  different levels. Cost runs under panel-venue spreads must carry the
  venue label in every trial's `cost_tier` block.
- No PnL, no edge claim, no scoring, no OOS look — this is a rules + cost
  authority document. Numbers here become load-bearing only when cited by
  lanes that run under the frozen calendar.

## Appendix A — measured per-UTC-hour spread schedule (this lane, 2026-09-29)

Method: M1 pairs — spread at minute close by UTC close-hour, exact histogram
percentiles, full panel 2021-01-01→2026-09-23; H1 pairs — `s_open` by
open-stamp hour, numpy percentiles, full parquet. Representative hours
(p50/p90, pips); the full 24-hour tables live in the handoff
`PC_pit_cost.json.outputs_stats` and are reproducible from Appendix B
parameters.

| pair | 13h | 14h | 15h | 19h | 20h | 21h | 22h |
|---|---|---|---|---|---|---|---|
| EURUSD M1 | 0.3/0.5 | 0.3/0.5 | 0.3/0.5 | 0.3/0.5 | 0.3/0.6 | 1.4/4.2 | 0.7/2.7 |
| GBPUSD M1 | 0.8/1.1 | 0.8/1.1 | 0.8/1.1 | 0.8/1.2 | 0.9/1.4 | 3.1/9.0 | 1.6/6.0 |
| USDJPY M1 | 0.5/0.8 | 0.5/0.8 | 0.5/0.8 | 0.5/0.8 | 0.6/1.1 | 2.3/8.3 | 1.1/5.1 |
| USDCAD H1 (s_open) | 1.1/1.4 | 1.2/2.0 | 1.1/1.8 | 1.1/1.5 | 1.1/1.5 | 1.2/2.7 | 4.6/9.2 |
| AUDUSD H1 (s_open) | 1.0/1.3 | 1.0/1.5 | 1.0/1.3 | 1.0/1.3 | 1.0/1.4 | 1.2/3.2 | 2.9/5.2 |

## Appendix B — measurement reproduction parameters (no repo script, by write scope)

Panels and paths: §1.1 (input 1). M1 decode: `struct '>5if'`, per-pair scale
1e5/1e5/1e3, spread quanta = integer (ask−bid) = 0.1 pip exactly on all three
pairs; tradable = volume>0 both sides; percentile = exact histogram quantile.
Windows: Friday fill = spread_open of the [20:00,20:01) minute (sec==72000)
on sleeve-window Fridays; roll = spread_close of minutes with sec in
[75600, 86340] (close stamp in (21:00,22:00]); Sunday reopen = spread_open of
the first tradable Sunday minute; hour table = spread_close by ((sec+60)//3600)%24.
H1: `s_open`/`s_close` columns of the ANC parquets, pip = 1e-4. Sleeve window
slice [2021-01-08, 2026-06-26]. Any re-run that reproduces these numbers from
the same digests (input 1) is authoritative; divergence = investigate before use.
