# A7-DEEP-6J — Independent audit of `dossiers_v2/6J_DEEP_v2.md` + `analysis/6J_*`

- Lane **A7-DEEP-6J** (fresh-context auditor), task `FUTURES-DEEPRESEARCH-V2-20261003`.
- Base commit `26d96eb4` (verified `git rev-parse HEAD` at audit start); lane artifacts
  uncommitted by design; nothing outside `audit/a7_6j/` + this handoff written.
  Data (`futures-databento-av1trim`, `futures-nonprice-10syms`) read-only, untouched.
- Method: **fresh recompute with independently written logic directly from the vendor
  parquet** (never importing `6J_deep_lib` or `6J_cache/`), plus source-of-truth
  cross-checks of the nonprice archives (MOF parquet **and** the raw official CSV).
  Scripts: `a7_recompute_core.py`, `a7_recompute_events.py`; outputs
  `a7_core_results.json`, `a7_events_results.json`, `a7_cache/census.json`
  (cache parquets deleted after the run — regenerable in ~2 min).
- Audit date: 2026-10-03 (UTC+7 local). Verdict at end.

---

## 1. Headline recomputation (8 of 8 families recomputed fresh; mandate was ≥6)

| # | Dossier claim | Fresh recompute | Match |
|---|---|---|---|
| 1 | Super-cycle DD **−46.7%**, peak 2020-03-09 → trough 2026-07-28; legs −29.8/−12.9/−12.1/−11.4/−7.4%; up-legs +16.1%, +11.1%/18sess, +6.2% | **−46.6826%**, same peak/trough; all 16 down-legs and top up-legs reproduce with identical dates, depths (−29.803/−12.886/−12.078/−11.390/−7.415) and session counts | **MATCH** |
| 2 | 23h continuous; median held session **1,357/1,380** bars; 1 break bar; 0 weekend bars; 2,843,938 rows; 0 tick-grid violations; 0 duplicates | **1,357.0** median (p5 1,236.2), 1,745 sessions / 27 rolls / 2020-01-02→2026-10-01; break 1, weekend 0; 2,843,938 rows; violations 0 (gcd of all closes = 500 int-nanos = exactly 5e-7); duplicates 0 | **MATCH** |
| 3 | Tokyo morning **11.0%** volume / 13.0% range; **18.1%** of session highs; BoJ window 9.5%, median 34 vs 53 | **11.00 / 13.01**; highs **18.05%** (lows 15.24%); 9.50%, 34 vs 53; evening/overnight/day 21.3/27.3/51.3; hour-09 = 10.3%; gap stats 0 / 12.8bp / 43.6bp | **MATCH** |
| 4 | **100%** near<far on all 14 pairs; median −138 ticks; **25/27** positive gaps (2021-06 −20t, 2021-09 −3t); median +105t = 0.78% | 14 pairs at exactly **100.0%**; median-of-medians **−138.0**; **25/27** positive, negatives exactly (2021-06-15, −20t) and (2021-09-14, −3t); median +105t / 0.781%; ann-by-year medians 0.52/0.13/2.33/5.50/5.46/2.87/2.42 | **MATCH** (but see M-3, m-3, m-6) |
| 5 | Implied JPY short rate −0.40/−0.08/+0.26/−0.42/−0.62/**+1.02/+1.19** by year | identical to 2 decimals under my independent gap + DTB3 recomputation | **MATCH** |
| 6 | 9 MOF ops: ret +0.78…+2.35% (8/9), vol **1.8–4.8×**, TR 94–100th pct; bursts 02:51/01:35/04:27/12:42/20:16 UTC; 2026-07-30 +2.36%, 5.66×, 607,579 = panel-max volume, 13:36 UTC burst | all nine op-day returns, vol multiples, TR percentiles, burst timestamps/volumes/center labels reproduce exactly; 2026-07-30 confirmed **largest volume session of the panel**; MPM 0.568% vs 0.304%, 1.27×; 2026-09-18 = 424,807 = top Sep-2026 day; next-5 paths verify | **MATCH** (but see M-1, m-1) |
| 7 | OI-leads-volume **3–7 days, 12/12**; volume cross ~5 days before delivery; Sep-2026 exemplar | OI-before-volume **12/12** ✓; vol cross before old expiry: 26/27 at exactly 5 days ✓; exemplar numbers exact (1.6/11.7/34.8/92.4/99.7; U6 final 127 bars/838 lots; OI cross 09-08; switch 09-15) — **but the lead is 1–3 days, not 3–7** | **PARTIAL** (M-3) |
| 8 | CoT record short **−184,223** (2024) → record long **+179,212** (2025) → −163,412 (2026-07-28, z=−1.44) | −184,223 @2024-07-02 ✓; +179,212 @2025-04-29 = series max ✓; −163,412, z=−1.4443 ✓; OI 158.5k→382.5k ✓ — **but the series record short is −188,077 @2007-06-26** | **PARTIAL** (M-2, m-2) |

Additional verified panel facts: per-era row table exact (812,558/771,595/39,726/1,237 `6AV3` etc.); registry 95 contracts (40 quarterly / 55 serial / 0 strays); bar extremes low 0.0061095 @2026-07-28 10:22 UTC on 6JQ6, high 0.0099205 @2020-03-09 on 6JM0; 16 missing weekday sessions (identical list); serial-month volume share 0.09–0.39% every year.

**Conclusion of §1: the dossier's measured numbers are genuine, reproducible, and honest at the computation level.** Every discrepancy found below is a claim/label/spec-level error, not a broken computation.

---

## 2. MOF intervention record vs source of truth (audit question 2)

Source of truth: `~/.my-quantitative-data/futures-nonprice-10syms/mof/foreign_exchange_intervention_operations.csv`
(official MOF daily history, Shift-JIS) and `normalized/mof_intervention_tidy.parquet`.

- The 9 in-window ops and amounts in the dossier **match the parquet exactly**
  (2022-09-22 ¥2.84T; 2022-10-21 ¥5.62T; 2024-04-29 ¥5.92T; 2024-05-01 ¥3.87T;
  2024-07-11 ¥3.17T; 2024-07-12 ¥2.37T; 2026-04-30 ¥6.28T; 2026-05-04 ¥0.78T;
  2026-05-06 ¥4.68T).
- **2026-07-30 "NOT MOF-VERIFIED pending Q3-2026 page" — label HONEST and correct.**
  Parquet ends 2026-05-06; the quarters archive ends at `2026_2Qe.html`; no Q3-2026
  page exists at access. The dossier consistently carries price-anatomy-only framing.
- **2022-10-24 — label honest but understated; the miss is a normalizer defect.**
  The raw official CSV contains an **explicit daily op row** for 2022-10-24
  (¥7,296 × ¥100m = ¥0.73T, USD-sold/JPY-bought; row 519: `['','','24日','','','24','7,296',…]`
  with blank year AND month columns), and the Q4-2022 quarterly aggregate 63,499 =
  56,202 + 7,296 (+1 MOF rounding unit). The normalizer that built the tidy parquet
  did not carry blank months forward and **dropped 300 of the 386 official daily ops**
  (every dropped row has a blank month field; every month-present row is in the
  parquet — 0 exceptions). The dossier said "quarterly aggregate row exists in the
  raw MOF csv; lane did not re-parse" — true but incomplete: the daily row was
  available in the same archive, one carry-forward fix away.
- Consequence measured fresh: on 2022-10-24 the held chain moved **−0.84%**, volume
  **1.75×** past-21 median, TR **98th** pctile, 246,433 contracts — the true in-window
  JPY-buying op count is **10**, and the op-day positivity statement would become
  "8/10" (not "8/9"). The 2022-10-20 zigzag leg-end sits +2 sessions from this op.
- Header "81 ops 1991-04→2026-05" is wrong on both ends of the claim: the full record
  is **386 daily ops 1991-05-13→2026-05-06**.

## 3. Quote-orientation law (audit question 3)

- Sweep of all eight 6J scripts: `1/price` appears **only** in A1 reporting fields
  (`usdjpy_implied_*`, correctly labeled) — never inside any return, vol, drawdown,
  term-structure, event or CoT computation. Trend semantics correct (price-up =
  JPY-up); roll gap = new−old consistent with near<far; "long 6J = long JPY" applied
  consistently. **No inversion found.**
- Tick grid: `TICK=500` int-nano units used in every tick conversion I recomputed
  (pairs, roll gaps); independent gcd of all 2.84M closes = 500 nanos = **5e-7
  exactly**; 0 violations. **Respected everywhere.**

## 4. The 6AV3 contaminant (audit question 4)

- 1,237 `6AV3` rows exist only in `AV1B-O1M-6J-BACKFILL2` (2020-03-24→2020-07-13) —
  a foreign (AUD-family) outright inside the vendor's 6J response (my census
  reproduces the count exactly).
- Every dossier number flows through `6J_deep_lib.load_outright_1m()`, whose single
  filter `^6J[FGHJKMNQUVXZ]\d$` excludes `6AV3` (and the dash-joined spread legs),
  with an assert guarding the drop. The QA census counts the 1,237 separately.
  **No dossier number is affected.**
- Disclosure: the dossier §8 table already reports it ("1 stray non-6J symbol `6AV3`
  (filtered)") — file mtimes show the dossier (07:54) disclosed it *before* the
  integration scan (08:35); the scan's parenthetical "not in DEEP-6J's report" is
  inaccurate for the dossier as it stands. **No erratum needed for 6J on this point.**

## 5. Taxonomy / PIT (audit question 5)

- FACT/OBSERVED/POSTULATED/NOT_RUN tags present and used consistently; NOT_RUN
  register explicit (§9). Good.
- Strict-past verified in code: op-day baselines `shift(1).rolling(21).median()`;
  TR percentile over `[i-126, i)`; CoT z `rolling(150).shift(1)`; vol terciles use
  `hist = seg.iloc[:-1]`. Good.
- Publish-lag PIT statement present at every intervention use (§5 preamble, A4 JSON
  `pit_disclosure`, H5 "the LAG is the PIT constraint", §9 same-day-detection
  NOT_RUN). Good.
- No return-conditioned selection found; ex-post CoT anatomy explicitly labeled
  "description only". Good.
- Two PIT-adjacent defects found: the k=5 rule spec-vs-code mismatch (m-5) and the
  2022-09-20 held-chain session drop (M-5) — details below.

---

## Findings register

Severity scale: BLOCKER (invalidates dossier) / MAJOR (stated claim contradicted by
source or data; must be errata'd before downstream use) / MINOR (wrong label/number,
no downstream consequence) / NOTE (observation).

### BLOCKER — none.

### MAJOR

- **M-1. MOF normalized record is defective; in-window op count is 10, not 9.**
  300 of 386 official daily ops dropped by the nonprice normalizer (blank-month
  carry-forward failure), including the 2022-10-24 ¥0.73T op. Dossier FACT claims
  "81 ops", "9 JPY-buying ops in-window", and the §5 op-day table inherit the
  undercount. The dossier's two honesty labels adjudicate as: 2026-07-30 honest;
  2022-10-24 honest-as-stated but understated (explicit daily row existed in the
  archived CSV, not just the quarterly aggregate). Errata: correct op count + add
  the 2022-10-24 anatomy row; upstream: fix the normalizer and rebuild the parquet.
- **M-2. "Record speculator short −184,223 (2024)" is false.** Series record is
  −188,077 on 2007-06-26 — a value the dossier's own §6 lists ("2007 short-yen
  carry extreme −188k") two lines before calling 2024 "the record". Correct claim:
  deepest short since 2007 / 2nd-deepest in the 20-year series. (Record long
  +179,212 ✓; +363k single-year flip is the largest rapid flip, though the
  all-time trough-to-peak range 2007→2025 is 367k.)
- **M-3. OI-leads-volume magnitude wrong.** Fresh recompute: OI crossover leads the
  raw volume crossover by **1–3 calendar days (12/12, mode 2)**, not "3–7 days".
  The 4–7-day figure belongs to the lead over the **k=5 switch**, not over the
  volume crossover; headline 7, §4 and the H2 spec all state the wrong comparator
  (the dossier's own Sep-2026 exemplar — OI 09-08 → volume 09-11 = 3 days — already
  contradicts its own "3–7"). Direction (12/12 OI first) verified true.
- **M-4. H5 / headline-3 regularity overclaim.** "Every ≥3% zigzag DOWN leg
  2022–2026 terminated within 0–2 sessions of a MOF op / op-window" — actual:
  **4 of 14** legs (2022-10-20, 2024-04-26, 2024-07-10, 2026-07-28; the first three
  at +1 session, the last +2 from the unverified window). Ten legs end nowhere near
  an op (2022-07-14, 2023-03-08, 2023-06-29, 2023-11-13, 2024-08-15, 2024-11-14,
  2025-01-08, 2025-05-12, 2025-07-31, 2026-01-13). Headline 3's own list includes
  2024-11-14 (−11.4%) which has no attached event.
- **M-5. QA claim "16 missing weekdays = exchange holidays only" is false for
  2022-09-20 — an undisclosed held-rule artifact.** That Tuesday the exchange was
  open and the next quarterly (Z2) traded 125,303 lots over 1,357 bars, but the k=5
  rule still "held" the ceased U2 (its stale trailing-5 mean exceeded Z2's ramp),
  so the session silently vanishes from the 1,745-session chain — in the middle of
  the September-2022 intervention week; the 09-21 rolled return then spans two
  calendar days off a 97-bar stale U2 close. An inferred-pass QA attribution (the
  mission's cardinal sin). The vendor panel itself has no hole that day, so
  "zero genuine data holes" survives for the *panel*; the *chain* claim needs erratum.

### MINOR

- **m-1.** Op-day true-range range is 85th–100th pctile, not "94th–100th"
  (2026-05-04 = 0.849 — the ¥0.78T stealth op). Volume range 1.75–4.79× (stated
  "1.8–4.8×" — rounding).
- **m-2.** "−163,412 … 6th-largest short ever" — it is the **11th**-most-negative
  week of 1,082 (10 weeks lie below it: six in 2007, four in 2024).
- **m-3.** §4 pair-text endpoints wrong: sessions per pair **50–83** (stated
  50–78); per-pair median spread **−216 to −90 ticks** (stated −215 to −132; three
  pairs have medians −97/−93/−90).
- **m-4.** "the 21 depleted (<25% bars) sessions" — there are **20** (in the lane's
  own JSON and in my recompute).
- **m-5.** k=5 roll rule: code ≠ disclosed spec. Code labels day t's held contract
  using day-t volume (`held[t]` from trailing mean through t); dossier/A1 spec say
  "decided at session t close … new contract held from t+1". Quantified impact:
  max DD and cumulative rolled return are **bit-identical** under both variants
  (fresh sensitivity run), so headline numbers stand — but H1's "executable PIT"
  claim describes a rule the code does not implement; fix the text or shift the code.
- **m-6.** Era roll-gap ranges in headline 4 / H3 ("0.1–0.7% (2020–21)",
  "4.6–5.5% (2023–24)", "2.1–3.1% (2025–26)") match neither the per-year medians
  (0.52/0.13; 5.50/5.46; 2.87/2.42) nor the per-roll ranges (−0.44–3.95; 4.63–6.60;
  1.70–4.29). Regime-dependence conclusion itself is sound.

### NOTE

- **n-1.** 6AV3 contaminant fully excluded and (pre-)disclosed — no dossier number
  affected, no erratum needed (§4 above). The integration scan's "not in DEEP-6J's
  report" is stale w.r.t. the dossier as committed to the worktree.
- **n-2.** MOF header start "1991-04" unsupported by either source (record begins
  1991-05-13); with the CSV fix the count is 386 ops.
- **n-3.** BoJ 2026 titles ("Change in the Guideline" 2026-06-16 / 09-18) carried
  as v1-FACT with archive NOT_RUN — disclosed honestly in §5, §8 and the handoff.
- **n-4.** BoJ "54 decision dates" ✓; ~6 are roll-date/holiday NaNs, medians
  computed over the ~48 measurable days (values reproduce exactly).
- **n-5.** Handoff_DEEP-6J canonical: base `26d96eb4` = dispatch sha, `commit_sha
  null` explicitly disclosed with reason, changed-paths list matches worktree
  contents, known-limitations accurate (all nine verify against my findings).
- **n-6.** A1 "sign-match-trailing-50d" window includes the current day
  (contemporaneous, not strictly trailing) — trivial, descriptive only.

---

## Verdict

**PASS_WITH_REQUIRED_ERRATA.** BLOCKER 0 · MAJOR 5 · MINOR 6 · NOTE 6.

The dossier's computational core is trustworthy: every headline number family I
recomputed (all 8, from the raw vendor parquet with independent code) reproduces —
most to the 4th significant digit, several exactly. The failures are at the
claim layer: one upstream data defect (MOF normalizer dropped 300 official ops
including the in-window 2022-10-24 op), three false/overstated regularity or
record labels (CoT "record short", OI-lead "3–7 days", "every down-leg ends at an
op"), and one inferred-pass QA attribution (2022-09-20 "holiday"). Required errata
before any downstream use — especially anything consuming H2 (OI roll trigger) or
H5 (intervention-threshold history built on the "81-op" record): fix the MOF
source, correct the five MAJOR statements, and correct the six MINOR labels.
Nothing requires re-running the price-side pipeline; every corrected claim is
supported by numbers already in this audit's outputs.
