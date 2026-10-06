# TERMINAL A7 — FUTURES-ES-PB1-V1 (post-scored-run scientific evaluation)

- Task: TERMINAL-A7 · Cycle: FUTURES-ES-PB1-V1 · Date: 2026-10-06
- Audited HEAD: `8283f135e4c4ada9f9903ef9509838864aff5ee0` (branch
  `prep/futures-es-reg-20261004`) — ONE rev-parse at start, status EMPTY at
  start; artifacts read-only; zero network; root `.venv` Python only.
- Authority: SPEC_PB1_ES.md §8 (gates G1-G9 + K2, pre-registered) + §9
  (terminal outcomes, pre-decided); registered plan
  `plans/PLAN_futures_es_pb1_v1.md` §4 gate 6 ("terminal outcomes
  pre-decided; REJECT_ALL valid"); ratified D-1 two-layer law
  (`auth/RATIFICATION_RECORDED.json`): ledger PASS = execution-status ONLY;
  the scientific layer is evaluated by THIS audit.
- Scored run of record: `gate6/ledger/runs/go_run_1/`
  (terminal_handoff.json: EXECUTION_COMPLETE, exit 0, 2026-10-06T00:54:48Z).

## VERDICT (one line)

**TERMINAL OUTCOME: `FUTURES_ES_V1_REJECT_ALL`. K2 FIRED — PB1 family dead,
re-param forbidden. Zero of 8 primary arms survive the pre-registered
SPEC §8 floor. No promotion/paper/live. S1 stays SEALED_UNTOUCHED.**

---

## V1 — Artifact integrity (all PASS; evaluated before any science)

| check | result | source |
|---|---|---|
| ledger file sha256 re-measured | `c51143bc6b960572ed4e06ba391d7df777207058413dc72577ee806fead8a4d2` == terminal_handoff.ledger_summary.file_sha256 == reconciliation.ledger_summary.file_sha256 | `shasum -a 256 gate6/ledger/trial_ledger.jsonl` vs `terminal_handoff.json` L8/L15 |
| frozen 24 ids == ledger identity set == terminal_handoff per-identity set | TRUE (set-equal, 24/24) | `reconciliation.json.frozen_identity_ids` vs trial_ledger.jsonl rows vs terminal_handoff L17-42 |
| observed denominator | 24 (slots 24, rows 24, status PASS 24 / FAIL 0 / NOT_RUN 0 / REFUSED 0) | terminal_handoff.ledger_summary |
| reconciliation integrity flags | `cost_recompute_sample: PASS`, `warmup_regression: PASS`, `pass: true`, `output_files_match_frozen_table: true`, `terminal_ids_exact_once: true` | `reconciliation.json` |
| twin manifests byte_match | TRUE, 26/26 files, differing=[], only_in_a/b=[] | `twin_manifests.json` |
| twin re-hash (5 sampled pass_a/pass_b pairs) | 5/5 byte-identical on disk AND equal to manifest sha (CONT-UP-D0-S2, REV-DN-D30-S2, PLA-D0-S2, ALW-D0-S2, FLAT) | fresh `shasum -a 256` this audit |
| ledger result_sha == pass_a file sha (spot) | match (CONT-UP-D0-S2: `f0064013…`) | trial_ledger.jsonl row seq 1 vs twin_manifests.pass_a |
| per-record trade count == totals.n_trades | 24/24 match; Σ trades = 13,165 | pass_a records |
| execution-status ledger | 24/24 PASS — **execution semantics only (D-1), NOT profitability** | trial_ledger.jsonl |

## V2 — Applied evaluation law (computed from pass_a trades[]; definitions)

Computed by this audit from `pass_a/<id>.json` per-trade records
(`net_pnl_usd`, `fold`, `session_date`) — the FIRST lawful consumption of
scored outcomes; no precomputed PnL totals exist in the artifacts.

- Expectancy = mean(`net_pnl_usd`)/trade. PF = Σ(wins)/|Σ(losses)| on
  `net_pnl_usd`. Fold sums over F1..F4 (SPEC §7).
- K1 eras (G4): session year 2010-2016 / 2017-2021 / 2022-2026; G4 PASS =
  same expectancy sign in all 3 eras (sign-consistency; stable-negative
  counts as stable — documented finding TA7-F3).
- G6 (K3): share = window PnL(2020-03..2020-04)/total_net, evaluated only
  when total_net > 0; otherwise NOT_EVALUABLE_G6_TOTAL_NONPOSITIVE (never
  inferred PASS) — finding TA7-F2.
- G7 comparators at S2: C2 `FBES1-ALW-D0-S2` exp = −10.22;
  C1 `FBES1-PLA-D0-S2` exp = −100.28 (both FAIL G1 themselves, as controls
  should). FOMCIN within-set reading gives identical verdicts (TA7-F5).
- Survivor unit = ARM (pattern × direction × delay) at its **S2** record:
  SPEC §8 pre-registers G2/G3/G7 "tại S2"; the S1 tier appears only inside
  G1 "(và S1)" via the P-B S1 sibling. D30 arms have no S1 sibling in the
  frozen 24 table (SPEC §6 design) → G1-S1 extension NOT_IN_FROZEN_TABLE
  (TA7-F8).
- Cell vocabulary: PASS / FAIL / N/A_TIER(S2_BINDING) / N/A_ROLE /
  NOT_EVALUABLE_<gap> — N/A and NOT_EVALUABLE never count as pass.

## V3 — 24 × G matrix (all numbers from pass_a records)

Comparator reference: C1 exp −100.28 · C2 exp −10.22.

### Primary arms P-A (8, all S2)

| identity | n | exp | PF | f+/4 | era signs (K1) | G1 | G2 | G3 | G4 | G5 | G6 | G7 | floor |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CONT-UP-D0-S2 | 288 | +34.03 | 1.0672 | 3 | −++ | PASS | **FAIL** | PASS | **FAIL** | PASS | PASS (−0.04) | PASS | **FAIL {G2,G4}** |
| CONT-UP-D30-S2 | 288 | +46.22 | 1.1019 | 2 | −+− | PASS | PASS | PASS | **FAIL** | PASS | **FAIL (1.247)** | PASS | **FAIL {G4,G6}** |
| CONT-DN-D0-S2 | 264 | −7.81 | 0.9876 | 1 | −−+ | **FAIL** | **FAIL** | **FAIL** | **FAIL** | PASS | NE*t | PASS | **FAIL {G1,G2,G3,G4}** |
| CONT-DN-D30-S2 | 265 | −66.81 | 0.8934 | 1 | −−+ | **FAIL** | **FAIL** | **FAIL** | **FAIL** | PASS | NE*t | **FAIL** | **FAIL {G1,G2,G3,G4,G7}** |
| REV-UP-D0-S2 | 288 | −152.09 | 0.7633 | 0 | −−− | **FAIL** | **FAIL** | **FAIL** | PASS | PASS | NE*t | **FAIL** | **FAIL {G1,G2,G3,G7}** |
| REV-UP-D30-S2 | 288 | −130.97 | 0.7790 | 1 | −−+ | **FAIL** | **FAIL** | **FAIL** | **FAIL** | PASS | NE*t | **FAIL** | **FAIL {G1,G2,G3,G4,G7}** |
| REV-DN-D0-S2 | 264 | −181.34 | 0.7511 | 1 | −−− | **FAIL** | **FAIL** | **FAIL** | PASS | PASS | NE*t | **FAIL** | **FAIL {G1,G2,G3,G7}** |
| REV-DN-D30-S2 | 265 | −125.86 | 0.8045 | 1 | +−− | **FAIL** | **FAIL** | **FAIL** | **FAIL** | PASS | NE*t | **FAIL** | **FAIL {G1,G2,G3,G4,G7}** |

NE*t = NOT_EVALUABLE_G6_TOTAL_NONPOSITIVE (total_net ≤ 0; window sums
recorded in computed_stats.json). G5 (K4) PASS for all 4 P-A pairs: D0/D30
expectancy signs agree (CONT-UP +/+ · CONT-DN −/− · REV-UP −/− · REV-DN −/−)
— no sign flip anywhere; the family's failures are NOT delay-pair
instabilities.

### P-B cost siblings (8; D0 arms at S1/S3 — NOT survivor candidates; robustness views)

| identity | n | exp | PF | era signs | G1 (own tier) | G4 | notes |
|---|---|---|---|---|---|---|---|
| CONT-UP-D0-S1 | 288 | +59.03 | 1.1191 | +++ | PASS (S1 binding) | PASS | G2/G3/G6/G7-side: G4,G6 PASS; see TA7-F1 |
| CONT-UP-D0-S3 | 288 | +9.03 | 1.0174 | −++ | PASS_at_S3 (non-binding) | FAIL | stress tier |
| CONT-DN-D0-S1 | 264 | +17.19 | 1.0278 | −−+ | PASS (S1 binding) | FAIL | tier flips sign vs S2 (−7.81) — cost fragility |
| CONT-DN-D0-S3 | 264 | −32.81 | 0.9491 | −−+ | FAIL_at_S3 (non-binding) | FAIL | |
| REV-UP-D0-S1 | 288 | −127.09 | 0.7972 | −−+ | FAIL | FAIL | |
| REV-UP-D0-S3 | 288 | −177.09 | 0.7313 | −−− | FAIL_at_S3 (non-binding) | PASS | |
| REV-DN-D0-S1 | 264 | −156.34 | 0.7811 | +−− | FAIL | FAIL | |
| REV-DN-D0-S3 | 264 | −206.34 | 0.7222 | −−− | FAIL_at_S3 (non-binding) | PASS | |

G2/G3/G7 = N/A_TIER(S2_BINDING) for all P-B rows (values reported above).
G5 = PASS_VIA_PA_PAIR (same arms).

**TA7-F1 (LOW)**: a mechanical per-identity floor scan marks
CONT-UP-D0-S1 "floor=True" because its tier lacks G2/G3/G7 cells. Refuted
as survivor: the pre-registered law binds those gates at S2; arm
CONT-UP-D0 fails G2 at S2 (PF 1.0672 < 1.10). Evaluating G2/G3/G7 on the
S1 record and promoting it would be post-hoc gate invention
(outcome-informed: S2-negative-PF arm passing at S1). NOT a survivor.
Recorded to block resurrection attempts.

### FOMCIN sensitivity (4, all S2)

| identity | n | exp | PF | f+ | era signs | G1 | G2 | G3 | G4 | G6 | G7 | floor |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CONT-UP-D0-S2-FOMCIN | 9 | +344.81 | 1.9625 | 2/4 | −++ | PASS | PASS | PASS | **FAIL** | PASS (0.297) | PASS | **FAIL {G4}** |
| CONT-DN-D0-S2-FOMCIN | 2 | −141.99 | 0.0000 | 0/1‡ | −.. | **FAIL** | **FAIL** | **FAIL**‡ | NE‡ | NE*t | **FAIL** | **FAIL** |
| REV-UP-D0-S2-FOMCIN | 9 | −1078.80 | 0.0363 | 1/4 | −−− | **FAIL** | **FAIL** | **FAIL** | PASS | NE*t | **FAIL** | **FAIL** |
| REV-DN-D0-S2-FOMCIN | 2 | +8.01 | 1.5431 | 1/1‡ | +.. | PASS | PASS | **FAIL**‡ | NE‡ | PASS (0.0) | PASS | **FAIL {G3}** |

‡ only 1 fold populated (2 trades) — G3 "≥2/4 folds positive" cannot be met
(FAIL with ONLY_1_FOLDS_POPULATED); G4 NOT_EVALUABLE_G4_ERA_WITHOUT_TRADES.
G5 = N/A_ROLE(NOT_P_A_FAMILY). The sparse-cell FOMCIN arms are
sensitivity views, not candidates; the informative one (CONT-UP-FOMCIN,
n=9) still fails G4. FOMCIN improves CONT-UP expectancy (344.81 vs 34.03)
but n=9 — no gate is met that would change any verdict.

### Controls (4; reference roles, not candidates)

| identity | n | exp | PF | f+ | era signs | evaluable failures |
|---|---|---|---|---|---|---|
| C1 PLA-D0-S2 | 2920 | −100.28 | 0.7936 | 0/4 | −−− | G1,G2,G3 FAIL |
| C2 ALW-D0-S2 | 2920 | −10.22 | 0.9771 | 2/4 | −−+ | G1,G2,G4 FAIL |
| C3 FLAT | 0 | — (no trades) | — | 0 | — | G1/G4/G6 NOT_EVALUABLE_NO_TRADES (correct by construction) |
| C4 DOSE-D0-S2 | 2885 | −108.00 | 0.7798 | 0/4 | −−− | G1,G2,G3,G7 FAIL |

G7 = N/A_ROLE for C1/C2 (they are the comparators). Controls behaved as
controls must: all negative after cost — the placebo/baseline/flat/dose
ladder shows no conditioning-free edge, which supports the machinery's
discriminative validity.

### G8 / G9 (cycle-level)

- **G8 repro byte-match: PASS (carried)** — twin manifest 26/26 byte_match
  + 5 sampled pairs re-hashed identical this audit (V1).
- **G9 A7 0 HIGH/CRITICAL unresolved: PASS** — closed by this audit:
  findings TA7-F1..F8 below are LOW/NOTE only; none is outcome-flipping.

### Per-tier pass counts (floor = all applicable G1-G7 PASS)

- Primary arms (8): **0 above floor**.
- FOMCIN (4): **0 above floor**.
- Controls (4): 0 (by construction/reference).
- P-B siblings (8): not candidates (arm-level law); TA7-F1 recorded.

## V4 — K2 family verdict (SPEC §8)

Floor definition: an arm is above the floor iff it passes every binding
pre-registered gate G1-G7 on its S2 record (G8/G9 cycle-level, both PASS).

- CONT primaries: 0/4 above floor (best: CONT-UP-D30 fails G4 era-stability
  + G6 COVID concentration; CONT-UP-D0 fails G2 PF 1.0672 < 1.10).
- REV primaries: 0/4 above floor — every REV identity has NEGATIVE
  after-cost expectancy at every tier (G1 sign-level failure, 8/8 rows).
- **K2 FIRES: CONT and REV both below the floor ⇒ PB1 family DEAD,
  re-param FORBIDDEN** (SPEC §8 K2 law). This forbids re-parameterization
  of the family in this lineage; a different family is a new cycle with a
  new registration and a fresh budget ceiling — not a re-param of PB1.

## V5 — TERMINAL OUTCOME (SPEC §9 pre-decided vocabulary)

Applied selection law (documented, none invented):

- `FUTURES_ES_V1_SURVIVOR_PENDING_S1` — requires ≥1 arm survivor. **None.**
- `FUTURES_ES_V1_BLOCKED_<reason>` — requires a process/integrity blocker.
  V1 integrity is all PASS; run terminal_state = EXECUTION_COMPLETE. None.
- `FUTURES_ES_V1_NO_ELIGIBLE_IDENTITY` — fits when eligibility is
  undetermined or vacuous. Not used: the rejection is fully determined
  per-gate with recorded numbers, and K2 fires.
- **`FUTURES_ES_V1_REJECT_ALL`** — evaluation complete on the full
  pre-registered 24, zero survivors, family dead by K2. Selected. (The
  registered plan §4 gate 6 explicitly notes "REJECT_ALL valid".)

Evidence chain (each step an artifact field):
1. GO two-key complete (`auth/GO_RECORDED.json`: owner verbatim typed GO +
   A7 prelaunch AUTHORIZED_WITH_FINDINGS 0 HIGH/CRITICAL).
2. Scored run EXECUTION_COMPLETE, exit 0, lock acquired/released
   (terminal_handoff.json), twin byte_match 26/26.
3. Ledger 24/24 PASS execution-status, observed denominator 24
   (trial_ledger.jsonl; D-1 law: execution semantics only).
4. V1 integrity all PASS (this audit, table above).
5. Scientific layer computed by this audit from pass_a trades[]:
   0/8 primary arms above floor; per-gate numbers in the matrix.
6. K2 fires (CONT and REV both below floor) ⇒ family dead, re-param
   forbidden.
7. §9 selection ⇒ `FUTURES_ES_V1_REJECT_ALL`. No promotion/paper/live in
   this cycle. S1 remains SEALED_UNTOUCHED (moot under REJECT_ALL; any
   future reopening is a NEW explicitly-authorized cycle, not this one).

## Honesty statements

1. **Ledger PASS ≠ profitability** (ratified D-1 two-layer law, restated):
   the 24/24 ledger PASS records certify mechanics-complete execution; the
   scientific layer evaluated here REJECTS ALL 24 identities. Both facts
   stand simultaneously; neither may be quoted without the other.
2. **Denominator law**: 24/24 identities observed, published (published=true
   24/24), and consumed by this evaluation. No publication failure; no
   NOT_RUN slot; no denominator ambiguity.
3. **Multiple comparisons**: 24 pre-registered identities were evaluated on
   pre-registered gates — this is the census-gate situation; however NO
   survivor selection occurred, so no selection inflation enters the
   record. The near-miss CONT-UP-D0 (G2 PF 1.0672 vs 1.10) must NOT be read
   as "almost eligible": post-hoc threshold relaxation is re-param-adjacent
   and forbidden by K2.
4. **NOT_RUN remains NOT_RUN**: S1 sealed prospective stage (would need its
   own explicitly-authorized stage; moot under REJECT_ALL);
   VERIFIED_VS_ACCOUNT cost verification (costs stay MODELED COST); BBO
   measured fills; D2 account/tier evidence; the ×1.5/×2.0 stress ladder
   has no pre-registered binding gate in this cycle (×1.0 was the gate
   number) — ladder evaluation NOT_RUN, recorded, not inferred.
5. **Cost model caveats carried**: current-as-approximation exchange fees,
   close-proxy spread, D1 research-assumption slippage tiers (SPEC §5
   notes; known-wrong approximations documented, direction not claimed).
6. **No invention**: every cell cites computed_stats.json /
   computed_gates.json / the pass_a records; NOT_EVALUABLE cells are
   explicit with named gaps; no gate was evaluated at a tier or in a way
   the pre-registration does not support (TA7-F1 documents the one
   tempting violation and its refusal).

## Findings (G9 close: 0 HIGH / 0 CRITICAL / 3 LOW / 5 NOTE)

| id | severity | finding |
|---|---|---|
| TA7-F1 | LOW | CONT-UP-D0-S1 mechanical floor=True artifact (N/A tier cells) — refuted as survivor by the S2-binding law; arm fails G2 at S2 (PF 1.0672). Post-hoc resurrection blocked. No outcome impact. |
| TA7-F2 | LOW | G6 NOT_EVALUABLE (total_net ≤ 0) for 13 identities — degenerate share denominator; window sums recorded; all affected fail G1 anyway; no outcome sensitivity. |
| TA7-F3 | LOW | G4 "era-sign stable" = same-sign across the 3 pre-registered eras; stable-negative counts as stable (consistency test). The two stable-negative primaries fail G1; no outcome sensitivity. |
| TA7-F4 | NOTE | CONT-UP-D30-S2 G6 failure is substantive: 2020-03..04 window = +16,601.20 vs total +13,311.90 (124.7% of net profit) — profits exist only inside the COVID window. |
| TA7-F5 | NOTE | FOMCIN G7 under the within-set reading ≡ plain C2/C1 reading (identical verdicts). |
| TA7-F6 | NOTE | 2-trade FOMCIN arms: G4 NOT_EVALUABLE (eras without trades), G3 unmeetable (1 fold populated); both fail G1/G7 regardless. |
| TA7-F7 | NOTE | Era boundaries = calendar years on session_date; E1 is 2010-06..2016-12 in practice (data window post-EXCLUDE). |
| TA7-F8 | NOTE | G1 "(và S1)" extension NOT_IN_FROZEN_TABLE for D30 arms (SPEC §6 design); not a failure, recorded. |

## Outputs of this audit

- `research/control/FUTURES-ES-PB1-V1/terminal/TERMINAL_A7.md` (this file — authority)
- `research/control/FUTURES-ES-PB1-V1/terminal/terminal_a7_digest.json` (machine mirror)
- `research/control/FUTURES-ES-PB1-V1/terminal/computed_stats.json` (per-identity raw statistics)
- `research/control/FUTURES-ES-PB1-V1/terminal/computed_gates.json` (per-identity gate cells + verdicts)
- `research/control/FUTURES-ES-PB1-V1/dispatch/handoff_TERMINAL-A7.json` (zcode_orch_v3_handoff@1)

Artifacts unmodified; S1 untouched; root read-only; zero network; no
commit/stage/push (controller records the outcome).
