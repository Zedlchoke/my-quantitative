# PLAN (DRAFT) — PWS-PROGRAM-V1 — Master plan: chương trình tìm kiếm strategy identity theo từng pair (Forex + Crypto, trần khảo sát ≤100 identity)

> **Status: `DRAFT_FOR_OWNER_DECISION — NOT REGISTERED, NOT EXECUTED.** File
> này không đăng ký cycle, không spawn worker/lane, không download, không mở
> S1/sealed holdout, không đụng shadow/daemon/dashboard, không đặt lệnh,
> không tiêu GO nào. Nó nằm DƯỚI umbrella `ECONOMIC-ROBUSTNESS-PROGRAM-V1`
> (ACTIVE_LIGHT trong registry) — kế thừa toàn bộ luật umbrella §§1–11, charter
> `ERP-FOREX-PROGRAM-V1` (R0–R6, roster §5, reopening law) và luật mechanism/
> fences của `SRLV-PROGRAM-V1` (F-0 court, PIT §3, kill rules §10, stop
> conditions §11) trừ khi child chặt hơn. Owner phê chuẩn charter này bằng
> quyết định ghi vào
> `research/control/PWS-PROGRAM-V1/OWNER_PACKET_program_open_2026-09-26.md`.
>
> Authored 2026-09-26 bởi Lead từ owner instruction (verbatim intent: lập và
> vận hành chương trình tìm kiếm tối đa ~100 strategy identity khác biệt về
> cơ chế, nghiên cứu TỪNG PAIR MỘT trên Forex + crypto; 100 là TRẦN KHẢO SÁT
> chứ không phải chỉ tiêu phải backtest đủ — multiple-testing là rủi ro đã
> được nghiên cứu: Harvey–Liu–Zhu, Bailey và cộng sự về backtest overfitting;
> mục tiêu là ứng viên có bằng chứng kinh tế, PIT-clean, sau phí, tái lập
> được; không âm thầm dùng prompt này làm quyền vượt cap; A7 review + owner
> duyệt amendment trước khi đăng ký/chạy; prompt này KHÔNG PHẢI GO-1/GO-2/
> GO-3, không đặt lệnh, không sửa shadow, không push/merge, không mở S1).

## 0. Program identity

```text
program_id    PWS-PROGRAM-V1 (master layer; scored cells = 0/0 — không bao
             giờ tự score; mọi scored surface thuộc child pair-cycle)
parent        ECONOMIC-ROBUSTNESS-PROGRAM-V1 (umbrella, luật chung §§1–11)
sibling-law   ERP-FOREX-PROGRAM-V1 (R0–R6, roster, reopening R1–R5),
              SRLV-PROGRAM-V1 (F-0 court, PIT §3, K-* kill rules)
tracks        PWS-FX (EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF —
              chịu luật reopening R1–R5; frontier đang NO_CANDIDATE)
              PWS-CX (BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT — Binance USDⓈ-M
              perp, không gian còn mở nhưng bounded bởi ancestry + cost)
ceiling       ≤ 100 strategy identity ID toàn chương trình (TRẦN KHẢO SÁT
              của proposer space — KHÔNG phải chỉ tiêu, không phải quota
              phải score; xem §2). 100 proposal khác nhau ⇒ theo luật
              multiple-testing, xác suất chọn trúng may mắn tăng theo N nếu
              chọn max — vì vậy luật chọn/multiple-testing ở §6 là binding.
budget cap    theo amendment `DRAFT_amendment_PWS-PROGRAM-V1_caps_2026-09-26.md`
              (đề xuất mặc định: ≤96 scored cells program; ≤18 cells/pair;
              ≤6 pair-child FX + ≤4 pair-child CX; ≤3 identity frozen/pair).
              KHÔNG hiệu lực tới khi owner duyệt amendment (P-8).
goal          ≥1 strategy identity đạt BACKTEST_CANDIDATE_REPLICATED (đủ 7/7
              điều kiện R0–R6 của forex-program charter) trên ≥1 pair, HOẶC
              kết luận NO_CANDIDATE / BLOCKED_<class> đúng gate
ledger        per-child trial_ledger.jsonl (append-only) + IDENTITY_REGISTRY
              program-level (§2) + P-9 denominators; mọi outcome-viewed
              pair/timeframe/parameter = 1 trial row
S1            SEALED_UNTOUCHED ở mọi nơi; sealed OOS per-identity một lần,
              sau GO riêng
orders        NONE — mọi kết luận paper/backtest tier; shadow/live là GO riêng
stops         §11 (hết giả thuyết mới / hết data authority / hết OOS sạch /
              hết power / hết ngân sách / 2 pair liên tiếp REJECT_ALL ⇒
              viability council ⇒ dừng đúng gate, không chạy vô hạn)
```

## 1. Mục tiêu / không-mục-tiêu

### 1.1 Mục tiêu

Tìm kiếm mechanism-first, **pair-by-pair**: mỗi pair là một child cycle riêng
với data/license/PIT/cost/power gate riêng, council outcome-blind, falsify
TRƯỚC PnL, score dưới cost book đo được, bảo toàn sealed OOS, replication
độc lập. Không gian đề xuất RỘNG (≤100 identity thật sự khác payer/
information/risk), không gian score HẸP (chỉ identity qua được toàn bộ
falsifier mới được freeze; ≤3 identity/pair). Chuẩn không hạ để có số dương:
`REJECT_ALL` / `NO_CANDIDATE` hợp lệ và theo base rate đo được là kết quả
modal (xem §6.4).

### 1.2 Không-mục-tiêu

- **100 không phải chỉ tiêu.** Không ép đủ 100 proposal, không dựng biến thể
  tham số/đổi tên/đảo dấu/đổi filter/đổi timeframe để lấp số (K-F0 kill).
- Không chọn pair theo PnL rồi gọi pair đó là OOS; thứ tự pair được đăng ký
  TRƯỚC khi pair đầu tiên được score (§3.2, chống cherry-pick surface).
- Không cứu family đã chết (FAMILY_FAILURES 136 entries; 12 dead classes FX;
  fences crypto) bằng bất kỳ hình thức re-clock/re-label/buffer/window
  (umbrella §6; Q-3; F-0 court; LESSON P-28).
- Không tái chạy panel FX cũ như discovery; không score lại EURUSD/GBPUSD
  hay panel đã outcome-exposed khi không có reopener bytes (§5).
- Không hạ gate, không nới power, không "thử lại" sau khi một identity fail
  OOS; không parameter rescue sau khi PnL xuất hiện.
- Không gọi OHLC sweep là thanh khoản order-book; không dùng liquidation/
  OI/depth lịch sử khi không có (§7); không cứu SETTLE-RESOLVE bằng đảo
  chiều (inverted out-earn = kill, không phải signal — LESSON P-28).
- Không claim live-readiness (umbrella §1.3); không đụng shadow/dashboard/
  worker đang chạy; không push/merge; không mở sealed OOS; không đặt lệnh.
- Mass test KHÔNG PHẢI mass selection (SRLV §8 nguyên văn): cùng một
  identity frozen áp toàn panel được phép của pair-child; cấm tối ưu riêng
  từng pair rồi gọi là replication.

## 2. Identity registry — luật trần 100 identity

### 2.1 ID và vòng đời

- Mỗi đề xuất được cấp ID `PWS-<TRACK>-<PAIR>-I<NNN>` (vd
  `PWS-CX-SOLUSDT-I001`) khi vào registry; ID không bao giờ tái sử dụng.
- Registry: `research/control/PWS-PROGRAM-V1/IDENTITY_REGISTRY.jsonl`
  (append-only, tạo tại charter approval, 0 rows khi mở). Mỗi row:
  `{schema: pws/identity@1, id, track, pair, proposed_by_lane, date_utc,
  payer, premium, information_layer, cost_class, falsifier, status,
  status_date, evidence_paths[]}`.
- Status transitions (một chiều): `PROPOSED → F0_KILLED | FREEZE_ELIGIBLE →
  FROZEN → SCORED → <verdict> | DEFERRED | WITHDRAWN_BY_OWNER`. `F0_KILLED`
  và mọi verdict âm là first-class rows — kills là assets (Q-16), không
  xóa, không sửa. `DEFERRED` (parked, có thể quay lại) vẫn chiếm chỗ trần;
  chỉ `WITHDRAWN_BY_OWNER` (owner rút bằng quyết định ghi) là ra khỏi trần.
- **Trần 100**: tổng số row có status ≠ `WITHDRAWN_BY_OWNER` không
  vượt 100 trong toàn đời chương trình. Đạt 100 ⇒ proposer space đóng;
  scoring của identity đã frozen vẫn tiếp tục theo GO riêng. Trần này là
  luật chống multiple-testing (cùng §6.3), không phải target.

### 2.2 Điều kiện một proposal được vào registry (thiếu ⇒ `BLOCKED_INCOMPLETE`)

Đầy đủ 10 trường umbrella §5.3 (payer/premium/persistence/risk transferred/
PIT observable + availability evidence/holding horizon/capacity/costs
decomposition/falsifier + controls) VÀ trả lời được 3 câu F-0 court
(SRLV §2.3): (1) skeleton test — bỏ mechanism-specific observable, giữ
trigger/direction/exit shape, còn edge không? cùng shape = cùng family chết;
(2) payer test — ai trả, vì sao họ BẮT PHẢI trả, tự arbitrage đi không;
(3) information test — thông tin gì chưa có trong clock/trend/spread (Q-7).
Skeptic lane có VETO pre-PnL tại F-0. **"Thêm observable không phải thêm cơ
chế"** (owner law 2026-09-26, LESSON P-27).

### 2.3 Khác biệt tối thiểu giữa hai identity (anti-variant law)

Hai proposal là MỘT identity (⇒ F0_KILLED `VETO_VARIANT_SAME_FAMILY`) nếu
chỉ khác nhau bởi: rename; đảo dấu/invert; thêm/bớt filter/gate Observable
trong khi trigger/direction/exit shape và payer giống; đổi timeframe/
cadence của cùng lịch sử giá (re-clock Q-3); đổi session/cặp giữ nguyên
skeleton. Hai identity khác nhau phải khác ít nhất HAI trong ba: (a) payer
và cơ chế ép trả tiền; (b) information layer PIT (nguồn + observable);
(c) risk shape (holding horizon, direction logic, risk transferred).

## 3. Kiến trúc pair-by-pair (binding)

### 3.1 Một pair — một child cycle

Mỗi pair có child cycle riêng (`PWS-CX-SOLUSDT-C1`, `PWS-FX-AUDUSD-C1`, …)
với plan child riêng (draft sau khi charter duyệt), worktree/branch theo
registry, trial_ledger riêng, cost book theo track, GO phrase riêng, verdict
riêng. Hai track không trộn ledger/cost book/verdict/GO phrase (SRLV §4).

### 3.2 Thứ tự pair đăng ký trước, tuần tự, mù outcome

- **Thứ tự pair được freeze tại charter approval** (trước khi pair đầu tiên
  được score) — đổi thứ tự = owner amendment. Pair tiếp theo chỉ bắt đầu
  sau khi pair trước được A7 terminal + two-half close. Không quá MỘT
  pair-child đang ở giai đoạn scored tại một thời điểm (heavy lock là
  mechanism enforcement).
- Proposal drafting (outcome-blind, không chạm data) được phép tích lũy vào
  registry cho mọi pair bất kỳ lúc nào; council/data gate/scoring của một
  pair chỉ mở khi đến lượt pair đó theo thứ tự đã đăng ký.
- Đề xuất mặc định (owner duyệt/sửa tại Q3 của OWNER_PACKET):
  - **CX:** SOLUSDT → BNBUSDT → BTCUSDT → ETHUSDT. Lý do: SOL/BNB chỉ
    baseline-exposed (sạch nhất về ancestry — positive trên đó mạnh nhất);
    BTC giàu cost authority nhất nhưng dày fence (G5 concentration
    structurally unpassable cho long-biased); ETH xếp cuối do va chạm
    `ETHUSDT-OPEN-SEARCH-V2` đang ACTIVE (STOP-1 chờ owner GO) — luật không
    xâm phạm theo OUTCOME_EXPOSURE_MAP §2.1: PWS không tiêu GO phrase hay
    surface S1 của cycle đó, không re-stage corpus của nó.
  - **FX:** mọi pair `BLOCKED_FRONTIER_NOT_REOPENED` cho tới khi một
    reopener R1/R2/R3/R5 có bằng chứng bytes (§5). Khi reopener mở: pair
    đầu tiên là pair mà reopener tạo ra bề mặt MỚI thật (R2 nguồn độc lập
    ⇒ pair có corpus mới đầy đủ sớm nhất; R1/R3 ⇒ AUDUSD hoặc USDCAD vì
    dev-eligible cho observable mới + sealed 2026-H1 còn nguyên).
    EURUSD/GBPUSD/USDJPY giữ vai trò ancestry/fixture/cost authority;
    USDCHF BLOCKED_DATA_LICENSE (0 bytes) — chỉ mở theo R4 sau khi một
    identity qua dev gates.

### 3.3 Per-pair gate (GO-1 của child, không score-all)

Mỗi pair qua gate riêng: data probe/census/DST/rollover/scale fixtures,
license posture từng nguồn, PIT seam check, cost census (spread theo giờ
fill; crypto: funding dual-book + fee declared + spread census từ
bookTicker/aggTrades — thiếu ⇒ BLOCKED), power analysis tại freeze.
Trạng thái đo sẵn: `research/control/SRLV-PROGRAM-V1/DATACOST_FEASIBILITY_
MATRIX.md` (kế thừa làm baseline; child re-verify bằng bytes tại GO-1 của
mình). Cặp thiếu nguồn hợp lệ ⇒ `BLOCKED_<reason>` ghi vào freeze artifact;
KHÔNG âm thầm thay cặp; thay slate = owner decision riêng.

## 4. Phân bổ identity & ngân sách (đề xuất; hiệu lực theo amendment)

### 4.1 Phân bổ trần 100 identity theo pair (trần khảo sát, không phải eligible)

| Track | Pair | Trần identity khảo sát | Trần frozen/scored | Tran scored cells | Trạng thái mở cửa hôm nay |
|---|---|---|---|---|---|
| CX | SOLUSDT | 20 | ≤3 | ≤18 | MỞ (dev, ancestry-disclosure, baseline-exposed) |
| CX | BNBUSDT | 15 | ≤3 | ≤18 | MỞ (như SOL) |
| CX | BTCUSDT | 15 | ≤3 | ≤18 | MỞ (dev, ancestry-exposed dày; fence G5 long-biased) |
| CX | ETHUSDT | 10 | ≤3 | ≤18 | MỞ nhưng xếp cuối (va chạm EOS-V2; surface S1 của cycle đó cấm tiêu) |
| FX | AUDUSD | 10 | ≤3 | ≤18 | KÍNH (dev chỉ cho observable MỚI qua D2; sealed 2026-H1 còn nguyên; chờ reopener) |
| FX | USDCAD | 10 | ≤3 | ≤18 | KÍNH (như AUDUSD) |
| FX | EURUSD | 5 | ≤3 | ≤18 | ĐÓNG (outcome-exposed trọn window — chỉ ancestry/fixture/cost authority; không bao giờ dev/OOS cho search mới) |
| FX | GBPUSD | 5 | ≤3 | ≤18 | ĐÓNG (như EURUSD) |
| FX | USDJPY | 5 | ≤3 | ≤18 | ĐÓNG (như EURUSD) |
| FX | USDCHF | 5 | ≤3 | ≤18 | ĐÓNG (BLOCKED_DATA_LICENSE, 0 bytes; chỉ R4 sau khi có identity) |
| — | Dự phòng cross-pair (replication one-look) | — | — | không tăng cap | theo R5 replication, xem §8 |
| | **Tổng** | **100** | ≤30 | **≤96 program (FX≤48/CX≤48)** | |

Các trần KHÔNG cộng dồn: program cap ≤96 (FX≤48/CX≤48) luôn thắng; trần
per-pair ≤18 và ≤3 identity/pair chỉ phân bổ trong program cap (binding
order chi tiết trong amendment §3).

### 4.2 Số identity đủ điều kiện THẬT (honest, theo base rate đo được)

- **Hôm nay, scoreable được: 0 identity FX** (VIABILITY: 0/12 class qua
  pre-PnL; zero remainder trên authorized space) và **≤12 identity CX về
  mặt cấu trúc** (≤3/pair × 4 pair), bị tiếp tục cắt bởi ancestry fences
  (crypto-ng 11/11 chết ở |rho| 0.20; BTC-BEAR double veto; PSV1
  CONTROL_OUTEARNED; EOS1-E1/E2; G5 concentration) và cost ceiling
  (funding measured, fee declared 5bps+1tick, spread census chưa chạy).
- Base rate đo được của pipeline falsifier: ERP1-TRACKA-COHORT-2 7/7 chết
  pre-PnL; SRLV-CX-C1 3/4 skeptic-veto, 1/1 frozen chết ở dev gates;
  EURUSD open-search 1/48 gate-eligible rồi fail holdout; DSR V14 0.00224
  trên N=146. **Kỳ vọng trung thực: đa số pair-child đóng REJECT_ALL hoặc
  slate rỗng; số identity thực sự được score trên toàn chương trình khả cao
  ∈ [0, 16]** (≤96 cells ÷ 6 cells/identity; identity tối thiểu 4 cells =
  anchor + causal control + inverted control + baseline).
- ≥76/100 identity theo thiết kế KHÔNG BAO GIỜ được score — chúng sống và
  chết ở registry (F0_KILLED/DEFERRED). Đây là feature, không phải waste:
  mỗi kill pre-PnL tiết kiệm cells + OOS (owner note cohort-2 nguyên văn).

### 4.3 Năng lực tính toán

Heavy lock machine-wide: MỘT scored run tại một thời điểm (`NOT_RUN_RESOURCE_
CONFLICT` nếu held; không kill worker ngoại). Council/proposer/skeptic/PIT/
cost lanes là light, chạy song song được. Nhịp dự kiến mỗi pair-child:
1–3 ngày council+falsifiers+freeze; scored run bounded bởi time-stop 14
ngày lịch/gate (§11f); A7 terminal + two-half close. 10 pair tuần tự ⇒
khung thời gian nhiều tuần-tháng; stop conditions sẽ đóng sớm hơn theo kỳ
vọng. Shadow workers (FX-RANGEFADE, PSV1, ILLIQ, gateway) không bao giờ
giữ heavy lock — không đụng.

## 5. Frontier law — PWS-FX (kế thừa SRLV §6 + forex program status, binding)

Forex đang `NO_CANDIDATE` trên frontier được cấp quyền (VIABILITY 2026-09-26:
12 classes enumerated, 0 survive; sàn chi phí 3.6/4.4 pips stressed RT chia
đôi không gian với zero remainder; P3-A đo chết tại tick geometry IBKR:
crossing p50 0.9–1.0 pip tại book cơ bản, p25 0.8 — mọi cách đọc đều vượt
ngưỡng đóng băng ≤0.41 pip yêu cầu tại stress ×2.0). **Không pair
FX nào được score khi chưa có MỘT reopener dưới đây với bằng chứng bytes +
license + cost authority đo được tại GO-1 của child:**

| Reopener | Bằng chứng cần | Mở gì |
|---|---|---|
| **R1** broker cost authority | two-sided market-data subscription + Flex statement (commission + overnight interest measured) | all-in được ĐO (cao hơn hay thấp hơn ước tính đều được ghi nhận đúng); cơ chế chết F-5 chỉ xét lại bằng số đo |
| **R2** nguồn bid/ask độc lập | TrueFX registration / OANDA v20 practice / Dukascopy written consent (owner action) + bytes on disk + license gate PASS + cross-source PIT seam check | nguồn thứ hai cho cost authority; window mới outcome-free; limb replication (iii) nguồn-độc lập |
| **R3** financing band | broker-grade swap data cited | class multi-day hold / carry (đang BLOCKED NG6/NG7 F4) |
| **R5** information layer mới | artifact có authority (không-PnL) | observable mới qua D2 |
| **R4** (không phải reopener scoring) | một identity qua dev gates | slate amendment USDCHF/new pairs |

- Không reopener ⇒ pair-child FX đóng `BLOCKED_FRONTIER_NOT_REOPENED`, 0
  scored cell, 0 holdout look — kết quả đúng, không phải thất bại (Q-16).
- minTick 0.5 pip (đo 5 cặp tại IBKR SIM) chỉ là fact hình học tick — CẤM
  suy ra executable spread/all-in; two-sided NOT_SUBSCRIBED, commission
  NOT_RUN ⇒ all-in CHƯA ĐO. Ngưỡng P3-A ≤0.41 pip đã pin không re-derive.
- Tái chạy cùng panel Dukascopy cũ với cơ chế cùng skeleton/payer = F-0 kill
  ngay; không được gọi là discovery.

## 6. Council, trial freeze, và luật multiple-testing (chống backtest overfitting)

### 6.1 Council outcome-blind (mỗi pair-child)

Kế thừa nguyên văn roster `PLAN_erp_forex_program_v1.md` §5: A1 controller;
PIT/data auditor (FAIL ngay nếu leak, không xem PnL); economic skeptic
(VETO pre-PnL tại F-0); cost/execution auditor (BLOCKED khi thiếu nguồn);
blind proposers P1..Pn (packet phi-outcome); independent reproducer/A7
(không kế thừa verdict implementer; REFUSED = remediation arc). Mỗi lane:
dispatch packet + worktree đúng registry + handoff `zcode_orch_v3_handoff@1`
tại đúng `handoff_path`.

### 6.2 Trial freeze (≤3 identity/pair, trước mọi PnL)

Umbrella §5.2 giữ nguyên: một pair-child freeze tối đa 3 identity; mỗi
identity 1 anchor + ≤2 neighbour + 1 causal control + 1 inverted control +
1 baseline (beta-matched per pair; FX thêm short-beta/carry-beta theo pair)
= 4–6 cells/identity. Không grid, không blend, không per-pair tuning.
Freeze pin nguyên văn danh sách PIT/intrabar SRLV §3 (thuật toán mức +
digest; pivot confirm ≥1 bar; fill open bar t+1 quote ngược chiều; CẤM thứ
tự high/low trong bar — không tách được ⇒ `NOT_CONSTRUCTIBLE_INTRABAR`;
cấm same-day statistic P-18; panel-truncation byte-identical + future-
mutation + independent implementation; delay-pair Q-4 cho sub-hour;
dry-run exact-arm non-vacuous + leak-scan).

### 6.3 Multiple-testing law (mở rộng P-9/P-11 theo owner instruction)

1. **Observed vs published** tách bạch (P-9): mọi kết quả scientifically
   computed vào observed denominator kể cả khi publication fail.
2. **DSR tại mọi terminal** tính trên TOÀN BỘ trial ledger của PWS đến thời
   điểm, với N_eff = max(số scored trials, số identity đã score, số frozen
   identity khác nhau đã xem outcome) VÀ **phải công khai N_registry** (số
   identity đã đề xuất ≤ 100) như cỡ không gian tìm kiếm (Harvey–Liu–Zhu:
   deflation theo vũ trụ search, không chỉ theo số lần bấm máy). Phạm vi:
   denominator DSR là trial ledger CỦA PWS; các ancestor trial của program
   trước (V14 N=146, EURUSD 48, FX-MAJORS 96…) không nằm trong ledger PWS
   nhưng phải được disclose cùng bảng (cross-program totals P-9) — dùng làm
   bối cảnh base rate, không cộng vào N_eff của PWS. Per-period series
   persist (P-11).
3. **PBO** chỉ khi cấu trúc frozen ≥8 configs; else `NOT_RUN` (fail-closed).
4. **Smoke/dry-run kill-được, không select-được** (P-15), không vào
   denominator.
5. Kết quả âm và rerun khoa học ghi observed ledger; không có headline PnL
   nào được dùng để chọn pair/identity/cửa sổ (chống cherry-pick: thứ tự
   pair §3.2, sealed §8, transfer one-look §8).

### 6.4 Kill rules (preregistered; bắn bất kỳ cái nào = terminal cho identity)

Kế thừa nguyên văn SRLV §10: **K-F0** skeptic VETO tại F-0; **K-ANC** ancestry
|rho| > 0.20 trên frozen representation hoặc trúng class veto; **K-PIT** lỗi
§3/truncation/future-mutation/delay-1; **K-COST** ceiling âm hoặc cost
auditor BLOCKED thiếu thành phần trọng yếu; **K-CTRL** clock/placebo tái tạo
≥0.5× anchor, inverted out-earn anchor (— không được đọc ngược thành signal,
LESSON P-28), baseline bị beat thiếu biên ≥2×; **K-VOL** vol-state fail
incrementality; **K-CONC** top fold/contribution > 50%; **K-POWER** dưới
floors; **K-OOS** sealed one-look fail ⇒ terminal, không rescue, không thử
cặp/window khác; **K-THIN** occupancy floors fail ⇒ NOT_RUN_THIN.

## 7. Hợp đồng cost & luật crypto (tách lớp bằng chứng, fail-closed)

Kế thừa nguyên văn SRLV §7 + DATACOST matrix §3:

- **FX measured book**: event-time session/rollover spread curve tại
  fill-bar × k ∈ {1.0,1.5,2.0}, sha-pinned census per pair; spread giãn lúc
  phá mức lấy theo PHÂN PHỐI FILL của cơ chế (Q-2/Q-8). Commission/slippage
  = DECLARED_UNMEASURED tới R1; financing structural-zero bằng force-flat
  fixture; multi-day chỉ khi R3. Ceiling âm ⇒ VETO trước scoring (K-COST).
  Mọi verdict FX mang `PAPER_TIER + SINGLE_SOURCE_PANEL +
  FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK`.
- **CX**: funding = MEASURED per-settlement path (native, while held; dual
  book với frozen constant; funding-path stress 24.7% settlements âm trong
  downtrend, worst −0.30%/8h ≈ 2.5 fee RT); fee 5 bps + 1 adverse tick =
  DECLARED book (từ CHR3F; lên lớp measured chỉ khi validate vs fills);
  spread census theo giờ fill từ bookTicker/aggTrades (coverage verify;
  thiếu ⇒ BLOCKED); gap/outage/latency = DECLARED bands + ×1.5/×2.0;
  maker-only CẤM tới khi queue-position đo được; levered/borrow/
  liquidation-model BLOCKED ⇒ mọi arm unlevered 1x.
- **Nhãn bắt buộc CX**: `PROXY_NOT_ORDERBOOK` cho mọi cơ chế sweep/zone/
  absorption trên klines; `SINGLE_VENUE_PANEL`; `FUNDING_PATH_STRESSED`;
  `FILL_QUALITY_CLASS_<measured|declared>`; fictional-counterparty veto cho
  mọi payer story không encode được bằng observable PIT hợp pháp.
- **15m/1m cùng giai đoạn giá đã outcome-exposed ở 1h** =
  `ANCESTRY_EXPOSED_RECLK` — chỉ dùng làm `ANCESTRY_EXPOSED_DEV`
  (kill/engineering), KHÔNG BAO GIỜ OOS (Q-3). OOS thật của CX khi history
  hết sạch = prospective accumulation sau freeze.

## 8. Sealed OOS, replication, transfer (one-look law)

- S1 program-wide `SEALED_UNTOUCHED`; sealed OOS per-identity MỘT LẦN sau
  GO riêng, membership sha-frozen trước pass; arm chết không được nhìn
  holdout (umbrella §5.10; Q-9 seal criteria lẫn data lẫn thresholds).
- FX sealed assets: AUDUSD + USDCAD 2026-H1 (`SEALED-UNREAD`) — **một cửa
  sổ transfer = MỘT look cấp chương trình** (matrix L5): window của cặp
  transfer chỉ được tiêu một lần bởi MỘT identity trong toàn chương trình.
- Replication sang pair khác: chỉ với identity đã freeze (qua đủ dev gates
  trên home pair) + evaluation pass duy nhất trên toàn window với identity
  frozen; đủ cả 3 limb R5 (impl độc lập / thời gian chưa dùng để chọn /
  bề mặt độc lập). Thiếu limb ⇒ không viết "replicated".
- Không dùng cùng thời gian để vừa chọn vừa xác nhận — sélection trên dev,
  xác nhận trên sealed/prospective, không chồng lấn.

## 9. Điểm dừng / stop conditions (fail-safe)

Kế thừa SRLV §11, cộng luật pair:

- (a) 2 pair-child LIÊN TIẾP của MỘT track đóng REJECT_ALL/slate rỗng ⇒
  viability council của track; không pair mới khi không có observable/
  nguồn/giả thuyết payer mới CÓ BẰNG CHỨNG (owner note cohort-2 nguyên văn).
- (b) hết data authority (mọi nguồn §3/§5 blocked, owner chưa mở);
- (c) sealed map trống (crypto: chỉ còn prospective);
- (d) power không đạt với ngân sách còn lại;
- (e) hết cap amendment (cells/identity/pair) — gia hạn chỉ bằng owner
  decision mới;
- (f) một pair-child vượt 14 ngày lịch mà không qua gate kế tiếp ⇒ time-stop,
  báo owner, không treo;
- (g) registry đạt 100 identity ⇒ proposer space đóng (scoring tiếp diễn).
- Kết luận `NO_CANDIDATE` (đã tìm trong không gian được cấp quyền) hoặc
  `BLOCKED_<class>` — cả hai đều thành phẩm (Q-16).

## 10. Chuỗi GO và GO phrase (gõ đúng chữ tại đúng gate; P-8)

| Gate | Hành động được phép sau GO | GO phrase (mẫu theo pair) |
|---|---|---|
| Charter approval | ghi quyết định owner vào OWNER_PACKET + duyệt amendment (không cần registry row — umbrella là cycle quản trị) | quyết định ghi, không phrase |
| **GO-1 (CX pair đầu = SOLUSDT theo đề xuất)** | register child + council + data gate + falsifiers + trial freeze — RỒI DỪNG | `GO PWS CX SOLUSDT C1 COUNCIL AND FREEZE` |
| **GO-2 (CX)** | scored dev walk-forward dưới heavy lock | `GO PWS CX SOLUSDT C1 SCORED EXECUTION` |
| **GO-3 (CX)** | sealed/prospective OOS one-look + replication MỘT LẦN | `GO PWS CX SOLUSDT C1 SEALED OOS AND REPLICATION` |
| GO-1/2/3 (CX pair kế) | như trên, thay tên pair (BNBUSDT, BTCUSDT, ETHUSDT) | `GO PWS CX <PAIR> C1 …` |
| GO-1/2/3 (FX) | chỉ có hiệu lực khi reopener §5 có bằng chứng bytes | `GO PWS FX <PAIR> C1 …` |

A7 prelaunch đứng giữa GO-1→GO-2 và sau dev trước GO-3 (forex-program §8).
Sau mỗi pair-child: A7 terminal fresh-context + two-half close (registry +
P-9 ledger + IDENTITY_REGISTRY status + FAMILY_FAILURES/MAP/LESSONS + errata
P-19). Shadow promotion / nguồn mới / slate change / mở S1 program-wide =
owner decision riêng ngoài chuỗi trên. **Prompt 2026-09-26 KHÔNG PHẢI GO nào
cả.**

## 11. Artifacts & nhãn terminal

Per pair-child: council reports + handoffs, data-gate verdict per pair (kể
cả BLOCKED rows), falsifier battery (F-0…F-7), freeze artifact (membership,
arm digests, thresholds, seeds, pins — sha256), dry-run, scored cells +
margin-to-fail, seam/kill-law files, DSR (per-period series persisted), repro
twin, A7 prelaunch + terminal, trial_ledger.jsonl, CYCLE_VERDICT.md.
Program-level: IDENTITY_REGISTRY.jsonl (§2). Terminal vocabulary: umbrella
§9 + `NO_CANDIDATE` + `BACKTEST_CANDIDATE_REPLICATED` (paper-tier bound,
7/7 R0–R6). Mọi verdict âm là first-class close.

## 12. Quyết định owner đang chờ

Xem `research/control/PWS-PROGRAM-V1/OWNER_PACKET_program_open_2026-09-26.md`
(Q1 phê chuẩn charter; Q2 duyệt amendment caps; Q3 thứ tự pair + pair đầu;
Q4 FX reopeners R1/R2/R3 hoặc giữ NO_CANDIDATE; Q5 GO phrase đầu sẽ gõ tại
gate của nó).
