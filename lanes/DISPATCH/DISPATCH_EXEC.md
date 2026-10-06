# DISPATCH — Lane EXEC (NFL-WINPROB-NG-SCORED-V1) — POST-GO EXECUTION PATH + ERRATUM_R3

ROLE: implementation lane. Build the auditable POST-OWNER-GO execution path the owner ordered:
gate chain reading authority FROM THE REGISTRY, freeze-SHA checks, lock, snapshot/hash, week
≥5, margin ≥6h, correct arms, append-only ledger. Pre-GO it is proven ONLY on synthetic
fixtures (pass case via fixture registry with simulated typed GO); it must REFUSE every wrong
case; it must never compute real-game probabilities while the real registry has no live GO.
Lawfulness: freeze law allows ADDITIONS to the execution surface via ERRATUM (precedent:
ERRATUM_R2 added the recorder); arm code (CODE_FREEZE_SHA 7ec4c539) is untouched. Your work
lands with ERRATUM_R3 pinning the executor freeze.
ABSOLUTE WORKTREE: /Users/hoangminhlong/my-quantitative/.worktrees/nfl-winprob-ng-scored-v1/integration
BRANCH: orca/nfl-winprob-ng-scored-v1-integration · DISPATCH SHA: 876845e01932393319fcca05924dca0e8243744a
ALLOWED PATHS (write): lanes/EXEC/**, research/control/NFL-WINPROB-NG-SCORED-V1/recorder/**,
lanes/FREEZE_ERRATUM_R3/**, sandbox under ~/.my-quantitative-data/nfl-ng-scored-v1/
{exec_sandbox,exec_fixtures}/, + lanes/DISPATCH/handoff_EXEC.json.
FORBIDDEN: git; running the executor against the REAL registry expecting success (it must
refuse — prove the refusal); computing p_home for any real game under any fixture; creating
the real ledger; modifying lanes/T_SELECT, lanes/F_FREEZE, lanes/PIPE, lanes/S_SYNTH files;
2019+ outcome evaluation; betting vocabulary.

## Task 1 — Executor (research/control/NFL-WINPROB-NG-SCORED-V1/recorder/execute_post_go.py)
Argument-driven (--registry <path> defaults to the REAL plans/CYCLE_REGISTRY.json;
--snapshot <path>+--sha256; --ledger-target <path> sandbox in all your runs; --week N;
--batch-time <iso> or now). GATE CHAIN in order, each gate audited (append gate-log line:
gate name, inputs, verdict) and failing LOUD with a DISTINCT exit code, NOTHING written:
G1 AUTHORITY: parse registry row cycle_id=NFL-WINPROB-NG-SCORED-V1; PASS iff lifecycle in
   {ACTIVE_LIGHT, ACTIVE_HEAVY} AND go_phrase_state starts with the canonical live-GO token
   `OWNER_GO_TYPED_LIVE` (ERRATUM_R3 convention: when the owner types the GO phrase at this
   cycle's gate, the controller records go_phrase_state exactly as
   `OWNER_GO_TYPED_LIVE <utc-iso> at head <40-hex>`; any other state — REGISTERED_NOT_
   CONSUMED, CONSUMED, DEAD, intent records — REFUSES). Also verify the row's registered
   go_phrase field equals `GO NFL WINPROB NG SCORED V1 PROSPECTIVE` (no phrase equality ⇒
   refuse; the executor never reads chat, only the registry).
G2 FREEZE COHERENCE: worktree HEAD (measured via reading .git/HEAD + refs — NO git subprocess
   needed; or subprocess git rev-parse read-only) == registry row head == the head lineage
   pinned in ERRATUM_R3; arm files sha256 == freeze_digests.json values; recorder modules
   sha256 == ERRATUM_R2 recorder pins; executor own sha256 == ERRATUM_R3 pin; GENESIS payload
   digest R2 (bd94eb77…) recomputes from the erratum canonical form.
G3 LOCK: researchctl locks inspect (run from root cwd) verdict == FREE_PROVEN (retry 3×60s
   then refuse); record observation.
G4 SNAPSHOT: sha256(snapshot file) == provided pin AND the pin exists in the cycle's data
   manifest; abort on any future-kickoff row carrying a score; abort on missing kickoff UTC.
G5 WEEK: every batch game has season 2026, game_type REG/POST, week ≥ 5 (Option B law; week
   parsed from the snapshot week column or game_id; refuse any week-4/pre-week-5 game incl.
   2026_04_ATL_NO by name in a canary test).
G6 MARGIN: batch_time + 6h ≤ min(kickoff_utc of batch games) else refuse.
G7 ARMS: exactly the 3 fielded arms with frozen configs (B0 const 0.571399049390; B1*
   K=40/HCA=0/γ=2/3; C3 θ=50) — loaded from the FROZEN arms code by import; arm config
   digests == freeze values; no other arm runs.
G8 LEDGER: append via the ported nfl_ng_ledger tool at ledger-target; first use performs the
   GENESIS substitution law (placeholders replaced: created_at = the GO timestamp recorded in
   the registry state line; code_freeze_sha = 7ec4c539…; recorder_freeze_sha = R2 pin;
   then payload digest must equal bd94eb77… — assert BEFORE writing); chain validates after
   append; rows one per (game, arm) with recorded_at_utc < kickoff_utc enforced.
On ALL-PASS: warmup (state-carry law) → batch predict → append → validate → report (gate log
+ row count + chain head sha). The pass path computes probabilities ONLY for the batch games
at the ledger target — in YOUR runs the games are synthetic fixtures and the target sandbox.

## Task 2 — Synthetic gate-fixture suite (lanes/EXEC/test_executor_gates.py)
Fixture registry files (copies with edited go_phrase_state/head), fixture freeze states,
fixture snapshots. Cases (each asserts distinct exit code + nothing-written):
(a) REAL registry as-is (REGISTERED_NOT_CONSUMED) ⇒ REFUSE at G1, zero computation (prove no
    real data read — audit hook); (b) fixture GO-typed-live + synthetic week-5 snapshot +
    sandbox ledger ⇒ FULL PASS end-to-end (24 rows nominal = 8 games × 3 arms), chain valid,
    double-run deterministic; (c) CONSUMED state ⇒ refuse; (d) DEAD state ⇒ refuse; (e)
    wrong registered phrase ⇒ refuse; (f) head mismatch (registry head ≠ worktree) ⇒ refuse
    at G2; (g) arm-file sha tamper ⇒ refuse at G2; (h) GENESIS digest mismatch ⇒ refuse at
    G2; (i) lock held (simulate via a held flock fixture on a COPY of the lock path — do NOT
    touch the real lock; if simulation is not faithful, record NOT_RUN_LOCK_SIM and test the
    gate by code-path injection) ⇒ refuse at G3; (j) snapshot sha mismatch ⇒ refuse at G4;
    (k) future-game-with-score snapshot ⇒ refuse at G4; (l) week-4 batch (incl. 2026_04_
    ATL_NO canary) ⇒ refuse at G5; (m) margin 5.99h ⇒ refuse at G6, nothing written;
    (n) arm-set tamper (4th arm injected) ⇒ refuse at G7; (o) ledger chain pre-broken ⇒
    refuse at G8.

## Task 3 — ERRATUM_R3 (lanes/FREEZE_ERRATUM_R3/ERRATUM_R3.md + freeze_digests_r3.json)
Content: (1) authority ruling — freeze law permits execution-surface additions via ERRATUM
(R2 precedent); arm code untouched (7ec4c539 stands); (2) the executor module list + sha256
pins; EXECUTOR_FREEZE_SHA = controller-measured two-step addendum (state PENDING then let the
controller append); (3) the canonical GO-recording convention (exact string
`OWNER_GO_TYPED_LIVE <utc-iso> at head <40-hex>` recorded by the controller via researchctl
cycle update the moment the owner types the phrase at the gate; any other wording refuses);
(4) gate-chain specification (G1–G8) as the auditable post-GO contract; (5) statement: GENESIS
R2 digest unchanged and binding; window/arms/grids unchanged.
Re-run ALL existing suites at your final tree (ledger 42/42, successor 16/16, PIPE selftest
10/10 + e2e-synth 3 scenarios) — must remain green.

## Deliverables
lanes/EXEC/{EXECUTOR_REPORT.md (design + gate table + fixture results matrix), VERDICT_TABLE.md};
executor + gate tests; ERRATUM_R3 files.
HANDOFF: zcode_orch_v3_handoff@1 at lanes/DISPATCH/handoff_EXEC.json (task_id
nfl-winprob-ng-scored-v1-EXEC, dispatch_sha=actual_start_sha=876845e0…, commit_sha=null).
STOP CONDITIONS: any gate unimplementable faithfully (record BLOCKED_TOOLING, do not fake);
existing suite regression.
