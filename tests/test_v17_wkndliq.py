"""CRYPTO-V17 A8 WKNDLIQ lane tests (V17-A4-P1-WKNDLIQ, post-F1 remediation).

Synthetic only: every expected number below is computed BY HAND from the
frozen proposal (research/control/v17_run/d1/a4/proposal_P1.json, blob sha
efb773bcc3d70ae1c348be5ba0c99a7ee5efda47).  No real data file is read,
nothing is scored outside ``tmp_path``.

Fixture map (task items a-f):

* (a) weekend window boundary
      - test_anchor_calendar_flag_hand_computed   (-1 at Friday 21:00 only)
      - test_anchor_window_boundary_fri22_mon00   (decision Friday 21:00 ->
      Friday 22:00 vwap fill; cover Monday 00:00 vwap; 50 held buckets)
* (b) neighbour window
      - test_neighbour_window_fri20_mon02         (Friday 19:00 decision ->
      Friday 20:00 fill; Monday 02:00 cover; 54 held buckets)
* (c) sham: exclusion of overlap + seed determinism + one draw per week
      - test_sham_seed_determinism_one_draw_per_week (independent
      re-derivation of the default_rng(17040001) stream)
      - test_sham_windows_never_overlap_anchor    (admissible offsets
      72..140 only; equal 50-bucket duration; pairwise disjoint)
      - test_sham_refuses_nonfrozen_seed
* (d) rule-4 enforcement fail-closed
      - test_rule4_enforcement_dead_on_sparse_calendar (per-fold counts
      hand-computed on a 30-day fixture)
      - test_rule4_enforcement_pass_on_rich_calendar (180-day fixture)
      - test_rule4_malformed_block_refused_at_load
      - test_rule4_enforcement_refuses_unevaluable_anchor
      - test_no_frozen_rules_no_enforcement_field (legacy specs untouched)
* (e) availability law
      - test_availability_calendar_only (price/flow tamper leaves the
      series byte-identical; no bucket-close observable is consumed)
* (f) spec + diag contract load through the frozen paths
      - test_spec_loads_through_driver_schema
      - test_spec_end_to_end_scored_sanitized_and_enforced
      - test_diag_contract_passes_persistability_gate
"""

from __future__ import annotations

import copy
import json
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pytest

from research.control.v17_run.driver import family_registry_v17 as reg
from research.control.v17_run.driver import run_v17_cell as d
from research.governance.diagnostic_persistability import (
    CONDITIONAL_REQUIRED_FIELDS,
    expected_artifacts_from_contract,
    validate_contract,
)

REPO = Path(__file__).resolve().parents[1]
FAMILIES_DIR = REPO / "research/control/v17_run/driver/families"
SPEC_PATH = FAMILIES_DIR / "V17-A4-P1-WKNDLIQ.spec.json"
CONTRACT_PATH = FAMILIES_DIR / "V17-A4-P1-WKNDLIQ.diag_contract.json"
S0 = date(2025, 8, 22)  # a Friday, per the frozen S0 window


@reg.register("WKNDTEST.h1_first_bucket_long", example_only=False)
def _first_bucket_long(panels, params):
    """Test-only nonzero book (+1 over the first bucket of each symbol) so
    the legacy no-frozen-rules cell is non-vacuous without touching any
    WKNDLIQ formula."""
    return {
        sym: [1.0] + [0.0] * (len(rows) - 1)
        for sym, rows in panels.items()
    }

ANCHOR_PARAMS = {
    "entry_weekday_utc": "Friday",
    "entry_hour_utc": 22,
    "cover_weekday_utc": "Monday",
    "cover_hour_utc": 0,
}
NEIGHBOUR_PARAMS = {
    "entry_weekday_utc": "Friday",
    "entry_hour_utc": 20,
    "cover_weekday_utc": "Monday",
    "cover_hour_utc": 2,
}
CONTROL_PARAMS = {
    "entry_weekday_utc": "Friday",
    "entry_hour_utc": 22,
    "seed": 17040001,
    "holding_buckets": 50,
}
ADMISSIBLE = list(range(72, 141))  # Friday-anchored, no-overlap (69)


def _day(i: int) -> str:
    return (S0 + timedelta(days=i)).isoformat()


def _row(idx: int, symbol: str, vwap: float) -> dict:
    day, hour = idx // 24, idx % 24
    base = 100.0 + 0.01 * idx
    return {
        "symbol": symbol,
        "hour_utc": f"{_day(day)}T{hour:02d}",
        "day_utc": _day(day),
        "n_trades": 10,
        "vwap": vwap,
        "first_price": base,
        "last_price": base * 1.001,
        "entry_gap_s": 0.3,
    }


def _panels(n_days: int) -> dict:
    def rows_for(sym: str) -> list:
        return [
            _row(i, sym, (100.0 + 0.01 * i) * 1.0001)
            for i in range(n_days * 24)
        ]

    return {
        "BTCUSDT": rows_for("BTCUSDT"),
        "ETHUSDT": rows_for("ETHUSDT"),
    }


def _flag_index(series) -> set:
    return {i for i, v in enumerate(series) if v != 0.0}


# ------------------------------------------------------------------------- #
# (a) weekend window boundary: Friday 21:00 decision -> Friday 22:00 fill;
#     Monday 00:00 cover
# ------------------------------------------------------------------------- #
def test_anchor_calendar_flag_hand_computed():
    panels = _panels(24)  # Fridays at day offsets 0, 7, 14, 21
    series = reg.resolve("WKNDLIQ.anchor")(panels, ANCHOR_PARAMS)
    assert set(series) == {"BTCUSDT", "ETHUSDT"}
    for sym, rows in panels.items():
        s = series[sym]
        assert len(s) == len(rows)
        # the flag is -1.0 at EXACTLY the Friday hour_utc=21 buckets (the
        # decision at that bucket's close fills at the next bucket vwap)
        expected = {
            i
            for i, r in enumerate(rows)
            if datetime.strptime(r["day_utc"], "%Y-%m-%d").weekday() == 4
            and r["hour_utc"].endswith("T21")
        }
        assert _flag_index(s) == expected
        assert all(s[i] == -1.0 for i in expected)
        # no warmup None: a pure calendar flag decides everywhere
        assert all(v in (0.0, -1.0) for v in s)


def test_anchor_window_boundary_fri22_mon00(tmp_path, monkeypatch):
    """24-day world: Fridays 0/7/14/21; the 1-day purge on fold edges
    {7,8,15,16} and the grid end refuse every weekend but Friday 0, so the
    anchor books EXACTLY one trip per symbol: entry at the Friday 22:00
    bucket vwap, cover at the Monday 00:00 bucket vwap (50 held buckets)."""
    _, (spec,) = d.load_selection(SPEC_PATH)
    manifest = _stage(tmp_path, spec, n_days=24)
    monkeypatch.setattr(d, "PANEL_DIR", manifest["_panel_dir"])
    h1 = d.load_panels(d.repo_root(), manifest, spec.universe)
    state = d.compute_family(spec, h1, base_dir=tmp_path, allow_example=False)
    trips = state["arms"]["anchor"]["trips"]
    assert len(trips) == 2  # one weekend, both symbols
    for trip in trips:
        sym = trip["symbol"]
        entry_b, exit_b = trip["entry_bucket"], trip["exit_bucket"]
        # decision Friday 21:00 -> entry Friday 22:00 (driver one-bar lag:
        # the decision consumes the Friday-21 row, closed at the Friday-22
        # bucket open; the lag-0 fill executes INSIDE the position bucket
        # at its published vwap)
        assert h1[sym][entry_b]["hour_utc"].endswith("T22")
        assert datetime.strptime(
            h1[sym][entry_b]["day_utc"], "%Y-%m-%d"
        ).weekday() == 4
        assert trip["decision_bucket"] == entry_b  # lag-0 convention
        assert h1[sym][entry_b - 1]["hour_utc"].endswith("T21")
        assert h1[sym][entry_b - 1]["day_utc"] == h1[sym][entry_b]["day_utc"]
        # cover Monday 00:00, exactly 50 held H1 buckets later
        assert exit_b == entry_b + 50
        assert h1[sym][exit_b]["hour_utc"].endswith("T00")
        assert datetime.strptime(
            h1[sym][exit_b]["day_utc"], "%Y-%m-%d"
        ).weekday() == 0
        # fills execute at the published bucket VWAPs (fixture: vwap =
        # (100 + 0.01*idx) * 1.0001), short position
        assert trip["position"] == -1.0
        base_entry = 100.0 + 0.01 * entry_b
        base_exit = 100.0 + 0.01 * exit_b
        assert state["prices"][sym][entry_b] == pytest.approx(
            base_entry * 1.0001)
        assert state["prices"][sym][exit_b] == pytest.approx(
            base_exit * 1.0001)
    # and the BOOKED fills carry exactly those published prices
    book = d.simulate_book(
        trips, state["prices"], "T2.0", spec.universe)
    for sym in spec.universe:
        entry_fill = next(
            f for f in book.fills if f.symbol == sym and f.role == "entry")
        exit_fill = next(
            f for f in book.fills if f.symbol == sym and f.role == "exit")
        assert entry_fill.price == pytest.approx(
            (100.0 + 0.01 * entry_fill.bucket) * 1.0001)
        assert exit_fill.price == pytest.approx(
            (100.0 + 0.01 * exit_fill.bucket) * 1.0001)
    # and the positions themselves live on exactly the Friday-22 buckets,
    # fed by the Friday-21 decision rows (the calendar decision law)
    for sym in spec.universe:
        for d_b, pos in state["arms"]["anchor"]["positions"][sym].items():
            assert pos == -1.0
            assert h1[sym][d_b]["hour_utc"].endswith("T22")
            assert h1[sym][d_b - 1]["hour_utc"].endswith("T21")


# ------------------------------------------------------------------------- #
# (b) neighbour 30-bucket-label window: Friday 20:00 -> Monday 02:00
# ------------------------------------------------------------------------- #
def test_neighbour_window_fri20_mon02(tmp_path, monkeypatch):
    """Same 24-day world, neighbour arm: decision Friday 19:00, entry fill
    Friday 20:00 vwap, cover Monday 02:00 vwap (54 held buckets = the
    frozen '30-bucket' window's true calendar span)."""
    _, (spec,) = d.load_selection(SPEC_PATH)
    manifest = _stage(tmp_path, spec, n_days=24)
    monkeypatch.setattr(d, "PANEL_DIR", manifest["_panel_dir"])
    h1 = d.load_panels(d.repo_root(), manifest, spec.universe)
    state = d.compute_family(spec, h1, base_dir=tmp_path, allow_example=False)
    trips = state["arms"]["neighbour"]["trips"]
    assert len(trips) == 2
    for trip in trips:
        sym = trip["symbol"]
        entry_b, exit_b = trip["entry_bucket"], trip["exit_bucket"]
        assert h1[sym][entry_b]["hour_utc"].endswith("T20")
        assert datetime.strptime(
            h1[sym][entry_b]["day_utc"], "%Y-%m-%d"
        ).weekday() == 4
        assert trip["decision_bucket"] == entry_b  # lag-0 convention
        assert h1[sym][entry_b - 1]["hour_utc"].endswith("T19")
        assert h1[sym][entry_b - 1]["day_utc"] == h1[sym][entry_b]["day_utc"]
        assert exit_b == entry_b + 54
        assert h1[sym][exit_b]["hour_utc"].endswith("T02")  # Monday 02:00
        assert datetime.strptime(
            h1[sym][exit_b]["day_utc"], "%Y-%m-%d"
        ).weekday() == 0
        assert trip["position"] == -1.0
    # formula-level: the neighbour flag fires at Friday 19:00, two hours
    # before the anchor's, and nowhere else
    anchor = reg.resolve("WKNDLIQ.anchor")(_panels(24), ANCHOR_PARAMS)
    neighbour = reg.resolve("WKNDLIQ.neighbour")(_panels(24), NEIGHBOUR_PARAMS)
    for sym in anchor:
        assert _flag_index(neighbour[sym]) == {
            i - 2 for i in _flag_index(anchor[sym])
        }


# ------------------------------------------------------------------------- #
# (c) sham: exclusion of overlap + seed determinism + one draw per week
# ------------------------------------------------------------------------- #
def test_sham_seed_determinism_one_draw_per_week():
    n_days = 38  # Fridays at day offsets 0,7,14,21,28,35 -> SIX weeks
    panels = _panels(n_days)
    control = reg.resolve("WKNDLIQ.control")(panels, CONTROL_PARAMS)
    again = reg.resolve("WKNDLIQ.control")(panels, CONTROL_PARAMS)
    assert control == again  # deterministic: pure function of the seed
    # independent re-derivation BY HAND: one default_rng(17040001) draw per
    # Friday-anchored week, ascending, uniform over the 69 admissible
    # offsets; a decision is placed iff its entry bucket is on-grid
    rows = panels["BTCUSDT"]
    index_of = {r["hour_utc"]: i for i, r in enumerate(rows)}
    rng = np.random.default_rng(17040001)
    expected = [0.0] * len(rows)
    fridays = [
        i // 24
        for i, r in enumerate(rows)
        if datetime.strptime(r["day_utc"], "%Y-%m-%d").weekday() == 4
        and r["hour_utc"].endswith("T00")
    ]
    assert len(fridays) == 6
    drawn_offsets = []
    for fd in fridays:
        k = ADMISSIBLE[int(rng.integers(0, len(ADMISSIBLE)))]
        drawn_offsets.append(k)
        entry_dt = datetime(S0.year, S0.month, S0.day) + timedelta(
            days=fd, hours=k
        )
        decision_key = (entry_dt - timedelta(hours=1)).strftime("%Y-%m-%dT%H")
        di = index_of.get(decision_key)
        if di is not None and di + 1 < len(rows):
            expected[di] = -1.0
    assert control["BTCUSDT"] == expected
    assert control["ETHUSDT"] == expected  # symbols independent, same book
    # the last week's entry (day 35 + 3..5 days) is off-grid: the draw is
    # CONSUMED anyway (one draw per week, frozen stream) but not placed
    placed = _flag_index(control["BTCUSDT"])
    assert len(placed) == len(fridays) - 1


def test_sham_windows_never_overlap_anchor():
    n_days = 80  # ~12 weeks of sham draws
    panels = _panels(n_days)
    control = reg.resolve("WKNDLIQ.control")(panels, CONTROL_PARAMS)["BTCUSDT"]
    rows = panels["BTCUSDT"]
    entries = [i + 1 for i in _flag_index(control)]
    assert entries
    friday_starts = {
        i
        for i, r in enumerate(rows)
        if datetime.strptime(r["day_utc"], "%Y-%m-%d").weekday() == 4
        and r["hour_utc"].endswith("T00")
    }
    H = 50
    for e in entries:
        # the entry offset within its Friday-anchored week is admissible
        fd = max(f for f in friday_starts if f <= e)  # f is a bucket index
        k = e - fd
        assert k in ADMISSIBLE  # 72..140: Monday 00:00 .. Wednesday 20:00
        # and its equally-long window misses EVERY true anchor window
        # (anchor entry Friday 22:00 = f + 22 for Friday f, 50 held buckets)
        sham = set(range(e, min(e + H, len(rows))))
        for f in friday_starts:
            anchor = set(range(f + 22, min(f + 22 + H, len(rows))))
            assert not (sham & anchor)
    # every placed entry starts Monday 00:00 .. Wednesday 20:00 (the
    # complementary arc) and is short-only
    for e in entries:
        wd = datetime.strptime(rows[e]["day_utc"], "%Y-%m-%d").weekday()
        hour = int(rows[e]["hour_utc"][11:13])
        assert (wd, hour) >= (0, 0) and (wd, hour) <= (2, 20)
    assert all(control[i] == -1.0 for i in _flag_index(control))


def test_sham_refuses_nonfrozen_seed():
    panels = _panels(24)
    with pytest.raises(ValueError, match="17040001"):
        reg.resolve("WKNDLIQ.control")(
            panels, {**CONTROL_PARAMS, "seed": 17040002}
        )


# ------------------------------------------------------------------------- #
# (d) frozen rule 4 enforcement: fewer than 12 scored weekend events in any
#     single fold kills the family -- fail-closed in the driver path
# ------------------------------------------------------------------------- #
def test_rule4_enforcement_dead_on_sparse_calendar(tmp_path, monkeypatch):
    """30-day fixture, hand-computed coverage: fold edges [0,10,20,30],
    purged {9,10,19,20}, folds F0=0..8 / F1=11..18 / F2=21..29.  Anchor
    weekends: Friday 0 (inside F0), Friday 14 (inside F1), Friday 21
    (inside F2); Fridays 7 (purge), 28 (off-grid) refused.  Every fold
    scores 2 pooled weekend events << 12 => the family is MARKED DEAD in
    the cell record."""
    _, (spec,) = d.load_selection(SPEC_PATH)
    manifest = _stage(tmp_path, spec, n_days=30)
    monkeypatch.setattr(d, "PANEL_DIR", manifest["_panel_dir"])
    out = tmp_path / "out"
    result = d.run_family(
        spec, manifest, d.repo_root(), out,
        sanitized=False, base_dir=tmp_path, code_freeze_sha="0" * 40,
    )
    enf = result["frozen_rule_enforcement"]  # MUST exist: fail-closed
    assert enf["rule_id"] == "weekend_event_coverage"
    assert enf["book"] == "anchor" and enf["tier"] == "T2.0"
    assert enf["min_scored_events_per_fold"] == 12
    assert enf["per_fold_scored_events"] == {"F0": 2, "F1": 2, "F2": 2}
    assert enf["min_fold_scored_events"] == 2
    assert enf["verdict"] == "DEAD_FROZEN_RULE_COVERAGE"
    assert enf["family_alive"] is False
    assert enf["fail_closed"] is True
    # the pre-registered death is a legal REJECT path: the cell still
    # emitted its diagnostics (non-vacuous) but the verdict is owned
    assert result["arms"]["anchor"]["kernel"]["n_round_trips"] > 0


def test_rule4_enforcement_pass_on_rich_calendar(tmp_path, monkeypatch):
    """180-day fixture: ~8 booked weekends per fold x 2 symbols = 16 >= 12
    in every fold -> the enforcement PASSES the family alive."""
    _, (spec,) = d.load_selection(SPEC_PATH)
    manifest = _stage(tmp_path, spec, n_days=180)
    monkeypatch.setattr(d, "PANEL_DIR", manifest["_panel_dir"])
    h1 = d.load_panels(d.repo_root(), manifest, spec.universe)
    state = d.compute_family(spec, h1, base_dir=tmp_path, allow_example=False)
    enf = d.enforce_frozen_coverage_rule(spec, state)
    assert enf["verdict"] == "PASS"
    assert enf["family_alive"] is True
    assert all(v >= 12 for v in enf["per_fold_scored_events"].values())
    assert set(enf["per_fold_scored_events"]) == {"F0", "F1", "F2"}


def test_rule4_malformed_block_refused_at_load():
    base = {
        "family_id": "SYNTH-WKND-RULES", "clock": "H1",
        "universe": ["BTCUSDT"],
        "entry": {"lag_buckets": 1}, "exit": {"holding_buckets": 1},
        "arms": [
            {"arm_id": "a", "kind": "anchor",
             "exposure": {"type": "panel_formula",
                          "formula_id": "WKNDLIQ.anchor", "params": {}}},
            {"arm_id": "b", "kind": "neighbour",
             "exposure": {"type": "panel_formula",
                          "formula_id": "WKNDLIQ.neighbour", "params": {}}},
            {"arm_id": "c", "kind": "control",
             "exposure": {"type": "panel_formula",
                          "formula_id": "WKNDLIQ.control", "params": {}}},
        ],
    }

    def rules(**over):
        rule = {
            "min_scored_events_per_fold": 12,
            "book": "anchor",
            "tier": "T2.0",
            "action": "mark_dead",
        }
        rule.update(over)
        return {"weekend_event_coverage": rule}

    ok = copy.deepcopy(base)
    ok["frozen_falsification_rules"] = rules()
    spec = d._parse_family(ok, base_dir=Path("/"))
    assert spec.frozen_rules["weekend_event_coverage"][
        "min_scored_events_per_fold"
    ] == 12
    bad_cases = [
        rules(min_scored_events_per_fold=0),
        rules(min_scored_events_per_fold=12.0),
        rules(book="control"),
        rules(tier="T9.9"),
        rules(action="warn"),
        {"some_other_rule": {}},
    ]
    for bad in bad_cases:
        doc = copy.deepcopy(base)
        doc["frozen_falsification_rules"] = bad
        with pytest.raises(d.DriverError):
            d._parse_family(doc, base_dir=Path("/"))


def test_rule4_enforcement_refuses_unevaluable_anchor(tmp_path):
    """Fail-closed: an enforcement request without an anchor book is a hard
    refusal (never a silent pass)."""
    _, (spec,) = d.load_selection(SPEC_PATH)
    with pytest.raises(d.DriverError, match="fail closed|anchor book"):
        d.enforce_frozen_coverage_rule(spec, {"arms": {}})


def test_no_frozen_rules_no_enforcement_field(tmp_path, monkeypatch):
    """The enforcement is opt-in per spec: a family whose spec declares no
    frozen_falsification_rules block runs the legacy path (no field), so
    the SILRES/ATTN-PHASE lanes are untouched."""
    base = {
        "family_id": "SYNTH-NORULES", "clock": "H1",
        "universe": ["BTCUSDT", "ETHUSDT"],
        "entry": {"lag_buckets": 0}, "exit": {"holding_buckets": 2},
        "fill_price": "vwap",
        "arms": [
            {"arm_id": "a", "kind": "anchor",
             "exposure": {"type": "panel_formula",
                          "formula_id": "WKNDTEST.h1_first_bucket_long",
                          "params": {}}},
            {"arm_id": "b", "kind": "neighbour",
             "exposure": {"type": "panel_formula",
                          "formula_id": "WKNDTEST.h1_first_bucket_long",
                          "params": {}}},
            {"arm_id": "c", "kind": "control",
             "exposure": {"type": "panel_formula",
                          "formula_id": "WKNDTEST.h1_first_bucket_long",
                          "params": {}}},
        ],
    }
    doc = {"cycle_id": "CRYPTO-V17", "families": [base]}
    sel = tmp_path / "sel.json"
    sel.write_text(json.dumps(doc), encoding="utf-8")
    _, (spec,) = d.load_selection(sel)
    assert spec.frozen_rules is None
    manifest = _stage(tmp_path, spec, n_days=10)
    monkeypatch.setattr(d, "PANEL_DIR", manifest["_panel_dir"])
    result = d.run_family(
        spec, manifest, d.repo_root(), tmp_path / "o",
        sanitized=False, base_dir=tmp_path, code_freeze_sha="0" * 40,
    )
    assert "frozen_rule_enforcement" not in result


# ------------------------------------------------------------------------- #
# (e) availability law: the trigger consumes NO bucket-close observable
# ------------------------------------------------------------------------- #
def test_availability_calendar_only():
    """WKNDLIQ is a pure calendar flag: perturbing EVERY price/flow column
    of every row must leave all three series byte-identical -- there is no
    forward lookup because there is no price input at all; and the value
    at index i is a function of row i's own (day_utc, hour_utc) only."""
    n_days = 30
    panels = _panels(n_days)
    tampered = copy.deepcopy(panels)
    for sym, rows in tampered.items():
        for j, row in enumerate(rows):
            row["vwap"] = row["vwap"] * 1.7 + 11.0
            row["first_price"] = row["first_price"] * 0.3 + 5.0
            row["last_price"] = row["last_price"] * 2.2 + 1.0
            row["n_trades"] = row["n_trades"] * 13 + 7
            row["entry_gap_s"] = row["entry_gap_s"] * 3.3 + 1.0
    for fid, params in (
        ("WKNDLIQ.anchor", ANCHOR_PARAMS),
        ("WKNDLIQ.neighbour", NEIGHBOUR_PARAMS),
        ("WKNDLIQ.control", CONTROL_PARAMS),
    ):
        s1 = reg.resolve(fid)(panels, params)
        s2 = reg.resolve(fid)(tampered, params)
        assert s1 == s2
    # and the flag at index i moves ONLY with row i's own calendar:
    # relabelling one row's weekday moves at most that one index
    relabelled = copy.deepcopy(panels)
    rows = relabelled["BTCUSDT"]
    target = next(
        i
        for i, r in enumerate(rows)
        if datetime.strptime(r["day_utc"], "%Y-%m-%d").weekday() == 4
        and r["hour_utc"].endswith("T21")
    )
    rows[target]["day_utc"] = _day((target // 24) + 1)  # a Saturday label
    rows[target]["hour_utc"] = rows[target]["day_utc"] + "T21"
    s_orig = reg.resolve("WKNDLIQ.anchor")(panels, ANCHOR_PARAMS)["BTCUSDT"]
    s_new = reg.resolve("WKNDLIQ.anchor")(
        relabelled, ANCHOR_PARAMS
    )["BTCUSDT"]
    diffs = [i for i in range(len(s_orig)) if s_orig[i] != s_new[i]]
    assert diffs == [target]


# ------------------------------------------------------------------------- #
# (f) frozen spec + diag contract load through the driver/governance paths
# ------------------------------------------------------------------------- #
def test_spec_loads_through_driver_schema():
    cycle, (spec,) = d.load_selection(SPEC_PATH)
    assert cycle == "CRYPTO-V17"
    assert (spec.family_id, spec.clock, spec.universe) == (
        "V17-A4-P1-WKNDLIQ", "H1", ("BTCUSDT", "ETHUSDT"))
    # frozen fills/holding: decision at the Friday 21:00 close, lag-0 fill
    # at the position bucket's published vwap (= the Friday 22:00 vwap),
    # cover Monday 00:00 => 50 held H1 buckets
    assert (spec.lag_buckets, spec.holding_buckets, spec.fill_price) == (
        0, 50, "vwap")
    assert spec.booking == "event"
    by_kind = {arm.kind: arm for arm in spec.arms}
    assert {arm.arm_id for arm in spec.arms} == {"anchor", "neighbour", "control"}
    assert by_kind["anchor"].exposure["formula_id"] == "WKNDLIQ.anchor"
    assert by_kind["anchor"].exposure["params"] == ANCHOR_PARAMS
    assert by_kind["anchor"].holding_override is None
    # neighbour: frozen window Friday 20:00 -> Monday 02:00 => override 54
    assert by_kind["neighbour"].exposure["formula_id"] == "WKNDLIQ.neighbour"
    assert by_kind["neighbour"].exposure["params"] == NEIGHBOUR_PARAMS
    assert by_kind["neighbour"].holding_override == 54
    # control: the frozen sham (seed verbatim, duration-matched)
    assert by_kind["control"].exposure["formula_id"] == "WKNDLIQ.control"
    assert by_kind["control"].exposure["params"] == CONTROL_PARAMS
    assert by_kind["control"].holding_override is None  # inherits K=50
    # all three formulas resolve and are SCORED (never example-only)
    for arm in spec.arms:
        assert callable(reg.resolve(arm.exposure["formula_id"]))
        assert not reg.is_example_only(arm.exposure["formula_id"])
    # the FROZEN RULE-4 block rides the spec and parses fail-closed
    rule = spec.frozen_rules["weekend_event_coverage"]
    assert rule["min_scored_events_per_fold"] == 12
    assert rule["book"] == "anchor" and rule["tier"] == "T2.0"
    assert rule["action"] == "mark_dead"
    assert "falsification_rule (4)" in rule["rule"]
    # the control's duration param matches the family holding (equal-length
    # sham windows) -- a spec/driver consistency pin
    assert by_kind["control"].exposure["params"]["holding_buckets"] == 50
    assert spec.holding_buckets == 50
    # the sham-calendar descriptor matches the diag contract's marker
    doc = json.loads(CONTRACT_PATH.read_text())
    assert (
        spec.sham_calendar["calendar"]
        == doc["concretization"]["sham_row_marker"]
        == "SHAM_WEEKEND_OFFSET:default_rng(17040001)_one_draw_per_week_no_anchor_overlap"
    )


def test_spec_end_to_end_scored_sanitized_and_enforced(tmp_path, monkeypatch):
    _, (spec,) = d.load_selection(SPEC_PATH)
    manifest = _stage(tmp_path, spec, n_days=24)
    monkeypatch.setattr(d, "PANEL_DIR", manifest["_panel_dir"])
    out = tmp_path / "out"
    result = d.run_family(
        spec, manifest, d.repo_root(), out,
        sanitized=False, base_dir=tmp_path, code_freeze_sha="0" * 40,
    )
    for arm_id in ("anchor", "neighbour", "control"):
        res = result["arms"][arm_id]
        assert res["kernel"]["n_round_trips"] > 0
        assert res["kernel"]["remediated_kernel"] is True
        assert res["kernel"]["cost_holding_terms"] == 0.0
    arm_dir = out / "results/v17/V17-A4-P1-WKNDLIQ/anchor"
    assert {p.name for p in arm_dir.iterdir()} == (
        SCORED_CATEGORIES | {"sham_control_calendar.jsonl"})
    # the calendar_conditioned family emits its sham rows on every arm
    for arm_id in ("anchor", "neighbour", "control"):
        sham = [
            json.loads(ln)
            for ln in (
                out / f"results/v17/V17-A4-P1-WKNDLIQ/{arm_id}"
                / "sham_control_calendar.jsonl"
            ).read_text().splitlines()
            if ln.strip()
        ]
        assert sham == [{
            "cycle_id": "CRYPTO-V17",
            "arm_id": arm_id,
            "calendar": spec.sham_calendar["calendar"],
            "note": spec.sham_calendar["note"],
        }]
    # margins carry arm identity (P-3 attribution)
    for arm_id in ("anchor", "neighbour", "control"):
        margins = [
            json.loads(ln)
            for ln in (
                out / f"results/v17/V17-A4-P1-WKNDLIQ/{arm_id}"
                / "margins_to_fail.jsonl"
            ).read_text().splitlines()
            if ln.strip()
        ]
        assert [m["gate_id"] for m in margins] == [
            "G1", "G2", "G3", "G4", "G5"]
        assert all(m["arm_id"] == arm_id for m in margins)
    dsr = out / "results/v17/V17-A4-P1-WKNDLIQ/dsr_per_period_series.jsonl"
    assert dsr.exists()
    # the 24-day fixture is sparse: the frozen rule 4 fires and the cell
    # record owns the verdict (hand-computed per-fold counts)
    enf = result["frozen_rule_enforcement"]
    assert enf["verdict"] == "DEAD_FROZEN_RULE_COVERAGE"
    assert enf["per_fold_scored_events"] == {"F0": 2, "F1": 0, "F2": 0}
    assert enf["family_alive"] is False
    # control trips are duration-matched to the anchor (50 buckets) and the
    # neighbour books its 54-bucket window
    state = d.compute_family(
        spec, d.load_panels(d.repo_root(), manifest, spec.universe),
        base_dir=tmp_path, allow_example=False,
    )
    for trip in state["arms"]["anchor"]["trips"]:
        assert trip["exit_bucket"] - trip["entry_bucket"] == 50
    for trip in state["arms"]["neighbour"]["trips"]:
        assert trip["exit_bucket"] - trip["entry_bucket"] == 54
    for trip in state["arms"]["control"]["trips"]:
        assert trip["exit_bucket"] - trip["entry_bucket"] == 50
    # sanitized dry-run: decisions only, non-vacuous, no outcome fields
    san = tmp_path / "san"
    summary = d.run_family(
        spec, manifest, d.repo_root(), san,
        sanitized=True, base_dir=tmp_path, code_freeze_sha="0" * 40,
    )
    assert sum(summary["decisions"].values()) > 0
    for arm_id in ("anchor", "neighbour", "control"):
        recs = [
            json.loads(ln)
            for ln in (
                san / f"research/control/v17_run/q_dry_run/V17-A4-P1-WKNDLIQ"
                f"/{arm_id}/decisions.jsonl"
            ).read_text().splitlines()
            if ln.strip()
        ]
        assert recs and all(
            set(r) == {"cycle_id", "family_id", "arm_id", "date", "hour",
                       "decision_taken", "symbol"}
            for r in recs
        )
    # determinism: two scored runs are byte-identical
    out2 = tmp_path / "out2"
    d.run_family(
        spec, manifest, d.repo_root(), out2,
        sanitized=False, base_dir=tmp_path, code_freeze_sha="0" * 40,
    )
    for rel in ("anchor", "neighbour", "control"):
        for name in {p.name for p in arm_dir.iterdir()}:
            a = out / "results/v17/V17-A4-P1-WKNDLIQ" / rel / name
            b = out2 / "results/v17/V17-A4-P1-WKNDLIQ" / rel / name
            assert a.read_bytes() == b.read_bytes()


def test_diag_contract_passes_persistability_gate():
    doc = json.loads(CONTRACT_PATH.read_text())
    contract = doc["contract"]
    assert contract["cycle_id"] == "CRYPTO-V17"
    assert contract["calendar_conditioned"] is True
    verdict, findings = validate_contract(contract)
    assert verdict == "DIAGNOSTIC_CONTRACT_PASS"
    assert not [f for f in findings if f["severity"] == "HIGH"]
    # the recorded verdict block matches a fresh run of the gate
    assert doc["validate_contract"]["verdict"] == verdict
    assert doc["validate_contract"]["high_findings"] == 0
    assert doc["validate_contract"]["findings"] == findings
    # the artifact list derives from the contract and carries the canon
    artifacts, problems = expected_artifacts_from_contract(contract)
    assert not problems
    categories = {a["category"] for a in artifacts}
    assert "sham_control_calendar" in categories
    assert "dsr_per_period_series" in categories
    for a in artifacts:
        if a["category"] == "sham_control_calendar":
            assert a["required_fields"] == list(
                CONDITIONAL_REQUIRED_FIELDS["sham_control_calendar"])
            assert a["artifact"].startswith(
                "results/v17/V17-A4-P1-WKNDLIQ/")
    # the driver's canon mirrors the governance canon for the conditional
    assert set(d.CANON_FIELDS["sham_control_calendar"]) == set(
        CONDITIONAL_REQUIRED_FIELDS["sham_control_calendar"])


# ------------------------------------------------------------------------- #
# helpers: synthetic staging through the REAL loader path (csv + sha manifest)
# ------------------------------------------------------------------------- #
SCORED_CATEGORIES = {
    "identity.jsonl", "per_period_series.jsonl", "per_symbol_breakdown.jsonl",
    "per_fold_breakdown.jsonl", "stress_tiers.jsonl", "drop_one_inputs.jsonl",
    "benchmark_context.jsonl", "margins_to_fail.jsonl", "counters.jsonl",
    "reproduction_inputs.jsonl",
}


def _write_wknd_csv(directory: Path, symbol: str, n_days: int) -> None:
    path = directory / d.PANEL_FILE.format(symbol=symbol)
    lines = [",".join(d.H1_SCHEMA)]
    for idx in range(n_days * 24):
        day, hour = idx // 24, idx % 24
        base = 100.0 + 0.01 * idx
        vwap = base * 1.0001
        row = {
            "symbol": symbol, "hour_utc": f"{_day(day)}T{hour:02d}",
            "day_utc": _day(day), "n_trades": 10, "buy_count": 5,
            "sell_count": 5, "buy_qty": 10.0, "sell_qty": 10.0,
            "buy_quote": 10.0 * vwap, "sell_quote": 10.0 * vwap,
            "quote_total": 20.0 * vwap, "qty_total": 20.0, "vwap": vwap,
            "first_price": base, "last_price": base * 1.001,
            "high_price": base * 1.002, "low_price": base * 0.999,
            "max_trade_quote": 5.0, "sum_qty_squared": 400.0,
            "n_price_moves": 60, "sum_squared_log_ret": 0.001,
            "gap_sum_s": 2.5, "gap_count": 10, "entry_gap_s": 0.3,
            "run_close_dir": "buy", "run_close_len": 3,
            "run_switch_count": 2, "max_run_buy": 5, "max_run_sell": 4,
            "first_ts_ms": 1_724_000_000_000 + idx * 3_600_000,
            "last_ts_ms": 1_724_000_063_000 + idx * 3_600_000,
        }
        lines.append(",".join(
            repr(row[c]) if isinstance(row[c], float) else str(row[c])
            for c in d.H1_SCHEMA
        ))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _stage(tmp_path: Path, spec: d.FamilySpec, n_days: int) -> dict:
    panel_dir = tmp_path / "staging"
    for sym in spec.universe:
        _write_wknd_csv(panel_dir, sym, n_days)
    doc = {
        "schema": "v17_run_artifact_v1",
        "artifact": "staging_panel_manifest",
        "symbols": list(spec.universe),
        "window": [_day(0), _day(n_days - 1)],
        "panel_sha256": {
            sym: d.sha256_bytes(
                (panel_dir / d.PANEL_FILE.format(symbol=sym)).read_bytes()
            )
            for sym in spec.universe
        },
        "hourly_rows": {sym: n_days * 24 for sym in spec.universe},
    }
    (panel_dir / "panel_manifest_v17_published.json").write_text(
        json.dumps(doc, sort_keys=True, indent=1), encoding="utf-8")
    manifest = d.load_manifest(
        panel_dir / "panel_manifest_v17_published.json")
    manifest["_panel_dir"] = panel_dir
    return manifest
