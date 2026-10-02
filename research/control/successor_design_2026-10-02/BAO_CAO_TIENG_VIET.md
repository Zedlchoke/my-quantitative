# BÁO CÁO TIẾNG VIỆT — Phân tích journal & thiết kế danh mục kế nhiệm (2026-10-02)

Bản này dành cho owner: nói thẳng đã biết gì, chưa biết gì, chiến lược lớn
dự kiến chạy ra sao, và bước kế tiếp cụ thể. Mọi con số đều truy được về
artifact trong packet `research/control/successor_design_2026-10-02/` và
các nguồn đã commit trước đó.

## 1. Đã biết gì (bằng chứng đo được)

**Cấu trúc lợi nhuận của danh mục 12 tài sản:** gần như TOÀN BỘ tiền nằm ở
USDJPY (99.6% turnover, ~600–687k đơn vị journal cả hai arm). EURUSD và
GBPUSD là hai sách nhỏ (+0.6–2.3k và +0.7–0.9k). 9 tài sản còn lại không có
sách giao dịch: USDCAD/AUDUSD chết vì chi phí ngay từ TRAIN, 7 tài sản bị
chặn vì dữ liệu (PIT/chi phí/chuỗi futures) — mọi thao tác mở khóa đều là
quyền owner.

**Lợi nhuận đến từ CÁI TRỘN, không từ từng chân:** so sánh ba cách quy cho
mỗi chân phát hiện điều then chốt — S026 (chân breakout intraday) đứng sau
+825k nếu tính theo "chân gây ra lệnh vào", nhưng chạy MỘT MÌNH chỉ ra
+9.2k với drawdown 300k. Ngược lại S014 (meanrev) bị quy −222…−320k trong
danh mục nhưng chạy một mình lại +109k. Tức là: giá trị nằm ở việc
stop-cascade của S026 tái nhập quanh khối trend tồn giữ của các chân
monthly/weekly. **Không có artifact nào trên đĩa tính được "danh mục bỏ
chân X" — các arm `_MO_` là arm SOLO chứ không phải minus-one (sửa lại mô
tả sai trong docket B §9).**

**Cơ chế thất bại của 7 lần chết gating (đo chính xác đến cent):** tổng thiệt
hại −85,263 của POLICY so với always-on phân rã thành GATE −385.5k (bỏ lỡ
giao dịch) · SIZE −7.3k (đổi cỡ) · PONLY +65.7k · CARRY +241.9k. Tức là
**gating gây hại 4.4 lần tổng thiệt hại thực**, và thiệt hại chỉ còn lại
sau khi phần vị thế kế thừa (+242k) hoàn lại 79%. L6 cost guard một mình
chiếm −353k; E1 floor lại là lớp duy nhất DƯƠNG (+17.3k). Điều khiển
"oracle" (biết trước kết quả eligibility) còn thua always-on ~300k — kết
luận cấu trúc (giới hạn trong tập cơ chế ĐÃ ĐO trên lịch này, không phải
mọi gate có thể tưởng tượng được): mọi cơ chế gate portfolio đã thử đều
phá giá trị của trộn, kể cả
gate thông minh.**

**Hai bucket admission duy nhất nhất quán ở cả hai arm:** lệnh LONG USDJPY
phiên New York (16–21z) âm ở cả 8 fold cả hai arm (−281k/−84k) trong khi
London long +972k; giờ vào 12:00/16:00 UTC của EURUSD âm cả hai arm. Hai cái
này trùng khung giờ nhau — cơ chế chuyển giao London→NY CHUNG cho hai
symbol là giả thuyết POST_OUTCOME (HN-1), chưa phải nhân quả đã đo; control
placebo-session + clock-shadow mới là thứ chứng minh hay bác nó.

**Hình học exit:** cả GBPUSD S017 (20 stop : 6 take-profit, 15/28 lần đóng
trong 1 phút) và S002 (toàn bộ edge = "sống đến 16:00"; stop ±2 pip ăn −2.9k
trong khi time-exit +3.9k) là vấn đề stop nằm trong nhiễu của bar vào —
không sửa được bằng journal, phải qua lane triple-barrier.

**Cycle DAILY-EXPLORATORY-V1 đã đóng âm:** DS-03+DS-05 âm mọi tier
(−1.088k→−1.713k), floors mỏng (61 quyết định < 100), FLAT thắng tuyệt đối.
Bài học P-35: đồng hồ daily quá thưa cho corpus rules — ràng buộc thiết kế,
không phải chỗ chỉnh ngưỡng. Lưu ý minh bạch: control clock-shadow C2 trong
battery đó đã bị thay bằng REPORT20_PAIR (A7 TF-1) — không được mô tả
C2 như đã chạy.

## 2. Chưa biết gì (dữ liệu không trả lời được)

- MAE/MFE, đường giá intrabar giữa fill và close, thứ tự chạm stop/target —
  journals không có; TB-LABELS (đã thiết kế, chưa chạy) là chìa khóa.
- Chi phí thật (commission/swap/slippage) — vẫn DECLARED đến khi owner xuất
  statement IBKR (OI-2). Mọi con số "sau phí" hiện tại là PROVISIONAL.
- Counterfactual portfolio-minus-một-chân — không tồn tại; chỉ battery kế
  nhiệm với arm leave-one-leg mới trả lời được.
- Đồng quy đổi tiền: pooled cross-symbol là quy ước at-par (USDJPY);
  so sánh pooled giữa các arm bị giới hạn quy đổi (erratum DP §13). Engine
  DAILY đã có quote-CCY book — dùng lại.
- Hành vi 9 tài sản còn lại: không suy ra được từ 3 cặp FX.

## 3. Strategy lớn dự kiến hoạt động ra sao

Một câu: **"always-on có vệ sinh"** — giữ nguyên cuốn trộn netted 12 chân
(nơi tiền sống), bỏ hẳn lớp gate portfolio, chỉ thêm ba lớp vệ sinh ở mức
symbol/leg:

1. **Chặn vào lệnh trong cửa sổ chuyển giao London→NY** (USDJPY block long
   16–21z; EURUSD chặn giờ 12/16z; ngưỡng học trên LEARN, không nhìn fold
   cũ). Cơ chế đã đặt tên, hai mặt đều đo được (bỏ lỡ winner bắt buộc phải
   báo).
2. **Activity floor theo đồng hồ chân** — thay floor 3/26w toàn cục bằng
   floor theo tốc độ quyết định kỳ vọng của từng chân (chân monthly thưa là
   thiết kế, không phải chết; nhưng SIG-exit-only giữ nguyên luật cũ đóng
   băng).
3. **Nghỉ hưu/chỉ đo:** S017 nghỉ hưu theo quyết định của owner tại đăng
   ký (cả ba cách quy đều âm, cơ chế stop-trong-nhiễu, không tham số); S014
   cũng do owner quyết tại đăng ký — arm leave-one-leg chỉ là diagnostic
   cho cycle sau, không quyết trong chu kỳ; cost guard mặc định GỠ BỎ.

Hai điều thiết kế cố tình KHÔNG làm: không re-weight (equal-weight thua
−332k; lớp size đo được ≈ 0), không router/regime/breadth gate (7 cái chết
+ oracle). Baseline bắt buộc phải thắng vẫn là always-on wall; nếu lại
thua, verdict gõ `POLICY_NO_INCREMENTAL_VALUE` lần 8 và chương trình quay
sang cost-authority + mở khóa cohort khác.

## 4. Bước kế tiếp cụ thể (v3 — vòng sửa thứ ba theo F1–F5, xem ERRATUM_V3.md)

**Hai đường song song (protocol §5):**

**Đường 1 — nghiên cứu EXPLORATORY trên dữ liệu đã exposed, bắt đầu NGAY:**
(i) chạy TB-LABELS trên các panel M1 đã commit (mở khóa câu hỏi hình học
exit: thứ tự chạm stop/target, MAE/MFE); (ii) forensics journal: histogram
dải chi phí của guard (đầu vào cần THIẾT trước đăng ký cho J3), đối chiếu
session/DST của các bucket NY/handover; (iii) replay toàn-path LOL/LORO
trên fold đã exposed như một identity exploratory đăng ký riêng — cách duy
nhất hợp pháp định giá "bỏ chân X" (cấm cộng trừ PnL từng chân trên sách
netted). Mọi score mới vẫn cần cycle + gate + GO riêng; kết quả chỉ sinh
giả thuyết, không bao giờ là validation độc lập.

**Đường 2 — thu thập bằng chứng PROSPECTIVE sau khi đóng băng:** battery
6×26w chỉ chạy sau FREEZE-2 + A7 + GO; fold 1 bắt đầu SAU ngày GO
(`fold1 = max(LEARN+1+purge, GO+1)`); mọi ngày là ILLUSTRATIVE cho tới khi
có mốc đăng ký thật: biến thể A (cần owner phê chuẩn lại tail + bầu cử
tail-as-LEARN) hết ≈ 2029-10-05 (δ=1w) hoặc 2029-10-26 (δ=4w); biến thể B
(không unseal) hết ≈ 2030-04-04 (δ=1w) hoặc 2030-04-25 (δ=4w). Các mốc
mẫu và ô mỏng đã khai báo sẵn trong SAMPLE_FEASIBILITY_MATRIX.md; các bar
acceptance KHÔNG đổi để có kết quả sớm.

**Ba điều v3 sửa so với v2 (owner cần biết):** (1) luật floor tách hai lớp
INF/ECO — count tổng của fold CHỈ được điền kiểu NOT_RUN_THIN khi đóng
fold, tuyệt đối không chặn lệnh trong fold (bằng chứng: floor của DAILY là
fold-total lookahead — đã chứng minh, tác động giới hạn 3 lệnh); (2) lịch
học tách FREEZE-1 (tại đăng ký: không gian tìm kiếm/bầu cử) vs FREEZE-2
(sau LEARN: giá trị học được + code SHA); với biến thể B, 4 chân
(S002-JPY, S003, S014, S009) cần warmup 46–58 tuần nên fold 1 phải đọc
sealed tail — owner chọn: cho đọc tail làm FEATURE, hoặc các chân này vào
từ fold 2 (typed NOT_RUN_WARMUP), hoặc loại; KHÔNG cắt warmup để lọt lịch;
(3) budget canonical một số duy nhất mỗi option, kiểm bằng máy: Option A
30/32 identities, 174/186 scored rows, tối đa 35/204, tổng 216; Option B
24/26 identities, 138/150 rows, tối đa 29/168, tổng 180 (LOL chỉ trên chân
còn admited — S017 nghỉ hưu trước nên không có arm LOL∖S017).

**Owner quyết (mỗi mục một hành động):** D-1 chọn biến thể A/B (+ kỳ vọng
δ); D-1a (chỉ A) phê chuẩn lại tail-for-exploratory + bầu cử
tail-as-LEARN — lưu ý khuyết điểm lineage: ba artifact của DAILY ghi "S1
SEALED_UNTOUCHED" trong khi journal của chính nó có fill trong khoảng tail
(cần ratify hoặc erratum); D-1b (chỉ B) bầu cử warmup cho 4 chân; D-2
(không bắt buộc) xuất statement IBKR — chỉ nâng được commission/swap,
không đo được slippage/spread/capacity; D-3 đăng ký (gói FREEZE-1: budget
theo manifest, luật floor INF/ECO + cách đọc aggregate floor, bầu cử
membership, pin warmup, risk caps, grids); D-4 lộ trình cohort khác; D-5
hành động rỗng (giữ FLAT) cũng hợp pháp.

**Khuyến nghị ưu tiên (có lý do):** Đường 1 mục (i)+(ii) TRƯỚC — TB-LABELS
và histogram guard là đầu vào bắt buộc của chính đăng ký Đường 2 (chúng
cung cấp MAE/MFE cho engine kế nhiệm và độ khả thi node J3); sau đó mục
(iii) replay exploratory làm bằng chứng bầu cử membership; Đường 2 đăng ký
khi nào owner sẵn sàng — không có gì trong Đường 1 phải chờ 2029/2030.

— hết báo cáo v3 —