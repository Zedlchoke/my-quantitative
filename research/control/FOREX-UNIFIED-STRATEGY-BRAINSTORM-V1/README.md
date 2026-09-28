# FOREX-UNIFIED-STRATEGY-BRAINSTORM-V1

**Loại:** research brainstorm (knowledge-only) — owner-space, không phải cycle đã đăng ký.
**Ngày:** 2026-09-28. **Phương thức:** 14 research lane song song (12 symbol + 2 macro), facts thời điểm được verify qua web-search tháng 9/2026; mục không verify được đánh dấu "(cần kiểm chứng)" ngay trong file.

## Trạng thái evidence — ĐỌC TRƯỚC KHI DÙNG

Toàn bộ 1.200 strategy ideas trong chương trình này là **HYPOTHESIS / NOT_RUN** theo mission invariant của workspace: chưa có ý tưởng nào được backtest, đo lường hay reproduce. Correlation maps trong các file symbol là **prior kiến thức**, không phải số đo trên data repo — mọi con số cần re-measure trước khi dùng làm gate chính thức. Không cell budget nào bị tiêu hao; không cycle registry nào bị ghi.

## Mục đích

Trả lời yêu cầu owner 2026-09-28: nghiên cứu sâu từng symbol (bản chất, điểm đặc biệt, tin tức/thông số ảnh hưởng), brainstorm 100 strategy ideas/symbol trên 12 symbol, kết hợp yếu tố quốc gia/đồng tiền bên ngoài, rồi tổng hợp thành **một chiến lược thống nhất** để trade toàn thị trường forex — xem `UNIFIED_STRATEGY.md`.

## Phạm vi (12 symbol + macro)

| Cụm | Symbols |
|---|---|
| FX majors (USD-bloc) | EURUSD, GBPUSD, USDJPY, USDCHF |
| Commodity-FX | USDCAD, AUDUSD, NZDUSD |
| Precious metals | XAUUSD, XAGUSD |
| Energy | BRENT (US Brent Oil), WTI, NATGAS (Henry Hub) |

## Index

### symbols/ — deep-dive + 100 ideas mỗi symbol (mỗi file: Phần 1 bản chất · Phần 2 S1–S100 theo 10 family · Phần 3 top-10 + bẫy overfit + weekly checklist)

- [EURUSD.md](symbols/EURUSD.md) — 702 dòng
- [GBPUSD.md](symbols/GBPUSD.md) — 717 dòng
- [USDCAD.md](symbols/USDCAD.md) — 700 dòng
- [USDJPY.md](symbols/USDJPY.md) — 368 dòng
- [AUDUSD.md](symbols/AUDUSD.md) — 705 dòng
- [NZDUSD.md](symbols/NZDUSD.md) — 701 dòng
- [USDCHF.md](symbols/USDCHF.md) — 485 dòng
- [XAUUSD.md](symbols/XAUUSD.md) — 703 dòng
- [XAGUSD.md](symbols/XAGUSD.md) — 1.009 dòng
- [BRENT.md](symbols/BRENT.md) — 595 dòng
- [WTI.md](symbols/WTI.md) — 878 dòng
- [NATGAS.md](symbols/NATGAS.md) — 710 dòng

### macro/ — bản đồ yếu tố quốc gia/đồng tiền

- [CURRENCIES_CORE.md](macro/CURRENCIES_CORE.md) — USD, EUR, GBP, JPY + cross-cutting + coupling rules + lịch tuần
- [CURRENCIES_BLOC.md](macro/CURRENCIES_BLOC.md) — CAD, AUD, NZD, CHF + commodity-FX cross-cutting + coupling rules + lịch tuần

### Tổng hợp

- [UNIFIED_STRATEGY.md](UNIFIED_STRATEGY.md) — chiến lược thống nhất 6 lớp (market-state engine → regime router → macro gates → risk budget → execution → monitoring)

### handoffs/

14 file JSON `zcode_orch_v3_handoff@1` (một lane một file, status DONE) — bằng dấu vết hoàn thành của từng lane.

## 10 family strategy dùng thống nhất across symbols

Trend/Momentum · Mean-reversion · Breakout/Vol-expansion · Carry/Rate-differential (với commodity là Term-structure/Seasonal) · Session/Time-of-day/Seasonality · Event/Data-driven · Cross-asset/Correlation · Positioning/Flows · Pattern/Pairs/Stat-arb · Regime-conditioned/Options-flavored.

Quy tắc chất lượng đã áp: 100 ý/symbol thật sự khác nhau (đổi threshold không tính là ý mới); mỗi ý có hypothesis kinh tế, không chỉ mô tả pattern suông.

## Bối cảnh thị trường verify được của tháng 9/2026 (xương sống chung của cả chương trình)

- Fed hike 16/09 → 3.75–4.00% (12–0); ECB hike 10/09 → depo 2.50%; BoE hold 3.75% giữa gilt-stress (10Y ~5.38%, đỉnh 19 năm); BoJ ~1.00% sau can thiệp phối hợp Nhật–Mỹ Jul–Aug ở vùng 160–164 (USDJPY hiện ~152.9–154.5).
- War Mỹ–Iran/Hormuz: Brent đỉnh ~$108, WTI >$100, whipsaw $90→108→90→104; Brent–WTI spread $11–14 (bình thường $3–6).
- **Nghịch lý định giá quan trọng nhất:** gold $4,144 (−26% từ ATH $5,589 ngày 28/01/2026) — oil shock đẩy CPI → kỳ vọng hike → real yields (TIPS 2.85%, +23bp/tuần) → gold TỤT; kênh safe-haven bị kênh lãi suất đè. Kênh truyền dẫn đảo chiều theo regime là lý do tồn tại của UNIFIED_STRATEGY.
- CAD yếu dù oil >$100 (differential −150/−175bp + Section 338 trade war) — rate regime lấn át terms-of-trade.
- NATGAS (HH ~$2.5–3.35) decoupled hoàn toàn khỏi TTF (~€60/MWh) —(symbol có |ρ| thấp nhất universe).

Chi tiết + nguồn trong từng file; các mục chưa khẳng định được liệt kê "(cần kiểm chứng)" cuối mỗi file.

## Bước tiếp theo (chờ owner quyết, không tự thực hiện)

1. Re-measure correlation maps & thresholds trên data thật của repo (DATA-FOUNDATION-SIXSOURCE-V1) trước khi chọn ý tưởng đưa vào test.
2. Nếu muốn test: soạn DRAFT plan đăng ký cycle mới theo đúng quy trình (preregistered matrix, warmup, baselines, budget cells, gates + GO của owner) — precedent REGIME-GATED-COMBO-V1 cho dạng conditional-allocation.
