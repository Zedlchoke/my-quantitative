# SPRINT V7P → V7 → conditional V8 — Overnight Research Run

> **Thời lượng tối đa:** 12 giờ treo máy
>
> **Mục đích:** hoàn thiện lớp ra quyết định khoa học, chạy đúng 4 trial V7 đã preregister, rồi chỉ chuyển sang V8 nếu V7 kết thúc hợp lệ và toàn bộ transition gate PASS.
>
> **Trạng thái bắt đầu:** V6P đạt; V6 không có candidate; V7 chưa chạy; S1 chưa được phép mở; live trading bị cấm.
>
> **Nguyên tắc:** một kết quả `REJECT_ALL` trung thực vẫn là một sprint thành công. Không tối ưu cho việc “phải tìm được strategy thắng”.

---

## 0. Executive truth — sự thật tại điểm bàn giao

### 0.1 Kết luận đã được xác minh

- Git hiện sạch tại `56381078757814353f0c9c378822503f6fe9e1da`.
- Full test suite hiện tại: `636 passed`.
- Controller đã đóng ở `SHUTDOWN_COMPLETE`; không còn portfolio/matrix/backtest worker chạy ngầm.
- V6P đã hoàn tất `20/20` gate và được A7 cho phép chạy V6.
- V6 đã chạy đủ **4/4 trial**, nhưng **0 candidate được lock**.
- V7 có spec preregister và module tín hiệu sơ bộ, nhưng **0/4 trial đã chạy**.
- Không được tuyên bố V7 “đã hoàn tất”, “đã backtest”, hay “đã thất bại”. Trạng thái đúng là `NOT_RUN / NOT_AUTHORIZED`.
- Không được mở, backfill, phân tích hay dùng S1. Không paper trade, không live trade.

### 0.2 Kết quả định lượng V6

| Trial | Net PnL | PF | MDD | Funding | Fold PnL | Kết luận |
|---|---:|---:|---:|---:|---|---|
| Funding Carry 1D | -5,679.96 | 0.9784 | 24.50% | +1,958.03 | +10,112 / +7,782 / -23,575 | Reject |
| Funding Carry 3D | +2,076.03 | 1.0116 | 15.18% | +2,129.47 | +6,949 / +8,704 / -13,578 | Reject |
| Funding Carry 7D | +20,580.87 | 1.1570 | 8.84% | +2,277.23 | +10,866 / +10,169 / -454 | Reject: top positive fold 51.66% > 50% |
| Reverse 3D control | -20,102.83 | 0.8699 | 28.52% | -1,677.84 | negative control | Expected failure |

**Diễn giải bắt buộc:** 7D là tín hiệu nghiên cứu đáng lưu lại, nhưng không đủ điều kiện promotion vì lợi nhuận phụ thuộc quá nhiều vào một fold. Không rescue, không nới ngưỡng và không thêm biến thể 14D/21D trong sprint này.

### 0.3 Những gì V6 làm tốt

- Accounting dùng continuous capital, có fees/slippage/funding và risk caps.
- Có PIT data checks, hashes, frozen universe/window và registry.
- Có stress thật: fee ×1.5, adverse 2 ticks, delay 1 event, drop-one-symbol và drop-one-fold.
- Reverse control thất bại theo hướng mong đợi.
- A7 kiểm toán độc lập và không còn HIGH/CRITICAL unresolved.
- Không có false promotion: hệ thống cuối cùng đã loại cả bốn trial.

### 0.4 Khoảng trống phải sửa trước V7

| ID | Khoảng trống | Rủi ro nếu không sửa |
|---|---|---|
| P01 | `heartbeat.json`, `CONTINUE.md`, master report và MAP còn giữ một số trạng thái/HEAD cũ | Agent mới hiểu sai tiến trình |
| P02 | Status sidecar V6 vẫn ghi 0 scored trial và chưa có verdict | Máy và báo cáo con người mâu thuẫn |
| P03 | `family_summary.json` không đưa concentration vào FG3 | Có thể bỏ sót đúng lý do 7D phải bị loại |
| P04 | `gate_result.json`/scorecard cũ còn `NOT_YET_TESTED`, `INCONCLUSIVE`, `DIAGNOSTIC_ONLY` | Quyết định cuối phụ thuộc memo thủ công thay vì machine gate hoàn chỉnh |
| P05 | Chỉ 7D và reverse control có successful full-surface reproduction cuối cùng | Chưa chứng minh tái lập đủ 4/4 trial |
| P06 | DSR dùng 3 fold returns và chỉ đếm 4 configuration, trong khi có daily returns và global trial ledger | DSR không có ý nghĩa thống kê |
| P07 | PBO chưa tính được ở 4 configuration; sau V7 sẽ có đúng 8 comparable configurations | Cần chuẩn bị dữ liệu aligned trước khi chạy |
| P08 | Sáu worktree có tồn tại nhưng A2–A6 còn `UNASSIGNED` | Có topology nhưng chưa chứng minh agent thật sự làm việc độc lập |
| P09 | V7 signal module chưa được nối vào CLI/dispatcher/end-to-end runner | V7 chưa runnable |
| P10 | Candidate YAML còn placeholder runtime dù hash spec đã freeze | Dễ tạo drift giữa preregistration và execution |
| P11 | V7 spec/novelty đã freeze trước V6, nhưng signal-code commit xuất hiện sau khi V6 có kết quả | Chỉ được claim **spec-level preregistration**, không được claim code-level blindness |

### 0.5 Phán quyết khoa học hiện tại

`V6P_ENGINE_VALID + V6_FAMILY_REJECTED + V7_NOT_RUN`.

Phần engine/data/PIT/accounting của V6 có bằng chứng tốt. Phần finalizer, DSR/PBO, full-family reproduction và lifecycle reporting chưa đủ hoàn chỉnh để gọi toàn bộ decision surface là “fully automated”. Sprint này sửa chính phần đó.

---

## 1. Scope, authority và điều cấm

### 1.1 Trong scope

1. Đóng sổ V6 bằng addendum, không sửa lịch sử.
2. Đồng bộ machine state, handoff và Wayfinder MAP.
3. Tạo worktree/branch mới cho V7P–V7 và gán agent thật.
4. Nối strategy `funding_price_divergence` vào production runner.
5. Xây final gate + scorecard máy đọc được, bao gồm concentration.
6. Sửa DSR/PBO dùng daily returns và global trial ledger đúng cách.
7. Reproduce lại đủ bốn trial V6 để chứng minh contract.
8. A7 audit và authorize riêng trước V7.
9. Chạy đúng bốn trial V7 preregister, stress, reproduce, score và kết luận.
10. Preregister V8 trước khi V7 lộ scored metric; chỉ chuẩn bị code trong worktree riêng và chỉ chạy V8 sau valid V7 terminal transition.

### 1.2 Ngoài scope

- Không mở hoặc quan sát S1.
- Không thêm strategy family mới trong V7, ngoại trừ V8 preregistration và isolated preparation được mô tả chính xác tại §17; V8 tuyệt đối không được score trước transition gate.
- Không thêm lookback ngoài `1D`, `3D`, `7D` và reverse control đã freeze.
- Không tuning threshold, universe, date range, cost, folds hay ranking sau khi thấy kết quả.
- Không đổi hard gate để cứu candidate.
- Không paper/live trading, không Binance order API, không credential.
- Không merge/sửa các worktree lịch sử ngoài manifest mới.
- Không chạy đồng thời quá hai heavy validation workers.

### 1.3 Bất biến bằng chứng

- Không sửa artifact V6P/V6 đã phát hành chỉ để làm chúng “đẹp” hơn.
- Correction phải là artifact addendum mới, trỏ tới file cũ bằng hash và nêu rõ lý do.
- Frozen V7 `candidate.yaml` và novelty proof hiện có là read-only.
- Runtime fields được giải quyết trong một `resolved_run_contract.json` mới; không điền ngược vào YAML đã hash.
- Một trial đã lộ metric scored sẽ tiêu thụ budget, bất kể metric đẹp hay xấu.

---

## 2. Topology bắt buộc: 7 agent + detached workers

### 2.1 Nguyên tắc Orca

A1 phải thật sự tạo worktree, mở agent riêng và ghi identity. Việc chỉ tạo thư mục/branch nhưng để `UNASSIGNED` **không được tính** là multi-agent execution.

### 2.2 Worktree mới

Giữ các V6P worktree làm lịch sử read-only. Tạo topology mới từ một bootstrap commit sạch:

| Role | Worktree đề xuất | Branch | Quyền chính |
|---|---|---|---|
| A1 | root repo | nhánh integration hiện tại | Orchestration, merge, controller |
| A2 | `../my-quantitative-v7-wt/a2-closure` | `orca/v7-a2-closure` | Closure/provenance/MAP/status |
| A3 | `../my-quantitative-v7-wt/a3-engine` | `orca/v7-a3-engine` | Dispatcher, CLI, PIT signal inputs |
| A4 | `../my-quantitative-v7-wt/a4-finalizer` | `orca/v7-a4-finalizer` | Gates, scoring, DSR/PBO, ledger |
| A5 | `../my-quantitative-v7-wt/a5-reproduction` | `orca/v7-a5-reproduction` | Reproduction, reconciliation, stress audit |
| A6 | `../my-quantitative-v7-wt/a6-conformance` | `orca/v7-a6-conformance` | Spec conformance, golden vectors, resolved contract |
| A7 | `../my-quantitative-v7-wt/a7-audit` | `orca/v7-a7-audit` | Read-only scientific audit; không viết production code |

Khi launch V7, tạo tối đa bốn detached execution worktree `r1..r4` tại **cùng frozen launch SHA**. Chỉ hai worker được chạy đồng thời.

### 2.3 Identity và ownership

Trước khi A2–A7 làm việc, `worktree_manifest.json` phải có:

- `role`, `agent_session_id`, `path`, `branch`, `bootstrap_sha`;
- `allowed_paths`, `forbidden_paths`;
- `status=ASSIGNED` và timestamp;
- planned commit, actual commit, merge status;
- không role nào dùng identity `UNASSIGNED` khi được tính là đang hoạt động.

Một file chỉ có một owner tại một thời điểm. Cross-cutting edit phải chuyển quyền trong journal trước khi sửa.

### 2.4 Merge discipline

1. Mỗi agent commit atomic trên branch của mình.
2. A1 kiểm tra diff, tests và allowed paths trước khi cherry-pick.
3. Merge order: `A2 → A3 → A4 → A5 → A6`.
4. A7 audit **sau** integration commit, không audit branch rời.
5. Mọi execution worktree phải được tạo lại từ launch SHA đã được A7 attest.

---

## 3. Vai trò và deliverable

### A1 — Owner / Integrator / Controller

- Freeze bootstrap, tạo/gate topology, launch agent thật.
- Duy trì `run_contract.json`, `event_log.jsonl`, `state.json`, heartbeat và retry budget.
- Cherry-pick có kiểm soát; không tự sửa hộ một agent đang sở hữu file.
- Không cho V7 chạy nếu A7 chưa ký prelaunch attestation.
- Sau terminal state: dừng heartbeat/worker, tạo shutdown report và clean Git.

### A2 — Closure & provenance

- Tạo `v6-closure-addendum-20260825.md/json` thay vì sửa evidence cũ.
- Đồng bộ state/status/CONTINUE/MAP theo HEAD và terminal truth hiện tại.
- Ghi rõ 7D fail bởi top-fold concentration 51.66%, không phải MDD 28.85%.
- Snapshot hashes của mọi artifact nguồn dùng cho addendum.

### A3 — V7 engine integration

- Thêm dispatcher/CLI cho `funding_price_divergence`.
- Truyền `daily_closes` và funding PIT-safe vào signal builder.
- Hỗ trợ normal và reverse direction đúng frozen spec.
- Propagate mọi execution/provenance env qua subprocess/reproduction.
- Xuất signal diagnostics đủ để audit rank, price-return, funding-mean và selected symbols.

### A4 — Machine finalizer & statistics

- Viết finalizer tạo `final_gate_result.json` và `final_scorecard.json`.
- FG3 phải chứa cả family adjacency, PF, net funding, top-positive-fold share và top-positive-symbol share.
- DSR dùng aligned **daily returns**, skew/kurtosis, sample length thật và effective global trial count.
- PBO dùng toàn bộ comparable configurations sau V7; không cherry-pick family/trial.
- Snapshot append-only global trial ledger trước và sau V7.

### A5 — Reproduction & reconciliation

- Reproduce đủ 4/4 trial V6 từ registry/config/hash hiện có.
- Chứng minh trade ledger, funding ledger, equity và metrics match theo tolerance định trước.
- Chuẩn bị harness giống hệt cho 4/4 V7 trials.
- Kiểm tra stress surface và chỉ ra derived stress nào không có full equity path.

### A6 — Conformance & golden proof

- So sánh code với frozen V7 candidate/novelty proof; không thay hypothesis.
- Ghi rõ chronology: hypothesis/spec được preregister trước V6; implementation code thì không blind với V6. Audit mọi code choice có thể làm hypothesis drift.
- Tạo `resolved_run_contract.json` chứa window, folds, symbols, dataset hashes, costs, limits và launch SHA.
- Tạo end-to-end synthetic golden panel có expected ranks/positions/PnL.
- Kiểm tra timestamp boundary để không dùng close/funding chưa biết tại decision time.

### A7 — Independent scientific auditor

- Chỉ đọc integration commit và evidence; không viết code production.
- Challenge lookahead, multiple-testing, concentration, accounting, provenance, reproduction và resource safety.
- Xuất prelaunch attestation `PASS` hoặc `FAIL` có blocker cụ thể.
- Sau V7, kiểm tra lại final verdict và ký closure audit.

---

## 4. Lịch thực thi 12 giờ

| Thời gian | Pha | Công việc |
|---|---|---|
| 00:00–00:45 | V7P-0 | Freeze bootstrap, tạo/gate worktree, launch A2–A7 |
| 00:45–03:15 | V7P-1 | A2 closure; A3 engine; A4 finalizer; A5 reproduction; A6 conformance song song |
| 03:15–04:30 | V7P-2 | A1 merge, full suite, resolved contract, baseline freeze |
| 04:30–05:30 | V7P-3 | A7 independent prelaunch audit và remediation tối đa một vòng |
| 05:30–08:30 | V7 | Chạy 4 trials theo hai wave, tối đa 2 workers/wave |
| 08:30–10:15 | V7 post | Stress, reproduction, reconciliation, DSR/PBO, gates và score |
| 10:15–11:15 | Audit | A7 terminal audit, challenge memo, verdict |
| 11:15–12:00 | Close | Master report, MAP/CONTINUE, shutdown, Git sạch |

Nếu còn ít hơn 180 phút trước hard stop mà chưa có prelaunch attestation, không launch V7. Đóng ở `V7P_COMPLETE_V7_NOT_STARTED_TIME_GUARD`.

Trong overnight continuation, hàng `Close` là điểm đóng pha V7: phải dừng/reconcile V7 workers và tạo terminal evidence. Nếu §17 T01–T15 PASS và còn ≥300 phút thì controller chuyển sang V8 thay vì final shutdown; nếu không thì shutdown ngay. Absolute hard stop 12 giờ vẫn giữ nguyên.

---

## 5. Pha V7P-0 — đóng sổ V6 và sửa control-plane truth

### 5.1 Addendum bắt buộc

Tạo mới:

- `research/wayfinder/evidence/v6-closure-addendum-20260825.md`
- `research/wayfinder/evidence/v6-closure-addendum-20260825.json`

Addendum phải nêu:

- final HEAD và Git cleanliness;
- bốn kết quả V6 cùng nguồn raw artifact;
- lý do reject thật của từng trial;
- 7D MDD đúng là khoảng 8.84%, không dùng claim 28.85%;
- V7 0/4 và chưa được chạy;
- file nào stale và cách supersede;
- danh sách checksum cho evidence liên quan.

### 5.2 Lifecycle reconciliation

- `state.json` và shutdown report là terminal authority.
- Không rewrite heartbeat lịch sử; tạo một closure heartbeat/event chỉ rõ sampler đã dừng và PID không còn sống.
- Cập nhật `CONTINUE.md` thành handoff hiện hành với current HEAD, clean tree và next command.
- Cập nhật `research/wayfinder/MAP.md`: V6 family rejected; V7 pending; S1 untouched.
- Status sidecar V6 phải phản ánh `4 scored / 0 locked / CANDIDATE_FAIL`.

### 5.3 Không được làm

- Không xóa retry/error history.
- Không sửa result metrics cũ tại chỗ.
- Không đổi master report cũ mà không để lại provenance; dùng addendum superseding statement.

---

## 6. Pha V7P-1 — repair decision surface

### 6.1 V7 runner contract

Runner phải hỗ trợ:

```text
--strategy-kind funding_price_divergence
--price-lookback-days {1,3,7}
--funding-lookback-days {1,3,7}
--signal-direction {normal,reverse}
```

Contract:

1. Mỗi ngày chỉ dùng daily close đã hoàn tất trước decision timestamp.
2. Funding window chỉ dùng event có `fundingTime <= decision_time`.
3. Score theo frozen spec: percentile(price return) trừ percentile(funding mean).
4. Normal: long top-2, short bottom-2; reverse đổi phía.
5. Thiếu dữ liệu/rank tie không giải quyết được phải fail closed và log reason.
6. Universe/window/folds/cost model/risk limits kế thừa resolved contract, không lấy default ngầm.
7. Mọi subprocess phải preserve provenance enforcement env.

### 6.2 End-to-end golden test

Golden test không chỉ unit-test hàm signal. Nó phải đi qua:

`synthetic panel → runner dispatcher → positions → accounting → artifact writer`.

Kiểm tra tối thiểu:

- rank/position đúng expected;
- reverse control đảo đúng phía;
- không sử dụng future close/funding;
- fees, slippage và funding sign đúng;
- result root có đủ provenance/hash;
- cùng input/seed cho output deterministic.

### 6.3 Final gate artifact

Mỗi trial phải có machine-readable final artifacts riêng, không overwrite diagnostic file cũ:

- `final_gate_result.json`
- `final_scorecard.json`
- `concentration_report.json`
- `statistical_haircut.json`
- `reproduction_report.json`
- `stress_manifest.json`

Finalizer chỉ được phát `LOCK_ELIGIBLE` nếu mọi hard gate PASS và A7 closure không có HIGH/CRITICAL unresolved.

### 6.4 DSR contract

DSR candidate inputs:

- daily return series của toàn evaluation window;
- observed daily Sharpe;
- skewness, kurtosis và sample length thực;
- `effective_n_trials` lấy từ append-only ledger của tất cả scored comparable trials trước thời điểm quyết định;
- trial Sharpe dispersion lấy từ comparable configurations, không lấy ba fold làm ba observations.

Nếu input không đủ hoặc không thể chứng minh provenance: `DSR_UNAVAILABLE_FAIL_CLOSED`, không tự động cho điểm.

### 6.5 PBO contract

Sau đúng bốn V7 trials, pool comparable dự kiến gồm 8 configurations: bốn V6 + bốn V7 cùng universe/window/execution contract. A4 phải:

- align daily return matrix theo timestamp;
- dùng tất cả 8 configurations, không loại loser;
- chạy CSCV với số partition preregister hợp lệ;
- ghi combination count, rank rule, tie rule và seed nếu có;
- nếu matrix không đủ/không comparable thì `PBO_UNAVAILABLE_FAIL_CLOSED`.

PBO/DSR là family-level haircut, không được dùng để rescue một trial fail hard gate.

### 6.6 Full-family reproduction

Trước authorization V7, A5 phải reproduce lại V6 4/4. Sau V7, reproduce V7 4/4.

Pass khi:

- config/data/code hashes match;
- net PnL, gross PnL, fees, slippage, funding, MDD và PF match trong tolerance được freeze trước;
- ledger/equity row counts match;
- không cần sửa source/result để chạy lại.

---

## 7. V7P prelaunch gates — 18/18 bắt buộc

| Gate | Điều kiện PASS |
|---|---|
| C01 | Evidence V6P/V6 bất biến; correction chỉ qua hashed addendum |
| C02 | State, shutdown, CONTINUE, MAP và status sidecar không còn mâu thuẫn |
| C03 | Worktree manifest sạch; A2–A7 đều ASSIGNED với session identity thật |
| C04 | Integration commit sạch, baseline/hash/lockfile đã freeze |
| C05 | Frozen V7 candidate + novelty hashes không đổi |
| C06 | `resolved_run_contract.json` đầy đủ, không placeholder/default ngầm |
| C07 | CLI/dispatcher hỗ trợ V7 normal/reverse và preserve env |
| C08 | Daily close PIT boundary có unit + integration tests |
| C09 | Funding PIT boundary có unit + integration tests |
| C10 | End-to-end golden normal/reverse deterministic PASS |
| C11 | Finalizer tính đủ FG0–FG7 và concentration bằng máy |
| C12 | Global scored-trial ledger snapshot đầy đủ, append-only, deduplicated |
| C13 | DSR dùng daily returns + global trial count; unavailable thì fail closed |
| C14 | PBO 8-config matrix contract/test sẵn sàng |
| C15 | Reproduction V6 đạt 4/4 trên integration baseline |
| C16 | Full suite PASS và không có uncommitted production/evidence edit |
| C17 | A7 prelaunch attestation PASS, 0 unresolved HIGH/CRITICAL |
| C18 | S1/live disabled; disk/RAM/time đủ; còn ≥180 phút |

Thiếu một gate: `V7_NOT_AUTHORIZED`. A1 không được “tự hiểu là gần đạt”.

---

## 8. Pha V7 — đúng bốn trial, không hơn

### 8.1 Trial inventory freeze

| ID | Strategy | Lookback | Direction |
|---|---|---:|---|
| `XSECT-FUND-PRICE-DIV-1D` | Funding–price divergence | 1D | normal |
| `XSECT-FUND-PRICE-DIV-3D` | Funding–price divergence | 3D | normal |
| `XSECT-FUND-PRICE-DIV-7D` | Funding–price divergence | 7D | normal |
| `XSECT-FUND-PRICE-DIV-REV-3D` | Funding–price divergence | 3D | reverse control |

Không trial thứ năm. Không thay đổi tham số sau khi wave đầu trả kết quả.

### 8.2 Hai wave execution

- Wave 1: 1D + 3D.
- Wave 2: 7D + reverse 3D.
- Hai detached worktree/wave, cùng launch SHA, config hash và data snapshot.
- Controller không đọc partial PnL để đổi wave sau.
- Chỉ publish metrics khi artifact hoàn chỉnh, atomic và registry committed.

### 8.3 Retry rule

- Không có performance retry.
- Không có `RETRY2` để cứu sentinel hay candidate cũ.
- Lỗi trước khi tạo bất kỳ scored artifact có thể relaunch cùng frozen trial nếu A7 xác nhận `PRELAUNCH_ABORT`, output lỗi được giữ nguyên và không thay config/code/data.
- Lỗi sau khi lộ scored metric tiêu thụ trial budget; không được thêm replacement trial.
- Mọi retry/abort phải vào append-only event log.

### 8.4 Stress bắt buộc

Cho mỗi normal trial:

- baseline;
- fee ×1.5;
- adverse fill +2 ticks;
- one-event execution delay;
- drop-one-symbol cho toàn universe;
- drop-one-fold cho toàn folds.

Stress phải là engine rerun khi cần equity-path metrics. Derived drop-one-fold chỉ được gọi là diagnostic và không thay thế full-path MDD.

---

## 9. Hard gates FG0–FG7

Một normal trial chỉ đủ điều kiện lock khi **tất cả** PASS:

| Gate | Tiêu chí |
|---|---|
| FG0 Integrity | PIT/data/code/config hashes, complete artifacts, no provenance violation |
| FG1 Mechanism | Dấu funding/price divergence đúng giả thuyết; reverse control không vượt normal |
| FG2 Performance | Net PnL > 0; PF ≥ 1.10; không fold nào có net PnL âm |
| FG3 Funding + concentration | Net funding > 0; ≥2 adjacent lookbacks cùng family qua mechanism/performance; top positive fold ≤50%; top positive symbol ≤40% |
| FG4 Risk | MDD ≤10%; exposure/turnover/leverage/risk caps không breach |
| FG5 Stress | Vẫn dương sau fee ×1.5, adverse 2 ticks và delay; drop-one diagnostics không cho thấy single-point dependency |
| FG6 Reproduction | Independent reproduction PASS; ledger/equity/metrics/hash match |
| FG7 Statistical + audit | DSR/PBO contract hợp lệ hoặc fail closed; A7 0 unresolved HIGH/CRITICAL |

Điều kiện family adjacency không được bỏ qua trong summary. Một lookback đơn lẻ không được promote.

### Hard rejection tức thì

- Lookahead/PIT/provenance violation.
- Artifact hoặc hash thiếu/không match.
- PF <1.10, MDD >10%, bất kỳ fold âm.
- Top positive fold >50% hoặc top positive symbol >40%.
- Cost/delay stress chuyển PnL âm.
- Reproduction fail.
- Reverse control tốt hơn normal theo cùng basis.
- A7 còn HIGH/CRITICAL unresolved.

---

## 10. Scorecard 100 điểm

Score chỉ dùng để xếp hạng **sau** khi hard gates PASS; không bù được gate fail.

| Nhóm | Điểm | Cách chấm |
|---|---:|---|
| Integrity & reproducibility | 20 | 5 PIT + 5 hashes/provenance + 5 independent reproduction + 5 deterministic artifacts |
| Robustness across folds | 20 | 8 all folds positive + 6 dispersion thấp + 6 walk-forward consistency |
| Risk-adjusted performance | 20 | 8 PF + 6 MDD + 6 return/risk efficiency |
| Costs & stress | 15 | 5 fee ×1.5 + 5 adverse ticks + 5 delay |
| Breadth & concentration | 15 | 5 adjacent lookbacks + 5 symbol share + 5 fold share |
| Statistical haircut | 10 | 5 DSR + 5 PBO; unavailable nhận 0, không nội suy |

Ngưỡng:

- `<70`: reject.
- `70–79`: research-only, không lock.
- `80–89`: lock-eligible nếu toàn bộ FG0–FG7 PASS.
- `≥90`: strong lock-eligible, vẫn cần A7 ký.

Không làm tròn metric để vượt ngưỡng. Lưu raw value và comparison operator trong JSON.

---

## 11. Quy tắc quyết định cuối

### Outcome A — `V7_LOCKED`

Chỉ khi:

- ít nhất hai adjacent normal lookbacks PASS toàn bộ FG0–FG7;
- mỗi candidate đạt ≥80/100;
- DSR/PBO không phát hiện selection-risk vượt ngưỡng preregister;
- A7 ký terminal audit;
- parameter/code/config được lock trước khi bắt đầu S1 clock.

Sau outcome này cũng **không chạy S1 trong sprint này**. Chỉ tạo S1 forward-start contract bắt đầu sau lock timestamp.

### Outcome B — `V7_REJECT_ALL`

Không candidate đủ điều kiện. Đây là kết quả hợp lệ. Ghi lesson ledger; không được dùng kết quả V7 để sửa V8 spec. V8 chỉ có thể tiếp tục theo preregistration đã freeze trước V7 và transition gate §17.

### Outcome C — `V7P_COMPLETE_V7_NOT_STARTED`

Decision-surface repair hoàn tất nhưng authorization/time/resource gate không đạt. Không chạy nửa chừng.

### Outcome D — `V7_INVALIDATED`

Có integrity/lookahead/provenance/reproduction blocker. Cách ly kết quả, không dùng PnL để học/tuning, giữ forensic evidence.

---

## 12. Artifact contract

### Control

```text
research/control/v7_twelve_hour_run/
  run_contract.json
  state.json
  event_log.jsonl
  heartbeat.json
  worktree_manifest.json
  wt_gate_check.json
  resource_guard.json
  shutdown_report.json
```

### Audit / repair

```text
research/audits/v7p/
  baseline_root.json
  resolved_run_contract.json
  global_trial_ledger_before.json
  global_trial_ledger_after.json
  v6_reproduction_summary.json
  golden_vector_report.json
  gate_ledger_v7p.json
  a7_prelaunch_attestation.json
  challenge_memo_v7p.md
  a7_terminal_audit.json
```

### Results

```text
results/matrix/v7_xsect_funding_price_divergence/
results/portfolio_v7/
results/reproduction_v7/
results/validation_v7p/
```

### Evidence

```text
research/wayfinder/evidence/v6-closure-addendum-20260825.{md,json}
research/wayfinder/evidence/sprint-v7p-v7-master-20260825.md
research/wayfinder/evidence/sprint-v7p-v7-master-20260825.json
```

Mọi JSON phải có schema version, generated_at UTC, source SHA, config/data hashes và parent artifact references.

---

## 13. Definition of Done

Sprint chỉ được gọi là hoàn tất khi:

### V7P DoD

- [ ] V6 closure addendum tồn tại và không rewrite lịch sử.
- [ ] CONTINUE/MAP/status/control-plane phản ánh đúng terminal truth.
- [ ] Worktree topology mới đạt gate; A2–A7 đều có session identity thật.
- [ ] V7 dispatcher/CLI normal+reverse chạy end-to-end.
- [ ] Golden test, PIT tests và full suite PASS.
- [ ] Finalizer machine-readable tính đúng concentration.
- [ ] DSR/PBO/global ledger contract hoạt động hoặc fail closed.
- [ ] V6 reproduction đạt 4/4.
- [ ] Resolved contract + baseline được freeze ở clean SHA.
- [ ] A7 prelaunch attestation PASS trước bất kỳ V7 metric nào.

### V7 DoD nếu được authorize

- [ ] Đúng 4/4 trial đã chạy; không trial thứ năm.
- [ ] Stress surface đầy đủ và gắn provenance.
- [ ] V7 reproduction đạt 4/4.
- [ ] Final FG0–FG7 + scorecard được máy tạo cho từng trial.
- [ ] DSR/PBO dùng ledger/matrix đầy đủ, không cherry-pick.
- [ ] A7 terminal audit kết luận LOCK/REJECT/INVALIDATED.
- [ ] Không S1/live access.
- [ ] Heartbeat/worker đã dừng; state terminal; Git sạch.
- [ ] Master evidence + CONTINUE + MAP đã cập nhật.

---

## 14. Stop conditions và fail-safe

Dừng launch mới ngay nếu:

- disk free <20 GB;
- memory pressure nghiêm trọng hoặc swap tăng liên tục;
- có hơn hai heavy worker;
- baseline/code/config/data hash drift;
- bất kỳ agent ghi ngoài allowed paths;
- provenance/PIT/golden/reproduction gate fail;
- A7 chưa authorize;
- còn <180 phút trước deadline;
- S1/live path bị chạm.

Khi dừng: không xóa artifacts; ghi event; terminate owned PID; tạo shutdown report; nêu next safe action.

---

## 15. Prompt hoàn chỉnh cho A1 / Orca

```text
Bạn là A1 — owner, integrator và controller của sprint V7P → V7 → conditional V8 trong repo
/Users/hoangminhlong/my-quantitative.

Đọc toàn bộ PLAN.md trước khi làm. PLAN.md là execution contract. Không tóm tắt rồi bỏ qua
các gate. Hãy triển khai sprint tối đa 12 giờ, dùng nhiều agent/worktree thật trong Orca.

BOOTSTRAP TRƯỚC KHI DELEGATE
- Chạy git status và xác minh thay đổi hiện có. PLAN.md có thể đang uncommitted.
- Tạo một administrative bootstrap commit chỉ chứa PLAN.md sau khi đã xác minh diff; không kéo
  unrelated dirty files vào commit.
- Ghi BOOTSTRAP_SHA. Mọi A2-A7 worktree phải được tạo từ đúng BOOTSTRAP_SHA này để tất cả agent
  nhìn thấy cùng một PLAN. Nếu không thể tạo clean bootstrap thì STOP và báo blocker; không launch giả.

SỰ THẬT KHỞI ĐẦU
- V6P đã PASS 20/20.
- V6 đã chạy 4/4 và REJECT_ALL; 7D có PF ~1.157, MDD ~8.84% nhưng fail top-fold
  concentration 51.66% > 50%.
- V7 chưa chạy: 0/4, NOT_AUTHORIZED.
- HEAD khởi đầu dự kiến 56381078757814353f0c9c378822503f6fe9e1da; hãy tự xác minh.
- Full suite khởi đầu dự kiến 636 passed; hãy tự chạy lại.
- S1 và live trading tuyệt đối bị cấm.

MỤC TIÊU
1. Đóng sổ/sửa reporting V6 bằng addendum, không rewrite evidence lịch sử.
2. Sửa decision surface: final gates, concentration, scorecard, DSR/PBO, global ledger,
   full-family reproduction.
3. Nối frozen strategy funding_price_divergence vào runner, chứng minh PIT bằng golden test.
4. Sau A7 prelaunch PASS, chạy đúng 4 V7 trials, stress/reproduce/score/audit.
5. Kết thúc bằng một verdict trung thực: V7_LOCKED, V7_REJECT_ALL,
   V7P_COMPLETE_V7_NOT_STARTED hoặc V7_INVALIDATED.
6. Nếu và chỉ nếu V7 terminal hợp lệ cùng transition T01-T15 PASS, tự động tiếp tục
   V8 theo §17; không chờ thêm owner input trong unattended run.

TOPOLOGY BẮT BUỘC
- A1 làm tại root integration repo.
- Tạo sáu worktree mới dưới ../my-quantitative-v7-wt/ cho:
  A2 closure, A3 engine, A4 finalizer, A5 reproduction, A6 conformance, A7 audit.
- Mỗi agent phải thật sự được launch trong Orca và có agent_session_id; UNASSIGNED không tính.
- Ghi role/path/branch/bootstrap/allowed/forbidden/identity/commit/merge vào manifest.
- Gate tất cả worktree sạch, đúng branch, cùng bootstrap trước khi giao việc.
- Sau khi launch, yêu cầu từng agent ACK bằng agent_session_id, pwd, branch, HEAD và allowed paths.
  A1 phải đối chiếu ACK với manifest; thiếu một ACK thì role đó chưa được tính là active.
- A7 độc lập, không viết production code.
- Execution dùng tối đa hai detached workers đồng thời tại cùng frozen launch SHA.

PHÂN CÔNG SONG SONG
- A2: V6 closure addendum, state/status/CONTINUE/MAP/provenance reconciliation.
- A3: CLI/dispatcher funding_price_divergence, daily close + funding PIT, env propagation,
  signal diagnostics.
- A4: machine FG0-FG7 finalizer, scorecard, concentration, global ledger, daily-return DSR,
  8-config PBO.
- A5: reproduce V6 đủ 4/4 và chuẩn bị/reproduce V7 đủ 4/4; ledger/equity reconciliation.
- A6: frozen-spec conformance, resolved_run_contract, end-to-end synthetic golden vectors.
- A7: audit integration commit, prelaunch attestation và terminal audit.
- Launch A2-A6 đồng thời sau topology gate. A7 có thể được launch cùng lúc nhưng phải chờ integration
  SHA và không đọc partial performance để đưa ra prelaunch verdict.
- Nếu Orca/runtime không hỗ trợ launch agent thật vào worktree riêng: STOP, ghi blocker và yêu cầu owner;
  tuyệt đối không giả lập multi-agent bằng cách để A1 tự làm tất cả rồi gắn nhãn A2-A7.

MERGE
- Mỗi agent commit atomic và chỉ sửa allowed paths.
- A1 không sửa cùng file với agent đang sở hữu file đó. Conflict phải trả lại owner xử lý trên worktree.
- A1 review/cherry-pick theo A2 → A3 → A4 → A5 → A6.
- Trước mỗi cherry-pick, xác minh commit là descendant của BOOTSTRAP_SHA, diff nằm trong allowed paths,
  worktree sạch và targeted tests của agent PASS.
- Chạy targeted tests sau từng merge và full suite sau integration.
- Freeze clean baseline; A7 audit chính integration SHA đó.
- Không launch V7 nếu 18/18 V7P gates chưa PASS hoặc còn <180 phút.

V7 TRIAL BUDGET — KHÔNG ĐƯỢC THAY
- XSECT-FUND-PRICE-DIV-1D normal
- XSECT-FUND-PRICE-DIV-3D normal
- XSECT-FUND-PRICE-DIV-7D normal
- XSECT-FUND-PRICE-DIV-REV-3D reverse control
- Wave 1: 1D + 3D. Wave 2: 7D + reverse 3D. Tối đa hai worker.
- Không trial thứ năm, không tuning, không rescue, không đọc partial PnL để đổi kế hoạch.
- Không performance retry. Prelaunch abort chỉ được relaunch khi chưa có scored artifact và A7 xác nhận.
- Không tạo RETRY2 cho sentinel/candidate cũ.

V8 FREEZE TRƯỚC V7 SCORE
- Trước scored metric V7 đầu tiên, tạo/freeze H-XSECT-REVERSAL-v2 spec + novelty hashes
  đúng §17.2. Nếu V7 đã lộ metric trước freeze thì V8_PREREG_WINDOW_MISSED và không V8.
- Có thể chuẩn bị V8 A2-A6 song song trong isolated worktrees, nhưng cấm đọc V7 result/log/metric,
  cấm merge V8 vào root và cấm V8 scored launch trước valid V7 terminal.

HARD GATES
Thực thi đúng FG0-FG7 trong PLAN.md. Đặc biệt:
- PF >=1.10; MDD <=10%; mọi fold dương.
- net funding dương; ít nhất hai adjacent lookbacks pass.
- top positive fold <=50%; top positive symbol <=40%.
- costs/delay stress vẫn dương.
- independent reproduction pass.
- DSR/PBO đúng contract hoặc fail closed.
- A7 không còn HIGH/CRITICAL.
Score >=80 không thể bù hard-gate failure.

CONTROL VÀ BẰNG CHỨNG
- Duy trì append-only event log, atomic state, heartbeat và owned-PID registry.
- Không sửa artifact V6 cũ; correction qua hashed addendum.
- Không sửa frozen V7 candidate YAML; runtime resolution ở resolved_run_contract.json.
- Mọi artifact ghi schema/source SHA/config/data hashes/parents.
- Không tuyên bố hoàn tất dựa trên exit code; phải kiểm tra artifact completeness và reconciliation.

V7 TERMINAL VÀ CONDITIONAL V8
- Chạy stress, reproduction, DSR/PBO, machine gates và scorecards.
- Cho A7 audit verdict cuối.
- Tạo sprint-v7p-v7-master-20260825.md/json, cập nhật CONTINUE.md và Wayfinder MAP.
- Dừng toàn bộ V7 heavy worker/heartbeat, reconcile registry, xác minh V7 terminal state và Git sạch.
- Ngay sau đó tính machine-readable transition T01-T15 tại §17.3.
- Nếu V7 là V7_LOCKED hoặc V7_REJECT_ALL, T01-T15 PASS và còn >=300 phút: KHÔNG shutdown
  toàn bộ controller và KHÔNG chờ owner; tự động tiếp tục V8 theo §17.4-§17.10.
- Nếu V7_INVALIDATED/INCOMPLETE, bất kỳ T-gate FAIL hoặc còn <300 phút: không V8; tạo
  V8_NOT_STARTED_* rồi shutdown sạch.
- Sau V8 terminal hoặc V8_NOT_STARTED: dừng tất cả owned workers/heartbeat, ghi final shutdown
  report, xác minh PID list rỗng và Git sạch.
- Báo cáo cuối cùng: commits, tests, V7 gates/metrics/verdict, V8 transition 15/15 hoặc blocker,
  V8 gates/metrics/verdict nếu đã chạy, artifact paths, PID còn sống và next safe action.

Ưu tiên tính đúng, tính tái lập và bằng chứng khoa học hơn việc tìm strategy có lời.
REJECT_ALL hợp lệ; false promotion là thất bại nghiêm trọng.
```

---

## 16. Mục tiêu nói thật ngắn cho người vận hành

Sprint này không đi tìm thêm thật nhiều “vé số strategy”. Nó sửa cái máy chấm bài để máy không bỏ sót lỗi, sau đó mới cho bốn bài V7 đã niêm phong vào thi. Nếu cả bốn rớt đúng luật, hệ thống vẫn thành công vì đã tránh đưa một strategy yếu ra sử dụng thật.

---

## 17. V8 conditional overnight continuation — Weekly Cross-Sectional Reversal

### 17.1 Mục tiêu và ranh giới khoa học

V8 kiểm tra một family độc lập với V6/V7:

`H-XSECT-REVERSAL-v2 — six-alt weekly cross-sectional reversal`.

Đây không phải rescue, filter hay tuning của funding-price divergence. V8 hỏi một câu khác: sau một giai đoạn tăng/giảm tương đối mạnh, nhóm altcoin thắng và thua có đảo chiều trong tuần kế tiếp hay không?

V8 được phép **preregister và chuẩn bị code** trước hoặc trong lúc V7 chạy, nhưng:

- candidate/spec/novelty hash phải freeze **trước scored artifact V7 đầu tiên**;
- agent V8 không được đọc `results/portfolio_v7`, V7 partial logs, metrics hay verdict;
- V8 không được chạy scored trial cho đến khi V7 có terminal outcome hợp lệ;
- nếu preregistration xảy ra sau khi V7 lộ metric: `V8_PREREG_WINDOW_MISSED`, không chạy V8 trong đêm đó;
- V8 dùng S0 screening; không được gọi là OOS/S1 hoặc promotion evidence.

Lý do chọn v2: v1 từng bị chặn vì universe gồm ETH chỉ có khoảng một năm dữ liệu. V2 loại ETH **chỉ theo data-availability rule được freeze trước performance**, dùng sáu altcoin có khoảng hai năm dữ liệu sạch. Không được loại thêm symbol dựa trên PnL.

### 17.2 V8 preregistration contract

Trước V7 launch, A6 phải tạo và A7 phải hash/novelty-check:

```text
research/hypotheses/H-XSECT-REVERSAL-v2/candidate.yaml
research/hypotheses/H-XSECT-REVERSAL-v2/hypothesis.md
research/hypotheses/H-XSECT-REVERSAL-v2/status.yaml
research/audits/v8p/v8_spec_freeze.json
research/audits/v8p/v8_catalog_novelty_check.md
```

Frozen rules:

| Field | Contract |
|---|---|
| Family | `cross_sectional_weekly_reversal` |
| Stage | `S0_EXPLORATORY` |
| Universe | `SOLUSDT, BNBUSDT, XRPUSDT, DOGEUSDT, LINKUSDT, ADAUSDT` |
| Benchmark context | `BTCUSDT`, measurement only |
| Data window | common six-alt intersection, target `2024-08-21T14:30Z → 2026-08-21T00:00Z`; canonical audit decides exact completed-bar endpoints |
| Signal clock | Monday `00:00 UTC`, completed bars only |
| Formation lookbacks | exactly `3D, 7D, 14D` |
| Direction | long bottom-2 past-return losers, short top-2 past-return winners |
| Negative control | long winners / short losers at `7D` |
| Rebalance/holding | every 7 days; no intraweek discretionary rebalance |
| Portfolio | gross 0.80, net 0, long gross 0.40, short gross 0.40, max abs symbol weight 0.20 |
| Eligibility | all six symbols required; incomplete cross-section skips whole rebalance |
| Execution | next completed 15m event, one-tick adverse slippage, fee 0.0005, native funding accounting |
| Split | three chronological folds; 7-day purge/embargo at fold boundary; warmup at least 14 days |
| Trial budget | exactly three normal + one negative control |

Trial inventory:

| ID | Formation | Direction |
|---|---:|---|
| `XSECT-WREV-3D` | 3D | reversal |
| `XSECT-WREV-7D` | 7D | reversal |
| `XSECT-WREV-14D` | 14D | reversal |
| `XSECT-WMOM-7D-CONTROL` | 7D | momentum control |

Forbidden after freeze:

- funding/OI/volatility/regime/liquidity filters;
- changing rebalance weekday or cadence;
- per-symbol parameters or removal by performance;
- adding formation lookbacks;
- changing thresholds, costs, folds, window or universe;
- using V7 results to change V8 code/spec;
- calling the six-symbol window “untouched OOS”.

### 17.3 Điều kiện chuyển V7 → V8 — 15/15 bắt buộc

V8 scored launch chỉ được authorize khi tất cả PASS:

| Gate | Điều kiện PASS |
|---|---|
| T01 | V7 chạy đúng 4/4 frozen trials; không trial thứ năm |
| T02 | V7 terminal outcome là `V7_LOCKED` hoặc `V7_REJECT_ALL` |
| T03 | Không phải `V7_INVALIDATED`, `INCOMPLETE`, `NOT_STARTED` hoặc provenance breach |
| T04 | V7 stress surface và machine FG0–FG7 hoàn chỉnh cho 4/4 |
| T05 | Independent V7 reproduction đạt 4/4 |
| T06 | DSR/PBO/global ledger đã update bằng toàn bộ V6+V7 scored trials, không cherry-pick |
| T07 | A7 terminal audit V7 PASS, 0 unresolved HIGH/CRITICAL |
| T08 | V7 worker/heartbeat đã dừng; owned PID list rỗng; state terminal |
| T09 | V7 evidence/master report/registry reconciliation hoàn chỉnh và Git sạch |
| T10 | V8 candidate + novelty hashes được freeze trước timestamp scored V7 đầu tiên |
| T11 | A7 xác nhận V8 distinct; không adaptive rescue/tuning từ V7 |
| T12 | Six-alt two-year data audit PASS: no unexplained gaps/duplicates, PIT timestamps, metadata and hashes frozen |
| T13 | V8 engine/golden/PIT/accounting/reproduction harness tests PASS trên clean integration SHA |
| T14 | V8 prelaunch A7 attestation PASS và baseline/contract/manifest pins match |
| T15 | Còn ít nhất 300 phút trước overnight hard stop; disk ≥20 GB; RAM safe; S1/live disabled |

Quy tắc outcome:

- `V7_LOCKED` **không** tự động cho V8 chạy; vẫn cần T01–T15.
- `V7_REJECT_ALL` vẫn được phép chuyển V8 vì đây là terminal scientific result hợp lệ.
- `V7_INVALIDATED` hoặc bất kỳ integrity blocker nào: dừng toàn bộ, không V8.
- Nếu thiếu thời gian: `V8_NOT_STARTED_TIME_GUARD`, không launch nửa chừng.

### 17.4 Topology V8 và parallel work

Không tái sử dụng V7 worktree để viết V8. Tạo topology mới từ `V8_BOOTSTRAP_SHA`:

| Role | Worktree | Nhiệm vụ |
|---|---|---|
| A1 | root integration | controller, merge, transition authority |
| A2 | `../my-quantitative-v8-wt/a2-data` | six-alt two-year data/PIT/provenance |
| A3 | `../my-quantitative-v8-wt/a3-engine` | weekly schedule, reversal dispatcher, artifacts |
| A4 | `../my-quantitative-v8-wt/a4-finalizer` | V8 gates/score/global-ledger cohort rules |
| A5 | `../my-quantitative-v8-wt/a5-reproduction` | reproduction/stress/reconciliation |
| A6 | `../my-quantitative-v8-wt/a6-spec` | preregistration, resolved contract, golden vectors |
| A7 | `../my-quantitative-v8-wt/a7-audit` | independent prelaunch + terminal audit |

Parallel rule:

- A2–A6 được launch song song với session identity thật và allowed paths tách biệt.
- A7 không viết production code và chỉ audit integration SHA.
- Trong khi V7 heavy workers đang chạy, V8 A2–A6 chỉ được chuẩn bị trong isolated worktrees; không đọc V7 result paths và không merge vào root trước V7 terminal.
- Merge V8 sau valid V7 terminal theo thứ tự `A2 → A3 → A4 → A5 → A6`; targeted tests sau mỗi merge, full suite sau integration.
- Tối đa hai heavy V8 workers; bốn trials chạy hai wave.
- Nếu Orca không tạo được agent/worktree thật, đóng `V8_NOT_STARTED_TOPOLOGY_BLOCKED`; không để A1 giả lập tất cả roles.

### 17.5 V8 execution schedule khi còn ≥300 phút

| Relative time | Công việc |
|---|---|
| 00:00–00:30 | Transition snapshot, V8 topology/identity gates |
| 00:30–01:45 | A2–A6 parallel implementation/evidence completion |
| 01:45–02:30 | Merge, targeted/full tests, resolved contract, clean baseline |
| 02:30–03:00 | A7 independent V8 prelaunch audit |
| 03:00–03:30 | Wave 1: `WREV-3D + WREV-7D` |
| 03:30–04:00 | Wave 2: `WREV-14D + WMOM-7D-CONTROL` |
| 04:00–04:40 | Stress + reproduction + FG0–FG7 + score |
| 04:40–05:00 | A7 terminal audit, master report, shutdown |

Thời gian là budget, không phải lý do giảm test. Nếu bất kỳ pha trễ làm remaining time không đủ để audit/close, không launch wave tiếp theo.

### 17.6 V8 hard gates và scoring

Áp dụng FG0–FG7 và scorecard 100 điểm tại §9–§10, với bổ sung:

- all three folds net-positive;
- PF ≥1.10; MDD ≤10%; net PnL >0 after funding/costs;
- ít nhất hai adjacent formation lookbacks trong `[3D,7D,14D]` cùng PASS;
- top positive fold ≤50%; top positive symbol ≤40%;
- reverse/momentum control không được thắng best reversal candidate;
- fee ×1.5, adverse +2 ticks, one-event delay vẫn dương;
- drop-one-symbol, drop-one-fold và rebalance-day shift `+1 day` là preregistered diagnostics;
- independent reproduction 4/4;
- weekly signal count và fold breadth đạt minimum được freeze trước run;
- không lookahead tại completed-bar/weekly boundary.

Statistical contract:

- Global trial ledger/DSR phải đếm toàn bộ trial lịch sử có thể được lựa chọn.
- Không trộn V8 six-alt/two-year/weekly returns vào V6/V7 PBO cohort nếu timestamps/universe/execution không comparable.
- PBO unavailable không được bịa hoặc hạ minimum. Khi PBO chưa đủ comparable configurations, V8 tối đa là `STAGE_A_PASS_EXPLORATORY`, chưa được lock cho S1.

### 17.7 V8 terminal outcomes

- `V8_STAGE_A_PASS_EXPLORATORY`: hard gates PASS nhưng còn statistical/forward evidence; không S1/live trong sprint.
- `V8_LOCK_FOR_FUTURE_S1`: chỉ khi toàn bộ hard/statistical gates gồm valid PBO PASS và A7 ký; chỉ tạo future S1 contract, không đọc S1.
- `V8_REJECT_ALL`: không candidate đạt; kết quả hợp lệ.
- `V8_INVALIDATED`: integrity/lookahead/provenance/reproduction failure; cách ly results.
- `V8_NOT_STARTED_*`: V7 transition, topology, audit, resource hoặc time guard không đạt.

### 17.8 Unattended fail-safe cho cả đêm

- Hard stop tuyệt đối: 12 giờ từ `overnight_started_at_utc`; không tự gia hạn.
- Heartbeat mỗi 60 giây gồm phase, progress, owned PIDs, last artifact, disk/RAM và deadline.
- Heartbeat stale >10 phút: controller dừng owned heavy worker, ghi forensic event; không tự retry nếu đã có scored metric.
- Không performance retry, không tuning, không trial replacement.
- Pre-engine failure chỉ relaunch khi output được archive, chưa có scored artifact và A7/contract cho phép.
- Không quá hai heavy workers; agent reasoning/test nhẹ có thể song song.
- Disk <20 GB, memory pressure nghiêm trọng, hash drift, dirty production tree, target-dir collision hoặc PID không thuộc owner: dừng launch mới.
- Mỗi wave phải atomic; không đọc partial PnL để đổi wave sau.
- Dù PASS/FAIL/timeout, cuối đêm phải dừng heartbeat/workers, ghi shutdown report và để next safe action rõ ràng.
- Không S1, paper trading, live trading, API keys hoặc order placement.

### 17.9 V8 artifact contract

```text
research/control/v8_overnight_run/
research/audits/v8p/
research/audits/v8/
results/portfolio_v8/
results/reproduction_v8/
results/matrix/v8_xsect_weekly_reversal/
results/registry/shards/v8_*.jsonl
research/wayfinder/evidence/sprint-v8-master-20260826.{md,json}
```

Mọi artifact phải có schema, UTC timestamp, V7 parent transition, source/launch SHA, candidate/config/data hashes và parent references.

### 17.10 Lệnh bổ sung cho A1 trước khi chạy xuyên đêm

```text
PLAN.md nay bao gồm conditional V8. Thay đổi PLAN này phải được commit trước final
V7 launch baseline; nếu PLAN/production code thay đổi sau attestation thì regenerate
baseline và A7 re-attest. Không dùng attestation cũ.

Trước scored metric V7 đầu tiên:
1. Tạo/freeze H-XSECT-REVERSAL-v2 candidate, hypothesis, status và novelty memo đúng §17.2.
2. Ghi spec hash + frozen_at_utc + current global-trial-ledger count.
3. A7 xác nhận freeze xảy ra trước V7 first_scored_at_utc.
4. Chỉ sau đó mới launch V7.

Trong lúc V7 chạy, có thể launch A2–A6 V8 trong worktree riêng để chuẩn bị code/tests,
nhưng cấm đọc results/portfolio_v7, logs/metrics/verdict và cấm merge V8 vào root.

Sau V7 terminal:
- Evaluate T01–T15 bằng machine-readable transition_gate.json.
- Chỉ `V7_LOCKED` hoặc `V7_REJECT_ALL` hợp lệ mới có thể authorize V8.
- Nếu PASS 15/15 và remaining >=300 phút: merge/audit/freeze V8 rồi chạy đúng 4 trials
  theo hai wave, tối đa hai heavy workers.
- Nếu bất kỳ gate FAIL: không V8; tạo V8_NOT_STARTED_* và shutdown sạch.
- V8 không được dùng để rescue/tune V7 và không được mở S1/live.
```
