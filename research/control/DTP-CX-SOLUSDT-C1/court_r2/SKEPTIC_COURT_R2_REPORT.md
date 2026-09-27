# SKEPTIC COURT R2 REPORT — DTP-CX-SOLUSDT-C1 (F-0 court, vòng 2: adjudication 5 lớp RULE từ corpus I001)

- Lane: `skp-r2` · Vai trò: economic skeptic (VETO pre-PnL) · Họp: 2026-09-27 (UTC)
- Cycle: `DTP-CX-SOLUSDT-C1` · Cha: `DAYTRADE-PLAYBOOKS-PROGRAM-V1`
- Worktree HEAD tại giờ tòa: `e23ff983ea69ae8d39c8c50bd70c882352ab50db`
  (branch `orca/dtp-cx-solusdt-c1-integration`); KHÔNG commit (lane write-only).
- Tiền lệ trực tiếp: `council/skeptic/SKEPTIC_COURT_REPORT.md` (R1 — I001
  ELIGIBLE_AS_GENERATOR với điều kiện C1–C6; I002 KILLED; tòa R2 này là bước
  C2 của R1: **mỗi RULE codify đi vào F-0 riêng**).
- Machine artifact: `court_r2/court_r2_machine@1.json` (mọi family_id được
  kiểm tra tồn tại đúng 1 lần trong `research/wayfinder/FAMILY_FAILURES.jsonl`
  — 137 rows, sha-pinned trong machine JSON).

> **Chưa có PnL nào được xem hoặc tính toán cho identity nào trong phiên tòa này.**
> Tòa R2 thuần PHÂN TÍCH: không load panel giá, không chạy measurement nào,
> không viết strategy code. Toàn bộ by-kill là **family đã chết CÓ ĐO** được
> cite bằng `family_id` chính xác hoặc class-death neo-MAP.

---

## 0. Tóm tắt phán quyết

| # | Lớp (rank corpus) | Setups | F-0 skeleton | Payer | Information | Verdict |
|---|---|---|---|---|---|---|
| 1 | RC-01 RANGE_FADE (row 7) — E01, E05, E08, E10 | 4 | **TRÙNG** family fade-tại-biên đã đo chết | FAIL (không có bên trả bắt buộc) | FAIL (state tự sinh từ price; "edge" đo được duy nhất = PIT seam) | **F0_KILLED** (4/4 rules) |
| 2 | RC-02/RC-05 BREAKOUT_CONTINUATION (row 1/2) — E04, E07-approx, E09, E11 | 4 | **TRÙNG** family continuation level-break đã đo chết cả 2 chiều, mọi gate | FAIL | FAIL (forensic: không có at-entry PIT state tách regime) | **F0_KILLED** (4/4; E07 dạng-OI thêm NOT_CONSTRUCTIBLE) |
| 3 | RC-03/RC-04 TREND_PULLBACK (row 4) — E02, E06 | 2 | **TRÙNG** continuation re-gate (gate không load-bearing — đo) | FAIL (E02 không khai payer; E06 lore) | FAIL (trend nằm trong lớp Q-7 loại) | **F0_KILLED** (2/2) |
| 4 | RC-07 PATTERN_REVERSAL_LEVEL (row 9) — E12 | 1 | **TRÙNG** breakdown-continuation short (đảo nhãn/kick tên của row 1; cả 2 nhánh fork đều chết có đo) | FAIL | FAIL | **F0_KILLED** (1/1) |
| 5 | RC-06 NEWS_FADE (row 8) — E03 | 1 | BLOCKED_DATA (lịch PIT event không tồn tại trên plane này) | MOOT | MOOT | **DATA-GATED + DEAD-COLLISION** (kép) |

**Survivors: 0 / 11 RULE constructible** (E03 bị chặn dữ liệu, không đếm là
survivor). Kỳ vọng pre-registered của proposal (≥80% chết collision) được đo
thực tế ở **100%** — không force-kill: mỗi rule chết vì khớp skeleton
(trigger/direction/exit sau khi bỏ observable đặc thù) với một family có
bằng chứng đo chết; không rule nào bị giết chỉ vì "nổi tiếng" hay vì phán
quyết tiền-council của Bảng 1.

---

## 1. Nguyên tắc phiên tòa R2 (tự phái sinh, không sao chép phán quyết Bảng 1)

1. **Skeleton test** (master §2.2-1): bỏ observable đặc thù của rule, giữ
   trigger/direction/exit shape. Còn lại trùng shape với một family trong
   `FAMILY_FAILURES.jsonl` (hoặc class-death neo-MAP) = trùng family chết.
2. **Payer test** (§2.2-2): ai trả, vì sao họ BẮT PHẢI trả. Câu chuyện payer
   trong nguồn được ghi là **lore** (manifest field `claims`); lore không phải
   cơ chế ép trả. Không có cơ chế ép trả + fill có điều kiện chọn ngược = 
   fictional-counterparty exposure (tiền lệ BTC-BEAR: VETOED_FICTIONAL_COUNTERPARTY).
3. **Information test** (§2.2-3, Q-7): thông tin nào KHÔNG có trong
   clock/trend/spread. State tự sinh từ chính klines (range, pivot, VWAP,
   volume, MA, neckline) = trend/price-geometry — nằm trong lớp bị loại.
4. **Anti-variant §2.3**: rename / đảo chiều / thêm-bớt gate khi giữ
   trigger-direction-exit + payer / re-clock / đổi session-pair giữ skeleton
   ⇒ MỘT identity với family đã chết. Hai identity khác nhau phải khác ≥2/3
   (payer, information-layer, risk-shape).
5. **Không force-kill, không rescue**: rule nào không khớp family chết nào
   phải được cho sống (`ELIGIBLE`) kèm lý do; equally không cứu rule trùng
   family chết bằng cách đổi nhãn.

Minh bạch: kết luận của tòa hội tụ với phán quyết tiền-council của Bảng 1
(rows 1/4/7/8/9 DEAD) nhưng **mỗi verdict dưới đây đứng trên chuỗi bằng chứng
riêng**; nơi tòa **khác** cách Bảng 1 dẫn chứng thì ghi rõ (mục 5 — row 9).

---

## 2. Lớp 1 — RC-01 RANGE_FADE (row 7; 4 authors: E01 Phemex, E05 Kraken, E08 LiteFinance, E10 Binance)

**Skeleton codify được từ nguồn** (RULE_CANDIDATES §RC-01): range state = 
min-low/max-high của W bar đóng trước; trigger = bar đóng chạm biên; entry ở
quote giao dịch được đầu tiên sau đóng bar; stop ngoài range; exit = biên đối
diện. E05 (sub-variant): thêm state RSI≤25 + pierce lower Bollinger trong
range; exit = quote đầu tiên trở lại trong range.

**Skeleton test — TRÙNG.** Bỏ observable đặc thù (độ rộng W, band, RSI, BB,
POC): còn lại *giá chạm mức sinh từ cực trị gần nhất → vào NGƯỢC chuyển động
gần nhất → thoát khi giá hồi về trong khung, stop sau cực trị*. Đó chính là
range-edge/mean-reversion fade:

- `FXOS-04` (EURUSD-OPEN-SEARCH-V1, HOLDOUT_FAILURE_NO_RESCUE): Bollinger
  fade 15m — dev PF 1.1445 → **holdout PF 0.9816**, −585 pips @1.5×; 5/48
  dev-positive trials, survivor duy nhất chết OOS = selection luck. Khớp
  trực tiếp sub-variant E05 (band-fade).
- `TRACKA1-M1-RANGEFADE-PIT` (ERP1-TRACKA-C1, KILL_PIT_SEAM): fade prev-day
  H/L PIT-clean ra **PF 1.0334/1.0509, chết @1.5×** trong khi twin
  lookahead-1-ngày pass cả 8 gates — toàn bộ "edge" nhìn thấy được của family
  này là một **data seam**, không phải thông tin.
- `TRACKA2-C1C2C3-REGATED-RANGEFADE` (cohort-2, VARIANT_SAME_FAMILY): các
  biến thể *có gate* (provenance/retest/probe) suy biến về đúng dead law khi
  bỏ gate — lần adjudication đầu của owner law "adding an observable is not
  a new mechanism". **Áp trực tiếp lên E05**: bỏ RSI+BB còn lại đúng dead law
  RANGEFADE; gate không load-bearing.
- `A6-V16-F1` CLOSE-DISPLACE-FADE (CRYPTO-V16, PF_BELOW_THRESHOLD razor
  PF 1.06356 + fold-conc 1.0 + MDD over ceiling): side crypto đã đo chết
  riêng dạng displacement-fade.
- `mean-reversion-transfer` (SPRINT-CRYPTO, RULE_TRANSFER_FAILED):
  **Bollinger+RSI frozen-rule** transfer sang 6 altcoins chết — đúng cặp
  indicator của E05, trên đúng asset class.
- Neo-MAP: VIABILITY cohort-3 (0/12 class FX sống) — "mean-reversion
  oscillators" và "range-edge fade mọi gate" là 2 trong 12 lớp chết; 
  `SRLVCX1-M1-SETTLE-RESOLVE` đo absorption/fade-at-level chết CẢ 2 chiều.

**Payer test — FAIL.** Bốn story từ nguồn (E01 "exit before the crowd at
$1,600"; E08 "market makers profit from spreads"; E10 momentum entrants;
E05 "overextended sellers") đều là lore, không có ai BẮT BUỘC giao dịch với
fader tại giá của fader: đám đông tại biên có thể không fill bạn (fill của
bạn tại biên có điều kiện ngược — adversely selected). Không có cơ chế ép
trả ⇒ không qua (tiền lệ BTC-BEAR).

**Information test — FAIL.** Range/band/RSI/BB/POC toàn bộ tự sinh từ chính
klines (lớp trend/price-geometry Q-7 loại). Không có lớp thông tin ngoài; và
bằng chứng đo cho biết khi family này *có vẻ* có thông tin, đó là seam
(TRACKA1-M1).

**Verdict per-rule:** `RC-01-E01`, `RC-01-E05`, `RC-01-E08`, `RC-01-E10` →
**F0_KILLED** (`K-F0` skeleton collision; payer + information FAIL). K-COST
không bắn ở geometry source-stated (capture khai vài %, ≥ 23.84 bps) — tường
binding là F-0, đúng như RULE_CANDIDATES đã khai.

---

## 3. Lớp 2 — RC-02/RC-05 BREAKOUT_CONTINUATION (row 1, E09 row 2-adjacent; 4 authors: E04 Kraken, E07 LiteFinance, E09 CryptoCred, E11 Phemex)

**Skeleton codify được**: range consolidate từ bar đóng → bar đóng vượt cực
trị (+ state volume ≥3× trung vị / TMF>0 / volume-only cho E07-approx / bias
HTF cho E09) → entry cùng chiều phá ở quote đầu tiên sau đóng bar → stop sau
mức/cấu trúc → exit level kế / volume-taper / giữ trend-day (E09).

**Skeleton test — TRÙNG.** Bỏ gate volume/flow/bias: *level-break → vào cùng
chiều → ride continuation*. Đã đo chết nhiều lần độc lập, cả 2 chiều:

- `PSV1-BTC_H1-UPTREND-BREAKOUT_CONT` (PHASE-STRATEGY-V1): net dương
  (+89,637) nhưng **G3 FAIL — ALWAYS_ON_LONG out-earns 4.8×, G5 conc 0.854**:
  cả phần lời là BTC beta trá hình, gate không mang thông tin.
- `PSV1-BTC_H1-DOWNTREND-BREAKDOWN_CONT`: **CONTROL_OUTEARNED** — control
  phase-shuffled out-earns; chiều short của cùng skeleton chết (che trước
  phép "đảo chiều = rule mới").
- `PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION`: **control block-shuffled gate
  EARNS MORE** (+190,392 vs +177,692) — timing của gate continuation không
  mang thông tin; `ES1-*`/`BRV1-RISK-OVERLAY` chốt thêm G5 structurally
  unpassable cho BTC-long window này.
- Forensic `BTC-H4-CONTINUATION-V2` (MAP, terminal c390375e): losses GROSS,
  entry cơ học giống hệt across folds, **KHÔNG có at-entry PIT state nào tách
  được regime**; min-hold được đo vô tội. Đây là kill information-test của
  cả lớp: không tồn tại state-vào-lệnh nào biết được break nào follow-through.
- `H-VOLCOMP-BRKOUT-v1` (SPRINT-CRYPTO): compression→breakout markup-only —
  **26/28 cells negative**. Khớp trực tiếp E04/E07/E11 (consolidation→break).
- `V17-a5-P1-ATTN-PHASE`: SOL US-session attention continuation — chết G1
  (expectancy −0.001716/day) ngay gate đầu. **Kill theo-pair (SOL) cho mọi
  biến thể session-continuation.**
- FX context: `FXFV1-A3-P1` London-open session continuation
  (EXPECTANCY_NONPOSITIVE, PF 0.849); `FXFV2-A4-P1` Tokyo-compression→
  London-expansion (chết, gross đã âm −0.40 bps break-even); VIABILITY:
  "momentum/continuation mọi cadence" + "fix-window/clock/calendar" là lớp chết.
- **E09 (RC-05, DO-reclaim):** DO = 00:00 UTC open — giá mở của bar đầu ngày,
  tự sinh từ chính klines tại mốc clock. Bỏ clock: bias-continuation entry =
  dead class. Giữ clock: "đổi session giữ nguyên skeleton" là anti-variant
  §2.3; "fix-window/clock/calendar" là lớp chết VIABILITY. Không có lối sống.

**Payer test — FAIL cả 4.** E04 "pent-up pressure released / late chaser
pays"; E11 "breakout doubters pay"; E07 (lore nội nguồn) "false breakout
caused by a liquidity sweep" — người bị stop-run trả (chính là lore row 9
rò sang row 1 — payer story tự mâu thuẫn trong cùng nguồn); E09 **không khai
payer** (NOT_STATED_BY_SOURCE). Không ai BẮT BUỘC chaser phải mua tại giá
entry của bạn; chaser là tự nguyện và adversely selected. FAIL.

**Information test — FAIL.** Volume/TMF là state cộng thêm từ chính
klines (P-27: adding an observable is not a new mechanism — đo tại PSV1 G6:
shuffle gate giữ nguyên occupancy mà control out-earns). Thông tin mà lớp
cần — "break này có follow-through không" — forensic BTC-H4-CONTINUATION-V2
đã đo: **không có at-entry PIT state nào tách được**. FAIL có đo.

**Verdict per-rule:** `RC-02-E04`, `RC-02-E07-approx`, `RC-05-E09`,
`RC-02-E11` → **F0_KILLED**. Ghi thêm honest: E07 dạng-OI nguyên văn
NOT_CONSTRUCTIBLE trên plane klines đóng (OI là data layer futures; multi-year
OI lịch sử không có — BLOCKED_UNCONSTRUCTIBLE theo bear-recon); chỉ approx
volume-only nhập F-0 và chết với lớp.

---

## 4. Lớp 3 — RC-03/RC-04 TREND_PULLBACK (row 4; 1 author, 2 setups: E02, E06 Kraken)

**Skeleton codify được**: E02 — trend state (≥2 HH+HL bar 1h đóng) → entry
at-market sau bar confirm → stop dưới swing low → BE → exit lower-low ngược
trend. E06 — session VWAP (00:00 UTC) + volume-node confluence → pullback bar
đóng vào vùng → limit tại node → stop dưới node → exit khi giá rời vùng.

**Skeleton test — TRÙNG (continuation re-gate).** Bỏ gate pullback
(VWAP/node/swing-state): *entry theo hướng trend intraday, exit theo trend*.
- `TRACKA2-P3B-DINV-1D` (ANCESTRY_RHO_BLOCK): "1-day continuation gated by
  quote-liquidity state **is measured to BE** the dead H1 momentum/donchian
  class at day cadence; **the ancestry is in the continuation leg, not the
  gate**" — rho 0.3032/0.3103 vs `FX2-H1TSMOM`/`FX2-H1DONCH` (lớp
  momentum/continuation). Gate pullback không cứu được vì ancestry nằm ở
  chân continuation.
- VIABILITY cohort-3: "momentum/continuation mọi cadence" — lớp chết trọn.
- `PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION` + forensic
  BTC-H4-CONTINUATION-V2 (mục 3): trend-gated continuation, control out-earns,
  không có state tách regime.
- Corroboration: `PSV1-BTC_H1-ACC-FLOOR_PROVISION` — phase-gated dip-buying
  (họ "mua nhịp lùi trong uptrend") earn nhưng **không bao giờ thắng
  hold-only BTC** sau cost: gate dip = beta trá hình.
- Riêng thành phần VWAP của E06: session-clock statistic + volume histogram —
  tất cả từ klines + clock; "clock/calendar" là lớp chết VIABILITY; thêm
  VWAP/node = P-27 observable.

**Payer test — FAIL.** E02: nguồn **không khai payer** (đã flag trung thực
trong RULE_CANDIDATES) — fail mặc định, và story constructed nào cũng đụng
fictional-counterparty veto. E06: "institutional levels provide the bounce;
VWAP widely used among institutions" — lore; institution dùng VWAP làm
benchmark không tạo nghĩa vụ phòng thủ mức; không ai BẮT BUỘC mua tại node
khi fader đứng chờ. FAIL.

**Information test — FAIL.** Trend state, swing, VWAP, volume-node: toàn bộ
tự sinh từ klines + clock — đúng các lớp Q-7 loại (clock/trend). FAIL.

**Verdict per-rule:** `RC-03-E02`, `RC-04-E06` → **F0_KILLED**
(skeleton = continuation re-gate; DINV-1D là kill dẫn chứng chính).

---

## 5. Lớp 4 — RC-07 PATTERN_REVERSAL_LEVEL (row 9; 1 author: E12 Bybit H&S)

**Skeleton codify được** (§RC-07): 3 pivot high (head cao nhất, shoulders
ngang), neckline qua 2 pivot low (có thể nghiêng); pre-condition prior
uptrend (MA state); **signal = bar đóng close dưới neckline; entry SHORT ở
quote đầu sau bar đóng đó**; stop trên head; target = measured move
(neckline→head trừ vào giá break).

**Suy luận từng nhánh như dispatch yêu cầu:**

- **(a) Có phải breakdown-continuation (row 1 đảo) không? CÓ — đây là nhánh
  đúng của fork.** Trigger = close dưới một mức sinh từ bar đóng; direction =
  **cùng chiều phá** (short); exit = fixed measured target; stop sau cấu trúc.
  Sau khi bỏ observable đặc thù ("neckline nghiêng qua 2 pivot + pattern
  3 đỉnh"), còn lại *đúng* shape `PSV1-BTC_H1-DOWNTREND-BREAKDOWN_CONT`
  (short breakdown continuation — đã đo **CONTROL_OUTEARNED**: control
  phase-shuffled out-earns, gate timing mang giá trị âm) và shape
  `markdown-breakdown-short` (SPRINT — fold-concentration kill) và
  `H-VOLCOMP-BRKOUT-v1` (26/28 negative). Rename ("neckline" thay "range
  low") + thêm gate (pattern state + MA prior-trend) = đúng các khác biệt
  liệt kê trong anti-variant §2.3 (rename; thêm gate).
- **(b) Có phải sweep-then-absorption SRLVCX1-M1 (level-then-reversal) không?
  KHÔNG.** M1 là *fade-at-level* (vào NGƯỢC sau sweep); E12 vào **CÙNG chiều**
  break. Khác trigger-direction. (Ghi chú trung thực: `SRLVCX1-M1-SETTLE-
  RESOLVE` chết cả 2 chiều với inverted out-earns — tức cả nhánh absorption
  lẫn nhánh continuation tại level đều đo chết — nhưng E12 không phải instance
  của skeleton đó vì không có settlement-window/sweep-state.)
- **(c) Có phải skeleton mới không? KHÔNG.** Khác biệt ứng viên duy nhất so
  với dead breakdown-continuation: (i) mức là đường nghiêng qua 2 pivot thay
  vì extreme ngang — cùng PIT layer (klines), vẫn là "mức từ bar đóng";
  (ii) target = measured-move thay vì trail/next-level — khác biệt **risk
  shape**, đúng 1/3 tiêu chí. Anti-variant §2.3 đòi ≥2/3 (payer, information,
  risk-shape): payer story (trap-bulls trả) không có cơ chế ép trả — cùng
  problemi payer với lớp đã chết; information layer cùng (klines). 1/3 ⇒
  MỘT identity với family chết.
- **Fork "failed-breakout":** nếu ai re-label E12 sang dạng failed-breakout
  (break rồi đóng ngược lại trong range, fade) — đó là đảo nhãn của row 1 và
  thuộc family fade-at-level: `TRACKA2-C1C2C3-REGATED-RANGEFADE` (class
  closed against gated variants), `A6-V16-F1` (crypto displacement fade),
  `V17-A6-P2-OICASCADE` (exhaustion/reversal event: **sham event-time
  out-earns anchor** + fold-negative-majority). **Cả hai nhánh của fork đều
  chết có đo — labeling không tạo ra nhánh sống.**
- **Ghi nhận khác biệt so với dẫn chứng của Bảng 1** (minh bạch): Bảng 1
  pre-judge row 9 chủ yếu qua nhánh "failed breakout = đảo nhãn row 1" +
  SRLVCX1-M1. Tòa R2 xác định E12 **như codify không phải failed-breakout
  mà là with-break continuation short** — kill đúng luật là
  `PSV1-BTC_H1-DOWNTREND-BREAKDOWN_CONT` (continuation branch), không phải
  absorption branch. Verdict không đổi (cả 2 nhánh chết), nhưng chuỗi
  citation cho ledger dùng đúng nhánh.

**Payer test — FAIL.** "Trapped bulls at the neckline retest pay the
breakdown entrant"; "one of the most reliable patterns" — lore + claim
(manifest đã ghi `claims`), retest là tự nguyện, không có cơ chế ép trả.

**Information test — FAIL.** Pattern state, neckline, MA, measured move: toàn
bộ từ klines. Forensic PSV1 (shuffle gate out-earns; không có state tách
regime) phủ trực tiếp loại "pattern gate biết được điều gì klines không biết".

**Verdict per-rule:** `RC-07-E12` → **F0_KILLED** (skeleton = breakdown
continuation short, rename+gate-add variant của row 1; risk-shape khác biệt
1/3 — không đủ tách identity).

---

## 6. Lớp 5 — RC-06 NEWS_FADE (row 8; 1 author: E03 Kraken) — **phán kép**

**(1) BLOCKED_DATA — khẳng định lại, có lý chính xác:** trigger của rule đòi
biết *sự kiện tin tức nào xảy ra lúc nào với `available_at` THẬT* (PIT event
calendar có revision). Plane được stage cho SOLUSDT (FREEZE_R1: klines 1m/15m,
mark/index, bookTicker 6 tháng, funding) **không có event calendar**; protocol
§1.5-4 + master §4.2 cấm proxy. Lưu ý quan trọng: một "proxy klines"
(spike-then-stabilize không biết event) **không phải chỉ là thiếu dữ liệu —
nó là phép thay thế bị cấm**, và nó đồng thời biến rule thành vol-shock
re-label — đúng lớp đã chết (xem (2)). BLOCKED_DATA là phán đúng và đủ.

**(2) DEAD-COLLISION — lớp event/macro chết có đo, cả 2 track:** ngay cả khi
lịch PIT tồn tại, lớp này đã bị đo chết nhiều lần độc lập:
- Crypto event-instant: `CNG1-A4-P1` (FOMC-instant, ANCESTRY_RHO_BLOCK
  **0.4409 vs generic_dvol_shock** — event book chính là vol-shock shadow),
  `CNG1-A4-P2`, `CNG1-A5-P1`, `CNG1-A5-P2`; `CNG2-A4-P1/P2`, `CNG2-A5-P1/P2`
  (CPI/NFP-instant); `V17-A6-P1-FUNDJUMP` (announcement-jump: carries the
  forbidden level, rho 0.2439).
- FX event: `FXNG1-A5-P1`, `FXNG1-A4-P2`, `FXNG3-*` (4 arms), `FXNG4-*`
  (4 arms); `FXFV5-A6-P1-pre-release-avoidance` (**+7d SHAM-CALENDAR
  out-earns anchor** — conditioning lịch mang thông tin ÂM), `FXFV6-A4-P1`
  (CPI direction: sham control ÂM nhưng anchor chết robustness — PF razor
  1.0979 + concentration + break-even; không cứu được), `FXFV7-A4-P1`
  (sham ≈ anchor — không incremental info); RATES/COMM NG1: release-clock
  control out-earns. VIABILITY: "event/macro" là 1/12 lớp chết.
- **Riêng hướng fade**: skeleton proxy-stripped (spike → stabilize → fade
  ngược) = displacement fade — đã đo chết crypto-side ở `A6-V16-F1` (PF razor)
  và ở lớp fade (mục 2).

**Payer/information — MOOT** cho cửa freeze (không constructible), ghi nhận
nguồn: "early buyers take profits" = lore; không cơ chế ép trả.

**Verdict per-rule:** `RC-06-E03` → **DATA_GATED + DEAD_COLLISION** (kép, như
dispatch nghi ngờ). Không phải survivor; không hồi sinh khi chỉ nâng budget
dữ liệu trừ khi owner mở R5-class event authority VÀ proposal mới qua F-0 mới
toàn phần — revival clause ghi ở machine JSON.

---

## 7. Anti-variant merge check GIỮA 5 lớp (mục 6 của dispatch)

Không lớp nào sống nên merge-law không thay đổi verdict nào; tuy nhiên để
ledger sạch, tòa ghi cấu trúc gộp:

- **RC-07 (H&S) GỘP vào family RC-02/05** (breakdown-continuation): khác
  nhau bởi rename-level + gate-add + risk-shape 1/3 ⇒ MỘT identity class theo
  §2.3 (đã lập luận ở mục 5).
- **RC-03/04 (pullback) GỘP vào chân continuation của RC-02/05**: gate
  pullback không load-bearing (DINV-1D đo: ancestry nằm ở chân continuation).
- **Phần constructible của RC-06 (bỏ event-conditioning) GỘP vào RC-01**
  (displacement fade; V16 đã đo đúng skeleton đó).
- Kết quả: 5 lớp corpus **suy về 3 skeleton-family**: (i) fade-tại-biên
  (RC-01 + RC-06-stripped), (ii) with-break continuation (RC-02/05 + RC-03/04
  + RC-07), (iii) event-conditioned (RC-06 nguyên dạng, BLOCKED). Cả 3 đều
  chết có đo hoặc bị chặn dữ liệu.
- Merge này đồng thời trả lời mục C3 (distinctness): không có rule nào để
  chọn ≤3 — cap không ràng buộc cycle này.

## 8. DEATH LEDGER (per-rule)

| # | rule | entry | F-0 verdict | Kill law chính | family_id dẫn chứng (đo) |
|---|------|-------|-------------|----------------|--------------------------|
| 1 | RC-01-E01 | E01 Phemex range fade | F0_KILLED | K-F0 skeleton row-7 + payer/info | `FXOS-04`, `TRACKA1-M1-RANGEFADE-PIT`, `TRACKA2-C1C2C3-REGATED-RANGEFADE`, `A6-V16-F1` |
| 2 | RC-01-E05 | E05 Kraken RSI/BB overext fade | F0_KILLED | K-F0 (gate-add variant; TRACKA2 precedent) | `TRACKA2-C1C2C3-REGATED-RANGEFADE`, `FXOS-04`, `mean-reversion-transfer`, `TRACKA1-M1-RANGEFADE-PIT` |
| 3 | RC-01-E08 | E08 LiteFinance range+POC | F0_KILLED | K-F0 skeleton row-7 | `FXOS-04`, `TRACKA1-M1-RANGEFADE-PIT`, `A6-V16-F1` |
| 4 | RC-01-E10 | E10 Binance range guide | F0_KILLED | K-F0 skeleton row-7 | `FXOS-04`, `TRACKA1-M1-RANGEFADE-PIT`, `A6-V16-F1` |
| 5 | RC-02-E04 | E04 Kraken vol breakout | F0_KILLED | K-F0 skeleton row-1 (control-out-earns đo) | `PSV1-BTC_H1-UPTREND-BREAKOUT_CONT`, `PSV1-BTC_H1-DOWNTREND-BREAKDOWN_CONT`, `PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION`, `H-VOLCOMP-BRKOUT-v1`, `V17-a5-P1-ATTN-PHASE` |
| 6 | RC-02-E07-approx | E07 LiteFinance (OI dạng NOT_CONSTRUCTIBLE) | F0_KILLED | K-F0 row-1 + NOT_CONSTRUCTIBLE(OI) | `H-VOLCOMP-BRKOUT-v1`, `PSV1-BTC_H1-UPTREND-BREAKOUT_CONT` |
| 7 | RC-05-E09 | E09 CryptoCred DO reclaim | F0_KILLED | K-F0 (session-swap anti-variant; clock lớp chết) | `V17-a5-P1-ATTN-PHASE`, `FXFV1-A3-P1`, `FXFV2-A4-P1` |
| 8 | RC-02-E11 | E11 Phemex TMF breakout | F0_KILLED | K-F0 row-1 (flow-gate observable) | `PSV1-BTC_H1-UPTREND-BREAKOUT_CONT`, `H-VOLCOMP-BRKOUT-v1`, `PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION` |
| 9 | RC-03-E02 | E02 Kraken trend swing-trail | F0_KILLED | K-F0 (continuation re-gate; ancestry ở chân continuation) | `TRACKA2-P3B-DINV-1D`, `PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION`, `PSV1-BTC_H1-ACC-FLOOR_PROVISION` |
| 10 | RC-04-E06 | E06 Kraken VWAP/node pullback | F0_KILLED | K-F0 (re-gate + clock statistic) | `TRACKA2-P3B-DINV-1D`, `PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION` |
| 11 | RC-07-E12 | E12 Bybit H&S neckline short | F0_KILLED | K-F0 (breakdown-continuation short; merge 1/3) | `PSV1-BTC_H1-DOWNTREND-BREAKDOWN_CONT`, `markdown-breakdown-short`, `H-VOLCOMP-BRKOUT-v1`; (nhánh fork fade: `TRACKA2-C1C2C3-REGATED-RANGEFADE`, `V17-A6-P2-OICASCADE`) |
| 12 | RC-06-E03 | E03 Kraken news fade | DATA_GATED + DEAD_COLLISION | BLOCKED_DATA (§1.5-4) + lớp event chết | `CNG1-A4-P1`, `CNG1-A4-P2`, `CNG1-A5-P1`, `CNG1-A5-P2`, `CNG2-A4-P1`, `CNG2-A4-P2`, `CNG2-A5-P1`, `CNG2-A5-P2`, `V17-A6-P1-FUNDJUMP`, `FXNG1-A5-P1`, `FXNG1-A4-P2`, `FXNG3-A4-P1/P2`, `FXNG3-A5-P1/P2`, `FXNG4-A4-P1/P2`, `FXNG4-A5-P1/P2`, `FXFV5-A6-P1-pre-release-avoidance`, `FXFV6-A4-P1`, `FXFV7-A4-P1`; hướng fade: `A6-V16-F1` |

Neo-MAP (class death không có row riêng trong ledger 137): forensic
BTC-H4-CONTINUATION-V2 (terminal c390375e, "KHÔNG có at-entry PIT state tách
regime"); BTC-BEAR-OPPORTUNITY recon (fictional-counterparty veto ×3);
VIABILITY cohort-3 (`research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/
forex_program/VIABILITY_cohort3_REPORT.md`, 0/12 class).

**Survivors: 0/11 constructible rules.** Không rule nào được force-kill mà
không khớp skeleton một family đo chết; không rule nào bị rescue.

## 9. Câu scope bắt buộc cho CYCLE_VERDICT

CYCLE_VERDICT của cycle này PHẢI mang nguyên văn câu sau (EN + VN mirror):

> **"This close adjudicates ONLY the rule skeletons constructible from the
> documented public playbook corpus of this cycle — 12 admissible entries
> from 6 dated exchange-education/educator channels under a 37/50 fetch
> budget with documented Reddit/TradingView/Binance-Square access walls
> (FETCH_LOG.md); it is NOT a claim that 'day trading is dead', and it does
> not pre-judge rule classes, data planes, or information layers that this
> corpus could not express."**

> **"Bản close này chỉ phán các skeleton rule CODIFY ĐƯỢC từ corpus playbook
> công khai đã tài liệu hóa của cycle này — 12 mục khả dụng từ 6 kênh
> exchange-education/educator có ngày công bố, trong ngân sách 37/50 lượt
> fetch với các bức tường truy cập Reddit/TradingView/Binance-Square được ghi
> trong FETCH_LOG.md; đây KHÔNG phải phát biểu 'day trading đã chết', và
> không phán trước các lớp rule, plane dữ liệu hay lớp thông tin mà corpus
> này không biểu diễn được."**

## 10. Ghi nhận trung thực & giới hạn

1. **K-COST không bắn rule nào** ở geometry source-stated (multi-percent
   capture ≥ 23.84 bps binding rung) — mọi kill là F-0; nếu một rule bị
   freeze sau này với construction co hẹp capture dưới rung, K-COST bắn tại
   freeze (đã khai trong RULE_CANDIDATES, C6).
2. **E07 dạng-OI**: NOT_CONSTRUCTIBLE (OI = data layer futures, không có
   lịch sử đa năm được authorize — BLOCKED_UNCONSTRUCTIBLE bear-recon); chỉ
   approx volume-only được xét và chết với lớp.
3. **Flat-by end-of-UTC-day là frozen parameter, không phải nguồn** — việc
   freeze nó không phải phép rescue nào; mọi rule đã chết trước khi tham số
   này có vai trò.
4. **Không có measurement nào được đề nghị** — tòa R2 không cần thêm phép đo:
   mọi kill đều đã có bằng chứng đo sẵn trong ledger. Đề xuất duy nhất cho
   A1: ghi 3 family-death summary vào FAMILY_FAILURES/MAP nếu Lead thấy cần
   — `DTPCX1-C1-PLAYBOOK-RULE-LEDGER` (11 rules F0_KILLED, 0 survivors,
   corpus-bounded) — quyền quyết định thuộc Lead/A1, không phải lane này.
5. **Outcome-blind**: tòa không load giá, không đọc outcome, không mở sealed;
   toàn bộ lead evidence là ledger đã đóng + MAP. `Chưa có PnL nào được xem
   hoặc tính toán cho identity nào trong phiên tòa này.`
