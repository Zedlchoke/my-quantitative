# CROSS_SYMBOL_DEDUPE — the 31 existing families × mechanism class, and the DUPLICATE-VETO rule

- Task `FUTURES-TEN-HYPO-PREP-20261004`, lane **CROSS**, 2026-10-04 UTC.
  Worktree @ `a4a882658e09092b5b282b666b30a3cfc5ac3418`.
- Census of families: **21 six-symbol** (PB1; ES-F1..F4; NQ-F1..F4; FX-F1..F6;
  JF1–JF3; AF1–AF3), **8 COMM** (NG-F1/F2, CL-F1/F2, GC-F1/F2, SI-F1/F2),
  **2 R2** (RMM, AF4) = **31**. Machine mirror: `hypotheses_cross.json
  §dedupe`. Outcome-blind throughout.
- Sources: `CENSUS_FINAL.md` (family rows), `FINAL_RANKING.md` §2,
  `RANKING_FRAMEWORK.md` §3, section structure of the four baseline hypo
  docs, `HYPOTHESES_R2.md` §2–§6.

## 1. Mechanism-class groups (G-*) and by-design cross-symbol membership

| class group | members (by design) | shared axis | source |
|---|---|---|---|
| G-FOMC-DECISION (central-bank decision windows) | ES-F1 · NQ-F1 · FX-F2 (6E FOMC / 6B MPC) · JF1 (BoJ MPM) · AF1 (RBA) | scheduled-decision uncertainty resolution / post-decision drift-vs-reversal across 5 symbols BY DESIGN | ESNQ §ES-F1/NQ-F1; FX §2; JPY_AUD §JF1/§AF1; CENSUS_FINAL rows |
| G-MACRO-0730 (US 8:30 hard-data clock) | ES-F2 · NQ-F2 · FX-F3 (both legs) | 07:30 CT / 08:30 ET release spike class across venues | ESNQ §ES-F2/NQ-F2; FX §3; RANKING_FRAMEWORK §3 rows |
| G-SESSION-STRUCTURE (city-session anatomy, T2) | FX-F1 · JF3 · AF3 (+ FX-F4 reopen-gap as T2 adjacent) | home-session discovery vs fade on venue clocks | FX §1; JPY_AUD §JF3/§AF3 |
| G-RUN-REV (multi-day run reversal, T4) | ES-F4 · NQ-F3 | run/VR reversal pair | ESNQ §ES-F4/NQ-F3 |
| G-ROLL-MIGRATION (T5 construction class) | NQ-F4 · RMM · GC-F2 | roll-week migration; RMM shares NQ-F4's Role-A construction law and proposes NO NQ leg by anti-duplication (HYPOTHESES_R2 §2 field 4, §4.3); GC-F2 is construction-only | ESNQ §NQ-F4; R2 §2/§4; COMM §GC-F2 |
| G-OVERLAY-RATES (T3 overlays on rates axes) | FX-F5 · JF2 · AF2 (+ AF4 tick-regime overlay adjacent) | regime conditioning overlaid on live hosts; rates/differential axes; vintage fragility is the shared kill | FX §5; JPY_AUD §JF2/§AF2; R2 §3 |
| G-OVERLAY-COT (T3 overlays on positioning axes) | FX-F6 (+ ES-F3 gated directional exception) | CoT positioning conditioning; 6B near-zero falsifier keeps FX-F6 6E-specific | FX §6; ESNQ §ES-F3 |
| G-EIA-NG-EVENT | NG-F1 ↔ NG-F2 | registered competitors on ONE Thursday-week event space — "falsification-by-competitor", registered together in any future cycle | COMM §6, §NG-F1/F2 |
| G-EIA-CL-EVENT | CL-F1 ↔ CL-F2 | adjudicated on ONE frozen event set with pre-registered conflict split | COMM §6, §CL-F1/F2 |
| G-CURVE-STATE | GC-F1 ↔ SI-F2 | contango-compression vs curve-flip; shared rates dependency declared once | COMM §6, §GC-F1/SI-F2 |
| G-BETA-CONVEX | SI-F1 | GC-beta convexity; dead-class adjacency to BAB-LOWBETA (row 10) but different asset/vehicle and time-series construction | COMM §SI-F1 |
| G-OVN-SESSION | PB1 | OWN class — registered parent; NQ OVN/overnight variants anti-multi-trial-blocked, not ancestry-blocked (HYPOTHESES_R2 §6) | PLAYBOOKS §1; R2 §6 |
| G-REOPEN-GAP | FX-F4 | session-transition trigger (17:00 CT reopen) | FX §4 |
| G-OVERLAY-TICKREGIME | AF4 | conditioning on the measured tick-grid EVENT; no dead ancestor (R2 §6 NO VETO) | R2 §3, §6 |

Overlays vs standalone: **overlays (0 standalone identities, H-G law)** —
FX-F5, FX-F6, JF2, AF2, AF4; ES-F3 is a T1+T3 gated hybrid (stage-1 vol leg
0 IDs). **Construction, never alpha**: GC-F2 (0 identities by class);
RMM Role A (0 IDs ledger); NQ-F4 Role A (standing law).

## 2. Rule output — where a NEW candidate lands, and when it is a DUPLICATE-VETO

**R1 (class-space entry).** A NEW candidate is assigned the class space of
the existing family with the same (mechanism class, venue, clock-window)
triple per §1. Its pre-registration must cite that family as host-of-record
and inherit its kill set (K-columns of `FALSIFICATION_MATRIX.md`).

**R2 (DUPLICATE-VETO — any one suffices).**
- V-a *Same triple, no §b delta*: same class group + same symbol + same
  clock-window as an existing family without a mechanism the dead corpus
  could not represent (court §b) → duplicate. The FX-F1 precedent is the
  honest boundary: same signal class as V2-A4-P2 forced D2=2 and PB2 HOLD
  (RANKING_FRAMEWORK §3 footnote \*; court §a).
- V-b *Dead-cluster rename*: candidate falls in an `ANCESTRY_COURT_INFRA.md`
  cluster whose veto rule fires (e.g. S5 volume-shock on NQ — already
  VOIDed as W1 in HYPOTHESES_R2 §6; S6 range-fade VARIANT_SAME_FAMILY
  kills; S10 rule ports).
- V-c *Registered-parent collision*: OVN/overnight/ES session classes are
  owned by the REGISTERED PB1 parent pair — blocked anti-multi-trial even
  absent a dead row (HYPOTHESES_R2 §6 row 4).
- V-d *Standalone overlay*: a T3-class claim without a live host violates
  H-G law — out-of-law (K7), not merely duplicate.
- V-e *Construction-as-alpha*: roll/migration/chain-integrity claims posed
  as alpha (GC-F2/NQ-F4 Role A/RMM Role A law) — out-of-law as scored
  families.
- V-f *Cap-space zero*: an ES-class candidate is born BLOCKED_TRIAL_BUDGET
  (cap 24 frozen, headroom 0, CENSUS_FINAL §3) — scheduling veto regardless
  of novelty.

**R3 (not a veto, but inherited gates).** A candidate entering a class with
standing pre-gates inherits them verbatim: anatomy reproduction pre-gates
(F1-K6/F2-K6/F3-K1/F4-K6/NQ-F1..F4 K6), census ≥500/symbol (FX-F1 court
§c2), K0 thin-n (6A class), 6J owner ceiling, rebuild precondition
(NQ-F3), NOT_QUALIFIED_V2 data path (all COMM).

**R4 (overlay attach rule).** A conditioning candidate must name its host
from the live-family set and add 0 standalone identities; era strata
follow the host's split law (AF4 pattern, R2 §3 field 5).

**R5 (leg discipline).** Multi-leg classes count identities per leg
(FX 36/leg census; RMM 4/leg); a "new family" that is an existing family's
missing leg is a leg addition, not a new family (RMM vs NQ-F4 adjudication,
R2 §2 field 4).

## 3. Family × class matrix (one row per family; full cells in the JSON mirror)

| family | class group | overlay/construction | by-design cross-symbol sharing |
|---|---|---|---|
| PB1 | G-OVN-SESSION | standalone (registered) | none (parent; blocks NQ OVN variants) |
| ES-F1 | G-FOMC-DECISION | standalone | NQ-F1; FX-F2-6E stratum; JF1/AF1 class |
| ES-F2 | G-MACRO-0730 | standalone | NQ-F2; FX-F3 class |
| ES-F3 | G-COT-CROWD | gated hybrid | FX-F6/JF2/AF2 conditioning class (directional exception) |
| ES-F4 | G-RUN-REV | standalone | NQ-F3 |
| NQ-F1 | G-FOMC-DECISION | standalone | ES-F1 |
| NQ-F2 | G-MACRO-0730 | standalone | ES-F2 |
| NQ-F3 | G-RUN-REV | standalone | ES-F4 |
| NQ-F4 | G-ROLL-MIGRATION | Role B gated | RMM (shared Role-A law); GC-F2 |
| FX-F1 | G-SESSION-STRUCTURE | standalone ×2 legs | JF3/AF3; DEAD-class adjacency FXFV1/V2 (PB2 HOLD) |
| FX-F2 | G-FOMC-DECISION | standalone ×2 legs | ES-F1/NQ-F1/JF1/AF1 |
| FX-F3 | G-MACRO-0730 | standalone ×2 legs | ES-F2/NQ-F2 |
| FX-F4 | G-REOPEN-GAP | standalone ×2 legs | T2 session-transition class |
| FX-F5 | G-OVERLAY-RATES | OVERLAY | JF2/AF2/AF4 |
| FX-F6 | G-OVERLAY-COT | OVERLAY | FX-F5/JF2/AF2/ES-F3 |
| JF1 | G-FOMC-DECISION | standalone | ES-F1/FX-F2/AF1 |
| JF2 | G-OVERLAY-RATES | OVERLAY | FX-F5/AF2/AF4 |
| JF3 | G-SESSION-STRUCTURE | standalone | FX-F1/AF3 |
| AF1 | G-FOMC-DECISION | standalone (contingency) | ES-F1/FX-F2/JF1 |
| AF2 | G-OVERLAY-RATES | OVERLAY | FX-F5/JF2/AF4 |
| AF3 | G-SESSION-STRUCTURE | standalone (contingency) | FX-F1/JF3 |
| NG-F1 | G-EIA-NG-EVENT | standalone | NG-F2 (registered competitor) |
| NG-F2 | G-EIA-NG-EVENT | standalone | NG-F1 |
| CL-F1 | G-EIA-CL-EVENT | standalone | CL-F2 (one frozen event set) |
| CL-F2 | G-EIA-CL-EVENT | standalone | CL-F1 |
| GC-F1 | G-CURVE-STATE | standalone | SI-F2 |
| GC-F2 | G-ROLL-MIGRATION | CONSTRUCTION | NQ-F4/RMM class; never alpha |
| SI-F1 | G-BETA-CONVEX | standalone | BAB-LOWBETA dead-class adjacency only |
| SI-F2 | G-CURVE-STATE | standalone | GC-F1 |
| RMM | G-ROLL-MIGRATION | Role B gated (proposal) | NQ-F4/GC-F2 class; distinct mechanism (R2 §6 NO VETO) |
| AF4 | G-OVERLAY-TICKREGIME | OVERLAY (proposal) | JF2/AF2/FX-F5 class |

— End CROSS_SYMBOL_DEDUPE.md. Outcome-blind; every row cites the baseline
docs; nothing registered or proposed by this lane.
