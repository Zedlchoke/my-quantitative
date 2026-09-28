# EURUSD — Deep Dive & 100 Strategy Ideas

Program: FOREX-UNIFIED-STRATEGY-BRAINSTORM-V1 · Lane: EURUSD · Ngày: 2026-09-28
Loại tài liệu: knowledge-only brainstorm. KHÔNG backtest, KHÔNG số liệu đo lại — mọi correlation/thông số là khoảng kinh nghiệm để re-measure, mọi item time-sensitive đã verify qua WebSearch 2026-09-28 hoặc đánh dấu **(cần kiểm chứng)**.

Bối cảnh policy đã verify (2026-09-28):
- **Fed**: FOMC 16-09-2026 hike 25bp (12-0) lên band **3.75%–4.00%**, lần hike đầu sau 2023; dot plot ngụ ý thêm 1 hike, end-2026 **4.00%–4.25%**; core PCE projection 3.4% (2026), unemployment 4.1% (Q4-2026). Source: federalreserve.gov, JPM AM, Lord Abbett. Danh tính Fed Chair hiện tại (Warsh?) **(cần kiểm chứng)**.
- **ECB**: họp 10-09-2026 hike 25bp — **deposit facility 2.50%**, MRO 2.65%, MLF 2.90% (hiệu lực 16-09-2026). Trước đó ECB đã cut 8 lần liên tiếp từ đỉnh 4.00% về 2.00%, rồi hike 06-2026 lên 2.25% và 09-2026 lên 2.50%. Lý do chính: oil surge từ xung đột Trung Đông (Iran). Market price >3 hike nữa trong ~1 năm; ING cho rằng 2.50% đã ở upper bound của mức "appropriate". Họp kế tiếp **29-10-2026**.
- **Tỷ giá**: ~1.1386 (28-09-2026), +2.94% y/y; rời vùng ~1.16 đầu tháng 9 sau Fed hawkish. ECB reference rate 1.1403 (25-09-2026).
- **Short-rate differential (thước đo operative)**: Fed mid 3.875% − ECB depo 2.50% = **~137.5bp nghiêng USD**, nhưng hướng thu hẹp nếu ECB hike nhanh hơn (3+ vs 1).
- **Regime đặc thù hiện tại**: cả hai CB cùng hawkish-turn sau energy shock; xung đột Trung Đông kéo dài; EUR chịu double-hit (terms-of-trade + USD bid) nhưng cũng được hỗ trợ từ kỳ vọng catch-up hiking của ECB. Đây chính là " BOTH-HIKING + ENERGY-SHOCK quadrant" — tham chiếu ở S99/S100.

---

## 1. Bản chất instrument

### 1.1 Microstructure & sessions

**Vị thế trong hệ sinh thái FX**
- Cặp thanh khoản cao nhất thế giới: BIS Triennial 2022 — EURUSD ~22.7% global turnover (đếm single-side; daily turnover mọi instrument cỡ $700–800bn/day cho leg EURUSD). Bản Triennial 2025 đã công bố **(cần kiểm chứng số cập nhật)** nhưng ranking không đổi.
- Hệ quả: spread chặt nhất toàn thị trường — ECN/prime: ~0.0–0.3 pip + commission (~$3–7/lot/side); retail spread all-in thường 0.6–1.2 pip; depth top-of-book tốt nhất giờ London/NY.
- Giá 5 số thập phân (pipette/fractional pip = 0.5 pip trên quote máy 5); pip chuẩn 0.0001; point value $10/pip/standard lot (100k EUR). Big figure hiện tại 1.13–1.14.
- **6E futures (CME)**: contract 125,000 EUR; tick 0.00005 = $6.25; full pip $12.50; roll quý H/M/U/Z (~1 tuần trước Wednesday tuần 3 của expiry month); calendar spread ≈ rate differential (fair value theo CIP). 6E là nguồn OI/COT sạch nhất cho positioning (CFTC Commitments of Traders, dữ liệu Tuesday — release Friday 15:30 ET).

**Session & volatility profile (giờ GMT, lưu ý DST lệch 2–3 tuần giữa US/EU vào Mar & Oct–Nov)**
- 24/5: mở Sunday ~21:00–22:00 GMT, đóng Friday ~21:00–22:00 GMT.
- Tokyo 00:00–08:00: mỏng, range hẹp (thường 15–30 pip), mean-reverting; gap risk nếu tin geopolitics cuối tuần.
- London 07:00–08:00 open: vol spike đầu giờ — thanh khoản Frankfurt + London; đây là giờ có informational content cao nhất về hướng ngày.
- **Overlap London/NY 12:00/13:00–16:00**: thanh khoản + vol cao nhất ngày; moves có follow-through tốt nhất; phần lớn daily range hình thành ở đây.
- NY afternoon 17:00–20:00: "dead zone", drift theo flow dư; roll window 21:00 GMT spread nở.
- Rollover/swap: 21:00 GMT (5pm NY), **Wednesday 3x**. Hiện tại: **short EURUSD nhận carry dương** (~+137bp/yr gross theo policy differential, trừ broker markup thường 1–3%/yr); long trả tương tự.
- Daily ATR điển hình: 40–90 pip regime thường; 100–160 khi có macro driver rõ; 200–400+ trong shock (2022-style). Vol theo tuần: Monday thường nén đến giờ London; Tuesday–Thursday có directional bias tốt nhất; Friday bị chi phối bởi US data + pre-weekend untold.
- **Weekend gap**: median nhỏ (~10–30 pip) nhưng fat-tail — Sunday-open gap 50–150 pip khi có biến Middle East/Nice-style shock; hiện tại là rủi ro sống (xung đột Iran 2026).
- Month/quarter-end: rebalancing flows làm nhiễu 2–3 phiên cuối kỳ, đặc biệt quanh **WM/Reuters 4pm London fix**.

**Bảng profile phiên (ước lượng kinh nghiệm — bắt buộc đo lại bằng tick data thực tế trước khi dùng)**

| Cửa sổ (GMT) | Tên | % daily range điển hình | Hành vi thống trị | Spread điển hình (ECN) |
|---|---|---|---|---|
| 21:00–00:00 | Sydney / late NY | 5–10% | drift, book mỏng | 0.5–1.5 pip |
| 00:00–07:00 | Tokyo | 15–25% | mean-reverting range | 0.3–1.0 pip |
| 07:00–08:00 | London open | 10–20% | impulse / stop-run, informational content cao | 0.2–0.6 pip |
| 08:00–12:00 | London morning | 25–35% | trend day được thiết lập | 0.1–0.4 pip |
| 12:00–16:00 | Overlap London/NY | 30–45% | continuation, depth sâu nhất | 0.0–0.3 pip |
| 16:00–18:00 | London close | 8–15% | fix flows, reversal cục bộ | 0.2–0.5 pip |
| 18:00–21:00 | NY afternoon | 5–12% | dead-zone drift | 0.3–1.0 pip |
| 21:00 (5pm NY) | Rollover | — | spread nổ 1–5 pip trong vài phút | nở mạnh |

Ghi chú theo ngày trong tuần:
- Monday: range nén đến giờ London; gap-open thường hoàn trả một phần nếu cuối tuần không có tin — tuần chưa cài đặt hướng.
- Tuesday–Thursday: directional content tốt nhất; German/EA data sáng GMT, US data chiều.
- Friday: NFP vào Friday đầu tháng; từ 18:00 GMT pre-weekend flattening; thứ Sáu có quarterly options expiries (NY 10am cut) thêm nhiễu.
- Hiệu ứng DST lệch: 2–3 tuần mỗi năm (Mar, Oct–Nov) "London open" theo giờ ET dịch tương đối — mọi session strategy phải tái tạo mốc giờ từ calendar, không hardcode.

**Ví dụ carry tính thô (regime 09-2026)** — short 1 lot EURUSD tại 1.1400, giữ 30 ngày:
- Rate leg: nhận USD ~3.875%/trả EUR 2.50% → gross ≈ +137.5bp/yr ≈ +$110/lot/tháng trên notional $114k (xấp xỉ, theo markup swap thực tế của broker mà ±).
- Markup broker thường ăn 1–3%/yr hai phía → net có thể gần 0 nếu markup nặng: lý do S38 (cost-aware carry) là gate bắt buộc chứ không phải chi tiết.
- Wednesday swap 3x; vị thế 6E chịu cùng economics qua calendar spread lúc roll quý — backtest futures phải back-adjust.

**6E futures linkage — chi tiết cho phần positioning của lane**
- Contract 125,000 EUR; tick 0.00005 = $6.25; giá trị 1 pip = $12.50; Globex gần 24/5 — gap pattern gần trùng spot.
- Roll quý H/M/U/Z: roll chính ~1 tuần trước Wednesday tuần 3 của expiry month; OI dồn sang back month làm OI tổng méo trong roll week — exclude roll week khi dùng S73.
- Fair value futures↔spot qua CIP: F = S·(1+r_USD·t)/(1+r_EUR·t); hiện futures dưới spot (discount ~137bp/yr) vì USD yield cao hơn — nhiều "backtest xu hướng" trên futures unadjusted thực chất là ăn roll yield, phải tách.
- COT (legacy + Disaggregated/TFF) của 6E là nguồn positioning sạch nhất của lane; data chốt Tuesday, phát hành Friday 15:30 ET — mọi signal COT chỉ được dùng từ close Friday trở đi (tránh look-ahead).
- Volume 6E cao nhất giờ Chicago morning (trùng overlap London/NY) — dùng volume/OI 6E làm proxy institutional cho spot khi feed spot không có volume thật.

**Điểm structure riêng đáng nhớ**
- Không có intervention risk đáng kể ở 2 leg (khác USDJPY/USDCHF) — can thiệp chỉ mang tính verbal hiếm hoi.
- Option market sâu nhất nhì thế giới sau (hoặc ngang) USDJPY: risk reversal, butterfly, expiry walls là thông tin thật, không phải noise.
- Cả hai leg đều reserve currency → EURUSD **không phải** proxy risk-on/off sạch (khác AUDJPY); tính chất haven bị chia giữa USD và EUR, đổi theo loại crisis.

### 1.2 Điểm ĐẶC BIỆT riêng EURUSD so với 11 symbol còn lại trong universe

| Khía cạnh | Điều riêng của EURUSD |
|---|---|
| Purest policy-differential vehicle | Fed vs ECB là cặp CB lớn nhất thế giới; EURUSD là cách sạch nhất biểu diễn divergence này (GBPUSD bị pha BoE idiosyncrasy, USDJPY bị pha MoF/JGB). |
| DXY weight | EUR chiếm ~57.6% DXY → EURUSD gần như là **-DXY thuần**. Không symbol nào trong universe có tính chất này. |
| Energy terms-of-trade | EU là energy net-importer: gas/oil spike làm xấu ToT, GDP và CURRENT ACCOUNT của EA → EUR giảm. Ngược dấu hoàn toàn với CAD (petro). Kênh này là "chất riêng" post-2022 và đang sống dậy với Iran 2026. |
| Fragmentation tail | BTP-Bund (và OAT-Bund) spread là idiosyncratic eurozone sovereign risk — kênh áp lực EUR không tồn tại ở bất kỳ pair nào khác; gắn với anti-fragmentation tool (TPI) của ECB. |
| Dual reserve legs | Risk-off không tự động = EURUSD down. Đôi khi EUR được bid như funding currency unwind (BIS x-ccy basis) — EUR từng đóng vai trò funding cho EM carry tương tự JPY (yếu hơn). |
| Liquidity/efficiency | Chặt spread + sâu book → alpha từ pattern đơn thuần bị cạnh tranh arbitrage nhanh nhất; ngược lại macro transmission rõ và bền nhất. |
| Cross-vehicle hệ sinh thái | EURGBP, EURCHF, EURJPY cho phép tách noise: xem 1.5 và family 9. |
| Data cadence đối xứng | Hai nền kinh tế phát hành song song (CPI/HICP, PMI flash cùng ngày ~22–24 monthly) → relative-surprise trade khả thi có cấu trúc, hiếm cặp nào có lịch "đối xứng" đẹp thế. |

### 1.3 Tin tức/sự kiện ảnh hưởng

**Scheduled (mỗi mục kèm transmission channel)**

| Sự kiện | Nhịp | Channel chính vào EURUSD |
|---|---|---|
| FOMC decision + dots + presser | 8/năm (Sep-2026 vừa hike; dot plot 4.00–4.25 end-2026) | Rate-differential: repricing front-end UST → USD; dots + tone định đường differential tương lai; presser thường đảo nửa vòng statement move. |
| ECB decision + projections + presser | 8/năm (kế 29-10-2026) | Rate-differential chiều ngược + fragmentation channel (nói về spreads, TPI); lag trước US ~1 tuần tạo "policy ping-pong". |
| US CPI (core m/m) | ~13 hằng tháng | Fed path → USD; core m/m là con số nhạy nhất cho EURUSD trong 1–2 năm trở lại. |
| US NFP / employment report | Friday đầu tháng | Dual-mandate → Fed path; kèm revision; whisper thường khác consensus. |
| US PCE core | cuối tháng, trễ hơn CPI | Fed target chính thức nhưng trễ → ít surprise, dùng confirm. |
| EA HICP flash | cuối tháng (ngày làm việc cuối/cận cuối) | ECB path; core & services nhỏ nhất có sẵn ở flash. |
| Flash PMI (EA composite vs US flash) | ~22–24 monthly, CÙNG NGÀY | Growth-differential — setup đẹp cho relative-surprise (S52). |
| ISM M/M services | ngày làm việc 1 & 3 (US) | Growth-differential USD leg. |
| German factory orders / IP, Ifo, ZEW | đầu & cuối tháng | Early-cycle lead của EA cycle; orders là số "leading" nhất cho EUR. |
| ECB Consumer Expectations, UMich/consumer conf. | monthly | Inflation-expectation channel. |
| Jackson Hole + Powell/Lagarde testimony | Aug; testimony 2 lần/năm | Regime-shift channel: historical các pivot lớn được signal ở đây. |
| Treasury refunding + auction size | quý | Term-premium channel → UST yields → USD. |
| BTP/OAT/Bund auctions, rating actions (Moody's/Fitch/S&P) | rải rác | Fragmentation channel: BTP-Bund nở → EUR risk premium. |
| EU summit, German fiscal/debt-brake news, French budget | không định kỳ nhưng calendar rõ | Fiscal-differential + fragmentation. |
| OPEC+ meetings, Middle East war milestones | không cố định | ToT channel qua oil; hiện tại là driver hàng đầu (S58/S62/S63/S99). |
| Month/quarter-end, WM/R 4pm fix, option expiries (10am NY cuts, Friday lớn) | tháng/quý | Flow/hedging channel — không phải "news" mà là demand tạm thời. |

**Nhịp macro chuẩn của một tháng điển hình (dùng lập lịch cho family E/F)**

| Tuần | US | Euro area | Ý nghĩa trading |
|---|---|---|---|
| W1 | NFP (Friday đầu), ISM manufacturing (ngày làm việc 1), ISM services (ngày 3) | German factory orders / IP (ngày làm việc 5–6) | growth-differential đặt tone tháng |
| W2 | CPI (~13), retail sales | (im lặng lớn) | tuần repricing Fed path mạnh nhất |
| W3 | FOMC (hoặc blackout speaker window) | ZEW (Tuesday), EA industrial production | policy/data xen kẽ |
| W4 | Flash PMI, PCE (cuối tháng) | Flash PMI composite + HICP flash (cuối tháng) | relative surprise window đẹp nhất tháng (S52/S53) |
| Cuối tháng | month-end fix, rebalance | German Ifo (W3–W4 tùy lịch) | flow week (S43/S44) |

Quý: 4 kỳ FOMC có dots và 4 kỳ ECB có projections (Mar/Jun/Sep/Dec) lệch nhau ~1 tuần — hai tuần quanh cặp meeting này là cao điểm vol trung bình năm; "policy ping-pong" Fed→ECB→Fed là khung cho S5/S54/S55.

**Phân loại transmission channel (6 kênh — dùng chung cho mọi event ở trên)**

| Kênh | Cơ chế | Horizon điển hình | Sự kiện tiêu biểu |
|---|---|---|---|
| Rate-differential / expectations | repricing đường lãi ngắn →carry & discounting | phút → tuần | FOMC, ECB, CPI, NFP, OIS moves |
| Growth-differential | kỳ vọng tăng trưởng tương đối → dòng vốn dài hạn | tuần → quý | PMI, ISM, German orders |
| Terms-of-trade | giá năng lượng nhập khẩu → current account EA | ngày → tháng | OPEC+, war spikes, TTF |
| Risk sentiment / haven | USD vs EUR như tài sản an toàn (bất đối xứng theo loại khủng hoảng) | giờ → tuần | VIX spikes, credit events |
| Flow / hedging | fix, rebalance, options expiry tạo demand tạm thời | phút → ngày | month-end, WMR fix, expiries |
| Fragmentation / sovereign | rủi ro peripheral EA → risk premium nội tại EUR | tuần → quý | BTP spreads, rating, elections |

**Unscheduled**
- Middle East escalation (Iran 2026 đang sống): oil spike → ToT hit EUR + USD haven bid + ECB forced hawkish — ba lực không cùng dấu, tuần tự: ngày 1 EUR gục, sau đó hawkish-ECB discount có thể kéo EUR lại (đã thấy pattern 06→09-2026).
- Russia–Ukraine energy infrastructure strikes: tương tự qua TTF.
- Pháp/Ý chính trị (motion de censure, snap election kiểu 2024), German coalition shocks: fragmentation channel.
- Credit downgrade Pháp/Ý: fragmentation.
- Cross-currency basis blowout / repo stress: funding channel, EUR bị bid khi basis thắt (EUR funding demand).
- Thin-liquidity flash event (kiểu 03-01-2019 JPY flash crash): EURUSD ít đau hơn JPY crosses nhưng văng theo; Monday gap risk.
- Verbal intervention / WSJ/FT stories về Fed/ECB thinking ("trial balloon"): channel kỳ vọng, hiệu lực giờ.

### 1.4 Thông số ảnh hưởng (driver dashboard)

1. **Short-rate differential & path**: Fed funds vs ECB depo; 2Y OIS forward paths. Driver số 1 horizon ngày–tuần.
2. **2Y government spread (UST–Schatz)**: proxy market pricing của differential — rất sát price action EURUSD intraday quanh data.
3. **10Y spread (UST–Bund) + term premium**: driver tuần–tháng, thêm growth/TP dimension.
4. **DXY**: EURUSD thường ~ −0.90 trở lên với DXY; dùng như sanity check xem move là "USD-wide" hay "EUR-specific".
5. **Risk sentiment (VIX, S&P, credit spreads)**: correlation không ổn định — dùng có điều kiện (S66), đừng hardcode.
6. **Energy**: Brent/WTI (ToT), **TTF** (EA-specific pain), **TTF–Henry Hub spread** (EA vs US energy divergence — chất riêng, S63), US natgas (phản chiếu US inflation → Fed hawkish).
7. **BTP-Bund 10Y (và OAT-Bund)**: fragmentation premium của EUR.
8. **Breakevens/inflation swaps 5y5y EA vs US**: real-rate differential decomposition.
9. **Positioning & flows**: CFTC COT 6E, 25-delta risk reversal, x-ccy basis, COFER (quý), ETF AUM, month-end fix ước tính.
10. **Carry/swap**: forward points; hiện short có carry dương ~137bp gross — ảnh hưởng cost model của mọi longer-holding idea.

**Ngưỡng cảnh báo nhanh (trigger đề xuất cho weekly checklist — số liệu phải hiệu chỉnh khi re-measure)**

| Driver | Ngưỡng | Hành động sleeve |
|---|---|---|
| 2Y diff (Fed−ECB) slope 20d | đổi dấu | re-evaluate toàn bộ trend/carry bias (S1/S8/S31) |
| 10Y UST−Bund | vượt ±1σ 60d | bias multi-week cho S37/S64 |
| DXY non-confirmation | EURUSD move mà DXY <30% implied | bật S19 fade / giảm size breakout |
| Brent 1d | >±4% kèm supply tag | bật S58/S62/S99 short stack |
| TTF−HH z(20d) | >2 | bật S63; cảnh báo ToT regime |
| BTP-Bund 10y | Δ tuần >+15bp | tắt MR longs; bật fragmentation caution |
| VIX | <18 / >28 | đổi chiều sleeve bias theo S66 |
| COT 6E percentile | >90 / <10 | bật S71 watch; kết S80 overlay |
| 25d RR z(1Y) | ±2 | bật S75/S93 confirm |
| 1w−1M implied vol | <0 | event radar S92: stand-aside pre-event |

### 1.5 Correlation map với 11 symbol (baseline 60–90d daily returns — KINH NGHIỆM, cần re-measure tại thời điểm chạy)

| Symbol | Correlation điển hình vs EURUSD | Cùng driver nào | Khi nào breakdown |
|---|---|---|---|
| GBPUSD | +0.65 … +0.85 | USD leg (anti-USD chung) | BoE divergence, gilt stress, UK fiscal shock; UK data day mà US im lặng |
| USDCHF | −0.75 … −0.90 (đôi khi −0.95) | CHF bị chi phối bởi EURCHF; EURUSD up ⇒ USDCHF down gần máy móc | SNB act (verbal/real) trên EURCHF; khủng hoảng geopolitical thật sự (CHF haven bid mạnh hơn EUR) — lưu ý regime Iran 2026 có thể làm nhiễu |
| AUDUSD | +0.35 … +0.70 | USD leg + risk appetite | Commodity/China idiosyncrasy; RBA divergence; iron ore shock |
| NZDUSD | +0.30 … +0.60 | như AUD, beta thấp hơn | AU–NZ spread moves; RBNZ bất thường |
| USDCAD | −0.40 … −0.75 | USD leg | **Oil lớn**: oil up ⇒ CAD up (USDCAD down) trong khi EUR down (ToT) ⇒ hai pair cùng giảm, correlation số tụt/thậm chí đảo dấu — đang là regime 2026, cực kỳ quan trọng |
| USDJPY | −0.20 … +0.30 (bất ổn nhất) | gần như không có driver chung ổn định | Phân rã: UST yields lên ⇒ USDJPY up + EURUSD down (corr −); risk-off ⇒ JPY up + USD up (corr +) — luôn condition theo nhóm shock |
| XAUUSD | +0.10 … +0.50 | anti-USD chung; real yields âm giúp cả hai | Khủng hoảng thật: gold bid bằng cả USD lẫn EUR; ToT shock: gold (inflation hedge) up trong khi EUR down — âm lại |
| XAGUSD | +0.10 … +0.45 | như gold, beta vol cao | Industrial demand (global growth) trội: XAG up cùng risk-on mà EUR đi theo USD leg |
| BRENT | −0.10 … −0.45 (post-2022; trước ~2014 mixed) | ToT channel + USD-inflation channel | USD-led oil sell (dollar down, oil up, EUR up) ⇒ dương; supply-led spike ⇒ âm mạnh — hiện tại âm |
| WTI | −0.10 … −0.40 | như Brent | WTI–Brent spread nở (US-specific supply) ⇒ EUR ít phản ứng hơn Brent — dùng chênh lệch này là signal (S62/S63) |
| NATGAS (HH) | ~0.0 ± 0.20 | gián tiếp qua US inflation → Fed | Chỉ ăn via TTF: HH spike làm US LNG export hấp dẫn hơn ⇒ hỗ trợ gián tiếp EA supply ⇒ nhẹ dương cho EUR (yếu) |

**Ma trận driver-chủ-đạo → dấu kỳ vọng (cách "đọc" map trên mỗi tuần)**

| Driver chủ đạo | EURUSD | DXY | Oil | XAU | Nhận biết đang ở regime nào |
|---|---|---|---|---|---|
| Fed repricing | ngược USD | dẫn dắt | nhẹ | ngược USD | move bắt đầu tại US data/statement; UST dẫn FX vài phút |
| ECB repricing | theo EUR | phản chiếu nhẹ | ~0 | nhẹ | move bắt đầu tại EA data; Schatz/BTP dẫn |
| Energy shock (supply) | xuống | lên | lên mạnh | lên | oil dẫn, TTF nở, mọi FX dồn về USD-bid (regime 2026) |
| Risk-off thật | xuống (USD haven) | lên | xuống | lên | VIX spike, credit nở, JPY+CHF mạnh đồng loạt |
| Flow/fix | nhiễu 15–60 phút | mờ | ~0 | ~0 | giờ fix / cuối tháng / volume bất thường không headline |

Cách dùng đúng: correlation là **hệ quả của driver chung**, không phải hằng số — mọi idea ở family 7 đều gate theo "driver nào đang chủ đạo" (USD-wide vs EUR-specific vs commodity-specific vs risk).

### 1.6 Note trung thực: bối cảnh nào các họ strategy hay chết trên EURUSD

- **Trend-following chết** trong "coordination chop": khi Fed và ECB cùng im lặng/cùng hướng yếu (kiểu 2019, các đợt summer range): ADX thấp, whipsaw quanh EMA200; drawdown dài không trend.
- **Mean-reversion chết** trong policy-divergence freight train (2014 taper–QE chênh lệch, 2021–2022 Fed-vs-đứng yên ECB): fade mọi rally liên tục bị đè bẹp; và chết nhanh nhất khi **energy shock** đang chạy (2026): "EUR rẻ quá nên mua" là lý do tồi khi ToT đang xấu đi.
- **Breakout chết** trong tuần không data + nửa hè: London breakout false-rate cao khi không có catalyst; NR7 breakout bị push ngược tại NY open.
- **Carry chết** tại pivot đồng loạt (2008, 2020-03, hoặc khi Fed bắt đầu cut trong khi market chưa price); hiện tại carry short đang đẹp nhưng chính ECB catch-up hike là rủi ro thu hẹp differential — carry không phải free lunch, luôn kèm vol regime gate (S38, S100).
- **Event/data strategy chết** khi consensus đã = whisper và OIS đã price: surprise thực = 0 dù headline "hawkish"; cũng chết trên slippage nếu backtest không mô hìnhng spread nở quanh release.
- **Stat-arb/crosses chết** khi quan hệ policy thay đổi nhanh: EURGBP band chết khi BoE–ECB divergence bùng (2022–23 kiểu mini-2022); EURCHF là warn lịch sử về regime break (15-01-2015).
- **Pattern đơn thuần** (chart suông không macro conditioning) yếu nhất ở EURUSD vì efficiency cao — cần một trong: session edge, flow edge, hoặc macro gate, nếu không sau chi phí ~0.6–1.2 pip/round trip sẽ âm.

### 1.7 Đọc nhanh regime 09-2026 cho lane EURUSD

Snapshot để hậu kiểm (viết 2026-09-28, mọi số verify tại đầu file):
- **State**: (Fed hike, ECB hike) — quadrant "both-hiking" hiếm; differential level 137.5bp USD-favor nhưng **slope đang thu hẹp** nếu ECB thực hiện 3+ hike đã price trong khi Fed chỉ còn 1 per dots → carry short (S31) có thu nhập nhưng rủi ro unwind tăng theo từng kỳ họp ECB.
- **Overlay energy**: xung đột Trung Đông giữ oil cao → ToT vẫn âm cho EUR (S62/S63/S99 justified); nhưng chính shock đó buộc ECB hawkish — kênh kép đẩy EUR hai chiều: ngày oil-spike thì xuống, tuần ECB-hawkish-repricing thì lên. Đó là vì sao top ideas tập trung ở family D/F (đo đúng surprise) thay vì trend suông.
- **Sleeve nên ON**: D (carry có gate), F (event drifts), H (positioning extremes), B giới hạn intraday range-session; **OFF/giảm size**: A trend thuần (chờ differential slope rõ), C breakout thuần (chop quanh policy ping-pong), I band trades liên quan policy (rủi ro break).
- **Rủi ro đặc thù tuần tới**: ECB 29-10 và FOMC cuối 10 (ngày chính xác cần kiểm chứng) — hai bên có thể đẩy differential hai hướng; weekend gap risk từ Middle East headlines; month/quarter-end flow cuối tháng 9 vừa qua để lại drift.
- **Invalidation tổng**: nếu ECB chỉ hike đúng 25bp và guidance dovish-tilt → differential slope quay lại mở rộng USD-favor → carry + trend short bật mạnh; nếu ECB signal chuỗi hike nhanh hơn → rút ngắn mọi short bias, bật long-drift F-sleeves.

---

## 2. 100 strategy ideas

Quy ước: family = A Trend/Momentum · B Mean-reversion · C Breakout/Vol-expansion · D Carry/Rate-differential · E Session/Time/Seasonality · F Event/Data-driven · G Cross-asset/Correlation · H Positioning/Flows · I Pattern/Pairs/Stat-arb · J Regime-conditioned/Options-flavored. Timeframe viết tắt: TF = M5/H1/H4/D/W.

Luận đề kinh tế gốc của từng family (mỗi family 10 ý đều là biến thể cơ chế, không phải đổi ngưỡng):

| Family | Luận đề kinh tế gốc | Điều kiện sống |
|---|---|---|
| A Trend | policy/growth differential autocorrelated → underreaction kéo dài | vol percentile 20–80, differential slope rõ |
| B Mean-reversion | EURUSD hiệu quả cao → noise không info hoàn trả | low-ADX, không event, không freight |
| C Breakout | nén vol tích tụ positioning → release có continuation | có catalyst hoặc squeeze cấu trúc |
| D Carry | rate risk premium tồn tại (UIP thất bại) | differential ổn định + vol thấp |
| E Session | cấu trúc flow theo giờ/ngày cố định (fix, session liquidity) | calendar đúng DST, không holiday |
| F Event | surprise → repricing path CB chậm hơn lý thuyết | đo surprise đúng (OIS/whisper), không consensus suông |
| G Cross-asset | driver chung tạo quan hệ dẫn–theo đo được | phân loại đúng driver chủ đạo |
| H Positioning | crowd phải giải phòng khi flow đảo | extreme + divergence confirm |
| I Pairs/Stat-arb | quan hệ dài hạn giữa các cross có lực hồi | cointegration chưa bị policy break |
| J Regime/Options | điều kiện thị trường quyết định sleeve nào sống | state variable đo được (vol, policy, smile) |

**Ma trận holding horizon (để chọn sleeve theo cơ chế hạ tầng dữ liệu & monitoring có sẵn)**

| Horizon | Ideas tiêu biểu | Yêu cầu hạ tầng |
|---|---|---|
| Scalp (phút–giờ) | S17, S19, S20, S42, S64, S76, S83, S89 | tick data, cost thực đo, news wire realtime |
| Intraday (1 phiên) | S11, S21, S30, S41, S45, S49, S52, S77, S84 | M5–M15 + calendar chính xác DST |
| Swing (2–10 phiên) | S12, S13, S16, S22, S24, S26, S27, S28, S53, S55, S58, S59, S61, S71, S76 | daily + surprise/expiry/COT calendar |
| Multi-week | S1, S2, S5, S7, S8, S31, S33, S34, S35, S37, S39, S51, S54, S56, S62, S63, S67, S72, S79, S81, S82, S85, S93, S99 | yields/OIS/TTF/COT series |
| Multi-month/structural | S3, S6, S18, S40, S44, S47, S48, S50, S68, S69, S78, S100 | quarterly datasets, reserve/flows data |

### Family A — Trend/Momentum (S1–S10)
*Phân biệt cơ chế trong family: S1/S8/S10 dùng đồng thuận rates-macro; S2/S7 cấu trúc kênh/extreme; S3/S6 thống kê cross-section; S4/S5/S9 cấu trúc giá-sự kiện.*

**S1 — Policy-divergence trend lock (A)**
Hypothesis: chênh lệch policy Fed/ECB được truyền thông autocorrelated nên trend EURUSD bền khi price và 2Y differential cùng hướng · Signal: giá D trên EMA200 + slope 2Y UST–Schatz 20 ngày cùng dấu · Trade: vào theo hướng trend tại pullback H4 về EMA20, stop 1.5×ATR(14) dưới swing, trail Chandelier · Risk: pivot đồng loạt hai CB làm divergence sập giữa đường · Data: EURUSD OHLC, 2Y yields cả hai nước · Coupling: không vào ngược hướng slope differential quá 3 ngày.

**S2 — Donchian 20/55 vol-normalized breakout (A)**
Hypothesis: breakout kênh đa tuần phản ánh macro regime shift được thêm giá trị bởi underreaction · Signal: đóng cửa D qua Donchian 55 (entry) với Donchian 20 làm trailing ngược · Trade: size = risk 0.5%/trade theo ATR(20); pyramid 1 lần · Risk: chop regime sinh chuỗi false break · Data: OHLC D · Coupling: chỉ long breakout nếu Brent không ở spike regime z>1.5 (tránh long EUR chống ToT).

**S3 — Time-series momentum 3–12M (A)**
Hypothesis: momentum horizon quý–năm từ slow diffusion của policy/growth differential · Signal: dấu của return tích lũy 6 tháng qua; holding scale theo vol mục tiêu · Trade: rebalance tháng, size inversely ATR(60) · Risk: đảo regime USD cycle kiểu 2008, 2022 reversal · Data: monthly closes, D ATR · Coupling: gate bằng policy-cycle quadrant (S100) — tránh cả-hai-cùng-hawk chop như hiện tại nếu differential flat.

**S4 — Market-structure continuation London-confirmed (A)**
Hypothesis: swing H4 break có informational content cao nhất khi diễn ra trong London nếu là trend thật · Signal: BOS (break of structure) HH/HL trên H4 xảy ra 07:00–16:00 GMT · Trade: entry retest FVG/order block gần break, stop dưới swing low, RR≥2 · Risk: London fake BOS trong tuần trống data · Data: H4 candles + lịch data · Coupling: số phiên có BOS ≥2/3 tuần mới xác nhận trend active.

**S5 — Post-decision direction join (A)**
Hypothesis: hướng được "khóa" tại ngày FOMC/ECB decision có drift vì positioning chưa kịp chuyển hết · Signal: direction = dấu return ngày decision; filter: |return| > 0.75×ATR(20) của ngày đó · Trade: vào open ngày H+1 theo hướng, giữ tối đa 15 phiên, stop 2×ATR · Risk: decision "non-event" rồi đảo chiều tại data tiếp theo · Data: lịch CB + daily bars · Coupling: hủy nếu phiên H+2 đóng ngược quá 50% decision candle.

**S6 — Cross-sectional anti-USD ranking (A)**
Hypothesis: USD trend là yếu tố chung; EUR chỉ đáng trade long khi là cặp anti-USD mạnh nhất bảng · Signal: rank 20d return của {EUR,GBP,AUD,NZD,CHF,JPY,CAD} vs USD; vào EURUSD long chỉ khi EUR rank 1–2 · Trade: hold tới khi rơi khỏi top-3, stop 2×ATR · Risk: EUR-specific bad news giữa kỳ (fragmentation) · Data: close 7 pair · Coupling: rank nhất quán 2 tuần liên tiếp mới vào.

**S7 — Weekly Keltner trend ride + pyramid (A)**
Hypothesis: extreme tuần phản ánh flow institutional accumulations nhiều tuần · Signal: đóng W trên EMA20(W) + Keltner(20,2.5ATR); thêm 0.25N mỗi lần W close mới cực đại · Trade: stop trượt theo mid-band, exit 2 closes trong band · Risk: blow-off reversal chỉ trong một tuần · Data: W bars · Coupling: COT cùng phía (family H) thì giữ full size, ngược thì nửa.

**S8 — Carry-momentum agreement (A)**
Hypothesis: trend có nền tảng kinh tế mạnh nhất khi rate differential slope và price cùng chiều (hai thị trường đồng thuận) · Signal: slope 20 ngày của forward points (hoặc 2Y diff) + EMA50/EMA200 cross trên D cùng dấu · Trade: entry pullback, size 0.75% risk, trail ATR×3 · Risk: differential flat regime sinh whipsaw · Data: forward points/2Y, OHLC · Coupling: x-ccy basis không stress ngược hướng.

**S9 — MACD-histogram exhaustion exit (A)**
Hypothesis: momentum decay thấy trước price turn ở horizon tuần · Signal: vào trend theo EMA alignment; thoát khi MACD-H(12,26,9) D phân kỳ 2 đỉnh với price · Trade: thoát phần 2/3 tại divergence, phần còn trail swing · Risk: thoát sớm trong freight train 2022-style · Data: D bars · Coupling: chỉ dùng exit rule này khi vol percentile <80.

**S10 — Vol-expansion-confirmed trend entry (A)**
Hypothesis: move có vol thật đi kèm tiếp diễn, move vol-thiếu (drift mỏng) hay fail — tách hai loại này ngay từ đầu · Signal: nến D vượt EMA50 kèm range ≥1.3×ATR(20) và tick-volume ≥1.5× trung bình 20 ngày · Trade: vào breakout close, stop dưới nến signal · Risk: event-day vol tự tắt sau 1 ngày (fade tail) · Data: D bars + tick volume + calendar · Coupling: loại nến event-day (CPI/FOMC) khỏi signal vì vol méo.

### Family B — Mean-reversion (S11–S20)
*Phân biệt cơ chế: S11/S20 noise session; S12/S13/S15 oscillator tại structure/expiry; S14/S18 anchoring mốc thời gian/giá; S16/S19 reversion sau khi nhận diện "không-info move".*

**S11 — Asia-range fade at London open (B)**
Hypothesis: drifted Tokyo range chủ yếu là noise thin-liquidity, London pricing-in đảo lại hướng fair · Signal: giá lệch ≥70% Asian range (00–07 GMT) một phía khi London mở · Trade: fade về giữa/đáy range, stop 8 pip ngoài extreme Asia, target mid-range rồi VWAP morning · Risk: London breakout thật (khi có data 07:00–08:00 GMT kiểu German data) · Data: M15 + calendar DE/EA · Coupling: skip nếu hôm có EA flash data trước 09:00 GMT.

**S12 — RSI(2) extreme fade at structure (B)**
Hypothesis: exhaustion ngắn hạn tại weekly S/R có xác suất bật cao nhất vì liquidity hai phía · Signal: RSI(2) H1 <5 (hoặc >95) CHỈ khi giá trong 15 pip của weekly pivot/round number và ADX(D)<25 · Trade: fade về EMA9(H1), stop 1×ATR(H1), 2_ENTRIES scaling · Risk: counter-trend trong divergence freight · Data: H1, D, W pivots · Coupling: cấm khi |slope 2Y diff| 20d ở top-quartile (macro đang chạy).

**S13 — Bollinger z-score reversion in low-ADX (B)**
Hypothesis: khi không có driver macro, giá revert về mean theo micro-mean-reversion tính chất của EURUSD hiệu quả · Signal: z=(close−SMA20)/σ20 trên H4 vượt ±2 khi ADX(14,H4)<20 · Trade: vào ngược, target SMA20, stop tại 2.8σ · Risk: vol regime chuyển mid-trade (event) · Data: H4 bars · Coupling: tắt hẳn sleeve này trong tuần có FOMC/ECB/CPI hai bên.

**S14 — Monday weekly-pivot fade (B)**
Hypothesis: Monday open overshoot quanh weekly pivot do weekend-gap pricing thường tự sửa Tue–Wed khi tuần không có macro sớm · Signal: Monday close cách pivot W ±1.2×ATR(20)/5 · Trade: fade hướng lệch vào Tuesday London, target pivot, stop 1.5×ATR(D)/3 · Risk: tuần có FOMC/ECB sớm thì pivot fade chết · Data: W/D bars + calendar · Coupling: chỉ khi Friday trước đó không có US shock close.

**S15 — Round-number & expiry-strike fade (B)**
Hypothesis: mốc 00 (1.10/1.15) + option strike lớn tạo "gravity" và pin, rồi puncture — hai pha đều trade được nhưng cần biết mình ở pha nào · Signal: giá tiếp cận trong 10 pip mốc 00 có expiry report ≥500M EUR strike trùng · Trade: pha pin: fade về xa 8–12 pip với stop ngoài; pha puncture: vào break sau khi đóng M15 ngoài mốc kèm vol nở · Risk: đứng giữa hai pha (vào pin khi sắp puncture) · Data: expiry reports (mỗi sáng), M15 · Coupling: RR 25d không cực đoán cùng phía pin thì mới fade.

**S16 — Post-data overshoot fade vs whisper (B)**
Hypothesis: khi surprise nhỏ hơn chênh whisper-consensus, move phút đầu là liquidity event chứ không phải info → hoàn trả · Signal: spike 1-phút ≥25 pip sau release nhưng surprise <0.5σ lịch sử surprise · Trade: fade spike khi M1 đóng ngược, stop cao/thấp spike +3 pip, target pre-event price · Risk: surprise thực lớn (mis-read ban đầu) · Data: L1 hoặc M1 quanh release + surprise history · Coupling: chỉ làm với data có lịch sử whisper tốt (CPI, NFP, PMI).

**S17 — NY-session VWAP reversion (B)**
Hypothesis: dead-zone 17:00–20:00 GMT thiếu taker flow nên lệch VWAP ngày tự kéo về · Signal: giờ 17:30–19:30, giá lệch session-VWAP ≥1.2×ATR(H1), không có headline · Trade: scalp về VWAP, stop 10 pip, time-stop 90 phút · Risk: late headline/positioning day (month-end) · Data: M5 + VWAP + newswire · Coupling: skip 2 phiên cuối tháng và phiên có Fed speaker 18:00+.

**S18 — 200dma stretch rubber band (B)**
Hypothesis: lệch xa MA200 quá 2.5 ATR là mức mà mean-revert macro (valuation/CTA rebalancing) historically gapped về · Signal: close − MA200 ≥2.5×ATR(20) trên D (chiều bất kỳ) · Trade: fade với lệnh chia 3 entry trong 3 phiên, target MA200, stop 1×ATR(20) ngoài extreme · Risk: đây là counter-trend lớn — chết trong freight train nếu không có macro catalyst đổi chiều · Data: D bars · Coupling: chỉ vào khi có event catalyst phía revert (CB pivot speech, oil roll-over).

**S19 — DXY non-confirmation fade (B)**
Hypothesis: move EURUSD mà DXY không xác nhận là idiosyncratic noise (một maker sweep) → hoàn trả trong phiên · Signal: |ΔEURUSD 15'| ≥12 pip trong khi |ΔDXY implied| <3 pip tương đương · Trade: fade về mức trước sweep, stop 8 pip, target pre-sweep · Risk: move là tin EUR chưa public (headline sắp ra) · Data: tick/M1 EURUSD + DXY realtime · Coupling: skip quanh 10:00 NY option cut.

**S20 — Tokyo micro-reversion scalps (B)**
Hypothesis: session Tokyo của EURUSD gần như pure noise mean-revert vì không info flow — thống kê đủ tốt cho scalp chi phí thấp · Signal: BB(40,2) trên M5 trong giờ 01:00–06:00 GMT, fade chạm band khi BB width percentile <40 · Trade: target mid-band, stop 6 pip, tối đa 3 lần/đêm · Risk: gap-tin đêm (geopolitics) và spread nở · Data: M5 + broker cost thật · Coupling: dừng sleeve khi có escalation headline Middle East (regime 2026).

### Family C — Breakout/Vol-expansion (S21–S30)
*Phân biệt cơ chế: S21/S23/S24 cấu trúc range-thời gian; S22/S30 event-kick; S25/S27 chuyển regime vol; S26/S28/S29 phản-breakout hoặc level-macro.*

**S21 — London opening range breakout (C)**
Hypothesis: nửa giờ đầu London gói thông tin Frankfurt+London; break range đó là hướng có follow-through tốt nhất tuần · Signal: break 30' đầu London (07:00–07:30 GMT) với filter chỉ trade khi ATR(H1) percentile>30 · Trade: stop ngoài range 5 pip, target 1.5× range, move BE sau 1R · Risk: false-break ngày trống news · Data: M5/M15 + calendar · Coupling: chiều break phải cùng dấu slope 2Y diff tuần đó.

**S22 — Pre-NFP compression straddle (C)**
Hypothesis: vol compression trước NFP + lịch sử NFP tạo kick lớn một phía → buy straddle-style bằng stop orders hai chiều · Signal: ATR(5D) percentile <25 vào phiên Friday NFP · Trade: stop-entry ±0.5×ATR(D) quanh pre-release price 12:30GMT; winner trail, loser hủy khi phía kia trigger (OCO) · Risk: inside-number NFP hai số bù nhau → không đi đâu · Data: D ATR + release clock · Coupling: chỉ khi whisper ≠ consensus rõ ràng (đã kiểm calendar commentary).

**S23 — Weekly opening-range measured move (C)**
Hypothesis: week đầu tiên break Monday range thường extend bằng N× range (measured move logic) vì weekly flow kế thừa · Signal: Monday high/low bị phá Tuesday–Wednesday với London volume · Trade: target = break point ±1.0×Monday range, stop nửa range · Risk: tuần FOMC/ECB đảo chiều giữa tuần · Data: D/H4 + calendar · Coupling: CB-week thì giảm target một nửa.

**S24 — NR7 / inside-day daily breakout (C)**
Hypothesis: nén range đa ngày tích tụ energy positioning; break có continuation 2–4 phiên · Signal: NR7 hoặc 2 inside-days liên tiếp trên D · Trade: stop-order hai phía quanh day range +3 pip; trail 2×ATR(10) · Risk: nén do "chờ data" → break ngay tại data rồi đảo · Data: D bars + calendar · Coupling: nếu NR7 rơi ngay trước CPI/FOMC thì hoãn xử lý như S22 thay vì breakout thuần.

**S25 — BB-squeeze directional release (C)**
Hypothesis: sau squeeze, hướng release xác nhận bằng rate-differential momentum có chất tải (cả vol lẫn macro) · Signal: BB width (D) percentile<15; hướng = dấu 10-day change 2Y diff · Trade: vào nến D đầu đóng ngoài band cùng hướng, stop 1.2×ATR · Risk: release ngược macro một phiên rồi quay lại · Data: D bars + 2Y diff · Coupling: dầu (Brent 3d) không được ngược hướng quá 1σ.

**S26 — Failed-breakout reversal / spring (C)**
Hypothesis: stop-hunt trên daily extremes để rồi quay vào range là footprint của absorption; reversal có edge khi có tick-volume divergence · Signal: wick qua 20-day high/low rồi đóng ngược vào range, tick-volume của candle phá kỷ lục nhưng close yếu · Trade: vào theo close, stop ngoài wick, target mid-range · Risk: breakout thật hai nến (già stop) · Data: D bars + tick volume · Coupling: tốt hơn khi trước đó 1–2 ngày có COT extreme cùng phía bị hunt.

**S27 — ATR-ratio expansion onset (C)**
Hypothesis: chuyển regime vol xảy ra khi ATR ngắn/vài dài vượt ngưỡng — vào sớm trend kèm vol mới sống · Signal: ATR(5)/ATR(50) trên H4 vượt 1.5 từ dưới 1.0 trong 10 phiên · Trade: vào hướng nến gây expansion, stop 1×ATR(5), trail · Risk: spike một phiên tự dập (event stub) · Data: H4 bars · Coupling: nến expansion không nằm trong release-window thì độ tin cậy cao hơn.

**S28 — Monday gap conditional trade (C)**
Hypothesis: gap mở tuần có hai loại — flow-gap (fill) và news-gap (extend); phân loại bằng nguyên nhân Friday close · Signal: gap >0.5×ATR(D); nếu Friday close do US data thrust → trade continuation, nếu không rõ nguyên nhân → trade fill · Trade: fill: target close Friday; continuation: trail sau 1 phiên · Risk: phân loại sai · Data: W gap + newswire tuần trước · Coupling: gap cùng chiều oil-shock tuần đó thì continuation xác suất cao hơn (2026 context).

**S29 — Monthly extreme break with expiry wall (C)**
Hypothesis: phá high/low tháng trước là level macro thật; nếu trùng expiry strike lớn bị puncture, dealer gamma flip tạo fuel · Signal: close D ngoài monthly H/L + strike ≥1bn trong 20 pip phía ngoài bị xé · Trade: entry retest level, stop trong range cũ 10 pip, target 1×ATR(M) · Risk: puncture giả rồi snap lại trong tháng · Data: D/M bars + expiry reports · Coupling: RR không cực đối ngược hướng.

**S30 — Post-event failed-spike drift (C)**
Hypothesis: khi spike phút-đầu bị hoàn trả >80%, phía còn lại thường drift tiếp phần còn lại ngày (wrong-footed positioning thoát) · Signal: sau release, 15' đầu vẽ spike rồi quay qua pre-event;-condition reversal vượt pre-event +5 pip · Trade: vào phía breakout ngược, trail 15', giữ tới NY close · Risk: two-way data day · Data: M1/M5 quanh release · Coupling: làm sau CPI/PMI, không làm sau FOMC (presser hai chiều).

### Family D — Carry/Rate-differential (S31–S40)
*Phân biệt cơ chế: S31/S34/S38 carry thuần + gates; S32/S36/S37 tín hiệu đường cong; S33/S39/S40 deviation funding/term-premium; S35 drift sau policy surprise.*

**S31 — Classic policy-gap carry short (D)**
Hypothesis: chênh lệch policy 137bp (Fed mid vs ECB depo) + forward points cho phép thu carry khi vol thấp · Signal: differential >100bp và 1M implied vol percentile <50 · Trade: short EURUSD core size, hold tháng, hedge tail bằng far-put khi vol percentile >70 · Risk: ECB catch-up 3 hike thu hẹp gap → unwind mạnh (chính risk 2026) · Data: forward points, policy rates, implied vol · Coupling: gate S100 quadrant; S38 cost-check.

**S32 — 2Y swap-differential slope trade (D)**
Hypothesis: thị trường swap 2Y pricing path CB nhanh hơn FX (thông tin chảy rates→FX); slope swap-diff là dẫn đường · Signal: 5-day change 2Y swap diff vượt ±15bp · Trade: vào hướng dấu (diff lên → USD mạnh → short EURUSD), giữ tới slope flat 3 phiên · Risk: risk-driven yield moves không phải policy (safe haven bid UST) · Data: 2Y swaps · Coupling: filter bằng equity VIX — bỏ qua tín hiệu khi VIX single-day >8%.

**S33 — Forward-point CIP-deviation signal (D)**
Hypothesis: khi forward points lệch khỏi money-market implied, phản ánh demand/supply tiền tệ (hedging corporate) đi trước spot flows · Signal: 3M forward points − CIP-implied points vượt ±1.5σ 60 ngày · Trade: cùng hướng premium (điểm thuận USD quá cao → short EURUSD vì demand USD chưa thể hiện hết vào spot) · Risk: deviation do credit/liquidity chứ không flow · Data: forwards + MM rates · Coupling: đối chiếu x-ccy basis cùng hướng mới vào.

**S34 — Carry + momentum combo gate (D)**
Hypothesis: carry thuần dễ chết bởi trend ngược; momentum đồng thuận lọc phần lớn tail đó · Signal: carry 3M >+50bp cho short VÀ 20d momentum âm · Trade: short, exit khi một trong hai điều kiện tắt (momentum đảo trước thường hơn) · Risk: cả hai đảo cùng lúc tại pivot — gap risk · Data: forwards, daily bars · Coupling: giữ nửa size khi có ECB meeting trong 2 tuần tới.

**S35 — Hawkish-surprise drift 20–40 ngày (D)**
Hypothesis: sau policy surprise thật (so với OIS prior, không phải consensus headline), underreaction kéo dài vài tuần vì investor rebalancing chậm · Signal: surprise index (OIS 1Y trước/sau decision) >+15bp cho Fed (hoặc >+10bp cho ECB chiều ngược) · Trade: vào hướng surprise ngày H+1, giữ tối thiểu 20 phiên trừ khi stop 2.5×ATR · Risk: surprise bị "taken back" bởi data ngược ngay sau · Data: OIS curve quanh meeting dates, calendar · Coupling: kết hợp COT — nếu positioning đã extreme cùng hướng thì nửa size (squeeze risk).

**S36 — OIS-implied fair-value convergence (D)**
Hypothesis: short-horizon EURUSD bám giá trị ngụ ý từ path OIS hai bên; lệch tạm thời từ flow noise hoàn trả · Signal: regress daily ΔEURUSD vào Δ(2Y OIS diff); residual z>2 · Trade: fade residual về fit, holding ~5 phiên, stop 1.5×resid σ · Risk: structural break làm model lỗi (quantitative tightening khác nhau…) · Data: OIS daily, EURUSD · Coupling: R² rolling >0.3 mới cho sleeve chạy.

**S37 — Curve-shape differential regime (D)**
Hypothesis: 2s10s slope so sánh (US dốc hơn EA) phản ánh growth + policy mix dài hơn → bias tuần–tháng cho USD · Signal: (US2s10s − EA2s10s) 20-day change > +10bp · Trade: bias short EURUSD trong mọi entry pullback của trend; không standalone entry · Risk: curve twist do sợ hãi (recession scare) làm slope dốc mà USD vẫn bid — ok; nhưng bull-steepening từ cut thì khác · Data: yield curves · Coupling: dùng như filter cho S1/S2 thay vì entry riêng.

**S38 — Cost-aware carry viability (D)**
Hypothesis: carry chỉ justified khi expected move against < carry thu được theo vol — kiểm mỗi tuần · Signal: (carry 3M annualized − broker markup) / (ATR annualized) >0.5 thì carry sleeve ON, <0.25 OFF · Trade: position sizing theo Sharpe-of-carry · Risk: markup broker đổi, Wednesday 3x quên model · Data: forward points markup, ATR · Coupling: là gate chính cho S31/S34.

**S39 — X-ccy basis stress signal (D)**
Hypothesis: basis EUR/USD thắt = demand USD funding của châu Âu và EUR loanables dư → tín hiệu EUR weak; cơ sở này mean-revert chậm nên có drift trade được · Signal: 3M x-ccy basis (EUR/USD) widen quá −25bp từ −10bp nền · Trade: short EURUSD trong lúc basis stress, thoát khi basis về trong 1σ · Risk: policy backstop (Fed swap lines) đảo basis nhanh · Data: x-ccy basis quotes · Coupling: cùng chiều với S33 tăng xác suất.

**S40 — Term-premium differential slow trade (D)**
Hypothesis: chênh term premium (UST vs Bund, ACM-style hoặc 5y5y fwd decomposition) là driver quý của USD mà price lag nhiều tuần · Signal: 60-day change term-premium diff >+20bp · Trade: bias position theo hướng, rebalance tháng, hedge bằng gold long một phần (risk regime) · Risk: premium estimate model-risk cao · Data: term premium estimates (FEDS/ACM-style), yields · Coupling: align với COFER trend (S78) thì giữ dài.

### Family E — Session/Time-of-day/Seasonality (S41–S50)
*Phân biệt cơ chế: S41/S42 microstructure giờ; S43/S44/S46 flow calendar institutional; S45/S49 event-giờ cố định; S47/S48/S50 regime mùa.*

**S41 — Overlap-only momentum continuation (E)**
Hypothesis: 13:00–16:00 GMT là window duy nhất có taker depth lớn đủ cho continuation intraday đáng tin sau chi phí · Signal: 12:00–13:00 thiết lập hướng, vào break M15 đầu tiên cùng hướng trong overlap · Trade: stop 1×ATR(M15)×1.5, target 2R, đóng hết 16:30 GMT · Risk: dead overlap ngày tháng 8 · Data: M15 + session clock · Coupling: chỉ khi không có data 14:00 GMT (US data 8:30/10:00 ET đổi giờ).

**S42 — Frankfurt pre-positioning fade (E)**
Hypothesis: 06:45–07:15 GMT có run-up trước German data/fix; run-up không có info tự bị sell khi data trùng consensus · Signal: move ≥12 pip 06:45–07:10 GMT không kèm headline, data 07:00 GMT in-line · Trade: fade về mức 06:45 · Risk: data miss thật · Data: M1 + DE data clock · Coupling: chỉ những ngày có scheduled DE data 07:00.

**S43 — Month-end WM/R 4pm fix imbalance (E)**
Hypothesis: flow rebalance cuối tháng (equity/bond return differential US vs EA) tạo demand một chiều quanh 4pm London fix cuối tháng — direction dự đoán được từ returns tháng · Signal: sign(US equity+bono return − EA return) tháng đang chạy với magnitude >2% · Trade: vào chiều flow 15:15–15:45 GMT ngày cuối cùng (LNBU), exit sau fix 16:15 · Risk: month có USD-hedging dự phòng lớn offset; fix ước tính sai · Data: SX5E vs SPX, Agg vs EA agg returns, fix calendar · Coupling: nếu quarter-end trùng (Mar/Jun/Sep/Dec) size gấp đôi vì hedging flows lớn hơn.

**S44 — Quarter-end hedge-rebalance drift (E)**
Hypothesis: European institutional US-asset holders phải bán USD hedging khi USD tăng quá mức trong quý (rebalance về hedge ratio) — tạo ngược chiều EURUSD cuối quý · Signal: QTD return EURUSD <−3% (USD mạnh) vào tuần cuối quý · Trade: long EURUSD nhẹ tuần cuối, exit ngày làm việc đầu quý mới · Risk: chỉ hoạt động khi flow USD-hedging lớn (rate regime), không phải luôn · Data: EURUSD QTD, hedging surveys (cần kiểm chứng source tốt) · Coupling: cùng hướng với S43 sign khi hai cái không mâu thuẫn.

**S45 — Friday-post-NFP drift (E)**
Hypothesis: chiều Friday sau NFP có continuation nhẹ của hướng NFP vì position cuối tuần không kịp build đối ứng · Signal: hướng NFP surprise; filter surprise >0.5σ · Trade: vào 14:30 GMT chiều Friday theo hướng, flat trước close 20:30 GMT · Risk: profit-taking muộn Friday đảo chiều · Data: NFP surprise + M30 bars · Coupling: skip khi có Fed speaker 15:00 ET.

**S46 — Turn-of-month flow effect (E)**
Hypothesis: ngày đầu tháng có salary/pension/rebalance flows ở EA (EUR-denominated) tạo bidBias nhẹ; thống kê turn-of-month nổi tiếng equity lan sang FX USD-leg · Signal: 4 phiên quanh month-turn, bias = sign của tháng trước (continuation) — kiểm mỗi năm · Trade: nhỏ size, combined với S43 logic trái chiều? Không — giữ riêng sleeve, hold ≤4 phiên · Risk: effect yếu, bị phí ăn; chỉ đáng với size vol-target · Data: daily closes 20 năm · Coupling: bật sleeve chỉ khi S38 cost-check qua.

**S47 — Summer-chop regime switch (E)**
Hypothesis: Jul–Aug thanh khoản mỏng làm EURUSD range; Sep–Nov data-heavy tái lập trend — cấu trúc mùa tự nhiên của policy year · Signal: lịch: 01-Jul→15-Aug chạy MR sleeves; sau Jackson Hole chuyển trend sleeves · Trade: chuyển trọng số sleeve theo mùa, không entry riêng · Risk: năm có shock mùa hè (2026 Middle East) break pattern · Data: calendar · Coupling: dùng làm meta-gate cho S13/S2.

**S48 — Holiday thin-liquidity fade (E)**
Hypothesis: giữa Christmas–NewYear, moves không có backing flow → hoàn trả January · Signal: |move| tuần lễ giữa holidays >1.5×ATR mùa-vụ-mảnh (per weekday count) mà không có event thật · Trade: fade nhẹ, giữ tới tuần đầu January, stop 2×thin-ATR · Risk: genuine shock đúng dịp (rẻ nhưng có) · Data: D bars + holiday calendar · Coupling: dầu không spike mới fade.

**S49 — ECB-time microstructure (E)**
Hypothesis: 13:45 CET statement + 14:45 presser có footprint: statement-spike thường bị presser đảo một phần — fade mid-window có edge thống kê · Signal: statement move >0.8×ATR(H1) trong 2 phút đầu · Trade: fade 30–50% move tại 14:30 CET window, flat trước Q&A dài · Risk: year có real surprise (2026 đang là năm đó — use smaller size) · Data: M1 quanh ECB dates, lịch · Coupling: skip ECB có projections quarter (Mar/Jun/Sep/Dec) vì noise lớn hơn.

**S50 — H2 USD seasonality conditioning (E)**
Hypothesis: lịch sử USD có xu hướng mạnh hơn nửa sau năm (hedging/funding year-end) — tài liệu không chắc chắn **(cần kiểm chứng bằng stats riêng)** · Signal: nếu đã verify: bias theo hướng USD-strong H2 làm gate cho S1; chưa verify: chỉ log không trade · Trade: meta-bias ±, size 0.5 bình thường · Risk: seasonality yếu & regime-dependent, dễ overfit · Data: 25 năm daily · Coupling: không dùng standalone bao giờ.

### Family F — Event/Data-driven (S51–S60)
*Phân biệt cơ chế: S51/S56 chỉ số/leading indicator tổng hợp; S52/S53 relative surprise trong ngày; S54/S55 kênh CB trực tiếp; S57–S60 kênh gián tiếp qua positioning/oil/funding/speech.*

**S51 — Macro surprise differential index (F)**
Hypothesis: dòng surprise data hai bên (CITI-style economic surprise EA vs US) là state variable tốt nhất của growth-differential — FX lag nó vài tuần khi pivot · Signal: EWMA 3M surprise diff (US−EA) vượt ±1σ và slope cùng dấu 4 tuần · Trade: vào hướng (US surprise mạnh hơn → short EURUSD), trail 4 tuần, rebalance theo weekly index · Risk: data revision đổi index ex-post · Data: surprise indices hai bên (hoặc tự build từ releases vs consensus) · Coupling: cùng dấu slope 2Y diff thì full size.

**S52 — Flash-PMI same-day relative surprise (F)**
Hypothesis: EA flash & US flash PMI ra cùng sáng — relative surprise là cú growth-differential sạch nhất tháng, market thường underreact composite vì nhìn từng số · Signal: Δ(EA composite surprise) − Δ(US composite surprise) vượt ±0.5 điểm · Trade: vào 5–15 phút sau cả hai release (khi spread hết nở), giữ đến NY close hoặc 2 ngày nếu >1 điểm · Risk: một trong hai bị delay/revise · Data: PMI calendar + consensus · Coupling: nếu chiều surprise cùng hướng với 20d momentum → giữ 2 ngày thay vì 1.

**S53 — HICP surprise magnitude rule (F)**
Hypothesis: surprise HICP core lớn (>1σ surprise history) tiếp tục được follow vài ngày vì repricing ECB path chậm; surprise nhỏ bị fade · Signal: |core surprise z|≥1 → continuation chiều surprise 3 phiên; z<0.5 → fade phiá spike ngày · Trade: hai rule rời rạc, size theo z · Risk: FOMC rơi vào cùng tuần lấn át ECB pricing · Data: HICP flash + consensUs history · Coupling: không có FOMC ±2 ngày.

**S54 — FOMC dots joint repricing (F)**
Hypothesis: EURUSD phản ứng FOMC chủ yếu qua dots/statement relative với OIS prior; đo đúng prior thì residual move là info thật và drift tiếp · Signal: Δ(median dot end-year) vs_prior + Δ(OIS 1Y) → combined repricing score · Trade: hướng score score>+10bp → short EURUSD từ H+1, giữ 10–20 phiên · Risk: presser đảo tone (đã ship một phần vào score? — score gồm cả statement-based OIS nên ít bị) · Data: dots history, OIS quanh meetings · Coupling: ECB response 1–4 tuần sau (ping-pong) là invalidation cứng.

**S55 — ECB presser language NLP (F)**
Hypothesis: word-count hawkish/dovish ("vigilant", "determination", "data-dependent"…) của Lagarde presser shift market khi statement neutral — đo được bằng text diff so với kỳ trước · Signal: Δhawkish-score ≥2σ lịch sử · Trade: vào 2 phút sau câu quote quyết định (first 10 min presser), giữ tới cuối ngày · Risk: NLP score noise trên các từ mới (war-related vocabulary 2026) · Data: transcript/LIVE text, từ điển score tự build · Coupling: chỉ khi statement không tạo surprise riêng (tách thông tin).

**S56 — German factory orders early-cycle lead (F)**
Hypothesis: orders là leading indicator EA cycle 1–2 quý; surprise lớn của orders tiên tri chuỗi PMI/IP sau đó → EUR drift dài hơn market pricing ngày · Signal: orders m/m surprise >+1σ hai tháng trong ba tháng · Trade: bias long EURUSD 4–8 tuần với size nhỏ, stop theo 2×ATR(D) · Risk: orders volatile/chuẩn bị lại; war regime cắt chu kỳ · Data: Destatis releases + consensus · Coupling: ZEW/Ifo tuần sau confirm cùng chiều thì add.

**S57 — Pre-event positioning squeeze fade (F)**
Hypothesis: positioning cực đoan vào trước FOMC/ECB khiến phản ứng giá bất đối xứng: surprise ngược phía crowding bị amplify, surprise cùng phía bị chặn — trade phía ngược crowd an toàn hơn thống kê · Signal: COT spec net percentile >85 (hoặc <15) trong tuần có CB meeting · Trade: đứng ngoài release; vào 30' sau theo hướng giải tighten (ngược crowd) nếu price break pre-event range · Risk: crowd đúng và freight tiếp · Data: COT, calendar · Coupling: RR skew cùng phía crowd xác nhận thêm.

**S58 — OPEC+/oil-spike ToT proxy (F)**
Hypothesis: supply-driven oil spike (OPEC+ cut, Middle East) đánh EUR qua ToT với lag giờ–ngày trong khi USD nhận bid inflation — kênh 2026 chủ đạo · Signal: Brent 1-day >+4% do supply news (phân loại theo newswire) · Trade: short EURUSD 30' sau oil spike xác nhận (không fade), giữ 3–5 phiên, stop 1.5×ATR(D) · Risk: spike do demand-hope (risk-on) thì chiều EUR dương lại · Data: Brent intraday + news tag supply/demand · Coupling: TTF cùng spike mới xác nhận EA channel (S63).

**S59 — Treasury refunding term-premium trade (F)**
Hypothesis: refunding statement tăng coupon size bất ngờ → term premium UST lên → USD mạnh → EURUSD xuống, với drift vài ngày vì index như ý parsing chậm · Signal: refunding quarterly + surprise tăng size (vs panel consensus) · Trade: short EURUSD cuối ngày refunding, giữ 5 phiên · Risk: risk-off đồng thời làm EUR được haven bid giảm hiệu lực kênh · Data: refunding calendar + size consensus · Coupling: VIX không spike quá 15% baseline.

**S60 — Speaker-cluster communication cycle (F)**
Hypothesis: các tuần trước FOMC/ECB có "chorus" speakers đồng điệu hóa expectations — EURUSD trend theo hướng chorus nhưng chỉ những tuần đủ mật độ speakers · Signal: ≥4 speakers/một CB trong 5 phiên với tone đồng nhất (score word) · Trade: bias theo tone, hold đến meeting, flat trước decision day · Risk: dissent công khai làm chorus giả · Data: speaker calendar + NLP score · Coupling: data trong blackout-inverse — blackout week thì tín hiệu tự tắt.

### Family G — Cross-asset/Correlation (S61–S70)
*Phân biệt cơ chế: S61/S65/S66 residual/filter regime; S62/S63 kênh năng lượng; S64 lead-lag intraday; S67/S70 phân rã cross để tách driver; S68/S69 bloc growth/equity flows.*

**S61 — USD-basket residual reversion (G)**
Hypothesis: phần variance EURUSD không giải thích được bởi anti-USD basket chung là idiosyncratic EUR (hoặc noise) và hoàn trả về đường regression trong vài phiên · Signal: regress daily returns lên basket {GBPUSD, AUDUSD, NZDUSD, −USDJPY, −USDCAD, −USDCHF}; residual z(20d)>2 · Trade: fade residual, target z=0.3, stop z=3, holding ≤10 phiên · Risk:EUR-specific structural news (fragmentation event) làm residual mới thành trend · Data: 7 pairs daily · Coupling: BTP-Bund không nở mạnh (fragmentation gate).

**S62 — Brent 3-day lead-lag ToT (G)**
Hypothesis: EUR phản ứng oil với lag vì hedging/psychology chậm; 3-day oil trend supply-driven tiên tri EUR 1–3 ngày · Signal: Brent 3d return ±3% + tag supply; vào EURUSD ngược dầu hôm sau giờ London · Trade: hold tới oil flatten 2 phiên; stop 1.2×ATR(D) · Risk: oil–USD correlation đảo (dollar-driven oil) — phải tag được nguyên nhân · Data: Brent daily + news tag · Coupling: WTI cùng hướng Brent (không phải spread trade US) mới vào.

**S63 — TTF–Henry Hub EA-energy shock (G)**
Hypothesis: chênh TTF vs HH là thước ToT EA-thứ thiệt; z>2 của spread là EUR pain idiosyncratic không bị USD factor giải thích · Signal: (TTF−HH) 20d z-score >2 · Trade: short EURUSD kèm long USDCAD hedge nhỏ (chia oil-beta), stop khi z<1, target z về 0.5 · Risk: LNG normalization nhanh (cấu trúc supply 2026 đã khác 2022) · Data: TTF, HH daily · Coupling: skip nếu BTP-Bund cũng nở (fragmentation trùng — chọn 1 kênh).

**S64 — Bund–UST 10Y intraday lead-lag (G)**
Hypothesis: trong data windows, yield spread 10Y dẫn EURUSD 5–30 phút vì rates desks định giá trước FX desks trung bình · Signal: |Δ10Y spread| >3bp trong 15' post-data; vào EURUSD theo hướng spread (spread rộng hơn → short EURUSD) sau 5–10 phút nếu FX chưa đi · Trade: scalp 30–60 phút, stop 0.5×ATR(H1) · Risk: HFT đã ăn phần lớn edge ở mốc giây — edge còn lại ở mốc 10' và chỉ tại data windows · Data: 10Y yields realtime, EURUSD M5 · Coupling: chỉ chạy 60 phút quanh US releases.

**S65 — Gold anti-USD confirmation filter (G)**
Hypothesis: move USD-wide thật cần gold xác nhận (gold ngược USD); EURUSD break không có gold confirm là EUR-specific — xác suất continuation khác nhau hẳn · Signal: EURUSD phá 20d high MÀ gold không phá 20d high tương ứng · Trade: dùng như filter giảm size 50% cho mọi breakout sleeve (S2/S23/S29); không entry riêng · Risk: gold bị ETF-flow idiosyncrasy · Data: XAUUSD daily · Coupling: mặc định cho family A/C entries.

**S66 — VIX regime gate (G)**
Hypothesis: EURUSD có tính chất risk kép (USD haven vs EUR cyclical): VIX<18 trend anti-USD hoạt động; VIX>28 USD bid chủ đạo — hai regime cần chiều ngược nhau · Signal: VIX 20d theo hai band trên; điều hướng sleeve bias · Trade: meta-gate cho mọi sleeves: band thấp ưu longs, band cao ưu shorts, giữa = neutral · Risk: VIX spike từ sự kiện không FX-relevant (AI equity selloff kiểu 2024-25?) **(cần kiểm chứng regime gần)** · Data: VIX daily · Coupling: kết hợp DXY momentum cùng xác nhận.

**S67 — EURGBP as ECB-pure vehicle for EURUSD noise filter (G)**
Hypothesis: EURGBP tách bỏ USD leg; nếu EURGBP đi cùng hướng EURUSD thì driver là EUR — tăng conviction giữ trend; nếu ngược thì USD đang cầm lái, theo DXY thay vì EUR story · Signal: daily sign agreement của hai pair trong 5 phiên · Trade: meta-filter: agreement → full-size trend sleeve; disagreement → chỉ trade bằng USD-breadth (S6) · Risk: BoE shock làm EURGBP mất ý nghĩa vehicle · Data: EURGBP daily · Coupling: lịch BoE không có meeting ±1 tuần.

**S68 — Copper/global-growth EUR bias (G)**
Hypothesis: EUR là cyclical currency (export-heavy); copper là real-activity proxy hàng đầu — quan hệ dương bền theo chu kỳ · Signal: copper 63d momentum percentile >70 (hoặc <30) · Trade: bias long/short EURUSD multi-week, size vol-target, stop theo copper reversal ±1σ · Risk: war regime: copper down + EUR down + USD up — quan hệ đảo tạm (2026) · Data: HG copper daily **(ngoài universe — bổ sung nếu được phép; nếu không dùng proxy XAG industrial)** · Coupling: PMI composite EA cùng dấu thì giữ.

**S69 — SX5E vs SPX relative equity performance (G)**
Hypothesis: dòng vốn equity quốc tế theo relative performance; 8–12 tuần lệch có hệ số ra vào EURUSD qua rebalancing & sentiment · Signal: 8w relative return (SX5E−SPX, currency-hedged nếu có) vượt ±3% · Trade: vào hướng outperformer's currency (EA mạnh → long EURUSD), rebalance tháng · Risk: hedged-returns vs unhedged khác nhau (đa số US flow đã hedge) — dùng hedged nếu lấy được · Data: hai index + hedged series nếu có · Coupling: S44 cùng dấu mạnh thì tăng size (flow hệ thống hóa).

**S70 — EURJPY × USDJPY decomposition (G)**
Hypothesis: EURUSD = EURJPY/USDJPY; phân rã giúp biết move hiện tại từ risk appetite (EURJPY) hay rates (USDJPY) — continuation probability khác nhau · Signal: ngày move: nếu EURJPY dẫn (risk channel) thì EURUSD move cần VIX xác nhận; nếu USDJPY dẫn (rates) thì cần 2Y diff xác nhận · Trade: filter condition-continuation cho intraday trend; nếu driver không xác nhận → chốt sớm hơn bình thường · Risk: phân rã correlations tại flash events · Data: 3 pairs M15 + VIX + yields · Coupling: dùng chung với S41.

### Family H — Positioning/Flows (S71–S80)
*Phân biệt cơ chế: S71/S74/S75 contrarian extremes; S72/S73/S77 confirmation flows; S76/S79 mechanical flow calendar; S78/S80 structural/risk overlay.*

**S71 — COT leveraged-funds extreme contrarian (H)**
Hypothesis: spec net 6E ở percentile cực (top/bottom 5%/95%) phản ánhCrowding; price thường đảo trong 2–6 tuần khi flow đảo chiều phải giải phòng · Signal: COT Friday release: net spec percentile 95 ngày giao dịch ≤5% hoặc ≥95% + price divergence 3 tuần (new price extreme không kèm new positioning extreme) · Trade: vào ngược crowd size nhỏ, stop khi percentile breakout tiếp, target phân vị 50 · Risk: freight train giữ extreme 6+ tháng (2022) · Data: COT 6E history · Coupling: RR skew cùng phía extreme (S75) thì chờ thêm 1 confirmation candle W.

**S72 — COT 4-week change momentum confirm (H)**
Hypothesis: thay đổi tốc độ positioning là đồng thuận flow mới; price trend kèm COT change cùng chiều có continuation tốt hơn trend không có flow back · Signal: Δnet spec 4 tuần >+1σ lịch sử cùng hướng trend EMA50 · Trade: cho phép trend sleeves (S1/S7) tăng size 1.5× khi confirm; không entry riêng · Risk: COT delay (Tuesday→Friday) + chỉ một slice thị trường · Data: COT · Coupling: OI 6E cùng tăng (S73) là bộ confirm đầy đủ.

**S73 — 6E OI + price breakout confirmation (H)**
Hypothesis: breakout có OI tăng = vị thế mới thật; breakout OI giảm = short-covering hết linh hoạt, hay fail · Signal: daily breakout 20d range; OI CME tăng >3 ngày liên tiếp quanh breakout · Trade: vào breakout thứ 2 ngày khi OI confirm, stop dưới breakout day low · Risk: OI data delay intraday — dùng OI ước lượng sơ bộ của exchange · Data: 6E OI daily · Coupling: roll tuần phải exclude (OI cơ học thay đổi).

**S74 — Retail-sentiment contrarian (H)**
Hypothesis: retail positioning ratio (broker-published) là crowd-noise indicator; cực >65% một phía có giá trị fade nhỏ nhưng ổn định ở EURUSD vì depth retail lớn nhất · Signal: sentiment ratio ≥65% long (fade short) hoặc ≤35% (fade long) + price trong range 20 ngày (không freight) · Trade: nhẹ, target 1.5×ATR(D), stop 2×ATR(D) · Risk: trend mạnh crowd đúng — gate range bắt buộc · Data: broker sentiment feed · Coupling: COT không extreme cùng phía retail (spec thường ngược retail).

**S75 — 25-delta risk-reversal extreme (H)**
Hypothesis: RR skew đo demand tail-hedge; extreme EUR-put skew là fear marker — historically fade khi fear không có nền structural, confirm khi có (phân biệt bằng BTP-Bund) · Signal: 25d RR z(1Y) <−2 (put-skew cực) · Trade: nếu BTP-Bund bình thường: long EURUSD; nếu fragmentation đang nở: đi theo skew (short) · Risk: hai regime lẫn — điều kiện BTP là bắt buộc · Data: RR quotes, BTP-Bund · Coupling: dùng cùng COT (S71) tăng conviction.

**S76 — Option-expiry pinning & puncture (H)**
Hypothesis: strikes lớn (≥500M EUR) ở 10am NY cut tạo dealer hedging gravity (pin) cho tới khi hết, rồi price puncture giải phóng — cả hai đều quantifiable quanh expiry clock · Signal: strike report sáng; giá trong 15 pip strike sau 07:00 NY và vol thực tắt dần → pin; sau 10:00 giá xuyên strike kèm vol → puncture continuation · Trade: pin: fade về strike từ rìa 20 pip; puncture: theo chiều xuyên, giữ tới NY close · Risk: expiry bị rolling (chủ position roll strike) không pin · Data: morning expiry reports, M15 · Coupling: 2 nút rule — không trade ngược chiều slope 2Y diff ngày đó.

**S77 — London-open order-flow delta continuation (H)**
Hypothesis: imbalances đầu phiên London (aggressor delta M5 tổng hợp) là proxyinstitutional direction của ngày; continuation có edge tới NY open · Signal: cumulative delta 07:00–08:00 GMT >+1.5σ 20 ngày cùng chiều break Asian range · Trade: theo chiều delta, stop dưới Asian extreme, flat 16:00 GMT nếu chưa hit target · Risk: delta từ một masking parent order (twap) không có info · Data: tick delta từ feed có depth-tag · Coupling: skip nếu German data 07:00–08:00 (delta méo bởi release).

**S78 — COFER reserve-share structural bias (H)**
Hypothesis: USD share dự trữ toàn cầu (COFER quarterly) là dòng structural dài hạn cho USD cycle đa năm; EURUSD trend lớn đi kèm — bias quý, không phải entry · Signal: USD share downtrend 4 quý liên tiếp (−1pp+) → structural long bias EURUSD sleeves · Trade: meta-allocator: skew weight các sleeve long khi trend COFER thuận chiều · Risk: dữ liệu quý, lag 3 tháng; regimenge nhỏ · Data: IMF COFER **(cần kiểm chứng bản quarterly mới nhất)** · Coupling: dùng cùng S40 term-premium làm "slow pair".

**S79 — Currency-ETF AUM flow momentum (H)**
Hypothesis: AUM change của FX ETF (EUR-hedge products) là retail-aggregate flow observable hàng tuần, đi sau smart money — dùng làm fade-timing phụ trợ · Signal: 4-week AUM %change >+2σ vào đúng lúc price stall (không new high cùng tuần) · Trade: fade theo combo trên, nhẹ, horizon 2 tuần · Risk: AUM change từ performance chứ không flow (phải adjust) · Data: ETF AUM weekly · Coupling: chỉ khi COT spec cũng đã extreme (double-crowd).

**S80 — Crowding + basis-stress squeeze exit overlay (H)**
Hypothesis: vị thế crowd + funding stress (basis) + vol bật là công thức squeeze; overlay này không tạo entry mà buộc exit/thắt stop đúng lúc · Signal: COT extreme + |x-ccy basis 1M Δ| >2σ + 1M implied vol 3-day change >20% · Trade: mọi positions ngược hướng crowd: cắt nửa + stop về BE; không mở mới · Risk: false alarm tốn cơ hội một phần · Data: COT, basis, vol surface · Coupling: là risk-overlay toàn program cho EURUSD lane.

### Family I — Pattern/Pairs/Stat-arb (S81–S90)
*Phân biệt cơ chế: S81/S82/S90 band giữa các cross có driver policy/sentiment riêng; S83/S84/S89 phân rã triangular/lead-lag; S85/S86/S87 statistical regime; S88 pattern có điều kiện.*

**S81 — EURGBP policy-drift band trade (I)**
Hypothesis: EURGBP mean-revert quanh đường trượt theo 2Y (UK−EA) swap diff; band quanh drift-line là stat-arb có nền tảng policy · Signal: spread EURGBP − β·(2Y swap diff) vượt ±2σ(60d) · Trade: fade về drift-line, stop 2.8σ, size theo half-life ước lượng · Risk: BoE/ECB divergence bùng nhanh (2022-style) phá cointegration · Data: EURGBP, swaps · Coupling: gate lịch BoE+ECB ±2 tuần cảnh báo cao.

**S82 — EURCHF haven-spike fade (I)**
Hypothesis: CHF haven premium trong stress spike rồi decay khi stress không escalated — EURCHF V-revert; dùng làm vehicle EUR-sentiment thay vì can thẳng khi USD đang loạn · Signal: EURCHF 1-day drop >1.5×ATR do geopolitics, SNB không can thiệp · Trade: long EURCHF (tức long EUR sentiment) 2–5 phiên, stop dưới spike low, target 50% retracement · Risk: escalation thật (2026 Iran — cẩn thận) · Data: EURCHF + news tag · Coupling: oil không tiếp tục spike mới cùng ngày.

**S83 — Triangular consistency monitor (I)**
Hypothesis: EURUSD vs EURGBP×GBPUSD deviation là check arbitrage mechanical; ở mốc sub-second bị HFT ăn sạch nhưng ở mốc 5–15 phút vẫn lộ execution-gap khi tin number hai bên lệch giờ · Signal: log deviation >2 pip kéo dài >10 phút · Trade: fade bên mắc lỗi (pair lagging release) khi release schedule bất đối xứng (UK data 09:30 GMT vs EA 10:00) · Risk: gần-zero edge sau cost; giữ như monitoring/sanity check sleeve · Data: 3 pairs realtime · Coupling: dùng để quyết định pair nào thể hiện view tốt nhất hôm đó.

**S84 — Cross-decomposition continuation filter (I)**
Hypothesis: move EURUSD có EURGBP xác nhận (cùng hướng) là EUR-driver → continuation khi driver còn đó; không confirm → USD-driver, continuation phụ thuộc DXY breadth · Signal: 1h move EURUSD kèm EURGBP same-sign ≥0.4× scale · Trade: continuation trades chỉ khi decomposition rõ ràng; filter cho S21/S41 · Risk: 3-currency confounding tại flash moves · Data: 3 pairs realtime · Coupling: intrinsic với family C/E sleeves.

**S85 — Kalman dynamic-hedge synthetic deviation (I)**
Hypothesis: hedge-ratio EURUSD vs basket anti-USD trôi chậm (policy weights đổi); Kalman filter bắt ratio theo thời gian thực tốt hơn OLS tĩnh — deviation trade nổi bật quanh regime turn · Signal: Kalman residual vượt adaptive ±2.5σ · Trade: fade residual với holding theo half-life Kalman implicit · Risk: filter lag đúng lúc structural break (2015-style) · Data: 7 pairs, Kalman engine · Coupling: same fragmentation gate như S61.

**S86 — Hurst regime switch selector (I)**
Hypothesis: EURUSD luân phiên persistent/anti-persistent; Hurst 100-ngày phân loại regime và chọn sleeve đúng (trend khi H>0.55, MR khi H<0.45, flat giữa) — meta-strategy giảm giao thoa sleeves trái chiều · Signal: rolling H estimate bootstrap CI hẹp đủ tin · Trade: allocator; mỗi sleeve giữ rule riêng · Risk: H estimate noise ở short window; đổi regime giữa đường · Data: daily closes · Coupling: chỉ switch khi CI không chứa 0.5 hai tuần liên tiếp.

**S87 — Flow-adjusted momentum (I)**
Hypothesis: month-end/fix days làm méo momentum calculation; strip những ngày đó ra trước khi tính signal thì momentum sạch hơn cho mọi sleeve dùng nó · Signal: momentum series xây trên excluded-calendar days · Trade: không entry riêng — feed cho S1/S3/S6 · Risk: lọc quá mức mất info những ngày quan trọng (CB days KHÔNG được strip) · Data: calendar + closes · Coupling: giữ CB/data days trong tập.

**S88 — Conditional chart-pattern statistics (I)**
Hypothesis: pattern (flag, H&S, double top) không có edge trung bình nhưng có edge có điều kiện: chỉ sau event-vol window và tại level có story (round/expiry/200dma) — backtest có điều kiện mới không overfit · Signal: pattern detect + điều kiện (3 phiên sau data ≥1σ surprise + level confluence) · Trade: theo pattern breakout với stop cấu trúc · Risk: pattern library quá rộng → multiple-testing trap; giới hạn 3 pattern chuẩn · Data: OHLC + surprise history + levels · Coupling: buộc đủ 2/3 điều kiện.

**S89 — GBPUSD lead-lag filter in London (I)**
Hypothesis: có những phút London mà GBPUSD phản ứng tin Anh/trung chuyển trước EURUSD vài chục giây–2 phút (cross-venue sama maker); dùng làm early filter giảm lag entry EURUSD · Signal: GBPUSD impulse ≥1.5×M1 ATR không do EURUSD-lead · Trade: filter timing cho scalping sleeves; nếu impulse GBP mang GBP-idiosyncrasy (BoE headline) thì bỏ · Risk: inverted causality thực tế · Data: M1 hai pair + news tag · Coupling: chỉ London hours.

**S90 — EUR vs commodity-bloc divergence (EURAUD band) (I)**
Hypothesis: EURAUD gói growth-quality divergence (EA export quality vs China-commodity cycle); spread quanh drift theo relative PMI; vượt band là những pha global-growth re-rate mà EURUSD trade có hệ số theo · Signal: EURAUD deviation từ PMI-implied trend ±2σ · Trade: band fade EURAUD + chuyển bias tương ứng cho EURUSD (risk-regime positioning) · Risk: China hard-landing event phá vỡ quan hệ · Data: EURAUD, PMI hai bloc · Coupling: copper/XAG confirm growth direction (S68).

### Family J — Regime-conditioned/Options-flavored (S91–S100)
*Phân biệt cơ chế: S91–S95 vol/smile làm gate hoặc cấu trúc premium; S96/S76-level flows từ options; S97/S98/S100 state model toàn cục; S99 stack khủng hoảng chuyên dụng regime 2026.*

**S91 — Vol-percentile regime gate (J)**
Hypothesis: trend sleeve chỉ hoạt động 20–80 percentile realized vol; ngoài hai đầu (chop chết / chaos stop-hunt) → off; gate này tăng Sharpe trung bình của mọi trend sleeve vì tránh hai đuôi xấu · Signal: 20d realized vol percentile rolling · Trade: allocator: pct<20 hoặc >80 → flat trend sleeve, bật MR trong pct<20 · Risk: đứng ngoài chính đúng month đầu freight (2022-01) · Data: OHLC + vol calc · Coupling: default gate cho family A.

**S92 — Vol term-structure inversion event radar (J)**
Hypothesis: 1w/1M implied inverted = market anticipate event trong tuần; tuần pre-event có drift về hướng được hedge (skew) rồi kick — playbook: stand-aside pre, drift post · Signal: 1w−1M implied <0 kèm |RR 1w| cao · Trade: flat trước event; post-event vào hướng kick sau 30' nếu OIS prior bị bất ngờ (kết S35) · Risk: anticipation sai hướng · Data: implied vol surface 2 mốc + RR · Coupling: dùng cho FOMC/ECB/CPI weeks.

**S93 — Risk-reversal slope slow-trend confirm (J)**
Hypothesis: dRR/dt (thay đổi skew 3 tháng) là proxy positioning-weighted expectations chậm; trend EURUSD phù hợp dRR cùng chiều có xác suất sống cao hơn — giống S75 nhưng là dạng confirm-theo-thời-gian, không phải extreme · Signal: 3M change của 3M RR cùng dấu trend EMA100 · Trade: size multiplier cho S1/S3; không entry riêng · Risk: skew bị quarterly hedging flows cơ học · Data: RR time series · Coupling: loại 2 tuần quanh quarter-end.

**S94 — Butterfly smile rich/cheap kurtosis bias (J)**
Hypothesis: butterfly (25d) đắt = tails được giá cao = market chờ jump → mean-reversion sleeve trong khi strangle-selling logic tăng edge; butterfly rẻ = calm complacency → breakout sleeves tốt hơn · Signal: 25d fly z(1Y) ±1.5 · Trade: allocator: fly expensive → MR bias; cheap → breakout bias · Risk: model vol surface đơn giản miss sticky-strike effects · Data: vol surface · Coupling: kết hợp S86 Hurst như double-confirm.

**S95 — Event-week gamma calendar (J)**
Hypothesis: term structure của implied vol dốc quanh event; mua tuần-có-event bán tuần-sau (long gamma event, short vega sau) capture premium mispricing có cấu trúc · Signal: event weeks (FOMC/ECB/CPI) với term slope >median lịch sử · Trade: structure trên options (hoặc proxy bằng straddle-style breakout S22 hai tuần khác nhau); thay vì directional · Risk: event dud → long gamma mất 2 lần; sizing nhỏ · Data: options quotes cả hai expiry · Coupling: chỉ khi surprise-history của event đó có σ>0 (không phải "dead" data).

**S96 — Barrier-defense fade at exotic walls (J)**
Hypothesis: exotic barriers/knock-outs lớn (khách hàng corporate) tạo defense flow giữ giá dưới/above strike tới expiry rồi thả — fade về phía safe của strike khi nhận diện được wall · Signal: persistent capping pattern tại level đẹp + dealer chatter/report về barriers · Trade: fade approach trong 30 pip phía unsafe, stop 12 pip ngoài strike, exit trước expiry 4h · Risk: wall giả (không có thật options) — cần nhiều lần test level · Data: expiry/barrier reports, M15 · Coupling: kết hợp S76 cùng strike trùng tăng conviction.

**S97 — Markov regime-switching allocator (J)**
Hypothesis: hai-state (trend/MR) hidden Markov theo return+vol nắm bắt phần lớn cấu trúc EURUSD; allocation theo smoothed probabilities tốt hơn static sleeves · Signal: HMM 2-state fit rolling 3 năm, P(trend)>0.6 → trọng số trend · Trade: allocator chỉ; mỗi sleeve giữ rule gốc · Risk: overfit số state; cần locked spec trước backtest · Data: daily returns, realized vol · Coupling: state phải nhất quán với S86 Hurst (cross-check).

**S98 — Growth×inflation differential quadrant (J)**
Hypothesis: phân lớp (growth diff US−EA, inflation diff US−EA) thành 4 quadrant; mỗi quadrant có hệ số EURUSD bias và sleeve ưu tiên khác nhau — macro clock của lane · Signal: quarterly PCA/momentum trên PMI diff và core CPI diff · Trade: bias allocation theo quadrant; e.g. US-hot/EA-cool → short bias + carry sleeve mạnh · Risk: quadrant đổi chậm trễ 1 quý · Data: PMI, CPI hai bên · Coupling: dùng cho top-level sizing mọi families.

**S99 — Crisis-alpha short: war-shock stack (J)**
Hypothesis: khi geopolitical/energy shock chồng USD-bid và EUR ToT-hit (chính regime 09-2026), short EURUSD có hai tailwinds trừ phi ECB hawkish-catch-up lấn át — bộ ba điều kiện xác định stay/exit · Signal: (oil 20d z>1.5) AND (VIX>22) AND (TTF−HH z>1.5); exit khi ECB repricing (OIS EA 1Y Δ>+25bp trong 2 tuần) · Trade: short size vol-target, stop 2×ATR(D), partial profit 1.5R · Risk: peace headlines gap (cover một phần trước weekend) · Data: oil, TTF, VIX, OIS · Coupling: tối đa 1 add; weekend-flat rule khiMiddle East headline hot.

**S100 — Policy-cycle clock conditioning (J)**
Hypothesis: hành vi EURUSD phụ thuộc trạng thái (Fed, ECB) ∈ {hike, hold, cut} — 9 tổ hợp; mỗi tổ hợp chọn sleeve + direction bias khác nhau; 2026-09 đang ở (hike, hike) với energy overlay → carry short + surprise-drift sleeves mạnh, trend sleeve chỉ khi differential slope rõ · Signal: phân loại state từ OIS forward path mỗi kỳ meeting; chuyển state = portfolio rebalance · Trade: meta-allocator toàn lane · Risk: mis-classification tại transition blur (dot vs speech) · Data: OIS forwards, meeting minutes · Coupling: là parent gate của S3/S31/S91/S98 — mọi sleeve cuối cùng đều đọc state này.

---

## 3. Tổng hợp cho symbol

### 3.1 Top-10 ideas nền tảng kinh tế mạnh nhất

1. **S1 Policy-divergence trend lock** — cơ chế đầu tiên của pair này kể từ 1999; rate differential là driver có lý thuyết rõ nhất (UIP thất bại nhưng directionally mạnh ở regime divergence lớn).
2. **S31 Classic carry short (với S38/S100 gates)** — 137bp differential hiện tại + short carry dương; kinh tế học carry (risk premium) thuyết phục nhất khi hai CB lệch pha rõ.
3. **S35 Hawkish-surprise drift** — post-policy surprise drift là một trong những regularities vững nhất của macro FX (underreaction có tài liệu); đo surprise bằng OIS prior chứ không phải consensus headline.
4. **S51 Surprise differential index** — growth-differential là bộ xương của mọi mô hình fair-value FX (PPP catch-up + surprise momentum); index dạng CITI-style có tính tiên lượng vài tuần.
5. **S54 FOMC dots joint repricing** — dots là channel có cấu trúc nhất của USD; đo prior qua OIS tránh nhầm "hawkish headline" đã priced.
6. **S62 Brent lead-lag ToT** — kênh riêng của EUR (net energy importer), đã validate 2022 và đang chạy lại 2026; điều kiện tag supply-vs-demand là linh hồn của ý.
7. **S63 TTF–Henry Hub spread** — thước EA-energy pain idiosyncratic sạch nhất có thể xây từ universe; không symbol USD-major nào có signal riêng biệt thế này.
8. **S43 Month-end WM/R fix imbalance** — flow mechanism xác thực (fix có documentation công khai), edge nhỏ nhưng đều; hệ số predictive từ returns differential.
9. **S71 COT extreme contrarian** — positioning data công khai 20+ năm, cơ chế unwind crowd rõ ràng; cần gate divergence để tránh freight-train death.
10. **S100 Policy-cycle clock** — meta-conditioning biến 9 tổ hợp policy state thành bộ lựa chọn sleeve; chính là cách dùng "2026-09 = both-hiking + energy shock" một cách hệ thống thay vì ad-hoc.

**Bảng triển khai nhanh top-10 (idea → data cốt lõi → gate bắt buộc)**

| Idea | Data cốt lõi | Gate bắt buộc |
|---|---|---|
| S1 | 2Y yields hai nước + OHLC D | slope differential cùng dấu giá |
| S31+S38 | forward points, broker markup, ATR | S100 quadrant + carry-viability ratio >0.5 |
| S35 | OIS quanh meeting + calendar | surprise đo vs OIS prior, không phải consensus |
| S51 | surprise index hai bên (EWMA 3M) | slope cùng dấu 4 tuần |
| S54 | dots history + OIS prior | ECB response window = invalidation cứng |
| S62 | Brent + news tag supply/demand | WTI cùng hướng; TTF xác nhận kênh EA |
| S63 | TTF, Henry Hub daily | fragmentation gate (BTP-Bund không nở) |
| S43 | fix calendar + returns differential tháng | ngày LNBU cuối tháng, quarterly size x2 |
| S71 | COT 6E percentile + price | price-positioning divergence 3 tuần |
| S100 | OIS forwards + minutes | parent gate — mọi sleeve đọc state này |

### 3.2 Bẫy overfitting đặc thù khi backtest EURUSD

- **DST & broker time**: session boundaries dịch 2 lần/năm; US/EU DST lệch nhau 2–3 tuần (Mar & Oct–Nov) làm khung "London open" trượt; broker server GMT+2/+3 làm daily candle đổi giờ — mọi session idea (E) phải tái sinh theo calendar chứ không hardcode giờ tĩnh.
- **Cost model**: spread sub-pip khiến nhiều scalping/MR ideas chỉ âm nhẹ — phải dùng spread realistic theo giờ + commission + swap (Wednesday 3x; hiện short +~137bp/yr gross trừ markup) — kể cả idea long-holding cũng phải qua swap.
- **6E continuous contracts**: back-adjust khi test futures-based (S73/S72); roll yield 137bp/yr sẽ fake ra PnL nếu dùng unadjusted.
- **Event windows**: không model spread nở + slippage quanh NFP/FOMC thì mọi stop trong event window là fiction; hoặc loại event bars hoặc model riêng (S22/S30 logic).
- **Look-ahead**: COT (data Tue, release Fri 15:30 ET), OIS prior (phải dùng info trước meeting), surprise vs whisper (whisper không observable — dùng consensus công bố + OIS thay thế), COFER (lag 3 tháng), expiry reports (dùng đúng buổi sáng phát hành).
- **Regime dominance**: 2014 & 2022 freight làm trend/carry sleeves trông đẹp phi lý; 2017/2019 chop làm MR đẹp phi lý — bắt buộc sub-sample theo policy-cycle quadrant (S100) và walk-forward.
- **Sample & structural breaks**: EUR chỉ tồn tại từ 1999; DEM-proxy khác structure; SNB-floor era (2011–2015) và QE-era (2015–2020) là world khác — report theo era.
- **Correlation hardcode**: mọi hệ số ở 1.5 là dạng "typical" — regime 2026 (oil + cả hai CB hike) đã làm EURUSD/USDCAD có xu hướng cùng chiều; re-measure rolling trước khi dùng family G.
- **Multiple testing**: 100 ideas trong file này — khi đưa vào backtest phải đăng ký spec trước (family, params, gates) và áp penalty thủ tục selección; đặc biệt nhóm pattern (S88) dễ chọn lọc survivor.
- **Round-number & expiry data**: levels đẹp trong backtest thường là kết quả của cùng data dùng để detect — out-of-sample theo thời gian, không theo random shuffle (shuffle phá autocorrelation của regime).
- **Trial accounting**: 100 ideas trong file này không được backtest tự do — đăng ký spec (family/params/gates) trước, một ledger trial chung cho lane, áp penalty multiple-testing khi đọc kết quả; mọi kết quả thiếu evidence ghi `NOT_RUN`, không suy ra `PASS`.
- **News-tag subjectivity**: S58/S62/S63 phụ thuộc phân loại "supply vs demand" của oil move — tag phải làm bằng rule cơ học (theo newswire nguồn cố định) nếu không sẽ leak discretion vào backtest.
- **War overlay 2026**: sample sống hiện tại có driver (Iran conflict + both-hike) chưa từng tồn tại trong history — mọi parameter fit trên 2015–2024 cần treat như khác-regime khi War-overlay ON; giữ một indicator nhị phân overlay để sub-sample.
- **Demo vs live microstructure**: spread/latency demo không đại diện — mọi idea scalping (S17/S19/S20/S77/S83/S89) phải qua cost thực đo trước khi tính edge.

### 3.3 MUST-WATCH weekly macro checklist riêng cho EURUSD

Hàng tuần (thứ Hai sáng), theo thứ tự ưu tiên:
1. **Lịch policy**: FOMC/ECB 6 tuần tới (kế tiếp ECB 29-10-2026; FOMC cuối tháng 10 **(cần kiểm chứng ngày chính xác)**), speakers hai bên, blackout weeks; Jackson Hole-type events.
2. **Data calendar hai bên**: US CPI/PCE/NFP/ISM; EA HICP flash/flash PMI (cùng ngày ~22–24); German orders/IP/Ifo/ZEW — đánh dấu các ngày "relative surprise" khả thi (S52/S53).
3. **Rates**: 2Y UST−Schatz slope & level; 10Y UST−Bund; OIS 1Y hai bên (path priced) — cập nhật state cho S100; so sánh với differential policy hiện tại 137.5bp.
4. **Energy**: Brent & TTF weekly change; **TTF−HH spread z-score** (S63); OPEC+ headlines; Middle East (Iran) escalation/de-escalation — weekend gap risk assessment (S99 weekend-flat rule).
5. **Fragmentation**: BTP-Bund & OAT-Bund 10Y weekly Δ; upcoming BTP/OAT auctions; rating agency calendar.
6. **Positioning**: COT 6E (thứ Sáu 15:30 ET) — percentile & 4-week change (S71/S72); 25d RR skew & butterfly (S75/S93/S94); option expiries notable tuần tới (S76/S96).
7. **Flows & risk**: VIX regime band (S66); x-ccy basis 1M/3M (S39/S80); WM/R month-end ước tính flow sign (S43); quarter-turn hedge rebalance nếu cuối quý (S44).
8. **Sanity cross-asset**: DXY vs EURUSD non-confirmation (S19); gold confirm (S65); EURGBP decomposition (S67) — xác định driver chủ đạo tuần trước: USD-wide, EUR-specific, energy, hay risk.
9. **Vol state**: realized vol percentile + 1w/1M term structure (S91/S92) — quyết định sleeves ON/OFF.
10. **Regime log**: ghi quadrant S98/S100 + ghi chú bất thường — journal này chính là evidence trail khi về sau soi lại vì sao sleeve thắng/thua.

**Ánh xạ checklist → top ideas (thứ tự xử lý buổi sáng thứ Hai)**

| Mục checklist | Ideas được bật/tắt |
|---|---|
| Lịch policy + OIS paths | S100 state update → S5/S35/S54 arming |
| Data calendar hai bên | S52/S53 windows đánh dấu; S51 update |
| Rates (2Y/10Y) | S1/S8 slope check; S37/S64 bias |
| Energy (Brent/TTF/HH) | S58/S62/S63/S99 stack status |
| Fragmentation (BTP) | gate cho S61/S63/S75; MR caution |
| Positioning (COT/RR/expiries) | S71/S72/S75/S76/S93/S96 |
| Flows & risk (VIX/basis/fix) | S39/S43/S44/S66/S80 |
| Cross-asset sanity (DXY/gold/EURGBP) | S19/S65/S67 driver identification |
| Vol state | S91/S92 sleeve ON/OFF |
| Regime log | evidence trail toàn lane |

---

## Phụ lục — Danh mục "(cần kiểm chứng)" hợp nhất & nguồn dữ liệu gợi ý

**Các mục time-sensitive/uncertain cần verify trước khi dùng trong backtest:**
1. BIS Triennial 2025: thị phần turnover EURUSD mới nhất (đang dùng số 2022 ~22.7%).
2. Danh tính Fed Chair hiện tại (dấu hiệu nguồn 2026 chỉ tới Warsh — chưa khẳng định).
3. Ngày FOMC cuối tháng 10-2026 (chỉ biết ECB 29-10-2026).
4. COFER quarterly mới nhất (USD share dự trữ) cho S78.
5. USD seasonality H2 (S50) — chưa có bằng chứng thống kê đã lock.
6. Nguồn hedged-equity flow cho S44/S69 (hedging survey chỉ mang tính chỉ báo).
7. Copper (HG) nằm ngoài universe 12 symbol — S68 cần phê duyệt mở rộng hoặc dùng XAG proxy.
8. Chi tiết xung đột Trung Đông/Iran 2026 (diễn biến, mức độ ảnh hưởng LNG/TTF) — chỉ verify được qua news theo thời gian thực.
9. Cơ chế "ECB raised growth forecasts" kỳ 09-2026 (Morningstar) — cần đọc staff projections gốc để hiểu driver (chiến tranh/pent-up demand?).
10. Markup swap hiện hành của broker cụ thể của program (S38/S31) — chỉ đo được khi mở tài khoản demo/real.

**Nguồn dữ liệu gợi ý theo nhóm sleeve (để chuẩn bị hạ tầng, không phải khuyến nghị vendor):**
- Rates/macro: FRED (UST), Bundesbank/ECB SDW (Schatz, BTP, OIS EA), CME FedWatch-style OIS (thay thế nội bộ).
- Positioning: CFTC COT (6E), exchange OI CME.
- Options: volatility surface/RR/fly từ vendor hoặc broker API; expiry reports từ big-dealer morning notes.
- Energy: Brent/WTI/TTF/HH — trong universe đã có Brent/WTI/NATGAS; TTF cần bổ sung.
- Calendar/surprise: lịch kinh tế chuẩn + consensus database tự build để tránh lỗi revision.
- Microstructure: tick data spot (hoặc 6E làm proxy institutional).

**Ma trận family × policy-cycle quadrant (S100) — sleeve nào sống ở state nào**

| Family | Fed cut / ECB cut | Fed cut / ECB hike | Fed hike / ECB cut | Cả hai hike (hiện tại) | Cả hai hold |
|---|---|---|---|---|---|
| A Trend | trung bình | mạnh (EUR uptrend) | mạnh (EUR downtrend) | yếu — cần slope rõ | yếu (chop) |
| B MR | mạnh | yếu | yếu | trung bình (intraday only) | mạnh |
| C Breakout | trung bình | trung bình | mạnh | trung bình quanh event | trung bình |
| D Carry | long-bias carry | mệt (diff thu hẹp) | mạnh nhất (short carry) | thu hẹp — gate chặt | trung bình |
| E Session | ổn định mọi regime (flow cấu trúc) | như nhau | như nhau | như nhau + war-headline giờ | như nhau |
| F Event | mạnh (pivot surprises) | rất mạnh | rất mạnh | rất mạnh (ping-pong) | mạnh |
| G Cross-asset | oil driver tăng quyền | TTF channel mạnh | oil+USD đồng hướng | ToT + fragmentation | gold/risk filter |
| H Positioning | ổn định mọi regime — extremes xuất hiện quanh pivot | | | | |
| I Pairs/Stat-arb | ổn định | EURGBP break risk | EURGBP break risk | break risk cao | tốt |
| J Regime | chuyển state | chuyển state | chuyển state | chuyển state + S99 active | vol gates |

Ghi chú: hàng E/H gần như regime-agnostic vì dựa trên cấu trúc flow/positioning cố định; hàng I ngược lại mỏng giòn nhất khi policy hai CB lệch pha — lý do mọi band trade (S81/S85/S90) đều có gate lịch CB.

**Đồ thị phụ thuộc giữa ideas (gate/filter — tránh backtest trùng lặp info)**
- S100 (policy clock) là parent của S3, S31, S91, S98 — không backtest 4 sleeve này như độc lập khi chúng cùng đọc state.
- S38 (carry viability) là gate bắt buộc của S31/S34; S80 (crowding+basis) là risk-overlay cho mọi position ngược crowd.
- S19/S65/S67 là bộ lọc driver-identification dùng chung cho family C/E khi vào breakout/continuation.
- S86 (Hurst) và S97 (HMM) là hai cách đo cùng regime — chọn một làm primary, cái kia chỉ cross-check (double-counting risk).
- S43/S44/S46 cùng họ flow-calendar: nếu chạy song song phải trừ overlap window cuối tháng/tháng đầu.

*Hết tài liệu lane EURUSD — FOREX-UNIFIED-STRATEGY-BRAINSTORM-V1.*
