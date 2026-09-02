"""A4 safe-cache tests (PLAN.md section 6, H06 / H08 items 15-17).

Synthetic producer scripts only -- no real data, no scored backtests:

* ``make_cache_key``: deterministic, order-insensitive for dict inputs
  (and sorted symbol universes), sensitive to EVERY component (changing
  any one changes the key), TypeError on non-JSON-serializable material;
* ``ProcessLocalCache``: two instances are isolated; pickling/copying is
  refused so the store can never cross a process boundary;
* ``SharedCacheMergeGate`` byte-parity helper: manifest equality over a
  directory tree (nested files, deterministic, mismatch names the rel,
  unreadable root -> uncertain);
* full adoption flow with a SYNTHETIC producer executed through the H04
  streamed runner twice (cache-off slow path vs cache-on fast path):
  identical artifact sets prove parity via sha256 manifests, an
  instrumented counter file proves the raw-read budget (<= 2), and the
  wall-time reduction metric clears the 30% target -> adopted;
* fail-closed rejections: tampered artifact breaks parity, raw_reads > 2
  exceeds budget, repro flag false or missing, proofs missing entirely,
  below-target reduction under strict=True -- every rejection carries
  reasons; strict=False downgrades ONLY the performance miss to
  advisory-only;
* pnl_seen forbids adoption even with perfect proofs (posture freeze).
"""

from __future__ import annotations

import copy
import json
import pickle
import sys
from pathlib import Path

import pytest

from research.cache_v10 import (
    ProcessLocalCache,
    SharedCacheMergeGate,
    adopt_shared_cache,
    make_cache_key,
    sha256_file_chunked,
)
from research.reproduction_stream_v10 import run_streamed

PY = sys.executable

#: Synthetic "pipeline" producer: simulates raw-bar reading cost through a
#: caller-tunable sleep and an instrumented raw_reads counter FILE that
#: lives OUTSIDE the artifact dirs; then writes a deterministic artifact
#: set identical in both modes (cache never changes outputs).
PRODUCER = r'''
import json, sys, time
from pathlib import Path
mode, art_dir, counter_path, delay = (
    sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]), float(sys.argv[4]))
count = 0
if counter_path.exists():
    count = int(json.loads(counter_path.read_text())["raw_reads"])
count += 1
counter_path.parent.mkdir(parents=True, exist_ok=True)
counter_path.write_text(json.dumps({"raw_reads": count}))
time.sleep(delay)
art_dir.mkdir(parents=True, exist_ok=True)
(art_dir / "nested").mkdir(exist_ok=True)
rows = "".join(f'{{"i": {i}, "sym": "AAA", "v": {i * 2}}}\n' for i in range(64))
(art_dir / "schedule.jsonl").write_text(rows)
(art_dir / "canonical_metrics.json").write_text('{"total_pnl": 0.0, "pf": 1.25}')
(art_dir / "nested" / "digest.txt").write_text("deterministic-bytes\n")
'''


def _run_producer(base: Path, mode: str, delay: float,
                  counter: Path) -> tuple[Path, object]:
    art = base / f"artifacts_{mode}"
    log_dir = base / f"logs_{mode}"
    result = run_streamed(
        [PY, "-c", PRODUCER, mode, str(art), str(counter), str(delay)],
        log_dir, f"PRODUCER-{mode.upper()}", timeout_s=60)
    assert result.exit_code == 0, result.tail_excerpt
    return art, result


# --------------------------------------------------------------------------- #
# cache keys
# --------------------------------------------------------------------------- #
_BASE_KW = dict(
    data_catalog_hash="cat-hash-abc",
    symbols=["BTC", "ETH", "SOL"],
    window_start="2024-01-01",
    window_end="2024-03-31",
    bar_type="1h",
    funding_model="native_8h",
    signal_inputs={"lookback": 24, "thresholds": {"up": 0.8, "dn": -0.8}},
)


def test_cache_key_deterministic():
    assert make_cache_key(**_BASE_KW) == make_cache_key(**_BASE_KW)
    key = make_cache_key(**_BASE_KW)
    assert isinstance(key, str) and len(key) == 64


def test_cache_key_order_insensitive_for_dicts_and_symbols():
    shuffled_inputs = {"thresholds": {"dn": -0.8, "up": 0.8}, "lookback": 24}
    reordered = dict(_BASE_KW, symbols=["SOL", "ETH", "BTC"],
                     signal_inputs=shuffled_inputs)
    assert make_cache_key(**reordered) == make_cache_key(**_BASE_KW)


@pytest.mark.parametrize("override", [
    {"data_catalog_hash": "cat-hash-XYZ"},
    {"symbols": ["BTC", "ETH"]},
    {"symbols": ["BTC", "ETH", "SOL", "BNB"]},
    {"window_start": "2024-01-02"},
    {"window_end": "2024-04-01"},
    {"bar_type": "4h"},
    {"funding_model":"native_1h"},
    {"signal_inputs": {"lookback": 25, "thresholds": {"up": 0.8, "dn": -0.8}}},
])
def test_cache_key_sensitive_to_every_component(override):
    changed = dict(_BASE_KW, **override)
    assert make_cache_key(**changed) != make_cache_key(**_BASE_KW)


def test_cache_key_rejects_non_serializable(tmp_path):
    with pytest.raises(TypeError):
        make_cache_key(**dict(_BASE_KW, signal_inputs={"obj": object()}))
    with pytest.raises(TypeError):
        make_cache_key(**dict(_BASE_KW, signal_inputs=[("a", 1)]))  # not Mapping


# --------------------------------------------------------------------------- #
# process-local isolation
# --------------------------------------------------------------------------- #
def test_process_local_cache_isolated_instances():
    c1, c2 = ProcessLocalCache(), ProcessLocalCache()
    key = "k" * 64
    c1.put(key, {"payload": [1, 2, 3]})
    assert c1.get(key) == {"payload": [1, 2, 3]}
    assert key not in c2                      # second instance shares nothing
    assert c2.get(key) is None
    assert c2.get(key, "missing") == "missing"
    assert len(c2) == 0 and len(c1) == 1
    stats = c1.stats()
    assert stats["cache_mode"] == "process_local"
    assert stats["hits"] == 1 and stats["misses"] == 0
    assert ProcessLocalCache.persists_across_processes is False


def test_process_local_cache_cannot_be_pickled_or_copied():
    cache = ProcessLocalCache()
    cache.put("k", "v")
    with pytest.raises(TypeError):
        pickle.dumps(cache)
    with pytest.raises(TypeError):
        copy.copy(cache)
    with pytest.raises(TypeError):
        copy.deepcopy(cache)


# --------------------------------------------------------------------------- #
# byte-parity helper / manifests
# --------------------------------------------------------------------------- #
def _make_artifacts(root: Path) -> None:
    (root / "nested").mkdir(parents=True)
    (root / "a.txt").write_bytes(b"alpha\n")
    (root / "nested" / "b.bin").write_bytes(bytes(range(256)))


def test_manifest_deterministic_and_nested(tmp_path):
    d1, d2 = tmp_path / "one", tmp_path / "two"
    _make_artifacts(d1)
    _make_artifacts(d2)
    gate = SharedCacheMergeGate()
    m1 = gate.sha256_manifest(d1)
    assert gate.sha256_manifest(d1) == m1          # deterministic
    assert set(m1) == {"a.txt", "nested/b.bin"}
    assert m1["nested/b.bin"] == sha256_file_chunked(d1 / "nested" / "b.bin")
    ok, reason = gate.parity_from_dirs(d1, d2)
    assert ok is True and reason is None
    # empty dirs still compare equal (no hidden files)
    e1, e2 = tmp_path / "e1", tmp_path / "e2"
    e1.mkdir(); e2.mkdir()
    ok, reason = gate.parity_from_dirs(e1, e2)
    assert ok is True


def test_parity_helper_detects_mismatch_naming_rel(tmp_path):
    d1, d2 = tmp_path / "one", tmp_path / "two"
    _make_artifacts(d1)
    _make_artifacts(d2)
    (d2 / "nested" / "b.bin").write_bytes(b"tampered")
    ok, reason = SharedCacheMergeGate.parity_from_dirs(d1, d2)
    assert ok is False
    assert "artifact_manifest_mismatch" in reason
    assert "nested/b.bin" in reason


def test_parity_helper_uncertain_on_missing_dir(tmp_path):
    ok, reason = SharedCacheMergeGate.parity_from_dirs(
        tmp_path / "gone", tmp_path)
    assert ok is None and "parity_manifest_unreadable" in reason


# --------------------------------------------------------------------------- #
# adoption happy path: synthetic producer, cache OFF vs ON
# --------------------------------------------------------------------------- #
def test_gate_adopts_with_full_proofs_and_wall_time_metric(tmp_path):
    counter = tmp_path / "instrumentation" / "raw_read_counter.json"
    off_art, off_res = _run_producer(tmp_path, "off", delay=0.5, counter=counter)
    on_art, on_res = _run_producer(tmp_path, "on", delay=0.05, counter=counter)

    reads = int(json.loads(counter.read_text())["raw_reads"])
    assert reads == 2, "producer should have read 'raw bars' exactly twice"

    decision = adopt_shared_cache(
        parity_dirs=(on_art, off_art),
        repro_all_match=True,
        raw_reads=reads,
        wall_time_cached_s=on_res.duration_s,
        wall_time_uncached_s=off_res.duration_s,
        strict=True,
    )
    assert decision["adopted"] is True, decision["reasons"]
    assert decision["reasons"] == []
    assert decision["advisory_only"] is False
    assert decision["proofs"]["parity_proof"] is True
    assert decision["proofs"]["repro_all_match"] is True
    assert decision["proofs"]["raw_reads"] == 2
    reduction = decision["metrics"]["wall_time_reduction"]
    assert reduction is not None and reduction >= 0.30, reduction
    # honest measurement sanity: cached path really was faster
    assert on_res.duration_s < off_res.duration_s


# --------------------------------------------------------------------------- #
# fail-closed rejections
# --------------------------------------------------------------------------- #
def _full_proof_kwargs(tmp_path):
    """Fresh identical artifact pairs + passing proof values."""
    counter = tmp_path / "ctr.json"
    off_art, off_res = _run_producer(tmp_path / "case", "off", 0.05, counter)
    on_art, on_res = _run_producer(tmp_path / "case", "on", 0.05, counter)
    return dict(
        parity_dirs=(on_art, off_art),
        repro_all_match=True,
        raw_reads=int(json.loads(counter.read_text())["raw_reads"]),
        wall_time_cached_s=on_res.duration_s,
        wall_time_uncached_s=max(off_res.duration_s, 1.5),
    )


def test_gate_rejects_tampered_cache_on_artifact(tmp_path):
    kwargs = _full_proof_kwargs(tmp_path)
    victim = sorted(Path(kwargs["parity_dirs"][0]).rglob("*"))
    target = next(p for p in victim if p.is_file())
    target.write_bytes(target.read_bytes() + b"\ntamper")
    decision = adopt_shared_cache(strict=True, **kwargs)
    assert decision["adopted"] is False
    assert any("artifact_manifest_mismatch" in r for r in decision["reasons"])
    assert decision["proofs"]["parity_proof"] is False


def test_gate_rejects_raw_reads_over_budget():
    gate = SharedCacheMergeGate(max_raw_reads=2)
    decision = gate.evaluate(
        parity_proof=True, repro_all_match=True, raw_reads=3,
        wall_time_cached_s=1.0, wall_time_uncached_s=10.0)
    assert decision["adopted"] is False
    assert any(r.startswith("raw_reads_budget_exceeded:3>2")
               for r in decision["reasons"])


def test_gate_rejects_when_repro_flag_false_or_missing():
    gate = SharedCacheMergeGate()
    false_case = gate.evaluate(parity_proof=True, repro_all_match=False,
                               raw_reads=2,
                               wall_time_cached_s=1, wall_time_uncached_s=10)
    assert false_case["adopted"] is False
    assert any("independent_reproduction_not_all_match" in r
               for r in false_case["reasons"])

    missing_case = gate.evaluate(parity_proof=True, raw_reads=2,
                                 wall_time_cached_s=1, wall_time_uncached_s=10)
    assert missing_case["adopted"] is False
    assert any("repro_all_match_proof_missing_or_uncertain" in r
               for r in missing_case["reasons"])


def test_gate_fail_closed_when_proofs_missing_entirely():
    decision = adopt_shared_cache()  # nothing supplied at all
    assert decision["adopted"] is False
    assert any("parity_proof_missing_or_uncertain" in r
               for r in decision["reasons"])
    assert any("repro_all_match_proof_missing_or_uncertain" in r
               for r in decision["reasons"])
    assert any("raw_reads_counter_missing_or_uncertain" in r
               for r in decision["reasons"])


def test_gate_rejects_below_target_reduction_strict_but_advisory_only_lenient():
    gate = SharedCacheMergeGate(min_wall_time_reduction=0.30)
    proofs = dict(parity_proof=True, repro_all_match=True, raw_reads=2)

    strict_decision = gate.evaluate(
        wall_time_cached_s=9.0, wall_time_uncached_s=10.0,  # ~10% only
        strict=True, **proofs)
    assert strict_decision["adopted"] is False
    assert any(r.startswith("wall_time_reduction_below_target:")
               for r in strict_decision["reasons"])

    lenient = gate.evaluate(
        wall_time_cached_s=9.0, wall_time_uncached_s=10.0,
        strict=False, **proofs)
    assert lenient["adopted"] is True
    assert lenient["advisory_only"] is True
    assert any("advisory_only_strict_false" in note
               for note in lenient["advisory_notes"])

    unknown = gate.evaluate(strict=False, **proofs)   # wall times absent
    assert unknown["adopted"] is True
    assert unknown["metrics"]["wall_time_reduction"] is None
    assert unknown["advisory_only"] is True


def test_gate_rejects_adoption_once_pnl_seen():
    gate = SharedCacheMergeGate()
    decision = gate.evaluate(
        parity_proof=True, repro_all_match=True, raw_reads=1,
        wall_time_cached_s=0.5, wall_time_uncached_s=10.0,
        strict=True, pnl_seen=True)
    assert decision["adopted"] is False
    assert any("pnl_visible_posture_change_forbidden" in r
               for r in decision["reasons"])
