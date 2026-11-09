# QUYẾT ĐỊNH CỦA COORDINATOR — 2026-11-06

Thẩm quyền: chủ ra lệnh 2026-11-06 09:22 ICT "bạn nghiên cứu rồi quyết cho tôi
luôn được không" + "sau đó đưa tôi prompt". Chủ ủy quyền quyết cho coordinator;
đây là quyết định của chủ qua ủy quyền, ghi lại để truy vết và tính chi phí hoãn lại.

Căn cứ đọc trực tiếp trên Mac (không qua tóm tắt):
- AUDIT SPEC A2 RF1 (B4-AUDITOR-GLM-2026-11-05, CONFIRMED kèm 3 điều kiện).
- NQM6_RECONCILIATION.md sha 6aa87d77… (B2).
- KE_HOACH_V2.md sha 61188913… + AUDIT_KE_HOACH_V2.md (AUDITOR-1, CONFIRMED).
- RF1 sha 204f45ce7e1588e3831f379a0008101c891dd1e43a97a06d63ec696d5cb4108a.

## A2 — 3 điều kiện của verdict B4

### 1. Kỷ nguyên: CHẤP NHẬN ~7,6 năm (phương án a)
- (b) nới cổng sau khi thấy số đếm: KHÔNG. Cổng đặt trước khi đếm; số đếm
  chính là kết quả. Nới sàn ≥200 hay nới percentile để cứu VWAPB/ICHI là
  sửa luật theo kết quả — cấm theo luật spec đóng băng.
- (c) thêm mã INDEX: KHÔNG CÓ DỮ LIỆU. Khảo sát 29/10: chỉ ES/NQ có bar;
  YM/RTY đã bỏ theo GO chủ; CL/GC chỉ có definition, không có bar.
- Hậu quả ghi nhận: phán xét 1000/sàn tới ~2034 (68 CAND-B/130 phiên =
  0,52/ngày là TRẦN; thực tế có thể chậm hơn). Deliverable tháng 01/2027
  theo đúng ranh giới đã chấp nhận: spec đóng băng + bàn chạy forward +
  bài học — không phải phán xét.

### 2. Mức "bar tín hiệu" §4.2: CAND
- §4.2 gắn excursion với vị thế mở; bar RAW bị nuốt (không mở vị thế) thì
  excursion không xác định — đo excursion của bar không thành lệnh là sai
  khái niệm sàn dừng lỗ.
- CAND cũng là lựa chọn chống hướng thuận: nó LOẠI VWAPB thay vì cứu.
- Đường tính lại trên RAW chỉ mô tả trong audit, KHÔNG CHẠY.

### 3. Cách đọc "<200 → DỪNG": theo từng generator
- Nguyên văn R3 §4.2 điểm 1 là per-generator ("Generator nào có < 200…
  generator đó không được đóng băng").
- Brief tự nó ra lệnh OUT/IN từng generator + đòi file đóng băng mới +
  hash — cơ chế OUT chỉ có nghĩa khi generator đủ điều kiện vẫn được
  đóng băng. Đọc dừng chung sẽ giết cả G-ST và mâu thuẫn brief.
- Vế NQM6 không chặn: B2 xong (xem kiểm toán bổ sung riêng).

### Bản build chính cho B5: BẢN BUILD MAC
- Cây `ai_desk_waveA2/engine/` trên Mac (B0 build) là bản chính cho B5.
  Lý do: cây này ở cùng máy với dữ liệu + freeze + audit.
- Bản build VM (32 file, 27 test, BUILD_REPORT sha fa4b70c7…) build theo
  spec BỊ ĐÌNH CHỈ (G-ST + G-ICHI), không thể làm cây live nếu không port.
  Giữ làm tham chiếu.
- B5 phải re-base đúng RF1: chỉ G-ST sinh ứng viên wave 1; G-ICHI +
  G-VWAPB KHÔNG sinh ứng viên (sàn CHƯA ĐẶT); 1 file config;
  self-test xanh; FULL BATTERY xanh ngay sau GO rồi mới bước live đầu tiên.

### GO B5: BAN HÀNH (theo ủy quyền chủ 2026-11-06)
- B5 = re-base + self-test + full battery + bước live đầu tiên.
- Kỷ nguyên bắt đầu ở bước live đầu tiên đó. A1 vẫn PAUSED/đóng, không đụng.

### NQM6
- Xem file kiểm toán bổ sung riêng:
  COORDINATOR_SUPPLEMENTARY_AUDIT_NQM6_2026-11-06.md.
- Kết luận: ĐỐI CHIẾU ĐƯỢC đứng; khoản nợ 17/06 vs 18/06 đóng về mặt dữ
  liệu (expiration ghi trong definition là 18/06/2026 13:30 UTC, thứ Năm).

## Trần request Polymarket — phán quyết về phạm vi
- Trần 200 request/ngày là CỘNG DỒN mọi tiến trình (theo spec v2 đóng
  băng), tính cả worker WSL.
- Ngày 05/11 tổng 222 (Việc 3: 200 + WSL: 22) — ghi nhận là vượt trần 1
  lần, không truy cứu ngược. Từ nay preflight phải đếm đủ 3 nguồn (Việc 3,
  worker WSL, lane này) và KHÔNG chạy khi thiếu bằng chứng.

## Ví pro — GĐ4

### Ngưỡng CHỐT (đúng số đề xuất trong KE_HOACH_V2)
- NBA: ≥30 lệnh/6 tháng + ≥5.000 USD tiền đặt; bóng đá nam: ≥30 + ≥5.000
  USD; WSL: ≥15 + ≥1.000 USD; lãi ròng dương giữ-tới-chốt; tối đa 30 ví/giải.
- Ý kiến: ≥3 ví cùng phía + ≥60% tiền pro phía đó.
- Trần lane: 120 request/ngày; tổng mọi nguồn ≤200.
- Phán xét: ≥30 trận có ý kiến pro MỖI GIẢI; kịch bản "theo pro"
  100 USD/trận @ VWAP fill pro; tiền fill = price × size.
- Sổ bóng tại `.my-quantitative-data/PRO-WALLET-V1/shadow/`.

### N1–N5 (xử lý bằng chữ, KHÔNG sửa file KE_HOACH_V2.md đã kiểm toán)
- N1: dòng ước ngân sách sửa thành "29–139 (thành phần), thường ~40–110
  nếu bóng đá ~2 request/trận".
- N2: tách trích dẫn NBA thành 2 nguồn riêng (mem-uta chứng minh tồn tại
  thị trường trận đơn; mẫu 23 ví trên sas-dal).
- N3: thêm BAN_DRAW vào enum quyet_dinh_ban.
- N4: ghi errata — journal WSL đếm lại 394 file (GĐ1 ghi 395).
- N5: paper_pnl_usd thuộc kịch bản "theo pro"; kịch bản "bàn đơn thuần"
  đọc từ sổ D2 lúc chấm.
- File KE_HOACH_V2.md giữ nguyên từng byte (hash 61188913…); các xử lý
  trên sống trong quyết định này + báo cáo GĐ4, collector áp dụng trực tiếp.

### F2: (a) XẾP HÀNG sau Việc 3 (~08–09/11)
- Việc 3 cần đủ 200/ngày để xong trong ~3 ngày; chia trần làm chậm cả 2 bên.
- Tháng chạy bóng chưa bắt đầu (T_freeze gắn trước thu thập) nên chờ 2–3
  ngày không mất gì.

### GO GĐ4: BAN HÀNH (theo ủy quyền chủ 2026-11-06)
- GĐ4a preflight đếm mô tả trước; nếu ước ≤120 request/ngày VÀ cửa sổ
  chọn ≤14 ngày thì chạy tiếp GĐ4b; vượt thì DỪNG và báo chủ duyệt ngân sách.
- Thu thập chỉ sau khi Việc 3 xong (bằng chứng: interim log ghi xong).
- GĐ7 vẫn CẤM. GĐ5 kiểm toán dữ liệu vẫn cần agent khác sau GĐ4.

## Hậu quả hoãn lại / ghi nhận
- B5 kích hoạt bàn A2 lần đầu: A1 không bị ảnh hưởng; kỷ nguyên A2 bắt đầu
  ở bước live đầu tiên.
- 2 prompt thi hành đính kèm trong thư chủ ngày 2026-11-06:
  MAC_AGENT_PROMPT_A2_B5_GO_2026-11-06.md,
  MAC_AGENT_PROMPT_PRO_WALLET_GD4_GO_2026-11-06.md.

Ký: coordinator — 2026-11-06
