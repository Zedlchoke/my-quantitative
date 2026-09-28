# UNIFIED STRATEGY — Chiến lược thống nhất cho toàn thị trường Forex + Metals + Energy

**Chương trình:** FOREX-UNIFIED-STRATEGY-BRAINSTORM-V1 · **Ngày:** 2026-09-28
**Trạng thái:** RESEARCH BRAINSTORM. Mọi thành phần dưới đây là **hypothesis / NOT_RUN** cho tới khi được đo theo quy trình cycle của workspace. Tài liệu này là bản thiết kế, không phải evidence.

---

## 0. Triết lý — vì sao "thống nhất" là một KHUNG chứ không phải một TÍN HIỆU

Điểm quan trọng nhất mà 14 lane nghiên cứu hội tụ: **không có kênh truyền dẫn nào thắng mãi — kênh nào đang thắng là thuộc tính của regime, không phải của symbol.** Bằng chứng sống tháng 9/2026:

- Cùng một oil shock: đẩy Brent lên $108, nhưng đẩy **gold XUỐNG** −26% từ đỉnh (vì CPI → kỳ vọng hike Fed → real yields 2.85% → kênh lãi suất đè kênh safe-haven).
- Cùng oil >$100: **CAD vẫn yếu** (differential −150/−175bp + trade war) — rate regime lấn át terms-of-trade.
- Cùng risk geopolitical: JPY được bid, CHF được SNB chủ động yếu hóa, gold không được bid — ba safe-haven, ba số phận.

Vì vậy chiến lược thống nhất không thể là "một chỉ báo chạy trên 12 symbol". Nó phải là một pipeline 6 lớp trong đó **bước định giá duy nhất mỗi tuần là: thị trường đang ở state nào** — rồi từng cụm symbol bật đúng họ strategy đã nghiên cứu cho state đó, dưới một hệ risk budget chung. Tóm một câu:

> **Không dự báo một chiều. Phân loại trạng thái thị trường bằng 5 chiều vĩ mô → router bật/tắt họ strategy theo từng cụm symbol → phủ gate sự kiện → quản trị rủi ro theo cụm tương quan → kill-switch машин cho mọi tầng.**

---

## 1. Kiến trúc tổng quan (6 lớp)

```
[Lớp 0] Universe & Clustering        — 12 symbol → 4 cụm + 1 ngoại lệ
   ↓
[Lớp 1] Market State Engine          — 5 chiều state vector, tính tuần
   ↓
[Lớp 2] Regime Router                — allocation matrix: state × cụm → families ON/OFF
   ↓
[Lớp 3] Macro Gates & Blackouts      — CB/data/intervention/OPEC/EIA event gates
   ↓
[Lớp 4] Portfolio Risk Budget        — cluster caps, per-trade risk, kill-switches
   ↓
[Lớp 5] Execution & Cost Guardrails  — session, spread, gap policy
   ↓
[Lớp 6] Monitoring & Kill Criteria   — dashboard tuần, điều kiện tắt cả hệ thống
```

---

## 2. Lớp 0 — Universe & Clustering

| Cụm | Symbols | Driver thống trị | Ghi chú |
|---|---|---|---|
| **USD-bloc majors** | EURUSD, GBPUSD, USDJPY, USDCHF | Rate differential + dollar cycle + idiosyncratic tail (gilt, intervention, SNB) | Tương quan lẫn nhau cao → quản trị như MỘT rủi ro |
| **Commodity-FX** | USDCAD, AUDUSD, NZDUSD | Rate differential TRƯỚC, terms-of-trade SAU (Sep-2026 chứng minh) | Liên kết chéo với cụm Energy |
| **Precious** | XAUUSD, XAGUSD | Real yields × DXY × VIX (hai yếu tố đầu quyết định regime) | XAG thêm industrial/squeeze; GSR là router nội bộ |
| **Energy** | BRENT, WTI | Headline-intensity (war/peace) + term structure + inventories | Brent–WTI spread là tín hiệu riêng |
| **Ngoại lệ** | NATGAS | Weather + storage vs 5-yr norm | |ρ| thấp nhất universe → diversifier thật sự; quản trị rủi ro riêng vì tail đậm |

Nguyên tắc clustering: **position cùng cụm = cùng hướng exposure USD/risk** — risk budget tính theo cụm, không theo symbol (mục 6).

---

## 3. Lớp 1 — Market State Engine (5 chiều, cập nhật tuần)

Mỗi chiều là một câu hỏi có thang đo cơ giới (không judgment mềm), tổng hợp thành state vector `(R, K, E, I, V)`:

### R — Rate/Hike regime
- Đo bằng: (a) slope kỳ vọng policy 3 tháng tới của Fed (OIS/fed funds futures pricing), (b) tốc độ Δ real yield 10Y TIPS/tuần, (c) chiều của differential Fed vs gói {ECB, BoE, BoJ}.
- Trạng thái: `HIKING_FAST` (≥ +10bp real/tuần hoặc ≥2 hike priced 3 tháng) · `HIKING_SLOW` · `FLAT` · `EASING`.
- Sep-2026: `HIKING_FAST` (TIPS +23bp/tuần; ~95% priced thêm hike đến 12/2026).

### K — Risk regime
- Đo bằng: VIX level & term structure (M1 vs M3), credit spreads, và **gold-vs-DXY confirmation** (gold bid + DXY yếu = risk-off thật; tháng 9/2026 gold rơi cùng áp lực hike → risk-off "giả" với precious).
- Trạng thái: `RISK_ON` · `NEUTRAL` · `RISK_OFF_REAL` · `RISK_OFF_RATE_DRIVEN` (loại thứ 4 này là phát kiến của chương trình: risk-off do kỳ vọng hike, gold KHÔNG làm safe-haven).

### E — Energy/Geopolitical regime (cho cụm Energy + lan tỏa commodity-FX)
- Đo bằng: Brent–WTI spread (bình thường $3–6; $11–14 = war premium), headline-intensity (số tanker/sanctions headlines/tuần, multi-source confirm hay không), spare capacity OPEC+ hiệu dụng, backwardation depth M1–M3.
- Trạng thái: `WAR_ON` (premium cao + headline ping-pong) · `DE_ESCALATION` (deal headlines tăng, premium co) · `PEACE_BASELINE`.

### I — Intervention map (ràng buộc cứng, không phải dự báo)
- USDJPY: "warning track" 158–160 sau can thiệp phối hợp Jul–Aug/2026; verbal intervention của MOF là tín hiệu số 1.
- CHF: SNB sight deposits WoW (≥ +5 tỷ CHF = footprint bán CHF); tail = SNB hike surprise (bài học floor 2015).
- CNY/funcion khác khi xuất hiện. Trạng thái mỗi điểm: `CLEAR` · `WARNING` · `ACTIVE`.

### V — Volatility regime (per cụm)
- Đo bằng: realized vol percentile 63 ngày của mỗi cụm; bimodal check cho USDCHF (SNB nén vol); OVX cho energy.
- Trạng thái: `COMPRESSED` · `NORMAL` · `EXPANDED`.

**Output mỗi tuần:** state vector, ví dụ Sep-2026 = `(R=HIKING_FAST, K=RISK_OFF_RATE_DRIVEN, E=WAR_ON, I={JPY:WARNING@158–160, CHF:ACTIVE-selling}, V=EXPANDED{energy,GBP}, NORMAL{majors})`.

---

## 4. Lớp 2 — Regime Router (allocation matrix)

Matrix gốc (trích những hàng có nền tảng kinh tế mạnh nhất từ 1.200 ý tưởng; đầy đủ family-map từng symbol nằm trong `symbols/*.md`):

| State (chi phối) | Cụm | Families bật | Families tắt | Rationale |
|---|---|---|---|---|
| HIKING_FAST | USD-bloc | Carry/Rate-differential **về phía USD** (long USDCHF, long USDJPY chỉ khi I=JPY:CLEAR), Policy-divergence trend | Mean-reversion AgainstUSD; static carry mọi chiều khác | Differential là driver số 1; nhưng carry luôn kèm kill-switch (mục 6) |
| HIKING_FAST | Precious | **Tắt hoặc short-bias** (regime matrix TIPS-slope × VIX); chỉ bật XAG squeeze-fuel nếu 3 cổng GSR+COT+deficit cùng mở | Trend-long gold; "geopolitical bid" assumption | Real yields giết gold — bằng chứng −26% từ ATH giữa war |
| HIKING_FAST | Commodity-FX | Differential-carry filter (funding legs: NZD; CAD tùy BoC), event-surprise drift | ToT-pure strategies (bị lấn át) | Sep-2026: oil mạnh + CAD yếu — rate regime lấn át ToT |
| WAR_ON | Energy | Headline-intensity router: Backwardation long-tilt, weekend-gap continuation, deal-headline **fade** (thiếu multi-source confirm) | Mean-reversion quanh "fair value" chết; naked short premium | Premium không quan sát trực tiếp — chỉ trade qua proxy (spread, term structure) |
| WAR_ON (lan tỏa) | Commodity-FX | War/peace classifier gate USDCAD; CAD giữ long-bias khi trade-war overlay cùng chiều | Ý tưởng "oil lên → CAD mạnh" không điều kiện | Section 338 + differential đảo chiều quan hệ oil-CAD |
| RISK_OFF_REAL | USD-bloc | Safe-haven basket (JPY, CHF cùng chiều), gold long nếu R ≠ HIKING_FAST | Carry toàn bộ; risk-beta (AUD, NZD) | Carry-unwind cascades — kill-switch VIX term structure |
| RISK_OFF_RATE_DRIVEN | Precious | **Không auto-long gold** — chờ two-factor matrix xác nhận kênh rate đã chạm ngừng | Safe-haven assumptions | Trạng thái tháng 9/2026: gold rơi dù risk-off |
| V=COMPRESSED | Tất cả | Breakout/Vol-expansion chuẩn bị (squeeze setup), XAG three-gate squeeze | Trend-following (chết trong compression) | Vol mean-reverts — chuẩn bị nổ chứ không đoán hướng |
| EASING + PEACE_BASELINE | Precious, Commodity-FX | Trend-long gold (real yields rơi), ToT strategies bật lại, carry funding-legs đảo | Short-precious | Mirror-image của state hiện tại |

**Quy tắc vàng của router:** cùng một họ strategy chỉ được bật ở một symbol khi **Coupling condition** của ý tưởng đó (ghi trong từng file symbol) thỏa mãn — router không bỏ qua được coupling; router chỉ quyết định cửafamily, coupling quyết định cửa ý tưởng.

---

## 5. Lớp 3 — Macro Gates & Event Blackouts

Nguồn: lịch tuần chuẩn trong `macro/CURRENCIES_CORE.md §7` và `CURRENCIES_BLOC.md §7`.

- **CB blackout:** không mở position mới ±window quanh FOMC/ECB/BoE/BoJ/SNB/RBA/RBNZ/BoC (window mặc định: 24h trước → 2h sau; mở lại theo event-drift rules đã nghiên cứu nếu muốn trade aftermath).
- **Data blackout top-tier:** NFP, CPI (Mỹ & quốc gia chân quote), PCE — giảm 50% size hoặc flat tùy family; chỉ Event/Data-driven family (đã thiết kế cho surprise) được trade xuyên.
- **Intervention warning (JPY):** trong vùng 158–160 hoặc sau verbal intervention → cấm long breakout USDJPY, mọi carry JPY half-size.
- **Energy events:** OPEC+ meetings, EIA Wed (WTI) / Thu (NATGAS) 10:30 ET, monthly reports EIA/OPEC/IEA.
- **Trade-war calendar (sống Sep-2026):** mốc Section 338 (import bans 29/09), đe thuế auto 01/01/2027 — gate riêng cho CAD.
- **Gilt credibility test (GBP):** gilt 10Y lên MÀ GBP xuống → bật fiscal-stress flag, tắt mọi GBP long.

---

## 6. Lớp 4 — Portfolio Risk Budget & Kill-switches

- **Per-trade risk:** 0.25–0.5% equity; stop theo ATR (không stop tĩnh số tròn); news window nới stop theo event-vol, không theo cảm tính.
- **Cluster caps (theo Lớp 0):** tổng risk một chiều theo cụm ≤ 2%; USD-bloc tính là MỘT exposure (4 symbol tương quan cao); NATGAS cap riêng và thấp hơn (tail đậm) ≤ 1%.
- **Cross-cluster netting:** cho phép energy-long được hedge một phần bằng commodity-FX ngược chiều KHI coupling cùng mở (ví dụ USDCAD long × WTI short là cặp có nền tảng) — nhưng netted risk vẫn nằm trong cluster cap của bên lớn hơn.
- **Kill-switches tầng (từ 1.200 ý tưởng, những cái phổ quát nhất):**
  - Carry family: VIX term-structure inversion (M1>M3) → thoát toàn bộ carry trong cụm (tín hiệu unwind sớm nhất, bài học Aug/2024 & 2026).
  - Intervention: MOF/SNB action xác nhận → flat chân liên quan 48h.
  - Trend family:跌破 structural stop theo regime của family (không phải theo pain tolerance).
  - Event-drift: surprise bị revert hoàn toàn trong 2 phiên → hypothesis đòi chết, không average down.
  - Cả cụm: drawdown cụm > 4% trong state vector hiện hành → cụm về flat chờ state vector đổi.
- **Nghịch lý position sizing NATGAS:** vì |ρ| với mọi thứ thấp, NATGAS là diversifier — nhưng tail dày nên size nhỏ bất thường (widow-maker; sizing theo tail không theo vol trung bình).

---

## 7. Lớp 5 — Execution & Cost Guardrails

- **Sessions:** FX majors — London + NY overlap; AUD/NZD — Asia; XAU/XAG — London AM + COMEX open; Energy — NY. Tránh mở moi mới Friday close; tránh rollover 22–23h UTC (spread nở).
- **Spread/margin guardrail theo instrument:** NATGAS, XAGUSD có spread/margin "đắt gấp 2–3 lần" (lane NZDUSD/XAGUSD) — tần suất strategy phải trả chi phí đó trước khi sinh lời; mọi ý tưởng tần suất cao trên instrument đắt tự động rớt hạng.
- **Weekend gap policy:** energy + precious có gap đậm (WTI giải phóng 48h event risk trong 1 tick — lane WTI): không giữ size đầy qua weekend trong WAR_ON; gold gaps trong vol-cluster.
- **Futures roll:** Brent/WTI/NATGAS CFD roll theo lịch contract của broker — ghi nhận roll cost vào hypothesis trước khi tính edge (term-structure carry đã được thiết kế thành family riêng để ăn/ttrả phần này minh bạch).

---

## 8. Lớp 6 — Monitoring & Kill Criteria

**Dashboard tuần (một trang):** state vector 5 chiều + bảng allocation hiện hành + hiệu suất từng family theo cụm + danh sách gate tuần tới (CB/data/events) + trạng thái kill-switches.

**Điều kiện tắt cả hệ thống (typed, không judgment):**
1. Hệ thống thua baseline "ALWAYS_ON random-selection" sau chu kỳ đánh giá định trước (JEV law của workspace — precedent REGIME-GATED-COMBO-V1).
2. State engine tự nó fail: state vector đổi chiều liên tục > N lần trong M tuần (whipsaw regime) → về flat + nghiên cứu lại thang đo.
3. Regime chưa có trong bảng router (ví dụ: EASING + WAR_ON đồng thời lần đầu) → flat cụm affected chờ bổ sung matrix — không extrapolate.

---

## 9. Worked example — state Sep-2026 → allocation hiện hành

State: `(R=HIKING_FAST, K=RISK_OFF_RATE_DRIVEN, E=WAR_ON, I={JPY:WARNING, CHF:ACTIVE-sell}, V=EXPANDED{energy,GBP})`

| Cụm | Đang bật | Đang tắt | Ghi chú sống |
|---|---|---|---|
| USD-bloc | Carry long USD (USDCHF với sight-deposit confirm; USDJPY chỉ dưới 158), gilt-credibility short GBP nếu flag mở | Mean-reversion against USD; long breakout USDJPY | Hedge rates bằng... không có gì — size half |
| Commodity-FX | War/peace-gated CAD short (differential + trade war), NZD-funding strategies, RBA-outcome drift AUD | ToT-pure | Chờ RBA 29/09 & Section 338 mốc 29/09 |
| Precious | Two-factor matrix: gold flat/short-bias tới khi TIPS-slope flập; XAG chỉ squeeze 3-cổng; XAU/XAG ratio theo GSR 66 | Trend-long gold; geopolitical-bid gold | Câu hỏi mở: CB-floor $4,000–4,100 |
| Energy | Backwardation long-tilt Brent; deal-headline fade; Cushing <20M watch (21.5M và đi xuống); EIA composite surprise WTI | Mean-reversion; naked short war premium | Roll + gap policy khắt khe |
| NATGAS | EIA surprise drift (|surprise| ≥25 Bcf), storage×weather dispatcher, fade HH-spike-do-global-news khi feedgas flat | ToT/Hormuz lan tỏa assumption | HH decoupled TTF — diversifier |

---

## 10. Bảng tra nhanh: symbol × driver chính × coupling gate phải thỏa

| Symbol | Driver #1 | Driver #2 | Gate bắt buộc cùng chiều / veto |
|---|---|---|---|
| EURUSD | Fed–ECB differential & slope | Energy ToT (EU nhập khẩu) | 2Y UST–Schatz slope cùng hướng giá; oil-spike veto nửa ngày |
| GBPUSD | BoE path + gilt stress | USD cycle | Fiscal-stress flag veto long; gilt↑+GBP↓ = short cả GBPUSD/EURGBP |
| USDCAD | Rate differential | Oil + Section 338 | War/peace classifier; net-US-surprise (không raw NFP) |
| USDJPY | UST 10Y + carry | Intervention map | <158–160 ceiling; VIX M1>M3 kill carry |
| AUDUSD | RBA + China credit | Iron ore/copper | China impulse trend; risk-on xác nhận |
| NZDUSD | OCR funding-leg status | GDT WMP | ΔWMP ≥±3% drift; spread-cost filter (instrument đắt) |
| USDCHF | SNB 0% + sight deposits | Risk sentiment | Deposits WoW ≥+5 tỷ CHF mở band; SNB-hike tail stop |
| XAUUSD | Real yields (TIPS slope) × VIX | DXY, CB buying | Two-factor matrix quyết định long/flat/short |
| XAGUSD | Gold lead-lag | GSR + industrial | 3-cổng squeeze gate; ratio GSR breakout |
| BRENT | Headline intensity (war/peace) | Term structure | Backwardation confirm; multi-source headline check |
| WTI | EIA/Cushing physical | Risk premium (theo Brent) | Backwardation gate; Cushing <20M trigger |
| NATGAS | Storage vs 5-yr norm × weather | LNG feedgas | Dual-regime dispatcher; fade global-news spikes khi feedgas flat |

---

## 11. Con đường từ brainstorm → evidence (theo luật workspace)

1. **Re-measure trước:** correlation maps + mọi ngưỡng "(cần kiểm chứng)" trong 14 file phải đo trên data thật (DATA-FOUNDATION-SIXSOURCE-V1) trước khi chọn family đưa vào test — prior ≠ measurement.
2. **Chọn nhỏ, test đúng:** không test 1.200 ý. Router chỉ cần kiểm định từng khối: (a) state engine đo được và ổn định (backtest state vector trên lịch sử), (b) TỪNG hàng allocation có expectation dương sau cost vs 4 baselines chuẩn của nhà (ALWAYS_ON / random / best-leg / clock-shadow — precedent REGIME-GATED-COMBO-V1), (c) kill-switches thực sự cắt tail.
3. **Đăng ký cycle:** DRAFT plan → owner duyệt → gates + GO theo quy trình; budget cells giới hạn; dead-disclosed nếu thua baselines. Không có ngoại lệ "vì nó hay quá".

## 12. Hạn chế trung thực

- State engine 5 chiều dùng ngưỡng định tính-chuẩn hóa (percentile, bp/tuần) — chưa tối ưu, cố ý không fit quá khứ; mọi con số là điểm khởi đầu để preregister, không phải sự thật đo được.
- Toàn bộ correlation/regime claims là prior kiến thức + verify tin tức Sep-2026, chưa đối chiếu data repo.
- Headline-intensity và multi-source-confirm cho energy là quy trình thủ công — tự động hóa được nhưng cần nguồn dữ kiện đáng tin (chưa có trong repo).
- Intervention map là "đọc水务" — các ngưỡng (158–160 JPY, 5 tỷ CHF WoW) là heuristic từ giai đoạn 2022–2026, có thể lỗi thời sau lần can thiệp kế tiếp.
- 1.200 ý tưởng không đồng đều về chất lượng — đó là bản chất của brainstorm; bảng router ở trên đã lọc theo nền tảng kinh tế, phần còn lại là kho mỏ để sau.
