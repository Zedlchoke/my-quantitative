# PLAN (DRAFT) — ERP-FOREX-PROGRAM-V1 — Master plan: chương trình tìm kiếm strategy Forex qua nhiều cohort

> **Status: `DRAFT_FOR_OWNER_DECISION — NOT REGISTERED, NOT EXECUTED.** File
> này không đăng ký cycle, không spawn worker, không download, không mở S1,
> không đụng shadow/daemon/dashboard, không tiêu GO nào. Nó là chương trình
> tầng master nằm DƯỚI umbrella `ECONOMIC-ROBUSTNESS-PROGRAM-V1`
> (ACTIVE_LIGHT trong registry) — kế thừa toàn bộ luật umbrella §§1–11 trừ
> khi child chặt hơn; mọi cohort là child cycle riêng với budget/freeze/A7/
> GO riêng. Owner phê chuẩn bản charter này bằng quyết định ghi vào
> `forex_program/OWNER_PACKET_cohort2_2026-09-26.md` (không cần registry row
> mới — umbrella đã là cycle quản trị đang sống).
>
> Authored 2026-09-26 bởi Lead từ owner instruction (verbatim intent: tiếp
> tục nghiên cứu qua nhiều cohort cho tới khi tìm được ÍT NHẤT MỘT strategy
> trên ít nhất một cặp Forex đạt chuẩn `BACKTEST_CANDIDATE_REPLICATED`; nếu
> bằng chứng không đạt thì kết luận `NO_CANDIDATE`, bảo toàn OOS, đề xuất
> cohort mới; tuyệt đối không hạ chuẩn để hoàn thành chỉ tiêu).

## 0. Program identity

```text
program_id    ERP-FOREX-PROGRAM-V1  (master layer; scored cells = 0/0 —
             không bao giờ tự score; mọi scored surface thuộc child cohort)
parent        ECONOMIC-ROBUSTNESS-PROGRAM-V1 (umbrella, Track A + luật chung)
goal          ≥1 strategy identity đạt BACKTEST_CANDIDATE_REPLICATED (§4)
              trên ≥1 cặp Forex, HOẶC kết luận NO_CANDIDATE/BLOCKED đúng gate
ledger        per-child trial_ledger.jsonl (append-only) + P-9 denominators
S1            SEALED_UNTOUCHED ở mọi nơi; sealed OOS per-identity một lần
orders        NONE — mọi kết luận paper/backtest tier; shadow/live là GO riêng
stops         §7 (hết giả thuyết mới / hết data authority / hết OOS sạch /
              hết power / hết ngân sách ⇒ dừng đúng gate, không chạy vô hạn)
```

## 1. Mục tiêu / không-mục-tiêu

### 1.1 Mục tiêu

Tìm kiếm theo cơ chế (mechanism-first) trên FX majors: mỗi cohort freeze tối
đa 3 cơ chế kinh tế thật, falsify TRƯỚC PnL, score dưới cost book đo được,
bảo toàn sealed OOS, và chỉ báo `BACKTEST_CANDIDATE_REPLICATED` khi một
identity hội đủ cả bảy điều kiện R0–R6 (§4). Chuẩn không hạ để có số dương:
`REJECT_ALL`/`NO_CANDIDATE` là kết quả hợp lệ và được kỳ vọng là kết quả modal.

### 1.2 Không-mục-tiêu

- Không cứu RANGEFADE hay bất kỳ family đã chết bằng đổi ngưỡng/đảo dấu/đổi
  tên/đổi timeframe/thêm indicator/đổi session (umbrella §6; Q-3).
- Không hạ ngưỡng gate, không nới power, không "thử lại" trên cặp/cửa sổ
  khác sau khi một identity fail OOS.
- Không claim live-readiness ở bất kỳ đâu (umbrella §1.3). Kết quả tốt nhất
  của chương trình này là "ứng viên backtest đáng tin" — đưa vào shadow là
  quyết định GO riêng của owner.
- Không re-litigate license posture trong child cycle (EDQ1/D-C); không đụng
  worker FX/BANDRIDGE/PSV1, dashboard, broker, lệnh.

## 2. Danh mục cặp và dữ liệu được phép (binding)

Nguồn lịch sử duy nhất đang có authority: **Dukascopy M1 BID/ASK** với
`OWNER_DIRECTIVE_SOURCE_AUTHORIZATION + TCU_RISK_DISCLOSED` (posture kế thừa
EDQ1/umbrella; mọi verdict mang `SINGLE_SOURCE_PANEL + PAPER_TIER`). Nguồn
độc lập (TrueFX/OANDA v20 practice/Dukascopy written consent) = 0 bytes cho
tới khi owner unblock (EDQ1 packet 2026-09-22); Twelve Data chỉ dùng
mid-price reconciliation. Broker/exchange domains bị filter môi trường
(L-FXFF-1) — mọi nguồn mới chạy G0 reachability probe trước khi dispatch.

| Bề mặt | Exposure (xem matrix) | Vai trò được phép |
|---|---|---|
| EURUSD, GBPUSD, USDJPY (2021-01..2026-06) | outcome-exposed | ancestry, fixture, spread-curve authority |
| AUDUSD, USDCAD dev 2021-01..2025-12 | outcome-exposed cho class range-fade | dev cho observable MỚI (D2 adjudicate) |
| AUDUSD, USDCAD holdout 2026-01..06 | **SEALED-UNREAD** | one-look OOS cho identity mới |
| USDCHF / pair chưa search khác | outcome-free (cần data gate) | replication-transfer surface |
| Nguồn độc lập | BLOCKED (owner unblock) | replication limb R5(iii)-source khi mở |

Child cohort chốt slate pair của chính nó tại GO-1; mọi pair mới chạy đủ data
gate cohort-1 §5.2 (probe/census/DST/rollover/scale fixtures; engine đã
parametrize PIP/scale/band per pair).

## 3. Kiến trúc cohort (luật cố định cho mọi cohort)

1. **Council outcome-blind** (§5 roster): proposals chỉ chứa cơ chế + 10
   trường umbrella §5.3; không PnL/PF/winner nào trong packet.
2. **Freeze tối đa 3 cơ chế**; mỗi cơ chế 1 anchor + ≤2 neighbour + 1 causal
   control + 1 inverted control + 1 baseline set (beta-matched per pair).
   Không grid, không blend, không sign-flip rename.
3. **Falsification pre-PnL** F-1..F-7 (child plan §8): ancestry rho ≤0.20
   (representation law P-12), F-PIT-1 battery mở rộng (M-1..M-5 + future-data
   mutation + delay-pair Q-4 cho sub-hour), clock-placebo non-vacuous (Q-11),
   beta/bloc, cost-survivability ceiling F-5, feasibility nearest-window Q-6,
   concentration pre-check Q-12. Skeptic có VETO pre-PnL; cost auditor có
   BLOCKED; PIT auditor không xem PnL.
4. **Scored walk-forward**: folds thời gian F1..F6, force-flat, gates
   G1–G8 với margin-to-fail, stress ×1.5/×2.0, kill laws + control-prediction
   bands (cohort-1 §9.2–9.4 freeze nguyên văn làm mặc định).
5. **Sealed OOS một lần, sau GO riêng** (GO-3): membership artifact sha256
   trước pass; arm chết không được nhìn holdout.
6. **Replication ladder** §4 cho identity sống sót.
7. **Đóng cohort**: A7 terminal fresh-context + two-half close (registry +
   P-9 ledger + FAMILY_FAILURES/MAP/LESSONS + errata bundle P-19).

## 4. Định nghĩa `BACKTEST_CANDIDATE_REPLICATED` (chuẩn báo owner — 7/7)

Một identity X chỉ được báo `BACKTEST_CANDIDATE_REPLICATED` khi hội đủ TOÀN BỘ:

- **R0 Identity freeze trước outcome**: arm digests + membership + thresholds
  sha256-pinned trước computation đầu tiên của identity.
- **R1 PIT + data authority PASS**: F-PIT battery (panel-truncation
  byte-identical, future-mutation test, không same-day statistic) và data
  gate PASS trước PnL; nguồn theo §2.
- **R2 Dev gates PASS**: G1–G8 PASS toàn bộ @×1.0 và net>0 @×1.5 trên home pair
  (floors ≥100 RT + ≥6 tháng; power gate ≥236 RT hoặc bootstrap CI loại 1.0).
- **R3 Controls không tái tạo edge**: clock-placebo KHÔNG đạt band
  (≥0.5×anchor ⇒ kill); inverted strictly below (cả trên OOS); beta-matched
  baseline bị beat với biên ≥2× theo §9.4; không KILL_* nào bắn.
- **R4 Sealed OOS one-look PASS**: net>0 @×1.0 VÀ @×1.5 trên cửa sổ sealed,
  một lần, membership frozen, sau GO riêng.
- **R5 Replication ĐÚNG ĐỊNH NGHĨA — cả ba limb**: (i) **impl độc lập** —
  A7 lane viết lại từ đầu (không import engine của implementer), tái tạo
  net/folds/trade-count từ raw planes trong tolerance frozen; (ii) **thời
  gian chưa dùng để chọn** — cửa sổ OOS/transfer chưa từng bị search cho X;
  (iii) **bề mặt độc lập** — HOẶC cặp outcome-free (vd USDCHF, một evaluation
  pass duy nhất trên toàn window với identity frozen từ home pair), HOẶC
  nguồn dữ liệu độc lập có authority (hiện BLOCKED — chỉ khi owner unblock).
  **Một cửa sổ transfer = MỘT look cấp chương trình, không phải per-identity:
  window của cặp transfer chỉ được tiêu một lần bởi một identity trong toàn
  chương trình; look thứ hai trên cùng window là void (matrix L5).** Thiếu
  một limb ⇒ KHÔNG được viết "replicated".
- **R6 A7 độc lập PASS**: terminal audit recompute từ bytes, không kế thừa
  verdict implementer; mọi finding blocking đã đóng.

Kèm theo: DSR trên toàn trial ledger của chương trình tới thời điểm; PBO chỉ
khi ≥8 configs (else NOT_RUN); báo cáo gross / declared-cost net /
measured-cost net tách bạch; labels `SINGLE_SOURCE_PANEL`, `PAPER_TIER`,
`FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK` trên mọi row. **Phát ngôn bắt buộc
khi báo owner**: đây là "ứng viên backtest đáng tin", KHÔNG phải strategy
chắc chắn kiếm tiền, KHÔNG được phép live/shadow nếu thiếu GO riêng.

## 5. Roster subagent (mỗi cohort; ranh giới mù outcome)

| Lane | Vai trò | Được thấy | Bị cấm | Quyền đặc biệt |
|---|---|---|---|---|
| A1 | Controller/ghi sổ | state, freeze, ledger | tự đề xuất cơ chế | — |
| **A. PIT/data auditor** | audit timestamp từng feature/event; publication time, timezone/DST, bar close, as-of join, ngày nghỉ, missing; panel-truncation + future-mutation fixtures | code + data planes + fixtures | MỌI PnL/outcome | FAIL ngay nếu leak |
| **B. Economic skeptic** | phản biện payer/premium/persistence/ancestry/controls/selection bias; đo ancestry rho trên frozen representation | proposals + failure memory + dữ liệu phi-outcome | viết strategy code | **VETO pre-PnL** |
| **C. Cost/execution auditor** | bid/ask, phí, spread theo phiên/sự kiện, slippage, gap/no-fill, capacity, ceiling 1×/1.5×/2× | cost censuses, fill laws, planes | điền giả định lạc quan khi thiếu nguồn | **BLOCKED** khi thiếu nguồn |
| **D. Independent reproducer/A7** | impl độc lập, recompute, audit freeze/gates | artifact machine + (outcome chỉ đúng giai đoạn được phép) | kế thừa verdict implementer | REFUSED = remediation arc |
| P1..Pn | Blind proposers | packet phi-outcome | mọi outcome surface | proposals only |

Không một lane nào vừa đề xuất, vừa score, vừa tự duyệt. Mọi lane nộp
PASS/FAIL/NOT_RUN kèm đường dẫn bằng chứng + handoff `zcode_orch_v3_handoff@1`;
Lead tổng hợp bất đồng — không bỏ phiếu ghi đè FAIL.

## 6. Vòng lặp giữa các cohort

Sau mỗi cohort bị bác bỏ: (1) ghi FAMILY_FAILURES/LESSONS/MAP đúng quy trình
two-half close; (2) trả lời "cơ chế nào chết vì sao" bằng số liệu đã freeze;
(3) cohort kế tiếp chỉ được mở từ **thông tin MỚI** (observable mới có
authority, nguồn mới được unblock, bài học phương pháp mới thay đổi falsifier)
— không phải tinh chỉnh quanh winner/loss vừa nhìn. Chuỗi cohort hiện hữu:
COHORT-1 (đóng REJECT_ALL 2026-09-25: M1 KILL_PIT_SEAM+KILL_INVERSION cả 2
pair; M2 D2-veto; M3 F-5 kill) → **COHORT-2 (draft, plans/
PLAN_erp1_tracka_cohort_2.md)** với inputs mới: 3 future-cohort candidates
P1/P2 (PROV-ABSORB, RECLAIM-ABSORB pending class adjudication, PROBE-DEPLETION
GATE) + open-call cho cơ chế ngoài range-edge family + tài sản sealed holdout
AUDUSD/USDCAD 2026-H1 + USDCHF outcome-free.

## 7. Điều kiện dừng / đổi hướng (fail-safe)

Dừng và báo owner (không tự mở rộng) khi một trong: (a) không còn giả thuyết
mới nào qua được D2 sau ≥2 cohort liên tiếp trống slate; (b) hết data
authority (mọi nguồn §2 blocked + owner chưa unblock); (c) hết OOS sạch
(sealed map trống); (d) không đạt power với ngân sách còn lại; (e) hết ngân
sách được cấp. Kết luận `NO_CANDIDATE` (đã tìm trong không gian được cấp
quyền, không có gì đạt R0–R6) hoặc `BLOCKED_<class>` — cả hai đều thành phẩm
nghiên cứu (Q-16), không phải thất bại quy trình.

## 8. Ngân sách & lịch GO (mỗi cohort)

- Budget scored cells: child tự chốt (cohort-2 chốt **18 = 3 cơ chế × 6 arms
  × 1 home pair**); program-level cap do owner đặt từng cohort; observed/
  published split P-9.
- Chuỗi gate: **GO-1 register+council+falsifiers+freeze (dừng)** → A7
  prelaunch → **GO-2 scored dev** → nếu identity qua đủ dev gates: A7 kiểm →
  **GO-3 sealed OOS + replication pass (một lần)** → A7 terminal → two-half
  close. GO phrase của cohort ghi trong child plan; GO gõ trước gate = intent
  (P-8). Early-typed GO không bao giờ thành quyền thường trực.
- Shadow promotion / nguồn mới / đổi slate pair = owner decision riêng.

## 9. Artifacts & nhãn terminal

Per-child: council reports + handoffs, data-gate verdict, falsifier battery
results, freeze artifact (seeds, membership, pins — P-19 hygiene), dry-run,
scored cells + margins, seam/kill-law files, DSR, repro twin, A7 prelaunch +
terminal, trial_ledger.jsonl, CYCLE_VERDICT.md. Terminal vocabulary: umbrella
§9 + `NO_CANDIDATE` (program-level) + `BACKTEST_CANDIDATE_REPLICATED`
(program goal label, paper-tier bound). Mọi verdict âm là first-class close.
