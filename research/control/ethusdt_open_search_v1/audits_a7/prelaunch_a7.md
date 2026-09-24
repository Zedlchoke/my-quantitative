# A7 PRELAUNCH AUDIT — ETHUSDT-OPEN-SEARCH-V1 (fresh context)

- Auditor: A7-fresh-context (independent; nothing trusted, everything recomputed from bytes)
- Audited at: 2026-09-24T15:19:34Z
- Interpreter for every python command: `/Users/hoangminhlong/my-quantitative/.venv/bin/python`
- Working dir: `/Users/hoangminhlong/my-quantitative/.worktrees/ethusdt-open-search-v1/integration`
- Plan authority read at: `/Users/hoangminhlong/my-quantitative/plans/PLAN_ethusdt_open_search_v1.md`
- Verdict: **REMEDIATION_REQUIRED** (2 blocking findings: F-1 HIGH, E-1 MEDIUM-blocking; details below)

---

## A. Freeze chain — PASS

Command: `shasum -a 256` on every file listed in `freezes/eos1_freeze.json` `code_freeze` and
`evidence_freeze`; compared against the recorded digests.

Observed — all 8/8 match exactly:

| file | recorded | recomputed | match |
|---|---|---|---|
| scripts/eos1_engine.py | 20eaf96f…64d1c4 | 20eaf96f…64d1c4 | YES |
| scripts/run_scored.py | 6747604…80f34a2 | 6747604…80f34a2 | YES |
| scripts/stage_all.py | c9ef1c8…e0e9e22 | c9ef1c8…e0e9e22 | YES |
| tests_py/test_fixtures.py | 1266bbb…f21bac | 1266bbb…f21bac | YES |
| freezes/staged_manifest.json | 18911c1…9741b6 | 18911c1…9741b6 | YES |
| freezes/census.json | 30fee58…c0c539 | 30fee58…c0c539 | YES |
| freezes/feasibility.json | ba93e45…c691d9 | ba93e45…c691d9 | YES |
| freezes/dry_run.json | 654e65d…dea4df | 654e65d…dea4df | YES |

Note: freeze `tree.head` = e18ff6b2 (registry head agrees); current worktree HEAD is c52e8eb
(the P3 files were committed after the freeze was built). The freeze pins bytes by sha256, and
`git status` shows no tracked file modified (only gitignored `data_local/` untracked), so the
chain is byte-valid at audit time.

Verdict: **PASS**.

## B. Fixtures — PASS

Command: `/Users/hoangminhlong/my-quantitative/.venv/bin/python research/control/ethusdt_open_search_v1/tests_py/test_fixtures.py`

Observed: 43/43 individual checks printed `PASS` across all 9 fixture groups (resample golden,
indicators, one-bar lag + costs-once, funding sign/cadence, fold boundary, truncation invariance,
block-shuffle determinism, no-lookahead mutation, tier scaling). Exit code **0**. Final line:
**`ALL FIXTURES PASS`**.

Verdict: **PASS**.

## C. Census spot-recompute — PASS

C1. Independent 1h recount (own parser written for this audit, no engine import, raw zip bytes
    of `data_local/vision/klines_um_ETHUSDT_1h/*.zip`):
    observed **58,440 bars, first 2020-01-01T00:00:00Z, last 2026-08-31T23:00:00Z** — exactly
    equal to `freezes/census.json` (`bars_1h 58440`, same first/last). Vision's true floor is
    2020-01-01, so 2019-10/11/12 are MISSING in `staged_manifest.json` (MISSING verdicts
    recorded after the retry law) — the plan's warmup-truncation disclosure covers this.
C2. Zip hash spot-check (2020-01, 2023-07, 2026-08 — includes one 2020 and one 2026 month) on
    both `klines_um_ETHUSDT_1h` and `fundingRate_um_ETHUSDT`: **6/6 sha256 match**
    `staged_manifest.json`. Full inventory sweep: every zip on disk is in the manifest with a
    matching hash, no phantom entries, no missing files (ETH 80, BTC 80, ETHBTC 88, funding 80).
C3. Funding first settlement: read the earliest funding zip on disk
    (`fundingRate_um_ETHUSDT/2020-01.zip`), first row `calc_time=1577836800000` =
    **exactly 2020-01-01T00:00:00Z**. No earlier funding month exists on disk (2019-11/12
    confirmed MISSING). Census `first_settlement` matches.

Verdict: **PASS**.

## D. Dry-run hygiene — PASS

D1. Raw-byte leak scan over the serialized `freezes/dry_run.json` (case-insensitive) for
    `pnl, net, gross, fee, profit, drawdown, mdd, sharpe, stress, equity, payoff`: the ONLY hit
    in the entire file is the required hygiene flag `"real_pnl": false`. No per-fold dollar
    amounts anywhere (every `books` value is an integer count or boolean). The flags
    `"scored": false`, `"real_pnl": false`, `"published": false` are present as required
    metadata. No outcome data leaked.
D2. **84 records, pairwise-distinct** record IDs (`record_ids_pairwise_distinct: true`
    re-verified independently; 84 = 8 arms×3 tiers + 4 refs×3 tiers + 8 arms×2 controls×3
    tiers; `expected_computations == actual_computations == 84`, `denominator_delta: 0`).
D3. Every non-`BASE_CASH` book has `fills > 0` (re-verified: zero exceptions);
    `BASE_CASH` books all have fills=0, decisions=0, funding events=0. `dry_run_pass: true`.

Verdict: **PASS**.

## E. Engine adversarial review — PASS_WITH_FINDINGS

Read `scripts/eos1_engine.py` in full (470 lines).

E1 PIT/lookahead — PASS. `build_targets` computes raw states at each ETH H4 bar ts (an SMA/state
at info bar j uses only closes ≤ j, knowable at bar j's close = ts(j)+4h) and then applies
exactly one positional shift `[0]+raw[:-1]`; `run_book` consumes `target[i]` at bar i's OPEN
(`open_(desired, bar["open"], …)`). Decision at bar i−1 close (time ts(i)) fills at bar i open
(time ts(i)) — no bar uses its own close for its own decision. Property test run by A7: mutating
the last info bar's close leaves `target[0..n-2]` unchanged (PIT holds). The ONLY close-derived
fill in the engine is the fold-end force-flat at the LAST existing bar's close — that is the
plan-frozen boundary law (§3), not an info-driven decision. Missing info boundaries read the
last observed state (hold, counted in feasibility `reads_fallback_last_observed`) — PIT-safe.

E2 Cost law — PASS. `fees = qty*entry_raw*fee + qty*px_raw*fee` (5 bps×tier on RAW prices both
legs); adverse tick 0.01×tier in PRICE per side (`entry_px = px_raw ± tick`, `exit_eff = px_raw ∓
tick`, long pays up); tier scales fee+tick only (fixture 9 + code); funding cashflow
`cf = -pos*qty*px*rate` (longs pay positive rates, shorts receive; fixture 4); `qty =
100000/px_raw` at entry. Entry fee booked once at exit is accounting attribution — `close()`
books both legs' fees exactly once and `open_()` books none; `fills_total` counts each side once.

E3 Fold law — PASS. Fold membership by UTC date of ETH bar open_ts with frozen bounds
F1 [2020-01-01,2021-05-01) … F4 [2025-01-01,2026-09-01); trading only inside folds (bars with
`fold is None` are skipped entirely); at the LAST existing bar of a fold, `close(bar["close"],
fold)` fires when `fold_of(next) != fold` (or data end) — force-flat at that bar's CLOSE, trade
attributed to the exit fold; no position crosses a boundary. Warmup bars cannot open positions
(skipped before any fill).

E4 Mutation (run by A7 with invented numbers, not the test's) — PASS. Synthetic 10-bar F1 case,
`raw=[0,0,1,0,0,1,1,0,0,1]` vs the same info one bar later: fill schedules move bar-by-bar
(ENTER@bar3/EXIT@bar4/ENTER@bar6/EXIT@bar8 → ENTER@4/EXIT@5/ENTER@7/EXIT@9), gross differs,
repeat run identical. The shipped test (group 8) does assert the same property; A7's independent
numbers confirm.

E5 Settlement pricing — **FAIL (finding E-1, MEDIUM, blocking)**. Frozen law (per plan-disclosed
engine contract and this audit's checklist): fallback = close of the last 1h bar **ending** ≤ ts.
Implementation (`PriceAtSettlement.price`): exact 1h-open stamp → that bar's OPEN (correct);
otherwise the last bar with open_ts **≤ ts** and its **CLOSE**. On real staged data, 3,267 /
7,305 funding stamps (44.7%) carry odd milliseconds (e.g. `2020-01-02T00:00:00.002Z`); for every
one of them the floor-hour bar exists, so the fallback returns the settlement-hour bar's CLOSE —
a price finalized up to 1 hour AFTER the settlement instant. Deterministic (verified across
instances) and economically small (same-hour close-vs-open delta on a ~$10-scale cashflow;
direction roughly cost-conservative for long books), but it violates the stated fallback law and
"cannot use future prices" does not hold. The implementer's own event log mischaracterizes it as
"bar-close ending at ts" — the close used ends at floor(ts)+1h > ts. Remediation pre-GO is
trivial (price odd-ms stamps at floor-hour OPEN — knowable at the stamp — or at the last bar
ENDING ≤ ts). Secondary: the `settlement_price_fallbacks` counter is a running cumulative total
across all 84 book runs (shared `PriceAtSettlement` instance), so per-record values in
`dry_run.json` are not per-book (LOW, observability only; not consumed by any gate).

E verdict: E1–E4 PASS; E5 FAIL → **PASS_WITH_FINDINGS**.

## F. Plan conformance — FAIL (finding F-1, HIGH, blocking)

F1 Gates, `scripts/run_scored.py gates()` vs plan §6:

- G1 `net>0 @1.0×` ✓; G2 `net>0 @1.5×` ✓; G3 strictly beats
  BASE_ALWAYS_ON_LONG / BASE_TREND_LF / REF_SHORT_ALWAYS ✓ (BASE_CASH covered by G1);
  G4 `≥3/4 folds>0 OR best-fold-removed>0` ✓; G5 max positive-fold share ≤0.50 ✓;
  G6 both controls not out-earning @1.0× ✓ (implemented strict `>` — a tie kills, LOW note;
  ties unreachable for valid cells since feasibility requires shuffle≠arm and non-zero flips);
  G10 combined-net increase vs BASE_TREND_LF + no fold flips pos→neg ✓; G11 disclosure-only,
  values pulled from frozen feasibility.json ✓.
- **G7 — FINDING F-1 (HIGH, blocking):** implementation is
  `cost_roundtrip_bps(c15["res"], 1.5) <= 10.0` where the formula is
  `2*FEE_BPS*tier + (2*TICK*tier/px)*1e4`. At tier 1.5 the fee floor alone is
  2×5 bps×1.5 = **15 bps > 10 bps** for any price, so G7 is **structurally unpassable for every
  cell**; `all_pass` can never fire and the runner's verdict is predetermined to
  `…NO_INCREMENTAL_VALUE` regardless of economics. The plan's G7 text attaches "@1.5×" only to
  the fills clause; the cost clause's tier is unpinned (and even at 1.0× a fee+tick round trip
  is 10.07 bps > 10 strict — only a fee-only baseline reading passes at exactly 10). §12 forbids
  gate amendments, so this needs an owner ruling (pre-outcome clarification/erratum of the
  intended tier+components, or accept G7 as a structural kill and do not spend the GO). Must be
  resolved BEFORE the owner types GO; burning the GO with this gate intact wastes the 8-cell
  budget on a predetermined verdict.
- G8/G9 are process gates (P5 detached twin; this audit) — correctly not per-cell numeric.

F2 Verdict enum: freeze `verdict_enum` matches plan §11 **exactly** (5 strings, byte-equal).
Budget: plan 8 = freeze `cells_max` 8 = state.json 0/8 = registry 0/8 ✓. Refs list in freeze ==
plan §4 (BASE_CASH, BASE_ALWAYS_ON_LONG, BASE_TREND_LF, REF_SHORT_ALWAYS) ✓. Arm ladder in
`ARMS` == plan §5 (A1-A4/B1-B4 incl. declared combos and ladders) ✓. LOW notes: plan §1 cites a
"symbol-swap law, §14.3" but the plan has 12 sections (dangling reference; the law itself is in
§0/§1); `scored()` auto-emits only 2 of the 5 enum values (the other three live at process
level — if BLOCKED_DATA appeared at scored time the runner would still print
NO_INCREMENTAL_VALUE).

F3 GO guard — verified by code read and by ATTEMPT: with no
`audits_a7/go_authorization.json` present, `run_scored.py scored` printed
`REFUSED: no audits_a7/go_authorization.json (STOP-1 owner gate not passed)` and exited **2**
before any computation (auth check is the first statement; no data loaded, no PnL). Phrase
equality against the registered `GO ETHUSDT OPEN SEARCH V1 SCORED EXECUTION` is exact. No
fabricated authorization was created.

F4 Hygiene paths — network code exists only in `p1_probe.py` and `stage_all.py`, both keyless
GETs to `https://data.binance.vision` (preregistered pacing/backoff; no auth headers, no
accounts, no trading endpoints; no orders anywhere; no credentials in any script). The only
cross-cycle reference is `census.py` reading ES1's `staging_manifest.json` — read-only
cross-check, explicitly allowed by plan §10. All writes stay inside the cycle namespace
(`freezes/*`, `scored/scored_summary.json`, `scripts/probe_result.json`). Scored mode has no
network path.

F verdict: **FAIL** on G7 (F-1); everything else conforms.

## G. Ancestry/novelty adjudication — PASS (no veto)

Method: read all 124 rows of `/Users/hoangminhlong/my-quantitative/research/wayfinder/FAMILY_FAILURES.jsonl`
(40 `asset:"crypto"`), full text searched for ETH / ETHBTC / ratio / rotation / lead-lag /
cross-asset; adjudicated each lane against the (info-source, vehicle) tuples.

Lane E1 (BTC H4 price state → ETHUSDT long/flat; info=BTCUSDT series, vehicle=single-asset
ETHUSDT):
- Dead comparators: `PSV1-BTC_H1-UPTREND-BREAKOUT_CONT`, `PSV1-BTC_H1-ACC-FLOOR_PROVISION`,
  `PSV1-BTC_H1-DOWNTREND-BREAKDOWN_CONT`, `PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION` — all four
  are BTC **own-price phase routers gating BTC books** (tuple (BTC, BTC)); their kills (G3
  baseline loss; G6 block-shuffle control out-earned) say BTC phase timing carried no value FOR
  BTC. E1's tuple (BTC → ETH) differs in the vehicle member and the hypothesis (cross-asset
  re-rating), so it is NOT a symbol/timeframe/parameter swap of them. (The true symbol-swap
  forbidden zone — ETH-own-price entry timing — is exactly what E1 does NOT do.)
- Closest prior external-gate use: `A8-V11-ILLIQ-AMIHUD/REG-GATE-O1V2` (gate member V2 = BTC
  rvol30 floor) — but that gates an already-dead cross-sectional weekly illiquidity book with a
  BTC realized-VOL floor, a different info form and vehicle; it does not preempt E1.
- Cross-sectional families (`XSECT-*`, `ILLIQ-*`, `OILEV`, `A5-V15/V16`) rank many symbols
  relatively — never another asset's absolute state executed on one asset. **E1 is a new
  (info-source, vehicle) tuple: NO VETO.**

Lane E2 (ETHBTC spot ratio trend/pct-rank → ETHUSDT long/flat; info=ETHBTC ratio series,
vehicle=single-asset ETHUSDT):
- Dead comparators: funding/basis classes (`CARRY-1D/3D/7D`, `V17-A6-P1-FUNDJUMP`,
  `A14-V14-A5-BASISLV-PREMFADE`) are perp funding/basis, not the spot price ratio; dead
  pair-spread TRADING trades two legs (E2 trades none — no spread PnL); dead regime routers
  (RSM/JEV/PSV1/TRV1/ILLIQ-REG per plan §0) key on the traded asset's own state, not a
  bivariate ratio; `XSECT-TSTREND`/`H-XSECT-*` are cross-sectional rank universes, not a single
  ratio's absolute trend. No crypto row contains ETHBTC or a ratio-trend gate on ETH.
- **E2 is a new (info-source, vehicle) tuple: NO VETO.**
- Disclosure note (not a veto): feasibility G11 Spearman vs BASE_TREND_LF is 0.56–0.87 (E1) and
  0.16–0.27 (E2) — recorded pre-PnL, disclosure-only per plan G11; the PSV1-BTC_H4 shuffle
  control result is adverse empirical evidence about BTC gate timing that E1's own G6 will test.

G verdict: **PASS**.

## H. Registry consistency — PASS

Command: `cd /Users/hoangminhlong/my-quantitative && .venv/bin/python research/researchctl.py cycle list | grep ETHUSDT`
plus direct read of `plans/CYCLE_REGISTRY.json`.

Observed: `ETHUSDT-OPEN-SEARCH-V1 ACTIVE_LIGHT 0/8 e18ff6b orca/ethusdt-open-search-v1-integration`;
registry record has `plan: plans/PLAN_ethusdt_open_search_v1.md`, `budget {used:0, max:8}`,
`go_phrase: "GO ETHUSDT OPEN SEARCH V1 SCORED EXECUTION"` with state `REGISTERED_NOT_CONSUMED`,
`s1: SEALED_UNTOUCHED`, head matching freeze `tree.head`.

Verdict: **PASS**.

---

## Findings summary

| id | severity | blocking | where | what |
|---|---|---|---|---|
| F-1 | HIGH | YES | `scripts/run_scored.py` `gates()` G7 / plan §6 G7 | G7 cost clause pinned at tier 1.5× (2×5bps×1.5 = 15 bps fee floor alone) — structurally unpassable for every cell; every-cell all_pass impossible; scored verdict predetermined to NO_INCREMENTAL_VALUE regardless of economics. Owner must rule the intended tier/components pre-outcome before GO. |
| E-1 | MEDIUM | YES | `scripts/eos1_engine.py` `PriceAtSettlement` fallback | 44.7% of funding stamps (3,267/7,305) are odd-ms and get priced at the settlement-hour bar's CLOSE, finalized up to 1h AFTER the settlement — violates the stated fallback law ("last 1h bar ending ≤ ts"); deterministic, economically small, cost-conservative for long books; trivial pre-GO fix (floor-hour OPEN or last bar ending ≤ ts). Implementer event log mischaracterizes the law as satisfied. |
| L-1 | LOW | no | `gates()` G6 | Implemented strict `>` (a tie kills); plan's "must NOT out-earn" admits ties. Unreachable for valid cells. |
| L-2 | LOW | no | `run_scored.py scored()` | Auto-verdict emits only 2 of the 5 plan-enum values; BLOCKED_DATA/NO_ELIGIBLE/TECHABORT branches live at process level. |
| L-3 | LOW | no | `dry_run.json settlement_price_fallbacks` | Cumulative counter shared across all 84 runs, not per-book (non-monotone in display order); observability only. |
| L-4 | LOW | no | plan §1 | Dangling reference "§14.3" (plan has 12 sections). |

## Verdict

**REMEDIATION_REQUIRED.** Everything an audit can certify clean is clean: the freeze chain is
byte-exact, fixtures pass, the census reproduces from raw zip bytes, the dry-run is hygienic and
non-vacuous (84/84), the engine's PIT/cost/fold/mutation laws hold under adversarial test, the
GO guard refuses correctly, no order/credential/network path exists in scored mode, both lanes
are genuinely new (info-source, vehicle) tuples (no veto), and the registry is consistent.
Two pre-outcome defects must be resolved before the owner types GO: F-1 (G7 gate structurally
disables the verdict ceiling — HIGH) and E-1 (settlement fallback uses a future close on 44.7%
of funding events — MEDIUM). No scored PnL exists; budget and denominators remain 0/8
unconsumed; both fixes are pre-PnL and leave no outcome exposure.
