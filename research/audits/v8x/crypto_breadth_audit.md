# V8X Crypto Breadth Audit (Agent A8) — CORRECTED

- Agent session: R-A8 remediation follow-up
- Branch/worktree: `orca/v8-a8-crypto-breadth` @ `/Users/hoangminhlong/my-quantitative-v8-wt/a8-crypto-breadth`
- Date: 2026-08-26
- Corrects: commit `4f1d704` (manifest schema 1.0.0), which violated the frozen selection contract
- Manifest: `data/v8x_manifests/crypto_universe_selection.json` (**schema_version 2.0.0**)
- Selection script: `scripts/v8x_crypto_universe_selection.py` (new; fully reproducible, offline, byte-deterministic)
- Tests: `tests/test_v8x_crypto_universe_selection.py` (15 passed)
- Performance-blind: **yes** — no `results/**`, PnL, or V7/V8 verdict artifacts accessed.
- **Verdict: `V8X_CRYPTO_TOP10_ELIGIBLE_PREWINDOW_BENCHMARK_EXCLUDED`** — 19/19 eligible altcoins, top-10 selected, BTC excluded as benchmark-only.

## 0. Violations of the prior version — all four fixed

| # | Prior flaw (commit 4f1d704) | Correction implemented |
|---|---|---|
| V1 | Ranked by median daily quote volume over the **scored** window `[2025-08-21, 2026-08-21)` — look-ahead into the evaluation period | Ranking uses **only the pre-window** `[2025-07-22T00:00Z, 2025-08-21T00:00Z)` (`ranking_rule=median_daily_quote_volume_pre_window_only`) |
| V2 | BTCUSDT was rank #1 **inside the traded top-10** | BTC (`BTCUSDT-PERP.BINANCE`, equivalent of `PERP.BINANCE.BTC-USDT`) is **benchmark measurement-only**: flagged `btc_benchmark_measurement_only=true`, excluded **before ranking**, never traded |
| V3 | Gap screen at **daily granularity** (`gap_day`); single-bar/partial-day holes explicitly tolerated — could not detect intra-day data loss | **Exact 15-minute grid census** over BOTH windows for every candidate: every expected slot checked, every gap given a machine-readable `cause`; any unexplained gap ⇒ fail |
| V4 | Funding gate = `funding_rows >= 1` | **Held-exposure completeness proof** per selected symbol across `[first-possible-exposure, scored end]`: sorted/deduped rows, every inter-settlement interval a legal Binance step ≤ 8 h + jitter, boundary coverage from the conservative first possible weekly entry to the scored-window end inclusive, and cross-symbol-corroborated explanation for any sub-8h regime step |

## 1. Frozen corrected selection contract (as implemented)

1. **Selection window (pre-window):** `[2025-07-22T00:00Z, 2025-08-21T00:00Z)` — strictly before the scored one-year window `[2025-08-21, 2026-08-21)`. Ranking ONLY within the pre-window.
2. **Ranking metric:** median daily quote volume (native 15m parquet `quote_volume`, USDT) computed only over distinct pre-window bar-days (Decimal-exact sums; even-count median = mean of central two).
3. **BTC excluded** from the ranked/traded top-10 entirely; retained in `candidates_evaluated` for transparency with `reason_if_rejected=["BTC_BENCHMARK_MEASUREMENT_ONLY_EXCLUDED_BEFORE_RANKING"]`.
4. **Tie-break:** primary metric desc, tie-break symbol asc — carried unchanged from the prior frozen artifact (`rank_tiebreak` in schema 1.0.0). No contradicting frozen prereg exists elsewhere (`data/v8x_manifests/` holds only this manifest).
5. **Listing-age gate:** onboard date ≤ scored-window start − 365 d = `2024-08-21T00:00Z` (age ≥ 365 d at first possible exposure). Consistent with prior artifact's ≥365d preference; stated here per contract since no separate frozen prereg file exists.
6. **Metadata sanity:** instrument present, venue BINANCE, quote USDT, contractType PERPETUAL, exchange status TRADING.
7. **Funding assumption (stated explicitly):** weekly Monday rebalance ⇒ a strategy could first hold any symbol at the earliest moment the scored window opens. Conservative **first-possible-exposure = pre-window end = scored-window start `2025-08-21T00:00Z`**; coverage required through scored-window end `2026-08-21T00:00Z` inclusive.

## 2. Exact 15-minute gap census (audit 5a)

Scope: every candidate × both windows. Expected slots = exact grid `[start, end)` step 900 s on slot-open times (local bars are stamped slot-close − 0.1 ms and mapped to their own slot).

| Quantity | Value |
|---|---:|
| Total expected 15m slots (20 symbols × both windows) | **758,400** |
| Gaps found | **57** |
| Unexplained gaps | **0** |

- Pre-window: **2880/2880 slots present for every candidate — zero gaps anywhere in the ranking window.**
- Scored window: single finding — **ETHUSDT, one run of 57 consecutive missing slots** `[2025-08-21T00:00Z → 14:15Z opens]`, i.e. bars with close times 00:15–14:30.
  - `cause = "local_capture_boundary_between_sessions"`, explained. Evidence (machine-readable in manifest): previous session's last bar open `2025-08-20T23:45:00Z`; next capture session's first bar open `2025-08-21T14:15:00Z`. The hole lies strictly BETWEEN two capture sessions' observed ranges — ETHUSDT is the only symbol whose catalog is fragmented across multiple capture files, and the earlier session simply ended before the scored window opened while the next session began 14½ hours later.
  - Classification rule (frozen, applied uniformly): a run strictly inside ONE capture session's observed range ⇒ `unexplained_hole_inside_single_capture_session` (fail); a run bounded by capture-session edges ⇒ explained boundary cause. No run in the entire dataset falls inside a session.
  - The prior daily-granularity screen structurally could not see this hole (2025-08-21 still had bars after 14:15 ⇒ counted as "covered"). This is exactly violation V3.
- Residual honesty note: offline we cannot prove what the exchange printed during the ETHUSDT hole; the cause attribution ("not captured locally between two sessions") is provenance evidence, which is the strongest available without network access, and it is deterministic/reproducible.

## 3. Listing age & metadata sanity (audits 5b, 5c)

- All 19 altcoins pass listing age ≥ 365 d at first possible exposure (oldest requirement: onboard ≤ 2024-08-21; latest onboarding among candidates ENAUSDT 2024-04-02 ≈ 506 d).
- All 20 candidates pass metadata sanity: BINANCE / USDT quote / PERPETUAL / status TRADING (from embedded exchange `info` blobs).

## 4. Funding held-exposure coverage (audit 5d)

Per selected symbol over `[2025-08-21T00:00Z, 2026-08-21T00:00Z]`:

- The other 9 of 10 selected symbols run a strict 8 h cadence: exactly **1095 settlements in-span** (= 365 d × 3), first settlement ≤ start + 8 h, last settlement = `2026-08-21T00:00Z` (+≤ ms jitter) — complete by construction.
- ENAUSDT runs a 240-min cadence (2189 in-span settlements) with a **single 480-min step at `2026-06-24T00:00Z`**; the identical step-pair appears at an identical millisecond timestamp in all four sub-8h-cadence candidates (ACE/BOME/ENA/ONG) ⇒ `cause="exchange_wide_funding_interval_step"` (exchange-wide interval-regime change, corroborated n=4). An isolated uncorroborated step would be classified unexplained and FAIL (unit-tested).
- Zero duplicate timestamps anywhere; all intervals legal Binance steps {1h, 2h, 4h, 8h} ± jitter.
- **Verdict: COMPLETE for all 10 selected symbols** (`funding_held_exposure_audit.complete=true`, machine-readable).

## 5. Eligibility counts (audit 6)

| Stage | Count |
|---|---:|
| Candidates evaluated (catalog bar dirs) | 20 |
| Excluded: BTC benchmark measurement-only | 1 |
| Altcoin pool | 19 |
| Eligible altcoins | **19 / 19** (0 rejected; rejection reasons recorded per candidate in manifest) |
| Selected top-10 | 10 |

## 6. Final chosen top-10 (ranked by PRE-WINDOW median daily quote volume, USDT)

| Rank | Symbol | Median daily qvol, pre-window (USDT) | Pre-w gaps | Scored gaps (unexplained) | Funding held-exposure |
|--:|---|---:|--:|--:|--|
| 1 | ETHUSDT | 24,602,646,500.99 | 0 | 57 (0) | complete |
| 2 | SOLUSDT | 4,183,797,973.53 | 0 | 0 | complete |
| 3 | XRPUSDT | 2,535,180,935.50 | 0 | 0 | complete |
| 4 | DOGEUSDT | 1,846,862,953.66 | 0 | 0 | complete |
| 5 | ENAUSDT | 1,159,139,794.95 | 0 | 0 | complete |
| 6 | SUIUSDT | 918,797,625.17 | 0 | 0 | complete |
| 7 | 1000PEPEUSDT | 857,082,216.07 | 0 | 0 | complete |
| 8 | ADAUSDT | 685,861,178.04 | 0 | 0 | complete |
| 9 | BNBUSDT | 685,005,825.08 | 0 | 0 | complete |
| 10 | LINKUSDT | 563,231,921.52 | 0 | 0 | complete |

**BTCUSDT explicitly EXCLUDED** (benchmark measurement-only; its pre-window median, 14,745,568,711.89 USDT, is recorded measurement-only and did not enter ranking).

Eligible but not selected (pre-window median, USDT): AVAX 383.85M, AAVE 250.66M, BCH 244.80M, NEAR 153.83M, WLD 145.47M, BOME 33.43M, ZEC 5.59M, ACE 3.72M, ONG 2.24M.

## 7. How the correction changes the universe (sanity, performance-blind)

Ranking on the pre-window alone legitimately reshuffles and re-composes the set vs the flawed version: e.g. ZECUSDT drops out entirely (its scored-window volume reflects a later regime: 599M scored vs 5.6M pre-window), ENAUSDT/LINKUSDT enter, and ADA/BNB swap order at ranks 8/9 (685.86M vs 685.01M — decided deterministically by the frozen tie-break-free metric ordering). No scored-window information influenced any decision; the selection is a pure function of pre-window catalog data plus audits.

## 8. Reproducibility

- `scripts/v8x_crypto_universe_selection.py` regenerates the manifest byte-for-byte offline from local data (fixed `generated_at_utc` constant; Decimal-exact arithmetic; sorted iteration everywhere). Verified: two consecutive runs produced identical sha256 `e73c703f5fb4dea7ff0c6c2c6c8c756b12218fa1960bf46c0ebb2509abb56376`.
- `tests/test_v8x_crypto_universe_selection.py`: 15 tests over slot mapping, census classification, funding completeness gates (incl. dropped-settlement detection and corroboration logic), metric/ranking determinism — all passing.
- Provenance anchors retained: SHA-256 of each `funding.json` and per-symbol bar-dir digests for all 20 candidates.
