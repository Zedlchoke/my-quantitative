# A7 — KIỂM TOÁN ĐỘC LẬP CHU TRÌNH FREE-RESEARCH (PAPERDESK-FIXALL-NCAA-V1)
Ngày kiểm toán: 2026-10-22. HEAD cuối: **main @ `e1ce4fab`**
(merge của nhánh `orca/paperdesk-fixall-ncaa-v1-integration` @ `9085b981`).
Người kiểm toán: bàn thực thi theo lệnh owner (kiểm toán tại HEAD cuối
của chính bàn — khác khuôn A7 trước đây do agent độc lập lập; đây là
HẠN CHẾ được ghi nhận thẳng vào verdict).

## Phạm vi kiểm (chu trình FREE-RESEARCH R0–R5 + R0c + adoption)

### 1. Battery
- `tests/papertrade_exec/` — **315/315 PASSED, 2 lần liên tiếp**, chạy
  TỪ chính checkout production (root, post-merge) tại HEAD cuối.
- Battery mới `test_free_research.py` (34 test) phủ R0b/R0c/R1/R2/R3
  (đủ 5 ca bắt buộc a–e)/R4/R5.

### 2. Luật quyết định không bị đụng
- `seal.js`, `pm_stake_law.js`, `paper_policy.js`, `ai_gate.js`:
  diff `9f7b8011..e1ce4fab` = RỖNG (free-research không đụng seal,
  stake, policy, gate JS).
- Luật EV/stake/cap/cổng deterministic: không thay đổi; đổi duy nhất
  cấu hình model + effort + balance-key_ref + khối `ai_free_research`
  theo LỆNH OWNER (có nhật ký ai ra lệnh/khi nào trong config note).

### 3. Chuỗi DeepSeek + đồng hồ số dư
- Config: head `deepseek/deepseek-v4.1-flash-1017` effort max; fallback
  duy nhất `deepseek/deepseek-v4.1-flash` (lệnh #2); kiểm slug sống 2
  lần trên `/api/v1/models`.
- Cascade THẬT (máy bay production): `cascade_state.json` updated
  `2026-10-22T03:44:31Z` — `deepseek/deepseek-v4.1-flash-1017` **UP**,
  `deepseek/deepseek-v4.1-flash` **UP** nhờ đồng hồ số dư (10.00 ≥
  10.00). Các slot chuỗi cũ còn treo COOLDOWN_402 là STALE (không còn
  trong config order, không tham gia) — dọn dẹp để khối quan sát sau.
- Khóa quản trị: Keychain-only, `balance_key_ref` trong config, luật
  balance-only, hết hạn VĨNH VIỄN (không cần alarm); số dư đọc được
  **10.00 USD**; fallback `/credits` chỉ chạy cho khóa quản trị — khóa
  thường giữ None trung thực.

### 4. Shadow plane (R5)
- Real path giữ V2 byte-for-byte (battery phân lập + gate không bao giờ
  đọc `shadow/opinions_v3`).
- Máy bay thật: pending trống, `decisions_paused=True`
  (window-close-policy — việc mở lại là của owner trong UI) → bóng ma
  chưa có mục; đường bóng ma đã chạy SỐNG end-to-end ở sandbox M6
  (6 vòng / 7 Tavily / 5 trang / 102.1s / hết trần → im lặng đúng luật)
  — bằng chứng `evidence/ai_free_research/live_sandbox_20261022/`.

### 5. Bảo mật / akhlak kỹ thuật
- Quét giá trị khóa (`sk-or-v1-`, `tvly-dev-<đoạn giá trị>`) trên
  research/ apps/ tests/ plans/: SẠCH.
- Không câu GO nào được typed trong tài liệu chu trình (scan regex).
- Không push: `origin/main..main` = 161 commit (toàn bộ lịch sử local
  cũ + merge mới; chu trình KHÔNG chạy lệnh push).
- Ledger: self-check của app — **91/91 rows, chain_ok=true, 0 errors**.

## FINDINGS

| # | Mức | Nội dung |
|---|-----|----------|
| F-1 | LOW | Registry mainline không có dòng PAPERDESK-FIXALL-NCAA-V1 và dòng SPORTS-PAPERTRADE-EXEC-V1 phía main thiếu marker GO-consumed → flags fail-closed khi chạy code mới. ĐÃ XỬ LÝ: đối chiếu 2 marker vào dòng row qua house tool `researchctl cycle update` (CAS, có reason + provenance; registry sha256 ghi trong output tool). Kiến nghị: controller rà lại lần nữa. |
| F-2 | LOW | Cascade thật còn 8 slot stale của chuỗi cũ (COOLDOWN_402 / minimax UP) không còn trong config — chỉ là dữ liệu quá khứ; khối dashboard đọc config order nên không ảnh hưởng. |
| F-3 | INFO | `decisions_paused=True` (window-close policy) — production sẽ bắt đầu sinh candidate + dữ liệu bóng ma thật sau khi owner mở lại quyết định trong cửa sổ PaperDesk. |
| F-4 | INFO | A7 lần này do bàn thực thi chu trình tự lập tại HEAD cuối (owner lệnh), không phải agent ngoài — đã ghi ở đầu verdict. |

## VERDICT

**PASS_WITH_FINDINGS — 0 CRITICAL / 0 HIGH / 2 LOW / 2 INFO.**

FREE-RESEARCH R0–R5 + R0c + adoption: cấu hình đúng hai lệnh owner,
battery xanh 2× tại HEAD cuối, luật quyết định nguyên vẹn, seal không
đụng, khóa không lộ, không push, cascade 2 nấc DeepSeek UP bằng đồng hồ
số dư thật (10.00 USD), ledger chain OK. Việc kích hoạt V3 (lật
`ai_free_research.shadow=false`) VẪN LÀ GO RIÊNG CỦA OWNER — workstream
này không typed câu GO nào.
