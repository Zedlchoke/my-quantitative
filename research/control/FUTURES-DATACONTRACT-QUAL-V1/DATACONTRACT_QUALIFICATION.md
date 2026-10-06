# FUTURES-DATACONTRACT-QUAL-V1 — Data Contract Qualification (Bước 1)

- Task: `FUTURES-DATACONTRACT-QUAL-V1`, lane A1 (Lead), theo chỉ thị owner 2026-10-03
  (điều chỉnh thứ tự): **BƯỚC 1 chốt data contract sạch → BƯỚC 2 đặc tả playbook
  daytrading → BƯỚC 3 chỉ khi gate đủ mới đăng ký cycle.**
- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep`
  @ base `b71c837d1f72d17b35475ab5e2795f6d113c1f9f`, branch
  `prep/futures-behavior-10syms-20261002`.
- Phạm vi: 6 mã có dossier v2 (NQ, ES, 6E, 6B, 6A, 6J) + 4 mã v1-only (CL, NG,
  GC, SI) + 6F (owner nêu, không có data). Heavy lock lúc intake: FREE_PROVEN;
  không worker futures nào đang chạy.
- Taxonomy: **FACT** (nguồn chính + ngày) / **OBSERVED** (script + cửa sổ, theo
  dossier v2 đã A7) / **POSTULATED** / **NOT_RUN** / **BLOCKED**. Thiếu bằng
  chứng không bao giờ là PASS.
- Nguồn: `FUTURES-DEEPRESEARCH-V2-20261003/REPORT_VI_DEEPRESEARCH_V2.md`,
  `dossiers_v2/*.md` (đã áp errata đầy đủ, A7 0 BLOCKER), `analysis/ERRATA_SUMMARY.md`;
  intake riêng `research/control/FUTURES-DATA-10SYMS-V1/` (IBKR, không trộn
  claims dataset); v1 `FUTURES-BEHAVIOR-10SYMS-PREP-20261002/BACKTEST_LAUNCH_DRAFT.md`
  chỉ là bằng chứng lịch sử (era 14 tháng) — mọi con số v1 đã bị v2 đo lại.
- Phân biệt luật (owner): **construction rule** (roll timing, chain, session
  clock) ≠ **alpha hypothesis**; roll-gap/CIP là structural input, không tự coi
  là tín hiệu có edge.
- **Ràng buộc thứ tự bổ sung (owner, 2026-10-03)**: CHƯA viết/freeze playbook
  như executable spec khi A7 và DC-VERIFY chưa chốt Bước 1. Được phác thảo
  câu hỏi kiểm thử, nhưng mọi tham số entry/TP/SL/chi phí phải ghi
  **[PROVISIONAL]** cho tới khi contract mapping, event timestamps,
  calendar/roll và fill data được xác minh. Nếu Bước 1 chỉ PARTIAL → playbook
  phụ thuộc **BLOCKED**, không đi thẳng sang cycle registration.

---

## 1. DATA CONTRACT — đặc tả ràng buộc cho mọi cycle tương lai

### 1.1 Danh tính hợp đồng (contract mapping theo thời gian) [OBSERVED]

| mã | venue | multiplier | minTick | quote | registry v2 | ghi chú mapping |
|---|---|---|---|---|---|---|
| NQ | CME Globex | 20 | 0.25 | index pts | 111 cluster (4 stray loại) | **ALIAS VIEW RULE ràng buộc**: `instrument_id==16908 AND date<2020-06-01 → 'NQM0'` (ERRATUM F1; data 2020 đầy đủ 100%, không phải hole) |
| ES | CME Globex | 50 | 0.25 | index pts | 71 outright quarterly (ESHM0-2010→ESZ7-2027) | 2027 deferred tails loại bằng floor ≥100k volume; June expiry dời theo Juneteenth (2026-06-18 measured; 2027-06-17 từ definitions) |
| 6E | CME Globex | 125,000 | 5e-05 | USD/EUR | 90 contracts (33 quarterly + 57 serial) | serial chết (0.34% volume) — universe HMUZ-only |
| 6B | CME Globex | 62,500 | 0.0001 (definitions 19,183 hàng, adjudicated) | USD/GBP | 48 registry → 32 quarterly | 59 stray cluster cách ly (incl. GCQ4 leak 2,139 bars, 6BM5 early-cluster) |
| 6A | CME Globex | 100,000 | 5e-05 (vendor; legacy conflict 1e-4 CHƯA adjudicated) | USD/AUD | 86 contracts (32 quarterly) | 1,584 bars contaminant `6BU5` loại; instrument 7084 pre-activation strays loại |
| 6J | CME Globex | 12,500,000 | 5e-07 | **USD/JPY** (KHÔNG đảo) | 95 contracts (40 quarterly) | 6J UP = yen mạnh; "USDJPY-long" = 6J SHORT; band 1m 0.0061095–0.0099205 |

Nguồn danh tính: v2 dossiers §0/§1; identity song song từ intake IBKR
`S1_IDENTITY.json` (multiplier/minTick chỉ có ở S1, không tái suy từ raw —
caveat C4 của S9). `instrument_id` là key chính (miễn nhiễm decade-repeat),
definitions 2023-10+ cross-check 0 mismatch (6A), trước đó bằng time-cluster +
delivery-frame containment.

### 1.2 Session clock / DST / holiday [OBSERVED + 1 NOT_RUN]

- **Session template per symbol (đo từ bars, không giả định)**: 17:00 CT (D-1)
  → 16:00 CT (D), trade date = ngày Chicago của close; maintenance break
  16:00–17:00 CT (6J: 1,380 phút truyền thống; median bars/session 1,357).
  ES: close lịch sử 16:30 CT (→2012) → 16:15 CT (2013→2015-11) → 16:00 CT (từ
  2015-11/2016); NQ: Mon-Thu 16:15→16:00 CT từ 2015-09-21, Friday 15:15 CT
  hết từ 2012-12. Volume pre-2016 ngồi trong break bucket đã được tách.
- **DST-proven**: NQ 32/32 transitions modal-hour đúng, 0 unexpected flip;
  6E DST-mismatch weeks dịch đúng 1 giờ CT (chứng minh London-local bucketing);
  6B BoE 12:00 London anchor giữ minute 720 across mismatch weeks; 6J
  center-local windows (Asia/Tokyo v.v.). **Luật ràng buộc: mọi feature
  session-bucketed phải bucket theo clock THÀNH PHỐ CỤC BỘ** (Europe/London
  cho London windows, Australia/Sydney cho RBA, Asia/Tokyo cho BoJ), không
  theo CT cố định.
- **Holiday — nâng cấp r6 cho ES (lane D3-CMECAL)**: **17/17 năm (2010-2026)
  holidays + early-closes authority-backed** — 2026 LIVE_OFFICIAL
  (trading-hours.html fetch sống 2026-10-03; 403 cũ không tái lập, ghi như
  re-measurement có ngày); 2010 ARCHIVED_OFFICIAL từ PDF chính thức 38 trang;
  2011-2025 ARCHIVED_OFFICIAL (verbatim tables). **Expirations 36/68 quý
  ARCHIVED_OFFICIAL** (đủ 2012-2018 + 2025); NOT_OBTAINED 2019-2023 + 2026 —
  không suy diễn lấp gap; ES-specific 2026 Globex times NOT_OBTAINED (widget).
  5 mã CME khác: chưa trích trong phiên — giữ inferred. Binding rule không đổi:
  ngày không chắc ⇒ EXCLUDE/NOT_RUN. Bằng chứng:
  `analysis/d3_cmecalendar/ES_CALENDAR_EVIDENCE.md`.

### 1.3 Roll — construction rule strict-past, đóng băng từng mã [OBSERVED]

| mã | rule ràng buộc | bằng chứng | guard bắt buộc |
|---|---|---|---|
| NQ | PIT k=5 volume-crossover (trailing-5-session mean, quyết định tại close t, giữ từ t+1) | 66 rolls; daily-crossover DTE median 7; corr(roll-gap, spread)=0.999 | **cease-guard** (xem dưới) |
| ES | T-5 calendar (expiry = 3rd Friday + Juneteenth shift) | 66/66 lệch 0..−2 session vs crossover; OI cùng ngày 12/12 (2023-10+) | OI-rule chỉ legal 2023-10+ |
| 6E | roll tại close **Friday của expiry week** (= 1 session trước Monday last-trade) | 27/27 crossover đúng Friday đó; expiry rule 80/80 (holiday set đầy đủ: MLK, Presidents, Juneteenth 2022+, Columbus, Good Friday, Veterans) | declared-rule 0 thin sessions <10k |
| 6B | PIT k=5 volume-crossover | crossover median 11 session SAU declared roll (9-13), old vẫn liquid 66-172k; declared rule giữ book mỏng ~11 session (1,069..13,222/ngày) | **cease-guard** |
| 6A | k=5 là **[DECLARED-EXTRAPOLATION]** — dossier 6A đo **daily total-volume** crossover 9-15 ngày sau declared (median 11) + OI lead 2-3 session (2023-12+), KHÔNG đo k=5 trailing-mean trên 6A; phải đo k=5 trên 6A trước khi dùng scored [ERRATUM A7-DC-F3: tag [OBSERVED] cho k=5 là quá mức] | crossover 9-15 ngày sau declared (median 11); OI leads 2-3 session (2023-12+) | **cease-guard** |
| 6J | PIT k=5 volume-crossover + **cease-guard** | 27 rolls; OI leads raw volume crossover 1-3 ngày lịch (12/12, mode 2) | guard thiếu gây artifact 2022-09-20 (k=5 giữ U2 đã cease → session biến mất khỏi chain) |

**Cease-guard (mới, ràng buộc toàn FX)**: nếu contract đang giữ ngừng giao
dịch (<25% bars hoặc volume≈0 của session) mà rule chưa switch, force-switch
sang quarterly kế tiếp tại close session đó. Bài học 6J ERRATUM M-5/M-5b.
Timing-disclosure 6J m-5 (code gắn day-t volume) được giữ nguyên cho descriptive;
scored engine phải implement "quyết định tại close t, hiệu lực t+1" đúng chữ.

**Roll ≠ alpha**: mọi rule trên là construction. Roll-gap/CIP (6B corr +0.84
Pearson; 6A 16/16 khi |Δ|≥25bp; 6E 27/27 dấu nhưng r=0.91 vintage-fragile →
PIT-as-of −0.11; 6J near<far 100%) là **structural input** cho chi phí/adjust,
không phải tín hiệu. CIP-vintage sensitivity phải lượng hóa trước khi đăng ký
bất kỳ hypothesis carry/H2 nào (REPORT_VI "còn chờ") — không áp dụng cho 3
playbook daytrading (flat trước close, không giữ qua roll-carry).

### 1.4 Event release timestamps + available_at/PIT [FACT/OBSERVED, từng nguồn]

| nguồn | available_at | chất lượng PIT | trạng thái |
|---|---|---|---|
| FOMC statements (147 files = 132 a-statements + 15 b/c) | thời điểm "For release at" in-document (92 statements có proof, 2016+; 85 @14:00 ET + 7 irregular liệt kê) | primary-source as-issued HTML | **PASS_EVIDENCED** (2011-2015 chỉ day-level — 40 statements không có giờ) |
| ECB GC (55 ngày 2020-2026) | 14:15 CET decision / 14:45 presser | **55/55 machine-verified (lane D4-ECBVERIFY 2026-10-03: HTTP 200 + title + date-string từng ngày; 19/19 ngày hiệu lực MRO khớp tuyến phụ SDW; 2020-03-18 = biến thể tiêu đề PEPP, disclosed)**; assembly-method cũ bị thay thế | **PASS_EVIDENCED** (PB2 vẫn HOLD theo phán quyết — verify không mở gì) |
| BoE MPC (2020-2027) | 12:00 London (measured 3,451 vs 1,392 contracts/min) | calendar assembled bankofengland.co.uk (fetch 2026-10-02); rate-change subset == parquet exactly | **PASS_EVIDENCED (assembly-method disclosed)** |
| RBA cash-rate (1990→2026-09) | 14:30 Sydney, effective_date − 1 AU business day | bảng as-published đầy đủ trong corpus; 67 meetings đo anatomy | **PASS_EVIDENCED** |
| MOF intervention (386 daily ops 1991-05-13→2026-05-06) | **lag ~1 tháng** (monthly/quarterly) | tidy 386 hàng đã tái tạo + verify trên đĩa; 2022-10-24 ¥0.73T đã recover | **PASS_EVIDENCED** — KHÔNG có tín hiệu same-day; chỉ dùng ex-post/descriptive |
| CFTC CoT legacy (2006-01→2026-09-22) | Tuesday as-of → Friday 15:30 ET release, as-published no-revision | release-honest alignment (forward windows bắt đầu sau release) | **PASS_EVIDENCED** |
| US CPI/NFP (BLS), ABS, China calendars | — | `bls_gate/` trống; chưa fetch | **NOT_RUN** — mở khóa cần owner acquisition |
| Rates (SOFR/€STR/DFF/DTB3) | latest-vintage + ALFRED year-end snapshots | KHÔNG PIT-strict | **NOT_RUN cho PIT use** (chỉ dùng descriptive/CIP với sensitivity) |

### 1.5 Raw-vs-normalized reconciliation [OBSERVED; refresh 2026-10-03 bởi lane DC-VERIFY — 8/8 check, 6 FACT + 2 OBSERVED, 0 NOT_RUN]

- `cftc_legacy_tidy.parquet` bản fix sha256 `f7a2719e745c2f6f…362fca` **khớp**
  (15,347 hàng; `.bak_prefix_mixed_20261003` 13,369 hàng còn giữ); NQ ALT
  loader 850 hàng 2010-06-15..2026-09-22 **khớp**; `mof_intervention_tidy`
  **386 hàng + row 2022-10-24 (7296, JPY_buying) + bak 81 hàng — khớp**;
  NQ alias counts **exact** (92,075/19,406 bars; 58 dates; 21,824,572 vol);
  6E venue-OI probe week 2024-06-04 deduped **671,736 exact** vs raw-sum
  1,343,543 (reproduced artifact của claim đã retract — mỗi contract có đúng
  2 publication batches); inventory 6 mã khớp ballpark ≤0.36%.
- **PATH LAW (mới, ràng buộc)**: root vendor vật lý là
  `/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/`
  (KHÔNG dấu chấm). Path có dấu chấm
  `~/.my-quantitative-data/futures-databento-av1trim` **KHÔNG tồn tại** (đo
  2026-10-03) — mọi tham chiếu dấu chấm trong DISPATCH V2/dossier 6B là stale;
  nonprice và IBKR legacy nằm ở path có dấu chấm như cũ.
- Các luật reconciliation giữ nguyên từ V2: ES lọc exact-name "E-MINI S&P 500"
  (3 market trộn 1 id, đã fixed); venue-OI (GLBX stat_type-9) **luật dedupe
  publications** trước mọi join (claim "2×" đã RETRACT); 6A raw-sum chỉ dùng
  cho timing, cấm reuse cho levels; 6J volume definition gap (1m volume =
  0.455× cleared-volume) → **dùng volume SHARES/ratios, không absolute
  levels**; IBKR daily closes KHÔNG dùng làm fill price (settlement-vs-
  last-trade convention gap NQ 17.5 / ES 15 ticks đã đo); iCloud mirror
  10,539/10,539 SHA-khớp (báo cáo V2).
- **IBKR staleness (bằng chứng cho blocker 4)**: max mtime mọi nhóm mã = 2026-10-02
  09:37–10:46 (serial span ~69 phút) — mặt cắt overlap đã stale 1+ ngày và
  tường expired lùi dần mỗi tuần không re-fetch.

### 1.6 Exclusions ràng buộc [OBSERVED]

1. Calendar-spread instruments (mọi mã; row share tăng 6%→14% là fact, không
   vào price panel).
2. Stray clusters đã cách ly (NQ 4; 6B 59 incl. GCQ4/6BM5; 6A 6BU5 + instr
   7084; 6J 6AV3; ES deferred 2027 tails).
3. Serial months FX (dead books: 6E 0.34%, 6A median 51.5 lots/ngày, 6J ≤0.39%/năm).
4. Maintenance-break bars (1–5k/era, negligible, loại khỏi aggregates).
5. Session cuối/phần: 2026-10-01 partial tail; roll-date final partial
   sessions (6J 20 "depleted" đều là roll-final).
6. NQ alias-window: **recovered** sau re-measure (không còn NaN-hole); các số
   2020 của dossier được thay bằng giá trị addendum §1.5; erratum worst-day-date
   đã ghi. [ERRATUM A7-DC-F1: chỗ này còn viết "tới khi addendum land"]
7. Holiday/short sessions: inferred flags (§1.2).

### 1.7 Cost authority — trạng thái khai báo [FACT/NOT_RUN]

| mục | ES | NQ | 6E/6B | 6A | 6J |
|---|---|---|---|---|---|
| Commission IBKR $0.85/side (doc 2026-10-02) | ✓ | ✓ | ✓ | ✓ | ✓ |
| Exchange fee | **1.38+reg → all-in 2.24 (doc)** | **NOT_FETCHED** | **NOT_FETCHED** | **NOT_FETCHED** | **NOT_FETCHED** |
| Spread front median (close-proxy 20d, USD) | 12.50 | 32.50 | 18.75/18.75 | 20 | 25 |
| BBO true spread | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN |
| Slippage declared | **NOT_RUN_NO_DECLARED_VALUE** (cả 10 mã) — owner-declared scenarios bắt buộc trước pass/fail |
| Margin initial/maint (2 nguồn public, chênh <2%) | 26-29k | 42-46k | 2.4-2.6k / 2.2-2.4k | 1.9-2.1k | 2.7-3.0k |

Caveat: spread close-proxy **thiên cao** (NQ 6.5 ticks đặc biệt); không có
BBO → không claim spread thực. Stress law: ×1.0/×1.5/×2.0 trên
(spread + slippage-declared).

---

## 2. QUALIFICATION MATRIX (mã × chiều; OBSERVED/POSTULATED/NOT_RUN/BLOCKED)

Chiều: (A) contract mapping; (B) session/DST; (C) holiday official; (D) roll
strict-past; (E) event PIT; (F) raw-vs-normalized; (G) cost authority.

| mã | A mapping | B session/DST | C holiday | D roll | E event PIT | F reconciliation | G cost | verdict |
|---|---|---|---|---|---|---|---|---|
| NQ | OBSERVED (+alias view; **re-measured** — addendum §1.5 [ERRATUM A7-DC-F1: chỗ này còn viết "đang chạy"]) | OBSERVED (era-aware, 32/32 DST) | NOT_RUN official (inferred) | OBSERVED (k=5, 66 rolls) | OBSERVED (FOMC timed) | OBSERVED (alias + CoT ALT + IBKR overlap) | BLOCKED (fee NOT_FETCHED, slippage) | QUALIFIED_WITH_GAPS |
| ES | OBSERVED (71 contracts, Juneteenth) | OBSERVED (close history recovered) | **OBSERVED r6** (D3: holidays/early-closes 17/17 năm authority-backed; expirations 36/68; uncertain ⇒ EXCLUDE/NOT_RUN) | OBSERVED (T-5 66/66) | OBSERVED (FOMC timed) | OBSERVED (CoT exact-name, IBKR overlap) | PARTIAL (bảng phí public-reference plan/tier r6; account verification NOT_RUN; slippage = giả định) | QUALIFIED_WITH_GAPS |
| 6E | OBSERVED (90 contracts, serials dead) | OBSERVED (London-local proof) | NOT_RUN official | OBSERVED (Friday rule 27/27) | PARTIAL (ECB 10/55 verified) | OBSERVED (dedupe law; tidy fix) | BLOCKED (fee, slippage) | QUALIFIED_WITH_GAPS |
| 6B | OBSERVED (32 quarterly; strays cách ly) | OBSERVED (BoE anchor proof) | NOT_RUN official | OBSERVED (k=5; thin-window measured) | OBSERVED (BoE assembly) + PARTIAL (gilt ends 2024) | OBSERVED (whitespace fix số giống) | BLOCKED (fee, slippage) | QUALIFIED_WITH_GAPS |
| 6A | OBSERVED (86 contracts, 0 def-mismatch) | OBSERVED (Sydney/Tokyo/London local) | NOT_RUN official | OBSERVED (k=5 + OI lead) | OBSERVED (RBA table) / NOT_RUN (ABS) | OBSERVED (6BU5 excluded) | BLOCKED (fee, slippage; tick legacy conflict) | QUALIFIED_WITH_GAPS |
| 6J | OBSERVED (95 contracts) | OBSERVED (center-local) | NOT_RUN official | OBSERVED (k=5 + cease-guard MỚI) | OBSERVED (MOF 386 +lag law; BoJ titles) | OBSERVED (volume-definition gap disclosed) | BLOCKED (fee, slippage) | QUALIFIED_WITH_GAPS — phụ, quote-orientation law |
| CL | v1 dossier only (14 tháng IBKR) | v1 RTH-only | NOT_RUN | v1 declared (chưa đo sâu) | NOT_RUN | NOT_RUN | BLOCKED | NOT_QUALIFIED_V2 |
| NG | v1 only | v1 | NOT_RUN | v1 (NG 3rd-last-BD) | NOT_RUN | NOT_RUN (signed-surprise NG chưa pin) | BLOCKED | NOT_QUALIFIED_V2 |
| GC | v1 only | v1 | NOT_RUN | v1 | NOT_RUN | NOT_RUN | BLOCKED | NOT_QUALIFIED_V2 |
| SI | v1 only (SI 5000oz đúng class) | v1 | NOT_RUN | v1 | NOT_RUN | NOT_RUN | BLOCKED | NOT_QUALIFIED_V2 |
| **6F** | — | — | — | — | — | — | — | **NOT_RUN_DATA_ABSENT** (không trong 10-symbol intake lẫn v2 dossiers; acquisition/quality gate riêng, cấm thay bằng 6J) |

Ghi chú 6F (owner nêu): đưa vào coverage matrix với trạng thái duy nhất
NOT_RUN_DATA_ABSENT; mở khóa cần acquisition cycle riêng (data + identity + PIT
theo đúng §1) — không suy diễn, không thay thế.

---

## 3. Verdict tổng Bước 1

**DATA_PLANE: QUALIFIED_WITH_GAPS** (6 mã v2: mapping/session/DST/roll/
exclusions/reconciliation đều OBSERVED và đã qua 7 A7 của V2 + errata).
**REGISTRATION GATE (Bước 3): BLOCKED** bởi các thiếu hụt cụ thể:

1. **Cost authority**: bảng phí ES public-reference theo plan/tier đã có
   (r6, D2: IBKR Fixed 0.85 / Tiered 0.85-0.25 + exchange 1.386 + regulatory
   0.011; all-in tính 2.247 @≤1k) — nhưng **đối chiếu account thật vẫn NOT_RUN
   (owner đang xin chứng từ đã che)**; biểu lịch sử theo năm đa số
   CURRENT_SCHEDULE_AS_APPROXIMATION; 5 mã khác chưa có bảng; slippage = giả
   định {1,2,3 tick}/chiều (D1). ⇒ MODELED COST; không có complete-cost
   statement nào.
2. **Holiday official**: **ES đã có authority 17/17 năm cho
   holidays/early-closes (r6, D3)**; còn thiếu: expirations 2019-2023 + 2026,
   ES 2026 giờ cụ thể, và trích cho 5 mã CME khác. Ngày không chắc ⇒
   EXCLUDE/NOT_RUN.
3. ~~ECB dates~~ **ĐÃ XONG r6 (D4): 55/55 machine-verified**; PB2 vẫn HOLD.
4. **Serial IBKR re-fetch**: **đã chạy r6 (D6 PASS: canary + 24 request
   tuần tự, 6 file vào staging_refetch_20261003 + sha manifest, 0 ghi raw/)**;
   tường expired chưa lùi ở chu kỳ 1 ngày — việc này ĐỊNH KỲ hàng tuần.
5. ~~NQ 2020 re-measure~~ **ĐÃ XONG trong task này** (addendum §1.5; qualitative
   claims đứng vững, erratum worst-day-date mới được ghi).
6. **BBO/depth**: NOT_RUN — spread thực không đo được (chỉ close-proxy); fill
   data cho execution realism chưa có.

Theo luật owner: dừng ở qualification + playbook draft BLOCKED/NOT_RUN,
**không ghi READY, không đăng ký cycle scored**.

## 4. A7 (chốt Bước 1 — chạy TRƯỚC khi playbook thành spec)

Lane A7-DC (fresh-context) audit **riêng Bước 1**: DATACONTRACT_QUALIFICATION
+ analysis/verify (DC-VERIFY) + analysis/nq2020_remeasure; chỉ viết trong
`audit/a7_dc/`. Playbooks chỉ được viết SAU khi A7-DC chốt; nếu verdict Bước 1
là PARTIAL (dự kiến, do §3) → PLAYBOOKS_DRAFT ở dạng câu hỏi kiểm tra với mọi
tham số [PROVISIONAL], trạng thái BLOCKED, không freeze executable spec.

## 5. Owner actions mở khóa (chi tiết trong OWNER_DECISION_PACKET.md)

(a) Khai báo slippage scenarios (menu đề xuất kèm packet) — hoặc duyệt phương án
    evidence-based tiers; (b) fetch exchange fee per symbol (IBKR login hoặc
    duyệt scope ES-only); (c) chọn authority holiday calendar (CME unblock /
    exchange_calendars / chấp nhận inferred + disclosure); (d) chỉ thị serial
    IBKR re-fetch; (e) quyết định 6F acquisition cycle riêng; (f) sau khi (a)-(c)
    đủ + playbooks được A7 duyệt → điểm GO đăng ký cycle.

— Hết DATACONTRACT_QUALIFICATION (Bước 1). Mọi số truy được về dossier v2
+ script; không có claim PASS nào ngoài bằng chứng đã dẫn.
