# PLAN (DRAFT) — DAYTRADE-PLAYBOOKS-PROGRAM-V1 — Master plan: chương trình nghiên cứu day-trading playbook theo từng pair (Forex + Crypto), độc lập với shadow đang chạy

> **Status: `DRAFT_FOR_OWNER_DECISION — NOT REGISTERED, NOT EXECUTED.** File
> này không đăng ký cycle, không spawn worker/lane, không download, không mở
> S1/sealed holdout, không đụng shadow/daemon/dashboard/worker, không đặt
> lệnh, không tiêu GO nào. Nó nằm DƯỚI umbrella `ECONOMIC-ROBUSTNESS-PROGRAM-V1`
> (ACTIVE_LIGHT trong registry) — kế thừa toàn bộ luật umbrella §§1–11, charter
> `ERP-FOREX-PROGRAM-V1` (R0–R6, roster §5, reopening law R1–R5), luật
> `SRLV-PROGRAM-V1` (F-0 court, PIT §3, kill rules §10, stop conditions §11)
> và luật identity/pair-order của `PWS-PROGRAM-V1` (§2, §3) trừ khi child chặt
> hơn. Owner phê chuẩn charter này bằng quyết định ghi vào
> `research/control/DAYTRADE-PLAYBOOKS-PROGRAM-V1/GO1_OWNER_PACKET.md`.
>
> Authored 2026-09-27 bởi Lead từ owner instruction (verbatim intent: lập
> cycle mới nghiên cứu **day-trading playbooks theo từng pair Forex và crypto,
> làm việc độc lập với các shadow strategy đang chạy**; mục tiêu là cơ chế
> intraday định nghĩa được, PIT, trừ đủ chi phí, tái lập được; `NO_CANDIDATE`
> là kết quả hợp lệ. Đổi pair/timeframe/session/filter KHÔNG PHẢI strategy
> mới. Forex chỉ được score khi có reopener dữ liệu/chi phí đúng luật; crypto
> không được gọi hình dạng nến là order flow hay thanh khoản L2. Bàn giao đầu
> tiên dừng tại GO-1 — chưa đăng ký/chạy scored, chưa mở OOS, chưa đụng
> worker/dashboard/shadow/lệnh.)

## 0. Program identity

```text
program_id    DAYTRADE-PLAYBOOKS-PROGRAM-V1 (master layer; scored cells = 0/0 —
             không bao giờ tự score; mọi scored surface thuộc child pair-cycle)
parent        ECONOMIC-ROBUSTNESS-PROGRAM-V1 (umbrella, luật chung §§1–11)
sibling-law   ERP-FOREX-PROGRAM-V1 (R0–R6, roster §5, reopening R1–R5),
              SRLV-PROGRAM-V1 (F-0 court, PIT §3, K-* kill rules, §11 stops),
              PWS-PROGRAM-V1 (identity registry §2, pair-order §3, crypto fences §7)
tracks        DTP-CX (SOLUSDT → BTCUSDT → ETHUSDT → BNBUSDT — Binance USDⓈ-M
              perp; frontier F2 của DATA-FOUNDATION: READY với dead-set dày)
              DTP-FX (DORMANT — AUDUSD → USDCAD khi có reopener R1/R2/R3/R5;
              EURUSD/GBPUSD/USDJPY chỉ ancestry/fixture/cost authority;
              USDCHF BLOCKED_DATA_LICENSE)
ceiling       ≤ 60 strategy identity ID toàn chương trình (TRẦN KHẢO SÁT của
              proposer space — không phải chỉ tiêu; xem §2). Mọi kill pre-PnL
              là tiết kiệm cells/OOS, không phải waste.
budget cap    CX: ≤18 scored cells/pair-child, ≤72 program. FX: 0 cho tới khi
              reopener có bytes (amendment mở ≤18/pair, ≤36 program sau đó).
              Hiệu lực khi owner duyệt tại GO-1 packet (P-8).
goal          ≥1 strategy identity đạt BACKTEST_CANDIDATE_REPLICATED (đủ 7/7
              R0–R6 của forex-program charter, điều kiện R4 thay bằng
              sealed-HOẶC-prospective one-look tùy track — §8) trên ≥1 pair,
              HOẶC kết luận NO_CANDIDATE / BLOCKED_<class> đúng gate
ledger        per-child trial_ledger.jsonl (append-only) + IDENTITY_REGISTRY
              program-level (§2) + P-9 denominators; mọi outcome-viewed
              pair/timeframe/parameter = 1 trial row
S1            SEALED_UNTOUCHED ở mọi nơi; sealed/prospective OOS per-identity
              một lần, sau GO riêng
orders        NONE — mọi kết luận paper/backtest tier; shadow/live là GO riêng
stops         §9 (2 pair-child liên tiếp của một track đóng trống/REJECT_ALL ⇒
              viability council; hết giả thuyết mới / hết data authority / hết
              OOS sạch / hết power / hết ngân sách ⇒ dừng đúng gate)
```

## 0.1 Phase-0 intake snapshot (đo lúc soạn draft 2026-09-27; A7-F4)

- Root `/Users/hoangminhlong/my-quantitative`, branch `main`, HEAD
  `96d65aaedcd0555d8a036ce23fd93244fef0b3e7`; 3 file draft này untracked;
  không có row DTP nào trong `plans/CYCLE_REGISTRY.json`.
- Heavy lock `FREE_PROVEN` (không holder, không flock; history cuối =
  SRLV-CX-C1 GO-2 đã FINISHED 2026-09-26T09:31Z). Không worker nặng chạy.
- 10 cycle ACTIVE_LIGHT lân cận (PROSPECTIVE-SHADOW-V1, LIVE-DATA-GATEWAY-V1,
  CRYPTO-HISTORICAL-REPLICATION-3F-V1, FX-RANGEFADE-2M-SHADOW-V1,
  ILLIQ-LOSS-MECH-V1, SHADOW-PAPER-REVIEW-V1, ETHUSDT-OPEN-SEARCH-V2,
  ECONOMIC-ROBUSTNESS-PROGRAM-V1, ERP1-TRACKB-COHORT-1 terminaled ngày
  2026-09-26, STOCKS-SEARCH-V1 BLOCKED) — mọi điều tra read-only, danh sách
  re-measure tại G1 của child theo luật F7-DFV1.
- Doctor: mọi finding HIGH đều `FROZEN_ARTIFACT_DRIFT` trên pause/close packet
  của các cycle TERMINAL cũ (CRYPTO-V17/FOREX-FREE-V8/STOCKS-FREE-V12 —
  worktree đã dọn); không blocker nào cho cycle mới, tiền lệ ghi nhận.
- Disk: **6.2 GiB free** (`df -h /`, đo 2026-09-27) — ràng buộc §3.4.
- DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1 TERMINAL 2026-09-26 (91 authority rows
  VALID; F1 stocks READY-PARTIAL / **F2 crypto READY** / F3 FX BLOCKED-R1) —
  nguồn các bảng dữ liệu của chương trình này.

## 1. Mục tiêu / không-mục-tiêu

### 1.1 Mục tiêu

Nghiên cứu **mechanism-first theo từng pair** các *day-trading playbook* —
tập hợp cách giao dịch intraday mà day trader thực sự dùng (taxonomy đóng băng
§4) — dưới luật falsification-first của umbrella: council outcome-blind,
falsify TRƯỚC PnL, score dưới cost book đo được/declared đúng lớp, bảo toàn
sealed OOS, replication độc lập. Không gian đề xuất RỘNG (≤60 identity), không
gian score HẸP (≤3 identity frozen/pair; đa số proposal bị F-0/F-1 giết
pre-PnL). Chuẩn không hạ: `REJECT_ALL` / `NO_CANDIDATE` / `BLOCKED_<class>`
hợp lệ và theo base rate đo được là kết quả modal (ERP1-TA-C2 7/7 chết
pre-PnL; SRLV 3/4 veto + 1/1 chết dev gates; EURUSD open-search 1/48
gate-eligible rồi fail holdout; DSR V14 0.00224 N=146).

### 1.2 Không-mục-tiêu (hard)

- **Đổi pair/timeframe/session/filter KHÔNG PHẢI strategy mới** (owner law
  2026-09-27; LESSON P-29 pair-swap opens nothing; Q-3 re-clock; P-27 adding
  an observable is not a new mechanism). Anti-variant law §2.3 binding.
- Không cứu bất kỳ family nào trong `research/wayfinder/FAMILY_FAILURES.jsonl`
  (137 entries) bằng rename/đảo dấu/đổi filter/đổi window/đổi cadence.
- Crypto: **CẤM gọi hình dạng nến/level trên klines là order flow, thanh
  khoản L2, hay liquidation** — mọi cơ chế sweep/zone/absorption trên klines
  mang nhãn `PROXY_NOT_ORDERBOOK` + `SINGLE_VENUE_PANEL` và qua
  fictional-counterparty veto (SRLV §7; DATA-FOUNDATION OWNER_DIRECTIVE
  prohibition; không có L2/liquidation/OI lịch sử đa-năm —
  `BLOCKED_UNCONSTRUCTIBLE`).
- Forex: **KHÔNG pair FX nào được score khi chưa có reopener R1/R2/R3/R5 với
  bằng chứng bytes + license + cost authority đo được** (PWS §5 kế thừa
  nguyên văn; VIABILITY 2026-09-26: 0/12 class sống sót, sàn 3.6/4.4 pip
  stressed RT chia đôi không gian zero remainder).
- Không đụng shadow/worker/dashboard đang chạy (FX-RANGEFADE-2M-SHADOW-V1,
  PROSPECTIVE-SHADOW-V1, ILLIQ-LOSS-MECH-V1, LIVE-DATA-GATEWAY-V1,
  DASHBOARD-AND-SHADOW-RELIABILITY-V1, SHARED-PORTFOLIO-100K-V1,
  **CRYPTO-HISTORICAL-REPLICATION-3F-V1 (scored execution dưới heavy lock),
  SHADOW-PAPER-REVIEW-V1**): read-only về dữ liệu công khai của chúng, không
  restart/sửa/đọc trạng thái nội bộ. Không tiêu GO phrase hay surface S1 của
  `ETHUSDT-OPEN-SEARCH-V2` (ACTIVE).
- Không dùng chart đã biết kết quả để vẽ lại entry; nguồn trader/video/
  journal phải ghi nguồn + thời điểm công bố (§4.3). Không grid tham số,
  không parameter rescue sau khi PnL xuất hiện, không hạ gate/nới power.
- Không claim live-readiness; pass backtest ≠ shadow ≠ giao dịch thật.

## 2. Identity registry — luật trần 60 identity

### 2.1 ID và vòng đời

- ID `DTP-<TRACK>-<PAIR>-I<NNN>` (vd `DTP-CX-SOLUSDT-I001`), cấp khi vào
  registry, không tái sử dụng. Registry:
  `research/control/DAYTRADE-PLAYBOOKS-PROGRAM-V1/IDENTITY_REGISTRY.jsonl`
  (append-only, tạo khi charter được duyệt, 0 rows khi mở). Row schema như
  PWS §2.1: `{schema: dtp/identity@1, id, track, pair, playbook_class,
  proposed_by_lane, date_utc, payer, premium, information_layer, cost_class,
  falsifier, status, status_date, evidence_paths[]}` (thêm `playbook_class`
  trỏ tới dòng taxonomy §4).
- Status một chiều: `PROPOSED → F0_KILLED | FREEZE_ELIGIBLE → FROZEN → SCORED
  → <verdict> | DEFERRED | WITHDRAWN_BY_OWNER`. Kill là asset (Q-16), không
  xóa không sửa. Trần 60 = tổng row ≠ `WITHDRAWN_BY_OWNER`; đạt trần ⇒
  proposer space đóng, scoring identity đã frozen tiếp tục theo GO riêng.

### 2.2 Điều kiện vào registry

Đủ 10 trường umbrella §5.3 (payer/premium/persistence/risk transferred/
observable + availability evidence/holding horizon/capacity/costs
decomposition/falsifier + controls) VÀ trả lời 3 câu F-0 court (SRLV §2.3):
(1) **skeleton test** — bỏ mechanism-specific observable, giữ
trigger/direction/exit shape, còn edge không? cùng shape = cùng family chết;
(2) **payer test** — ai trả, vì sao họ BẮT PHẢI trả, tự arbitrage đi không;
(3) **information test** — thông tin gì chưa có trong clock/trend/spread
(Q-7). Skeptic VETO pre-PnL tại F-0.

### 2.3 Anti-variant law (nguyên văn PWS §2.3)

Hai proposal là MỘT identity (⇒ `F0_KILLED VETO_VARIANT_SAME_FAMILY`) nếu chỉ
khác nhau bởi: rename; đảo dấu/invert; thêm/bớt filter/gate observable trong
khi trigger/direction/exit shape và payer giống; đổi timeframe/cadence của
cùng lịch sử giá (re-clock Q-3); **đổi session/đổi pair giữ nguyên skeleton**.
Hai identity khác nhau phải khác ít nhất HAI trong ba: (a) payer và cơ chế ép
trả tiền; (b) information layer PIT (nguồn + observable); (c) risk shape
(holding horizon, direction logic, risk transferred).

## 3. Kiến trúc pair-by-pair (binding)

### 3.1 Một pair — một child cycle

Mỗi pair là child cycle riêng (`DTP-CX-SOLUSDT-C1`, `DTP-FX-AUDUSD-C1`, …)
với plan child riêng (draft khi đến lượt pair), worktree/branch theo registry,
trial_ledger riêng, cost book theo track, GO phrase riêng, verdict riêng.
Hai track không trộn ledger/cost book/verdict/GO phrase.

### 3.2 Thứ tự pair freeze tại GO-1 — trước MỌI PnL của chương trình

Thứ tự đăng ký tại charter approval (GO-1 packet Q3); đổi thứ tự = owner
amendment. Pair tiếp theo chỉ bắt đầu sau khi pair trước A7 terminal +
two-half close. Không quá MỘT pair-child ở giai đoạn scored tại một thời điểm
(heavy lock enforce). Proposal drafting (outcome-blind, không chạm data) được
tích lũy vào registry mọi lúc; council/data gate/scoring chỉ mở khi đến lượt.

**Đề xuất mặc định (owner duyệt/sửa tại GO-1 packet Q3):**

- **CX: SOLUSDT → BTCUSDT → ETHUSDT → BNBUSDT.**
  - SOLUSDT đầu: plane đã verify (klines 1h 2020-09..2026-08 gapless
    floor-exact; funding 6,580 settlements bit-exact; **spread census ĐO
    p50 0.469 bps** — PWS-CX-SOLUSDT durable assets tái dùng); ancestry mỏng
    nhất cho class price-level intraday (chỉ `OUTCOME_EXPOSED_baseline`);
    gate dữ liệu rẻ nhất (staging 1m/15m trong ngân sách disk §3.4).
  - **Công khai bắt buộc (A7-F2):** PWS-CX-SOLUSDT-C1 và PWS-CX-BNBUSDT-C1
    (chương trình anh em, observable funding-run) đều đã đóng
    `NO_ELIGIBLE_PROPOSAL` 0/18 và stop-rule PWS §9(a) ĐÃ BẮN (2 pair-child
    liên tiếp trống slate ⇒ viability council bắt buộc). Cơ sở pháp lý để
    chương trình này mở pair-child trên SOL là owner Q1 ở GO-1 packet —
    quyết định rằng **taxonomy playbook price-level/session + lớp annotation
    mù outcome là "observable/giả thuyết payer mới CÓ BẰNG CHỨNG"** mà note
    A7/A1 của PWS đòi hỏi — KHÔNG phải sự tiếp nối ngầm của PWS. Nếu owner
    từ chối định nghĩa đó, pair đầu CX chuyển sang pair chưa từng mở child
    theo thứ tự (BTCUSDT) hoặc track đóng DORMANT như FX.
  - BTCUSDT: cost authority dày nhất (funding measured 11.798%/yr; fee
    declared 5bps+1tick frozen CHR3F; 15m catalog 2024-08+ đã stage) NHƯNG
    spread census bookTicker NOT_RUN + ancestry dày nhất + **G5 fold-conc
    0.50 structurally unpassable cho long-biased 2020-2026** ⇒ cơ chế phải
    two-sided hoặc prospective-only.
  - ETHUSDT: như BTC + VA CHẠM `ETHUSDT-OPEN-SEARCH-V2` (ACTIVE) — không tiêu
    GO/S1 của cycle đó, không re-stage corpus của nó (OUTCOME_EXPOSURE_MAP
    §2.1 precedent).
  - BNBUSDT cuối: spread census `NOT_RUN_DISK_CONSTRAINT` (cần 25GB, disk
    6.1GiB) ⇒ BLOCKED cho tới khi disk đỡ hoặc census cửa sổ hẹp được duyệt
    bởi cost auditor như measured-band có giới hạn công bố.
- **FX: DORMANT toàn track cho tới khi reopener §5 có bytes.** Thứ tự đóng
  băng sẵn khi mở: AUDUSD → USDCAD (chỉ hai pair có dev-cho-observable-mới +
  sealed 2026-H1 còn nguyên); EURUSD/GBPUSD/USDJPY KHÔNG BAO GIỜ dev/OOS
  (outcome-exposed trọn window — chỉ ancestry/fixture/cost authority);
  USDCHF BLOCKED_DATA_LICENSE (chỉ R4 sau khi một identity qua dev gates).
  Nếu R2 (nguồn độc lập) mở: pair đầu = pair có corpus nguồn-mới đầy đủ sớm
  nhất (PWS §3.2 precedent).

### 3.3 Per-pair gate (GO-1 của child; không score-all)

Data probe/census/DST/rollover/scale fixtures, license posture từng nguồn,
PIT seam check, cost census (spread theo giờ fill; crypto: funding dual-book
+ fee declared + spread census + **quote (bookTicker) / trade (aggTrades) /
mark & index per contract — coverage-verify từng loại, thiếu ⇒ BLOCKED**),
power analysis tại freeze. Mọi identity khai bề mặt đo của chính nó: cơ chế
dùng "chưa adjust/độ trễ quote" phải chỉ định series đo độ trễ đó và series
phải qua gate — không series hợp lệ ⇒ identity vào F-0 với `BLOCKED_DATA`,
không thay bằng proxy (A7-F1).
Baseline: `research/control/SRLV-PROGRAM-V1/DATACOST_FEASIBILITY_MATRIX.md`
kế thừa; child re-verify bằng bytes tại GO-1 của mình. Cặp thiếu nguồn hợp lệ
⇒ `BLOCKED_<reason>` ghi freeze artifact; KHÔNG âm thầm thay cặp.

### 3.4 Ràng buộc disk (hard, đo `df -h /` 2026-09-27: 6.2 GiB free — A7 đo
lại cùng ngày 6.2; con số pinned kèm timestamp, re-measure trước mỗi staging)

Mọi staging mới của child ≤0.5 GB; abort mọi acquisition nếu free <5.0 GiB
(`BLOCKED_STORAGE`, luật DFV1 §8). BNB spread census toàn-history (cần ~25GB)
stay BLOCKED. Staging 1m/15m của một pair = data gate riêng, manifest sha
bắt buộc, xóa tail theo luật P-13 archive-then-delete.

## 4. Taxonomy-first law (đặc thù của chương trình này)

### 4.1 Taxonomy đóng băng TRƯỚC council

`research/control/DAYTRADE-PLAYBOOKS-PROGRAM-V1/PLAYBOOK_TAXONOMY.md` là
artifact freeze tại GO-1: mọi playbook day-trader thường dùng được liệt kê,
định nghĩa theo **quantifier xây được từ bar đã đóng**, và đối chiếu NGAY với
family đã chết (bảng collision). Council của pair-child chỉ được đề xuất:
(i) một playbook có sẵn trong taxonomy (kèm phán quyết collision của nó), hoặc
(ii) một skeleton MỚI phải tự chứng minh qua F-0 rằng không trùng shape nào
trong bảng chết. Không có "playbook mới" ngoài taxonomy mà không qua F-0.

### 4.2 Quy tắc định nghĩa mức/giờ (PIT, áp dụng mọi identity)

Kế thừa nguyên văn SRLV §3: mức giá chỉ định nghĩa từ **bar đã đóng**; pivot/
level phải chờ confirm ≥1 bar; lệnh sớm nhất ở **quote có thể giao dịch sau
khi tín hiệu đã biết** (bar tín hiệu đóng → fill ở quote bar kế tiếp; fill
open bar t+1 theo quote ngược chiều); **CẤM same-bar fill dựa vào thứ tự
high/low trong bar** (không tách được ⇒ `NOT_CONSTRUCTIBLE_INTRABAR`); cấm
same-day statistic (P-18); panel-truncation byte-identical + future-mutation
+ delay-pair Q-4 cho sub-hour; dry-run exact-arm non-vacuous + leak-scan.
News/event: `available_at` THẬT từ nguồn có authority + xử lý revision;
thiếu ⇒ `BLOCKED_DATA`, không thay bằng proxy rồi khẳng định cơ chế gốc.

### 4.3 Luật nguồn trader (annotation-first cho discretionary)

Ví dụ từ trader/video/trade journal: ghi **nguồn + thời điểm công bố**; CẤM
dùng chart đã biết kết quả để vẽ lại entry "đẹp". Muốn nghiên cứu hành vi
discretionary: xây **bộ annotation mù outcome trước khi score** — annotator
không thấy tương lai của bar sau điểm annotation; bộ annotation có manifest
(nguồn, ngày công bố, rule codify, phiên giao dịch, mù outcome checklist);
mọi rule codify từ annotation vẫn chịu F-0/anti-variant/collision như mọi
identity — annotation không phải giấy thông hành.

## 5. Frontier law — DTP-FX (kế thừa PWS §5 nguyên văn, binding)

Forex đang `NO_CANDIDATE` trên frontier được cấp quyền (VIABILITY 2026-09-26:
12 classes enumerated, 0 survive; sàn chi phí 3.6/4.4 pips stressed RT chia
đôi không gian zero remainder; P3-A đo chết tại tick geometry). **Không pair
FX nào được score khi chưa có MỘT reopener dưới đây với bằng chứng bytes +
license + cost authority đo được tại GO-1 của child:**

| Reopener | Bằng chứng cần | Mở gì |
|---|---|---|
| **R1** broker cost authority | two-sided market-data subscription + Flex statement (commission + overnight interest measured) | all-in được ĐO; cơ chế chết F-5 chỉ xét lại bằng số đo |
| **R2** nguồn bid/ask độc lập | TrueFX / OANDA v20 practice / Dukascopy written consent (owner action) + bytes on disk + license PASS + cross-source PIT seam check | nguồn thứ hai cost authority; window outcome-free; limb replication nguồn-độc-lập |
| **R3** financing band | broker-grade swap data cited | class multi-day hold / carry (đang BLOCKED NG6/NG7 F4) |
| **R5** information layer mới | artifact có authority (không-PnL) | observable mới qua D2 |

Không reopener ⇒ pair-child FX đóng `BLOCKED_FRONTIER_NOT_REOPENED`, 0 scored
cell, 0 holdout look — kết quả đúng, không phải thất bại (Q-16). Tái chạy
panel Dukascopy cũ với skeleton/payer đã chết = F-0 kill ngay. minTick 0.5
pip chỉ là fact hình học tick — CẤM suy ra executable spread/all-in.

## 6. Council, trial freeze, multiple-testing

### 6.1 Roster (owner-required lanes; kế thừa ERP §5)

| Lane | Vai trò | Được thấy | Bị cấm | Quyền đặc biệt |
|---|---|---|---|---|
| A1 | Controller/ghi sổ | state, freeze, ledger | tự đề xuất cơ chế | — |
| **Playbook collector/definer (P1..Pn)** | thu thập/định nghĩa playbook từ taxonomy + nguồn trader (§4.3), đề xuất theo schema §5.3 | packet phi-outcome + taxonomy + nguồn dated | mọi outcome surface | proposals only |
| **Economic skeptic** | phản biện payer/premium/persistence/ancestry/controls; đo ancestry rho trên frozen representation | proposals + failure memory + dữ liệu phi-outcome | viết strategy code | **VETO pre-PnL (F-0)** |
| **PIT/data auditor** | timestamp từng feature/event; DST/bar close/as-of join; truncation + future-mutation fixtures | code + data planes + fixtures | MỌI PnL/outcome | FAIL ngay nếu leak |
| **Cost/execution auditor** | bid/ask, phí, funding, spread theo phiên/sự kiện, gap/no-fill, ceiling 1×/1.5×/2× | cost censuses, fill laws, planes | điền giả định lạc quan | **BLOCKED** khi thiếu nguồn |
| **Scorer** | chạy scored cells dưới heavy lock từ freeze đã pin | freeze + engine | sửa freeze/tham số sau khi thấy PnL | — |
| **A7 reproducer** | impl độc lập, recompute, audit freeze/gates; plan review + prelaunch + terminal | artifact machine + (outcome chỉ đúng giai đoạn được phép) | kế thừa verdict implementer | REFUSED = remediation arc |

Không một lane nào vừa đề xuất, vừa score, vừa tự duyệt. Mọi lane nộp
PASS/FAIL/NOT_RUN + đường dẫn bằng chứng + handoff `zcode_orch_v3_handoff@1`
tại đúng `handoff_path` của dispatch packet; Lead tổng hợp bất đồng — không
bỏ phiếu ghi đè FAIL.

### 6.2 Trial freeze (≤3 identity/pair, trước mọi PnL)

Một pair-child freeze tối đa 3 identity; mỗi identity 1 anchor + ≤2 neighbour
+ 1 causal/placebo control + 1 inverted control + 1 baseline set (beta-matched
per pair; FX thêm short-beta/carry-beta theo pair) = 4–6 cells/identity.
Không grid, không blend, không per-pair tuning rồi gọi là replication (mass
test ≠ mass selection — SRLV §8). Freeze pin nguyên văn §4.2 + SRLV §3.

### 6.3 Multiple-testing law

1. Observed vs published tách bạch (P-9); per-period series persist (P-11).
2. DSR tại mọi terminal trên toàn trial ledger của DTP; N_eff =
   max(scored trials, identity đã score, frozen identity khác nhau đã xem
   outcome); **công khai N_registry** (≤60) như cỡ không gian tìm kiếm;
   ancestor trials của program trước disclose làm base rate, không cộng N_eff.
3. PBO chỉ khi ≥8 configs; else NOT_RUN.
4. Smoke/dry-run kill-được không select-được (P-15), không vào denominator.
5. Không headline PnL nào được dùng để chọn pair/identity/cửa sổ.

### 6.4 Kill rules (preregistered; bắn một cái = terminal cho identity)

Kế thừa SRLV §10: **K-F0** skeptic VETO; **K-ANC** ancestry |rho| > 0.20 trên
frozen representation hoặc trúng class veto; **K-PIT** lỗi §4.2/truncation/
future-mutation/delay; **K-COST** ceiling âm hoặc cost auditor BLOCKED thiếu
thành phần trọng yếu (ceiling×power grid một dòng — P-29); **K-CTRL**
clock/placebo tái tạo ≥0.5× anchor, inverted out-earn anchor (KHÔNG đọc
ngược thành signal — P-28), baseline bị beat thiếu biên ≥2×; **K-VOL**
vol-state fail incrementality; **K-CONC** top fold/contribution > 50%;
**K-POWER** dưới floors (§6.5); **K-OOS** sealed/prospective one-look fail ⇒
terminal, không rescue, không thử cặp/window khác; **K-THIN** occupancy
floors fail ⇒ NOT_RUN_THIN.

### 6.5 Power floors (umbrella §5.14; child chỉ được nâng)

- FX intraday: ≥100 closed RT + ≥6 tháng; PF≈1.3 cần n≈236 (power analysis
  tại freeze). Crypto intraday (1m–15m): ≥100 closed RT + ≥2 vol regimes với
  occupancy floors (TWO-REGIME precedent 20/3/100); child freeze n riêng sau
  power analysis; sàn ≥100 RT. Mọi positive sub-power = INCONCLUSIVE.

## 7. Hợp đồng cost & luật crypto (fail-closed)

Kế thừa nguyên văn SRLV §7 + DATACOST §3:

- **CX**: mark & index per contract = gate bắt buộc (owner law 2026-09-27:
  "crypto cần quote/trade, phí, funding và mark/index đúng hợp đồng") — dùng
  cho funding accounting, funding-adjacent labels và mọi xác định giá không
  dùng last-trade; coverage-verify per contract, thiếu ⇒ BLOCKED. Fee =
  DECLARED book (taker 5 bps + 1 adverse tick, frozen từ
  CHR3F; lên lớp measured chỉ khi validate vs fills — Q-8); funding =
  MEASURED per-settlement path (dual-book với frozen constant; funding-path
  stress: 24.7% settlements âm trong downtrend, worst −0.30%/8h); spread =
  census theo giờ fill từ bookTicker/aggTrades (verify coverage; thiếu ⇒
  BLOCKED, không điền số đẹp — BNB precedent); gap/outage = DECLARED band +
  ×1.5/×2.0; maker-only CẤM tới khi queue-position đo được; levered/borrow/
  liquidation-model BLOCKED ⇒ mọi arm unlevered 1x. Nhãn bắt buộc:
  `PROXY_NOT_ORDERBOOK`, `SINGLE_VENUE_PANEL`, `FUNDING_PATH_STRESSED`,
  `FILL_QUALITY_CLASS_<measured|declared>`, `ANCESTRY_EXPOSED_DEV` (mọi dev
  trên 1m/15m — re-clock của plane 1h đã exposed; KHÔNG BAO GIỜ OOS).
- **FX**: spread event-time theo PHÂN PHỐI FILL của cơ chế × k∈{1.0,1.5,2.0}
  sha-pinned (Q-2/Q-8 — range-edge fade fill đúng lúc spread giãn, P3-A
  precedent); commission/slippage `DECLARED_UNMEASURED` tới R1; financing
  structural-zero bằng force-flat fixture; ceiling âm ⇒ VETO trước scoring.
  Nhãn: `PAPER_TIER + SINGLE_SOURCE_PANEL +
  FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK`.

## 8. Sealed OOS, replication, transfer (one-look law)

- S1 program-wide `SEALED_UNTOUCHED`; sealed/prospective OOS per-identity
  MỘT LẦN sau GO riêng, membership sha-frozen trước pass; arm chết không
  được nhìn holdout.
- **CX**: lịch sử mọi pair đã outcome-exposed ở 1h (và 15m re-clock) ⇒ dev
  chỉ `ANCESTRY_EXPOSED_DEV`; **OOS thật = prospective accumulation sau
  freeze** (trackb §4.2 precedent). GO-3 của CX là sealed-nếu-có (15m/1m
  window chưa từng score CHỈ TUYỆT ĐỐI KHÔNG dùng làm OOS — re-clock law)
  hoặc prospective, ghi rõ trong child plan.
- **FX**: sealed assets AUDUSD + USDCAD 2026-H1 (`SEALED-UNREAD`) — một cửa
  sổ transfer = MỘT look **cấp lineage, không chỉ cấp chương trình này**
  (A7-F5): khi một identity của DTP tiêu look, việc tiêu được ghi vào
  `OUTCOME_EXPOSURE_MAP` tại two-half close và cửa sổ cạn cho toàn bộ các
  chương trình anh em (PWS-successor gồm cả DTP); ngược lại look do chương
  trình khác tiêu trước cũng cạn với DTP. Replication đủ 3 limb
  R5 (impl độc lập / thời gian chưa dùng để chọn / bề mặt độc lập); thiếu
  limb ⇒ không viết "replicated".

## 9. Stop conditions (fail-safe)

(a) 2 pair-child LIÊN TIẾP của MỘT track đóng trống slate/REJECT_ALL ⇒
viability council của track, không pair mới khi không có observable/nguồn/
giả thuyết payer mới CÓ BẰNG CHỨNG (owner note cohort-2; PWS §9(a) precedent
đã từng bắn); (b) hết data authority; (c) sealed map trống (CX: chỉ còn
prospective); (d) power không đạt với ngân sách còn lại; (e) hết cap — gia
hạn chỉ bằng owner decision; (f) một pair-child vượt 14 ngày lịch không qua
gate kế tiếp ⇒ time-stop báo owner; (g) registry đạt 60 ⇒ proposer space
đóng. `NO_CANDIDATE` / `BLOCKED_<class>` đều là thành phẩm (Q-16).

## 10. Chuỗi GO và GO phrase (gõ đúng chữ tại đúng gate; P-8)

| Gate | Hành động sau GO | GO phrase (mẫu) |
|---|---|---|
| Charter approval (GO-1 packet) | duyệt charter + thứ tự pair + caps; ghi quyết định vào packet | quyết định ghi, không phrase |
| **GO-1 (CX pair đầu = SOLUSDT theo đề xuất)** | register child + council + data gate + falsifiers + trial freeze — RỒI DỪNG | `GO DTP CX SOLUSDT C1 COUNCIL AND FREEZE` |
| **GO-2 (CX)** | scored dev walk-forward dưới heavy lock | `GO DTP CX SOLUSDT C1 SCORED EXECUTION` |
| **GO-3 (CX)** | OOS one-look (sealed nếu có luật §8, không thì prospective) + replication MỘT LẦN | `GO DTP CX SOLUSDT C1 OOS ONE LOOK AND REPLICATION` |
| GO-1/2/3 (CX pair kế) | như trên, thay tên pair | `GO DTP CX <PAIR> C1 …` |
| GO-1/2/3 (FX) | CHỈ có hiệu lực khi reopener §5 có bằng chứng bytes | `GO DTP FX <PAIR> C1 …` |

A7 prelaunch đứng giữa GO-1→GO-2 và sau dev trước GO-3. Sau mỗi pair-child:
A7 terminal fresh-context + two-half close (registry + P-9 ledger +
IDENTITY_REGISTRY status + FAMILY_FAILURES/MAP/LESSONS + errata P-19).
Shadow promotion / nguồn mới / slate change / mở S1 = owner decision riêng.
**Owner instruction 2026-09-27 KHÔNG PHẢI GO nào cả — bàn giao đầu tiên dừng
trước GO-1 của pair đầu.**

## 11. Artifacts & nhãn terminal

Per pair-child: council reports + handoffs, data-gate verdict (kể cả BLOCKED
rows), falsifier battery (đánh số thống nhất theo umbrella; master governs —
F-4 beta/bloc và F-7 các fixture bổ sung định nghĩa tại freeze, A7-F9),
annotation corpus manifest (nếu route
discretionary), freeze artifact (membership, arm digests, thresholds, seeds,
pins — sha256), dry-run, scored cells + margin-to-fail, seam/kill-law files,
DSR, repro twin, A7 prelaunch + terminal, trial_ledger.jsonl, CYCLE_VERDICT.md.
Program-level: IDENTITY_REGISTRY.jsonl, PLAYBOOK_TAXONOMY.md (frozen §4).
Terminal vocabulary: umbrella §9 + `NO_CANDIDATE` + `BLOCKED_<class>` +
`BACKTEST_CANDIDATE_REPLICATED` (paper-tier bound, 7/7 R0–R6). Mọi verdict âm
là first-class close.

## 12. Quyết định owner đang chờ (xem GO1_OWNER_PACKET.md)

Q1 phê chuẩn charter — **bao gồm quyết định định nghĩa (A7-F2): taxonomy
playbook price-level/session + lớp annotation mù outcome có phải là
"observable/giả thuyết payer mới CÓ BẰNG CHỨNG" đủ để mở pair-child SOL sau
khi stop-rule §9(a) của PWS-CX đã bắn trên 2 pair trống liên tiếp hay không**
(nếu không: pair đầu CX = BTCUSDT, hoặc track CX DORMANT như FX); Q2 duyệt
caps (cells/identity ceiling); Q3 duyệt thứ tự pair + pair đầu; Q4 FX: giữ
DORMANT hay chủ động mở reopener R1/R2/R3; Q5 duyệt GO phrase sẽ gõ tại gate
GO-1 của pair đầu.
