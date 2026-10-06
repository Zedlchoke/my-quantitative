# SUMMARY_QUAL_ACTIONS — vòng qualification r6 (2026-10-03)

Theo chỉ thị Co-Owner trên prep @`73abf15c`. **Không đăng ký cycle, không
freeze spec, không scored/PnL, không S1, không paper/live/order, không mua
data, không push/merge, không đụng root main; NO_GO_REGISTER/SCORE/ORDER giữ
nguyên.** Mọi lane không commit; A1 tích hợp. Verdict dưới đây là của lane,
Lead đã kiểm chứng artifact tồn tại + JSON parse OK (log tích hợp trong git
commit r6).

## Bảng verdict từng mục

| mục | việc chạy thật | verdict | blocker thực tế còn lại |
|---|---|---|---|
| **D1 slippage** | không cần hành động (đã là luật: giả định {1,2,3 tick}/chiều, cấm stress nhân đôi) | RECORDED | chỉ thành measured khi có fill/BBO thật (không mua) |
| **D2 phí ES** | Lane D2-FEESRC: IBKR pricing page LIVE_OFFICIAL (web_reader 2026-10-03; WebFetch vẫn 403 như đo cũ); bảng theo **plan/tier**: Fixed 0.85; Tiered 0.85/0.65/0.45/0.25 (+exchange +regulatory +overnight-fee NOT_FETCHED); components exchange 1.386 + regulatory 0.011 (IBKR CME.php offset table, LIVE_OFFICIAL); all-in tính từ components = **2.247** (tier ≤1k) — khớp ví dụ 2.24 của IBKR; NFA timeline chính thức 0.02→0.01(2014)→0.02(2018). CME HTML không với tới mọi đường; PDF CME 2020/2025/2026 có nhưng **không trích được cell** (không đoán). Historical 2010-2026: đa số năm phải **CURRENT_SCHEDULE_AS_APPROXIMATION** (ghi rõ caveat); **$2.24 giữ nhãn DOC_EXAMPLE_NOT_ACCOUNT_VERIFIED**; mọi dòng SOURCE=PUBLIC_REFERENCE, VERIFIED_VS_ACCOUNT=NOT_RUN; đã ghi rõ **D6 re-fetch không thay thế account fee evidence**; broker LIVE dự kiến = IBKR | **PASS (public-reference)** | **đối chiếu account thật: NOT_RUN** — owner đang xin chứng từ đã che thông tin; plan/tier account chưa biết; overnight-position fee chưa fetch |
| **D3 lịch CME (ƯU TIÊN)** | Lane D3-CMECAL: holidays + early-closes **17/17 năm (2010-2026) authority-backed**: 2026 LIVE_OFFICIAL (trading-hours.html fetch sống 2026-10-03 — **403 cũ không tái lập, ghi như re-measurement có ngày**); 2010 ARCHIVED_OFFICIAL từ PDF chính thức 38 trang (chi tiết từng ngày/giờ cho họ Equity/ES); 2011-2025 ARCHIVED_OFFICIAL (verbatim window tables; capture quyết định 20241112201950). **Expirations: 36/68 quý ARCHIVED_OFFICIAL** (đủ 2012-2018 + 2025; một phần 2010/2011/2024); **NOT_OBTAINED: 2019-2023 + 2026** (khoảng trống Wayback 2017-04→2020-09; sau đó React shell/account-gated) — **không suy diển lấp gap**; 1 anomaly 2017 (cell stale 2016) đã re-verify. ES-specific 2026 Globex times nằm sau widget ⇒ NOT_OBTAINED từ static HTML. Kỷ luật truy cập: ≤2 lần/URL/phương thức, không spoof UA, không proxy (không bypass) | **PASS với coverage khai báo** | ngày không chắc ⇒ EXCLUDE/NOT_RUN (luật); expirations 2019-2023+2026 thiếu authority; ES 2026 giờ cụ thể thiếu; 5 mã CME còn lại cần trích từ cùng bộ bằng chứng (chưa làm trong phiên) |
| **D4 verify ECB** | Lane D4-ECBVERIFY: **10/55 → 55/55 machine-verified** (HTTP 200 + title + date-string từng ngày; 54 "Monetary policy decisions"; 2020-03-18 là biến thể tiêu đề PEPP — disclosed); tuyến phụ độc lập: 19/19 ngày hiệu lực MRO (ECB SDW tươi) khớp trọn tập hợp; enumeration giải qua search backend công khai của chính site ECB (cùng call trình duyệt thường lệ), KHÔNG bypass; Wayback CDX vẫn 503 (đã ghi) | **PASS** | không còn cho Bước-1 ECB; **PB2 vẫn HOLD** (không mở gì tự động) |
| **D5 schema/quote ES** | Lane D5-ESSCHEMA (read-only, in-repo): schema sạch ổn định (fixed-point 1e-9; instrument_id 1:1 vs definitions; **không có trường publication** trong bản trim); **tick grid tuyệt đối trên outright** (0/478,951) nhưng **calendar-spread trộn cùng file (79-84% off-grid) ⇒ lọc `-` bắt buộc**; **ts_event = mốc BẮT ĐẦU bar** (bar "16:00" thực là bar đóng 15:59); **IBKR daily close = settlement mark CME — khớp tick-for-tick 96/96**; last-trade 16:00 CT vs IBKR lệch median **18 ticks**; proxy S6 reproduce **exact** (median 1.0 tick = $12.50, cùng phiên BID/ASK close); analogue vendor 2.0 ticks (thiên cao); volume 1m ≈ 1.19× IBKR daily (reconciliation chính xác NOT_RUN) | **PASS** | không BBO (không mua; bbo-1m cũng không chứng minh fill/queue) — mọi fill claim giữ conservative; MODELED COST |
| **D6 IBKR re-fetch** | Lane D6-IBKRREFETCH: inspect fut10_probe.py (TWS socket 127.0.0.1:7497, readonly, không credential trong script; gateway chủ đang sống); **canary PASS**; 25 request tuần tự (2.5s pacing, clientIds readonly); **6 file staged** vào `~/.my-quantitative-data/futures-10syms-v1/staging_refetch_20261003/` + sha256 manifest; **0 ghi vào raw/** (verify); fronts không đổi; newly-listable 0; **tường expired chưa lùi ở chu kỳ 1 ngày** (walls ES/NQ=202509, FX=202512) | **PASS** | re-fetch là việc **định kỳ hàng tuần** (wall lùi dần); staging cần owner/phiên sau promote vào raw theo luật; không đụng manifest gốc |
| **D7 6F** | không hành động | **NOT_RUN_DATA_ABSENT** (giữ) | owner quyết định mua sau |

## Ảnh hưởng lên gate (không tự mở gì)

- **Bước-1 dimension "Holiday" cho ES: nâng cấp từ NOT_RUN → OBSERVED với
  coverage khai báo** (17/17 năm holidays/early-closes; expirations 36/68;
  uncertain ⇒ EXCLUDE/NOT_RUN). 5 mã khác chờ trích cùng bộ bằng chứng.
- **Bước-1 dimension "Event PIT" cho 6E: ECB PARTIAL → PASS_EVIDENCED 55/55**
  (PB2 vẫn HOLD theo phán quyết).
- **Cost authority: vẫn chưa đủ freeze** — cần chứng từ account thật (owner
  đang xin) + quyết định dùng biểu nào cho năm lịch sử
  (CURRENT_SCHEDULE_AS_APPROXIMATION phải khai rõ; NFA đổi 2014/2018; CME tăng
  giá trong cửa sổ).
- **A-r4 (24 identity) vẫn PROJECTED SCOPE, chưa freeze.** PB1 [PROVISIONAL]/
  BLOCKED; PB2 HOLD; PB3 PARK; NO_GO_REGISTER/SCORE/ORDER giữ nguyên.
- Chi tiết làm mới cho spec tương lai (ghi nhận, không tự áp vào playbook
  trong phiên): ts_event=interval-start; IBKR daily close=settlement mark;
  18-tick gap 16:00-last-trade-vs-settlement; lọc dash-symbol bắt buộc.

## Đường dẫn bằng chứng

`analysis/d3_cmecalendar/{ES_CALENDAR_EVIDENCE.md, cmecal_coverage.json}` ·
`analysis/d2_feesrc/{ES_FEE_SOURCES.md, fees_table_es.json}` ·
`analysis/d4_ecb/{ECB_VERIFY_REPORT.md, ecb_dates_verification.json}` ·
`analysis/d5_esschema/es_schema_eval.{md,json,py}` ·
`analysis/d6_ibkr/{d6_report.md, d6_fetch_log.json, d6_staging_manifest.json,
canary.json}` · handoff `zcode_orch_v3_handoff@1` đầy đủ trong `dispatch/`.

— Hết SUMMARY_QUAL_ACTIONS r6. Mọi số truy về artifact lane; không có claim
PASS nào ngoài bằng chứng đã dẫn.
