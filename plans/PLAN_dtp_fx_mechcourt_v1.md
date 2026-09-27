# PLAN — DTP-FX-MECHCOURT-V1 — Tòa cơ chế day-trading Forex: 3 cơ chế owner-định danh, adjudication pre-PnL

> **Status: `REGISTERED by owner instruction 2026-09-27 — pre-scoring adjudication
> cycle.** Owner instruction (verbatim intent): lập cycle mới nghiên cứu
> day-trading Forex, đi nhanh từ giả thuyết đến scored development cells;
> nghiên cứu đúng ba cơ chế (A) dòng tái cân bằng trước London fix cuối tháng,
> (B) FX điều chỉnh sau bất ngờ kinh tế khi phản ứng thị trường lãi suất ĐÃ
> QUAN SÁT ĐƯỢC, (C) lệch quote đồng bộ giữa hai địa điểm giao dịch với mô
> hình khớp đủ hai chân. Trước khi code, đối chiếu từng cơ chế với
> FAMILY_FAILURES và các cycle FX đã đóng; trùng skeleton đã chết ⇒ loại ngay,
> không cứu bằng đổi pair/session/ngưỡng/đảo dấu. Nếu không cơ chế nào có dữ
> liệu PIT và chi phí đủ để score ⇒ kết thúc `BLOCKED_DATA/COST` với chính xác
> nguồn, quyền truy cập và dữ liệu owner cần cung cấp; tuyệt đối không chạy
> scored cell vô nghĩa. Owner instruction này KHÔNG PHẢI GO nào (P-8).
>
> Owner đã nói thẳng và Lead xác nhận như luật: DTP-FX frontier law (master
> plan `PLAN_daytrade_playbooks_program_v1.md` §5, kế thừa PWS §5) cấm scored
> cell trên panel FX cũ khi chưa có reopener R1/R2/R3/R5 với bytes + license +
> cost authority. Cycle này hoạt động ở LỚP PRE-SCORE (council/court/census);
> mọi scored surface chỉ mở nếu một cơ chế qua đủ gate VÀ reopener có bytes VÀ
> owner gõ GO riêng tại gate của cycle.

## 0. Cycle identity

```text
cycle_id      DTP-FX-MECHCOURT-V1
parent        DAYTRADE-PLAYBOOKS-PROGRAM-V1 (DRAFT master; track DTP-FX) dưới
              umbrella ECONOMIC-ROBUSTNESS-PROGRAM-V1; kế thừa ERP-FOREX-PROGRAM-V1
              (R0–R6, §2 danh mục dữ liệu, §7 stop), SRLV-PROGRAM-V1 (F-0 court,
              PIT §3, kill rules), PWS-PROGRAM-V1 (§2 identity, §5 frontier) —
              trừ khi child chặt hơn.
asset         forex
worktree      /Users/hoangminhlong/my-quantitative/.worktrees/dtp-fx-mechcourt-v1/integration
branch        orca/dtp-fx-mechcourt-v1-integration
budget        0/0 scored cells theo thiết kế (pre-registered): cycle này không
              score trừ khi amendment mở reopener + GO-2. Mọi adjudication là
              pre-PnL, không tiêu denominator scored (P-9: 0/0; adjudication
              rows ghi trial_ledger loại ADJUDICATION_NOT_SCORED).
S1            SEALED_UNTOUCHED — holdout AUDUSD/USDCAD 2026-H1 KHÔNG mở, không
              đọc, kể cả để "kiểm tra nhanh" (một look = tiêu cấp lineage).
orders        NONE. Không broker, không lệnh, không paper/testnet.
GO phrase     GO DTP FX MECHCOURT V1 SCORED EXECUTION (REGISTERED_NOT_CONSUMED;
              chỉ có hiệu lực nếu một cơ chế qua đủ gate + reopener có bytes +
              owner gõ tại gate này. Đóng BLOCKED ⇒ phrase chết UNCONSUMED).
goal          Ba cơ chế A/B/C được adjudicate trọn vẹn bằng bằng chứng đo được;
              verdict đúng luật cho TỪNG cơ chế; owner packet unblock chính xác.
              `BLOCKED_DATA_OR_COST` tổng là kết quả hợp lệ và theo mọi bằng
              chứng đứng trước (VIABILITY 2026-09-26: NO_CANDIDATE 0/12 class)
              là kết quả KỲ VỌNG, không phải thất bại (Q-16).
```

## 1. Re-measure Phase-0 (đo 2026-09-27, Lead)

- Root `main` @ `656c106a`, dirty tree = file untracked của các session khác
  (bảo toàn, không sweep — P-10). Heavy lock `FREE_PROVEN`. Disk 29 GiB free
  (đo `df -h /`; cải thiện từ 6.2 GiB sau dọn worktree).
- FX data plane đo bằng bytes (Lane D re-verify độc lập): Dukascopy M1 bid/ask
  EURUSD (shadow worktree, cập nhật tới 2026-09-23) + GBPUSD/USDJPY
  (fx-majors worktree, tới 2026-09-23); AUDUSD/USDCAD raw corpus KHÔNG còn
  trên đĩa (chỉ manifest + census JSON + 1H ANC parquet chứa sealed rows —
  CẤM mở). Rates: CHỈ daily (EFFR/SOFR tới 2026-09-14); intraday rates = 0
  bytes; futures = 0 bytes (CME BLOCKED_TRANSPORT L-FXFF-1). Venue thứ hai =
  0 bytes; IBKR probe 2026-09-26: 0 two-sided obs, minTick 0.5 pip,
  `BLOCKED_BROKER_COST_AUTHORITY` đứng nguyên.
- Frontier đứng nguyên: VIABILITY cohort-3 `NO_CANDIDATE` (0/12 class);
  reopener R1/R2/R3/R5 = 0 bytes mới từ 2026-09-26; EDQ1 chờ owner source
  decision; DTP GO-1 Q4 = "FX giữ DORMANT" (GO_RECORD.md); owner instruction
  2026-09-27 (cycle này) là authority mở LỚP ADJUDICATION, không phải reopener.

## 2. Ba cơ chế — định nghĩa đóng băng nguyên văn từ owner instruction

Mọi lane adjudicate đúng ba định nghĩa này; không tự nới, không tự thêm biến
thể. Biến thể (đổi pair/session/ngưỡng/đảo dấu) bị cấm như luật anti-variant
(DTP master §2.3; owner law 2026-09-26 "adding an observable is not a new
mechanism"; owner law 2026-09-27 "đổi pair/timeframe/session/filter không
phải strategy mới").

### 2.1 Cơ chế A — `DTPFX-A1` month-end London fix rebalancing

> "London fix cuối tháng: kiểm dòng tái cân bằng theo benchmark tạo chuyển
> động có thể dự đoán trước 16:00 London, với hướng giao dịch xác định từ
> thông tin đã công khai trước đó." (Owner; ghi chú owner: "có dòng giao dịch
> thật quanh fix, nhưng điều đó không đồng nghĩa có lợi nhuận sau phí".)

Skeleton chuẩn hóa để đối chiếu (strip test): trigger = cửa sổ lịch/trước-fix
(ngày cuối tháng/cuối tuần giao dịch, giờ tới 16:00 London); direction = dấu
của đại lượng công khai tính từ lịch sử giá (month-to-date return / ước lượng
rebalance theo benchmark weights); exit = sau fix. Payer khai báo: mandates
track benchmark phải giao dịch tại fix, trả spread + drift cho deadline
certainty.

### 2.2 Cơ chế B — `DTPFX-B1` news → rate repricing → FX lag

> "Tin kinh tế → định giá lại lãi suất → FX: chỉ vào lệnh sau khi tin và phản
> ứng của thị trường lãi suất đã quan sát được; kiểm FX điều chỉnh chậm hơn.
> Đây không phải 'đoán tin' hay news-fade." (Owner; ghi chú owner: "phải có
> dữ liệu đúng thời điểm".)

Skeleton chuẩn hóa: event = release kinh tế có PIT available_at; điều kiện
vào lệnh = phản ứng thị trường lãi suất đã QUAN SÁT ĐƯỢC (series lãi suất
tần suất intraday, cùng window với FX); hướng = theo repricing lãi suất; FX
leg = M1 bid/ask. KHÔNG được thay leg rates bằng chính phản ứng FX (đó là
news-fade — dead class).

### 2.3 Cơ chế C — `DTPFX-C1` lệch quote đồng bộ hai venue

> "Lệch giá FX giữa hai nơi giao dịch: kiểm một mức giá cập nhật chậm so với
> nơi còn lại, nhưng chỉ khi có quote hai chiều đồng bộ và mô phỏng được cả
> hai chân khớp lệnh." (Owner; ghi chú owner: "không được thay bằng nến của
> một nguồn rồi gọi là arbitrage".)

Skeleton chuẩn hóa: hai feed bid/ask ĐỒNG BỘ (cùng clock discipline, tick
hoặc tốt hơn) từ hai venue độc lập; tín hiệu = lệch stale-quote; execution =
hai chân taker, mỗi chân theo book của venue nó.

## 3. Luật kế thừa binding (rút gọn, trỏ về văn bản gốc)

1. **Frontier law DTP master §5** (kế thừa PWS §5): không pair FX nào được
   score khi chưa có reopener R1/R2/R3/R5 với bytes + license + cost authority.
   Không reopener ⇒ `BLOCKED_FRONTIER_NOT_REOPENED`, 0 scored cell, 0 holdout
   look. Tái chạy skeleton/payer đã chết = F-0 kill ngay.
2. **ERP-FOREX §2**: nguồn lịch sử duy nhất có authority = Dukascopy M1
   BID/ASK (`SINGLE_SOURCE_PANEL + PAPER_TIER + OWNER_DIRECTIVE_SOURCE_
   AUTHORIZATION + TCU_RISK_DISCLOSED`); EURUSD/GBPUSD/USDJPY outcome-exposed
   ⇒ CHỈ ancestry/fixture/cost authority, không bao giờ evidence mới/OOS;
   AUDUSD/USDCAD dev = chỉ cho observable MỚI; 2026-H1 SEALED; USDCHF 0 bytes.
3. **F-0 court** (SRLV §2.3 / DTP master §2.2): skeleton test (bỏ observable
   mới, còn edge không? cùng shape = cùng family chết); payer test; information
   test (Q-7: thông tin gì chưa có trong clock/trend/spread). Skeptic VETO
   pre-PnL. Anti-variant §2.3: hai identity khác nhau phải khác ≥2/3 (payer;
   information layer PIT; risk shape).
4. **Ancestry law**: pooled |rho| > 0.20 trên frozen representation = K-ANC
   (P-12 representation law; đo, không tranh luận). Q-3: đổi cadence không
   giặt được family. Class law: dead class trong FAMILY_FAILURES/VIABILITY
   census binds mọi proposal cùng skeleton.
5. **Cost law**: spread theo PHÂN PHỐI FILL của cơ chế × k∈{1.0,1.5,2.0}
   (Q-2/Q-8); executor book = bar-open opposite-quote spread; measured beats
   stated; commission/slippage `DECLARED_UNMEASURED`; ceiling âm ⇒ VETO trước
   scoring. Sàn đo: AUDUSD/USDCAD ×2.0-stressed conditional RT 3.6/4.4 pips;
   EURUSD/GBPUSD/USDJPY crossing p50 0.3/0.8/0.5 pips (census pinned); bucket
   fix-window/tháng-cuối CHƯA TỪNG ĐO (census chỉ có session buckets) —
   cycle này ĐO nó (G2, cost authority trên pair exposed — hợp lệ).
6. **PIT law** (SRLV §3 / DTP §4.2): mức từ bar đã đóng; earliest fill = quote
   giao dịch được sau khi tín hiệu biết; cấm same-bar fill intrabar-order; cấm
   same-day statistic (P-18); event phải có `available_at` THẬT từ nguồn có
   authority + xử lý revision; thiếu ⇒ `BLOCKED_DATA`, KHÔNG thay bằng proxy.
7. **Microstructure law** (VIABILITY class 10; Q-4): M1 bid/ask không có
   volume/depth/tape; mọi "edge" sub-minute trong lịch sử chương trình bay
   hết ở delay-1; sub-M1/maker/queue = UNFUNDABLE-ARM VETO.
8. **No-rescue / no-re-tune**: không đổi threshold/band/fill-law sau khi số
   xuất hiện; mọi kill là terminal cho identity trên surface đó.

## 4. Luật verdict PRE-REGISTERED (đóng băng trước khi lane chạy)

Mỗi cơ chế nhận MỘT verdict chính theo đúng thứ tự ưu tiên (violation đầu tiên
theo thứ tự chặn):
(a) `F0_KILLED <VETO class>` — skeleton/payer/information trùng family chết
(theo F-0 court, dẫn chứng FAMILY_FAILURES row + class law);
(b) `BLOCKED_DATA` — thiếu dữ liệu PIT/venue theo định nghĩa §2 (đo bằng bytes);
(c) `BLOCKED_COST` — không đủ cost authority để đặt ceiling (components thiếu);
(d) `BLOCKED_FRONTIER_NOT_REOPENED` — cơ chế qua (a)-(c) về lý thuyết nhưng
scoring bị cấm vì chưa có reopener (DTP §5).

Quyết định cụ thể đóng băng cho từng cơ chế (giả thuyết làm việc của Lead,
lane xác nhận/bác bằng bằng chứng — lane KHÔNG được đảo ngược thứ tự ưu tiên):

- **A**: kỳ vọng (a) `F0_KILLED VETO_VARIANT_SAME_FAMILY` vs
  `TRACKA2-P4A-FIXCERT-01` (London fixing-window certainty premium; kill
  `DECLARED_BAND_BELOW_MEASURED_COST`; RC: "owner amendment with a NEW
  economic basis (cheaper measured execution or larger evidenced premium);
  parameter re-tunes are barred") + class 5 VIABILITY (fix-window/clock/
  calendar). Month-end subset + direction-MTD = re-gate/re-clock của cùng
  skeleton (trigger pre-fix window; payer fix-certainty; exit post-fix).
  Parkings: nếu lane S cho skeleton KHÔNG trùng (chỉ xảy ra nếu payer/
  information layer khác căn bản), verdict rơi xuống (d) — vẫn không score
  (không reopener). Census chi phí fix-window (G2) KHÔNG cứu A trong mọi
  kết cục (kill là ancestry/class + frontier, không phải chỉ cost); census
  chỉ sharpen owner packet.
- **B**: kỳ vọng (b) `BLOCKED_DATA` — leg rates-market intraday = 0 bytes
  (daily EFFR/SOFR không quan sát được "phản ứng đã xảy ra" trước entry);
  PIT release ledger hiện có (131 events, 10/131 minute-exact, không
  consensus/revision vintages, diagnostic outcome-exposed) dưới evidence
  floor. Secondary (ghi kèm, không phải verdict chính): adjacency class 7
  VIABILITY (15 dead macro entries; DGS10-shadow shape — FXFV8/FXNG1-A4-P2:
  rate-level exposure control OUT-EARNED anchor); taxonomy row 8 DEAD +
  DATA-GATED.
- **C**: kỳ vọng (b) `BLOCKED_DATA` — chỉ MỘT feed hai chiều tồn tại; venue
  thứ hai 0 bytes (IBKR 0 two-sided obs; Dukascopy re-download
  BLOCKED_TRANSPORT; TrueFX/OANDA owner-gated EDQ1); hai chân taker cần
  broker-grade books. Secondary: cross-venue lead-lag class dead
  (FXFV7-A6-P2) + Q-4 delay law + class 10 UNCONSTRUCTIBLE trên M1.

**Verdict tổng**: nếu cả ba không score được (kỳ vọng) ⇒ terminal
`DTP_FX_V1_BLOCKED_DATA_OR_COST`, 0 scored cells, GO phrase chết UNCONSUMED,
owner packet §7. Nếu (trái kỳ vọng) một cơ chế qua (a)-(c): DỪNG ngay trước
gate scored — freeze artifact (membership, arms, cost book, power) và bàn
giao owner GO phrase + cell list; KHÔNG tự score (P-8; owner instruction:
prompt sớm không phải GO-2).

## 5. Roster lanes (mù outcome theo thiết kế — cycle không có PnL)

| Lane | Việc | Được thấy | Viết artifacts |
|---|---|---|---|
| A1 (Lead) | plan/registry/verdict assembly/close | tất cả (không có outcome nào) | verdict, owner packet, ledger, MAP |
| **S — skeptic court** | F-0 skeleton/payer/information + class-law đối chiếu A/B/C; ancestry representation định nghĩa (nếu cần đo rho thì đo trên representation frozen, pre-registered) | plan §2/§4, FAMILY_FAILURES, VIABILITY, cohort-2 F0/F1/F5, taxonomy, exposure matrix | `SKEPTIC_court_REPORT.md` + handoff |
| **D — data/PIT + cost census** | (i) byte-verify data plane (FX corpora, macro ledger, rates, venue 2, cost artifacts); (ii) fix-window spread census EURUSD/GBPUSD/USDJPY: s_open của bar 15m theo London-local hour × {month-end last-1, last-2 trading days} × {fix window vs neighbor hours}, p50/p75/p90/p99 + n; DST bằng Europe/London zoneinfo; KHÔNG tính giá-drift/premium/PnL | data planes (read-only), corpora của shadow/fx-majors (read-only public data, không đụng trạng thái nội bộ), census scripts | `DATAPIT_census_REPORT.md` + `fixwindow_spread_census.json` + handoff |
| **A7 — terminal audit** | fresh-context: recompute census từ bytes, re-check từng trích dẫn court, audit verdict-vs-law, proof refusal paths | mọi artifact + bytes | `A7_TERMINAL_AUDIT.md` + handoff |

Ràng buộc lane: không lane nào vừa đề xuất vừa adjudicate; S không viết code
engine; D không adjudicate; A7 không sửa gì. Handoff `zcode_orch_v3_handoff@1`
tại `research/control/DTP-FX-MECHCOURT-V1/HANDOFF_<lane>.json` (trong
worktree). Census phải non-vacuous (n>0 mỗi bucket công bố; bucket rỗng ghi
rỗng). Thứ tự: S và D chạy song song; verdict assembly sau cả hai; A7 cuối.

## 6. Census fix-window — preregistration chính xác (chạy trước khi nhìn số)

- Cặp: EURUSD, GBPUSD, USDJPY (exposed ⇒ cost authority only; không premium).
- Nguồn: `bars15.parquet` (s_open = a_open − b_open tại bar-open 15m) của
  EURUSD (shadow worktree) + GBPUSD/USDJPY (fx-majors worktree); span toàn
  corpus 2021-01..2026-09; sha256 file pin trong artifact.
- Buckets: London-local hour ∈ {13,14,15,16,17} của bar-open × day-set ∈
  {ME1 (ngày giao dịch cuối tháng), ME2 (2 ngày cuối), MID (ngày giữa tháng
  kiểm soát: ngày 13–16)} × pair. Thêm bucket tham chiếu rollover_21_22UTC.
- Thống kê: n, p25, p50, p75, p90, p99 của s_open (pips); zero/negative
  spread count. Không thống kê giá, không returns, không PnL.
- Mục đích pháp lý: đo bucket chi phí mà FIXCERT từng bị kill bằng proxy
  session-bucket — biến prior thành số đo cho owner packet. KHÔNG ảnh hưởng
  verdict của A (đã đóng băng ở §4: census không cứu A).

## 7. OWNER_PACKET unblock (nội dung bắt buộc nếu verdict tổng BLOCKED)

Gói bàn giao owner phải chứa, cho TỪNG cơ chế, đúng các mục:

1. **Chung (mở lại scored surface FX)**: một reopener theo DTP master §5 —
   R1 (IBKR: bật FX delayed data two-sided qua "Manage Data Subscriptions"
   hoặc share sub từ tài khoản funded; xuất Activity/Flex statement có trade
   FX + overnight positions, tốt nhất T4–T7 gồm cuối tuần, đặt tại
   `~/.my-quantitative-data/ibkr_statement/`; restart TWS giữ socket 7497
   Read-Only — probe đông lạnh đo lại một lệnh) HOẶC R2 (EDQ1: chọn MỘT trong
   TrueFX free-reg + capture TCU nguyên văn / Dukascopy written-consent email
   / OANDA v20 practice + đọc API terms + probe M1) HOẶC R3 (financing band
   broker-grade) HOẶC R5 (information layer có authority, không-PnL).
2. **Riêng A**: bằng chứng "larger evidenced premium" (information layer PIT
   ngoài panel giá — vd ước lượng fix order-flow từ nguồn có license) hoặc
   "cheaper measured execution" (R1/R2) — theo RC nguyên văn của FIXCERT; và
   một bề mặt FX chưa exposure cho premium measurement (USDCHF-class corpus
   sau data gate; CẢNH BÁO: holdout sealed AUDUSD/USDCAD 2026-H1 là one-look
   cấp lineage — không tiêu cho cơ chế đang blocked).
3. **Riêng B**: (i) dữ liệu thị trường lãi suất intraday — CME ZQ/ZZT
   (fed funds / SOFR futures) tick/minute: cần owner unblock network CME
   (SNI filter đo bởi FX-FUTURES-FRONTIER-V1) + license dữ liệu, hoặc nguồn
   broker-grade tương đương; (ii) PIT release feed có available_at + consensus
   + revision vintages (ALFRED keyless cho US; lịch chính thức non-US; nguồn
   consensus có license); (iii) bề mặt FX dev chưa exposure cho class này.
4. **Riêng C**: venue thứ hai đồng bộ (chọn một path EDQ1), granularity tick
   hoặc tốt hơn CẢ HAI venue, clock discipline đồng bộ, và cost authority hai
   chân (R1 cho ít nhất một venue thực thi được).
5. **Trung thực kỳ vọng**: kể cả có đủ dữ liệu, A/B nằm kề các class đã đo
   chết (class 5/7 VIABILITY); dữ liệu mở phép ĐO, không mở edge.

## 8. Artifacts & nhãn terminal

`research/control/DTP-FX-MECHCOURT-V1/` (trong worktree, cherry về main theo
two-half close): INTAKE.md, SKEPTIC_court_REPORT.md, DATAPIT_census_REPORT.md,
fixwindow_spread_census.json, VERDICT_assembly.md, OWNER_PACKET.md,
A7_TERMINAL_AUDIT.md, CYCLE_VERDICT.md, trial_ledger.jsonl (rows
ADJUDICATION_NOT_SCORED ×3), HANDOFF_*.json. Terminal vocabulary: per-mechanism
verdicts §4 + tổng `DTP_FX_V1_BLOCKED_DATA_OR_COST` (hoặc
`BLOCKED_FRONTIER_NOT_REOPENED` nếu A/B/C qua data nhưng không reopener).
FAMILY_FAILURES: append row cho mỗi cơ chế bị F0_KILLED (chỉ sau A7 confirm).
MAP bullet + HYPOTHESIS_LEDGER stamp `+0/+0 scored (adjudication pre-PnL)`.

## 9. Stop conditions

(a) Cả ba cơ chế verdict xong ⇒ close theo §4; (b) lane phát hiện data mới
thay đổi frontier (bytes mới xuất hiện giữa cycle) ⇒ dừng, báo owner
(amendment), không tự hấp thụ; (c) mọi blocked-ngừ nguồn đều là owner action —
không vòng lặp thay thế proxy (A7-F1 law: "không series hợp lệ ⇒ BLOCKED_DATA,
không thay bằng proxy").
