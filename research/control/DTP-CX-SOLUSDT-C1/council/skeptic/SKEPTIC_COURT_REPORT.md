# SKEPTIC COURT REPORT — DTP-CX-SOLUSDT-C1 (F-0 court, pre-PnL)

- Lane: `skp` · Role: economic skeptic (VETO pre-PnL) · Convened: 2026-09-27 (UTC)
- Cycle: `DTP-CX-SOLUSDT-C1` · Parent: `DAYTRADE-PLAYBOOKS-PROGRAM-V1`
- Worktree HEAD at court: `9ba72e6cd2b28a039791cc6a6f75e8ac10ef1cb2`
  (branch `orca/dtp-cx-solusdt-c1-integration`); no commit made (lane write-only).
- Machine artifact: `council/skeptic/court_machine@1.json` (mọi số dưới đây có
  ở đó, kèm commands + sha256 của mọi input).
- Scope: F-0 three tests (I001, I002) + I002 measurement battery (BTC 1m staging,
  event census 1m/5m, lag feasibility, ceiling×power grid, representation rho)
  + I001 generator adjudication + open-call record + court verdicts.

> **Chưa có PnL nào được xem hoặc tính toán cho identity nào trong phiên tòa này.**
> Mọi phép đo là **census độ lớn có điều kiện outcome-blind** (falsifier khả thi,
> tiền lệ PWS) — KHÔNG phải PnL, KHÔNG có strategy code nào được viết cho arm nào.

---

## 0. Tóm tắt phán quyết (verdict table)

| Identity | Verdict | Luật |
|---|---|---|
| **I001** (OUTCOME-BLIND ANNOTATED PLAYBOOK CORPUS) | **ELIGIBLE_FOR_FREEZE — AS GENERATOR** (điều kiện ràng buộc C1–C6) | route hợp lệ master §4.3; scored surface = từng RULE sau F-0 riêng |
| **I002** (INTRADAY BTC→SOL LEAD-LAG DIFFUSION) | **KILLED — `K-F0` + `K-COST` + `K-ANC`** (terminal pre-PnL) | §6.4 master; 3 luật độc lập, đều đo trên bytes đã stage |
| Slot 3 (OPEN-CALL) | **SLATE_EMPTY** — không có proposal nào trước giờ tòa mở | hợp lệ theo master §2 + child plan §3 |

**Một câu cho I002:** SOL đã adjust xong **trong chính phút tín hiệu** (median
cùng-phút 17.8–62.8 bps, cùng chiều BTC), phút kế tiếp còn lại **median ≈ 0.00 bps,
mean ≤ 2.2 bps** — trong khi sàn RT là 11.92 bps (1×). "SOL chưa adjust" là
hư cấu đo được; grid trần×sức mạnh **rỗng ở mọi θ, mọi multiplier**; và chuỗi
quyết định của I002 có |rho| 0.23–0.51 với gate momentum-sign (dead class) ở
mọi θ. Không có gì để freeze.

---

## 1. Data nền của tòa (staging + census nguồn)

- **Staged BTCUSDT 1m klines** 2020-09..2026-08 từ Binance Vision (keyless):
  **72/72 zips, 72/72 .CHECKSUM MATCH, 135,328,606 bytes (135.3 MB)**; manifest
  sha256 riêng của lane skeptic:
  `data_local/vision/klines_um_BTCUSDT_1m/MANIFEST_sha256.json`
  (sha `6ec3189f…`). df-guard trước từng file; **free disk 5.72 GiB → 5.56 GiB**,
  sàn 5.0 GiB không bị vượt (`BLOCKED_STORAGE` không kích hoạt).
- **Census nguồn BTC corpus:** 3,155,040 rows 1m; first open
  2020-09-01T00:00Z (`1598918400000`), last 2026-08-31T23:59Z (`1788220740000`);
  không tháng SOL nào thiếu; guard scale µs→ms (L-TRACKB1-1) áp dụng per-row
  (corpus này all-ms, nhất quán với census của lane dg).
- Script (sha-pinned trong machine JSON):
  `council/skeptic/scripts/skp_stage_btc_1m.py`,
  `council/skeptic/scripts/skp_census_i002.py` — streaming theo tháng, không
  load toàn bộ corpus; job nhẹ (<10 phút CPU, <1 GB temp).
- **Công bố lỗi đã sửa:** lần chạy đầu census có lỗi off-by-one-ms trong
  one-shot consumption khung 1m (`lastc = m+1` thay vì `m+60000`) — 1m oneshot
  bằng raw; đã sửa và **chạy lại đúng một lần** trước khi phán. Đường 5m không
  bị ảnh hưởng. Mọi số trong báo cáo này là của lần chạy đã sửa (xem `notes`
  trong machine JSON).

## 2. I002 — đo đạc phân xử (mọi số: one-shot, completed bars, non-overlapping)

### 2.1 Event census — BTC |close/open−1| ≥ θ (1m; và 5m aggregate)

| θ (bps) | 1m raw | 1m oneshot | 5m oneshot | oneshot evaluable (lag) | oneshot trong 6 tháng bookTicker |
|---|---|---|---|---|---|
| 10 | 420,039 | 315,579 | 159,012 | 312,299 | 17,195 |
| 15 | 191,552 | 151,012 | 106,322 | 149,488 | 7,350 |
| 20 | 99,500 | 80,843 | 72,382 | 80,018 | 3,606 |
| 25 | 56,795 | 47,083 | 50,752 | 46,620 | 1,962 |
| 30 | 35,065 | 29,384 | 36,603 | 29,086 | 1,179 |
| 40 | 15,528 | 13,257 | 20,625 | 13,126 | 485 |
| 50 | 8,029 | 6,909 | 12,413 | 6,840 | 255 |

(5m raw: 237,028 → 14,841 tương ứng; xem `events_5m` trong machine JSON.) One-shot
(per-θ): event tại phút m tiêu thụ m+1; candidate kế tiếp ≥ m+2 — mirror đúng
I002 §1 "no stacking". Cột cuối: số event rơi vào 6 tháng bookTicker đo được
(2023-05/07/09/11, 2024-01/03) — cơ sở phân xử nhánh BLOCKED_DATA (§2.5).

**Kết luận power:** sàn ≥100 closed RT (master §6.5) **đạt ở mọi θ**, cả
full-span lẫn trong-window. Power KHÔNG phải nguyên nhân chết — identity chết
khi đã có power trong tay, không có lối thoát INCONCLUSIVE.

### 2.2 Lag feasibility — "SOL chưa adjust" là hư cấu đo được (information test)

Conditional on BTC oneshot events, SOL move (bps, signed theo chiều BTC,
close-to-close 1m cả hai chân):

| θ | SOL cùng phút (median / mean) | SOL phút kế (median) | SOL phút kế (mean cc) | SOL phút kế (mean executable open→close) |
|---|---|---|---|---|
| 10 | **+17.80** / 21.15 | **−0.000** | 0.562 | **0.532** |
| 15 | +24.06 / 28.27 | 0.000 | 0.944 | 0.882 |
| 20 | +30.04 / 35.32 | −0.207 | 1.271 | 1.193 |
| 25 | **+36.14** / 42.68 | 0.000 | 1.624 | **1.515** |
| 30 | +41.84 / 49.67 | −0.245 | 1.909 | 1.770 |
| 40 | +52.57 / 63.39 | −0.000 | 2.234 | 2.034 |
| 50 | **+62.80** / 76.78 | 0.000 | 1.987 | **1.693** |

(full distribution p10/p25/median/mean/p75/p90 trong machine JSON.)

Đọc kinh tế: SOL thực hiện **phần lớn adjustment TRONG phút tín hiệu** —
median cùng-phút 17.8→62.8 bps tăng gần tuyến tính với θ, tức SOL phản ánh
gần đúng mức move của BTC ngay trong bar. Phút kế tiếp — cửa sổ có thể capture —
còn lại **median ≈ 0.00 bps ở mọi θ** (nửa số event: 0 hoặc bất lợi), mean
0.53–2.03 bps dạng executable. Tầng thông tin "SOL not yet adjusted" do đó là
**fictional đo được ở granularity 1m bar**: không có residual đủ lớn để trả
chi phí. Đây chính là điều information test (Q-7) đòi đo, và nó FAIL có số.

One-way ratchet (nêu rõ): census klines này là **falsifier** — nó có thể giết,
không thể cứu. Cửa "cứu" duy nhất là series IL được khai tên đo được
staleness event-time DƯƠNG và vượt trần — bất khả thi về mặt cấu trúc khi toàn
bộ adjustment phút-kế chỉ ≤2.2 bps mean ở mức bar.

### 2.3 Ceiling×power grid (P-29 one-line kill) — `K-COST` RỖNG TOÀN BỘ

RT ladder từ cost book (`cost_book@draft.json`, sha `896bcf85…`): declared
out-window (PRIMARY, binding full-span, `FILL_QUALITY_CLASS_declared`)
12.0/18.0/24.0 bps; in-window measured (sensitivity) 11.92/17.88/23.84 bps.
Capture = mean executable next-minute (định nghĩa nghiêm nhất có lợi cho
identity đã ghi kèm upper bound close-to-close). Quy tắc template (strict):
net ≤ 0 tại BẤT KỲ multiplier nào ⇒ VETO.

| θ | capture exec (bps) | net @1× (declared) | net @1.5× | net @2× | net @1× (measured ladder) | VETO | Grid rỗng (full-span) | Grid rỗng (bookTicker window) |
|---|---|---|---|---|---|---|---|---|
| 10 | 0.532 | −11.47 | −17.47 | −23.47 | −11.39 | ✓ | ✓ | ✓ |
| 15 | 0.882 | −11.12 | −17.12 | −23.12 | −11.04 | ✓ | ✓ | ✓ |
| 20 | 1.193 | −10.81 | −16.81 | −22.81 | −10.73 | ✓ | ✓ | ✓ |
| 25 | 1.515 | −10.49 | −16.49 | −22.49 | −10.41 | ✓ | ✓ | ✓ |
| 30 | 1.770 | −10.23 | −16.23 | −22.23 | −10.15 | ✓ | ✓ | ✓ |
| 40 | 2.034 | −9.97 | −15.97 | −21.97 | −9.89 | ✓ | ✓ | ✓ |
| 50 | 1.693 | −10.31 | −16.31 | −22.31 | −10.23 | ✓ | ✓ | ✓ |

Grid **jointly empty ở cả 7 θ × 3 multiplier × 2 ladder × 2 cơ sở power**.
Điều kiện freeze của child plan §3 ("diffusion capture 1m phải ≥ ceiling ở cả
θ grid") fail sai lệch một bậc độ lớn: cần capture ≥ ~12 bps để hòa 1×; đo được
≤ 2.03 bps. **`K-COST` bắn pre-PnL, cơ học.**

### 2.4 Representation rho (K-ANC) — decision series nằm trong dead class

Representation đóng băng one-shot (committed trước khi chạy, trong header của
census script): `d(m) = sign(r_BTC(m))·1{oneshot event tại θ}` trên đồng hồ
1m BTC (sau warmup 200 bar); hai proxy dead-class từ klines:
- **g1** — EOS1-E1-style BTC own-price SMA200 state gate:
  `sign(close − SMA200(close, 200 bar 1m))` (dead: `EOS1-E1`,
  FAMILY_FAILURES — BTC state gate không tách được anything posthoc);
- **g2** — BTC momentum sign-run gate, k=30 (pinned): `sign(Σ30 return 1m)`
  (dead-class representative của `PWSCXSOL1-I001` run/sign-gate +
  VIABILITY "momentum/continuation mọi cadence dead").

rho đo trên **decision grid của chính representation** (V9 lesson: committed,
reproducible). Verdict bar của skeptic = max(|rho_full|, |rho_event|) > 0.20:

| θ | rho event-subset vs g1 (SMA200) | vs g2 (momentum-sign) | rho full-grid g1 / g2 | K-ANC |
|---|---|---|---|---|
| 10 | 0.1650 | **0.2341** | 0.052 / 0.074 | ✓ (g2) |
| 15 | **0.2083** | **0.2903** | 0.045 / 0.063 | ✓ (g1+g2) |
| 20 | **0.2500** | **0.3395** | 0.039 / 0.054 | ✓ |
| 25 | **0.2831** | **0.3794** | 0.034 / 0.046 | ✓ |
| 30 | **0.3104** | **0.4127** | 0.029 / 0.039 | ✓ |
| 40 | **0.3658** | **0.4669** | 0.023 / 0.030 | ✓ |
| 50 | **0.4108** | **0.5085** | 0.018 / 0.023 | ✓ |

Trong 6 tháng bookTicker measured, kết luận không đổi (bt g1-event
0.184→0.398). Full-grid rho nhỏ chỉ là pha loãng do d thưa — thước đo trung
thực là event-subset (chính là "decision grid" của representation). **`K-ANC`
bắn ở mọi θ** qua g2 (và θ≥15 qua g1). Xu hướng tăng theo θ: yêu cầu print
càng lớn, event càng nằm sâu trong momentum-run — chuỗi quyết định của I002
không phải tầng thông tin độc lập, nó là re-gate của dead momentum/continuation.

### 2.5 Nhánh BLOCKED_DATA pre-declared — phân xử trung thực (master §3.3)

Câu hỏi tòa phải trả: với aggTrades `NOT_RUN_STAGE_BUDGET`, I002 có được tiếp
tục bằng (klines representation + bookTicker measured months) mà KHÔNG proxy
substitution không?

1. **Klines-only cho lag claim: KHÔNG.** Klines không phải tầng quote/trade;
   dùng nó thay IL-1/IL-2 rồi khẳng định cơ chế gốc = proxy substitution bị cấm
   (§3.3, A7-F1, `PROXY_NOT_ORDERBOOK`). Census klines của tòa là falsifier,
   không phải tầng thông tin của identity.
2. **Restricted-form (dev = đúng 6 tháng bookTicker, IL-2 only): ĐÚNG LUẬT về
   hình thức.** Đó là series IL-2 được khai tên trên coverage measured
   gate-PASS — giới hạn về vùng đo được, không phải thay series khác. Power
   in-window đạt (255–17,195 events ≥ 100). Tức là **nhánh BLOCKED_DATA về
   nguyên tắc có một lối freeze hợp lệ**.
3. **Nhưng về bản chất nhánh đó cũng chết:** grid rỗng y hệt trong bookTicker
   window, K-ANC giữ nguyên in-window. ⇒ **Nhánh BLOCKED_DATA là MOOT: I002
   KILLED trên luật đo được; nâng ngân sách aggTrades KHÔNG hồi sinh** (vụ giết
   không đứng trên lớp dữ liệu thiếu). Điều kiện hồi sinh (R5-class, master §5,
  quyền owner): proposal MỚI với series PIT quote/trade được khai tên, đo được
   staleness event-time DƯƠNG vượt trần RT — tức book-level staleness lớn hơn
   bậc độ lớn so với residual ≤2.2 bps mức bar; F-0 mới toàn phần.

### 2.6 Ghi nhận khung 5m

5m chỉ đo event count theo scope của tòa (oneshot 159,012 @θ=10 → 12,413
@θ=50). Pivot sang khung 5m SAU khi đo = re-clock của cùng dead family
(owner law 2026-09-27; Q-3), vẫn đụng K-ANC (rho tăng theo cỡ move) và lớp IL
BLOCKED — không có lối cứu.

## 3. I002 — F-0 three tests (verdict từng test)

1. **Skeleton test: FAIL (conditional).** Bỏ observable đặc thù ("chưa adjust")
   còn lại: BTC move confirm → vào SOL cùng chiều, time-stop — đúng skeleton
   continuation đã chết (taxonomy row 1/4; VIABILITY momentum/continuation mọi
   cadence DEAD; `PSV1 CONTROL_OUTEARned`; `H-VOLCOMP-BRKOUT` DEAD). Observable
   là load-bearing ⇒ identity sống hay chết nằm ở lag — và lag đo được ≈ 0
   (§2.2). Không có "edge còn lại" khi bỏ observable.
2. **Payer test: NOT_VERIFIED_ON_BYTES + fictional-counterparty exposure mở.**
   Câu chuyện stale-quote maker bị adversely select là cơ chế thật trên nguyên
   tắc (latency floor), nhưng (a) IL-1 NOT_RUN, IL-2 chỉ 6 tháng; (b) đo được
   SOL adjust NGAY TRONG phút tín hiệu (median 17.8–62.8 bps) — mâu thuẫn trực
   tiếp với tiền đề "maker chưa kịp adjust". Không xác minh được payer = không
   qua payer test.
3. **Information test: FAIL CÓ SỐ.** Thông tin "chưa có trong clock/trend/spread"
   mà identity đòi hỏi là residual BTC→SOL 1 phút; đo được: median −0.245..0.00
   bps, mean ≤ 2.23 bps — dưới 10 bps fee-only, xa dưới RT 11.92. ⇒ không có
   tầng thông tin.

## 4. I001 — adjudication route generator (master §4.3)

**Route có hợp pháp không? CÓ — `ADMIT_AS_GENERATOR`.** Lý do:

- Taxonomy row 13 là METHOD row được master §4.3 cho phép; generator không phải
  identity scored; "annotation không phải giấy thông hành" — mọi RULE codify
  chịu F-0/anti-variant/collision như mọi identity. Proposal I001 tự khai đúng
  điều đó (§0: generator, không phải scored identity; kỳ vọng ≥80% RULE chết
  collision — trung thực, testable).
- **Blindness guarantees kiểm tra từng điều khoản của protocol (I001 §1):**
  (1.1) nguồn public + dated (platform timestamp) + geometry-stated + author
  cap + pre-decision-point rule — đúng; (1.3) annotator workspace truncate
  byte-level tại publication timestamp + sha — outcome-blind by construction;
  (1.4) prohibition list đủ: cấm chart biết kết quả, cấm ex-post recap/hindsight,
  cấm nguồn sau window, cấm paraphrase-sharpening, cấm outcome-stat làm bằng
  chứng premium, cấm peeking sealed OOS. Protocol text **hold**.
- **F-0 per test:** skeleton = DEFERRED per-rule (method row, không có skeleton
  riêng; pre-registration ≥80% collision là prediction testable); payer =
  DEFERRED per-rule (khai từ chính nguồn, author win-rate không tính); 
  information = **PASS ở tầng route** — corpus dated-public-playbook là lớp
  nguồn PIT mới thật sự (available_at = platform publication timestamp), không
  tái dùng observable chết nào làm trigger.

**Điều kiện ràng buộc (binding, vi phạm = incident + entry invalid):**

- **C1** — corpus build CHỈ sau protocol freeze của council (K tác giả, N
  top-rules, windows pin tại protocol freeze) và sau GO; không lane nào build
  ad hoc.
- **C2** — từng RULE codify vào F-0 riêng (3 tests + anti-variant §2.3 merge)
  trước khi xét freeze; độ nổi tiếng của nguồn không miễn trừ.
- **C3** — số RULE trong cap ≤3 identity/pair; lựa chọn chỉ theo tiêu chí
  two-of-three distinctness đã khai trước.
- **C4** — truncation fixtures do PIT auditor xác minh (F-2 battery: truncation
  byte-identical + future-mutation + delay-pair Q-4); blind checklist của
  collector là cần nhưng không đủ.
- **C5** — ex-post recap + author-claimed outcome stats: ghi nhận, KHÔNG BAO
  GIỜ là bằng chứng premium (I001 §1.4 thành binding).
- **C6** — K-COST per-rule: geometry stop/target khai ra implying gross capture
  < RT ceiling tại horizon đóng băng ⇒ pre-dead ở F-0.

Generator tiêu 0 scored cell, 0 OOS look. Registry row khuyến nghị:
`FREEZE_ELIGIBLE (generator)` — scored surface chỉ tồn tại qua RULE sống F-0.

## 5. OPEN-CALL (slot 3)

Tại giờ tòa mở: thư mục `council/proposals/` chứa đúng `OPEN_CALL.md`,
`PROPOSAL_I001.md`, `PROPOSAL_I002.md` — **không có submission nào cho slot 3**.
Deadline của OPEN_CALL là "before the skeptic court convenes" ⇒ **slate đóng
TRỐNG, hợp lệ** (master §2: không nhồi identity cho đủ số; child plan §3).
Slot 3 = EMPTY, không consume gì.

## 6. Disk

- Trước staging skeptic: **5.72 GiB free** (6,140,817,408 B, statvfs; df -h
  5.7 GiB). Sau staging BTC 1m (135.3 MB): **5.56 GiB** (5,964,664,832 B).
  df cuối phiên: 5.6 GiB. Sàn 5.0 GiB **không bị vượt**; không `BLOCKED_STORAGE`;
  budget skeptic 150 MB respected (≤ 0.5 GB/staging của master §3.4).

## 7. Phán quyết tòa (final)

- **DTP-CX-SOLUSDT-I001** → `ELIGIBLE_FOR_FREEZE` **AS GENERATOR**, điều kiện
  C1–C6 binding; per-RULE F-0 subordination; 0 scored cell.
- **DTP-CX-SOLUSDT-I002** → **`KILLED_K-F0_K-COST_K-ANC`** — terminal pre-PnL.
  Ba luật độc lập: (i) F-0 information test fail có số (residual phút-kế
  median 0.00, mean ≤2.23 bps vs RT 11.92); (ii) `K-COST` ceiling×power grid
  rỗng ở mọi θ/multiplier/ladder/cơ-sở-power; (iii) `K-ANC` |rho| 0.23–0.51 vs
  momentum-sign gate ở mọi θ (0.21–0.41 vs SMA200 gate tại θ≥15). Khuyến nghị
  ghi family failure: `DTPCX1-I002-BTC-ALT-1M-LEADLAG` (revival conditions §2.5).
- **Slot 3** → `SLATE_EMPTY` (hợp lệ).

*Phiên tòa outcome-blind: không PnL, không sealed/holdout, không strategy code.
Mọi số tái lập bằng: `.venv/bin/python research/control/DTP-CX-SOLUSDT-C1/council/skeptic/scripts/skp_census_i002.py`.*
