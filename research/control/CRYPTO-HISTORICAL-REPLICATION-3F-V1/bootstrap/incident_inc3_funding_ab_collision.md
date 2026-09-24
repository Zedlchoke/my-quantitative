# INC-3 — A/B funding staging collision (found 2026-09-24 ~00:45Z)

Symptom: ILLIQ equivalence run produced funding_sum = 0.0 (vs nonzero in the
A7 baseline) plus structural deltas (328 vs 336 positions, hit 23/52 vs
24/52, PF 1.379 vs 1.355, MDD 0.104 vs 0.092). Equivalence gate FAILED ->
STOP per plan §5 -> root-cause before anything else.

Root cause (measured): staging/funding/<SYM>_funding.json was written by BOTH
the A-window job (2024-08-20..2026-08-22) and the B-window job (2020-07-01..
2024-08-20) under the SAME path; the B job ran later and overwrote A. The
scan_2026 conversion then consumed the B-window bytes for every symbol
(ETHUSDT: 4,534 settlements from 2020-07-18 = exactly the B window; A7 r2
independently measured requested_start_ms=1593561600000).

Impact assessment:
- XSECT scored cells (8, already reported): UNAFFECTED — their folds
  (Y2020P/Y2021/Y2022/Y2023) lie entirely inside the B window that was on
  disk; A7 r2 verified those exact bytes. Results stand.
- ILLIQ equivalence: INVALID as run (no settlements in its 2025-26 spans ->
  zero funding booked). Root-caused; remediation = separate roots per window.
- ILLIQ replication folds (Y2021/22/23/Y2020P) will consume the B-window root
  (correct); the A-window refetch feeds the equivalence run only.
- BASISLV: unaffected (basis is a separate surface; funding B window correct
  for its folds once restaged).

Remediation: fetch_funding_a.py re-fetches the A window into a SEPARATE root
funding_data_scan/scan_2026_a (B stays in scan_2026); ILLIQ equivalence
driver repointed to scan_2026_a. Layout law added: one window = one root.

## INC-4 (2026-09-24 04:3xZ): SIGTERM kill of basis runner left stale heavy-lock row
To let the ILLIQ-REG-V1 gate-series build use the machine-wide lock, the
running CHR3F B_basis sweep was stopped with pkill (SIGTERM) instead of a
clean-stop path — the stage runner has no SIGTERM handler, so the registry row
stayed RUNNING with a dead pid -> locks inspect = CONTROL_STATE_DRIFT. The
heavy_lock.acquire proven-stale reclaim path is expected to clear it. The
interrupted B_basis item restages cleanly (idempotent .done design; partial
fetch leaves no artifact). Disclosed; watcher resumed after the gate build.
