# HANDOVER R2 — Vòng nghiên cứu tool-calling trong producer
(PAPERDESK-FIXALL-NCAA-V1 / FREE-RESEARCH; 2026-10-22)

## Kiến trúc

`ai_producer.py` thêm `run_research_loop(...)` — sau khi gói nền
(`ai_research.collect_evidence` — KHÔNG đổi) được lắp, lượt chấm chạy
dạng hội thoại OpenRouter tool-calling:

- Model được khai báo đúng 2 công cụ (`FR.TOOL_SCHEMAS`): `tim_web`,
  `mo_trang`. Model CHỈ RA LỆNH; code bàn thực thi
  (`FR.execute_tool`); kết quả append vào hội thoại (role=tool) VÀ ghi
  nhật ký nguyên văn TRƯỚC khi model thấy.
- Model trả lời ngay 0 vòng công cụ = HỢP LỆ (gói nền đã đủ với nó) —
  battery ca (e).
- Trần cứng mỗi lượt chấm (config `ai_free_research`, dội vào spec
  workstream): `max_tool_rounds=6`, `max_page_fetches=10`,
  `max_tokens_per_round=8000`, và đồng hồ ngân sách DÙNG CHUNG U3
  `ai_provider.max_budget_seconds=600`. Hết trần chưa phán → LUẬT IM
  LẶNG (ứng viên nằm chờ, không ép phán) — battery ca (d).

## Cascade U3 giữ nguyên cho TỪNG lần gọi model trong vòng

- Mỗi lần gọi đi qua `_first_available` (mạnh nhất trước, skip slot đã
  rơi) + máy trạng thái nấc như hiện tại (UP/COOLDOWN/HALF_OPEN,
  trigger 429/402/5xx/401/403 như cũ).
- **Lời gọi công cụ rác** (tên công cụ lạ / arguments không parse được)
  = HỎNG MỂM theo luật U3: retry CÙNG model ĐÚNG 1 lần kèm
  `TOOL_GARBAGE_SUFFIX`, vẫn rác → lùi nấc + tính soft-fail (3 lần/1h →
  COOLDOWN 30 phút). Battery `test_malformed_tool_call_is_soft_fail_
  never_config_broken`.
- **Model không hỗ trợ tool-calling**: HTTP 400/404 trong vòng nghiên
  cứu = HỎNG MỂM (lùi nấc cho lượt đó) — KHÔNG đánh CONFIG_BROKEN
  (khác với đường nền), đúng lệnh owner "coi như hỏng mềm, lùi nấc".
  Battery `test_tool_incapped_400_is_soft_fail_keeps_slot`.
- Lưu ý trung thực: 402 trong vòng giữ nấc trả phí mà KHÔNG gọi balance
  check nội vòng (`check_balance_on_402=False`) — đồng hồ số dư chạy ở
  đầu pass producer như cũ và sẽ hồi sinh nấc ở pass kế tiếp.

## Tái dùng nhật ký theo candidate_hash

- Journal theo `<candidate_hash>`; lượt chấm lại cùng hash trong cửa
  sổ chờ: journal tươi (< `journal_freshness_hours`=4h) → TÁI DÙNG —
  nguồn công cụ cũ đi thẳng vào payload như nguồn bắt được, model vẫn
  có thể gọi thêm công cụ; KHÔNG gọi lại Tavily cho những gì đã có.
  Battery `test_journal_reused_on_rescore_no_refetch` (lượt 1 im lặng
  → lượt 2 tái dùng, 0 lần gọi Tavily mới).

## Ý kiến cuối + luật trích dẫn H1/U0 nguyên vẹn trên tập hợp mới

- Schema ALLOW|VETO như cũ (`parse_v2` không đổi).
- Bộ lọc trích dẫn chạy trên **tập hợp nhất** (gói nền + journal):
  URL ngoài nhật ký bị loại hoàn toàn; ALLOW bị lọc rỗng → `.invalid/`
  (battery ca c).
- Opinion ghi `model_id` + `reasoning_effort` + `prompt_version/_sha256`
  của phiên bản prompt đã sản xuất nó.

## Tác động danh nghĩa

`ai_producer.py`, `ai_gate_v2.py` (so dấu prompt theo phiên bản của
opinion), `ops_service.py` (1 dòng truyền telemetry cho scorecard),
`config.json`, `ai_scorecard.py`, `apps/paperdesk/renderer/app.js`
(khối dashboard R4), battery mới + 1 dòng `fr_over` trong helper U3.
Battery: 313/313 × 2 lần liên tiếp.
