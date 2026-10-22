# Gói bàn giao mô hình NCAA (bóng rổ đại học Mỹ, nam + nữ)

## Đây là gì
Toàn bộ đường ống nghiên cứu đã đóng băng: xây dữ kiện từ kết quả các trận trước đó (chỉ dùng quá khứ), điểm sức mạnh Elo, và mô hình cây (GBM) cho ra tỉ lệ thắng của đội nhà cho từng trận. Mã chính: `frozen_test.py` (đường ống đầy đủ) và `pilot_elo.py` (phần Elo).

**Lưu ý kỹ thuật quan trọng:** đây là đường ống nghiên cứu chạy theo lô trên dữ liệu lịch sử, KHÔNG phải dịch vụ dự đoán trực tiếp. Muốn dùng cho trận sắp diễn ra, agent của bạn phải tự viết lớp bọc: kéo lịch thi đấu + kết quả mới nhất, chạy lại phần xây dữ kiện đúng thứ tự thời gian, cho mô hình dự đoán. Mọi công thức nằm trong `frozen_test.py`.

## Đã chứng minh được (có kiểm toán độc lập — xem AUDIT.md)
- Dự đoán **thắng Elo thuần và mọi mô hình nền** ở cả nam và nữ, trên 3 mùa thi (2024–2026), thắng ở cả 6/6 mùa con. Kiểm toán soi rò rỉ dữ kiện: sạch, tái lập từng bit.
- Nam: mức thắng Elo ≈ +0,037 (độ đo log-loss, càng thắng nhiều càng tốt). Nữ: ≈ +0,063.

## Đã chứng minh là KHÔNG được (xem MONEY_TEST.md)
- **Nam thua thị trường.** So với giá chốt của nhà cái ESPN BET trên 11.305 trận: mô hình kém thị trường một khoảng chắc chắn về thống kê. Mô phỏng đặt cược ngay tại giá chốt (điều không thể ngoài đời) vẫn lỗ −6,2% mỗi lượt. → Đừng dùng mô hình này để đánh tiền thật theo kiểu so giá đơn thuần.
- **Nữ chưa kiểm tra được tiền bạc** — máy chủ dữ liệu odds nữ không kết nối được từ môi trường này. Giá trị tiền bạc của mô hình nữ = CHƯA BIẾT, không phải bằng 0.

## Một quan sát chưa được chứng nhận (đọc kỹ trước khi dùng)
Chia các lượt "có lời theo mô hình" theo độ lệch giữa mô hình và thị trường (tính lại từ dữ kiện của MONEY_TEST):
- Lệch 0–2%: lỗ −12,1%/lượt (n=2.738) · Lệch 2–5%: lỗ −5,2% (n=3.316) · Lệch 5–10%: lỗ −9,9% (n=3.024)
- Lệch trên 10%: **+4,5%/lượt (n=2.227)** · Lệch trên 15%: **+15,1%/lượt (n=953)**

Ba lý do vệt sáng ở nhóm lệch cực lớn CHƯA đáng tin:
1. Đó là lãi tính tại **giá chốt** — ngoài đời không mua được giá đó; nhóm lệch lớn nhất cũng là nhóm giá biến động mạnh nhất trước giờ bóng.
2. Cách khử phần lãi của nhà cái (de-vig) theo tỉ lệ đơn giản dễ **tạo ra "lệch" giả** ở các đội cửa dưới giá rất dài.
3. Vệt sáng này được **moi ra sau khi đã xem kết quả** của chính dữ kiện đã thi — theo kỷ luật của chương trình, nó chỉ xứng đáng làm giả thuyết cho một bản thiết kế MỚI, đăng ký trước, thi trên mùa giải MỚI với giá ghi lại TRƯỚC giờ chốt. Chưa phải bằng chứng để xuống tiền.

## Kỷ luật đi kèm (nếu agent của bạn tích hợp)
- Không chỉnh lại mô hình trên cùng dữ kiện 2024–2026 rồi nhận là bằng chứng mới.
- Mọi "cổng lọc" (gate) phải được định nghĩa trước bằng luật cố định, ghi lại quyết định giữ/bỏ, và chấm bằng câu hỏi duy nhất: nhóm được GIỮ có thắng được giá chốt trên dữ kiện mới không. Cổng hay đến mấy mà không qua được bài chấm đó trên giấy thì không qua được bằng tiền thật.
