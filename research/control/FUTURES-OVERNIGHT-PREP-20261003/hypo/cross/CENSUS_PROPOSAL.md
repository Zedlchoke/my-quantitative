# CENSUS_PROPOSAL — trial-family census framework (P1-CROSS)

- Task: **FUTURES-OVERNIGHT-PREP-20261003**, lane **P1-CROSS**. Generated UTC
  2026-10-04. Worktree @ `72c9bc5b1d94b812044a9bd21768c53b4d378436`
  (re-measured; no tracked drift), branch `prep/futures-behavior-10syms-20261002`.
- Class: **denominator planning only. NO registration proposals, NO GO
  recommendations, NO family selection.** Nothing in this document schedules
  any run; it counts what WOULD be counted, exposes the arithmetic, and
  leaves every cap and freeze decision to the owner and the owning cycle.
- Sources: PLAYBOOKS_DRAFT r5 §1/§4 (A-r4 = 24; D1 = 52 / D2 = 53 lesson),
  PB2 court §c2-§c4 + §d (census gate, MDE/power, placebo-budget ruling
  pending), sibling censuses `hypo/es_nq/RANKING_INPUT.md` §3 and
  `hypo/6e_6b/FX_HYPOTHESES.md` §8, DATACONTRACT §1.3, FEES_CORRECTED.
  All sha256 in `cross_hypotheses.json`.
- Labels: OBSERVED (committed arithmetic/verdicts) / INFERENCE (this lane's
  arithmetic over committed inputs, flagged) / NOT_RUN. Missing evidence is
  never PASS.

---

## 1. Family types and their identity-count arithmetic

Census unit = **one trial identity** = one scored cell with its own PnL path
(family, symbol leg, arm, tail, delay, cost tier). Convention follows
PLAYBOOKS §4.2: every scored result — controls included — enters the
observed denominator; hiding or silently cutting cells is forbidden
(BLOCKED_TRIAL_BUDGET label instead).

| type | definition (committed examples) | identity grid | full-grid IDs | typical minimal-core | scored controls |
|---|---|---|---|---|---|
| **T1** event-anchored daytrade | ES-F1/F2, NQ-F1/F2, FX-F2, FX-F3; PB3-6A ancestry; 6J MPM themes (PENDING) | arms(2) × tails(2) × delays × tiers(3); delays = 2 (D0/D30, ESNQ) or 3 ({0,+1bar,+30m}, FX) | 24 (ESNQ) / 36 (FX) per symbol leg | S2-only slice = 8; era-gated families narrower | C1 clock placebo + C2 always-in + family-specific NC (ESNQ: 3; FX convention: uncounted, §3) |
| **T2** session-transition daytrade | PB1 OVN pair (registered, A-r4 = 24 incl. FOMCIN 4 + controls 4); FX-F1 (HOLD); FX-F4 | as T1; FX delay triple | 24-36 per leg | PB1 A-r4 primary 16; FX-F1/F4 = 8 | as T1; PB1 additionally C3 flat (1) + C4 dose (1) |
| **T3** conditioning overlay | FX-F5 (CIP regimes), FX-F6 (CoT strata); ES-F3 directional leg is T1-with-gate, vol leg = 0 | **0 standalone** (H-G law); ×2 regime strata on ONE chosen host leg | host ×2 | host ×2 | host's controls re-run within strata (placebo bands per stratum) |
| **T4** multi-day horizon | ES-F4, NQ-F3 | arms(2) × tails(2) × 1 delay × tiers(1, S2) ; k=3 sensitivity = view, not identities without budget | 8 (k∈{3,5} ⇒ 8 counted at k=5 only... see sibling rows: 8 with k pair, minimal 4) | 4 | C1, C2, NC (3) |
| **T5** construction/roll | NQ-F4 | Role A chain audit = **standing law, 0 identities** (kills any NQ run on failure); Role B gated differential 2×2×1×1 = 4 | 4 | 4 | C1, C2, NC-8 (3) |
| **T6** cross-symbol diagnostic | X-1..X-5 (this lane) | **0 by class law** — consistency statistics on committed series / mandatory control legs; no PnL path exists | 0 | 0 | own pre-declared placebos are permutations, not identities |

Standing type rules [OBSERVED, from PLAYBOOKS §1 census + K1/NEW-1
precedent]: descriptive legs (anatomy pre-gates, stage-1 vol legs, era/K
views, census passes, C5-style non-PnL conventions, cross diagnostics) cost
**0 identities** — they are evaluation views on existing paths or prep-legal
measurements. A scored variant of anything descriptive is a NEW registration
needing its own budget line.

---

## 2. Standing caps — the complete list, stated plainly

1. **ES: 24 scored identities, FROZEN** (Co-Owner r5 decision, PLAYBOOKS §1:
   A-r4 scope = primary 16 + FOMC sensitivity 4 + C1/C2/C3/C4 = 4; SPEC_PB1_ES
   r3 untouched). **Headroom for new ES identities = 0.**
   - Consequence [OBSERVED, ESNQ RANKING_INPUT §3]: the four ES families'
     minimal demands (F1 11 + F2 11 + F3 7 + F4 7 = **aggregate 36**) exceed
     headroom ⇒ **every ES family is BLOCKED_TRIAL_BUDGET**. Executable now
     at zero identities: ES-F3 stage-1 vol leg, ES-F1/F2/F4 anatomy pre-gates
     (F1-K6/F2-K6/F4-K6 descriptive measurements).
   - Any ES entry ⇒ owner amendment + explicit ceiling re-check. No silent
     grid cutting; label everything that exceeds.
2. **NQ, FX (6E/6B), and by extension 6J/6A/COMM: NO cap is defined by any
   standing ruling.** Stated plainly: the FX lane's own census
   (≈360 base + ≈288 strata/overlays ≈ **648** if ALL families+strata ran)
   has **no ceiling applied to it**; the NQ census (minimal aggregate 36,
   full-grid 168 ESNQ-wide) is **contingency only** behind cost/clock gates
   + full-era rebuild. If the owner sets caps, these censuses are the input
   to that decision — this document does not propose levels.
3. **The one measured lesson about cap pressure** [OBSERVED, PLAYBOOKS §1
   r5 arithmetic]: the PB1 FULL design is **D1 = 52** identities (single-delay
   placebo, consistent with the C1 row) or **D2 = 53** (placebo as a delay
   PAIR — the more rigorous control). Both > 24 ⇒ BLOCKED_TRIAL_BUDGET; the
   chosen A-r4 = 24 publishes the limitation "single-seed placebo 20261002,
   single delay — NO permutation-robustness claim". Lesson, restated as a
   rule: **every census must show BOTH the full-rigor count and the capped
   scope with its published limitation** — rigor costs identities by
   construction, and the honest output is the pair, never a quietly
   downsized grid.

---

## 3. The placebo-budget question (owner-decision, framed)

The program currently holds **three inconsistent conventions** for control
legs [OBSERVED]:

| convention | where | treatment |
|---|---|---|
| (a) PLAYBOOKS r4/r5 law | PB1 | C1/C2/C4 = scored identities (own PnL path); C3 flat = 1 identity, 0 trades; C5 non-PnL convention = 0 |
| (b) ESNQ census | ES/NQ families | minimal totals include C1+C2+NC = 3 scored controls |
| (c) FX census | 6E/6B families | controls NOT counted as identities at all; PB2 court §c4 demands multi-seed (≥100 seeds) clock/placebo with seed-dispersion bands and flags the treatment as **Co-Owner ruling pending** (court §d row 6) |

The arithmetic that forces the decision [INFERENCE from committed inputs]:

- If multi-seed placebo is ruled **budgeted identities**: ≥100 seeds ×
  families run. For the 18 returned family-legs alone that is ≥1,800 placebo
  identities — an order of magnitude above every existing or conceivable
  cap; nothing else in the program would be schedulable. The D2=53-vs-24
  lesson shows the pressure already at ONE extra placebo delay.
- If ruled **diagnostics (0 identities)**: the A-r4-style publication law
  applies program-wide — every family's control band must publish
  "single-seed, no permutation-robustness claim" until a court-class
  multi-seed pass is explicitly funded as prep (the PB2 court treats the
  multi-seed band as a PASS CRITERION for reopening, i.e. robustness is a
  gate input, not a scored result).
- The PB2 court's power findings bound the whole question [OBSERVED, §c2-§c3]:
  at realistic trigger densities (n ≈ 300-900/symbol) the court can only
  detect mean effects ≈ 4-9 bp/trade — **at or above the full modeled cost —
  the power floor and the cost floor coincide**; the ≥500-trigger census
  gate is a PRE-commitment before any scored design freeze; a court that
  cannot reach the census gate or the power floor is VOID before scoring
  (kill-by-thinness, PB3 K0 precedent). Consequence: the placebo-budget
  decision interacts with caps — underpowered families burn identities to
  learn nothing, which is the strongest denominator-level argument for
  census-gate-before-scored-cell sequencing that this program has measured.

**This document takes no side.** The synthesis packet should carry the three
conventions, the arithmetic above, and the owner's ruling slot empty.

---

## 4. Census table skeleton (the synthesis lane fills the PENDING rows)

Columns are fixed; every cell must cite its source doc (sibling RANKING_INPUT
§ / FX §8 / PLAYBOOKS §1 / this lane's CROSS_HYPOTHESES). "Controls counted"
records which convention §3 the row uses — **do not sum across rows with
mixed conventions without normalizing first.**

| family | lane | legs | type | arms | tails | delays | tiers | full-grid IDs | minimal-core | controls counted (n) | minimal total | 0-cost legs | cap status / headroom | gates before any scoring | source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PB1 OVN pair (H-A/H-B) | parent | ES | T2 | 2 | 2 | 2 | 3 | 24 (+28 FOMCIN full) | A-r4 = 24 FROZEN | yes (C1/C2/C3/C4 = 4) | 24 incl. | K1-K5 era views; C5 convention | **FROZEN 24; headroom 0**; NO_GO stands | fees-account D2, calendar D3, A7 review, spec freeze | PLAYBOOKS §1 |
| ES-F1 FOMC-RES | ESNQ | ES | T1 | 2 | 2 | 2 | 3 | 24 | 8 (S2) | yes (3) | **11** | F1-K6 anatomy gate | **BLOCKED_TRIAL_BUDGET** (headroom 0) | F1-K6 reproduce; owner amendment for any cell | ESNQ RI §2-3 |
| ES-F2 MACRO-0730 | ESNQ | ES | T1 | 2 | 2 | 2 | 3 | 48 (CPI+NFP) | 8 (CPI,S2) | yes (3) | **11** | F2-K6 gate; NC-2b canceled-day subset | BLOCKED_TRIAL_BUDGET | F2-K6 per-era anatomy | ESNQ RI §3 |
| ES-F3 COT-CROWD | ESNQ | ES | T1+T3 gated | 2 | 2 | 1 | 1 | 4 (stage-1 vol = 0) | 4 | yes (3) | **7** | stage-1 vol leg (0 IDs) | BLOCKED_TRIAL_BUDGET | F3-K1 session-granularity vol gate | ESNQ RI §3 |
| ES-F4 RUN-REV | ESNQ | ES | T4 | 2 | 2 | 1 | 1 | 8 (k∈{3,5}) | 4 (k=5,S2) | yes (3) | **7** | F4-K6 placement gate | BLOCKED_TRIAL_BUDGET | F4-K6 intraday placement | ESNQ RI §3 |
| **ES aggregate** | | | | | | | | | | | **36 minimal** | | **all BLOCKED; headroom 0** | | ESNQ RI §3 |
| NQ-F1 FOMC-ERA | ESNQ | NQ | T1 | 2 | 2 | 2 | 3 | 24 | 8 (S2) | yes (3) | **11** | NQ-F1-K6 gate | no NQ cap defined — CTG | cost gate (fee A7), calendar 2026, full-era rebuild | ESNQ RI §3 |
| NQ-F2 MACRO-0730-NQ | ESNQ | NQ | T1 | 2 | 2 | 2 | 3 | 48 | 8 (2023-26, S2) | yes (3) | **11** | K6 era gate; NC-6b | CTG | anatomy gate (2023-26 only on committed evidence) | ESNQ RI §3 |
| NQ-F3 RUN-REV-NQ | ESNQ | NQ | T4 | 2 | 2 | 1 | 1 | 8 | 4 | yes (3) | **7** | rebuild itself = K6 | CTG | **full-era rebuild (hard precondition)** | ESNQ RI §3 |
| NQ-F4 ROLLWK | ESNQ | NQ | T5 | 2 | 2 | 1 | 1 | 4 (Role-B) | 4 | yes (3) | **7** | Role A chain audit (standing, 0) | CTG | K6 interaction measurement; Role A audit law | ESNQ RI §3 |
| FX-F1 London-Range | 6E6B | 6E,6B | T2 | 2 | 2 | 3 | 3 | 36/leg | census-gated | **no (0)** | (census contingency) | court census ≥500 triggers | **PB2 HOLD — not schedulable** | court census + power floor + ancestry court | FX §8 |
| FX-F2 Policy-Decision | 6E6B | 6E,6B | T1 | 2 | 2 | 3 | 3 | 36/leg (+36/stratum) | n/a | no (0) | (census contingency) | ECB/FOMC strata descriptive | no FX cap defined — CTG | power honesty (MDE 17-21 bp at n 56-58) | FX §8 |
| FX-F3 US-8:30 | 6E6B | 6E,6B | T1 | 2 | 2 | 3 | 3 | 36/leg (+36/stratum) | n/a | no (0) | (census contingency) | unclassified-8:30 stratum | no FX cap defined — CTG | vintage law application; latency NOT_RUN inherited | FX §8 |
| FX-F4 Reopen-Gap | 6E6B | 6E,6B | T2 | 2 | 2 | 3 | 3 | 36/leg (+36 Sunday) | n/a | no (0) | (census contingency) | 6B gap-std anatomy gate | no FX cap defined — CTG | 6B anatomy-first gate | FX §8 |
| FX-F5 CIP overlay | 6E6B | overlay | T3 | — | — | — | — | 0 standalone; host×2 | 0 | host's | 0 standalone | — | **owner-gated** (vintage decision, court §d row 7) | FX §8 |
| FX-F6 CoT overlay | 6E6B | 6E | T3 | — | — | — | — | 0 standalone; host×2 | 0 | host's | 0 standalone | 6B near-zero falsifier | no cap defined — CTG | intraday-transfer NOT_RUN | FX §8 |
| **FX aggregate if ALL ran** | | | | | | | | **≈648** | | | | | **no ceiling applied** | | FX §8 |
| X-1..X-5 cross diagnostics | CROSS | multi | T6 | — | — | — | — | **0 by class** | 0 | own permutations | **0** | ALL steps 0-cost | n/a (never scored) | per-design prereqs (NQ rebuild, common-window re-measure) | CROSS_HYPOTHESES |
| 6J/6A families | 6J6A | 6J,6A | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING (PB3-6A ancestry PARK standing) | PENDING | **lane concurrent — not read** |
| COMM families | COMM | CL/NG/GC/SI | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING (v1: NOT_QUALIFIED_V2 — status per lane) | PENDING | **lane concurrent — not read** |

Program-wide hypotheticals [INFERENCE, denominator illustration only —
NOT a proposal]: ESNQ full-grid sum = 24+48+4+8+24+48+8+4 = **168**;
FX all-in ≈ **648**; cross = **0**; PB1 = 24 (frozen). Nothing above is
registered, schedulable, or recommended; ES is hard-blocked at 0 headroom,
NQ sits behind its gates, FX sits behind HOLD/none, and two lanes are
unreturned.

---

## 5. Census hygiene rules the synthesis lane should enforce

1. **Mixed conventions cannot be summed** — normalize §3 conventions (or
   report both totals) before any program-wide denominator is quoted.
2. **Every scored result enters the observed denominator**, controls
   included, even on publication fail (PLAYBOOKS §4.2 law).
3. **Full-design vs capped-scope pairs** must be shown together (the
   D1=52/D2=53/A-r4=24 precedent) — no silent downsizing.
4. **0-cost legs are enumerated, not assumed**: anatomy pre-gates, stage-1
   descriptive legs, court census passes, era views, cross diagnostics —
   each named with its source, so prep work is never mistaken for scored
   spend.
5. **Missing = NOT_RUN**: no PENDING cell may be filled by inference from
   dossiers alone; only the returning lane's artifacts fill it.

— End of CENSUS_PROPOSAL.md. Denominator planning only; no registration
proposed; no GO recommended; every number above traces to a committed
artifact or is labeled INFERENCE with inputs named.
