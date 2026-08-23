# SPRINT V1 — Quant Research Loop 24h · Báo cáo đầy đủ

> **Repo:** my-quantitative · **Ngày:** 2026-08-23 · **A1:** opencode coordinator
> **Verdict cuối: `PIPELINE_PASS_CANDIDATE_FAIL`**
> Pipeline dựng thành công, chạy end-to-end, tái lập được; 0/77 combo PASS Stage A
> → hệ thống đã loại đúng các false edge thay vì bán kỳ vọng.

---

## 1. Mục tiêu & phạm vi

Dựng **Minimum Viable Quant Research Factory** theo `PLAN.md` (source of truth):

```text
Hypothesis → khóa spec → implement → backtest matrix → chronological
walk-forward + costs + funding → hard gates + scorecard → PASS/FAIL/INCONCLUSIVE
→ registry append (giữ cả negative) → học → hypothesis kế (nếu còn budget)
```

Không bắt buộc tìm PASS. `PIPELINE_PASS_CANDIDATE_FAIL` là thành công nếu hệ
thống loại đúng false edge — và nó đã làm đúng điều đó.

## 2. Đội hình & cách phối hợp thực tế

| Agent | Vai trò | Branch/worktree | Commit chính |
|---|---|---|---|
| A1 | Coordinator, Contract Owner, Integrator, Final Reviewer | main | `f57ad34` contracts, `46d3658` wiring, `f40d86d` handoff |
| A2 | Data, Universe & Backtest Matrix | `wt/data-matrix` | `4ecd8bf` |
| A3 | Validation, Metrics, Risk, Reproducibility | `wt/validation-protocol` | `d2928ee` |
| A4 | Hypothesis & Strategy Engineer | `wt/research-loop` | `7623808` |

Lưu ý kiến trúc: A2–A4 là **subagent nội bộ** của phiên A1 (không phải 4 CLI riêng).
Merge order tuân thủ PLAN §5: contracts → schemas (A3) → runner (A2) → strategy (A4).

## 3. Contracts đã khóa (`contracts/protocol.py`) — bất biến của sprint

- **Verdict taxonomy cell:** COMPLETED / REUSED / CANDIDATE_FAIL / INCONCLUSIVE /
  DATA_INCOMPLETE / PIPELINE_ERROR / NOT_RUN_BUDGET.
- **Sprint verdict hợp lệ:** chỉ 4 giá trị; cấm EDGE_CONFIRMED / PRODUCTION_READY /
  LIVE_READY.
- **Manifest 29 trường** đúng PLAN §8 (config hash, data snapshot, split policy,
  cost assumptions, seed nullable có lý do, trial count…).
- **Canonical metrics:** mọi metric là `value + reason`; metric không tính được
  trả `null + reason code`, **cấm default 0.0** (chặn đúng bug cũ: drawdown bị
  report 0 khi engine thiếu key).
- **Reason codes enum** cho G0–G5 + pipeline (~40 mã) — mọi artifact dùng mã trong enum.
- **Scorecard 100 điểm:** economic 10 · data/leakage 15 · edge quality 25 ·
  robustness 15 · cost realism 10 · risk 10 · portfolio 5 · reproducibility 10;
  band: <50 reject · 50–59 diagnostic · 60–69 exploratory · 70–79 lock-for-OOS ·
  ≥80 strong-candidate (vẫn chưa confirmed edge).
- **Budget:** ≤3 hypotheses · ≤2 strategy mới · ≤16 combo/hypothesis · ≤2 iterations ·
  cutoff H18 · workers ≤2.

## 4. Data audit (`research/data_audit.py` → coverage.json)

- Universe khai báo: top-20 USD-M từ `config/research_scan_top20.yaml`.
- **Eligible: 19/20** — duy nhất `ETHUSDT` DATA_INCOMPLETE với 3 gaps
  (870min @2025-08-20→21 straddle đầu S0; 75min @2026-08-21; 45min @2026-08-23).
  Gaps được gắn cờ vào gate G0, không âm thầm bỏ qua.
- Common intersection all-universe: 2024-08-23 → 2026-08-21 (70,045+ bars/mã),
  phủ declared S0 ✓.
- Funding bundles `funding_data/scan_2026`: đủ 20/20, requested 730 ngày.
- Instrument metadata: đủ cho toàn universe.

## 5. Hypotheses (3/3 budget)

### H-VOLCOMP-BRKOUT-v1 — volatility_compression_breakout (IMPLEMENTED → REJECTED)
- **Mechanism:** squeeze BB-bandwidth (rank ≤25 trong trailing window, đánh giá
  trên bar *trước* trigger — no lookahead) giải phóng bằng expansion leg; entry
  Donchian-upper close-breakout + volume burst mua trước đám breakout-chaser.
- **Rules frozen trước scored run:** long-only; stop 1.5×ATR (đóng băng tại fill);
  TP 2R; exit khi close < BB basis; 15m; warmup ≥200 bar (212); universe S0 7 mã.
- **Grid 4 combo:** squeeze_lookback {96,192} × volume_min_ratio {1.5,2.0}.
- **State:** SPEC_LOCKED bởi A1 trước run → REJECTED sau kết quả (xem §8).

### H-FUNDCROWD-MR-v1 — funding/OI crowding (SPEC_DRAFT, chờ S1)
- reclaim_mr gate thêm funding-rate percentile (settlement cuối, point-in-time
  safe 8h): skip long khi funding percentile > ngưỡng {70/75/80}.
- Data khả thi (bundle 730d), nhưng **không implement trong sprint** — cần cửa sổ
  mới để tránh in-sample.

### H-XSECT-REVERSAL-v1 — cross-sectional reversal (IDEA, blocked)
- Common intersection ~1 năm + thiếu portfolio-engine cho rank rebalance → ghi rõ
  DATA_INCOMPLETE, không triển khai.

## 6. Strategy mới đã implement (1/2 budget)

`strategy_vol_compression_breakout.py` — Nautilus Strategy, tự chứa settings
(không đụng `config/settings.py`), tái sử dụng house plumbing `_submit_entry/
_submit_exit`, daily-loss cap, cooldown 4 losses, allow_short=False bắt buộc.
Wiring tích hợp do A1 thực hiện: factory branch + runner param-variants +
passthrough kwarg trong `run_backtest_for_symbol` (protected-file handoff có ghi
nhận commit `c74cf31`).

## 7. Thực thi matrix

| Tier | Phạm vi | Declared | Completed | PIPELINE_ERROR |
|---|---|---:|---:|---:|
| Tier 0 smoke | strategies × ETH/SOL (3 ngày, warmup cap 10d) | 16 | 16 | 0 |
| Tier 1 existing | 7 frozen strategies × 7 mã S0 × 3 folds | 49 | **49** | 0 |
| Tier 1 volcomp | 4 combo × 7 mã × 3 folds | 28 | **28** | 0 |

- Window Stage A: S0 2025-08-21 → 2026-08-21, 3 fold chronological
  (~4 tháng/fold), warmup ngoài window (baselines 220 ngày, volcomp 212 bar).
- Costs: maker/taker theo instrument + one-tick adverse fill + **funding
  post-trade audit từng position** (metric chính là after-funding).
- Resumable: index theo identity (strategy, symbol, variant, config-hash,
  snapshot, split, fee, slippage, seed) → rerun sinh REUSED.
- Mỗi cell = 1 artifact JSON độc lập; cell crash → PIPELINE_ERROR cô lập,
  matrix chạy tiếp.

## 8. KẾT QUẢ ĐẦY ĐỦ — 77 combo (exp/PF sau funding)

**Tổng: 0 PASS · 77 FAIL Stage A · không có survivor → G4/G5 = NOT_APPLICABLE.**

### 8.1 Existing frozen strategies (49 combo)

| Strategy | Symbol | Exp sau funding | PF | Trades | Kết luận |
|---|---|---:|---:|---:|---|
| breakout | ETHUSDT | +1.5864 | inf | 5 | FAIL (5 trades = vô nghĩa mẫu) |
| breakout | BNBUSDT | +0.3209 | inf | 47 | FAIL concentration |
| breakout | ADA/SOL/DOGE/LINK/XRP | −0.86…−5.21 | ~0 | 1–18 | FAIL toàn tiêu chí |
| ema_atr | ETHUSDT | −0.3701 | 0 | 415 | FAIL |
| ema_atr | ADA/BNB/DOGE/LINK/SOL/XRP | −0.31…−0.49 | 0–0.26 | 374–407 | FAIL |
| mean_reversion | ETHUSDT | −0.2230 | 0.18 | 278 | FAIL |
| mean_reversion | 6 mã còn lại | −0.36…−0.67 | ~0 | 304–383 | FAIL |
| regime_switch | 7 mã | −0.21…−0.61 | 0–0.22 | 487–562 | FAIL |
| trend_pullback | 7 mã | −0.07…−0.75 | 0–0.55 | 328–408 | FAIL |
| **reclaim_mr** | **ETHUSDT** | **+0.1889** | **1.84** | **75** | **FAIL fold_pf_floor + concentration** |
| reclaim_mr | 6 mã còn lại | −0.10…−0.99 | 0–0.46 | 75–87 | FAIL |

Chi tiết fold các combo đáng chú ý nhất:

```text
reclaim_mr ETHUSDT:   fold0 (08-12/25): 31 lệnh, −16.85 ← fold0 PF < 0.80 floor
                      fold1 (12/25-04/26): 20, +21.30
                      fold2 (04-08/26):    24, +9.72   → tổng +14.17 nhưng FAIL
markdown_breakdown ADAUSDT (BEST existing):
                      fold0: +8.68 | fold1: −30.20 | fold2: +32.38
                      tổng +10.86 · exp +0.0782 · PF 1.36 · 139 trades
                      FAIL: top fold >50% tổng PnL
markdown_breakdown BNBUSDT: exp +0.2119 · PF 1.75 · 55 trades — folds dương <2/3
```

### 8.2 H-VOLCOMP-BRKOUT-v1 iteration 1 (28 combo) → REJECTED

Expectancy sau funding (PF trong ngoặc):

| Symbol | v0 (96/1.5) | v1 (96/2.0) | v2 (192/1.5) | v3 (192/2.0) |
|---|---|---|---|---|
| ADAUSDT | −0.358 (0) | −0.214 (0.52) | −0.377 (0.01) | −0.255 (0.34) |
| BNBUSDT | −0.212 (0) | −0.077 (0.55) | **+0.219 (13.6)** ⚠ | **+0.302 (23.5)** ⚠ |
| DOGEUSDT | −0.564 (0) | −0.575 (0) | −0.496 (0.08) | −0.412 (0.18) |
| ETHUSDT | −0.271 (0.29) | −0.234 (0.38) | −0.313 (0) | −0.363 (0.02) |
| LINKUSDT | −0.656 (0) | −0.526 (0.04) | −0.475 (0.02) | −0.398 (0.03) |
| SOLUSDT | −0.790 (0) | −0.969 (0) | −0.770 (0) | −0.915 (0) |
| XRPUSDT | −0.422 (0.16) | −0.511 (0.18) | −0.190 (0.34) | −0.408 (0.16) |

⚠ Chi tiết fold BNBUSDT v2/v3 — lý do KHÔNG được coi là edge:

```text
v2: fold0 +24.09 (54 lệnh) | fold1 −2.67 | fold2 +12.25 → top ≈ 72% tổng > 50%
v3: fold0 +24.76 | fold1 −1.82 | fold2 +17.89            → top ≈ 58% > 50%
→ CẢ hai FAIL `fold_concentration_high`. PF lớn một phần do fold âm quá nhỏ
  làm mẫu số co lại. Đây đúng loại "một kỳ may" mà gate tồn tại để chặn.
```

26/28 còn lại: expectancy âm sau funding, đa số PF≈0.

### 8.3 Đọc kết quả — 3 nhận định định lượng

1. **Không có edge nào sống qua Stage A trên S0** ở cả 77 combo → mọi claim
   "chiến lược có lãi" trước đây đều chưa vượt chuẩn này.
2. `fold_concentration_high` là reason phổ biến nhất trên các combo exp dương →
   gate chống single-fold-luck hoạt động đúng vai trò.
3. Baseline strategies "an toàn" (ema_atr, mean_reversion, regime_switch,
   trend_pullback) thua đều và THUA LỚN về sample (300-500 lệnh/mã) → bằng chứng
   mạnh rằng chúng không có edge trên crypto 15m S0; nên loại khỏi watchlist.

## 9. Reproducibility verification (G2)

| Experiment | Hash | Trades | PnL after funding | Fold digest | Verdict |
|---|---|---:|---:|---|---|
| markdown_breakdown ADAUSDT (EXP-20260823-0049) | ✓ | 139=139 | 10.863531 = 10.863531 | ✓ | **PASS** |
| vol_compression_breakout BNBUSDT v2 | ✗* | 154=154 | 33.674711 = 33.674711 | ✓ | FAIL benign* |

\* Benign: `candidate.yaml` được thêm ghi nhận REJECTED SAU khi chạy → hash file
đổi, economics khớp tuyệt đối. Provenance hoạt động đúng mục đích.

Registry: `results/registry/experiments.jsonl` — **79 entries append-only,
integrity OK** (77 CANDIDATE_FAIL + 2 VERIFY entries).

## 10. Safety & LIVE guard

- Guard giữ nguyên hiệu lực suốt sprint; KHÔNG live-money change; KHÔNG YAML param đổi.
- Audit 13 đường dẫn entry (`research/protocol/live_guard_audit.md`) + 11 tests pass.
- **2 lỗ hổng đã biết (P0 backlog, CHƯA fix theo đúng scope):**
  1. `LiveSettings(environment='live', enable_trading=True)` lọt qua guard so-chuỗi case-sensitive `'LIVE'` (config/settings.py:488).
  2. YAML `enable_trading:"false"` dạng chuỗi → `bool("false")==True` bật execution mức Testnet (config/settings.py:754).
  Cả hai được khóa bằng `xfail(strict=True)` — nếu ai fix sẽ XPASS và buộc cập nhật test.

## 11. Tests

```text
Baseline H0 : 54 passed
Sau contracts: 67 passed
Final main  : 201 passed + 2 xfailed  (.venv/bin/python -m pytest tests/ -q)
LIVE guards : 11 passed + 2 xfailed
Thời gian full suite: ~3s
```

## 12. Bài học sprint

1. Gate chống concentration là lớp phòng vệ hữu dụng nhất sprint — mọi combo
   exp dương đều rơi vào đây, không có ngoại lệ "đáng tin".
2. Metric default 0.0 (drawdown) từng là bug im lặng thật — contract null+reason
   + regression test chặn vĩnh viễn lớp bug này.
3. Silent-skip download (bẫy W1) giờ fail-loud với reason `catalog_not_current`.
4. Subagent model (không phải 4 CLI riêng) phối hợp hiệu quả qua worktrees +
   merge order + contracts import chung.
5. Không mở iteration 2 trên cùng S0 dù còn budget — variant suy ra từ fold đã
   nhìn = in-sample. Kỷ luật này đáng giá hơn một PASS giả.

## 13. Backlog

| Ưu tiên | Việc |
|---|---|
| P0 | Fix 2 LIVE-guard holes (normalize case; strict bool parse) → xfail thành XPASS |
| P0 | Capture **S1 untouched** (sau param-lock) cho H-FUNDCROWD-MR-v1 |
| P1 | Two-tick slippage fill model + one-bar delayed-fill → G4 hết NOT_IMPLEMENTED |
| P1 | BTC-beta-neutral context benchmark cho altcoin |
| P2 | Cân nhắc tinh chỉnh metric concentration (top/total bị fold âm nhỏ bóp méo) — chỉ sửa gate cho candidate version MỚI, không hồi tố |
| P2 | Native intrarun funding · per-fill digest · DSR/PBO stats |

## 14. Artifact index

```text
contracts/protocol.py                     # schemas/reasons/scorecard/budget (A1)
research/protocol/                        # manifest, registry, metrics, gates, scorecard, reproduce (A3)
research/data_audit.py                    # coverage audit (A2)
data/incremental.py                       # fail-loud fetch (A2)
research/matrix_runner.py                 # resumable Tier0/Tier1 runner (A2)
research/sprint_eval.py                   # bridge matrix→gates→registry (A1)
research/verify_rerun.py                  # independent G2 verifier (A1)
strategy_vol_compression_breakout.py      # strategy mới (A4)
research/hypotheses/*/                    # 3 hypothesis specs + ANALYSIS_MEMO
results/matrix/stage_a_s0_20260823/       # 49 cells + index + report
results/matrix/stage_a_volcomp_iter1/     # 28 cells + index + report
results/matrix/audit_20260823/coverage.json
results/stage_a/EXP-*/                    # 77 manifest/gate/scorecard dirs
results/registry/experiments.jsonl        # 79 entries append-only
research/wayfinder/evidence/sprint-24h-20260823.md          # evidence ngắn
research/wayfinder/evidence/sprint-24h-20260823-H0_checkpoint.md
NOTES.md §19                              # sprint verdict chính thức
```

Git: main @ `f40d86d` (sprint chain: contracts `f57ad34` → merges → integration
`46d3658` → protected handoff `c74cf31` → handoff `f40d86d`).

