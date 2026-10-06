# CYCLE_LAUNCH_DRAFT — FUTURES-SIX-V1 (working title) — cycle/historical-backtest launch packet

- Round: **FUTURES-SIX-ADOPT-PREP-20261004**, lane **PACKET** (parallel task, owner item).
- Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-six-adopt/prep`,
  branch `codex/futures-six-adopt-prep-20261004`, HEAD measured at lane start
  **`9fb66c88d464fd90748bc04d78280c2d87939cd3`** (== dispatch_sha; one `git rev-parse HEAD`
  run, no other git; controller commits per manifest `commit_policy`).
- Format precedent: `research/control/FUTURES-ES-V1-PACKET/` (PLAN + SPEC_PB1_ES + A7-SPEC
  structure) and `research/control/DAILY-EXPLORATORY-V1/` (A7 two-key + GO_RECORDED gate).
- Status: **LAUNCH DRAFT — PACKED FOR OWNER REVIEW. NOT REGISTERED. NOT AUTHORIZED. NOT GO.**
  `NO_GO_REGISTER / NO_GO_SCORE / NO_GO_ORDER` remain in force. This packet grants nothing:
  no scored cell, no A7 run, no registration, no order of any kind is authorized, performed
  or enabled by its existence. Machine mirrors: `packet/open_decisions_dependency.json`
  (§8), lane handoff `dispatch/handoff_PACKET.json`.

## 0. Mission and scope

One future registered scored cycle covering 6 CME futures — **ES, NQ, 6E, 6B, 6J, 6A** —
run as a *historical* backtest under a frozen, registration-bounded trial budget,
falsification-first. No edge is claimed unless every gate in §6 passes at the cycle's own
gate after a typed owner GO. This document is the packet an owner reviews BEFORE any
registration/GO; per-symbol executable specs (SPEC_PB1_*-style) are produced only from an
approved packet, at the cycle's own registration freeze.

Standing rulings carried unchanged into this draft (all restated, none reopened):
`NO_GO_REGISTER/SCORE/ORDER`; **PB2 HOLD** (6E/6B program court); **PB3 PARK** (6A);
6F `NOT_RUN_DATA_ABSENT`; all fees MODELED / `VERIFIED_VS_ACCOUNT=NOT_RUN` / UNDER REVIEW
until owner-authorized fee A7 (D2); ES 24 trial identities frozen until D4 rules otherwise;
BLS/FOMC/BoE/RBA PIT vintage law in force; `data-ready ≠ scored-authorized`.

## 1. Data contract (per symbol; binding at freeze)

Pinning law (all symbols): the chain of record consumed by the cycle must be **re-hashed
(sha256) into the selection freeze at registration**; raw-lineage re-derivation scripts and
their digests are pinned alongside; the reproduction twin (§6 step 4) re-derives and must
match. Any drift between pinned digest and consumed bytes ⇒ `BLOCKED`, never silent reuse.
Deprecated caches (NQ baseline cache, pre-v3) are **not** consumable by any future research.

| Sym | Chain of record (candidate) | Span / size | O1M coverage window | Pinning anchors |
|---|---|---|---|---|
| ES | baseline chain per SPEC_PB1_ES §1 (rule-based T-5 PIT roll, 68/68 expiries re-derived, 66/66 data-side) | 2010-06 → 2026-10; 4,204 held sessions | full era, era-correct sessions ~97–100% | SPEC_PB1_ES.md `445f7499…b7073`; DATA_READINESS_ES.md `1407b1d4…67927` |
| NQ | **cache_v3** (`FUTURES-SIX-READINESS-20261004/nq/cache_v3/`) — **canonical candidate, PENDING D9 ratification** | 6,780,608 bars; 66 rolls; 4,219 held sessions | 2010-06-06 22:00Z → 2026-09-30 23:59Z | held-chain key digest `d359b4d4…e07e3d`, sessions digest `64203dd2…f7da66` (run-1 = run-2, independently reproduced); DATA_READINESS_NQ.md `fc14b69c…c097` |
| 6E | measured k=5 chain (`held_calendar.parquet`), 27 switches, lead 13–19d | 3,054,311 bars; 1,746 held sessions | 2020-01 → 2026-09-30 (AV1B/AV1R/AV1T eras, butts no-overlap verified) | DATA_READINESS_6E.md `c7ea807b…3cd05` |
| 6B | measured k=5 chain, 27 switches | 1,746 held sessions (measured) | same acquisition eras as 6E | DATA_READINESS_6B.md `555ab253…c4cf7` |
| 6J | baseline k=5 chain, 1,745 sessions — **cease-guard standard adoption PENDING D9** | 2,843,938 bars; 27 rolls | 2020-01-01 → 2026-10-01 | 6J cease-guard law `6J_DEEP_v2.md §8 / ERRATUM M-5`; DATA_READINESS_6J.md `2e322ef2…3ef7` |
| 6A | measured k=5 chain, 1,746 sessions, 27 rolls — **explicit cease-guard variant pending D9** | 2,703,211 bars (1,584 `6BU5` contaminant bars excluded by documented rule) | 2020-03-17 → 2026-09-14 (first→last roll) | `6a_roll_measured.json`; DATA_READINESS_6A.md `28ea9093…9a8e` |

Hole / DST handling laws carried from round-1 (all six symbols):

1. **Adjudicate before patching.** A hole is classified `OBTAINED-absence` vs
   `data-absence` only from evidence (alias adjudication precedent). Absence-class holes
   close at $0 only via sha-pinned view-rule repairs (NQ §2 boundary); never via imputation.
2. **Low-coverage ≠ hole.** Sessions with RTH-core coverage < 60% minutes-with-bar
   (ES law; NQ 154 such sessions = real market structure: US holidays incl. Juneteenth
   2022+, Dec-24 half days, era-A Friday early closes, DST-fall-back Sundays, 2026-10-01
   partial tail) are EXCLUDED by deterministic bar-count/coverage rules, never imputed.
3. **DST fall-back quirk (NQ) reproduced, not fixed, flagged for owner**: baseline caches
   prove absolute-24h session semantics on fall-back Sundays (35 (contract, session) rows
   2010–2024 keep the Sunday `session_date` for post-17:00 Globex-open bars). v3 lib
   reproduces the measured behavior. Changing semantics = new chain build + new digest +
   full before/after reconciliation; never an in-place edit.
4. **2026 dubious days excluded** wherever ES/NQ Globex holiday session times are
   NOT_OBTAINED; FX holiday session times 2024-25 NOT_OBTAINED (early-close minutes) —
   holiday-shortened sessions excluded by bar-count in FX family specs.
5. **Vendor contaminants excluded by documented rule** (6A: 1,584 `6BU5` bars; ES/NQ:
   `raw_symbol` dash-filter with the §2 alias boundary).
6. **6J volume-definition law**: the 0.455× definition gap makes volume usable as
   shares/ratios only — never as absolute levels (no liquidity claims in levels).

## 2. PIT laws (in force; binding on every arm)

- **Vintage law (standing)**: event calendars are keyed to the vintage as-of the decision
  date — `available_time = vintage(decision_date)`; **current-calendar inference
  FORBIDDEN** everywhere (BLS vintages incl. 2025 lapse anomalies already resolved in
  baseline artifacts; DFF 16 year-end vintages + latest snapshot, no 2025 vintage —
  declared caveat stands, not a dense PIT series).
- **FOMC**: 58/59 release-time proof law; ES standing-outside law — every FOMC statement
  day is base-EXCLUDED at day level (132 statements 2011–2026 incl. 40 untimed 2011–2015),
  FOMCIN = the inverse include set. 6E overlay: ECB 55/55 meetings 2020–2026.9, decision
  14:15 CET/CEST (declared convention).
- **BoE (6B)**: MPC 30/32 dated decisions; **RBA (6A)**: 395 dated decisions
  1990–2026-09-30, PASS at *date* granularity only — decision TIME not carried; the
  14:30-Sydney anchor stays a declared convention. **BoJ (6J): PARTIAL** — 156 statement
  files, dates only, **no intraday timestamps in corpus**; intraday stamps remain an owner
  decision; the JF1 12:00–15:30 JST anchor stays a declared convention with its
  anchor-robustness K-law. None of these may be inferred PASS.
- **Calendar cells provenance classes**: every expiry/holiday/deviation cell consumed at
  freeze carries provenance **OBTAINED** (file + sha256, or fetch-log line) or
  **NOT_OBTAINED** — and NOT_OBTAINED is **never rule-derived** (IMM-rule expiry derivation
  forbidden; aged-out service windows are INCONCLUSIVE and never counted as cells). Current
  NOT_OBTAINED inventory (D12): 6E ECU26/ECZ26; 6B 2023Q1–2024Q2 expiries + 0/42 holiday
  windows (documented absence); 6J 2023+2026 quarters + holiday times; 6A 2023Q1/Q2 +
  2026 quarters; NQ 2026 holiday deviations; 6E 7 aged-out 2023 windows inconclusive.
  Any quarter/session whose status cannot be proven is EXCLUDED (fail-closed), per-quarter
  for roll-integrity cells.
- **Alias view-rule boundary (pre-fixed repair decision, NQ)**: `instrument_id == 16908
  AND dt < 2020-06-01 UTC ⇒ raw_symbol = 'NQM0'` (relabel, include); all other dash rows
  are true calendar-spread rows and stay excluded. This boundary is fixed once, sha-pinned
  inside cache_v3 lineage (`alias_lineage.json`: 92,075 rows / 24,686,121 vol recovered,
  id-16908-only proof), and is **not re-litigated per arm**. Changing it = owner amendment
  + full re-derivation + new chain digests.

## 3. Cost contract (per symbol; MODELED COST everywhere)

Labels binding on every number below: **MODELED COST / UNDER REVIEW /
`VERIFIED_VS_ACCOUNT=NOT_RUN`** until the owner-authorized fee A7 runs clean (D2).
**A7 precondition per D2**: the fee A7 (packet READY-not-run, sha `60b095fe…f9dfc` pin in
`DATA_READINESS_6E.md`; status artifact `verify/fee_a7_status.json`
`5f81c7f2…532f9`) must return 0 HIGH/CRITICAL unresolved BEFORE any scored cell on any
symbol. No words "measured cost" may appear on any output.

| Sym | Tier-1 all-in / side (modeled) | Composition / notes |
|---|---|---|
| ES | **2.24** | 0.85 commission Fixed + 1.38 exchange + 0.00 clearing + 0.01 regulatory — IBKR's own byte-verified worked example. SPEC §5's frozen cell 1.386 is the retired glued-superscript value, carried as UNDER-REVIEW-ERRATUM; frozen specs are never edited in place |
| NQ | **2.24** | same corrected table (pointer `FEES_CORRECTED.md @72c9bc5b` + `esnq_hypotheses.json::cost_law`); slippage tiers S1/S2/S3 = 23.49 / 28.49 / 33.49 per side (modeled, D1 assumption); 6.5-tick close proxy ⇒ $16.25 spread half-turn |
| 6E / 6B | **2.46** | 0.85 + 1.60 + 0.01; FX-group fee alias mapping PARTIAL (generic CME "Forex Futures" row). RT bands: 6E **3.6–6.3 bp**, 6B **6.3–11.2 bp** (close-proxy spreads, high-biased) |
| 6J | **2.46** (tier table T1 2.46 / T2 2.26 / T3 2.06 / T4 1.86) | **RT tier table**: RT T1 / 1-tick = 2 × (2.46 + 25.00 + 6.25) = **$67.42 = 8.4499 bp** of measured notional $79,787.50 (12,500,000 × 0.006383, re-measured from the 2026 raw tail); tier range **8.30–12.10 bp**; spread $25 = 4-tick close proxy (high-biased); slippage {1,2,3} ticks × $6.25 |
| 6A | same FX tier table | **era-aware tick law (D8) REQUIRED — see below**; post-break RT T1/1-tick $54.92 = 8.2 bp; NOT valid in the 2020 sub-era |

- **D3 basis choice = OPEN input, both variants quantified** (regulatory cell, ES/NQ):
  - **Variant A — official NFA timeline (SPEC §5 frozen law)**: 0.02/side default;
    0.01 only 2014-10-01 → 2017-12-31; single-source rule (IBKR's 0.011 offset NOT added
    anywhere). ES per-side all-ins S1/S2/S3 = 21.006 / 33.506 / 46.006 (window −0.01 ⇒
    20.996 / 33.496 / 45.996).
  - **Variant B — captured IBKR basis**: 0.01/side throughout (the 2.24 tier-1
    composition above). Delta vs A = $0.01/side = $0.02/RT per contract.
  Selection is an owner ruling at or before the cycle's registration freeze; until then
  the frozen SPEC §5 law (Variant A) binds by default.
- **6A era-aware tick law (D8, REQUIRED spec element for any 6A arm)**: era-1
  2020-01-02..2020-11-20 (231 sessions) = 1e-04 grid = **$10.00/tick** (zero odd prints in
  327k+ closes); era-2 from 2020-11-23 = 5e-05 grid = **$5.00/tick**. Every 6A cost/spread/
  slippage model must branch on the era boundary; fail-closed default until D8 is ruled:
  **era-2-only cost models may not back-cast into 2020-era windows** (Option B keeps the
  boundary PROVISIONAL pending a vendor/exchange document).
- **Stress ladder (every scored identity, every symbol)**: declared modeled costs evaluated
  at **×1.0 (base/observed composition), ×1.5, ×2.0** (DAILY-EXPLORATORY precedent). The
  ×1.0 after-cost number is the gate number; ×1.5/×2.0 are disclosed robustness views; a
  survivor that dies at ×1.5 is disclosed as such, never hidden.
- **BBO / fill / queue NOT_RUN on all six symbols** (D5 law — single-level BBOMsg cannot
  prove fill/queue). Conservative fill law binds everywhere: fill = next-bar open, no
  limit/queue claims, close proxies only, SL-priority on same-bar TP/SL.

## 4. Trial budget & folds

Per-symbol census surfaces (all recounted in round-1, no new trials opened):

| Sym | Census surface | Status / ceiling |
|---|---|---|
| ES | **36 minimal vs 24 frozen** (headroom 0) — D4 | all ES families `BLOCKED_TRIAL_BUDGET` until ruled. Default scope if 24 stands: SPEC §6 table — P-A 8 + P-B 8 + FOMC 4 + C1/C2/C3/C4 = 24; any cell outside the table = owner amendment |
| NQ | 4 families / 6 mechanisms, all `CONTINGENT` | **no NQ numeric cap exists in standing rulings — explicit owner ceiling required** before registration |
| 6E / 6B | **648 program-hypothetical** = 288 base (4 families × 2 syms × 36) + 360 declared strata contingency | **no ceiling defined by any standing ruling**; PB2 HOLD must be lifted first; owner ceiling required |
| 6J6A | **29–36 minimal** (JF1 11 + JF2 7/host + JF3 11; the 3 controls count inside minimal; full-grid 96); 6A side: AF1 11 + AF3 11 minimal (full-grid 48) | 6A is **PB3 PARK — contingency only**; 6J has no cap — explicit owner ceiling required |

Denominators (P-9 ledger law): every registered identity counts into the observed
denominator regardless of publication failure; folds multiply evaluation, never
identities; intake snapshot ≠ current total.

**Fold structure proposal** (per symbol; final boundaries fixed at registration freeze):
yearly sequential folds over each chain's measured span with warmup carve-outs —
warmup = 252 sessions (ES precedent) excluded from scoring at each fold head; folds
respect era seams as *views*, not fold cuts. ES precedent 4-fold shape: F1 2010-06..2012-12
· F2 2013-01..2017-12 · F3 2018-01..2021-12 · F4 2022-01..2026-09. FX/6A symbols fold only
inside their measured 2020-03+ spans; the 6A 2020-11 tick break and the ES session eras are
handled as declared era views (K1-style era-sign stability), never as silent resplits.
S1 = **SEALED_UNTOUCHED** (prospective post-freeze only). Era K-views to declare per
symbol at freeze: ES session eras (16:30/16:15/16:00 CT), 6A tick eras (D8), FOMC/COVID
regimes, fee-tier windows.

**Placebo-budget ruling pointer**: C1-style placebo cells are single-seed/single-delay by
ES precedent (declared seed, published-limitation framing, no permutation-robustness
claims). Any permutation/robustness expansion requires an explicit owner placebo-budget
ruling (folds into D4/ceiling law); absent that ruling, no permutation claims exist.

## 5. Baselines & controls (per the baseline hypo format)

- **Control set per family (ES precedent, carried)**: **C3 FLAT anchor** (identity
  instantiated, zero trades — accounting floor), **C2 always-on control** (signal ignored;
  an arm that does not beat C2 after cost ⇒ "no conditioning information"), **C1 placebo**
  (declared seed, §4 pointer), **C4 dose-response**. Every family names its
  **neighbour family** (nearest mechanism) and the expected sign/ordering between them;
  neighbour non-response is a registered family anomaly, not a pass.
- **Clock-only shadow law** (sibling-after-cost/clock gate, NQ census): every family
  registers a clock-only shadow arm — identical entry/exit/holding machinery driven purely
  by the clock, no signal. An arm that does not beat its clock-only shadow after ×1.0 cost
  is dead for that family; shadows consume identity budget like any cell.
- **Cease-guard event days as natural-experiment controls**: the three measured
  manifestations — **6J 2022-09-20** (k=5 held dead 6JU2 while 6JZ2 traded 125,303 lots),
  **6A 2024-12-17** (dead 6AZ4 held; 6AH5 traded 55,675 lots), **6A 2026-06-16** (dead
  6AM6 held; 6AU6 traded 55,533 lots) — plus the eliminated NQ-before window
  (NQH0_2020 dead-held 2020-03-23..05-29, fixed in cache_v3). Any roll-window arm must
  reconcile behavior between naive-chain and explicit-guard-chain switch dates on these
  days; divergence is a data-contract violation (§1), never alpha. These cells register
  as controls, are never tuned, and count toward the budget like all cells.

## 6. Gates — sequence and SHAs (two-key law)

Ordered; each step's outputs are sha-pinned; **no step runs without the prior one**:

1. **Registration** at the cycle's own gate, at ROOT checkout (owner-run or explicitly
   owner-delegated root session — registry writes on main are outside every prep lane).
   Freeze set, all sha256 into the selection freeze: cycle spec sha + exclude-list sha +
   identity-table sha + §1 chain digests + §3 cost-table digest + §2 calendar provenance
   manifest. Re-hash at freeze; drift vs this packet's §9 pins ⇒ BLOCKED.
2. **Prelaunch A7 — key 1 of 2.** Independent fresh-context audit (A7-SPEC probe style,
   machine digest) covering: identity enumeration vs the frozen table, cost arithmetic
   vs the pinned table, PIT/exclude coverage, budget accounting, freeze integrity,
   "no-measured-cost" language scan. Verdict required: **0 HIGH/CRITICAL unresolved**
   (`AUTHORIZED` / `AUTHORIZED_WITH_FINDINGS`, findings discharged). Fee-layer A7
   precondition (D2) is separate and prior for any cost-bearing cell (§3).
3. **Exact-arm dry-run.** Single-shot rehearsal of the exact registered identity set
   under declared ×1.0 costs; budget counters untouched; output quarantined
   descriptive-only (zero scored cells consumed). Pass = byte-exact identity enumeration
   vs the frozen table AND cost recomputation matching the pinned table (probe R1/R2
   precedent). A dry-run failure ⇒ back to freeze, never a mid-flight repair.
4. **Owner typed GO — key 2 of 2** (§7) — consumed verbatim at the gate, EXACT match,
   recorded `auth/GO_RECORDED.json` (DAILY-EXPLORATORY-V1 format precedent
   `ef88fd80…07df`).
5. **Scored run under heavy lock** (single heavy job machine-wide;
   `researchctl.py locks inspect`; held ⇒ `NOT_RUN_RESOURCE_CONFLICT`).
6. **Reproduction twin (G8)**: detached twin re-runs the scored computation; byte/logical
   match required; chain re-derivation digests must equal the pinned §1 digests.
7. **Terminal A7 + two-half close** (handbook §32). Terminal outcomes pre-decided at
   freeze (`*_REJECT_ALL` / `*_NO_ELIGIBLE_IDENTITY` / `*_SURVIVOR_PENDING_S1` /
   `*_BLOCKED_<reason>`); REJECT_ALL is a clean, valid result.

Per-identity gates (G-series shape, ES precedent): after-cost expectancy > 0 at the
declared tier; PF floor; ≥2/4 folds positive; era-sign stability (K-views); D0/D30-style
delay sign-stability within family; crash-window concentration cap (K3-type); arm beats
C2 and C1 after cost; repro byte-match; A7 clean. Family kill (K2-type): if both signed
arms sit under the floor, the family is dead — re-parameterization forbidden.

## 7. GO law (explicit)

**NOTHING in this packet runs until the owner issues a typed GO at this cycle's own
gate, AFTER registration.** This packet grants nothing and exists for review only:

- `NO_GO_REGISTER / NO_GO_SCORE / NO_GO_ORDER` remain in force end-to-end.
- The owner directive "cho agent làm đi" (for PREP) does **not** ratify
  D2/D3/D4/D8/D9 and does **not** grant a typed GO or scoring.
- GO form (exact, typed verbatim, fresh, at the gate): `GO <REGISTERED-CYCLE-ID> SCORED
  EXECUTION`. An early/paraphrased GO = intent only, dies unconsumed. Two-key completion:
  key 1 = prelaunch A7 authorized (0 HIGH/CRITICAL unresolved); key 2 = owner phrase,
  EXACT match. No promotion, no paper, no live, no order, no S1 access, no registry
  write outside the registration step, no post-GO spec edits — any of these ends the
  cycle as `BLOCKED_AUTHORITY`.

## 8. Open-decision dependency table (machine mirror: `open_decisions_dependency.json`)

| ID | Decision (source) | Blocks packet section(s) | Fail-closed default if unanswered |
|---|---|---|---|
| **D1** | P3 transport adjudication (carried; recommended default B) | §2 (admissibility of P3-obtained calendar evidence; Q5 reuse rules) | P3-obtained cells stay quarantined; Q5 data usable only after per-use independent re-verify |
| **D2** | Authorize the fee A7 (4 sub-rulings e.1–e.4) | **§3 (every cost number, all 6 symbols); §6 gate 2 precondition** | fees stay MODELED / VERIFIED_VS_ACCOUNT=NOT_RUN / UNDER REVIEW; no scored cell passes any cost gate |
| **D3** | NFA basis $0.01/side (NFA 0.02 vs offset) | §3 (regulatory cell ES/NQ) | SPEC §5 frozen Variant A binds (0.02 default, single-source; 0.01 window only) |
| **D4** | ES denominator: 36 minimal vs 24 frozen | §4 (ES scope + placebo budget) | 24 frozen stands, headroom 0; ES families BLOCKED_TRIAL_BUDGET |
| **D5** | CPI Jan-2026 announcement pin (permitted routes) | §2 (BLS vintage completeness for macro-conditioned arms) | current-calendar inference forbidden; dependent cells stay NOT_RUN |
| **D6** | Remaining calendar cells (sibling list; non-mission symbols) | §2 (carried siblings only) | NOT_OBTAINED stands; derivation forbidden |
| **D7** | NG signed-surprise rule + comm data path | §2 (not this cycle's symbols) | no NG/commodity arm exists in this cycle |
| **D8** | 6A era-aware tick/cost law (Option A ratify boundary / Option B demand document) | §1 (6A chain digest semantics); §3 (6A cost spec REQUIRED element) | era-2-only cost models may not back-cast into 2020-era windows; boundary PROVISIONAL |
| **D9** | Explicit cease-guard standing law + NQ cache_v3 canonicalization | §1 (NQ/6J/6A chains of record); §5 (control-day set) | cache_v3 stays "candidate"; any chain consumption requires measuring and disclosing guard violations first |
| **D10** | Sibling Q5 coverage over-claim erratum (8/23 captures absent) | §2 (provenance hygiene for Q5-derived cells) | sibling artifact keeps working status with corrective evidence; no new cell may cite the 8 absent captures |
| **D11** | Databento corpus rights posture beyond read-only research | §1 (any use beyond read-only research: sharing, redistribution, derived products; publication-subset branch) | read-only research only; anything else needs a fresh ruling first |
| **D12** | Residual NOT_OBTAINED calendar cells (6 symbols; bounded permitted-route extension vs leave) | §1/§2 (late-2026 rolls; holiday windows) | cells stay NOT_OBTAINED; affected windows excluded fail-closed; no purchase/signup proposed anywhere |

**Hardest single dependency: D2.** It is the only exit from the fee layer for all six
symbols simultaneously, gates the prelaunch A7 precondition in §6, and every D3 variant
and every per-symbol cost table is dead weight until it is ruled.

## 9. Evidence index (sha256, computed at this HEAD `9fb66c88…`)

| Artifact | sha256 (head) |
|---|---|
| `FUTURES-SIX-READINESS-20261004/synth/OWNER_DECISIONS.md` | `d14e436f9110dd1a9f425ed1c0303d4acd77064344d1902cff26019fa1daad93` |
| `FUTURES-SIX-READINESS-20261004/synth/SIX_SYMBOL_CENSUS.md` | `7c006db6aa0aecb554904eeb765a65dcf1d074cc293128b3061a52302f97fe35` |
| `FUTURES-SIX-READINESS-20261004/synth/six_symbol_census.json` | `6296df9eb40b3bbde25c77aaf3c39e7eada4e3f65bfbd45fdfb9d02a76ed9107` |
| `FUTURES-SIX-READINESS-20261004/es/DATA_READINESS_ES.md` | `1407b1d4828c4d715fff474da4693e5a94153ab1b8b069f2e6528c08c0567927` |
| `FUTURES-SIX-READINESS-20261004/nq/DATA_READINESS_NQ.md` | `fc14b69c16ef04daf46851653f5b7595b2740b5bd2cfcd3d3e8e8fb55a11c097` |
| `FUTURES-SIX-READINESS-20261004/fx_eb/DATA_READINESS_6E.md` | `c7ea807b7e3a48e5ec5ad485448a71bd77139b9a68be0581e6776e8d8993cd05` |
| `FUTURES-SIX-READINESS-20261004/fx_eb/DATA_READINESS_6B.md` | `555ab25361264a4209a01c1c09a0e76ed5f4ac456837937959e8ff747a7c4cf7` |
| `FUTURES-SIX-READINESS-20261004/fx_ja/DATA_READINESS_6J.md` | `2e322ef2199a2f8d8019a073b906be27275865ac4c64855b00a23ff5081a3ef7` |
| `FUTURES-SIX-READINESS-20261004/fx_ja/DATA_READINESS_6A.md` | `28ea9093b25516112a96efbeb58c9ddd57d6d94f914b845954eec3d26da39a8e` |
| `FUTURES-SIX-READINESS-20261004/verify/fee_a7_status.json` | `5f81c7f2eaf3569cb3dab79fdc0961c7a6abee22dd5ca403c80934c3146532f9` |
| `FUTURES-ES-V1-PACKET/SPEC_PB1_ES.md` | `445f749906481f33080185cab1628e6365ef2f6db3b9c4f9f0847646eb6b7073` (== lane pin, unedited) |
| `FUTURES-ES-V1-PACKET/PLAN_futures_es_v1.md` | `06140882f13d96fd1325c472ef3788da7d4ce1c6b571c7c27d75b8e8e0c7a06b` |
| `DAILY-EXPLORATORY-V1/auth/GO_RECORDED.json` (two-key gate precedent) | `ef88fd8043e54dc0337983d6e17040fde656d2a4acc2697a7664106b8b0f07df` |

Round-2 lane outputs (adoption packet, cease-guard standard, D8/D9 measurement, fee A7
status) land under `research/control/FUTURES-SIX-ADOPT-PREP-20261004/{adopt,cal_eb,
cal_janq,fee_es,hypo,verify}/` and are incorporated by their own handoffs; this packet
pins their round-1 inputs only. If any §9 digest drifts at the cycle's freeze ⇒ BLOCKED.

— End CYCLE_LAUNCH_DRAFT. Preparation, not authorization. No PnL was computed, no
backtest executed, no cycle registered, no network used.
