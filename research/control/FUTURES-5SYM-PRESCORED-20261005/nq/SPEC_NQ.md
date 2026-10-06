# SPEC_NQ — Nasdaq-100 E-mini futures (NQ) PRE-SCORED packet draft — load-bearing laws (bản r1)

- Round **FUTURES-5SYM-PRESCORED-20261005**, lane **NQ**, 2026-10-05. PREP-only.
- Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-5sym-prescored/prep`,
  branch `prep/futures-5sym-prescored-20261005`, HEAD `ffed828f73fa19fa0ff4aee3ac1b441909a43940`
  (== dispatch `base_sha`, measured via one `git rev-parse HEAD` at lane start). No commits by this lane.
- Class: **DRAFT-PENDING-OWNER. 0 PnL, 0 scored runs, 0 backtest PnL, 0 conditional-on-signal
  statistics — outcome-blind.** Structure mirrors the SPEC precedent
  `research/control/FUTURES-ES-V1-PACKET/SPEC_PB1_ES.md` (sha256 `445f7499…b7073`); content is
  NOT copied — every law below is NQ-specific and cited to a committed artifact. Missing evidence
  is `NOT_RUN`, never inferred `PASS`.
- **CONDITIONAL-BINDING STATEMENT.** This spec binds ONLY if, and after, the owner (i) rules
  **ADOPT-D9 Option A** (explicit cease-guard standing law + NQ cache_v3 canonicalization —
  `research/control/FUTURES-SIX-ADOPT-PREP-20261004/adopt/D8_D9_DECISION_SHEET.md`, sha256
  `b1d6079f…f8ae`; D9 is UNRATIFIED as of this round — the chain of record is canonical-CANDIDATE,
  never ratified), (ii) signs an **NQ identity ceiling** (no NQ cap exists in standing rulings —
  `IDENTITY_TABLES.md` §4, sha256 `750858ab…f6e6`), (iii) names the **clock-shadow reading (a)/(b)**
  (`IDENTITY_TABLES.md` §2.1), and (iv) rules the **D3 regulatory basis** for NQ
  (`COST_FREEZE_ERRATUM.md` §2, sha256 `cf83bc2d…9ae8`). Nothing herein self-ratifies, registers,
  schedules, or scores anything. `NO_GO_REGISTER / NO_GO_SCORE / NO_GO_ORDER` stand.
- Companion packet files (same lane, same status): `IDENTITY_BUDGET_NQ.md`(+`.json`),
  `COST_CONTRACT_NQ.md`, `CALENDAR_PIT_POLICY_NQ.md`, `FREEZE_BUILDER_SPEC_NQ.md`,
  `RUNNER_COMPAT_NQ.md`, `GAPS_AND_DECISIONS_NQ.md`. New decision IDs are prefixed `P5-`.

## 1. Instrument identity (binding at any future freeze)

| field | value | status | evidence cite (committed path + sha256, this worktree) |
|---|---|---|---|
| Product | CME **E-mini Nasdaq-100** futures, Globex root `NQ` (contract keys `NQ<SYM>_<YEAR>`, 113 registry clusters) | FACT (restate) | `FUTURES-SIX-READINESS-20261004/nq/cache_v3/contract_registry_v3.json` (sha256 `6a629d71…edcfb`, 35,833 bytes); `DATA_READINESS_NQ.md` §1 (sha256 `fc14b69c…c097`) |
| Multiplier | **20 USD per index point** | PASS_ARITHMETIC_TRIANGULATED; **direct vendor definition capture: NOT_RUN** | `HYPOTHESES_ESNQ_R3.md` field 4 ("NQ: mult 20, tick 0.25 ($5.00/tick)", sha256 `9dfe7b12…d288`); consistent with `esnq_hypotheses.json::cost_law` slippage 5.00/10.00/15.00 = {1,2,3} ticks × $5.00 (sha256 `68e21c56…6605`); consistent with `S6_FRONT_SPREADS.json` NQ median full spread 6.5 ticks = $32.50 (committed at ROOT `d8cf8eca`, **not present in this worktree** — read-only root evidence, disclosed) ⇒ $32.50/6.5 = $5.00/tick ⇒ tick 0.25 pt × $20/pt. No in-repo CME/Databento definition row for NQ (multiplier/min_price_increment) was located — the identity rests on this three-source arithmetic triangulation, and the direct-capture leg stays NOT_RUN |
| Min tick | **0.25 index pt = $5.00/tick** | PASS_ARITHMETIC_TRIANGULATED (same basis as above) | same cites. **Pointer-line defect disclosed:** `DATA_READINESS_NQ.md` §1 prints "NQ tick 0.25 pt / $2.50" — that line is internally inconsistent with its own second half (6.5-tick proxy ⇒ $16.25 half-turn ⇒ $5.00/tick) and with all numeric ladders; flagged **P5-NQ4** (annotation-only erratum; no number in this packet consumes $2.50) |
| Quote unit | index points, USD-denominated contract | PASS (implied by $/pt identity) | same cites |
| Tick constancy | single tick regime across the corpus era 2010-06..2026-09 (no NQ-era tick break analogous to 6A D8; slippage priced in constant $5.00 ticks era-wide) | CARRIED_CONSTRUCTION | `esnq_hypotheses.json::cost_law` prices slippage 5.00/10.00/15.00 flat across the era; no committed NQ tick-era break exists anywhere in the six-round evidence chain (contrast: 6A `6A_TICK_ERA_LAW.md` — 6A-specific law, never applied to NQ) |
| Sessions (era-correct) | Globex day boundary **17:00 CT**; era-A close **16:15 CT** through 2015-09-18 (era-A Fridays 15:15 CT early close class); era-B close **16:00 CT** from 2015-09-21 (`SESSION_SWITCH_DATE`, measured constant); maintenance break 16:00–17:00 CT (**5–6 pm ET**) | MEASURED_CONSTRUCTION | `DATA_READINESS_NQ.md` §4; `CACHE_V3_PIT_STATEMENT.md` §1.2 (sha256 `602ed0d6…9595`). The generic description "Sun 6pm ET open → Fri 5pm ET close + 5–6pm ET maintenance" matches **era-B only**; the era-correct law (16:15→16:00 CT switch) binds, and era-A Friday-15:15 sessions are handled per-session by measured last minute (`NQ_K6_GATES.md` §0.2 statistic 3, sha256 `364f0412…2781`) |
| Expiry rule | quarterly; NQ expiration calendar **68/68 quarters** (36 product-specific + 32 family-level, zero divergence); Juneteenth shifts: **2026-06-18, 2027-06-17; June-2021 NOT shifted** | OBSERVED (authority calendar, never rule-derived) | `FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/cme_cal/nq_es/nq_cal_coverage.json` (sha256 `ad7f4b3a…bf93`); `esnq_hypotheses.json::calendar.juneteenth_law` |

Anything not in this table (margin levels, delivery terms verbatim, a raw vendor contract-definition
capture for NQ): **NOT_RUN for this packet** — margin is a sizing fact, not an edge; the
identity-capture gap is tracked as P5-NQ4-adjacent (direct capture would upgrade
PASS_ARITHMETIC_TRIANGULATED to PASS_CAPTURED, it changes no number).

## 2. Chain of record — cache_v3 (D9-BLOCKED, never ratified)

- **The chain of record law = the cache_v3 panel**:
  `research/control/FUTURES-SIX-READINESS-20261004/nq/cache_v3/` — outright 1m panel
  **6,780,608 rows**, ts 2010-06-06 22:00Z → 2026-09-30 23:59Z; held chain **4,219 sessions /
  66 rolls**; sessions table **11,715** rows; registry **113** clusters; held-daily 4,219 rows,
  **0 NaN closes**. PIT classification **PIT_CLEAN_BY_CONSTRUCTION** (canonical set) /
  **PIT_CLEAN_PER_DECISION** (cease-guard variant) with seams 1–5 declared
  [`CACHE_V3_PIT_STATEMENT.md`, sha256 `602ed0d6…9595`].
- **Alias view rule: 92,075 bars recovered.** `instrument_id == 16908 AND ts_event < 2020-06-01 UTC
  ⇒ raw_symbol = 'NQM0'` (relabel, include); all OTHER dash rows are true calendar-spread rows and
  stay excluded; applied BEFORE the dash-excluding filter. Provenance: adjudication
  `A_ALIAS_NOT_ABSENCE` fixed ~1 day before the rebuild, never tuned on any chain/roll/outcome
  metric; `alias_lineage.json` proves the rule touches **only** id 16908 (sha256 `8669ab65…1a68`).
  Recovered volume **24,686,121** contracts.
- **2020-03-19 crossover**: the v2 chain's wrong 2020-06-01 roll (dte −73 dead handoff) is replaced
  by the true PIT volume crossover **2020-03-19** (dte +1; roll-day volume old 85,489 vs new
  487,005); the other 65/66 rolls are byte-identical dates; **66/66 rolls satisfy 0 ≤ dte ≤ 45**
  (the v2 dte>45 quarantine is retired) [`before_after_2020.json`, sha256 `83753151…2302`].
- **Cease-guard law = max(crossover, cease-floor)** — the explicit guard per
  `CEASE_GUARD_STANDARD.md` §2 (sha256 `6c58a3f8…1b44`): switch date = max(volume-crossover date,
  cease floor); the chain never holds a contract past its bars-present cessation. **STATUS: PROPOSED
  standard, pending owner decision ADOPT-D9 — NOT in force. This spec is D9-BLOCKED: the packet is
  not executable, and the builder hard-refuses, while D9 is unsigned** (`FREEZE_BUILDER_SPEC_NQ.md`
  §5). Measured NQ facts: guard fired **0 times**; cg chain logically identical to plain
  (byte-identical parquets, sha256 `99ff1ca1…6db6`); v2 chain carried 1 violation (NQH0_2020
  dead-held 49 sessions) — eliminated in v3 [`cease_guard_audit.json`, sha256 `4432293a…750b`].
- **v2 caches: SUPERSEDED, never consumable** for any future NQ research
  (`DEPRECATION_NQ_V2_CACHES.md`, sha256 `29790cd1…16b0`); v2's canonical status is closed
  independent of D9; consumption of anything else requires citing that marker.
- **Re-hash verification (this lane, this worktree, 2026-10-05):** all 10 cache_v3 files re-hashed —
  **10/10 sha256+bytes match `adopt/cache_v3_hashes.json`** (sha256 `6cad549d…894d3`) exactly;
  parquet metadata row counts re-measured: panel 6,780,608; annotated 6,780,608; sessions 11,715;
  held 4,219; cg 4,219; held-daily 4,219; rolls file 66; hold segments 67. Lock state at the check:
  `FREE_PROVEN` (`research/researchctl.py locks inspect`); light read only, lock not taken.
- **D9 open-state consequence (fail-closed)**: cache_v3 remains **canonical-CANDIDATE**; any
  consumption elsewhere must cite the D8/D9 sheet per-cycle and must measure and disclose guard
  violations first. This packet never treats it as ratified.

## 3. Session / calendar law — full text in `CALENDAR_PIT_POLICY_NQ.md`

Binding skeleton (details and exact exclusion lists in the companion file):
era-correct session mask per §1 table; **DST fall-back absolute-24h quirk PRESERVED AS MEASURED**
(35 (contract, session) rows 2010–2024 keep the Sunday session_date for post-17:00 Globex-open bars
— reproduced, not fixed; changing semantics = new chain build + new digests, never an in-place edit)
[`DATA_READINESS_NQ.md` §4]; holiday/early-close exclusions **fail-closed** with exact dates/windows
(NQ 2026 product-code holiday deviations **0/10 structurally absent / BLOCKED_TRANSPORT
re-confirmed**; advisory-class register **10/10** incl. Good-Friday 2026-04-03 closed at CLASS level
only — no Equity-class row ⇒ NQ-specific time NOT_OBTAINED ⇒ 2026 dubious days EXCLUDE fail-closed;
NQ early-close times 2011 / 2021–2025 NOT_TRANSCRIBED ⇒ those days EXCLUDE until transcribed);
RTH-core coverage < 60% minutes-with-bar ⇒ EXCLUDE session (154 low-coverage sessions are real
market structure, listed in `v3_qc.json`, sha256 `58ec922b…e1d5`).

## 4. Event PIT law — full text in `CALENDAR_PIT_POLICY_NQ.md`

- **FOMC standing-outside law**: EVERY day with a base FOMC statement is EXCLUDED at day level —
  **132 statements 2011–2026 incl. 40 untimed 2011–2015** (day-level exclusion is time-safe);
  FOMCIN-class arms use the inverse include set [`SPEC_PB1_ES.md` §3 precedent, carried; 
  `CYCLE_LAUNCH_DRAFT.md` §2, sha256 `bc2b6488…cb03`]. On cache_v3 the timed-14:00-ET event set
  reproduces: **85 qualifying events** (v3 admits exactly one additional event, 2020-04-29, vs the
  committed 84) [`NQ_K6_GATES.md` §1, sha256 `364f0412…2781`].
- **BLS first-published vintage rule**: calendars keyed to the vintage as-of the decision date —
  **current-calendar inference FORBIDDEN** (standing ruling); CPI 204 + EMPSIT 204 scheduled dates
  2010–2026, all 08:30 ET (07:30 CT), with the 2025/2026 canceled-and-rescheduled anomalies
  enumerated and canceled-expected days kept as separate negative-control strata, never pooled
  [`esnq_hypotheses.json::bls_pit`, sha256 `68e21c56…6605`].
- **D5 pin (SIX-GATE cal_close)**: CPI January-2026 release **Friday 2026-02-13, embargo 08:30 a.m.
  ET** — two independent official BLS artifacts (pre-release schedule snapshot + release document)
  agree [`CAL_CLOSE_REPORT.md` §1 + §6 T4, sha256 `338cf4e8…a56f`].

## 5. Cost contract — MODELED, full derivation in `COST_CONTRACT_NQ.md`

- Fee A7: **EXECUTED — AUTHORIZED_WITH_FINDINGS, 0 HIGH / 0 CRITICAL unresolved**
  [`fee_a7/A7_FEE_REAUDIT.md`, sha256 `2c1095d6…11ad`]. Every number below and in the companion
  file: **MODELED COST / UNDER REVIEW / `VERIFIED_VS_ACCOUNT=NOT_RUN`.** The words "measured cost"
  and "complete cost" are forbidden on any output.
- **Dual-variant law applied to NQ exactly as the A7 tabulates** [`COST_FREEZE_ERRATUM.md` §2]:
  Variant A (NFA basis 0.02 default / 0.01 only 2014-10-01→2017-12-31) fee all-in **2.25/side**
  ⇒ NQ per-side ladder **23.50 / 28.50 / 33.50**; Variant B (captured IBKR basis 0.01 throughout)
  fee all-in **2.24/side** ⇒ **23.49 / 28.49 / 33.49**. **Delta A−B = +$0.01/side = +$0.02/RT.**
  D3 is an OPEN owner input; until ruled, the packet defaults to Variant A (basis only — the
  retired glued value **1.386 is never consumable**, and the stale SPEC print class
  **21.006/33.506/46.006 is never consumable** anywhere).
- NQ composition: fee all-in + **$16.25 spread half-turn** (6.5-tick close proxy, high-biased;
  full-spread close proxy 6.5 ticks = $32.50 measured on 2026 fronts [`S6_FRONT_SPREADS.json`,
  root `d8cf8eca`, outside this worktree — disclosed]) + **slippage 5.00/10.00/15.00 per side**
  ({1,2,3} ticks × $5.00, research assumption D1) [`esnq_hypotheses.json::cost_law`].
- **BBO NOT_RUN** (synchronous quotes absent; conservative fill law binds: fill = next 1m bar open,
  no limit/queue claims, close proxies only, **SL priority on same-bar TP/SL**). **Stale 21.006-class
  prints are never consumable** (retired glued-value class; see `COST_FREEZE_ERRATUM.md` §1).

## 6. Folds & evaluation (identity-multiplication law)

- **4 folds, ES-precedent shape, mapped to the cache_v3 era** (boundaries fixed at any future
  registration freeze; folds are evaluation multipliers, **never** identity multipliers —
  `SPEC_PB1_ES.md` §6/§7 law carried):
  **F1 2010-06..2012-12 · F2 2013-01..2017-12 · F3 2018-01..2021-12 · F4 2022-01..2026-09**
  (panel coverage 2010-06-06..2026-09-30; held chain last session 2026-10-01 partial tail is
  excluded from scoring by the coverage law). **Warmup = 252 held sessions** excluded from scoring
  at each fold head (ES precedent). **S1 = SEALED_UNTOUCHED** (prospective post-freeze only).
- **Declared era K-views** (evaluation views, never fold cuts, never identities):
  (K-V1) session-close eras — era-A ≤ 2015-09-18 (16:15 CT; Friday 15:15 class) vs era-B ≥
  2015-09-21 (16:00 CT); (K-V2) tri-eras 2010-16 / 2017-21 / 2022-26 (family-field eras);
  (K-V3) FOMC data-eras 2016-19 / 2020-22 / 2023-26; (K-V4) COVID window 2020-03..04 (K3
  concentration-cap view; 2020-03-19/20 roll+expiry sits inside); (K-V5) alias-repair region view
  2018-08..2020-06 (the only region whose bars/rolls changed v2→v3 — an evaluation view, not an
  exclusion); (K-V6) regulatory-fee window view 2014-10-01→2017-12-31 (Variant-A reg = 0.01 there
  ⇒ A ≡ B inside the window; disclosed at any freeze where A binds).

## 7. Baselines / controls / verdict criteria (per the launch-draft §5 law)

- **CONV-B control convention** (3 scored controls per family, controls counted inside minimal
  totals — `IDENTITY_TABLES.md` §2 convention table): (i) **clock-only shadow arm** — identical
  entry/exit/holding machinery driven purely by the clock, no signal; single-seed/single-delay C1
  class per PB1 precedent (seed 20261002; publication-limit framing, NO permutation-robustness
  claim); counted as 1 of the 3 controls under **reading (a)** (owner may rule (b) additive —
  `IDENTITY_TABLES.md` §2.1); (ii) **C2 always-on** (signal ignored; an arm that does not beat C2
  after cost ⇒ "no conditioning information"); (iii) **C3 FLAT anchor** (identity instantiated,
  zero trades — accounting floor). C4 dose-response is the full-grid/sensitivity class, outside the
  CONV-B minimal 3. Family-specific negatives are carried per family from the owning family docs
  (incorporated as the identity-table annex at registration): NQ-F1 NC = FOMCIN inverse-include
  class; NQ-F2 NC = canceled-but-expected BLS days + quiet-era contrast; NQ-F3 NC = M-NQ-RG trend
  competitor; NQ-F4 NC = non-roll-week matched stratum + NEW-4 switch-day audit.
- **Per-identity G-gates (pre-registered, ES G-series shape)**: **G1** after-modeled-cost expectancy
  > 0 at S2 (and S1 reported); **G2** PF ≥ 1.10 at S2; **G3** ≥ 2/4 folds positive at S2; **G4**
  era-sign stability across declared K-views; **G5** delay sign-stability within the family's delay
  pair (D0/D30 families); **G6** K3 concentration — < 80% of contribution from 2020-03..04;
  **G7** arm beats C2 AND C1-class shadow after cost at S2 (failure ⇒ "no conditioning
  information"); **G8** reproduction twin byte/logical match; **G9** terminal A7 with 0 HIGH/CRITICAL
  unresolved. **Clock-shadow gate (NQ census law)**: an arm that does not beat its clock-only shadow
  after ×1.0 cost is dead for that family; shadows consume identity budget like any cell.
- **Family kill law (K2-class)**: if BOTH competing arms sit under the floor at S1, the family is
  dead — **re-parameterization FORBIDDEN**. **Role-A standing law (NEW-4)**: the switch-day jump
  audit is binding on EVERY NQ run — a construction failure kills the RUN, never the hypothesis.
- **Power honesty carried**: EXPWITCH-class MDE arithmetic on NQ (session σ ≈ 112.3 bp from the
  pre-recovery series, defect disclosed) gave MDE ≈ 38.7 bp vs RT(S2) ≈ 15.8 bp conservative —
  power-marginal by construction; the fuller per-family MDE tables are post-freeze arithmetic
  (NOT_RUN now) and use the repaired dispersion where applicable (hole window now measured: 49
  sessions, |1m ret| mean 3.60 bp [`NQ_K6_GATES.md` §3]; full-era RTH 5-min dailyized sd 71.1 bp
  [`session_dispersion_v3.json`, sha256 `87a0eb74…ca46`]).

## 8. Exclusions with pre-decided dispositions

1. **EXPWITCH-NQ leg: DEAD-AT-GATE — excluded from every slate, NOT re-litigated.** F5-K6 part (ii)
   FAILED at its pre-declared condition: **35/66** expiry-Friday held sessions carry RTH 15-minute
   gaps (34 × 15 min, 1 × 14 min; failure years 2012(1), 2013–2020(4 each), 2021(2)); the post-hoc
   (declared-diagnostic, non-adjudicating) ordinary-Friday sample fails 46/80 — the 15-min gap
   signature is a **panel-wide property of the committed 1m data 2013–2021 (vendor granularity
   era-wide)**, not expiry-specific anatomy, and cache_v3's repair scope never targeted it. Per the
   owning doc's own consequence clause the family never enters scoring on the NQ leg; per the
   anti-cherry-pick law the fail is recorded, never re-tuned. Resolving it is an owner DATA-PLANE
   decision (**P5-NQ5**), not a lane parameter [`NQ_K6_GATES.md` §2; `SYNTHESIS_K6.md` §1/§2,
   sha256 `03a8e77e…8237`]. Consequence for the option set: option **NQ-D (43) has no lawful path**
   in this packet; the workable ceiling of drafted options is **NQ-C = 36** (`IDENTITY_BUDGET_NQ.md`).
2. Pre-v2/v2 caches: superseded, never consumable (§2).
3. Stale/glued cost prints (1.386; 21.006-class): never consumable (§5).
4. 2026 dubious days + NOT_TRANSCRIBED early-close days: EXCLUDE fail-closed (§3).
5. Untimed-FOMC 2011–2015 statements: day-level exclusion only (no minute anatomy — standing
   committed NOT_RUN, respected).

## 9. Terminal outcomes (pre-decided at any future freeze)

`FUTURES_NQ_V1_REJECT_ALL` · `FUTURES_NQ_V1_NO_ELIGIBLE_IDENTITY` ·
`FUTURES_NQ_V1_SURVIVOR_PENDING_S1` · `FUTURES_NQ_V1_BLOCKED_<reason>`. REJECT_ALL is a clean,
valid result. No promotion / paper / live / order in any cycle born from this packet. Today the
only honest terminal status of THIS packet is: **DRAFT — NOT_RUN (D9-blocked; ceiling-unsigned;
D3-open)**.

— End SPEC_NQ r1. Draft pending owner; nothing herein registers, schedules, scores, or ratifies.
