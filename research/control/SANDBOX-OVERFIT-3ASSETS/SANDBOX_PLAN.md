# SANDBOX-OVERFIT-3ASSETS — plan stub (KHÔNG đăng ký registry)

**Cycle id:** SANDBOX-OVERFIT-3ASSETS
**Loại:** SANDBOX / EXPLORATORY — theo chỉ đạo trực tiếp của owner ngày
2026-09-19 ("lập cycle không liên quan luật lệ, overfit cũng được, muốn
kiểm tra một số thứ").

## Phạm vi what-is / what-is-not

| Có | Không có |
|---|---|
| Tìm strategy overfit tối đa lợi nhuận in-sample, từng mã | Không fold discipline, không DSR/PBO, không trial accounting |
| 3 tài sản: BTCUSDT-PERP, ETHUSDT-PERP, SOLUSDT-PERP (15m, ~2 năm) | Không S1, không GO phrase, không scored cells |
| Chi phí xấp xỉ: taker fee + slippage + funding drag | Không mô hình thanh khoản/l Liquidation khi L>1 |
| OOS diagnostic 20% cuối (chỉ chẩn đoán, KHÔNG dùng để chọn) | Không dùng kết quả này làm evidence cho cycle nào |

## Ràng buộc cứng vẫn giữ (kể cả khi "bỏ luật")

- KHÔNG đụng `plans/CYCLE_REGISTRY.json`, ledgers, hay lane của
  STOCKS-SEARCH-V1 / PROSPECTIVE-SHADOW-V1.
- KHÔNG push / merge main / lịch sử git. Toàn bộ file sandbox để ngoài
  commit hoặc commit sau theo yêu cầu riêng của owner.
- Job nhẹ (vài phút CPU), không chiếm heavy lock (đã kiểm tra
  `locks inspect` → FREE_PROVEN trước khi chạy).

## Dữ liệu

Nguồn: Binance fapi public klines `15m`, window ~2 năm (2024-09 → hiện tại),
cache parquet tại `data/`. Lý do không dùng catalog nội bộ: schema
nautilus nhị phân + BTC chỉ phủ 1 năm.

## Họ strategy + grid (chọn theo net total return IS, cho phép overfit)

1. SMA crossover (fast×slow, mode long/both)
2. Donchian breakout (entry×exit lookback)
3. RSI mean reversion (period×threshold, hold-until)
4. Time-series momentum (lookback)
5. Bollinger mean reversion (period×k, hold-until)
6. Đòn bẩy L ∈ {1,2,3} nhân exposure (không mô hình liquidation — báo cáo maxDD để nhìn cái giá)

Chốt output: `out/results.csv` (toàn bộ config), top-10/bảng/tài sản +
top-1 equity SVG trong `SANDBOX_OVERFIT_REPORT.md`.

## Phase 2 — FAMILY OVERFIT (2026-09-20, chỉ đạo owner)

Yêu cầu: từ **corpus family đã research của workspace**, chọn 1 family cho
mỗi lớp tài sản rồi overfit tối đa lợi nhuận:

| Lớp | Family (nguồn) | Grid |
|---|---|---|
| crypto | H-VOLCOMP-BRKOUT-v1 (`strategy_vol_compression_breakout.py`) | 800/46.656 config lấy mẫu seed=42 |
| stocks | EVENT-UNWIND (PLAN_stocks_search_v1.md family #1, NG6 anchor) | 900 config × 36 mã Yahoo EOD 15y |
| forex | SWING-EXTREME ABSORPTION / DIVERGENT CLV (PLAN_forex_ng7.md anchor FNG7-A2-P1) | 72 config × 7 cặp major |

Engine + runner: `families_lib.py`, `run_families.py` (`--only=...`).
Output: `out/family_results_{CRYPTO,STOCKS,FOREX}.csv` +
`FAMILY_OVERFIT_REPORT.md`. Chi phí xấp xỉ theo lớp; OOS 20% cuối chỉ
chẩn đoán; vẫn KHÔNG đăng ký registry, KHÔNG đụng cycle sống.
