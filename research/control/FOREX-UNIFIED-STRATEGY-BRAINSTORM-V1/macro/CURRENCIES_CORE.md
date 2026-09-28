# Bản đồ yếu tố quốc gia/đồng tiền — CORE (USD, EUR, GBP, JPY)

> Lane: `MACRO_CORE` · Program: `FOREX-UNIFIED-STRATEGY-BRAINSTORM-V1` · Ngày: 2026-09-28
> Kiến thức-only brainstorm (no backtest, no code, no data download). Phục vụ 12 symbol lane:
> EURUSD, GBPUSD, USDCAD, USDJPY, AUDUSD, NZDUSD, USDCHF, XAUUSD, XAGUSD, BRENT, WTI, NATGAS.
> **Trạng thái verify**: các mục số liệu Sep-2026 đã verify qua WebSearch ngày 2026-09-28
> (nguồn: Reuters, CNBC, AP/BBC/Morningstar cho BoE, Yahoo Finance/Il Foglio cho ECB, forex.com
> cho DXY/USDJPY, lane XAUUSD/USDJPY đã verify FRED DFII10, Fed press release, Kitco, TradingEconomics).
> Mục chưa verify độc lập đánh dấu **(cần kiểm chứng)**. Các con số "độ nhạy/độ move" là
> **kinh nghiệm heuristic** dùng làm giả thuyết — phải đo lại bằng data thực trước khi dùng làm gate.

---

## 0. Snapshot bối cảnh Sep-2026 (đã verify — anchor cho mọi section dưới)

| Khối | Policy rate | Trạng thái | Nguồn verify |
|---|---|---|---|
| Fed (Chair **Kevin Warsh**) | **3.75–4.00%** sau hike 25bp ngày **16/09/2026** (vote 12–0, hike đầu tiên kể từ 2023) | Hawkish; SEP/dots → **4.00–4.25% cuối 2026** (còn ~1 hike); market pricing ~70% Oct / ~95% Dec **(mức % pricing theo lane XAUUSD/TradingEconomics)** | Reuters, CNBC |
| ECB | Depo **2.50%** sau hike 25bp ngày **10/09/2026** (MRO 2.65%); hike thứ hai của chuỗi re-tightening từ ~Jul/2026 | Thắt chặt trở lại vì energy shock đẩy HICP; "no preset path", data-dependent | Yahoo Finance, Il Foglio |
| BoE | **3.75%** — hold ngày **17/09/2026**, vote **6–3** (3 phiếu đòi hike lên 4%); hold thứ 6 liên tiếp từ cut 12/2025 | Hawkish-tilt hold; CPI Aug **3.1%** và BoE nói "likely to rise further"; gilt 10Y **5.378%** (10/09) — cao nhất từ Jul/2007 | AP, BBC, BoE MP Summary, Reuters, Morningstar |
| BoJ | **~1.00%** (hike 12/2025 — mức cao 30 năm; 2026: Jan hold, Apr board chia rẽ lớn nhất 10 năm, Jul stand-pat) | Normalization chậm, nhịp phụ thuộc wage data; **kết quả meeting Sep/2026 (kỳ vọng 25bp) — cần kiểm chứng** | Lane USDJPY (Reuters/OMFIF/Morgan Stanley) |
| MOF Nhật | Can thiệp **phối hợp Nhật–Mỹ** Jul–Aug/2026: yen đáy **163.99** (23/07) → can thiệp → yen mạnh về **152.89** (08/09, +4.5%/tuần) → dao động **152.9–154.5** | "Joint intervention" đầu tiên sau ~15 năm (từ 2011); Nhật ước **$53bn trong 1 ngày** (kỷ lục), tổng đợt ~$75–100bn (các nguồn chênh nhau); Mỹ tham gia, mức không công bố (lane ước $5–10bn) **(tổng số cần kiểm chứng)** | Reuters 08/09, The Peninsula, Forex.com, Vantage, lane USDJPY |
| Geo | War Mỹ–Iran / eo Hormuz ON: phong tỏa cảng Iran, Brent đỉnh **~$108** (28/09: $108.07, +61% y/y), WTI **>$100**; 25/09 Iran đề nghị mở lại Hormuz trong 7 ngày đổi dỡ phong tỏa, 27/09 Trump từ chối | Oil-shock truyền vào CPI toàn cầu → câu chuyện "hike vì oil" của Fed/ECB | Lane XAUUSD (verify Kitco/TradingEconomics), Reuters |
| Markets | Gold **$4,144** (28/09, −3.25%/ngày; −26% từ ATH $5,589.38 ngày 28/01/2026); **10Y TIPS real yield 2.85%** (24/09, +23bp/tuần); DXY vùng **~100** (resistance ~100.54, range 98–103), vừa break dưới uptrend 2026 ngắn hạn nhưng cấu trúc dài hạn lên; UST 10Y ~4.78% (19-month high) — mâu thuẫn với headline ~5.2% của Kitco theo lane XAUUSD **(cần kiểm chứng)**; HH gas $2.50–3.35 decoupled TTF ~€60/MWh | "Hike-cycle + oil-shock": cả DXY lẫn gold cùng chịu áp lực — **quan hệ inverse gold-DXY tạm thời gãy** | FRED (qua lane), Forex.com, Kitco, TradingEconomics |

---

## 1. USD — Mỹ

### 1.1. Fed: mandate, stance, dot-path, reaction function

- **Mandate**: dual mandate — maximum employment + price stability (mục tiêu PCE 2%). Từ 2020 FAIT framework → 2025 framework review nới lại định nghĩa "shortfall" **(chi tiết framework mới cần kiểm chứng)**. Dưới Chair **Kevin Warsh** (thay Powell, nhiệm kỳ cũ kết thúc May/2026 — thời điểm chuyển giao chính xác cần kiểm chứng): Fed đang trong "regime change" — Warsh chống forward guidance ("Fed officials have tipped their hand too much"), im lặng về đường đi tương lai trong khi các governor khác vẫn nói.
- **Stance hiện tại (verified)**: 3.75–4.00% sau hike 25bp ngày 16/09/2026 — hike đầu tiên kể từ 2023, vote 12–0. Lý do: "Inflation is too high and has been for too long" — Fed chấp nhận trả giá tăng trưởng để lấy "timelier drop in inflation". SEP mới: policy rate đạt **4.00–4.25% cuối 2026 và đi vào 2027** → tín hiệu ~1 hike nữa. Market: ~70% cho meeting Oct, ~95% cho Dec (HSBC/JPM/GS đều đã chuyển sang kỳ vọng Sep+Dec hikes).
- **Reaction function (cách đọc Fed dưới Warsh)**:
  1. **Inflation-first**: oil shock (Hormuz) đang truyền vào headline CPI → Fed treat như persistent, không "look through" (khác playbook 2022 đầu chu kỳ). CPI/PCE surprise **lên** = hawkish repricing mạnh hơn bất kỳ dữ liệu lao động nào.
  2. **Chống forward guidance** → volatility quanh FOMC cao hơn bình thường: thị trường không được "lead" bởi phỏng đoán phát ngôn → dot plot và presser Q&A là lúc repricing dồn.
  3. **Áp lực chính trị**: White House gây áp lực lên Warsh Fed (tuần trước FOMC chỉ ~60% nhà đầu tư cược hike) → rủi ro hai chiều: Fed có thể hike thêm để chứng minh độc lập (hawkish surprise) hoặc bị đọc là nhượng bộ nếu hold (USD bị bán). Kênh "Fed independence premium" là driver mới của DXY vol.
  4. **Balance sheet**: Warsh muốn cắt QT nhanh hơn nhưng đang bị kháng nội bộ (stalled) — nếu tái khởi động, áp lực funding/term premium thêm → USD bullish qua thiếu dollar liquidity.
- **Lịch FOMC còn lại 2026**: Oct 27–28 và Dec 8–9 (chuẩn lịch — cần kiểm chứng) + minutes (3 tuần sau), Jackson Hole đã qua (Aug).

### 1.2. Dữ liệu định kỳ Mỹ (tần suất — lịch — mức surprise điển hình — tác động DXY)

| Dữ liệu | Nhịp / giờ | Vì sao quan trọng | Surprise điển hình gây move (heuristic — cần đo lại) | Tác động DXY |
|---|---|---|---|---|
| **NFP** | Thứ Sáu đầu tháng, 8:30 ET | Anchor cho leg "employment" của mandate | ±50–100k vs consensus: 20–50 pips tức thời trên DXY proxy (EURUSD/USDJPY); kèm revision ±100k dễ đảo chiều phản ứng đầu | Bidding: payroll mạnh + AHE mạnh → USD lên toàn phần |
| **CPI** | Giữa tháng (10–15), 8:30 ET | Trong regime Sep-2026 là release **quan trọng nhất** — Fed inflation-first | Core m/m lệch ±0.1pp vs 0.2/0.3% consensus: 30–70 pips + dịch cả đường OIS Oct/Dec | Surprise lên → DXY lên, gold xuống (kênh real yield) |
| **PCE (core)** | Cuối tháng, 8:30 ET | Gauge chính thức của Fed; trễ hơn CPI, ít surprise hơn | ±0.1pp: 10–30 pips | Xác nhận/pHủ nhận CPI, hiếm khi đảo narrative |
| **Retail sales** | Giữa tháng, 8:30 ET | Proxy consumer 70% GDP | Control group ±0.3pp: 15–40 pips | Mạnh → hawkish → USD lên |
| **GDP** | Advance ~30 ngày sau quý; 8:30 ET | Level-check tăng trưởng; thường bị revision nhiều | ±0.3ppq/q: 15–30 pips, fade nhanh nếu conflict với inflation narrative | Thứ cấp trong regime "hike vì lạm phát" |
| **ISM Mfg/Services + PMI flash** | ISM Mfg: ngày làm việc đầu; Services: ngày 3; S&P flash ~ngày 23 | Leading, giá đầu vào (prices-paid) feeding CPI narrative | >2đ lệch: 15–40 pips; prices-paid nóng đặc biệt quan trọng trong oil-shock | Hai chiều theo prices vs employment mix |
| **Claims + JOLTS** | Claims: thứ Năm hằng tuần; JOLTS: đầu tháng | Cung cầu lao động high-frequency | Claims surprise >20k hai tuần liên tiếp mới có narrative | Thứ cấp |
| **UST auctions** | 2/3/5/7/10/30Y mỗi tháng; refunding quarterly | Term premium/funding — Sep-2026 30Y ở vùng high 2007 | Tail 2–3bp: 10–20 pips; tail 30Y mạnh → "bond vigilante" bid USD ngắn nhưng có thể thành risk-off | Bid-to-cover yếu → USD vol nở |

**Nguyên tắc đọc regime hiện tại**: trong "hike-cycle because of oil", **CPI > NFP** về quyền lực định giá — nghịch với regime 2023–24 (NFP là vua). Cặp dữ liệu CPI tháng này + dot plot là hai event duy nhất đủ lực đổi trend DXY.

### 1.3. Kênh truyền dẫn USD vào TỪNG symbol (12-symbol universe)

| Symbol | Kênh chính từ USD | Chú thích riêng |
|---|---|---|
| EURUSD | Rate differential Fed–ECB (3.75–4.00 vs 2.50) + risk sentiment | Cả hai CB đang hike → differential nở chậm; EURUSD ít "one-way USD" hơn — động năng đến từ oil/ToT eurozone |
| GBPUSD | Differential Fed–BoE (3.75–4.00 vs 3.75) + gilt stress channel | Gilt stress làm GBP rơi **dù** yield lên (credibility channel, dạng mini-2022) — USD mạnh kép |
| USDCAD | Differential Fed–BoC + oil | **Ngoại lệ thú vị Sep-2026**: oil mạnh thường kéo CAD, nhưng differential nghiêng USD (BoC thấp hơn Fed — mức BoC cần kiểm chứng) + USD funding mạnh → USDCAD không bán được chỉ dựa oil |
| USDJPY | Differential (~275–300bp) + UST 10Y + **MOF intervention overlay** | Xem §4 — layer chính trị đè lên layer rate |
| AUDUSD, NZDUSD | USD leg (rate/real-yield) + risk-on/off + commodity terms-of-trade | RBA/RBNZ stance Sep-2026 cần kiểm chứng từng lane; AUD/NZD là "risk beta" — bán khi USD funding tighten |
| USDCHF | Safe-haven parity (CHF & JPY cùng được mua khi stress) + SNB | Sep-2026: carry thuận USD vs CHF nhưng unwind JPY thường kéo CHF cùng lên → USDCHF down-bias trong干预 days |
| XAUUSD | **Real yield (10Y TIPS 2.85%) >> DXY** | Tháng 9/2026: DXY break dưới uptrend (yếu đi kỹ thuật) mà gold vẫn rơi −26% từ đỉnh → **inverse gold–DXY chỉ đúng khi real yield đi ngang**; khi real yield tăng nhanh, cả hai cùng áp lực — rule "gold = anti-USD" SAI trong regime này |
| XAGUSD | Như gold × beta 1.3–1.5 + industrial demand | G/S ratio (~68 ngày 28/09 — cần kiểm chứng) là gauge risk-appetite |
| BRENT / WTI | **Oil priced in USD** — hai chiều: USD mạnh (rate) thường đè giá nominally, nhưng Sep-2026 supply shock (Hormuz) áp đảo → oil lên **cùng** USD lên | Kết cặp hiếm "USD lên + oil lên" chỉ tồn tại khi supply shock lớn hơn liquidity effect |
| NATGAS | Kết nối USD yếu hơn oil; chủ yếu weather/storage + LNG | HH decoupled TTF — yếu tố USD chỉ là noise |

### 1.4. Rủi ro tài khóa / chính trị Mỹ

1. **Debt issuance & term premium**: 30Y yield vùng high-2007 (Aug selloff) — supply áp lực đều tháng qua auctions; nếu refunding quarterly (Nov) công bố issuance lớn hơn → term premium lên → USD short-end mạnh nhưng risk assets/gold chịu.
2. **Section 338 trade war**: thuế 50% + đe thêm 50% cho auto từ 01/01/2027 (theo context lane — cần kiểm chứng chi tiết văn bản): kênh (a) giá nhập → CPI thêm nóng → Fed hike thêm; (b) retaliation → hit exporters/earnings → risk-off; (c) nếu đàm phán gỡ → disinflation shockdown.
3. **Mid-term 03/11/2026**: chia Cam Tòa Bạch Ốc + quan hệ White House–Fed là variable chính trị lớn nhất Q4; kết quả có lợi cho pressure-Nới Fed → dovish USD risk.
4. **Fed–White House conflict**: đã là bid-asset cho vol USD; mọi hearing/phát ngôn Trump–Warsh là scheduled event rủi ro.

### 1.5. DXY composition & dollar cycle

- **Composition (cố định)**: EUR 57.6%, JPY 13.6%, GBP 11.9%, CAD 9.1%, SEK 4.2%, CHF 3.6% → DXY thực chất là "anti-EUR + anti-JPY" basket; 71.2% trọng số là EUR+JPY+GBP — tức **3 currency core của file này chi phối ~83% DXY**.
- **Dollar cycle phases (framework 15–20 năm, dạng prior knowledge — đo lại bằng data trước khi dùng)**:
  1. **Phase 1 — Monetary divergence mở** (Fed hike đầu chu kỳ khi khác CB còn ease): USD trend mạnh nhất. *Sep-2026 đang ở dạng muộn của phase này — nhưng khác biệt: ECB/BoE cũng hawkish → divergence đến từ mức xuất phát, không phải hướng.*
  2. **Phase 2 — Catch-up & peak rate differential**: CB khác bắt đầu hike theo; USD choppy-top. *Đặc trưng 2026: BoE 3.75% và ECB đang đuổi → USD mạnh nhưng không parabolic (DXY ~100 statt 110+).*
  3. **Phase 3 — Divergence đóng / easing đầu**: Fed cut trước → USD xuống nhanh. *Trigger tiềm năng 2027: oil shock tắt (Hormuz mở lại) → CPI rơi → Fed pivot trước ECB.*
  4. **Phase 4 — Dollar bear bottom** (fiscal/credit stress Mỹ): hiện chưa có evidence.
- **Cách đọc hiện trạng**: DXY ~100, vừa break dưới uptrend 2026 ngắn hạn (forex.com 15/09) nhưng cấu trúc dài hạn còn lên → **đặc trưng phase-2 late: chop, không one-way** — mọi strategy USD-beta cần gate theo phase, không assume trend.

---

## 2. EUR — Eurozone

### 2.1. ECB: stance, legacy portfolios, fragmentation

- **Stance (verified)**: depo **2.50%** (hike 10/09/2026 từ 2.25%, MRO 2.65%, effective 16/09) — hike thứ hai của chuỗi re-tightening bắt đầu ~Jul/2026 sau khi chuỗi cắt 2024–25 chạm đáy 2.00%. Lý do: **energy shock đẩy HICP** (Brent $108 → EU là net energy importer). Guideline: "no preset rate path", data-dependent.
- **APP/PEPP legacy**: APP không reinvest từ 2024, PEPP reinvestments kết thúc cuối 2024 → đến Sep/2026 cả hai portfolio đều trong **passive run-off** → cung cấp một lượng maturing debt phải refinance với rate cao hơn →(torch) tightening tài chính tự động, thêm reason ECB thận trọng; quy mô run-off hiện tại cần kiểm chứng.
- **TPI (Transmission Protection Instrument)**: công cụ chống fragmentation khi cần — chưa dùng; nếu BTP-Bund bung >200bp kèm dysfunction thì TPI activation là event EUR two-way (ban đầu risk-off rồi stabilize).
- **Fragmentation risk — BTP-Bund spread**: gauge stress chính. Ngưỡng heuristic: <120bp bình thường; 150–200bp cảnh giác; >200bp kèm failure auction Ý = stress. Sep-2026 mức chính xác cần kiểm chứng; cấu trúc rủi ro: Ý fiscal + Pháp chính trị (budget fail曾多次 2024–25) + German fiscal loosening (hạ khẩu discipline chung).
- **Terms-of-trade shock**: EU nhập ~70–90% energy hóa thạch nhu cầu (heuristic); Brent +61% y/y = tỷ lệ trao đổi xấu đi 1–2% GDP kiểu 2022 → HICP lên nhưng GDP thực down = **stagflation config** — ECB hike vào tăng trưởng yếu, EUR không hưởng "hawkish currency" chuẩn.
- **ECB leadership**: nhiệm kỳ President Lagarde kết thúc **31/10/2026** — succession là event chính trị Q4 lớn cho EUR (hawkish/dovish danh tính người kế nhiệm; tình hình kế nhiệm cần kiểm chứng).

### 2.2. Dữ liệu eurozone

| Dữ liệu | Nhịp | Điểm nhấn |
|---|---|---|
| **HICP flash** | Cuối tháng | Core vs energy split — trong oil-shock, headline nóng nhưng **core mới quyết định ECB có hike tiếp** |
| **PMI flash (S&P/HCOB)** | ~ngày 23 | Composite <50 đang là baseline; >50 surprise = EUR bid |
| **German factory orders / Ifo / ZEW** | Đầu/giữa tháng | Export engine — nhạy với trade war (Section 338) cả hai chiều |
| **ECB wage tracker / negotiated wages** | Quý | Lagarde-era anchor: wage >3% y/y giữ hawkish bias |
| **Tankan-type EU sentiment + GDP flash** | Quý | Xác nhận stagflation depth |

### 2.3. Truyền dẫn

- **EURUSD**: differential nở chậm (cả hai hike) → động lượng thật đến từ (a) ToT/energy — xấu cho EUR; (b) political risk Pháp/Đức; (c) risk sentiment (EUR có beta risk-on nhẹ nhờ export cyclicality). Bias nền Sep-2026: **EURUSD chịu** nhưng có floor vì ECB cũng hawkish (CACIB forecast ~1.12–1.16 — tham khảo, cần kiểm chứng).
- **XAUUSD (qua USD)**: EUR yếu → DXY mạnh → đè gold thêm một lớp trên real-yield layer — hai lớp cùng chiều xuống trong Sep-2026.
- **EU energy demand**: Brent $108 kéo demand destruction EU + chuyển LNG — giảm trưởng → EUR risk. Ngược lại nếu Hormuz mở lại (đề nghị 25/09 của Iran) → **disinflation + EUR relief rally** là một trong các big-binary còn treo.

### 2.4. Rủi ro chính trị Pháp/Đức, fiscal rules

- **Pháp**: budgetSaga lặp lại mỗi cuối năm — vote bất tín nhiệm/fail budget = EUR gap-down theo pattern 2024–25; theo dõi cửa sổ Oct–Dec.
- **Đức**: coalition sau bầu cử 2025 (fiscal loosening — infra/defense fund) = issuance tăng → Bund supply → spread EUR hy kiểm soát; ngược lại supportive growth.
- **EU fiscal rules vs re-armament**: escape clause quốc phòng đang làm mềm Stability Pact — tốt cho growth ngắn, rủi ro rating/spread dài.
- Kết hợp gilt-stress Anh (§3): nếu **cả BTP lẫn gilt** cùng stress → "sovereign stress G7" regime → USD funding bid toàn phần + CHF/JPY haven bid.

---

## 3. GBP — Anh

### 3.1. BoE: stance, MPC split, gilt stress

- **Stance (verified)**: hold **3.75%** ngày 17/09/2026, vote **6–3** (Mann-type hawks đòi 4% — hold thứ 6 liên tiếp từ cut 12/2025). Câu văn BoE: "CPI increased to 3.1% in August and **is likely to rise further over coming quarters**" → ngôn ngữ hawkish-hold; BoE **từ chối đánh nhau với energy price bằng rate** (EY ITEM bình luận "đúng") — tức chấp nhận inflation overshoot.
- **Next meeting**: 05/11/2026 (theo context lane — cần kiểm chứng) — ngay sau mid-term Mỹ và trước Autumn Statement: cluster event risk Q4 dày.
- **MPC split dynamics**: 3 phiếu hike = highest hawkish dissent chuỗi hold → market sẽ định giá "BoE bị ép hike theo Fed" mỗi lần CPI bật; ngược lại nếu dissent rơi về 1–2 → dovish surprise. Đọc vote-count quan trọng ngang statement.
- **Gilt stress 2026 — "slow-motion mini-budget echo"**: 10Y gilt **5.378%** ngày 10/09/2026 — cao nhất từ Jul/2007 (19 năm). Khác 2022 (speed shock do mini-budget), 2026 là **slow-motion**: tích lũy từ (a) global term premium selloff; (b) UK issuance + fiscal credibility vết sẹo 2022; (c) inflation above-target + MPC không hành động → bond market "thay Fed hành phạt". **Signature phải xem: gilt lên + GBP xuống cùng lúc = credibility channel ON** (kiểu 2022) — nếu gilt lên nhưng GBP cũng lên (real yield attract) thì là "clean tightening" (bullish GBP). Sep-2026 đang nghiêng về kênh nào cần đo bằng correlation rolling — đây là một trong những gate quan trọng nhất cho GBP lane.
- **Fiscal event risk**: Autumn Statement (thường Nov/Dec) là event lớn nhất GBP trong quý; nếu OBR forecast xấu / issuance lớn → lặp gilt spike; fiscal giveaway có kiểm soát → GBP kễ.

### 3.2. Dữ liệu Anh

| Dữ liệu | Nhịp | Điểm nhấn Sep-2026 |
|---|---|---|
| **CPI** | Giữa tháng | 3.1% Aug (verified), hướng lên theo BoE — surprise lên → push hike odds + gilt; tác động GBP **phụ thuộc channel** (xem §3.1 credibility test) |
| **Labor/earnings** | Thứ Ba giữa tháng | AWE (incl. bonus) — sticky services inflation anchor |
| **PMI flash** | ~23 | Services PMI là proxy GDP Anh |
| **GDP monthly / retail sales** | Cuối/giữa tháng | Confirmation stagnation vs stagflation |
| **Gilt auctions / DMO calendar** | Theo lịch DMO | Direct gilt-stress feed — thêm dimension mà USD/EUR ít nhạy bằng |

### 3.3. Truyền dẫn

- **GBPUSD**: có rate parity với Fed (3.75 vs 3.75–4.00) → động lượng đến từ gilt stress + UK inflation idiosyncrasy; Fed hike thêm (Dec) trong khi BoE hold → differential nghiêng lại cho USD → **GBPUSD bias xuống nhưng gap-risk hai chiều quanh gilt events**.
- **EURGBP**: BoE 3.75% vs ECB 2.50% = **carry dương cho GBP** → EURGBP có structural floor; chỉ gãy khi gilt stress chuyển thành credibility event (GBP bị bán bất chấp yield) hoặc ECB hike bắt kịp (2.75–3.00% vào 2027).
- **Cross-asset**: gilt stress lan ra = risk-off khu vực + USD bid; GBP là "canary" của sovereign-bond stress G7 cùng BTP.

---

## 4. JPY — Nhật

### 4.1. BoJ: rate & normalization path

- **Policy rate ~1.00%** (hike 12/2025 lên mức cao 30 năm — verified qua lane từ Reuters/MS). Năm 2026: Jan hold; Apr vote chia rẽ lớn nhất 10 năm; Jul stand-pat với OIS ~69% hike trước Oct; **meeting Sep/2026 (kỳ vọng 25bp) — kết quả cần kiểm chứng**; Reuters 08/09 ghi nhận cú yen surge +4.5%/tuần có đóng góp từ "BOJ rate bets" → market đang nghiêng hike.
- **Cadence Ueda**: 8 meeting/năm + Outlook Report (Apr/Oct) + branch managers (Jan/Apr/Jul/Oct) + SOO (~10 ngày sau meeting) + Minutes (~1 tháng) — board split 2026 khiến **SOO thành event dịch giá thật** (leak dissent).
- **Điều kiện hike của BoJ**: wage-price virtuous cycle — Shunto (Feb–Mar) là annual binary lớn; Tokyo CPI cuối tháng là leading indicator CPI toàn quốc; Tankan (đầu quý) cho capex.
- **YCC đã dứt điểm (3/2024)**, JGB purchases taper → JGB 10Y yield tự do hơn → kênh UST–JGB spread sống lại: **GB 10Y Nhật lên theo UST là pressure hike BoJ** — trong Sep-2026 UST 10Y vùng high → BoJ bị "kéo" hike; đây là feedback loop: Fed hawkish → BoJ gần hike hơn → JPY mạnh hơn → intervention thấp hơn.

### 4.2. MOF intervention: lịch sử 2022–2026 + fingerprints

- **Các episode đã verify** (lane USDJPY): 22/09/2022 (~145.9) & 21/10/2022 (~151.9) — tổng 2022 ¥9.2trn (yen-buying đầu tiên từ 1998); 29/04 & 01–02/05/2024 (~157–158, ¥9.8trn); 11–12/07/2024 (~161.9, ¥5.5trn); **Jul–Aug/2026: phối hợp Nhật–Mỹ** sau khi yen chạm đáy 40 năm **163.99** (23/07/2026) — joint đầu tiên từ ~2011; Nhật ước **$53bn/1 ngày** (kỷ lục), tổng đợt ~$75–100bn tùy nguồn (Vantage: ¥15.4trn/tháng), Mỹ tham gia mức không công bố (lane ước $5–10bn) **(tổng cần kiểm chứng)**. Kết quả: 164 → bật >1% → trôi lại ~163 giữa Aug → quay lại >160 cuối Aug → **yen surge 4.5%/tuần về 152.89 (08/09)** — Reuters: "upsets the carry trade faithful" → Sep dao động **152.9–154.5**, "suspected rate check" giữa tháng.
- **Verbal intervention patterns**: bậc thang escalate — (1) FM phát ngôn "watching with sense of urgency" → (2) Vice FM Mimura "excessive one-sided moves" → (3) **rate check** (hỏi giá bank — tín hiệu bán-forward can thiệp thật) → (4) can thiệp. Tên FM hiện tại: lane ghi Kato, một số tin Sep ghi Katayama **(cần kiểm chứng — có thể thay đổi sau cabinet shuffle)**. Political backing: Trump đã trực tiếp than phiền weak-yen với PM → MOF có "được phép" hành động hai chiều.
- **Sight-deposit / volume proxy**: MOF công bố **daily sight deposits** (BoJ account) — nhảy vọt thứ Sáu = funding cho can thiệp tuần đó; **monthly intervention disclosure** cuối tháng kế tiếp (ex-post) → backtest intraday dùng disclosure là lookahead bias kinh điển (lane USDJPY đã cảnh báo).
- **Ranh木齐 hoạt động 2026**: vùng **160+ với tốc độ >2%/tuần** = trigger can thiệp bán USDJPY; vùng **<145 quá nhanh** = rủi ro can thiệp chiều ngược (mua yen quá mạnh) — hiện tại nguy cơcan thiệp tiếp còn treo vì CACIB/end-2026 forecasts còn ~160: bất kỳ cú drift nào về 158–160 đều vào "intervention watch".

### 4.3. Carry mechanics

- **JPY = funding currency của global carry**: differential USD–JPY ~275–300bp (Fed 3.75–4.00 vs BoJ 1.00) — carry **thuận chiều USD nhưng "đậm" giảm** so với 525bp của 2023–24 → carry payoff/vol ratio tệ đi đáng kể; trong khi đó JPY vừa +4.5%/tuần (08/09) — carry P&L một tuần bị xóa.
- **Carry-unwind template (Aug/2024)**: BoJ hawkish surprise + US data yếu → differential kỳ vọng thu hẹp → unwind hàng loạt: Nikkei −12.4% (05/08/2024), VIX intraday ~65, AUDJPY/USDJPY gap-down, CHF bid cùng JPY. **Sep-2026 có đủ nguyên liệu lại** (BoJ Sep hike bets + Fed at peak + risk premium geo) — carry ON/OFF phải gate bằng:
  - **AUDJPY** — "carry thermometer": break xuống kèm vol = unwind starting.
  - **VIX term-structure**: contango bình thường; backwardation (M1>M2) = funding stress, short-carry warning.
  - **Carry/vol ratio**: basket forward yield ÷ implied vol — khi <0.5, carry không còn trả đủ cho tail risk.
- **Feedback với 12 symbols**: unwind JPY = JPY mạnh + CHF mạnh + USD biến động + equities xuống + AUD/NZD bán + gold hai chiều (unwind đầu: gold bị bán để cover margin; unwind sau: gold bid nếu Fed cut được price).

---

## 5. Cross-cutting — các chế độ vĩ mô chung

### 5.1. Dollar cycle phases × 12 symbols

| Phase | DXY | EURUSD/GBPUSD/AUDUSD/NZDUSD | USDJPY | USDCAD/USDCHF | XAU/XAG | BRENT/WTI/NATGAS |
|---|---|---|---|---|---|---|
| 1. Divergence mở (Fed hike một mình) | Trend mạnh lên | Trend xuống | Lên mạnh (diff) | CHF xuống (carry), CAD tùy oil | Real yield lên → xuống | USD đè nominally |
| 2. Catch-up/peak diff (**Sep-2026 ở đây**) | Chop-top ~100 | Range, idiosyncratic chi phối (gilt/BTP/toT) | Lên nhưng intervention-capped | Ngoại lệ CAD (oil>diff) | Real yield vẫn chủ đạo; inverse-DXY gãy | Supply shock có thể áp đảo USD effect (đang vậy) |
| 3. Fed pivot trước | Xuống nhanh | Lên nhanh | Xuống nhanh (diff thu) | CHF lên | Real yield rơi → gold lên mạnh | Bull nếu đồng USD yếu + demand sống |
| 4. US fiscal/credit stress | Xuống + funding bid two-way | EUR lên "dù sao" | Phức tạp — haven cả hai | CHF/JPY bid mạnh nhất | Parabolic nếu kèm inflation | Risk-off đè |

### 5.2. Carry index — cách dựng & ON/OFF

- **Cách dựng**: basket rate-differential: mỗi cặp dùng forward-implied 3M differential (hoặc policy-rate differential nếu forward không có) × sign theo hướng funding→asset; peso: USDJPY, AUDJPY, EURJPY, USDCAD, AUDUSD, NZDUSD. Chuẩn hóa bằng realized vol → **carry/vol ratio** là biến regime chính, không phải carry thuần.
- **Carry ON**: ratio cao, VIX contango, ranges hẹp, IMM positioning chưa cực đoan → các strategy trend/breakout trên USDXXX chạy.
- **Carry OFF**: ratio <0.5, VIX backwardation, hoặc **JPY intervention window active** (Sep-2026: OFF-điều-kiện — carry thuận về rate nhưng unwind risk sống) → cắt leverage, giảm size, bật mean-reversion/de-haven legs (JPY, CHF long).

### 5.3. Risk sentiment regimes — nhận diện & mapping

- **Đồng hồ**: VIX (level + term structure), gold-vs-DXY relative, HY credit spreads (HY OAS >450bp = stress), AUDJPY, Nikkei vs S&P relative.
- **Quan trọng Sep-2026 — gold không còn safe-haven chuẩn**: kênh rate (real yield 2.85%) đang **đè lên** kênh haven; geo escalates → CPI → Fed hawkish → gold **xuống** (đã xảy ra 28/09: Hormuz căng + gold −3.25%). Safe-haven hierarchy hiện tại: **JPY, CHF, USD-funding > gold** — chỉ khi stress dạng **financial** (banking/credit, khi market price Fed **cut**) thì gold mới bid bền (kênh rates cùng chiều haven).
- Mapping: risk-off thật (credit+equity) → JPY/CHF bid, AUD/NZD offered, USD hai chiều (funding bid vs haven giải phóng), oil xuống nếu demand-shock (nhưng **Sep-2026 oil là supply-shock: oil lên cùng risk-off** — dạng 1970s stagflation-shock, hiếm).

### 5.4. Regime đặc thù "Hike-cycle + oil-shock" (đang sống) — ai hưởng, ai chịu

- **Hưởng**: USD (inflation-first Fed), energy complex (BRENT/WTI supply-driven), CAD có lợi cấu trúc từ oil nhưng bị differential đè (nửa vời), NOK/energy exporters ngoài universe.
- **Chịu**: **gold/silver** (real yield đè — đã −26%), **EUR** (energy ToT), **JPY** (import energy + differential) **NHƯNG** được intervention floor + BoJ hike bets — JPY là phức tạp nhất: yếu về cơ bản, mạnh về chính sách.
- **Kịch bản đổi regime (các binary còn treo)**: (a) Hormuz mở lại (đề nghị 7 ngày của Iran 25/09 còn trên bàn) → disinflation shock → gold bounce mạnh nhất, USD ra khỏi phase-2; (b) escalation → $130+ oil → stagflation sâu, Fed hike vào recession → cuối cùng pivot → phase 3; (c) BoJ Sep hike hawkish → carry unwind global kiểu Aug/2024.

---

## 6. Coupling rules (overlay hypotheses)

Quy ước: mỗi rule = IF điều kiện vĩ mô THEN bias/gate cho symbol(s) — kèm logic kinh tế & **điều kiện thoát (kill-switch)**. Tất cả là hypothesis cần kiểm định bằng data trước khi lên production. Độ ưu tiên thử nghiệm: C01–C05 trùm regime hiện tại.

**Nhóm A — regime hiện tại (hike + oil war + JPY intervention)**

- **C01 — Real-yield vise**: IF Δ10Y TIPS +10bp trong ≤5 ngày THEN bias short XAUUSD/XAGUSD (đặt sell-rally), bỏ qua tín hiệu DXY. Logic: kênh opportunity cost đè mọi kênh khác (Sep-2026 đã diễn ra). Thoát: real yield đảo chiều 2 phiên liên tiếp hoặc VIX >32 (chuyển haven-bid).
- **C02 — Intervention ceiling USDJPY**: IF USDJPY >158 AND tốc độ tăng >2%/tuần AND có rate check/verbal bậc-2 THEN cấm long breakout USDJPY, bật bias short có stop trên 161. Logic: MOF đã chứng kiến ở 163.99 (Jul/2026) — 158–160 là "warning track". Thoát: MOF disclosure cho thấy không hành động + giá consolidate 5 phiên dưới 158.
- **C03 — Carry-unwind starter**: IF BoJ hike (hoặc hike-bets OIS >80% giữa 2 meeting) AND AUDJPY break 20-day low kèm VIX >22 THEN mở legs unwind: long JPY (short AUDJPY), long CHF, giảm AUD/NZD long. Logic: template Aug/2024. Thoát: AUDJPY reclaim 20-day MA + VIX contango trở lại.
- **C04 — Oil-shock vs USD conflict**: IF Brent +5%/tuần AND DXY cùng +0.5% THEN giảm size mọi long commodity-FX (AUD/CAD) vì hai driver đánh nhau; chỉ giữ long BRENT/WTI (supply-shock thuần). Thoát: correlation Brent–DXY đảo dấu.
- **C05 — Hormuz binary**: IF có headline breakthrough mở eo Hormuz THEN thiết lập disinflation basket: long XAUUSD + short USD (EURUSD/GBPUSD long) + short energy. Logic: single event gỡ đồng thời CPI-path + ToT + term premium. Thoát: headline bị phủ nhận trong 48h.

**Nhóm B — Fed / dữ liệu Mỹ**

- **C06 — CPI là vua**: IF core CPI m/m surprise ±0.1pp trong regime Fed inflation-first THEN tăng size gấp đôi phản ứng DXY-proxy (EURUSD/USDJPY) so với NFP surprise tương đương. Thoát: Fed chuyển ngôn ngữ cân bằng (mention employment risk ngang inflation).
- **C07 — Payroll fade in hike-regime**: IF NFP blowout (+250k) trong Fed inflation-first THEN phản ứng USD ban đầu mạnh nhưng fade 50% trong phiên nếu AHE yếu — không chase. Thoát: rule chết khi AWE/AHE surprise cùng dấu payroll.
- **C08 — Auction tail → term-premium trade**: IF 30Y auction tail >2bp THEN bias long USD vs commodity-FX (AUD/NZD) + áp lực XAUUSD, vì term premium lên = real yield lên. Thoát: tail bị reverse trong phiên.
- **C09 — Fed-independence premium**: IF headline xung đột Trump–Warsh escalates THEN bật mode "hawkish-defiance": bias USD lên + vol nở (straddle-friendly), DXY chop 0.5%+ ngày. Thoát: cả hai bên im 1 tuần.
- **C10 — Mid-term binary (03/11/2026)**: IF kết quả mid-term nghiêng "thắng phe gây áp lực nới Fed" THEN bias USD xuống trước kỳ họp Dec FOMC; ngược lại giữ hawkish baseline. Thoát: pricing OIS Dec quay về >90% hike.

**Nhóm C — EUR / UK / EU**

- **C11 — Stagflation-EUR ceiling**: IF Brent >$105 AND eurozone composite PMI <50 THEN cap mọi long EURUSD (dù ECB hike) — ToT đè. Thoát: PMI reclaim 50 hoặc Brent <$90.
- **C12 — BTP stress contagion**: IF BTP–Bund >180bp AND tăng 20bp/tuần THEN bias EUR xuống toàn phần + risk-off nhẹ (bán AUD, mua CHF); TPI-activation là điểm stabilize (đóng bias). Thoát: spread <150bp.
- **C13 — Gilt credibility test**: IF gilt 10Y +15bp/tuần AND GBPUSD **cùng xuống** (credibility channel) THEN bias short GBPUSD + short EURGBP (GBP yếu hơn cả EUR); nếu gilt lên mà GBP cũng lên thì **tắt** bias (clean tightening bullish GBP). Thoát: signal trong rule.
- **C14 — MPC vote-count trade**: IF dissent hike ≥3 (như 17/09: 6–3) THEN mỗi CPI surprise lên có beta GBP dương gấp đôi bình thường (short-hike-squeeze). Thoát: dissent rơi ≤1.
- **C15 — Autumn Statement straddle**: IF 5 phiên trước Autumn Statement THEN không giữ naked GBP position qua event; straddle/option thay spot. Logic: event risk phân phối đuôi lớn hai chiều (2022 precedent). Thoát: statement qua + OBR forecast được digest.

**Nhóm D — JPY / carry**

- **C16 — Verbal ladder entry**: IF Vice-Mimura-grade verbal "excessive one-sided" (bậc 2) THEN scale vào short USDJPY 1/3 size, thêm mỗi bậc escalate (rate check = bậc 3), can thiệp thật = full nhưng trailing chặt. Thoát: giá reclaim high trước verbal +3%.
- **C17 — Tokyo-CPI/BoJ-hike correlation**: IF Tokyo CPI (cuối tháng) core y/y >2.5% AND Shunto wage >5% THEN bias long JPY trước meeting BoJ kề (event-pre positioning). Thoát: meeting qua không hike (dùng stop qua-event thay vì hold tin).
- **C18 — UST-led USDJPY**: IF ΔUST10Y ±15bp/5 ngày THEN bias USDJPY cùng dấu — NHỮNG tắt hoàn toàn nếu USDJPY trong intervention window (C02). Thoát: correlation 10-day rolling về <0.3.
- **C19 — Yen-strength spillover**: IF JPY surge >2%/tuần (intervention hoặc BoJ) THEN CHF bid theo + AUD/NZD/NOK offered + Nikkei-applied risk-off — mở các bias này thay vì追 USDJPY đã chạy. Thoát: USDJPY stabilize (ATR 5 ngày < ATR 20 ngày).

**Nhóm E — risk regime / cross-asset**

- **C20 — VIX regime switch**: IF VIX >28 AND backwardation THEN mọi carry-định-value strategy OFF; bật haven basket long JPY/CHF; giảm 50% size toàn symbol. Thoát: VIX <22 + contango.
- **C21 — Gold-safe-haven conditioner**: IF geo-escalation headline AND real yield 5 ngày đi ngang THEN long XAUUSD (haven channel sống); IF real yield đang +10bp/tuần THEN **fade** phản ứng haven đầu tiên (sell into spike). Đặc trưng Sep-2026: nhánh fade là đúng.
- **C22 — Supply-shock oil định vị**: IF oil +5%/tuần do geo (không phải demand data) THEN (a) bias short JPY (energy import), (b) bias EUR xuống, (c) **không** short oil vì "risk-off". Thoát: backwardation Brent những tuần sau (spot premium phai).
- **C23 — CAD anomaly**: IF Brent >$100 AND policy diff Fed–BoC >100bp (nghiêng USD) THEN USDCAD range-bias — không trade oil-beta CAD thuần; chỉ trade khi một trong hai driver tắt. Thoát: BoC path thay đổi hoặc oil <$90.
- **C24 — Silver beta-leverage**: IF tín hiệu gold-direction ON (từ C01/C21) THEN dùng XAGUSD làm beta-đòn (1.3–1.5x) cho cỡ size nhỏ + stop rộng tương ứng. Thoát: G/S ratio break 20-day trend ngược hướng gold.
- **C25 — Quarter-end flow seasonality**: IF 3 phiên cuối quý AND tháng 3/9 THEN bật mode range-fade quanh Tokyo fix + WM/R 4pm London (rebalance flows) — giảm size break-out. Thoát: qua fix + first week quý mới.
- **C26 — Dollar-phase meta-gate**: IF DXY break cấu trúc 6 tháng (như break dưới uptrend 15/09) THEN hạ weight mọi strategy pure USD-beta xuống 50% và tăng weight idiosyncratic (JPY/GBP narratives) cho đến khi phase mới xác nhận (2 tháng close). Logic: phase-2 chop-top giết cả trend lẫn MR nếu không phân loại. Thoát: xác nhận phase mới.

*(26 rules — phủ: regime hiện tại C01–C05, từng CB C06–C18, cross-asset C19–C24, cấu trúc/thời vụ C25–C26. Nhóm "disinflation/easing" được nhét qua C05/C10/C13 — khi Fed pivot được price, priorities đảo: C05 trở thành rule nền.)*

---

## 7. Lịch vĩ mô tuần chuẩn (skeleton)

Tuần mẫu chuẩn (mùa thu 2026 — có FOMC vừa qua, CPI mới, BoE vừa hold). Giờ = ET (US), lệch DST lưu ý khi build calendar tự động.

| Ngày | Release chính (US) | Release khác (EU/UK/JP) | Symbol nhạy nhất | Độ nhạy |
|---|---|---|---|---|
| **Thứ Hai** | Nhẹ (Fed speeches cuối ngày có thể) | EU: ít; JP: đôi khi speech BoJ | Toàn bộ mở tuần theo narrative cuối tuần; gap risk từ weekend geo (Hormuz/JPY) | Thấp–vừa; đầu tuần châu Á mỏng |
| **Thứ Ba** | NY Fed manufacturing; đôi khi Fed speakers | DE: ZEW (giữa tháng); UK: labor/earnings (tuần giữa tháng); JP: thỉnh thoảng data | EURUSD (ZEW), GBPUSD (earnings) | Vừa |
| **Thứ Ba (tuần flash-PMI ~23)** | — | **PMI flash US+EU+UK 9:00/9:45 ET** | EURUSD, GBPUSD, risk assets | Cao |
| **Thứ Tư** | Nhà ở (existing/new sales); FOMC các tuần có meeting (14:00 + presser 14:30) | — | USD-all; XAUUSD (FOMC ngày); USDJPY (dot-path) | FOMC: rất cao; housing: thấp |
| **Thứ Năm** | **Claims 8:30**; đôi khi GDP/PCE final; UST auctions 13:00 | ECB meeting các tuần có (thứ Năm — như 10/09); DE: Ifo (cuối tháng); **JP: Tankan (đầu quý), BoJ meeting thi thoảng** | EURUSD (ECB), USDJPY (BoJ/Tankan), DXY (claims/auction) | Vừa–cao |
| **Thứ Sáu** | **NFP (thứ Sáu đầu tháng) 8:00–8:30**; UMich sentiment; đôi khi retail sales | JP: Tokyo CPI (cuối tháng); UK: retail sales/GDP monthly (cuối tuần) | Tất cả USD-pairs; XAUUSD; sau NFP: vol toàn phần | NFP: rất cao |
| **Giữa tháng (tuần CPI)** | **US CPI 8:30 (Thứ Ba/Wed/Thu tùy tháng)**; retail sales; PPI | UK CPI; DE/EA HICP final | XAUUSD/XAGUSD (cao nhất), EURUSD, DXY-proxy | Rất cao (regime inflation-first) |
| **Cuối tháng** | **PCE 8:30**; GDP final; month-end rebalance | **EA HICP flash** (ngày cuối/thứ Năm cuối); MOF intervention disclosure (cuối tháng kế tiếp); CFTC COT 15:30 thứ Sáu | XAUUSD (PCE), EURUSD (HICP), JPY-pairs (disclosure) | Vừa–cao |
| **Quý (mốc)** | FOMC Oct 27–28, Dec 8–9 **(cần kiểm chứng)**; refunding quarterly; mid-term 03/11 | **BoE 05/11 (cần kiểm chứng)**; Autumn Statement (Nov/Dec); ECB họp 8 lần/năm (thứ Năm); BoJ 8 lần/năm + Outlook Apr/Oct; Lagarde term hết 31/10 | Cluster Q4 dày nhất năm | Event-driven |

**Nguyên tắc xếp hạng độ nhạy cho 12-symbol (regime Sep-2026)**: CPI-US > FOMC/SEP > BoJ/MOF-event > ECB > BoE/gilt-auction > NFP > PMI flash > PCE > phần còn lại. Áp cho calendar-based sizing của mọi symbol lane.

---

## 8. Danh mục "(cần kiểm chứng)" tập hợp (verify checklist cho lane sau)

1. Kết quả BoJ meeting Sep/2026 (kỳ vọng hike 25bp) và OIS hiện hành.
2. Tên FM Nhật (Kato vs Katayama) sau cabinet shuffle; PM Takaichi chính xác.
3. Tổng quy mô can thiệp Jul–Aug/2026 (các nguồn: $53bn/1 ngày; $75bn; $98.6bn; ¥15.4trn/tháng — cần khoanh bằng MOF disclosure monthly).
4. UST 10Y nominal hiện tại (mâu thuẫn 4.78% vs ~5.2% theo nguồn lane XAUUSD/Kitco).
5. GSR & silver quote nhất quán (lane XAUUSD: $61.12, GSR 67.9 ngày 28/09 vs context $65.5–67).
6. BoC policy rate hiện tại (cho rule C23) và RBA/RBNZ stance (cho AUD/NZD mapping).
7. Lịch FOMC Oct 27–28 / Dec 8–9, BoE 05/11, ngày Autumn Statement.
8. BTP–Bund spread mức hiện tại; PEPP/APP run-off pace hiện tại.
9. Tình trạng kế nhiệm ECB President (nhiệm kỳ Lagarde hết 31/10/2026).
10. Section 338 chi tiết văn bản & timeline auto-tariff 01/01/2027.
11. DXY quote close chính xác (chỉ có range ~98–103, resistance 100.54).
12. Fed framework review 2025 chi tiết & quy mô QT hiện tại.

— Hết file MACRO_CORE.
