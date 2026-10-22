# HANDOVER R5 — Bóng ma trước, DỪNG chờ GO (không tự kích hoạt)
(PAPERDESK-FIXALL-NCAA-V1 / FREE-RESEARCH; 2026-10-22)

## Trạng thái bàn giao (mặc định khi bàn)

- Cờ config `ai_free_research.shadow = true` (BẬT): vòng nghiên cứu
  V3 chạy và ghi Ý KIẾN-BÓNG-MA vào namespace riêng
  (`ai_review/shadow/opinions_v3` + `shadow/research_journal` +
  `shadow/telemetry.jsonl`).
- **Phán quyết THẬT vẫn của đường V2 gói-nền hiện tại** — hành vi
  production KHÔNG ĐỔI: cùng prompt V2 + dấu V2, cùng opinion record
  schema, cùng cascade. Battery chứng minh phân lập:
  `test_shadow_plane_isolation_real_path_stays_v2`,
  `test_shadow_never_consumed_by_the_gate` (xóa opinion thật → cổng
  KHÔNG bao giờ fallback sang bóng ma).

## Lượt bóng ma sống đầu tiên (sandbox, 2026-10-22 02:27–02:29 UTC)

Trận NCAA thật Villanova–Notre Dame (401920982), chuỗi DeepSeek mới:
- đường THẬT: V2 nền → VETO, model deepseek-v4.1-flash-1017 effort
  max (đúng kiểm chứng R0b);
- đường BÓNG MA: 6 vòng công cụ (7 Tavily, 5 trang, 54 nguồn vào
  nhật ký), 102.1s, hết trần 6 vòng chưa phán → **luật im lặng** đúng
  thiết kế (SHADOW_SILENT, round_cap) — không ép phán.
Bằng chứng: `evidence/ai_free_research/live_sandbox_20261022/`.

## Báo cáo so sánh bóng ma (điều kiện đọc trước GO)

`P.shadow_comparison(data_root)` (schema
`shadow_research_comparison@1`, read-only) — sinh khi owner yêu cầu:
- đồng thuận trên các cặp cùng `candidate_hash` được CẢ HAI đường
  phán (consensus_rate);
- các ca sẽ-khác (bóng ma cho qua mà thật chặn và ngược lại) kèm tóm
  tắt bằng chứng 2 bên + cờ RUMOR_UNCORROBORATED;
- chi phí thêm THẬT đo được (Tavily calls, pages, provider seconds,
  journal reuse) từ shadow telemetry;
- `ready_for_owner_review` bật khi ≥ 20 bóng ma hoặc 4 ngày kể từ
  bóng ma đầu (cái nào tới trước).
Hiện trạng: 0/20 bóng ma ở máy bay thật — báo cáo đầy đủ sẽ có giá
trị sau vài ngày runtime; khung + luật sẵn sàng
(`test_shadow_comparison_readiness_rule`).

## DỪNG — không tự kích hoạt

Báo cáo tổng kết chu trình (PAPERDESK_FREE_RESEARCH_FINAL) ghi rõ
"V3 sẵn sàng — chờ owner GO kích hoạt". Việc lật cờ
`ai_free_research.shadow=false` (bóng ma tắt / V3 thành đường thật)
là GO RIÊNG của owner, KHÔNG nằm trong workstream này. Không câu GO
nào được typed ở bất kỳ đâu trong tài liệu của workstream.
