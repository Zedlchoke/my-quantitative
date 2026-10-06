# HYPOTHESES_R2 — round-2 outcome-blind hypothesis continuation, 6 symbols (lane HYPO)

- Task: **FUTURES-SIX-ADOPT-PREP-20261004**, lane **HYPO** (parallel, owner
  item: outcome-blind hypothesis continuation, no PnL). Generated 2026-10-04
  UTC. Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-six-adopt/prep`
  @ HEAD **`9fb66c88d464fd90748bc04d78280c2d87939cd3`** (measured via the one
  permitted `git rev-parse HEAD`; == dispatch base_sha), branch
  `codex/futures-six-adopt-prep-20261004`.
- Class: PREP hypothesis dossier. **0 PnL, 0 returns, 0 scored runs, 0 sweeps,
  0 selection by any return statistic. ZERO-PnL law restated in the handoff
  authority_claims.** Every parameter **[PROVISIONAL]**. Outcome-blind
  throughout; missing evidence is **NOT_RUN**, never PASS.
- **No cycle registration, no trial creation.** Everything below is a PROPOSAL
  on paper. NO_GO_REGISTER / NO_GO_SCORE / NO_GO_ORDER stands; ES cap 24
  FROZEN (headroom 0); PB2 HOLD; PB3 (6A) PARK — all restated, never reopened.
- Standing rulings inherited unchanged: fees MODELED /
  VERIFIED_VS_ACCOUNT=NOT_RUN / UNDER REVIEW until owner-authorized A7 (D2
  open; round-1 verify verdict **A7-fee READY-NOT-RUN**); BBO NOT_RUN (D5
  law); NO network access was used this lane (zero fetches, zero web reads).
- **Field format**: the 11 numbered fields per family follow the baseline
  hypo file set EXACTLY (FX_HYPOTHESES.md / JPY_AUD_HYPOTHESES.md /
  ESNQ_HYPOTHESES.md: 1 Mechanism+microstructure · 2 Expected direction,
  falsifiable · 3 PIT feature availability · 4 Contract/unit/session/
  timezone/roll/expiry bindings · 5 Entry/stand-aside/exit · 6
  Baselines/placebo/negative controls · 7 Refutation conditions · 8
  Cost/spread/slippage sensitivity · 9 Regime/era breaks · 10 Coverage/hole
  proof · 11 Sources). The dispatch prose's concept list maps into these
  fields as: hypothesis ID = family header; universe/clock/warmup/anchor =
  fields 4-5; features/lags = fields 3+5; entry/exit/fills = field 5;
  costs = field 8; neighbour = field 6 (C1-class clock/neighbour placebo);
  falsification rule = field 7; expected-failure interpretation = field 7
  (K2 honesty clauses).
- Taxonomy: **FACT** (primary source + date) / **OBSERVED** (script + window
  on committed artifacts, cited `file:field`) / **MECHANISM_HYPOTHESIS**
  (unmeasured causal story) / **INFERENCE** / **DERIVED** (arithmetic from
  named measured inputs) / **NOT_RUN** (never PASS) / **NOT_OBTAINED**.
  Forbidden words: "measured cost", "complete cost" (fee layer corrected,
  spread high-biased proxy, slippage assumption); "edge" claims of any kind.

---

## 0. Evidence base consumed before writing (all read-only, in-worktree)

1. Baseline hypo base (FUTURES-OVERNIGHT-PREP-20261003): `hypo/es_nq/
   ESNQ_HYPOTHESES.md` (8 families ES-F1..F4, NQ-F1..F4 + §0.5 anti-multi-
   trial rulings), `hypo/6e_6b/FX_HYPOTHESES.md` (FX-F1..F6 + §7 cost table
   + §8 census 648), `hypo/6j_6a/JPY_AUD_HYPOTHESES.md` (JF1..JF3, AF1..AF3 +
   PB3 park law + K0 thin-n kill), `hypo/cross/RANKING_FRAMEWORK.md` (the
   5-dim D1-D5 0-3 rubric, aggregation + tie-break law, §4 diagnostics
   class), `synth/CENSUS_FINAL.md` (trial-identity census incl. T5
   construction/roll class: NQ-F4 Role B 4 IDs; GC-F2 ROLL-MIGRATION 0 IDs
   "never scored as alpha").
2. Round-1 readiness (FUTURES-SIX-READINESS-20261004): `fx_eb/
   DATA_READINESS_6E.md` (expiries 66/68; roll 27 switches, lead 13-19d
   `cost_roll_events/cost_roll_events_fxeb.json`), `DATA_READINESS_6B.md`
   (expiries 62/68; lead 17d; holiday grid 0/42 NOT_OBTAINED), `fx_ja/
   DATA_READINESS_6J.md` (tick 5e-7 unique; orientation PROVEN; cease-guard
   2022-09-20 element-exact; BoJ stamps NOT_IN_CORPUS), `DATA_READINESS_6A.md`
   (tick eras RESOLVED_PER_ERA; k=5 MEASURED 27 rolls, 21 cease-guard
   trigger / 6 crossover; vanished sessions 2024-12-17 + 2026-06-16),
   `verify/nq_recompute.json` + `verify/verify_findings.json` (NQ v3 chain
   VERIFIED: 66 rolls, crash roll 2020-03-19 NQH0→NQM0, cg variant ==
   baseline v3 byte-identical ⇒ 0 cease-guard violations post-repair; old
   chain held dead NQH0 49 sessions 2020-03-20..05-29), `fx_ja/
   6a_roll_measured.json` (mode triggers, ramp-day receiving volumes),
   `fx_ja/6a_tick_adjudication.json` + `6j_identity.json` (era grids).
3. Ancestry authorities: `FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/deep/
   6e_6b/PB2_ANCESTRY_COURT_DRAFT.md` (FOREX-FREE-V1 A3-P1 London-open
   continuation −2.353/PF 0.849/11,459 trades; FOREX-FREE-V2 A4-P1
   Tokyo→London expansion −3.80, A4-P2 London-AM break+retest −3.09; six
   cells 12/12 EXPECTANCY_NONPOSITIVE; forbidden-inventory: London-open
   continuation, late-NY fade, session relabeling, near-duplicate
   London-to-NY momentum), `deep/es_nq/NQ_DEEPFOUR_V3_ADDENDUM.md` §10
   (dead-family transplant warning; FX cost-domination lesson), DC
   §1.3 in `FUTURES-DATACONTRACT-QUAL-V1/DATACONTRACT_QUALIFICATION.md`
   (owner distinguishing law: construction rule ≠ alpha hypothesis;
   roll-gap/CIP structural inputs; cease-guard binding on all FX).
4. Dead-family inventory: `research/wayfinder/FAMILY_FAILURES.jsonl` —
   **all 173 entries scanned this lane** (crypto 66 / forex 27 / stocks 45 /
   rates 3 / vol 6 / commodities 3 / sprint 6 / misc; classes
   SCIENTIFIC_REJECTION, SELECTION_REJECTION, ANCESTRY_RHO_BLOCK,
   VARIANT_SAME_FAMILY, COST_VETO_PRE_PNL, DATA_BLOCK, HOLDOUT_FAILURE).
5. Round-2 standing context: `FUTURES-SIX-ADOPT-PREP-20261004/dispatch/
   DISPATCH_MANIFEST.json` (lanes, standing rulings, commit policy).

No new numerics were produced by this lane beyond arithmetic on the cited
artifacts; there are no captures and no fetch log (zero network, disclosed).

---

## 1. Search result and closure (what was proposed, what was vetoed, and why)

**2 NEW families are proposed** (cap ≤6; quality over quantity), **2
zero-identity diagnostics**, and **3 carried-family status proposals** (not
new families; clearly typed so the cap accounting stays honest). The gap
between 2 and the cap is deliberate and evidenced — every other candidate
generated in this lane's search died against one of three walls, each cited:

- **W1 Ancestry veto (dead-family rename).** A "volume/participation-shock
  continuation" family on NQ (the natural (a)-space candidate using the
  repaired 2020 volume data) is the same signal class as dead crypto
  `XSECT-VOLSHK-S15` "Dollar-volume shock continuation"
  (SELECTION_REJECTION, FAMILY_FAILURES.jsonl row 4) and sits in the
  program-level "session/open FX momentum/fade rejected at high trade
  counts" warning (NQ_DEEPFOUR_V3_ADDENDUM §10). Symbol/era tweak of a
  rejected family ⇒ **VOID by ancestry law**. Likewise any overnight-fade
  variant hits dead `DT100-20-OVERNIGHTFADE` / `DT100-70-ONRET` (crypto,
  NEGATIVE_EXPECTANCY) at the signal-class level, and the OVN-tail classes
  are the REGISTERED parent pair's territory (PB1 M-A/M-B, 24 FROZEN) —
  a third overlap would be a disguised re-parameterization (baseline ESNQ
  §0.5-1 ruling).
- **W2 Standing law (out-of-law classes).** Any calendar-spread / curve /
  carry-dynamics family on the FX symbols is out-of-law by DC §1.3 ("roll
  timing, chain, session clock = construction rules, NOT alpha hypotheses;
  roll-gap/CIP are structural inputs, not edge signals") + the H-G law
  (conditioning, never standalone). The six R2 candidates were screened
  against this before anything was written.
- **W3 Data absence (NOT_RUN, never invented).** BoJ intraday decision
  stamps NOT_IN_CORPUS (6J) kills any minute-anchored BoJ refinement beyond
  JF1's window convention; ABS/China calendars NOT_RUN (6A) keep AF3's K4
  alive; BBO NOT_RUN everywhere keeps every fill story conservative-law
  only. None of these may be designed around by assumption.

The two survivors are exactly the round-1 repair surfaces the owner named
as opened design space: (b)+(d) merge into one migration-mode family, and
(c) becomes one overlay family plus a cost-law audit; (a) resolves into
carried-family status proposals after W1/W2 vetoes (§4). Each candidate's
ancestry check is tabulated in §6 with the cited dead rows.

---

## 2. R2-F1 `RMM` — Roll-Migration Mode (T5-class; legs 6E/6B/6J/6A; NQ excluded by cross-reference)

**Type: T5 construction/roll class (CENSUS_FINAL convention), with Role A =
binding construction ledger (0 identities) and Role B = gated small-ID
alpha leg (PROPOSAL; DC §1.3 boundary ruling required before any
registration — declared, not self-ratified).** Unifies owner design spaces
(b) cease-guard event days as exogenous microstructure shocks and (d) 6E/6B
roll-lead measured 13-19d.

1. **Mechanism + microstructure** [MECHANISM_HYPOTHESIS]. **Who is
   forced/slow**: program funds and CTAs rolling quarterly FX exposure on
   fixed calendar/DTE schedules, and the dealers intermediating them — the
   migration is *forced* (delivery approaches) while its *speed* is chosen
   by the crowd. **Why the effect exists**: when migration is COMPRESSED —
   the receiving contract ramps to dominance only as the dying contract's
   book ceases (cease-guard-triggered switch) — a quarter's worth of
   position transfer lands in a handful of sessions; the receiving
   contract's book absorbs one-sided migration flow and dealers price the
   overhang, which plausibly creates transient pressure that decays once
   migration completes (arm **M-COMPRESS-REV**), versus the migration
   carrying genuine directional position information that persists (arm
   **M-COMPRESS-CONT**). **Measured anatomy being conditioned on** (all
   OBSERVED, cited): 6A mode split **21/27 rolls cease-guard-triggered
   (abrupt) vs 6/27 crossover-triggered (gradual)**
   [`6a_roll_measured.json:k5_cease_guard_variant.rolls[].trigger`]; the
   extremal abrupt episodes put **55,675 lots (6AH5, 2024-12-17)** and
   **55,533 lots (6AU6, 2026-06-16)** into the receiving contract on the
   very session the baseline chain still held the dead contract
   [`6a_roll_measured.json:variant_delta.cease_guard_vanished_session_detail`];
   6J 2022-09-20: **Z2 125,303 lots / 1,357 bars while k=5 still held
   ceased U2 (stale trailing-5 mean 92,857.8 vs Z2 88,234.0)**, switch
   09-21, U2 final session 09-19 with 97 bars
   [`6j_cease_guard_2022.json`; DATA_READINESS_6J Dim 3]; roll LEADS now
   measured, not extrapolated: **6E 13-19 days before official expiry, 6B
   17 days** on the 2024Q4→2026Q3 cells
   [`cost_roll_events_fxeb.json:roll_remeasure.6E/6B.switches[].days_lastheld_before_expiry_obs`;
   DATA_READINESS_6E/6B §3]; 6B gradual anatomy: crossover median 11
   sessions AFTER declared roll, old contract stays liquid 66-172k/day
   (DC §1.3 table); 6A crossover 9-15d after declared (median 11)
   [`6a_roll_measured.json:calendar_rule_cross_reference.note`]. The
   family's variable is the **migration-SPEED classification** (mode), a
   microstructure observable; it is NOT the roll-gap level and NOT the
   rate differential (those stay FX-F5/AF2 structural overlays, DC §1.3).
2. **Expected direction, falsifiable** [PROVISIONAL, no PnL claim]:
   M-COMPRESS-REV — E[receiving-contract close-to-close over
   [switch, switch+K]] conditional on the switch-window signed move carries
   the OPPOSITE sign on abrupt-mode rolls more than on gradual-mode rolls
   and more than the weekday-matched non-roll clock placebo; M-COMPRESS-CONT
   — the same conditional carries the SAME sign with abrupt > gradual
   intensity. The mode GRADIENT (abrupt vs gradual) is part of the
   falsifiable claim: a mechanism of compressed forced flow predicts
   mode-monotone behavior. Both arms below floor at realistic n kills the
   family (K2, with the honest power interpretation in field 7).
3. **PIT feature availability**: mode label = strict-past classification
   from the measured old-contract last-bars session vs the k=5 crossover
   trigger, decided at close t, effective t+1 (DC §1.3 timing law verbatim:
   "quyết định tại close t, hiệu lực t+1"); roll switch dates, old/new
   volumes and leads all in-repo measured (27 rolls/symbol, 2020-2026);
   official expiry cells provenanced where obtained (6E 66/68 incl. ECH26/
   ECM26; 6B 62/68; 6A 62/68; 6J 58/68) and NOT_OBTAINED cells declared
   with derivation FORBIDDEN; no external conditioner of any kind.
   **NOT_RUN (family-specific interaction — anatomy-first gate)**: the
   per-roll mode classification is MEASURED for 6A (21/6 trigger split) and
   re-derivable for 6E/6B/6J from the committed switch tables; the
   mode × post-switch-drift interaction itself has never been measured
   (that measurement IS the family — Role A ledger first).
4. **Contract / unit / session / timezone / roll / expiry bindings**
   (universe, clock, warmup, anchors): 6E EUR 125,000, tick 5e-05 =
   $6.25; 6B GBP 62,500, tick 1e-04 = $6.25; 6J JPY 12,500,000, tick
   5e-07 = $6.25, **quote USD-per-JPY, 6J UP = yen strong (orientation
   PROVEN round-1; DC §1.1 law)**; 6A AUD 100,000, tick 5e-05 = $5.00
   from 2020-11-23, **$10.00/tick in the 2020 sub-era (era-aware cost law
   mandatory)**. 23h CT session template, all windows in America/Chicago
   trade dates; **universe = the measured roll set per symbol (27 switches
   each on 6E/6B/6J/6A, 2020-2026, 108 events total; NQ's 66 rolls
   EXCLUDED — see cross-reference below)**. **Event clock (anchor)** = the
   explicit cease-guard-variant switch session (rule-independent measured
   trigger: first session the receiving contract takes the book); holding
   window [switch close, switch+K], **K=5 sessions [PROVISIONAL]**; warmup
   for ATR sizing only, 20 sessions of the same window [PROVISIONAL]. Chain
   law: any scoring implementation MUST use the explicit cease-guard
   variant chain (6A: 0 vanished sessions; NQ v3: cg == baseline
   byte-identical) and MUST spread-adjust switch-day returns (corr 0.999
   phantom-drift law, NQ_a3_term via DC §1.3).
   **NQ cross-reference (anti-duplication adjudication)**: NQ-F4 `ROLLWK`
   (baseline, CTG) already occupies the NQ roll-window microstructure class
   (Role B 4 IDs) and its Role A standing audit is the same construction
   law. RMM therefore proposes **no NQ leg**; the v3 repair's contribution
   to NQ runs through NQ-F4 (§4 status proposals), not through a duplicate.
5. **Entry / stand-aside / exit [PROVISIONAL]** (Role B gated leg only):
   signal day = switch session t; entry = open of the first 1m bar after t
   close (next-bar open conservative fill law; no limit/queue claims);
   **mandatory delay variants +1 bar and +30m**; direction = the two arms
   of field 2, both tails registered (PB §4.6 law); stand-aside: (i) switch
   sessions overlapping FOMC/ECB/MPC/BoJ decision windows EXCLUDE
   (event-stacking; the 6J 2022-09-20 exemplar sits INSIDE the Sep-2022
   intervention week — flagged stratum, never base); (ii) calendar-uncertain
   days EXCLUDE/NOT_RUN (6B holiday grid 0/42 — holiday-adjacent switches
   EXCLUDE fail-closed); (iii) 6A legs before 2020-11-23 carry the era tick
   caveat and enter only descriptive views until the D-2 cost audit lands;
   (iv) the three held-dead exemplar days (2022-09-20 6J; 2024-12-17 and
   2026-06-16 6A) form the **extremal abrupt stratum — descriptive only,
   0 identities, n=3 fails any ≥5-per-fold floor (pre-declared here,
   mirroring the JF1 regime-subset law)**. Exit: TP 2×SL; SL 1.0×ATR(20
   same-window); same-bar SL-priority; mandatory time exit at switch+K.
   Role A has no entries (construction ledger; GC-F2 precedent).
6. **Baselines / placebo / negative controls**: C1 **mode-block-shuffle
   placebo** — shuffle the abrupt/gradual labels across the same roll
   calendar with a BLOCK shuffle (≥100 seeds; iid shuffle forbidden — the
   label is autocorrelated via era clustering); C2 always-in at the switch
   clock on ALL rolls regardless of mode (does MODE carry anything beyond
   roll-week exposure?); C3 weekday-matched non-roll clock (same weekday
   distribution); C4 delay pair (+1 bar vs +30m). **Family-specific
   negative control = the gradual-mode rolls themselves** (crossover-
   triggered; 6/27 measured on 6A): compressed-flow mechanism predicts
   gradual rolls show NOTHING — if gradual rolls behave like abrupt rolls,
   mode is not the mechanism (K3).
7. **Refutation conditions** (mechanism kills first, then cost):
   - **K1** block-shuffled mode labels reproduce the split ⇒ dead.
   - **K2 both arms below floor at realistic n** ⇒ dead. *Expected-failure
     interpretation, stated plainly* [DERIVED, court §c3 method]: at
     n ≈ 108 FX events, MDE ≈ 12.97×√(100/108) ≈ 12.5 bp-class, versus
     modeled RT 3.6-6.3 (6E) / 6.3-11.2 (6B) / ≈8.5-14.7 (6J) / ≈8.2 (6A)
     bp — **MDE sits at/above the full modeled cost; this family is
     power-marginal by construction, and a null at this n is the
     pre-registered K2 death, NOT evidence of absence**. Role A (0 IDs)
     survives K2 regardless and is the family's guaranteed deliverable.
   - **K3** gradual-mode rolls show the same behavior as abrupt-mode ⇒
     migration-speed is not the mechanism; on FX the family dies (the
     residual would be generic roll-week exposure — a class that on NQ
     already belongs to NQ-F4 Role B; no new FX family may be spun from
     the residual).
   - **K4** delay flip (+1 bar vs +30m sign reversal) ⇒ switch-auction
     microstructure artifact, downgrade to descriptive.
   - **K5** era concentration (effect only 2022, or only in the 2020
     crash-adjacent rolls) ⇒ vol-regime proxy, dead.
   - **K6 Role-A construction gates (scoring preconditions)**: (a) chain
     choice (baseline-code k=5 vs explicit cease-guard) must not flip any
     sign; (b) switch-day returns spread-adjusted; (c) declared-rule and
     measured-rule date divergence (6B 11d; 6A 9-15d) must be reported as
     a sensitivity, never silently normalized.
   - **K7 DC §1.3 boundary**: if the only surviving conditional is a
     function of the roll-GAP level or the rate differential ⇒ out-of-law
     (FX-F5/AF2 territory), family void as proposed.
   - **Registration precondition (declared, not self-ratified)**: Role B
     enters a census only after an owner ruling that a migration-mode
     microstructure hypothesis is distinguishable from "roll timing as
     construction" under DC §1.3 — the NQ-F4 Role B precedent
     (CENSUS_FINAL T5 row) is the cited prior; GC-F2's "never scored as
     alpha" shows the same class CAN be held construction-only.
8. **Cost / spread / slippage sensitivity**: MODELED COST only; fee layer
   corrected (2.46 USD/side T1 all four FX symbols; T2-T4 2.26/2.06/1.86)
   and UNDER REVIEW until a new A7; VERIFIED_VS_ACCOUNT=NOT_RUN. Spread
   close-proxy high-biased: 6E $18.75/side, 6B $18.75/side, 6J $25/side,
   6A $20/side (DC §1.7); slippage {1,2,3} ticks/side ⇒ modeled RT
   3.6-6.3 bp (6E), 6.3-11.2 bp (6B), ≈8.5-14.7 bp (6J, notional
   $79.8k @0.006383), ≈8.2 bp (6A @0.6696) [DERIVED from named measured
   inputs]. Ramp-session fills plausibly face worse-than-median books —
   but **no slippage claim beyond the {1,2,3} tier triple is legal**
   (double-stress forbidden); BBO NOT_RUN. 6A era caveat: the $10/tick
   sub-era doubles tick-denominated cost components before 2020-11-23.
   Words "measured cost"/"complete cost" FORBIDDEN.
9. **Regime / era breaks**: 2020 COVID era (the 2020-03-17 6A switch shows
   receiving volume 99,416 — a crash-adjacent roll; the 2020-03-19 NQ
   crash roll is the class's most extreme member but sits on the excluded
   NQ leg); 2022 vol regime; **rolling 2020-22 vs 2023-26 split mandatory**
   in any scored view; the 6A leg straddles the 2020-11-23 tick boundary
   (era-aware everything, D-2 audit feeds it); 6B London-share drift era
   (28.7→23.7%) annotated as background, never a conditioning variable.
10. **Coverage / hole proof**: 108 roll events (4 symbols × 27, 2020-2026);
    mode classification MEASURED on 6A (21/6), NOT_RUN on 6E/6B/6J until
    the Role-A ledger derives it from the committed switch tables
    (mechanical, prep-legal); panels 1,746 held sessions/symbol, 0
    integrity violations per round-1 dossiers; holes declared: 6B holiday
    grid 0/42 NOT_OBTAINED (holiday-adjacent switch sessions EXCLUDE);
    expiry cells 6E ECU26/ECZ26, 6B 2023Q1-2024Q2, 6A 2023Q1/Q2+2026,
    6J 2023Q1-Q4+2024Q1/Q2+2026Q1-Q4 NOT_OBTAINED, derivation forbidden —
    none of RMM's windows touches expiry-date timing (switch dates are
    measured from bars), declared per law.
11. **Sources**: `6a_roll_measured.json` (mode triggers, variant delta),
    `6j_cease_guard_2022.json`, `6j_identity.json`,
    `6a_tick_adjudication.json`, `cost_roll_events_fxeb.json`
    (`roll_remeasure.6E/6B`), `fx_eb_expiry_2023_2026.json`,
    DATA_READINESS_{6E,6B,6J,6A}.md, `verify/nq_recompute.json` +
    `verify_findings.json` (T2/T5), DC §1.3/§1.1/§1.7, FEES_CORRECTED §2,
    CENSUS_FINAL T5 rows (NQ-F4 Role B precedent; GC-F2 construction-only
    precedent), PB2_ANCESTRY_COURT_DRAFT (dead-corpus distinguishability
    method), NQ_DEEPFOUR_V3_ADDENDUM §10-§11 (Role-A/corr-0.999 law).
    All local, read-only; no new fetches.

---

## 3. R2-F2 `AF4` — Tick-Regime Conditioning (T3 overlay; 6A; PB3 PARK — contingency only)

**Type: T3 conditioning overlay (0 standalone identities), host families
AF1/AF3 (both PB3 PARK ⇒ this proposal creates NO budget surface).
Operationalizes owner design space (c): the 6A era-tick boundary 2020-11-23
as a cost-regime natural experiment.** The boundary's cost-law audit itself
is split out as diagnostic D-2 (§5) so the overlay family and the audit
never blur.

1. **Mechanism + microstructure** [MECHANISM_HYPOTHESIS]. **Who is
   forced/slow**: market makers quoting on a discrete grid, and
   rounding-bound flow (orders whose achievable limit prices snap to the
   old coarser grid). **Why the effect exists**: the measured halving of
   6A's minimum increment (grid 1e-04 = $10.00/tick through 2020-11-20 →
   5e-05 = $5.00/tick from 2020-11-23; zero odd 5e-05-multiple closes in
   327k+ era-1 closes vs ~49% odd share in every era-2 chunk
   [`6a_tick_adjudication.json`; verify T5 recompute]) lowers the book's
   rounding floor: quotes can shade inside the old increment, so
   thin-window price discovery should change — concretely, grid-snap
   overshoot in the thinnest windows (Sydney morning secondary peak,
   19:00-20:00 CT at 1.19-1.27bp |1m ret|; 11:30 Sydney modal slot) is
   predicted to shrink post-break. **Direction deliberately NOT asserted**
   (two-sided, overlay law — the modulation of host anatomy is the
   hypothesis content, as in FX-F5/JF2). **When it must fail**: if 6A's
   thin-window anatomy is invariant across the tick boundary, the grid
   carries nothing (K1); if unchanged-tick symbols shift at the same dates,
   it is a date artifact, not a grid law (K2).
2. **Expected direction, falsifiable** [PROVISIONAL]: the host families'
   session anatomy (AF3's Sydney-morning trigger frequency and thin-book
   fade rates; AF1's ±5' reaction dispersion) DIFFERS between era-1
   (2020-01-02..2020-11-20, 231 sessions) and era-2 (2020-11-23..) beyond
   their placebo bands; falsified if the era split is identical to pooled
   (overlay null = identity with host ⇒ dead). NOT a standalone signal:
   no entry is ever defined from the tick era itself.
3. **PIT feature availability**: era label is deterministic from the
   venue's grid change — **data-side adjudicated** (odd-print GCD evidence,
   break located to the 2020-11-20→23 weekend, reproduced independently in
   round-1 verify T5 with pre/post samples 2020-11-16/18/20 GCD 100,000 vs
   2020-11-23/25/27 GCD 50,000); the official CME rulebook page remains
   BLOCKED_TRANSPORT and the as-of-public announcement date is NOT
   evidenced ⇒ the label is anchored at the MEASURED break (conventional
   anchor, disclosed — this is why D4=2 in §7). Era-1 has only 231
   sessions ⇒ any fold structure fails the ≥5-per-fold floor
   (**pre-declared: era-1 may only ever be a descriptive stratum**, JF1
   subset law). NOT_RUN: 6E/6B tick-constancy at the same boundary
   (D-2 audit step) — required before the cross-symbol negative control
   can be scored; 6J constancy already measured (field 4).
4. **Contract / unit / session / timezone / roll / expiry bindings**:
   6A, AUD 100,000, quote USD-per-AUD; **tick ERA LAW: $10.00/tick to
   2020-11-20, $5.00/tick from 2020-11-23** (all tick-denominated host
   statistics must be era-aware before any pooled use); session 17:00 CT
   Sun → 16:00 CT, hosts bucketed Australia/Sydney local (DC §1.2);
   rolls k=5 + explicit cease-guard (27 rolls, 0 violations measured);
   **cross-symbol negative instrument: 6J, tick 5e-07 = $6.25, measured
   CONSTANT across eras (increment GCD 500 int-nano in the 2020-03,
   2023-01 and 2026-07 sampled eras [`6j_identity.json`])** — 6J did NOT
   change grid at 2020-11. Universe/clock/warmup inherit the host family's
   field 4/5 verbatim; the overlay adds only the era split.
5. **Entry / stand-aside / exit [PROVISIONAL]**: NONE of its own (T3
   overlay; H-G law). Hosts: AF1/AF3 (PB3 PARK). Split: host evaluable
   days into era-1 vs era-2 strata using the as-of measured boundary;
   era-1 descriptive-only (field 3); host specs otherwise unchanged.
6. **Baselines / placebo / negative controls**: host C1-C4 run WITHIN each
   era stratum (placebo bands per stratum); **family-specific negative =
   the same-date anatomy continuity on unchanged-tick 6J**: if 6J's
   thin-window anatomy "shifts" at 2020-11-23 the way 6A's does, the shift
   is a date/crisis artifact (2020 COVID confound), not a grid effect
   (K2); secondary negative = 6E/6B once D-2 proves their constancy
   (NOT_RUN today, declared).
7. **Refutation conditions**: **K1** host anatomy identical across eras ⇒
   conditioning value nil, overlay dead (the overlay's null is identity
   with the host — a null here is a dead conditioning variable, NOT a host
   failure). **K2** 6J date-placebo shifts too ⇒ date artifact, dead.
   **K3** era-1 too thin to adjudicate (231 sessions; fold floor fails) ⇒
   stays descriptive forever unless the owner extends the 2020 panel.
   **K4** attribution: if the 6A discontinuity concentrates in a single
   week ⇒ single-event artifact (e.g. AUD-specific news), not grid law,
   dead. *Expected-failure interpretation*: this family is expected to die
   at K3 (thin era-1) even if the mechanism is real — stated a priori so
   a K3 death is not later re-litigated as a mechanism verdict.
8. **Cost / spread / slippage sensitivity**: no own cost surface; host
   cost floors apply (AF1-7: RT ≈ $54.92 ≈ 8.2 bp, MODELED, UNDER REVIEW).
   **Era-aware recomputation mandatory before any era-1 host scoring**
   (the $10/tick fact is not yet wired into any frozen cost spec — round-1
   6A closing line); the D-2 audit delivers that recomputation.
9. **Regime / era breaks**: the tick boundary IS the family's era
   variable; **the dominant confound is declared: era-1 overlaps the COVID
   crash** (the 231 sessions are crisis-labeled), which is exactly why the
   6J same-date placebo is the load-bearing control; hosts' own era splits
   (2020-22 / 2023-26) reported alongside.
10. **Coverage / hole proof**: 6A panel 2,703,211 outright bars, 1,746
    held sessions, 6BU5 contaminant + instrument-7084 strays excluded
    (round-1 dossier, cited); era-1 = 231 sessions, era-2 ≈ 1,515; 0
    missing 2023 weekdays (measured). Holes: 6E/6B tick-era constancy
    NOT_RUN (D-2); official rulebook page BLOCKED_TRANSPORT (label
    conventional); ABS/China calendars NOT_RUN (hosts' own standing holes,
    unchanged).
11. **Sources**: `6a_tick_adjudication.json`, `6j_identity.json`,
    `verify/verify_findings.json` (T5 tick-era recompute),
    DATA_READINESS_6A.md Dim 1/6, DATA_READINESS_6J.md Dim 1, DC §1.1/§1.2/
    §1.7, FEES_CORRECTED §2, JPY_AUD_HYPOTHESES fields AF1-4/AF3 (host
    anchors), CENSUS_FINAL T3 row convention. All local; zero fetches.

---

## 4. Carried-family status proposals (NOT new families; 0 cap consumption)

These record how round-1 repairs change EXISTING families' preconditions.
They create no identities and propose no registrations.

1. **NQ design-space (a) adjudication — no new NQ family, three cited
   vetoes.** The alias-repaired v3 chain (VERIFIED: 66 rolls; crash roll
   2020-03-19; 49 dead-held 2020 sessions eliminated; cg variant
   byte-identical) makes the 2020 hole measurable with real front data —
   but the candidate new families that the hole was blocking all die on
   existing law: (i) volume/participation-shock continuation = dead
   `XSECT-VOLSHK-S15` signal class (ancestry W1); (ii) OVN-tail /
   overnight classes = the REGISTERED PB1 parent pair's territory +
   baseline §0.5-1 ruling (anti-multi-trial); (iii) roll-window
   microstructure = NQ-F4's registered class (anti-duplication). The
   repair's value routes through the carried families instead (items
   2-3).
2. **NQ-F3 `RUN-REV-NQ`: rebuild precondition status.** Baseline hard
   precondition "full-era rebuild on the alias-recovered series" is now
   executable — the v3 chain exists and is digest-verified (nq_recompute
   T2/digests). NOT claimed done: the a1/a2 AGGREGATE tables beyond the
   chain are still hole-era until re-run; only the chain and 2020
   aggregates are repaired (NQ addendum §9 wording stands). Status
   proposal: rebuild = unblocked-in-principle; NQ-F3 stays CTG (cost A7 +
   calendar 2026 + trial-ceiling arithmetic + K3 concentration risk now
   measurable on real 2020 data — the K3 window is "honest here in a way
   it could not be on the hole-aware series" per NQ addendum §11).
3. **NQ-F4 `ROLLWK`: Role-A audit discharge proposal + D1 upgrade path.**
   NQ-F4 was ranked lowest (D1=1, "family-specific interaction NOT_RUN;
   only adjacent roll anatomy"). The v3 repair + the RMM Role-A ledger
   (shared construction) would let NQ-F4's Role B anatomy gate be measured
   on a repaired chain INCLUDING the crash roll. Status proposal only:
   NQ-F4 remains CTG; no identity added.
4. **FX-F4-6B leg: gap-std anatomy gate unchanged** (0/42 holiday grid
   and gap-std NOT_RUN stand; nothing in round-1 closed it).

---

## 5. Diagnostics (X-class: 0 scored identities, 0-cost descriptive passes; never gate or rescue a family except via pre-declared refutation conditions)

| diag | name | design | D1 | D2 | D3 | D4 | sum |
|---|---|---|---|---|---|---|---|
| D-1 | CEASE-SYNC | Cross-symbol migration-mode synchronization: derive per-roll mode (abrupt=cease-guard-triggered vs gradual=crossover) for all five measured roll sets (6E/6B/6J/6A 27 each + NQ 66 v3) from committed switch tables; test whether abrupt mode clusters on the same calendar weeks across symbols (market-wide liquidity events, e.g. crisis-adjacent quarters) vs symbol-local contract-specific OI dynamics. Placebo: block-shuffled mode calendars ≥100 seeds; null = symbol-local. The 3 held-dead days are the named extremal members. Pure arithmetic on committed artifacts. | 3 | 3 | 3 | 2 | **11** |
| D-2 | TICK-ERA AUDIT | 6A era-aware cost-law audit: (i) recompute the 6A RT cost surface for era-1 at $10.00/tick (spread proxy and tick components double; deliver the corrected table so no 6A spec ever pools across the boundary silently); (ii) spread-proxy step test at 2020-11-23 on 6A vs the same-date 6J placebo; (iii) tick-constancy checks for 6E/6B at the boundary (currently NOT_RUN — closes AF4's secondary control). Feeds every 6A family's cost field; prep-legal descriptive pass. | 3 | 2 | 2 | 2 | **9** |

D-class ordering rule (baseline): sum desc, then D1 desc, then id asc —
D-1 leads.

---

## 6. Ancestry-check table (every candidate vs the dead inventory; citations to FAMILY_FAILURES.jsonl rows and the court/addendum inventories)

Scan basis: all **173** FAMILY_FAILURES.jsonl entries read this lane;
dead FX corpus from PB2_ANCESTRY_COURT_DRAFT §FOREX-FREE-V1/V2 (V1-A3-P1
London-Open Session Continuation −2.353, PF 0.849, 3/3 folds negative,
11,459 trades; V2 six cells 12/12 EXPECTANCY_NONPOSITIVE: A4-P1
Tokyo-range→London-expansion −3.80, A4-P2 London-AM break+retest −3.09);
program-level warning from NQ_DEEPFOUR_V3_ADDENDUM §10 ("FX-spot
session/open — must NOT be transplanted without evidence"; DAYTRADER-100-V1
FX session books cost-marginal, die at ×2.0).

| candidate | nearest dead entries (asset, family_id, primary code) | distinguishability statement | verdict |
|---|---|---|---|
| R2-F1 RMM | FXFV1-A3-P1, FXFV1-A3-P2, FXFV2-A4-P1, FXFV2-A4-P2 (forex; EXPECTANCY_NONPOSITIVE / CONTROL_REPRODUCED_MECHANISM — London-window spot session families); TRACKA2-C1C2C3-REGATED-RANGEFADE (VARIANT_SAME_FAMILY, range-fade class); FXNG1/NG3/NG4 rows (ANCESTRY_RHO_BLOCK class); XSECT-VOLSHK-S15 (crypto volume-shock); TRACKA1-M3-QSTATE (F5_COST_CEILING) | Mechanism class = CONTRACT-MIGRATION microstructure (forced quarterly position transfer between futures contracts). The dead spot corpus contains no contract migration, no receiving/dying contract pair, no migration-speed variable — the signal class is unrepresentable there (court §b test passes). The trigger is the measured migration episode + mode label, NOT a volume spike (no VOLSHK adjacency: ramp volume is a classifier, never the traded signal) and NOT a roll-gap/CIP level (DC §1.3 K7). Not a session-window momentum/fade rename (no London/open/late-NY window anywhere). | **NO VETO** — pass, with K7 boundary clause + NQ-F4 anti-duplication cross-reference |
| R2-F2 AF4 TRC | No tick-grid/regime-conditioning ancestor exists in any dead list; nearest by name only: DT100-71-RVREGIME, DT100-74-VOLTARGET (crypto vol-regime STANDALONE daytrade, NEGATIVE_EXPECTANCY), BAB-LOWBETA (crypto beta) | AF4 is an OVERLAY (0 standalone identities, H-G law) conditioning hosts on a venue microstructure EVENT (measured grid change), not a vol-regime standalone signal; the dead rows are crypto standalone volatility-trading families — different asset, different class, different construction. Hosts AF1/AF3 are ALIVE (PB3 PARK contingency), so no rename of a rejected family either. | **NO VETO** — pass, thin-n K3 pre-declared |
| NQ volume-shock candidate (REJECTED) | XSECT-VOLSHK-S15 (crypto, SELECTION_REJECTION, dollar-volume shock continuation); DT100-70-ONRET, DT100-20-OVERNIGHTFADE (crypto, NEGATIVE_EXPECTANCY) | An NQ volume/participation-shock continuation family is a symbol/era tweak of a rejected signal class — exactly the vetoed pattern. | **VOID — ancestry veto, cited** (W1) |
| NQ overnight/OVN-tail candidate (REJECTED) | (no dead row — blocks on the REGISTERED parent, not the dead list) | PB1 M-A/M-B 24 FROZEN + baseline ESNQ §0.5-1 ruling (OVN-variance-share conditioning = evaluation view, not a new family). | **VOID — anti-multi-trial, not ancestry** |
| FX curve/carry candidate (REJECTED) | (no dead row needed — out-of-law) | DC §1.3 distinguishing law + H-G law: roll-gap/CIP/curve = structural inputs, never alpha. | **VOID — out-of-law (W2)** |

Also cited in every packet's field 7/8 where load-bearing: the FX
cost-domination lesson (NQ addendum §10) transfers as a WARNING into RMM's
D5=1 and K2 honesty clause.

---

## 7. Ranking — 5-dim 0-3 rubric (RANKING_FRAMEWORK.md anchors, applied mechanically; outcome-blind: no return statistic enters any cell)

| rank | family | leg(s) | D1 | D2 | D3 | D4 | D5 | total | status | one-line mechanical basis (artifacts only) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | R2-F1 RMM | 6E/6B/6J/6A | 2 | 3 | 2 | 3 | 1 | **11** | PROPOSAL; Role A 0 IDs; Role B gated on owner DC §1.3 boundary ruling | Roll sets measured on-target multi-era (D1=2: family interaction NOT_RUN, anchor c); actors+timing+mode-negative+dead-corpus unrepresentable (D2=3); kills complete but MDE ≈12.5bp ≥ cost at n≈108 (D3=2); strict-past in-repo mode labels, decide-t/hold-t+1 (D4=3); floor computable, MDE NOT_RUN (D5=1) |
| 2 | R2-F2 AF4 TRC | 6A (overlay) | 2 | 3 | 2 | 2 | 1 | **10** | PROPOSAL; 0 standalone IDs; PB3 PARK contingency only | Tick eras measured on-symbol (D1=2: host interaction NOT_RUN); MMs/rounding+exact boundary+constant-tick 6J negative+dead-corpus no grid (D2=3); kills complete, power NOT_RUN disclosed (D3=2); label data-side, official page BLOCKED_TRANSPORT (D4=2); overlay host floor, MDE NOT_RUN (D5=1) |
| — | D-1 CEASE-SYNC | 5 roll sets | 3 | 3 | 3 | 2 | n/a | **11 (0-12)** | diagnostic, 0 IDs | leads D-class by the baseline ordering rule |
| — | D-2 TICK-ERA AUDIT | 6A(+6E/6B checks) | 3 | 2 | 2 | 2 | n/a | **9 (0-12)** | diagnostic, 0 IDs | cost-law deliverable feeding AF4 + every 6A spec |

Tie-break law not triggered (no equal totals between registrable families).
Divergence disclosure: RMM's D2=3 rests on the court §b distinguishability
test (mechanism class absent from the dead spot corpus), the same anchor
that cost FX-F1 its D2=2 in the baseline — RMM passes where FX-F1 did not
because migration has no spot analog; this is the single most consequential
anchor choice in this table, disclosed for the synthesis lane.

---

## 8. Budget surfaces (marked per dispatch; NO caps invented)

- **FX (6E/6B): no ceiling defined by any standing ruling** (CENSUS_FINAL:
  648 program-hypothetical, uncapped). RMM Role B, if ever legalized,
  adds **4 IDs/leg** (NQ-F4 Role-B convention) ⇒ 6E 4 + 6B 4 = 8 additive
  ⇒ 656 program-hypothetical. AF4: 0 standalone (host×2 strata only).
  Stated plainly, no ceiling applied or assumed.
- **6J: no cap defined — explicit owner ceiling required before any
  registration.** Existing minimal ≈ 29-36 (JF1 11 + JF2 7/host + JF3 11;
  full-grid 96). RMM Role B adds 4 ⇒ ≈ 33-40 minimal-surface
  program-hypothetical.
- **6A: PB3 PARK ⇒ 0 budget.** RMM-6A leg 4 IDs and AF4 0 IDs are
  CONTINGENCY-ONLY census lines; the K0-class thin-n laws already
  pre-registered in the baseline carry over.
- **ES: no proposal.** Cap 24 FROZEN, headroom 0; ESNQ aggregate 36 > 24
  BLOCKED. Any ES family would be born blocked.
- **NQ: no new family.** NQ-F1..F4 remain CTG (no NQ cap defined;
  gated on cost A7 + calendar 2026 + rebuild/arithmetic per CENSUS_FINAL).
  Carried-status items (§4) add 0 identities.
- **Diagnostics D-1/D-2: 0 identities, 0-cost** (prep-legal descriptive
  passes; X-class law: never gate or rescue a family except through
  pre-declared refutation conditions).
- Controls: NOT counted as trial identities (court §c4 convention
  inherited; if ever ruled budgeted, ≥100 seeds × families run applies to
  RMM C1 and AF4 era placebos).

**Proposed-census delta if everything above were someday legalized:
+12 IDs (RMM Role B 8 FX + 4 6J) + 4 contingency-only 6A IDs + 0 ES +
0 NQ.** Nothing here registers anything.

---

## 9. NOT_RUN / NOT_OBTAINED register (this lane)

1. Migration-mode classification for 6E/6B/6J (Role-A ledger) — NOT_RUN
   (6A measured 21/6; mechanical derivation from committed switch tables
   is the first prep-legal step of D-1/RMM Role A).
2. Mode × post-switch-drift interaction (RMM family-specific) — NOT_RUN;
   anatomy-first gate before any Role B freeze.
3. 6E/6B tick-constancy at 2020-11-23 (AF4 secondary control, D-2 step
   iii) — NOT_RUN.
4. 6A era-1 cost table at $10.00/tick (D-2 step i) — NOT_RUN (round-1
   declared the gap; this lane proposes the audit, executes nothing).
5. Official CME rulebook tick-change page — BLOCKED_TRANSPORT (unchanged;
   6A label stays data-side/conventional).
6. Fee account verification (A7) — READY-NOT-RUN (round-1 verify verdict);
   all fees MODELED / UNDER REVIEW; BBO NOT_RUN everywhere.
7. Owner rulings DECLARED (not self-ratified): (a) DC §1.3 boundary for
   RMM Role B; (b) 6J ceiling before any 6J registration; (c) PB3 PARK
   continuation for all 6A lines; (d) ES cap 24 continues to freeze
   everything ES.
8. BoJ intraday stamps, ABS/China calendars, surprise vintages, publish
   latency — inherited NOT_RUN (unchanged; no family designed around them).

---

— End HYPOTHESES_R2.md. Zero PnL/returns entered any cell; zero network;
zero git beyond the one permitted rev-parse; 2 new families + 2 diagnostics
+ 3 carried status items; every ancestry check cited; missing evidence is
NOT_RUN, never PASS. No registration, no trial creation — proposals on
paper only.
