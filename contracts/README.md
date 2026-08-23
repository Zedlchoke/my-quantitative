# Sprint 24h contracts — owner A1

Thư mục này là **interface freeze** cho sprint (PLAN.md §12 H0–H2). A2/A3/A4
import `contracts/protocol.py`; KHÔNG định nghĩa lại schema/reason codes/
scorecard/budget ở nơi khác.

## Đã khóa (H0)

1. **Manifest schema** — `ManifestSpec` (đúng 29 trường theo PLAN §8; validate()
   trả reasons machine-readable).
2. **Candidate/hypothesis schema** — `HypothesisSpec` + `HypothesisState`
   (state machine PLAN §6).
3. **Canonical metric fields** — `CanonicalMetrics` với `MetricValue`
   (null + reason code bắt buộc; CẤM default 0.0).
4. **Hard-gate reason codes** — `REASON_CODES` (G0→G5 + pipeline/cells);
   mọi reason xuất hiện trong artifact phải thuộc enum này.
5. **Scorecard fields** — `SCORECARD_COMPONENTS` (tổng 100) +
   `scorecard_max_verdict()` bands theo PLAN §11.
6. **Matrix cell result schema** — `MatrixCellResult` + `CellStatus`.
7. **Ownership** — theo PLAN §5; bổ sung: thư mục `contracts/` chỉ A1 sửa.
8. **Merge/dependency order** — theo PLAN §5.
9. **Trial/resource budget** — `MAX_HYPOTHESES=3`,
   `MAX_NEW_STRATEGIES=2`, `MAX_PARAM_COMBOS_PER_HYPOTHESIS=16`,
   `MAX_LOOP_ITERATIONS=2`; workers matrix ≤2 (máy 2 core).
10. **Artifacts bàn giao** — theo PLAN §13; verdicts hợp lệ `SprintVerdict`;
    cấm `FORBIDDEN_VERDICTS`.

## Baseline H0 (bằng chứng)

- git main @ `37ecda5`, clean trừ 1 deletion user giữ nguyên:
  `research/wayfinder/TWO_AGENT_5_DAY_RESEARCH_PLAN.md` (không reset/commit).
- `.venv/bin/python -m pytest tests/ -q` → **54 passed** (Python 3.12.14,
  nautilus_trader 1.230.0, pytest 9.1.1).
- Worktrees: `wt/data-matrix`, `wt/validation-protocol`, `wt/research-loop`
  (mới, branch từ commit contracts); worktree cũ `wt/data-pipeline`,
  `wt/quality-safety`, `wt/research-analysis`, `wt/ops-reporting` giữ làm input
  lịch sử, không merge tự do.

## Known limitations ghi nhận tại H0

- Engine không hỗ trợ two-tick slippage / delayed-fill → G4 một phần sẽ là
  `NOT_IMPLEMENTED`.
- Chưa có BTC-beta-neutral implementation → context benchmark này
  `NOT_IMPLEMENTED` trong sprint.
- Common intersection đa mã thực tế = cửa sổ S0 1 năm (35,038 bars,
  2025-08-21 → 2026-08-21) — mọi khai báo "2 năm" per-symbol không được dùng
  làm sample đa mã.
