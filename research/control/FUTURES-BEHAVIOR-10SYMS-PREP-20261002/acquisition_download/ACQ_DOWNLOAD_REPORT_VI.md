# BÁO CÁO TẢI DỮ LIỆU DATABENTO (lane ACQ-DOWNLOAD) — tiếng Việt tóm tắt cho owner

Sinh 2026-10-02T22:40:14+00:00

## Đã làm gì

1. **Gói trim**: A-v1 gốc $129.57 > trần → tính get_cost 4 phương án trim (miễn phí, chỉ metadata). Chọn **C3_staggered_9m_6m**: cắt sâu ohlcv-1m 4 cặp FX (6E/6J từ 2026-01, 6B/6A từ 2026-04), GIỮ NGUYÊN NQ/ES/GC/SI 24m, CL/NG 9m, definitions+statistics 24m. Tổng quote **$113.0460** ≤ mục tiêu $115. (Phương án FX 12 tháng $115.52 bị loại vì vượt $115.)
2. **Tải theo chunk**: 92 batch nhỏ (3-6 tháng/lần) qua API batch chính thức; MỖI batch đều get_cost lại trước khi submit và kiểm luật ngân sách (cam kết ≤ $118 < trần $125 của owner). Thứ tự: definitions/statistics → NQ/ES → GC/SI → FX → CL/NG. Mỗi batch: SHA256 khớp hash nhà cung cấp → QA bằng adapter code/futbt/dbn → chuyển parquet → checkpoint ledger → copy iCloud.
3. **Tiến độ tại thời điểm báo cáo**: 72/92 chunk hoàn tất (tải+QA+mirror); cam kết chi tiêu **$105.8101** / quote gói $113.0460 / hard-stop $118 / trần $125.
4. **QA từng batch**: số bản ghi thực tế khớp quote (drift 0.000% trên các chunk đã QA — xem ledger); schema fail-closed; kiểm trùng/lệch chuỗi/cửa sổ thời gian; giá âm giữ nguyên; thang 6J hợp lệ; DST/session. Phát hiện và ghi nhận quy tắc phát sóng của vendor (definitions phát lại mỗi phiên mở, spread legs là bản ghi riêng theo leg_index — 0 trùng thật, 0 xung đột nội dung).
5. **iCloud mirror**: copy raw + parquet + QA json + entry ledger vào CloudDocs/my-quantitative-futures/av1-trim/, SHA256 verify từng file. Trạng thái trung thực: COPIED + SYNC_PENDING_UNVERIFIED (việc upload lên đám mây là của macOS/iCloud — lane không tuyên bố đã lên cloud). Đây là backup cá nhân của owner cho dữ liệu có bản quyền — không phân phối.
6. **IBKR overlap validation** (NQ + CL, cửa sổ 2025-08→nay nơi IBKR raw có dữ liệu): xem kết quả chi tiết trong IBKR_OVERLAP_VALIDATION.json và bảng tiếng Anh trong DOWNLOAD_REPORT.md.

## Tiền

- Quote gói đã duyệt (trim): **$113.0460**
- Đã cam kết (submit+): **$105.8101**
- Còn lại tới hard-stop lane $118: **$12.1899**
- Còn lại tới trần owner $125: **$19.1899**
- get_cost là báo giá chính thức theo từng chunk (không phải ước tính); vendor tính phí batch theo cùng bảng $/GB. Đối chiếu hóa đơn thực tế trên usage page là bước owner-side.

## Blocker / lưu ý

- Trạng thái chunk còn lại: {"MIRRORED": 72, "DROPPED_BY_OWNER_RESCOPE": 20}. Nếu lane dừng giữa chừng, ledger COMPLETION_LEDGER.json ghi chính xác chunk nào xong, chunk nào pending — chạy lại acq_pipeline.py sẽ resume không mua trùng.
- Dữ liệu thô nằm NGOÀI git: /Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/
- Không có key/credential trong bất kỳ artifact nào (đọc in-process, chỉ qua Authorization header, lỗi được redact).
