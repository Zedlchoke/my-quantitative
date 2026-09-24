# A7 prelaunch ILLIQ — round 4 (delta, A4b narrowed scope) — REFUSED

Cycle: CRYPTO-HISTORICAL-REPLICATION-3F-V1, family ILLIQ-AMIHUD-28D-W.
Artifact of record: `a7_prelaunch_illiq/a7_prelaunch_illiq.json` (schema `chr3f_a7_prelaunch@1`, round 4).
Lane HEAD audited: `2128cbcc` (integration worktree); root `c6f5bba8`.
Supersedes r3 (REFUSED at the launch-gated path, head `adc6e7f9`); r1 AUTHORIZED 20/20 preserved at
`a7_prelaunch_illiq_r1_SUPERSEDED.json`. Scope: amendment A4b — fold set = **Y2024P only**
(2024-01-01..2024-08-19) → 2 cells (ANCHOR `ILLIQ-AMIHUD-28D-W` + INV `ILLIQ-AMIHUD-28D-W-INV`).
Everything recomputed from bytes; nothing trusted.

## The two r3 blockers, against the narrowed scope

**r3 F1 (universe override not book-identical) — RESOLVED for this scope.** A4b drops
Y2021/Y2022/Y2023 before any of their scored cells ran, so the 6/53-stamp Y2023 divergence is out
of scope. For the one remaining fold, r3's own A/B (reproduced here from the r3 artifact bytes:
r3 md N1 and r3 JSON F2) measured books **identical at all 33/33 stamps** on Y2024P — variant B's
n_eligible grew 17→18→19 from 2024-05-20 (BOME/ENA) but never reached a tail leg. The relabel is
also truthful: commit `2128cbcc` rewrote the `universe()` comment to declare NOT-book-identical,
the Y2023 6/53 divergence, and the A4 outcome-exposed status (comment-only diff, no behavior change).

**r3 F2 (terminal-valuation wall) — RESOLVED.** The cell runner now loads bars 3 days past the
window end (`timedelta(days=3)`); `read_bars_15m` reads only the staged catalog parquet
(`hyp_a8_m01.py:337-365`) — no S1, no gateway, no new fetch; the extension reads more rows from the
same already-staged public month zips. Covering bars verified from the parquet for BTCUSDT /
1000PEPEUSDT / SUIUSDT: 288 bars each in (2024-08-19T00:00Z, 2024-08-22T00:00Z), first = the
2024-08-19T00:00Z mark bar. The DIAG run proves completion end-to-end.

## DIAG Y2024P-ANCHOR-A4 — through the wall, correctly booked not-scored

`illiq_diag/Y2024P-ANCHOR-A4/` exists; metrics match the dispatch exactly (net_return_sum
**0.137736325744**, position_pf **1.099712620819**, max_drawdown **0.205030513488**,
n_positions **216**). 33/33 stamps (F1=10, F2=11, F3=12), n_boundaries=33 with the terminal row at
exactly 1724025600000000000 = 2024-08-19T00:00Z (FORCE_FLAT, fill applied, cost charged) — the
instant that aborted r3. No `DataUnavailable` anywhere. `scored: false` is hardcoded by the frozen
runner (`adapter_v10/runner.py:220`); no status row, no denominator entry. Outcome exposure is
disclosed (A4 umbrella sentence + A4b commit message carries the four metrics).

## Verified clean

- Engine frozen: all 8 files (`illiq_amihud/{__init__,audits,plugin,strategy}.py`,
  `adapter_v10/{runner,benchmarks,base,protocol}.py`) byte-identical to `c97283e0`.
- Census Y2024P 30/33 OK (33 stamps, 3 engine-authored skips) — non-vacuous; engine handles skips
  (DIAG `skipped_boundaries=3`, consistent); all 3 window folds populated.
- Launcher: FOLDS = Y2024P only, self-gates on this artifact's path (rc=5 unless AUTHORIZED);
  resume logic intact. Status file: 13 rows, all rc=1 null-metric (failed-sweep family, incl. the
  2 Y2024P rows); **0 scored ILLIQ cells**.
- Budget: 8 XSECT scored + 2 ILLIQ pending = 10 ≤ 24.
- Boundaries: delta commit touches only 3 cycle files; no S1; no credentials; gateway/shadow
  worktree writes are those cycles' own runtime outputs; outputs cycle-local; funding B bundle ends
  exactly at the declared 2024-08-20T00:00Z boundary. Heavy-lock stale row (pid 71445 dead, flock
  free) carried from r3 N3.

## Blocking finding B1 — the amendment labels are not stamped anywhere in code

The dispatched invariant requires four labels on every cell row: EQUIVALENCE_DATA_RESTAGE_UNPROVEN +
REPLICATION_NOT_PROSPECTIVE + UNIVERSE_LISTED_AT_WINDOW_START + OUTCOME_EXPOSED_AMENDMENT_A4.
Bytes say otherwise. The launcher row builder (`illiq_scored.py` lines 61-71) stamps only
`namespace: REPLICATION_NOT_PROSPECTIVE` and `label: EQUIVALENCE_DATA_RESTAGE_UNPROVEN`; all 13
existing status rows carry exactly those two. A repo-wide search finds
`UNIVERSE_LISTED_AT_WINDOW_START` and `OUTCOME_EXPOSED_AMENDMENT_A4` in exactly one file — the
amendment markdown itself — and in no code, no status row, no cell artifact (the DIAG payload
carries neither). A4b asserts the labels "remain" on cells; they were never stamped.

Consequence: authorizing as-is would open the gate and immediately write scored authority rows that
violate A4's own mandate ("Every ILLIQ cell therefore carries … OUTCOME_EXPOSED_AMENDMENT_A4 … can
never be presented as preregistered evidence"), and retrofitting labels after the sweep would mean
mutating an authority surface post-hoc. Same disclosure-integrity failure class as r3 F1, now on
the labeling surface.

Remediation is minimal: stamp all four labels in the `illiq_scored.py` row dict (and optionally the
runner payload identity), fix the stale "8 cells" docstring, commit, return for r5. No engine,
catalog, or funding surface is affected — all other evidence in this round remains valid for r5.

## Non-blocking (carried/noted)

N1 stale "8 cells" launcher docstring (code is authoritative: 2 cells); N2 heavy-lock registry
stale row (reclaim per round-2 discipline); N3 the new Y2024P DIAG should be named explicitly
alongside the Y2021 DIAG in the post-sweep narrative; N4 frozen identity window strings /
1e-07 tick table / funding boundary row still travel with every report line; N5 dead
`or s == self._benchmark` clause in `universe()`.

## Verdict

**REFUSED.** The launch gate stays rc=5. Single blocker B1 (label stamping absent from the sweep
surface). r3's F1 and F2 are resolved for the A4b-narrowed scope and the Y2024P DIAG is honest,
complete, and correctly non-scored — but the gate cannot open onto a sweep that would emit cell
rows violating the amendment's disclosure labels.
