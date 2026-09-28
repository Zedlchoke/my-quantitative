# XAUUSD — Deep Dive & 100 Strategy Ideas

- **Chương trình**: FOREX-UNIFIED-STRATEGY-BRAINSTORM-V1 — lane XAUUSD (knowledge-only brainstorm)
- **Ngày**: 2026-09-28 · **Ràng buộc**: no backtest, no Python, no git, no data download
- **Trạng thái dữ liệu vĩ mô**: mục có số liệu đã verify qua WebFetch ngày 2026-09-28 (nguồn: FRED DFII10, Federalreserve.gov, Kitco, TradingEconomics). Mục chưa verify được đánh dấu **(cần kiểm chứng)**.
- **Nguồn verify chính**: FRED (real yield), Federal Reserve press release 16/09/2026, Kitco gold chart (quote 28/09), TradingEconomics Brent/WTI/Silver. WebSearch bị rate-limit xuyên suốt session — các chủ đề phụ phải bỏ cờ "(cần kiểm chứng)".

---

## 1. Bản chất instrument

### 1.1 Microstructure & sessions

XAUUSD (spot gold) giao dịch gần 24/5: mở Chủ nhật ~22:00 UTC cùng Wellington/Asia, đóng Friday ~21:00 UTC. Không có sàn tập trung duy nhất — giá "spot" là composite của ba lớp thị trường:

1. **OTC London (LOCO London)**: sâu nhất về physical, trái tim của leasing/forward (lease rate, GOFO-type funding, EFP), benchmark qua **LBMA auctions (AM 10:30 & PM 15:00 London time)**.
2. **COMEX futures (GC)**: price-discovery leader phần lớn thời gian, mở electronic gần 23h/ngày; margin do CME quản lý (nguồn margin-hike cascade).
3. **Broker CFD**: parse giá từ futures/OTC trừ forward fair-value; quote cho retail; swap/rollover riêng từng broker.

Hệ quả cho quant: "giá vàng" không phải một con số — tùy data source (fix LBMA vs GC vs CFD) mà backtest cho kết quả khác nhau; đây là nguồn sai lệch thầm lặng số một (chi tiết ở 3.2).

**Ba khối phiên chính** (giờ UTC, mùa đông; DST lệch ±1h — bẫy backtest, xem 3.2):

- **Asia (00:00–07:00)**: thanh khoản mỏng nhất; driver là physical demand TQ/Ấn (Shanghai Gold Exchange premium), vol thấp, range hẹp; spread CFD giãn 1.5–3x mức London. Session này chịu can thiệp JPY (2026: vùng USDJPY 152.9–154.5 sau can thiệp phối hợp Nhật–Mỹ Jul–Aug — theo lane FX, chưa verify độc lập) → gián tiếp dời USD và vàng qua DXY.
- **London (07:00–16:00)**: thanh khoản sâu nhất trong ngày; hai **fix 10:30 & 15:00 London** là liquidity event định kỳ (bank benchmark lô physical) — vol thường nhồi quanh fix; 3 tháng đầu năm là mùa demand physical lớn nhất.
- **NY / COMEX (12:30–21:00)**: overlap London–NY (12:30–16:00) là cửa sổ volume + vol cao nhất ngày; **COMEX pit/element open 13:30 UTC** (8:30 ET) trùng nhóm data 8:30 ET (NFP, CPI, retail sales); close 17:00 ET; Globex electronic kéo dài.

**Cheat-sheet phiên nhanh** (cho các ý Family E; giờ UTC mùa đông, chỉnh ±1h khi DST):

| Cửa sổ | UTC | Đặc trưng | Module phù hợp |
|---|---|---|---|
| Asia range build | 00:00–06:00 | mỏng, range anchor hình thành | build signal cho S11/S21/S42 |
| Tokyo fix / JPY risk | ~00:55 | can thiệp JPY nếu có (2026-style) | watch DXY spillover (S66) |
| Frankfurt pre-move | 06:00–07:00 | probing biên Asia | warning cho fade Asia |
| London open + AM fix | 07:00–10:30 | volume + vol đỉnh 1 | breakout/fade fix (S21/S41) |
| Lunch London | 11:30–12:30 | hơi chùng | tránh entry mới |
| Data 8:30 ET / COMEX open | 12:30–13:30 | đỉnh 2, spike data | S22/S27/S50/S51 |
| Overlap afternoon | 13:30–16:30 | sâu nhất, follow-through tốt | mọi ý directional intraday (S49) |
| PM fix + COMEX close | 15:00–17:00 | fix London PM, cân GC | S16 exit / OPEX pin (S46) |
| Late NY | 19:00–21:00 | books-flattening Friday | S44 |
| Rollover/swap window | ~21:00–22:00 | spread CFD giãn | tránh execute (S90) |

**Vol profile intraday (kinh nghiệm chuẩn của symbol)**: hình chữ U — đáy ở Asia, hai đỉnh ở London-fix và NY-open; realized vol NY chiếm ~40–50% tổng ngày. **Volatility clustering rất mạnh** (hiệu ứng GARCH cao hơn hầu hết cặp FX chính): sau ngày ±3% (28/09/2026: gold -3.25%) thì vài phiên sau vol tiếp tục cao — mọi ý sizing phải tôn trọng clustering này.

**Spread & chi phí thực tế**:

- Spread retail CFD tốt: $0.20–0.35/oz (với pip vàng = $0.01, tức 20–35 pips vàng); giãn 4–10x quanh FOMC/CPI/NFP và giờ Asia mỏng.
- Ngày 28/09/2026 Kitco ghi bid/ask OTC 4,144.80/4,146.80 (~$2 spread cho size lớn) — tham chiếu về spread institutional trong ngày vol cao.
- **Rollover/swap CFD**: XAUUSD CFD về bản chất là synthetic futures — long swap thường âm (contango roll + funding + broker markup), short swap thường dương một phần. Multi-day strategy bắt buộc tính swap vào backtest; không tính là ảo tưởng 0-cost.
- **Weekend gaps**: vàng đóng Friday ~21:00 UTC và mở Chủ nhật ~22:00 UTC; trong tuần geo nóng (Hormuz 9/2026) gap Sunday có thể 0.5–1.5% hai chiều. Stop-loss CFD execute ở giá mở, không phải giá stop → **slippage gap là chi phí thật** của mọi ý giữ qua cuối tuần (cấu trúc lại ở S93).

**Thông số hợp đồng/giá tham chiếu nhanh** (để Normalize các ý sau):

| Đại lượng | Giá trị tham khảo |
|---|---|
| Pip/point | $0.01 (1 pip) — "1 dollar move" = 100 pips |
| Lot chuẩn CFD | 100 oz → $1 move = $100 PnL/lot |
| ATR(D) vùng vol thường | ~1.2–2.5% giá (Sep-2026 đang vùng cao: ngày 28/09 range ~$140 ≈ 3.4%) |
| Quote hiện tại (28/09/2026) | $4,144.80/4,146.80; day range 4,140.30–4,279.90 |
| Đỉnh lịch sử | $5,589.38 (28/01/2026) — hiện -26% |
| Mốc kỹ thuật vừa vỡ | $4,300 (support hằng tuần 25/09) |

### 1.2 Điểm ĐẶC BIỆT riêng XAUUSD (không cặp FX nào trong universe có đủ combo)

1. **Tam diện: monetary asset + risk asset + safe-haven — regime-dependent**. Vàng là symbol duy nhất trong universe phản ứng *hai mặt* với risk-on/off: risk-off có thể làm vàng tăng (safe-haven flow) HOẶC giảm (liquidation để cover margin ở tài sản khác). Cùng một headline, hai chiều khả dĩ — phân biệt bằng trạng thái real yields + positioning, không bằng narrative.
2. **Không có cashflow, không có NHTW policy riêng — định giá "màn ảnh" của real rates**: mô hình chuẩn = giá vàng nghịch đảo opportunity cost giữ vàng = **10Y TIPS real yield** (driver trái chiều cốt lõi). Sep-2026: TIPS 10Y = **2.85%** (24/09, +23bp trong tuần — FRED DFII10) — mức restrictive hiếm thấy, lý do trực tiếp vàng mất ~26% từ đỉnh.
3. **Central-bank structural bid (price-insensitive)**: sau khi dự trữ Nga bị đóng băng (2022), các NHTW mua >1,000 tấn/năm ba năm liền (2022: ~1,082t; 2023: ~1,037t; 2024: ~1,045t — baseline kiến thức; **quy mô 2025–2026 cần kiểm chứng** qua WGC Gold Demand Trends/IFS). Người mua này không stop-loss, mua vì mục tiêu reserve diversification → tạo **convex floor** quanh "CB zone" (2026: thị trường đang test vùng ~$4,000–4,100 — ranh giới chính xác cần kiểm chứng bằng dữ liệu mua thực tế).
4. **Dual-channel của geo shock — nghịch lý đang sống ở Sep-2026**: xung đột Mỹ–Iran / eo Hormuz đẩy Brent lên ~$108 (28/09: $108.07, +61% y/y) nhưng vàng **giảm** (-3.25% cùng ngày; -26% từ đỉnh $5,589 28/01/2026). Kênh truyền dẫn: oil shock → CPI lên → Fed hawkish hơn (16/09/2026: hike 3.75–4.00% unanimous 12–0; thị trường định giá ~70% hike tháng 10, ~95% tháng 12) → **real yields lên 2.85% → vàng xuống**. Kênh safe-haven bị kênh rate-hike đè hiên. "Gold is throwing out the old rulebook" (Kitco, 9/2026). Đây là bài học regime lớn nhất cho cả 100 ý dưới đây.
5. **Physical anchoring thật**: khác FX thuần, vàng có chuỗi physical (mine supply ~3,200–3,700t/năm, recycle, SGE premium, ETF custodian, lease market) → spread SGE–LOCO London, lease rate, EFP COMEX–London là các "đồng hồ" structurally informative mà EURUSD không có.
6. **Beta dọc: silver**. XAGUSD ($61.12 ngày 28/09, ATH $121.64 cũng 01/2026, -5% ngày) có corr +0.8–0.9 với vàng nhưng beta ~1.3–1.5 và mix industrial demand → G/S ratio (67.9 hiện tại) là gauge risk-appetite của cả phức kim loại.
7. **Đối tượng của fleet institutional đa tầng**: CTA (trend), macro funds (real-rate trade), official sector (structural), retail-ETF (momentum), dealer hedging (options) — từng nhóm hành xử khác nhau theo session/regime, tạo nhiều "edge cửa sổ" cho strategy time/event-based.

### 1.3 Tin tức / sự kiện ảnh hưởng

**Scheduled (lịch biết trước)**:

| Sự kiện | Nhịp | Kênh truyền dẫn vào XAUUSD |
|---|---|---|
| FOMC decision + SEP/dot plot | 8/năm | Fed path → real yields + DXY; hike = headwind (16/09/2026: +25bp unanimous, "inflation remains elevated", "will deliver price stability" → vàng tiếp tục suy yếu) |
| US CPI (core) | tháng, 8:30 ET | Surprise lên → hike pricing → vàng hạ (kênh rate đè kênh inflation-hedge trong regime hawkish hiện tại) |
| NFP / unemployment | tháng thứ nhất, 8:30 ET | Downturn lao động → pivot hopes → vàng tăng; blowout payroll → hạ |
| GDP / PCE / retail sales | quý/tháng | tương tự CPI, biên độ nhỏ hơn |
| FOMC minutes, Jackson Hole (Aug), Fed speeches | rải | Hawkish/dovish re-pricing qua 2Y/real yields; spike không kèm yields = noise fade-able (S56) |
| Treasury auctions (10Y, 30Y) | tháng | Tail → real yield lên → áp lực vàng (S59) |
| WGC Gold Demand Trends (quý), CB statistics (tháng), IMF IFS | quý/tháng | Con số CB buying vs kỳ vọng → drift; dữ liệu trễ 1–2 tháng và hay revised |
| CFTC COT | tuần, Fri 15:30 ET | Managed Money net-length extremes → crowding logic |
| Options expiry COMEX | cuối tháng | OI pin / gamma quanh strike lớn (S46/S76) |
| LBMA events, quarterly roll GC | quý | Liquidity & curve dynamics |

**Unscheduled (đột ngột) — kèm kênh**:

- **Geopolitical escalation** (đang sống: MoU Mỹ–Iran giữa 6/2026 sụp đổ, chiến sự suốt mùa hè, phong tỏa hải quân cảng Iran + đóng băng tài sản; 25/09 Iran đề nghị mở lại Hormuz trong 7 ngày nếu Mỹ dỡ phong tỏa; 27/09 Trump từ chối — "Tehran overplayed its hand"; 28/09 Brent >$106): bid tức thời 5–60 phút, sau đó **phân ký** — nếu không truyền vào rates thì fade nhanh (S57); nếu đẩy breakeven/hawkish repricing thì có thể *trái chiều* (vàng giảm — chính điều xảy ra 28/09).
- **Banking/financial stress** (kiểu SVB 3/2023): flight-to-safety + kỳ vọng cắt lãi → vàng tăng mạnh và bền vì kênh rates **cùng chiều** safe-haven. Đây là loại stress mà gold-bid bền nhất (điều kiện hoá ở S68/S100).
- **BoJ/MoF intervention** (JPY): dội USD toàn phần → ảnh hưởng gián tiếp qua DXY; can thiệp phối hợp Nhật–Mỹ Jul–Aug/2026 là tiền lệ hiếm (theo lane FX — cần kiểm chứng độc lập).
- **Exchange actions**: CME tăng margin sau vol-spike → forced liquidation tầng (S80); thay đổi margin/sạp cũng đổi curve dynamics.
- **Wholesale funding stress**: lease-rate spike, EFP bung (kiểu 3/2020) — tín hiệu scarcity physical (S33/S36).

### 1.4 Thông số ảnh hưởng (drivers, xếp theo quyền lực — trạng thái Sep-2026 verify được)

1. **10Y TIPS real yield** — quan trọng nhất, trái chiều. Hiện **2.85%** (24/09/2026), +23bp/tuần — lực đè chính. Quy tắc kinh nghiệm (regime-dependent, không ổn định): Δreal +10bp ≈ -0.8 đến -1.5% vàng.
2. **DXY** — trái chiều, hệ số -0.4 đến -0.6 dài hạn. Mức hiện tại **(cần kiểm chứng — fetch DXY thất bại 28/09)**; nhất quán với hawkish Fed + 10Y nominal ~5.2% (headline Kitco) thì DXY chắc chắn ở vùng mạnh nhiều năm.
3. **Fed path pricing** — ~70% hike Oct / ~95% Dec (verify qua TradingEconomics 28/09) → path hawkish = headwind cho tới khi curve reversal.
4. **VIX / risk appetite** — convex: VIX>30 tạo bid NHƯNG chỉ thắng khi real yields đi ngang/hạ (S68, S91).
5. **CB flows** — structural, price-insensitive, chậm nhưng dai; tạo floor thay vì catalyst. Quy mô 2025–26 **(cần kiểm chứng)**.
6. **ETF flows (GLD/IAU)** — Western money theo momentum; xác nhận trend hơn là dẫn dắt; holdings hiện trạng **(cần kiểm chứng)**.
7. **Physical premiums (SGE), lease rates, EFP** — tín hiệu structural/funding.
8. **Oil/inflation complex** — hai chiều theo regime: bình thường +, rate-hawkish − (Sep-2026 là −; xem S64).

### 1.5 Correlation map (12 symbol) + breakdown theo regime

Baseline dài hạn (hợp thức từ kiến thức đến 2025; con số hiện tại phải đo lại trên checkout — nguyên tắc evidence-first):

| Symbol | Corr với XAUUSD (baseline) | Ghi chú |
|---|---|---|
| XAGUSD | **+0.80 → +0.90** | cặp đôi cao nhất; silver beta 1.3–1.5; G/S = risk gauge phức kim loại (hiện 67.9) |
| EURUSD | +0.4 → +0.6 | cả hai short-USD; vàng thêm driver real yield |
| AUDUSD | +0.4 → +0.6 | phức commodity-FX anti-USD; vàng nằm trong terms-of-trade Úc |
| GBPUSD | +0.3 → +0.5 | anti-USD thuần, ít idio trùng vàng |
| NZDUSD | +0.3 → +0.5 | như AUD, yếu hơn |
| USDCHF | −0.3 → −0.5 | CHF & gold đều safe-haven → USDCHF trái chiều vàng |
| USDJPY | ~0 (bất ổn) | risk-off: JPY & gold cùng được mua → âm; regime chênh lệch lãi suất: dương |
| USDCAD | −0.2 → −0.4 | oil-CAD vs gold; trái dấu qua USD |
| BRENT | +0.1 → +0.3 (regime thường) | **Sep-2026: âm** (ngày 28/09: Brent +3.6% vs gold −3.25%) — kênh hike đè kênh inflation |
| WTI | như Brent | corr với Brent ~0.95 |
| NATGAS | ~0 | idiosyncratic thời tiết; chỉ dùng làm noise control trong energy-PCA (S70) |

**Breakdown theo regime** (quan trọng hơn con số baseline — mọi backtest phải stratify):

- **Risk-off thuần (VIX>30, real yields đi ngang/hạ)**: gold↑, USDCHF↓ mạnh (CHF↑) → corr vàng–USDCHF âm sâu; gold–AUD/NZD **đảo thành âm** (AUD bị bán dù anti-USD); gold–USDJPY âm (JPY↑); gold–silver vẫn dương nhưng silver underperform (beta gãy khi industrial demand sợ recession).
- **Rate-shock / hawkish repricing (regime Sep-2026)**: real yields +, DXY + → gold↓ **ngay cả khi risk-off và oil↑**; gold–EURUSD decouple (cả hai giảm vì USD, nhưng vàng giảm nhiều hơn theo real yields); gold–oil **âm**; gold–silver dương rất cao (cùng bị bóp).
- **Debasement / reserve-diversification (2022–2025)**: gold tăng vs **mọi** fiat → corr với EURUSD yếu đi (vàng rally đồng thời EUR yếu); đặc trưng CB buying + de-dollarization; residual của mô hình vàng~macro dịch dương liên tục.
- **Risk-on / disinflation**: vàng đi ngang hoặc giảm nhẹ (opportunity cost tăng), corr với AUD/NZD dương rõ, với XAG cao.

Cách dùng trong research: corr map này là *đầu vào cho gates*, không phải giả định cố định — ý S61/S62/S86/S97 tồn tại chính để đo và khai thác sự bất ổn của các hệ số này.

**Tóm tắt nhanh 4 regime — hành vi vàng và module gợi ý** (chi tiết hoá tại S91):

| Regime | Gold vs USD | Gold vs oil | Gold vs AUD/NZD | Module gợi ý |
|---|---|---|---|---|
| Risk-off thuần (VIX↑, TIPS flat/↓) | tăng vs mọi fiat | + yếu | **âm** (AUD giảm) | safe-haven long + USDCHF confirm (S68) |
| Rate-shock hawkish (Sep-2026) | giảm mạnh | **âm** | âm nhưng ít hơn | vol/short + pair S64 |
| Debasement (2022–25) | tăng vs mọi fiat, corr EURUSD yếu | + | + | structural floor S31/S39 |
| Risk-on disinflation | đi ngang, opp-cost tăng | + | + rõ | MR/session + sell-vol (S95) |

### 1.6 Note trung thực — bối cảnh nào các họ strategy hay CHẾT trên XAUUSD

- **Naive mean-reversion trong trend real-yield**: vàng rơi -26% (01→09/2026) không chóng mặt — MR "đón dao" liên tục bị quét; MR chỉ sống khi có gate real-yield ổn định (S15) hoặc washout-positioning xác nhận (S20).
- **Safe-haven knee-jerk (mua theo headline geo)**: regime hawkish đè bid — headline Hormuz 25–27/09 mà vàng vẫn giảm; đây là cái bẫy đã giết nhiều hệ thống "geo-long" trong Q3/2026. Gate TIPS bắt buộc (S57/S68).
- **Breakout short trong CB floor zone**: người mua price-insensitive (NHTW) làm false-breakdown đảo chiều quanh $4,000–4,100 — short-breakout ở đó có xác suất chết cao bất thường (S96 là mặt đúng của hiện tượng).
- **Stat-arb XAU–XAG với tham số cũ**: G/S đã từ vùng 80–110 co về 67.9 — band calibrate giai đoạn trước liên tục bị prob; silver squeeze riêng (ATH $121.64 01/2026) làm pair nổ bất kể vàng.
- **Holding-cost-blind backtest**: quên swap CFD âm cho long + weekend gap slippage → PnL ảo, đặc biệt với các ý event/swing multi-day.
- **Microstructure data mixing**: giá CFD broker ≠ GC futures ≠ fix LBMA — trộn nguồn trong backtest là lỗi thầm lặng lớn nhất của symbol này (chốt ở 3.2).

---

## 2. 100 strategy ideas

Quy ước chung: mọi ý là hypothesis cần kiểm định, KHÔNG phải kết quả — không ý nào được coi là PASS. Timeframe viết tắt: D = daily, W = weekly, H4/H1/M15/M5 = intraday. ATR = ATR(14) của khung tương ứng. Mỗi ý ghi rõ Coupling = yếu tố ngoài cùng chiều/gate bắt buộc để không thành "một signal đánh mọi regime".

**Bảng tra nhanh: family ↔ regime thuận lợi ↔ điều kiện giết** (chỉ đạo chọn module; chi tiết hoá ở S91):

| Family | Regime thuận lợi | Điều kiện giết chính |
|---|---|---|
| A Trend/Momentum | TIPS-slope ≤ 0, CB mua mạnh | TIPS spike, range $4,000–4,300 |
| B Mean-reversion | ngày rates yên tĩnh, không event | trend real-yield mạnh (2026) |
| C Breakout/Vol | compression → ignition, event-sau | CB floor fade short-break |
| D Carry/Structural | CB pace cao, festival window | CB pause, hawkish đè seasonal |
| E Session/Seasonality | cấu trúc participant ổn định | DST bug, event trùng, macro đè mùa |
| F Event/Data | surprise rõ, kênh rate sạch | bỏ qua điều kiện regime (dấu đổi) |
| G Cross-asset | tương quan band ổn định | corr-flip giữa chừng |
| H Positioning/Flows | extreme + price-confirm | crowding kéo dài, data trễ |
| I Pattern/Stat-arb | band/beta còn hợp lệ | structural shift (G/S, quota) |
| J Regime/Options | cần meta-layer chọn đúng họ | meta-param fit quá khứ, tail ngoài phân phối |

### Family A — Trend / Momentum (S1–S10)

Lý do kinh tế của họ: structural flows (CB, ETF, CTA) tạo autocorrelation dängen multi-month ở vàng; clustering vol làm trend tự nuôi. Cái chết điển hình của họ: regime đảo (TIPS spike kiểu 2026) — nên phần lớn ý có gate real-yield.

**S1 — Donchian-CTA đa kỳ (Trend)** — Hypothesis: vàng có xu hướng decad do structural flows (CB/ETF/CTA) tạo autocorrelation dương multi-month; channel-break giữ được phần lớn các đoạn lớn.
· Signal: giá đóng D vượt/vượt xuống kênh Donchian 20 tuần · Trade: vào theo hướng break, stop = kênh đối diện hoặc 2×ATR_D, pyramiding tối đa 2 lần; time-stop 60 ngày không tiến.
· Risk: whipsaw trong range hiện tại $4,000–4,300; drawdown dài khi regime đảo chưa xác nhận · Data: giá D roll-adjusted, ATR · Coupling: chỉ long khi 10Y TIPS 20d-slope ≤ 0 hoặc CB net buying dương trailing 3 tháng.

**S2 — Real-yield trend gate (Trend)** — Hypothesis: phần lớn drift dương của vàng xảy ra trong các đoạn TIPS-bull (real yield hạ); theo slope lãi suất thực lọc được phần lớn drawdown kiểu 2026.
· Signal: slope 20 ngày của DFII10 < 0 → cho phép long; > 0 → cấm long mới · Trade: overlay gate cho S1/S3/S6, không standalone.
· Risk: DFII10 revised; chuỗi flat cho gate lơ lửng · Data: FRED DFII10 daily + giá D · Coupling: breakeven song hành (tránh inflation-scare giả).

**S3 — 200-DMA pullback-buy (Trend)** — Hypothesis: trong uptrend xác nhận (giá > 200DMA, 200DMA dốc lên), pullback đầu tiên về 50DMA là entry risk/reward tốt nhất của nhà trend.
· Signal: giá > 200DMA ∧ 50DMA > 200DMA ∧ giá chạm 50DMA lần đầu trong 20 ngày · Trade: buy limit tại 50DMA, stop dưới swing low − 1×ATR, trail 2.5×ATR.
· Risk: regime flip khi TIPS spike (9/2026-style) — pullback thành breakdown; kill-switch khi close D < 200DMA · Data: giá D · Coupling: DXY không lập đỉnh 20 ngày trong tuần entry.

**S4 — ADX-verified breakout continuation (Trend)** — Hypothesis: breakout vàng có follow-through khi trend-strength đã cao *trước* break (khác tính chất MR của nhiều cặp FX).
· Signal: ADX(14) D > 25 và breakout 20-bar high có closing confirmation · Trade: enter tại close, stop = breakout level − 1.5×ATR, exit trail.
· Risk: ADX lag — vào muộn đoạn đã chạy 2 ATR · Data: OHLC D (+volume GC nếu có) · Coupling: volume COMEX > 20d avg xác nhận.

**S5 — Kim loại dual-momentum rotation (Trend)** — Hypothesis: giữa vàng và bạc, giữ metal có 3M-return cao hơn nâng Sharpe vì beta bạc chỉ trả trong risk-appetite, và rotation tránh đoạn bạc bị bóp工业.
· Signal: ranking 63-day return XAUUSD vs XAGUSD, re-rank tuần · Trade: hold metal mạnh hơn; neutral khi cả hai âm.
· Risk: rotation đúng lúc tương quan gãy (silver squeeze riêng); whipsaw khi chênh lệch mỏng · Data: giá D hai symbol · Coupling: G/S ratio làm context (67.9 hiện tại — trung tính).

**S6 — 12-1 time-series momentum (Trend)** — Hypothesis: return 12 tháng trừ 1 tháng gần nhất có predictive sign ở vàng (momentum của tài sản thay thế tiền tệ).
· Signal: sign của XAUUSD return (252−21) ngày, đổi trạng thái đầu tháng · Trade: long/flat (không short thuần vì CB floor), flip theo sign.
· Risk: đảo regime (đầu 2026: từ +momentum sang −26%) phản ứng chậm 3–6 tháng · Data: giá D ≥ 15 năm · Coupling: chỉ flip long khi CB 6m-buying > 0.

**S7 — Vol-target trend sizing (Trend)** — Hypothesis: sizing theo inverse-vol nâng Sharpe của mọi trend entry vì vol vàng cluster mạnh (GARCH-persistent).
· Signal: core = EMA20/50 cross D; size = target 10% annual vol ÷ realized 20d vol, cap 2x · Trade: theo core signal, chỉ đổi size.
· Risk: vol-burst ngay sau khi tự giảm size → underexposed ở turn · Data: OHLC D + realized vol · Coupling: sau ngày |r|>3% (như 28/09) khoá size tối thiểu 24h.

**S8 — BOS/retest price-action trend (Trend)** — Hypothesis: cấu trúc swing H4 (break-of-structure rồi retest) bắt trend sớm hơn MA mà không parameter nặng — tận dụng stop-flow phía trên đỉnh cũ.
· Signal: break swing-H4 gần nhất → pullback retest 38–62% đoạn break bằng rejection candle · Trade: enter retest, stop dưới rejection low, target = 1×đoạn gốc.
· Risk: fake-BOS hình thành trong Asia mỏng · Data: H4 OHLC · Coupling: chỉ take nếu xảy ra trong London/NY overlap.

**S9 — CB-tail trend-follow (Trend)** — Hypothesis: khi NHTW mua ròng > ngưỡng (vd > 70t/tháng trailing 3m), phân phối return vàng nghiêng rõ về phía dương → trend-long có expectancy cao hơn hẳn.
· Signal: WGC/IFS net CB tonnage trailing 3 tháng > ngưỡng · Trade: cho phép double-size module trend long (S1/S3).
· Risk: dữ liệu CB trễ 1–2 tháng + revised — snapshot luôn stale · Data: WGC monthly CB statistics, IMF IFS · Coupling: giá không vượt +2σ dải 200DMA (không mua đỉnh bubble).

**S10 — Momentum-crash de-risking (Trend)** — Hypothesis: сочет VIX-spike + DXY-breakout cùng ngày là early-warning của liquidation cascade (vàng bị bán để cover margin) — cần cắt trend kịp lúc.
· Signal: VIX +20% intraday ∧ DXY vượt 20-bar high cùng phiên ∧ vàng giảm > 1.5×ATR · Trade: thoát nửa trend-long, hedge nửa còn lại bằng short H4 đến khi vol dịu.
· Risk: whipsaw nếu VIX-spike tự dập trong 1 ngày · Data: VIX, DXY, XAUUSD intraday · Coupling: vào lại định kỳ sau 3 phiên yên tĩnh.

### Family B — Mean-reversion (S11–S20)

Lý do kinh tế: hành vi mean-revert của vàng đến từ (i) dealer hedging quanh fix, (ii) physical premium bands, (iii) overshoot sau rate-shock rồi rates nghỉ. Cái chết: trend real-yield mạnh + CB-pause — nên mọi ý có lọc sự kiện/regime.

**S11 — Asia-range z-score fade (Mean-reversion)** — Hypothesis: biên range Asia do thanh khoản mỏng hay bị quét quá biên trong London overlap rồi kéo về VWAP ngày.
· Signal: giá vượt biên range Asia (00:00–06:00 UTC) > 0.5×ATR_H1 ∧ |z| H1 > 2 · Trade: fade ngược hướng, stop 1×ATR_H1 ngoài biên, target VWAP.
· Risk: ngày có data/sự kiện 8:30 ET đổi chiều thẳng — cấm NFP/CPI/FOMC · Data: H1 + lịch event · Coupling: chỉ khi TIPS ngày đó ±<3bp (ngày rates yên tĩnh).

**S12 — RSI(2) swing-buy trong uptrend (Mean-reversion)** — Hypothesis: oversold cực ngắn trong trend dài là điểm nhập của oscillator money (Connors-style) — thắng nhờ trend-context chứ không phải oscillator.
· Signal: giá > 200DMA ∧ RSI(2) D < 10 · Trade: buy market, exit khi close > EMA5 hoặc RSI(2)>70; stop 2×ATR.
· Risk: knife-catch khi 200DMA vừa gãy — chỉ chạy khi 200DMA dốc lên · Data: giá D · Coupling: skip nếu TIPS +>5bp trong 2 ngày trước đó.

**S13 — Round-number magnet fade (Mean-reversion)** — Hypothesis: mốc $100-handle ($4,000/$4,100/$4,200) hút liquidity; spike vượt handle đầu tiên trong tuần thường revert khi không có macro mới.
· Signal: lần đầu xuyên handle trong tuần, giờ không-event, không trend-day (ADX intraday < 20) · Trade: fade về handle, stop 0.6×ATR_H1 ngoài handle, target handle.
· Risk: breakout thật qua handle khi có flow ngày (CB/ETF) — cần volume-check · Data: H1 + volume futures nếu có · Coupling: chỉ trade phía spike hướng về handle.

**S14 — SGE premium mean-reversion (Mean-reversion)** — Hypothesis: premium SGE–LOCO London có band cân bằng do quota xuất-nhập; premium z>2 прогноз pullback (physical demand bão hòa ở đắt quá).
· Signal: SGE premium z-score 20 ngày vượt ±2 · Trade: fade giá London 1–2 ngày theo hướng premium normalize.
· Risk: chính sách quota TQ đổi làm band dịch vĩnh viễn; nguồn data premium công khai hạn chế · Data: SGE premium daily · Coupling: chỉ khi CNH ổn định (không stress tỷ giá TQ).

**S15 — Real-yield shock snapback (Mean-reversion)** — Hypothesis: sau cú tăng TIPS +>15–20bp/tuần mà KHÔNG có Fed event trong 48h tới, phần phản ứng quá mức của vàng (−>2.5×ATR tuần) hồi một phần vì rates nghỉ.
· Signal: ΔDFII10 5 ngày > +15bp ∧ XAUUSD 5-day return < −2×ATR · Trade: buy峭 size nhỏ, target 1×ATR_D, stop đáy swing; exit trước event.
· Risk: chuỗi shock liên tiếp (chính Sep-2026); event < 48h tới → skip · Data: DFII10 + lịch FOMC/CPI + giá D · Coupling: breakeven không tăng cùng (nếu cả nominal lẫn breakeven tăng → skip, đó là inflation-shock thật).

**S16 — COMEX-session VWAP reversion (Mean-reversion)** — Hypothesis: opening drive 13:30–14:00 UTC thường quá biên do stop-run rồi trở về VWAP phiên NY.
· Signal: |giá − VWAP_NY| > 1.5×ATR_M15 sau 14:15 UTC · Trade: fade về VWAP, stop 2×ATR_M15, time-exit 17:00 UTC.
· Risk: trend-day data (release 8:30 mạnh) — skip khi có · Data: M15 + lịch · Coupling: DXY intraday cùng chiều ban đầu (macro-driven, không idio).

**S17 — Stretch-from-200DMA reversion (Mean-reversion)** — Hypothesis: deviation > +2σ của dải quanh 200DMA (khi 200DMA phẳng, tức range-regime) tự revert do profit-take + CB không chase đỉnh.
· Signal: z = (giá − 200DMA)/σ252 > +2 ∧ slope 200DMA ≈ 0 · Trade: short nhẹ target 200DMA, stop z > +3.
· Risk: bắt đỉnh trong supercycle (đầu 2026: trên +2σ rồi còn chạy tới $5,589) · Data: giá D · Coupling: ETF flow ròng âm tuần đó (xác nhận distribution).

**S18 — Weekend-gap fill fade (Mean-reversion)** — Hypothesis: weekend gap 0.2–0.5×ATR_D phần lớn fill trong 1–2 phiên đầu tuần trừ khi có catalyst mới.
· Signal: Sunday-open gap vs Friday-close thuộc bucket nói trên ∧ lịch tuần không có FOMC/CPI ngay thứ 2–3 · Trade: fade về Friday close; stop 0.8×ATR.
· Risk: gap theo hướng catalyst tuần (Hormuz-type headline cuối tuần) — cấm khi geo đang hot · Data: Sunday open feed + lịch · Coupling: Brent Monday-open không gap cùng hướng >1%.

**S19 — Synthetic-gold deviation trade (Mean-reversion)** — Hypothesis: tái tạo "vàng bóng FX" bằng hồi quy XAUUSD ~ EURUSD + USDJPY + DXY; residual idiosyncratic quá biên sẽ revert — biến CB-flow/overshoot thành số đo.
· Signal: residual z 30 ngày > ±2 · Trade: trade residual (long gold + hedge FX theo beta), target z→0.
· Risk: residual thật là thông tin (CB mua mạnh) — tránh khi WGC đang báo cáo mua mạnh · Data: giá D các cặp + OLS rolling · Coupling: R² rolling > 0.6 mới active.

**S20 — Liquidation-cascade relief bounce (Mean-reversion)** — Hypothesis: sau 3 ngày giảm lớn nhất trong quý + washout positioning, 1–3 phiên kế tiếp có drift dương (forced sellers cạn; đúng kiểu cuối chuỗi bán 9/2026).
· Signal: 3-day return thuộc phân vị 1% tệ nhất 252 ngày ∧ MM net length COT < percentile 20 · Trade: buy cuối phiên ngày 3 hoặc mở ngày 4, stop đáy cascade, exit 3 phiên.
· Risk: falling-knife — bắt buộc xác nhận COT washout · Data: giá D + COT · Coupling: TIPS không lập đỉnh tuần mới ngay sau đó.

### Family C — Breakout / Vol-expansion (S21–S30)

Lý do kinh tế: dealer anchoring quanh session-level, compression năng lượng vol, stop-cluster trên đỉnh/đáy cũ. Cái chết: session-breakout trong tuần event; compression-break bị CB floor fade khi short.

**S21 — Asia-range London breakout (Breakout)** — Hypothesis: biên range Asia là anchor của dealer; break có volume London follow-through trong 2 giờ đầu.
· Signal: break Asia high/low sau 07:00 UTC giữ ≥ 2 bar H1 · Trade: follow break, stop giữa range Asia, target 1×chiều dài range.
· Risk: fake quanh fix 10:30 — exit tại fix nếu chưa đạt 1R · Data: H1 OHLC · Coupling: ngày không có data 8:30 ET phía sau (nếu có, thu nhỏ target).

**S22 — COMEX-open volume thrust (Breakout)** — Hypothesis: nến 13:30–14:00 UTC với volume > 120% avg20 và body > 1×ATR_H1 dự báo hướng phiên NY.
· Signal: thrust candle theo định nghĩa trên · Trade: enter break candle-high/low, stop ngoài candle, exit 20:00 UTC.
· Risk: hai thrust ngược chiều (data-day) → chỉ take cái đầu · Data: M15/H1 + volume GC · Coupling: DXY trust cùng hướng.

**S23 — NR7 compression straddle (Breakout)** — Hypothesis: tuần có daily-range hẹp nhất 7 tuần (NR7) tích năng lượng; hướng break có momentum tuần kế tiếp.
· Signal: NR7 tuần hiện tại; OCO stop-order hai phía quanh high/low tuần NR7 · Trade: stop 1×ATR_D, trail; hủy phía còn lại khi một phía trigger.
· Risk: chop hai phía — OCO nghiêm ngặt + re-entry tối đa 1 lần · Data: D OHLC · Coupling: IV options thấp trước break (nếu có feed) xác nhận compression.

**S24 — ATR-percentile ignition (Breakout)** — Hypothesis: chuyển vol-percentile từ < 20 lên > 50 trong ≤ 3 phiên cùng lúc break 10-bar extreme là ignition của trend mới (vol-before-price ở vàng).
· Signal: ATR_D percentile thỏa bộ trên, loại event-window · Trade: theo hướng break, stop 1.5×ATR mới.
· Risk: vol-spike do single event rồi tắt · Data: D OHLC + lịch · Coupling: GARCH forecast tăng đồng bộ.

**S25 — Pre-FOMC compression post-decision break (Breakout)** — Hypothesis: 24h trước FOMC vol nén; hướng break 15–60 phút sau statement có continuation trong phiên.
· Signal: range 4 giờ quanh decision; break giữ 3 bar M15 · Trade: follow, stop edge range, exit cuối phiên hoặc trail 1×ATR_H1.
· Risk: whip đầu tiên quanh statement rất hay xảy ra — chấp nhận 1 stop/reverse; cấm pre-position · Data: M5/M15 + lịch FOMC · Coupling: dot-plot shock cùng hướng (S54) thì hold qua hôm sau.

**S26 — Failed-breakout stop-hunt reversal (Breakout)** — Hypothesis: sweep beyond prior high/low < 0.3×ATR rồi đóng ngược vào range là dấu stop-hunt; move ngược có độ tin cao.
· Signal: liquidity sweep H1 + reversal bar đóng lại trong range · Trade: enter close reversal-bar, stop ngoài sweep extreme, target opposite side range.
· Risk: break thật hai bước (sweep rồi continue) — strict invalidation · Data: H1 · Coupling: hiệu quả nhất quanh session-open và fix.

**S27 — NY opening-range measured move (Breakout)** — Hypothesis: range 8:30–9:00 ET predictive: break đầu tiên chạy ~1×chiều range (measured move).
· Signal: break OR đầu tiên giữ 10 phút · Trade: target 1×OR, stop nửa OR.
· Risk: data-day hai chiều — skip ngày release lớn trừ khi release trùng hướng · Data: M5/M15 + lịch · Coupling: yield 10Y intraday không counter-trend mạnh.

**S28 — Weekly-close confirmation entry (Breakout)** — Hypothesis: chỉ tin break level khi weekly close vượt — giảm false-break, giữ phần lớn move (vàng tôn trọng weekly closes do flow institutional).
· Signal: weekly close ngoài 20-bar high/low · Trade: vào đầu tuần sau theo hướng, stop = level break, trail weekly.
· Risk: nhập muộn 1 tuần = tốn 1–2 ATR entry · Data: W OHLC · Coupling: COT cùng hướng tuần đó.

**S29 — Gap continuation vs exhaustion buckets (Breakout)** — Hypothesis: gap Sunday > 1.5×ATR có phi tuyến: bucket 1.5–2.5 ATR thường continuation, bucket > 3.5 ATR thường exhaustion.
· Signal: phân bucket gap theo ATR_D · Trade: bucket giữa follow gap; bucket cực fade với stop ngoài extreme.
· Risk: biên bucket là meta-parameter — fit theo regime vol, validate walk-forward · Data: Sunday opens 15 năm · Coupling: Brent/JPY gap cùng hướng xác nhận macro-gap.

**S30 — Cross-asset vol-storm directional (Breakout)** — Hypothesis: khi VIX cross > 30 và gold vol percentile > 90, hướng ngày đầu của cơn bão tiếp diễn 2–4 phiên (clustering), bất kể narrative.
· Signal: ngày |r_gold| > 2.5% ∧ VIX > 30 · Trade: follow hướng ngày đầu từ ngày 2, stop 1×ATR_D, exit khi VIX < 25.
· Risk: một-ngày-reversal (policy response tin) — chỉ 1 stop · Data: giá D + VIX · Coupling: TIPS không counter-move mạnh (nếu chạy ngược hướng gold, thoát).

### Family D — Carry / Structural (S31–S40)

Lý do kinh tế: người mua structural (NHTW, ETF-tilt, festival physical) tạo drift/floor không cần timing; term structure & funding (lease, EFP) trả tiền cho ai chịu phức tạp logistics. Cái chết: CB pause, quota đổi, hawkish macro đè seasonal.

**S31 — CB-buying floor ladder (Structural)** — Hypothesis: quanh vùng NHTW lịch sử tăng tốc mua (vùng "CB zone" 2026 ~$4,000–4,100 — cần kiểm chứng), phân phối downside bị nén → ladder long có convexity.
· Signal: giá vào zone ∧ WGC trailing CB buying > 60t/tháng · Trade: 3 nấc buy-limit cách 1×ATR_D (mỗi nấc 1/3 size), stop tổng dưới zone − 2×ATR, không time-stop.
· Risk: CB pause (TQ từng ngừng 6 tháng) — monitor định kỳ; zone dịch theo AISC + lạm phát · Data: WGC/IFS tonnage + giá · Coupling: ETF không đồng loạt outflow mạnh (nếu có, chờ pin bar).

**S32 — Futures term-structure roll yield (Carry)** — Hypothesis: trong backwardation (scarcity physical) long front-tháng kiếm positive roll; contango sâu thì tránh/reverse — carry thật của "hold vàng bằng futures".
· Signal: GC M1−M3 spread z-score · Trade: long front/short deferred khi backwardation sâu; exit khi z→0.
· Risk: curve dynamics đổi do storage/financing; cần tài khoản futures (CFD không có spread trực tiếp) · Data: GC curve daily · Coupling: lease rate cùng chiều.

**S33 — EFP / COMEX–London dislocation (Structural)** — Hypothesis: EFP (futures − spot London) có band cân bằng; stress thanh khoản (kiểu 3/2020) bung band tạo mean-revert có nền logistics.
· Signal: EFP z-score 60 ngày > ±3 · Trade: fade EFP bằng cặp futures vs spot proxy; size nhỏ (liquidity mỏng).
· Risk: dislocation kéo dài nhiều tuần; margin spike · Data: GC + spot London + lease/EFP feed · Coupling: chỉ khi VIX < 40.

**S34 — ETF-flow trend tilt (Structural)** — Hypothesis: GLD holdings 4 tuần tăng + giá > 200DMA = Western money xác nhận trend; tilt long có EV dương trên tuần kế.
· Signal: ΔGLD tonnage 20 ngày > 0 ∧ giá > 200DMA · Trade: long size cơ bản 0.5x, tăng 1x khi hai điều kiện giữ 4 tuần liên tiếp.
· Risk: ETF flow là lagging/crowding — đỉnh flow thường đỉnh giá · Data: GLD holdings daily · Coupling: COT MM không ở percentile > 90.

**S35 — Debasement core-long với real-yield cap (Structural)** — Hypothesis: long lõi vàng hợp lý trong xu hướng debasement NHƯNG phải tự cắt khi TIPS vượt cap — kết hợp long-bias với tail-protection.
· Signal: sleeve lõi 25% NAV; reduce về 0 khi DFII10 > cap (calibrate ~2.5%) hoặc slope dương 8 tuần · Trade: allocation động, rebalance tuần.
· Risk: cap bị prob thường xuyên (2.85% hiện tại) → sleeve đóng ~now, đúng chủ ý bảo toàn vốn · Data: DFII10 + giá · Coupling: CB mua mạnh cho phép nới cap +25bp.

**S36 — Lease-rate funding-stress spike (Structural)** — Hypothesis: lease rate tăng vọt = borrower hoảng loạn mượn physical (scarcity) — dẫn trước giá tăng vài phiên.
· Signal: lease rate (hoặc proxy forward) z > 3 · Trade: tactical long 3–8 phiên, stop 1×ATR.
· Risk: spike do technical delivery — check futures calendar · Data: lease/forward rate feed (thương mại; public hạn chế) · Coupling: EFP cùng tín hiệu (S33).

**S37 — Producer-hedging cycle contrarian (Structural)** — Hypothesis: khi ngành khai khoáng de-hedged hoàn toàn + giá dưới "incentive price" (marginal cost + 15%), supply tương lai thắt → floor cấu trúc dài hạn.
· Signal: tổng hedge book ngành ở low percentile ∧ giá < incentive band · Trade: accumulation dài hạn theo nấc, horizon nhiều quý.
· Risk: vàng không có "cân bằng cung cầu" thuần — financial demand áp đảo; horizon quá dài để verify nhanh · Data: hedge book disclosures (tập hợp thủ công) · Coupling: mine supply growth chậm (WGC).

**S38 — Festival-demand seasonal carry (Structural/Seasonality)** — Hypothesis: cầu physical Ấn Độ (Diwali, đám cưới) + TQ (Tết) tạo drift dương Oct→Feb khi macro không adversarial.
· Signal: gate giữa Tháng 10: TIPS 20d-slope ≤ 0 HOẶC SGE premium dương · Trade: long Tháng 10→tháng 2, stop time 15%/năm, exit sớm nếu gate gãy.
· Risk: seasonal yếu trước macro (2026: TIPS 2.85% dốc lên — gate đang FAIL) · Data: giá D + SGE premium + TIPS · Coupling: G/S không ở cực thấp (silver-crowded).

**S39 — De-dollarization macro basket (Structural)** — Hypothesis: xu hướng diversification dự trữ biểu hiện qua spread "gold vs reserve-bond basket" (short UST+JGB+Bund theo trọng số reserve, long gold) có drift dương dài hạn.
· Signal: trend bằng 200DMA của spread · Trade: giữ spread, hedge nominal duration, rebalance quý.
· Risk: câu chuyện 10 năm — drawdown intra −20%; carry trái chiều (trả coupon short) · Data: futures UST/Bund/JGB + gold · Coupling: % reserve USD global (COFER quý) xác nhận.

**S40 — Tail-hedge substitution (Options/Structural)** — Hypothesis: khi gold skew/RR rẻ (put-bid thấp, IV thấp), thay thế phần bảo hiểm danh mục bằng long call vàng rẻ hơn protection khác.
· Signal: 25Δ RR percentile < 30 ∧ IV percentile < 40 · Trade: buy OTM call 2–3 tháng làm portfolio-hedge thay SPX put.
· Risk: gold hedge thua khi stress đi kèm rate-shock (bài học 9/2026) — cap tỷ trọng · Data: options COMEX · Coupling: activation khi TIPS slope ≤ 0 (gold-hedge hiệu quả nhất khi rates hỗ trợ).

### Family E — Session / Time-of-day / Seasonality (S41–S50)

Lý do kinh tế: cấu trúc participant theo giờ (physical bank quanh fix, dealer NY quanh open, books-flattening cuối tuần) + chu kỳ nhu cầu physical theo mùa. Cái chết: DST bug, lịch event trùng, regime macro đè mùa.

**S41 — London-fix window drift (Session)** — Hypothesis: quanh LBMA fix 10:30 London có micro-drift theo tháng (fix-flow bank) đo được trên lịch sử.
· Signal: thống kê drift 09:45–10:45 London theo tháng rolling 3 năm, chỉ trade tháng |t|>2 · Trade: M15 theo drift, stop 0.8×ATR_M15, exit sau fix 30 phút.
· Risk: cấu trúc fix đã đổi sau scandal — drift không stable; validate khắc nghiệt · Data: M15 + lịch fix · Coupling: không ngày data 8:30 ET.

**S42 — Asia-extreme London fade (Session)** — Hypothesis: extreme hình thành 00:00–05:00 UTC (thin book) bị test lần hai và đảo trong London (double-test fail).
· Signal: giá tag extreme Asia lần 2 và không vượt thêm 0.2×ATR_H1 · Trade: fade từ extreme, stop ngoài extreme +0.3×ATR, target mid-range Asia.
· Risk: ngày trend thật từ London open — skip nếu London open break mạnh · Data: H1 · Coupling: khác biệt vs S11: dùng cấu trúc double-test chứ không z-score.

**S43 — COMEX 30-min momentum persistence (Session)** — Hypothesis: return 13:30–14:00 UTC dự báo 14:00–16:30 UTC khi volume cửa sổ đó > 120% avg.
· Signal: |r30| > 0.5×ATR_H1 ∧ volume điều kiện · Trade: follow r30, stop 1×ATR_H1, exit 16:30 UTC.
· Risk: phân phối fat-tail — size theo vol · Data: M30 + volume · Coupling: yield 10Y cùng hướng.

**S44 — Friday profit-squaring reversal (Session)** — Hypothesis: extension cuối chiều Friday (17:00–20:00 UTC) do books-flattening thường reverse một phần trước close — nhất thiết sau tuần đã có move lớn.
· Signal: |r_week| > 2×ATR_W ∧ Friday extension cùng hướng > 1×ATR_D trong giờ cuối · Trade: fade size nửa, flat trước close.
· Risk: quarterly rebalance/OPEX hành vi khác — exclude · Data: H1 + lịch · Coupling: gap-risk-weekend cao thì giảm size thêm.

**S45 — Monday-gap directional with catalyst (Session)** — Hypothesis: Monday gap có follow-through cả tuần chỉ khi tuần đó có catalyst macro lớn xếp giữa tuần và gap cùng hướng "positioning for event".
· Signal: Monday gap > 0.5×ATR ∧ lịch tuần có event trung tâm · Trade: hold hướng gap đến trước event T−1.
· Risk: fade-into-event (gap bị hoàn trước event) — stop 1×ATR · Data: weekly opens + lịch · Coupling: COT positioning phía gap.

**S46 — OPEX pin & post-OPEX drift (Session/Options)** — Hypothesis: tuần hết hạn option COMEX giá pin quanh strike có OI lớn; sau OPEX có drift rời strike (gamma release).
· Signal: xác định strike max-OI; khoảng cách < 0.5×ATR_D trong 3 phiên cuối · Trade: pin-week fade extremes quanh strike; post-OPEX follow break khỏi strike.
· Risk: pin yếu khi vol cao; cần data OI · Data: options OI COMEX · Coupling: dealer-gamma sign (S78) xác nhận.

**S47 — September seasonal weakness (Seasonality)** — Hypothesis: sau Labor Day, dài-position book (summer rally) thường bị vuốt trước mùa physical Q4 + window-dressing — drift âm Sep nhiều thập kỷ.
· Signal: gate hiện đại: chỉ short Sep khi TIPS slope dương (regime hawkish đồng thuận với mùa) · Trade: short đầu Tháng 9, cover cuối tháng, stop 1.5×ATR_D.
· Risk: geo shock ngẫu nhiên đổi mùa (năm có chiến tranh Sep thành hai chiều) · Data: lịch sử 25 năm · Coupling: ETF flow giảm trong Aug (xác nhận book dài).

**S48 — Diwali/CNY accumulation window (Seasonality)** — Hypothesis: 6 tuần trước Diwali và 4 tuần trước Tết TQ có physical-bid rõ (SGE + premium Ấn) nâng xác suất local bottom.
· Signal: lịch của năm + SGE premium z > 1 · Trade: buy pullback trong window (không chase), stop 1.5×ATR, exit sau lễ 1 tuần.
· Risk: hawkish macro đè (2026-style) — gate TIPS bắt buộc · Data: SGE premium + lịch văn hóa · Coupling: INR/CNH không stress (người mua physical nhạy local FX).

**S49 — Overlap-session concentration execution (Session)** — Hypothesis: phần lớn EV của các ý intraday nằm 12:30–16:30 UTC; cắt risk ngoài khung này nâng IR vì spread/slippage ngoài khung ăn mòn.
· Signal: thời gian · Trade: wrapper điều hành mọi ý intraday chỉ active khung overlap.
· Risk: bỏ gap Asia; một số ý (S11) cần Asia để build signal — wrapper phải cho phép exception · Data: timestamps UTC tuyệt đối · Coupling: DST — log giờ theo UTC, không local.

**S50 — NFP-Friday two-step pattern (Session)** — Hypothesis: spike 8:30 ET, retrace 9:30–10:30, rồi continuation/reversal theo quy tắc 50%-retention: spike không giữ 50% mức trong 30 phút → hướng cuối buổi sáng = hướng phiên.
· Signal: NFP release bar + quy tắc retention · Trade: enter 10:30 theo rule, stop ngoài spike-extreme, target 1.5R, flat trước close.
· Risk: NFP mix (payroll vs unemployment trái chiều) → skip · Data: M5 + lịch NFP · Coupling: yield-reaction cùng hướng gold-reaction = xác nhận Hawk-Dovish sạch.

### Family F — Event / Data-driven (S51–S60)

Lý do kinh tế: vàng phản ứng data qua *cầu nối duy nhất* là repricing đường lãi suất thực; hiểu cầu nối cho phép dự đoán dấu của phản ứng theo regime. Cái chết: bỏ qua điều kiện regime — cùng một CPI, hai năm khác nhau hai dấu.

**S51 — CPI-day inverse-surprise trade (Event)** — Hypothesis: ở regime hawkish (hike-cycle), core CPI surprise ↑ → gold ↓ ngay và tiếp tục trong phiên (kênh rate áp đảo kênh inflation-hedge).
· Signal: core CPI m/m lệch consensus > 1σ lịch sử surprise · Trade: theo hướng −surprise (CPI nóng → short) tại 8:35 ET sau khi spread ổn, stop 1×ATR_H1, exit cuối phiên.
· Risk: regime đổi khi Fed pivot — chỉ chạy khi hike-prob > 50% cho kỳ họp tới · Data: surprise history + real-time print + M5 · Coupling: khớp bảng 9/2026 (hawkish, gold yếu).

**S52 — FOMC statement-diff trade (Event)** — Hypothesis: đổi wording statement (thêm/bỏ kiểu "will deliver price stability") mang thông tin vượt quyết định đã priced; hướng diff + dot xác định hướng phiên.
· Signal: NLP-diff statement vs kỳ trước + hướng SEP median · Trade: vào 5 phút sau release theo hướng, stop 1.5×ATR_H1, hold qua ngày nếu diff mạnh.
· Risk: interpret market khác mô hình — validate trên ≥ 20 cuộc họp · Data: statements archive + giá · Coupling: 2Y yield cùng hướng gold-inverse (hike-ish: 2Y↑, gold↓).

**S53 — Labor-weakness pivot-buy (Event)** — Hypothesis: unemployment +0.2pp hoặc payroll miss lớn khởi động pivot-pricing → vàng tăng mạnh 2–5 phiên sau (kênh rates cùng chiều safe-haven).
· Signal: U3 jump hoặc NFP miss > 150k vs consensus · Trade: buy close phiên release, stop 1×ATR, trail 5 phiên.
· Risk: "bad news is bad" khi recession thật → vàng bị bán cùng mọi thứ · Data: BLS releases + giá · Coupling: chỉ khi VIX < 28.

**S54 — Dot-plot shock trade (Event)** — Hypothesis: lệch giữa SEP median và market-implied path (OIS) tại giờ họp là shock thuần; gold phản ứng theo chiều dovish-surprise.
· Signal: Δ(SEP median − OIS implied) tại 19:00 ET presser · Trade: theo chiều dovish surprise, hold qua H+1 nếu |Δ| ≥ 25bp đường.
· Risk: presser đảo statement — exit rule tại 20:00 ET · Data: SEP + OIS curve + M5 · Coupling: dùng chung hạ tầng diff với S52.

**S55 — Breakeven lead-lag catch-up (Event)** — Hypothesis: 10Y breakeven di chuyển trước, gold adjust chậm 30–120 phút khi move do flow (không phải headline chung tác động cả hai cùng lúc).
· Signal: ΔBE 60 phút > 3bp ∧ gold flat cùng khung · Trade: buy gold theo hướng inflation-up, stop 0.8×ATR_H1, time-exit 2h.
· Risk: move BE do supply auction — loại khi trùng giờ auction · Data: BE intraday + giá · Coupling: oil không phải nguyên nhân trực tiếp (tránh chồng S64).

**S56 — Speaker-spike fade (Event)** — Hypothesis: spike do phát ngôn Fed không kèm move yields là noise — fade.
· Signal: gold |move| > 0.7×ATR_H1 trong 2 phút quanh headline Fed ∧ Δ10Y < 1bp · Trade: fade spike, target pre-spike, stop ngoài extreme.
· Risk: yields catch-up muộn (spike thành thật) — invalidation khi 10Y chạy cùng hướng spike · Data: headline feed + yields intraday · Coupling: tốt nhất giờ Asia mỏng.

**S57 — Geopolitical risk-premium decay model (Event)** — Hypothesis: escalation verified (kiểu Hormuz 25–27/09/2026) đưa risk-premium vào giá trong 5–60 phút rồi decay theo hàm mũ (τ ~ vài giờ) nếu không leo thang vật lý.
· Signal: event-classification + spike ≥ 1×ATR_H1 KHÔNG kèm TIPS rally · Trade: buy 2–5 phút sau headline, exit theo decay-schedule hoặc trail 0.5×ATR_H1, tối đa 6h hold.
· Risk: FALSE trong regime Sep-2026 (kênh hike đè) — gate bắt buộc: ΔTIPS cùng ngày ≤ +2bp; escalation leo thang → thoát · Data: news feed timestamp + TIPS + M5 · Coupling: CHF/JPY cùng bid xác nhận safe-haven tổng thể.

**S58 — CB-report drift (Event)** — Hypothesis: số liệu NHTW mua (WGC monthly / GDT quarterly) gây drift 1–3 phiên theo hướng surprise vs kỳ vọng ngầm (consensus ~ trailing average).
· Signal: tonnage vượt trailing-12m avg > 20% · Trade: buy sau release, stop 1×ATR, exit 3 phiên.
· Risk: số liệu trễ — giá phản ánh trước (CB mua âm thầm qua London) · Data: WGC calendar + giá · Coupling: giá trong CB zone (S31) thì drift mạnh hơn.

**S59 — Treasury-auction tail trade (Event)** — Hypothesis: 10Y/30Y auction tail yếu → real yield lên → vàng xuống trong giờ sau; strong bid → ngược.
· Signal: bid-to-cover & tail vs 6-auction avg · Trade: theo kênh (tail → short 1h), stop 0.6×ATR_H1.
· Risk: reaction bị macro cùng giờ đè — validate bucket theo vol regime · Data: auction results + M15 · Coupling: tốt nhất khi không có Fed speaker cùng giờ.

**S60 — Pre-event vol crush (Event/Options)** — Hypothesis: IV event (FOMC/CPI) thường over-priced vs realized post-event khi positioning đã extreme một chiều.
· Signal: IV term structure trước event > 90th percentile + RR/positioning extreme · Trade: short strangle bằng options futures, delta-hedge theo khung, exit event +1h.
· Risk: event tail thật — size nhỏ + defined-risk spreads, không naked · Data: IV surface COMEX · Coupling: margin + commission đầy đủ trong giả định.

### Family G — Cross-asset / Correlation (S61–S70)

Lý do kinh tế: vàng là "tổng hợp" của USD + real rates + risk + inflation; các đối tượng còn lại trong universe là các thành phần — trade chênh lệch/tổng hợp thay vì directional thuần. Cái chết: hệ số tương quan bất ổn; chồng tín hiệu (multicollinearity).

**S61 — TIPS-residual regression trade (Cross-asset)** — Hypothesis: mô hình XAUUSD = f(DFII10, DXY) ổn định trong regime; residual quá biên revert — biến "vàng đắt/rẻ so với macro" thành con số.
· Signal: residual z 60 ngày > ±2 · Trade: trade residual (gold + hedge TIPS/DXY theo beta futures), target z→0, stop z ±3.
· Risk: structural shift (CB era) làm residual "đắt" mãi — re-estimate rolling, cắt khi R² collapse · Data: DFII10 + DXY + futures hedge · Coupling: 9/2026: residual là câu hỏi mở — CB-floor có đang kẹp vàng trên mức TIPS-2.85% hàm ý không?

**S62 — DXY-beta-neutral gold book (Cross-asset)** — Hypothesis: phần lớn drawdown vàng là USD-move; strip beta USD thì phần idio còn lại (real-yield/CB/geo) có tín hiệu rõ hơn để trade.
· Signal: beta rolling 60 ngày vs DXY · Trade: quy trình quản trị — overlay hedge DXY futures cho mọi module directional.
· Risk: beta bất ổn khi regime đổi → hedge sai · Data: DXY + gold + futures · Coupling: dùng kèm S61 chung hạ tầng.

**S63 — Gold-silver ratio regime bands (Cross-asset)** — Hypothesis: G/S dao động trong band thô (60–90) và extreme dự báo relative performance: > 80 long XAG/short XAU; < 60 ngược — phản ánh risk-appetite của phức kim loại.
· Signal: G/S vs band rolling 5 năm (hiện 67.9 — trung tính) · Trade: spread XAG–XAU theo hướng extreme, stop khi vượt extreme +5%, size theo vol-spread.
· Risk: structural shift (silver solar-demand) dịch band vĩnh viễn — calibrate walk-forward · Data: giá D hai symbol · Coupling: gold regime gate từ S91.

**S64 — Oil-shock inversion pair (Cross-asset)** — Hypothesis: trong hike-regime, oil-shock là *tiêu cực* cho vàng (CPI↑ → hike↑ → real yield↑); pair long-oil/short-gold thu đoạn divergence không cần directional view.
· Signal: regime flag (hike-prob > 50%) ∧ Brent 5d z > 2 → short gold vs long Brent beta-matched · Trade: vào khi hai chân confirm; exit khi hike-prob < 40% hoặc TIPS đảo slope.
· Risk: tương quan đổi sign giữa chừng — stop pair-level; margin hai chân · Data: Brent + gold + hike-prob feed (OIS) · Coupling: verify tinh thần 28/09/2026 (Brent +3.6% vs gold −3.25%).

**S65 — Gold-vs-copper growth hedge (Cross-asset)** — Hypothesis: vàng over copper là câu chuyện stagflation/risk-off; khi growth-leading indicators gãy, spread long-gold/short-copper outperform.
· Signal: PMI composite < 50 và giảm 2 tháng · Trade: spread theo beta-vol, exit khi PMI > 50 trở lại.
· Risk: copper idio supply (đình công mỏ) — beta-hedge + size nhỏ · Data: PMI + futures HG/GC · Coupling: kết hợp S98.

**S66 — USDJPY-divergence spillover (Cross-asset)** — Hypothesis: khi JPY yếu/mạnh vọt (can thiệp MoF hoặc BoJ shift), giá vàng tính JPY tại Nhật (tài sản phổ biến của retail Nhật) tạo flow → ảnh hưởng global marginal.
· Signal: intervention-verified ngày + XAUJPY break 20-bar · Trade: trade XAUUSD cùng hướng XAUJPY break 1–2 phiên.
· Risk: hai chiều không stable, horizon ngắn · Data: USDJPY + XAUJPY + tin can thiệp · Coupling: DXY cùng tín hiệu thì tăng size.

**S67 — AUD-confirmation gate (Cross-asset)** — Hypothesis: breakout vàng có độ tin cao hơn khi phức anti-USD commodity (AUD) breakout cùng — chứng minh USD-weakness broad chứ không idio-gold.
· Signal: gold 20-bar break ∧ AUDUSD 20-bar break cùng hướng trong tuần · Trade: cho breakout system tăng size 1.5x khi confirm; không trade ngược.
· Risk: chỉ là gate — cor cao thì redundancy · Data: AUDUSD + gold · Coupling: G/S không ở extreme ngược hướng.

**S68 — VIX-convexity conditional bid (Cross-asset)** — Hypothesis: VIX>30 chỉ tạo gold-bid bền khi real yields flat/falling; nếu TIPS surge thì VIX-bid bị nuốt (bài học Sep-2026).
· Signal: VIX cross 30 ∧ slope TIPS 5d ≤ 0 → buy; slope > 0 → no-trade · Trade: buy khi đủ bộ, trail 2×ATR, exit VIX < 25.
· Risk: điều kiện hiếm — selective by design · Data: VIX + DFII10 + giá · Coupling: USDCHF cùng directional (double safe-haven confirm).

**S69 — BTC-vs-gold debasement pair (Cross-asset)** — Hypothesis: hai tài sản cạnh tranh vai "debasement hedge"; relative performance theo liquidity regime (BTC thắng khi liquidity dồi dào, gold khi thắt + geo nóng).
· Signal: rolling 90d return spread vs liquidity proxy (M2 + Fed balance) · Trade: rotate exposure theo hướng spread-forecast.
· Risk: BTC idio lớn (halving, ETF flow) — band rộng, size nhỏ · Data: BTC daily + liquidity proxies · Coupling: regime gate S91.

**S70 — Energy-complex PCA residual filter (Cross-asset)** — Hypothesis: phần move vàng "giải thích bởi" energy-complex (Brent/WTI/NATGAS PCA factor) là kênh inflation; phần dư là real-rate/safe-haven — tách kênh giúp chọn strategy-family đúng.
· Signal: rolling regression gold ~ energy-PC1; residual sign & magnitude · Trade: meta-filter — dư âm lớn + TIPS↑ → ưu tiên trend-short; dư dương + VIX↑ → ưu tiên safe-haven long.
· Risk: nhân quả mờ — chỉ diagnostic · Data: 3 energy symbols + gold · Coupling: nền tảng cho S64/S91.

### Family H — Positioning / Flows (S71–S80)

Lý do kinh tế: giá là flow; các báo cáo định kỳ (COT, ETF holdings, OI options) là kính lúp nhìn flow chậm một tuần — đủ để trade multi-day, không đủ cho intraday. Cái chết: crowding kéo dài trong structural bull; dữ liệu trễ/revised.

**S71 — COT Managed-Money extreme fade (Positioning)** — Hypothesis: MM net length percentile > 90 (hoặc < 10) đánh dấu crowding; 2–4 tuần sau drift ngược.
· Signal: percentile MM net spec length trong COT weekly · Trade: tại extreme: cắt positions sẵn có; contrarian entry nhỏ ngược hướng, stop 2×ATR, horizon 3 tuần.
· Risk: crowding kéo dài trong structural-bull (CB era dài hạn long-crowded mà vẫn lên) · Data: CFTC COT (Fri 15:30 ET) · Coupling: giá + TIPS cùng confirm exhaustion (double-top + TIPS đỉnh).

**S72 — Commercial-hedge confirmation (Positioning)** — Hypothesis: commercials max-short xảy ra muộn trong uptrend — kết hợp MM extreme tạo double-confirm cho đỉnh vùng.
· Signal: producer net-short percentile > 85 ∧ MM long percentile > 85 cùng tuần · Trade: chuẩn bị short/exit longs; entry sau break 20-bar low đầu tiên.
· Risk: commercials structural short — so percentile, không level · Data: COT · Coupling: chặt hơn S71 — dùng làm confirm layer.

**S73 — GLD-flow momentum confirm (Positioning)** — Hypothesis: trend dài cần Western-flow xác nhận; entries có GLD 4w-flow > 0 có win-rate cao hơn rõ.
· Signal: ΔGLD tonnage 20 ngày · Trade: gate tăng/giảm size cho module trend (không entry riêng).
· Risk: lag ~1 tuần của holdings data · Data: GLD holdings · Coupling: vai trò confirm cho S34/trend system.

**S74 — Price-ETF divergence fade (Positioning)** — Hypothesis: giá lập new-high mà holdings không lập new-high = uptrend thiếu fuel — fade/exit.
· Signal: giá 20-bar high ∧ holdings < high 20 ngày trước ≥ 1% · Trade: thoát long trend; short nhỏ với stop trên giá mới 0.5×ATR.
· Risk: CB-era giá lên không cần ETF (2022–25) — check CB mua mạnh thì skip · Data: giá + GLD · Coupling: S31 CB-flow check bắt buộc.

**S75 — CB+MM alignment dashboard (Positioning)** — Hypothesis: khi "smart-structural" (NHTW mua mạnh) và "fast-money" (MM washout percentile < 20) cùng xảy ra, xác suất rally 1–2 tháng cao bất thường (floor người mua lớn + fuel người quay lại).
· Signal: hai điều kiện đồng thời · Trade: long 1–2 tháng, stop 2×ATR_D, scale-out.
· Risk: hai data-đường khác nhịp (COT tuần, CB tháng) — alignment hiếm, sẵn sàng miss · Data: WGC + COT · Coupling: tư duy "floor + fuel" dùng chung S31/S96.

**S76 — Max-pain / OI pinning (Positioning/Options)** — Hypothesis: tuần OPEX giá bị hút về strike max-pain (dealer hedging tối ưu).
· Signal: strike max-OI + gamma dealer dương (ước tính) · Trade: mean-revert quanh strike tuần OPEX, stop ngoài 1×ATR_D từ strike.
· Risk: pin yếu khi event lớn rơi tuần OPEX · Data: options OI/gamma ước tính · Coupling: S46 là bản session, đây là bản position-week.

**S77 — Risk-reversal contrarian (Positioning/Options)** — Hypothesis: 25Δ RR cực âm (put khan) phản ánh panic-hedging — thường gần đáy vol; cực dương gần đỉnh euphoria.
· Signal: RR percentile 1 năm ngoài ±10% · Trade: contra: RR cực âm + giá ổn định → buy; cực dương + giá stall → reduce.
· Risk: RR cực đoan hợp lệ trong trend mạnh (momentum không đảo) · Data: options surface · Coupling: kèm S40/S60 chung hạ tầng IV.

**S78 — Dealer-gamma regime map (Positioning/Options)** — Hypothesis: dealers long-gamma (pin regime) → range nén, fade extremes; short-gamma (gamma-flip) → vol nổ, chỉ chạy breakout.
· Signal: ước tính net gamma dealer qua OI; spot vs gamma-flip level · Trade: meta-switch giữa module MR và Breakout theo gamma sign.
· Risk: ước tính gamma sai số lớn với dữ liệu public · Data: OI chain daily · Coupling: nền lý thuyết chung cho S23/S46/S76.

**S79 — OI-surge accumulation tell (Positioning)** — Hypothesis: futures OI tăng nhanh + giá đi ngang = tích lũy (absorption); break sau đó có continuation mạnh (Wykoff-flow version).
· Signal: ΔOI 10 ngày > percentile 80 ∧ realized vol < percentile 30 · Trade: straddle-order quanh range nén; trail mạnh khi break.
· Risk: OI tăng cũng là short-build — hướng break quyết định, không đoán trước · Data: GC OI daily · Coupling: volume profile cho level hấp thụ nếu có.

**S80 — Margin-hike cascade short (Positioning)** — Hypothesis: sau vol-spike, sàn tăng margin → forced liquidation tầng tiếp theo; cửa sổ short 1–2 phiên sau thông báo margin-hike.
· Signal: COMEX/CME margin notice + giá đã −1×ATR · Trade: short vào retrace đầu, stop 1×ATR, exit khi OI giảm chậm lại.
· Risk: cascade ngắn; notice đến muộn sau đỉnh sell · Data: exchange notices + OI + giá · Coupling: S20 là mặt trái (sau khi cascade xong).

### Family I — Pattern / Pairs / Stat-arb (S81–S90)

Lý do kinh tế: hai kim loại + hai thành phố + hai lớp thị trường (futures/spot) = nhiều cặp tương quan cao để lai; pattern giá trị khi gắn với level flow thật. Cái chết: band/beta cũ sau structural shift; chi phí execution ăn hết meat mỏng.

**S81 — XAU–XAG cointegration spread (Stat-arb)** — Hypothesis: hai kim loại cointegrated dài hạn; spread OU-reverting với half-life 15–60 ngày → pairs trade.
· Signal: ADF/coint rolling 2 năm; z-spread entry ±2, exit ±0.5 · Trade: long under/short over beta-matched theo vol; stop khi z > 3.5 hoặc half-life break.
· Risk: structural divergence (silver industrial shift 2024–26); squeeze bạc 01/2026 bust band — re-test định kỳ · Data: giá D hai symbol · Coupling: G/S band (S63) không ở extreme lịch sử.

**S82 — Miners-lead-gold timing (Stat-arb)** — Hypothesis: GDX/GDXJ (equity beta vàng) phản ứng earnings-flow nhanh hơn metal — đảo chiều miners dẫn trước vàng 1–3 phiên ở local top/bottom.
· Signal: GDX lập 5-day extreme mới trong khi vàng chưa; hoặc tương quan rolling vỡ · Trade: theo hướng miners chỉ khi vàng confirm break H4 (tránh knife).
· Risk: miners có beta SPX — phải hedge market beta · Data: GDX + SPX + gold · Coupling: leading-indicator cho S3/S20.

**S83 — Triangulated synthetic XAU (Stat-arb)** — Hypothesis: XAUUSD tái tạo gần-đúng từ XAUEUR×EURUSD (và GBP/CHF tương tự); chênh lệch giữa các đường tái tạo là pricing error/microstructure noise — revert nhanh.
· Signal: spread synthetic vs quote > cost-threshold (2× spread) · Trade: arb-direction tại venue có quote lệch; cần size lớn để có meat.
· Risk: gần execution-arb — retail spread ăn hết; demo trước để hiểu pricing · Data: multi-venue quotes · Coupling: nghi ngờ khả thi retail trước khi đầu tư hạ tầng (cùng S84).

**S84 — Futures-lead spot timing (Stat-arb)** — Hypothesis: GC futures phản ứng news trước spot-CFD broker 0.5–3 giây (price-discovery leader) — dùng futures-tick làm trigger vào cho lệnh CFD.
· Signal: futures break M15 level trước spot rõ ràng · Trade: execution-timing enhancement cho mọi ý breakout.
· Risk: latency + spread ăn lợi thế; broker requote · Data: tick futures + CFD quotes song song · Coupling: hạ tầng dùng chung S22/S26.

**S85 — Shanghai–London band trade (Stat-arb)** — Hypothesis: premium SGE có band do cost xuất-nhập (2–3% mỗi hướng) — chạm mép band kích hoạt arbitrage physical → premium revert.
· Signal: premium ngoài band lịch sử 3 năm · Trade: fade premium bằng cặp spot London vs SGE-linked proxy (khó tiếp cận retail — tối thiểu dùng như signal cho spot).
· Risk: chính sách quota TQ; nguồn premium cần tin cậy · Data: SGE/LBMA giá · Coupling: S14 là bản z-score ngắn-hạn; đây là bản structural band.

**S86 — Kalman-beta dynamic residual (Stat-arb)** — Hypothesis: beta vàng–DXY đổi liên tục; Kalman filter beta real-time cho residual hedge chính xác hơn OLS rolling.
· Signal: Kalman state + innovation z · Trade: như S61 nhưng beta động; entry khi innovation z > 2.
· Risk: over-fit filter parameters (Q/R) — out-of-sample nghiêm ngặt · Data: DXY + gold + filter infra · Coupling: thay OLS trong S61/S62.

**S87 — Weekly pin/engulfing tại structural level (Pattern)** — Hypothesis: nến tuần dạng pin/engulfing TẠI level đa tần suất (200WMA, handle tròn, CB-zone) có giá trị phản chiều cao hơn ngẫu nhiên vì stop-flow tập trung nơi đó.
· Signal: candle pattern + level + volume tuần · Trade: enter break candle, stop ngoài wick, target level kế, horizon 1–3 tuần.
· Risk: pattern-subjectivity — code hóa strict · Data: W OHLC + volume · Coupling: khớp macro-regime gate (S91) để chọn hướng.

**S88 — STL seasonal-residual extremes (Stat-arb)** — Hypothesis: tách mùa + trend (STL decomposition), residual weekly cực đoan revert khi không có macro-event.
· Signal: residual percentile ngoài 5% + lịch tuần sạch · Trade: fade residual, stop nửa ATR_W, exit 2 tuần.
· Risk: STL endpoints sensitive — recompute rolling · Data: giá W dài hạn · Coupling: dùng kèm S47/S48 cho bức tranh mùa.

**S89 — Hurst regime meta-switch (Stat-arb)** — Hypothesis: H > 0.5 (persistent) thời điểm module Trend thắng; H < 0.5 (anti-persistent) thời điểm MR thắng — chuyển module theo H đo sliding.
· Signal: Hurst 100 ngày với CI bootstrap · Trade: meta-switch giữa S1 và S11/S15.
· Risk: H noisy ở biên — threshold ±0.05 buffer + hysteresis · Data: giá D · Coupling: xác nhận bằng S97 (correlation-flip meta).

**S90 — CFD-vs-futures basis monitor (Stat-arb)** — Hypothesis: một số broker CFD pricing vàng lệch hệ thống quanh rollover (swap window) — đo basis để tránh bị "chốt" và đôi khi thu lợi.
· Signal: basis CFD−GC(fair) vượt cost ngoài rollover window · Trade: surveillance + tránh execute quanh window; arb khi rõ.
· Risk: chi phí-kiểm-soát chủ yếu, meat nhỏ · Data: hai feeds song song · Coupling: quy trình bắt buộc cho mọi ý multi-day trên tài khoản CFD.

### Family J — Regime-conditioned / Options-flavored (S91–S100)

Lý do kinh tế: bản chất regime-dependent của vàng (mục 1.2) đòi hỏi *meta-layer* chọn đúng họ chiến lược; options cho phép trade phân phối (vol/skew/gap) thay vì chỉ kỳ vọng. Cái chết: meta-parameter fit quá khứ; tail-event ngoài phân phối.

**S91 — Two-factor regime matrix (Regime)** — Hypothesis: trạng thái (TIPS-slope × VIX) 2×2 phân loại hành vi vàng đủ tốt để chọn family: (slope↓,VIX↑)=safe-haven bull; (slope↓,VIX↓)=disinflation bull; (slope↑,VIX↑)=hawkish-stress — vàng hai chiều, ưu tiên vol/short; (slope↑,VIX↓)=bear-trend.
· Signal: slope 20d DFII10 ± threshold ∧ VIX vs 25 · Trade: matrix điều phối modules (long-trend/short/vol/flat) với hysteresis chống nhấp nháy.
· Risk: ma trận thô — biên regime fuzzy · Data: DFII10 + VIX · Coupling: SEP-2026 = ô (slope↑,VIX↑) — lý giải gold giảm giữa chiến tranh; module đúng lúc này là vol/short, không phải safe-haven long.

**S92 — GARCH vol-target overlay (Regime/Options)** — Hypothesis: forecast vol (GJR-GARCH) dự đoán clustering chính xác hơn realized trailing — sizing theo forecast giảm drawdown sau shock.
· Signal: σ̂ t+1 từ model fit rolling · Trade: overlay size = target ÷ σ̂ cho mọi module directional.
· Risk: model risk khi innovation ngoài phân phối (tuần 28/09/2026) · Data: returns D + model infra · Coupling: sau innovation > 3σ set floor cho σ̂ vài ngày.

**S93 — Weekend gap-insurance straddle (Options)** — Hypothesis: tuần geo nóng (Hormuz-class: blockade, đàm phán bế tắc, nghỉ lễ TQ dài) xác suất gap Sunday cao — mua OTM strangle Friday khi headline-risk index cao mà IV chưa phản ánh đủ.
· Signal: geo-risk score (headline count + oil vol) > percentile 80 ∧ IV term chưa steep · Trade: long strangle OTM ~1.5% hai phía, hold qua weekend, sell Monday.
· Risk: premium ăn thịt nếu gap không đến — cần hit-rate ~ >35% · Data: news classification + options IV · Coupling: xác nhận qua Brent Friday close mạnh bất thường (weekend-war-risk bid).

**S94 — FOMC time-spread calendar trade (Options)** — Hypothesis: vol trước FOMC đắt hơn sau; short front-week/long next-week (time spread) thu diff khi event passé mà không bet direction.
· Signal: event tuần này + term structure steep · Trade: calendar spread delta-neutral, unwind sau event.
· Risk: hike-shock lớn chuyển vol toàn đường cong — long-leg đủ tenor · Data: options chain GC · Coupling: chỉ khi tuần sau không có event lớn (double-event làm spread ngược).

**S95 — Skew harvest in calm regimes (Options)** — Hypothesis: trong ô (slope↓,VIX↓) hoặc range-pin, gold skew rẻ lại — bán strangle/RR có capital-efficient edge.
· Signal: RR percentile < 30 ∧ S78 báo pin-regime · Trade: short strangle 1 tháng OTM 1.5×σ, delta-hedge tuần 2 lần, stop gamma khi spot ngoài break-even 70%.
· Risk: tail — size nhỏ + defined-risk; cấm khi geo-score cao (S93 flag) · Data: options surface + gamma infra · Coupling: đối xứng S40 (mua khi đắt, bán khi rẻ).

**S96 — CB-zone defense reversal (Regime/Options)** — Hypothesis: vùng $4,000–4,100 có người mua price-insensitive — lần từ chối đầu (long lower-wick M15/H1 + không close dưới) tại zone là long risk/reward cao.
· Signal: zone map (CB historical accumulation ± 1×ATR) + rejection pattern + TIPS không thêm spike hôm đó · Trade: long tight stop dưới wick, target 2–3×ATR hoặc trailing.
· Risk: CB pause tháng đó (data trễ) — theo dõi WGC monthly; close D dưới zone − 2×ATR = thesis chết, thoát · Data: giá intraday + WGC zone calibrate (mức zone chính xác cần kiểm chứng) · Coupling: S31/S75 cung cấp cùng trade ở khung lớn hơn.

**S97 — Correlation-flip meta-indicator (Regime)** — Hypothesis: dấu của rolling-corr(gold, TIPS-yield) là phát hiện regime sớm: âm = normal regime (yield↑ gold↓); tiến về 0/dương = structural bid (CB/debasement) chi phối — đổi bộ strategy.
· Signal: 60d Spearman corr với band ±0.3 · Trade: meta-switch: âm mạnh → ưa TIPS-residual & trend; 0/dương → ưa structural/floor & sell-vol.
· Risk: flip muộn; window-selection bias · Data: DFII10 + gold · Coupling: nền tảng cho S61/S89 — "đồng hồ regime" tổng.

**S98 — Stagflation barbell (Regime)** — Hypothesis: tín hiệu stagflation (Brent-shock + PMI<50 + payroll yếu) làm cả bond lẫn equity xấu, vàng + TIPS (real duration) cùng thắng — barbell long-gold/long-TIPS hưởng hai kênh.
· Signal: bộ ba tín hiệu đồng thời · Trade: 50/50 gold + long TIPS futures, rebalance tuần, thoát khi PMI>50 hoặc Brent z<1.
· Risk: TIPS chịu thêm hike (nominal crush) — chính regime 2026: barbell thua chân TIPS; validate kỹ · Data: Brent + PMI + TIPS futures · Coupling: bản hedge đầy đủ của S64/S65.

**S99 — Anti-martingale pullback add-on (Regime)** — Hypothesis: trong trend đã verify, add vào vị thế CHỈ sau pullback nông (<1×ATR), không bao giờ sau sâu — nâng average mà không averaging-down vào collapse.
· Signal: pullback depth bucket + trend regime còn nguyên (200DMA slope) · Trade: tối đa 2 nấc add, mỗi nấc 50% size gốc, stop dời theo trailing chung.
· Risk: early-trend chỉ 1 entry — chấp nhận · Data: chung module trend · Coupling: đi kèm S10 làm kill-switch.

**S100 — Crisis-alpha sleeve với real-yield kill-switch (Regime)** — Hypothesis: vàng là crisis-hedge tốt nhất chỉ khi rates không spike (giai đoạn sau 2008; SVB 3/2023); sleeve được kích hoạt bởi composite-stress (VIX>28 + credit-spread rộng + DXY momentum dương) nhưng TẮT khi DFII10 slope 5d > +5bp — hợp nhất bài học Sep-2026 vào allocation.
· Signal: stress index composite ∧ kill-switch TIPS · Trade: sleeve 10–20% NAV long gold + tail options (S40), exit theo composite normalize.
· Risk: stress-index design là meta-parameter — validate từng thành phần · Data: VIX + HY-spread + DXY + DFII10 · Coupling: là "chiến lược tổng kết" — mọi ý trên phải nằm trong khung regime này để tránh cái bẫy safe-haven đã chết trong Q3/2026.

---

## 3. Tổng hợp cho symbol

### 3.1 Top-10 ideas (xếp theo EV × khả năng verify)

| # | Ý | Vì sao chọn |
|---|---|---|
| 1 | **S91 — Two-factor regime matrix** | Sep-2026 là bằng chứng sống: gold -26% giữa chiến tranh vì ô (TIPS↑, VIX↑). Mọi ý khác cần khung này để không chết oan. Data rẻ (FRED + CBOE), verify được ngay bằng lịch sử regime. |
| 2 | **S1 — Donchian-CTA + gate S2** | Core trend của symbol có clustering thuộc nhóm mạnh nhất universe; gate real-yield-slope lọc phần lớn drawdown kiểu 2026. Chuẩn CTA, dễ benchmark. |
| 3 | **S61 — TIPS-residual regression** | Biến "vàng đắt/rẻ so với macro" thành con số; tại thời điểm này (TIPS 2.85%, gold -26%) residual trả lời câu hỏi mở: CB-floor có đang kẹp không. |
| 4 | **S64 — Oil-shock inversion pair** | Divergence verify ngay 28/09 (Brent +3.6% vs gold -3.25%); pair không cần directional view, khai thác đúng regime hiện tại. |
| 5 | **S31 — CB-buying floor ladder** | Người mua price-insensitive là edge structural duy nhất không thể copy bằng indicator; zone hiện tại ($4,000–4,100) đang được test — phải verify zone bằng dữ liệu WGC thật trước khi tin. |
| 6 | **S15 — Real-yield shock snapback** | MR duy nhất có lý do kinh tế vững trong downtrend hiện tại (rates nghỉ → oversold bounce); exit-before-event là kỷ luật sạch. |
| 7 | **S71/S75 — COT extremes + CB alignment** | Dữ liệu miễn phí (CFTC) + dữ liệu structural (WGC); cấu hình "floor + fuel" là setup xác suất cao hiếm gặp. |
| 8 | **S57 — Geo risk-premium decay** | Biến nhược điểm của lane (headline noise) thành mô hình decay verify được bằng event-study; gate TIPS bắt buộc — chính là bài học 25–28/09. |
| 9 | **S93 — Weekend gap insurance** | Tuần Hormuz-type mà CFD không có gì chống gap — strangle Friday là cấu trúc duy nhất có hệ thống; IV có thể còn rẻ so với rủi ro thật. |
| 10 | **S100 — Crisis-alpha sleeve + kill-switch** | Đóng gói toàn bộ bài học regime vào một allocation rule — là "spine" để ghép portfolio với các lane FX khác. |

### 3.2 Bẫy overfitting đặc thù khi backtest XAUUSD

1. **Regime-dominance trong sample**: mọi backtest 2020–2026 gồm ba cấu trúc khác nhau (zero-rate 2020–21; CB-bid + debasement 2022–25; hike-shock 2026). Một tham số fit cả sample = trung bình của ba câu chuyện, không thuộc câu chuyện nào. Stratify theo S91 trước khi evaluate module nào.
2. **Beta real-yield bất ổn**: quan hệ ΔTIPS→gold đổi hệ số theo regime; đừng fit beta cố định — dùng rolling/Kalman (S86) và kiểm định stability, cắt khi R² collapse.
3. **Contract-roll & swap**: backtest trên GC futures phải roll-adjust; backtest trên spot CFD phải cộng swap đêm (long âm) và weekend-hold cost. Không có hai mục này thì mọi ý swing/event đều PnL ảo.
4. **Gap & bar-granularity**: các ngày 8:30 ET (CPI/NFP) — bar M15/D chứa spike; fill theo OHLC tạo phantom fill. Dùng M1/M5 hoặc loại cửa sổ ±2 phút quanh release.
5. **Data-source mixing**: fix LBMA ≠ COMEX GC ≠ CFD broker. Chọn một chuẩn (đề nghị GC continuous roll-adjusted làm primary; CFD chỉ cho nghiên cứu microstructure).
6. **Round-number & CB-zone lookahead**: biết $4,000 quan trọng *ngày nay* không có nghĩa nó quan trọng năm 2015 — mọi level-based rule phải tính level từ dữ liệu available tại thời điểm đó.
7. **G/S tham số cũ**: band calibrate giai đoạn G/S 80–110 vô dụng ở 67.9 — walk-forward bắt buộc cho mọi ý pairs kim loại.
8. **Sự kiện geo không lặp lại được**: event-study Hormuz-2026 n=1; không generalize decay-constant (τ) từ một chuỗi headline.
9. **DST/session-time**: "London open" đổi giờ UTC hai lần/năm — hardcode giờ local làm lệch toàn bộ ý session (S41–S50).
10. **Dữ liệu CB/ETF revised**: WGC và GLD holdings có revision — point-in-time snapshot phải lưu khi chạy live, không tái tạo sau bằng data hiện tại.
11. **Silver beta cực端正 không đối xứng**: beta XAG lên ~1.5 nhưng xuống ~2.0 trong selloff — các ý pair phải mô hình beta phi tuyến, không một con số.
12. **Broker-specific swap/quote**: cùng strategy, hai broker CFD cho kết quả khác nhau quanh rollover — backtest phải pin tên broker/data feed như một tham số.

### 3.3 MUST-WATCH weekly macro checklist (cho XAUUSD)

Chốt mỗi Sunday 20:00 UTC / Monday 06:00 UTC trước open:

1. **DFII10 (10Y TIPS)**: mức + Δ5d + slope 20d — driver số 1 (tuần này: 2.85%, +23bp, slope dương = headwind).
2. **10Y nominal & breakeven**: tách story real vs inflation; breakeven thấp + nominal cao = real-crush regime (xấu cho vàng).
3. **Fed path**: xác suất hike kỳ họp tới + lịch Fedspeak tuần tới (tuần này: ~70% Oct, ~95% Dec — cực hawkish).
4. **DXY**: mức + 20d momentum (mức chính xác hiện tại cần kiểm chứng — đang ở vùng mạnh).
5. **USDJPY & rủi ro can thiệp**: vùng 152.9–154.5 là ngưỡng can thiệp Nhật–Mỹ; spill qua DXY/USD.
6. **WGC CB statistics (tháng) + IMF IFS (trễ 2 tháng)**: tonnage net trailing 3–6 tháng; cập nhật CB zone.
7. **GLD (và tổng ETF) weekly Δ holdings**: confirm/fade trend.
8. **COT (Friday 15:30 ET)**: MM net-length percentile + commercial percentile.
9. **Brent + Hormuz status**: mức giá + headline đàm phán/blockade (tuần này: $108.07; Iran đề nghị 25/09 bị từ chối 27/09 — geo nóng mà gold giảm = xác nhận regime S91).
10. **SGE premium & lease/EFP (nếu có nguồn)**: physical bid + funding stress.
11. **Options**: strike OI lớn nhất tuần, 25Δ RR percentile, gamma-flip level (nếu có feed).
12. **Lịch tuần**: FOMC/CPI/NFP/auctions/OPEX — quyết định ý nào được bật/tắt (event-window rules của từng ý).

### 3.4 Trạng thái kiểm chứng & các mục còn mở

**Đã verify 2026-09-28** (nguồn: FRED DFII10; federalreserve.gov press release 16/09; Kitco gold 28/09; TradingEconomics Brent/WTI/silver 28/09):

- Gold spot $4,144.80/4,146.80, -3.25% ngày, range 4,140.30–4,279.90; ATH $5,589.38 (28/01/2026); -26% từ đỉnh; $4,300 đã vỡ trong tuần 25/09.
- 10Y TIPS real yield 2.85% (24/09), +23bp trong tuần; 10Y nominal ~5.2% (headline Kitco — mức chính xác cần kiểm chứng).
- FOMC 16/09/2026: hike 25bp lên 3.75–4.00%, biểu quyết 12–0, "inflation remains elevated", "will deliver price stability"; thị trường ~70% hike Oct, ~95% Dec (TradingEconomics).
- Brent $108.07 (+3.59% ngày, +61% y/y), WTI $95.65; Hormuz: MoU 6/2026 sụp → chiến sự mùa hè → blockade cảng Iran; 25/09 Iran đề nghị mở lại Hormuz; 27/09 Trump từ chối; 28/09 Brent >$106.
- Silver $61.12 (-5% ngày, -8% tháng, +30% y/y), ATH $121.64 (01/2026); G/S = 67.9.

**(cần kiểm chứng)**:

- Mức DXY chính xác (fetch DXY thất bại 28/09).
- Tonnage CB mua 2025–2026 + danh sách buyer (trang WGC chỉ có landing; cần file xlsx GDT/Q2-2026 hoặc Central Bank Survey 2026).
- Holdings ETF hiện tại & hướng flow 2026.
- Ranh giới chính xác "CB zone" $4,000–4,100 (hiện là ước tính thị trường).
- SGE premium & lease rate hiện tại (cần feed thương mại).
- Chi tiết can thiệp Nhật–Mỹ Jul–Aug/2026 và vùng USDJPY 152.9–154.5 (do lane FX cung cấp; WebSearch rate-limit nên chưa verify độc lập — đã có làm rõ trong mục 1.1/3.4).

### 3.5 Phụ lục: nguồn data dự kiến cho giai đoạn kiểm định (chỉ ghi tên, không download ở lane này)

| Data | Nguồn dự kiến | Dùng cho |
|---|---|---|
| 10Y TIPS real yield (DFII10) | FRED | S2, S15, S35, S61, S91, S97, S100 |
| DXY & các cặp FX | broker feed / Stooq | S19, S62, S66, S67, S86 |
| Vàng spot roll-adjusted (chuẩn primary) | GC continuous (qiib-style adj) | hầu hết ý price-based |
| CFD quote song song | broker | S83, S84, S90 |
| Brent/WTI/NATGAS | broker / EIA | S64, S70, S98 |
| COT CFTC | cftc.gov weekly | S20, S71, S72, S75 |
| GLD/ETF holdings | sponsor daily | S34, S73, S74 |
| WGC CB statistics / GDT | gold.org (xlsx) | S9, S31, S58, S75, S96 |
| SGE premium | SGE/LBMA so sánh | S14, S48, S85 |
| Options IV/OI COMEX | feed thương mại | S40, S60, S76, S77, S78, S93–S95 |
| Lịch event (FOMC/CPI/NFP/auction) | official calendars | toàn bộ Family E/F |

Ghi chú: danh mục này là kế hoạch kiểm định, không phải tuyên bố đã có data. Mọi verify sau này phải đi qua quy trình cycle/gate của workspace trước khi coi là bằng chứng.

*Hết file. Toàn bộ 100 ý là hypothesis cần kiểm định theo quy trình evidence-first của workspace; không có ý nào được treated như PASS; missing evidence = NOT_RUN.*
