# OWNER PACKET — ERP-TRACKB-PROGRAM-V1 + ERP1-TRACKB-COHORT-1 (BTCUSDT spot–perp delta-neutral basis/carry)

- Ngày: 2026-09-26. Lead phiên A1 dưới umbrella `ECONOMIC-ROBUSTNESS-PROGRAM-V1`
  (ACTIVE_LIGHT 0/0, registry authority).
- Trạng thái phiên: **DỪNG TẠI GATE GO-1**. Không registered, không worker,
  không download, không scored cell, không sealed look, không S1, không
  order, không shadow/dashboard thay đổi. Prompt mở hướng của owner KHÔNG bị
  đọc là GO-2 hay GO-3 (nguyên văn chỉ thị).

## 1. Re-measure intake (2026-09-26, root checkout)

```text
HEAD          main @ e4e3b9159685b9da0bafeed6814f0a73c872cbcb
heavy lock    FREE_PROVEN (worker cuối: FAILED cohort-2 build, đã release)
ERP1          ACTIVE_LIGHT 0/0 — umbrella sống
GO đã consumed: A1/A2/A3 amendments (25 Sep), TRACKA-COHORT-2 GO-1 (26 Sep)
GO đang chờ owner (không liên quan lane này): ETHUSDT-V2 STOP-1 phrase;
  PSCTV1 A4-draft portfolio GO (draft, chưa gõ)
owner changes  .zcode/, plan_at.md, A4-draft, SHARED-PORTFOLIO-100K-V1/,
              SANDBOX-OVERFIT-3ASSETS/, d2_curiosity_v1_sources/ + file mới
              ERP1 — GIỮ NGUYÊN, không stage (P0-4)
siblings      CHR3F ACTIVE_LIGHT (scored execution theo registry phase —
              re-measure tại GO-1; heavy lock machine-wide vẫn áp dụng);
              ETHUSDT-V2 ACTIVE_LIGHT chờ GO riêng
doctor        HIGH findings còn lại = class TERMINAL-pause-packet chấp nhận-
              historical (P0-3, owner D9)
```

## 2. Bàn giao (5 artifacts + 6 council artifacts, tất cả đã commit theo pathspec)

| Artifact | Path |
|---|---|
| Master plan (charter Track B) | `plans/PLAN_erp_trackb_program_v1.md` |
| Child plan cohort-1 | `plans/PLAN_erp1_trackb_cohort_1.md` |
| Council: proposer (blind) | `research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/trackb_cohort1/PROPOSER_cohort1_REPORT.md` |
| Council: PIT/data auditor | `.../trackb_cohort1/PITDATA_cohort1_REPORT.md` |
| Council: economic skeptic (VETO) | `.../trackb_cohort1/SKEPTIC_cohort1_REPORT.md` |
| Council: cost/execution auditor (BLOCKED) | `.../trackb_cohort1/COSTEXEC_cohort1_REPORT.md` |
| A7 plan-audit (fresh context) | `.../trackb_cohort1/A7_trackb1_plan_audit_REPORT.md` |
| Handoffs `zcode_orch_v3_handoff@1` ×6 | `.../trackb_cohort1/HANDOFF_trackb1_*.json` |

A7 plan-audit verdict: **PASS_WITH_CONDITIONS** (0 CRITICAL / 2 HIGH / 3
MEDIUM / 3 LOW). Cả 2 HIGH + 3 MEDIUM đã disposition vào text plans TRƯỚC
commit (F2 relabel cửa sổ seam; F7 pin membership sealed-pass = M1 ANCHOR
only, DTX/N1/N2 không bao giờ nhìn; erratum 18→7 cells; citation CHR3F;
verify nguồn thêm FAMILY_FAILURES/MAP).

## 3. Data/cost feasibility (đo được)

- **Khả thi về dữ liệu** (PITDATA): funding PIT law đã có code sẵn
  (`research/funding_pit.py`, settled-only, no forward-fill); fapi floor
  2020-07-18, vision funding từ 2019-09-10 (prefix single-source bị loại
  theo luật exclusion-not-merge); checklist GO-1 gồm 14 item; rủi ro lớn
  nhất: (i) Predicted funding từ premium-index (đã cách ly cấu trúc),
  (ii) join close-stamped vs open-stamped (đã phát hiện, có fixture),
  (iii) spot BTCUSDT bars chưa stage ở đâu (việc bounded, heavy-lock).
- **Chi phí** (COSTEXEC): 5 thành phần MEASURED-path / 4 DECLARED-required /
  3 BLOCKED. Trần F-5 vận hành: **45–60 bps all-in @×2.0** (gồm band outage).
  Số liệu breakeven verify: 12.4–15.5 ngày ở mean carry ×2.0; downtrend
  18–23d ×1.0 → 36–45d ×2.0; một settlement −0.30%/8h = 1.2–1.5 full RT
  (erratum sửa "2.5" của umbrella). Kết luận trung thực: book 100k
  unlevered chỉ qua được trần ở các hold ≥6–8 tuần trong regime funding
  dương; downtrend nằm NGAY trần (knife-edge).
- **Vốn chung 100k**: một book hai chân (đề xuất freeze N=65k spot / M=35k
  margin, 1:1 hedge), stress ×1.5/×2.0 mọi thành phần + funding-path stress;
  so với cash / long BTC / perp-only-khả-thi; thiếu bằng chứng ⇒ BLOCKED.

## 4. Slate cohort-1 (đóng băng từ council mù-kết-quả, hash-pin tại GO-1)

- **1 mechanism: M1 TB1-DN-CARRY-CTG** — cash-and-carry gate bằng bất đẳng
  thức khả thi (expected carry ≥ hóa đơn RT ×2.0, tính trên phân phối
  settled gần, không phải archive mean), hold cố định, clock tuần. 6
  arm-classes: anchor 35d + neighbours 28d/42d + causal (entry-timing
  permutation) + inverted (book trong trạng thái bị gate loại) + baseline
  set. + 1 arm diagnostic DTX (exit-gate theo âm-run, sign-scramble null,
  không bao giờ được chọn làm anchor).
- **Slot 2–3: EMPTY** theo F-0 court (P-27): skeptic chỉ ADMIT 1 class;
  7 class khác VETO/STRUCTURAL (basis-level=BASISLV, funding-momentum=V17
  FUNDJUMP, vol-gate, calendar, cross-sectional=XSECT, OI=OITD,
  post-cascade=liquidation tape BLOCKED; inverse=borrow BLOCKED).
- **Budget: 7 scored cells**. Trial ledger schema + P-9 + DSR/PBO fail-closed.
- Kỳ vọng trung thực của council: **prior bị giết trước PnL = 0.70–0.80**
  (F-1 ancestry rho là killer hợp thức — class A monotone theo funding
  level, các tiền lệ V16/V17 đo 0.19–0.24 sát/ngưỡng 0.20). Đóng cohort với
  0 scored cell là kết quả hạng nhất.

## 5. Kill rules + luật chống cứu (nguyên văn chỉ thị owner, nhúng vào plan)

Không cứu họ đã chết bằng: đổi tên / đổi tham số / đổi timeframe / giả định
maker fill / giảm phí. KILL_*: KILL_COST_CEILING, KILL_INVERSION,
KILL_CONTROL_REPRODUCED, KILL_BETA_EXPLAINED, KILL_PIT_SEAM, rho breach,
concentration breach; TIME-STOP 60 ngày; không thay arm giữa cohort; sealed
OOS đúng một lần (chỉ M1 anchor + companions); replication độc lập (engine
viết lại, không import); loop cohort kế tiếp chỉ khi có thông tin mới được
cấp quyền; dừng ở NO_CANDIDATE khi giả thuyết cạn.

## 6. Các GO phrase (gõ ĐÚNG NGUYÊN VĂN, MỚI, tại gate của chính nó)

```text
GO-1 (đăng ký + đóng băng + data gate + falsifiers — DỪNG):
  GO ERP1 TRACKB COHORT 1 REGISTER AND FREEZE
GO-2 (chỉ sau A7 prelaunch PASS):
  GO ERP1 TRACKB COHORT 1 SCORED
GO-3 (chỉ nếu identity sống sót dev gates; một lần):
  GO ERP1 TRACKB COHORT 1 SEALED OOS AND REPLICATION
```

## 7. Quyết định owner cần (D-B1..D-B4) + khuyến nghị

- **D-B1**: duyệt charter + child plan, gõ GO-1 (hoặc từ chối).
- **D-B2**: duyệt ngân sách 7 cells.
- **D-B3**: xác nhận các giới hạn cấu trúc: single-venue (limb replication
  (iii) BLOCKED — trần verdict là CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION,
  không bao giờ "replicated" trong chương này); dev evidence toàn bộ
  ANCESTRY_EXPOSED_DEV (chỉ kill + engineer); bằng chứng promote duy nhất =
  tích lũy prospective sau freeze (wall-clock nhiều tuần/tháng sau GO-2).
- **D-B4**: KHÔNG cấp nguồn mới (venue thứ hai, bookTicker depth history) —
  mặc định fail-closed; mở = quyết định riêng.

**Khuyến nghị của Lead: GO cho GO-1 (D-B1/D-B2), với kỳ vọng chết sớm là
kết quả bình thường.** Lý do: đây là lần đầu Track B được tổ chức đúng luật
(council mù, F-0 trước rho trước PnL, cost ceiling đo được, 100k một book);
ngay cả khi F-1/F-5 giết cohort với 0 cell, câu hỏi "carry BTC có sống sót
qua ancestry + cost không" được trả lời bằng bằng chứng với chi phí thấp
nhất có thể. Nếu owner muốn dừng ở đây: mọi artifact là draft vô hại, không
tiêu tốn GO nào, không đụng surface đang sống.

## 8. Phép lệnh đăng ký đề xuất (chỉ chạy SAU khi GO-1 được gõ)

```bash
.venv/bin/python research/researchctl.py cycle register \
  --cycle ERP1-TRACKB-COHORT-1 \
  --asset crypto \
  --plan plans/PLAN_erp1_trackb_cohort_1.md \
  --branch orca/erp1-trackb-cohort-1-integration \
  --worktree .worktrees/erp1-trackb-cohort-1/integration \
  --budget-max 7 --lifecycle ACTIVE_LIGHT \
  --reason "Owner GO-1 2026-09-26 (phrase typed at gate); Track B child per umbrella §10.6 + program charter"
```

(Đối chiếu `researchctl cycle register --help` trước khi chạy; worktree do
A1 tạo sau đăng ký theo playbook §31.)
