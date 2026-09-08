"""CRYPTO-V17 A8 driver lane tests (family-agnostic run_v17_cell).

Synthetic only: tiny H1 panels are written through the SAME loader path
(csv + sha256-verified temp manifest), no real data file is read, nothing
is scored outside ``tmp_path``, and no frozen module byte is edited.

Fixtures
* 3-day x 24h panel  -> loader / sha-verification tests (per the lane task).
* 12-day x 24h panel -> pipeline tests.  12 days: fold edges floor(i*12/3)
  = [0,4,8,12]; the 1-day purge around the internal boundaries purges day
  indices {3,4,7,8}; fold members F0={0,1,2} F1={5,6} F2={9,10,11}.

Fixture map (task items a-f):
* (a) test_v17_purge_*                   -- purge math + refused boundary trips
* (b) test_v17_cost_once_*               -- L-V14-0 schedule, hand-exact,
                                            cost once per fill, tier ratios,
                                            kernel-primitive equality
* (c) test_v17_gate_margins_arm_attributed
* (d) test_v17_sanitized_*               -- decisions only, leak scan,
                                            vacuous = HARD FAILURE,
                                            EXAMPLE formula refused when scored
* (e) test_v17_two_runs_byte_identical
* (f) test_v17_manifest_sha_mismatch_refuses
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from research.adapter_v10.base import GenericStrategyBase
from research.adapter_v10.protocol import CostModel, StressSpec
from research.control.v17_run.driver import family_registry_v17 as reg
from research.control.v17_run.driver import run_v17_cell as d

# ------------------------------------------------------------------------- #
# Synthetic H1 panels through the real loader path
# ------------------------------------------------------------------------- #
S0 = date(2025, 8, 22)
#: (last - vwap)/vwap cycled per hour; |disp| spreads the trigger thresholds.
DISP_CYCLE = (0.003, -0.002, 0.001, -0.0025, 0.0008, -0.0018)
UNIVERSE = ("BTCUSDT", "ETHUSDT")
ARM_PARAMS = {
    "anchor": {"threshold": 0.0012},
    "neighbour": {"threshold": 0.0024, "warmup": 5},
    "control": {"threshold": 0.0009},
}
HEAD = "0" * 40


def _write_h1_panel(directory: Path, symbol: str, n_days: int) -> Path:
    days = [(S0 + timedelta(days=i)).isoformat() for i in range(n_days)]
    path = directory / d.PANEL_FILE.format(symbol=symbol)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [",".join(d.H1_SCHEMA)]
    idx = 0
    for day in days:
        for hour in range(24):
            disp = DISP_CYCLE[idx % len(DISP_CYCLE)]
            price = 100.0 + 0.01 * idx
            vwap = price / (1.0 + disp)
            row = {
                "symbol": symbol,
                "hour_utc": f"{day}T{hour:02d}",
                "day_utc": day,
                "n_trades": 100,
                "buy_count": 50,
                "sell_count": 50,
                "buy_qty": 10.0,
                "sell_qty": 10.0,
                "buy_quote": 10.0 * vwap,
                "sell_quote": 10.0 * vwap,
                "quote_total": 20.0 * vwap,
                "qty_total": 20.0,
                "vwap": vwap,
                "first_price": price * 0.999,
                "last_price": price,
                "high_price": price * 1.001,
                "low_price": price * 0.998,
                "max_trade_quote": 5.0,
                "sum_qty_squared": 400.0,
                "n_price_moves": 60,
                "sum_squared_log_ret": 0.001,
                "gap_sum_s": 2.5,
                "gap_count": 10,
                "entry_gap_s": 0.3,
                "run_close_dir": "buy",
                "run_close_len": 3,
                "run_switch_count": 2,
                "max_run_buy": 5,
                "max_run_sell": 4,
                "first_ts_ms": 1_724_000_000_000 + idx * 3_600_000,
                "last_ts_ms": 1_724_000_063_000 + idx * 3_600_000,
            }
            lines.append(",".join(
                repr(row[col]) if isinstance(row[col], float) else str(row[col])
                for col in d.H1_SCHEMA
            ))
            idx += 1
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _write_manifest(directory: Path, symbols, n_days: int) -> Path:
    doc = {
        "schema": "v17_run_artifact_v1",
        "artifact": "staging_panel_manifest",
        "symbols": list(symbols),
        "window": [S0.isoformat(), (S0 + timedelta(days=n_days - 1)).isoformat()],
        "panel_sha256": {
            sym: hashlib.sha256(
                (directory / d.PANEL_FILE.format(symbol=sym)).read_bytes()
            ).hexdigest()
            for sym in symbols
        },
        "hourly_rows": {sym: n_days * 24 for sym in symbols},
    }
    path = directory / "panel_manifest_v17_published.json"
    path.write_text(json.dumps(doc, sort_keys=True, indent=1), encoding="utf-8")
    return path


def _stage(tmp_path: Path, symbols=UNIVERSE, n_days: int = 12):
    panel_dir = tmp_path / "staging"
    for sym in symbols:
        _write_h1_panel(panel_dir, sym, n_days)
    return panel_dir, _write_manifest(panel_dir, symbols, n_days)


def _family_doc(params_by_arm, *, formula_id="TEST.h1_momentum_flag",
                universe=UNIVERSE, family_id="SYNTH-FAM", lag=1, holding=1):
    return {
        "family_id": family_id,
        "clock": "H1",
        "universe": list(universe),
        "entry": {"lag_buckets": lag},
        "exit": {"holding_buckets": holding},
        "arms": [
            {
                "arm_id": arm_id,
                "kind": arm_id,
                "exposure": {
                    "type": "panel_formula",
                    "formula_id": formula_id,
                    "params": params,
                },
            }
            for arm_id, params in params_by_arm.items()
        ],
    }


def _make_spec(params_by_arm=ARM_PARAMS, **kw):
    return d._parse_family(_family_doc(params_by_arm, **kw), base_dir=Path("/"))


def _write_selection(path: Path, params_by_arm=ARM_PARAMS, **kw):
    doc = {
        "cycle_id": "CRYPTO-V17",
        "families": [_family_doc(params_by_arm, **kw)],
    }
    path.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    return path


@pytest.fixture
def panel12(tmp_path, monkeypatch):
    panel_dir, manifest_path = _stage(tmp_path, n_days=12)
    monkeypatch.setattr(d, "PANEL_DIR", panel_dir)  # absolute join wins
    manifest = d.load_manifest(manifest_path)
    manifest["_path"] = manifest_path  # for CLI-level tests
    return manifest


# ------------------------------------------------------------------------- #
# Test formulas (registered, non-example; the registry ships the EXAMPLE)
# ------------------------------------------------------------------------- #
@reg.register("TEST.h1_momentum_flag", example_only=False)
def _momentum_flag(panels, params):
    threshold = float(params["threshold"])
    warmup = int(params.get("warmup", 0))
    out = {}
    for sym, rows in panels.items():
        series = []
        for t, row in enumerate(rows):
            if t < warmup:
                series.append(None)
                continue
            disp = (float(row["last_price"]) - float(row["vwap"])) / float(row["vwap"])
            series.append(float(reg.sign(disp)) if abs(disp) >= threshold else 0.0)
        out[sym] = series
    return out


@reg.register("TEST.h1_zero", example_only=False)
def _zero(panels, params):
    return {sym: [0.0] * len(rows) for sym, rows in panels.items()}


# ------------------------------------------------------------------------- #
# (a) purge force-flat at fold boundaries
# ------------------------------------------------------------------------- #
def test_v17_purge_math_matches_the_frozen_indices():
    assert d.purged_day_indices(365) == d.FROZEN_PURGED_DAY_INDICES
    assert d.FROZEN_PURGED_DAY_INDICES == frozenset({120, 121, 242, 243})
    folds, purged = d.build_folds(365)
    assert [f.label for f in folds] == ["F0", "F1", "F2"]
    assert folds[0].member_days[0] == 0 and folds[0].member_days[-1] == 119
    assert folds[1].member_days[0] == 122 and folds[1].member_days[-1] == 241
    assert folds[2].member_days[0] == 244 and folds[2].member_days[-1] == 364
    members = {day for f in folds for day in f.member_days}
    assert not (members & set(purged)) and len(members) + len(purged) == 365
    # 12-day analogue used by the fixtures
    folds12, purged12 = d.build_folds(12)
    assert purged12 == frozenset({3, 4, 7, 8})
    assert [f.member_days for f in folds12] == [(0, 1, 2), (5, 6), (9, 10, 11)]


def test_v17_purge_force_flat_refuses_boundary_crossing_trips(panel12):
    spec = _make_spec(universe=("SYN0",))
    n_buckets = 12 * 24
    bucket_day = [b // 24 for b in range(n_buckets)]
    folds, purged = d.build_folds(12)
    # d=69: last bookable bucket of F0 (entry 70, exit 71 both on day 2).
    # d=70: exit 72 lands on purged day 3 -> refused.
    # d=72 / d=100: decision ON a purged day -> refused.
    # d=165: bookable in F1 (entry 166, exit 167 both on day 6).
    # d=166: exit 168 lands on purged day 7 -> refused.
    # d=287: round trip would run off the grid -> refused.
    decisions = {"SYN0": {dd: 1.0 for dd in (69, 70, 72, 100, 165, 166, 287)}}
    trips = d.compute_round_trips(decisions, spec, bucket_day, folds, purged, n_buckets)
    assert {t["decision_bucket"] for t in trips} == {69, 165}
    # holding 2: even d=69 crosses the purged day-3 boundary (exit 72) -> refused
    spec_h2 = _make_spec(universe=("SYN0",), holding=2)
    assert d.compute_round_trips(
        decisions, spec_h2, bucket_day, folds, purged, n_buckets
    ) == []
    # every booked trip stays inside one fold and never touches a purged day
    fold_by_day = {day: f for f in folds for day in f.member_days}
    for trip in trips:
        window_days = {
            bucket_day[b]
            for b in range(trip["entry_bucket"], trip["exit_bucket"] + 1)
        }
        assert not (window_days & set(purged))
        assert window_days <= set(
            fold_by_day[bucket_day[trip["decision_bucket"]]].member_days
        )


def test_v17_purge_force_flat_holds_for_every_computed_book(panel12):
    spec = _make_spec()
    h1 = d.load_panels(d.repo_root(), panel12, spec.universe)
    state = d.compute_family(spec, h1, base_dir=Path("/"), allow_example=True)
    folds, purged = state["folds"], state["purged"]
    bucket_day = state["bucket_day"]
    fold_by_day = {day: f for f in folds for day in f.member_days}
    n_trips = 0
    for arm_state in state["arms"].values():
        for book in arm_state["books"].values():
            for trip in book.round_trips:
                n_trips += 1
                days = {
                    bucket_day[b]
                    for b in range(trip["entry_bucket"], trip["exit_bucket"] + 1)
                }
                assert not (days & set(purged))
                assert days <= set(
                    fold_by_day[bucket_day[trip["decision_bucket"]]].member_days
                )
    assert n_trips > 0  # the fixture actually books


# ------------------------------------------------------------------------- #
# (b) cost exactly once per fill -- L-V14-0 schedule, hand-computed 8 legs
# ------------------------------------------------------------------------- #
class _KernelProbe:
    """Duck-typed cost-model carrier for the audited kernel primitive."""

    def cost_model(self):
        return CostModel(
            taker_fee_bps=5.0,
            adverse_tick_slip_floor=1,
            default_tick_sizes={"SYN0": 0.01},
        )


FLAT_PRICES = {"SYN0": [100.0] * (12 * 24)}


@pytest.fixture
def eight_leg_trips():
    spec = _make_spec(universe=("SYN0",))
    n_buckets = 12 * 24
    bucket_day = [b // 24 for b in range(n_buckets)]
    folds, purged = d.build_folds(12)
    legs = (0, 8, 16, 24, 32, 40, 48, 56)  # 8 legs, all inside fold F0
    decisions = {"SYN0": {leg: 0.125 for leg in legs}}
    trips = d.compute_round_trips(decisions, spec, bucket_day, folds, purged, n_buckets)
    assert len(trips) == 8
    return trips


def test_v17_cost_once_8leg_hand_exact_and_kernel_equal(eight_leg_trips):
    universe = ("SYN0",)
    base = d.simulate_book(eight_leg_trips, FLAT_PRICES, "T1.0", universe)
    fee15 = d.simulate_book(eight_leg_trips, FLAT_PRICES, "T1.5", universe)
    tier2 = d.simulate_book(eight_leg_trips, FLAT_PRICES, "T2.0", universe)
    # Hand world (L-V14-0 schedule): price 100.0, fee 5e-4, tick 0.01.
    # 8 legs x |w|=0.125, entry+exit -> cost = 8*0.125*rate*2.
    # T1.0 rate 6e-4 -> 0.0012;  T1.5 rate 8.5e-4 -> 0.0017;
    # T2.0 (fee x2.0 + 2 ticks) rate 1.2e-3 -> 0.0024.
    assert base.cost_fills_total == pytest.approx(0.0012, abs=1e-12)
    assert fee15.cost_fills_total == pytest.approx(0.0017, abs=1e-12)
    assert tier2.cost_fills_total == pytest.approx(0.0024, abs=1e-12)
    assert len({base.cost_fills_total, fee15.cost_fills_total, tier2.cost_fills_total}) == 3
    assert fee15.cost_fills_total == pytest.approx(base.cost_fills_total * 17 / 12, rel=1e-12)
    assert tier2.cost_fills_total == pytest.approx(base.cost_fills_total * 24 / 12, rel=1e-12)
    # flat prices -> zero gross; the net is EXACTLY minus the charged cost once
    assert base.gross_pnl == 0.0
    assert base.pnl == pytest.approx(-0.0012, abs=1e-12)
    assert base.n_fills == 16 and base.n_round_trips == 8
    # cost lives on the fill records, ONCE, and holding terms are exactly zero
    assert len(base.fills) == 16
    assert all(f.cost_holding_terms == 0.0 for f in base.fills)
    assert base.cost_holding_terms_total == 0.0
    assert sum(f.cost_fills for f in base.fills) == pytest.approx(
        base.cost_fills_total, abs=1e-15
    )
    # identical arithmetic inside the AUDITED kernel primitive, per tier
    probe = _KernelProbe()
    for tier, mult, ticks in (("T1.0", 1.0, 1), ("T1.5", 1.5, 1), ("T2.0", 2.0, 2)):
        kernel_cost = GenericStrategyBase.rebalance_cost_between(
            probe, {}, {"SYN0": 0.125}, prices={"SYN0": 100.0},
            stress=StressSpec(name="baseline", fee_multiplier=mult, tick_slip_ticks=ticks),
        )
        assert kernel_cost == pytest.approx(d.fill_cost(0.125, 100.0, tier), abs=1e-15)


def test_v17_cost_once_independent_of_holding_length():
    spec1 = _make_spec(universe=("SYN0",))
    spec3 = _make_spec(universe=("SYN0",), holding=3)
    n_buckets = 12 * 24
    bucket_day = [b // 24 for b in range(n_buckets)]
    folds, purged = d.build_folds(12)
    legs = (0, 8, 16, 24, 32, 40, 48, 56)
    decisions = {"SYN0": {leg: 0.125 for leg in legs}}
    trips1 = d.compute_round_trips(decisions, spec1, bucket_day, folds, purged, n_buckets)
    trips3 = d.compute_round_trips(decisions, spec3, bucket_day, folds, purged, n_buckets)
    assert len(trips1) == len(trips3) == 8
    b1 = d.simulate_book(trips1, FLAT_PRICES, "T1.0", ("SYN0",))
    b3 = d.simulate_book(trips3, FLAT_PRICES, "T1.0", ("SYN0",))
    # SAME 16 fills either way: holding 3x longer charges NOTHING extra
    assert b1.n_fills == b3.n_fills == 16
    assert b1.cost_fills_total == b3.cost_fills_total == pytest.approx(0.0012, abs=1e-12)
    assert b3.pnl == pytest.approx(-0.0012, abs=1e-12)


# ------------------------------------------------------------------------- #
# (c) gate margins are arm-attributed
# ------------------------------------------------------------------------- #
def test_v17_gate_margins_arm_attributed(tmp_path, panel12):
    out = tmp_path / "out"
    spec = _make_spec()
    d.run_family(spec, panel12, d.repo_root(), out,
                 sanitized=False, base_dir=tmp_path, code_freeze_sha=HEAD)
    margins = {}
    for arm_id in ("anchor", "neighbour", "control"):
        path = out / "results/v17/SYNTH-FAM" / arm_id / "margins_to_fail.jsonl"
        records = [json.loads(ln) for ln in path.read_text().splitlines() if ln.strip()]
        assert [r["gate_id"] for r in records] == ["G1", "G2", "G3", "G4", "G5"]
        for rec in records:
            _UPPER = {"G4", "G5"}
            assert set(rec) == {"cycle_id", "gate_id", "value", "threshold",
                                "margin", "arm_id"}
            assert rec["arm_id"] == arm_id          # arm-attributed, in the record
            assert rec["cycle_id"] == "CRYPTO-V17"
            assert rec["margin"] == d.r12(
                (rec["threshold"] - rec["value"]) if rec["gate_id"] in _UPPER
                else (rec["value"] - rec["threshold"]))
        margins[arm_id] = {r["gate_id"]: r for r in records}
    # distinct arms -> distinct OWN series -> distinct G1 margins (no sharing)
    assert margins["anchor"]["G1"]["value"] != margins["control"]["G1"]["value"]
    assert margins["anchor"]["G1"]["margin"] != margins["control"]["G1"]["margin"]
    # first-fail gate order (frozen) on synthetic metrics
    assert d.first_failing_gate(d.ArmMetrics(-0.1, 2.0, 0.01, 10, 3, 0.1)) == "G1"
    assert d.first_failing_gate(d.ArmMetrics(0.1, 1.05, 0.01, 10, 3, 0.1)) == "G2"
    assert d.first_failing_gate(
        d.ArmMetrics(0.1, float("inf"), 0.01, 10, 1, 0.1)) == "G3"
    assert d.first_failing_gate(
        d.ArmMetrics(0.1, float("inf"), 0.01, 10, 3, 0.8)) == "G4"
    assert d.first_failing_gate(
        d.ArmMetrics(0.1, float("inf"), 0.25, 10, 3, 0.1)) == "G5"
    assert d.first_failing_gate(
        d.ArmMetrics(0.1, float("inf"), 0.01, 10, 3, 0.1)) is None
    # all 10 scaffold categories + the family dsr file are on disk
    arm_dir = out / "results/v17/SYNTH-FAM/anchor"
    expected = {
        "identity.jsonl", "per_period_series.jsonl", "per_symbol_breakdown.jsonl",
        "per_fold_breakdown.jsonl", "stress_tiers.jsonl", "drop_one_inputs.jsonl",
        "benchmark_context.jsonl", "margins_to_fail.jsonl", "counters.jsonl",
        "reproduction_inputs.jsonl",
    }
    assert {p.name for p in arm_dir.iterdir()} == expected
    dsr_path = out / "results/v17/SYNTH-FAM/dsr_per_period_series.jsonl"
    assert dsr_path.exists()
    # the dsr series comes from the ANCHOR book (same numbers, fewer fields)
    anchor_series = [
        json.loads(ln)
        for ln in (arm_dir / "per_period_series.jsonl").read_text().splitlines()
        if ln.strip()
    ]
    dsr_series = [json.loads(ln) for ln in dsr_path.read_text().splitlines() if ln.strip()]
    assert len(dsr_series) == len(anchor_series)
    for a, b in zip(dsr_series, anchor_series):
        assert set(a) == {"cycle_id", "period", "returns"}
        assert a["period"] == b["period"] and a["returns"] == b["returns"]


# ------------------------------------------------------------------------- #
# (d) sanitized mode: decisions only; vacuous is a HARD FAILURE
# ------------------------------------------------------------------------- #
def _tree_files(root: Path):
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())


def test_v17_sanitized_emits_decisions_and_nothing_outcome_shaped(tmp_path, panel12):
    out = tmp_path / "out"
    spec = _make_spec()
    summary = d.run_family(spec, panel12, d.repo_root(), out,
                           sanitized=True, base_dir=tmp_path, code_freeze_sha=HEAD)
    assert summary["sanitized"] is True
    files = _tree_files(out)
    assert files, "sanitized emission produced nothing"
    for rel in files:  # ONLY the dry-run surface, nothing outcome-shaped anywhere
        assert rel.startswith("research/control/v17_run/q_dry_run/"), rel
        assert not rel.startswith("results/"), rel
    total_taken = 0
    for arm_id in ("anchor", "neighbour", "control"):
        path = (out / "research/control/v17_run/q_dry_run/SYNTH-FAM" / arm_id
                / "decisions.jsonl")
        records = [json.loads(ln) for ln in path.read_text().splitlines() if ln.strip()]
        assert records
        taken = 0
        for rec in records:
            _UPPER = {"G4", "G5"}
            assert set(rec) == {
                "cycle_id", "family_id", "arm_id", "date", "hour",
                "decision_taken", "symbol",
            }
            for key in rec:  # scan EVERY key for outcome-shaped strings
                assert not d.LEAK_PATTERN.search(str(key)), key
            assert isinstance(rec["decision_taken"], bool)
            assert rec["arm_id"] == arm_id and rec["family_id"] == "SYNTH-FAM"
            taken += int(rec["decision_taken"])
        assert taken > 0  # non-vacuous
        total_taken += taken
    assert total_taken == sum(summary["decisions"].values())


def test_v17_vacuous_book_is_a_hard_failure_and_example_never_scored(tmp_path, panel12):
    manifest = panel12
    # all-zero formula -> zero decisions -> sanitized HARD FAILURE
    zero_spec = _make_spec(formula_id="TEST.h1_zero")
    with pytest.raises(d.DriverError, match="VACUOUS"):
        d.run_family(zero_spec, manifest, d.repo_root(), tmp_path / "z1",
                     sanitized=True, base_dir=tmp_path, code_freeze_sha=HEAD)
    # ...and the scored path refuses the vacuous cell as well
    with pytest.raises(d.DriverError, match="VACUOUS CELL"):
        d.run_family(zero_spec, manifest, d.repo_root(), tmp_path / "z2",
                     sanitized=False, base_dir=tmp_path, code_freeze_sha=HEAD)
    # the EXAMPLE_TEST_ONLY formula runs the sanitized dry-run...
    example_spec = _make_spec(formula_id="EXAMPLE_TEST_ONLY.h1_vwap_revert")
    d.run_family(example_spec, manifest, d.repo_root(), tmp_path / "ex",
                 sanitized=True, base_dir=tmp_path, code_freeze_sha=HEAD)
    # ...but can NEVER back a scored arm
    with pytest.raises(d.DriverError, match="EXAMPLE_TEST_ONLY"):
        d.run_family(example_spec, manifest, d.repo_root(), tmp_path / "ex2",
                     sanitized=False, base_dir=tmp_path, code_freeze_sha=HEAD)


# ------------------------------------------------------------------------- #
# (e) determinism: two runs byte-identical
# ------------------------------------------------------------------------- #
def test_v17_two_runs_byte_identical(tmp_path, panel12):
    spec = _make_spec()
    out1, out2 = tmp_path / "run1", tmp_path / "run2"
    for out in (out1, out2):
        d.run_family(spec, panel12, d.repo_root(), out,
                     sanitized=False, base_dir=tmp_path, code_freeze_sha=HEAD)
    files1, files2 = _tree_files(out1), _tree_files(out2)
    assert files1 == files2 and files1
    for rel in files1:
        assert (out1 / rel).read_bytes() == (out2 / rel).read_bytes(), rel
    # sanitized determinism too
    s1, s2 = tmp_path / "srun1", tmp_path / "srun2"
    for out in (s1, s2):
        d.run_family(spec, panel12, d.repo_root(), out,
                     sanitized=True, base_dir=tmp_path, code_freeze_sha=HEAD)
    assert _tree_files(s1) == _tree_files(s2)
    for rel in _tree_files(s1):
        assert (s1 / rel).read_bytes() == (s2 / rel).read_bytes(), rel


# ------------------------------------------------------------------------- #
# (f) manifest sha mismatch refuses
# ------------------------------------------------------------------------- #
def test_v17_manifest_sha_mismatch_refuses(tmp_path, monkeypatch):
    panel_dir, manifest_path = _stage(tmp_path, n_days=3)
    manifest = d.load_manifest(manifest_path)
    # honest manifest loads through the real loader (3 days x 24h = 72 rows)
    monkeypatch.setattr(d, "PANEL_DIR", panel_dir)
    panels = d.load_panels(d.repo_root(), manifest, ("BTCUSDT", "ETHUSDT"))
    assert len(panels["BTCUSDT"]) == 72
    # one flipped hex digit in one symbol's sha -> refusal BEFORE any use
    bad = dict(manifest["panel_sha256"])
    first = bad["ETHUSDT"]
    bad["ETHUSDT"] = ("0" if first[0] != "0" else "1") + first[1:]
    tampered = dict(manifest)
    tampered["panel_sha256"] = bad
    with pytest.raises(d.DriverError, match="MISMATCH"):
        d.load_panels(d.repo_root(), tampered, ("BTCUSDT", "ETHUSDT"))
    # a symbol missing from the manifest refuses as well
    missing = dict(manifest)
    missing["panel_sha256"] = {"BTCUSDT": manifest["panel_sha256"]["BTCUSDT"]}
    with pytest.raises(d.DriverError, match="lacks symbol"):
        d.load_panels(d.repo_root(), missing, ("BTCUSDT", "ETHUSDT"))


# ------------------------------------------------------------------------- #
# CLI + spec-validation refusals (fail closed, no product invention)
# ------------------------------------------------------------------------- #
def test_v17_cli_scored_and_sanitized(tmp_path, panel12, monkeypatch, capsys):
    selection = _write_selection(tmp_path / "selection.json")
    monkeypatch.setattr(d, "MANIFEST_FILE", panel12["_path"])
    monkeypatch.chdir(tmp_path)
    rc = d.main(["--selection", str(selection)])
    assert rc == 0
    scored_files = _tree_files(tmp_path / "results")
    assert any("v17/SYNTH-FAM/anchor/margins_to_fail.jsonl" in f for f in scored_files)
    out = capsys.readouterr().out
    assert "scored emission" in out and "remediated_kernel=True" in out
    san_dir = tmp_path / "san"
    san_dir.mkdir()
    monkeypatch.chdir(san_dir)
    rc = d.main(["--selection", str(selection), "--sanitized"])
    assert rc == 0
    dry = list((tmp_path / "san").rglob("decisions.jsonl"))
    assert len(dry) == 3
    assert capsys.readouterr().out.count("0 outcome fields emitted") == 3
    # --smoke writes ONLY into the isolated v17_smoke namespace
    smoke_dir = tmp_path / "smoke"
    smoke_dir.mkdir()
    monkeypatch.chdir(smoke_dir)
    rc = d.main(["--selection", str(selection), "--smoke"])
    assert rc == 0
    smoke_files = _tree_files(smoke_dir / "results")
    assert smoke_files and all(f.startswith("v17_smoke/") for f in smoke_files)
    assert capsys.readouterr().out.count("[SMOKE]") == 3
    # smoke + sanitized is refused
    monkeypatch.chdir(tmp_path)
    with pytest.raises(d.DriverError, match="mutually exclusive"):
        d.main(["--selection", str(selection), "--smoke", "--sanitized"])


def test_v17_selection_spec_refusals(tmp_path, panel12, monkeypatch):
    # duplicate kind
    path = tmp_path / "sel_dup.json"
    _write_selection(path)
    doc = json.loads(path.read_text())
    doc["families"][0]["arms"][1]["kind"] = "anchor"
    path.write_text(json.dumps(doc))
    with pytest.raises(d.DriverError, match="duplicate kind"):
        d.load_selection(path)
    # lag 0 would peek the same-bucket close -> refused
    doc = json.loads(path.read_text())
    doc["families"][0]["arms"][1]["kind"] = "neighbour"
    doc["families"][0]["entry"]["lag_buckets"] = 0
    path.write_text(json.dumps(doc))
    with pytest.raises(d.DriverError, match="lag_buckets"):
        d.load_selection(path)
    # unknown formula id -> refusal at exposure evaluation
    spec = _make_spec(formula_id="TEST.does_not_exist")
    stage_dir, manifest_path = _stage(tmp_path / "stage_unknown", n_days=12)
    monkeypatch.setattr(d, "PANEL_DIR", stage_dir)
    manifest = d.load_manifest(manifest_path)
    h1 = d.load_panels(d.repo_root(), manifest, spec.universe)
    with pytest.raises(d.DriverError, match="registry refusal"):
        d.compute_family(spec, h1, base_dir=tmp_path, allow_example=True)
    # --families with an unknown id refuses
    valid = _write_selection(tmp_path / "selection.json")
    _, specs = d.load_selection(valid)
    with pytest.raises(d.DriverError, match="not in the selection"):
        d.select_families(specs, "NOPE")
    # registry discipline: duplicate registration and example-only flags
    with pytest.raises(ValueError):
        reg.register("TEST.h1_zero", example_only=False)(_zero)
    assert reg.is_example_only("EXAMPLE_TEST_ONLY.anything")
    assert not reg.is_example_only("TEST.h1_zero")
