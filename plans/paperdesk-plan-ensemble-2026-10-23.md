# KẾ HOẠCH + SPEC — ENSEMBLE BA NGUỒN CHO PAPERDESK

Tỉ lệ cuối = thị trường sắc (Pinnacle) làm neo + model của desk + nhóm dự đoán ngoài, trộn trên thang log-odds, cộng phần chỉnh theo tin của DeepSeek có nắp cứng. Owner ra lệnh nghiên cứu + viết kế hoạch 2026-10-23. Chưa có dòng code nào được đổi bởi tài liệu này. Chu trình như thường lệ: xây trong worktree → battery → A7 → chạy bóng ma → owner bấm kích hoạt riêng.

## 0. Quan hệ với kế hoạch Blend + Breaker (2026-10-23)

Kế hoạch blend + breaker CHƯA được xây và CHƯA kích hoạt, nên spec này thay thế nó trước khi kích hoạt (không phải sửa giữa đường chạy):

- GIỮ NGUYÊN từ kế hoạch cũ: chốt chặn lệch 2 nấc (bảng ngưỡng theo giải), nguyên tắc FORECAST thô không sửa một chữ số, phán quyết chỉ trên dữ liệu từ lúc kích hoạt, chu trình build → battery → A7 → bóng ma → owner GO.
- THAY 3 điểm: (a) giá neo đổi từ Polymarket khử lãi sang **Pinnacle khử lãi tại thời điểm quyết định** (PM chỉ còn là giá đặt được để tính EV); (b) pha trong **không gian log-odds** thay cho cộng phần trăm trực tiếp; (c) thêm 2 thành phần mới: nhóm dự đoán ngoài và phần chỉnh tin của DeepSeek.
- Hệ số co đầu mùa `w = g/(g+10)` của kế hoạch cũ được giữ, nhưng áp lên trọng số của model (xem §3.3).

## 0.1. Đối chiếu kế hoạch ↔ prompt build (chốt 2026-10-23)

Agent Mac phát hiện 3 điểm lệch giữa kế hoạch này và prompt build (`paperdesk-ensemble-shadow-agent-prompt-2026-10-23.md`) và dừng đúng luật. Đã chốt: ở cả ba điểm **PROMPT BUILD THẮNG** — vì prompt là văn bản chi tiết hơn và chứa các luật an toàn cứng; kế hoạch được sửa 3 chỗ cho khớp (prompt giữ nguyên không sửa chữ nào):

1. **Δ_news:** lượt gọi DeepSeek bóng ma RIÊNG (`AI_PROMPT_ENSEMBLE_SHADOW_V1`), AI_PROMPT_V3 không đổi một chữ — không nhét khối Δ vào opinion V3 (sửa §7).
2. **Đường giá Pinnacle:** bộ chụp độc lập trên Mac cho slate của desk; đầu ra W2-1 của coordinator chỉ để đối chiếu chéo, không làm nguồn nuôi chính (sửa §6 bước 0).
3. **Độ dài chạy:** hai pha — chu trình build dừng ở báo cáo bóng ma đầu tiên (sau 2 slate NBA thật); pha chạy dài tới mốc §5.4 chỉ bắt đầu bằng lệnh tiếp tục riêng sau khi coordinator kiểm + owner quyết (sửa §6 bước 5–6).

## 1. Bằng chứng nghiên cứu (đã tra, có nguồn)

1. **Trộn thẳng phần trăm làm hỏng hiệu chuẩn.** Nghiên cứu chuẩn về gộp dự báo (Ranjan & Gneiting) chứng minh: trung bình cộng tuyến tính của các dự báo đã chuẩn sẽ cho ra dự báo mất chuẩn và thiếu tự tin; cách sửa là hiệu chuẩn từng nguồn trước rồi gộp trên thang log-odds, hoặc dùng dạng beta-transform. Đây là lý do spec này bỏ cách pha phần trăm của kế hoạch cũ.
2. **Chuyên gia gộp lại cũng chỉ ngang thị trường.** Nghiên cứu trên ~2.000 người dự đoán NFL: thị trường thông tin cho độ chính xác ngang với gộp ý kiến chuyên gia; chấm trọng số theo thành tích quá khứ KHÔNG cải thiện kết quả gộp. Hệ quả thực tế: đừng kỳ vọng nhóm dự đoán ngoài thắng thị trường — nó chỉ có giá trị khi nó độc lập và giảm nhiễu.
3. **"Nghịch lý gộp dự báo":** trung bình đơn giản rất khó bị đánh bại; trọng số ước lượng từ dữ liệu thường thua vì nhiễu ước lượng. Cách làm đúng theo tài liệu: trọng số ước lượng phải bị **co mạnh về trọng số gốc**, cắt bỏ nguồn tệ hẳn, và gộp các nguồn giống nhau thành một nhóm trước khi cân.
4. **Pinnacle đóng cửa là chuẩn vàng, nhưng không phải phép màu.** Trên 31.550 trận bóng đá, đặt theo giá "công bằng" đã khử lãi của Pinnacle chỉ lỗ ~1% — tức tỉ lệ của nó rất sát sự thật. Một kiểm tra độc lập trên Ngoại hạng Anh lại thấy bet365 đóng cửa ngang Pinnacle về log-loss. Kết luận dùng cho spec: Pinnacle xứng đáng làm neo có trọng số lớn nhất, nhưng không độc quyền — vẫn chừa chỗ cho nguồn khác khi chúng bất đồng có lý do.
5. **Giá mở cửa yếu hơn giá đóng cửa một cách hệ thống** (nhiều nghiên cứu thị trường hiệu quả): thông tin chảy vào giá theo thời gian. Hệ quả: tỉ lệ neo phải lấy tại đúng thời điểm quyết định của desk, và giá đóng cửa Pinnacle là thước phán xét (CLV), không phải đầu vào.
6. **Dự báo gộp thường quá rụt rè:** khi các nguồn độc lập cùng đồng ý, tỉ lệ gộp đúng phải "cực đoan" hơn trung bình một chút (hệ số phóng đại log-odds ~1.16–3.9 trong nghiên cứu Satopää). Spec này KHÔNG áp hệ số phóng đại ở vòng đầu — vì neo thị trường đã rất mạnh; chỉ xem xét ở vòng spec sau nếu bảng điểm cho thấy tỉ lệ cuối rụt rè có hệ thống.

## 2. Kiểm kê nguồn (đã kiểm tra còn sống ngày 2026-10-23)

### 2.1. NBA

| Nguồn | Lấy ở đâu | Tính chất | Trạng thái |
|---|---|---|---|
| Pinnacle tại T−24h / T−6h10m / CLOSE | Collector W2-1 của desk đã chạy sẵn (guest API theo giải, không cần key) | Neo thị trường sắc | DÙNG — đầu vào chính |
| Model của desk | FORECAST trong sổ cái | Tín hiệu riêng của desk | DÙNG |
| ESPN Matchup Predictor (BPI) | Trang trận ESPN | Model độc lập, cập nhật sau mỗi loạt trận | DÙNG CÓ ĐIỀU KIỆN: chỉ khi chụp được ảnh chụp đóng băng kèm giờ giấc trong gói bằng chứng (luật cũ: bản live trôi nổi không tính là bằng chứng đóng băng); không chụp được → trọng số 0 trận đó |
| numberFire (FanDuel Research) | Bài dự đoán hằng ngày, có % thắng từng trận, đóng dấu giờ xuất bản | Model nERD, không phải gói lại odds | DÙNG |
| Funnyball (Substack) | Trang forecast cập nhật hằng ngày, Elo + dự phóng cầu thủ, có ghi giờ làm mới | Độc lập; tác giả nói rõ KHÔNG tính chấn thương ngắn hạn | DÙNG — coi là "sức mạnh đội hình nền" |
| Massey Ratings | Trang ratings, tỉ lệ từ cách biệt dự đoán | Độc lập, lâu đời | DÙNG (nếu lấy được đều tay; không được thì bỏ, không chặn hệ thống) |

### 2.2. WSL

| Nguồn | Lấy ở đâu | Tính chất | Trạng thái |
|---|---|---|---|
| Pinnacle | Collector bóng đá của desk đã có giá Pinnacle T−5 phút làm giá đóng cửa tham chiếu; cần mở rộng chụp tại thời điểm quyết định | Neo thị trường | DÙNG — cần 1 việc build nhỏ (§6, bước 0) |
| Model của desk | FORECAST trong sổ cái | Tín hiệu riêng | DÙNG |
| Opta Analyst (bài dự đoán vòng đấu) | Bài viết trước mỗi vòng, đủ % thắng/hòa/thua từ 10.000 lượt mô phỏng, đóng dấu ngày | Model mô phỏng độc lập với odds — nguồn ngoài tốt nhất của WSL | DÙNG — nguồn ngoài duy nhất của WSL ở vòng này |

### 2.3. Danh sách LOẠI TRỪ (đã kiểm, có lý do)

- **FiveThirtyEight / RAPTOR:** đã đóng cửa; bản mới ở Silver Bulletin chưa ra (mới hứa "trong mùa"). Không có nguồn sống → loại.
- **Các trang tip "AI prediction" kiểu Betarazi, SportBot AI:** bản chất là lấy odds nhà cái khử lãi rồi gói lại thành "model", hoặc không có thành tích kiểm chứng. Đưa vào là đếm thị trường hai lần → loại vĩnh viễn khỏi spec này.

### 2.4. Nguồn cho WNBA và bóng đá nam (kiểm kê bổ sung 2026-10-23)

- WNBA: Pinnacle (có mở kèo WNBA; neo lấy cùng cách §2.1 khi lane chạy lại) + ESPN Matchup Predictor WNBA (xác nhận còn sống qua loạt Finals 2026) + Massey Ratings (có mục WNBA). Opta không có sản phẩm dự đoán WNBA tương đương → không dùng.
- Bóng đá nam: Pinnacle (neo chính, collector bóng đá của desk đã có đường Pinnacle) + Opta Analyst (dự đoán hằng tuần Ngoại hạng Anh + các giải lớn châu Âu, 1X2 đầy đủ) + Club Elo (tỉ lệ từ Elo độc lập, phủ sóng rộng hơn Opta — dùng cho các giải Opta không viết bài, theo luật phân tầng ở §3.2).
- **Giá Polymarket làm neo:** PM là giá ĐẶT ĐƯỢC (để tính EV và đối chiếu), không làm neo tỉ lệ thật — giá PM mỏng và chậm hơn Pinnacle (bằng chứng từ các wave trước của chính desk).

## 3. Công thức tỉ lệ cuối (đóng băng cho vòng bóng ma)

### 3.1. Định nghĩa

Mọi tỉ lệ được đổi sang log-odds: `L(p) = ln(p / (1 − p))`. Tỉ lệ cuối:

```
L_final = w_sharp·L(p_sharp) + w_model·L(p_model*) + w_pub·L(p_pub) + Δ_news
p_final = 1 / (1 + e^(−L_final))
```

- `p_sharp`: Pinnacle khử lãi (chuẩn hoá trên các chân, như luật khử lãi hiện hành) tại ảnh chụp neo gần nhất TRƯỚC thời điểm quyết định. Thiếu ảnh Pinnacle → lùi về PM khử lãi và gắn cờ `SHARP_MISSING`; thiếu cả hai → fail-closed như luật hiện hành.
- `p_model*`: tỉ lệ model sau co đầu mùa (§3.3). Dòng FORECAST thô trong sổ cái KHÔNG đổi — `p_model*` chỉ sống ở tầng chọn kèo, như `p_use` của kế hoạch cũ.
- `p_pub`: trung vị (median) của các nguồn ngoài khả dụng trận đó, sau hiệu chuẩn (§3.4). Có ít hơn 1 nguồn ngoài → `w_pub` chuyển hết sang `w_sharp`.
- `Δ_news`: phần chỉnh của DeepSeek, luật ở §4.

Thị trường 3 cửa (WSL): tính log-odds theo từng chân so với phần còn lại (one-vs-rest), trộn xong chuẩn hoá lại 3 chân về tổng 1.

### 3.2. Trọng số gốc (đóng băng, chỉ đổi bằng spec mới)

| Giải | w_sharp | w_model | w_pub |
|---|---:|---:|---:|
| NBA | 0.55 | 0.25 | 0.20 |
| WSL | 0.50 | 0.20 | 0.30 |
| WNBA | 0.50 | 0.25 | 0.25 |
| SOCCER (bóng đá nam) | 0.55 | 0.15 | 0.30 |

Ghi chú cho hai lane bổ sung (owner hỏi và chốt 2026-10-23):

- **WNBA:** thị trường mỏng hơn NBA (ít tiền sắc hơn, tin chấn thương vào giá chậm hơn) nên neo hạ xuống 0.50; model giữ 0.25 như NBA; nhóm ngoài 0.25 gồm ESPN Matchup Predictor (đã xác nhận còn sống — được dùng công khai trong loạt Finals WNBA 2026) + Massey Ratings, với cùng điều kiện chụp đóng băng như NBA. Lane đang hết mùa — trọng số đóng băng từ bây giờ, build khi lane chạy lại (mùa 2027), GO riêng như các lane khác.
- **Bóng đá nam:** Pinnacle bóng đá ở các giải lớn là thị trường hiệu quả bậc nhất (chính là dữ liệu của nghiên cứu 31.550 trận ở §1.4) nên neo giữ 0.55; model của desk ở bóng đá là thành phần ít được kiểm chứng nhất (Lane X phần lớn rơi vào Box 3) nên chỉ 0.15; nhóm ngoài 0.30 gồm Opta Analyst (bài dự đoán hằng tuần cho Ngoại hạng Anh và các giải lớn, đủ % thắng/hòa/thua từ 10.000 lượt mô phỏng — đã xác nhận còn sống) + Club Elo. **Luật phân tầng giải đấu (đóng băng):** giải nào Opta không phủ sóng thì `w_pub` tự hạ còn 0.15, phần cắt chuyển sang `w_sharp`. **Ngoài phạm vi:** ensemble này chỉ áp cho kèo dạng 1X2 của cổng EV; các thị trường đặc biệt của lane bóng đá (BTTS, tỉ số đúng, kèo hòa đứng riêng) không tự động được áp — muốn áp phải có ánh xạ tỉ lệ riêng bằng spec riêng. Δ_news ở bóng đá nam dự kiến hiếm khi dùng được vì đội hình xuất phát chỉ lộ ~1 giờ trước giờ bóng lăn, sau hầu hết các mốc quyết định — nắp giữ nguyên ±0.20, kiểm tra "đã vào giá chưa" dùng neo T−60 phút mà collector bóng đá đã có.

Lý do: Pinnacle lớn nhất nhưng không độc quyền (§1.4); Opta ở WSL được trọng số cao hơn nhóm ngoài của NBA vì nó là model mô phỏng độc lập có kiểm chứng công khai, còn nhóm NBA pha nhiều nguồn không đồng đều.

### 3.3. Co đầu mùa cho model

Trọng số hiệu dụng của model: `w_model_eff = w_model · g/(g+10)`, với `g` như định nghĩa kế hoạch cũ (số trận đã kết thúc của đội ít trận hơn). Phần trọng số bị cắt chuyển sang `w_sharp`. Hệ quả: trận mở màn model gần như không có tiếng nói; khoảng trận 20 model nhận đủ trọng số gốc. Thêm một hệ số phụ đóng băng: đội bóng thay người nhiều (tỉ lệ phút thi đấu của cầu thủ mùa trước còn ở lại đội < 60%) thì `g` bị tính như `g/2` — đây là bài học trực tiếp từ vụ Giannis/LaMelo/Trae Young đổi đội hè 2026. Ngưỡng 60% và phép chia đôi là thông số đóng băng của spec này, agent tính từ dữ liệu đội hình trong corpus.

### 3.4. Hiệu chuẩn từng nguồn

- Trước khi trộn, mỗi nguồn ngoài thị trường được hiệu chuẩn dạng `L'(p) = a + b·L(p)`.
- Khi chưa đủ 200 trận có nguồn đó đi kèm kết quả: `a = 0, b = 1` (giữ nguyên, không hiệu chuẩn) — trừ model vẫn chịu §3.3.
- Từ 200 trận trở đi: ước lượng `a, b` bằng log-loss nhỏ nhất trên dữ liệu forward đã tích lũy, với `b` bị co 50% về 1 và `a` co 50% về 0. Chỉ cập nhật tại các mốc phán xét (§5), không cập nhật liên tục.

### 3.5. Cập nhật trọng số

- Chỉ tại các mốc phán xét (§5), bằng cách tối thiểu log-loss forward của tỉ lệ cuối, với ràng buộc đóng băng: `w_sharp ∈ [0.40, 0.80]`, `w_model ∈ [0.05, 0.40]`, `w_pub ∈ [0.00, 0.30]`, và kết quả ước lượng bị co 50% về trọng số gốc §3.2. Đây là cách chống "nghịch lý gộp dự báo" (§1.3): không bao giờ tin trọn con số ước lượng từ mẫu nhỏ.

## 4. Luật DeepSeek chỉnh tin (Δ_news)

DeepSeek GIỮ NGUYÊN quyền phủ quyết (VETO) hiện hành — phần này chỉ thêm một đầu ra số mới, chạy bóng ma trước như mọi thứ khác.

1. **Đầu ra bắt buộc có cấu trúc:** danh sách mục chỉnh, mỗi mục gồm: sự kiện (ai, chuyện gì), nguồn + giờ đăng (theo thang chất lượng nguồn hiện hành của V3), chân bị ảnh hưởng, mức chỉnh đề xuất theo log-odds, và câu trả lời cho câu hỏi "vì sao thị trường/model chưa tính việc này".
2. **Nắp cứng:** tổng `Δ_news ∈ [−0.20, +0.20]` log-odds (xấp xỉ ±5 điểm % quanh 50%, ±4 điểm quanh 30/70). Code của desk tự kẹp (clamp), không tin số AI tự khai. Chỉnh muốn lớn hơn nắp → không được cộng vào tỉ lệ; thay vào đó mục đó chỉ có thể đi đường VETO hoặc cờ bất đồng (§5.2).
3. **Kiểm tra "đã vào giá chưa":** sự kiện đã công khai quá 6 giờ trước thời điểm quyết định VÀ giá Pinnacle đã di chuyển cùng chiều với sự kiện → mức chỉnh của mục đó = 0. Tin chấn thương mới trong báo cáo chính thức gần giờ quyết định, thay đổi đội hình xuất phát, sân trung lập, nghỉ/B2B mà model chưa có — là các ca được chỉnh điển hình.
4. **Cấm:** chỉnh dựa trên tin đồn đơn lẻ (theo thang nguồn hiện hành), chỉnh không có nguồn giờ giấc, chỉnh lặp lại một sự kiện hai lần, dùng tin của giải nam cho trận nữ (bài học FD-2026-M48).
5. Mọi mục chỉnh được ghi vào candidate payload cạnh 5 con số của kế hoạch cũ, mở rộng thành: `p_sharp, p_model, p_pub (+ từng nguồn), Δ_news (+ từng mục), p_final, w từng nguồn, g`.

## 5. Cổng EV, chốt chặn, và cách phán đúng/sai

### 5.1. Cổng EV

- EV tính trên `p_final` và giá ĐẶT ĐƯỢC (Polymarket sau phí, như luật hiện hành). Ngưỡng EV và luật stake không đổi.
- Chốt chặn lệch: giữ bảng ngưỡng của kế hoạch cũ, nhưng độ lệch `d` đo giữa `p_model` thô và `p_sharp` (thay cho PM). Nấc cứng chặn trước AI như cũ.

### 5.2. Cờ bất đồng nguồn (mới)

- Nếu hiệu số lớn nhất giữa hai nguồn bất kỳ trong ba nguồn > 0.25 (phần trăm, trên chân được chọn): gắn cờ `SOURCE_SPLIT`. Candidate có cờ này chỉ qua được khi AI ALLOW khẳng định bằng bằng chứng (như nấc mềm của chốt chặn), bất kể EV.
- Nếu `p_final` lệch `p_sharp` quá nấc cứng của giải (bảng kế hoạch cũ): chặn như DIVERGENCE_BLOCK, lý do ghi `ENSEMBLE_DIVERGENCE_BLOCK`.

### 5.3. Bảng điểm (chạy nền, mọi trận có neo — không chỉ candidate)

Mỗi tuần, cho từng nguồn và cho `p_final`: log-loss và Brier so với kết quả thật; thêm log-loss so với Pinnacle CLOSE (ai gần giá đóng cửa sắc nhất). Bảng này là cơ sở cho §3.4–§3.5 và cho phán quyết.

### 5.4. Phán giữ/bỏ (đóng băng)

Tại 200 candidate đã quyết HOẶC 2027-02-01, mốc nào đến SAU:

- GIỮ (đủ điều kiện xin owner kích hoạt): (i) log-loss của `p_final` trên các trận candidate THẤP hơn log-loss của riêng `p_sharp` (ensemble phải thắng chính cái neo của nó, không chỉ thắng model); (ii) tiền giấy của đường ensemble ≥ đường luật hiện hành giả định trên cùng candidate; (iii) nhóm bị chặn bởi §5.2 không thắng giá đóng cửa một cách có hệ thống (CLV trung bình ≤ 0).
- Trượt bất kỳ điều nào → ensemble CHẾT ở dạng này; các nguồn thành phần vẫn giữ bảng điểm riêng để phục vụ spec khác. Cấm vặn trọng số/nắp để "cho khớp" kết quả bóng ma — muốn đổi phải viết spec mới trước khi kích hoạt.

## 6. Việc cho agent (theo thứ tự, chu trình thường lệ)

0. **Đường dữ liệu:** (a) bộ chụp Pinnacle ĐỘC LẬP chạy trên Mac cho đúng các trận thuộc slate của desk (neo tại giờ quyết định + T−6h10m + CLOSE) — tầng bóng ma phải tự chủ và kiểm chứng được tại chỗ; đầu ra W2-1 của coordinator chỉ dùng để đối chiếu chéo, không làm nguồn nuôi chính; (b) WSL: cùng bộ chụp đó mở rộng cho các trận WSL thuộc slate (thêm neo tại thời điểm quyết định; giữ luật mất dữ liệu trung thực như W2-1: thiếu là ghi MISSED, không bù sau); (c) collector nguồn ngoài: numberFire + Funnyball (NBA), Opta Analyst (WSL), ESPN predictor khi chụp đóng băng được — mọi trang lấy qua đường tim_web/mo_trang hiện hành, lưu nguyên văn + giờ lấy (luật H1).
1. **Máy chấm bóng ma:** tính `p_final` cho mọi candidate và mọi trận trên slate có neo; ghi đủ bộ số §4.5; KHÔNG đụng quyết định production.
2. **Bảng điểm tự động** theo §5.3, xuất báo cáo tuần.
3. **Battery:** số học log-odds và chuẩn hoá 3 cửa; kẹp Δ đúng biên ±0.20; lịch co g đúng tại 0/5/10/20/82 và ca đội thay người (§3.3); trung vị nhóm ngoài khi thiếu nguồn; FORECAST thô không đổi một chữ số; thiếu cả Pinnacle lẫn PM → fail-closed; cổng §5.2 kích hoạt đúng biên.
4. **A7** như thường lệ, kiểm riêng: AI_PROMPT_V3 không đổi; quyền VETO của DeepSeek không bị phần số mới lấn; không dòng lịch sử nào bị sửa.
5. **Chạy bóng ma theo 2 pha:** pha build (chu trình ENSEMBLE-SHADOW-V1) chỉ chạy tới BÁO CÁO BÓNG MA ĐẦU TIÊN (sau 2 slate NBA thật; WSL sau 1 vòng đấu đầy đủ nếu kịp) rồi DỪNG để coordinator kiểm độc lập + owner quyết. Pha chạy dài (tới mốc §5.4 hoặc ít nhất 6 tuần, báo cáo theo §5.3–§5.4) chỉ bắt đầu bằng lệnh tiếp tục riêng sau khi báo cáo đầu tiên đạt — không tự chạy liền một mạch.
6. Kích hoạt theo từng giải (NBA trước, WSL sau) chỉ bằng GO riêng của owner sau khi thấy báo cáo bóng ma + A7 PASS. Khi kích hoạt NBA: cổng EV chuyển sang `p_final`, chốt chặn đo theo §5.1 — thay cho kế hoạch blend cũ (kế hoạch cũ coi như đã bị thay thế, ghi rõ trong adoption record).

## 7. Rủi ro đã thấy trước

- **Đếm trùng ẩn:** một nguồn ngoài lén dùng odds (ví dụ đổi nhà cung cấp dữ liệu) sẽ làm ensemble tự tin giả. Giảm rủi ro: bảng điểm §5.3 đo tương quan sai số giữa các nguồn tại mỗi mốc; hai nguồn giống nhau quá mức thì gộp một nhóm theo §1.3.
- **Mẫu nhỏ:** 200 candidate là tối thiểu để phán, không phải con số đẹp. Trước mốc đó mọi kết quả chỉ là mô tả.
- **Pinnacle mất sóng:** đã có luật outage của W2-1; khi neo thiếu diện rộng (>20% slate một tuần) thì tuần đó không tính vào phán xét.
- **Chi phí AI:** Δ_news chạy bằng lượt gọi DeepSeek BÓNG MA RIÊNG (`AI_PROMPT_ENSEMBLE_SHADOW_V1`), dùng lại đúng gói bằng chứng đã thu cho candidate (không fetch thêm) và TUYỆT ĐỐI không sửa AI_PROMPT_V3 — prompt production đóng băng trong suốt chu trình này. Chi phí cộng thêm ~0,001 USD/candidate theo giá cascade hiện tại: không đáng kể so với việc giữ production nguyên vẹn.
- **WSL mỏng dữ liệu:** chỉ 1 nguồn ngoài + neo cần build thêm → WSL kích hoạt sau NBA là cố ý, không phải quên.

## 8. Điều kiện dừng

- Bất kỳ dòng FORECAST lịch sử nào thay đổi dù một chữ số.
- Battery đỏ không rõ nguyên nhân, hoặc A7 ra BUG.
- Cần đổi trọng số gốc, nắp Δ, hay ngưỡng đã đóng băng ở §3–§5 để "cho khớp" kết quả — cấm; hủy spec, viết spec mới.
- Phát hiện một nguồn ngoài trong danh sách DÙNG thực chất là gói lại odds → loại nguồn đó ngay và ghi vào adoption record (không cần hủy spec, vì §2.3 đã định trước nguyên tắc loại).
