# Phase C3 — Council synthesis & trial freeze — PWS-CX-BNBUSDT-C1

- Thời điểm: 2026-09-26T15:2xZ (22:2x+07). A1/Lead (GO-1 execution dưới ủy
  quyền chuỗi GO + chỉ thị sprint owner 13:41Z).
- Inputs: C0_control_plane.md (PASS), C1_data_gate_REPORT.md + 2 machine files
  (klines PASS; funding PASS WITH CAVEATS; spread NOT_RUN_DISK_CONSTRAINT với
  df 7GB < 25GB precondition; license PASS), C2_EXPOSURE_VERIFICATION.md
  (CONFIRMED: ELIGIBLE_DEV_BASELINE_EXPOSED; folds F1–F4 pin trước outcome),
  council/P1_PROPOSALS_BNBUSDT.md (0 proposal, 5 autopsies phủ 11 lớp
  direction-source, 0 slot registry tiêu), council/SKEPTIC_VERIFY_REPORT.md
  (SLATE_EMPTY_VERIFIED), handoffs/ (4 handoff JSON đúng schema).

## Kết quả council

- **P1: 0 proposal** — mọi direction source trên lớp observable được cấp quyền
  khớp dead family/fence (5 autopsies: funding-run carry; event-layer BNB =
  BLOCKED_NEW_DATA_OWNER_GATE — revival condition R5 cho owner, không phải
  proposal; ratio/x-section; clock/session; tape/OI/liq).
- **Skeptic-verify: SLATE_EMPTY_VERIFIED bằng số đo trên chính chuỗi BNB**
  (không phải chuyển khẳng định từ SOL): sign persistence lag-1 +0.759,
  P(same nonzero sign) 0.7637–0.9940 ⇒ run-gate ≡ smoothed level; representation
  rho vs CARRY-1D/3D/7D level-window shadows: two-sided θ=0.50 +0.594/+0.527/
  +0.479/+0.383 (W3/W9/W21/W90), neg-only +0.438..+0.237; θ=1.00 +0.556..+0.353
  / +0.423..+0.225 — mọi level-window shadow 1.12×–2.97× bar 0.20, cả hai quy
  ước side đều kill (K-ANC). Asymmetry trung thực: leg vs-unconditional
  KHÔNG vượt bar trên BNB (max |rho| 0.175) — fence bind là họ CARRY
  level-window, đủ để kill.
- **Ceiling×power (fee-only floor, RT 10 bps, θ_min 3.333): 80 PIT episode
  (45 neg-side) — KHÔNG rỗng như SOL, nhưng < sàn ≥100 ở mọi cách đọc PIT**
  (chỉ bracket lookahead hai phía đạt 144 — không eligible); và cost gate
  BLOCKED tối nay (spread NOT_RUN_DISK_CONSTRAINT). K-CONC pre-kill của SOL
  KHÔNG chuyển sang BNB (worst year 25.50%, top-2 45.72% < 0.50) — kill dựa
  trên same-family + K-ANC, không dựa concentration.

## Trial freeze — SLATE TRỐNG

- Số identity frozen: **0/3**. Không cơ chế nào qua F-0 ⇒ không freeze, không
  scored cell, không dry-run, **không GO-2** (per chỉ thị owner sprint:
  cùng thông tin cũ chỉ sinh lại dead family ⇒ ĐÓNG, không chạy backtest).
- GO-2 phrase `GO PWS CX BNBUSDT C1 SCORED EXECUTION` chết UNCONSUMED tại close.
- IDENTITY_REGISTRY: **không thay đổi** — BNB tiêu 0 slot (tổng N_registry
  = 1/100, của SOLUSDT I001). Trial ledger: 0 rows. Denominators P-9
  observed/published KHÔNG đổi (không outcome nào được xem).
- DSR: `NOT_RUN_NO_SCORED_TRIALS` (0 scored trial trong ledger PWS; công khai
  N_registry = 1/100 như cỡ không gian tìm kiếm — master §6.3).

## Verdict đề xuất (chờ A7 terminal)

`NO_ELIGIBLE_PROPOSAL` — council sản xuất 0 cơ chế freezable sau F-0 court
với novelty-bar; 0 scored cells; 0 holdout/OOS looks; S1 SEALED_UNTOUCHED;
không shadow/worker bị đụng; không lệnh.

## Track-level note (cho master) — stop-rule §9(a) kích hoạt

Đây là pair-child #2 LIÊN TIẾP của track PWS-CX đóng slate rỗng (SOLUSDT
NO_ELIGIBLE_PROPOSAL → BNBUSDT NO_ELIGIBLE_PROPOSAL). Master §9(a): **viability
council của track CX bắt buộc trước khi mở pair-child mới**; không pair mới
(BTCUSDT/ETHUSDT) khi không có observable/nguồn/giả thuyết payer mới CÓ BẰNG
CHỨNG — LESSON P-29 "pair-swap không mở lại không gian" nay được đo xác nhận
trên chính chuỗi BNB. Revival conditions: (i) R5-class information layer có
authority qua cổng owner — ứng viên đo sẵn: BNB event calendar (burn quý /
SEC-DOJ 2023 / Launchpool) — W2 autopsy; (ii) dated cost-regime break; (iii)
identity khác ≥2/3 trục. Spread census BNB cần disk trống ≥25GB — chỉ có ý
 nghĩa khi một identity thực sự vượt được F-0.

## Tài sản để lại (durable assets)

- Data plane BNB đã kiểm: klines 57,472 bars GAPLESS floor-exact 2020-02-10
  (khác SOL: 0 lỗ maintenance), funding 7,261 settlements đo riêng (median 0,
  49.6% zero prints, neg_share 23.94%, worst −58.44 bps, 0 deep-print
  ≥75bps, 0 anomalous spacings — pair-contrast thật so với SOL).
- Phương pháp kill rẻ áp dụng lần 2 thành công: representation-rho đo trên
  chuỗi của chính pair + ceiling×power grid + skeptic-verify độc lập.
- Số đo pair-contrast trung thực (asymmetry rho-unconditional, ceiling
  non-empty-but-underpowered, K-CONC non-transfer) — tránh cho các phiên
  sau tái dựng niềm tin sai rằng "BNB khác nên cơ chế cũ sống lại được".
