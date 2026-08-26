# SPRINT V8R — Context Recovery → V8 Core → conditional V8X-Crypto

> **Đối tượng:** một A1 hoàn toàn mới, không có context của phiên agent trước.
>
> **Mục tiêu:** tiếp quản 7 worktree đã hoàn thành phần lớn code, sửa các sai lệch khoa học còn lại, tích hợp có kiểm toán, chạy đúng 4 trial V8 đã đóng băng và chỉ mở V8X-Crypto khi toàn bộ gate hợp lệ.
>
> **Không phải mục tiêu:** gọi lại 7 agent để làm từ đầu, cứu một strategy bằng tuning, mở S1/live, hoặc chạy equity khi data/spec chưa hợp lệ.

---

## 1. Sự thật bàn giao đã được kiểm tra

### 1.1 Root và sprint cũ

- Root repository: `/Users/hoangminhlong/my-quantitative`.
- Bootstrap HEAD hiện tại: `291a158` — `V8 BOOTSTRAP: sprint contract (V8P→V8→conditional V8X)`.
- Parent V7 closure: `72eada1`.
- Root có artifact chưa track: `research/control/v8_run/worktree_manifest.json`.
  - Không xóa, không overwrite mù và không dùng `git clean`.
  - Manifest này là bằng chứng topology cũ nhưng đang stale: session ID vẫn `PENDING_ACK`, commit/lifecycle chưa phản ánh output thật.
- Sprint cũ bắt đầu `2026-08-25T14:45:53Z`, deadline bất biến `2026-08-26T02:45:53Z`.
- Phiên cũ bị mất context trước integration. Không được đổi timestamp rồi giả vờ cùng một sprint.
- Chưa có scored artifact V8 hoặc V8X. Vì vậy được phép tạo một lineage phục hồi mới mà không tiêu tốn trial budget.

### 1.2 Output thật từ bảy worktree

| Role | Branch / worktree | Tip đã bàn giao | Trạng thái | Verdict tiếp quản |
|---|---|---:|---|---|
| A2 | `orca/v8-a2-core-data` / `../my-quantitative-v8-wt/a2-core-data` | `300391d` | clean | code tốt; T12 chỉ provisional vì funding thiếu đầu window 41.25 giờ chưa chứng minh không chồng held exposure |
| A3 | `orca/v8-a3-weekly-engine` / `../my-quantitative-v8-wt/a3-weekly-engine` | `b6743aa` | **dirty** | engine merge được; golden chứa absolute pytest temp path nên không deterministic |
| A4 | `orca/v8-a4-finalizer` / `../my-quantitative-v8-wt/a4-finalizer` | `846ecd5` | clean | sẵn sàng integration |
| A5 | `orca/v8-a5-reproduction` / `../my-quantitative-v8-wt/a5-reproduction` | `1b388ab` | clean | sẵn sàng integration |
| A6 | `orca/v8-a6-contract-golden` / `../my-quantitative-v8-wt/a6-contract-golden` | `0857c7b` | clean | template/prereg có ích; contract chưa được resolve ở integration SHA |
| A7 | `orca/v8-a7-independent-audit` / `../my-quantitative-v8-wt/a7-independent-audit` | `291a158` | clean | chưa audit vì chưa có integration SHA |
| A8 | `orca/v8-a8-crypto-breadth` / `../my-quantitative-v8-wt/a8-crypto-breadth` | `4f1d704` | clean | **không đạt scientific conformance**, cần follow-up |
| A9 | `orca/v8-a9-equity-breadth` / `../my-quantitative-v8-wt/a9-equity-breadth` | `d053f0c` | clean | kết luận blocker hợp lệ; equity không được chạy |

Không được tin bảng này một cách mù quáng. A1 phải đo lại `git status --short`, `git rev-parse HEAD`, branch và path của từng worktree trước khi làm.

### 1.3 Kết quả rehearsal integration

Một integration clone tạm đã cherry-pick bảy commit theo thứ tự:

```text
300391d → b6743aa → 846ecd5 → 1b388ab → 0857c7b → 4f1d704 → d053f0c
```

Kết quả đã đo:

- Không có cherry-pick conflict.
- Targeted new tests: `146 passed in 13.42s`.
- Full suite: `835 passed, 16 warnings in 62.73s`.
- Warnings đã thấy là deprecation của pandas trong `tests/test_execution_truth.py`, không phải test failure.

Điều này chỉ chứng minh code ghép được. Nó **không** chứng minh T12/T13/T14 hoặc scientific validity đã PASS.

---

## 2. Bốn blocker phải sửa trước bất kỳ V8 backtest nào

### B1 — A3 golden không deterministic

`research/audits/v8p/golden_vector_report_v8.json` đang thay đổi chỉ vì absolute pytest temp directory (`pytest-522` thành `pytest-523`).

PASS khi:

1. Serializer loại bỏ/canonicalize machine-specific absolute temp paths.
2. Chạy generator hai lần trong hai temp directories khác nhau tạo byte-identical canonical artifact và cùng SHA-256.
3. Targeted tests và full relevant surface PASS.
4. Worktree A3 sạch và có follow-up commit mới; không giao file dirty cho A1.

### B2 — T12 funding coverage chưa được chứng minh đúng

A2 tìm thấy funding coverage ngắn hơn price window khoảng 41.25 giờ ở đầu kỳ. Không được dùng ngưỡng materiality tự đặt hoặc chỉ kiểm tra “có funding rows”.

PASS khi có machine-readable proof cho từng symbol:

- xác định first possible fill/held exposure theo warmup + Monday schedule + next-event fill;
- funding đầy đủ từ first possible held exposure đến final liquidation;
- không có missing settlement chồng lên thời gian giữ vị thế;
- nếu có overlap: `T12_FAIL_FUNDING_COVERAGE`, không launch V8;
- không trim window chỉ để né lỗi, trừ khi frozen contract rõ ràng cho phép và A7 xác nhận.

T12 hiện chỉ là `PROVISIONAL_PENDING_HELD_EXPOSURE_PROOF`, không phải PASS cuối.

### B3 — A8 crypto selection vi phạm frozen rule

A8 phải sửa các lỗi sau:

1. Ranking volume đã dùng cả scored one-year window; frozen rule yêu cầu 30 ngày **strictly before** scored window.
2. BTC là benchmark measurement-only nhưng A8 đã đưa BTC vào top-10 traded universe.
3. Gap audit mới thiên về daily; yêu cầu là census 15m exact và zero unexplained gaps.
4. Funding gate chỉ kiểm tra `>=1 row`; phải kiểm tra đủ toàn khoảng có thể held exposure.

Corrected selection contract:

- selection window: `[2025-07-22T00:00Z, 2025-08-21T00:00Z)` hoặc exact UTC boundaries được resolved contract pin;
- rank median daily quote volume chỉ trong pre-window đó;
- BTC bị loại khỏi ranked/traded universe, chỉ giữ làm benchmark;
- chọn đúng 10 eligible altcoins theo deterministic tie-break đã freeze;
- 15m gap census, listing age, metadata, funding-held-exposure coverage đều machine-readable;
- tuyệt đối không đọc V8/V8X PnL để thay symbol.

### B4 — Manifest và identity stale

Manifest hiện chưa chứng minh agent nào thực sự làm commit nào.

PASS khi manifest phục hồi ghi đúng:

- Orca task/session identity thật; nếu không truy xuất được thì ghi `UNKNOWN_NOT_RECOVERABLE`, không bịa ID;
- worktree path, branch, bootstrap SHA, actual tip, dirty/clean;
- allowed/forbidden paths, artifacts, tests, handoff verdict;
- commit nào được merge, superseded hoặc rejected;
- hash nối tới manifest sprint cũ.

---

## 3. Blocker riêng của equity V8X

### 3.1 Data provider blocker

A9 xác nhận:

- Binance TradFi universe hiện không có đủ 10 mã với ≥365 ngày dữ liệu hợp lệ;
- external equity mode thiếu provider credentials/SDK, exchange calendar và corporate-action contract.

Verdict bắt buộc:

```text
V8X_EQUITY_NOT_STARTED_PROVIDER_BLOCKED
```

Không download tùy tiện, không giả lập dữ liệu, không dùng stock spot bars như Binance perpetual và không chạy scored equity trial trong sprint này.

### 3.2 Spec mapping blocker

Frozen equity v1 chứa mapping `formation_lookbacks_sessions: [15,25,50]` với mô tả xấp xỉ `3D/7D/14D`. Mapping này không tương đương về mặt thời gian và chưa được owner phê duyệt.

- Không sửa frozen v1 in-place.
- Append audit/addendum đánh dấu `SPEC_MAPPING_AMBIGUITY_BLOCKED`.
- Một equity v2 chỉ được tạo trong sprint tương lai, trước mọi equity score và sau owner approval.

---

## 4. Topology phục hồi — dùng worktree cũ, chỉ gọi agent cần thiết

A1 mới là controller/integration owner. Không gọi lại cả bảy agent.

### 4.1 Wave R0 — read-only recovery

1. Đọc `PLAN.md`, `CONTINUE.md`, old manifest và frozen specs.
2. Chạy `git worktree list --porcelain` và đo tất cả branch/tip/status.
3. Xác nhận chưa có `results/portfolio_v8`, registry cell hoặc scored metric V8/V8X.
4. Ghi old lineage terminal state là:

```text
V8_PREP_CONTEXT_HANDOFF_NO_SCORED_ARTIFACT
```

5. Không đổi old deadline. Tạo control lineage mới:

```text
research/control/v8_resume_run/
```

Nó phải có `parent_manifest_sha256`, `parent_bootstrap_sha`, `resume_started_at_utc`, `hard_deadline_utc`, owner PID/heartbeat và state machine mới.

### 4.2 Wave R1 — ba remediation song song

Chỉ dispatch tối đa ba scoped agents:

| Agent | Worktree | Task | Cấm |
|---|---|---|---|
| R-A2 | existing A2 | funding-held-exposure proof, corrected T12 artifacts, follow-up commit | không đổi strategy/spec/window để né gap |
| R-A3 | existing A3 | deterministic golden, clean dirty file, double-generation proof, follow-up commit | không đổi signal semantics |
| R-A8 | existing A8 | corrected pre-window ranking, exclude BTC, 15m/funding audit, follow-up commit | không xem scored results; không chọn theo PnL |

A1 đồng thời cập nhật recovery manifest và chuẩn bị integration branch/worktree riêng. Không sửa trực tiếp file thuộc worktree agent đang làm.

### 4.3 Wave R2 — review contract/spec

Sau R1:

- A6 scoped follow-up chỉ khi contract builder cần pin corrected T12/T13/A8 artifacts hoặc cần addendum cho equity blocker.
- A7 được gọi như independent auditor; A7 không sửa production code.
- Nếu Orca không thể reattach đúng agent cũ, tạo agent mới nhưng bắt buộc giao đúng existing worktree, branch và phạm vi trên; không tạo duplicate branch.

### 4.4 Resource rule

- Tối đa 3 agent code/audit nhẹ song song trong R1.
- Tối đa 2 heavy backtest workers cùng lúc.
- Chỉ một A1 được sở hữu integration, state machine và merge.
- Không chạy nhiều agent cùng ghi một artifact/path.

---

## 5. Integration protocol

### 5.1 Không tích hợp khi còn dirty

Trước cherry-pick, mỗi source worktree phải có:

- clean status;
- handoff commit;
- exact test command/result;
- artifact hashes;
- declared limitations.

Nếu A3 vẫn dirty hoặc A2/A8 chưa có follow-up commit thì dừng integration.

### 5.2 Thứ tự cherry-pick

Tạo một integration branch/worktree từ `291a158`. Dùng corrected tip thay cho tip cũ nếu agent có follow-up:

```text
A2 corrected tip
A3 corrected tip
846ecd5              # A4
1b388ab              # A5
0857c7b              # A6, cộng follow-up nếu có
A8 corrected tip
d053f0c              # A9
```

Sau mỗi cherry-pick:

1. `git status --short`;
2. targeted tests của commit;
3. kiểm tra file ngoài allowlist;
4. ghi merge ledger.

Sau tất cả:

- chạy targeted V8/V8X tests;
- chạy full suite bằng `.venv/bin/python -m pytest -q`;
- tree phải sạch;
- không được coi kết quả rehearsal 835 PASS là thay thế test trên final integration SHA.

Không `git add -A`, không `git reset --hard`, không `git clean`, không force push.

---

## 6. Resolve contract, baseline và T14

Tại final code-bearing integration SHA:

1. Generate resolved V8 contract; không còn `PENDING`, `TO_FREEZE`, `None` ở launch-critical field.
2. Pin chính xác:
   - launch SHA;
   - frozen hypothesis/spec hashes;
   - data manifest và T12 hashes;
   - deterministic golden hash;
   - exact four trial IDs/configs/windows/folds;
   - output roots, registry shards và execution topology.
3. Generate canonical baseline tự loại trừ các artifact mutable được khai báo.
4. Tạo detached clean execution worktrees tại đúng launch SHA.
5. Preflight phải kiểm tra tối thiểu:
   - T01–T15 = `15/15 PASS`;
   - T12 held-exposure funding proof PASS;
   - T13 golden deterministic proof PASS;
   - baseline/contract/manifest/launch pins khớp;
   - execution heads sạch và đúng SHA;
   - no scored V8 artifact trước launch;
   - no S1/live/order capability.
6. A7 audit độc lập và phát hành T14 attestation.

Chỉ khi A7 verdict là `PASS` và `V8_LAUNCH_AUTHORIZED` mới chuyển sang V8. A7 không được tự sửa blocker rồi tự attest.

---

## 7. V8 core execution — đúng bốn trial đã freeze

Không thêm, bỏ, đổi lookback, symbol, fee, fill, fold hoặc window sau khi thấy kết quả.

### Wave 1 — tối đa hai workers

```text
XSECT-WREV-3D
XSECT-WREV-7D
```

### Wave 2 — chỉ sau Wave 1 process/accounting validation

```text
XSECT-WREV-14D
XSECT-WMOM-7D-CONTROL
```

Mỗi trial:

- frozen command từ resolved contract;
- unique output dir và registry shard;
- stdout/stderr log, PID, start/end, exit code;
- provenance enforced;
- một trial publish scored metric thì budget đã tiêu thụ;
- technical retry chỉ theo frozen retry contract, không performance retry.

Sau bốn trial:

1. artifact/accounting reconciliation;
2. stress suite;
3. independent reproduction `4/4 all-match`;
4. FG0–FG7, score, DSR/PBO honesty;
5. concentration/fold/symbol checks;
6. A7 terminal audit;
7. terminal verdict, kể cả `V8_REJECT_ALL_CANDIDATE`.

Không coi PF tốt là đủ nếu provenance/reproduction/gate thất bại.

---

## 8. Điều kiện duy nhất để chuyển V8 → V8X-Crypto

V8X-Crypto chỉ được mở nếu **tất cả** điều sau đúng:

1. V8 có terminal audit hợp lệ; không còn worker/PID/artifact dang dở.
2. V8X prereg/freeze được A7 xác nhận xảy ra trước scored V8 artifact đầu tiên.
3. Corrected A8 universe audit PASS, BTC benchmark-only và đúng pre-window selection.
4. Engine/golden/resolved contract thực sự hỗ trợ cohort 10 crypto; selection artifact một mình không đủ.
5. V8X baseline/preflight/A7 attestation riêng PASS.
6. Còn ít nhất 300 phút trước resume hard deadline.
7. V8X có budget riêng được frozen; không mượn budget hoặc parameter từ V8.

Nếu một điều kiện sai:

```text
V8X_CRYPTO_NOT_STARTED_GATE_BLOCKED
```

Không phải sprint failure; đó là shutdown an toàn.

V8X equity luôn NOT_STARTED trong sprint này vì hai blocker ở §3. Crypto và equity không được gộp data, costs, sessions, metrics hoặc verdict.

---

## 9. Deadline và unattended fail-safe

- Resume sprint có tối đa 12 giờ tính từ `resume_started_at_utc`; deadline phải freeze trước mutation đầu tiên.
- Old sprint deadline giữ nguyên trong historical record.
- Heartbeat ghi phase, owner PID, live child PIDs, last artifact, remaining time và blocker.
- Nếu remaining <300 phút: không launch V8X.
- Nếu remaining <120 phút: không launch V8 wave mới; ưu tiên validation/close wave đã chạy.
- Nếu remaining <45 phút: hard shutdown, terminate owned workers, reconcile artifacts, A7 audit phần đã chạy và ghi terminal state trung thực.
- Không để shell monitor/sleep loop trở thành “agent đang làm việc”. Mọi worker phải có PID, log và output contract.
- Không tự động push remote.

---

## 10. Definition of Done

### V8R preparation DONE

- Old lineage đóng `PREP_CONTEXT_HANDOFF`, không sửa deadline.
- Recovery manifest có identity/tip/status/merge truth.
- A3 deterministic golden proof PASS và clean commit.
- T12 held-exposure funding proof PASS.
- Corrected A8 selection/data audit PASS.
- Equity blockers được ghi rõ, không scored run.
- Final integration full suite PASS và tree sạch.
- T01–T15 = `15/15 PASS`.
- A7 T14 = `V8_LAUNCH_AUTHORIZED`.

### V8 DONE

- Đúng 4/4 frozen trials, không trial thứ năm.
- Stress/reproduction/accounting/FG/score hoàn tất.
- A7 terminal audit và one terminal verdict.
- S1/paper/live vẫn disabled.

### V8X-Crypto DONE hoặc SAFE NOT-STARTED

- Chỉ chạy nếu §8 đạt toàn bộ.
- Nếu chạy: contract/baseline/attestation/results/reproduction/audit riêng hoàn chỉnh.
- Nếu không: blocker machine-readable, không partial scored launch.
- Equity verdict vẫn là provider/spec blocked, không được giả thành test failure.

---

## 11. Prompt hoàn chỉnh cho A1 context mới

Copy nguyên khối dưới đây vào một agent mới:

```text
Bạn là A1 mới, controller và integration owner của repo
/Users/hoangminhlong/my-quantitative.

Phiên agent trước đã gọi 7 agent và mất context trước integration. Hãy tiếp quản,
KHÔNG làm lại từ đầu. Đọc toàn bộ PLAN.md và CONTINUE.md trước khi mutation.
PLAN.md là execution contract hiện hành; frozen specs và evidence là source of truth.

MỤC TIÊU:
1) đóng lineage cũ dưới dạng V8_PREP_CONTEXT_HANDOFF_NO_SCORED_ARTIFACT;
2) tạo lineage V8R mới với start/deadline thật, không kéo dài deadline cũ;
3) reattach các existing worktree/branch;
4) sửa đúng ba blocker A2/A3/A8;
5) integrate các commit đã làm, chạy targeted + full suite;
6) resolve contract/baseline, cho A7 audit T14;
7) chỉ khi 15/15 PASS và A7 AUTHORIZED mới chạy đúng 4 V8 trials;
8) close V8 bằng stress/repro/score/A7 terminal audit;
9) chỉ chạy V8X-Crypto nếu toàn bộ conditional gate trong PLAN §8 PASS;
10) không chạy V8X equity trong sprint này.

SỰ THẬT BAN ĐẦU CẦN ĐO LẠI:
- root bootstrap dự kiến 291a158;
- root có untracked research/control/v8_run/worktree_manifest.json: bảo tồn;
- A2 300391d clean, A3 b6743aa dirty do golden absolute temp path,
  A4 846ecd5 clean, A5 1b388ab clean, A6 0857c7b clean,
  A7 chưa audit, A8 4f1d704 cần scientific correction, A9 d053f0c blocked hợp lệ;
- rehearsal cherry-pick không conflict; targeted 146 PASS, full 835 PASS,
  nhưng phải test lại trên final integration SHA;
- chưa có scored V8/V8X artifact.

TOPOLOGY:
- Dùng lại worktree trong ../my-quantitative-v8-wt/; không tạo 7 worktree trùng.
- Gọi song song tối đa ba remediation agent:
  R-A2 existing A2: held-exposure funding coverage proof + T12 follow-up commit;
  R-A3 existing A3: canonicalize golden, generate hai lần byte-identical,
       clean tree + follow-up commit;
  R-A8 existing A8: pre-window 30d volume, exclude BTC from traded top10,
       exact 15m gaps và held-exposure funding proof + follow-up commit.
- Nếu không reattach được agent cũ, gọi agent mới vào đúng existing worktree/branch.
- A6 chỉ follow-up contract/spec nếu integration cần. A7 chỉ audit độc lập.
- Không cho hai agent ghi cùng path. A1 duy nhất có merge authority.

QUY TẮC KHOA HỌC:
- Không xem/tuning theo PnL cũ hoặc partial PnL.
- Không đổi frozen V8 hypothesis/spec.
- Không sửa frozen equity v1; ghi SPEC_MAPPING_AMBIGUITY_BLOCKED.
- Equity: V8X_EQUITY_NOT_STARTED_PROVIDER_BLOCKED, tuyệt đối không launch.
- Crypto/stocks tách biệt hoàn toàn.
- Không S1, paper/live, order placement, push remote.
- Không git add -A, reset --hard hoặc clean. Bảo tồn user/untracked files.

TRÌNH TỰ:
A. Read-only inventory: git worktree list, HEAD/status/tips, artifact census,
   xác nhận no scored V8/V8X.
B. Freeze v8_resume_run start/deadline và recovery manifest nối hash old manifest.
C. Dispatch R-A2/R-A3/R-A8 song song; ghi identity thật hoặc UNKNOWN_NOT_RECOVERABLE.
D. Nhận clean follow-up commits và kiểm tra artifacts/tests/hashes.
E. Tạo integration branch/worktree từ bootstrap; cherry-pick corrected A2, corrected A3,
   A4 846ecd5, A5 1b388ab, A6 0857c7b (+ follow-up nếu có), corrected A8,
   A9 d053f0c. Targeted test sau mỗi merge; full pytest cuối.
F. Resolve V8 contract ở final code SHA; baseline/manifest/detached exec trees/preflight.
G. A7 audit: chỉ 15/15 PASS + V8_LAUNCH_AUTHORIZED mới launch.
H. Run V8 Wave 1 (WREV-3D/7D), validate; Wave 2 (WREV-14D/WMOM-7D control),
   tối đa 2 heavy workers; rồi stress/repro 4/4/FG/score/A7 terminal.
I. Đánh giá V8X gate. Chỉ chạy Crypto nếu tất cả §8 PASS và còn >=300 phút.
   Không chạy equity. Nếu gate thiếu, đóng SAFE NOT-STARTED.
J. Reconcile PIDs, tree, registry, evidence; cập nhật CONTINUE.md và master report.

Hãy tự động tiếp tục qua các phase khi gate machine-readable PASS; không hỏi GO lặp lại.
Chỉ dừng hỏi owner khi cần authority mới, có dữ liệu/provider credential bên ngoài,
phải sửa frozen scientific contract, hoặc có destructive/unrecoverable conflict.
Gửi progress ngắn theo phase và báo ngay blocker. Báo cáo cuối phải nêu:
commit graph, tests, T01-T15, trial budget, V8 verdict, V8X status,
A7 verdict, active PIDs, dirty files, artifact paths và next safe action.
```

---

## 12. Cách hiểu ngắn gọn

Các agent trước đã làm xong nhiều “miếng Lego”. A1 mới không đập chúng ra xây lại. A1 kiểm tra ba miếng đang lệch, nhờ đúng ba người sửa, ghép cả bộ, rồi nhờ A7 làm giám khảo. Chỉ khi giám khảo nói chiếc cân đo strategy đã chính xác thì máy mới chạy bốn bài V8. V8X-Crypto là bài thêm nếu còn thời gian và đủ điều kiện; stocks vẫn để sang sprint sau vì chưa có dữ liệu và luật đo đáng tin.
