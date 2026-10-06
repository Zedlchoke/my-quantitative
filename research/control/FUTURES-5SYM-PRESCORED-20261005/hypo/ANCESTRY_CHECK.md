# ANCESTRY_CHECK — every 5SYM census candidate vs FAMILY_FAILURES.jsonl (173 rows) and prior census VOIDED classes

- Round: **FUTURES-5SYM-PRESCORED-20261005**, lane **HYPO**. All 173
  rows of `research/wayfinder/FAMILY_FAILURES.jsonl` read in full this
  lane (row numbering = file line order). Prior census VOIDED classes
  re-checked from HYPOTHESES_R2 §6, ESNQ_R3 §4–§5, and
  CANDIDATE_CENSUS_10SYM §3/§5. Outcome-blind; citations only; zero
  re-entry of dead families; reopening of anything requires an owner
  decision, noted only as P5-* (see HYPO_GAPS.md).
- Verdict vocabulary: **NO_VETO** (carried, no dead-class adjacency or
  adjacency disclosed and distinguished) / **OVERLAP-BOUND** (honest
  partial overlap with a dead class; carried with the binding control
  set named) / **HELD** (the family IS the PB2 ancestry pair — status
  HOLD, contingency spec only) / **PARKED-ANCESTRY-CLEAN** (6A rows;
  no dead adjacency; PB3 PARK regardless) / **DEAD-AT-GATE** (EXPWITCH)
  / **VOID** (attempted new candidates killed this round).

## 1. Method

For each candidate: (i) nearest dead rows by mechanism class, window,
and payer; (ii) the court §b distinguishability test (is the mechanism
class representable in the dead construction?); (iii) the anti-variant
identity test (does the candidate merely re-parameterize a dead or
existing family?); (iv) the standing-law screen (DC §1.3 construction-
vs-alpha; H-G overlay law; DC §1.4 lag law; PB §4.6 both-tails law);
(v) the prior VOIDED-class list (R2/R3/ten-hypo) re-affirmed, never
re-litigated.

## 2. NQ candidates

| candidate | nearest dead rows (row# = file line) | distinguishability / overlap statement | verdict |
|---|---|---|---|
| NQ-F1 FOMC-ERA | none on any futures symbol; nearest-name only: CNG1-A4-P1 (#76, crypto FOMC-instant drained-liquidity, ANCESTRY_RHO_BLOCK vs generic vol-shock) | different asset, different construction (crypto taker-flow form vs futures sign-carry); #76 was blocked pre-scoring, never falsified on this class; R3 FOMC re-parameterizations (minutes window, pre-FOMC drift) already VETOED W1+W2 (ESNQ_R3 §4 V3/V4) — re-affirmed, not re-opened | **NO_VETO** (carried class owner) |
| NQ-F2 MACRO-0730-NQ | none on futures; class walls: SFV5-A6-H2 (#22) no; nearest-name DT100 macro-timed books are crypto session books (#141-160 owner-rescore set) | the R3 print-clock extensions stand VETOED W2 (ESNQ_R3 §4 V5/V6) — re-affirmed; no new wall crossed | **NO_VETO** (carried class owner) |
| NQ-F3 RUN-REV-NQ | none on futures multi-day reversion; EOS1 BTC price-state long/flat gates (#125) and ES1 band-trend (#122) are crypto trend/beta classes | different asset and construction; the OVN-tail classes are the REGISTERED PB1 parent's territory (anti-multi-trial, baseline §0.5-1) — NQ-F3 is distinct by horizon (T4 multi-day vs OVN window), the standing adjudication | **NO_VETO** (carried) |
| NQ-F4 ROLLWK Role-B | none; RMM anti-duplication is an anti-duplication law, not a dead row | Role-B interaction NOT_RUN — the family cannot re-enter any dead class because its class has no dead member; anti-duplication with RMM (no RMM NQ leg) re-affirmed | **NO_VETO** (carried; NEEDS_EVIDENCE) |
| ESNQ-F5 EXPWITCH (NQ leg) | none in the ledger (NO_VETO at birth, ESNQ_R3 §5) | **dead at its own pre-declared F5-K6 gate** (K6GATE: part (ii) FAIL, vendor granularity; anti-cherry-pick: not re-tuned). Re-entry NOT permitted by any lane; owner re-adjudication slot minted as P5-OD-1 (default stays dead) | **DEAD-AT-GATE** (recorded REJECT) |

## 3. 6E / 6B candidates

| candidate | nearest dead rows | distinguishability / overlap statement | verdict |
|---|---|---|---|
| FX-F1 London-Range (6E+6B) | #32 FXFV1-A3-P1 London-open session continuation (EXPECTANCY_NONPOSITIVE, PF 0.849, 11,459 trades); #34 FXFV2-A4-P1 Tokyo→London expansion (−3.80); #35 FXFV2-A4-P2 London-AM break+retest (−3.09, CONTROL_REPRODUCED_MECHANISM); #134 TRACKA2-C1C2C3-REGATED-RANGEFADE (gated-variant class closure) | **HELD — this IS the PB2 ancestry pair.** Court §b honest category: partially overlapping dead signal class; D2=2 is the disclosed consequential anchor. NOT a re-entry: the consolidated spec is the pre-existing contingency census, unchanged; no gated variant is added (#134 closes those permanently — "adding an observable is not a new mechanism", owner law 2026-09-26). Scheduling blocked by PB2 HOLD; census gate ≥500 PASSED descriptively (`fx_f1_f4_census.json` 6E 1,362 / 6B 1,342) — a court instrument, not a scored pass | **HELD (PB2)** |
| FX-F2 Policy-Decision (6E FOMC / 6B MPC) | #49 FXFV6-A4-P1 own-economy CPI reaction-direction drift (dead on robustness, razor PF 1.0979); #51 FXFV7-A4-P1 cross-economy release-sign spillover (dead; sham reproduced — cluster #12); #82 FXNG1-A5-P1 release-order drift (dead); #92–95 FXNG4 EZ print-deviation forms (dead on weekday geometry) | distinguishable: those are spot-FX daily-grid release-sign/rollout drift books; FX-F2 conditions on the DECISION minute + first-5m realized sign on the futures venue with archived minute-proof calendars; the intensity-ordering claim (×17.24 / ×9.5 / ×1.73) has no analog in the dead set. Overlap disclosed, not blocking | **OVERLAP-BOUND, NO_VETO** (HOLD via PB2) |
| FX-F3 US-8:30 Spillover (6E+6B) | **#51 FXFV7-A4-P1 is the named near-miss** (cross-economy release-sign spillover continuation drift — same information-transfer class, dead EXPECTANCY_NONPOSITIVE with sham-calendar reproduction); #40 FXFV5-A6-P1 (sham-calendar out-earned anchor → sham control now MANDATORY house standard); #149/#157 crypto overnight-fade rows (non-adjacent) | distinguishability argued on: same-economy (US) print into the futures book; BLS vintage law (absent in the dead constructions); release-minute 1m anchor vs daily-grid windows. The overlap is honest and load-bearing: any FX-F3 scored future MUST carry (i) the sham-calendar control (row 40 standard) and (ii) the unclassified-8:30 weaker-sign-carry requirement | **OVERLAP-BOUND, NO_VETO** (HOLD via PB2) |
| FX-F4 Globex Reopen Gap (6E+6B) | none for reopen-gap on any venue; nearest-name #149 DT100-20-OVERNIGHTFADE / #157 DT100-70-ONRET (crypto overnight fades) | different asset, different construction (venue's own maintenance break vs overnight hold); the ES-side Sunday-reopen W2 veto (PB1 territory) does not reach the FX 23h-venue break structure (disclosed in baseline). M2c erratum consumed (premise correction — an evidence matter, not ancestry) | **NO_VETO** (HOLD via PB2) |
| FX-F5 CIP overlay (6E/6B) | **#56 FXFV8-A5-P1** (inflation-slope anchor; DGS10-level control out-earned 4.01× — falsification cluster #14, "nominal-yield-level exposure in new words"); **#64/#65 FXFV9-A5-P1/P2** (realized-inflation PPP-deviation forms, ANCESTRY_RHO_BLOCK); **#83 FXNG1-A4-P2** (CTL-DGS10LEVEL out-earned; "the DGS10-level shadow remains the most lethal control in the forex program") | the dead rows are STANDALONE differential/misalignment-conditioned books. FX-F5 is lawful ONLY as an H-G overlay with 0 standalone identities; the DC §1.3 law (roll-gap/CIP = structural inputs) plus these rows form its standing out-of-law boundary. Any drift toward standalone ⇒ void; the 0.20 rho bar vs the V8/V9 nominal/PPP shadows must be re-measured at any D2-equivalent stage | **OVERLAP-BOUND** (NEEDS_EVIDENCE; overlay-only) |
| FX-F6 CoT overlay (6E) | **#107–109 COMMNG1-A4-P2 ×3 arms** (bare release-clock control out-earned every positioning book — positioning frontier measured-closed on that substrate); class walls in ESNQ_R3 (CoT-release-clock candidates VETOED) | F6 is overlay-only (0 standalone), 6E-specific, conditioning an intraday host; the COMM precedent binds its scored future (release-clock control mandatory) but does not kill the overlay FORM. 6B near-zero falsifier measured | **OVERLAP-BOUND** (NEEDS_EVIDENCE; overlay-only) |
| RMM Role-B (6E/6B) | #78 CNG1-A5-P1 (crypto quarterly futures pre-expiry positioning drift, ANCESTRY_RHO_BLOCK vs Amihud proxy); #128 TRACKA1-M3-QSTATE (spread-gating F5 cost ceiling, spot); dead spot session corpus (#32/34/35) | R2 §6 court §b test passes: contract-migration microstructure (receiving/dying contract pair, migration-speed variable) is unrepresentable in the dead spot corpus; #78 is a different asset and window (pre-expiry positioning vs inter-contract migration), blocked pre-scoring, never falsified on this class. K7 boundary (roll-gap level / rate differential ⇒ out-of-law) re-affirmed as the internal tripwire | **NO_VETO** (NEEDS_EVIDENCE: interaction; DC §1.3 ruling) |
| attempted NEW: month-end/WMR-fix drift | **#132 TRACKA2-P4A-FIXCERT-01** (fix-certainty premium, declared band below measured cost — own kill rule) + **#140 DTPFX1-A1-MEFIX-VARIANT** (VARIANT_SAME_FAMILY) | twice-dead class; reopening barred by FIXCERT reopening condition (owner amendment with NEW economic basis only — none exists) | **VOID** |

## 4. 6J candidates

| candidate | nearest dead rows | distinguishability / overlap statement | verdict |
|---|---|---|---|
| JF1 BoJ MPM window | no Japan-specific row in the 173; prior-round adjudications: TOKYO-FIX dead ×2 and JP-0850 (TEN-HYPO FXJA); fixing-window class = #132/#140 | MPM decision window ≠ Tokyo fixing window (different hour, different payer — policy decision vs fix-certainty premium); FYJ-SEAS calendar-flow dead ×5 concerned seasonal calendar books, not the decision window | **NO_VETO** (carried) |
| JF2 MOF regime overlay | no dead intervention-class row; nearest-name #79 CNG1-A5-P2 (crypto post-expiry unwind) non-adjacent | lag law (DC §1.4) makes the same-day form impossible, which is the class the dead rows would have occupied; overlay-only | **NO_VETO** (NEEDS_EVIDENCE: owner constant) |
| JF3 Tokyo-morning | **#34 FXFV2-A4-P1 "Tokyo-range compression → London-morning expansion"** (spot FX, 7 pairs, EXPECTANCY_NONPOSITIVE, gross pre-cost already negative) — the census's most important near-miss after FX-F1 | same signal CLASS family (session-structure continuation/fade); distinguishability: 6J futures single-symbol; trigger = Tokyo-morning range-break with hold into London/NY (not compression→expansion trigger); Asia/Tokyo local-clock law; thin-book cost floor. The honest consequence (already the standing record): the dead-spot-corpus warning and full clock/sham placebo set bind JF3's scored future; the FXJA stricter D2 pass (11 vs 12) exists because of exactly this adjacency and stays disclosed, never silently adopted | **OVERLAP-BOUND, NO_VETO** (carried) |
| RMM Role-B (6J) | as RMM general (none binding) | + 6J-specific: 2022-09-20 exemplar sits inside the Sep-2022 intervention week — flagged stratum, never base (event-stacking law) | **NO_VETO** (NEEDS_EVIDENCE) |
| AU-REL / CN-REL dossiers | none (never scored; candidate-grade) | blocked on data (ABS/China calendars NOT_RUN), not ancestry | **NO_VETO** (NEEDS_EVIDENCE: data) |

## 5. 6A candidates (all PB3 PARK regardless of ancestry)

| candidate | nearest dead rows | distinguishability statement | verdict |
|---|---|---|---|
| AF1 RBA decision-minute | none (no RBA/event-class row) | carried with K0 pre-registered | **PARKED-ANCESTRY-CLEAN** |
| AF2 differential overlay | standalone differential forms dead (#56/#64/#65/#83) — same boundary law as FX-F5 | overlay-only; H-G law; K2 vintage bar pre-registered | **PARKED-ANCESTRY-CLEAN** (boundary cited) |
| AF3 bimodal U-curve | none on 6A | China-window K4 boundary is data-absence, not ancestry | **PARKED-ANCESTRY-CLEAN** |
| AF4 tick-regime overlay | none (no tick-grid ancestor; R2 §6) — nearest-name #158/#160 crypto vol-regime standalones | overlay (0 standalone) vs dead standalone vol classes; constant-tick 6J/6E/6B negative instruments | **PARKED-ANCESTRY-CLEAN** |
| RMM Role-B (6A) | as RMM general | mode split MEASURED 21/6; PB3 PARK | **PARKED-ANCESTRY-CLEAN** (NEEDS_EVIDENCE: interaction) |

## 6. Diagnostics and cross-checks

- **D-1 CEASE-SYNC / D-2 TICK-ERA AUDIT**: X-class, 0 identities;
  descriptive only; cannot gate or rescue any family except through
  pre-declared refutation conditions (delivered: JF1-K3 anchor
  robustness feeds JF1's K3; 6E/6B constancy closes AF4's secondary
  control).
- **Prior census VOIDED classes re-affirmed (not re-opened)**: NQ
  volume-shock (W1, row #4 XSECT-VOLSHK-S15); NQ overnight/OVN-tail
  (anti-multi-trial, PB1 territory); FX curve/carry standalone (W2,
  DC §1.3); ESNQ-F5 EXPWITCH both legs (dead-at-gate); ten-hypo
  FXJA/FXEB veto walls (fix-certainty ×2, UK/euro own-economy classes,
  lead-lag #51, round-levels) — all stand.

## 7. Near-miss register (the overlaps a future reader must not miss)

1. **FX-F1 vs #32/#34/#35** — the PB2 ancestry pair itself (HELD).
2. **JF3 vs #34** — same-window-pair dead spot family; class overlap
   honest; JF3's placebo set binds.
3. **FX-F3 vs #51** — information-transfer class overlap; sham-calendar
   control mandatory (row 40 standard).
4. **FX-F5/AF2 vs #56/#64/#65/#83** — the nominal-level shadow; overlay
   boundary is the only lawful posture; rho bar re-measure at D2-class
   stage.
5. **FX-F6 vs #107–109** — positioning release-clock precedent;
   release-clock control mandatory in any scored future.
6. **RMM vs #78** — nearest-name crypto pre-expiry class; different
   asset/window; disclosed at D2-class stages.
7. **NQ-F3 vs PB1 (registered, not dead)** — anti-multi-trial adjacency
   by horizon; standing adjudication re-affirmed.

**Zero re-entry of dead families: confirmed.** Every HOLD/PARK/REJECT
ancestor keeps its status; every carried row is the pre-existing
consolidated spec with its committed precondition upgrades consumed;
the single disposition change this round is EXPWITCH (already dead at
its own gate — recorded, not changed by this lane).

— End ANCESTRY_CHECK.md. Machine mirror: `ancestry_check.json`.
