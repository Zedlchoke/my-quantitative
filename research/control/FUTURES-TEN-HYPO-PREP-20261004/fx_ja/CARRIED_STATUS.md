# CARRIED_STATUS — 6J/6A hypothesis families carried into FUTURES-TEN-HYPO-PREP-20261004 (lane FXJA)

- Task: **FUTURES-TEN-HYPO-PREP-20261004**, lane **FXJA**. Generated 2026-10-04
  UTC. Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-ten-hypo/prep`
  @ HEAD **`a4a882658e09092b5b282b666b30a3cfc5ac3418`** (single permitted
  `git rev-parse HEAD` at lane start; == dispatch base). Branch
  `prep/futures-ten-hypo-20261004`.
- Class: PREP carried-status register. **0 PnL, 0 returns, 0 scored runs, 0
  sweeps, 0 selection by any return statistic. Outcome-blind. Missing evidence
  is NOT_RUN, never PASS.** Every parameter **[PROVISIONAL]**. No registration,
  no trial creation, no budget request.
- Purpose: record the STATUS of every family this lane must carry (not
  duplicate), and the BLOCKERS each still faces, after rounds
  FUTURES-OVERNIGHT-PREP-20261003 (JF1-3/AF1-3 + PB3 park law + K0),
  FUTURES-SIX-READINESS-20261004 (6J/6A data readiness: tick eras, k=5 rolls,
  cease-guard pathology, event PIT) and FUTURES-SIX-ADOPT-PREP-20261004
  (AF4 + RMM). **No spec is changed by this document.** All specs of record:
  `FUTURES-OVERNIGHT-PREP-20261003/hypo/6j_6a/JPY_AUD_HYPOTHESES.md` (JF/AF
  11-field specs) and `FUTURES-SIX-ADOPT-PREP-20261004/hypo/HYPOTHESES_R2.md`
  (R2-F1 RMM, R2-F2 AF4).
- Standing rulings restated, never reopened: **PB3 PARK for 6A** (0 budget;
  every 6A line below is contingency bookkeeping); **6J has NO trial cap
  defined** (explicit owner ceiling required before any 6J registration);
  **6A tick era law** ($10.00/tick ≤2020-11-20, $5.00/tick ≥2020-11-23;
  era-1 = 231 sessions = descriptive-only stratum, fold floor fails);
  **6J orientation PROVEN** (USD-per-JPY, up = yen strong); **6J volume
  0.455× law** (shares/ratios only, never absolute levels); **BoJ intraday
  decision stamps NOT_IN_CORPUS** (owner decision pending — no minute-anchored
  BoJ refinement possible beyond JF1's window convention); fees **MODELED /
  VERIFIED_VS_ACCOUNT=NOT_RUN / UNDER REVIEW** until owner-authorized A7 (D2);
  **BBO NOT_RUN** (D5); ABS/China calendars **NOT_RUN** (AF3 K4 alive);
  cease-guard exemplars 6J 2022-09-20, 6A 2024-12-17 + 2026-06-16 (extremal
  stratum, descriptive-only, n=3); D1-D12 all open; **DC §1.3: construction ≠
  alpha** (roll-gap/CIP structural inputs, never signals).

## PART I — 6J (secondary symbol; gates open)

### JF1 — BoJ MPM Decision-Window Resolution — CARRIED, spec unchanged
- Status: PREP-complete (11 fields, JPY_AUD_HYPOTHESES §1); measured anatomy
  on-symbol multi-era (54 MPM days; median |ret| 0.568% vs 0.304% = 1.87×;
  window 1m volume 34 vs 53 full-day = 35.8% thinner) [OBSERVED,
  `6J_a4_events.json:boj_mpm_vs_alldays`, `6J_a2_sessions.json:
  boj_decision_window`]. Provisional 5-dim program score (this lane, §6 of
  HYPOTHESES_FXJA_R3.md): **D1=3 D2=2 D3=2 D4=2 D5=2 → 11/15**.
- Blockers (unchanged): (i) BoJ statement **intraday timestamps
  NOT_IN_CORPUS** — the 12:00–15:30 JST anchor stays a declared window
  convention; owner decision pending on stamp acquisition; K3
  anchor-robustness law binds (`ja_event_pit.json:boj.timestamps`);
  (ii) surprise classification NOT_RUN (no consensus/pricing series);
  (iii) fees UNDER REVIEW (A7/D2); BBO NOT_RUN; (iv) **no 6J cap defined —
  owner ceiling required** before any registration; (v) the MPM regime-change
  subset (4 measured + 2 v1-FACT titled dates) is descriptive-only forever
  (fold floor fails, n=6-7).

### JF2 — MOF Intervention-Regime Conditioning (ex-post, lag law) — CARRIED, spec unchanged
- Status: PREP-complete (JPY_AUD_HYPOTHESES §2); 386-row MOF tidy
  SOURCE_TIDY_RESOLVED on disk (ERRATUM M-1 upheld); 10 disclosed in-window
  ops 2020-2026; 2026-07-30 window stays price-anatomy-only (NOT
  MOF-verified). Provisional 5-dim: **D1=2 D2=3 D3=2 D4=2 D5=1 → 10/15**.
- Blockers (unchanged): (i) threshold constant for any zone-distance label is
  an owner-gated PARAM-GAP (6J_DEEP §7-H5) — the base K=63 trailing-disclosure
  label needs none and is PIT-clean; (ii) only 10 in-window ops →
  power-marginal by construction; (iii) MOF Q3-2026 daily detail unpublished
  at data access; (iv) overlay law: 0 own identities; host floors apply.

### JF3 — Tokyo-Morning Session Structure — CARRIED, spec unchanged
- Status: PREP-complete (JPY_AUD_HYPOTHESES §3); strongest 6J measured
  anatomy (session extrema 18.1%/15.2% in tokyo_am; 11.0%/13.0% volume/range
  shares; depth 59-vs-120; era-stable) [OBSERVED, `6J_a2_sessions.json`].
  Provisional 5-dim: **D1=3 D2=2 D3=2 D4=3 D5=1 → 11/15** — note the D2=2
  under the program rubric's dead-corpus clause (Tokyo-session
  continuation/fade overlaps dead FXFV2-A4-P1's spot signal class); this
  divergence from the 3-axis MS=3 is disclosed in HYPOTHESES_FXJA_R3.md §6.
- Blockers (unchanged): (i) session-of-day-dependent cost model is a
  SPECIFICATION FLOOR (Tokyo-window fills carry the thinner-book slippage
  assumption); (ii) fees UNDER REVIEW; BBO NOT_RUN; (iii) 6J volume absolute
  levels forbidden (0.455× law) for any volume trigger; (iv) 6J owner ceiling
  required; (v) K2 live risk (RT 8.5–14.7 bp vs per-trigger scale).

## PART II — 6A (PB3 PARK — everything below contingency only, 0 budget)

### AF1 — RBA Decision-Minute Reaction — CARRIED (PARK), spec unchanged
- Status: PREP-complete (JPY_AUD_HYPOTHESES §4); strongest event anatomy in
  the lane (±5' 9.0× volume / 4.8× |ret|; change-vs-hold 59 vs 29 ticks;
  n=67). Provisional 5-dim: **D1=3 D2=2 D3=2 D4=2 D5=1 → 10/15**.
- Blockers: (i) **PB3 PARK** — owner ruling; (ii) **K0 thin-n kill
  pre-registered** (fold floor ≥5 fails at n=67; single-stratum or pooled-era
  only — inherited, not negotiable); (iii) ±5' scale 4.35 bp below one RT
  (8.2 bp) — power-starved, K2 expected outcome, stated honestly; (iv) RBA
  decision TIME not carried in-corpus (14:30-Sydney anchor = declared
  convention; `ja_event_pit.json:rba` has dates only); (v) tick-era law:
  era-aware cost mandatory if the 2020 stratum is ever touched (era-1 =
  descriptive-only); (vi) round-1 closed AF1's two data gates (k=5 MEASURED;
  tick RESOLVED_PER_ERA — `6a_roll_measured.json`, `6a_tick_adjudication.json`)
  — those gates are CLOSED, the park is not.

### AF2 — RBA-vs-Fed Differential Regime Conditioning (overlay) — CARRIED (PARK), spec unchanged
- Status: PREP-complete (JPY_AUD_HYPOTHESES §5); H-F/H-G law binding
  (conditioning INPUT, never carry harvest; 0 own identities). Provisional
  5-dim: **D1=2 D2=2 D3=2 D4=1 D5=1 → 8/15** (D4=1: DFF latest-vintage
  conditioning, NOT PIT-strict; D2=2: the 5-dim dead-corpus clause —
  yield-exposure-form classes appear in the dead corpus as the CONTROLS that
  killed FXNG1-A4-P2 / FXFV8-A5-P1; disclosed).
- Blockers (unchanged): DFF year-end vintages only (no 2025); K2 vintage-flip
  test runnable from corpus, still NOT_RUN; block-shuffle placebo mandatory;
  PB3 PARK.

### AF3 — Bimodal US+Sydney Session Structure — CARRIED (PARK), spec unchanged
- Status: PREP-complete (JPY_AUD_HYPOTHESES §6); bimodal U-curve +
  hub-window shares measured all three eras. Provisional 5-dim: **D1=3
  D2=2 D3=2 D4=3 D5=1 → 11/15** (D2=2: Sydney-morning → US-rotation
  continuation/fade overlaps dead FXFV2-A4-P1's Tokyo-state→London-expansion
  spot class on the same pairs; disclosed — the 3-axis MS=3 divergence is
  mechanical, see R3 §6).
- Blockers (unchanged): **ABS/China calendars NOT_RUN keep K4 alive** (a
  trigger cluster inside 09:30–10:00 Shanghai kills the base spec); PB3
  PARK; tick-era law for any 2020 stratum (era-1 descriptive-only);
  fees UNDER REVIEW; BBO NOT_RUN.

### AF4 — Tick-Regime Conditioning (R2-F2, T3 overlay, 6A) — CARRIED (PARK), spec unchanged
- Status: PROPOSED in R2 (HYPOTHESES_R2 §3), not superseded. 0 standalone
  identities; hosts AF1/AF3 (both PARK ⇒ creates no budget surface). R2
  5-dim score **10/15** stands. The D8 era law it needs is now measured
  (`6a_tick_adjudication.json`; DATA_READINESS_6A Dim 1) but the D-2
  era-aware cost audit and the 6E/6B tick-constancy secondary control remain
  NOT_RUN.
- Blockers: PB3 PARK; era-1 231 sessions (fold floor fails — descriptive-only
  stratum, pre-declared); official CME rulebook page BLOCKED_TRANSPORT (label
  stays data-side/conventional); COVID confound on era-1 (6J same-date
  placebo is the load-bearing control).

## PART III — RMM (R2-F1) 6J/6A legs — CARRIED, spec unchanged

- Status: PROPOSED in R2 (HYPOTHESES_R2 §2), not superseded. Role A
  (construction ledger, 0 identities) + Role B (gated alpha leg, 4 IDs/leg,
  PROPOSAL; registration precondition = owner DC §1.3 boundary ruling). R2
  5-dim score **11/15** stands.
- 6J leg blockers: (i) 6J migration-mode classification NOT_RUN (Role-A
  derivation from committed switch tables is the first prep-legal step —
  mechanical, not done here); (ii) 6J cease-guard exemplar 2022-09-20 sits
  INSIDE the Sep-2022 intervention week — flagged stratum, never base;
  (iii) 6J owner ceiling required before any registration; (iv) fee A7/D2.
- 6A leg blockers: (i) **PB3 PARK**; (ii) tick-era law — 6A legs before
  2020-11-23 enter descriptive views only until the D-2 cost audit lands;
  (iii) the two 6A ceased-guard exemplar days (2024-12-17, 2026-06-16) are
  the extremal abrupt stratum, descriptive-only, n=3 (with the 6J day,
  pre-declared); (iv) mode × post-switch-drift interaction NOT_RUN (Role-A
  anatomy-first gate).

## PART IV — What this round changed (and did not change)

- **Changed**: nothing in any family spec. This round's outputs are (a) this
  carried register, (b) the R3 candidate adjudications (0 NEW, 16 vetoes /
  classifications, HYPOTHESES_FXJA_R3.md), (c) provisional 5-dim program
  scores for JF1-JF3/AF1-AF3 (RANKING_FRAMEWORK anchors — synthesis-lane
  input, PROVISIONAL), (d) two primary-source captures documenting two veto
  walls (RBA minutes cadence 8/year T+2wk; MOF JGB auction calendar public —
  `fetch_log.jsonl` + `captures/` + `SHA256SUMS_lane.txt`).
- **Unchanged**: every binding law listed in the header; every NOT_RUN in the
  standing register (JPY_AUD_HYPOTHESES §8 + HYPOTHESES_R2 §9); PB3 PARK; 6J
  no-cap; NO_GO_REGISTER / NO_GO_SCORE / NO_GO_ORDER.

— End CARRIED_STATUS. Zero PnL entered any cell; specs untouched; missing
evidence is NOT_RUN, never PASS.
