# USDCHF — Deep Dive & 100 Strategy Ideas

> Lane: **USDCHF** · Program: FOREX-UNIFIED-STRATEGY-BRAINSTORM-V1 · Ngày: 2026-09-28
> Loại产出: knowledge-only brainstorm (không backtest). Mọi con số mang tính tham khảo,
> phải re-measure trên data thật trước khi tin. Các mục gắn *(cần kiểm chứng)* chưa verify được.

## 0. Fakta đã verify (WebSearch, 2026-09-28)

- **SNB policy rate = 0%**, giữ nguyên tại họp 24/09/2026 (lần thứ liên tiếp trong năm 2026);
  Swiss CPI tháng 8/2026 ≈ **0.8%** (trong band mục tiêu 0–2%); họp kế tiếp **10/12/2026**;
  market цен first hike ~tháng 3/2027. SNB dùng **tiered remuneration**: sight deposits vượt
  threshold được trả **−0.25%** (policy rate 0% + phạt 0.25pp) — nguồn "0.25%" lẫn lộn trên
  mạng là mức phạt tầng vượt hạn mức, không phải policy rate.
- **Fed đã hike 25bp ngày 16/09/2026 lên 3.75–4.00%** — lần tăng đầu tiên kể từ 2023, vote
  12–0, signal thêm ít nhất một hike nữa. Khớp với kết luận của lane EURUSD.
- **Chênh lệch lãi suất SNB–Fed ≈ −375 tới −400bp** → USDCHF đang ở chế độ carry thuận
  chiều mạnh cho long USDCHF (CHF = funding currency kinh điển).
- **SNB can thiệp FX**: tháng 7/2025 sight deposits tăng vọt **+CHF 11.2 tỷ trong 1 tuần**
  (lên ~CHF 475.3 tỷ) → thị trường đọc là SNB mua ngoại tệ bán CHF; FX positions của SNB
  ~**CHF 879 tỷ** (6/2026, FRED). Heuristic market: **WoW jump ≥ CHF 5–15 tỷ = dấu vết can
  thiệp**, phát hành hàng tuần.
- Mức giá tham khảo 9/2026: **USDCHF ≈ 0.81**; **EURCHF ≈ 0.930–0.945** (đỉnh đầu năm
  0.9451 ngày 14/09 sau ECB hike — *(cần kiểm chứng chi tiết ECB)*); BNP Paribas giữ CHF là
  "safe-haven currency" với target 12 tháng EURCHF 0.92.

---

## 1. Bản chất instrument

### 1.1 Microstructure & sessions

- **Quy ước giá**: quote 5 chữ số thập phân (0.81234), 1 pip = 0.0001, pipette = 0.00001.
  Spread retail điển hình **0.7–2.0 pips** (account ECN), rộng hơn EURUSD/USDJPY nhưng hẹp
  hơn mọi cặp CHF chéo. Slippage tăng vọt quanh SNB events và geopolitical shocks.
- **Tương quan thanh khoản**: USDCHF thuộc nhóm major nhưng **CHF được trade tích cực nhất
  ở cặp chéo EURCHF** — nghĩa là CHF-leg của USDCHF "thừa hưởng" độ sâu thanh khoản mà thị
  trường định giá CHF chủ yếu qua EURCHF. Do đó USDCHF về mặt thực nghiệm ≈ EURUSD "đảo
  dấu" + một lớp idiosyncratic CHF. Doanh số ước ~5% turnover FX toàn cầu (BIS Triennial,
  top-10 pair) — *(cần kiểm chứng con số chính xác theo survey mới nhất)*.
- **Sessions**:
  - **Asian (Tokyo)**: mỏng nhất; USDCHF hay dính range hẹp, nhưng **đây lại là khung giờ
    CHF bid khi có rủi ro địa chính trị Á/đêm Mỹ** — spike sáng Tokyo không hiếm (ví dụ flash
    move đầu tháng 1/2019 ở CHF crosses).
  - **London (07:00–16:00 UTC)**: CHF là đồng tiền châu Âu → London là session chủ lực;
    Zurich fix (**15:15 CET / WM|Reuters 4pm London**) tạo window flow định giá.
  - **Overlap London–NY (13:00–16:00 UTC)**: thanh khoản + volatility cao nhất, nơi các
    breakout có follow-through tốt nhất.
  - **NY muộn / rollover (21:00–01:00 UTC)**: mỏng, swap/rollover cost áp đảo edge của mọi
    intraday strategy; flash-gap risk.
- **Chi phí giao dịch đặc thù**: với chính sách 0% của SNB, chi phí funding CHF thấp, nhưng
  **swap dài của long USDCHF hiện dương lớn** (thu carry) — mọi backtest intraday phải tách
  bạch PnL giá vs PnL swap; mọi backtest multi-week phải model swap thực của broker.

### 1.2 Điểm ĐẶC BIỆT riêng USDCHF

**(a) CHF = safe haven có "người giữ}".**
- Nền tảng kinh tế: trung lập chính trị >200 năm, current account surplus cấu trúc
  (đầu tư ra nước ngoài lớn → dòng lợi nhuận về CHF), lạm phát thấp kinh niên, trung tâm
  tài chính Zurich/Geneva, hệ thống ngân hàng úy thác. Khi risk-off toàn cầu (geopolitics,
  khủng hoảng ngân hàng châu Âu, stress chính sách), dòng "haven bid" vào CHF dồn dập.
- Hệ quả định lượng: **phân phối return USDCHF lệch trái (left fat tail)** — các cú sụt
  nhanh 1–3% trong phiên è cổ phiếu. Đây là khác biệt gốc so với EURUSD: cùng USD-leg nhưng
  CHF-leg có "spring" chạy ngược risk.

**(b) SNB intervention risk — bài học 2015 phải kể đúng.**
- 06/09/2011: giữa khủng hoảng nợ eurozone, SNB đặt **floor EURCHF 1.20** ("maximum
  exchange-rate"), cam kết mua ngoại tệ không giới hạn. Ba năm giữ floor, dự trữ phình to.
- 15/01/2015: SNB **bỏ floor đột ngột** (kết luận ECB-QE sẽ khiến việc giữ floor bất khả
  thi/đắt đỏ), đồng thời cắt lãi suất từ −0.25% xuống **−0.75%**. EURCHF rơi từ 1.20 xuống
  intraday ~0.85 (**≈ −30% trong vài phút**), khép phiên còn ~1.03 (−13/−15%); USDCHF sụt
  cỡ 20–25% intraday trước khi khép lại còn ~ −13%. Hệ quả thị trường: một số broker vỡ
  (Alpari UK), khách retail âm tài khoản, liquidity toàn thị trường CHF biến mất vài phút.
- Bài học đúng cho 2026: SNB **không còn floor**, nhưng **vẫn can thiệp hai chiều** và đã
  từng can thiệp bán CHF (mua ngoại tệ) trong 2025 khi lãi suất về 0 (bằng chứng sight
  deposits tháng 7/2025). Interventions hiện nay là **đa dạng quy mô** (nhỏ, liên tục, qua
  kênh sight deposits) thay vì cam kết floor → tail risk thấp hơn 2015 nhưng **bias-chiều
  bất đối xứng vẫn còn**: khi CHF mạnh quá nhanh, xác suất SNB "làm gì đó" cao.
- Ký ức 1.20 tạo **"floor memory"** ở EURCHF: mỗi lần EURCHF về vùng thấp lịch sử, thị
  trường pricing sẵn khả năng SNB phản ứng → hiệu ứng hỗ trợ kép quanh các mốc đó.

**(c) EURCHF shadow.**
- Do CHF được định giá chủ yếu qua EURCHF, USDCHF gần như là "EURUSD đảo dấu + phần dư CHF".
  Khi EURUSD đi trend mạnh, USDCHF đi trend ngược gần như cơ học; khi EURCHF tự break (ECB
  vs SNB divergence, năng lượng, bầu cử Pháp/Đức), USDCHF trượt theo một cách "vô lý" nếu
  chỉ nhìn Mỹ. Bất kỳ model nào bỏ sót EURCHF là bỏ sót một nửa phương trình.

**(d) Low-vol nhiều giai đoạn.**
- Kết hợp (a)+(b): SNB có động cơ nén vol CHF (chống CHF quá mạnh), cộng tính chất haven
  khiến realized vol USDCHF thường **thấp hơn EURUSD/GBPUSD ở pha bình thường**, rồi nhảy
  vọt gấp 3–5 lần trong sự kiện. Mặt bimodal vol này định hình cả chương trình strategy:
  range/MR strategies sống ở pha 1, chết ở pha 2; breakout ngược lại.

**(e) CHF như funding currency trong carry.**
- Lãi suất CHF nằm đáy G10 gần như liên tục từ 2010s (âm 2015–2022; về 0% giữa 2025 sau
  chuỗi cắt từ đỉnh 1.75% năm 2023 — *(cần kiểm chứng từng bước cắt)*). Với Fed 3.75–4.00%
  (9/2026), CHF là một trong hai funding legs chuẩn của carry toàn cầu (cùng JPY). Carry
  regime = USDCHF có drift lên "nuôi swap"; carry-unwind (risk-off) = cú giật xuống mạnh
  nhất — bất đối xứng này là hạt nhân của cả family Carry ở Section 2.

### 1.3 Tin tức/sự kiện ảnh hưởng

**Scheduled (lịch cố định)**

| Sự kiện | Nhịp | Kênh truyền (transmission) | Cường độ điển hình |
|---|---|---|---|
| SNB Monetary Policy Assessment | Quarterly (T3/2026: 19/3, 18/6, 24/9 đã xong; 10/12 kế tiếp) — *(kiểm chứng ngày 2027)* | Policy rate + forecast CPI/GDP + câu chữ về CHF "appropriately valued / overvalued" → kỳ vọng lãi suất & kỳ vọng can thiệp | Cao: 60–150 pips trong phút; đôi khi "non-event" nếu hold đúng consensus |
| Swiss CPI (FSO) | Đầu mỗi tháng | Kích hoạt/nuôi kỳ vọng SNB easing/hiking → CHF-leg | Trung bình 20–40 pips |
| KOF Barometer (ETH) | Cuối tháng | Leading indicator kinh tế Thụy Sĩ → CHF-leg trung hạn | Thấp–trung |
| Swiss PMI, GDP, SECO outlook, trade balance, unemployment | Tháng/quý | Vĩ mô Thụy Sĩ, thường chỉ material khi cực端 | Thấp |
| Fed FOMC (16/9/2026 vừa hike 3.75–4.00%; kế tiếp ~27–28/10 và 8–9/12 — *(cần kiểm chứng)*) | 8 lần/năm + dot plot + presser | USD-leg qua đường lãi suất kỳ vọng | Cao cho mọi cặp USD |
| US NFP | Friday đầu tháng | USD-leg | Cao |
| US CPI / PCE | Giữa/cuối tháng | USD-leg, hiện là driver số 1 của Fed path | Cao |
| ISM, retail sales, claims, GDP | Tuần/tháng | USD-leg | Trung bình |
| ECB & dữ liệu eurozone (đặc biệt sau đợt ECB hike 9/2026 — *(cần kiểm chứng)*) | 8 lần/năm | EUR-leg → trượt qua EURCHF → shadow lên USDCHF | Trung bình–cao bất thường |
| BoJ (cho kênh CHFJPY/carry) | 8 lần/năm | Carry unwind risk | Gián tiếp |

**Unscheduled (không lịch)**
- **Geopolitical shocks** (chiến tranh, khủng hoảng ngân hàng EU — testcase Credit Suisse
  3/2023: USDCHF rơi thẳng, EURCHF về ~0.93; stress nợ công eurozone): kênh = haven bid.
- **SNB action/rumor**: sight-deposit jump hàng tuần, phát ngôn chủ tịch (Martin Schlegel
  từ 10/2024 — *(cần kiểm chứng)*) than phiền "CHF quá mạnh" → tín hiệu bán CHF sắp diễn ra.
- **Carry-unwind toàn cầu** (AUDJPY/CHF sập): dòng tiền cover funding leg.
- **Flash events** phiên mỏng (đầu tháng 1/2019): stop-cascade, liquidity hole.
- Kênh truyền chung của nhóm này: **không qua fundamentals, qua flow thị trường** → giá
  quá shoots rồi thường partially revert (nếu nguyên nhân là noise) hoặc trend tiếp (nếu
  nguyên nhân thật) — chiến lược cần phân biệt được hai trường hợp, xem S17/S97.

### 1.4 Thông số ảnh hưởng (driving factors)

1. **SNB–Fed rate differential & path kỳ vọng** (hiện −375/−400bp và Fed signal thêm hike):
   driver chậm, tạo drift & carry; phản ứng qua 2y swap differential là gauge sạch nhất.
2. **Risk sentiment**: VIX (mức + term structure), credit spreads, equities. Risk-off →
   USDCHF xuống bất chấp lãi suất. Đây là biến "gate" quan trọng nhất cho family Carry.
3. **Gold**: CHF và gold cùng mang chức năng haven; đồng thời cả hai đều "chống USD".
   XAUUSD lên kèm CHF mạnh → xác nhận risk-off thật (khác falsifiable với USD-move thuần).
4. **EURCHF flows**: chính sách ECB vs SNB, energy shock châu Âu, chính trị Pháp/Đức/Ý,
   M&A cross-border Thụy Sĩ. Shadow trực tiếp lên USDCHF.
5. **Intervention footprint**: sight deposits (tuần), FX positions (tháng), phát ngôn SNB.
6. **Dòng cấu trúc**: current account surplus Thụy Sĩ (hỗ trợ CHF dài hạn), chi trả cổ tức
  /thu hồi lợi nhuận, repatriation mùa cuối năm (year-end CHF funding squeeze có sử sách).

### 1.5 Correlation map (11 symbol trong universe)

Số liệu là **range điển hình của correlation daily-return** theo trải nghiệm giai đoạn
2015–2025 — **bắt buộc re-measure trên data của chính chương trình** trước khi dùng
(*(cần kiểm chứng bằng dữ liệu thực)*).

| Symbol | Corr với USDCHF (điển hình) | Ổn định? | Cơ chế |
|---|---|---|---|
| EURUSD | **−0.70 … −0.90** | Rất ổn định, quan trọng nhất | USD-leg chung đảo dấu + CHF≈EUR tạo "double link" |
| GBPUSD | −0.35 … −0.60 | Trung bình | USD-leg đảo dấu; GBP risk-on nhẹ |
| USDCAD | −0.20 … −0.50 | Thấp–trung | CAD commodity/risk-on ngược haven CHF;油价 episode lệch |
| USDJPY | **+0.20 … +0.50 (regime-dependent)** | Thấp | Hai haven chung USD-leg: cùng nhau khi USD-driven, cùng nhau khi risk-off (cả hai xuống), chỉ tách khi stress đặc thù châu Âu/Nhật |
| AUDUSD | −0.30 … −0.60 | Trung bình | Risk-on commodity ngược haven |
| NZDUSD | −0.25 … −0.50 | Trung bình | Như AUD, weaker |
| XAUUSD | **−0.20 … −0.50, đậm mạnh nhất trong khủng hoảng** | Episodic | Gold & CHF cùng haven, cùng "chống-USD" |
| XAGUSD | −0.15 … −0.40 | Thấp, nhiễu công nghiệp | Bản sao yếu hơn của gold |
| BRENT | −0.10 … −0.30 | Episodic | Oil spike = shock lạm phát/địa chính trị → CHF haven bid (đặc thù châu Âu) |
| WTI | −0.10 … −0.25 | Thấp | Như Brent, gắn Mỹ hơn |
| NATGAS | ~0 (±0.15) | Không ổn | Gas shock đánh EUR mạnh hơn CHF → đi qua EURCHF shadow thay vì trực tiếp |

**Breakdown / cách dùng:**
- **Hai chế độ tương quan cơ bản**: (i) *USD-driven* (Fed data, US yield) — USDCHF chạy
  cùng USDJPY, ngược EURUSD; (ii) *CHF-driven / risk-driven* (haven flows, ECB, SNB) —
  USDCHF chạy ngược cả EURUSD lẫn USDJPY. Cùng một mốc tin Mỹ có thể ra hai kết cục khác
  nhau tùy chế độ — strategy tốt phải condition, không averageblind.
- **EURUSD là hedge tự nhiên** gần 1:1.8 (beta USDCHF vs EURUSD ≈ −0.6/−0.7) nhưng khi
  EURCHF self-move, hedge này phá sản — đúng lúc cần nó nhất.
- **Gold & VIX là bộ lọc xác nhận haven-flow**: CHF bid + gold bid + VIX bid đồng thời =
  trend xuống USDCHF bền; CHF bid một mình = thường chỉ idiosyncratic (revert được).
- **NATGAS/BRENT** quan trọng ở khía cạnh *event*: gas spike châu Âu làm EURCHF rơi —
  với universe hiện tại dùng như gate cho EURCHF-shadow plays.

### 1.6 Note trung thực: họ strategy nào hay CHẾT trên USDCHF

- **Trend-following thô** chết trong pha SNB-nén-vol (range dài hàng tháng, ATR nhỏ → chi
  phí giao dịch ăn mòn); chỉ sống khi có gate regime (vol/rates/CHF-flow).
- **Mean-reversion & short-vol** chết bởi hai thứ: tail 2015-type (đã bỏ floor nhưng
  "bất đối xứng can thiệp" còn) và geopolitical gap. Mọi MR phải có kill-switch event.
- **Breakout** chết vì false-break quanh intervention rumor: giá đâm qua ngưỡng rồi bị
  SNB đập ngược trong cùng ngày (whipsaw lệch đỉnh).
- **Carry** chết đúng một lần duy nhất nhưng chết đủ vốn: carry-unwind risk-off (2008,
  2010, 2011, 2015, 3/2023). Carry không có vol-stop là timed bomb.
- **Scalp intraday quanh SNB days**: spread nở + slippage + gap qua stop → edge giả định
  biến mất sau cost thực.
- **Seasonality đơn biến** rất dễ overfit (mẫu hình 20 năm thường là 2–3 event gộp).

---

## 2. 100 Strategy Ideas

Quy ước: Timeframe viết tắt D/W = daily/weekly, H1/H4 = intraday. Mọi ngưỡng là điểm
khởi đầu để tối ưu, không phải kết luận. "Data" liệt kê dữ liệu tối thiểu để kiểm định.

### Family A — Trend / Momentum (S1–S10)

**S1 — Donchian dual-channel turtle (Trend/Momentum)** — Hypothesis: USDCHF có xu hướng đa tháng khi differential SNB–Fed rộng và SNB đứng ngoài thị trường, breakout 20/55 ngày bắt được phần lớn move · Signal: close D qua high 20 (entry) / 55 (regime), low 10 (exit) · Trade: theo trend, stop 2×ATR(20), pyramiding tối đa 2 lần · Risk: whipsaw trong phase SNB nén vol (xem S91 gate) · Data: OHLC D 10 năm, swap points · Coupling: chỉ bật khi slope 2y swap differential (US–CH) cùng dấu.

**S2 — MACD weekly + daily trigger (Trend/Momentum)** — Hypothesis: momentum tầng cao lọc nhiễu tầng thấp, tăng hit-rate trên pair low-vol · Signal: MACD(12,26) W cùng chiều histogram + MACD H4 flip cùng chiều · Trade: entry khi cả hai khớp, stop dưới swing H4 gần nhất · Risk: trễ vào, bỏ sót move kiểu gap SNB · Data: OHLC W/H4 · Coupling: VIX<20 để tránh đâm đầu vào haven-spike.

**S3 — 200DMA regime filter + momentum burst (Trend/Momentum)** — Hypothesis: trên/dưới 200DMA là ranh giới regime dài hạn có ý nghĩa kinh tế (differential kỳ vọng) · Signal: giá D vs 200DMA định chiều; entry burst = 2 ngày đóng cùng chiều > 0.5×ATR · Trade: long-only trên 200DMA, short-only dưới, stop 2.5×ATR · Risk: chết ở sideways quanh 200DMA (chop zone) · Data: OHLC D · Coupling: phương án only-long khi carry dương >200bp.

**S4 — ADX-gated directional movement (Trend/Momentum)** — Hypothesis: chi phí trend-strategy nằm ở ngày vô xu hướng; ADX>25 tách được hai pha trên USDCHF bimodal-vol · Signal: ADX(14) D >25 và DI+ > DI− (hoặc ngược) · Trade: hold theo DI cross, thoát khi ADX<20 · Risk: ADD lag sau cú intervention-reversal — stop sự kiện riêng · Data: OHLC D · Coupling: sight deposits tuần đi ngang (SNB không can thiệp) mới cho phép trend chạy.

**S5 — EMA-ribbon slope riding H4 (Trend/Momentum)** — Hypothesis: trong London session, stack 3 EMA (20/50/200 H4) slope đồng hướng giữ chân intraday trend USD-leg · Signal: 3 EMA xếp lớp đúng thứ tự + giá pullback chạm EMA20 không xuyên · Trade: entry tại retest, stop dưới EMA50 H4, thoát khi ribbon flat · Risk: London fix reversal 15:15 CET · Data: OHLC H4 có timestamp · Coupling: chỉ trade chiều USD-leg khi US yields cùng chiều.

**S6 — Policy-divergence ignition continuation (Trend/Momentum)** — Hypothesis: cú hawkish-surprise của Fed tạo "ignition" — 3 ngày đầu sau FOMC hawkish có continuation, SNB-side không cản · Signal: Fed surprise (dot/stmt hawkish vs consensus) + USDCHF close ngày D1 cùng chiều >0.7×ATR · Trade: vào ngày D2 theo chiều surprise, stop dưới low D1, target 5–10 ngày · Risk: surprise bị haven-flow nuốt (gold cũng spike) · Data: lịch FOMC + consensus + OHLC · Coupling: VIX không vượt 25, gold không cùng chiều CHF.

**S7 — 52-week-high absolute momentum (Trend/Momentum)** — Hypothesis: time-series momentum (12-1) tồn tại ở FX majors; với USDCHF nó đồng thời tương thích carry chiều dương · Signal: giá D > max(close) 252 ngày trước đó · Trade: long duy nhất, trailing stop 15%, size theo vol · Risk: mua đỉnh ngay trước risk-off — cần vol-target nghiêm · Data: OHLC D dài hạn ≥15 năm · Coupling: bật khi 3M USD–CHF swap differential >+150bp.

**S8 — Cross-sectional G10 dollar-pair momentum (Trend/Momentum)** — Hypothesis: xếp hạng momentum 3 tháng của các cặp USD (EURUSD đảo dấu, USDJPY, USDCAD, USDCHF, AUDUSD đảo dấu) có autocorrelation; dài winner rút ngắn loser giảm noise đơn pair · Signal: rank 63 ngày, top-quartile long / bottom short, rebalance tuần · Trade: basket bằng USD-notional, beta-neutral hoá phần USD · Risk: rotation nhanh quanh regime Fed · Data: OHLC D 6 cặp USD · Coupling: none — đây là nền tảng multi-symbol.

**S9 — Post-shock gap regime-join (Trend/Momentum)** — Hypothesis: sau cú gap sự kiện (SNB/geopolitics) >3×ATR, ngày 2–5 có continuation vì vị thế thị trường chưa kịp điều chỉnh (bài học ngược của 2015: những ai join new-regime sớm sống) · Signal: gap qua mức + close ngoài gap + không fill ≥50% trong 3 phiên · Trade: enter sau phiên xác nhận, stop tại mép gap, hold tới khi ATR về median · Risk: gap được fill = false regime · Data: OHLC intraday quanh event lịch sử · Coupling: xác nhận bằng gold/VIX đồng chiều haven.

**S10 — Ichimoku Kumo-twist daily (Trend/Momentum)** — Hypothesis: hệ chỉ báo Ichimoku vốn sinh ra cho thị trường Nhật nhưng đã trở thành standard self-fulfilling ở FX; Kumo twist bắt sự chuyển regime chậm của USDCHF · Signal: tenkan/kijun cross trên/v dưới cloud + cloud đổi màu · Trade: theo twist, stop dưới kijun, partial tại Senkou B · Risk: nhiễu nhiều twist trong range — chỉ tin twist khi |twist| xảy ra ngoài cloud · Data: OHLC D · Coupling: none.

### Family B — Mean-reversion (S11–S20)

**S11 — Bollinger-squeeze fade trong quiet regime (Mean-reversion)** — Hypothesis: khi ADX<20 và BB(20,2.5) D hẹp, USDCHF oscillate quanh mean vì không có driver — fade band chạm là edge cổ điển · Signal: giá chạm band ±2.5σ + RSI(14) >70/<30 · Trade: fade về midline, stop 1.2×ATR ngoài band · Risk: breakout thật (event) — kill-switch lịch SNB/Fed/CPI · Data: OHLC D + calendar · Coupling: chỉ chạy khi sight deposits tuần đi ngang (SNB đứng ngoài).

**S12 — RSI(2) Connors-style với 200DMA flat (Mean-reversion)** — Hypothesis: mô hình RSI(2) cực端 trên SPX nổi tiếng; trên USDCHF hoạt động khi 200DMA slope |<0.02%/ngày| (range thực sự) · Signal: RSI(2)<5 (long) / >95 (short) giá trên/dưới EMA5 · Trade: enter close, exit khi RSI(2)>50 hoặc 5 phiên · Risk: ăn đòn tail trong trending · Data: OHLC D · Coupling: gate slope 200DMA + không event tuần đó.

**S13 — Asian-extreme fade tại Frankfurt open (Mean-reversion)** — Hypothesis: phiên Asian mỏng đẩy giá lệch khỏi equilibrium London; London re-opens và kéo về · Signal: từ 00:00–06:00 UTC giá đi >0.35% một chiều khỏi VWAP daily trước đó · Trade: 06:00 UTC enter ngược, target VWAP hôm qua, stop 0.6×ATR(H1) · Risk: khi spike là thật (địa chính overnight) — filter tin trước khi vào · Data: tick/H1 có session stamp · Coupling: nếu gold/VIX cùng spike overnight → bỏ trade.

**S14 — EURCHF-anchored reversion (Mean-reversion)** — Hypothesis: EURCHF gần như không di chuyển (SNB/ECB neo) thì mọi lệch USDCHF so với hàm EURUSD×EURCHF là noise USD → revert · Signal: residual USDCHF − (EURUSD×EURCHF) z-score 20 ngày vượt ±2 · Trade: trade residual: long USDCHF + short EURUSD 0.8 lot tương đương, target z=0 · Risk: residual thật = CHF-event đang diễn ra (sight deposits!) · Data: OHLC D 3 symbol + sight deposits · Coupling: tắt khi sight deposits WoW >+3 tỷ.

**S15 — Three-down-weeks + RSI(25) weekly bounce (Mean-reversion)** — Hypothesis: chuỗi 3 tuần một chiều liên tiếp trên USDCHF tự nó hiếm (mean-reverting ở tần số thấp khi không có differential-shift) · Signal: 3 tuần close giảm liên tiếp + RSI(14) W <30 · Trade: long tuần kế, exit +2 ATR(W) hoặc 4 tuần · Risk: trend tháng thứ 4 của carry-unwind · Data: OHLC W ≥20 năm · Coupling: chỉ long khi swap differential thuận (không bắt dao rơi ngược carry).

**S16 — VWAP-fade NY-afternoon (Mean-reversion)** — Hypothesis: sau 16:00 UTC thanh khoản mỏng dần, overextension trong ngày thường được拽 về VWAP trước close · Signal: 16:30 UTC giá lệch VWAP session >1.8×ATR(H1) mà không có tin mới · Trade: fade về VWAP, flat trước 20:00 UTC · Risk: late-US-news — chỉ chạy ngày không calendar đỏ · Data: tick intraday 2 năm · Coupling: none.

**S17 — Haven-spike partial-fade (Mean-reversion)** — Hypothesis: geopolical headline-shock có pattern 2 pha: overshoot 30–90 phút rồi partially revert nếu sự kiện không escalate; khác biệt với trend haven thật là gold/VIX giữ高水平 · Signal: USDCHF rơi >1% trong <60 phút trên headline; vào 90 phút sau nếu VIX đã đi ngang 15 phút · Trade: long USDCHF retracement 38–50% cú rơi, stop dưới low spike · Risk: escalation đêm — size nhỏ, không hold qua đêm đầu · Data: tick + news feed timestamped + VIX intraday · Coupling: S97 (dispersion) cùng подтвер.

**S18 — Intervention-cap fade trong Keltner zone (Mean-reversion)** — Hypothesis: khi sight deposits tăng liên tục (SNB đang bán CHF), vùng Keltner(20,2) trên USDCHF là "trần ảo" — giá bị cap nhưng không trend, fade trong biên · Signal: regime-flag SNB-selling (3 tuần liên tiếp deposits tăng) + giá chạm upper Keltner D · Trade: short về midline, stop trên 0.5×ATR ngoài band · Risk: Fed-leg break mạnh hơn cap SNB · Data: sight deposits weekly + OHLC D · Coupling: dovish SNB statement cùng quý.

**S19 — Z-score(20) extreme reversion (Mean-reversion)** — Hypothesis: phiên bản thống kê sạch của fade: z của close so SMA20 và σ20 vượt ±2.5 thì kỳ vọng revert về 0 trong 5–8 phiên khi vol-regime không đổi · Signal: z>2.5 short / z<−2.5 long, thoát khi |z|<0.5 · Trade: size nghịch đảo |z|, stop khi z>3.5 (regime shift admit) · Risk: cluster hóa trong trending — ADX gate · Data: OHLC D · Coupling: gộp vào S91 làm nhánh regime-1.

**S20 — Floor-trader pivot S3/R3 fade (Mean-reversion)** — Hypothesis: các mức pivot kinh điển (P, S1–3, R1–3) còn là mức mà community смотр; chạm S3/R3 trong ngày không-event hiếm khi tiếp tục · Signal: giá chạm R3 sau 14:00 UTC không có tin → fade về R2/P · Trade: scalp 15–25 pips, stop 12 pips ngoài R3 · Risk: trending day type (open-drive) — bỏ qua nếu giá chưa quay về P trong ngày · Data: OHLC H1 + pivot calc · Coupling: chỉ Tuesday–Thursday.

### Family C — Breakout / Vol-expansion (S21–S30)

**S21 — Asian-range London breakout (Breakout/Vol-expansion)** — Hypothesis: range Asian nén thông tin; London chọn hướng và continuation có mặt bằng thống kê ở pair có USD-leg mạnh · Signal: range 00:00–07:00 UTC < 0.6×ATR20(H1); stop-order 2 pip ngoài range · Trade: target 1×range rồi trailing 1×ATR; stop nửa range đối diện · Risk: false-break hai chiều (stop-hunt London) — yêu cầu 15m close ngoài range · Data: H1/tick + session stamp · Coupling: chiều breakout phải khớp sign của EURUSD-inverse cùng lúc.

**S22 — NR7 + inside-day trước US CPI (Breakout/Vol-expansion)** — Hypothesis: nén biên độ nhiều ngày liên tiếp trước dữ liệu CPI Mỹ làm "spring"; hướng breakout sau release có momentum thật · Signal: NR7 hoặc inside-day D trong 2 ngày trước CPI · Trade: straddle stop-order 3 pip ngoài high/low ngày trước, sau release; giữ bên thắng 3×ATR trailing · Risk: whipsaw cả hai bên nếu CPI in-line — exit con thua ngay · Data: OHLC D + release time chuẩn · Coupling: chỉ khi surprise >1σ consensus mới giữ dài.

**S23 — BB-width percentile squeeze breakout (Breakout/Vol-expansion)** — Hypothesis: vol cluster: sau khi BB-width vào decile dưới cùng (10th percentile 2 năm), expansion sắp tới và direction có tính continuation theo trend trước squeeze · Signal: BBW D < p10 + giá đóng ngoài band theo hướng EMA50 · Trade: enter breakout, stop mép squeeze-kênh, target 3×chiều cao kênh · Risk: đầu-cuối squeeze không đo được thời điểm — chấp nhận 早 vào · Data: OHLC D · Coupling: hướng cùng slope 2y swap differential.

**S24 — FOMC opening-range straddle (Breakout/Vol-expansion)** — Hypothesis: 30 phút đầu sau presser FOMC thiết lập range "thật"; break range đó có follow-through còn lại của phiên NY · Signal: OR 30 phút sau statement; stop-order ngoài OR khi có 2 nến M5 close cùng chiều · Trade: target 1.5×OR, stop 0.5×OR · Risk: presser hai chiều (Powell nói cả hawkish lẫn dovish) — cắt nhanh · Data: tick M5 quanh FOMC lịch sử · Coupling: dot-plot delta cùng chiều tăng xác suất.

**S25 — Round-number failed-break reversal (Breakout/Vol-expansion)** — Hypothesis: các mức 0.8000/0.8500 (bội số 500 pip) là nơi stops dày; đâm qua rồi quay vào trong 30–60 phút là pattern stop-flip có xác suất · Signal: break 0.xx00 trên M15/H1 rồi close lại trong vòng ≤60 phút · Trade: reversal entry khi quay vào, stop ngoài extreme của đâm, target đường EMA20 H1 · Risk: breakout thật (đặc biệt khi có event) — không dùng ngày SNB/Fed · Data: OHLC M15 · Coupling: vàng/VIX bình thường.

**S26 — Monday gap-and-go (Breakout/Vol-expansion)** — Hypothesis: gap mở cửa tuần chứa thông tin cum tích từ cuối tuần; gap không fill trong phiên Monday có continuation tuần đó · Signal: gap开盘 vs close Friday >25 pips; 17:00 UTC chưa fill >50% · Trade: enter theo chiều gap cuối Monday, stop full-fill level, hold tới cuối tuần · Risk: gap do thanh khoản mỏng (≤15 pips không tính) · Data: tick weekly opens 15 năm · Coupling: cùng chiều drift carry.

**S27 — Pre-SNB event straddle (Breakout/Vol-expansion)** — Hypothesis: implied vol trước SNB thường thấp hơn realized event-move trung bình khi thị trường expecting hold (complacency) → mua 2 phía bằng stop-orders (hoặc options) có giá trị kỳ vọng dương · Signal: 2 ngày trước SNB, 1M implied < median realized |move| các cuộc họp 3 năm · Trade: stop-order ±0.5×ATR(D) quanh giá, chiều thắng giữ 2–4 ngày, chiều thua tự cut · Risk: SNB non-event → chết cả 2 bên phí spread — version options tốt hơn · Data: OHLC + implied vol (broker/đại lý) · Coupling: các kỳ hold kéo dài liên tiếp tăng xác suất complacency.

**S28 — Post-ECB cross-vol drag (Breakout/Vol-expansion)** — Hypothesis: ECB event moves EURCHF trước, USDCHF trễ 1–3 phút do depth khác nhau → break EURCHF kéo USDCHF theo (statistical lead-lang dạng event) · Signal: EURCHF break range pre-ECB >0.3% trong 2 phút · Trade: enter USDCHF cùng hướng implied (EURCHF lên → short USDCHF 60%), thoát 30–60 phút · Risk: divergence khi move là EURUSD-driven (check EURUSD cùng lúc) · Data: tick 3 cặp + calendar · Coupling: chỉ dùng khi EURUSD flat trong window đó.

**S29 — ATR-expansion day-2 continuation (Breakout/Vol-expansion)** — Hypothesis: vol cluster: ngày có range >2×ATR(20) thường theo sau bởi ngày tiếp theo range cao hơn median và continuation 55%+ thời gian theo chiều close ngày 1 (khi không phải event SNB) · Signal: range D1 >2×ATR + close trong 30% biên của hướng · Trade: enter open D2 cùng chiều, stop 1×ATR, exit cuối D2 hoặc trailing · Risk: mean-revert sau haven-spike (dùng S17 phân loại) · Data: OHLC D + news label · Coupling: direction cùng carry bias thì size chuẩn, ngược thì nửa.

**S30 — Midweek-only breakout filter (Breakout/Vol-expansion)** — Hypothesis: breakouts Tuesday–Thursday có chất lượng follow-through tốt hơn Monday (gap-noise) và Friday (position-squaring) — hiệu ứng được ghi nhận rộng ở FX majors · Signal: mọi hệ breakout S21/S23 chỉ execute Tue–Thu · Trade: giữ nguyên logic gốc, chỉ đổi lịch · Risk: bỏ sót event-Monday moves — chấp nhận đổi lấy hit-rate · Data: OHLC + weekday stamp · Coupling: version đối chiếu Fri-Mon để đo chênh.

### Family D — Carry / Rate-differential (S31–S40)

**S31 — Classic positive-carry hold (Carry)** — Hypothesis: với differential −375bp (SNB 0% vs Fed 3.75–4.00%), long USDCHF thu swap dương lớn; trong regime vol thấp, carry chiếm ưu thế trung hạn · Signal: 3M USD–CH swap differential >+200bp + 1M implied vol USDCHF < median 1 năm · Trade: long spot, size để tail-loss ≤10% vốn (vol-target), roll mỗi ngày · Risk: carry-unwind — vol-stop bắt buộc · Data: swap rates broker, implied vol, OHLC · Coupling: S39 (VIX-stop) là bản sao rủi ro, dùng một trong hai.

**S32 — Carry + trailing drawdown stop (Carry)** — Hypothesis: carry không có stop chết chìm; thêm trailing 5% từ đỉnh equity giữ được phần lớn carry PnL và cắt trước unwind · Signal: điều kiện carry như S31 · Trade: long, trailing 5% trên giá hoặc equity, kích hoạt lại khi vol quay về thấp · Risk: whipsaw quanh ngưỡng trailing sau spike giả · Data: OHLC D + swap · Coupling: tái vào chỉ khi VIX<20.

**S33 — Carry basket đa funding-leg (Carry)** — Hypothesis: rủi ro unwind của CHF-leg giảm khi kết hợp long nhiều high-yield vs CHF (AUDCHF, NZDCHF, USDCHF) — correlation unwind cao nhưng không hoàn hảo · Signal: basket 3 cặp CHF-quote, weight nghịch đảo vol, chỉ khi carry trung bình >+150bp · Trade: rebalance tuần, vol-target tổng 10% · Risk: unwind đồng loạt (2008-style) vẫn giết cả basket · Data: OHLC 3 cặp + swap · Coupling: gate VIX term structure không inversion.

**S34 — Swap-differential momentum (Carry)** — Hypothesis: prices lead levels:/change của 2y swap differential (US–CH) dự báo hướng USDCHF 4–12 tuần tốt hơn bản thân differential · Signal: Δ 2y swap differential 20 ngày > +10bp (long) / <−10bp (short) · Trade: vị thế theo sign, size theo |Δ| chuẩn hoá, rebalance tuần · Risk: divergences khi SNB can thiệp hãm path · Data: yield/swap curves hai nước · Coupling: Fed-hawkish-oops (S37) thường là catalyst khởi động.

**S35 — Carry-to-vol ratio filter (Carry)** — Hypothesis: carry chỉ có edge khi tỷ lệ carry annualized / implied vol (tương tự Sharpe kỳ vọng) >0.5; dưới mức đó phí rủi ro tail không đáng · Signal: (3M carry) / (1M implied vol) >0.5 · Trade: bật/tắt exposure carry theo điều kiện, giữ directional rules của S31 · Risk: ratio đứng im trong dàikań giai đoạn → ít giao dịch (tốt chứ không xấu) · Data: swap + implied vol lịch sử · Coupling: chính là gate dùng lại cho S91.

**S36 — Negative-carry reversal short (Carry)** — Hypothesis: khi differential đảo chiều (Fed cắt về dưới SNB), USDCHF có drift xuống + carry thuận cho short — phần đối xứng của chu kỳ · Signal: 3M differential <−50bp và giảm 2 quý liên tiếp · Trade: short spot, vol-target, roll · Risk: SNB bán CHF đồng thời (kiểm sight deposits) sẽ hãm move xuống · Data: swap curves + sight deposits · Coupling: kích hoạt thêm khi deposits tăng (SNB yếu CHF cùng lúc).

**S37 — Hawkish-surprise carry-add (Carry)** — Hypothesis: thêm vào vị thế carry trong các dip 2–3 ngày sau Fed hawkish surprise mua được mức với xác suất continuation cao (differential sắp nới) · Signal: sau FOMC hawkish surprise, RSI(5) D <35 trên nền trend lên · Trade: add 50% size gốc, stop chung 2×ATR dưới entry trung bình · Risk: surprise là đỉnh chu kỳ hike (last-hike phenomenon) · Data: lịch FOMC + consensus + OHLC · Coupling: dots cho thấy còn hike (như tín hiệu 9/2026 "one more") thì add.

**S38 — FX-swap roll-down harvest (Carry)** — Hypothesis: đường forward USDCHF dốc thuận (contango do chênh lệch lớn); mua spot + bán forward 3M, giữ tới expiry, roll lại — thu roll-down với durée ngắn và ít directional risk · Signal: annualized forward-point roll >150bp · Trade: spot vs forward swap leg qua broker hỗ trợ FX swaps / futures spread · Risk: basis-widening khi stress dollar funding (mất thanh khoản close sớm) · Data: forward curve lịch sử · Coupling: theo dõi cross-currency basis (XCCY) như gauge stress.

**S39 — VIX-hard-stop carry (Carry)** — Hypothesis: mô hình carry chết khi VIX term structure inverted (front > 3M) — tín hiệu unwind sớm nhất quan sát được; dùng làm stop duy nhất đơn giản hoá quản trị · Signal: VIX futures M1 > M3 bất kỳ ngày nào · Trade: đóng toàn bộ carry trong ngày, tái mở khi cấu trúc bình thường 5 phiên liên tiếp · Risk: whipsaw quanh ngưỡng (mở/đóng vài lần/năm → cost chấp nhận) · Data: VIX futures term structure · Coupling: thay cho vol-stop của S31/S32 — không chồng lấp.

**S40 — December-meeting carry pause (Carry)** — Hypothesis: rủi ro bất đối xứng quanh SNB December (lịch can thiệp/chính sách bất thường từng diễn ra: floor bỏ tháng 1 sau họp 12/2014; year-end CHF funding stress) không bù bằng carry 2 tuần · Signal: flat carry từ 3 phiên trước tới 3 phiên sau SNB Dec · Trade: đơn giản là de-risk window cho mọi family Carry · Risk: bỏ lỡ continuation — chấp nhận · Data: lịch SNB + OHLC lịch sử Q4/Q1 · Coupling: khớp với S47 (year-end CHF squeeze).

### Family E — Session / Time-of-day / Seasonality (S41–S50)

**S41 — Overlap-session momentum (Session)** — Hypothesis: 13:00–16:00 UTC có density flow cao nhất; momentum 15 phút đầu overlap có continuation đến cuối phiên NY · Signal: break high/low 12:00–13:00 trong 15 phút đầu overlap · Trade: theo hướng break, stop ngoài extreme giờ trưa, flat 20:00 UTC · Risk: news 14:00 UTC đảo chiều — bỏ ngày có calendar đỏ giờ đó · Data: M15 + calendar · Coupling: hướng phải khớp EURUSD-inverse sign.

**S42 — Frankfurt-open reversal (Session)** — Hypothesis: Frankfurt 07:00 UTC thường đảo chiều drift của phiên Asian (thanh khoản châu Âu thực đến sau 07:30) — phiên bản thời điểm cụ thể của S13 · Signal: nếu Asian trending >0.3%, đợi nến M15 Frankfurt break ngược EMA(H1)20 · Trade: vào ngược hướng Asian-drift, target Asian mid, stop extreme Asian · Risk: Asian trend có nguyên nhân thật (tin đêm) · Data: tick/M15 session-stamped · Coupling: gold flat qua đêm thì mới vào.

**S43 — WM/Reuters fix-window drift (Session)** — Hypothesis: cửa sổ 15:15 CET (4pm London fix) có order-flow institution tập trung; đo được drift có hệ thống trong 10 phút trước fix theo hướng flow cuối ngày, self-fulfilling qua weighted vote các bank · Signal: hướng giá 30 phút trước fix + imbalance tin tức Mỹ trong ngày cùng dấu · Trade: vào 15:45–15:50 CET theo hướng đó, thoát sau fix 5 phút · Risk: cấu trúc benchmark đã đổi sau scandal fix 2015 — hiệu ứng suy yếu *(cần kiểm chứng bằng data gần)* · Data: tick 4 năm gần nhất với phút stamp · Coupling: chỉ dateráng có trọng số flow rõ (payroll week).

**S44 — Month-end rebalancing flow (Session/Seasonality)** — Hypothesis: quỹ toàn cầu cân bảng vào cuối tháng; nếu tài sản Mỹ tăng mạnh trong tháng → bán USD mua CHF/EUR cuối tháng (rebalancing bán USD) → USDCHF nghiêng xuống 2 ngày cuối tháng · Signal: return MSCI USA − World tháng đó >+2% → bias short cuối tháng · Trade: short 2 ngày cuối tháng, cover ngày làm việc đầu tháng kế · Risk: chiều flow đảo khi tài sản Mỹ giảm — dùng dấu điều kiện · Data: index equity + OHLC D · Coupling: mạnh hơn trong quý 4 và sau tháng Fed-hike.

**S45 — Turn-of-month effect (Seasonality)** — Hypothesis: 4 ngày cuối tháng + 3 ngày đầu tháng có drift thuận chiều carry (liquidity + salary/pension flows) được ghi nhận ở nhiều asset class · Signal: cửa sổ TOM + điều kiện carry như S31 · Trade: chỉ long USDCHF trong TOM khi carry dương; ngoài TOM flat · Risk: TOM trùng SNB/Fed → skip · Data: OHLC D 20 năm · Coupling: la ghép với S31 thành version timing-aware.

**S46 — August risk-off bias (Seasonality)** — Hypothesis: tháng 8 thanh khoản mỏng (Europe holiday) + lịch sử các cú risk-off lớn dồn về nửa sau năm → CHF có xác suất mạnh trong tháng 8 hơn baseline · Signal: vào 1/8, bias short USDCHF toàn tháng, size nửa · Trade: short với stop 2×ATR, cover 1/9 · Risk: sample size nhỏ (n≈20 tháng) — coi là tilt gate chứ không standalone · Data: OHLC D 20+ năm · Coupling: chỉ kích hoạt khi VIX đã >18 đầu tháng.

**S47 — Year-end CHF funding squeeze (Seasonality)** — Hypothesis: cuối năm ngân hàng châu Âu khoá lợi nhuận, kéo CHF funding; CHF đắt lên spike 1–2 tuần quanh 20/12–5/1 (có sử sách: EONIA-CHF basis nở cuối năm) · Signal: vào 15/12 short USDCHF (mua CHF), cover 5/1; tăng size nếu cross-currency basis đang nở · Trade: stop 1.5×ATR(D), không dùng đòn lớn vì spike hai chiều trong mỏng · Risk: Fed hawkish December đá ngược — check FOMC Dec trước · Data: OHLC D + XCCY basis nếu có · Coupling: khớp cửa sổ S40 (de-risk SNB Dec).

**S48 — Holiday-illiquidity range harvester (Session)** — Hypothesis: 20/12–5/1 và tuần lễ Lễ/Tết (boxing day…), USDCHF chuyển hẳn sang micro-range — chiến lược range-scalp nhỏ làm việc, còn mọi trend/breakout không · Signal: date-window + BBW(D) < p25 · Trade: fade band Bollinger H4 trong window, size 30%, flat trước mỗi ngày lễ nửa · Risk: flash-move phiên mỏng (1/2019) — hard stop luôn có · Data: OHLC H4 + holiday calendar · Coupling: inverse schedule của các hệ breakout (tắt trong window này).

**S49 — Monday-continuation / Friday-reversal (Seasonality)** — Hypothesis: xu hướng tuần được xác nhận Monday thường chạy tiếp (position build đầu tuần); Friday hay bị square-off đảo nhẹ (position flatten cuối tuần) — hai quy tắc một hệ · Signal: Monday close cùng chiều trend tuần trước + không break P Friday → giữ hướng; chiều周五 ngược trend + range nhỏ → fade nhẹ đầu tuần sau · Trade: long/short theo quy tắc, stop 1.5×ATR · Risk: mid-week news đổi regime · Data: OHLC D · Coupling: dùng làm meta-gate cho S30.

**S50 — Quarterly futures roll / options expiry distortion (Seasonality)** — Hypothesis: ngày roll futures FX (thứ Tư trước thứ Sáu thứ 3 của tháng 3/6/9/12) và expiry options lớn tạo flow tạm thời làm giá lệch equilibrium vài giờ → mean-revert sau đó · Signal: trong 2 giờ quanh roll/expiry, giá dịch >0.5×ATR(H1) không có tin · Trade: fade về mức trước distortion sau khi flow kết thúc, scalp 10–20 pips · Risk: distortion đúng lúc trend thật — gate ADX<25 · Data: tick + lịch expiry · Coupling: none.

### Family F — Event / Data-driven (SNB) (S51–S60)

**S51 — SNB-decision drift (Event)** — Hypothesis: sau SNB surprise (không phải hold đúng consensus), giá tiếp tục drift theo chiều surprise 3–5 ngày do vị thế thị trường điều chỉnh chậm · Signal: move phút đầu sau release >0.5×ATR(D) so với consensus-hold · Trade: enter cuối phiên ngày event theo chiều surprise, trailing 1.5×ATR · Risk: surprise bị SNB "thu hồi" bằng phát ngôn hôm sau — theo dõi interviews · Data: SNB calendar + consensus + tick quanh release · Coupling: chiều surprise khớp chiều sight-deposit trend trước đó thì mạnh hơn.

**S52 — SNB statement-language score (Event)** — Hypothesis: thay đổi từ vựng trong Monetary Policy Assessment ("inflationary risks" vs "downside risks", nhắc đến "foreign exchange market"/"CHF valuation") dẫn đường policy 1 quý tới; score hoá ngôn ngữ → trade tuần sau · Signal: NLP score delta so quý trước >ngưỡng · Trade: vị thế 1–15 ngày theo sign score (hawkish score → short USDCHF qua kênh CHF mạnh) · Risk: ngôn ngữ trung tính — beta thấp · Data: archive statement SNB 10 năm + tool NLP · Coupling: kết hợp KOF/CPI cùng chiều tăng conviction.

**S53 — Swiss-CPI surprise fade (Event)** — Hypothesis: Swiss CPI thấp bất ngờ → SNB dovish kỳ vọng → CHF yếu (USDCHF lên) và ngược lại; hiệu ứng lớn hơn bình thường vì SNB đang ở 0% (mọi dữ liệu định hướng can thiệp) · Signal: CPI FSO surprise >±0.2pp vs consensus · Trade: vào 5 phút sau release theo chiều (low CPI → long USDCHF), target 1×ATR, stop 0.5×ATR · Risk: CPI Mỹ cùng tuần nuốt tín hiệu — ưu tiên tuần release CH riêng · Data: calendar CH + tick · Coupling: dùng chung mô hình surprise với S56 (chia sẻ code).

**S54 — KOF-barometer macro tilt (Event)** — Hypothesis: KOF leading index trên trend & tăng 2 tháng liên tiếp → kinh tế Thụy Sĩ khá → SNB ít reason yếu CHF → tilt short USDCHF trung hạn (CHF mạnh) · Signal: KOF > SMA12 của nó và Δ2m >0 · Trade: vị thế swing 1 tháng, rebalance theo KOF monthly, stop 3×ATR(W) · Risk: KOF good mà SNB vẫn can thiệp — gate sight deposits · Data: KOF series + OHLC D · Coupling: gold/VIX haven-confirm cùng lúc thì tăng size.

**S55 — NFP straddle with revision filter (Event)** — Hypothesis: NFP surprise lớn move USDCHF tức thì; nhưng chỉ các NFP có revision đồng hướng mới tạo trend tuần được (quality surprise) — straddle vào, giữ theo filter · Signal: |surprise| >1σ 5-năm + revisions cùng dấu surprise · Trade: stop-order 2 phía 1 phút trước release; chiều thắng giữ nếu revision-filter đạt, thoát cả 2 nếu không · Risk: whipsaw cả hai bên (đã có filter giảm) · Data: tick + payroll history với revisions · Coupling: đồng bộ với lane EURUSD (cùng event, hướng USD chung).

**S56 — US-CPI momentum ignition (Event)** — Hypothesis: CPI Mỹ là driver số 1 của Fed path trong 2026 (Fed vừa tái hike vì inflation); surprise CPI >1σ tạo continuation 2–3 ngày trên USDCHF · Signal: surprise >1σ + close ngày D1 cùng chiều >0.6×ATR · Trade: enter D2 cùng chiều, stop low/high D1, target 3×ATR · Risk: CPI in-line → không trade (không phải loss) · Data: calendar + tick + OHLC · Coupling: nếu surprise hawkish + gold cũng lên (stagflation mix) → size nửa vì haven-flow đối nghịch.

**S57 — FOMC dot-plot delta trade (Event)** — Hypothesis: thay đổi median dots là tín hiệu chính sách mạnh nhất; dot delta +25bp Hawkish → long USDCHF kỳ 1–4 tuần, trừ khi haven-flow lấn át · Signal: dots median tăng so kỳ trước, hoặc statement đổi "accommodative"→"restrictive" style · Trade: enter cuối ngày FOMC theo delta, stop 2×ATR, thoát trước FOMC kế · Risk: buy-rumor-sell-fact đã price-in (check kỳ vọng trước) · Data: dots archive + OHLC · Coupling: S6 là phiên bản 3-ngày đầu của cùng hiện tượng — chọn một làm primary.

**S58 — Sight-deposit footprint trade (Event/Positioning)** — Hypothesis: WoW sight deposits tăng ≥CHF 5 tỷ (ngoài quý cuối tháng — biến động cơ học) phát hiện SNB đang mua ngoại tệ → CHF supply → USDCHF drift lên những ngày/tuần sau · Signal: Δ deposits tuần ≥+5 tỷ CHF, xác nhận 2 tuần liên tiếp tăng · Trade: long USDCHF tuần kế, stop 1.5×ATR(D), thoát khi deposits đi ngang 2 tuần · Risk: SNB dừng đột ngột / Fed-leg đổi chiều · Data: SNB sight deposits weekly (thứ Hai) + OHLC · Coupling: kết hợp S18 (cap-fade) tạo khối SNB-regime hoàn chỉnh.

**S59 — SNB-speech posture scanner (Event)** — Hypothesis: chủ tịch SNB (Schlegel — *(cần kiểm chứng tên/chức danh hiện tại)*) nói về "CHF strength"/"valuation" theo chu kỳ trước hành động; index hoá tần suất từ khoé → early-warning can thiệp · Signal: ≥2 bài phát biểu trong 30 ngày nhắc CHF valuation tiêu cực · Trade: chuẩn bị short-CHF bias (long USDCHF) vào dip, đợi footprint S58 xác nhận mới full size · Risk: nói mà không làm (posturing) — chỉ là bias không phải entry đơn lẻ · Data: archive speeches/interviews + keyword scan · Coupling: S58 là xác nhận bắt buộc.

**S60 — ECB-diversion event via CHF (Event)** — Hypothesis: ECB hike (như đợt 9/2026 — *(cần kiểm chứng chi tiết)*) làm EURCHF lên mạnh; USDCHF bị kéo theo bất hợp lý vì thị trường lẫn CHF với EUR — cú kéo đó sau đó mất một phần (EUR-strength không phải CHF-weakness) · Signal: ECB event ngày D0: EURCHF +>0.5% mà EURUSD flat/to lên nhẹ · Trade: short USDCHF 1–5 ngày sau (mean-revert phần kéo nhầm), hedge EURUSD 50% để tách EUR-leg · Risk: ECB move thật sự thay đổi capital flow dài hạn sang EUR-block · Data: tick 3 cặp + ECB calendar · Coupling: dùng cùng khối phân tích với S28.

### Family G — Cross-asset / Correlation (S61–S70)

**S61 — EURUSD non-confirmation divergence (Cross-asset)** — Hypothesis: EURUSD break xuống thấp mới mà USDCHF không break lên cao mới = CHF-specific weakness đang bot đi (hoặc USD weakness ẩn) → trade về phía CHF mạnh (short USDCHF) · Signal: divergence 20 phiên dùng swing high/low · Trade: enter khi USDCHF mất swing support H4, stop trên swing high, target 1.5×AR · Risk: divergence kéo dài hàng tuần trong regime SNB-nén · Data: OHLC D/H4 2 symbol · Coupling: gold cùng đi lên xác nhận (CHF&gold đồng haven).

**S62 — Gold-CHF confirmation filter (Cross-asset)** — Hypothesis: haven-flow thật sự hai chân (gold+CHF) bền hơn một chân; vào short USDCHF chỉ khi XAUUSD cùng tăng 20-ngày rolling corr dương · Signal: corr(XAUUSD, CHF-strength proxy) 20d >0.3 + XAUUSD uptrend D · Trade: long-CHF (short USDCHF) theo trend gold, stop 2×ATR · Risk: gold đi vì USD-weakness thuần (check DXY cùng lúc) · Data: XAUUSD + USDCHF + DXY · Coupling: là filter dùng lại cho S63/S66.

**S63 — VIX-regime switcher (Cross-asset)** — Hypothesis: hai quy tắc theo VIX: <15 → dollar-carry bias (long USDCHF); >25 → haven bias (short USDCHF); giữa hai là no-trade — hệ regime thuần từ một biến exogenous · Signal: VIX ngưỡng 15/25, đổi chế độ khi qua ngưỡng 2 phiên liên tiếp · Trade: bias position vol-target, flip theo regime · Risk: VIX lag trong stress bank kiểu Credit Suisse (CHF bid trước VIX) · Data: VIX + OHLC · Coupling: khớp với S92 (term structure version tinh hơn).

**S64 — Bund-yield haven channel (Cross-asset)** — Hypothesis: Bund 10y xuống nhanh + gold lên = European risk-off → CHF bid (khác Mỹ-risk-off); USDCHF short signal mạnh khi cặp điều kiện này khớp · Signal: Δ Bund 10y 5 ngày <−15bp + XAUUSD >SMA20 · Trade: short USDCHF, stop 1.5×ATR, exit khi Bund flatten/stabilize · Risk: SNB can thiệp chống CHF mạnh (gate sight deposits) · Data: Bund yields + gold + OHLC · Coupling: S61 tăng conviction khi cùng kích hoạt.

**S65 — Oil-spike haven bid (Cross-asset)** — Hypothesis: Brent tăng >12%/20 phiên (supply shock) → lạm phát/chân chính trị rủi ro châu Âu → CHF như haven của châu Âu được mua (sử sách: các cú oil-shock 70s/90s/2022 đều CHF mạnh) · Signal: return BRENT 20d >+12% · Trade: short USDCHF khi điều kiện bật, giữ khi điều kiện giữ, stop 2×ATR · Risk: oil lên vì demand-boom (risk-on!) — check đồng thời equities đang lên thì bỏ · Data: BRENT + SPX + OHLC · Coupling: equities phải flat/down mới xác nhận haven-kênh.

**S66 — Equity-led risk-off momentum (Cross-asset)** — Hypothesis: ngày SPX −1.5% trở lên, phiên sau USDCHF tiếp tục nghiêng xuống (haven momentum có continuation 1–3 ngày, không chỉ spike) · Signal: SPX daily <−1.5% + VIX up; vào short USDCHF open phiên sau nếu close SPX dưới VWAP ngày đó · Trade: short 1–3 phiên, stop 1.2×ATR · Risk: bounce-equity mạnh (V-shape) cắt stop · Data: SPX + VIX + OHLC · Coupling: S63 cùng chế độ; không chồng 2 vị thế trùng hướng (chọn 1).

**S67 — Gold-vs-real-yields USD-debasement (Cross-asset)** — Hypothesis: khi gold lên dù TIPS real yields cũng lên (phá vỡ tương quan âm lịch sử) → thị trường pricing debasement/geopolitics USD → short USDCHF là cách表达的 "anti-USD với haven kèm theo" · Signal: 60d corr(XAUUSD, 10y TIPS) >0 và XAUUSD uptrend · Trade: short USDCHF theo trend gold, stop 2×ATR · Risk: quan hệ trở lại bình thường → edge tắt · Data: TIPS/XAUUSD/OHLC · Coupling: cùng hướng S62 (điều kiện mạnh hơn).

**S68 — CHFJPY-haven confirm basket (Cross-asset)** — Hypothesis: CHFJPY break down (cả hai haven nhưng CHF thắng JPY) xác nhận risk-off toàn cầu sâu; USDCHF short + USDJPY short như cặp đôi cùng hướng haven → dùng CHFJPY làm leading confirm · Signal: CHFJPY break 20d low + VIX>20 · Trade: đồng thời short USDCHF và short USDJPY (50/50), stop riêng từng leg · Risk: BoJ can thiệp JPY-leg (sự kiện riêng của Nhật) — stop cứng leg đó · Data: CHFJPY/USDJPY/USDCHF + VIX · Coupling: nhìn chung dùng cho mọi family hướng risk-off (gate tăng xác suất).

**S69 — DXY-residual pure-CHF trade (Cross-asset)** — Hypothesis: tách β·DXY khỏi USDCHF (hồi quy rolling 60d), phần residual ε là pure-CHF factor — trade ε mean-revert/trend riêng, tránh đoán USD · Signal: ε z-score ±2 (MR) hoặc ε trend 20d (trend mode) · Trade: vị thế USDCHF hedged bằng basket USD theo β (EURUSD+USDJPY+GBPUSD đối trọng) · Risk: β ước lượng cũ sai sau regime-shift — re-est 60d bắt buộc · Data: DXY hoặc basket + OHLC · Coupling: nền tảng cho mọi ý muốn "đánh CHF mà không đánh USD".

**S70 — Commodity-FX risk proxy confirm (Cross-asset)** — Hypothesis: AUDUSD+NZDUSD đi xuống cùng lúc (commodity/risk-on block yếu) → xác nhận global risk-off; short USDCHF khi đó có xác suất thắng cao hơn đáng kể so với stand-alone · Signal: AUDUSD và NZDUSD cùng dưới SMA20 D + SMA20-down · Trade: short USDCHF theo điều kiện, exit khi một trong hai hồi SMA20 · Risk: commodity-selloff không lan sang broader risk (idiosyncratic Trung Quốc demand) · Data: 3 symbol OHLC · Coupling: dùng làm gate cho S63/S66 giảm false positive.

### Family H — Positioning / Flows (S71–S80)

**S71 — COT non-commercial extreme fade (Positioning)** — Hypothesis: khi specs (CFTC) đạt cực端 net-long CHF (2y percentile >90), phần còn lại của thị trường không còn ammo mua CHF → fade (long USDCHF) · Signal: COT CHF net-long percentile >90 (hoặc <10 cho chiều kia) · Trade: enter tuần sau theo chiều ngược cực端, stop 2×ATR(D), hold tới khi percentile về giữa · Risk: cực端 còn cực端 hơn trong trend haven mạnh · Data: CFTC COT weekly (CHF futures) + OHLC · Coupling: sight deposits tăng (SNB cùng bán CHF) thì conviction tăng.

**S72 — COT flip momentum confirm (Positioning)** — Hypothesis: specs flip từ net-long sang net-short CHF lần đầu sau 6 tháng net-long đánh dấu regime change thực dụng; theo flip có continuation · Signal: chuyển dấu COT net position sau ≥26 tuần cùng dấu · Trade: theo chiều mới 4–8 tuần, stop 2×ATR · Risk: flip ngược do noise 1 tuần — yêu cầu 2 tuần liên tiếp confirm · Data: COT weekly · Coupling: khớp Δ swap differential cùng chiều (S34) tăng chất lượng.

**S73 — COT-vs-price divergence squeeze (Positioning)** — Hypothesis: specs record-long CHF nhưng USDCHF không lập lows mới = thiếu người mua mới + trapping → short squeeze likely (long USDCHF) · Signal: COT percentile >90 + giá không break 20d low trong 3 tuần · Trade: long USDCHF, stop dưới 20d low, target 1×ATR mỗi 2 tuần · Risk:haven-event mới nổ → invalidate · Data: COT + OHLC · Coupling: VIX bình thường mới chạy squeeze logic.

**S74 — SNB FX-reserves trend harvest (Positioning)** — Hypothesis: FX positions của SNB (monthly, FRED/IMF) tăng dần liên tục = chính sách yếu CHF persistent → drift up USDCHF tương lai 1–3 tháng; nghịch đảo 2022–23 (SNB bán để chống lạm phát) đã tương ứng CHF mạnh · Signal: Δ FX positions 3 tháng liền >0 (hoặc <0) · Trade: bias position theo dấu, vol-target, flip theo dấu mới · Risk: báo cáo monthly trễ +noise valuation của chính reserves (USD move đổi giá trị USD-denominated reserves) — cần điều chỉnh FX-effect trước khi đọc · Data: FRED SNB FX positions + OHLC · Coupling: cùng hướng với S58 nhưng tần số thấp hơn, dùng cross-check.

**S75 — Current-account structural gate (Positioning)** — Hypothesis: current account surplus Thụy Sĩ (dòng lợi nhuận/đầu tư về) là luồng mua CHF cấu trúc quý-cụ thể quanh ngày quý điểm (dividend season Q1/Q3) → tilt short USDCHF quanh các đợt repatriation; ngoài ra dùng như long-run bias chống long-USDCHF quá đà · Signal: calendar repatriation (quý điểm báo cáo) + historically CHF-biased windows · Trade: bias nhẹ (size 30%), không standalone · Risk: quá structural, edge nhỏ từng giao dịch — chỉ đáng làm gate · Data: SNB BOP quarterly · Coupling: dùng tăng conviction cho S46/S47.

**S76 — Cross-border M&A flow sniper (Positioning)** — Hypothesis: M&A lớn công ty Thụy Sĩ mua nước ngoài (trả ngoại tệ, về CHF… chiều ngược: công ty nước ngoài mua target Thụy Sĩ bằng CHF cần mua CHF) → CHF demand spike quanh closing deal lớn; các deal >$5bn di chuyển EURCHF/USDCHF measurable · Signal: deal announcement với expected closing window · Trade: position trước closing window theo hướng flow, thoát sau closing · Risk: deal hủy/hoãn; flow đã hedge trước bằng FX derivatives từ lâu · Data: deal feed (Bloomberg/Reuters announcements) + lịch closing · Coupling: cần kiểm chứng tần suất — ý tưởng knowledge-based, chưa thấy edge định lượng.

**S77 — Swiss-vs-Bund spread haven gauge (Positioning)** — Hypothesis: spread 10y Swiss conf − Bund nở (CHF bonds chạy tốt hơn) = inflow haven vào Thụy Sĩ đang mạnh → short USDCHF bias; spread là thước đo giá cả của haven demand chính xác hơn price FX đơn thuần · Signal: Δ spread 20 ngày >+10bp (CHF outperform) · Trade: short USDCHF theo điều kiện, stop 1.5×ATR · Risk: spread do fiscal-supply Bund (issuance) không phải haven demand · Data: hai đường yield 10y + OHLC · Coupling: S64 dùng Bund đơn — spread version sạch hơn về mặt danh nghĩa.

**S78 — SMI-relative domestic confidence (Positioning)** — Hypothesis: SMI (Swiss equity) under/over-perform Stoxx phản chiếu niềm tin nội khối và dòng vào CHF assets; SMI/Stoxx ratio lên + CHF thường mạnh (dòng water vào cả bonds lẫn equity CH) · Signal: ratio SMI/Stoxx 20d slope dương >1σ · Trade: tilt short USDCHF 2–4 tuần, rebalance weekly · Risk: SMI là ngân hàng/bigtail hẹp — proxy thô, dùng chỉ làm gate · Data: SMI + Stoxx + OHLC · Coupling: thêm cho cụm haven-confirm (S62/S64).

**S79 — Carry-unwind CHF-bid episode harvester (Positioning)** — Hypothesis: khi carry-basket chuẩn (AUDJPY/NZDJPY/AUDCHF) sập >3%/5 phiên → global unwind đang chạy → CHF như funding leg được mua lại mạnh; vào CHF ngay trong episode có continuation 3–10 phiên · Signal: carry basket index 5-session return <−3% · Trade: long CHF (short USDCHF) day+1, trailing 2×ATR, exit khi basket stabilizes 2 phiên · Risk: episode ngắn (2 phiên) bounce ngay · Data: AUDJPY/NZDJPY + USDCHF · Coupling: chính là "phần đời còn lại" của S31 — hai ý chia nhau chu kỳ carry; chạy bên nào tùy regime VIX (S63).

**S80 — Retail-sentiment contrarian (Positioning)** — Hypothesis: crowd retail luôn nghiêng ngược carry/with-trend ở extremes; >70% retail long USDCHF (Myfxbook/OANDA positioning) thường ghi nhận vùng top · Signal: sentiment broker aggregate >70% một phía · Trade: fade về phía còn lại khi price-action confirm (lost swing) · Risk: sentiment extremes kéo dài trong trend cuối — bắt buộc confirm giá · Data: retail positioning feed + OHLC · Coupling: đối trọng crowd với COT (S71) — nếu COT+retail cùng extreme ngược nhau thì rất mạnh.

### Family I — Pattern / Pairs / Stat-arb (S81–S90)

**S81 — Triangular-consistency residual fade (Stat-arb)** — Hypothesis: USDCHF × EURUSD phải ≈ EURCHF; sai lệch tạm thời (residual sau cost) do liquidity mismatch revert trong phút — phiên bản tần số cao của S14 · Signal: log-residual vượt ±3σ của phân phối tick-to-tick 60 phút, sau khi trừ spread cả hai leg · Trade: đồng thời 3 chân (EURUSD, USDCHF, EURCHF) về khớp tam giác, hold giây–phút · Risk: latency/execution ăn hết edge ở retail tier — mô hình chỉ để đo lường, production cần VPS/colocated; và residual có thể là lead-information thật · Data: tick đồng bộ 3 symbol (Dukascopy/LMAX) · Coupling: measure độ lớn residual theo session — edge concentrate ở London.

**S82 — EURCHF floor-memory trade (Pattern/Pairs)** — Hypothesis: quanh vùng thấp EURCHF lịch sử (0.90–0.93 tùy giai đoạn), thị trường pricing sẵn SNB-put (floor memory từ 1.20-era); khi EURCHF tiến vào vùng + sight deposits tăng → mua EURCHF (equivalent short USDCHF 60% / short EURUSD 40% tuỳ beta) có xác suất thắng cao với stop rõ · Signal: EURCHF <vùng 3 tháng low + sight deposits WoW >+3 tỷ · Trade: long EURCHF, stop 1×ATR(D) dưới low, target 2×AR ngược · Risk: SNB thực sự không phản ứng lần này (floor memory là ảo) · Data: EURCHF + sight deposits + OHLC · Coupling: S58/S18 cùng khối logic SNB-footprint.

**S83 — CHFJPY haven-swap spread (Stat-arb)** — Hypothesis: CHFJPY là tỷ số hai haven; long-run nó neo về differential kỳ vọng lãi suất & risk; deviation lớn 6 tháng revert — và breakdown của nó là signal risk-off cho cả family khác · Signal: z-score CHFJPY vs dự báo từ rates-differential vượt ±2 (mean-rev mode); hoặc break 20d low (signal mode cho S68) · Trade: MR: trade về z=0 1–3 tháng; Signal: dùng kích hoạt S68 · Risk: hai CB thay đổi chính sách đồng thời làm relationship mới — re-est sau mỗi BoJ/SNB pivot · Data: CHFJPY + swap curves 2 nước + OHLC · Coupling: hai mode không chạy chồng — chọn theo vol regime.

**S84 — Correlation-regime-break monitor (Stat-arb)** — Hypothesis: corr(USDCHF, EURUSD đảo dấu) 60d là nhịp tim của pair; khi corr rời khỏi vùng âm sâu (ví dụ >−0.3), một trong hai cặp đang có idiosyncratic driver (CHF-event hoặc EUR-event) — chế độ này breakout/MR truyền thống chết, phải chuyển expression · Signal: rolling corr >−0.3 5 phiên · Trade: không trade trực tiếp: system-switch signal — tắt S1/S11, bật S82/S61-type · Risk: corr ước lượng trễ — kết hợp event-calendar để không vào muộn · Data: 2 symbol OHLC · Coupling: meta-gate cho cả Section 2, ứng cử auto-regime-switch.

**S85 — Beta-hedged USDCHF residual (Stat-arb)** — Hypothesis: phiên bản clean của S69 ở tần số D: USDCHF = β(DXY)·DXY + ε với β rolling 60d; ε có tính MR mạnh (CHF idiosyncratic được SNB/thị trường pull về) — trade ε z-score ±2.5 · Signal: z(ε) vượt ngưỡng · Trade: long/short USDCHF + hedge β bằng DXY-proxy basket, target z=0.3, stop z=3.5 · Risk: intervention mới tạo ε regime mới — gate sight deposits · Data: DXY + OHLC + deposits · Coupling: cùng gia đình với S69 (một cái là phiên bản hedge bằng basket, một là biểu diễn không hedge).

**S86 — EURUSD→USDCHF lead-lag micro (Stat-arb)** — Hypothesis: trong NY session, EURUSD (thanh khoản sâu nhất) phản ứng tin/chunk-order trước USDCHF vài trăm ms–vài giây; đo được cross-correlation lag dương → dự báo ngắn hạn USDCHF bằng EURUSD return gần nhất · Signal: cross-corr M1 lag 1–3 phút > ngưỡng trong khung NY · Trade: vào USDCHF theo sign EURUSD trigger với filter magnitude >2 pips, scalp 3–8 phút · Risk: latency + spread phá edge ở tier retail; hiệu ứng có thể là trade-through artifact — phải đo net-of-cost kỹ · Data: tick đồng bộ 2 symbol *(cần kiểm chứng tồn tại sau cost)* · Coupling: S81 đo cùng cơ chế từ phía khác (tam giác).

**S87 — Inside-bar + pin-bar confluence (Pattern)** — Hypothesis: price-pattern cổ điển hoạt động tốt nhất trên pair có cấu trúc session rõ (nén trong Asian/London rồi nổ); inside-day kèm pin-bar tại daily S/R là setup xác suất có cộng hưởng community → self-fulfilling · Signal: inside-bar D + pin-bar ở level S/R lịch sử (round number,前期 swing) · Trade: stop-order ngoài nose pin, stop quá nose, target 2R · Risk: pattern mộc mạc quá — chỉ đáng dùng với regime gate (range regime) · Data: OHLC D + levels · Coupling: dùng trong regime-1 của S91.

**S88 — Harmonic completion at intervention leg (Pattern)** — Hypothesis: sau cú can thiệp/shock tạo impulsive leg, giá thường retrace về 0.618–0.786 của leg trước khi tiếp tục (cấu trúc Gartley/Bat xuất hiện nhiều trong data can thiệp) — phiên bản có cấu trúc của pullback-join · Signal: harmonic pattern hoàn tất tại 0.786 của intervention leg + rejection candle H4 · Trade: enter tại PRZ, stop ngoài X-point, target 0.382 ngược rồi trailing · Risk: pattern hoàn tất rồi break luôn (đè PRZ) — kill-switch khi quá PRZ 0.5×ATR · Data: OHLC H4/D + event labels · Coupling: hợp với S9 (cùng hiện tượng post-shock, hai biểu diễn).

**S89 — Round-number rejection scalps (Pattern)** — Hypothesis: 0.8000/0.8500 và các mốc 0.xx50 là magnet + barrier tự nhiên; giá bị đẩy khi chạm trong trạng thái không-driver — scalp rejection 10–20 pips quanh đó có edge nhỏ nhưng lặp lại nhiều · Signal: chạm mốc trong session London với tốc độ giảm (momentum dying: 3 nến M5 nhỏ dần) · Trade: vào ngược tại mốc ±3 pips, stop 10 pips qua mốc, target 15 pips · Risk: breakout thật qua mốc (không có driver check) · Data: M5 + round levels · Coupling: hợp S25 (failed-break) — một cái pre-break, một cái post-break.

**S90 — Instrument-switching vol-ratio (Pattern/Pairs)** — Hypothesis: khi vol-trẻ CHF (USDCHF vs EURUSD vol ratio) bất thường cao → CHF đang có idiosyncratic event → biểu diễn clean nhất là EURCHF (bỏ USD-leg); hệ thống nên switch instrument thay vì cố trade USDCHF với model sai chế độ · Signal: ratio ATR(USDCHF)/ATR(EURUSD) >1.5 (20d) — bình thường <1.2 · Trade: mọi tín hiệu directional USD-leg được routing sang EURCHF trong window đó; trở lại khi ratio <1.2 · Risk: switching rules tạo look-ahead nếu tính ratio bao gồm ngày hiện tại — dùng lag chuẩn · Data: 2 symbol OHLC · Coupling: meta-rule cho toàn hệ (kết hợp S84).

### Family J — Regime-conditioned / Options-flavored (S91–S100)

**S91 — Two-state HMM regime switcher (Regime)** — Hypothesis: USDCHF có 2 trạng thái đo được (range-SNB-nén vs trend-macro); HMM trên returns+vol chia đúng thì MR thắng state-1, trend thắng state-2 — tổng hòa hai hệ đơn lẻ không đủ tốt · Signal: HMM(2) fit rolling 3 năm, state xác suất hậu nghiệm >0.7 mới active · Trade: state-1 → S11/S19; state-2 → S1/S4; giữa state rõ ràng thì flat · Risk: transition bị nhận muộn sau event — thêm event-kill · Data: OHLC D 15 năm · Coupling: bộ khung tổng cho toàn Section 2 (nhiều ý trên đã reference).

**S92 — VIX term-structure toggle (Regime)** — Hypothesis: cấu trúc term VIX (contango/backwardation) phân loại risk-regime chính xác hơn mức VIX đơn thuần — inverted là signal carry-unwind sớm nhất; CHF responsive mạnh tín hiệu này · Signal: M1/M3 VIX futures ratio >1.0 (inversion) 2 phiên · Trade: mọi exposure dài CHF-weak (long USDCHF) bị cut; bias sang CHF-strong cho tới khi contango trở lại 5 phiên · Risk: whipsaw quanh ngưỡng — dùng vùng đệm 0.98–1.02 · Data: VIX futures curve daily · Coupling: tinh hóa S63; dùng làm master gate cho S31/S33/S37.

**S93 — Pre-SNB option straddle buying (Options)** — Hypothesis: event-risk pricing dưới realized trung bình các kỳ SNB-hold-dài (complacency hiện tại: SNB đã hold cả 2026) → mua 1W straddle trước họp có kỳ vọng dương; đặc biệt quý 12 và quý có kỳ vọng can thiệp · Signal: 1W implied < 75% của median |event-week move| 3 năm · Trade: mua straddle ATM 2 ngày trước, thoát ngay sau event (không đợi theta ăn) · Risk: theta loss khi SNB non-event lần nữa — size theo edge định giá được · Data: option chain lịch sử hoặc implied proxy *(cần kiểm chứng nguồn data options CHF khả dụng)* · Coupling: đối trọng của S27 (một dùng stop-orders, một dùng options — chọn theo cost).

**S94 — Covered-short-put overwrite trong carry regime (Options)** — Hypothesis: bán 25Δ put USDCHF strike dưới spot 2×ATR trong regime carry-dương thu premium + nhận assignment ở mức tốt nếu рынок dips — yield enhancement trên S31 · Signal: điều kiện S31 đạt + 1M 25Δ put premium >1.2% annualized excess baseline · Trade: bán put 1M strike ≈ spot−2×ATR, roll monthly, stop-mental tại strike−1×ATR đónggröße nửa · Risk: cú gap-risk (SNB/geo) xuyên qua — không dùng khi có event trong tháng · Data: option chain + OHLC · Coupling: bắt buộc gate S92 contango.

**S95 — 25Δ risk-reversal skew fade (Options)** — Hypothesis: khi 25Δ RR lệch cực端 (thị trường trả giá đắt cho quyền một phía — thường CHF-calls trong stress), spot thường không đi hết cái giá đã trả → fade direction qua options hoặc spot có variance-edge · Signal: 25Δ RR z-score 1 năm >±2 · Trade: bán phía đắt (hoặc trade spot ngược hướng skew-extreme), horizon 2–4 tuần · Risk: stress thật sự chạy tiếp — hard stop qua S92 · Data: RR series *(cần kiểm chứng nguồn)* + OHLC · Coupling: kết hợp COT-extreme (S71) cùng cực端 tăng conviction mạnh.

**S96 — Vol-surface kurtosis filter (Options)** — Hypothesis: butterfly/spread kurtosis implied cảnh báo tail trước khi realized nổ; hệ directional chỉ nên full-size khi implied kurtosis bình thường · Signal: 25Δ-fly và (strangle−straddle)/ATM-IV vượt percentile 90 → giảm size mọi hệ 60% · Trade: không trade riêng — risk-overlay cho Section 2 toàn bộ · Risk: implied kurtosis có thể sống mãi ở mức cao mà không nổ (false alarm đắt — chỉ giảm size chứ không đảo) · Data: vol surface *(cần kiểm chứng nguồn)* · Coupling: overlay song song với S92.

**S97 — Basket-dispersion CHF-idio fade (Regime)** — Hypothesis: khi USDCHF vol cao hơn hẳn "phần được giải thích" bởi DXY/EURUSD (idiosyncratic vol spike = CHF-event/lo ngại can thiệp), spot thường bị kéo quá mức tạm thời rồi về mặt bằng basket · Signal: idio-vol ratio (residual vol / total vol) 10d >0.45 · Trade: fade move USDCHF về mức dự báo từ basket, stop 1.2×ATR, horizon 3–7 phiên · Risk: đây chính là cơ chế của 2015 — dispersion có thể là new-regime thật; kill-switch: sight deposits bất thường + SNB calendar trong 5 phiên thì không fade · Data: basket + USDCHF + deposits · Coupling: dùng chung triết lý S17 nhưng đo bằng vol thay vì spike-percentage.

**S98 — Barrier-defense drift magnet (Options)** — Hypothesis: quanh expiry tuần options có barrier lớn (0.8000-style), giá có "magnet" về phía barrier được bảo vệ (option-dealer gamma hedging kéo giá) trong 2–3 phiên trước expiry; sau expiry, magnet biến mất và spring · Signal: giá trong 0.5×ATR của mốc barrier tròn quan trọng + tuần expiry quý · Trade: theo hướng barrier được bảo vệ (đo bằng giá kiên trì một phía), thoát ngay sau expiry; hoặc fade spring post-expiry nếu bị đè · Risk: đoán barrier bị phá (dữ liệu barrier OTC không public — suy từ price action) *(cần kiểm chứng tính khả dụng tin tức barrier)* · Data: OHLC + expiry calendar + market intel · Coupling: chồng với S89 quanh cùng mốc.

**S99 — Correlation-breakdown CHF-call convexity (Options)** — Hypothesis: khi corr(USDCHF, gold) hoặc corr(USDCHF, EURUSD-inverse) sập đột ngột trong stress, đó là dấu hiệu regime-shift chưa price (CHF đang có vai trò mới) — mua options hướng CHF-mạnh (calls CHF) mua convexity thay vì spot · Signal: |Δ corr 20d| >0.4 trong 3 phiên + VIX>20 · Trade: mua USDCHF puts 1M OTM 25Δ, budget 0.5% vốn/trade, chờ regime materialize hoặc lose premium · Risk: premium cháy nếu correlation-heal nhanh — size nhỏ, tần suất thấp · Data: correlations + option chain *(cần kiểm chứng nguồn)* · Coupling: kích hoạt đồng thời tín hiệu S84 (chính là cơ chế đằng sau).

**S100 — Regime-weighted meta-portfolio với intervention kill-switch (Regime)** — Hypothesis: tổng hợp là cách duy nhất sống sót trên pair bimodal: portfolio các ý trên với trọng số theo regime (S91 state + S92 VIX + S58 SNB-footprint + S84 corr-regime), vol-target 8%, và một kill-switch toàn cục: sight deposits WoW >+8 tỷ hoặc SNB-event bất ngờ → flat mọi vị thế CHF-weak trong 24h · Signal: board regime hàng ngày · Trade: meta-allocation, không manual per-idea · Risk: over-engineering — yêu cầu mỗi family chạy được độc lập trước khi ghép; trial accounting nghiêm theo chuẩn workspace · Data: toàn bộ data của các ý thành phần + registry program · Coupling: đây là sản phẩm cuối chương trình brainstorm cho symbol này.

---

## 3. Tổng hợp cho symbol

### 3.1 Top-10 ideas (khuyến nghị ưu tiên kiểm định)

| # | Idea | Vì sao chọn |
|---|---|---|
| 1 | **S58 — Sight-deposit footprint trade** | Signal dữ liệu công khai, hypothesis kinh tế rõ (SNB supply CHF → drift), hiện tượng đang sống (7/2025 +11.2 tỷ), khó overfit vì cơ chế trực tiếp |
| 2 | **S31/S39 (gộp) — Carry + VIX hard-stop** | Differential −375/−400bp là chế độ hiếm có; edge lớn nhất nhưng chỉ sống với kill-switch — cấu trúc S39 là cách test thận trọng nhất |
| 3 | **S61 — EURUSD non-confirmation divergence** | Dựa vào cấu trúc tương quan âm sâu ổn định nhất của pair; tận dụng lợi thế lane EURUSD đã chạy song song |
| 4 | **S84 — Correlation-regime-break monitor** | Meta-gate rẻ (chỉ cần 2 series), bảo vệ mọi hệ khác khỏi chết ở chế độ sai; bằng chứng 2015 cho thấy thiếu nó là chết |
| 5 | **S51 — SNB-decision drift** | Event rõ ràng, tần số 4 lần/năm, asymmetric payoff, backtest được bằng tick quanh release |
| 6 | **S69/S85 — DXY-residual pure-CHF trade** | Cho phép đánh CHF mà không phán đoán USD — tách biến khỏi đám nhiễu Fed-noise đang lớn năm 2026 |
| 7 | **S17 — Haven-spike partial-fade** | Khai thác tail-structure đặc thù CHF; đo được bằng tick+news+VIX; đối trọng rủi ro rõ |
| 8 | **S21 — Asian-range London breakout** | Classic có nền tảng thống kê, chi phí test thấp, chạy tốt trên pair có session structure |
| 9 | **S11 — Bollinger-squeeze fade + SNB-quiet gate** | Đại diện tốt nhất cho pha range chiếm đa số thời gian của pair; gate sight deposits là điểm mới so với textbook |
| 10 | **S91 — Two-state HMM switcher** | Cơ sở hạ tầng regime cho cả danh mục; không phải alpha đơn lẻ nhưng quyết định alpha nào được bật |

### 3.2 Bẫy overfitting đặc thù khi backtest USDCHF

1. **2015 structural break**: mọi data kéo qua 15/01/2015 chứa một regime đã chết (floor
   1.20). hoặc tách sample, hoặc robust-check bỏ 2011–2015. Tương tự cẩn thận khoảng
   negative-rate era 2015–2022 (CHF leg hành xử khác nay).
2. **Intervention asymmetry không sample được**: SNB hành động theo quyết định chính trị,
   không theo phân phối quá khứ — backtest sẽ không có "SNB surprise mới" trong sample.
   Bù bằng kill-switch giả định (S100), không bằng optimization.
3. **Low-vol trap**: pair phẳng dài → metrics trung bình đẹp nhờ vài ngày vol lớn; luôn
   báo cáo phân phối PnL theo vol-quintile, không chỉ Sharpe toàn mẫu.
4. **Swap/carry trong backtest**: bỏ qua swap làm carry-strategy "thần thánh hóa" hoặc
   ngược lại tốn swap giả. Phải gắn lịch policy rate thực của 2 nước 2008–2026.
5. **Session/daylight-saving**: giờ London/Zurich dịch 1h hai lần/năm; mọi rule theo
   giờ fixed bị smear nếu không DST-adjust.
6. **Spread biến động theo event**: backtest spread fixed sẽ quá lạc quan với event
   strategies (S27/S55); cần mô hình spread theo vol/event-window.
7. **COT small-sample**: 2 cực端/năm mỗi chiều — mọi ngưỡng percentile trên COT dễ là
   noise; yêu cầu ≥15 năm và out-of-sample chéo (dùng GBP/JPY COT làm control).
8. **Sight deposits mùa vụ cuối quý**: biến động cơ học cuối quý (window-dressing) giả
   giống intervention — phải loại exclusion window chuẩn (S58 đã ghi).
9. **Correlation ước lượng trễ**: mọi hệ dùng rolling corr (S61/S84/S99) nhạy với
   window-length — chọn window a priori theo lý thuyết (60d trade-flow, 20d risk), không
   grid-search.
10. **Trial accounting**: theo chuẩn workspace — mọi biến thể threshold là 1 trial và
    phải ghi; USDCHF dễ sinh 500 biến thể vì "nhìn affordability" — kỷ luật trial là rào
    chính chống chọn-kết-quả-đẹp.

### 3.3 MUST-WATCH weekly macro checklist (USDCHF desk)

- [ ] **Thứ Hai: SNB sight deposits** (WoW Δ, loại trừ cuối quý) — footprint can thiệp
      (S58/S18/S82); bất thường >+5 tỷ → review mọi vị thế CHF-weak.
- [ ] **Lịch tuần**: SNB/FOMC/ECB/BoJ trong 10 phiên tới?; US CPI/NFP/PCE/ISM ngày nào?;
      tháng 3/6/9/12 → cửa sổ SNB quarterly + futures roll/expiry (S50/S93).
- [ ] **Rates**: 2y swap differential US–CH (mức + slope 20d) — driver drift (S34);
      10y Swiss−Bund spread (S77); cross-currency basis stress (S38).
- [ ] **Risk**: VIX mức + M1/M3 term structure (S63/S92); credit spreads nếu có;
      carry-basket (AUDJPY 5d) cho unwind-watch (S79).
- [ ] **Gold**: XAUUSD trend + corr 20d với CHF (S62/S67) — xác nhận haven-flow thật.
- [ ] **EURCHF**: vị trí so vùng thấp 3 tháng + shadow-driver của tuần (ECB, energy,
      chính trị EU) (S60/S82).
- [ ] **Positioning**: COT thứ Sáu (CHF net + percentile) (S71–S73); retail sentiment
      nếu feed (S80).
- [ ] **Swiss data發 hành tuần đó**: CPI/KOF/PMI (S53/S54); phát ngôn Schlegel/SNB
      board — keyword "valuation/strength" (S59).
- [ ] **SNB FX positions monthly** (FRED) khi phát hành — cross-check trend dài (S74).
- [ ] **Sự kiện địa chính trị đang mở** (chiến tranh, bầu cử EU lớn, stress ngân hàng)
      — trạng thái haven-channel bật/tắt (S17/S64–S68).

---

*Sản phẩm brainstorm — mọi con số cần re-measure. Không con số nào ở đây là kết quả
backtest. (cần kiểm chứng) = chưa verify được tại thời điểm 2026-09-28.*
