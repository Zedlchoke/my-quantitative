# SAMPLE_FEASIBILITY_MATRIX — successor_design_2026-10-02 v3 (F1 deliverable)

Produced by the sample-power/floor-causality review lane (read-only; the only
computation is journal-row counting and Poisson rate arithmetic — no
backtest, no PnL). All rates are measured on the EXPOSED PC12A window
(8 folds × 26w = 4y) and are therefore **priors, not promises**.
**Model-based estimates (round-4 correction):** every P(unmet) below is
computed under a Poisson independence assumption; clustering /
zero-inflation (noted per row) make the TRUE P(unmet) uncertain in EITHER
direction at a given threshold (dependence can raise or lower tail
probabilities depending on threshold vs cluster size) — the figures are
ordering guidance for feasibility, NOT bounds. **Denominators are frozen
per estimand:** repeated decisions are not independent trades; the campaign
≥20/3/100 floors carry their exact law and unit, and NO denominator is
re-denominated (no entry→decision, no per-leg→battery switch) to make any
floor pass. **No floor is loosened anywhere in this matrix.**

Arithmetic base `[M: analysis/census.json, B1 nonzero-vote decisions / 8
folds]`: S026 946 → 118.25/fold · GBP-S002 245 → 30.625 · S014 144 → 18.0 ·
S013 119 → 14.875 · S009 63 → 7.875 · S046 47 → 5.875 · S003-JPY 47 → 5.875
· S002-JPY 41 → 5.125 · S017 39 → 4.875 · VC2-EUR 37 → 4.625 · VC2-JPY 21
→ 2.625 · S023 8 → 1.0. LEARN 26w = 1 fold-rate; LEARN 39.86w = ×1.533;
validation pooled = 6 fold-rates. Docket priors: NY-longs 91/74; EUR-hour
trades 57/59; S017 28/39; S014 excursions 24/29; guard defers 331 (29
matched). Decision→trade conversion ≈ 2.5:1 (S009: 123 blocked decisions ↔
49 missed trades).

## The matrix

| # | hypothesis / arm | denominator & surface | rate /26w · /y | clustering | E[LEARN 26w · 39.86w · VAL 6×26w] | floors | P(unmet), Poisson | verdict → typed consequence |
|---|---|---|---|---|---|---|---|---|
| 1 | HN-1-JPY (NY-long block) | NY-long decisions, suppressed rows in validation journals (prior 91/74, min fold 5) | 9.25–11.4 · 18.5–22.75 | clusters on NY trend days; fold spread 5–15 | 9.3–11.4 · 14.2–17.4 · **55.5–68.3** | ≥3/fold, ≥20/window; LEARN grid ≥20 | per-fold <3: 0.5%; VAL <20: ~0; **LEARN ≥20 unmet 70–99%** | VAL FEASIBLE; **LEARN grid expected NOT_RUN_GRID_THIN** → collapse to frozen default (the POST_OUTCOME shape survives un-de-biased). Design change BEFORE registration: a family-level DESCRIPTIVE read on the pooled 2-symbol suppressed set may accompany — the pooled count (≈99.8 VAL) satisfies NO per-symbol floor, does not rescue either LEARN grid, and is NOT evidence for the shared mechanism (heterogeneity, per-symbol floor failures, cross-symbol dependency retained and reported per symbol) + pre-type the per-symbol LEARN collapse |
| 2 | HN-1-EUR (hour gate) | suppressed-hour trades (prior 57/59, 6/8 folds nonzero) | 7.1–7.4 · 14.25–14.75 | zero-inflated (2/8 folds zero) → Poisson optimistic | 7.1–7.4 · 10.9–11.3 · **42.75–44.25** | ≥40/window; LEARN grid ≥40 | VAL <40: **24–32%** (worse under zero-inflation); LEARN ≥40 ~100% unmet (even 2-symbol pooled ≈ 18.75/28.7 < 40) | BORDERLINE on VAL; STRUCTURALLY UNDERPOWERED on LEARN → pre-type NOT_RUN_GRID_THIN + the VAL NOT_RUN_THIN branch; a family-pooled DESCRIPTIVE read may accompany (satisfies no per-symbol floor; not shared-mechanism evidence) |
| 3 | HN-2 floors (per leg) | trailing decisions (ECO layer) + blocked-set P-MW/P-FA tables (trade-level ≈ decisions ÷ 2.5) | A.1 rates | floor blocks cluster at cold window starts; defers cluster in trends | per leg λ×6 pooled | 20/window, 3/fold; aggregate 100 (READING AMBIGUOUS — resolve at registration) | per-fold <3: VC2-JPY 51%, **S023 92%**; VAL <20: **S023 ≈100%, VC2-JPY 83%**, VC2-EUR 5%, S002-JPY 1.6%; aggregate-100 per-leg: 8–9 of 12 legs unmet | FEASIBLE for the vote-carrying core (S026, GBP-S002, S014, S013); pre-type S023/VC2-JPY NOT_RUN_THIN; declare the aggregate reading + the decisions→trades conversion BEFORE registration |
| 4 | SU-RS-G1 / S017 would-be book (via LORO(G1); LOL∖S017 ≡ SLATE) | would-be trades (prior 28/39) | 3.5–4.9 · 7.0–9.75 | weekly-clock sparse; stop-outs cluster in vol bursts | 3.5–4.9 · 5.4–7.5 · **21.0–29.25** | ≥50 per arm book (VAL) | VAL <50: **99.97–~100%**; EXPECTING 50 needs ≈ 10.3 folds ≈ 5.1y (expectation math, not a forecast) | **STRUCTURALLY UNDERPOWERED** — refutation cannot lawfully fire; pre-register expected close NOT_RUN_THIN; the retire rests on registration election + prior evidence alone |
| 5 | A-H1 / J3 admitted defers | admitted defers in guard-IN crossed arms (pool 331/296; matched proxy 29/4y) | all-defers 37–41.4 · 74–82.8; matched-proxy 3.6 · 7.25 | defers cluster serially in trends (trailing-spend persistence) | matched 3.6 · 5.6 · **21.75**; ∞-node 41.4 · 63.4 · **248** | ≥20/window, ≥3/fold; LEARN ≥20 | ∞ node: ~0 unmet. m∈{1.5,2.0}: **RESOLVED STATICALLY in round 4** — the committed histogram (`forensics/guard_spend_band_histogram.json`) shows all fired defers at r = spend/cap ∈ [1.00, 1.41], so {1.5, 2.0, ∞} admit identical defer sets (grid statically degenerate) | UPDATED → the grid is either re-anchored INSIDE [1.00, 1.41] (m=1.1 → 5%/27% firing; m=1.2 → 0%/15%; endogeneity/selection caveats) or collapsed to binary remove-vs-keep-at-cap (register A-H1); counts are decisions, not marginal PnL |
| 6 | HN-3 / LOL∖S014 (frozen membership diagnostic) | would-be S014 entries (prior 24/29); decision-unit upper bound 18.0/fold | entries 3.0–3.6 · 6.0–7.25; decisions 18.0 · 36.0 | monthly-clock sparse; regime-clustered; sign flips by attribution law | entries 3.0–3.6 · 4.6–5.6 · **18.0–21.75** | ≥20 pooled (VAL); ≥3/fold; campaign 20/3/100 | VAL pooled <20: **33–65% (coin-flip-to-likely-miss)**; per-fold <3: 30–42% → ~1.8 of 6 folds thin; EXPECTING 100 aggregate needs ≈ 27.8 folds ≈ 13.9y (expectation math) | BORDERLINE → freeze the evaluation UNIT now (decision unit: 108 pooled vs ≥20, comfortable; entry unit: coin-flip). Choosing the unit after seeing counts is outcome-shaped |
| 7 | LOL arms (A ×11 admitted / B ×5 live) | removed leg's would-be decisions (campaign floor) | A.1 | as row 3 | λ×6 pooled | ≥20/window, ≥3/fold; aggregate ambiguous | VAL ≥20 met ≥98% for 8 of 11 legs; **S023 0.0005% · VC2-JPY 17%**; VC2-EUR 95% | FEASIBLE for 8/11; S023 + VC2-JPY pre-typed NOT_RUN_THIN (Option B carries LOL∖S023 — 1 id/6 rows on a pre-known thin cell; the canonical v3 manifest keeps it only as declared-typed) |
| 8 | LORO arms {J1-JPY, J1-EUR, HN-2, G1, J3} | per-rule contrast surfaces | — | — | — | rows 1–5 floors | inherit rows 1–5 | J1-JPY feasible; J1-EUR 24–32% window risk; G1 structurally unmeasurable (row 4 — S017's only readable surface); J3 node-dependent |

| 9 | HN-5 USD-cluster cap (optional identity) | bind-rate of the cap (share of decision hours with net USD-factor exposure above the frozen multiple), not a count floor | n/a | exposure clustering IS the hypothesis | bind-rate bands preregistered (<5% vacuous / >50% gate-in-disguise) | anti-hypothesis bind-rate bands (design §2 Layer 3) | n/a (bind-rate, not Poisson count) | OUT-OF-SCOPE for count floors: feasibility is the preregistered bind-rate band itself, evaluated on the LEARN exposure distribution at FREEZE-2; a vacuous or gate-like bind auto-refutes per its own anti-hypothesis |

**Cross-cutting (resolve at registration, none is a floor change):** the
campaign aggregate floor's two readings give OPPOSITE verdicts — per-leg:
8–9 of 12 legs expected NOT_RUN_THIN_AGGREGATE on 6×26w; battery-pooled
(DAILY practice, 61 = 34+27): ≈ 1,318 expected, trivially passes. Declare
the reading; pre-type the losers.

## Floor-causality law (INF / ECO) — replaces the FLAT-law sentence

**The defect:** design v2 §1 said "a leg whose per-fold decision floor
fails is FLAT for THAT fold (DAILY precedent)". A per-fold floor is a
fold-TOTAL count knowable only at fold close; suppressing in-fold trades
with it is lookahead. **The cited DAILY precedent is PROVEN to have
implemented exactly that** (lane audit: the 24 BLOCKED_FLOOR rows exist only
in the two sub-3-fire folds, at mid-fold timestamps, reason text "leg below
the per-fold decision floor (>=3); leg FLAT for this fold", and the DAILY
journal schema carries NO trailing-count field — a lawful trailing rule
would have blocked early decisions in ≥3-fire folds too). **IMPACT_ON_VERDICT_NOT_MEASURED
(round-4 correction):** counting the suppressed fires (3 would-be market
fires across arm-replays) does NOT bound the full-path effect —
netting/state/caps/cost amplification could scale it either way and no
replay or bound exists. The DAILY terminal verdict STANDS as recorded; this
note QUALIFIES its reliability on the floor-eligibility mechanics
specifically — it neither overturns nor re-affirms the PnL read. An
append-only incident erratum on the DAILY side is PROPOSED as an owner
action (protocol §1.1), not executed here.

**Layer INF — inference floors (fold-total; fold-close only).** Inputs are
fold-total/window/battery counts computed by a separate fold-close pass.
INF TYPES conclusions (`NOT_RUN_THIN` fold/window,
`NOT_RUN_THIN_AGGREGATE`) and restricts claims for that cell. INF may not
create, suppress, resize, defer, or relabel ANY trade; journals and PnL run
unchanged; INF outputs never enter the order path and never feed Layer ECO
in-cycle. No retroactive zeroing of any fold, ever.

**Layer ECO — economic-eligibility floors (trailing-only; PIT at decision).**
Any trade-suppressing floor is a pure function of journal rows with
`ts < decision_ts` (e.g. trailing-26w decision count) plus
registration-frozen constants: window length, count definition, SEEDING LAW
(may the trailing window read LEARN/prior execution history; the cold-start
verdict at the calendar's first decision — frozen, no longer unspecified),
thresholds, per-leg clock expectations. The computed count and verdict are
journaled per decision PRE-order-emission; the row joins the prefix for
later decisions. PC12A's `decision_count_trailing` field is the ECO-shaped
precedent.

**Pseudo-code** (testable):

```text
# INF: at fold close ONLY — read-only typing
function inf_fold_close(fold_rows, window_rows, battery_rows):
    for leg: if count(fold_rows, leg) < 3:  type[leg][fold]   = NOT_RUN_THIN
    for leg: if count(window_rows, leg) < 20: type[leg][window] = NOT_RUN_THIN
    if aggregate(battery_rows) < 100: type[battery] = NOT_RUN_THIN_AGGREGATE
    return types            # attach to report rows only; touch no trade

# ECO: at each decision t, BEFORE order emission
function eco_floor_at(t, leg, journal_prefix):        # prefix = rows with ts < t ONLY
    n_trail = count(journal_prefix, leg, DECISION, ts in [t-26w, t))
    verdict = (n_trail >= threshold_frozen[leg]) ? ELIGIBLE : OFF_DEFER
    append(journal_prefix, {ts:t, leg, trailing_count:n_trail, threshold, verdict, prev_row_sha256})
    if verdict == OFF_DEFER: emit BLOCKED_FLOOR row; no order
    else: emit order
```

**Truncation-replay test spec (design only; the successor engine must
implement and A7 prelaunch must pass it):**
- **T1 prefix-identity:** replay truncated at each t (population: all
  BLOCKED_FLOOR rows + first/last decision per leg per fold) —
  `eco_floor_at(t)` byte-identical to the full-stream computation restricted
  to rows < t.
- **T2 future-mutation invariance:** delete one decision with ts > t (one
  per future fold per leg); all ECO outputs at ts ≤ t byte-identical,
  hash chain up to t unchanged. Any change = STOP-3.
- **T3 INF/ECO separation:** no journal `blocked_reason_detail` references
  fold totals (string contract); fold typings live only in metrics/report;
  recomputing with INF disabled yields an IDENTICAL trade book.
- **T4 cold-start determinism:** replay from empty prefix reproduces the
  frozen seed law's verdicts deterministically.

Engine obligations: floor fields in `journal_row@1` successor emitted
pre-order; truncation harness; mutation harness; INF in a module with no
write access to the order path (interface-enforced).

— end matrix —
