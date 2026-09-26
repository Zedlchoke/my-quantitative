# PIT/DATA GATE SPEC — ERP-TRACKB cohort-1 (BTCUSDT spot–perp delta-neutral)

Lane: trackb-cohort1-pitdata (quant-auditor) · 2026-09-26 · base root main @ `e4e3b9159685b9da0bafeed6814f0a73c872cbcb` (measured HEAD).
OUTCOME-BLIND: no scored outcome/ledger/terminal-PnL file opened. Authority: TrackB plan §2/§4.2/§5 → umbrella §7/§8 → CHR3F §2/§4 (identity/data only) → `research/funding_pit.py` → LESSONS P-7/P-18/Q-6/Q-8.

## 1. Funding settlement PIT contract

- Observable fields (fapi `/fapi/v1/fundingRate`, program precedent V8/V11/V14/CHR3F): rows of `{symbol, fundingTime (epoch ms), fundingRate (string decimal)}`. **No `fundingCount` field is served** by this endpoint — settlement count is DERIVED by the census, never read (Q-8/P-18: verify every field name against served schema before filtering).
- Availability semantics: a settlement exists as an observable ONLY at its settle instant `fundingTime`. A decision at time T may legally consume exactly the set `{s : s.fundingTime ≤ T}`. This is the `rate_asof` law already coded in `research/funding_pit.py` (bisect_right on `fundingTime`; between two settlements the OLDER one binds; reasons `empty_bundle`/`insufficient_history`(<10)/`no_settlement_asof`; no forward-fill). Cashflow accrual: a position held across stamp T_s receives/pays the settlement AT T_s (`fundingTime == T_s` exact match on the 3-stamp grid).
- Settlement clock: 00:00/08:00/16:00 UTC for BTCUSDT, 24/7, no DST. The gate MEASURES modal interval per V8 method (`research/audits/v8p/funding_coverage_v8.json`: modal inter-settlement interval, minute-quantized stamps, anchored at first settlement) instead of assuming 3/day; interval changes (via fapi `/fapi/v1/fundingInfo` `fundingIntervalHours`, cross-checked) are enumerated as regime stamps, never silently absorbed.
- Predicted-vs-settled separation: fapi `/fapi/v1/premiumIndex` `lastFundingRate` for the NEXT interval is a PREDICTED quote — a different observable. Hard rules: separate channel name + provenance tag `funding_predicted` vs `funding_settled`; predicted values may NEVER enter a scored signal, feature, or cashflow; any code path reading premiumIndex must be structurally unable to write into the settled panel (separate loader, separate schema, grep-audited).
- Cross-check channel (P-7): vision monthly fundingRate zips are CROSS-CHECK ONLY (CHR3F §4 conflict policy: any disagreement → affected symbol-month EXCLUDED, `BLOCKED_DATA`, counts disclosed; no merging). Measured precedent of the conflict: `research/control/bear_opportunity_recon_2026-09/data_a2/funding_events.parquet` (vision schema `calc_time, funding_interval_hours, last_funding_rate`) starts 2019-09-10 — BEFORE the fapi floor 2020-07-18 (CHR3F §2); pre-floor vision rows must be dropped, not reconciled. Measured stamp residue `16:00:00.001` in that file mandates the minute-quantization check below.
- Proof fixture (P-18, M-class): **panel-truncation replay** — for every decision time T_i in the window, re-run the exact signal/feature/funding-accounting code on the panel truncated to `fundingTime ≤ T_i` and require BYTE-IDENTICAL output vs the full-panel run restricted to T_i. A same-function-same-panel parity self-test is NOT evidence (blind to growing-panel divergence). Truncation delta on ANY replay = FAIL.

## 2. Spot–perp clock alignment contract

- Basis is derived, not a source (TrackB §2): `basis_t = perp_close_t − spot_close_t` from two bar series that are SAME venue (Binance), SAME interval, SAME bucket grid, SAME stamping convention.
- MEASURED hazard — stamping: the staged catalog bars (`.worktrees/crypto-historical-replication-3f-v1/integration/catalog/data/binance_bar/BTCUSDT-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL/`, 2 parquets, 35,039 rows, 2025-08-20T02:45Z..2026-08-20T02:29:59.999Z, contiguous — all consecutive diffs exactly 15m, measured) are **bar-CLOSE-stamped** (`…:14:59.999` style, nautilus fixed-precision byte-encoded prices). Vision/fapi klines are bar-OPEN-stamped. Joining the two without normalizing shifts one leg 15 minutes. Gate: normalize both legs to ONE declared convention (recommend bucket = bar-open key, value = close of that bar) + fixture that proves the join on a known stamp.
- MEASURED hazard — price convention: catalog perp bars are `LAST` (last-trade). Funding settles against premium index (mark vs index). So last-vs-last basis is a tradable proxy, NOT the funding premium; they are different observables and must be named differently. If a mark/index basis is needed it must come from fapi `markPriceKlines`/`indexPriceKlines` (V14 precedent) as separate staged channels with their own census.
- Drift: spot and perp last-trade tapes do not co-time inside a bucket; bar-close basis embeds intra-bucket leg skew. No tick-level co-timing exists in staged data ⇒ mandatory seam disclosure: (a) stamp convention of each leg, (b) LAST-vs-MARK-vs-INDEX basis identity, (c) intra-bucket drift unmeasured (declared band, never zero-claimed), (d) missing-bar policy: a bucket is basis-eligible ONLY if BOTH legs have a real bar — no interpolation, no carry-forward (missing ⇒ `NOT_RUN` count).
- Note: the dispatch's `crypto_perpetual/BTCUSDT-PERP.BINANCE/` parquets are instrument-DEFINITION snapshots (1 row each; `onboardDate` 2019-09-25T08:00Z measured — corroboration only per CHR3F), NOT bars; the bars live under `binance_bar/…-15-MINUTE-LAST-EXTERNAL/`. Coverage verdicts name the exact channel (P-7).

## 3. Coverage/census gates (all measured BEFORE any PnL, Q-8)

- Funding census: expected = measured-modal-interval × window (near-3/day for BTCUSDT, but measured); outputs per V8 precedent: `rows_total, first/last_settlement_utc, coverage_ratio, missing_settlements_estimate` + ENUMERATED list of missing stamps (to the minute), head/tail uncovered hours. Any missing stamp ⇒ fold-level `NOT_RUN_DATA` counts; no interpolation.
- Bar census: spot 15m klines full grid from staged start (spot NOT staged today — measured: zero BTCUSDT spot bars anywhere in repo/catalog ⇒ staging is a GO-1 precondition); perp same-grid; per-month-file sha256 pinned into a committed staged manifest (CHR3F §4 law); duplicates (same stamp twice), out-of-order rows, zero-volume/halt bars FLAGGED not dropped.
- Calendar law: crypto 24/7 UTC, DST-free by construction — assert every settlement stamp ≡ {00,08,16}:00:00 (minute-quantized) and every bar stamp on the exact 15m UTC grid; the `.001` residue class above is the standing fixture.
- Minimum window (Q-6): feasibility ceiling measured on the RECENT window (trailing ~90d funding/basis distribution), never the full-archive average; window ancestry law (TrackB §4.2): all dev evidence `ANCESTRY_EXPOSED_DEV`, 2026-08-22..freeze = `SEAM_CONSISTENCY_ONLY`, sealed OOS = post-freeze accumulation only.
- Survivorship/canary: cross-sectional survivorship NOT APPLICABLE (single symbol BTCUSDT — no universe selection, no dead-name panel to fake). P-7 channel canary IS APPLICABLE as empty-file/duplicate-identity probes per channel: fapi REST, vision funding zip, vision spot klines, vision bookTicker/aggTrades, catalog parquet are five channels; a PASS on one licenses nothing on another.

## 4. License posture (umbrella §7 state machine)

- All Binance-public channels start `DOCUMENTED_CANDIDATE` → `AUTHORIZED_INTERNAL_RESEARCH` only via this data gate. Gate must verify per source: retrieval URL+method+date recorded, every downloaded byte sha256-pinned in a committed manifest, machine-local gitignored storage, no credentials/no order APIs/no paid source, no redistribution, fail-closed conflict policy accepted. Sources and dispositions: fapi fundingRate (PRIMARY, settled), fapi markPriceKlines/indexPriceKlines (mark/index channels), vision spot BTCUSDT klines, vision fundingRate zips (cross-check only), vision bookTicker/aggTrades (fill-hour spread census). `free ≠ authorized` — posture inherited from ancestor crypto cycles (P-25 lineage), one verdict per channel (P-7).

## 5. BLOCKED list (fail-closed today; unblock conditions)

1. Liquidation tape (forceOrder archive) — BLOCKED; unblocks when a data-authority cycle stages forceOrder/buyLiquidation history. Until then `LIQUIDATION_MODEL_DECLARED` (maintenance tiers venue-published = DECLARED model).
2. Borrow rates / spot-margin terms (inverse short-spot leg) — BLOCKED per TrackB law (e); unblocks via owner-authorized margin/borrow data source + §5.5 amendment. Cash-and-carry (long spot + short perp, unlevered) remains the only scoreable form.
3. Queue position / maker fills — unmeasurable from staged top-of-book; unblocks only with depth+fill replay evidence; until then maker-only assumptions are FORBIDDEN in the cost book (§5.5).
4. Second-venue funding (OKX/Bybit) — BLOCKED-unauthorized; unblocks via owner unblock of source + license (replication limb iii); ceiling stays `CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION (SINGLE_VENUE)`.
5. Slippage replay-vs-fill — no own fills exist (paper tier): stays DECLARED+stress unless/until measured fills appear.

## 6. Data-gate checklist for child cycle at GO-1 (PASS / FAIL / BLOCKED each, with evidence path)

1. Fapi funding staged ≥ window, rows `{symbol,fundingTime,fundingRate}` verified vs served schema → `staging/funding_manifest.json` (sha256 per page-bundle). FAIL if any field name assumed unverified.
2. Funding census: coverage_ratio==1.0 on scored folds, missing stamps enumerated, modal interval measured, interval-change stamps recorded → `staging/funding_census.json` (V8 template). Any unenumerated gap = FAIL.
3. Vision funding zip cross-check: per-month sha256 pins; mismatch months EXCLUDED with counts → `staging/funding_crosscheck.json`. FAIL if merged silently.
4. Predicted-funding quarantine: grep/AST proof no premiumIndex-derived value reaches settled panel; `funding_predicted` tag isolated → `staging/pit_predicted_separation.json`. FAIL if any shared loader.
5. Truncation replay (P-18): N decision times, byte-identical truncated replays, delta count == 0 → `staging/pit_truncation_proof.json` + replay hashes.
6. Spot 15m klines staged (vision monthly), full-grid census, sha pins → `staging/spot_klines_census.json`. BLOCKED until staged (today: absent, measured).
7. Perp bars staged for window (vision monthly klines and/or catalog parquet channel named explicitly), full-grid census, stamp-convention normalized → `staging/perp_klines_census.json`. Note catalog covers only 2025-08-20..2026-08-20 (measured) — earlier windows need vision zips.
8. Alignment fixture: one-bucket join both legs, declared convention, known-stamp proof, LAST-vs-MARK-vs-INDEX identity declared → `staging/alignment_fixture.json`.
9. Calendar/DST fixture: all stamps on UTC grids; `.001`-residue detector zero-hits → `staging/calendar_check.json`.
10. Duplicate/out-of-order scan all channels: 0 duplicates unflagged, order sorted-or-flagged → in census files above.
11. Q-6 nearest-window feasibility: trailing-90d funding distribution + basis + anchor taker RT recomputed, not inherited → `staging/recent_window_feasibility.json`.
12. License state per source → `staging/license_posture.json` (DOCUMENTED_CANDIDATE→AUTHORIZED_INTERNAL_RESEARCH rows with evidence).
13. BLOCKED register (§5) written verbatim into child plan; maker/borrow/venue-2 unattainable paths absent from cost book → `staging/blocked_register.json`.
14. PIT loader contract: `funding_pit.py` semantics (or stricter reimplementation) with fail-closed reasons; reproducer rewrites settlement accounting from raw bytes (TrackB §6) — engine import shared = FAIL.

Gate verdict rule: 1–5, 8–14 PASS + 6–7 PASS-or-explicitly-BLOCKED-with-owner-decision ⇒ data gate OPEN; any silent gap ⇒ `BLOCKED_DATA_OR_SELECTION`.

## 7. Auditor verdict

Data gate is FEASIBLE as specified: funding PIT contract is already codified (`funding_pit.py` + V8 census precedent + CHR3F conflict policy) and the two blocking unknowns (spot staging, pre-window perp staging) are bounded staging work, not research risk. Top PIT risks, ranked: (1) settlement-adjacent timing errors — consuming predicted funding, off-by-one settlement at boundary stamps, or forward-fill across gaps; (2) alignment — close-stamp catalog bars vs open-stamp vision klines (measured 15-min shift) and LAST vs mark/index conflation; (3) coverage — silent merges across the measured pre-2020-07-18 fapi/vision divergence and unenumerated missing stamps. All three have concrete fixtures above; none requires new data authority.
