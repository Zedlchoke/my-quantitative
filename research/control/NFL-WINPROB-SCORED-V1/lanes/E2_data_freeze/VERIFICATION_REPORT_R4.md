# VERIFICATION_REPORT_R4 — NFL-WINPROB-SCORED-V1 (E2, round 4, post-AMENDMENT_1)

- verifier: independent, fresh context; prior round-1/round-4-prior verdicts
  carry no authority — every item below re-measured from bytes on 2026-10-04.
- scope evaluated: the CURRENT package only (freeze v2). The prior A7
  (AUTHORIZED, 4 LOW) is superseded by the AMENDMENT_1 remediation.
- worktree HEAD measured: `18412f4876804c07a25b9ddeb3fefdb1062cc992`
  (branch `orca/nfl-winprob-scored-v1-integration`, `git status --porcelain`
  empty — clean tree)
- code freeze v2: `91dcff14bf66d5ba5a0fb2322be10ee1b08d26ad`
  (`code_freeze_sha` in `FREEZE_MANIFEST.json` v2)
- supersedes v1: `8cd0e1bcf9c9d45f5e10ae1b73b93eee7560a7b7` (manifest renamed
  `FREEZE_MANIFEST.SUPERSEDED_BLOCKED.json`, byte-identical rename verified —
  commit `27dbc1d8` shows `0` content delta — plus `SUPERSEDED_NOTE.md`)

# VERDICT: VERIFICATION_PASS (7/7)

0 HIGH, 0 CRITICAL, 3 LOW (LOW-1 is the A7 conditional-pin action; LOW-2/LOW-3
recorded-not-normalized). The AMENDMENT_1 remediation (ledger schema + drift
prefix + 2 tests) is verified fixed; the freeze v2 chain is coherent; the
pre-launch accounting is exact; nothing real has been computed.

## V1 Freeze chain, diff scope, and code-freeze coverage — PASS

- `git diff --name-status 91dcff14..HEAD` = exactly one path:
  `A research/control/NFL-WINPROB-SCORED-V1/FREEZE_MANIFEST.json` (199
  insertions) — inside `post_freeze_allowlist`
  (`research/control/NFL-WINPROB-SCORED-V1/**`). Manifest-only, as allowlisted.
- `git diff 91dcff14..HEAD -- nfl_winprob/` is EMPTY: the package is
  byte-unchanged since the code-freeze commit.
- `code_freeze_sha` covers BOTH current code files (blob ids quoted):
  - `nfl_winprob/run_evaluation.py` → blob
    `1fe355b7d4c6463bd19f2d34358dfb8c3a6b830a` at HEAD == at `91dcff14` ==
    at `649557b7` (AMENDMENT_1)
  - `nfl_winprob/make_freeze_manifest.py` → blob
    `8e5ebb9e14b877f245594aed9fe14e8875a4b6b0` at HEAD == at `91dcff14`
  - `91dcff14` (generator prep) changed ONLY `make_freeze_manifest.py`
    (+3 lines) and PREDATES the manifest commit `18412f48` — generator
    committed before manifest generation (the C1 lesson honored).
- Full remediation chain scope, each verified by `git show --stat`:
  - `649557b7` AMENDMENT_1 = `run_evaluation.py` (+21/−6), `tests` (+36),
    `AMENDMENT_1.md` (+23). No ledger, no data.
  - `27dbc1d8` = pure rename `FREEZE_MANIFEST.json` →
    `FREEZE_MANIFEST.SUPERSEDED_BLOCKED.json` (0 delta) + `SUPERSEDED_NOTE.md`.
  - `91dcff14` = generator only. `18412f48` = manifest only.
  - Cumulative `2986de8c..HEAD` touches only `nfl_winprob/` and the cycle
    control dir; `TRIAL_LEDGER.jsonl` untouched by the whole chain.

## V2 AMENDMENT_1 fix (a): ledger schema — PASS (re-measured by execution)

Verifier's own python (not the test suite):

- Source sweep: `nba_winprob_trial_ledger` occurs **0** times in the
  `run_evaluation` module source.
- Execution: `append_trial_rows` into a temp-dir ledger, PRIMARY pass then
  `repro=True` pass → 4 appended rows, schemas == `{nfl_winprob_trial_ledger@1}`
  only, classes == `{PRIMARY, REPRO}`.
- Ledger on disk: exactly 9 rows, every row
  `schema=nfl_winprob_trial_ledger@1`, `status=PREREGISTERED`,
  `observed=false`, **0 COMPUTED**, arm_ids
  B0/B1-a/B1-b/B1-c/B1-d/B2-a/B2-b/B2-c/B2-d.
- Companion test `test_ledger_schema_consistency_amendment1` asserts 18 rows
  (9 PRIMARY + 9 REPRO) all NFL-schema + no NBA-schema string in source —
  present and passing.

## V3 AMENDMENT_1 fix (b): drift helper — PASS (re-measured by execution)

`from nfl_winprob.run_evaluation import _code_drift_reasons`:

- Positive: `nfl_winprob/x.py` → flagged with reason
  `CODE DRIFT (nfl_winprob/ immutable): ['nfl_winprob/x.py']` (plus the
  outside-allowlist reason — correct dual semantics; my first assertion
  expected one reason and was corrected: two reasons is the intended output).
- Negative: `research/control/NFL-WINPROB-SCORED-V1/FREEZE_MANIFEST.json`
  against the manifest allowlist → `[]` (not flagged).
- The dead NBA prefix is no longer special: `nba_winprob/whatever.py` yields
  only the allowlist reason, never the immutable-prefix reason.
- Companion test `test_code_drift_helper_positive_negative` present and passing.

## V4 Tests, selftest, refusal paths — PASS

- `pytest nfl_winprob/tests -q` → **25 passed** in 20.91s (round 1: 23;
  +2 = the two AMENDMENT_1 tests, both collected and PASSED by name).
- `--synthetic-selftest` → `SELFTEST PASS: 9 arms, 11 comparisons
  (pooled+per-fold), verdicts emitted, fold reliability/slope present,
  bootstrap deterministic; no real data touched.` exit 0. (Its trailing
  `PROGRAM_PASS:false / REJECT:true` JSON is the verdict struct on random
  synthetic data — mechanics-only, expected, carried from round 1 L4.)
- `nfl_winprob/evaluate.py` stub → exit **3** (REFUSED: budget 0 scored cells,
  owner directive explicitly NOT a typed GO).
- Scored runner with a nonexistent GO record → exit **3** with named reason
  (`no GO record: '/tmp/nonexistent_go.json' …`).

## V5 Data hashes + attribution — PASS (all recomputed from bytes)

| input | sha256 (first 16) | manifest | match |
|---|---|---|---|
| raw `games.csv` | `f1e8fe781400c128` | `f1e8fe78…248e` | MATCH |
| derived `games_nfl.csv` | `f7909fa514dccdcb` | `f7909fa5…1565` | MATCH |
| derived `lineages_nfl.csv` | `977a43e22649e833` | `977a43e2…aff0` | MATCH |
| derived `features_nfl.csv` | `4ee2175eb549fda2` | `4ee2175e…98982` | MATCH |
| raw `ATTRIBUTION.md` | `b18529758d62284a` | `b1852975…aedc` | MATCH |

`pinned_features` hash equals the manifest `features` entry and is
**unchanged at `4ee2175e…`** — the remediation touched neither raw nor
derived features (raw untouched since pull; features byte-identical to the
round-1/round-2 verified value). Protocol digest `5b035a1c…` recomputed from
`lanes/NFL_C_protocol/PROTOCOL_EVAL_NFL.md` and matches the manifest.

## V6 Hygiene: no real-outcome metric, no GO, budget 0/9 — PASS

- Metric-token sweep over `nfl_winprob/*.py`: the only odds/spread/moneyline
  hits are `QUARANTINED_COLUMNS` definitions in `build_dataset.py` (the
  no-metric control itself) and ledger/bookkeeping mechanics; no PnL/profit/
  edge/betting computation anywhere; runner output field is
  `language_law: "calibration language only; no PnL/betting/edge vocabulary"`.
- `results/` directory: **0 files**. Ledger: **0 COMPUTED**.
- No GO record exists for NFL-WINPROB-SCORED-V1 anywhere (searched the
  control tree; the `GO_RECORDED*` files found belong to other cycles:
  DAYTRADE/DAILY-EXPLORATORY/BTC-COMBO6/DAYTRADER-100/EVENT-MECHANISMS/
  ECONOMIC-ROBUSTNESS/PORTFOLIO-COMPOSITE — none in this cycle's dir).
- `plans/CYCLE_REGISTRY.json` (repo root): NFL-WINPROB-SCORED-V1
  `budget used 0 / max 9`, `go_phrase_state REGISTERED_NOT_CONSUMED`,
  `s1 SEALED_UNTOUCHED`.
- Heavy lock: `researchctl.py locks inspect` → `FREE_PROVEN`
  (launch-gate condition currently satisfiable).

## Findings

- **LOW-1 (stale A7 pin — the A7 conditional action)** Manifest
  `a7_report_path` still names `audits/AUDIT_PRELAUNCH.md` (round 1). That
  file carries the required `A7_PRELAUNCH_AUTHORIZED` token, so the launch
  gate would mechanically pass — but the token certifies superseded HEAD
  `2ddef086` / freeze `8cd0e1bc` and describes the now-FIXED LOW-1/LOW-2 as
  open. Required manifest-only action (allowlisted path, NBA precedent:
  NBA pin moved to `AUDIT_PRELAUNCH_ROUND3.md`): repoint
  `a7_report_path` → `audits/AUDIT_PRELAUNCH_R4.md`. Detailed in
  `audits/AUDIT_PRELAUNCH_R4.md` (A7_PRELAUNCH_AUTHORIZED_CONDITIONAL_ON_PIN).
- **LOW-2** Registry `head` for this cycle is stale at `2986de8c…` vs measured
  `18412f48…` (last registry write 14:11:00Z precedes the four remediation
  commits). Recorded-not-normalized; registry writes are outside
  verifier/auditor lanes; controller updates at landing (same disposition as
  round-1 LOW-3).
- **LOW-3** Generator divergence: `make_freeze_manifest.py` still hardcodes
  `a7_report_path` → `audits/AUDIT_PRELAUNCH.md` (line 54); if re-run
  post-pin-move it would regenerate the stale pin. The manifest is the
  operative authority consumed by the launch gate, so this is latent, not
  active; the NBA twin has the identical divergence (generator ROUND2 vs
  manifest ROUND3). Owner's call whether to fold the generator into the
  pin-move commit or leave it recorded.

## Verifier posture

Verifier never repairs; writes confined to this lane directory
(`VERIFICATION_REPORT_R4.md`, `handoff_E2r4.json`). Launch remains two-key
gated: A7 artifact (R4 + pin move) + owner structured GO record typed at this
cycle's own gate.
