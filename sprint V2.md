# SPRINT V2 — Correctness First · Báo cáo đầy đủ

> **Repo:** my-quantitative · **Ngày:** 2026-08-24 · **A1:** opencode coordinator
> **Verdict cuối: `PIPELINE_PASS_CANDIDATE_FAIL`**
> Pipeline đo đúng, khóa đúng provenance bất biến, tái lập độc lập được.
> 0/98 combo PASS Stage A trên corrected semantics — lần này con số đó đáng tin.
> **Pushed:** main `1941b5d` + branches `wt/correctness-v2`, `wt/data-v2`, `wt/fundcrowd-v2`.

---

## 1. Mục tiêu Sprint V2

Không phải ép tìm strategy thắng. Mục tiêu là **sửa và xác minh research pipeline**:
mọi backtest đo đúng (position-level), không leakage, provenance bất biến,
tái lập độc lập. Source of truth: `PLAN.md` (Sprint V2).

Điểm xuất phát từ V1: `PIPELINE_PARTIAL_PASS_CANDIDATE_FAIL` với 6 lỗi P0 —
(1) PF suy từ fold-net thay vì gross wins/losses; (2) G0/G1 hard-code;
(3) G2 chưa per-candidate, hash mismatch bị gọi "benign"; (4) manifest thiếu
actual hashes/argv/dirty-state; (5) 2 lỗ hổng LIVE guard; (6) ETH unexplained gaps.

## 2. Đội hình & ownership (không chồng chéo)

| Agent | Vai trò | Branch | Commit chính |
|---|---|---|---|
| A1 | Coordinator, Safety & Contract Owner | main | safety fix, contracts v2 (`965f110`), wiring (`0bc1a4c`), handoff (`1941b5d`) |
| A2 | Data Integrity & Coverage | `wt/data-v2` | `d9bc38d` — gap classification, clean-window rule, FundingPIT |
| A3 | Metrics, Backtest & Reproducibility | `wt/correctness-v2` | `62aee90`→`cca964e` — provenance, position-PF, gates, eval v2, matrix |
| A4 | Quant Researcher & Independent Reviewer | `wt/fundcrowd-v2` | `ff6ca0f` analysis/challenge · `d88b24f` fundcrowd implementation |

Handoff được ghi nhận: `matrix_runner.py`, `sprint_eval.py`, `verify_rerun.py`
→ A3 cho V2; protected-file edits (`engine.py` passthrough) do A1 thực hiện có commit riêng.
Merge order: contracts → A3 → A2 → A4(phase-1) → integration → A4(phase-2) → final.

## 3. SAFETY — 2 lỗ hổng P0 đã FIX (A1)

| Lỗ hổng V1 | Fix V2 (`config/settings.py`) | Test |
|---|---|---|
| HOLE-1: `environment='live'` thường bỏ qua guard so-chuỗi `'LIVE'`; không reject giá trị lạ | `ALLOWED_ENVIRONMENTS = {TESTNET, DEMO, LIVE}`; case-normalize qua `object.__setattr__`; giá trị ngoài allowlist → ValueError | lowercase-live raise ✓ · unknown-env raise ✓ |
| HOLE-2: YAML `enable_trading:"false"` → `bool("false")==True` bật execution | `_require_bool()`: chỉ nhận boolean thật; string `"true"/"false"/"0"/"1"` → ValueError; áp cho live loader + DataDownloadSettings env | quoted-false raise ✓ · quoted-true raise ✓ |

Kết quả: **277 passed / 0 failed / 0 xfailed** (từ 201 passed + 2 xfail).
LIVE guard giữ nguyên hiệu lực; live-money changes: none.

## 4. CONTRACTS V2 (`contracts/protocol.py`, freeze bởi A1)

- `GateVerdict.INCONCLUSIVE` bổ sung vào taxonomy (PLAN §9 yêu cầu 4 trạng thái gate).
- `ManifestV2Spec` — schema_version 2, đúng PLAN §7: frozen paths + actual SHA-256,
  `git_commit_at_launch`, `dirty_worktree_at_launch`, `exact_argv`,
  `parameter_lock_utc < run_started_utc` (bất biến kiểm bằng validate → reason
  `lock_not_before_run`), purge/embargo/outer_folds, declared/executed combos.
- `PositionPnLStats` + `position_pnl_stats(pnls)`: PF = Σmax(pnl,0)/|Σmin(pnl,0)|;
  no-trades → None+`no_trades`; no-losers → None+`no_losing_positions`
  (không tự động PASS mẫu nhỏ).
- Reason codes mới: `lock_not_before_run`, `no_trades`, `no_losing_positions`,
  `g0_coverage_not_evidenced`, `g1_evidence_missing`, `positions_digest_mismatch`,
  `funding_publication_lag_violated`.

## 5. CANONICAL PF — sửa lỗi phương pháp V1

```text
SAI (V1): PF ≈ Σ fold-net-dương / |Σ fold-net-âm|     ← gộp net từng fold
ĐÚNG (V2): PF  = Σ max(position_pnl,0) / |Σ min(position_pnl,0)|  ← từng vị thế sau funding
```

Hệ quả đo lường (V1 → V2):

| Combo | PF V1 | PF V2 | Δ | Kết luận |
|---|---:|---:|---:|---|
| vol_compression_breakout BNB v3 | 23.47 | **1.395** | −22.07 | "edge" V1 là artifact phương pháp |
| vol_compression_breakout BNB v2 | 13.63 | **1.278** | −12.35 | vẫn FAIL concentration |
| breakout BNBUSDT | ∞ | 1.169 | n/a | hết "vô cực" |
| reclaim_mr ETHUSDT | 1.84* | 1.131 | −0.71 | FAIL floor fold0 + concentration |

\* Cùng gốc lỗi phương pháp. **verdict_changed = 0/77** — mọi combo vẫn FAIL,
nhưng giờ FAIL bằng đúng lý do định lượng.

Regression tests (hand-calculated, `tests/test_position_pf_v2.py`): mixed
(160/65.5→PF 2.4427), winner-only, loser-only (PF=0 exactly), PF=0.1 exact pair,
empty (`no_trades`), funding đổi thắng→thua (3.33→0.67), reconcile
Σpositions==net==Σfolds @1e-9. **POSITION_PF_REGRESSION_PASS = TRUE.**

## 6. GATES evidence-backed (A3)

- **G0**: đọc coverage payload THẬT; thiếu/malformed → `INCONCLUSIVE(g0_coverage_not_evidenced)`
  — hết hard-code PASS; gap-in-window của ETH → FAIL đúng 11 cells round-1.
- **G1**: 5 evidence bắt buộc (split declared, warmup-outside bằng bars count,
  transforms-fit-on-train, universe frozen trước run, execution model declared);
  thiếu key nào → fail-closed `g1_evidence_missing`.
- **G2**: hash mismatch LUÔN FAIL kể cả khi PnL trùng khớp ("benign" bị xóa sổ);
  so config+candidate+data hashes, positions digest, canonical PnL rtol 1e-6.
- Checkpoint **H9 = PASS** cả 4 mục; **H14 = PASS** (data contract + 77/77 + V1 unchanged).

## 7. DATA CONTRACT (A2) — ETH gaps

| Gap | Window (UTC) | Duration | Slots | Classify | Evidence |
|---|---|---:|---:|---|---|
| ETH-G1 | 08-20 23:59 → 08-21 14:29 (2025) | 870m | 58 | **downloader_failure** (straddle S0 start) | 6 mã peers đủ 58/58 stamps |
| ETH-G2 | 08-21 13:59 → 15:14 (2026) | 75m | 5 | downloader_failure (ngoài S0 end) | BTC/ZEC/AVAX/AAVE đủ 5/5 |
| ETH-G3 | 08-23 05:44 → 06:29 (2026) | 45m | 3 | **unexplained** (fail-closed) | không peer nào phủ window |

- Repair: Binance fapi probe timeout (không egress) → **blocked**, xử lý theo rule.
- **Rule pre-declared TRƯỚC khi xem strategy result**: trim scored start qua gap
  boundary; gap unexplained GIỮA window → loại symbol.
- **Continuous clean intersection: `[2025-08-21T14:30Z , 2026-08-21T00:00Z]`, 7/7 mã.**
- Funding completeness: COMPLETE ×7 (measured missing = 0).
- Artifact: `results/matrix/data_contract_v2/{data_contract_v2.json,gap_investigation.md}` (+checksums inputs).

## 8. THỰC THI MATRIX V2

| Run | Matrix ID | Cells | Kết quả |
|---|---|---:|---|
| Round-1 (S0 gốc) | `v2_stage_a_20260823` | 77/77 COMPLETED | giữ nguyên làm bằng chứng |
| **Final (clean intersection)** | `v2_stage_a_final` | **98/98 COMPLETED, 0 PIPELINE_ERROR** | evaluated → `results/stage_a_v2/` |

Mỗi cell artifact gồm: identity hash, plan/window, folds (kèm `positions_stats`
per-fold: trades/gross_profit/gross_loss/net/PF), positions ledger JSONL,
`positions_digest`. Mỗi EXP dir (`results/stage_a_v2/EXP-*`) chứa: manifest.yaml
schema v2, `frozen/` snapshots + hashes, positions.jsonl, canonical_metrics.json,
gate_result.json, scorecard.json, artifact_hashes.json.

## 9. KẾT QUẢ ĐẦY ĐỦ — 98 combo (exp USDT/lệnh · PF vị thế · sau funding)

**Tổng: 0 PASS · 98 FAIL G3 · G0/G1/G2 = 98 PASS (sau data contract) · G4/G5 = NO_SURVIVOR.**

### 9.1 ema_atr — DEAD (7/7 âm, PF 0.60–0.78)

| Symbol | Trades | Exp | PF | Folds+ |
|---|---:|---:|---:|---:|
| ETH | 414 | −0.3693 | 0.683 | 0/3 |
| SOL | 378 | −0.4561 | 0.683 | 0/3 |
| BNB | 374 | −0.3121 | 0.691 | 0/3 |
| XRP | 378 | −0.4915 | 0.600 | 0/3 |
| DOGE | 384 | −0.2961 | 0.782 | 0/3 |
| LINK | 406 | −0.3882 | 0.751 | 1/3 |
| ADA | 391 | −0.4544 | 0.742 | 1/3 |

### 9.2 mean_reversion — DEAD (7/7 âm, PF 0.55–0.80)

ETH −0.2230/0.804 · SOL −0.5155/0.649 · BNB −0.3571/0.648 · XRP −0.5641/0.569 ·
DOGE −0.6627/0.548 · LINK −0.4805/0.671 · ADA −0.6268/0.628 (278–381 trades mỗi mã, folds+ ≤1/3).

### 9.3 regime_switch — DEAD (7/7 âm, PF 0.64–0.82)

ETH −0.2130/0.816 · SOL −0.4658/0.688 · BNB −0.3642/0.664 · XRP −0.4466/0.644 ·
DOGE −0.5019/0.655 · LINK −0.2680/0.824 · ADA −0.6234/0.647 (487–560 trades).

### 9.4 trend_pullback — DEAD (7/7 âm, PF 0.58–0.95)

ETH −0.3751/0.722 · SOL −0.3193/0.773 · BNB −0.3335/0.715 · XRP −0.0647/0.948 ·
DOGE −0.1748/0.879 · LINK −0.5862/0.636 · ADA −0.7534/0.576 (328–406 trades).

### 9.5 breakout — gần hết mẫu; BNB dương mỏng nhưng FAIL concentration

| Symbol | Trades | Exp | PF | Folds+ | FAIL reasons |
|---|---:|---:|---:|---:|---|
| ETH | 5 | +1.5864 | 1.629 | 1/3 | vô nghĩa mẫu (5 lệnh); concentration |
| BNB | 46 | +0.3898 | 1.169 | 2/3 | fold_concentration_high |
| SOL | 18 | −1.5742 | 0.550 | 0/3 | toàn bộ |
| XRP | 1 | −3.0756 | 0 | 0/3 | toàn bộ |
| DOGE | 11 | −0.8579 | 0.738 | 0/3 | toàn bộ |
| LINK | 7 | −5.2122 | 0 | 0/3 | toàn bộ |
| ADA | 6 | −2.2580 | 0.431 | 0/3 | toàn bộ |

### 9.6 reclaim_mr — ETH dương nhưng FAIL floor + concentration

| Symbol | Trades | Exp | PF | Folds+ | FAIL reasons |
|---|---:|---:|---:|---:|---|
| ETH | 75 | +0.1889 | 1.131 | 2/3 | fold_pf_below_floor; concentration |
| SOL | 78 | −0.2044 | 0.884 | 1/3 | toàn bộ |
| BNB | 87 | −0.3740 | 0.722 | 0/3 | toàn bộ |
| XRP | 77 | −0.9742 | 0.458 | 0/3 | toàn bộ |
| DOGE | 74 | −0.9094 | 0.566 | 0/3 | toàn bộ |
| LINK | 81 | −0.1048 | 0.939 | 1/3 | toàn bộ |
| ADA | 80 | −0.6371 | 0.701 | 1/3 | toàn bộ |

### 9.7 markdown_breakdown — short-only; ADA/BNB dương mỏng, FAIL pf/conc

| Symbol | Trades | Exp | PF | Folds+ | FAIL reasons |
|---|---:|---:|---:|---:|---|
| ETH | 83 | +0.0920 | 1.037 | 1/3 | pf<1.10; folds; concentration |
| SOL | 103 | −0.0323 | 0.988 | 2/3 | exp; pf; fold floor |
| BNB | 58 | +0.1238 | 1.061 | 1/3 | pf; folds; fold floor; concentration |
| XRP | 137 | −0.4549 | 0.815 | 1/3 | toàn bộ |
| DOGE | 162 | −0.0007 | 0.9997 | 1/3 | exp; pf; folds; floor |
| LINK | 99 | −1.1169 | 0.662 | 0/3 | toàn bộ |
| ADA | 139 | +0.0782 | 1.027 | 2/3 | pf<1.10; concentration |

### 9.8 vol_compression_breakout (H-VOLCOMP-BRKOUT-v1) — REJECTED

| Symbol | v0 (96/1.5) | v1 (96/2.0) | v2 (192/1.5) | v3 (192/2.0) |
|---|---|---|---|---|
| ETH | −0.271 (PF .81) | −0.234 (.84) | −0.313 (.78) | −0.363 (.75) |
| SOL | −0.790 (.56) | −0.969 (.47) | −0.770 (.57) | −0.915 (.52) |
| BNB | −0.191 (.81) | −0.050 (.95) | **+0.239 (1.278)** ⚠ | **+0.326 (1.395)** ⚠ |
| XRP | −0.422 (.70) | −0.511 (.65) | −0.192 (.85) | −0.412 (.70) |
| DOGE | −0.538 (.71) | −0.575 (.70) | −0.475 (.74) | −0.412 (.78) |
| LINK | −0.656 (.61) | −0.526 (.69) | −0.475 (.71) | −0.398 (.76) |
| ADA | −0.358 (.79) | −0.214 (.87) | −0.377 (.80) | −0.255 (.86) |

⚠ BNB v2/v3: PF vị thế thật chỉ 1.28/1.39 (không phải 13.6/23.5 như PF-sai V1);
vẫn FAIL `fold_concentration_high`. 26/28 còn lại âm hoàn toàn.

### 9.9 funding_crowding (H-FUNDCROWD-MR-v2) — REJECTED

Spec: family `funding_crowding`, feature `point_in_time_funding_percentile`,
thresholds {70,75,80} × HTF ON = đúng 3 combos, oi_overlay false,
stage S0_EXPLORATORY. Gate PIT: LONG block khi percentile > p/100; SHORT block
khi ≤ (100−p)/100; FundingPIT trả None → block fail-closed (đếm counter);
decision_ts = close ts bar tín hiệu; không bao giờ dùng settlement chưa publish.

| Symbol | v0 (p70) | v1 (p75) | v2 (p80) |
|---|---|---|---|
| ETH | **+0.587 (PF 1.401)** ⚠ | **+0.581 (PF 1.402)** ⚠ | **+0.493 (PF 1.343)** ⚠ |
| SOL | −0.798 (.63) | −0.546 (.74) | −0.325 (.83) |
| BNB | −0.541 (.61) | −0.733 (.49) | −0.808 (.46) |
| XRP | −0.950 (.52) | −0.913 (.53) | −0.941 (.51) |
| DOGE | −0.507 (.75) | −0.400 (.79) | −0.347 (.82) |
| LINK | −0.420 (.80) | −0.472 (.78) | −0.456 (.79) |
| ADA | −0.750 (.67) | −0.685 (.70) | −0.737 (.68) |

⚠ ETH (80–88 lệnh): exp dương, PF vị thế 1.34–1.40, folds 2/3 — nhưng
**concentration 68–81%**: một fold mang đa số PnL → single-fold artifact +
single-symbol universe artifact → trúng điều kiện bác bỏ đã lock trước run.
**Verdict: REJECTED.** Không candidate nào để lock.

## 10. REPRODUCIBILITY (G2)

```text
Independent rerun: funding_crowding ETHUSDT v1 (EXP-20260823-0156)
  config_hash_match    : TRUE
  trades               : 81 = 81
  PnL after funding    : 47.055868 = 47.055868 (exact)
  fold digest          : MATCH
  → G2 PASS (registry VERIFY entry)
Manifest: ManifestV2Spec ×98 validate() sạch; frozen inputs snapshot + actual
SHA-256; artifact_hashes.json từng EXP tự kiểm 0 mismatch.
```

## 11. CHALLENGE MEMO (A4 — phản biện độc lập)

Phát hiện quan trọng nhất: **bar-close fill optimism (HIGH, confidence rất cao)** —
probe trên chính engine của repo: market order submit trong `on_bar(bar_t)` được
fill tại **close bar_t ±1 tick cùng timestamp**, KHÔNG phải open bar kế tiếp;
indicator cũng đã gồm current bar → lookahead nội-bar. Toàn pipeline (V1+V2)
đang tối ưu nhẹ theo hướng có lợi cho strategy. **P0 sprint sau:** one-bar
delayed-entry execution mode. Các phát hiện khác: warmup positions tính theo
ts_closed (LOW-MED); funding audit gộp zero-trade folds vào
funding_coverage_insufficient (MED, đã phân tách trong V2 runner); provenance
gaps V1 (HIGH) — đã fix bằng ManifestV2Spec.

## 12. REGISTRY & TESTS

```text
Registry : results/registry/experiments.jsonl — 178 entries append-only, integrity OK
           (V1 77 FAIL + verify ×2 · V2 round-1 78 · V2 final 98 CANDIDATE_FAIL + VERIFY)
Tests    : .venv/bin/python -m pytest tests/ -q → 277 passed / 0 failed / 0 xfailed
Baseline : 201+2xf → safety fixes + 43 A3 tests + 20 A2 tests + 16 A4 tests
V1 immutability: checksum coverage.json khớp snapshot H14 ✓ · không file V1 bị ghi
```

## 13. BÀI HỌC SPRINT V2

1. **PF fold-net là lỗi nghiêm trọng nhất V1** — thổi phồng 17× trên combo "tốt
   nhất"; chỉ position-level accounting mới đáng tin.
2. Fail-closed gates bắt đúng ETH: 11 cells protocol-fail khi gap chưa resolved,
   được đánh giá lại hợp lệ sau khi rule boundary pre-declared.
3. Execution optimism là hạn chế cấu trúc còn lại: mọi con số hiện tại vẫn hơi
   "tốt hơn thực tế" — one-bar delay là điều kiện tiên quyết trước khi tin bất kỳ
   con số dương nào trong tương lai.
4. Fundcrowd ETH gần sống sót nhất từ trước đến nay (PF 1.40, 81 lệnh) nhưng vẫn
   bị chặn bởi kỷ luật concentration/single-symbol — gate hoạt động đúng.
5. Immutable provenance phát hiện ngay hash-drift (candidate.yaml thêm verdict
   sau run) → phân biệt được "evidence" với "diagnostic".

## 14. BACKLOG

| Ưu tiên | Việc |
|---|---|
| P0 | One-bar delayed-entry execution mode (diệt bar-close fill optimism) |
| P0 | Expectancy-R normalization (hiện MISSING_R_NORMALIZATION → component C nhận 0) |
| P1 | Two-tick slippage model · BTC-beta-neutral benchmark |
| P1 | Batch independent reruns (hiện 1 representative) |
| P2 | Concentration metric refinement (top/total bóp méo khi fold âm nhỏ) — chỉ áp candidate version mới |
| P2 | Native intrarun funding · per-fill digest · DSR/PBO |

S1: chưa capture (không candidate lock). Khi lock: capture SAU parameter_lock_utc,
không xem trước budget pre-registered, chấm một lần.

## 15. ARTIFACT INDEX

```text
contracts/protocol.py                          # +ManifestV2Spec, PositionPnLStats, INCONCLUSIVE
config/settings.py                             # env allowlist + strict bool (A1 safety)
research/provenance.py                         # immutable snapshots (A3)
research/protocol/{metrics,gates,scorecard,manifest,registry,reproduce}.py
research/matrix_runner.py                      # position-level accounting + hypothesis-types
research/sprint_eval.py                        # --schema v2 (mặc định)
research/verify_rerun.py                       # independent G2
research/data_audit.py · research/funding_pit.py (A2)
strategy_funding_crowding_mr.py                # A4 phase-2
research/hypotheses/H-FUNDCROWD-MR-v2/         # spec LOCKED → REJECTED (bằng chứng đầy đủ)
research/hypotheses/_analysis_v2/              # negative analysis + challenge memo + draft
results/matrix/v2_stage_a_final/               # 98 cells + ledgers + v1_v2_comparison.json
results/matrix/v2_stage_a_20260823/            # round-1 evidence (giữ nguyên)
results/matrix/data_contract_v2/               # gap investigation + clean-window contract
results/stage_a_v2/EXP-*/                      # 98 manifests + frozen/ + canonical + gates
results/registry/experiments.jsonl             # 178 entries append-only
research/wayfinder/evidence/sprint-v2-24h-20260824.md   # evidence ngắn chính thức
NOTES.md §20                                   # verdict chính thức
```

Git: main @ `1941b5d`. Sprint chain: PLAN v2 commit → safety fix → contracts v2
(`965f110`) → merges A3/A2/A4 → wiring + lock (`0bc1a4c`) → final (`1941b5d`).
Remote: đã push main + `wt/correctness-v2`, `wt/data-v2`, `wt/fundcrowd-v2`.

