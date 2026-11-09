# BÁO CÁO GĐ4a PREFLIGHT — 2026-11-09 — VERDICT: VƯỢT KHUNG 14 NGÀY → DỪNG GĐ4, CHỦ QUYẾT THU HẸP

Người thực hiện: automation backstop hằng ngày (ủy quyền chủ 2026-11-08). Cửa sổ chọn dự kiến: [T_freeze−183 ngày, T_freeze), T_freeze dự kiến 2026-11-10 (sẽ gắn chính thức TRƯỚC lần chạy GĐ4b đầu tiên nếu được duyệt).

## 1. Số liệu đo trong ngày (đầy đủ, 3 nguồn)

- **Việc 3 HOÀN TẤT** (commit `9c3698f` đêm 09/11: phủ 105/105 ngày, hàng đợi rỗng, 71.351 thị trường duy nhất / 19.230 hợp lệ, 1.305 request thật/6 ngày) → điều kiện mở cửa GĐ4 ĐẠT. Từ nay Việc 3 = 0 request/ngày.
- Ngày Saigon 09/11 tại lúc chạy: Việc 3 = 175 (phiên cuối của nó), WSL = 0, lane ví pro = **3** (probe dưới đây) → tổng 178/200 ✓.

## 2. Probe trực tiếp (3 request, nhịp ≥10 giây, log + snapshot đầy đủ)

| # | URL | Kết quả |
|---|---|---|
| 1 | gamma `/events?tag_id=105959&closed=false` (WSL) | HTTP 200, 6 event mở (slug `wsl-mnu-whu-2026-09-27-total-corners`…) — đường liệt kê WSL theo tag HOẠT ĐỘNG |
| 2 | gamma `/events?closed=false&limit=5&order=id` | HTTP 200 — /events sống, trả tags kèm event |
| 3 | gamma `/tags?limit=100` | HTTP 200 — tồn tại nhưng săn id NBA/Soccer qua đây tốn nhiều trang; ĐỂ PHÍA SAU (không cần cho ước tính) |

Request log: `.my-quantitative-data/PRO-WALLET-V1/collect/request_log.jsonl`; snapshot kèm sha256 trong `collect/snapshots/`.

## 3. Đếm mô tả từng giải + ước request (neo trên SỐ ĐO của listing Việc 3 vừa xong, 2025-09-13→12-12)

Neo đo được (listing hợp lệ, trận đơn trước trận): **NBA 2.646 thị trường/54 ngày mùa = ~49/ngày mùa** (0 mùa nghỉ); **bóng đá nam 2.800/90 ngày = ~31/ngày mùa cao điểm**; **WSL = 0 qua /markets** (bị bỏ sót — chỉ thấy qua tag 105959, đã chứng minh).

Chiếu lên cửa sổ chọn 183 ngày (2026-05-11 → 2026-11-10; NBA nghỉ hè 19/6–19/10, bóng đá hạ 14/6–9/8 còn ~35% mật độ, WSL theo tuần):

| Giải | Thị trường ước | Request trades ước (1,2–3 lượt/thị trường, 500 fill/lượt) | Liệt kê |
|---|---|---|---|
| NBA | ~1.100–1.400 | ~1.900–3.800 | tag (~50, nếu tìm được id) hoặc quét /markets (~1.460) |
| Bóng đá nam | ~3.800–5.400 | ~5.500–9.100 | như trên |
| WSL | ~85 (tag) | ~95 | tag ~10–20 |

**Tổng 3 giải: ~9.000–14.600 request → 75–122 ngày @120/ngày. VƯỢT khung 14 ngày từ 5 đến 8,7 lần.**

| Phạm vi thay thế | Tổng ước | Ngày @120 | so khung 14 ngày |
|---|---|---|---|
| Chỉ NBA (có tag) | ~1.950–3.850 | 16–32 | VƯỢT 1,2–2,3× |
| Chỉ NBA (quét /markets) | ~3.350–5.250 | 28–44 | VƯỢT 2–3,1× |
| NBA + WSL (có tag) | ~2.050–3.950 | 17–33 | VƯỢT 1,2–2,4× |
| Chỉ WSL | ~105 | <1 | ĐẠT — nhưng cả tháng bóng chỉ ~4–6 trận có ý kiến → gần chắc THIẾU DỮ LIỆU theo luật ≥30 trận/giải |

## 4. Kết luận + đề xuất (KHÔNG dựa trên lãi — chủ quyết, lane không tự thu hẹp)

**Verdict: VƯỢT** — không phạm vi nào chứa NBA nằm trong khung ≤14 ngày & ≤120/ngày đã duyệt → theo luật GĐ4a: DỪNG HẲN GĐ4b, automation backstop tự tạm dừng.

Đề xuất theo thứ tự tôi khuyên:
- **A (khuyên) — NBA + WSL, nới khung NGÀY còn giữ nguyên mọi luật chọn ví + trần 120/ngày**: thu thập ~17–33 ngày (cận dưới nếu tìm được tag NBA ở phiên đầu). Không đụng luật đã chốt nào; đổi duy nhất hạn 14 ngày thành hạn mới do chủ ghi (ví dụ ≤35 ngày). Kết luận cuối lùi từ ~cuối 12 sang ~giữa tháng 1.
- **B — như A + nâng trần lane 120 → ~145/ngày** (tổng vẫn ≤200 vì WSL ≤50, Việc 3 = 0): giảm ~20% số ngày. Cần chủ chốt lại trần đã ghi trong quyết định b11e2172.
- **C — WSL-only chạy trước**: thu thập <1 ngày, khởi động quy trình sớm nhất; nhưng như bảng trên — mẫu quá nhỏ, cả tháng bóng gần chắc kết luận THIẾU DỮ LIỆU. Chỉ đáng nếu chủ muốn chạy thử quy trình.
- **KHÔNG đề xuất** thu hẹp cửa sổ chọn 6 tháng (183→90 ngày): đó là đổi định nghĩa "6 tháng" trong luật chọn ví đã chốt — làm danh sách ví mất tính hợp lệ theo đúng nghĩa đã kiểm toán.

## 5. Trạng thái cửa sau báo cáo này

- GĐ4b/c/d: **DỪNG** chờ chủ chọn phương án (A/B/C hoặc chỉ đạo khác).
- Automation backstop hằng ngày: **TẠM DỪNG** (đúng điều kiện dừng trong lệnh lập nó).
- Mọi thứ khác giữ nguyên: WSL 30 phút đã hoạt động, Việc 3 đã xong (chờ kiểm toán của riêng lane đó), lane này đã tiêu 3/23 request hôm nay.

---

"Giai đoạn 4a xong (preflight). Làm được: xác nhận Việc 3 HOÀN TẤT → mở cửa GĐ4, probe 3 request xác minh đường liệt kê, đếm mô tả 3 giải neo trên số đo của listing 19.350 thị trường. Chưa làm được: GĐ4b/c/d — preflight verdict VƯỢT (3 giải = 75–122 ngày; NBA+WSL tốt nhất 17–33 ngày vs khung 14) → dừng đúng luật. Cửa tiếp theo: chủ chọn phương án A/B/C (hoặc chỉ đạo riêng) → nếu duyệt, phiên GĐ4b đầu tiên gắn T_freeze rồi chạy."
