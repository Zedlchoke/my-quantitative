# HANDOVER R0b — Đổi nấc chủ cascade + mức suy luận theo nấc
(PAPERDESK-FIXALL-NCAA-V1 / FREE-RESEARCH workstream; 2026-10-22)

## Hai lệnh owner đã coded (đúng thứ tự đến)

1. **Lệnh #1 (2026-10-22)**: trọng tài nấc 1 →
   `deepseek/deepseek-v4.1-flash-1017`, các nấc dưới giữ nguyên thứ tự;
   mức suy luận **max** cho nấc này; owner đã nạp 10 USD OpenRouter.
2. **Lệnh #2 (2026-10-22, tin nhắn sau)**: **chuỗi chỉ còn DeepSeek** —
   `model_id = deepseek/deepseek-v4.1-flash-1017`, **fallback DUY NHẤT
   `deepseek/deepseek-v4.1-flash`**; toàn bộ chuỗi đa hãng cũ
   (claude-opus-5.5 → gpt-5.6-sol → claude-sonnet-5.5 → gemini-3.1-pro →
   deepseek-v4-pro → grok-4.7 → hàng free → openrouter/free) bị BỎ khỏi
   chuỗi theo lệnh này.

## Kiểm chứng slug (tự kiểm lại như luật, trước khi ghi config)

- Lần kiểm 1 (lệnh #1): `/api/v1/models` sống trả 468 model;
  `deepseek/deepseek-v4.1-flash-1017` tồn tại — canonical
  `DeepSeek V4.1 Flash 1017`, ctx 1.048.576, `supported_parameters` gồm
  `tools`, `tool_choice`, `reasoning`, `reasoning_effort`,
  `structured_outputs`; giá 0.3 / 1.2 USD per M token in/out.
- Lần kiểm 2 (lệnh #2): KHÔNG tồn tại slug `deepseek/deepseek-v4.1`
  thuần. Các biến thể sống: `deepseek/deepseek-v4.1-flash-1017`,
  `deepseek/deepseek-v4.1-flash`, `deepseek/deepseek-v4.1-flash:batch`.
  Bàn pin **`deepseek/deepseek-v4.1-flash`** (bản flash thường, tools +
  reasoning, ctx 1M) làm fallback — khác biệt so với chữ "deepseek v4.1"
  được ghi minh bạch ở đây: nếu owner muốn biến thể khác (vd batch),
  đổi một dòng config là đủ.

## Cơ chế mức suy luận theo nấc (R0b)

- Config mới `ai_provider.reasoning_effort_by_model`:
  `{"deepseek/deepseek-v4.1-flash-1017": "max"}` — chỉ nấc này max, nấc
  khác giữ mặc định provider (đúng lệnh #1; lệnh #2 không nói effort cho
  fallback → giữ mặc định).
- Producer `_post_chat_full` thêm `reasoning: {"effort": …}` vào thân
  request khi nấc cấu hình effort; `data_collection: "deny"` +
  `require_parameters: true` GIỮ NGUYÊN trên mọi request (U3.4);
  ONE-MODEL-PER-REQUEST giữ nguyên.
- Battery: `test_free_research.py::test_reasoning_effort_rides_the_body_
  of_its_stage_only` (body bắt được qua monkeypatch urllib) + 2 test
  config (test_free_research + test_upgrade_u3 — cả hai đã cập nhật kèm
  erratum ghi hai lệnh owner).
- Nhật ký ý kiến: opinion record thêm trường `reasoning_effort` (nấc
  thật đã dùng); scorecard U2 `per_model` giữ key model_id — effort
  nằm trong opinion + telemetry (đủ truy vết; key mở rộng thêm effort
  khi cần so sánh sẽ làm ở workstream sau nếu owner yêu cầu).

## Kiểm chứng sống (sandbox, máy bay M6 không đụng production)

- Lượt chấm thử sandbox với mạng + khóa thật tại data root production
  (`<data-root>/sandbox/ai_review`), trận NCAA thật Villanova–Notre Dame
  (ESPN id 401920982): kết quả ghi ở `evidence/ai_free_research/` —
  xem mục "Kiểm chứng sống" trong PAPERDESK_FREE_RESEARCH_FINAL.
- Đồng hồ số dư: `check_balance` chạy đầu mỗi pass producer như luật U3
  — nấc trả phí (giờ là cả hai nấc DeepSeek, không còn ':free') hồi sinh
  từ COOLDOWN 402 khi số dư ≥ low_balance_usd ($10). Máy bay THẬT đang
  giữ COOLDOWN 402 với chuỗi CŨ — lượt pass production kế tiếp (chạy
  từ worktree CŨ cho tới khi owner rebuild) sẽ hồi sinh chuỗi cũ; chuỗi
  DeepSeek mới có hiệu lực ở production sau khi owner merge + rebuild.

## Ranh giới

- KHÔNG đụng seal/ledger/quyết định thật; KHÔNG push/merge; không câu
  GO. Config là một file của worktree; A7 kiểm toán tại HEAD cuối.
