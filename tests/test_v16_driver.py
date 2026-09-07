"""CRYPTO-V16 I/A8 -- synthetic hand-computed fixtures for the scored driver.

Every expected value below is computed BY HAND and asserted.  All data is
SYNTHETIC (small fake panels, never the real staging files); nothing is
scored against real data here, no network, no wall clock.

Synthetic world (default fixture, N=130 days from 2025-08-22):
    last_price alternates 100.0 / 101.0 (so daily returns alternate
    +0.01 / -0.01 and ret_z never degenerates);
    vwap = last - 4, high = last + 5, low = last - 5
        -> disp[t] = (last - vwap) / (high - low) = 4 / 10 = 0.4 EXACTLY
           on every row (a boundary case: |disp| EQUALS its own 60-day
           quantile, and >= fires);
    buy_streak_max = 5, sell_streak_max = 3
        -> run_imb[t] = (5-3)/(5+3) = 0.25 on every row.

Hand world costs (frozen kernel, T1.0): fee 5 bps -> 5e-4 per unit
notional; tick 0.01; entry fill 100.0 -> slip 1e-4; entry rate 6e-4.

Fixture map:
* (a)  test_golden_features_disp_run_imb_ret_z
* (b)  test_golden_trigger_quantile_and_side
* (c)  test_one_bar_lag_future_rows_cannot_change_decisions
* (d)  test_fold_force_flat_and_fold_labels_match_frozen_semantics
* (e)  test_cost_once_round_trip_two_fills_holding_terms_zero
* (f)  test_control_book_differs_from_anchor_book
* (g)  test_deterministic_double_run_byte_identical
* (h)  test_malformed_panel_row_fails_closed
* (i)  test_sanitized_leak_scan_recursive_and_nonvacuous
* (j)  test_sanitized_zero_decisions_is_hard_failure
* (k)  test_scored_records_carry_exactly_canon_fields
* (l)  test_arm_config_digest_is_sha256_of_frozen_spec_text
* (m)  test_frozen_diagnostic_contracts_validate
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List

import pytest

from research.control.v16_run.driver import run_v16_cell as drv
from research.governance.diagnostic_persistability import (
    PASS,
    validate_contract,
)

REPO = drv.repo_root()
VENV_DATE = date(2025, 8, 22)


# --------------------------------------------------------------------------- #
# Synthetic panel builders
# --------------------------------------------------------------------------- #
def _iso(i: int) -> str:
    return (VENV_DATE + timedelta(days=i)).isoformat()


def make_rows(
    n: int = 130,
    disp_seq=None,
) -> List[dict]:
    """The hand world: disp = 0.4 and run_imb = 0.25 on every row unless a
    custom per-index disp sequence is supplied (``disp_seq(i) -> d`` gives
    disp via vwap = last - d with high-low = 10)."""
    rows: List[dict] = []
    for i in range(n):
        last = 100.0 + float(i % 2)  # alternating 100.0 / 101.0
        d = 4.0 if disp_seq is None else disp_seq(i)
        rows.append(
            {
                "date": VENV_DATE + timedelta(days=i),
                "iso": _iso(i),
                "vwap": last - d,
                "last_price": last,
                "high_price": last + 5.0,
                "low_price": last - 5.0,
                "buy_streak_max": 5,
                "sell_streak_max": 3,
            }
        )
    return rows


def default_panels(n: int = 130) -> Dict[str, List[dict]]:
    return {sym: make_rows(n=n) for sym in drv.UNIVERSE}


def freeze_fixture() -> dict:
    return drv.load_freeze(REPO)


# --------------------------------------------------------------------------- #
# (a) golden features
# --------------------------------------------------------------------------- #
def test_golden_features_disp_run_imb_ret_z():
    rows = make_rows(n=70)
    feats = drv.build_features(rows)
    # disp[0] = (100 - 96) / (105 - 95) = 0.4 exactly (hand)
    assert feats["disp"][0] == pytest.approx(0.4, abs=1e-15)
    assert feats["disp"][1] == pytest.approx(0.4, abs=1e-15)
    # run_imb = (5 - 3) / (5 + 3) = 0.25 (hand)
    assert feats["run_imb"][0] == pytest.approx(0.25, abs=1e-15)
    # ret_z[60]: the honest warmup.  Rows 0..59 alternate 100/101 except the
    # window ret[1..60]: 30 x (+0.01) + 29 x (-0.01) + ret[60].
    p = [r["last_price"] for r in rows]
    assert p[0] == 100.0 and p[1] == 101.0
    ret60 = p[60] / p[59] - 1.0
    window = [p[i] / p[i - 1] - 1.0 for i in range(1, 61)]
    mean = sum(window) / 60.0
    var = sum((x - mean) ** 2 for x in window) / 60.0  # population std, ddof=0
    expected = ret60 / (var ** 0.5)
    assert feats["ret_z"][60] == pytest.approx(expected, abs=1e-12)
    assert feats["ret_z"][59] is None  # honest warmup: undefined before row 60


def test_golden_disp_custom_sequence_hand_exact():
    # disp_seq(i) = 0.5 - 0.001*i  ->  strictly decreasing, hand-checkable
    rows = make_rows(n=8, disp_seq=lambda i: 0.5 - 0.001 * i)
    feats = drv.build_features(rows)
    for i in range(8):
        assert feats["disp"][i] == pytest.approx((0.5 - 0.001 * i) / 10.0, abs=1e-15)


# --------------------------------------------------------------------------- #
# (b) golden trigger: quantile + side, hand-computed on a tiny window
# --------------------------------------------------------------------------- #
def test_golden_trigger_quantile_and_side():
    # window W=4, q80 over |[1,2,3,4]|: numpy linear -> index 0.8*3 = 2.4
    # -> 3 + 0.4*(4-3) = 3.4 (hand).
    feats = {"s": [1.0, 2.0, -3.0, 4.0, 10.0, -3.0]}
    arm = drv.ArmSpec(
        family_id="CLOSE-DISPLACE-FADE", role="anchor", spec_text="x",
        arm_config_digest="0", series="s", window=4, quantile=80.0, side=-1,
    )
    positions, eligible = drv.compute_arm_positions(arm, {"BTCUSDT": feats, "ETHUSDT": feats}, 6)
    # t=4: |s[3]| = 4 >= p80(|[1,2,3,4]|) = 3.4 -> pos = -sign(4) = -1 (FADE)
    assert positions["BTCUSDT"][4] == -1
    # t=5: |s[4]| = 10 >= p80(|[2,3,4,10]|) = 4 + 0.4*(10-4) = 6.4 -> pos = -1
    assert positions["BTCUSDT"][5] == -1
    assert eligible == [4, 5]
    # continuation side (+1) mirrors the same triggers (RUNPERSIST family)
    arm_cont = drv.ArmSpec(
        family_id="RUNPERSIST", role="anchor", spec_text="x",
        arm_config_digest="0", series="s", window=4, quantile=80.0, side=1,
    )
    positions_c, _ = drv.compute_arm_positions(arm_cont, {"BTCUSDT": feats, "ETHUSDT": feats}, 6)
    assert positions_c["BTCUSDT"][4] == 1 and positions_c["BTCUSDT"][5] == 1
    # below-threshold day does not fire: |s[5]| = 3 < p80(|[-3,4,10,-3]|)
    # sorted |[3,3,4,10]| index 2.4 -> 4 + 0.4*6 = 6.4 -> no t=6 day (n=6)
    assert 6 not in positions_c["BTCUSDT"]


# --------------------------------------------------------------------------- #
# (c) one-bar lag
# --------------------------------------------------------------------------- #
def test_one_bar_lag_future_rows_cannot_change_decisions():
    panels = default_panels(n=130)
    freeze = freeze_fixture()
    base = drv.compute_family(freeze, panels, "CLOSE-DISPLACE-FADE")
    # perturb EVERY row after day 64 (prices, vwap, range, streaks)
    perturbed = {sym: [dict(r) for r in rows] for sym, rows in panels.items()}
    for sym, rows in perturbed.items():
        for i in range(65, len(rows)):
            rows[i]["last_price"] *= 1.10
            rows[i]["vwap"] *= 1.05
            rows[i]["high_price"] *= 1.20
            rows[i]["low_price"] *= 0.80
            rows[i]["buy_streak_max"] = 9
            rows[i]["sell_streak_max"] = 1
    after = drv.compute_family(freeze, perturbed, "CLOSE-DISPLACE-FADE")
    for role in drv.ARM_ROLES:
        for sym in drv.UNIVERSE:
            before_pos = {
                t: p for t, p in base["positions"][role][sym].items() if t <= 65
            }
            after_pos = {
                t: p for t, p in after["positions"][role][sym].items() if t <= 65
            }
            assert before_pos == after_pos, (role, sym)
        # booked round trips decided at days <= 64 are untouched as well
        bt = [t for t in base["books"][role]["T1.0"].round_trips if t["decision_day"] <= 64]
        at = [t for t in after["books"][role]["T1.0"].round_trips if t["decision_day"] <= 64]
        assert bt == at, role


# --------------------------------------------------------------------------- #
# (d) fold force-flat + frozen fold semantics
# --------------------------------------------------------------------------- #
def test_fold_force_flat_and_fold_labels_match_frozen_semantics():
    from research.hyp_a8_m01 import chronological_folds

    # exact chronological_folds semantics (F0/F1/F2 labels): thirds + 1 purge
    mine = drv.build_folds(list(range(10)))
    theirs = chronological_folds(list(range(10)), purge_days=1)
    assert [f.label for f in mine] == ["F0", "F1", "F2"]
    assert [list(f.members) for f in mine] == [list(m) for _, _, m in theirs]
    assert [list(f.members) for f in mine] == [[0, 1], [3, 4, 5], [7, 8]]

    panels = default_panels(n=130)
    freeze = freeze_fixture()
    state = drv.compute_family(freeze, panels, "CLOSE-DISPLACE-FADE")
    for role in drv.ARM_ROLES:
        folds = state["folds"][role]
        for tier in drv.STRESS_TIERS:
            book = drv.simulate_book(state["positions"][role], folds, state["prices"], tier)
            for trip in book.round_trips:
                fold = next(f for f in folds if f.label == trip["fold_label"])
                if fold.index + 1 < len(folds):
                    nxt = folds[fold.index + 1].members[0]
                    assert trip["exit_day"] < nxt, (role, tier, trip)
                assert trip["exit_day"] <= 129
        # with a trigger on EVERY eligible day, the delay tier must force-flat
        # the last decision day of every fold (never booked, never carried)
        base = drv.simulate_book(
            state["positions"][role], folds, state["prices"], "T1.0"
        )
        delayed = drv.simulate_book(
            state["positions"][role], folds, state["prices"], "T2.0"
        )
        last_members = {f.members[-1] for f in folds}
        for trip in delayed.round_trips:
            assert trip["decision_day"] not in last_members, (role, trip)


# --------------------------------------------------------------------------- #
# (e) cost-once (L-V14-0)
# --------------------------------------------------------------------------- #
def test_cost_once_round_trip_two_fills_holding_terms_zero():
    from fractions import Fraction as F

    # one single round trip: BTCUSDT decided at day 60, entry fill at
    # last_price[60] = 100.0, exit at last_price[61] = 101.0 (hand world).
    positions = {"BTCUSDT": {60: -1}, "ETHUSDT": {}}
    prices = {
        "BTCUSDT": [100.0 if i % 2 == 0 else 101.0 for i in range(70)],
        "ETHUSDT": [100.0] * 70,
    }
    # 8 eligible days -> thirds + 1 purge: F0=[60,61], F1=[63], F2=[65,66].
    # Day 60 is an F0 member; base exit 61 and delayed exit 62 both precede
    # the next fold's first member 63 (force-flat holds in both tiers).
    folds = drv.build_folds(list(range(60, 68)))
    book = drv.simulate_book(positions, folds, prices, "T1.0")
    assert book.n_fills == 2  # a round trip is EXACTLY two fills
    assert book.n_round_trips == 1
    # hand: gross = -1 * (101/100 - 1) = -0.01 (short fades the +1% day)
    # entry cost = 6e-4 (fee 5e-4 + slip 0.01/100 = 1e-4)
    # exit cost  = 5e-4 + 0.01/101
    gross = F(-1) * (F(101, 100) - 1)
    cost_entry = F(5, 10000) + F(1, 100) * F(1, 100)
    cost_exit = F(5, 10000) + F(1, 100) / F(101)
    expected_net = gross - cost_entry - cost_exit
    # the driver records money at 12 decimals (adapter convention), so the
    # hand-exact fraction may differ by at most half an ulp of that rounding
    assert abs(book.pnl - float(expected_net)) < 5e-13
    assert abs(book.gross_pnl - (-0.01)) < 5e-13
    assert abs(book.cost_fills_total - float(cost_entry + cost_exit)) < 5e-13
    # holding terms are EXACTLY zero on every fill record and in total
    assert book.cost_holding_terms_total == 0.0
    for fill in book.fills:
        assert fill.cost_holding_terms == 0.0
        assert fill.cost_fills > 0.0
    # holding longer would change NOTHING: same single round trip, the exit
    # is the only second fill (no per-holding-day charge can exist)
    assert len({f.day for f in book.fills}) == 2
    # a delayed tier books the same round trip with its own two fills only
    delayed = drv.simulate_book(positions, folds, prices, "T2.0")
    assert delayed.n_fills == 2
    assert delayed.cost_holding_terms_total == 0.0


# --------------------------------------------------------------------------- #
# (f) control differs from anchor
# --------------------------------------------------------------------------- #
def test_control_book_differs_from_anchor_book():
    panels = default_panels(n=130)
    freeze = freeze_fixture()
    state = drv.compute_family(freeze, panels, "CLOSE-DISPLACE-FADE")
    anchor = state["books"]["anchor"]["T1.0"]
    control = state["books"]["control"]["T1.0"]
    anchor_rt = {(t["symbol"], t["decision_day"], t["position"]) for t in anchor.round_trips}
    control_rt = {(t["symbol"], t["decision_day"], t["position"]) for t in control.round_trips}
    assert anchor_rt != control_rt
    # the hand world: the anchor FADES on every eligible day (disp == 0.4
    # equals its own quantile and >= fires) at position -1 for both symbols;
    # the ret_z control cannot reproduce that - its eligible surface starts
    # 60 days later and it fires only on alternating days.
    assert {p for _, _, p in anchor_rt} == {-1}
    # per symbol at most (purged days + the off-panel last day + fold edges)
    # eligible days can be force-flattened, never more
    assert len(anchor_rt) >= 2 * (len(state["eligible"]["anchor"]) - 4)
    assert len(control_rt) < len(anchor_rt)
    assert state["eligible"]["control"][0] == state["eligible"]["anchor"][0] + 60


# --------------------------------------------------------------------------- #
# (g) deterministic double-run, byte-identical
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("family", list(drv.FAMILIES))
def test_deterministic_double_run_byte_identical(family, tmp_path):
    panels = default_panels(n=130)
    freeze = freeze_fixture()
    manifest = drv.load_manifest(REPO)
    roots = []
    for run in ("run1", "run2"):
        out = tmp_path / run
        out.mkdir()
        drv.emit_scored(freeze, manifest, panels, family, "anchor", out)
        drv.emit_sanitized(freeze, panels, family, "anchor", out)
        roots.append(out)
    files1 = sorted(p.relative_to(roots[0]) for p in roots[0].rglob("*") if p.is_file())
    files2 = sorted(p.relative_to(roots[1]) for p in roots[1].rglob("*") if p.is_file())
    assert files1 == files2 and len(files1) >= 11
    for rel in files1:
        b1 = (roots[0] / rel).read_bytes()
        b2 = (roots[1] / rel).read_bytes()
        assert b1 == b2, rel
        assert b1.endswith(b"\n")


# --------------------------------------------------------------------------- #
# (h) malformed panel fails closed
# --------------------------------------------------------------------------- #
def _write_csv(path: Path, rows: List[dict]) -> None:
    cols = ["symbol", "date", "vwap", "last_price", "high_price", "low_price",
            "buy_streak_max", "sell_streak_max"]
    lines = [",".join(cols)]
    for r in rows:
        lines.append(",".join(
            ["BTCUSDT", r["iso"], str(r["vwap"]), str(r["last_price"]),
             str(r["high_price"]), str(r["low_price"]),
             str(r["buy_streak_max"]), str(r["sell_streak_max"])]
        ))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


@pytest.mark.parametrize(
    "mutate,fragment",
    [
        (lambda rows: rows[5].update({"vwap": "not-a-float"}), "not a float"),
        (lambda rows: rows[5].update({"last_price": float("nan")}), "not finite"),
        (lambda rows: rows[5].update({"high_price": 1.0, "low_price": 2.0}), "high < low"),
        (lambda rows: rows[5].update({"buy_streak_max": -1}), "negative streak"),
    ],
)
def test_malformed_panel_row_fails_closed(tmp_path, mutate, fragment):
    rows = make_rows(n=10)
    mutate(rows)
    target = tmp_path / "v16_data" / "staging_v16"
    target.mkdir(parents=True)
    _write_csv(target / "panel_BTCUSDT_daily.csv", rows)
    with pytest.raises(drv.DriverError, match=fragment):
        drv.load_panel(tmp_path, "BTCUSDT")


def test_malformed_panel_symbol_and_date_fails_closed(tmp_path):
    rows = make_rows(n=10)
    target = tmp_path / "v16_data" / "staging_v16"
    target.mkdir(parents=True)
    panel = target / "panel_BTCUSDT_daily.csv"
    _write_csv(panel, rows)
    text = panel.read_text()
    # a wrong-symbol row inside the BTCUSDT panel
    bad = text.replace("BTCUSDT,2025-08-23", "ETHUSDT,2025-08-23", 1)
    panel.write_text(bad)
    with pytest.raises(drv.DriverError, match="symbol 'ETHUSDT' inside BTCUSDT"):
        drv.load_panel(tmp_path, "BTCUSDT")
    # a non-ISO date
    panel.write_text(text)
    bad = text.replace("2025-08-23", "23-08-2025", 1)
    panel.write_text(bad)
    with pytest.raises(drv.DriverError, match="bad date"):
        drv.load_panel(tmp_path, "BTCUSDT")
    # dates out of order
    panel.write_text(text)
    bad = text.replace("2025-08-23", "2026-08-23", 1)
    panel.write_text(bad)
    with pytest.raises(drv.DriverError, match="strictly ascending"):
        drv.load_panel(tmp_path, "BTCUSDT")


# --------------------------------------------------------------------------- #
# (i)+(j) sanitized mode: recursive leak scan + non-vacuity
# --------------------------------------------------------------------------- #
def _walk_keys(obj, keys):
    if isinstance(obj, dict):
        for k, v in obj.items():
            keys.append(str(k))
            _walk_keys(v, keys)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            _walk_keys(item, keys)


@pytest.mark.parametrize("family", list(drv.FAMILIES))
@pytest.mark.parametrize("arm", list(drv.ARM_ROLES))
def test_sanitized_leak_scan_recursive_and_nonvacuous(family, arm, tmp_path):
    panels = default_panels(n=130)
    freeze = freeze_fixture()
    n = drv.emit_sanitized(freeze, panels, family, arm, tmp_path)
    assert n > 0
    path = (
        tmp_path / "research/control/v16_run/q_dry_run" / family / arm / "decisions.jsonl"
    )
    records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    assert records
    taken = [r for r in records if r["decision_taken"] is True]
    assert len(taken) == n
    # every emitted record carries EXACTLY the sanitized canon fields
    canon = set(drv.CANON_FIELDS["sanitized_decisions"])
    # recursive leak scan over the whole parsed object tree
    keys: List[str] = []
    _walk_keys(records, keys)
    pattern = re.compile(r"pnl|profit|return|expectancy|pf|stress|sharpe|drawdown", re.I)
    leaked = [k for k in keys if pattern.search(k)]
    assert leaked == [], leaked
    for rec in records:
        assert set(rec) == canon
    # the surface covers every (symbol, evaluated decision day) exactly once
    assert len(records) == 2 * len({r["date"] for r in records})


def test_sanitized_zero_decisions_is_hard_failure(tmp_path):
    # strictly decreasing |disp|: |disp[t-1]| is the MINIMUM of its own
    # rolling window on every day, so the >= quantile trigger never fires.
    # (N=130 so the whole family - including the ret_z control with its
    # 120-day honest warmup - still has an eligible surface to compute.)
    panels = {
        sym: make_rows(n=130, disp_seq=lambda i: 0.5 - 0.001 * i)
        for sym in drv.UNIVERSE
    }
    freeze = freeze_fixture()
    with pytest.raises(drv.DriverError, match="VACUOUS"):
        drv.emit_sanitized(freeze, panels, "CLOSE-DISPLACE-FADE", "anchor", tmp_path)
    assert not (tmp_path / "research").exists()


# --------------------------------------------------------------------------- #
# (k) scored records carry EXACTLY the canon fields
# --------------------------------------------------------------------------- #
SCORED_FILES = (
    "identity", "per_period_series", "per_symbol_breakdown", "per_fold_breakdown",
    "stress_tiers", "drop_one_inputs", "benchmark_context", "margins_to_fail",
    "counters", "reproduction_inputs",
)


@pytest.mark.parametrize("family", list(drv.FAMILIES))
@pytest.mark.parametrize("arm", list(drv.ARM_ROLES))
def test_scored_records_carry_exactly_canon_fields(family, arm, tmp_path):
    panels = default_panels(n=130)
    freeze = freeze_fixture()
    manifest = drv.load_manifest(REPO)
    drv.emit_scored(freeze, manifest, panels, family, arm, tmp_path)
    arm_dir = tmp_path / "results/v16" / family / arm
    for name in SCORED_FILES:
        path = arm_dir / f"{name}.jsonl"
        assert path.exists(), name
        records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        assert records, name
        canon = set(drv.CANON_FIELDS[name])
        for rec in records:
            assert set(rec) == canon, (name, sorted(rec))
    dsr = tmp_path / "results/v16" / family / "dsr_per_period_series.jsonl"
    records = [json.loads(line) for line in dsr.read_text().splitlines() if line.strip()]
    for rec in records:
        assert set(rec) == set(drv.CANON_FIELDS["dsr_per_period_series"])
    # every registered gate is present with all five fields
    margins = [json.loads(line) for line in (arm_dir / "margins_to_fail.jsonl").read_text().splitlines()]
    assert [m["gate_id"] for m in margins] == [
        "G1", "G2", "G3", "G4", "G5", "G10", "G11", "G12"
    ]
    identity = json.loads((arm_dir / "identity.jsonl").read_text())
    assert identity["cycle_id"] == "CRYPTO-V16"
    assert identity["cost_tier"] == "T2.0"
    assert set(identity["data_snapshot_digest"]) == {"BTCUSDT", "ETHUSDT"}
    assert identity["code_freeze_sha"] == drv.git_head_sha(REPO)
    repro = json.loads((arm_dir / "reproduction_inputs.jsonl").read_text())
    assert repro["sanitized"] is False
    assert repro["data_manifest_sha"] == drv.sha256_bytes(
        (REPO / "research/control/v16_run/staging/panel_manifest.json").read_bytes()
    )
    # the sanitized flag is a per-file constant; scored mode never emits a
    # sanitized record and vice versa
    assert not (tmp_path / "research/control/v16_run/q_dry_run").exists()


def test_margins_carry_frozen_thresholds_and_d2_rho(tmp_path_factory):
    panels = default_panels(n=130)
    freeze = freeze_fixture()
    manifest = drv.load_manifest(REPO)
    result = drv.emit_scored(freeze, manifest, panels, "CLOSE-DISPLACE-FADE", "anchor", tmp_path_factory.mktemp("m1"))
    margins = {g["gate_id"]: g for g in result["gates"]}
    assert margins["G2"]["threshold"] == 1.10
    assert margins["G4"]["threshold"] == 0.50
    assert margins["G5"]["threshold"] == 0.20
    assert margins["G12"]["threshold"] == 0.20
    assert margins["G12"]["value"] == 0.1438
    result2 = drv.emit_scored(freeze, manifest, panels, "RUNPERSIST", "anchor", tmp_path_factory.mktemp("m2"))
    margins2 = {g["gate_id"]: g for g in result2["gates"]}
    assert margins2["G12"]["value"] == 0.1927
    # G11 threshold is exactly 0.5x the anchor expectancy on the same book
    assert margins["G11"]["threshold"] == pytest.approx(0.5 * margins["G1"]["value"], abs=1e-12)


# --------------------------------------------------------------------------- #
# (l) identity digest
# --------------------------------------------------------------------------- #
def test_arm_config_digest_is_sha256_of_frozen_spec_text():
    freeze = freeze_fixture()
    for fam in freeze["frozen_families"]:
        for role, text in fam["arms"].items():
            arm = drv.resolve_arm(freeze, fam["family_id"], role)
            assert arm.spec_text == text
            assert arm.arm_config_digest == hashlib.sha256(text.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# (m) the frozen contracts themselves validate
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("proposal", ("A6-V16-P1", "A6-V16-P2"))
def test_frozen_diagnostic_contracts_validate(proposal):
    contracts = json.loads(
        (REPO / "research/control/v16_run/d2/diagnostic_contracts_concretized.json").read_text()
    )
    verdict, findings = validate_contract(contracts[proposal])
    assert verdict == PASS, findings
