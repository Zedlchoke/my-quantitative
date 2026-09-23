# JRV2-DECISION-AUDIT-V1 — Báo cáo audit độc lập quyết định regime của JEV-REGIME-ROUTER-V2

**Ngày:** 2026-09-23 · **Audited corpus:** JEV-REGIME-ROUTER-V2 terminal worktree
`0c277a94` (clean tree) · **Audit HEAD:** nhánh `orca/jrv2-decision-audit-v1-integration`
· **Phạm vi:** BTC_H1, BTC_H4, SPY_D1 — 13,315 quyết định (8,567 / 1,997 / 2,751).

> **Định vị:** đây là audit chẩn đoán S0. Nó KHÔNG phải cycle tìm strategy,
> KHÔNG sửa JEV V2, KHÔNG đảo ngược verdict `JEV_NO_INCREMENTAL_VALUE`, và
> KHÔNG chứng minh khả năng kiếm tiền. Corpus V2 đã outcome-observed; mọi số
> agreement dưới đây là **đồng thuận blind-vs-JEV, không phải accuracy**
> (không có ground-truth độc lập định nghĩa trước). Không paper/live.

---

## Tóm tắt điều hành (TL;DR)

1. **Pipeline nhất quán và trung thực:** toàn bộ 13,315 quyết định tái tính
   bằng đúng frozen code path khớp tuyệt đối với reports/manifests đã đóng
   băng (counts, digests, occupancy, switches, usage token). **Không có bất
   kỳ bằng chứng lookahead/staleness/schema nào.** Mọi check census: PASS.
2. **76 anomaly `choice ≠ argmax(probabilities)`** (0.19% khối câu hỏi):
   model đôi khi đưa `choice` trái với chính phân phối xác suất của nó ở
   các trạng thái near-tie. **27/27 case ở câu hỏi phase đều bị gate
   `low_confidence` chặn thành UNKNOWN** — lớp an toàn đã hấp thụ hết. 17
   flip ở câu hỏi structure/direction đi vào nhãn effective (10 case dạng
   "rescue" khỏi contradiction, 6 case nhãn khác biệt); contract không ràng
   buộc choice↔argmax nên xếp **ANOMALY_REVIEW**, không phải FAIL.
3. **Blind review 216 case (rubric + seed khóa trước):** khi blind-reviewer
   dám kết luận một phase (125/216), đồng thuận với JEV là **59.2%**; phân
   theo phase: **UPTREND 96% (65/68), DOWNTREND 89% (56/63)** nhưng
   **ACCUMULATION 40%, DISTRIBUTION 8%** — hai phase range gần như không
   đọc được từ state (blind tự bỏ quyền 60–100% tuỳ cell).
4. **UNKNOWN làm cả hai việc:** bảo vệ đúng (30/67 case UNKNOWN-stratum
   blind cũng từ chối) nhưng cũng che (37 case blind đọc được phase còn JEV
   abstain). Ngược lại, **JEV tự tin kết luận trên 61/149 case mà blind
   reviewer không dám kết luận** — model over-commit ở vùng mơ hồ, đúng với
   cảnh báo canary đã ghi ("model answers confidently on mixed evidence").
5. **Có cơ sở để đề xuất thí nghiệm non-JEV MỚI** (mục 6): một gate 3-trường
   trong suốt (slow-trend/ADX/drawdown) đúng ở vùng TREND nơi đồng thuận
   89–96%, nhưng chỉ được xác nhận trên dữ liệu/fold MỚI chưa outcome-observed.
   Không tối ưu ngưỡng trên corpus V2.

---

## 1. Intake và ranh giới

- Re-measure tại thời điểm audit: root `main @ bce0515c` (chỉ untracked
  `.zcode/`, `SANDBOX-OVERFIT-3ASSETS/` — **không đọc**, đúng luật cấm);
  JEV V2 worktree `0c277a94` **clean**; không lock heavy đang giữ;
  `JEV-REGIME-ROUTER-V2 TERMINAL 18/18` trong registry.
- Đã đọc: `AGENTS.md`, plan V2, 10 freeze contracts (digest tự verify lại
  10/10 lúc census chạy), classification + backtest reports, A7-1/A7-2/A7
  terminal audits, `SCORED_GO.json` chain như A7 đã mô tả.
- **Điều KHÔNG làm:** không gọi JEV API (census import chỉ `CacheProvider`;
  không có đường gọi provider), không sửa cache/labels/thresholds/plan V2,
  không chạy scored cell, không mở S1, không đặt lệnh, không đọc V1.
- Mọi code/báo cáo audit nằm trong worktree riêng
  `.worktrees/jrv2-decision-audit-v1/integration`, cycle
  `JRV2-DECISION-AUDIT-V1` đăng ký qua `researchctl` (budget 0 scored cells,
  không GO phrase — không gate nào tiêu GO vì không có call billable/PnL).

## 2. Full census — tái tính bằng code, mọi quyết định

Phương pháp: dựng lại timeline bằng **chính frozen code path** của V2
(`data.load_cell` → `features.RegimeFeatures` →
`questionio.sequential_timeline` + `safety`) với cache provider — hàm mà
scoring đã dùng, không reimplement luật. Kèm các kiểm tra độc lập vượt ra
ngoài validator V2.

| Cell | n | OK | Schema/Timeout/Provider | eff UNKNOWN | Persisted occ (ACC/UP/DIST/DOWN/UNK) | Switches | Max run UNKNOWN persisted |
|---|---|---|---|---|---|---|---|
| BTC_H1 | 8,567 | 8,550 | 6/8/3 | 42.71% | .34/.21/.19/.26/**.0007** | 90 | 6 |
| BTC_H4 | 1,997 | 1,994 | 2/1/0 | 27.24% | .10/.31/.14/.45/**.0035** | 31 | 7 |
| SPY_D1 | 2,751 | 2,750 | 1/0/0 | 29.08% | .003/.70/.03/.26/**.0051** | 34 | 14 |

- Khớp **exact-count** với `bulk_response_manifest_*.json` (effective counts,
  persisted counts, switches, unknown-run, usage, `decisions_sha256` của cả
  3 file decisions). Khớp mọi số classification report (trừ 1 lỗi đánh máy,
  xem anomaly A2).
- **Điểm cần biết đọc:** "Max UNKNOWN run" trong report là run của
  *persisted* UNKNOWN; tất cả persisted-UNKNOWN bars đều nằm ở đoạn khởi động
  (6/7/14 bar đầu) — **sau switch đầu tiên, persisted state không bao giờ
  quay lại UNKNOWN** (đúng thiết kế: UNKNOWN-candidate không đổi trạng thái).
- **State-level lookahead/staleness proxy:** `input_digest` của 13,315 dòng
  tái tạo đúng từ state dựng lại bằng frozen features trên frozen data —
  state mà JEV trả lời chính là state suy ra được từ dữ liệu tại bar t.
  Cộng thêm spot-check nhân quả: 36/36 bar lấy mẫu, tính lại feature trên
  chuỗi **cắt tại t** cho numerics giống hệt chuỗi đầy đủ.
- Fold counts khớp contract: BTC_H1 [2142,2142,2142,2141], BTC_H4
  [500,499,499,499], SPY [688,688,688,687]; không dòng nào ngoài fold.
- Chất lượng response: 100% schema-valid theo validator; prob-sum drift tối
  đa 0.00999 (nằm trong tolerance ±0.01, không dòng vượt); `choice ∈ schema`,
  model pin echo 13,314/13,314 OK-rows; `request_id` unique; usage present
  trên mọi OK row; không duplicate state_id; file order tăng đều bar_index.
- `confidence` của model là scalar **thấp hơn top1-prob** gần như luôn
  (mean −0.05…−0.06; p95 = 0.00): gate 0.50 dùng `confidence` thực chất
  NGHIÊM hơn gate trên top-prob. Contract không định nghĩa quan hệ
  confidence↔probs — ghi nhận là đặc tính đo được, không phải lỗi.

**Anomaly ledger (78 dòng, đầy đủ trong `census/anomalies.json`):**

| # | Loại | Số lượng | Xử lý |
|---|---|---|---|
| A1 | `choice ≠ argmax(probabilities)` | 76 khối câu hỏi (0.19%): phase 27, direction 30, structure 19 | ANOMALY_REVIEW — contract UNSPECIFIED. 27 phase-flips đều bị `low_confidence` chặn (0 lọt). 17 flip question-level trên dòng effective: 10 "rescue" (argmax sẽ thành contradiction→UNKNOWN; choice NEUTRAL cứu thành ACC/DIST), 7 "khác biệt nhưng nhất quán". **Không case nào effective label mâu thuẫn với phân phối của chính nó ở mức đậm đặc** |
| A2 | Classification report Total "Provider OK" = 13,314 | 1 | REPORT_PROSE_ERROR — đúng phải 13,294 (Σ 8,550+1,994+2,750); census xác nhận 13,294 |
| A3 | Manifest BTC_H1 usage (raw) − decisions sum = 310,109 in / 9,289 out | 1 | DISCLOSED_CONVENTION_INFO — đúng 71 adapter-cache mồ côi từ lần bulk TECHABORT 00:17:08Z (partial lines đã xoá, cache còn; `cache_entries 8638 − digest_matches 8567 = 71`). Chính là convention "raw +0.32% vs used-only −0.21%" A7-2 đã công bố. H4/SPY khớp exact 0 mồ côi |

Không anomaly nào là lỗi pipeline. Không case "đẹp được lọc riêng" — census
tính trên **toàn bộ** dòng kể cả lỗi provider/schema và UNKNOWN.

**Vì sao quyết định bị loại (reason census, trả lời câu hỏi owner #1):**

| Lý do effective=UNKNOWN | BTC_H1 | BTC_H4 | SPY_D1 |
|---|---|---|---|
| `low_confidence` (<0.50) | 1,441 (16.8%) | 266 (13.3%) | 480 (17.4%) |
| contradiction structure×direction×prior | 1,139 (13.3%) | 168 (8.4%) | 76 (2.8%) |
| phase disagrees với structure×direction | 1,062 (12.4%) | 107 (5.4%) | 243 (8.8%) |
| provider/schema/timeout (fail-closed) | 17 | 3 | 1 |
| **Đạt nhãn (`ok`)** | **4,908 (57.3%)** | **1,453 (72.8%)** | **1,951 (70.9%)** |

BTC_H1 là cell "nóng" nhất về contradiction (25.7% bars bị loại vì mâu
thuẫn phân cấp) — đúng ở asset biến động cao, nơi các câu trả lời
TREND/RANGE của model hay tự phá luật lineage.

## 3. Blind review (đánh giá ý nghĩa thị trường)

Quy trình chống nhiễm: rubric và sampler **commit trước** khi render case
sheets (thứ tự git đã được checker độc lập xác minh); case sheet chỉ chứa
state mà model thấy (9 bins, 14 numerics, prior lineage, cell) — không nhãn,
không confidence/margin, không timestamp/bar index; 216 case xáo trộn theo
seed; blind verdicts commit xong mới unblind.

**Phân tầng (đủ yêu cầu):** cell × effective-label (cả 4 phase + UNKNOWN);
trong stratum: transition-zone (±3 bar quanh switch) × strength (conf cao/
thấp; UNKNOWN theo reason); phủ 4 fold; phase hiếm lấy all (SPY ACCUMULATION
6/6 — ghi rõ). Tổng **216 case** (BTC_H1 72, BTC_H4 72, SPY 72).

**Kết quả (unblinded, `blind/unblinded_agreement.json`):**

| Stratum (JEV nhãn) | n | Blind từ chối (UNDETERMINED) | Đồng thuận khi blind kết luận |
|---|---|---|---|
| UPTREND (3 cell) | 53 | 10 | **96.3%** (BTC_H1 87.5%, H4 100%, SPY 100%) |
| DOWNTREND (3 cell) | 45 | 14 | **89.4%** (100% / 84.6% / 87.5%) |
| ACCUMULATION | 27 | 20 | **42.9%** (BTC_H1 40%, H4 50%, **SPY 0/0** — blind từ chối cả 6) |
| DISTRIBUTION | 24 | 17 | **7.7%** (0% / 0% / 33.3%) |
| TRANSITION_UNKNOWN | 67 | 30 | — (đo riêng, xem dưới) |

- Tổng: blind dám kết luận 125/216 (58%); đồng thuận **74/125 = 59.2%**.
- **Gradient tự tin có thông tin:** blind tự tin cao → đồng thuận 78.9%;
  trung bình 63.3%; thấp 34.2%. Tự đánh giá của rubric là tín hiệu thật.
- **JEV conf cao ↔ dễ đọc:** case JEV gán nhãn với confidence ≥0.7 đồng
  thuận với blind **91.1%**; conf 0.5–0.7: 71.9%. JEV "đọc được" nhất ở
  chính nơi nó tự tin nhất.
- **UNKNOWN hai mặt:** 67 case JEV-abstain → blind cũng từ chối 30 (45%,
  UNKNOWN bảo vệ trước mơ hồ thật) nhưng blind đọc được phase trên 37 (55%,
  UNKNOWN che mất); ngược lại JEV gán nhãn trên 61/149 case mà blind không
  dám kết luận (41%) — **JEV over-commit ở vùng mờ**.
- Ma trận nhầm (blind→JEV, khi blind kết luận): blind UPTREND → JEV
  UPTREND 42 / UNKNOWN 24 / DISTRIBUTION 6; blind DOWNTREND → DOWNTREND 28 /
  UNKNOWN 10 / ACCUMULATION 4. Blind gần như không bao giờ chủ động gọi
  range-phase (ACC 8, DIST 2 trên 125 lần kết luận).
- Transition-zone đồng thuận 68.2% vs off-zone 54.3% — mô hình chuyển pha
  không tệ hơn phần ổn định; churn của JEV không "đọc lung tung" hơn người.

## 4. Trả lời trực tiếp 5 câu hỏi của owner

1. **Bao nhiêu qua/rớt bộ lọc, vì lý do gì?** 13,315 quyết định: 57.3% /
   72.8% / 70.9% (BTC_H1/H4/SPY) đạt nhãn; phần rớt chủ yếu `low_confidence`
   (~13–17%) và mâu thuẫn phân cấp lineage (BTC_H1 25.7%, SPY chỉ 11.6%).
   Lỗi provider 21/13,315 (0.16%) fail-closed đúng luật. Chi tiết mục 2.
2. **JEV có tự mâu thuẫn hay rất tự tin ở case mơ hồ không?** Có, ở mức đo
   được nhưng bị kiểm soát: 0.19% khối câu hỏi choice trái argmax của chính
   nó (đều near-tie; toàn bộ 27 phase-flip bị gate chặn); và 41% case nó
   gán nhãn là case blind-reviewer phải từ chối. Ngược lại nó cũng abstain
   trên 24 case blind gọi rõ là UPTREND (đa số do conf 0.4x < 0.50).
3. **Phase nào rõ, phase nào mỏng?** UPTREND/DOWNTREND rõ (đồng thuận
   89–96%, JEV conf cao khớp 91%). **ACCUMULATION/DISTRIBUTION mỏng ở mọi
   cell** — blind hầu như không trích được chúng từ state (từ chối 60–100%),
   và khi thử thì gần như không khớp JEV (0–50%). Đây là điểm yếu thật của
   thiết kế: giá trị phân biệt nằm ở 2 phase trend; 2 phase range đang gánh
   phần lớn contradiction + UNKNOWN (mục 2).
4. **UNKNOWN bảo vệ hay che?** Cả hai, định lượng được: bảo vệ 30/67 case
   mơ hồ thật; che 37 case có thể đọc được (55% UNKNOWN-stratum); và mặt
   kia: JEV kết luận 41% case mà người theo rubric phải bỏ. UNKNOWN không
   phải nguyên nhân sụp (không UNKNOWN_COLLAPSE như V1) nhưng tỷ lệ
   eff-UNKNOWN 27–43% là chi phí thông tin lớn, tập trung ở BTC_H1.
5. **Bằng chứng cho bộ quy tắc non-JEV?** Có cơ sở **đề xuất**, chưa đủ để
   khẳng định (mục 6). Dữ liệu chỉ ra signal nằm ở vài trường trong suốt
   (slow EMA slope, ADX, drawdown/extension, dist_ema) — chính các trường
   blind dùng để đạt 89–96% đồng thuận ở trend; vùng range/lineage là nơi
   JEV tốn nhất mà người cũng không đọc ra.

## 5. Bảng kiểm PASS/FAIL/NOT_RUN

| # | Kiểm tra | Kết quả |
|---|---|---|
| C1 | Freeze integrity (10/10 digest) | **PASS** |
| C2 | Data identity + census vs freeze (sha parquet/SPY, gaps) | **PASS** |
| C3 | Coverage/đơn điệu/unique state_id & request_id | **PASS** |
| C4 | input_digest + state_id tái tính (staleness/lookahead proxy) | **PASS** (0 violation; 36/36 causality spot-check) |
| C5 | Schema/prob-sum/model pin/usage presence | **PASS** (max drift 0.00999 < 0.01) |
| C6 | choice == argmax | **ANOMALY_REVIEW** (76 khối; contract không ràng buộc; chi tiết A1) |
| C7 | Đối soát report/manifest exact-count + usage | **PASS** (2 anomaly đã định vị: A2 prose, A3 convention) |
| C8 | Fold counts vs contract | **PASS** |
| C9 | Blinding (masking + thứ tự commit rubric→sheets→reviews→unblind) | **PASS** (2 observation không chặn) |
| C10 | Sampling reproducibility (seed 20260923) | **PASS** (216/216 exact) |
| C11 | Unblind consistency | **PASS** |
| C12 | Kiểm tra phương pháp độc lập (fresh-context checker) | **PASS** 6/6 (+3 observation) — `methodological_check.json` |
| C13 | Ground-truth độc lập cho phase (để gọi là "accuracy") | **NOT_RUN** — không tồn tại theo thiết kế; đo đồng thuận |
| C14 | Gọi JEV API / S1 / credentials | **NOT_RUN** — cấm theo luật, không thử |

## 6. Đề xuất thí nghiệm MỚI (prospective — không tối ưu trên V2)

Bằng chứng đủ để **đăng ký thí nghiệm**, chưa đủ để khẳng định hiệu quả:

- **Câu hỏi falsifiable:** một gate regime trong suốt 3-trường (ví dụ dạng:
  TREND_UP/TREND_DOWN khi `slow_trend` bin khác flat KẾT HỢP `drawdown_state`
  phù hợp và `trend_strength` ≥ medium; range/UNKNOWN cho phần còn lại) có
  đạt đồng thuận rubric ≥ JEV ở vùng trend **và** giảm tỷ lệ
  che-mất-case-đọc-được (37/216 trong audit này) mà không tăng case
  over-commit (61/216), trên dữ liệu chưa outcome-observed?
- **Luật chống nhiễm:** corpus V2 (BTC đến 2026-08-20, SPY đến 2026-09-16)
  đã outcome-observed → **cấm chọn ngưỡng bằng cách nhìn nhãn/kết quả V2**.
  Ngưỡng phải đóng băng từ domain convention + synthetic fixtures (như V2 đã
  làm), rồi kiểm chứng trên cửa sổ dữ liệu MỚI sau các mốc trên (hoặc
  forward/paper-fold), fold đóng băng trước, trial accounting riêng.
- **Đ appropriately scoped:** đúng phạm vi successor
  `REGIME-STRATEGY-MAPPING-V1` (đã PLANNED_NOT_STARTED trong registry) hoặc
  một cycle riêng; audit này chỉ nộp bằng chứng, không tự mở quyền gì.
- **Không khuyến khích:** hạ threshold để tăng trade, tune trên PnL V2,
  hay tái sử dụng GO cũ.

## 7. Bàn giao & tái lập

- `AUDIT_REPORT.md` (file này) · `census/census_rows.csv.gz` (13,315 dòng,
  máy đọc được) · `census/census_summary.json` · `census/anomalies.json`
- `blind/rubric.md` · `blind/sampling.json` (sealed design) ·
  `blind/cases.jsonl` + `blind/case_sheets.md` · `blind/blind_reviews.jsonl`
  · `blind/unblinded_agreement.json`
- `methodological_check.json` · `manifest.json` (sha256 của 13 artifacts +
  digests input + lệnh tái lập)

```bash
cd /Users/hoangminhlong/my-quantitative/.worktrees/jrv2-decision-audit-v1/integration
/Users/hoangminhlong/my-quantitative/.venv/bin/python research/control/jrv2_decision_audit_v1/tools/census.py      # census đầy đủ
/Users/hoangminhlong/my-quantitative/.venv/bin/python research/control/jrv2_decision_audit_v1/tools/sample_blind.py # tái lập mẫu (seed 20260923)
/Users/hoangminhlong/my-quantitative/.venv/bin/python research/control/jrv2_decision_audit_v1/tools/unblind.py      # join + thống kê
```

*Lưu ý tái lập: `census.py`/`sample_blind.py`/`unblind.py` deterministic;
`blind_reviews.jsonl` là bản ghi review của người, không regenerate.*

---

**Ranh giới đã giữ:** không push, không merge main, không đụng V2/V1/S1,
không broker surface, registry chỉ qua `researchctl`. Audit này là chẩn đoán
S0 trên corpus outcome-observed: **không chứng minh khả năng kiếm tiền,
không cho phép paper/live, không đảo verdict terminal của V2.**
