# fixtures/ — hand-computed accounting gates for FILL_ACCOUNTING_SPEC (PC12A, pre-GO)

Six fixture cases pin the fill and bookkeeping model defined in
`../FILL_ACCOUNTING_SPEC.md` to the last identity. They are the future
accounting gate: a Stage-C engine that cannot reproduce every number below
within tolerance does not implement the spec, and any scored run it produces
is void (`NOT_RUN_INTEGRITY`, STOP-3). (fx6 added 2026-09-29 by the skeptic
F-16 remediation; fx2 renumbered/casing-unified by F-13/F-14 and its calendar
wording softened by F-15 — numbers unchanged.)

## What each fixture exercises

| fixture | mechanism pinned |
|---|---|
| `fx1_open_close_same_day.json` | entry+exit fills, spread-once law (cross = half-spread + slip, charged exactly once via the fill price), commission per side, gross-vs-mid, equity marks at each step, the decomposition invariant with zero swap |
| `fx2_overnight_hold_with_wed.json` | weekly-clock hold crossing a WEDNESDAY: the DECLARED U4/U5 swap calendar (Sun/Mon/Tue ×1, **Wed ×3**, Thu ×1, no event at Fri close or Sat — a declared modeling calendar, not a venue-measured fact) yields 7 pip-nights for 7 calendar nights; dated swap accrual rows; swap charged against, never income; equity marked at every accrual |
| `fx3_netting_two_legs_opposite.json` | L4 netting: two legs voting OPPOSITE on one asset (+0.6 / −0.4 lot) → ONE net fill of +0.2 lot; both votes journaled as VOTE rows with NULL fill fields; cash effect only on NET-ORDER rows; virtual per-leg attribution (pro-rata) sums exactly to book totals |
| `fx4_blocked_signal.json` | E3 fail-closed block (`BLOCKED_STALE`, PIT input 16d > P7D max-age): decision-state snapshot ONLY, no fill block, no cost block, zero cash/position effect; blocked leg casts NO netting vote while the sibling leg fills |
| `fx5_deferred_cost_guard.json` | L6 cost guard: trailing budget exhausted → `DEFERRED_COST_GUARD` row with the pre-commit estimate journaled but NOT charged; position and swap accruals continue; window rolls → same target executes at the next decision as an ADJUST; fixture ENDS OPEN so the invariant includes an unrealized leg |
| `fx6_worst_fill_grading.json` | §1.5 worst-fill grading: a stop-market exit on a gap bar that trades THROUGH the stop level fills at worst(bid_open, bid_close) − slip — never at the stop price; the distance beyond the ordinary quoted-side-open+band fill is booked as GAP EXCESS inside the slippage-beyond-halfspread line; the spread-once identity still holds; `LOSS_FILL` candidacy flagged |

All bars are synthetic (invented M1 bid/ask opens/closes at realistic
EURUSD June-2024 pip magnitudes, ~1.07–1.09, spreads 0.4 pip inside the
measured C1 EURUSD Friday-20:00 band p50 0.3 / p90 0.5). Every expected
number was computed by hand (see the `hand_calc` field of each fixture,
which states the decimal arithmetic step by step) and verified twice:
once in exact `Decimal` arithmetic (residual exactly 0) and once in float
(invariant residuals ≤ 2.8e-11, far inside the 1e-9 tolerance).

## Conventions block (fixture-law constants, same in all five)

`pip = 0.0001` · `lot = 100,000` base units · pip value `$10/pip/lot`
(USD-quote major) · commission `0.000035 × |Δ| × fill_price` per side (U2,
0.35 bps) · slippage `0.00002` (0.2 pip) per side non-event (U3; no fixture
fill sits inside an event window) · swap `1.0 pip/night` against the
position, Wed ×3, boundary 22:00 UTC (U4/U5) · initial cash `$100,000.00` ·
stress tier 1.0 · tolerance `1e-9`.

## Field map (what the engine consumes, what it must reproduce)

- `conventions` — the constants above (the engine must take them as inputs,
  never hardcode).
- `input_bars` — synthetic M1 bars with `role` ∈ {`decision_bar` (completed
  bar the decision reads, PIT), `fill_bar` (next bar whose OPEN prices the
  fill), `accrual_mark_bar` (bar whose mid_close marks equity at an accrual
  event)}.
- `decisions` — the frozen decision stream (votes, desired units, PIT
  snapshots, netting arithmetic, guard state; for fx5 also `guard_state`
  with the trailing-window instantiations at each decision).
- `expected.timeline` — `cash_usd_after`, `units_after`, `mark_mid`,
  `equity_usd_after` at EVERY step (decisions, fills, each accrual, final
  mark). `equity = cash + units × mark_mid` must hold at every row.
- `expected.fills` — `fill_price` (= quoted side ± slip), `mid_at_fill`,
  `spread_once_usd` (= |quoted_side − mid| × |Δ|), `slip_beyond_halfspread_usd`,
  `cross_cost_usd` (= `spread_once + slip` = `|fill − mid| × |Δ|` exactly),
  `commission_usd`, `cash_delta_usd`.
- `expected.costs` — totals plus `swap_lines` (one dated row per accrual
  event, with `multiplier` and `wed_x3`).
- `expected.gross_vs_mid_usd`, `expected.net_pnl_usd` — the trade-level and
  book-level identities.
- `expected.decomposition` — the invariant: `lhs` (Σ gross-vs-mid −
  Σ spread_once − Σ slip − Σ commission − Σ swap) vs `equity_delta`
  (`equity_T − equity_0`); `residual` must be ≤ 1e-9.
- `expected.vote_rows` / `blocked_rows` / `deferred_row` — journal-row laws:
  VOTE rows carry votes + netting blocks with NULL fill fields and
  `cash_delta_usd = 0`; BLOCK/DEFER rows carry the decision-state snapshot,
  outcome enum, reason detail, and NO fill/cost block.
- `hand_calc` — the human-auditable decimal arithmetic.

## How the future engine test consumes them

Equality assertions, tolerance `1e-9` on every number, plus structural
assertions (row kinds, NULL vs 0 discipline, swap calendar). Runner spec
(pytest-style pseudocode — no engine exists yet; the future
`tests/test_fill_accounting_fixtures.py` implements exactly this):

```python
# tests/test_fill_accounting_fixtures.py  (future; implements this spec)
import json, math, pathlib
import pytest

FIX = pathlib.Path("research/control/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1"
                   "/journal/fixtures")
TOL = 1e-9
FIXTURES = ["fx1_open_close_same_day", "fx2_overnight_hold_with_wed",
            "fx3_netting_two_legs_opposite", "fx4_blocked_signal",
            "fx5_deferred_cost_guard", "fx6_worst_fill_grading"]

@pytest.mark.parametrize("fid", FIXTURES)
def test_fill_accounting_fixture(fid):
    fx = json.loads((FIX / f"{fid}.json").read_text())
    conv = fx["conventions"]; exp = fx["expected"]

    engine = FillAccountingEngine(conv)          # implements FILL_ACCOUNTING_SPEC
    out = engine.replay(bars=fx["input_bars"], decisions=fx["decisions"],
                        guard_state=fx.get("guard_state"))

    # 1. timeline: cash / units / equity at EVERY step (strict order)
    assert len(out.timeline) == len(exp["timeline"])
    for got, want in zip(out.timeline, exp["timeline"]):
        assert got["event"] == want["event"]
        assert got["units_after"] == want["units_after"]
        for k in ("cash_usd_after", "equity_usd_after"):
            assert abs(got[k] - want[k]) < TOL, (want["event"], k)
        # book identity at every step
        assert abs(got["equity_usd_after"]
                   - (got["cash_usd_after"] + got["units_after"] * want["mark_mid"])) < TOL

    # 2. fills: fill price, spread-once law, commission
    assert len(out.fills) == len(exp["fills"])
    for got, want in zip(out.fills, exp["fills"]):
        for k in ("fill_price", "mid_at_fill", "spread_once_usd",
                  "slip_beyond_halfspread_usd", "cross_cost_usd",
                  "commission_usd", "cash_delta_usd"):
            assert abs(got[k] - want[k]) < TOL, k
        # spread-once law: the two crossing lines sum to |fill - mid| * |delta|
        assert abs((got["spread_once_usd"] + got["slip_beyond_halfspread_usd"])
                   - abs(got["fill_price"] - got["mid_at_fill"]) * abs(want["delta_units"])) < TOL

    # 3. swap lines: dates, multipliers, Wednesday x3, totals
    for got, want in zip(out.swap_lines, exp["costs"]["swap_lines"]):
        assert got["ts_utc"] == want["ts_utc"] and got["multiplier"] == want["multiplier"]
        assert got["wed_x3"] == want["wed_x3"]
        assert abs(got["swap_usd"] - want["swap_usd"]) < TOL

    # 4. totals + the decomposition invariant
    for k in ("spread_once_total_usd", "slip_total_usd",
              "commission_total_usd", "swap_total_usd"):
        assert abs(out.costs[k] - exp["costs"][k]) < TOL, k
    assert abs(out.gross_vs_mid_usd - exp["gross_vs_mid_usd"]) < TOL
    assert abs(out.net_pnl_usd - exp["net_pnl_usd"]) < TOL
    lhs = (out.gross_vs_mid_usd - out.costs["spread_once_total_usd"]
           - out.costs["slip_total_usd"] - out.costs["commission_total_usd"]
           - out.costs["swap_total_usd"])
    equity_delta = out.timeline[-1]["equity_usd_after"] - conv["initial_cash_usd"]
    assert abs(lhs - equity_delta) < TOL          # THE invariant, to 1e-9
    assert abs(exp["decomposition"]["residual"]) < TOL  # fixture self-check

    # 5. structural journal laws
    for row in out.vote_rows + out.blocked_rows + [r for r in out.deferred_rows]:
        assert row["fill_price"] is None and row["spread_once_usd"] is None
        assert row["cash_delta_usd"] == 0.0       # NULL, never 0-valued cost fields
    if fid == "fx4_blocked_signal":
        assert out.blocked_rows[0]["outcome"] == "BLOCKED_STALE"
        assert out.blocked_rows[0]["feature_pit_snapshot"][0]["max_age_ok"] is False
    if fid == "fx5_deferred_cost_guard":
        d = out.deferred_rows[0]
        assert d["outcome"] == "DEFERRED_COST_GUARD" and d["order_kind"] == "DEFER"
        assert abs(d["estimate"]["est_total_usd"]
                   - fx["decisions"][1]["estimate"]["est_total_usd"]) < TOL
    if fid == "fx6_worst_fill_grading":
        g = out.fills[1]                       # the graded stop exit
        assert g["graded"] is True and g["order_kind"] == "STOP_EXIT"
        assert abs(g["fill_price"] - exp["fills"][1]["fill_price"]) < TOL
        assert abs(g["fill_price"]
                   - (min(exp["fills"][1]["grading"]["bid_open"],
                          exp["fills"][1]["grading"]["bid_close"]) - conv["slip_applied_per_side"])) < TOL
        assert g["fill_price"] < fx["decisions"][0]["attached_standing_order"]["stop_level"]  # never at stop
        assert abs(g["gap_excess_usd"] - exp["fills"][1]["gap_excess_usd"]) < TOL
        assert g["loss_fill_candidate"] is True
        # gap excess sits INSIDE the slip line; spread-once identity intact
        assert abs(g["cross_cost_usd"] - (g["spread_once_usd"] + g["slip_beyond_halfspread_usd"])) < TOL
    if fid == "fx3_netting_two_legs_opposite":
        # both votes journaled; net fill is the SINGLE smaller position
        assert len(out.vote_rows) == 4 and len(out.fills) == 2
        assert out.fills[0]["delta_units"] == 20000
        v = exp["virtual_check"]
        assert abs(v["leg_TA_gross_vs_mid_usd"] + v["leg_MB_gross_vs_mid_usd"]
                   - exp["gross_vs_mid_usd"]) < TOL

# optional stress sweep: rerun each fixture at tier tau in {1.0, 1.5, 2.0}
# with every variable component scaled (fill crossing distance, commission
# rate, swap rate) and assert proportionality of the crossing/comm/swap
# lines and that the invariant still closes to 1e-9 (FILL_ACCOUNTING_SPEC §5).
```

## Reference numbers (for the handoff and quick eyeball)

| fixture | net PnL (USD) | swap total | ends |
|---|---|---|---|
| fx1 | 54.40717 | 0.00 | flat |
| fx2 | 274.40556 | 70.00 (Sun 10 + Mon 10 + Tue 10 + **Wed 30** + Thu 10; DECLARED U4/U5 calendar) | flat |
| fx3 | 8.07764 | 0.00 | flat |
| fx4 | 4.900432 | 0.00 | flat |
| fx5 | 5.658097 | 14.00 (two weeks × 7, each with Wed ×3; DECLARED U4/U5 calendar) | OPEN (30,000 units) |
| fx6 | **−21.560214** | 0.00 | flat (graded stop exit; gap excess $5.00 inside the slip line) |

Float values inside the JSONs are written at full round-trip precision; the
`hand_calc` fields state the decimal arithmetic; the two agree to ≤ 1e-9
(asserted at generation time and re-asserted by the runner).
