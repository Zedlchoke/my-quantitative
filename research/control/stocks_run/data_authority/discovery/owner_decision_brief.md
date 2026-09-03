# BRIEF QUYẾT ĐỊNH CHO OWNER — tìm nhà cung cấp dữ liệu Stocks (DA0)

> Ngày tra cứu: 2026-09-03 UTC. Chỉ dùng nguồn chính thức của nhà cung cấp.
> **Không có nhà cung cấp nào được tuyên bố đã qua kiểm định ingestion** — mọi
> verdict R01–R19 trong factory vẫn `UNAVAILABLE_FAIL_CLOSED`. Không có giao
> dịch, đăng ký hay tải dữ liệu nào được thực hiện trong DA0.

## 1. Kết luận ngắn

- **Family F1 (`EQ_S2_A3_F1_PIT_RECON_FLOW`) có lộ trình khả thi cho cá nhân**
  nhờ Norgate Data (Platinum/Diamond) — nhà bán lẻ duy nhất được tìm thấy có
  tài liệu chính thức về **historical index constituents** (S&P 500 từ 1957,
  NDX 1993, Russell 1990) kèm cổ phiếu đã delist (25.222 mã từ 1950).
- **Family F2 (`A5-S2-F1-LENDING-CONSTRAINT-PREMIUM`) CHƯA CÓ LỘ TRÌNH** cho
  cá nhân: dữ liệu lịch sử borrow fee / utilization / recalls chỉ có ở cấp
  tổ chức (S3 Partners, FIS Astec, S&P Global MI — đều CONTACT_SALES). Ortex
  bán lẻ nhưng là **mô hình ước lượng**, đã bị loại (`NOT_SUITABLE`) làm bằng
  chứng authority. → F2 vẫn `BLOCKED_DATA_AUTHORITY`.
- Khoảng trống F1 còn lại: **R06** (timestamp công bố vs hiệu lực của thay đổi
  index) — không vendor bán lẻ nào có; nguồn chính thức duy nhất là thông cáo
  báo chí của chính S&P DJI (miễn phí nhưng phải tự trích dẫn và lưu trữ có
  kiểm soát).

## 2. Stack đề xuất theo ngân sách

| Stack | Thành phần | Chi phí công khai ước tính | F1 | F2 |
|---|---|---|---|---|
| **S-CHEAP-F1** (rẻ nhất khả dĩ) | Norgate Platinum + archive thông cáo S&P DJI (tự lập) + SPY NAV/dividend chính thức (SSGA) + FINRA short interest | Norgate **chưa chốt giá** (calculator động; snapshot tìm kiếm: Diamond USD 787.50/12 tháng; Platinum thường thấp hơn) + ~0 USD | **ĐỦ** | Không |
| **S-RESEARCH** (chất lượng nghiên cứu) | S-CHEAP-F1 + Massive (ex-Polygon) Advanced 20+năm trades/quotes | Norgate + **USD 1.908/năm** (199×12×0.8) | **MẠNH** | Không |
| **S-INSTITUTIONAL** (tham chiếu) | CRSP/WRDS + feed index S&P DJI thương mại + S3/Astec/S&P MI borrow + price vendor | CONTACT_SALES toàn bộ | Đủ | **Đủ** — lộ trình duy nhất thấy được cho R11/R12 |

## 3. Cá nhân tại Việt Nam có đủ điều kiện không?

- **Norgate / Massive / Sharadar**: đăng ký cá nhân tự phục vụ; **không có
  trang tài liệu nào ghi cấm theo quốc gia**. Thanh toán: Norgate qua
  chuyển khoản USD wire/ACH (Việt Nam wire được về nguyên tắc nhưng **chưa
  xác thực**); Massive/NDL qua thẻ (thẻ VN **chưa xác thực**). → xếp
  "không có rào cản được ghi nhận; khả thi thanh toán từ VN chưa kiểm chứng".
- **Massive Advanced** ghi chú "non-pros only" — cá nhân nghiên cứu thường
  thuộc diện đủ, nhưng cần xác nhận nghĩa vụ hội viên.
- **S3 / Astec / S&P MI / CRSP**: quy trình tổ chức; cá nhân VN gần như không
  đủ điều kiện trừ khi có affiliation học thuật (CRSP/WRDS) hoặc lập pháp nhân.

## 4. Việc còn chưa biết (chặn quyết định mua)

1. Giá Platinum Norgate chính xác (VQ-N1).
2. Điều khoản license: lưu trữ cục bộ, dẫn xuất, commit checksum (VQ-N4,
   VQ-M3, VQ-S4) — bắt buộc trước mọi giao dịch (R18).
3. Chính sách revision/vintage của mọi vendor (VQ-N3, VQ-M4) — R14 gần như
   chưa vendor nào công bố.
4. Độ sâu bản archive thông cáo S&P DJI dạng máy đọc được + license lưu trữ
   curated (VQ-I1/I2).
5. Borrow: mức hợp đồng tối thiểu, độ sâu lịch sử, recall/accrual docs,
   eligibility cá nhân/VN (VQ-B1…B6).

## 5. Hành động tiếp theo chính xác cho owner

1. **Nếu muốn mở khóa F1 trước** (khuyến nghị): liên hệ Norgate với bộ câu hỏi
   `vendor_questions.md` (VQ-N1…N6), yêu cầu file mẫu delisted + constituents;
   đồng thời xác nhận khả năng thanh toán USD từ VN. Nếu đạt → mua **Platinum**
   (không cần Diamond trừ khi muốn 1950+), đi theo
   `ingestion_acceptance_checklist.md`.
2. **Nếu muốn F2**: chỉ có đường tổ chức — cân nhắc liên hệ S3 Partners
   (S3.Sales@s3partners.com) hoặc FIS Astec với VQ-B1…B6 để hỏi eligibility cá
   nhân/tổ chức nhỏ TRƯỚC KHI quyết định anything khác; nếu không khả thi,
   chốt F2 `BLOCKED_PRE_SCORE` (giữ 3 slot budget không dùng, không thay thế).
3. **Dù stack nào**: điền `provider_evaluation_template.json` bằng bằng chứng,
   chạy checklist ingestion, và chỉ khi mọi R cần thiết = PASS (có evidence
   path) thì S0/S1 window mới được freeze và S4 mới được dispatch.
4. Không mua gói nào trước khi VQ-N4/VQ-M3 (license lưu trữ) được trả lời bằng
   văn bản.

## 6. Phủ sóng R01–R19 (tóm tắt)

- Đã có candidate được tài liệu hóa: R02, R13, R15, R16 (Norgate); R05, R08,
  R09, R10 (Massive + SSGA); R01/R03/R04/R07 (Norgate/Massive/Sharadar, độ
  chắc khác nhau).
- Đường DIY chính thức: R06 (S&P DJI), R10 (SSGA).
- **Không có candidate khả dĩ cho cá nhân**: R11, R12 (borrow history).
- Mở câu hỏi toàn ngành: R14 (vintage), R17 (immutable snapshot guarantees),
  một phần R18/R19.
