# PROMPT CHO AGENT — BUILD BẢN BÓNG MA ENSEMBLE BA NGUỒN (CHỈ SHADOW, KHÔNG KÍCH HOẠT)

PaperDesk / chu trình ENSEMBLE-SHADOW-V1. Ngày ra lệnh: 2026-10-23 (owner GO build bóng ma).
Nguồn sự thật của chu trình này: file kế hoạch `paperdesk-plan-ensemble-2026-10-23.md` (owner sẽ đặt cùng thư mục control với prompt này). ĐỌC TOÀN BỘ trước khi đụng vào code. Prompt này chép nguyên các thông số đóng băng của spec (§3–§5 của kế hoạch) — nếu có chỗ nào prompt và kế hoạch mâu thuẫn, DỪNG và báo owner, không tự chọn.

## Phạm vi (đọc kỹ, đây là ranh giới cứng)

- Chu trình này CHỈ xây tầng bóng ma: tính tỉ lệ ensemble cho candidate, ghi sổ, chấm điểm nền, ra báo cáo. **Production vẫn ra quyết định bằng luật hiện hành, không đổi một hành vi nào.**
- KHÔNG kích hoạt cổng EV theo tỉ lệ ensemble. KHÔNG đổi luật stake, luật anchor, luật chọn kèo. Kích hoạt là chu trình riêng, cần GO riêng của owner sau báo cáo bóng ma + A7.
- Kế hoạch blend + breaker cũ coi như ĐÃ BỊ THAY THẾ bởi spec ensemble (chưa từng được build) — không build cả hai.

## Luật chung (không thương lượng)

1. KHÔNG đổi văn bản AI_PROMPT_V3 — sha256 phải giữ nguyên `c2c4fd464f0413a054d94cb2f555f1e9325ed3b78111142b551026f3e2a0c890` trước và sau chu trình. Quyền VETO của DeepSeek trong production KHÔNG đổi.
2. Mọi dòng FORECAST lịch sử và hiện tại trong sổ cái GIỮ NGUYÊN từng chữ số. Tỉ lệ ensemble chỉ sống ở tầng bóng ma và payload phụ, không bao giờ ghi đè tỉ lệ thô của model.
3. Mọi thay đổi đi qua battery kiểm thử đầy đủ + kiểm toán A7 như các chu trình trước. Battery đỏ không rõ nguyên nhân = DỪNG, báo owner, không đi tiếp.
4. Luật trung thực nhật ký giữ nguyên: nguồn nào không lấy được thì ghi rõ 0 nguồn / MISSED + lý do. Tuyệt đối không bịa nguồn, không bịa tỉ lệ, không bù số liệu sau khi trận đã qua (no back-fill).
5. Mọi ảnh chụp giá/dự đoán phải kèm mốc thời gian lấy thật (UTC) và chỉ được dùng nếu lấy TRƯỚC thời điểm quyết định của candidate. Ảnh chụp sau giờ quyết định = không dùng cho candidate đó, ghi rõ lý do.
6. Mỗi task xong phải có: test tương ứng trong battery + mục ghi trong báo cáo chu trình (đã làm gì, file nào đổi, bằng chứng nào).

## Thông số đóng băng (chép từ spec — cấm vặn)

- Log-odds: `L(p) = ln(p / (1 − p))`; tỉ lệ cuối `L_final = w_sharp·L(p_sharp) + w_model·L(p_model*) + w_pub·L(p_pub) + Δ_news`, `p_final = 1 / (1 + e^(−L_final))`.
- Trọng số gốc: NBA — sharp 0.55 / model 0.25 / ngoài 0.20. WSL — sharp 0.50 / model 0.20 / ngoài 0.30.
- `p_sharp`: Pinnacle khử lãi (chuẩn hoá `q_i = 1/odds_i` trên các chân) tại ảnh chụp neo gần nhất trước giờ quyết định. Thiếu Pinnacle → lùi về Polymarket khử lãi + cờ `SHARP_MISSING`. Thiếu cả hai → candidate không có tỉ lệ ensemble (ghi rõ), không chặn gì ở production.
- Co đầu mùa cho model: trọng số hiệu dụng `w_model_eff = w_model · g/(g+10)`, `g` = số trận regular-season đã kết thúc của đội ít trận hơn tại thời điểm forecast; phần bị cắt chuyển sang `w_sharp`. Thêm: nếu tỉ lệ phút mùa trước của cầu thủ còn ở lại đội < 60% thì `g` tính như `g/2` cho đội đó (lấy phía bất lợi hơn trong hai đội).
- `p_pub`: trung vị (median) các nguồn ngoài khả dụng trận đó. < 1 nguồn → `w_pub` chuyển hết sang `w_sharp`.
- `Δ_news ∈ [−0.20, +0.20]` log-odds, code tự kẹp (clamp) — không tin số AI tự khai.
- Thị trường 3 cửa (WSL): log-odds one-vs-rest từng chân, trộn xong chuẩn hoá 3 chân về tổng 1.
- Chốt chặn và cờ bất đồng CHỈ ĐỂ BÁO CÁO trong chu trình này (would-block / would-flag), không chặn thật: độ lệch `d = |p_model thô − p_sharp|` trên chân chọn; nấc mềm/cứng theo bảng của kế hoạch blend cũ (NBA 0.10/0.20; WSL 0.12/0.22); cờ `SOURCE_SPLIT` khi hai nguồn bất kỳ lệch nhau > 0.25.

## Task 0 — Đường giá Pinnacle tại thời điểm quyết định (trên máy Mac)

- Hiện trạng: collector W2-1 của coordinator chạy trên VM và chụp Pinnacle tại T−24h / T−6h10m / CLOSE cho các trận NBA có trên Polymarket. Tầng bóng ma trên Mac cần dữ liệu của riêng nó, tự chủ, kiểm chứng được tại chỗ.
- Việc: (1) xây bộ chụp Pinnacle cho đúng các trận thuộc slate candidate: tại giờ quyết định (neo quyết định), tại T−6h10m, và tại CLOSE (ảnh cuối trước giờ bóng lăn), qua guest API theo giải như cách W2-1 đã chứng minh (league-scoped; sport-scoped bị chặn địa lý trên VM — trên Mac tự kiểm chứng và ghi kết quả vào báo cáo). (2) Mỗi ảnh chụp lưu: mã trận, hai/ ba chân, odds thô, giờ lấy UTC, nguồn URL. (3) WSL: mở rộng cùng bộ chụp cho các trận WSL thuộc slate (Pinnacle có WSL; collector bóng đá phía coordinator đã dùng Pinnacle T−5 phút làm giá đóng cửa — ở đây cần thêm neo giờ quyết định).
- Cấm: không bù ảnh chụp đã lỡ (MISSED là MISSED, ghi sổ); không dùng giá đóng cửa làm neo quyết định.
- Nghiệm thu: slate thật đầu tiên — mọi candidate có dòng neo (hoặc MISSED trung thực); báo cáo ghi tỉ lệ phủ Pinnacle theo slate; spot-check tay 1 trận: odds trong ảnh chụp khớp trang Pinnacle tại cùng thời điểm trong sai số làm tròn.

## Task 1 — Collector nguồn dự đoán ngoài

- NBA: (a) numberFire / FanDuel Research — bài dự đoán ngày, lấy % thắng từng trận + giờ xuất bản; (b) Funnyball — trang forecast, lấy % thắng + mốc "last refresh" của trang; (c) Massey Ratings — tỉ lệ từ trang ratings nếu lấy đều tay được, không được thì bỏ và ghi rõ; (d) ESPN Matchup Predictor — CHỈ dùng khi chụp được ảnh đóng băng kèm giờ giấc trong gói bằng chứng của candidate (bản live trôi nổi không tính); không chụp được → nguồn vắng mặt trận đó.
- WSL: Opta Analyst — bài dự đoán vòng đấu (đủ % thắng/hòa/thua), lấy trước giờ quyết định của từng trận trong vòng.
- Mọi lần lấy đi qua đường fetch có journal nguyên văn như luật H1 hiện hành (URL + fetched_at + nội dung gốc). Trang lấy sau giờ quyết định → không dùng cho candidate đó.
- Cấm: không đưa bất kỳ trang tip/"AI prediction" nào khác vào danh sách (đặc biệt các trang chỉ gói lại odds nhà cái). Muốn thêm nguồn phải có spec sửa riêng.
- Nghiệm thu: báo cáo chu trình có bảng: nguồn × slate × số trận lấy được / tổng số trận, kèm 2 ví dụ journal nguyên văn.

## Task 2 — Máy tính ensemble bóng ma

- Việc: với mỗi candidate (mọi lane đang chạy thật: NBA trước, WSL khi Task 0/1 sẵn sàng cho WSL), tính và ghi vào payload bóng ma riêng (không đụng payload production): `p_sharp, p_model (thô), p_model*, p_pub (+ từng nguồn thành phần), Δ_news (Task 3; chưa có thì = 0 + cờ NEWS_PENDING), p_final, w_sharp, w_model_eff, w_pub, g, cờ SHARP_MISSING, cờ SOURCE_SPLIT, would-block/would-flag theo luật chốt ở trên`.
- Đội thay người (§ hệ số g/2): tính tỉ lệ phút còn ở lại từ dữ liệu đội hình/thống kê ESPN mà desk đã có đường lấy. Nếu KHÔNG có đường lấy tin cậy: để hệ số này ở trạng thái `CONTINUITY_UNKNOWN` (không áp g/2), ghi rõ trong báo cáo để owner/coordinator quyết — tuyệt đối không ước lượng tay.
- Nghiệm thu: battery — số học log-odds; chuẩn hoá 3 cửa; lịch co g đúng tại g = 0/5/10/20/82; median khi thiếu nguồn; trọng số dồn đúng khi w_pub = 0 hoặc model bị co; clamp Δ đúng biên; FORECAST thô không đổi một chữ số trên corpus đóng băng; thiếu cả Pinnacle lẫn PM → không sinh p_final và ghi lý do.

## Task 3 — Δ_news bóng ma bằng lượt gọi DeepSeek RIÊNG (không đụng V3 production)

- Việc: tạo prompt bóng ma riêng `AI_PROMPT_ENSEMBLE_SHADOW_V1` (file riêng, đóng băng, ghi sha256 vào báo cáo chu trình). Lượt gọi này chạy SAU opinion V3 production, dùng lại đúng gói evidence đã thu cho candidate (không fetch thêm), và chỉ xuất 1 khối cấu trúc: danh sách mục chỉnh — mỗi mục gồm: sự kiện, citation (nguồn + giờ đăng, phải có sẵn trong gói evidence), chân ảnh hưởng, mức chỉnh đề xuất (log-odds), và trường `why_not_priced` trả lời vì sao thị trường/model chưa tính việc này.
- Luật cứng trong prompt + code kiểm lại: (1) sự kiện công khai > 6 giờ trước giờ quyết định VÀ giá Pinnacle đã chạy cùng chiều → mức chỉnh mục đó bị code ép về 0 (trường hợp này agent phải tự mô tả cách kiểm "giá đã chạy cùng chiều" từ 2 ảnh chụp Pinnacle gần nhất có được; không kiểm được thì ghi `PRICE_CHECK_UNAVAILABLE` và mục đó = 0); (2) tin đồn đơn lẻ theo thang nguồn V3 → không được thành mục chỉnh; (3) cấm hai mục cùng một sự kiện; (4) tổng Δ bị clamp ở Task 2.
- Cấm: không sửa prompt V3 để "nhồi" thêm đầu ra này; không cho khối bóng ma ảnh hưởng bất kỳ quyết định production nào.
- Nghiệm thu: 1 candidate thật: khối Δ_news có đủ trường, mọi citation truy được về gói evidence; battery có test ép 0 cho ca "đã vào giá" và test clamp tổng.

## Task 4 — Bảng điểm nền + báo cáo bóng ma

- Việc: sau khi trận kết thúc, chấm cho TỪNG nguồn (p_sharp neo, p_model thô, từng nguồn ngoài, p_final) trên MỌI trận thuộc slate có neo: log-loss + Brier; thêm log-loss của từng nguồn so với Pinnacle CLOSE (ai gần giá đóng cửa nhất). Cộng dồn theo tuần.
- Báo cáo bóng ma đầu tiên sau **2 slate NBA thật** (WSL: sau 1 vòng đấu đầy đủ nếu kịp): (a) bảng phủ dữ liệu (Pinnacle / từng nguồn ngoài / Δ_news); (b) bảng điểm tích lũy tới thời điểm báo cáo (ghi rõ n còn nhỏ, chỉ mô tả); (c) danh sách candidate mà luật ensemble SẼ khác luật hiện hành (would-block / would-flag / EV đổi dấu), kèm bộ số đầy đủ của từng candidate đó; (d) mọi lỗi, MISSED, SHARP_MISSING, CONTINUITY_UNKNOWN gặp phải.
- Nghiệm thu: báo cáo tồn tại dạng file trong thư mục control, số liệu truy được về journal/sổ cái; coordinator sẽ kiểm lại độc lập.

## Thứ tự chạy + điểm dừng

Task 0 → Task 1 → Task 2 → Task 3 → Task 4. Xong Task 4 (báo cáo bóng ma đầu tiên) thì DỪNG, chờ coordinator kiểm + owner quyết. Các mốc phán giữ/bỏ chính thức (200 candidate hoặc 2027-02-01) và việc kích hoạt nằm ngoài chu trình này.

## Phụ lục (ghi vào spec, KHÔNG build trong chu trình này)

Trọng số gốc cho hai lane còn lại đã được owner chốt trong kế hoạch (§3.2): WNBA — sharp 0.50 / model 0.25 / ngoài 0.25 (lane hết mùa, build khi chạy lại mùa 2027, GO riêng); bóng đá nam (SOCCER) — sharp 0.55 / model 0.15 / ngoài 0.30, kèm luật phân tầng giải đấu (giải Opta không phủ sóng: w_pub hạ còn 0.15) và loại trừ các thị trường đặc biệt (BTTS, tỉ số đúng). Agent chỉ ghi nhận phụ lục này vào bản spec đặt trong repo; không mở rộng phạm vi build của chu trình này sang hai lane đó.

## Điều kiện dừng ngay (báo owner, không đi tiếp)

- Bất kỳ dòng FORECAST lịch sử nào thay đổi dù một chữ số, hoặc sha AI_PROMPT_V3 thay đổi.
- Battery đỏ không rõ nguyên nhân, hoặc A7 ra BUG.
- Cần đổi bất kỳ thông số đóng băng nào ở trên để "cho khớp" kết quả — cấm; báo owner để viết spec mới.
- Phát hiện một nguồn ngoài trong Task 1 thực chất là gói lại odds nhà cái → loại nguồn đó, ghi vào báo cáo, đi tiếp với các nguồn còn lại (đây là ngoại lệ duy nhất được tự xử).
