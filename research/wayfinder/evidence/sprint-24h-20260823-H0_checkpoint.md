# Sprint 24h — H0 Checkpoint Report (A1)

Thời điểm: ngay sau contract freeze. Đây là bằng chứng "Gate H2" của PLAN §12.

## Baseline workspace

- `git status` lúc H0: `M PLAN.md` (plan mới của user → đã commit riêng
  `37ecda5`, giữ nguyên nội dung), `D research/wayfinder/TWO_AGENT_5_DAY_RESEARCH_PLAN.md`
  (**deletion của user — không reset, không revert, chờ user quyết định**).
- main @ `f57ad34` sau khi thêm contracts.

## Baseline tests

```
.venv/bin/python -m pytest tests/ -q
→ 54 passed (trước contracts)
→ 67 passed (sau contracts: +13 test_protocol_contracts.py)
Python 3.12.14 · nautilus_trader 1.230.0 · pytest 9.1.1
```

## Agent ownership (không overlap)

| Vùng | Owner |
|---|---|
| `contracts/`, `PLAN.md`, integration docs, merge, verdict cuối | A1 |
| `data/` additions, coverage audit, `research/matrix_runner.py`, matrix artifacts | A2 |
| `research/protocol/` (manifest/registry/metrics/gates/scorecard), validation tests, LIVE-guard test, independent rerun | A3 |
| `research/hypotheses/`, strategy mới + unit tests, phân tích memo, `strategy_factory.py` (handoff duy nhất qua A1) | A4 |
| `backtest/engine.py`, `main.py`, `config/settings.py` | Protected — chỉ sửa qua quyết định A1 |
| Frozen: toàn bộ `config/*.yaml` params hiện có, `strategy_*.py` hiện hữu | Không ai sửa |

## Interface decisions (đã khóa trong `contracts/protocol.py`)

1. Verdict taxonomy cell: COMPLETED / REUSED / CANDIDATE_FAIL / INCONCLUSIVE /
   DATA_INCOMPLETE / PIPELINE_ERROR / NOT_RUN_BUDGET.
2. Gates G0–G5 với enum `REASON_CODES`; metric null phải kèm reason
   (`MetricValue`), cấm default 0.0.
3. Manifest 29 trường đúng theo PLAN §8; `random_seed` nullable có lý do.
4. Scorecard weights tổng 100 + band verdict tối đa.
5. Budget: ≤3 hypotheses, ≤2 strategy mới, ≤16 param combo/hypothesis,
   ≤2 iterations, cutoff H18.
6. Sprint verdict chỉ được là 1 trong 4 giá trị `SprintVerdict`.

## Known limitations tại H0

- Two-tick slippage & delayed-fill chưa hỗ trợ bởi fill model → G4 một phần
  `NOT_IMPLEMENTED`.
- BTC-beta-neutral context chưa có implementation → `NOT_IMPLEMENTED`.
- Common intersection đa mã = S0 1 năm (35,038 bars, 2025-08-21 → 2026-08-21);
  khai báo matrix dùng intersection này, phần dư universe ghi DATA_INCOMPLETE.
- Máy 2 core → matrix workers ≤2.

## Worktrees

| Agent | Path | Branch |
|---|---|---|
| A2 | `/Users/hoangminhlong/my-quantitative-wt/data-matrix` | `wt/data-matrix` |
| A3 | `/Users/hoangminhlong/my-quantitative-wt/validation-protocol` | `wt/validation-protocol` |
| A4 | `/Users/hoangminhlong/my-quantitative-wt/research-loop` | `wt/research-loop` |

Worktree cũ (`wt/data-pipeline`, `wt/quality-safety`, `wt/research-analysis`,
`wt/ops-reporting`) giữ nguyên làm input lịch sử — KHÔNG merge tự do; nội dung
giá trị (forward_lib, live-guard audit findings, edge-stability script) sẽ được
port có chủ đích qua review nếu cần.
