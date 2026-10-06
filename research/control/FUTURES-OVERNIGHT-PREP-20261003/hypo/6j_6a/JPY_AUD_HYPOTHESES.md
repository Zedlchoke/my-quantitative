# JPY_AUD_HYPOTHESES — 6J / 6A competing-hypothesis family portfolio (P1-6J6A)

- Task: `FUTURES-OVERNIGHT-PREP-20261003`, lane **P1-6J6A**, generated
  2026-10-04 UTC. Worktree HEAD at write: `72c9bc5b` (dispatch_sha ==
  actual_start_sha == `72c9bc5b1d94b812044a9bd21768c53b4d378436`; re-measured
  via `git -C` before writing).
- Class: PREP hypothesis dossier. **0 PnL, 0 scored runs, 0 sweeps, 0 selection
  by any return statistic. Outcome-blind.** Every parameter **[PROVISIONAL]**.
- **Symbol status laws**: **6J = secondary symbol** — the three open gates
  (quote orientation adjudication / BBO / cost) are stated per family and none
  is closed by this document. **6A = PB3 PARK** — everything below is PREP
  only: no registration, no budget, no scheduling proposal; the trial census
  in `RANKING_INPUT.md` §3 is **CONTINGENCY ONLY**.
- **INCIDENT (inherited partial)**: a previous attempt of this lane died
  mid-run leaving `captures/source_sha256.tsv` as a stale partial. All
  pre-existing files in this directory were treated as untrusted; the ledger
  was **REBUILT FRESH this session** (every hash recomputed at `72c9bc5b`;
  the inherited 18 hashes were incidentally hash-identical to the rebuild, and
  the rebuild adds `handoff_P0-VERIFY.json` + a provenance header). No other
  pre-existing file existed. Disclosed in handoff incidents.
- Evidence base consumed in full before writing (paths relative to
  `research/control/`; every one sha256-pinned in `captures/source_sha256.tsv`):
  `FUTURES-DEEPRESEARCH-V2-20261003/dossiers_v2/6J_DEEP_v2.md` (6J §n, errata
  M-1..M-5/m-1..m-6 applied), `.../6A_DEEP_v2.md` (6A §n, errata MINOR-1..3
  applied), the v2 analysis JSONs cited as `script:field`,
  `FUTURES-DATACONTRACT-QUAL-V1/DATACONTRACT_QUALIFICATION.md` (DC §n — §1.1
  identity, §1.2 local-clock law, §1.3 roll/cease-guard, §1.4 event PIT,
  §1.7 cost authority),
  `FUTURES-OVERNIGHT-PREP-20261003/fees_erratum/source/FEES_CORRECTED.md`
  (FEES §n — tier-1 all-in 6J/6A = **2.46 USD/side, corrected, upheld by
  P0-VERIFY**; MODELED COST; account NOT_RUN; UNDER REVIEW until a new A7;
  FX symbol-group mapping PARTIAL — 1 dated binding page pending),
  `.../cme_cal_gap/fx_comm/FXCOMM_GAPFILL_EVIDENCE.md` (FXCAL §n — FX
  expiries 208/272, 2010-2022 complete per symbol, 2023-2026 NOT_OBTAINED;
  FX holiday times 2017-2023 expanded),
  `.../bls_vintage/BLS_VINTAGE_INVESTIGATION.md` (BLSV §n — 2025-vintage
  law), `.../dispatch/handoff_P0-VERIFY.json` (fees upheld).
- **No web access was performed this session**: every new numeric below is
  quoted from the pinned local artifacts; there are therefore no new web
  captures, only the rebuilt source ledger.
- Taxonomy (labels used throughout): **FACT** (primary source + date) /
  **OBSERVED** (script + window on this panel) / **MECHANISM_HYPOTHESIS**
  (unmeasured mechanism) / **INFERENCE** (reasoning over measured inputs) /
  **DERIVED** (arithmetic from named measured inputs) / **NOT_RUN** (missing
  evidence is never PASS).

---

## 0. Portfolio overview — why these families genuinely compete

Six families: three per symbol. Each symbol gets **two session-window event
families + one regime/conditioning family**. Competition is enforced by
mutually exclusive day-sets and different clock anchors, not parameter
variation:

| id | name | symbol | window / anchor | mechanism class | relation to the other families |
|---|---|---|---|---|---|
| JF1 | BoJ MPM Decision-Window Resolution | 6J | 12:00–15:30 JST decision window (day-2 statement dates) | scheduled-uncertainty resolution in a thin US-overnight book | **JF3's base excludes these days** |
| JF2 | MOF Intervention-Regime Conditioning (ex-post) | 6J | disclosure-lagged regime labels from the 386-op history | official-risk regime changes hedging-flow asymmetry | overlay on JF1/JF3; same-day signal FORBIDDEN (lag law) |
| JF3 | Tokyo-Morning Session Structure | 6J | Tokyo 09:00–11:30 JST, Asia/Tokyo local clock | home-session information discovery vs fade | trades exactly the days JF1 stands aside |
| AF1 | RBA Decision-Minute Reaction (PB3 core) | 6A | 14:30 Sydney ±5' (as-published table) | decision-surprise resolution: drift vs spike-reversal | **AF3's base excludes these days** |
| AF2 | RBA-vs-Fed Differential Regime Conditioning | 6A | overlay; |Δ|≥25bp sign regime from roll-gap/CIP law | CIP structural INPUT conditioning (H-F/H-G law) — never carry harvest | overlay on AF1/AF3 |
| AF3 | Bimodal US+Sydney Session Structure | 6A | Sydney 11:30 modal peak + 19:00–20:00 CT secondary peak | two-hemisphere liquidity rotation | trades the non-decision session skeleton |

Genuine-competition proof [INFERENCE]: JF1 trades the 54 BoJ decision dates
and stands aside everywhere else; JF3 trades the ordinary-session skeleton and
excludes JF1's days; if JF3's measured effect were "really" an MPM-day
artifact, the exclusion test kills it (and vice versa — K1 below). JF2 does
not create a new window at all: it re-labels JF1/JF3's existing days by a
disclosure-lagged regime variable, so it can only survive if the regime split
carries information the pooled families lack. On 6A the same three-way
structure holds with AF1/AF3/AF2. None of this is disguised multi-trials of
one idea: the day-sets are disjoint or explicitly overlay-typed, and each
family's negative control (C3/C3') is the others' null.

Cross-venue tests are OUT OF SCOPE (sibling P1-CROSS owns them). Cross-venue
comovement claims (6E/6B/ES) appear only as declared NOT_RUN dependencies.

---

# PART I — 6J (Japanese Yen futures; SECONDARY symbol)

## Open gates on 6J, stated once and binding on all three families

1. **Quote orientation gate**: 6J = **USD per JPY** (price band 0.0061095 –
   0.0099205 across 2020–2026 absolute 1m extremes; 6J_DEEP §0 "orientation
   trap" is CONTRACT LAW here) [OBSERVED, `6J_qa_ledger.json` +
   `6J_a2_sessions.json:panel`]. **6J UP = yen STRONG; long 6J = long JPY /
   short USD; any "USDJPY-long" spot idea is a 6J SHORT** [DC §1.1]. Every
   direction statement below is written in 6J price terms. The gate remains
   OPEN in the sense that no scored engine has yet implemented + verified the
   orientation transform; a scored-cycle gate must re-adjudicate it.
2. **BBO gate**: true spread NOT_RUN everywhere (only close-proxy; DC §1.7).
3. **Cost gate**: fee layer corrected (2.46 USD/side T1) but UNDER REVIEW
   until a new A7; FX-group mapping PARTIAL (FEES §2 honesty note).

## 1. JF1 — BoJ MPM Decision-Window Resolution (drift vs reversal)

1. **Mechanism + microstructure** [MECHANISM_HYPOTHESIS]: BoJ policy decisions
   resolve scheduled uncertainty inside a continuously-traded 23h venue whose
   decision window is structurally thin. Two competing microstructure stories:
   **JF1-DRIFT** — the decision resolves a genuine uncertainty premium and the
   dispersed 23h crowd underreacts; late liquidity keeps processing for hours
   and price drifts in the decision-direction; **JF1-REV** — the first prints
   are a liquidity-hole overshoot in a book that is ~35% thinner than the
   full-day median, and arriving liquidity corrects them. The **execution-floor
   mechanism is measured**: BoJ window median 1m volume **34 vs 53 full-day**
   (35.8% thinner), 9.50% of session volume [OBSERVED,
   `6J_a2_sessions.json:boj_decision_window`; 6J_DEEP §3]. Event-day anatomy:
   MPM-day median |return| **0.568% vs 0.304% all-days (1.87×)**, median
   volume **1.27× vs 1.00×**, BoJ-window range share **13.43% vs 10.35%**
   baseline [OBSERVED, `6J_a4_events.json:boj_mpm_vs_alldays`; 6J_DEEP §5].
   Regime-change MPM subset (titled): 2024-03-19 (framework change), 2024-07-31
   (+1.77%, 2.68× vol), 2025-01-24 (+0.05%, 1.94×), 2025-12-19 (−1.41%,
   2.18×) [OBSERVED, `6J_a4_events.json:boj_mpm_days.is_regime_change`].
2. **Expected direction, falsifiable** [PROVISIONAL]: JF1-DRIFT —
   E[ret(14:30JST→session close) | sign of decision-window move] carries the
   same sign as the decision-window move (in 6J price terms); JF1-REV — the
   same conditional carries the opposite sign. The two arms cannot both
   survive; a zero both-arm result kills the family (K2). Conditioning set
   [PROVISIONAL]: (a) all 54 MPM days; (b) titled regime-change subset
   (n=4 measured + 2 v1-FACT 2026-06-16/09-18 — see field 3).
3. **PIT feature availability** — stated exactly as the dossier evidences:
   - **BoJ decision DATES**: FACT from the in-corpus statement archive
     (2011→2026-09-18; 54 decision dates 2020–2026 measured, "day-2
     statements" = decisions announced on day 2 of each 2-day MPM)
     [6J_DEEP §5, §8].
   - **BoJ statement INTRADAY timestamps: NOT evidenced.** The dossier
     records no minute-level release stamp for any statement. The
     12:00–15:30 JST "decision window" is a **window convention** — the
     Tokyo-afternoon block where decisions are known to land, measured via
     range-share concentration (13.4% vs 10.3%), NOT a minute-anchored
     release like FOMC's "For release at". Any scored spec must treat the
     window, not a minute, as the event anchor, or first acquire
     minute-stamped release times (owner acquisition, NOT_RUN here).
   - **mpmdeci TITLES**: 2018→2026-01 only; the 2026-06-16/09-18 titles
     ("Change in the Guideline") are v1-FACT (boj.or.jp, 2026-10-02), NOT_RUN
     in this archive's PDFs [6J_DEEP §5].
   - **Surprise classification: NOT_RUN** (buildable $0 from the 156 stored
     statements; no consensus/market-pricing series in corpus) [6J_DEEP §9].
   - **MOF lag law** (for excludes): op amounts publish ~1 month
     (monthly)/quarterly (daily detail) after the fact — no same-day signal
     [FACT, DC §1.4].
   - **ABS: NOT_RUN**; **BLS: NOT_RUN in corpus** (bls_gate empty) — and if
     any US-macro conditioning ever enters, the **2025-vintage law** applies:
     the 2025 lapse in appropriations moved/canceled CPI/EMPSIT releases and
     current pages show the AS-REVISED schedule; any BLS calendar use must
     carry as-first-published vs as-revised vintage labels [BLSV §1–§3].
4. **Contract / unit / quote-orientation / session / timezone / roll /
   expiry**: 6J, CME Globex, multiplier **12,500,000 JPY**, minTick 5e-07 =
   **$6.25/tick**, quote **USD per JPY — orientation law in force (field:
   open gates §1)**. Session 17:00→16:00 CT continuous (1,380 min, no
   maintenance break; median held session 1,357/1,380 1m bars) [OBSERVED,
   `6J_qa_ledger.json`]. **Local-clock law: all BoJ/Tokyo windows bucketed in
   Asia/Tokyo local time** (DST-correct via zoneinfo; DC §1.2) — the decision
   window is US overnight (~22:00–01:00 CT) and only Tokyo-clock bucketing
   keeps it stable. Roll: **PIT k=5 volume-crossover + cease-guard**
   (mandatory; the missing guard produced the 2022-09-20 artifact, DC §1.3);
   OI leads the raw volume crossover 1–3 calendar days (12/12 rolls,
   mode 2; OI 2023-10+ only) [OBSERVED, `6J_a3_term.json:
   oi_migration_2023plus`]. Expiry dates: official 2010–2022
   (FXCAL §1: 208/272 cells, 127/127 rule-consistent), **2023–2026
   NOT_OBTAINED — IMM-rule derivation forbidden**; families touching 2023+
   expiry timing declare the gap (JF1's windows do not).
5. **Entry / stand-aside / exit [PROVISIONAL]**: anchor = the 12:00–15:30 JST
   window on the 54 statement dates; signal evaluation begins at window
   **close** (15:30 JST), fill = **open of the next 1m bar**; **mandatory
   delay variants +1 bar and +30m** (thin-book family — the 34-vs-53 floor
   makes fill-timing a first-order unknown); exclude MOF op days as labeled
   ex-post (they are a different family's regime, JF2) and any
   calendar-uncertain date (EXCLUDE/NOT_RUN law, DC §1.2); TP 2×SL; SL
   1.0×ATR(20 sessions of the same window); same-bar SL-priority; time exit
   = session close (16:00 CT) if not stopped — no position held into the next
   session, so roll-carry never enters this family.
6. **Baselines / placebo / negative controls**: C1 clock/placebo — seeded
   random-sign entries at identical times, ≥100 seeds; C2 always-in-window on
   all non-event days (the JF3 skeleton baseline); C3 weekday-matched
   non-event clock (same weekday distribution over ordinary days — the
   family-specific negative: BoJ dates are not Monday/Friday-clustered in a
   way that could mimic a weekday effect); C4 the delay pair itself
   (+1 bar vs +30m adjudication); C3′ regime-change vs ordinary-MPM split as
   built-in falsifier (if the effect exists only on the 4+2 titled dates,
   the all-54 arm must say so or die).
7. **Refutation conditions** (mechanism-level first, then cost):
   - **K1 (reclassification)**: if the MPM-day effect disappears once the
     2026-07-30 unverified op-window and the 10 disclosed op days are
     excluded, the family belongs to JF2, not JF1.
   - **K2 (both-arms-below-floor)**: DRIFT and REV both below the cost floor
     at realistic n ⇒ dead.
   - **K3 (window-artifact)**: if the effect vanishes when the anchor moves
     ±45 min within the 12:00–15:30 JST window (no minute-stamped release
     exists — the anchor-robustness test is the substitute), it is a
     bucketing artifact.
   - **K4 (thin-book fill)**: if the +30m delay variant reverses the sign of
     the fill-window conditional, the effect is a spread artifact of the
     34-vs-53 book (BBO NOT_RUN — delay adjudication is the only available
     microscope).
   - **n honesty**: 54 events full-set; **6–7 regime-change dates** (4
     measured titles + 2 v1-FACT + 2024-03-19); any fold structure on the
     regime-change subset **will fail a ≥5-per-fold floor** — pre-declared,
     the subset may only ever be a descriptive view (0 identities).
   - **Cost level [MODELED, UNDER REVIEW]**: RT cost (spread close-proxy
     $25/side = 4 ticks [DC §1.7: 6J column] + slippage 1 tick $6.25/side +
     fee $2.46/side T1) = **2×$33.71 = $67.42 RT ≈ 8.5 bp of 2026 notional
     (0.006383×12.5M ≈ $79.8k)** [DERIVED]; tiers: T2 2.26 / T3 2.06 /
     T4 1.86; slippage {1,2,3} ticks ⇒ RT 8.5–14.7 bp. MPM-day median |ret|
     57 bp [OBSERVED] vs RT 8.5–14.7 bp: the family is not automatically
     cost-dead, but per-event MDE at n=54 is ≈ 2×(σ_day/√54) ≈ 13–19 bp —
     **at or above the modeled RT cost; K2 is a live risk, stated plainly**.
   - **Volume-definition gap law**: 6J 1m summed volume = **0.455× (median)
     the GLBX cleared-volume statistic** (p10–p90 0.29–0.48, 2023-10+,
     n=752 days) — volume SHARES and RATIOS only, never absolute levels
     [OBSERVED, `6J_qa_ledger.json`; 6J_DEEP §8].
8. **Cost sensitivity**: MODELED COST only; the words "measured/complete
   cost" are FORBIDDEN. Fee 2.46/side T1 corrected (P0-VERIFY upheld) but
   UNDER REVIEW; spread proxy **high-biased** (close-proxy, 20d median; BBO
   NOT_RUN); stress law ×1.0/×1.5/×2.0 on (spread + declared slippage)
   [DC §1.7]; FX fee-group mapping PARTIAL (1 dated binding page pending).
9. **Regime / era breaks**: 2021 quiet regime (vol 5.6%) vs 2022 YCC shock
   (11.4%) vs 2024–26 intervention era [OBSERVED, `6J_a1_regimes.json:
   realized_vol_summary`]; the four titled MPMs cluster 2024–2026 — era
   stability of the MPM effect cannot be tested on a balanced panel
   (pre-2024 titled events outside window); rolling 2020–22 vs 2023–26 split
   mandatory in any scored run.
10. **Coverage / hole proof**: panel 2020-01-02→2026-10-01, 2,843,938
    outright 1m bars, 95-contract registry, 1,745 held-chain sessions; 0
    tick-grid violations, 0 duplicate (instrument, ts) rows, 1 halt bar, 0
    weekend bars; 16 missing weekdays = 15 holidays + 1 held-rule artifact
    (**2022-09-20 cease-guard artifact law**: exchange open, Z2 traded
    125,303 lots, k=5 still held ceased U2 — the artifact sits INSIDE the
    September-2022 intervention week; a scored engine must carry the
    cease-guard or re-derive) [OBSERVED, `6J_qa_ledger.json`; 6J_DEEP §8,
    ERRATUM M-5]. Curve never flipped: near<far on 100.0% of overlapping
    sessions, all 14 pairs; 25/27 positive roll gaps [OBSERVED,
    `6J_a3_term.json`].
11. **Sources**: all citations are local artifacts sha256-pinned in
    `captures/source_sha256.tsv` (dossiers, analysis JSONs, DC, FEES, FXCAL,
    BLSV, P0-VERIFY handoff). Upstream URL/archive authority documented
    inside those artifacts (boj.or.jp statements/titles via nonprice archive;
    mof.go.jp daily intervention CSV; Databento GLBX.MDP3 panel ledgers;
    interactivebrokers.com commissions + CME.php archives per FEES §5;
    cmegroup product-calendar captures per FXCAL §1a).

## 2. JF2 — MOF Intervention-Regime Conditioning (ex-post only; lag law)

1. **Mechanism + microstructure** [MECHANISM_HYPOTHESIS]: once MOF discloses
   an intervention (or a cluster), the market's perceived **official-risk
   regime** changes: hedgers re-price the probability that further weakness
   will be met with official JPY buying, which changes the **asymmetry of
   hedging flow** (importers pre-hedge dips; speculative shorts cap size) —
   a slowly-decaying conditioning variable, NOT a same-day event. This is the
   only lawful use of the MOF record: **lag law — op amounts publish ~1 month
   (monthly) / quarterly (daily detail) after the fact; same-day signals are
   FORBIDDEN** [FACT, DC §1.4; 6J_DEEP §5 preamble]. OBSERVED anatomy being
   conditioned on: the 2021–2026 yen-weak super-cycle is **ONE unrecovered
   −46.7% drawdown** (peak 2020-03-09 → trough 2026-07-28, rolled long-JPY
   basis) whose 3% zigzag decomposition shows **4 of 14 down-legs terminating
   within 0–2 sessions of an op/op-window** (2022-10-20 vs 10-21 op [and the
   recovered 10-24 op +2 sessions], 2024-04-26 vs Apr-29, 2024-07-10 vs
   Jul-11/12, 2026-07-28 vs the UNVERIFIED 07-30 window) — **the other ten
   end nowhere near an op** (ERRATUM M-4 corrected count) [OBSERVED,
   `6J_a1_regimes.json:zigzag_down_legs_3pct`; 6J_DEEP §2, §7-H5]. Op-day
   anatomy (10 in-window ops, disclosure-lagged labels): session return
   +0.78…+2.35% on 8/10 (exceptions 2026-05-04 −0.09%, recovered 2022-10-24
   −0.84%), volume **1.75–4.79×** strict-past-21 median, true range
   **85th–100th percentile** of past-126 [OBSERVED, `6J_a4_events.json:
   mof_ops_anatomy` (9 rows — pre-erratum JSON; the 10th op 2022-10-24's
   anatomy −0.84%/1.75×/98th/246,433 is the A7-6J recompute quoted in
   6J_DEEP §0-6/§5)]. Full official record: **386 daily ops
   1991-05-13→2026-05-06**; regenerated 386-row tidy verified on disk
   (SOURCE_TIDY_RESOLVED) [FACT mof.go.jp via nonprice archive; ERRATUM M-1].
2. **Expected direction, falsifiable** [PROVISIONAL]: in a
   disclosed-intervention regime (label: a disclosed op within the trailing
   K sessions [PROVISIONAL K=63, ~1 quarter], computed STRICTLY from
   disclosure-date-visible data), the conditional session-behavior of JF1/JF3
   host windows differs measurably from the non-regime state — concretely:
   regime-state window volatility and volume-share exceed non-regime state,
   and down-leg termination clusters near zone re-tests. Direction of any
   RETURN conditioning is deliberately NOT asserted — this family conditions
   session behavior; the hedging-asymmetry mechanism predicts higher
   up-move / lower down-move persistence in 6J price within the regime
   [MECHANISM_HYPOTHESIS, pre-stated as the falsifiable content].
3. **PIT feature availability**: MOF record **PASS_EVIDENCED as an ex-post
   source** (386-row tidy regenerated + verified; release lag ~1 month is the
   PIT constraint itself — labels must be built on the DISCLOSURE date, not
   the op date) [DC §1.4]. Q3-2026 daily detail unpublished at data access
   (2026-10-02): the **2026-07-30 window (+2.36%, 607,579 contracts = 5.66×,
   burst 13,366/min at 13:36 UTC) is NOT MOF-VERIFIED — price anatomy only**
   [OBSERVED, `6J_a4_events.json:pending_window_context_2026_07_30`]. CoT
   companion (positioning context): as-published 2006-01→2026-09-22,
   Tuesday as-of → Friday 15:30 ET release, PASS_EVIDENCED [DC §1.4]. BoJ
   statement dates FACT (field JF1-3). Threshold constant for a
   "distance-to-highest-USDJPY-acted-upon" zone label **must be fixed a
   priori by the owner** (PARAM-GAP, 6J_DEEP §7-H5).
4. **Contract / unit / session / timezone / roll / expiry**: identical to JF1
   field 4 (12,500,000 JPY; USD-per-JPY orientation law; 23h CT session;
   Asia/Tokyo local-clock bucketing for any Tokyo-window conditioning;
   k=5 + cease-guard; OI-lead 1–3d; expiries official 2010–2022, 2023–2026
   NOT_OBTAINED). Additional era note: the 386-op history spans 1991→2026
   but the 1m panel spans 2020→2026 — only 10 in-window ops; pre-2020 ops
   are usable ONLY to build the historical zone levels (price data for those
   levels must come from the disclosed op records themselves, not the panel)
   [INFERENCE].
5. **Entry / stand-aside / exit [PROVISIONAL]**: JF2 is an OVERLAY — it has
   no own entries; it splits JF1/JF3 host families by the disclosure-lagged
   regime label. Host entries/exits unchanged (JF1 field 5 / JF3 field 5).
   Regime label construction [PROVISIONAL]: disclosure-date-visible ops only;
   K=63-session trailing window; shuffled-label placebo (C3′) mandatory.
6. **Baselines / placebo / negative controls**: C1–C4 inherited from the
   host; **C3′ intervention-regime placebo = regime labels shuffled across
   the same calendar** (dispatch-mandated): shuffle the disclosure dates
   among the same weekday/count distribution, ≥100 seeds — if shuffled labels
   reproduce the split, the regime variable carries nothing. C3″ pre-2022
   null era: 2020-01→2022-08 contains ZERO in-window ops until 2022-09-22 —
   the label must be "non-regime" throughout, and any family-level effect
   that "appears" in 2020–21 under the regime label is a construction bug.
7. **Refutation conditions**: **K1** the shuffled-label placebo reproduces
   the split ⇒ dead. **K2** the split exists ONLY on the 10 op days
   themselves (a same-day effect leaking through mis-labeled dates) ⇒ lag-law
   violation, dead. **K3** the 4-of-14 leg-termination conditioning does not
   generalize: forward (post-disclosure) window vol/volume in regime state
   not above non-regime state ⇒ the hedging-asymmetry mechanism is falsified
   (mechanism-level kill: the 10 counterexample legs already cap the claim at
   4/14 — the family must predict BEHAVIOR gradients, not leg-endings).
   **K4** era concentration: effect present only 2022–2024 ⇒ regime variable
   is a proxy for the (already-measured) vol regime, adds nothing ⇒ dead.
   **Cost level**: overlay = 0 own identities; host cost floors apply
   (JF1/JF3). n honesty: 10 disclosed in-window ops (11 counting the
   unverified 07-30 window as a SEPARATE price-only label, never merged).
8. **Cost sensitivity**: no own cost surface; MODELED COST of hosts + the
   JF1 tier set; same UNDER-REVIEW law (2.46/side T1 corrected; spread proxy
   $25/side high-biased; BBO NOT_RUN).
9. **Regime / era breaks**: the family IS a regime family — its own falsifier
   is era concentration (K4); super-cycle structure: −46.7% peak-to-trough
   with legs itemized in `6J_a1_regimes.json:zigzag_down_legs_3pct` (16 down
   / 16 up legs ≥3%); 2026 intervention year vol-skew +1.62 with ex-kurt 4.8
   (few huge up-moves, many small down-days — the intervention-year
   signature) [OBSERVED, `6J_a1_regimes.json`].
10. **Coverage / hole proof**: as JF1 field 10, PLUS the MOF-source defect
    disclosure: the original shipped tidy carried only 81 of 386 ops
    (blank-month carry-forward normalizer defect; the in-window 2022-10-24
    op was among the dropped); regenerated 386-row tidy verified on disk
    2026-10-03, `.bak_81rows_20261003` preserved [ERRATUM M-1; FACT]. Any
    consumer must use the regenerated tidy — the 81-row bak is forbidden
    evidence.
11. **Sources**: `captures/source_sha256.tsv` pins 6J_DEEP_v2.md,
    `6J_a1_regimes.json`, `6J_a4_events.json`, `6J_a5_cot.json`, DC, FEES,
    FXCAL. Upstream: mof.go.jp daily FX-intervention official CSV (raw, in
    nonprice archive); CFTC legacy CoT as-published; disclosure-lag law DC
    §1.4.

## 3. JF3 — Tokyo-Morning Session Structure (home-session discovery vs fade)

1. **Mechanism + microstructure** [MECHANISM_HYPOTHESIS]: the Tokyo morning
   (09:00–11:30 JST) is the yen's home session — Japanese importers,
   institutional rebalancing, and the pre-BoJ-window information set trade
   while Western liquidity is absent (US evening/overnight). Competing
   stories: **JF3-CONT** — Tokyo-morning moves encode real home-session
   information that the arriving London/NY book continues (continuation into
   london_pm/ny_am); **JF3-FADE** — the Tokyo morning over-extends in a thin
   book (median 1m volume 59 vs ny_am's 120) and the deep US book fades it.
   OBSERVED anatomy: tokyo_am carries **11.0% of session volume and 13.0% of
   bar-range**; **18.1% of session HIGHS and 15.2% of session LOWS print in
   tokyo_am** (first-occurrence argmax/argmin) — "the session extreme prints
   in Tokyo ~1 day in 6–7" [OBSERVED, `6J_a2_sessions.json:
   session_high_minute_window_pct` / `session_low_minute_window_pct` /
   `center_windows`; 6J_DEEP §3]. Execution floor: tokyo_am median 1m volume
   59 vs ny_am 120 — Asia-hours execution pays ~2× thinner books
   (6J_DEEP §7-H6: session-of-day-dependent cost model is a SPECIFICATION
   FLOOR for ANY JPY strategy).
2. **Expected direction, falsifiable** [PROVISIONAL]: JF3-CONT —
   E[ret(Tokyo close→16:00 CT) | Tokyo-morning range-break sign] carries the
   break's sign; JF3-FADE — opposite. Both arms below floor ⇒ family dead.
   Trigger definition [PROVISIONAL]: first 1m close strictly outside the
   09:00–11:30 JST Tokyo range, evaluated 11:30 JST, fill open of next 1m.
3. **PIT feature availability**: no external calendar needed for the base
   family (pure session structure, all inputs from the price panel PIT);
   EXCLUDES use BoJ statement dates (FACT, field JF1-3) and MOF disclosure
   dates (FACT, lag law). ABS/BLS NOT_RUN laws unchanged.
4. **Contract / unit / session / timezone / roll / expiry**: as JF1 field 4;
   **Asia/Tokyo local clock is the family's load-bearing law** — Tokyo
   09:00 JST must be found even as UTC/CT offsets shift (DST-correct,
   zoneinfo; DC §1.2 binding rule). Roll k=5 + cease-guard; expiry official
   2010–2022 / 2023–2026 NOT_OBTAINED (not touched by this family's windows).
5. **Entry / stand-aside / exit [PROVISIONAL]**: trigger as field 2; fill =
   open next 1m; **mandatory delay variants +1 bar and +30m** (59-vs-120
   thin-book floor); base EXCLUDES BoJ MPM dates and MOF disclosure dates;
   coverage rule: Tokyo-morning window must have ≥80% of its nominal bars
   (holiday-shortened sessions EXCLUDE — calendar-uncertain ⇒ EXCLUDE/NOT_RUN,
   DC §1.2; FX holiday times 2017–2023 per FXCAL §2, 2024–2025 still
   NOT_OBTAINED — treat those dates by the panel's own bar counts); TP 2×SL;
   SL 1.0×ATR(20); same-bar SL-priority; **time exit = 16:00 CT session
   close** (position crosses into the deep US book by construction; local
   exit at 15:30 JST would truncate the mechanism's London leg).
6. **Baselines / placebo / negative controls**: C1 clock placebo (≥100
   seeds); C2 always-in (all non-excluded days, no trigger); C3
   weekday-matched non-event clock — the family-specific negative vs JF1
   (MPM days removed); C3″ the DST-mismatch falsifier: Tokyo-local bucketing
   must be invariant to US DST flips (a ±1h CT shift of the effect = clock
   bug, kill); C4 delay pair.
7. **Refutation conditions**: **K1** effect concentrated on MPM/op-adjacent
   days ⇒ belongs to JF1/JF2 (exclusion test). **K2** both arms below cost
   floor at realistic n (n ≈ 1,600 non-excluded sessions; per-event MDE ≈
   2×σ_intrady-window/√n — with RT cost 8.5–14.7 bp [DERIVED, field JF1-7]
   the family needs a window-move scale well above ~10 bp, plausible only on
   the tail; K2 live risk stated plainly). **K3** DST-mismatch sign flip ⇒
   clock-law bug (kill). **K4** thin-book fill: +30m delay sign reversal ⇒
   spread artifact of the 59-vs-120 book. Volume-definition law (0.455×)
   applies to any volume trigger.
8. **Cost sensitivity**: MODELED, UNDER REVIEW; identical tier set to JF1
   (2.46/2.26/2.06/1.86; spread proxy $25/side high-biased; slippage
   {1,2,3} ticks; stress ×1.0/1.5/2.0); ADDITIONAL floor: the
   session-of-day-dependent cost model (6J-H6) — Tokyo-window fills must
   carry a thicker-book slippage assumption than NY-window fills
   [PROVISIONAL: +1 tick on entry-side slippage for Tokyo-window fills].
9. **Regime / era breaks**: session structure stable across eras (2020-21 /
   2022-23 / 2024-26 top-3 CT hours identical; tokyo-day bucket 7.4–8.0%)
   [OBSERVED, `6J_a2_sessions.json:eras`] — stability is itself the falsifier
   target: a family that only works in one era sub-window (e.g. 2022-23 vol
   shock) is era-overfit, kill via rolling split.
10. **Coverage / hole proof**: as JF1 field 10 (2,843,938 bars; 1,745
    sessions; artifact law 2022-09-20; never-flipped curve; volume 0.455
    law).
11. **Sources**: `captures/source_sha256.tsv` pins `6J_a2_sessions.json`,
    `6J_qa_ledger.json`, 6J_DEEP_v2.md, DC, FEES, FXCAL.

---

# PART II — 6A (Australian Dollar futures; PB3 PARK)

## Park law (stated once, binding)

**PB3 is PARKED.** Everything below is hypothesis PREP: no registration, no
budget request, no scheduling proposal. The census in `RANKING_INPUT.md` §3
is contingency bookkeeping for a future packet draft, exactly like the
sibling lanes' parked families. The **K0 thin-n kill is pre-registered
here** so that a future reopen inherits it, not negotiates it.

## 4. AF1 — RBA Decision-Minute Reaction (drift vs reversal; PB3 core)

1. **Mechanism + microstructure** [MECHANISM_HYPOTHESIS]: the RBA cash-rate
   decision resolves scheduled uncertainty at a machine-known minute
   (14:30 Sydney) inside the home session of a two-hemisphere 23h book.
   Competing stories: **AF1-DRIFT** — the 14:30 spike direction persists as
   the still-arriving Sydney afternoon + London overnight book processes the
   surprise (underreaction); **AF1-REV** — the ±5' prints overshoot a
   modest-depth home-session book and the +15–60' liquidity corrects them.
   OBSERVED anatomy (67 meetings 2020-01→2026-09): ±5' window volume
   **2,199 vs 245 baseline = 9.0×**, mean |1m ret| **4.35 vs 0.91 bp =
   4.8×**; +5–15' 4.1×/3.6×; +15–60' 1.9×/1.7×; event-day session range
   **38 vs 19 ticks (2.0×)**; Sydney share of daily volume 30.4% vs 26.2%
   (activity migrates home on decision days); **change-days (n=23): median
   93.0k volume, 59-tick range; hold-days (n=44): 77.7k, 29 ticks; non-event
   19** — the decision-surprise channel is visible in volume/range with NO
   return conditioning computed (law) [OBSERVED, `6A_a4_events.json:rba.
   windows_median_across_events` / `.baseline_non_event_sessions_same_clock`
   / `.event_day_vs_non_event_day`; 6A_DEEP §4.1].
2. **Expected direction, falsifiable** [PROVISIONAL]: AF1-DRIFT —
   E[ret(14:35 Syd→17:00 Syd) | sign of the ±5' move] carries the spike's
   sign; AF1-REV — opposite. Both arms below floor ⇒ dead. Change-vs-hold
   split is the built-in intensity gradient (59 vs 29 ticks measured) but is
   a WEAK surprise proxy, labeled as such (no market-pricing series in
   corpus) [6A_DEEP §6-H1].
3. **PIT feature availability**: **RBA cash-rate table PASS_EVIDENCED —
   full as-published decision table 1990→2026-09** (in-corpus gate HTML);
   anchor = 14:30 Sydney on effective_date − 1 AU business day; the only
   off-Tuesday case (2020-03-19 COVID emergency cut) is flagged and the
   −1-BD rule still lands correctly [FACT + OBSERVED, DC §1.4; 6A_DEEP
   §4.1]. 2026 remaining meetings per v1-FACT: Nov 3, Dec 8. Surprise
   classification NOT_RUN (weak proxy change-vs-hold measured). FOMC
   context (excludes): 147 archived statements 2011-01→2026-09;
   ±5' volume 8.2×, |1m ret| 6.2× on 6A — the US-rates common factor is
   LARGER than RBA's on this symbol [OBSERVED, `6A_a4_events.json:fomc`].
   ABS NOT_RUN (no family in corpus; landing-page 11:30 AEDT verified
   2026-10-03) [6A_DEEP §4.3]. BLS: NOT_RUN + 2025-vintage law (BLSV) if
   US macro ever enters.
4. **Contract / unit / session / timezone / roll / expiry**: 6A, CME Globex,
   multiplier **100,000 AUD**, minTick **5e-05 vendor = $5.00/tick — the
   legacy 1e-4 conflict is UNADJUDICATED** (vendor value used throughout the
   dossier; if the true tick were 1e-4, tick value doubles to $10 and every
   tick-denominated stat halves — the conflict must be adjudicated before
   any scored use; DC §1.1; 6A_DEEP defect 8). Quote USD per AUD. Session
   17:00→16:00 CT (1,746 held sessions, 0.0% zero-volume minutes on front)
   [OBSERVED, 6A_DEEP §7]. **Local-clock law: Australia/Sydney bucketing
   for all RBA windows** (DST-correct; DC §1.2). Roll: the v1 declared
   calendar rule (nearest HMUZ until last session before delivery-month
   day-1) is **[DECLARED-EXTRAPOLATION]** — measured: new quarterly reaches
   10k/day in 4–12 days (median 8); total-volume crossover lands 9–15 days
   AFTER the declared roll (median 11); OI leads volume crossover 2–3
   sessions (2023-12+); **k=5 on 6A NOT measured — must be measured before
   any scored use** (ERRATUM A7-DC-F3); cease-guard mandatory [OBSERVED,
   `6A_a3_term.json`; DC §1.3]. Expiries: official 2010–2022 (FXCAL §1b:
   6A +17 rows, 52/52), **2023–2026 NOT_OBTAINED**.
5. **Entry / stand-aside / exit [PROVISIONAL]**: anchor 14:30 Sydney; signal
   = the ±5' window's signed move; entry evaluation at 14:35, fill = open of
   next 1m; **mandatory delay variants +1 bar and +30m**; base EXCLUDES FOMC
   statement days (59 in panel — the bigger common factor) and any
   calendar-uncertain date; TP 2×SL; SL 1.0×ATR(20 same-window); same-bar
   SL-priority; time exit = 17:00 Sydney (home-session close) [PROVISIONAL —
   holding into London is a declared variant, not the base].
6. **Baselines / placebo / negative controls**: C1 clock placebo (≥100
   seeds, random sign at 14:30–14:35 on non-event days); C2 always-in-window
   all days; C3 weekday-matched non-event clock (RBA days are Tuesdays +
   flagged specials — the negative must match the Tuesday distribution,
   which is the family-specific hazard); C3′ change-vs-hold split (measured
   gradient 59/29); C3″ FOMC-day exclusion test (K1 cross-venue leak into
   the 14:30 Syd window is impossible — 13:00 CT ≠ 14:30 Syd — but the
   NEXT-day FOMC spillover must be excluded); C4 delay pair.
7. **Refutation conditions**: **K0 (thin-n kill, PRE-REGISTERED)**: n=67
   meetings total; any fold structure (e.g. 8 folds) gives ≈8.4/fold —
   **the ≥5-per-fold floor likely FAILS**; the family may only ever be
   scored as a single-stratum cell or must pool eras — pre-declared, not
   negotiated at reopen. **K1** effect disappears when FOMC-adjacent days
   excluded ⇒ common-factor artifact. **K2** both arms below floor:
   RT cost = 2×(spread $20 [DC §1.7: 6A column, 4 ticks × $5] + slip $5 +
   fee $2.46) = **$54.92 ≈ 8.2 bp of 2026 notional (0.6696×100k ≈ $67.0k)**
   [DERIVED]; the ±5' mean |1m ret| is 4.35 bp — the per-event signal scale
   is BELOW one RT; per-event MDE at n=67 ≈ 2×σ/√67 — **power-starved,
   K2 is the expected outcome and is stated as such (honest)**. Tiers
   2.46/2.26/2.06/1.86; slippage {1,2,3} ticks.
8. **Cost sensitivity**: MODELED COST, UNDER REVIEW (same fee erratum law as
   6J — identical FX group row); spread $20/side close-proxy high-biased;
   BBO NOT_RUN; stress ×1.0/1.5/2.0; tick-conflict caveat (field 4) — if
   1e-4 adjudicates, all tick-denominated costs double in tick units.
9. **Regime / era breaks**: 23 changes span COVID cuts (0.10), 2022-23 hike
   cycle (4.35), 2025 cuts (3.60), 2026 hikes Feb/Mar/May/Sep (4.60) [FACT
   RBA table]; era splits 2020-22 / 2023-26 mandatory; the 2020-03-19
   special (Thursday) is a flagged single-point era.
10. **Coverage / hole proof**: 2,703,211 post-exclusion outright bars;
    **1,584-bar `6BU5` vendor contaminant excluded** (2020-05→08) and
    **instrument 7084 (`6AM5`) pre-activation strays (914 bars) excluded**;
    0 negative outright prices (32,694 negative CALENDAR-SPREAD bars are the
    curve sign itself, never in price stats); 1 break-window bar; 0 weekend
    anomalies; 0.0% zero-volume front minutes; trade date 2026-10-01 partial
    (2h) — all full-session stats end 2026-09-30 [OBSERVED, 6A_DEEP §7].
11. **Sources**: `captures/source_sha256.tsv` pins 6A_DEEP_v2.md,
    `6A_a4_events.json`, `6A_a3_term.json`, DC, FEES, FXCAL. Upstream: RBA
    gate HTML as-published (in-corpus nonprice archive); FOMC statements
    archive (federalreserve.gov); Databento GLBX.MDP3 panel; IBKR/CME fee
    captures per FEES §5.

## 5. AF2 — RBA-vs-Fed Differential Regime Conditioning (CIP structural input)

1. **Mechanism + microstructure** [MECHANISM_HYPOTHESIS]: the AUD-USD
   overnight rate differential sets the sign of the carry/roll structure
   (CIP), and the SIGN REGIME of that differential is a structural state that
   conditions how the home session behaves on decision days and ordinary
   days (e.g. hedging-flow asymmetry, the direction cheapness of deferreds,
   and the intensity of 14:30 reactions when RBA moves WITH vs AGAINST the
   differential). **H-F/H-G LAW: the differential is a CONDITIONING INPUT —
   carry harvest is NOT an alpha hypothesis and is NOT proposed here.** Any
   AF2-conditioned family must be a session-behavior design (conditioning
   AF1/AF3 host windows), never a standing carry position. OBSERVED basis:
   roll-gap sign matches sign(US−AUD differential) on **16/16 rolls with
   |Δ|≥25bp (100%)** and 20/27 overall (74%; every mismatch sits in the 2021
   ZIRP-era ~0.0–0.1pp noise) [OBSERVED, `6A_a3_term.json:
   roll_gap_vs_rate_differential` (n=27, n_material=16); 6A_DEEP §3.2];
   2026 mild backwardation = CIP-consistent expression of RBA 4.35→4.60 >
   DFF ~3.63.
2. **Expected direction, falsifiable** [PROVISIONAL]: the AF1 14:30 reaction
   (volume/range anatomy) and AF3 session peaks differ by differential-sign
   regime (positive AUD-USD differential vs negative), with the direction of
   any RETURN conditioning deliberately not asserted. Falsifiable statement:
   regime-split anatomy ≡ pooled anatomy ⇒ the conditioning carries nothing
   ⇒ dead (it is an overlay; its null is identity with the host).
3. **PIT feature availability**: RBA table PASS_EVIDENCED as-published
   (field AF1-3); **DFF = FRED latest vintage — ALFRED vintages in corpus are
   year-end snapshots only ⇒ the differential series is NOT PIT-strict**
   (declared caveat; a 6E-side test showed PIT-as-of recomputation can flip a
   fragile CIP correlation from +0.91 to −0.11 — vintage sensitivity MUST be
   quantified before any registration; DC §1.3 roll≠alpha law + 6A_DEEP
   §3.2 caveat). Overnight tenor proxy (no 3m AUD series in corpus).
4. **Contract / unit / session / timezone / roll / expiry**: as AF1 field 4
   (100,000 AUD; USD-per-AUD; Sydney local clock for hosts; declared-
   extrapolation roll law + cease-guard + measure-k=5-first; tick conflict
   UNADJUDICATED; expiries 2010-2022 official / 2023-2026 NOT_OBTAINED).
5. **Entry / stand-aside / exit [PROVISIONAL]**: overlay — no own entries;
   splits AF1/AF3 hosts by the differential-sign regime (material |Δ|≥25bp
   label; immaterial band excluded as noise by the measured 2021 mismatches).
6. **Baselines / placebo / negative controls**: C1–C4 inherited; C3′ regime
   label shuffled across the same calendar (≥100 seeds) — the 27-roll sign
   law gives only ~16 material regime observations across 6.8y, so the label
   is a low-frequency variable and the placebo MUST respect its
   autocorrelation (block shuffle, not iid) [INFERENCE].
7. **Refutation conditions**: **K1** shuffled-label (block) placebo
   reproduces the split ⇒ dead. **K2** vintage sensitivity: recompute the
   differential with year-end ALFRED vintages as-of each roll; if the sign
   regime flips on ≥3 of 16 material rolls, the conditioning variable is
   vintage-fragile ⇒ dead (the 6E precedent is the stated bar). **K3** the
   split exists only in the 2022-23 hike era ⇒ era proxy, dead. Cost: 0 own
   identities (overlay law); host floors apply.
8. **Cost sensitivity**: none of its own; MODELED/UNDER-REVIEW host tiers.
9. **Regime / era breaks**: the differential regime IS the era variable
   (negative 2020-21 ZIRP noise band; strongly negative AUD-USD 2022-23
   [gap +1.82% ann 2022-12-01 vs diff −0.98pp]; positive 2026 [−1.87% ann
   vs +0.72pp]) — era concentration IS the kill (K3).
10. **Coverage / hole proof**: host coverage (AF1 field 10) + the 27-roll
    measured set itself (all rolls 2020-2026, `6A_a3_term.json:
    quarterly_rolls`); vintage hole: year-end-only ALFRED (declared, K2).
11. **Sources**: `captures/source_sha256.tsv` pins `6A_a3_term.json`,
    6A_DEEP_v2.md, DC (§1.3 roll≠alpha, §1.4 rates NOT PIT-strict), FEES.

## 6. AF3 — Bimodal US+Sydney Session Structure (two-hemisphere book)

1. **Mechanism + microstructure** [MECHANISM_HYPOTHESIS]: 6A is a genuinely
   two-hemisphere book — a primary US-day peak and a secondary Sydney/Tokyo
   morning peak — so the session has TWO liquidity regimes per day. Competing
   stories: **AF3-ROT** — information discovered in the quiet Sydney morning
   (home-session flows, the 11:30 modal slot) transfers into the deep US book
   (continuation); **AF3-ABS** — the Sydney-morning prints are thin-book
   overshoots that the US book corrects (fade). OBSERVED anatomy: US RTH core
   (08:30–15:00 CT) carries only **38.0/39.5/42.7%** of volume by era; Sydney
   day 07:00–17:00 **26–28%**; London ~51%; intraday U-curve **bimodal**:
   primary peak 09:00 CT (1.68bp mean |1m ret|, 2024-26), **secondary peak
   19:00–20:00 CT (1.19–1.27bp = Sydney/Tokyo morning 10:00–11:00 local)**,
   minimum 15:00 CT (0.68bp) [OBSERVED, `6A_a2_sessions.json:
   mean_abs_1m_ret_by_ct_hour_bp`, `hub_windows`; 6A_DEEP §2.1]. Sydney
   morning profile: modal peak **11:30 Syd = 2.35% of daily volume** in that
   half-hour (~1.1× the average half-hour, ~1.3× median, ~3.9× only vs the
   quiet 09:00 Sydney slot — ERRATUM MINOR-1 corrected multipliers); Sydney
   open 30m (09:45–10:15) 1.4–1.5% with modest open effect; China-data
   window 09:30–10:00 Shanghai 2.2–2.3% with the **highest mean 1m range of
   any hub window (2.36 ticks)** [OBSERVED, `6A_a2_sessions.json:
   volume_by_syd_halfhour`, `hub_windows.shanghai_data_0930_1000`].
2. **Expected direction, falsifiable** [PROVISIONAL]: AF3-ROT — E[ret(11:30
   Syd→16:00 CT) | Sydney-morning range-break sign] carries the break's
   sign; AF3-ABS — opposite. Both below floor ⇒ dead. Trigger [PROVISIONAL]:
   first 1m close outside the 09:30–11:30 Syd range, evaluated 11:30 Syd.
3. **PIT feature availability**: base family needs no calendar (pure session
   structure on the panel); EXCLUDES: RBA dates (PASS_EVIDENCED), FOMC dates
   (in-corpus). **China event splits NOT_RUN** (no Caixin/NBS calendar in
   corpus — the 09:30–10:00 Shanghai window is OBSERVED as structure only);
   **ABS NOT_RUN** (the 11:30 slot is hot on ALL days; event-day splits
   impossible without historical ABS dates — owner acquisition decision)
   [6A_DEEP §4.3/§4.4]. BLS law if US macro enters (BLSV).
4. **Contract / unit / session / timezone / roll / expiry**: as AF1 field 4.
   **Australia/Sydney local clock load-bearing** for the Sydney-morning
   windows (DST-correct, both hemispheres shift independently — the family's
   natural falsifier, C3″ below); Asia/Shanghai clock for the China window.
5. **Entry / stand-aside / exit [PROVISIONAL]**: trigger as field 2; fill =
   open next 1m; **mandatory delay variants +1 bar/+30m** (Sydney morning is
   the thinner hemisphere by the U-curve); base EXCLUDES RBA + FOMC days;
   coverage rule ≥80% of nominal Sydney-morning bars else EXCLUDE; TP 2×SL;
   SL 1.0×ATR(20); same-bar SL-priority; time exit 16:00 CT.
6. **Baselines / placebo / negative controls**: C1 clock placebo; C2
   always-in-Sydney-window; C3 weekday-matched non-event clock (family
   negative vs AF1); C3″ **opposite-DST-month natural experiment**: in the
   ~3-4 weeks when Sydney and Chicago are on opposite DST phases, a genuine
   Sydney-local mechanism keeps its local-clock profile while a CT-artifact
   shifts by one hour — pre-registered as the clock-law falsifier; C4 delay
   pair.
7. **Refutation conditions**: **K1** concentration on RBA/FOMC-adjacent days
   ⇒ reclassify to AF1. **K2** both arms below floor: RT 8.2 bp [DERIVED,
   AF1-7] vs Sydney-morning per-minute scale ~1.2–1.5bp — the trigger needs
   multi-minute accumulation to clear cost; n ≈ 1,600 non-excluded sessions
   gives MDE ≈ 2×σ/√n; honest: plausible only on tail triggers; K2 live.
   **K3** DST-artifact kill (C3″). **K4** the Shanghai-window contamination:
   if triggers cluster 09:30–10:00 Syd-equivalent (i.e. inside the China
   data window), the family is a China-event family in disguise — and
   China-event splits are NOT_RUN, so the cluster itself kills the base
   spec (re-specification would need the missing calendar).
8. **Cost sensitivity**: MODELED, UNDER REVIEW; host tier set; spread $20/
   side close-proxy high-biased; BBO NOT_RUN; stress ×1.0/1.5/2.0;
   session-of-day floor: Sydney-morning fills carry the thinner-book
   slippage assumption (+1 tick [PROVISIONAL]) per the U-curve evidence.
9. **Regime / era breaks**: hub-window shares stable across eras (Sydney day
   27.7/26.2/26.3%; bimodal shape present in all three era slices
   [`6A_a2_sessions.json:mean_abs_1m_ret_by_ct_hour_bp` per era]) — era
   stability is the falsifier target (one-era-only ⇒ overfit, kill).
10. **Coverage / hole proof**: as AF1 field 10 (2,703,211 bars post-exclusion;
    6BU5 contaminant + 7084 strays excluded; 0.0% zero-volume minutes; 1,746
    sessions; partial 2026-10-01 tail disclosed).
11. **Sources**: `captures/source_sha256.tsv` pins `6A_a2_sessions.json`,
    6A_DEEP_v2.md, DC, FEES, FXCAL.

---

## 7. Shared cost model (both symbols; MODELED, UNDER REVIEW)

| layer | 6J | 6A | basis |
|---|---|---|---|
| tick value | $6.25 (5e-7 × 12.5M) | $5.00 (5e-5 × 100k; **1e-4 conflict UNADJUDICATED**) | DC §1.1 |
| commission T1/T2/T3/T4 | 0.85/0.65/0.45/0.25 | same | FEES §2 |
| exchange + reg | 1.60 + 0.01 | same | FEES §2 (corrected; P0-VERIFY upheld) |
| **all-in per side T1** | **2.46** | **2.46** | FEES §2; MODELED; account NOT_RUN |
| spread close-proxy (20d median) | $25 (4 ticks) | $20 (4 ticks) | DC §1.7; **high-biased; BBO NOT_RUN** |
| slippage tiers | {1,2,3} ticks/side | {1,2,3} ticks/side | DC §1.7 stress law ×1.0/1.5/2.0 |
| RT cost, 1-tick slip, T1 | ≈$67.4 ≈ 8.5bp (2026 notional $79.8k) | ≈$54.9 ≈ 8.2bp (2026 notional $67.0k) | DERIVED |
| notional band | $76.4k–$124.0k (price 0.00611–0.00992) | ≈$60k–$80k (price 0.60–0.80) | DERIVED from measured price bands |

Forbidden words: "measured cost", "complete cost" — the fee layer alone is
corrected; spread is a high-biased proxy and slippage is an assumption.

## 8. Standing NOT_RUN register (this lane)

- Any PnL/backtest/conditional mean-return evaluation of any family (law).
- BBO/true spread on both symbols; slippage measurement.
- 6J: BoJ statement intraday timestamps; surprise classification; policy-rate
  levels 2024-2026 from primary PDFs; same-day intervention detection
  (impossible PIT); MOF Q3-2026 daily detail (2026-07-30 window stays
  price-anatomy-only); TONA/PIT-strict CIP closure.
- 6A: k=5 roll rule measurement (declared-extrapolation law); tick-size
  adjudication (1e-4 vs 5e-5); ABS historical release dates; China
  calendars; surprise classification; tradeable roll-cost computation
  (adjacent-close gaps only).
- Both: FX expiries 2023-2026 (NOT_OBTAINED; derivation forbidden); FX
  holiday times 2024-2025 (NOT_OBTAINED); cross-venue tests (P1-CROSS owns).
- 6J volume absolute levels (0.455 law — shares/ratios only).

— End JPY_AUD_HYPOTHESES. No outcome data existed to be blind to; none was
used.
