# CONTINUE.md — Handoff cho Hermes · Sprint V5→V6 (master PLAN §28–40)

> **Viết bởi:** A1 (opencode) lúc 2026-08-24 ~05:00 UTC
> **Mục đích:** migrate toàn bộ trạng thái đang dở của Sprint V5 (Scientific
> Integrity Closure) + chuẩn bị V6 (H-XSECT-FUNDING-CARRY-v1).
> **Nguyên tắc:** PLAN.md §28–40 là source of truth. Không rescue candidate cũ.
> Không fake independent audit. Không đụng S1. Không live money.

---

## 1. TRẠNG THÁI MÔI TRƯỜNG KHI BÀN GIAO

| Hạng mục | Giá trị đã xác minh |
|---|---|
| Repo | `/Users/hoangminhlong/my-quantitative`, branch `main`, remote `origin=github.com/Zedlchoke/my-quantitative` |
| Commit cuối trên main | `0d38feb` + các commit V5 sau đó (xem `git log --oneline -8`) |
| **UNCOMMITTED** | `research/portfolio_runner.py`: patch CLI flags `--output-root / --registry-kind / --source-trial-experiment-id` (**ĐÃ TEST, CHƯA COMMIT — commit việc đầu tiên**) |
| Python | 3.12.14 qua `.venv/bin/python` (LUÔN dùng đường dẫn tuyệt đối này) |
| NautilusTrader | 1.230.0 |
| Baseline tests | **553 passed / 0 failed / 0 xfailed** (sau khi merge cả 2 nhánh V5); chạy lại full suite ngay khi nhận |
| Worktrees còn sống | `../my-quantitative-wt/{v5-metrics, v5-accounting, ...}` — đã merge vào main, có thể prune |

### Lệnh đầu tiên cần chạy

```bash
cd /Users/hoangminhlong/my-quantitative
git add research/portfolio_runner.py && git commit -m "A1 V5: portfolio_runner CLI flags --output-root/--registry-kind/--source-trial-experiment-id"
.venv/bin/python -m pytest tests/ -q   # kỳ vọng ≥553 passed
date -u +%Y-%m-%dT%H:%M:%SZ
```

---

## 2. SUBAGENT INFRA — ĐÃ SẬP, ĐÂY LÝ DO TÔI DỞ VIỆC

- Task dispatch về provider liên tục trả `finish_reason: network_error`
  (kể cả probe prompt 1 từ). Phiên chính vẫn hoạt động bình thường.
- **Hệ quả:** tôi tự thực hiện kỹ thuật thay (được phép theo PLAN §30), nhưng
  **A4 independent audit KHÔNG ĐƯỢC giả mạo bởi A1**.
- **Hành động cho Hermes:** thử dispatch một subagent nhỏ ngay khi nhận.
  Nếu hạ tầng đã hồi phục → dùng nó cho bước A4 audit (mục 5). Nếu không:
  verdict trung thực là `INDEPENDENT_AUDIT_BLOCKED` → `BLOCKED_BY_V5`
  (terminal outcome hợp lệ theo §32/§39).

---

## 3. NHỮNG GÌ ĐÃ XONG (V5)

### Phase 0–1 ✅
- `research/audits/v5/baseline_v5.json` — commit/tests/python/nautilus lúc H0.
- `research/audits/v5/v3_v4_source_hashes.json` — **1474 file** V3/V4 hash
  freeze (kiểm tra lại cuối sprint cho V5-C02: chỉ được lệch
  `results/registry/experiments.jsonl` do append-only).
- `research/audits/v5/v3_v4_findings.json` — đủ F01–F16 (PLAN §28.3).
- `research/audits/v5/global_trial_ledger.json` — phân loại toàn bộ registry:
  **472 SCORED_TRIAL (99 unique configs)** · 18 REPRODUCTION · 1 NEGATIVE_CONTROL.
  Con số **99 unique scored configs** là N cho DSR ở V6.

### Merge nền tảng ✅ (main chứa tất cả)
- **A2 (`wt/v5-accounting`, merged):** `research/accounting.py`
  (`map_to_canonical` raise khi thiếu field — hết F01;
  `build_accounting_reconciliation` identity
  `ΔE = closed_price_pnl + terminal_pnl + funding − commissions − slippage − rejection_costs`
  tol 1e-9); engine `TERMINAL_POLICY="FORCE_LIQUIDATE_AT_LAST_OBSERVABLE_BAR"`
  (hết F04); continuous capital `reset_folds=False` mặc định (hết F03);
  exposure controller `RISK_MODE_V1` (target 0.80/cap 1.00/net ±0.10,
  check **mọi bar 15m**, breach → reduce-only same-bar — hết F09);
  funding grid từ ACTUAL settlement timestamps + jitter snap ±120s
  (hết nửa F06); `coverage_report` tách 4 block
  bar/benchmark/funding/metadata (chuẩn bị F06).
- **A3 (`wt/v5-metrics`, merged):** family metrics KHÔNG fake-R
  (`daily_sharpe` id `DAILY_SHARPE_RF0_V1`; `chained_returns_mdd` id
  `CHAINED_FOLD_RETURNS_MDD_V1`; contribution bắt `ContributionMismatch`
  nếu parts≠total — hết F02); reason semantics `not_tested` /
  `metric_missing` / `*_negative` tách bạch (hết F08);
  XG1 đếm từ ledger thật + XG2a đo bằng `research/reconciliation.py`
  `verify_experiment_dir` (hash mọi file, newest-mtime check bắt F15,
  không nhận bare True — hết F16);
  `research/dsr.py` DSR Bailey/López de Prado dùng variance ACROSS trial
  Sharpes + N global; PBO/CSCV `NOT_ENOUGH_CONFIGURATIONS` nếu <8 configs;
  `sprint_eval --schema v5` + `finalize_artifacts()` ghi
  `artifact_hashes.json` CUỐI cùng kèm `.hashes_final` guard.

### Phase 6 — 4 recalcs `-DIAG-V5` ✅ (vừa chạy xong, chưa commit vì results/ gitignored)
```
results/diagnostic_v5/XSECT-MOM-3D-DIAG-V5            verdict REJECTED (score 13 DIAGNOSTIC_ONLY)
results/diagnostic_v5/XSECT-MOM-7D-DIAG-V5            REJECTED
results/diagnostic_v5/XSECT-MOM-14D-DIAG-V5           REJECTED
results/diagnostic_v5/XSECT-REVERSE-7D-CONTROL-DIAG-V5 REJECTED
```
Registry kind `DIAGNOSTIC_RECALC` + `--source-trial-experiment-id` link đúng
V4 gốc. **Không tăng trial count.**

---

## 4. VIỆC CÒN DỞ — LÀM THEO THỨ TỰ

### Bước 4.1 — Independent reproduction ×4 (→ V5-C20)
```bash
for pair in "XSECT-MOM-3D-DIAG-V5:VERIFY-DIAG-3D" \
            "XSECT-MOM-7D-DIAG-V5:VERIFY-DIAG-7D" \
            "XSECT-MOM-14D-DIAG-V5:VERIFY-DIAG-14D" \
            "XSECT-REVERSE-7D-CONTROL-DIAG-V5:VERIFY-DIAG-CTRL"; do
  IFS=: read exp vid <<< "$pair"
  rm -rf results/reproduction_v5/$vid
  .venv/bin/python -m research.portfolio_runner --reproduce results/diagnostic_v5/$exp --verify-id $vid
done
```
Yêu cầu: `all_match=true` **×4**, registry kind `INDEPENDENT_RERUN_VERIFY`.
Lưu ý: kiểm tra output-root của reproduce worker trỏ đúng
`results/diagnostic_v5` (nếu worker ghi nhầm vào portfolio_v4 thì sửa path
trước khi chấp nhận).

### Bước 4.2 — Comparison old/new (F01/F03/F04/F05/F09 evidence)
Tạo `results/matrix/v4_recalc_diagnostic_v5/v4_v5_recalc_comparison.json`:
so từng cặp OLD `results/portfolio_v4/<orig>/canonical_metrics.json` vs NEW
`results/diagnostic_v5/<diag>/canonical_metrics.json` trên:
`total_pnl, pf_position_level.profit_factor, fold_pnls, gross_max,
net_abs_max, max_drawdown_fraction, legs_closed, top_symbol_share`
+ NEW-only presence: `terminal_positions` count,
`funding_cashflows` rows, `commission_slippage` totals.
Kỳ vọng định tính: gross_max mới ≤1.0 (controller), terminal legs >0,
funding rows >0, leg PnL ≠ 0 hàng loạt như V4.

### Bước 4.3 — Finalize + tests + commit
```bash
.venv/bin/python -m research.portfolio_runner --finalize-matrix --matrix-dir results/matrix/v4_recalc_diagnostic_v5
.venv/bin/python -m pytest tests/ -q        # kỳ vọng 553+ (hoặc hơn nếu thêm test)
git add -A && git commit -m "V5 Phase-6: DIAG-V5 recalcs x4 + reproductions x4 + comparison"
```

### Bước 4.4 — Stresses & drop-one (→ V5-C14/C15) — **CHƯA LÀM**
- fee×1.5 và two-tick: engine đã nhận `fee_multiplier`/`adverse_ticks` qua
  adapter → chạy lại mỗi DIAG với `PORTFOLIO_V4_*`-style params tương ứng
  (adapter map `fee_taker=0.0005*mult`, `slippage_ticks=1+ticks`).
- **extra 15m delay: CHƯA implement** — adapter hiện raise
  NotImplementedError. Cần implement: dịch điểm thực thi sang bar-event kế
  tiếp trong `portfolio_engine` (tham số `extra_delay_events`) + test.
- drop-one-symbol / drop-one-fold: drop-one-fold tính được từ fold results
  sẵn có; drop-one-symbol cần engine nhận `exclude_symbols` set → thêm +
  test.
- Mọi kết quả stress PHẢI ghi `not_tested` nếu chưa chạy, `<name>_negative`
  chỉ khi đã chạy và âm (không được vi phạm lại F08).

### Bước 4.5 — Freeze + A4 audit (→ V5-C22)
1. Chạy full suite lần cuối, ghi kết quả vào
   `research/audits/v5/final_tests_v5.json`.
2. Re-hash 1474 file nguồn so với `v3_v4_source_hashes.json` → chỉ
   `registry.jsonl` được phép khác (append-only). Ghi
   `research/audits/v5/source_hash_recheck_v5.json`.
3. **Code freeze tuyên bố.**
4. Dispatch subagent MỚI (chưa bao giờ tham gia implement) làm A4 read-only:
   - audit: accounting identity, hashes, leakage, signal<fill ordering,
     fold boundaries, terminal liquidation, funding PIT + cadence,
     commission/slippage, trial ledger, reason semantics, reproductions;
   - random sample ≥50 orders, ≥50 positions, ≥30 funding settlements,
     toàn bộ fold boundaries — lưu seed+sample hash;
   - outputs: `research/audits/v5/challenge_memo_v5.md` +
     `scientific_audit_v5.json` ký PASS/FAIL/INDEPENDENT_AUDIT_BLOCKED.
   Nếu subagent infra vẫn sập tới đây → ghi
   `INDEPENDENT_AUDIT_BLOCKED`, **dừng, không mở V6**.

### Bước 4.6 — `results/matrix/v4_recalc_diagnostic_v5/v5_transition.json`
Machine-readable V5-C01..C26 (nguyên văn tên criterion trong PLAN §32),
mỗi mục {verdict, evidence_path[], command?, reason_if_fail}.
Chỉ `all_pass=true` → `"transition":"V6_AUTHORIZED"`. Commit + push.

---

## 5. SPRINT V6 (CHỈ KHI V6_AUTHORIZED)

1. Viết `research/hypotheses/H-XSECT-FUNDING-CARRY-v1/hypothesis.md` +
   `candidate.yaml` đúng khối YAML PLAN §33.2 (lookbacks [1,3,7], long
   bottom-2 funding / short top-2, target_gross 0.80, |w|≤0.20, budget
   3+1 reverse_funding_rank_3d, purge/embargo 24h) → **SPEC_LOCKED trước
   signal code** (state + locked_at_utc = thời điểm thật).
2. Signal thuần (A1 làm được sau lock): `research/funding_rank_signal.py`
   — trailing MEAN của published settled funding (dùng
   `research/funding_pit.py`, chỉ settlements đã publish ≤ cutoff),
   lookback 1/3/7 ngày, long bottom-2 / short top-2 (±0.20 mỗi symbol
   theo cap), reverse flag cho control, SKIP nếu thiếu bất kỳ symbol.
   Unit test: PIT không lookahead, tie-break, missing→skip, determinism.
3. Adapter: mở rộng `_default_engine_loader()` trong
   `research/portfolio_runner.py` để nhận `signal_kind=funding_carry`
   (weight_fn wrap signal mới) — giữ nguyên mẫu adapter hiện có.
4. Chạy đúng 4: `XSECT-FUND-CARRY-1D / 3D / 7D` +
   `XSECT-FUND-REVERSE-3D-CONTROL` vào `results/matrix/v6_xsect_funding_carry/`
   + `results/portfolio_v6/<id>/` (artifact set đầy đủ theo §38).
5. Gates FG0–FG6 (PLAN §35) + mechanism check riêng: total PnL>0 AND
   net funding cashflow>0 AND ≥2/3 folds funding dương (price PnL không
   được cứu funding âm — ghi rõ trong gate_result).
6. Scorecard 100 điểm theo §36; eligible = all(FG)+score≥75+DSR≥0.95
   (N=99 từ ledger)+audit PASS. Tie-break: DSR cao nhất → MDD thấp →
   turnover thấp. Lock tối đa 1 candidate → ghi S1 start timestamp sau
   lock, KHÔNG đọc S1.
7. Reproduction: rerun 100% survivors; nếu 0 survivor thì best diagnostic
   + negative control (separate process bắt buộc).
8. A4 audit lần 2 (dispatch mới sau freeze V6).

## Final report
`research/wayfinder/evidence/sprint-v5-v6-master-20260824.md` với đủ
ENGINEERING_VERDICT / SCIENTIFIC_AUDIT_VERDICT / FAMILY_VERDICT /
GLOBAL_TRIAL_COUNT / S1_STATUS / LIVE_MONEY_STATUS=UNCHANGED_DISABLED
và master outcome thuộc 5 giá trị §39. Sau đó commit + push origin main
(+ branches nếu tạo).

---

## 6. BỆNH ĐỂ BIẾT (gotchas đã mất thời gian của V3/V4/V5)

1. **zsh không word-split** `$var` trong `set -- $spec` → dùng `IFS=: read`.
2. **YAML duplicate key**: key sau đè key trước (đã từng che mất lock stamp).
3. Timestamp ledger là **chuỗi ns digits** → parse bằng
   `pd.to_datetime(int(s), unit='ns', utc=True)` (evaluate_execution_ordering
   đã vá — đừng revert).
4. Funding settlement sàn có **jitter ms** → join phải snap ±120s (đã vá).
5. `PortfolioRunResult` là dataclass → `.to_dict()` trước `dict()`.
6. **KHÔNG BAO GIỜ** `rm -rf results/stage_a_v3` hay bất kỳ dir nào giữa
   chừng sprint — launch manifest/frozen bị xóa là mất provenance vĩnh viễn
   (phải rerun whole matrix).
7. Hai runner chạy đồng bộ cùng output dir → corrupt; `pkill -f matrix_runner`
   rồi mới chạy lại.
8. Engine cần `tick_size/step_size/min_notional` từ catalog instrument
   (`{SYM}-PERP.BINANCE`), min_notional ≥5.
9. `commission` trong Nautilus realized_pnl là net — decomposition null là
   hạn chế đã khai (P1 backlog), đừng "vá" bằng số bịa.
10. `pf_position_level` là dict lồng nhau — đọc `.profit_factor`.

## 7. IMMUTABLE ZONES (cấm ghi)

```
results/portfolio_v4/**          results/matrix/v4_xsect_mom/**
results/matrix/v3_execution_truth/**   results/stage_a_v3/**
results/matrix/v2_stage_a_final/**     results/stage_a_v2/**
results/registry/experiments.jsonl  ← append-only, chỉ thêm dòng
```

## 8. NGUỐN THAM CHIẾU NHANH

- Verdict V3/V4 chi tiết: `research/wayfinder/evidence/sprint-v3-v4-master.md`
- Challenge memo V3: `research/hypotheses/_analysis_v3/challenge_memo.md`
- Findings: `research/audits/v5/v3_v4_findings.json`
- Trial ledger: `research/audits/v5/global_trial_ledger.json` (N=99 unique)
- Transition V3: `results/matrix/v3_execution_truth/v3_transition.json` (19/19)
- NOTES.md §21 · PLAN.md §28–40

## 9. TRẠNG THÁI NGÂN GỮA NẾU HERMES CẦN RESUME GIỮA CHỪNG

Sau Bước 4.1–4.3, trạng thái đạt sẽ là: mọi P0 accounting/gates/measured-evidence
đã đóng (C01–C19, C21, C23–C26 đều có evidence), chỉ còn **C20** (reproduction
×4) và **C22** (A4 audit) quyết định transition. Nếu C20 match ×4 và A4 PASS →
`V6_AUTHORIZED`. Bất kỳ mismatch chưa giải thích → `BLOCKED_BY_V5` với exact
reason — đây là terminal outcome hợp lệ, không có waiver.
