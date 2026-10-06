# ERRATUM_R1 — WNBA-PLAYERFEAT-SCORED-V1 · execution-surface addition (REAL OOS runner)

Date of record: 2026-10-06 · lane EXEC · dispatch
`lanes/DISPATCH/DISPATCH_EXEC.md` (dispatch_sha = actual_start_sha =
`3bbd2b79190a162d1386f65e2a9c8ffb91d6c455`) · branch
`orca/wnba-playerfeat-scored-v1-integration` · interpreter
`/Users/hoangminhlong/my-quantitative/.venv/bin/python` · no git write commands · $0.

## 1. Authority ruling

This ERRATUM records an **execution-surface addition only**. The pre-GO freeze left the
real OOS execution lane deliberately unbuilt ("real-data OOS execution lives POST-GO" —
T_SELECT harness; S_SYNTH DRYRUN_REPORT §3 token law item 5). DISPATCH_EXEC (owner-round
authority) instructs lane EXEC to complete that lane so it executes **only post-GO**.

- **Arm code is untouched.** The engine and arm definitions remain exactly
  `lanes/T_SELECT/arms.py` (sha256 pinned in §2) and `lanes/T_SELECT/harness.py` (pinned);
  both files are UNMODIFIED (byte-verified). The runner imports the frozen engine as-is
  and adds no arm code, no arm parameter, and no third arm.
- **Window, arms and metrics are unchanged.** OOS = [2020..2026] (§5), the 2 frozen arms
  B0 (constant p = 0.603755) + B1-WNBA (K=32, HCA=50, γ=0.65), and the frozen metric stack
  (LL primary; Brier; 10-bin reliability; calibration slope band [0.85,1.15]; paired dLL
  with tip-date-cluster bootstrap 10,000 resamples seed 20261005; frozen falsifier,
  packet §3 REJECT-vs-B0 rule) are exactly the registered freeze.
- **Pre-GO behavior is unchanged in law:** with the REAL registry as-is
  (`go_phrase_state=REGISTERED_NOT_CONSUMED`), the runner refuses at G1 BEFORE any data
  read (audit-hook-proven, fixture (a)); the pass-path proof uses synthetic seasons only.
  Nothing on real 2019+ data was computed in this round.

## 2. Runner sha pins (this ERRATUM freezes the execution surface)

| artifact | sha256 |
|---|---|
| `research/control/WNBA-PLAYERFEAT-SCORED-V1/runner/run_oos.py` | `1bfc951a08182dfa9e549764e1b05c4c84cf129f5e3db56b934ac3fdbb14cd2e` |
| `lanes/EXEC/exec_fixture_builder.py` | `cd505c6b15e9b8f16ea3c74ee57b8b90fec449f132603424b941cf7c19b9e1c3` |
| `lanes/EXEC/test_runner_gates.py` | `b92ce6d6c445f6d4cbadb7c95a28da57b99f232ea476f919d739bde2aa65f5d1` |
| `lanes/T_SELECT/arms.py` (frozen, unchanged — G2 pin) | `82263eab713258b09ef920500a56d1fbf36ef9b9b8ea20965c6b4fd99b04cdd3` |
| `lanes/T_SELECT/harness.py` (frozen, unchanged — G2 pin) | `b9446f7699ce2e29c8ce66490fc0f9941cc38dda0ed02e8e7fc108e65373485e` |
| frozen feature table (2002–2026 parquet) | `ceaf10ba33e705b9569a11cec2aa33e1875e372c35d643ed5d80d5e757ffc7bf` (826,415 B) |

**RUNNER_FREEZE_SHA = `PENDING_CONTROLLER_ADDENDUM`** — two-step convention: the lane
pins the per-file digests above; the controller's addendum sets RUNNER_FREEZE_SHA to the
sha256 of `run_oos.py` (or a digest list) at its own freeze step, after which any drift is
a G2 refusal. Until that addendum, G2 pins the per-file digests above (already enforced).

## 3. Canonical GO-recording convention (identical law to the NFL ERRATUM_R3 convention)

When the owner types the registered phrase **`GO WNBA PLAYERFEAT SCORED V1 EVALUATION`**
verbatim at this cycle's own gate, the controller records in the registry row:

```
go_phrase_state = OWNER_GO_TYPED_LIVE <utc-iso> at head <40-hex>
```

- `<utc-iso>` = the instant of the owner's typing, format `YYYY-MM-DDTHH:MM:SSZ`.
- `<40-hex>` = the worktree HEAD sha at the moment of typing (lowercase hex).
- Example: `OWNER_GO_TYPED_LIVE 2026-10-06T09:00:00Z at head 3bbd2b79190a162d1386f65e2a9c8ffb91d6c455`.
- G1 accepts exactly this canonical form (anchored regex) plus `lifecycle ACTIVE_*` plus
  registered-phrase equality plus GO-head==row-head coherence. Every other state
  (REGISTERED_NOT_CONSUMED, CONSUMED, DEAD, NOT_REGISTERED, prose) refuses.
- The phrase itself is never consumed by the runner; the runner reads only the recorded
  state. Recording the state is the CONTROLLER's write; the runner never writes the
  registry.

## 4. Gate-chain spec (G1–G5; each audited; distinct exit codes; nothing computed on refusal)

| gate | law | pass requires | refusal exit code |
|---|---|---|---|
| G1 AUTHORITY | registry row `WNBA-PLAYERFEAT-SCORED-V1`; `lifecycle` startswith `ACTIVE`; `go_phrase` == `GO WNBA PLAYERFEAT SCORED V1 EVALUATION` (exact); `go_phrase_state` matches `^OWNER_GO_TYPED_LIVE \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z at head [0-9a-f]{40}$`; GO-state head == row head | all of the above; fires BEFORE any data read and before any code-file hash | 2 |
| G2 FREEZE COHERENCE | worktree `git rev-parse HEAD` == registry head; `arms.py` sha == `82263eab…`; `harness.py` sha == `b9446f76…`; B1 constants in code == law literals (32.0, 50.0, 0.65) asserted INSIDE the gate; B0 == 0.603755 asserted INSIDE the gate; arm set == exactly `B0,B1-WNBA` (no φ-arming acceptance path; `arm_feature_phi()` refuses unconditionally) | all of the above | 3 |
| G3 LOCK | `researchctl locks inspect` == `FREE_PROVEN`, 3×60s retry | FREE_PROVEN | 4 |
| G4 WINDOW | seasons argument law: real == (2020..2026) exactly, synth >= 2027 and == manifest; every scored-window game `tip_utc < run time`; corpus census == frozen counts (real: 2020→147 … 2026→341, warm-up 1022, universe 5,988; synth: manifest census); schedule/feature-table id sets identical; any missing season/game ⇒ refuse (no silent shrink) | all of the above | 5 |
| G5 SINGLE BATCH | one process computed both frozen arms on the identical game list; exact-arm record ids pairwise distinct; non-vacuous (≥1 row/arm; per-season counts == census) | all of the above | 6 |

Other exits: 0 = ALL-PASS (results written), 1 = usage, 70 = unexpected TECHABORT.
On ALL-PASS with `--source real`: warm-up 1997–2001 + stream 2002–2019 feed the frozen
rating stream; OOS 2020–2026 is predicted with the 2 arms; results JSON + markdown +
per-arm prediction CSVs are written to `--out`. The real-path loaders are reachable only
after G1+G2+G3 pass and the G4 window law holds.

## 5. WINDOW_RESOLUTION binding

`lanes/EXEC/WINDOW_RESOLUTION.md` is **binding** for this cycle: raw-bytes re-verification
CONFIRMED the controller's pre-measurement (2026 = 341 universe games, tips
2026-05-08T23:30Z → 2026-10-03T01:00Z, zero future-tipped universe games at every freeze
anchor; raw `post` minus Postponed minus All-Star == 341 == feature table exactly; the 15
future-dated raw rows are `pre` TBD placeholders that the frozen universe law excludes).
**OOS = [2020, 2021, 2022, 2023, 2024, 2025, 2026]** — windows, arms and metrics
unchanged from the registered freeze. The runner re-asserts at run time that every OOS
game is in the past (G4); a still-future game refuses as a stale corpus.

## 6. Falsifier language (frozen, applied verbatim by the runner)

REJECT-vs-B0 **iff** the pooled 95% paired tip-date-cluster-bootstrap CI of
ΔLL = LL(B1-WNBA) − LL(B0) includes 0, **OR** ≥ half of the season folds are non-negative
(7 OOS folds ⇒ threshold 4 = (7+1)//2; recorded per run with the actual fold count).
Effects smaller than ~0.003 ΔLL are INCONCLUSIVE at this capacity — stated, not stretched.
Calibration-slope band [0.85, 1.15] is the frozen diagnostic; B0's slope is the honest nan
(constant predictor).
