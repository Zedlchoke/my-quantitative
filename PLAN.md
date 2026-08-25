# SPRINT V8P → V8 → conditional V8X — Core Reversal and Breadth Expansion

> **Thời lượng tối đa:** 12 giờ kể từ `sprint_started_at_utc`.
>
> **Mục tiêu chính:** hoàn tất ba preparation gate còn thiếu `T12 → T13 → T14`, chạy đúng bốn trial V8 đã preregister, kiểm toán và đóng kết quả.
>
> **Mục tiêu phụ có điều kiện:** nếu V8 đóng hợp lệ và còn đủ thời gian, chạy breadth screen riêng trên 10 crypto có ít nhất một năm dữ liệu và, nếu data contract khả dụng, 10 US stocks có ít nhất một năm dữ liệu.
>
> **Nguyên tắc:** crypto và stocks là hai cohort độc lập. Không gộp session, funding, costs, PnL, DSR, PBO hoặc score giữa hai asset class.

---

## 0. Executive truth tại điểm bắt đầu

### 0.1 Trạng thái đã được kiểm chứng

- Parent terminal commit: `72eada1` (`V7P→V7 CLOSURE`). Khi triển khai, A1 phải đo lại `git rev-parse HEAD`; không hard-code commit này nếu HEAD đã tiến lên vì PLAN commit.
- V7P: `18/18 PASS` sau một remediation hợp lệ; A7 re-audit PASS.
- V7: chạy đúng `4/4` frozen trials; provenance CLEAN; reproduction `4/4 all-match`.
- V7 terminal: `V7_REJECT_ALL_CANDIDATE`.
- PF V7: khoảng `0.977 / 0.983 / 1.005 / 0.888`; tất cả dưới hard floor `1.10`.
- V7 không thất bại vì concentration; top positive fold và top positive symbol đều nằm trong cap.
- Global V6+V7 scored budget đã dùng đúng `8/8`; không có candidate được lock.
- Transition V7→V8 mới đạt `10/15`; blocker thực là:
  - `T12`: chưa có dedicated six-alt two-year data/PIT audit;
  - `T13`: chưa có weekly reversal dispatcher + golden end-to-end;
  - `T14`: chưa thể attest trước khi T12/T13 hoàn chỉnh.
- V8 chưa chạy và chưa thất bại. Trạng thái đúng: `V8_NOT_STARTED_PREP_GATES_T12_T13_T14_FAIL`.
- V8 core spec `H-XSECT-REVERSAL-v2` đã freeze hợp lệ tại commit `6533ce0`, trước scored V7 artifact đầu tiên. Các file spec đó là read-only.
- S1 chưa mở. Paper/live trading và order placement vẫn bị cấm.

Nguồn sự thật bắt buộc:

```text
CONTINUE.md
research/control/v7_twelve_hour_run/shutdown_report.json
research/audits/v7p/a7_terminal_audit.json
research/audits/v7/scientific_audit.json
research/audits/v8p/t01_t15_transition.json
research/wayfinder/evidence/sprint-v7p-v7-master-20260825.{md,json}
research/hypotheses/H-XSECT-REVERSAL-v2/*
```

### 0.2 Diễn giải khoa học

V7 là một sprint thành công về phương pháp nhưng family bị loại. Không được dùng PnL/PF V6 hoặc V7 để sửa V8, thêm filter, chọn symbol, đổi lookback hoặc nới hard gate.

V8 hỏi một câu độc lập: liệu altcoin thắng/thua tương đối có đảo chiều trong tuần kế tiếp hay không. Sprint mới sửa khả năng chạy và kiểm toán câu hỏi đã niêm phong; không phát minh câu hỏi khác để cứu kết quả cũ.

---

## 1. Scope, authority và điều cấm

### 1.1 Trong scope

1. Bootstrap topology mới từ commit sạch và gán agent/worktree thật.
2. Thực hiện dedicated V8 six-alt two-year data/PIT audit (`T12`).
3. Implement weekly Monday-00:00 dispatcher, runner path, golden vectors và full-surface tests (`T13`).
4. Tạo resolved V8 contract, baseline, manifest và A7 prelaunch attestation (`T14`).
5. Re-evaluate machine-readable `T01–T15`; chỉ launch khi `15/15 PASS`.
6. Chạy đúng bốn V8 core trials đã freeze, không trial thứ năm.
7. Chạy stress, independent reproduction, FG0–FG7, scorecard, DSR/PBO honesty và A7 terminal audit.
8. Preregister V8X trước scored V8 core artifact đầu tiên; data-only preparation được phép trong isolated worktrees.
9. Sau valid V8 terminal, conditionally chạy hai V8X cohorts độc lập:
   - `CRYPTO_USDM_1Y_10`;
   - `US_EQUITY_SPOT_1Y_10`, hoặc đóng blocker nếu stock data contract không khả dụng.
10. Cập nhật CONTINUE, MAP, registry, master report và shutdown report.

### 1.2 Ngoài scope

- Không mở, backfill, xem hoặc phân tích S1.
- Không paper/live trading, API đặt lệnh hoặc thay đổi live configuration.
- Không tuning từ V6/V7/V8 PnL đã thấy.
- Không sửa `H-XSECT-REVERSAL-v2` candidate/hypothesis/status để thêm symbol.
- Không gọi dữ liệu US equity spot là Binance perpetual.
- Không ghép bars underlying stock vào lịch sử Binance TradFi perpetual.
- Không gộp crypto và stocks thành một portfolio, score hoặc statistical cohort.
- Không dùng adjusted stock close làm execution price mà không có raw-price/corporate-action reconciliation.
- Không performance retry, replacement trial hoặc “thêm một lookback để xác nhận”.
- Không push remote nếu owner chưa yêu cầu.

### 1.3 Bất biến bằng chứng

- Artifact V6/V7 là lịch sử read-only. Correction chỉ được append bằng addendum có parent hash.
- Frozen V8 hash phải giữ nguyên byte-for-byte.
- Mọi universe V8X phải được chọn bằng rule freeze trước performance, không loại symbol theo PnL.
- Một trial đã publish bất kỳ scored metric nào sẽ tiêu thụ budget dù process sau đó lỗi.
- `EXIT=0` chỉ là pipeline success; không phải strategy PASS.
- `REJECT_ALL` là terminal hợp lệ. False promotion là failure nghiêm trọng.

---

## 2. Topology bắt buộc — real parallel agents, isolated worktrees

### 2.1 Nguyên tắc

A1 không được tự giả lập toàn bộ vai trò. Worktree chỉ được tính khi có branch, bootstrap SHA, allowed paths, forbidden paths, session identity thật, commit bàn giao và merge verdict.

Tạo topology mới; không tái sử dụng worktree V7 lịch sử:

| Role | Worktree đề xuất | Nhiệm vụ chính |
|---|---|---|
| A1 | root integration | controller, merge authority, state machine, resource owner |
| A2 | `../my-quantitative-v8-wt/a2-core-data` | T12 six-alt data/PIT/provenance audit |
| A3 | `../my-quantitative-v8-wt/a3-weekly-engine` | T13 weekly dispatcher/runner/artifacts |
| A4 | `../my-quantitative-v8-wt/a4-finalizer` | FG0–FG7, score, ledger, DSR/PBO cohort rules |
| A5 | `../my-quantitative-v8-wt/a5-reproduction` | independent reproduction, stress, reconciliation |
| A6 | `../my-quantitative-v8-wt/a6-contract-golden` | resolved contract, golden vectors, V8X preregistration |
| A7 | `../my-quantitative-v8-wt/a7-independent-audit` | prelaunch + terminal scientific audit; không viết production code |
| A8 | `../my-quantitative-v8-wt/a8-crypto-breadth` | 10-crypto universe/data audit, không đọc V8 metrics |
| A9 | `../my-quantitative-v8-wt/a9-equity-breadth` | stock provider/session/corporate-action data contract, không đọc V8 metrics |

Detached execution worktrees chỉ tạo sau attestation:

```text
../my-quantitative-v8-exec/rr1
../my-quantitative-v8-exec/rr2
../my-quantitative-v8-exec/rr3
../my-quantitative-v8-exec/rr4
../my-quantitative-v8x-exec/xr1
../my-quantitative-v8x-exec/xr2
```

### 2.2 Parallel và merge discipline

- A2–A6 chạy song song trên allowed paths không chồng lấn.
- A8–A9 chỉ chuẩn bị data/spec trong isolated worktrees trước V8 terminal; cấm đọc `results/portfolio_v8`, partial logs, metrics hoặc verdict.
- A7 chỉ audit integration SHA và artifacts; không nhận task sửa production.
- Merge V8 core: `A2 → A3 → A4 → A5 → A6`; targeted test sau từng merge, full suite sau integration.
- Sau valid V8 terminal mới merge V8X: `A8 → A9 → breadth integration follow-up`; A7 attest riêng.
- Không dùng `git add -A`, không reset/clean, không overwrite unrelated user changes.
- Tối đa hai heavy backtest/download workers đồng thời. Agent code/test nhẹ có thể song song nếu RAM/disk an toàn.

---

## 3. Lịch 12 giờ và phase boundary

| Thời gian tương đối | Phase | Công việc |
|---|---|---|
| 00:00–00:20 | Bootstrap | freeze start/deadline, clean SHA, worktrees, identities, manifest |
| 00:20–01:50 | V8P parallel | A2 T12; A3 T13; A4/A5/A6 gates/repro/contract; A8/A9 data-only prep |
| 01:50–02:40 | Integration | merge core theo thứ tự, targeted/full tests, resolved contract |
| 02:40–03:20 | T14 | baseline, manifest, A7 independent prelaunch audit |
| 03:20–03:55 | V8 Wave 1 | `XSECT-WREV-3D + XSECT-WREV-7D` |
| 03:55–04:30 | V8 Wave 2 | `XSECT-WREV-14D + XSECT-WMOM-7D-CONTROL` |
| 04:30–05:30 | V8 validation | stress, reproduction 4/4, FG0–FG7, score, ledger/statistics |
| 05:30–06:00 | V8 close | A7 terminal audit, V8 verdict, workers/PIDs reconciled |
| 06:00–06:30 | V8X gate | merge eligible breadth work, data audits, resolved contracts, A7 attest |
| 06:30–08:30 | V8X execution | tối đa bốn waves, hai heavy workers |
| 08:30–09:40 | V8X validation | stress/repro/score riêng từng cohort |
| 09:40–10:20 | Scientific close | A7 audit, cohort verdicts, master report |
| 10:20–12:00 | Reserve | remediation kỹ thuật không-performance, final reconciliation, hard shutdown |

Đây là budget, không phải deadline để bỏ test. Nếu remaining time không đủ hoàn tất audit/close, không launch phase hoặc wave tiếp theo. Hard stop tuyệt đối vẫn là 12 giờ.

---

## 4. V8P Gate T12 — six-alt two-year data audit

### 4.1 Universe read-only

```text
SOLUSDT, BNBUSDT, XRPUSDT, DOGEUSDT, LINKUSDT, ADAUSDT
BTCUSDT = benchmark measurement-only
```

Target window: common completed-bar intersection gần `2024-08-21T14:30Z → 2026-08-21T00:00Z`. A2 quyết định exact endpoints bằng dữ liệu, không bằng cách sửa target để né gap.

### 4.2 T12 PASS contract

A2 phải tạo machine-readable audit và chứng minh:

1. Đúng venue/instrument: Binance USD-M perpetual, quote USDT, contract metadata PIT.
2. 15m bar schema, timezone UTC và completed-bar semantics nhất quán.
3. Mỗi symbol có coverage ≥730 ngày mục tiêu hoặc exact common intersection hợp lệ theo frozen rule.
4. Zero duplicate timestamp; monotonic strict; OHLC/volume hợp lệ.
5. Gaps được census toàn bộ, phân loại explained/unexplained bằng rule freeze trước performance.
6. Không forward-fill price/funding qua unexplained gap.
7. Funding settlement coverage đủ toàn window và mapping đúng vị thế đang giữ.
8. Tick/step size và instrument metadata có effective timestamp hoặc limitation rõ ràng.
9. Hash SHA-256 cho từng source file, normalized dataset và manifest.
10. Universe không được thay đổi do PnL; thiếu một required symbol thì `T12_FAIL_DATA_INCOMPLETE`.
11. BTC benchmark không tham gia ranks/weights/PnL.
12. Data label là `S0_ALREADY_INSPECTED`, không phải untouched OOS.

Artifacts:

```text
research/audits/v8p/data_audit_v8.json
research/audits/v8p/data_manifest_v8.json
research/audits/v8p/gap_census_v8.json
research/audits/v8p/funding_coverage_v8.json
research/audits/v8p/t12_gate.json
```

---

## 5. V8P Gate T13 — weekly engine, golden và reproduction surface

### 5.1 Frozen behavior phải implement nguyên văn

- Signal clock: Monday `00:00 UTC`, chỉ dùng completed bars có timestamp ≤ cutoff.
- Lookbacks: đúng `3D, 7D, 14D`.
- Reversal: long bottom-2 losers, short top-2 winners.
- Control: long winners, short losers tại 7D.
- Hold/rebalance: bảy ngày, không discretionary intraweek rebalance.
- Target: gross 0.80, net 0; long 0.40, short 0.40; max abs symbol target 0.20.
- All-six eligibility; incomplete cross-section skip toàn rebalance.
- Fill tại next completed 15m event, one-tick adverse, fee 0.0005, native funding.
- Ba chronological folds; purge/embargo 7 ngày; warmup ≥14 ngày.

### 5.2 Tests bắt buộc

T13 chỉ PASS khi có unit + integration + golden tests chứng minh:

1. Monday schedule xử lý đúng UTC, year/month boundary và không tạo duplicate cutoff.
2. Không dùng bar đang hình thành hoặc future bar trong return rank.
3. Tie-breaking deterministic và freeze; missing symbol skip toàn rebalance.
4. Bottom/top legs đúng hướng cho reversal và control.
5. Signal cutoff và execution event tách rời; delay stress dịch đúng một event.
6. Fold boundary purge/embargo không leak position hoặc warmup.
7. Fee, slippage, funding, terminal liquidation và cash/equity identity đúng.
8. Golden normal/control có expected orders, weights, funding cashflows, ledger digest và metrics.
9. Runner CLI resolve đúng family, lookback, direction, output, registry và frozen hashes.
10. Reproduction harness rerun từ frozen artifacts và so ledger/equity/metrics/hash.
11. Full suite PASS trên `.venv/bin/python`; không claim system Python result.

Artifacts:

```text
research/audits/v8p/golden_vector_report_v8.json
research/audits/v8p/t13_gate.json
research/audits/v8p/test_report_v8p.json
```

---

## 6. Gate T14 và V8 launch authorization

A6 tạo resolved contract mới mà không sửa frozen YAML:

```text
research/audits/v8p/resolved_run_contract_v8.json
research/audits/v8p/baseline_root_v8.json
research/control/v8_run/worktree_manifest.json
research/control/v8_run/preflight.json
```

Resolved contract phải pin:

- exact four trial IDs;
- exact common data window/folds;
- candidate/config/data/golden hashes;
- final code-bearing launch SHA;
- output roots và registry shards duy nhất;
- costs, risk caps, stress surface và trial budget;
- prior global ledger count/digest;
- no S1/live/order capability;
- owned PID/resource/deadline contract.

A7 phải độc lập xác minh T12/T13, baseline, contract, manifest, clean worktrees và freeze lineage. `T14_PASS` yêu cầu `0 unresolved HIGH/CRITICAL`.

Trước launch, A1 regenerate machine-readable `T01–T15`. Tất cả `15/15 PASS`; không carry-forward boolean cũ mà không remeasure. Thiếu một gate: `V8_NOT_AUTHORIZED`.

---

## 7. V8 core execution — đúng bốn trial

| Wave | Trial 1 | Trial 2 |
|---|---|---|
| 1 | `XSECT-WREV-3D` | `XSECT-WREV-7D` |
| 2 | `XSECT-WREV-14D` | `XSECT-WMOM-7D-CONTROL` |

Rules:

- Mỗi trial chạy trong detached worktree tại cùng attested launch SHA.
- Stagger launch ≥5 giây; tối đa hai workers.
- Controller không đọc partial PnL để quyết định Wave 2.
- Wave chỉ hoàn tất khi artifact publish atomic và registry append thành công.
- Không performance retry. Pre-engine abort chỉ relaunch cùng trial khi zero scored artifact, output cũ archive và A7/contract cho phép.
- Lỗi sau scored metric tiêu thụ trial; không có replacement.

### 7.1 Stress và diagnostics bắt buộc

Cho mỗi normal trial:

- fee ×1.5;
- adverse +2 ticks;
- delay +1 event;
- drop-one-symbol cho đủ sáu symbols;
- drop-one-fold cho đủ ba folds;
- rebalance-day shift `+1 day` theo prereg diagnostics.

Stress cần path-dependent MDD/PF phải là engine rerun. Derived diagnostic không được giả làm full-path stress.

### 7.2 Core hard gates

Áp dụng FG0–FG7 và scorecard 100 điểm hiện có, cộng:

- net PnL >0 after fees/slippage/funding;
- PF ≥1.10; MDD ≤10%; all three folds net-positive;
- ít nhất hai adjacent lookbacks trong `[3D,7D,14D]` cùng PASS;
- top positive fold ≤50%; top positive symbol ≤40%;
- control không được thắng best reversal candidate;
- các stress bắt buộc vẫn dương;
- minimum weekly rebalances/legs được freeze trước score;
- reproduction `4/4 all-match`;
- DSR dùng daily returns và toàn global trial ledger;
- PBO chỉ tính trong comparable cohort. Unavailable phải fail-closed, không bịa.

### 7.3 V8 terminal outcomes

- `V8_STAGE_A_PASS_EXPLORATORY`: core hard gates PASS nhưng chưa đủ forward/statistical evidence.
- `V8_LOCK_FOR_FUTURE_S1`: chỉ khi mọi hard/statistical gate, valid PBO và A7 đều PASS; chỉ tạo future S1 contract, không mở S1.
- `V8_REJECT_ALL`: không candidate đạt; terminal hợp lệ.
- `V8_INVALIDATED`: integrity/lookahead/provenance/reproduction failure; quarantine results.
- `V8_NOT_STARTED_*`: preparation, topology, audit, resource hoặc time gate fail.

---

## 8. V8X preregistration — không sửa V8 core

V8X là breadth screen mới, không phải thêm symbol vào `H-XSECT-REVERSAL-v2`.

A6 phải freeze V8X specs, selection rules và hashes **trước scored V8 core artifact đầu tiên**. Nếu missed: `V8X_PREREG_WINDOW_MISSED`; không chạy V8X trong sprint này.

Artifacts prereg:

```text
research/hypotheses/H-XSECT-REVERSAL-BREADTH-CRYPTO-v1/*
research/hypotheses/H-XSECT-REVERSAL-BREADTH-EQUITY-v1/*
research/audits/v8x/v8x_spec_freeze.json
research/audits/v8x/v8x_novelty_and_independence.md
```

V8X tuyệt đối không được:

- dùng V8 core result để chọn universe/lookback/cost;
- gọi một năm là đủ promotion;
- thay đổi V8 core verdict;
- gộp two-year/six-alt V8 với one-year/breadth cohort trong PBO nếu không comparable.

---

## 9. V8X Cohort C — 10 Binance crypto USD-M có ≥1 năm

### 9.1 Universe selection freeze

Không chọn tay theo chart hoặc PnL. A8 áp dụng deterministic rule:

1. Binance USD-M `PERPETUAL`, quote `USDT`, status hợp lệ tại frozen cutoff.
2. `onboardDate ≤ window_start - 365 ngày`.
3. Có ≥365 ngày common 15m bars và native funding coverage.
4. Zero unexplained gap trong scored window; PIT metadata/hash đầy đủ.
5. Rank eligible symbols theo median daily quote volume trong 30 ngày **trước** scored window; lấy đúng top 10.
6. Lưu cả accepted và rejected universe để chống survivorship/cherry-pick.
7. Nếu dưới 10 symbol đạt: `V8X_CRYPTO_NOT_STARTED_DATA_INCOMPLETE`; không hạ gate.

Target window: common one-year intersection kết thúc không muộn hơn `2026-08-21T00:00Z`; exact endpoints do audit quyết định.

Execution contract crypto:

- 24/7 UTC; Monday 00:00 cutoff; next completed 15m fill;
- native funding; fee 0.0005; one-tick adverse;
- long bottom-2 / short top-2; gross 0.80, net 0;
- 3D/7D/14D reversal + 7D momentum control;
- three chronological folds, 7-day purge/embargo.

---

## 10. V8X Cohort E — 10 stocks có ≥1 năm, contract riêng

### 10.1 Hai instrument mode không được đánh tráo

**Mode A — `BINANCE_TRADFI_PERP_1Y`:** chỉ được chạy nếu có đúng 10 stock perpetual thực sự có ≥365 ngày Binance contract bars, funding và historical session coverage. Snapshot repo gần nhất có `0` mã đạt gate; vì vậy mode này dự kiến `NOT_STARTED_DATA_MATURITY` cho đến khi dữ liệu đủ. Không backfill bằng underlying spot.

**Mode B — `US_EQUITY_SPOT_1Y`:** được phép dùng data provider ngoài Binance nhưng phải mang label riêng. Default frozen basket, chọn trước performance:

```text
AAPL, MSFT, NVDA, AMZN, META, GOOGL, TSLA, AVGO, JPM, XOM
SPY = benchmark measurement-only
```

Provider contract:

- Preferred: official Alpaca historical stock bars hoặc owner-approved equivalent.
- Read-only market-data credentials chỉ lấy từ environment; không ghi/log/commit secret và không có trading permission.
- Nếu provider/credential/license không sẵn sàng: `V8X_EQUITY_NOT_STARTED_PROVIDER_BLOCKED`; không silent fallback sang nguồn không khai báo.
- Freeze provider, feed (`SIP`/`IEX`), adjustment mode, `asof`, calendar version và hashes trước score.
- Tải cả raw và corporate-action-adjusted views; reconcile splits/dividends/symbol changes.
- Signal dùng series đã điều chỉnh đúng contract; fill/PnL dùng raw tradable price với corporate-action cash/position adjustments.

### 10.2 Equity execution contract

- Chỉ regular US session theo official exchange calendar; xử lý holiday/early close fail-closed.
- Weekly signal dùng last completed regular-session close trước rebalance; fill next valid regular-session open.
- Không giả crypto Monday 00:00 UTC cho stocks.
- Fee/slippage/spread và short-borrow model freeze trước run; thiếu point-in-time borrow evidence thì outcome tối đa `MECHANISM_SCREEN_NON_EXECUTABLE`.
- Không funding; dividends, splits, borrow costs và overnight gaps phải được account riêng.
- Ba chronological folds theo trading sessions; purge/embargo ít nhất một holding week.
- Vì chỉ khoảng 52 weekly observations/năm, cohort này chỉ là exploratory breadth screen, không được lock cho S1/live.

---

## 11. V8X trial inventory, waves và statistical separation

### 11.1 Đúng tám trials

| Wave | Crypto trial | Equity trial |
|---|---|---|
| X1 | `V8X-C-WREV-3D` | `V8X-E-WREV-3D` |
| X2 | `V8X-C-WREV-7D` | `V8X-E-WREV-7D` |
| X3 | `V8X-C-WREV-14D` | `V8X-E-WREV-14D` |
| X4 | `V8X-C-WMOM-7D-CONTROL` | `V8X-E-WMOM-7D-CONTROL` |

Nếu equity cohort bị block, crypto có thể chạy một worker/wave sau khi A7 ghi `EQUITY_NOT_STARTED_*`; không được tạo replacement equity trials.

### 11.2 Không gộp kết quả

- Hai initial capitals, ledgers, cost models, calendars và scorecards riêng.
- DSR counts toàn global search history nhưng estimate riêng theo comparable return cohort.
- PBO crypto không chứa equities; PBO equities không chứa crypto.
- Không cộng PnL crypto+equity và gọi là portfolio diversification.
- Report có side-by-side comparison chỉ để mô tả, không tạo combined PASS.

### 11.3 V8X gates

Mỗi cohort phải riêng biệt đạt:

- data/PIT/session/corporate-action audit PASS;
- ≥48 scored weekly rebalances toàn window và minimum per fold freeze trước run;
- PF ≥1.10, MDD ≤10%, net PnL >0 after full asset-class costs;
- all three folds positive;
- two adjacent reversal lookbacks PASS;
- top fold ≤50%, top symbol ≤40%;
- fee/slippage/delay/drop-one stress không đảo kết luận;
- control không thắng reversal;
- independent reproduction 4/4 cho cohort đã chạy;
- A7 0 unresolved HIGH/CRITICAL.

Vì chỉ một năm dữ liệu, outcome tốt nhất:

- crypto: `V8X_CRYPTO_BREADTH_PASS_EXPLORATORY`;
- equity: `V8X_EQUITY_MECHANISM_PASS_EXPLORATORY` hoặc `MECHANISM_SCREEN_NON_EXECUTABLE` nếu borrow evidence thiếu.

Không outcome V8X nào tự authorize S1/live.

---

## 12. Điều kiện chuyển V8 → V8X — 12/12 bắt buộc

| Gate | PASS condition |
|---|---|
| X01 | V8 core chạy đúng 4/4 frozen trials hoặc có valid terminal scientific outcome |
| X02 | V8 outcome là PASS/LOCK/REJECT_ALL; không INVALIDATED/INCOMPLETE |
| X03 | V8 stress/reproduction/finalizer/registry hoàn chỉnh |
| X04 | A7 V8 terminal audit PASS, 0 HIGH/CRITICAL |
| X05 | V8 workers stopped, PIDs empty, Git sạch, master evidence complete |
| X06 | V8X specs/selection/cost rules freeze trước first V8 scored timestamp |
| X07 | A8 crypto ten-symbol audit PASS hoặc machine blocker rõ ràng |
| X08 | A9 equity provider/session/corporate-action audit PASS hoặc machine blocker rõ ràng |
| X09 | V8X engine/golden/reproduction tests PASS cho cohort được authorize |
| X10 | A7 V8X prelaunch attestation pins baseline/contract/manifest/launch SHA |
| X11 | Global trial ledger snapshot/digest và separate cohort mappings hoàn chỉnh |
| X12 | Còn ≥300 phút, disk ≥20 GB, RAM safe, max two workers, S1/live disabled |

Ít nhất crypto cohort phải được authorize để gọi `V8X_STARTED`. Equity blocker không được che giấu. Nếu remaining time <300 phút: data/spec artifacts có thể được giữ, nhưng không launch scored V8X.

---

## 13. Artifact contract

### V8 core

```text
research/control/v8_run/
research/audits/v8p/
research/audits/v8/
results/portfolio_v8/
results/reproduction_v8/
results/matrix/v8_xsect_weekly_reversal/
results/registry/shards/v8_*.jsonl
research/wayfinder/evidence/sprint-v8-master-*.{md,json}
```

### V8X breadth

```text
research/control/v8x_run/
research/audits/v8x/
data/v8x_manifests/
results/portfolio_v8x/crypto/
results/portfolio_v8x/equity/
results/reproduction_v8x/
results/matrix/v8x_crypto_weekly_reversal/
results/matrix/v8x_equity_weekly_reversal/
results/registry/shards/v8x_*.jsonl
research/wayfinder/evidence/sprint-v8x-master-*.{md,json}
```

Mọi artifact phải có schema version, UTC timestamps, source/launch SHA, parent hashes, candidate/config/data digests, execution identity và atomic-complete marker.

---

## 14. Unattended fail-safe

- Heartbeat mỗi 60 giây: phase, progress, owned PIDs, last artifact, disk/RAM, deadline.
- Heartbeat stale >10 phút: stop owned heavy workers, forensic event, không tự performance retry.
- Hard stop tuyệt đối sau 12 giờ; không tự gia hạn.
- Disk <20 GB, severe memory pressure, hash drift, dirty production tree, target collision hoặc foreign PID: dừng launch mới.
- Mỗi wave atomic; không đọc partial PnL để sửa wave sau.
- Network/rate-limit failure trước score có bounded retry theo data contract; không đổi provider im lặng.
- Failure sau scored metric tiêu thụ budget.
- Dù PASS/FAIL/timeout: stop heartbeat/workers, PID list rỗng, Git sạch, shutdown report và next safe action.
- Không S1, paper/live, API order keys hoặc order placement.

---

## 15. Definition of Done

### 15.1 V8P complete

- T12, T13, T14 đều PASS bằng machine-readable artifacts.
- Recomputed T01–T15 = `15/15 PASS` hoặc honest `V8_NOT_AUTHORIZED_*`.
- Full tests PASS, clean attested launch SHA và A7 0 HIGH/CRITICAL.

### 15.2 V8 complete

- Đúng 4/4 frozen trials, không trial thứ năm.
- Complete artifacts, stress, reproduction 4/4, FG0–FG7, score, ledger/DSR/PBO truth.
- A7 terminal audit và một terminal outcome duy nhất.
- Không false promotion, S1/live vẫn đóng.

### 15.3 V8X complete hoặc honest not-started

- V8X prereg freeze đúng deadline.
- 10-crypto selection/data audit machine-readable.
- Stock mode/provider được ghi rõ; Binance maturity hoặc external provider limitation không bị che giấu.
- Cohort được authorize chạy đúng 4 trials; nếu cả hai chạy thì tổng đúng 8.
- Separate metrics/statistics/reproduction/audits; không combined score.
- Terminal cohort outcomes hoặc `V8X_*_NOT_STARTED_*` rõ ràng.

### 15.4 Sprint close

- CONTINUE.md và MAP phản ánh đúng terminal truth.
- Master MD/JSON trỏ tới mọi evidence/hash/commit.
- Không owned worker/heartbeat còn sống; Git sạch; không push nếu owner chưa yêu cầu.

---

## 16. Prompt hoàn chỉnh cho A1 / Orca

```text
Bạn là A1 — owner/integrator/controller của sprint V8P→V8→conditional V8X.
Đọc toàn bộ PLAN.md, CONTINUE.md và các source-of-truth §0 trước khi hành động.
PLAN mới thay thế lịch V7 cũ nhưng KHÔNG cho phép sửa frozen V8 spec.

MỤC TIÊU:
1. Dùng real parallel Orca agents trong worktrees riêng để hoàn tất T12→T13→T14.
2. Recompute T01–T15; chỉ khi 15/15 PASS mới chạy đúng V8 quartet.
3. Stress/reproduce/score/audit và đóng V8 trung thực.
4. Nếu V8 terminal hợp lệ và X01–X12 PASS, tự động chạy V8X breadth screen:
   10 crypto ≥1y và 10 stocks ≥1y theo HAI cohort độc lập.
5. Không chờ owner input giữa các phase khi machine gates PASS; fail closed khi gate fail.

BOOTSTRAP:
- Xác minh root Git sạch; commit PLAN này trước khi freeze bootstrap/baseline.
- Không push.
- Ghi sprint_started_at_utc và hard_deadline_utc = start + 12h.
- Tạo topology mới đúng §2 từ clean V8_BOOTSTRAP_SHA; không reuse V7 worktrees.
- Spawn A2–A9 thành agent/session thật; ghi identity/allowed/forbidden paths.
- A7 độc lập, không production code.
- Không quá hai heavy workers.

PARALLEL TASKS:
- A2: dedicated six-alt two-year T12 audit và data manifests.
- A3: weekly Monday scheduler, reversal/control dispatcher, CLI/runner/artifacts.
- A4: FG0–FG7, score, global ledger, honest DSR/PBO cohort handling.
- A5: reproduction/stress/reconciliation full surface.
- A6: resolved V8 contract/golden; freeze V8X specs trước first scored V8 metric.
- A8: performance-blind 10-crypto selection/data audit; không đọc V8 results.
- A9: stock mode/provider/session/corporate-action audit; không đọc V8 results.
- A7: audit only after clean integration SHA.

MERGE V8 CORE:
- Merge A2→A3→A4→A5→A6; targeted tests sau mỗi merge, full suite cuối.
- Không sửa research/hypotheses/H-XSECT-REVERSAL-v2 frozen files.
- Generate resolved contract/baseline/manifest và dispatch A7 T14.
- Recompute toàn bộ T01–T15; thiếu một gate thì V8_NOT_AUTHORIZED và shutdown/handoff.

RUN V8:
- Wave 1: XSECT-WREV-3D + XSECT-WREV-7D.
- Wave 2: XSECT-WREV-14D + XSECT-WMOM-7D-CONTROL.
- Detached worktrees cùng attested SHA, stagger ≥5s, max two workers.
- Không đọc partial PnL, tuning, replacement trial hoặc performance retry.
- Chạy full stress, reproduction 4/4, finalizer, registry, A7 terminal audit.
- REJECT_ALL là kết quả hợp lệ.

CONDITIONAL V8X:
- Chỉ sau valid V8 terminal và X01–X12 machine PASS.
- V8X prereg phải precede first V8 scored artifact; missed thì không V8X.
- Không thêm 10+10 symbols vào frozen V8 core.
- Crypto: deterministic top-10 eligible rule §9, ≥365d bars+funding.
- Stocks: ưu tiên Binance TradFi chỉ khi đủ 10 contracts ≥365d. Nếu không,
  US_EQUITY_SPOT mode chỉ chạy khi approved provider/read-only credentials/calendar/
  corporate actions contract PASS. Không giả underlying spot là Binance perp.
- Merge breadth work chỉ sau V8 close; A7 attest riêng.
- Chạy đúng waves X1–X4, tối đa hai workers; cohort blocked không có replacement.
- Scores, PnL, DSR, PBO và verdicts hoàn toàn tách crypto/equity.
- One-year breadth chỉ exploratory; không S1/live/promotion.

CONTROL PLANE:
- Heartbeat 60s; state/event log append-only; owned PID registry.
- Stale >10m hoặc resource/hash/dirty-tree breach: stop safe, ghi forensic event.
- Hard stop 12h; không tự gia hạn.
- Không git add -A, reset/clean, sửa artifact lịch sử hoặc push.

FINAL REPORT:
- Commits/worktrees/agent identities/merge order.
- Tests và T12/T13/T14 evidence; T01–T15 verdict.
- V8 4/4 metrics/gates/stress/repro/statistics/A7 verdict.
- X01–X12 và V8X cohort data/trials/verdicts hoặc exact not-started blocker.
- Artifact paths/hashes, global trial counts, S1/live state, remaining PIDs.
- Stop mọi owned process, để Git sạch và ghi next safe action.

Ưu tiên scientific integrity và reproducibility hơn việc tìm strategy có lời.
Không được biến một limitation thành PASS bằng lời giải thích thủ công.
```

---

## 17. Mục tiêu nói đơn giản cho owner

V7 đã làm xong bài kiểm tra và trả lời: “strategy này chưa đủ tốt”. Sprint mới trước tiên sửa ba bộ phận còn thiếu để chiếc máy có thể chấm bài V8. Sau đó máy cho bốn bài V8 vào thi.

Nếu V8 được chấm xong sạch sẽ, máy mới mở thêm hai lớp học thử:

- một lớp gồm 10 crypto;
- một lớp gồm 10 stocks.

Hai lớp dùng đồng hồ, luật phí và cách tính tiền khác nhau nên không được trộn điểm. Nếu Binance chưa có đủ một năm dữ liệu cho 10 stocks, máy phải nói “chưa đủ dữ liệu”, chứ không được lấy dữ liệu khác rồi giả vờ đó là Binance.
