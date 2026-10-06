# EXECUTOR_REPORT — EXEC lane, cycle NFL-WINPROB-NG-SCORED-V1

- Lane: `EXEC` · Written: 2026-10-05 · Dispatch SHA:
  `876845e01932393319fcca05924dca0e8243744a` (= actual start HEAD, measured equal at lane
  start and end) · Branch: `orca/nfl-winprob-ng-scored-v1-integration`
- Deliverable: the auditable POST-OWNER-GO execution path (gates G1–G8), proven ONLY on
  synthetic fixtures; ERRATUM_R3 drafted pinning it. The owner has NOT typed GO; the REAL
  registry still refuses at G1 (proven, case a).
- Language law: calibration/forecasting vocabulary only. $0 spent. No 2019+ outcome
  evaluation; no real-game probability computed in any lane run (pass-path games are
  `SYNTH_` fixtures; the real canary `2026_04_ATL_NO` is refused BY NAME before any
  computation).

## 1. Design

`research/control/NFL-WINPROB-NG-SCORED-V1/recorder/execute_post_go.py`
(sha256 `8318a399207e86b2a8f4dee4e88b4e7452a6bb17bb43710e78c3a81979e242d4`, pinned in
`lanes/FREEZE_ERRATUM_R3/freeze_digests_r3.json`) WRAPS the frozen recorder — it imports
`frozen_refs` / `pipeline` / `priors` / `schedule` and the ported `nfl_ng_ledger@1` tool
read-only (all R2 pins re-verified at every run) and adds the gate chain in front of the
existing batch pipeline. It contains NO wall-clock read: every timestamp is an explicit
argument or the GO instant recorded in the registry state line, so identical arguments give
byte-identical ledgers (proven by double-run).

Authority flows FROM THE REGISTRY: G1 reads `plans/CYCLE_REGISTRY.json` (default
`--registry`), accepts ONLY lifecycle `ACTIVE_LIGHT`/`ACTIVE_HEAVY` AND a `go_phrase_state`
matching the ERRATUM_R3 canonical form `OWNER_GO_TYPED_LIVE <utc-iso> at head <40-hex>` AND
`go_phrase == "GO NFL WINPROB NG SCORED V1 PROSPECTIVE"`. The executor never reads chat.

Nothing-written law: every gate writes audit lines (gate, inputs, verdict, detail) to the
gate log BEFORE and after evaluation; on any refusal the ONLY file written is the gate log.
Distinct exit codes: G1=11 G2=12 G3=13 G4=14 G5=15 G6=16 G7=17 G8=18 (usage=2, ok=0).
`--allow-control-tree-ledger` guards the REAL control-tree ledger path (never set in lane
runs; post-GO controller use only). GENESIS substitution law asserted BEFORE any write:
the rebuilt placeholder-form payload must re-digest to the R2 pin (`bd94eb77…` on the real
freeze root), and the substitution may touch EXACTLY `created_at` (← registry GO instant)
and `recorder_freeze_sha` (← `3e52b7b1de64c8e2f04867cee37524886c6b3111` from the ERRATUM_R2
CONTROLLER_ADDENDUM).

## 2. Gate table

| gate | implements | refuses on (exit) | fixture proof |
|---|---|---|---|
| G1 registry authority | lifecycle ∈ {ACTIVE_LIGHT, ACTIVE_HEAVY}; `go_phrase_state` startswith `OWNER_GO_TYPED_LIVE` + full canonical regex; registered phrase equality; row head carried to G2 | no row / wrong lifecycle / non-canonical state / phrase mismatch (11) | a, c, d, e |
| G2 freeze coherence | worktree HEAD (read from `.git` files, read-only `git rev-parse` fallback) == registry row head == `freeze_digests_r3.json head_lineage.expected_sha`; arm files (arms/select/boot) sha == `frozen_facts_index.code_freeze_files` pins; recorder 5 modules == R2 pins; frozen imports (arms, ledger tool) == pins; executor own sha == R3 pin; freeze-packet bytes sha == R1 pin; GENESIS payload R2 recomputes == R2 pin; `code_freeze_sha` in payload == `7ec4c539…` | head incoherence / any pin drift / GENESIS recompute mismatch (12) | f, g, h |
| G3 heavy lock | `researchctl locks inspect` from the root cwd, verdict == `FREE_PROVEN`; 3 attempts × 60 s (delay injectable for tests) | lock held or inspect failing after retries (13) | i (+ real FREE_PROVEN in the pass path) |
| G4 snapshot | sha256(file) == provided pin AND pin present in the cycle data manifest (`--data-manifest` fixture form / `freeze_digests.json data_frozen_inputs` real form); load re-pins + quarantines + kickoff-parses (missing/unparseable kickoff ⇒ refuse); future-with-score rows abort | pin mismatch / pin not in manifest / load failure / future score (14) | j, k |
| G5 week (Option B) | `--week ≥ 5`; every batch game: season == target, game_type ∈ {REG, POST}, week ≥ 5; canary `2026_04_ATL_NO` and every `2026_0[1-4]_*` id refused BY NAME before any computation | week < 5 / pre-week-5 game in batch / empty batch (15) | l |
| G6 capture margin | batch_time + 6 h ≤ min(batch kickoff UTC) (exact boundary passes) | margin < 6 h (16) | m |
| G7 arms | arms loaded BY IMPORT from the sha-pinned `lanes/T_SELECT/arms.py`; arm-config digests recomputed == `frozen_refs` pins == `freeze_digests.json` values; declared freeze arm set == exactly {B0, B1_STAR, C3} (no 4th arm); diagnostic twin never fielded; predict output == exactly 3 arms | arm-set cardinality/identity mismatch / digest drift (17) | n |
| G8 ledger | filename law `predictions_<cycle>_<season>.jsonl`; real-path guard; GENESIS pre-write assertions (placeholder digest + substitution diff); existing-ledger chain verify; append via the ported tool; chain validates after append; per-row `recorded_at_utc < kickoff_utc`; row count == 3 × games | filename law / real-path guard / broken chain / placeholder digest / over-wide substitution / post-append break / timestamp violation (18) | o (+ pass path) |

Only after G1–G8: state warmup (state-carry law, ERRATUM_R2 §2 — completed games through the
batch timestamp via the frozen arms; no metric on any warmup game) → batch predict → append
→ chain validation → report (gate log + row count + chain head sha).

## 3. Fixture matrix results (15 cases, 83/83 checks)

Suite: `lanes/EXEC/test_executor_gates.py` (fixtures under
`~/.my-quantitative-data/nfl-ng-scored-v1/exec_fixtures/`, sandboxes under
`.../exec_sandbox/`; evidence `lanes/EXEC/gate_matrix_evidence.json`).

| case | scenario | gate → exit | result |
|---|---|---|---|
| a | REAL registry as-is (`REGISTERED_NOT_CONSUMED`) | G1 → 11 | PASS — plus audit-hook proof: opens during `main()` = registry + sandbox gate log ONLY; zero reads of schedules/pbp/T_SELECT/freeze files before refusal; nothing written but the gate log |
| b | fixture GO-typed-live + synthetic week-5 snapshot + sandbox ledger | all pass → 0 | PASS — 8 SYNTH games × 3 arms = 24 rows, 24 unique pairs, chain valid vs the fixture freeze-packet anchor, scoring rehearsal 24 VALID_PROSPECTIVE, `recorded_at < kickoff` on every row, substitution touches exactly the two placeholders, gate log G1..G8 PASS, double-run byte-identical (ledger 18,936 B, sha256 `fdcc09f88c59ddc…e102b9`; genesis sidecar; registration payload), real freeze digests absent from sandbox bytes, canary absent from all rows |
| c | CONSUMED state | G1 → 11 | PASS |
| d | DEAD lifecycle | G1 → 11 | PASS |
| e | wrong registered phrase | G1 → 11 | PASS |
| f | registry head ≠ worktree HEAD | G2 → 12 | PASS |
| g | arm-file sha tamper (tampered freeze PIN — the real `lanes/T_SELECT/arms.py` is never modified) | G2 → 12 | PASS |
| h | GENESIS R2 digest mismatch (tampered R2 pin) | G2 → 12 | PASS |
| i | lock held | G3 → 13 | PASS — code-path injection, 3 attempts, distinct exit, nothing written. **NOT_RUN_LOCK_SIM** disclosure: the faithful held-flock subprocess variant is not exercised (researchctl hard-codes the REAL lock path; touching it is forbidden); during this lane's runs the REAL `locks inspect` was observed both FREE_PROVEN (pass path) and HELD_PROVEN (a foreign worker `FUTURES-ES-PB1-V1` pid 91472 held it; the executor refused faithfully, nothing written; the foreign worker was never touched) |
| j | snapshot sha mismatch | G4 → 14 | PASS |
| k | future-game-with-score snapshot | G4 → 14 | PASS |
| l | week-4 batch (`--week 4`) + `2026_04_ATL_NO` canary | G5 → 15 | PASS — both the week law and the by-name canary refusal (refusal precedes predict; no p_home ever computed for the canary) |
| m | margin 5.99 h | G6 → 16 | PASS — nothing written |
| n | 4th arm injected into the freeze arm set | G7 → 17 | PASS |
| o | ledger chain pre-broken | G8 → 18 | PASS — nothing appended; target bytes untouched |

Every refusal case: distinct exit code + gate-log REFUSE line + nothing written except the
gate log.

## 4. Freeze-law compliance

- Writes: `lanes/EXEC/**`, `research/control/NFL-WINPROB-NG-SCORED-V1/recorder/
  execute_post_go.py` (ONE new file; the 5 R2-frozen recorder modules untouched and
  re-verified), `lanes/FREEZE_ERRATUM_R3/**`, sandbox dirs, handoff. `git status --porcelain`
  at lane end shows exactly those paths (plus the pre-existing untracked dispatch packet).
- Arm code untouched: `CODE_FREEZE_SHA 7ec4c539…` stands; the R2 module pins re-verified
  green at every executor run.
- GENESIS R2 (`bd94eb77…`) unchanged and binding; the sandbox ledgers anchor to a FIXTURE
  freeze packet (real bytes + marker line) so no real freeze digest ever appears in sandbox
  bytes (asserted in case b).
- ERRATUM_R3 drafted at `lanes/FREEZE_ERRATUM_R3/` (sha256
  `977e34b11fa9e5cbf933ed7f1d9d77c2239c23208953e45a0fcf116b7f40e45e`; digests twin
  `32d3f746e150e32e2cc1628c2a10a821aebf2634466f490c6c778ce468cf52e0`): authority ruling
  (R2 precedent), executor pin, `EXECUTOR_FREEZE_SHA = PENDING_CONTROLLER_ADDENDUM`
  two-step law + head-lineage re-pin law, canonical GO-recording convention, G1–G8
  contract, GENESIS-R2-unchanged statement.

## 5. Existing suites re-run at the final tree (evidence `lanes/EXEC/suites_rerun_evidence.json`)

| suite | result |
|---|---|
| `test_ledger_synthetic.py` (ledger) | **42/42 passed** |
| `test_successor_synthetic.py` (S_SYNTH) | **16/16 passed** |
| PIPE recorder `--mode selftest` | **PASS (10 checks)** |
| PIPE recorder `--mode e2e-synth` | **PASS (3 scenarios + scoring rehearsal; double-run BYTE-IDENTICAL; 0 real-ledger paths)** — the evidence write was REDIRECTED to `lanes/EXEC/pipe_rerun_evidence/` (A7_PRELAUNCH_R2 precedent) so `lanes/PIPE/` files are untouched |

Nothing weakened; no test of any prior lane was modified.

## 6. Known limitations / disclosures

1. **G3 held-lock simulation**: code-path injection only (case i). The faithful
   subprocess variant is impossible for a lane without touching the REAL machine lock.
   Mitigating evidence: the real `locks inspect` was exercised in BOTH states during this
   lane (FREE_PROVEN on the pass path; HELD_PROVEN during the earlier run — the executor
   refused cleanly with exit 13 and nothing written).
2. **Case (g)/(h)/(n) tamper surface**: tampering is modeled on FIXTURE freeze-state copies
   (pins), never on the real frozen files — byte-equivalent evidence for the same checks
   (sha(file) vs pin), without violating the no-touch law for `lanes/T_SELECT` and the
   freeze lanes.
3. **Fixture freeze root**: the pass path anchors its sandbox ledger to a FIXTURE freeze
   packet (real packet bytes + one appended marker line) so the whole digest chain
   recomputes consistently while keeping real freeze digests out of sandbox bytes; the REAL
   ledger (post-GO, controller-run) anchors to the real packet (`9978a950…`).
4. **Head lineage**: `freeze_digests_r3.json head_lineage.expected_sha` is pinned to the
   registered head `876845e0…`; once the controller commits the EXEC outputs, HEAD moves and
   the controller must re-pin (two-step addendum) — G2 refuses until then, by design.
5. The real post-GO predict path uses the REAL pbp pins (`rec_priors.verify_pbp_pins`) —
   implemented but never executed in lane runs (lane runs use the synthetic prior-E table;
   the real warmup path was proven separately by PIPE's `warmup-check`, aggregate counts
   only).
