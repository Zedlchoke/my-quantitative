# FINAL_RANKING — consolidated outcome-blind ranking, ALL families (SYNTH-VERIFY)

Task FUTURES-OVERNIGHT-PREP-20261003, lane SYNTH-VERIFY, 2026-10-04 UTC.
Rubric: **P1-CROSS `RANKING_FRAMEWORK.md` verbatim** (5 dimensions D1-D5,
integer 0-3, sum 0-15; tie-break total→D3 desc→D2 desc→D1 desc→D4 desc→id asc,
leg asc; registration status DISPLAYED, never an ordering key). This document
mechanically appends the two PENDING rows sets (P1-6J6A, P1-COMM) that
P1-CROSS could not read (lanes concurrent at its writing), using ONLY those
lanes' own returned artifacts (`hypo/6j_6a/RANKING_INPUT.md`,
`hypo/comm/RANKING_INPUT.md`, dossiers + sha256-pinned citations).

**Outcome-blind verified**: no return statistic, no PnL, no expectancy, no
hit-rate enters any cell (language scan of every batch-2 output: all
"measured cost"/"complete cost"/return-statistic occurrences are the
prohibitions themselves; 0 positive uses). Sibling rubrics (ESNQ sum 0-9,
6E6B/6J6A product 0-27, COMM sum 0-9) likewise contain no return statistic —
**no recompute required**. Scores describe PRE-REGISTRATION PACKAGE QUALITY
ONLY. Nothing here is schedulable, registered, or recommended.

## 1. PENDING rows filled under the program rubric (this lane's mechanical application)

6J6A (source facts: 6J6A RANKING_INPUT §Scores/§census + dossier anatomy):

| family | leg | D1 | D2 | D3 | D4 | D5 | total | mechanical basis |
|---|---|---|---|---|---|---|---|---|
| JF3 Tokyo-morning structure | 6J | 3 | 3 | 2 | 3 | 1 | **12** | on-symbol multi-era anatomy (18.1%/15.2% extrema, 59-vs-120 depth, era tables) ⇒ D1=3; home-session actors + DST falsifier + weekday negative ⇒ D2=3; court-MDE NOT_RUN, tail-only plausibility ⇒ D3=2; venue-clock strict-past, no external conditioner ⇒ D4=3; floor computed (RT 8.5-14.7bp), MDE NOT_RUN ⇒ D5=1 |
| AF3 bimodal US+Sydney structure | 6A | 3 | 3 | 2 | 3 | 1 | **12** | same profile as JF3 measured on 6A, all three eras (U-curve bimodal, 11:30-Syd modal 2.35%); D3=2 (per-minute scale 1.2-1.5bp vs RT 8.2bp — tail-only, MDE NOT_RUN); D4=3 in-repo; D5=1 |
| JF1 BoJ MPM decision-window | 6J | 3 | 2 | 2 | 2 | 2 | **11** | 54 measured MPM days ×1.87 |ret|/×1.27 vol multi-era ⇒ D1=3; window-convention anchor (minute stamps NOT evidenced), actors inferred ⇒ D2=2; MDE ≈13-19bp ≥ RT 8.5-14.7 ⇒ D3=2; decision dates FACT but intraday anchor is a convention ⇒ D4=2; r = RT/MDE ≈ 0.5-1.1 ⇒ D5=2 |
| JF2 MOF regime conditioning | 6J (overlay) | 2 | 3 | 1 | 2 | 1 | **9** | 386-op history + 4-of-14 leg anatomy measured but the conditioning claim (post-disclosure gradients) NOT_RUN ⇒ D1=2; named actor + lag law + shuffled-label placebo + null-era ⇒ D2=3; n=10 in-window ops + threshold constant owner-gated ⇒ D3=1; official disclosure dates PIT but owner-gated constant ⇒ D4=2; overlay host floor, MDE NOT_RUN ⇒ D5=1 |
| AF1 RBA decision-minute | 6A | 3 | 2 | 1 | 3 | 1 | **10** | ±5′ anatomy 9.0×/4.8× + change/hold 59/29 + calendar 1990→2026 ⇒ D1=3; change-vs-hold weak proxy, actors inferred ⇒ D2=2; K0 thin-n kill PRE-REGISTERED (n=67 fold floor fails; 4.35bp < one RT 8.2bp) ⇒ D3=1; 14:30 Sydney clock-known ⇒ D4=3; r ≈ 1.9 ⇒ D5=1 |
| AF2 RBA-vs-Fed differential overlay | 6A (overlay) | 2 | 3 | 1 | 1 | 1 | **8** | 16/16 material-roll sign law measured; gradients NOT_RUN + DFF vintage-fragile ⇒ D1=2; CIP + H-F/H-G law + block-shuffle placebo ⇒ D2=3; n≈16 power-starved ⇒ D3=1; DFF latest-vintage NOT PIT-strict ⇒ D4=1; overlay host floor ⇒ D5=1 |

COMM (source facts: COMM RANKING_INPUT §2/§3 + §0 measured archives;
D4 scored on PIT of conditioners — WNGSR/WPSR/CPC archives are as-published
vintage-grade; single-era/settlement-defect penalties live in D1):

| family | leg | D1 | D2 | D3 | D4 | D5 | total | mechanical basis |
|---|---|---|---|---|---|---|---|---|
| NG-F1 WNGSR-DESK | NG | 2 | 2 | 2 | 3 | 1 | **10** | release clock FACT + Thu-10:00 bucket 25.3% share = family-linked adjacent anatomy, single era, interaction NOT_RUN ⇒ D1=2; daily-only INFERENCE mapping ⇒ D2=2; kills + tiers + r-1 blocker pre-registered, no intraday delay axis (NOT_RUN_DATA_ABSENT) ⇒ D3=2; 1,205 as-published vintages PIT ⇒ D4=3; floor computed (tiers 22.46/32.46/42.46), MDE NOT_RUN ⇒ D5=1 |
| GC-F1 curve-compression | GC | 2 | 2 | 2 | 3 | 1 | **10** | curve anatomy IS the conditioning variable measured on-symbol (contango 99.8-100%, 7 gaps) but single era + settlement-derived defect ⇒ D1=2; competitor named, stage-gated directional kill deferred ⇒ D2=2/C3=2; in-repo strict-past ⇒ D4=3; D5=1 |
| SI-F1 beta-convexity | SI | 2 | 2 | 2 | 3 | 1 | **10** | corr 0.828 / elasticity ~1.9 / ratio 44→93 measured on-symbol, single regime ⇒ D1=2; convexity POSTULATED w/ vol-artifact NC ⇒ D2=2; single-regime auto-kill + 2-leg tiers ⇒ D3=2; in-repo ⇒ D4=3; D5=1 |
| SI-F2 curve-flip | SI | 2 | 2 | 2 | 3 | 1 | **10** | 6/6 gaps measured on-symbol; flip never observed in-window ⇒ D1=2; scarcity-vs-staleness competitors + thin-leg control ⇒ D2=2; retire-to-construction kill ⇒ D3=2; D4=3; D5=1 |
| CL-F1 WPSR-naive | CL | 1 | 2 | 2 | 3 | 1 | **9** | 790 feature vintages committed but no family-linked symbol stat (interaction NOT_RUN) ⇒ D1=1; naive-proxy blocker declared, INFERENCE ⇒ D2=2; double-proxy + Tuesday NC + tiers, no delay axis ⇒ D3=2; WPSR PIT + Wed-10:30 FACT ⇒ D4=3; D5=1 |
| CL-F2 conflict-reversal | CL | 1 | 2 | 2 | 3 | 1 | **9** | conflict inputs measured (Cushing 790/790) but conditional path NOT_RUN ⇒ D1=1; distinguishing observable named ⇒ D2=2; one frozen event set, adjudicated ⇒ D3=2; D4=3; D5=1 |
| NG-F2 CPC-revision | NG | 1 | 2 | 2 | 2 | 1 | **8** | feature archive multi-era but NOT symbol anatomy ⇒ D1=1; vintage clock named, INFERENCE ⇒ D2=2; seasonal placebo kill + error-leg NOT_RUN_DATA_ABSENT ⇒ D3=2; issuance time = file clock only (schedule NOT verified) ⇒ D4=2; D5=1 |

Not ranked (construction/execution class, per COMM RANKING_INPUT):
GC-F2 roll-migration (measured observable, 0 identities, feeds the cost
model — listed separately below), NG-F3 / SI-F3 / CL cost-law declarations.

## 2. CONSOLIDATED TABLE — all 31 ranked family-legs (mechanical order)

Ordering law applied across ALL rows: total desc → D3 desc → D2 desc →
D1 desc → D4 desc → id asc, leg asc. Flags: BLK = BLOCKED_TRIAL_BUDGET
(ES cap 24 frozen, headroom 0); CTG = contingent (no cap defined for that
symbol); HOLD = PB2 HOLD; PARK = PB3 PARK; GATE = owner-gated; OV = overlay
(0 standalone identities); NQV2 = NOT_QUALIFIED_V2 (no registration path).

| rank | family | leg | D1 | D2 | D3 | D4 | D5 | total | status |
|---|---|---|---|---|---|---|---|---|---|
| 1 | AF3 bimodal US+Sydney | 6A | 3 | 3 | 2 | 3 | 1 | **12** | **PARK** (PB3) |
| 2 | JF3 Tokyo-morning | 6J | 3 | 3 | 2 | 3 | 1 | **12** | CTG (6J secondary gates; no 6J cap) |
| 3 | FX-F2 Policy-Decision | 6B | 3 | 3 | 2 | 2 | 2 | **12** | CTG (no FX cap) |
| 4 | FX-F3 US-8:30 | 6B | 2 | 3 | 2 | 3 | 2 | **12** | CTG |
| 5 | FX-F3 US-8:30 | 6E | 2 | 3 | 2 | 3 | 2 | **12** | CTG |
| 6 | FX-F1 London-Range | 6E | 3 | 2 | 2 | 3 | 2 | **12** | **HOLD** (PB2) |
| 7 | FX-F2 Policy-Decision | 6E | 3 | 3 | 1 | 2 | 3 | **12** | CTG (court power finding 17.0bp) |
| 8 | ES-F1 FOMC-RES | ES | 3 | 3 | 2 | 2 | 1 | **11** | **BLK** |
| 9 | NQ-F1 FOMC-ERA | NQ | 3 | 3 | 2 | 2 | 1 | **11** | CTG + full-era rebuild |
| 10 | ES-F2 MACRO-0730 | ES | 2 | 3 | 2 | 3 | 1 | **11** | **BLK** |
| 11 | NQ-F2 MACRO-0730-NQ | NQ | 2 | 3 | 2 | 3 | 1 | **11** | CTG + rebuild |
| 12 | ES-F4 RUN-REV | ES | 3 | 2 | 2 | 3 | 1 | **11** | **BLK** |
| 13 | FX-F1 London-Range | 6B | 3 | 2 | 2 | 3 | 1 | **11** | **HOLD** |
| 14 | FX-F6 CoT-Conditioning | 6E | 3 | 2 | 2 | 3 | 1 | **11** | OV |
| 15 | JF1 BoJ MPM window | 6J | 3 | 2 | 2 | 2 | 2 | **11** | CTG (6J gates) |
| 16 | FX-F4 Reopen-Gap | 6E | 2 | 2 | 2 | 3 | 2 | **11** | CTG |
| 17 | ES-F3 COT-CROWD | ES | 2 | 2 | 2 | 3 | 1 | **10** | **BLK** |
| 18 | GC-F1 curve-compression | GC | 2 | 2 | 2 | 3 | 1 | **10** | NQV2 |
| 19 | NG-F1 WNGSR-DESK | NG | 2 | 2 | 2 | 3 | 1 | **10** | NQV2 (NOT_RUN_BLOCKED_R1) |
| 20 | NQ-F3 RUN-REV-NQ | NQ | 2 | 2 | 2 | 3 | 1 | **10** | CTG + rebuild |
| 21 | SI-F1 beta-convexity | SI | 2 | 2 | 2 | 3 | 1 | **10** | NQV2 |
| 22 | SI-F2 curve-flip | SI | 2 | 2 | 2 | 3 | 1 | **10** | NQV2 |
| 23 | AF1 RBA decision-minute | 6A | 3 | 2 | 1 | 3 | 1 | **10** | **PARK** (K0 pre-registered) |
| 24 | CL-F1 WPSR-naive | CL | 1 | 2 | 2 | 3 | 1 | **9** | NQV2 |
| 25 | CL-F2 conflict-reversal | CL | 1 | 2 | 2 | 3 | 1 | **9** | NQV2 |
| 26 | FX-F4 Reopen-Gap | 6B | 1 | 2 | 2 | 3 | 1 | **9** | CTG (anatomy gate) |
| 27 | NQ-F4 ROLLWK | NQ | 1 | 2 | 2 | 3 | 1 | **9** | CTG |
| 28 | JF2 MOF regime conditioning | 6J | 2 | 3 | 1 | 2 | 1 | **9** | OV/CTG (owner-gated constant) |
| 29 | NG-F2 CPC-revision | NG | 1 | 2 | 2 | 2 | 1 | **8** | NQV2 |
| 30 | AF2 differential overlay | 6A | 2 | 3 | 1 | 1 | 1 | **8** | OV/PARK |
| 31 | FX-F5 CIP-Regime | overlay | 2 | 3 | 1 | 1 | 1 | **8** | **GATE** (owner) |

Reference row (parent, NOT re-ranked): PB1 H-A/H-B ES = 12, registered,
A-r4 24 FROZEN. Construction-class: **GC-F2 roll-migration (GC)** — measured
observable, **0 identities by class**, feeds cost inputs; listed here, never
registered as alpha. Cross diagnostics X-1..X-5 rank separately as
falsifiers (X-5 11 · X-1 11 · X-2 11 · X-3 10 · X-4 9; 0 identities by
class; sequencing X-5 → X-1 → X-2 → X-3, X-4 harvest-only).

## 3. TOP-5 (families, mechanical)

1. **AF3 bimodal US+Sydney structure (6A) — 12/15 — PB3 PARK**
2. **JF3 Tokyo-morning structure (6J) — 12/15 — 6J secondary gates**
3. **FX-F2 Policy-Decision (6B) — 12/15 — CTG**
4. **FX-F3 US-8:30 Spillover (6B) — 12/15 — CTG**
5. **FX-F3 US-8:30 Spillover (6E) — 12/15 — CTG**

**Mandatory reading of the top-5**: the mechanical tie-break (D4 desc)
elevates the two 6J6A session-structure packages above the FX court
packages because their conditioning is fully in-repo strict-past (D4=3) —
**this is a package-quality ordering, not a schedulability claim**. Rank 1
sits on a PARK-gated symbol (reopen = owner decision, K0/AF1-style kills
would inherit); rank 2 sits behind three 6J gates (orientation proof, BBO
ruling, cost A7) and has NO cap. The highest rows whose gates are closable
by evidence work alone are the FX trio (ranks 3-5, all CTG; FX-F2-6B/6E
carry the court power finding 17-21bp verbatim in D3/D5). Every ES row is
BLOCKED_TRIAL_BUDGET (cap 24 frozen, headroom 0; minimal aggregate 36);
every NQ row is contingent-after-gates + full-era rebuild; every comm row
NOT_QUALIFIED_V2. This divergence from the sibling orderings (ESNQ ES-F1
9/9; 6J6A JF3 18/27 product) is the rubric split (power D3 vs floor D5,
PIT D4 added) working as designed — disclosed in RANKING_FRAMEWORK §3.

## 4. Standing rulings attached to every row

NO_GO_REGISTER · NO_GO_SCORE · NO_GO_ORDER; ES 24 identities frozen
(BLOCKED_TRIAL_BUDGET for all ES additions); NQ sibling-after-cost/clock-gate
+ full-era rebuild; PB2 HOLD (FX-F1 both legs); PB3 PARK (all 6A); COMM
no-registration-path (NOT_QUALIFIED_V2, owner data decision); 6F absent.
Fees: corrected + upheld, MODELED COST, UNDER REVIEW until a new A7.

— End of FINAL_RANKING.md. Mechanical, outcome-blind, artifacts-only; no
return statistic entered any cell; missing evidence scored NOT_RUN, never PASS.
