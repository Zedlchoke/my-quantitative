# VIABILITY_REVIEW_BTCUSDT — DAYTRADE-PLAYBOOKS-PROGRAM-V1 (cấp chương trình, read-only, outcome-blind)

- Authored 2026-09-27 bởi A1/Lead theo owner instruction verbatim intent:
  **chưa đăng ký DTP-CX-BTCUSDT-C1**; review chỉ hỏi một câu — BTC có
  information layer, payer hoặc risk shape MỚI THẬT, khác ≥2 trục theo
  anti-variant law §2.3, với dữ liệu PIT và chi phí có authority, hay không;
  corpus giáo dục nhiều hơn hay đổi pair đơn thuần KHÔNG đủ; không vượt tường
  truy cập Reddit/TradingView; dừng trước GO-1 của BTC; không score/OOS/
  shadow/lệnh.
- Nguồn: DATACOST_FEASIBILITY_MATRIX + OUTCOME_EXPOSURE_MAP (SRLV-PROGRAM-V1),
  FAMILY_FAILURES.jsonl 137 rows, MAP.md (V10/V15/V16/V17, PSV1, EOS1, bear-recon,
  PWS, ERP1-TRACKB, SRLV-CX), DATA-FOUNDATION NEXT_RESEARCH_FRONTIER/authority
  rows, DATA-EDGE-UNLOCK-V1 Lane C, PLAN_daytrade_playbooks_program_v1 §2.3/§5.
  Không đọc PnL/sealed nào (không tồn tại cho chương trình này; các verdict cũ
  được dẫn như bằng chứng chết, không phải outcome của DTP).

## 1. Bề mặt PIT của BTC và trạng thái authority (đo/tăng)

| Bề mặt | PIT authority | Trạng thái chi phí | Ghi chú |
|---|---|---|---|
| Vision klines 1h 2020-01..2026-08; catalog 15m 2024-08+ (CHR3F staged) | keyless PIT_USABLE | fee DECLARED 5bps+1tick (CHR3F frozen); **spread census bookTicker NOT_RUN** | `OUTCOME_EXPOSED` dày nhất chương trình (BTC-H4 ×4, PSV1, EOS1 gates, CHR3F baselines) |
| aggTrades multi-year (V16 đã từng stage) | keyless | chưa có census điều kiện | V16 close: "aggTrades frontier **measured-exhausted ở DAILY clock**; sub-daily là trục chưa test" — nhưng xem §2.3 |
| bookTicker | keyless | census NOT_RUN (SOL từng cần 12GB/6 tháng lấy mẫu; disk 32GiB hiện khả thi — là gate-work, không phải layer mới) | — |
| mark/index/premium multi-year (bear-recon PIT_USABLE) | keyless | — | plane basis/premium: xem §2.4 |
| premiumIndexKlines forecast funding (~7MB, PS1 verified) | keyless | — | plane funding: xem §2.5 |
| daily metrics (OI/taker, V15) | keyless | — | các class V15 đo chết |
| liquidationSnapshot / OI lịch sử / L2 | 404 / none / none | — | `BLOCKED_UNCONSTRUCTIBLE` |
| Options (Deribit) | keyless WS **prospective-only** | — | không có history ⇒ không mở scored lịch sử |
| Cross-venue / ETF / CME | **không gated** (cần data-authority cycle riêng); CME transport blocked (L-FXFF-1) | — | ngoài quyền hiện có |

## 2. Phân tích 3 trục anti-variant (§2.3) — từng ứng viên

Luật: hai identity khác nhau phải khác ≥ HAI trong ba trục (payer+cơ chế ép
trả tiền; information layer PIT; risk shape). F-0 skeleton test BỎ observable
đặc thù, giữ trigger/direction/exit shape — cùng shape = cùng family chết.

### 2.1 Skeleton playbook kinh điển trên BTC (= corpus SOL-C1 đã đo)
- **Payer/mechanism:** không mới — payer lore giống hệt (stop-run, FOMO retest,
  breakout chaser); các skeleton đã đo chết pair-agnostic (death ledger
  DTP-CX-SOLUSDT-C1: 11/11; taxonomy rows 1–11).
- **Information layer:** không mới (klines).
- **Risk shape:** không mới.
- **Kết luận: 0/3 trục ⇒ pair-swap thuần — CẤM theo đúng luật owner.**

### 2.2 Tape microstructure (aggTrades sub-daily) — ứng viên "trục chưa test" duy nhất
- V10 M01-AGGRESSOR-ABSORPTION-PANEL chết BLOCKED_PRELAUNCH (coverage) —
  chưa từng đo kinh tế. NHƯNG skeleton của nó = level-then-absorption, chính
  là shape SRLV-CX M1 SETTLE-RESOLVE đã đo chết CẢ HAI chiều trên BTC/ETH 1h
  (inverted out-earns anchor). F-0 skeleton test bỏ "tape" observable còn lại
  shape absorption tại mức ⇒ **cùng family chết**; tape là dữ liệu tốt hơn
  trên cùng hình, không phải cơ chế mới (P-27 đọc đúng chiều: adding an
  observable/better data is not a new mechanism).
- RUNPERSIST (aggressor run persistence) chết daily (V16); sub-daily re-run =
  re-clock (Q-3) ⇒ CẤM.
- **Kết luận: payer trục có tiềm năng danh nghĩa nhưng skeleton fail; 0-1/3
  trục thực.**

### 2.3 Basis/premium/mark-index plane
- PREMFADE-28D chết fold-conc (V14); ERP1-TRACKB carry identity-killed
  (continuous pooled rho **1.0000** vs CARRY-BAB — "lawful entry observable
  IS the dead carry class's observable"); mark-trigger catch-down VETOED ×3
  (bear-recon). Plane đóng bằng identity.

### 2.4 Funding plane (kể cả forecast funding premiumIndexKlines)
- PWS funding-run chết bằng representation math (sign-run ≈ level-window,
  P-29); CNG2 funding-dodge/settle-adjacent chết; SRLV settle-adjacent chết
  cả hai chiều. Forecast funding = input mượt của chính settled funding —
  representation rho kỳ vọng cao (đo được bằng một buổi như P-29), rào
  pair-agnostic.

### 2.5 Event/exogenous clock (FOMC/CPI/NFP, ETF flows, listings)
- CNG1/CNG2 + FXNG* + FXFV5/6/7: dead class hai track; lịch PIT đủ điều kiện
  không có trên plane này; BNB event-layer tiền lệ = BLOCKED_NEW_DATA_OWNER_GATE.
  Cross-venue/ETF = không gated (cycle data riêng của owner).

### 2.6 Risk shape mới?
- Rào G5 fold-conc cho BTC-long 2020–2026 vẫn nguyên; mọi arm unlevered 1x;
  two-sided là yêu cầu, không phải trục mới. Không có risk shape nào chưa
  expressed mà có payer + information đi kèm.

## 3. Chi phí có authority?

BTC hôm nay **YẾU HƠN SOL**: spread census NOT_RUN (SOL có p50 0.469bps đo);
fee vẫn DECLARED; funding measured (11.798%/yr). Disk 32GiB hiện đủ cho một
census lấy mẫu — nhưng đó là gate-work cho một child ĐÃ hợp pháp, không phải
bằng chứng mở frontier.

## 4. QUYẾT ĐỊNH

**`PARK_DTP_NO_NEW_FRONTIER`** — không đăng ký DTP-CX-BTCUSDT-C1; không có
ứng viên nào trên bề mặt BTC hiện được cấp quyền khác ≥2/3 trục theo anti-
variant law với PIT + cost authority. Trục "sub-daily aggTrades chưa test"
của V16 là trục DỮ LIỆU, không phải cơ chế: mọi skeleton gọi tên được trên đó
đã chết đo (absorption cả hai chiều, run persistence daily, momentum mọi
cadence). Pair-swap và corpus giáo dục thêm bị loại đúng luật owner.

### Điều kiện mở lại (concrete, đúng luật reopen từng bề mặt)

- **RC-1 — information layer mới có bằng chứng:** một nguồn PIT mới có
  authority xuất hiện (liquidation tape thật / L2 đa-năm / options history có
  depth / cross-venue flows qua data-authority cycle riêng + license gate) ⇒
  child BTC mở với mechanism ĐƯỢC GỌI TÊN trên layer đó (chuỗi GO riêng).
- **RC-2 — owner plan gọi tên mechanism:** một plan của owner nêu mechanism
  cụ thể kèm phân tích F-0 trên giấy chống lại toàn bộ dead-set (tiền lệ
  reopening law BTC-BEAR / BTC-H4-CONTINUATION) — gánh nặng chứng minh thuộc
  đề xuất; A1/skeptic chỉ thẩm.
- **RC-3 — FX reopener R1/R2/R3 có bytes:** track DTP-FX (AUDUSD-C1) là bề
  mặt hợp pháp kế tiếp của chương trình — ưu tiên cao hơn BTC vì mở ô không
  gian thật (cost all-in đo được / nguồn độc lập / financing band).
- **RC-4 — close sớm cấp chương trình:** nếu owner không mở RC nào,
  `NO_CANDIDATE` cấp chương trình (đã tìm trong không gian được cấp quyền:
  1 pair-child đo trọn death ledger + BTC review này) là close hợp lệ theo
  master §9 — không bắt buộc chạy từng pair còn lại để chứng minh điều đã đo.

**KHÔNG phải điều kiện mở lại** (luật owner 2026-09-27): thêm corpus giáo
dục; đổi pair; phá tường Reddit/TradingView.

## 5. Tuyên bố phạm vi

- Không đăng ký cycle mới, không GO nào được tiêu, không score/OOS/shadow/
  worker/lệnh. Review thuần đọc-hai (tài liệu + bằng chứng chết có sẵn),
  outcome-blind: không số liệu PnL nào của DTP tồn tại để xem.
