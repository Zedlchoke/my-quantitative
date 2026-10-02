# HYPOTHESIS_REGISTER — successor_design_2026-10-02

Complete re-adjudication of EVERY hypothesis the corpus has produced (dockets
A/B/C, RULE_SLATE incl. benched rows, DP §5 paths, daily_successor DS legs),
plus new hypotheses from this session's census. Law: every hypothesis names
its attribution law (trig / pfold / solo — census §5); every carry-over
trigger shaped on the exposed folds is labeled POST_OUTCOME_HYPOTHESIS;
nothing here is validated — the register exists so the successor cycle can
preregister, and so dead ideas are not re-mined.

Status vocabulary: **KEEP** (unchanged, preregister as drafted) · **AMEND**
(kept with stated change) · **REFUTED-BY-EVIDENCE** (measured kill on
available data; do not re-mine) · **DATA-BLOCKED** (well-posed, cannot run;
named unlock) · **EXECUTED-NEGATIVE** (ran and closed) · **BASELINE-CLASS**
(control, not edge) · **DESIGN-LAW** (protocol requirement, not a
hypothesis).

---

## Part 1 — Prior hypotheses, re-adjudicated

### USDJPY family (docket A)

**A-H1 / SU-RS-J3 — relax/remove the L6 cost guard (ON-admission, S026). AMEND.**
- Prior basis: 331 defers; 29 B1-filled matched defers +274,572 (16W/13L,
  one trade 46%); removing them worsens B1 DD −378k→−501k `[trig/derived]`.
- New evidence this session: S026 **solo** = +9,203 (DD 299,849) vs trig
  +825k — the guard's deferrals were protecting/removing trades whose value
  exists only inside the netted blend; an eligibility-oracle control (B8)
  LOST ~300k vs always-on, warning that ANY admission-side meddling with the
  blend, even favorable-looking, can destroy path value.
- Amendment: hypothesis is retained but its predicted-benefit band is
  cut to "recovery of a share of the +274.6k attribution, sign-uncertain";
  it may ONLY be tested with leave-one-rule-out AND leave-one-leg arms
  live; the ×1.5 multiplier remains a free parameter learned on LEARN
  (grid {1.5, 2.0, ∞} per RULE_SLATE §4). Overfit risk HIGH (n=29, one
  trade 46%). POST_OUTCOME_HYPOTHESIS.
- Anti-hypothesis (unchanged, plus): ≥20 admitted defers net ≤ 0 pooled; any
  fold's admitted set nets below −pooled gain; admitted set worsens slate
  DD vs always-on; NEW — solo-S026 evidence suggests the admitted re-entries
  alone are a coin-flip: if the LORO-without-S003/S023 arms show the guard's
  value collapsing when the trend core is absent, the mechanism is
  blend-protection, not signal-quality — retype and close.

**A-H2 / SU-RS-J1 — block USDJPY NY-session LONG entries. KEEP (highest-confidence rule).**
- Basis unchanged: only rule PnL- and DD-consistent in BOTH arms and all 8
  folds (POLICY −281,460 n=91 / B1 −83,684 n=74; London longs +972k);
  mechanism named (post-London-close liquidity fade; PDH-break longs pay
  widening cells into thin afternoons); long-only split is POST_OUTCOME.
- Note: survives the oracle-control warning because it is entry-admission
  on a specific symbol/session, not portfolio gating; and its two-sided
  table is mandatory (50 losers −795.8k avoided vs 38 winners +514.4k
  suppressed).
- Anti-hypothesis: unchanged (REFUTED if blocked set nets ≥0 pooled, or ≥2
  fresh folds negative, or DD worsens in ≥3/6 folds, or one suppressed
  winner > 50% of avoided-loss total). Floors ≥3/fold, ≥20/window.

**A-H3 — exempt calendar-sparse legs from E1. AMEND (merged into new HN-2 clock-aware floors).**
- Prior basis: blocked S002/S003/S023/VC2-JPY worth +428.7k paper / +187.1k
  realized entries `[pfold/derived]`; HIGH-RISK (exemption list = exposed
  blocked set).
- New evidence: S002-JPY **solo always-on −248,990 vs floored +137,883** —
  the floor on S002 was not a mistake but a save; a blanket "sparse-leg
  exemption" would have re-admitted a solo-disaster. The exemption must be
  leg-conditional on something other than sparsity. Merged into HN-2.

**A-H4 / SU-RS-J2 — retire USDJPY meanrev (S014). AMEND — evidence weakened, test-law changed.**
- Prior basis: S014-triggered excursions −222,301/−319,604 `[trig]`;
  RSI2_MID_CROSS family −470,442 (n=33); "mechanistically cleanest
  negative."
- **New evidence this session (material): S014 solo = +109,448 (DD 58,494)
  in BOTH solo arms; pfold attribution +34,984.** Two of three attribution
  laws say S014 is POSITIVE. The retire hypothesis now rests on ONE law
  (entry-trigger) and is directly contradicted by the leg's standalone
  economics. The honest position: S014 is either (a) a positive leg whose
  entries get mistimed inside the blend, or (b) a hedge whose removal
  worsens the blend — undecidable without portfolio-minus-S014 `[NR]`.
- Amendment: demoted from "retire" to "MEASURE FIRST": S014's fate is
  decided by the leave-one-leg arm on the fresh calendar, not by a
  preregistered retire. If a retire is still desired by the owner, its
  anti-hypothesis gains: REFUTED if LORO-without-S014 nets ≤ slate AND DD
  worse (the netting-hedge channel, docket A §7-H4, now the PRIMARY risk,
  not a footnote). POST_OUTCOME_HYPOTHESIS (family chosen after seeing
  folds).

**A-H5 — micro-flip churn is pure friction. KEEP BENCHED (as RULE_SLATE: trigger not decision-time lawful; +2–4k ceiling).**
- Re-entry condition unchanged (TB-LABELS shows friction-dominance
  persisting AND a decision-time reformulation). Note new solo evidence:
  the churn IS the cascade's breathing — S026 solo shows 1,844 fills for
  +9.2k; any churn-filter experiment must guard the re-entry chain.

### EURUSD family (docket B)

**B-H-E1 / SU-RS-E2 — codify E1 floor for SIG-exit-only legs. AMEND (merged into HN-2).**
- Prior basis: S009 always-on −587.8 (TEST) vs TRAIN +7,207 prior that did
  not transfer; floor avoided ≈ +504; solo S009 −2,127.77 confirms
  `[solo,M]`.
- New evidence: the same floor on S002-JPY saved a solo-negative leg
  (−249k → +137.9k floored). The floor's value generalizes beyond
  "SIG-exit-only": the common thread is legs whose TRAIN prior does not
  transfer AND whose realized book goes negative — an outcome-conditional
  floor is look-ahead, so the lawful generalization is the clock-aware,
  prior-transfer-checked floor (HN-2). B-H-E1 survives as ONE INSTANCE of
  HN-2 with its constants inherited frozen (3/26w, no retuning).

**B-H-E2 / SU-RS-E1 — EURUSD 12:00/16:00 entry gate. KEEP with unchanged HIGH-RISK flag, folded into HN-4.**
- Hour set was scanned on exposed journals (POST_OUTCOME); mechanism
  (handover spread widening + H4-clock meanrev votes) independently named
  and cost-visible; admissible only via preregistered per-symbol grid
  re-learned on fresh LEARN. Folded into the unified session-admission
  family HN-4 to cut multiple-testing count. Anti-hypothesis unchanged:
  REFUTED if suppressed-hour book nets >0 pooled or in ≥3 folds, or DD
  reduction fails to reproduce.

**B-H-E3 — admit VC2-LVNFAIL-EURUSD. KEEP BENCHED (under-powered n=26/13; pair-cherry-pick risk).**
- Unchanged: re-entry if first fresh-fold review shows blocked set ≥50
  trades with positive net → register as amendment, never mid-cycle. Solo
  +75.30 `[M]` adds nothing at this n.

**B-H-G1 / SU-RS-G1 — retire GBPUSD-S017. KEEP (stop-geometry mechanism, zero parameters).**
- Basis unchanged: both arms negative, 20SL:6TP, 15/28 ≤1-minute stop-outs;
  solo −318.71/−95.02 `[M, new]` — all three attribution laws now agree →
  strongest retire candidate in the register. Anti-hypothesis unchanged
  (TP share ≥40% or pooled >0 on fresh replication refutes). Floor ≥50.

**B-H-G2 — widen GBPUSD-S002 stop to ±3 pips (TB-EXIT-OVERLAY node). KEEP DATA-BLOCKED (exit-law change = new identity, needs fresh calendar + TB-LABELS).**
- Unchanged; dual-side law per RULE_SLATE §2. Explicitly NOT
  journal-recomputable; barrier-touch ordering [NR].

### H1-pair family (docket C)

**C-H-C1 — spread-cell reprice of USDCAD-S011/S091. KEEP DATA-BLOCKED** (per-fill hour-stamped pricing or owner-frozen cell schedule; both ×1.0-positive legs died only at ×2.0).
**C-H-C2 — swap drag dominates AUDUSD hold-heavy legs. KEEP DATA-BLOCKED** (owner Activity/Flex statement; swap events 353:1 fills on S002-AUD).
**C-H-C3 — Friday-deferral asymmetry AUDUSD-specific. KEEP DATA-BLOCKED** (amended fill law / denser Friday panel).
All three keep their exact failure conditions (docket C §1.4). A successor
re-attempt on these symbols additionally requires the changed-mechanism-axis
law (TERMINAL Q-10) — cost-infrastructure changes qualify; same-rule retries
do not.

### DP §5 ranked paths — status after DAILY-EXPLORATORY-V1

| path | status now |
|---|---|
| 1. Daily-cohort cycle | **EXECUTED-NEGATIVE** as DAILY-EXPLORATORY-V1 (DS-03/DS-05; every arm negative; NOT_RUN_THIN aggregate). The 5 parked candidates (DP §6 rows 1,3,4,6,7) remain UNADJUDICATED — parked by owner law, not by evidence; any re-attempt inherits P-35 (clock/floor geometry) and must justify decision-rate BEFORE registration |
| 2. TB-LABELS (analysis-only) | **NOT RUN — unchanged.** Now the single highest-leverage analysis unlock (feeds A-H5, B-H-G2, MAE/MFE, exit forensics). See HN-6 |
| 3. TB-EXIT-OVERLAY | **DATA-BLOCKED** (fresh calendar required; 57-row design registered) |
| 4. EOSV2 V3 | DATA-BLOCKED on owner-named tuples; walls structural (G3 margin ~−1.25M) |
| 5. Always-on carry book | **BASELINE-CLASS**: B1 always-on remains the designated primary baseline (B1S) of the successor battery, not an edge claim; its P1-B0/B1 positive is [M] under DECLARED costs, DSR-deflated REJECT on selection overlap (DP corr-1) |

### RULE_SLATE rows 7–12 (benched) — unchanged dispositions
B-H-E3 (bench, under-powered) · A-H3 (merged → HN-2) · A-H5 (bench) ·
C-H-C1/C2/C3 (data-blocked). R-G2 hour-8-only and R-G3/R-E4 direction
gates: **REFUTED-BY-EVIDENCE** (docket B §6: regime artifacts / remove
profit) — do not re-mine.

### Additional measured nulls to carry as dead (do not re-mine)
- **Decision-density (dct) deferral**: null-to-harmful (δ=0.028; defers cut
  −580k of net at dct>100) — REFUTED-BY-EVIDENCE (docket A §6).
- **Portfolio-level gating/overlay classes** (7 terminal deaths + B8 oracle
  −300k vs always-on + B5 clock −92% + B2 equal-weight −332k + B6 inverted
  −256k): REFUTED-BY-EVIDENCE **as a class on this calendar** — the
  successor may only propose per-symbol/per-entry rules or leg retirement,
  never portfolio-level participation gates over the blend.
- **DS-03/DS-05 legs** (xasset_energy_lng, usdbasket_rank at daily clock):
  EXECUTED-NEGATIVE, family failure CLOSED (DEV1-DAILY-EXPLORATORY-DS03-DS05).

---

## Part 2 — New hypotheses from this session (HN-*)

### HN-1 — Unified handover-session admission family (USDJPY + EURUSD instances)
- **Corpus/journal basis:** USDJPY NY-longs negative both arms all folds
  (−281k/−84k) `[M]`; EURUSD hours 12/16z suppressed-book negative both
  arms (−496/−1,037) `[derived]`; both mechanisms are the SAME structural
  window (London→NY liquidity handover, widening quoted spreads,
  cost-visible in session medians).
- **Economic mechanism:** orders routed into the handover window pay the
  widening crossing exactly when continuation probability decays
  (PDH-break longs after London close; H4 meanrev votes inside the
  handover).
- **Trigger (PIT-at-entry):** per symbol, a preregistered UTC-hour set ×
  direction scope, evaluated on the decision row's timestamp before order
  emission. Hour sets learned ONLY on fresh-LEARN from a structural anchor
  grid around the London close (16z±1) and the handover votes (12z±1) —
  never from exposed-fold scans.
- **Action:** OFF (defer entry) for that decision only; exits untouched.
- **Why it can help:** removes the only admission buckets sign-consistent
  on both arms/quantities. **Why it can fail:** the hours are
  fold-shaped (POST_OUTCOME); blocking handover entries also blocks
  re-entries of the S026 cascade whose value is path-dependent (solo-S026
  warning); NY DD improvement (−412k→−360k) may not reproduce.
- **Samples/clustering/overfit:** USDJPY 91/74 trades across 8 folds (min
  fold 5); EURUSD 57/59; winner-concentration risk documented (38
  suppressed winners +514k USDJPY). One family, two per-symbol instances,
  one shared structural anchor — total free parameters: 2 hour-sets.
- **Missing data:** per-fill quoted spread at entry (C-cell bands are
  declared, not per-fill measured).
- **Controls & refutation:** dwell-matched random battery + clock-shadow +
  PLACEBO-SESSION (block the symmetric Tokyo-morning hours as a null —
  if the placebo "works" too, the mechanism is cadence, not the handover);
  REFUTED per symbol if suppressed book nets ≥0 pooled, or ≥2 fresh folds
  negative-effect, or placebo passes equally. Floors ≥3/fold ≥20/window
  (USDJPY), ≥40/window (EURUSD).
- **Label:** POST_OUTCOME_HYPOTHESIS (both instances).

### HN-2 — Clock-aware activity floors (generalizes B-H-E1 + A-H3)
- **Basis:** E1 floor pooled +17.3k; saved S009 (−504 avoided) and S002-JPY
  (solo −249k → floored +138k) but blocked S003/S023 (B1 realized entries
  +187k; paper +428.7k) `[M/derived]`. The floor's errors are all
  CLOCK-TYPE errors: one global 3-decisions/26w rate applied to monthly,
  weekly, daily and M1 legs alike.
- **Mechanism:** an activity floor can only detect a dead leg relative to
  its own clock's expected decision rate; calendar-sparse legs (tsmom
  monthly, squeeze weekly) are sparse BY DESIGN; M1 legs (VOLPROF) are
  fast by design.
- **Trigger (PIT):** at decision time, leg eligibility OFF if trailing
  realized decision rate < f × the leg's corpus-declared clock expectation
  (e.g., < 1/3 of expected decisions per 26w for its declared clock), with
  f inherited-frozen = the E1 ratio (no retuning); SIG-exit-only legs keep
  the original strict 3/26w law (B-H-E1 constants frozen).
- **Why it helps:** keeps the measured S009/S002 saves while unblocking the
  S003/S023 class. **Why it fails:** the corpus clock metadata may be wrong
  for some legs; unblocking S002-JPY fully (its rate is low for a
  multimonth leg) could re-admit the solo-negative book — the f-ratio must
  be validated per leg on LEARN before fold-1.
- **Samples:** legs with ≥20 admitted or blocked decisions per window;
  blocked-set two-sided tables mandatory (missed-winners vs avoided-losers
  per leg per fold).
- **Missing data:** none for the trigger itself (decision history is
  journaled); attribution of blocked value needs LORO-by-leg arms.
- **Controls & refutation:** REFUTED if, pooled over fresh folds, the
  floors' suppressed books net > 0 (missed-winners bar P-MW), or any leg
  unblocked by the clock-awareness realizes ≤ 0 while its floor was OFF
  (false-admission bar P-FA). Clock-shadow control on the floor cadence.
- **Label:** POST_OUTCOME_HYPOTHESIS (generalization shaped by the S003/
  S023/S009/S002 outcomes).

### HN-3 — S014 netting-hedge measurement (replaces "retire S014")
- **Basis:** attribution conflict (trig −222k/−320k vs solo +109k vs pfold
  +35k) `[M]` — the only leg in the corpus whose sign flips by attribution
  law. No minus-one artifact exists.
- **Mechanism (hypothesis, not evidence):** a counter-trend fade holding
  overnight inventory opposite the trend core may be paying the blend as a
  hedge (its losses are the trend core's insurance) or bleeding it
  (fighting the macro trend with a mid-cross exit).
- **Design:** NOT a strategy rule. A leave-one-leg identity (SLATE∖S014 vs
  SLATE) on the fresh calendar answers it; decide S014's fate by
  preregistered rule: if net(SLATE∖S014) ≥ net(SLATE) AND maxDD(SLATE∖S014)
  ≤ maxDD(SLATE) → retire is justified on fresh data; else keep (and the
  trig attribution is declared blend-artifact).
- **Refutation/controls:** the LORO arm IS the test; two-sided table
  mandatory; floor ≥20 would-be S014 entries per window in the LORO arm.
- **Label:** POST_OUTCOME_HYPOTHESIS.

### HN-4 — (reserved; HN-1 subsumes the earlier SU-RS-J1/E1 numbering merge)

### HN-5 — USD-cluster exposure cap (sizing-layer, capped scope)
- **Basis:** co-loss weeks are the common-USD regime (27/208 weeks, all
  EUR×JPY; 2022 clusters) `[derived]`; USDJPY long-dominant + GBPUSD
  short-profitable = concurrent long-USD in the rally; no fold shows EUR/GBP
  offsetting a USDJPY drawdown.
- **Mechanism:** the portfolio's dominant risk factor is USD, not any leg;
  a soft cluster cap (reduce NEW entries when net portfolio USD-factor
  exposure exceeds a frozen multiple of its LEARN-window distribution)
  trades a slice of the rally's tail for drawdown control.
- **Trigger (PIT):** computed from open positions + pending votes at
  decision time; no future data.
- **Why it helps:** caps the only measured common factor. **Why it fails
  badly:** SIZE-layer interventions on this calendar measured ≈ $0
  (SIZE −7.3k; supermajority pathdown −31.7k) while the blend's value is
  path persistence (CARRY +242k) — a cap that trims the trend carry may
  cost more than the co-losses it avoids. B2 equal-weight re-sizing lost
  −332k.
- **Controls & refutation:** must beat both B1S AND an uncapped slate on
  the AND-pair; REFUTED if net < B1S or DD ≥ B1S at ×1.5; also REFUTED if
  the cap binds in < 5% of decision hours (vacuous) or > 50% (it is a
  gate in disguise → re-classify and apply the F1 class-refutation).
- **Label:** POST_OUTCOME_HYPOTHESIS (factor identified on exposed folds).

### HN-6 — TB-LABELS producer run (analysis-only unlock; makes NO claim)
- **Basis:** design frozen (`triple_barrier/INVENTORY_AND_DESIGN.md` §2a
  firewall); M1 panels exist for exactly the 3 journaled symbols; every
  exit-geometry question (S013 2.8σ ordering, S017 1-min stop-outs, S002
  ±2-pip vs ±3, MAE/MFE separation, "did the stop touch before the
  target") is [NR] without it.
- **Action:** offline labeling over committed panels, TRAIN-side +
  already-exposed folds labeled as EXPOSED (labels for forensics only);
  feeds B-H-G2, A-H5 re-entry, and the successor engine's MAE/MFE fields.
- **Refutation:** n/a (not a claim); firewall violations (any test-fold
  label informing a rule before LEARN) are a STOP-3 integrity kill.

---

## Part 3 — Register summary (what the successor preregisters)

| id | symbol/leg | class | status into successor |
|---|---|---|---|
| SU-RS-J1 / HN-1-JPY | USDJPY | OFF entry (session×direction) | preregister (family HN-1) |
| SU-RS-E1 / HN-1-EUR | EURUSD | OFF entry (hour set) | preregister (family HN-1) |
| SU-RS-E2 / HN-2 | EURUSD + all legs | floor (clock-aware) | preregister (HN-2; E1 constants frozen) |
| SU-RS-G1 | GBPUSD-S017 | retire | preregister (three-law agreement) |
| SU-RS-J3 / A-H1 | USDJPY-S026 | ON admission (guard) | preregister ONLY with LORO×LORO arms (HIGH overfit) |
| SU-RS-J2 / HN-3 | USDJPY-S014 | retire→measure | preregister as LORO-decided rule |
| HN-5 | portfolio | USD-cluster cap | optional single identity, strict anti-hypothesis |
| B-H-E3 | EURUSD VC2 | admit | benched (floor-gated re-entry) |
| A-H5 | USDJPY | churn filter | benched (needs HN-6) |
| B-H-G2 | GBPUSD-S002 | exit overlay | data-blocked (HN-6 + fresh calendar) |
| C-H-C1/C2/C3 | USDCAD/AUDUSD | cost family | data-blocked (named owner unlocks) |
| DP paths 2/3/4 | — | analysis/new-identity | HN-6 now; others blocked |
| gating-overlay class | portfolio | — | REFUTED-BY-EVIDENCE (class) |
| dct-density deferral | USDJPY | — | REFUTED-BY-EVIDENCE |
| direction gates, hour-8-only | EUR/GBP | — | REFUTED-BY-EVIDENCE |
| DS-03/DS-05 | daily | — | EXECUTED-NEGATIVE (closed) |

— end register —
