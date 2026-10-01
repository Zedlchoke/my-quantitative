# RULE_SLATE — PC12A successor rule slate (DRAFT FOR OWNER REVIEW; NOT RUN)

**STATUS HEADER — READ FIRST.** This is a *preregistration design artifact* for
a hypothetical successor cycle. Nothing in it has been run, scored or
validated. Every measurement cited is a retrospective read of the PC12A
**exposed scored TEST folds** (2022-01-07→2025-12-26) or TRAIN-only
diagnostics produced by the three symbol dockets — **those 8 test folds are
EXPOSED and can never serve as validation**; they justify preregistration
only. No engine run, no S1, no network, no ledger write occurred for this
file. Hypothesis-generating throughout. Missing evidence is `NOT_RUN`, never
inferred PASS.

Prepared 2026-10-01 for the terminal-review successor program prep
(DECISION_PACKET §11/§12, owner steering D-B). Inputs:

- `research/control/terminal_review_2026-10-01/symbol_docket/USDJPY_DOCKET.md` (cited "A §n")
- `research/control/terminal_review_2026-10-01/symbol_docket/EURGBP_DOCKET.md` (cited "B §n")
- `research/control/terminal_review_2026-10-01/symbol_docket/H1_AND_BLOCKED_DOCKET.md` (cited "C §n")
- `research/control/terminal_review_2026-10-01/DECISION_PACKET.md` (cited "DP §n")
- `research/control/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/policy/PASS_BARS_V2.md` (cited "PB2 §n")
- `research/control/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/campaign/BACKTEST_CAMPAIGN_DESIGN.md` (cited "CAM §n")
- `research/control/PC12A-7ASSET-DATA-UNBLOCK-2026-10-01/GATE_UPDATE_7ASSETS.md` + `OWNER_PACKET.md` (read-only at branch `orca/pc12a-7asset-unblock-20261001`; cited "UNBLOCK")
- `…/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/poolB/data_audit/audit_summary.json` (panel spans)

**Units caveat inherited (A §0):** all USDJPY magnitudes are journal units
under the frozen at-par JPY quote-currency convention; the successor engine
must implement explicit quote→USD conversion before any dollar bar is read.
Anti-hypothesis thresholds below are therefore stated in *relative*
(improvement-sign, fold-count, ratio) terms wherever possible.

---

## 1. Ranking of the 12 docket hypotheses

The dockets carry 13 falsifiable hypotheses; 12 are on/off (entry/governance)
hypotheses and form the ranked table below. The 13th — B H-G2 (widen
GBPUSD-S002's ±2-pip stop as a TB-EXIT-OVERLAY node) — is an **exit-law**
hypothesis that names the registered TB lane, not an eligibility rule
(B §7), and is out of this slate's scope by construction.

Axis definitions (per dispatch; ranking is on these, NOT exposed PnL):
(a) **mechanism** — is the causal story about market structure/flow, or a
mined pattern; (b) **coverage** — n of measured decisions/trades and the
min-fold cell; (c) **overfit risk** — free parameters, and whether the
trigger shape was chosen AFTER looking at the exposed folds.

| # | hypothesis (docket id / DP §11.3 id) | symbol | (a) mechanism | (b) coverage | (c) overfit risk | one-line justification |
|---|---|---|---|---|---|---|
| 1 | A-H2 / H-J1 — block NY-session LONG entries | USDJPY | HIGH — liquidity fade after London close; PDH-break longs pay widening C2/C3 cells into thin NY afternoons (A §3, §6) | n=91 POLICY + 74 B1 NY entries, sign-consistent all 8 folds; min fold 5 | MEDIUM — bounds [16,21)z anchor on a structural boundary (London close), but the LONG-only asymmetry was identified on the exposed folds | Only rule PnL- and DD-consistent in BOTH arms and all folds (A §6); mechanism named, not fitted |
| 2 | A-H4 / H-J3 — meanrev family (S014) off | USDJPY | HIGH — RSI2 fade repeatedly sells a macro-trending pair; mid-cross exit realizes the damage (A §3, §7-H4) | family n=53 pooled excursions (thin); S014 negative in both arms every traded fold | MEDIUM-LOW — family selected post-observation but the mechanism (counter-trend fade vs macro trend) is structural; netting-hedge risk must be checked, not assumed | Mechanistically cleanest negative in the docket; family-level OFF, no fitted threshold |
| 3 | B-H-G1 — retire GBPUSD-S017 | GBPUSD | HIGH — +1σ stop sits inside entry-bar noise at the M1 clock: 20 SL : 6 TP, 15/28 close ≤1 min (B §4) | 28 POLICY / 39 B1 trades; fold cells 1–8 (thin) | MEDIUM — retirement decided after seeing the TEST book, but the stop-geometry argument is instrument-physics, not PnL fitting | Stop-geometry mechanism + negative both arms 6–7/8 folds; smallest parameter count of any rule (zero) |
| 4 | B-H-E1 — codify E1 activity floor for SIG-exit-only legs | EURUSD | MEDIUM-HIGH — a SIG-only exit leg with <3 decisions/26w has no adaptive information to size against; TRAIN prior did not transfer (B §7-H-E1) | S009 always-on n=50, missed-set n=49; ≤0 in 5/7 traded folds | MEDIUM-LOW — the floor's constants (3/26w) predate scoring (PC12A POLICY layer); "SIG-exit-only" scoping is the only new generalization | The floor was the policy's one measured win (R-E1 avoided ≈ $504); retention, not new fitting |
| 5 | A-H1 / H-J2 — re-tune/remove L6 cost guard (admit defers) | USDJPY | MEDIUM — guard caps re-entries exactly when the stop-cascade's continuation frequency peaks (A §7-H1) | matched-defer set n=29 only; folds {1,2,3,5,6,7}, min fold 1; one trade = 46% of effect | HIGH — derived attribution on B1's path, n=29, heavy concentration; the ×1.5 cap multiple is a post-hoc free parameter | Large B1-path attribution (+274.6k journal units on the 29 matched defers; not an ablation — the causal effect of relaxing the guard is unmeasured) but the weakest evidence base of the top six; enters the slate only with a grid + strict anti-hypothesis |
| 6 | B-H-E2 — EURUSD 12:00/16:00 entry gate | EURUSD | MEDIUM-HIGH — H4-clock meanrev vote inside the London/NY handover + NY-open spread widening, cost-visible (B §5, §7-H-E2) | 57/59 suppressed trades (POLICY/B1), 6/8 folds each | **HIGH-RISK — trigger shaped on exposed folds: the hour set {12,16} was picked from the entry-hour table computed on the scored journals (B §3: hour 16 worst on POLICY, hour 12 worst on B1)** | Consistent both arms and halves pair DD, but the specific hours are a fold-shaped choice; admissible only via a preregistered grid re-learned on fresh TRAIN |
| 7 | B-H-E3 — admit VC2-LVNFAIL-EURUSD | EURUSD | MEDIUM — E1 floor is calibrated for daily/weekly clocks and mis-fires on M1 VOLPROF; cost-light barriers, no O/N swap (B §7-H-E3) | n=26 B1 book / 13 strictly-missed — under-powered (docket's own ranking note) | MEDIUM-HIGH — pair-cherry-pick: EUR admitted vs VC2-GBPUSD TRAIN-negative (B §1, §8); pair specificity chosen after seeing both | Positive 6/8 folds and design-faithful exits, but n cannot carry a rule; benched pending fresh-fold floor |
| 8 | A-H3 — exempt calendar-sparse legs from E1 | USDJPY | MEDIUM — sparsity ≠ dead signal: monthly/weekly clocks are sparse by design (A §7-H3) | realized entries n=13; paper book only for the rest (154 blocks) | **HIGH-RISK — the exemption list is exactly the exposed blocked set (S002/S003/S023/VC2-USDJPY), named after the folds were seen; benefit rests on the paper book (+428.7k) that ignores netting** | Realized ≪ paper is the docket's own expected failure mode; needs the successor engine's per-leg attribution before it is even testable |
| 9 | C-H-C1 — spread-cell reprice of the two near-miss H1 legs | USDCAD | MEDIUM-HIGH — 13.6% of Friday fills defer into the 4–6× wider C3 reopen cell (C §1.4) | TRAIN-only fold-7 diagnostics; zero scored folds | MEDIUM — legs (S011/S091) chosen from TRAIN outcomes (lawful discovery) but the claim is about cost infrastructure as much as the market; currently unrunnable | Plausible and precisely falsable, but gated on a panel/fill-law upgrade that does not exist (NOT_RUN) |
| 10 | C-H-C2 — swap drag dominates AUDUSD hold-heavy legs | AUDUSD | MEDIUM — swap events outnumber fills 353:1 on hold-heavy legs under the never-income DECLARED calendar (C §1.2, §1.4) | TRAIN-only; per-component cost dollars [NR] | MEDIUM — depends on an owner statement that has not landed; effect size unmeasurable today | Well-posed falsification but every input is DECLARED, not measured; parked |
| 11 | C-H-C3 — Friday-deferral asymmetry is AUDUSD-specific | AUDUSD | MEDIUM — 87/286 missing 20:00 bars vs 39/286 charges C3 2.8/6.3 vs C1 1.0/1.3 pips (C §1.4) | TRAIN-only; per-fill deferral flags [NR] | MEDIUM — mechanism is real but the test requires an amended fill law; no calendar | Same gate as H-C1; NOT_RUN |
| 12 | A-H5 — micro-flip churn is pure friction | USDJPY | MEDIUM — BE book is fee-dominated (friction/\|gross\| 1.42; 13/24 sub-friction gross) (A §5, §7-H5) | 24 BE trades + SL micros; floor ≥50 currently met | MEDIUM plus a **feasibility defect: the stated trigger (hold ≤ 2h) is exit-known, not decision-time observable — not implementable as an eligibility rule without reformulation** | Smallest predicted benefit (+2–4k/window) and the docket itself ranks it last; benched |

Honest flags, restated: **three of the twelve trigger shapes were visibly
tailored on the exposed folds** — B-H-E2 (hours scanned on scored journals),
A-H3 (exemption list = the exposed blocked legs), and A-H1 (cap multiple and
the 29-trade matched set identified post-hoc). A-H2's long-only restriction
and B-H-E3's pair choice are milder cases of the same exposure. None of
these disqualifies preregistration; all of them demand grid re-learning on
fresh TRAIN data (§4) and the anti-hypotheses in §2.

---

## 2. The slate — 6 rules (per-symbol specificity over generality)

Selection bias declared: ranks 1–6 of §1 enter; ranks 7–12 are benched with
reasons at the end of this section. Every rule is **eligibility semantics
only** (OFF entry / ON admission / retire) — no sizing laws are created or
modified. All journal field names refer to the successor engine's journal
(`journal_row@1` successor of PC12A's, which already carries the fields cited
by the dockets: `ts`, `direction_vote`, `cluster_id`, `leg_id`,
`onoff_features.decision_count_trailing`, `blocked_reason_detail`).

Summary:

| rule_id | symbol(s) | action class | leg scope | free thresholds |
|---|---|---|---|---|
| SU-RS-J1 | USDJPY | OFF entry (defer) | all 6 USDJPY legs (S002,S003,S014,S023,S026,VC2-JPY) | 1 (session bound) — gridded |
| SU-RS-J2 | USDJPY | retire leg | USDJPY-S014 (cluster meanrev_daily) | 0 |
| SU-RS-J3 | USDJPY | ON admission | USDJPY-S026 only | 1 (cap multiplier) — gridded |
| SU-RS-E1 | EURUSD | OFF entry (defer) | all 4 EURUSD legs (S009,S013,S046,VC2-EUR) | 1 (hour set) — gridded |
| SU-RS-E2 | EURUSD | keep floor (OFF gate) | SIG-exit-only class: EURUSD-S009 (+ any successor leg of that exit class) | 0 (constants inherited frozen) |
| SU-RS-G1 | GBPUSD | retire leg | GBPUSD-S017 | 0 |

### SU-RS-J1 — USDJPY NY-session long block

- **Source:** A §7-H2 / DP §11.3-1.
- **Trigger (decision-time, PIT-clean):** on any USDJPY decision row with a
  nonzero vote, if UTC hour of `ts` ∈ [16, 21) AND `direction_vote == +1` →
  eligibility OFF for that entry (defer; short entries untouched). Session
  marks derived from calendar, never hardcoded DST (CAM §1).
- **Overfit disclosure:** MEDIUM — bounds anchored to the London-close
  boundary; long-only split observed on exposed folds (§1 row 1).
- **Measured prior (exposed, journal units, both sides):** POLICY NY bucket
  −281,460.12 (n=91) / B1 −83,683.91 (n=74); blocking removes 50 losers
  (−795,805.74 avoided) against 38 winners (+514,369.07 suppressed); maxDD
  −412,208.31 → −359,621.76; fold counts 13/5/9/12/9/15/15/13 [path
  arithmetic on the realized exposed path, exits unchanged; an
  interventional re-run would produce different re-entry/netting/sizing
  paths — attribution only] (A §3, §6).
- **Anti-hypothesis (refutation on fresh folds):** REFUTED if (i) the
  blocked NY-long set nets ≥ 0 pooled over the fresh folds (suppressed-
  winner net ≥ avoided-loser net), or (ii) the rule's net effect is
  negative in ≥ 2 fresh folds (A §7-H2 failure condition, restated), or
  (iii) slate maxDD worsens in ≥ 3 of ≥ 6 fresh folds, or (iv) one
  suppressed winner exceeds 50% of the pooled avoided-loss total
  (concentration; mirrors PB2 §7 logic).
- **Floor:** ≥ 3 NY-long decisions per fresh fold and ≥ 20 per window
  (A §7-H2); floor failure → typed `NOT_RUN_THIN` for this rule, not a pass.

### SU-RS-J2 — USDJPY meanrev family retire (S014)

- **Source:** A §7-H4 / DP §11.3-6.
- **Trigger:** leg identity — `leg_id == "USDJPY-S014"` (equivalently
  `cluster_id == "meanrev_daily"` on USDJPY) → permanent eligibility OFF
  (retire at cycle registration).
- **Overfit disclosure:** MEDIUM-LOW — family chosen post-observation;
  mechanism structural.
- **Measured prior (exposed):** S014-triggered excursions −222,300.73
  (POLICY, n=24) / −319,603.73 (B1, n=29); RSI2_MID_CROSS family −470,441.67
  (n=33 pooled); meanrev cluster −541,904.46 (n=53) (A §2, §3).
- **Anti-hypothesis:** REFUTED if on fresh folds (i) the would-be S014 book
  nets > 0 pooled (missed-winners bar, §7 P-MW), or (ii) removal worsens
  slate maxDD by more than the PnL it saves — the netting-hedge channel the
  docket explicitly demands be checked (A §7-H4 failure condition), or
  (iii) the LORO contrast shows the retire contributes ≤ 0 net of suppressed
  winners.
- **Floor:** ≥ 3 would-be meanrev entries per fresh fold in the LORO arm
  (≥ 20 window) for the refutation test to be lawful (A §7-H4).

### SU-RS-J3 — USDJPY-S026 cost-guard cap relaxation (ON admission)

- **Source:** A §7-H1 / DP §11.3-5.
- **Trigger:** at a nonzero-vote decision on `leg_id == "USDJPY-S026"` where
  the L6 guard condition would fire (`guard.trailing_spend ≥ cap`, the exact
  condition recorded in `blocked_reason_detail` "L6 cost guard: trailing 28d
  spend X >= cap Y"; A §6, DP §2.3-a) → ADMIT the entry instead whenever
  `trailing_spend < m × cap`. Eligibility-only: admitted entries take the
  successor's standard vote size; no sizing law is added.
- **Overfit disclosure:** HIGH — n=29 matched defers, one trade 46% of the
  measured effect, cap multiple chosen post-hoc (§1 row 5). This rule is in
  the slate because the deferred set's B1-path attribution is the largest single attributed block of the
  USDJPY harm, and it carries the strictest grid + anti-hypothesis.
- **Measured prior (exposed, derived on B1's path):** 331 guard defers
  (S026 299); the 29 B1 filled netted +274,572.47 (16W/13L); removing them
  worsens B1 USDJPY maxDD −378,482.09 → −501,493.31 [leave-29-out on B1's realized path = attribution; not evidence that relaxing the guard causes these outcomes on any other path] (A §6).
- **Anti-hypothesis:** REFUTED if at the frozen multiplier (i) ≥ 20 admitted
  defers realize net ≤ 0 pooled (A §7-H1 failure condition), or (ii) any
  fresh fold's admitted-defer set nets below −(the pooled admitted gain)
  (single-fold wipeout), or (iii) the admitted set worsens slate maxDD vs
  the always-on control (false-admission bar, §7 P-FA).
- **Floor:** ≥ 20 admitted defers per window, ≥ 3 per fold (A §7-H1).

### SU-RS-E1 — EURUSD entry-hour gate

- **Source:** B §7-H-E2 / DP §11.3-4.
- **Trigger:** on any EURUSD decision row with a nonzero vote, if UTC hour
  of `ts` ∈ {12, 16} → eligibility OFF for that entry (defer). Default hour
  set {12,16}; grid in §4.
- **Overfit disclosure:** **HIGH-RISK — the hour set was selected from the
  entry-hour scan on the exposed scored journals (B §3)**; the rule is
  admissible only because the mechanism (handover spread widening + the
  S013 H4-clock votes at 12:00/16:00) is independently named and
  cost-visible (B §5), and because the grid is re-learned on fresh TRAIN
  (§4).
- **Measured prior (exposed):** suppressed book −495.9 (POLICY, 57 trades:
  17 winners −901.4 / 40 losers +1,397.3 avoided) and −1,037.1 (B1, 59);
  pair-book maxDD 878→387 / 2,277→977; 6/8 folds each (B §6 R-E2).
- **Anti-hypothesis:** REFUTED if on fresh folds (i) the suppressed-hour
  book nets > 0 pooled, or (ii) it nets > 0 in ≥ 3 fresh folds (B §7-H-E2
  failure condition), or (iii) the DD reduction fails to reproduce vs the
  always-on control.
- **Floor:** ≥ 40 suppressed trades per arm replication (B §7-H-E2).

### SU-RS-E2 — E1 activity floor, codified for SIG-exit-only legs

- **Source:** B §7-H-E1 / DP §11.3-2.
- **Trigger:** at any decision on a leg whose exit inventory is SIG-only
  (corpus identity field `exit_class == SIG_ONLY`; today: EURUSD-S009), if
  `onoff_features.decision_count_trailing` (26-week trailing window) < 3 →
  leg eligibility OFF for that decision. Constants 3/26w are INHERITED
  FROZEN from PC12A's E1 — no retuning is permitted (this rule codifies,
  it does not fit).
- **Overfit disclosure:** MEDIUM-LOW — constants predate scoring; the
  SIG-only scoping generalizes from one exposed leg (S009).
- **Measured prior (exposed):** S009 always-on −587.8 (50 trades, ≤0 in 5/7
  traded folds, worst f2 −496); the floor's missed set −504.0 over 49 trades
  (avoided loss ≈ $504 against +683.8 of cut c-winners) (B §2.1, §6 R-E1).
- **Anti-hypothesis:** REFUTED if on fresh folds (i) the floor-blocked
  SIG-only book would have netted > 0 pooled (B §7-H-E1 failure condition,
  restated in fresh-fold terms), or (ii) any single fresh fold's blocked
  book exceeds the fold-count-weighted equivalent of the docket's +$200
  tripwire, or (iii) the floor suppresses ≥ 30 trades whose pooled net is
  positive (missed-winners bar).
- **Floor:** ≥ 30 blocked-or-admitted decisions per evaluation window
  (B §7-H-E1).

### SU-RS-G1 — GBPUSD-S017 retire

- **Source:** B §7-H-G1 / DP §11.3-3.
- **Trigger:** leg identity — `leg_id == "GBPUSD-S017"` → permanent
  eligibility OFF (retire at cycle registration). No decision-time
  predicate, no threshold.
- **Overfit disclosure:** MEDIUM — retirement decided on the exposed TEST
  book (28–39 trades); stop-geometry mechanism structural.
- **Measured prior (exposed):** −47.6 (POLICY, 28) / −212.9 (B1, 39);
  exits 20 SL : 6 TP with 15/28 closing ≤ 1 minute; pair maxDD 676→502
  when suppressed (B §2.2, §4, §6 R-G1).
- **Anti-hypothesis:** REFUTED if a fresh-fold replication of the would-be
  S017 book shows (i) pooled net > 0, or (ii) TP share of exits ≥ 40%, or
  (iii) the overnight-carry subset providing the majority of gross
  (B §7-H-G1 failure conditions) — any one refutes.
- **Floor:** ≥ 50 would-be trades per arm book for the refutation test
  (current 28–39 is under-powered; B §7-H-G1).

### Benched (ranked 7–12), with standing re-entry conditions

- **B-H-E3 (admit VC2-EURUSD):** under-powered (n=26/13) + pair-cherry-pick
  risk. Re-entry: if at the first fresh-fold review the VC2-EUR blocked set
  meets the ≥ 50-trade floor with positive net, register as an amendment —
  never mid-cycle.
- **A-H3 (E1 sparse-leg exemption):** HIGH-RISK (leg list = exposed blocked
  set; paper-book dependence). Re-entry: only after the successor engine's
  per-leg attribution (A §9 unlock iii) exists on fresh folds.
- **A-H5 (micro-flip churn):** trigger not decision-time lawful as written;
  benefit negligible. Re-entry: only if TB-LABELS shows the friction-
  dominance population persists and a decision-time reformulation (re-entry
  cooldown at the vote quantum) is preregistered.
- **C-H-C1 / H-C2 / H-C3 (USDCAD/AUDUSD cost family):** no lawful calendar
  (§6); parked with their own named data unlocks (per-fill hour-stamped
  pricing; owner Activity/Flex swap statement; amended Friday fill law).

---

## 3. Controls (design; none executed)

Per-rule and slate-level controls, all preregistered here:

1. **C0 — always-on same-legs control (successor B1S).** The identical
   successor corpus with the eligibility layer pinned ON for every leg at
   every decision, everything else equal (PB2 §1 B1 semantics). Every rule
   contrast and every PASS bar is evaluated against C0.
2. **C1 — leave-one-rule-out (LORO).** Six re-runs, slate-minus-r vs C0 for
   each r ∈ {J1,J2,J3,E1,E2,G1}. Attribution by difference; also the
   anti-hypothesis vehicle for SU-RS-J2 and SU-RS-G1 (the retired/blocked
   would-be book is readable only in the LORO arm). Mirrors PB2 §8 P8 with
   rules replacing legs.
3. **C2 — random dwell-matched gating battery.** ≥ 100 seeds (≤ 128 seeded
   sub-runs), per-rule duty and flip rate matched to the slate's realized
   LEARN-window gating path; one identity, seeds on their own budget line
   (PB2 §4 / E-Law 8; PC12A precedent: 128/128 duty-matched random patterns
   beat the frozen policy objective — DP §2.3 — so this control is load-
   bearing, not decorative).
4. **C3 — clock-shadow.** Deterministic every-k-th-decision schedule per
   rule, duty-matched, phase 0 (PB2 §1 B5 semantics). Guards against
   cadence-as-value.
5. **C4 — cost stress.** ×1.5 governing (slate AND C0 both re-priced; PB2
   §6 P6a semantics), ×2.0 reporting-only (P6b), on ALL variable components
   (measured cells + DECLARED U2/U3/U4) per CAM §4 / FILL_ACCOUNTING_SPEC
   §5.
6. **C5 — missed-winners accounting (every OFF rule: J1, J2, E1, E2, G1).**
   Per fresh fold per rule, mandatory table: n suppressed; Σ suppressed-
   winner net (winners = net > +c_pair, c = per-pair median round-trip cost,
   the docket convention); Σ avoided-loser net; friction delta; largest
   single suppressed winner as a share of avoided-loss total. Reporting
   avoided losses without the winner side is an integrity trip
   (NOT_RUN_INTEGRITY), never a presentation choice.
7. **C6 — false-admission accounting (every ON rule: J3, and the mirror of
   E2).** Per fresh fold: n admitted-beyond-control; their pooled net;
   W/L split at c_pair; the worst single admitted loser vs the pooled
   admitted gain.
8. **C7 — inherited auxiliary baselines (available, recommended minimum:
   inverted).** Sign-inverted eligibility (PB2 B6) — for the two retire
   rules the complement is "S014/S017 always-on", the sharpest refutation
   probe; lagged eligibility (PB2 B7) optional. Both are one identity each
   if the owner enables them; the budget in §5 excludes them (headroom
   exists for both within the ≤ 24 identity cap).

---

## 4. Thresholds and grids

| rule | frozen default | preregistered grid (≤ 3 nodes) | notes |
|---|---|---|---|
| SU-RS-J1 | UTC hour ∈ [16,21), long-only | A `[16,21)` (default) · B `[15,21)` (NY-open wider) · C `[17,21)` (narrower) | nodes anchored to structural session boundaries, not to observed PnL |
| SU-RS-J3 | cap multiplier m = 1.5 | {1.5 · 2.0 · removed (∞)} | eligibility-only; the ∞ node also directly prices A-H1's remove branch |
| SU-RS-E1 | hour set {12, 16} | A `{16}` · B `{12,16}` (default) · C `{12..17}` (full NY-open block) | HIGH-RISK rule (§1 row 6): the default is the fold-shaped choice, disclosed as such; the grid exists so fresh TRAIN can overrule it |
| SU-RS-J2 / E2 / G1 | — | none | identity/class rules; E2 constants (3 / 26w) inherited frozen, retuning forbidden |

**Learning window law (frozen here).**

1. Grid nodes are learned ONLY on the earliest TRAIN data of the FRESH
   calendar. The designated learning window **LEARN** = the never-scored M1
   segment 2025-12-27 → 2026-09-23 (270 days = 38.6 weeks), which includes
   the 26-week sealed tail. Consuming the sealed tail as TRAIN requires an
   explicit owner declaration, and it then can NEVER count toward the ≥ 6
   validation folds (DP §5 calendar law).
2. Selection objective (frozen): maximize net-of-suppressed-winners
   improvement vs C0 on LEARN, subject to maxDD not worse on LEARN;
   tie-break: fewer deferred decisions (narrower gate), then lexicographic
   rule_id. Grid nodes evaluate as LEARN-side discovery rows only.
3. Freeze before fold-1 scoring; 1-week embargo between LEARN and fold 1;
   no contact with post-LEARN data during selection; the selected node is
   immutable thereafter.
4. Floor failure on LEARN (< 40 suppressed trades for SU-RS-E1; < 20
   admitted defers for SU-RS-J3; < 20 NY-long decisions for SU-RS-J1) →
   the grid collapses to the frozen default, recorded
   `NOT_RUN_GRID_THIN` — never silently widened.
5. Fallback if the owner declines to unseal the tail: defaults stand now;
   grids learn on the first 26 weeks of live accumulation instead (LEARN
   2026-09-24→2027-03-24, fold 1 starts 2027-03-31; full battery ≈ 2030-03
   under that variant, §6).

---

## 5. Trial budget draft

Counting unit follows PB2 E-Law 8 / CAM §6: baseline IDENTITIES on the
scored line; the random battery is ONE identity executed as ≤ 128 seeded
sub-runs on its own disclosed line; stress-tier and LORO re-runs are
identity-classified.

**Scored battery identities: 14 (cap ≤ 24).**

| identity | count | folds | rows |
|---|---|---|---|
| SLATE_FULL (6-rule policy) | 1 | 6 | 6 |
| C0 always-on same-legs | 1 | 6 | 6 |
| LORO slate-minus-r | 6 | 6 | 36 |
| C3 clock-shadow | 1 | 6 | 6 |
| C2 random battery (≥100 seeds) | 1 | 6 | 6 (+ ≤128 seed sub-runs, own line) |
| C4 ×1.5 slate / ×1.5 C0 (governing) | 2 | 6 | 12 |
| C4 ×2.0 slate / ×2.0 C0 (reporting) | 2 | 6 | 12 |
| **total** | **14** | | **84** |

- **Trial-ledger rows: 84 scored-side + 18 LEARN-side grid rows
  (3 gridded rules × 3 nodes × 2 LEARN sub-folds) = 102 total ≤ ~120.**
- Headroom within the ≤ 24 identity cap: 10 identities — enough for C7's
  inverted + lagged arms (2) and up to 8 contingency re-runs (e.g. a typed
  mid-cycle integrity twin) without amendment.
- Missed-winners / false-admission accounting (C5/C6) adds ZERO rows —
  computed from the same journals, analysis-side, mandatory disclosure.
- Inherited floors stay binding: campaign 20/3/100 per leg per fold (CAM
  §3) plus each rule's docket floor (§2). Floor failure is a typed
  `NOT_RUN_THIN`, never a relaxed retry.

---

## 6. Validation calendar feasibility per symbol

Arithmetic (venv python, 2026-10-01): 6 × 26w = 156 weeks = 1,092 days ≈
2.99 years. Never-scored M1 segment 2025-12-27→2026-09-23 = 270 days =
38.6w = 1.48 folds.

| symbol group | fresh data on file | accumulation path | earliest lawful ≥ 6×26w evaluation | status |
|---|---|---|---|---|
| EURUSD, GBPUSD, USDJPY (M1) | panels 2021-01-01→2026-09-23 (poolB audit; FX-RANGEFADE/fx-majors panels); scored folds end 2025-12-26 ⇒ never-scored segment 38.6w (incl. the 26w sealed tail) | live IBKR read-only streaming collector active (`DATA-FOUNDATION-SIXSOURCE-V1/ibkr_fx/sessions_index.jsonl`, sessions through 2026-09-28); M1 history via HMDS size-capped **NOT_RUN** (probe, DP §11.0) ⇒ forward accumulation only | **2028-12-23** if the full 38.6w segment is owner-credited toward folds 1–1.5; **2029-09-26** under §4's recommended design (38.6w consumed as LEARN; folds 2026-09-30→, fold 1 readable 2027-03-31); **2029-09-27** from today with zero credit | future accumulation only — **the dispatch's "mid-2027" is NOT attainable**: fresh stock at 2027-06-30 = 78.6w = 3.02 folds < 6 ⇒ `NOT_RUN_INSUFFICIENT_CALENDAR` (PB2 E-Law 5) |
| USDCAD, AUDUSD (H1) | H1 panels frozen 2021-01-03→2026-06-30, `read_only` (C §1.1, H1_PANELS.json) | **no H1 live collector on file** (the sixsource collector covers the 3 M1 majors); HMDS M1 history NOT_RUN_SIZE_CAP; H1 extension feasibility NOT_RUN | even if a lane opened today, 6×26w from zero ⇒ ≈ 2029-10 | **no lawful calendar exists — NOT_RUN**; re-attempt requires the changed mechanism axis / TERMINAL_DECISION Q-10 reopening + C §1.4 hypotheses |
| daily cohort (NZDUSD, USDCHF, XAUUSD, XAGUSD; energy signal side) | IBKR D1 BID/ASK 2020-10-02→2026-09-30 (≈ 1,553/1,544 days, DV-verified); FRED/ECB cross archives through 2026-09 (ECB served 2026-09-30; FRED FX series observed stale, ended 2026-09-25 at retrieval — UNLOCK D-1c); EIA dailies 2020-10-01→2026-09-29 span-complete (UNLOCK) | daily/weekly forward extension of the same free channels | **feasible TODAY as a calendar**: 312.7w span − 52w warmup = 260.7w ≈ 10.03 × 26w folds ≥ 6 | conditional on their gate + owner D-decisions (PIT thresholds unfrozen, lag not measured, costs pending statement, plan amendment — UNLOCK D-1); **hosts the 7 NEW-DAILY candidates (DP §6), NOT this slate's M1-pair rules** — opening it does not accelerate §2 |

Consequence, stated plainly: the §2 slate's own symbols cannot be lawfully
validated before **late 2028 at the absolute earliest** (2028-12 with maximal
owner credit; 2029-09 under the recommended LEARN design). The only calendar
that can open sooner is the daily cohort, which validates different
candidates. Everything in this file remains hypothesis-generating until one
of those calendars exists.

---

## 7. PASS bars for the successor

**Inheritance (wholesale).** PASS_BARS_V2 law carries over unchanged in
semantics: AND-only (net PnL strictly higher AND maxDD strictly lower vs the
named baseline, ties fail — PB2 §0 E-Law 4), pooled test folds, E-Laws 1–8
(quantities, fold-edge force-flat disclosure, comparability, strictness,
≥ 6-fold calendar floor, book-integrity precondition, ordering, budget
counting). Baseline mapping for the successor: B0 FLAT; **B1S = always-on
same-legs** (C0); B4S = random dwell-matched battery (C2); B5S = clock-shadow
(C3); stress ×1.5 governing with ×2.0 reporting and the ×2.0 sign-flip
`POLICY_COST_DOMINATED` disclosure trigger (PB2 §6); fold concentration ≤ 50%
PnL share / ≤ 2× pro-rata DD share (PB2 §7); **P8R = leave-one-RULE-out**
replacing leave-one-leg (exactly-one break → `POLICY_ONE_RULE_CARRIER`).
Successor engine prerequisites inherited as hard conditions: explicit
quote→USD conversion (A §0), MAE/MFE + per-leg exposure journaling (A §9,
B §9) — without them the missed-winners bar below is NOT_RUN.

**Addition 1 — P-MW, missed-winners bar (GOVERNING, per OFF rule: SU-RS-J1,
J2, E1, E2, G1).** A rule passes only if, pooled over the fresh folds:

```
Σ_f avoidedLoserNet_f(r)  >  Σ_f suppressedWinnerNet_f(r)          [strict]
AND  Δ(r) = netPnL(slate) − netPnL(slate ∖ r)  >  0                 [strict]
AND  maxDD(slate) < maxDD(slate ∖ r) is NOT required per rule,
     but a rule whose removal improves slate maxDD is reported as
     DD-inconsistent (refutes via the rule's own anti-hypothesis)
```

with the full per-fold two-sided table (C5) attached; **omission of the
suppressed-winner column → `NOT_RUN_INTEGRITY`** (STOP-3 class). A rule that
improves portfolio net only because OTHER rules carry it, while its own
suppressed winners outweigh its avoided losers, is refuted even if the
slate-level bars pass.

**Addition 2 — P-FA, false-admission bar (GOVERNING, per ON rule:
SU-RS-J3; mirror-applied to SU-RS-E2's kept-floor reading).** The
admitted-beyond-control set must satisfy, pooled over fresh folds:

```
netPnL(admitted set) > 0   AND   worst single admitted loser
                            <  pooled admitted gain
```

with per-fold disclosure (C6). Fail → the rule is refuted even if the slate
passes portfolio bars; single-trade concentration ≥ 50% of the admitted gain
carries a mandatory concentration disclosure (A §7-H1's 46% lesson).

**Slate-level acceptance (restated).** The successor claim passes only if on
the fresh calendar (≥ 6 × 26w folds, else `NOT_RUN_INSUFFICIENT_CALENDAR`):

1. netPnL(SLATE) > netPnL(B1S) AND maxDD(SLATE) < maxDD(B1S) — AND-semantics,
   vs always-on same-legs (the baseline that killed PC12A);
2. the same AND-pair holds at cost tier ×1.5 (governing) with ×2.0 disclosed;
3. SLATE beats the B4S battery per PB2 §4 clause semantics;
4. P7 fold-concentration holds;
5. P8R holds for all six rules;
6. **every rule individually passes P-MW or P-FA as applicable**;
7. every floor in §2/§5 met, else the affected contrast is `NOT_RUN_THIN`.

Nothing in this document is evidence toward any of these bars. All bars are
`NOT_RUN` until a lawful fresh calendar exists (§6).

---

## Traceability index (claim → source)

- USDJPY harm decomposition, NY bucket, guard defers, E-floor paper book,
  session tables, exit classes, cost anatomy, H1–H5: A §0–§9.
- EURGBP per-arm books, hour scan, R-E1/R-E2/R-E3/R-G1 rule tests, S017
  stop anatomy, H-E1/H-E2/H-E3/H-G1/H-G2: B §1–§9.
- H1-panel facts, COST_DOMINATED kills, C2/C3 cells, deferral rates,
  H-C1/H-C2/H-C3, 3-of-12 inference statement: C §1–Part 3.
- Pooled harm tables, seven-deaths ancestry, calendar-burned law, §11.3
  ranking, §12 successor sketch, B4 128/128 precedent: DP §2, §4, §5,
  §11, §12.
- AND-semantics, E-Laws, baseline realization laws, P1–P8, stress tiers,
  budget counting: PB2 §0–§9.
- Fold calendar, floors 20/3/100, cost tiers, multiple-testing ledger:
  CAM §3–§6.
- Daily-cohort spans, FRED/ECB/EIA coverage, staleness, owner gates:
  UNLOCK (branch `orca/pc12a-7asset-unblock-20261001`).
- Panel end dates and collector liveness: poolB `audit_summary.json`;
  `DATA-FOUNDATION-SIXSOURCE-V1/ibkr_fx/sessions_index.jsonl` (read-only).

— end of slate —
