# USDCAD — Deep Dive & 100 Strategy Ideas

- Program: `FOREX-UNIFIED-STRATEGY-BRAINSTORM-V1` · Lane: USDCAD · Ngày: 2026-09-28
- Loại tài liệu: knowledge-only brainstorm (NO backtest, NO code). Mọi mức ngưỡng/tương quan trong file là **prior cấu trúc** để phase đo lường đối chiếu — không phải kết quả PASS/FAIL.
- Quy ước dấu: USDCAD lên = USD mạnh hơn CAD; "CAD mạnh" ⇔ USDCAD xuống. Mốc giờ mặc định ET (New York). "D" = daily bar, "H1/H4" = intraday.
- Cross-lane note: lane EURUSD đã verify Fed hike 16/09/2026; lane USDCAD này đã re-verify độc lập (mục 1.0) — khớp.

---

## 1. Bản chất instrument

### 1.0 Bối cảnh vĩ mô đã verify (snapshot Sep 2026)

Nguồn: finance-search (trusted_media/official_derived), cửa sổ 08/2026–09/2026. Dùng làm "current regime prior" cho toàn bộ 100 ý.

| Khối | Trạng thái đã verify | Hàm ý cho USDCAD |
|---|---|---|
| Fed | Hike 16/09/2026 +25bp → **3.75–4.00%**, lần đầu sau 07/2023, 12/0 vote; Chair **Kevin Warsh**; SEP dots **4.1%** cuối 2026 (hàm ý thêm 1 hike, consensus tháng 12/2026); 2027 giữ, 2028 mới giảm | USD-leg bullish; differential nới |
| BoC | **Giữ 2.25%** ngày 02/09/2026; statement nêu "broadening recovery" nhưng cảnh báo **upside inflation risk do oil pass-through** (Hormuz) + chi phí thuế quan; press dùng cụm từ "may need to hike" | CAD-leg: hold với hawkish-risk — meeting 10/2026 là event sống |
| Differential | Fed − BoC ≈ **+150…175bp** nghiêng USD và xu hướng nới | Positive carry cho long USDCAD; đối trọng là repatriation flow (dưới) |
| Oil | Chiến tranh US–Iran (>6 tháng); Strait of Hormuz gián đoạn; Mỹ đánh chìm 5 tanker Iran gần Kharg (08/09); **Brent đỉnh ~$108, WTI ~$104** (10–11/09), WTI lần đầu >$100 sau nhiều tháng; 22/09 rơi về Brent ~$98/WTI ~$90 khi Iran tín hiệu mở lại Hormuz 7 ngày + Saudi xuất lại từ Yanbu; 24/09 Brent ~$104 khi có tin hòa bình (NYT) | Oil-regime đỉnh cao volatility, headline-driven; whipsaw hai chiều trong 1 tuần |
| Trade war | Mỹ từ chối gia hạn USMCA tại review 6 năm (mùa hè 2026); Section 338 thuế 50% (~$20B hàng CA, hiệu lực 22/08); Canada trả đũa dollar-for-dollar từ 08/09; điều chỉnh phạm vi 15/09; **import bans alcohol/dairy 29/09**; đe dọa thuế 50% auto/steel từ 01/01/2027 | CAD-structural-drag vĩnh viễn hóa; giải thích vì sao CAD yếu dù oil >$100 |
| Flow | Canadian investors bán kỷ lục **C$31B** cổ phiếu Mỹ trong tháng 7/2026 + 6 tháng liên tục giảm UST (StatCan 17/09) | Repatriation bid cho CAD — lực cân với carry |
| USDCAD level | ~**1.40–1.41** (suy ra "1 CAD = 0.71 USD" trong bài 17/09/2026) — **(cần kiểm chứng)** bằng tick data thực | Vùng 1.40 big-figure — barrier/pinning candidate |

Điểm cần làm rõ ngay: tháng 9/2026 là ví dụ kinh điển của **"USDCAD regime tension"**: oil $100+ (CAD-bullish) bị triệt tiêu bởi (i) carry −150bp, (ii) thuế quan, (iii) risk-off hỗ trợ USD. Chiến lược đơn-factor (chỉ oil hoặc chỉ rates) chết trong môi trường này — mọi ý dưới đây đều được thiết kế multi-factor.

*Nguồn verify chính (đã tra cứu 2026-09-28 qua finance-search, hạng nguồn trusted_media/official_derived):*
- BoC hold 2.25% + cảnh báo oil pass-through: Xinhua English 03/09/2026; tổng kết tuần các central bank của 21st Century Business Herald 21/09/2026.
- Fed hike 16/09/2026 → 3.75–4.00%, Warsh, dots 4.1%: Xinhua/China Economic Net 17/09; phân tích SEP Securities Times 17–18/09; FRED Blog SEP 21/09.
- Oil: Reuters 22/09 (two-week low, Iran reopen 7 ngày); Bloomberg 08–09/09 (Kharg strike, ~$108); Xinhua 10/09 (WTI >$100); CNBC 11/09; Bloomberg 24/09 (Iran peace plan, Brent ~$104).
- Trade war: Xinhua 15/08, 22/08, 09/09 (Section 338, bans 29/09); Jiemian/ThePaper 24–25/08 (auto 50% 2027, Carney retaliation 08/09).
- Flows: Xinhua 18/09 (record C$31B divestment US equities tháng 7/2026).
- Chuỗi nguồn trên là media/official_derived, không phải primary filing — mọi con số mang tính "đã verify nhất có thể trong knowledge-only mode"; phase đo lường vẫn phải đối chiếu primary (boC.ca, federalreserve.gov, StatCan).

### 1.1 Microstructure & sessions

**Đặc tả instrument:**
- Spot USD/CAD: quote 5 chữ số, pip = 0.0001, pipette = 0.00001. Settlement T+2. Retail/CFD spread điển hình 0.6–1.5 pip giờ NY; nở 2–4 pip giờ Á. Size lô chuẩn 100k.
- Futures chuẩn: CME **CAD futures `6C`** (CAD 100,000/contract — kiểm chứng spec hiện hành vì CME từng đổi size), options trên 6C; liquidity đủ cho hedging cỡ tổ chức. Mini/micro có nhưng mỏng.
- Vai trò trong hệ thống: top-7 cặp FX toàn cầu (~4–5% turnover). CAD là 1 trong ~6 reserve currency có share nhỏ nhưng ổn định (COFER) — có "real money" flow nền (reserve managers, sovereign).
- Đặc thù 2-chân-same-timezone: hầu như toàn bộ thông tin giá trị phát sinh 8:30–14:00 ET — pair có "information clock" tập trung nhất nhóm major.

**Cấu trúc ngày điển hình (ET):**

| Session | Giờ (ET) | Đặc tính liquidity | Hành vi giá điển hình |
|---|---|---|---|
| Asia | 19:00–03:00 | Mỏng nhất; spread nở | Range hẹp, false-break, mean-revert; đôi khi oil-Asia-headline dẫn dắt |
| London | 03:00–08:00 | Trung bình; USD-common flows | Theo DXY; CAD-leg vẫn ngủ; London-overshoot hay bị NY mop |
| NY overlap | 08:00–12:00 | **Tốt nhất** (Toronto+NY cùng lúc) | Event window chính: 8:30 data hai nước, 9:45 BoC, 10:00 Ivey, 10:30 EIA |
| NY afternoon | 12:00–17:00 | Giảm dần sau 15:00 | 14:00 Fed days; Canadian fixing ~16:15 ET; flattening |
| NY late/Rollover | 17:00–20:00 | Rất mỏng (post-fixing) | Gaps quanh 17:00; swap/rollover cost cao |

- ADR (average daily range) điển hình 60–90 pip chu kỳ bình thường; regime war/tariff 2026 ước 100–170 pip ngày có headline **(cần kiểm chứng bằng data)**.
- **Fixings**: WM/Refinitiv 4pm London (16:00 UK) tác động qua USD-leg; Canadian institutional fixing ~16:15 ET tác động trực tiếp CAD-leg — hai fixing cách nhau ~4–5 giờ tạo 2 "gravity wells" cuối ngày.
- **Databook chất lượng**: CFTC COT (CAD futures, thứ Sáu 15:30 ET), StatCan mọi data CA, EIA dầu tuần, CME OI — USDCAD là cặp có dữ kiện positioning/flow công khai phong phú bậc nhất, lợi thế cho family H.

**Cost & execution realism (để phase backtest không tự lừa):**
- Chi phí điển hình: spread 0.7–1.2 pip + commission ~0.2–0.5 pip/side ở broker tốt; slippage event-window 1–5 pip; rollover/swap là income stream chính của carry ý (kiểm chứng swap point thực tế của broker vì khác nhau lớn).
- Với ADR 60–90 pip, cost round-trip ~2 pip ≈ 2.2–3.3% ADR — mọi ý intraday phải có edge trung bình > 4–5 pip/limit trade mới sống qua cost; các ý H4/D đỡ nhạy hơn.
- Event-window execution: stop-market trong 8:30 spike có thể slip qua stop (gap-through) — backtest phải mô phỏng fill tại giá vượt stop, không phải đúng stop.
- Futures vs spot: 6C có tick 0.00005 (nửa pip), rẻ execution cỡ lớn, nhưng calendar roll 4 lần/năm tạo session-gap nhỏ cần xử lý trong backtest (continuous adjustment).
- Session bias data: nhiều historical tick feed thiếu chiều sâu book phiên Á — không kết luận về "bid-ask imbalance phiên Á" từ data không đủ.

### 1.2 Điểm ĐẶC BIỆT riêng USDCAD (vs EURUSD / GBPUSD / USDJPY)

1. **Petro-FX (terms-of-trade channel)**: Canada top-5 nước xuất khẩu dầu thế giới (oil sands + conventional, chủ yếu heavy WCS). Giá dầu lên → thu ngoại tệ của ngành năng lượng → cầu CAD → CAD mạnh → USDCAD xuống. Chuỗi: WTI/Brent → WCS revenue → corporate hedging & conversion flow → CAD spot. Lưu ý "identity gần đúng chứ không luật": nó bị lấn át bởi USD-leg (carry) và risk-leg — bằng chứng sống: Sep 2026 oil >$100 nhưng USDCAD ~1.40+.
2. **Kép-US-data (double-US-foot)**: data Mỹ tác động CẢ HAI chân vì kinh tế Canada bán ~72% export sang Mỹ. NFP mạnh → USD lên nhưng đồng thời kéo theo tăng trưởng Canada → CAD cũng lên. Hệ quả đo được: **beta của USDCAD với US surprise thấp hơn hẳn EURUSD**; nhiều lần sign còn ngược. Công thức hóa: `effective_surprise = z_US − β_spill × z_CA(same-slot)`. Mọi news-strategy trên pair này phải qua lăng kính đó (xem S53).
3. **Hai nền kinh tế gắn chặt nhất thế giới**: chuỗi ô tô/steel tích hợp (~37% bilateral trade), điện Ontario bán sang Mỹ, pipeline và refining chéo biên giới. Mọi cú sốc thương mại là sốch tương đối lệch về CAD → USDCAD là **"trade-war thermometer"** của Bắc Mỹ. 2026 là năm test lớn nhất kể từ USMCA thay NAFTA: Mỹ đã từ chối gia hạn tự động, dùng Section 338 (Smoot-Hawley!) — rủi ro tail thật chứ không chỉ headline.
4. **WCS differential là niche driver không pair nào có**: USDCAD không chỉ phản ánh giá dầu chung mà còn **giá dầu riêng của Canada** (WCS tại Hardisty). WCS blowout (pipeline constraint, wildfire Alberta, refinery outage Gulf) làm CAD yếu dù WTI đi ngang. Sau TMX vận hành (05/2024) differential trung bình đã hẹp; giá trị Sep 2026 **(cần kiểm chứng)**.
5. **Asymmetric liquidity map + event calendar "một cửa"**: mọi scheduled event nằm trong 8:30–14:00 ET → backtest event-window sạch, ít problem timezone hơn EURUSD (London event) hay USDJPY (Tokyo event). Phía Á chỉ có oil-headline không có data CB.
6. **CAD có "identity kép" commodity-G10**: vừa là G10 (rates-driven) vừa là commodity (ToT-driven). Khi hai identity đồng thuận (oil lên + BoC hawkish) → CAD trend mạnh; khi xung đột (Sep 2026) → chop khó chịu — đây là nguồn regime-switch nội tại của pair.

**Định lượng double-US-foot (cho phase đo lường):** chạy event-study phân loại: (i) ngày chỉ có data Mỹ, (ii) ngày chỉ có data Canada, (iii) ngày có cả hai (thứ Sáu đầu tiên). So sánh |return 8:35–10:00 ET| của ba nhóm trên 10 năm — kỳ vọng prior: nhóm (ii) có |move| lớn nhất mỗi đơn vị surprise, nhóm (iii) có phân phối heavy-tail nhất (net hai hướng), nhóm (i) nhỏ nhất. Nếu đo ra ngược prior thì mọi ý family F phải viết lại.

### 1.3 Tin tức/sự kiện ảnh hưởng

**Scheduled** (giờ ET; "(cần kiểm chứng)" cho slot không chắc):

| Sự kiện | Giờ (ET) | Tần suất | Transmission channel |
|---|---|---|---|
| BoC policy rate + statement | **9:45**, presser 10:30 | 8/năm | Rate differential trực tiếp; CAD OIS curve; tone về oil pass-through |
| BoC MPR (Jan/Apr/Jul/Oct meeting) | 9:45 | 4/năm | Projection oil pass-through, output gap → đường lãi suất kỳ vọng |
| Fed FOMC + SEP | **14:00** | 8/năm | USD-leg qua DXY/yields; spill sang kỳ vọng BoC |
| Canadian CPI (StatCan) | 8:30 (~ngày 15–21) | tháng | BoC reaction function trực tiếp CAD-leg |
| Canadian LFS employment | 8:30, **thứ Sáu đầu tiên — trùng slot NFP Mỹ** | tháng | Net-surprise hai chân (1.2.2) → whipsaw rồi reprice |
| Ivey PMI | ~10:00, đầu tháng (cần kiểm chứng ngày) | tháng | Business activity; lead nhẹ monthly GDP |
| Canadian GDP/retail/wholesale | 8:30 | tháng | Growth differential |
| BoC Business Outlook Survey | ~(cần kiểm chứng) | quý | Capex/credit intentions — CAD "real economy" |
| US CPI/NFP/PCE/ISM/retail | 8:30/10:00 | tháng/tuần | USD-leg + CAD spillover (double-foot) |
| EIA crude inventories | 10:30 thứ Tư | tuần | Oil balance → petro channel; đồng thời proxy demand Mỹ |
| OPEC+ meeting/JMMC | không cố định | ~2–6/năm | Oil supply path → CAD ToT |

**Unscheduled (kèm transmission):**
- **Geopolitical oil shock** (chiến tranh US–Iran, tanker attacks, Hormuz): hit 3 layer cùng lúc — oil spot, oil term structure (backwardation nới), Fed/BoC expected path. CAD hưởng petro + hawkish-BoC pass-through nhưng mất risk-leg → net ambiguous intraday, clear trending vài ngày. Sep 2026: loạt $90→108→90→104 là dataset "war whipsaw" quý giá để calibration.
- **Tariff proclamations**: Trump Section 338/232 (50% thuế, import bans 29/09, đe 50% auto 01/01/2027); Canada retaliation dollar-for-dollar (08/09); Ontario (Doug Ford) đe cắt điện/khoáng sản, tỉnh bàn phụ phí dầu/kali. Channel: export/GDP Canada (ước −0.4% GDP, ~90k jobs nếu không deal) → CAD bán; đồng thời đẩy costs/inflation hai nước → làm phức tạp reaction function cả hai CB (BoC phải cân "thuế đẩy giá" với "thuế bóp tăng trưởng").
- **WCS/pipeline/wildfire**: outage TMX/Keystone, wildfire Alberta (mùa hè), refinery turnaround Gulf → differential blowout → CAD-drag không thấy ở WTI.
- **Political Canada**: PM **Mark Carney** — cựu Governor BoC & BoE, giao tiếp market-savvy, chiến lược "diversify khỏi Mỹ" (gấp đôi export non-US trong 10 năm, energy superpower). Bầu cử/tin chính trị liên quan Alberta.
- **M&A flow**: Canadian oil M&A boom (Alberta heavy crude, demand châu Á qua TMX — Bloomberg 09/09/2026) → khối hedge CAD theo deal.

*Sơ đồ gán nhãn sự kiện (event-labeling scheme) cho phase đo lường:* mỗi sự kiện ghi 5 trường — `type` (CB/data/geopolitic/trade/oil-ops), `timestamp ET gốc`, `expected` (consensus/OIS-implied), `actual/surprise z`, và `reversal-24h` (có/không tin đồn ngược trong 24h). Riêng nhóm trade-war: bắt buộc thêm `retaliation-window` (Canada phản ứng trong bao lâu). Không có 5 trường này thì không đưa vào dataset event — đây là cách chống look-ahead và chống nhầm rumor với fact.

### 1.4 Thông số ảnh hưởng (parameter set)

1. **BoC–Fed policy differential**: chuẩn hóa bằng 2Y OIS spread hoặc fx-swap-implied; hiện −150/−175bp nghiêng USD (BoC 2.25% vs Fed 3.75–4.00%). Driver tương đối mạnh nhất hiện tại. Đo slope (3M change) chứ không chỉ level.
2. **Oil price & term structure**: level Brent/WTI; độ sâu backwardation (`CL1−CL6`) — backwardation sâu = tightness cung = CAD-tailwind thật; contango = demand yếu. Slope đổi dấu là inflection (S98).
3. **WCS−WTI differential**: hẹp (single digit) = pipeline đầy/tốt = CAD-friendly; nở >$15–20 = chokepoint. Sep 2026 **(cần kiểm chứng)**; cấu trúc post-TMX hẹp hơn pre-2024.
4. **DXY & US yields**: USD-common-leg; US 2Y real yield là proxy Fed path. Lưu ý reaction function mới của Fed dưới Warsh: theo "medium-term moving average" của inflation, ghét single-data — beta của Fed-path với 1 CPI giảm (đánh giá lại 9/2026).
5. **Risk sentiment**: SPX/VIX/MOVE; CAD là commodity G10 không phải haven. Risk-off thuần → USDCAD up; risk-off + oil-supply-shock (2026) → USD và CAD cùng mạnh → USDCAD đi ngang/xuống (S97 vs S96).
6. **Flows/positioning**: COT CAD spec; StatCan portfolio flows (repatriation); OI 6C; dealer gamma quanh expiry; RR skew.
7. **Trade-war intensity index**: đếm/điểm hoá headline thuế quan mới + proximity các deadline cứng (29/09/2026, 01/01/2027) — tự xây (S58 phụ thuộc).

**Sketch công thức tham khảo (để phase đo lường thống nhất quy ước):**
- `carry_ann = (r_US − r_CA) × hướng` — dùng OIS 1M annualized, không dùng nominal policy rate (mất thông tin expectation).
- `z_surprise(x) = (actual − survey_median) / MAD(surprise history 3 năm)` — MAD thay std để kháng outlier CPI mùa war.
- `net_surprise_NFP = z_US(NFP) − β_spill × z_CA(LFS)`, β_spill ước lượng rolling 2 năm (khởi điểm 0.5–0.7).
- `oil_beta = Cov(r_USDCAD, r_WTI) / Var(r_WTI)` rolling 60D, Kalman upgrade theo S85.
- `z_residual = (USDCAD − fairvalue_model) / robust_std(residual history 1 năm)` — fair-value theo S18/S88.

### 1.5 Correlation map (USDCAD vs 11 symbols trong universe program)

**Bảng 1 — prior tương quan daily-return điển hình** (chu kỳ 2015–2024 trung bình trải vùng; KHÔNG phải đo tại checkout 2026-09-28 — phase đo lường phải re-measure; regime 2026 có thể lệch tạm):

| Symbol | Hướng | Khoảng điển hình | Cơ chế chính |
|---|---|---|---|
| EURUSD | âm mạnh | −0.60 ~ −0.75 | USD common leg; USDCAD ≈ DXY + petro residual |
| GBPUSD | âm | −0.45 ~ −0.65 | USD leg + risk beta chung |
| USDJPY | dương yếu→vừa | +0.15 ~ +0.45 | USD leg chung; bị triệt tiêu khi oil-shock (JPY nhập dầu, CAD xuất dầu — CADJPY mới là petro-pair sạch) |
| AUDUSD | âm | −0.35 ~ −0.60 | Hai commodity currency cùng phe vs USD; phân kỳ khi oil ≠ metals/China |
| NZDUSD | âm | −0.30 ~ −0.55 | Như AUD, beta yếu hơn |
| USDCHF | dương | +0.35 ~ +0.60 | Mirror EURUSD; CHF haven |
| XAUUSD | âm yếu→vừa | −0.15 ~ −0.45 | Gold up = USD yếu; war-regime cả gold lẫn CAD cùng mạnh → âm co lại |
| XAGUSD | âm yếu | −0.10 ~ −0.40 | Industrial/risk lai |
| BRENT | âm | −0.35 ~ −0.60 | Petro terms-of-trade |
| WTI | âm | −0.40 ~ −0.65 | Như Brent, thường âm hơn chút nhờ chuỗi WCS/NA trực tiếp |
| NATGAS | âm rất yếu | −0.05 ~ −0.25 | AECO tách Henry Hub; liên kết yếu |

**Bảng 2 — tương quan có điều kiện (điều mà bảng 1 giấu):**

| Regime | USDCAD–WTI | USDCAD–DXY | USDCAD–USDJPY | Ghi chú |
|---|---|---|---|---|
| Supply-shock dầu (war, 2026) | −0.60 ~ −0.80 | +0.1 ~ +0.3 (yếu đi) | ~0 hoặc âm | CAD hưởng ToT, JPY mất (nhập dầu) |
| Demand-boom toàn cầu | −0.40 ~ −0.60 | +0.4 ~ +0.6 | +0.3 ~ +0.5 | Cả USD-leg và ToT chạy |
| Recession/risk-off thuần | −0.10 ~ −0.30 | +0.6 ~ +0.8 | +0.4 ~ +0.6 | USD haven lấn át oil |
| Range/low-vol | −0.30 ~ −0.50 | +0.5 ~ +0.7 | +0.3 ~ +0.5 | Baseline |

**Bảng 3 — tương quan bên trong universe (cần cho correlation budget của S100):** các cặp nội-universe ổn định nhất theo prior cấu trúc: WTI–BRENT ~ +0.90 (cùng driver supply; tách rời khi có shock riêng WCS/Gulf); XAU–XAG ~ +0.80; AUD–NZD ~ +0.75 (đồng commodity-downunder); EURUSD–USDCHF ~ −0.90 (gần mirror); EURUSD–DXY ~ −0.95 (định nghĩa gần trùng); USDJPY–XAUUSD ~ +0.3 đổi dấu theo regime yield-vs-risk. Ý nghĩa thực hành: portfolio giữ 2 ý oil-heavy + 3 ý USD-heavy thì thực chất đang đặt 1 cược — S100 bắt buộc có correlation budget trên ma trận này.

**Phân rã (decomposition)**:
- Tương quan với EUR/GBP/CHF/JPY phần lớn là **USD-common-leg** — có thể triệt bằng hedge DXY futures (S61); phần còn lại là CAD idiosyncratic (oil + BoC).
- Tương quan với WTI/BRENT là **CAD-specific alpha block** — thứ USDCAD có mà EURUSD không; đây là lý do pair này tồn tại trong program như một "asset class riêng: USD × petro".
- **Historical episodes để calibration backtest** (nhớ kiểm chứng ngày khi có data): oil crash 2014–15 (USDCAD 1.05→1.46); WCS blowout 2018 (~$50 differential, pipeline constraint); COVID 3/2020 (USDCAD đỉnh ~1.46+); rate-cycle 2022 (Fed nhanh hơn BoC, USDCAD ~1.30); trade-war + war-regime 2025–26 (hiện tại).

*Cách dùng correlation map ở phase đo lường:* (1) re-measure Bảng 1 trên rolling 1 năm + 3 năm, vẽ corridor min–max; (2) kiểm tra mỗi khi Bảng 2 đổi regime — correlation conditional là dữ kiện, không phải nhiễu; (3) mọi cặp ý strategy có |corr| > 0.5 trong cùng regime phải chia sẻ risk budget (input trực tiếp cho S100); (4) nếu tương quan WTI rơi vào khoảng −0.2…+0.2 kéo dài > 1 quý thì coi như episode decoupling — audit lại toàn bộ ý oil-heavy đang sống.

### 1.6 Note trung thực — bối cảnh nào các họ strategy hay CHẾT trên USDCAD

- **News-trading data Mỹ thuần (USD-leg)**: chết vì double-US-foot — beta với US surprise thấp, whipsaw khi Canadian data đồng slot (LFS/NFP).
- **Mean-reversion intraday phiên Á**: chết vì mỏng + spread nở; stop-hunt quanh big-figure.
- **Trend-following thuần không oil-filter**: chết trong episode "oil-decoupling" — như 8–9/2026 oil >$100 nhưng USDCAD ~1.40+ vì tariff + carry; trend pair ngược hướng oil nhiều tuần.
- **Carry không hedge**: nếu BoC hike theo oil pass-through (đã cảnh báo), differential −150bp nới về −100bp nhanh → carry loss cộng dồn với spot move ngược; và chưa kể gap tariff.
- **Stat-arb USDCAD–WTI beta tĩnh**: chết vì correlation regime-switch (Bảng 2) — bắt buộc rolling/dynamic beta + regime gate.
- **Vol-selling quanh BoC/OPEC trong war-regime**: implied premium "đắt" có lý do — realized event-move 2026 rất lớn (S92 chỉ chạy khi classifier S96 = peace).
- **Breakout thứ Sáu đầu tiên (double-data)**: false-break rate cao vì hai surprise triệt tiêu — cần net-surprise filter.

---

## 2. 100 Strategy Ideas

Quy ước template: **S<n> — tên (family)** rồi 2 dòng field: `Hypothesis · Signal · Trade` / `Risk · Data · Coupling`. Ngưỡng là điểm khởi đầu để tune, KHÔNG phải kết quả tối ưu.

**Bản đồ 10 family (vì sao mỗi family có lý do tồn tại trên USDCAD):**

| Family | Cơ hội cốt lõi trên USDCAD | Kẻ thù chính |
|---|---|---|
| A Trend/Momentum | Petro + carry regime tạo trend dài rõ (2014-15, 2022) | Chop regime-tension như 9/2026 |
| B Mean-reversion | NY liquidity sâu, phiên Á mỏng tạo dislocation nho nhỏ | Structural break (tariff) |
| C Breakout/Vol | Event calendar "một cửa" 8:30–14:00 ET + oil-gap | False-break double-data |
| D Carry | Differential −150bp + dots nới — carry thật, có swap income | BoC reverse (oil pass-through) |
| E Session/Seasonality | Timezone kép concentrate flow; mùa năng lượng | War headline xuyên session |
| F Event/Data | Canadian data bị under-react; BoC/Fed lệch nhịp | Net-surprise triệt tiêu |
| G Cross-asset | Oil là trục phụ trợ trong suốt (leading & hedgeable) | Correlation regime-switch |
| H Positioning/Flows | COT/OI/StatCan dồi dào nhất nhóm major | Lag weekly + endogeneity |
| I Pattern/Stat-arb | USDCAD–WTI là cặp stat-arb kinh điển | Non-stationarity 2026 |
| J Regime/Options | Regime-switch nội tại (petro vs USD vs risk) + 6C options sâu | Meta-overfit, sparse war-sample |

Nguyên tắc chống-padding: mỗi ý dưới đây phải khác biệt về **cơ chế hoặc nguồn dữ liệu**, không chỉ khác threshold; các biến thể threshold của cùng một cơ chế được gộp vào một ý và ghi chú ở Coupling.

### Family A — Trend / Momentum (S1–S10)

*Ghi chú family:* USDCAD là pair của các trend kỷ lục (1.05→1.46 trong 2014–15; 2022 quanh 1.30) vì driver (oil, differential, thuế quan) là các quá trình chậm, thị trường absorption theo tuần. Kẻ thù là regime-tension khi 3 driver đánh nhau (9/2026). Mười ý dưới chia theo: driver-gated (S1, S4, S5), cấu trúc cổ điển (S2, S3, S6, S9), tương đối/đa tài sản (S7, S10), và lead-lag (S8).

**S1 — Oil-Gated Trend Following (Trend/Momentum)**
Hypothesis: trend USDCAD bền nhất khi ngược hướng trend dầu (petro tailwind đồng thuận). · Signal: WTI 50DMA vs 200DMA quyết định hướng cho phép (downtrend oil → chỉ long USDCAD; ngược lại chỉ short); entry Donchian-20D breakout cùng hướng. · Trade: pyramid 3 mốc, trailing stop 2×ATR(14).
Risk: episode oil-decoupling (tariff lấn át như 8–9/2026) — cần thêm differential gate S31. · Data: USDCAD D, WTI D. · Coupling: BoC–Fed diff cùng chiều → tăng size.

**S2 — Donchian 20/55 Classic (Trend/Momentum)**
Hypothesis: USDCAD có momentum chu kỳ từ flows thương mại + hedging tuần hoàn của ngành năng lượng. · Signal: close vượt Donchian-20 (entry) / Donchian-55 (stop-and-reverse). · Trade: always-in-market, risk 0.5%/trade, không filter gì thêm (baseline sạch để benchmark).
Risk: chop regime ADX<20 ăn sequence loss nhỏ. · Data: D bars. · Coupling: biến thể có Oil-Gate S1 để so pairwise.

**S3 — ADX-Filtered Trend Ride (Trend/Momentum)**
Hypothesis: chỉ trade khi trend "thật" (ADX>25) giúp bỏ phase chop, đặc biệt các tuần ít thông tin. · Signal: ADX(14)D > 25 và DI+>DI− (hoặc ngược). · Trade: entry pullback đầu về EMA20; stop dưới swing gần nhất; trail bằng Chandelier.
Risk: ADX lag → vào muộn, ra muộn ở V-top event. · Data: D. · Coupling: event-week (BoC/Fed) nới stop theo bội ATR.

**S4 — 200DMA Dislocation Momentum (Trend/Momentum)**
Hypothesis: khi USDCAD lệch 200DMA > 2×ATR-year thì driver cấu trúc (rate diff hoặc tariff) đang mạnh, continuation thắng revert. · Signal: |price − 200DMA| / ATR200 > 2.0 cùng dấu momentum 20D. · Trade: join theo hướng lệch, stop nửa đường về 200DMA.
Risk: policy-reversal (BoC hike surprise) đảo nhanh. · Data: D. · Coupling: dấu phải khớp oil-gate S1, nếu không thì giảm nửa size.

**S5 — Oil Term-Structure Trend (Trend/Momentum)**
Hypothesis: backwardation sâu (CL1−CL6 cao) = tightness cung thật → CAD mạnh bền; term structure dẫn spot. · Signal: slope 6M futures > percentile-80 của 3 năm → short USDCAD. · Trade: giữ khi slope giữ nguyên, thoát khi slope về median.
Risk: demand-collapse backwardation có sign ngược cho CAD (dầu rẻ vì recession). · Data: WTI curve 12 mốc. · Coupling: chỉ chạy khi supply-driven (gate S96).

**S6 — Weekly Dow Structure Break (Trend/Momentum)**
Hypothesis: cấu trúc HH/HL tuần phản ánh institutional hedger, bền hơn noise daily. · Signal: break swing-high tuần + close tuần ngoài middle Bollinger tuần. · Trade: entry đầu tuần sau, stop dưới swing-low tuần trước.
Risk: gap tariff/war headline cuối tuần không stop được. · Data: W bars. · Coupling: tránh tuần có BoC/Fed trừ khi break cùng hướng kỳ vọng CB.

**S7 — Cross-Sectional G10 Momentum (Trend/Momentum)**
Hypothesis: rank momentum USD vs G10; USDCAD chỉ nên ăn phần rank CAD tương đối (đã strip DXY). · Signal: residual-momentum 1M/3M của CAD xếp cuối/m đầu bảng. · Trade: long USDCAD size theo rank, basket-neutral với các pair USD khác.
Risk: USD-common-leg nhiễu rank nếu không strip. · Data: 7 pair G10 D + DXY. · Coupling: chuẩn hóa residual theo S61 trước khi rank.

**S8 — Lagged Oil-Impulse Echo (Trend/Momentum)**
Hypothesis: USDCAD phản ứng oil-move lớn với lag giờ→ngày (corporate hedging flow chậm), tạo momentum thừa kế. · Signal: WTI 1-day return > 2σ mà USDCAD chưa đi 0.5×beta×move. · Trade: entry mở phiên NY sau, hướng = nghịch với dầu, stop 1×ATR H4.
Risk: market đã price trong Asia session qua NDF/CFD. · Data: WTI D + USDCAD H1. · Coupling: chỉ khi move dầu là supply-news (S96), không phải demand-news.

**S9 — H4 MACD Ignition at Overlap (Trend/Momentum)**
Hypothesis: momentum ignition khởi phát 8:00–12:00 ET (liquid + event) có follow-through tốt nhất trong ngày. · Signal: MACD-hist H4 cắt 0 trong overlap window cùng hướng slope NY-open 30 phút. · Trade: target extension VWAP×2, stop dưới ignition bar.
Risk: ngày không event → noise chop. · Data: H4 + calendar. · Coupling: tăng size khi trùng EIA/OPEC window.

**S10 — Dual Momentum vs DXY (Trend/Momentum)**
Hypothesis: move "phi-DXY" (USDCAD đi ngược DXY) là CAD-alpha thật, chất lượng trend cao hơn move do USD-leg. · Signal: sign(USDCAD 20D) ≠ sign(DXY 20D). · Trade: theo hướng USDCAD, stop ATR-based.
Risk: signal hiếm, concentration thời gian. · Data: DXY + USDCAD D. · Coupling: xác nhận bằng WTI cùng dấu (attribution petro).

### Family B — Mean-reversion (S11–S20)

*Ghi chú family:* lợi thế MR của USDCAD nằm ở microstructure: NY depth sâu hũ các spike ngắn, phiên Á mỏng tạo extreme giả, và cặp có "fair-value anchor" tự nhiên (oil) để đo dislocation. Tất cả ý B đều yêu cầu trả lời: revert về ĐÂU — anchor phải được định nghĩa trước khi vào.

**S11 — RSI-2 Pullback with Trend (Mean-reversion)**
Hypothesis: pullback sâu ngắn hạn trong trend dài revert về EMA5/EMA20 nhờ liquidity NY hũ. · Signal: RSI(2)D < 10 trong uptrend (price > 200DMA); ngược cho downtrend. · Trade: buy tại open phiên hôm sau, thoát khi RSI2 > 60, stop 1.5×ATR.
Risk: trend-break thật vì event. · Data: D. · Coupling: không đứng ngược oil-gate S1.

**S12 — Asian Range Fade (Mean-reversion)**
Hypothesis: phiên Á mỏng tạo extreme giả; London+NY revert khi không có driver mới. · Signal: giá chạm biên ±1.5σ Asian range trước 8:00 ET và oil flat (|WTI overnight| < 0.5%). · Trade: fade về mid-range, stop ngoài biên + 3 pip.
Risk: Asia oil-headline thật (Hormuz news đêm) → bắt buộc skip. · Data: H1 + WTI continuous. · Coupling: skip nếu calendar có data 8:30.

**S13 — Oil-Residual Fair-Value Reversion (Mean-reversion)**
Hypothesis: phần USDCAD không giải thích bằng WTI (residual rolling regression 60D) là tạm thời, revert về 0. · Signal: residual z-score > ±2.0. · Trade: trade về fair-value, size nghịch với |z|, z>3 cắt.
Risk: structural break (tariff new-normal) làm residual không revert — đây chính là rủi ro lớn nhất của ý này trong 2026. · Data: D USDCAD + WTI. · Coupling: đồng thời check DXY-residual (S61) để biết residual nằm ở chân CAD hay USD.

**S14 — Overnight Gap Fade (Mean-reversion)**
Hypothesis: gap giữa NY close và London open do mỏng, không có info, hay bị fill. · Signal: gap > 0.8×ATR20(H1) và không có event đêm. · Trade: fade gap, target full-fill, stop qua gap-extreme.
Risk: gap có catalyst thật (OPEC/Geopolitics đêm). · Data: H1 24/5. · Coupling: oil-overnight filter như S12.

**S15 — Post-Data Exhaustion Fade (Mean-reversion)**
Hypothesis: sau spike 8:30, nếu surprise nhỏ (<0.5σ lịch sử surprise) thì extension đầu revert 40–60% trong 2 giờ khi liquidity bổ sung lại. · Signal: bar M15 sau data > 2×ATR nhưng surprise z < 0.5. · Trade: fade 50% move sau khi bar đóng, stop tại spike-high/low.
Risk: surprise lớn xếp chồng đẩy rate-odds (như CPI 9/2026 đẩy Fed hike odds ~90%). · Data: M15 + surprise dataset. · Coupling: skip thứ Sáu đầu tiên (double-data).

**S16 — Bollinger Squeeze Range Reversion (Mean-reversion)**
Hypothesis: bandwidth percentile < 20 + ADX < 15 → regime range, biên ±2σ revert. · Signal: chạm biên trong khi bandwidth thấp. · Trade: fade biên, target giữa range, stop 1×ATR.
Risk: breakout thật khi có CB event tuần đó — đóng vị thế trước event. · Data: H4/D. · Coupling: expiry pinning (S93) tăng xác suất range.

**S17 — 3-Week Exhaustion with Oil-Divergence (Mean-reversion)**
Hypothesis: 3 tuần liên tiếp cùng hướng + RSI tuần > 70 + WTI không xác nhận (divergence) → exhaustion. · Signal: đủ 3 điều kiện, divergence là bắt buộc. · Trade: vào tuần thứ 4, stop high/low tuần 3.
Risk: carry-regime kéo dài bất thường. · Data: W bars. · Coupling: differential ngược hướng → tăng edge.

**S18 — Fundamental Fair-Value Reversion (Mean-reversion)**
Hypothesis: USDCAD dài hạn neo về fair value = f(WTI, 2Y diff, DXY, commodity index); lệch xa 1 năm+ revert trong 1–3 tháng. · Signal: |actual − model| > 1.5×std 1Y. · Trade: accumulate theo thang lệch, horizon quý.
Risk: model thiếu biến mới (tariff permanent shift) — cần tariff-intensity regressor và break-check quý. · Data: input D + fit walk-forward. · Coupling: BoC/Fed meeting là catalyst re-anchoring.

**S19 — Small-Surprise OR15 Reversion (Mean-reversion)**
Hypothesis: opening range 15 phút sau CPI/Ivey với net-surprise nhỏ → revert về pre-data. · Signal: |net surprise| z < 0.5. · Trade: fade biên OR15, stop 1.2× chiều cao OR.
Risk: revision-driven follow-through. · Data: M15 + surprise. · Coupling: loại trừ thứ Sáu đầu tiên.

**S20 — Sympathy-Spike Fade (Mean-reversion)**
Hypothesis: khi EUR/GBP spike trên data USD, USDCAD theo "sympathy" quá mức (chưa reprice CAD-foot) rồi revert một nửa. · Signal: USDCAD move vượt beta_DXY×DXY-move + 0.7×ATR. · Trade: fade phần dư 30 phút sau, stop ATR/2.
Risk: CAD có news riêng chồng lên đúng lúc. · Data: H1 multi-pair. · Coupling: chỉ khi calendar CA trống.

### Family C — Breakout / Vol-expansion (S21–S30)

*Ghi chú family:* "một cửa thông tin" 8:30–14:00 ET + oil-gap qua đêm làm USDCAD là máy phát breakout có lịch trình. Khác biệt của family này so với A: nhìn vol-expansion TRƯỚC rồi mới hướng, chấp nhận ăn ít lần nhưng mỗi lần to.

**S21 — Asian Range Breakout London (Breakout/Vol)**
Hypothesis: range Á hẹp + break tại London có follow khi driver USD tồn tại. · Signal: break Asian high/low 03:00–06:00 ET + ATR H1 expand. · Trade: stop lại trong range, target 2R.
Risk: London fake-break (đặc biệt thứ Hai). · Data: H1. · Coupling: chỉ khi DXY đồng thời break cùng hướng.

**S22 — Pre-BoC Compression Break (Breakout/Vol)**
Hypothesis: vol nén trước BoC; decision tạo direction-day; entry sau decision sạch hơn straddle mù. · Signal: realized vol 3D trước BoC < percentile-60; bar M5 đầu post-decision close ngoài pre-event range. · Trade: theo hướng bar, stop tại biên opposite của pre-event range.
Risk: hold + hawkish statement → whipsaw hai pha 9:45→10:30 (chính kịch bản hiện tại của BoC!). · Data: M5 + BoC calendar. · Coupling: bias theo oil pass-through narrative.

**S23 — NFP OR15 Breakout (Breakout/Vol)**
Hypothesis: sau 8:30, break OR15 theo hướng net-surprise có follow 2–4 giờ. · Signal: net z > 1.0 (công thức S53) + break OR15. · Trade: entry retest, stop OR opposite.
Risk: double-foot triệt tiêu (net ≈ 0) → skip. · Data: M15 + surprise kép. · Coupling: oil-flat morning để loại confound.

**S24 — Squeeze Breakout H4 (Breakout/Vol)**
Hypothesis: BB-squeeze nhiều ngày nổ khi có catalyst (EIA/OPEC/tariff headline). · Signal: bandwidth H4 percentile < 15 + break biên Bollinger. · Trade: theo break, trailing 2×ATR.
Risk: nổ ngược trong war headline. · Data: H4 + news timestamp. · Coupling: hạn chế giữ qua cuối tuần khi war-risk cao.

**S25 — Multi-Week Range Retest Continuation (Breakout/Vol)**
Hypothesis: break range ≥ 15 ngày, retest đầu là entry continuation xác suất cao (institutional re-allocation). · Signal: retest biên cũ + rejection candle D. · Trade: entry D-close xác nhận, stop trong range cũ.
Risk: double-top trap. · Data: D. · Coupling: yêu cầu OI-confirm (S73) để tăng edge.

**S26 — Canadian Data Underreaction Breakout (Breakout/Vol)**
Hypothesis: thị trường under-react data Canada (ít được model) → drift sau surprise kéo dài hơn data Mỹ. · Signal: CA CPI/LFS surprise z > 1.5 → trade theo hướng CAD giữ 3 ngày. · Trade: entry close ngày data, stop 2×ATR.
Risk: US data ngược chiều override. · Data: D + CA surprise series. · Coupling: Fed blackout week thì edge sạch nhất.

**S27 — ATR-Normalized Day Expansion (Breakout/Vol)**
Hypothesis: ngày |move| > 1.8×ATR(14) khi đa-asset kể cùng câu chuyện (DXY + oil đồng thuận) → continuation hôm sau. · Signal: k > 1.8 + same-narrative check. · Trade: vào 15:00 ET nếu chưa đảo, stop ATR.
Risk: exhaustion cuối NY. · Data: D + intraday. · Coupling: war-regime 9/2026 rất hợp (S96 on).

**S28 — Oil-Gap Transmission Break (Breakout/Vol)**
Hypothesis: WTI open-gap > 2% (war overnight) → USDCAD break session-range theo hướng petro trong 60–90 phút đầu NY. · Signal: gap không fill ngay + break session range. · Trade: theo break, stop trong range.
Risk: gap fill nhanh (peace rumor whipsaw như 22–24/09/2026). · Data: WTI + USDCAD H1. · Coupling: chỉ regime supply-shock.

**S29 — Day-of-Week Conditional Breakout (Breakout/Vol)**
Hypothesis: break Tue–Thu chất lượng hơn Fri (flow thật vs squaring). · Signal: breakout D + day ∈ {2,3,4}. · Trade: như S2 chỉ thêm filter ngày.
Risk: bỏ lỡ trend mở đầu thứ Sáu lớn. · Data: D. · Coupling: gộp với S21 làm module chung.

**S30 — OPEC/EIA Event Range Break (Breakout/Vol)**
Hypothesis: ngày EIA/OPEC, break 10-day range theo hướng inventory surprise có follow. · Signal: EIA draw > 2σ expectation hoặc OPEC cut surprise + break 10D high/low. · Trade: theo break, stop 1×ATR.
Risk: "sell the news" khi giá đã chạy trước. · Data: EIA weekly + OPEC calendar. · Coupling: WCS phẳng → beta mạnh hơn.

### Family D — Carry / Rate-differential (S31–S40)

*Ghi chú family:* đây là family "gần nguyên lý kinh tế nhất" hiện tại (differential −150/−175bp là fact, không hypothesis) nhưng cũng là family có rủi ro regime-reversal cao nhất vì BoC đang ở trạng thái hold-with-hawkish-risk. Mọi ý D đều được viết kèm lối thoát khi differential nới về.

**S31 — Classic Differential Carry + Oil Hedge (Carry)**
Hypothesis: Fed − BoC > +100bp và nới rộng (hiện ~150–175bp, dots 4.1%) → long USDCAD thu swap + spot drift. · Signal: differential level > 100bp và slope 3M > 0. · Trade: long + short WTI futures theo beta để strip petro leg; disaster stop 3×ATR.
Risk: BoC hike surprise thu hẹp + spot gap ngược. · Data: OIS/swap curves + WTI. · Coupling: oil-hedge là bắt buộc, không tùy chọn.

**S32 — Carry-to-Vol Filter (Carry)**
Hypothesis: carry chỉ có edge khi annualized carry > 0.5×implied vol. · Signal: ratio ≥ 0.5 on; < 0.3 off. · Trade: toggle cho S31.
Risk: vol spike ngay sau khi on. · Data: 1M implied + swap points. · Coupling: VIX > 30 force-off (S97).

**S33 — Curve-Slope Differential Leader (Carry)**
Hypothesis: US−CA 2s10s slope lead policy differential 3–6 tháng (term structure prices BoC path trước). · Signal: slope-diff đổi dấu. · Trade: accumulate 4 tuần theo hướng mới.
Risk: term premium noise xuyên tả hai nước. · Data: 2 yield curves. · Coupling: MPR/SEP xác nhận mới tăng size.

**S34 — Forward-Differential Momentum (Carry)**
Hypothesis: Δ của 1Y forward rate differential (annualized) dẫn spot vì market reprices trước CB action. · Signal: Δforward-diff 4W > ngưỡng. · Trade: theo dấu Δ, horizon tuần.
Risk: đã priced (forward-spot đồng thời nhích). · Data: FX forwards. · Coupling: filter cho S31 thay vì standalone.

**S35 — Carry with Tail Hedge (Carry)**
Hypothesis: tail-risk của long USDCAD carry là CAD-rally (BoC hike/oil spike) → mua OTM USDCAD puts tài trợ bằng carry. · Signal: carry on + puts 25Δ rẻ (RR percentile < 30). · Trade: carry + 1M put 25Δ mỗi tháng.
Risk: premium ăn mòn khi vol cao kéo dài. · Data: options 6C. · Coupling: tháng có BoC meeting tăng protection.

**S36 — Reverse-Divergence Convergence (Carry)**
Hypothesis: nếu BoC hike (đã cảnh báo oil pass-through) trong khi Fed pause → differential nới về → short USDCAD convergence trade. · Signal: BoC hike + statement hawkish, Fed dots không tăng. · Trade: short post-decision, stop 2×ATR.
Risk: Fed hike tiếp (Dec 2026 consensus) phá narrative nhanh. · Data: CB calendars + SEP. · Coupling: Brent backwardation sâu xác nhận pass-through narrative.

**S37 — Carry Unwind Early-Warning (Carry)**
Hypothesis: carry collapse có tiền triệu: carry-to-vol nén + implied basis nở (bài học JPY-carry unwind 9/2026). · Signal: ratio giảm 2 tuần + 1M implied +40%. · Trade: de-risk toàn bộ S31-type trước drawdown.
Risk: false alarm whipsaw. · Data: vol surface + swap. · Coupling: global FX carry index (AUDJPY proxy) confirm.

**S38 — CA Yield-Curve Inversion Recession Signal (Carry)**
Hypothesis: CA 2s10s invert sâu → recession Canada → USDCAD up sau 3–6 tháng. · Signal: inversion < −50bp. · Trade: long USDCAD nửa size, horizon quý.
Risk: inversion do BoC hawkish (khác dynamic — lúc đó CAD mạnh). · Data: CA curve. · Coupling: Ivey/BOS confirm suy giảm mới vào.

**S39 — Petro-FX Carry Basket Relative (Carry)**
Hypothesis: chọn giữa petro-FX theo carry-adjusted oil beta — long USDCAD vs short USDNOK khi differential chênh đáng kể. · Signal: chênh carry chuẩn hóa > 1σ. · Trade: pairs giữ oil-beta neutral.
Risk: idiosyncratic từng nước (Norges Bank, Norway fund). · Data: các pair + oil. · Coupling: đo beta trước bằng S85.

**S40 — QT/Liquidity Differential Modifier (Carry)**
Hypothesis: chênh lệch balance sheet Fed vs BoC ảnh hưởng slow-carry qua term premium. · Signal: ΔCB balance 3M. · Trade: modifier ±20% size cho S31.
Risk: đo thô, noise. · Data: balance sheets. · Coupling: chỉ meta-filter, không standalone.

### Family E — Session / Time-of-day / Seasonality (S41–S50)

*Ghi chú family:* timezone kép (Toronto+NY) khiến cấu trúc trong ngày của USDCAD khác hẳn EUR/JPY — đây là nguồn edge session không transfer được từ lane khác; mùa vụ thì ăn theo chu kỳ năng lượng Bắc bán cầu. Cảnh báo: các hiệu ứng session nhỏ (vài pip) chỉ sống nếu cost model thực tế.

**S41 — NY Continuation of London Move (Session)**
Hypothesis: move London còn xăng khi NY mở nếu DXY-confirm. · Signal: London |z| > 1 và chưa revert > 30% lúc 8:00. · Trade: join 8:05, stop London-mid.
Risk: London-fade scenario (S12/S43). · Data: H1. · Coupling: skip nếu có data 8:30.

**S42 — Asian Extreme Fade (Session)**
Hypothesis: extreme tạo trước 03:00 ET do thin book bị mop up. · Signal: giá ngoài ±2σ 20-day Asian range lúc 02:00. · Trade: fade 02:00→08:00.
Risk: Asia news thật (OPEC giờ Á, Hormuz đêm). · Data: H1 + newsfeed. · Coupling: oil overnight flat filter.

**S43 — London-Overshoot Reversal at NY (Session)**
Hypothesis: London overshoot khi oil flat + không data → NY revert về daily VWAP. · Signal: 07:00 ET price > 2×ATR band quanh VWAP. · Trade: fade về VWAP.
Risk: trend-day thật (OR đã break). · Data: H1 + VWAP. · Coupling: chọn giữa S41/S43 bằng DXY-confirm test.

**S44 — Fixing-Flow Pattern (Session)**
Hypothesis: quanh 16:15 ET Canadian fixing có drift theo hướng flow ngày (portfolio rebalancing). · Signal: hướng 14:00–16:00 persist + oil neutral. · Trade: join 15:45, exit 16:30.
Risk: fixing weight mùa biến động; tồn tại của edge này cần đo **(cần kiểm chứng bằng M5 nhiều năm)**. · Data: M5. · Coupling: month-end tăng trọng lượng (S45).

**S45 — Month-End Rebalance Drift (Seasonality)**
Hypothesis: rebalancing cổ phiếu/trái phiếu CA–US cuối tháng tạo hedge-flow có hệ thống theo hướng return tháng. · Signal: |monthly equity diff return| lớn. · Trade: cuối ngày cuối tháng, horizon 2 ngày.
Risk: bất ổn qua thập kỷ, hai chiều. · Data: index returns + FX. · Coupling: StatCan flows (S74) xác nhận cơ chế.

**S46 — Post-Canadian-Data Friday Drift (Session)**
Hypothesis: sau LFS thứ Sáu đầu tiên, CAD-drift kéo dài cả ngày (reprice chậm). · Signal: surprise z > 1.2. · Trade: vào 10:30 ET, exit close.
Risk: US leg dominate buổi chiều. · Data: surprise + H1. · Coupling: dùng net-surprise vì trùng NFP.

**S47 — Winter CAD Strength Seasonality (Seasonality)**
Hypothesis: Nov–Feb heating-oil demand + energy revenue + year-end repatriation → CAD mạnh tương đối. · Signal: vào giữa tháng 11, thoát giữa tháng 2. · Trade: short USDCAD nửa size + oil-hedge ngược.
Risk: war-regime kéo oil cao quanh năm làm mùa gộp vào trend (2026 note). · Data: D nhiều năm. · Coupling: chỉ đúng logic khi cầu mùa đông là driver.

**S48 — August Liquidity Fade (Seasonality)**
Hypothesis: tháng 8 mỏng → breakout giả nhiều, mean-reversion thắng. · Signal: August-only MR module. · Trade: fade biên range 2σ.
Risk: tariff August surprise (như 8/2026) — module phải có news-kill switch. · Data: D seasonal. · Coupling: war/trade calendar check hằng tuần.

**S49 — Monday Gap Fade vs Wednesday Trend (Seasonality)**
Hypothesis: gap thứ Hai (weekend war/politics noise) hay fill; breakout giữa tuần hay thật. · Signal: Monday gap > 0.5×ATR → fade; Wednesday breakout → follow (S29). · Trade: hai rule riêng biệt.
Risk: Sunday-night event thật. · Data: H1/D. · Coupling: oil weekend-gap filter.

**S50 — Quarterly Expiry/Window-Dressing Cycle (Seasonality)**
Hypothesis: cuối quý có hedging cycle (6C expiry, portfolio) → vol + drift cuối tuần cuối quý. · Signal: tuần cuối quý + skew nghiêng. · Trade: risk-toggle (nới target, bó stop).
Risk: hiệu ứng yếu. · Data: expiry calendar. · Coupling: kết hợp S93/S94.

### Family F — Event / Data-driven (S51–S60)

*Ghi chú family:* hai cảm giác trái chiều phải giữ cùng lúc: data Mỹ bị double-foot triệt tiêu (kém hấp dẫn), nhưng data Canada + CB decision bị under-react (rất hấp dẫn). Family F vì vậy thiên về chân CAD và các cú sốc differential, tránh cạnh tranh USD-news với lane EURUSD.

**S51 — BoC Decision Surprise Trade (Event)**
Hypothesis: BoC surprise (đặc biệt hike khi market priced hold) tạo CAD move lớn + drift 2 ngày; hiện hawkish-risk vì cảnh báo oil pass-through. · Signal: decision ≠ OIS-implied consensus. · Trade: theo hướng surprise tại 9:46, thêm sau presser 10:30 nếu cùng chiều.
Risk: statement trái chiều action (hold + hawkish) → whipsaw hai pha. · Data: BoC calendar + OIS. · Coupling: BoC 10/2026 là event sống (cần kiểm chứng ngày chính xác).

**S52 — Same-Week Fed vs BoC Divergence (Event)**
Hypothesis: khi cả hai CB họp cùng tuần và phát biểu lệch hướng (hawkish Fed + hold BoC) → USDCAD rally tuần đó có edge. · Signal: net tone-diff (word-count NLP). · Trade: position tuần event, exit tuần sau.
Risk: cả hai cùng "market-friendly" → không direction. · Data: statements text. · Coupling: NLP giống S60.

**S53 — US NFP Net-of-CAD Filter (Event)**
Hypothesis: chỉ trade NFP khi Canadian LFS cùng slot không triệt tiêu — sửa trực tiếp lỗ hổng double-US-foot. · Signal: |z_US − 0.6×z_CA| > 1. · Trade: theo net-surprise hướng USD, stop ATR.
Risk: CA revision lớn làm z_CA sai. · Data: double surprise series. · Coupling: là fix bắt buộc cho mọi news-strategy US trên pair này.

**S54 — Canadian LFS Revision-Quality Trade (Event)**
Hypothesis: LFS surprise kèm revision cùng chiều đáng tin hơn; surprise ngược revision là noise. · Signal: sign(surprise) = sign(revision). · Trade: hold 3 ngày.
Risk: sample ít, mix full-time/part-time làm nhiễu. · Data: StatCan detail. · Coupling: thêm quality-of-jobs filter.

**S55 — CPI Differential Relative Trade (Event)**
Hypothesis: US CPI và CA CPI cách ~1 tuần; chênh surprise đổi kỳ vọng differential → move có hướng. · Signal: Δz = z_US − z_CA > 1. · Trade: vào sau CPI thứ hai, horizon 1 tuần.
Risk: oil đảo giữa hai release. · Data: 2 CPI series. · Coupling: Warsh theo moving-average → beta Fed-side với 1 CPI giảm (re-rate 9/2026).

**S56 — EIA Inventory CAD Catalyst (Event)**
Hypothesis: EIA draw lớn thứ Tư 10:30 ET → CAD strong 1–2 ngày (hedger flow cập nhật ToT chậm). · Signal: surprise draw > 2σ. · Trade: short USDCAD 10:35, stop 1×ATR.
Risk: draw do demand-collapse (bearish thật). · Data: EIA + expectations. · Coupling: chỉ khi interpretation supply-side (S96).

**S57 — OPEC+ Post-Announcement Drift (Event)**
Hypothesis: sau OPEC decision thật sự surprise, drift kéo dài nhiều ngày vì curve reprice chậm. · Signal: decision lệch consensus. · Trade: qua USDCAD theo hướng oil-nghịch, horizon tuần.
Risk: "buy rumor sell fact". · Data: OPEC calendar/outcomes. · Coupling: curve move xác nhận (S5).

**S58 — Tariff Headline Fade/Repeat (Event)**
Hypothesis: Section 338/232 announcement gây CAD-dump tức thời; nếu 48h không có material follow-up → revert một phần; nếu có retaliation-chain → continuation. · Signal: headline classifier + có/không retaliation trong 24h. · Trade: fade 24–48h nếu one-sided; theo hướng nếu chain.
Risk: escalation thật (deadline auto 50% autos 01/01/2027). · Data: news feed labeled. · Coupling: deadline cứng là dated-event cho options (S95).

**S59 — Monthly GDP Divergence (Event)**
Hypothesis: GDP Canada monthly vs US quarterly tạo information-asymmetry tuần chót tháng. · Signal: CA GDP z > 1 khi US nowcast flat. · Trade: theo hướng CAD.
Risk: sample ghép thô, endogenous với oil. · Data: StatCan + nowcast. · Coupling: Ivey lead confirm.

**S60 — BoC MPR Tone-Shift NLP (Event)**
Hypothesis: word-count hawkish/dovish của MPR đổi trước action 1–2 quý (statement 02/09/2026 đã "warned"). · Signal: tone-score Δ > ngưỡng so với MPR trước. · Trade: position theo tone, horizon tháng.
Risk: NLP đơn giản overfit ngôn ngữ; BoC đổi format qua các năm. · Data: MPR PDFs lịch sử. · Coupling: theo dõi riêng từ khóa "oil", "pass-through", "inflation risks".

### Family G — Cross-asset / Correlation (S61–S70)

*Ghi chú family:* oil là trục chính nhưng không phải duy nhất — DXY, SPX, gold, natgas, thậm chí Brent–WTI spread đều mang thông tin. Nguyên tắc: cross-asset chỉ có giá trị khi nó mang thông tin MỚI so với price action USDCAD (leading, filtering, hoặc hedging), không phải vẽ lại quá khứ.

**S61 — DXY-Hedged USDCAD (Cross-asset)**
Hypothesis: strip USD-common-leg để trade CAD factor sạch. · Signal: residual USDCAD vs DXY-beta rolling 60D. · Trade: spot + DXY futures hedge theo beta.
Risk: beta instability. · Data: D. · Coupling: là input chuẩn cho S7/S10/S13.

**S62 — USDCAD–WTI Pairs Trade (Cross-asset)**
Hypothesis: spread USDCAD − β×WTI (β rolling 60D) stationary; z > ±2 thì revert. · Signal: z-score của spread. · Trade: pairs hai chân dollar-neutral, target z → 0.5.
Risk: structural break tariff-regime → z>3 cắt. · Data: D. · Coupling: cùng logic S13 nhưng hedge thật hai chân.

**S63 — Pure-CAD Basket vs Oil (Cross-asset)**
Hypothesis: CAD-vs-basket (trung bình EURCAD/GBPCAD/AUDCAD) là "pure CAD index" — tương quan oil sạch hơn USDCAD. · Signal: z(pure-CAD) lệch z(oil) > 1.5. · Trade: express qua USDCAD + hedge EURUSD/GBPUSD.
Risk: EUR/GBP idiosyncratic. · Data: 4 pair D. · Coupling: research input cho mọi ý petro.

**S64 — Gold/Risk-Off Conditional (Cross-asset)**
Hypothesis: risk-off thuần → USDCAD up; war (gold+oil cùng lên) → CAD mạnh — phải phân nhánh bằng hướng oil. · Signal: sign(XAUUSD×SPX) kết hợp sign(WTI). · Trade: long/short theo nhánh.
Risk: nhánh hiếm sample nhỏ. · Data: D. · Coupling: classifier S96 cung cấp nhánh chính thức.

**S65 — NATGAS AECO Spill (Cross-asset)**
Hypothesis: Canada xuất gas; Henry Hub/AECO spike mùa đông → CAD support ngoài oil. · Signal: NATGAS 5D z > 2 vào mùa lạnh. · Trade: tilt short USDCAD +20% size.
Risk: AECO–Henry Hub tách rời (1.5). · Data: NATGAS + AECO riêng. · Coupling: cùng mùa với S47.

**S66 — Stock-Bond Correlation Regime Switch (Cross-asset)**
Hypothesis: corr(SPX, US10Y) đổi dấu → macro regime đổi → tính chất vol/trend của USDCAD đổi. · Signal: rolling 60D corr đổi dấu. · Trade: strategy-selector TF vs MR.
Risk: trung gian, lag. · Data: D. · Coupling: meta-gate dùng chung nhiều family.

**S67 — AUDCAD vs USDCAD Commodity Split (Cross-asset)**
Hypothesis: AUD = metals/China beta, CAD = oil/US beta; AUDCAD kể chuyện commodity-split; split cực đoan thì một trong hai revert. · Signal: |z(AUDCAD) − z(USDCAD-inverse)| > 2. · Trade: pairs.
Risk: cả hai cùng regime (commodity super-cycle). · Data: 2 pair D. · Coupling: oil/metals ratio sense-check.

**S68 — CADJPY Barbell Decomposition (Cross-asset)**
Hypothesis: CADJPY = petro + carry barbell; breakout CADJPY xác nhận USDCAD petro-move thật. · Signal: CADJPY break 20D-high cùng lúc USDCAD break 20D-low. · Trade: tăng size USDCAD trade.
Risk: BOJ hiking path (1.25% 9/2026, còn tiếp) làm JPY-leg mạnh không liên quan dầu. · Data: 2 pair D. · Coupling: BOJ calendar check.

**S69 — Brent–WTI Spread as NA Refinery Signal (Cross-asset)**
Hypothesis: WTI rẻ hơn Brent nhiều → Gulf refiners chạy mạnh → tăng cầu WCS → CAD-friendly nhẹ; spread hẹp ngược. · Signal: rolling 30D spread change. · Trade: tilt nhỏ hướng USDCAD.
Risk: proxy thô cho WCS — cần kiểm chứng beta WCS–spread trước khi tin. · Data: 2 crude D. · Coupling: WCS data thật thay thế khi có.

**S70 — Copper/Gold Ratio Growth Beta (Cross-asset)**
Hypothesis: copper/gold = global growth proxy; growth lên → CAD hưởng (cyclical G10) → USDCAD xuống ngoài oil. · Signal: ratio 20D z > 1.5. · Trade: short bias.
Risk: war bóp méo gold. · Data: XCU/XAU. · Coupling: trung gian cho S66.

### Family H — Positioning / Flows (S71–S80)

*Ghi chú family:* USDCAD có bộ dữ kiện flow công khai tốt nhất nhóm major (COT, OI, StatCan portfolio flow, COFER) — bất lợi trở lợi thế nghiên cứu. Rủi ro chung của family: endogeneity (flow là kết quả của move, không phải nguyên nhân) — mọi ý H phải trả lời được "flow này ai tạo ra và vì sao họ chậm".

**S71 — COT Spec Extreme Fade (Positioning)**
Hypothesis: CAD non-commercial net cực đoan (percentile > 90 / < 10) → contrarian, reverse risk cao. · Signal: z COT 52W ngoài ±1.8. · Trade: fade hướng crowded, horizon 2–4 tuần.
Risk: positioning cực đoan vẫn chạy tiếp trong carry-regime mạnh. · Data: CFTC COT weekly. · Coupling: skip khi carry on (S31).

**S72 — Commercial Hedger Pressure (Positioning)**
Hypothesis: oil producer hedging (bán CAD forward khi oil cao) tạo flow cấu trúc; đổi hướng hedging dẫn trend. · Signal: Δ commercial CAD positioning 4W > ngưỡng. · Trade: theo hướng commercials.
Risk: COT bucket không tách production-hedge rõ; weekly lag. · Data: COT. · Coupling: oil level regime xác nhận động cơ.

**S73 — OI-Confirmed Trend Continuation (Positioning)**
Hypothesis: breakout + rising OI 6C = new money confirm; breakout + falling OI = short-cover sắp hết. · Signal: ΔOI tuần quanh breakout. · Trade: size theo dấu ΔOI.
Risk: OI multi-cause. · Data: CME OI. · Coupling: điều kiện tăng cường cho S25.

**S74 — StatCan Portfolio Repatriation Monitor (Positioning)**
Hypothesis: divestment tài sản Mỹ của Canadian (record C$31B equities tháng 7/2026 + 6 tháng bán UST) → convert-flow CAD bid bền, chống carry. · Signal: monthly flow + xu hướng 3 tháng. · Trade: tilt short USDCAD khi flow lớn, horizon tháng.
Risk: endogeneity — flow là hậu quả của weak-USD đã qua. · Data: StatCan international transactions. · Coupling: đối trọng thực nghiệm của S31 — đo để biết phe nào thắng.

**S75 — Cross-Border M&A Hedging Wave (Positioning)**
Hypothesis: Canadian oil M&A boom (Alberta 9/2026) tạo khối hedge CAD quanh deal-announce → pressure nhất thời rồi fade. · Signal: aggregate deal > $5B/tháng. · Trade: fade pressure sau 2–4 tuần.
Risk: timing hedge không đều. · Data: M&A announcements. · Coupling: khớp narrative diversification của Carney.

**S76 — Retail Sentiment Contrarian (Positioning)**
Hypothesis: retail crowd usually against carry-trend trên USDCAD; extreme là contrarian. · Signal: broker long/short percentile > 85 / < 15. · Trade: fade nhỏ size.
Risk: retail data broker-specific, chất lượng thấp. · Data: broker sentiment. · Coupling: chỉ làm confirm.

**S77 — 25Δ Risk-Reversal Extreme (Positioning)**
Hypothesis: skew cực đoan (RR z ngoài ±2) đánh dấu panic/hubris → contrarian spot. · Signal: 1M/3M RR percentile. · Trade: fade ngược hướng skew.
Risk: skew đúng trong trend war kéo dài. · Data: options chain 6C. · Coupling: dùng chung giá options với S35.

**S78 — Global Carry-Unwind Contagion (Positioning)**
Hypothesis: khi JPY-carry unwind (episode BOJ 9/2026), CAD bị bán theo như funding-adjacent dù là yield currency — contagion window 1–2 tuần. · Signal: AUDJPY/CADJPY rơi nhanh + FX vol basket lên. · Trade: long USDCAD trong window, exit khi vol normalized.
Risk: CAD không còn funding property → window không xảy ra. · Data: crosses + vol. · Coupling: BOJ calendar.

**S79 — ETP Flow Proxy (Positioning)**
Hypothesis: FXC (CAD trust) flow là proxy retail/institutional CAD demand. · Signal: 4W flow z. · Trade: breadcrumb xác nhận.
Risk: ETP nhỏ so market. · Data: fund flows. · Coupling: phụ trợ cho S76.

**S80 — Reserve Diversification Slow Trend (Positioning)**
Hypothesis: CAD reserve share tăng dần (diversification khỏi USD thời trade-war) → structural bid nhiều năm. · Signal: COFER CAD share Δ nửa năm. · Trade: strategic tilt short USDCAD 5–10%.
Risk: quá chậm cho trading — chỉ allocation overlay. · Data: IMF COFER. · Coupling: khớp narrative Carney diversification.

### Family I — Pattern / Pairs / Stat-arb (S81–S90)

*Ghi chú family:* USDCAD–WTI là một trong những cặp stat-arb được nghiên cứu nhiều nhất FX — edge "dễ nghĩ" nên dễ bị arbitrage away ở dạng cổ điển; các ý dưới cố tìm góc lệch: scale-specific (S89), dynamic beta (S85), cross petro-FX (S83), microstructure (S82, S84). Tất cả đều phải có stationarity test làm gate sống còn.

**S81 — Rolling Cointegration USDCAD–WTI (Stat-arb)**
Hypothesis: hai chuỗi cointegrated trong window 1 năm weakening; spread OU tradable. · Signal: Engle-Granger p<0.05 + z > 2. · Trade: pairs, exit theo half-life.
Risk: cointegration break khi tariff-regime shift. · Data: D. · Coupling: ADF rolling làm gate.

**S82 — Triangular Dislocation Arbitrage (Stat-arb)**
Hypothesis: USDCAD vs EURUSD×EURCAD tạm lệch (lag microstructure) trong news giây–phút. · Signal: |implied − direct| > cost + buffer. · Trade: lock 3 chân.
Risk: cần execution latency thấp; cost thực lớn hơn lý thuyết. · Data: tick 3 pair. · Coupling: quanh event timestamps.

**S83 — USDCAD vs USDMXN Petro Pair (Stat-arb)**
Hypothesis: hai petro-FX; spread strip risk commodity chung để trade G10-vs-EM. · Signal: z spread > 2. · Trade: pairs.
Risk: Mexico idiosyncratic (Banxico, politics). · Data: 2 pair D. · Coupling: match oil-beta trước.

**S84 — Brent Lead-Lag Minute Scale (Stat-arb)**
Hypothesis: cùng headline war hit Brent futures trước OTC spot FX vài chục giây–phút. · Signal: Brent tick impulse > ngưỡng. · Trade: USDCAD nghịch hướng oil.
Risk: latency — cần infrastructure gần exchange; ngoài khả năng retail. · Data: tick đồng bộ. · Coupling: chỉ supply-news classifier on.

**S85 — Kalman Dynamic Oil Hedge Ratio (Stat-arb)**
Hypothesis: beta USDCAD–oil đổi liên tục; Kalman realtime tốt hơn OLS tĩnh cho mọi ý pairs. · Signal: state-space estimate. · Trade: dùng cho S62/S81.
Risk: filter lag trong jump. · Data: D/H1. · Coupling: infrastructure chung nhiều ý.

**S86 — OU Half-Life Strategy Selector (Stat-arb)**
Hypothesis: ước lượng half-life rolling chọn ý MR nào đang sống (HL < 10 ngày) hay chết. · Signal: HL estimate + CI. · Trade: allocation switch giữa các ý family B.
Risk: estimate noise. · Data: D. · Coupling: meta cho family B.

**S87 — Hurst Regime Switch (Stat-arb)**
Hypothesis: H > 0.55 ưa TF; H < 0.45 ưa MR; USDCAD đổi regime theo oil-cycle rõ. · Signal: rolling Hurst 100D. · Trade: strategy selector.
Risk: Hurst estimator variance cao. · Data: D. · Coupling: dual-gate với S86.

**S88 — Multi-Factor Fair-Value Residual Model (Stat-arb)**
Hypothesis: USDCAD = f(WTI, 2Y diff, DXY, SPX, tariff-index) fit walk-forward (ridge/kernel); residual z tradable. · Signal: |z| > 2 với model CI hẹp. · Trade: revert-to-model, rebalance tháng.
Risk: omitted-variable — tariff-index là biến bắt buộc của 2026. · Data: factor set D. · Coupling: mở rộng S88 từ S18 bằng ML discipline (walk-forward, không leakage).

**S89 — Wavelet Scale-Specific Oil Link (Stat-arb)**
Hypothesis: oil-link mạnh ở scale 1–2 tuần, yếu ở intraday — trade đúng scale. · Signal: wavelet coherence per scale. · Trade: band-filter cho S62.
Risk: edge artifacts, biên window. · Data: D. · Coupling: nâng chất lượng mọi ý petro.

**S90 — NATGAS/WTI Ratio Structural Break (Stat-arb)**
Hypothesis: gas/oil ratio break (winter spike) đổi driving của CAD từ oil sang gas ở mức nhất định. · Signal: CUSUM break test trên ratio. · Trade: re-weight petro factor trong S88.
Risk: share gas trong export Canada nhỏ. · Data: 2 futures D. · Coupling: mùa đông tăng trọng số (S47).

### Family J — Regime-conditioned / Options-flavored (S91–S100)

*Ghi chú family:* USDCAD có "ba linh hồn" (USD-leg, petro-leg, risk-leg) — family J không dự đoán giá mà dự đoán *linh hồn nào đang cầm lái*, rồi phân bổ các family khác cho đúng; nhánh options khai thác thị trường 6C sâu để định giá tail/event. Meta-overfit là rủi ro số một — mọi classifier phải rule-based trước, ML sau.

**S91 — Vol-Percentile Regime Allocation (Regime)**
Hypothesis: realized vol percentile quyết định TF vs MR allocation (low-vol chuẩn bị breakout; high-vol MR/scalp). · Signal: 20D RV percentile. · Trade: dynamic weight family A ↔ B.
Risk: transition loss khi regime đổi giữa chừng. · Data: D + intraday. · Coupling: meta-allocator.

**S92 — Event Vol-Premium Selling (Options)**
Hypothesis: event premium BoC thường overpriced khi hold priced > 85% — sell strangle 6C pre-event, gamma-manage. · Signal: implied event-move vs realized history. · Trade: short 1W strangle, cut trước presser.
Risk: hike surprise đúng như BoC đã cảnh báo — tail lớn; size nhỏ + vol stop tuyệt đối. · Data: options + BoC history. · Coupling: skip khi war-regime (S96 on → vol thật).

**S93 — Big-Figure Barrier Pinning (Options)**
Hypothesis: quanh 1.4000/1.4250 có option barriers/expiry strikes pinning giá trong ngày expiry (Sep 2026 spot đúng vùng 1.40). · Signal: approach round + expiry calendar + RR flatten. · Trade: range-trade quanh barrier, tránh breakout qua.
Risk: barrier bị overwhelm trong event thật. · Data: expiry info (bank feeds — cần kiểm chứng nguồn). · Coupling: cuối quý tần suất tăng (S50).

**S94 — OPEX Gamma-Day Mean-Reversion (Options)**
Hypothesis: ngày expiry lớn → dealer gamma cao → pin/intraday MR quanh strike OI dày. · Signal: expiry calendar + high-OI strike gần spot. · Trade: intraday fade quanh strike.
Risk: post-expiry trending. · Data: OI/strike. · Coupling: sibling của S93.

**S95 — Carry + War-Tail Call Overlay (Options)**
Hypothesis: cấu trúc 2026 (trade war + oil war) có tail CAD-dump khi escalation — carry long USDCAD mua OTM calls tài trợ một phần carry. · Signal: carry on + calls rẻ (percentile < 40). · Trade: carry + 3M 25Δ call mỗi quý.
Risk: premium drag nếu flat. · Data: options + carry. · Coupling: deadline auto-tariff 01/01/2027 là dated-event hoàn hảo cho calls.

**S96 — War/Peace Regime Classifier Gate (Regime)**
Hypothesis: supply-shock regime (Hormuz đóng) vs peace-talk regime (whipsaw 22–24/9/2026) đổi sign hầu hết oil-beta edge — NLP classifier headline là gate toàn cục. · Signal: classifier state + term-structure confirm. · Trade: gate on/off các ý S5, S8, S28, S56–S58.
Risk: misclassification (rumor vs fact). · Data: headlines + oil curve. · Coupling: dùng chung cả program.

**S97 — Crisis-Beta Liquidity Mode (Regime)**
Hypothesis: khi VIX > 30 + Treasury vol cao, USDCAD hành xử như USD-liquidity proxy (up) bất chấp oil — decouple tạm petro-link. · Signal: VIX + MOVE vượt ngưỡng. · Trade: tắt petro-strategies, bật USD-proxy long.
Risk: false positive. · Data: VIX/MOVE D. · Coupling: đối trọng của S96.

**S98 — Oil Curve Shape Regime Inflection (Regime)**
Hypothesis: chuyển contango ↔ backwardation là inflection trend USDCAD (term structure dẫn ToT). · Signal: sign-change của 6M slope giữ 20 ngày. · Trade: theo hướng mới, stop ngược slope-zero.
Risk: whipsaw quanh zero-slope. · Data: futures curve. · Coupling: nâng cấp discrete của S5.

**S99 — Monetary-Regime Transition Matrix (Regime)**
Hypothesis: (Fed state × BoC state) ∈ {hiking, hold, cutting} — mỗi transition có expected drift; cell hiện tại (hiking × hold-with-hawkish-risk) là cell hiếm, dễ overfit vì sample ít. · Signal: state classification từ OIS forwards. · Trade: drift position theo transition table.
Risk: sparse-sample overfit — phải có prior từ lý thuyết, không chỉ data. · Data: OIS 2 curves. · Coupling: khung quản trị mọi ý carry.

**S100 — Regime-Weighted Ensemble with Correlation Budget (Regime)**
Hypothesis: tổ hợp 10 family với weights theo regime (S91/S96/S97/S99) + constraint tổng oil-exposure và USD-exposure (correlation budget) cho output ổn định hơn từng ý riêng. · Signal: regime posteriors + exposure optimizer. · Trade: portfolio layer, risk parity cứng.
Risk: meta-overfit — weights phải out-of-sample và đơn giản. · Data: mọi input trên. · Coupling: bản nháp cuối cho phase portfolio của program.

---

## 3. Tổng hợp cho symbol

### 3.1 Top-10 ideas ưu tiên phase đo lường (kèm lý do)

*Tiêu chí chọn: (i) cơ chế kinh tế rõ và đo được ngay bằng data công khai; (ii) sống sót qua cảnh báo regime-2026 (3.2); (iii) có tính methodology — kết quả dùng lại cho các lane khác; (iv) cost-aware (edge kỳ vọng > friction).*

1. **S31 Classic Differential Carry + Oil Hedge** — differential ~150–175bp là driver mạnh nhất, dễ đo, có futures để hedge; bắt buộc có WTI hedge vì petro-FX.
2. **S13/S62 Oil-Residual / Pairs USDCAD–WTI** — khai thác đúng "identity" của pair; residual post-tariff 2026 hoặc là edge mới hoặc là bẫy — phải đo sớm để biết.
3. **S53 NFP Net-of-CAD Filter** — sửa đúng lỗ hổng double-US-foot; triển khai rẻ (chỉ cần surprise series hai data); giá trị metodologic cho cả program.
4. **S58 Tariff Headline Fade/Repeat** — regime 2026 sinh headline mật độ cao; có calendar cứng (15/09, 29/09/2026 đã qua; 01/01/2027 sắp tới) để thiết kế thử nghiệm sạch.
5. **S96 War/Peace Classifier Gate** — tháng 9/2026 chứng minh whipsaw $90→108→90→104; gate này quyết định sống/chết của mọi oil-beta ý — xây sớm, dùng chung program.
6. **S51 BoC Decision Surprise** — BoC đã cảnh báo hike; meeting 10/2026 có asymmetry đẹp vì market priced hold; rủi ro downside rõ (S92 là phía ngược).
7. **S36 Reverse-Divergence Convergence** — kịch bản BoC hike + Fed pause hiếm gặp, edge lớn nếu xảy ra; triển khai như conditional position với size nhỏ.
8. **S74 StatCan Repatriation Monitor** — flow CAD-bid cấu trúc (record C$31B/tháng) là đối trọng thực nghiệm của carry; đo để biết phe nào đang thắng — quyết định sign của nhiều ý khác.
9. **S5/S98 Oil Term-Structure Trend** — backwardation wartime vừa là signal vừa là filter; data curve dễ lấy, logic kinh tế vững, ít tham số.
10. **S71 COT Spec Extreme Fade** — rẻ, robust qua nhiều thập kỷ, đặc biệt hữu ích khi carry đẩy crowd một chiều (thực trạng 2026).

*Thứ tự triển khai đề xuất (measurement sequencing):*
1. Tuần 1: xây data nền — OHLC D + WTI + surprise series + COT; re-measure Bảng 1 correlation (kịch bản `NOT_RUN` cho đến khi xong).
2. Tuần 2: đo các "gate" trước — S96 classifier (rule-based), S91 vol-percentile, S99 regime matrix — vì chúng quyết định cách cắt data cho mọi ý còn lại.
3. Tuần 3-4: family D + B (carry & residual) vì có nền kinh tế mạnh nhất và data sạch nhất.
4. Sau đó: family F (event) — cần event-labeling scheme 1.3 hoàn chỉnh trước.
5. Cuối: family I/J (stat-arb & regime ensemble) — chỉ chạy khi đã có các khối đo lường ở trên làm input; tránh "ensemble trước, evidence sau".
6. Ràng buộc xuyên suốt: mọi trial phải ghi rõ regime-label (war/peace, carry on/off) tại thời điểm vào — không có label thì kết quả không có nghĩa trên pair này.
7. Benchmark bắt buộc: mọi ý phải thắng được S2 (Donchian thô) và S31 (carry + hedge) sau cost — nếu không thì không có lý do tồn tại ngoài độ phức tạp.

### 3.2 Bẫy overfitting đặc thù khi backtest USDCAD

- **Regime dependency 2026**: 8–12 tháng gần nhất chứa 3 shock chồng nhau (chiến tranh dầu, trade war, Fed restart-hike) — in-sample có structural break; walk-forward bắt buộc, không dùng expanding-window mù; tách pre/post-USMCA-review.
- **Oil-correlation non-stationarity**: calibrate beta/cointegration thời bình rồi test war-regime (hoặc ngược lại) cho kết quả rác — mọi ý petro phải có regime gate (S96) ngay từ khâu thiết kế backtest, không phải sau.
- **Double-US-foot confound**: news-strategy Mỹ trên USDCAD dễ ra beta giả với DXY — luôn chạy control DXY-hedged (S61) và EURUSD đối chứng.
- **Tariff event clustering**: các headline 7–9/2026 dày và tương quan nhau (escalation chain) — tách từng headline làm sample độc lập sẽ thổi phồng significance; phải cluster-robust standard errors.
- **Session/liquidity survivorship**: tick data Asia session xưa kém, spread lịch sử thiếu → MR intraday đẹp trên mid-price chết trên executable price; mô hình cost bằng spread thực tế biên + slippage event.
- **Parameter proximity round numbers**: 1.40 big-figure magnet (S93) khiến nhiều breakout backtest "gần thắng" — fill assumption nghiêm ngặt, không cho stop "trúng đúng" vì 1 pip.
- **BoC/Fed calendar drift**: giờ họp, cấu trúc presser, tần suất SEP đổi qua các năm — đồng bộ historical calendar chính xác trước khi định nghĩa event-window.
- **CAD data revision**: LFS/CPI revision lớn — dùng real-time vintage nếu có; nếu không phải ghi rõ look-ahead bias trong limitation.
- **War-regime sample nhỏ**: classifier S96/S97 học từ vài episode — danger zone của ML overfit; ưu tiên rule-based + human-label trước.
- **Survivorship of "petro-identity"**: toàn bộ período trước 2014 oil còn >$100 và shale chưa bùng nổ có cấu trúc ToT khác căn bản — chọn cửa sổ backtest cẩn thận, không lấy cửa sổ "10 năm tuỳ tiện" mà không nói chuyện cấu trúc năng lượng Bắc Mỹ đã đổi.
- **Look-ahead trong news-labeling**: gán nhãn "tariff headline" bằng nguồn phát sau sự kiện (bài tổng kết) sẽ leak — dùng timestamp gốc của proclamation/speech, và ghi timezone rõ ràng (ET) vì USDCAD nhạy giờ Mỹ.

### 3.3 MUST-WATCH weekly macro checklist (USDCAD)

1. **CB calendars**: BoC kế tiếp (October 2026 — ngày cần kiểm chứng, kèm MPR); Fed December 2026 (consensus thêm 25bp theo dots 4.1%); BOJ path (ảnh hưởng S68/S78).
2. **Differential & forwards**: 2Y OIS spread US−CA, 1Y forward diff, slope 3M — cập nhật mỗi tuần, đổi dấu là event.
3. **Oil**: Brent/WTI level; Brent 6M backwardation depth; EIA Wednesday 10:30 ET surprise; tanker/Hormuz shipping headlines; peace-talk progress (NYT-type reports).
4. **WCS−WTI differential** (nguồn cần kiểm chứng) + TMX apportionment + Alberta production/wildfire season.
5. **Trade-war tracker**: proclamations Section 338/232 mới; hiệu lực import bans 29/09; deadline auto 50% autos 01/01/2027; Canada retaliation list mở rộng; Ontario electricity/critical-minerals threats.
6. **Canadian data**: CPI (~15–21), LFS (thứ Sáu đầu tiên, trùng NFP — dùng net-surprise), Ivey PMI (đầu tháng), monthly GDP (cuối tháng), BoC BOS (quý).
7. **US data**: CPI/PCE (nhớ Warsh theo moving-average — một CPI không xoay Fed, hai CPI cùng hướng thì có), NFP, ISM.
8. **Flows/positioning**: COT CAD spec (thứ Sáu 15:30 ET); StatCan portfolio flows (tháng, ~45 ngày lag); M&A deal-flow Canada; CME OI 6C.
9. **Cross-asset**: DXY, US10Y, VIX/MOVE, CADJPY, AUDCAD, XAUUSD (war bid), CAD vs NOK/MXN (petro-FX relative).
10. **Options surface**: 1M/3M implied + 25Δ RR của 6C trước event lớn; expiry/OPEX calendar cho S93–S94; RR percentile cho S35/S77.

### 3.4 Nguồn dữ liệu cần cho phase đo lường (bảng kê)

| Nhóm data | Nguồn đề nghị | Dùng cho |
|---|---|---|
| Spot/Futures OHLC | broker feed, CME 6C continuous | mọi ý price-based |
| WTI/Brent term structure | futures curve hàng ngày | S5, S57, S98 |
| WCS Hardisty | vendor dầu (cần kiểm chứng nguồn công khai) | S69, fair-value models |
| OIS/forwards 2 nước | rate curves nhà cung cấp | family D, S99 |
| Surprise series US/CA | calendar + consensus (multiple vendors) | family F, S53 |
| CFTC COT + CME OI | công khai | family H |
| StatCan portfolio flows | công khai (tháng, lag) | S74, S45 |
| Options 6C (IV, RR, OI/strike) | vendor options | family J |
| News/headline timestamps | wire gốc có timestamp ET | S58, S96, event labels |

---

*Tài liệu brainstorm — không phải kết quả nghiên cứu. Mọi ngưỡng/correlation là prior phải re-measure tại checkout trước khi có bất kỳ tuyên bố hiệu quả nào (mission invariant: missing evidence = NOT_RUN, không bao giờ infer PASS).*
