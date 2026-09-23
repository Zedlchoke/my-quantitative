# A4_VERDICTS — adversarial killer lane, BTC-BEAR-OPPORTUNITY-RECON

lane A4 (killer) · 2026-09-23 · measured from bytes; heavy lock NOT acquired
(held by CRYPTO-HISTORICAL-REPLICATION-3F-V1 pid 77456 at start; light-job law
obeyed: 72.4 MB downloads + sub-5-minute CPU compute steps; no §8 exemption
used). All artifacts in this directory; no writes outside it and
`../handoffs/handoff_killer_a4.json`; no git commits.

**Headline: BOTH PROPOSALS VETOED. Honest close = NO_ELIGIBLE_PROPOSAL.**
No cycle P3 is warranted; there are no arms to freeze.

---

## 0. Measurement base (re-measured, not inherited)

- Frozen PSV1 H4 panel re-derived exactly: phase label reproduction matches
  `labels_frozen.parquet` on **14742/14742 bars**; census aggregates
  reproduced to the digit (DOWNTREND 2932 / 0.200973; SMA200-lens 6772 /
  0.464185; agreement 0.7365; containment P(DT∧¬lens)=0.000137,
  P(lens∧¬DT)=0.2633 — A3's identity inputs confirmed).
- 5m panel built from data.binance.vision (PIT_USABLE per A2): um klines +
  markPriceKlines + indexPriceKlines 5m, monthly 2020-01→2026-08 (80×3) +
  daily tail 2026-09-01..22 (22×3) = **306 files, 72.4 MB, 0 missing**;
  merged 702,706 bars, no nulls; 13 non-5m grid steps (largest holes
  2021-07-24..27 (1152 bars), 2022-07-25/28 (576×2) — interior archive
  holes; no θ-events lost).
- funding class-8 shadow from A2's own `funding_events.parquet`
  (7,643 settlements, sha-pinned archive).
- Class-2 shadow trigger taken VERBATIM-form from the PSV1 freeze
  (`lane-btc-h1/code/proposals.py`: entry = close < PRIOR 480-bar min of
  lows while state==DOWNTREND), mapped to H4 (120-bar lookback = same 20
  days) and 5m (5760 bars).
- Class-9 LIQEPIS definition form NOT findable (crypto-V13 worktree is
  cleaned; only ledger rows survive) → declared fallback used, disclosed:
  **20-bar drawdown > 15% event flag**, computed at each decision frequency.

## 1. C1+C4-POWER — PROPOSAL A reconstruction ("Confirmation-Lag Front-Run")

Mechanical state machine exactly per proposals.md (edge-triggered
SMA200-down ∧ label-not-DOWN; re-arm requires conjunction false ≥1 bar;
K_ABANDON=12; H_HOLD=6; invalidation exits; descriptive only, no costs):

| A3 claim | Measured |
|---|---|
| "~≤59 events per 6.5y … churn ≈ 12 bps/event" | **284 edge-triggered entries** (4.8× the claim). Cumulative round-trip drag 284×12 bps = **34.1% of notional** vs ~0.7% implied by A3's arithmetic. |
| "event supply 40–59" | **34 confirming** episodes / **250 fake-outs** (88% of entries never see the compelled flow) |
| floor: <30 confirming ⇒ NOT_RUN | 34 ≥ 30 — floor technically met, barely; A3's own claimed range was wrong |
| kill (ii): median confirmation lag <1 bar | NOT fired — median lag fill→confirmation **3.5 bars** (14h); lens-onset→confirmation median 26.5 bars |
| kill (iii): fake-out arm same drift | NOT decidable pre-PnL — gross DESCRIPTIVE_EVENT_STUDY: confirming +2.81%/event vs fake-out −0.40% (diff +3.21pp), **but the comparison is contaminated by construction**: fake-out exits (lens-flip/abandon) are *triggered by up-moves*, so the arm difference is exit-rule-asymmetric drift, not evidence of forced flow. Adjudication-relevant only inside a scored run. |
| kill (iv): rho vs class-2 > 0.20 | NOT fired: Pearson −0.009, event-conditional +0.13/+0.14 (see §3) |
| kill (v): owner rejects TRANSITION_UNKNOWN deviation | open owner decision; no fallback exists (A3's own words) |

**Mechanism attack verdict (C4): FICTIONAL_COUNTERPARTY.**
- The WHO of A's forced-flow story is "any book whose state variable IS the
  frozen PSV1 DOWNTREND label". That label is a **program-internal
  construct** (PSV1 plan §5, born in this repo, its own label-conditioned
  cells closed REJECT in PHASE-STRATEGY-V1/RSM-V1). No external market
  participant is compelled by it; the only label-following capital in
  evidence is this program's own, dead and forbidden (class 1).
- The parenthetical "SMA-lens siblings" imports external SMA books, but A's
  entry bar *is* the SMA-flip bar (first bar of the conjunction is usually
  the lens flip: rho vs lens-down flag +0.151) — A does not front-run those
  books, it **is** one of them (class-1/2 regime-flip short in new words),
  with the differentiating parts being exactly the fictional-cohort
  countdown machinery.
- **G6 block-shuffle evidence on this same label**: PHASE-STRATEGY-V1
  measured BTC_H4-DONCHIAN +177,692 losing to its 30-bar block-shuffle
  control +190,392 ("phase TIMING carries no information") and
  BTC_H1-DOWN −44,486 control-killed by the shuffled median. A's entire
  edge is label-timing information (a countdown to the confirmation
  instant). The program's own control apparatus already measured that
  information content as absent on this label, on this panel, at this grid.
- The TRANSITION_UNKNOWN deviation (holding through a 43.7%-of-window
  uncertain state, vs A3's prose "44.6%") is the mechanism's load-bearing
  crutch: 250/284 episodes are held through uncertainty that never
  resolves to DOWN.

**VERDICT A: VETOED_FICTIONAL_COUNTERPARTY** (mechanism layer), with
supporting findings: event-supply/cost misdeclaration (284 vs ≤59), program
G6 timing-information kill on the same label, class-1/2 regime-flip residual
identity. Rho caveat recorded honestly: under a Pearson-only full-grid
reading A passes every measured shadow (max |rho| 0.151); the event-
conditional Spearman loadings (displacement 0.73, label 0.55, LIQEPIS 0.28,
run-imbalance 0.42) are tie-degenerate on a 98%-zero series and are recorded
as corroboration, not as the primary ground. A3's own preregistered kill
list (i)/(ii)/(iv) does NOT fire — the veto is a mechanism veto, which is
the correct layer for a pre-PnL killer lane.

## 2. C1+C2+C4-POWER — PROPOSAL B reconstruction ("Mark-Trigger Catch-Down")

Signal S_t = (mark_close − last_close)/index_close; θ=0.12% for 2
consecutive closes; PIT DOWNTREND gate (H4 label usable after its close);
T_MAX=144×5m. Raw spread series recorded (mean +1.3e-5, p50 +1.5e-6, p99
7.3e-4, autocorr lag-1 **0.63** — a slow state, not an event clock).

| quantity | measured |
|---|---|
| raw 2-close θ-signals | 425 |
| in-gate θ-signals | **350** (A3 floor "N<40 ⇒ NOT_RUN" nominally met) |
| **independent events** (merge gap ≤12h = T_MAX scale) | **13 clusters; 96.3% of events within 12h of the previous; top-1 cluster = 319 events = 91.1% of all events; top-3 = 95.1%** |
| what is the top-1 cluster | **2020-03-12 → 2020-03-20 (COVID), 7.6 days**. Remainder: 2021-05 (Luna), 2022-01/05/06, 2026-02-06 (single). θ-event share by year: 2020 1.04% → 2024-25 **0.02%** — the phenomenon is extinct in the modern regime |
| half-life (A3 kill (i): <2 bars ⇒ untradable) | median **4–5 bars** (20–25 min) from θ-crossing; **15 bars** from confirmation; survival P(S>0) ≈ 0.80–0.83 even 144 bars after crossing. Kill (i) does NOT fire — the spread is grid-tradable. |
| **DESCRIPTIVE_EVENT_STUDY** (labelled; no fees/funding/book) | traded arm short forward return: **mean −4.87%, median −1.58% per event** (the short LOSES); excluding the COVID cluster still −1.54%/−1.33%; exit-per-rules mean hold 24.8 bars |
| matched neighbour control (in-gate r5m ≤ −0.30% crashes, S<θ, n=12,753) | control short forward ≈ −0.04%…−0.22% ≈ flat. **Traded − control: −0.95pp (H=1h), −2.79pp (H=3h), −2.89pp (H=12h)** |
| 350 matched pairs (±7d, nearest \|r5m\|) | paired diff mean **−4.55pp**, median **−2.14pp**, traded worse in **68.6%** of pairs |
| bounce contamination | 48.6% of signals occur after a POSITIVE 2-bar open move — the wide spread is a *stale/squeeze* state, not a pending-liquidation clock |

A3's preregistered prediction: "wide-spread (traded) events drift further
down post-entry than matched narrow-spread events; if both behave
identically, … kills the mechanism." **Measured: the opposite sign — the
wide-spread arm is 2–5% WORSE than control.** A3's declared failure mode
"wide-spread events are squeeze ignitions that resolve UP, flipping
conditional sign" is exactly what the data shows, before any PnL.

**Cost survival arithmetic (C4)**: entry θ = 12 bps (one round trip); ≤2
funding settlements per hold (mean +0.37 bps received, 24.7% negative,
−30 bps cap tail). For G1 to be arithmetically possible the event study
needs gross drift > ~12 bps + funding allowance ≈ +12…+42 bps/event.
Measured: **−487 bps mean / −158 bps median gross of all costs.** Dead by
roughly 10–40× the cost floor, before a single fee is applied.

**Mechanism attack (C4)**: on Binance, mark = index + smoothed basis is the
liquidation *trigger*, but forced IOC orders execute against the LAST-price
book — the forced flow is spent *while* the crash drives mark down through
liq prices, i.e., during the same bars that widen nothing (mark falls WITH
last). A persistently wide (mark − last) after the next-open fill means the
trigger surface is stale relative to the tape — precisely when remaining
longs are *not* being forced (their mark-triggered liq prices already
crossed) and mean-reversion/squeeze flows dominate. The strongest
alternative explanation — short-horizon momentum continuation after 5m
crashes — is what the neighbour control was built to separate; the control
MOVES the signal (Q-11 satisfied: −0.95pp at 1h, −2.9pp at 12h, p<0.001 by
sign test 68.6% worse), and it moves it in the **anti-mechanism direction**.

**Ancestry (C3)**: entries vs the class-7 dead-adjacent premium-basis
ancestry (V14 BASISLV-PREMFADE, ANCESTRY_TABLE #7 "same-mechanism
re-parameters are NOT new"): premium-fade entry representation rho
**+0.369 full / +0.542 event-conditional**; premium LEVEL −0.418/−0.515;
construction identity: S vs (premium − 12h-EMA premium) Pearson **−0.68**
— S is substantially repackaged fast premium/basis dislocation, the exact
observable of the dead near-miss family. Class-9 declared main risk:
0.168 (below bar). Class-2: 0.023 (clean). Classes 5/13: ≤0.12 (clean,
as A3 predicted). Textual-identity note: B self-describes as harvesting a
"liquidation cascade leg" — the V17 OICASCADE ancestry (#3) was killed by
randomized-event-time sham out-earning; the measured 91%-one-episode
clustering reproduces the same disease (event clock ≈ two cascade weeks).

**VERDICT B: VETOED — three independent measured grounds**
`VETOED_DESCRIPTIVE_EVENT_STUDY_SIGN_FLIP` (preregistered kill (iii)),
`VETOED_POWER_INDEPENDENT_EVENTS` (kill (ii) on the census independent-
episode convention: 13 clusters < 40), `ANCESTRY_VETO` vs class-7
premium-basis shadow (0.369–0.542 > 0.20; kill (iv) fires on class-7
rather than the declared class-9 — the CNG4 lesson repeated: the kill
found the real ancestor, not the declared one).

## 3. C3 rho table (same-representation convention; full |rho| > 0.20 ⇒ veto)

### Proposal A — H4 entry series (284 events / 14,589 bars)

| shadow (class) | full Pearson | full Spearman | event-cond ±12 bars (P / S) |
|---|---|---|---|
| SMA200-down lens flag (1/2 core) | **+0.151** | +0.151 | +0.188 / +0.188 |
| DOWNTREND label flag (1) | −0.071 | +0.281* | −0.120 / +0.548* |
| breakdown DT-label+120-bar-low (2, PSV1-H1-480 mapping) | −0.010 | +0.496* | +0.009 / +0.141 |
| breakdown edge (2 entry repr) | −0.009 | +0.433* | +0.008 / +0.129 |
| LIQEPIS proxy 20-bar-dd>15% (9, declared) | −0.004 | +0.716* | +0.007 / +0.282* |
| down-displacement 5-bar<−2σ (5 CDF proxy) | +0.030 | +0.828* | +0.043 / +0.726* |
| rev24 = −ret24 (5 CNG4 leg) | +0.025 | −0.027 | +0.014 / −0.031 |
| funding LEVEL ffill (8) | 0.000 | NA | 0.000 / NA |
| run-imbalance 24-bar (13) | −0.034 | +0.241* | −0.024 / +0.416* |
| premium LEVEL (7 dead-adj) | −0.026 | −0.037 | +0.018 / −0.073 |
| premium-fade entry \|z\|>2 (7 repr) | −0.007 | +0.621* | +0.026 / +0.607* |

\* Spearman on a 98%-zero binary series is tie-degenerate (value is
tie-handling-sensitive); recorded for completeness. **Honest reading: A
passes the rho bar under the Pearson full-grid program convention (max
0.151); it accumulates >0.20 loadings only under the SNG6-style
event-conditional Spearman reading. A's veto does NOT rest on rho.**

NOT_MEASURABLE_PRE_PNL for A: class-6 DVOL/vol-shock (no DVOL source
exists in the Binance Vision PIT_USABLE set; shadow defined in V16/NG1
freeze inventories, e.g. `generic_dvol_shock` — CNG1-A4-P1 was killed
0.4409 vs it) — judgment: **elevated** (A's entries sit inside
down-displacement neighborhoods, event-cond Spearman 0.73 vs the
displacement proxy, and crash-window vol states are the same
information). Classes 3/4 OI (only source is RETROSPECTIVE_ONLY 5m
metrics from 2020-09; shadows `v17_oi_level`/OITD in V13/V17 freeze
inventories): judgment low-moderate for A (no OI feature). Class 10
taker (shadows defined on the daily/H1 planes in V15/V16/V17
inventories): per dispatch, not measured; judgment low for A.

### Proposal B — 5m gated entry series (350 gated events / 702,706 bars)

| shadow (class) | full Pearson | full Spearman | event-cond ±36 bars (P / S) |
|---|---|---|---|
| DOWNTREND label PIT gate flag (1) | UNDEFINED (gate constant within event windows) | — | — / — |
| breakdown DT-label+5760-bar-low (2, declared mapping) | +0.023 | +0.023 | +0.045 / +0.045 |
| LIQEPIS proxy 20-bar-dd>15% @5m (9, declared) | +0.168 | +0.168 | +0.142 / +0.142 |
| down-displacement 1-bar<−2σ (5 CDF proxy) | +0.003 | +0.003 | −0.000 / −0.000 |
| rev24 @5m (5 CNG4 leg) | +0.075 | +0.021 | +0.119 / +0.117 |
| funding LEVEL ffill (8) | −0.000 | NA | −0.000 / NA |
| run-imbalance 24-bar (13) | −0.014 | −0.014 | −0.065 / −0.067 |
| **premium LEVEL (7 dead-adj, V14 lineage)** | **−0.418 VETO** | −0.075 | **−0.515 / −0.454 VETO** |
| **premium-fade entry \|z\|>2 (7 repr)** | **+0.369 VETO** | +0.369 | **+0.542 / +0.542 VETO** |

Construction identity: S vs (premium − 12h-EMA premium) Pearson **−0.684**;
S vs premium LEVEL **−0.616/−0.565**. The "contractual trigger surface" is
substantially the dead near-miss family's own observable, high-pass
filtered.

NOT_MEASURABLE_PRE_PNL for B: classes 3/4 OI (RETROSPECTIVE_ONLY; V17
`v17_oi_level`, V13 OITD freeze inventories) — judgment **high textual
loading** (B self-identifies as cascade harvesting; #3 OICASCADE was
killed by sham-event-timing, the same disease measured here as 91%
single-episode clustering). Class-6 DVOL/vol-shock (no DVOL in the
keyless set; NG1/V17 inventories) — judgment high (θ-events are
definitionally crash-vol events). Class 10 taker (V15/V16/V17 daily/H1
inventories; not measured per dispatch) — judgment moderate-high
(cascade events are taker-sell saturation events by construction).

## 4. C5 — FINAL ADJUDICATION INPUT

```
Proposal A ("Confirmation-Lag Front-Run"):
  VETOED_FICTIONAL_COUNTERPARTY
Proposal B ("Mark-Trigger Catch-Down"):
  VETOED_DESCRIPTIVE_EVENT_STUDY_SIGN_FLIP +
  VETOED_POWER_INDEPENDENT_EVENTS + ANCESTRY_VETO (class-7, 0.369–0.542)
```

**Recommendation to owner: NO_ELIGIBLE_PROPOSAL. Do not open cycle P3 for
either proposal.** Under the max-6-arms law the question of which arms to
freeze is moot — zero anchors survive pre-PnL; there is nothing to
neighbour, placebo, or baseline (CASH / simple-short-in-DOWNTREND / trend
risk-off analogue are all already-published dead baselines on this same
label per PHASE-STRATEGY-V1 and the class-1 ancestry). The bear-side short
sub-family on this panel is now measured-closed at the mechanism layer:
the regime label carries no timing information (program G6), the label
cohort is internal (fictional counterparty), and the mark-spread
"pending liquidation" clock measurably runs backwards (wide spread = stale
trigger/squeeze, the short loses 1.5–5% per event gross).

## 5. Incidents / disclosures

- LOW — census `label_occupancy_all_phases_window.TRANSITION_UNKNOWN=6506`
  (44.6%, quoted in A3 prose) vs **6371 (43.7%)** recomputed from the
  frozen labels my reproduction matches exactly (14742/14742). The other
  four label counts in that census block match. Non-load-bearing: the
  containment identity inputs (0.200973/0.464185/0.736) all reproduce.
- LOW (finding, not incident) — A3 Proposal A event-supply claim (≤59,
  "every label onset passes through the pre-state") is contradicted by
  mechanical reconstruction under A3's own re-arm law: **284 entries**;
  its cost-survival arithmetic (churn ≈ 71 bps cumulative) understates
  fee drag ~48× (34.1% cumulative at 284×12 bps).
- INFO — Binance Vision 5m file naming is `BTCUSDT-5m-{YYYY-MM}.zip` (no
  family infix; the `fundingRate`-style infix pattern 404s); 75–78 of 102
  files carry header rows; loader handles both. Concat digests recorded
  (kl d8b3bdcc82523426, mk cbb65a0364be22c6, ix 5ceb8277ea9197bd,
  order-pinned, in `dl5m/`).
- INFO — 13 non-5m grid steps; largest interior holes 2021-07-24..27
  (1152 bars) and 2022-07-25/28 (576×2); no θ-events lost.
- Lock discipline: `locks inspect` run first; heavy lock held by
  CRYPTO-HISTORICAL-REPLICATION-3F-V1 (pid 77456) the whole session; never
  acquired; all compute light (<5 min/step; no getrusage §8 exemption
  needed); downloads 72.4 MB < 200 MB.
- Outcome-blindness is N/A for this lane by design (killer may read
  failure memory/ledgers/terminal reports); no scored PnL was computed
  anywhere; every forward-return number is labelled DESCRIPTIVE_EVENT_STUDY.
