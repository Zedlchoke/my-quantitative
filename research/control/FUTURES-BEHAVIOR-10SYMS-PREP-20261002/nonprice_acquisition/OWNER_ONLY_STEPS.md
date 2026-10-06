# OWNER_ONLY_STEPS — NONPRICE-DATA-ACQUISITION (2026-10-02)

Task: FUTURES-BEHAVIOR-10SYMS-PREP-20261002 · Lane NONPRICE-DATA-ACQUISITION.
CHỈ những bước THẬT SỰ chỉ owner làm được (tạo key / quyết định trả tiền / mở
tài khoản). KHÔNG có key nào được paste vào chat/log/git. Mọi lệnh dưới đây
dùng `read -s` để key không hiện màn hình, lưu file 0600 NGOÀI git.

## 0. Nguyên tắc chung

- File secret: `~/.config/my-quantitative-secrets/` (chmod 700), mỗi file
  chmod 600, chỉ chứa key thô (không xuống dòng).
- KHÔNG cần key cho bất cứ nguồn nào đã tải xong trong round này — toàn bộ
  CFTC/EIA-archive/FRED-latest/ALFRED-year-end-vintages/ECB/BoJ/MOF/BoE/NOAA
  đều lấy qua route file-public không key. Chỉ làm các bước dưới khi muốn mở
  khóa các mảnh đang chờ.

## 1. FRED/ALFRED API key — CHỈ nếu cần vintage mịn hơn năm-kết-thúc

Vì sao: lane đã tải PIT snapshots theo từng năm-cuối (2010..2025 + 2026-09-30)
qua route `alfredgraph.csv?vintage_date=` miễn phí, nhưng host bị rate-limit
nặng (mỗi request có thể mất phút). Nếu cần vintage THEO TỪNG NGÀY PHÁT HÀNH
(đặc biệt CPIAUCSL/PAYEMS để lấy first-print chính xác từng tháng), API key
(miễn phí) là đường chuẩn.

Các bước (chỉ owner):
1. Mở https://fred.stlouisfed.org/docs/api/api_key.html (truy cập 2026-10-02).
2. Đăng ký tài khoản St. Louis Fed (email của owner) → "Request API key".
3. Lưu key KHÔNG qua chat:
   ```
   mkdir -p ~/.config/my-quantitative-secrets && chmod 700 ~/.config/my-quantitative-secrets
   read -s FRED_API_KEY && printf '%s' "$FRED_API_KEY" > ~/.config/my-quantitative-secrets/fred-api-key
   chmod 600 ~/.config/my-quantitative-secrets/fred-api-key && unset FRED_API_KEY
   ```
4. Sau đó lane kế tiếp đọc key IN-PROCESS (không echo, không log), ví dụ:
   `fred/series/observations?api_key=$(cat ...)&file_type=json&realtime_start=...`
   và kiểm soát 429 theo documents (rate limits công khai của FRED).

KHÔNG làm nếu: vintage năm-cuối đã đủ cho NQ-H1/GC-H5/CL-H4 (theo config là
đủ cho minimal test).

## 2. NOAA NCEI CDO token — hiện KHÔNG cần

CPC FTP, climdiv bulk, NDFD bucket đều không cần token (đã tải không key).
Chỉ cần CDO token (https://www.ncdc.noaa.gov/cdo-web/token, truy cập
2026-10-02) nếu sau này muốn GHCN-Daily theo trạm qua API:
```
read -s CDO_TOKEN && printf '%s' "$CDO_TOKEN" > ~/.config/my-quantitative-secrets/noaa-cdo-token
chmod 600 ~/.config/my-quantitative-secrets/noaa-cdo-token && unset CDO_TOKEN
```
Lưu ý: GFS/NDFD forecast VINTAGES nhiều năm KHÔNG giải được bằng token —
kho NDFD công khai không version hóa (đã đo), archive chính thức là NCEI AIRS
theo yêu cầu; nếu owner muốn thì đó là quy trình request riêng của NCEI.

## 3. EIA API key — hiện KHÔNG cần

Toàn bộ WNGSR/WPSR archive as-published (1996/2011→2026) đã tải qua
www.eia.gov không key. Chỉ cần key (miễn phí, https://www.eia.gov/opendata/,
truy cập 2026-10-02) nếu muốn query API v2 theo series:
```
read -s EIA_API_KEY && printf '%s' "$EIA_API_KEY" > ~/.config/my-quantitative-secrets/eia-api-key
chmod 600 ~/.config/my-quantitative-secrets/eia-api-key && unset EIA_API_KEY
```

## 4. Danh sách PAID chờ owner quyết (KHÔNG đăng ký/buy gì trong prep)

| Hạng mục | Vì sao chờ | Giá trị nghiêm cấm thay thế |
|---|---|---|
| Consensus archive (S&P Global / Action Economics / các vendor tương tự) cho CPI/NFP/WNGSR/WPSR/FOMC/BoE/EA | 8 hypothesis BLOCKED_CONSENSUS (NQ-H3, ES-H3, GC-H2, NG-H1*, CL-H2, 6E-H3, 6E-H4, 6B-H2) — không có archive consensus as-issued miễn phí hợp pháp | TUYỆT ĐỐI không dùng actual thay expected |
| *NG-H1 ngoại lệ một phần: WNGSR archive có nhúng survey "The Desk" (median/range) as-published — miễn phí; owner thẩm định có đủ dùng hay vẫn mua vendor | | |
| LBMA/IBA silver lease rates (SI-H3) | trả phí | không được thay bằng proxy tự chế khi khai báo là lease rate |
| S&P forward dividend yield (ES-H2) | index-provider trả phí | |
| Iron-ore primary price (6A-H2) | licensed | |
| Databento GLBX.MDP3 (depth giá lịch sử) | billable — theo DATA_ACQUISITION_SPEC §7 Phase 0/1/2, owner gate | |
| Ổ đĩa ngoài nếu muốn nới disk gate | cap 2 GiB hiện tại đủ cho mọi nguồn đã tải; WAIT_STORAGE chỉ ở CPC daily 2025-07+ (file 3.3MB/ngày) và GFS vintages | |

## 5. Ghi chú 403-gate đã ghi nhận (không cần owner làm gì, chỉ biết)

- www.bls.gov + download.bls.gov: 403 với client tự động (đã lưu evidence);
  fallback PIT CPI/NFP = ALFRED vintages (đã tải).
- rba.gov.au: 403 (RBA dates/times đã FACT trong configs từ dossier lane).
- ir.eia.gov: 403 (trừ ngs/schedule.html) — đã dùng archive www.eia.gov tốt
  hơn (as-published vintage).
- CPC /products/archives/*: 403 — đã dùng FTP công khai.
