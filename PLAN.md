# PLAN.md — Sprint V2 24 giờ · 4 AI Agent · Correctness First

> **Dự án:** `my-quantitative` — Quant research cho Binance USD-M perpetuals
> **Thời lượng:** 24 giờ kể từ khi A1 phát lệnh bắt đầu
> **Môi trường:** research, signal-only, Testnet/Demo; tuyệt đối không live money
> **Điểm xuất phát:** Sprint V1 đã chạy 77 strategy–symbol combinations, không có
> candidate vượt gate; test suite hiện có 201 pass và 2 expected-fail
> **Mục tiêu Sprint V2:** biến pipeline từ “chạy được” thành “đo đúng, khóa đúng,
> tái lập được và không tự lừa mình”

---

## 1. Kết luận chính thức từ Sprint V1

### 1.1. Verdict bắt đầu Sprint V2

```text
PIPELINE_PARTIAL_PASS_CANDIDATE_FAIL
```

Ý nghĩa:

- Kiến trúc research loop, matrix, registry và lưu negative results đã hoạt động.
- Kết luận 0/77 candidate được promote nhiều khả năng đúng về phương hướng.
- Chưa được gọi pipeline là hoàn toàn validated vì canonical PF, G0/G1/G2,
  provenance, ETH coverage và hai LIVE guard còn vấn đề.
- Không candidate V1 nào được mang sang paper/live dưới nhãn confirmed edge.

### 1.2. Những gì phải giữ nguyên

1. Matrix cell độc lập, có thể resume và một cell fail không làm hỏng toàn run.
2. Registry append-only; không xóa `FAIL`, `INCONCLUSIVE` hay negative evidence.
3. Metric không tính được phải là `null + reason`, không giả thành `0.0`.
4. Trial budget được khai báo trước.
5. Không chạy iteration 2 trên cùng S0 chỉ để cứu candidate vừa thất bại.
6. Funding, cost và multi-symbol evidence tiếp tục là phần bắt buộc.

### 1.3. Sáu lỗi/thiếu sót P0 cần giải quyết

1. Aggregate PF đang được suy ra từ net PnL của fold thay vì gross wins/losses
   ở position level.
2. G0/G1 có check khai báo hoặc hard-code, chưa phải bằng chứng fail-closed.
3. G2 chưa được áp dụng cho từng candidate; config-hash mismatch không được gọi
   là “benign”.
4. Manifest chứa trường mutable, placeholder hoặc không phải actual SHA-256.
5. `environment: live` và YAML string `"false"` có thể đi qua safety parsing sai.
6. ETH có unexplained gaps; boundary intersection chưa chứng minh continuous
   coverage.

---

## 2. Definition of Done sau 24 giờ

Sprint V2 chỉ được coi là thành công khi hoàn thành các mục bắt buộc sau:

1. Hai LIVE guard regression tests chuyển từ `xfail` thành `pass`.
2. Canonical position-level PF có unit test với dữ liệu tay tính được.
3. G0/G1/G2 là evidence-backed và fail-closed; không có hard-coded PASS.
4. Mỗi scored run snapshot immutable config/candidate/data manifest trước khi
   chạy và lưu actual hashes, commit, dirty state, command, seed, lock time.
5. ETH được repair hoặc bị loại khỏi scored universe bằng reason code rõ; common
   clean intersection được tính lại.
6. 77 V1 cells được re-evaluate hoặc rerun dưới semantic V2; không ghi đè V1.
7. Registry V2 ghi đủ verdict và reason cho mọi declared cell.
8. Ít nhất một representative experiment G2 PASS từ immutable manifest.
9. Báo cáo phân biệt rõ `pipeline verdict` và `candidate verdict`.
10. Chỉ khi mục 1–8 PASS mới được implement/chạy H-FUNDCROWD exploratory.

Sprint vẫn thành công nếu corrected matrix tiếp tục có 0 candidate PASS.

### Không phải mục tiêu trong 24 giờ

- Không xác nhận production edge.
- Không triển khai live money.
- Không đánh giá future S1 ngay sau khi lock.
- Không thử vô hạn indicator, parameter hoặc symbol-specific tuning.
- Không bắt buộc phải tạo strategy mới nếu correctness work chưa hoàn thành.

---

## 3. Các nguyên tắc bất di bất dịch

1. **Correctness trước throughput:** sai metric thì dừng research.
2. **Hard gate trước score:** điểm cao không thể cứu một gate fail.
3. **Fail-closed:** thiếu bằng chứng là `NOT_YET_TESTED`, `INCONCLUSIVE` hoặc
   `FAIL`; không tự động PASS.
4. **Point-in-time:** không feature, universe, funding/OI join hoặc transform nào
   được dùng thông tin chưa tồn tại tại decision time.
5. **Immutable evidence:** không sửa artifact/spec của run cũ; thay đổi tạo
   version và experiment mới.
6. **No post-hoc rescue:** không thêm filter/regime sau khi nhìn kết quả để cứu
   candidate cùng version.
7. **No silent exclusion:** symbol/fold thiếu dữ liệu vẫn phải xuất hiện trong
   report với reason code.
8. **No S0 laundering:** S0 đã xem là development/screening data, không được đổi
   tên thành untouched OOS.
9. **Future S1 only:** candidate phải được khóa trước timestamp bắt đầu S1.
10. **No score shopping:** không thay weights/thresholds sau khi nhìn ranking.
11. **No trial-budget expansion:** hết budget thì reject/redesign ở sprint sau.
12. **No cross-market assumption:** crypto perpetual và equity/TradFi perpetual
    phải dùng universe, calendar, gaps, funding, leverage và risk contract riêng.
13. **No concurrent file ownership:** một file chỉ có một owner tại một thời điểm.
14. **No overwrite:** V2 ghi artifact/registry mới, giữ nguyên toàn bộ V1.

---

## 4. Research loop chuẩn

```text
Đọc negative evidence và market structure
        ↓
Viết hypothesis có cơ chế kinh tế và điều kiện bác bỏ
        ↓
Khóa spec, universe, parameter grid và trial budget
        ↓
Snapshot immutable inputs + hashes
        ↓
Audit dữ liệu point-in-time và common clean window
        ↓
Implement strategy + unit/integration tests
        ↓
Tier 0 compatibility smoke
        ↓
Stage A chronological walk-forward trên toàn declared matrix
        ↓
Canonical costs + funding + execution stress
        ↓
G0–G5 hard gates
        ↓
Chỉ xếp điểm những candidate đủ điều kiện
        ↓
REJECT / INCONCLUSIVE / LOCK_FOR_FUTURE_S1
        ↓
Lưu evidence bất biến và reason codes
        ↓
Học từ kết quả để viết hypothesis version tiếp theo
```

Loop có thể tiếp tục nhiều sprint, nhưng mỗi candidate chỉ được sử dụng future
S1 đúng theo protocol đã khóa.

---

## 5. Đội hình bốn agent

| Agent | Vai trò Sprint V2 | Ownership chính |
|---|---|---|
| **A1** | Coordinator, Safety và Contract Owner | plan, config parsing, LIVE guards, interface freeze, merge, final verdict |
| **A2** | Data Integrity và Coverage Engineer | data audit, ETH gaps, timestamps, funding/OI coverage, clean intersection |
| **A3** | Metrics, Backtest và Reproducibility Engineer | position metrics, gates, manifests, hashes, matrix V2, G2 rerun |
| **A4** | Quant Researcher và Independent Reviewer | negative-result analysis, hypothesis, strategy implementation, audit challenge |

### 5.1. Protected ownership

| Khu vực | Owner mặc định |
|---|---|
| `PLAN.md`, final report, integration decisions | A1 |
| `config/settings.py`, LIVE safety tests | A1 |
| `research/data_audit.py`, coverage artifacts, data contract | A2 |
| `research/sprint_eval.py`, gates, scorecard, manifest, registry | A3 |
| `strategy_*`, `research/hypotheses/` | A4 |
| Shared engine/runner | A1 giao một owner cụ thể trước khi sửa |

### 5.2. Quy tắc phối hợp

- Mỗi agent dùng branch/worktree riêng nếu hệ thống hỗ trợ.
- Không hai agent sửa cùng file trong cùng checkpoint.
- Mỗi handoff phải có: commit, files changed, command đã chạy, kết quả test,
  artifact path và limitation.
- A4 là người phản biện độc lập cho A3; A3 là người kiểm định độc lập cho A4.
- A1 không tự hạ gate để kịp deadline.
- Block quá 45 phút phải báo exact error, command, evidence và phương án hẹp nhất.
- Sau H20 chỉ bugfix, reproduction, docs và integration; không feature mới.

---

## 6. Lịch thực thi 24 giờ

### H0–H4 — P0 Safety và immutable provenance

#### A1 — Safety

- Chuẩn hóa `environment` bằng enum/case-normalization trước validation.
- Reject giá trị environment không thuộc allowlist.
- YAML boolean phải là boolean thật; reject string `"true"`, `"false"`, `"0"`,
  `"1"` thay vì ép bằng `bool(value)`.
- Chuyển hai expected-fail regression tests thành PASS.
- Chạy targeted tests và full test suite.

#### A3 — Provenance

- Snapshot config và candidate spec vào experiment directory trước run.
- Tính SHA-256 từ bytes của snapshot thực tế.
- Ghi actual git commit và dirty-worktree state tại thời điểm launch.
- Ghi exact argv/command, seed, runner version và dependency versions cần thiết.
- `parameter_lock_utc` phải sớm hơn scored run start.
- Candidate research status được lưu riêng, không sửa frozen spec.

#### Gate H4

```text
LIVE_GUARDS_PASS
IMMUTABLE_MANIFEST_TEST_PASS
NO_MUTABLE_CONFIG_REFERENCE
```

Nếu gate H4 fail: dừng matrix và hypothesis mới.

### H4–H9 — Canonical metrics và evidence-backed gates

#### A3 — Position-level accounting

- Persist từng closed position hoặc tối thiểu gross winning PnL, gross losing
  PnL, net PnL và trade count sau commission/funding/slippage.
- Aggregate PF từ positions, tuyệt đối không aggregate từ fold net PnL.
- Thêm hand-calculated regression fixtures cho winner-only, loser-only, mixed,
  no-trade và funding-changing-sign cases.
- Phân biệt `undefined` với `infinite PF`; không dùng số vô cực để tự động PASS.

#### A2/A3 — G0/G1/G2

- G0 đọc coverage/data manifest thật, không hard-code catalog/metadata PASS.
- Funding completeness phải kiểm tra toàn scored window.
- G1 lưu evidence cho split, warmup, transforms, selection, universe freeze và
  point-in-time joins.
- G2 so config hash, selected parameters, position digest và canonical PnL.
- Hash mismatch là `G2_FAIL`, kể cả khi PnL tình cờ giống nhau.

#### Gate H9

```text
POSITION_PF_REGRESSION_PASS
G0_FAIL_CLOSED_PASS
G1_EVIDENCE_TEST_PASS
G2_REPRODUCTION_TEST_PASS
```

Nếu gate H9 fail: không chạy lại 77 cells.

### H9–H14 — Data repair/decision và corrected V1 matrix

#### A2 — Data contract

- Liệt kê chính xác ETH gaps: start, end, duration, expected bars, actual bars.
- Phân loại gap: exchange outage, downloader failure, listing boundary hoặc
  unexplained.
- Repair từ nguồn canonical nếu có thể và lưu source/checksum.
- Nếu không repair được, loại ETH khỏi scored matrix hoặc dời scored boundary
  theo rule được khai báo trước.
- Báo riêng:
  - boundary intersection;
  - continuous clean intersection;
  - per-symbol gap completeness;
  - funding completeness.

#### A3 — Matrix V2

- Re-evaluate/rerun toàn bộ 77 declared V1 cells bằng semantic đã sửa.
- V1 artifact chỉ đọc; V2 có experiment/matrix ID mới.
- Mỗi cell có một trong các trạng thái:
  `COMPLETED`, `DATA_INCOMPLETE`, `PIPELINE_ERROR`, `NON_REPRODUCIBLE`.
- Registry append đủ 77 entries hoặc reason rõ cho cell chưa chạy.
- Xuất bảng so sánh V1/V2 cho PF, expectancy, gate và verdict.

#### Gate H14

```text
DATA_CONTRACT_RESOLVED
MATRIX_COMPLETED_OR_EXPLAINED = 77/77
V1_ARTIFACTS_UNCHANGED
```

Nếu matrix chưa hoàn tất do correctness issue, ưu tiên sửa/rerun và bỏ phần
hypothesis mới của sprint.

### H14–H18 — Execution realism và survivor validation

Chỉ chạy cho candidate vượt corrected G0–G3:

- Baseline fees và funding.
- +50% fee stress.
- One-tick và two-tick adverse fill.
- One-bar delayed entry để loại bar-close fill optimism.
- Parameter neighborhood theo grid đã pre-register.
- Drop-one-fold và drop-one-symbol sensitivity.
- BTC-beta-neutral contextual benchmark khi dữ liệu/implementation hỗ trợ.
- Shared-capital replay nếu có hơn một survivor.

Không có survivor thì ghi `NO_SURVIVOR`; không nới gate.

### H18–H22 — H-FUNDCROWD exploratory, có điều kiện

Chỉ bắt đầu nếu H4, H9 và H14 đều PASS.

#### Spec correction trước khi lock

- Nếu chỉ dùng funding percentile thì tên family là `funding_crowding`.
- Chỉ gọi `funding_oi_crowding` khi OI thực sự đi vào signal point-in-time.
- Threshold `{70, 75, 80}` với HTF fixed ON là **3 combinations**, không phải 4.
- Ghi rõ counterparty, expected mechanism, holding horizon, invalidation,
  costs, universe và stop condition.
- Đây là S0 exploratory/nested selection, không phải S1/OOS.

#### A4 implement; A2/A3 kiểm định

- A4 viết spec trước khi xem kết quả và implement feature lag-safe.
- A2 xác minh funding publication timestamps và không forward-fill qua tương lai.
- A3 chạy đúng declared grid, ghi trial count toàn family và chấm gate.
- Chọn tối đa một candidate để lock; không có candidate thì reject family version.

### H22–H24 — Freeze, S1 capture và final handoff

- Feature freeze tuyệt đối.
- Nếu có candidate đủ điều kiện: freeze code, config, universe, data boundary,
  hashes và lock timestamp.
- Bắt đầu thu thập future S1 sau lock; chưa chấm S1 trong sprint này.
- A3 independent rerun một representative corrected experiment từ manifest.
- A4 challenge report: tìm leakage, selection bias và execution optimism còn sót.
- A1 chạy full tests, kiểm tra artifact completeness và phát final verdict.

---

## 7. Experiment manifest bắt buộc

Mọi scored run phải snapshot và lưu tối thiểu:

```yaml
schema_version: 2
experiment_id: EXP-YYYYMMDD-NNNN
matrix_id: MATRIX-YYYYMMDD-NNNN
hypothesis_id: <family-and-sequence>
candidate_version: <integer>
strategy_type: <name>
owner_agent: <A1-A4>
validator_agent: <A1-A4>

run_started_utc: <timestamp>
parameter_lock_utc: <timestamp-before-run>
git_commit_at_launch: <sha>
dirty_worktree_at_launch: <true-or-false>
exact_argv: [<argv-items>]
random_seed: <integer>

frozen_config_path: <artifact-local-path>
frozen_config_sha256: <actual-sha256>
frozen_candidate_path: <artifact-local-path>
frozen_candidate_sha256: <actual-sha256>
data_manifest_path: <artifact-local-path>
data_manifest_sha256: <actual-sha256>
universe_snapshot_path: <artifact-local-path>
universe_snapshot_sha256: <actual-sha256>

requested_start_utc: <timestamp>
requested_end_utc: <timestamp>
actual_start_utc: <timestamp>
actual_end_utc: <timestamp>
continuous_clean_intersection: <boundaries-or-null>
split_policy: <id>
warmup_bars: <integer>
purge_bars: <integer>
embargo_bars: <integer>
outer_folds: <integer>

declared_parameter_combinations: <integer>
executed_parameter_combinations: <integer>
prior_family_trials: <integer>
fee_model: <id>
slippage_model: <id>
funding_mode: <native-or-audited-post-trade>
```

Artifact directory phải chứa frozen inputs, raw positions/cells, canonical
metrics, gate result, diagnostic/final scorecard, log và artifact hashes.

---

## 8. Canonical metric contract

### 8.1. Canonical PnL

```text
canonical_position_pnl
= realized gross trading PnL
- commission
- modeled spread/slippage
+/- funding cashflows
- declared latency/session penalties nếu có
```

Mọi component phải có timestamp, currency và sign convention rõ.

### 8.2. Position-level Profit Factor

```text
gross_profit = sum(max(position_pnl, 0))
gross_loss   = abs(sum(min(position_pnl, 0)))
PF           = gross_profit / gross_loss
```

Rules:

- Aggregate trực tiếp từ positions thuộc scored set.
- Không lấy trung bình PF của fold.
- Không chia tổng positive-fold net PnL cho negative-fold net PnL.
- Không có lệnh thua: PF là `null/infinite_with_reason`, không tự động PASS khi
  sample nhỏ.
- Không có trade: toàn bộ trade metrics là `null + NO_TRADES`.

### 8.3. Metrics bắt buộc

- Closed trades, gross profit, gross loss, expectancy USDT và expectancy R.
- Position PF, win rate, average winner/loser.
- Net PnL, return, max drawdown và drawdown duration.
- Exposure, turnover, holding time và funding contribution.
- Per-fold, per-symbol, per-quarter/regime metrics.
- Positive-fold ratio, top-fold contribution, top-symbol contribution.
- Drop-one-fold/symbol sensitivity.

---

## 9. Hard gates

Hard gate có bốn trạng thái:

```text
PASS
FAIL
INCONCLUSIVE
NOT_YET_TESTED
```

Chỉ `PASS` cho phép đi tiếp. Không dùng boolean mặc định để biến thiếu bằng chứng
thành PASS.

### G0 — Data integrity

- Không duplicate hoặc unexplained gap trong scored window.
- Timestamp semantics và publication lag được khai báo.
- OHLCV, funding và metadata đủ cho toàn scored window.
- Universe snapshot và continuous clean intersection tồn tại.
- Mỗi exclusion có reason code trước khi xem strategy result.

### G1 — Leakage và research protocol

- Test fold không tham gia parameter/feature/universe selection.
- Transform chỉ fit trên training segment.
- Warmup nằm ngoài scored observation set.
- Purge/embargo phù hợp holding horizon nếu cần.
- Current-bar signal không được giả định fill cùng close nếu không chứng minh.
- Config, universe và grid được freeze trước scored run.

### G2 — Reproducibility

- Immutable manifest và actual hashes đầy đủ.
- Independent rerun khớp frozen parameters.
- Position digest và canonical PnL khớp tolerance đã khai báo.
- Config/candidate/data hash mismatch là FAIL.

### G3 — Stage A edge

- After-cost/funding expectancy > 0.
- Position PF ≥ 1.10.
- Ít nhất 2/3 chronological folds dương.
- Ít nhất 20 closed trades mỗi required symbol; thiếu là `INCONCLUSIVE`.
- Không fold có ≥5 trades nhưng PF < 0.80.
- Không một fold đóng góp >50% positive total PnL.
- Required symbol âm không được che bằng average toàn universe.

### G4 — Robustness và execution

- Baseline và +50% fee stress vẫn có expectancy dương.
- Two-tick hoặc one-bar-delay stress theo declared execution model vẫn dương.
- Parameter neighborhood không phải single-point spike.
- Drop-one-fold/symbol không làm kết luận đổi dấu bất thường.
- Mọi stress dùng cùng frozen candidate; không retune.

### G5 — Portfolio

- Shared-capital PnL >0 và position PF ≥1.10.
- Không vi phạm gross exposure, concurrency, cluster hoặc daily-loss limits.
- Một symbol không đóng góp quá 40% portfolio PnL/risk.
- Có contextual benchmark; BTC-beta-neutral khi phù hợp.

### Future gates — chưa thể PASS trong Sprint V2

- Future S1 untouched evaluation.
- Tổng sample đủ lớn, ví dụ ≥100 closed trades theo contract được khóa.
- PF/MDD threshold cho promotion.
- 6–8 tuần shadow/signal-only stability.

Các mục này phải là `NOT_YET_TESTED`, không được suy ra từ S0.

---

## 10. Cách chấm điểm 100 điểm

### 10.1. Luật chấm

1. Candidate fail G0, G1 hoặc G2: `UNRANKED_PROTOCOL_FAIL`.
2. Candidate fail/inconclusive G3: có thể nhận `diagnostic_score`, nhưng không
   nằm trong survivor leaderboard.
3. `final_research_score` chỉ có khi G0–G5 đều PASS.
4. Missing metric nhận 0 ở component tương ứng và phải có reason code.
5. Weights và bands được khóa trước run; không đổi sau khi xem kết quả.
6. Score chỉ xếp hạng survivor, không thay verdict của hard gate.

### 10.2. Bảng điểm chi tiết

#### A. Economic rationale và simplicity — 10 điểm

| Thành phần | Điểm tối đa | Cách chấm |
|---|---:|---|
| Cơ chế kinh tế rõ | 3 | 0: không có; 1: mô tả chung; 2: mechanism cụ thể; 3: mechanism + điều kiện tồn tại/biến mất |
| Counterparty/nguồn edge | 2 | 0: không rõ; 1: giả thuyết; 2: nêu ai trả edge và vì sao |
| Falsifiable trước run | 2 | 0: hậu nghiệm; 1: có invalidation mơ hồ; 2: điều kiện bác bỏ định lượng |
| Simplicity/trial discipline | 3 | 0: quá budget; 1: nhiều knobs; 2: bounded grid; 3: ít knobs và trial accounting đầy đủ |

#### B. Data và leakage integrity — 15 điểm

Chỉ chấm khi G0/G1 PASS.

| Thành phần | Điểm tối đa |
|---|---:|
| Continuous coverage + funding completeness | 4 |
| Timestamp/publication-lag evidence | 4 |
| Train/test/warmup/purge correctness | 4 |
| Frozen point-in-time universe và exclusions | 3 |

Mỗi mục chỉ nhận toàn điểm khi có artifact/test dẫn chứng; khai báo bằng lời nhận
0 cho mục đó.

#### C. Chronological edge quality — 25 điểm

| Metric | Band | Điểm |
|---|---|---:|
| Expectancy R/trade | ≤0 / (0,.03) / [.03,.05) / [.05,.10) / ≥.10 | 0 / 2 / 4 / 6 / 8 |
| Position PF | <1.10 / 1.10–1.14 / 1.15–1.24 / 1.25–1.49 / ≥1.50 | 0 / 2 / 4 / 6 / 7 |
| Positive folds | <2/3 / 2/3 / 3/3 | 0 / 3 / 5 |
| Closed trades | <20 / 20–49 / 50–99 / ≥100 | 0 / 1 / 2 / 3 |
| Flat after-cost benchmark | không thắng / thắng | 0 / 2 |

Nếu project chưa chuẩn hóa R/trade, component expectancy nhận 0 và report phải
hiện `MISSING_R_NORMALIZATION`; không thay bằng USDT threshold tùy symbol.

#### D. Robustness theo time/symbol/parameter — 15 điểm

| Thành phần | Điểm tối đa | Cách chấm |
|---|---:|---|
| Fold stability | 4 | 0 nếu fail G3; 2 nếu 2/3 dương; 4 nếu 3/3 và không concentration fail |
| Symbol breadth | 4 | 0 nếu required symbol fail; 2 nếu ≥70% dương; 4 nếu ≥85% dương |
| Parameter neighborhood | 4 | 0 spike; 2 mixed nhưng median dương; 4 neighborhood ổn định |
| Drop-one sensitivity | 3 | 0 đổi dấu; 1 mong manh; 3 vẫn dương và verdict giữ nguyên |

#### E. Cost và execution realism — 10 điểm

| Thành phần | Điểm tối đa |
|---|---:|
| Baseline commission/slippage/funding đầy đủ | 3 |
| +50% fee stress vẫn dương | 2 |
| Two-tick adverse fill vẫn dương | 2 |
| One-bar delay vẫn dương | 2 |
| Capacity/turnover limitation được ghi | 1 |

#### F. Risk quality — 10 điểm

| Thành phần | Điểm tối đa |
|---|---:|
| MDD nằm trong pre-registered budget | 4 |
| Drawdown duration/recovery chấp nhận được | 2 |
| Tail loss và worst-fold không vi phạm limit | 2 |
| Exposure/leverage không vi phạm limit | 2 |

Risk limits cụ thể phải nằm trong candidate spec trước run; không tạo threshold
sau khi thấy equity curve.

#### G. Portfolio/diversification — 5 điểm

| Thành phần | Điểm tối đa |
|---|---:|
| Shared-capital replay PASS | 2 |
| Top-symbol contribution ≤40% | 1 |
| Cluster/concurrency limits PASS | 1 |
| Benchmark/BTC-beta-neutral context | 1 |

#### H. Reproducibility/auditability — 10 điểm

| Thành phần | Điểm tối đa |
|---|---:|
| Immutable inputs + hashes | 3 |
| Independent position/PnL rerun match | 4 |
| Exact command/commit/seed/environment | 2 |
| Append-only registry và reason codes | 1 |

### 10.3. Diễn giải tổng điểm

| Điểm | Ý nghĩa tối đa |
|---:|---|
| `<50` | Reject/redesign |
| `50–59` | Diagnostic only |
| `60–69` | Exploratory candidate; chưa được lock |
| `70–79` | Có thể lock cho future S1 nếu mọi G0–G5 PASS |
| `80–100` | Strong research candidate; vẫn chưa phải confirmed edge |

Một candidate 90 điểm nhưng fail G1 vẫn là `UNRANKED_PROTOCOL_FAIL`.

---

## 11. H-FUNDCROWD contract cho lần thử tiếp theo

Trước khi `SPEC_LOCKED`, agent phải sửa các điểm sau:

```yaml
family: funding_crowding
feature: point_in_time_funding_percentile
thresholds: [70, 75, 80]
htf_filter: true
declared_parameter_combinations: 3
oi_overlay: false
stage: S0_EXPLORATORY
```

Nếu thêm OI:

- Tạo candidate version mới.
- Chứng minh OI timestamp và publication delay.
- Không backfill/forward-fill qua thời điểm chưa biết.
- Cập nhật trial budget trước run.

Output hợp lệ chỉ gồm:

```text
REJECTED
INCONCLUSIVE
STAGE_A_PASS_EXPLORATORY
LOCK_FOR_FUTURE_S1
```

Không dùng `EDGE_CONFIRMED`, `PRODUCTION_READY` hoặc `LIVE_READY`.

---

## 12. Future S1 protocol

S1 không phải một file dữ liệu cũ được đổi nhãn. S1 là dữ liệu xuất hiện **sau**
khi candidate đã được khóa.

Trình tự bắt buộc:

1. Candidate vượt G0–G5 trên development/S0.
2. Freeze code, parameters, universe, costs, risk limits và hashes.
3. Ghi `parameter_lock_utc`.
4. Bắt đầu capture dữ liệu sau timestamp đó.
5. Không xem/tune theo S1 trong thời gian tích lũy.
6. Chỉ đánh giá khi đạt observation/trade/time budget pre-registered.
7. Chấm một lần; fail thì reject version, không sửa rồi dùng lại cùng S1.

---

## 13. Required artifacts Sprint V2

```text
results/registry/experiments.jsonl

results/matrix/<matrix_v2_id>/
  index.json
  coverage.json
  v1_v2_comparison.json
  report.json

results/stage_a/<experiment_v2_id>/
  manifest.yaml
  frozen/
    candidate.yaml
    config.yaml
    data_manifest.json
    universe.json
  positions.parquet-or-jsonl
  cells.jsonl
  canonical_metrics.json
  gate_result.json
  scorecard.json
  artifact_hashes.json
  run.log

research/hypotheses/<hypothesis_id>/
  hypothesis.md
  candidate.yaml

research/wayfinder/evidence/sprint-v2-24h-<date>.md
```

---

## 14. Stop conditions

Dừng research và chuyển sang correctness/reporting khi:

- Một trong H4/H9/H14 gate fail.
- Position-level accounting không reconcile với total canonical PnL.
- Data coverage/funding không đủ và chưa có pre-registered exclusion rule.
- Reproduction hash hoặc position digest mismatch.
- Trial budget đã hết.
- Có nguy cơ ghi đè V1/user artifacts.
- CPU/disk budget vượt limit A1 đã đặt.
- H20 đã tới.

Không tăng budget, đổi score band hoặc hạ hard gate để tạo survivor.

---

## 15. Final report bắt buộc

```text
SPRINT V2 VERDICT
- pipeline_status:
- candidate_status:
- blockers:

SAFETY
- live_guard_tests:
- typed_boolean_validation:
- live_money_changes: none

CORRECTNESS
- position_pf_test:
- G0_evidence:
- G1_evidence:
- G2_reproduction:

DATA
- universe_declared:
- universe_eligible:
- ETH_gap_resolution:
- continuous_clean_intersection:
- funding_completeness:

CORRECTED MATRIX
- completed/declared:
- V1_artifacts_unchanged:
- G0/G1/G2/G3/G4/G5_counts:
- top_rejection_reasons:
- V1_V2_metric_changes:

RESEARCH
- hypotheses_specified:
- trials_declared/executed:
- rejected:
- inconclusive:
- exploratory_survivors:
- locked_for_future_S1:

REPRODUCIBILITY
- manifest_hash:
- independent_rerun:
- position_digest_match:
- canonical_PnL_match:

TESTS
- passed:
- failed:
- xfailed:

NEXT ACTIONS
- P0:
- P1:
- P2:
```

Sprint-level verdict hợp lệ:

```text
PIPELINE_PASS_CANDIDATE_FAIL
PIPELINE_PASS_CANDIDATE_INCONCLUSIVE
PIPELINE_PASS_LOCK_FOR_FUTURE_S1
PIPELINE_PARTIAL_PASS_CANDIDATE_FAIL
PIPELINE_FAIL
```

---

## 16. Thứ tự ưu tiên sau Sprint V2

Nếu pipeline PASS nhưng không candidate:

1. Dùng rejection reasons để tạo hypothesis mới, không random indicator search.
2. Ưu tiên funding crowding đã sửa contract.
3. Sau đó mới xây portfolio engine cho cross-sectional reversal/momentum.
4. BTC-beta-neutral residual strategy chỉ chạy khi benchmark/hedge accounting
   đã chính xác.
5. Mỗi sprint chỉ mở bounded families và ghi cumulative family trial count.

Nếu có candidate được lock:

1. Bắt đầu future S1 capture.
2. Không sửa candidate.
3. Tiếp tục research family khác trên S0 nhưng cách ly hoàn toàn với S1.
4. Chờ đủ pre-registered S1 horizon trước khi đánh giá.

Đích dài hạn là một **research factory trung thực**, không phải một báo cáo có
equity curve đẹp: tìm ý tưởng, kiểm tra toàn diện, loại edge giả, giữ bằng chứng,
học từ thất bại và chỉ tin candidate sống sót qua dữ liệu tương lai.
