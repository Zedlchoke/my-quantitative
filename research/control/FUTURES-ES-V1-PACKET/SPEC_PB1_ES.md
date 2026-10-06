# SPEC_PB1_ES — Executable specification (FREEZE-READY, OUTCOME-BLIND) — bản r3

- Cycle (planned): **FUTURES-ES-V1** — asset `futures` (ES-only). Plan:
  `research/control/FUTURES-ES-V1-PACKET/PLAN_futures_es_v1.md`.
- Spec trạng thái: **FREEZE-READY r3** (5 điểm review Co-Owner đã sửa ở r2;
  A7-SPEC verdict **FREEZE_READY_WITH_ERRATA** 0 BLOCKER/0 MAJOR/5 MINOR/7 NOTE
  — 5 MINOR đã áp ở r3 với nhãn [ERRATUM A7-SPEC-M*]; chờ owner GO + đăng ký). **Chưa có số PnL nào được
  tính**; mọi tham số chọn từ bằng chứng đo được/anatomy hoặc khai báo bảo
  thủ — không từ PnL đã thấy.
- Cơ sở: DATACONTRACT_QUALIFICATION (Bước 1 CLOSED_WITH_ERRATA) + r6 (D2/D3/
  D5/D6) + PLAYBOOKS_DRAFT r5 (A-r4). Phí: **MODELED COST** (owner chấp nhận;
  D2 account = NOT_RUN).

## 1. Universe & data contract (binding)

- **Chỉ ES** (E-mini S&P 500, CME; mult 50, tick 0.25 = $12.50). NQ và các mã
  khác ngoài cycle.
- Dữ liệu: Databento GLBX ohlcv-1m per-contract 2010-06→2026-10 (root vật lý
  không dấu chấm; PATH LAW), schema D5 (fixed-point 1e-9; **ts_event = mốc
  BẮT ĐẦU bar**; **lọc `raw_symbol` chứa `-` bắt buộc**; deferred 2027 tails
  loại bằng floor ≥100k).
- Session clock **era-correct** (đo): close 16:30 CT (→2012) → 16:15 CT
  (2013→2015-11) → 16:00 CT (từ 2015-11/2016); break-tail pre-2016 tách riêng.
- **Roll T-5 — luật expiry PIT (sửa review điểm 4, không lookahead)**:
  expiry(t) = **quy tắc công khai tính-được-từ-trước**: thứ 6 tuần thứ 3 của
  delivery month, **[ERRATUM A7-SPEC-M2] dịch chuyển CHỈ nơi CME thực sự đã
  dịch: 2026-06-18 và 2027-06-17 (Juneteenth); June-2021 KHÔNG dịch dù liên
  bang quan sát — lịch dịch liệt-kê theo CME, không suy từ lịch liên bang;
  66/66 bars-validated**. Quy tắc CHỈ dùng lịch công khai —
  **KHÔNG dùng "last session with volume" làm luật** (đó là thông tin tương
  lai tại thời điểm quyết định; bars chỉ dùng để VALIDATE). Roll = chuyển tại
  close của phiên T-5 tính từ expiry theo quy tắc.
- **Validation bắt buộc tại freeze** (bảng, deterministic): (a) đối chiếu
  quy tắc vs **D3 authority expiry calendar — [ERRATUM A7-SPEC-M1] 37/68 quý
  ARCHIVED_OFFICIAL được liệt kê, 36 nằm trong cửa sổ eval 2010-06..2026-09**;
  (b) đối chiếu quy tắc vs expiry đo từ bars (dossier ES §1: 66/66 = 3rd
  Friday, ngoại lệ duy nhất ESM6-Juneteenth đã encode). **Quý nào lệch bất kỳ
  nguồn nào ⇒ EXCLUDE TOÀN QUÝ** khỏi evaluation (không chỉ 2 session quanh
  roll). Quý không có authority D3: quy tắc đứng nhờ **validation (b), cộng
  (a) nơi có authority [ERRATUM A7-SPEC-N4]** — A7-SPEC đã adjudicate R4:
  **PIT-LEGAL; authority-less quarters ALLOWED-with-validation**; bất kỳ
  mismatch nào ⇒ EXCLUDE TOÀN QUÝ (fail-closed).
- **C_prev**: close THỰC TẾ của session liền trước đúng mốc era; session liền
  trước short/holiday ⇒ `prev_short` flag; không chắc ⇒ EXCLUDE.
- IBKR daily closes = settlement marks (D5: 96/96 tick-exact) — chỉ tham
  chiếu, không bao giờ fill price.

## 2. EXCLUDE rules — D3 authority (deterministic; A7 adjudicate coverage)

- **E1 (ngày — sửa review điểm 5)**: session-day bị loại nếu trạng thái
  holiday/early-close **ES-cụ thể** KHÔNG được chứng minh từ bộ r6 ở mức
  từng-ngày: (i) 2026 LIVE_OFFICIAL (trang chung + pattern ClearPort/equities
  — ES-specific Globex times NOT_OBTAINED ⇒ mọi ngày 2026 có early-close
  nghi vấn mà không xác minh được giờ ES ⇒ EXCLUDE); (ii) 2010 PDF chính thức
  (per-day/per-time Equity family); (iii) 2011-2025 ARCHIVED_OFFICIAL: **cửa
  sổ holiday chung CME chưa tự chứng minh early-close-time ES từng ngày —
  A7 phải adjudicate từ `analysis/d3_cmecalendar/` xem coverage thật tới đâu
  (per-day ES times vs chỉ window-level)**; mọi ngày không chứng minh được
  ES-specific ⇒ **EXCLUDE** (mặc định fail-closed). Exclude-list liệt kê
  tường minh từng ngày + lý do.
- **E2 (quý/roll)**: như §1-validation — quý lệch nguồn hoặc adjudicated
  chưa đủ ⇒ **EXCLUDE TOÀN QUÝ**.
- **E3 (2026 bounds)**: session bounds 2026 lấy từ bars; mâu thuẫn với bảng
  LIVE_OFFICIAL chung ⇒ EXCLUDE session.
- **E4**: prev-session không chắc ⇒ EXCLUDE (tín hiệu); `prev_short` vào
  sensitivity, không phải EXCLUDE.
- **E5**: strays/dash/break-bars loại theo DATACONTRACT §1.6.
- Exclude-list sinh bằng script deterministic tại freeze; sha256 vào selection
  freeze; không sửa sau GO.

## 3. Tín hiệu & arms (không chọn hậu nghiệm)

- m = log(open_0830 / C_prev); điều kiện |m| ≥ q80(|m|, trailing-252d,
  strict-past) — q80 từ anatomy (NQ dossier H4 refined spec; ES §8-H5), không
  tune. Arms **CONT** (sign(m)) và **REV** (−sign(m)) đăng ký đồng thời; tail
  UP/DN đều vào. Warmup 252 session.
- **Standing outside [ERRATUM A7-SPEC-M3]**: **MỌI ngày có statement FOMC
  base-EXCLUDE ở cấp NGÀY** (132 statements 2011-2026, gồm 40 untimed
  2011-2015 — ngày công khai day-level, loại theo ngày an toàn thời gian);
  FOMCIN arm = tập INCLUDE ngược. Coverage **RTH-core [ERRATUM A7-SPEC-M4] =
  tỷ lệ phút 08:30–15:00 CT có bar (close era-correct)** <60% ⇒ EXCLUDE; E1-E5.

## 4. Entry/exit/fills (conservative fill law)

- Entry: bar 1m đầu 08:30 CT (D0) hoặc 09:00 CT (D30) theo hướng arm; **fill =
  open bar 1m kế tiếp**. Không claim limit/queue (D5).
- TP = 2.0 × SL-distance; **[ERRATUM A7-SPEC-M5] SL = 1.0 × median của 20
  range RTH session liền trước (strict past; close marks era-correct; loại
  session short/flagged)** — frozen a priori, R=2 (không dùng tên ATR/Wilder).
- **Same-bar TP/SL**: bar chạm cả hai ⇒ **SL ưu tiên** (giá xấu hơn), deterministic.
- Time exit: close RTH **era-correct** — flat bắt buộc, không giữ qua đêm.
- Sizing: 1-2 hợp đồng (margin ~$29k/ct; tham chiếu 100k; 4× coverage); risk
  0.5%/lần [freeze tại GO].

## 5. Chi phí MODELED COST (per side, USD) — sửa review điểm 2+3

| thành phần | giá trị | nguồn/giới hạn |
|---|---|---|
| Commission IBKR | 0.85 | Fixed plan (LIVE_OFFICIAL 2026-10-03) — hàng bảo thủ nhất bảng public (tiered thấp hơn chỉ giảm chi phí); **plan/tier account KHÔNG BIẾT (D2 NOT_RUN)** |
| Exchange (CME) | 1.386 | public LIVE_OFFICIAL (IBKR CME.php offset table); **current-as-approximation mọi năm lịch sử** |
| Regulatory (NFA) | **0.02** (mặc định); **0.01** cho 2014-10-01→2017-12-31 | **timeline chính thức NFA (LIVE_OFFICIAL) — dùng MỘT nguồn duy nhất**; **IBKR offset 0.011 KHÔNG dùng, KHÔNG cộng kèm** (tránh trùng/giả hợp hai nguồn của cùng một khoản) |
| Spread half-turn | 6.25 | close-proxy (median full-spread 1.0 tick, reproduce exact r6) — proxy, không phải BBO measured |
| Slippage tier | **S1/S2/S3 = 12.50/25.00/37.50** (1/2/3 tick × $12.50) | **GIẢ ĐỊNH NGHIÊN CỨU (D1)** |
| **All-in/side (mặc định NFA 0.02)** | **S1 21.006 · S2 33.506 · S3 46.006** | cửa sổ 2014-10-01→2017-12-31 trừ 0.01 (NFA 0.01); round-trip ×2 |

- **Ghi chú bias (điểm 3)**: biểu lịch sử per-year NOT_OBTAINABLE (D2 r6: PDF
  CME 2020/2025/2026 có nhưng không trích được cell) ⇒ current-as-
  approximation; **KHÔNG khẳng định chiều thiên lệch**. NFA là thành phần duy
  nhất điều chỉnh theo năm (timeline chính thức). [NOTE A7-SPEC-N1] NFA 0.02
  từ 2018-01-01 tựa filing chính thức cuối (2017, open-ended); mirror chưa
  kiểm chứng nói 0.01 từ 2026-07-01 — KHÔNG adopt (0.02 = bảo thủ chi phí cao
  hơn). [NOTE A7-SPEC-N3] approximation known-wrong theo ≥2 cách đã ghi
  (timeline NFA — đã xử lý; lead chưa fetch về CME tăng giá) — không nêu hướng.

## 6. Trial identities — A-r4 đúng 24, liệt kê tường minh (sửa review điểm 1)

**Primary 16 = hai họ con, KHÔNG phải full grid 2×2×2×3=24:**

| họ | pattern | n |
|---|---|---|
| P-A (cặp delay tại S2) | `FBES1-PB1-{CONT,REV}-{UP,DN}-{D0,D30}-S2` | 8 |
| P-B (hai tier ngoài tại D0) | `FBES1-PB1-{CONT,REV}-{UP,DN}-D0-{S1,S3}` | 8 |

| nhóm khác | IDs | n |
|---|---|---|
| FOMC sensitivity | `FBES1-PB1-{CONT,REV}-{UP,DN}-D0-S2-FOMCIN` | 4 |
| C1 placebo | `FBES1-PLA-D0-S2` (seed 20261002; đơn seed đơn delay — giới hạn công bố, không claim permutation robustness) | 1 |
| C2 baseline | `FBES1-ALW-D0-S2` | 1 |
| C3 anchor | `FBES1-FLAT` | 1 |
| C4 dose-response | `FBES1-DOSE-D0-S2` | 1 |
| **TỔNG** | | **24** |

(Ô D30×{S1,S3} và các tổ hợp ngoài hai họ trên **không tồn tại** trong cycle
này — mở rộng = owner amendment + re-check trần.) Mọi identity đã chạy vào
observed denominator; era-checks = evaluation views; fold nhân evaluation
không nhân identity.

## 7. Folds & evaluation

- 4 folds tuần tự: F1 2010-06..2012-12 · F2 2013-01..2017-12 · F3
  2018-01..2021-12 · F4 2022-01..2026-09 (sau EXCLUDE). K1 đo trên 3 era
  OVN-share 2010-16/2017-21/2022-26 (views).
- **S1 = SEALED_UNTOUCHED** (prospective post-freeze mặc định).

## 8. Stage-A gates (pre-registered; per identity)

G1 after-modeled-cost expectancy > 0 tại S2 (và S1) · G2 PF ≥ 1.10 tại S2 ·
G3 ≥ 2/4 folds positive tại S2 · G4 K1 era-sign ổn định · G5 K4 D0/D30 không
đổi dấu (trong họ P-A) · G6 K3 <80% đóng góp trong 2020-03..04 · G7 arm vượt
C2 và C1 về after-cost expectancy tại S2 (không vượt ⇒ "no conditioning
information") · G8 repro byte-match · G9 A7 0 HIGH/CRITICAL unresolved. K2:
CONT và REV đều dưới sàn ⇒ family dead, cấm re-tparam. K5 không áp dụng.

## 9. Terminal outcomes (pre-decided)

`FUTURES_ES_V1_REJECT_ALL` · `FUTURES_ES_V1_NO_ELIGIBLE_IDENTITY` ·
`FUTURES_ES_V1_SURVIVOR_PENDING_S1` · `FUTURES_ES_V1_BLOCKED_<reason>`.
Không promotion/paper/live trong cycle này.

— Hết SPEC_PB1_ES r3. Freeze = spec sha + exclude-list sha + bảng identity
sha, ghi vào selection freeze tại đăng ký.
