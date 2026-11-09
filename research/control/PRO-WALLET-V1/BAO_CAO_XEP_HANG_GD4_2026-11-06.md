# BÁO CÁO KIỂM XẾP HÀNG GĐ4 — 2026-11-06 — VERDICT: NOT_RUN (HÀNG CHƯA MỞ)

Người viết: agent chính (Mac), lúc 02:33 UTC 06/11. Prompt GĐ4 nhận cùng ngày, GO đã ban hành theo văn bản lệnh của chủ. Báo cáo này là kiểm tra bắt buộc mục 1 (xếp hàng) TRƯỚC phiên chạy đầu tiên.

## 1. Verify chuỗi đầu vào (đều PASS)

| Đối tượng | Kết quả |
|---|---|
| KE_HOACH_V2.md không bị sửa (N1–N5 xử lý bằng chữ) | sha256 `61188913b9e0bb8b9a176807a65b35a07ce12c5c0c413c781e4db7d1710c5d59` — KHỚP, giữ nguyên từng byte |
| Spec copytrade v2 (pin theo FILE) | sha256 `ae504a97feb50204c7028644f78bfd0d1728b8d3f0c9b7a52d0dfb64cbee55d8` — KHỚP |
| File QUYET_DINH_COORDINATOR_2026-11-06.md | **KHÔNG TÌM THẤY trên đĩa** — đã find: `research/control/`, `PRO-WALLET-V1/`, `Downloads/Polymarket/docs`, `workspace/your_files`, home (3 cấp), repo input `edge-hunt-ai-desk`. Xem mục 5 |

## 2. Kiểm xếp hàng — điều kiện "Việc 3 phải XONG trước": KHÔNG ĐẠT

Bằng chứng (file + commit, không suy diễn):

- `polymarket-copytrade-20-VIEC3-FIX-INTERIM-2026-11-06.md` (commit `040802a`): tiêu đề **"CHƯA XONG, DỪNG THEO LUẬT WATCHDOG"**; độ phủ tự nhiên **32/105 ngày**; còn thiếu 73/105 ngày (`09-27→09-30`, `10-04→10-06`, `10-10→10-13`, `10-23→10-26`, `10-30→12-26`); "Ước còn ~300–400 request nữa mới xong hết" (≈ 2 ngày chạy @200/ngày → xong ~08/11).
- Kết luận: Việc 3 CHƯA XONG → theo mục 1 prompt GĐ4: **NOT_RUN, báo cáo, chờ — không chạy**. Lane này HÔM NAY tốn **0 request** Polymarket.

## 3. Bảng đếm request 3 nguồn trong ngày (bắt buộc trước mỗi phiên — lần đầu tiên, ghi chú quy ước ngày)

| Nguồn | Số đã dùng | Bằng chứng | Quy ước ngày |
|---|---|---|---|
| (i) Việc 3 | 111/200 (còn 89, dừng vì watchdog hết lượt retry, chờ lệnh) | interim 06/11 + commit 040802a; tích lũy cả Việc 3: 869 request thật | Dương lịch Asia/Saigon |
| (ii) Worker WSL | 10 (00:04:14Z → 02:22:45Z, nhịp ~15,5 phút, 1 request/file journal, URL `gamma-api/events?tag_id=105959&closed=false…`) | 10 file `journal_wsl_lane_2026-11-06*.jsonl`, mỗi file 1 dòng LIVE_HTTP http 200 | UTC (tên file) |
| (iii) Lane PRO-WALLET-V1 | 0 (chưa từng chạy; request log sẽ khởi tạo ở phiên đầu) | — | — |

Cả 3 nguồn đều KIỂM CHỨNG được. Nhưng điều kiện tiên quyết (Việc 3 xong) sai → phiên hôm nay không mở, bất kể số dư trần.

## 4. Ước sơ bộ ngân sách GĐ4 (0 request, CHỈ từ mốc đo được — KHÔNG thay thế GĐ4a)

Mốc đo được (đều có file):
- Việc 3 tiêu 869 request để liệt kê 105 ngày thị trường (kèm dò-trước tối ưu) ≈ **8,3 request/ngày-liịch**. Cửa sổ chọn của lane này 183 ngày → liệt kê tương đương **~1.500 request ≈ 12–13 ngày @120/ngày** — gần cạn ngân sách 14 ngày trước khi lấy được phát lệnh trade nào.
- Việc 3 đo **15.428 thị trường hợp lệ/105 ngày** (2025, toàn thể thao, trận đơn trước trận) ≈ 147/ngày → 183 ngày ≈ ~27.000 thị trường; lấy trade ≥1 request/thị trường (trên 500 fill phải chia cửa sổ) → **hàng nghìn đến hàng chục nghìn request** cho 3 giải.

Hệ quả sơ bộ (cần GĐ4a đo thật để chốt): thu thập ĐẦY ĐỦ 6 tháng × 3 giải trong khung 14 ngày × 120/ngày (tổng 1.680) **có nguy cơ cao VƯỢT**. Nếu GĐ4a xác nhận vượt → theo luật: DỪNG + đề xuất giữ/thu hẹp KHÔNG dựa trên lãi (ví dụ: ưu tiên 1 giải trước, hoặc tìm tag_id riêng từng giải qua `/events?tag_id=` như WSL 105959 để rẻ hóa liệt kê — NBA/soccer chưa có tag_id đo được). Chủ quyết — lane không tự thu hẹp.

Khuyến nghị vận hành cho phiên GĐ4a đầu tiên (khi hàng mở): probe 3–5 request tìm tag_id NBA/soccer trước khi cam kết khuôn liệt kê toàn-thể-thao.

## 5. Phát hiện cần chủ/coordinator xử lý

1. **File QUYET_DINH_COORDINATOR_2026-11-06.md (bản ghi GO) không có trên đĩa.** Văn bản lệnh của chủ trong prompt vẫn là quyền hạn số 1, nhưng theo luật kiểm toán "file được trích dẫn mà không mở được → ghi rõ, không dựa vào nó": cần coordinator ghi file này (kèm hash) hoặc chủ chỉ đường dẫn, TRƯỚC phiên thu thập đầu tiên, để chuỗi GO khép kín cho GĐ5 kiểm toán.
2. Việc 3 còn cơ hội chạy tiếp 89 request trong cùng ngày 06/11 nếu chủ duyệt bằng văn bản (interim mục "Còn thiếu + đề xuất") — quyết của chủ, lane này không can thiệp.

## 6. Kế hoạch phiên sau

- Điều kiện mở phiên GĐ4a: interim/log Việc 3 ghi XONG (hoặc chủ ra lệnh chia trần riêng). Khi mở: kiểm 3 nguồn trong ngày + hash spec → chạy GĐ4a (đếm mô tả từng giải, ước request, ước ngày @120/ngày) → DỪNG, báo cáo preflight theo mục 2 prompt. Chỉ chạy tiếp GĐ4b nếu preflight ≤120/ngày VÀ ≤14 ngày.
- Hàng đợi ước lượng: Việc 3 xong ~08/11 (nếu chạy tiếp 89 request hôm nay và 200 các ngày 07–08/11).

---

"Giai đoạn 4 CHƯA xong — hôm nay NOT_RUN vì hàng chưa mở. Làm được: verify hash kế hoạch + spec (khớp), chứng minh Việc 3 chưa xong bằng interim 06/11, đếm đủ 3 nguồn request trong ngày (111 / 10 / 0), ước sơ bộ ngân sách 0-request với 2 mốc đo được, nêu rủi ro vượt khung 14 ngày × 120. Chưa làm được: mọi request thu thập (cấm khi Việc 3 chưa xong), GĐ4a preflight đo thật, GĐ4b/c/d. Cửa tiếp theo: Việc 3 xong (interim ghi XONG) + coordinator ghi file quyết định GO + kiểm 3 nguồn ngày đó → mở phiên GĐ4a đầu tiên."
