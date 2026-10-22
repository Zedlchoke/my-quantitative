# HỒ SƠ KÍCH HOẠT AI_PROMPT_V3 LÊN TRỌNG TÀI THẬT — GO CỦA OWNER
(PAPERDESK-FIXALL-NCAA-V1 / FREE-RESEARCH; kích hoạt 2026-10-22)

## Căn cứ GO

- **Owner GO qua chat điều phối lúc 2026-10-22 14:17 ICT (07:17Z)**:
  "cho AI_PROMPT_V3 (trọng tài tự nghiên cứu) lên phán lane thật NGAY
  BÂY GIỜ".
- **GHI RÕ QUYẾT ĐỊNH BỎ QUA CỔNG CHỜ**: điều kiện đọc báo cáo bóng ma
  (≥20 ý kiến bóng ma hoặc 4 ngày) **CHƯA ĐẠT** tại thời điểm kích hoạt
  — mới có 1 lượt bóng ma thật (FD-2026-M48, SHADOW_SILENT round_cap
  07:05:34Z + SHADOW_OPINION VETO 07:07:34Z, ngày đầu tiên). Owner chủ
  ĐỘNG bỏ qua thời gian tập sự bằng GO này; hồ sơ này ghi đúng thực tế:
  **kích hoạt là quyết định chủ quyền của owner, KHÔNG phải cổng chờ đã
  đạt.**
- Việc kích hoạt theo đúng thiết kế đã đóng băng: chỉ lật công tắc,
  không sửa code, không đụng luật khác.

## Thao tác

- File: `research/papertrade_exec/config.json` (production, checkout
  gốc — file mà `execute.load_config()` của service đang chạy đọc mỗi
  pass).
- Khóa lật: `ai_free_research.shadow` — **True → False** (lúc
  2026-10-22 07:26Z / 14:26 ICT).
- Khác biệt so với bản backup (`/tmp/config_pre_v3_activation.json`,
  sao chép vào evidence): **KHÔNG khóa nào khác thay đổi** (so cây
  JSON tự động). Code không đụng; `AI_PROMPT_V2.md` giữ nguyên trên
  đĩa (trọng tài V2 vẫn đóng băng, có thể quay lại bằng cách lật ngược
  công tắc).
- Không cần khởi động lại: `load_config` đọc file mỗi pass producer;
  pass kế tiếp tự đi nhánh GO (prompt V3 + tools).

## Ý nghĩa vận hành (luật hiện hành sau kích hoạt)

- Mọi candidate PENDING_AI mới được chấm bởi vòng nghiên cứu V3:
  prompt AI_PROMPT_V3 (sha đăng ký `c2c4fd46…`), cascade
  DeepSeek-only (flash-1017 effort max → flash), trần 6 vòng / 10
  trang / 8k token-vòng / đồng hồ 600s dùng chung, nhật ký công cụ
  nguyên văn theo candidate_hash, bộ lọc trích U0 trên tập hợp nhất
  (nền + công cụ), thang nguồn + răng cứng rumor.
- Luật im lặng giữ nguyên: trọng tài MỚI được ĐI TÌM trước, nhưng nếu
  tra cứu mà không ra gì đáng tin → VETO INSUFFICIENT_EVIDENCE; hết
  trần chưa phán → im lặng (candidate nằm chờ, bị chặn an toàn).
  Ý kiến ghi `prompt_version: AI_PROMPT_V3` + `prompt_sha256:
  c2c4fd46…`.

## Bằng chứng kích hoạt

- Xem `evidence/ai_free_research/v3_activation_20261022/` (config
  trước/sau + ý kiến thật đầu tiên do V3 phán, cập nhật khi có).
