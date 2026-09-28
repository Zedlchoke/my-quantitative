# DAYTRADER-100-V1 — OWNER FRONTIER STATUS NOTE (2026-09-28, in-flight)

Owner-supplied measured status table, recorded verbatim as cycle evidence. Source:
owner message this session (companion data-lane measurements, 2026-09-28).

| Nguồn | Đã có gì | Còn thiếu |
|---|---|---|
| Orderbook/L2 crypto | 10 phút dữ liệu Binance spot BTCUSDT và ETHUSDT, ~11.981 cập nhật, không đứt chuỗi | Chưa có L2 lịch sử nhiều năm; dữ liệu chỉ bắt đầu từ 28/9 |
| On-chain | Ethereum RPC head + finalized block; finality lag đo 65 block | Chưa có dataset lịch sử as-of-time hoặc cross-provider |
| Options | Deribit BTC: 988 hợp đồng trong chain; 10/10 ticker có bid/ask, IV, Greeks | Chưa có lịch sử options hoặc dải phí/khả năng khớp lệnh |
| Rates intraday | CHƯA CÓ quote/tick intraday (SOFR/EFFR daily không thay thế) | Nguồn rates futures có license + đường truyền |
| CME | Xác nhận lại SNI-block; 0 byte dữ liệu thị trường | Nhà mạng/IT mở đường hoặc nguồn broker-grade |
| FX cost-band | IBKR paper Read-Only trả bid/ask live 5 cặp; ~5 phút, 8.484 quan sát hợp lệ | Giờ giao dịch khác, commission, swap/rollover, slippage; statement IBKR có sẵn giúp đo — KHÔNG cần tạo lệnh |

## Phân tích tích hợp (Lead, 2026-09-28)

1. **Không thay đổi tập runnable của G3 freeze.** Mọi nguồn mới đều prospective-only
   từ 2026-09-28 → 28 family `NOT_RUN_DATA_BLOCKED_UNDER_OWNER_ORDER` giữ nguyên cho
   backtest lịch sử. Bảng này TƯƠNG THÍCH và củng cố census (CME 0 bytes đo lại;
   rates intraday 0 bytes đo lại).
2. **Mở cửa tiến-lớp:** L2 spot + on-chain RPC + Deribit chain là ba collector-candidate
   cho forward collection (gia hạn DATA-EDGE-UNLOCK-V1 pattern: collector chạy theo
   contract đóng băng rồi dừng sạch). Bất kỳ cycle lịch sử nào dùng chúng cần tối thiểu
   vài năm thu thập — quyết định mở collector là owner-only (compute/network dài hạn).
3. **FX cost-band:** mẫu IBKR 5 cặp/8.484 obs (lane bạn) + mẫu DT100 3 cặp/500 quotes
   (`TWS_SPREAD_PROBE_20260928T015508Z.json`) cùng khẳng định realizability ở mức
   sub-pip median. Việc cần cho một FX cycle tương lai không phải thêm mẫu live mà là
   (a) phân bố theo giờ/phiên, (b) commission schedule, (c) swap/rollover — đúng như
   cột "còn thiếu" của owner. Statement giao dịch có sẵn (không cần tạo lệnh) là nguồn
   đo slippage thật tốt nhất.
4. **Không hành động nào trong bảng này bị từ chối:** toàn bộ là đo-lường read-only,
   đúng luật. Ghi nhận là evidence, không mở scope mới trong phiên này.
