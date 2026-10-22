# HANDOVER R0 — Cấp khóa Tavily (PAPERDESK-FIXALL-NCAA-V1 / FREE-RESEARCH workstream)

- Ngày: 2026-10-22. Worktree:
  `.worktrees/paperdesk-fixall-ncaa-v1/integration`, branch
  `orca/paperdesk-fixall-ncaa-v1-integration`, HEAD tại thời điểm làm:
  `9f7b8011657ca08e200942ab5d82acda8f52568e` (không commit nào của workstream
  này trong mục R0 — R0 thuần ops, không đổi code).
- Lệnh owner: 2026-10-22 (tin nhắn cấp khóa trong chu trình).

## Đã làm

1. **Lưu khóa vào Keychain** — đúng khuôn khóa OpenRouter hiện tại:
   - service `com.myquant.paperdesk`, account `tavily-api-key`
     (`security add-generic-password -U`), cập nhật nếu đã tồn tại.
   - Giá trị khóa đi qua biến môi trường của shell tại thời điểm tạo;
     KHÔNG ghi vào repo, log, config, handover hay bất kỳ file nào.
     Config production chỉ được phép mang `key_ref` (service/account).
2. **Đọc lại kiểm chứng**: `security find-generic-password -s
   com.myquant.paperdesk -a tavily-api-key -w` → so sha256 với giá trị
   owner cung cấp → **READBACK_MATCH**. Giá trị không bao giờ được in.
3. **Smoke test Tavily thật** (R0/R1 dùng chung): 1 lần
   `POST https://api.tavily.com/search` (Bearer, `search_depth=basic`,
   `max_results=5`, query "Duke basketball injury report today"):
   - Lần 1 + 2: lỗi phi HTTP do **python framework 3.13 của máy thiếu CA
     bundle** (`SSL: CERTIFICATE_VERIFY_FAILED`) và một lần **khóa rỗng do
     thiếu `export` biến môi trường** (lỗi của bàn thực thi, đã sửa; 401 trả
     về là của lệnh gọi KHÔNG có khóa — không phải khóa bị từ chối).
   - Lần 3 (venv gốc `/Users/hoangminhlong/my-quantitative/.venv/bin/python`,
     đúng interpreter production `apps/paperdesk/main/runner.js:13`):
     **HTTP 200, 5 kết quả, latency 2.44 s** — khóa SỐNG.
   - Nhật ký nguyên văn (cả 3 lần, gồm cả lỗi):
     `evidence/ai_free_research/r0_tavily_smoke_20261022T012646Z.json` và
     `r0_tavily_smoke_20261022T012958Z.json` (lần 200).
4. **Hạn mức gói dev tại thời điểm xây** (tài liệu Tavily,
   docs.tavily.com/documentation/api-credits, đọc 2026-10-22):
   - Khuôn khóa `tvly-dev-` = gói dev; tài liệu gọi bậc miễn phí là
     **Researcher: 1.000 credits/tháng** (tìm kiếm basic = 1 credit;
     advanced = 2). Đây là **trần cho khớp** khi đặt budget Tavily.
   - Phản hồi Search API KHÔNG mang header hạn mức (đã ghi nguyên văn
     `quota_headers: {}` trong bằng chứng) — không đọc được số dư còn lại
     từ header; bảng điều khiển Tavily cần đăng nhập web (ngoài khả năng
     của bàn). Ghi nhận trung thực: **giám sát hạn mức phải dựa vào việc
     đếm lượt gọi của mình (telemetry R4) + bắt lỗi 432/429 từ API**.
   - Rate limit (requests/phút): tài liệu trang credits không nêu con số.

## Trạng thái & ranh giới

- Khóa đã cấp và kiểm chứng. Chưa có code nào tiêu thụ nó (R1 sẽ thêm
  `key_ref` thứ hai: `com.myquant.paperdesk / tavily-api-key`).
- KHÔNG đụng: seal, ledger, quyết định production, cascade sống, CLV plane,
  kỷ nguyên U7. KHÔNG push/merge. Không câu GO nào trong tài liệu này.
- Việc owner còn lại (nhắc lại trong báo cáo cuối): **tạo lại khóa Tavily
  sau khi cài đặt chạy ổn** (vì khóa đã đi qua kênh chat).

## Chuyển tiếp

- R1 lấy khuôn keychain `keychain_key(key_ref)` của `ai_producer.py`
  (`<service> / <account>`) cho khóa Tavily; transport dùng
  `urllib` như `ai_research._get_json`, chạy dưới venv gốc.
