# WTI (US Oil) — Deep Dive & 100 Strategy Ideas

- **Program**: FOREX-UNIFIED-STRATEGY-BRAINSTORM-V1 · **Lane**: WTI (broker: "US Oil" / USCRUDE / USOIL)
- **Ngày**: 2026-09-28 · **Loại**: knowledge-only brainstorm, không backtest, không data pull
- **Nguồn kiểm chứng thời sự Sep-2026**: news retrieval (wind-docs, finance-search index); các mục chưa xác minh được đánh dấu **(cần kiểm chứng)**. Bối cảnh trade-war (Section 338, thuế 50% + đe 50% auto 01/01/2027) lấy từ lane USDCAD đã verify — ảnh hưởng WTI gián tiếp qua demand & trade flows.

---

## 1. Bản chất instrument

### 1.1 Microstructure & sessions

- **Sản phẩm gốc**: NYMEX WTI Crude Oil futures (mã **CL**), light sweet (API gravity ~39.6°, sulfur ~0.24%), contract size 1,000 bbl, tick 0.01 USD = 10 USD/contract. Settlement 14:30 ET. Futures expiry ~3 ngày làm việc trước ngày 25 dương lịch của tháng liền trước tháng giao hàng; roll window thực tế ~5 ngày trước đó.
- **Sản phẩm broker**: "USCRUDE/USOIL" CFD track front-month continuous → giá đã nhúng roll: backwardation/contango hiện thể qua swap/overnight funding. Với chiến lược CFD, **roll cost là chi phí chiến lược**, không phải chi phí vụn vặt: giữ long qua 1 tháng backwardation sâu ~ +carry, contango sâu ~ −carry.
- **Giờ giao dịch** (CME Globex): Chủ nhật 18:00 ET → Thứ sáu 17:00 ET, break 17:00–18:00 ET (gần 23h × 5 ngày). Không có session "chính thức" đóng, nhưng liquidity profile phân tầng rõ:
  - **Asia (19:00–02:00 ET)**: mỏng, thường range; nhưng **Monday Asia open là nơi weekend gap hiện hình đầu tiên** — Sep-2026 chứng minh: các đợt tấn công/tanker incidents cuối tuần → gap 1–5% mở tuần.
  - **London (03:00–08:00 ET)**: ICE Brent dẫn dắt, WTI follow; nhiều headline Hormuz/Saudi rơi vào khung này (7/9/2026: Brent kéo lên ~$97 buổi sáng London).
  - **NY (08:00–14:30 ET)**: thanh khoản cao nhất; NYMEX floor open 09:00 ET; **EIA 10:30 ET**; settle 14:30 ET. Sau 15:30 ET liquidity void — avoid size.
- **Weekend gap**: dầu nghỉ Sat–Sun nhưng Middle East không nghỉ → trong regime xung đột, gap risk là structural (không phải noise). Khác biệt lớn so với FX majors: WTI có **event risk tích lũy 48h giải phóng trong 1 tick mở cửa**.
- **Options**: LO (NYMEX options) expire 3 ngày làm việc trước futures expiry; có weekly options thứ Hai — công cụ cho event trades (EIA, OPEC, weekend).

### 1.2 Điểm ĐẶC BIỆT riêng WTI (không có ở FX pairs, và khác cả Brent)

1. **Cushing, Oklahoma = delivery point vật lý duy nhất của CL**. Giá giấy WTI về bản chất là "giá dầu giao tại Cushing" → mức tồn Cushing là physical anchor. Working capacity ~76–91M bbl; vùng hoạt động an toàn mà market mặc định ~**20–25M bbl** (tank bottoms + minimums) — dưới ngưỡng, pipeline logistics gây backwardation sâu và squeeze risk. **Verified Sep-2026**: EIA tuần 11/9 Cushing **21.48M (−0.342M)**, tuần 4/9 **−0.684M** — đang trôi sát vùng nhạy cảm (ngưỡng chính xác theo capacity 2026 **(cần kiểm chứng)**).
2. **EIA crude inventories Wednesday 10:30 ET** là event định kỳ lớn nhất của instrument: reaction chuẩn hoá trong 1–5 phút đầu (spread co lại ngay trước release, nới ra ngay sau). API (Tuesday ~16:30 ET, private) đóng vai trò preview nhưng lệch EIA thường xuyên. **Tuần có lễ Monday (vd Labor Day) → EIA dời sang Thursday** — bẫy backtest kinh điển.
3. **Shale supply elasticity**: Mỹ sản ~13.9M bpd (EIA, Sep-2026). Cơ chế: giá cao → rig/completions tăng sau lag 3–9 tháng → tự tạo ceiling cho giá kéo dài. Breakeven Permian core ~$40s–50s, full-cost ~$60s–70s theo Dallas Fed survey các năm gần đây **(cần kiểm chứng survey 2026)**. Ở $90–104 (Sep-2026), shale là lực mean-reversion trung hạn mà Brent (OPEC+ quản lý) không đối xứng.
4. **Hurricane season (Jun–Nov, đỉnh ~10/9–20/9)**: GoM ~1.5–1.8M bpd crude + toàn bộ refining complex Gulf (~50% capacity Mỹ). Bão **vừa cắt supply (shut-in GoM) vừa cắt demand crude (refinery outage)** → chiều ròng của WTI phụ thuộc tỉ lệ bị ảnh hưởng; gasoline (RBOB) gần như luôn spike mạnh hơn crude — asymmetry để trade ratio.
5. **WTI–Brent spread = instrument nội bộ sống động**: drivers = pipeline nội địa (Midland→Gulf: Cactus II, EPIC, Gray Oak…), export capacity, freight, sanctions, quality. Bình thường ~$3–6. **Sep-2026 verified**: spread mở rộng bất thường ~$4 → ~**$12** trong tuần 21–25/9 (Brent giữ 101.94→105.85 trong khi WTI rơi 98.27→93.80) vì risk premium dồn vào barrels seaborne (Hormuz/Saudi) còn inventory Mỹ build — regime spread hiếm, phải track weekly.
6. **SPR cạn**: **285–287M bbl, thấp nhất từ 1982–83 (verified)** → "political put" truyền thống yếu đi; ngược lại pressure chính trị (xăng >$4/gal, mid-term 11/2026) đẩy quyết định release — SPR đang draw đều (~−0.4 đến −3.1M/tuần các tuần Aug–Sep 2026).
7. **Giá là hàm của 2 tầng**: (a) physical balance nội địa Mỹ (EIA/Cushing/exports) và (b) risk premium seaborne (Hormuz, OPEC+). Sep-2026 là tháng hiếm hoi 2 tầng tách rời nhau (WTI −6.4%/tuần trong khi Brent +2.1%) — bằng chứng sống rằng WTI không phải "Brent trừ hằng số".

### 1.3 Tin tức/sự kiện ảnh hưởng

**Scheduled** (giờ ET):

| Sự kiện | Thời điểm | Kênh truyền dẫn |
|---|---|---|
| EIA Weekly Petroleum Status Report | **Wed 10:30** (dời Thu nếu Monday là lễ) | Surprise crude/gasoline/distillate/Cushing vs consensus → front-month term structure → giá |
| API weekly | Tue ~16:30 | Preview EIA; lệch mẫu thường xuyên |
| Baker Hughes rig count | Fri ~13:00 | Supply 3–9 tháng tới (lag) |
| OPEC+ meeting (8 nước + full/JMMC) | đầu tháng, lịch không đều | Quota → seaborne balance → Brent → WTI |
| FOMC, CPI, NFP | theo lịch Fed/BLS | USD & yields → denominator; demand via growth |
| EIA STEO | Tue đầu tháng | Forecast anchor cho desks |
| OPEC MOMR / IEA OMR | ~giữa tháng | Balance revisions, often headline |
| CFTC COT | Fri ~15:00–15:30 (data Tuesday) | Positioning |

**Unscheduled + transmission channel**:

- **Tanker attacks / Hormuz transit collapse** (Kpler counts: verified 8/9/2026 chỉ ~6 tàu/ngày qua Hormuz vs ~120 tàu/ngày trước chiến tranh; trackable traffic 17 vs 37 tuần trước vào 21/9) → seaborne risk premium → Brent trước, WTI theo một phần.
- **Sanctions (OFAC) trên Iran/Russia/Venezuela** → supply anticipation → spike trước, mean-revert khi enforcement mờ.
- **SPR release/announcement** → political put; announcement thường bị fade (thể tích release nhỏ hơn thoại).
- **Pipeline outage** (Keystone, East-West Saudi…) → tách nội địa vs seaborne → spread trades.
- **Bão (NHC forecast cone)** → shut-in vs refinery outage (mục 1.2.4).
- **Ceasefire/talks headline** (verified 25/9/2026: Mỹ–Iran thảo luận phased end — Iran mở lại Hormuz đổi Mỹ dỡ sanctions → WTI −6.4%/tuần) → premium gỡ nhanh, hai chiều dữ dội.

### 1.4 Thông số ảnh hưởng (drivers đo được)

- **Inventories & Cushing**: (i) absolute vs 5-yr seasonal band; (ii) surprise z-score vs consensus; (iii) 4-week draw/build trend; (iv) Cushing absolute (<25M = nhạy).
- **Term structure**: CL1–CL2 calendar spread (backwardation = tight; contango = loose); độ sâu backwardation là thước "scarcity" tốt hơn flat price.
- **Shale economics**: rig count, breakeven band ($40s–70s), DUC wells; production 13.9M bpd (9/2026).
- **USD & real yields**: tương quan âm nhóm −0.2 → −0.4 theo regime; Sep-2026: 10Y ~5.0–5.04% (đỉnh 19 năm), Fed đã hike 16/9 → 3.75–4.00% — headwind song song với risk premium (hai lực đối nghịch giải thích whipsaw).
- **Demand mùa**: driving season (Memorial Day → Labor Day), RVP transitions (Apr, Sep), heating season (Dec–Feb, distillate), refinery turnaround (spring/fall).
- **Positioning/flows**: COT managed money & commercials; OI; options skew; USO AUM.
- **Geopolitical intensity**: Kpler/tanker transit counts, headline frequency, conflict escalation ladder (Mỹ–Iran từ cuối Feb-2026; Brent +30% từ lúc đó; đỉnh $126 cuối Apr; đáy WTI <$70 tháng 7 khi kỳ vọng MOU; Sep whipsaw 90→102→90→94 — verified).

### 1.5 Correlation map (11 symbol trong universe)

Số liệu là **bậc độ lớn điển hình theo regime** (daily, 60–120d rolling) — bắt buộc phải đo lại trên checkout trước khi dùng cho sizing; không phải hằng số:

| Symbol | Hướng | Bậc độ lớn | Breakdown / cơ chế |
|---|---|---|---|
| **BRENT** | + | **0.90–0.97** (cao nhất) | Cùng chất rủi ro seaborne; khác phần nội địa Mỹ + Cushing + export. Sep-2026 tách rời thành spread $12 — correlation moments giảm khi spread regime break |
| **USDCAD** | − | −0.3 → −0.5 | CAD = petro-currency (WCS heavy, energy ~20%+ export CAD). WTI up → CAD mạnh → USDCAD down. Phát mạnh khi WTI trend, chết khi WTI range |
| **XAUUSD** | + | +0.1–0.3 bình thường; +0.4–0.6 trong shared shock | Cùng hưởng inflation + geopolitical risk (Sep-2026: cả hai bid vì Hormuz + 10Y 5%); gold miễn nhiễm phần Cushing |
| **XAGUSD** | + | +0.2–0.4 | Precious beta + industrial demand; mạnh hơn gold khi risk-on, yếu hơn khi pure safe-haven |
| **AUDUSD** | + | +0.2–0.4 | Risk-on commodity beta; iron ore/China demand chồng lên |
| **NZDUSD** | + | +0.2–0.3 | Như AUD nhưng ít oil-link hơn (dairy/agri) |
| **EURUSD** | − | −0.1 → −0.3 (2026 lệch âm hơn) | (i) USD denominator; (ii) EU là oil importer thuần → energy shock đứt terms-of-trade của EUR (Sep-2026 rõ) |
| **GBPUSD** | ~0 ± | −0.1 → +0.1 | North Sea producer-ish vs USD effect — hai lực triệt tiêu |
| **USDJPY** | ~0 ± | ±0.2, phức tạp | Risk-off (oil spike) → JPY bid; nhưng US yields 5% → JPY yếu — hai lực đối nghịch, regime-dependent |
| **USDCHF** | − | −0.1 → −0.3 | CHF safe-haven bid khi oil spike do shock |
| **NATGAS** | + | +0.1–0.3 | Idiosyncratic weather/storage; link thật = associated gas production + cùng basin capex |

**Dùng thế nào**: Brent = twin (stat-arb + lead-lag); USDCAD = transmission trade; XAU/XAG = shared-regime confirmation; EUR = terms-of-trade pair; NATGAS = ratio rotation; JPY/CHF = risk-gauge exit signals.

### 1.6 Note trung thực — họ strategy hay chết trên WTI

- **Intraday mean-reversion + tight stops trong geopolitical one-way regime**: Sep-2026 có ngày +5.2% (1/9), +3σ ngày 14–15/9, chuỗi gap; mọi fade intraday không có gate regime đều chết.
- **Fade-the-news khi headline chưa xác nhận supply loss vật lý**: "talks" vs "attacks" nhảy nhau trong cùng tuần 3 (Sep-2026) — phải phân loại headline theo tính vật lý.
- **Stat-arb WTI–Brent không có regime gate**: sanctions/freight/pipeline break cointegration ngay ($4→$12 trong 1 tuần là bằng chứng).
- **Seasonality đứng sau war regime**: driving season 2026 bị geopolitics override hoàn toàn.
- **Carry trong contango deep**: giữ long front-month CFD trả roll + funding.
- **Breakout trong OPEC+ leak-window**: buy-rumor-sell-fact đảo chiều trong 15 phút.
- **Backtest không modeling**: EIA Thursday-shift, 10:30 ET whipsaw trong bar 30m, weekend gap không fill được, negative price 4/2020 phá log-return → các lỗi này thổi phồng kết quả (chi tiết mục 3.2).

---

## 2. 100 Strategy Ideas

Template mỗi ý (5 dòng nội dung): **S\<n\> — tên (family)** rồi Hypothesis / Signal / Trade / Risk / Data · Coupling.
Tất cả là hypothesis chưa test — không con số nào ở đây là kết quả.

### 2.1 Trend / Momentum (S1–S10)

**S1 — Donchian 20-day breakout hai chiều (Trend)**
- Hypothesis: dầu trending mạnh trong supply/demand-shock regime (fat tails 2 phía: 2020, 2022, 2026 đều vậy).
- Signal: giá close qua high/low 20 ngày trước đó; ATR(14) percentile >30 làm gate.
- Trade: entry stop-order tại channel edge, stop 2×ATR, trailing Donchian 10 ngày.
- Risk: chop trong low-vol regime (2023-style grind).
- Data: daily OHLC liên tục (roll-adjusted) · Coupling: chỉ bật khi backwardation hoặc contango sâu (term structure xác nhận trend có cơ sở vật lý).

**S2 — EMA 8/21 crossover H4 + ADX>25 (Trend)**
- Hypothesis: momentum intraday-week persists giữa các cú shock vì flow thông tin (tanker/sanction) đến theo cụm.
- Signal: EMA8 cắt EMA21 trên H4 + ADX(14)>25.
- Trade: entry tại close H4 sau cross, stop dưới swing gần nhất, exit khi cross ngược.
- Risk: whipsaw quanh EMA trong tin hỗn hợp (tuần 21–25/9/2026).
- Data: H4 OHLC · Coupling: session London+NY only; bỏ signal sinh trong Asia mỏng.

**S3 — Weekly continuation vào driving season (Trend)**
- Hypothesis: chuẩn bị mùa lái xe (refinery demand crude tăng) + breakout kỹ thuật = momentum có nền mùa.
- Signal: Friday close > high 4 tuần trước đó, trong tháng 5–6.
- Trade: long Monday open, stop 2×ATR(weekly), thoát trước Labor Day.
- Risk: war regime override mùa (2026); hurricane sớm.
- Data: weekly OHLC + lịch mùa · Coupling: chỉ chạy khi escalation index thấp (S92).

**S4 — 6-month time-series momentum, rebalance tháng (Trend)**
- Hypothesis: TSMOM 3–12m hoạt động tốt trên commodity có storage cost (literature: momentum trên futures curve).
- Signal: tổng return 6 tháng (roll-adjusted) >0 → long; <0 → flat (hoặc short riêng).
- Trade: monthly rebalance, vol-target 15% annualized (S96).
- Risk: đảo chiều nhanh khi premium gỡ (tuần 23/9/2026 loại long trễ).
- Data: continuous futures total-return series · Coupling: cùng engine cho 12 symbol → cross-section ở S90.

**S5 — Geopolitical ignition continuation (Trend)**
- Hypothesis: sau ngày headline >1.5×ATR theo hướng escalation, ngày+1 có continuation vì desks chưa cover hết + retail FOMO.
- Signal: ngày close |return| >1.5×ATR cùng chiều với headline escalation (attack/sanction, KHÔNG phải talks).
- Trade: entry next open, stop 1×ATR dưới đáy ngày ignition, trailing 2×ATR.
- Risk: false positive khi headline bị phủ định ngay (ceasefire giờ thứ 89).
- Data: daily OHLC + news classifier (attacks vs diplomacy) · Coupling: Kpler transit counts cùng chiều xác nhận physical loss.

**S6 — Trend-with-shale-ceiling (Trend)**
- Hypothesis: giá trên full-cost band ($85–95, ước 2026) kéo dài tự sinh cung shale sau 3–9 tháng → asymmetric: bỏ long breakout trên band.
- Signal: Donchian 20d + price vs shale full-cost band.
- Trade: long breakout chỉ khi price < band; trên band: chờ breakdown hoặc flat.
- Risk: band drift theo inflation/capex; ở $120+ wartime band mất ý nghĩa.
- Data: Dallas Fed breakeven survey, rig count lag, daily price (cần kiểm chứng band 2026) · Coupling: Fitch 2027-oversupply forecast cùng chiều ceiling.

**S7 — MACD histogram zero-cross + ATR gate (Trend)**
- Hypothesis: zero-cross MACD lọc bớt false signal cross trong vol cao.
- Signal: MACD(12,26,9) histogram đổi dấu trên daily + ATR percentile >40.
- Trade: entry close ngày cross, stop 2×ATR, exit cross ngược hoặc 3×ATR trail.
- Risk: lag lớn trong V-bottom (2/9→15/9/2026 đi lên quá nhanh).
- Data: daily OHLC · Coupling: không dùng 2 ngày quanh OPEC+/EIA holiday-shift.

**S8 — Market-structure shift H4/D cơ học (Trend)**
- Hypothesis: chuỗi HH/HL vỡ là đơn vị trend của discretionary oil desks → hành vi tự hoàn thành ngắn hạn.
- Signal: swing high/low định nghĩa bằng fractal 5-bar; shift khi break structure + retest.
- Trade: entry tại retest, stop dưới retest swing.
- Risk: chop: market structure tan vỡ trong 1 bar EIA.
- Data: H4/D OHLC · Coupling: skip signal sinh ngay sau 10:30 ET Wednesday.

**S9 — Bollinger %B persistence (Trend)**
- Hypothesis: %B>0.9 giữ nguyên 3 ngày liên tiếp = strength thật (không phải spike đơn).
- Signal: %B(20,2) >0.9 ba ngày close liên tiếp.
- Trade: long ngày 4, stop dưới đáy 3 ngày, trail %B<0.2.
- Risk: exhaustion ở đỉnh premium (15/9/2026 là ví dụ thoát đúng lúc).
- Data: daily OHLC · Coupling: Cushing draw cùng thời điểm tăng xác suất continuation.

**S10 — Momentum kill-switch theo vol z (Trend)**
- Hypothesis: khi realized vol z(10d) >3, phân phối return trở nên bimodal (gap risk) — cắt momentum trước khi momentum crash.
- Signal: RV10 z-score >3 → force flat mọi trend book, 2 ngày quan sát.
- Trade: overlay quản trị, không entry riêng.
- Risk: bỏ qua đợt continuation lớn nhất (chi phí bảo hiểm).
- Data: daily/intraday OHLC · Coupling: bật cùng weekend straddle book (S44/S100).

### 2.2 Mean-reversion (S11–S20)

**S11 — EIA overshoot fade khi surprise nhỏ (Mean-reversion)**
- Hypothesis: khi |surprise z| <1, cú 60–300 giây đầu là liquidity event, không phải information → retracement 50%+ trong 30 phút.
- Signal: |crude surprise| <1 std của phân phối surprise 3 năm.
- Trade: fade chiều tick đầu sau 10:30:15, stop 0.6×move đầu, target 50% retracement, thoát trước 11:30 ET.
- Risk: surprise nhỏ nhưng Cushing/gasoline mâu thuẫn lớn → one-way thật.
- Data: EIA surprise history + M1 data + consensus · Coupling: API cùng chiều trước đó → giảm kích thước fade.

**S12 — Monday gap fade không xác nhận supply loss (Mean-reversion)**
- Hypothesis: weekend headline "đàm phán/nói chuyện" tạo gap thiếu vật lý → gap fills trong tuần khi không có tổn thất barrel xác nhận.
- Signal: Monday Asia gap >1.5×ATR(20)_daily mà Kpler transit + shut-in counts không đổi.
- Trade: fade gap hướng về Friday close, stop ngoài gap extreme, target 50% gap, T+2 ngày.
- Risk: tuần mà escalation thật đến giữa tuần (7–9/9/2026).
- Data: weekend news classification + Kpler + daily OHLC · Coupling: chỉ fade hướng XUỐNG khi SPR/policy floor đang hoạt động.

**S13 — Bollinger(20, 2.5σ) touch-fade trong ADX<20 (Mean-reversion)**
- Hypothesis: regime low-vol, oil bị kéo về mean bởi storage economics (contango nhẹ hút arbitrage).
- Signal: giá chạm band 2.5σ trên daily + ADX(14)<20.
- Trade: entry tại band, stop 0.7×ATR ngoài band, target middle band.
- Risk: breakout thật từ trong compression (đúng lúc OPEC leak).
- Data: daily OHLC · Coupling: chỉ khi term structure flat — deep backwardation thì bỏ (trend regime).

**S14 — Cushing squeeze fatigue fade (Mean-reversion)**
- Hypothesis: Cushing <22M + prompt backwardation sâu làm giá spike, nhưng logistics (re-route từ Gulf) điều chỉnh trong 2–4 tuần → fade phần cuối.
- Signal: Cushing <22M (2 tuần liên tiếp) + CL1−CL2 spread z>2.
- Trade: short từng leg nhỏ vào các ngày spike, stop 1.5×ATR, T+3 tuần, hedge long call chống tail chiến sự.
- Risk: thiếu barrel thật sự (squeeze thật).
- Data: EIA Cushing weekly + futures curve · Coupling: exports tuần giảm → điều kiện fade mất.

**S15 — Buy pullback về 10-EMA trong uptrend (Mean-reversion)**
- Hypothesis: trong trend, nhịp 2–4 ngày pullback được absorb bởi passive bid (index/xuất khẩu).
- Signal: daily uptrend (định nghĩa S1) + giá chạm 10-EMA + RSI(2)<25.
- Trade: long tại EMA touch, stop dưới swing 2-bar, target channel high.
- Risk: pullback thành reversal khi premium gỡ (23/9/2026).
- Data: daily OHLC · Coupling: chỉ khi DXY không phá lên cùng lúc.

**S16 — Long-horizon value: z(price/200dma) >2 fade (Mean-reversion)**
- Hypothesis: dầu về mặt bằng shale full-cost trong 3–9 tháng trừ khi chiến tranh cấu trúc.
- Signal: (log price − log 200dma)/stdev >2 và war escalation index thấp.
- Trade: short nhỏ, accumulate theo scale 0.25σ, T+2–3 tháng, stop khi z>3.
- Risk: regime Hormuz "new normal" (HSBC Sep-2026 gọi thế) giữ premium có cấu trúc.
- Data: daily + news index · Coupling: Fitch/BofA/GS forecast band làm sanity check.

**S17 — Pre-EIA Tuesday dip buy trong driving season (Mean-reversion)**
- Hypothesis: tay mùa giảm position trước event → Tuesday hơi rẻ so với fair trong tuần EIA mùa cầu.
- Signal: mùa 5–8; Tuesday close < Friday close quá 0.5×ATR không có tin xấu.
- Trade: long Tuesday close, thoát Wednesday 10:25 ET (TRƯỚC release) — premium capture, không phải event bet.
- Risk: tuần có holiday-shift làm nhịp loạn.
- Data: daily + lịch EIA/lễ · Coupling: dùng chung distribution với S43.

**S18 — Post-vol-spike compression fade (Mean-reversion)**
- Hypothesis: sau ngày RV>3σ, 2–3 ngày sau range co lại (vol cluster nhưng không one-way).
- Signal: extension ngoài 1.5×ATR trong ngày sau spike → fade về VWAP ngày.
- Trade: intraday fade tối đa 2 lần/ngày, stop 0.5×ATR.
- Risk: ngày 2–3 của cùng cụm headline (9/9→14/9/2026 liên tục).
- Data: intraday + news cluster counter · Coupling: kill khi cluster counter vượt ngưỡng.

**S19 — VWAP 2σ fade sau 13:00 ET (Mean-reversion)**
- Hypothesis: buổi chiều NY (post-lunch, pre-settle) thiếu flow mới; extension từ morning session bị flatten cho settle.
- Signal: giá > VWAP + 2σ(RV intraday) sau 13:00 ET.
- Trade: fade về VWAP, stop 0.3×ATR(daily), force-exit 14:25 ET.
- Risk: EIA/exceptional flow trễ; settle run (index).
- Data: M5 + VWAP · Coupling: không dùng Wednesday (EIA) & expiry window.

**S20 — Hurricane landfall sell-the-news (Mean-reversion)**
- Hypothesis: market mua "shut-in supply" trước landfall; sau landfall câu chuyện lật sang "refinery outage = crude demand loss".
- Signal: NHC cone xác nhận major hurricane (Cat≥2) hướng GoM refining > production.
- Trade: pre-landfill thoát long; post-landfall short WTI 1–3 ngày, stop 1×ATR.
- Risk: bão thật sự phá production + export (chiều ngược).
- Data: NHC tracks + shut-in statistics (BSEE) · Coupling: gasoline spike đồng thời = confirm refinery-side.

### 2.3 Breakout / Vol-expansion (S21–S30)

**S21 — EIA bracket breakout (Breakout)**
- Hypothesis: 5–15 phút đầu sau EIA có trending persistency do cascade stop + algo interpret.
- Signal: stop orders 2 phía range 9:45–10:29 ET cách 0.3×ATR; kích hoạt bởi tick đầu vượt.
- Trade: OCO bracket; stop đối diện 0.5×range; target 2R; thoát 12:00 ET.
- Risk: whipsaw 2 phía trong release mâu thuẫn (crude draw + gasoline build như 17/9/2026).
- Data: M1 quanh release + surprise history · Coupling: surprise z>1.5 mới bật (nhỏ hơn nhường cho S11).

**S22 — NR7 / inside-day compression breakout (Breakout)**
- Hypothesis: compression range tuần đi trước expansion trên commodity có event calendar dày.
- Signal: ngày range nhỏ nhất trong 7 ngày (hoặc inside day); breakout次日 qua edge ±0.25×range đó.
- Trade: stop orders 2 phía, stop 0.5×compression range, trail 2×ATR.
- Risk: false break trong Wednesday EIA → skip nếu NR7 rơi vào thứ Tư.
- Data: daily OHLC · Coupling: open interest tăng trong compression = confirm.

**S23 — Asia-range breakout tại London open (Breakout)**
- Hypothesis: London desks react tin Middle East tích lũy từ Asia; break range Asia có continuation tới NY.
- Signal: giá vượt Asia high/low (range 19:00–02:00 ET) trong 03:00–05:00 ET với volume London xác nhận.
- Trade: entry break, stop đối diện range giữa, target 1×Asia range.
- Risk: false break trong liquidity mỏng thứ Hai lễ.
- Data: H1/M15 + session map · Coupling: Brent break cùng chiều trước WTI = confirm (S62).

**S24 — Vol-cone breakout (Breakout)**
- Hypothesis: giá break 20d high + realized vol break percentile 80 của chính nó = expansion kép, hiếm false.
- Signal: RV10 > upper vol cone (rolling 1y percentile) & price > 20d high.
- Trade: long breakout, stop 1.5×ATR, trail chandelier.
- Risk: vol burst đơn ngày rồi tắt (headline bị bác).
- Data: daily OHLC + RV calc · Coupling: term structure cùng chiều steepen.

**S25 — OPEC+ resolution breakout (Breakout)**
- Hypothesis: 2–3 ngày trước OPEC+ meeting giá nén lại; sau quyết định thực tế, chiều thật bung trong 1–3 giờ đầu.
- Signal: range 3 ngày pre-meeting; entry khi headline chính thức (quota số, không phải phát ngôn) break edge ±0.4×range.
- Trade: theo chiều quyết định so với kỳ vọng (cut > kỳ vọng → long), stop 1×ATR, T+2 ngày.
- Risk: leak/đồn trước đó đã price-in → sell the news.
- Data: OPEC release history + kỳ vọng survey (Reuters/Bloomberg pre-meeting) · Coupling: chỉ khi kỳ vọng vs actual lệch đủ lớn.

**S26 — Weekend gap-and-go Monday (Breakout)**
- Hypothesis: khi có tấn công cuối tuần xác nhận vật lý, Monday gap có continuation ngày 1–2 (khác S12: gap CÓ tổn thất barrel).
- Signal: gap >2% + Kpler/tanker incident count tăng.
- Trade: theo chiều gap tại Asia mở, stop 50% gap, trail 1.5×ATR.
- Risk: phản ứng chính trị ôn hòa lập tức → gap fill.
- Data: weekend incident feed + M15 Monday · Coupling: gold gap cùng chiều = shared shock confirm (S63).

**S27 — 52-week high/low close-confirm (Breakout)**
- Hypothesis: break vùng 52 tuần với daily close là tail-risk được định giá lại (cấu trúc shift).
- Signal: close ngoài 52w high/low; confirm volume >1.5×median.
- Trade: entry次日 open, stop 2×ATR, position nhỏ (tail regime).
- Risk: đỉnh/đáy giả trong wartime whipsaw.
- Data: daily OHLC full history · Coupling: kết hợp với S4 TSMOM.

**S28 — Chandelier H1 breakout NY (Breakout)**
- Hypothesis: trong NY session, ATR-chandelier trên H1 bắt trend intraday các ngày nóng.
- Signal: H1 close > chandelier(22, 3×ATR_H1) trong 09:00–13:00 ET.
- Trade: long, stop chandelier flip, exit 14:30 settle — intraday thuần, không giữ overnight.
- Risk: ngày dull chop chết theo trail.
- Data: H1 intraday · Coupling: bật khi daily regime = trend (S91 gate).

**S29 — NYMEX open-range breakout 9:00–9:30 ET (Breakout)**
- Hypothesis: 30 phút đầu floor định nhịp ngày thường nhật (trừ Wednesday).
- Signal: break high/low của 9:00–9:30 trong 9:30–11:00.
- Trade: stop order tại OR edge, stop 0.5×OR, target 1.5×OR.
- Risk: Wednesday: EIA invalidate; Friday: pre-weekend risk-off.
- Data: M5 · Coupling: dùng kèm S43 calendar map.

**S30 — Post-thrust first-pullback continuation (Breakout)**
- Hypothesis: sau ngày >3×ATR (thrust), pullback đầu tiên về 38–50% của cú thrust được absorb.
- Signal: thrust day xác nhận; 1–3 ngày sau giá về vùng 38–50% retracement + volume cạn.
- Trade: theo hướng thrust tại retracement, stop dưới 50% level, target new extreme.
- Risk: pullback sâu hơn 61.8% = reversal flag.
- Data: daily OHLC · Coupling: S18 là dạng intraday cùng triết lý — không chạy song song cùng ngày.

### 2.4 Carry / Term-structure (S31–S40)

**S31 — Backwardation depth gate cho long bias (Carry)**
- Hypothesis: backwardation prompt sâu = thị trường thiếu barrel thật; flat price có drift dương (roll + scarcity premium).
- Signal: CL1−CL2 (chuẩn hoá 30 ngày) > 75th percentile 1 năm.
- Trade: long bias mọi pullback (kết hợp S15), funding dương từ roll.
- Risk: gỡ premium nhanh khi ceasefire (23–25/9/2026).
- Data: futures curve daily + CFD swap · Coupling: inventory draw cùng chiều = strongest combo.

**S32 — Contango steepener short bias (Carry)**
- Hypothesis: contango sâu = over-supply vật lý; flat drift âm + roll âm.
- Signal: CL1−CL2 < 25th percentile.
- Trade: short bias trên rally, hoặc short calendar spread riêng.
- Risk: SPR mua lại / chiến tranh lật cấu trúc trong 1 tuần.
- Data: futures curve + SPR policy feed · Coupling: giá dưới shale breakeven band làm short yếu đi (phản diện S54).

**S33 — Roll-yield harvest filter (Carry)**
- Hypothesis: giữ long front-month CFD chỉ khi roll yield dự kiến 30 ngày tới dương → chuyển negative-carry tail thành positive-carry đều.
- Signal: roll yield 1 tháng annualized >0 (từ curve hiện tại).
- Trade: long khi positive & trend không chống; flat khi negative.
- Risk: flat price swing lấn át carry (carry nhỏ so với ATR).
- Data: curve + swap cost broker · Coupling: overlay cho mọi long-holding strategy ở lane này.

**S34 — Calendar spread CL2−CL1 trend thuần túy (Carry)**
- Hypothesis: term structure trending chậm hơn flat price và có momentum riêng theo inventory cycle.
- Signal: 20d change của CL2−CL1 vượt 1σ → theo chiều.
- Trade: trade spread bằng 2 legs futures (hoặc 2 CFD khác tháng nếu broker có), stop 0.5σ, T+1 tháng.
- Risk: warehouse/SPR policy discontinuity.
- Data: curve history · Coupling: gate bằng 4-week inventory trend cùng chiều.

**S35 — WTI–Brent spread momentum theo logistics (Carry)**
- Hypothesis: khi sự kiện logistics diễn ra chậm (pipeline outage, export terminal hỏng), spread trend theo hướng đó tới khi capacity khôi phục — không phải MR ngay.
- Signal: spread vượt 90d percentile ngay sau sự kiện logistics xác nhận.
- Trade: theo chiều spread (vd Sep-2026: short WTI/long Brent khi spread nới ra), stop 0.5×event move, exit khi repair headline.
- Risk: repair nhanh + ceasefire cùng lúc → snapback dữ dội.
- Data: spread series + logistics news · Coupling: freight rates (VLCC) cùng chiều confirm.

**S36 — Inventory + term-structure combo gate (Carry)**
- Hypothesis: draw + steepening backwardation = thiếu barrel kép; build + contango = thừa kép; trạng thái khác neutral.
- Signal: 4-week inventory trend × CL1−CL2 slope cùng dấu.
- Trade: binary gate: (+,+) → long-only book; (−,−) → short-only; còn lại flat.
- Risk: divergent states (draw + contango = export pull) thường chết.
- Data: EIA + curve · Coupling: meta-gate cho S1/S15/S31.

**S37 — Winter storage spread Dec1−Dec2 (Carry)**
- Hypothesis: mùa đông demand distillate kéo rộng Dec calendar; spread có mùa rõ (fall build → winter draw).
- Signal: trong Sep–Oct, Dec1−Dec2 spread rộng hơn 5-yr trung bình + forecast lạnh (NOAA).
- Trade: long Dec1/short Dec2 từ giữa Sep, exit giữa Dec, stop 0.5×seasonal band.
- Risk: mùa đông ấm + chiến tranh kết thúc.
- Data: curve seasonal + NOAA · Coupling: NATGAS winter bid cùng chiều confirm.

**S38 — Roll-window microstructure fade (Carry)**
- Hypothesis: trong roll window 5 ngày, flow bị động (index funds) làm giá front-month lệch khỏi fair → mean revert sau roll xong.
- Signal: front-month under/over-perform liên tục 3 ngày trong roll window không có tin.
- Trade: fade distortion, exit cuối roll window, size nhỏ.
- Risk: distortion thật do delivery squeeze.
- Data: front/second data + OI decay · Coupling: liên quan S80 (định lượng roll pressure).

**S39 — Carry-adjusted trend (Carry)**
- Hypothesis: trend entry chỉ có edge dương kỳ vọng khi roll yield không ngược chiều quá 1/3 ATR/tháng.
- Signal: S1 breakout + roll yield cùng chiều (hoặc flat).
- Trade: kích thước nhân 1.0 khi carry thuận, 0.5 khi ngược nhẹ, 0 khi ngược mạnh.
- Risk: filter làm mất các đợt breakout pure-sentiment.
- Data: OHLC + curve · Coupling: đúng triết lý S33 nhưng là sizing overlay cho S1.

**S40 — Butterfly CL1−CL3−CL5 curvature (Carry)**
- Hypothesis: curvature của curve dao quanh equilibrium storage; cực đoan revert khi mùa storage bình thường.
- Signal: fly z-score >±2 trong 1 năm rolling.
- Trade: mean-revert fly bằng 3 legs tỷ lệ 1:−2:1, stop 0.5σ, T+3 tuần.
- Risk: chiến tranh làm near-leg tách khỏi storage logic.
- Data: 5 tenor curve history · Coupling: chỉ khi không có event regime (S92 index thấp).

### 2.5 Session / Time-of-day / Seasonality (S41–S50)

**S41 — Driving-season long có trend gate (Seasonality)**
- Hypothesis: mùa cầu (Memorial Day → Labor Day) tạo drift dương trung bình khi không có chiến sự.
- Signal: giữ long từ cuối tháng 5 chỉ khi trend filter (đóng trên 50dma) bật.
- Trade: entry scale 3 lô, stop 2×ATR(weekly), thoát 25/8.
- Risk: 2026-type war regime override (mùa 2026 đã vậy).
- Data: daily + lịch · Coupling: gasoline demand EIA cùng chiều để giữ vị thế.

**S42 — Hurricane-season long vol (Seasonality/Options)**
- Hypothesis: IV underprice đỉnh mùa bão (Sep trung bình) → straddle mua trước mùa có edge dương trung bình.
- Signal: mua straddle 30–45 ngày vào giữa tháng 6–7 hằng năm.
- Trade: giữ qua 15/9, thoát sau; size 0.5% NAV.
- Risk: năm không bão (theta cháy).
- Data: options chain lịch sử (cần kiểm chứng tính sẵn có của chain quá khứ) · Coupling: NHC seasonal forecast trên trung bình.

**S43 — EIA-day intraday shape calendar (Session)**
- Hypothesis: Wednesday có hình dạng cố định: co range 9:30–10:30, expand sau — trade được như calendar thời gian.
- Signal: IV thấp → long straddle M15 lúc 10:00 ET, thoát 11:30 ET; IV cao → bracket S21.
- Trade: hai cấu hình tách bạch theo IV trước event.
- Risk: release trễ / tuần holiday-shift.
- Data: M1/M15 + EIA calendar · Coupling: S17 (exit trước event) là chân đối xứng của distribution này.

**S44 — Friday-close weekend straddle trong war regime (Session/Options)**
- Hypothesis: trong regime chiến sự, weekend event frequency cao → gamma Friday mua rẻ so với realized gap.
- Signal: escalation index > ngưỡng (tuần có tanker incident) → mua Monday-expiry straddle Friday 14:00 ET.
- Trade: giữ qua weekend, thoát Monday 1–2 giờ sau mở; size 0.5–1% NAV.
- Risk: tuần im (theta + IV crush).
- Data: options + incident feed · Coupling: Kpler counts thấp → tăng size (S100 cùng gia đình, khác trigger đo lường).

**S45 — NY first-hour open-drive continuation (Session)**
- Hypothesis: ngày có "open drive" (9:00–10:00 ET một chiều không chạm VWAP) thường tiếp tục tới settle (market profile).
- Signal: 10:00 ET giá chưa chạm VWAP + return 1h >0.75×ATR(hourly).
- Trade: entry 10:05, stop VWAP, exit 14:25.
- Risk: Wednesday bị EIA chặn (skip); Friday risk-off.
- Data: M5 + VWAP · Coupling: S19 là chiều ngược của cùng profile — chọn theo open-drive có hay không.

**S46 — Liquidity-void fade 15:30+ ET (Session)**
- Hypothesis: sau 15:30 ET liquidity mỏng, extension không có flow đỡ → về VWAP/đóng ngày.
- Signal: 15:30–17:00 ET giá extension >1σ RV intraday không tin mới.
- Trade: fade nhỏ về VWAP, force close 17:00 ET, stop 0.25×ATR.
- Risk: quy mô nhỏ bắt buộc; algos quét stop.
- Data: M5 · Coupling: không chạy expiry/witching.

**S47 — Turn-of-month / roll bias (Session)**
- Hypothesis: 5 ngày cuối tháng có flow định kỳ (rebalance index commodity) một chiều nhẹ.
- Signal: đo drift trung bình 5 ngày cuối tháng trên 15 năm; giao dịch nếu t-stat vượt ngưỡng.
- Trade: theo drift đo được, size 0.5×base.
- Risk: drift không ổn định qua các thập kỷ (phải walk-forward).
- Data: daily continuous + lịch roll · Coupling: S38 cùng window — không chồng lấn kích thước.

**S48 — Winter distillate-cold-snap long (Seasonality)**
- Hypothesis: đợt lạnh Mỹ Đông trong Nov–Feb khi distillate stocks thấp → WTI bid theo heating demand.
- Signal: NOAA 8–14d forecast dưới trung bình 3°F + distillate inventories < 5y band thấp.
- Trade: long 2–5 ngày quanh forecast release, stop 1×ATR.
- Risk: natural gas thay thế + mùa đông ấm.
- Data: NOAA + EIA distillate · Coupling: NATGAS cùng spike confirm (gia đình S66).

**S49 — September-slump short (Seasonality)**
- Hypothesis: sau Labor Day, driving season kết thúc + refinery turnaround → nhu cầu crude gap xuống.
- Signal: short 5–10/9 hằng năm khi không có chiến sự; cover 20/9.
- Trade: short, stop 1.5×ATR, target 3–5%.
- Risk: năm có bão/chiến sự thì ngược hoàn toàn (chính Sep-2026: +15% trước khi rơi).
- Data: daily 20 năm + event calendar · Coupling: gate escalation index + NHC active storms — hai cái này đỏ thì bỏ.

**S50 — SC (Shanghai) → WTI lead-lag mở NY (Session)**
- Hypothesis: phiên Asia price-in tin Trung Quốc/demand trước; SC mở 09:00 CST dẫn WTI mở NY cùng ngày khi có tin demand.
- Signal: SC breakout session đầu (09:00–10:30 CST) >1% không có tin Mỹ tương ứng.
- Trade: theo chiều SC vào WTI tại 18:00–19:00 ET reopening, stop 0.5×ATR(H).
- Risk: hai thị trường khác cấu trúc (SC premium nội địa, nội tệ) làm nhịp loạn.
- Data: SC intraday + WTI intraday (cần kiểm chứng availability broker) · Coupling: USDCNH cùng chiều.

### 2.6 Event / Data-driven (S51–S60) — EIA inventory surprise là trục

**S51 — EIA surprise direction trade (Event)**
- Hypothesis: composite surprise (crude + gasoline + distillate + Cushing) dự báo chiều return cùng ngày vì algo + desks chase cùng nguồn.
- Signal: composite z = w1·crude + w2·gasoline + w3·distillate (trọng số theo lịch sử R², tự đo).
- Trade: entry 10:31 ET theo dấu z nếu |z|>1, exit close ngày, stop 1×ATR(H2).
- Risk: composite mâu thuẫn nội bộ → z gần 0 (skip).
- Data: surprise history + M1 · Coupling: S21 cho entry nhanh hơn nhưng rủi ro hơn.

**S52 — API–EIA divergence trade (Event)**
- Hypothesis: khi API lệch consensus mạnh, EIA thường về phía API (cùng nguồn khảo sát vật lý).
- Signal: |API surprise − consensus| >1.5 std và chiều ngược consensus.
- Trade: vị thế theo API setup Wednesday 10:15 ET, flatten ngay sau release nếu EIA xác nhận, giữ nếu EIA trệch.
- Risk: API sample lệch kéo dài (private, sai thường xuyên 2020s).
- Data: API + EIA + consensus · Coupling: API chỉ làm prior, không làm tín hiệu độc lập.

**S53 — Cushing <20M trigger long-bias (Event)**
- Hypothesis: dưới ~20M bbl, tổn thất vận hành xảy ra (tank bottoms) → premium cấu trúc cho tới khi barrels quay lại.
- Signal: EIA Cushing <20M hai tuần liên tiếp.
- Trade: long-bias book (kết hợp S31) đến khi Cushing rebuild >22M, stop theo ATR không theo mốc.
- Risk: xuất khẩu sụt làm Cushing tự rebuild nhanh; ngưỡng thay đổi theo capacity (cần kiểm chứng 2026).
- Data: EIA Cushing + curve backwardation · Coupling: exports weekly cùng watch.

**S54 — Rig-count 3-tuần decline + sub-breakeven price → long (Event)**
- Hypothesis: market undervalue supply-response lag 3–9 tháng; giá dưới breakeven lâu → production sắp giảm.
- Signal: rig count giảm 3 tuần liên tiếp & giá 3 tháng trước < breakeven band.
- Trade: long giữ 1–3 tháng (vị thế kỳ hạn nếu broker có), stop 2×ATR(monthly).
- Risk: rig productivity tăng phá liên kết rig→production.
- Data: Baker Hughes + breakeven survey · Coupling: DUC wells count điều chỉnh.

**S55 — OPEC+ quota surprise follow (Event)**
- Hypothesis: quyết định quota lệch kỳ vọng ≥ vài trăm kbpd chưa price-in hoàn toàn trong 1–3 ngày (desks phải re-run balance).
- Signal: actual quota vs survey kỳ vọng lệch >500 kbpd.
- Trade: theo chiều (cut → long) tại confirmation headline, stop 1×ATR, T+3 ngày.
- Risk: leak sớm đã price-in; members không tuân thủ.
- Data: OPEC release + pre-meeting survey · Coupling: tanker exports 4 tuần sau xác nhận (Kpler).

**S56 — SPR announcement fade (Event)**
- Hypothesis: SPR release headline tạo cú down nhanh, nhưng thể tích release luôn nhỏ hơn thoại → bounce 2–5 ngày.
- Signal: DOE announcement SPR release/sale.
- Trade: long 30 phút sau headline (fade cú xuống), stop dưới low headline, T+5 ngày.
- Risk: release khẩn quy mô lớn wartime (chưa từng).
- Data: DOE announcements + SPR levels · Coupling: SPR đã 285M (đáy 1982) → biên độ công cụ mỏng dần.

**S57 — NHC cone: pre-landfall long / post-landfall reverse (Event)**
- Hypothesis: market định giá shut-in trước, refinery-loss sau → chiều oil trái nhau giữa 2 pha.
- Signal: NHC 5-day cone xác nhận Cat≥2 GoM landfall trong 72h.
- Trade: pha 1 (72h trước): long WTI + long gasoline; pha 2 (sau landfall): short WTI giữ gasoline long.
- Risk: bão trượt / mạnh hơn dự kiến.
- Data: NHC + BSEE shut-ins · Coupling: S20 chỉ trade pha 2 — tránh double count.

**S58 — Post-FOMC USD-reversal oil bounce (Event)**
- Hypothesis: hawkish Fed đẩy DXY lên → oil bị bán theo denominator; khi USD reversal cùng session, oil bounce mạnh (phần rủi ro supply vẫn đó).
- Signal: FOMC ngày: DXY +0.4% lúc 14:30–15:30 ET rồi đảo giảm dưới +0.15% trước đóng.
- Trade: long oil theo USD reversal, stop 0.7×ATR, exit次日 open.
- Risk: oil-demand-bearish hawkish (growth scare) thì không bounce.
- Data: DXY intraday + oil M15 + FOMC calendar · Coupling: 10Y yield ổn định mới bật.

**S59 — Sanction-headline reaction ladder (Event)**
- Hypothesis: sanctions escalation có decay 2–3 ngày (spike ngày 0, chew ngày 1–2, fade nếu enforcement mờ).
- Signal: OFAC/sanction headline loại mới (Iran/Russia/Venezuela).
- Trade: long 30 phút sau headline (không đuổi spike đầu), scale out 1/3 mỗi ngày, T+3 ngày, stop 1×ATR.
- Risk: thực thi ngay lập tức (tanker bị bắt thật) → không fade.
- Data: OFAC feed + enforcement news · Coupling: Brent phản ứng trước WTI.

**S60 — Export surge + Cushing draw combo long (Event)**
- Hypothesis: exports 4.8M bpd (verified Sep-2026, +1.4M) kéo barrel từ Cushing → "Mỹ đang cấp thế giới" bullish flat + backwardation.
- Signal: weekly exports z>1 & Cushing draw z>1 cùng tuần.
- Trade: long Thursday sau EIA, giữ tới EIA tuần sau, stop 1.5×ATR.
- Risk: demand nước ngoài sụt → exports đảo nhanh; spread regime làm WTI đi ngược Brent.
- Data: EIA exports + Cushing · Coupling: Brent cùng tuần phải bid (Brent yếu → skip).

### 2.7 Cross-asset / Correlation (S61–S70)

**S61 — USDCAD crude-beta pair (Cross-asset)**
- Hypothesis: WTI trend → CAD mạnh → USDCAD xuống; beta mạnh khi WTI trend, chết khi range.
- Signal: WTI close qua 20d high + USDCAD chưa break 20d low.
- Trade: short USDCAD (0.6×beta-sized), stop 0.8×ATR(USDCAD), exit khi WTI trend kill.
- Risk: BoC policy / domestic factors CAD đè beta.
- Data: WTI + USDCAD daily + beta rolling · Coupling: WCS heavy spread điều chỉnh beta (cần kiểm chứng data).

**S62 — Brent lead / WTI lag cross-listed signal (Cross-asset)**
- Hypothesis: tin seaborne chạm ICE Brent session London trước; WTI follow trong 1–4 giờ (arbitrage latency người).
- Signal: Brent break 20-bar H4 high trong London session, WTI chưa.
- Trade: long WTI khi Brent confirm, stop 0.6×ATR(H4), target move Brent đã đi ×beta ~0.9.
- Risk: spread regime break (tuần 21–25/9/2026) làm lead-lag đảo hỗn loạn.
- Data: H4 cả hai + rolling beta · Coupling: S35 regime gate bật cùng lúc.

**S63 — Gold-confirmation gate cho oil breakout (Cross-asset)**
- Hypothesis: breakout WTI có gold cùng bid = shared inflation/geopolitical shock (broad) → win-rate cao hơn breakout đơn độc.
- Signal: oil break 20d high trong cùng ngày gold break 20d high.
- Trade: cho phép khởi động S1/S24; không có gold confirm → kích thước nửa.
- Risk: gold bị yields (10Y 5%, Sep-2026) chặn → confirmation thiếm trong khi oil vẫn chạy (miss, không loss).
- Data: daily cả hai · Coupling: 10Y real yield là biến loại trừ.

**S64 — Oil-vs-SPX supply-shock overlay (Cross-asset)**
- Hypothesis: supply-shock oil rally là "thuế người tiêu dùng" → SPX xuống; cặp long oil/short SPX có payoff convex trong shock.
- Signal: escalation index cao + oil 5d return > +5%.
- Trade: long WTI + short SPX dollar-matched, size nhỏ, thoát khi oil trend kill.
- Risk: risk-on đồng loạt (Fed pivot + war end) → cả hai chân thua.
- Data: SPX + WTI + news index · Coupling: breakeven inflation (S98) tăng confirm.

**S65 — DXY-inverse alignment gate (Cross-asset)**
- Hypothesis: oil bull bền cần USD không chống (denominator); DXY downtrend + oil uptrend = alignment tối ưu.
- Signal: DXY < 50dma giảm dần & WTI > 50dma tăng.
- Trade: gate kích thước S1 book ×1.5 khi alignment; DXY uptrend → ×0.5.
- Risk: wartime decoupling 2022 (cả hai cùng lên vì safe-haven USD).
- Data: DXY + WTI · Coupling: đo lại tương quan 60d mỗi tuần (map 1.5).

**S66 — WTI/NATGAS ratio rotation (Cross-asset)**
- Hypothesis: tỷ lệ oil/gas dao động theo mùa (mùa đông gas mạnh) và theo associated-gas production; cực đoan revert khi capex điều chỉnh.
- Signal: ratio z(63d) >±2.
- Trade: fade ratio bằng 2 legs, stop 0.5σ, T+1 tháng.
- Risk: mùa đông cực đoan (gas spikes) làm ratio rơi liên tục.
- Data: WTI + NATGAS daily · Coupling: NOAA forecast & EIA gas storage Thursday 10:30 ET.

**S67 — AUD confirmation gate (Cross-asset)**
- Hypothesis: oil rally do demand-thật có AUD đi cùng; oil rally chỉ vì supply scare thì AUD đi ngang — phân biệt 2 loại rally.
- Signal: trong 5 ngày oil +4%: AUDUSD cũng >+0.5% = demand-type.
- Trade: demand-type → giữ trend lâu (trail rộng); supply-type → chốt sớm (trail chặt).
- Risk: RBA policy nhiễu AUD.
- Data: AUDUSD + WTI · Coupling: SC futures (S50) cùng xác nhận demand Trung Quốc.

**S68 — Oil-JPY feedback exit (Cross-asset)**
- Hypothesis: khi oil spike đủ lớn gây risk-off, JPY mạnh → JPY strength là tín hiệu unwinding risk trades kể cả oil longs.
- Signal: oil ở đỉnh 20d & USDJPY break 20d low cùng phiên.
- Trade: thoát 50% oil longs, nâng stop cuối; không mở long mới 3 ngày.
- Risk: yield-driven JPY weaken che tín hiệu (2026: 10Y 5% giữ JPY yếu) → gate chỉ dùng khi yields flat.
- Data: USDJPY + oil + 10Y · Coupling: dùng kèm S10 kill-switch.

**S69 — Precious-metals basket relative strength (Cross-asset)**
- Hypothesis: trong shared-shock regime, phân bổ theo strongest-of {WTI, XAU, XAG} hàng tháng thắng buy-hold đơn lẻ vì shock luân chuyển energy → precious.
- Signal: rank 3-month momentum 3 symbol, hold top-1.
- Trade: monthly rebalance, vol-target chung 15%.
- Risk: whipsaw khi shock kết thúc cả nhóm.
- Data: daily 3 symbol · Coupling: mở rộng thành 12-symbol ở S90.

**S70 — EUR energy terms-of-trade pair (Cross-asset)**
- Hypothesis: oil spike làm EU (importer thuần) yếu tương đối → EURUSD xuống khi oil lên; cặp long WTI/short EURUSD capture shock được đếm 2 lần.
- Signal: oil 20d return z>1.5 & EURUSD break 20d low.
- Trade: long WTI + short EURUSD dollar-matched, exit khi oil trend kill.
- Risk: Fed hawkish mạnh hơn ECB → EUR lên tạm (decoupling).
- Data: EURUSD + WTI · Coupling: TTF gas châu Âu cùng spike xác nhận (ngoài universe, cần kiểm chứng data).

### 2.8 Positioning / Flows (S71–S80)

**S71 — COT managed-money extreme fade (Positioning)**
- Hypothesis: MM net-long z>2 (4+ năm) = fuel hết → 2–6 tuần counter-move trung bình.
- Signal: CFTC MM net position z-score >+2 (hoặc <−2) trên report hàng tuần (data Tuesday, release Friday).
- Trade: fade ngược cực đoan, entry Monday mở, T+4 tuần, stop 1.5×ATR(weekly).
- Risk: wartime regime giữ extreme cả năm (MM có thể persistent long 2026).
- Data: COT history + price · Coupling: S97 regime gate (backwardation → không fade long extreme).

**S72 — COT momentum confirm (Positioning)**
- Hypothesis: MM cộng position 4 tuần liên tiếp cùng giá tăng = new-money trend (không phải cover) → trend còn tiếp.
- Signal: ΔMM net 4 tuần >0 & price 4 tuần >0.
- Trade: cho phép S1 giữ xuyên pullback (không chết theo trail chặt).
- Risk: MM data chậm 3 ngày → thông tin cũ trong week nóng.
- Data: COT + daily · Coupling: S74 là chiều phản diện của cùng dữ liệu.

**S73 — Commercial-short extreme squeeze fuel (Positioning)**
- Hypothesis: producers short cực đoan khi giá thấp = hedge khổ; khi giá quay lên, short-cover tạo squeeze.
- Signal: commercial net-short z<−2 & giá vừa break 50dma lên.
- Trade: long theo break, stop dưới 50dma, T+3 tuần.
- Risk: commercial short đúng (cung thật thừa).
- Data: COT commercials + price · Coupling: term structure phải flat-to-backwardation.

**S74 — New-high-without-new-longs divergence (Positioning)**
- Hypothesis: giá lập đỉnh mới mà MM net không lập đỉnh = lực lượng mỏng → trend dễ đảo.
- Signal: price 20d new high & MM net < 80% đỉnh cũ.
- Trade: chốt 50% trend book, stop cuối → breakeven; không short ngược (chỉ thoát).
- Risk: passive/index flows thay MM làm chủ trend (thập kỷ 2020s).
- Data: COT + price · Coupling: OI (S75) đối chiếu.

**S75 — Open-interest surge trend confirmation (Positioning)**
- Hypothesis: breakout kèm OI tăng = new money; OI giảm = short-cover — chỉ dạng đầu bền.
- Signal: breakout 20d + OI 5d change >+3%.
- Trade: filter kích thước: +OI → full size; −OI → skip hoặc 0.3×.
- Risk: OI data delay (t+1 ngày).
- Data: OI futures + price · Coupling: chuẩn cho mọi breakout family 2.3.

**S76 — Liquidation-selloff contrarian buy (Positioning)**
- Hypothesis: selloff kèm OI giảm mạnh = long liquidation (không phải new shorts) → hết người bán thì bounce.
- Signal: 5-day price <−6% & OI <−5% & MM net vẫn dương lớn.
- Trade: long nhỏ khi xuất hiện hammer/absorption, stop dưới low, T+5–10 ngày.
- Risk: stage 2: new shorts vào sau đó → đợt 2 xuống.
- Data: OI + COT + price action · Coupling: S71 cùng logic positioning cực đoan.

**S77 — USO AUM flow fade (Positioning)**
- Hypothesis: retail oil sentiment (USO AUM tuần) cực đoan là counter-indicator — retail mua đỉnh panic.
- Signal: AUM weekly change z>2 cùng giá spike.
- Trade: fade 1–2 tuần, size nhỏ, stop 1×ATR(weekly).
- Risk: institutional flows qua USO làm nhiễu.
- Data: USO AUM/shares history (cần kiểm chứng nguồn free) · Coupling: MM COT cùng cực đoan → tăng conviction fade.

**S78 — 25Δ call-skew spike fade sau event (Positioning/Options)**
- Hypothesis: pre-event (EIA/OPEC/war) call skew phình; event qua không continuation → skew normalize nhanh.
- Signal: 25Δ call−put IV z>2 và event đã qua không có surprise lớn.
- Trade: short risk-reversal vol-matched, T+5 ngày, delta-hedge thô bằng spot.
- Risk: event chain (một loạt escalation) giữ skew cao.
- Data: options chain history · Coupling: chỉ khi escalation index giảm.

**S79 — Dealer gamma pin quanh strike lớn (Positioning/Options)**
- Hypothesis: strike lớn (round $100 như Sep-2026) có dealer gamma dày → giá bị hút về strike vào expiry tuần.
- Signal: strike có options OI lớn nhất + giá trong 0.7×ATR của nó vào expiry window.
- Trade: fade deviation về strike (pin trade), thoát expiry 14:00 ET.
- Risk: gamma flip (dealer đảo chiều) khi break khỏi strike.
- Data: options OI/chain · Coupling: vô hiệu trong 1 giờ quanh EIA.

**S80 — Front-month OI decay → roll pressure forecast (Positioning)**
- Hypothesis: tốc độ OI front decay trong roll window dự báo áp lực lên calendar spread.
- Signal: OI front decay nhanh hơn median lịch sử → spread nới theo hướng.
- Trade: trade calendar spread (S34 cấu hình) theo hướng áp lực trong roll window.
- Risk: passive roll ổn định làm tín hiệu phẳng dần theo thập kỷ.
- Data: OI per-tenor + roll calendar · Coupling: S38 execution complement.

### 2.9 Pattern / Pairs / Stat-arb (S81–S90)

**S81 — WTI–Brent beta-hedged z-score MR (Stat-arb)**
- Hypothesis: trong regime logistics bình thường, spread là Ornstein-Uhlenbeck quanh equilibrium vận chuyển (pipeline+freight); z cực đoan revert.
- Signal: spread residual sau Kalman beta-hedge z>±2; gate: KHÔNG có sanctions/pipeline event trong 30 ngày.
- Trade: 2 legs dollar-matched, stop 0.6σ, T+3 tuần.
- Risk: regime break (Sep-2026 $4→$12) — gate là sống còn.
- Data: cả 2 series + news gate · Coupling: freight (VLCC rates) là biến ngoại sinh phải monitor.

**S82 — WTI–NATGAS seasonal spread (Stat-arb)**
- Hypothesis: ratio oil/gas có chu kỳ năm (mùa đông gas, mùa hè oil); cực đoan ngoài seasonal band revert.
- Signal: ratio remove seasonal median z>±2.
- Trade: fade ratio 2 legs, T+4–6 tuần, stop 0.8σ.
- Risk: năng lượng chuyển đổi cấu trúc (coal-switching, LNG export) làm seasonal drift.
- Data: 2 series 10 năm+ · Coupling: EIA gas storage Thursdays.

**S83 — WTI vs USDCAD beta-residual pair (Stat-arb)**
- Hypothesis: tương quan −0.3/−0.5 để lại residual trade được: oil stronger-than-beta hoặc CAD weaker-than-beta đều revert về beta line trong 2–3 tuần.
- Signal: residual (WTI − β·(−USDCAD)) z>±2.
- Trade: trade residual bằng cặp, stop 0.7σ, T+3 tuần.
- Risk: BoC/tariff shock (Section 338 ảnh hưởng CAD — lane USDCAD) làm residual cấu trúc.
- Data: 2 series + rolling regression · Coupling: WCS spread data điều chỉnh.

**S84 — WTI vs 10Y-yield inflation pair (Stat-arb)**
- Hypothesis: trong inflation-regime, oil và yields cùng lên (breakeven tăng); khi cặp lệch nhau (oil lên, yields flat) → chân lag đuổi theo.
- Signal: 60d rolling corr(WTI, yield) >0.5 & cặp lệch z>1.5.
- Trade: long chân lag khi spread z恢复, T+2 tuần.
- Risk: Fed policy shock break pair tức thì.
- Data: 10Y futures/YTM + WTI · Coupling: breakeven 5y5y (S98) là biến xác nhận.

**S85 — Oil–gold beta regime detector (Stat-arb)**
- Hypothesis: rolling beta(WTI, gold) đổi dấu/cỡ là detector macro: dương mạnh = inflation-shock regime (trend-friendly); âm/zero = dollar-driven regime (MR-friendly).
- Signal: 60d beta >+0.4 → bật trend family; <0 → bật MR family.
- Trade: meta-switch giữa S1 và S13 theo beta.
- Risk: beta lag 60d chậm hơn regime change thật 2–4 tuần.
- Data: 2 series · Coupling: biến phân loại cho toàn lane, đo lại weekly.

**S86 — SC–WTI overnight info-arb (Stat-arb)**
- Hypothesis: phiên SC nhốt thông tin demand Trung Quốc lúc Mỹ đóng cửa; SC↑ đêm → WTI↑ mở NY có autocorrelation đáng kể.
- Signal: SC overnight return (close→open) z>1 và không tin Mỹ giữa chừng.
- Trade: long/short WTI tại reopen theo dấu, stop 0.5×ATR(H), exit 4–6 giờ.
- Risk: giờ giao dịch khác (SC break trưa) + capital controls làm tín hiệu nhiễu.
- Data: SC + WTI intraday (cần kiểm chứng) · Coupling: USDCNH cùng phiên cùng chiều.

**S87 — Time-of-day AR(1) microstructure (Stat-arb)**
- Hypothesis: persistence của 30m bar khác nhau theo giờ (NY cao, Asia thấp/thậm chí negative) — predictability theo lịch ngày.
- Signal: đo AR(1) coefficient theo khung giờ rolling 1 năm; khung |AR|>0.25 đáng trade.
- Trade: khung AR dương → continuation entry (S45); AR âm → fade entry (S19).
- Risk: cấu trúc nhảy khi liquidity regime đổi (24h liquidity 2020s).
- Data: M30 dài hạn · Coupling: kết quả喂 trực tiếp S91 gate.

**S88 — Hurst exponent regime switch (Stat-arb)**
- Hypothesis: H>0.55 = trending/persistent; H<0.45 = anti-persistent — chọn family strategy theo H đo trên 60 ngày.
- Signal: H(60d) qua R/S hoặc DFA.
- Trade: meta-switch trend/MR books.
- Risk: H ước lượng nhiễu (cần bootstrap CI); chuyển late 1–2 tuần.
- Data: daily rolling · Coupling: so với S85 (beta-based) — 2 detector độc lập vote.

**S89 — Failed-breakout (spring) reversal daily (Stat-arb)**
- Hypothesis: break 20d high bị thu hồi trong 2 ngày (close lại dưới) = bẫy thanh khoản; reversal ngược có edge vì stops của breaker bị quét.
- Signal: break rồi close-back-under trong ≤2 ngày.
- Trade: short tại close-back (hoặc long mirror với breakdown), stop trên false-break extreme, target middle 20d range.
- Risk: thật sự re-break ngày 3 (trend tiếp).
- Data: daily OHLC · Coupling: OI tăng trong break (S75) làm spring ít probable — skip.

**S90 — 12-symbol cross-sectional momentum (Stat-arb)**
- Hypothesis: trong universe FX+CMDT, momentum cross-section 3 tháng có spread return; WTI thường là chân mạnh nhất trong commodity-shock quý.
- Signal: rank 3m return 12 symbol, long top-3 / short bottom-3 dollar-neutral.
- Trade: monthly rebalance, vol-target mỗi chân.
- Risk: FX majors chiếm cả 6 chân → WTI đóng góp nhỏ khi không có commodity regime.
- Data: 12 series daily · Coupling: nối thẳng vào cross-lane backtest của chương trình FOREX-UNIFIED.

### 2.10 Regime-conditioned / Options-flavored (S91–S100)

**S91 — GARCH vol-percentile gate (Regime)**
- Hypothesis: trend strategies thắng ở vol trung-cao (40–90 percentile); MR thắng ở vol thấp (<40) — gate nâng expectancy chung của lane.
- Signal: GARCH(1,1) vol forecast percentile rolling 3 năm.
- Trade: meta-gate phân bổ vốn giữa 2.1–2.3 (trend) và 2.2 (MR).
- Risk: chuyển regime giữa chu kỳ FOMC làm percentile lag.
- Data: daily returns + GARCH fit · Coupling: S87/S88 là detector cùng lớp, cross-check.

**S92 — Conflict-escalation index long-only collar (Regime)**
- Hypothesis: đếm headline tấn công/tanker/sanction tuần (news classifier) tạo index 0–10; >6 = war regime → chỉ long (với collar), bỏ mọi short/MR.
- Signal: weekly escalation index (Kpler transit + headline count + confirmed incidents).
- Trade: long core + mua 1-month 5% OTM put collar, thoát khi index <4 hai tuần liên tiếp.
- Risk: classifier sai loại (đàm phán nhầm là escalation).
- Data: news feed + Kpler (cần kiểm chứng nguồn tự động hoá) · Coupling: index dùng chung cho S5/S12/S26/S43/S44.

**S93 — Short put spread trong backwardation + low inventory (Options)**
- Hypothesis: trạng thái thiếu barrel (backwardation + Cushing thấp) làm xác suất sập sâu thấp → bán put spread ăn premium có nền vật lý.
- Signal: CL1−CL2 >75th pct & Cushing <25M & escalation index <6.
- Trade: short 1-month put spread 5% OTM/10% OTM, size 1–2% NAV, quản lý đến expiry.
- Risk: ceasefire-crash (premium gỡ + vol nổ) — stop khi spread z co lại 50%.
- Data: options chain + curve + EIA · Coupling: đối trọng rủi ro với S31 long bias.

**S94 — Post-event vol-crush short straddle (Options)**
- Hypothesis: IV trước EIA/OPEC phình 2–4 vol points so với realized sau event (không surprise) → bán IV ngay khi event qua.
- Signal: IV − RV(20d sau event lịch sử) >2 points & event vừa qua không surprise.
- Trade: short straddle 1 tuần, delta-hedge 1 lần/ngày, stop vol +30%.
- Risk: event chain (một OPEC ra một OPEC khác — leak window).
- Data: options IV history + event calendar · Coupling: S78 skew variant — không chạy song song cùng chiều.

**S95 — Convex tail-hedge book (Options)**
- Hypothesis: phân bổ 1% NAV/quý mua straddle xa (3–6 tháng) trong hurricane + war regime tạo convexity trả 5–20× khi shock; chi phí thấp nhờ chọn timing mùa.
- Signal: vào Jun (hurricane) và khi escalation index 4–6 (chưa 8+ — IV còn thấp).
- Trade: straddle 10% OTM 4 tháng, roll quarterly, không stop-loss (đó là điểm của tail hedge).
- Risk: năm không có gì — mất 1%/năm, chấp nhận.
- Data: options chain + seasonal + escalation index · Coupling: bảo hiểm cho toàn trend book 2.1.

**S96 — Vol-targeting position sizing overlay (Regime)**
- Hypothesis: WTI vol thay 3–4× qua các regime (2020 → 2023 → 2026); sizing theo inverse-vol giữ risk ổn định và tránh chết vì đơn vị sai.
- Signal: target 15% annualized; N = target/RV20.
- Trade: overlay áp cho mọi ý 2.1–2.9; rebalance weekly.
- Risk: vol cao kéo dài làm size nhỏ đúng lúc trend lớn nhất (trade-off đã chấp nhận).
- Data: daily RV · Coupling: chuẩn mực sizing cho cả lane — mọi backtest sau phải dùng cái này.

**S97 — Term-structure sign meta-switch (Regime)**
- Hypothesis: backwardation → momentum family thắng (storage thiếu, trend có vật lý); contango → MR family thắng (storage thừa, ceiling vật lý) — quy tắc từ literature commodity.
- Signal: dấu CL1−CL2 chuẩn hoá 30 ngày.
- Trade: switch allocation 2.1–2.3 vs 2.2 theo dấu, confirm bằng slope 4 tuần.
- Risk: chuyển cấu trúc theo mùa storage (fall build) tạo whipsaw switch.
- Data: curve daily · Coupling: S36 là phiên bản chặt hơn (dùng thêm inventory) — chọn 1 khi backtest.

**S98 — Breakeven-inflation confirmation gate (Regime)**
- Hypothesis: oil trend "thật" (macro pricing-in inflation) có 5y5y breakeven cùng tăng; breakeven lăn xuống = oil rally chỉ là scare → chuẩn bị thoát.
- Signal: oil 20d up & breakeven 5y tăng >10bp cùng kỳ.
- Trade: giữ trend dài khi confirm; breakeven roll → chốt 50%.
- Risk: TIPS liquidity distortions 2020-style.
- Data: breakeven series + WTI · Coupling: S64 (SPX) và S84 (yields) cùng khối macro-confirm.

**S99 — Mid-term political-cycle short bias (Regime)**
- Hypothesis: gasoline >$4/gal trước mid-term (Nov-2026) tạo pressure chính trị buộc Washington hạ giá (SPR, diplomatic nhượng bộ, jawboning Saudis) → drift xuống nhẹ trong 6 tuần trước bầu.
- Signal: (gasoline avg >$4) & (ngày <60 trước bầu) & (escalation index giảm).
- Trade: bias short nhẹ (0.5×base) vào các ngày rally không có tin, cover ngay sau election.
- Risk: escalation thật trước bầu đảo ngược hoàn toàn (Sep-2026 chính là case ngược).
- Data: EIA gasoline price + political calendar (cần kiểm chứng cơ chế) · Coupling: S56 SPR-announcement là event chân cùng câu chuyện.

**S100 — Weekend strangle scaled theo Kpler transit counts (Options/Regime)**
- Hypothesis: transit counts Hormuz là thước physical-flow trực tiếp: counts sụt dưới ngưỡng → xác suất weekend event cao → mua weekend strangle size tỷ lệ độ tắc.
- Signal: weekly transit count <50% của median 8 tuần (Sep-2026 từng có 6 tàu/ngày).
- Trade: Friday mua Monday-expiry strangle, size 0.3–1.2% NAV theo độ tắc, thoát Monday 2 giờ sau mở.
- Risk: tuần im mất premium; counts recover giữa chừng (giảm size kịp).
- Data: Kpler/tracker (cần kiểm chứng tự động hoá) + options chain · Coupling: S44 (headline-trigger) + S92 (index) cùng gia đình weekend-risk.

---

## 3. Tổng hợp cho symbol

### 3.1 Top-10 ideas (đề xuất ưu tiên cho backtest đầu tiên)

| # | Idea | Vì sao ưu tiên |
|---|---|---|
| 1 | **S51** EIA composite surprise direction | Trục dữ kiện đẹp nhất của WTI: surprise history dài, cơ chế kinh tế rõ (algo chase), tách bạch khỏi flat-price noise; backtest rẻ (M1 quanh release + surprise) |
| 2 | **S31/S97** Backwardation gate + term-structure meta-switch | Cấu trúc vật lý đặc thù WTI (Cushing), literature ủng hộ, gate được cho cả lane; Sep-2026 là live proof 2 tầng tách rời |
| 3 | **S53** Cushing <20M long-bias | Ngưỡng vận hành vật lý hiếm hoi có sẵn "trigger số" — hiện đang 21.5M (9/2026), tức live test sắp tới |
| 4 | **S5** Geopolitical ignition continuation | Cách duy nhất kiếm tiền từ one-way war regime (Sep-2026 +5.2%/ngày); news classifier đơn giản: attacks vs diplomacy |
| 5 | **S35/S81** WTI–Brent spread (momentum + MR gated) | Cặp nội bộ sẵn trong universe; $4→$12 trong 1 tuần 9/2026 là payoff proof; dạy bài học regime gate |
| 6 | **S61** USDCAD crude-beta pair | Nối lane WTI ↔ lane USDCAD của cùng program; beta đo được, cơ chế kinh tế vững (energy export CAD) |
| 7 | **S44/S100** Weekend straddle/strangle | WTI là instrument duy nhất trong universe có event-risk tích luỹ 48h giải phóng 1 tick — gamma weekend là edge cấu trúc |
| 8 | **S71** COT MM extreme fade | Dữ liệu CFTC miễn phí, sạch, dài lịch sử; coupling với S97 để không fade wartime persistence |
| 9 | **S1** Donchian 20d + vol gate | Baseline trend chuẩn để đối chiếu mọi ý phức tạp hơn; nếu phức tạp không thắng baseline thì bỏ |
| 10 | **S96** Vol-targeting overlay | Không phải ý kiếm tiền mà là ý TRÁNH CHẾT — vol WTI đổi 3–4× giữa regime; không có overlay này mọi backtest khác đều sai đơn vị |

### 3.2 Bẫy overfitting đặc thù khi backtest WTI

1. **EIA timestamp & DST**: 10:30 ET = 14:30/15:30 UTC đổi theo daylight saving; bar 30m chứa release nếu align sai → mọi event strategy (S11/S21/S43/S51) bị thổi phồng hoặc đảo dấu. Build bằng M1 + timezone rõ ràng.
2. **Holiday-week shift**: tuần Monday-lễ → EIA dời Thursday; OPEC+ lịch không đều; không model thì event-map sai 4–6 tuần/năm.
3. **Contract roll & continuous series**: back-adjust phá giá tuyệt đối (percent return trên giá adjusted sai); roll monthly → 12 seam/năm; negative price 20/4/2020 ($−37.63) phá log/percent math. Dùng ratio-adjusted + xử lý outlier cấu trúc tường minh.
4. **Weekend gap không fill được**: backtest daily-close entry Monday không hiện thực — gap mở là giá giao dịch đầu tiên; S12/S26 phải model fill tại mở.
5. **Lookahead qua dữ liệu bị revise**: EIA weekly numbers được revise; COT là snapshot Tuesday release Friday; dùng bản release-date, không bản final.
6. **Regime contamination**: một cuộc chiến 7 tháng (Feb–Sep 2026) dominates sample gần — backtest 2024–2026 thực chất là "backtest cuộc chiến này"; bắt buộc regime-split (war/peace) + walk-forward.
7. **EIA whipsaw trong bar thấp hơn**: stop 0.3×ATR chết trong 20 giây đầu release; spread CFD nới 3–5× quanh 10:30 — model slippage theo lịch giờ, không hằng số.
8. **Seasonality drift**: driving season yếu đi sau 2020 (remote work, EV penetration); mùa 20 năm trước không còn đúng — seasonal ideas (S41/S49) phải dùng cửa sổ 10 năm + trend-adjust.
9. **Spread/stat-arb regime break**: cointegration WTI–Brent chết đúng lúc có payoff (sanctions, freight) — in-sample đẹp là bẫy; out-of-sample phải gồm 2022 & 2026.
10. **Chi phí CFD**: swap/overnight theo backwardation/contango đổi mỗi tháng — backtest "spread cố định 3 cents" sai lệch lớn trên chiến lược holding >1 tuần (S31/S33/S41).

### 3.3 MUST-WATCH weekly macro checklist (cho lane WTI)

**Mỗi tuần cố định** (giờ ET):

- **Mon**: weekend incident review (tanker/sanction/attack) → cập nhật escalation index (S92); gap map Monday Asia.
- **Tue**: API ~16:30 (prior cho S52); EIA STEO nếu tuần đầu tháng; kiểm OPEC+ calendar tuần.
- **Wed**: **EIA 10:30** — crude/gasoline/distillate/Cushing/exports/production/refinery utilization; đối chiếu consensus → surprise z; cập nhật Cushing trend (S53) và backwardation (S31).
- **Thu**: EIA natgas storage 10:30 (coupling S66/S82); nếu tuần lễ → EIA crude hôm nay.
- **Fri**: Baker Hughes rig 13:00 (S54); COT 15:00–15:30 (S71–S74); weekly review vị thế & kill-switches (S10/S96).

**Liên tục (không theo thứ)**:

- Kpler/tanker transit Hormuz + Saudi East-West pipeline repair progress (S35/S92/S100 — yếu tố quyết định tuần 21–25/9/2026, verified).
- NHC tropical outlook (15/5–30/11) (S20/S42/S57).
- DXY & 10Y yield (S58/S63/S65/S84 — Sep-2026: 10Y ~5%, Fed 3.75–4.00% sau hike 16/9, verified).
- Brent–WTI spread & freight (VLCC) — phát hiện spread-regime break sớm.
- SPR level & DOE announcements (đang 285M, đáy 1982 — S56/S99, verified).
- Lịch chính trị: mid-term 11/2026; UNGA/summit Mỹ–Gulf; Section 338 & auto-tariff 01/01/2027 (cross-lane USDCAD) — demand & trade-flow risk.

**Khung cảnh báo đặc biệt Sep→Oct-2026** (verified lane này): ceasefire-talks headline có thể gỡ $10–15 premium trong 1–2 tuần (giá về $70s như tháng 7-2026 từng xảy ra khi kỳ vọng MOU) — mọi long-bias strategy phải có S92 gate & stop ATR thực; mọi short-bias phải nhớ floor ≥$70 theo cấu trúc restocking (~450k bpd trong 3+ năm, ước tính Nuttall 9/2026).

---

*Hết file. 100 ý trên là hypothesis chưa test — không con số nào là kết quả backtest. Mọi tương quan/ngưỡng mốc phải re-measure trên checkout trước khi dùng.*
