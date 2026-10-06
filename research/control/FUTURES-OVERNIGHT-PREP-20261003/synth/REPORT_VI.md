# BÁO CÁO TIẾNG VIỆT — FUTURES-OVERNIGHT-PREP-20261003 (SYNTH-VERIFY, 2026-10-04)

Vòng PREP qua đêm theo chỉ thị owner 2026-10-03 (~15:00Z), chạy đến
~08:00 Asia/Ho_Chi_Minh 2026-10-04. **Không phải cycle đăng ký, không
scoring.** 11 lane nghiên cứu (batch-1: P0A/P0B + P2A/P2B/P2C, base
`a8cd06f2`; batch-2: P0-VERIFY + 5 lane P1, base `72c9bc5b` sau checkpoint
commit batch-1) + lane này (SYNTH-VERIFY) tổng hợp và kiểm chứng độc lập.
Root main `4f266528` dirty của owner — không đụng. Heavy lock FREE_PROVEN
suốt phiên, không lane nào lấy lock.

## Sự cố usage-limit (disclose đầy đủ)

Lần chạy đầu của batch-2 (~23:59Z ngày 2026-10-03): **cả 6 lane chết vì
usage limit**. Sau reset, chạy lại thành 2 đợt: đợt 1 (P0-VERIFY, P1-ESNQ,
P1-6E6B, P1-CROSS — handoff 00:00-00:45Z), đợt 2 (P1-6J6A, P1-COMM —
handoff 05:55/09:30Z). Một lane kế thừa partial từ lần chết — P1-6J6A khai
báo incident rõ: `hypo/6j_6a/captures/source_sha256.tsv` stale partial
(18 dòng, không header) được **REBUILT fresh** (19 dòng + provenance
header, toàn bộ hash recompute tại `72c9bc5b`; 18 dòng cũ trùng hash —
disclosed, không dùng unverified). Không output nào của lần chết được làm
bằng chứng nếu chưa rebuild.

## P0 — erratum phí: ĐƯỢC UPHOLD TOÀN BỘ (UPHELD_IN_FULL)

Lỗi gốc xác định byte-level: **glued superscript** — `1.38<sup>6</sup>` và
`0.01<sup>1</sup>` trên CME.php bị renderer dán thành 1.386/0.011 (đúng lỗi
A4 cha). P0A lưu 4 raw archive HTML + 4 live render (shasum); P0-VERIFY
kiểm chứng độc lập: mọi cell then chốt定位 byte-level, worked-example
`0.85+1.38+0.00+0.01=2.24` nguyên văn, **10/10 mã tier-1 CONFIRMED**
(ES/NQ 2.24; 6E/6B/6J/6A 2.46 — mapping FX alias PARTIAL; CL 2.36; NG
2.46; GC/SI 2.51 — kèm 2 thay đổi thật trong 2026: COMEX 1.60→1.65 và reg
0.02→0.01, cả 2 epoch đều capture). Lane này recompute lại: verdict file
tồn tại, bảng verdict khớp `fees_corrected.json` **10/10**. Giá trị cha
1.386/0.011/2.247/2.461/2.37/2.47 → RETIRE làm SOURCE; 22 artifact
frozen-historical giữ nguyên, erratum nằm cạnh (append-only); **account
verification vẫn NOT_RUN; UNDER REVIEW đến khi có A7 mới**; SPEC_PB1_ES r3
không sửa.

## P2 — đóng gap lịch (mọi claim có capture + sha256)

- **P2A equity**: đủ 5 quý ES thiếu (Sep/Dec-2010, Mar/Jun/Sep-2011 =
  2010-09-17, 2010-12-17, 2011-03-18, 2011-06-17, 2011-09-16) từ 2 capture
  archived độc lập của trang product-calendar chính thức — **ES 68/68 quý**
  (42 product + 26 family rolldates; NQ cross-check khớp 100%; giả thuyết
  "trang NQ mang hàng ES" của Lead bị bác firsthand). Giờ Globex 2026 cụ thể
  ES/NQ: **NOT_OBTAINED** (chỉ nằm trong DATE widget — host
  BLOCKED_TRANSPORT; PDF settlement-times là giờ GIÁ settle, không suy ra
  giờ phiên).
- **P2B FX + comm**: FX expiries **96 → 208/272** (4 mã × 52/68, đủ
  2010-2022 kể cả ECH12 khó nhất; 112 artifact mới; 2023-2026
  NOT_OBTAINED — mọi tuyến đã thử). Holiday-times FX 2017-2023: **lật
  nhận định "không archive" của A2 cha** — 49/95 cell (2017 11/11 …
  2023 1/10). GC kéo dài đến **Dec-2023** (+11 contract), SI đến
  **Dec-2022** (+7). Energy/metals 2011-2015: theo grid từng năm của
  chính lane = **52/55 in-universe** (headline "43/45" của lane là lỗi
  cộng — finding F-7, thiên hướng bảo thủ).
- **P2C BLS vintage**: 2 anomaly cha giải quyết xong bằng capture có ngày,
  không đoán. Phân kỳ late-2025 = **sửa lịch chính thức giữa năm** do lapse
  in appropriations: CPI Sep-ref Oct 15→24 (notice 10-10, lý do SSA verbatim),
  CPI Oct-ref **CANCELED**, CPI Nov-ref Dec 10→18; EMPSIT Sep-ref Oct 3→
  Nov 20 (công bố 11-14), Oct-ref **CANCELED**, Nov-ref Dec 5→16 — cả 6 claim
  đều pin được capture (lane này mở file xác nhận: schedule 09-10 còn
  Oct.15/Nov.13/Dec.10; schedule 11-21 đã thành Oct.24/Dec.18 và hàng
  October bị xóa). 2016-04 double-entry = **parsing artifact phía cha**:
  6 capture 2016 đều chỉ có MỘT hàng April → May 17 (không có "Jun 2").
  Luật PIT cụ thể hóa: bảng vintage-as-of-decision-date; 2025 có 11 CPI /
  10 EMPSIT prints; 2 ngày bị hủy-but-expected = falsifier tự nhiên.

## P1 — portfolio giả thuyết cạnh tranh (5 lane, outcome-blind)

- **ESNQ**: 8 family (4 ES + 4 NQ), 11 trường bắt buộc mỗi family; phân loại
  đúng (0 PnL, 0 return statistic). ES-F1 FOMC-RES 2.906×/3.188× (7 số
  headline lane này mở JSON verify khớp làm tròn); NQ era 0.80→0.59,
  2.99→1.46; VR 0.808/0.711/0.669; OVN 10.2→23.8%; COT U-shape n=922; roll
  61/66. Census ES minimal **36 > cap 24 → mọi ES family
  BLOCKED_TRIAL_BUDGET**.
- **6E6B**: 4 family + 2 overlay; FOMC-on-6E **×17.24** (minute 780),
  6B MPC **18.7×** (7,090.5 vs 379.5), 8:30 spike ×1.95 + RV 15.58%/
  volume 12.5%, reopen-gap std 0.378% = 0.805×, 6B corr +0.84, 6E
  +0.91→−0.107 (vintage flip) — lane này verify 8/8 số. PB2 HOLD giữ
  nguyên; FX không có cap.
- **6J6A**: 6 family (3 6J + 3 6A); BoJ 54 ngày quyết định FACT nhưng
  **không minute-stamp** (window convention +±45min thay thế); window book
  34-vs-53 (35.8% mỏng hơn); 6A ±5′ 9.0×/4.8× — phép đo mạnh nhất dossier
  nhưng K0 thin-n kill (n=67) pre-registered; 386-op MOF; 16/16 material-roll
  sign law. 6J SECONDARY (3 gate chưa đóng), 6A PB3 PARK.
- **COMM**: 7 alpha + GC-F2 execution + 3 khai báo construction; mọi thứ
  intraday **NOT_RUN_DATA_ABSENT** (vendor root **0 comm O1M** — lane này
  đếm lại thư mục: chỉ 6A/6B/6E/6J/ES/NQ); re-measure kho feature của lane
  được lane này **recompute độc lập khớp 100%**: WNGSR 1,205 issues
  (2001-05-07→2026-01-22), survey 369 dòng (inj 247/wd 87/NaN 35, **100%
  medians dương** → blocker r-1 xác nhận cấp cột), WPSR 790 + Cushing
  790/790, CPC 4,459+65+31 (inventory 4,555), HDD/CDD 1,319 MONTHLY.
  CL/NG/GC/SI vẫn NOT_QUALIFIED_V2 — không có lối đăng ký.
- **CROSS**: 5 thiết kế phủ định liên-symbol (X-1..X-5, 0 identity theo
  class) + **RANKING_FRAMEWORK** (rubric 5 chiều, cấm tuyệt đối return
  statistic) + **CENSUS_PROPOSAL** (khung denominator, câu hỏi
  placebo-budget 3 quyước để owner phán).

## Tổng hợp của lane này (synth/)

- **FINAL_RANKING top-5** (cơ học theo rubric CROSS, điền nốt 2 lane
  PENDING): **1) AF3 bimodal US+Sydney (6A) 12/15 — PB3 PARK; 2) JF3
  Tokyo-morning (6J) 12/15 — 6J secondary gates; 3) FX-F2 6B 12/15; 4)
  FX-F3 6B 12/15; 5) FX-F3 6E 12/15**. Tie-break cơ học (D4) đưa 2 gói
  6J6A lên đầu vì conditioning hoàn toàn strict-past in-repo — đây là điểm
  chất lượng gói, KHÔNG phải khẳng định schedulability (rank 1 nằm trên
  symbol PARK, rank 2 sau 3 gate 6J và chưa có cap). Mọi dòng ES BLK;
  NQ contingent-after-gates; comm NQV2.
- **CENSUS_FINAL**: điền đủ skeleton — ES **minimal 36 vs frozen 24,
  headroom 0** (bảng conflict riêng); FX ≈648 nếu chạy hết, **không ceiling
  nào**; 6J6A ≈29-36 minimal / 96+8 full; COMM **54 > 24** trên bất kỳ
  single-cycle nào; cross = 0 theo class; 6F = 0. Tổng giả định toàn program
  ≈1,068 full-grid (INFERENCE, quyước lẫn nhau — không được cộng trực tiếp).
  Câu hỏi placebo-budget chuyển owner nguyên văn, slot phán để trống.
- **BLOCKER_MATRIX** (11 symbol × 8 chiều, kèm JSON): headline — lịch
  expiry: ES 68/68 CLOSED, NQ 68/68, FX 208/272 (2023-26 NOT_OBTAINED), GC
  →Dec-2023, SI →Dec-2022, CL/NG rule+dates đầy đủ; phí 10/10 mã
  CORRECTED+UPHELD nhưng account NOT_RUN toàn bộ; **zero comm O1M là blocker
  dữ liệu lớn nhất**; BBO NOT_RUN program-wide; roll-rule 6A
  DECLARED-EXTRAPOLATION; 6F nguyên trạng NOT_RUN_DATA_ABSENT.

## Kiểm chứng cơ học của lane này (verify2/findings.json)

11/11 handoff: schema, dispatch_sha==actual_start_sha đúng theo batch;
`authority_claims != []` ở P2A/P2B (5-6 mục — là claim bằng chứng, không
phải claim quyền hạn; vi phạm cơ học, finding LOW); sha256 outputs recompute
— **0 mismatch nội dung**, 6 finding: 2 typo 1-ký-tự trong hash khai báo
(P0A COMEX.php.txt 65 ký tự — kèm phát biểu "17/17" của P0-VERIFY bị rộng
quá; P2C live_ics sai 1 ký tự), 1 placeholder "see file" (P2B
SHA256SUMS.txt), 1 self-hash disclosed (P1-ESNQ), 2 authority_claims
(P2A/P2B). **F-7 (MEDIUM)**: headline "43/45" của P2B không tái lập được
từ artifact của chính nó (grid thật 52/55 — understatement). Không lane
nào sửa tracked file (git status sạch; checkpoint `72c9bc5b` = 359 file
thuần addition trong round dir). Spot-recompute toàn bộ qua (ES 5 ngày +
68/68; 208/272; GC/SI; 6 claim BLS + 2016-04; 10/10 phí; ≥6 citation/lane
P1 — tất cả resolve). Quét ngôn ngữ cấm trên 32 file batch-2: **0 lần dùng
tích cực** (mọi hit là câu luật/phủ định). Verdict từng lane: P0A PARTIAL,
P0B VERIFIED, P2A PARTIAL, P2B PARTIAL, P2C PARTIAL, P0-VERIFY VERIFIED,
P1-ESNQ PARTIAL, P1-6E6B VERIFIED, P1-6J6A VERIFIED, P1-COMM VERIFIED,
P1-CROSS VERIFIED.

## Gate — KHÔNG gate nào thay đổi

NO_GO_REGISTER · NO_GO_SCORE · NO_GO_ORDER; PB2 HOLD; PB3 PARK; 6F
NOT_RUN_DATA_ABSENT; ES 24 identities frozen (headroom 0); NQ
sibling-after-cost/clock-gate; CL/NG/GC/SI PROVISIONAL-only. Mọi phí
MODELED COST, VERIFIED_VS_ACCOUNT=NOT_RUN, UNDER REVIEW đến A7 mới.

## Biên giới phiên (đã giữ)

0 scored, 0 PnL, 0 S1, 0 order/paper/live, 0 USD chi, 0 mua data/signup,
0 push/merge/rebase, 0 sửa tracked file, 0 đụng root main, 0 đụng
registry/ledger, 0 worker bị kill, heavy lock không lấy. Ghi duy nhất trong
`research/control/FUTURES-OVERNIGHT-PREP-20261003/{synth,verify2}/**` +
handoff lane này.

— Hết REPORT_VI. Mọi số truy về artifact lane + fetch_log; không có claim
PASS nào ngoài bằng chứng đã dẫn.
