# LIVE READINESS — Polymarket thật (PAPERDESK-FIXALL-NCAA-V1 · W6)

> Ngày: 2026-10-21 · **HỒ SƠ THÔI — KHÔNG CODE, KHÔNG VÍ, KHÔNG NẠP TIỀN
> trong gói này.** `LiveExecution` giữ nguyên SEALED
> (`apps/paperdesk/main/seal.js` — method duy nhất `submit()` ném lỗi).
> Không một dòng chữ nào dưới đây là GO.

## 0. Trạng thái thật (đo tại HEAD của gói)

- Toàn bộ vòng đời hiện tại là **paper**: `BET_PAPER` trên
  `paper_ledger.jsonl` append-only (hash-chain), không có đường nào đến
  một order thật. Ngay cả câu GO "cutover" cũng chỉ đổi NGUỒN GIÁ PAPER
  (xem CUTOVER_READINESS_NOTE_2026-10-21.md) — không có tiền thật nào di
  chuyển.
- Những mảnh đã DÙNG ĐƯỢC cho live sau này (đừng xây lại): book-walk theo
  stake thật + phí taker thật 0.05·p·(1−p) (`pm_moneyline.py`,
  `wsl_lane.py`); joiner khớp event/market/token theo tên đã ghim (đã
  live-verify trên event thật 1191461); luật UMA settle (WSL); ledger
  append-only + audit toàn bộ; CLV plane; cổng AI hash-lock.

## 1. Những gì CÒN THIẾU để đặt lệnh thật (liệt kê đủ, đúng thứ tự phụ thuộc)

| # | Mảnh | Trạng thái | Việc cần |
|---|---|---|---|
| 1 | Ví & custody | KHÔNG TỒN TẠI (không key, không seed, không địa chỉ nào trong repo — đúng luật) | Tạo ví giao dịch DEDICATED (không bao giờ tái sử dụng key khác); custody ngoài app (hardware/policy wallet); allow-list địa chỉ; quy trình xoay key |
| 2 | Ký EIP-712 cho CLOB | KHÔNG TỒN TẠI (không thư viện ký, không typed-data struct trong repo) | Chọn thư viện (poly-market clob-client chính thức hoặc tự viết typed-data), freeze phiên bản, audit tầng ký |
| 3 | Endpoint đặt/huỷ lệnh + vòng đời order | Mọi URL PM trong repo đều là GET (Gamma/CLOB book đọc) | POST/DELETE order, nhận fill một phần/toàn phần, xử lý partial fill theo stake law (không re-size sau walk), đối soát fill ↔ ledger |
| 4 | Redeem sau UMA | Chưa có | Claim winnings sau `umaResolutionStatus=resolved`, hạch toán về ví, ghi sổ rút tiền |
| 5 | Số dư/allowance/gas | Chưa có | Kiểm USDC balance + allowance cho exchange contract, gas dự phòng, cảnh báo số dư thấp |
| 6 | Geoblock / KYC / tài khoản | Chưa có | Xác minh quyền giao dịch theo khu vực; Polymarket có ràng buộc vùng — kiểm tra TRƯỚC khi tạo tài khoản |
| 7 | Pháp lý Việt Nam | Chưa đánh giá | Tham khảo pháp lý độc lập cho giao dịch prediction-market từ VN (dư địa pháp lý hiện hành); quyết định chỉ tiếp tục nếu hợp pháp |
| 8 | Giới hạn rủi ro live | Chưa có | Cap lệnh/ngày, cap exposure live RIÊNG (không kế thừa cap paper), kill-switch tự động, ngân sách mất tối đa chấp nhận được |
| 9 | Đối soát tiền | Chưa có | Đối chiếu on-chain balance ↔ ledger mỗi ngày; mọi lệch là incident cao |
| 10 | Điều kiện tiên quyết chương trình | — | (a) W0–W4 đã xong và đang chạy trên runner production; (b) CLV đo được > 0 trên mẫu đủ lớn (khối CLV W2.4 là nguồn số); (c) owner GO RIÊNG cho live (không phải GO cutover, không phải GO AI); (d) một vòng A7 audit độc lập RIÊNG cho tầng thực thi trước khi mở seal |

## 2. Thứ tự nếu owner quyết tiến (không phải làm trong gói này)

1. Đăng ký chu trình RIÊNG "SPORTS-LIVE-EXEC-V1" (spec, ngân sách, gates
   riêng) — live KHÔNG BAO GIỜ là một lần lật cờ của gói paper.
2. Items 1–2 (ví + ký) trong sandbox ký-tested, không mạng.
3. Testnet/paper-with-real-books: đặt lệnh giá trị tối thiểu, đối soát
   fill, redeem 1 lần.
4. A7 audit độc lập tầng thực thi (fresh context) → owner gõ GO tại cổng
   của chu trình live → mở seal theo đúng 4 điều kiện ghi sẵn trong
   `seal.js`.

## 3. Rủi ro phải nhận trước

- Smart-contract/bridge risk của Polymarket; thanh khoản mỏng ở chân xa
  (walk fail-closed sẽ từ chối — chấp nhận bỏ lỡ); UMA tranh chấp kết quả;
  geoblock thay đổi bất kỳ lúc nào; rủi ro pháp lý cá nhân.
- Mô hình hiện có KHÔNG có bằng chứng thắng thị trường ở giải nào trừ
 tín hiệu hậu kiểm NCAA-nam >10% (chưa đăng ký, chưa tiền xử lý) — nhãn sự
  thật W5.5 áp dụng cho mọi giải khi nói về tiền thật.
