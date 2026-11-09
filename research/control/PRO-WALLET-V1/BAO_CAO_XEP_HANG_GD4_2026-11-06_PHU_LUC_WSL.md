# PHỤ LỤC — LỆNH DUYỆT "Việc 3 chạy tiếp 79" KHÔNG THỂ THI HÀNH — 2026-11-06 03:12 UTC

Người viết: agent chính (Mac). Lệnh của chủ nhận sáng 06/11: "DUYỆT: Việc 3 chạy tiếp tối đa 79 request trong ngày 06/11... Tổng: 111 + 79 = 190, cộng WSL 10 = 200 đúng trần gộp. Nhịp 10 giây, 1 tiến trình, 1 khóa. Hết 79 thì dừng, báo interim."

## Kết luận: NOT_RUN — KHÔNG chạy tiếp. Hai con số trong lệnh đã cũ, và trần gộp ĐÃ VƯỢT.

## 1. Số liệu lệnh dựa trên đã cũ (đo lại tại 03:08–03:12Z)

| Số | Lệnh của chủ giả định | Đo thực lúc 03:08Z | Bằng chứng |
|---|---|---|---|
| Việc 3 đã dùng ngày Saigon 06/11 | 111 | **172** | đếm ledger.jsonl bằng đúng phương pháp sổ của Việc 3; commit `02d8f3f` ("BẢN CUỐI: 172/200 — đêm 111 + sáng 58 DNS-dừng + 3 watchdog; bỏ 28; chờ GO 07/11") |
| WSL đã dùng | 10 | **40** trong cửa sổ ngày Saigon 06/11 | 27 file journal 05/11T17:06→23:49Z + 13 file 06/11T00:04→03:07Z, mỗi file 1 request gamma `/events?tag_id=105959`, nhịp ~15,5 phút |

Diễn giải: lệnh 09:27 "chạy tiếp 89" của chủ cho phiên khác ĐÃ được thi hành một phần lúc 09:54–09:59 VN (log `list3_run_day6b/c.log`): +61 request → 172/200; agent Việc 3 tự dừng (DNS chậm + 3 watchdog), tuyên bố "BẢN CUỐI" ngày 06/11, "chờ GO 07/11", bỏ 28 request còn lại. Con số "WSL 10" trong lệnh là số tôi báo lúc 02:33Z theo quy ước NGÀY UTC; theo quy ước ngày Saigon (quy ước mà chính code Việc 3 dùng để kẹp trần 200) thì WSL đã ở 40.

## 2. Phép tính trần gộp (đúng quy ước ngày Saigon mà code Việc 3 tự kẹp)

- Việc 3: 172 + WSL: 40 + lane này: 0 = **212 > 200**. Ngày Saigon 06/11 đã vượt trần 12 request (WSL tiếp tục +~4 request/giờ).
- Khoảng dư còn lại = **−12**. Chạy thêm 1 request nào cũng vi phạm thêm. Theo luật "thiếu dư trần = NOT_RUN": không chạy.
- Ghi chú quy ước: nếu chủ định nghĩa ngày theo UTC thì hôm nay mới dùng 74/200 (Việc 3 61 + WSL 13) — còn dư. Hai quy ước cho hai kết luận trái ngược → **cần chủ chốt bằng văn bản một quy ước ngày cho trần gộp**. Trong lúc chưa chốt: fail-closed theo quy ước chặt hơn (Saigon, trùng code Việc 3).

## 3. Phát hiện cấu trúc (quan trọng hơn con số hôm nay)

Worker WSL chạy 24/7 nhịp ~15,5 phút ≈ **~93 request/ngày ≈ 47% trần 200**. Hệ quả:
1. Việc 3 còn cần ~300–400 request: tối đa ~107/ngày (200 − 93) → **3–4 ngày nữa**, không phải 2 như interim ước.
2. **Lane PRO-WALLET (GĐ4) không bao giờ mở được cửa xếp hàng** nếu WSL giữ nhịp này và trần gộp 200 giữ nguyên — hàng không bao giờ thông. Chủ cần một trong ba: (i) tạm dừng/giảm nhịp worker WSL trong các cửa sổ thu thập (worker của lane khác — tôi không đụng theo luật); (ii) chia trần bằng văn bản cho từng tiến trình (tổng vẫn ≤200); (iii) chấp nhận lùi thời gian toàn bộ.

## 4. Tôi đã làm / không làm

- 0 request API gọi thêm. Không đụng worker WSL, không đụng dữ liệu Việc 3 (chỉ đọc), không giữ/loại khóa nào (khóa Việc 3 hiện sạch, không tiến trình sống).
- Không chạy continuation dù lệnh yêu cầu — vì phép tính của lệnh không còn đúng với thực tế đo được và việc chạy sẽ vi phạm trần gộp do chính lệnh đó tái khẳng định ("đúng trần gộp").

## 5. Đề xuất chủ quyết (không khẩn cấp trong hôm nay — ngày đã đóng)

1. Chốt quy ước ngày cho trần gộp (Saigon hay UTC) — viết vào một dòng quyết định.
2. Quyết phương án WSL: giảm nhịp / tạm dừng theo cửa sổ / chia trần cố định.
3. GO ngày 07/11 cho Việc 3 (phiên của nó đang chờ) — kèm số trần phản ánh WSL ~93/ngày.
