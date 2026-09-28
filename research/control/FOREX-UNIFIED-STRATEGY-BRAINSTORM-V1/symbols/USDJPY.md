# USDJPY — Deep Dive & 100 Strategy Ideas

> Lane: `USDJPY` · Program: `FOREX-UNIFIED-STRATEGY-BRAINSTORM-V1` · Ngày: 2026-09-28
> Kiến thức-only brainstorm. Không backtest, không code. Mọi phát biểu time-sensitive đã verify qua WebSearch ngày 2026-09-28; phần chưa chắc chắn đánh dấu **(cần kiểm chứng)**.

---

## 1. Bản chất instrument

### 1.1. Microstructure & sessions

- **Chu kỳ giao dịch**: 24/5 (Wellington open Chủ nhật ~05:00 JST → Chicago close 06:00 JST Thứ bảy). Weekend gap là rủi ro thật — USDJPY từng gap 100–300 pips vào Tokyo open thứ Hai sau tin cuối tuần (vd. tuần can thiệp 9/2022). Không có trung tâm duy nhất: OTC dealer market + CME futures `6J` (12.5M JPY/contract) + TokyoFinancial Exchange click-365 cho retail Nhật.
- **Vai trò JPY trong hệ thống**: theo BIS Triennial 2022, JPY ~16–17% turnover toàn cầu (top 3–4, sau USD/EUR). Survey 2025 **(cần kiểm chứng số mới)**. JPY là **funding currency của global carry** → dòng vốn global hedge/unwind đi qua JPY nhiều hơn quy mô nền kinh tế Nhật.
- **Sessions**:
  - **Tokyo (09:00–15:00 JST)**: thanh khoản mỏng nhất trong 3 session chính; range thường 30–50% của London. **Tokyo fix 09:55 JST** (morning session close) là điểm tập trung order flow của corporate/toshin/nhà đầu tư Nhật — biến động & skew có cấu trúc quanh fix.
  - **London (16:00–01:00 JST)**: session thanh khoản nhất; phần lớn trend day của USDJPY khởi phát từ London open, đặc biệt khi có break của Asian range.
  - **NY (22:00–07:00 JST)**: overlap London–NY (22:00–01:00 JST) là cửa sổ volume cao nhất; US data (08:30 ET) và UST auctions xảy ra trong session này.
  - **Tokyo lunch (11:30–12:30 JST)** &gap liquidity giữa London–NY (01:00–06:00 JST): microstructure dễ bị đâm giá, spread nở.
- **Rollover/swap lớn do rate differential**: vị thế giữ qua 21:00/22:00 GMT chịu swap ≈ chênh lệch lãi suất USD–JPY quy ra pips/ngày. Với differential ~300bp (Sep 2026: Fed 3.75–4.00% vs BoJ ~1.00%), swap long USDJPY vẫn **dương** nhưng nhỏ hơn nhiều so với thời differential 500+bp (2023–24). **Wednesday = triple swap** (bù cuối tuần) → xảy ra hiện tượng positioning quanh Wednesday. Yên pairs quote 2–3 chữ số thập phân; "big figure" = 1.00 JPY; 1 pip = 0.01.
- **Weekend gap & Monday open**: liquidity giác ở Wellington/Tokyo open khiến gap fill không đối xứng — chiến lược持过 cuối tuần phải tính gap risk vào stop design.

### 1.2. Điểm ĐẶC BIỆT riêng USDJPY (so với các major khác)

1. **Carry king**: trong ~30 năm (1998–2024), USDJPY là nơi rate differential lớn & ổn định nhất trong G10 → là "trục" của mọi carry trade toàn cầu. Hệ quả: dòng unwind có tính concatenate — khi carry JPY unwind, AUDJPY/EURJPY/MXNJPY... bán theo, và ngược lại USDJPY dẫn dắt.
2. **Intervention risk (MOF, không phải BoJ quyết)**: Bộ Tài chính Nhật (MOF) quyết định can thiệp, BoJ chỉ thực thi với tư cách agent. Đây là **rủi ro chính trị hai chiều**: bán JPY hỗ trợ đồng yen khi yếu quá nhanh; (lịch sử) mua JPY bán USD khi yen mạnh quá. Trader mọi timeframe đều phải định giá "MOF put/call on volatility".
3. **Policy-normalization event risk**: BoJ đang trong chuỗi normal hóa hiếm có sau nhiều thập kỷ (chi tiết 1.4) — mỗi bước hike/YCC-exit là event rủi ro lớn cho carry positions; vd. 31/07/2024 hike + presser hawkish của Ueda góp phần triggers cú sell-off toàn cầu (Nikkei −12.4% ngày 05/08/2024, VIX intraday ~65) **(mức chính xác cần kiểm chứng)**.
4. **Safe-haven two-way**: JPY vừa là funding currency (risk-on → yếu) vừa là safe haven (risk-off → mạnh qua repatriation + unwind). Nhật là chủ nợ ròng lớn nhất thế giới (NIIP creditor ~¥400+ trn **(cần kiểm chứng số hiện tại)**) → khủng hoảng ở nơi khác tạo dòng tiền về JPY.
5. **Liên kết chặt với UST 10Y / global rates**: USDJPY là "cặp proxy" cho trades về term premium Mỹ và chênh lệch yields — correlation daily-change với UST 10Y thường +0.4→+0.7 từ 2022 (trước 2022 yếu hơn nhiều).
6. **Flow cấu trúc Nhật**: Toshin funds,保险公司 ngoại hối, exporters đặt sell USD ở vùng cao, repatriation cuối năm tài chính (31/03), tourism/hedging — tạo seasonality & supply/demand quanh các mức tròn.

### 1.3. Tin tức/sự kiện ảnh hưởng

**Scheduled (lịch cố định)**:
- **BoJ Monetary Policy Meeting (8 lần/năm)** + Ueda press conference ~15:30 JST cùng ngày. Kết quả thường "hold"; rủi ro nằm ởhawkish/dovish surprise và tone PC (vd. 31/07/2024).
- **BoJ Summary of Opinions** (~10 ngày làm việc sau meeting) & **Minutes** (~1 tháng sau) — nguồn leak quan điểm dissent nội bộ; năm 2026 board chia rẽ lớn ("biggest split in ten years", 04/2026 — đã verify qua báo chí) → SOO có thể dịch giá.
- **Outlook Report (Apr/Oct)** + branch managers' meeting (Jan/Apr/Jul/Oct) — cadence phát ngôn của Ueda/Mimura dày vào các tuần này.
- **Japan data**: CPI quốc gia (giữa tháng), **Tokyo CPI** (cuối tháng — leading indicator CPI toàn quốc), Jobs/applications, **Tankan** (quý: Apr/Jul/Oct/Dec đầu quý), **Shunto spring wage** (tháng 2–3, Rengo tallies) — chuỗi dữ liệu quyết định nhịp hike của BoJ vì BoJ neo vào wage-price virtuous cycle.
- **US data/events**: FOMC (8/năm, vd. 16/09/2026 đã hike), CPI (giữa tháng), NFP (thứ Sáu đầu tháng), ISM, PCE; **UST auctions** (2s/3s/5s mỗi tháng, 10s/30s mỗi tháng) — tails mạnh dịch USDJPY.
- **Quarter/month-end**: Tokyo fix cuối tháng, London WM/R 16:00 London, repatriation Mar/Sep.
- **MOF monthly FX intervention disclosure** (cuối tháng kế tiếp, vd. bản công bố 30/07/2026) — xác nhận/ex-post các đợt can thiệp.

**Unscheduled**:
- **MOF actual intervention**: bán JPY mua USD. Các episode đã verify: 22/09/2022 (~145.9), 21/10/2022 (~151.9, tổng 2022 ¥9.2trn); 29/04 & 01–02/05/2024 (~157–158, ¥9.8trn), 11–12/07/2024 (~161.9, ¥5.5trn); và **cuối Jul/đầu Aug 2026: can thiệp phối hợp Nhật–Mỹ** khi yen qua 160 (lần đầu sau Jul 2024), chạm ~164 (đáy 40 năm) — Goldman gọi là "biggest FX intervention in 15 years", Nhật ước ~$75bn, Mỹ ~$5–10bn, Fed phối hợp với BoJ (đã verify qua Reuters/OMFIF; lần Mỹ tham gia hỗ trợ yen gần nhất trước đó là 2011 G7 post-Tohoku **(cần kiểm chứng)**). Yen bật >1% về ~152 rồi trôi lại ~163 giữa Aug; **Sep 2026 giao dịch vùng thấp–giữa 150s** (swing low 152.90 ngày 08/09, resistance 154.50, "suspected rate check" giữa tháng — đã verify forex.com 19/09/2026).
- **Verbal intervention / rate checks**: phát ngôn FM Kato, Vice FM Mimura ("excessive one-sided moves"), BoJ officials; rate check (hỏi giá các bank) là tín hiệu bán-forward của can thiệp thật.
- **Risk shocks**: geopolitical, credit events, equity crash → carry unwind; vd. Aug/2024, các đợt risk-off 2018/2020/2022.

**Transmission channels (cách tin tức thành giá)**:
- Rate-diff channel: surprise hawkish Fed/dovish BoJ → US-Japan differential nở → USDJPY lên (qua forward points & real money allocation).
- Risk channel: risk-off → short-cover JPY (unwind carry) + repatriation → USDJPY xuống bất kể differential.
- Flow channel: auction tails, Tankan, portfolio flow data → dịch cung cầu giao ngay.
- Policy-risk channel: can thiệp/phát ngôn → risk premium đột biến, vol nở, options skew dịch.

### 1.4. Thông số ảnh hưởng (drivers chính)

- **US–Japan policy rate differential** (và kỳ vọng về nó): Fed 3.75–4.00% (hike 16/09/2026, Warsh Fed, dot plot còn 1 hike nữa trong 2026 → 4.00–4.25%; đã verify) vs **BoJ ~1.00%** (Dec/2025 hike lên mức 30-năm cao; 2026: Jan hold, Apr vote chia rẽ lớn nhất 10 năm, Jul stand-pat với ~69% xác suất hike trước Oct theo OIS; Morgan Stanley 08/2026 dẫn policy rate "at just 1%"; **kết quả meeting Sep/2026 — kỳ vọng 25bp — cần kiểm chứng**). Differential hiện ~275–300bp, hẹp hơn đỉnh 2023–24 (~525bp) → carry vẫn dương nhưng "đậm" giảm.
- **YCC đã dứt điểm**: BoJ bỏ YCC framework tháng 3/2024, ngừng JGB purchases cố định, sau đó taper dần lượng mua JGB (mức taper hiện tại **cần kiểm chứng**). Điều này trả lại volatility cho JGB curve và tăng kênh truyền rates→FX.
- **UST 10Y yield** (nominal + real + term premium): driver đồng hành số 1 từ 2022; 10Y lên nhanh → USDJPY lên, và ngược lại. Breakdown xảy ra khi yếu tố JPY-specific (BoJ surprise, intervention) áp đảo.
- **Risk sentiment**: VIX, S&P, Nikkei, credit spreads; AUDJPY là "thermometer" của carry regime.
- **Terms of trade Nhật**: Nhật nhập ~100% crude & lớn nhất thế giới về LNG → Brent/WTI/JKM-LNG tăng → JPY yếu (channel nhập khẩu), NATGAS có channel riêng qua LNG.
- **Nikkei**: quan hệ hai chiều — yen yếu → earnings exporters → Nikkei lên; Nikkei lên → foreign inflows (thường unhedged) → yen yếu nữa; đổ vỡ thì cả hai cùng quay đầu (Aug/2024).
- **DXY**: USDJPY = DXY × (JPY-specific); phân tách hai nhân tố này là nền của nhiều ý strategy.

### 1.5. Correlation map (universe 11 symbol, tính đến Sep 2026; tính chất định tính — cần đo lại bằng data thực)

| Symbol | Dấu / cường độ điển hình vs USDJPY | Kênh truyền dẫn chính | Khi nào breakdown |
|---|---|---|---|
| EURUSD | + (0.3→0.6, regime-dependent) | Risk-on chung (USD yếu vs EUR khi risk-on) | USD-specific news mạnh (payrolls) làm cả hai cùng phản USD theo cùng dấu? — thực tế USD mạnh → EURUSD xuống & USDJPY lên (−corr); risk-on → cả hai lên (+corr) → **dấu không ổn định, phải lọc regime** |
| GBPUSD | + yếu hơn EURUSD, nhiễu hơn | Như EURUSD + UK idiosyncrasy (fiscal events) | BoE/UK political shocks; intervention days |
| USDCAD | + nhẹ (0.1→0.4) | USD factor chung; oil (CAD mạnh khi oil lên nhưng JPY yếu khi oil lên → cùng chiều USDXXX) | Oil shock lớn: oil lên → CAD mạnh (USDCAD xuống) & JPY yếu (USDJPY lên) → **−corr tạm thời** |
| AUDUSD | không ổn định qua USD factor; **AUDJPY (chéo) vs USDJPY: + mạnh (0.5→0.8) trong carry regime** | Risk/carry chung; AUD là asset currency, JPY là funding | Intervention days (JPY leg riêng); commodity-specific shock (Trung Quốc/iron ore) |
| NZDUSD | tương tự AUDUSD, beta thấp hơn | Như AUD | RBNZ idiosyncrasy; dairy prices |
| USDCHF | **+ mạnh (0.5→0.7) trong risk stress** — cả hai là "long risk-carry vs funding/safe-haven" | Safe-haven basket (JPY & CHF cùng được mua khi risk-off) | SNB events; CHF đặc thù (EURCHF floor legacy); khi BoJ normal hóa, JPY mất dần tính funding → corr giảm dần **(xu hướng cần đo lại)** |
| XAUUSD | − nhẹ đến − vừa (qua real yields & risk) | US real yields lên → gold xuống & USDJPY lên; risk-off → gold lên & USDJPY xuống | Giai đoạn gold đi theo central-bank buying/debasement (2022–2026) corr với USDJPY trở nên lỏng; intervention days |
| XAGUSD | như gold, beta ~1.3–2x | Như gold + industrial demand | Samelike nhưng nhiễu hơn; squeeze vật chất |
| BRENT | + (0.2→0.4) chậm (daily/weekly) | Japan energy import terms-of-trade; oil lên thường đi cùng risk-on | Supply-shock oil (risk-off + oil lên) → USDJPY xuống dù oil lên (2014–15, 2022 các đợt) |
| WTI | + tương tự Brent, hơi yếu hơn | Như Brent; WTI mang US-specific (shale,库存) | WTI-specific storage/supply events |
| NATGAS | + (qua LNG/JKM) nhưng noise lớn | Nhật là nhà nhập LNG lớn nhất; NATGAS (HH) là proxy lệch cho JKM | HH tách rời Asia LNG (2018–20, 2023+ US export buildout) |

**Đặc biệt**:
- **AUDJPY**: "carry risk barometer" của hệ thống — tương quan với USDJPY mạnh và bền nhất trong các cặp chéo; dùng làm gate risk-on/off cho strategy USDJPY.
- **Gold**: quan hệ −corr chủ yếu qua real yields; khi gold lập đỉnh lịch sử (2024–2026) mà USDJPY không xuống tương ứng → tín hiệu gold driven bởi non-FX flows (CB buying) — chính là tín hiệu "correlation breakdown" có thể khai thác (ý S63).

### 1.6. Note trung thực — bối cảnh nào các họ strategy hay CHẾT trên USDJPY

- **Trend-following chết vào intervention days**: 22/09/2022, 21/10/2022, 04–05/2024, 07/2024, 07–08/2026 — long breakout bị đâm ngược 300–800 pips trong phút; stop-slide/slippage làm backtest đẹp thành live thảm. Backtest phải mô phỏng gap + slippage phi tuyến quanh các ngày này.
- **Carry chết khi differential thu hẹp nhanh + vol nở**: Aug/2024 là case study — carry tích lũy cả quý bị xóa trong 3 tuần. Carry cần gate "carry/vol ratio", không chỉ sign of differential.
- **Mean-reversion chết trong policy-regime shift**: khi BoJ đổi đường đi (1/2025, 12/2025...), giá không "quay về mean" cũ — mean của chính nó dịch.
- **Breakout chết trong vol-compression kéo dài không có catalyst** (whipsaw); và chết ngược khi breakout trùng vùng option barrier được bảo vệ (155/160) — bị đẩy lại.
- **Session/seasonality yếu khi Japan fiscal-year flows thay đổi cấu trúc** (toshin ít hedged, corporate đổi policy hedge sau 2022–24) — seasonality phải được kiểm định rolling, không full-sample.
- **Stat-arb/cointegration chết trong intervention & policy divergence** — quan hệ dài hạn破裂 từng đoạn; phải có regime filter can thiệp.
- Đặc thù dữ liệu: báo cáo MOF can thiệp ex-post (cuối tháng sau) → backtest intraday "biết trước" ngày can thiệp là lookahead bias kinh điển.

---

## 2. 100 Strategy Ideas

Quy ước: MRG = mean-reversion gate; TF = trend-following. Mỗi ý: Hypothesis (giả thuyết kinh tế) · Signal · Trade · Risk (cái gì giết nó) · Data · Coupling (điều kiện/yếu tố ngoài phải cùng chiều hoặc gate).

### Family A — Trend / Momentum (S1–S10)

**S1 — Donchian 20/55 daily breakout (Trend)** — Hypothesis: xu hướng macro (rate-diff, intervention-avoided) kéo dài nhiều tháng cho phép channel breakout hứng trọn wave. · Signal: đóng nến D1 trên Donchian-20 (hoặc 55 cho entry thứ cấp), close-based. · Trade: vào theo hướng breakout, stop dưới ATR×2 từ kênh, trail theo kênh đối diện 10. · Risk: intervention day đảo chiều 500+ pips; whipsaw trong range regime. · Data: OHLC D1. · Coupling: chỉ long khi UST10Y momentum cùng dấu; tắt khi gần vùng can thiệp (>155 và tốc độ >2%/tuần — tham chiếu episode 2024/2026).

**S2 — MA 50/200 + ADX regime filter (Trend)** — Hypothesis: golden/death cross chỉ có giá trị khi trend thật (ADX>25), tránh cross giả trong chop. · Signal: MA50>MA200 và ADX(14)>25. · Trade: position theo dấu, stop dưới swing 20 ngày, exit khi ADX<20 hai kỳ liên tiếp. · Risk: regime flip nhanh (BoJ surprise); lag lớn của MA200 bán đáy/bán đỉnh. · Data: D1. · Coupling: rate-diff sign cùng chiều đường MA.

**S3 — Time-series momentum 3–12 tháng skip-month (Trend)** — Hypothesis: TSMOM tồn tại ở FX nhờ persistence của policy cycles; skip tháng gần nhất tránh short-term reversal. · Signal: dấu của lợi suất 12 tháng (bỏ 1 tháng gần nhất), vol-target 10%/năm. · Trade: position theo dấu, rebalance tháng. · Risk:拐点 policy (2024–26 nhiều lần flip); TSMOM drawback sâu trong sideways. · Data: D1 lịch sử dài + vol estimate. · Coupling: gate differential momentum cùng dấu (S99 tương tự — S99 là meta-switch, S3 là raw TSMOM).

**S4 — UST 10Y momentum proxy trade (Trend)** — Hypothesis: 10Y yield dẫn đường USDJPY (real-money rebalance theo rates) → dùng yield làm signal sớm hơn giá FX. · Signal: 20-day change của UST10Y > +15bp → long bias; < −15bp → short bias. · Trade: vào theo bias khi giá break high/low 5 ngày cùng hướng, stop 1.5×ATR. · Risk: correlation breakdown (BoJ-driven moves). · Data: UST10Y daily + OHLC. · Coupling: hai bên cùng mới vào — nếu USDJPY đi ngược yield 3 ngày liên tiếp thì stand-down (dùng ý S97 làm circuit breaker).

**S5 — H4 market-structure swing continuation (Trend)** — Hypothesis: trong trend ngày–tuần, Break of Structure (BOS) H4 sau pullback là điểm tiếp diễn có xác suất cao vì orderflow backing. · Signal: H4 close vượt swing high vừa tạo sau khi pullback không break swing low (HH–HL sequence). · Trade: enter tại retest của break level, stop dưới HL, target 1:2 theo ATR. · Risk: intervention flash đảo cấu trúc; London fakeout. · Data: H4 OHLC. · Coupling: chỉ trade cùng chiều D1 EMA50 slope.

**S6 — 5-day return z-score continuation với intervention circuit breaker (Trend)** — Hypothesis: động lượng mạnh (|z|>2 của return 5 ngày chuẩn hóa bằng vol) thường tiếp diễn thêm 5–10 ngày do flow chasing — trừ khi nó chạm vùng can thiệp. · Signal: z5 = ret5/vol5×√5; |z5|>2. · Trade: vào cùng chiều, exit sau 5 ngày hoặc khi z về 0; **hard veto nếu giá trong 2% dưới mốc can thiệp hiện hành (160 sau Jul/2026 — cập nhật theo episode mới nhất)**. · Risk: chính điều kiện veto không bắt được verbal intervention. · Data: D1, lịch can thiệp MOF. · Coupling: AUDJPY cùng hướng (risk regime xác nhận).

**S7 — JPY-cross basket confirmation trend (Trend)** — Hypothesis: bỏ nhiễu USD-idiosyncratic: chỉ theo trend USDJPY khi EURJPY & AUDJPY xác nhận chiều JPY yếu/ mạnh tương ứng. · Signal: sign cân bằng 3 cặp (USDJPY, EURJPY, AUDJPY) của momentum 10 ngày đồng thuận. · Trade: vào USDJPY theo chiều đồng thuận, stop 2×ATR20, exit khi 2/3 cặp flip. · Risk: US-specific rally (basket không xác nhận → bỏ lỡ); EUR idiosyncrasy. · Data: OHLC 3 cặp. · Coupling: đây chính là gate cho họ Trend — dùng nội bộ.

**S8 — Ichimoku Kumo daily trend (Trend)** — Hypothesis: Ichimoku là bộ lọc trend & S/R phổ biến nhất với nhà đầu tư Nhật → tự fulfilling trên JPY pairs. · Signal: giá trên Kumo + Tenkan>Kijun + Chikou tự do. · Trade: vào khi đủ 3 điều kiện, stop dưới Kijun, trail theo Kumo. · Risk: chop quanh Kumo; intervention pierce rồi quay lại (giảm sức mạnh tín hiệu). · Data: D1. · Coupling: cùng chiều carry sign.

**S9 — ATR-pyramiding turtle variant (Trend)** — Hypothesis: xu hướng macro USDJPY có nhịp wave dài — pyramiding theo đơn vị 0.5N (N=ATR20) nhân đôi payout khi trend thật, tự giới hạn khi không. · Signal: break Donchian-20 (đơn vị 1), mỗi 1N thuận chiều thêm 1 đơn vị tối đa 4. · Trade: stop cả cụm tại entry−2N, trail 2N từ đơn vị cuối; kích thước đơn vị = risk 0.5%/1N. · Risk: gap qua stop (weekend/intervention); pyramiding tốn chi phí trong chop. · Data: D1, queue lệnh stop. · Coupling: chỉ chạy khi realized vol dưới percentile 80 (tránh can thiệp window).

**S10 — Weekly MACD persistence + carry-sign overlay (Trend)** — Hypothesis: histogram MACD weekly đo acceleration của trend macro; chỉ tin khi carry sign cùng chiều (động lực có nền kinh tế). · Signal: MACD(12,26,9) W1 histogram đồng dấu 2 tuần liên tiếp và swap forward 1M cùng dấu. · Trade: vào tuần thứ 3, stop dưới low 3 tuần, target trailing theo zero-line. · Risk: cú Tháng-cạn reversal tại turn of quarter. · Data: W1 OHLC + forward points. · Coupling: Nikkei cùng chiều (flow xác nhận).

### Family B — Mean-reversion (S11–S20)

**S11 — Bollinger 2σ daily fade trong range regime (MR)** — Hypothesis: khi không có driver macro mới (ADX<20), dao động quanh mean do liquidity providers harvest. · Signal: giá chạm band ±2σ với ADX(14)<20, đường giữa phẳng. · Trade: fade về middle band, stop 1.2×ATR ngoài band, target middle band. · Risk: breakout thật không tin hiệu (không có news gate); intervention từ vùng biên. · Data: D1. · Coupling: không có BoJ/Fed/auction trong 24h tới.

**S12 — Tokyo session range fade (MR)** — Hypothesis: Asian session thường là accumulation; nếu Tokyo di chuyển >70% ATR20 mà không có tin, xác suất reverse trong London cao. · Signal: biên độ Tokyo (00:00–09:00 JST) > 0.7×ATR(H1 20) và không news Nhật. · Trade: fade ngược hướng Tokyo khi London open phá false-break, stop ngoài extreme Tokyo, target 50% range. · Risk: London continuation thật (trend day). · Data: H1, calendar. · Coupling: AUDJPY đi ngang (không risk acceleration).

**S13 — Post-news-spike 5-min fade (MR)** — Hypothesis: overshoot đầu tiên sau data lớn (US CPI, NFP, Tokyo CPI) bị scaler mua lại trong 15–60 phút khi flow thật đến. · Signal: spike 5-min > 3× σ5 của 20 ngày và retrace 38% trong 15 phút. · Trade: vào ngược phần retrace, stop ngoài extreme spike, target 50–61.8% spike. · Risk: second leg (data thật mạnh); can thiệp cùng chiều spike. · Data: M5, calendar. · Coupling: chỉ fade nếu surprise vừa phải (|z surprise|<2.5) — surprise cực đoan thì đi tiếp.

**S14 — RSI(2) H4 fade với 200EMA filter (MR)** — Hypothesis: short-term overbought/oversold trong ctx trend lớn revert về trend mean (Connors-style). · Signal: RSI2 <5 trên H4 khi giá trên 200EMA H4 → long; >95 → short. · Trade: enter market, exit khi RSI2 cắt 50 hoặc sau 8 bar; stop 1×ATR. · Risk: trend acceleration không revert (Aug 2024-type). · Data: H4. · Coupling: không dùng trong tuần BoJ/FOMC.

**S15 — Quarter-end repatriation distortion fade (MR)** — Hypothesis: dòng repatriation/hedging cuối quý (nhất là 31/03 năm tài chính Nhật) đẩy USDJPY lệch khỏi fair value vài ngày rồi revert. · Signal: vào 3 phiên cuối tháng 3 (hoặc 9), nếu USDJPY đã rơi >1.5% trong 5 phiên → long về mean. · Trade: long tại close phiên T−1, exit tuần đầu tháng sau, stop 1×ATR tuần. · Risk: can thiệp/ event trong cửa sổ; xu hướng vĩ mô mạnh hơn flow mùa. · Data: D1 lịch sử ≥15 năm. · Coupling: mức flow (MOF weekly portfolio data) xác nhận áp lực bán thật.

**S16 — Rate-diff fair-value z-score fade (MR)** — Hypothesis: USDJPY dao động quanh "fair value" định nghĩa bằng regression lên 2Y swap differential; sai lệch z lớn revert. · Signal: residual của ln(USDJPY) ~ f(swap2Y diff) có |z|>2.5 trên rolling 3 năm. · Trade: fade residual, stop khi |z|>3.5, target z=0. · Risk: structural break (BoJ regime change làm beta đổi); intervention đẩy residual xa hơn. · Data: swap rates 2Y 2 nước + spot. · Coupling: chỉ khi vol regime bình thường (VIX<25).

**S17 — London-open Asia-move reversal (MR)** — Hypothesis: move mạnh của Asian session thường bị reverse tại London open do European books bắt đầu active với thông tin set khác (Asia fade). · Signal: từ 15:00 JST, nếu亚洲 move >0.8×ATR20(D1) và giá quay qua VWAP Asia trong 90 phút London. · Trade: vào ngược, stop ngoài London high/low, target open price của Tokyo. · Risk: ngày có trend macro mạnh hai session cùng chiều. · Data: M15/H1. · Coupling: UST futures đi ngang hoặc reverse cùng.

**S18 — Weekend gap fill Monday Tokyo open (MR)** — Hypothesis: gap cuối tuần do liquidity mỏng có xác suất fill một phần trong phiên Tokyo–London thứ Hai (gap-fill anomaly). · Signal: gap Monday open vs Friday close > 0.5×ATR(H1). · Trade: fade về giá close thứ Sáu, stop 0.6×gap size phía ngoài, target 50% gap. · Risk: gap thật do tin lớn cuối tuần (political/Payments); can thiệp sáng thứ Hai. · Data: H1 + news. · Coupling: không fade nếu gap cùng chiều breakout S1 đang chạy.

**S19 — Ichimoku Kijun flat-market bounce (MR)** — Hypothesis: Kijun-sen (26-period median) là magnet cho giá trong thị trường không trend — bounce có structure tự fulfilling. · Signal: ADX<18, giá chạm Kijun D1 với nến từ chối (pin/engulfing). · Trade: vào ngược nến tại Kijun, stop ngoài nến, target Tenkan hoặc band Kumo gần. · Risk: giá xuyên Kijun trong trend bắt đầu. · Data: D1. · Coupling: chờ xác nhận close H4 trở lại cùng phía Kijun.

**S20 — ATR percentile-95 exhaustion fade (MR)** — Hypothesis: sau cú vol spike cực đoan (nhưng KHÔNG phải can thiệp), lực cạn kiệt và giá revert một phần trong 2–4 phiên. · Signal: ATR14(D1) > percentile 95 của 2 năm và daily close đảo dấu sau chuỗi 3 nến cùng chiều. · Trade: fade ngày kế tiếp limit tại 50% của move 3 ngày, stop ngoài extreme, target 38.2% toàn bộ move. · Risk: đúnh chính là đợt can thiệp/policy regime shift → phải cross-check không có ngày can thiệp trong 3 phiên đó. · Data: D1 + MOF disclosure calendar. · Coupling: skipt nếu VIX>35 (real risk-off).

### Family C — Breakout / Vol-expansion (S21–S30)

**S21 — Asian-range breakout London (Breakout)** — Hypothesis: range Asia là accumulation; London break xác định hướng trend day với follow-through tốt nhất trong ngày. · Signal: break high/low khung 00:00–08:00 JST bằng H1 close sau 16:00 JST. · Trade: vào theo break, stop ngoài range mid, target 1.5×range, quản lý đến NY close. · Risk: false break London (S17 là mặt đối diện — chọn theo regime vol). · Data: H1. · Coupling: chỉ vào khi UST futures cùng chiều lúc break.

**S22 — NY 30-min opening range breakout (Breakout)** — Hypothesis: 08:30–09:00 ET gói tin data đầu phiên NY quyết định hướng phiên; ORB nắm momentum này. · Signal: break của biên 30 phút đầu NY. · Trade: vào theo break với stop đối diện OR, trail 1×ATR(H1), đóng 15:00 ET. · Risk: news fade hai chân; ngày không data thì OR meaningless. · Data: M5 + calendar. · Coupling: chiều phải khớp với surprise data của ngày (nếu có).

**S23 — Bollinger BandWidth squeeze breakout (Breakout)** — Hypothesis: vol compression (BBW < percentile 10 của 120 ngày) tiền tốn expansion; hướng break có môi kinh tế khi align với rates momentum. · Signal: BW< P10 và đóng nến ngoài band khi nở. · Trade: theo hướng break, stop ngoài band đối diện của squeeze zone, target 2×chiều rộng squeeze. · Risk: breakout giả do squeeze kéo dài vô thời hạn. · Data: D1. · Coupling: hướng UST10Y 10-day momentum (S4) chọn biased side, không trade break ngược.

**S24 — Weekly pivot breakout với Monday confirmation (Breakout)** — Hypothesis: pivot tuần (PP/R1/S1) là mức tham chiếu của dealer books; break pivot thứ Hai sau khi giữ giá quanh đó xác nhận flow tuần. · Signal: Monday close ngoài R1/S1 weekly pivot. · Trade: vào Tuesday theo chiều, stop về PP, target R2/S2. · Risk: Monday manipulation quay đầu. · Data: D1. · Coupling: month/quarter đầu tuần thì giảm size (fix flows).

**S25 — BoJ-day intraday straddle (Breakout/Event-vol)** — Hypothesis: BoJ MPM tạo cú vol 80–150 pips trong 10 phút đầu; straddle mua 2 hướng trước outcome nắm được hướng bất kể chiều. · Signal: vào 5 phút trước giờ công bố (thường ~10:45–11:00 JST hoặc giữa trưa nếu họp 2 ngày). · Trade: long stop trên + short stop dưới range 30 phút trước đó, một chân bị quét thì chân kia chạy, trail 1×ATR M15. · Risk: non-event (hold như kỳ vọng + PC neutral) →两 legs chết bởi decay; spread nở. · Data: M5, calendar, OIS-implied pricing. · Coupling: chỉ khi OIS có >25% xác suất hành động hoặc PC được kỳ vọng hawkish — nếu không, skip.

**S26 — Previous-day high/low session scalps (Breakout)** — Hypothesis: level high/low hôm trước là nơi cluster stops; break đầu London/NY tạo cascade ngắn có thể harvest. · Signal: H1 close qua PDH/PDL trong London hoặc NY session. · Trade: vào theo break, stop 0.5×ATR(H1) về phía trong, target 1×ATR(D1) mở rộng. · Risk: stop-hunt rồi quay lại (sweep). · Data: H1. · Coupling: không trade level trùng barrier option tròn (để S95 xử lý).

**S27 — 52-week high breakout anomaly (Breakout)** — Hypothesis: hiện tượng "giá gần đỉnh 52 tuần tiếp tục chạy" (anchoring + media attention) tồn tại nhẹ ở majors. · Signal: giá trong 0.5% của 52W high và đóng trên nó. · Trade: long breakout, stop dưới 20D low, giữ tối thiểu 1 tháng. · Risk: twin anomaly với MR ở cực đoan; intervention zone thường nằm ngay trên 52W high của USDJPY (160+ Jul/2026) → bắt buộc veto. · Data: D1 dài hạn. · Coupling: chỉ khi differential vẫn nở (không hike BoJ sắp tới theo OIS).

**S28 — Tokyo-open gap continuation (Breakout)** — Hypothesis: gap Monday lớn (đã ngoài ngưỡng S18 fade) thường là tin thật → continuation trong tuần hơn là fill (phân loại theo bản chất gap). · Signal: gap >1×ATR(H1)×3 và tin driver xác định được (event-driven gap). · Trade: vào theo hướng gap tại first pullback H1, stop dưới gap mid, target measured move 1× thêm. · Risk: phân loại gap chủ quan; giao thoa với S18 (cùng input, hướng ngược — chọn bằng phân loại driver, ghi rõ rule). · Data: H1 + news feed. · Coupling: forward points không đổi_sign trong tuần (carry cùng hướng).

**S29 — ATR-expansion regime switch breakout (Breakout)** — Hypothesis: chỉ breakouts trong pha vol nở (ATR5/ATR20 >1.5) có follow-through; trong pha co thì break là bẫy. · Signal: ATR ratio >1.5 + break 10-day high/low. · Trade: theo break với stop 1.5×ATR5, exit khi ratio <1.0. · Risk: vol nở bởi can thiệp — phải loại ngày can thiệp; whipsaw quanh ratio. · Data: D1. · Coupling: RSI đường D1 >55 (hoặc <45) xác nhận momentum.

**S30 — Round-number barrier stop-cascade trade (Breakout)** — Hypothesis: các mức tròn 150/155/160 dày stops & barriers; khi barrier bị break thật (sau khi được bảo vệ), cascade nhanh và tiếp diễn. · Signal: H1 close qua mức tròn + volume (futures) tăng >2× median 20 ngày. · Trade: vào cùng hướng sau close, stop quay lại trong mức 15 pips, target 100–150 pips. · Risk: barrier DEFENSE (S95) đẩy lại — phải phân biệt bằng volume & close; can thiệp ngay trên mức. · Data: H1, CME volume/OI. · Coupling: không trade LONG-break qua mức tròn nằm trong vùng can thiệp (160 hiện hành).

### Family D — Carry / Rate-differential — TRỤC CHÍNH (S31–S40)

**S31 — Classic carry hold với vol-target (Carry)** — Hypothesis: differential dương ổn định (hiện ~275–300bp) trả phí chờ đợi; vol-target giữ尾部风险 trong giới hạn. · Signal: 2Y swap diff > +150bp (long) hoặc < −100bp (short, hiếm). · Trade: position size = target vol 8%/năm chia realized vol, rebalance tháng. · Risk: unwind nhanh khi differential thu hẹp (Aug/2024 archetype); Jul/2026-style policy coordination. · Data: swap 2Y, realized vol. · Coupling: gate carry/vol (S36) và VIX<30.

**S32 — Carry × momentum agreement gate (Carry)** — Hypothesis: carry đứng một mình dễ chết; khi cả carry sign lẫn 3M momentum sign cùng dấu thì win-rate và payoff cùng tăng. · Signal: swap diff sign = 3M return sign. · Trade: chỉ vào khi đồng thuận, size gấp 1.5× baseline, exit khi một trong hai flip. · Risk: flip đồng thời (turning points) hai tín hiệu cùng lật. · Data: swap + OHLC. · Coupling: dùng làm core position, các ý khác vệ tinh.

**S33 — Swap-aware intraday hold window (Carry)** — Hypothesis: với scalper/intraday, tránh giữ vị thế qua 21:00 GMT ngược dấu swap (cost ăn mòn edge nhỏ); triple-Wednesday tạo drift nhẹ cùng chiều swap dương. · Signal: đồng hồ phiên + bảng swap broker. · Trade: flattened trước rollover nếu trade ngược swap và edge < 3× daily swap cost; Wednesday giữ chiều dương thêm 1 giờ. · Risk: edge quá nhỏ so với spread; liquidity 21:00GMT mỏng. · Data: bảng swap, lịch phiên. · Coupling: chỉ áp cho hệ intraday vốn có Sharpe thấp cần giữ từng bp.

**S34 — Δ(differential) impulse-response trade (Carry)** — Hypothesis: thay đổi 20 ngày của chênh lệch 10Y lead biến động USDJPY 1–2 tuần sau (real money rebalance chậm). · Signal: Δ(spread10Y, 20d) > +20bp → long USDJPY trong 10 phiên; < −20bp → short. · Trade: enter tại tín hiệu, exit 10 phiên hoặc khi spread đảo hướng 5 ngày. · Risk: FX đã pricing trước (variance risk premium); intervention phủ nhận. · Data: yields 10Y 2 nước. · Coupling: đồng hướng với S4 (momentum) thì size full, ngược thì nửa.

**S35 — OIS-path repricing convergence (Carry)** — Hypothesis: USDJPY đi theo DIFFERENTIAL CỦA KỲ VỌNG đường lãi suất (12M OIS US − JP); khi path kỳ vọng dịch, giá đuổi theo. · Signal: Δ(OIS12M diff, 5 ngày) vượt 1 sdev 6 tháng. · Trade: theo chiều dịch chuyển kỳ vọng, hold đến khi OIS diff ổn định 5 ngày. · Risk:-priced event không lặp; BoJ surprise đảo chiều kỳ vọng. · Data: OIS curves 2 nước (hoặc proxy futures giá). · Coupling: đối chiếu lịch FOMC/BoJ sắp tới để không đứng ngược event.

**S36 — Carry/vol ratio filter (Carry)** — Hypothesis: carry chỉ đáng giữ khi phần thưởng trên mỗi đơn vị vol > ngưỡng (kiểu Sharpe điều kiện); đây là "kill-switch" của cả họ carry. · Signal: (annualized carry) / (realized vol 1M) > 0.5 → cho phép carry; <0.25 → cấm. · Trade: không phải trade riêng — là gate của S31/S32; đứng riêng thì trade "regime": flat carry khi ratio thấp, full khi cao. · Risk: realized vol lag — spike tới từ event bất ngờ. · Data: forward points, realized vol. · Coupling: dùng cho mọi ý carry trong file này.

**S37 — Front-end curve twist driver (Carry)** — Hypothesis: USDJPY hiện đại nhạy 2Y hơn 10Y (policy path, không phải term premium) — twist ngắn đầu curve là driver thật. · Signal: Δ(2Y diff)/Δ(10Y diff) ratio >1.5 với 2Y diff cùng hướng → trade theo 2Y. · Trade: theo chiều 2Y diff change, stop 1.5×ATR, exit khi 2Y diff flatten. · Risk: các giai đoạn term premium chi phối (10Y dẫn) — phải đo beta rolling. · Data: yields 2Y/10Y. · Coupling: nếu 10Y dẫn (S4 mạnh hơn) thì nhường cho S4.

**S38 — CIP basis stress unwind (Carry)** — Hypothesis: khi 3M JPY cross-currency basis nở âm sâu (funding stress USD tại Nhật), ngân hàng Nhật mua lại JPY → USDJPY giảm. · Signal: JPY 3M basis < −40bp (nới rộng >1σ so với 3 tháng). · Trade: short USDJPY khi tín hiệu xuất hiện, hold đến khi basis thu về −25bp, stop khi basis nở gấp đôi. · Risk: basis nở nhưng bị bù bởi differential nở hơn nữa; quarter-end noise trong basis. · Data: JPY CCBS (Bloomberg/Refinitiv). · Coupling: VIX cùng tăng xác nhận (cùng là stress gauge).

**S39 — G10 carry basket rank weighting (Carry)** — Hypothesis: rủi ro idiosyncratic JPY (can thiệp) giảm khi USDJPY chỉ là 1 chân trong basket carry G10 xếp hạng theo differential. · Signal: xếp hạng 5 cặp theo 2Y diff; giữ 3 cặp cao nhất. · Trade: basket vol-target 6%, USDJPY weight cap 40%. · Risk: correlation 1 trong unwind (basket không diversify đúng lúc cần). · Data: swaps G10. · Coupling: dùng S92 làm overall kill-switch.

**S40 — Forward-premium momentum (Carry)** — Hypothesis: biến động forward points 1M (phần beyond-covered parity do balance-sheet cost) có thông tin về funding demand — forward return predictability. · Signal: Δ(1M forward points, 10 ngày) vượt ngưỡng ±1σ; forward premium tăng → long spot. · Trade: theo hướng forward premium change, hold 2 tuần, stop 1×ATR. · Risk: forward points chỉ tracking policy expectations (trùng S35); noise quarter-end. · Data: forward curve 1M. · Coupling: khác biệt hóa với S35 bằng việc đo supply/demand scaffolding, kiểm tra correlation hai tín hiệu <0.7 mới chạy song song.

### Family E — Session / Time-of-day / Seasonality (S41–S50)

**S41 — Tokyo fix (09:55 JST) flow skew trade (Session)** — Hypothesis: order imbalance tại morning fix tạo drift 10–30 phút trước fix, mạnh nhất ngày cuối tháng/cuối kỳ. · Signal: 09:35–09:50 JST momentum H1 cùng hướng 3 ngày liên tiếp ở tuần fix. · Trade: vào 09:40 theo hướng skew, exit 10:15, stop 15 pips. · Risk: fix flow đảo bất thường; spread nở quanh fix. · Data: M5. · Coupling: cuối tháng tăng size, giữa tháng skip.

**S42 — London–NY overlap continuation (Session)** — Hypothesis: trend hình thành trong 22:00–01:00 JST có follow-through cao nhất trong ngày (volume peak). · Signal: H1 break trong overlap cùng chiều D1 bias. · Trade: vào trong overlap, đóng trước 04:00 JST, stop 0.8×ATR(H1). · Risk: US data 08:30ET đảo chiều; liquidity rút sớm ngày lễ Mỹ. · Data: H1, calendar. · Coupling: bias D1 lấy từ S2.

**S43 — Wednesday triple-swap drift (Session/Carry)** — Hypothesis: phí triple swap Wednesday tạo tha lực positional nhỏ cùng chiều swap dương vào giữa tuần. · Signal: Wednesday Tokyo open → nếu long carry đang active, drift dương thống kê. · Trade: giữ core carry qua Wednesday với size tăng 10%, giảm lại Thursday; không standalone. · Risk: hiệu ứng rất mỏng, bị chôn trong spread; chỉ có nghĩa khi combined với carry core. · Data: bảng swap, D1. · Coupling: chỉ dùng kèm S31.

**S44 — March fiscal year-end repatriation window (Seasonality)** — Hypothesis: nhu cầu JPY cuối năm tài chính Nhật (31/03) tạo xu hướng JPY mạnh có lịch trong 3 tuần cuối tháng 3. · Signal: vào 10/03 hằng năm, short USDJPY kích thước 0.5× baseline. · Trade: hold đến 31/03 hoặc stop 1.5×ATR tuần; exit tất cả trước tuần đầu April. · Risk: năm có differential nở mạnh thì seasonality bị áp đảo (2024: USDJPY mạnh lên thẳng tháng 3 — can thiệp 4–5/2024 sau đó); sample size nhỏ. · Data: D1 ≥20 năm. · Coupling: chỉ khi không có kỳ vọng hawkish Fed event trong window.

**S45 — September 30 semi-annual book-squaring (Seasonality)** — Hypothesis: nửa năm tài chính 30/09 tạo flow squaring tương tự 3/2024 nhưng yếu hơn — JPY bid nhẹ + vol nở. · Signal: tuần cuối tháng 9, short bias nhẹ nếu giá đã yếu 5 phiên. · Trade: hold 5 phiên, stop 1×ATR tuần. · Risk: trùng FOMC/BoJ Sep (như 2026!) — event áp đảo seasonality. · Data: D1 đa năm. · Coupling: kiểm calendar trước khi vào (Sep/2026 có FOMC 16/09 và BoJ cuối tháng — giảm size hoặc skip).

**S46 — Golden Week/Obon thin-liquidity drift (Seasonality)** — Hypothesis: vắng mặt nhà giao dịch Nhật (29/04–05/05, 13–16/08) làm range co và drift theo flow nước ngoài —MR tại extreme làm việc hơn. · Signal: trong kỳ nghỉ Nhật, fade extreme range ngày (S11 condition tự nhiên thoả). · Trade: dùng size MR tăng 1.3× trong các cửa sổ này. · Risk: event global trong holiday Nhật gây gap không thanh khoản đối ứng. · Data: lịch nghỉ Nhật + D1. · Coupling: nhúng vào S11/S19 làm multiplier.

**S47 — US-afternoon reversal of London move (Session)** — Hypothesis: move London thường bị chốt/lật một phần sau 14:00–16:00 ET khi sách lệnh NY đóng (profit taking). · Signal: 14:00 ET, nếu London move >0.8×ATR(D1) và không có data 14:00 ET. · Trade: fade 30% move, stop ngoài NY high/low, target London mid-range. · Risk: trend day mạnh tiếp diễn; Fed speaker 15:00 ET đổi tone. · Data: H1, calendar. · Coupling: VIX<22 mới chạy (risk-on chop).

**S48 — Month-turn (T−2→T+2) fix pattern (Seasonality)** — Hypothesis: dòng rebalance/hedge quanh cuối tháng tạo "kịch bản" thống kê: giảm kích thước trend trước turn, MR quanh turn. · Signal: 2 phiên cuối + 2 phiên đầu tháng. · Trade: tắt breakout entries (S21/S26) trong window; bật MR size 1.2×. · Risk: tháng có can thiệp/policy thì pattern vỡ. · Data: D1 + calendar. · Coupling: meta-rule cho các ý session khác.

**S49 — Monday-open weekly bias vs prior week (Seasonality)** — Hypothesis: nếu tuần trước close mạnh (trend week), Monday open gap cùng chiều có continuation; nếu tuần trước chop, Monday breakout là bẫy. · Signal: phân loại tuần trước theo range/ATR ratio. · Trade: tuần-trend → cho phép Monday breakout entry (S21放宽); tuần-chop → chỉ MR. · Risk: meta-rule; hiệu ứng mỏng. · Data: W1/D1. · Coupling: dùng chung S21/S17.

**S50 — Hour-of-day heatmap persistence (Session)** — Hypothesis: một số khung giờ có drift thống kê bền (vd. Tokyo lunch reversal 11:30–12:30 JST; NY open momentum 22:30 JST) do cấu trúc participant cố định. · Signal: heatmap 30-min returns rolling 3 năm, chỉ giữ giờ có t-stat>3 sau FDR correction. · Trade: vào theo drift của giờ đó, exit cuối khung, stop 0.5×ATR(M30). · Risk: multiple-testing trap — phải out-of-sample; cấu trúc fix thay đổi. · Data: M30 dài hạn. · Coupling: rà calendar để loại trừ giờ bị event chiếm.

### Family F — Event / Data-driven (S51–S60)

**S51 — BoJ hawkish surprise fade-the-spike (Event)** — Hypothesis: sau BoJ hike/hawkish surprise, USDJPY rơi đầu tiên rồi bounce một phần khi thị trường absorbing — mô hình "spike & stabilize". · Signal: outcome hawkish hơn OIS-implied ≥15bp. · Trade: short tại spike retrace 30% (không đuổi top), stop trên pre-announcement high, target 50% spike, tối đa 3 phiên. · Risk: đây là điểm bắt đầu trend mới (Jan/2025 kéo dài); can thiệp cùng chiều tăng sức ép. · Data: OIS trước meeting, M5 quanh outcome. · Coupling: differential sau surprise vẫn > +200bp thì giảm target size 50%.

**S52 — SOO/Minutes dissent drift (Event)** — Hypothesis: Summary of Opinions tiết lộ dissent hawkish → thị trường repricing dần trong 2–4 phiên sau khi phát hành (drift, không phải jump). · Signal: SOO có ≥2 ý kiến đề nghị hike (hoặc vote split) trong ctx board đã chia rẽ (2026). · Trade: short USDJPY tại close ngày phát hành, hold 3 phiên, stop 1×ATR. · Risk: nếu đồng thời US data mạnh phủ nhận. · Data: SOO text, vote counts. · Coupling: FOMC trong 1 tuần tới thì skip.

**S53 — Tokyo CPI surprise continuation (Event)** — Hypothesis: Tokyo CPI (cuối tháng) là leading indicator CPI Nhật — surprise có continuation cao hơn mean-reversion vì nó chạm trực tiếp đường lối BoJ. · Signal: Tokyo CPI core-core vs consensus > +0.2pp. · Trade: short USDJPY tại 5-min break sau release, stop 30′ extreme, target 1×ATR(D1), tối đa 2 phiên. · Risk: tuần có FOMC ngay sau → US dollar dynamics lấn; mẫu ít. · Data: calendar + consensus + M5. · Coupling: giống hướng với surprise thì thêm size (2 surprise cùng chiều trong tuần).

**S54 — Shunto wage-season pre-positioning (Event/Seasonal)** — Hypothesis: market learned rằng shunto ≥5% (3 năm liên tiếp, điều kiện BoJ đã nêu trong SOO 10/2025 — đã verify) → hawkish repricing xảy ra TRƯỚC và TRONG mùa wage, không phải sau. · Signal: từ 15/02 đến 15/03 hằng năm, short bias 0.5× khi tin wage đầu tiên ≥mức năm trước. · Trade: swing short, stop 1.5×ATR tuần, exit khi Rengo final tally ra (~20/03). · Risk: năm Fed hawkish hơn (differential nở) thì thua; shunto disappoint. · Data: Rengo tallies, consensus. · Coupling: OIS BoJ 12M phải đang priced <2 hikes (còn room để reprice).

**S55 — FOMC→BoJ calendar divergence week (Event)** — Hypothesis: trong tuần xen giữa FOMC và BoJ meeting, giá dịch theo differential surprise còn dư âm — "policy divergence echo". · Signal: nếu FOMC hawkish surprise → long USDJPY trong tuần tới BoJ meeting (nếu BoJ kỳ vọng hold). · Trade: enter next Tokyo open, exit trước BoJ day, stop 1×ATR. · Risk: BoJ đi cùng lúc (double-surprise ngược); verbal intervention giữa tuần. · Data: calendar 2 bank, OIS. · Coupling: OIS BoJ-implied action <30% mới chạy (BoJ "hold" là tiền đề).

**S56 — Real-time intervention detection & join (Event)** — Hypothesis: can thiệp MOF tạo footprint: 1-min range > 6σ + volume futures bùng + tốc độ 200+ pips/15 phút từ vùng rủi ro (≥158–160 hiện hành) — đi theo phía JPY-strong vài giờ vì MOF thường đánh nhiều đợt. · Signal: trên cảnh báo, vào short USDJPY tại pullback 30% cú đâm, không đuổi đáy. · Trade: stop trên intervention high, target prior-day low hoặc 2×ATR, tối đa 2 phiên. · Risk: đâm假的 (option sweep) không phải can thiệp; can thiệp chỉ 1 đợt rồi reverse (mua lại discounted USD). · Data: M1, CME volume, lịch vùng rủi ro. · Coupling: xác nhận bằng Mimura/Kato statements cùng ngày; MOF disclosure ex-post để label backtest.

**S57 — Verbal intervention fade (Event)** — Hypothesis: phát ngôn verbal (chưa can thiệp) làm USDJPY rơi 50–100 pips nhưng revert ~60% trong 1–3 phiên nếu không có action thật theo sau. · Signal: FM/VFM phát ngôn về "excessive moves" khi daily move >1%. · Trade: fade sau khi đỉnh reversal hình thành (chờ 4h), stop trên verbal-spike high, target 50% spike. · Risk: verbal là tiền tỷ can thiệp thật (7/2026!) → phải stop-đüng; can thiệp thật xảy ra ngày sau. · Data: news feed, M5. · Coupling: chỉ fade khi giá còn dưới ngưỡng can thiệp thật; nếu vượt — chuyển sang S56.

**S58 — UST 10Y auction tail follow-through (Event)** — Hypothesis: auction 10Y/30Y tail mạnh (weak auction) → yields lên → USDJPY lên trong 1–2 phiên theo (channel rates). · Signal: tail ≥2bp vs WI trên 10Y/30Y. · Trade: long USDJPY tại Tokyo open kế tiếp, hold 2 phiên, stop 0.8×ATR. · Risk: auction weak do flight-to-quality lẫn lẫn (risk-off) — khi đó USDJPY xuống dù yields... phải check VIX cùng lúc. · Data: auction results, VIX. · Coupling: VIX<22 (auction demand-motivated, không phải panic) mới chạy.

**S59 — US data surprise conditional continuation (Event)** — Hypothesis: phản ứng USDJPY với payrolls/CPI có continuation khi surprise cùng chiều differential trend, chỉ spike-and-fade khi ngược chiều trend. · Signal: |z surprise|>1.5; hướng = differential sign. · Trade: vào theo surprise 15 phút sau release nếu cùng differential, stop 0.6×ATR, target 1×ATR. · Risk: revision lớn đổi narrative; can thiệp cùng ngày. · Data: economic surprises index, M5. · Coupling: surprise index (Citi ESI) 4 tuần cùng hướng tăng edge.

**S60 — MOF disclosure ex-post fade (Event)** — Hypothesis: khi MOF công bố chi tiết can thiệp (cuối tháng sau), phần "surprise còn lại" trong giá thoát — giá thường bounce ngược 1 chiều can thiệp vài phiên sau disclosure nếu đã overshot. · Signal: disclosure xác nhận ¥hoặc $ lớn (>¥2trn) trong khi giá đã reverse >70% cú can thiệp. · Trade: trade ngược lại phần residual move: long nếu can thiệp bán JPY mà giá hiện dưới 38.2% mức đỉnh trước can thiệp; stop 1×ATR, hold 3 phiên. · Risk: narrative đã chuyển (can thiệp kèm phối hợp Mỹ như 8/2026 → unterschied). · Data: MOF monthly release, D1. · Coupling: chỉ khi không có BoJ event trong 1 tuần.

### Family G — Cross-asset / Correlation (S61–S70)

**S61 — UST10Y lead-lag convergence (Cross)** — Hypothesis: 10Y dẫn USDJPY 1–3 ngày; khi USDJPY "đuổi kịp" hoặc "đi quá" so với quan hệ rolling → trade hội tụ. · Signal: spread(USDJPY ret − β×10Y ret) vượt ±1.5σ rolling 60 ngày. · Trade: fade spread với beta-neutral (short USDJPY + short/long futures UST tỷ lệ β), stop 2σ, target 0. · Risk: regime where FX dẫn (BoJ events); beta instability. · Data: UST futures + OHLC. · Coupling: tắt khi có BoJ/Fed event 5 phiên tới.

**S62 — Nikkei gap-informative trade (Cross)** — Hypothesis: trong giờ giao chồng (Tokyo mở cùng futures Mỹ đóng), gap Nikkei mở cung cấp đọc nhanh risk sentiment → USDJPY cùng hướng trong phiên Tokyo. · Signal: Nikkei open gap >±0.8% và USDJPY chưa price. · Trade: vào theo hướng gap (Nikkei lên → long USDJPY), stop 0.5×ATR(H1), exit Tokyo close. · Risk: exporter hedge flow làm hai tách rời (Nikkei lên nhưng exporter bán USD). · Data: Nikkei futures, H1. · Coupling: rolling corr 20 ngày của hai tài sản >0.3 mới chạy.

**S63 — Gold-JPY safe-haven convergence (Cross)** — Hypothesis: gold và JPY cùng nhận避风港 flow trong risk-off; khi gold lập đỉnh mà USDJPY không giảm tương ứng → USDJPY "nợ" một cú giảm (hoặc gold driven by non-FX flows — dùng converg. khi VIX nở). · Signal: VIX Δ5 ngày > +4 và z(USDJPY ret + β×gold ret)>1.5σ. · Trade: short USDJPY beta-weighted với long gold đã có (hedge completion), stop 1×ATR, exit khi VIX<20. · Risk: gold do central bank buying (không phải risk channel) → quan hệ giả; carry bù. · Data: gold, VIX, OHLC. · Coupling: gold trend phải đang dương (bull-market safe haven mới mạnh).

**S64 — Brent terms-of-trade trade (Cross)** — Hypothesis: Nhật nhập dầu → Brent 20 ngày tăng mạnh làm JPY yếu (cán cân trade xấu đi) với lag vài ngày. · Signal: Brent 20d ret > +8% và USDJPY flat/âm trong kỳ. · Trade: long USDJPY, hold 10 phiên, stop 1×ATR. · Risk: oil supply-shock risk-off (oil lên + risk-off) hai lực đối chọi → phải lọc. · Data: Brent, D1. · Coupling: VIX<25 và S&P không breakdown.

**S65 — LNG/NATGAS Japan exposure (Cross)** — Hypothesis: Nhật là nhà nhập LNG lớn nhất → NATGAS (proxy JKM lệch) tăng vọt làm JPY yếu với channel riêng khỏi dầu. · Signal: NATGAS 10d ret > +15% (breaking structure) khi Brent flat. · Trade: long USDJPY 5 phiên, stop 1×ATR. · Risk: NATGAS HH–JKM decouple (US export capacity); nổ vol NATGAS tự nó. · Data: NATGAS, Brent. · Coupling: chỉ khi Brent flat (để tách channel — nếu Brent cùng chạy thì là S64).

**S66 — VIX-threshold carry unwind short (Cross/Regime)** — Hypothesis: VIX>25 xác định pha carry-unwind; giữ short USDJPY suốt pha, thoát khi VIX<20 — hedge kinh điển cho risk portfolio. · Signal: VIX daily close >25 (2 ngày liên tiếp). · Trade: short 0.5× vol-target, stop 2×ATR, exit VIX<20 hoặc stop. · Risk: VIX spike giả (đảo nhanh); different rộng quá mạnh JPY. · Data: VIX, D1. · Coupling: cùng hệ với S92/S100 (đây là dạng đơn giản nhất).

**S67 — DXY-residual idiosyncratic JPY trade (Cross)** — Hypothesis: USDJPY = β×DXY + JPY-specific residual; residual z lớn có info về JPY events sắp tới (accumulation can thiệp risk...). · Signal: residual z>2 (JPY yếu hơn USD chung) khi giá trong vùng can thiệp. · Trade: short residual (short USDJPY, long DXY basket size β) — cược residual thu hẹp; stop z>3. · Risk: residual còn lý do (BoJ dovish tuần đó). · Data: DXY, USDJPY. · Coupling: giá trị riêng của residual là early-warning cho S56.

**S68 — Tech/Nasdaq risk proxy pass-through (Cross)** — Hypothesis: chu kỳ AI/semi định hình risk sentiment; Nasdaq futures lead USDJPY trong morning US theo cùng hướng (JPY funding của tech carry). · Signal: 09:30–11:00 ET Nasdaq trend day (±1%) xác nhận chiều cho USDJPY intraday. · Trade: vào USDJPY cùng chiều 10:30 ET, stop 0.5×ATR(H1), exit 15:00 ET. · Risk: tech up + yields down (growth scare mix) làm tách; can thiệp. · Data: NQ futures, H1. · Coupling: UST10Y intraday cùng chiều Nasdaq (risk-on thuần) mới chạy.

**S69 — Auction coverage differential drift (Cross)** — Hypothesis: chất lượng cầu JGB vs UST (bid-to-cover spread) phản ánh relative demand cơ cấu → drift chậm USDJPY theo hướng nước nào cầu tốt hơn. · Signal: 3M rolling (UST coverage − JGB coverage) z>1.5. · Trade: theo hướng (UST cầu tốt hơn → long USDJPY) 1 tháng, stop 1×ATR tháng. · Risk: coverage metrics nhiễu (mỗi đợt auction khác cơ cấu); BOJ mua JGB che cobertura. · Data: auction metrics 2 nước. · Coupling: đồng hướng Δ10Y spread 3M.

**S70 — AUDJPY lead-lag risk turn (Cross)** — Hypothesis: AUDJPY là risk barometer nhạy nhất — quay đầu trước USDJPY vài giờ trong các turning point risk. · Signal: AUDJPY break 20-day high/low khi USDJPY chưa break cùng hướng. · Trade: vào USDJPY cùng hướng AUDJPY lead, stop 1×ATR, target khi USDJPY catch-up xong (ATR равного move). · Risk: AUD idiosyncrasy (Trung Quốc/commodity) gây tín hiệu giả về risk. · Data: 2 cặp, D1/H1. · Coupling: thêm xác nhận bằng S&P futures cùng hướng.

### Family H — Positioning / Flows (S71–S80)

**S71 — CFTC IMM net-spec extreme contrarian (Positioning)** — Hypothesis: specs net-short JPY cực đoan (>P90 của 5 năm) → crowding → rủi ro snap-back mạnh hơn (như episode 7–8/2024 & 2026 reversal). · Signal: JPY net spec (asset-manager + leveraged funds) vượt P90/P10. · Trade: vào long JPY (short USDJPY) size 0.5×, stop 1.5×ATR, hold tối đa 4 tuần hoặc đến khi positioning về P60. · Risk: extreme còn kéo dài cực hơn (trend mạnh); timing tệ. · Data: COT weekly (Fri release). · Coupling: phối S74 (regime flip) và VIX regime.

**S72 — COT divergence vs price (Positioning)** — Hypothesis: USDJPY lập new 20-day high nhưng net-long USD specs GIẢM → động lượng không còn nhiên liệu → cảnh giác reversal sớm hơn thuần giá. · Signal: price new high + specs net change âm 3 tuần. · Trade: thoát trend positions / vào short nhỏ 0.3×, stop trên high, target 3×ATR. · Risk: price đi bằng dòng real money (specs không cần thiết); intervention làm обои cùng nhảy. · Data: COT, D1. · Coupling: dùng làm exit-rule cho S1/S9.

**S73 — Global retail sentiment contrarian (Positioning)** — Hypothesis: retail crowd đơn chiều (long USDJPY >70% accounts) tại vùng giá cao → chốt lời/stop-cascade tạo push-down. · Signal: broker sentiment metrics >70% hoặc <30%. · Trade: fade 1 ngày khi price action confirming (bearish engulfing D1 tại vùng cực). · Risk: trend mạnh碾 retail sentiment mãi; sentiment metrics không đại diện. · Data: broker sentiment feeds. · Coupling: kết hợp S86 (round number) cùng vùng.

**S74 — Positioning-regime flip follow-through (Positioning)** — Hypothesis: khi positioning lịch sử bị lật (LSEG "historic reversal" 9/2026 — đã verify), chiều mới có inertial 4–8 tuần do institutional re-positioning chậm. · Signal: specs flip sign + price trend 2 tuần cùng chiều flip. · Trade: theo chiều flip 4 tuần, trail stop 2×ATR, exit khi positioning qua P60 của chiều mới. · Risk: flip giả (noise); flip đã xong phases (đuối). · Data: positioning data (COT/LSEG). · Coupling: chính là trạng thái hiện tại 9/2026 — ưu tiên kiểm chứng và chạy nếu còn sớm pha.

**S75 — Japan foreign-bond outflow cap (Flows)** — Hypothesis: tuần Nhật mua mạnh ngoại tệ bonds (toshin/insurers) tạo supply USD bền → hạn chế sức mạnh JPY dù macro hawkish. · Signal: MOF weekly portfolio flow (net buying foreign bonds >¥1.5trn 2 tuần liên tiếp). · Trade: long USDJPY bias 1–2 tuần trong ctx khác, stop 1×ATR tuần. · Risk: purchases đã hedged (flow không tác động spot); data lag 1 tuần. · Data: MOF weekly flows. · Coupling: nghịch với OIS-hawkish JPY (đang "fight") — chọn bên có event hỗ trợ gần nhất.

**S76 — MOF weekly flow release Thursday trade (Flows)** — Hypothesis: bản flow tuần (thứ Năm) tạo mini-repricing khi số lệch consensus lớn. · Signal: |flow surprise| > 2× std 3 tháng. · Trade: theo hướng surprise (mua ngoại bond mạnh → long USDJPY) trong 2 phiên, stop 0.8×ATR. · Risk: số bị revision; thị trường đã smoke trước. · Data: MOF flows + consensus. · Coupling: trùng BoJ week thì skip.

**S77 — Hedge-flow proxy qua DXJ/futures OI (Flows)** — Hypothesis: dòng hedged-equity (DXJ AUM/OI thay đổi) là proxy cho taste hedge của nhà đầu tư Mỹ — khi hedge ratio tăng, cung JPY forward tăng → USDJPY chịu ép. · Signal: 4-week ΔOI 6J + DXJ flows cùng tăng mạnh. · Trade: short bias nhẹ 2 tuần, stop 1×ATR. · Risk: proxy quá gián tiếp; OI tăng vì speculation chứ không hedge. · Data: ETF flows, CME OI. · Coupling: S&P record-high cùng lúc (hedge demand tăng khi equity mạnh).

**S78 — 25-delta risk-reversal extreme contrarian (Positioning/Options)** — Hypothesis: RR JPY cực đoan (call JPY đắt — tức put USDJPY đắt) sau giai đoạn panic → fear priced → mean-revert. · Signal: 3M 25Δ RR z>2.5. · Trade: long USDJPY khi RR bắt đầu thu hẹp 3 ngày, stop 1.2×ATR, target z=0. · Risk: fear còn nền tảng (policy thật); RR sticky. · Data: options chain RR. · Coupling: VIX đang giảm xác nhận.

**S79 — CME volume/OI breakout confirmation (Positioning)** — Hypothesis: breakout giá + volume/OI futures cùng bùng = participation thật (không phải sweep); thiếu volume thì bỏ. · Signal: volume breakout-day >2× median 20 ngày + ΔOI dương. · Trade: filter cho S26/S30 — chỉ vào khi đủ điều kiện. · Risk: OI dương cũng có thể short-new... cần combined với giá. · Data: CME volume/OI. · Coupling: dùng làm confirm layer chung cho họ Breakout.

**S80 — Japanese retail margin positioning contrarian (Positioning)** — Hypothesis: retail Nhật (GMO/CLICK dữ liệu tuần) mất tiền đều ở vùng tròn khi bị loss-cut — positioning cực đoan của họ là tín hiệu ngược chất lượng cao hơn retail global (S73). · Signal: retail JP net-long USDJPY >P90 lịch sử riêng của sample này. · Trade: fade với stop-loss cluster map (thường trên/dưới mức tròn 50 pips), target 2×ATR. · Risk: dữ liệu chỉ từ broker Nhật, coverage một phần; loss-cut maps dịch. · Data: GMO/Click weekly reports. · Coupling: kết hợp S86 barrier/round-number.

### Family I — Pattern / Pairs / Stat-arb (S81–S90)

**S81 — Triangular consistency arbitrage (EURUSD×USDJPY vs EURJPY) (Stat-arb)** — Hypothesis: deviate tick-level giữa cross thực và cross suy ra bị market-maker hút về — mô hình mua-bán 3 chân cùng lúc. · Signal: deviation > 2× median spread của 3 cặp. · Trade: ba chân đồng thời (long cheap leg, short rich legs), target deviation=0, hold giây–phút. · Risk: đây là cạnh tốc độ/spread — retail khó; slippage ăn hết edge. · Data: tick 3 cặp, VPS colocation lý tưởng. · Coupling: chỉ dành cho hệ execution-heavy, không phải alpha research thường.

**S82 — Beta-neutral JPY factor trade (AUDJPY vs USDJPY) (Stat-arb)** — Hypothesis: tách nhân tố JPY khỏi USD: long AUDJPY + short USDJPY (tỷ lệ beta rolling) = pure JPY-weakening với USD neutral. · Signal: vào khi JPY-factor signal (vd: carry unwind threat thấp, risk-on) nhưng muốn loại USD risk (trước FOMC). · Trade: pair trade 2 chân beta-weighted, stop theo PnL pair 1×ATR, exit khi nhân tố đạt target. · Risk: beta instability; hai chân spread cost. · Data: 2 cặp, rolling beta. · Coupling: dùng để giữ JPY view xuyên qua sự kiện Fed.

**S83 — JPY-crosses basket index rich/cheap (Stat-arb)** — Hypothesis: xây JPY-effective index từ 6 crosses (EUR/AUD/NZD/CAD/CHF/GBP vs JPY); USDJPY lệch z so với fit basket → trade về. · Signal: |z|>2 của USDJPY residual vs basket PCA fit. · Trade: fade residual 1 tuần, stop z>3. · Risk: USD leg có lý do riêng (US-specific flows) khiến residual có căn cứ; basket weights老化. · Data: 7 cặp OHLC. · Coupling: không chạy khi US event tuần đó (FOMC/NFP).

**S84 — Cointegration EURUSD–USDJPY with regime filter (Stat-arb)** — Hypothesis: hai cặp chia sẻ dollar/risk factors → spread cointegrated trong đoạn lịch sử ổn định (không can thiệp, không policy shift). · Signal: ADF test trên rolling 2 năm; z spread >2 khi regime-filter ON (no intervention/policy-shift flags). · Trade: fade spread, stop 2.5σ, target 0.5σ. · Risk: relationship break tại từng structural break (2024, 2026) — regime filter là靈魂. · Data: 2 cặp D1 + flags. · Coupling: flags lấy từ lịch can thiệp + BoJ/Fed path changes.

**S85 — EURUSD lead-lag trong US data releases (Stat-arb)** — Hypothesis: tại 08:30 ET, EURUSD phản ứng trước USDJPY vài trăm ms–giây (depth/quoting) — lead leg làm signal cho lag leg. · Signal: move EURUSD >25 pips trong 5s sau data mà USDJPY chưa reprice tương đương (theo tỷ số). · Trade: vào USDJPY theo hướng EURUSD, hold 30–120s, stop nhanh. · Risk: execution-latency; hiệu ứng phụ thuộc infrastructure. · Data: tick-level 2 cặp. · Coupling: chỉ quanh các data release lớn (NFP/CPI).

**S86 — Round-number psychology bounce/cascade (Pattern)** — Hypothesis: mức 00/50 chứa stop & option barriers; trước khi VỰT qua được, thường có 1–3 cú test/rejection — trade rejection với volume thấp, trade cascade với volume cao (phân biệt bằng volume — nối S30/S79). · Signal: test mức tròn volume thấp + nến từ chối M15/H1. · Trade: fade test (target 30–50 pips về trong), stop ngoài mức 12 pips; ngược lại theo S30 khi break có volume. · Risk: can thiệp thường xảy ra NGAY vùng tròn (160 năm 2026) — phải kiểm vùng can thiệp trước. · Data: H1, volume, barrier intel. · Coupling: mức nằm trong vùng rủi ro can thiệp → chỉ chạy chiều JPY-mạnh.

**S87 — Candlestick rejection tại Kijun/PD confluence (Pattern)** — Hypothesis: pin bar/engulfing tại confluence (Kijun D1 + PDH/PDL + mức tròn) có xác suất revert cao do nhiều lớp participant cùng nhìn. · Signal: nến từ chối tại ≥2 lớp S/R trùng nhau. · Trade: vào ngược nến, stop ngoài wick, target lớp S/R kế, RR≥2. · Risk: trend day xuyên qua mọi level; confluence chủ quan nếu không rule hóa. · Data: D1/H4. · Coupling: chỉ đối chiều trend khi có MR regime (ADX<20), thuận trend khi pullback.

**S88 — PCA factor rotation dollar-vs-JPY (Stat-arb)** — Hypothesis: PCA trên ma trận G10 USD- pairs: PC1=dollar, PC2=JPY; khi PC2 loading của USDJPAY nở nhanh → sắp có JPY-specific event move — nắm bằng trade PC2-pure (basket). · Signal: explained variance của PC2 tăng >P80 rolling. · Trade: basket long/short theo hướng PC2 momentum, hold 1 tuần. · Risk: PCA churn trong ngoai模范 periods; interpretation. · Data: 10+ cặp daily. · Coupling: kèm S67 residual cùng dấu tăng conviction.

**S89 — Spot–forward points momentum mismatch (Stat-arb)** — Hypothesis: khi forward points dịch nhanh hơn spot (policy repricing trước), spot "catch up" theo phần mismatch còn lại — tín hiệu giá rẻ/đắt theo covered parity frame. · Signal: 1M forward-implied annualized carry change >+50bp mà spot chưa di chuyển tương ứng (theo beta carry→spot lịch sử). · Trade: theo hướng mismatch 2 tuần, stop 1×ATR. · Risk: forward dẫn vì quarter-end distortions; beta不准. · Data: forward curve, spot. · Coupling: khác S40 ở chỗ đo MISMATCH với spot (không chỉ momentum forward).

**S90 — Nikkei–USDJPY pair momentum divergence (Stat-arb)** — Hypothesis: hai tài sản cùng risk-factor nhưng khác liquidity — khi divergence mở rộng bất thường, một trong hai nhầm → trade hội tụ (thường FX nhầm nhiều hơn). · Signal: z(USDJPY ret − β×Nikkei ret, 20d) >2. · Trade: fade divergence bằng 2 chân (spot + futures), stop 2.5σ, target 0.5σ. · Risk: Nikkei có idiosyncrasy earnings; khi có can thiệp FX nhảy làm spread nở. · Data: Nikkei futures + OHLC. · Coupling: loại các ngày can thiệp khỏi sample tính z.

### Family J — Regime-conditioned / Options-flavored (S91–S100)

**S91 — Vol-regime strategy switching (GARCH gate) (Regime)** — Hypothesis: MR thắng trong vol thấp, Trend/Breakout thắng trong vol nở — GARCH forecast percentile làm switch tự động giữa hai bộ máy. · Signal: GARCH(1,1) 1-step vol forecast <P25 → bật MR set (S11–S19); >P75 → bật Trend/Breakout set. · Trade: meta-allocator chia vốn 2 bộ theo regime; hysteresis 5 percentile để tránh flip. · Risk: vol spike đột ngột giữa chu kỳ (event) làm sai side; GARCH lag. · Data: OHLC D1. · Coupling: là meta-layer cho cả file — phải backtest hai bộ tách biệt trước khi ghép.

**S92 — Global carry-basket drawdown cascade (Regime)** — Hypothesis: drawdown của G10 carry basket >2% là tín hiệu unwind đang lan — JPY (funding chính) sẽ mạnh thêm; đứng SHORT USDJPY cho đến khi basket hồi. · Signal: drawdown carry basket (5 cặp) từ đỉnh 60 ngày >2%. · Trade: short USDJPY 0.5×, trail theo basket recovery, exit khi drawdown<0.5%. · Risk: unwind V-shape nhanh bỏ qua JPY; idiosyncratic trong basket. · Data: G10 pairs + swaps. · Coupling: VIX confirm (S66) tăng xác suất.

**S93 — Covered short-vol in low-vol carry regime (Options)** — Hypothesis: trong carry-stable + vol thấp (1M IV <P25 và IV>RV thường xuyên), bán strangle ngòai expected move thu variance risk premium — với veto can thiệp. · Signal: 1M IV P25; giá ngoài band ±1.5×IV×√T; veto nếu giá trong vùng can thiệp hoặc BoJ event <2 tuần. · Trade: short strangle delta-hedge tuần 2 lần, stop khi realized 1-day >2×IV hoặc veto-trigger. · Risk: đỉnh của trái nguy hiểm — Aug/2024/2026-type ngày xóa cả năm premium; phải hard veto + size nhỏ. · Data: options chain, calendar, vùng can thiệp. · Coupling: dùng S96 ngược chiều như protection khi IV thấp bất thường trước event.

**S94 — Risk-reversal z-score regime re-entry (Options)** — Hypothesis: skew JPY-call cực đoan đi kèm đáy risk-off; khi skew bắt đầu normalize (2–3 ngày), risk-on tái khởi động → long USDJPY spot. · Signal: RR 1M z<−2.5 (JPY calls đắt) rồi thu về 0.5σ trong 3 ngày. · Trade: long spot tại xác nhận, stop 1×ATR, target 2×ATR. · Risk: đây là bắt dao rơi; skew normalize do can thiệp ổn định chứ không phải risk-return. · Data: RR series, spot. · Coupling: AUDJPY đã bounce xác nhận (không phải USD-only).

**S95 — Barrier defense fade tại Tokyo hours (Options)** — Hypothesis: option writers bảo vệ barrier tại mức tròn trong giờ Tokyo (vùng dễ điều phối) → giá bị đẩy lại nhiều lần trước expiry — fade các cú test không có volume. · Signal: giá test barrier (vd 155.00 trước expiry cuối tháng) volume thấp, M15 rejection. · Trade: fade vào trong mức 20–30 pips, stop ngoài barrier 10 pips phía ngoai, target 40–60 pips, đóng trước expiry. · Risk: barrier REALLY broken (đặc biệt khi có flow thật) → loss + cascade ngược; can thiệp phá mọi barrier. · Data: options expiry intel, H1 volume. · Coupling: không đứng chắn khi trend macro (S4) đang cùng chiều break.

**S96 — Term-structure vol ratio pre-event straddle (Options)** — Hypothesis: 1M/3M IV ratio >1.3 cho thấy market anticipates event lớn (BoJ/Fed) — mua straddle ngắn hạn trước event thu vol jump nếu surprise thật. · Signal: ratio>1.3 và event trong 5 phiên; IV ngắn hạn còn dưới P75. · Trade: long straddle 1 tuần trước event, thoát ngay sau outcome (bán trong vol nở), stop theo vega nếu vol collapse trước event. · Risk: event pass无异 → hai chân decay; đã priced đầy đủ. · Data: IV term structure, calendar. · Coupling: OIS-implied surprise probability >30% mới đáng chạy.

**S97 — Correlation-breakdown stand-down circuit (Regime)** — Hypothesis: rolling corr(USDJPY, ΔUST10Y) là "đồng hồ sức khỏe" của rates-FX regime; khi corr sập về 0/âm, các chiến lược rates-driven (S4/S34/S58/S61) mất nền — phải stand-down. · Signal: 30-day corr <0.2 trong 5 ngày. · Trade: không phải entry — là kill-switch: giảm weight họ rates-driven về 0, tăng weight họ flow/positioning. · Risk: miss re-engagement (corr hồi sau). · Data: 2 series. · Coupling: re-engage khi corr >0.4 ba ngày.

**S98 — Drawdown-controlled vol targeting với intervention veto (Regime)** — Hypothesis: vol targeting (size ∝ 1/realized vol) cải thiện Sharpe nhưng phải kết hợp veto cứng ngày can thiệp/rate-check suspicion — vì vol spike phi tuyến, stop không bảo vệ được gap. · Signal: realized vol 20d scaling; veto khi: giá trong vùng can thiệp HOẶC daily range>3×ATR HOẶC rate-check news. · Trade: position sizing rule áp cho mọi ý trong file; veto = flatten intraday không chờ stop. · Risk: veto quá nhạy làm miss trend resumption; vol estimate lag. · Data: ATR, news, vùng can thiệp. · Coupling: infra layer cho toàn bộ hệ thống.

**S99 — Meta-regime carry↔trend switch (Regime)** — Hypothesis: khi differential MỞ RỘNG → regime trend (momentum thắng); khi differential ỔN ĐỊNH/HẸP → regime carry-range (MR/carry thắng) — sign của Δ(differential) chọn bộ máy. · Signal: 3M Δ(2Y diff) >+30bp → trend mode; |Δ|<10bp → carry-range mode. · Trade: allocator chuyển vốn giữa S1/S6 (trend) và S31/S11 (carry-range). · Risk: transition zone nhảy đôi; policy coordination (2026) làm differential hẹp nhanh — cả hai mode đau. · Data: swap 2Y, các sub-strategy PnL proxy. · Coupling: là cách triển khai tự nhiên của hypothesis "carry là trục" của symbol này.

**S100 — Crisis-alpha long-JPY overlay (Regime/Options)** — Hypothesis: khi S&P dưới 200DMA và credit spreads nở (CDX HY >P80), JPY có beta dương với khủng hoảng — dùng long JPY (short USDJPY hoặc long JPY calls) làm tail-hedge thay/ngoài gold. · Signal: 2/3 điều kiện trên thoả. · Trade: cứa long 1M JPY call OTM 2% kích thước 0.3%/tháng premium budget, roll khi chưa kích hoạt. · Risk: кризис có inflation-led (JPY yếu do energy) → hedge sai hướng; cost bleed trong bull market. · Data: S&P, CDX, options. · Coupling: đối chiếu S63 — nếu gold cũng bid thì khủng hoảng "thật" (none-inflation) → JPY hedge đúng.

---

## 3. Tổng hợp cho symbol

### 3.1. Top-10 ideas (ưu tiên nghiên cứu sâu tiếp)

| # | Idea | Vì sao chọn cho USDJPY |
|---|---|---|
| 1 | **S31 + S36** (carry core + carry/vol gate) | Trục kinh tế của symbol; gate là bài học trực tiếp từ Aug/2024 & Jul/2026 — carry không chết, chỉ cần kill-switch đúng. |
| 2 | **S56** (intervention detection & join) | Edge bất đối xứng lớn nhất riêng USDJPY; footprint có thể nhận diện realtime (1-min range σ + volume + vùng giá); MOF đã can thiệp 3 cycles 2022/2024/2026 — đủ data để rule hóa. |
| 3 | **S98** (intervention-veto vol targeting) | Bảo hiểm hệ thống cho MỌI ý khác; without it mọi backtest đẹp đều ảo trên các ngày can thiệp. |
| 4 | **S4 + S61** (UST10Y momentum + lead-lag convergence) | Kênh truyền mạnh & bền nhất từ 2022; có nền lý thuyết (real-money allocation theo differential). |
| 5 | **S74** (positioning-regime flip follow) | Trạng thái HIỆN TẠI (9/2026: historic positioning reversal sau can thiệp phối hợp) — regime inertial 4–8 tuần là cơ hội đang mở. |
| 6 | **S44** (March repatriation seasonality) | Flow cấu trúc duy nhất có lịch cố định và rationale kinh tế rõ; cần kiểm định rolling trên 20+ năm. |
| 7 | **S25 + S51** (BoJ event complex) | BoJ đang trong hiếm normalization cycle (rate ~1.00%, board split 2026) — event stream dày hawkish surprise; straddle + fade-the-spike là cặp complements. |
| 8 | **S66** (VIX-threshold carry unwind short) | Đơn giản, robust, hedge tự nhiên cho portfolio risk; kênh safe-haven là đặc thù JPY. |
| 9 | **S71 + S72** (COT extremes + divergence) | Dữ liệu công bố miễn phí, tuần; hai episode lớn 2024/2026 đều có cảnh báo positioning cực đoan trước đó. |
| 10 | **S99** (meta carry↔trend switch) | Cách tổ chức toàn bộ symbol thành một hệ thống nhất quán với hypothesis "carry là trục". |

### 3.2. Bẫy overfitting đặc thù khi backtest USDJPY

- **Intervention outliers**: 5 cluster can thiệp (9–10/2022, 4–5/2024, 7/2024, 7–8/2026) chi phối tail distribution. Nếu backtest dùng daily bar + stop fill tại giá stop → giả định sai (gap qua stop 200–800 pips, slippage phi tuyến). Phải: (a) mô phỏng fill tại mức tệ hơn (stop + k×ATR), (b) chạy riêng subsample exclude-inclusion các cluster, (c) không dùng dữ liệu MOF disclosure (ex-post) làm input realtime — lookahead bias kinh điển.
- **Gap fills phi tuyến**: weekend gap & Monday Tokyo open mỏng liquidity — mean-reversion backtest trên close-to-close cao估 entry khả thi.
- **Policy-regime structural breaks**: 3/2024 (YCC end), 7/2024, 1/2025, 12/2025, 2026 hikes, 7–8/2026 can thiệp phối hợp — mọi tham số fit full-sample (beta vs rates, cointegration, seasonality) phải kiểm định per-regime.
- **Carry accounting**: backtest carry phải tính forward points/swap thực (không phải spot-only) — nếu không, MR trades hold-đêm bị bias, carry trades bị định giá sai hoàn toàn.
- **Survivorship của correlation**: corr(USDJPY, UST10Y) & corr với gold đổi dấu giữa regime — rolling-window validation bắt buộc; FDR correction cho mọi ý dạng heatmap/scan (S50, S86).
- **Sample nhỏ của event studies**: BoJ surprise, shunto, can thiệp — đếm trên đầu ngón tay; tránh kết luận từ <10 sự kiện, ghi rõ confidence.
- **Vol regime dependence**: hầu hết ý MR chỉ thắng vol-thấp, Trend chỉ thắng vol-cao — backtest chung sẽ average hai chế độ thành "không edge" ẩn gerçek edge ở từng chế độ.

### 3.3. MUST-WATCH weekly macro checklist (cho owner/UI theo dõi)

1. **BoJ**: lịch MPM tiếp theo + OIS-implied xác suất hike; Ueda PC tone; SOO/Minutes release date; dissent count (board split 2026 là tín hiệu dẫn hike). Kiểm chứng policy rate hiện hành (kết quả meeting Sep/2026) và mức taper JGB.
2. **Fed/UST**: FOMc dot path (một hike nữa 2026 → 4.00–4.25%); UST 10Y & 2Y levels + 20d momentum; lịch auctions 10Y/30Y (tails).
3. **Vùng can thiệp**: cập nhật "risk zone" — hiện hành ~158–160+ (sau episode Jul–Aug 2026 can thiệp ~160–164 với phối hợp Mỹ; verbal thường bắt đầu thấp hơn 2–4 JPY). Theo dõi phát ngôn Kato/Mimura, rate-check rumors, và MOF monthly FX disclosure (cuối tháng kế tiếp).
4. **Risk sentiment**: VIX, AUDJPY (barometer), Nikkei, S&P vs 200DMA, credit spreads.
5. **JPY-specific flows/positioning**: COT IMM JPY net specs (P90/P10), MOF weekly portfolio flows, LSEG/prime-broker positioning narratives.
6. **Japan data**: Tokyo CPI (cuối tháng) & CPI quốc gia (giữa tháng), Tankan (đầu quý), shunto season (Feb–Mar), wage data.
7. **Seasonality flags**: tháng 3 (fiscal year-end repatriation), 30/09 (semi-annual), Golden Week/Obon, Wednesday triple-swap, Tokyo fix cuối tháng.
8. **Options**: 1M IV level & 1M/3M ratio trước event; 25Δ RR extremes; lớn barrier/expiry tại các mức tròn.
9. **Correlation health**: rolling 30d corr(USDJPY, ΔUST10Y) — breakdown = stand-down rates-strategies (S97).
10. **CIP basis (JPY 3M)** — gauge funding stress cho S38.

---

### Appendix — Các dữ kiện time-sensitive đã verify (nguồn: WebSearch 2026-09-28)

- Fed 16/09/2026: hike +25bp → 3.75–4.00%, lần đầu kể từ 2023, nhất trí 12/12, Chair Kevin Warsh; dot plot còn 1 hike 2026 (end-2026 4.00–4.25%). (federalreserve.gov, Reuters, NYT, Chase)
- BoJ: hike 12/2025 lên mức 30-năm; 1/2026 hold; 4/2026 vote chia rẽ lớn nhất 10 năm; 7/2026 stand-pat, OIS ~69% hike trước 10/2026; 8/2026 Morgan Stanley dẫn policy rate "at just 1%"; 9/2026 kỳ vọng hike 25bp nữa quanh meeting cuối tháng **(kết quả cần kiểm chứng)**.
- Can thiệp 7–8/2026: yen qua 160 (lần đầu sau 7/2024), chạm ~164; can thiệp phối hợp Nhật (~$75bn) – Mỹ (~$5–10bn, Fed phối hợp BoJ) — "biggest in 15 years" (Goldman); yen bật về ~152 rồi ~163 giữa 8/2026; 9/2026 giao dịch ~152.9–154.5, "suspected rate check" giữa tháng, positioning reversal "historic" theo LSEG. (Reuters 30/07/2026, OMFIF, forex.com 19/09/2026)
- Còn **(cần kiểm chứng)**: mức chính xác VIX/Nikkei ngày 05/08/2024; số liệu BIS 2025 turnover JPY; NIIP hiện tại; lịch BoJ MPM 2026 cụ thể; kết quả BoJ Sep/2026; mức taper JGB hiện hành.
