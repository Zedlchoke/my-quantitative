# SKEPTIC_failres_REPORT — economic-skeptic adjudication (Phase B, pre-PnL)

**Labels (every claim below): `DIAGNOSTIC_OUTCOME_EXPOSED` ·
`SINGLE_SOURCE_PANEL` · `PAPER_TIER` · `FAILURE_ROOT_CAUSE_RESEARCH` ·
`EVENTS_OVERLAY_ONLY — NOT_CAUSAL_EVIDENCE`.** Ancestor-law numbers carry
`R-ORIG-SEMANTICS`. Nothing here is promotable evidence; zero scored cells
(this lane has no scoring authority and none was requested).

Lane: `failres-skeptic` · branch `orca/erp1-ta1-failres-skeptic` @ base
`5b0b34b1a19204f96903ad50763ea71aa4322da9` · heavy lock `FREE_PROVEN`
before and after compute (light joins only). Proposer of H-FR1/2/3 = the
Lead (disclosed); this lane holds VETO authority only and does not propose.

---

## 0. Verdict summary

- **Overlay re-derivation (duty 1): PASS — every lead number reproduced
  exactly**, under an explicitly reconstructed join rule (§1). Two rule
  details were undisclosed in the lead's provenance and are now pinned;
  no numeric discrepancy exists.
- **H-FR1 MACRO-DIV-PERSIST: VETOED** — `VETOED_DEAD_CLASS_MACRO`
  (intraday form, class #7/#2) with the multi-day arm
  `BLOCKED_FINANCING_UNCOSTABLE` (FOREX-NG6/NG7).
- **H-FR2 SCHED-TAIL-AVOID: VETOED — `VETOED_VARIANT_SAME_FAMILY`.**
  This is the owner-ordered kill: "RANGEFADE + news filter" is rescue of
  the same family, and the filter is panel-net-NEGATIVE on the family's
  own book (§3).
- **H-FR3 BOUNDED-REVERSION: VETOED — `VETOED_VARIANT_SAME_FAMILY`**
  (time-box = re-gate after seeing the pool); maker restatement
  `VETOED_UNFUNDABLE_ARM`.
- **Enumeration duty: CLOSED — no mechanism class is opened by Phase A**
  that the 12-class table did not already close.
- **§7 ruling: NO** — Phase A is diagnostic knowledge about a dead
  family's internals, not a new information layer / payer / data
  authority. No cohort may be opened on it today.
- **Final verdict (umbrella §9): `NO_ELIGIBLE_PROPOSAL`** with the veto
  table in §6. The R-DAEMON shadow diagnosis stands as Phase-A fact only.

---

## 1. Duty 1 — independent overlay re-derivation: PASS

Own join code (`scripts/failres_skeptic_check.py`, written from the
schemas alone; the lead's script was not read). Inputs:
`failres_daily_EURUSD.json` (1,427 rows; 1,299 in F1..F6), daemon trades
filtered from `failres_attrib_trades_EURUSD.json` (1,062 RT),
`failres_events_timeline.jsonl` (131 events). Join on UTC date of
`event_time_utc`.

**Rule reconstruction (the load-bearing finding of this duty).** The
lead's provenance states only "inner join on UTC date; SCHED/SURPRISE
sets; OTHER_EVENT excluded from both". That rule alone does NOT
reproduce Table 1; two further details were needed, now pinned:

1. **Table 1 uses UNION buckets**: a day with both a SCHED and a
   SURPRISE event counts in BOTH categories (3 such days, all F2:
   2022-06-15 FOMC+NS1, 2022-07-21 ECB+NS1, 2022-07-27 FOMC+NS1 — so
   SCHED 27 + SURPRISE 8 + NO_EVENT 185 = 220 ≠ 218 traded days), and
2. **OTHER-only days are excluded from ALL Table-1 buckets** (5 traded
   days panel-wide: 2021-07-08 ECB strategy −7.5, 2022-07-14 parity
   break +34.8, 2023-03-10 SVB −22.2, 2024-08-05 yen-carry crash +9.4,
   2025-01-24 BoJ −34.8).

Under that rule every Table-1 cell matches the lead EXACTLY (F1
−1.4/22, +10.2/1, −190.1/191 · F2 −136.9/27, +43.6/8, −756.2/185 ·
F3 +143.5/17, −47.0/3, +975.5/196 · F5 −25.1/21, +21.9/2, −162.9/191 ·
F6 +92.5/13, −189.4/3, +353.9/201; F4 ALL=NO-EVENT by construction).

Tables 2–4 match EXACTLY under the natural PARTITION join
(sched-first, no exclusions): every exit-type × event cell (F2 SCHED FF
−346.2/19, SCHED TE +209.3/6, SURP FF −26.1/4, SURP TE 0/0, NON FF
−1,744.2/105, NON TE +1,022.8/32; likewise all of F1/F3/F5/F6),
mode-at-entry (F2 fade −476.5/138, follow −407.9/28), and the TARGET_EXIT
gross pools (F1 43/+745.6/−24.8 · F2 38/+1,258.5/−26.4 · F3 44/+1,692.0/
−33.7 · F4 37/+1,036.8/−19.8 · F5 24/+676.7/−13.3 · F6 24/+736.8/−19.5).

**One rule-sensitivity nuance (disclosed, not a discrepancy):** under a
strict partition (overlap days in SCHED only), F2's no-event share of the
loss is **81.6%** (−721.4 of −884.4), not the lead's 85.5%; the lead's
"≥85% in every losing fold" headline holds only under its own union
rule. Substantively identical conclusion either way: the F2 bleed is an
ordinary-day regime fact, and F2 SURPRISE days were net-positive (+43.6
union / −26.1 partition — tiny either way).

**Verification of the lead's qualitative claims:** all confirmed on my
independent numbers — FF<0/TE>0 in 12/12 pair-folds (and inside no-event
cells); F2 SCHED FF worst per-RT −18.2; 10/12 F2 worst days carry flips;
TE gross positive every fold. The overlay's facts survive; only its
interpretation authority ends here (below).

---

## 2. H-FR1 MACRO-DIV-PERSIST — VETOED

Claim (lead): Fed/ECB realized decision-path divergence (trailing
cumulative decision differential) makes band breaks PERSIST at
multi-day/week horizon; FF bleed concentrates in divergence-on months;
mechanically REQUIRES multi-day holds.

Four viability tests + six economic questions:

- **Dead-class law (test i): FAIL.** The intraday degenerate form is
  class #7 (event/macro observables incl. policy-rate — 15 dead entries)
  and, wherever the divergence signal becomes continuation-shaped, class
  #2. Direct ancestors: **FXFV5** (the sham-calendar control OUT-EARNED
  release-avoidance conditioning — scheduled/calendar conditioning has
  measured NEGATIVE information vs generic exposure on this very book),
  **FXFV3-A6** (realized-vol-gated policy-rate-differential carry: even
  the anchored form died `STRESS_TIER_FAIL` at ×2.0 with
  `PIT_UNEVIDENCED` data authority), **FXNG1-A4-P2** (the DGS10-level
  control out-earned the anchor — policy/nominal-level exposure in new
  words), **TRACKA2-P3B-DINV** (day-continuation re-clock,
  `ANCESTRY_RHO_BLOCK` 0.3032/0.3103 vs the immovable 0.20 bar). Under
  the owner law 2026-09-26, re-gating the dead fade family with a macro
  observable is not a new mechanism.
- **Measured cost floor (test ii): FAIL for the multi-day arm — moot
  by blockage.** No financing band is citable on vendor data
  (FOREX-NG6/NG7 F4): holds >1 day are UNCOSTABLE, fail-closed. The
  intraday form inherits the EURUSD book (0.6 base / 1.2 stressed /
  2.4 non-fragile line per RT): the claim's own persistence premium is
  unmeasured and the family it conditions earns +1.05 pips/RT gross.
- **Unfundable arm (test iii): FAIL.** "No new data needed" is FALSE on
  the committed artifacts: the timeline's FOMC series is missing
  **2021-12-15 and 2022-05-04** inside F2 alone (5 of 7 meetings), and
  decision direction/size exists only in free-text `expected_vs_actual`
  — a trailing divergence series requires new data assembly (owner
  gate; adjacent to 15 dead macro families per viability §B.3).
- **Exposure-map legality (test iv): FAIL for EURUSD lineage** (class
  #7 EURUSD-lineage exposure note) plus the new-download gate.
- **Six questions:** payer asserted (hedgers/importers + stopped-out
  LPs) but never evidenced on this space; premium unmeasured; the
  persistence claim is precisely what the fold data contradicts (F2
  monthly FF is negative in 8/10 months but POSITIVE in 2021-12 +22.1
  and 2022-02 +120.6, both deep inside the divergence window — the
  "divergence-on months" description covers nearly the whole window and
  does not isolate the bleed); risk arm (convergence/TPI repricing) is
  the FXFV3-A6 stress-fail shape; observable not constructible from
  committed artifacts (see test iii); falsifier is fine but is being run
  on a dead class, which the class law forbids entering.
- **Verdict: `VETOED_DEAD_CLASS_MACRO`; the multi-day arm
  `BLOCKED_FINANCING_UNCOSTABLE`** — reopening only via viability §C
  item 3 (citable financing band under owner authority) AND a
  mechanism-class court showing a NEW payer + new information layer.

---

## 3. H-FR2 SCHED-TAIL-AVOID — VETOED (owner's kill-on-sight case)

Claim (lead): stand the fade down on scheduled-macro days; F2 sched FF
−346.2 (−18.2/RT) avoided.

- **This is literally the "RANGEFADE + news filter" variant the owner
  ordered killed on sight.** Skeleton test: strip the filter and the
  decision law is byte-identical to the dead R-DAEMON/R-ANCHOR fade
  (same trigger, direction, exit, payer) → `VARIANT_SAME_FAMILY`
  (TRACKA2-C1C2C3; owner law: adding an observable is not a new
  mechanism).
- **FXFV5 counter-evidence binds:** the +7-day sham-calendar control
  OUT-EARNED release-avoidance conditioning; sham-calendar control is
  mandatory on any calendar mechanism and the prior on this filter is
  negative information.
- **Measured upside bound kills it on its own numbers:** standing down
  on sched days saves **−1.4 (F1) −136.9 (F2) −25.1 (F5) = +163.4
  pips** in the losing folds while REMOVING **+143.5 (F3) +92.5 (F6) =
  +236.0 pips** of winners — the filter is **panel-net −72.6 pips WORSE**
  on the family's own outcome-exposed book. F2 after the filter is still
  **−747.5** (its loss is 81.6–85.5% no-event days, gross-side). The
  −18.2/RT sched-FF cell is 19 trades selected AFTER seeing F2.
- **Outcome-exposed hindsight selection:** the filter is chosen from the
  same windows it would trade; the events lane's own non-causality law
  (§4 of EVENTS report) forbids reading the co-occurrence as conditionable.
- **Verdict: `VETOED_VARIANT_SAME_FAMILY`.** No reopening condition at
  any gate value; a news filter rejoins only with a NEW payer + NEW
  information layer (F-0 three tests), which no committed artifact
  supplies.

---

## 4. H-FR3 BOUNDED-REVERSION — VETOED

Claim (lead): TARGET_EXIT gross pool positive every fold (F2
+1,258.5/38); the identity dies only on the unbounded day-close hold; a
holding-time limit (or maker/post-only restatement) is "the same
economic mechanism, honest form".

- **Selection-after-seeing-the-pool (decisive):** `exit_type` is an
  EX-POST label of the family's own state machine, computed from the
  law's own trades on outcome-exposed windows. My hold-time
  descriptives show the pools are not ex-ante separable: TE p50 2–5
  bars vs FF p50 6–7, but FF p25 = 4 and TE p75 = 5 — heavy overlap. A
  time-box cannot know which FF trades would have hit target; its PnL is
  knowable only by re-running variants, which is the barred repair loop
  (kill-first discipline: no "improved version").
- **Dead-class law:** the time-box is a re-gate/re-session of the same
  trigger-direction-exit skeleton → TRACKA2-C1C2C3
  `VARIANT_SAME_FAMILY` + owner law 2026-09-26. The FF give-back is
  gross-side (F2 FF gross −2,027.6 → net −2,116.5; costexec §5: FF and
  TE pay the same ~0.65 pips/RT), so this is not a cost artifact a
  bound could harvest.
- **Unfundable arm (maker restatement):** Dukascopy M1 bid/ask carries
  zero queue/maker/depth bytes (class #10 UNCONSTRUCTIBLE);
  P3-A reopening arithmetic: ALL-IN ≥ taker crossing ≥ quoted spread
  (EURUSD conditional ~0.3–0.6 pips base); "assumed maker/mid
  numbers are NOT evidence" (TRACKA2-P3A). Any maker claim needs queue
  evidence that cannot exist on this data layer.
- **Verdict: `VETOED_VARIANT_SAME_FAMILY`** (time-box);
  **`VETOED_UNFUNDABLE_ARM`** (maker form; reopening only via the P3-A/
  §C-1 broker-cost-authority condition, which would still leave the
  class veto to pass).

---

## 5. Duty 3 — independent enumeration: CLOSED (nothing opens)

Checked whether ANY mechanism class is opened by the Phase-A facts
beyond the 12-class table:

- **(a) TE-positive / FF-negative in 12/12 cells — NEW observable?**
  NO: it is a decomposition of the SAME family's own outcome —
  `exit_type` is the family's own exit state (target-hit vs day-close)
  labeled ex post on outcome-exposed windows; not PIT-implementable, not
  an information layer. **CLOSED.**
- **(b) F2 no-event-day persistence — tradable information layer on the
  authorized space?** NO: candidate conditioners are (i) flip/non-flip
  day state = the family's own partial-range mode machinery (class #1
  "+ANY gate", dead); (ii) ex-ante prior-day-range percentile = the
  R-ANCHOR input, measured NON-stable (terciles reorder across folds;
  class #9, Q-7 dead); (iii) hour/session geometry (class #5 dead; and
  London/NY losses are ∝ RT counts); (iv) anything else needs new
  downloads (owner gate, adjacent to 15 dead macro families). The
  ordinary-day bleed is the dead family's own fade behavior in a
  trending regime — diagnosis, not a layer. **CLOSED.**
- **(c) Any pair/surface where the cost floor changes the answer?** NO:
  EURUSD is the program's cheapest book (1.2 stressed RT / 2.4 line vs
  3.6/4.4 floors and ~7–9 lines), but every Phase-A losing fold is
  GROSS-negative (F2 cost share 13%), so a cheaper floor cannot flip
  any sign; the only pool above the line (TE +28.2 pips/RT gross) is
  the ex-post-selected pool of (a); GBPUSD sits at floor level and is
  more underwater (aggregate gross ≈ 0). **CLOSED.**
- **(d) Residual seams checked:** the 00:00–06:00 gap-fill trades (15
  EURUSD, net −4.5) are a data-seam disclosure with no payer — not a
  mechanism class; 2026 out-of-fold daemon +421.8 is outcome-exposed
  same-family material, not evidence; REVERSAL cells are empty (0/2,125
  daemon RTs), closing any "flip-capture" class variant. **CLOSED.**

Net: the three lead drafts already map onto classes #1+#7 (H-FR2),
#7+#8/#2 (H-FR1), #1+#10 (H-FR3). Zero unclaimed classes remain.

---

## 6. Duty 4 — §7 ruling: NO

Phase A does **not** constitute "genuinely new evidenced information"
(master plan §7 / viability §C) sufficient to open a cohort today. What
Phase A established is **diagnostic knowledge about a dead family's own
internals** (why R-DAEMON loses: gross-side directional bleed, mid-day
mode re-ranking, and the day-close continuation tail, on
outcome-exposed windows). The precise gap: it supplies

1. **no new information layer** — every candidate conditioner is the
   family's own state variable or a dead class (§5b);
2. **no new payer** — no §5.3 field-1 payer was evidenced beyond those
   already adjudicated in the 12-class table; and
3. **no new data/cost authority** — Dukascopy M1-only stands; financing
   band, broker cost authority, and independent source all remain
   owner-blocked (viability §C items 1–3 unmet).

Viability §C(a) stays MET (0/12 classes pass D2); §C(c) stays NOT-met
(2026-H1 AUDUSD/USDCAD remain SEALED-UNREAD — untouched here). Phase A
is exactly the class of output that must NOT self-authorize a cohort:
a post-mortem, not a frontier.

---

## 7. Duty 5 — final verdict for the owner packet

**`NO_ELIGIBLE_PROPOSAL`** (umbrella §9 vocabulary). Zero scored cells.

### Veto table

| Hypothesis | Verdict | Veto class | Decisive evidence lines |
|---|---|---|---|
| H-FR1 MACRO-DIV-PERSIST | VETOED | `VETOED_DEAD_CLASS_MACRO` (+ multi-day arm `BLOCKED_FINANCING_UNCOSTABLE`) | FXFV5 sham out-earned; FXFV3-A6 STRESS_TIER_FAIL+PIT_UNEVIDENCED; DINV rho 0.303/0.310; FOREX-NG6/NG7 no financing band; F2 FOMC series missing 2021-12-15 & 2022-05-04 (observable not constructible from committed data); FF bleed NOT month-isolated (+2021-12, +2022-02 inside divergence window) |
| H-FR2 SCHED-TAIL-AVOID | VETOED | `VARIANT_SAME_FAMILY` (news-filter rescue — owner kill-on-sight satisfied) | Skeleton test degenerates to dead fade; FXFV5 control-outearned precedent; filter saves +163.4 in losing folds but removes +236.0 in F3/F6 = panel −72.6; F2 stays −747.5; hindsight-selected −18.2/RT cell (19 RT) |
| H-FR3 BOUNDED-REVERSION | VETOED | `VARIANT_SAME_FAMILY` (time-box) + `UNFUNDABLE_ARM` (maker) | exit_type is ex-post (selection-after-seeing-pool); hold-time overlap FF p25=4 vs TE p75=5; C1C2C3 + owner law; FF give-back is gross-side (−2,027.6 F2); maker bytes = 0; P3-A ALL-IN ≥ 0.3–0.6 pip crossing |

**Standing advice to the owner:** file Phase A as the failure-memory
post-mortem of R-DAEMON (KILL-family diagnostic); do not let its most
consistent internal fact (TE+/FF− 12/12) be read as a strategy seed —
it is the family's own outcome decomposition. Reopening the program
runs exclusively through viability §C items 1–3 (broker cost authority,
EDQ1 source decision, citable financing band), each an owner gate, and
any post-gate proposal still faces the F-0 mechanism-class court before
rho/PnL.

---

## 8. Limitations and incidents

Limitations: all surfaces DIAGNOSTIC_OUTCOME_EXPOSED (never promotable);
SINGLE_SOURCE_PANEL; PAPER_TIER costs (FILL_QUALITY_UNMEASURABLE_ON_M1_
BIDASK); the overlay is correlation arithmetic — non-causal by the
events lane's binding law; R-ORIG-semantics numbers inside the inputs
carry R-ORIG-SEMANTICS; this lane scored nothing and proposed nothing.
The lead-rule reconstruction (union buckets + OTHER-day exclusion) is
inferred from numbers, not from the lead's code (script unread) — it is
recorded so future joins use an explicit rule.

Incidents: none. No foreign artifact touched; no shadow, journal,
dashboard, ledger, or registry contact; sealed holdouts never opened;
locks FREE_PROVEN before and after the single light-compute run.
