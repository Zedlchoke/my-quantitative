# V12 D2 — A9-F Data/Schedule Feasibility Audit (six blind proposals)

Producer: A9-F (independent auditor). Schedule-only: counts, spans, weight
algebra, transition-cost bounds. **No returns, PnL, PF, Sharpe, ranking or
backtest was computed.**

- Worktree: `d2-a9f-feasibility` @ `9c176797ec23352b96047d5c41108da7ff13fe8b`,
  branch `orca/v12d-a9f-feasibility`, porcelain clean. The worktree did not
  exist at audit start; A9-F created it deterministically from the bootstrap
  SHA (`git worktree add -b orca/v12d-a9f-feasibility <path> <sha>`) and
  re-ran the identity gate (PASS). No other branch touched.
- Machine-readable audit: `a9f_feasibility_audit.json` (this file summarises it).
- Raw evidence (scratch, loader-selected values only):
  `a9f_scratch/a9f_inventory.json`, `a9f_scratch/a9f_stampgrid_warmup.json`,
  `a9f_scratch/a9f_books.json` (+ the two scripts that produced them).

## Verdict table

| ID | Verdict | Decisive reason (key numbers) |
|---|---|---|
| V12-A5-P1-BAB-LOWBETA | **PASS** | 90d warmup OK for 18/19 names at first stamp 2025-08-25; breadth 18-19, legs 4/4, max\|w\| 0.291; dec/365d 53.2; median holding 77d; drag 0.35%/0.65% (conservative no-hysteresis 0.87%/1.61%); max symbol share 13.1% (16.5% cons). |
| V12-A5-P2-MIX-ORDERSIZE | **PASS** | `quote_volume`+`count` verified in all bar files (fail-closed precondition met); trades>0 gate passes 100%; breadth 18-19; drag 1.5%/2.9% (cons. 1.7%/3.3%); share <= 10.9%. |
| H-A6-OSCOMP | **PASS** | 13 monthly stamps -> 14.1 dec/365d; breadth 18-19, legs 4/4; drag 0.35%/0.66%; symbol share 17.7% (cons) < 25%. F2: declared G-band [1.0,2.0] is internally inconsistent with its beta split + cap; cap-clamped side-gross <= 1.2 variant is what is feasible (and is what was measured). |
| H-A6-RVX | **PASS** | 56d pair data computable for >= 7/8 pairs at every stamp; all 8 pairs ever threshold-activatable (its own kill-condition needs < 2); turnover 4.9 units/yr; drag 1.0%/1.9%; max\|w\| 0.25; share 10.4%. F4: EG/ADF must be implemented in numpy or a dependency added before scoring (venv has neither statsmodels nor scipy). |
| A8-P1-BAB-PERP | **PASS** | Same feasible skeleton as A5-P1 measured independently: 53.2 dec/365d, breadth 18-19, median holding 77d, drag 0.35%/0.65% (cons. 0.87%/1.61%), share <= 16.5%; its extra churn guards were not simulated and only tighten these bounds. |
| A8-P2-TICKET-MIX-CONTRARIAN | **PASS** | Highest turnover of the six (33.3/yr hyst, 45.5/yr cons) yet drag 2.3%/4.4% (cons. 3.1%/6.0%) inside 8%/12%; breadth 18-19; median holding 14d; share <= 11.5%. |

No HIGH or CRITICAL unresolved findings -> all six selectable on
data/schedule feasibility grounds.

## Data verification highlights (Task 1)

- Bars: all 20 REQUIRED_SYMBOLS present, 2024-08-21/23 .. 2026-08-21/23,
  **zero missing 15m slots inside S0** for every symbol; `close`,
  `quote_volume`, `count` (Binance "Number of trades") all present.
- **Decode trap (F7, INFO):** bar `close` is a Nautilus raw i128 equal to
  `price x 1e16` for every symbol/file — *not* derivable from the file's
  `price_precision` metadata. Cross-validated per file against the bar's own
  `taker_buy_quote_volume / taker_buy_base_volume` (median rel err ~1e-3).
  Scoring lanes must decode at 1e16.
- ETHUSDT has exactly one gap: 57 slots on 2025-08-21 (00:00-14:30Z), just
  before the S0 head -> one name short of full breadth only while a trailing
  window overlaps it (worst case 13 of 52 stamps for the 90d beta). Never
  below 18 eligible (floor 9; A5 fail-closed needs >= 10: passes).
- Funding (scan_2026): `fundingTime`/`fundingRate`/`markPrice` present; mixed
  8h/4h/1h cadences (ACE 1h/2h/8h, ONG 1h/4h/8h phases). Max internal
  settlement spacing is 8.0h for every symbol -> the frozen PIT span rule
  (no hole > 8h) never trips. The contract's hole counter reports 2097/2182
  cosmetic "holes" for ACE/ONG — cadence-change artifacts, not lost data (F8).
- Instrument metadata complete; taker fee floor 0.05% (5bp) everywhere;
  tick sizes 1e-7..1e-2; worst one-tick slip ~6bp of price (NEAR, ADA).
- OI: files present but **unused by all six proposals** (as declared).

## Warmup (Task 2)

Per-stamp exact-window coverage grids for 28d/56d/90d over all 52 Monday
stamps: every symbol fully covers every horizon at every stamp except the
ETH-gap stamps listed above. A5-P1/P2's ">= 10 of 19 at first stamp"
fail-closed precondition passes at 18/19. 52 weekly stamps (and 13 monthly
for OSCOMP) support 3 chronological folds with holding-sized purge and >= 2
folds surviving — no proposal needs to move its first stamp.

## Breadth (Task 3)

Books built per each proposal's own declared rules on real features at every
stamp: eligible 18-19 (floor 9), extreme legs 4/4, zero cap violations
(max|w|: BAB 0.2909, A5-P2 0.210, A8-P2 0.153, OSCOMP exactly 0.30 where the
clamp binds, RVX 0.25). A5-P2's >= 80% bars-with-trades gate passes at 100%.
RVX: both legs' 56d complete for >= 7 pairs at every stamp (data
availability 100%); threshold activation (EG 10% + |hedge| in [0.25,4]) is
sparser by design — >= 1 pair at 34/52 stamps, all 8 pairs ever activatable
(its falsification condition (c) would need < 2 — clear).

## Cost/turnover (Task 4, schedule-only)

Declared rules simulated on real features -> one-way deltas priced with the
frozen adapter arithmetic (5bp + 1 tick baseline; x1.5 + 3 ticks stressed;
00:15Z bar-close fills). Two variants: declared hysteresis, and a
conservative no-hysteresis upper bound (re-form extreme legs every stamp).
Terminal force-flat excluded (adds <= 1.4 units once; no conclusion changes).

| Proposal | dec/365d | med hold | to/yr (hyst/cons) | base drag (hyst/cons) | stress drag (hyst/cons) | max sym share (cons) |
|---|---|---|---|---|---|---|
| A5-P1 | 53.2 | 77d | 7.6 / 18.6 | 0.35% / 0.87% | 0.65% / 1.61% | 16.5% |
| A5-P2 | 53.2 | 28d | 23.9 / 27.1 | 1.53% / 1.75% | 2.89% / 3.29% | 10.9% |
| OSCOMP | 14.1 | 56d | 10.1 | 0.35% | 0.66% | 17.7% |
| RVX | 53.2 | 56d | 4.9 | 1.02% | 1.91% | 10.4% |
| A8-P1 | 53.2 | 77d | 7.6 / 18.6 | 0.35% / 0.87% | 0.65% / 1.61% | 16.5% |
| A8-P2 | 53.2 | 14d | 33.3 / 45.5 | 2.30% / 3.15% | 4.36% / 5.96% | 11.5% |

Floors: 60 dec/365d, 3d median holding, 8%/12% drag, 25% symbol share —
**all six pass every floor, including under the conservative bound**.

## Adapter compatibility (Task 5)

All six expressible with existing `research/adapter_v10` interfaces:
ImmutableSchedule (weekly or every-4th-Monday instants), TargetBook
(weights + carried_forward; neutralisation/clamp inside the deterministic
constructor), FillRecord FILLED_NEXT_EVENT at the 00:15Z bar close (+1 event
stress), SettlementPoint funding natively under LONG_PAYS_POSITIVE_RATE,
StressSpec exactly covering the frozen surface (x1.5, +2 ticks, +1 event,
drop-one-symbol via universe(stress), drop-one-fold), and
`GenericStrategyBase.rebalance_cost_between` reused verbatim.
`research/v11/cost_feasibility.evaluate_schedule_cost_feasibility` consumes
exactly the artifacts these schedules emit. No new adapter capability needed.

## Resource estimate (Task 6)

The entire audit feature pass (20 symbols x ~35k bars, per-stamp coverage
grids, 52-stamp beta panel, 8 EG tests x 52 stamps, six book families, cost
pricing) runs in ~6s wall, < 1GB RSS. Production feature generation + stamp
books for all six families: minutes, < 2GB RAM on an 8GB M1. No resource risk.

## Findings index

- **F2 (MEDIUM, OSCOMP)** declared `G in [1.0, 2.0]` equal-side gross
  contradicts its beta-neutral split and its own 0.25 cap claim; feasible
  subrange is side-gross <= 1.2 with the declared clamp (measured at
  side-gross 1.0; max|w| = 0.30 where the clamp binds). Construction-clarity
  defect, not data impossibility.
- **F4 (MEDIUM, RVX)** no statsmodels/scipy in the venv: freeze a numpy
  EG/ADF implementation (audit used 1-lag ADF + MacKinnon EG 10% CV -3.05)
  or add the dependency BEFORE scoring.
- F1/F3/F5/F6 LOW, F7/F8/F9 INFO — see the JSON.
