# Bản đồ yếu tố quốc gia/đồng tiền — BLOC (CAD, AUD, NZD, CHF)

- Program: `FOREX-UNIFIED-STRATEGY-BRAINSTORM-V1` · Lane: MACRO-BLOC · Ngày: 2026-09-28
- Tính chất: **knowledge-only brainstorm** (NO backtest, NO Python, NO data pull). Mọi
  ngưỡng/tương quan là *prior cấu trúc* cho phase đo lường — trạng thái mặc định **NOT_RUN**.
- Phạm vi: overlay vĩ mô cho 4 đồng tiền khối "bloc" — CAD, AUD, NZD, CHF — dùng làm
  gate/bias cho các lane symbol USDCAD, AUDUSD, NZDUSD, USDCHF và các cross
  (AUDNZD, AUDCAD, CADJPY, CHFJPY...).
- Trạng thái verify 2026-09-28 (WebSearch + kế thừa từ 12 lane symbol):
  - **Fed**: hike 25bp ngày 16/09/2026 → **3.75–4.00%** (lần đầu sau 07/2023; Chair Warsh;
    SEP dots ~4.1% cuối 2026 → hàm ý thêm 1 hike; FOMC kế 27–28/10). [verified]
  - **BoC**: giữ **2.25%** ngày 02/09/2026 (hold lần 7 liên tiếp; lần thay đổi cuối là cut
    25bp ngày 29/10/2025); Bank Rate 2.50%, deposit 2.20%; họp kế **28/10/2026** kèm MPR.
    Statement nêu "broadening recovery" + cảnh báo **upside inflation risk do oil
    pass-through (Hormuz) và chi phí thuế quan**. [verified]
  - **RBA**: cash rate **4.35%** (hold tại họp 08/2026; đã hike 3 lần trong 2026 từ 3.60%);
    họp **28–29/09/2026**, quyết định **29/09 14:30 AEST (04:30 UTC)**; CBA + 90% panel
    Finder dự hike 25bp → **4.60%** (mức cao nhất từ 2011); AU CPI tháng 7 về 3.5% y/y.
    **Kết quả thực tế chưa công bố tại thời điểm viết → (cần kiểm chứng)**.
  - **RBNZ**: **hike 25bp → OCR 2.75%** ngày 02/09/2026 (từ 2.50%); Governor **Anna
    Breman** phát biểu "có thể dành thời gian đánh giá" (nghiêng **pause**); track dự báo
    OCR 2.81% 12/2026, 3.12% 09/2027. MPC kế tiếp ~cuối 10/2026 **(cần kiểm chứng ngày)**. [verified]
  - **SNB**: giữ **0%** ngày 24/09/2026 (không đổi từ cut 06/2025); tuyên bố "sẵn sàng hoạt
    động trên thị trường ngoại hối" (willing to be active in FX market); 16/24 economist
    kỳ hold qua 2027; MPA kế **10/12/2026**. Sight deposits hiện tại WoW **(cần kiểm chứng
    số mới nhất)**; heuristic lịch sử: +11.2 tỷ CHF một tuần 07/2025. [verified]
  - Differential vs Fed (mid 3.875%): Fed−BoC **+150/175bp** (USD); RBA−Fed **+35…+60bp**
    (AUD, dương nhẹ); Fed−RBNZ **+112.5bp** (NZD funding leg −100~−125bp); Fed−SNB
    **+375bp** (thuận carry long USDCHF).
  - Commodity/geopolitics: war Mỹ–Iran + Hormuz ON (Brent đỉnh ~$108, WTI >$100, whipsaw
    $90→108→90→104 trong 3 tuần 9/2026); Section 338 (thuế 50% từ 22/08, **import bans
    29/09/2026**, đe 50% auto từ 01/01/2027); iron ore ~$90/t; gold ~$4,144 (−26% từ ATH);
    silver ~$65.5–67; GDT WMP là driver NZD. [kế thừa lane symbol — mức giá spot (cần
    kiểm chứng bằng tick data)]
  - Spot landmark: USDCAD ~1.40–1.41; NZDUSD trượt 0.59 → ~0.572. (cần kiểm chứng)

---

## 1. CAD — Canada

### 1.1 BoC — stance, mandate, cadence

- **Mandate**: inflation-targeting 2% CPI (midpoint 1–3%), chung với Chính phủ; phiên bản
  2021+ có ba  ưu tiên "make life more affordable / growth / net-zero" nhưng trong thực
  hành reaction function vẫn là CPI-first với labour-market slack làm điều kiện hai.
- **Cadence**: 8 quyết định/năm, 4 bản MPR (Jan/Apr/Jul/Oct). Quyết định **09:45 ET**,
  presser 10:30 ET — "một cửa thông tin" trùng khung data Mỹ (8:30–14:00 ET), khác biệt
  cấu trúc so với các CB khác châu Á/châu Âu.
- **Stance hiện tại (Sep-2026)**: hold 2.25% kéo dài (7 lần), nhưng statement 02/09 chuyển
  sang **hold with hawkish risk** — cảnh báo oil pass-through (Hormuz) + chi phí thuế quan
  đẩy inflation lệch lên. Meeting **28/10/2026 kèm MPR** là event sống: OIS priced hold
  nhưng tail hike không đá; press từng dùng "may need to hike".
- Khung đọc BoC 2026: BoC kẹt giữa **cost-push từ thuế quan** (bóp growth, đẩy giá) và
  **petro-income từ oil $100+** — hai lực cùng đẩy CPI lên nhưng khác hàm ý growth →
  statement language ("pass-through", "inflation risks") quan trọng ngang quyết định rate.

### 1.2 Dữ liệu

| Data | Nhịp/giờ (ET) | Vai trò |
|---|---|---|
| CPI (StatCan) | ~15–21 hàng tháng, 8:30 | Reaction function trực tiếp; trim/core là số BoC nhìn |
| LFS employment | Thứ Sáu đầu tiên, 8:30 — **trùng slot NFP Mỹ** | Double-foot: phải dùng net-surprise (z_US − β·z_CA) |
| Ivey PMI | ~đầu tháng, 10:00 | Business activity, lead nhẹ monthly GDP |
| Retail sales / monthly GDP | giữa–cuối tháng, 8:30 | Growth differential vs US |
| Housing (Teranet/NHV, starts) | giữa/cuối tháng | Household wealth channel — Canada nhạy housing |
| BoC Business Outlook Survey | quý | Capex/credit intentions, "real economy" CAD |
| US CPI/NFP/ISM | 8:30/10:00 | USD-leg + spill sang Canada (72% export sang Mỹ) |

### 1.3 Terms of trade: oil → CAD

- Chuỗi chuẩn: WTI/Brent → WCS revenue (Canada bán heavy crude) → corporate hedging &
  conversion flow → CAD spot. Chuỗi **chậm (ngày–tuần)** vì hedger flow cập nhật theo ky.
- **WCS differential** (WCS tại Hardisty − WTI): nở >$15–20 = chokepoint (pipeline, wildfire
  Alberta, refinery outage Gulf) → CAD yếu dù WTI đi ngang. Post-TMX (05/2024) differential
  trung bình hẹp hơn; giá trị Sep-2026 **(cần kiểm chứng)**.
- Pipeline capacity: TMX + Keystone + Enbridge mainline là trần vận chuyển; mọi outage/
  apportionment là shock WCS riêng không thấy ở WTI.
- **Nghịch lý Sep-2026 (case điển hình ToT bị lấn át)**: oil >$100 (petro-bullish) nhưng
  CAD vẫn yếu vì (i) differential Fed−BoC +150/175bp nghiêng USD, (ii) **Section 338 trade
  war** (thuế 50% + import bans 29/09 + đe auto 2027 — ước tác động tiêu cực export/GDP
  Canada), (iii) risk-off hỗ trợ USD. Kết quả: USDCAD ~1.40+ khi oil $100+ — bằng chứng
  sống rằng single-factor petro model chết trong regime này.
- Quan hệ WTI/Brent: spread Brent–WTI nở → Gulf refiners chạy mạnh → cầu WCS tăng nhẹ →
  CAD-friendly (proxy thô cho WCS demand).

### 1.4 Rủi ro đặc thù

- **USMCA/Section 338**: Mỹ từ chối gia hạn tự động USMCA tại review 6 năm (hè 2026);
  thuế 50% ~$20B hàng CA (22/08), Canada trả đũa dollar-for-dollar (08/09), điều chỉnh
  phạm vi 15/09, **import bans alcohol/dairy hiệu lực 29/09/2026**, đe 50% auto/steel
  01/01/2027. Đây là structural-drag vĩnh viễn hóa cho CAD — không chỉ headline.
- **Household debt**: trong nhóm cao nhất G10 (~170%+ disposable income, cần kiểm chứng
  số mới); housing correction + thuế quan đánh cùng lúc vào confidence.
- **Housing**: starts/price sửa đổi chậm ToT channel; Teranet là chỉ báo wealth-effect.
- **Political/flow**: PM Carney (cựu Governor BoC/BoE) — market-savvy, chiến lược
  diversify khỏi Mỹ; Canadian investors bán kỷ lục **C$31B** cổ phiếu Mỹ tháng 7/2026 +
  6 tháng giảm UST liên tiếp → **repatriation bid cho CAD** — lực cân với carry USD.

---

## 2. AUD — Úc

### 2.1 RBA — stance, cadence, tone

- **Cadence**: 8 họp/năm ~6 tuần một lần (kế tiếp **28–29/09/2026**, quyết định 29/09
  14:30 AEST = 04:30 UTC — book mỏng giờ này, spike hai chiều rồi chọn hướng); minutes sau
  2 tuần; SMP May/Nov.
- **Stance**: cash rate **4.35%** sau 3 lần hike trong 2026 (từ 3.60%) — hiking cycle
  hiếm có trong G10 2026. Kỳ vọng họp 09/2026: hike 25bp → **4.60%** (CBA, 90% Finder
  panel) — **kết quả (cần kiểm chứng khi công bố 29/09)**. AU CPI 3.5% y/y (tháng 7) —
  vẫn trên band 2–3% mục tiêu, labour market chắc.
- Governor tone: hawkish-leaning; presser sau quyết định là nơi drift 48–72h hình thành.
- Chế độ "cả hai CB cùng hawkish" (RBA 4.35% vs Fed 3.75–4.00%): differential hẹp + hai
  chiều → static carry AUDUSD yếu, **2y ACGB–UST spread momentum** là proxy đúng hơn level.

### 2.2 Dữ liệu

| Data | Nhịp/giờ (UTC) | Vai trò |
|---|---|---|
| Monthly CPI indicator | ~4 tuần sau month-end, 00:30 | Số RBA nhìn hàng tháng; vol cao nhất data Úc |
| Quarterly CPI + trim mean | quý, 00:30 | Trim mean là anchor policy thực tế |
| Labour force | ~thứ 5 tuần 3, 00:30 | Unemployment rate > jobs number trong framework RBA |
| PMI flash/final | tháng | Cycle pulse |
| Trade balance / export price | tháng | ToT xác nhận chậm |
| Retail sales, GDP | tháng/quý | Xác nhận, ít tự đi giá |

### 2.3 China coupling

- Úc xuất iron ore (~20–25% giá trị xuất khẩu, ~70–80% đi TQ), than luyện cốc, LNG, copper
  concentrate, vàng; TQ chiếm ~30–40% xuất khẩu Úc. Iron ore là **single best daily-frequency
  proxy** cho driver China-growth.
- Chuỗi: China credit/property → steel output → iron ore price → ToT Úc → national income
  → RBA hawkish bias + equity inflow → AUDUSD. Mạch chậm (tuần–tháng).
- Trạng thái 2026: iron ore **~$90/t** (dự báo từ ~$100; ING/Steel-on-the-Net); property
  đầu tư TQ **−16.2% y/y** (Jan–May 2026); cầu thép 2025 −6.9%; GDP TQ Q1 +5.0%. Nghĩa là
  **China channel đang âm/falt** trong khi RBA hawkish — AUD bị kéo hai phía; aud pullback
  ~4% giữa năm 2026 khi Fed quay lại hike.
- Watchlist TQ: NBS & Caixin PMI (cuối tháng, 01:00–01:45 UTC), TSF/credit impulse
  (10–15 hàng tháng), LPR (mùng 20), iron ore port inventory (Mysteel weekly), Politburo
  (Apr/Jul/Dec).

### 2.4 Rủi ro

- **China property deflation kéo dài**: credit impulse mất sức truyền sang demand thật —
  driver AUD mờ dần (2025–26 là bằng chứng).
- **Commodity shocks nguồn cung**: bão WA (mùa cyclone Oct–Apr), sự cố mỏ Brazil, sáp
  policy TQ — thổi ToT không qua kênh cầu, làm lead-lag đổi dấu.
- **Domestic inflation resurgence**: chính là kịch bản đang chạy (CPI 3.5%) — nếu RBA phải
  hike lên 4.85%+ thì AUD hưởng nhưng housing HH (mortgage belt) gánh → boom-bust risk.
- Carry-unwind toàn cầu (yen-carry type episode 8-9/2026 precedent): AUD bị bán như
  risk-proxy đầu tiên bất kể fundamentals Úc.

---

## 3. NZD — New Zealand

### 3.1 RBNZ — stance, cadence

- **Cadence**: MPC họp 7 lần/năm (kế tiếp ~cuối 10/2026 — *(cần kiểm chứng ngày)*), quyết
  định + statement; MPS quý (Feb/May/Aug/Nov) kèm OCR track.
- **Stance (verified 02/09/2026)**: **hike 25bp → OCR 2.75%** (từ 2.50%) — thuộc hiking
  cycle từ đáy 2.00% (2025). Nhưng Governor **Anna Breman** phát biểu ngay sau đó "có thể
  dành thời gian đánh giá trước khi tăng tiếp" → thị trường đọc là **pause-ready**; OCR
  track dự báo 2.81% 12/2026, 3.12% 09/2027 — đường đi rất phẳng (so với track hawkish
  của RBA 4.35→4.60%).
- Hệ quả cấu trúc: NZD là **funding leg của bloc** — differential vs Fed −100~−125bp
  (OCR 2.75% vs Fed 3.875% mid) khiến NZD bị bán carry trong khi RBA ở trên Fed →
  AUDNZD nhận lực policy-spread hai chiều.

### 3.2 Dữ liệu

| Data | Nhịp/giờ (NZ) | Vai trò |
|---|---|---|
| CPI (quarterly) | quý, ~ giữa quý sau | Quan trọng nhất — NZ vẫn CPI quý (không có monthly indicator chuẩn như AU cho đến gần đây) |
| Employment / HLFS | quý | Dual mandate RBNZ (CPI + max sustainable employment) |
| GDP | quý | NZ đã từng vào recession 2024–25 — kiểm tra tăng trưởng |
| Trade balance / export values | tháng | Dairy-led ToT |
| **GDT dairy auction (WMP)** | **2 tuần/lần, thứ Ba, kết quả ~14:00–15:00 UTC thứ Hai** | Driver NZD riêng — xem 3.3 |
| Electronic card transactions / ANZ business confidence | tháng | Nowcast nội địa |

### 3.3 Dairy-ToT → NZD; AUDNZD; trạng thái Sep-2026

- **GDT (GlobalDairyTrade) auction cycle**: 2 tuần/lần; **Whole Milk Powder (WMP)** là
  contract có beta NZD-tương-đối cao nhất (NZ là nhà xuất sữa bột lớn nhất thế giới;
  dairy ~20–30% export hàng hóa — *(cần kiểm chứng tỷ trọng hiện hành)*). Chuỗi: GDT WMP
  index ↑ → ToT NZ ↑ → national income → RBNZ hawkish bias + NZD spot ↑. Auction surprise
  thường move NZD 30–60 pips trong giờ, có continuation nếu 2 phiên cùng hướng.
- **AUDNZD cross**: "pure China-vs-domestic-dairy spread" — RBA hawk vs RBNZ pause
  (Sep-2026) là cấu hình tách policy rõ nhất từ 2024 → AUDNZD uptrend; stat-arb
  mean-reversion AUDNZD **đang break** (cointegration yếu hóa) — phải dùng half-life filter.
- **Sep-2026 funding-leg regime**: differential −100~−125bp + OCR track phẳng → NZDUSD
  trượt 0.59 → **~0.572**; NZD dưới.perform AUD và bị dùng làm funding cho carry bloc.
  Lưu ý đuôi: nếu OCR track revise lên (inflation surprise) thì funding-short squeeze.

### 3.4 Rủi ro

- **Recession / stagflation nội địa**: NZ đã trải recession 2024–25; hiking sớm quá có
  nguy cơ bóp growth — RBNZ phải chọn giữa CPI và employment (dual mandate bite).
- **Agri/weather shocks**: hạn hán El Niño/La Niña, mud fever FMD-type biosecurity —
  giảm nguồn cung sữa → WMP price lên nhưng volume xuống → ToT net ambiguous.
- **Housing NZ**: rate-sensitive, leverage hộ gia đình cao — tương tự Canada nhưng quy mô
  nhỏ hơn, ít ảnh hưởng global.
- **Thanh khoản**: NZDUSD mỏng nhất trong 4 đồng bloc → spike event overshoot & revert;
  false break phiên Á thường gặp hơn AUDUSD.

---

## 4. CHF — Thụy Sĩ

### 4.1 SNB — stance & intervention history

- **Stance (verified 24/09/2026)**: policy rate **0%** (không đổi từ cut 06/2025); SNB là
  CB duy nhất lớn còn ở zero — **divergence cực đoan vs Fed 3.75–4.00%** (differential
  **+375bp** thuận carry long USDCHF).
- Tuyên bố 24/09/2026: "willing to be active in the foreign exchange market" — tức sẵn
  sàng **mua ngoại tệ/bán CHF** để chống áp lực tăng giá CHF (safe-haven inflow). Kể từ
  06/2025 SNB đã từng quay lại mua ngoại tệ; stance 2026 = **floor-ish bằng lời nói + real
  intervention risk**.
- **Bài học 2015 (SNB floor EURCHF 1.20)**: khi ngưỡng bị bỏ (15/01/2015) CHF gap
  ~−20% trong phút — tail risk của mọi short-CHF/long-USDCHF carry: SNB có thể (i) đổi
  stance bất ngờ, (ii) mất khả năng/thị chí bảo vệ ngưỡng, (iii) hike đột ngột nếu
  inflation nội địa trở lại. Tail này không hedge được bằng stop thông thường trong gap.
- **Sight deposits proxy**: tổng số dư sight deposits của SNB tăng đều = dấu vết mua ngoại
  tệ. **Heuristic WoW ≥ +5 tỷ CHF = SNB đang can thiệp thật** (case +11.2 tỷ CHF một tuần
  07/2025). Giá trị WoW hiện tại **(cần kiểm chứng data.snb.ch tuần này)**. Đây là
  chỉ báo can thiệp công khai duy nhất gần-realtime của một CB lớn.
- Cadence: MPA quý (Mar/Jun/Sep/Dec); kế tiếp **10/12/2026**; dữ liệu inflation monthly.

### 4.2 Dữ liệu Thụy Sĩ

| Data | Nhịp | Vai trò |
|---|---|---|
| CPI | tháng (~đầu tháng) | SNB mandate 0–2%; Swiss CPI thường thấp (~0–1%) — điểm nya quyết định stance zero |
| KOF leading indicator | tháng | Cycle Swiss/EU proxy |
| PMI manufacturing/services | tháng | EU-demand pulse (Swiss = EU satellite) |
| Retail sales / GDP | tháng/quý | Xác nhận |
| Sight deposits | **tuần (thứ Hai)** | Intervention proxy — mục 4.1 |
| EURCHF spot vs "pain level" | realtime | Kênh can thiệp SNB |

### 4.3 Safe-haven mechanics

- CHF là một trong hai haven G10 (cùng JPY). Flow: geopolitical risk-off / Eurozone
  stress / banking stress → inflow vào CHF → USDCHF xuống **kể cả khi differential
  +375bp** — carry và haven luôn đánh nhau trên pair này; winner theo regime.
- **Gold linkage**: gold ~$4,144 (−26% từ ATH nhưng vẫn absolute-high) — haven basket
  {CHF, gold} có correlation regime-dependent: war-on (9/2026) cả hai nhận bid; peace-talk
  (22–24/09) cả hai rút. AUDUSD–gold correlation hai chế độ (risk-off âm vs
  commodity-producer dương) dùng làm gate cho lane XAUUSD.
- **EURCHF flows**: phần lớn CHF-trading thực chất là EURCHF (cross lớn nhất) — áp lực
  EURCHF giảm (CHF mạnh lên) là trigger can thiệp SNB lịch sử; theo dõi mức "pain" của
  SNB (khu vực parity/0.84 — *(cần kiểm chứng vùng kỹ thuật hiện hành)*).
- **CHFJPY**: haven-vs-haven cross — khi risk-off toàn cầu, CHFJPY thường đi ngang/âm nhẹ
  trong khi AUDJPY rơi mạnh; dùng làm "pure haven spread" để tách risk beta khỏi haven
  beta. Sep-2026: BoJ đang hiking (JPY leg mạnh) + CHF zero → CHFJPY chịu áp lực hai đầu.
- **Truyền dẫn vào USDCHF (Sep-2026)**: carry +375bp thuận long USDCHF, NHƯNG (i) tail
  SNB intervention (mua ngoại tệ = mua USD bán CHF → thực ra **cùng chiều** với long
  USDCHF — đây là điểm thú vị: can thiệp SNB Sep-2026 hậu thuẫn carry), (ii) risk-off
  war-shock có thể đảo chiều ngắn hạn. Tail chính là **SNB hike surprise** (inflation
  Thụy Sĩ phổ biến trở lại) — khi đó +375bp co lại nhanh.

---

## 5. Cross-cutting — commodity-FX bloc

### 5.1 Commodity-FX index

- Định nghĩa làm việc: **CFX = equal-weight (CAD + AUD + NZD) vs USD** — tính bằng
  1/3·(1/USDCAD + AUDUSD + NZDUSD) hoặc geometric mean; re-normalize z-score 60d.
- Mục đích: (i) tách "USD-common leg" (DXY) khỏi "bloc-specific move"; (ii) so với
  broad commodity index (Bloomberg Commodity / CRB) để đo **health của ToT channel**;
  (iii) regime label cho portfolio allocation giữa 4 lane.
- Thành phần đặc thù: CAD = oil/heavy-crude (energy ~50% export value); AUD = iron ore/
  coal/LNG/copper/gold (metals-energy mix, China-demand); NZD = dairy (soft commodity);
  CHF **không thuộc CFX** — là haven leg đối trọng (dùng làm nhóm chứng trong S95-type
  regime flip).

### 5.2 Correlation regimes (prior cấu trúc — cần đo lại)

| Regime | CFX vs DXY | CFX vs Brent/WTI | CFX vs gold | Ghi chú |
|---|---|---|---|---|
| Demand-boom toàn cầu (reflation) | âm mạnh (−0.6~−0.8) | dương (+0.4~+0.6) | ~0/âm | ToT channel khoẻ nhất; trend CFX rõ |
| Supply-shock dầu (war 2026) | âm yếu (~0/−0.3) | **phân kỳ: CAD hưởng, AUD/NZD mất** | dương nhẹ (haven lift commodity) | CFX nội bộ tách rời —AUDCAD/CAD-cross là vehicle |
| Risk-off + USD-bid (crisis) | âm sâu | âm (collapse demand) | dương mạnh | ToT chết; CHF/JPY thắng toàn bloc |
| Risk-off + USD-yếu (stagflation) | ~0 | lẫn | dương | Gold-producer AUD trụ hơn NZD/CAD |
| Range/low-vol | âm vừa | dương nhẹ | ~0 | Session/structure edge sống |

- Nội bloc: AUD–NZD corr +0.75~+0.90 (cao nhất hệ thống — nén khi RBA/RBNZ tách như 2026);
  AUD–CAD corr +0.35~+0.60 qua commodity chung + risk beta; **AUDCAD là cặp
  "metals-China vs oil-NorthAmerica"** — Sep-2026 đang ở cực (oil mạnh + iron ore yếu).

### 5.3 Terms-of-trade channel — khi nào dẫn, khi nào bị lấn át

- ToT dẫn khi: (i) driver là **demand-side** (China credit, global reflaton) — đồng thời
  đẩy commodity + growth beta cả bloc; (ii) rate differential giữa Fed và bloc **hẹp hoặc
  thuận bloc**; (iii) vol thấp (VIX<20) — risk-neutral định giá.
- ToT bị lấn át khi: (i) **rate differential lớn** (Sep-2026: Fed trên BoC +150/175bp làm
  CAD yếu dù oil $100+); (ii) **trade-war/structural shock** đè lên export nation
  (Section 338 với Canada); (iii) risk shock (haven USD/CHF/JPY mua bất kể ToT); (iv)
  driver là supply-side riêng phần (WCS blowout làm CAD yếu không thấy ở WTI; bão WA làm
  iron ore mạnh không phản ánh cầu).
- Test đo được cho phase sau: rolling 60d beta của CFX vs commodity index, so với
  |rate-differential| và VIX — kỳ vọng prior: beta ToT ~0 khi |diff|>150bp hoặc VIX>28.

### 5.4 Risk-sentiment beta từng đồng (thứ tự prior)

| Đồng | Risk beta | Cơ chế |
|---|---|---|
| AUD | **cao nhất bloc** (≈1) | China/commodity + carry target; AUDJPY là thước risk chuẩn |
| CAD | trung bình (≈0.4–0.6) | Cyclical G10 nhưng oil-haven-war che mất一部分 (war-on oil mạnh = CAD được nâng đỡ trong risk-off) |
| NZD | trung bình-cao nhưng funding-skew | Beta risk gần AUD nhưng carry-flow (short NZD) làm NZD yếu cả trong risk-neutral — Sep-2026 illustrative |
| CHF | **âm** (≈−0.5~−0.8) | Haven inflow khi VIX lên; CHFJPY = pure haven-vs-haven |

- Ứng dụng: risk-on melt-up → ưu tiên long AUD > NZD > CAD, tránh CHF; risk-off →
  short AUD trước (highest beta), CAD trụ hơn nếu oil-supply-shock đồng thời (Sep-2026).

---

## 6. Coupling rules (overlay hypotheses)

Quy ước: **IF <điều kiện> THEN <bias/gate>** cho symbol/cụm. Mỗi rule: điều kiện —
symbols — logic kinh tế — lối thoát khi mất điều kiện. Mọi ngưỡng là prior khởi điểm
(NOT_RUN cho đến khi đo). Viết tắt: DIFF_CB = Fed policy rate − CB bloc; TSF = China
aggregate financing; WoW = week-over-week.

**Rules CAD (1–7)**

1. **IF DIFF_Fed−BoC > +100bp VÀ slope 3M của 2y OIS spread > 0 THEN bias long USDCAD**
   (carry + drift), bắt buộc kèm oil-hedge theo beta (tham chiếu S31 lane USDCAD) —
   Symbols: USDCAD. Logic: differential nới là driver mạnh nhất 2026. Exit: slope flip
   dấu 2 phiên liên tiếp hoặc BoC hike surprise.
2. **IF WTI > $95 do supply-shock (war/Hormuz) VÀ trade-war intensity đang leo
   (headline/d蜜line mới) THEN giữ long USDCAD bias — CAD KHÔNG được hưởng oil.**
   Symbols: USDCAD. Logic: Sep-2026 — carry + thuế quan lấn át petro. Exit: de-escalation
   trade-war thật (dỡ thuế/gia hạn USMCA) hoặc Fed pause signal.
3. **IF Brent 6M backwardation sâu (CL1−CL6 percentile-80 3 năm) VÀ WCS−WTI hẹp
   (<$15) THEN bật petro-channel: bias short USDCAD.** Symbols: USDCAD, CADJPY.
   Logic: tightness cung thật + pipeline thông = CAD ToT tailwind thật. Exit:
   backwardation flatten về median hoặc WCS blowout.
4. **IF BoC hike (kịch bản oil pass-through) TRONG KHI Fed dots không tăng THEN short
   USDCAD convergence trade, size nhỏ.** Symbols: USDCAD. Logic: differential nới về
   +100→+75bp + CAD under-positioned. Exit: Fed hike tiếp (27–28/10 hoặc 12/2026) hoặc
   BoC quay lại dovish-tone.
5. **IF deadline trade-war cứng trong ≤10 ngày (29/09/2026 bans; 01/01/2027 auto 50%)
   THEN nới stop/long vol quanh USDCAD event window — không thêm vị thế direction mới.**
   Symbols: USDCAD, CAD crosses. Logic: binary headline → gap risk. Exit: sau khi qua
   deadline không có escalation material.
6. **IF StatCan portfolio flow (repatriation) ≥ C$25B/tháng 2 tháng liên tiếp THEN
   giảm một nửa bias long USDCAD.** Symbols: USDCAD. Logic: CAD-bid flow cấu trúc
   (bán US assets → convert CAD) chống carry — phe cân bằng đã xuất hiện 07–08/2026
   (C$31B kỷ lục). Exit: flow về <C$10B/tháng.
7. **IF thứ Sáu đầu tiên (LFS Canada trùng NFP Mỹ) THEN chỉ trade USDCAD theo
   net-surprise (z_US − 0.6·z_CA), không trade USD-leg thuần.** Symbols: USDCAD.
   Logic: double-US-foot triệt tiêu beta. Exit: không áp dụng (rule theo lịch).

**Rules AUD (8–14)**

8. **IF RBA hike → ≥4.60% (29/09 hoặc sau) VÀ SEP/dots Fed không tăng THEN bias long
   AUDUSD (differential mở theo Úc, +60→+85bp).** Symbols: AUDUSD, AUDNZD. Logic: hiếm
   có RBA trên Fed — allocation flow về AUD. Exit: Fed hike tiếp hoặc RBA signal pause
   (Breman-type language).
9. **IF iron ore 62% Fe 20d-momentum > 0 VÀ China credit impulse (TSF delta 3M) không âm
   THEN bật trend-family long AUDUSD; ngược lại thì gate off trend.** Symbols: AUDUSD.
   Logic: hai điều kiện = China demand thật, không chỉ price noise. Exit: credit impulse
   flip âm hoặc iron ore mất 20d-momentum.
10. **IF China stimulus headline lớn THEN chỉ theo AUD long nếu xác nhận "quy mô thật"
    (fiscal property-backed ≥ ngưỡng) trong 48h; nếu chỉ "talking stimulus" THEN revert
    toàn bộ spike.** Symbols: AUDUSD, NZDUSD. Logic: stimulus-talk tape 2024–26 nhiều
    false positive. Exit: theo định nghĩa nhánh (có/không follow-up material).
11. **IF VIX > 25 HOẶC AUDJPY < EMA50-D1 THEN gate-off mọi long AUD/NZD bất kể driver
    nội địa.** Symbols: AUDUSD, NZDUSD, AUDCAD. Logic: risk beta AUD cao nhất bloc —
    driver riêng bị risk leg đè. Exit: VIX < 20 hai ngày liên tiếp.
12. **IF China property đầu tư y/y < −10% (deflation regime đang chạy) THEN cap size
    long AUD ở 50% bình thường — ToT channel yếu hóa có hệ thống.** Symbols: AUDUSD.
    Logic: property −16.2% (Jan–May 2026) cắt chuỗi credit→steel→iron ore. Exit: property
    sequence cải thiện 2 quý liên tiếp.
13. **IF RBA−Fed differential ∈ (0, +100bp) (hẹp, hai chiều) THEN tắt static carry AUD,
    thay bằng 2y ACGB−UST spread momentum làm bias driver.** Symbols: AUDUSD. Logic:
    chế độ "hai CB cùng hawkish" 2026 làm level-carry chết (S8/S35 lane AUDUSD). Exit:
    |differential| > 100bp một bên.
14. **IF mùa cyclone WA (Oct–Apr) có supply event iron ore THEN không dùng iron-ore
    lead-lag theo hướng cầu (đổi dấu).** Symbols: AUDUSD. Logic: supply shock thổi giá
    không phản ánh demand — lead-laginvert. Exit: event logistics hết (cảng mở lại).

**Rules NZD (15–19)**

15. **IF RBNZ pause (Breman tone giữ) VÀ Fed còn hike (dots ≥4.1%) THEN NZD giữ vai
    funding leg: bias short NZDUSD / long AUDNZD trong bloc basket.** Symbols: NZDUSD,
    AUDNZD. Logic: differential −100~−125bp + OCR track phẳng (2.81% Dec-26) vs RBA
    hawkish. Exit: RBNZ OCR track revise lên ≥3.2% end-2027 hoặc Fed pause.
16. **IF GDT WMP index 2 phiên liên tiếp ≥ +1.5% THEN hủy bias short NZD (dairy-ToT
    override funding leg), cân nhắc long NZD vs AUD.** Symbols: NZDUSD, AUDNZD. Logic:
    WMP là driver NZD-specific mạnh nhất; 2 phiên = trend chứ không noise. Exit: WMP
    auction flip âm hoặc về flat.
17. **IF AUDNZD break 20d-high VÀ RBA hawk/RBNZ pause (policy-spread mở) THEN cho phép
    trend AUDNZD (không mean-revert); stat-arb AUDNZD chỉ chạy với half-life filter
    <20 ngày.** Symbols: AUDNZD. Logic: cointegration break 2024–26. Exit: RBNZ/RBA
    policy path hội tụ (tone shift).
18. **IF NZDUSD < 0.5750 (đáy Sep-2026) VÀ COT spec net-short NZD > 1.5 sd THEN cẩn
    thận funding-short squeeze — chốt lời short, không thêm.** Symbols: NZDUSD. Logic:
    positioning crowded + magnet đáy vùng. Exit: breakout đáy với volume (tiếp tục
    trend) hoặc positioning normalize.
19. **IF GDT auction day (thứ Ba tuần 1&3, kết quả ~14:00 UTC thứ Hai) THEN tắt NZD
    mean-reversion 12h quanh kết quả, bật bracket.** Symbols: NZDUSD, AUDNZD. Logic:
    scheduled vol window riêng NZD. Exit: sau khi kết quả in 4h.

**Rules CHF (20–23)**

20. **IF SNB sight deposits WoW ≥ +5 tỷ CHF THEN xác nhận SNB đang bán CHF: band long
    USDCHF (và EURCHF) được phép mở rộng target — can thiệp cùng chiều carry.**
    Symbols: USDCHF, EURCHF. Logic: heuristic 07/2025 (+11.2 tỷ); Sep-2026 stance
    "willing to be active". Exit: WoW < +2 tỷ hoặc âm 2 tuần liên tiếp (hết can thiệp).
21. **IF risk-off (VIX > 28 VÀ gold 20d-high) THEN tắt long USDCHF dù carry +375bp —
    haven flow lấn át carry.** Symbols: USDCHF, CHFJPY. Logic: war-shock/risk-event làm
    CHF nhận inflow nhanh hơn coupon tích lũy. Exit: VIX < 22.
22. **IF Fed−SNB differential > +300bp VÀ VIX < 18 THEN carry long USDCHF nhỏ size +
    tail-hedge (OTM put hoặc stop-time quanh SNB MPA).** Symbols: USDCHF. Logic: carry
    +375bp là một trong những differential lớn G10 nhưng tail SNB-hike/2015-floor-type
    luôn treo. Exit: SNB hike surprise, Swiss CPI > 1.5%, hoặc VIX regime đổi.
23. **IF SNB MPA (quý, kế 10/12/2026) ≤ 5 ngày THEN flat/de-risk toàn vị thế CHF-carry,
    không đứng qua event.** Symbols: USDCHF, CHFJPY, EURCHF. Logic: event 2015/2022
    cho thấy SNB đổi stance kiểu gap. Exit: sau statement + presser 24h.

**Rules cross-bloc (24–30)**

24. **IF oil 20d-momentum > 0 VÀ iron ore 20d-momentum < 0 (commodity split) THEN
    vehicle = AUDCAD long (hoặc USDCAD short + AUDUSD flat) — oil-FX vs metals-FX
    spread.** Symbols: AUDCAD. Logic: Sep-2026 exact — CAD hưởng ToT petro, AUD gánh
    China weakness. Exit: hai commodity cùng dấu (hội tụ).
25. **IF CFX index (CAD+AUD+NZD vs USD) break 20d-low TRONG KHI broad commodity index
    20d-momentum > 0 THEN tuyên bố regime "ToT bị lấn át": chuyển sang rate-driven/
    USD-leg family, tắt ToT-family cho cả bloc.** Symbols: cả 4 lane. Logic: Sep-2026
    là case (oil mạnh + CFX yếu). Exit: rolling 60d beta CFX~commodity phục hồi > 0.3.
26. **IF risk-on melt-up (SPX 20d-high VÀ VIX < 15) THEN ưu tiên long theo thứ tự
    AUD > NZD > CAD, tránh CHF; risk-off thì short AUD trước.** Symbols: cả 4. Logic:
    risk beta thứ tự mục 5.4. Exit: theo VIX/SPX điều kiện mất.
27. **IF war/peace classifier (Hormuz headline) đổi trạng thái THEN re-price toàn bộ
    oil-beta trong ≤24h: war-on → CAD petro mạnh nhưng USD-haven cũng mạnh (USDCAD
    chop, CADJPY sạch hơn); peace-talk → oil rơi, CAD mất petro nhưng risk-on nâng
    AUD/NZD.** Symbols: USDCAD, CADJPY, BRENT/WTI lanes. Logic: whipsaw $90→108→90→104
    tháng 9/2026 là dataset calibration. Exit: classifier ổn định 1 tuần.
28. **IF cả Fed + RBA cùng hike trong 6 tuần (hoặc dots hai bên cùng tăng) THEN USD
    common-factor mạnh: ưu tiên cược intra-bloc (AUDNZD, AUDCAD, CADCHF) thay vì
    bloc-vs-USD.** Symbols: cross bloc. Logic: khi tất cả CB hawkish, phân phối driver
    dồn về USD-leg — cross strip được USD. Exit: một CB pause (Fed 12/2026 hoặc RBA).
29. **IF month-end/quarter-end (L−1..L+1) THEN fixing-flow bias quanh WMR 16:00 UTC
    theo hướng month-return chữ V (equity up tháng → USD-bid cuối tháng → bloc-FX yếu
    nhẹ).** Symbols: cả 4. Logic: rebalancing flow có hệ thống. Exit: sau L+1.
30. **IF China Politburo window (Apr/Jul/Dec ±3 ngày) THEN bật bracket/vol-window cho
    AUD + NZD (stimulus binary); không giữ directional position mũiframe qua kết luận.**
    Symbols: AUDUSD, NZDUSD. Logic: historically catalyst lớn nhất Q4 cho China-proxy.
    Exit: 2 ngày sau công bố.

---

## 7. Lịch vĩ mô tuần skeleton (4 đồng + GDT)

Khung giờ chuẩn **UTC** (data Úc/NZ ghi kèm local vì DST hai bán cầu lệch nhau
Oct–Apr). Skeleton điền theo tuần chuẩn; mọi mốc cụ thể phải check calendar live.

### 7.1 Chu kỳ tuần điển hình

| Ngày | CAD/US (ET) | AUD (AEST→UTC) | NZD (NZST→UTC) | CHF/EU |
|---|---|---|---|---|
| **Mon** | — (risk set-up) | — | GDT results ~14:00 UTC (auction thứ Ba tuần 1&3, *ngày (cần kiểm chứng)*) | SNB sight deposits update tuần |
| **Tue** | — | — | — | — |
| **Wed** | EIA crude 10:30 ET | monthly CPI ~00:30 UTC (tuần có lịch) | — | — |
| **Thu** | — | labour force ~00:30 UTC (tuần 3) | — | SNB/ECB event window nếu có |
| **Fri** | **LFS + NFP 8:30 ET (thứ 6 đầu tiên)**; COT 15:30 ET | — | — | — |

- US data chung (đè mọi pair): CPI ~13 hàng tháng 12:30 UTC; NFP thứ Sáu đầu 12:30 UTC;
  ISM đầu tháng; FOMC 18:00 UTC (27–28/10 kế tiếp).
- China (đè AUD/NZD): PMI cuối tháng/mùng 1 (01:00–01:45 UTC); TSF 10–15; LPR mùng 20;
  trade/iron-ore imports ~mùng 7; Politburo Apr/Jul/Dec.

### 7.2 CB meetings đã biết còn lại 2026

| CB | Ngày | Ghi chú |
|---|---|---|
| **RBA** | **29/09** (mai, 04:30 UTC) | OIS/panel nghiêng hike → 4.60%; kết quả (cần kiểm chứng); kế tiếp ~Nov & Dec *(ngày (cần kiểm chứng))* |
| **BoC** | **28/10** kèm MPR | Hawkish-risk do oil pass-through; OIS priced hold |
| **RBNZ MPC** | ~cuối 10/2026 *(cần kiểm chứng ngày)* | Pause-ready (Breman); MPS tiếp theo Nov kèm OCR track |
| **SNB MPA** | 10/12/2026 | 16/24 economist kỳ hold 0% qua 2027; cập nhật intervention language |
| **FOMC** | 27–28/10; ~12/2026 | Dots 4.1% cuối 2026 — thêm 1 hike implied; là USD-leg cho cả 4 lane |
| **BoJ** (tham chiếu CHFJPY/CADJPY) | theo lịch | JPY-haven leg — đồng bộ với lane USDJPY |

### 7.3 GDT auction cycle (driver NZD)

- Nhịp: **2 phiên/tháng, kết quả công bố thứ Ba sáng NZ (~14:00–15:00 UTC thứ Hai)** —
  thực tế là "thứ Hai chiều EU/thứ Ba sáng Á" tùy DST; phiên kế 2026: ~06/10, ~20/10,
  ~03/11... *(ngày (cần kiểm chứng tại globaldairytrade.info)*.
- Watch: **WMP index % change** (driver chính), SMP/butter phụ; average win rate;
  participation. Rule 16/19 (mục 6) gắn trực tiếp vào chu kỳ này.
- Nhớ: GDT kết quả thường trùng khung Sydney open — book NZD mỏng → overshoot-revert
  quen thuộc; NHƯNG 2 phiên cùng hướng thì continuation thật.

### 7.4 Weekly checklist tóm tắt (macro lane)

- [ ] Mon: SNB sight deposits WoW (rule 20); GDT results nếu tuần auction (16/19); kiểm
      calendar CB tuần.
- [ ] Tue: trade-war tracker — deadline/proclamation mới (5); war/peace classifier (27).
- [ ] Wed: EIA + oil curve backwardation (3); AU CPI nếu có (8/13).
- [ ] Thu: AU labour force nếu tuần 3; CHF CPI tuần đầu tháng (22).
- [ ] Fri: net-surprise LFS+NFP (7); COT positioning (18); month-end flow (29).
- [ ]Cuối tuần: CFX index vs commodity index (25); RBA/Fed dots update (8/13/28);
      GDT calendar & RBNZ/BoC/SNB countdown.

---

## Phụ lục — nguồn & trạng thái bằng chứng

- Verify WebSearch 2026-09-28: RBA (rba.gov.au scheduling; CBA/Finder hike kỳ vọng;
  CPI 3.5%); RBNZ (UDC/Interest.co.nz/Binance — hike 02/09 → 2.75%, Breman pause hint,
  OCR track 2.81%/3.12%); SNB (ICM/DevDiscourse/Mitrade — hold 0% ngày 24/09, willing
  to intervene, 16/24 kì hold qua 2027); BoC (PFG — hold 2.25% ngày 02/09 lần 7, kế
  28/10).
- Kế thừa 12 lane symbol (verified trong lane): Fed hike 16/09 → 3.75–4.00% + dots 4.1%;
  oil war narrative $90→108→90→104; Section 338 timeline; iron ore ~$90; gold $4,144
  (−26% từ ATH); silver ~$65.5–67; USDCAD ~1.40–1.41; NZDUSD 0.59→0.572; C$31B
  divestment tháng 7/2026; sight deposits +11.2 tỷ CHF/tuần 07/2025.
- **(cần kiểm chứng)** còn mở: kết quả RBA 29/09; sight deposits WoW hiện tại; WCS−WTI
  hiện tại; ngày RBNZ MPC & RBA cuối 2026; ngày GDT cụ thể; mức SNB "pain" EURCHF; tỷ
  trọng dairy trong export NZ hiện hành; mọi spot level (bằng tick data).
- Tài liệu brainstorm — không có backtest/kết quả hiệu suất nào được tạo ra ở đây; mọi
  rule mục 6 là hypothesis với trạng thái **NOT_RUN**, chỉ được xác nhận qua trial
  accounting theo chuẩn program.
