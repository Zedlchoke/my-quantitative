# GBPUSD — Deep Dive & 100 Strategy Ideas

Chương trình: FOREX-UNIFIED-STRATEGY-BRAINSTORM-V1 · Lane: GBPUSD · Ngày: 2026-09-28
Loại tài liệu: knowledge-only brainstorm (không backtest, không Python, không data download).
Mọi con số "typical/điển hình" là kinh nghiệm hoặc tài liệu chuẩn — **phải đo lại bằng dữ liệu thực** trước khi vào phase measurement; mọi hypothesis ở Section 2 là thiết kế cần kiểm định, không phải kết quả.
Các sự kiện vĩ mô mốc Sep-2026 đã verify qua nguồn chính thống (BoE, Federal Reserve, Reuters/WSJ/FT) — xem footer "Nguồn verify".

---

## 1. Bản chất instrument

### 1.1 Microstructure & sessions

**Định danh và quy ước giá**
- GBPUSD ("Cable", tên lịch sử từ dây điện xuyên Đại Tây Dương thế kỷ 19) = số USD cho 1 GBP. Pip = 0.0001 (chữ số thập phân thứ 4); "pipette"/tick = 0.00001 với pricing 5 chữ số. Quote chuẩn: e.g. 1.34862/1.34878.
- Giá trị/pip/standard lot (100,000 GBP) = 10 USD; mini lot (10k) = 1 USD/pip. P&L luôn bằng USD (quote currency) — không có currency-of-account mismatch như cross EURGBP.
- Tick size thực tế trên venue chính (EBS/LMAX/Currenex/retail aggregator) ~0.1–0.5 pip median; tick frequency thấp hơn EURUSD — depth Cable mỏng hơn EURUSD ước tính 30–50% theo kinh nghiệm desk (cần kiểm chứng bằng tick data khi thu thập).

**Thông số thực thi (khởi điểm thiết kế — chuẩn hóa lại theo broker cuối)**
| Hạng mục | Giá trị điển hình | Ghi chú |
|---|---|---|
| Spread retail all-in | 0.8–1.5 pip (raw + commission) / 1.0–2.0 pip (markup) | Nở 1.5–3× giờ châu Á và quanh event 07:00/12:00 London |
| Spread institutional | ~0.2–0.5 pip giữa phiên London/NY | Đo trên feed thật nếu dùng cho execution-model |
| Commission | 3–7 USD/lot/side | retail ECN |
| Session giao dịch | Sun 22:00 UTC → Fri 22:00 UTC | 24/5 |
| Fixing | WM/Reuters 16:00 London hằng ngày | Flow fixing tuần/month-end lớn — mục 1.1 Fixing |
| Rollover | 22:00 UTC, triple swap Wednesday | Nở spread 5–30 pip 21:55–22:15 |
| Order types đủ dùng | market/limit/stop/OCO/bracket | Event bracket cần broker cho stop-limit tại spike |

**Thanh khoản theo phiên (giờ UTC; lưu ý BST/GMT đổi khác US DST — xem bẫy 3.2.1)**
- Sydney/Asian (22:00–06:00): depth mỏng nhất cho GBP; market-maker UK vắng; hành vi mean-reverting trong range châu Á; gap-risk với tin regional.
- Pre-London (06:00–07:00): ONS releases 07:00 London (CPI/GDP/earnings/retail) rơi vào lúc liquidity chưa đầy — cấu trúc spike-then-revert phổ biến hơn US data (đây là điểm khác biệt then chốt cho event design).
- London (07:00–16:30): UK price discovery; Cable thường có **directional move lớn nhất trong ngày ở 07:00–11:00** (UK data 07:00/09:30, London fix flow, dealer inventory reset). 08:00 London open là mốc "ignition" kinh điển.
- Overlap London–NY (13:30–16:30): thanh khoản sâu nhất; US data 13:30 (CPI/NFP), equity open 14:30; vol đỉnh ngày.
- NY late (17:00–21:00): drift/liquidation; Friday 19:00+ hay có reversal profit-taking.
- Rollover 22:00 UTC: không vào/lật vị thế 21:55–22:15.

**Volatility profile (điển hình — bắt buộc đo lại khi có data)**
- Daily ATR: ~60–110 pips regime bình thường; regime stress 120–200+ (2022 crisis, Sep-2026 gilt stress). Annualized realized vol điển hình 8–10% vs EURUSD 7–8% → **Cable vol cao hơn EURUSD ~15–25% dù correlation ~0.7–0.9** — idiosyncratic vol là đặc sản Cable, ảnh hưởng trực tiếp tới stop-sizing và expected-cost model.
- Hour-of-day: đỉnh 13:30–15:00 (US data + overlap); đỉnh phụ 07:00–09:00 (UK data + London open); đáy 22:00–05:00.
- Day-of-week: Tue–Thu vol & trend-reliability cao nhất; Monday thường positioning/range; Friday MR-afternoon bias + weekend gap risk.
- Event spikes (điển hình lịch sử, cần cập nhật bằng data): MPC 12:00 London hay move 50–120 pip trong 60 giây đầu; UK CPI 07:00 hay 30–80 pip phút đầu; tail events: 2019-01-03 Asian flash, 2022-09-26 low 1.0350.
- Weekend gap: median nhỏ (0–15 pip Monday open vs Friday close) nhưng tail nặng political/fiscal weekend news: 50–150+ pip (2019 Brexit votes, 2022 fiscal leak).

**Rollover/swap & cost**
- Swap qua đêm theo chênh SONIA (GBP) vs SOFR (USD) + bank markup. Trạng thái Sep-2026 (verified rates): BoE 3.75% vs Fed 3.75–4.00% → **long GBPUSD gánh carry âm nhẹ** (mid ≈ −12 đến −25bp/annum trước markup; broker retail hay tính thêm 30–50% — cần kiểm chứng theo broker cụ thể).
- Wednesday triple swap — daily-rebalance strategies phải tính đúng cost này.
- Weekend holding = 2 ngày không-mark nhưng mang gap risk: xem như một loại "cost ẩn" cho các strategy giữ qua Friday (S99).

**Fixing windows**
- WM/R 16:00 London hằng ngày: order-flow replay cuối phiên; tháng cuối flow lớn.
- Trước fixing 15–30 phút hay có acceleration hướng flow kỳ vọng — vừa là rủi ro cho counter-flow intraday, vừa là edge cho S43.

### 1.2 Điểm ĐẶC BIỆT riêng GBPUSD (so với EURUSD và các major)

1. **Vol idiosyncratic cao**: correlation với EURUSD cao nhưng "vol dư" lớn hơn hẳn — nguồn: UK policy/fiscal shocks + retail flow noise + GBP chiếm tỷ trọng lớn trong cross-flow. Hệ quả: không port strategy từ EURUSD theo threshold pip; phải re-scale theo vol-unit (bẫy 3.2.11).
2. **Kênh truyền dẫn fiscal/gilt riêng biệt — không major nào có tương đương**: UK là major duy nhất mà *định chế tài khóa* định giá trực tiếp vào FX qua gilt. Precedent 2022 mini-budget (23/09/2022): 30Y gilt +150bp trong ngày, LDI margin spiral, Cable flash xuống 1.0350 (low kỷ lục), BoE can thiệp mua dài hạn 28/09/2022. **Sep-2026 đang lặp lại biến thể kênh này (đã verify)**: gilt 10Y 5.378% ngày 10/09 (cao nhất từ 07/2007); 30Y đỉnh 5.921% ngày 02/09 (cao nhất 1998); auction 30Y 08/09 trả 5.82% (đắt nhất 1998, demand vẫn tốt); US 10Y vượt 5%; House of Lords Library cảnh báo fiscal headroom xói mòn; El-Erian gọi gilt "high beta".
3. **"Mover" của phiên London**: single-session trend-day rõ rệt hơn EURUSD (dealer flow + stop-runs). Cable nổi tiếng "saw-tooth": quét stop hai đầu range trước khi đi direction thật.
4. **Data Anh đặc thù, mật độ cao, giờ phát hành lệch chuẩn**: monthly GDP (hiếm trong G10), CPI + services CPI (anchor của MPC), average earnings incl bonus (wage anchor), PMI flash 09:30 — phần lớn ONS release **07:00 London**, trước khi London đầy liquidity → cấu trúc phản ứng khác US data (fade nhiều hơn).
5. **Chuỗi chính trị**: elections, Budget/fiscal-rule disputes, thay đổi PM/Chancellor, rating actions — unscheduled Cable movers kinh điển (2016 referendum là event rủi ro lớn nhất thế hệ).
6. **GBP là "half-risk currency"**: beta risk-on/off nằm giữa EUR và AUD/NZD — hưởng risk-on, bị đánh trong risk-off nhiều hơn EURUSD một chút trung bình.
7. **Current account deficit lịch sử** → nhạy funding/global dollar liquidity; dollar-squeeze làm Cable đau hơn EURUSD.
8. **GBP chiếm 11.9% DXY** → DXY một phần là *hệ quả* của Cable; lấy DXY làm USD-filter bị circularity — dùng EURUSD làm USD proxy sạch hơn.

### 1.3 Tin tức/sự kiện ảnh hưởng

**Scheduled (giờ London)**
| Sự kiện | Giờ | Tần suất | Transmission channel |
|---|---|---|---|
| BoE MPC decision + minutes | 12:00 (quarter MPR + presser 12:30) | 8/năm, Thứ Năm | Rate-path kỳ vọng → SONIA/OIS → carry & flow; vote split & minutes language là second-order driver |
| UK CPI (headline + services) | 07:00 | tháng | Reaction function BoE (services CPI là anchor) → path repricing → spot |
| Average earnings (incl bonus) | 07:00 | tháng | Wage-inflation channel → BoE path |
| PMI flash mfg/services | 09:30 | tháng | Growth-nowcast → rate path + risk sentiment |
| Monthly GDP + IoS | 07:00 | tháng | Growth surprise → rate path (đặc thù UK) |
| Retail sales, claimant count/payrolls, LFS | 07:00/09:30 | tháng | Labor channel — UK payrolls series mới, vol dữ liệu cao (S60) |
| Fiscal events: Budget / Autumn Statement + OBR | ~12:30 | 1–2/năm | Gilt supply + credibility → gilt yields → GBP risk premium (kênh 2022). Ngày autumn 2026: (cần kiểm chứng) |
| Gilt auctions (DMO) | sáng | hàng tuần | Long-end demand test → fiscal credibility signal (S77) |
| US: NFP (Fri 13:30 UTC), CPI (13:30), FOMC (Wed 19:00 UTC) | — | — | USD-common factor, chiếm phần lớn phương sai Cable ngày thường (ước tính — cần đo) |

**Sep-2026 sequencing vàng (verified)**: UK CPI sáng **16/09** (3.1% YoY, lên từ 2.9% tháng 7) → Fed hike **16/09** (3.75–4.00%) → BoE hold **17/09** (3.75%). Chuỗi "CPI → hawkish-Fed → hold-BoE" là template event-archetype cho lane; lặp lại cấu trúc tương tự mỗi quý có MPR.

**Unscheduled**
- Political shocks: resignation/khủng hoảng PM–Chancellor, election surprise, leadership challenge (channel: gilt → GBP).
- Gilt flash moves / LDI-type margin spiral / BoE intervention statements (channel: rate vol + liquidity).
- Credit rating outlook/actions trên UK sovereign (S&P/Moody's/Fitch).
- Asian-hours thin-liquidity dislocations (2019-01-03 template).
- Central bank speak giữa kỳ: Governor testimony, Treasury Committee, Fed speakers (USD-side).

### 1.4 Thông số ảnh hưởng (drivers, theo thứ tự tầm quan trọng thực dụng)

1. **BoE–Fed policy differential & path momentum** — trạng thái verified Sep-2026: Fed **3.75–4.00%** sau hike 25bp ngày **16/09/2026** (vote 12–0, ngôn ngữ hawkish "The Committee will deliver price stability"); BoE **3.75%** hold từ **18/12/2025**, giữ nguyên qua 6 họp 2025–2026 (gần nhất 17/09; kế tiếp **05/11/2026**). → Differential momentum nghiêng USD; nhưng UK CPI 3.1% tăng trở lại + BoE tự dự báo CPI ~3.2% Oct–Nov → thị trường bắt đầu price BoE-hike risk. Kết luận thiết kế: strategy differential phải theo **momentum/slope của differential**, không theo level tĩnh.
2. **Gilt yields 2Y/10Y/30Y** — 2Y = BoE path (clean); 10Y/30Y = growth + fiscal premium (kênh 2022). Phân biệt then chốt: 10Y tăng vì *growth/BoE-hawkish* (2Y cùng tăng, GBP thường LÊN) vs vì *fiscal risk* (30Y-led steepening, GBP XUỐNG). Sep-2026 là loại thứ hai trộn lẫn (cần kiểm chứng phân rã từng ngày bằng data).
3. **USD-common factor** — dùng EURUSD làm proxy sạch (DXY circular, mục 1.2.8).
4. **Risk sentiment** — S&P/VIX/gold; GBP half-risk beta.
5. **EURGBP flows** — đẳng thức nền tảng **EURUSD = GBPUSD × EURGBP**; EURGBP là instrument GBP-sạch nhất. Mọi nhận định "GBP mạnh/yếu" phải phân rã USD-common vs GBP-idio (S63).
6. **Rate-expectation instruments** — OIS/SONIA futures, 2Y swap differential, gilt–bund 10Y, gilt–Treasury 10Y, cross-currency basis.

### 1.5 Correlation map (12 symbol)

Giá trị là **daily-return correlation điển hình theo tài liệu/kinh nghiệm** — chỉ để thiết kế hypothesis; **bắt buộc đo lại** (rolling 60d/250d) trong phase measurement. Correlation đổi nhanh quanh fiscal events.

| Symbol | Corr điển hình | Cơ chế | Bối cảnh breakdown |
|---|---|---|---|
| EURUSD | +0.70 … +0.88 | anti-USD common factor dominant | UK-specific shock: corr rơi nhanh — 2022-09 Cable −5% khi EURUSD −2%; Sep-2026 gilt stress tương tự nhẹ hơn |
| AUDUSD | +0.55 … +0.75 | risk beta + anti-USD | commodity/China shock tách rời; risk-off AUD rơi nhanh hơn |
| NZDUSD | +0.45 … +0.65 | như AUD, yếu hơn | RBNZ divergence episodes |
| USDCAD | −0.40 … −0.60 | CAD-quoted ngược anti-USD | Brent supply shock: CAD mạnh, GBP không hưởng → corr âm sâu; UK fiscal shock: Cable rơi, USDCAD không phản ứng → corr về 0 |
| USDJPY | −0.20 … +0.30 (bất ổn nhất) | risk-on: cùng tăng (dương); US-rate-shock: ngược (âm) | regime-dependent — dùng qua risk-index tổng hợp (S86) |
| USDCHF | −0.45 … −0.65 | CHF anti-USD + haven | risk crisis: CHF mạnh vượt USD-factor, quan hệ nhiễu |
| XAUUSD | +0.15 … +0.35 | anti-USD common, yếu | risk-off gold rally cùng Cable fall → dấu lật |
| XAGUSD | +0.25 … +0.45 | như gold + industrial | silver squeeze riêng |
| BRENT | +0.05 … +0.25 (yếu) | UK net oil importer → supply-shock oil↑ nhẹ GBP-âm | demand-driven oil↑ (growth) dấu dương; phải phân loại supply vs demand |
| WTI | +0.00 … +0.20 | tương tự, noise hơn | WTI-specific (Cushing/storage) không chạm GBP |
| NATGAS | ~0.00 | Henry Hub không chạm UK | European gas shock (TTF 2021–22) GBP-negative episodic — theo TTF, không phải NATGAS |

Hướng dẫn ước lượng khi vào phase measurement: rolling 60d và 250d song song; tách subsample theo flag S96 (fiscal-stress on/off) và theo tuần có/không có BoE+Fed event; báo cáo cả median lẫn IQR — không chỉ một con số điểm.

### 1.6 Case study stress lịch sử (để thiết kế regime test)

| Episode | Diễn biến chính | Bài học cho strategy |
|---|---|---|
| 2016-06 Brexit referendum | Cable −8%+ trong một đêm, gap xuyên support lịch sử | Tail-risk của overnight positions; MR chết; gap model phải có political calendar input |
| 2019-01-03 flash | Asian thin-liquidity spike xuống ~1.20 rồi hồi trong phút | Stop-loss phải là stop-market thực thi được; backtest fill assumption phải chịu slippage tail |
| 2020-03 COVID dollar squeeze | GBP rơi cùng mọi asset; dollar-liquidity dominates idio | Current-account channel (1.2.7); hedge bằng USD-long basket |
| 2022-09 mini-budget | Fiscal statement → gilt 30Y +150bp/ngày → LDI spiral → Cable low 1.0350 (23–26/09) → BoE can thiệp 28/09 bounce | Template "fiscal dominance": gilt-led trend nhiều ngày; fade từng đợt = tự sát; tín hiệu thoát = BoE intervention headline |
| Sep-2026 gilt stress (verified) | 10Y 5.378% (10/09, đỉnh 19 năm); 30Y 5.921% (02/09, đỉnh 1998); auction 5.82% (08/09); GBPUSD ~1.3486 (15/09) chịu áp lực nhưng không crash kiểu 2022 | Biến thể "slow-motion": stress dài, auction vẫn hấp thụ được — phân biệt "crisis" vs "premium cao" là input sống còn cho flag S96 |

### 1.7 Bối cảnh nào các họ strategy hay CHẾT trên GBPUSD (note trung thực)

- **Trend-following chết trong "BoE-hold range regime"** — khi hai bank cùng đứng yên và không fiscal stress (phần lớn 2025–2026), Cable chop 80–120 pip/tuần; Donchian-type bị whipsaw chết bởi spread. Gate bằng differential momentum + vol percentile.
- **Mean-reversion chết trong fiscal-stress trend** (2022, Sep-2026): fading đợt bán gilt-led bán GBP mất tài khoản — MR chỉ chạy khi flag S96 TẮT.
- **Event-straddle chết khi decision in-line nhưng guidance dịch**: 12:00 hold đúng kỳ vọng nhưng minutes/vote-shift hawkish → bracket hai phía bị cắt. Cần filter "clean decision" (S94).
- **Session-breakout chết quanh holiday liquidity** (August, nửa cuối December, UK bank holiday lệch US holiday): expansion giả, retest fail.
- **Carry chết bởi reversal**: Sep-2026 long-Cable carry đã âm nhẹ và differential momentum chống lại — carry-family cần momentum veto (S34/S40).
- **Stat-arb vs EURUSD chết khi UK idio driver mạnh**: beta-dislocation kéo dài nhiều ngày trong fiscal episode — z-score không có lực hội tụ khi catalyst còn sống.
- **Execution-sensitive intraday chết bởi spread tại 07:00/12:00 London**: stop-entry tại price tồi trong spike-spread — backtest phải mô phỏng spread widening, không dùng static spread.

### 1.8 Data requirements theo family (chuẩn bị cho phase measurement)

| Family | Data tối thiểu | Data tăng cấp |
|---|---|---|
| A Trend/Momentum | daily + H4 OHLC | H1, session labels |
| B Mean-reversion | M15 + H1, Asian-range builder | M5, tick cho spike study |
| C Breakout/Vol | M5/M15 + event calendar | M1 quanh event, volume |
| D Carry/Rates | daily close + swap points + 2Y yields lịch sử | OIS curve daily/intraday, forward points multi-tenor |
| E Session/Seasonality | M15 + calendar (holiday 2 nước, fix dates) | tick volume, DST-aware session library |
| F Event/Data | release-time-accurate calendar + consensus point-in-time + M1 | minutes text (NLP), gilt intraday |
| G Cross-asset | daily 12-symbol universe | gilt futures intraday, FTSE intraday, 2Y intraday |
| H Positioning | COT GBP + RR 25Δ lịch sử | OI futures, retail sentiment feed, basis quotes |
| I Stat-arb | M1 đồng bộ 3 cặp GBPUSD/EURUSD/EURGBP | tick 3 cặp, G10 daily |
| J Regime/Options | RV series + IV 1W/1M + gilt daily | vol surface, basis, auction results |

---

## 2. 100 Strategy Ideas

Quy ước template: **S<n> — tên (family)**, rồi Hypothesis (lý do kinh tế) · Signal (chỉ báo/ngưỡng/timeframe) · Trade (entry/exit/stop sketch) · Risk (gì giết strategy) · Data (dữ liệu cần) · Coupling (yếu tố ngoài cùng chiều/gate). Mọi ngưỡng số là khởi điểm thiết kế, chưa tối ưu.

### Family A — Trend / Momentum (S1–S10)

**S1 — Donchian Daily Trend-Follow (Trend/Momentum)**
- Hypothesis: Cable có xu hướng đa tuần khi policy differential có hướng; TF thu phần tail moves · Signal: close qua Donchian-20 ngày; ATR(14) là unit risk · Trade: vào theo close; stop trailing 2.5×ATR; không target cứng.
- Risk: chop regime khi cả BoE & Fed hold (nửa 2025–2026) · Data: daily OHLC · Coupling: chỉ bật khi 2Y swap differential slope-20d cùng hướng.

**S2 — London-Open Direction Persistence (Trend/Momentum)**
- Hypothesis: London là price discovery chính của GBP; hướng 07:00–09:00 dự báo phần còn lại ngày London · Signal: sign return 07:00–09:00 London, lọc |ret| > 0.3×ATR-daily để bỏ ngày flat · Trade: 09:30 vào cùng hướng; stop ngoài range 07:00–09:00; exit 16:00.
- Risk: US-data 13:30 đảo chiều · Data: M15 + lịch US · Coupling: EURUSD cùng sign (USD-common confirm).

**S3 — ADX-Gated EMA Rider (Trend/Momentum)**
- Hypothesis: trend chỉ đáng trade khi directional strength cao (khác S1: dùng strength-gate thay channel) · Signal: ADX(14) H4 > 25 và EMA20/EMA50 H4 cùng hướng · Trade: pullback về EMA20-H4 entry; chandelier stop 3×ATR(H4).
- Risk: ADX muộn — vào muộn thoát muộn · Data: H4 OHLC · Coupling: gilt 2Y slope cùng hướng.

**S4 — Weekly Regime 5/20 MA (Trend/Momentum)**
- Hypothesis: chu kỳ differential tháng–quý hiện thân ở weekly closes · Signal: weekly close trên/dưới MA5 & MA20 weekly · Trade: position theo regime, rebalance weekly; stop = weekly close xuyên ngược MA20.
- Risk: lag lớn; whipsaw biên regime · Data: weekly OHLC · Coupling: carry sign (S31) cùng hướng → size gấp.

**S5 — Post-MPC Trend Day (Trend/Momentum)**
- Hypothesis: ngày MPC có surprise, repricing flow kéo dài qua NY (minutes + presser + dealer reposition) · Signal: surprise direction tại 12:00 London (decision vs consensus, hoặc soft-surprise vote-shift) · Trade: 12:05 entry; stop 1.5× pre-event 30m range; exit NY close.
- Risk: clean in-line → skip theo rule · Data: lịch MPC + consensus + M1 quanh 12:00 · Coupling: CPI sáng hôm trước cùng dấu (Sep-2026 template).

**S6 — Monthly TS-Momentum + Carry Gate (Trend/Momentum)**
- Hypothesis: momentum 3 tháng có autocorrelation ở horizon chính sách · Signal: sign return 3M; chỉ trade khi cùng dấu carry differential · Trade: position tháng; stop 5%.
- Risk: reversal tại differential flip · Data: daily close + swap rates · Coupling: S39 flip signal.

**S7 — Vol-Normalized Channel Breakout (Trend/Momentum)**
- Hypothesis: breakout đo bằng đơn vị vol mới so sánh được giữa regime (khác S1: Keltner thay Donchian + vol-unit) · Signal: close H4 qua Keltner(EMA20, 2.5×ATR) · Trade: theo breakout; stop nửa kênh; target 3R.
- Risk: vol regime shift làm threshold lag · Data: H4 OHLC · Coupling: RV percentile > 50th (S91).

**S8 — 4H Trend + M15 Pullback Ladder (Trend/Momentum)**
- Hypothesis: nhập dần theo pullback trong trend H4 cải thiện entry đáng kể so với breakout entry · Signal: H4 EMA50 slope; M15 pullback 50% leg gần nhất · Trade: 2–3 tranche limit tại retracement 38–62%; stop dưới swing; target prior extreme + extension.
- Risk: deep retracement đổi trend · Data: M15/H4 · Coupling: USD-proxy (EURUSD 60m momentum) không đối đầu.

**S9 — London Mover-Day Detector (Trend/Momentum)**
- Hypothesis: nếu đến 10:00 London range đã lớn + directional thì dealer flow đã chọn hướng — xác suất trend-day cao · Signal: range 07:00–10:00 > 60% ATR(20d) và M15 closes một phía VWAP · Trade: 10:15 join direction; trailing 1×ATR-daily/4; chạy tới NY close.
- Risk: ngày exhaustion (move đã xả hết buổi sáng) · Data: M5/M15 + daily ATR · Coupling: không US data 13:30 đối đầu.

**S10 — Trend Exhaustion De-Risk & Flip (Trend/Momentum)**
- Hypothesis: sau 3 trend-day + RSI daily extreme, risk-reward continuation xấu — cắt/flip từng phần (overlay, không phải system vào riêng) · Signal: 3 ngày cùng hướng + RSI(14)d > 75/< 25 + giá lệch VWAP-week · Trade: đóng 50% trend; lệnh flip chỉ khi break cấu trúc higher-low/lower-high.
- Risk: strong-trend months (2022-style) bỏ lỡ · Data: daily OHLC + RSI · Coupling: fiscal-stress flag S96 bật thì không fade.

### Family B — Mean-reversion (S11–S20)

**S11 — Asian-Range London Fade (Mean-reversion)**
- Hypothesis: breakout giả qua range châu Á 07:00–09:00 (stop-hunt) hồi về giữa range khi London thật định giá · Signal: xuyên Asian high/low rồi đóng lại trong range trước 09:00 · Trade: fade về mid-range; stop ngoài fake-extreme +2 pip; target mid.
- Risk: breakout thật do UK data mạnh · Data: M5 + Asian range 00:00–06:00 · Coupling: không UK data 07:00 mạnh.

**S12 — H1 RSI(2) + 200HMA Filter (Mean-reversion)**
- Hypothesis: overreaction ngắn-horizon revert khi trend trung tính · Signal: RSI(2) H1 < 5 / > 95 chỉ khi giá trong ±1% của 200HMA · Trade: entry close bar; exit RSI về 50 hoặc 8 bar; stop 1.2×ATR(H1).
- Risk: trend-start bar không revert · Data: H1 OHLC · Coupling: vol percentile < 50th.

**S13 — Asian Bollinger Snapback M15 (Mean-reversion)**
- Hypothesis: liquidity mỏng châu Á làm band-pierce tự hồi vì thiếu flow thật · Signal: M15 đóng ngoài BB(20,2) trong 22:00–05:00, bar sau đóng lại trong band · Trade: vào hướng vào lại band; target mid-band; stop nửa BB-width.
- Risk: Asian risk headline (BoJ/yen move) · Data: M15 · Coupling: spread châu Á thực tế < 2 pip.

**S14 — Round-Number Magnet Fade (Mean-reversion)**
- Hypothesis: mốc .00/.50 là options-barrier/take-profit cluster — test thứ 3+ thường fail · Signal: lần chạm thứ ≥3 của mốc .00/.50 trong 10 ngày không break bằng close H4 · Trade: fade từ mốc; stop 15 pip ngoài mốc; target 50 pip.
- Risk: barrier-break thật khi momentum mạnh (Sep-2026: vùng 1.35 đang bị test) · Data: H4 OHLC · Coupling: RR skew không nghiêng cùng hướng break.

**S15 — Small-Surprise CPI Fade (Mean-reversion)**
- Hypothesis: surprise CPI nhỏ (<0.2pp) tạo spike phút đầu rồi revert vì không đổi reaction function BoE · Signal: |actual − consensus| < 0.2pp; spike 1-min > 20 pip · Trade: fade sau 5–15 phút khi M1 break ngược; stop đỉnh spike; target 50% spike.
- Risk: surprise đúng chiều narrative nóng (services CPI vượt) · Data: M1 + consensus + release-time 07:00 chuẩn · Coupling: đêm Fed trước không cùng dấu surprise.

**S16 — Monday Gap Fill (Mean-reversion)**
- Hypothesis: gap Monday do thin weekend book không có flow hỗ trợ → fill · Signal: |gap| > 25 pip vs Friday 22:00 close · Trade: Sunday 22:30 vào hướng fill; stop nửa gap; target Friday close.
- Risk: gap do tin political/fiscal thật → continuation · Data: tick + news filter cuối tuần · Coupling: không có weekend fiscal leak.

**S17 — NY VWAP±2σ Reversion (Mean-reversion)**
- Hypothesis: buổi chiều NY không catalyst, deviation từ session-VWAP tự hồi về execution benchmark · Signal: 15:30–18:30 London, giá ngoài VWAP ± 2σ · Trade: vào về VWAP; stop +1σ; target VWAP.
- Risk: late-US-data trending afternoon · Data: M5 + VWAP intraday · Coupling: không data/Fedspeak 2h tới.

**S18 — Daily BB 2.5σ + RSI Divergence (Mean-reversion)**
- Hypothesis: đóng daily ngoài 2.5σ kèm divergence là exhaustion đa ngày · Signal: close ngoài BB(20,2.5) + RSI(14) divergence với swing trước · Trade: entry next open; target 20MA; stop 1 ATR ngoài extreme.
- Risk: band-walk trend mạnh (2022) · Data: daily OHLC · Coupling: S96 TẮT.

**S19 — EURGBP-Anchored Reversion (Mean-reversion)**
- Hypothesis: EURGBP extreme 30d khi EURUSD phẳng → phần idio của GBP quá tải, Mean-revert · Signal: EURGBP z(30d) > ±2 và |EURUSD 5d| < 0.3×|EURGBP 5d| · Trade: fade GBPUSD ngược extreme; stop 1×ATR; target z → 1.
- Risk: idio driver còn sống (fiscal event tuần đó) · Data: 3 cặp daily · Coupling: không UK event 3 ngày tới.

**S20 — Hurst-Gated MR Switch (Mean-reversion)**
- Hypothesis: MR chỉ có edge khi chuỗi có anti-persistence (H < 0.45) — đo, không phỏng đoán · Signal: rolling Hurst(100d) < 0.45 bật MR-family; > 0.55 tắt hẳn · Trade: meta-gate cho S11–S19.
- Risk: Hurst estimator noise; biên 0.45–0.55 không rõ ràng · Data: daily/H1 returns · Coupling: đồng thuận S91.

### Family C — Breakout / Vol-expansion (S21–S30)

**S21 — London Opening Range Breakout (Breakout/Vol)**
- Hypothesis: box 07:00–08:00 chốt inventory reset; break có continuation flow London · Signal: break box-boundary bằng M5 close ngoài + không re-enter trong 2 bar · Trade: stop mid-box hoặc opposite box; target 1.5R rồi trailing; time-exit 11:30.
- Risk: fake break ngày không data (Monday) · Data: M5 OHLC · Coupling: bật Tue–Thu (S27); ngày có UK data 07:00 thì dùng box 07:00–07:30.

**S22 — Pre-MPC Compression Expansion (Breakout/Vol)**
- Hypothesis: vol nén trước 12:00 MPC; post-decision expansion có direction thật · Signal: realized 30m vol 11:00–11:30 < 30th percentile của các ngày MPC · Trade: stop-entry hai phía 5 phút trước 12:00; OCO khi break pre-event 15m range; time-stop 60 phút.
- Risk: in-line + minutes neutral → cả hai phía bị cắt · Data: lịch MPC + M1 · Coupling: consensus rõ (không "coin-flip" meeting); nếu có options access thì thay bằng S93.

**S23 — NR7 / Inside-Day Breakout (Breakout/Vol)**
- Hypothesis: nén range đa ngày dự báo expansion (vol clustering) · Signal: daily range < min 6 ngày trước, hoặc inside-day · Trade: break high/low của ngày NR7 bằng 30m close hôm sau; stop mid-range; target 2R.
- Risk: false-start khi nén do thiếu liquidity · Data: daily OHLC · Coupling: không holiday-week; có event 24h tới tăng xác suất.

**S24 — NY Data-Window ORB (Breakout/Vol)**
- Hypothesis: box 13:30–14:30 UTC (US data + equity open) xác lập; break 15:00+ có institutional continuation · Signal: M15 close ngoài box sau 14:45 · Trade: stop mid-box; target đầu-day range extreme; time-exit 19:00.
- Risk: data two-sided đảo liên tục · Data: M15 + US calendar · Coupling: đồng thuận hướng London trend (S2).

**S25 — Asian Breakout With Retest (Breakout/Vol)**
- Hypothesis: break range châu Á cần retest giữ để loại stop-hunt (đối bù với S11: S11 fade break-fail; S25 join break-sau-retest) · Signal: break Asian range 07:00–08:30; retest edge trong 3 bar M15 và giữ · Trade: entry tại retest; stop trong range 5 pip; target 1× Asian-range height.
- Risk: double stop-hunt hai đầu · Data: M15 · Coupling: UK data 07:00 không phá structure.

**S26 — UK CPI Bracket Straddle (Breakout/Vol)**
- Hypothesis: impulse 07:00 CPI đủ lớn vượt spread hai chiều; bracket bắt direction không cần dự đoán · Signal: stop-order hai phía cách giá 06:55 khoảng 0.5× median 1-min move của 12 CPI trước · Trade: OCO; stop-loss 1× bracket-width; target 2×; gỡ bracket chưa fill lúc 07:05.
- Risk: whipsaw 2 nhịp khi headline vs services mâu thuẫn · Data: lịch CPI + M1 + phân phối spike lịch sử · Coupling: tuần CPI-trước-MPC tăng magnitude → nới target (Sep-2026 template).

**S27 — Weekday Vol Filter (Breakout/Vol)**
- Hypothesis: expansion reliability có mùa theo ngày: Tue–Thu thật, Mon/Fri giả nhiều hơn · Signal: bật breakout-family chỉ Tue–Thu; Mon/Fri chỉ MR · Trade: meta-gate.
- Risk: Monday holiday-shift dịch kỳ · Data: calendar + holiday 2 nước · Coupling: composite với S48.

**S28 — PDH/PDL Break With NY Confirm (Breakout/Vol)**
- Hypothesis: break previous-day high/low chỉ đáng tin khi NY (deep liquidity) confirm bằng close 14:00+ · Signal: H1 close ngoài PDH/PDL sau 14:00 London · Trade: entry tại close đó; stop re-entry trong range; target measured-move 1× day-range.
- Risk: stop-run hai đầu (saw-tooth Cable) · Data: H1 + daily · Coupling: EURUSD cũng break PD tương ứng (USD-led, sạch hơn).

**S29 — Midweek Weekly-Range Continuation (Breakout/Vol)**
- Hypothesis: range Mon–Tue định biên tuần; break Wednesday có quãng chạy tới Friday · Signal: break high/low của range Mon–Tue vào Wed London · Trade: entry break M30; stop biên đối diện tuần; exit Fri 16:00 hoặc trailing 2R.
- Risk: tuần data-heavy đổi narrative giữa tuần · Data: M30/daily · Coupling: không MPC/Budget giữa tuần.

**S30 — 3×ATR Blow-Off Fade (Breakout/Vol)**
- Hypothesis: nến M5 ≥ 3×ATR tại session extreme là exhaustion (vol climax), không phải start — fade nó, ngược logic breakout family · Signal: M5 range ≥ 3×ATR(M5,20) kết thúc tại high/low session + wick đảo · Trade: entry break ngược 50% candle; stop candle extreme; target VWAP.
- Risk: news cascade tiếp diễn thật · Data: M5 + calendar · Coupling: không nằm đúng thời điểm release chính.

### Family D — Carry / Rate-differential (S31–S40)

**S31 — SONIA–SOFR Carry Direction (Carry)**
- Hypothesis: chênh overnight spot (đúng nghĩa carry) có risk premium khi widening · Signal: SONIA − SOFR > +25bp và slope-20d dương → long-only; < −25bp và slope âm → short-only · Trade: position theo carry; stop 3×ATR-weekly; roll hằng ngày.
- Risk: carry reversal khi differential flip (Sep-2026: Fed hike qua BoE làm carry long âm nhẹ) · Data: overnight/swap rates · Coupling: momentum veto S40.

**S32 — 2Y Swap-Differential Trend Filter (Carry)**
- Hypothesis: slope differential 2Y là proxy path kỳ vọng — filter toàn bộ directional family · Signal: slope-20d của (UK 2Y − US 2Y) · Trade: chỉ cho entry cùng hướng slope (filter, không position riêng).
- Risk: lead/lag giữa rates và spot không ổn định · Data: 2Y swap/yield daily · Coupling: đồng thuận S4.

**S33 — CB-Calendar Front-Run (Carry)**
- Hypothesis: khi meeting-implied prob hai bank lệch pha, differential repricing diễn ra trước meeting · Signal: OIS implied BoE-hike prob > 70% với Fed đã priced-hold (hoặc đảo vai) → 3–5 ngày trước meeting · Trade: position theo hướng differential sẽ repricing; đóng trước decision.
- Risk: đã priced-in hết → "sell the fact" ngược · Data: OIS/SONIA + lịch · Coupling: CPI gần nhất cùng hướng.

**S34 — Carry + Momentum Combo (Carry)**
- Hypothesis: carry chỉ an toàn khi spot momentum cùng chiều — carry crash đều xảy ra sau khi momentum đã đảo · Signal: carry sign (S31) + 50d spot momentum sign đồng thuận · Trade: size theo carry magnitude; trailing stop 20d low/high.
- Risk: cliff reversal dù hai sign đồng thuận (2022) · Data: spot + rates · Coupling: S96 TẮT.

**S35 — Cable Legging via EURGBP (Carry)**
- Hypothesis: GBPUSD = EURGBP × EURUSD; khi có thesis GBP-direction, chọn leg có carry/momentum thuận hơn để vào, hedge leg còn lại — giảm cost và carry trôi · Signal: so sánh carry & momentum của 2 leg với cùng thesis · Trade: long GBP qua leg rẻ, short leg đắt theo ratio nominal 1:1:1.
- Risk: legs không khóa đúng (execution/basis) · Data: 2 cặp + swap points · Coupling: dùng khi chênh carry giữa 2 leg > 15bp.

**S36 — Forward-Premium Divergence (Carry)**
- Hypothesis: khi forward points imply one-way nhưng spot momentum ngược, spot thường thắng ngắn hạn (flow structure của covered-parity deviation) · Signal: 12M forward GBP discount ở percentile cao trong khi spot 20d momentum dương · Trade: long theo momentum với size giảm dần theo carry-cost; exit khi momentum flip.
- Risk: carry drag mỗi ngày giữ · Data: forward points + spot · Coupling: differential momentum dự kiến flip theo spot (S39).

**S37 — OIS 1Y1Y Repricing Momentum (Carry)**
- Hypothesis: sau khi 1Y1Y dịch chữ lớn (≥15bp/3 ngày), spot theo trong vài ngày · Signal: Δ(1Y1Y OIS UK) 3 ngày > +15bp → long-bias GBP, **trừ khi** US-side cũng shift cùng (phải lấy net) · Trade: 3-day window entry theo net-shift; stop khi curve retrace 50%.
- Risk: central bank push-back bằng speak · Data: OIS curve daily · Coupling: net UK − US, không dùng từng bên riêng.

**S38 — Forced-Hike Scenario (Carry)**
- Hypothesis: khi UK CPI ≥ 3% AND gilt 10Y ≥ 5% (vượt tolerance BoE), thị trường underprice khả năng BoE phải hike — long GBP vào MPC kế tiếp. Sep-2026 exact template: CPI 3.1%, gilt 5.38%, BoE hold (verified) · Signal: hai điều kiện cùng lúc + BoE hold gần nhất · Trade: long GBPUSD 5 ngày trước MPC (kế tiếp 05/11/2026); TP 12:30 decision day; stop nếu gilt rally đảo (fiscal trumps monetary).
- Risk: gilt selloff là fiscal-driven → GBP xuống dù CPI nóng (kênh 2022) · Data: CPI, gilt 10Y/2Y, MPC calendar · Coupling: gilt move phải là BoE-hawkish-repricing (2Y cùng tăng), không phải 30Y-led fiscal.

**S39 — Differential Momentum Sign Flip (Carry)**
- Hypothesis: monthly close của differential 2Y là turnover chậm nhưng bền của FX regime · Signal: sign slope-20d đổi và giữ 2 tháng liên tiếp · Trade: flip bias sau tháng close thứ 2; size 50% tháng đầu, full tháng sau.
- Risk: whipsaw quanh zero-line · Data: 2Y swaps monthly · Coupling: đồng thuận S4 weekly flip.

**S40 — Anti-Carry Veto Overlay (Carry)**
- Hypothesis: trend ngược carry mạnh (|diff| > 50bp) mang negative-carry tail — drag hằng ngày làm xác suất thua tăng phi tuyến · Signal: |SONIA − SOFR| > 50bp và trade ngược hướng carry · Trade: block hoặc size ×0.5 mọi lệnh trend ngược carry.
- Risk: miss counter-carry moves hiếm nhưng lớn · Data: swap rates · Coupling: áp cho Family A.

### Family E — Session / Time-of-day / Seasonality (S41–S50)

**S41 — Overlap Turbo Continuation (Session)**
- Hypothesis: 15:00–17:00 London là cửa sổ thanh khoản sâu nhất — continuation hướng ngày có participation thật · Signal: 14:45 xác lập hướng ngày (net-move từ day-VWAP) · Trade: entry 15:00; stop swing 14h-session; exit 17:30.
- Risk: 15:00 US flow đảo (hiếm) · Data: M15 + VWAP · Coupling: US data 13:30 đã digested không đảo.

**S42 — Friday-Late Liquidation Fade (Session)**
- Hypothesis: 19:00+ Friday weekly book được cắt → move cuối tuần thường retraces vào close · Signal: Friday 18:30+, |week-move| > 1.5× weekly ATR · Trade: fade ngược week-move; stop 30 pip; flat trước 21:30.
- Risk: genuine late-week cascade · Data: M30 + weekly stats · Coupling: không weekend-event risk.

**S43 — Month-End Fix Flow Anticipation (Session)**
- Hypothesis: WM/R 16:00 London fix ngày cuối tháng tạo order-flow một chiều ước lượng được từ monthly equity moves (hedge rebalancing) · Signal: ước tính flow-sign từ UK/US equity month-return × hedge-ratio heuristic · Trade: 15:00–16:00 vào cùng hướng flow ước tính; exit 16:15.
- Risk: ước tính sai dấu khi equity quay cuối tháng · Data: equity indices + fix calendar · Coupling: quarter-end size lớn hơn (S49).

**S44 — Turn-of-Month Bias (Session)**
- Hypothesis: 2 ngày cuối + 3 ngày đầu tháng có flow định kỳ (pension/rebalance) thuận hướng risk · Signal: calendar window; long-bias nếu macro không bear · Trade: position nhỏ theo bias; stop 2×ATR.
- Risk: bias yếu, phụ thuộc regime · Data: daily + calendar · Coupling: carry cùng dấu (S31).

**S45 — Thin-Liquidity Calendar Regime (Session)**
- Hypothesis: August & 20 Dec–3 Jan: market-maker rút → breakout giả tăng, range hoạt động tốt hơn · Signal: calendar flag · Trade: disable Family C; enable S13/S50; size ×0.5 toàn bộ.
- Risk: flash-move tail trong thin market (2019 template) — stop phải hard · Data: calendar · Coupling: kèm S99.

**S46 — UK/US Holiday-Mismatch Days (Session)**
- Hypothesis: ngày UK holiday nhưng US mở (hoặc ngược): Cable thin nhưng US data vẫn đẩy USD — spike không đối ứng GBP, thường revert một phần · Signal: holiday table lệch + có US data 13:30 · Trade: fade 50% spike US-data sau 1h nếu không continuation; stop spike-extreme.
- Risk: US-trend day thật · Data: holiday calendar + M15 · Coupling: liquidity proxy (volume) thấp rõ rệt.

**S47 — 09:30 Data Momentum Persistence (Session)**
- Hypothesis: surprise 09:30 (PMI/retail/LFS) có continuation dài hơn surprise 07:00 vì London đã có mặt để chase · Signal: |surprise| > 1σ lịch sử; hướng initial 5m move · Trade: entry 09:40 cùng hướng; stop initial-spike; exit 13:00.
- Risk: 13:30 US data đối đầu · Data: calendar UK + M5 · Coupling: không US data 13:30.

**S48 — Day-of-Week Family Gate (Session)**
- Hypothesis: Monday = positioning (MR-bias); Tue–Thu = discovery (trend-bias); Friday = profit-taking (MR-afternoon) · Signal: weekday · Trade: allocation weights MR/trend theo ngày (meta).
- Risk: meta-bias yếu nếu dùng một mình · Data: calendar · Coupling: composite với S27.

**S49 — Quarter-End Rebalance Flow (Session)**
- Hypothesis: cuối quý, UK pension/asset rebalance tạo GBP demand/supply hệ thống theo QTD asset performance · Signal: estimate từ QTD UK equity + gilt return signs · Trade: 2 ngày cuối quý theo flow-estimate sign; size nhỏ.
- Risk: estimate thô, nhiễu cao · Data: index QTD + calendar · Coupling: trùng month-end fix cùng dấu → size gấp (S43).

**S50 — Asian Band Fade (Session)**
- Hypothesis: 22:00–06:00 GBP thiếu participant → dao động band hẹp, fade biên hiệu quả nếu cost kiểm soát · Signal: chạm biên band-Asia 2 lần + RSI(M15) extreme · Trade: fade biên; stop 8 pip ngoài biên; target mid; force-flat 06:45.
- Risk: Asian risk headline; spread nở · Data: M15 + spread-monitor · Coupling: đo spread châu Á thực tế < 2 pip trước khi bật.

### Family F — Event / Data-driven (S51–S60)

**S51 — MPC Surprise Direction Trade (Event)**
- Hypothesis: decision lệch consensus là shock thông tin lớn nhất tháng — continuation qua NY · Signal: decision vs consensus (kể cả soft-surprise: vote-split dịch) · Trade: entry 12:01–12:05 theo surprise; stop pre-event 15m range; exit NY close; hold qua đêm nếu minutes cùng hướng.
- Risk: in-line → skip theo rule, không discretionary · Data: MPC consensus + realtime decision + M1 · Coupling: CPI sáng hôm trước cùng dấu.

**S52 — Vote-Split Shift Positioning (Event)**
- Hypothesis: đổi split phiếu (hoặc dissent mới) signal path đổi trước 1–2 meeting — drift nhiều ngày · Signal: split so với meeting trước (5–4 → 6–3 dạng hawkish, hoặc xuất hiện dissent-hike) · Trade: position sau 12:30 theo hướng shift; giữ tới minutes 3 tuần sau; stop gilt-move ngược.
- Risk: language shift neutral hóa split · Data: vote records + minutes text · Coupling: S37 1Y1Y đồng hướng.

**S53 — CPI Surprise Size-Scaled Continuation (Event)**
- Hypothesis: surprise ≥ 0.3pp đổi reaction-function kỳ vọng → continuation nhiều giờ; < 0.2pp là domain của S15 (fade) — phản ứng phân phối theo size, không tuyến tính · Signal: surprise ≥ 0.3pp, đặc biệt services CPI · Trade: entry sau pullback đầu (15–30m); stop retrace-low; target 2× initial spike; hold qua ngày nếu BoE tuần đó.
- Risk: base effects/revisions bị discount · Data: CPI detail + consensus + M5 · Coupling: S38 điều kiện kèm tăng conviction.

**S54 — Average Earnings Surprise Trade (Event)**
- Hypothesis: BoE coi wage (incl bonus) là anchor chính — earnings surprise dịch path mạnh gần bằng CPI · Signal: AWE incl bonus surprise > 0.3pp kèm private-sector regular pay cùng hướng · Trade: entry 07:15 sau spike-retrace; horizon 1–3 ngày; stop ATR(1d).
- Risk: series revision lớn, noise cao (S60) · Data: ONS earnings + consensus + daily · Coupling: CPI gần nhất cùng hướng.

**S55 — Flash PMI Momentum (Event)**
- Hypothesis: PMI flash là nowcast growth sạch nhất — crossing 50 là regime mark · Signal: services flash surprise > 1 điểm hoặc crossing 50/47 · Trade: 09:40 entry; stop initial spike; horizon 2 ngày.
- Risk: flash vs final revise mạnh · Data: PMI calendar + M5 · Coupling: monthly GDP kỳ trước cùng hướng.

**S56 — Monthly GDP Release Fade (Event)**
- Hypothesis: GDP 07:00 phát trong liquidity mỏng (khác US GDP 13:30) — spike thiếu participant, revert khi London đầy đủ · Signal: 07:00 spike > 25 pip trong 5m, không continuation tới 07:30 · Trade: fade 07:35; stop spike-extreme; target 60% spike.
- Risk: surprise cực lớn đổi narrative · Data: ONS GDP calendar + M1 · Coupling: skip nếu trùng tuần CPI (magnitude thật).

**S57 — Fiscal-Event Gilt-Led Playbook (Event)**
- Hypothesis: Budget/Autumn Statement truyền vào Cable qua gilt: nếu 30Y gilt + ≥ 20bp intraday & Cable break daily support → "fiscal dominance" mode, GBP tiếp tục rơi (2022 template; Sep-2026 echo với gilt 10Y 5.378% — verified) · Signal: trong/ngày sau fiscal statement: Δ30Y gilt + ΔFTSE + Cable vs daily support · Trade: short Cable khi break support; trailing 2×ATR; thoát khi gilt 30Y stall 2 phiên hoặc BoE-intervention headline.
- Risk: "good Budget" (gilt xuống) đảo chiều — bắt buộc tín hiệu hai-điều kiện (gilt & support) · Data: gilt 30Y intraday + Cable daily + fiscal calendar + newswire · Coupling: S96 flag; DMO auction tuần đó.

**S58 — MPC Minutes NLP Bias (Event)**
- Hypothesis: tần số từ vựng hawkish-vs-dovish trong minutes thay đổi trước policy — drift inter-meeting · Signal: word-count delta ("tighten/tightening" vs "accommodative/cut") chuẩn hóa độ dài so minutes trước · Trade: bias theo delta trong 3 tuần; vào bằng daily pullback; stop 2×ATR.
- Risk: NLP thô bỏ ngữ cảnh; Governor speech override · Data: minutes text + lexicon đơn giản · Coupling: S52 đồng hướng.

**S59 — Fed–BoE Same-Week Stack (Event)**
- Hypothesis: khi Fed & BoE cách nhau 1 ngày (Sep-2026: Fed 16/09 hike, BoE 17/09 hold — verified), tổng hợp 2 surprise quyết định drift tuần đó — trade residual sau khi CẢ HAI qua · Signal: combined sign = sign(Fed surprise theo hướng USD) + sign(BoE surprise theo hướng GBP) · Trade: entry Thu 13:00 London theo combined sign; horizon 3–5 ngày; stop 1.5×ATR(1d).
- Risk: một trong hai là "dovish hold" mơ hồ → combined sign yếu, skip · Data: lịch 2 bank + consensus + đọc minutes nhanh · Coupling: S39 cùng hướng.

**S60 — Wide-Consensus Veto (Event)**
- Hypothesis: khi consensus range rộng hoặc series đang volatile (UK payrolls mới), "surprise" thực chất là noise — EV của event trade âm · Signal: forecast dispersion > ngưỡng; hoặc revision-volatility của series cao · Trade: meta-veto cho S51–S55.
- Risk: bỏ lỡ vài surprise thật (chấp nhận) · Data: consensus detail (range/std) · Coupling: risk-discipline chung.

### Family G — Cross-asset / Correlation (S61–S70)

**S61 — Gilt 10Y Intraday Lead (Cross-asset)**
- Hypothesis: trong fiscal-stress regime, gilt 5m yield impulses dẫn Cable ngược dấu vài phút (risk-premium channel) · Signal: 5m gilt yield change > 2bp intraday; Cable lag 0–10 phút · Trade: momentum Cable theo hướng inverse của gilt burst; horizon 30–60m.
- Risk: dấu flip khi gilt-up do BoE-hawkish (GBP-up) — gate theo nguồn move (2Y cùng chiều = hawkish; 30Y-led = fiscal) · Data: gilt futures/10Y intraday + Cable M5 · Coupling: S96 bật.

**S62 — Gilt–Bund Spread → EURGBP (Cross-asset)**
- Hypothesis: chênh 10Y UK–DE là rate-channel tương đối của EURGBP; widening growth-driven → GBP mạnh vs EUR; widening fiscal-driven → GBP yếu vs EUR — dấu phụ thuộc regime · Signal: 20d change của spread + fiscal flag chọn dấu · Trade: EURGBP position 2 tuần; stop ATR-weekly.
- Risk: phân loại regime sai → chọn dấu sai · Data: 10Y UK + DE daily + S96 flag · Coupling: không có ECB meeting cùng tuần.

**S63 — EURGBP Decomposition Router (Cross-asset)**
- Hypothesis: nếu động lượng là GBP-idio (EURGBP trending, EURUSD flat) → trade Cable mạnh; nếu USD-common → dùng EURUSD làm signal, entry Cable để tránh tốn công double-position · Signal: 5d |ret| ratio của 2 cặp: idio-ratio > 2 → GBP-driver; < 0.5 → USD-driver · Trade: router cho toàn bộ Family A/B trên Cable.
- Risk: phân rã nhạy window · Data: 3 cặp daily · Coupling: chạy trước khi chọn instrument mỗi tuần.

**S64 — EURUSD Lead-Lag Confirmation (Cross-asset)**
- Hypothesis: trong giờ EU/US data chung, EURUSD (sâu hơn) break trước Cable vài phút — dùng làm trigger timing · Signal: EURUSD break M30 high/low với volume spike; Cable chưa break tương ứng · Trade: entry Cable cùng hướng ngay hoặc tại break của nó; stop theo EURUSD-reversal; target 1:1.5.
- Risk: lag chỉ vài phút — cần execution nhanh/bán tự động · Data: 2 cặp M5 đồng bộ timestamp · Coupling: S63 xác nhận USD-common đang dominant.

**S65 — EURUSD USD-Gate cho Cable Breakout (Cross-asset)**
- Hypothesis: breakout Cable đáng tin hơn khi USD-factor cùng hướng — loại break do GBP-noise; thay DXY (circular vì GBP 11.9%) bằng EURUSD · Signal: đồng thời Cable break PDH/PDL và EURUSD break same-side band · Trade: double-confirm entry; stop single-side invalidation; target 2R.
- Risk: double-confirm vào muộn mất đầu move · Data: 2 cặp H1 · Coupling: gate cho S28.

**S66 — FTSE–Gilt–Cable Triple Discriminator (Cross-asset)**
- Hypothesis: 3 biến phân biệt narrative: (a) growth story: FTSE↑ + gilt↑ + Cable↑; (b) fiscal stress: FTSE↑ (exporter-cheap) + gilt↑↑ + Cable↓ (2022 & Sep-2026); (c) risk-off: ba biến mixed-down · Signal: phân loại ngày theo triple-sign pattern · Trade: regime (b) → chỉ short-rallies; (a) → long-dips; (c) → giảm size toàn bộ.
- Risk: pattern hiếm ngày thường — dùng như overlay · Data: 3 assets daily + gilt intraday · Coupling: input cho S96.

**S67 — Risk-Appetite Beta Positioning (Cross-asset)**
- Hypothesis: GBP half-risk beta — composite risk (S&P trend + gold + VIX) ở extreme thì Cable drift thuận risk-on · Signal: composite risk-index z > ±1.5 · Trade: position theo risk-sign; horizon 3–5 ngày; stop composite flip.
- Risk: USD-shock risk-off: USD lên cùng risk-off → Cable rơi nhiều hơn proxy dự báo (double-hit) · Data: equity/gold/VIX daily · Coupling: EURUSD không ngược dấu (nếu ngược → USD-effect, skip).

**S68 — Oil–CAD Confirmation Filter (Cross-asset)**
- Hypothesis: khi Brent impulse lớn, USDCAD phản ứng nghịch — nếu Cable cũng move theo "dollar-story" thì confirm USD-driver; nếu Cable đứng yên thì driver là commodity → bỏ signal USD · Signal: Brent 5d |ret| > 4%; so response ratio USDCAD vs Cable · Trade: filter nâng/giảm conviction cho Family A (không position riêng).
- Risk: chỉ là heuristic đồng biến · Data: Brent + USDCAD + Cable daily · Coupling: kèm S65.

**S69 — 2Y Differential Intraday Momentum (Cross-asset)**
- Hypothesis: burst repricing 2Y US/UK trong phiên US (Fedspeak/data) đẩy Cable theo differential · Signal: 5m change của (US2Y − UK2Y) > 3bp; Cable theo hướng inverse · Trade: scalp M5 15–45 phút; stop pre-burst range.
- Risk: yield burst tự revert trong phiên · Data: 2Y intraday 2 bên + M5 · Coupling: giờ US-only 14:00–19:00 UTC.

**S70 — Cross-Asset Vol Regime Switch (Cross-asset)**
- Hypothesis: VIX percentile + (Cable IV − RV) quyết định family sống: vol cao → trend/event; vol thấp → MR/range · Signal: composite: VIX 60d-pct > 70 & IV > RV → trend-mode; < 30 & IV < RV → MR-mode · Trade: allocation switch Family A vs B.
- Risk: IV data chất lượng/tenor không nhất quán giữa nguồn · Data: VIX + Cable ATM IV 1W + RV · Coupling: master gate hàng tuần cùng S91.

### Family H — Positioning / Flows (S71–S80)

**S71 — COT Spec Extreme Fade (Positioning)**
- Hypothesis: net-spec GBP futures (CME) ở percentile cực đoan = crowd full → reversal có xác suất thuận · Signal: net-spec pct 52w > 90th (fade rallies) hoặc < 10th (fade dumps) · Trade: entry khi price-action confirm (daily engulf/spike-fail); stop 2×ATR; horizon 2–4 tuần.
- Risk: momentum crush contrarians khi trend kéo dài · Data: COT weekly (Tue data/Fri release — lag đúng!) + daily · Coupling: RR skew cùng extreme (S73).

**S72 — COT Zero-Cross Flip (Positioning)**
- Hypothesis: net-spec đổi dấu sau thời gian dài một phía đánh dấu regime flow mới — theo, không chống · Signal: cross 0 sau ≥ 6 tuần cùng dấu trước đó · Trade: theo hướng flip; position 2–4 tuần; stop flip-reversal.
- Risk: flip do roll/technical không phải conviction · Data: COT + daily · Coupling: S39 cùng hướng flip.

**S73 — Risk-Reversal Extreme Contrarian (Positioning)**
- Hypothesis: 25Δ RR 1M extreme = insurance một chiều quá tải → premium-crowd là nhiên liệu đảo chiều · Signal: RR z(1y) > +2 (GBP-call overloaded) → fade bullish moves; < −2 → ngược · Trade: entry sau daily-reversal pattern; horizon 2–4 tuần; stop 2×ATR.
- Risk: extreme còn cực hơn trước khi revert (skew chạy xa) · Data: RR 25Δ 1M + spot daily · Coupling: COT cùng extreme tăng conviction gấp.

**S74 — OI–Price Matrix (Positioning)**
- Hypothesis: futures OI + giá phân biệt new-money trend vs short-covering · Signal: OI↑ + price↑ = conviction long (join); OI↓ + price↑ = covering (fade-ready); OI↑ + price↓ = new shorts (tránh long) · Trade: quyết định cooperate-vs-fade với Family A theo cell.
- Risk: FX futures OI chỉ là slice của thị trường OTC · Data: CME GBP OI weekly + daily close · Coupling: volume-confirm.

**S75 — COT Divergence Veto (Positioning)**
- Hypothesis: giá lập 20d-high mới nhưng net-spec thấp hơn high trước → up-move thiếu flow mới (squeeze) → trend yếu · Signal: 20d-new-high & net-spec < high-trước > 15% · Trade: veto/trim Family A longs; tight-trailing.
- Risk: OTC flow thay thế COT làm đại diện sai · Data: COT + daily · Coupling: RR flat (không extreme).

**S76 — Session-Open Delta Imbalance (Positioning)**
- Hypothesis: M5 volume-delta một chiều 07:00–08:00 London là dấu hiệu dealer book lệch — hướng delta tiếp tục tới fix · Signal: |aggressive-buy − aggressive-sell| 07:00–08:00 > 2σ của 20 ngày · Trade: cùng hướng delta từ 08:05; stop delta-flip; exit 16:00.
- Risk: delta proxy từ 1 venue → sample bias; cần tổng hợp venue · Data: tick/volume-delta data chất lượng + M5 · Coupling: S9 đồng hướng tăng size.

**S77 — Gilt Auction Bid-to-Cover Signal (Positioning)**
- Hypothesis: long-end auction yếu (cover thấp, tail dài) đánh fiscal-credibility → GBP down-bias 1–2 ngày; auction mạnh neutral/positive (30Y 08/09/2026 demand tốt dù 5.82% — verified) · Signal: bid-to-cover vs 12-month avg; tail vs avg · Trade: theo bias ngày hôm sau (short-rally nếu yếu); stop 1.5×ATR.
- Risk: auction noise; global-bond beta lấn át · Data: DMO auction results + calendar · Coupling: S96 & S57 cùng tuần.

**S78 — Retail-Sentiment Contrarian (Positioning)**
- Hypothesis: broker client positioning (>70% một phía) thua trung bình ở reversal points — contrarian edge nhỏ nhưng thật ở extreme + S/R confluence · Signal: sentiment ≥ 70% / ≤ 30% kèm giá tại daily S/R hoặc round number · Trade: fade theo sentiment-extreme tại rejection candle; stop 1×ATR; target mid-range.
- Risk: trend-days đốt fade liên tục · Data: retail sentiment feed + daily · Coupling: S71 cùng phía extreme.

**S79 — Systematic-Flow Unwind Anticipation (Positioning)**
- Hypothesis: CTA/trend-fund positioning ước lượng qua vol-adjusted trend signals — khi position lớn & signal gần flip, unwind cascade tạo overshoot · Signal: composite trend-factor (20d/60d sign & vol-scaled) estimate GBP position; cảnh báo khi large & near-flip · Trade: khi flip xảy ra, join hướng unwind 2–3 ngày; stop re-flip.
- Risk: estimate model sai structure flow thật · Data: spot daily (rebuild factor) + public CTA notes nếu có · Coupling: S72 zero-cross confirm.

**S80 — Cross-Currency Basis Stress Flag (Positioning)**
- Hypothesis: GBP basis (vs USD/EUR) widening = UK funding stress (LDI-2022 template) — leading flag rủi ro GBP trước khi spot break · Signal: 3M GBP basis percentile 1y > 90th · Trade: risk-overlay: giảm size longs, widen stops, disable MR-fade longs (không position riêng).
- Risk: basis do money-market technicals không chạm FX · Data: basis quotes thương mại · Coupling: composite với S92.

### Family I — Pattern / Pairs / Stat-arb (S81–S90)

**S81 — Triangle Consistency Filter (Stat-arb)**
- Hypothesis: EURUSD = GBPUSD × EURGBP luôn đúng theo arbitrage; sai lệch vượt frictions = artifact dữ liệu/timing → mọi signal lúc đó nhiễm lỗi · Signal: |implied − actual EURUSD| > 3 pip trong 1 phút · Trade: veto/suspend signal-machine vài phút (hygiene layer).
- Risk: vô hại nếu logic đúng — chỉ tốn cơ hội · Data: 3 cặp tick đồng bộ · Coupling: chạy nền suốt.

**S82 — USD-Basket Residual Reversion (Stat-arb)**
- Hypothesis: Cable = β1·EURUSD + β2·USDJPY + β3·USDCAD + ε; ε là GBP-idio — z của ε reverting khi không catalyst UK · Signal: OLS rolling-60d residual z > ±2 và không có UK event 3 ngày tới · Trade: trade residual về 0 bằng Cable hedged basket theo β; target z → 0.5; stop z > 3.
- Risk: catalyst UK xuất hiện → residual trending không revert · Data: 4 cặp daily + calendar · Coupling: S63 tắt router khi idio-driver mạnh.

**S83 — Rolling-Beta Dislocation Switch (Stat-arb)**
- Hypothesis: beta Cable/EURUSD thoát band [0.75, 1.05] = GBP đang có driver riêng — family GBP-specific thắng USD-common · Signal: 60d beta ngoài band 10 ngày liên tiếp · Trade: router allocation: bật Family D/F/G-UK; giảm G-USD.
- Risk: beta estimate noise cửa sổ ngắn · Data: 2 cặp daily · Coupling: decision chung với S63.

**S84 — Hourly Autocorrelation Regime (Stat-arb)**
- Hypothesis: dấu AR(1) hourly returns quyết định persistence intraday: dương → momentum; âm → MR — đo, không phỏng đoán · Signal: rolling 120h AR(1) với CI; |coef| > 0.1 mới dùng · Trade: switch Family intraday (A-momentum vs B-MR) theo sign.
- Risk: coefficient nhỏ vô nghĩa thống kê · Data: H1 returns · Coupling: đồng thuận S20 Hurst.

**S85 — G10 Cross-Sectional Rank Tilt (Stat-arb)**
- Hypothesis: rank momentum 1M của GBP trong G10 có predictive nhẹ cho Cable tháng tới (cross-sectional FX momentum) · Signal: rank vol-adjusted 1M; top-3 → long-tilt; bottom-3 → short-tilt · Trade: tilt half-size; rebalance tuần; stop rank-flip.
- Risk: GBP giữa bảng thường xuyên → ít signal · Data: 10 cặp G10 daily · Coupling: carry cùng dấu rank (S31).

**S86 — USDJPY Risk-Proxy Lead Gate (Stat-arb)**
- Hypothesis: trong risk-episodes, USDJPY phản ứng risk nhanh/nét hơn Cable — dùng làm confirmation gate cho continuation entries · Signal: USDJPY 4h momentum theo risk-direction + Cable chưa confirm · Trade: cho phép/block Family A entries (gate, không position riêng).
- Risk: BoJ/yen-specific shock làm proxy sai · Data: USDJPY H4 + Cable · Coupling: chỉ trong VIX > 20 regime.

**S87 — Cross-Leg Z-Alignment Pairs (Stat-arb)**
- Hypothesis: khi EURGBP z và Cable z cùng extreme cùng "GBP-hướng" (vd EURGBP z −2 & Cable z +2 → GBP yếu khắp) → continuation xác suất cao hơn fade — cross-conditioned momentum (đối bù S19: S19 fade divergence, S87 trade alignment) · Signal: z(20d) 2 cặp cùng dấu GBP-nghĩa, |z| > 1.8 cả hai · Trade: theo hướng GBP-driver; stop z-flip một leg; target z 2.8.
- Risk: USD-factor đảo giữa chừng làm 1 leg flip · Data: 2 cặp daily · Coupling: S83 beta-regime idio đang bật.

**S88 — Forward-Point Term-Structure Trade (Stat-arb)**
- Hypothesis: quanh event repricing, near-dated forwards dịch hơn 12M — dislocation giữa tenors revert khi curve settle (micro term-premium arb) · Signal: |1M-annualized forward − 12M forward| z > 2 sau event-week · Trade: position theo hướng curve converge; roll hằng ngày; exit z < 0.5.
- Risk: curve repricing tiếp đúng hướng dislocation (không revert) · Data: forward points multi-tenor + event calendar · Coupling: S37 vừa shift.

**S89 — Event-Type Lead-Lag Router (Stat-arb)**
- Hypothesis: Cable dẫn EURGBP trong giờ BoE/UK-data; EURGBP dẫn Cable trong giờ ECB/EU-data — lead-lag phụ thuộc loại event · Signal: event-type flag theo calendar; đo leader trong 15 phút đầu release · Trade: laggard entry theo leader move khi intraday-correlation cao; scalp 30m.
- Risk: cả hai không move (non-event) · Data: 2 cặp M1 + calendar 2 vùng · Coupling: S64 cho cặp EURUSD giờ US-data.

**S90 — London Stop-Hunt Sweep-Reclaim (Pattern)**
- Hypothesis: sweep qua extreme châu Á/đêm rồi reclaim trong ≤ 2 bar M5 là stop-hunt xong — đảo chiều ngắn có structure · Signal: M5 sweep + reclaim + volume spike tại 07:00–10:00 London · Trade: entry tại reclaim-close; stop ngoài sweep-extreme +2 pip; target VWAP hoặc opposite Asian edge.
- Risk: sweep là breakout thật (S25 sẽ bắt — hai hypothesis đối bù trong cùng hệ phân loại) · Data: M5 + Asian range · Coupling: không UK data 07:00 đang bay.

### Family J — Regime-conditioned / Options-flavored (S91–S100)

**S91 — Realized-Vol Percentile Master Switch (Regime)**
- Hypothesis: RV20 percentile quyết định family sống: < 30th → MR/range; > 70th → trend/event; giữa → giảm size · Signal: RV20 percentile 1y rolling · Trade: allocation switch + size scaling (meta).
- Risk: percentile lag regime turn vài ngày · Data: daily returns · Coupling: đồng thuận S70, S20.

**S92 — Gilt-Vol Stress Spill Overlay (Regime)**
- Hypothesis: rate-vol Anh (gilt futures ATR / proxy MOVE-UK) extreme làm Cable fat-tail hai chiều — giảm exposure, không phải direction signal · Signal: gilt-futures RV20 > 80th percentile · Trade: risk-overlay: size ×0.5, stop ×1.5, disable counter-trend MR.
- Risk: bỏ lỡ moves lớn để sống qua stress (trade-off chủ đích) · Data: gilt futures daily/intraday · Coupling: composite với S80, S96.

**S93 — Pre-MPC Long-Gamma Straddle (Options)**
- Hypothesis: MPC là vol-event có expansion khi IV underprice decision risk · Signal: 1W ATM IV < 70th percentile so với 12 MPC trước (crush-risk thấp) · Trade: mua straddle (hoặc synthetic spot-bracket) 24h trước; đóng 2–4h sau decision; delta-hedge nếu spot chạy trước.
- Risk: IV đã đắt → crush dù move; options retail spread đắt — paper-trade trước · Data: IV surface/history + MPC calendar · Coupling: S22 là bản spot-only khi không có options access.

**S94 — Post-Event Clean-Pass Range Fade (Options)**
- Hypothesis: MPC in-line + minutes neutral → 48h vol crush, range compression — fade biên range như "short-vol proxy" · Signal: decision đúng consensus, vote không đổi, IV post-event rơi > 15% · Trade: fade extremes của post-event 48h range; stop ngoài range; target mid; flat trước US-data 13:30.
- Risk: Fedspeak/data giữa window · Data: MPC results + IV + M15 · Coupling: đã qua S60 veto.

**S95 — Skew-Momentum Tilt (Options)**
- Hypothesis: thay đổi 1W 25Δ RR theo tuần phản ánh insurance-demand mới — drift ngắn theo hướng skew đang dịch (momentum của skew, khác extreme-contrarian S73) · Signal: ΔRR tuần > +1.5σ lịch sử → tilt theo hướng call-demand; ngược thì put · Trade: spot tilt (không cần mua option); horizon 1 tuần; stop ΔRR flip.
- Risk: skew noise quanh event calendar · Data: RR 1W daily history · Coupling: không nằm trong event-week.

**S96 — Fiscal-Stress Regime Flag (Regime)**
- Hypothesis: composite (10Y gilt > 5%, 30Y−10Y steepening, auction cover yếu, basis rộng) bật → GBP down-bias cấu trúc, veto longs & MR-fade — đúng regime 2022 và Sep-2026 (đã verify trạng thái các thành phần) · Signal: ≥ 2/4 điều kiện bật giữ 3 ngày · Trade: overlay: Family A short-only; MR long bị veto; size ×0.75; thoát regime khi < 1/4.
- Risk: false-positive khi gilt tăng do growth (Cable dấu dương) — check 2Y đồng bộ để phân loại · Data: gilt 10Y/30Y, DMO auctions, basis · Coupling: master gate cho S57, S61, S66.

**S97 — Carry-Aware Sizing Overlay (Options)**
- Hypothesis: negative-carry per-diem là drag thực — overnight position scale theo roll cost; khi carry chống quá mạnh thì chuyển day-trade-only · Signal: annualized roll |cost| > 40bp chống hướng trade · Trade: size ×0.5 hoặc intraday-only version của cùng signal.
- Risk: bỏ overnight winners khi carry ngược tạm thời · Data: forward/swap points · Coupling: áp Family A/D.

**S98 — Conditional Trend-Day Probability Model (Regime)**
- Hypothesis: xác suất trend-day ước lượng được từ features trước NY-open: Asian-range tight + prior-day compression + event-on-calendar + London-directional open · Signal: probability score > ngưỡng (calibration chỉ để thiết kế; validate out-of-sample khi có data — giữ ít features) · Trade: score cao → bracket hai phía tại NY open; score thấp → range-fade; stop theo cấu trúc từng loại.
- Risk: probability model overfit nếu thêm features theo outcome · Data: M15 daily features + calendar · Coupling: S9 London-detector là input.

**S99 — Weekend-Gap Risk Overlay (Regime)**
- Hypothesis: gap-risk có điều kiện: trước Budget/election-weekend/MPC-Monday gap percentile cao hơn baseline — sizing Friday theo conditional percentile · Signal: weekend-risk score (event calendar + vol regime + positioning extreme) > ngưỡng · Trade: Friday 19:00 flat hoặc hedge bằng OTM strangle khi IV thấp; Monday 22:30 đánh giá với S16.
- Risk: options cost ăn margin nếu gap không đến thường xuyên · Data: calendar + historical gap distribution · Coupling: S45 tăng score.

**S100 — Meta-Composite Conductor (Regime)**
- Hypothesis: bất biến của lane — differential momentum (BoE–Fed path) + gilt regime + vol percentile là 3 trục quyết định family nào sống; conductor thay vì 100 signals chạy lạc loài · Signal: composite = sign(S39) + sign(S96) + bucket S91; ví dụ trạng thái Sep-2026 (USD-hawkish + gilt-stress + vol-high) → Family A short-side + Family F fiscal playbook + MR veto · Trade: allocation matrix; mọi thay đổi composite ghi log để tránh hindsight drift.
- Risk: chính composite parameters là chỗ overfit — nguyên tắc "đổi chỉ khi composite đổi", không tune theo backtest outcome · Data: tổng hợp module · Coupling: gate của toàn file.

---

## 3. Tổng hợp cho symbol

### 3.1 Top-10 ideas (ưu tiên nghiên cứu trước)

| # | Idea | Vì sao ưu tiên |
|---|---|---|
| 1 | **S96 Fiscal-Stress Regime Flag** | Kênh đặc trưng nhất của GBPUSD (không major nào có); đang ACTIVE trong Sep-2026 (gilt 10Y 5.378%, 30Y 5.92% — verified); là gate bảo vệ cho gần như mọi family khác |
| 2 | **S57 Fiscal-Event Gilt-Led Playbook** | Template 2022 + echo Sep-2026 đã verify; cơ chế kinh tế rõ (fiscal → gilt → risk premium); data khả dụng; giao dịch được ngay mùa Budget thu 2026 |
| 3 | **S38 Forced-Hike Scenario** | Đúng trạng thái hiện tại: CPI 3.1%↑ + gilt > 5% + BoE hold — thesis "BoE bị ép hike" có EV dương kỳ vọng và thời hạn rõ (MPC 05/11/2026 verified) |
| 4 | **S59 Fed–BoE Same-Week Stack** | Sep-2026 vừa diễn ra đúng template (Fed 16/09 hike, BoE 17/09 hold); recurring 3–4 lần/năm; kiểm định gọn bằng event-study |
| 5 | **S63 EURGBP Decomposition Router** | Cost thấp (3 cặp daily); điều kiện tiên quyết để mọi signal Cable được quy về đúng driver; giảm ảo tưởng "GBP mạnh/yếu" |
| 6 | **S61 Gilt 10Y Intraday Lead** | Cụ thể hóa kênh gilt xuống intraday — edge thời gian đo được bằng data 5 phút; chỉ bật trong flag S96 nên có gate rõ |
| 7 | **S21 London ORB (+S27 weekday gate)** | Bread-and-butter intraday; logic price discovery London; kiểm chứng nhanh, data rẻ; khớp vol-profile theo giờ của Cable |
| 8 | **S53/S15 CPI Size-Scaled Response** | UK CPI 07:00 là event đặc trưng (liquidity mỏng + BoE reaction function); cặp continuation/fade theo size surprise là hypothesis falsifiable gọn |
| 9 | **S82 USD-Basket Residual Reversion** | Stat-arb nền tảng cho "GBP-idio fair value"; tạo thước đo dùng chung cho S19/S83/S87; hedge-able; rủi ro mô tả được |
| 10 | **S100 Meta-Composite Conductor** | Khung ngăn 100 ideas tự giết nhau; mùa vụ regime Sep-2026 (hawkish-Fed + gilt-stress + vol-high) là test case sống |

Ghi chú phân bổ: top-10 có cấu trúc 3 lớp — (i) thesis vĩ mô đặc thù Anh (S38, S57, S59); (ii) cơ chế cấu trúc/microstructure (S21, S61, S63); (iii) hạ tầng đo lường & kiểm soát (S82, S96, S100). Layer (iii) nên xây trước vì nó là điều kiện để (i) và (ii) được đánh giá trung thực.

### 3.2 Bẫy overfitting đặc thù khi backtest GBPUSD

1. **Timezone/DST**: UK data 07:00 London, US data 13:30/14:00 ET; BST↔GMT đổi ngày *khác* US DST 2–3 tuần mỗi năm — cửa sổ lệch làm mọi session-boundary backtest sai nếu fix giờ UTC tĩnh. Dùng giờ exchange-local theo lịch DST từng năm.
2. **Event-time vs clock-time**: MPC 12:00, CPI 07:00 — daily-bar "ngày của CPI" nhòe effect; align theo event-timestamp M1/M5.
3. **Spread widening quanh event**: stop-order fill lúc 07:00:00 với spread bình thường là ảo tưởng — spike-spread 5–20 pip phút đầu. Mô phỏng spread theo thời gian hoặc dùng fill model bảo thủ.
4. **Ngày thống trị (outlier days)**: 2022-09 và vài ngày flash tạo toàn bộ "edge" của nhiều backtest fade/trend — dùng median trade, trimmed stats, out-of-sample theo *loại ngày* (fiscal-stress vs thường) chứ không chỉ random split.
5. **DXY circularity**: GBP 11.9% DXY — filter DXY cho Cable là tự tương quan; dùng EURUSD.
6. **COT look-ahead**: positions tính Thứ Ba, phát hành Thứ Sáu — backtest phải lag đúng bản release.
7. **Wednesday triple-swap**: daily-P&L của overnight family lệch 1 ngày/tuần nếu không tính roll đúng.
8. **ONS revisions & point-in-time consensus**: CPI/earnings/GDP revised; cần consensus point-in-time (archive) — nếu không, "surprise" là giả.
9. **Monday gap definition**: Friday-close vs Sunday-open phải thống nhất theo một venue; feed ghi NaN vs close-close tạo/khử "gap" giả.
10. **Regime segmentation đủ**: ít nhất 4 label (BoE/Fed cùng hướng, lệch hướng, fiscal-stress on/off) — pool toàn lịch sử sẽ fit vào trạng thái gần nhất (hiện nay gilt-stress).
11. **Vol-unit chuẩn hóa**: mọi threshold pip chuyển sang ATR/vol-unit trước khi so regime — nếu không backtest "tuned" cho một vol era.
12. **Triangular consistency**: backtest dùng 3 cặp phải check arbitrage-consistency của feed (S81) — sai lệch feed tạo alpha giả cho stat-arb.
13. **Multiple testing trên 100 ideas**: chính file này là 100 hypothesis — phase measurement phải có protocol trial-accounting (family-level gates giảm bậc tự do, hold-out theo thời gian, không retry cùng ý với threshold khác).

### 3.3 MUST-WATCH weekly macro checklist (Thứ Sáu trước tuần mới)

**Policy (bên Anh)**
- [ ] MPC calendar: kế tiếp **05/11/2026** (verified BoE schedule) — có MPR + presser 12:30
- [ ] OIS/SONIA implied path: xác suất hike/hold meeting kế tiếp; 1Y1Y dịch thế nào trong tuần (input S33/S37)
- [ ] Vote-split kỳ vọng vs thực tế kỳ trước (S52)

**Rates & fiscal (kênh đặc thù Anh)**
- [ ] Gilt 10Y & 30Y level + 20d change (mốc tham chiếu Sep-2026: 10Y ~5.38% đỉnh 19 năm; 30Y ~5.8–5.9% vùng 1998 — verified)
- [ ] 2s10s và 30Y−10Y steepening direction (phân loại growth vs fiscal)
- [ ] DMO auction calendar & kết quả gần nhất: bid-to-cover, tail (S77)
- [ ] Fiscal calendar: ngày Budget/Autumn Statement 2026 — **(cần kiểm chứng ngày chính thức)**; OBR forecast window; fiscal-rule headlines
- [ ] Rating agencies: outlook UK thay đổi chưa (unscheduled tail)

**Data UK tuần tới**
- [ ] CPI ngày/giờ 07:00 (headline + services) & consensus (S15/S53)
- [ ] Average earnings, claimant count/payrolls (series mới — nhớ veto S60 nếu noise cao)
- [ ] PMI flash 09:30 / monthly GDP 07:00 / retail sales
- [ ] Political radar: PM/Chancellor headlines, Treasury Committee (unscheduled)

**Policy & data (bên Mỹ — USD-common)**
- [ ] FOMC path sau hike 16/09/2026 (3.75–4.00%, vote 12–0, hawkish — verified): speakers, dot narrative, meeting kế tiếp **27–28/10** (verified calendar)
- [ ] US CPI & NFP calendar (13:30 UTC)

**Positioning & vol**
- [ ] COT GBP net-spec percentile (release Thứ Sáu; data Thứ Ba — S71–S75)
- [ ] 1M 25Δ risk-reversal & 1W ATM IV percentile (S73/S93/S95)
- [ ] Cable RV percentile + gilt-vol proxy (S91/S92)

**Regime flags tổng hợp**
- [ ] S96 fiscal-stress composite (gilt + auction + basis + steepening): BẬT/TẮT?
- [ ] S63 decomposition: tuần vừa rồi Cable move do USD-common hay GBP-idio?
- [ ] S100 conductor state: differential momentum + gilt regime + vol bucket → allocation tuần tới

**Execution housekeeping**
- [ ] Holiday lệch UK/US tuần tới (S46); month-end/quarter-end fix ngày nào (S43/S49); DST window đang ở trạng thái nào (bẫy 3.2.1)

### 3.4 Regime map Sep-2026 → allocation khuyến nghị (snapshot đầu ra của S100)

| Trục | Trạng thái verified 28/09/2026 | Ứng xử khuyến nghị |
|---|---|---|
| BoE–Fed differential momentum | USD-thuận (Fed hawkish-hike 16/09 vs BoE hold từ 12/2025); nhưng UK CPI 3.1%↑ tạo BoE-hike risk hai phía | Không closet-long carry; differential trades theo net-shift (S37), ưu tiên S38/S59 |
| Gilt regime | Stress cao (10Y 5.378% đỉnh 19 năm; 30Y 5.92% đỉnh 1998; auction vẫn hấp thụ — "premium cao" chưa phải "crisis") | S96 flag probable-ON (kiểm tra 2Y vs 30Y source); S57 standby cho Budget; MR-long bị veto |
| Vol regime | Cao (gilt-stress + event-dense tuần 14–18/09 vừa qua) | Family A short-side + Family F được ưu tiên; size ×0.75 theo S92 |
| Decomposition tuần qua | GBPUSD ~1.3486 (15/09) chịu áp lực phần lớn USD-lead (Fed repricing) — idio phần fiscal | Router S63: USD-driver → signal từ EURUSD, entry Cable; idio-burst → bật S61 |

Snapshot này là minh họa cách dùng conductor, không phải khuyến nghị giao dịch — mọi cấu hình phải qua phase measurement và gates của chương trình.

### 3.5 Câu hỏi nghiên cứu mở cho phase measurement (ưu tiên falsify)

1. Tỷ trọng phương sai USD-common vs GBP-idio của Cable theo tuần là bao nhiêu, và có ổn định qua các regime fiscal-stress on/off không? (nền cho S63/S82/S83)
2. Dấu quan hệ gilt-10Y-impulse → Cable có thực sự inverse trong regime Sep-2026, và đổi dấu khi gilt-move là 2Y-led (hawkish) hay không? (S61/S96)
3. Phân phối phản ứng CPI theo size surprise có còn "đường gãy" 0.2pp/0.3pp trên sample dài hơn không, hay đó là artifact của vài năm gần đây? (S15/S53)
4. Persistence post-MPC (S5/S51) sống bao lâu trung bình — 4 giờ, tới NY close, hay qua đêm? Có bất đối xứng hawkish/dovish không?
5. Lead-lag EURUSD → GBPUSD (S64) có lớn hơn friction thực tế (spread + slippage) đủ để ăn sống không, hay chỉ measurable chứ không tradeable?
6. COT percentile extreme (S71) trên GBP có cùng phân phối với EUR/JPY không — hay GBP có crowd-structure riêng do retail flow lớn hơn?
7. Asian-range fade (S11/S50) còn dương sau khi tính spread châu Á thực tế theo giờ không?
8. Monday gap (S16) có điều kiện hóa tốt hơn bởi political-calendar score (S99) hay bởi vol regime — kiểm định cả hai, chọn một.
9. Beta Cable/EURGBP–EURUSD band [0.75, 1.05] (S83) có ổn định khi ước lượng rolling 60d vs 120d không — nếu không, band là overfit.
10. Composite conductor (S100) khi chạy walk-forward trên lịch sử có giảm drawdown các family đơn lẻ không — nếu không cải thiện gì, conductor là phức tạp hóa vô ích.

### 3.6 Glossary nhanh (thuật ngữ dùng trong file)

| Thuật ngữ | Nghĩa trong ngữ cảnh lane GBPUSD |
|---|---|
| Cable | Tên thị trường của GBPUSD |
| Pip / pipette | 0.0001 / 0.00001 |
| ATR | Average True Range — đơn vị vol chuẩn hóa cho stop/target |
| BST/GMT | Giờ mùa hè/đông Anh — nguồn bẫy timezone (3.2.1) |
| SONIA / SOFR | Benchmark overnight GBP / USD — nền cho carry (S31) |
| OIS 1Y1Y | Kỳ vọng lãi suất forward 1 năm bắt đầu sau 1 năm — máy đo path kỳ vọng |
| Gilt | Trái phiếu chính phủ Anh; 2Y/10Y/30Y là các mốc tenor |
| DMO | UK Debt Management Office — tổ chức auction gilt |
| OBR | Office for Budget Responsibility — cơ quan dự báo tài khóa |
| MPC | Monetary Policy Committee của BoE (8 decision/năm) |
| MPR | Monetary Policy Report (quý, kèm presser) |
| LDI | Liability-driven investment — cấu trúc pension gây spiral 2022 |
| Cross-currency basis | Chi phí funding chéo — flag stress (S80) |
| WM/R 4pm fix | Fixing tham chiếu 16:00 London — flow tháng cuối (S43) |
| COT | Commitments of Traders (CFTC, futures positioning) |
| OI | Open Interest futures |
| RR 25Δ | Risk-reversal 25-delta — đo skew options |
| IV / RV | Implied vol / realized vol — so sánh cho regime options (S70/S93) |
| Idiosyncratic (idio) | Phần biến động riêng GBP sau khi tách USD-common |
| USD-common | Phần biến động USD chung cho mọi cặp XXX/USD |
| Trend-day | Ngày có hướng duy nhất, chiếm đa số daily range một session |
| Stop-hunt / sweep | Quét qua extreme để kích stop rồi đảo chiều (S90) |
| Whipsaw | Vào đúng hướng rồi bị cắt bởi pullback — kẻ thù trend system trong chop |
| Trial accounting | Quy ước chương trình: ghi nhận đúng số thử nghiệm để tránh multiple-testing bias (3.2.13) |

---

### Nguồn verify (truy cập 2026-09-28)

- Bank of England — official Bank Rate database (Bank Rate 3.75% hiệu lực 18/12/2025, chuỗi thay đổi gần nhất) & trang MPC dates (hold 17/09/2026; hold 30/07 & 18/06/2026; kế tiếp 05/11/2026; trang cập nhật 21/09/2026): bankofengland.co.uk
- Federal Reserve — FOMC calendar 2026 & Monetary Policy Statement 16/09/2026 (hike 25bp → 3.75–4.00%, vote 12–0, "The Committee will deliver price stability"): federalreserve.gov
- Reuters — "UK 10-year gilt yield hits new 19-year high" (10/09/2026; 5.378%); Reuters markets page (UK 10Y ~5.405% intraday, LSEG delayed)
- WSJ/Morningstar — 30Y gilt 5.921% đỉnh 02/09/2026 (cao nhất từ 1998), ~5.813% sau đó; FT — auction 30Y 08/09/2026 tại 5.82%, demand mạnh
- House of Lords Library — UK fiscal outlook Sep 2026 (cảnh báo headroom xói mòn)
- Forex.com / Vantage / Cambridge Currencies / Currency Solutions / Statista / Investing.com (qua web search) — GBPUSD ~1.3486 (15/09/2026, vùng hỗ trợ 1.35/1.33); UK CPI Aug 3.1% (Jul 2.9%); BoE forecast CPI ~3.2% Oct–Nov; UK payrolls −26k; week-range 1.33–1.365. Các con số thị trường này đối chiếu multi-source qua search nhưng **(cần kiểm chứng lại)** trước khi dùng làm input chính thức trong artifact downstream.

*Hết tài liệu. 100 ideas = 100 hypothesis chưa kiểm định — "Missing evidence is NOT_RUN, never inferred PASS."*
