# OWNER_ACQUISITION_RUNBOOK — DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1 (deliverable D3)

Vietsimple language; every action is OPTIONAL and owner-only. Nothing here
asks you for passwords or API secrets — never paste credentials, statement
contents or licensed bytes into chat or Git.

**An toàn chung:** mọi file bạn tải/xuất đặt thẳng vào máy ở
`~/.my-quantitative-data/<tên-nguồn>/` (thư mục này đã ngoài Git). Tôi chỉ
cần bạn ghi nhận "đã đặt file X ở đường dẫn Y" — tôi tự hash/manifest và
chỉ đưa checksum + metadata vào Git. Statement cá nhân, token, key,
raw bytes có license: KHÔNG gửi vào chat, KHÔNG commit.

---

## R1 — IBKR statement + FX market data (ưu tiên cao nhất; mở 6/10 thành phần cost của FX)

Tại sao: sàn cost 3.6/4.4 pip của ERP1 đang chia đôi không gian FX; dữ liệu
financing/swap từ broker là thứ duy nhất DI CHUYỂN được sàn này. Máy đã có
TWS (chạy hôm nay), API Read-Only đã chứng minh phía server — chỉ thiếu 2 việc:

1. Trong TWS/Client Portal: bật **market data FX delayed (free)** cho
   IDEALPRO (không tốn tiền, cần login tài khoản IBKR của bạn).
   https://www.interactivebrokers.com → Client Portal → Settings →
   Market Data Subscriptions.
2. Xuất **một** Activity Statement (hoặc Flex Query) gồm: giao dịch FX +
   vị thế qua đêm, cửa sổ bất kỳ có activity (tốt nhất T4–T7 gồm một cuối
   tuần). Client Portal → Performance & Reports → Statements/Flex Queries.
   Xuất CSV, lưu vào `~/.my-quantitative-data/ibkr_statement/`.
3. Khởi động lại TWS sau khi subscribe (API socket 7497 giữ Read-Only).
   Không cần đổi cài đặt API nào thêm.

Sau đó tôi chạy probe đã đóng băng (một lệnh, chỉ đọc: contractDetails +
phân tích statement) và đo spread/commission/swap/margin cho 5 cặp major.
KHÔNG gửi nội dung statement vào chat — chỉ đường dẫn file.

## R2 — Nguồn FX thứ hai để replication (chọn MỘT; mở gap O1)

Gói chi tiết đã có sẵn từ EURUSD-DATA-QUALIFICATION-V1:
`research/control/eurusd_data_qualification_v1/owner_packet_source_survey_2026-09-22.md`
(3 đường cụ thể + đánh giá license). Tóm tắt:
- **TrueFX** (https://www.truefx.com) — free sau khi đăng ký; cần chủ động
  đọc/ghi lại điều khoản (TCU) cho nghiên cứu nội bộ rồi gửi tôi bản chụp
  điều khoản (không gửi tài khoản/mật khẩu). Dung lượng ~2–4 GB/năm/cặp.
- **OANDA v20 practice** (https://www.oanda.com) — tài khoản practice free;
  tôi cần bạn tạo tài khoản và cấp "có tài khoản practice rồi", KHÔNG gửi
  token vào chat — token chỉ đặt vào `.env` trên máy theo hướng dẫn tôi gửi
  riêng (tôi không bao giờ đọc giá trị).
- Dukascopy written-consent email — chỉ nếu bạn muốn ở lại nguồn hiện tại.

## R3 — Giải phóng đĩa ≥25–40 GB (mở N7: spread census BTC/ETH + các corpus tương lai)

Đĩa hiện chỉ còn ~6.8 GB/228 GB. Ứng viên dọn an toàn (tôi kiểm tra + archive
theo P-13 trước khi xóa — bạn chỉ cần đồng ý danh mục tôi đề xuất): các
worktree TERMINAL lớn đã có evidence trên branch (pws-cx-solusdt 12 G giữ
lại data; các bản trùng), cache tarball trùng. Gợi ý: bạn phê duyệt một
"danh sách dọn" tôi sẽ đệ trình sau cycle này.

## R4 — Quyết định vendor PIT OI/liquidation/L2 cho crypto (mở O2)

Không có đường keyless. Nếu bạn muốn mở lại lớp forced-flow: tôi soạn gói
đối số kỹ thuật (symbols, độ sâu, lịch sử ≥3 năm, PIT snapshots vs
aggregates) để bạn xin quote từ 2–3 vendor (laevitas/amberdata/kaiko
class). Lưu ý: bản lưu lịch sử V14 đã mất khỏi máy (xem R7) — đây là mua
mới, không phải khôi phục. Không cam kết chi phí ở bước này.

## R5 — IEX historical tape cho stocks (chỉ khi có cơ chế cụ thể — O3/O6)

https://iexcloud.io → Historical Data. Chỉ nên làm khi một proposal đã
được preregister cần tape. Bounded slice 10–50 GB/năm + phí theo file.

## R6 — Borrow/short-fee history (O4)

Cần tài khoản broker có báo cáo securities-financing (IBKR của bạn có thể
đủ nếu có quyền short) — same statement-export pattern như R1.

## R7 — 8/14 archive trong ~/staging_backups bị mất (P-13 drift, sự cố I-1)

`~/staging_backups/SHA256SUMS.txt` liệt kê 14 tarball; đo lại chỉ còn 6.
Mất đáng kể nhất: `crypto-v14_full.tar.gz` (basis/OI/klines V14) và
`legacy_root_data.tar.gz` (oi_data 98 MB). Việc của bạn: cho tôi biết bạn
có (a) đã tự di chuyển/xóa các tarball này sang nơi khác (nếu còn: cho đường
dẫn), hay (b) chấp nhận mất — tôi sẽ ghi lại mất là vĩnh viễn và đánh giá
tái lập (CFTC/một số nguồn còn re-fetch được; V14 OI thì không).

## R8 — (Tham khảo) EODHD earnings entitlement

Không cần làm nếu chọn đường N2 (EDGAR free). Nếu vẫn muốn nâng gói EODHD
để có earnings history: https://eodhd.com — chỉ quyết định khi N2 cho thấy
thiếu dữ liệu.

---

## Thứ tự khuyến nghị (nếu chỉ làm một việc): R1.
Hai việc: +R3. Ba việc: +R2 (chọn TrueFX nếu muốn rẻ, OANDA nếu muốn nhẹ).
