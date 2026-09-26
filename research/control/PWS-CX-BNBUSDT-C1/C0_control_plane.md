# Phase C0 — Control plane & collision — PWS-CX-BNBUSDT-C1

- Thời điểm: 2026-09-26T14:1xZ (21:1x+07). A1/Lead, GO-1 execution.
- `researchctl locks inspect`: **FREE_PROVEN** (no holder; last history row =
  SRLV-CX-C1 run_go2 đã xong từ sáng) — không lock-drift ⇒ không BLOCKED (P0-2).
- Registry row `PWS-CX-BNBUSDT-C1` đăng ký qua researchctl (register + update
  head 363cf282, ACTIVE_LIGHT, budget 0/18, GO-2 phrase REGISTERED chưa tiêu);
  GO RECORD tại root `research/control/PWS-PROGRAM-V1/GO1_RECORD_PWS-CX-BNBUSDT-C1_2026-09-26.json`.
- workers = 0 cho child; không shadow worker bị đụng (PROSPECTIVE-SHADOW-V1,
  FX-RANGEFADE, ILLIQ, gateway chạy dưới cycle riêng, không giữ heavy lock).
- **Parallel-session disclosure (P0-2 record-not-block):** một session Lead
  khác đã đóng two-half PWS-CX-SOLUSDT-C1 (root c0ddf816, registry TERMINAL
  13:57:18Z) và dừng EDGE-SCANNER-TOOLING-V1 trước GO-2 (b04447f0) trong khi
  sprint này dispatch — không xung đột file/worktree với child này; registry
  ghi qua researchctl (unique cycle_id) là cơ chế chống double-register.
  Session đó cũng ghi OWNER_PACKET §6 khuyến nghị "pair #2 chỉ mở kèm thông
  tin mới" — child plan này làm khuyến nghị đó thành luật bind (§1 novelty
  test); tiebreaker là chỉ thị owner sprint 13:41Z ("kiểm tra pair kế tiếp
  theo luật PWS").
- Va chạm cycle sống: ETHUSDT-OPEN-SEARCH-V2 (ACTIVE, STOP-1 chờ GO) — không
  tiêu phrase/surface S1, không re-stage corpus (kể cả corpus 7-series có
  BNB); CRYPTO-HISTORICAL-REPLICATION-3F-V1 — heavy lock tôn trọng; không
  restart/sửa shadow workers. Worktree terminal SOLUSDT = append-only
  evidence (lane chỉ đọc chéo nếu cần, disclosed).
- Kết luận C0: **PASS** (điều kiện mở C1/C2/C3). Không phát hiện blocker.
