# HƯỚNG DẪN CHẠY (owner) — MT5 cost collector, chỉ 5 bước

> Bộ thu dữ liệu **CHỈ ĐỌC**: không đặt/sửa/đóng lệnh, không có bất kỳ hàm lệnh nào.
> Nút **Algo Trading giữ tắt** như cũ — collector không cần nó.

## Bước 0 — Đăng nhập đúng tài khoản OANDA (làm 1 lần)
- Hiện terminal đang đăng nhập **MetaQuotes-Demo** (đọc từ log terminal).
- MT5 → **File → Login to Trade Account** → chọn tài khoản **OANDA_Global-Demo-1**
  (bạn tự nhập mật khẩu — Lead/collector **không bao giờ** đụng mật khẩu).

## Bước 1 — Vào thư mục Experts
1. MT5 → **File → Open Data Folder**.
2. Vào `MQL5\Experts\` — file `mt5_cost_collector.mq5` đã được Lead copy sẵn
   (bản đã sửa theo audit; nếu không thấy, copy từ
   `my-quantitative/research/control/forex_mt5_cost_probe_2026-09/`).

## Bước 2 — Biên dịch (30 giây)
1. Nhấn **F4** (mở MetaEditor) → mở `mt5_cost_collector.mq5` → nhấn **F7** (Compile).
2. Phải thấy **`0 errors, 0 warnings`** — LUÔN biên dịch lại, đừng dùng file .ex5 cũ.

## Bước 3 — Gắn vào biểu đồ (một biểu đồ là đủ)
1. Quay lại MT5, mở biểu đồ **EURUSD** (M1 hay khung nào cũng được).
2. Kéo `mt5_cost_collector` từ Navigator thả vào biểu đồ.
3. Tab **Common** không cần tích gì; **Inputs** để nguyên (5s/60s).
4. **Quan trọng:** nút **Algo Trading** phải ở trạng thái **TẮT (Off)**.
5. Tab **Experts** (dưới cùng) phải thấy: `cost-collector: started READ-ONLY...`

## Bước 4 — Smoke test 30 phút, rồi tuần thu 7 ngày
- **Smoke:** để chạy **30 phút** rồi báo Lead.
- **Tuần chính thức (7 ngày):** chỉ cần **giữ MT5 mở** (mất mạng tự được ghi nhận
  là gap — missing = missing). Cuối tuần:
1. MT5 → **File → Open Shared Folder** → thư mục `forex_mt5_cost_probe`
   (4 file: `tick_samples.csv`, `spec_snapshot.csv`, `heartbeat.csv`, `events.csv`).
2. Copy cả thư mục ra **ngoài repo**: `/Users/hoangminhlong/.my-quantitative-data/forex_mt5_cost_probe_2026-09/raw/`
   rồi báo Lead (dữ liệu thô KHÔNG bao giờ vào git).
3. Lead chạy verifier + giao toàn bộ artifact cho **A7 audit**. Chỉ A7 kết luận.

## An toàn
- Collector **không đọc mật khẩu/login** (trường login cố tình ghi `REDACTED_LOGIN_BY_CONTRACT`).
- Mỗi dòng dữ liệu ghi kèm cờ AutoTrading bật/tắt — nếu ai đó bật nhầm, dữ liệu tự vạch ra.
- Muốn dừng: chuột phải biểu đồ → Expert List → Remove (EA tự ghi shutdown + snapshot cuối).
