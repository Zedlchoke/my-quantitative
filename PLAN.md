# PLAN.md — Master Research Program · V3 → V6 · Correctness Then Edge Search

> **Repo:** `my-quantitative`
> **Phạm vi:** Binance USD-M perpetual research; research/Testnet/Demo only
> **Thời lượng:** tối đa 48 giờ: V3 H0–H24, V4 H24–H48
> **Đội hình:** A1, A2, A3, A4
> **Không được phép:** live-money execution, S1 inspection, post-hoc tuning,
> ghi đè artifact V1/V2/V3
> **Transition rule:** V4 chỉ tự động mở khi toàn bộ V3 completion gate PASS;
> nếu V3 partial/fail thì V4 bị `BLOCKED_BY_V3`, không được implement strategy
>
> **Current frontier (2026-08-24):** V3/V4 đã chạy xong. Phần 28 trở đi là
> kế hoạch có hiệu lực cho Sprint V5→V6 và supersede mọi `NEXT ACTIONS` cũ;
> artifacts/báo cáo V3/V4 vẫn immutable để phục vụ audit.

---

## 1. Starting verdict từ independent audit Sprint V2

```text
PIPELINE_PARTIAL_PASS_CANDIDATE_FAIL
```

### 1.1. Những phần Sprint V2 đã PASS

1. LIVE environment được normalize/allowlist và boolean safety parsing đã được
   siết chặt cho đường live execution.
2. Full test suite được xác minh lại: `277 passed`, `0 failed`, `0 xfailed`.
3. Position-level Profit Factor đã thay fold-net PF và có regression tests.
4. ETH gap được phân loại; clean S0 intersection được khai báo trước final run.
5. Matrix index và cell artifacts chứa 98/98 completed cells, không pipeline
   error.
6. H-FUNDCROWD-MR-v2 bị reject đúng kỷ luật; không candidate được promote.
7. V1 artifacts được giữ lại và registry tiếp tục append-only.

### 1.2. Những claim chưa đủ bằng chứng để PASS hoàn toàn

1. `ManifestV2` được tạo bởi evaluator sau khi matrix backtest đã chạy. Do đó
   `run_started_utc`, `exact_argv`, git commit/dirty state và lock timestamp mô
   tả evaluation step, chưa chắc mô tả scored backtest launch.
2. Evaluator tự tạo `parameter_lock_utc` ngay trước evaluation; nó chưa xác minh
   `locked_at_utc` thật trong candidate spec trước matrix run.
3. H-FUNDCROWD frozen `config.yaml` và `candidate.yaml` có cùng bytes/hash;
   manifest ghi sai hypothesis/version/owner (`H-EXISTING-...-v1`, version 1,
   A2) thay vì candidate H-FUNDCROWD-MR-v2 do A4 sở hữu.
4. G1 vẫn nhận một số evidence hard-code, gồm
   `transforms_fit_on_train=True`; universe freeze dựa trên synthetic evaluation
   timestamp. Đây là assertion, chưa phải runtime proof.
5. G2 của 98 cells chủ yếu tự so ledger/hash vừa được evaluator tạo với chính
   artifact nguồn. Chỉ một experiment có independent backtest rerun thực sự.
6. `report.json` của final matrix khai báo 21 funding-crowding cells trong khi
   `index.json` và thư mục cells có 98. Aggregate report đã bị last-run overwrite.
7. Scorecard vẫn coarse/hard-coded: rationale 10, risk 0.5, cost 1.0; chưa triển
   khai các metric bands chi tiết đã khóa trong Sprint V2 plan.
8. Bar-close fill optimism đã được chứng minh: signal dùng close của bar `t` và
   market order có thể fill tại close cùng timestamp. Đây là P0 trước mọi
   candidate dương trong tương lai.

### 1.3. Ý nghĩa nghiên cứu

- Kết luận `0/98 candidate PASS` vẫn hợp lý và được giữ nguyên.
- Không rerun/tune H-FUNDCROWD-MR-v2 để cứu kết quả trên cùng S0.
- Không candidate nào đủ điều kiện capture S1.
- Sprint V3 phải đóng các lỗ hổng evidence/execution trước khi mở hypothesis
  implementation mới.

---

## 2. Mục tiêu Sprint V3

Trong 24 giờ, hoàn thành một pipeline mà:

1. Provenance được capture tại **scored backtest launch**, không phải evaluation.
2. Candidate thật sự được khóa trước launch và identity trong manifest chính xác.
3. G1 dựa trên runtime artifacts/tests, không dựa trên boolean hard-code.
4. G2 phân biệt artifact integrity với independent reproducibility.
5. Mọi signal-driven market entry có fill timestamp sau signal timestamp theo
   execution contract mới.
6. Expectancy-R và initial risk được ghi ở position level.
7. Scorecard dùng metric bands thật và không override hard gates.
8. Matrix V3 chạy lại frozen 98-cell inventory dưới execution semantics mới.
9. Aggregate report/index/registry tự reconcile bằng máy.
10. Chỉ survivor thật sự mới được stress, rerun và cân nhắc lock cho future S1.

Sprint thành công ngay cả khi V3 vẫn có 0 survivor.

---

## 3. Definition of Done

Tất cả điều kiện sau phải có machine-readable evidence:

### P0 bắt buộc

- [ ] Runner snapshot inputs trước khi đọc/chạy scored results.
- [ ] Manifest ghi exact matrix/backtest argv, commit, dirty state và launch time.
- [ ] `candidate.locked_at_utc < backtest.run_started_utc` được parse và validate.
- [ ] Runtime config và candidate spec là hai artifact đúng vai trò.
- [ ] Hypothesis ID, candidate version, owner và declared trials khớp source spec.
- [ ] G1 không còn unconditional `True` trong production evaluation path.
- [ ] Execution fixture chứng minh `fill_ts > signal_ts` cho entry market order.
- [ ] Legacy same-bar mode chỉ được phép với nhãn `DIAGNOSTIC_ONLY`.
- [ ] G2a artifact integrity và G2b independent rerun là hai verdict riêng.
- [ ] `report.declared_cells == len(index.cells) == actual cell files`.
- [ ] Scorecard bands có boundary tests.
- [ ] Full tests không fail/xfail.

### Rerun và research evidence

- [ ] Frozen V2 98-cell inventory được ánh xạ đầy đủ sang V3.
- [ ] V3 matrix 98/98 completed hoặc có reason code cho từng cell.
- [ ] V2 artifacts và registry entries không bị sửa.
- [ ] V2/V3 comparison giải thích tác động của execution delay.
- [ ] Mỗi strategy family có ít nhất một deterministic independent rerun sample.
- [ ] Mọi G3 survivor được independent rerun 100%.
- [ ] Không candidate fail nào được đưa vào G4/G5.
- [ ] Không future S1 được đọc.

Nếu một P0 không đạt, final pipeline verdict không được là `PIPELINE_PASS`.

---

## 4. Nguyên tắc bất di bất dịch

1. Correctness trước throughput và strategy count.
2. Hard gate trước score; score không cứu gate fail.
3. Thiếu evidence là `INCONCLUSIVE` hoặc `NOT_YET_TESTED`, không PASS.
4. Không synthetic timestamp để làm đẹp provenance.
5. Không lấy evaluator time thay backtest launch time.
6. Không tự so artifact với chính nó rồi gọi là independent rerun.
7. Không sửa candidate spec sau lock; status/verdict lưu ở file riêng.
8. Không post-hoc filter, symbol exclusion hoặc parameter expansion.
9. S0 chỉ là development/screening data.
10. S1 phải bắt đầu sau candidate lock và không overlap S0.
11. Không ghi đè V1/V2 artifacts.
12. Không sửa score bands sau khi xem V3 results.
13. Không mở strategy mới nếu P0 execution/provenance chưa PASS.
14. Crypto perpetual và TradFi/equity research universe phải tách biệt.
15. Không live-money change.

---

## 5. Đội hình và ownership

| Agent | Vai trò | Exclusive ownership |
|---|---|---|
| **A1** | Coordinator, Contract Owner, Integrator | `PLAN.md`, contract freeze, merge, final audit/verdict |
| **A2** | Execution Semantics & Risk Accounting Engineer | backtest execution mode, signal/fill audit, position initial-risk/R |
| **A3** | Provenance, Gates, Scorecard & Matrix Engineer | runner launch manifest, G1/G2, scorecard, registry/report reconciliation |
| **A4** | Independent Quant Reviewer & Research Designer | V2/V3 analysis, independent reruns, hypothesis drafts; no gate edits |

### 5.1. Protected files

| File/khu vực | Owner tại một thời điểm |
|---|---|
| `backtest/engine.py`, base strategy execution hooks | A2 |
| `research/matrix_runner.py` | A3; A2 chỉ đề xuất interface patch |
| `research/sprint_eval.py`, `research/provenance.py` | A3 |
| `research/protocol/{gates,scorecard,reproduce}.py` | A3 |
| `contracts/protocol.py` | A1 |
| `strategy_*.py` | chỉ A2 khi migration execution contract yêu cầu |
| hypothesis analysis/spec | A4 |

### 5.2. Handoff contract

Mỗi handoff phải gồm:

```text
commit_sha:
files_changed:
contract_changes:
commands_run:
tests_passed/failed/xfailed:
artifact_paths:
known_limitations:
```

Không hai agent sửa cùng protected file trong cùng checkpoint.

---

## 6. Lịch thực thi 24 giờ

### H0–H2 — Audit freeze và interface contract

**A1**

- Xác minh clean/dirty worktree và lưu baseline commit.
- Chạy baseline full tests bằng `.venv/bin/python`.
- Freeze schemas:
  - `ExecutionMode`
  - `RunLaunchManifest`
  - `LeakageEvidence`
  - `ArtifactIntegrityResult`
  - `IndependentReproductionResult`
  - `PositionRiskStats`
- Freeze V3 matrix inventory đúng 98 cells từ V2 index.
- Hash V2 index/cells trước mọi V3 run.

**A2/A3/A4** chỉ audit và đề xuất interface; chưa sửa overlap files.

#### Gate H2

```text
BASELINE_TESTS_PASS
V2_HASH_SNAPSHOT_WRITTEN
V3_INTERFACES_FROZEN
OWNERSHIP_NO_OVERLAP
```

### H2–H7 — Parallel P0 implementation

#### A2 — Execution truth

Implement hai explicit modes:

```text
SAME_BAR_CLOSE_DIAGNOSTIC
NEXT_BAR_EVENT_BASELINE
```

Rules:

- Default scored mode là `NEXT_BAR_EVENT_BASELINE`.
- Signal tạo tại closed bar `t` chỉ được submit/fill tại event sau `t`.
- Mỗi order/position lưu `signal_ts`, `submit_ts`, `fill_ts`, `signal_bar_close`,
  `fill_price`, `execution_mode`.
- Acceptance invariant: `signal_ts < fill_ts` cho scored entry.
- Nếu engine chỉ fill tại close bar kế tiếp, ghi đúng semantic đó; không gọi là
  next-open nếu không phải next-open.
- Exit timing phải được ghi và stress riêng; không ngầm dùng current close làm
  attainable exit price.
- One-tick và two-tick adverse fill phải là cấu hình explicit.
- Legacy same-bar run luôn có `evidence_class: DIAGNOSTIC_ONLY`.

Thêm micro-fixture với giá dễ tính để chứng minh signal/fill timestamp và price.

#### A2 — Position risk/R

Mỗi closed position lưu:

```text
initial_risk_usdt
canonical_pnl_after_cost_funding
r_multiple = canonical_pnl_after_cost_funding / initial_risk_usdt
```

Rules:

- Initial risk được freeze tại entry từ size, entry và initial stop.
- `initial_risk_usdt <= 0` trả `null + invalid_initial_risk`.
- Không dùng realized loss làm denominator.
- Aggregate expectancy-R là mean của position R trên scored positions.
- Reconcile canonical PnL với positions ở tolerance `1e-9`.

#### A3 — Launch-time provenance

Di chuyển provenance snapshot vào matrix/backtest runner trước run:

```text
parse locked candidate
→ validate locked_at < now
→ snapshot candidate/runtime config/data/universe
→ capture git/dirty/exact runner argv/start time
→ execute backtest
→ write results
→ evaluator chỉ đọc frozen manifest
```

Không cho evaluator tự tạo lock timestamp.

Manifest phải ghi đúng:

- Actual hypothesis ID và version.
- Actual owner/validator.
- Full runtime config snapshot.
- Candidate spec snapshot hoặc explicit existing-strategy spec.
- Actual declared/executed family trials.
- Actual runner command và launch commit.
- Execution mode và slippage mode.
- Source-to-frozen hashes.

Candidate và runtime config phải là hai logical inputs; không copy cùng source
cho cả hai chỉ để thỏa schema.

#### A3 — G1/G2/score/report

- Thay hard-coded G1 flags bằng `LeakageEvidence` được runner xuất.
- Learned transforms: ghi train-fit timestamps/rows.
- Không có learned transform: `NOT_APPLICABLE` kèm reason, không `True` giả.
- Warmup: lưu actual warmup/scored boundaries.
- Universe freeze: so candidate lock, universe hash và launch time thật.
- Execution leakage: G1 fail nếu scored `fill_ts <= signal_ts`.

Tách G2:

```text
G2A_ARTIFACT_INTEGRITY
G2B_INDEPENDENT_REPRODUCIBILITY
```

- G2a kiểm hashes/schema/reconciliation.
- G2b phải launch backtest mới từ frozen inputs và so positions/PnL.
- Không có independent rerun: G2b=`NOT_YET_TESTED`.
- Promotion G2 PASS yêu cầu cả G2a và G2b PASS.

Matrix report phải aggregate từ index cuối, không overwrite bằng last batch.
Thêm reconciliation test cho report/index/cells/registry.

Scorecard phải đọc metric thật; xóa constant rationale/risk/cost fractions.

### H7–H9 — Integration checkpoint

Merge order:

1. A1 contracts.
2. A2 execution/risk primitives.
3. A3 runner provenance.
4. A3 gates/score/report.
5. Strategy migrations nếu cần.

Chạy targeted tests và full tests.

#### Gate H9

```text
SIGNAL_FILL_ORDERING_PASS
POSITION_R_REGRESSION_PASS
LAUNCH_PROVENANCE_PASS
G1_NO_HARDCODED_PASS
G2A_G2B_SEPARATION_PASS
MATRIX_RECONCILIATION_TEST_PASS
FULL_TESTS_PASS
```

Fail bất kỳ mục nào: dừng V3 matrix và sửa P0.

### H9–H15 — Frozen 98-cell V3 matrix

**A3 chạy; A2 theo dõi execution evidence; A4 không xem partial results để tune.**

- Input inventory lấy nguyên từ frozen V2 index.
- Window giữ clean S0 contract đã chốt.
- Parameters, universe và family trial count không đổi.
- Execution mode: `NEXT_BAR_EVENT_BASELINE`.
- Mỗi cell có launch manifest riêng hoặc batch manifest liên kết chính xác tới
  immutable cell spec.
- Mỗi cell ghi signal/fill evidence và position R.
- Không overwrite `results/matrix/v2_stage_a_final` hoặc `results/stage_a_v2`.

Output:

```text
results/matrix/v3_execution_truth/
results/stage_a_v3/
```

#### Gate H15

```text
INDEX_CELLS = 98
ACTUAL_CELL_FILES = 98
REPORT_DECLARED = 98
COMPLETED_OR_EXPLAINED = 98
V2_HASHES_UNCHANGED
NO_SIGNAL_FILL_ORDER_VIOLATION
```

### H15–H19 — Comparison, reruns và survivor tests

**A4** tạo V2/V3 comparison:

- Trades, expectancy USDT, expectancy R, PF, PnL.
- Fill-delay impact theo strategy và symbol.
- Candidate nào đổi dấu hoặc đổi gate.
- Same-bar optimism magnitude.
- Concentration theo positive PnL denominator đã khai báo.

**A3/A4 independent reruns:**

- Deterministic sample tối thiểu một cell cho mỗi strategy family.
- 100% G3 survivors.
- Rerun từ frozen manifest bằng process/command riêng.
- So positions digest, canonical PnL, trades và execution timestamps.

Chỉ G3 survivor mới chạy:

- +50% fees.
- Two-tick adverse fill.
- Additional one-event delay stress.
- Parameter neighborhood đã declared từ trước.
- Drop-one-fold/symbol.
- Shared-capital replay nếu có nhiều survivor.

Không survivor: ghi `NO_SURVIVOR`, không hạ gate.

### H19–H22 — Research design, không data-mining

**A4** được viết tối đa hai `SPEC_DRAFT`, chưa scored run, dựa trên:

- V1/V2/V3 negative evidence.
- Cơ chế kinh tế và counterparty cụ thể.
- Dữ liệu point-in-time thực sự có sẵn.
- Trial budget tối đa 8 combinations/family.
- Điều kiện bác bỏ định lượng trước run.
- Required portfolio/benchmark engine.

Không được:

- Tạo H-FUNDCROWD-MR-v3 bằng cách sửa threshold trên cùng kết quả.
- Thêm OI nếu coverage/publication contract chưa đủ.
- Implement cross-sectional strategy trước khi shared-capital ranking/rebalance
  engine có contract và tests.
- Chạy draft trên S0 trong Sprint V3 nếu chưa được A1 lock cho sprint sau.

A1/A3 chỉ chọn tối đa một spec để làm frontier Sprint V4. Không bắt buộc chọn.

### H22–H24 — Independent audit và final report

- Feature freeze.
- A3 verify hashes và matrix reconciliation.
- A4 challenge audit provenance, leakage, fill semantics và selection process.
- A1 chạy full tests, kiểm tra git diff/status và artifact immutability.
- A1 phát pipeline verdict và candidate verdict riêng.
- Không capture S1 nếu không có locked survivor.

---

## 7. Execution evidence contract

Mỗi scored position cần tối thiểu:

```yaml
position_id: <stable-id>
strategy_type: <name>
symbol: <symbol>
fold: <id>
side: <LONG-or-SHORT>
signal_ts: <utc>
submit_ts: <utc>
fill_ts: <utc>
signal_reference_price: <number>
fill_price: <number>
execution_mode: NEXT_BAR_EVENT_BASELINE
slippage_ticks: <integer>
quantity: <number>
initial_stop_price: <number>
initial_risk_usdt: <number>
gross_pnl: <number>
commission: <number>
slippage_cost: <number>
funding_pnl: <number>
canonical_pnl: <number>
r_multiple: <number-or-null>
```

Hard invariant:

```text
signal_ts < submit_ts <= fill_ts
```

Nếu framework chỉ cho `submit_ts == fill_ts`, vẫn hợp lệ khi cả hai lớn hơn
`signal_ts` và semantic được ghi rõ.

---

## 8. Launch manifest contract

```yaml
schema_version: 3
experiment_id: <id>
matrix_id: <id>
hypothesis_id: <actual-id>
candidate_version: <actual-version>
strategy_type: <name>
owner_agent: <owner>
validator_agent: <validator>

candidate_locked_at_utc: <from-frozen-spec>
backtest_run_started_utc: <captured-before-engine-run>
backtest_run_finished_utc: <captured-after-engine-run>
git_commit_at_launch: <actual-sha>
dirty_worktree_at_launch: <bool>
exact_backtest_argv: [<actual-runner-argv>]
random_seed: <integer>

runtime_config_path: frozen/runtime_config.yaml
runtime_config_sha256: <actual-sha256>
candidate_spec_path: frozen/candidate.yaml
candidate_spec_sha256: <actual-sha256>
data_manifest_path: frozen/data_manifest.json
data_manifest_sha256: <actual-sha256>
universe_path: frozen/universe.json
universe_sha256: <actual-sha256>

execution_mode: NEXT_BAR_EVENT_BASELINE
slippage_ticks: 1
fee_model: <id>
funding_mode: <id>
split_policy: <id>
warmup_bars: <integer>
outer_folds: 3
declared_family_trials: <integer>
executed_family_trials: <integer>
```

Validation fail-closed khi:

- lock không tồn tại hoặc lock không sớm hơn launch;
- source/frozen hash mismatch;
- hypothesis identity không khớp candidate;
- argv là evaluator command thay vì backtest command;
- execution mode thiếu;
- actual window/universe không khớp frozen input.

---

## 9. Hard gates V3

### G0 — Data

- Continuous clean OHLCV coverage trong scored window.
- Funding/metadata đầy đủ hoặc reason code.
- Timestamp/publication semantics rõ.
- Universe exclusions pre-registered.

### G1 — Leakage và execution

- Train/test selection isolation.
- Actual warmup boundaries.
- Transform fit evidence hoặc explicit not-applicable reason.
- Universe/candidate khóa trước launch.
- `signal_ts < fill_ts` cho scored entries.
- Không current-bar price fill đối với current-bar signal.

### G2a — Artifact integrity

- Manifest/schema/hashes đầy đủ.
- Position totals reconcile canonical metrics.
- Report/index/cell counts reconcile.

### G2b — Independent reproducibility

- Backtest process mới chạy từ frozen inputs.
- Parameters, positions digest, trade count và canonical PnL match tolerance.

### G3 — Stage A

- After-cost/funding expectancy > 0.
- Position PF ≥1.10.
- Ít nhất 2/3 folds dương.
- Ít nhất 20 closed trades mỗi required symbol; thiếu là `INCONCLUSIVE`.
- Không fold có ≥5 trades nhưng PF <0.80.
- Không một fold đóng góp >50% positive aggregate PnL.
- Không dùng average để che required symbol âm.

### G4 — Robustness/execution stress

- +50% fee stress vẫn dương.
- Two-tick adverse fill vẫn dương.
- Additional delay stress vẫn dương.
- Parameter neighborhood không phải spike.
- Drop-one-fold/symbol không làm đổi kết luận bất thường.

### G5 — Portfolio

- Shared-capital PnL >0 và PF ≥1.10.
- Gross/concurrency/cluster/daily-loss limits PASS.
- Một symbol ≤40% PnL/risk contribution.
- BTC-beta-neutral context khi implementation phù hợp.

Chỉ G0, G1, G2a, G2b, G3, G4, G5 đều PASS mới được cân nhắc lock S1.

---

## 10. Scorecard V3 — 100 điểm

Score chỉ xếp hạng survivor; hard gate luôn có quyền ưu tiên.

| Component | Điểm |
|---|---:|
| Economic rationale/simplicity | 10 |
| Data/leakage integrity | 15 |
| Chronological edge quality | 25 |
| Time/symbol/parameter robustness | 15 |
| Cost/execution realism | 10 |
| Risk quality | 10 |
| Portfolio/diversification | 5 |
| Reproducibility/auditability | 10 |
| **Tổng** | **100** |

### 10.1. Chronological edge bands

| Metric | Bands | Điểm |
|---|---|---:|
| Expectancy R/trade | ≤0 / (0,.03) / [.03,.05) / [.05,.10) / ≥.10 | 0/2/4/6/8 |
| Position PF | <1.10 / 1.10–1.14 / 1.15–1.24 / 1.25–1.49 / ≥1.50 | 0/2/4/6/7 |
| Positive folds | <2/3 / 2/3 / 3/3 | 0/3/5 |
| Closed trades | <20 / 20–49 / 50–99 / ≥100 | 0/1/2/3 |
| Flat after-cost benchmark | fail/pass | 0/2 |

Các component khác phải dùng metric/evidence subcomponents như contract Sprint V2;
không được cấp full points chỉ vì một gate boolean PASS.

### 10.2. Score eligibility

- G0/G1/G2a fail: `UNRANKED_PROTOCOL_FAIL`.
- G2b chưa chạy: score chỉ diagnostic.
- G3 fail/inconclusive: không vào survivor leaderboard.
- `final_research_score` chỉ có sau G0–G5 PASS.
- Missing metric nhận 0 và machine-readable reason.

---

## 11. Matrix và registry reconciliation

Finalizer phải tính lại từ filesystem/index, không nhận manual counts:

```text
declared_cells
indexed_cells
actual_cell_files
completed
data_incomplete
pipeline_error
registry_entries_for_matrix
stage_a_artifact_dirs
```

Tất cả counts phải khớp hoặc final verdict là partial/fail.

Registry giữ append-only và phân biệt:

```text
CELL_RESULT
ARTIFACT_INTEGRITY_VERIFY
INDEPENDENT_RERUN_VERIFY
MATRIX_FINALIZE
```

Không ghi verify V3 thiếu `schema`, `matrix_id`, `verified_experiment_id` hoặc
verification type.

---

## 12. Required artifacts

```text
results/matrix/v3_execution_truth/
  frozen_v2_inventory.json
  index.json
  report.json
  reconciliation.json
  v2_v3_comparison.json
  cells/

results/stage_a_v3/<experiment_id>/
  launch_manifest.yaml
  frozen/
    runtime_config.yaml
    candidate.yaml
    data_manifest.json
    universe.json
  positions.jsonl
  execution_evidence.json
  canonical_metrics.json
  gate_result.json
  scorecard.json
  artifact_hashes.json
  run.log

results/reproduction_v3/<verify_id>/
  source_experiment.json
  rerun_manifest.yaml
  comparison.json
  run.log

research/hypotheses/_analysis_v3/
  v2_v3_execution_impact.md
  candidate_funnel.json
  hypothesis_drafts.md
  challenge_memo.md

research/wayfinder/evidence/sprint-v3-24h-<date>.md
```

---

## 13. Stop conditions

Dừng matrix/research khi:

- Signal/fill ordering test fail.
- Launch provenance không chứng minh lock-before-run.
- G1 còn hard-coded PASS trong scored path.
- G2b tự so cùng artifact/process.
- Position R hoặc canonical PnL không reconcile.
- V2 artifacts thay đổi.
- Trial budget hoặc resource budget bị vượt.
- Có nguy cơ live execution.
- H20 đã tới và matrix chưa hoàn tất.

Không hạ gate hoặc sửa result để hoàn thành sprint.

---

## 14. Final report format

```text
SPRINT V3 VERDICT
- pipeline_status:
- candidate_status:
- blockers:

BASELINE
- commit:
- tests:
- V2_hash_snapshot:

EXECUTION
- scored_execution_mode:
- signal_fill_invariant:
- same_bar_mode_classification:
- one_tick/two_tick evidence:

PROVENANCE
- snapshot_before_backtest:
- lock_before_launch:
- exact_backtest_argv:
- identity_accuracy:

GATES
- G0:
- G1:
- G2a:
- G2b:
- G3:
- G4:
- G5:

MATRIX
- declared/index/files/completed:
- registry_reconciliation:
- V2_unchanged:

V2 VS V3
- PnL/PF/expectancy-R impact:
- verdict changes:
- execution optimism magnitude:

REPRODUCIBILITY
- sampled families:
- survivor reruns:
- matches/mismatches:

RESEARCH
- survivors:
- locked_for_S1:
- hypothesis drafts only:
- S1 inspected: no

TESTS
- passed:
- failed:
- xfailed:

NEXT FRONTIER
- selected ticket/spec:
- prerequisites:
```

Allowed final verdicts:

```text
PIPELINE_PASS_CANDIDATE_FAIL
PIPELINE_PASS_CANDIDATE_INCONCLUSIVE
PIPELINE_PASS_LOCK_FOR_FUTURE_S1
PIPELINE_PARTIAL_PASS_CANDIDATE_FAIL
PIPELINE_FAIL
```

---

## 15. Completion gate bắt buộc để chuyển V3 → V4

A1 chỉ được phát lệnh bắt đầu V4 khi **tất cả** điều kiện dưới đây PASS bằng
machine-readable artifact. Không có quyền waiver để kịp thời gian.

### 15.1. V3 correctness gate

```text
V3-C01 baseline_and_final_tests_pass
V3-C02 no_failed_or_xfailed_tests
V3-C03 signal_ts_strictly_before_fill_ts_for_all_scored_entries
V3-C04 same_bar_close_is_diagnostic_only
V3-C05 position_pnl_and_expectancy_r_reconcile
V3-C06 launch_manifest_created_before_backtest
V3-C07 candidate_lock_precedes_real_backtest_launch
V3-C08 actual_runner_argv_commit_dirty_state_captured
V3-C09 hypothesis_identity_version_owner_are_exact
V3-C10 G1_has_no_unconditional_true_in_scored_path
V3-C11 G2a_and_G2b_are_separate
V3-C12 one_independent_rerun_per_strategy_family
V3-C13 all_G3_survivors_independently_rerun
V3-C14 matrix_report_index_files_registry_reconcile
V3-C15 V2_artifact_hashes_unchanged
V3-C16 V3_inventory_completed_or_explained_98_of_98
V3-C17 scorecard_band_boundary_tests_pass
V3-C18 no_live_money_change
V3-C19 S1_not_read
```

### 15.2. Transition decision

```text
if all(V3-C01..V3-C19):
    transition = V4_AUTHORIZED
else:
    transition = BLOCKED_BY_V3
```

`BLOCKED_BY_V3` là terminal condition của master plan. A1 phải báo exact failed
criteria và tiếp tục frontier correctness ở sprint sau; không được giao A4 chạy
hypothesis mới.

### 15.3. Candidate handling khi V3 PASS

- Nếu V3 có survivor: hoàn thành G4/G5/G2b, lock hoặc reject trước V4; S1 capture
  của survivor phải cách ly hoàn toàn với V4 research.
- Nếu V3 có 0 survivor: vẫn được mở V4 khi pipeline correctness PASS.
- Không tune lại H-FUNDCROWD-MR-v2 hoặc bất kỳ V1/V2 candidate nào trên cùng S0.

---

## 16. Sprint V4 objective — bounded cross-sectional edge research

V4 dùng pipeline đã được chứng minh ở V3 để triển khai đúng **một** family mới:

```text
H-XSECT-MOM-v1 — dollar-neutral cross-sectional momentum
```

Mục tiêu V4:

1. Xây shared-capital cross-sectional rank/rebalance engine point-in-time.
2. Test một hypothesis có cơ sở kinh tế, không random indicator search.
3. Dùng đúng ba lookback candidates và một negative-control experiment.
4. Walk-forward ở portfolio level, tính fees, slippage và funding.
5. Đo BTC beta, concentration, turnover và shared-capital drawdown.
6. Reject, inconclusive hoặc lock tối đa một candidate cho future S1.

V4 không có mục tiêu bắt buộc tìm được PASS.

---

## 17. Research basis và giới hạn ngoại suy

### 17.1. Execution research

NautilusTrader bar execution xử lý OHLC trước khi gọi `on_bar`; order gửi trong
callback có thể settle ở close cùng timestamp. Framework không cung cấp native
next-bar-open fill cho bar-only data. Vì repo dùng NautilusTrader `1.230.0`,
micro-fixture trên installed version là source of truth; documentation chỉ là
design reference.

### 17.2. Factor research

Nghiên cứu `Common Risk Factors in Cryptocurrency` tìm thấy market, size và
momentum giải thích cross-sectional crypto returns; nghiên cứu `Risks and
Returns of Cryptocurrency` cũng ghi nhận crypto time-series momentum.

Đây chỉ là prior cho hypothesis, không phải bằng chứng edge trong repo vì:

- paper universe lớn hơn bảy symbols;
- paper chủ yếu nghiên cứu spot/coin returns, không phải Binance perps;
- repo phải chịu funding, leverage, liquidation, fees và execution delay;
- S0 chỉ khoảng một năm và đã được dùng để research;
- cross-sectional result có thể phụ thuộc regime hoặc liquidity universe.

Vì vậy V4 dùng trial budget nhỏ, portfolio-neutral construction và future S1
trước mọi promotion.

### 17.3. Vì sao không chọn family khác ở V4

- Funding-crowding v2 đã bị reject; đổi threshold tiếp là post-hoc tuning.
- OI local overlay chỉ khoảng 30 ngày, chưa đủ cho S0 walk-forward dài.
- Directional EMA/MR/regime/breakout families đã thất bại rộng trên V2.
- Cross-sectional ranking chưa được thử và có khả năng loại bớt common market
  direction đã làm nhiều single-symbol strategies thất bại.

---

## 18. H-XSECT-MOM-v1 pre-registration contract

A4 viết `candidate.yaml` đúng nội dung dưới đây trước khi code hoặc scored run.
A1 kiểm tra và khóa spec sau khi V4 data/portfolio interfaces PASS.

```yaml
hypothesis_id: H-XSECT-MOM-v1
family: cross_sectional_momentum
candidate_version: 1
stage: S0_EXPLORATORY
owner_agent: A4

universe:
  traded_symbols:
    - ETHUSDT
    - SOLUSDT
    - BNBUSDT
    - XRPUSDT
    - DOGEUSDT
    - LINKUSDT
    - ADAUSDT
  benchmark_symbol: BTCUSDT
  universe_policy: fixed_before_run

bar_interval: 15m
signal_clock: daily_00_00_utc_close
rebalance_interval: 24h
execution_mode: NEXT_BAR_EVENT_BASELINE

signal:
  type: cumulative_log_return_rank
  lookback_days: [3, 7, 14]
  exclude_execution_bar: true
  long_count: 2
  short_count: 2
  tie_break: symbol_ascending

portfolio:
  gross_target: 1.0
  net_target: 0.0
  long_gross: 0.5
  short_gross: 0.5
  weighting: equal_within_leg
  max_abs_weight_per_symbol: 0.25
  min_eligible_symbols: 7
  incomplete_cross_section_action: skip_entire_rebalance

trial_budget:
  scored_candidates: 3
  negative_controls: 1
  total_experiments: 4

negative_control:
  type: reverse_rank
  lookback_days: 7
  eligible_for_selection: false

selection_tie_break:
  - all_hard_gates_pass
  - highest_median_fold_expectancy_r
  - lowest_turnover
  - lowest_max_drawdown
```

Không được thêm volatility scaling, funding threshold, regime filter, symbol
weight, extra lookback hoặc rebalance interval trong version 1.

---

## 19. V4 point-in-time data contract

### 19.1. Synchronized panel

- Sử dụng continuous clean S0 intersection được V3 xác nhận.
- BTCUSDT chỉ làm benchmark/beta context; phải audit coverage độc lập.
- Mỗi signal timestamp chỉ dùng bars có `ts_init/ts_event <= signal_ts` theo
  timestamp contract đã test.
- Daily close được resample deterministically từ completed 15m bars.
- Rank tại timestamp `t` không được dùng return/fill của event sau `t`.
- Nếu bất kỳ traded symbol thiếu required lookback tại một rebalance, skip toàn
  rebalance; không chỉ bỏ symbol thiếu rồi thay đổi cross-section.
- Universe membership không được thay sau khi xem PnL.

### 19.2. Liquidity và costs

- Chỉ universe đã được freeze; không tái chọn top-volume hậu nghiệm.
- Commission, one-tick baseline slippage và funding áp ở position/leg level.
- Rebalance turnover tính từ target-weight delta, không giả đóng/mở miễn phí.
- Quantity obey instrument precision, min quantity và min notional.
- Rejected order hoặc insufficient margin phải thành reason code.

### 19.3. BTC beta context

- Tính realized portfolio beta với BTC trên returns cùng timestamp.
- Window/beta estimator được freeze trước scored run.
- BTC không được dùng vào selection ngoài metric đã pre-register.
- Thiếu BTC clean coverage: V4 được chạy diagnostic nhưng không được lock S1.

---

## 20. Shared-capital portfolio engine contract

Engine phải rebalance cả cross-section như một portfolio, không chạy bảy
single-symbol backtests rồi cộng PnL.

### Required state

```text
shared_cash
shared_margin
gross_exposure
net_exposure
target_weights
actual_weights
pending_orders
per_symbol_position
portfolio_equity
portfolio_drawdown
funding_cashflows
turnover
```

### Rebalance sequence

```text
complete signal bar
→ build synchronized feature vector
→ rank all seven symbols
→ compute frozen target weights
→ risk/margin pre-check whole rebalance
→ submit reductions before increases
→ execute only after signal timestamp
→ record partial/rejected fills
→ update shared cash/margin/equity
```

### Required invariants

- Sum target weights approximately zero within `1e-9` before rounding.
- Gross target ≤1.0.
- Absolute net realized exposure ≤0.10 after rounding/fills or reason code.
- Absolute target weight per symbol ≤0.25.
- No double-counted capital across symbols.
- Funding charged/credited based on actual held positions at settlement.
- No lookahead from future cross-sectional membership or fill prices.

---

## 21. V4 agent ownership

| Agent | Vai trò V4 | Exclusive ownership |
|---|---|---|
| **A1** | V4 coordinator/contract lock/integrator | spec lock, interfaces, merge, final verdict |
| **A2** | Synchronized data & shared-capital engine | panel builder, rebalance engine, weights/margin/funding |
| **A3** | Portfolio metrics, gates, beta & reproduction | portfolio ledger, score, gates, matrix, independent rerun |
| **A4** | Hypothesis/strategy owner & independent analysis | H-XSECT-MOM spec, rank signal, result/challenge memo |

Protected file ownership tiếp tục áp dụng. A4 không sửa gates; A3 không sửa
hypothesis after lock.

---

## 22. Lịch Sprint V4 — H24 đến H48

### H24–H26 — Authorization và spec freeze

**A1**

- Đọc `v3_transition.json`; xác minh đủ V3-C01..V3-C19 PASS.
- Nếu thiếu một mục: ghi `BLOCKED_BY_V3` và dừng.
- Freeze V4 schemas, universe, three lookbacks và total trial budget 4.
- Chạy/hash baseline tests và V3 artifacts.

**A4**

- Viết hypothesis, mechanism, counterparty và invalidation trước code.
- Không xem partial V4 result trước spec lock.

#### Gate H26

```text
V4_AUTHORIZED
H_XSECT_MOM_V1_SPEC_LOCKED
TRIAL_BUDGET_4_LOCKED
UNIVERSE_AND_SIGNAL_CLOCK_LOCKED
```

### H26–H32 — Parallel foundation

**A2**

- Implement/test synchronized panel.
- Implement shared-capital rank/rebalance engine.
- Implement quantity rounding, reductions-before-increases và exposure checks.
- Wire funding/fees/slippage at leg level.

**A3**

- Implement portfolio ledger, beta, turnover, MDD và contribution metrics.
- Extend launch provenance/G1/G2a/G2b to portfolio experiments.
- Implement portfolio gate fixtures and report reconciliation.

**A4**

- Implement pure point-in-time ranking function and negative control.
- Unit-test lookbacks, ties, missing bars, rank direction và no-lookahead.

### H32–H35 — Integration checkpoint

Merge order:

1. A1 portfolio contracts.
2. A2 panel/shared-capital engine.
3. A4 rank signal.
4. A3 portfolio metrics/gates/runner.

#### Gate H35

```text
SYNCHRONIZED_PANEL_PASS
RANK_NO_LOOKAHEAD_PASS
SHARED_CAPITAL_INVARIANTS_PASS
FUNDING_AND_COST_RECONCILIATION_PASS
PORTFOLIO_PROVENANCE_PASS
FULL_TESTS_PASS
```

Fail gate H35: không chạy V4 scored matrix.

### H35–H41 — Stage A portfolio experiments

Chạy đúng bốn experiments:

```text
XSECT-MOM-3D
XSECT-MOM-7D
XSECT-MOM-14D
XSECT-REVERSE-7D-CONTROL
```

Rules:

- Ba chronological outer folds.
- Warmup ngoài scored folds.
- Shared capital duy nhất cho bảy symbols.
- Same frozen universe, execution, cost và funding model.
- Negative control không được chọn dù kết quả tốt.
- Mỗi experiment ghi complete launch manifest và portfolio ledger.
- Không rerun với parameter khác khi nhìn result.

### H41–H45 — Gates, stress và selection

Chỉ scored candidate vượt G0–G3 mới chạy:

- +50% fees.
- Two-tick adverse fill.
- Additional one-event delay.
- Drop-one-symbol.
- Drop-one-fold.
- Shared-capital risk limits.
- BTC beta/contribution checks.

Parameter-neighborhood rule:

- Ít nhất hai lookback liền kề trong `{3,7,14}` phải có positive portfolio
  expectancy sau costs.
- Chỉ một lookback dương là `PARAMETER_SPIKE_FAIL`.

### H45–H47 — Independent reproduction và lock decision

- Independent rerun 100% candidate đủ G0–G5.
- So order/position/portfolio digests, PnL, beta, turnover và drawdown.
- Áp pre-registered tie-break; chọn tối đa một candidate.
- Lock candidate hoặc reject/inconclusive family.
- Nếu lock: bắt đầu future S1 capture sau lock; chưa đánh giá S1.

### H47–H48 — Final audit và report

- A4 challenge memo: leakage, universe bias, rebalance/fill optimism, common-beta
  exposure và concentration.
- A3 reconcile experiments/artifacts/registry.
- A1 full tests, hashes, final verdict và next frontier.

---

## 23. V4 hard gates

### XG0 — Data/universe

- Seven-symbol panel và BTC benchmark clean trong declared window.
- No silent symbol/rebalance exclusion.
- Funding/metadata complete.
- Universe frozen trước result.

### XG1 — Point-in-time/leakage

- Feature bars completed before signal.
- Signal timestamp precedes every fill.
- Cross-sectional membership/ties deterministic.
- No execution-bar return in lookback.
- Warmup/train/test boundaries evidenced.

### XG2a/XG2b — Integrity/reproduction

- Portfolio manifest/hashes/ledger reconcile.
- Independent rerun matches orders, positions, portfolio PnL and metrics.

### XG3 — Stage A portfolio edge

- Portfolio canonical PnL >0 after commission/slippage/funding.
- Position-level PF ≥1.10.
- Portfolio expectancy-R >0.
- Ít nhất 2/3 folds có PnL và expectancy-R dương.
- Ít nhất 30 scored rebalances và 100 closed legs; thiếu là `INCONCLUSIVE`.
- Không fold đóng góp >50% positive aggregate PnL.
- Không symbol đóng góp >40% positive aggregate PnL.

### XG4 — Robustness/execution

- +50% fee, two-tick và extra-delay stresses vẫn có expectancy-R dương.
- Ít nhất hai adjacent lookbacks dương.
- Drop-one-symbol/fold không làm result phụ thuộc một observation duy nhất.
- Turnover không vượt pre-registered capacity budget.

### XG5 — Shared-capital risk

- Gross exposure ≤1.0.
- Absolute net exposure ≤0.10.
- Absolute weight/symbol ≤0.25.
- Không margin breach hoặc liquidation.
- Top-symbol contribution ≤40%.
- Absolute realized BTC beta ≤0.25; lớn hơn là `BETA_EXPOSURE_FAIL`.
- Maximum drawdown ≤10% cho candidate muốn lock S1.

Chỉ XG0–XG5 và independent rerun đều PASS mới được lock.

---

## 24. V4 score và selection

Giữ scorecard 100 điểm của V3 nhưng portfolio components phải dùng metric thật.

Additional scoring rules:

- Score chỉ tồn tại sau XG0/XG1/XG2a PASS.
- Final score chỉ tồn tại sau XG0–XG5 và XG2b PASS.
- Negative control luôn `CONTROL_ONLY`, không có selection rank.
- Candidate đủ gate cần score ≥70 để được cân nhắc lock.
- Tie-break duy nhất:
  1. highest median fold expectancy-R;
  2. lower turnover;
  3. lower maximum drawdown.

Không chọn theo highest total PnL đơn thuần.

---

## 25. V4 artifacts

```text
research/hypotheses/H-XSECT-MOM-v1/
  hypothesis.md
  candidate.yaml
  status.yaml

results/matrix/v4_xsect_mom/
  index.json
  report.json
  reconciliation.json
  experiments/

results/portfolio_v4/<experiment_id>/
  launch_manifest.yaml
  frozen/
  signal_ranks.parquet-or-jsonl
  orders.jsonl
  positions.jsonl
  portfolio_ledger.parquet-or-jsonl
  canonical_metrics.json
  beta_report.json
  contribution_report.json
  gate_result.json
  scorecard.json
  artifact_hashes.json

results/reproduction_v4/<verify_id>/
  rerun_manifest.yaml
  comparison.json
  run.log

research/wayfinder/evidence/sprint-v4-24h-<date>.md
```

---

## 26. Master final verdict

Final report phải tách:

```text
V3_PIPELINE_VERDICT
V3_TRANSITION = V4_AUTHORIZED | BLOCKED_BY_V3

V4_PIPELINE_VERDICT
V4_FAMILY_VERDICT = REJECTED | INCONCLUSIVE | LOCK_FOR_FUTURE_S1

S1
- candidate_locked:
- capture_started_after_lock:
- inspected_or_scored: no
```

Allowed master outcomes:

```text
V3_FAIL_V4_BLOCKED
V3_PARTIAL_V4_BLOCKED
V3_PASS_V4_CANDIDATE_FAIL
V3_PASS_V4_CANDIDATE_INCONCLUSIVE
V3_PASS_V4_LOCK_FOR_FUTURE_S1
```

Mục tiêu dài hạn vẫn là vòng lặp evidence-first:

```text
hypothesis → spec lock → point-in-time data → realistic execution
→ shared-capital walk-forward → hard gates → independent rerun
→ score survivors → future S1 → reject/shadow/promote
→ learn from immutable evidence → next hypothesis
```

---

## 27. Research references

- NautilusTrader, `Bar-Based Execution`:
  <https://nautilustrader.io/docs/nightly/concepts/backtesting/bar-execution/>
- NautilusTrader, `Backtest Execution Flow`:
  <https://nautilustrader.io/docs/latest/concepts/backtesting/execution-flow/>
- Liu, Tsyvinski, Wu, `Common Risk Factors in Cryptocurrency`, NBER Working
  Paper 25882: <https://www.nber.org/papers/w25882>
- Liu, Tsyvinski, `Risks and Returns of Cryptocurrency`, Review of Financial
  Studies: <https://doi.org/10.1093/rfs/hhaa113>

---

## 28. Post-sprint audit — verdict thực tế của V3/V4

### 28.1. Verdict được chấp nhận

```text
V3_ENGINEERING_VERDICT : PIPELINE_PASS_WITH_OPEN_AUDIT_DEBT
V3_CANDIDATE_VERDICT   : CANDIDATE_FAIL
V4_ENGINEERING_VERDICT : PIPELINE_PARTIAL_PASS
V4_FAMILY_VERDICT      : CANDIDATE_FAIL
S1_STATUS              : NOT_STARTED

CURRENT MASTER VERDICT : V3_PASS_V4_PARTIAL_CANDIDATE_FAIL
```

Không candidate V3/V4 nào được promote, shadow hoặc đọc S1. Kết luận
`H-XSECT-MOM-v1 REJECTED` được giữ nguyên; không được dùng các fix V5 để cứu,
chọn lại hoặc đổi tên candidate V4.

### 28.2. Phần đã làm tốt

1. V3 hoàn thành 98/98 cells, report/index/files reconcile, 17.320 entries có
   `signal_ts < fill_ts`, và 9/9 family cùng toàn bộ G3 survivors được rerun ở
   process riêng.
2. Candidate lock, launch manifest, argv/commit/dirty state và frozen hashes đã
   tiến bộ rõ rệt so với V1/V2.
3. V4 giữ đúng trial budget 3 scored + 1 reverse control; universe và spec được
   khóa trước scored runs.
4. V4 thật sự dùng shared-capital portfolio engine và đo được gross/net exposure,
   BTC beta, turnover, folds và MDD.
5. Current full suite được kiểm tra lại: `474 passed`, `0 failed`, `0 xfailed`.
6. Đội agent đã không promote một kết quả PnL dương nhưng rủi ro/tính ổn định
   không đạt. Đây là hành vi research đúng.

### 28.3. Findings bắt buộc sửa trước research mới

| ID | Severity | Finding | Tác động khoa học |
|---|---|---|---|
| F01 | **CRITICAL** | Aggregator đọc `canonical_pnl/pnl`, trong khi engine ghi `realized_pnl`; vì vậy `leg_pnls` và contribution theo symbol bị ghi 0 | XG3/XG5 và concentration không đáng tin |
| F02 | **CRITICAL** | Tính trực tiếp từ `positions.jsonl`: top-positive-symbol share của MOM 3D/7D/14D lần lượt khoảng 49,4%/64,4%/82,6%, nhưng artifacts báo 0% | Cả ba vượt hard limit 40% mà gate không bắt |
| F03 | **HIGH** | Mỗi fold reset về 100.000 USDT, sau đó equity segments được ghép như một curve; MDD trên curve ghép chưa phải shared-capital walk-forward liên tục | MDD và return path có thể bị méo tại fold boundary |
| F04 | **HIGH** | Positions còn mở ở cuối mỗi fold; total equity PnL gồm terminal mark/unrealized trong khi position PF/contribution chỉ dùng closed legs | PnL, PF và attribution không cùng một population |
| F05 | **HIGH** | Funding được engine áp vào state nhưng không có `funding_cashflows.jsonl`/decomposition trong V4 artifact | Không kiểm toán được edge đến từ price hay funding |
| F06 | **HIGH** | XG0 FAIL vì coverage payload/benchmark mapping không khớp evaluator; reason `funding_coverage_insufficient` đang được dùng cho BTC coverage | Verdict data gate sai semantics |
| F07 | **HIGH** | Portfolio không có stop/R definition nhưng PLAN yêu cầu expectancy-R; XG3 chắc chắn INCONCLUSIVE ngay từ thiết kế | Gate và hypothesis contract không tương thích |
| F08 | **HIGH** | Fee/two-tick/delay/drop-one stress chưa chạy; missing values lại hiển thị reason tên `*_negative` | Dễ hiểu nhầm “stress fail” với “stress chưa test” |
| F09 | **HIGH** | Gross target chỉ enforce lúc rebalance; actual gross drift 1,203–1,275, vượt cap 1,0 | Cả ba scored candidates fail shared-capital risk |
| F10 | **MEDIUM-HIGH** | Chỉ MOM-7D có independent rerun; không có candidate survivor nên đủ cho sample reproduction, nhưng chưa chứng minh toàn bộ matrix | Pipeline reproduction coverage còn hẹp |
| F11 | **MEDIUM-HIGH** | Không có `H-XSECT-MOM-v1/status.yaml`, V4 challenge memo độc lập hoặc report đúng path đã khai trong PLAN | Final scientific audit chưa đóng |
| F12 | **MEDIUM-HIGH** | A1 làm thay scope hypothesis/rank của A4 vì agent outage; final audit lại do A1 ký | Role separation của V4 không còn độc lập |
| F13 | **MEDIUM** | A4 V3 memo cuối cùng vẫn ghi `BLOCKED_BY_V3` trước khi reruns hoàn tất; không có addendum độc lập xác nhận 19/19 | V3 transition có machine evidence nhưng thiếu fresh reviewer sign-off |
| F14 | **MEDIUM** | Launch V4 ghi dirty worktree; reproducibility có capture nhưng code identity yếu hơn clean-commit launch | Khó tái dựng binary/code exact nếu diff thất lạc |
| F15 | **CRITICAL** | Kiểm tra lại 60 hashed files thấy 4/4 `run.log` không khớp `artifact_hashes.json`; runner hash trước rồi append verdict log | XG2a PASS không phản ánh artifact integrity thật |
| F16 | **CRITICAL** | V4 runner dựng sẵn XG1 booleans và `ArtifactIntegrityResult(...)=True` thay vì đo violation/hash/reconciliation thực tế | Leakage/integrity gates có thể PASS bằng constant |

### 28.4. Cách diễn giải kết quả V4

1. `MOM-7D +9.735 USDT` **không phải edge được xác nhận**. Nó chỉ là một
   diagnostic hint vì PF 1,028 <1,10; fold F2 âm lớn; top fold share 85,8%;
   true top-symbol share khoảng 64,4%; MDD 30,7%; gross cap bị vi phạm.
2. `MOM-7D` tốt hơn reverse control là thông tin về hướng ranking, nhưng một cặp
   so sánh không đủ để tuyên bố cơ chế có ý nghĩa thống kê.
3. MOM-3D và MOM-14D âm; do đó rule “hai adjacent lookbacks dương” không đạt.
4. Exact V4 economics phải được tính lại sau khi sửa accounting, nhưng rerun đó
   chỉ mang nhãn `DIAGNOSTIC_RECALC`; không có quyền đổi verdict V4.
5. Dù bỏ qua mọi bug accounting, gross violation, MDD và fold instability đã đủ
   để reject toàn bộ scored candidates.

---

## 29. Master objective Sprint V5 → V6

Thời lượng tối đa 48 giờ tiếp theo:

```text
V5 H0–H24  : SCIENTIFIC INTEGRITY CLOSURE
V6 H24–H48 : ONE BOUNDED NEW FAMILY, only if V5 PASS
```

Mục tiêu không phải “ép tìm ra strategy thắng”. Mục tiêu là:

1. biến portfolio engine thành một máy đo PnL/risk có thể kiểm toán;
2. đóng tất cả finding F01–F16 hoặc ghi blocker machine-readable;
3. chạy lại V4 ở chế độ diagnostic để chứng minh fix, không rescue candidate;
4. chỉ sau đó thử đúng một mechanism mới với trial budget khóa trước;
5. reject nhanh nếu evidence không đủ; lock tối đa một candidate cho future S1;
6. tiếp tục tuyệt đối không giao dịch tiền thật.

---

## 30. Four-agent ownership và scientific independence

| Agent | Vai trò duy nhất | Được sửa | Không được làm |
|---|---|---|---|
| **A1** | Coordinator, contract/trial-ledger owner, integrator | PLAN, schemas, locks, transitions, final merge | Không tự ký independent audit; không sửa result để đổi verdict |
| **A2** | Data + portfolio/execution accounting engineer | panel, engine, terminal liquidation, costs/funding, exposure controller | Không viết hypothesis verdict hoặc score threshold sau khi xem result |
| **A3** | Metrics/gates/reproduction engineer | canonical metrics, gates, DSR/PBO, rerun worker, reconciliation | Không thay hypothesis/spec sau lock |
| **A4** | Independent scientific auditor | challenge memo, audit scripts/read-only checks, final attestation | Không implement signal, engine, gates; không sửa scored artifacts |

Nếu một agent outage:

- A1 có thể nhận phần integration thuần kỹ thuật của A2/A3 sau handoff.
- Không ai được làm thay A4 rồi vẫn gọi kết quả là independent audit.
- Thiếu A4 thì transition là `INDEPENDENT_AUDIT_BLOCKED`; V6 không được mở.
- Mọi handoff ghi commit, file scope, tests, known limitations và conflict list.

---

## 31. Sprint V5 — scientific integrity closure

### 31.1. H0–H2 — freeze và baseline

**A1**

1. Hash toàn bộ artifacts V3/V4 hiện tại; snapshot là append-only.
2. Ghi current commit, dirty state, Python/Nautilus versions và exact test result.
3. Tạo `research/audits/v5/v3_v4_findings.json` gồm F01–F16.
4. Tạo global trial ledger: mọi scored run V1–V4 và mọi abandoned scored launch
   đều phải có trial identity; diagnostic/unit-test runs không trộn vào scored count.
5. Cấm overwrite `results/portfolio_v4` và `results/matrix/v4_xsect_mom`.

### 31.2. H2–H9 — canonical accounting contract

**A2 + A3, tách ownership**

Required identity cho từng fold và toàn experiment:

```text
ending_equity - starting_equity
= closed_price_pnl
+ terminal_unrealized_or_liquidation_pnl
+ funding_cashflows
- commissions
- modeled_spread_slippage
- liquidation_or_rejection_costs
```

Implementation requirements:

1. Chuẩn field duy nhất: `canonical_pnl`; adapter phải map `realized_pnl` rõ ràng,
   không fallback im lặng về 0.
2. Chọn và khóa một terminal policy trước diagnostic rerun:
   `FORCE_LIQUIDATE_AT_LAST_OBSERVABLE_BAR` là mặc định khuyến nghị. Nếu không
   liquidate, unrealized PnL phải là artifact riêng và tham gia PF/contribution
   theo rule đã khai.
3. Persist `funding_cashflows.jsonl`, commission, slippage, rejected orders và
   terminal-close rows; tất cả reconcile tới equity trong tolerance `1e-9` scale.
4. Contribution theo symbol/fold phải dùng cùng canonical population với PnL.
5. Walk-forward curve phải dùng continuous capital hoặc chain fold returns
   mathematically; tuyệt đối không ghép raw 100k-reset curves rồi tính MDD.
6. Mỗi cost/risk metric có estimator/version string và reason code khi missing.
7. Missing là `NOT_TESTED`/`METRIC_MISSING`, không dùng reason `*_negative`.
8. XG1 lấy counters/timestamps từ rows thật; XG2a phải hash/schema/reconcile sau
   khi mọi file writer/logger đã đóng. Không truyền constant `True` vào scored gate.
9. `artifact_hashes.json` được tạo cuối cùng; không file đã hash nào được append
   sau đó. Registry/index bên ngoài experiment directory được reconcile riêng.

### 31.3. H9–H14 — data, execution và risk contract

**A2**

1. XG0 đọc trực tiếp clean intersection + actual panel coverage; benchmark BTC có
   `benchmark_coverage_incomplete`, không giả làm funding failure.
2. Funding cadence lấy từ actual settlement timestamps theo từng symbol; không
   hard-code mọi contract luôn 8h.
3. Persist actual funding rate selected at each settlement và prove rate publication
   timestamp `<= decision/settlement timestamp`.
4. Implement cost stresses: fee ×1,5; baseline one tick → adverse two ticks;
   one additional 15m event delay.
5. Implement drop-one-symbol và drop-one-fold diagnostics.
6. Implement risk mode versioned:

```text
target_gross = 0.80
hard_gross_cap = 1.00
hard_abs_net_cap = 0.10
exposure_check = every_completed_15m_bar
breach_action = deterministic_reduce_only
```

Risk mode này chỉ dùng cho engine validation và future V6 spec. Không áp ngược
để rescue H-XSECT-MOM-v1.

### 31.4. H14–H18 — family-aware metrics và multiple testing

**A3**

1. Không bịa expectancy-R cho portfolio không có stop. Portfolio gate v5 dùng:
   after-cost daily returns, position PF, median fold return, MDD, turnover,
   concentration và explicit ex-ante gross risk budget.
2. Sharpe dùng daily net returns, risk-free 0, estimator version frozen.
3. DSR dùng global scored-trial count, distribution/variance Sharpe của toàn bộ
   scored trials, sample length, skewness và kurtosis; không chỉ dùng số
   candidate còn sống hoặc chỉ truyền một con số trial count.
4. PBO/CSCV chỉ xuất verdict khi số strategies và partitions đủ điều kiện đã
   pre-register; nếu không thì `NOT_ENOUGH_CONFIGURATIONS`, không PASS giả.
5. Unit fixtures phải bắt được:
   - top-symbol share 64% không thể thành 0%;
   - reset-fold curve không thể đi qua MDD gate;
   - terminal open positions không thể biến mất khỏi reconciliation;
   - funding/fee/slippage thiếu phải fail closed;
   - missing stress không được ghi thành negative stress.

### 31.5. H18–H21 — immutable V4 diagnostic recalculation

Chạy đúng bốn V4 specs bằng code đã sửa vào namespace mới:

```text
results/matrix/v4_recalc_diagnostic_v5/
results/diagnostic_v5/<experiment_id>/
```

Rules:

1. experiment ids thêm suffix `-DIAG-V5`; registry kind=`DIAGNOSTIC_RECALC`;
2. trial count không tăng vì không dùng để select, nhưng phải link source trial;
3. không sửa candidate/status/verdict V4;
4. compare old/new PnL, PF, MDD, funding, costs, concentration và terminal effects;
5. rerun tất cả bốn ở separate processes và compare digests;
6. bất kỳ mismatch chưa giải thích được làm V5 fail.

### 31.6. H21–H24 — independent audit và transition

**A4** chỉ đọc artifacts sau khi A1 tuyên bố code freeze:

1. adversarial audit leakage, accounting identity, fold construction, fill delay,
   costs, funding PIT, global trials, reason semantics và reproduction;
2. random sample tối thiểu 50 orders, 50 positions, 30 funding settlements và
   toàn bộ fold boundaries; sample seed/hash khóa trong manifest;
3. xác nhận current V3/V4 artifacts không đổi;
4. viết `challenge_memo_v5.md` và `scientific_audit_v5.json`;
5. ký một trong: `PASS`, `FAIL`, `INDEPENDENT_AUDIT_BLOCKED`.

---

## 32. V5 completion gate — không waiver

```text
V5-C01 current_full_tests_pass_no_xfail
V5-C02 v3_v4_source_artifacts_hash_unchanged
V5-C03 global_scored_trial_ledger_complete
V5-C04 canonical_leg_pnl_field_reconciles
V5-C05 total_pnl_cost_funding_terminal_identity_reconciles
V5-C06 terminal_position_policy_frozen_and_evidenced
V5-C07 continuous_capital_or_chained_return_wfa_valid
V5-C08 mdd_recomputed_from_valid_equity_path
V5-C09 symbol_and_fold_contribution_use_canonical_pnl
V5-C10 funding_cashflows_persist_and_reconcile
V5-C11 commission_and_slippage_persist_and_reconcile
V5-C12 xg0_coverage_and_reason_semantics_correct
V5-C13 actual_funding_settlement_cadence_supported
V5-C14 fee_twotick_delay_stresses_execute
V5-C15 dropone_symbol_and_fold_execute
V5-C16 gross_net_exposure_controller_passes_fixtures
V5-C17 family_aware_portfolio_metrics_no_fake_r
V5-C18 missing_not_tested_and_negative_are_distinct
V5-C19 v4_diagnostic_recalc_four_of_four_complete
V5-C20 independent_reproduction_four_of_four_match
V5-C21 matrix_report_index_registry_reconcile
V5-C22 a4_independent_scientific_audit_pass
V5-C23 no_live_money_change
V5-C24 no_s1_read_or_score
V5-C25 artifact_hashes_verified_after_all_writes
V5-C26 xg1_xg2_use_measured_evidence_no_true_constants
```

Transition:

```text
if all(V5-C01..V5-C26):
    V6_TRANSITION = V6_AUTHORIZED
else:
    V6_TRANSITION = BLOCKED_BY_V5
```

`BLOCKED_BY_V5` là terminal condition. Không được “chạy V6 thử trước”.

---

## 33. Sprint V6 — one bounded new family

### 33.1. Selected frontier

```text
H-XSECT-FUNDING-CARRY-v1
```

Đây là mechanism mới: dùng funding đã **settle và publish** để đo crowding/carry
tương đối giữa symbols; không dùng OI chưa đủ history và không sửa/tune momentum
V4. Positive funding nghĩa long trả short, nên hypothesis long nhóm funding thấp
và short nhóm funding cao nhằm thu net funding trong portfolio market-neutral.

Đây chỉ là prior kinh tế. Funding có thể đổi nhanh và price move có thể lớn hơn
carry; không được coi funding rank tự nó là edge.

### 33.2. Pre-registration draft

A1 tạo spec draft; chỉ được `SPEC_LOCKED` sau V5 PASS và trước signal code/scored
run. Contract tối thiểu:

```yaml
hypothesis_id: H-XSECT-FUNDING-CARRY-v1
family: cross_sectional_funding_carry
stage: S0_EXPLORATORY
universe: [ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, DOGEUSDT, LINKUSDT, ADAUSDT]
benchmark: BTCUSDT
signal_clock: daily_00_00_utc
feature: trailing_mean_of_published_settled_funding_only
lookback_days: [1, 3, 7]
long: bottom_2_funding
short: top_2_funding
rebalance: 24h
split_policy: chronological_3fold_with_24h_purge_embargo
target_gross: 0.80
hard_gross_cap: 1.00
net_target: 0.00
max_abs_weight_per_symbol: 0.20
trial_budget:
  scored: 3
  negative_control: 1
negative_control: reverse_funding_rank_3d
```

Không thêm momentum, OI, volatility filter, regime filter, per-symbol parameter,
extra lookback hoặc rebalance interval trong version 1.

### 33.3. Mechanism-specific invalidation

Candidate bị reject nếu một điều sau xảy ra:

1. total canonical PnL sau mọi costs/funding `<=0`;
2. net funding cashflow `<=0` hoặc dưới 2/3 folds có funding cashflow dương;
3. price PnL bù cho funding âm rồi strategy vẫn tự nhận là carry;
4. position PF `<1.10`, dưới 2/3 folds dương hoặc median fold return `<=0`;
5. chỉ một lookback dương, không có hai adjacent lookbacks dương;
6. top fold >50% positive aggregate PnL hoặc top symbol >40%;
7. MDD >10%, gross/net/weight cap bị breach hoặc |BTC beta| >0,25;
8. baseline không sống qua fee/two-tick/delay/drop-one stresses;
9. negative control thắng candidate tốt nhất;
10. DSR probability `<0.95` sau global multiple-trial adjustment;
11. bất kỳ gate data/PIT/integrity/reproduction/audit FAIL/INCONCLUSIVE.

---

## 34. V6 execution schedule — H24 đến H48

### H24–H27 — spec, data và lock

- A1 xác minh `V6_AUTHORIZED`, freeze global trial count và spec.
- A2 xác minh actual settlement timestamps, panel/universe và benchmark.
- A3 freeze metric/DSR estimators, hard gates và score thresholds.
- A4 chỉ review contract conflict; không code signal.

### H27–H33 — implementation và hand fixtures

- A2 implement funding panel + shared-capital engine adapter.
- A3 implement family metrics/gates/reproduction.
- A1 implement pure funding-rank signal hoặc nhận handoff riêng; signal code
  hoàn thành sau spec lock, không được đổi spec.
- Full unit/property tests; no scored run.

### H33 gate

```text
DATA_AND_FUNDING_PIT_PASS
CANONICAL_ACCOUNTING_PASS
SHARED_CAPITAL_RISK_PASS
COST_AND_TERMINAL_RECONCILIATION_PASS
FULL_TESTS_PASS
TRIAL_BUDGET_4_LOCKED
```

Fail bất kỳ mục: dừng V6.

### H33–H39 — four scored experiments

```text
XSECT-FUND-CARRY-1D
XSECT-FUND-CARRY-3D
XSECT-FUND-CARRY-7D
XSECT-FUND-REVERSE-3D-CONTROL
```

Không chạy experiment thứ năm. Không sửa universe, weights, costs hoặc lookback
sau khi thấy partial PnL.

### H39–H44 — gates, stresses và global selection adjustment

- evaluate hard gates trước score;
- chạy stresses chỉ cho candidate qua base data/integrity/edge gates;
- DSR dùng toàn global trial ledger;
- PBO/CSCV chỉ diagnostic nếu đủ cấu hình;
- negative control không bao giờ eligible.

### H44–H47 — independent reproduction và audit

- A3 rerun 100% base survivors ở separate process;
- nếu không survivor, rerun ít nhất best diagnostic + control để kiểm tra pipeline;
- A4 audit sau code/result freeze và không nhận summary chọn lọc từ A1;
- A4 xác nhận trial budget, PIT, funding identity, terminal handling và no tuning.

### H47–H48 — final verdict

A1 chỉ tổng hợp từ machine artifacts + A4 attestation; không tự đổi gate.

---

## 35. V6 hard gates

### FG0 — Data/universe

- 7/7 traded symbols + BTC benchmark sạch trong declared common window;
- actual settlement coverage/cadence complete;
- tick/step/min-notional metadata point-in-time hoặc frozen limitation;
- không silent skip/replacement; universe freeze trước result.

### FG1 — PIT/leakage

- funding feature chỉ dùng settlements có publication timestamp `<= signal_ts`;
- bars dùng làm mark/feature completed trước signal;
- signal trước fill; execution bar không vào feature;
- warmup nằm ngoài scored folds; purge/embargo 24h giữa folds; toàn bộ boundaries
  được evidence.

### FG2a/FG2b — Integrity/reproduction

- canonical accounting identity + hashes + registry reconcile;
- independent rerun match orders, positions, funding, costs, equity, metrics và
  digests trong tolerance khóa trước.

### FG3 — Base edge

- PnL >0; funding cashflow >0; PF ≥1,10;
- 2/3 folds PnL dương và 2/3 folds funding dương;
- median fold return >0;
- ít nhất 90 scored daily rebalances và 100 canonical terminal/closed legs;
- top fold ≤50%, top symbol ≤40%;
- daily net Sharpe ≥0,50 chỉ để đủ sample score; DSR vẫn là selection gate.

### FG4 — Robustness

- fee ×1,5, adverse two ticks, extra 15m delay vẫn PnL/funding mechanism dương;
- two adjacent lookbacks dương;
- drop-one-symbol và drop-one-fold không làm sign flip ở mọi trường hợp;
- turnover/capacity budget không breach.

### FG5 — Shared-capital risk

- gross ≤1,00; |net|≤0,10; |weight/symbol|≤0,20 ở mọi completed bar;
- không margin breach/liquidation;
- MDD ≤10%; |BTC beta|≤0,25;
- top-symbol contribution ≤40%.

### FG6 — Selection bias + audit

- DSR probability ≥0,95 với global trial count;
- trial ledger complete và append-only;
- A4 scientific audit PASS;
- no unresolved HIGH/CRITICAL finding.

Chỉ FG0–FG6 PASS và score ≥75 mới được lock cho future S1.

---

## 36. V6 scorecard — 100 điểm chi tiết

Hard gate luôn đứng trước score. Candidate có 100 điểm nhưng một hard gate FAIL
vẫn bị reject; metric missing làm component 0 và có reason code.

### A. Data & point-in-time — 15 điểm

- 5: 7 symbols + BTC + funding coverage/cadence complete.
- 5: không lookahead; signal/fill/warmup/fold evidence đầy đủ.
- 5: universe, metadata, manifest và hashes freeze trước run.

### B. Accounting & cost truth — 15 điểm

- 5: total/canonical/fold/terminal equity identity reconcile.
- 5: commission, slippage và rejected-order decomposition reconcile.
- 5: funding cashflows persisted, PIT-valid và reconcile theo symbol/fold.

### C. Chronological edge — 20 điểm

- 5: after-cost total PnL >0.
- 5: position PF ≥1,20; 3 điểm nếu 1,15–<1,20; 1 điểm nếu 1,10–<1,15.
- 5: 3/3 folds dương; 3 điểm nếu đúng 2/3.
- 5: daily Sharpe ≥1,00; 3 điểm nếu 0,75–<1,00; 1 điểm nếu 0,50–<0,75.

### D. Risk & concentration — 15 điểm

- 5: MDD ≤6%; 4 điểm nếu >6–8%; 2 điểm nếu >8–10%.
- 5: không gross/net/weight/margin violation.
- 5: top symbol ≤30% và top fold ≤40%; 3 điểm nếu vẫn trong hard limits
  symbol ≤40% và fold ≤50%.

### E. Robustness & execution — 15 điểm

- 6: fee/two-tick/extra-delay cùng dương, mỗi stress 2 điểm.
- 4: drop-one-symbol và drop-one-fold sạch, mỗi nhóm 2 điểm.
- 3: turnover/capacity budget pass.
- 2: ít nhất hai adjacent lookbacks dương.

### F. Multiple testing — 10 điểm

- 6: DSR probability ≥0,99; 4 điểm nếu 0,975–<0,99; 2 điểm nếu 0,95–<0,975.
- 2: global scored-trial ledger complete/append-only.
- 2: PBO ≤25% nếu estimable; nếu không đủ configs thì 0 điểm và
  `NOT_ENOUGH_CONFIGURATIONS`, không phạt hard gate riêng.

### G. Reproduction & scientific audit — 10 điểm

- 5: independent rerun all-match.
- 3: A4 audit PASS và không có unresolved HIGH/CRITICAL finding.
- 2: matrix/report/index/registry/status artifacts reconcile.

Selection:

```text
eligible = all(FG0..FG6 PASS) and score >= 75
tie_break = highest_DSR_then_lower_MDD_then_lower_turnover
max_locked_candidates = 1
```

---

## 37. S1 và promotion rule

1. S0 hiện tại đã bị dùng nhiều lần; không gọi bất kỳ đoạn nào trong đó là
   untouched OOS.
2. Chỉ sau khi một V6 candidate được khóa mới tạo future S1 start timestamp.
3. S1 không backfill, không inspect trong V6, không đổi candidate sau capture.
4. S1 tối thiểu phải đủ duration/trades pre-register; thiếu sample là
   `WAIT_FOR_MORE_DATA`, không PASS/FAIL sớm.
5. Promotion vẫn cần Stage B: after-cost PF ≥1,15, MDD ≤10%, shared-capital,
   stress/delay, DSR/global trials và signal-only observation; không live money.
6. Nếu V6 không có candidate, không tạo S1 giả. Chuyển sang hypothesis family
   mới ở sprint sau và tiếp tục thu future research reservoir riêng.

---

## 38. Required V5/V6 artifacts

```text
research/audits/v5/
  v3_v4_findings.json
  challenge_memo_v5.md
  scientific_audit_v5.json

results/matrix/v4_recalc_diagnostic_v5/
  index.json
  report.json
  reconciliation.json
  v5_transition.json

results/diagnostic_v5/<experiment_id>/
  launch_manifest.yaml
  accounting_reconciliation.json
  funding_cashflows.jsonl
  commission_slippage.json
  terminal_positions.jsonl
  canonical_metrics.json
  gate_result.json
  artifact_hashes.json

research/hypotheses/H-XSECT-FUNDING-CARRY-v1/
  hypothesis.md
  candidate.yaml
  status.yaml

results/matrix/v6_xsect_funding_carry/
  index.json
  report.json
  reconciliation.json
  final_transition.json

results/portfolio_v6/<experiment_id>/
  launch_manifest.yaml
  frozen/
  signals.jsonl
  orders.jsonl
  positions.jsonl
  terminal_positions.jsonl
  funding_cashflows.jsonl
  portfolio_ledger.jsonl
  accounting_reconciliation.json
  canonical_metrics.json
  beta_report.json
  contribution_report.json
  dsr_pbo_report.json
  gate_result.json
  scorecard.json
  artifact_hashes.json

results/reproduction_v6/<verify_id>/
research/audits/v6/challenge_memo.md
research/audits/v6/scientific_audit.json
research/wayfinder/evidence/sprint-v5-v6-master-20260824.md
```

---

## 39. Terminal outcomes

```text
V5_FAIL_V6_BLOCKED
V5_PASS_V6_PIPELINE_FAIL
V5_PASS_V6_CANDIDATE_FAIL
V5_PASS_V6_CANDIDATE_INCONCLUSIVE
V5_PASS_V6_LOCK_FOR_FUTURE_S1
```

Final report phải tách rõ:

```text
ENGINEERING_VERDICT
SCIENTIFIC_AUDIT_VERDICT
FAMILY_VERDICT
GLOBAL_TRIAL_COUNT
S1_STATUS
LIVE_MONEY_STATUS = UNCHANGED_DISABLED
```

---

## 40. Additional research basis

- Binance, funding payments/direction and variable settlement intervals:
  <https://academy.binance.com/en/articles/what-are-funding-rates-in-crypto-markets>
- Binance Developer Documentation, supported official APIs and historical market
  data: <https://developers.binance.com/en/docs/introduction>
- Cao, Zhai, Luo, `Anatomy of cryptocurrency perpetual futures returns`:
  <https://www.research.ed.ac.uk/en/publications/anatomy-of-cryptocurrency-perpetual-futures-returns/>
- Ackerer, Hugonnier, Jermann, `Fundamentals of Perpetual Futures`:
  <https://arxiv.org/abs/2212.06888>
- Bailey, López de Prado, `The Deflated Sharpe Ratio`:
  <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551>
- Bailey, Borwein, López de Prado, Zhu, `The Probability of Backtest
  Overfitting`: <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253>
