# QUYẾT ĐỊNH BỔ SUNG CỦA COORDINATOR — TRẦN REQUEST + WSL — 2026-11-06

Thẩm quyền: chủ ủy quyền quyết (09:22 ICT 06/11) + báo cáo GĐ4 phụ lục WSL
(sha 03501a5c…) do chủ chuyển tới 10:15 ICT. Bổ sung cho
QUYET_DINH_COORDINATOR_2026-11-06.md (sha 914838c1… — không sửa file đó).

## Sự việc đã đo (03:08–03:12Z 06/11, bằng chứng file-level, Mac agent đo)
- Việc 3: 172/200 (ngày Saigon). Lệnh "chạy tiếp 89" của chủ lúc 09:27
  (phiên khác) đã thi hành một phần 09:54–09:59 VN (+58 DNS-stop +
  3 watchdog = +61); agent Việc 3 commit cuối 02d8f3f "172/200, BẢN CUỐI,
  bỏ 28, chờ GO 07/11".
- WSL: 40 (ngày Saigon): 27 file tối 05/11 (17:06–23:49Z) + 13 file sáng
  06/11. Số "10" báo 02:33Z là theo ngày UTC — báo cáo đầu đã trộn 2 quy
  ước (Việc 3 theo Saigon, WSL theo UTC). Lỗi trộn quy ước này đã được tìm
  ra, ghi nhận.
- Tổng ngày Saigon 06/11: 172 + 40 + 0 = 212/200 — VƯỢT 12. Theo ngày UTC:
  74/200 — còn dư. Hai quy ước cho kết luận trái ngược.
- Lệnh duyệt 79 (coordinator đề xuất ~09:59) KHÔNG CÒN KHẢ THI — ngày đã
  vượt trần, chạy thêm 1 request cũng vi phạm thêm. GĐ4 NOT_RUN lần 2 đúng
  luật, 0 request tiêu.
- WSL chạy 24/7 nhịp ~15,5 phút ≈ ~93 request/ngày ≈ 47% trần 200. Đây
  là rò rỉ cấu trúc, không phải chuyện 1 ngày: 05/11 tổng 222; 06/11 tổng
  212 và còn tăng ~4/giờ nếu để chạy.

## Quyết định 1 — Quy ước ngày cho trần gộp: SAIGON
- Lý do: GO của chủ cấp theo ngày Việt Nam; code Việc 3 đã kẹp trần theo
  ngày Saigon; quy ước chặt hơn là quy ước an toàn cho trần đóng băng
  (trần tồn tại để bảo vệ tài khoản API khỏi rate limit).
- Hệ quả: ngày 06/11 đã vượt (212/200). Không lane nào chạy thêm hôm nay.

## Quyết định 2 — WSL + chia trần bằng văn bản (phân kỳ)
- WSL giảm nhịp từ ~15,5 phút xuống ~30 phút (≈50 request/ngày), từ
  07/11. Lý do bắt buộc: trần lane ví pro đã chốt là 120/ngày;
  120 + 93 = 213 > 200 — nếu WSL giữ 93 thì GĐ4 không bao giờ dùng đủ
  trần của nó, kể cả sau khi Việc 3 xong.
- Hôm nay 06/11: TẠM DỪNG worker WSL tới 00:00 ICT 07/11 (ngày đã vượt
  trần; để chạy tiếp sẽ tăng vượt từ 12 lên ~65). Rủi ro: khoảng trống
  snapshot WSL ~14 giờ — thấp (trận WSL theo tuần, event ít đổi trong
  ngày) so với rủi ro tài khoản API bị rate limit.
- Chia trần bằng văn bản (tổng luôn ≤200):
  - Tới khi Việc 3 xong: Việc 3 tối đa 150/ngày; WSL tối đa 50/ngày;
    lane ví pro 0 (đang xếp hàng).
  - Sau khi Việc 3 xong: lane ví pro tối đa 120/ngày (trần đã chốt);
    WSL tối đa 50/ngày; Việc 3 0. Tổng tối đa 170.
- GO ngày 07/11 cho Việc 3: trần 150 request (không phải 200), ngày
  Saigon, nhịp 10 giây/request, 1 tiến trình, 1 khóa. Việc 3 còn
  ~300–400 request → xong trong ~2–3 ngày (07–09/11) ở 150/ngày.

## Luật đứng (để không lặp lại vụ 09:27)
- Không duyệt thêm request khi chưa đếm đủ 3 nguồn trong ngày (Việc 3 +
  WSL + lane này), theo ngày Saigon. Lệnh duyệt 89 lúc 09:27 được ban khi
  chưa có số WSL đúng quy ước — ghi nhận, không truy cứu ngược.

## Hậu quả hoãn lại
- GĐ4 lùi theo Việc 3 (~2–3 ngày nữa). GĐ7 vẫn CẤM.
- Ngày 06/11 ghi nhận vượt trần 12 request (tăng dần nếu WSL không dừng)
  — vi phạm trần, không phải vi phạm luật khác; không phạt lane nào, sửa
  bằng chia trần ở trên.

Ký: coordinator — 2026-11-06
