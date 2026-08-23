# PLAN.md — Sprint 24 giờ · 4 AI agent · Quant Research Loop

> **Dự án:** `my-quantitative` — NautilusTrader, Binance USD-M perpetuals
> **Thời lượng:** 24 giờ liên tục kể từ khi A1 phát lệnh bắt đầu
> **Môi trường:** research, signal-only, Testnet/Demo; không live money
> **Mục tiêu:** dựng và chạy một vòng lặp có thể tìm, backtest, kiểm định và xếp
> hạng strategy trên nhiều mã mà không biến project thành máy overfit

---

## 1. Mục tiêu của sprint

Trong 24 giờ, bốn agent phải tạo được một **Minimum Viable Quant Research
Factory** với loop:

```text
Khảo sát market và negative results
        ↓
Đề xuất hypothesis có lý do kinh tế
        ↓
Khóa rules, universe, parameters và trial budget
        ↓
Implement strategy + tests
        ↓
Backtest toàn bộ declared strategy–symbol matrix
        ↓
Chronological walk-forward + costs + funding
        ↓
Hard gates + scorecard + portfolio replay
        ↓
PASS / FAIL / INCONCLUSIVE
        ↓
Lưu evidence → tạo hypothesis tiếp theo nếu còn budget
```

### Thành công sau 24 giờ

1. Pipeline chạy end-to-end và có thể tái lập.
2. Toàn bộ strategy–symbol matrix đã khai báo được chạy hoặc có reason code rõ.
3. Có ít nhất một completed research-loop iteration.
4. Mọi kết quả được lưu, kể cả FAIL và INCONCLUSIVE.
5. Có exploratory watchlist và candidate verdict rõ ràng.
6. Không có data leakage, tune hậu nghiệm hoặc live-money change.

Sprint không bắt buộc tìm được PASS. `PIPELINE_PASS_CANDIDATE_FAIL` vẫn là thành
công nếu hệ thống đã loại đúng một false edge.

---

## 2. Nguyên tắc bất di bất dịch

1. Không gỡ hard guard chặn LIVE-money.
2. Không đổi frozen parameters của experiment cũ.
3. Không dùng S0 như untouched OOS và không dùng future S1 để tune.
4. Không loại symbol/fold sau khi nhìn result.
5. Không thêm regime gate hậu nghiệm để cứu candidate cũ.
6. Regime insight mới phải thành candidate version mới, khóa trước scored run.
7. Không dùng average để che một required symbol âm.
8. Không gọi near-winner là confirmed edge.
9. Không xóa negative results hoặc ghi đè artifact cũ.
10. Không mở rộng trial budget chỉ vì chưa tìm được PASS.
11. Không để nhiều agent sửa cùng một file cùng lúc.
12. Run thiếu manifest chỉ là diagnostic, không phải evidence.
13. Buy-and-hold là contextual benchmark; flat after-cost là hard benchmark.
14. Với altcoin, báo BTC-beta-neutral context khi implementation cho phép.

---

## 3. “Backtest toàn bộ” nghĩa là gì?

Không thử vô hạn indicator và parameter. Trong sprint này, “toàn bộ” nghĩa là:

### 3.1. Frozen strategy inventory

```text
ema_atr
mean_reversion
regime_switch
breakout
reclaim_mr
trend_pullback
markdown_breakdown
```

### 3.2. Frozen symbol universe

Ưu tiên top-20 liquid USD-M universe trong `config/research_scan_top20.yaml`, nhưng
multi-symbol evidence phải dùng **actual common data intersection** phù hợp.

Nếu thiếu history, funding hoặc metadata:

- không âm thầm bỏ qua;
- ghi cell `DATA_INCOMPLETE`;
- ghi actual/requested boundaries;
- giữ symbol trong report cùng rejection reason.

### 3.3. Ba tầng backtest

#### Tier 0 — Compatibility smoke

- Mọi frozen strategy × declared symbol trên fixture/window ngắn.
- Chỉ xác nhận compatibility; không chấm edge.

#### Tier 1 — Full Stage A matrix

- Frozen parameters trên actual common S0 window.
- Chronological folds, warmup ngoài scored window.
- Commission, modeled slippage và funding audit.
- Một artifact cho mỗi strategy–symbol combination.
- Một cell fail không làm hỏng toàn matrix.

#### Tier 2 — Survivor validation

Chỉ Tier 1 survivor mới chạy:

- cost và delayed-fill stress nếu hỗ trợ;
- parameter-neighborhood robustness;
- shared-capital portfolio replay;
- contribution/concentration report.

### 3.4. Không rerun vô ích

Reuse artifact nếu cùng strategy version, config hash, data snapshot, split policy,
cost model và seed. Chỉ rerun để kiểm tra reproducibility hoặc khi dependency thay
đổi. Mọi artifact cũ vẫn được đếm trong trial registry.

---

## 4. Đội hình bốn agent

| Agent | Vai trò | Critical ownership |
|---|---|---|
| **A1** | Coordinator, Contract Owner, Integrator, Final Reviewer | `PLAN.md`, interface freeze, merge, final verdict |
| **A2** | Data, Universe và Backtest Matrix Engineer | data pipeline, coverage audit, matrix execution |
| **A3** | Validation, Metrics, Risk và Reproducibility Engineer | manifests, registry, gates, scorecards, independent rerun |
| **A4** | Quant Researcher và Strategy Engineer | hypotheses, strategy implementation, analysis memo |

### Worktrees/branches

| Agent | Branch/worktree đề xuất |
|---|---|
| A1 | integration/main; không phát triển strategy |
| A2 | `wt/data-matrix` |
| A3 | `wt/validation-protocol` |
| A4 | `wt/research-loop` |

Data directories lớn có thể dùng read-only symlink từ repo chính. Không copy
`.env` vào artifact hoặc PR.

---

## 5. Ownership và merge

| Khu vực | Owner |
|---|---|
| `data/`, coverage audit, matrix runner | A2 |
| `research/protocol/`, validation additions | A3 |
| strategy, hypothesis, analysis code | A4 |
| `PLAN.md`, integration docs, final verdict | A1 |
| `backtest/engine.py`, `main.py`, `config/settings.py` | Shared protected; handoff một owner tại một thời điểm |
| `NOTES.md`, `README.md` | A1 merge cuối; agent khác chỉ đề xuất patch |

### Merge order

1. A1 contract/interface commit.
2. A3 manifest, metric và verdict schemas.
3. A2 data audit/matrix runner.
4. A3 gates, registry và validation tests.
5. A4 strategy/hypothesis implementation.
6. A1 integration và final verdict.

### Quy tắc

- Kẹt quá 45 phút: gửi A1 error, command và attempted fix.
- Không tự đổi scope; không merge code thiếu test.
- Không feature mới sau H18; feature freeze tuyệt đối H20.

---

## 6. Research state machine

```text
IDEA
  → SPEC_DRAFT
  → SPEC_LOCKED
  → IMPLEMENTED
  → TIER0_COMPATIBLE
  → STAGE_A_SCREENED
  → SURVIVOR_VALIDATED
  → PORTFOLIO_TESTED
  → LOCKED_FOR_FUTURE_OOS
```

Nhánh kết thúc:

```text
REJECTED
INCONCLUSIVE
DATA_INCOMPLETE
PIPELINE_ERROR
NON_REPRODUCIBLE
BLOCKED
```

Không có `EDGE_CONFIRMED`, `PRODUCTION_READY` hoặc `LIVE_READY` trong sprint.

---

## 7. Bounded research loop

### Một iteration

1. **Discover:** A4 đọc negative results, folds/regimes, funding/OI/mark data và
   tạo tối đa ba hypothesis drafts.
2. **Pre-register:** A1/A3 khóa mechanism, counterparty, entry/exit, invalidation,
   universe, holding horizon, warmup, parameter/trial budget, costs và splits.
3. **Implement:** A4 implement strategy và unit tests. Spec thay đổi tạo version
   mới, không sửa im lặng version cũ.
4. **Data gate:** A2 xác minh coverage, funding, metadata, common intersection.
5. **Tier 0:** A2/A4 chạy compatibility smoke.
6. **Stage A:** A2 chạy full matrix; A3 tính canonical metrics/hard gates.
7. **Survivor tests:** A3 chạy robustness, cost và portfolio tests.
8. **Verdict:** A1 phát `REJECTED`, `INCONCLUSIVE`,
   `STAGE_A_PASS_EXPLORATORY` hoặc `LOCK_FOR_FUTURE_OOS`.
9. **Learn:** A4 dùng negative evidence tạo hypothesis mới; registry append kết
   quả cũ nguyên vẹn.

### Trial budget 24 giờ

```text
Tối đa 3 hypothesis specifications
Tối đa 2 strategy implementations mới
Tối đa 16 parameter combinations/new hypothesis
Tối đa 2 completed loop iterations
Không tune riêng theo symbol
Không mở iteration mới sau H18
Không dùng S1
```

### Hypothesis families ưu tiên

1. Funding/OI crowding và unwind.
2. BTC-beta-neutral residual momentum/reversal.
3. Volatility compression → breakout.
4. Cross-sectional momentum/reversal trong frozen liquid universe.
5. Regime-conditioned rule chỉ khi condition được pre-register.

A4 chọn tối đa hai family có data sẵn và implementation khả thi.

---

## 8. Experiment manifest

Mọi scored run phải lưu tối thiểu:

```yaml
experiment_id: EXP-YYYYMMDD-NNNN
hypothesis_id: <family-and-sequence>
candidate_version: 1
strategy_type: <name>
owner_agent: A4
validator_agent: A3
git_commit: <sha>
dirty_worktree: <true-or-false>
config_path: <path>
config_sha256: <hash>
data_snapshot_id: <id>
data_manifest_sha256: <hash>
universe_snapshot: <path>
actual_start_utc: <timestamp>
actual_end_utc: <timestamp>
common_intersection: <boundaries>
split_policy: <id>
warmup_bars: <integer>
purge_bars: <integer>
embargo_bars: <integer>
outer_folds: <integer>
parameter_combinations: <integer>
prior_family_trials: <integer>
fee_model: <id>
slippage_model: <id>
funding_mode: <native-or-post-trade-audit>
random_seed: <integer>
parameter_lock_utc: <timestamp>
command: <exact-command>
```

Outputs: manifest, raw cells, summary, gate result, scorecard, logs và hashes.

---

## 9. Canonical metrics

Canonical PnL:

```text
gross PnL
- commission
- modeled spread/slippage
- funding cashflows
- declared latency/session penalties nếu có
```

### Position metrics

- trades, expectancy USDT/R, position PF;
- win rate chỉ để mô tả;
- average winner/loser, PnL concentration.

### Return/equity metrics

- Sharpe/Sortino nếu có;
- maximum drawdown và duration;
- exposure và turnover.

### Stability

- từng symbol/fold/quarter/regime;
- positive-fold ratio;
- top-fold contribution;
- drop-one-fold/symbol sensitivity.

Metric không tính được trả `null + reason`, không thay bằng `0.0`.

---

## 10. Hard gates

Hard gate xét trước score; score không override gate fail.

### G0 — Data

- Không duplicate/unexplained gaps.
- Timestamp semantics, point-in-time/lag-safe joins rõ.
- Actual coverage/common intersection được báo.
- Funding coverage đầy đủ hoặc candidate bị đánh dấu thiếu after-funding evidence.

### G1 — Leakage/protocol

- Scored fold không tham gia parameter selection.
- Warmup ngoài scored window; transforms fit trên train.
- Purge/embargo theo holding horizon nếu cần.
- Universe/config frozen trước run.

### G2 — Reproducibility

- Manifest/hashes/seed đầy đủ.
- Independent rerun khớp selected params, positions và canonical PnL.

### G3 — Stage A

- After-cost/funding-adjusted expectancy > 0.
- Aggregate position PF ≥1.10.
- Ít nhất 2/3 folds dương.
- Ít nhất 20 closed trades/symbol; thiếu thì `INCONCLUSIVE`.
- Không fold có ≥5 trades nhưng PF <0.80.
- Không fold đóng góp >50% total PnL.
- Multi-symbol rule không che required symbol âm bằng average.

### G4 — Survivor robustness

- Baseline và +50% fee stress vẫn dương.
- Two-tick/one-bar delay stress nếu implementation hỗ trợ.
- Parameter neighborhood không phải spike đơn lẻ.
- Drop-one-fold/symbol không làm expectancy đổi dấu bất thường.

### G5 — Portfolio

- Shared-capital canonical PnL >0 và PF ≥1.10.
- Không vi phạm gross/concurrency/cluster/daily-loss limits.
- Một symbol ≤40% PnL/risk contribution.

Future gates như untouched S1, ≥100 trades, PF ≥1.15, MDD ≤10% và 6–8 tuần
signal-only được ghi `NOT_YET_TESTED`.

---

## 11. Scorecard 100 điểm

| Nhóm | Điểm |
|---|---:|
| Economic rationale và simplicity | 10 |
| Data/leakage integrity | 15 |
| Chronological edge quality | 25 |
| Time/symbol/parameter robustness | 15 |
| Cost/execution realism | 10 |
| Risk quality | 10 |
| Portfolio/diversification | 5 |
| Reproducibility/auditability | 10 |
| **Tổng** | **100** |

| Điểm | Verdict tối đa trong sprint |
|---:|---|
| <50 | Reject/redesign |
| 50–59 | Diagnostic only |
| 60–69 | Exploratory Stage A candidate |
| 70–79 | Có thể lock cho future OOS nếu G0–G5 pass |
| ≥80 | Strong research candidate, vẫn chưa confirmed edge |

Missing metric nhận 0 ở component tương ứng và reason code.

---

## 12. Lịch 24 giờ

### H0–H2 — Audit và contract freeze

**A1:** kiểm tra git, đọc canonical docs, xác minh test commands, khóa manifest,
metrics, gates, verdicts, ownership và merge order.

**A2:** audit data, coverage, weekly forward script, reusable/missing matrix cells.

**A3:** audit metrics, acceptance, funding và regression-test gaps.

**A4:** audit strategy inventory, configs, negative results; tạo tối đa ba drafts.

**Gate H2:** baseline tests xanh, interfaces khóa, ownership không overlap.

### H2–H7 — Parallel foundation

**A2:** harden incremental data pipeline, coverage artifact, isolated/resumable
matrix runner, pipeline/candidate verdict separation.

**A3:** manifest/registry/verdict schemas, canonical metrics, max-drawdown test,
LIVE-guard test.

**A4:** khóa hypothesis #1, implement strategy #1 nếu mới, unit tests.

**A1:** review interface commits, chặn scope expansion.

### H7–H9 — Integration checkpoint 1

- Merge schemas trước runner/strategy.
- Chạy tests; sửa interface mismatch.
- Xác nhận matrix size, disk/CPU budget và process-worker limit.

### H9–H13 — Frozen existing-strategy matrix

**A2:** Tier 0 inventory, Tier 1 compatible cells, resume artifacts, lưu từng cell.

**A3:** validate artifacts, preliminary gates/scorecards, reason codes.

**A4:** phân tích matrix, exploratory watchlist, concentration/regime memo.

**A1:** theo dõi failures/resources, chặn rerun vô ích.

### H13–H17 — Research loop iteration 1

- A1 khóa candidate version/trial budget.
- A4 hoàn thiện implementation/hypothesis.
- A2 chạy data gate, Tier 0 và Stage A.
- A3 chạy independent gates, score và robustness tối thiểu.
- A1 phát verdict; registry append.

### H17–H20 — Iteration 2 hoặc survivor portfolio

1. Có survivor: cost stress và shared-capital replay.
2. Iteration 1 fail nhưng có insight pre-register được: iteration 2.
3. Pipeline/reproducibility fail: dừng research, sửa correctness.

Không mở iteration mới sau H18, không vượt trial budget.

### H20 — Feature freeze

Không feature/refactor/hypothesis mới; chỉ bugfix, tests, reproduction, docs và
integration.

### H20–H23 — Independent verification

- A3 rerun representative experiment từ manifest.
- A2 xác minh matrix completeness/reason codes.
- A4 hoàn thiện memo/candidate specs.
- A1 so hashes/params/positions/PnL, chạy full tests và review artifacts.

### H23–H24 — Final handoff

A1 xuất sprint verdict, matrix coverage, candidate/watchlist table,
PASS/FAIL/INCONCLUSIVE counts, artifact paths, test results, limitations và
P0/P1/P2 backlog.

---

## 13. Required artifacts

```text
research/hypotheses/<hypothesis_id>/
  hypothesis.md
  candidate.yaml

results/registry/experiments.jsonl

results/stage_a/<experiment_id>/
  manifest.yaml
  cells.jsonl
  summary.json
  gate_result.json
  scorecard.json
  run.log

results/matrix/<matrix_id>/
  index.json
  coverage.json
  report.json

research/wayfinder/evidence/sprint-24h-<date>.md
```

---

## 14. Deliverables

### Bắt buộc

1. Plan/interface freeze evidence.
2. Baseline và final test results.
3. Data coverage report.
4. Matrix index có artifact/reason cho mọi declared cell.
5. Canonical metric regression test.
6. LIVE hard-guard regression test.
7. Experiment manifest và append-only registry.
8. Ít nhất một completed loop iteration.
9. Exploratory watchlist/regime memo.
10. Independent rerun result.
11. Final verdict và backlog.

### Optional sau khi hoàn thành bắt buộc

- `python main.py status`.
- Advanced DSR/PBO/Reality Check/SPA.
- Empirical order-book slippage.
- Native intrarun funding.
- Cron/digest/README polish/artifact cleanup.

---

## 15. Stop conditions

Dừng matrix/research loop khi:

- H20 đã tới;
- pipeline/reproducibility test fail;
- data coverage không đủ;
- disk/CPU budget bị vượt;
- trial budget đã hết;
- hai iterations liên tiếp fail cùng mechanism;
- candidate cần future OOS;
- có nguy cơ ghi đè user changes/artifacts.

Không tăng budget hoặc hạ gate để ép survivor.

---

## 16. Final verdict format

```text
PIPELINE
- status:
- reproducible:
- data coverage:
- matrix completed/declared:
- tests:

RESEARCH LOOP
- hypotheses specified:
- implementations completed:
- iterations completed:
- trials consumed:

RESULTS
- rejected:
- inconclusive:
- exploratory survivors:
- locked for future OOS:

PORTFOLIO/COST
- tests completed:
- tests not implemented:

SAFETY
- LIVE guard:
- live-money changes: none

NEXT ACTIONS
- P0:
- P1:
- P2:
```

Sprint-level verdict hợp lệ:

```text
PIPELINE_PASS_CANDIDATE_FAIL
PIPELINE_PASS_CANDIDATE_INCONCLUSIVE
PIPELINE_PASS_LOCK_FOR_FUTURE_OOS
PIPELINE_FAIL
```
