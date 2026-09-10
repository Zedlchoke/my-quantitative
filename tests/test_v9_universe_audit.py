"""Unit tests for the V9 cohort-10 universe + data audit (owner: A2/A3).

MDP-V2R1 A3 remediation: the six former error tests ran the full audit against
REAL host data paths (which the owner cleaned) and crashed in the module
fixture.  They now run the ENGINE (``run_audit_from_bundle``) over the
COMMITTED synthetic fixture bundle under tests/fixtures/v9_universe_audit/
(repo-authored, SYNTHETIC_HAND_COMPUTED / SCHEMA_MINIMAL; no real provider
payload) with the SAME semantic assertions, using hand-computed fixture
values.  Tier-H mutation tests prove the assertions bite; every mutation
operates on a tmp copy of the fixture, never on the committed bytes.

Still covered unchanged: the pure helpers (analyze_funding synthetics,
intersection_range, close_stamp_iso, listing_age_check, pinned loader,
_pinned_exact_volume, gate shape).
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from scripts.v9_universe_audit import (
    FIXTURE_DIR,
    GATE_ID,
    PINNED_SOURCE_MANIFEST_SHA256,
    PINNED_SOURCE_SELECTOR_SHA256,
    REPO_ROOT,
    AuditDescriptor,
    PinVerificationError,
    REAL_FROZEN_CONFIG,
    _pinned_exact_volume,
    close_stamp_iso,
    fixture_descriptor,
    fixture_frozen_config,
    intersection_range,
    listing_age_check,
    load_inputs,
    load_pinned_selection,
    run_audit_from_bundle,
    run_real_historical_audit,
    write_json,
)
from scripts.v8x_crypto_universe_selection import (
    BAR_INTERVAL_S,
    MAX_FUNDING_INTERVAL_S,
    PRE_END_S,
    PRE_START_S,
    SCORED_END_S,
    SCORED_START_S,
    analyze_funding,
    build_corroboration,
)

EXPECTED_DIR = FIXTURE_DIR / "expected"
EXPECTED = tuple(EXPECTED_DIR / name
                 for name in ("manifest.json", "audit.json", "gate.json"))
RUN_NAMES = ("manifest.json", "audit.json", "gate.json")
SELECTOR_PATH = REPO_ROOT / "scripts" / "v8x_crypto_universe_selection.py"

# --------------------------------------------------------------------------- #
# Hand-computed fixture constants (see build_fixture.py for the derivation)
# --------------------------------------------------------------------------- #
AAA = "AAAUSDT"                       # rank 1, carries the documented ETH-like case
HAND_PRE_GAPS = 2784                  # 2880 pre slots - 96 observed
HAND_SCORED_GAPS_GENERIC = 34944      # 35040 scored slots - 96 observed
HAND_SCORED_GAPS_AAA = 34848          # 2784 between-sessions + 32064 ends-before
HAND_SLOTS_CHECKED = 10 * (2880 + 35040)                    # 379200
HAND_GAPS_TOTAL = 9 * (2784 + 34944) + (2784 + 34848)       # 377184
HAND_MEASURED_SCORED = ("2025-08-21T00:15:00Z", "2025-08-22T00:00:00Z")
HAND_FUNDING_IN_SPAN = 1096           # 8h settlements inside [SCORED_START, SCORED_END]
HAND_LISTING_AGE_DAYS = 400.0
BENCH = "BTCUSDT"


# --------------------------------------------------------------------------- #
# Module-scoped fixture: run the ENGINE over the COMMITTED bundle twice
# --------------------------------------------------------------------------- #
def _run_engine_into(out_dir: Path) -> None:
    loaded = load_inputs(fixture_descriptor(repo_root=REPO_ROOT))
    assert loaded.available, loaded.missing
    res = run_audit_from_bundle(loaded)
    for name, key in zip(RUN_NAMES, ("manifest", "audit", "gate")):
        write_json(out_dir / name, res[key])


@pytest.fixture(scope="module")
def rerun_pair(tmp_path_factory):
    """Two independent engine runs over the committed fixture bundle."""
    d1 = tmp_path_factory.mktemp("v9_fx_run1")
    d2 = tmp_path_factory.mktemp("v9_fx_run2")
    _run_engine_into(d1)
    _run_engine_into(d2)
    return d1, d2


@pytest.fixture(scope="module")
def docs(rerun_pair):
    """Parsed (manifest, audit, gate) from the FIRST rerun directory."""
    d1, _ = rerun_pair
    return tuple(json.loads((d1 / n).read_text()) for n in RUN_NAMES)


# --------------------------------------------------------------------------- #
# 1. Deterministic rerun identity
# --------------------------------------------------------------------------- #
def test_deterministic_rerun_byte_identical(rerun_pair):
    d1, d2 = rerun_pair
    for name in RUN_NAMES:
        b1 = (d1 / name).read_bytes()
        b2 = (d2 / name).read_bytes()
        assert b1 == b2, f"{name} differs between runs"


def test_rerun_reproduces_committed_artifact_bytes(rerun_pair):
    """The committed EXPECTED artifacts are exactly what the engine produces
    from the committed fixture bundle."""
    d1, _ = rerun_pair
    for path, name in zip(EXPECTED, RUN_NAMES):
        assert path.exists(), f"committed expected artifact missing: {path}"
        assert (d1 / name).read_bytes() == path.read_bytes(), (
            f"committed expected {name} not reproducible by the engine"
        )


# --------------------------------------------------------------------------- #
# 2. BTC exclusion (benchmark measurement-only)
# --------------------------------------------------------------------------- #
def test_btc_excluded_from_traded_top10(docs):
    manifest, audit, gate = docs
    assert manifest["btc_excluded"] is True
    selected = [c["symbol"] for c in manifest["selected_symbols"]]
    assert len(selected) == 10
    assert BENCH not in selected
    # benchmark context present but flagged measurement-only
    ctx = manifest["btc_benchmark_context_only"]
    assert ctx["symbol"] == BENCH
    assert ctx["excluded_from_ranks_weights_pnl"] is True
    assert ctx["context_summary"]["role"] == (
        "benchmark_measurement_only_excluded_from_ranking")
    # normalized block keeps BTC as context role, never 'required'
    assert manifest["normalized"]["symbols"][BENCH]["role"] == (
        "benchmark_context_only")
    assert all(
        s["role"] == "required"
        for k, s in manifest["normalized"]["symbols"].items() if k != BENCH
    )
    assert audit["btc_exclusion_check"]["in_selected_ten"] is False
    btc_gate_check = next(
        c for c in gate["checks"]
        if c["id"] == "btc_excluded_from_traded_universe")
    assert btc_gate_check["ok"] is True


# --------------------------------------------------------------------------- #
# 3. Zero unexplained gaps over both windows (hand-computed fixture values)
# --------------------------------------------------------------------------- #
def test_zero_unexplained_gaps_both_windows(docs):
    manifest, audit, gate = docs
    gc = audit["gap_census"]
    assert gc["slots_checked_total"] == HAND_SLOTS_CHECKED
    assert gc["gaps_found_total"] == HAND_GAPS_TOTAL
    assert gc["unexplained_gaps_total"] == 0
    documented_causes = {
        "local_capture_boundary_between_sessions",
        "local_capture_starts_after_window_start",
        "local_capture_ends_before_window_end",
    }
    for run in gc["documented_gap_classes_present"]:
        assert run["explained"] is True
        assert run["cause"] in documented_causes
    # the documented ETH-like capture-boundary class IS present, on the
    # designed carrier symbol, in both windows
    aaa_between = [r for r in gc["documented_gap_classes_present"]
                   if r["symbol"] == AAA
                   and r["cause"] == "local_capture_boundary_between_sessions"]
    assert {r["window"] for r in aaa_between} == {"pre_window", "scored_window"}
    assert gc["non_boundary_explained_classes"] == []
    # per-symbol census consistency with the hand computation
    for sym, blocks in gc["per_symbol"].items():
        pre, scored = blocks["pre_window"], blocks["scored_window"]
        assert pre["expected_15m_slots"] == 2880
        assert scored["expected_15m_slots"] == 35040
        assert pre["gaps_found"] == HAND_PRE_GAPS
        expected_scored = (HAND_SCORED_GAPS_AAA if sym == AAA
                           else HAND_SCORED_GAPS_GENERIC)
        assert scored["gaps_found"] == expected_scored, (sym, "scored gaps")
        assert pre["unexplained_gaps"] == 0
        assert scored["unexplained_gaps"] == 0, (sym, "unexplained")
    # selected_symbols census fields agree with the pinned hand values
    for c in manifest["selected_symbols"]:
        assert c["census_pre_window_gaps"] == HAND_PRE_GAPS
        assert c["census_scored_window_gaps"] == (
            HAND_SCORED_GAPS_AAA if c["symbol"] == AAA
            else HAND_SCORED_GAPS_GENERIC)
        assert c["census_scored_window_unexplained"] == 0
    gate_check = next(
        c for c in gate["checks"]
        if c["id"] == "gap_census_unexplained_zero_both_windows")
    assert gate_check["ok"] is True
    btc_tot = gc["btc_context_totals"]
    assert btc_tot == {"slots_checked": 37920, "gaps_found": 37728,
                       "unexplained_gaps": 0}


def test_window_constants_and_measured_scored_window(docs):
    manifest, audit, _ = docs
    pre = audit["windows"]["pre_window"]
    assert (pre["start_utc"], pre["end_utc"]) == (
        "2025-07-22T00:00:00Z", "2025-08-21T00:00:00Z")
    contract = audit["windows"]["scored_window_contract"]
    assert (contract["start_utc"], contract["end_utc"]) == (
        "2025-08-21T00:00:00Z", "2026-08-21T00:00:00Z")
    measured = manifest["scored_window"]
    assert measured["start_utc"] >= contract["start_utc"]
    assert measured["end_utc"] <= contract["end_utc"]
    assert measured["start_utc"] < measured["end_utc"]
    # hand-computed measured common window over the fixture coverage
    assert (measured["start_utc"], measured["end_utc"]) == HAND_MEASURED_SCORED
    assert measured["start_utc"] == close_stamp_iso(SCORED_START_S)
    assert measured["end_utc"] == close_stamp_iso(
        SCORED_START_S + 95 * BAR_INTERVAL_S)


# --------------------------------------------------------------------------- #
# Tier-H mutation machinery (tmp copies only; committed bytes never touched)
# --------------------------------------------------------------------------- #
def _mutated_descriptor(tmp_path, mutate_manifest=None, mutate_files=None):
    """Copy the committed fixture into tmp, apply mutations, return a
    descriptor over the copy with a recomputed pinned-manifest sha."""
    dst = tmp_path / "fx"
    shutil.copytree(
        FIXTURE_DIR, dst,
        ignore=shutil.ignore_patterns("build_fixture.py", "fixture_entries.json",
                                      "__pycache__"))
    pinned = dst / "pinned_selection_manifest.json"
    if mutate_files is not None:
        mutate_files(dst)
    if mutate_manifest is not None:
        m = json.loads(pinned.read_text())
        mutate_manifest(m)
        pinned.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n")
    return AuditDescriptor(
        repo_root=REPO_ROOT,
        catalog_root=dst / "catalog_root",
        funding_root=dst / "funding",
        pinned_manifest_path=pinned,
        pinned_manifest_sha256=hashlib.sha256(pinned.read_bytes()).hexdigest(),
        selector_path=SELECTOR_PATH,
        pinned_selector_sha256=PINNED_SOURCE_SELECTOR_SHA256,
        frozen_config=fixture_frozen_config(),
        pit_provider="instrument_parquet",
    )


def _run_mutated(tmp_path, **kwargs):
    loaded = load_inputs(_mutated_descriptor(tmp_path, **kwargs))
    assert loaded.available, loaded.missing
    return run_audit_from_bundle(loaded)


# (a) BTC added to the selected set -> btc exclusion gate fails
def test_mutation_btc_in_selected_breaks_btc_gate(tmp_path):
    def mutate(m):
        for c in m["chosen_top10"]:
            if c["symbol"] == "JJJUSDT":
                c["symbol"] = BENCH
                c["instrument_id"] = f"{BENCH}-PERP.BINANCE"

    res = _run_mutated(tmp_path, mutate_manifest=mutate)
    gate, audit = res["gate"], res["audit"]
    check = next(c for c in gate["checks"]
                 if c["id"] == "btc_excluded_from_traded_universe")
    assert check["ok"] is False
    assert gate["status"] == "FAIL_BTC_EXCLUSION_BROKEN"
    assert audit["btc_exclusion_check"]["in_selected_ten"] is True
    assert BENCH in gate["selected_symbols"]


# (b) one required bar removed -> interior unexplained gap -> census + gate fail
def test_mutation_removed_bar_creates_unexplained_gap(tmp_path):
    def mutate_files(dst):
        f = (dst / "catalog_root" / "data" / "binance_bar" /
             "EEEUSDT-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL" /
             "eeeusdt-scored-0001.parquet")
        import pyarrow as pa
        import pyarrow.parquet as pq

        t = pq.read_table(f)
        pq.write_table(pa.concat_tables([t.slice(0, 10), t.slice(11)]), f)

    res = _run_mutated(tmp_path, mutate_files=mutate_files)
    gate, audit = res["gate"], res["audit"]
    gc = audit["gap_census"]
    assert gc["unexplained_gaps_total"] == 1
    eee_scored = gc["per_symbol"]["EEEUSDT"]["scored_window"]
    assert eee_scored["gaps_found"] == HAND_SCORED_GAPS_GENERIC + 1
    assert eee_scored["unexplained_gaps"] == 1
    unexplained_runs = [r for r in eee_scored["gap_runs"] if not r["explained"]]
    assert len(unexplained_runs) == 1
    assert unexplained_runs[0]["cause"] == (
        "unexplained_hole_inside_single_capture_session")
    gap_check = next(c for c in gate["checks"]
                     if c["id"] == "gap_census_unexplained_zero_both_windows")
    drift_check = next(c for c in gate["checks"]
                       if c["id"] == "top10_revalidated_against_current_catalog_bytes")
    assert gap_check["ok"] is False
    assert drift_check["ok"] is False  # census gap count drifted vs pinned
    assert gate["status"] != "PASS"


# (c) one needed funding settlement removed -> completeness fails (typed)
def test_mutation_missing_funding_settlement_fails_completeness(tmp_path):
    def mutate_files(dst):
        fp = dst / "funding" / "FFFUSDT" / "funding.json"
        d = json.loads(fp.read_text())
        del d["rows"][500]  # creates one 16h interval -> illegal
        fp.write_text(json.dumps(d, indent=1, sort_keys=True) + "\n")

    res = _run_mutated(tmp_path, mutate_files=mutate_files)
    gate, audit = res["gate"], res["audit"]
    assert audit["funding_coverage"]["all_selected_complete"] is False
    fff = audit["funding_coverage"]["per_symbol"]["FFFUSDT"]
    assert fff["verdict"] == "INCOMPLETE"
    assert fff["gate_legal_intervals_f2"] is False
    assert 57600 in fff["distinct_interval_seconds"]
    fund_check = next(c for c in gate["checks"]
                      if c["id"] == "funding_held_exposure_completeness_all_selected")
    drift_check = next(c for c in gate["checks"]
                       if c["id"] == "top10_revalidated_against_current_catalog_bytes")
    assert fund_check["ok"] is False
    assert drift_check["ok"] is False  # pinned completeness flag drifted
    assert gate["status"] != "PASS"


# (d) pinned exact volume string altered -> selection drift fail
def test_mutation_altered_pinned_volume_string_drifts(tmp_path):
    def mutate(m):
        for cand in m["candidates_evaluated"]:
            if cand["symbol"] == "GGGUSDT":
                cand["volume"]["median_daily_quote_volume_usdt_exact"] = "0.00"

    res = _run_mutated(tmp_path, mutate_manifest=mutate)
    gate, audit = res["gate"], res["audit"]
    drift_check = next(c for c in gate["checks"]
                       if c["id"] == "top10_revalidated_against_current_catalog_bytes")
    assert drift_check["ok"] is False
    assert gate["status"] == "FAIL_SELECTION_DRIFT"
    drifts = audit["revalidation_vs_pinned"]["drifts"]
    assert any(d["symbol"] == "GGGUSDT"
               and d["field"] == "median_daily_quote_volume_usdt_exact"
               and d["pinned"] == "0.00"
               and d["current"] == "22128.0" for d in drifts)  # 96 x 230.5
    assert audit["revalidation_vs_pinned"]["matched"] is False


# (e) output invariant across two cwd values and two PYTHONHASHSEED values
def test_output_invariant_across_cwd_and_hashseed(tmp_path):
    runner = textwrap.dedent("""
        import sys
        from pathlib import Path
        sys.path.insert(0, sys.argv[1])
        from scripts.v9_universe_audit import (
            fixture_descriptor, load_inputs, run_audit_from_bundle, write_json)
        loaded = load_inputs(fixture_descriptor(repo_root=Path(sys.argv[1])))
        assert loaded.available, loaded.missing
        res = run_audit_from_bundle(loaded)
        out = Path(sys.argv[2])
        for name, key in (("manifest.json", "manifest"),
                          ("audit.json", "audit"), ("gate.json", "gate")):
            write_json(out / name, res[key])
    """)
    runs = []
    for i, (cwd, seed) in enumerate([(REPO_ROOT, "0"), (tmp_path, "12345")]):
        out = tmp_path / f"inv{i}"
        out.mkdir()
        env = dict(os.environ, PYTHONHASHSEED=seed)
        subprocess.run([sys.executable, "-c", runner, str(REPO_ROOT), str(out)],
                       cwd=cwd, env=env, check=True)
        runs.append(out)
    o1, o2 = runs
    for name in RUN_NAMES:
        assert (o1 / name).read_bytes() == (o2 / name).read_bytes(), (
            f"{name} is not invariant across cwd/PYTHONHASHSEED")


# --------------------------------------------------------------------------- #
# Tier-R availability behavior (engine function; absent tmp data paths)
# --------------------------------------------------------------------------- #
def test_run_real_historical_audit_absent_data_writes_availability_artifact(
        tmp_path):
    descriptor = AuditDescriptor(
        repo_root=REPO_ROOT,
        catalog_root=tmp_path / "absent_catalog",
        funding_root=tmp_path / "absent_funding",
        pinned_manifest_path=REPO_ROOT / "data" / "v8x_manifests" /
        "crypto_universe_selection.json",
        pinned_manifest_sha256=PINNED_SOURCE_MANIFEST_SHA256,
        selector_path=SELECTOR_PATH,
        pinned_selector_sha256=PINNED_SOURCE_SELECTOR_SHA256,
        frozen_config=REAL_FROZEN_CONFIG,
    )
    out_dir = tmp_path / "tier_r_out"
    outcome = run_real_historical_audit(descriptor, out_dir=out_dir)
    assert outcome["verdict"] == "NOT_RUN_DATA_UNAVAILABLE"
    artifact = json.loads(
        Path(outcome["availability_artifact_path"]).read_text())
    assert artifact["verdict"] == "NOT_RUN_DATA_UNAVAILABLE"
    assert "catalog_root not found" in artifact["exact_blocker"]
    assert "funding_root not found" in artifact["exact_blocker"]
    assert artifact["offline_assertion"]["network_access_used"] is False
    assert artifact["offline_assertion"]["provider_api_calls"] == 0
    assert artifact["invocation"]["host"]
    assert artifact["invocation"]["code_sha256"]
    # zero-mutation hashes of the existing legacy states
    for relpath in ("data/v9_manifests/universe_selection_v9.json",
                    "research/audits/v9p/data_audit_v9.json",
                    "research/audits/v9p/t02_gate_v9.json"):
        assert relpath in artifact["legacy_state_hashes"]
    # never a fake manifest/audit/gate
    for name in ("universe_selection_v9.json", "data_audit_v9.json",
                 "t02_gate_v9.json"):
        assert not (out_dir / name).exists()


# --------------------------------------------------------------------------- #
# Committed-fixture integrity (governance fragment covers every file)
# --------------------------------------------------------------------------- #
def test_fixture_entries_cover_every_committed_file():
    entries = json.loads((FIXTURE_DIR / "fixture_entries.json").read_text())
    by_path = {e["path"]: e for e in entries["entries"]}
    seen = set()
    for p in sorted(FIXTURE_DIR.rglob("*")):
        if not p.is_file() or p.name == "fixture_entries.json":
            continue
        if "__pycache__" in p.parts:
            continue
        rel = p.relative_to(REPO_ROOT).as_posix()
        seen.add(rel)
        entry = by_path.get(rel)
        assert entry is not None, f"fixture file missing from entries: {rel}"
        assert entry["sha256"] == hashlib.sha256(p.read_bytes()).hexdigest()
        assert entry["license_authority"] == "repo-authored synthetic"
        assert entry["contains_real_provider_payload"] is False
        assert entry["contains_secret"] is False
    assert seen == set(by_path), (
        set(by_path).symmetric_difference(seen))


# --------------------------------------------------------------------------- #
# 4. Funding held-exposure completeness checker (synthetic bundles)
# --------------------------------------------------------------------------- #
EIGHT_H_MS = MAX_FUNDING_INTERVAL_S * 1000
HOUR_MS = 3_600_000


def _rows(times_ms):
    return [{"fundingTime": int(t), "fundingRate": "0.00010000",
             "markPrice": "1.0"} for t in times_ms]


def _span_series(step_ms=EIGHT_H_MS, drop=None):
    """Settlements covering [SCORED_START - 8h, SCORED_END] inclusive."""
    start = (SCORED_START_S * 1000) - EIGHT_H_MS
    end = SCORED_END_S * 1000
    times = list(range(start, end + step_ms, step_ms))
    if drop is not None:
        del times[drop]
    return times


def test_funding_checker_complete_bundle_passes_all_gates():
    res = analyze_funding(_rows(_span_series()), {})
    assert res["complete"] is True
    assert res["gate_sorted_unique_f1"] is True
    assert res["gate_legal_intervals_f2"] is True
    assert res["gate_boundary_coverage_f3"] is True
    assert res["flagged_interval_steps"] == []
    assert res["settlements_in_exposure_span"] >= 1090


def test_funding_checker_missing_settlement_breaks_legality():
    # dropping one 8h settlement creates a 16h interval -> illegal -> fail
    res = analyze_funding(_rows(_span_series(drop=500)), {})
    assert res["complete"] is False
    assert res["gate_legal_intervals_f2"] is False
    assert 57600 in res["distinct_interval_seconds"]


def test_funding_checker_duplicate_timestamps_fail():
    times = _span_series()
    times.insert(300, times[300])  # exact duplicate stamp
    res = analyze_funding(_rows(sorted(times)), {})
    assert res["duplicate_timestamps"] >= 1
    assert res["gate_sorted_unique_f1"] is False
    assert res["complete"] is False


def test_funding_checker_head_boundary_shortfall_fails():
    # first settlement arrives AFTER exposure_start + 8h -> f3 fails
    times = _span_series()[3:]
    res = analyze_funding(_rows(times), {})
    assert res["gate_boundary_coverage_f3"] is False
    assert res["complete"] is False


def test_funding_checker_tail_boundary_shortfall_fails():
    times = _span_series()[:-3]
    res = analyze_funding(_rows(times), {})
    assert res["gate_boundary_coverage_f3"] is False
    assert res["complete"] is False


def test_funding_checker_empty_bundle_fails_closed():
    res = analyze_funding([], {})
    assert res["complete"] is False
    assert res["first_settlement_utc"] is None


def test_corroborated_exchange_wide_step_is_explained():
    # three symbols run an HOURLY cadence but share ONE identical 8h step;
    # cross-symbol corroboration (>=2 sharers) marks it exchange-wide.
    t0 = SCORED_START_S * 1000
    shared_a, shared_b = t0 + 1000 * HOUR_MS, t0 + 1008 * HOUR_MS

    def hourly_with_shared_step():
        times = list(range(t0 - EIGHT_H_MS, SCORED_END_S * 1000, HOUR_MS))
        times = [t for t in times if not (shared_a < t < shared_b)]
        return times

    funding_by_sym = {
        "AAAUSDT": _rows(hourly_with_shared_step()),
        "BBBUSDT": _rows(hourly_with_shared_step()),
        "CCCUSDT": _rows(hourly_with_shared_step()),
    }
    corroborate = build_corroboration(funding_by_sym)
    res = analyze_funding(funding_by_sym["AAAUSDT"], corroborate)
    assert res["cadence_mode_minutes"] == 60
    steps = res["flagged_interval_steps"]
    assert len(steps) == 1
    assert steps[0]["symbols_sharing_identical_step"] >= 2
    assert steps[0]["cause"] == "exchange_wide_funding_interval_step"
    assert steps[0]["explained"] is True
    assert res["complete"] is True


def test_isolated_interval_step_is_unexplained_and_fails():
    t0 = SCORED_START_S * 1000
    shared_a, shared_b = t0 + 1000 * HOUR_MS, t0 + 1008 * HOUR_MS

    def hourly_with_shared_step():
        times = list(range(t0 - EIGHT_H_MS, SCORED_END_S * 1000, HOUR_MS))
        return [t for t in times if not (shared_a < t < shared_b)]

    def plain_hourly():
        return list(range(t0 - EIGHT_H_MS, SCORED_END_S * 1000, HOUR_MS))

    # NO other symbol carries the identical step -> isolated -> unexplained
    corroborate = build_corroboration({
        "AAAUSDT": _rows(hourly_with_shared_step()),
        "BBBUSDT": _rows(plain_hourly()),
    })
    res = analyze_funding(_rows(hourly_with_shared_step()), corroborate)
    steps = res["flagged_interval_steps"]
    assert len(steps) == 1
    assert steps[0]["cause"] == "unexplained_isolated_interval_step"
    assert res["complete"] is False


# --------------------------------------------------------------------------- #
# Supporting pure helpers
# --------------------------------------------------------------------------- #
def test_intersection_range_takes_max_start_min_end():
    r = {"A": (100, 900), "B": (150, 800), "C": (200, 850)}
    assert intersection_range(r) == (200, 800)
    assert intersection_range({}) == (None, None)


def test_close_stamp_iso_adds_bar_interval():
    assert close_stamp_iso(PRE_START_S - BAR_INTERVAL_S) == "2025-07-22T00:00:00Z"
    assert close_stamp_iso(SCORED_END_S - BAR_INTERVAL_S) == "2026-08-21T00:00:00Z"


def test_listing_age_check_gate_at_365d():
    cutoff_ok_inst = {"onboard_date_utc": "2024-08-01T00:00:00Z",
                      "onboard_ms": (SCORED_START_S - 400 * 86400) * 1000}
    young_inst = {"onboard_date_utc": "2025-09-01T00:00:00Z",
                  "onboard_ms": (SCORED_START_S + 10 * 86400) * 1000}
    none_inst = {"onboard_date_utc": None, "onboard_ms": None}
    assert listing_age_check(cutoff_ok_inst, SCORED_START_S)["ok"] is True
    assert listing_age_check(young_inst, SCORED_START_S)["ok"] is False
    assert listing_age_check(none_inst, SCORED_START_S)["ok"] is False


def test_load_pinned_selection_rejects_wrong_sha(tmp_path):
    bad_root = tmp_path / "repo"
    (bad_root / "data" / "v8x_manifests").mkdir(parents=True)
    shutil.copy(REPO_ROOT / "data" / "v8x_manifests" /
                "crypto_universe_selection.json",
                bad_root / "data" / "v8x_manifests" /
                "crypto_universe_selection.json")
    with pytest.raises(PinVerificationError):
        load_pinned_selection(repo_root=bad_root,
                              pinned_manifest_sha256="0" * 64)


def test_pinned_selection_loader_returns_verified_source():
    pinned, source_block = load_pinned_selection()
    assert pinned["schema_version"] == "2.0.0"
    assert source_block["sha256"] == (
        "e73c703f5fb4dea7ff0c6c2c6c8c756b12218fa1960bf46c0ebb2509abb56376")
    assert len(pinned["chosen_top10"]) == 10
    assert "BTCUSDT" not in [c["symbol"] for c in pinned["chosen_top10"]]


def test_pinned_exact_volume_lookup_matches_chosen_entry():
    pinned, _ = load_pinned_selection()
    entry = pinned["chosen_top10"][0]
    expected = next(
        c["volume"]["median_daily_quote_volume_usdt_exact"]
        for c in pinned["candidates_evaluated"]
        if c["symbol"] == entry["symbol"])
    assert _pinned_exact_volume(pinned, entry["symbol"]) == expected
    with pytest.raises(KeyError):
        _pinned_exact_volume(pinned, "NOTAREALSYMBOL")


# --------------------------------------------------------------------------- #
# Gate document shape
# --------------------------------------------------------------------------- #
def test_gate_document_shape_and_status(docs):
    _, _, gate = docs
    assert gate["artifact"] == "t02_gate_v9"
    assert gate["gate"] == GATE_ID == "P03/P04"
    assert gate["status"] == "PASS", [
        c for c in gate["checks"] if not c["ok"]]
    ids = [c["id"] for c in gate["checks"]]
    assert len(ids) == len(set(ids))
    for key in ("selected_symbols", "btc_excluded", "normalized_manifest_sha256"):
        assert key in gate
