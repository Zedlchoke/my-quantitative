# V10-N1 E-S0 — screened-window hypothesis generation (findings)

> ## HYPOTHESIS_GENERATING_S0 — NO STATISTICAL CREDIT IS CLAIMED
>
> Every number below was computed **after looking at the same S0 crypto bar
> window that every prior V1–V9 evaluation already inspected**
> (`S0_ALREADY_INSPECTED`). Nothing here is out-of-sample evidence. Survival
> rates, hit rates, profit factors and per-trade expectancies in this document
> describe the **screened window only**; they are conditioning observations used
> to generate (or retire) intuition for other blind agents' pipelines, never
> evidence of edge. Any V10 scored trial started because of this document is
> contaminated by construction and must be labelled accordingly downstream.
>
> Role: E-S0 (empirical screen agent), wave N1. Distinct from A8/A9, which
> reason from priors only. This role exists to ground their reasoning with real
> numbers that armchair analysis cannot produce.

## 1. Provenance

| Item | Value |
|---|---|
| Worktree | `/Users/hoangminhlong/my-quantitative-v10-wt/n-e0-research` |
| Branch / HEAD | `orca/v10-n-e0` @ `aec9324c97771c26e840c1c10b73dd56737f8f96` (clean at start) |
| Mandate | PLAN.md §7 + §3 S0-screening sanction + `research/control/v10_discovery_run/v10_contract.json` (`discovery_mode_amendment`) |
| Data read | `catalog/data/binance_bar/{BTCUSDT,ETHUSDT}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL/*.parquet` and `catalog/data/crypto_perpetual/*/` instrument definitions, read-only |
| Loader | project `data/catalog.py` decoding path replicated at raw fixed-point level after the catalog query path raised a schema-merge error; decoded values verified against OHLC invariants (`high ≥ open,close ≥ low` on all four files) |
| Tooling | `/Users/hoangminhlong/my-quantitative/.venv/bin/python`, pandas/pyarrow; all scripts under `.scratch_e0/` (deleted before commit) |
| Data NOT present locally | funding-rate/clock companions (`derivatives_data/`, `funding_data/scan_2026`); all other five S0 symbols (SOL/BNB/XRP/DOGE/LINK/ADA); any OI or basis series |

### Window actually screened

Declared S0 window is `2025-08-21T00:00Z → 2026-08-21T00:00:00Z`
(`research/data_audit.py` L60-L63). Local bars cover
`2025-08-21T00:14:59.999Z → 2026-08-20T02:29:59.999Z` = **34,954 completed 15m
bars per symbol**, zero duplicate stamps, zero irregular cadence. The final
~21.7 h of the declared window (2026-08-20 03:00 → 2026-08-21 00:00) was not
available in this worktree.

Symbol coverage inside S0 here: **BTCUSDT-PERP** and **ETHUSDT-PERP only**
(n=2). BTC is not one of the seven frozen S0 symbols, so it is used strictly as
a directional cross-check leg; it can never back a proposal scoped to the S0
seven-symbol universe. One additional non-S0 slice existed in the worktree
(ETH prior year 2024-08-20→2025-08-20; BTC stub 2026-07-20→2026-08-19) and was
**not used in any decision recorded here** beyond loading/integrity checks.

Clock convention used everywhere: bar label `ts` = `ts_init` = the bar's **close
timestamp** (bar spans `[ts−15m, ts)`); features use only bars ≤ `ts`; a fill is
modelled at the **next event** (`open[t+1]`); horizon-H forward return =
`close[t+H] / open[t+1] − 1`.

Regime context (measured, for reading every number below): the S0 window fell in
every fold — cumulative 15m log-return ≈ −21.5 %, −10.6 %, −6.5 % (BTC) and
−20.0 %, −17.8 %, +1.9 % (ETH) across chronological thirds, with price ranges
BTC 58,145→125,993 and ETH 1,519→4,998 USDT then back to ~69,500 / ~2,258 by
window end. Unconditional mean forward drift over the window was small and
negative: fwd4 −0.54 bp, fwd16 −1.93 bp (BTC); −0.59 bp, −2.15 bp (ETH).

## 2. Screens performed (complete ledger)

Legend: "folds" = three equal chronological thirds of the S0 slice
(F0 2025-08→2025-12, F1 2025-12→2026-04, F2 2026-04→2026-08). All screens used
only the two available symbols unless stated. Outcome lines are deliberately
blunt; several are dead ends kept for denominator honesty.

| # | Screen | Exact slice | Symbols/n | Outcome |
|---|---|---|---|---|
| 01 | Parquet schema + content inspection of `catalog/data/**` (7 files) | n/a | 7 files | `crypto_perpetual/*` are instrument definitions only (no funding/OI companion anywhere in worktree) |
| 02 | Raw fixed-point decode + OHLC invariant check | full files | 4 bar files | PASS; scale 1e9 confirmed against price magnitudes |
| 03 | Duplicate-stamp audit per file | full files | 4 bar files | 0 duplicates |
| 04 | Bar cadence/gap audit inside declared S0 | 2025-08-21 → 2026-08-21 | 2 × 34,954 rows | 0 irregular steps; tail 21.7 h missing |
| 05 | Single-bar aggressor imbalance `imb=2·tb_vol/vol−1`, deciles vs fwd4/16/48 | S0 slice | 2 × 34,85x | DEAD END — BTC t = +1.51/+0.48/−0.67, ETH fold-ICs flip sign (+0.0162/−0.0150/+0.0011) |
| 06 | Rolling signed flow `cflow8` (40-min) vs fwd4/16/48 | S0 slice | 2 × 34,9xx | DEAD END — strongest cell ETH fwd4 t=+4.06 but fold ICs (+0.0089/−0.0393/−0.0331) disagree with sign |
| 07 | Rolling signed flow `cflow32` vs fwd4/16/48 | S0 slice | 2 × 34,9xx | MIXED/inconsistent — BTC fwd16 LS +8.9 bp t=+2.1 but fold ICs +0.018/−0.021/−0.041 flip |
| 08 | Rolling signed flow `cflow96` vs fwd4/16/48 | S0 slice | 2 × 34,8xx | REJECTED as momentum proxy — fwd48 slope t=+4.60 (BTC)/+7.74 (ETH) with huge decile spread (ETH top-bottom +51.6 bp) but this is trend beta; adjacent to VOLSHOCK/TSTREND → rescue risk, dropped |
| 09 | Hour-of-day drift map (24 cells) vs fwd4 | S0 slice | 2 symbols (48 cell means) | DEAD END for anchoring — best hours 20–21 UTC positive both symbols but per-fold means flip sign across folds |
| 10 | Funding-clock neighbourhood (hours 23/00/01 UTC) vs rest | S0 slice | 2 comparisons | NULL — BTC −0.59 vs −0.53 bp fwd4; ETH −1.05 vs −0.52 bp; no material funding-window effect measurable without funding data anyway |
| 11 | Day-of-week drift vs fwd16 | S0 slice | 14 cell means | NOT PURSUED — Thursday strongly negative on both (BTC −12.80, ETH −22.18 bp) but likely concentrated in crash days; economically weak, unexamined clustering |
| 12 | Realised-vol octiles (rv over 24×15m) vs fwd4/16/48 | S0 slice | 8 octiles × 3 horizons × 2 sym | STRONG unconditional pattern but regime-confounded — lowest octile best bucket both symbols (BTC +8.87 bp, ETH +17.91 bp fwd48), elevated vol negative (ETH −30.47 bp) |
| 13 | Vol-quartile × fold matrix | S0 thirds | 4 q × 3 folds × 2 sym | Directionally stable — low-q positive in 3/3 folds both symbols; q0−q3 spread [+36.6,+6.1,+9.8] (BTC), [+14.0,+15.5,+70.2] (ETH) — but see #14 |
| 14 | Quiet-regime carry simulated as tradable state machine (rank<q_in, exit rank≥q_out, hold cap), walk-forward ranks over trailing 672 bars | S0 slice | 2 configs × 2 sym | **KILLED BY COSTS** — BTC net@10 bp rt: −16.43 / −23.33 bp per trade; ETH −8.57 / −11.81 bp. The pretty octile table does not survive entry-after-detection + exit-on-vol-rise + fees |
| 15 | Absorption legs at fixed thresholds (count-pct 0.85 & range-pct 0.35 ⇒ long-ish leg; count-pct 0.30 & range-pct 0.80 ⇒ short-ish leg) | S0 slice | 2 legs × 3 folds × 2 sym | WEAK — BTC spread works in F1/F2 only; ETH direction inconsistent (F0 leg signs reversed) |
| 16 | Ticket-size anomaly (quote-volume-per-trade ÷ rolling median), deciles vs fwd16/48 | S0 slice | 10 deciles × 2 horizons × 2 sym | DEAD END — extreme-decile signs disagree across symbols (BTC bottom decile −7.67 bp, ETH bottom decile +12.78 bp fwd48) |
| 17 | Thin-participation expansion, unconditioned (count rank<0.30 & range rank>0.85) | S0 slice, wf-ranks trailing 672 bars | BTC n=727, ETH n=1,203 events | SURVIVES DIRECTIONALLY — mean fwd16 −27.54 bp (BTC: per-fold +1.0/−54.44/−28.88), −12.52 bp (ETH: +0.23/−7.13/−22.81) |
| 18 | Same events conditioned on bar direction (close>open = markup leg) | S0 slice | 2 dirs × 3 folds × 2 sym | MECHANISM CANDIDATE — markup leg negative in 3/3 folds on BOTH symbols |
| 19 | Anchor gate primary `cnt_rank<0.30 & rng_rank>0.85 & close>open` | S0 slice | BTC 382 events incl. overlap; ETH 605 | POSITIVE-directional, per-fold gross −38.12 bp pooled (BTC) / −21.02 bp (ETH); hit rate 53–72 % (short side) |
| 20 | Neighbour gate `cnt_rank<0.40 & rng_rank>0.75 & close>open` | S0 slice | BTC 1,027 / ETH 566 overlapping events | Same sign, diluted — pooled gross −20.03 bp (BTC) / −12.92 bp (ETH) |
| 21 | Control A: fat-count + narrow-range (predicted flat) | S0 slice | BTC 1,239 / ETH 1,767 bars | Consistent with mechanism specificity — BTC +1.86 bp, ETH −6.45 bp, folds mixed/small |
| 22 | Validity check: participation-CONFIRMED wide-range up-thrust (cnt rank>0.70 & rng rank>0.85) | S0 slice | BTC 1,641 / ETH 1,272 | Specificity evidence — BTC −1.66 bp (≈flat) vs thin-participation −38 bp; ETH +12.00 bp with 3/3 positive folds ⇒ effect is not "wide range up" generically |
| 23 | Hour-of-day-normalised activity z (top decile) | S0 slice | 2 | NO EDGE — BTC −0.73 bp, ETH +1.94 bp fwd16, folds opposite-signed |
| 24 | Lead-lag corr(BTC ret_t , ETH ret_{t+lag}), lags ±8 | aligned S0 bars, n=34,930 | 17 lag comparisons | DEAD END — contemporaneous 0.536 dominates; lag ±1 only 0.050/0.0399, lag −2 0.0209; nothing actionable, plus BTC is outside the frozen S0 seven |
| 25 | Robustness probe: alternative markup definition (close-in-range > 0.60) | S0 slice | 2 | Same sign/magnitude (BTC +34.58 bp net, ETH +10.48 bp net per trade incl. overlap) but BTC F0 still negative |
| 26 | Horizon robustness probes H8 / H32 (pre-declared alongside H16 anchor) | S0 slice | 2 horizons × 2 sym | H8 weak (BTC +8.86 bp, ETH +4.97 bp net, overlap-weighted), H32 stronger but BTC F0 −28.32 bp ⇒ H16 was already a sane midpoint, no tuning done afterwards |
| 27 | **Non-overlapping re-measurement** (one position per symbol, skip while in trade, H16) | S0 slice | BTC 157 trades, ETH 197 | **EDGE EVAPORATES** — BTC +5.27 bp/trade net, crude PF 1.16, win 47.8 %, F0 negative (50 trades); ETH −3.65 bp/trade, PF 0.92, F0/F1 negative. See §4 |
| 28 | Unconditional baselines for context (all-bars fwd4/fwd16; quiet-state subset) | S0 slice | 2 × 2 subsets | fwd16 baseline −1.93 bp (BTC) / −2.15 bp (ETH); quiet-state baseline −4.03 / −3.08 bp |

### Honest multiple-testing note

Roughly **279 conditional comparisons** were made against a single inspected
year (counts per row above sum to ~279 cell-tests; several tests appear twice
because they re-use the same bars under a different conditioning variable).
Under that many looks on one window, isolated |t|-statistics near 2 carry
essentially no information. Only results reported as surviving in **both
symbols AND all three folds** (#13, #19) clear even a *heuristic* screening
bar — and #19's survival is destroyed by the non-overlap measurement (#27),
which is the measurement that matches how a fixed-size book would actually
trade.

## 3. What survived, and why it still does not become a proposal

Survivor: **thin-participation markup fade** — a wide-range up-thrust printed
with trade count in the bottom tail of its own trailing distribution precedes
consistent negative drift.

Mechanism reading: an upward thrust without two-sided participation is illiquid
markup. There are no resting resting-limit sellers to absorb and no fresh buyers
to confirm; the marginal buyer paid for depth that did not exist. Fade the
markup, take its round trip. The control legs support the reading (#21 flat,
#22 shows the effect needs *thin* participation, not merely a wide-range bar),
and the asymmetry is sensible: the down-side twin (thin-participation markdown)
is far more frequent but should *not* be faded, because gravity — downhill moves
in low liquidity do not need participants.

Evidence for it: negative in 3/3 folds on both symbols, on the direction-of-bar
conditioning (i.e., 6/6 symbol-fold agreement), magnitude an order larger than
unconditional drift (−38 bp vs −2 bp baseline over 16 bars when overlaps count).

Evidence against it, measured:

* Non-overlap sampling (#27): BTC +5.27 bp/trade net (crude PF 1.16,
  157 trades) and ETH −3.65 bp/trade (crude PF 0.92, 197 trades). At the
  preregistered cost model (5 bp taker each way) plus a further 1.5× fee stress,
  BTC goes to roughly breakeven-or-below and ETH stays negative.
* Per-event equal-weight path troughs of −1,763 bp (BTC) / −4,855 bp (ETH)
  reflect extreme signal clustering (up to 33 signals/day on BTC event days);
  cluster members double-count the same decline windows and inflate the
  overlapped statistic.
* Median per-trade outcome is near zero or negative (BTC +9.17 bp incl.
  overlap; ETH −1.89 bp) while the standard deviation is ~140 bp on both
  symbols: the expectancy lives in the right tail of cascade days, i.e., it
  depends on being able to hold/add through exactly the episodes where
  execution degrades.

## 4. Terminal statement of this role

**No mechanism proposed.** The single pattern that survived the full
screening funnel fails the constraints that Stage A will apply later
(expectancy after costs must stay positive under 1.5× fee and adverse-tick
stress, PF ≥ 1.10, MDD ≤ 10 %, neighbour must support anchor). Applying those
constraints now, on the same inspected window where the pattern was found, it
fails: PF estimate 1.16 on one leg and 0.92 on the other.

Consequences requested of the integration owner:

1. **E-S0 consumes zero V10 budget**: no scored slot, no family module, no
   prelaunch gate dependency.
2. The veto applies to *this* mechanism as specified; it is not permission to
   retune thresholds, holding horizon, ranking window (672), the cost model or
   the concurrency rule to make it pass. That would be exactly the rescue
   behaviour the contract forbids.
3. Items deliberately left out of scope rather than stretched into proposals:
   funding-aware variants (untestable here — no funding data in this worktree);
   concurrency-intensity sizing (would be a different, leverage-bearing
   mechanism and is *not* validated by anything in §2); BTC-anchored lead-lag
   (outside the frozen S0 seven-symbol universe and empirically empty at usable
   lags, #24).

For A8/A9 grounding only (not a proposal): the empirically strongest stylised
facts found are (a) conditional drift concentration is 10–20× the unconditional
baseline when a wide-range bar prints without participation, (b) low
realised-vol states show persistently better forward drift but a tradable state
machine pays away more than the advantage once detection lag and costs are
charged (#13/#14 together are a cautionary pair: always simulate the gate, never
read the octile table), (c) aggressor-flow imbalance, hour-of-day, weekday,
ticket-size and cross-lag effects are too unstable on this window to build on.

## 5. Limitations and accidents

1. **Universe:** only BTC and ETH bars exist in this worktree; five of the seven
   frozen S0 symbols could not be screened at all. Every conclusion is
   two-symbol evidence and may not generalise to SOL/XRP/DOGE etc., whose
   microstructure differs materially.
2. **Missing companions:** no funding, clock, open-interest, basis or order-book
   data locally; `catalog/data/crypto_perpetual/*` holds instrument definitions
   only. Anything funding-dependent was untestable and therefore unproposed.
3. **Window tail:** bars stop at 2026-08-20T02:29Z; the declared window extends
   to 2026-08-21T00:00Z (~21.7 h, ≈87 bars per symbol) unscreened.
4. **Overlap bias found and disclosed:** initial per-trade figures for the
   survivor counted overlapping 16-bar holds inside signal clusters; the
   non-overlap re-measurement (#27) reverses the commercial verdict. This is
   recorded rather than smoothed over because the first number is what a casual
   reader would have acted on.
5. **Metric exposure accidents (recorded, closed immediately):**
   a grep over `research/hypotheses/**` returned a line from
   `_analysis_v2/v1_negative_analysis.md` quoting historical V1 per-cell
   expectancies; the file was not opened and the figures were not used. Reading
   `H-VOLCOMP-BRKOUT-v1/hypothesis.md` (nearest-family spec) exposed one
   sentence citing a historical scan-matrix pass count ("0/60 PASS"); closed,
   not used. No `results/**` file was opened at any time; no scoring, finalize,
   reproduction or V10-family metric artifact was accessed; no other agent's
   proposal draft was read; nothing was fetched; nothing installed.
6. **No code changes** were made to production/backtest/statistics paths; the
   only written artifacts are these two proposal files. All scratch computation
   lived in `.scratch_e0/` and was deleted before commit.
