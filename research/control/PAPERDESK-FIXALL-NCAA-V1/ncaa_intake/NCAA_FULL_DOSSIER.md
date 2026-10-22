# HỒ SƠ ĐẦY ĐỦ — MÔ HÌNH NCAA + THIẾT KẾ AI ORCHESTRATOR KIỂM DUYỆT LỆNH

Ngày tổng hợp: 21/10/2026. Mọi con số trong file này đều lấy từ các bài chạy đã đóng băng và đã qua kiểm toán độc lập (xem mục 4 và 5). Mã nguồn nằm trong thư mục `ncaa-model-handoff/` đi kèm.

---

## 0. PHÁN QUYẾT TÓM TẮT (đọc trước)

- **Dự đoán: SỐNG — đã kiểm toán, chính thức.** Mô hình đoán thắng/thua giỏi hơn hẳn các mô hình nền, ở cả nam và nữ, 3 mùa liên tiếp.
- **Kiếm tiền (nam): CHẾT — đã kiểm toán, chính thức.** So với giá chốt của nhà cái, mô hình thua rõ ràng. Đặt cược mô phỏng ngay tại giá chốt (điều không thể ngoài đời) vẫn lỗ −6,2%/lượt.
- **Kiếm tiền (nữ): CHƯA BIẾT.** Máy chủ chứa odds nữ không kết nối được từ môi trường chạy test. Không có kết luận nào về tiền bạc cho nữ.
- **Hệ quả cho orchestrator:** theo đúng thiết kế ở mục 7, mô hình NCAA hiện **chỉ được phép chạy trên giấy (paper)**. Nó chưa qua được cổng tiếp nhận để ra lệnh thật. Đây là kết luận của chính dữ kiện, không phải ý kiến.

---

## 1. MÔ HÌNH LÀM NHƯ THẾ NÀO

### 1.1 Dữ liệu đầu vào
- Lịch thi đấu + tỉ số bóng rổ đại học Mỹ hạng 1 (Division 1), nam và nữ, từ bản phát hành dữ liệu ESPN qua sportsdataverse, các mùa 2016–2026. Chỉ lấy trận hai đội đều có mã giải đấu (đúng nghĩa D1 đấu D1), đã đấu xong, không hòa.
- Mọi dữ kiện của một trận đều được tính từ các trận **diễn ra trước nó**. Không có bất kỳ thông tin nào của tương lai hay cuối mùa bị trộn vào — đây là nguyên tắc sống còn của toàn bộ chương trình, và kiểm toán đã xác nhận sạch (mục 4).

### 1.2 Ba lớp mô hình đấu nhau
1. **Mức ngây thơ (chuẩn sàn):** luôn đoán "đội nhà thắng với tỉ lệ cố định" lấy từ các mùa trước (nam ≈ 64%, nữ ≈ 60,7%).
2. **Elo thuần (chuẩn giữa):** mỗi đội một điểm sức mạnh, cập nhật sau từng trận.
3. **Mô hình cây GBM (kẻ thách đấu — và là kẻ thắng):** ăn Elo + hiệu suất ghi điểm đã chỉnh theo đối thủ + ngữ cảnh trận đấu.

### 1.3 Elo — thông số đã đóng băng
- Điểm khởi đầu đội mới: **1500**. Hệ số cập nhật **K = 20**.
- Lợi thế sân nhà: **+65 điểm Elo** (sân trung lập = 0).
- Giữa hai mùa: mọi điểm số bị kéo **25% về 1500** (đội mạnh yếu lại một phần vì sinh viên ra trường).
- Tỉ lệ thắng từ chênh lệch Elo: công thức logistic cơ số 10, thang 400.

### 1.4 Hiệu suất ghi điểm đã chỉnh (phần "khôn" hơn Elo)
Chạy song song với Elo trong cùng một vòng lặp theo thời gian:
- Mỗi đội có hai chỉ số: **tấn công** (ghi nhiều hơn mức trung bình bao nhiêu điểm) và **phòng ngự** (để đối thủ ghi ít hơn bao nhiêu), khởi đầu = 0.
- Dự đoán điểm của đội nhà = mức ghi điểm trung bình toàn giải (mở rộng dần theo thời gian, khởi đầu 70) + tấn công đội nhà + phòng ngự đội khách + **3,2 điểm sân nhà** (sân trung lập = 0).
- Sau mỗi trận, hai chỉ số được nhích theo sai số dự đoán với bước **0,06**. Giữa mùa: kéo 25% về 0, cùng lúc với Elo.
- *Ghi nhận sai lệch duy nhất so với thiết kế gốc:* hiệu suất tính theo **điểm số** (points space) thay vì theo **lượt bóng** (per-possession), vì nguồn ESPN không có dữ liệu từng lượt bóng. Kiểm toán xác nhận sai lệch này làm mô hình **yếu đi**, không phải mạnh lên — kết quả đậu bất chấp nó.

### 1.5 Tám dữ kiện đầu vào của GBM (đã đóng băng)
1. `elo_diff` — chênh lệch Elo (đã gồm điểm sân nhà).
2. `eff_margin` — chênh lệch điểm dự đoán từ lớp hiệu suất (đội nhà − đội khách).
3. `net_diff` — chênh lệch (tấn công − phòng ngự) giữa hai đội.
4. `rest_h`, 5. `rest_a` — số ngày nghỉ của mỗi đội (trận đầu tiên tính 10; trần 30).
6. `rest_diff` — hiệu số ngày nghỉ.
7. `conf_game` — hai đội cùng bảng đấu hay không (0/1).
8. `neutral` — sân trung lập hay không (0/1).

### 1.6 GBM — thông số đã đóng băng
- Thuật toán: `HistGradientBoostingClassifier` (thư viện scikit-learn), **để nguyên mọi cài đặt mặc định**, `random_state=0`, **không tinh chỉnh gì cả**. Việc "không tinh chỉnh" là cố ý: tránh khớp quá mức vào quá khứ.
- Cách huấn luyện theo mùa: để thi mùa Y, mô hình chỉ học từ các trận mùa thường của các mùa **trước Y**. Hệ số của GBM cố định trong suốt mùa Y; còn Elo và hiệu suất thì cập nhật sau từng trận ngay trong mùa.

### 1.7 Cách chấm thi (giao thức)
- Chỉ chấm trên **mùa thường** (regular season), ba mùa thi: **2024, 2025, 2026** — ba mùa hoàn chỉnh gần nhất tại thời điểm chạy. Mỗi mùa là một bài thi đi tới (walk-forward): không mùa nào được học từ chính nó.
- Thang đo chính: **log loss** — phạt nặng những lần tự tin sai (đoán 90% mà thua thì bị phạt rất nặng). Phụ: Brier score và tỉ lệ đoán trúng.
- Ngoài ra có "sân khấu giải cuối mùa" (tournament): so GBM với cách đoán theo hạt giống (seed) bằng Brier score.

---

## 2. KẾT QUẢ BACKTEST — DỰ ĐOÁN

### 2.1 Nam (mùa thường)
| Mùa | Số trận | Elo | GBM | Ngây thơ | Đoán trúng GBM |
|---|---|---|---|---|---|
| 2024 | 5.606 | 0,5756 | 0,5446 | 0,6539 | 71,9% |
| 2025 | 5.641 | 0,5710 | 0,5301 | 0,6516 | 72,3% |
| 2026 | 5.647 | 0,5726 | 0,5333 | 0,6554 | 71,5% |
| **Gộp** | **16.894** | **0,5731** | **0,5360** | **0,6536** | **71,9%** |

(Số là log loss — **càng nhỏ càng tốt**.)

Vạch giết đã đăng ký trước: GBM phải thắng Elo trung bình ≥ 0,005 và không thua 2/3 mùa → thực tế **+0,0371, thắng cả 3 mùa**. Mô hình tốt nhất phải thắng mức ngây thơ ≥ 0,03 → thực tế **0,1177**. Đậu với khoảng cách xa.

### 2.2 Nữ (mùa thường)
| Mùa | Số trận | Elo | GBM | Ngây thơ | Đoán trúng GBM |
|---|---|---|---|---|---|
| 2024 | 5.395 | 0,5389 | 0,4785 | 0,6705 | 76,4% |
| 2025 | 5.160 | 0,5276 | 0,4661 | 0,6715 | 75,9% |
| 2026 | 5.480 | 0,5360 | 0,4696 | 0,6745 | 75,9% |
| **Gộp** | **16.035** | **0,5343** | **0,4715** | **0,6722** | **76,1%** |

Vạch giết: thắng Elo ≥ 0,005 → thực tế **+0,0628, thắng cả 3 mùa**. Thắng ngây thơ ≥ 0,03 → thực tế **0,2008**. Đậu xa.

### 2.3 Giải cuối mùa (tournament, 201 trận mỗi giới, gộp 2024–2026)
Chấm bằng Brier (nhỏ = tốt), đối thủ là cách đoán theo hạt giống:
- Nam: GBM **0,1711** thắng hạt giống 0,1765 (thắng 2/3 năm; cách biệt mỏng — ghi nhận là mỏng).
- Nữ: GBM **0,1110** thắng hạt giống 0,1266 (thắng cả 3 năm).
- Elo thuần **thua** cách đoán hạt giống ở cả hai giới → Elo không được nhận tuyên bố nào về giải cuối mùa. Tuyên bố tournament chỉ thuộc về lớp GBM.

---

## 3. KẾT QUẢ BACKTEST — TIỀN BẠC (chỉ nam; nữ chưa chạy được)

### 3.1 Cách làm
- Key dữ liệu CollegeBasketballData do chủ tài khoản tự đăng ký (miễn phí) và bàn giao. Nguồn này ghi rõ nhà cái cho từng trận, có giá cuối (giá chốt) cho cược thắng/thua và giá mở cho cược chấp điểm.
- Đếm nhà cái **trước khi tính**: ESPN BET đầy đủ nhất (12.007 bản ghi trận; 11.536 có giá hai phía), tiếp theo Bovada (4.952), DraftKings (4.505). Luật chạy đã định sẵn: dùng **một nhà cái đầy đủ nhất** → ESPN BET. Không chọn nhà cái theo kết quả.
- Ghép với dự đoán đã đóng băng: khớp tên đội 100% (4 trường hợp đổi tên trường được lập danh sách căn cứ rõ ràng), 16.863/16.894 trận có trong kho, **11.305 trận có giá chốt hai phía** (66,9%). Kiểm tra tỉ số chéo trên mọi trận đã ghép: **0 sai lệch**.
- Giá thị trường được khử phần lãi nhà cái (de-vig): hai tỉ lệ cược → tỉ lệ thắng thị trường, chuẩn hóa tổng = 1. Mức lãi nhà cái điển hình (trung vị overround) ≈ 1,040.
- **Cổng tiền bạc đã đăng ký trước (REPORT §5.4):** mô hình phải thắng thị trường ở thang log loss với độ chắc chắn thống kê t ≥ +3,2 và số trận có giá ≥ 1.000.

### 3.2 Kết quả (gộp 11.305 trận)
| | Log loss | Chênh vs thị trường | Độ chắc chắn (t) |
|---|---|---|---|
| Thị trường (giá chốt ESPN BET) | 0,5236 | — | — |
| GBM (mô hình của ta) | 0,5377 | **−0,0141 (thua)** | **−7,00** |
| Elo thuần (tham chiếu) | 0,5761 | −0,0525 | −21,70 |

Theo mùa: 2024 thua −0,0162 (t = −6,09); 2025 thua −0,0168 (t = −6,31); 2026 (chỉ đầu mùa, kho giá dừng ở 02/12/2025) thắng +0,0121 nhưng t = +0,99 — xa vạch +3,2. **Cổng: RỚT.** Kết luận: thị trường không bị đánh bại.

### 3.3 Mô phỏng đặt cược tại giá chốt (trần trên lý thuyết)
Cho đặt cược đúng giá chốt — điều ngoài đời không ai làm được — chọn phía mô hình cho là có lời:
- GBM: 11.305 lượt, **−6,2% mỗi lượt**. Elo: **−12,8% mỗi lượt**.
- Nghĩa là: thua không phải vì vào lệnh chậm. Thua vì dự đoán chưa hơn thị trường.

### 3.4 Nữ — bị chặn, không có số
Máy chủ `api.collegewomensbasketballdata.com` không kết nối được từ môi trường này (thử ~25 lần, rớt toàn bộ; máy chủ nam chạy bình thường qua cùng đường truyền; kiểm toán đã thử lại độc lập và xác nhận y hệt). Quy trình nữ giống hệt nam, chạy được ngay khi có môi trường kết nối tới máy chủ đó. **Hiện tại: THIẾU DỮ LIỆU.**

### 3.5 Chẩn đoán lệch giá (hậu kiểm — KHÔNG phải bằng chứng, đọc kỹ cảnh báo)
Chia các lượt theo độ lệch giữa xác suất mô hình và xác suất thị trường (điểm %):

| Độ lệch | Số lượt | Kết quả/lượt tại giá chốt |
|---|---|---|
| 0–2% | 2.738 | −12,1% |
| 2–5% | 3.316 | −5,2% |
| 5–10% | 3.024 | −9,9% |
| trên 10% | 2.227 | **+4,5%** |
| trên 15% | 953 | **+15,1%** |

Ba cảnh báo bắt buộc:
1. Đây là lãi tại **giá chốt** — giá không mua được ngoài đời. Nhóm lệch lớn nhất cũng là nhóm giá biến động mạnh nhất trước giờ đấu.
2. Cách khử lãi nhà cái theo tỉ lệ đơn giản dễ **tạo "lệch" giả** ở đội cửa dưới giá rất dài (hiệu ứng favourite–longshot).
3. Bảng này được moi ra **sau khi đã xem kết quả** của chính dữ kiện đã thi. Theo kỷ luật chương trình: nó chỉ là **giả thuyết cho một bản thiết kế mới đăng ký trước**, thi trên mùa mới với giá ghi lại trước giờ chốt. Không phải giấy phép xuống tiền.

---

## 4. KIỂM TOÁN BÀI DỰ ĐOÁN — CONFIRMED (đã chính thức)

Kiểm toán độc lập được xây dựng như một cuộc săn rò rỉ (vì đây là phán quyết "sống" đầu tiên của chương trình):
- Tự tay tính lại dữ kiện của 12 trận mẫu từ dữ liệu thô, chỉ dùng các trận trước đó: **sai số 0,00000 trên mọi dữ kiện**.
- Viết lại toàn bộ đường ống độc lập: khớp **từng bit** trên 117.306 trận (xác suất Elo, cả 8 dữ kiện, kết quả).
- Hằng số Elo, luật hồi quy, luật chỉ-học-mùa-trước: khớp thiết kế từng chi tiết. Dữ liệu tái tạo sạch từ bản phát hành ESPN gốc.
- Mức thắng tái lập: nam +0,0372, nữ +0,0624 — mọi vạch giết đều đậu xa.
- Nhận định cơ chế: mô hình thắng vì nó nhìn được **cách biệt điểm và hiệu suất ghi điểm đã chỉnh đối thủ** — thứ Elo thắng/thua thuần không có. Thắng lợi là có thật và giải thích được, không cần gian lận.

## 5. KIỂM TOÁN BÀI TIỀN BẠC — CONFIRMED (đã chính thức)

- Toán của cổng tái lập **đến chữ số cuối** từ file ghép của đội chạy, và gần như y hệt từ một phép ghép độc lập hoàn toàn (ghép theo mã đội thay vì tên): n = 11.335, chênh −0,0140, t = −6,97.
- Một lỗi nhỏ được tìm thấy: đội chạy bỏ sót một trường hợp đổi tên trường (Texas A&M–Commerce → East Texas A&M), làm rơi 30 trận có giá. Cộng lại 30 trận đó: kết quả **không đổi** (vẫn thua −0,0140). Lỗi thật nhưng không lật phán quyết. Dòng chữ "khớp tên 100%" trong báo cáo gốc là sai vì lỗi này — cần sửa văn bản, không cần chạy lại.
- Thiên lệch mẫu: **không có**. Nhóm trận có giá còn hơi *khó hơn* trung bình cho mô hình (+0,0017 log loss so với toàn bộ) — nhỏ hơn khoảng thua thị trường 10 lần. Cái thua là tính chất của phép so sánh cặp, không phải do mẫu.
- Độ bền theo nhà cái (chẩn đoán, không phải chạy lại cổng): mô hình thua **cả ba** giá chốt — ESPN BET (t = −7,00), Bovada (chênh −0,0097, t = −3,06, n = 4.445), DraftKings (chênh −0,0089, t = −1,84, n = 1.524). Không tồn tại cách chọn nhà cái nào cứu được.
- Kết luận kiểm toán: với bản thiết kế này, câu hỏi tiền bạc của nam là **tịt hẳn**. Đường hồi sinh duy nhất: bản thiết kế MỚI đăng ký trước (ví dụ mô hình theo lượt bóng trên mùa mới, hoặc giá ghi kèm mốc thời gian để đo được CLV). Nữ: chỉ bị chặn bởi một máy chủ không tới được.

---

## 6. CÁCH TÍCH HỢP (cho agent của bạn)

### 6.1 Bản chất thứ được bàn giao
`frozen_test.py` là đường ống nghiên cứu chạy theo lô trên dữ liệu lịch sử — **không phải** dịch vụ trực tuyến. Muốn dự đoán trận sắp đấu, cần viết lớp bọc vận hành quanh nó (mục 6.2). Toàn bộ công thức nằm trong file đó; `pilot_elo.py` chứa phần Elo rút gọn.

### 6.2 Công thức lớp bọc dự đoán hằng ngày
1. **Kéo dữ liệu:** lịch đấu + tỉ số mới nhất (ESPN qua sportsdataverse, hoặc CBBD bằng key của bạn). Cần cho mỗi trận: ngày, mã đội nhà/khách, tỉ số, sân trung lập hay không, mã bảng đấu của hai đội.
2. **Chạy lại vòng lặp thời gian** (`walk_forward` trong `frozen_test.py`) trên toàn bộ các trận đã xong từ 2016 tới hiện tại, theo đúng thứ tự ngày. Trạng thái cuối vòng lặp = điểm Elo, chỉ số tấn công/phòng ngự, ngày đấu gần nhất của từng đội, mức ghi điểm trung bình toàn giải. **Không được tắt vòng lặp này hay thay bằng ảnh chụp cuối mùa** — dữ kiện chỉ hợp lệ khi được xây đúng thứ tự thời gian.
3. **Huấn luyện GBM** trên các trận mùa thường của các mùa đã hoàn tất (luật đóng băng: mùa < mùa hiện tại), 8 dữ kiện ở mục 1.5, cài đặt mặc định, `random_state=0`. Huấn luyện lại mỗi khi một mùa mới bắt đầu (không phải mỗi ngày).
4. **Dự đoán các trận hôm nay:** xây dữ kiện tiền trận từ trạng thái ở bước 2 (Elo/hiệu suất/ngày nghỉ lấy tại thời điểm trước trận), cho qua GBM → xác suất đội nhà thắng.
5. **Hợp đồng đầu ra** (đề xuất): một bản ghi JSON cho mỗi trận —
   `{"date", "league": "ncaab_men|ncaab_women", "home_id", "away_id", "p_home_model", "p_home_elo", "features": {...8 dữ kiện...}, "model_version": "ncaa-frozen-v1", "trained_through_season": Y, "generated_at": timestamp}`.
   Orchestrator (mục 7) tiêu thụ đúng bản ghi này cộng với giá thị trường tại thời điểm quyết định.

### 6.3 Những chỗ dễ gãy khi tích hợp
- **Mã đội và đổi tên trường:** các nguồn khác nhau gọi cùng một trường khác nhau (ví dụ IUPUI → IU Indianapolis; Texas A&M–Commerce → East Texas A&M). Phải có bảng ánh xạ mã đội duy nhất, và mọi trường hợp lệch tên phải được ghi lại — một lỗi ánh xạ thầm lặng từng làm rơi 30 trận trong bài tiền bạc.
- **Cờ sân trung lập và mã bảng đấu** ảnh hưởng trực tiếp tới 3/8 dữ kiện; thiếu chúng thì đừng dự đoán trận đó.
- **Giờ và múi giờ:** ngày trận theo giờ Mỹ; lệch một ngày làm hỏng dữ kiện ngày nghỉ và thứ tự vòng lặp.
- **Đừng "cải tiến" lặng lẽ:** bất kỳ thay đổi nào về dữ kiện, thông số, hay cách huấn luyện đều biến v1 thành một mô hình khác chưa được kiểm chứng. Muốn đổi → bản thiết kế v2 đăng ký trước, thi trên dữ kiện mới.

---

## 7. THIẾT KẾ AI ORCHESTRATOR KIỂM DUYỆT LỆNH (bản tôi cho là tốt)

### 7.1 Triết lý — ba điều phải tin trước khi xây
1. **Orchestrator không tạo ra lợi thế. Nó là hệ thống NÓI KHÔNG.** Việc của nó là chặn lệnh xấu, giới hạn thiệt hại, và ghi lại mọi thứ để chấm điểm. Một orchestrator "thông minh" đến mấy cũng không biến một mô hình thua thị trường thành thắng thị trường — bằng chứng nằm ở mục 3: mô hình NCAA đoán giỏi thật, qua cổng lọc nào thì vẫn mang cái thua −0,014 log-loss đó theo.
2. **Mặc định = TỪ CHỐI.** Lệnh chỉ đi tiếp khi mọi lớp đều cho qua. Bất kỳ tín hiệu nào thiếu, cũ, hoặc không chắc → từ chối. "Không rõ" là một câu trả lời hoàn chỉnh.
3. **Chính orchestrator cũng phải thi.** Cổng lọc là một giả thuyết như mọi giả thuyết khác: nó chỉ đúng nếu **nhóm lệnh được GIỮ thắng được giá chốt trên dữ kiện mới**. Không đo được điều đó thì cổng chỉ là nghi lễ.

### 7.2 Lớp 0 — Tiếp nhận mô hình (cổng quan trọng nhất, chạy một lần cho mỗi mô hình)
Một mô hình chỉ được orchestrator xét lệnh khi có đủ cả ba:
- (a) Bản thiết kế đóng băng viết trước khi thi (dữ kiện, thông số, vạch đậu/rớt).
- (b) Kết quả thi trên dữ kiện chưa từng đụng vào + kiểm toán độc lập đạt (đúng thiết kế, không rò rỉ).
- (c) **Bài kiểm tra tiền bạc trên dữ kiện mới:** nhóm lệnh mô hình đề xuất phải thắng giá chốt của một nhà cái có tên tuổi, với độ chắc chắn thống kê đặt trước (khung tham chiếu đã dùng ở đây: t ≥ 3,2 trên ≥ 1.000 trận có giá).
Không đủ (c) → mô hình ở chế độ **PAPER vĩnh viễn** cho tới khi đủ. *Áp dụng ngay:* mô hình NCAA nam rớt (c) với t = −7,00 → **PAPER**. Mô hình NCAA nữ chưa có (c) → **PAPER**. Đây không phải sự cố — đây là hệ thống hoạt động đúng.

### 7.3 Lớp 1 — Kiểm tra tất định (mã cứng, KHÔNG có AI)
Chạy cho từng lệnh đề xuất; rớt một ô là chết:
1. **Độ tươi của dữ kiện:** trạng thái mô hình (Elo/hiệu suất) cập nhật tới trận gần nhất chưa; lịch đấu/đội hình có thay đổi sau khi mô hình chạy không. Cũ → từ chối.
2. **Giá so với giá tham chiếu:** giá bạn sắp lấy phải không tệ hơn giá của nhà cái tham chiếu sắc bén (hoặc giá đồng thuận nhiều nhà cái) quá một ngưỡng cố định. Thị trường đích (ví dụ một sàn dự đoán) mỏng và lệch giá thường xuyên — lấy giá tệ hơn tham chiếu là tự nộp tiền.
3. **Ngưỡng lệch tối thiểu:** chỉ xét lệnh khi mô hình và thị trường lệch nhau **rất lớn** (bằng chứng mục 3.5: lệch nhỏ và vừa là vùng lỗ nặng nhất, −5% đến −12%/lượt; chỉ vùng lệch cực lớn mới có tia sáng — và tia sáng đó vẫn chưa được chứng nhận). Ngưỡng cụ thể phải là một phần của bản thiết kế đăng ký trước, không chỉnh theo cảm tính.
4. **Thanh khoản tối thiểu** tại mức giá định lấy.
5. **Trần rủi ro:** tối đa cho một lệnh, một trận, một ngày, và tổng các lệnh tương quan (cùng một đội, cùng một giải). Vốn cho một lệnh tính theo phân số cố định nhỏ của ngân quỹ; không tăng tay sau thua.
6. **Công tắc giết (kill-switch):** sụt vốn lũy kế chạm ngưỡng đặt trước → dừng toàn bộ, chuyển PAPER. Mất nguồn dữ liệu giá hoặc dữ liệu trận → dừng. Độ lệch hành vi của mô hình (phân phối xác suất gần đây khác hẳn thời kỳ thi) → dừng và báo người.

### 7.4 Lớp 2 — AI xét duyệt (CHỈ ĐƯỢC PHÉP CẤM — veto-only)
Đây là chỗ duy nhất có AI, và nó bị xích chặt:
- **Quyền:** chỉ được (i) **cấm** một lệnh đã qua Lớp 1, hoặc (ii) **giảm** cỡ lệnh. **Không bao giờ** được tạo lệnh mới, **không bao giờ** được tăng cỡ, **không bao giờ** được lật một lệnh bị Lớp 1 chặn.
- **Việc của nó:** đọc ngữ cảnh mà mô hình số không thấy — tin chấn thương, đội hình ra sân, cầu thủ bị treo giò, thay đổi huấn luyện viên, thời tiết (môn ngoài trời), tin đồn đã kiểm chứng nguồn — và trả lời một câu duy nhất: "có lý do cụ thể nào để KHÔNG đánh lệnh này không?"
- **Đầu ra bắt buộc:** `{"decision": "allow|veto", "reason_code": "...", "note": "<tối đa 2 câu, dẫn nguồn>", "confidence": "low|medium|high"}`. Thiếu trường, thiếu nguồn, hoặc `confidence = low` → coi như **veto**. Câu chữ của AI được lưu nguyên văn vào log.
- **Vì sao xích chặt như vậy:** phán đoán từng trận của AI là thứ chưa ai kiểm chứng được ở bất kỳ đâu trong chương trình này. Cho nó quyền *tạo* lệnh là trao tiền cho một giả thuyết chưa thi. Cho nó quyền *cấm* thì rủi ro của nó bị chặn ở mức "bỏ lỡ một lệnh" — và giá trị của nó đo được (mục 7.5).
- Cài đặt gợi ý: nhiệt độ (temperature) thấp nhất có thể, cùng một mẫu prompt đóng băng theo phiên bản, cấm AI tự ý đổi mẫu prompt — đổi prompt = đổi mô hình = phải thi lại trên giấy.

### 7.5 Lớp 3 — Ghi log và tự chấm (phần làm cho cả hệ thống đáng tin)
Mỗi đề xuất lệnh — được giữ hay bị cấm, ở lớp nào — đều ghi một dòng bất biến:
`{thời gian, mô hình + phiên bản, trận, xác suất mô hình, giá tại thời điểm quyết định, giá tham chiếu, quyết định từng lớp + lý do, cỡ lệnh, giá chốt cuối cùng, kết quả trận}`.
Từ log này, chấm hằng tuần (trên giấy cho tới khi qua cổng thăng cấp):
- **CLV (giá trị so với giá chốt):** giá mình lấy (hoặc sẽ lấy) so với giá chốt — trung bình phải dương và thắng rõ ràng mới là có lợi thế thật. *Muốn có CLV thì bắt buộc phải ghi giá kèm mốc thời gian TRƯỚC giờ chốt* — kho giá chỉ-chốt không bao giờ chứng nhận được CLV (đây là giới hạn đã gặp ở bài tiền bạc).
- **Nhóm được GIỮ vs giá chốt:** log loss của mô hình trên đúng nhóm lệnh được giữ, so với thị trường. Đây là bài thi của chính orchestrator.
- **Giá trị của Lớp AI:** tỉ lệ thắng/lỗ của nhóm bị AI cấm so với nhóm được cho qua. Nếu nhóm bị cấm không hề tệ hơn nhóm được qua sau một số lượng đủ lớn → Lớp AI vô giá trị → **tắt nó đi**, giữ lại các lớp tất định.
- **Tự giáng cấp:** cửa sổ trượt (ví dụ 500 lệnh gần nhất) mà CLV trung bình < 0 → mô hình tự rơi về PAPER, không cần ai quyết.

### 7.6 Chế độ vận hành và cổng thăng cấp
1. **PAPER:** lệnh chỉ ghi log, không tiền. Bắt buộc cho mọi mô hình mới và mọi thay đổi (kể cả đổi prompt AI).
2. **SHADOW:** chạy song song hệ thống thật nhưng vẫn không tiền, để bắt lỗi vận hành (trễ, lệch mã đội, giá cũ).
3. **LIVE với trần nhỏ:** chỉ mở khi nhóm được giữ, trên dữ kiện PAPER/SHADOW mới tinh, thắng giá chốt đạt khung thống kê đã đăng ký trước (tham chiếu: t ≥ 3,2; ≥ 1.000 quyết định có giá; CLV trung bình > 0). Trần vốn tăng theo nấc, mỗi nấc lại phải giữ vững chỉ số như nấc trước.
Bất kỳ thay đổi nào — mô hình, ngưỡng lệch, prompt, nhà cái tham chiếu — đều **đưa hệ thống về PAPER** và thi lại cổng thăng cấp. Không có ngoại lệ "chỉnh nhỏ thôi".

### 7.7 Những kiểu làm SAI phổ biến (tránh xa)
- Cho AI **chọn** lệnh ("AI thấy trận nào ngon?") — trao quyền tạo lệnh cho thứ chưa từng thi. Đây là lỗi thiết kế phổ biến nhất và đắt nhất.
- Chỉnh ngưỡng cổng **sau khi xem kết quả** của chính dữ kiện đang chấm — tự biến bài thi thành bài tập về nhà.
- Không ghi log lệnh bị cấm → không bao giờ biết cổng của mình có giá trị hay chỉ đang cản trở.
- Lấy giá ở một thị trường mỏng rồi so với mô hình, gọi phần chênh là "lợi thế" — phần lớn chênh lệch đó là giá tệ của thị trường mỏng, không phải tiền miễn phí.
- Bỏ qua công tắc giết vì "đang chuỗi thua tạm thời" — chuỗi thua là lúc công tắc tồn tại.

### 7.8 Ranh giới của tài liệu này
Thiết kế trên là khung kiểm duyệt và quản trị rủi ro cho hệ thống của bạn, vận hành **trên giấy trước** theo đúng kỷ luật bằng chứng của chương trình. Nó không phải giấy phép kết luận rằng mô hình NCAA (hay bất kỳ mô hình nào chưa qua Lớp 0 mục c) đáng tiền thật — bằng chứng hiện tại nói ngược lại. Lưu ý pháp lý giữ nguyên như đã trao đổi: cá cược thể thao nước ngoài nằm ngoài diện thí điểm được cấp phép hẹp ở Việt Nam, và việc truy cập các sàn dự đoán từ Việt Nam vướng vấn đề xác minh/khu vực — hãy tự xác minh tư cách pháp lý trước bất kỳ vận hành tiền thật nào.

---

## PHỤ LỤC — BẢN ĐỒ FILE
- `frozen_test.py` — toàn bộ đường ống mô hình (Elo + hiệu suất + GBM + chấm thi).
- `pilot_elo.py` — phần Elo rút gọn.
- `REPORT.md` — bản thiết kế gốc đã đóng băng (gồm cổng tiền bạc §5.4).
- `FROZEN_TEST_RESULTS.md` — kết quả backtest dự đoán đầy đủ.
- `AUDIT.md` — kiểm toán độc lập bài dự đoán (CONFIRMED).
- `MONEY_TEST.md` — bài kiểm tra tiền bạc (nam RỚT cổng; nữ bị chặn).
- `MONEY_AUDIT.md` — kiểm toán độc lập bài tiền bạc (CONFIRMED).
- Dữ kiện đã ghép giá–dự đoán và kết quả chi tiết: thư mục làm việc `sports_ml/ncaa/cbbd_lines/` (file `men_joined_priced.csv`, `money_gate_results.json`).

