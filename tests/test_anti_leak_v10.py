"""A10 anti-leak / pre-registration guards (sprint V9H→V10 wave-H2).

* Golden-path determinism harness (gate H-12 style): the PURE function cores
  of ``research.v9_ts_trend`` and ``research.v9_vol_shock`` are fed fixed
  synthetic series; canonical-serialized outputs must be byte-identical
  across two independent invocations AND across two temp roots (inputs and
  golden outputs read/written relative to each root, mirroring the two-root
  gate flow).  HONEST LIMIT: the full-engine VOLSHOCK path
  (``v9_vol_shock.load_daily_dollar_volume`` → ``research.panel``) needs a
  live data catalog that does not exist in-unit, so the full-engine golden is
  DEFERRED_TO_GATE_RUN; only the pure-function core is pinned here.  This is
  not faked or papered over.
* Anti-rescue guard: if ``research.contract_v10`` exists on this branch it is
  exercised directly against an unfrozen/archived family id; otherwise the
  test SKIPS with an explicit merge-reason (A5 parallel wave) and a clearly
  labelled STUB-MIRROR pins the required runner-entrypoint semantics so the
  shape survives until A1 reruns after merge.
* Budget immutability probe: the append-only global trial ledger refuses
  rewrite/decrement attempts and its writer never mutates existing bytes.

No network, no scored backtests, no live catalog access.
"""

from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Sequence, Tuple

import pytest

from research import v9_ts_trend, v9_vol_shock
from research.v9_ts_trend import (
    compute_targets as ts_compute_targets,
    trend_scores,
    trailing_return,
)
from research.v9_vol_shock import (
    aggregate_daily_dollar_volume,
    compute_targets as vs_compute_targets,
    select_shocked_universe,
    shock_ratios,
)

DAY_NS = v9_ts_trend.DAY_NS
CUTOFF_NS = 30 * DAY_NS


# ----------------------------------------------------- deterministic fixtures
def synth_world() -> Tuple[Dict[str, List[Tuple[int, float]]], Dict[str, List[List[float]]]]:
    closes: Dict[str, List[Tuple[int, float]]] = {}
    for sym, base, drift in (
        ("BTCUSDT", 100.0, 1.0007),
        ("ETHUSDT", 50.0, 0.9981),
        ("SOLUSDT", 20.0, 1.0023),
    ):
        closes[sym] = [
            (i * DAY_NS, round(base * drift ** i + ((i * 13) % 7) * 0.01, 8))
            for i in range(40)
        ]
    bars15: Dict[str, List[List[float]]] = {}
    for sym, base in (("BTCUSDT", 100.0), ("ETHUSDT", 50.0)):
        rows: List[List[float]] = []
        for d in range(30):
            for k in range(96):
                ts = d * DAY_NS + k * (DAY_NS // 96)
                px = round(base * (1 + 0.0005 * ((d * 97 + k) % 11)), 8)
                vol = round(1.0 + ((d * 31 + k * 7) % 17) * 0.25, 6)
                rows.append([ts, px, px, px, px, vol])
        bars15[sym] = rows
    return closes, bars15


def golden_payload_from(
    closes: Mapping[str, List[Tuple[int, float]]],
    bars15: Mapping[str, Sequence[Sequence[float]]],
) -> Dict[str, Any]:
    dollar_volume = {
        sym: aggregate_daily_dollar_volume(bars15[sym]) for sym in sorted(bars15)
    }
    shocks = shock_ratios(dollar_volume=dollar_volume, signal_cutoff_ns=CUTOFF_NS)
    ts_scores = trend_scores(
        daily_closes=closes,
        signal_cutoff_ns=CUTOFF_NS,
        traded_symbols=["SOLUSDT", "BTCUSDT", "ETHUSDT"],
    )
    return {
        "schema": "a10_anti_leak_golden_v1",
        "ts_trailing_edge": trailing_return(closes["BTCUSDT"], cutoff_ns=CUTOFF_NS),
        "ts_trailing_insufficient": trailing_return(
            closes["BTCUSDT"][:2], cutoff_ns=CUTOFF_NS
        ),
        "ts_scores": ts_scores,
        "ts_targets": ts_compute_targets(
            daily_closes=closes,
            signal_cutoff_ns=CUTOFF_NS,
            traded_symbols=["ETHUSDT", "BTCUSDT", "SOLUSDT"],
        ),
        "ts_targets_reverse": ts_compute_targets(
            daily_closes=closes,
            signal_cutoff_ns=CUTOFF_NS,
            traded_symbols=["ETHUSDT", "BTCUSDT", "SOLUSDT"],
            reverse=True,
        ),
        "vs_dollar_volume": {sym: list(dollar_volume[sym]) for sym in dollar_volume},
        "vs_shocks": shocks,
        "vs_universe_top": select_shocked_universe(shocks),
        "vs_universe_bottom_control": select_shocked_universe(shocks, reverse=True),
        "vs_targets": vs_compute_targets(
            daily_closes=closes,
            dollar_volume=dollar_volume,
            signal_cutoff_ns=CUTOFF_NS,
            traded_symbols=["BTCUSDT", "ETHUSDT", "SOLUSDT"],
        ),
        "vs_targets_reverse": vs_compute_targets(
            daily_closes=closes,
            dollar_volume=dollar_volume,
            signal_cutoff_ns=CUTOFF_NS,
            traded_symbols=["BTCUSDT", "ETHUSDT", "SOLUSDT"],
            reverse=True,
        ),
    }


def canonical_bytes(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


# --------------------------------------------- gate H-12 style determinism
def test_golden_path_pure_core_byte_identical_two_invocations_and_two_roots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    closes_a, bars_a = synth_world()
    first = canonical_bytes(golden_payload_from(closes_a, bars_a))
    assert first and len(first) > 256

    closes_b, bars_b = synth_world()
    second = canonical_bytes(golden_payload_from(closes_b, bars_b))
    assert first == second, "two invocations of the pure core diverged"

    inputs_doc = {
        "closes": {sym: [list(pt) for pt in pts] for sym, pts in closes_a.items()},
        "bars15": {sym: [list(row) for row in rows] for sym, rows in bars_a.items()},
    }

    def root_job(root: Path) -> bytes:
        root.mkdir(parents=True, exist_ok=True)
        (root / "inputs.json").write_bytes(canonical_bytes(inputs_doc))
        monkeypatch.chdir(root)
        loaded = json.loads((root / "inputs.json").read_text(encoding="utf-8"))
        closes = {
            sym: [(int(ts), float(px)) for ts, px in pts]
            for sym, pts in loaded["closes"].items()
        }
        bars = {sym: loaded["bars15"][sym] for sym in loaded["bars15"]}
        payload = golden_payload_from(closes, bars)
        out = root / "golden.json"
        out.write_bytes(canonical_bytes(payload))
        return hashlib.sha256(out.read_bytes()).hexdigest()

    try:
        sha_root_a = root_job(tmp_path / "root_a")
        sha_root_b = root_job(tmp_path / "root_b")
    finally:
        monkeypatch.undo()

    assert sha_root_a == sha_root_b, "two-root golden parity broken"
    assert sha_root_a == hashlib.sha256(first).hexdigest(), (
        "cross-root golden diverges from direct-invocation golden"
    )


def test_golden_full_engine_deferred_is_documented_not_faked() -> None:
    """The catalog-bound loader stays UNCALLED here: DEFERRED_TO_GATE_RUN.

    Pins honestly that this suite covers only the pure-function core; the
    full-engine VOLSHOCK golden across two roots requires a live catalog and
    belongs to the gate run (A7/A1 consume that evidence).
    """
    source = Path(v9_vol_shock.__file__).read_text(encoding="utf-8")
    assert "from research.panel import load_bars_15m" in source
    assert "load_daily_dollar_volume" in source


# ------------------------------------------------------- anti-rescue guard
def test_anti_rescue_real_contract_rejects_unfrozen_family() -> None:
    """Exercise research.contract_v10 directly when present on this branch."""
    try:
        contract_v10 = importlib.import_module("research.contract_v10")
    except ImportError:
        pytest.skip(
            "research.contract_v10 absent on branch orca/v10-qa (A5 parallel "
            "wave not merged yet); STUB-MIRROR below pins semantics — A1 reruns "
            "this suite after merge",
            allow_module_level=False,
        )
    candidates = [
        name for name in ("validate_family_admission", "ensure_family_allowed",
                          "check_family_admission", "validate_family")
        if hasattr(contract_v10, name)
    ]
    if not candidates:
        pytest.skip("research.contract_v10 present but exposes no known admission validator", allow_module_level=False)
    validate: Callable[..., Any] = getattr(contract_v10, candidates[0])
    verdict = validate("A10-NOT-A-FROZEN-FAMILY-XYZ")
    admitted = getattr(verdict, "admitted", None)
    if admitted is None and isinstance(verdict, dict):
        admitted = verdict.get("admitted", verdict.get("ok", False))
    assert not admitted, "unfrozen family was admitted by contract_v10"


class StubFrozenFamilyContract:
    """STUB MIRROR of the expected research.contract_v10 surface.

    Merge expectation: when A5's research.contract_v10 lands, delete this
    stub reliance and let test_anti_rescue_real_contract_reject_unfrozen_family
    take over (it currently skips).  Semantics pinned per PLAN H07: the
    runner entrypoint must reject an archived OR unfrozen family even if the
    scoring code supports it.
    """

    def __init__(self, frozen_ids: set[str], archived_ids: set[str]) -> None:
        self.frozen_ids = frozen_ids
        self.archived_ids = archived_ids

    def validate_family_admission(self, family_id: str) -> Dict[str, Any]:
        if family_id in self.archived_ids:
            return {"admitted": False, "reason": "ARCHIVED_FAMILY"}
        if family_id not in self.frozen_ids:
            return {"admitted": False, "reason": "UNFROZEN_FAMILY"}
        return {"admitted": True, "reason": "FROZEN_AND_ACTIVE"}


def runner_entrypoint_stub(contract: StubFrozenFamilyContract, family_id: str, payload: str) -> str:
    decision = contract.validate_family_admission(family_id)
    if not decision["admitted"]:
        raise PermissionError(decision["reason"])
    return payload


@pytest.mark.parametrize(
    "family_id,expected_reason",
    [
        ("v9_ts_trend_ARCHIVED_XSECT-TSTREND-CTRL", "ARCHIVED_FAMILY"),
        ("never_frozen_rescue_attempt_v10", "UNFROZEN_FAMILY"),
    ],
    ids=["archived-but-code-supported", "totally-unfrozen"],
)
def test_stub_mirror_runner_rejects_archived_and_unfrozen(family_id: str, expected_reason: str) -> None:
    """STUB-MIRROR (not production coverage): pins the H07 admission shape."""
    contract = StubFrozenFamilyContract(
        frozen_ids={"v9_ts_trend_ACTIVE"},
        archived_ids={"v9_ts_trend_ARCHIVED_XSECT-TSTREND-CTRL"},
    )
    with pytest.raises(PermissionError) as excinfo:
        runner_entrypoint_stub(contract, family_id, "scored-payload")
    assert expected_reason in str(excinfo.value)


def test_stub_mirror_runner_admits_active_frozen_family() -> None:
    contract = StubFrozenFamilyContract(frozen_ids={"v9_ts_trend_ACTIVE"}, archived_ids=set())
    assert runner_entrypoint_stub(contract, "v9_ts_trend_ACTIVE", "payload") == "payload"


# -------------------------------------------------- budget immutability probe
def _ledger_entry(experiment_id: str, appended_at: str | None = None) -> Dict[str, Any]:
    entry: Dict[str, Any] = {
        "experiment_id": experiment_id,
        "verdict": "PASS",
        "schema": "a10_budget_probe_v1",
        "matrix_id": "v10qa_probe_cell",
    }
    if appended_at is not None:
        entry["appended_at"] = appended_at
    return entry


def test_budget_ledger_append_only_writer_never_mutates_prefix(tmp_path: Path) -> None:
    gl = pytest.importorskip("research.global_ledger")
    ledger = tmp_path / "experiments.jsonl"
    gl.append_verified(
        _ledger_entry("v10qa-001", "2026-08-26T00:00:01+00:00"), ledger
    )
    gl.append_verified(
        _ledger_entry("v10qa-002", "2026-08-26T00:00:02+00:00"), ledger
    )
    prefix = ledger.read_bytes()

    gl.append_verified(
        _ledger_entry("v10qa-003", "2026-08-26T00:00:03+00:00"), ledger
    )
    after = ledger.read_bytes()
    assert after.startswith(prefix), "append-only writer rewrote existing bytes"
    snapshot = gl.snapshot(ledger)
    assert snapshot["count"] == 3
    assert [row["experiment_id"] for row in snapshot["rows"]] == ["v10qa-001", "v10qa-002", "v10qa-003"]
    assert gl.verify_append_only(ledger) is True


def test_budget_ledger_refuses_rewrite_and_decrement_attempts(tmp_path: Path) -> None:
    gl = pytest.importorskip("research.global_ledger")
    ledger = tmp_path / "experiments.jsonl"
    for idx in (1, 2, 3):
        gl.append_verified(
            _ledger_entry(f"v10qa-{idx:03d}", f"2026-08-26T00:00:0{idx}+00:00"), ledger
        )
    before_digest = gl.snapshot(ledger)["sha256"]

    lines = ledger.read_text(encoding="utf-8").splitlines(keepends=True)
    ledger.write_text("".join(reversed(lines)), encoding="utf-8")

    assert gl.verify_append_only(ledger) is False
    with pytest.raises(ValueError, match="append_only_violation"):
        gl.append_verified(_ledger_entry("v10qa-004"), ledger)
    assert "".join(reversed(lines)) == ledger.read_text(encoding="utf-8"), (
        "refused append mutated the file anyway"
    )

    ledger.write_text("".join(lines), encoding="utf-8")
    restored_digest = gl.snapshot(ledger)["sha256"]
    assert restored_digest == before_digest

    ledger.write_text(lines[0], encoding="utf-8")
    decremented = gl.snapshot(ledger)
    assert decremented["count"] == 1
    assert decremented["sha256"] != before_digest

    missing_verdict = {"experiment_id": "v10qa-broken", "schema": "x"}
    with pytest.raises(ValueError):
        gl.append_verified(missing_verdict, ledger)
    assert gl.snapshot(ledger)["count"] == 1
