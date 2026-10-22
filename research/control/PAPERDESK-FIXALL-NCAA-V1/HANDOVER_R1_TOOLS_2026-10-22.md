# HANDOVER R1 — Hai công cụ nghiên cứu tim_web / mo_trang
(PAPERDESK-FIXALL-NCAA-V1 / FREE-RESEARCH; 2026-10-22)

## Module mới

`research/papertrade_exec/ai_free_research.py` — module anh em của
`ai_research.py`, KHÔNG đụng đường ESPN hiện sống.

## tim_web(query, max_results=5)

- Gọi `POST https://api.tavily.com/search` (Bearer); khóa đọc từ
  Keychain TẠI THỜI ĐIỂM GỌI theo `key_ref`
  `com.myquant.paperdesk / tavily-api-key` (cùng khuôn khóa OpenRouter;
  bản sao cục bộ của `keychain_key` để tránh vòng import).
- Chuẩn hóa kết quả: `{url, title, excerpt, published_utc}` (url 400
  ký tự, excerpt 280).
- Lỗi trung thực: `ToolError` có `.kind` — `quota` (HTTP 429/432: hết
  hạn mức gói dev), `http`, `network`, `bad_input`. KHÔNG bao giờ bịa
  kết quả; vòng nghiên cứu suy biến về gói nền.

## mo_trang(url)

- Chỉ http/https công khai: chặn scheme lạ, URL có credential, port
  khác 80/443, host `localhost` / `*.local` / `*.internal`, và **mọi IP
  sau phân giải DNS** không phải global (loopback/private/link-local/
  reserved/multicast/unspecified đều chặn — `ipaddress.is_global` cộng
  rào kép). `file://`, `ftp://` bị chặn.
- Timeout 20s; trần 3.000.000 byte transport; trần chữ đã làm sạch
  400.000 ký tự (`max_page_chars` cấu hình được).
- Làm sạch bằng `html.parser` (bỏ script/style/noscript/template/svg/
  head, gộp whitespace); lỗi parser rơi về regex-strip — không bao giờ
  crash vòng nghiên cứu.
- Nhận diện charset từ Content-Type; từ chối content-type không phải
  text/json/xml (honest error).

## Nhật ký nguyên văn (luật xương sống)

`ResearchJournal` — một file JSON cho MỘT `candidate_hash`, tại
`<plane>/research_journal/research_journal_<hash>.json` (máy bay thật)
hoặc `<plane>/shadow/research_journal/` (bóng ma):
- mỗi lệnh gọi công cụ (kể cả LỖI) = 1 entry `verbatim`: câu hỏi/thời
  điểm/kết quả nguyên văn (tim_web) hoặc url + fetched_at + sha256 nội
  dung + đoạn trích đưa cho model (mo_trang, 3.000 ký tự đầu);
- `journal.sources` = bộ nguồn hợp lệ (union set với gói nền) — chỉ lớn
  lên bằng URL THỰC SỰ trả về từ công cụ, không bao giờ từ model;
- tái dùng: `ResearchJournal.load(freshness_hours)` — file tươi (< 4h
  mặc định) → reused=True (không tìm lại từ đầu); stale → tạo mới,
  file cũ không được trộn lặng lẽ.

## Hạn mức gói dev (R0 yêu cầu ghi con số)

- Tài liệu Tavily (docs.tavily.com/documentation/api-credits, đọc
  2026-10-22): gói dev/Researcher = **1.000 credits/tháng** (basic
  search = 1 credit). Phản hồi Search KHÔNG có header hạn mức — giám
  sát bằng đếm lượt (telemetry R4) + bắt 429/432. Ghi trong config
  `ai_free_research.dev_plan_quota_note`.

## Smoke test thật trên máy Mac

- 1 tìm kiếm + đọc trang thật: `evidence/ai_free_research/` — file
  `r0_tavily_smoke_*.json` (HTTP 200, 5 kết quả, 2.44s) và nhật ký
  lượt chấm sống sandbox (R2). Khóa không bao giờ vào bất kỳ file nào.

## Battery (giả lập, không đụng mạng)

`tests/papertrade_exec/test_free_research.py` — 12 test R1/R0b: SSRF
guard 11 ca chặn (numeric IP loopback/link-local/private/IPv6, scheme,
credential, port, host nội bộ), clean_html, tim_web chuẩn hóa + journal
verbatim + lỗi quota typed, mo_trang hash + excerpt, journal freshness.
Toàn suite `tests/papertrade_exec/` xanh 313/313 hai lần liên tiếp.

## Ranh giới

Model KHÔNG TỰ cầm trình duyệt — nó ra lệnh gọi, code bàn thực thi
(R2); mọi kết quả công cụ ghi nhật ký nguyên văn trước khi vào hội
thoại. KHÔNG push/merge, không câu GO.
