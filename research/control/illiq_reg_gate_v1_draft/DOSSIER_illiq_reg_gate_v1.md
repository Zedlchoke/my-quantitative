# DOSSIER — FORENSIC + PREREGISTRATION DRAFT: "regime-gated ILLIQ" (ILLIQ-REG-V1 draft)

- Namespace: `research/control/illiq_reg_gate_v1_draft/` (CHỈ namespace này được ghi; mọi thao tác khác READ-ONLY)
- Ngày: 2026-09-24 · Vai trò: quant-researcher (read-only lane)
- Trạng thái: **DRAFT — chưa đăng ký cycle; chưa chạy scored cell nào; engine frozen không bị sửa**
- Sản phẩm kèm: `PREREG_ILLIQ-REG-V1.yaml` (bản thảo preregistration), `forensic_numbers.json`,
  `pit_conc_gate_single_shot.json`, `forensic_compute.py`, `pit_conc_gate_single_shot.py`

---

## 0. Tuân thủ ràng buộc (compliance)

| Ràng buộc | Trạng thái |
|---|---|
| Không chạy scored cell | OK — toàn bộ số liệu là aggregation của artifact DIAG có sẵn (`scored: False`, `REPLICATION_NOT_PROSPECTIVE`) + đọc mô tả dữ liệu staged |
| Không sửa file ngoài namespace | OK — ghi mới 5 file trong namespace; không commit, không đụng ledgers/registries |
| Không tuning gate trên 2024-25 | OK — ngưỡng gate là quy tắc quantile CỐ ĐỊNH trên pre-window 2020-01→2024-08-21; gate được áp lên S0R đúng MỘT LẦN (single-shot, mô tả, không iterate) |
| Không sửa engine frozen | OK — engine chỉ được đọc (`.../recovered/v11_root/research/v11/families/illiq_amihud/`) |
| Không đụng shadow/gateway/S1 | OK |

Lưu ý vị trí engine: đề bài nêu `recovered/v11_root/...` — vị trí thực là
`.worktrees/crypto-historical-replication-3f-v1/integration/research/control/crypto_historical_replication_3f_v1/recovered/v11_root/research/v11/families/illiq_amihud/`
(`__init__.py`, `audits.py`, `plugin.py`, `strategy.py` — A7-r5 §7 xác nhận 18 file byte-identical với freeze `c97283e0`).

---

## 1. Provenance của các artifact được phân tích

| Artifact | Window thực (từ `schedule`) | result_sha256 (8 đầu) | Ghi chú |
|---|---|---|---|
| `illiq_diag/S0R-ANCHOR-A5/results/artifact.json` | 2024-08-26 → 2025-08-18 (52 stamp Monday 00Z) | `2ae1c48e…` | A5, owner ủy quyền 2026-09-24 |
| `illiq_diag/Y2024P-ANCHOR-A4/results/artifact.json` | 2024-01-08 → 2024-08-19 (33 stamp) | `bf3e4a8c…` | A4b |
| `illiq_diag/Y2021-ANCHOR-v2/results/artifact.json` | 2021-01-04 → 2021-12-27 (52 stamp) | — | bối cảnh pre-window |

Caveat metadata (A7-r5 N6): trường `identity.window_start_iso/window_end_iso` trong artifact mang
giá trị template frozen (2025-08-22→2026-08-21), KHÔNG phải window fold — window chuẩn phải đọc từ
`schedule.*_decision_ns`. Mọi báo cáo dòng ILLIQ phải ghi window fold tường minh.

Baseline gốc (context-only): `recovered/v11_root/baseline_wave2.json` W2-1 — ILLIQ anchor scored
trên window frozen 2025-08-22→2026-08-21: net **+0.581969**, PF 1.3548, MDD 0.0918, 336 position,
funding +0.1109. Restage không tái lập được (0.713248 vs 0.581969, rel 0.2255) → namespace
`EQUIVALENCE_DATA_RESTAGE_UNPROVEN` (A3).

---

## 2. PHASE 1 — FORENSIC (từ artifact, không compute mới)

### 2.0 Bảng chéo 3 năm — CÙNG engine frozen

| | Y2021 | Y2024P | **S0R** |
|---|---|---|---|
| Window | 2021-01-04→12-27 | 2024-01-08→08-19 | 2024-08-26→2025-08-18 |
| Net return (sum) | **+1.0360** | +0.1377 | **−0.5893** |
| MDD (additive) | 0.1323 | 0.2050 | **0.6245** |
| Position PF | 1.4689 | 1.0997 | 0.7742 |
| Boundary hit-rate | 42.3% | 36.4% | 25.0% |
| Price P&L | +1.0175 | +0.1235 | −0.5807 |
| Funding | +0.0289 | +0.0204 | **0.0000** (xem §2.3) |
| Costs | −0.0103 | −0.0062 | −0.0086 |
| BTC leg (window return, benchmark context) | +55.1% | +33.8% | **+83.2%** |
| EW benchmark (20 legs) | +1401.2% | +42.1% | +64.2% |

**Kết luận khung**: cùng một spec frozen cho +103.6% (2021), +13.8% (nửa đầu 2024) và −58.9%
(2024-08→2025-08). Sự phụ thuộc chế độ (regime dependence) là hiện tượng cần giải thích, không phải
nhiễu. Đối chứng: benchmark EW cho thấy 2021 là alt-mania (pool illiquid nhân hàng chục lần) còn
S0R là năm majors-led (BTC +83.2% trong khi sách long-illiquid/short-liquid âm sâu).

### 2.1 (a) Lỗ tập trung ở đâu — fold / tháng / symbol

**Fold (S0R, tổng exactly −0.589312; 96+128+112 = 336 position):**

| Fold | Window | Net | Price | MDD fold | PF | Hit |
|---|---|---|---|---|---|---|
| F1 | 2024-08-26→12-16 | −0.0424 | −0.0390 | 0.2190 | 0.947 | 29.4% |
| **F2** | 2024-12-23→2025-04-14 | **−0.3479** | −0.3456 | 0.3479 | **0.670** | 35.3% |
| F3 | 2025-04-21→08-18 | −0.1990 | −0.1962 | 0.2759 | 0.741 | 11.1% |

F2 là fold chết người (59% tổng lỗ); F3 có hit-rate tệ nhất (1/18 boundary dương).

**Theo tháng (boundary returns, 13 tháng):** 4 tháng âm nặng = **2025-01 (−0.2342)**,
**2024-11 (−0.1680)**, **2025-07 (−0.1222)**, 2025-06 (−0.0780) + 2025-08 (−0.0758); tháng dương lớn
nhất chỉ +0.0952 (2024-12) và +0.0633 (2025-05). Không có tháng nào bù nổi.

**Theo symbol (P&L scale theo weight, tổng cả S0R):**

| Symbol | Leg (số lần) | Price P&L | Net |
|---|---|---|---|
| ETHUSDT | SHORT (42/42 tuần) | −0.1772 | −0.1781 |
| DOGEUSDT | SHORT (31) | −0.0994 | −0.0998 |
| BOMEUSDT | LONG (34) | −0.0891 | −0.0897 |
| XRPUSDT | SHORT (37) | −0.0774 | −0.0780 |
| SOLUSDT | SHORT (42) | −0.0700 | −0.0708 |
| ACEUSDT | LONG (42) | −0.0685 | −0.0708 |
| ONGUSDT | LONG (42) | −0.0528 | −0.0535 |
| 1000PEPEUSDT | SHORT (7) | −0.0517 | −0.0519 |

Lỗ phân tán đều trên NHIỀU symbol chứ không dồn 1 tên: top-8 loser gộp −0.693 net trong khi tổng lỗ
−0.589 (có winner bù: AAVEUSDT long +0.1484, ZECUSDT long +0.0120). Điểm đáng chú ý: 3/8 loser là
**long-leg** (BOME, ACE, ONG — các tên mới list 2024, decay hậu list), còn short-leg mất money chủ
yếu qua các tên majors (ETH, DOGE, XRP, SOL).

### 2.2 (b) Long-leg hay short-leg gây lỗ

Tổng S0R theo leg (168 position/leg):

| Leg | Price P&L | Net | Win count | Tỉ lệ lỗ gộp |
|---|---|---|---|---|
| LONG (illiquid quintile) | −0.0779 | −0.0809 | 64/168 | 13.4% |
| **SHORT (liquid quintile)** | **−0.5029** | **−0.5059** | 83/168 | **86.6%** (theo price P&L; 86.2% theo net) |

Theo fold, cấu trúc LUÂN PHIÊN (không phải một leg chết suốt năm):

| Fold | LONG net | SHORT net | Chẩn đoán |
|---|---|---|---|
| F1 | +0.2874 | **−0.3288** | majors melt-up (post-election 11/2024) đâm short-leg |
| F2 | **−0.5128** | +0.1654 | long-illiquid (BOME/ACE/ONG post-listing) sụp trong khi majors đi ngang |
| F3 | +0.1445 | **−0.3425** | majors rally ATH 7-8/2025 đâm short-leg lần hai |

Đối chứng pre-window: Y2021 cả hai leg dương (LONG +1.0012, SHORT +0.0373); Y2024P LONG +0.3879 /
SHORT −0.2487 — short-leg đã bắt đầu bleed từ nửa đầu 2024 (majors-led), được long-leg che.

### 2.3 (c) Funding đóng góp bao nhiêu

- **Trong artifact S0R-ANCHOR-A5: funding = 0.0 trên CẢ 336 position** (0 position có funding ≠ 0);
  `portfolio_metrics.funding_sum = 0.0`. Toàn bộ −58.93% là **price P&L (−58.07%) + cost (−0.86%)**.
- Đây là **missing data, không phải funding thật = 0**: A7-r5 blocker **B2** đo đạc — runner ghi cứng
  `SCAN = funding_data_scan/scan_2026` (BTC coverage 2020-07-01→**2024-08-20**, 0 row trong window
  S0R) trong khi scan phủ đúng window (`scan_2026_a`, 2024-08-20→2026-08-21, 2196 row BTC) tồn tại
  staged nhưng "nothing reads it". Remediation per-fold đã commit (`2404f5d4`), S0R DIAG wired-funding
  **chưa re-run / re-disclose** trên artifact tôi nhận.
- Đối chứng: Y2024P funding +0.0204 (213/216 position), Y2021 +0.0289 (216/216) — pre-window,
  funding đóng góp dương nhỏ.
- Mô tả funding-rate (staged `scan_2026_a`, mô tả thuần): tại các stamp lỗ 11-12/2024, funding
  majors dương mạnh và tăng vọt (cross-section mean annualized +4.3%→+8.1%→+17.3%→+33.5% tại
  2024-12-09). Kinh tế: short majors khi funding dương = leg này KIẾM carry — nên funding-wired
  có khả năng CẢI THIỆN nhẹ con số S0R, không giải thích được −58.9% price-driven.

> **Bắt buộc trước mọi scored run của family này**: re-run S0R DIAG với funding wired (A7-r5
> remediation) và re-disclose con số mới; mọi số −58.9% phải được nhãn "no-funding DIAG (B2)".

### 2.4 (d) Chuỗi ngày tạo MDD 62%

Quy ước engine (`adapter_v10/metrics.py::max_drawdown`): MDD là **additive peak-to-trough trên
cumsum** boundary returns (52 điểm, Monday 00Z) — "62%" = 62.45 điểm phần trăm return lũy kế
per-unit; equity nhânływ cuối ≈ ×0.528 (−47.2% multiplicative, đối chiếu chiều).

- **Peak: 2024-10-14** (equity +0.0352). **Trough: 2025-08-18** (equity −0.5893 = cuối window).
- Depth **0.6245**; equity KHÔNG bao giờ lập đỉnh mới sau 2024-10-14 → toàn bộ 45 stamp cuối
  (44 tuần, 2024-10-14→2025-08-18) là MỘT episode drawdown duy nhất gồm 3 pha:

| Pha | Tuần | Boundary returns | Bối cảnh observable |
|---|---|---|---|
| A. Majors melt-up | 2024-11-04→11-18 | −0.68%, **−10.25%**, −8.29% | BTC 90d trend +21%→+53%; funding majors +9%→+19% ann |
| B. Long-leg sụp | 2025-01-06→02-03 | −4.38%, −3.67%, **−12.76%**, −2.61%, −6.00% | BTC dao động ~100k (trend +52%→+46%); BOME/ACE/ONG decay |
| C. Grind ATH majors | 2025-06-16→08-18 | −3.78%, −1.91%, −6.78%, −2.24%, −6.78%, −4.44%, −2.34% | BTC 104k→119k (trend +20%→+43%); rvol30 giảm 0.35→0.22 |

- 5 boundary xấu nhất: **2025-01-20 (−12.76%)**, 2024-11-11 (−10.25%), 2024-11-18 (−8.29%),
  2025-07-21 (−6.77%), 2025-02-03 (−6.00%).
- Quy kết position trong toàn chuỗi MDD (theo stamp đóng): ETH −0.1920, DOGE −0.0998, SOL −0.0922,
  BOME −0.0897, XRP −0.0878, 1000PEPE −0.0730, ACE −0.0571, ONG −0.0367, BNB −0.0272; ZEC +0.0417.
- Turnover boundary = 1.0 (reconstitute trọn sách, force-flat) tại 7 stamp fold-boundary
  (2024-12-16, 12-23, 2025-04-14, 04-21, 05-12, 06-02, 08-18); 3 stamp **SKIP_NO_SELECTION**
  (2025-05-12/19/26 — n_eligible < 10, sách phẳng). Tổng turnover one-side S0R = 16.96×
  (≈33 tuần full-turnover/52) — cost chỉ −0.86% nên lỗ KHÔNG do cost.

### 2.5 (e) Trạng thái biến quan sát được tại các stamp lỗ

Nguồn: sách + diagnostics trong artifact; BTC marks & DV từ catalog staged `catalog_live_crypto_s0r`
(2024-04-01→2025-09-30, cùng nguồn bars của DIAG); funding staged `scan_2026_a` (chỉ mô tả).
PIT-share tính với denominator chỉ gồm symbol đã list ≥28 ngày (cùng luật listing-age của engine).

| Biến | Trạng thái tại chuỗi lỗ (S0R) | Đối chứng pre-window (2020-01→2024-08, 242 Monday) |
|---|---|---|
| **BTC 90d trend** | Pha A: +21%→**+76%** (2024-12-16). Pha B: +40..+52%. Pha C: +20%→+43%. Chỉ pha B-Feb→Apr âm (−10..−21%) và vẫn lỗ | BTC +83.2% cả window S0R vs +33.8% Y2024P, +55.1% Y2021 |
| **DV-share BTC (CONC28, PIT)** | 0.85→0.94, tăng dần; Δ90d phần lớn ÂM (−3.7%..+2.2%) — alt DV cũng tăng | Δ90d pre-window: p50 +0.18%, p70 +2.13%, p90 +5.77% |
| **Funding cross-section (majors, ann.)** | Pha A: +4.3%→+19%→**+33.5%** (2024-12-09); p90−p10 ~7-23 điểm; majors ≫ illiq (Nov: +3.3% vs −0.4%) | — |
| **Turnover** | 16.96× one-side/năm; 1.0 tại fold boundaries; 0 tại SKIP | Y2021: 20.6×; Y2024P: 12.4× |
| **Vol (BTC rvol30, ann.)** | 0.35→0.58 (pha A/B) → **0.22-0.31** (pha C, thấp hơn p10 pre-window 0.329) | pre-window p10 = 0.329, p50 = 0.553, p90 = 0.862 |
| **Book diagnostics** | n_eligible = 19 ổn định; rho(amihud, reversal-7d) dao động −0.63..+0.45 (không bất thường tại stamp lỗ); rho(amihud, size) ≈ −0.93 (feature ≈ rank ngược size — cấu trúc, không đổi theo regime) | tương tự |

Đọc chính: **lỗ không đến từ một cú sốc liquidity acknowledgeable trong book diagnostics** mà đến
từ chế độ thị trường: (i) majors-led melt-up/rally làm short-leg (86.8% lỗ) thua liên tục, (ii)
cohort illiquid mới-list decay (pha B), (iii) vol nén dần về vùng chưa từng thấy trong 2020-2024 ở
pha cuối. Cross-section funding cho thấy crowding long-majors cực mạnh đúng pha A.

### 2.6 Single-shot gate replay (mô tả — KHÔNG phải validation)

Với đúng MỘT bộ ngưỡng frozen từ pre-window (không iterate): gate ON khi ΔCONC90(PIT) ≤ p70 (+2.13%)
hoặc OFF khi ≥ p90 (+5.77%); cộng điều kiện rvol30 ≥ p10 (32.9%, hysteresis 10%):

| Window | Ungated net | Gated net (single-shot) | Gated MDD | Số stamp bị tắt |
|---|---|---|---|---|
| S0R | −0.5893 | −0.4030 | 0.6245 → 0.4435 | 6/52 (chỉ pha C) |
| Y2024P | +0.1377 | +0.1188 | 0.2050 (không đổi) | 2/33 |
| Y2021 | +1.0360 | +1.0660 | 0.1323 → 0.1038 | 9/52 |

→ Gate a-priori này **bỏ sót cả pha A lẫn pha B** (nguồn ~80% lỗ) và chỉ cắt được pha C. Suy ra
đúng như luật: kết hợp biến "concentration hướng DV-share + vol-floor" ở dạng này khả năng cao bị
FALSIFY nếu đăng ký nguyên trạng. Đây là input trung thực cho Phase 3 (falsification-first), không
phải lý do để biến Gateway khác khớp S0R (bị cấm).

---

## 3. PHASE 2 — MECHANISM HYPOTHESIS (≤2 biến, lý do kinh tế viết trước)

### Biến 1 — CHIỀU XOAY VÒNG THANH KHOẢN (liquidity-rotation direction) — biến chính

**Lý do kinh tế (viết trước khi nhìn S0R, theo tài liệu Amihud; liquidity-as-risk):** premium illiquid
là phần bù cho việc nắm tài sản đắt chiếu trade. Nó tồn tại khi dòng tiền phân tán/chảy về long tail
(rủi ro thanh khoản được định giá, discount illiquid được mua dần) và CHẾT khi dòng tiền tập trung
vào nhóm liquid-majors: khi đó "illiquid" không còn là rủi ro được bù mà là ballast bị bỏ rơi —
spread illiquid-vs-liquid suy giảm cấu trúc, đúng chiều đâm cả hai leg của sách (short majors thua
khi majors trend up; long illiquid thua khi chỉ còn người bán dần). Trong crypto 2024-25 đây là chế
độ dòng ETF/institutional mua majors — biến này được chọn theo lý kinh tế + bằng chứng pre-window
(2021: alt-mania, pool illiquid bùng nổ → sách +103.6%; không cần dữ liệu 2024-25 để phát biểu).

**Operationalization:**
- **O1 (đã freeze, đã replay single-shot):** CONC = DV-share của BTC trong universe PIT-listed
  (≥28 ngày tuổi), trailing 28d; S = CONC28 − CONC90. Kết quả single-shot (mục 2.6): phân lập YẾU —
  kỳ vọng bị falsify. O1 được đem ra prereg NGUYÊN TRẠNG với vai trò giả thuyết bị thử thách.
- **O2 (POST-HOC-PROPOSED, cùng biến kinh tế):** hiệu xu hướng 90d giữa index majors (EW 10 tên
  liquid) và index alt-cohort PIT. Ghi rõ: O2 sinh ra SAU khi nhìn DIAG S0R (Phase 1 cho thấy majors
  90d trend dương mạnh tại mọi pha lỗ) — KHÔNG được tính là bằng chứng; bar bằng chứng bị phạt
  (mục 4), bề mặt xác nhận duy nhất = forward window.

### Biến 2 — SÀN BIẾN ĐỘNG THỰC (BTC realized-vol floor) — biến phụ

**Lý do kinh tế (viết trước):** phần bù thanh khoản là trả công cho bearing liquidity risk; nó tập
trung ở các chế độ vol mở rộng/stress khi margin-lenders và market-makers bị ràng buộc vốn, và chết
trong chế độ grind vol-nén (spread bị MM bào mòn, dòng passive-institutional chỉ mua majors). Sách
chỉ nên ON khi vol regime "sống".

**Operationalization (freeze):** VOL = stdev nhật log-close BTC 30d × √365, từ completed daily blocks.
ON nếu VOL ≥ 32.9% (p10 của 2020-01→2024-08-21); OFF nếu VOL < 29.6% (= floor × 0.90, hysteresis);
giữa hai mức: giữ trạng thái. Single-shot: chỉ tắt được pha C (6 stamp) — trung thực: biến này một
mình không cứu S0R, chỉ cắt đuôi vol-nén.

**Quy tắc kết hợp (freeze):** GATED = (Biến-1 ON) AND (Biến-2 ON). Gate tính tại stamp T 00:00Z từ
daily data COMPLETED trước T (PIT tuyệt đối), áp lên sách hình thành tại T; đổi trạng thái chỉ xảy
ra tại stamp (weekly, cùng nhịp rebalance — không có intra-week trading).

**Tuyên bố chống-tuning:** không ngưỡng nào được chọn bằng cách xem P&L 2024-08-22+; hai lần duy
nhất gate được áp lên S0R trong dossier này là single-shot mô tả ở §2.6 với ngưỡng đã freeze trước.

---

## 4. PHASE 3 — PREREGISTRATION DRAFT ILLIQ-REG-V1 (tóm tắt; chi tiết trong YAML)

**Tuyên bố ancestry (bắt buộc, verbatim):** mọi kết quả của family ILLIQ-AMIHUD (mọi arm) tính đến
24/09/2026 là **OUTCOME-EXPOSED ANCESTRY**: DIAG −58.9% (S0R, no-funding B2), +13.8% (Y2024P),
+103.6% (Y2021), baseline W2-1 +58.2% (window frozen 2025-08→2026-08) đã bị owner/researcher quan
sát. Bất kỳ kết quả nào tái hiện trên {Y2021, Y2022, Y2023, Y2024P, S0R} đều có trọng số xác nhận
= 0; chúng chỉ dùng làm exploratory/falsification. **Bề mặt xác nhận duy nhất của ILLIQ-REG-V1 là
forward window 2025-08-22→2026-08-21 chạy prospective/shadow sau khi freeze.**

Các khối chính của YAML (đã soạn):

1. **Gate spec frozen** — biến 1 (O1 nguyên trạng + O2 post-hoc có nhãn), biến 2 (vol floor);
   ngưỡng p70/p90/p10 dẫn xuất từ pre-window 2020-01→2024-08-21; hysteresis; PIT law; weekly apply.
2. **Universe** — PIT-listed (list-at-window-start, luật A4; S0R: 20/20 list từ 2024-04-02 → full,
   no divergence); fail-closed giữ nguyên engine (MIN_ELIGIBLE=10, cap 0.30, SKIP law).
3. **Windows** — exploratory: Y2021, Y2024P, S0R (đều outcome-exposed, disclose bắt buộc mỗi dòng);
   confirmatory: forward 2025-08-22→2026-08-21 (shadow trước, scored chỉ sau GO).
4. **Falsification rule** — combo frozen phải qua đồng thời trên S0R DIAG: gated net ≥ −0.295
   (cải thiện ≥50% so −0.5893) VÀ gated MDD ≤ 0.437 (giảm ≥30%); nếu fail → combo FALSIFIED, cấm
   biến thể gate mới trong cycle (không có vòng tuning). Trên forward window: gated net > 0 và
   gated net − ungated net > 0 và rank ≥ p95 trong 200 random-gate; INV-gated phải âm khi anchor
   dương; nếu forward gate ON < 8/52 stamp → test vô lực (inconclusive, không tính GO).
5. **Controls** — INV arm (causal negative control frozen) chạy gated cùng gate; 200 random-gate
   seeded (hoán vị chuỗi gate giữ số toggle + độ dài run tối thiểu 4 stamp).
6. **Stress** — ×1.5 và ×2.0 trên taker fee (baseline slip +1 tick giữ nguyên), áp cho mọi cell
   gated baseline; disclose thêm stress native của engine (×1.5, +2 tick, +1 event delay).
7. **Budget đề xuất** — chu kỳ còn 12/24 (đã dùng 12: 8 XSECT + 4 ILLIQ). Đề xuất dùng **12/12**:
   gated DIAG {ANCHOR, INV} × {Y2021, Y2024P, S0R} × {baseline, ×1.5, ×2.0} = 12 cell
   `scored=False, namespace=REPLICATION_NOT_PROSPECTIVE`, kèm điều kiện tiên quyết: re-run S0R DIAG
   wired-funding (A7-r5 B2 remediation) và re-disclose TRƯỚC cell S0R đầu tiên; forward-window
   shadow KHÔNG tốn budget scored.
8. **Phụ thuộc dữ liệu** — catalog s0r (2024-04→2025-09) + b20 (2020-01→2024-08); funding scan_2026
   (pre-window) + scan_2026_a (S0R/forward); forward window cần bars/funding scan_2026_a đã phủ
   (→2026-08-21) — xác minh PIT coverage là bước đầu của cycle nếu được duyệt.

---

## 5. Phụ lục — file trong namespace & tái hiện

```
research/control/illiq_reg_gate_v1_draft/
├── DOSSIER_illiq_reg_gate_v1.md      (file này)
├── PREREG_ILLIQ-REG-V1.yaml          (bản thảo preregistration — CHƯA đăng ký)
├── forensic_compute.py               (aggregation artifact + observables)
├── pit_conc_gate_single_shot.py      (gate single-shot mô tả)
├── forensic_numbers.json             (toàn bộ số Phase 1)
└── pit_conc_gate_single_shot.json    (ngưỡng + chuỗi gate + replay)
```

Tái hiện (read-only, không lock-heavy):
```bash
cd .worktrees/crypto-historical-replication-3f-v1/integration/research/control/crypto_historical_replication_3f_v1
/Users/hoangminhlong/my-quantitative/.venv/bin/python \
  /Users/hoangminhlong/my-quantitative/research/control/illiq_reg_gate_v1_draft/forensic_compute.py
/Users/hoangminhlong/my-quantitative/.venv/bin/python \
  /Users/hoangminhlong/my-quantitative/research/control/illiq_reg_gate_v1_draft/pit_conc_gate_single_shot.py
```

*Nguồn dữ liệu mô tả (không compute scored): artifact DIAG (3), catalog b20/s0r (parquet 15m), funding
scan_2026/scan_2026_a. Không S1, không gateway, không network fetch.*
