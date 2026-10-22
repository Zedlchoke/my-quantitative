# HANDOVER R4 — Đo lường "tự do đọc" có đáng không
(PAPERDESK-FIXALL-NCAA-V1 / FREE-RESEARCH; 2026-10-22)

## Telemetry mỗi lượt chấm

`<plane>/telemetry.jsonl` (thật) và `<plane>/shadow/telemetry.jsonl`
(bóng ma) — 1 dòng/1 lượt chấm:
`{plane, match_id, candidate_hash, research_depth: base_only|
researched, rounds, pages, tavily_calls, tool_errors, journal_reused,
models_used: [{model, effort, round}], elapsed_s, outcome,
prompt_version}`. Đường V2 nền cũng ghi dòng `base_only` → R4 có tử số
so sánh từ ngày đầu. Battery: `test_telemetry_and_research_split`.

## Bảng điểm tuần tách nhóm

`ai_scorecard.compute_research_split` (schema `ai_research_split@1`)
— đọc 2 telemetry, nối với opinion (đếm
`RUMOR_UNCORROBORATED` riêng) và ledger DECISION (`ai_gate`
hypothetical_* + results plane) để tính **PnL giả định của nhóm bị
chặn** theo luật chốt tài frozen cho từng nhóm `base_only` vs
`researched`: passes/verdicts/vetoes/veto_rate/rumor count/blocked
hypo-PnL/chi phí (tavily_calls, page_fetches, provider_seconds).
Gắn vào scorecard tuần như một khối `ai_research`
(ops `_maybe_weekly_scorecard` truyền `telemetry_path`).

## Dashboard

Khối **"AI RESEARCH (free-research, weekly)"** trên PaperDesk
(`renderer/app.js`) hiển thị 2 nhóm trên: passes/verdicts/vetoes, veto
rate, RUMOR_UNCORROBORATED, blocked hypo-PnL (scored), chi phí
Tavily/pages/provider-seconds. Số đi qua `desk.ai_scorecard` như khối
scorecard hiện có (không đổi hợp đồng state; hiệu lực khi owner
rebuild app).

## Chi phí đo được (thật, không ước tính)

Lượt bóng ma sống đầu tiên (sandbox, trận Villanova–Notre Dame
401920982): 6 vòng, 7 lần Tavily (70 kết quả), 5 trang mở, 102.1s
provider, usage OpenRouter của toàn phiên ~0.0028 USD
(`evidence/ai_free_research/live_sandbox_20261022/`). Ước tính chi phí
đầy đủ sẽ tích lũy từ telemetry ở runtime.
