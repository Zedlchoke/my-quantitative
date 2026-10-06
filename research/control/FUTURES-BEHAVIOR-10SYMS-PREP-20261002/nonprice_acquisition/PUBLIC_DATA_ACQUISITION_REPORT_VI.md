# PUBLIC_DATA_ACQUISITION_REPORT_VI — NONPRICE-DATA-ACQUISITION (tiếng Việt)

Task: `FUTURES-BEHAVIOR-10SYMS-PREP-20261002` · Lane `NONPRICE-DATA-ACQUISITION`
Ngày: 2026-10-02 · Base commit `8ce10f7e` (tree không đổi phần committed; mọi
output của lane nằm trong `nonprice_acquisition/**` + handoff).
Raw data NGOÀI git: `~/.my-quantitative-data/futures-nonprice-10syms/`
(10.579 file / **1,35 GB** — 66% cap 2 GiB; ổ đĩa còn ~42 GB free).

## ERRATUM 2026-10-02 (lane NONPRICE-FIX, theo audit A7-NONPRICE-VERIFY) — các con số cũ → mới

Audit độc lập A7 verdict `PASS_WITH_FINDINGS` (2 MAJOR, 5 MINOR). Lane
NONPRICE-FIX đã sửa; mọi số thay đổi nằm đây (nguyên văn các mục dưới phần
này giữ như đã xuất bản, số mới là thẩm quyền):

- **M-1 `net_change_bcf` (WNGSR tidy) — REBUILT.** Cột cũ lấy giá trị
  "net injection/withdrawal of X Bcf" ĐẦU TIÊN gặp trong issue → chỉ khớp
  phép kiểm độc lập (hiệu totals hai issue liên tiếp) ~**11%** (audit:
  62/561 = 11,1%; đo lại theo basis totals-bảng: 136/673 = 20,2%) — nhầm
  grabs gồm market-expectation/survey-bound/last-year/5-yr-average. REBUILT:
  (a) nguồn chính = bảng stocks của chính issue ("Working gas in underground
  storage … Total cur prior change", có kiểm nhất quán nội tại cur−prior=
  change; xử lý cờ C/R và mũi tên tái phân loại `-->`; phát hiện + loại
  bảng cũ date-stale trong file archive 2001-2015); (b) nguồn phụ = narrative
  neo-mục (loại câu region/season-cumulative/prior-week-reprint, kiểm
  'week ending' hợp lệ 4-8 ngày trước release); (c) kiểm độc lập = hiệu
  totals liên tiếp (tolerance 2 Bcf; check vô lý >400 Bcf → loại check, ghi
  rõ); (d) rows vẫn không khớp → **EXTRACT_LOW_CONFIDENCE, giá trị = NULL +
  reason** (không bao giờ giữ im lặng giá trị sai). Cột giờ **CÓ DẤU**
  (+injection/−withdrawal; cũ = không dấu). Kết quả: agreement
  **98,4% (752/764 hàng giữ giá trị có check; test ≥95%)**; cờ:
  733 OK_VERIFIED_TOTALS_DIFF · 9 OK_VERIFIED_NARR_NONCORROB · 10
  OK_PRIOR_WEEK_REVISED (revision có bằng chứng bảng) · 58+44 OK_TABLE* ·
  190 OK_NARRATIVE_ONLY · **27 EXTRACT_LOW_CONFIDENCE (nulled)** · 178
  NOT_PARSED (2004-2011 era phrasing chưa phủ + bảng stale). Giá trị legacy
  giữ ở cột `net_change_legacy_firstmention_bcf` (minh bạch erratum).
  5 case audit pin đúng: 2016-01-14 = −168 (cũ 178), 2016-03-17 = −1 (cũ
  19), 2018-10-11 = +90 (cũ 74), 2023-01-12 = +11 (cũ 157), 2019-03-14 =
  −204 (cũ 99). Regression test: 18 known-good + 5 misgrabbed pin exact.
- **M-2 readiness labels — re-derived mechanically (rules R1-R5 trong
  `build_readiness.py`).** CŨ: 34 READY_DATA · … MỚI: **27 READY_DATA**, +
  **4 PARTIAL_VINTAGE** (NQ-H1, GC-H5, CL-H4, 6E-H2: config đòi
  "first-release vintage mandatory" nhưng archive chỉ có snapshot
  ALFRED cuối-năm — per-release-day cần FRED key, OWNER_KEY_WAIT) và +
  **3 PARTIAL_MISSING_ROUTE** (6J-H3 thiếu TONA daily free-route — label
  READY_DATA cũ tự mâu thuẫn với piece MISSING_ROUTE của chính nó; ES-H4
  chân CPI-date calendar MISSING/BLS 403; 6B-H5 cùng luật CPI-date như
  ES-H4 — audit chỉ nêu ES-H4, mở rộng cơ học và disclose ở đây). Tên gap
  chính xác ghi trong từng piece. Rates-leg của ES-H2/SI-H3 (đã
  PARTIAL_PAID_OWNER) thêm caveat vintage-granularity ở mức piece.
- **Số liệu parse WNGSR:** totals parse 693/1.205 → **954/1.205** (2014+:
  93,17% → **98,81%**; nguồn = bảng stocks + narrative lọc region/forecast);
  survey median 352 → **369** issue (thêm biến thể "median estimate of net
  withdrawals of X Bcf"; NOTE-1 của audit).
- **BoJ statements: "181" → 180 trên đĩa** (114 PDF 2011-2017 + 66 HTML
  2018+; URL thứ 181 = PDF >4MB wait_storage, bản HTML cùng ngày có sẵn).
  Inventory tidy cũ chỉ có 66 HTML → giờ đủ **180** (test).
- **`issue_date_raw` không đáng tin (m-4)** → cột mới `issue_date` (1.169/
  1.205 từ header "Release date:", ISO) + `issue_date_source`; 1.185/1.205
  khớp ngày filename.
- **m-3:** file `fred_alfred/pit/DFII10/DFII10_asof_2024-12-31.csv` là probe
  CHẾT chứa vintage LATEST (param realtime bị bỏ qua — đã đo); raw bất biến
  nên giữ nguyên + fence test (không normalizer nào nạp; sha không xuất hiện
  trong bảng PIT nào) + ghi chú manifest.
- **m-2 (dedupe):** 60 cặp fetch trùng (url, sha) trong-session tồn tại
  trong manifest (58 ALFRED verify-pass, 1 CPC zip, 3 NCEI listing; sha
  giống nhau, không ảnh hưởng integrity); rule dedupe trong-session đã thêm
  vào `collect/common.py`; không đụng raw.
- **m-5 (BLS CPI calendar):** config ghi "FACT, fetched" (12/2026 dates,
  dossier lane) KHÔNG tái kiểm chứng được từ raw nonprice (BLS 403 với lane
  này) — wording trong readiness đã đổi thành "config-claimed FACT, cần
  cross-lane reconciliation"; date-level CPI calendar giữ typed MISSING.
- **Tests: 29/29 → 41/41 PASS, exit 0** (12 regression mới: 5 misgrab pins,
  18 known-good pins, quarantine-null, agreement ≥95%, survey pins 3 issue,
  issue_date robust, readiness 3 luật, BoJ 180, DFII10 fence).

## ERRATUM 2026-10-03 (lane INTEGRATION-FIX-V2, task FUTURES-DEEPRESEARCH-V2-20261003) — CFTC tidy trộn market-line

Khiểm chứng độc lập của 2 lane DEEP (DEEP-NQ + DEEP-ES) phát hiện cùng một lỗi
trong `normalize/cftc_normalize.py`: matching market theo **substring** làm
một `series_id` gộp nhiều dòng CFTC cùng ngày (Consolidated + Mini/Micro + ICE
…). Đã sửa tại nguồn bằng **exact market-name mapping** (bảng tên chính xác,
strip khoảng trắng; kiểm trên cả 21 file deacot 2006-2026; CFTC đổi tên giữa
2022 → giữ cả 2 chính tả, union mỗi symbol = 1.082 tuần, 0 ngày trùng).

- **`cftc_legacy_tidy.parquet` CŨ (sha256 `4f9cd789…`) → MỚI (sha256
  `f7a2719e…`)**; bản cũ giữ ở `cftc_legacy_tidy.parquet.bak_prefix_mixed_20261003`.
  Số dòng bị trùng ngày theo series (cũ → mới = **0** trên cả 10): **ES 1.126,
  CL 928 (gộp cả WTI ICE Europe vào NYMEX!), NQ 548, GC 164, NG 10, SI 5**;
  6A/6B/6E/6J 0. Chuỗi `COT_LEGACY_NQ` cũ **chỉ bắt đầu 2010-06-15** (dòng
  Consolidated; e-mini `'NASDAQ-100 STOCK INDEX (MINI)'` không bao giờ được
  gom) → mới về **2006-01-03** đủ 1.082 tuần như 9 symbol còn lại (mục "NQ
  consolidated bắt đầu 2010-06-15 = ngày series chính thức" ở bảng mục 1 dưới
  chỉ còn đúng cho dòng ALT).
- **Cấu trúc mới:** 10 series chuẩn `COT_LEGACY_{SYM}` = đúng 1 market line
  (khớp plane vendor: NQ/ES = E-mini, FX = 1 dòng CME, CL = WTI NYMEX outright,
  NG = Henry Hub NYMEX, GC/SI = COMEX); các dòng anh em (Consolidated,
  Micro, pit full-size, ICE, E-miny-typo) **giữ nguyên dữ liệu** dưới id
  `COT_LEGACY_{SYM}__ALT__{SLUG}` (14 series / 4.527 dòng legacy) — không xóa
  dữ liệu, không trộn vào series chuẩn. Tổng legacy 13.369 → 15.347 dòng
  (thêm NQ e-mini 2006-2010 + full-size pit NQ/ES từng bị sót).
- **TFF/disagg tidy cùng lỗi substring** → tái sinh cùng luật exact:
  cũ `d798ed27…` (17.337 dòng trộn) → mới `1dbb5e93…` (15.170 dòng:
  10.766 chuẩn + 4.404 ALT); giá trị vẫn ~null metadata/backcast như đã caveat.
- **Tương thích dossier V2:** DEEP-ES (lọc exact E-mini 1.082 tuần) ==
  series chuẩn mới; dòng DEEP-NQ dùng (NASDAQ-100 Consolidated, 850 tuần,
  2010-06-15→2026-09-22, OI median 2010-2013 = 94.852/89.278/91.118/78.607)
  reproduce 1:1 từ id ALT; DEEP-6B dùng as-is == chuẩn 6B. Không số nào trong
  dossiers_v2 đổi.
- **Tests: 41/41 → 48/48 PASS, exit 0** (7 regression mới: 0 duplicate-date
  trên 10 series + pin số dup cũ, 1.082 tuần/symbol, ALT không trộn, 3
  spot-check NQ/ES/6B theo số lane DEEP, contaminant CL/GC/SI/NG chỉ còn dưới
  ALT).

## ERRATUM 2026-10-03 (lane NONPRICE-SOURCE-FIX2, task FUTURES-DEEPRESEARCH-V2-20261003) — MOF thiếu 305 ops + fin tidy trùng archive-overlap

Theo audit A7-DEEP-6J (**M-1, n-2**) + A7-INTEGRATION (**F-1..F-5**). Lane chạy
dở vì **cúp điện giữa chừng** (INCIDENT): mọi trạng thái từng phần đã được
kiểm chứng lại từ raw trước khi tiếp tục (chi tiết ở handoff lane).

- **MOF daily ops: 81 → 386** (parquet sha `6a5ce702…`; bản 81-row giữ ở
  `mof_intervention_tidy.parquet.bak_81rows_20261003`). Parser cũ đòi mỗi
  hàng mang cột Year VÀ MonthEN riêng; CSV chính thức dùng merged-cell
  (tháng chỉ ghi ở hàng đầu mỗi khối) → **rơi đúng 305/386 ops** (mọi hàng
  rơi đều có tháng trắng; census 386−81 = 305 — audit văn nói "300" là làm
  tròn). Fix: carry-forward tháng khi trắng, như năm đã làm. Hồ sơ đủ:
  **386 ops 1991-05-13→2026-05-06** (369 ngày riêng biệt; 17 cặp cùng-ngày =
  đa ngoại tệ trong ngày, KHÔNG phải duplicate) — KHÔNG phải "1991-04" như
  header mục 1 cũ. **Op 2022-10-24 ¥0,73T (JPY-buying) được phục hồi** (raw
  row 519, năm+tháng trắng; Q4-2022 56.202+7.296 = 63.498 vs hàng kỳ tổng
  63.499, +1 đơn vị làm tròn của MOF); **ops trong cửa sổ 2020+ = 10, không
  phải 9** → dossier DEEP-6J ("81 ops", "9 ops in-window", bảng §5) kế thừa
  undercount — erratum thuộc lane dossier đó. Set-parquet == recount raw
  (0 thiếu/0 thừa, test).
- **Fin tidy (TFF+disagg) dedupe theo audit F-1:** bản tái sinh của
  INTEGRATION-FIX-V2 (`1dbb5e93…`, giữ ở `.bak_dup_overlap_20261003`) vẫn
  đọc đôi archive chồng lấn (`fut_disagg_txt_hist_2006_2016.zip` /
  `fin_fut_txt_2006_2016.zip` + annual 2010..2016) → **1.825 hàng trùng**
  (DISAGG chuẩn 365×4 = 1.460 + CL __ALT__ ICE 365) trên 2010-01-05..
  2016-12-27. Fix = dedupe với **precedence annual-wins** (annual = bản xuất
  thường niên liên tục; bulk = re-pack đóng băng; giá trị trùng nhau trừ 9
  cell sai số làm tròn `Pct_of_OI_*`/`Change_in_*` trên 9 series-ngày — tất
  cả disclosed, giữ giá trị annual). Cùng đợt sửa 2 lỗi cùng lớp: (b) date
  parser ISO-only làm rơi nguyên file TFF bulk (ngày `M/D/YYYY`) → TFF chuẩn
  845 → **1.059 rows, floor 2006-06-13**; (c) value-column filter theo
  schema legacy → TFF all-NaN, disagg mất `M_Money_*`/`Open_Interest_All` —
  giờ mang mọi cột non-metadata. File mới **`c3ba5391…`** (15.065 dòng =
  10.590 chuẩn + 4.475 ALT; 23 series, 0 duplicate-date, gate
  `assert_fin_clean` + generation-time conflict log).
- **INCIDENT (cúp điện) — bản trung gian bị ngược precedence:** lane dở để
  lại file sha `3e32e0ee…` (giữ ở `.bak_bulkwins_20261003`) với sort/keep
  **ngược** luật đã ghi (bulk thắng annual). Resume pass bắt được bằng pin
  cell COT_TFF_6A 2016-05-31 (raw: hist 24,0 vs annual 23,9; file trung gian
  mang 24,0/bulk). Đã sửa code, tái sinh `c3ba5391…`; diff so bản trung gian
  = đúng 4 cell numeric (các xung đột 0,0/−0,0 so sánh bằng) + 4.983 hàng
  đổi provenance về zip annual.
- **Đính chính F-3 cho erratum của INTEGRATION-FIX-V2 ở trên:** dòng "cũ
  `d798ed27…` (17.337 dòng trộn)" là **SAI** — file cũ thật = **13.898
  dòng** (audit đo từ DATA-BACKUP mirror SHA-verify 23:30 UTC 2026-10-02 +
  rerun code git-HEAD: DISAGG CL 2.708 / GC 1.588 / NG 1.434 / SI 1.429; TFF
  ES 1.966 / NQ 1.393 / FX 845×4). Con số 15.170 của `1dbb5e93` đúng. Lưu ý:
  mirror iCloud hiện đã là bản `1dbb5e93` (được sync sau lane đó) — cần
  re-sync sau lane này.
- **Đính chính 2 md analysis/integration** (F-2/F-4/F-5/N-2):
  `nq2020_hole_probe.md` — NQJ0 là **HTTP 504 timeout** (không phải "422
  unresolvable/not in feed"; serial coverage = NOT_RUN), probe = **8 calls**
  (không phải 7; record_count ×6 + get_cost + billable_size, đều free),
  "alias duy nhất" sai — sweep 6-root tìm thấy thêm instrument **2563**
  (`NQH5-NQM5` 2014-12..2016-05, 5.946 bars/395.166 contracts, deferred-scale
  → khuyến nghị khái quát hóa view-rule theo family+time-contiguity) và
  **2173** (1 bar `ESU6-ESU7` lạc trong ES-delta + đuôi `6BX1` trong 6B
  backfill2 — id va chạm cross-family, không remap); "51 = weekday count" →
  58 phiên = 49 weekday + 9 Sunday-open Globex. `contaminant_scan.md` — tổng
  spread bars **2.637.950 → 2.537.950** (tổng per-root vốn đúng; prose hơn
  đúng 100.000).
- **Tests: 48/48 → 59/59 PASS, exit 0** (11 regression mới: 5 pin MOF — 386
  ops/1991-05-13, pin 2022-10-24, 10 ops 2020+, Q4-2022 khớp kỳ tổng, set ==
  recount raw; 6 pin fin — 0 duplicate-date mọi series, DISAGG 1.059
  full-span, TFF floor 2006, value columns có mặt, pin precedence
  annual-wins 23,9/`fut_fin_txt_2016.zip`).

## 1. Đã tải gì (tổng quan theo nguồn — tất cả PRIMARY official, miễn phí, không key)

| Nguồn | Files | Bytes | Coverage thật | PIT-legal ngay? |
|---|---:|---:|---|---|
| CFTC CoT (legacy futures-only + TFF + disaggregated) | 59 | 85,8 MB | 2006-01-03 → 2026-09-22 (NQ consolidated bắt đầu 2010-06-15 = ngày series chính thức) | **CÓ** cho legacy as-published (không revise sau khi phát hành; as-of Thứ Ba ≠ release Thứ Sáu 15:30 ET đã tách bảng). TFF/disagg = backcast classification → chỉ descriptive, không phải vintage thật (caveat đã encode) |
| FRED latest + ALFRED vintages | 193 | 21,1 MB | 12 series latest full-history (DFII10, DGS10, DGS2, T10YIE, DTB3, SOFR, DFF, FEDFUNDS, DFEDTARU, DTWEXBGS, CPIAUCSL, PAYEMS) + **122 vintage snapshot** cuối-năm 2010→2025 + 2026-09-30 | **CÓ** ở mức snapshot theo năm (route `vintage_date` đã verify cột mang đúng ngày as-of). Latest được flag `latest_revised_NOT_PIT`. Vintage theo-từng-ngày-phát-hành KHÔNG lấy được không key (host rate-limit nặng) → cần owner key nếu muốn mịn |
| EIA WNGSR (weekly gas storage) | 1.460 | ~150 MB | **1.205 issue HTML 2001-05→2026-01 + 254 issue PDF 1996-05→2001** (floor config 1994 → archive thật bắt đầu 1996, đã disclose) + schedule page (holiday moves) | **CÓ** — mỗi issue = 1 vintage as-published; tổng storage parse tidy 693/1.205 (2014+ ≈ 93-100%; pre-2014 còn nguyên file raw để parse tiếp) *(ERRATUM: 954/1.205, 2014+ 98,81% sau khi thêm bảng stocks làm nguồn totals — xem block ERRATUM)* |
| EIA WPSR (weekly petroleum) | 3.910+ | ~143 MB | **790 issue 2011-01-07→2026-09-30** + 3.120 bảng as-published (table1/3/4 CSV + table13 PDF) + errata sheet + 2 series dnav revised-latest đối chiếu | **CÓ** — table1/table4 tidy đủ 790/790 tuần: crude commercial, **Cushing stocks** (hàng "Cushing" trong table4), gasoline; mỗi tuần = 1 vintage |
| Fed FOMC | 159 | 13,4 MB | Lịch 2010→2026 (fomccalendars + fomchistorical 2010-2020) + **147 statements 2011-01→2026-09** (2010: có NGÀY họp trên calendar page; statement 2010 route không tìm ra — gap nhỏ đã typed) | **CÓ** — statement as-issued; giờ release 14:00 ET là convention công bố |
| ECB / BoJ / MOF / BoE / ONS / gov.uk / RBA | 226 | 57,0 MB | €STR daily 2019+; ECB MRO rates; **BoJ 181 statements 2010→2026** (PDF 2010-17 + HTML 2018+) + MPM calendar; **MOF CSV can thiệp tỷ giá THEO NGÀY 1991-04→2026** (bản gốc Shift-JIS, 81 thao tác) + quarterly EN 2019+; BoE Bank Rate 56 mốc 2000→2025 + **gilt nominal daily curve zip**; ONS calendar hiện tại + dataset CPI; gov.uk autumn-statement collection | MOF/BoJ/FOMC/ECB-ESTR: **CÓ** (as-published; MOF inherent lag công bố ~1 tháng/quý — không same-day PIT, config đã ghi nhận). BoE gilt = **DECLARED_LAG** (chỉ latest-vintage, không có vintage miễn phí). ONS lịch lịch-sử = MISSING route. *(ERRATUM: BoJ 181 = URL enumerate; 180 trên đĩa — xem block ERRATUM)* |
| NOAA CPC issued forecasts + observed | 4.565 | 877,6 MB | **6-10 ngày TEMP: 4.459 issue/ngày liên tục 2012-09-11→2025-06-30** (archive thật bắt đầu 2012-09, không phải 2010-06) + 65 mẫu tuần (Thứ Hai) 2025-07→2026-10 (regime file 3,3MB ăn disk); 8-14 ngày: pilot 31 ngày 2026-09→2026-10; **HDD/CDD chính thức theo climate-division 1895-01→2026-10** (2 file bulk 4,6MB) + weights census TIÊN-ĐỊNH | CPC: **CÓ** (issued_at = ngày issue, tách bảng khỏi observed). Observed = outcome/regime context, KHÔNG BAO GIỜ là feature vào lệnh. GFS/NDFD vintages nhiều năm = **KHÔNG truy cập được free** (bucket không version hóa — đã đo) → NOT_RUN_PIT cho mảnh đó |
| GDELT | 0 | 0 | — | **OPTIONAL_SKIPPED** — không hypothesis nào cần; nguồn primary đã phủ mọi nhu cầu được đặt tên; route free bắt buộc tải cả ngày dữ liệu to |

Tổng: **10.579 file ok / 1.348,1 MB** (không có file nào bị xóa; 11 bản ghi
`wait_storage` + các bản ghi 403/404 gate giữ nguyên trong
`raw_manifest.jsonl` như evidence — sha256
`339d022b53c969312af37595dad2b30b0bbc2777ef9d338d165cba684f34d364` tại thời
điểm đóng; manifest là append-only nên con số này tăng theo mỗi lần chạy).

## 2. Chứng minh PIT (29/29 parse tests PASS — `tests/test_parse.py`) *(ERRATUM: 41/41 sau NONPRICE-FIX — xem block ERRATUM)*

- revised-latest ≠ PIT vintage: bảng fred latest và fred vintage tách nhau
  bằng `vintage_flag`; test join tìm giá trị khác nhau giữa snapshot as-of và
  latest (series có revise sẽ khác).
- released_at ≥ observation_period: CFTC test khoảng 2→7 ngày (Thứ Ba → Thứ
  Sáu kế tiếp) PASS toàn bộ 13.369 dòng legacy.
- issued vs observed weather: 2 bảng parquet riêng, `series_id` rời nhau PASS.
- CFTC as-of vs release: tách cột, convention encode PASS.
- Không có dòng nào "tương lai" so với hôm nay (2026-10-02) trên mọi bảng PASS.
- WNGSR survey median (The Desk) extract được ở 352 issue — **bất ngờ lớn**:
  issue WNGSR as-published NHÚNG consensus pre-release (median/range của survey
  The Desk) → đây là bản ghi consensus MIỄN PHÍ as-published cho NG storage.
  Owner thẩm định fitness (nó không phải vendor consensus archive đầy đủ).
  *(ERRATUM: 369 issue sau khi thêm biến thể phrasing "median estimate of net
  withdrawals of X Bcf" — xem block ERRATUM.)*

## 3. Trạng thái từng hypothesis (50/50) — `hypothesis_readiness.json`
*(ERRATUM NONPRICE-FIX — số MỚI thẩm quyền: **READY_DATA 27** (−7), +
**PARTIAL_VINTAGE 4** (NQ-H1, GC-H5, CL-H4, 6E-H2) và +
**PARTIAL_MISSING_ROUTE 3** (6J-H3, ES-H4, 6B-H5); các nhóm khác không đổi;
đầy đủ ở block ERRATUM đầu báo cáo.)*

- **READY_DATA: 34** (những thứ nonprice yêu cầu đã có, hoặc hypothesis
  không cần dữ liệu ngoài nào — phần price-depth còn thiếu là lane khác).
- **BLOCKED_CONSENSUS: 7** (NQ-H3, ES-H3, GC-H2, CL-H2, 6E-H3, 6E-H4, 6B-H2) —
  không có archive consensus as-issued miễn phí hợp pháp; TUYỆT ĐỐI không thay
  actual vào chỗ expected. (NG-H1 vốn thuộc nhóm này nhưng được tính PARTIAL
  nhờ The Desk survey nhúng trong WNGSR — xem dưới.)
- **PARTIAL / PARTIAL_*: 6** — NG-H1 (consensus một phần qua WNGSR survey;
  M1 vendor còn thiếu), NG-H2 + NG-H4 (CPC issued READY từ 2012-09; GFS/NDFD
  vintages nhiều năm KHÔNG có free → NOT_RUN_PIT cho mảnh đó), 6B-H3 (gilt
  DECLARED_LAG + lịch fiscal UK một phần), 6J-H3 (thiếu TONA daily free-route),
  ES-H2 + SI-H3 (rates READY, dividend-yield/lease-rates trả phí).
- **VENDOR_PAID / PAID_OWNER_WAIT: 4** (6A-H2 HG+iron-ore; mảnh paid của
  ES-H2/SI-H3; CL-H3 RB/HO).
- **MISSING: 1** (GC-H1 serial-refetch = hành động entitlement IBKR của lane
  data, không phải nonprice-public; time-critical ~Q1-2027).

Đếm nhanh theo hypothesis-id: 34 READY · 7 BLOCKED_CONSENSUS · 2 PARTIAL_PAID_OWNER
(ES-H2, SI-H3) · 2 PARTIAL_NOT_RUN_PIT_GFS (NG-H2, NG-H4) · 1 PARTIAL (NG-H1) ·
1 PARTIAL_DECLARED_LAG (6B-H3) · 1 VENDOR_PAID_PARTIAL (CL-H3) · 1 VENDOR_PAID
(6A-H2) · 1 MISSING (GC-H1).

## 4. Cái gì chỉ descriptive / DECLARED_LAG

- FRED/ECB/BoE **latest** series (không vintage) — chỉ descriptive.
- BoE gilt curve (latest-vintage) — jump-filter descriptive; vintage-grade
  NOT_RUN_PIT.
- TFF/disagg CoT histories — backcast classification.
- ONS UK CPI hiện tại; CPC 610temp sau 2025-07 chỉ mẫu tuần (3,3MB/file).
- WNGSR tidy pre-2014 parse một phần (raw giữ đủ 100%).

## 5. Blockers (đã type đúng)

| Kiểu | Chi tiết |
|---|---|
| BLOCKED_CONSENSUS | 7 hypothesis trên; không bypass, không fabricate |
| NOT_RUN_PIT (GFS/NDFD vintages) | bucket AWS NDFD không S3-version (đo được 1 version duy nhất); NCEI AIRS là request-based; GFS nhiều năm > cap |
| WAIT_STORAGE (nhỏ) | 3 file CPC 610temp lẻ tiếp >1MB (2013/2018); climdiv tmax/tmin `-inv` >48MB (bỏ chủ đích — file HDD/CDD chính thức 4,6MB đủ); 1 pdf BoJ >2MB (bản HTML cùng ngày có sẵn) |
| 403/404 gate (đã ghi, không bypass) | BLS (toàn site), RBA (rba.gov.au), ir.eia.gov (trừ schedule.html), CPC /products/archives/*, gov.uk budget-collection |
| OWNER_KEY_WAIT (chỉ nếu cần mịn hơn) | FRED API key cho vintage theo-ngày-phát-hành (năm-cuối đã có free) |
| MISSING route | ONS lịch sử + first prints UK CPI; BoJ TONA daily free; FOMC statements 2010 (PDF route không tìm ra); Budget-documents collection gov.uk |

## 6. Số liệu vận hành

- HTTP requests ok: 10.579 (rate-limit 0,15-1s tùy nguồn, retries có giới hạn,
  backoff nhân; dedupe bằng sha256 → chạy lại không tải lại).
- Bản ghi lỗi đã lưu: 1.960 (đa số là các attempt sai-pattern đã được thay bằng
  pattern đúng — CFTC disagg/tff, WPSR thiếu đuôi .php, WNGSR dir-root cũ, MOF
  quarterly EN pre-2019; log append-only giữ tất cả làm evidence).
- Disk: 1,35 GB / cap 2 GiB raw+derived (noaa subcap 1,1 GiB: đã dùng 878 MB).

## 7. Owner cần làm gì tiếp

Xem `OWNER_ONLY_STEPS.md` (chỉ các bước thật sự chỉ owner làm được: FRED key
nếu muốn vintage mịn, các quyết định PAID: consensus/LBMA/dividend-yield/
iron-ore/Databento; KHÔNG đòi key cho nguồn đã đủ bằng file-public).
