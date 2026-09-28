# NZDUSD — Deep Dive & 100 Strategy Ideas

- Lane: NZDUSD · Program: `FOREX-UNIFIED-STRATEGY-BRAINSTORM-V1` · Ngày: 2026-09-28
- Chế độ: **knowledge-only brainstorm** — không backtest, không data, không code. Mọi hypothesis ở đây đều `NOT_RUN` cho tới khi được trial theo quy trình chương trình.
- Kiểm chứng thời điểm (WebSearch 2026-09-28): RBNZ, Fed, RBA, GDT, macro NZ — xem mục 1.0. Cái gì chưa chắc đánh dấu **(cần kiểm chứng)**.
- Quy ước: mọi correlation / con số thống kê lịch sử là "giá trị điển hình theo kiến thức chuyên môn" (prior), CHƯA đo lại trên data của repo. Universe tham chiếu: EURUSD, GBPUSD, USDCAD, USDJPY, AUDUSD, NZDUSD, USDCHF, XAUUSD, XAGUSD, BRENT, WTI, NATGAS.

### Cách sử dụng file này

- **Đọc theo thứ tự**: 1.0 (snapshot macro đã kiểm chứng) → 1.2 (điểm đặc thù) → 1.6 (họ strategy hay chết) → Phụ lục A (chỉ mục nhanh 100 ý) → quay lại mục 2 đọc chi tiết các ý quan tâm.
- **Ranh giới đã tuân thủ**: knowledge-only — không backtest, không chạy code, không tải data, không git; mọi tuyên bố dạng "có edge" đều là hypothesis `NOT_RUN`.
- **Tương thích lane khác**: mục 1.0 đã đối chiếu lane EURUSD (Fed hike 16/09/2026) và lane AUDUSD (RBA 4.35%, họp 28–29/09); nếu hai lane kia re-verify khác kết quả thì snapshot này phải cập nhật theo.
- **Khi được cấp quyền chạy data**: bắt đầu bằng 3.4 (đo lường nền) — không nhảy thẳng vào backtest 100 ý; thứ tự ưu tiên validate ở 3.6.
- **Người review nên tra chéo**: các mục đánh dấu **(cần kiểm chứng)** liệt kê tập trung ở dòng cuối file.

## 1. Bản chất instrument

### 1.0 Trạng thái macro đã kiểm chứng (snapshot 2026-09-28)

| Chủ đề | Trạng thái đã xác minh | Ghi chú |
|---|---|---|
| RBNZ OCR | **2.75%** sau hike 25bp ngày **02/09/2026** (lần 2 trong 2026; trước đó hike 08/07/2026 lên 2.50%, và giữ 2.25% từ sau đợt cut đến 11/2025) | MPS 02/09/2026 cho thấy market pricing dịch thêm ~+35bp; hike vì inflation sticky (~3.9–4.1%) trên band mục tiêu 1–3% |
| Fed | Hike 25bp ngày **16/09/2026** lên **3.75–4.00%** — lần đầu sau 3+ năm, Chair mới **Kevin Warsh**, 16/18 officials kỳ vọng thêm hike tới cuối năm | Trùng khớp verification của lane EURUSD |
| RBA | Cash rate **4.35%** (giữ tại họp 08/2026); họp **28–29/09/2026**: 4 major banks + market fully priced hike 25bp → 4.60%; nhưng CPI Q2 AU mềm (công bố ~19/09) làm suy yếu kỳ vọng | **Kết quả chưa công bố tại thời điểm viết (cần kiểm chứng)** |
| Carry differential | Fed − RBNZ ≈ **+100–125bp nghiêng USD** → NZD hiện là **funding leg**: lãi swap âm với long NZDUSD | Cấu trúc headwind cho mọi hệ long-bias |
| GDT dairy | WMP dao động **US$3,585–3,910/MT** trong tháng 9: event 01–02/09 WMP −0.1% còn $3,585; ~15/09 GDT index −1.1%,均价 $3,868/t; một event khác index +2.3% với WMP +3.0% → $3,591 | Nhịp auction chính 2 tuần/lần + **GDT Pulse** hàng tuần (event nhỏ) |
| Fonterra | Nâng forecast Farmgate Milk Price 2026/27: midpoint **$9.25 → $9.50/kgMS** (range $8.50–10.50) | Kênh thu nhập nông nghiệp đang cải thiện |
| NZ economy | Recovery **hai tốc độ**: GDP +0.5% (Q4'25), +0.8% (Q1'26, ~1.5% y/y, được chỉnh tăng); Treasury kỳ vọng ~2.3% FY tới 6/2027; **unemployment 5.6%** Q2'26 (đỉnh 11 năm); inflation ~3.9%, household expectations ~5% | Growth tới nhưng labour market và inflation chưa lành |
| Giá | NZDUSD mở tháng 9 ~0.59 → **vỡ 0.5800** giữa tháng → **~0.572–0.578** (~18/09); support kỹ thuật ~0.5625 | Driver: USD mạnh + UST yields tăng sau Fed 16/09 |

Nguồn kiểm chứng (WebSearch 28/09/2026): rbnz.govt.nz (OCR/MPS), globaldairytrade.info + BusinessDesk/AHDB (GDT), MarketScreener (Fonterra FGMP), wwlp.com/finance-commerce.com (Fed), afr.com/canstar.com.au/stonex.com (RBA), StatsNZ/1News/OECD/ASB/Westpac (NZ macro), mitade/tradingview (mức giá). Toàn bộ là thời điểm — sẽ cũ nhanh, phải re-verify trước khi dùng trong bất kỳ cycle nào.

### 1.1 Microstructure & sessions

- Phân loại: **minor pair**. NZD đứng ở một bên của ~2% doanh số FX toàn cầu (BIS Triennial 2022) — xếp sau AUD/CHF/CAD; con số BIS 2025 **(cần kiểm chứng)**.
- Chi phí: retail ECN raw spread ~0.6–1.2 pip + commission; all-in round-trip thường **1.5–2.5 pip** (so EURUSD ~0.3–0.8). Slippage stop-loss ~1.5–2× major trong phiên mỏng. Đây là biến số sống còn cho mọi hệ tần suất cao.
- Quote: pip = 0.0001, báo giá 5 số lẻ; ATR(D1) điển hình ~55–75 pip, 2026 nới rộng do differential rộng + Fed hawkish (cần đo lại).
- Sessions (GMT, lệch theo DST): Wellington mở ~19:00–20:00; Sydney ~21:00–22:00; Tokyo 00:00; London 07:00–08:00; NY 12:00–13:00. Liquidity sâu nhất **London–NY overlap 12:00–16:00 GMT**.
- Sách mỏng nhất: 17:00–19:00 GMT (post-NY, pre-Wellington) và một phần Asia lunch. Đây là khung stop-hunt quanh số tròn 0.XX00/0.XX50 hay gặp nhất.
- Đặc thù "morning NZ": RBNZ (~01:00–02:00 GMT), GDT (~00:00–01:00 GMT), data NZ (~21:45–22:45 GMT ngày trước theo UTC) đều rơi vào book mỏng → cú move bị amplify so với cùng tin ở USD-leg giờ Mỹ.
- Rollover/swap 17:00 NY, Wednesday 3×. Với differential âm sâu (2026), long NZDUSD trả swap đáng kể — phải tính vào expectancy của mọi hệ giữ qua đêm.

### 1.2 Điểm ĐẶC BIỆT riêng NZDUSD

1. **Dairy terms-of-trade (đặc thù nhất trong các major/minor)**: NZ là nhà xuất khẩu sữa lớn nhất thế giới; dairy ~1/4–1/3 kim ngạch xuất khẩu. GDT (Fonterra) định giá WMP/SMP **2 tuần/lần** — một driver giá rời rạc, không phải futures liên tục. Chuỗi WMP → Farmgate milk price → thu nhập nông nghiệp → GDP/ToT → NZD. Không cặp major nào có driver soft-commodity rời rạc kiểu này, tạo "nhịp vol 2 tuần" phủ lên nhịp dữ liệu quý.
2. **Thanh khoản mỏng**: mọi thứ đắt hơn (spread, slippage, gap) — nhưng mặt trái là inefficiency nhỏ tồn tại lâu hơn, đáng khai thác bằng tần suất vừa/thấp chứ không phải HFT retail.
3. **"Nửa AUD, nửa USD-cycle"**: tương quan AUDUSD rất cao (cùng commodity/risk bloc, cùng USD quote) nhưng central bank khác nhau (RBA vs RBNZ) và dairy ≠ iron ore. **AUDNZD** là cross thanh khoản nhất của NZD — "vehicle sạch" để tách phần NZ-specific khỏi phần commodity/USD chung.
4. **RBNZ dám đi sớm**: lịch sử là CB tiên phong mỗi chu kỳ (hike đầu 2014, hike đầu thế giới 10/2021, cut nhanh 2024–25); 7 OCR reviews/năm + MPS quý. Năm 2026: RBNZ hike lại từ 7/2026 nhưng Fed cũng vừa bắt đầu hike (9/2026) và nhanh hơn về mức → differential mở nghiêng USD.
5. **Risk-sentiment beta cao**: NZD là một trong các proxy risk-on của FX (cùng AUD, CAD); trong risk-off NZD thường bị bán mạnh hơn cả AUD → AUDNZD có xu hướng lên trong panic.
6. **Economy nhỏ, news tập trung**: một hãng (Fonterra) + một ngành (dairy) đủ lớn để corporate news移动 ngoại tệ — hiếm gặp ở major.

### 1.3 Tin tức/sự kiện ảnh hưởng

#### Scheduled (chu kỳ cố định)

| Sự kiện | Nhịp | Giờ (GMT, ~tùy DST) | Transmission channel |
|---|---|---|---|
| RBNZ OCR + MPS | 7 lần/năm (MPS theo quý) | ~01:00–02:00 | Policy rate → OIS/2y swap → differential → NZD trực tiếp; MPS track path → kỳ vọng dài hạn |
| GDT auction (chính) | 2 tuần/lần (thường Thứ 3) | ~00:00–01:00 | WMP → Farmgate milk price → thu nhập dairy/ToT → NZD (T+0 vài phút tới T+5 ngày) |
| GDT Pulse | hàng tuần (Thứ 4) | ~01:00–02:00 | Khối lượng nhỏ, tín hiệu yếu hơn, chủ yếu xác nhận xu hướng GDT chính **(cần kiểm chứng giờ)** |
| NZ CPI (quý) | giữa quý sau | ~21:45–22:45 | Inflation → kỳ vọng OCR → NZD; surprise lớn đổi cả path |
| NZ HLFS employment (quý) | giữa quý | ~21:45–22:45 | Unemployment + hourly wages → underlying inflation → RBNZ |
| NZ GDP (quá khú) | giữa–cuối tháng | ~21:45–22:45 | Growth → OCR path; ít nhạy hơn CPI |
| NZ trade balance / export values | hàng tháng | ~21:45 | Dairy export values → xác nhận ToT trend |
| ANZ business confidence, NZIER QSBO | tháng/quý | sáng NZ | Forward-looking activity → kỳ vọng RBNZ |
| Fonterra FGMP revision | ~2–3 lần/năm | sáng NZ | Định hướng thu nhập nông nghiệp cả season → NZD multi-week |
| US: FOMC, NFP, CPI, ISM, retail | tháng | 12:30/14:00/18:00 | USD-leg — chiếm phần lớn variance ngày thường |
| RBA + AU CPI/GDP | ~8 họp/năm | ~04:30–05:30 | AUD gravity → NZD đồng hướng một phần; divergence tạo sóng AUDNZD |
| China PMI, trade, stimulus headlines | tháng | ~01:00–02:00 | Cầu hàng NZ (dairy, gỗ, du lịch, education) → NZD |

#### Unscheduled (kèm transmission channel)

- **RBNZ verbal intervention** / phát biểu ngoài lịch: kênh kỳ vọng lãi suất (OIS repricing trong phút).
- **FX intervention hiếm** (lịch sử 2007, đầu thập niên 2000): spot tức thời, thường mean-revert chậm — rủi ro cho hệ short-bias khi NZD quá yếu.
- **China stimulus / stress headlines**: risk + cầu commodity → NZD (kênh trade exposure); thường xảy ra giờ Asia mỏng → move amplified.
- **Risk-off global** (VIX spike, credit event, geopolitical): deleveraging carry, NZD bị sell với beta cao hơn AUD.
- **Thời tiết/thiên tai**: drought (El Niño) giảm milk production → giá GDT tăng (kênh ToT); earthquake (2010, 2016 Kaikoura) → GDP/RBNZ easing (kênh policy).
- **Biosecurity scare** (foot-and-mouth): rủi ro xuất khẩu dairy → NZD risk premium tức thời.
- **M&A cross-border có leg NZD**, issuance NZGB, equity flow: kênh cầu-cầu ngoại tệ tạm thời, thường revert.
- **US politics / Fed Chair (mới: Kevin Warsh) surprise**: USD-leg, lan nhanh qua DXY.
- **Dairy futures (NZX/CME) pre-pricing GDT**: thông tin auction có thể "leak" trước → kiểm trước khi trade straddle GDT.
- **NZ politics**: Budget (thường tháng 5), coalition news, chính sách immigration/housing → kỳ vọng fiscal/RBNZ.

### 1.4 Thông số ảnh hưởng (drivers, xếp theo ước tính quan trọng)

1. **USD-leg / DXY / UST yields** — phần lớn variance ngày thường; mọi hệ NZDUSD thực chất đang mang một short-USD exposure ngầm.
2. **RBNZ−Fed differential & path** (2y swap spread, OIS meeting-date): hiện **−100~−125bp nghiêng USD** — headwind cấu trúc với NZD cho tới khi path đổi.
3. **WMP/GDT dairy** — driver đặc thù, tác động multi-day, bị amplify khi rơi vào session mỏng.
4. **Risk sentiment** (VIX/SPX/credit): beta dương risk-on, phi tuyến ở tail (risk-off đau hơn).
5. **AUD gravity & AUDNZD**: AUD dẫn một phần ở cấp độ cấu trúc; RBA−RBNZ divergence thể hiện sạch trên cross.
6. **China demand & commodity complex**; terms-of-trade (dairy giá trị so dầu nhập).
7. **NZ domestic data** (CPI > employment/wage > GDP) — chủ yếu qua kênh kỳ vọng RBNZ.

### 1.5 Correlation map (daily-return; "giá trị điển hình theo kiến thức", CHƯA đo — NOT_RUN)

| Symbol | Corr điển hình với NZDUSD | Phân rã nhân tố |
|---|---|---|
| AUDUSD | +0.80 … +0.92 | Commodity bloc + risk + cùng USD quote; cao nhất universe; chênh lệch phần còn lại = dairy + RBA/RBNZ |
| EURUSD | +0.45 … +0.70 | Chủ yếu USD-leg; phần riêng euro nhỏ |
| GBPUSD | +0.40 … +0.65 | USD-leg; UK idiosyncratic chiếm phần riêng lớn hơn euro |
| USDCAD | −0.55 … −0.75 | USD-leg âm; phần commodity/risk của CAD triệt tiêu một phần |
| USDCHF | −0.45 … −0.70 | USD-leg âm + CHF risk-off đối xứng NZD risk-on (cộng synergistic) |
| USDJPY | −0.20 … −0.50, bất ổn | USD-leg âm nhưng risk-on đẩy cùng chiều → net thấp, đổi dấu theo regime |
| XAUUSD | +0.35 … +0.60 | Anti-USD + real rates; gold risk-off vs NZD risk-on triệt tiêu một phần |
| XAGUSD | +0.45 … +0.70 | Công nghiệp + risk-on mạnh hơn gold, cùng anti-USD |
| BRENT | +0.25 … +0.50 | Risk appetite; NZ nhập khẩu dầu nên có chút ToT ngược |
| WTI | +0.25 … +0.45 | Tương tự Brent, thưa hơn |
| NATGAS | −0.10 … +0.15 | Gần 0; idiosyncratic thời tiết Mỹ, không có kênh truyền tới NZ |

Breakdown / lưu ý sử dụng:

- **Regime dependence**: trong đợt Fed-hawkish (như 9/2026), USD-leg nuốt phần cross → corr với EURUSD/AUDUSD tăng vọt; trong dairy-shock, corr(NZDUSD, AUDUSD) rơi. Ngưỡng vận hành: corr 60d < ~0.7 = "NZ-idiosyncratic regime" (cơ sở cho S70).
- **AUDNZD** = NZDUSD/AUDUSD: là cross sạch nhất để tách NZ story; nhớ cross này không có USD-leg nên vol profile khác hẳn NZDUSD.
- **Diversification**: 3 cluster chính — USD-cluster (EURUSD/GBPUSD/AUDUSD/NZDUSD đồng pha), funding (JPY/CHF), commodity complex (Brent/WTI/XAG đồng pha yếu). NATGAS gần orthogonal.
- **CẢNH BÁO**: đây là prior không phải đo đạc; mọi portfolio build trên universe này phải re-measure rolling correlation trên data repo trước khi tin.

### 1.6 Note trung thực — họ strategy hay CHẾT trên NZDUSD

1. **HFT/scalping tần suất cao**: chi phí RT 1.5–2.5 pip vs biên độ trung bình nhỏ → edge bị ăn sạch; chỉ khả thi với microstructure data tốt + rebate, ngoài scope retail.
2. **Mean-reversion không event-filter**: RBNZ ~02:00 GMT, GDT ~01:00 GMT, US data 12:30 GMT — MR đứng qua event sẽ ăn gap có/không cảnh báo.
3. **Breakout stop chặt trong Asia thin book**: whipsaw + stop-hunt quanh số tròn; cần stop theo ATR và giờ liquidity-aware.
4. **Grid/martingale**: rollover spikes (17:00 NY), Sunday gap, GDT surprise → drawdown sâu hơn mô phỏng vì book mỏng.
5. **Carry dài "vì truyền thống"**: 2026 differential âm sâu — long NZDUSD vừa âm swap vừa ngược headwind macro; carry giờ là short-biased, nhưng short-carry dễ bị risk-on squeeze ngược.
6. **Copy tham số từ AUDUSD**: dairy ≠ iron ore, RBA ≠ RBNZ — hai hệ lệch pha đủ để parameters AUD overfit phá tài khoản NZD.
7. **Short options premium không kiểm soát size**: tail GDT/RBNZ trong book mỏng; IV spike + assignment rủi ro lớn hơn major.
8. **Seasonality mỏng mẫu**: ~30 obs/tháng trong 20 năm, CI rất rộng; chỉ dùng khi neo được cơ chế kinh tế (dairy flush, fiscal year).
9. **Backtest dùng mid-quote**: over-report nghiêm trọng trên NZD hơn major; phải mô hình spread theo giờ + slippage stop; không tin fill giả 17:00–19:00 GMT và Sunday open.

### 1.7 Lịch sử regime tiêu biểu (prior từ kiến thức — con số cần re-verify khi dùng; "cần kiểm chứng")

- 2013–2014: RBNZ hike đầu chu kỳ toàn cầu, WMP đỉnh ~US$5,000/MT, NZDUSD đỉnh ~0.88 (7/2014).
- 2014–2015: **dairy crash** (WMP về ~US$2,000/MT) + RBNZ cut + USD strong → NZDUSD rơi ~25% trong ~1 năm — minh họa kênh dairy-ToT mạnh nhất lịch sử gần.
- 2017–2018: range ~0.68–0.74; AUDNZD trend vì RBA–RBNZ divergence — bằng chứng cho family stat-arb.
- 2020–2021: COVID low ~0.5470 (3/2020) rồi V-recovery lên ~0.74 (2021) trên risk-on + RBNZ hike đầu thế giới (10/2021).
- 2022–2023: Fed aggressive → NZDUSD ~0.55–0.62 dù RBNZ cũng hike tới OCR đỉnh 5.5% — minh họa USD-leg nuốt phần domestic.
- 2024–2025: RBNZ cut nhanh 5.5% → 2.25% (đến 11/2025), NZ recession 2024–25.
- 2026: recovery hai tốc độ; RBNZ hike lại (7 và 9/2026) nhưng Fed hike lại (9/2026) với mức cao hơn → NZDUSD trượt về ~0.57. Bài học xuyên suốt: **relative policy + dairy quyết định phần NZ-specific; USD-leg quyết định phần còn lại.**

### 1.8 Câu hỏi mở cần data kiểm chứng (chỉ khi được phép chạy data)

- Rolling corr 60d (NZDUSD, AUDUSD) hiện ở đâu so ngưỡng 0.7 — quyết định meta-allocator S70 route vào cụm nào.
- Implied vol quanh OCR so với realized-conditional — quyết định S92 khả thi; đồng thời xác nhận venue có options NZDUSD hay không (nhiều venue retail không có).
- Spread theo giờ thực tế của venue dự định (24×7) — đặt trần tần suất cho toàn bộ book.
- GDT results archive kéo dài bao xa với đầy đủ WMP avg price (USD/MT) + quantity sold (từ ~2008) — cỡ sample cho S56/S61.
- COT disaggregated NZD có từ khi nào — z-score 3 năm của S71 cần tối thiểu 5+ năm dữ liệu.
- Forward points/swap lịch sử của broker — điều kiện sống còn cho S36 và wrapper S49.
- Dairy futures (NZX/CME) khả dụng tới đâu — cho pre-pricing gate của S25.
- Có series Farmgate milk price forecast đầy đủ (Fonterra archive) — cho S57.

## 2. 100 strategy ideas

Template mỗi ý: **S<n> — tên (family)** — Hypothesis · Signal · Trade · Risk · Data · Coupling. Mọi ngưỡng số là **điểm khởi điểm để tối ưu**, không phải khẳng định đã test — tất cả `NOT_RUN`. Ngưỡng "đổi con số" không tạo ý mới; 100 ý dưới đây khác nhau về cơ chế.

### 2.0 Cách đọc template

- **Hypothesis** — cơ chế kinh tế một câu: tại sao edge này tồn tại trên NZDUSD chứ không phải noise.
- **Signal** — thứ đo được khách quan (chỉ báo, ngưỡng, thời điểm); không dùng từ mơ hồ như "mô hình đẹp".
- **Trade** — sketch entry/exit/stop đủ để ai khác tái hiện được logic, chưa phải spec đầy đủ.
- **Risk** — cái giết strategy (không phải rủi ro chung chung, mà là điều kiện cụ thể làm edge mất).
- **Data** — dữ liệu tối thiểu cần có trước khi dám nói "đã test".
- **Coupling** — yếu tố ngoài cùng chiều (gate) giúp tăng tin cậy, hoặc ràng buộc với ý khác.
- Quy ước validate: mỗi ý là một trial riêng theo accounting của chương trình; **nghiêm cấm** gộp 100 ý thành một backtest khổng lồ rồi chọn top — đó là đường nhanh nhất tới overfit selection.

### Family 1 — Trend/Momentum (S1–S10)

Nền kinh tế chung: dollar-cycle và relative-policy tạo xu hướng bền ở tần suất ngày/tuần; NZDUSD trend thường bị dẫn bởi USD-leg nên cần gate điều kiện.

**S1 — Daily EMA-stack trend ride (Trend/Momentum)** — Hypothesis: khi ba EMA D1 xếp cùng hướng, dòng vốn theo differential đang định giá một chiều và pullback là cơ hội tiếp trend. · Signal: D1 EMA20>EMA50>EMA200 (long) hoặc đảo ngược (short); giá cùng phía EMA20.
· Trade: entry pullback chạm EMA20; stop 1.5×ATR(14) qua EMA50; trailing theo EMA20. · Risk: chop khi differential đi ngang; whipsaw quanh EMA. · Data: D1 OHLC. · Coupling: 2y NZ-US swap spread cùng dấu tăng hiệu quả.

**S2 — Donchian 20/55 breakout (Trend/Momentum)** — Hypothesis: breakout kênh đa ngày chọn lọc được shift regime chứ không phải noise. · Signal: D1 close ngoài kênh 20d (entry) / 55d (xác nhận strong).
· Trade: stop-order theo close-based entry; stop mép trong kênh +1×ATR; target 2×ATR hoặc trailing kênh 10d; skip tín hiệu trong 2 ngày trước RBNZ/GDT. · Risk: false break phiên mỏng — chỉ dùng close D1, không dùng poke intraday. · Data: D1 + event calendar. · Coupling: DXY break ngược dấu cùng lúc thì tăng tin cậy.

**S3 — ADX-filtered Chandelier trend (Trend/Momentum)** — Hypothesis: chỉ đi trend khi trend có thật (ADX cao) tránh trả phí chop. · Signal: ADX(14) D1 >25 và rising; hướng theo DI+/DI−.
· Trade: entry breakout 5d high khi điều kiện ADX đạt; Chandelier stop 3×ATR; exit khi ADX<20. · Risk: ADX lag muộn vào cuối trend. · Data: D1. · Coupling: VIX<20.

**S4 — 3M/12M time-series momentum (Trend/Momentum)** — Hypothesis: FX nhỏ có autocorrelation dương ở tần suất tháng (dollar-cycle chậm). · Signal: dấu tổng return 63 ngày và 252 ngày.
· Trade: re-balance hàng tháng: hai khung cùng dấu giữ full size, lệch dấu nửa size; không stop cố định, exit khi đổi dấu. · Risk: đảo regime mạnh (Fed pivot) đốt momentum cả hai khung. · Data: D1 ≥5 năm. · Coupling: differential momentum cùng chiều.

**S5 — NZD relative-strength gate vs commodity bloc (Trend/Momentum)** — Hypothesis: long NZDUSD thắng suất cao nhất khi NZD là đồng mạnh nhất bloc (thay vì chỉ nhờ USD yếu). · Signal: rank 20d return của NZD/AUD/CAD vs USD.
· Trade: chỉ long khi NZD rank #1, chỉ short khi rank #3; size theo khoảng cách rank. · Risk: khi cả bloc đồng pha thì rank nhiễu. · Data: AUDUSD, USDCAD, NZDUSD D1. · Coupling: hướng GDT cùng dấu.

**S6 — TWI-proxy trend alignment (Trend/Momentum)** — Hypothesis: RBNZ và nhà quản trị rủi ro theo dõi TWI; NZDUSD thường tuân theo trend TWI tổng thể. · Signal: synthetic TWI từ weights minh bạch (AUD ~30%, USD ~20%, EUR ~20%, JPY ~10%, CNY ~10%), re-weight hàng năm.
· Trade: trade NZDUSD cùng hướng trend TWI D1; nếu NZDUSD lệch hướng TWI quá 5 ngày → cắt. · Risk: weights sai làm proxy lệch. · Data: 5–6 cặp D1. · Coupling: commentary TWI của RBNZ.

**S7 — Heikin-Ashi weekly persistence + H1 trigger (Trend/Momentum)** — Hypothesis: chuỗi nến HA tuần đồng màu xác nhận trend sạch, còn H1 cho giá vào tốt. · Signal: ≥3 nến HA tuần đồng màu + H1 pullback về EMA20(H1) theo hướng đó.
· Trade: entry nến H1 reversal tại EMA; stop dưới swing H1; trailing theo đổi màu HA tuần. · Risk: đổi màu tuần giữa chừng. · Data: W1 + H1. · Coupling: không bắt buộc.

**S8 — Volatility-normalized momentum (Trend/Momentum)** — Hypothesis: momentum đo bằng ATR-units có signal-to-noise tốt hơn đo bằng pip (thang đo ổn định qua regime vol). · Signal: mom20 = (close−close[20]) / (ATR14×√20); vượt +1 long, dưới −1 short.
· Trade: pyramid mỗi lần vượt ±2; exit khi về 0. · Risk: vol regime đổi khiến thang đo dịch → re-estimate ATR rolling. · Data: D1. · Coupling: không bắt buộc.

**S9 — Trend-pullback continuation (Trend/Momentum)** — Hypothesis: trong D1 uptrend, dip 2–3 ngày về EMA20 là tiếp trend chứ không phải đảo chiều. · Signal: điều kiện trend của S1 đạt + RSI(2)<25 (hoặc >75 cho short).
· Trade: buy tại close ngày RSI reset; exit khi RSI(2)>70 hoặc close <EMA50; stop 1×ATR. · Risk: dip thành break trend khi có event ác → exclude 1 ngày quanh GDT/RBNZ. · Data: D1 + calendar. · Coupling: hướng dairy cùng chiều.

**S10 — Trend committee ensemble vote (Trend/Momentum)** — Hypothesis: bình chọn đa hệ thống giảm variance nhưng giữ edge trend. · Signal: ba hệ (EMA stack, Donchian, momentum 20d) trên H4+D1 vote {−1,0,+1} hằng ngày.
· Trade: |sum|≥2 full size theo dấu; |sum|=1 nửa size; 0 flat. · Risk: các hệ tương quan cao trong crash → committee tự cô lập, cần vol-target wrapper. · Data: D1/H4. · Coupling: regime gate S91.

### Family 2 — Mean-reversion (S11–S20)

Nền kinh tế chung: không có dòng tin mới,dealer hedging và thanh khoản phiên kéo giá về giá trị vừa; NZDUSD có "drift session mỏng" riêng thích hợp fade — nhưng event 2 tuần/lần (GDT) và quý (CPI/OCR) là kẻ thù tự nhiên.

**S11 — Bollinger z-score fade D1 (Mean-reversion)** — Hypothesis: không event, biến động vượt ±2.5σ phần lớn snapback khi thanh khoản quay lại. · Signal: %B(20, 2.5) ngoài rìa + calendar trống 24h.
· Trade: fade về SMA20; stop 0.75×ATR ngoài cực; time-stop 5 ngày. · Risk: trend mạnh đi liên tục ngoài band. · Data: D1 + calendar. · Coupling: Hurst<0.45 (S19).

**S12 — RSI(2) range-bound fade (Mean-reversion)** — Hypothesis: trong range (giá trong dải EMA200±1×ATR), cực RSI(2) revert nhanh. · Signal: |price−EMA200|<1×ATR và RSI(2)≤5 / ≥95.
· Trade: fade; target EMA5; stop 0.6×ATR; tự tắt khi giá thoát dải 2 ngày. · Risk: breakout thật khỏi range. · Data: D1. · Coupling: flat trước event.

**S13 — Asia-session overshoot fade (Mean-reversion)** — Hypothesis: drift late-NY/Asia trong book mỏng thường over-extend rồi hồi khi London vào. · Signal: move 18:00–06:00 GMT >1.5×ATR(Asia 20 phiên).
· Trade: fade ngay khi London mở với volume xác nhận; target 50% của move; stop new extreme +0.3×ATR. · Risk: move thật do tin China/NZ → news gate bắt buộc. · Data: H1 + news feed. · Coupling: tránh sáng có GDT.

**S14 — Anchored-VWAP reversion intraday (Mean-reversion)** — Hypothesis: quanh VWAP phiên, dealer hedging tạo trường hấp dẫn. · Signal: H1 lệch VWAP (anchor NY open) >1.8σ intraday.
· Trade: fade về VWAP; stop 0.5×ATR(H1); chỉ hoạt động 12:00–17:00 GMT. · Risk: trend-day không revert. · Data: H1/M15 + volume. · Coupling: tránh 12:30 US data.

**S15 — AUD-residual reversion (Mean-reversion)** — Hypothesis: phần NZ-specific (residual của NZDUSD vs β·AUDUSD) có xu hướng revert vì arbitrage cross hoạt động. · Signal: residual hồi quy 21d, z>±2.
· Trade: fade residual về 0 bằng NZDUSD (hoặc AUDNZD cho sạch hơn); stop z±3; time-stop 4 ngày. · Risk: event RBA/RBNZ đổi beta giữa chừng. · Data: AUDUSD + NZDUSD D1. · Coupling: không trade trong tuần có họp RBA/RBNZ.

**S16 — GDT overshoot fade (Mean-reversion)** — Hypothesis: phản ứng WMP quá mức so với quy mô kinh tế (Δ giá sữa ≤1.5% ~ nhỏ so GDP) thường retrench. · Signal: NZD di chuyển sau GDT >1.2×ATR nhưng ΔWMP chỉ ±1.5% (nhỏ).
· Trade: fade nửa size sau 2 giờ; target pre-event price; stop pre-GDT high/low. · Risk: GDT trùng US event cùng chiều. · Data: GDT results + M15. · Coupling: OIS không đổi.

**S17 — Round-number rejection fade (Mean-reversion)** — Hypothesis: 0.XX00 là magnet/barrier trong book mỏng; wick rejection là footprint của dealer. · Signal: H1/H4 wick ≥1.2× body tại mức 00 kèm volume spike giờ mỏng.
· Trade: entry khi re-break fail; stop qua extreme wick +2 pip; target 0.5×ATR. · Risk: breakout thật theo momentum. · Data: H1 + volume. · Coupling: option expiry (S95).

**S18 — Weekend gap fade (Mean-reversion)** — Hypothesis: gap Monday Wellington do close mỏng thường fill vì không có flow underlying. · Signal: |gap| >0.6×ATR(D1) và không event cuối tuần.
· Trade: fade từ London Monday; target Friday close; stop thêm 0.5×gap. · Risk: gap có lý do (hội nghị CB, chiến sự) → tin gate. · Data: W1 open/close + news. · Coupling: S48 holiday version.

**S19 — Hurst-regime MR gate (Mean-reversion)** — Hypothesis: MR chỉ có edge khi chuỗi anti-persistent; đo trực tiếp thay vì giả định. · Signal: rolling 120d Hurst <0.45.
· Trade: bật các ý MR (S11/12/14/16) chỉ trong regime này; ngoài ra tắt toàn bộ MR book. · Risk: Hurst lag và dao động quanh 0.5. · Data: D1. · Coupling: ATR percentile (S91).

**S20 — No-news vol-spike snapback (Mean-reversion)** — Hypothesis: cú vol lớn KHÔNG do event (liquidation/flow kỹ thuật) hồi nhanh hơn event-move. · Signal: daily TR >2.5×ATR20 và calendar trống.
· Trade: fade 30% move của giờ đầu vào cuối NY; stop ngoài daily extreme; target EMA9. · Risk: đó thực ra là leak trước event hôm sau → kiểm forward calendar 48h. · Data: D1 + calendar chất lượng. · Coupling: COT context (S71).

### Family 3 — Breakout/Vol-expansion (S21–S30)

Nền kinh tế chung: nén vol (squeeze) + mồi liquidity (stop cluster) tạo acceleration; NZDUSD có hai "đồng hồ vol" riêng — GDT 2 tuần/lần và RBNZ 7 lần/năm — biến event straddle thành một subclass hẳn.

**S21 — Asia-range London breakout (Breakout/Vol-expansion)** — Hypothesis: London cung cấp liquidity để break range Asia có continuation. · Signal: range 18:00–06:00 GMT; H1 close ngoài rìa trong giờ London đầu.
· Trade: stop-order rìa +2 pip buffer; stop rìa kia hoặc 0.8×ATR(H4); target 1.5× range. · Risk: false break khi range quá hẹp (<0.5×ATR H4) — filter min-range. · Data: H1. · Coupling: nếu trade kéo dài, quản lý 12:30 US data.

**S22 — NR7/inside-day squeeze breakout D1 (Breakout/Vol-expansion)** — Hypothesis: nén vol đa ngày tích tụ năng lượng, break có xu hướng extend. · Signal: NR7 hoặc 2 inside-day liên tiếp trên D1.
· Trade: stop-order hai phía extreme ±1 pip; stop 0.6×ATR; target 2×ATR; hủy phía còn lại khi fill. · Risk: whipsaw hai chiều ngày có data Mỹ → skip nếu US CPI/NFP. · Data: D1. · Coupling: TTM squeeze cùng hướng (S23).

**S23 — TTM-squeeze fire direction (Breakout/Vol-expansion)** — Hypothesis: BB nằm trong KC tích tụ rồi nổ theo hướng momentum đầu tiên. · Signal: squeeze ON (BB20/2 trong KC20/1.5); OFF khi nến đầu momentum cùng hướng.
· Trade: entry close nến fire; stop mép KC ngoài; trailing 1.5×ATR. · Risk: fire giả trong Asia → chỉ nhận tín hiệu 07:00–20:00 GMT. · Data: H4/D1. · Coupling: ADX(H4)>20 sau fire.

**S24 — London opening-range breakout (Breakout/Vol-expansion)** — Hypothesis: ORB giờ đầu London bắt được việc dọn stop hai chiều của overnight positions. · Signal: high/low của giờ đầu London (07:00–08:00 GMT).
· Trade: break + retest; stop mép OR; target 1×ATR(D1) hoặc trailing. · Risk: chop day khi DXY đi ngang → filter ADX(H4)>20. · Data: H1. · Coupling: EURUSD cùng break xác nhận USD-leg.

**S25 — GDT straddle (Breakout/Vol-expansion)** — Hypothesis: kết quả GDT ~01:00 GMT trong book NZ mỏng tạo cú move nhanh mà thị trường thường under-price. · Signal: straddle stop-order hai phía biên range 30 phút trước auction.
· Trade: giữ phía thắng theo first 1-min close; stop biên kia; trailing 1×ATR(M15); thoát trong 2 giờ. · Risk: kết quả trung tính whipsaw hai phía → chỉ vào khi environment ATR > trung bình; dairy futures đã pre-price thì bỏ. · Data: GDT calendar + M5. · Coupling: S56 drift version; S92 options version.

**S26 — OCR straddle (Breakout/Vol-expansion)** — Hypothesis: RBNZ surprise 25bp tạo trend-day; vol pre-event thường nén trong book mỏng. · Signal: straddle quanh range 15 phút trước OCR (~02:00 GMT).
· Trade: như S25 nhưng hold tới 4 giờ nếu MPS cùng hướng surprise; thoát nếu language trung hòa. · Risk: hold-vs-hike không binary — tone quyết định; rút theo 1-min close. · Data: OCR calendar + M5 + OIS prior. · Coupling: chỉ đáng khi priced-in <60% (OIS).

**S27 — Weekly-level breakout with follow-through (Breakout/Vol-expansion)** — Hypothesis: break extreme tuần trước có chọn lọc hơn khi xảy ra Tue–Wed với confirm 2 bar (tự loại fake Monday). · Signal: D1 close ngoài high/low tuần trước hai ngày liên tiếp.
· Trade: entry ngày thứ hai; stop 0.7×ATR; target 0.5× của 52-week range extrapolation. · Risk: news Thu–Fri đảo ngược. · Data: D1. · Coupling: differential cùng chiều.

**S28 — ATR-percentile spike continuation (Breakout/Vol-expansion)** — Hypothesis: sau vol-shock, continuation H1 có edge khi shock KHÔNG phải event của chính NZ. · Signal: ATR(H1,14) >percentile 90 + M15 close ngoài extreme buổi trước.
· Trade: join continuation leg; stop 1×ATR(H1); exit khi ATR rơi về percentile 60. · Risk: phân loại event sai (đó là event NZ đã priced). · Data: M15/H1 + calendar. · Coupling: S30 là subset theo US data.

**S29 — Failed-breakout reversal (Breakout/Vol-expansion)** — Hypothesis: break giả (spring/upthrust) là tín hiệu ngược mạnh vì hai nhóm trader kẹt cùng lúc. · Signal: poke ngoài biên 20d nhưng close lại trong range cùng ngày.
· Trade: entry tại close-in-range; stop poke extreme; target giữa kênh; R:R tối thiểu 1:2.5. · Risk: "failed" thực ra là retest trước break thật → stop kỷ luật. · Data: D1. · Coupling: volume/POI nếu có.

**S30 — Post-US-data confirmed breakout (Breakout/Vol-expansion)** — Hypothesis: sau NFP/CPI, hướng thật xác nhận sau 15–30 phút retest; vào retest an toàn hơn đuổi spike. · Signal: data 12:30/14:00 GMT; M15 close ngoài pre-data range + retest giữ được.
· Trade: entry retest; stop pre-data mid; target 1×ATR(D1). · Risk: data hai chiều (mixed details) → skip khi spike&chop >2 lần. · Data: M15 + US calendar. · Coupling: DXY break ngược dấu xác nhận.

### Family 4 — Carry/Rate-differential (S31–S40)

Nền kinh tế chung: 2026 đảo ngược thế hệ carry cũ — Fed 3.75–4.00% vs OCR 2.75% → NZD thành funding leg. Family này exploiting differential bằng cả hai chiều, luôn kèm vol/policy kill-switch.

**S31 — Classic inverted carry short (Carry/Rate-differential)** — Hypothesis: differential âm sâu (Fed−RBNZ +100bp) tạo drift thống kê âm + swap dương cho short NZDUSD; cần vol gate. · Signal: 2y NZ-US swap spread <−50bp và slope còn âm.
· Trade: short core, size vol-target 0.5%; cut khi spread thu hẹp <25bp hoặc VIX>25 (squeeze risk). · Risk: risk-on rally bắn short; RBNZ hawkish surprise. · Data: swap/OIS + VIX. · Coupling: S38 asymmetry engine.

**S32 — Carry-to-vol ratio filter (Carry/Rate-differential)** — Hypothesis: carry chỉ đáng ăn khi differential so với implied vol cao. · Signal: CVR = |2y diff| / 3m implied vol; xếp quartile lịch sử.
· Trade: giữ carry khi CVR top-quartile, flat khi bottom-quartile. · Risk: IV spike làm CVR nhảy → dùng lag 1 ngày. · Data: IV nguồn options/broker. · Coupling: S98 vol targeting.

**S33 — OIS repricing momentum (Carry/Rate-differential)** — Hypothesis: thay đổi kỳ vọng cuộc họp kế tiếp (ΔOIS) dẫn đường spot vài ngày sau đó. · Signal: Δ weekly OIS next-meeting của RBNZ trừ của Fed, lấy dấu cumulative 2 tuần.
· Trade: vào theo dấu Δ; exit khi Δ flat 5 ngày. · Risk: OIS nhiễu quanh data print. · Data: OIS/pricing meeting-date. · Coupling: S51 event overlay.

**S34 — Post-first-hike cycle alignment (Carry/Rate-differential)** — Hypothesis: sau hike ĐẦU TIÊN của chu kỳ mới, path repricing kéo dài nhiều tuần (anchoring của thị trường). · Signal: xác nhận chu kỳ — Fed hike đầu sau 3 năm (16/09/2026), RBNZ hike đầu từ 7/2026 → CB nào hawkish hơn relative.
· Trade: bias theo phía CB hawkish hơn (hiện short NZDUSD); scale 3 lần trong 6 tuần; stop theo 20d high. · Risk: chu kỳ bị data đảo ngược giữa chừng. · Data: meeting history + OIS. · Coupling: S38/S96.

**S35 — Carry basket USD-neutral (Carry/Rate-differential)** — Hypothesis: tách câu chuyện rates NZ khỏi USD bằng funding basket. · Signal: NZ 2y − weighted(AU, CA, CH) 2y >0 và tăng.
· Trade: long NZD vs basket (long NZDUSD + short AUDNZD/CADNZD/CHFNZD theo weight) — net USD ~0; rebalance tuần. · Risk: bốn chân → cost cộng dồn ăn edge. · Data: 5 cặp + swap. · Coupling: chỉ khi AUDNZD range (S81/82).

**S36 — Forward-roll drift capture (Carry/Rate-differential)** — Hypothesis: covered-interest khiến spot trôi về forward; các entry EOD hưởng roll-down đều đặn. · Signal: 1m forward points giữ dấu ổn định ≥3 tuần.
· Trade: position theo dấu forward, vào sau 17:00 NY khi spread rollover thu hẹp; size nhỏ; cân nhắc hedge delta. · Risk: transaction cost ăn mất roll nếu size nhỏ. · Data: forward points/swap broker. · Coupling: S49 timing.

**S37 — Differential-momentum trend gate (Carry/Rate-differential)** — Hypothesis: trend systems sống lâu hơn khi cùng chiều carry momentum. · Signal: 20d change của 2y NZ-US swap spread.
· Trade: gate S1/S2/S4 — chỉ nhận tín hiệu cùng dấu với Δ differential. · Risk: cắt mất trend sớm khi differential flat. · Data: swap. · Coupling: S96 (phiên bản MA60) — chọn một tránh double-gate.

**S38 — Inverted-carry asymmetry engine (Carry/Rate-differential)** — Hypothesis: khi differential <−75bp, phân phối return NZDUSD lệch âm (down-drift + risk-on bounce) → mọi setup nên skew short, long chỉ khi dairy surge. · Signal: differential <−75bp (đúng với 2026) + GDT 4-event MA không tăng mạnh.
· Trade: short-bias cho mọi breakout/mean-extreme setup; long chỉ khi WMP cumulative +5% trong 2 event; kill-switch khi differential >−50bp. · Risk: Fed dovish pivot đổi cấu trúc nhanh. · Data: swap + GDT. · Coupling: S61/S68 dairy gates.

**S39 — Relative-policy spread via AUDNZD overlay (Carry/Rate-differential)** — Hypothesis: chênh lệch path RBA vs RBNZ định giá AUDNZD; dùng cross như "policy spread" để hedge/thêm vị thế. · Signal: OIS cho thấy RBA hawkish hơn RBNZ (đúng 2026: 4.35→4.60 vs 2.75).
· Trade: khi short NZDUSD (S31) và AUDNZD uptrend → giữ long AUDNZD như partial hedge của leg NZD. · Risk: cross vol cao hơn ước tính. · Data: OIS 2 CB + AUDNZD. · Coupling: S81/82/87.

**S40 — Carry crash-hedge overlay (Carry/Rate-differential)** — Hypothesis: tail-risk của carry nằm ở risk-off; hedge rẻ bằng AUDNZD (NZD yếu hơn AUD khi panic). · Signal: VIX>20 rising hoặc credit spreads mở rộng.
· Trade: thêm long AUDNZD size theo beta khi đang giữ carry position; gỡ khi VIX<18. · Risk: hedge tốn kém nếu vol không nổ. · Data: VIX + AUDNZD. · Coupling: S99.

### Family 5 — Session/Time-of-day/Seasonality (S41–S50)

Nền kinh tế chung: profile liquidity của NZD bị chi phối bởi chu kỳ Tokyo–Wellington–London–NY; thêm nhịp nông nghiệp nam bán cầu cho seasonality có cơ chế thật.

**S41 — Wellington-open momentum continuation (Session/Time-of-day)** — Hypothesis: sau NY trend-day, Wellington/Sydney tiếp momentum vì vị thế chưa được square. · Signal: NY close ngoài 80% daily range + trend D1 rõ.
· Trade: 19:00–21:00 GMT vào cùng hướng nếu giờ đầu Wellington giữ trên/dưới NY mid; stop NY low/high; target 0.5×ATR. · Risk: đó chỉ là NY over-extension → Asia reversal (S13 là mặt trái). · Data: H1. · Coupling: chọn S41 hay S13 theo regime (S91).

**S42 — London–NY overlap-only day-trading (Session/Time-of-day)** — Hypothesis: giới hạn 12:00–16:00 GMT giảm noise và chi phí opportunity của phiên mỏng. · Signal: setup H1 đơn giản (break 20-bar high/low + EMA filter).
· Trade: chỉ trong 4 giờ đó; force-flat trước 17:00 tránh rollover spread. · Risk: bỏ lỡ move US morning (đã có S30 lo phần đó). · Data: H1. · Coupling: US data ngày đó → skip hoặc đổi target.

**S43 — NY-afternoon London-move fade (Session/Time-of-day)** — Hypothesis: extension London thường retrace 30–50% trong buổi chiều NY mỏng. · Signal: London tạo extension >1.2×ATR(H4); sau 16:00 GMT chưa retrace.
· Trade: fade 16:30–17:30; target mức retrace 38%; stop new extreme. · Risk: strong-trend day (event) không retrace → event filter. · Data: H1 + calendar. · Coupling: đối trọng S42/S41.

**S44 — Friday late-NY squaring reversal (Session/Time-of-day)** — Hypothesis: quỹ square cuối tuần tạo drift ngược move của tuần. · Signal: Friday 16:00–20:00 GMT; |week move| >1.5×ATR tuần.
· Trade: fade 25–40% weekly move; flat trước weekend; stop 0.5×ATR. · Risk: month-end flow cùng chiều đẩy xa hơn. · Data: H1. · Coupling: S45 — skip tuần có month-end.

**S45 — Month-end fixing flow trade (Session/Time-of-day)** — Hypothesis: WM/Reuters fix 16:00 London cuối tháng hút rebalancing flow equity/bond tạo bias nhỏ có cấu trúc. · Signal: chênh lệch return tháng giữa equity US và NZ lớn (ước lượng nhu cầu rebalance).
· Trade: vào 14:00–15:45 GMT theo hướng flow ước tính; thoát sau fix; size rất nhỏ. · Risk: nhiễu ước lượng rebalancing; cạnh tranh arbitrage. · Data: index returns + fix time. · Coupling: chỉ business day cuối tháng.

**S46 — Southern-hemisphere dairy seasonality window (Seasonality)** — Hypothesis: Sep–Nov (spring flush + đơn hàng pre-Christmas châu Á) nghiêng hỗ trợ nhu cầu sữa và NZD. · Signal: cửa sổ 15/09–15/12 hằng năm.
· Trade: bias long cho các setup pullback-in-trend trong cửa sổ, size 1.25×; tắt nếu GDT 4-event MA âm. · Risk: season bị yếu hoá bởi global risk-off; mẫu lịch sử nhỏ. · Data: GDT history + D1. · Coupling: S61 — đây là phiên bản time-window của dairy gate.

**S47 — Calendar-month seasonality ensemble (Seasonality)** — Hypothesis: vài tháng có drift thống kê nhưng phải gate bằng trend để không tự lừa mình. · Signal: month-of-year z-score (|z|>1, 20+ năm) CHỈ nhận khi trùng trend 20d đầu tháng.
· Trade: giữ bias tháng; stop cấu trúc 1.5×ATR từ entry tuần 1. · Risk: data mining — chỉ giữ tháng có cơ chế (dairy flush, fiscal year, year-end repatriation). · Data: 20+ năm D1. · Coupling: dùng như prior, không phải edge độc lập.

**S48 — Holiday-liquidity filter & gap-back (Session/Time-of-day)** — Hypothesis: ngày lễ US/UK/NZ tạo gap thanh khoản — cần tránh, hoặc khai thác gap-back sau lễ. · Signal: calendar lễ (ANZAC 25/4, NZ Labour, US Thanksgiving…).
· Trade: giảm size 50% phiên trước lễ; sau lễ fade gap mở cửa nếu không event. · Risk: ít obs mỗi năm. · Data: holiday calendar. · Coupling: S18.

**S49 — Rollover-timing execution wrapper (Session/Time-of-day)** — Hypothesis: tối ưu chi phí swap — vào sau 17:00 NY tránh trả triple-swap Wednesday trên trade ngắn không hướng thu swap. · Signal: pending entry 17:05 NY.
· Trade: execution wrapper cho S31/S36; tiết kiệm 1–2 pip/tháng chi phí ẩn. · Risk: spread giãn quanh rollover → vào 17:05–17:30 sau khi thu hẹp. · Data: broker spread log. · Coupling: mọi carry/short-hold system.

**S50 — U-shape intraday vol allocation (Session/Time-of-day)** — Hypothesis: vol profile chữ U — phân bổ risk theo giờ tăng chất lượng mà không đổi signal. · Signal: hour-of-day ATR percentile trên 1 năm.
· Trade: size hệ H1 theo profile: 60% risk cho 07:00–16:00, 25% cho Asia, 15% cho 17:00–21:00. · Risk: profile dịch khi regime đổi (họp CB) → re-fit quý. · Data: M15/H1 1 năm. · Coupling: wrapper cho mọi intraday system.

### Family 6 — Event/Data-driven (RBNZ, GDT) (S51–S60)

Nền kinh tế chung: lịch NZ thưa (CPI/employment/GDP quý; OCR 7/năm; GDT 2 tuần/lần) nên mỗi event mang nhiều thông tin; combined với USD events dày tạo cấu trúc "event matrix" hai lớp.

**S51 — OCR surprise direction trade (Event/Data-driven)** — Hypothesis: surprise vs consensus (kể cả "hold khi market priced hike") tạo continuation 1–3 ngày vì fast money phân phối chậm trong book mỏng. · Signal: outcome vs survey + OIS prior; surprise = ±25bp hoặc tone-shift mạnh.
· Trade: vào spike-retest (không đuổi gap); stop pre-event range; target 1.5–2×ATR hoặc 3 ngày. · Risk: surprise bị MPS ngược chiều trung hòa (hike + dovish track). · Data: OCR dates, consensus, OIS. · Coupling: S52 quyết định hold thêm.

**S52 — MPS language-shift score (Event/Data-driven)** — Hypothesis: biến đổi từ ngữ MPS dẫn đường drift sau decision. · Signal: score = Δ tần suất cụm hawkish/dovish giữa hai MPS liên tiếp, chuẩn hóa.
· Trade: hold S51 theo dấu score; score cực đoan → pyramid ngày 2. · Risk: score NLP nhiễu — dùng rule từ đơn giản, kiểm chứng được. · Data: MPS PDFs. · Coupling: S33 OIS confirm.

**S53 — NZ CPI surprise + range break (Event/Data-driven)** — Hypothesis: CPI quý là dữ liệu hiếm đủ sức đổi path OCR giữa hai cuộc họp; surprise lớn break cấu trúc giá. · Signal: QoQ lệch consensus ≥0.3pp.
· Trade: vào retest 12h đầu; nếu đồng thời break 20d range → hold 5 ngày; ngược lại thoát sớm. · Risk: CPI bị "nhìn xuyên" khi RBNZ đã commit path. · Data: CPI calendar + consensus. · Coupling: OIS ngay sau print.

**S54 — HLFS wage-surprise combo (Event/Data-driven)** — Hypothesis: khi unemployment cao (5.6% Q2'26), wage inflation là phần RBNZ còn lo — wage surprise lấn át headline unemployment. · Signal: private-sector hourly earnings QoQ lệch ≥0.4pp dù unemployment đúng consensus.
· Trade: theo hướng wage; size 0.75×; stop 1×ATR; horizon 2–4 ngày. · Risk: sample quý ít obs → CI rộng. · Data: HLFS + consensus. · Coupling: nếu trùng tuần CPI thì CPI ưu tiên.

**S55 — GDP nowcast-gap drift (Event/Data-driven)** — Hypothesis: GDP phản ứng chậm hơn data tần cao nên drift sau surprise kéo dài hơn. · Signal: print vs median nowcast (ASB/Westpac/BNZ).
· Trade: vào 30 phút sau (đợi spread NZ thu hẹp); hold theo trend; size 0.5×. · Risk: GDP bị revise nhiều. · Data: GDP + nowcast survey. · Coupling: chỉ khi cùng hướng trend OIS.

**S56 — GDT WMP %-change drift (Event/Data-driven)** — Hypothesis: ΔWMP lớn thay đổi kỳ vọng Farmgate milk price → thu nhập ngành dairy → NZD drift T+0..T+2. · Signal: WMP USD/MT Δ ≥+3% hoặc ≤−3% so event trước; quantity sold làm confirm thứ cấp.
· Trade: vào 30–60 phút sau kết quả (đợi spread thu hẹp); stop 0.8×ATR; target 1.2×ATR hoặc 3 phiên; hai event liên tiếp cùng dấu → size 1.5×. · Risk: trùng US data đêm đó → giảm size; dairy futures đã pre-price → edge giảm. · Data: GDT results + calendar. · Coupling: S57/S61/S46.

**S57 — Fonterra farmgate revision trade (Event/Data-driven)** — Hypothesis: nâng/hạ forecast milk price đổi kỳ vọng thu nhập cả season → drift multi-week bền (vừa thấy midpoint $9.25→$9.50). · Signal: midpoint revision ≥±$0.50/kgMS.
· Trade: bias theo hướng revision 2–4 tuần qua các setup pullback; stop cấu trúc 20d. · Risk: revision bị front-run bởi chuỗi GDT trước đó. · Data: Fonterra announcements + GDT. · Coupling: S61.

**S58 — NZ trade-balance/dairy export confirm (Event/Data-driven)** — Hypothesis: giá trị xuất khẩu dairy xác nhận ToT trend — filter chậm nhưng chắc cho medium bias. · Signal: slope của dairy export value rolling 3m đổi dấu.
· Trade: không vào riêng — gate cho medium-term position (chỉ giữ position cùng dấu slope). · Risk: noise/revision hàng tháng. · Data: StatsNZ trade. · Coupling: S61/S68.

**S59 — US-data beta-scaled trade (Event/Data-driven)** — Hypothesis: NZDUSD phản ứng data Mỹ với beta ~0.6–0.8× của EURUSD; khoảng trễ beta chưa adjust là edge. · Signal: surprise NFP/CPI/ISM >1.5× STD của dispersion forecast.
· Trade: theo hướng USD; vào sau retest M5; size theo surprise z; stop pre-data range. · Risk: surprise đã priced (blackout nuance). · Data: US calendar + consensus. · Coupling: S30 breakout version.

**S60 — RBA spill-over convergence (Event/Data-driven)** — Hypothesis: RBA move AUD ngay lập tức; NZD đi theo với lag phút→giờ; lag đó là edge. · Signal: RBA surprise khiến AUDUSD ±0.5% trong 15 phút mà NZDUSD chưa move ≥0.6× tương ứng.
· Trade: vào NZD cùng hướng AUD; target converge 0.8×; stop 0.4×ATR(H1); thoát trong 4h. · Risk: thị trường từ chối converge vì chuyện riêng NZ. · Data: RBA calendar + 2 cặp H1/tick. · Coupling: S62/S85.

### Family 7 — Cross-asset/Correlation (dairy, AUD, SPX, gold) (S61–S70)

Nền kinh tế chung: NZDUSD là tổng của USD-factor + risk-factor + NZ-idio (dairy/policy); mỗi symbol trong universe mang một factor — dùng chúng như gauge hoặc gate.

**S61 — Dairy 4-event MA trend gate (Cross-asset)** — Hypothesis: xu hướng WMP trung bình 4 event (~8 tuần) là navigator trung hạn của phần NZ-specific. · Signal: slope của MA(WMP, 4 events).
· Trade: chỉ nhận medium-term position cùng dấu slope (long khi WMP trend lên); tách khỏi intraday book. · Risk: WMP định giá USD trong khi NZD cũng bị USD — dollar-effect nhiễu ratio. · Data: GDT series. · Coupling: S38 cần dairy surge để override long chính là dùng gate này.

**S62 — AUD level-break lead-lag (Cross-asset)** — Hypothesis: AUDUSD break cấu trúc thường dẫn NZDUSD theo trong vài giờ vì depth AUD lớn hơn cập nhật giá trước. · Signal: AUDUSD break 20d extreme; NZDUSD còn cách level tương ứng <0.5×ATR.
· Trade: vào NZD cùng hướng; stop 0.6×ATR; target NZD break level +1×ATR. · Risk: NZ-news ngược chặn convergence (GDT xấu). · Data: 2 cặp D1/H1. · Coupling: chỉ dùng khi corr 60d (NZD,AUD) >0.7 — S70.

**S63 — VIX risk-beta gate (Cross-asset)** — Hypothesis: NZD long chỉ có môi trường thuận khi vol thấp và giảm. · Signal: VIX<20 và 5d slope ≤0.
· Trade: gate mọi long-biased intraday/medium systems; VIX>25 rising → bật short-bias + giảm size. · Risk: VIX spike đột ngột xuyên gate (gap). · Data: VIX. · Coupling: S99.

**S64 — Gold catch-up (Cross-asset)** — Hypothesis: gold và NZD chia sẻ anti-USD factor; gold break mà NZD chưa theo → catch-up xác suất cao. · Signal: XAUUSD 5d new high + NZDUSD chưa vượt 5d high.
· Trade: long NZD; stop 5d low; target NZD break 5d high +0.7×ATR. · Risk: gold tăng vì flight-to-safety (risk-off) — check VIX: đang lên thì skip. · Data: XAUUSD + NZDUSD + VIX. · Coupling: S63.

**S65 — Oil-trend risk gate (Cross-asset)** — Hypothesis: Brent 20d trend là proxy global demand/risk; NZ nhập khẩu dầu nên tín hiệu pha trộn nhưng vẫn có informational value. · Signal: Brent trên/dưới EMA20(D1).
· Trade: size wrapper: along oil-trend cho long-bias 1.25×, ngược 0.75×. · Risk: supply-shock (giá tăng vì supply) cho tín hiệu sai chiều risk → skip khi oil spike thuần geopolitical. · Data: BRENT. · Coupling: S68 dùng oil triệt để hơn.

**S66 — DXY inverse mirror (Cross-asset)** — Hypothesis: USD-leg là driver số một; break DXY là tín hiệu NZDUSD ngược dấu với beta khá ổn định. · Signal: DXY break 20d extreme với close confirm.
· Trade: NZDUSD ngược dấu, size theo beta hồi quy 60d (~0.6–0.8); stop 0.8×ATR; target 1.3×ATR. · Risk: giai đoạn NZ-story mạnh khiến beta gãy. · Data: DXY + NZDUSD. · Coupling: S70 corr check.

**S67 — 10y NZGB-UST spread momentum (Cross-asset)** — Hypothesis: chênh lệch yield dài hạn dẫn dòng vốn và hướng FX ở tần suất tuần/tháng. · Signal: 20d Δ của (NZ 10y − US 10y).
· Trade: gate/overlay hướng cho swing positions; giữ khi Δ cùng dấu. · Risk: yield move do global duration chứ không phải NZ-specific. · Data: 2 yields. · Coupling: S33 (ngắn hạn hơn).

**S68 — Dairy/oil terms-of-trade composite (Cross-asset)** — Hypothesis: ToT thật của NZ = giá xuất (WMP) / giá nhập (Brent) — chỉ báo thu nhập quốc gia trung hạn. · Signal: z-score 60d của (WMP index / Brent).
· Trade: z>+1 long bias, z<−1 short bias; exit khi z về 0; re-balance tuần. · Risk: cả tử và mẫu là USD-commodity — USD mạnh làm cả hai giảm, ratio ít nói về NZ. · Data: GDT + Brent. · Coupling: S61.

**S69 — SPX-divergence catch-up (Cross-asset)** — Hypothesis: SPX new-high kéo risk-on flow vào NZD; nếu NZD không theo thì hoặc catch-up hoặc có chuyện riêng chặn. · Signal: SPX 20d new high + NZDUSD dưới 20d high ≥2 ngày + VIX<20.
· Trade: long NZD catch-up; stop 20d low; target NZD 20d high. · Risk: NZ bị chặn bởi dairy/RBNZ ngược → stop sớm nếu GDT sắp tới xấu. · Data: SPX + GDT calendar. · Coupling: S63.

**S70 — Correlation-regime switch (Cross-asset)** — Hypothesis: corr 60d (NZD,AUD) là thermostat: cao = USD-regime (dùng S62/S66); thấp = NZ-idiosyncratic (dùng S56/S61). · Signal: rolling corr 60d so ngưỡng 0.7 (kèm hysteresis ±0.05 chống whipsaw).
· Trade: meta-allocator bật/tắt hai cụm strategy trên; hai book có size budget riêng. · Risk: corr lượn quanh ngưỡng. · Data: AUDUSD + NZDUSD D1. · Coupling: gate cho S62/S66 và S56/S61.

### Family 8 — Positioning/Flows (COT) (S71–S80)

Nền kinh tế chung: thị trường nhỏ → positioning extremes có thông tin hơn ở major; nguồn CME COT (thứ Sáu 15:30 ET), CME OI, RR skew, retail sentiment.

**S71 — COT leveraged-fund contrarian extreme (Positioning/Flows)** — Hypothesis: spec cực đoan + giá hết momentum = nhiên liệu đảo chiều nhiều tuần. · Signal: CME NZD net leveraged-funds z-score (3 năm) >±2 + 20d momentum đảo dấu.
· Trade: fade theo hướng ngược vị thế; horizon 4–8 tuần; stop khi positioning tiếp tục cực đoan thêm 2 tuần. · Risk: extreme persist trong trend mạnh. · Data: COT weekly. · Coupling: S75.

**S72 — COT momentum alignment (Positioning/Flows)** — Hypothesis: Δ positioning 8 tuần cùng giá = flow thật chứ không phải noise. · Signal: 8w Δnet và 8w Δgiá cùng dấu.
· Trade: join hướng đó bằng trend system làm vehicle; thoát khi Δnet flat 3 tuần. · Risk: crowding đảo bất ngờ. · Data: COT. · Coupling: S71 là mặt trái.

**S73 — Asset-manager vs leveraged-fund divergence (Positioning/Flows)** — Hypothesis: asset managers dẫn xu hướng trung hạn; leveraged funds nhiễu ngắn hạn. · Signal: Δ4w AM net dương trong khi LF net giảm (hoặc ngược).
· Trade: theo phía AM; hold tới khi AM flat. · Risk: ranh giới hai nhóm trong COT mập mơ. · Data: COT disaggregated. · Coupling: S72.

**S74 — Positioning-price divergence (Positioning/Flows)** — Hypothesis: positioning new extreme mà giá không new extreme = đang absorb → đảo chiều gần. · Signal: net spec z>2 nhưng giá chưa vượt 20d extreme.
· Trade: fade hướng positioning; stop khi giá break extreme; target EMA50. · Risk: breakout trễ vẫn đến. · Data: COT + giá. · Coupling: S71.

**S75 — Record-short × hawkish-event squeeze (Positioning/Flows)** — Hypothesis: record shorts gặp RBNZ hawkish surprise → short squeeze dốc nhất thị trường. · Signal: positioning percentile >90 một phía TRƯỚC cuộc họp RBNZ/CPI quan trọng.
· Trade: long-bias/straddle vào sự kiện theo hướng nghịch positioning; size 1.5×; thoát 2–3 ngày. · Risk: event đi theo hướng positioning → thua cả squeeze lẫn trend. · Data: COT + calendar. · Coupling: S26/S51.

**S76 — OI-price divergence on futures (Positioning/Flows)** — Hypothesis: OI tăng + giá rơi = short accumulation (tiền mới); OI giảm + giá rơi = long liquidation (sắp hết nhiên liệu). · Signal: dấu của ΔOI tuần × Δgiá.
· Trade: liquidation-phase → chuẩn bị MR long; accumulation → không bắt dao rơi. · Risk: CME OI chỉ một phần thị trường global NZD. · Data: CME OI. · Coupling: S71/S74.

**S77 — 25-delta risk-reversal contrarian (Positioning/Flows)** — Hypothesis: RR skew cực đoan = crowd one-way + bảo hiểm đắt → spot thường revert. · Signal: 1m 25d RR z-score (2 năm) >±2.
· Trade: fade theo hướng skew (RR call cực đoan → short spot); horizon 2–4 tuần; stop khi skew + giá cùng tiếp tục. · Risk: trend thật kéo cả hai. · Data: RR quotes. · Coupling: S94 là structure version.

**S78 — Risk-reversal momentum confirm (Positioning/Flows)** — Hypothesis: RR dịch về calls đồng thời giá tăng = thị trường định giá upside thật. · Signal: 4w ΔRR và 4w Δgiá cùng dấu.
· Trade: tăng size trend system cùng hướng; ngược dấu → giảm size. · Risk: RR có tính endogenous (đuổi theo giá) → dùng như confirm, không phải trigger duy nhất. · Data: RR + giá. · Coupling: S72.

**S79 — M&A/flow event fade (Positioning/Flows)** — Hypothesis: deal lớn có leg NZD tạo cầu tạm thời; sau khi flow thực hiện xong giá revert. · Signal: tin deal ≥US$1bn chạm NZ acquirer/target với funding từ nước ngoài.
· Trade: fade move NZD sau 2–5 phiên khi giá stabilize; horizon 2–4 tuần. · Risk: sample nhỏ, discretionary nặng; flow khó quantify. · Data: news M&A. · Coupling: dùng như risk-note cho medium systems.

**S80 — Retail-sentiment contrarian (Positioning/Flows)** — Hypothesis: retail crowd one-way tại extreme là nhiên liệu ngược. · Signal: broker long/short ratio >65/35 một phía + giá tại 20d extreme.
· Trade: fade; stop extreme +0.5×ATR; target 1×ATR ngược. · Risk: crowd đúng trong early-trend. · Data: broker sentiment (nếu có). · Coupling: S71 (institutional) ưu tiên khi xung đột.

### Family 9 — Pattern/Pairs/Stat-arb (AUDNZD là vehicle chính) (S81–S90)

Nền kinh tế chung: NZ và AU chia sẻ bloc thương mại + risk factor nhưng khác policy/dairy → spread có tính stationary dài hạn với break có lý do; AUDNZD thanh khoản nhất nên là vehicle chính, NZDUSD chỉ dùng khi cần USD-flavor.

**S81 — AUDNZD cointegration mean-reversion (Stat-arb)** — Hypothesis: hai đồng liên quan cấu trúc → spread stationary dài hạn; residual z-trade. · Signal: Engle-Granger trên AUDNZD có điều kiện driver (2y AU-NZ spread); z(20d)>±2.
· Trade: fade residual bằng AUDNZD trực tiếp; stop z±3 hoặc theo half-life; exit z→0. · Risk: structural break khi policy regime đổi. · Data: AUDNZD + swaps. · Coupling: S86/S87 filters.

**S82 — AUDNZD regime breakout (Stat-arb)** — Hypothesis: khi policy divergence mở ra (RBA 4.35→4.60 vs RBNZ 2.75), cross trend thay vì revert. · Signal: residual z>±2 kéo dài 3 phiên + 2y AU-NZ spread mở rộng cùng hướng.
· Trade: join cross trend; stop 1×ATR(AUDNZD); trailing EMA20; hủy nếu z quay về trong 2 phiên. · Risk: đây chính là break của S81 — hai ý là hai regime của cùng spread, chỉ chạy một phía mỗi lúc. · Data: như S81. · Coupling: S39/S70.

**S83 — NZDUSD vs XAUUSD stat pair (Stat-arb)** — Hypothesis: tách USD-factor: residual của NZDUSD hồi quy trên gold xấp xỉ phần NZ-specific, có revert. · Signal: residual 60d z>±2 với beta ổn định.
· Trade: hai chân NZDUSD + XAUUSD theo dấu residual; rebalance beta tuần. · Risk: gold có phase tự đi (CB buying) → residual mở tiếp. · Data: 2 series + rolling beta. · Coupling: S84.

**S84 — NZDUSD vs EURUSD beta-residual pair (Stat-arb)** — Hypothesis: phần variance NZD không giải thích được bởi EURUSD (USD-common) là NZ-idio và có revert. · Signal: residual 60d z>±1.8, beta drift <±0.05.
· Trade: hai chân; chỉ vào khi z>1.8 vì cost 2 spread; exit z<0.5. · Risk: residual nhỏ → cost chiếm tỷ trọng lớn. · Data: 2 series. · Coupling: so với S15 (một chân) — chọn theo cost.

**S85 — Intraday AUD→NZD lead-lag regression (Stat-arb)** — Hypothesis: ở cấp phút, quote AUD cập nhật trước NZD (depth khác nhau) → return AUD trễ dự báo return NZD. · Signal: r_NZD(t) ~ β·r_AUD(t−1…−5) fit trong phiên London.
· Trade: scalp NZD theo dự báo khi |predicted| >1.5× spread; hit-rate gate hằng tuần. · Risk: cost/latency cao — chỉ khi có data tốt. · Data: tick/M1 hai cặp. · Coupling: S60 event version.

**S86 — OU half-life adaptive MR (Stat-arb)** — Hypothesis: ước lượng half-life quyết định có đáng trade mean-reversion không và khi nào thoát. · Signal: fit Ornstein-Uhlenbeck trên spread; HL ∈ [1,10] ngày mới cho trade.
· Trade: entry z=±2; exit tại t=HL hoặc z=0 (tùy cái nào trước); stop z=±3.2. · Risk: HL nhảy theo regime → re-fit rolling 120d. · Data: spread series. · Coupling: wrapper cho S81/S83/S84.

**S87 — Kalman-filter dynamic beta (Stat-arb)** — Hypothesis: beta hedge-ratio thay đổi theo policy divergence — Kalman cập nhật liên tục tốt hơn OLS rolling. · Signal: state-space beta + residual innovation.
· Trade: dùng beta_Kalman cho mọi pair trade; entry/exit theo innovation z. · Risk: quá nhạy → tune process noise; beta degenerate. · Data: 2 series + filter. · Coupling: S81/S84.

**S88 — Dairy fair-value cointegration (Stat-arb)** — Hypothesis: dài hạn NZD TWI ~ f(WMP); residual lớn = mispricing có hồi quy. · Signal: regression quý của TWI vs log WMP 10 năm; residual z theo tần quý.
· Trade: chỉ đổi bias quý — very low frequency; dùng như sanity-check cho medium systems. · Risk: cấu trúc kinh tế NZ đổi (diversify khỏi dairy). · Data: TWI + GDT dài hạn. · Coupling: S6/S61.

**S89 — Two-bar key-reversal at extremes (Pattern/Stat)** — Hypothesis: mô hình 2-nến đảo chiều tại cực 20d có thông tin có điều kiện khi KHÔNG có event trong 48h. · Signal: bar1 break extreme, bar2 engulf ngược và close lại trong range.
· Trade: entry close bar2; stop bar2 extreme; target EMA20; R:R tối thiểu 1:1.5; skip khi có event 48h. · Risk: hiệu ứng mỏng trong trending regime → Hurst gate. · Data: D1 + calendar. · Coupling: S19.

**S90 — G10 factor-neutral NZD alpha (Stat-arb)** — Hypothesis: tách alpha NZ-specific khỏi 3 factor (dollar, carry, momentum) của G10 → residual alpha ổn định hơn giá thô. · Signal: cross-sectional regression tuần; residual NZD >|1σ| hai tuần liên tiếp.
· Trade: position NZDUSD theo dấu residual, hedge basket theo factor loadings; re-fit tháng. · Risk: factor model spec sai thì residual là risk chứ không phải alpha. · Data: G10 FX + carry + momentum. · Coupling: S97 là bản đơn giản hóa.

### Family 10 — Regime-conditioned/Options-flavored (S91–S100)

Nền kinh tế chung: edge của mọi family trên phụ thuộc regime; family này là lớp điều phối + khai thác sai định giá vol quanh các sự kiện đặc thù (GDT/OCR) trong book mỏng.

**S91 — Vol-regime switch meta-gate (Regime-conditioned)** — Hypothesis: ATR-percentile + VIX phân loại {trend-friendly, MR-friendly, crisis} để route strategies. · Signal: ATR(D1) percentile 1 năm × VIX bucket.
· Trade: vol thấp & giảm → MR book; vol mở rộng → breakout/trend book; crisis → flat + S99. · Risk: whipsaw ngưỡng → hysteresis. · Data: D1 + VIX. · Coupling: router cho cả 9 family kia.

**S92 — Pre-OCR cheap-vol long straddle (Options-flavored)** — Hypothesis: implied vol trước OCR thường dưới realized-conditional vì book mỏng under-price tail CB. · Signal: implied 1w ≤0.8× median realized-conditional quanh OCR lịch sử.
· Trade: long straddle ATM 2 ngày trước; thoát ngay sau quyết định (bán vol còn lại). · Risk: hai lần consensus liên tiếp → bleed premium. · Data: IV + realized quanh event. · Coupling: S26 (spot straddle) — chọn một theo instrument khả dụng.

**S93 — Post-event vol-crush short straddle (Options-flavored)** — Hypothesis: sau khi GDT/OCR resolve, IV rơi nhanh hơn realized. · Signal: event xong mà IV 1w vẫn >percentile 70.
· Trade: short straddle delta-hedged; giữ tới IV<median; stop gap 2×. · Risk: event kế tiếp đến sớm; tail toàn cầu. · Data: IV + calendar. · Coupling: S92 mặt trái.

**S94 — RR-skew financed structure (Options-flavored)** — Hypothesis: khi RR cực đoan, phía bị định giá rẻ có expected value dương. · Signal: 3m 25d RR z>±2.
· Trade: buy cheap-side OTM spread, bán expensive-side để finance (risk-defined); hold 2–4 tuần. · Risk: skew tiếp tục deepen; theta ăn premium. · Data: options chain. · Coupling: S77 cùng tín hiệu ở spot.

**S95 — Option-expiry pinning (Options-flavored)** — Hypothesis: strike lớn tại số tròn vào cut 10:00 NY tạo magnet trong ngày expiry. · Signal: expiry level công bố/khám phá bằng hành vi giá; giá trong ~30 pip quanh strike vào expiry day.
· Trade: fade move ra xa strike 08:00–09:30 NY (pin), thoát sau cut; hoặc trade breakout sau cut khi flow biến mất. · Risk: thông tin expiry ở retail không chính thức → đo bằng hành vi giá quanh mức. · Data: expiry calendars + M15. · Coupling: S17.

**S96 — Differential-regime trend gate (Regime-conditioned)** — Hypothesis: dấu của MA60(2y NZ-US spread) quyết định hướng trend được phép — không đi ngược carry cấu trúc. · Signal: sign(MA60(spread)).
· Trade: gate S1/S2/S4: tín hiệu ngược dấu → size 0.3× hoặc skip. · Risk: cắt trend đầu chu kỳ vì spread lag. · Data: swap. · Coupling: S37 — chỉ chọn một trong hai.

**S97 — Composite macro score allocation (Regime-conditioned)** — Hypothesis: tổ hợp z {trend, carry, dairy, risk, USD-momentum} mô tả regime tốt hơn từng phần riêng. · Signal: composite z 5 thành phần, trọng số đều.
· Trade: position medium-term theo dấu composite, size theo |z|, cap vol 2×ATR-target; re-balance tuần. · Risk: trọng số ad-hoc → sensitivity test bắt buộc. · Data: 5 input series. · Coupling: bản "thô nhưng robust" của S90.

**S98 — Vol-targeted risk engine (Regime-conditioned)** — Hypothesis: sizing theo inverse vol + drawdown kill-switch tăng chất lượng và sống sót qua tail. · Signal: target 10% annualized; position = target/realized20.
· Trade: wrapper cho mọi hệ; DD>8% → half size, >12% → flat tới khi composite z đổi dấu. · Risk: vol-target đuổi theo spikes (mua đỉnh bán đáy size). · Data: returns stream. · Coupling: S91.

**S99 — Crisis-alpha NZD short (Regime-conditioned)** — Hypothesis: NZD là high-beta risk leg — tín hiệu credit/vol nổ → short NZDUSD có alpha ngay cả khi USD đi ngang. · Signal: HY OAS mở rộng >5% trong tuần hoặc VIX>30 breakout.
· Trade: short NZDUSD beta-scaled vs SPX; trailing chậm; thoát khi VIX<22. · Risk: rescue-rally (hệ thống hỗ trợ đột ngột). · Data: VIX + credit proxy. · Coupling: S40 hedge ngược.

**S100 — Ensemble committee + cluster allocation (Regime-conditioned)** — Hypothesis: phân bổ theo regime-match và tương quan cluster tránh double-count cùng một risk factor. · Signal: mỗi family gắn nhãn cluster {USD, NZ-idio, risk, dairy, flow}; cap 1.5× tổng exposure mỗi cluster.
· Trade: weight = hit-rate gần đây × diversity score; re-weight tháng bằng quy tắc cứng. · Risk: meta-overfit — không học weight từ quá khứ ngắn; mọi thứ mặc định `NOT_RUN` cho tới khi qua trial accounting. · Data: input của các family + trial ledger. · Coupling: chịu quản trị của gates chương trình.

## 3. Tổng hợp cho symbol

### 3.1 Top-10 ideas và vì sao

1. **S56 — GDT WMP %-change drift**: edge đặc thù nhất của NZDUSD (không major nào có driver rời rạc 2 tuần/lần); tần suất vừa phải để spread không giết; cơ chế kinh tế rõ (WMP → farmgate → thu nhập); ít bị arb bởi crowd lớn vì data ngách.
2. **S26/S92 — OCR straddle (spot hoặc vol)**: RBNZ đang trong hiking cycle với 7 họp/năm; vol nén trước event trong book mỏng; cơ chế sạch dù sample ít — phải quản trị bẫi ít-obs (xem 3.2).
3. **S81 — AUDNZD cointegration MR**: cross thanh khoản nhất của NZD; tách sạch USD-noise; lịch sử 2017–18 cho thấy divergence RBA-RBNZ tạo break có logic — hai regime (S81/S82) dùng chung hạ tầng.
4. **S62 — AUD level-break lead-lag**: cơ chế dẫn-lag ổn định (depth AUD >> NZD); chi phí thấp; dễ kết hợp gate corr (S70).
5. **S31+S38 — Inverted-carry short bias với asymmetry engine**: cấu trúc 2026 (Fed 3.75–4.00 vs OCR 2.75) cho vừa drift vừa swap dương cho short; kill-switch rõ theo differential và dairy.
6. **S21 — Asia-range London breakout**: khớp cấu trúc phiên của NZD; chi phí chấp nhận được nếu tuân giờ; là đại diện tốt nhất của intraday breakout cho symbol thanh khoản mỏng.
7. **S66 — DXY inverse mirror**: USD-leg là driver số một của variance; beta ổn định giúp scale; đơn giản, khó overfit.
8. **S71 — COT contrarian extremes**: thị trường nhỏ → positioning extremes có thông tin hơn major; sample COT 20+ năm đủ cho validation nghiêm túc.
9. **S61/S68 — Dairy gates (WMP MA, dairy/oil ToT)**: biến driver đặc thù thành risk gate trung hạn cho mọi hệ khác — tăng chất lượng của toàn bộ book chứ không chỉ một strategy.
10. **S97 — Composite macro score**: khung tổng hợp chống việc all-in một câu chuyện (USD hay dairy); trọng số đều giảm rủi ro curve-fitting trọng số.

### 3.2 Bẫy overfitting đặc thù khi backtest NZDUSD

- **Cost model phải NZD-specific**: spread RT 1.5–2.5 pip theo giờ, không dùng 0.3 của EURUSD; slippage stop ≥1.5× spread; fill giả 17:00–19:00 GMT và Sunday open là nguồn over-report lớn nhất.
- **Timestamp & DST**: NZ_DST và US_DST lệch nhau vài tuần mỗi năm — event 01:00 GMT có thể nhảy 02:00 GMT; lịch sử GDT/OCR phải align theo Wellington time gốc, không theo UTC cứng.
- **Sample event mỏng**: OCR 7/năm, GDT 26/năm, CPI 4/năm — mọi event strategy có vài trăm obs tối đa trong 15 năm; yêu cầu walk-forward theo chu kỳ policy và minimum sample trước khi tin.
- **AUD-proxy leakage**: nếu dùng AUDUSD làm feature (S15/S62/S85) trên ngày GDT, phần NZ-idio bị AUD "che" — tách event-day khỏi training set của feature này.
- **Regime cluster nhỏ**: 2014–15 dairy crash, 2020 COVID, 2022 Fed, 2024–25 cut-cycle — mỗi regime gần như một obs; báo cáo phải chia performance theo regime thay vì tổng gộp.
- **Seasonality ~30 obs/tháng**: CI rất rộng; chỉ giữ khi có cơ chế (dairy flush, fiscal year) và gate trend như S47.
- **Carry-hindsight**: dùng differential hiện tại (âm sâu) để fit short-bias trên quá khứ khi differential từng dương là leakage kinh điển — differential phải là time-varying input.
- **Survivorship của broker feed**: NZDUSD quote khác nhau giữa venue nhiều hơn major; backtest trên một feed rồi live trên feed khác dễ "mất edge" vi mô.
- **Whipsaw quanh số tròn trong backtest fill giả**: các mô hình S17/S95 nhạy với giả định fill; phải mô phỏng requote/queue.

### 3.3 MUST-WATCH weekly macro checklist

- **Thứ 2**: duyệt lịch tuần — RBNZ/GDT/NZ data/US data/RBA; kiểm GDT auction có phải tuần này không (nhịp 2 tuần); dairy futures có pre-price mạnh không.
- **Thứ 3 (tuần GDT)**: theo dõi kết quả auction ~00:00–01:00 GMT — WMP avg price, Δ%, quantity sold, GDT index; so sánh với dairy futures để đo surprise.
- **Thứ 4**: GDT Pulse (event nhỏ, xác nhận); Kiwi TWI data của RBNZ nếu có.
- **Thứ 5**: cân nhắc lại medium bias theo differential (2y swap NZ-US, OIS next meetings RBNZ vs Fed) và composite S97.
- **Thứ 5 tối/Thứ 6 (giờ Mỹ)**: CFTC COT 15:30 ET thứ Sáu — net leveraged funds NZD, asset managers, OI; cập nhật z-score S71/S74.
- **Hằng tuần**: VIX/SPX (risk gate S63/S69), DXY & UST 10y (S66/S67), Brent (S65/S68), AUDNZD mức giá + corr 60d (S70), status của GDT 4-event MA (S61).
- **Hằng tháng**: NZ trade balance/exports dairy; US CPI/NFP/ISM calendar cho tuần tới; Australia CPI quý (RBA path → S39/S60); China PMI (ngày 31/1).
- **Hằng quý**: NZ CPI, HLFS employment, GDP, RBNZ MPS (đọc diff ngôn ngữ cho S52); COT cực đoan vào các tuần trước OCR (S75).
- **Ad-hoc**: Fonterra announcements (farmgate revision — S57); NZ politics/Budget; RBNZ speeches; tin thời tiết El Niño/La Niña; M&A có leg NZ.
- **Cuối mỗi tháng**: re-verify toàn bộ snapshot 1.0 (tốc độ cũ hóa nhanh — đặc biệt RBA outcome 28–29/09/2026 và OCR tiếp theo).

### 3.4 Đề xuất đo đạc ban đầu khi được phép chạy data (nguyên tắc, không phải kết quả)

- Spread/ATR theo giờ (24×7) và theo session — xây cost model NZD-specific trước bất kỳ backtest nào.
- Ma trận rolling correlation 60d với 11 symbol của universe — thay bảng prior ở 1.5 bằng số đo.
- Event study GDT/OCR/CPI: phân phối return T−1→T+5 quanh mỗi loại event, tách regime differential.
- Kiểm định stationarity của AUDNZD residual và ước lượng half-life (S86) — quyết định S81 vs S82.
- Phân phối gap weekend/holiday và slippage giả định — input cho mọi hệ có stop.

### 3.5 Ma trận family × bối cảnh sống/chết

| Family | Sống khi | Chết khi |
|---|---|---|
| Trend/Momentum | differential đang trending, dollar-cycle rõ ràng | chop kéo dài khi differential đi ngang |
| Mean-reversion | vol thấp, không event trong 48h | đứng qua RBNZ/GDT/US data, hoặc trending mạnh |
| Breakout/Vol-expansion | squeeze + vào đúng liquidity window | Asia thin whipsaw, stop đặt dưới 0.5×ATR |
| Carry/Rate-differential | differential rộng và ổn định hướng | policy pivot đột ngột, vol nổ (VIX>25) |
| Session/Seasonality | cấu trúc phiên ổn định, đã re-fit DST | kỳ DST lệch, holiday đặc biệt, regime đổi |
| Event/Data-driven | lịch sự kiện sạch + consensus/OIS data tốt | sample mỏng bị fit; event đã priced-in |
| Cross-asset/Correlation | corr regime xác nhận beta ổn định | beta gãy khi NZ-idio (dairy/RBNZ) áp đảo |
| Positioning/Flows | extremes thật + event mồi nearby | extreme persist thêm nhiều tuần trong trend |
| Pattern/Pairs/Stat-arb | spread stationary (kiểm định qua) | structural break khi policy regime đổi |
| Regime/Options | infrastructure vol/options có sẵn | venue không có options; meta-overfit weight |

### 3.6 Thứ tự ưu tiên validate (nguyên tắc, không phải kết quả)

1. **Cost model NZD-specific** (spread/slippage theo giờ) — điều kiện tiên quyết cho mọi ý còn lại.
2. **S56/S25/S26 event studies** trên lịch sử GDT/OCR sạch — edge đặc thù nhất, cần chứng minh sớm.
3. **Hạ tầng stat-arb S81/S86** — kiểm định cointegration AUDNZD + ước lượng half-life.
4. **S1/S21/S66** — trend/breakout/mirror đơn giản với cost thật, làm baseline so sánh.
5. **S71** — COT z-score chuẩn hóa, sample dài nhất trong các ý.
6. Các ý còn lại chỉ sau khi (1)–(5) có bằng chứng và đã qua gates của chương trình.

---

## Phụ lục A — Chỉ mục 100 ideas theo family

| # | Tên | Family | Hook một cụm |
|---|---|---|---|
| S1 | Daily EMA-stack trend ride | Trend | Ba EMA cùng hướng, ride pullback |
| S2 | Donchian 20/55 breakout | Trend | Kênh Da breakout close-based |
| S3 | ADX-filtered Chandelier trend | Trend | Chỉ đi trend khi ADX xác nhận |
| S4 | 3M/12M time-series momentum | Trend | Dấu return 63d/252d làm bias tháng |
| S5 | NZD relative-strength gate vs bloc | Trend | Chỉ long khi NZD mạnh nhất bloc |
| S6 | TWI-proxy trend alignment | Trend | Synthetic TWI dẫn hướng NZDUSD |
| S7 | Heikin-Ashi weekly + H1 trigger | Trend | Chuỗi nến HA tuần, vào bằng H1 |
| S8 | Volatility-normalized momentum | Trend | Momentum đo bằng ATR-units |
| S9 | Trend-pullback continuation | Trend | Mua dip RSI(2) reset trong uptrend |
| S10 | Trend committee ensemble vote | Trend | Bình chọn ba hệ, size theo tổng phiếu |
| S11 | Bollinger z-score fade D1 | Mean-rev | Fade ±2.5σ khi không event |
| S12 | RSI(2) range-bound fade | Mean-rev | MR chỉ trong dải quanh EMA200 |
| S13 | Asia-session overshoot fade | Mean-rev | Fade over-extension giờ mỏng |
| S14 | Anchored-VWAP reversion | Mean-rev | Gravity quanh VWAP phiên |
| S15 | AUD-residual reversion | Mean-rev | Fade phần NZ-idio vs beta AUD |
| S16 | GDT overshoot fade | Mean-rev | Reaktion sữa nhỏ, move lớn |
| S17 | Round-number rejection fade | Mean-rev | Wick rejection tại 0.XX00 |
| S18 | Weekend gap fade | Mean-rev | Gap Monday không có lý do |
| S19 | Hurst-regime MR gate | Mean-rev | MR chỉ khi anti-persistent |
| S20 | No-news vol-spike snapback | Mean-rev | Vol-shock kỹ thuật hồi nhanh |
| S21 | Asia-range London breakout | Breakout | Range đêm, break giờ London |
| S22 | NR7/inside-day squeeze breakout | Breakout | Nén vol đa ngày rồi nổ |
| S23 | TTM-squeeze fire direction | Breakout | BB trong KC rồi fire |
| S24 | London opening-range breakout | Breakout | ORB giờ đầu London |
| S25 | GDT straddle | Breakout | Straddle quanh kết quả GDT |
| S26 | OCR straddle | Breakout | Straddle quanh quyết định RBNZ |
| S27 | Weekly-level breakout follow-through | Breakout | Break tuần có confirm 2 bar |
| S28 | ATR-percentile spike continuation | Breakout | Tiếp cú vol-shock không-event |
| S29 | Failed-breakout reversal | Breakout | Break giả = tín hiệu ngược |
| S30 | Post-US-data confirmed breakout | Breakout | Vào retest sau NFP/CPI |
| S31 | Classic inverted carry short | Carry | Short ăn swap khi differential âm |
| S32 | Carry-to-vol ratio filter | Carry | Carry khi differential/IV cao |
| S33 | OIS repricing momentum | Carry | Theo Δ kỳ vọng họp tới |
| S34 | Post-first-hike cycle alignment | Carry | Hike đầu chu kỳ = drift nhiều tuần |
| S35 | Carry basket USD-neutral | Carry | Funding basket tách USD |
| S36 | Forward-roll drift capture | Carry | Hưởng roll-down có kiểm soát |
| S37 | Differential-momentum trend gate | Carry | Gate trend bằng Δ differential |
| S38 | Inverted-carry asymmetry engine | Carry | Skew short, dairy override long |
| S39 | Relative-policy spread AUDNZD | Carry | Cross như "policy spread" |
| S40 | Carry crash-hedge overlay | Carry | Hedge risk-off bằng AUDNZD |
| S41 | Wellington-open continuation | Session | Tiếp momentum sau NY trend-day |
| S42 | London–NY overlap only | Session | Chỉ trade 12:00–16:00 GMT |
| S43 | NY-afternoon London-move fade | Session | Fade retrace chiều NY mỏng |
| S44 | Friday late-NY squaring reversal | Session | Fade move tuần cuối tuần |
| S45 | Month-end fixing flow | Session | Bias quanh WM fix cuối tháng |
| S46 | Dairy seasonality window | Seasonality | Cửa sổ 15/09–15/12 bias long |
| S47 | Calendar-month seasonality | Seasonality | z-score tháng + gate trend |
| S48 | Holiday gap-back | Session | Tránh/gặp gap quanh lễ |
| S49 | Rollover-timing wrapper | Session | Vào sau 17:05 NY tối ưu swap |
| S50 | U-shape vol allocation | Session | Size theo profile giờ |
| S51 | OCR surprise direction | Event | Hướng surprise + 1–3 ngày |
| S52 | MPS language-shift score | Event | Diff ngôn ngữ MPS dẫn drift |
| S53 | CPI surprise + range break | Event | CPI quý break cấu trúc |
| S54 | HLFS wage-surprise combo | Event | Wage lấn át unemployment |
| S55 | GDP nowcast-gap drift | Event | Print vs nowcast, drift chậm |
| S56 | GDT WMP %-change drift | Event | ΔWMP ≥±3% → drift 3 phiên |
| S57 | Fonterra farmgate revision | Event | Revision FGMP → multi-week |
| S58 | Trade-balance confirm | Event | Export dairy xác nhận bias |
| S59 | US-data beta-scaled | Event | Surprise Mỹ qua beta NZD |
| S60 | RBA spill-over convergence | Event | AUD move trước, NZD theo sau |
| S61 | Dairy 4-event MA gate | Cross-asset | WMP trend dẫn medium bias |
| S62 | AUD level-break lead-lag | Cross-asset | AUD break, NZD theo trong giờ |
| S63 | VIX risk-beta gate | Cross-asset | Long chỉ khi vol thấp |
| S64 | Gold catch-up | Cross-asset | Gold break, NZD theo sau |
| S65 | Oil-trend risk gate | Cross-asset | Brent EMA20 làm size wrapper |
| S66 | DXY inverse mirror | Cross-asset | Break DXY → NZD ngược dấu |
| S67 | 10y spread momentum | Cross-asset | NZGB−UST dẫn swing |
| S68 | Dairy/oil ToT composite | Cross-asset | WMP/Brent z-score |
| S69 | SPX-divergence catch-up | Cross-asset | SPX high, NZD chưa theo |
| S70 | Correlation-regime switch | Cross-asset | Corr 60d NZD-AUD làm thermostat |
| S71 | COT contrarian extreme | Positioning | Spec z>±2 fade nhiều tuần |
| S72 | COT momentum alignment | Positioning | Δ8w position + giá cùng dấu |
| S73 | AM vs LF divergence | Positioning | Theo asset managers |
| S74 | Positioning-price divergence | Positioning | Absorb tại extreme |
| S75 | Record-short event squeeze | Positioning | Short cực đoan + RBNZ hawkish |
| S76 | OI-price divergence | Positioning | Phân biệt accumulation/liquidation |
| S77 | Risk-reversal contrarian | Positioning | Skew cực đoan fade spot |
| S78 | RR momentum confirm | Positioning | RR + giá cùng hướng |
| S79 | M&A flow fade | Positioning | Fade pop sau deal lớn |
| S80 | Retail-sentiment contrarian | Positioning | Crowd one-way tại extreme |
| S81 | AUDNZD cointegration MR | Stat-arb | Fade residual có điều kiện |
| S82 | AUDNZD regime breakout | Stat-arb | Break residual khi policy diverge |
| S83 | NZDUSD-XAUUSD stat pair | Stat-arb | Tách USD-factor bằng gold |
| S84 | NZDUSD-EURUSD residual pair | Stat-arb | Tách USD-factor bằng euro |
| S85 | Intraday AUD→NZD regression | Stat-arb | Lag phút của quote |
| S86 | OU half-life adaptive MR | Stat-arb | HL quyết định trade/exit |
| S87 | Kalman dynamic beta | Stat-arb | Hedge ratio thời biến |
| S88 | Dairy fair-value cointegration | Stat-arb | TWI vs WMP quý |
| S89 | Two-bar key reversal | Pattern | Đảo chiều 2 nến không-event |
| S90 | G10 factor-neutral alpha | Stat-arb | Residual vs factor model |
| S91 | Vol-regime switch meta-gate | Regime | Router trend/MR/crisis |
| S92 | Pre-OCR cheap-vol straddle | Options | Mua vol khi IV rẻ trước OCR |
| S93 | Post-event vol crush | Options | Bán vol sau resolve |
| S94 | RR-skew financed structure | Options | Mua phía rẻ của skew |
| S95 | Option-expiry pinning | Options | Magnet quanh strike expiry |
| S96 | Differential-regime trend gate | Regime | MA60 spread chọn hướng |
| S97 | Composite macro score | Regime | 5 z-score tổ hợp |
| S98 | Vol-targeted risk engine | Regime | Inverse-vol + DD kill-switch |
| S99 | Crisis-alpha NZD short | Regime | Credit/vol nổ → short |
| S100 | Ensemble + cluster cap | Regime | Phân bổ anti double-count |

## Phụ lục B — Thuật ngữ và nguồn dữ liệu đề xuất (khi được phép)

- **OCR** — Official Cash Rate của RBNZ; **MPS** — Monetary Policy Statement (kèm một số họp OCR).
- **GDT** — Global Dairy Trade (Fonterra); **WMP/SMP** — whole-milk / skim-milk powder; **GDT Pulse** — auction nhỏ hàng tuần.
- **FGMP** — Fonterra Farmgate Milk Price (forecast theo season); **ToT** — terms of trade; **TWI** — trade-weighted index (RBNZ công bố).
- **OIS** — overnight index swap (kỳ vọng họp tới); **COT** — Commitments of Traders (CFTC, 15:30 ET thứ Sáu); **OI** — open interest (CME).
- **RR** — 25-delta risk reversal; **IV** — implied volatility; **HY OAS** — high-yield option-adjusted spread (proxy credit).
- **DXY** — dollar index; **HLFS** — Household Labour Force Survey (employment NZ); **ATR/EMA/ORB/NR7** — các chỉ báo kỹ thuật tiêu chuẩn.
- **OU** — Ornstein-Uhlenbeck (mô hình mean-reversion); **EG** — Engle-Granger (kiểm định cointegration).
- Nguồn dữ liệu đề xuất khi mở quyền chạy: rbnz.govt.nz (OCR/MPS/TWI), globaldairytrade.info (kết quả auction), StatsNZ (CPI/HLFS/GDP/trade), Fonterra announcements (FGMP), CFTC (COT), CME (OI), VIX/DXY (thương mại), broker (spread/forward points), dairy futures NZX/CME (pre-pricing GDT).

---

**Trạng thái kết thúc (lane NZDUSD)**

- Nội dung: knowledge-only brainstorm; không backtest, không code, không data, không git.
- Mọi strategy (S1–S100), ngưỡng, correlation và con số lịch sử: `NOT_RUN` cho tới khi qua trial của `FOREX-UNIFIED-STRATEGY-BRAINSTORM-V1`.
- Danh sách **(cần kiểm chứng)** khi dùng tiếp: kết quả RBA 28–29/09/2026; giờ GDT Pulse; tỷ trọng doanh số NZD theo BIS 2025; các con số lịch sử ở mục 1.7.
- Snapshot macro 1.0 hết hạn nhanh — re-verify trước mỗi lần sử dụng.
