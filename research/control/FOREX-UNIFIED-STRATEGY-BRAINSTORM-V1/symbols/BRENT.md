# BRENT (US Brent Oil) — Deep Dive & 100 Strategy Ideas

- Program: FOREX-UNIFIED-STRATEGY-BRAINSTORM-V1 · Lane: BRENT (UKOIL)
- Ngày: 2026-09-28 · Kiểu: knowledge-only brainstorm, KHÔNG backtest, KHÔNG data download
- Mọi con số tương quan/mức giá trong file là hypothesis cần re-measure; trạng thái thời sự Sep-2026 đã verify qua WebSearch (nguồn kèm cuối file), mục chưa verify đánh dấu **(cần kiểm chứng)**.

---

## 1. Bản chất instrument

### 1.1 Instrument & microstructure

- **UKOIL / "US Brent Oil"** tại broker (MT4/MT5, Exness/ICMarkes-style) là CFD **track hợp đồng futures Brent (ICE Europe)** tháng gần nhất — không phải spot dầu vật lý. Giá quote USD/thùng (USD/bbl), tick 0.01.
- **Underlying thật**: ICE Brent Crude Futures — benchmark giá cho **~2/3 dầu thô giao dịch toàn cầu** (cả нефte xuất khẩu Trung Đông/Nga/châu Phi ra biển thường price vs Brent). Giao dịch cơ sở trên rổ **BFOET** (Brent, Forties, Oseberg, Ekofisk, Troll) — chất lượng nhẹ ngọt, giao nhận **đường biển** (Sullom Voe và các terminal khác) → "benchmark biển".
- Contract size futures: 1,000 bbl/contract. CFD broker: 10–100 bbl/lot tuỳ broker **(cần kiểm chứng spec broker cụ thể)**.
- **Sessions**: ICE Brent electronic gần 24/5 (khoảng 01:00–23:00 London, trừ maintenance); CFD broker mở lại **Sunday ~22:00 London** và đóng **Friday ~21:45–22:00 London**. Thanh khoản đỉnh: **London 08:00–16:30** và **overlap London–NY 13:30–16:30 London (08:30–11:30 ET)**.
- **Asia session mỏng** (00:00–07:00 London): spread CFD nới 2–5×, nhưng đây lại là khung giờ **tin địa-chính-trị Middle East nổ ra** (Hormuz attacks, IRGC statements) → các cú gap/spike to bất thường in Asia là đặc trưng riêng của Brent 2026.
- **Gap cuối tuần**: Middle East cuối tuần là Fri/Sat (khớp market close Sat–Sun) → 48h tin tức dồn lại, Sunday reopen gap thường xuyên 0.5–2% trong war regime; trong peace regime gap nhỏ (<0.3%). Friday-close decision (flat/giảm size) là một risk decision thật, không phải chi tiết vặt.
- **Rollover futures tháng**: ICE Brent front contract cease trading **ngày làm việc cuối của tháng T-2 so với tháng giao hàng** (ví dụ contract Nov hết hạn cuối Sep). Broker roll UKOIL thường trước expiry vài ngày (thường Friday tuần expiry **(cần kiểm chứng lịch roll broker)**). Hậu quả: (a) swap/rollover charge 1 lần/tháng, (b) spread nới rộng 2–3 phiên quanh roll, (c) **back-adjusted vs unadjusted continuous series cho kết quả breakout khác hẳng nhau** — bẫy backtest số 1 của Brent.
- **Dữ liệu benchmark**: settlement futures ICE ~19:30 London (cửa sổ settle Brent **(cần kiểm chứng giờ hiện hành)**); OVX (CBOE Oil Volatility Index) là proxy implied vol **(cần kiểm chứng tính sẵn dùng)**.

### 1.2 Điểm ĐẶC BIỆT riêng Brent (so với FX pairs và cả WTI)

1. **Benchmark biển + rổ BFOET**: giá Brent phản ánh dầu **đường biển**, tức nhạy với freight, war-risk insurance, tanker routes — thứ WTI (pipeline về Cushing) không có. Đây là lý do **geopolitical premium cư ngụ chủ yếu ở Brent**, không phải WTI.
2. **OPEC+ lever**: phần lớn quota OPEC+ được price vs Brent → quyết định quota là "supply switch" trực tiếp của instrument này. Sep-2026: quota tăng +188 kbd/lần (4 lần liên tiếp từ sự kiện Hormuz), nhưng **spare capacity hiệu dụng chỉ ~0.22 mb/d** (ước tính Baratelli Institute 19-09-2026) → thị trường không tin nguồn cung thay thế → giá vẫn $100+.
3. **Geopolitical premium là một state ẩn**: Brent = fundamental value + risk premium; premium này trồi lên/rụng xuống theo headline (mẫu Sep-2026: $97 → $107 chỉ trong ~3 phiên quanh tin deal bị từ chối). Premium không quan sát được trực tiếp — proxy: Brent-WTI spread, war-risk insurance, timespread prompt.
4. **Term-structure information (backwardation/contango)**: đường cong futures là "thermometer" tightness. Backwardation sâu = thị trường physical căng (spare thấp, demand > supply) → long có roll-yield dương; contango = thừa供给/storage economics. Đây là thông tin **miễn phí, cập nhật liên tục** mà FX pairs không có — chiến lược Carry/Term-structure (Family D) khai thác đúng thứ này. Trạng thái cong cụ thể Sep-2026: prompt backwardation sâu được suy luận từ spare 0.22 mb/d + $100+, nhưng **độ sâu M1–M3 hiện tại (cần kiểm chứng)**.
5. **Brent-WTI spread** như instrument thứ hai: bình thường $3–6 (freight Mỹ–Châu Âu + quality), hiện **~$11–14** (Sep-2026: Brent ~$103–107, WTI ~$92–93) — mức nới rộng bất thường phản ánh supply-căng-biên-giới; spread này là cả signal (regime) lẫn đối tượng trade (stat-arb).
6. **Không có central bank backstop**: không có "lender of last resort" như FX (BOJ-style intervention) — nhưng có **OPEC+ như một "central bank của dầu"**: có can thiệp (quota), có forward guidance (MOMR), có "currency floor" ngầm (Saudi fiscal break-even). Tư duy "đọc OPEC+ như đọc Fed" là mental model đúng.
7. **Dựa vào dữ liệu định kỳ dày đặc** (EIA/OPEC/IEA monthly + weekly inventories) → surface area cho event-strategy lớn hơn mọi FX pair.

### 1.3 Tin tức & sự kiện ảnh hưởng

#### Scheduled (lặp lại, có lịch)

| Sự kiện | Thời gian | Kênh truyền (transmission channel) | Biên động điển hình |
|---|---|---|---|
| **OPEC+ meeting / JMMC** (2026: 7 nước chính họp online, ~1–2 lần/tháng) | Thường đầu tháng | quota (+/−188 kbd steps) → kỳ vọng supply → giá; "surprise vs expectation" mới quan trọng, không phải con số quota | $0.5–2; surprise lớn >$4 |
| **OPEC MOMR** (Monthly Oil Market Report) | ~10–15 hàng tháng | demand/supply revision (đặc biệt global demand growth) → drift 2–3 phiên | $0.5–1.5 |
| **IEA OMR** | ~giữa tháng | OECD stocks, supply call, SPR commentary | $0.5–1.5 |
| **EIA STEO** | Đầu tháng | forecast giá/demand → anchor kỳ vọng | $0.3–1 |
| **EIA Weekly Petroleum Status** (crude/gasoline/distillate inventories, implied demand) | **Wed 10:30 ET (15:30 London)** | inventory surprise → prompt tightness → timespread → giá | $0.5–1.5, đôi khi $2+ |
| **API weekly** | Tue sau close (~16:30 ET) | precursor EIA → positioning trước EIA | $0.3–1 |
| **Baker Hughes rig count** | Fri 13:00 ET | US supply tương lai (lead WTI, spill sang Brent) | $0.2–0.5 |
| **China official/Caixin PMI**; **China customs crude imports**; India PPAC | 1–2 tuần đầu tháng | China/India demand growth → cấu phần demand lớn nhất thế giới | $0.5–2 |
| **US CPI / FOMC / PCE** | theo lịch | USD & real rates → giá dầu tính bằng USD; demand-fear khi rates spike | $0.5–2 |
| Month-end **futures roll & options expiry** (ICE) | cuối tháng | volume migration front→second; micro-structure noise quanh roll | nới spread, không direction |

#### Unscheduled (không lịch — đây là thịt của Brent 2026)

| Sự kiện | Kênh truyền | Ghi chú Sep-2026 |
|---|---|---|
| **Hormuz tanker attacks / mines / seizures** | ~20% dầu thế giới + đáng kể LNG đi qua Hormuz → war-risk premium & insurance repricing trong phút → physical differentials → Brent | Iran tuyên bố bắn 19 tàu trong 48h; mìn đã gài; nổ vẫn nghe trong eo dù đang đàm phán (Al Jazeera 27-09) |
| **Đàm phán Mỹ–Iran / ceasefire headlines** | probability-weighted risk premium vào/ra | Iran đề nghị deal 7 ngày mở lại Hormuz; **Trump từ chối 26-09**; hai bên xa deal → Brent bật từ ~$97 lên $103–107 |
| **IRGC/military statements** (mở rộng vùng đe doạ ra Indian Ocean) | escalation surface mở rộng → premium | IRGC dọa đánh tàu Mỹ ngoài Indian Ocean — nâng "bán kính rủi ro" vượt khỏi Hormuz |
| **Sanctions (OFAC: Russia shadow fleet, Iran, Venezuela); price-cap G7 thay đổi** | differentials + freight + chất lượng rổ BFOET | thường drift nhiều ngày thay vì gap |
| **OPEC+ emergency meeting / Saudi statement** | quota expectation | Saudi thường "hút thính" bằng nguồn tin Reuters trước |
| **Libya/Nigeria/Kazakhstan outages** | supply mất trực tiếp vs Brent | cổ điển: Libya force majeure |
| **SPR release / refill (US, China)** | supply tạm thời / demand chiến lược | SPR US đã cạn sâu sau 2022 → đạn ít (cần kiểm chứng mức hiện tại) |
| **Hurricane GOM (Jun–Nov)** | chủ yếu WTI nhưng lan cả complex | spillover 1–2 phiên |
| **Kinh tế choáng (recession scare)** | demand destruction fear | oil rơi nhanh hơn cả SPX trong fade |

### 1.4 Thông số ảnh hưởng (drivers) — thứ tự ưu tiên theo regime

1. **OPEC+ policy & compliance & spare capacity** — regime war: spare 0.22 mb/d làm mọi quota hike thành "giấy" (output thực tế tụt sau quota vì war disruption).
2. **Inventories & term structure** — OECD stocks vs 5-yr avg; M1–M3 slope là tổng hợp nhanh nhất của physical tightness.
3. **China/India demand** — import run-rate, teapot refinery runs, EV penetration (xu hướng dài hạn bào mòn demand growth xăng dầu).
4. **USD & real rates** — DXY âm với Brent (đồng-đô-la kênh); real-rate jump → khấu khấu future cash của mọi commodity → oil chịu.
5. **Refinery maintenance seasonality** — spring (Feb–Apr) & autumn (Sep–Oct) turnaround làm giảm crude demand; driving season (May–Aug) & heating (Nov–Feb) nâng.
6. **Geopolitical risk premium** — war-risk insurance rates, tanker traffic (AIS), headline intensity.
7. **Speculative positioning** — COT managed money net long (extremes → squeeze/fade).
8. **Cross-energy substitution** — TTF/Henry Hub vs oil (fuel-switching quyền năng ở châu Âu/Châu Á đã giảm sau 2022 nhưng vẫn có).
9. **Macro risk appetite** — SPX/credit; phân biệt supply-led oil-up (SPX down) vs demand-led oil-up (SPX up) là **phân loại regime quan trọng nhất** (xem S64, S98).

### 1.5 Correlation map (BRENT vs 11 symbol trong universe)

Số liệu là **khoảng giả định theo regime** tổng hợp từ hiểu biết thị trường, CHƯA re-measure — phải đối chiếu bằng dữ liệu thật trước khi dùng (mission invariant: hypothesis ≠ PASS).

| Symbol | Corr giả định (daily returns) | Kênh truyền | Breakdown theo regime |
|---|---|---|---|
| **WTI** | **+0.92 → +0.97** (cao nhất hệ thống) | cùng commodity, khác location/quality | corr giảm nhẹ khi US-specific news (EIA/Cushing, GOM hurricane); **spread là variable riêng** — hiện $11–14, bình thường $3–6 |
| **USDCAD** | **−0.35 → −0.60** | CAD petro-currency; terms of trade; TSX energy weights | mạnh nhất khi oil-led moves; yếu khi BoC policy diverge; giữa 2022 kiểu "oil lên + Fed hawkish hơn BoC" từng làm corr gãy |
| **AUDUSD** | +0.25 → +0.45 | commodity beta + China demand proxy | cao trong risk-on inflation regime; tách rời khi RBA/China-specific |
| **NZDUSD** | +0.15 → +0.35 | risk beta bậc thang | giống AUD, beta thấp hơn |
| **USDJPY** | **bimodal**: +0.15 (inflation/rates regime) / −0.30 (geo risk-off) | oil↑→US yields↑→JPY cross-carry; nhưng JPY haven trong geo shock | trung bình dài hạn ~0 — **tuyệt đối không dùng corr tĩnh** |
| **USDCHF** | −0.20 → −0.35 | CHF haven + gold link (SNB) | sâu hơn trong geo stress |
| **EURUSD** | +0.10 → +0.20, **đuôi âm** trong energy crisis | kênh USD (DXY yếu → cả hai lên) vs Europe oil-import bill (spike làm EUR yếu, mẫu 2022) | gần zero trung bình; chỉ trade được theo regime |
| **GBPUSD** | +0.15 → +0.25 | North Sea legacy (UK giờ là importer ròng); BoE inflation channel | dễ break khi UK-specific fiscal events |
| **XAUUSD** | +0.25 → +0.50 | inflation hedge + USD debasement + geo hedge | corr cao nhất trong geo stress (cả hai hedge cung一场); tách rời khi real rates spike (gold xuống, oil đi theo demand) |
| **XAGUSD** | +0.20 → +0.35 | gold beta + industrial | yếu hơn gold trong geo stress (risk-off hurting industrial) |
| **NATGAS** | +0.10 → +0.25 | Henry Hub = US/weather-driven, gần như tách fundamental | chỉ co-move trong broad energy shock (Hormuz chặn cả LNG); fuel-switching yếu |

**Điểm dùng được**: (a) WTI như "same-asset hedge/confirm" (hệ số cao & ổn định nhất); (b) USDCAD như petro-confirm chéo; (c) gold như geo-stress co-factor; (d) SPX (ngoài universe nhưng dùng làm filter) như supply-vs-demand-shock classifier.

### 1.6 Note trung thực — họ strategy nào HAY CHẾT trên Brent

- **Mean-reversion chết trong supply-shock trend**: 1990, 2003, 2022, 2026 — mọi hệ "fade về mean" bị cuốn khi $90→108 một mạch. MR chỉ sống khi có **regime gate** (term structure, headline intensity).
- **Breakout chết bởi headline fakes**: geopolitical breakout thường retrace 100% trong cùng phiên (mẫu deal-bị-từ-chối 26-09: bật lên rồi xoài). Breakout không có "materiality check" (supply thật mất hay chỉ headline) là mồi.
- **Trend-following chết trong war/peace ping-pong**: Sep-2026 whipsaw $90→108→90→104 đánh kill trend chậm; chỉ trend có **fast trailing + vol-target** sống sót.
- **Carry/term-structure chết khi curve flip**: ceasefire 1 tin → backwardation sâu thành flat trong ngày; carry position không có stop theo slope-change thì chết sạch.
- **Pairs/Stat-arb chết khi spread regime shift**: Brent-WTI từ $4 sang $14 — mọi cointegration parameter ước lượng trong peace regime vô hiệu hoá.
- **Session/ToD patterns chết khi Asia có headline**: Asia-range breakout dựa vào "Asia yên tĩnh" — giả định này sai trong 2026.
- **Seasonality bị war override**: driving-season long mà gặp supply shock ngược → mất dấu.
- **Positioning (COT) chết vì lag 3 ngày +战争**: dữ liệu Tue, công bố Fri; trong tuần war headlines thì signal cũ như báo hôm qua.
- **Chung**: weekend gap là rủi ro tail cho MỌI họ; sizing phải tính jump-risk, không chỉ ATR.

---

## 2. 100 Strategy Ideas

Quy ước: mọi ý là hypothesis chưa test. `D1/H4/H1/M15` = khung thời gian; `ATR` = Average True Range; `M1/M3/M6` = futures month; `OVX` = oil implied vol index; `MM` = managed money (COT); `ToT` = terms of trade.

### Family 1 — Trend / Momentum (S1–S10)

- **S1 — Donchian 20/55 War-Filtered (Trend/Momentum)**
  Hypothesis: xu hướng Brent có độ bền cao vì driver (war/OPEC+) là process nhiều tuần, không phải noise.
  Signal: break 20-bar high/low trên D1 với filter ADX(14)>20; size halved khi OVX>60 · Trade: entry stop-order tại channel edge, stop 2×ATR(14), trail 3×ATR · Risk: whipsaw $90↔108 chop giết bằng đường chéo · Data: D1 OHLC broker + OVX · Coupling: backwardation dương cùng chiều.

- **S2 — Dual-Timeframe MACD Alignment (Trend/Momentum)**
  Hypothesis: momentum W1 + H4 cùng dấu lọc bỏ nửa tín hiệu giả.
  Signal: W1 MACD histogram cùng dấu + H4 MACD cross cùng hướng · Trade: entry H4 close, stop dưới swing H4, target 4R rồi trail · Risk: lag lớn bỏ qua phần đầu move war-driven · Data: W1+H4 · Coupling: Brent-WTI spread cùng hướng xác nhận.

- **S3 — 200DMA Regime Pullback Continuation (Trend/Momentum)**
  Hypothesis: trong bull-regime (giá > 200DMA), pullback về 20/50EMA là điểm vào có reward/risk tốt nhất.
  Signal: giá > 200DMA(D1) + pullback chạm 50DMA không đóng xuyên · Trade: buy limit 50DMA, stop 1.5×ATR dưới 200DMA, target đỉnh cũ · Risk: death-by-a-thousand-cuts khi giá cạo 200DMA · Data: D1 · Coupling: inventories không build liên tiếp 3 tuần.

- **S4 — ATR-Normalized Momentum (Trend/Momentum)**
  Hypothesis: chuẩn hoá return theo vol làm momentum so sánh được giữa peace và war regime.
  Signal: sum(return/ATR, 10 ngày) > +3 → long bias; < −3 → short bias · Trade: vào theo giờ cố định, stop 2×ATR hiện hành, size = target vol 15% annualized · Risk: vol burst làm ATR stale ngay sau event · Data: D1 + ATR · Coupling: term-structure slope cùng dấu.

- **S5 — Time-Series Momentum 3/12 (Trend/Momentum)**
  Hypothesis: TSMOM đa chu kỳ (khoan 3M/1Y) là cấu trúc robust nhất cho commodity có regime rõ.
  Signal: return 3M và 12M cùng dấu · Trade: position định kỳ tháng, vol-target 12%, không intraday stop (stop theo tín hiệu đảo) · Risk: whipsaw ở lằn ranh regime; drawdown dài khi oil ranging 2015–2017 style · Data: monthly continuous back-adjusted · Coupling: slope M6–M12 cùng dấu (deficit/surplus dài hạn).

- **S6 — ADX-Gate Trend-Only Mode (Trend/Momentum)**
  Hypothesis: chop và trend là hai trạng thái đo được; chỉ giao dịch trạng thái trend.
  Signal: ADX(14) D1 > 25 và DI+ ≠ DI− · Trade: theo hướng DI mạnh, entry pullback 38.2% của swing gần nhất, stop dưới swing · Risk: ADX confirm muộn trong V-reversal war headline · Data: D1 · Coupling: headline-intensity thấp (S91) mới bật hệ này.

- **S7 — Brent-WTI Relative-Strength Confirm (Trend/Momentum)**
  Hypothesis: khi spread Brent-WTI nới cùng hướng giá Brent, đó là supply-căng thật sự (không phải noise).
  Signal: Brent break 20-day high VÀ spread Brent−WTI ở >75th percentile 60 ngày · Trade: long Brent, stop 2×ATR, target 3R · Risk: spread vì lý do US-specific (WTI yếu do Cushing build) → signal sai hướng gốc · Data: BRENT + WTI daily · Coupling: corr(Brent,WTI) rolling > 0.9.

- **S8 — Weekend-Gap Continuation in War Regime (Trend/Momentum)**
  Hypothesis: trong war regime, gap Sunday chứa thông tin (48h tin Middle East) và continuation có xác suất cao hơn revert.
  Signal: gap Sunday reopen > 1×ATR(D1) theo hướng xu hướng 200DMA · Trade: enter at London open nếu gap không fill 50%, stop dưới gap-low, target 2×gap size · Risk: peace-regime gap là ngược lại (thường fill) — phải gate regime · Data: Sunday opens + war-state flag · Coupling: tin tanker/insurance trong cuối tuần cùng hướng.

- **S9 — Chandelier-Thrust Rider (Trend/Momentum)**
  Hypothesis: war-thrust (đà 3+ bar cùng hướng, body lớn) có autopilot; trail nhanh giữ được đuôi.
  Signal: 3 bar D1 cùng hướng, mỗi bar close > high bar trước; ATR đang tăng · Trade: enter bar 4, chandelier exit = 3×ATR từ đỉnh cao nhất · Risk: tin đối nghịch đảo chiều thrust trong 1 bar · Data: D1 · Coupling: only khi OVX tăng (thrust thật) chứ không phải OVX flat.

- **S10 — Back-Adjusted-Series Methodology Guard (Trend/Momentum)**
  Hypothesis: nhiều "edge" của Brent trend là artefact roll; đúng quy trình (back-adjusted, roll-date skip) là điều kiện sống của mọi hệ trend.
  Signal: so sánh backtest trên continuous back-adjusted vs unadjusted — chỉ giữ hệ whose signals khác < 20% giữa hai chuỗi · Trade: n/a (meta-rule áp cho mọi hệ trend) · Risk: bỏ qua → overfit artefact roll-yield · Data: futures continuous + roll calendar ICE · Coupling: dùng chung cho Family A/D.

### Family 2 — Mean-reversion (S11–S20)

- **S11 — RSI(2) Fade với Term-Structure Gate (Mean-reversion)**
  Hypothesis: Brent oversold cực đoan hồi về mean khi KHÔNG có supply-shock đang chạy.
  Signal: RSI(2) D1 < 5 VÀ M1−M3 spread ≥ 0 (không deep contango) VÀ không có war-escalation headline 48h · Trade: buy close, thoát RSI(2)>60, stop 1.5×ATR · Risk: gate thủng khi war news lọt khe · Data: D1 + futures curve + news flag · Coupling: inventories không build.

- **S12 — Bollinger %B Snapback (Mean-reversion)**
  Hypothesis: chạm dải ±3σ D20 tự nhiên hồi dải giữa trong regime ranging.
  Signal: %B < 0.02 hoặc > 0.98, sau đó bar đóng ngược vào trong dải · Trade: enter bar kế, target mid-band, stop ngoài extreme bar · Risk: bùng nổ supply-shock đi 3 dải liền · Data: D1 Bollinger(20,3) · Coupling: ADX<20 (S6 phủ định).

- **S13 — Weekly Reversion to 20-Week Mean (Mean-reversion)**
  Hypothesis: lệch nhiều tuần khỏi mean trung bình dài xảy ra chủ yếu do premium emotion, tàn dần.
  Signal: z-score close vs SMA20(W1) < −2 và W1 close > SMA40 (bull context) · Trade: scale-in 2 mép, target SMA20, stop khi z < −3.5 · Risk: demand-destruction collapse (z đi −5) · Data: W1 · Coupling: curve không deepening contango.

- **S14 — Asia-Spike Fade at London Open (Mean-reversion)**
  Hypothesis: spike Asia giờ mỏng liquidity thường overshoot; London vào lùi về.
  Signal: Asia session (00:00–07:00 London) move > 1.2×ATR(H1,20d avg of session) không kèm supply-loss confirmed (chỉ statement/rumor) · Trade: fade ngược hướng tại 08:00–08:30 London, target 50% spike, stop ngoài spike-extreme + 0.3×ATR · Risk: nếu tin là supply-loss THẬT → spike không revert · Data: H1 + tin real-time · Coupling: tanker-tracking/AIS xác nhận không mất tải.

- **S15 — Failed-Breakout Reversal (Mean-reversion)**
  Hypothesis: geopolitical breakouts không có materiality (không mất barrel thật) có xác suất fail ngược cao nhất.
  Signal: giá xuyên 20-day high > 0.5×ATR rồi CLOSE lại dưới mức đó trong cùng D1 · Trade: short at close, stop trên high of day + 0.25×ATR, target 20-day mid-range · Risk: breakout thật đến trễ (mất tải xác nhận sáng hôm sau) · Data: D1 + materiality check · Coupling: volume không xác nhận (<1.3× avg).

- **S16 — Streak-Day Reversal, no-OPEC week (Mean-reversion)**
  Hypothesis: 4+ ngày cùng hướng không có event → exhaustion thống kê.
  Signal: 4 ngày D1 cùng dấu close-to-close, tuần không có OPEC/EIA-triple-week… (gate: không có scheduled event trong 48h tới) · Trade: fade day 5 open, target 1×ATR, stop 1×ATR · Risk: streak do escalation liên tiếp (mỗi ngày một tin) — gate news bắt buộc · Data: D1 + event calendar · Coupling: OVX flat (không panic).

- **S17 — Hurst-Regime Gated MR (Mean-reversion)**
  Hypothesis: chỉ fade khi chuỗi có memory mean-reverting đo được.
  Signal: Hurst exponent rolling 100 ngày < 0.45 · Trade: fade z-score |z|>2 của price vs SMA50, target z=0, stop |z|=3 · Risk: Hurst nhảy trên/dưới ngưỡng giữa chừng · Data: D1 + Hurst calc · Coupling: term structure flat.

- **S18 — Range-Mid Fade in Consolidation Cluster (Mean-reversion)**
  Hypothesis: consolidation 15+ ngày có "magnet" mid-range khi không có driver mới.
  Signal: 15 ngày trong band rộng 3×ATR; giá chạm mép band lần 2+ · Trade: fade tại mép, target mid, stop 0.5×ATR ngoài mép · Risk: OPEC meeting tới gần trong < 3 ngày → skip · Data: D1 · Coupling: curve flat & OVX decreasing.

- **S19 — OVX-Spike Price-Pop Fade (Mean-reversion)**
  Hypothesis: khi implied vol nổ nhưng supply không mất thật, giá pop được "mượn" từ vol — hai thứ đều revert.
  Signal: OVX 1-day jump > 20% VÀ price jump > 2×ATR VÀ không supply-loss confirmed · Trade: fade ngược hướng sau 2 bar H4, stop ngoài extreme, target pre-event price · Risk: war loop nhiều đợt (OVX nổ tiếp) · Data: OVX + H4 · Coupling: war-risk insurance rates flat (chỉ headline).

- **S20 — Weekend Gap-Fill in Peace Regime (Mean-reversion)**
  Hypothesis: peace-regime gap Sunday là noise thanh khoản → fill trong 2–3 ngày.
  Signal: gap < 0.8×ATR và war-state flag = OFF · Trade: trade ngược hướng gap Monday London, target gap-close, stop 0.7×ATR từ entry · Risk: gap đúng hướng tin thật (gate war-state bắt buộc) · Data: Sunday opens + war flag · Coupling: S91 regime router phải ghi "peace".

### Family 3 — Breakout / Vol-expansion (S21–S30)

- **S21 — London Open Range Breakout (Breakout/Vol-expansion)**
  Hypothesis: 30 phút đầu London là price-discovery của châu Âu; break range đó có follow-through trong ngày.
  Signal: break high/low của 08:00–08:30 London range > 0.25×ATR(H1) · Trade: stop-order tại mép, stop mép kia của range, target 2× range-height · Risk: false-break hai chiều trong 08:30–09:00 · Data: M5/M15 · Coupling: hướng break trùng D1 trend.

- **S22 — NY Open Momentum + EIA Overlay (Breakout/Vol-expansion)**
  Hypothesis: NY open (09:30 ET) kế thừa momentum London; Wednesday có EIA 10:30 ET khuếch đại.
  Signal: hướng của London session + break NY first-15m range cùng hướng · Trade: entry 15m break, stop 1×ATR(H1), Wednesday: chỉ vào sau khi EIA in ra và retrace 38% · Risk: EIA ngược hướng cắt stop cả position Tuesday-style · Data: M15 + EIA calendar · Coupling: gasoline implied demand trend cùng hướng.

- **S23 — NR7 Compression Breakout (Breakout/Vol-expansion)**
  Hypothesis: ngày có range hẹp nhất trong 7 ngày (NR7) đi trước expansion (vol clustering).
  Signal: NR7 D1 + inside-day tăng cấp · Trade: straddle-order hai mép NR7 day + 0.1×ATR hôm sau, stop 1.2×ATR, target 2.5×ATR · Risk: breakout ngay trong Asia mỏng → fill xấu; chỉ đặt order từ London · Data: D1 · Coupling: scheduled event < 2 ngày → size nhỏ (direction sẽ do event chọn).

- **S24 — Pre-OPEC Bracket Breakout (Breakout/Vol-expansion)**
  Hypothesis: thị trường co trước OPEC; quyết định quota chọn hướng và move có continuity.
  Signal: 3 phiên trước OPEC/JMMC có range < 0.8× avg; bracket hai mép range đó · Trade: stop-order hai mép ngay trước giờ họp, stop 1×ATR, target 3R, thoát nếu 2 phiên không đạt 1R · Risk: "no-change + statement" gây whipsaw hai mép · Data: D1 + OPEC calendar · Coupling: tin rò rỉ (Reuters whisper) khớp hướng break.

- **S25 — ATR-Expansion Breakout (Breakout/Vol-expansion)**
  Hypothesis: vol gấp đôi + break cấu trúc = chế độ trending mới thật.
  Signal: ATR(5)/ATR(50) > 1.8 VÀ close ngoài 10-day high/low · Trade: enter close, stop 1.5×ATR mới, target theo 3×ATR trail · Risk: expansion do 1 event duy nhất rồi co lại · Data: D1 · Coupling: OI tăng (futures) xác nhận dòng tiền.

- **S26 — Keltner Squeeze Release with Curve Direction (Breakout/Vol-expansion)**
  Hypothesis: hướng của vol-release được quyết định bởi fundamental tightness (đường cong), không random.
  Signal: Bollinger nằm trong Keltner ≥ 5 ngày (squeeze); hướng break lấy dấu M1−M2 slope (backwardation → long-side break ưu tiên) · Trade: chỉ trade break cùng dấu slope; stop 1×ATR, target 2.5×ATR · Risk: release ngược dấu slope 1 lần rồi quay lại · Data: D1 + futures curve · Coupling: inventories draw cùng dấu.

- **S27 — Asia Range Sweep Breakout (Breakout/Vol-expansion)**
  Hypothesis: sweep (quét qua) low/high Asia tại London open là liquidity grab; break thật là break có close.
  Signal: giá quét qua Asia extreme trong 07:00–09:00 London nhưng H1 close quay lại trong range → false; H1 close ngoài range → true break · Trade: chỉ trade true-break, stop về Asia mid, target 1.5× Asia range · Risk: breakout một chiều duy nhất vào ngày EIA · Data: H1 · Coupling: hướng D1 trend.

- **S28 — Monday Weekly-Opening-Range Breakout (Breakout/Vol-expansion)**
  Hypothesis: Monday mở tuần mới gói tin cuối tuần; break OR Monday định tone tuần.
  Signal: break Monday first-hour range (London) > 0.5×ATR(D1) · Trade: enter, stop OR opposite, hold-to-Friday với trail 2×ATR · Risk: tone tuần đảo giữa chừng vì event; rút về flat-by-Friday trong war regime · Data: H1 + weekly view · Coupling: S8 gap-direction cùng dấu.

- **S29 — Volume/OI-Confirmed Breakout (Breakout/Vol-expansion)**
  Hypothesis: breakout không volume/OI là liquidity vacuum; có new money thì mới continuation.
  Signal: 20-day break + futures volume > 1.5× 20d avg + OI tăng > 3% (ngày kế) · Trade: enter khi OI-confirm, stop 1.2×ATR, target 3R · Risk: OI data lag 1 ngày (ICE) · Data: D1 + futures vol/OI (broker có thể thiếu → cần data phụ) · Coupling: managed-money net cùng hướng tăng (COT).

- **S30 — News-Tail Momentum Candle (Breakout/Vol-expansion)**
  Hypothesis: candle 15m khổng lồ (2×ATR 15m) ngay sau headline có continuation trong phiên — thị trường định giá phân phối, không one-shot.
  Signal: post-headline M15 body > 2×ATR(M15,20) · Trade: enter break of candle-extreme retracement (38–50%), stop ngoài candle origin, target 2× candle-height · Risk: headline bị phủ nhận (denial) trong 1h · Data: M15 + news feed · Coupling: second-source confirm (Reuters+AP cùng tin) trước khi vào.

### Family 4 — Carry / Term-structure (S31–S40)

- **S31 — Backwardation Long-Tilt (Carry/Term-structure)**
  Hypothesis: backwardation M1−M3 là tín hiệu tightness + roll-yield dương; long trong trạng thái này có tail-wind hai lớp.
  Signal: M1−M3 spread > +0.5% of price (annualized roll > 2%) · Trade: long bias D1 trend-định-khiểm (enter pullback), position core + tactical, stop slope-based (thoát khi slope về < 0) · Risk: ceasefire → slope flip một phiên · Data: futures curve daily · Coupling: inventories dưới 5-yr avg.

- **S32 — Contango Short-Bias / No-Long Filter (Carry/Term-structure)**
  Hypothesis: contango sâu = surplus có thật; long có chi phí roll âm và head-wind fundamental.
  Signal: M1−M3 < −0.5% of price · Trade: hoặc short-bias rally-fade, hoặc overlay cấm long cho mọi hệ khác · Risk: contango đáy → policy pivot (OPEC cut) gây squeeze · Data: futures curve · Coupling: inventories trên 5-yr avg.

- **S33 — Slope-Change Momentum (Carry/Term-structure)**
  Hypothesis: thay đổi slope (dF/dt) dẫn đầu giá: curve steepens trước khi giá trend.
  Signal: Δ(M1−M2) 5 ngày > +0.8× σ60 của chính nó · Trade: long spot-proxy cùng hướng steepening, stop khi Δ revert 50%, target ATR-multiple 2.5× · Risk: slope noise quanh roll dates · Data: M1, M2 daily closes · Coupling: OPEC+ policy direction cùng dấu.

- **S34 — Roll-Window Micro-Avoidance (Carry/Term-structure)**
  Hypothesis: 3 phiên quanh broker roll có spread-cost + noise không có edge kỳ vọng.
  Signal: roll calendar broker (1/tháng) · Trade: flatten/or reduce 50% hệ thống trong cửa sổ roll ±1 phiên; không mở position mới · Risk: bỏ lỡ move thật đúng roll-week (hiếm nhưng có) · Data: broker roll calendar + lịch ICE expiry · Coupling: S47 (roll micro-pattern) đối chiếu.

- **S35 — Full-Carry Contango Fade (Carry/Term-structure)**
  Hypothesis: khi M1−M2 contango chạm ngưỡng full-carry (storage+finance), front đã priced tồn kho tối đa → mean-revert về trong band carry.
  Signal: (M2−M1)/price annualized > 12–15% (proxy full carry Brent storage **cần kiểm chứng tham số**) · Trade: long front-proxy (CFD) + short M2 nếu có futures; CFD-only: long bias D1 với stop thời gian 10 ngày · Risk: storage đầy thật (2020-style) → band bị xuyên · Data: curve + storage rates · Coupling: OECD stocks không còn tăng.

- **S36 — Convenience-Yield / Inventory Divergence (Carry/Term-structure)**
  Hypothesis: prompt spread là convenience yield; khi spread và inventory đổi nhau, một trong hai sai — inventory (survey, lag) hay spread (real-time) → tin spread.
  Signal: spread M1−M2 steepen trong khi EIA báo build 2 tuần liên tiếp · Trade: long theo hướng spread (fade tin inventory), stop khi spread flat, target 2×ATR · Risk: build là thật → spread sập theo sau · Data: curve + EIA weekly · Coupling: tanker imports data cùng spread.

- **S37 — Carry + Trend Combo Gate (Carry/Term-structure)**
  Hypothesis: long chỉ khi cả fundamental (backwardation) và technical (>50DMA) cùng nói — twin-engine có survival cao nhất.
  Signal: M1−M3 > 0 VÀ close > 50DMA(D1) · Trade: long pullback 20EMA, stop 2×ATR, exit khi MỘT trong hai điều kiện gãy (AND-gate exit) · Risk: điều kiện gãy đồng thời tại đỉnh → exit muộn · Data: curve + D1 · Coupling: USD không ở rally mạnh.

- **S38 — Post-War Curve Flattener (Carry/Term-structure)**
  Hypothesis: war premium cư ngụ ở front (M1–M2); khi premium decay, front rụng nhanh hơn deferred → flattener.
  Signal: war-state ON→OFF chuyển trạng thái (S91) VÀ M1−M2 vẫn ở > 90th percentile lịch sử · Trade: short M1 / long M3 (futures cần); CFD-only: short front CFD size nửa, hedge bằng long WTI-far-month ETF nếu có — hoặc chỉ short nhỏ · Risk: war bật lại ON → steepen tiếp · Data: ICE calendar futures + regime flag · Coupling: insurance rates giảm.

- **S39 — Negative-Roll Overlay cho CFD Systems (Carry/Term-structure)**
  Hypothesis: hệ CFD long-held trong contango âm lặng lẽ mất roll-cost; overlay loại bỏ phần lớn chi phí vô hình.
  Signal: trước khi vào long đa ngày, check roll state (broker swap history + curve) · Trade: nếu negative-roll > 6%/yr → chỉ cho phép intraday long hoặc giảm size 50% · Risk: bỏ lỡ bull-market trong contango đầu chu kỳ (2016-style) · Data: broker swap + curve · Coupling: dùng chung mọi Family A.

- **S40 — Deferred Slope Long-Cycle Signal (Carry/Term-structure)**
  Hypothesis: slope M6–M12 (phần "structurural" của curve, ít war-noise) là tín hiệu deficit/surplus đa năm.
  Signal: M6−M12 slope > +1%/yr duy trì 20 phiên (structure backwardation dài hạn) · Trade: core long tái cân bằng tháng, size cố định nhỏ (5% risk), không stop intraday — stop theo slope flip · Risk: structural shift chậm làm capital cost cao · Data: futures deferred · Coupling: China demand trend cùng dấu.

### Family 5 — Session / Time-of-day / Seasonality (S41–S50)

- **S41 — Driving-Season Long Bias (Session/Seasonality)**
  Hypothesis: demand xăng Mỹ tăng May–Aug (driving season) tạo drift dương có baseline.
  Signal: May 1–Aug 31 + giá > 100DMA · Trade: long bias D1, chỉ enter pullback; stop mùa (thoát khi close < 100DMA) · Risk: supply-shock ngược cuốn mất mùa; war override · Data: D1 + lịch mùa · Coupling: EIA gasoline implied demand tăng 3 tuần liên tiếp khi vào mùa.

- **S42 — Autumn-Maintenance Rally-Fade (Session/Seasonality)**
  Hypothesis: Sep–Oct turnaround refinery làm crude demand dip → rally trong cửa sổ này dễ fail.
  Signal: Sep 15–Oct 25 + giá trong 10% của 60-day high · Trade: fade rally chạm 20DMA-extreme, stop 1×ATR trên high, target 20-day mid · Risk: war escalation hủy todo mùa (2026 là ví dụ sống) · Data: D1 + lịch maintenance · Coupling: refinery utilization EIA đang giảm.

- **S43 — Winter Heating-Demand Tilt (Session/Seasonality)**
  Hypothesis: Dec–Feb distillate demand + cold-snap risk làm skew phân phối return dương.
  Signal: Nov 15–Feb 28 + forecast colder-than-normal (NOAA 8–14 day) · Trade: long bias với entry theo cold-forecast confirmation, stop 1.5×ATR · Risk: mùa đông ấm (2023–24 style) · Data: D1 + weather · Coupling: distillate inventories thấp vs 5-yr.

- **S44 — Asia-Session Execution Avoidance (Session/ToD)**
  Hypothesis: chi phí execution Asia (spread 2–5×, slippage quanh headline) ăn hết edge của hầu hết hệ intraday.
  Signal: đồng hồ phiên; spread-sample broker theo giờ · Trade: mọi order limit-only trong 00:00–06:00 London; không stop-market trong khung này; hệ ToD chỉ chạy London+NY · Risk: bỏ lỡ move war Asia (phải chấp nhận — đó là tail-risk, không phải edge) · Data: spread log broker · Coupling: S91 war-mode → Friday decision đồng bộ.

- **S45 — EIA-Wednesday Intraday Pattern (Session/ToD/Event)**
  Hypothesis: có cấu trúc intraday Wednesday: drift nhẹ trước 10:30 ET, spike data, rồi partial-reverse do profit-taking.
  Signal: Wednesday; pre-data range 09:30–10:30 ET; surprise = |actual−consensus| top-quintile lịch sử · Trade: fade 40–60% của spike data sau 30–60 phút (enter tại retrace 38% của spike-leg), stop ngoài spike-extreme, target mid of pre-data range · Risk: surprise khổng lồ (>5σ) continuation · Data: M5 + EIA history · Coupling: API divergence cùng hướng (S53).

- **S46 — Friday Risk-Off into Weekend (War regime) (Session/ToD)**
  Hypothesis: trong war regime, holder dài giảm exposure vào Friday close để tránh 48h tin — tạo drift âm cuối ngày Friday.
  Signal: war-state ON + Friday 14:00–20:00 London · Trade: short bias nhẹ (half size) hoặc flatten longs; thoát Sunday reopen · Risk: tin tốt cuối tuần → gap-up chống lại short · Data: H1 + war flag · Coupling: S20 ngược regime (peace) — hai ý loại nhau có chủ đích.

- **S47 — Month-End Roll Micro-Pattern (Session/ToD)**
  Hypothesis: quanh roll ICE, front-month volume mỏng dần làm price path "gãy" kỹ thuật; second month là price-discovery thật.
  Signal: 5 phiên cuối tháng; so sánh vol front vs second (futures) · Trade: tránh dùng front-based indicator trong cửa sổ; indicator tính trên second-month proxy · Risk: nhỏ nhưng systematic · Data: futures hai tháng · Coupling: S34 cùng chủ đề, góc khác (execution vs signal-source).

- **S48 — Vol-Seasonal Position Sizing Overlay (Session/Seasonality)**
  Hypothesis: oil vol có mùa (driving-season cao, shoulder-month thấp, Q4 geo-cluster); size theo mùa vol cải thiện risk-adjusted.
  Signal: ATR(20)/price percentile theo lịch sử từng tháng · Trade: size = base × (target_vol / seasonal_vol); tháng percent-vol cao → size nhỏ tự động · Risk: geo event ngoài mùa lật bảng · Data: D1 ATR history · Coupling: OVX percentile đồng bộ.

- **S49 — China-Data-Day Reaction Continuation (Session/ToD)**
  Hypothesis: PMI/imports Trung Quốc tốt/xấu → Brent Asia-move; continuation vào London khi move > ngưỡng.
  Signal: ngày PMI chính thức (01 hàng tháng) hoặc customs crude imports; Asia move > 0.8×ATR(D1) cùng dấu surprise · Trade: enter London open cùng hướng, stop 1×ATR, target 2×ATR · Risk: surprise nhỏ bị quên trong 2h · Data: calendar + H1 · Coupling: AUDUSD cùng hướng confirm (China-beta).

- **S50 — Holiday Thin-Liquidity False-Move Fade (Session/Seasonality)**
  Hypothesis: giữa Christmas–New Year, move to thường là liquidity vacuum, revert mạnh ngày đầu liquidity đầy.
  Signal: Dec 24–Jan 2 move > 1.5×ATR không event thật · Trade: fade move vào Jan 2–3, stop ngoài extreme, target 61% retrace · Risk: OPEC+ từng chọn đầu năm công bố (mẫu lịch sử) · Data: D1 + calendar · Coupling: không scheduled event đầu tháng.

### Family 6 — Event / Data-driven (S51–S60)

- **S51 — OPEC+ Meeting Breakout-and-Hold (Event/Data)**
  Hypothesis: quyết định quota lệch expectation tạo move có continuity vì phải re-price supply path cả quý.
  Signal: so quota quyết định vs consensus (Reuters survey); surprise = ±>100 kbd hoặc language-shift · Trade: vào theo hướng surprise tại phiên đầu sau công bố, stop 1.5×ATR, hold tối thiểu 1 tuần nếu hold-từ-tín-hiệu (giá không revert 50% trong 2 phiên) · Risk: "surprise" bị读懂 là bluff (spare thấp không tăng được) → fade nhanh · Data: OPEC outcomes + consensus archive · Coupling: compliance trend cùng dấu surprise.

- **S52 — OPEC MOMR Revision Drift (Event/Data)**
  Hypothesis: revision demand-growth trong MOMR là tin "value" duy nhất của báo cáo; thị trường phản ứng chậm trong 2–3 phiên.
  Signal: global demand growth revision > ±150 kb/d so với MOMR trước · Trade: enter close ngày release, thoát 3 phiên hoặc 2.5×ATR, stop 1.2×ATR · Risk: revision trùng ngày event lớn khác · Data: MOMR hai kỳ liên tiếp · Coupling: IEA revision cùng dấu (confirm tuần sau).

- **S53 — EIA-vs-API Divergence Trade (Event/Data)**
  Hypothesis: khi API (Tue tối) và EIA (Wed) lệch dấu, thị trường confuse → move sau EIA overreact rồi correct.
  Signal: |API draw − EIA build| > 3 triệu bbl về dấu · Trade: fade hướng EIA-reaction 60 phút sau data, stop ngoài spike, target retest pre-EIA · Risk: cả hai data cùng hướng thật (divergence do survey error) · Data: API + EIA weekly · Coupling: gasoline demand cùng dấu EIA-crude.

- **S54 — IEA OMR Headline Trade (Event/Data)**
  Hypothesis: IEA OMR có bias ngôn ngữ (urgency vs comfort) mà market reprice theo câu chữ, không chỉ con số.
  Signal: headline keywords ("tighter", "risk premium", "urgently") vs ("surplus", "ample") đếm được bằng text-score · Trade: enter theo hướng tone, stop 1×ATR, target 2×ATR trong 3 phiên · Risk: tone lặp lại tuần sau không còn surprise · Data: IEA OMR text · Coupling: OECD stocks trend khớp tone.

- **S55 — Ceasefire/Deal-Headline Fade (Event/Data)**
  Hypothesis: headline hoà bình/khung deal gây gap-down overshoot vì pricing cả kịch bản hoàn hảo; tỷ lệ triển khai deal thật thấp → revert một phần.
  Signal: headline "deal/ceasefire/reopen Hormuz" chưa có confirmation đa nguồn; gap > 2×ATR · Trade: fade sau khi velocity giảm (1–2h), enter tại retrace 30% của spike-down, stop dưới spike-low, target 50% gap · Risk: deal THẬT có implementation (mẫu ngược Sep-2026: Trump từ chối → giá bật lại lên) · Data: news feed realtime · Coupling: second-source (AP+Reuters+BBC) chưa khớp thì mới fade.

- **S56 — Sanctions-Announcement Grind (Event/Data)**
  Hypothesis: sanctions (OFAC/shadow-fleet) reprice chậm vì market phải ước barrels ảnh hưởng; drift nhiều phiên thay vì gap.
  Signal: OFAC action nhắm fleet/carrier dầu; volume tanker bị tag > ngưỡng lịch sử của action tương tự · Trade: long drift sau 1 phiên đầu (enter day-2 continuation), stop 1.5×ATR, exit 5–8 phiên hoặc 3×ATR · Risk: carve-out/loại trừ nhanh khiến market bỏ qua · Data: OFAC listings + tanker tracking · Coupling: freight rates tăng cùng kỳ.

- **S57 — SPR-Release Fade (Event/Data)**
  Hypothesis: SPR release là supply tạm thời + tín hiệu political; giá rơi rồi hồi vì barrels vay phải trả lại và volume release không thay được structural deficit.
  Signal: SPR release announcement > 20 triệu bbl quy đổi · Trade: long sau khi giá ổn định 2 phiên post-announcement, stop dưới low post-drop, target pre-announcement − 30% · Risk: release nối tiếp chuỗi (giống 2022) · Data: DOE announcements + SPR levels · Coupling: SPR đang ở mức thấp lịch sử → hiệu ứng tâm lý mạnh hơn (cần kiểm chứng mức hiện tại).

- **S58 — China Monthly Imports Surprise (Event/Data)**
  Hypothesis: số imports/customs Trung Quốc là pulse demand lớn nhất; surprise có continuation 2 phiên vì allocator cần re-weight.
  Signal: imports y/y lệch > ±0.8 mb/d so kỳ vọng愚 · Trade: enter close ngày release, stop 1×ATR, target 2×ATR, max 3 phiên · Risk: stockpiling vào SPR bị nhầm là demand商用 · Data: China customs + run-rate · Coupling: teapot runs cùng dấu.

- **S59 — US CPI Hot-Print Impulse Short (Event/Data)**
  Hypothesis: CPI nóng → real-rate jump → discount future + demand-fear → oil bị đánh trong phiên; nhưng phần lớn là macro-flow, hồi nhanh nếu physical tight.
  Signal: CPI core m/m > consensus +0.2pp; oil rơi < 1% trong 90 phút đầu (chưa priced) · Trade: short 90 phút sau release nếu thesis chưa chạy, stop 0.8×ATR, target 1.5×ATR cùng phiên · Risk: stagflation bid (oil như inflation hedge tự nó hút tiền) · Data: CPI calendar + M15 · Coupling: backwardation sâu → physical tight → chỉ trade short-to-cover.

- **S60 — No-Surprise IV-Crush Reversion (Event/Data)**
  Hypothesis: event "trôi qua không chuyện gì" (OPEC giữ nguyên đúng kỳ vọng, EIA in-line) → vol crush → price co về mean of pre-event range.
  Signal: event outcome trong consensus; OVX/range expected vs realized chênh > 40% · Trade: trade về phía mid of pre-event 5-day range, stop 0.8×ATR, target mid-range · Risk: statement kèm (dù quota不变) có language shift · Data: event outcomes + realized vol · Coupling: curve flat (không tightness bias).

### Family 7 — Cross-asset / Correlation (S61–S70)

- **S61 — USDCAD Divergence Convergence (Cross-asset)**
  Hypothesis: Brent–CAD là quan hệ terms-of-trade ổn định nhất hệ; khi hai giá phá cấu trúc lệch nhau, convergence có xác suất cao.
  Signal: Brent new 20-day high trong khi USDCAD không làm new 20-day low (divergence) trong 3 phiên · Trade: trade Brent theo hướng Brent-break (CAD lag → catch-up), stop 1.5×ATR, target 2.5×ATR · Risk: CAD đang bị driver nội (BoC/housing) chi phối · Data: BRENT + USDCAD D1 · Coupling: WTI cùng hướng Brent (loại kịch bản Brent-only anomaly).

- **S62 — CAD-Strength-without-Oil Fade (Cross-asset)**
  Hypothesis: CAD mạnh mà oil không theo là nonsensical về ToT → một trong hai sẽ nhảy về; lịch sử oil thắng vì CAD có lực cản policy nội.
  Signal: USDCAD break 20-day low trong khi Brent flat/down 5 phiên · Trade: long Brent nhỏ (nửa size) hoặc short USDCAD với stop hẹp; target convergence 1×ATR · Risk: CAD driver thật bền (risk-on toàn cầu) · Data: D1 hai symbol · Coupling: oil curve không deepening contango (đừng bắt dao rơi structural).

- **S63 — Gold Co-Confirm Stress Regime (Cross-asset)**
  Hypothesis: cả Brent + XAUUSD cùng trending lên = real geopolitical/通胀 stress — tăng size trend oil vì hai lớp demand hedging cùng chạy.
  Signal: Brent & XAUUSD đều > 50DMA và cùng làm 20-day high trong cùng tuần · Trade: size ×1.5 cho hệ trend oil (S1/S5), stop chuẩn · Risk: real-rate spike đánh riêng gold → co-lead biến mất · Data: D1 hai symbol · Coupling: DXY cùng kỳ giảm (đúng kênh debasement).

- **S64 — Supply-vs-Demand Shock Classifier (Cross-asset)**
  Hypothesis: oil-up + SPX-down = supply shock (trend oil bền); oil-up + SPX-up = demand boom (cả hai bền nhưng oil có ceiling khi rates lên); phân loại quyết định họ nào được bật.
  Signal: rolling 10-day corr(Brent, SPX) và dấu同期 returns · Trade: routing rule — corr âm & oil up → bật Trend Long; corr dương & oil up → bật Cyclical Long có take-profit; corr dương & oil down → bật MR short-bias · Risk: corr flip giữa chừng mỗi quý · Data: D1 BRENT + SPX proxy · Coupling: dùng làm gate cho S91 router.

- **S65 — DXY-Inverse Overlay (Cross-asset)**
  Hypothesis: kênh USD (dầu tính bằng đô) chỉ rõ ràng ở biên: DXY break cấu trúc → oil ngược hướng trong 70% các phiên đầu.
  Signal: DXY break 20-day high/low với body xác nhận · Trade: bias oil ngược dấu DXY-break trong 3 phiên (chỉ dùng để confirm/gate các tín hiệu khác, không standalone) · Risk: risk-off đồng thời (DXY lên + oil lên vì geo) · Data: D1 DXY (proxy bằng EURUSD×权重) · Coupling: geo-state OFF thì kênh USD mạnh hơn.

- **S66 — Brent/NATGAS Ratio Mean-Reversion (Cross-asset)**
  Hypothesis: ratio oil/gas có band dài hạn do fuel-switching giới hạn; ratio extreme (.percentile 90/10) revert chậm.
  Signal: ratio Brent/NATGAS percentile 120 ngày > 90 hoặc < 10 · Trade: fade ratio về percentile 60 (long kẻ dưới-perform, short kẻ trên — chú ý NATGAS vol cao hơn nhiều → size theo vol-matching), stop percentile ngoài 2 bậc, horizon 3–6 tuần · Risk: structural shift energy transition · Data: D1 hai symbol · Coupling: weather regime không cực đoan (không polar vortex).

- **S67 — AUD as China-Demand Fragility Filter (Cross-asset)**
  Hypothesis: oil-rally không có AUD theo = rally thuần supply → fragile, dễ chết khi tin lắng; dùng để chỉnh stop chứ không đảo chiều.
  Signal: Brent +8% trong 10 phiên trong khi AUDUSD flat/down · Trade: giữ long nhưng stop rút về 1×ATR (từ 2×) và take-profit 50% tại 2R thay vì trail dài · Risk: bỏ mất phần đuôi supply-shock lớn · Data: D1 hai symbol · Coupling: XAUUSD cũng flat → chắc fragile.

- **S68 — USDJPY Inflation-vs-Geo Discriminator (Cross-asset)**
  Hypothesis: oil-up + USDJPY-up = inflation/rates regime (trend oil bền); oil-up + USDJPY-down = geopolitical (JPY haven) → whipsaw regime, giảm size.
  Signal: đồng dấu 5-day returns Brent & USDJPY, rolling · Trade: router rule — cùng dấu dương: full-size trend; trái dấu: half-size + chỉ intraday · Risk: BOJ intervention fakeout USDJPY · Data: D1 hai symbol · Coupling: ăn khớp với S64 classifier (hai vote cùng regime thì mạnh).

- **S69 — EUR Energy-Stress Oil Fade (Cross-asset)**
  Hypothesis: Brent spike + EURUSD underperform đồng EUR-peers = châu Âu trả hóa đơn năng lượng → demand destruction tại потребитель lớn → oil đỉnh gần.
  Signal: Brent +6%/10 phiên & EURUSD −1.5%/10 phiên & EURGBP break down · Trade: short Brent tại cấu trúc D1 (double-top hoặc break 20DMA đầu tiên), stop 1.2×ATR, target 3×ATR · Risk: spike còn dài vì supply mất thật (2022 kéo dài hơn mong đợi) · Data: D1 ba symbol · Coupling: European gas storage thấp.

- **S70 — XAG/XAU Risk-Appetite Gate (Cross-asset)**
  Hypothesis: XAG/XAU ratio lên = risk appetite (công nghiệp) — môi trường oil demand-led friendly; ratio xuống = defensive → oil rally thiếu nền demand.
  Signal: XAG/XAU 20-day trend · Trade: chỉ cho phép long-bias hệ cyclical khi ratio flat/up; defensive → chỉ bật geo-hedge family (S94) · Risk: silver bị squeeze riêng làm ratio giả · Data: D1 hai symbol · Coupling: đồng bộ với S64 routing.

### Family 8 — Positioning / Flows (S71–S80)

- **S71 — COT Managed-Money Extreme Fade (Positioning/Flows)**
  Hypothesis: MM net-long ở percentile 95+ = crowding; giá không còn "fuel" spec → rủi ro squeeze ngược.
  Signal: COT MM net (futures+options) percentile 3 năm > 95 VÀ giá fail làm new high 5 phiên · Trade: short bias vào break 10-day low đầu tiên sau extreme, stop trên high, target 50DMA · Risk: fundamental thật (war) hút thêm long — crowding vẫn thắng thêm 3 tuần · Data: CFTC COT weekly · Coupling: curve backwardation cực đoan cùng lúc → cẩn thận double-confirmed tightness.

- **S72 — COT Momentum Confirmation (Positioning/Flows)**
  Hypothesis: MM net tăng 3 tuần liên tiếp cùng giá trend = institutional accumulation còn dư địa.
  Signal: ΔMM net 3 tuần > +40k contracts & giá > 50DMA · Trade: size ×1.25 cho hệ trend đang chạy (không mở mới), giữ tới khi ΔMM net flip dấu · Risk: data lag (Tue→Fri) trong tuần war · Data: COT weekly · Coupling: S78 xử lý lag.

- **S73 — Producer-Hedging Pressure Proxy (Positioning/Flows)**
  Hypothesis: OI tăng trong downtrend = producer sell-hedge mới = supply thực sắp tới → trend xuống bền.
  Signal: giá < 100DMA & OI tăng 4 tuần & commercials net-short mở rộng · Trade: short bias rally-fade (enter tại 38% retrace), stop 1.5×ATR, target new low · Risk: OI tăng do short spec, không phải producer — phân biệt bằng commercial leg · Data: COT + OI futures · Coupling: curve contango cùng dấu.

- **S74 — Swap-Dealer vs MM Divergence (Positioning/Flows)**
  Hypothesis: swap dealers (đối tác tự nhiên của specs) đảo ròng trước turning point; divergence giữa hai phe là early signal.
  Signal: MM net & swap net cùng đổi dấu trong 2 tuần (một tăng một giảm bất thường so với histórico inverse) · Trade: theo hướng swap flip với size nửa, stop theo giá 2×ATR · Risk: nhầm lẫn identity reporting của COT · Data: COT disaggregated · Coupling: confirm bằng giá 50DMA flip sau 5 phiên.

- **S75 — ETF Flow Drift (BNO/USO-style) (Positioning/Flows)**
  Hypothesis: retail/passive flow qua oil-ETF có tính chu kỳ theo momentum giá; creation lớn → drift cùng hướng vài phiên.
  Signal: weekly shares-outstanding change của BNO/USO > +3% & giá trend cùng dấu · Trade: bias cùng hướng flow, enter pullback H4, stop 1×ATR, max 2 tuần hold · Risk: arbitrage làm flow không dịch chuyển giá thật · Data: ETF AUM/shares (cần data ngoài broker **cần kiểm chứng nguồn**) · Coupling: OVX thấp (retail tham gia khi vol thấp).

- **S76 — New-High with Falling MM Net (Positioning/Flows)**
  Hypothesis: giá lên đỉnh mà specs rút = đỉnh "thiếu người mua" — cấu trúc đỉnh mong manh.
  Signal: giá new 20-day high & MM net thấp hơn 3 tuần trước · Trade: thoát long hiện có / cấm long mới 2 tuần; short chỉ khi break 20DMA xác nhận · Risk: rút là profit-taking sớm trong super-trend · Data: COT + D1 · Coupling: volume không confirm (S29 ngược dấu).

- **S77 — OI-Spike Move Continuation (Positioning/Flows)**
  Hypothesis: move lớn kèm OI spike = new positioning (không phải short-cover) → continuation xác suất cao.
  Signal: daily move > 2×ATR & OI +>5% (xác nhận T+1) · Trade: enter T+1 pullback 30%, stop dưới origin-move, target 1.5× move gốc · Risk: data OI lag 1 ngày · Data: futures OI daily · Coupling:方向 move trùng regime classifier (S64).

- **S78 — Stale-COT Fade After Big Moves (Positioning/Flows)**
  Hypothesis: tuần giá ±8% làm COT (as-of Tuesday) công bố Friday thành "cổ tích" — positioning đã đổi; dùng ngược: fade các tín hiệu COT vừa ra sau tuần như vậy.
  Signal: weekly |return| > 7% ngay trước COT release · Trade: n/a meta-rule — tạm ngưng mọi COT-based entry 1 tuần · Risk: nhỏ (chỉ bỏ tín hiệu) · Data: D1 + COT calendar · Coupling: dùng kèm S71–S74.

- **S79 — China SPR Buying-Floor Detection (Positioning/Flows)**
  Hypothesis: Bắc Kinh mua strategic khi giá rẻ (<$75-80 vùng **cần kiểm chứng ngưỡng chính sách**) tạo demand-floor có thể quan sát qua run-rate imports > refining runs.
  Signal: imports − refinery throughput (Tea pot+mainland) dương 2 tháng liên tiếp khi giá trong vùng thấp · Trade: long-bias với stop dưới floor-zone, horizon tháng · Risk: ngưỡng chính sách dịch theo budget · Data: China customs + PPAC · Coupling: XAUUSD đang mạnh (China reserve diversification cùng chu kỳ).

- **S80 — Short-Covering Rally Detector (Positioning/Flows)**
  Hypothesis: rally mà OI giảm = short-cover (nhiên liệu hữu hạn) → take-profit sớm, không trail dài.
  Signal: giá +5%/5 phiên & OI giảm > 4% · Trade: rút target về 1R và stop về breakeven cho mọi long đang chạy; không mở long mới · Risk: bỏ mất trend thật sau khi cover xong tiếp tục lên bằng new longs · Data: futures OI + D1 · Coupling: MM net đang low (nhiều short để cover) thì tín hiệu mạnh hơn.

### Family 9 — Pattern / Pairs / Stat-arb (S81–S90)

- **S81 — Brent-WTI Z-Band Trade with Regime Gates (Stat-arb)**
  Hypothesis: spread có band "mềm" do freight/quality; ngoài band có pull-force — nhưng chỉ khi không có sanctions/logistics event mới.
  Signal: z-score(Brent−WTI vs 60-day mean) > +2.5 hoặc < −2.5; gate: không OFAC/logistics event 10 phiên · Trade: short spread (long WTI, short Brent) tại z>2.5, target z=0.5, stop z=3.5 · Risk: regime shift spread cấu trúc (hiện $11–14 — mọi param cũ chết) · Data: D1 hai symbol + event log · Coupling: freight rates flat.

- **S82 — Brent-WTI Spread Momentum (Structural) (Stat-arb)**
  Hypothesis: khi driver là sanctions/logistics (shadow-fleet, insurance), spread TREND chứ không revert — trade cùng hướng driver.
  Signal: spread break 60-day high & đã có sanctions-logistics event trong 20 phiên · Trade: long spread (long Brent/short WTI) với trail 2×ATR-spread, không target cứng · Risk: policy reverse (ceasefire + sanctions relax) đảo Spread nhanh · Data: D1 hai symbol + OFAC log · Coupling: freight/war-risk insurance tăng.

- **S83 — Brent vs NATGAS Complex Arb (Stat-arb)**
  Hypothesis: hai năng lượng có liên kết yếu nhưng tồn tại — regime co-move chỉ khi cả hai bị chung cú sốc supply (Hormuz chặn cả dầu+lọc LNG).
  Signal: 30-day corr(Brent,NATGAS) > 0.45 (đột biến so với base ~0.15) & ratio ở extreme · Trade: trade theo relative-value khi corr cao (mean-reversion của ratio), tắt hệ thống khi corr về base · Risk: correlation giả do cùng ngày hai tin khác nhau · Data: D1 hai symbol · Coupling: mùa đông bán cầu bắc (cả hai demand).

- **S84 — Commodity-Bloc vs USD Basket (Stat-arb)**
  Hypothesis: Brent + XAUUSD là "commodity bloc"; EURUSD+USDCHF… là "USD-bloc" — trade basket-vs-basket lọc noise từng symbol.
  Signal: PC1 của (Brent, XAU, XAG) break 20-day extreme trong khi USD-PC1 không phản ứng → trade PC1 continuation vì USD không cản · Trade: position theo trọng số PC1 (long Brent+XAU khi PC1 lên), stop theo z-score basket, target 2×ATR-basket · Risk: trọng số PC1 drift · Data: D1 nhiều symbol + PCA calc · Coupling: DXY flat (S65 đồng thuận).

- **S85 — WTI-Lead at EIA 10:30 ET (Stat-arb)**
  Hypothesis: EIA inventory là số Cushing/PADD-focused → WTI phản ứng trước Brent vài giây–phút; latency-arb phiên bản slow.
  Signal: EIA release; WTI tick-move > 0.4% trong 60 giây đầu · Trade: enter Brent cùng hướng sau 60–120 giây, stop 0.6×ATR(H1), target 1× spike WTI-quy-đổi · Risk: move do Cushing-specific không lan (spread widening thay vì price) · Data: M1 cả hai symbol + EIA clock · Coupling: Brent-WTI spread ổn định trong ngày.

- **S86 — Brent–USDJPY Inflation Pair Bands (Stat-arb)**
  Hypothesis: trong inflation/rates regime, oil và USDJPY cùng nguồn (US yields); cointegration tạm thời cho phép band-trade.
  Signal: regime = S68 ghi "inflation"; residual của регресси Brent~USDJPH 60 ngày |z|>2.2 · Trade: trade residual về mean (short kẻ-rich/long kẻ-cheap, vol-matched), stop |z|=3.2 · Risk: regime flip sang geo → pair break hoàn toàn · Data: D1 hai symbol + regime flag · Coupling: US 10y yield trend cùng USDJPY.

- **S87 — Brent vs AUD–NZD China-Growth Differential (Stat-arb)**
  Hypothesis: AUDNZD là proxy чист China-vs-global growth; Brent rich so với proxy = premium không demand-nền → fragile.
  Signal: residual Brent~AUDNZD z > +2 kéo dài 10 phiên · Trade: short Brent residual (hoặc chỉ hạ size long), stop z=3, target z=0, horizon 15 phiên · Risk: supply-shock chính đáng giữ residual rich lâu · Data: D1 · Coupling: China imports data đang soft.

- **S88 — Brent–USDCAD Synthetic Petro-Pair (Stat-arb)**
  Hypothesis: quan hệ Brent↔CAD gần như đồng nhất về ToT; residual break là cơ hội vì hai chân cùng một driver nền.
  Signal: regression Brent~USDCAD⁻¹ 120 ngày, |residual z| > 2.5 · Trade: long/short residual bằng cặp BRENT + USDCAD (vol-matched), stop z=3.5, target z=0.5 · Risk: BoC policy shock chỉ đánh một chân · Data: D1 hai symbol · Coupling: oil share trong Canadian exports không thay đổi cấu trúc.

- **S89 — Expiry-Week Front-Month Reversion (Stat-arb)**
  Hypothesis: tuần expiry, giá front tháng bị physical-settlement flows (docs giao nhận) méo mó tạm thời; hết expiry revert về second-month path.
  Signal: 3 phiên cuối trước ICE expiry; deviation front vs.synthetic second > 1×ATR mà không có event · Trade: fade deviation bằng position trung tính (long front/short second nếu có futures; CFD-only: fade hướng deviation với size nửa) · Risk: deviation là thật (squeezes cổ điển expiry) · Data: futures hai tháng + lịch ICE · Coupling: volume open interest front đang giảm mạnh (roll chạy).

- **S90 — Commodity-FX PCA Residual Stat-Arb (Stat-arb)**
  Hypothesis: Brent = beta·(commodity-FX common factor) + idio; idio extreme có mean-reversion vì common factor là "giá công bằng" đa thông tin.
  Signal: PCA trên (AUDUSD, NZDUSD, USDCAD, XAUUSD, XAGUSD) → factor F; residual Brent−βF |z|>2.5 · Trade: fade residual về 0 (position Brent ngược residual, hedge bằng basket FX theo β), stop z=3.5 · Risk: Brent là leader thật (tin dầu trước, FX theo sau) → residual "đúng" · Data: D1 đa symbol · Coupling: không event dầu 48h (nếu có → skip, FX mới là lag).

### Family 10 — Regime-conditioned / Options-flavored (S91–S100)

- **S91 — Headline-Intensity Regime Router (Regime)**
  Hypothesis: trạng thái war/peace định measurable bằng cường độ tin; router bật đúng họ strategy cho từng state là cấu trúc sống sót cao nhất trên Brent 2026.
  Signal: đếm headlines geo/trọng lượng (tanker/insurance/OPEC-emergency) 7 ngày lăn; index > ngưỡng = WAR, < = PEACE · Trade: WAR → bật S1/S8/S30/S38/S46/S94, tắt MR/pairs; PEACE → bật MR (S11–S20), seasonality (S41–S43), COT (S71–S74) · Risk: ngưỡng router overfit; state flip lag 1–2 ngày · Data: news metadata count + lịch · Coupling: là meta-gate cho hầu hết family khác.

- **S92 — OVX Regime Size-Filter (Regime/Options)**
  Hypothesis: implied vol oil phân loại environment: OVX<25 bình thường, 25–45 stressed, >45 panic — mỗi vùng một bộ hệ.
  Signal: OVX daily close · Trade: >45 → size ×0.5 + chỉ hệ tail-defined (S94); 25–45 → trend + breakout; <25 → MR + ToD + seasonality · Risk: OVX spike là after-the-fact · Data: OVX (cần kiểm chứng nguồn) · Coupling: ATR(5)/ATR(50) cùng dấu xác nhận.

- **S93 — Put-Skew Steepening Long-Warning (Options)**
  Hypothesis: 25Δ risk-reversal dốc lên phía put = smart money mua bảo hiểm downside (demand-shock fear) trước khi giá thể hiện.
  Signal: RR(25Δ) 5-day change steepen > 1 σ lịch sử mà giá chưa rơi · Trade: giảm long exposure 50%, đặt stop-sell dưới support 1×ATR, hoặc mua protection nếu có instrument · Risk: skew là noise quỹ cover thường kỳ · Data: Brent options chain (cần data ngoài broker **cần kiểm chứng**) · Coupling: COT MM net đang giảm đồng thời → tin.

- **S94 — War-Window OTM Call Ladder (Options)**
  Hypothesis: trong escalation window, convexity (đạn bắn thẳng lên) quý hơn direction bet — defined-risk long convexity là cách "mua bảo hiểm ngược".
  Signal: war-state ON & OVX chưa panic (>70); giá trên 50DMA · Trade: call ladder +3%/+6%/+10% strikes (nếu broker có options trên UKOIL — hiếm; thay bằng: long spot nửa size + stop far + tái vào theo S9 chandelier) · Risk: thời gian trôi (theta) khi war im lặng · Data: options chain hoặc proxy cấu trúc · Coupling: S91 router xác nhận WAR.

- **S95 — Post-Event IV-Crush Mean-Reversion Proxy (Options)**
  Hypothesis: sau event lớn, implied回落 nhanh hơn realized → đường giá thường co về mean of pre-event — "sell the aftermath".
  Signal: event xong 24h; realized vol(2d) < implied pre-event × 0.7 · Trade: fade extreme 2 phiên sau event về mid pre-event range, stop 0.8×ATR · Risk: aftershock event thứ hai · Data: event log + realized vol calc · Coupling: curve không thay đổi slope sau event.

- **S96 — War-Premium Decay Short (Regime/Options)**
  Hypothesis: premium = Brent − (12M forward proxy hoặc fair-value từ freight+inventory) đo được; premium cao mà không có barrel mất thật xác nhận trong N ngày → decay.
  Signal: premium proxy (Brent−WTI residuals + M1−M6 slope z-score composite) > 90th pct & tanker flow thực tế qua Hormuz chưa giảm >5% (AIS) sau 10 ngày · Trade: short Brent nửa size, stop khi flow giảm >5% (materialization), target premium về median · Risk: mất tải đến trễ (đo flow sai) · Data: curve + spread + tanker data (cần kiểm chứng nguồn AIS) · Coupling: S38 flattener cùng hướng.

- **S97 — Peace-Hold Premium Decay (Regime/Options)**
  Hypothesis: sau khi ceasefire nắm giữ >N phiên không vi phạm, premium decay theo thời gian (theta của tin tức) — giá trượt về fundamental dù không tin xấu mới.
  Signal: ceasefire hiệu lực ≥ 10 phiên không incident mới; premium vẫn > 75th pct · Trade: short bias với entry theo rally-to-20DMA-fail, stop trên 50DMA, target premium median · Risk: incident đầu tiên blow-through stop · Data: incident log + premium proxy · Coupling: insurance rates giảm dần xác nhận.

- **S98 — Correlation-Flip Regime Detector (Regime)**
  Hypothesis: rolling corr(Brent, SPX) và corr(Brent, XAU) là "đo nhiệt kế regime": supply-shock (SPX âm, XAU dương), demand-boom (SPX dương), dollar-shock (DXY dẫn) — mỗi regime một route.
  Signal: 20-day corr matrix ba chiều phân loại bằng quy tắc dấu · Trade: routing — supply-shock → trend oil + short SPX-beta FX (AUD); demand-boom → oil+AUD long; dollar-shock → oil chỉ trade ngược DXY ngắn · Risk: corr regime giao thời 2 tuần · Data: D1 ba symbol · Coupling: hợp nhất vote với S64/S91.

- **S99 — Jump-Risk-Buffered Vol Targeting (Regime)**
  Hypothesis: Brent có jump-risk (headline) mà ATR-normal sizing bỏ qua; thêm buffer jump làm sizing sống sót war-time.
  Signal: size = target_vol / (realized vol + k × jump-terms) với jump-term = avg(|overnight gap|², 20) mở rộng · Trade: overlay sizing cho MỌI hệ; k calibrate để weekend-war không vượt 3% NAV/week · Risk: quá bảo thủ trong bull market · Data: daily + overnight gaps history · Coupling: S92 OVX percentile làm k multiplier.

- **S100 — Family-Ensemble Meta-Gate (Regime)**
  Hypothesis: mỗi family có regime sống của nó; ensemble (mỗi family vote theo router, vốn phân theo inverse-drawdown) vượt bất kỳ family đơn lẻ trên Brent — symbol có regime rõ nhất trong universe.
  Signal: router states (S91×S92×S98) xác định family active list; capital weight ∝ 1/maxDD_60d từng family · Trade: meta-quản trị (không signal riêng); re-balance tuần · Risk: router sai → tất cả family sai cùng lúc (single point of failure) — cần disagreement threshold · Data: toàn bộ signal pipeline + router states · Coupling: là đầu ra tự nhiên của file này, tực điều phối mọi S1–S99.

---

## 3. Tổng hợp cho symbol

### 3.1 Top-10 ideas (đề xuất ưu tiên pipeline test)

| # | Idea | Vì sao chọn |
|---|---|---|
| 1 | **S91 Headline-Intensity Regime Router** | Brent-2026 là symbol regime-driven nhất universe; router là điều kiện tiên quyết cho mọi họ khác sống sót — meta-edge cao nhất |
| 2 | **S55 Ceasefire/Deal-Headline Fade** | Lắp đúng microstructure hiện tại (headline ping-pong Sep-2026: deal bị từ chối → $97→$107); mẫu sự kiện lặp lại dày |
| 3 | **S51 OPEC+ Meeting Breakout-and-Hold** | Event định kỳ 1–2 lần/tháng, transmission rõ (quota), có consensus archive để đo surprise |
| 4 | **S31 Backwardation Long-Tilt (+S37 combo gate)** | Thông tin term-structure là lợi thế thông tin độc quyền của oil vs FX; spare 0.22 mb/d Sep-2026 làm backwardation cực đoan |
| 5 | **S1 Donchian War-Filtered (với S99 sizing)** | Xu hướng war-driver dài và trơn khi có filter đúng; trend vẫn là họ có bằng chứng lịch sử mạnh nhất trên commodity |
| 6 | **S81 Brent-WTI Z-Band with Regime Gates** | Spread hiện $11–14 là "sự kiện" — cấu trúc hội tụ về $3–6 hứa hẹn trade lớn nhất năm khi war hạ nhiệt; cần gates chống regime |
| 7 | **S96 War-Premium Decay Short** | Cách đo và short premium (thứ không quan sát trực tiếp ở FX) — edge tri thức đúng nghĩa, có AIS/insurance làm confirm |
| 8 | **S15 Failed-Breakout Reversal** | Counter-programming cho nạn nhân số một của Brent-2026 (headline breakout giả); tiêu chí materiality biến noise thành tín hiệu |
| 9 | **S45 EIA-Wednesday Intraday Pattern** | Event tuần có lịch cố định 15:30 London, sample size lớn, phù hợp automation intraday |
| 10 | **S61 USDCAD Divergence Convergence** | Quan hệ ToT ổn định nhất hệ, dùng được ngay bằng data broker thuần (2 symbol CFD, không cần data ngoài) |

### 3.2 Bẫy overfitting đặc thù khi backtest Brent

1. **Regime war/peace là biến phụ giải thích gần hết variance** — sample 2026 bị thống trị bởi một sự kiện Hormuz duy nhất (N=1); mọi parameter tối ưu trên cửa sổ war là mô tả quá khứ, không phải edge. Bắt buộc train/test tách theo regime-block, không random k-fold.
2. **Roll artifacts**: continuous series unadjusted vs back-adjusted cho breakout levels khác hẳn (Brent roll mỗi tháng, backwardation/contango thay roll-yield dấu). Không khai báo roll-method = backtest không tái lập được.
3. **Spec contract đổi theo lịch sử** (rổ BFOET thêm Troll 2018, thay đổi expiry/settlement 2022) — survivorship của chính instrument; data trước 2018 khác "sản phẩm" ngày nay.
4. **Mean-reversion backtest đẹp trong peace regimes** (2015–19, 2023) rồi chết trong 1 tuần war — nếu không gate, kết quả MR là ảo ảnh chọn mẫu thời gian hoà bình.
5. **Event studies N nhỏ**: OPEC surprise ~vài chục lần từ 2016; "OPEC fade" hoặc "OPEC follow" đều fit được nếu chọn cửa sổ. Đòi hỏi pre-registered rule + out-of-sample theo thời gian.
6. **COT lookahead/lag bias**: data as-of Tuesday, ra Friday; dùng "contemporaneously" trong backtest = nhìn tương lai. Đồng thời 3-day lag làm nhiều edge biến mất thật — hai lỗi trái chiều.
7. **Broker UKOIL ≠ ICE front month**: giờ roll broker khác, swap khác, weekend gap khác futures session break — backtest trên futures data rồi deploy CFD sẽ lệch; phải đo thêm tracking error.
8. **2020 COVID/âm giá + 2022 Ukraine + 2026 Hormuz** là ba outlier làm ATR/vol model và Kelly-sizing choán liv — winsorize hoặc dùng median-vol.
9. **Correlation tĩnh chết người**: USDJPY bimodal, EURUSD đổi dấu theo energy-crisis — mọi hedge beta tĩnh (S86, S88, S90) phải re-estimate rolling và có regime gate.
10. **Headline dataset hindsight**: gán nhãn "war headline" biết kết quả giá sau đó = survivorship; phải dùng timestamp gốc multi-source.
11. **Seasonality N ~ vài chục năm nhưng cấu trúc demand đổi** (EV, refinery closures) — driving-season edge đang mòn dần; test thêm trend gãy cấu trúc.
12. **Overlapping sessions & DST**: giờ EIA/London-NY trôi 1h hai lần/năm; ToD strategy không chỉnh DST là overfit giờ.

### 3.3 MUST-WATCH weekly macro checklist (Brent edition)

**Hằng tuần (khung giờ London trừ khi ghi chú):**
- [ ] **Mon 00:00**: quét 48h cuối tuần — tanker incidents, IRGC statements, negotiation headlines; cập nhật war-state flag (S91) TRƯỚC Asia open.
- [ ] **Mon**: cập nhật Brent-WTI spread level & percentile; M1−M2/M1−M3 slope; xác nhận roll-window tháng này (S34/S47).
- [ ] **Tue sau close US**: API inventories (precursor EIA); ghi chú divergence tiềm năng (S53).
- [ ] **Tue–Wed**: kiểm calendar OPEC+/JMMC tuần này không; nếu có — dựng bracket (S24) và snapshot consensus để đo surprise.
- [ ] **Wed 15:30 London (10:30 ET)**: EIA Weekly Petroleum — crude/gasoline/distillate + implied demand; đối chiếu API; chạy logic S45/S53.
- [ ] **Wed/Thu giữa tháng**: OPEC MOMR & IEA OMR release tuần — diff demand-growth revision (S52, S54).
- [ ] **Thu**: China customs crude imports (tuần release ~7–13 hàng tháng); teapot runs; India PPAC nếu có.
- [ ] **Fri 18:00 London (13:00 ET)**: Baker Hughes rig count; **Fri sau close: COT report** — MM net percentile, OI trend (S71–S80); weekend-risk decision: WAR-state → flat/50% size vào Friday close (S46/S99).
- [ ] **Cuối tuần**: duyệt OVX percentile (S92), 25Δ skew (S93 nếu có data), war-risk insurance/freight chatter, tanker traffic tín hiệu (S96 materiality check).

**Hằng tháng**: curve snapshot đầy đủ M1–M12 (S31–S40); EIA STEO; roll calendar; rebalance ensemble weights (S100); re-measure bảng correlation 1.5 bằng dữ liệu thật.

**Trạng thái Sep-2026 cần bắt đầu template này**: WAR-state ON (deal bị từ chối 26-09, 19 tàu/48h, mìn, IRGC mở rộng Indian Ocean); spare ~0.22 mb/d; OPEC+ đã hoàn tất rollback quota nhưng output thực tụt; Brent-WTI $11–14; các mục OVX/COT/độ sâu backwardation cụ thể **(cần kiểm chứng trước khi dùng làm gate số)**.

---

## Phụ lục — nguồn verify Sep-2026 (WebSearch, truy cập 2026-09-28)

- Al Jazeera (27-09-2026): "Strait of Hormuz tensions linger as Iran and US move further from a deal".
- AP/PBS/BBC/Fox (26–27-09-2026): Iran đề nghị deal 7-day mở lại Hormuz; Trump từ chối.
- The Independent/ABC: Iran tuyên bố 19 vessels/48h; mìn; 8 Marines bị thương; IRGC đe doạ Indian Ocean.
- Reuters (02-08-2026, via US News): OPEC+ duyệt +188 kbd quota từ Sep-2026, hoàn tất rollback (7 nước chính, online).
- Baratelli Institute (19-09-2026): effective spare capacity ~0.22 mb/d.
- WSJ (~4 ngày trước 28-09): Brent settle $103.08 (+3.9%), WTI $92.16; MarketWatch/Forbes: Brent ~$107, WTI ~$92.7; Reuters: Brent low tuần ~$97.36 (thấp nhất từ 08-09).
- Rigzone/EIA STEO (vintage Nov-2025 — đã stale so war): dự báo giảm giá 2026.
- Các mục "tham số/giá trị còn trống": depth backwardation M1–M3, OVX, COT hiện tại, mức SPR, ngưỡng SPR-mua của Trung Quốc, lịch roll UKOIL broker, spec contract broker — **(cần kiểm chứng)**.
