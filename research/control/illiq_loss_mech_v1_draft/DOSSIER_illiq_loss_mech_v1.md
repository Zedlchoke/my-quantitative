# DOSSIER — ILLIQ-LOSS-MECH-V1 draft: cơ chế gây lỗ của ILLIQ-AMIHUD-28D-W trên S0R 2024-08-22→2025-08-21

- Namespace: `research/control/illiq_loss_mech_v1_draft/` (CHỈ namespace này được ghi; mọi tree khác READ-ONLY)
- Ngày: 2026-09-24 · Bootstrap/owner session theo chỉ đạo owner 2026-09-24
- Trạng thái: **DRAFT — chưa đăng ký cycle; chưa chạy cell nào; engine frozen `c97283e0` không bị sửa**
- Sản phẩm kèm: `p1_forensics.json` + `p1_ledger_forensics.py` (P1), PREREG draft yaml (P3 freeze)

---

## 0. Compliance

| Ràng buộc | Trạng thái |
|---|---|
| Không chạy scored cell / heavy job | OK — aggregation artifact có sẵn (`scored: False`) + đọc tên file parquet catalog; KHÔNG cần heavy lock |
| Heavy lock máy | HELD bởi CHR3F BASISLV data-staging (pid 22173, token match) — mọi compute nặng trong cycle mới phải chờ lock; session này không chạy |
| Không sửa engine frozen | OK — engine chỉ đọc (`.../recovered/v11_root/research/v11/families/illiq_amihud/`) |
| Không retune O1/V2 / chọn ngày-symbol-ngưỡng sau PnL | OK — P2 chỉ nêu giả thuyết cơ chế mới; mọi ngưỡng test được freeze TRƯỚC cell trong plan §6 |
| Không đụng shadow đang chạy / S1 / gateway | OK |
| Baseline funded −56.31%, gate −34.58% FAIL bar −29.47%, INV +32.97% chỉ diagnostic | Giữ nguyên verbatim trong §2 — không đổi chiều, không gọi discovery |

## 1. Provenance + tái lập byte/ledger-level (P1.0)

Artifact chính: `illiq_diag/S0R-ANCHOR-A5-funded/results/artifact.json` (CHR3F, funded,
`result_sha256 = 8c8e1242…`, file sha256 ghi trong `p1_forensics.json`).

| Kiểm tra | Kết quả |
|---|---|
| 5/5 payload hash (positions, portfolio_payload, benchmarks, fold_metrics, result) recomputed = recorded | **MATCH** |
| Ledger sums (336 positions) vs `portfolio_metrics`: price diff 0.0, funding diff 9e-12 | **MATCH** |
| Net: position-sum −0.560534 vs recorded −0.563058; chênh 0.002524 = cost boundary-turnover KHÔNG gán vào position record; identity price+funding−cost=net khớp **1.1e-16** ở portfolio level | **MATCH (có giải thích)** |
| MDD additive recompute 0.601152 = recorded | **MATCH** |
| 4/4 headline cell (`illiq_scored_summary.json`): S0R ANCHOR −0.5631 / S0R INV +0.5459 / Y2024P ANCHOR +0.1377 / Y2024P INV −0.1501 | **MATCH** |
| Funding-wiring delta vs no-funding twin B2: −0.589312 → −0.563058 = **+2.63 pts** | khớp terminal ILLIQ-REG-V1 |
| Detached-twin re-run (heavy) | **NOT_RUN_RESOURCE_CONFLICT** — lock máy bị CHR3F giữ; twin byte-identical đã tồn tại cho 4 cell gated (ILLIQ-REG-V1 @31985732) |

## 2. P1 — Pháp y lỗ (baseline FUNDED −0.563058 per-unit)

### 2.1 Tổng quan

net −0.5631 = price −0.5807 + funding **+0.0263** + cost −0.0086 (0.0060 gán position + 0.0025 boundary).
MDD 0.6012. Lỗ là **price-driven**: stress fee ×1.5/×2.0 chỉ dịch −0.004/−0.008 (ILLIQ-REG-V1 P1-C2/C3);
cost cả năm −0.86%. Funding wired giúp +2.63 pts (short majors KIẾM carry khi funding dương) — không giải thích được lỗ.

### 2.2 Theo leg — SHORT majors là thủ phạm chính

| Leg | n | Price | Funding | Net | Win rate | % tổng net lỗ |
|---|---|---|---|---|---|---|
| SHORT (liquid quintile = majors) | 168 | −0.5029 | +0.0252 | **−0.4807** | 49.4% | **85.8%** |
| LONG (illiquid quintile) | 168 | −0.0779 | +0.0011 | −0.0798 | 37.5% | 14.2% |

### 2.3 Theo fold — LUÂN PHIÊN, không leg nào chết cả năm

| Fold | Net | LONG | SHORT |
|---|---|---|---|
| F1 (2024-08-26→12-16) | −0.0392 | +0.2742 | −0.3134 |
| **F2 (2024-12-23→2025-04-14)** | **−0.3210** | **−0.4892** | +0.1681 |
| F3 (2025-04-21→08-18) | −0.2003 | +0.1351 | −0.3354 |

### 2.4 Ba cụm lỗ theo yêu cầu owner (ledger funded)

| Cụm | Net | LONG | SHORT | Top losers |
|---|---|---|---|---|
| **Cuối 2024 (11–12/2024, majors melt-up hậu bầu cử)** | −0.1109 | **+0.3592** | **−0.4701** | DOGE:S −0.151, 1000PEPE:S −0.116, ETH:S −0.110, SOL:S −0.056 |
| **01/2025 (long-leg sụp)** | −0.2449 | **−0.2853** | +0.0405 | BOME:L −0.114, ACE:L −0.083, ZEC:L −0.060, ONG:L −0.029 |
| **07–08/2025 (ATH grind majors)** | −0.1984 | +0.0113 | **−0.2097** | ETH:S −0.088, DOGE:S −0.056, XRP:S −0.041, SOL:S −0.024 |

5 stamp xấu nhất: 2025-01-20 (−12.79%), 2024-11-11 (−10.24%), 2024-11-18 (−8.24%), 2025-07-21 (−6.77%), 2025-02-03 (−5.89%).
MDD là MỘT episode duy nhất 2024-10-14→2025-08-18 (equity không lập đỉnh mới).

### 2.5 Listing age — TOÀN BỘ lỗ long-leg nằm ở cohort trẻ 90–365 ngày

First-bar proxy từ tên file parquet `binance_bar` (b20 ∪ s0r; BOME 2024-03-16 = đúng ngày list Binance — proxy chuẩn):

| Bucket tuổi tại entry | n (long legs) | Net |
|---|---|---|
| 90–365 ngày (BOME 03/2024, ACE 12/2023, ONG 11/2023, ENA 04/2024) | 40 | **−0.1070** |
| >365 ngày (ZEC 02/2020, …) | 128 | **+0.0272** |

Không có leg nào <90 ngày (luật listing-age engine ≥28d + formation 28d + universe PIT-list full từ 2024-04-02).
→ Long-leg không chết vì "illiquid", mà chết vì **cohort trẻ hậu-list**; illiquid-già thậm chí dương.

### 2.6 BTC/majors exposure + hedge

Engine beta-neutral vs **BTC** qua 90d trailing beta. `book_beta_pre_hedge` (trước hedge, PIT trong artifact):

| Pha | mean pre-hedge beta | min..max |
|---|---|---|
| Cả window | +0.032 | −0.252..+0.480 |
| 11–12/2024 | −0.006 | −0.184..+0.130 |
| 01/2025 | +0.018 | −0.005..+0.067 |
| **07–08/2025** | **+0.268** | +0.065..**+0.480** |

Đọc: cụm 07–08/2025 — pre-hedge beta bật lớn (long-illiquid leg có beta BTC cao hơn hẳn short-majors leg).
Cụm 11–12/2024 — pre-hedge beta ≈ 0 mà short-leg vẫn chảy máu ⇒ bleed đó KHÔNG phải beta, mà là
**idiosyncratic majors-vs-BTC spread** (DOGE/PEPE meme bùng vs BTC). Hedge BTC-only không bảo vệ
chống spread trong chính liquid leg. Bối cảnh: BTC +83.2% window (benchmark context, artifact).

### 2.7 PIT availability (quan sát nào có TRƯỚC thời điểm quyết định)

| Quan sát | PIT? |
|---|---|
| Leg membership, weights, 90d beta, book_beta_pre_hedge, n_eligible, rho diagnostics (books) | **PIT** — trong book snapshot tại stamp T |
| Listing date / tuổi listing (first-bar proxy từ catalog b20/s0r) | **PIT** — có trước T |
| Funding cross-section tại stamp (scan_2026/scan_2026_a) | **PIT** — rate của kỳ đang áp |
| BTC trend / rvol30 / CONC28 (dossier trước) | **PIT** — daily completed blocks |
| PnL, boundary returns, MDD, phân rã leg/symbol | KHÔNG PIT — outcome ledger, chỉ dùng chẩn đoán |
| O2 (majors-vs-alt trend spread) trong dossier cũ | sinh SAU khi nhìn DIAG — nhãn post-hoc, trọng số 0 |

## 3. P2 — Hai giả thuyết cơ chế (đề xuất, ≤2, đều sinh SAU khi nhìn PnL ⇒ trọng số xác nhận 0 trên mọi window đã quan sát)

### H-A — Nhiễm cohort trẻ hậu-list trong chân long Amihud

- **Kinh tế:** Amihud rank trộn (i) premium rủi ro thanh khoản thật với (ii) price-discovery hậu list &
  decay hậu hype của cohort mới (drift hậu listing âm được ghi nhận rộng rãi trong crypto). Chân long
  "harvest" decay chứ không phải premium khi cohort trẻ chiếm đuôi illiquid. 2021 alt-mania che decay;
  2024-25 majors-led để cohort tự chết (F2, §2.5).
- **Observable PIT:** tuổi listing tại entry (nguồn: listing timestamp sàn / first-bar catalog đã staged;
  coverage đủ 20/20 universe S0R; license: không cần data mới).
- **Dự đoán trước PnL (freeze trong plan):** trên fold FRESH Y2022 & Y2023 (chưa cycle nào chạy ILLIQ —
  kiểm tra MAP/FAMILY_FAILURES/CHR3F tree), trong đúng quintile illiquid của engine, cohort <365d
  underperform cohort ≥365d (Δnet cùng dấu trên CẢ HAI fold, |Δ| ≥ mức freeze); loại cohort trẻ không
  phá các fold dương pre-window.
- **Phép thử bác:** nếu Y2022/Y2023 không cho young-underperformance nhất quán ⇒ H-A FALSIFIED,
  cấm mọi rule age trong cycle này.

### H-B — Hedge BTC-only để hở majors-spread + 90d beta lag

- **Kinh tế:** book chỉ beta-neutral vs BTC. Ở regime majors-led, chính liquid quintile (bị short) chứa
  cohort mạnh nhất ngoài BTC (meme 11/2024; ETH 7–8/2025) ⇒ book về bản chất là short
  "majors-vs-BTC spread"; premium illiquid phải thắng spread đó, và đã thua 2024-25. Pre-hedge beta
  trôi +0.27..+0.48 ở pha C (§2.6) cho thấy 90d beta lag regime shift.
- **Observable PIT:** (i) spread-beta ex-ante của book vs EW-majors index (10 tên liquid nhất universe,
  daily completed trước T); (ii) |β28 − β90| mỗi leg; (iii) book_beta_pre_hedge (đã có trong artifact).
  Nguồn: catalog đã staged, không license mới.
- **Dự đoán trước PnL:** trên Y2022/Y2023 fresh, short-leg PnL tuần xấu tương quan với spread-beta
  ex-ante; biến thể hedge thêm majors-spread giảm đuôi lỗ short-leg ≥30% (mức freeze) trên CẢ HAI fold
  fresh mà KHÔNG lật dấu anchor ở regime dương (đối chứng Y2021 disclosure-only, trọng số 0); INV
  coherent.
- **Phép thử bác:** hedge spread không giảm đuôi lỗ, hoặc phá regime dương ⇒ H-B FALSIFIED.

**Kết luận eligibility:** CẢ HAI có observable PIT đủ mạnh, nguồn đã staged, là thay đổi cơ chế
(book/hedge construction) chứ không phải bộ lọc chọn tuần lỗ, không phải retune O1/V2 ⇒ **ELIGIBLE**,
không kết thúc NO_ELIGIBLE_PROPOSAL. Số phận của chúng do phép thử quyết định, không do circle này.

## 4. P3 — thiết kế kiểm chứng (chi tiết freeze trong `plans/PLAN_illiq_loss_mech_v1.md`)

- Baseline gốc (anchor) + INV giữ nguyên làm đối chứng; 2 identity MỚI trong worktree mới:
  `…v2-age` (H-A: long-leg eligibility thêm tuổi ≥365d) và `…v2-hedge` (H-B: hedge thêm majors-spread).
- Bề mặt: **fresh folds Y2022 & Y2023** (chưa từng quan sát cho family — kiểm chứng MAP/CHR3F tree) là
  DIAG falsification; **Y2021/Y2024P/S0R/2025-26 = outcome-exposed, disclosure-only, trọng số 0**;
  confirmatory duy nhất = **forward/prospective shadow sau freeze**, scored chỉ sau typed GO tại gate.
- Mọi cell: funding wired (B2 law), stress ×1.5/×2.0, turnover/concentration per fold, mọi trial đếm vào
  observed counter (P-9). Ngưỡng PASS/FAIL + budget freeze TRƯỚC scored run đầu tiên.
- Heavy lock hiện HELD (CHR3F BASISLV) ⇒ phase-1 của cycle mới chỉ chạy khi lock free; bootstrap
  session này KHÔNG chạy cell nào.
- A7 độc lập phản biện kế hoạch + leakage/identity trước prelaunch; owner gate/GO của cycle mới là
  điều kiện bắt buộc cho mọi scored run. Không mở S1, không đưa candidate vào app.

## 5. Phụ lục file

```
research/control/illiq_loss_mech_v1_draft/
├── DOSSIER_illiq_loss_mech_v1.md   (file này)
├── p1_ledger_forensics.py          (tái hiện: .venv/bin/python p1_ledger_forensics.py)
└── p1_forensics.json               (toàn bộ số P1)
```
