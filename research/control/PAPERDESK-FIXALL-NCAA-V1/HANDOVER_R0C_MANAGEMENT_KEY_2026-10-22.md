# HANDOVER R0c — Khóa quản trị OpenRouter cho đồng hồ số dư
(PAPERDESK-FIXALL-NCAA-V1 / FREE-RESEARCH; lệnh owner 2026-10-22)

## Thông tin khóa (theo luật: không bao giờ ghi giá trị)

- Vị trí: macOS Keychain, service `com.myquant.paperdesk`, account
  `openrouter-management-key` (đọc lại kiểm chứng khớp theo sha, giá trị
  không in).
- **Hạn dùng: VĨNH VIỄN (không có ngày hết hạn)** — không cần alarm hết
  hạn; chỉ luân chuyển khi owner ra lệnh hoặc nghi lộ.
- **Luật sử dụng: CHỈ phục vụ đồng hồ số dư** (`GET /credits`, suy
  `limit_remaining = total_credits − total_usage`). CẤM mọi thao tác
  quản trị khóa khác. Config chỉ giữ tham chiếu
  `ai_provider.balance_key_ref` — giá trị không bao giờ vào repo/log/
  config/handover.

## Gắn vào đồng hồ số dư

- `ai_producer._default_balance_transport`: khóa quản trị được `/key`
  trả **HTTP 200 với `limit_remaining: null`** (không phải 401 — bản
  fix thứ hai sau phát hiện sống); nhận diện `is_management_key` từ
  thân phản hồi → rơi xuống `/credits`. Khóa inference THƯỜNG với
  limit null giữ nguyên `None` trung thực (view `/credits` của nó là
  cấp khóa, dễ bịa số — battery cấm gọi `/credits` cho khóa thường).
- `produce_for_pending` đọc `balance_key_ref` cho ĐỒNG HỒ (chat vẫn
  dùng khóa inference); khóa quản trị biến mất → hạ cấp trung thực về
  khóa chat (balance None).

## Kiểm chứng sống (bắt buộc theo lệnh owner)

- **Đọc số dư: `total_credits = 10`, `total_usage = 0` → số dư
  10.00 USD** — khớp 10 USD owner nạp trừ phần đã dùng (khoảng ~0.003
  USD dùng thử trước đó chưa phản ánh vào endpoint này tại thời điểm
  đọc).
- Cascade thật hồi sinh ngay pass đầu sau restart:
  `deepseek/deepseek-v4.1-flash-1017` **UP**, `deepseek/deepseek-v4.1-flash`
  **UP** (cascade_state.json updated 2026-10-22T03:44:31Z).

## Hai lỗi đã sửa trên đường này (trung thực ghi lại)

1. Fallback đầu tiên (bắt 401/403) không bao giờ chạy vì /key trả 200 —
   đã sửa theo thân phản hồi thật.
2. Một bản fallback tạm trước đó suy ra **số dư âm** từ view cấp khóa
   và sẽ GIỮ mọi nấc trả phí vô thời hạn — đã thu hồi; luật cuối: đọc
   không được thì trả None, tuyệt đối không bịa số.

## Battery

`test_balance_clock_management_key_credits_fallback` (kịch bản 200-null
+ cấm /credits cho khóa thường) + `test_config_carries_balance_key_ref`.
Toàn suite `tests/papertrade_exec/` **315/315 xanh 2 lần liên tiếp** tại
HEAD cuối (chạy lại từ chính checkout production).
