# PAPERDESK_FREE_RESEARCH_FINAL — 2026-10-22
(PAPERDESK-FIXALL-NCAA-V1 / workstream FREE-RESEARCH R0–R5)

**Tình trạng: V3 SẴN SÀNG — CHỜ OWNER GO KÍCH HOẠT.** Verdict của bàn
là TẠM cho tới khi A7 kiểm toán độc lập tại HEAD cuối. KHÔNG có câu GO
nào được typed trong chu trình này; việc lật
`ai_free_research.shadow=false` là GO riêng của owner.

## Đã bàn giao (đủ R0–R5)

| Gói | Nội dung | Handover |
|---|---|---|
| R0 | Khóa Tavily vào Keychain (service `com.myquant.paperdesk` / account `tavily-api-key`), đọc lại khớp, smoke test HTTP 200, hạn mức dev 1.000 credits/tháng | HANDOVER_R0 |
| R0b | Chuỗi DeepSeek-ONLY (2 lệnh owner cùng ngày): head `deepseek/deepseek-v4.1-flash-1017` effort **max**, fallback duy nhất `deepseek/deepseek-v4.1-flash`; cơ chế `reasoning_effort_by_model` | HANDOVER_R0B |
| R1 | `ai_free_research.py`: `tim_web` (Tavily, khóa từ Keychain tại thời điểm gọi) + `mo_trang` (SSRF guard cả IP sau DNS), nhật ký nguyên văn theo `candidate_hash` | HANDOVER_R1 |
| R2 | `run_research_loop`: hội thoại tool-calling, trần 6 vòng / 10 trang / 8000 token-vòng / đồng hồ 600s dùng chung, cascade cho TỪNG lần gọi, hỏng mềm cho tool rác + tool-incapable, tái dùng journal, bộ lọc union H1/U0 | HANDOVER_R2 |
| R3 | `AI_PROMPT_V3.md` đóng băng, sha đăng ký `c2c4fd46…` (công thức digest-blanked U0), erratum V2→V3, cổng tiêu thụ so dấu theo phiên bản, răng cứng thang nguồn `rumor_domains` | HANDOVER_R3 |
| R4 | Telemetry mỗi lượt chấm + `compute_research_split` (base_only vs researched: veto rate, hypo-PnL nhóm bị chặn, RUMOR đếm riêng, chi phí) + khối dashboard "AI RESEARCH" | HANDOVER_R4 |
| R5 | `shadow=true` mặc định: bóng ma ghi riêng, phán quyết thật giữ V2; `shadow_comparison` + điều kiện sẵn sàng ≥20 bóng ma / 4 ngày | HANDOVER_R5 |

## Kiểm chứng sống (máy Mac, 2026-10-22)

- Tavily: 1 search thật HTTP 200/5 kết quả (2.44s).
- Model: `deepseek/deepseek-v4.1-flash-1017` kiểm sống trên
  `/api/v1/models` 2 lần (trước và sau lệnh #2); fallback pin
  `deepseek/deepseek-v4.1-flash` (slug `deepseek-v4.1` thuần KHÔNG tồn
  tại — khác biệt ghi minh bạch trong HANDOVER_R0B).
- Lượt chấm sandbox (trận thật 401920982 Villanova–Notre Dame): opinion
  THẬT do deepseek-1017 **max** tạo ra (VETO), nấc UP; bóng ma: 6 vòng,
  7 Tavily, 5 trang, 102.1s, hết trần → im lặng đúng luật. Toàn bộ ở
  `evidence/ai_free_research/live_sandbox_20261022/`.
- Battery: `tests/papertrade_exec/` **313/313 xanh 2 lần liên tiếp**
  (chạy lại lần nữa sau thay đổi đồng hồ số dư — vẫn 2× xanh).

## Phát hiện quan trọng (owner cần đọc)

**Đồng hồ số dư MÙ với khóa OpenRouter hiện tại.** Khóa là khóa cấp
tài khoản (`/api/v1/key`: `limit=null`, `limit_remaining=null`);
`/api/v1/credits` đọc được bằng khóa này là view cấp khóa
(`total_credits=0`) — KHÔNG phản ánh 10 USD owner nạp. `check_balance`
trả `None` trung thực (không bao giờ bịa số — một bản fallback tạm đã
bị thu hồi vì nó suy ra số dư ÂM và sẽ GIỮ nấc trả phí vô thời hạn).
Hệ quả:
- Chuỗi cũ (có nấc free) vẫn chạy khi trả phí held; **chuỗi DeepSeek-ONLY
  mới KHÔNG còn nấc free** → một cú 402 sẽ đưa CẢ LỚP AI vào im lặng
  (QD2) cho tới khi có hành động bên ngoài. AI_LOW_BALANCE /
  AI_PROVIDER_DOWN alarm vẫn là kênh báo owner.
- Khuyến nghị (quyết định owner): cấp một **provisioning key** có quyền
  đọc credits cho đồng hồ số dư (key_ref thứ ba trong Keychain), hoặc
  chấp nhận chế độ "402 → im lặng + alarm".

## Việc còn lại của owner

1. Đọc `SHADOW_RESEARCH_COMPARISON.json` sau khi đã ≥20 bóng ma / 4
   ngày runtime (cần rebuild trước để bóng ma chạy ở production) →
   **GO kích hoạt V3** (lật `ai_free_research.shadow=false`).
2. Quyết định đồng hồ số dư: provisioning key hay chấp nhận 402→im
   lặng + alarm (mục trên).
3. Nạp OpenRouter (đã nạp 10 USD — xác nhận còn hiệu lực).
4. GO kỷ nguyên U7 (việc đang chờ sẵn).
5. Merge/push + rebuild app — từ rebuild, bóng ma R5 bắt đầu chạy ở
   production với chuỗi DeepSeek mới.
6. (Khuyến nghị) tạo lại khóa Tavily sau khi cài đặt chạy ổn — khóa
   hiện tại đã đi qua kênh chat.

## Ranh giới đã giữ

Không push/merge, không đụng seal/ledger/quyết định thật, không đụng
CLV plane (U6) và bóng ma U7, giấy 100%, battery xanh 2× sau mỗi lần
code đổi, handover riêng từng workstream, không tự gõ bất kỳ câu GO
nào. Giá trị khóa Tavily KHÔNG nằm trong repo/log/config/handover
(chỉ `key_ref`).
