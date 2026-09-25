# PLAN ETHUSDT-OPEN-SEARCH-V2 — tranche 2 of the owner-directed ETHUSDT strategy-search campaign

> Standing owner directive 2026-09-24 (verbatim): "mở cycle tìm kiếm strategy
> cho ETHUSDT cho tới khi tìm được strategy kiếm tiền có bằng chứng kinh tế
> rõ ràng"; continuation clause confirmed 2026-09-24 ("Hãy trong loop cho tới
> khi kiếm được strategy đủ chỉ tiêu. Khi bạn dừng lại là lúc đã có kết quả
> và chờ Go"). V1 terminal 2026-09-25 `NO_INCREMENTAL_VALUE` (8/8 cells,
> E1/E2 families dead) authorizes this successor tranche. The directive is
> the campaign opener, NOT a scoring GO (P-8); this tranche needs its own
> fresh typed GO at its own STOP-1. Class: POSTHOC S0 DISCOVERY (unchanged).
> S1 `SEALED_UNTOUCHED`. No paper/live/orders.

## 0. Cycle identity

```text
cycle_id     ETHUSDT-OPEN-SEARCH-V2
asset        crypto (single asset: ETHUSDT USDT-M perpetual)
class        POSTHOC S0 DISCOVERY (campaign tranche 2)
question     Do ETHUSDT books driven by NEW cross-asset observables —
             BTC's realized-VOLATILITY state (lane V2-A) or the alt-breadth
             confirmation count over {SOL,BNB,XRP,ADA} (lane V2-B) — beat
             the frozen reference wall after measured costs across
             2020-01..2026-08? V1's dead space (BTC-PRICE-state gates,
             ratio gates, and all program dead classes) is NOT re-entered.
budget       2 lanes × 4 configs = 8 scored cells MAX
s1           SEALED_UNTOUCHED
orders       NONE
go_phrase    GO ETHUSDT OPEN SEARCH V2 SCORED EXECUTION
engine       inherited byte-frozen from V1 terminal 8196e3ea
             (eos1_engine.py copied into this cycle's namespace; only NEW
             signal constructors + ARMS table added; cost kernel, folds,
             PIT laws, funding law, force-flat law identical)
forbidden    everything in V1's forbidden list, PLUS the now-dead V1
             families: EOS1-E1 (BTC own-PRICE state -> ETH gates, all
             transforms incl. drawdown states) and EOS1-E2 (relative-
             strength RATIO gates in all pair variants incl. SOLETH);
             rescue of V1 cells under any redefined wall; parameter
             ladders chosen by scanning V1 fold PnL beyond the round
             conventions below; gate relaxation after PnL; mid-run stop
             on ugly numbers; git add -A.
```

## 1. Ancestry and open-space position (pre-PnL, A7 adjudicates)

```text
DEAD by program record (never re-test): all V1-forbidden classes; V1
families EOS1-E1 (BTC-price-state gates) and EOS1-E2 (ratio gates,
symbol swaps fenced); vol-MANAGED sizing (ES1-A — sizing by the traded
asset's own vol); DVOL-shock (TRV1); XSECT relative-rank portfolios
(V9 TSTREND etc.).
OPEN (new observable × same vehicle, never measured in-program):
  V2-A  BTC realized-vol STATE as ETH exposure driver. Distinct from
        dead ES1-A (which SIZED BTC books by BTC's own vol and died on
        economics, not information — its G6-A showed the vol series
        carries information); here BTC rvol is a BINARY gate input and
        the vehicle is ETHUSDT. Mechanism: BTC rvol spikes (2020-03,
        2021-05, 2022) lead ETH drawdowns; quiet-BTC regimes are when
        ETH earns its beta. Falsifier: block-shuffled rvol state must
        not out-earn (V1-E2's fate is the cautionary precedent).
  V2-B  ALT-BREADTH confirmation: count of {SOL,BNB,XRP,ADA} above own
        SMA(H4) drives ETH long/flat. Distinct from dead XSECT-TSTREND
        (relative-RANK long-short portfolios across 20 names): breadth
        is an absolute-threshold COUNT gating ONE asset, no second leg
        traded, no cross-sectional ranks. Mechanism: broad alt uptrend
        confirms risk-on for ETH; breadth collapse flags rotation-out.
        SOL coverage starts 2020-09 — PIT eligibility law: breadth over
        AVAILABLE names with a minimum-count floor (>=3 of the listed 4
        from 2020-09; before that the lane is NOT_RUN_THIN and disclosed;
        B-configs declare their own eligible-window start).
Config ladders (ROUND, frozen NOW):
  V2-A1  BTC rvol(180 H4 closes = 30d) < trailing 1y median        -> long
  V2-A2  BTC rvol(180)  < trailing 1y 40th percentile              -> long
  V2-A3  BTC rvol(540 = 90d) < trailing 1y median                  -> long
  V2-A4  A1 AND A3 (double-notch)
  V2-B1  breadth_200(SOL,BNB,XRP,ADA) >= 3/4                       -> long
  V2-B2  breadth_200 >= 2/4                                        -> long
  V2-B3  breadth_200 == 4/4                                        -> long
  V2-B4  breadth_600 (SMA600 basis) >= 3/4                         -> long
Controls per cell: block-shuffle(30 H4 bars) of the gate state
(seed = sha256("eosv2|<arm>|shuffle")); sign-inversion. Identical law
to V1.
```

## 2. Data authority (P1)

Corpus law identical to V1 §2 (keyless Vision monthly zips, GET-only,
pacing ≥2 s, 404 retry ladder, missing-month re-verify after 120 s quiet,
sha256-pinned manifest). Series:

- `klines:ETHUSDT:1h`, `klines:BTCUSDT:1h` um perp 2020-01..2026-08 —
  RESTAGED into this cycle's `data_local/` (self-contained provenance),
  cross-checked byte-identical against the V1 staged manifest (any
  mismatch = BLOCKED_DATA, fail-closed).
- `fundingRate:ETHUSDT` um 2020-01..2026-08 — restaged, V1 cross-check.
- NEW `klines:{SOLUSDT,BNBUSDT,XRPUSDT,ADAUSDT}:1h` um perp from their
  measured Vision floors (expected ≈2020-01 BNB/XRP/ADA; SOL ≈2020-09) —
  census records floors; breadth PIT eligibility per §1.
- Warmup: SMA600 needs ≈100 d pre-2020-01 of each alt where available;
  months before 2020-01 that exist are WARMUP-ONLY (never scored).
- Costs/PIT/folds/tiers/force-flat/one-bar-lag: byte-identical laws to
  V1 (engine inherited from 8196e3ea).

## 3. Windows and folds

Identical to V1 §3 (F1 2020-01..2021-05, F2 2021-05..2023-01,
F3 2023-01..2025-01, F4 2025-01..2026-09-01, force-flat, warmup
truncated, floors ≥100 scored bars per fold per arm).

## 4. References (inside the scored run; NOT cells)

Identical to V1 §4: BASE_CASH, BASE_ALWAYS_ON_LONG, BASE_TREND_LF,
REF_SHORT_ALWAYS — recomputed on this cycle's restaged corpus (expected
to reproduce V1's numbers byte-close; material divergence = STOP +
investigate before PnL).

## 5. Gates (per scored cell; ALL must PASS; identical semantics to V1)

G1 net>0 @1.0×; G2 net>0 @1.5×; G3 net @1.0× beats ALL references;
G4 ≥3/4 folds net>0 OR best-fold-removed net>0; G5 max positive-fold
share ≤0.50; G6 both controls must NOT out-earn @1.0×; G7 fills@1.5×
≤10,000 AND execution cost/round-trip (2 ticks in bps, ES1 semantics)
≤10 bps; G8 reproduction byte-match; G9 A7 terminal clean; G10 vs
BASE_TREND_LF combined-increase + no positive→negative fold flips;
G11 ancestry disclosure (spearman vs TREND_LF weights + vs V1 dead-arm
weight series where computable — disclosure-only).

## 6. Cycle phases

P0 register + worktree + bootstrap (this commit) → P1 restage + alt
staging + census + V1 cross-check → P2 feasibility (flips, fold
populations, warmup/PIT-eligibility table, G6 null validity, G11) →
P3 freeze + fixtures (V1 suite + NEW rvol/breadth goldens) + sanitized
dry-run + A7 prelaunch fresh-context (lane novelty adjudication has
VETO power) → STOP-1 owner GO
(`GO ETHUSDT OPEN SEARCH V2 SCORED EXECUTION`) → P4 scored run (no
mid-run stop) → P5 repro twin + A7 terminal → P6 two-half close.

## 7. Terminal verdicts (exactly one)

```text
ETHUSDT_OPEN_SEARCH_V2_POSTHOC_DISCOVERY_CANDIDATE_FOR_PROSPECTIVE_VALIDATION
ETHUSDT_OPEN_SEARCH_V2_NO_INCREMENTAL_VALUE
ETHUSDT_OPEN_SEARCH_V2_NO_ELIGIBLE_PROPOSAL   (A7 prelaunch veto of both lanes)
ETHUSDT_OPEN_SEARCH_V2_BLOCKED_DATA_OR_SELECTION
TECHABORT
```

## 8. Campaign law (unchanged from V1 §9, extended)

Candidate ⇒ owner decides prospective sleeve (preregistered promote/
kill/time-stop + short-beta control + pre-fill cost-identity reconcile).
NO candidate ⇒ standing directive authorizes tranche V3 ONLY with new
lawful tuples; if A7 vetoes both lanes here, the posthoc open space on
keyless data is EXHAUSTED and the campaign parks at an owner-redirection
decision (asset change / new data authority / wall-redesign successor —
each an owner decision per §34.5, not agent-derivable).

## 9. Boundaries

Worktree `.worktrees/ethusdt-open-search-v2/integration`, branch
`orca/ethusdt-open-search-v2-integration`, base = main HEAD at
registration. V1's worktree/evidence byte-untouched (read-only
cross-check of its manifest only). Registry writes via researchctl only.
Raw bytes gitignored; manifests/digests/fixtures commit. No push/merge/
orders/credentials/S1.

## 10. Amendments log

None yet. Amendments pre-outcome only; may not touch folds, gates,
ladders or the verdict ceiling.
