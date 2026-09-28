# AUDUSD — Deep Dive & 100 Strategy Ideas

- Program: FOREX-UNIFIED-STRATEGY-BRAINSTORM-V1 · Lane: AUDUSD · Ngày: 2026-09-28
- Tính chất: knowledge-only brainstorm (không backtest, không data pull). Mọi con số
  "typical range" là kinh nghiệm thị trường, phải đo lại trên dữ liệu live trước khi dùng.
- Trạng thái verify (WebSearch 2026-09-28): Fed đã **hike 25bp ngày 16/09/2026 → target
  3.75–4.00%** (lần đầu kể từ 2023, unanimous, IORB 3.90%, SEP chỉ ~4.00–4.25% cuối
  2026/2027; FOMC kế tiếp 27–28/10) — nguồn federalreserve.gov/CNBC/Reuters. RBA cash
  rate **~4.35%** sau 3 lần hike trong 2026 (từ 3.60%), quyết định tiếp theo **29/09/2026**,
  thị trường/analyst (Westpac) nghiêng về hike thêm 25bp → 4.60% — mức cao nhất từ 2011
  (nguồn ABC/Guardian/Finder; chi tiết đường đi cần kiểm chứng). China 2026: Q1 GDP +5.0% y/y
  (JPM), OECD dự 4.5% cho 2026, property đầu tư **-16.2% y/y (Jan–May 2026, World Bank)**,
  cầu thép 2025 **-6.9%** (OECD), sản lượng thép 06/2026 83.67Mt +0.4% y/y (Reuters),
  iron ore 62% Fe dự báo rơi về **~$90/t năm 2026** từ ~$100 (ING/Steel-on-the-Net), IMF
  (02/2026) kêu gọi stimulus mạnh hơn. Mức spot AUDUSD hiện tại: **(cần kiểm chứng)**.

---

## 1. Bản chất instrument

### 1.1 Microstructure & sessions

- AUDUSD là cặp G10 liquid hàng đầu (top ~5 FX pair theo turnover RBA BIS survey, ~6-7%
  global turnover), pip = 0.0001, spread ECN điển hình 0.6–1.2 pip, giãn 2–4× lúc có tin; point value $10/pip/standard lot. Giá chạy liên tục 24/5 Sydney mở tuần → NY đóng.
- **Session map (UTC, mùa Úc DST Oct–Apr dịch +1h cho các mốc Úc/Á)**:
  - Sydney/Tokyo (22:00–06:00 UTC): thanh khoản mỏng nhất nhưng **chứa hầu hết thông tin
    riêng của AUD** — data Úc 00:30/01:30 UTC (11:30 AEST), data Trung Quốc 01:30–02:45 UTC.
    Spread giãn, depth mỏng → false breakout thường gặp hơn các pair USD châu Âu.
  - London mở 07:00 UTC: re-pricing theo overnight China/Á; đây là cửa sổ breakout thật
    nhất trong ngày cho AUDUSD.
  - London/NY overlap 12:00–16:00 UTC: thanh khoản sâu nhất, USD-common-factor chi phối,
    AUDUSD phần lớn chạy theo DXY/EURUSD ở khung này.
- **Đặc thù giờ_events khác mọi pair USD khác**: RBA quyết định **14:30 AEST = 04:30 UTC =
  00:30 New York** — rơi vào buổi trưa muộn/màn hình cuối ngày của Mỹ, order book mỏng →
  phản ứng giật cục, hay spike cả hai chiều rồi mới chọn hướng. Tương tự mọi data Úc lúc
  11:30 AEST rơi vào đầu giờ Tokyo — nếu Tokyo nghỉ lễ thì liquidity gap rất lớn.
- Fixing: WM/Refinitiv 4pm London (16:00 UTC) chuẩn global; **benchmark AUD riêng của Úc
  tính ~09:30–10:30 Sydney** — dòng quỹ superannuation/pension nội địa và month-end
  corporate hedging tập trung quanh các fixing này (flash-move ngắn, hay có mean-reversion
  sau fixing).
- Rollover swap 3x ngày Wednesday; AUD từng là carry currency kinh điển → cost/benefit
  holding đa ngày bất đối xứng theo sign của rate differential (2026: RBA 4.35% vs Fed
  ~3.75–4.00% → long AUDUSD đang nhận swap dương nhẹ, (cần kiểm chứng swap forward thực tế)).
- Liquidity actors: 3 big AU banks (CBA/WBC/NAB/ANZ) + global dealers; Tokyo banks và
  Chinese SOE treasury là flow tự nhiên lớn bên mua/bán AUD quanh trade settlement; macro
  funds dùng AUD làm **điểm vào liquid nhất cho chữ ký "China growth / risk-on"** — vì thế
  AUDUSD và AUDJPY là hai vehicle chuẩn của risk appetite toàn cầu.

### 1.2 Điểm ĐẶC BIỆT riêng AUDUSD (đừng trade nó như một EURUSD khác)

1. **China-growth proxy hàng đầu của FX**. Úc xuất iron ore (~20-25% giá trị xuất khẩu,
   ~70-80% đi Trung Quốc), than luyện cốc, LNG, copper concentrate, vàng. Trung Quốc chiếm
   ~30-40% xuất khẩu hàng hoá Úc (bao gồm dịch vụ/giáo dục). Kết quả: 1 shock cầu Trung
   Quốc (credit impulse, PMI, property) truyền vào AUDUSD nhanh và mạnh hơn vào bất kỳ cặp
   G10 nào khác. Iron ore là **single best daily-frequency proxy** cho driver này.
2. **Risk beta toàn cầu**: AUD = thân risk-on; AUDJPY được thị trường dùng làm thước risk
   appetite (thay CSPP-type gauges). VIX>25-30 → AUD bị bán bất kể narrative riêng; risk-on
   melt-up → AUD outperform. Nghĩa là một nửa variance của AUDUSD không đến từ Úc cũng như
   Mỹ — nó đến từ **chiều global risk**.
3. **Commodity Terms-of-Trade (ToT) mechanics**: AUD dài hạn theo ToT (RBA commodity index /
   import price). Chuỗi truyền: China stimulus/property ↑ → steel output & iron ore price ↑
   → ToT Úc ↑ → national income ↑ → RBA hawkish bias ↑ + equity inflow ↑ → AUDUSD ↑.
   Ngược lại hoàn toàn khi China throttle (2021 power cuts, 2024-26 property deflation).
   ToT là mạch **chậm (weeks-months)** trong khi positioning là mạch **nhanh (giờ)** — hai
   mạch này đúng chiều thì tạo trend months dài (ví dụ 2026: hawkish RBA vs Fed dovish đầu
   năm đẩy AUD lên, Fed quay lại hike giữa năm kéo về ~4% — StoneX 06/2026).
4. **RBA vs Fed differential là xương sống carry**: 2026 đang là chế độ hiếm — **cả hai
   đều hawkish** (Fed vừa hike lần đầu từ 2023; RBA đã hike 3 lần trong năm). Differential
   hẹp và hai chiều → carry AUDUSD yếu hơn lịch sử, **chính sách phải nghiêng về rate-path
   expectation (2y spread momentum) thay vì static carry**.
5. **Asian-session native**: AUDUSD là cặp G10 duy nhất có "home session" trùng khung
   thông tin Trung Quốc → các window session-based quanh data TQ là edge cấu trúc riêng.
6. **Chất liệu giá**: AUDUSD có xu hướng trend tốt trong macro-trend (TSMOM historically
   mạnh ở commodity FX) nhưng spike event thường **overshoot rồi reverting 30-60%** trong
   ngày — asymmetry giữa impulse và decay là nguyên liệu cho cả hai họ strategy.

### 1.3 Tin tức & sự kiện ảnh hưởng

**Scheduled (mốc UTC, ngày ko cố định tuyệt đối — luôn check calendar tuần):**

| Event | Nhịp | Giờ (UTC) | Kênh truyền vào AUDUSD |
|---|---|---|---|
| RBA decision + statement + presser | 8/năm, ~6 tuần lễ (28-29/09/2026 kế tiếp) | 04:30 | Cash rate path → rate diff, OIS repricing → spot giật cục do book mỏng giờ này |
| RBA minutes + SMP (May/Nov) | 2 tuần sau họp | 00:30-01:00 | Dove/hawk re-read → drift 1-3 ngày |
| Australia monthly CPI indicator | hàng tháng (~4 tuần sau month-end) | 00:30 | Trực tiếp vào kỳ vọng RBA → vol cao nhất trong các data Úc |
| Quarterly CPI | quý | 00:30 | Same, mạnh hơn (trim mean là số RBA nhìn) |
| Labour force (employment/participation) | ~thứ 5 tuần lễ 3 | 00:30 | Slack → RBA path; unemployment rate surprise thường overshadow số jobs |
| Retail sales, GDP, trade balance, building approvals | tuần/tháng | 00:30-01:00 | Nhẹ hơn CPI/labour, dùng xác nhận chứ ít tự đi giá |
| China NBS & Caixin PMI | cuối tháng / mùng 1 | 01:00-01:45 | Cầu sản xuất TQ → iron ore/copper → AUD (Caixin thường có gap vs NBS — divergence là tín hiệu) |
| China aggregate financing (TSF) + new loans | 10-15 hàng tháng | ~02:00 | **Credit impulse = driver xu hướng 1-3 tháng** của AUD |
| China LPR | mùng 20 | 01:30 (09:15 Beijing) | Hiếm khi đổi; khi đổi là regime shift lớn |
| China trade balance / iron ore import volume | ~mùng 7 | 02:00-03:00 | Volume nhập iron ore TQ = cầu thật (vs giá speculative) |
| Mysteel/Dalian iron ore port inventory | hàng tuần/tuần | Cuối ngày Á | Inventory ↑ = nhu cầu tồn kho yếu → AUD pressure |
| FOMC + SEP + presser | 8/năm (16/09/2026 vừa hike; 27-28/10 kế tiếp) | 18:00 | USD-common-factor: hawkish Fed → AUDUSD xuống kể cả khi RBA cũng hawk (differential thu hẹp) |
| US CPI / NFP / ISM | tháng | 12:30/14:00 | USD leg; NFP surprise 3 sigma thường đẩy AUDUSD 40-80 pips |
| China Politburo meeting (Apr/Jul/Dec) + NPC (Mar) | quý | ad hoc đầu giờ Á | Stimulus expectation repricing — window vol lớn nhất của "unscheduled" |

**Unscheduled:**
- China stimulus/bailout surprise (headline trên state media): AUD là assets phản ứng
  nhanh nhất của FX, thường 50-100 pips trong phút, rồi **chọn lọc**: stimulus có quy mô
  thật (fiscal property-backed) thì drift tiếp; stimulus "giọng nói" thì revert toàn bộ.
- PBoC ad-hoc RRR/yuan fixing surprise; US–China tariff headline (AUD gánh cả hai chân:
  China growth + global risk).
- Iron ore supply events: bão West Australia (mùa cyclone Oct–Apr), tai nạn mỏ Brazil
  (Brumadinho-type), sáp output policy TQ — thổi ToT không qua kênh cầu.
- Risk-off shock (pandemic/geopolitik/vol event): AUD bị bán như proxy risk trước khi
  chuyện gì xảy ra với Úc.
- RBA governor speech ad-hoc, intermeeting narrative qua báo chí tài chính Úc (AFR).

### 1.4 Thông số ảnh hưởng (driver dashboard)

| Driver | Đại lượng theo dõi | Tần suất | Vai trò |
|---|---|---|---|
| RBA–Fed differential | cash rate gap, 2y ACGB–UST spread, 3m AUD-USD swap | realtime/daily | Xương sống carry & 2-6 tuần hướng |
| Iron ore | 62% Fe CFR Qingdao futures/spot, Dalian close, port inventory | daily/weekly | Proxy #1 của China demand; lead-lag 0-3 ngày |
| Copper | LME/COMEX Cu, copper concentrate TC/RC | daily/intraday | China manufacturing pulse, beta cao hơn vàng |
| China credit cycle | TSF yoy, credit impulse (delta of delta), M1-M2 gap | monthly | Regime 1-3 tháng, gate cho trend |
| VIX / risk sentiment | VIX, AUDJPY, S&P futures night session | intraday | Gate risk-on/off; xác định họ strategy sống |
| DXY / US rates | DXY, US10y real yield, IORB path | intraday/daily | Chân USD — thường chiếm ~nửa biến động |
| Gold (XAUUSD) | price, 25d risk reversal | daily | Hai kênh đối nghịch: risk-off (AUD↓ gold↑) vs ToT-producer (cùng ↑) — regime quyết định dấu |
| ToT tổng hợp | RBA Commodity Index (SDR), export price index | monthly | Trend nền months, chậm nhưng bền |

### 1.5 Correlation map (11 symbol) — AUDUSD vs

Con số là **khoảng phổ biến lịch sử** của rolling 60-day daily-return correlation; chúng
dao động theo regime — phải đo lại live, dùng như bản đồ chứ không phải hằng số (cần kiểm
chứng bằng đo đạc thực tế trước khi đưa vào model):

| Symbol | Khoảng điển hình | Cấu trúc & ghi chú |
|---|---|---|
| NZDUSD | **+0.75 → +0.90** | Cao nhất hệ thống: chung commodity-bloc + chung_RSP. Tạm nén khi RBA/RBNZ divergence policy (2026 RBA hawkish trong khi RBNZ cutting — compress mạnh hơn bình thường, cần đo). Chi tiết: AUDNZD là "pure China-vs-domestic" spread. |
| EURUSD | +0.35 → +0.65 | Chủ yếu USD-common-factor; rơi mạnh trong risk-off thuần (EUR bị bán cùng AUD khi USD/CHF/JPY được mua). |
| GBPUSD | +0.30 → +0.60 | Giống EURUSD nhưng nhiễu UK idiosyncratic (fiscal event) nhiều hơn. |
| USDCAD | **-0.40 → -0.70** | Commodity-bloc mirror + USD factor cùng chiều âm. Gãy khi oil đi một chiều riêng (OPEC shock) mà iron ore đi chiều khác. |
| USDJPY | **-0.20 → -0.60 khi risk dẫn dắt; ~0/+ khi USD dẫn dắt** | Regime-switching rõ nhất trong map: AUDJPY (cả hai non-USD) mới là thước risk thật. Đừng dùng USDJPY làm risk proxy tĩnh. |
| USDCHF | -0.25 → -0.60 | CHF safe-haven làm dấu âm bất đối xứng: corr âm sâu nhất đúng lúc risk-off. |
| XAUUSD | -0.10 → +0.35 (bất ổn) | Hai kênh đánh nhau: (a) risk-off → gold↑ AUD↓ (âm); (b) Úc là nước xuất vàng lớn + commodity bull cùng lúc (dương). Kênh nào thắng tuỳ real-rate & VIX regime — sign flip là tín hiệu regime. |
| XAGUSD | +0.10 → +0.45 | Bạc mang beta công nghiệp/China nên dương ổn hơn vàng. |
| BRENT | +0.15 → +0.40 | Kênh global growth + Úc xuất LNG/than (energy ToT dương). Dấu giảm khi oil-shock gây stagflation USD-bid. |
| WTI | +0.10 → +0.35 | Như Brent trừ nhiễu US-shale/WTI-specific storage. |
| NATGAS | -0.10 → +0.15 | Gần zero, weather-driven; kênh LNG Nhật-Trung mờ, chỉ dùng như noise control. |

**Phân rã nhân tố** (khung hiểu, không phải mô hình ước lượng): ~(1) USD common factor
(DXY) chiếm chunks lớn variance mọi pair USD; (2) commodity/ToT factor nhóm {AUD, NZD,
CAD, XAG, copper, iron ore}; (3) risk-appetite factor dài {AUD} vs {JPY, CHF, USD}; (4)
China-specific factor {AUD, NZD, XAG, iron ore, copper, HK equities}. AUDUSD đứng ở giao
của cả bốn — vì thế nó vừa giàu tín hiệu vừa dễ bị "driver chồng nhau" phá model đơn.

**Regime matrix — correlation thay đổi thế nào theo bối cảnh** (định tính, để đo):

| Regime | NZDUSD | USDJPY | XAUUSD | USDCAD | Hệ quả |
|---|---|---|---|---|---|
| Risk-on + USD-weak (global reflaton, 2017, 2021-H1) | +0.85+ | -0.3 | +0.3 | -0.6 | Cross-asset confirm mạnh nhất —edge S61/S63/S66 tốt |
| Risk-on + USD-strong (US exceptionalism, 2018-19 style) | +0.7 | ~0/+ | ~0 | -0.4 | USD-leg chèn ép: fade residual DXY (S65) sống |
| Risk-off + USD-bid (crisis, 03/2020) | +0.9 | âm sâu | -0.4 | -0.2 | MR chết; S100/S91 bắt buộc; gold-channel âm |
| Risk-off + USD-weak (stagflation/China-only shock) | +0.8 | ~0 | +0.4 | -0.5 | Gold-channel dương —AUD trụ hơn; S64 là chốt |

### 1.6 Trung thực: bối cảnh nào các họ strategy hay CHẾT trên AUDUSD

- **Mean-reversion chết** trong China stimulus surprise / tariff headline tape (giá đi
  một chiều 100+ pips không nhìn kèm overbought); và trong RBA/Fed tuần họp.
- **Trend chết** trong "talking stimulus" tape TQ 2024-2026: mỗi headline gây thrust 3
  ngày rồi quay đầu — chuỗi lower-high giả tạo chop giết trend-follower. Range regime nửa năm
  2026 (Fed quay hawkish đối đầu RBA) là điển hình.
- **Carry chết** khi differential hai chiều hẹp (chính 2026) hoặc khi vol spike nuốt
  coupon (Aug-Yen-carry-unwind-type events).
- **Breakout chết** trong Asian session thanh khoản mỏng (false break quanh data TQ khi
  Tokyo nghỉ), và trong "coiled but no catalyst" days.
- **Stat-arb AUDNZD chết** khi RBNZ/RBA policy path tách (đang xảy ra 2026) — cointegration
  break, z-score treo 2-3 sigma hàng tuần.
- **Cross-asset lead-lag (iron ore) chết** khi iron ore bị driver supply riêng (bão WA,
  Brazil supply, TQ sáp policy) — lead-lag đổi dấu.
- **Event strategy chết** nếu backtest theo giờ local Úc mà không xử lý **daylight saving
  hai bán cầu lệch nhau** (tháng Oct/Nov & Mar/Apr events lệch 1 tiếng) — bug kinh điển.

### 1.7 Đặc tính thống kê & các episode lịch sử tiêu biểu

- **Vol profile trong ngày (khung quan sát, cần đo lại)**: daily range trung bình ~50–90
  pips tuỳ regime (calm 2017-19 ~60, high-vol 2020/2022 ~90+); range Asian session thường
  20–35 pips; hai cửa sổ vol cao nhất là London mở (07:00–09:00 UTC) và overlap
  (12:00–15:00 UTC); ngày RBA 04:30 UTC là đỉnh spike riêng.
- **Phân phối**: return có fat tails & vol clustering mạnh (kiểu GARCH); skew âm rõ trong
  crisis (đợt sell AUD nhanh hơn đợt buy); weekend gap thường <20 pips nhưng đuôi trái dài
  (CNY 08/2015, COVID 03/2020 là ví dụ gap khủng).
- **Episode cần thuộc (để phân tầng backtest)**:

| Giai đoạn | Chuyện gì | Bài học cho strategy |
|---|---|---|
| 2008 GFC | Carry unwind, AUD -~35% peak-trough | Carry không có stop = chết; S100 cần thiết |
| 2010-11 | Iron ore/than siêu chu kỳ, AUD trên parity USD | ToT driver mạnh nhất lịch sử hiện đại; epoch "China boom" |
| 2013 | Taper tantrum + RBA cut | Differential hai chiều nhanh; MR chết |
| 08/2015 | CNY devalue bất ngờ | Gap risk cuối tuần/đầu tuần; S18 phải có event gate |
| 2016-19 | Range thấp vol, RBA đứng yên | Session/time strategies phát triển; trend đói |
| 2018 | Trade war một | China-headline tape —sinh họ "stimulus-talk" whipsaw |
| 03/2020 | COVID crash ~0.55 rồi V-recovery | Beta risk áp đảo mọi driver riêng; V-bottom MR thần kỳ |
| 2021-22 | Fed hike thẳng + China lockdown | Differential & risk cùng đè AUD (~0.62) |
| 08/2024 | Yen carry unwind | Carry-family cần kill-switch liên FX |
| 2025-26 | RBA hawkish trở lại (4.35%), Fed hike lại 16/09/2026; AUD pullback ~4% giữa năm | Chế độ "hai CB cùng thắt" mới —static carry chết, spread momentum sống |

### 1.8 Data & cost checklist cho lane AUDUSD (chuẩn bị trước backtest)

- **Minimum data stack**: (1) AUDUSD tick/M1 bid (đủ dài ≥10 năm, qua ≥2 epoch China);
  (2) event calendar có giờ local gốc (AEST/Beijing/NY) + consensus survey cho RBA, AU
  CPI/labour, FOMC, US CPI/NFP, China PMI/TSF/LPR/trade; (3) iron ore 62% Fe daily (SGX
  TIO hoặc Platts — chọn một nguồn duy nhất); (4) copper, DXY, VIX, SPX futures overnight;
  (5) yields 2y/10y ACGB-UST; (6) forward/swap points 3m-12m; (7) COT weekly
  (disaggregated); nice-to-have: options 25d RR, Mysteel port inventory, retail
  positioning feed.
- **Cost model trung thực**: spread theo session (Asian ×2–3 lần London), slippage Event
  window (mô phỏng thêm 5-15 pips quanh RBA/China print), swap chính xác theo dấu &
  broker, commission; mọi kết quả phải chạy sensitivity ×2 chi phí trước khi tin.
- **Repro hygiene**: canonical timezone = UTC nhưng event stamp giữ local gốc + DST flag;
  holiday calendar ba thị trường (AU, CN, US/UK/JP trùng khung ảnh hưởng); ghi rõ nguồn
  từng data line vào trial ledger.

### 1.9 Câu hỏi nghiên cứu mở (đặt cho phase backtest)

1. Lead-lag iron ore→AUD còn tồn tại thật không trong 2021-2026, hay đã bị arb đi vì
   cả hai giờ giao dịch giờ trùng nhau hơn (SGX TIO qua đêm)? (kiểm chứng S61)
2. Trong chế độ "hai CB cùng hawkish" (2026), 2y-spread momentum còn dẫn spot khi hai
   bên cùng đổi kỳ vọng? (S8/S35)
3. Asia-session MR edge có còn sau khi spread retail hạ xuống sub-pip? (S11/S13)
4. China credit impulse mất sức dự báo bao nhiêu khi property chuyển sang "quản lý suy
   giảm" thay vì "chu kỳ"? (S4/S55)
5. RBA-drift (S51) có asymmetric theo hướng hike vs cut không —và có còn khi RBA họp
   8 lần/năm với presser chuẩn hoá?
6. Correlation AUD-gold đã đổi cấu trúc vĩnh viễn chưa (eternal safe-hid gold vs
   producer gold)? (S64/S95)
7. AUDNZD còn là cặp "mean-reverting tin được" sau chặng RBA-hawk/RBNZ-dove? (S81/S84)

---

## 2. 100 strategy ideas

Quy ước template: **S<n> — tên (family)** — Hypothesis · Signal · Trade · Risk · Data ·
Coupling. Timeframe viết tắt: M5/H1/H4/D1/W1. "CSI" = China scheduled info. Mọi ngưỡng là
khởi điểm cần optimize-kiểm-chứng, không phải lời khuyến nghị.

### Family A — Trend / Momentum

**S1 — EMA-stack multi-timeframe trend (Trend/Momentum)** — Hypothesis: AUDUSD trending
giỏi trong macro-trend vì driver (ToT, rate path) chậm và bền · Signal: H4: EMA20>EMA50>EMA200 và giá trên EMA200-D1 · Trade: entry pullback EMA20-H4 theo hướng stack, stop dưới swing H4 gần nhất, trail EMA50-H4 · Risk: sideways chop giữa hai meeting CB làm ăn liệt stop · Data: OHLCV AUDUSD · Coupling: chỉ long khi China credit impulse không âm.

**S2 — Donchian 20/55 breakout Turtle (Trend/Momentum)** — Hypothesis: channel breakout
nắm được nhịp China-stimulus thrust · Signal: close D1 qua high 20 ngày (entry) / 55 (stop&reverse) · Trade: stop-and-reverse hai chiều, size theo ATR14 (risk 0.5%/trade) · Risk: whipsaw trong range; false break Asian session · Data: D1 OHLC · Coupling: gate ADX14>20.

**S3 — ADX-filtered momentum persistence (Trend/Momentum)** — Hypothesis: momentum tự
feed khi trend strength cao (positioning flows bổ sung chiều giá) · Signal: ADX14-D1>25 & MACD histogram cùng dấu 3 bar · Trade: vào theo dấu MACD khi ADX cross 25, exit khi ADX<20 · Risk: ADX lag — vào muộn mất nửa move · Data: D1 OHLC · Coupling: VIX<25.

**S4 — China credit impulse macro trend (Trend/Momentum)** — Hypothesis: credit impulse
TSF dẫn hướng AUDUSD 1-3 tháng vì nó là cầu beforehand của thép/iron ore · Signal: TSF yoy 3M-MA đi lên/xuống xuyên zero + đồng bộ M1-M2 gap cùng dấu · Trade: nắm vị thế D1 theo dấu impulse, rebalance monthly sau khi TSF print, stop 2×ATR14-W1 · Risk: credit impulse "không chuyển sang demand thật" khi property chết (2025-26) — tín hiệu mờ dần · Data: China TSF/M1/M2 monthly, AUDUSD D1 · Coupling: iron ore price cùng dấu xác nhận.

**S5 — Iron-ore-confirmed trend filter (Trend/Momentum)** — Hypothesis: trend AUDUSD
không có confirmation commodity là trend USD-leg, có confirmation là trend thật · Signal: sign(momentum 20d của iron ore 62% Fe) == sign(trend AUDUSD EMA50-D1) · Trade: bật chiến lược trend S1/S2 theo điều kiện, không trade khi lệch dấu · Risk: iron ore driver supply riêng làm filter sai · Data: D1 iron ore + AUDUSD · Coupling: dùng S4 làm floor.

**S6 — Time-series momentum 3/6/12 tháng (Trend/Momentum)** — Hypothesis: TSMOM của FX
commodity có bằng chứng dài hạn —AUD là một trong các cross mạnh nhất · Signal: sign(AUDUSD hôm nay vs 63/126/252 ngày trước), đa số phiếu · Trade: position theo đa số sign, vol-target 10% annualized, rebalance tuần · Risk: ngay sau VIX spike sign lật liên tục · Data: daily close dài hạn · Coupling: DXY TSMOM ngược dấu xác nhận.

**S7 — Relative-strength dual momentum G10 (Trend/Momentum)** — Hypothesis: khi AUD là
đồng mạnh/yếu nhất G10, momentum tự tiếp tục nhờ allocation flow · Signal: rank 20d return của AUD trong 8 cặp USD-G10; chỉ trade AUDUSD khi AUD nằm top-1 hoặc bottom-1 và gap với hạng 2 > x bp · Trade: theo hạng, exit khi rời top/bottom-2 · Risk: rotation nhanh giữa AUD/NZD khi RBA-RBNZ tách · Data: 8 cặp G10 daily · Coupling: carry sign cùng chiều tăng edge.

**S8 — Rate-differential dislocation trend (Trend/Momentum)** — Hypothesis: spot lag
đập theo 2y ACGB-UST spread — khi gap mở rộng mà giá chưa đi, catch-up trend nổ ra · Signal: z-score(2y spread, 60d) > 1.5 cùng/đối dấu với 20d AUDUSD return (dislocation) · Trade: vào theo chiều spread, stop khi z quay về 0.5 · Risk: spread move bởi expectation, bị reverse nếu central bank surprise · Data: 2y yields hai nước, spot · Coupling: OIS path kỳ vọng.

**S9 — Vol-normalized momentum ladder (Trend/Momentum)** — Hypothesis: momentum đều step
khi scale theo vol sống sót qua cả hai regime · Signal: n-bar return chia ATR14; cộng dồn 3 khung (H4/D1/W1) cùng dấu · Trade: size nghịch ATR, thêmposition mỗi khi ladder thêm tầng, trail ATR-chandelier 3× · Risk: vol regime shift giữa chừng làm ladder lật · Data: OHLCV đa khung · Coupling: realized/implied vol ratio <1.2.

**S10 — Market-structure HH/HL break & retest (Trend/Momentum)** — Hypothesis: cấu trúc
swing D1 tự nhiên của AUDUSD cho continuation tốt hơn indicator · Signal: break swing high/low gần nhất với close-confirmation + retest không vỡ · Trade: entry tại retest, stop dưới retest low, target RR 2 · Risk: false structural break quanh số tròn 0.6600/0.6800 do option barrier · Data: D1 swings · Coupling: volume tick H1 xác nhận break.

### Family B — Mean-reversion

**S11 — Asia-range Bollinger fade (Mean-reversion)** — Hypothesis: trong khung Á không
driver, AUDUSD oscillator quanh giá trị đêm trước —edge MR địa phương · Signal: H1 z-score BB(20,2) vượt ±2 giữa 22:00–05:00 UTC và không có event scheduled · Trade: fade về band giữa, stop 1×ATR-H1, thoát trước 06:00 UTC · Risk: China unscheduled headline giữa fade · Data: H1 OHLC + calendar · Coupling: VIX<20 & DXY range ngày.

**S12 — RSI(2) extreme fade với trend filter (Mean-reversion)** — Hypothesis: short-term
exhaustion trong uptrend dài là điểm mua đều đặn (Connors-style) · Signal: RSI2-H1 <10 khi giá trên EMA200-D1 (và ngược cho short) · Trade: vào market, exit RSI2>60 hoặc 4 bar, stop dưới swing 5 bar · Risk: gap event qua đêm; dùng cho USD-leg driver thì yếu · Data: H1 · Coupling: chỉ dùng khi tuần không có RBA/FOMC.

**S13 — London-open spike reversal fade (Mean-reversion)** — Hypothesis: stop-hunt
London thường vượt đánh Asia range rồi quay về —cấu trúc lặp củaliquidity grab · Signal: giá vượt high/low range Á (22:00–06:00) ≥ 15 pips trong 07:00–09:00 UTC rồi close M15 ngược vào range · Trade: vào ngược spike, target giữa range Á, stop ngoài spike-extreme 5 pips · Risk: ngày có driver thật (China stimulus) spike không quay · Data: M15/H1 · Coupling: iron ore futures đêm đó flat.

**S14 — Session-VWAP deviation fade NY (Mean-reversion)** — Hypothesis: quanh VWAP
NY session,algo Mean reversion quanh anchored VWAP phổ biến · Signal: giá lệch VWAP-NY (từ 12:00 UTC) ≥ 1.8×SD-band · Trade: fade về VWAP, stop 2.2×SD, thoát 15:45 UTC trước fixing · Risk: trend-day FOMC/CPI · Data: tick/M5 NY session · Coupling: DXY cùng lệch chiều ngược (xác nhận USD-leg noise).

**S15 — Hurst-gate mean reversion (Mean-reversion)** — Hypothesis: MR chỉ sống khi chuỗi
anti-persistent —gate bằng Hurst exponent · Signal: rolling Hurst(100, H1) < 0.45 · Trade: bật S11/S12 chỉ khi gate mở; Hurst>0.55 thì tắt toàn MR · Risk: Hurst ước lượng nhiễu, biên 0.45-0.55 không định đoạt được · Data: H1 closes · Coupling: dùng S98 (HMM) thay nếu Hurst tốn.

**S16 — VIX-spike normalization reversion (Mean-reversion)** — Hypothesis: AUD bị bán
quá mức trong VIX spike rồi hồi khi VIX về —"risk-off overshoot decay" · Signal: VIX 5d-change > +20% rồi quay dưới mức spike; AUDUSD 5d-return < -1.5% · Trade: buy AUDUSD khi VIX bắt đầu bình thường hoá, stop dưới low spike, target 38.2%→61.8% retrace · Risk: VIX spike là stage-1 của crisis (2015-08, 2020-03) —cần stop kỷ luật · Data: VIX + spot · Coupling: AUDJPY cùng tín hiệu.

**S17 — DeMark TD-Sequential exhaustion fade (Mean-reversion)** — Hypothesis: count 9/13
đếm được cluster stop-reversal quanh driver wave · Signal: TD9 hoàn tất trên H4/D1 cùng hướng với divergence RSI · Trade: vào ngược sau price-flip, stop trên high/low của bar 9, target TD level đối xứng · Risk: trend mạnh đi đến count 13+ (continuation) · Data: OHLC H4/D1 · Coupling: iron ore/copper cùng exhaustion thì edge nhân.

**S18 — Overnight-gap fill Sydney (Mean-reversion)** — Hypothesis: gap giữa NY close và
Sydney open (đêm cuối tuần hoặc sau holiday Á) là liquidity artifact, phần lớn fill · Signal: gap cuối tuần > 25 pips và không có event weekend · Trade: trade về giá đóng NY tuần trước ngay Monday Sydney session, stop half-gap · Risk: gap có thật sau G7/PBoC weekend event —check calendar trước · Data: W1/M5 open-close · Coupling: futures DXY gap cùng chiều.

**S19 — 3-week streak counter-trend không-driver (Mean-reversion)** — Hypothesis: ba
tuần liền cùng dấu không kèm macro catalyst mới thường là positioning extreme · Signal: 3 tuần close cùng dấu + COT spec positioning cùng chiều > 1 sd + không có thay đổi rate-path kỳ vọng trong kỳ · Trade: counter vào đầu tuần 4, stop khi tuần thứ 4 break extreme, target 2-3 tuần ngược · Risk: đây là cách catch falling knife —bắt buộc gate COT/catalyst · Data: W1 + COT + rate expectations · Coupling: S71 positioning extreme.

**S20 — NZD-lead reversion sync (Mean-reversion)** — Hypothesis: NZDUSD (thanh khoản
thấp hơn) revert trước, AUDUSD theo —lead-lag MR cặp commodity · Signal: NZDUSD đã revert 50% của swing H4 trong khi AUDUSD chưa (spread AUDNZD giãn) · Trade: fade AUDUSD theo hướng NZD đã chọn, stop khi AUDNZD break thêm 0.3% · Risk:_news Úc riêng lúc đó AUD đi đúng (không phải lag) · Data: H4 hai cặp · Coupling: RBA/RBNZ không họp tuần đó.

### Family C — Breakout / Vol-expansion

**S21 — London range breakout box (Breakout/Vol-expansion)** — Hypothesis: range Á tích
lũy thông tin China overnight, London phá vỡ theo chiều thật · Signal: box 22:00–06:00 UTC; break M15 close ngoài box + tick-volume trong top quartile · Trade: stop-entry ngoài box, stop half-box, trail 2×ATR-M15 · Risk: false-break ngày DXY-neutral —lọc bằng EURUSD đồng thời break cùng chiều · Data: M15 + tick volume + calendar · Coupling: China data đêm đã print cùng chiều.

**S22 — Asia-compression breakout vào China data (Breakout/Vol-expansion)** — Hypothesis:
trước release TQ 01:30-02:00 UTC, giá coil; release chọn hướng với continuation · Signal: ATR-H1 của 4 giờ trước release < 60% median; straddle stop-entry ±0.4×ATR-M5 quanh pre-release price vào đúng giờ · Trade: bracket hai chiều, cancel chân kia khi một chân trigger, exit end-of-London · Risk: whipsaw cả hai chân khi số liệu mixed (PMI vs employment sub) —thêm rule 1-reentry · Data: M5 + release lich chính xác đến phút · Coupling: deviation surprise >1 sd mới giữ qua London.

**S23 — NR7 squeeze weekly (Breakout/Vol-expansion)** — Hypothesis: tuần
range hẹp nằm
trong chuỗi trend month là accumulation · Signal: weekly range của tuần này < min 7 tuần gần nhất, và giá trong nửa trên/dưới của 20-week range · Trade: bracket thứ Hai tuần sau theo hướng nửa nằm, stop trong squeeze-range · Risk: squeeze do holiday-thiếu liquidity (Giáng sinh) —loại tuần lễ · Data: W1/D1 · Coupling: iron ore cùng squeeze cùng hướng.

**S24 — RBA-day bracket straddle (Breakout/Vol-expansion)** — Hypothesis: RBA 04:30 UTC
trong book mỏng tạo impulse mạnh rồi continuation trong ngày nếu surprise thật · Signal: 30 phút trước RBA đặt stop-entry ±0.6×ATR-M5 quanh giá; chỉ giữ nếu decision lệch survey-consensus · Trade: chân bị cancel khi chân kia fill; trail thời gian 4h · Risk: RBA "hawkish hold" gây spike hai chiều —cần đọc statement, chỉ giữ khi rate/statement lệch rõ · Data: M5, RBA calendar, consensus survey · Coupling: OIS-implied probability trước họp lệch >70% thì skip (đã priced).

**S25 — Iron-ore-inventory surprise vol expansion (Breakout/Vol-expansion)** —
Hypothesis: Mysteel port inventory weekly print đột biến →gap risk cho chuỗi ToT, AUDUSD breakout theo chiều · Signal: weekly inventory change > 1.5 sd lịch sử + Dalian iron ore close cùng dấu · Trade: breakout theo hướng của Dalian vào Sydney open, stop pre-break swing, target 2 ngày · Risk: inventory tăng do logistics (đến cảng) chứ không phải cầu yếu · Data: Mysteel weekly, D1 iron ore, AUDUSD H1 · Coupling: S61 lead-lag cùng chiều.

**S26 — Bollinger-width percentile expansion (Breakout/Vol-expansion)** — Hypothesis:
sau khi BB-width (20) D1 vào decile thấp nhất, expansion breakout có persistence · Signal: BBW percentile <15 trong 5 ngày rồi close D1 ngoài band · Trade: theo break, stop về mid-band, size theo BBW khi break · Risk: low-vol persistent (summer) —decay trước khi break; thêm timeout 8 ngày · Data: D1 · Coupling: realised vol ratio xác nhận expansion thật.

**S27 — Failed-breakout reversal trap (Breakout/Vol-expansion)** — Hypothesis: break
rồi thủng lại trong 1 giờ là trap điển hình của Asian-session thin book —đi ngược rất đều · Signal: break box/level với volume cao nhưng close M15/H1 ngược lại trong 2 bar · Trade: vào ngược, stop ngoài fake-extreme, target đối diện box · Risk: "trap" thật ra là retest của break thật —chỉ chơi khi volume của bar revert > volume bar break · Data: M15 + volume · Coupling: dùng sau S21/S22 để tái sử dụng structure.

**S28 — EURUSD-lead co-movement breakout (Breakout/Vol-expansion)** — Hypothesis: trong
khoảng 12:00-16:00 UTC, EURUSD break level quan trọng thường dẫn AUDUSD vài giây-phút (USD-common-factor truyền qua liquid pair trước) · Signal: EURUSD break 20d-high intraday trong khi AUDUSD chưa rời range 1 giờ · Trade: buy/sell AUDUSD theo chiều EUR lead, stop range-local, scalp 30-60 phút · Risk: AUD-specific headline phủ nhận USD-leg —skip nếu có event Úc/TQ trong giờ đó · Data: tick hai cặp đồng bộ · Coupling: DXY break cùng chiều EUR.

**S29 — Weekly high/low persistence break (Breakout/Vol-expansion)** — Hypothesis: phá
swing W1 cấp trend continuation tuần dài, sạch hơn daily noise · Signal: close H4 ngoài high/low tuần trước ≥ 2 lần liên tiếp · Trade: theo break với stop trong tuần trước, giữ đến khi 2×ATR-W1 hoặc flip structure · Risk: đầu tháng và cuối tháng flow fixing phá cấu trúc —giảm size tuần đó · Data: H4/W1 · Coupling: S66 risk gate.

**S30 — Keltner retest continuation (Breakout/Vol-expansion)** — Hypothesis: break thật
thường retest channel vừa vỡ rồi tiếp —mua retest an toàn hơn mua đuổi break · Signal: giá break Keltner(20,2.5ATR) D1, rồi quay chạm EMA20-D1 trong 5 ngày không đóng ngược channel cũ · Trade: entry EMA20 touch theo hướng break, stop dưới retest low · Risk: retest chuyển thành full reversal khi catalyst cũ chết (stimulus thất bại) · Data: D1 · Coupling: S5 iron ore cùng dấu.

### Family D — Carry / Rate-differential

**S31 — Classic sign-of-carry (Carry/Rate-differential)** — Hypothesis: AUDUSD hưởng
roll khi differential dương đủ lớn · Signal: 3m AUD-USD swap point > ngưỡng (ví dụ +30bp annualized) · Trade: long spot giữ khi swap dương, exit khi swap về 0/âm; sizing theo drawdown budget · Risk: 2026 differential hẹp + Fed cũng hawk → swap chạm 0, strategy nhạt; vol spike nuốt coupon · Data: forward/swap quotes, spot · Coupling: S33 carry/vol.

**S32 — Carry với trend filter (Carry/Rate-differential)** — Hypothesis: carry sống khi
hướng giá cùng chiều (carry+trend double engine) · Signal: swap 3m dương VÀ giá trên EMA50-D1 · Trade: long khi cả hai đúng, flat khi lệch dấu, stop trailing 3×ATR-D1 · Risk: unwind carry (risk-off) —cắt bằng S91 VIX gate · Data: swap + D1 · Coupling: AUDJPY cùng chiều (risk xác nhận).

**S33 — Carry-to-vol ratio gate (Carry/Rate-differential)** — Hypothesis: carry chỉ đáng
nhặt khi yield/vol ratio cao (risk-adjusted) · Signal: (annualized 3m swap) / (20d realized vol) > 0.25 · Trade: bật carry position theo sign, vol-target 8%, de-risk khi ratio <0.1 · Risk: realized vol lag —dùng implied vol thay khi có data · Data: swap, OHLCV (hoặc IV) · Coupling: kèm S16 nếu vol spike xảy ra.

**S34 — Forward-curve rolldown capture (Carry/Rate-differential)** — Hypothesis: khi
curve steep, mua outright forward (giá thấp hơn spot) và giữ cho spot-converge tạo tổng return dương cả khi giá flat · Signal: forward premium 3m >1% annualized & đường path OIS không đảo chiều trong quý · Trade: mua AUDUSD 3m forward, hold, roll hàng tháng, cắt khi curve flatten >50% · Risk: expectation shock làm spot rơi nhanh hơn rolldown bù · Data: forwards, OIS curve · Coupling: RBA hawkish bias xác nhận.

**S35 — 2y-spread momentum (Carry/Rate-differential)** — Hypothesis: thay đổi kỳ vọng
policy (2y spread momentum 20d) dẫn spot 1-4 tuần · Signal: 20d-change của ACGB2y-UST2y > +10bp → long bias; < -10bp → short bias · Trade: position theo bias, rebalance tuần, stop khi momentum sign flip 2 phiên liên tiếp · Risk: cả hai CB cùng đổi kỳ vọng → spread flat nhưng spot vẫn đi (USD-leg chung) · Data: 2y yields · Coupling: DXY momentum đối dấu xác nhận.

**S36 — Carry hedged bằng AUDJPY (Carry/Rate-differential)** — Hypothesis: tách "USD
carry" khỏi "risk beta": long AUDUSD + short AUDJPY×beta bỏ phẩn risk · Signal: beta 60d của AUDJPY trên AUDUSD >0.6 · Trade: long AUDUSD, short AUDJPY size beta —thu USD-carry, neutral risk · Risk: AUDJPY borrow cost & correlation break trong event · Data: hai cặp + rates · Coupling: dùng khi VIX trung bình cao.

**S37 — Forward-premium reversal (Fama) (Carry/Rate-differential)** — Hypothesis: khi
forward premium cực đoan (expectation quá đà), spot revert ngược kỳ vọng forward —uncovered parity thất bại · Signal: 12m forward premium z-score(3y) > ±2 · Trade: đi ngược hướng forward-implied direction, horizon 1-3 tháng, stop z>3 · Risk: regime hiking thật bền (2026 RBA) làm z treo dài · Data: forwards dài hạn · Coupling: ToT cùng chiều thì mới vào.

**S38 — ACGB-UST 10y sovereign spread (Carry/Rate-differential)** — Hypothesis: spread
trái phiếu chính phủ 10y là carry-tham chiếu chậm bền hơn swap ngắn · Signal: 60d-change của spread > ±20bp · Trade: position theo dấu với lag 1 tuần, stop khi spread cross-back 50% move · Risk: spread move do supply/technical trái phiếu (auction) không phải macro · Data: 10y yields · Coupling: S35 cùng dấu nhân edge.

**S39 — RBA-cycle-aware carry (Carry/Rate-differential)** — Hypothesis: giảm carry qua
các tuần decision (event risk) tăng sharpe rõ · Signal: calendar RBA+FOMC; flat 24h trước decision, vào lại 24h sau nếu path không đổi · Trade: quản lý position quanh event, giữ phần còn lại theo S32 · Risk: bỏ lỡ post-decision drift —nếu muốn giữ drift dùng S51 · Data: swap + calendar · Coupling: kiểm chứng trên 3 năm gần.

**S40 — Contrarian value-carry (Carry/Rate-differential)** — Hypothesis: khi differential
sâu âm VÀ ToT đang cải thiện, AUD cheap về macro —mua value · Signal: 3m swap < -50bp annualized + RBA Commodity Index 3m-change >0 · Trade: accumule long theo lưới 1% step, exit khi swap về dương hoặc ToT flip, stop khi ToT -2 sd · Risk: catching knife trong China hard-landing · Data: swap + RBA commodity index · Coupling: S4 credit impulse hết giảm.

### Family E — Session / Time-of-day / Seasonality

**S41 — Asia-session momentum continuation (Session/Time-of-day)** — Hypothesis: flow
Tokyo theo hướng mở Sydney thường tiếp tục đến giờ London —inertia session Á · Signal: return 22:00-02:00 UTC > +0.3×ATR-H1 thì bias chiều đó cho 02:00-07:00 · Trade: vào 02:00 theo chiều, stop ATR-H1, thoát 07:00 UTC · Risk: đêm có data TQ 02:00+ thì khác cấu trúc —loại đêm đó · Data: H1 · Coupling: Nikkei/ASX mở cùng chiều.

**S42 — Overlap momentum window (Session/Time-of-day)** — Hypothesis: 12:00-16:00 UTC
là khung duy nhất AUDUSD "mặc" USD-leg hoàn toàn —momentor trong khung này thuần nhất nhất · Signal: break high/low của 11:00-12:00 M15 trong khung overlap + DXY break cùng · Trade: theo break, stop micro, target 25-35 pips, không giữ qua 16:30 · Risk: pre-FOMC/CPI dead-tape —lọc event calendar · Data: M15 + calendar · Coupling: EURGBP/EURUSD cùng break.

**S43 — Month-end fixing flow bias (Session/Time-of-day/Seasonality)** — Hypothesis:
rebalancing equity/FX quanh WMR 4pm London các ngày cuối tháng tạo drift ngắn có hướng theo month-return chữ V · Signal: nếu tháng đó US equities down (up), USD-bid (offer) flow vào ngày L-1..L+1 · Trade: bias ngược AUDUSD tương ứng trong 16:00-16:30 UTC window, scalp 15-40 pips · Risk: quy mô flow yếu dần khi passive/deriv-based rebal —kiểm chứng yearly · Data: SPX monthly return, AUDUSD M5 · Coupling: magnitude month-return >2%.

**S44 — AU fiscal year-end repatriation (Session/Time-of-day/Seasonality)** — Hypothesis:
30/06 superannuation/corporate hedging_AUD-demand kéo AUDUSD quanh cuối năm tài chính Úc · Signal: 5 ngày quanh 30/06, bias long nhẹ + realized vol giảm · Trade: long nhỏ 24-28/06, thoát 01-02/07, stop 1×ATR-D1 · Risk: hiệu ứng nhỏ, có thể bị macro month-end đè —backtest với caution (cần kiểm chứng) · Data: D1 nhiều năm · Coupling: skip năm có FOMC/RBA rơi đúng tuần đó.

**S45 — China-data window bracket (Session/Time-of-day/Seasonality)** — Hypothesis: các
release 01:30-02:00 UTC (PMI/credit/LPR) tạo jump có continuation 2-6 giờ khi surprise lớn · Signal: deviation của print vs consensus >1 sd; hướng jump xác nhận trong bar M5 thứ 2 · Trade: vào theo hướng bar đầu sau khi bar 2 confirm, stop dưới bar release, exit 4h · Risk: revision/mixed print; whipsaw khi Tokyo holiday · Data: M5 + data releases + consensus · Coupling: surprise cùng chiều iron ore futures cùng sáng.

**S46 — Day-of-week seasonality (Session/Time-of-day/Seasonality)** — Hypothesis: Monday
range-extension (Asia re-entry) và Friday squaring tạo pattern tuần · Signal: thống kê 10 năm: Monday Asia range mở rộng vs median; Friday NY reversal sau 18:00 UTC · Trade: Monday: chơi breakout range Á thay vì fade; Friday: đóng/day-trade only sau 18:00 · Risk: mùa vụ yếu, phụ thuộc regime —chỉ dùng như prior, không standalone · Data: H1 10 năm · Coupling: kết hợp S21/S11.

**S47 — Sydney-open gap fade (Session/Time-of-day/Seasonality)** — Hypothesis: mở tuần/
mở phiên Sydney sau ngày nghỉ Á thường gap vài pip rồi fill trong giờ đầu · Signal: gap Sydney open vs NY close trước > 8 pips (không phải cuối tuần) · Trade: fade gap, stop half-gap, target pre-gap · Risk: gap sau event US đêm —check overnight news · Data: M5 opens · Coupling: futures AUD (6A) open cùng hướng xác nhận artifact.

**S48 — Triple-swap Wednesday positioning (Session/Time-of-day/Seasonality)** —
Hypothesis: swap 3x Wed tạo distortion positioning nhỏ —giá bị kéo về hướng có carry vào Tue-Wed · Signal: swap dương → bias nhẹ long Tue close→Wed 04:00 UTC · Trade: scalp bias 10-20 pips cùng hướng carry, không giữ qua Wed NY · Risk: hiệu ứng nhỏ & broker-specific; (cần kiểm chứng) trên feed riêng · Data: M5 + swap schedule · Coupling: chỉ khi không event.

**S49 — Sep-Oct risk-off seasonal (Session/Time-of-day/Seasonality)** — Hypothesis: lịch
sử: mùa thu (Sep-Oct) hay có equity risk-off → AUD yếu hơn trung bình trong thập kỷ (2018, 2022...) · Signal: bias short AUDUSD 15/09-31/10 khi VIX term-structure flat/inverted · Trade: short bias nhỏ, stop 1.5×ATR-W1, thoát khi VIX re-steepen · Risk: năm risk-on mạnh (boycott) —nhất thiết kết hợp VIX gate, không standalone · Data: W1 + VIX lịch sử · Coupling: AUDJPY breakdown xác nhận.

**S50 — Overnight US-futures beta catch-up (Session/Time-of-day/Seasonality)** —
Hypothesis: AUD phản ứng chậm hơn so với move futures S&P/ES overnight —catch-up đầu phiên Sydney · Signal: ES futures 00:00-21:50 ET change > 0.7% và AUDUSD chưa move tương đương beta 30d · Trade: vào theo hướng beta-residual khi Sydney mở, stop 0.5×ATR-H1, exit khi residual close về 0 · Risk: overnight move do USD-news thì AUD phản ứng khác —loại khi DXY cũng break · Data: ES futures + AUDUSD H1 + DXY · Coupling: beta rolling cập nhật tuần.

### Family F — Event / Data-driven

**S51 — RBA surprise post-decision drift (Event/Data-driven)** — Hypothesis: surprise
họp RBA (vs consensus) tạo drift 2-3 ngày vì book mỏng + slow money repricing · Signal: decision hoặc statement tone lệch consensus ≥1 mức (hike thay vì hold...) · Trade: vào 30-60 phút sau decision theo hướng surprise (chờ spike ban đầu dịu xuống), stop dưới extreme spike, exit 48-72h hoặc khi phút RBA governor speech flip · Risk: statement "hawkish hold" gây drift yếu; US event giữa drift · Data: RBA calendar + consensus + statement text · Coupling: OIS-implied trước họp càng lệch outcome thì drift càng mạnh.

**S52 — AU CPI asymmetry learned reaction (Event/Data-driven)** — Hypothesis: thị trường
phản ứng bất đối xứng với CPI Úc: miss nóng → move lớn hơn miss lạnh (RBA bias) —học sign và magnitude riêng · Signal: monthly CPI indicator vs consensus; riêng trim-mean core · Trade: theo hướng surprise với size tỷ lệ |surprise|, giữ qua London; core surprise thì giữ qua ngày · Risk: CPI print trùng ngày FOMC tuần —giảm size một nửa · Data: CPI releases + consensus · Coupling: RBA meeting gần nhất <3 tuần thì nhân phản ứng.

**S53 — Labour-force surprise trade (Event/Data-driven)** — Hypothesis: unemployment
rate là biến RBA nhạy nhất (2024-25 framework) —surprise URate mạnh hơn surprise jobs · Signal: URate lệch consensus ≥0.15pp bất kể employment change · Trade: theo chiều nghịch với URate surprise (URate↓ → long AUD), entry sau bar M5 thứ 2, stop 20 pips, target 60 · Risk: participation swing làm print nhiễu —đọc kèm participation rate · Data: ABS labour force + consensus · Coupling: tháng có CPI cùng tuần thì skip.

**S54 — China PMI surprise với iron-ore confirm (Event/Data-driven)** — Hypothesis: PMI
surprise chỉ đáng trade khi commodity cùng xác nhận (tránh headline fade) · Signal: Caixin/NBS PMI lệch ≥0.5đ + iron ore futures cùng chiều trong 30 phút · Trade: theo chiều sau confirm, stop dưới swing 30-phút, exit end-of-day Á · Risk: PMI divergence NBS-vs-Caixin —chọn hướng theo Caixin (smaller firms nhạy China demand AUD hơn) · Data: PMI releases + iron ore H1 · Coupling: copper cùng confirm tăng edge.

**S55 — TSF/credit print macro entry (Event/Data-driven)** — Hypothesis: monthly TSF
surprise đặt lại hướng 1-2 tuần của AUDUSD (không phải intraday) · Signal: TSF yoy lệch ≥1pp vs consensus hoặc credit impulse 3m flip sign · Trade: position theo dấu vào cuối phiên Á ngày print, giữ 5-10 ngày, stop 1.5×ATR-D1 · Risk: print sai lịch sử/revision; property-dead regime làm credit→demand yếu (2025-26) —cần S4 làm nền · Data: TSF series + calendar · Coupling: iron ore cumulative return 3 ngày sau print cùng dấu.

**S56 — LPR regime-shift event (Event/Data-driven)** — Hypothesis: LPR hiếm khi đổi —
khi đổi là tín hiệu regime TQ lớn, AUD drift nhiều tuần · Signal: bất kỳ LPR change (5y hay 1y) bất kỳ hướng · Trade: vào theo hướng easing/tightening sau 1 giờ, giữ 10-20 ngày với trail ATR-D1 · Risk: LPR cut "symbolic" 5bp chỉ tạo blip —phân tầng theo magnitude (≥10bp mới đáng) · Data: LPR releases · Coupling: PBoC RRR/policy rate cùng tuần → cộng hưởng.

**S57 — FOMC-driven AUDUSD reaction (Event/Data-driven)** — Hypothesis: FOMC move
AUDUSD chủ yếu qua USD-leg và có mô hình reaction chuẩn (spike→fade→resume) 18:00 UTC · Signal: Fed decision/SEP lệch expectation hawkish/dovish · Trade: 15 phút sau statement vào theo hướng hawkish→short AUDUSD, stop ngoài initial spike, target qua NY close; presser flip thì thoát · Risk: RBA cùng tuần hai CB đánh nhau —thì dùng S8 thay · Data: FOMC calendar + statement + SEP · Coupling: AUDJPY cùng phản ứng thì đó là risk-leg, giữ yên hơn.

**S58 — Commodity export price monthly drift (Event/Data-driven)** — Hypothesis: trade
balance + export price index Úc phản ánh ToT với lag, thị trường under-react · Signal: monthly export value iron ore/coal ≈ volume×giá tăng 2 tháng liền · Trade: long bias AUDUSD sau print thứ 2, horizon 1 tháng, stop ATR-W1 · Risk: giá hàng hoá đã về lại khi index print (lag) —dùng futures realtime làm gate · Data: ABS trade series · Coupling: S38 spread cùng dấu.

**S59 — Minutes/speech tone word-count (Event/Data-driven)** — Hypothesis: hawkish/dovish
word shift trong minutes & speeches thống kê được, dẫn spot · Signal: đếm từ "inflation/risk" bias đổi >1 sd so documents trước · Trade: position theo tone drift 1-2 ngày sau release phút 00:30 UTC · Risk: NLP noise; thống kê cần labelled corpus (cần kiểm chứng) · Data: RBA minutes/speeches text · Coupling: OIS 1y change cùng tuần xác nhận.

**S60 — Post-event vol crush re-entry (Event/Data-driven)** — Hypothesis: sau event, vol
impl collapse nhưng spot giữ hướng —vào lại theo hướng event sau khi vol về median · Signal: realized vol H1 24h sau event <60% của event-day vol, spot vẫn cùng phía pre-event mean · Trade: vào theo chiều event residual, stop 1×ATR mới, horizon 2 ngày · Risk: event "chưa xong" (two-step: RBA rồi minutes) —chỉ dùng sau event cuối chuỗi · Data: OHLC + IV nếu có · Coupling: S51/S57 chain.

### Family G — Cross-asset / Correlation

**S61 — Iron-ore lead-lag (Cross-asset/Correlation)** — Hypothesis: iron ore 62% Fe daily
change dẫn AUDUSD 0-3 ngày (information flow TQ → commodity trước → FX sau) · Signal: iron ore 3-day cumulative return > +2% (hoặc <-2%) khi AUDUSD 3-day return cùng dấu <0.5% (lag) · Trade: theo hướng iron ore, entry cuối phiên NY, giữ 2-4 ngày, stop khi AUDUSD catch-up xong residual=0 · Risk: iron ore supply-driven (bão WA/Brazil) làm lag đổi dấu —gate bằng news loại supply events · Data: iron ore D1 + AUDUSD · Coupling: copper cùng dấu tăng xác suất.

**S62 — Copper-AUD divergence arb (Cross-asset/Correlation)** — Hypothesis: khi copper
đi mạnh mà AUD không theo, residual đóng nhanh —AUD là laggard bị ràng buộc · Signal: 20d-return của copper - beta×20d-return AUDUSD > 1.5 sd của residual lịch sử · Trade: long AUDUSD (short khi residual âm), stop 1 sd thêm, exit residual=0 · Risk: copper idiosyncratic (strike/mine) —residual không đóng · Data: copper + AUDUSD · Coupling: đồng thời kiểm tra DXY để loại USD-leg.

**S63 — SPX-futures → AUD next-session (Cross-asset/Correlation)** — Hypothesis: risk
appetite đêm Mỹ định hình AUDUSD phiên Á hôm sau (beta ổn định hơn cùng tuần) · Signal: SPX/ES overnight return >1 sd & VIX không spike quá +30% · Trade: vào Sydney open theo hướng beta-residual, stop 0.6×ATR-H4, exit London open · Risk: risk move đồng thời USD-bid (flight to quality) thì AUD đi hai chiều —cần DXY filter · Data: ES, VIX, DXY, AUDUSD · Coupling: AUDJPY cùng tín hiệu mạnh hơn.

**S64 — Gold-ToT regime trade (Cross-asset/Correlation)** — Hypothesis: trong commodity
bull + real-rate giảm, gold kéo AUD theo (Úc xuất vàng); trong risk-off thuần thì ngược —phân regime trước · Signal: XAUUSD 20d-momentum >0 và US10y real yield 20d-change <0 → gold-channel dương cho AUD · Trade: long bias AUDUSD khi gate mở, stop ATR-W1 · Risk: hai kênh gold đánh nhau ở regime chuyển tiếp —corr sign flip là stop signal · Data: gold, TIPS real yield · Coupling: XAGUSD cùng dấu xác nhận industrial channel.

**S65 — DXY-inverse residual reversion (Cross-asset/Correlation)** — Hypothesis: phần
biến động AUDUSD không giải thích bởi -beta×DXY là idiosyncratic —hay revert về model · Signal: residual AUDUSD_return + beta×DXY_return 5 ngày > 1.5 sd · Trade: fade residual, stop residual 2 sd, horizon 3-5 ngày · Risk: idiosyncratic thật (RBA week, China surprise) —flat quanh events · Data: DXY + AUDUSD · Coupling: residual cùng hướng iron ore thì không fade (đó là ToT thật).

**S66 — AUDJPY risk-gate overlay (Cross-asset/Correlation)** — Hypothesis: chỉ long
AUDUSD khi risk-appetite (AUDJPY trend) xác nhận —giảm half of losing longs · Signal: AUDJPY trên EMA50-D1 → cho phép long; dưới → chỉ short/flat AUDUSD · Trade: dùng làm gate cho S1/S32/S41, không standalone · Risk: cồng kềnh trong chop; gate sai khi JPY event riêng (BoJ) · Data: AUDJPY + AUDUSD · Coupling: VIX cùng chiều AUDJPY-trend.

**S67 — China-equity divergence trade (Cross-asset/Correlation)** — Hypothesis: FXI/
HSCEI và AUD cùng proxy China —khi tách nhau, AUD catch-up theo equities (equity phản ứng stimulus nhanh hơn FX) · Signal: 5-day HSCEI return > +3% khi AUDUSD 5-day flat · Trade: long AUDUSD theo hướng equities, stop nếu HSCEI give-back >50% · Risk: equity rally do US-rate (không China) —lọc bằng Hang Seng vs SPX relative · Data: HSCEI/FXI, SPX, AUDUSD · Coupling: S63 như một.

**S68 — CRB/commodity-index beta trade (Cross-asset/Correlation)** — Hypothesis: broad
commodity index momentum là phiên bản ToT rộng, dẫn AUD 5-10 ngày · Signal: CRB/berkshire broad index 20d-momentum flip sign · Trade: position theo sign với 1 tuần lag entry, stop 1×ATR-W1 · Risk: index bị energy chi phối trong khi Úc exposure metals —dùng sub-index ex-energy nếu có · Data: commodity index daily · Coupling: S5 narrower nhưng nhanh hơn.

**S69 — USDCAD-inverse confirmation (Cross-asset/Correlation)** — Hypothesis: hai chân
commodity-FX phải cùng phản ứng USD —khi lệch là oil-vs-iron-ore divergence, trade theo metal side · Signal: AUDUSD break 20d-high nhưng USDCAD không break 20d-low (oil đang yếu) · Trade: vẫn theo AUD break nhưng size 50%, stop chặt hơn · Risk: divergence ấy chính là oil crash week —AUD bị kéo theo sau đó · Data: hai cặp + oil · Coupling: copper/iron ore đứng về phía nào.

**S70 — Cross-asset vol-spillover filter (Cross-asset/Correlation)** — Hypothesis: khi
vol của commodities và VIX cùng tăng, AUDUSD sắp có expansion —chỉ báo dẫn cho mọi chiến lược breakout · Signal: 5d-change của (iron ore realized vol + VIX)/2 > +30% · Trade: tắt MR, bật breakout (S21/S26/S29) trong 5 ngày sau signal · Risk: vol spillover hai phía (cả dump lẫn melt-up) —chỉ là timing tool không direction · Data: vol series · Coupling: dùng chung làm regime gate.

### Family H — Positioning / Flows

**S71 — COT leveraged-fund extreme reversal (Positioning/Flows)** — Hypothesis: khi
leveraged funds net-long AUD cực đoan, tiếp theo là squeeze —crowd trade đảo · Signal: CFTC AUD net (leveraged) > +1.5 sd 3y và giá flat/đảo chiều 2 tuần · Trade: counter-position, entry weekly sau COT release (Fri 20:30 UTC theo dữ liệu Tue), stop khi positioning tăng tiếp 0.5 sd, horizon 2-4 tuần · Risk: positioning extreme tồn tại MONTHS trong trend thật (2026 hawkish-RBA) —bắt buộc kết hợp trend-flat gate · Data: COT weekly · Coupling: risk-reversal cùng extreme tăng edge.

**S72 — Asset-manager alignment momentum (Positioning/Flows)** — Hypothesis: real money
(asset managers/PMs) đúng chiều thường hơn —follow không phải fade · Signal: AM net position 4-week change cùng dấu với 4-week price change · Trade: vào theo dấu khi AM z-score vượt ±1, stop 1×ATR-W1, horizon 1 tháng · Risk: AM position lag giá —vào muộn · Data: COT disaggregated · Coupling: S38 sovereign spread cùng dấu.

**S73 — Price-new-high/positioning-not divergence (Positioning/Flows)** — Hypothesis:
giá làm new 20d-high mà positioning không tăng = short-covering rally —yếu, sắp revert · Signal: price percentile(20d)>95 & COT net change 4w < +10 percentile points · Trade: fade sau khi momentum bar đầu phai (3-5 ngày), stop trên extreme · Risk: giai đoạn đầu trend mới positioning luôn "chưa kịp" —kết hợp ADX thấp để lọc · Data: COT + price · Coupling: open interest futures cùng rule (S77).

**S74 — Crowd-spec contrarian tại extremes (Positioning/Flows)** — Hypothesis: tổng spec
(incl. non-reportable proxy retail) cực đoan là timing hint ngược trong 1-2 tuần · Signal: tổng spec net z>±2 & RSI-D1>70/<30 cùng chiều · Trade: counter scalp 5-10 ngày, stop 1×ATR-D1 · Risk: cần dữ liệu phi COT (retail broker positioning) —(cần kiểm chứng) nguồn sẵn có · Data: COT + retail sentiment feed · Coupling: dùng kèm S19.

**S75 — RBA FX-turnover slow flow read (Positioning/Flows)** — Hypothesis: quarterly FX
turnover & OTC derivatives statistics của RBA nêu bật regime flow (hedging volume, cross-currency swap) —slow confirmation · Signal: turnover AUD/USD segment tăng >15% yoy cùng chiều dealer-initiated proxy · Trade: bias position theo hướng giá của quý turnover tăng, horizon quý tiếp theo · Risk: data lag 3 tháng, tần suất thấp —chỉ là overlay · Data: RBA BIS semi-annual + AU FX committee · Coupling: S72 cùng dấu.

**S76 — 25d risk-reversal skew extremes (Positioning/Flows)** — Hypothesis: RR skew là
positioning+hedge demand gọn nhất —extreme gánh revert hoặc breakout tùy sign · Signal: 1m 25d RR z-score(1y) > ±2 · Trade: RR call-skew cực đoan dương (crowd mua upside) + giá flat → fade; RR âm cực đoan khi giá đã rơi sâu → buy (S16 cousin) —phân theo trạng giá · Risk: skew stale sau events; needs options data feed · Data: RR quotes daily · Coupling: COT cùng cực đoan nhân conviction.

**S77 — Futures OI-price divergence (Positioning/Flows)** — Hypothesis: new trend leg
đi cùng OI tăng; giá đi mà OI rơi = short-cover —sắp hết hơi · Signal: 5d price change >1 sd với 5d OI change <-5% · Trade: không vào mới trend direction, hoặc fade nhẹ, stop OI flip tăng · Risk: OI report daily lag —dùng 6A futures OI realtime nếu có · Data: 6A OI + price · Coupling: volume profile S87.

**S78 — ETF flow momentum (FXA) (Positioning/Flows)** — Hypothesis: retail ETF flow vào
AUD (FXA AUM change) là proxy sentiment chậm —đi ngược khi cực đoan, theo khi tăng dần từ mức thấp · Signal: 4-week AUM change z-score · Trade: tầng thấp→theo, tầng cao (z>2)→ngược, horizon tuần · Risk: FXA nhỏ, creation/redemption noise (cần kiểm chứng) significance · Data: FXA AUM daily · Coupling: S74 cùng dùng.

**S79 — Equity-fund inflow beta proxy (Positioning/Flows)** — Hypothesis: global equity
fund inflow (EM/Asia) là risk-on fuel —AUD hưởng theo với lag vài ngày · Signal: weekly fund-flow proxy (EPFR-type hoặc futures-only substitute: CME equity OI+price composite) tăng · Trade: long bias AUDUSD tuần sau flow print nếu VIX<20 · Risk: proxy thay thế chính xác thấp nếu không có EPFR —đánh dấu (cần kiểm chứng) · Data: fund flows/futures composite · Coupling: S63/S66.

**S80 — Volume-absorption fade (Positioning/Flows)** — Hypothesis: bar volume lớn mà
range nhỏ tại local high/low = absorption (đối thủ lớn chặn) —giá revert · Signal: H1 bar volume >3× median & range <0.5× median tại swing point · Trade: fade chiều mà absorption chặn, stop ngoài absorption bar, target VWAP session · Risk: absorption là re-accumulation của trend (bidUser thật) —cần bar đóng để confirm · Data: tick volume H1 · Coupling: dùng với level rõ (S88).

### Family I — Pattern / Pairs / Stat-arb

**S81 — AUDNZD cointegration band với directional overlay (Pattern/Pairs/Stat-arb)** —
Hypothesis: AUDNZD neo về mean dài hạn; trade band quanh mean nhưng chơi trên AUDUSD (dùng NZDUSD làm hedge) khi còn muốn giữ USD-view · Signal: AUDNZD z-score(60d) > ±2 & half-life OU <20 ngày · Trade: long AUDUSD + short NZDUSD size 1:1 khi z>2 (đóng khi z=0.3), stop z>3 · Risk: RBA-RBNZ policy tách (2026!) làm band break —giới hạn hold bằng thời gian 2×half-life · Data: hai cặp · Coupling: S35 hai policy path hội tụ mới vào.

**S82 — Beta-neutral China exposure (AUDUSD vs AUDJPY) (Pattern/Pairs/Stat-arb)** —
Hypothesis: tách "China-beta" (chung hai cặp) khỏi "USD-vs-JPY": trade chênh · Signal: residual của regression AUDUSD~AUDJPY 60d >1.5 sd · Trade: long leg/short leg theo residual, stop 2 sd, horizon 1 tuần · Risk: JPY leg có event riêng của BoJ —flat quanh BoJ · Data: hai cặp · Coupling: S66 ngược hướng sử dụng (overlay thay hedge).

**S83 — EURAUD range model (Pattern/Pairs/Stat-arb)** — Hypothesis: EUR (anti-risk) vs
AUD (pro-risk) tạo slow oscillator —EURAUD range bền hơn trend · Signal: EURAUD 100d-range position >80% (đỉnh) khi risk-appetite đang tăng → short EURAUD (được phát trên AUDUSD leg) · Trade: cấu long AUDUSD/short EURUSD tương ứng, stop ngoài range-extreme 0.5%, target mid-range · Risk: ECB-ES divergence policy mạnh (rate shock) làm range vỡ · Data: EURAUD + policy news · Coupling: VIX gate —không trade khi VIX>28.

**S84 — Pairs z-score + half-life filter (Pattern/Pairs/Stat-arb)** — Hypothesis: mọi
cặp AUDUSD-asset phải qua OU half-life test trước khi stat-arb —filter này tăng kỳ vọng của cả family · Signal: estimate OU trên residual, chỉ vào khi half-life 5-20 ngày & stationarity pass (ADF p<0.05 rolling) · Trade: framework điều phối S81/S82/S62/S83 · Risk: parameter instability —rolling re-estimate tuần · Data: theo từng cặp · Coupling: đây là meta-gate.

**S85 — NZDUSD lead-lag 1-2 bar (Pattern/Pairs/Stat-arb)** — Hypothesis: intraday, NZD
phản ứng nhanh hơn trên news TQ/dairy-Á; AUD theo sau 1-2 bar H1 · Signal: NZDUSD H1 return spike >2 sd & AUDUSD chưa đi tương ứng · Trade: vào AUDUSD theo hướng spike trong 2 bar, stop sau khi NZD revert, target beta-residual=0 · Risk: spike NZD do dairy news riêng của NZ —lọc news loại chúng · Data: H1 hai cặp + news tag · Coupling: dùng trong khung Á session.

**S86 — Futures-spot lead (6A vs spot) (Pattern/Pairs/Stat-arb)** — Hypothesis: CME 6A
futures (có giờ nghỉ + open outcry lịch sử) thỉnh thoảng dẫn spot quanhreopen gaps · Signal: 6A reopen gap hoặc burst OI-vs-spot diverge H1 · Trade: trade spot theo futures direction khi diverge >threshold, thoát khi converge · Risk: hiệu ứng mỏng trong thời đại 24h —(cần kiểm chứng) trên data riêng · Data: 6A tick + spot · Coupling: S47.

**S87 — Volume-profile POC acceptance (Pattern/Pairs/Stat-arb)** — Hypothesis: trong
day, giá quay về POC (point of control) của profile 20 ngày; acceptance ngoài value area là break thật · Signal: giá ở value-area edge của 20d profile với volume ngày thấp → fade về POC; volume cao + hold ngoài → theo break · Trade: hai kịch bản như signal; stop 0.7×value-area width · Risk: profile kiến trúc đổi sau event —rebuild sau RBA/China print · Data: tick/M5 volume · Coupling: S88 levels.

**S88 — Round-number & option-barrier defense fade (Pattern/Pairs/Stat-arb)** —
Hypothesis: big figures (0.6500/0.7000) và barrier strikes có gamma defense —giá rung quanh rồi bật khi không có catalyst · Signal: price tiếp cận round number 00/50 tốc độ chậm (không event) + tick volume tăng mà progress chậm · Trade: fade từ trước số 8-12 pips, stop xuyên số 6 pips, target 20 pips · Risk: số vỡ đúng lúc catalyst —tuyệt đối không dùng ngày event · Data: M5 + levels + options expiry calendar nếu có · Coupling: S97 expiry pin.

**S89 — Prior-day H/L + pivot confluence intraday (Pattern/Pairs/Stat-arb)** —
Hypothesis: S/R từ prior day high/low + daily pivots tụ lại tạo zone phản ứng xác suất cao hơn từng level riêng lẻ · Signal: ≥2 level (PDH/PDL/pivot/round) trong 10 pips · Trade:Reaction trade tại zone: reversal candle M15 + volume, stop ngoài zone 5 pips, target zone kế tiếp · Risk: trend-day xuyên mọi zone —gate bằng S70 vol filter · Data: M15 + levels · Coupling: S87 POC.

**S90 — Kalman-filter dynamic beta vs DXY (Pattern/Pairs/Stat-arb)** — Hypothesis: beta
AUDUSD-DXY đổi regime liên tục —Kalman update realtime bắt residual tốt hơn OLS 60d · Signal: Kalman beta + residual band ±1.5 sd innovation · Trade: fade residual ngoài band, stop theo innovation spike, exit giữa · Risk: model overshoot khi structural break (Fed hike tuần) —reset filter sau events · Data: DXY+spot, filter code · Coupling: thay OLS trong S65.

### Family J — Regime-conditioned / Options-flavored

**S91 — VIX regime switch (Regime/Options)** — Hypothesis: VIX<18: AUDUSD mean-reverting
& carry-friendly; VIX>25: trending & risk-driven —một chiến lược hai chế độ · Signal: VIX 20d-median hai bên ngưỡng · Trade: chế độ thấp chạy S11/S32; chế độ cao chạy S2/S16 hướng theo risk; chuyển chế độ flat 2 ngày · Risk: vùng 18-25 lưỡng tính —giảm size một nửa · Data: VIX + spot · Coupling: AUDJPY vol làm cross-check.

**S92 — Vol term-structure gate (Regime/Options)** — Hypothesis: upward-sloping vol
term (calm) favore MR; inverted/humped (event fear) favore momentum & straddle · Signal: 1m vs 3m implied vol ratio AUDUSD (hoặc VIX1m/VIX3m proxy) · Trade: ratio<0.95 → MR set; >1.05 → breakout/straddle set · Risk: cần options data —nếu không có, VIX term proxy (cần kiểm chứng) · Data: IV term structure · Coupling: S22/S26 bật khi humped.

**S93 — Pre-Politburo straddle (Regime/Options)** — Hypothesis: cuối tháng hội Politburo
(Apr/Jul/Dec) là catalyst stimulus binary —long vol trước đó có edge · Signal: mua straddle 1 tuần trước kỳ họp, exit sau kết luận 2 ngày · Trade: delta-neutral vào, cắt gamma chạy sau headline · Risk: premium cao nếu thị trường cũng biết; hội không ra gì → decay · Data: options quotes + calendar TQ · Coupling: S45 bracket làm replacement nếu không có options.

**S94 — Risk-reversal momentum confirm (Regime/Options)** — Hypothesis: RR skew đổi
sign chậm hơn spot —dùng làm confirm cho swing entry · Signal: 3m RR 5d-change cùng dấu breakout S29 · Trade: chỉ vào weekly break khi RR đồng hướng, nếu không chờ · Risk: skew nhịp event khống · Data: RR daily · Coupling: S76 đối cực (fade extremes) —hai chiều của cùng một thông tin.

**S95 — Correlation-regime flip detector (Regime/Options)** — Hypothesis: khi corr
AUDUSD-XAU hoặc AUDUSD-SPX flip sign, regime driver đổi —mọi correlation-based strategy cần reset · Signal: 30d rolling corr đổi dấu & |corr|>0.25 hai tuần liền · Trade: không standalone —meta gate: reset S61-S69 weights, flat 1 tuần · Risk: flip nhiễu quanh zero —cần magnitude filter như trên · Data: các chuỗi asset · Coupling: dùng chung cả program.

**S96 — Vol-targeted Kelly-lite sizing (Regime/Options)** — Hypothesis: AUDUSD regime vol
2-3× giữa calm/crisis —fixed size chết một trong hai; vol targeting sống cả hai · Signal: position size = target_vol / realized_vol_20d, cap 3× · Trade: overlay sizing cho mọi chiến lược trend/carry ở trên, không directional view · Risk: vol backward looking —couple với S91 cho chuyển nhanh · Data: realized vol · Coupling: meta-overlay.

**S97 — Option-expiry pinning (Regime/Options)** — Hypothesis: NY 10:00 UTC cut-off các
expiry lớn (bilat + listed) làm giá gravitate về strike lớn nhất open interest trong 24h cuối · Signal: strike có OI lớn trong 40 pips của spot & expiry hôm nay · Trade: scalp về strike từ 10:00-14:00 UTC, stop 12 pips, target strike · Risk: pin chỉ xảy ra khi dealer gamma dương —cần gamma estimate (cần kiểm chứng) data · Data: expiry calendar + OI · Coupling: S88 round numbers.

**S98 — HMM expansion/contraction state gate (Regime/Options)** — Hypothesis: hai trạng
ngầm (expansion vs contraction) của return distribution quyết định breakout vs MR sống —để model tự học thay rule-based · Signal: 2-state Gaussian HMM trên daily returns + realized vol; state posterior >0.7 · Trade: expansion → S2/S26; contraction → S11/S12; chuyển state flat 1 ngày · Risk: HMM label-switching & overfit states —cần out-of-sample strict · Data: returns + vol · Coupling: so sánh với S91/S15 nếu trùng tín hiệu tăng conviction.

**S99 — ToT × rate-diff four-quadrant allocation (Regime/Options)** — Hypothesis: hai
driver chậm (ToT 3m-change, rate-diff 3m-change) chia mặt phẳng 4 góc —mỗi góc một allocation: cả hai dương = long trend mạnh; ToT dương + rate âm = long nhẹ hedged; v.v. · Signal: sign và magnitude hai driver chuẩn hóa · Trade: matrix size/hedge (long full, long-half-hedged-by-AUDJPY, flat, short...) · Risk: driver correlate nhau trong commodity-currency regime → góc xoay chậm · Data: RBA commodity index + rate diff · Coupling: đây là "master regime" cho cả family khác.

**S100 — Crisis-alpha tail switch (Regime/Options)** — Hypothesis: khi tail-risk bùng
(VIX>30 + gold>20d-high + AUDUSD<20d-low cùng lúc), AUD có negative skew —flat/reverse mọi long và chuyển sang cấu tail (long AUD vs short AUDJPY leg) · Signal: ba điều kiện trên thoả trong 2 ngày · Trade: thoát longs theo rule cứng; optional short AUDUSD scalp với stop siết, không average · Risk: whipsaw khi VIX mean-revert nhanh (2015-08, 2024-08) —size nhỏ, đây là capital-preservation module · Data: VIX, gold, spot · Coupling: là kill-switch của S31/S32/S63.

---

## 3. Tổng hợp cho symbol

### 3.1 Top-10 ideas (ưu tiên nghiên cứu & backtest trước)

| # | Idea | Vì sao chọn cho AUDUSD |
|---|---|---|
| 1 | **S61 Iron-ore lead-lag** | Edge cấu trúc riêng AUDUSD mà 10 cặp kia không có; driver verified còn sống 2026 (iron ore ~$90, cầu TQ yếu nhưng biến) |
| 2 | **S4 China credit impulse trend** | Driver regime 1-3 tháng, chính là "bản chất" China-proxy của pair; hợp layer với S61 |
| 3 | **S51 RBA surprise drift** | Book mỏng 04:30 UTC + repricing chậm → drift có cơ sở vi cấu trúc; 2026 RBA đang active (4.35%→?) tạo sample nhiều event |
| 4 | **S8/S35 2y-spread momentum** | Chế độ "cả hai CB hawkish" 2026 làm static carry chết —spread momentum là cách đúng để chơi differential hai chiều |
| 5 | **S91 VIX regime switch** | AUD là thân risk —meta-gate này cải thiện gần mọi family; rẻ data (chỉ VIX) |
| 6 | **S13 London-open spike fade** | Pattern liquidity-grab lặp lại, chi phí kiểm chứng thấp (chỉ M15), fit với cấu trúc session Á-London của pair |
| 7 | **S66 AUDJPY risk-gate** | Tách risk-leg khỏi USD-leg —giảm false long, dùng được cho nhiều chiến lược khác trong program |
| 8 | **S45/S22 China-data window bracket** | Session-native edge; window event fixed giờ —dễ backtest đúng (chú ý DST) |
| 9 | **S32 Carry + trend filter** | Framework tồn tại qua mọi regime; 2026 swap dương nhẹ khi RBA trên Fed —kiểm chứng sớm được |
| 10 | **S81 AUDNZD band (meta S84)** | Hai commodity-FX cùng bloc; lưu ý 2026 RBA-RBNZ tách —half-life filter bắt buộc, đây chính là test thiết kế |

### 3.2 Bẫy overfitting đặc thù khi backtest AUDUSD

1. **Timezone & DST hai bán cầu**: events Úc/TQ theo AEST/Beijing nhưng backtest theo UTC
   lệch 1h trong các tuần DST chuyển (Oct & Apr) —đánh sai bar event là bug thầm lặng kinh
   điển. Cố định event theo giờ local gốc.
2. **Epoch China**: chuỗi 2003-2013 (super-cycle) và 2013-2020 (China slowdown) và
   2021-2026 (property deflation + stimulus-talk tape) là ba chế độ khác nhau —optimize
   trên cả chuỗi sẽ fit trung bình không thuộc regime nào. Walk-forward theo năm.
3. **Iron ore data**: giá 62% Fe có nhiều nguồn (Platts/SteelIndex/Dalian/Singapore
   futures) lệch nhau và lịch sử sạch chỉ từ ~2013-2014 (SGX TIO) —survivorship/patching
   dễ tạo fake lead-lag. Chọn một nguồn duy nhất và document.
4. **RBA framework đổi**: 8 họp/năm (từ 2024-style schedule), guidance style đổi, monthly
   CPI indicator chỉ có từ 2017-2018 và weight đổi —event study cần metadata theo từng era.
5. **Carry accounting**: backtest AUDUSD multi-day không cộng swap point là sai sống còn
   (carry từng là driver chính); forward-vs-spot handling phải tường minh.
6. **Spread session**: spread Asian session và quanh RBA 04:30 UTC giãn 2-4× —cost model
   dùng spread fixed kiểu London-session sẽ fabrication profit cho scalping session Á.
7. **Correlation không hằng số**: mọi strategy dùng DXY/gold/SPX filter phải test rolling
   window, không optimize trên full-sample corr (nhân tố driver đổi sign — mục 1.5).
8. **Event overlapping**: RBA, FOMC, China data thường rơi cùng tuần —attribution lỗi nếu
   backtest không phân event-time vs calendar-time; tách file event-day.
9. **AUDNZD/RBNZ structural break 2024-2026**: RBNZ cutting trong khi RBA hike —bất kỳ
   cointegration ước lượng tới 2023 đều break ngoài sample; báo cáo phải nêu.
10. **China data revision & LPR era**: TSF/PMI revise, LPR chỉ tồn tại từ 2019-08 —cẩn
    thận với "historical" signal trước đó (dùng loan-growth proxy nếu cần).

### 3.3 MUST-WATCH weekly macro checklist (thứ tự trong tuần, giờ UTC)

- [ ] **Mon**: kiểm calendar tuần: RBA? FOMC? China PMI/TSF/LPR? AU CPI/labour? —đặt
      event windows & tắt các strategy xung đột (S39/S95).
- [ ] **Mon sáng Á**: Dalian/SGX iron ore mở —đọc gap cuối tuần (feed cho S61/S25).
- [ ] **Tue/Wed**: CFTC COT (data Tue, release Fri 20:30 nhưng chuẩn dùng ngay khi có) —
      update z-score positioning (S71-S73, S76 RR nếu có).
- [ ] **~mùng 7**: China trade + iron ore import volume (tháng trước) —xác nhận cầu thật.
- [ ] **10-15**: China TSF/new loans/M1-M2 —cập nhật credit impulse (S4/S55).
- [ ] **Mùng 20 01:30**: China LPR —regime shift hiếm nhưng lớn (S56).
- [ ] **Cuối tháng 01:00-01:45**: NBS & Caixin PMI (tháng sau mùng 1) —divergence là
      thông tin (S54).
- [ ] **00:30 UTC các ngày data Úc**: monthly CPI (≈4 tuần sau month-end), labour force
      (tuần 3), retail sales —so consensus, đánh dấu RBA-implied repricing.
- [ ] **RBA tuần (8/năm, kế tiếp 29/09/2026)**: consensus + OIS-implied probability;
      sau decision đọc statement diff, schedule presser; driff window 48-72h (S51).
- [ ] **US**: CPI (~13th, 12:30), NFP (Fri đầu, 12:30), FOMC (27-28/10 kế tiếp) —USD-leg,
      kiểm SEP dots & IORB path.
- [ ] **Risk & commodity**: VIX level/term, AUDJPY trend, gold vs real yield (regime
      gold-channel — S64), copper, DXY; iron ore port inventory (Mysteel, cuối tuần).
- [ ] **ToT slow**: RBA Commodity Index khi release (monthly) —update S99 quadrant.
- [ ] **Season guard**: mùa cyclone WA (Oct-Apr) —tin supply iron ore; cuối tháng/AU
      fiscal year-end flow (S43/S44).

Lịch đã biết còn lại của 2026 (đặt window trước, giờ UTC):

- **29/09 (mai)**: RBA decision 04:30 + presser —window S24/S51; theo verify thị trường
  nghiêng hike 25bp → 4.60% (cần kiểm chứng kết quả thực tế).
- **27-28/10**: FOMC —window S57; SEP mới là chất liệu cho S8/S35 cả quý.
- **RBA meetings còn lại 2026**: ~Nov và ~Dec (khung 6-tuần-lẻ; xác nhận exact dates
  trên rba.gov.au —cần kiểm chứng).
- **Politburo TQ đầu-Dec**: window stimulus S93/S45 —historically binary lớn nhất Q4.
- **US CPI các tháng còn lại**: ~ngày 13, 12:30 UTC; **NFP**: Friday đầu tháng 12:30.
- **Cuối năm tài chính không có nữa** (30/06 đã qua); chú ý month-end fixing Q4 + giảm
  thanh khoản tuần Giáng sinh/Năm mới (loại khỏi sample breakout session Á).

### 3.4 Quan hệ với các lane khác trong program (synergy)

- **NZDUSD lane**: chia sẻ factor commodity-bloc —hai lane nên dùng chung suy nghĩ
  S81/S85 nhưng KHÔNG copy strategy mà không đổi half-life filter (RBA-RBNZ tách 2026).
- **XAUUSD / XAGUSD lane**: AUD-gold correlation hai chế độ (mục 1.5) —kết quả từ lane
  vàng về regime real-rate dùng trực tiếp làm gate S64/S95 của lane này.
- **EURUSD / GBPUSD lane**: USD-common-factor block —COT và DXY-residual framework
  (S65/S90) tái sử dụng được, đổi beta mỗi pair.
- **USDJPY lane**: S66/S82 cần kết luận về risk-leg từ lane JPY; hai lane nên thống nhất
  definition "risk regime" (VIX ngưỡng + AUDJPY trend) để tránh contradicting signals.
- **Energy lanes (BRENT/WTI/NATGAS)**: chỉ cung ToT-nhẹ qua LNG/than; không ưu tiên ghép.
- **USDCAD lane**: gương mirror commodity-FX —so sánh backtest cùng chiến lược trend/
  breakout giữa hai lane là test robustness rẻ (nếu edge chỉ sống ở AUD thì nghi overfit
  vào driver China, không phải structure).

### 3.5 Backtest blueprint cho Top-10 (đề xuất thứ tự chạy)

- **Lớp 1 — data rẻ, kiểm chứng nhanh**: S13 (M15), S21 (M15+volume), S91 (VIX+D1) —chạy
  trước để có baseline "pair này có edge gì không với giá không".
- **Lớp 2 — cross-asset cơ bản**: S61/S5 (iron ore), S66 (AUDJPY), S8/S35 (yields 2y) —
  kiểm tra xem driver còn dẫn không trong epoch 2021-2026.
- **Lớp 3 — event & macro**: S51 (RBA surprise, cần consensus DB), S45 (China window),
  S4 (credit impulse, monthly) —event-time accounting, embargo quanh events.
- **Lớp 4 — pairs/stat-arb**: S81+S84 (AUDNZD với half-life filter, cảnh giác break
  policy 2024-2026).
- **Falsification gate cho mọi trial**: (a) cost ×2 làm sập Sharpe → ý tưởng chết;
  (b) chỉ sống trong <2/5 năm walk-forward → chết; (c) metrics bắt buộc: Sharpe, CVaR 5%,
  max DD, turnover, sensitivity chi phí, split theo regime VIX</>20 và ToT up/down;
  (d) mọi hyperparameter >3 thì phải có lý do kinh tế ghi trước khi chạy (anti-p-hack).

### 3.6 Ghi chú nguồn (verify 2026-09-28)

- Federal Reserve FOMC statement 16/09/2026 (federalreserve.gov), CNBC, Reuters, NYT —
  Fed hike 25bp → 3.75-4.00%, SEP ~4.00-4.25% end-2026/2027, FOMC kế 27-28/10.
- ABC/Guardian/Finder (via search) — RBA 4.35%, ba lần hike 2026, họp 29/09/2026,
  thị trường chờ khả năng 4.60%; Westpac forecast. (đường chính xác cần kiểm chứng)
- JPMorgan (Q1-2026 China GDP 5.0%), OECD (4.5% 2026; steel -6.9% 2025), World Bank
  (property -16.2% Jan-May 2026), Reuters (steel 06/2026), Bloomberg/Goldman (capacity
  cuts chậm), ING & Steel-on-the-Net (iron ore ~$90 forecast 2026), IMF 02/2026,
  Mining.com 08/2026, FXStreet 12/2025 & StoneX 06/2026 (AUDUSD narrative/pullback ~4%).
- Mọi "typical correlation range" và mọi ngưỡng số trong file: kinh nghiệm chưa đo —
  **(cần kiểm chứng bằng dữ liệu live)** trước khi vào bất kỳ model nào.

### Phụ lục — quy ước viết tắt dùng trong file

- ATR: Average True Range · ADX: Average Directional Index · BBW: Bollinger Band Width ·
  COT: CFTC Commitments of Traders · DST: daylight saving time · EMA/ SMA: exponential/
  simple moving average · HMM: Hidden Markov Model · IORB: interest on reserve balances
  (Fed) · LPR: Loan Prime Rate (TQ) · MR: mean-reversion · OIS: overnight index swap ·
  OU: Ornstein-Uhlenbeck · POC: point of control (volume profile) · RBA: Reserve Bank of
  Australia · RR: 25-delta risk reversal (options) · SD: standard deviation · SMP:
  Statement on Monetary Conduct (RBA) · ToT: terms of trade · TSF: total social financing
  (TQ) · TSMOM: time-series momentum · VWAP: volume-weighted average price · VIX: CBOE
  S&P500 implied vol index · WMR: WM/Refinitiv 4pm London fixing · 6A: CME AUD futures.
- Khung thời gian: M1/M5/M15/H1/H4/D1/W1. Giờ mặc định **UTC**; các mốc Úc/Trung Quốc
  ghi kèm local (AEST/Beijing) vì DST hai bán cầu lệch nhau —nguyên nhân bug #1 mục 3.2.

---

**Footer — phạm vi & trạng thái bằng chứng**: tài liệu này là brainstorm knowledge-only
của lane AUDUSD trong program FOREX-UNIFIED-STRATEGY-BRAINSTORM-V1. Không có backtest,
không có data pull, không có con số hiệu suất nào được tạo ra ở đây; mọi ngưỡng/tham số
là giả thuyết khởi điểm. Trạng thái mặc định của mọi strategy idea: **NOT_RUN** —chỉ
backtest theo blueprint mục 3.5 (trial accounting, walk-forward, cost sensitivity) mới
được coi là bằng chứng. Cập nhật verify WebSearch gần nhất: 2026-09-28.
