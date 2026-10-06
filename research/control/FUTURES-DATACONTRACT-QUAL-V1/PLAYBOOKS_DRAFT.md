# PLAYBOOKS_DRAFT — FUTURES-DATACONTRACT-QUAL-V1 (Bước 2, bản r5)

- **PHÁN QUYẾT CO-OWNER ÁP DỤNG (2026-10-03): `NO_GO_REGISTER · NO_GO_SCORE ·
  NO_GO_ORDER`.** Bản r5 phản ánh D1–D7 + review r3/r4 + **quyết định r5 của
  Co-Owner: chọn A-r4 làm PHẠM VI DỰ KIẾN cho PB1-ES** — tổng tối đa 24
  identity (primary 16 + FOMC sensitivity 4 + C1/C2/C3/C4 = 4), **chưa freeze,
  KHÔNG phải GO_REGISTER/GO_SCORE/GO_ORDER**; seed placebo đơn 20261002 là
  **giới hạn đã công bố — không claim permutation robustness**. Sửa bất nhất
  số học thiết kế đầy đủ: nay ghi rõ HAI thiết kế đầy đủ (52 với placebo
  đơn-delay như dòng C1; 53 với placebo cặp delay) — cả hai > 24 ⇒
  BLOCKED_TRIAL_BUDGET. Các bản cũ nằm trong git history và bị THAY THẾ,
  không chạy song song.
- **TRẠNG THÁI: DRAFT / PHÁC THẢO — KHÔNG PHẢI EXECUTABLE SPEC.**
  Viết SAU khi A7-DC chốt Bước 1 (verdict `CLOSED_WITH_ERRATA`, 0 BLOCKER /
  0 MAJOR / 3 MINOR đã áp). Vì Bước 1 vẫn **PARTIAL** ở các chiều
  cost-authority / holiday-official / fill-data (DATACONTRACT_QUALIFICATION §3),
  toàn bộ playbook dưới đây ở trạng thái **BLOCKED**: mọi tham số entry/TP/SL/
  chi phí mang cờ **[PROVISIONAL]** — chỉ được freeze khi contract mapping,
  event timestamps, calendar/roll và fill data được xác minh trọn (luật owner
  2026-10-03). Không có số PnL nào được tính, không selection theo PnL.
- Trạng thái từng playbook sau phán quyết: **PB1 ES-first (đường hoàn thiện
  spec)** · **PB2 HOLD (ancestry)** · **PB3 PARK (n mỏng + lỗi mở 6A)**.
- Mọi cơ sở thực nghiệm dẫn về dossier v2 (đã errata) + DC-VERIFY +
  NQ2020_ADDENDUM. Taxonomy: OBSERVED (đo rồi) / POSTULATED (cơ chế, chưa đo)
  / NOT_RUN / BLOCKED.

---

## 0. Ma trận evidence theo hypothesis (per-hypothesis, mã × giả thuyết)

| hypothesis | mã | cơ chế | trạng thái bằng chứng | verdict |
|---|---|---|---|---|
| H-A OVN→RTH continuation | ES-first; NQ sau cost gate | thông tin Globex (OVN mang 21-54% variance ES; share 10→24% NQ) chưa priced đủ tại open RTH | cấu trúc OVN/session OBSERVED (NQ §2, ES §3); phiên điều kiện **NOT_RUN** (luật prep) | POSTULATED — dữ liệu đủ 16y, chờ cycle đăng ký |
| H-B OVN→RTH reversion (đuôi ngược) | ES-first; NQ sau cost gate | VR(20)=0.71/VR(60)=0.67 NQ; ES acf1 âm 6/7 era ⇒ đuôi OVN là thành phần mean-revert | cấu trúc VR/ACF OBSERVED (NQ §1, ES §2); phiên điều kiện NOT_RUN | POSTULATED — đối thủ trực tiếp của H-A, đăng ký CÙNG lúc |
| H-C London-morning range → US continuation | 6E, 6B — PB2 **HOLD** | flow London sáng (6E 21.6% volume London-local, RV-share cao nhất 17.6%; 6B modal 15:00 London) khám phá thông tin khi US vắng; US session hấp thụ tiếp | cấu trúc session/DST OBSERVED (6E §4, 6B §2); range-break conditional NOT_RUN | POSTULATED |
| H-D London-morning fade (reversion) | 6E, 6B — PB2 **HOLD** | range extension London bị US liquidity fade lại (đối thủ H-C) | như H-C | POSTULATED |
| H-E RBA decision-window reaction | 6A — PB3 **PARK** | quyết định RBA 14:30 Sydney cô lập thông tin vào session mỏng (9.0× volume, 4.8× |ret| ±5'; change-days range 59 vs 29 ticks) | anatomy OBSERVED (6A §4.1); reaction-direction trade NOT_RUN; **n mỏng: 67 meetings** | POSTULATED — rủi ro kill-by-thinness cao, ghi sẵn kill |
| H-F 6A regime beta vs ES | 6A+ES | beta 6A-vs-ES 0.351 risk-on vs 0.247 risk-off (tag frozen a priori) | beta/regime map OBSERVED descriptive (6A §6-H4); ancestry-veto vs dead families CHƯA phân tích | POSTULATED — cần phân tích representation-rho trước khi vào cycle; không phải daytrading, để vòng sau |
| H-G carry/CIP roll-gap "edge" | mọi mã | roll-gap = CIP carry | ĐÃ ĐO là structural (6B corr 0.84; 6A 16/16 |Δ|≥25bp; 6E vintage-fragile; 6J near<far 100%) | **KHÔNG PHẢI HYPOTHESIS ALPHA** — structural input; cấm đăng ký làm tín hiệu (luật owner) |
| H-H 6J BoJ/MPM, intervention | 6J | MPM |ret| 1.9×; MOF ops 4/14 down-legs | anatomy OBSERVED; PIT: MOF lag ~1 tháng (không same-day); book BoJ window mỏng hơn 35%; volume-definition gap | PHỤ — chỉ vào cycle sau khi 6J có BBO/spread thực + khối lượng đủ; quote-orientation law |
| 6F (owner nhắc) | 6F | — | không data | **NOT_RUN_DATA_ABSENT** — acquisition gate riêng, cấm thay bằng 6J |
| CL/NG/GC/SI | 4 mã | — | chỉ v1 dossier (14 tháng IBKR) | NOT_QUALIFIED_V2 — không vào đợt playbook này |

Construction-rule ↔ alpha: roll rule từng mã (DATACONTRACT §1.3), session
clock, DST bucketing, exclusions là **điều kiện chạy**, không phải nội dung
hypothesis; kill của playbook không được quy cho construction rule nếu rule
đóng băng đúng đặc tả.

---

## 1. PB1 — OVN→RTH conditional daytrade (ES-first; NQ sibling sau cost gate) [PROVISIONAL]

**Câu hỏi kiểm thử**: biến động overnight (17:00 CT → open 08:30 CT) lớn (đuôi
strict-past) có tiếp diễn hay đảo chiều có hệ thống trong RTH (08:30 →
**close RTH era-correct của product/date**) sau chi phí không? Hai arm đối thủ
**đăng ký CÙNG lúc, không chọn tail/chiều hậu nghiệm (D-luật Co-Owner)**:
**PB1-CONT** (theo hướng OVN) và **PB1-REV** (ngược hướng OVN). Cả hai tail
(lên/xuống) đều vào — theo luật "test both tails" (NQ dossier H4). **ES ưu
tiên hoàn thiện spec** (all-in doc + spread 1 tick mỏng nhất + 16.4y); NQ chỉ
vào sau cost gate D2.

| trường | đặc tả [PROVISIONAL] |
|---|---|
| Universe | **ES-first**; NQ sibling sau cost gate (D2) — chuỗi held-contract theo §1.3 contract (ES T-5; NQ k=5 + cease-guard) |
| Tín hiệu | m = log(open_0830 / **C_prev**); **C_prev = close THỰC TẾ của session liền trước, đúng mốc era của product/date** — KHÔNG dùng "close_1600_prev" cứng [sửa theo review Co-Owner r3]: 16:30 CT (→2012) → 16:15 CT (2013→2015-11) → 16:00 CT (từ 2015-11/2016). **Kiểm tra Friday/short session [bắt buộc]**: (a) nếu session liền trước kết thúc sớm (Friday lịch sử/short/inferred-holiday — cờ §1.2), C_prev vẫn là print cuối thực tế của session đó NHƯNG phiên hiện tại gắn cờ `prev_short` và vào báo cáo era/Friday sensitivity; (b) nếu lịch sử của session trước không chắc chắn (chưa có authority D3) ⇒ phiên hiện tại **EXCLUDE/NOT_RUN**, không nội suy, không inferred-pass. Điều kiện \|m\| ≥ q80(\|m\|, trailing-252d, strict-past) [PROVISIONAL: q80 — chọn từ anatomy, không tune] |
| Entry | bar 1m đầu 08:30 CT theo hướng arm (PB1-CONT: sign(m); PB1-REV: −sign(m)); fill = open bar kế. **Delay {0, +30m} là HAI scored identity bắt buộc** (entry 09:00 CT cho delay) — KHÔNG phải "reporting-only"/miễn trừ trial [sửa theo review Co-Owner r3]; K4 tiêu thụ trực tiếp kết quả của cặp này |
| Đứng ngoài (stand-aside) | (i) ngày FOMC có giờ phát hành biết trước (92 timed) — base EXCLUDE, sensitivity INCLUDE; (ii) ngày không chắc chắn về lịch ⇒ **EXCLUDE/NOT_RUN** (D3 — không inferred-pass); (iii) session thiếu coverage RTH-core <60% EXCLUDE; (iv) warmup 252d |
| **Session theo era** | close RTH theo giai đoạn lịch sử ĐO ĐƯỢC: 16:30 CT (→2012) → 16:15 CT (2013→2015-11) → 16:00 CT (từ 2015-11/2016); break-tail pre-2016 tách riêng — không dùng đồng hồ 16:00 hồi cổ (D-luật Co-Owner) |
| TP | 2.0 × SL-distance [PROVISIONAL R=2] |
| SL | 1.0 × ATR(20d RTH-session range, median) [PROVISIONAL] |
| **Same-bar TP/SL** | khi MỘT bar 1m chạm cả TP và SL: xử lý deterministic thận trọng — **SL ưu tiên** (đóng giá xấu hơn), không xét thứ tự OHLC ưu ái; luật ghi cứng trong spec khi freeze (D-luật Co-Owner) |
| Time exit | close RTH **era-correct** (xem trên) **bắt buộc** — daytrade, không giữ qua đêm ⇒ không ăn roll-carry |
| Roll | theo §1.3; position flat trước roll-session close nên roll chỉ tác động reference chain |
| Sizing | risk 0.5% equity/lần [PROVISIONAL]; N = min(risk-size, margin-size 4× coverage); margin binds: ES ~$29k/ct ⇒ vốn 100k ≤ 2 ES [margin public 2 nguồn] |
| Phí/spread/slippage | **MODELED COST, KHÔNG PHẢI MEASURED COST** [sửa theo review Co-Owner r3]: (a) commission $0.85/side + exchange — ES 2.24 all-in là **biểu phí HIỆN TẠI (doc 2026-10-02)**, đến khi xác minh đúng account (D2) vẫn chỉ là input của mô hình; (b) **phí lịch sử theo năm ≠ biểu phí hiện tại** — commission tier/exchange fee của CME+IBKR đổi qua 2010-2026; backtest nhiều năm PHẢI khai báo dùng biểu nào (per-year nếu có nguồn, hoặc current-schedule-as-approximation với disclosure; hiện nguồn per-year NOT_RUN); (c) spread half-turn ES $6.25 = **close-proxy thiên cao** (không phải BBO measured); (d) slippage {1,2,3 tick}/chiều = **GIẢ ĐỊNH NGHIÊN CỨU (D1)**. Mọi statement phải ghi "modeled cost" — **CẤM dùng chữ complete-cost/measured-cost**; không nhân stress trùng lặp (bộ 3 tier là chiều sensitivity duy nhất) |
| Counter-hypothesis (control) | **Phân loại r4 — mỗi control khai rõ có tính đường PnL mới không**: (C1) clock/random-sign placebo — entry 08:30 hướng random-sign, **CÓ PnL path riêng ⇒ scored identity** (seed cố định 20261002, sign-draw deterministic theo session; known limitation: 1 seed duy nhất — permutation nhiều seed sẽ vượt trần); (C2) always-in-RTH baseline — **CÓ PnL path ⇒ scored identity**; (C3) flat — không có trade (anchor 0), vẫn log 1 identity; (C4) OVN-direction-unconditional (dose-response: vào sign(m) MỌI ngày, không threshold) — **CÓ PnL path ⇒ scored identity**, thay phần trading của quy ước ±21d; (C5) ±21d non-event convention — **KHÔNG tính PnL** (thống kê phân phối return của session không-điều kiện) ⇒ không phải scored identity, không gọi nhầm evaluation-view-có-PnL |
| Kill rule (định trước) | K1: dấu hiệu kỳ hiệu quả KHÔNG ổn định qua 3 era OVN-share (2010-16/2017-21/2022-26) ⇒ participation artifact, kill cả họ; K2: cả CONT lẫn REV đều dưới sàn Stage-A ở tier slippage 1 tick ⇒ family dead, cấm re-tparam; K3: ≥80% đóng góp nằm trong 2020-03..04 ⇒ drop-window sensitivity fail; **K4: dấu đảo giữa hai scored identity delay 0 và delay +30m (cùng arm/tail/tier) ⇒ open-microstructure artifact — phán quyết dựa TRỰC TIẾP trên kết quả đã tính của cả hai identity, không được bỏ identity nào**; K5: NQ vs ES trái dấu (khi NQ vào) ⇒ hạ cấp symbol-specific, không claim họ |

**Bảng liệt kê scored identity — PB1-ES (đầy đủ cả controls, không giấu)**
[sửa theo review Co-Owner r4; mọi kết quả khi được tính PHẢI xuất hiện ở đây
và vào observed denominator, kể cả khi publication fail]:

| nhóm | tính PnL mới? | cấu hình / seed / cost-tier / fold | số identity |
|---|---|---|---|
| Primary directional | CÓ | arm {CONT,REV} × tail {up,down} × delay {0,+30m} × tier {1,2,3 tick}; fold contract chung mọi PnL path (fold nhân số evaluation, không nhân identity) | 2×2×2×3 = **24** |
| C1 clock/random-sign placebo | **CÓ** (seeded path) | seed 20261002, delay 0, tier 2, cùng fold/session set với primary; không áp arm/tail (hướng random) | **1** |
| C2 always-in-RTH baseline | **CÓ** | tier 2, cùng folds | **1** |
| C3 flat anchor | không (0 trade) | log ledger; folds n/a | **1** |
| C4 OVN-direction-unconditional (dose-response) | **CÓ** | sign(m) mọi ngày, delay 0, tier 2 | **1** |
| C5 ±21d non-event convention | **KHÔNG** (descriptive return stats, không PnL path) | — | **0** |
| FOMC sensitivity (INCLUDE-event-days) | **CÓ** (filter khác ⇒ path mới) | đầy đủ: primary grid re-run = 24; rút gọn: arm×tail×delay0×tier2 = 4 | **24 đầy đủ / 4 rút gọn** |
| Era checks | KHÔNG (metrics trên paths đã có) | sign/expectancy per era + cờ `prev_short`/Friday trên chính primary cells; nếu owner đòi identity riêng ⇒ re-check trần | **0 mới** |
| **TỔNG thiết kế đầy đủ D1 (placebo đơn-delay — nhất quán với dòng C1)** | | primary 24 + FOMC 24 + C1(1)+C2(1)+C3(1)+C4(1) = 4 | **52 > 24 ⇒ BLOCKED_TRIAL_BUDGET** |
| **TỔNG thiết kế đầy đủ D2 (placebo cặp delay — rigor cao hơn)** | | primary 24 + FOMC 24 + C1(2: delay 0 và +30, cùng seed/tier)+C2(1)+C3(1)+C4(1) = 5 | **53 > 24 ⇒ BLOCKED_TRIAL_BUDGET** |
| **A-r4 — PHẠM VI DỰ KIẾN (Co-Owner chọn r5; CHƯA FREEZE, KHÔNG GO)** | | primary: delay{0,+30}×tier{2} = 8 + tier{1,3}×delay0 = 8; FOMC rút gọn 4; C1 placebo 1 (delay0, tier2, seed 20261002 đơn — giới hạn công bố, không claim permutation robustness); C2 1; C3 1; C4 1 | **8+8+4+1+1+1+1 = 24 đúng trần** |

Trạng thái xử lý sau quyết định Co-Owner r5: **A-r4 được chọn làm PHẠM VI DỰ
KIẾN của PB1-ES** (24 đúng trần: primary 16 + FOMC 4 + controls 4) — **chưa
freeze; không phải GO_REGISTER/GO_SCORE/GO_ORDER**; freeze chỉ xảy ra sau khi
D2 (phí ES đúng account, modeled cost) + D3 (lịch CME official) về đủ và A7
review spec. Giới hạn công bố kèm theo: **placebo đơn seed 20261002, đơn
delay — không claim permutation robustness** (distribution nhiều seed/multi-
delay là thiết kế đầy đủ D2 = 53 identity, đã BLOCKED_TRIAL_BUDGET). Lịch sử
số học r4→r5: dòng C1 luôn là 1 identity (delay 0); dòng tổng cũ ghi 53 vì
đếm controls = 5 với placebo cặp delay — **bất nhất đã sửa**: nay tách rõ
thiết kế đầy đủ **D1 = 52** (placebo đơn, nhất quán C1) và **D2 = 53**
(placebo cặp delay); cả hai > 24 ⇒ BLOCKED_TRIAL_BUDGET không đổi; A-r4 = 24
không đổi. NQ sibling: chỉ tính thêm khi trần còn và cost gate D2 mở. Mọi
identity khi chạy (kể cả C1–C4) vào observed denominator, không giấu.

Cơ chế kinh tế: OVN thông tin (news châu Á/châu Âu, macro 07:30 CT spike ×2-4
đo được) tích luỹ khi liquidity mỏng; nhà cung ứng thanh khoản RTH mở sách
chậm → continuation; HOẶC đuôi OVN là over-extension của crowd mỏng → reversion
(định lượng đối nghịch bởi VR<1). Hai cơ chế này không cùng sống sót —
đăng ký song song là falsification-by-competitor.

## 2. PB2 — London-morning range → US-session daytrade (6E/6B) — **HOLD** [PROVISIONAL, KHÔNG ĐĂNG KÝ]

**PHÁN QUYẾT CO-OWNER: HOLD.** Lý do ancestry: **FOREX-FREE-V1/V2 London
failures** — họ London-session trên FX spot đã chết; bản futures này chưa
chứng minh khác họ. Điều kiện mở lại (cả hai, theo thứ tự): (1) **mechanism
court** — phân biệt cơ chế + nguồn thông tin + causal control so với họ chết
(§14.3 ancestry veto, representation-rho); (2) **placebo court** — clock/
placebo control phải có power phân định thật. Verify ECB (D4) KHÔNG tự mở
HOLD. Spec dưới đây giữ làm phác thảo, không hoàn thiện thêm.

**Câu hỏi kiểm thử (khi mở lại)**: phá vỡ range sáng London (08:00–11:00
local) có tiếp diễn trong phiên US (tới 16:00 CT) sau chi phí không? Arm
**PB2-CONT** vs **PB2-REV**.

| trường | đặc tả [PROVISIONAL] |
|---|---|
| Universe | 6E, 6B (2020-01→2026-09; chuỗi theo §1.3: 6E Friday-rule, 6B k=5 + cease-guard) |
| Tín hiệu | R_lon = high−low 08:00–11:00 Europe/London local (bucketing theo London local — DST law §1.2); trigger: 1m close ngoài biên R_lon trong 11:00–15:30 London |
| Entry | fill = open bar 1m kế sau trigger; **biến thể +1 bar và +30m delay bắt buộc** (07:30 CT US-block spike ×1.95 đo được rơi vào cửa sổ) |
| Đứng ngoài | (i) ngày ECB GC (6E) / BoE MPC (6B) base-EXCLUDE — vì 45/55 ECB dates chưa machine-verify (blocker Bước 1); sensitivity INCLUDE chỉ khi verify xong; (ii) FOMC days EXCLUDE (13:00 CT trong holding); (iii) London-morning coverage <80% bars kỳ vọng EXCLUDE; (iv) warmup 60d |
| TP/SL | như PB1 [PROVISIONAL R=2, ATR20] |
| Time exit | 16:00 CT |
| Roll | §1.3; flat trước close |
| Sizing | margin FX nhỏ (~2.2–2.6k/ct) — risk-based 0.5% [PROVISIONAL], cap 5 contracts [PROVISIONAL capacity] |
| Phí/spread/slippage | spread 6E/6B $18.75 (**close-proxy**) half-turn; exchange NOT_FETCHED ⇒ **BLOCKED modeled-cost statement** (không dùng chữ complete/measured); slippage = giả định {1,2,3 tick}/chiều như PB1 (D1) — PB2 đang HOLD nên không liệt kê identity |
| Counter-hypothesis | clock/placebo (entry cùng giờ không điều kiện range); always-in-London-window baseline; London-share drift split (6B 28.7→23.7%) |
| Kill rule | K1: hiệu ứng chỉ sống khi INCLUDE event-days ⇒ là event-effect (thuộc họ khác, cần surprise data không có) — kill bản session-breakout; K2:CONT và REV đều fail sàn; K3: 6E vs 6B trái dấu ⇒ không claim cơ chế chung; K4: DST-mismatch weeks hành xử ngược chiều bucketing ⇒ lỗi luật local-clock (bug, không phải alpha); K5: rolling-window sign instability qua 2020-22/2023-26 |

## 3. PB3 — RBA decision-window reaction daytrade (6A) — **PARK** [PROVISIONAL, KHÔNG ĐĂNG KÝ]

**PHÁN QUYẾT CO-OWNER: PARK.** Lý do: (i) n=67 events trên 6.8y — fold
trade-count floor gần như chắc chắn fail (K0 đã đoán trước, không burn budget
để chứng minh lại); (ii) hai lỗi mở của 6A chưa giải: tick-size legacy
conflict 5e-5 vs 1e-4 chưa adjudicated + roll k=5 chưa đo (A7-DC-F3). Điều
kiện mở lại: hai lỗi mở 6A được đóng + owner quyết định riêng. Spec giữ
nguyên làm phác thảo.

**Câu hỏi kiểm thử (khi mở lại)**: hướng phản ứng 5 phút đầu sau 14:30 Sydney
(decision minute 9.0× volume) có tiếp diễn tới cuối phiên Sydney/đầu London
không?

| trường | đặc tả [PROVISIONAL] |
|---|---|
| Universe | 6A (2020-01→2026-09) |
| Tín hiệu | hướng d = sign(giá 14:35 Sydney − giá 14:29 Sydney) [PROVISIONAL cửa sổ ±5'] chỉ tại 67 ngày RBA đã biết trước (bảng as-published) |
| Entry | 14:36 Sydney, fill open bar kế; book mỏng: bắt buộc +30m delay variant (Tokyo evening) |
| Đứng ngoài | ngày không-RBA; change-vs-hold là SPLIT báo cáo, không phải điều kiện (surprise thật NOT_RUN) |
| TP/SL/time exit | TP 2×SL [PROVISIONAL]; SL 1×ATR20; time exit 17:00 Sydney close [PROVISIONAL] |
| Roll | §1.3 (6A: k=5 CHƯA ĐO — phải đo trước scored, erratum A7-DC-F3; interim: daily-crossover + cease-guard declared) |
| Sizing | 1 contract tối thiểu, margin ~2k; thin book ⇒ cap 2 [PROVISIONAL] |
| Chi phí | spread 6A $20 proxy; tick legacy conflict 5e-5 vs 1e-4 chưa adjudicated ⇒ cost BLOCKED thêm một tầng |
| Counter | placebo: cùng entry-time ngẫu nhiên 67 ngày không-RBA khớp weekday |
| Kill rule | **K0 (đặt trước, kỳ vọng cao): n=67 events trên 6.8y ⇒ fold trade-count floor gần như chắc chắn fail → NOT_RUN_THIN kill, không cứu**; K1: hold vs change split đảo logic; K2 book mỏng khiến fill-model không defens được (không BBO) |

## 4. Luật chung cho cả 3 playbook (khi cycle được đăng ký — hiện NO_GO_REGISTER)

1. **Nested train-only selection**: selection rule chỉ nhìn fold train; fold
   test/sealed untouched; S1 SEALED_UNTOUCHED.
2. Trial IDs phân biệt: `FBH1-PB1-CONT-ES-…` v.v. (cycle_id + playbook + arm +
   mã + config-digest); **trần 24 scored results TỔNG KỂ CẢ baseline**
   (Co-Owner). Mọi thiết kế phải kèm **bảng liệt kê toàn bộ scored identity**
   (arm, tail, delay, cost tier, FOMC sensitivity, era checks, baselines) như
   §1; vượt trần ⇒ ghi **BLOCKED_TRIAL_BUDGET**, không cắt lưới âm thầm; kết
   quả đã tính không được giấu — mọi identity đã chạy vào observed denominator
   kể cả khi publication fail.
3. Baselines/controls bắt buộc: flat (C3), always-in-window (C2), seeded clock-placebo (C1), dose-response unconditional (C4) — C1/C2/C4 là scored identity có PnL path, liệt kê trong bảng identity; drop-one-era sensitivity.
4. **Chi phí (D1/D2, r3)**: toàn bộ chi phí trong mô hình là **MODELED COST**.
   Slippage {1,2,3 tick}/chiều = giả định nghiên cứu; spread = close-proxy
   (thiên cao); fee 2.24 all-in = biểu HIỆN TẠI, ngay cả khi xác minh đúng
   account (D2) vẫn là input mô hình — **cấm gọi complete-cost/measured-cost**.
   **Phí lịch sử theo năm ≠ biểu hiện tại**: commission tier/exchange fee đổi
   qua 2010-2026; backtest phải khai báo biểu nào đang dùng (per-year nếu có
   nguồn — hiện NOT_RUN; hoặc current-as-approximation + disclosure). Không
   nhân stress trùng lặp (bộ 3 tier là chiều sensitivity duy nhất).
5. Reproduction độc lập (detached twin, byte-match) + A7 prelaunch trước GO.
6. Điều kiện chọn theo PnL đã thấy: CẤM (luật owner lặp lại; selection chỉ
   theo rubric freeze trước); **không chọn tail/hướng hậu nghiệm** — CONT và
   REV là hai arm đăng ký đồng thời.
7. 6F: NOT_RUN_DATA_ABSENT (D7 giữ); CL/NG/GC/SI: NOT_QUALIFIED_V2 — không
   nhét vào.
8. **Fill law (D5)**: chưa mua BBO; **bbo-1m KHÔNG đủ chứng minh intrabar
   fill/queue** — mọi fill mô phỏng giữ conservative (open bar kế; same-bar
   TP/SL xử lý kín theo SL-priority; không claim limit/queue fill). Đánh giá
   schema/quote ES được phép như nghiên cứu read-only.
9. **Holiday (D3)**: authority = lịch CME official historical theo
   product/year (acquisition lane riêng khi mở khóa); ngày không chắc chắn ⇒
   EXCLUDE/NOT_RUN, không inferred-pass.

## 5. Blocker còn lại (sau phán quyết D1–D7)

| mục | trạng thái sau D1–D7 | ai mở |
|---|---|---|
| Slippage | **GIẢI QUYẾT ở cấp giả định nghiên cứu** {1,2,3 tick}/chiều (D1) — vẫn không phải measured cost; mọi statement ghi rõ "assumption, not measured" | đo thật chỉ khi có fill/BBO sau này |
| Exchange fee ES | **NOT_RUN đúng-account** (D2) — 2.24 doc là biểu hiện tại; xác minh xong vẫn chỉ cho **modeled cost**, không nâng thành measured | owner (account của owner) |
| Exchange fee NQ/FX | đứng sau cost gate, không ưu tiên | owner, sau ES |
| Holiday official | **NOT_RUN** — authority đã chốt (CME official per product/year) nhưng lịch chưa về; ngày không chắc EXCLUDE/NOT_RUN. **CME transport từng bị blocked (FX-FUTURES-FRONTIER-V1 SNI-keyed; tái đo 2026-10-02: DNS resolve nhưng HTTP 403 app-layer)** — lane acquisition KHÔNG circumvent, KHÔNG suy diễn PASS | acquisition lane khi owner mở khóa |
| ECB 45/55 verify | **được phép** (lane $0) nhưng PB2 vẫn HOLD — không mở gì tự động | A1 chạy khi được điều phối |
| BBO/fill | **KHÔNG mua (D5)**; bbo-1m đã biết không đủ chứng minh intrabar fill/queue; đánh giá schema/quote ES là read-only research | owner nếu sau này đổi ý |
| IBKR re-fetch | **được phép read-only tuần tự** nếu lock/pacing cho phép (D6) — CHƯA CHẠY phiên này | A1 chạy khi cửa sổ mở |
| 6F | NOT_RUN_DATA_ABSENT, **chưa mua** (D7) | owner quyết định sau |

— Hết PLAYBOOKS_DRAFT r5. Không có gì ở đây được freeze; mọi con số
[PROVISIONAL]. `NO_GO_REGISTER · NO_GO_SCORE · NO_GO_ORDER` giữ nguyên cho
đến khi owner gõ GO tại gate của cycle tương lai (sau D2 + D3 + freeze spec
PB1-ES + A7 review).
