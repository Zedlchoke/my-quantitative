# PLAN (DRAFT) — ERP1-TRACKA-COHORT-2 — FX mechanism cohort 2: range-edge absorption với observable mới + open call

> **Status: `DRAFT_FOR_OWNER_GO — NOT REGISTERED, NOT EXECUTED.** File này
> đăng ký nothing, không spawn worker, không download (trừ khi GO-1 cho phép
> probe có giới hạn), không mở S1, không đặt lệnh, không đụng shadow worker
> nào. Parent: `plans/PLAN_economic_robustness_program_v1.md` (umbrella,
> ACTIVE_LIGHT) + `plans/PLAN_erp_forex_program_v1.md` (master program,
> draft đi kèm). Registration chỉ qua `researchctl cycle register` sau owner
> GO trên plan này.
>
> Authored 2026-09-26 bởi Lead từ owner instruction 2026-09-26. Cohort-1
> (`ERP1-TRACKA-COHORT-1`, TERMINAL `REJECT_ALL`, A7-certified 2026-09-25)
> là ancestry trực tiếp: M1 RANGEFADE-PIT chết KILL_PIT_SEAM + KILL_INVERSION
> trên cả AUDUSD lẫn USDCAD; M2 chết D2-veto; M3 chết F-5 pre-PnL; holdout
> 2026-H1 hai pair **chưa đọc** — tài sản sealed của chương trình.

## 0. Cycle identity

```text
cycle_id     ERP1-TRACKA-COHORT-2
class        MECHANISM COHORT (outcome-blind council -> pre-PnL falsification
             -> frozen scored trials dưới paper-tier cost book; verdict bound
             paper tier; program-goal label BACKTEST_CANDIDATE_REPLICATED chỉ
             theo ladder §10.2 khi đủ R0-R6)
parent       ECONOMIC-ROBUSTNESS-PROGRAM-V1 (umbrella Track A) +
             ERP-FOREX-PROGRAM-V1 (master, draft charter)
asset        forex (majors; slate §5)
budget       18 scored cells MAX (≤3 cơ chế × 6 arms × 1 home pair —
             3×6×1; A7 review F6/BC-6: cap 18, không 24, vì mỗi cơ chế
             đúng 1 home pair); holdout looks + replication passes là
             ledgered re-evaluations, không phải cell mới (như cohort-1)
ledger       research/control/ERP1-TRACKA-COHORT-2/trial_ledger.jsonl
             (append-only; schema cohort-1 §10 + labels)
S1           SEALED_UNTOUCHED (không có surface S1 trong cycle này)
orders       NONE — không broker, không paper order; prospective continuation
             = owner-GO surface riêng
shadow       KHÔNG đụng FX-RANGEFADE-2M-SHADOW-V1 / PROSPECTIVE-SHADOW-V1
             (workers, journal, daemon, dashboard, worktree: read-only citation)
GO-1 phrase  GO ERP1 TRACKA COHORT 2 REGISTER AND COUNCIL
             (tại gate đăng ký; authorizes: register, council dispatch (đã có
             slate input §4), data-gate probe nếu cần, PIT/cost audits,
             falsification battery, trial freeze — VÀ DỪNG)
GO-2 phrase  GO ERP1 TRACKA COHORT 2 SCORED
             (chỉ sau A7 prelaunch PASS; authorizes dev cells trong cap 18)
GO-3 phrase  GO ERP1 TRACKA COHORT 2 SEALED OOS AND REPLICATION
             (chỉ cho identity qua đủ dev gates + R5 freeze; mở sealed OOS
             MỘT LẦN + replication transfer pass MỘT LẦN; không có identity
             nào qua thì GO-3 không tồn tại)
forbidden    parameter grids; indicator blending; sign-flip renames; lo_q/hi_q
             re-tune là "cơ chế mới"; rescue RANGEFADE dưới mọi dạng (đổi
             ngưỡng/đảo dấu/đổi tên/đổi timeframe/đổi session/thêm indicator/
             THÊM OBSERVABLE-GATE lên luật chết — "thêm observable" không đủ
             là cơ chế mới, F-0 adjudicate); thay candidate bị F-0 veto bằng
             biến thể cùng họ; lấp slot bằng giả thuyết yếu (slot trống là kết
             quả hợp lệ); re-score cửa sổ đã lộ làm evidence mới; đọc ancestry
             PnL vào proposer packets; S1; orders; shadow-worker touch;
             registry edits ngoài researchctl; merge/push; sửa verdict TERMINAL
```

## 1. Mục tiêu / không-mục-tiêu

### 1.1 Mục tiêu

- Tối đa 3 cơ chế FX có nguyên nhân kinh tế kiểm chứng được, mỗi cơ chế là
  một identity mới với observable MỚI (chưa từng được search ở surface dùng
  làm dev của nó), **qua được F-0 mechanism-class adjudication (§8) trước mọi
  rho/PnL — "thêm observable" không đủ là cơ chế mới**, falsify trước PnL,
  score dưới cost book đo được, và nếu sống sót — đi tiếp ladder replication
  R0–R6 để tới `BACKTEST_CANDIDATE_REPLICATED` hoặc chết trung thực.
- Đầu vào mới hợp pháp (thông tin MỚI theo master §6): (a) ba future-cohort
  candidates từ council cohort-1 (P1 PROV-ABSORB; P2-A RECLAIM-ABSORB;
  P2-B PROBE-DEPLETION GATE) — được thiết kế outcome-blind và chưa tiêu
  slot/look nào; (b) open-call cho cơ chế NGOÀI range-edge family để tránh
  monoculture; (c) tài sản sealed holdout AUDUSD/USDCAD 2026-H1; (d) USDCHF
  outcome-free làm replication-transfer surface (cần owner amendment chốt
  slate).

### 1.2 Không-mục-tiêu

- Không có Task-1 "replication RANGEFADE" — đã xong và đã chết ở cohort-1;
  mọi biến thể range-fade không thêm observable mới = rescue, bị cấm.
- Không hạ G-gate/power/concentration band. `REJECT_ALL` là kết quả mong đợi
  về mặt xác suất và là đóng góp hợp lệ.
- Không claim nào vượt paper tier; không live-readiness wording.

## 2. Authority, Phase-0, boundaries

- Authority order: owner instruction > child plan (khi registered) > master
  program plan > umbrella > CLAUDE.md + handbook v2. Child chỉ được chặt hơn.
- Phase-0 tại intake của chính cycle (umbrella §3): re-measure registry/
  doctor/locks; lock-drift ⇒ BLOCKED; doctor HIGH findings chỉ chặn nếu đụng
  freeze chain của cycle này (P0-3 accepted-historical class cho TERMINAL
  cycles đã archive worktree). Snapshot tại drafting: root `main` @
  `73ae43e1` (đo 2026-09-26); heavy lock FREE_PROVEN; FX daemon + PSV1
  e-worker alive và UNTOUCHED (PSV1 đang chạy engine-fix arc dưới owner
  delegated decision 2026-09-26 — không phải quyền của cycle này).
- Một Live session; council/audit chạy light dưới umbrella authority; heavy
  job (nếu có download) dưới machine-wide lock, yielding pattern.
- Lanes implementation chỉ trong worktree của cycle; council artifacts vào
  `research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/tracka_cohort2/` +
  handoffs tại dispatch path.

## 3. Ancestry disclosure (binding, mọi artifact của cycle phải mang)

Kế thừa nguyên văn §3 cohort-1 + bổ sung:

1. Toàn bộ ancestry cohort-1: M1 KILL_PIT_SEAM (S=2884.1/4348.6 pips, 3/3
   limb, cả hai pair) + KILL_INVERSION (inverted thắng trên F5 AUDUSD; F1/F6
   USDCAD) — PIT-clean law PF 1.033/1.051, 3/6 folds, net âm @×1.5. R-ORIG
   qua 8 gate cả hai pair là bằng chứng leak (L3 trong matrix), không phải
   target. M2 `NOT_SCORED_FALSIFIED (D2 V-4_BLEND)`. M3 `NOT_SCORED_
   FALSIFIED (F-5: stress RT 4.8 ≥ 2.0)`.
2. Outcome-exposure map = `forex_program/LESSON_TO_GATE_MATRIX.md` (bảng
   exposure) là phụ lục binding của plan này. Cụ thể: AUDUSD/USDCAD dev
   2021-2025 là surface ĐÃ THẤY outcome cho class range-fade — cơ chế cohort-2
   dùng surface này làm dev chỉ hợp pháp khi observable của nó chưa từng
   được search ở đó (D2 kiểm qua registry + trial ledger toàn chương trình).
3. 12-family census exposure (EURUSD/GBPUSD/USDJPY) binding như cohort-1 §3.5.
4. Blindness law (label-only disclosure — A7 review F2 remediation):
   proposer packets chứa **§3 ở dạng LABEL-ONLY** (tên cycle + nhãn verdict
   của ancestry, KHÔNG bất kỳ con số PnL/PF/fold nào — kể cả các số trong
   §3.1, vì trong đó có +3207/+5030 pips của arm lookahead R-ORIG) + §4
   candidate text + §5 source table + KHÔNG PnL/PF/win-rate/trade-count/
   journal/MAP outcome rows/dashboard. **OWNER_PACKET và mọi artifact
   owner/audit KHÔNG BAO GIỜ là nguồn build proposer packet (A7 delta2 N2).**
   A7 prelaunch kiểm packet build theo luật này.
5. Ancestry gate: pooled |rho| ≤ 0.20 (immovable) vs FAMILY_FAILURES + MAP
   closed-bullets + các shadow cohort-1 (R-ANCHOR, R-ORIG, placebo, inverted,
   baselines trên AUDUSD/USDCAD) + class vetoes (re-clock, calendar geometry,
   displaced-fade, nominal-level, vol-level, premium-fade, retest/second-probe
   class — xem §8 F-1a).

## 4. Cơ chế slate (input cho council; freeze tối đa 3 tại GO-1)

Mỗi candidate phải trả lời 10 trường umbrella §5.3 + 6 câu hỏi kinh tế
cohort-1 §7.3 TRƯỚC khi được xét (chưa nhìn PnL nào). Council (A/B/C/D +
blind proposers) adjudicate và đề xuất ≤3; **mọi candidate được freeze vào
slate phải qua F-0 mechanism-class adjudication (§8) trước — skeptic phán
C1/C2/C3 và mọi open-call ở cấp mechanism class TRƯỚC rho/PnL; cả ba
candidate P1/P2 bị veto thì cohort vẫn mở với open-call hoặc đóng
`NO_ELIGIBLE_PROPOSAL` (slot không bị lấp bằng giả thuyết yếu)**; skeptic có
VETO pre-PnL.

- **C1 — PROV-ABSORB (từ P1, designed outcome-blind 2026-09-25).**
  Provenance-gated band-break absorption: chỉ fade break của prev-day
  high/low khi chính mức bị break *được hình thành trong cửa sổ phiên thanh
  khoản* (observable: session-of-formation của extreme — layer thông tin mới
  so với M1/M3). Payer giả thuyết: stop-flow bắt buộc tại biên mà nguồn biên
  là thanh khoản thật (không phải biên mỏng giờ ít người). Cần D2: ancestry
  vs RANGEEXP/R-ANCHOR shadows + F-PIT cho biến provenance.
- **C2 — RECLAIM-ABSORB (từ P2-A) — CHỈ SAU F-0.** Fade band sweep chỉ khi
  bar đóng lại trong band (reclaim). **Cross-lane tension cohort-1 (binding):
  explorer đã self-veto class retest/second-probe trên ancestry FXFV2-A4-P2
  (placebo tái tạo anchor) + displaced-fade class; F-0 xử lý câu hỏi class
  này TRƯỚC khi chạy bất kỳ rho fixture nào** — nếu class chết, C2 chết ngay
  không tốn fixture.
- **C3 — PROBE-DEPLETION GATE (từ P2-B).** Fade gated bằng số lần M1 probe
  cùng biên trong ngày (≥2 lần chạm không break trước khi break) — observable
  microstructure M1 mới (probe count), không phải re-tune. Unfundable-arm
  check: costable trên M1 bid/ask với H1 clock (critic C thẩm định; nếu cần
  sub-M1 sequencing ⇒ veto như M3-era law).
- **C4..Cn — OPEN CALL (≥1 cơ chế NGOÀI range-edge family).** Council mời
  proposal mới ngoài family để tránh monoculture (vd: session-liquidity-cycle
  hay fix-window flow có payer định danh được — nhưng mọi cơ chế event/
  calendar chịu F-3 clock-placebo + Q-7 clock-only shadow như luật đứng);
  candidate phải có observable PIT trên nguồn §5 đã có authority (không mở
  nguồn mới trong cycle này trừ owner amendment).

Cả ba dạng input đều chịu novelty law cohort-1 §7.4 nguyên văn (mechanism +
information source + causal control phải mới; veto renamed/re-tuned/
re-clocked/re-sessioned/inverted-dead/blends/cross-horizon rescue). Cơ chế
thứ 4 bị cấm; council propose nhiều hơn thì owner/A1 chỉ freeze 3 cái tốt
nhất theo ranking skeptic, các cái còn lại ghi `NOT_FROZEN_SLATE_FULL` làm
future-cohort candidates.

## 5. Data authority và slate pair

### 5.1 Corpora sẵn có (sha-pinned, censused — cohort-1 assets)

- AUDUSD, USDCAD: Dukascopy M1 BID/ASK 2021-01..2026-06, probe/census/DST/
  rollover/session-spread BUILD_PASS, engine per-pair scale fixtures OK.
  Dev 2021-2025: exposure rule §3.2. Holdout 2026-01..06: **SEALED**.
- EURUSD/GBPUSD/USDJPY: chỉ ancestry/fixture/cost-authority (matrix).

### 5.2 Slate pair đề xuất (owner chốt tại GO-1)

- **Home pairs**: AUDUSD và/hoặc USDCAD (không download mới) — mỗi cơ chế 1
  home pair do council đề xuất theo logic kinh tế (bloc/USD-geometry), D2
  xác nhận surface hợp lệ cho observable của cơ chế đó.
- **Replication-transfer surface (R5(iii)-pair)**: **USDCHF** — outcome-free;
  cần: (a) **owner amendment riêng chốt slate (D2-2) — GO-1 TỰ NÓ KHÔNG cấp
  quyền download USDCHF** (A7 review BC-7), (b) data gate cohort-1 §5.2 đầy đủ
  (download bounded ~44MB+probe, heavy lock, yield), (c) FIX CHỈ IDENTITY ĐÃ
  QUA dev gates mới được evaluation pass MỘT LẦN trên toàn window USDCHF
  (dev+holdout hợp nhất, criteria frozen; một look cấp chương trình — §9.1).
  Alternative nếu owner unblock nguồn độc lập (EDQ1): R5(iii)-source thay thế.
- NZDUSD giữ nguyên lý do loại của cohort-1 (bloc-redundant với AUDUSD);
  crosses giữ nguyên (không USD anchor cho beta framework).

### 5.3 Nguồn độc lập

BLOCKED (D-C posture kế thừa): Twelve Data = mid-price reconciliation-only;
TrueFX/OANDA/Dukascopy-consent chờ owner action (EDQ1 packet). Mọi verdict
giữ `SINGLE_SOURCE_PANEL` cho tới khi một nguồn độc lập được unblock VÀ
được dùng cho R5(iii).

## 6. Cost authority (paper-tier book — five binding conditions nguyên văn)

Kế thừa nguyên văn cohort-1 §6 (conditions 1–5 + charging semantics + force-
flat fixtures + taker model + wording bans + incident cross-ref). Tóm tắt
binding: verdict class bounded paper tier; structural-zero financing bằng
executor fixture; per-session spread đo được tại fill-bar ×k∈{1.0,1.5,2.0}
(không dùng global p50); adverse selection declared-unmeasurable (taker PAYS
spread — cấm mọi từ "capture/earn the spread", "fill at mid"); marks-vs-fills
seam disclosed; unfundable-arm veto (cần sub-M1 sequencing/maker/queue ⇒ veto
pre-PnL). Mọi hằng số theo Q-8: measured hoặc chết conservative.

## 7. Council (composition + blindness)

- Lanes: A1 controller + **A. PIT/data auditor** + **B. economic skeptic
  (VETO pre-PnL)** + **C. cost/execution auditor (BLOCKED power)** + **D.
  independent reproducer/A7 (outcome-staged: trước scored chỉ thấy freeze/
  code/planes, không thấy PnL)** + blind proposers P-lanes cho open call.
- Packet blindness như §3.4. Council artifacts + `zcode_orch_v3_handoff@1`
  tại dispatch paths dưới `tracka_cohort2/`.
- Không lane nào vừa đề xuất vừa score vừa tự duyệt (master §5).

## 8. Pre-PnL falsification battery (gate TRƯỚC cell scored đầu tiên)

Kế thừa F-1..F-7 cohort-1 §8 nguyên văn, với các mở rộng bắt buộc. **Thứ tự
bắt buộc: F-0 → F-1 → F-2..F-7** (child chặt hơn master/umbrella — được phép):

- **F-0 MECHANISM-CLASS ADJUDICATION (owner law 2026-09-26; skeptic lane;
  TRƯỚC mọi rho fixture, TRƯỚC mọi PnL, áp cho TOÀN BỘ candidate gồm C1, C2,
  C3 và mọi open-call):**
  1. Skeptic đóng băng **family signature của họ đã chết** (range-edge
     pressure absorption = fade các break của biên ngày/băng trước: họ
     trigger = break prev-day high/low hoặc band tương đương; direction =
     fade ngược break; exit = reversion về mid-band / đóng ngày; payer
     story = stop-flow/pressure tại biên rồi hồi quy) — nguồn: M1 cohort-1
     + ancestry RANGEEXP/RANGEFADE/PDHLOC/FXFV2-A4-P2/displaced-fade.
  2. Mỗi candidate bị soi bởi **ba phép thử class**, kết quả ghi trong
     artifact F-0 trước khi bất kỳ con số rho/PnL nào tồn tại:
     (a) **Skeleton test** — gỡ observable mới khỏi luật candidate; phần
     còn lại có suy biến về luật chết (cùng họ trigger + direction + exit)
     không? Có ⇒ candidate là "RANGEFADE/range-edge fade đổi gate" ⇒
     `VETO_VARIANT_SAME_FAMILY`;
     (b) **Payer test** — nguồn premium phải khác "biên bị break rồi hồi
     quy"; payer định danh được và khác payer của họ chết; nếu câu chuyện
     payer vẫn là stop-flow range-edge hồi quy ⇒ cùng họ ⇒ VETO;
     (c) **Information test** — observable mới phải quyết định một điều
     KHÔNG phải "có/không/khi nào trade như luật cũ" (đổi bản chất risk
     được chuyển giao hoặc đổi tập hợp payer); chỉ thêm gate lên luật cũ
     là không đủ.
  3. VETO tại F-0 đóng slot vĩnh viễn trong cohort: **không thay bằng biến
     thể cùng họ**; slot chỉ được lấp lại bởi open-call candidate từ family
     KHÁC (owner D2-3).
  4. **Slot policy (D2-3 + luật không lấp yếu)**: open-call candidate được
     xét như candidate thường (10 trường + 6 câu hỏi + F-0 với family
     signature riêng của family đó); một slot để trống
     (`SLOT_LEFT_EMPTY_NO_QUALIFIED_CANDIDATE`) là kết quả HỢP LỆ và được
     ưu tiên hơn lấp bằng giả thuyết không qua được F-0/F-5/control-
     constructibility. ≤3 cơ chế, fewer allowed (umbrella §5.2).
  5. Artifact F-0 (signature + ánh xạ từng candidate + verdict + shas/timestamps
     chứng minh nó committed TRƯỚC mọi rho fixture) là điều kiện tiền-GO-2.
     **F-0 là one-shot (A7 delta2 N3): mỗi candidate được adjudicate đúng MỘT
     lần; mọi re-run/adjudicate lại đòi hỏi owner amendment ghi lý do; không
     có vòng "chỉnh candidate rồi phán lại đến khi qua".**
- **F-1 Ancestry + representation law** (rho trên frozen representation, do
  skeptic đo — **chỉ chạy SAU khi F-0 pass**): pooled |rho| ≤ 0.20 + class
  vetoes; câu hỏi class retest/second-probe (FXFV2-A4-P2 placebo-death +
  displaced-fade ancestry) đã được F-0 xử lý trước khi rho chạy — nếu F-0 đã
  veto thì không tốn fixture.
- **F-2 PIT audit mỗi signal code = F-PIT-2 battery (mở rộng từ M-1..M-5)**:
  (i) independent-implementation equivalence (M-1-style cho mọi biến mới);
  (ii) non-vacuity ≥2% mọi mutation; (iii) daemon-seam emulation N/A trừ khi
  candidate liên quan shadow law; (iv) self-test-blindness fixture giữ nguyên
  luật; (v) **panel-truncation replay: tín hiệu freeze phải byte-identical
  trên panel cắt đúng mỗi decision time**; (vi) **future-data mutation test**
  (mutate bars sau decision time ⇒ output không đổi); (vii) mọi biến trạng
  thái ngày/biên ngày audit same-day statistic (L1); (viii) audit timestamp
  từng feature/event: publication/effective/available tách biệt, timezone/DST
  fixtures, bar-close vs as-of join, holiday/weekend, missing-data rule —
  lane A xuất bảng EVIDENCED/ASSERTED/UNEVIDENCED (P-1: asserted = NOT_RUN).
- **F-3 Clock/session geometry**: CLOCK-PLACEBO control phải MOVE (Q-11
  non-vacuity predicates nguyên văn cohort-1) + mode-sham/shuffle nơi có biến
  regime rời rạc + per-hour PnL tables + pre/post-DST splits + S6 no-drift-
  flag law cho fades; mọi cơ chế event/calendar thêm Q-7 clock-only shadow.
- **F-4 Beta/bloc**: per-pair frozen directions như cohort-1 (AUDUSD →
  SHORT_ALWAYS; USDCAD → LONG_ALWAYS; USDCHF nếu dùng → full-window drift-sign
  rule + mid-window inversion disclosed); beta-composition disclosure P2.
- **F-5 Cost-survivability ceiling**: declared-band arithmetic, premium band
  từ proposal field-2 vs ×2.0-stressed per-session book đo từ census trên 6
  tháng gần nhất, conditional spread tại break-style bars; âm ⇒ veto pre-PnL
  (VOL-NG1 precedent; M3 cohort-1 chết đúng luật này).
- **F-6 Feasibility nearest-window** (Q-6): per-fold populations vs floors.
- **F-7 Concentration pre-check** (Q-12) + exclusion zones mọi ngưỡng.

Ordering law: data/PIT/cost audit + falsification chạy XONG trước PnL đầu
tiên của cycle; fail F-* ⇒ `NOT_SCORED_FALSIFIED`, không mở vòng sửa.

## 9. Fold/holdout contract, thresholds, kill laws

### 9.1 Folds + sealed OOS

- Dev 2021-01-01..2025-12-31, folds F1..F6 chronological, force-flat; không
  substitute fold sau khi thấy PnL.
- **Sealed OOS = holdout 2026-01-01..2026-06-30 trên home pair** (UNREAD từ
  cohort-1 — asset của chương trình; mở MỘT LẦN bởi GO-3 chỉ cho identity qua
  đủ dev gates; membership artifact sha256 trước pass; arm chết không nhìn).
  Nếu home pair của một identity là pair mà cửa sổ 2026-H1 đã bị tiêu bởi
  identity khác ⇒ identity đó không được dùng cửa sổ đó (một cửa sổ - một
  identity - một look; sổ đăng ký sealed map do A1 giữ).
- **Companion membership — single pass (kế thừa cohort-1 §9.1 P2-extension,
  A7 review F6 remediation)**: mỗi pass holdout của một identity gồm CHÍNH
  identity đó + các companion đã preregister (causal control, inverted
  control, baseline books) được tính trong CÙNG một pass duy nhất — companions
  không bao giờ là consumer độc lập và không được đòi pass thứ hai cho bất kỳ
  mục đích nào (kể cả limb "inverted strictly below anchor" của R3: inverted
  companion đã có trong pass).
- **Replication transfer (R5(iii)-pair)**: MỘT evaluation pass trên toàn
  window USDCHF 2021-01..2026-06 với identity + criteria frozen từ home pair;
  pass này thuộc GO-3, ledgered riêng. **Một cửa sổ transfer = MỘT look CẤP
  CHƯƠNG TRÌNH, không phải per-identity (A7 review F5 remediation): window
  USDCHF chỉ được tiêu MỘT lần bởi MỘT identity trong toàn bộ chương trình;
  các identity sau (cùng cohort hoặc cohort khác) không được nhìn nó lần nữa —
  từ look thứ hai, mọi pass trên window đã lộ là void theo matrix L5.** Sealed
  map của A1 đăng ký cả hai loại cửa sổ (holdout per-identity một lần;
  transfer per-program một lần) và cập nhật tại mỗi two-half close.

### 9.2 Dev gates (frozen — kế thừa cohort-1 §9.2 nguyên văn)

G1 net>0 @×1.0; G2 PF ≥1.20; G3 ≥4/6 folds net>0; G4 net>0 @×1.5; G5 ≥100
closed RT AND ≥6 tháng; G6 top-fold share ≤50%; G7 top-5-trades ≤50%; G8
top single session-hour ≤50% (+ margin-to-fail mọi gate + exclusion zones).

### 9.3 PROMOTE/KILL/TIME-STOP (kế thừa cohort-1 §9.3 + power gate)

Nguyên văn cohort-1: kill terminal cho identity trên pair; inverted ≥ anchor
hoặc inverted dương trên fold anchor thua ⇒ KILL_INVERSION; control reproduce
⇒ KILL_CONTROL_REPRODUCED; beta-explained (≤0 hoặc <0.5×) ⇒ KILL_BETA;
holdout net ≤0 ⇒ chết, KHÔNG đổi pair/ngưỡng để thử lại; no mid-cohort
replacement; PROMOTE kèm power ≥236 RT hoặc bootstrap CI (seed frozen);
`NOT_POWERED_CANDIDATE` là trần khi thiếu power. TIME-STOP: freeze+60 ngày
không qua data gate/falsifier ⇒ `BLOCKED_*` trung thực.

### 9.4 Control-prediction bands + seam law

Kế thừa cohort-1 §9.4 nguyên văn (bands ×0.5/×2; seam law áp dụng cho mọi
cặp PIT-variant/diagnostic twin nếu có; limb-iii minimum-N 20; units = pip
của pair). Với cơ chế không có twin PIT-variant, seam law N/A và ghi NOT_RUN
có lý do — không bịa twin sau khi thấy số.

## 10. Replication ladder, budget, ledger

### 10.1 Ladder (đầy đủ mới được nhãn mục tiêu)

R0–R6 như master plan §4. Trong cycle này: GO-2 authorizes dev; GO-3 mở
sealed OOS + replication (i) impl độc lập bởi lane D + (iii) transfer pass;
(ii) được đảm bảo bởi sealed map + membership freeze. A7 terminal certify.

### 10.2 Budget

18 cells MAX (≤3 cơ chế × 6 arms × 1 home pair). Holdout/transfer/repro =
ledgered re-evaluations. TECHABORT re-run vẫn đếm observed. Program-level
forex denominators tiếp tục theo P-9 (two-half close stamp). **PBO — luật
đếm-at-freeze duy nhất (sửa mâu thuẫn bản trước theo owner 2026-09-26): A1
đếm distinct frozen config classes THỰC TẾ của slate tại freeze (tập hợp
anchor + neighbour configs của các cơ chế được freeze, theo yêu cầu CSCV);
count ≥ 8 ⇒ PBO BẮT BUỘC tính trên đúng tập đó (per-period series persisted,
P-11); count < 8 ⇒ PBO = `NOT_RUN_FAIL_CLOSED` kèm số đếm measured trong
ledger. Không có khẳng định tiên nghiệm "sẽ/không sẽ" đủ ngưỡng.**

### 10.3 Ledger schema

Cohort-1 §10 nguyên văn + labels `SINGLE_SOURCE_PANEL`, `FILL_QUALITY_
UNMEASURABLE_ON_M1_BIDASK`, `PAPER_TIER`, + labels OOS/transfer
`SEALED_LOOK_ONE` / `TRANSFER_PASS_ONE`. DSR mọi trial; **PBO theo luật
đếm-at-freeze duy nhất ở §10.2** (≥8 distinct frozen config classes ⇒ tính;
else `NOT_RUN_FAIL_CLOSED` với measured count — hai mục luôn dùng cùng một
luật, không còn mâu thuẫn).

## 11. A7 arc, decisions, close

- A7 plan-audit (lane độc lập, fresh context) trên CHÍNH plan này trước khi
  owner gõ GO-1 — đã dispatch 2026-09-26, verdict + findings trong
  `forex_program/plan_review/` (xem OWNER_PACKET). A7 prelaunch trước GO-2;
  A7 terminal tại close; positive claims dùng stricter audit (handbook §22.2).
- Two-half close: registry flip + P-9 ledger + FAMILY_FAILURES/MAP/LESSONS +
  errata bundle P-19 + sealed-map sổ cập nhật (cửa sổ đã tiêu ghi rõ).
- Owner decisions cần: **(D2-1)** GO-1 tại gate register; **(D2-2)** chốt
  slate pair (đề xuất: home AUDUSD/USDCAD, transfer USDCHF qua amendment);
  **(D2-3)** có mở open-call cơ chế ngoài family (khuyến nghị CÓ, ≥1 slot);
  **(D2-4)** GO-2/GO-3 tại các gate của chúng. Các pending quyết khác của
  chương trình (P-G1..P-G3 amendments, EDQ1 nguồn, PSV1 engine-fix) không
  thuộc cycle này và không bị cycle này chặn.

## Appendix A — Slate input provenance

P1/P2 candidates: `tracka_cohort1/PROPOSER1_cohort1_REPORT.md`,
`PROPOSER2_cohort1_REPORT.md` (blind, outcome-blind by law; chưa tiêu slot/
cell/look nào — cohort-1 §A.3). Class tension C2: cùng file. M1/M2/M3 kills:
`tracka_cohort1/SCORED_REPORT.md` + `audits/A7_terminal_REPORT.md`. Sealed
holdout status: A7 terminal C-3 (HOLDOUT_UNREAD_CONSUMED_BY_NONE).
