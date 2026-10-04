# FINAL_REPORT — FUTURES-DATA-10SYMS-V1 (2026-10-02)

Lane dữ liệu độc lập theo lệnh owner 2026-10-02 (verbatim: `dispatch/OWNER_DIRECTIVE_2026-10-02.md`).
0 scored cells, 0 PnL, 0 orders, 0 subscriptions/purchases, 0 credentials, không
push/merge. Không đăng ký cycle (disclosure trong INTAKE.md, precedent
DATA-FOUNDATION-SIXSOURCE-V1). Không mở lại cycle TERMINAL nào.

Trạng thái đóng phiên: heavy lock FREE_PROVEN (không từng chiếm); đĩa 24 GiB trống
(raw session 36.1 MB, trần công bố 2.0 GB không chạm); root checkout `main` —
HEAD di chuyển 6770d790 → cfb7ae57 do owner commit song song trong phiên (không
đụng file của session này); mọi artifact session là untracked, owner duyệt và commit.

## Kết luận 1 câu cho 10 mã

**Cả 10 mã đều SIGNAL_RESEARCH_READY = PASS** (daily từng hợp đồng rõ đáo hạn,
tách được settlement, timezone đúng, quy ước giá xác minh). **Không mã nào đạt
DAILY_FUTURES_BACKTEST_READY hay INTRADAY_FUTURES_BACKTEST_READY ở độ sâu
nhiều năm** — cả hai nhãn BLOCKED ×10 vì hai bức tường đo được: (1) secdef hợp
đồng hết hạn chỉ resolve được ~1 năm, nên chuỗi front-month volume-thật chỉ liên
tục từ ~2025-08→nay (~14 tháng); (2) intraday (H1/M1) chỉ lưu ~10 tháng (NG
~2.2 năm). Trước 2025 dữ liệu per-contract vẫn có nhưng là bar close-only
volume-0 (settlement-derived) — dùng làm giá tham chiếu/signal được, làm giá
khớp lệnh thì KHÔNG.

## Bảng 10 dòng

| Mã | Venue | Dữ liệu mới đã tải | Độ sâu daily (per-contract) | H1/M1 đã tải | Số HĐ thực | Quote live/delayed | HMDS lịch sử | Chất lượng | Chi phí đo được | SIGNAL | DAILY_BT | INTRADAY_BT | Blocker chính | Hành động mở khóa rẻ nhất |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| NQ | CME | 10 HĐ × (daily 6Y + H1 30D + M1 2D + BID/ASK 1Y) | từ 2022-05 (front NQZ6 cả đời); sâu hơn bị cắt bởi dur 6Y | H1/M1 chỉ ~10 tháng gần (2026) | 10 (5 expired 202509→) | KHÔNG (type1/type3 đều rỗng) | PASS 7/7 | front thật; 88% bar close-only trong đời HĐ; 0 crossed | spread front 6.5 tick=$32.5; comm $0.85+exch (ES-doc $2.24 style) | PASS | BLOCKED | BLOCKED | tường expired ~1 năm + intraday ~10 tháng | vendor lịch sử (owner quyết), hoặc tích lũy prospective |
| ES | CME | 10 HĐ × 5 job types | từ 2021-06 | H1 ~2025-11, M1 gần | 10 (5 expired) | KHÔNG | PASS 7/7 | front thật (ESU6 169 ngày volume liên tục); flat 66-99% toàn đời | spread 1.0 tick=$12.5; all-in doc $2.24/side (IBKR ví dụ chính thức) | PASS | BLOCKED | BLOCKED | như NQ | như NQ |
| CL | NYMEX | 28 HĐ × 5 job | từ 2019-09 | H1 ~2025-11, M1 ~2025-12 | 28 (12 expired, liền mạch 202510→202609) | KHÔNG (err 10168/300) | PASS 7/7 | front thật; ~25% flat ở HĐ thanh khoản, 75-90% ở HĐ xa | spread 3 tick=$30; comm $0.85+exch NOT_FETCHED | PASS | BLOCKED | BLOCKED | như NQ | như NQ |
| NG | NYMEX | 28 HĐ × 5 job | từ 2019-09 | H1+M1 sâu nhất nhóm: ~2023-11 | 28 (12 expired liền mạch) | KHÔNG (err 10168/300) | PASS 7/7 | như CL; front medv thấp hơn CL | spread 2 tick=$20 | PASS | BLOCKED | BLOCKED | expired ~1 năm (intraday tương đối tốt nhất) | như NQ |
| GC | COMEX | 22 HĐ × 5 job | từ 2019-12 | H1 ~2025-11, M1 ~2025-12 | 22 (6 expired 202510→) | KHÔNG | PASS 7/7 | front thật; HĐ xa 100% flat | spread 5 tick=$50 | PASS | BLOCKED | BLOCKED | như NQ | như NQ |
| SI | COMEX | 22 HĐ × 5 job | từ 2020-12 | H1 ~2025-12, M1 ~2025-12 | 22 (6 expired; đúng tradingClass SI 5000oz — không nhầm SIL 1000oz) | KHÔNG | PASS 7/7 | 1 ngày crossed book/251; HĐ xa mỏng | spread 4.5 tick=$112.5 | PASS | BLOCKED | BLOCKED | như NQ | như NQ |
| 6E | CME | 20 HĐ × 5 job | từ 2020-12 | M1 ~2025-12 (quarterly 6EZ6) | 20 (4 quarterly expired 202512→; serial tháng liệt kê đầy đủ) | KHÔNG | PASS 7/7 | serial mỏng (38-67% flat), quarterly thật | spread 3 tick=$18.75 | PASS | BLOCKED | BLOCKED | như NQ | như NQ |
| 6J | CME | 20 HĐ × 5 job | từ 2020-12 | M1 ~2025-12 | 20 (4 quarterly expired) | KHÔNG | PASS 7/7 | niêm yết JPY/USD: giá 0.006333-0.00643 USD/JPY (đảo của USDJPY ~157), mult 12.5M JPY, minTick 5e-7 — KHÔNG đảo chiều | spread 4 tick=$25 | PASS | BLOCKED | BLOCKED | như NQ | như NQ |
| 6B | CME | 20 HĐ × 5 job | từ 2020-12 | M1 gần | 20 (4 quarterly expired) | KHÔNG | PASS 7/7 | như 6E; giá 1.3102-1.3266 USD/GBP | spread 3 tick=$18.75 | PASS | BLOCKED | BLOCKED | như NQ | như NQ |
| 6A | CME | 20 HĐ × 5 job | từ 2021-09 | M1 gần | 20 (4 quarterly expired) | KHÔNG | PASS 7/7 | như 6E; giá 0.6457-0.6984 USD/AUD | spread 4 tick=$20 | PASS | BLOCKED | BLOCKED | như NQ | như NQ |

Ghi chú bảng: "HĐ" = hợp đồng. Front ngày 2026-10-02: NQZ6/ESZ6 (202612), CLX6
(202610), NGX26, GCV6, SIV6, 6EV6/6JV6/6BV6/6AV6 (202610 serial). Quote streaming
type1/type3: ticker rỗng toàn bộ 10 mã (CL/NG kèm error 10168/300) — lỗi quote
KHÔNG kéo theo lỗi lịch sử (đã kiểm chứng riêng, đúng như yêu cầu).

## Phát hiện kỹ thuật chính (đều đo được, có artifact)

1. **Expired wall ~1 năm**: reqContractDetails với includeExpired chỉ resolve
   hợp đồng hết hạn trong ~12 tháng qua (NQ/ES 5 quý, CL/NG 12 tháng, GC/SI 6
   kỳ, FX 4 quý). localSymbol fallback mở thêm đúng tới ~Dec 2025 rồi tường
   (CLZ4/CLZ3 EMPTY). Hợp đồng cũ hơn không có conId → không thể request.
2. **endDateTime cho expired**: request cửa sổ phải chồng lên vòng đời hợp đồng.
   Hợp đồng hết hạn + daily 6Y + end=đầu tháng đáo hạn → full life (CLU6:
   1478 bar 2020-07→2026-06). Lỗi 162 hôm trước là cửa sổ lệch, KHÔNG phải hết
   quyền (sửa lại kết luận giữa phiên).
3. **Bar close-only**: phần đời xa của mỗi hợp đồng là bar O=H=L=C, volume=0
   (settlement-derived) — 25-90% tùy hợp đồng; chỉ ~3-8 tháng cuối đời có
   volume thật. Đây là same disease PC12A F-1 (CONTFUT synthetic) nhưng ở
   per-contract, tách và khai báo được.
4. **Intraday vintage wall**: M1/H1 chỉ có ~10 tháng gần (CL/GC/SI/ES/6E),
   NG ~2.2 năm, NQ ngắn hơn ES. Đã probe 3 mốc end (2026/2024/2022) — file
   `S7_DEPTH_ACTIVE.json`.
5. **CONTFUT không dùng**: session này không tải CONTFUT làm chuỗi hợp đồng.
   Bằng chứng cũ (PC12A) và mới thống nhất: không có roll rule, 41-63% bar chết.
6. **CME direct re-measure**: DNS giờ resolve IP Akamai thật (không còn
   sinkhole 127.0.0.1 như FX-FUTURES-FRONTIER-V1 đo 2026-09-17), TLS+SNI bắt
   tay OK — nhưng HTTP 403 mọi endpoint + WebFetch timeout 60s. Vẫn
   BLOCKED_HTTP tầng ứng dụng (bot filtering); không lách.
7. **SI identity**: symbol SI trên COMEX trả 2 tradingClass (SI 5000oz + SIL
   1000oz); session chọn đúng SI 5000oz bằng tradingClass tường minh. FX
   (6E/6J/6B/6A) cần tradingClass tường minh nếu không error 200.

## Quy tắc roll khai báo (PIT-legal, không lookahead)

Holding: giữ hợp đồng đến phiên cuối cùng TRƯỚC ngày 1 của tháng đáo hạn, chuyển
sang hợp đồng kế tiếp (cùng mã, kỳ kế theo chu kỳ niêm yết) tại close phiên đó.
Danh sách tháng đáo hạn do sàn công bố trước nhiều năm → điểm quyết định roll
chỉ dùng thông tin đã có. KHÔNG back-adjust trong session này; chi phí roll
quan sát được từ chênh lệch close 2 hợp đồng liền kề tại ngày roll (đã có dữ
liệu, chưa tính toán — NOT_COMPUTED). Không nội suy khoảng trống.

## Bảng chi phí (per symbol, đơn vị USD/side/lượt 1 hợp đồng)

- Commission IBKR (document-class, fetched 2026-10-02, `costs/IBKR_futures_commissions_2026-10-02.json`): chuẩn 0.85 (tier ≤1000; fixed cũng 0.85) + exchange + regulatory pass-through. Ví dụ chính thức duy nhất có số exchange: ES 1.38 + 0.00-0.01 → all-in 2.24. Exchange fee từng mã khác: NOT_FETCHED (bảng JS không render; CME chính thức BLOCKED_HTTP).
- Spread quan sát được (front, median 20 ngày, close-to-close proxy, `S6_FRONT_SPREADS.json`): ES 12.50 · NG 20 · 6A 20 · 6E 18.75 · 6B 18.75 · 6J 25 · NQ 32.50 · CL 30 · GC 50 · SI 112.50. 1 năm BID/ASK daily đủ cho mọi mã (241-251 ngày, crossed: 0; SI 1 ngày).
- Slippage: NOT_RUN_NO_DECLARED_VALUE (không có giá trị khai báo trong repo cho futures; không bịa 0).
- Roll cost: quan sát được từ dữ liệu (chênh lệch close kề nhau ngày roll) — NOT_COMPUTED session này.
- Margin (broker-class, 2 nguồn công khai chênh <2%, CME SPAN chính thức BLOCKED_HTTP, IBKR login-gated): NQ ~42k/46k, ES ~26k/29k, CL ~8k/8.8k, NG ~2.8k/3.1k, GC ~22k/25k, SI ~33k/37k, 6E 2.4k/2.6k, 6J ~2.7k/3k, 6B ~2.2k/2.4k, 6A 1.9k/2.1k (maintenance/initial, chi tiết `costs/SPECS_MARGINS_PUBLIC_2026-10-02.md`).
- Overnight position fee (tiered): tồn tại, số NOT_FETCHED. Quy ước giá/đơn vị hợp đồng: specs đầy đủ trong file costs trên.

## Điều kiện nhãn (khai báo trước khi gán)

- SIGNAL_RESEARCH_READY = PASS khi có daily TRADES per-contract rõ đáo hạn, ≥6 tháng chuỗi front volume-thật, settlement tách được, tz xác minh. **10/10 PASS.**
- DAILY_FUTURES_BACKTEST_READY = PASS khi chuỗi front-month volume-thật liên tục ≥24 tháng + roll PIT + chi phí đủ. Thực tế ~13-14 tháng (2025-08→2026-10) → **10/10 BLOCKED** (đường lấy dữ liệu hoạt động, chỉ thiếu độ sâu; deeper là bar settlement-only không thể thay giá khớp).
- INTRADAY_FUTURES_BACKTEST_READY = PASS khi M1/H1 nhiều năm per-contract. Thực tế ~10 tháng (NG 2.2 năm) → **10/10 BLOCKED**.
- Giá proxy (EIA spot CL/NG, XAUUSD/GLD cho GC): KHÔNG dùng làm giá futures trong session này; chỉ ghi nhận là proxy/signal nếu cycle sau muốn.

## Câu trả lời cuối (mã nào nghiên cứu được ngay)

- **Ngay bây giờ**: cả 10 mã dùng được cho nghiên cứu daily signal trên chuỗi
  front-month thật 2025-08→2026-10 (~14 tháng) và trên giá close/settlement
  per-contract sâu hơn (2019/2020→nay, phải khai báo là settlement-derived).
  Cửa sổ intraday gần (~10 tháng) đủ cho khám phá cơ chế gần hạn. BID/ASK daily
  1 năm đủ dựng chi phí spread.
- **Cần thêm để backtest thực sự**: chuỗi volume-thật ≥2 năm và M1/H1 sâu → cần
  MỘT trong: (a) mua dữ liệu lịch sử từ vendor có license CME (Databento /
  CME DataMine / tương đương — quyết định và thanh toán của owner); (b) tích lũy
  prospective từ nay (collector đã chạy được theo pattern session này); (c) giới
  hạn chấp nhận backtest 14 tháng với chi phí khai báo. Mọi loại dữ liệu cần:
  per-contract daily TRADES + BID/ASK từ ~2019, M1 từ ~2019, cho đủ 10 mã.

## Artifacts & tái lập

Control dir `research/control/FUTURES-DATA-10SYMS-V1/`: INTAKE.md, S1_IDENTITY.json,
S2_QUOTES.json, S3_HISTPROBE.json, S4_SAMPLES.json, S5_BULK_LOG.json,
S6_VALIDATION.json, S6_FRONT_SPREADS.json, S7_DEPTH_ACTIVE.json,
S8_MANIFEST_DIGEST.json (manifest sha256 40efc8a3…, 1150 file raw, 36,085,503 B),
S9_INDEPENDENT_VERIFY.md (verifier độc lập), cme_check/, costs/, fut10_probe.py
(tái lập: stages identity/quotes/histprobe/sample/bulk — checkpoint qua
raw_manifest.jsonl), fut10_validate.py, fut10_depth.py. Raw ngoài Git:
`~/.my-quantitative-data/futures-10syms-v1/raw/` (37 MB). Báo lỗi nguồn:
CME HTTP 403/timeout (cme_check/cme_transport_recheck_2026-10-02.json);
IBKR margin login-gated; WebFetch ibkr.com 403 (webReader dùng được cho page
pricing).

## Kiểm định độc lập (S9) + gap-fill

Verifier độc lập (subagent, không phải người tạo dữ liệu) PASS cả 7 kiểm tra:
SHA 1150/1150 file khớp manifest; identity khớp 10/10 front (multiplier/minTick
chỉ có trong S1, không tái suy được từ raw — caveat ghi nhận); coverage 200/200
hàng khớp S6; timezone 50/50 file 1-min đúng offset theo timeZoneId tại từng
bar (DST đúng); 6J quote đúng thang 0.00633 (0 bar >1.0 trong 9,136 bar); 0
trùng lặp ngày. Phát hiện C1 (medium): CLV6/NGV26 (kỳ giao tháng 10-2026, vừa
ngừng giao dịch cuối tháng 9) rơi qua khe walk-back vì tháng hợp đồng = tháng
hiện tại — **đã gap-fill ngay trong session**: mỗi hợp đồng thêm daily 6Y
(1474/1483 bar) + H1 30D + BID/ASK 1Y (245/249 ngày). C2 (NQU7 toàn bar phẳng
2027-09 — quý tương lai chưa giao dịch, không phải lỗi dữ liệu), C3 (quy ước
tháng NYMEX: `expiry_month` raw chứa lastTradeDate, tháng giao = tháng sau mã
chữ — đã ghi nhận tránh nhầm), C4 (metadata raw không chứa multiplier/minTick;
tz trống ở file expired — truy vết được về S1). Manifest cuối: sha256
`5e8e2b77…`, 1160 file, 36,463,541 B.

## Handoff

`HANDOFF.json` (schema zcode_orch_v3_handoff@1) tại control dir. No-commit
session; owner reviews và commit.
