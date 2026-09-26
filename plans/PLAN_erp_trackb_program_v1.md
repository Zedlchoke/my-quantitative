# PLAN (DRAFT) — ERP-TRACKB-PROGRAM-V1 — Master plan: chương trình BTCUSDT spot–perpetual delta-neutral basis/carry qua nhiều cohort

> **Status: `DRAFT_FOR_OWNER_DECISION — NOT REGISTERED, NOT EXECUTED.** File này
> không đăng ký cycle, không spawn worker, không download, không mở S1, không
> đụng shadow/daemon/dashboard, không tiêu GO nào, không đặt lệnh. Nó là chương
> trình tầng master nằm DƯỚI umbrella `ECONOMIC-ROBUSTNESS-PROGRAM-V1`
> (ACTIVE_LIGHT trong registry), Track B của umbrella §5.4 — kế thừa toàn bộ
> luật umbrella §§1–11 trừ khi child chặt hơn; mọi cohort là child cycle riêng
> với budget/freeze/A7/GO riêng. Owner phê chuẩn charter này bằng quyết định
> ghi vào `trackb_program/OWNER_PACKET_cohort1_<date>.md` (không cần registry
> row mới — umbrella đã là cycle quản trị đang sống).
>
> Authored 2026-09-26 bởi Lead từ owner instruction (verbatim intent: mở hướng
> nghiên cứu BTCUSDT spot–perpetual delta-neutral basis/carry; lập kế hoạch và
> triển khai theo từng gate; KHÔNG PHẢI GO vĩnh viễn cho scoring, sealed OOS,
> shadow hay giao dịch; vốn chung mô phỏng 100.000 USD không nhân đôi cho hai
> chân; dừng chờ owner tại các gate bắt buộc).

## 0. Program identity

```text
program_id    ERP-TRACKB-PROGRAM-V1  (master layer; scored cells = 0/0 —
             không bao giờ tự score; mọi scored surface thuộc child cohort)
parent        ECONOMIC-ROBUSTNESS-PROGRAM-V1 (umbrella, Track B + luật chung)
home surface  BTCUSDT spot (Binance spot) + BTCUSDT perpetual (USDⓈ-M,
             Binance fapi) — MỘT cặp, một venue; mở rộng symbol/venue = cohort
             mới + owner decision
goal          ≥1 strategy identity đạt chuẩn program-goal §4 (tối đa là
              CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION / paper tier trên
              venue duy nhất — §4.3 giới hạn cấu trúc) HOẶC kết luận
              NO_CANDIDATE/BLOCKED đúng gate
ledger        per-child trial_ledger.jsonl (append-only) + P-9 denominators
S1            SEALED_UNTOUCHED ở mọi nơi; sealed OOS per-identity một lần
orders        NONE — mọi kết luận paper/backtest tier; shadow/live là GO riêng
stops         §7 (hết giả thuyết mới / hết data authority / hết cửa sổ sạch /
              hết power / hết ngân sách ⇒ dừng đúng gate, không chạy vô hạn
              để ép ra winner)
capital       MÔ PHỎNG một vốn chung 100.000 USDT cho toàn bộ hai chân
              (§5) — simulation tier, không phải tài khoản broker, không đụng
             .epoch-2 portfolio của A4-draft (đó là surface shadow khác,
              owner-GO riêng)
```

## 1. Mục tiêu / không-mục-tiêu

### 1.1 Mục tiêu

Tìm kiếm theo cơ chế (mechanism-first) trên đúng một bề mặt BTCUSDT
spot–perp: mỗi cohort freeze tối đa 3 cơ chế kinh tế thật sự khác ancestry,
trả lời bắt buộc SÁU CÂU HỎI KINH TẾ (§3.2) TRƯỚC khi bất kỳ PnL nào được
tính, falsify trước PnL, score dưới cost book đo được trên vốn chung 100k
không nhân đôi, bảo toàn sealed OOS một lần, replication độc lập. Chuẩn
không hạ để có số dương: `REJECT_ALL`/`NO_CANDIDATE` là kết quả hợp lệ và
được kỳ vọng là kết quả modal (Track A: 2/2 cohort đóng REJECT_ALL).

### 1.2 Không-mục-tiêu

- Không cứu bất kỳ family đã chết (CARRY V6, BASISLV V14, BAB-LOWBETA V12,
  OITD V13, FUNDCROWD, XSECT-FUND-CARRY prospective 77:1, FOREX-V4 carry
  class rho 0.997–1.000) bằng đổi tên / đổi tham số / đổi timeframe / giả định
  maker fill / giảm phí — owner instruction 2026-09-26 liệt kê nguyên văn,
  cộng Q-3 cross-horizon rescue.
- Không hạ gate, không nới power, không "thử lại" sau khi một identity fail.
- Không claim live-readiness (umbrella §1.3). Không thay đổi shadow/dashboard,
  không đặt lệnh, không push/merge, không mở S1 — owner instruction
  2026-09-26 nguyên văn.
- Không tự duyệt: implementer không duyệt kết quả của chính mình; reproducer/
  A7 là lane độc lập (owner instruction 2026-09-26).

## 2. Data authority binding (đo được, không tuyên bố)

| Bề mặt | Nguồn & tiền lệ | Trạng thái |
|---|---|---|
| Funding settlements (8h, BTCUSDT-PERP) | fapi `/fapi/v1/fundingRate` pagination (tiền lệ V8/V11/V14/CHR3F) + `data.binance.vision` fundingRate monthly zip cross-check | floor fapi 2020-07-18 (CHR3F §2 đo); PIT: một settlement chỉ available TẠI thời điểm settle (`fundingTime`), rate của interval kế tiếp là PREDICTED ≠ observable khác — tách biệt |
| Perp bars | vision monthly klines + catalog `crypto_perpetual/BTCUSDT-PERP.BINANCE` (15m) | có sẵn một phần; cohort stage theo window của mình |
| Spot bars | vision monthly klines `spot/daily|monthly/BTCUSDT` | CHƯA stage — cần data gate đầy đủ trước PnL (probe/census/DST-free UTC calendar/license) |
| Basis | perp mark/last − spot last, tính từ hai bar series ĐỒNG HỒ | phái sinh, không phải nguồn độc lập |
| Phí | bảng phí venue-published (spot taker/maker, perp taker/maker, các tier) | Q-8: measured beats stated — giá công bố là DECLARED cho đến khi đối chiếu được với fills; anchor đo sẵn: two-leg taker RT ≈ 20–25 bps (umbrella §4.5) |
| Spread/slippage | vision bookTicker/aggTrades theo granary có sẵn | cần census điều kiện theo giờ fill; thiếu ⇒ BLOCKED không điền số đẹp |
| Borrow/margin spot, liquidation tape | — | **BLOCKED** theo Track B luật (e): levered/borrow variants không scoreable đến khi data-authority cycle mở |
| Venue thứ hai (OKX/Bybit funding) | — | BLOCKED-unauthorized: replication limb bề mặt độc lập (§4.3) chỉ mở khi owner unblock nguồn + license |

License posture: kế thừa posture Binance-public-archive của các cycle crypto
tổ tiên (DOCUMENTED_CANDIDATE → AUTHORIZED_INTERNAL_RESEARCH qua data gate
từng nguồn; P-25). Mọi verdict mang `SINGLE_VENUE_PANEL + PAPER_TIER`.

## 3. Kiến trúc cohort (luật cố định cho mọi cohort Track B)

1. **Council outcome-blind** (roster §6): proposals chỉ chứa cơ chế + 10
   trường umbrella §5.3; không PnL/PF/winner nào trong packet.
2. **Freeze tối đa 3 cơ chế thật sự khác ancestry** (F-0 court P-27 quyết
   trước rho, trước PnL); mỗi cơ chế 1 anchor + ≤2 neighbour + 1 causal
   control + 1 inverted control + 1 baseline set. Không grid, không blend,
   không sign-flip rename.
3. **Sáu câu hỏi kinh tế trả lời TRƯỚC PnL** — nguyên văn khung owner
   2026-09-26 (định dạng đầy đủ umbrella §5.3 + tracka-1 §7.3): (1) ai trả
   carry, vì sao họ bị ép/nóng lòng; (2) premium kỳ vọng bao nhiêu bps/period
   và rủi ro nào ta nhận (tên đuôi); (3) premium tồn tại bao lâu, cái gì xói
   mòn; (4) rủi ro nào ta gánh đổi lấy premium — khi nào hóa đơn phí vượt
   premium (breakeven horizon theo số đo §5); (5) observable PIT nào mã hóa
   cơ chế (funding settled/basis, available-time tách biệt); (6) kết quả quan
   sát nào BÁC BỎ, control nào phải KHÔNG tái tạo edge.
4. **Falsification battery pre-PnL**: F-0 class court → F-1 ancestry rho
   (một lần, skeptic lane, exact representation) → F-2 PIT battery (funding-
   settlement timing, spot–perp clock alignment, truncation proofs M-class
   P-18 cho mọi biến regime) → F-3 clock-placebo non-vacuous → F-4 baseline/
   beta controls → F-5 cost-survivability ceiling TRÊN PHÂN PHỐI ĐO ĐƯỢC
   (fill-hour conditional + funding-path stress) → F-6 feasibility nearest
   window → F-7 concentration pre-check. Skeptic VETO pre-PnL; cost auditor
   BLOCKED khi thiếu nguồn; PIT auditor không xem PnL.
5. **Scored walk-forward trên window ancestry-exposed** (§4.2), force-flat
   fold boundaries, gates G1–G8-style với margin-to-fail, stress ×1.5/×2.0,
   kill laws preregistered (child plan freeze nguyên văn).
6. **Sealed OOS một lần sau GO riêng** (GO-3): membership artifact sha256
   trước pass; arm chết không nhìn holdout.
7. **Đóng cohort**: A7 terminal fresh-context + two-half close (registry +
   P-9 ledger + FAMILY_FAILURES/MAP/LESSONS + errata bundle P-19). Loop cohort
   kế tiếp chỉ khi có THÔNG TIN MỚI được cấp quyền (§6 chương forex-program
   §6 đồng áp dụng).

## 4. Chuẩn kết luận của chương trình

### 4.1 Bậc thang verdict

`REJECT_ALL` (cohort) → `CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION` (dev +
sealed-OOS sống sót, paper tier) → replication ladder → tối đa
`BACKTEST_CANDIDATE_REPLICATED`-class **chỉ khi đủ cả ba limb** (impl độc
lập; thời gian chưa dùng để chọn; bề mặt độc lập). Không đạt limb nào ⇒ không
được viết "replicated".

### 4.2 Ràng buộc cấu trúc: window BTCUSDT toàn bộ đã outcome-exposed

Đo từ registry + FAMILY_FAILURES (2026-09-26): trục funding/basis BTCUSDT bị
tìm kiếm/scored trên 2020-07-18..2026-08-21 (V6 CARRY window trong đó; V12
BAB-LOWBETA; V13 OITD; V14 BASISLV; CHR3F 2024-08-20..2026-08-21 staged +
scored; BTC-H4 ×4 trên trục giá 2020–2026; PSV1 sleeves sống 2026-09-14+).
Hệ quả binding:

- Dev evidence của mọi cohort Track B mang nhãn `ANCESTRY_EXPOSED_DEV` —
  dùng để KILL và để engineering, KHÔNG BAO GIỜ là bằng chứng promote tự nó.
- Cửa sổ 2026-08-22..ngày freeze = `SEAM_CONSISTENCY_ONLY`, trong đó
  **2026-09-14 trở đi là `ANCESTRY_EXPOSED_SEAM`** (PSV1 sleeves sống từ
  2026-09-14 book quyết định trục funding với BTCUSDT trong benchmark/basis
  panel — A7 F2 relabel): chỉ PIT/parity/consistency, không bao giờ là
  bằng chứng chọn lọc.
- **Sealed OOS duy nhất có thật = tích lũy prospective sau freeze** (một
  look theo decision-count gates umbrella §5.12 D13/D26/D52映射 theo decision
  epoch của cơ chế). Verify per-window against registry tại GO-1 của child.

### 4.3 Replication limbs trên venue duy nhất — giới hạn công khai

Limb (iii) bề mặt độc lập (symbol/venue thứ hai) BLOCKED-unauthorized hôm
nay ⇒ trần program-goal thực tế là
`CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION (SINGLE_VENUE)`. Viết "replicated"
mà thiếu limb (iii) là vi phạm ngôn từ của chương trình.

## 5. Hợp đồng mô phỏng vốn chung 100.000 USDT (binding mọi scored cell)

1. **Một book, hai chân, không nhân đôi vốn**: equity khởi đầu 100,000 USDT
   cho CẢ hai chân; notional spot ≤ book, perp short notional = spot notional
   (delta-hedge 1:1), margin perp và buffer rút từ cùng book. Không bao giờ
   mô phỏng hai book 100k riêng cho spot và perp (owner instruction
   2026-09-26).
2. **Cost book đo được mới được vào số liệu**: spot fee + perp fee (theo tier
   venue, DECLARE cho đến khi validate), spread spot/perp tại giờ fill (census
   điều kiện), slippage (replay-vs-fill nếu có, else DECLARED + stress),
   funding THỰC NHẬN/TRẢ theo settlement series từng 8h, hedge drift
   (tracking error hai chân theo bar), margin buffer + đường liquidation
   (maintenance tier venue-published = DECLARED model; liquidation tape
   BLOCKED — khai báo, không đo được), outage scenario (miss N settlement +
   gap reopen bất lợi — DECLARED band), capacity (top-of-book/ADV order-of-
   magnitude).
3. **Stress bắt buộc**: ×1.5 và ×2.0 trên MỌI thành phần cost + funding-path
   stress theo phân phối settlement đo được (anchor: 24.7% settlement âm
   trong downtrend; worst −0.30%/8h ≈ 2.5 fee round-trips; downtrend mean ≈
   1.11 bps/ngày ⇒ breakeven ≈ 18–23 ngày ở anchor taker RT 20–25 bps, 27–34
   ngày @×1.5 — umbrella §4.5). Thiếu bằng chứng quan trọng ⇒ BLOCKED/NOT_RUN,
   không điền số đẹp.
4. **Bộ so sánh bắt buộc**: giữ tiền mặt (cash 0%), long BTC spot (cùng cost
   book), perp-only unlevered funding structure nếu scoreable, và các control
   của cơ chế. Mọi artifact tách bạch gross / declared-cost net /
   measured-cost net / funding-received / funding-paid / fees / slippage /
   drift (Q-14: gross-net pair cùng vehicle).
5. **Luật form scoreable trên BTCUSDT**: cash-and-carry thu funding dương
   (long spot + short perp, unlevered) là form chuẩn; inverse (short spot cần
   borrow) BLOCKED theo luật (e) cho tới data-authority mở. Maker-only
   assumption bị cấm trong cost book cho tới khi queue-position đo được.

## 6. Roster lane (mỗi cohort; ranh giới mù outcome)

Bảng roster của `PLAN_erp_forex_program_v1.md` §5 áp dụng nguyên văn (A1
controller; PIT/data auditor FAIL-ngay; economic skeptic VETO pre-PnL;
cost/execution auditor BLOCKED; blind proposers P1..Pn; independent
reproducer/A7 không kế thừa verdict implementer). Thêm riêng Track B:
reproducer/A7 bắt buộc viết lại engine funding-settlement accounting từ raw
settlement bytes, không import engine implementer.

## 7. Điều kiện dừng / đổi hướng (fail-safe)

Dừng và báo owner khi: (a) ≥2 cohort liên tiếp trống slate sau F-0/F-5 ⇒
`NO_CANDIDATE` (giả thuyết mới cạn — không chạy vô hạn); (b) hết data
authority (funding/spot/klines/fee một trong đó blocked + owner chưa mở);
(c) sealed map trống (không còn cửa sổ sạch/thời gian tích lũy); (d) không
đạt power với ngân sách còn lại; (e) hết ngân sách owner cấp. Cả
`NO_CANDIDATE` lẫn `BLOCKED_<class>` đều là thành phẩm (Q-16).

## 8. Ngân sách & chuỗi GO (mỗi cohort)

- Budget scored cells: child tự chốt (cohort-1 council 2026-09-26 froze
  **1 mechanism → 7 cells** = M1 6 arm-classes + 1 diagnostic arm; slots 2–3
  empty by F-0 court — fewer is lawful, SLOT_LEFT_EMPTY; observed/published
  split P-9). Holdout/sealed looks ledgered, không cộng vào cell cap.
- Chuỗi gate: **GO-1 register + council freeze + data gate + falsifiers +
  trial freeze (DỪNG)** → A7 prelaunch → **GO-2 scored dev** → nếu sống sót:
  A7 kiểm → **GO-3 sealed prospective OOS + replication pass (MỘT LẦN)** →
  A7 terminal → two-half close. GO phrase của cohort ghi trong child plan;
  GO gõ trước gate = intent chết unconsumed (P-8). Prompt mở chương trình
  2026-09-26 KHÔNG PHẢI GO-2 hay GO-3 (owner instruction nguyên văn).

## 9. Artifacts & nhãn terminal

Per-child: council reports + handoffs (`zcode_orch_v3_handoff@1`), data-gate
verdict, falsifier battery results, freeze artifact (seeds, membership, pins
— P-19), dry-run non-vacuous, scored cells + margins, seam/kill-law files,
DSR (per-period series persisted — P-11), repro twin, A7 prelaunch +
terminal, trial_ledger.jsonl, CYCLE_VERDICT.md. Nhãn bắt buộc trên mọi row:
`SINGLE_VENUE_PANEL`, `PAPER_TIER`, `ANCESTRY_EXPOSED_DEV` (dev rows),
`FUNDING_PATH_STRESSED`, `LIQUIDATION_MODEL_DECLARED`, `FILL_QUALITY_CLASS_<
measured|declared>`. Terminal vocabulary: umbrella §9 + `NO_CANDIDATE`.
Mọi verdict âm là first-class close.
