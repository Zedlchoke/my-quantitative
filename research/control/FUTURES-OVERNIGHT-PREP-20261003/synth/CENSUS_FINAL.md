# CENSUS_FINAL — trial-family census, all lanes filled (SYNTH-VERIFY)

Task FUTURES-OVERNIGHT-PREP-20261003, lane SYNTH-VERIFY, 2026-10-04 UTC.
This fills the P1-CROSS `CENSUS_PROPOSAL.md` §4 skeleton (PENDING rows) from
the returning lanes' own census sections. **Denominator planning only: NO
registration proposal, NO GO, NO family selection.** Census unit = one scored
trial identity (family × leg × arm × tail × delay × tier) with its own PnL
path; controls counted where the row's convention says so. Mixed conventions
are NOT summed (§4 hygiene rule 1).

## 1. The completed census table

| family | lane | legs | type | full-grid IDs | minimal-core | controls counted | minimal total | 0-cost legs | cap status / headroom | gates before any scoring | source |
|---|---|---|---|---|---|---|---|---|---|---|---|
| PB1 OVN pair (H-A/H-B) | parent | ES | T2 | 24 (+28 FOMCIN full) | A-r4 = 24 | yes (4) | **24 (FROZEN)** | K1-K5 era views; C5 convention | **FROZEN 24; headroom 0**; NO_GO stands | fees-account D2, calendar D3, A7 review, spec freeze | PLAYBOOKS §1 |
| ES-F1 FOMC-RES | ESNQ | ES | T1 | 24 | 8 (S2) | yes (3) | **11** | F1-K6 anatomy gate | **BLOCKED_TRIAL_BUDGET** (36>24) | F1-K6; owner amendment for any cell | ESNQ RI §3 |
| ES-F2 MACRO-0730 | ESNQ | ES | T1 | 48 (CPI+NFP) | 8 (CPI,S2) | yes (3) | **11** | F2-K6; canceled-day subset | BLOCKED_TRIAL_BUDGET | F2-K6 per-era anatomy | ESNQ RI §3 |
| ES-F3 COT-CROWD | ESNQ | ES | T1+T3 gated | 4 (stage-1 vol = 0) | 4 | yes (3) | **7** | stage-1 vol leg (0 IDs) | BLOCKED_TRIAL_BUDGET | F3-K1 session-granularity gate | ESNQ RI §3 |
| ES-F4 RUN-REV | ESNQ | ES | T4 | 8 (k∈{3,5}) | 4 (k=5,S2) | yes (3) | **7** | F4-K6 placement gate | BLOCKED_TRIAL_BUDGET | F4-K6 intraday placement | ESNQ RI §3 |
| **ES aggregate** | | | | | | | **36 minimal** | | **all BLOCKED; headroom 0** | | ESNQ RI §3 |
| NQ-F1 FOMC-ERA | ESNQ | NQ | T1 | 24 | 8 | yes (3) | **11** | NQ-F1-K6 | no NQ cap — CTG | cost A7, calendar 2026, full-era rebuild | ESNQ RI §3 |
| NQ-F2 MACRO-0730-NQ | ESNQ | NQ | T1 | 48 | 8 | yes (3) | **11** | K6 era gate | CTG | anatomy gate (2023-26 only) | ESNQ RI §3 |
| NQ-F3 RUN-REV-NQ | ESNQ | NQ | T4 | 8 | 4 | yes (3) | **7** | rebuild = K6 | CTG | **full-era rebuild (hard precondition)** | ESNQ RI §3 |
| NQ-F4 ROLLWK | ESNQ | NQ | T5 | 4 (Role-B) | 4 | yes (3) | **7** | Role A audit (standing, 0) | CTG | K6 interaction; Role A law | ESNQ RI §3 |
| FX-F1 London-Range | 6E6B | 6E,6B | T2 | 36/leg | census-gated | **no (0)** | (contingency) | court census ≥500 triggers | **PB2 HOLD** | court census + power floor + ancestry | FX §8 |
| FX-F2 Policy-Decision | 6E6B | 6E,6B | T1 | 36/leg (+36/stratum) | n/a | no (0) | (contingency) | strata descriptive | no FX cap — CTG | power honesty (MDE 17-21bp) | FX §8 |
| FX-F3 US-8:30 | 6E6B | 6E,6B | T1 | 36/leg (+36/stratum) | n/a | no (0) | (contingency) | unclassified-8:30 stratum | no FX cap — CTG | vintage law; latency NOT_RUN | FX §8 |
| FX-F4 Reopen-Gap | 6E6B | 6E,6B | T2 | 36/leg (+36 Sunday) | n/a | no (0) | (contingency) | 6B gap-std gate | no FX cap — CTG | 6B anatomy-first | FX §8 |
| FX-F5 CIP overlay | 6E6B | overlay | T3 | 0 standalone; host×2 | 0 | host's | 0 | 0 standalone | **owner-gated** | vintage decision | FX §8 |
| FX-F6 CoT overlay | 6E6B | 6E | T3 | 0 standalone; host×2 | 0 | host's | 0 | 0 standalone | no cap — CTG | intraday transfer NOT_RUN | FX §8 |
| **FX aggregate if ALL ran** | | | | **≈648** | | | | | **no ceiling applied anywhere** | | FX §8 |
| **JF1 BoJ MPM window** | 6J6A | 6J | T1 | 24 | 8 | yes (3) | **11** | — | no 6J cap — CTG (secondary gates) | orientation proof, BBO ruling, cost A7 | 6J6A RI census |
| **JF1 regime subset** | 6J6A | 6J | descriptive | 0 | 0 | 0 | **0** | fold floor fails (4+2 titled) | n/a | n/a | 6J6A RI census |
| **JF2 MOF regime conditioning** | 6J6A | 6J | T3 overlay | 4/host (8 both) | 4 | yes (3, shuffled-label) | **7/host** | regime-shuffle = view | no 6J cap — CTG | threshold constant owner-gated | 6J6A RI census |
| **JF3 Tokyo-morning** | 6J6A | 6J | T2 | 24 | 8 | yes (3) | **11** | — | no 6J cap — CTG | 6J gates | 6J6A RI census |
| **AF1 RBA decision-minute** | 6J6A | 6A | T1 | 24 | 8 | yes (3) | **11** | — | **PB3 PARK — contingency only** | K0 thin-n kill PRE-REGISTERED; k=5 roll + tick adjudication | 6J6A RI census |
| **AF2 differential overlay** | 6J6A | 6A | T3 | 0 (views) | 0 | 0 | **0** | 0 standalone | PB3 PARK | DFF vintage test | 6J6A RI census |
| **AF3 bimodal structure** | 6J6A | 6A | T2 | 24 | 8 | yes (3) | **11** | — | PB3 PARK — contingency only | 6A prerequisites | 6J6A RI census |
| **6J minimal aggregate (if packet ever drafted)** | | | | 96 full (24×4) | | | **≈29-36** (JF3 11 + JF2 7/host + JF1 11) | | **no 6J cap defined; explicit owner ceiling required first** | | 6J6A RI §standing |
| **NG-F1 WNGSR-DESK** | COMM | NG | T1 | 24 | 8 | yes (3) | **11** | r-1 draft + survey verify | no path (NQV2) | r-1 rule freeze + price depth | COMM RI §3 |
| **NG-F2 CPC-REVISION** | COMM | NG | T1 | 24 | 8 | yes (3) | **11** | degree-day rule derivation | no path (NQV2) | aggregation rule + depth | COMM RI §3 |
| **CL-F1 WPSR-NAIVE** | COMM | CL | T1 | 24 | 8 | yes (3) | **11** | naive-freeze drafts | no path (NQV2) | naive-proxy freeze + depth | COMM RI §3 |
| **CL-F2 CONFLICT-REV** | COMM | CL | T1 (joint w/CL-F1) | 24 (shared grid, split arms) | 8 | yes (3) | **11 (joint)** | — | no path (NQV2) | same | COMM RI §3 |
| **GC-F1 CURVE-COMPRESS** | COMM | GC | T1 (daily) | 12 | 4 | yes (3) | **7** | stage-1 panel | no path (NQV2) | serial re-fetch + power ≥2y | COMM RI §3 |
| **GC-F2 ROLL-MIGRATION** | COMM | GC | **construction (T5-class)** | **0** | 0 | 0 (placebo = view) | **0** | roll-cost table | never scored as alpha | produces cost inputs | COMM RI §3 |
| **SI-F1 BETA-CONVEX** | COMM | SI | T1 (daily) | 12 | 4 | yes (3) | **7** | stage-1 panel | no path (NQV2) | 2-leg depth ≥2y + regime split | COMM RI §3 |
| **SI-F2 CURVE-FLIP** | COMM | SI | T1 (daily) | 12 | 4 | yes (3) | **7** | gap-vs-floor panel | no path (NQV2) | flip observation + depth | COMM RI §3 |
| **COMM aggregate if ever legalized** | | | | 132 full (24×4 + 12×3) | | | **54 minimal > 24 ⇒ BLOCKED_TRIAL_BUDGET on any single-cycle attempt** | | **no registration path until owner data decision** | | COMM RI §3 |
| X-1..X-5 cross diagnostics | CROSS | multi | T6 | **0 by class** | 0 | own permutations | **0** | ALL steps 0-cost | never scored | per-design prereqs | CROSS |
| 6F | — | — | — | — | — | — | **0 (NOT_RUN_DATA_ABSENT)** | — | no data owned | — | standing ruling |

## 2. Totals per family-type (identity arithmetic, all lanes)

| type | families (legs) | full-grid sum | minimal-core sum | notes |
|---|---|---|---|---|
| T1 event-anchored daytrade | ES-F1/F2, NQ-F1/F2, FX-F2/F3 (4 legs), JF1, AF1, NG-F1/F2, CL-F1/F2 | 24+48+24+48+36×4+24+24+24+24+24+24(shared) = **328** | 8+8+8+8 + (FX: census-gated, 0) + 8+8+8+8+8+8 = **72** (FX legs uncounted by convention c) | ESNQ/6J6A/COMM count controls in minimal; FX does not |
| T2 session-transition | PB1 (frozen), FX-F1 (2 legs), FX-F4 (2 legs), JF3, AF3 | 24(PB1) + 36×4 + 24×2 = **212** | PB1 24 (frozen) + FX census-gated + 8+8 = **40** | |
| T3 conditioning overlay | FX-F5, FX-F6, JF2, AF2 (+ES-F3 directional = T1-gated) | 0 standalone (host×2 each) | **0 standalone** | H-G law: overlays never standalone |
| T4 multi-day horizon | ES-F4, NQ-F3 | 8+8 = **16** | 4+4 = **8** | |
| T5 construction/roll | NQ-F4 (Role B), GC-F2 | 4 + 0 = **4** | 4 | Role A = standing law, 0 IDs |
| T6 cross diagnostic | X-1..X-5 | **0** | 0 | consistency statistics + control legs only |
| **Program hypothetical (INFERENCE, not a proposal)** | all lanes | ESNQ 168 + FX ≈648 + 6J6A 96+8 + COMM 132 + PB1 24 = **≈1,068** | ESNQ 36 + 6J6A ≈29-36 + COMM 54 + PB1 24 (FX uncountable under convention c) | mixed conventions — normalize before any program-wide denominator is quoted |

## 3. The ES cap conflict (the round's headline denominator fact)

| item | count | evidence |
|---|---|---|
| ES frozen cap (A-r4, Co-Owner r5) | **24** (primary 16 + FOMC 4 + C1-C4 4) | PLAYBOOKS §1; SPEC_PB1_ES r3 untouched |
| ESNQ minimal aggregate demand (F1 11 + F2 11 + F3 7 + F4 7) | **36** | ESNQ RI §3 |
| Headroom for new ES identities | **0** | OBSERVED |
| Consequence | every ES family **BLOCKED_TRIAL_BUDGET**; executable at 0 identities: ES-F3 stage-1 vol leg + F1/F2/F4 anatomy pre-gates | ESNQ RI; census hygiene rule 3 (full-rigor vs capped-scope pairs: D1=52/D2=53/A-r4=24 precedent) |

## 4. No-cap statements (stated plainly, unchanged)

- **NQ**: no cap defined; census (minimal 36, full 168 ESNQ-wide) is
  contingency only behind cost/clock gates + full-era rebuild.
- **FX (6E/6B)**: no cap defined anywhere; all-in census ≈648 has NO ceiling
  applied; FX census counts 0 scored controls (convention c).
- **6J**: no cap defined (NOT_RUN ceiling arithmetic); minimal ≈29-36 is the
  input to a future owner ceiling; 6J secondary gates close first.
- **6A**: PB3 PARK — census contingency only; K0 thin-n kill inherited.
- **COMM**: no registration path (NOT_QUALIFIED_V2); aggregate 54 > 24 would
  be BLOCKED_TRIAL_BUDGET on any single-cycle attempt.
- **6F**: NOT_RUN_DATA_ABSENT — no census exists.

## 5. Placebo-budget question — carried to the owner, ruling slot EMPTY

Three inconsistent control-counting conventions hold simultaneously
[OBSERVED]: (a) PLAYBOOKS law (C1/C2/C4 = scored identities), (b) ESNQ/6J6A/
COMM censuses (minimal totals include 3 scored controls), (c) FX census
(controls not counted; PB2 court §c4 demands ≥100-seed bands, Co-Owner
ruling pending). Arithmetic forcing the decision [INFERENCE, from CENSUS_PROPOSAL
§3]: multi-seed-as-identities ⇒ ≥1,800 placebo identities for the 18 returned
legs alone; multi-seed-as-diagnostics ⇒ program-wide "single-seed, no
permutation-robustness claim" publication law until funded. Court power
findings bound the question: at n≈300-900 the court detects only ≈4-9bp —
power floor and cost floor coincide; census-gate-before-scored-cell is the
strongest denominator-level argument the program has measured. **No side
taken; owner slot empty.**

— End of CENSUS_FINAL.md. Denominator planning only; nothing registered,
scheduled, or recommended; every number traces to a lane artifact or is
labeled INFERENCE.
