# Kế hoạch 5 ngày: hai AI agent dựng Quant Research Factory

**Repo:** `my-quantitative`  
**Thời lượng:** 4–5 ngày làm việc tập trung  
**Phạm vi chính:** Binance USD-M crypto perpetuals  
**Phạm vi phụ:** chuẩn bị interface cho Binance TradFi perpetuals, chưa nghiên cứu
scored nếu lịch sử/data contract chưa đủ  
**Môi trường:** research, signal-only và Testnet/Demo; không live money

---

## 1. Kết quả phải đạt sau 5 ngày

Sau sprint này, hai AI agent chưa cần tìm được một edge đủ để giao dịch. Kết quả
bắt buộc là một **Minimum Viable Research Factory** có thể:

1. Nhận một hypothesis có specification rõ ràng.
2. Tạo experiment manifest chứa code/config/data/split hashes.
3. Chạy nested chronological walk-forward có warmup và outer OOS riêng.
4. Tính canonical after-cost metrics nhất quán.
5. Chấm hard gates và score 100 điểm tự động.
6. Lưu cả PASS, FAIL và INCONCLUSIVE vào append-only registry.
7. Chạy end-to-end ít nhất một strategy pilot trên S0.
8. Tạo candidate bundle để sau này Agent B có thể kiểm tra trên future S1.
9. Giữ nguyên hard guard không cho live-money execution.

### Sprint được xem là thành công khi

```text
hypothesis spec
    → locked manifest
    → nested walk-forward
    → after-cost report
    → hard-gate verdict
    → scorecard
    → append-only registry
```

Toàn bộ chuỗi trên chạy lại được bằng một command và cho kết quả deterministic
trong tolerance đã khai báo.

### Không cố làm trong 5 ngày

- Không xây hàng chục strategy mới.
- Không tuyên bố có profitable edge từ S0.
- Không chạy live money.
- Không cố hoàn thiện native funding, order-book queue, empirical market impact
  và TradFi session model cùng lúc.
- Không tải và làm sạch mọi nguồn dữ liệu có thể có.
- Không dùng S1 để sửa strategy.

Các phần trên sẽ thành backlog sau sprint. Trong 5 ngày, correctness và auditability
quan trọng hơn số lượng experiment.

---

## 2. Hiện trạng và vấn đề phải xử lý

Repo đã có:

- NautilusTrader event-driven backtest.
- Bar catalog, funding, OI và mark-price data.
- Maker/taker fees và fill/slippage models.
- Nhiều strategy, per-symbol backtest và shared-capital portfolio backtest.
- Universe scan, baseline walk-forward, acceptance rules và risk limits.
- Wayfinder tickets, data snapshot, negative results và forward-test artifacts.
- 54 unit tests hiện tại pass.

Các lỗi thiết kế quan trọng nhất:

1. `research/optimize.py` chấm mỗi parameter combo trên toàn bộ fold rồi dùng chính
   toàn bộ fold để xếp hạng. Đây chưa phải nested walk-forward.
2. Optimizer cắt scored window nhưng chưa mang warmup đứng trước window vào như
   `baseline_wf.py`.
3. Sign-test trên sáu fold kết hợp BH-FDR trên hàng chục hypothesis gần như không
   thể pass. Với 6/6 fold dương, p-value nhỏ nhất chỉ `0.015625`; điều chỉnh khoảng
   58 tests vẫn không thể đạt `q <= 0.10` cho một survivor đơn lẻ.
4. Funding mới chủ yếu được cộng sau backtest; chưa tác động intrarun equity/margin.
5. Canonical PnL, PF, Sharpe và max drawdown chưa có một module duy nhất làm source
   of truth. Artifact có trường hợp PnL âm nhưng max drawdown bằng `0.0` cần audit.
6. Chưa có immutable experiment/trial registry.

Sprint tập trung sửa mục 1, 2, 3, 5 và 6. Mục 4 được ghi rõ là limitation, không
được che giấu bằng score.

---

## 3. Phân vai hai AI agent

### Agent A — Researcher / Strategy Engineer

Agent A chịu trách nhiệm:

- Hypothesis template và pilot hypothesis.
- Strategy/feature implementation.
- Lag-safe feature semantics.
- Warmup requirements của strategy.
- Unit tests cho signal, entry, exit và invalidation.
- Stage A execution trên S0.
- Viết report giải thích cả kết quả tốt và xấu.

Agent A không được:

- Đọc future S1 để tune.
- Tự sửa promotion threshold.
- Bỏ symbol/fold sau khi nhìn result.
- Tự phê duyệt candidate do mình viết.

### Agent B — Validator / Protocol and Risk Engineer

Agent B chịu trách nhiệm:

- Manifest, split registry và append-only trial registry.
- Nested walk-forward, purge/embargo/warmup enforcement.
- Canonical after-cost metrics.
- Leakage/reproducibility/golden tests.
- Hard gates và scoring engine.
- Independent review strategy của Agent A.
- Machine-readable PASS/FAIL/INCONCLUSIVE verdict.

Agent B không được:

- Sửa strategy parameter để làm validation đẹp hơn.
- Chạy lại cùng untouched holdout với phiên bản đã nhìn kết quả rồi gọi đó là OOS.
- Bỏ metric bất lợi khỏi report.
- Dùng tổng score để override hard gate.

### Quy tắc four-eyes

```text
Agent A ký: hypothesis + implementation đúng specification
Agent B ký: protocol + data + result có thể reproduce
```

Thiếu một chữ ký thì candidate chưa được `VALIDATED`.

---

## 4. Quy tắc làm việc song song

### Ownership file

Trong sprint, tránh hai agent cùng sửa một file:

| Vùng | Owner chính |
|---|---|
| `research/hypotheses/`, strategy pilot, feature code/config | Agent A |
| `research/protocol/`, scoring, manifests, validation tests | Agent B |
| `backtest/engine.py`, `reports/performance.py` | Chỉ sửa qua ticket bàn giao |
| `research/wayfinder/` decisions | Agent B merge, Agent A review |

Nếu cần sửa file thuộc owner khác:

1. Tạo ticket ghi interface/thay đổi mong muốn.
2. Owner thực hiện hoặc bàn giao ownership rõ ràng.
3. Không edit song song trên cùng file.

### Branch/worktree đề xuất

```text
agent-a/research-sprint
agent-b/validation-sprint
integration/five-day-sprint
```

Agent B là integration owner cho protocol artifacts, nhưng không được thay đổi
logic strategy của Agent A khi merge. Conflict về strategy trả lại Agent A; conflict
về protocol trả lại Agent B.

### Nhịp đồng bộ

- Đầu ngày: khóa interface và ticket ownership.
- Giữa ngày: báo blocker và artifact path, không gửi nhận xét chung chung.
- Cuối ngày: integration merge, test và ghi decision.
- Không mang code chưa pass unit test sang ngày tiếp theo nếu lỗi thuộc P0.

---

## 5. State machine tối giản cho sprint

```text
IDEA
  → SPEC_LOCKED
  → IMPLEMENTED
  → SCREENED_S0
  → VALIDATED_PIPELINE
  → LOCKED_FOR_FUTURE_OOS
```

Nhánh kết thúc khác:

```text
REJECTED        Không có edge hoặc fail hard gate.
INCONCLUSIVE    Sample/metric/data chưa đủ.
BLOCKED         Dependency chưa giải quyết.
```

S0 chỉ được dùng để kiểm tra pipeline và research screening. Không trạng thái nào
trong sprint được gọi là `PRODUCTION_READY` hoặc `LIVE_READY`.

---

## 6. Lịch thực hiện 5 ngày

## Ngày 1 — Khóa contract và dựng skeleton

### Agent A

1. Chọn đúng một pilot strategy hiện có; ưu tiên strategy đơn giản, đủ trades và
   đã có config, ví dụ frozen baseline thay vì tạo strategy hoàn toàn mới.
2. Viết `hypothesis.md` gồm:
   - economic mechanism;
   - universe bucket;
   - signal/entry/exit;
   - expected regimes;
   - invalidating evidence;
   - parameter budget;
   - benchmark;
   - warmup và maximum holding horizon.
3. Viết machine-readable `candidate.yaml`.
4. Kiểm tra strategy không dùng future bar/OI/funding.

### Agent B

1. Tạo `research/protocol/` skeleton:

```text
splits.py
manifests.py
registry.py
metrics.py
gates.py
scoring.py
```

2. Định nghĩa manifest schema.
3. Định nghĩa state enum và verdict reason codes.
4. Tạo append-only JSONL registry contract.
5. Ghi rõ S0 và future S1 semantics.

### Merge gate cuối ngày 1

- Hypothesis ID và config schema thống nhất.
- Split policy, canonical PnL fields và score input fields đã khóa.
- Manifest parser có unit tests.
- Không bắt đầu optimizer trước khi interface được merge.

### Artifact bắt buộc

```text
research/hypotheses/<id>/hypothesis.md
research/hypotheses/<id>/candidate.yaml
research/protocol/schema/experiment-manifest.schema.json
results/registry/README.md
```

---

## Ngày 2 — Nested walk-forward và canonical metrics

### Agent A

1. Bổ sung method khai báo:
   - warmup duration;
   - maximum holding horizon;
   - tunable parameter names;
   - frozen parameter defaults.
2. Viết tests cho signal tại boundary và first tradable bar sau warmup.
3. Tạo parameter grid nhỏ, tối đa 16–32 combinations.

### Agent B

1. Implement nested chronological walk-forward:

```text
outer train
  → inner validation chọn parameter
  → lock parameter
  → outer test chạy đúng một lần
```

2. Mang warmup bars vào mỗi fold nhưng loại warmup trades/PnL khỏi scored window.
3. Implement purge và embargo bằng maximum holding horizon.
4. Tạo canonical metrics:
   - after-cost PnL;
   - expectancy theo USDT và R;
   - position PF;
   - win/loss distribution;
   - Sharpe từ return series;
   - canonical max drawdown;
   - turnover/exposure;
   - funding adjustment status.
5. Nếu metric không tính được, trả `null + reason`, không tự thay `0.0`.

### Merge gate cuối ngày 2

- Test chứng minh outer-test không tham gia parameter selection.
- Test warmup không bị tính vào OOS metrics.
- Test PnL âm tạo drawdown âm/dương theo convention đã khai báo, không trả 0 giả.
- Hai rerun cùng seed có cùng selected params, orders và metrics.

---

## Ngày 3 — Hard gates, scoring và reproducibility

### Agent A

1. Chạy smoke diagnostic trên sample nhỏ.
2. Sửa implementation bugs, không sửa hypothesis để chạy theo result.
3. Viết expected failure cases:
   - missing funding;
   - insufficient warmup;
   - no trades;
   - inverted timestamps;
   - unsupported symbol.

### Agent B

1. Implement hard gates ở mục 8.
2. Implement score engine ở mục 9.
3. Implement block-bootstrap expectancy confidence interval bản tối thiểu.
4. Ghi số trials đã thử trong family.
5. Loại sign-test sáu fold khỏi promotion gate chính; nếu giữ lại thì chỉ báo như
   diagnostic.
6. Tạo golden run fixture và artifact hash comparison.

### Merge gate cuối ngày 3

- Raw metrics → subscores → total score reproducible bằng code.
- Missing metric không được silently pass.
- Candidate fail hard gate vẫn có scorecard nhưng verdict là FAIL.
- Registry không ghi đè entry cũ.
- Full unit/integration suite pass.

---

## Ngày 4 — End-to-end pilot trên S0

### Agent A

1. Khóa pilot candidate version.
2. Chạy Stage A nested WF trên S0 bằng declared parameter budget.
3. Viết report trước khi sửa bất kỳ hypothesis nào.
4. Phân tích theo symbol/fold/regime, kể cả negative results.

### Agent B

1. Audit manifest, data hashes, split boundaries và trial count.
2. Chạy độc lập lại cùng command/config.
3. So sánh fills, positions, PnL và scorecard.
4. Chạy baseline cost và +50% fee/slippage stress nếu pipeline cho phép.
5. Chạy shared-capital replay nếu pilot là multi-symbol.
6. Ra verdict:
   - `PIPELINE_PASS_CANDIDATE_FAIL`;
   - `PIPELINE_PASS_CANDIDATE_INCONCLUSIVE`;
   - `PIPELINE_PASS_LOCK_FOR_FUTURE_OOS`;
   - hoặc `PIPELINE_FAIL`.

### Merge gate cuối ngày 4

- End-to-end command exit code rõ ràng.
- Manifest và registry entry tồn tại.
- Agent A/B rerun khớp tolerance.
- Report không gọi S0 là untouched OOS.
- Không thay parameter sau khi nhìn S0 result trong cùng candidate version.

---

## Ngày 5 — Ổn định, tài liệu và bàn giao

Nếu chỉ có bốn ngày, các task P0 của ngày 5 phải làm ở cuối ngày 4; P1/P2 đưa vào
backlog.

### Agent A

1. Đóng gói pilot candidate bundle.
2. Viết guide tạo hypothesis mới theo interface đã hoàn thành.
3. Tạo backlog tối đa ba hypothesis family tiếp theo, chưa chạy mass scan:
   - funding/OI crowding;
   - BTC-beta-neutral residual momentum/reversal;
   - volatility compression/breakout.

### Agent B

1. Chạy full test suite và deterministic rerun.
2. Viết command runbook.
3. Khóa future S1 capture rule và parameter-lock timestamp.
4. Ghi known limitations:
   - post-trade funding vs native funding;
   - bar fill assumptions;
   - data-history limits;
   - missing empirical latency/slippage;
   - TradFi chưa đủ contract.
5. Tạo sprint verdict và prioritized backlog.

### Definition of Done cuối ngày 5

- Một pilot chạy end-to-end.
- Nested WF thực sự có outer test.
- Warmup/purge/embargo được test.
- Canonical metrics không silently default.
- Hard gate và score 100 điểm chạy bằng code.
- Manifest + registry + output hashes đầy đủ.
- Hai agent rerun giống nhau.
- S0 được ghi là screening only.
- Future S1 chưa bị tiêu thụ.
- Không live-money change.

---

## 7. Manifest và bàn giao

### Experiment manifest tối thiểu

```yaml
experiment_id: EXP-YYYYMMDD-0001
hypothesis_id: CRYPTO-PILOT-001
candidate_version: 1
owner_agent: agent_a
validator_agent: agent_b
git_commit: <sha>
dirty_worktree: true_or_false
config_path: <path>
config_sha256: <sha256>
data_snapshot_id: S0-20260822
data_manifest_sha256: <sha256>
universe_snapshot: <path>
split_policy: NESTED-WF-V1
warmup_bars: <integer>
purge_bars: <integer>
embargo_bars: <integer>
outer_folds: <integer>
inner_folds: <integer>
parameter_combinations: <integer>
prior_family_trials: <integer>
cost_model: BINANCE-USDM-BASE-V1
funding_mode: post_trade_audit
random_seed: 42
started_at_utc: <timestamp>
lock_timestamp_utc: <timestamp>
```

### Agent A → Agent B

```text
candidate/<hypothesis_id>/v1/
  hypothesis.md
  candidate.yaml
  manifest.yaml
  stage_a_report.json
  known_limitations.md
```

Sau bàn giao, mọi code/config change tạo `v2`; không sửa evidence của `v1`.

### Agent B → Agent A

```text
validation/<hypothesis_id>/v1/
  validation_manifest.yaml
  gate_result.json
  scorecard.json
  robustness.json
  verdict.md
```

---

## 8. Hard gates trong sprint

Hard gate xét trước score. Một fail không được tổng điểm override.

### G0 — Data

- Không duplicate/unexplained gaps trong scored range.
- Timestamp semantics được khai báo.
- Feature joins point-in-time và lag-safe.
- Missing funding được fail-closed hoặc ghi candidate không đủ điều kiện after-
  funding promotion.
- Universe được freeze trước run.

### G1 — Leakage

- Outer-test không tham gia parameter selection.
- Stateful transform fit trên train.
- Warmup nằm ngoài scored metrics.
- Purge/embargo theo maximum holding horizon.

### G2 — Reproducibility

- Manifest, hashes và seed đầy đủ.
- Hai rerun sinh cùng selected params, positions và canonical PnL trong tolerance.

### G3 — Stage A candidate screen

- After-cost expectancy > 0.
- Aggregate PF ≥1.10.
- Ít nhất 2/3 outer folds dương.
- Ít nhất 20 trades/symbol combined, hoặc trả `INCONCLUSIVE`.
- Không fold có ≥5 trades nhưng PF <0.80.
- Không fold đóng góp >50% total PnL.

### G4 — Basic robustness

- +50% fee/slippage không làm aggregate expectancy âm.
- One-bar delayed fill được chạy nếu implementation đã hỗ trợ; nếu chưa thì
  candidate chưa được lock cho promotion, chỉ `PIPELINE_VALIDATED`.
- Parameter neighborhood không chỉ có một spike duy nhất.

### G5 — Portfolio, nếu multi-symbol

- Shared-capital PnL >0 và PF ≥1.10.
- Không vi phạm gross/concurrency/cluster/daily-loss limits.
- Không symbol đóng góp >40% PnL/risk.

Trong sprint, không có forward-test gate vì chưa đủ 6–8 tuần dữ liệu tương lai.

---

## 9. Scoring contract 100 điểm

### 9.1. Quy tắc

- Score chỉ xếp hạng candidate đã có hard-gate result.
- Candidate hard-gate FAIL vẫn được tính score để chẩn đoán, nhưng không promote.
- Dùng after-cost outer-OOS metrics.
- Không chấm win rate trực tiếp.
- Missing/NaN metric nhận 0 điểm và reason code.
- Agent B chạy scoring code; Agent A không nhập tổng điểm thủ công.

Hàm chuẩn hóa:

```text
unit(x, bad, good) = clip((x-bad)/(good-bad), 0, 1)
inverse_unit(x, good, bad) = clip((bad-x)/(bad-good), 0, 1)
```

### 9.2. Phân bổ

| Nhóm | Điểm |
|---|---:|
| A. Economic rationale/simplicity | 10 |
| B. Data/leakage integrity | 15 |
| C. Outer-OOS edge | 25 |
| D. Robustness | 15 |
| E. Cost/execution | 10 |
| F. Risk | 10 |
| G. Portfolio/diversification | 5 |
| H. Reproducibility/audit | 10 |
| **Tổng** | **100** |

### A. Economic rationale/simplicity — 10

| Thành phần | Điểm |
|---|---:|
| Mechanism/counterparty rõ | 0–4 |
| Hypothesis falsifiable trước run | 0–2 |
| ≤4 tunable params: 2; 5–8: 1; >8: 0 | 0–2 |
| Expected regimes và invalidation rõ | 0–2 |

### B. Data/leakage integrity — 15

| Thành phần | Điểm |
|---|---:|
| Coverage và anomaly checks | 0–3 |
| Timestamp/lag contract | 0–4 |
| Nested split, warmup, purge, embargo | 0–4 |
| Point-in-time universe | 0–2 |
| Snapshot hashes | 0–2 |

G0/G1 fail làm B=0 và verdict FAIL/INCONCLUSIVE bất kể tổng điểm.

### C. Outer-OOS edge — 25

Gọi:

- `E_R`: after-cost expectancy theo R-multiple.
- `PF`: position profit factor.
- `P_pos`: tỷ lệ outer folds dương.
- `C_top`: tỷ lệ absolute total PnL do fold lớn nhất đóng góp.

```text
expectancy_score    = 10 × unit(E_R, 0.00, 0.10)
pf_score            =  6 × unit(PF, 1.00, 1.25)
positive_fold_score =  5 × unit(P_pos, 0.50, 0.8333)
concentration_score =  4 × inverse_unit(C_top, 0.35, 0.60)
C_score             = tổng bốn thành phần
```

Ví dụ `E_R=0.06`, `PF=1.18`, `5/6 folds dương`, `C_top=0.40`:

```text
expectancy       = 10 × 0.60                 = 6.00
PF               =  6 × (0.18/0.25)         = 4.32
positive folds   =  5 × 1.00                 = 5.00
concentration    =  4 × ((0.60-0.40)/0.25)  = 3.20
C_score                                        = 18.52 / 25
```

### D. Robustness — 15

| Thành phần | Điểm |
|---|---:|
| Time/fold stability | 0–4 |
| Parameter neighborhood plateau | 0–4 |
| Drop-one-fold/symbol jackknife giữ dấu | 0–3 |
| Cross-symbol transfer với frozen params | 0–2 |
| Block-bootstrap expectancy CI | 0–2 |

Parameter neighborhood:

- ≥70% neighbors dương: 4.
- 50–69% neighbors dương: 2.
- <50%: 0.

Không chọn lại best neighbor; đây chỉ là phép đo plateau/spike.

### E. Cost/execution — 10

| Thành phần | Điểm |
|---|---:|
| Commission + slippage + funding baseline đầy đủ | 0–3 |
| +50% costs vẫn dương | 0–3 |
| One-bar delayed fill vẫn dương | 0–2 |
| Turnover/capacity report | 0–1 |
| Funding mode limitation báo đúng | 0–1 |

Nếu delayed-fill hoặc native funding chưa implement, component tương ứng bằng 0;
không dùng giả định tốt nhất để bù điểm.

### F. Risk — 10

Gọi `MDD` là canonical maximum drawdown theo tỷ lệ vốn:

```text
mdd_score = 5 × inverse_unit(MDD, 0.05, 0.15)
```

Phần còn lại:

| Thành phần | Điểm |
|---|---:|
| Không vi phạm risk/daily/circuit limits | 0–2 |
| Tail loss/expected shortfall report | 0–2 |
| Drawdown duration/recovery report | 0–1 |

Nếu drawdown extraction lỗi hoặc trả default 0, nhóm F bằng 0 và G2 fail.

### G. Portfolio/diversification — 5

| Thành phần | Điểm |
|---|---:|
| Shared-capital result dương/PF ≥1.10 | 0–2 |
| Không symbol/cluster concentration | 0–1 |
| Marginal diversification dương | 0–1 |
| Correlation stress nằm trong budget | 0–1 |

Single-symbol pilot chỉ có thể lấy tối đa 2/5 cho reporting/risk compatibility;
không giả vờ có diversification evidence.

### H. Reproducibility/audit — 10

| Thành phần | Điểm |
|---|---:|
| Complete manifest/hashes | 0–3 |
| Deterministic rerun | 0–3 |
| Golden integration test | 0–2 |
| Append-only registry gồm negative result | 0–2 |

### 9.3. Diễn giải tổng điểm trong sprint

| Điểm | Ý nghĩa | Hành động |
|---:|---|---|
| <50 | Pipeline/candidate yếu | Fix protocol hoặc reject |
| 50–59 | Diagnostic | Không lock candidate |
| 60–69 | Stage A research candidate | Có thể nghiên cứu tiếp trên S0 |
| 70–79 | Candidate đáng theo dõi | Có thể lock cho future S1 nếu G0–G4 pass |
| ≥80 | Strong research candidate | Vẫn phải chờ untouched future OOS |

Trong 5 ngày:

- Không score nào cho phép signal-only/Testnet vì chưa có future observation.
- Để `LOCKED_FOR_FUTURE_OOS`: tổng ≥70, C ≥15/25, B ≥12/15, H ≥8/10 và
  G0–G4 pass.
- Nếu sample thiếu, verdict `INCONCLUSIVE` dù tổng điểm tạm tính cao.

---

## 10. Command/runbook mục tiêu

Tên command có thể thay đổi trong implementation, nhưng cuối sprint cần tương
đương với:

```bash
# Validate hypothesis/config/manifest
python -m research.protocol.manifests validate \
  --candidate research/hypotheses/<id>/candidate.yaml

# Run nested Stage A on S0
python -m research.protocol.run \
  --candidate research/hypotheses/<id>/candidate.yaml \
  --snapshot S0-20260822

# Independent validation and scoring
python -m research.protocol.validate \
  --experiment-id <experiment_id>

# Reproduce from manifest
python -m research.protocol.reproduce \
  --manifest results/stage_a/<experiment_id>/manifest.yaml

# Full tests
python -m unittest discover -s tests -v
```

Mỗi command phải trả exit code khác nhau hoặc verdict reason rõ cho:

```text
PASS
FAIL
INCONCLUSIVE
MANIFEST_INVALID
DATA_INCOMPLETE
LEAKAGE_DETECTED
NON_REPRODUCIBLE
```

---

## 11. Backlog ngay sau sprint

Chỉ mở sau khi Definition of Done ngày 5 đạt:

### P0

- Native intrarun funding và parity với post-trade audit.
- Empirical latency/spread/slippage.
- Point-in-time universe history dài hơn.
- S1 future capture automation.

### P1

- Deflated Sharpe, PBO/CSCV và family-level Reality Check/SPA đầy đủ.
- Dynamic correlation clusters và portfolio attribution.
- Quote/trade/order-book candidate replay.

### P2

- Funding/OI crowding family.
- BTC-beta-neutral residual family.
- Volatility compression/breakout family.
- TradFi session/calendar/earnings contract.

---

## 12. Quyết định cuối cùng cho sprint

Trong 4–5 ngày, mục tiêu tốt nhất không phải “tìm thật nhiều edge”. Mục tiêu là
đưa hai agent vào một dây chuyền có separation-of-duties, nested OOS, hard gates,
scorecard và evidence registry. Khi dây chuyền này chạy đúng, việc mở rộng sang
nhiều hypothesis và nhiều mã mới có giá trị.

Một kết quả `PIPELINE_PASS_CANDIDATE_FAIL` vẫn là sprint thành công: hệ thống đã
loại đúng một false edge. Một backtest đẹp nhưng không có manifest, nested OOS và
reproducibility mới là thất bại.

