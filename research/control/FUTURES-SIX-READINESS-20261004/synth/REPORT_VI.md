# BÁO CÁO TIẾNG VIỆT — FUTURES-SIX-READINESS-20261004 (2026-10-04)

## Tóm tắt một dòng (tầng 1)
Vòng PREP hoàn tất cho 6 mã ES/NQ/6E/6B/6J/6A: **sửa được lỗi dữ liệu thật (NQ), đóng thêm được ô calendar
thật (6E/6B), đo được 2 luật mới (6A) — tất cả verify độc lập 0 lỗi nghiêm trọng; không mã nào được phép
scored vì các quyết định của owner (phí D2/D3, ngân sách ES D4) vẫn còn mở.** 0 scored / 0 PnL / 0 S1 /
0 lệnh / 0 mua sắm.

## Đã làm (đủ 6 mã, 8 chiều/mã — chi tiết trong `SIX_SYMBOL_CENSUS.md`)

**1. NQ — sửa alias (ưu tiên cao nhất): LÀM XONG, TÁI LẬP ĐƯỢC.**
92,075 phút-ba bị rơi 2018-08→2020-05 (do filter dấu gạch) được thu hồi chính xác qua view rule PIT;
panel mới 6.780.608 dòng = cũ + đúng 92.075. Một ngày roll được sửa về điểm giao dịch(volume) thật
2020-03-19 (trước đó là handoff "chết" 2020-06-01). Quan trọng: chuỗi CŨ bị lỗi giữ hợp đồng đã ngừng
giao dịch 49 phiên (đúng "bệnh" 6J) — chuỗi mới hết sạch (0 vi phạm). Rebuild chạy 2 lần độc lập cho
kết quả trùng khớp từng byte logic.

**2. ES — 6/8 chiều PASS.** 68/68 ngày đáo hạn suy dẫn lại độc lập; giờ phiên 2026 verify từ bytes
23/23 ô; chặn còn lại là ngân sách trial (tối thiểu 36 > trần đóng băng 24) và phí chưa đối chiếu tài
khoản — cả hai là quyết định owner (D4, D2/D3), không phải thiếu dữ liệu.

**3. 6E/6B — calendar tiến rõ.** Đáo hạn FX cộng dồn 236/272 → **248/272**; tìm ra lịch 6B chính thức
sau-2018 đầu tiên; lập được bảng giờ-nghỉ-đ lệch 6E đầu tiên (34/42 cửa sổ); luật roll nâng từ
"chưa đo" lên "đo được 27 lần roll/mã, dẫn trước đáo hạn 13–19 ngày". PB2 giữ nguyên HOLD.

**4. 6J/6A — 2 luật mới đo được.** 6A: xung đột tick GIẢI QUYẾT theo thời kỳ — tick $10 đến 2020-11-20,
tick $5 từ 2020-11-23 (đo từ 327k+ giá đóng; bản cũ "$5 xuyên suốt" SAI với 2020). 6A: quy tắc roll k=5
đo thực 27 lần và bắt được **2 lần giữ hợp đồng chết** (17-12-2024, 16-06-2026) — cùng một bệnh với 6J
2022-09-20; biến thể có cease-guard tường minh = 0 vi phạm. 6J: hướng báo giá CHỨNG MINH lại từ dữ liệu
thô (không đảo chiều); chi phí RT $67,42 = 8,4499bp tái suy diễn chính xác từng bit. PB3 giữ PARK.

## Phát hiện sai sót (báo đủ, không xoá)
- **Chính tôi (controller)**: claim "d7fc6231 là ancestor của main" là SAI — owner bắt được; đã đo lại
  (fork tại 1f61b489; d7fc6231 nằm trên lineage futures, là cha của P3) và ghi INC-1 vào manifest.
- **Round anh em (Q5)**: coverage JSON liệt kê 23 capture nhưng 8 cái không có trên đĩa và không nằm
  trong fetch_log của chính nó (không ô giá trị nào phụ thuộc — MINOR).
- **Dispatch của tôi**: 2 con số gán nhầm (số expiry T2 bị ghi là holiday; "dòng 6E 2027-2029" không
  tồn tại trong capture 6E) — lane đã tự chỉnh in-artifact và tôi ghi nhận ở synth.
- 2 lane lần đầu ghi handoff thiếu/sai path — đã lập lại để ghi đúng; bản stray đã dọn.

## Quyền dữ liệu & A7 (tầng 2)
- Corpus databento = **owner đã duyệt mua** (trần $125, thực $105,81, có ledger); vòng này chỉ đọc.
  Quyền ngoài đọc-nghiên-cứu: **CHƯA GIẢI QUYẾT** (fail-closed) — D11.
- A7 phí: packet READY nhưng **KHÔNG CHẠY** — không có văn bản D2 của owner (71 kết quả grep toàn phủ
  định). Mọi mức phí giữ MODELED / chưa đối chiếu tài khoản / UNDER REVIEW.

## Owner cần quyết (gói `OWNER_DECISIONS.md`: D1–D7 giữ nguyên + 5 mục mới)
- **D8** chuẩn hóa luật tick 6A theo thời kỳ ($10→$5 tại 2020-11-20/23).
- **D9** đặt cease-guard tường minh thành luật chuẩn cho mọi chain-builder (bằng chứng 3 mã).
- **D10** ghi nhận erratum Q5 (8/23 capture thiếu).
- **D11** ghi rõ lớp giấy phép corpus databento.
- **D12** ô calendar còn hở: chạy tiếp lane permitted-route giá $0, hay để NOT_OBTAINED (không đề xuất
  mua/đăng ký gì).

## Trạng thái cuối
Worktree riêng `.worktrees/futures-six-readiness/prep`, branch `codex/futures-six-readiness-20261004`,
checkpoint wave-1 `9fa3fd14` + commit cuối của vòng này; 5 handoff `zcode_orch_v3_handoff@1` hợp lệ;
heavy lock không dùng; dirty tree của owner ở root không đụng; mọi gate đứng nguyên.

— Hết REPORT_VI.
