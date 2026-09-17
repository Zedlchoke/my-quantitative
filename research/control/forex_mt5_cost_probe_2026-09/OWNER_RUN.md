# HƯỚNG DẪN CHẠY (owner) — MT5 cost collector, chỉ 4 bước

> Bộ thu dữ liệu **CHỈ ĐỌC**: không đặt/sửa/đóng lệnh, không có bất kỳ hàm lệnh nào.
> Nút **Algo Trading giữ tắt** như cũ — collector không cần nó.

## Bước 1 — Mở MT5 và vào thư mục Experts
1. Mở **MetaTrader 5** (đã cài sẵn trên máy).
2. Menu **File → Open Data Folder** (Mở thư mục dữ liệu).
3. Vào con đường `MQL5\Experts\`.
   - *File `mt5_cost_collector.mq5` đã được Lead copy sẵn vào đây; nếu chưa thấy, copy từ
     `my-quantitative/research/control/forex_mt5_cost_probe_2026-09/mt5_cost_collector.mq5` vào.*

## Bước 2 — Biên dịch (30 giây)
1. Trong MT5 nhấn **F4** (mở MetaEditor).
2. Trong MetaEditor mở file `mt5_cost_collector.mq5` (panel Navigator → Experts), nhấn **F7** (Compile).
3. Phải thấy `0 errors, 0 warnings`.
   - *(Nếu Lead đã compile sẵn có file `mt5_cost_collector.ex5` thì bỏ qua bước này.)*

## Bước 3 — Gắn vào biểu đồ (một biểu đồ là đủ)
1. Quay lại MT5, mở biểu đồ **EURUSD** (khung thời gian nào cũng được, ví dụ M1).
2. Trong Navigator kéo `mt5_cost_collector` thả vào biểu đồ EURUSD.
3. Cửa sổ hiện ra: tab **Common** KHÔNG cần tích gì; tab **Inputs** để nguyên (5s/60s).
4. **Quan trọng:** đảm bảo nút **Algo Trading** trên thanh công cụ ở trạng thái **TẮT (Off)**.
   Collector không cần nó.
5. Tab **Experts** (dưới cùng) phải thấy dòng: `cost-collector: started READ-ONLY...`

## Bước 4 — Để chạy & gửi dữ liệu
- **Smoke test:** để chạy **30 phút** rồi báo Lead (không cần làm gì thêm trong lúc chạy).
- **Tuần thu chính thức (7 ngày):** chỉ cần **giữ MT5 mở** (máy có thể làm việc khác; MT5 tự
  ghi và tự ghi nhận gap nếu mất mạng — missing = missing). Cuối tuần:
1. MT5 → **File → Open Shared Folder** → thư mục `forex_mt5_cost_probe`
   (có 4 file: `tick_samples.csv`, `spec_snapshot.csv`, `heartbeat.csv`, `events.csv`).
2. Copy cả thư mục đó vào `my-quantitative/.my-quantitative-data` hoặc gửi trực tiếp cho Lead.
3. Lead chạy verifier + giao toàn bộ cho **A7 audit**. Chỉ A7 kết luận.

## An toàn
- Collector **không đọc mật khẩu/login** (cố tình REDACT trong cả dữ liệu ghi ra).
- Mọi dòng dữ liệu đều ghi kèm cờ "AutoTrading đang bật hay tắt" → nếu ai đó bật nhầm,
  dữ liệu tự vạch ra, không im lặng.
- Muốn dừng: gỡ EA khỏi biểu đồ (chuột phải biểu đồ → Expert List → Remove). Nó tự ghi
  dòng shutdown + snapshot cuối.
