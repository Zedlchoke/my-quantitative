# 6J_DEEP_v2 — Japanese Yen Futures Deep Dossier v2 (2020–2026)

- Lane DEEP-6J, task FUTURES-DEEPRESEARCH-V2-20261003 (prep-class deep descriptive
  research; NOT a scored cycle; no PnL evaluation, no signal selection — anything
  PnL-linked selection = NOT_RUN by dispatch law).
- Generated_utc: 2026-10-02/03 (lane local). Worktree
  `prep/futures-behavior-10syms-20261002` @ base 26d96eb4 (uncommitted lane
  artifacts; see handoff).
- Supersedes (does not replace) v1: `FUTURES-BEHAVIOR-10SYMS-PREP-20261002/dossiers/6J_DOSSIER.md`
  (16-month true-front daily window, RTH-blind). v1 remains evidence of record for
  its window; this dossier re-measures everything on the NEW vendor panel.
- Inputs (read-only data):
  - Databento GLBX.MDP3 6J ohlcv-1m, **4 chained windows, 2020-01-01 → 2026-10-01**:
    `AV1B-O1M-6J-BACKFILL2` (2020–22, $3.05, FX-BACKFILL lane), `AV1R-O1M-6J-BACKFILL`
    (2022–24, 2024–26), `AV1T-O1M-6J` (2026-01→07, 07→10). Ledger:
    `FUTURES-BEHAVIOR-10SYMS-PREP-20261002/acquisition_download/backfill_20261003/BACKFILL_LEDGER.json`
    + `COMPLETION_LEDGER.json` (vendor sha verified 16/16 by that lane).
  - GLBX statistics + definition (2023-10+ only → OI statements are 2023+ only).
  - Nonprice PIT archives `~/.my-quantitative-data/futures-nonprice-10syms/`:
    MOF daily FX intervention (**full official record 386 daily ops
    1991-05-13→2026-05-06**, publish lag ~1 month; the normalized tidy as
    originally shipped carried only 81 of them — 300 dropped by a blank-month
    carry-forward defect in the normalizer, incl. the in-window 2022-10-24
    op; **SOURCE_TIDY_RESOLVED 2026-10-03**: the regenerated 386-row
    `normalized/mof_intervention_tidy.parquet` was verified ON DISK by lane
    DOSSIER-ERRATA-V2 — 386 rows, 2022-10-24 ¥7,296×¥100m JPY-buying row
    present, pre-fix copy preserved as `.bak_81rows_20261003`
    [ERRATUM M-1/n-2: header previously said
    "81 ops 1991-04→2026-05" — wrong on both ends]), BoJ statements archive
    (2011→2026-09) + mpmdeci indices (2018→2026-01),
    CFTC legacy CoT 6J as-published (2006-01→2026-09-22), FRED DTB3 (latest +
    year-end ALFRED vintages).
- Analysis artifacts (this lane, all under
  `research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/`):
  `6J_deep_lib.py`, `6J_build_cache.py`, `6J_a1_regimes.{py,json}`,
  `6J_a2_sessions.{py,json}`, `6J_a3_term.{py,json}`, `6J_a4_events.{py,json}`,
  `6J_a5_cot.{py,json}`, `6J_qa_ledger.{py,json}`, cache `6J_cache/`
  (2,843,938 outright 1m bars; contract registry 95 contracts; sessions 9,386
  (contract × session); held-chain 1,745 sessions).
- Claims taxonomy: **FACT** (sourced primary + date) / **OBSERVED** (script +
  window on this panel) / **POSTULATED** (mechanism, unmeasured) / **NOT_RUN**
  (default; never inferred PASS).
- **ERRATA applied 2026-10-03** (lane DOSSIER-ERRATA-V2, from
  `audit/a7_6j/A7_DEEP_6J.md`, verdict PASS_WITH_REQUIRED_ERRATA — all 8
  headline families recomputed fresh and reproducing): **M-1** MOF source
  defect — in-window op count 9→**10** (2022-10-24 ¥0.73T exists as an
  explicit daily row in the raw official CSV; the normalizer dropped 300 of
  386 daily ops on a blank-month carry-forward failure;
  SOURCE_TIDY_RESOLVED — the regenerated 386-row tidy verified on disk
  2026-10-03, this erratum now records the completed change); **M-2** "record short −184,223" → deepest-since-2007
  (series record −188,077 @2007-06-26); **M-3** OI-lead "3–7 days" →
  **1–3 days** vs the raw volume crossover; **M-4** "every down-leg ends at
  an op" → **4 of 14**; **M-5** QA "16 missing weekdays = holidays only"
  has one exception (2022-09-20 held-rule artifact); + 6 MINOR labels.
  Full old→new ledger in §10.
- **Quote-orientation trap (restated, load-bearing)**: 6J = **USD per JPY**
  (0.0061–0.0099 across 2020–2026), NOT USDJPY. 6J UP = yen appreciation;
  long 6J = long JPY / short USD. A "USDJPY-long" spot idea is a 6J **SHORT**.
  Implied USDJPY = 1/(6J price): band **100.80–163.68** [OBSERVED: absolute 1m
  extremes — low 0.0061095 = USDJPY 163.68 on 6JQ6 2026-07-28 10:22 UTC (the
  pre-intervention weak extreme, a *serial* book bar); high 0.0099205 = USDJPY
  100.80 on 6JM0 2020-03-09 (COVID squeeze)].

---

## 0. Headline findings (upgrades vs v1)

1. **The 6.8-year panel kills v1's "settlement-derived deep era" limitation.**
   2.84M outright 1m bars, 1,745 held-chain sessions, 0 tick-grid violations,
   0 duplicate (instrument, ts) rows, 1 stray bar in the 16:00–17:00 CT halt,
   0 weekend bars [OBSERVED: `6J_qa_ledger.json`]. Everything v1 could only
   measure 2025-05→2026-10 is now measured 2020→2026.
2. **CME FX trades 23h CONTINUOUSLY (17:00→16:00 CT, 1380 minutes, no
   maintenance break)** — measured: median held session has 1,357/1,380 1m
   bars [OBSERVED: `6J_qa_ledger.json`]. v1's RTH-only blindness dissolved:
   **Tokyo morning (09:00–11:30 JST) alone carries 11.0% of full-session volume
   and 13.0% of bar-range; evening+overnight (17:00–07:00 CT) carry 48.6%**;
   the BoJ decision window (12:00–15:30 JST, US overnight) has real but thin
   books (median 1m volume 34 vs 53 full-day) [OBSERVED: `6J_a2_sessions.json`].
3. **The 2021–2026 yen-weak super-cycle is ONE unrecovered −46.7% drawdown**
   (peak 2020-03-09 → trough 2026-07-28, rolled long-JPY basis incl. carry
   drag), decomposed by 3% zigzag into legs — **4 of the 14 down-legs
   terminate within 0–2 sessions of a MOF op / op-window** (2022-10-20
   [+1 of the 10-21 op; also +2 of the recovered 10-24 op], 2024-04-26
   [+1 of the Apr-29 op], 2024-07-10 [+1 of the Jul-11/12 ops], 2026-07-28
   [+2 of the unverified 07-30 window]); the other ten end nowhere near an
   op [ERRATUM M-4: was "legs that END at intervention/BoJ events" /
   H5's "every ≥3% down leg … 0–2 sessions of an op" — counterexamples:
   2022-07-14, 2023-03-08, 2023-06-29, 2023-11-13, 2024-08-15, 2024-11-14,
   2025-01-08, 2025-05-12, 2025-07-31, 2026-01-13; note the 2024-11-14
   (−11.4%) leg in this very list has no attached event] [OBSERVED:
   `6J_a1_regimes.json` + A7-6J fresh recompute].
4. **Term structure: near < far on 100.0% of overlapping sessions for ALL 14
   measured quarterly pairs (2022–2026, n=50–83 sessions/pair [ERRATUM
   m-3: was 50–78], median 3-month spread −138 ticks ≈ −$863/contract,
   per-pair medians −216 to −90 ticks [ERRATUM m-3: was −215 to −132;
   three pairs sit at −97/−93/−90])**; 25/27 roll gaps positive (2 tiny
   negatives in zero-rate 2021); annualized gap by year (median): 0.52%
   (2020), 0.13% (2021), 2.33% (2022), **5.50% (2023), 5.46% (2024)**,
   2.87% (2025), 2.42% (2026) — per-roll ranges −0.44..+3.95% (2020–21),
   +4.63..+6.60% (2023–24), +1.70..+4.29% (2025–26) [ERRATUM m-6: the
   previous era-range labels "0.1–0.7% / 4.6–5.5% / 2.1–3.1%" matched
   neither the per-year medians nor the per-roll ranges] — the roll-drag
   hurdle is **regime-dependent, not constant** (v1's −2.6%/yr was a
   2025–26 snapshot) [OBSERVED: `6J_a3_term.json`].
5. **First CIP anchoring from the curve itself**: implied USD-over-JPY rate from
   roll gaps vs FRED DTB3 gives implied JPY short rate ≈ −0.4/−0.1% (2020/21),
   −0.4/−0.6% (2023/24, vs known negative-to-zero policy — a systematic ~50–90bp
   offset = discount-yield convention + cross-currency basis, disclosed), rising
   to **+1.0/+1.2% (2025/26)** — consistent with the two 2025 and two 2026
   "Change in the Guideline" BoJ MPMs in this timeline [OBSERVED + FACT titles;
   caveat: ALFRED vintages are year-end snapshots only — NOT a PIT-strict series].
6. **All 10 MOF yen-buying ops of 2022–2026 measured in 1m** [ERRATUM M-1:
   was "all 9" — the raw official CSV contains an explicit 2022-10-24 daily
   op row (¥7,296 × ¥100m = ¥0.73T, USD-sold/JPY-bought; Q4-2022 aggregate
   63,499 = 56,202 + 7,296 + 1 rounding unit) that the defective normalized
   tidy dropped; op count 9→10; the regenerated 386-row MOF tidy was
   verified on disk by lane DOSSIER-ERRATA-V2 on 2026-10-03 —
   SOURCE_TIDY_RESOLVED)]: op-day volume 1.75–4.79× the
   strict-past 21-session median [ERRATUM m-1: was "1.8–4.8×" — same
   numbers, honest rounding now stated exactly], true range at the
   85th–100th percentile of the strict-past 126-session distribution
   [ERRATUM m-1: was "94th–100th" — 2026-05-04 (¥0.78T stealth op) =
   0.849], session return +0.78…+2.35% on 8/10 ops (exceptions:
   2026-05-04 −0.09% and the recovered 2022-10-24 at −0.84% — a
   JPY-BUYING op landing on a down day for 6J price), and the intervention
   bursts are timestamped: Tokyo-afternoon bursts (2024-04-29 01:35 UTC
   tokyo_am, 2026-05-06 04:27 UTC tokyo_pm) vs US-morning bursts
   (2024-07-11 12:42 UTC london_pm/ny_am; 2026-07-30 13:36 UTC, 5.7×
   volume, NOT MOF-VERIFIED — Q3-2026 page pending). 2022-10-24 anatomy
   (A7-6J fresh recompute): held chain −0.84%, volume 1.75× past-21
   median, TR 98th pctile, 246,433 contracts; the 2022-10-20 zigzag
   leg-end sits +2 sessions from this op. MPM days: median |return| 0.57%
   vs 0.30% all-days, volume 1.27× [OBSERVED: `6J_a4_events.json`; ops
   FACT mof.go.jp via nonprice archive (raw CSV for 2022-10-24)].
7. **Liquidity migration re-measured precisely (v1 partially wrong)**: the new
   quarterly ramps over ~2 weeks but **raw daily volume crossover happens only
   ~5 calendar days (=2 sessions) before the old quarterly's delivery**, and
   **open interest crosses 1–3 calendar days BEFORE the raw volume crossover
   (12/12 rolls, mode 2)** (2023-10+ only) [ERRATUM M-3: was "3–7 days" —
   that magnitude is the lead over the k=5 SWITCH, not over the volume
   crossover; the dossier's own Sep-2026 exemplar (OI 09-08 → volume 09-11 =
   3 days) already contradicted "3–7"] — e.g.
   Sep-2026: OI cross Sep-08 → volume cross Sep-11 (Z6 share 2.5%→92.4% in 9
   sessions) → k=5 held-rule switch Sep-15 [OBSERVED: `6J_a3_term.json` +
   A7-6J fresh recompute].
8. **CoT 2006–2026**: deepest speculator short since 2007, **−184,223
   (2024-07-02)** into the Apr/Jul-24 ops — the SERIES RECORD is **−188,077
   on 2007-06-26** (so 2024 is the 2nd-deepest of the 20-year series)
   [ERRATUM M-2: was "record speculator short"], then a record LONG
   +179,212 (2025) — the largest rapid regime flip in the
   20-year series (+363k in ~9 months; the all-time trough-to-peak range
   2007→2025 is 367k) — and back to −163,412 by 2026-07-28 (the
   **11th**-most-negative week of 1,082 — 10 weeks lie below it: six in
   2007, four in 2024 [ERRATUM m-2: was "6th-largest short ever"], but
   z=−1.44 because the trailing-3y window is inflated by the 2025 record
   longs) [OBSERVED: `6J_a5_cot.json`; as-published, not revised].

---

## 1. Panel construction (PIT rules, no vendor stitching)

- **Contract registry** [OBSERVED: `6J_build_cache.py` → `6J_cache/contract_registry.json`]:
  95 outright contracts (40 HMUZ quarterlies, 55 serials), 0 unresolved strays,
  resolved from one-digit-year symbols by time-cluster + 3rd-Wednesday delivery
  windows (2010–2028 candidates). 8 contracts have two bar-clusters (deferred
  trickle then roll-window activity separated >60d) — mapped to one key, benign.
- **Held-contract rule** (both maps built; volume rule primary):
  `volume-crossover k=5`: hold the HMUZ contract with the highest trailing-5-
  session mean volume, decided at session t close (strictly past + current
  close), new contract held from t+1 → **27 rolls, 1,745 sessions,
  2020-01-02→2026-10-01** [OBSERVED]. [ERRATUM m-5 — spec-vs-code
  disclosure: the CODE labels day t's held contract using day-t volume
  (`held[t]` from the trailing mean THROUGH t), i.e. the switch is visible
  on the switch session itself rather than strictly from t+1 as the spec
  sentence reads. Quantified by A7-6J: max DD and cumulative rolled return
  are bit-identical under both variants — headline numbers stand; the
  "decided at t close, held from t+1" wording overstates the code's
  strict-PIT timing and H1's "executable PIT" phrasing should be read
  with this caveat.] Calendar quarterly rule (v1-consistent)
  as sensitivity: vol 9.48%/yr vs 9.44% (volume rule) — rule choice is not
  material to descriptive stats [OBSERVED: `6J_a1_regimes.json`].
- **Returns**: `ret_within` = within-contract daily log returns (no roll-gap
  jumps anywhere; 27 first-sessions carry NaN); `ret_rolled` = consecutive held
  closes incl. the cross-contract carry gap on roll dates (economic PnL of a
  rolled position at close, no spread/commission). All vol/trend stats use
  ret_within; drawdown anatomy uses ret_rolled (disclosed per-field).
- **Session clock**: trade date = CT date of the 16:00 close; DST-correct via
  zoneinfo (America/Chicago, Asia/Tokyo, Europe/London, America/New_York);
  center windows defined in each center's OWN local clock so Tokyo 09:00 JST is
  always found even as UTC/CT offsets shift [OBSERVED: `6J_deep_lib.py`
  CENTER_WINDOWS].

## 2. A1 — Strict-past regime map 2020–2026 [OBSERVED: `6J_a1_regimes.json`]

- **Path**: price 0.009247 (2020-01-02, USDJPY 108.1) → 0.006383 (2026-10-01,
  USDJPY 156.7); cum within-contract −58.3% vs rolled −37.1% (**+21.2pp = 27
  roll-gap carry payments, ≈3.1%/yr**); close extreme 0.006126 on 2026-07-28
  (USDJPY 163.24). Up-days only 43.7%; median daily move −6.0bp.
- **Vol by year** (ann., within-contract): 2020 9.0% (COVID; rvol21 max 25.1%
  on 2020-03-27; worst day −3.27% 2020-03-13, best +2.84% 2020-03-09), 2021
  **5.6% (the quiet regime)**, 2022 11.4% (YCC shock; best day +3.84% 2022-11-10,
  second YCC day 2022-12-20 +4.83% incl. roll gap), 2023 9.8% (rvol60 peak 16.0%
  on 2023-02-03), 2024 10.3%, 2025 9.9%, 2026 8.3% (skew +1.62, ex-kurt 4.8 —
  the intervention-year signature: few huge up-moves, many small down-days).
- **Strict-past vol terciles** (rvol60 vs trailing-756d own distribution): 2022
  = 228/257 sessions HIGH-vol; 2026 = 0 high (127 low + 68 mid — the 2022 bar
  re-anchored the whole scale; the 2026 intervention vol never reached 2022
  percentiles on a 60d basis).
- **Trend persistence**: acf1 −0.022 full-sample (no daily momentum/reversal);
  variance ratios 5/20/60 = 0.91/0.90/0.81 (**persistent anti-persistence at
  60d — mean-reverting multi-month regime, consistent with intervention-capped
  trends**); sign-match-trailing-50d share 54.9%; |ret| acf1 +0.196 (vol
  clustering). Rolling acf1 p10–p90 [−0.10, +0.06].
- **Trend regimes** (120d t-stat ±1): trend_jpy_down 712 sessions vs trend_jpy_up
  7 — **the down-trend regime overwhelmingly dominates 2021–2026** (2021: 134/0,
  2022: 223/0, 2023: 143/0, 2024: 53/0, 2026: 90/0). v1's "mild trending bias"
  was an understatement of a 6-year structural regime.
- **Drawdown anatomy** (rolled series, 3% zigzag legs):
  - structural: peak 2020-03-09 → trough 2026-07-28 = **−46.7%** unrecovered;
  - legs: 2021-01-05→2022-07-14 **−29.8%** (395 sess, the carry leg to 139);
    2022-08-01→2022-10-20 **−12.9%** (ends at the Oct-21 op); +16.1% rebound
    2022-10-20→2023-01-13 (largest up-leg — post-intervention repositioning);
    2023-12-29→2024-04-26 **−12.1%** (ends 1 session before the Apr-29 op);
    2024-07-10→2024-08-05 **+11.1% in 18 sessions** (Jul-11/12 ops + Jul-31 BoJ
    hike + Aug-5 carry crash — the fastest leg of the era); 2024-09-16→11-14
    −11.4% (post-US-election dollar); 2026-01-27→07-28 −7.4% (final weak leg);
    +6.2% 2026-07-28→09-09 (post-window recovery).
- **v1-window context**: v1 (2025-05-20+) rvol21 median 8.66% = 56th pctile of
  2020–24 — i.e., v1's "12.4% peak vol" window was elevated but NOT extreme on
  the full panel; v1-window max DD within window 13.8%.

## 3. A2 — Session/intraday structure, DST-correct [OBSERVED: `6J_a2_sessions.json`]

Panel: held-contract 1m bars, 1,745 sessions × median 1,357 bars.

- **Exchange-clock hours (CT, volume share)**: peak = **09:00–10:00 CT (10.3%)**,
  then 08:00 (8.9%), 07:00 (8.6%) — the London/NY overlap with legacy 08:20 ET
  FX open; trough = 16:00 (halt), 17:00–18:00 CT (1.5–1.8%, Sydney open).
  Evening 17:00–24:00 CT = 21.3%, overnight 00:00–07:00 CT = 27.3%, US day
  07:00–16:00 CT = 51.3%. Stable across eras (2020-21 / 2022-23 / 2024-26 top-3
  hours identical; tokyo-day bucket 7.4–8.0%).
- **Center-local windows** (overlap disclosed — london_pm ∩ ny_am):
  tokyo_am 11.0% vol / 13.0% range; tokyo_lunch 2.7% (dead); tokyo_pm 6.2%;
  tokyo_fix 2.9% (median 1m vol 53 = full-day median — the fix is thin but
  normal-liquidity); london_am 16.6%; **london_pm 35.5% vol (peak window)**;
  ny_am 32.5% (median 1m vol 120 = deepest book); ny_pm 15.5%; ny_post 1.5%.
- **Where extremes print** (first-occurrence session high/low minute): highs —
  london_pm 25.4%, ny_am 24.0%, tokyo_am **18.1%**, ny_pm 13.4%; lows —
  london_pm 27.4%, ny_am 25.7%, tokyo_am 15.2%. **Tokyo morning prints the
  session extreme ~1 day in 6–7** — invisible to v1.
- **Gaps**: close→open (1h halt) median 0.0bp, p95 |gap| 12.8bp; weekend gap
  p95 43.6bp — a genuinely 23h market; no tradable gap structure at 1m close
  granularity.
- **BoJ decision window** (12:00–15:30 JST = ~22:00–01:00 CT): 9.5% of session
  volume, median 1m volume 34 vs 53 full-day — **tradeable but ~35% thinner**:
  entry/exit around MPM decisions pays a liquidity premium (H4 floor).

## 4. A3 — Term structure, 27 rolls, CIP [OBSERVED: `6J_a3_term.json`]

- **Serial books confirmed dead on the new panel**: serial months carry
  0.09–0.39% of total 6J volume in EVERY year 2020–2026 (peak 0.39% in 2024).
  The HMUZ-only universe rule is correct for all 7 years (v1: 2 years).
- **Near < far, always**: all 14 liquid-overlapping quarterly pairs (≥50
  both-quoted sessions, both ≥30 bars — evidence starts 2022; 2020–21 deferred
  books too thin for pair stats, rolls carry the signal there) show near-below-
  far on **100.0%** of sessions (50–83 sessions per pair); median 3m spread
  −138 ticks (−216 to −90 by pair [ERRATUM m-3: was −215 to −132; three
  pairs have medians −97/−93/−90]), i.e. contango-in-carry (deferreds
  premium) never flipped. v1 finding extended and sharpened.
- **Roll gaps (same-session close spread new−old at last both-traded session —
  the economically correct carry cost; close-to-close across the switch would
  smear in the old contract's final partial session and is NOT used)**:
  27/27 measured, **25 positive**, 2 tiny negatives (2021-06 −20 ticks,
  2021-09 −3 ticks — zero-rate-diff noise); median +105 ticks (≈$656/contract,
  0.78% per roll); annualized by delivery spacing: 2020 0.52%, 2021 0.13%,
  2022 2.33%, **2023 5.50%, 2024 5.46%**, 2025 2.87%, 2026 2.42%.
- **Migration anatomy per roll** (raw daily volume): old quarterly stays
  dominant until ~2 sessions before its delivery-month cessation; new's share
  ramps over the prior ~2 weeks; **first new>old session is consistently 5
  calendar days before the old delivery date**; **OI crossover leads the raw
  volume crossover by 1–3 calendar days (12/12 rolls 2023-12→2026-09, mode 2;
  the 4–7-day figures previously quoted here are the lead over the k=5
  SWITCH) [ERRATUM M-3]** [OI 2023-10+ only].
  Sep-2026 exemplar (Z6 share of U6+Z6): 08-31 1.6% → 09-03 11.7% → 09-10
  34.8% → **09-11 92.4%** → 09-14 99.7% (U6's 127-bar final session; volume
  838 lots); OI cross 09-08; k=5 rule switch 09-15.
- **CIP check (descriptive, vintage-caveated)**: implied JPY short rate =
  DTB3 − annualized gap → 2020 −0.40%, 2021 −0.08%, 2022 +0.26%, 2023 −0.42%,
  2024 −0.62%, 2025 **+1.02%**, 2026 **+1.19%**. Sign and time-variation track
  the policy cycle (BoJ: negative rates until the 2024-03 framework change;
  hikes titled 2024-07-31, 2025-01-24, 2025-12-19 + v1-FACT 2026-06-16/09-18);
  the absolute level carries a systematic ~50–90bp offset (DTB3 discount-yield
  convention + futures-forward basis + cross-currency basis — NOT decomposed).
  ALFRED vintages in store are year-end snapshots (2020…2025 + 2026-09-30
  latest); a 2022-12-31-vintage sensitivity on the 2020–22 rolls moves the
  median implied rate by <50bp. **NOT a PIT-strict rate series** — H3 closure
  still needs a proper JPY-side series (TONA) + release-stamped US series.

## 5. A4 — Intervention & BoJ MPM anatomy [OBSERVED: `6J_a4_events.json`]

PIT law: MOF op amounts publish ~1 month (monthly) / quarterly (daily detail)
AFTER the fact — **no same-day PIT signal exists from the op record**; every
op-day number below is description of a disclosed operation. Ops FACT
(mof.go.jp daily history via nonprice archive; **the full official record is
386 daily ops 1991-05-13→2026-05-06** [ERRATUM M-1/n-2: this preamble
previously said "81 ops 1991-04→2026-05", and "9 JPY-buying ops in-window"];
**10 JPY-buying ops in-window** as re-adjudicated from the RAW official CSV:
2022-09-22 ¥2.84T, 2022-10-21 ¥5.62T, **2022-10-24 ¥0.73T (recovered —
explicit daily row in the raw CSV, row 519, blank year/month columns; the
normalized tidy's normalizer failed to carry blank months forward and
dropped 300 of 386 official daily ops; every dropped row has a blank month
field, every month-present row IS in the parquet — 0 exceptions.
SOURCE_TIDY_RESOLVED: the nonprice source-fix lane regenerated the MOF
tidies; this lane verified the regenerated
`normalized/mof_intervention_tidy.parquet` on disk 2026-10-03 — 386 rows,
the 2022-10-24 ¥7,296 row present, pre-fix copy kept as
`.bak_81rows_20261003`)**, 2024-04-29 ¥5.92T,
2024-05-01 ¥3.87T, 2024-07-11 ¥3.17T, 2024-07-12 ¥2.37T, 2026-04-30 ¥6.28T,
2026-05-04 ¥0.78T, 2026-05-06 ¥4.68T).

- **Op-day descriptives** (vs STRICT-PAST baselines): session return +0.78% to
  +2.35% on 8/10 ops (2026-05-04 −0.09%: the ¥0.78T stealth op; 2022-10-24
  −0.84%: the recovered op, A7-6J fresh recompute); volume
  1.75–4.79× past-21-median; true-range percentile 0.85–1.00 of past-126.
- **Timing visible in 1m**: largest bursts — 2022-09-22 02:51 UTC (tokyo_lunch;
  9,625 contracts/minute), 2024-04-29 01:35 UTC (tokyo_am; 10,581), 2026-05-06
  04:27–04:28 UTC (tokyo_pm; 12,603 — classic Tokyo-afternoon intervention
  burst), vs 2024-07-11 12:42–12:43 UTC (london_pm/ny_am; 17,448 — the biggest
  per-minute futures volume of any op day) and 2024-05-01 20:16–20:47 UTC
  (ny_post; the thin-book late-NY continuation of the holiday-session op).
  Range-by-window: Tokyo-afternoon ops put 30–45% of bar-range in tokyo_pm;
  US-hours ops put 60–80% in london_pm+ny_am.
- **Next-5-session paths** (descriptive, per-op in JSON): partial retracement
  then chop on most ops (e.g. 2026-04-30 +2.35% → −0.32/−0.09/−0.42/+0.95/−0.37);
  2024-04-29 → d+2 +2.03% (the May-1 op). NOT a conditional-return table.
- **Pending window (2026-07-30)**: +2.36% session, 607,579 contracts = 5.66×
  past-21-median (the largest volume day of the entire panel), top burst 13,366
  contracts/minute 13:36 UTC (london_pm/ny_am). **NOT MOF-VERIFIED** — Q3-2026
  daily detail unpublished at data access (2026-10-02); price anatomy only.
- **BoJ MPM days (54 decision dates 2020–2026, day-2 statements; FACT archive)**:
  median |return| 0.57% vs 0.30% all-days (≈1.9×); median volume 1.27× vs
  1.00×; BoJ-decision-window (12:00–15:30 JST) range share 13.4% vs 10.3%
  baseline — the decision itself is visible as a modest overnight range
  concentration, not a gap (23h market absorbs it). Regime-change MPMs
  (titled): 2024-03-19 (framework change; roll-date NaN in within-returns —
  disclosed), 2024-07-31 (+1.77%, 2.68× vol), 2025-01-24 (+0.05%, 1.94×),
  2025-12-19 (−1.41%, 2.18×). 2026-06-16/09-18 titles NOT_RUN in this archive
  (PDFs unfetchable); v1-FACT (boj.or.jp, 2026-10-02) says both were "Change in
  the Guideline" MPMs — 2026-09-18 was the largest volume day of Sep-2026 after
  the roll (424,807) [OBSERVED].

## 6. A5 — CoT JPY positioning 2006–2026 [OBSERVED: `6J_a5_cot.json`]

- **20-year regimes** (net non-commercial, contracts): 2007 short-yen carry
  extreme −188k; 2008 flip to +66k (unwind); 2013–15 Abenomics shorts (median
  −80k); 2016 long +72k; 2022–24 heavy shorts (min **−184,223** in 2024 —
  the deepest short since 2007 / 2nd-deepest of the 20-year series; the
  SERIES RECORD is −188,077 on 2007-06-26, listed two lines above —
  set weeks before the 2024 interventions) [ERRATUM M-2: was "the record"];
  **2025 record LONG +179,212**
  (largest rapid flip in series history, +363k contracts in ~9 months;
  the all-time trough-to-peak range 2007→2025 is 367k); 2026 back to
  −163,412 by 07-28. OI nearly doubled 2020→2026 (158k→382k median weekly).
- **Strict-past extremes** (|z|≥2 vs trailing-150wk): 2021-10-26 (−107k) →
  fwd4w vol 8.9% vs pre 5.8%; 2022-04-12 (−112k) → fwd 12.8% vs pre 9.4%;
  2024 cluster (−133k/−129k/−144k/−148k, Feb–Jun) → fwd 6.1–9.7%; 2024-08-06
  (+z post-crash) → fwd 12.1%. Ex-post labels, description only.
- **Down-leg starts (A1 zigzag) vs CoT**: the big legs began from UNREMARKABLE
  z-scores (2021-01-05 z=+1.59 long-ish; 2023-12-26 z=+0.45) — **positioning
  extremes did not mark the starts of the big yen-weak legs; they marked the
  ENDINGS** (record short Feb–Jun 2024 into the Apr/Jul ops; record long 2025
  before the 2026 re-weakening). The 2026-07-28 extreme short (−163k) carries
  z=−1.44 only, because the trailing window still contains the 2025 record
  longs — **rolling-z mutes structural regime shifts** (H5 refinement).

## 7. A6 — Hypothesis refinement vs v1 (specs WITHOUT PnL evaluation)

Re-use law unchanged: corpus-1200 out of scope; FX-spot ideas transfer only as
hypotheses (orientation, roll basis, costs, margin). v1's five hypotheses
re-ranked and re-specified; PARAM-GAP status updated with the new panel.

**6J-H1 (v1 H1) — HMUZ quarterly universe + roll rule. DISSOLVED as hypothesis;
now a measured construction standard.** Serial share ≤0.39%/yr every year
2020–2026; PIT volume-crossover k=5 chain measured (27 rolls); calendar rule
sensitivity immaterial (9.48 vs 9.44% vol). Spec for any future backtest:
universe = nearest HMUZ; roll = k=5 volume crossover (or calendar-quarterly);
both executable PIT on this panel. PARAM-GAP: none. Floor: none.

**6J-H2 (v2, NEW) — OI-leads-volume roll timing.** OBSERVED 12/12 rolls
2023-12→2026-09: OI crossover precedes the raw volume crossover by **1–3
calendar days (mode 2)** [ERRATUM M-3: was "3–7 days" — that magnitude is
the lead over the k=5 SWITCH, not over the volume crossover]; both precede
old-contract death (~2 sessions). POSTULATED mechanism: positions
transfer via spreads/EFPs before outright flow. Testable spec (future): roll
trigger = "next quarterly OI > old OI" (PIT, T+1 statistics) vs k=5 volume —
compare execution-day liquidity cost near rolls, NOT PnL selection. PARAM-GAP:
statistics publish time (cleared-volume/OI next-morning lag is tested in the
dbn fixture suite but the exact GLBX publication stamp for 2023–26 must be
pinned before scoring). Floor: OI data 2023-10+ only.

**6J-H3 (v1 H3, upgraded) — Regime-dependent roll-carry hurdle (CIP-anchored).**
v1 said "constant −0.22…−0.33%/month"; v2 measures the hurdle as a FUNCTION of
the rate differential: per-year medians 0.52%/0.13% (2020/21), 5.50%/5.46%
(2023/24), 2.87%/2.42% (2025/26); per-roll ranges −0.44..+3.95% (2020–21),
+4.63..+6.60% (2023–24), +1.70..+4.29% (2025–26) [ERRATUM m-6: the previous
era-range labels "0.1–0.7%/yr (2020–21), 4.6–5.5% (2023–24), 2.1–3.1%
(2025–26)" matched neither the per-year medians nor the per-roll ranges],
with implied JPY rate +1.0/+1.2% in 2025–26. Any long-JPY idea's
hurdle must be re-estimated from the LIVE curve, not a constant. Invalidation:
near<far persists while implied diff collapses below zero. PARAM-GAP: JPY-side
rate series (TONA) + release-stamped US series to close the CIP loop
PIT-strictly (ALFRED year-end vintages insufficient). Floor: curve itself
measured (27/27 rolls).

**6J-H4 (v1 H4, partially de-gapped) — BoJ MPM-day conditional behavior.**
v1's PARAM-GAP "RTH files cannot time decisions" is DISSOLVED: 1m data covers
the 12:00–15:30 JST window 2020–2026 (books ~35% thinner there — measured
floor). Measured descriptives: MPM |ret| 1.9× baseline, vol 1.27×; regime-
change MPMs carry 1.9–2.7× volume. Remaining PARAM-GAPs: (a) surprise
classification (in-house statement-text classifier buildable $0 from the
statements archive — 156 statements stored); (b) policy-rate levels 2024–2026
NOT verified from primary PDFs (titles only) — needed to label hike sizes.
Refined spec: condition on titled regime-change MPMs only (4 measured + 2
v1-FACT 2026); entry window = decision-window ±30min; NO evaluation run here.

**6J-H5 (v1 H5, refined) — Intervention-threshold regime break.** v2 adds the
measured anatomy: **4 of the 14 ≥3% zigzag DOWN legs 2022–2026 terminated
within 0–2 sessions of a MOF op / op-window** (2022-10-20/21 + recovered
10-24, 2024-04-26/29, 2024-07-10/11, 2026-07-28/30); the other ten end
nowhere near an op [ERRATUM M-4: was "every ≥3% zigzag DOWN leg …
terminated within 0–2 sessions of a MOF op / op-window" — an overclaim;
counterexample legs incl. 2024-11-14 (−11.4%) with no attached event];
op-day volume 1.75–4.79× [ERRATUM m-1: was "1.8–4.8×"]; op-day true range
85th–100th pctile [ERRATUM m-1: was "≥94th pctile" — 2026-05-04 (¥0.78T
stealth op) = 0.849].
Threshold definition now buildable PIT-strict from the 386-op history [ERRATUM
M-1: was "81-op history" — the defective tidy's count; the regenerated
386-row tidy is on disk, SOURCE_TIDY_RESOLVED] (e.g.
"distance to the highest USDJPY level at which MOF has ever acted", levels
recomputed as ops disclose with ~1-month lag — the LAG is the PIT constraint,
not the data). CoT refinement: use fixed lookback percentile-of-history (e.g.
rank vs all-prior since 2006) instead of rolling-3y z (which muted 2026 to
−1.44 at the 11th-most-negative week of 1,082 [ERRATUM m-2: was
"6th-largest short ever"]). Invalidation: a future approach to the
zone with no conditional vol/liquidity change. PARAM-GAPs: threshold constant
must be fixed a priori by owner; same-day op detection is NOT available (no
PnL-linked selection until registered cycle).

**6J-H6 (v2, NEW, floor-only) — Tokyo-session liquidity for execution.**
Measured: tokyo_am 11% of volume at 59 median 1m contracts vs ny_am 120 —
Asia-hours execution of US-devised JPY strategies pays ~2× thinner books (but
tighter than the fix windows); MPM decision window 34 vs 53. Specification
floor for ANY future JPY strategy: execution-cost model must be
session-of-day-dependent. No hypothesis evaluation run.

**Quote-orientation trap — restated**: every table above is in 6J price terms
(USD per JPY). Long-JPY = long 6J. USDJPY-long ideas = 6J SHORT + you EARN the
roll carry (near<far); USDJPY-short ideas = 6J LONG + you PAY it (now 2.1–5.5%
/yr depending on year). Spot-corpus PnL never transfers without both
transforms.

## 8. A7 — Data-quality ledger per era [OBSERVED: `6J_qa_ledger.json`]

| Era (window, source chunk) | Rows (total/outright/spread) | Contracts | Notes |
|---|---|---|---|
| 2020-01→2021-12 (AV1B BACKFILL2) | 812,558 / 771,595 / 39,726 | 29 | 1 stray non-6J symbol `6AV3` (filtered); identity via instrument_id + clusters (definition registry starts 2023-10) |
| 2022-01→2023-12 (AV1R BACKFILL) | 906,730 / 840,217 / 66,513 | 32 | clean |
| 2024-01→2025-12 (AV1R BACKFILL) | 1,028,939 / 906,220 / 122,719 | 33 | clean |
| 2026-01→2026-06 (AV1T) | 250,506 / 217,475 / 33,031 | 16 | clean |
| 2026-07→2026-09 (AV1T) | 121,508 / 108,431 / 13,077 | 10 | clean; last bar 2026-09-30 23:59 UTC |

- Global: 2,843,938 outright bars; **tick-grid violations 0** (all OHLC on the
  5e-7 grid); negative/zero closes 0; duplicate (instrument_id, ts_event) rows
  0; break-window bars 1 (16:00–17:00 CT, in 2.84M); weekend bars 0.
- Held-chain continuity: 1,745 sessions; 16 missing weekdays = 15 exchange
  holidays + **1 held-rule artifact (2022-09-20)** [ERRATUM M-5: was
  "= exchange holidays only" — that Tuesday the exchange was OPEN and the
  next quarterly (Z2) traded 125,303 lots over 1,357 bars, but the k=5 rule
  still "held" the ceased U2 (its stale trailing-5 mean exceeded Z2's ramp),
  so the session silently vanishes from the 1,745-session chain — in the
  middle of the September-2022 intervention week; the 09-21 rolled return
  then spans two calendar days off a 97-bar stale U2 close. The vendor PANEL
  itself has no hole that day, so "zero genuine data holes" below survives
  for the panel; the CHAIN attribution was an inferred pass] (Good Friday,
  Christmas, New Year… are the other 15); the 20 "depleted"
  (<25% bars) sessions are ALL roll-date final partial sessions (old
  contract's 09:16 CT cessation) or the 2026-10-01 partial tail
  [ERRATUM m-4: was "the 21 depleted" — the lane's own JSON and the A7-6J
  recompute both say 20] — **zero
  genuine data holes** (contrast: NQ 2020 COVID hole).
- Volume definition gap: summed 1m outright volume = 0.455× (median,
  p10–p90 0.29–0.48) the GLBX cleared-volume statistic (2023-10+, n=752 days).
  Vendor/definition mismatch unresolved → **use volume SHARES and ratios, never
  absolute levels** (extends v1's caveat from IBKR-scale to intra-Databento
  definition scale).
- Statistics/OI: 2023-09-29→2026-09-30 only (all OI claims 2023+).
- Nonprice: MOF record ends 2026-05-06 (Q3-2026 pending, ~1-month lag); CoT
  2006-01-03→2026-09-22 as-published; BoJ statement archive complete
  2011→2026-09-18 but mpmdeci TITLES only 2018→2026-01 (2026-06/09 titles
  carry v1-FACT); FRED DTB3 latest snapshot 2026-09-30 + year-end vintages.

## 9. NOT_RUN register (explicit)

- Any PnL/backtest/conditional mean-return evaluation of H1–H6 (selection law).
- JPY-side rate series (TONA) fetch; PIT-strict CIP closure (year-end ALFRED
  only).
- BoJ surprise classification from statement texts (buildable, $0).
- BoJ policy-rate LEVELS 2024–2026 from primary PDFs.
- Same-day intervention detection signal (impossible PIT: ~1-month lag).
- MOF Q3-2026 daily detail (unpublished at access) — 2026-07-30 window is
  price-anatomy only, NOT MOF-VERIFIED.
- ~~2022-10-24 op (¥0.73T press-reported) absent from the normalized MOF record —
  single-day reconciliation NOT_RUN (quarterly aggregate row exists in the raw
  MOF csv; lane did not re-parse).~~ **RESOLVED by ERRATUM M-1** (A7-DEEP-6J
  re-parsed the raw official CSV: an explicit daily row exists — ¥7,296 ×
  ¥100m, USD-sold/JPY-bought; the op is recovered into the §5 table with its
  anatomy row, and the regenerated 386-row tidy carries it —
  SOURCE_TIDY_RESOLVED).
- Spread-instrument books (6JH1-6JZ0 calendar-spread bars present, 272k rows)
  not analyzed.
- Cross-asset comovement (6E/6B/6A/ES in corpus) — other lanes' scope.
- Trade-classification/aggressor side (ohlcv schema has no side data).

## 10. ERRATA ledger (applied 2026-10-03, lane DOSSIER-ERRATA-V2)

Source of record: `audit/a7_6j/A7_DEEP_6J.md` (verdict PASS_WITH_REQUIRED_ERRATA;
BLOCKER 0 / MAJOR 5 / MINOR 6 / NOTE 6). Every item below is applied in place
above and marked `[ERRATUM …]` at the correction site; nothing was silently
rewritten. NOTEs n-1..n-6 required no dossier change (n-1: 6AV3 already
disclosed; n-3/n-4: honest labels verified; n-5: handoff canonical; n-6:
descriptive-only).

| id | severity | was (old) | now (new) | site |
|---|---|---|---|---|
| M-1 | MAJOR | "81 ops 1991-04→2026-05"; "9 JPY-buying ops in-window"; 2022-10-24 NOT_RUN | 386 daily ops 1991-05-13→2026-05-06; **10** in-window ops; 2022-10-24 ¥0.73T recovered from the raw CSV with anatomy row (−0.84%, 1.75×, TR 98th, 246,433). SOURCE_TIDY_RESOLVED: regenerated 386-row `mof_intervention_tidy.parquet` verified on disk 2026-10-03 (2022-10-24 row present; pre-fix `.bak_81rows_20261003` kept) | header inputs; §0-6; §5 preamble; §9 bullet |
| M-2 | MAJOR | "record speculator short −184,223 (2024)" | deepest short since 2007 / 2nd-deepest of the series; record = −188,077 @2007-06-26; flip +363k (~9mo), trough-to-peak 367k | §0-8; §6 |
| M-3 | MAJOR | OI leads volume crossover by "3–7 days" | **1–3 calendar days (12/12, mode 2)** vs the raw volume crossover; "3–7" is the lead over the k=5 SWITCH | §0-7; §4; §7-H2 |
| M-4 | MAJOR | "every ≥3% down leg terminated within 0–2 sessions of an op" | **4 of 14** legs (2022-10-20, 2024-04-26, 2024-07-10, 2026-07-28); ten end nowhere near an op | §0-3; §7-H5 |
| M-5 | MAJOR | "16 missing weekdays = exchange holidays only" | 15 holidays + 1 held-rule artifact (2022-09-20: exchange open, Z2 traded 125,303 lots, k=5 still held ceased U2); panel itself hole-free | §8 |
| m-1 | MINOR | TR "94th–100th pctile"; vol "1.8–4.8×" | 85th–100th (2026-05-04 = 0.849); 1.75–4.79× | §0-6; §5; §7-H5 |
| m-2 | MINOR | "6th-largest short ever" | 11th-most-negative week of 1,082 (10 below: six 2007, four 2024) | §0-8; §7-H5 |
| m-3 | MINOR | pairs "50–78 sessions"; medians "−215 to −132 ticks" | 50–83; −216 to −90 (three pairs at −97/−93/−90) | §0-4; §4 |
| m-4 | MINOR | "the 21 depleted sessions" | **20** | §8 |
| m-5 | MINOR | k=5 spec "decided at t close, held from t+1" | spec-vs-code disclosure: code labels day t with day-t volume; DD and cumulative return bit-identical under both variants; H1 "executable PIT" carries this caveat | §1 |
| m-6 | MINOR | era roll-gap ranges "0.1–0.7 / 4.6–5.5 / 2.1–3.1%" | per-year medians 0.52/0.13; 5.50/5.46; 2.87/2.42; per-roll ranges −0.44..+3.95 / +4.63..+6.60 / +1.70..+4.29 | §0-4; §4; §7-H3 |

INCIDENT (lane DOSSIER-ERRATA-V2, 2026-10-03): a power outage killed the
errata session mid-run; this dossier's errata were completed from partial
state on resume (headline sites were already applied; §6/§7/§8/§9 sites and
this ledger were finished on resume; PENDING_SOURCE_TIDY resolved after
on-disk verification of the regenerated MOF tidy).

---

### Reproducibility

Run order: `6J_build_cache.py` (rebuilds `6J_cache/` from the read-only
parquet; ~90s) → `6J_a1_regimes.py` → `6J_a2_sessions.py` → `6J_a3_term.py` →
`6J_a4_events.py` → `6J_a5_cot.py` → `6J_qa_ledger.py` (same interpreter:
`/Users/hoangminhlong/my-quantitative/.venv/bin/python`). All thresholds inside
analyses are strict-past/rolling (trailing windows only); event labels
(MOF/BoJ/CoT) are FACT-sourced archives with disclosed lags. No network access
performed by this lane.
