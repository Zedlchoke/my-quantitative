# STOCKS-FREE-V4 — A7-T Terminal Audit Report

- **Producer role:** A7-T (independent terminal auditor; audits only, never repairs)
- **Cycle:** STOCKS_FREE_V4
- **Recorded (UTC):** 2026-09-04T05:20:00Z
- **Lane:** `/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v4/q-a7-prelaunch` (branch `orca/stocks-free-v4-q-a7-prelaunch`, at `d2b5069` when the audit started)
- **Subject under audit:** terminal integration branch `orca/stocks-free-v4-integration` at `42b7a73c01dac25924fcb32c59f7db00d8c89375` ("V4 terminal: STOCKS_FREE_V4_REJECT_ALL …")
- **Machine-readable twin:** `research/control/stocks_free_v4_run/r_a7_terminal_audit.json` (schema `stocks_free_v4_run/a7_terminal_audit@1`)

## VERDICT

**STOCKS_FREE_V4_REJECT_ALL_CONFIRMED** — unresolved HIGH/CRITICAL findings: **0**.

Every link of A1's terminal chain was recomputed by measurement, not taken from self-claims. All seven audit sections PASS with zero findings. The terminal verdict **STOCKS_FREE_V4_REJECT_ALL** (both preregistered families fail Stage A; zero survivors; nothing promotable; S1 sealed) is confirmed.

## Section results (all measured)

### 1. Ledger once-only — PASS (severity NONE)
`execution_ledger.json`: `observed=6`, `published=6`, 6 published keys. Per key exactly **1** FIRST_PUBLICATION, **1** REPLAY_ZERO_DELTA, **1** COMPUTE_RECORDED, **1** artifact-digest entry; total COMPUTE_RECORDED = 6 = observed. Once-only discipline holds.

### 2. Artifact-byte digests — PASS (severity NONE)
For all six cell files, sha256 of exact file bytes and of canonical bytes (`json.dumps(artifact, sort_keys=True, separators=(',',':'))`) were recomputed. All 6 file digests match `terminal_report.json scored_cells.file_sha256`; all 6 canonical digests match `scored_cells.canonical_sha256` **and** the ledger `artifact_digest` per key. All 12 digests pairwise unique; 6 canonical digests pairwise unique. Integration-tree cells are byte-identical to exec-tree (`e-exec-1`) cells.

### 3. Cell math spot-check — PASS (severity NONE)
Arms `SFV4-A4-H1-A` and `SFV4-A5-H1-A`:

| Check | A4-H1-A | A5-H1-A |
|---|---|---|
| equity_curve len == n_sessions | 3918 == 3918 | 3918 == 3918 |
| len(period_pnls) == n_periods_base | 50 == 50 | 33 == 33 |
| expectancy == Σpnl/n (≤1e-12) | delta 0.0 | delta 0.0 |
| Σ fold n_periods == n_periods_base | 15+17+18 = 50 | 11+11+11 = 33 |
| gates vs arm_gates_all_pass | 13/15 FAIL ↔ false | 13/15 FAIL ↔ false |
| last_session | 2025-07-31 | 2025-07-31 |
| max eq / max pnl date | 2025-07-31 / 2025-07-24 | 2025-07-31 / 2025-07-24 |

S1 seal respected: no session date ≥ 2025-08-01 anywhere in either artifact.

### 4. Family verdicts + denominator — PASS (severity NONE)
Both families **STOCKS_FREE_V4_FAMILY_REJECT** in `family_verdicts.json` and `terminal_report.json`. Every quoted headline number was recomputed from the six cell files and matches:

- A5 anchor: pnl −17.62%, PF 0.606, α −0.791, 1/3 folds+, MDD 18.5%, stress −20.6%, 13/15 gates FAIL — all match.
- A5 neighbour: −4.53%, PF 0.967, α −0.662 — match. A5 control (stale ranks): +14.91%, PF 1.668, α −0.470 (all folds negative) — control outperformed anchor; falsification rule fires, as claimed.
- A4 anchor: pnl −28.08%, PF 0.702, α −0.487, 0/3 folds+, MDD 32.1%, stress −31.6%, 13/15 gates FAIL — all match.
- A4 neighbour: −16.27%, PF 0.905, α −0.332 — match. A4 control (vol LEVEL): +53.14%, PF 2.582, α +0.189 (2/3 folds), MDD 34.1% — control outperformed anchor; falsification fires, as claimed.
- Budget 6/6; V4 observed/published 6/6; prior historical 12/12 carried unchanged; denominator 18 = 12 + 6.

### 5. Reproduction — PASS (severity NONE)
`r-reproduce` is detached at `dfa099a` (= W1). Independent re-verification of **all six arms**: loaded exec-tree (`e-exec-1`) and repro-tree artifacts, normalized **only** `run_utc` and `pins.{git_head, staging_manifest_sha256}` (repro artifacts record empty `pins: {}`), compared canonical JSON strings:

| Arm | Result |
|---|---|
| SFV4-A4-H1-A | EXACT_MATCH |
| SFV4-A4-H1-C | EXACT_MATCH |
| SFV4-A4-H1-N | EXACT_MATCH |
| SFV4-A5-H1-A | EXACT_MATCH |
| SFV4-A5-H1-C | EXACT_MATCH |
| SFV4-A5-H1-N | EXACT_MATCH |

**6/6 EXACT_MATCH** — confirms A1's reproduction claim. Repro `run_utc` differs from exec (04:56:45Z vs 04:51:29Z), consistent with a genuine fresh-process rerun; both twins record canonical driver pin `918d02e7…`.

### 6. Safety — PASS (severity NONE)
- Workers: `ps aux | grep -iE "pytest|backtest|scoring" | grep -v grep` → zero processes; state/heartbeat report 0.
- No push: `git branch -vv` shows no upstream/tracking ref on any V4 branch.
- Main untouched: `git merge-base --is-ancestor orca/stocks-free-v4-integration main` **fails** (exit 1) — V4 not merged; main has advanced independently (owner work).
- S1: `SEALED_UNTOUCHED` present in `state.json` and `terminal_report.json`.
- No file under `research/control/stocks_free_v4_run/` claims `"scored": true` or `"real_pnl": true` (grep: zero hits anywhere, including the six cells — stricter than the boundary).
- All six cell artifacts: max session date 2025-07-31 < 2025-08-01.
- Deployment: NO_PAPER_NO_LIVE_NO_ORDERS.

### 7. Boundaries — PASS (severity NONE)
- Worktrees: 13 `stocks-free-v4` worktrees present; every V4 lane recorded in `worktree_manifest.json` exists; no deletions. (Planned lane `r-a7-terminal` was never created — immaterial, no count reduction.)
- Staged data MANIFEST: `sha256(.staging/MANIFEST.json)` = `62ac324d7e683961b0d88f85153e4a072d09fe0a6745a54687b9e3b219d8f658` in **both** twins (e-exec-1 and r-reproduce), byte-recomputed; exec artifact pins echo the same value.

## Informational observations (no severity, no action)

1. `total_pnl` is the geometric equity-curve return (end/start − 1, exact), while `period_pnls`/`fold_pnl` follow an arithmetic per-period PnL convention (`fold_pnl == fold_expectancy × n`, exact; `fold_return ==` equity return over the fold window, exact). The two measures are internally consistent under their own definitions; no verdict depends on the distinction since all six cells fail `arm_gates_all_pass`.
2. Repro-twin artifacts record `pins: {}`; the mandated normalization covers exactly those fields, so the comparison is strict on all remaining bytes.
3. `worktree_manifest.planned_lanes` includes `r-a7-terminal`, never materialized.

## Findings summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 0 |

**Unresolved HIGH/CRITICAL: 0 → VERDICT: STOCKS_FREE_V4_REJECT_ALL_CONFIRMED**

## Commits in this lane

1. `V4 A7T: terminal audit` — adds this report and `r_a7_terminal_audit.json` (HEAD `b61fa817842a83d8ac528e809aad3ffcb75892de`)
2. `V4 A7T: audit head pin` — pins the audit commit sha into the JSON (`audit_head_pin`)
