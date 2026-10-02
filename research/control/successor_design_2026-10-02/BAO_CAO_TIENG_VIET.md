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
này cùng một cơ chế: cửa sổ chuyển giao thanh khoản London→NY.

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

## 4. Bước kế tiếp cụ thể (v2 — đã sửa theo phản biện co-owner, xem ERRATUM_V2.md)

Thứ tự đúng, mỗi bước một hành động:

1. **Owner D-1 — chọn cửa sổ lịch học** (ngày là OUTPUT của script
   `analysis/calendar_variants.py`, không phải con số dán): biến thể A
   (LEARN 27-12-2025→01-10-2026, fold 1 từ 02-10-2026, hết fold 6
   **27-09-2029**) — nhưng A tiêu thụ sealed tail, mà directive owner
   ngày 01-10 đã ghi "stays SEALED, unseal DEAD" nên A chỉ chạy nếu owner
   ra quyết định mới ghi đè; hoặc B (LEARN 02-10-2026→01-04-2027 hoàn toàn
   sau đăng ký, fold 1 08-04-2027, hết **03-04-2030**, không cần unseal,
   warmup cắt còn 26 tuần). Biến thể A′ rút khỏi bàn — nó dùng đúp dữ liệu.
   Lưu ý: đoạn M1 "chưa scored" 27-12-2025→23-09-2026 đã bị DAILY folds 7-8
   đọc & tính PnL exploratory — không phải untouched, chỉ hợp pháp làm
   LEARN.
2. **Owner D-2 (tùy chọn, theo từng cấu phần)** — xuất statement IBKR:
   chỉ nâng được commission + swap/accrual (khi attribution hợp lệ); KHÔNG
   đo được slippage/spread-beyond-cells/capacity; DECLARED + stress
   ×1.5/×2.0 vẫn là luật cho exploratory; không có con số exploratory nào
   thành "after-cost PASS" nhờ statement một phần.
3. **Owner D-3 — đăng ký cycle kế nhiệm** theo budget v2 đã tính đúng
   (Option A 33 committed/36 max identities, 192/210 scored rows, 204/222
   tổng; Option B 27/30 identities, 156/174 scored, 168/186 tổng — LOL cắt
   còn 6 chân có câu hỏi sống, 6 chân còn lại typed NOT_RUN_LOL_DEFERRED).
   Tại đăng ký: đóng băng danh sách thành phần (composition) + rule nodes;
   membership S014/S017 do owner quyết (LEARN quá mỏng để quyết: ~3–6
   entries vs floor ≥20); LOL/LORO trên validation chỉ là diagnostics,
   không bao giờ được dùng để chọn thành phần.
4. **Trước fold 1:** chạy HN-6 TB-LABELS (chỉ phân tích) và implement
   journal per-leg exposure + MAE/MFE + quote-CCY (kế thừa engine DAILY).
5. **Không có gì chạy scored** trước khi A7 prelaunch PASS + GO mới của
   owner tại gate của cycle mới (đúng thứ tự giai đoạn: draft → đăng ký →
   implementation → LEARN → freeze → A7 → GO → execution → terminal).
   Budget cũ không tái sử dụng; fold cũ đã exposed không bao giờ làm
   validation lại.

Nếu owner từ chối mọi giả thuyết trong register: hành động rỗng (D-5) cũng
hợp pháp — chương trình giữ FLAT, và hai đường duy nhất còn mở là cost
authority (D-2, từng cấu phần) và mở khóa dữ liệu cohort daily/futures (D-4).

— hết báo cáo v2 —
