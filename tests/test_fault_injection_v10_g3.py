"""G3 independent fault-injection suite -- sprint V10P-R lane ``v10p-g3-qa``.

Authority/role
--------------
* Producer role ``G3`` (tests + audit artifacts only; NO production edits).
* Bootstrap commit of this lane: ``5bb1a90551c8f7823773af713316a45e0ca070cd``.
* H08 matrix extension: cases **12-20** (owner-authorized, PLAN.md section 3.3
  "H08 items 12-20 need explicit owner-authorized enumeration").  Cases 1-11
  belong to earlier evidence and are deliberately NOT touched here.
* Companion RED suite: ``tests/test_adapter_acceptance_v10_g3.py``
  (adapter-contract tests against ``research.adapter_v10``, RED BY DESIGN until
  G1/G2 integrate).  Everything in THIS file runs against code that already
  exists, so every test here is expected to execute GREEN right now.

Fault construction discipline
-----------------------------
Every test builds its fault DELIBERATELY (bad input, mutated artifact, missing
evidence) and then asserts the system rejects it or marks it fail-closed --
never silently coerces it.  Small detectors/comparators defined below are
**QA-owned verification oracles**, written inside this test module only.  They
are explicitly NOT production code: they exist so the fault contracts can be
executed and so any gap between contract and current production behaviour is
RECORDED as a finding instead of being papered over (see the limitation probes
marked ``recorded_limitation_probe``).

Synthetic fixtures only: no data/ loads, no network, no scored backtest.
"""

from __future__ import annotations

import copy
import json
import math
import os
import pickle
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import pytest

from research.cache_v10 import (
    ProcessLocalCache,
    SharedCacheMergeGate,
    make_cache_key,
    sha256_file_chunked,
)
from research.contract_v10 import BENCHMARKS_V10, STRESS_MATRIX_V10
from research.global_ledger import (
    append_verified,
    digest as ledger_digest,
    snapshot as ledger_snapshot,
    verify_append_only,
)
from research.hyp_a8_m01 import (
    ADVERSE_TICK_SLIP_FLOOR,
    BAR_INTERVAL_NS,
    CAP,
    DAY_NS,
    FORCE_FLAT_REASON,
    FORCE_FLAT_STATUS,
    HoldingSpan,
    M01Bar,
    StressParams,
    TAKER_FEE_FLOOR_BPS,
    apply_stress_filter,
    build_rebalance_schedule,
    chronological_folds,
    derive_holding_spans,
    fill_cost_rate,
    funding_cashflows,
    GROSS_TARGET,
    iso_from_ns,
    normalize_settlements,
    parse_iso_utc_ns,
    payload_sha256,
    rebalance_cost,
    resolve_fill_event,
    stratified_expectancy,
    traded_notional,
)
from research.pit_hooks_v10 import DataIntegrityError, InfoPoint
from research.resource_governor_v10 import (
    MIN_RESERVED_RAM_GB,
    OverCapacityError,
    PromotionLockedError,
    ResourceGovernorV10,
)

#: NOTE: no custom pytest marks are used -- the repo registers none and G3 may
#: not touch pytest configuration (allowlist), so selection is by file name and
#: test-id prefix (``test_h08_``, ``test_bg``, ``test_g15``).

#: Bootstrap HEAD this lane was dispatched from (frozen provenance).
G3_BOOTSTRAP_SHA = "5bb1a90551c8f7823773af713316a45e0ca070cd"

#: H08 case-id -> owning test fragment (single source of truth for the audit).
H08_CASE_MAP: Dict[str, Tuple[str, str]] = {
    # case: (category, detection mechanism summary)
    "12": ("provenance", "exactly-once trial publish gate refuses duplicate digests"),
    "13": ("data", "accrual-coverage detector marks spans without settlements UNAVAILABLE"),
    "14": ("provenance", "chunked sha256 manifest re-check flags mutated artifacts"),
    "16": ("reproduction", "cache key over full input surface makes stale entries unreachable"),
    "17": ("runtime", "resource governor admission control raises OverCapacityError"),
    "15": ("adversarial", "scored-window hash re-check detects any post-cutoff mutation"),
    "18": ("runtime", "finalize guard refuses any run missing a required stress variant"),
    "19": ("adversarial", "cross-fold holding-span leakage detector over purge boundaries"),
    "20": ("reproduction", "exact-equality reproduction comparator flags 1-ulp divergence"),
}


# --------------------------------------------------------------------------- #
# QA-owned failures raised only from QA-owned detectors in this module
# --------------------------------------------------------------------------- #
class QAFaultNotRejected(AssertionError):
    """A deliberately constructed fault was accepted instead of rejected."""


class QADuplicatePublishRefused(ValueError):
    """Second publication attempt for an already-published trial identity."""


class QAPublishAfterFailureForbidden(RuntimeError):
    """Publication attempted for a trial id that previously failed mid-publish."""


class QAPartialStressMatrix(ValueError):
    """Finalization attempted with a required stress variant missing."""


class LeakageDetected(ValueError):
    """A holding span crosses a chronological-fold/purge boundary."""


# --------------------------------------------------------------------------- #
# QA oracle 1: exactly-once publication wrapper over the existing ledger
# --------------------------------------------------------------------------- #
class QAExactlyOncePublisher:
    """QA oracle modelling the BG-6 publication contract.

    Delegates the actual write to :func:`research.global_ledger.append_verified`
    (the only writer) and adds the exactly-once/idempotency layer BG-6 requires:
    one trial identity may ever contribute one row to the denominator.  The
    duplicate/publish-after-failure refusals live HERE because the raw registry
    primitive intentionally keeps no unique constraint (see the
    ``recorded_limitation_probe`` test below -- that gap must be closed by the
    G1 adapter finalizer, not by mutating global_ledger).
    """

    def __init__(self, ledger_path: Path) -> None:
        self._path = Path(ledger_path)
        self.published_digests: Dict[str, str] = {}

    @property
    def path(self) -> Path:
        return self._path

    def publish(self, entry: Mapping[str, Any]) -> Dict[str, Any]:
        experiment_id = str(entry.get("experiment_id", "")).strip()
        if not experiment_id:
            raise ValueError("trial identity required")
        payload_digest = ledger_digest([dict(entry)])
        if experiment_id in self.published_digests:
            raise QADuplicatePublishRefused(
                f"duplicate_trial_publication_refused:{experiment_id}"
            )
        stored = append_verified(dict(entry), self._path)
        self.published_digests[experiment_id] = payload_digest
        return {
            "published": True,
            "experiment_id": experiment_id,
            "entry_digest": payload_digest,
            "stored": stored,
        }

    def mark_failed(self, experiment_id: str) -> None:
        self.published_digests[f"FAILED::{experiment_id}"] = ""

    def publish_after_failure(self, entry: Mapping[str, Any]) -> Dict[str, Any]:
        experiment_id = str(entry.get("experiment_id", "")).strip()
        if f"FAILED::{experiment_id}" in self.published_digests:
            raise QAPublishAfterFailureForbidden(
                f"republish_for_failed_trial_forbidden:{experiment_id}"
            )
        return self.publish(entry)

    def denominator(self) -> int:
        """Distinct scored trials contributing to the statistical denominator."""
        return len(self.published_digests)


# --------------------------------------------------------------------------- #
# QA oracle 2: funding accrual coverage (H08-13)
# --------------------------------------------------------------------------- #
def qa_accrual_coverage_report(
    holdings: Sequence[HoldingSpan],
    settlements: Sequence[Any],
) -> Dict[str, Any]:
    """Mark any held span with NO settlement inside ``(start, end]`` UNAVAILABLE.

    Fail-closed rule under test: a held leg that crosses a candidate settlement
    instant without a published rate must surface as ``unavailable`` -- the
    accrual engine is never allowed to return a silent 0.0 for it.
    """
    stamps = sorted(int(getattr(p, "publish_ts_ns")) for p in settlements)
    unavailable: List[Dict[str, Any]] = []
    covered: List[str] = []
    for span in holdings:
        weight = float(span.signed_weight)
        if weight == 0.0 or int(span.end_ns) <= int(span.start_ns):
            continue
        inside = [t for t in stamps if int(span.start_ns) < t <= int(span.end_ns)]
        if not inside:
            unavailable.append(
                {
                    "symbol": str(span.symbol),
                    "start_ns": int(span.start_ns),
                    "end_ns": int(span.end_ns),
                    "status": "UNAVAILABLE_FAIL_CLOSED",
                    "reason": "no_native_settlement_published_inside_holding_span",
                }
            )
        else:
            covered.append(str(span.symbol))
    return {
        "is_complete": not unavailable,
        "covered_spans": covered,
        "unavailable_spans": unavailable,
    }


# --------------------------------------------------------------------------- #
# QA oracle 3: cross-fold leakage detector (H08-19)
# --------------------------------------------------------------------------- #
def qa_fold_windows(folds: Sequence[Tuple[int, str, Sequence[int]]]) -> Dict[str, Dict[str, int]]:
    """Legal execution window of each fold, in fill-open nanoseconds.

    Window: ``[first_member_open, last_member_close]`` where the close edge is
    the UTC-midnight AFTER the last member day (purge removes every trailing
    member closer than one holding period to the next fold).
    """
    windows: Dict[str, Dict[str, int]] = {}
    for _idx, label, members in folds:
        members = sorted(int(d) for d in members)
        windows[label] = {
            "open_ns": members[0],
            "close_ns": members[-1] + DAY_NS,
        }
    return windows


def qa_assert_no_cross_fold_leakage(
    spans: Sequence[HoldingSpan],
    folds: Sequence[Tuple[int, str, Sequence[int]]],
) -> List[str]:
    """Raise :class:`LeakageDetected` when a span survives past its own fold.

    Frozen rule: the fold whose window contains ``start_ns`` owns the leg; a leg
    may not stay open at or beyond that fold's terminal close (which the purge
    already pushed one holding period ahead of the next fold).  A span that
    starts outside every fold window, or that overlaps two fold windows outright,
    is a violation as well.
    """
    windows = qa_fold_windows(folds)
    violations: List[str] = []
    for span in spans:
        if float(span.signed_weight) == 0.0:
            continue
        start, end = int(span.start_ns), int(span.end_ns)
        overlapping = sorted(
            label for label, w in windows.items()
            if start < w["close_ns"] and end >= w["open_ns"]
        )
        owning = [label for label, w in windows.items() if w["open_ns"] <= start < w["close_ns"]]
        if len(owning) != 1:
            violations.append(
                f"span_{span.symbol}_[{start},{end}]_no_unique_owning_fold_{owning}"
            )
            continue
        owner = owning[0]
        if end > windows[owner]["close_ns"]:
            violations.append(
                f"span_{span.symbol}_[{start},{end}]_held_past_"
                f"{owner}_close_{windows[owner]['close_ns']}"
                + (f"_overlapping_{overlapping}" if len(overlapping) > 1 else "")
            )
    if violations:
        raise LeakageDetected("; ".join(violations))
    return []


# --------------------------------------------------------------------------- #
# QA oracle 4: exact-equality reproduction comparator (H08-20)
# --------------------------------------------------------------------------- #
def qa_exact_reproduction_compare(
    expected: Any, observed: Any, *, path: str = "$"
) -> List[str]:
    """Path-listing comparator requiring EXACT equality of scored surfaces.

    Reproduction proof tolerance is ZERO: a single ULP change in any reported
    float is a mismatch (V10 evidence closure demands byte-stable reruns).
    """
    if isinstance(expected, bool) or isinstance(observed, bool):
        if type(expected) is not type(observed) or expected != observed:
            return [f"{path}:bool_type_or_value_mismatch"]
        return []
    if isinstance(expected, Mapping) and isinstance(observed, Mapping):
        diffs: List[str] = []
        exp_keys, obs_keys = set(expected), set(observed)
        for key in sorted(exp_keys - obs_keys, key=str):
            diffs.append(f"{path}.{key}:missing_from_observed")
        for key in sorted(obs_keys - exp_keys, key=str):
            diffs.append(f"{path}.{key}:unexpected_in_observed")
        for key in sorted(exp_keys & obs_keys, key=str):
            diffs.extend(
                qa_exact_reproduction_compare(
                    expected[key], observed[key], path=f"{path}.{key}"
                )
            )
        return diffs
    if isinstance(expected, (list, tuple)) and isinstance(observed, (list, tuple)):
        if len(expected) != len(observed):
            return [
                f"{path}:sequence_length_mismatch:{len(expected)}!={len(observed)}"
            ]
        out: List[str] = []
        for idx, (e_item, o_item) in enumerate(zip(expected, observed)):
            out.extend(
                qa_exact_reproduction_compare(e_item, o_item, path=f"{path}[{idx}]")
            )
        return out
    if isinstance(expected, float) or isinstance(observed, float):
        if type(expected) is not type(observed):
            return [f"{path}:numeric_type_mismatch"]
        same_bits = False
        if math.isnan(float(expected)) and math.isnan(float(observed)):
            same_bits = True  # NaN == NaN by canonical-reproduction convention
        else:
            same_bits = repr(float(expected)) == repr(float(observed))
        if not same_bits:
            return [
                f"{path}:float_bit_mismatch:{float(expected)!r}!={float(observed)!r}"
            ]
        return []
    if expected != observed or type(expected) is not type(observed):
        return [f"{path}:value_type_or_equality_mismatch"]
    return []


# --------------------------------------------------------------------------- #
# QA oracle 5: refuse-finalize-if-any-required-variant-missing (H08-18)
# --------------------------------------------------------------------------- #
#: Frozen variant identity grammar shared with the acceptance suite:
#:     baseline | fee_slippage_x1_5 | plus_2_ticks | plus_1_event_delay
#:     drop_one_symbol:<SYMBOL> | drop_one_fold:<LABEL>
BASELINE_VARIANT_ID = "baseline"
VARIANT_QUALIFIER_SEPARATOR = ":"


def qa_required_stress_variant_ids(
    cohort_symbols: Sequence[str],
    fold_labels: Sequence[str],
) -> List[str]:
    """Full preregistered stress surface, expanded per cohort symbol/fold."""
    unknown = sorted(set(STRESS_MATRIX_V10) ^ {
        "fee_slippage_x1_5",
        "plus_2_ticks",
        "plus_1_event_delay",
        "drop_one_symbol",
        "drop_one_fold",
    })
    if unknown:  # contract drift guard: the preregistered five are frozen
        raise AssertionError(f"STRESS_MATRIX_V10 drifted: {unknown}")
    required = [BASELINE_VARIANT_ID]
    required += ["fee_slippage_x1_5", "plus_2_ticks", "plus_1_event_delay"]
    required += [
        f"drop_one_symbol{VARIANT_QUALIFIER_SEPARATOR}{sym}"
        for sym in sorted(str(s) for s in cohort_symbols)
    ]
    required += [
        f"drop_one_fold{VARIANT_QUALIFIER_SEPARATOR}{label}"
        for label in [str(x) for x in fold_labels]
    ]
    return required


REQUIRED_FINALIZED_RESULT_KEYS = (
    "schema_version",
    "variant_id",
    "schedule_sha256",
    "metrics",
)


def qa_finalize_stress_guard(
    results_by_variant: Mapping[str, Any],
    required_variant_ids: Sequence[str],
) -> Dict[str, Any]:
    """Refuse finalization unless EVERY required variant produced full output."""
    missing = [
        vid for vid in required_variant_ids
        if results_by_variant.get(vid) is None
    ]
    malformed = [
        vid for vid, payload in results_by_variant.items()
        if payload is not None and any(k not in payload for k in REQUIRED_FINALIZED_RESULT_KEYS)
    ]
    if missing or malformed:
        raise QAPartialStressMatrix(
            f"refuse_finalization:missing={sorted(missing)}:malformed={sorted(malformed)}"
        )
    extras = sorted(set(results_by_variant) - set(required_variant_ids))
    if extras:
        raise QAPartialStressMatrix(
            f"refuse_finalization:undeclared_variants_present:{extras}"
        )
    return {
        "finalized": True,
        "variant_count": len(required_variant_ids),
        "variant_ids": list(required_variant_ids),
    }


# --------------------------------------------------------------------------- #
# Synthetic fixtures (light, deterministic, no data/ access)
# --------------------------------------------------------------------------- #
CLOSE_SHAVE_NS = 100_000
SYNTHETIC_COHORT: Tuple[str, ...] = (
    "ALPHAUSDT", "BETAUSDT", "GAMMAUSDT", "DELTAUSDT", "EPSILONUSDT",
    "ZETAUSDT", "ETAUSDT", "THETAUSDT", "IOTAUSDT", "KAPPAUSDT",
)
PANEL_BASE_DAY = parse_iso_utc_ns("2025-09-03T00:00:00Z") - 4 * DAY_NS
PANEL_WINDOW_START = "2025-09-03T00:00:00Z"
PANEL_WINDOW_END = "2025-09-05T00:00:00Z"


def synth_block_bars(
    *,
    day_start_ns: int,
    flow_fraction: float,
    open_px: float,
    move_fraction: float,
) -> List[M01Bar]:
    """One UTC-day block of 96 completed 15m bars with controlled observables."""
    bars: List[M01Bar] = []
    price = float(open_px)
    growth = (1.0 + float(move_fraction)) ** (1.0 / 96)
    for i in range(96):
        nxt = price * growth
        mid = 0.5 * (price + nxt)
        ts_event = day_start_ns + (i + 1) * BAR_INTERVAL_NS - CLOSE_SHAVE_NS
        jitter = 1.0 + 0.04 * ((i % 5) - 2)
        qty = jitter * 96_000.0 / 96.0 / mid
        bars.append(
            M01Bar(
                ts_event_ns=ts_event,
                ts_init_ns=ts_event,
                open=price,
                high=max(price, nxt) * 1.001,
                low=min(price, nxt) * 0.999,
                close=nxt,
                volume=qty,
                quote_volume=qty * mid,
                count=11 + i % 3,
                taker_buy_quote_volume=float(flow_fraction) * qty * mid,
            )
        )
        price = nxt
    return bars


@pytest.fixture(scope="module")
def synthetic_panel() -> Dict[str, List[M01Bar]]:
    """7 UTC days x 10 symbols x 96 completed bars (~6.7k tiny objects)."""
    panel: Dict[str, List[M01Bar]] = {}
    for si, symbol in enumerate(SYNTHETIC_COHORT):
        bars: List[M01Bar] = []
        price = 100.0 * (1.0 + 0.05 * si)
        for d in range(7):
            chunk = synth_block_bars(
                day_start_ns=PANEL_BASE_DAY + d * DAY_NS,
                flow_fraction=0.45 + 0.02 * si,
                open_px=price,
                move_fraction=0.002 + 0.001 * ((si + d) % 3),
            )
            bars.extend(chunk)
            price = chunk[-1].close
        panel[symbol] = bars
    return panel


T0 = parse_iso_utc_ns("2026-01-01T00:00:00Z")


def _settlement(hour: int, rate: str) -> InfoPoint:
    return InfoPoint(T0 + hour * 3600 * 1_000_000_000, float(Decimal(rate)))


# ========================================================================= #
# H08-12  provenance  -- duplicated publish / publish after failure
# ========================================================================= #
def test_h08_12_duplicate_ledger_write_refused_and_append_only_preserved(tmp_path):
    """Duplicate digest publish MUST be refused once; append-only stays True."""
    ledger_path = tmp_path / "ledger.jsonl"
    publisher = QAExactlyOncePublisher(ledger_path)
    entry = {
        "experiment_id": "v10p_anchor_trial_a",
        "verdict": "PASS",
        "matrix_id": "v10p-anchor-a",
        "kind": "CELL_RESULT",
        "schema": "orca.v10.cell.v1",
        "score_sha256": "a" * 64,
    }

    first = publisher.publish(entry)
    assert first["published"] is True
    snap = ledger_snapshot(ledger_path)
    assert snap["count"] == 1

    fault_entry = dict(entry)          # byte-identical content => same digest
    with pytest.raises(QADuplicatePublishRefused):
        publisher.publish(fault_entry)

    # Fault is REFUSED: nothing else lands, denominator intact, integrity true.
    assert ledger_snapshot(ledger_path)["count"] == 1
    assert publisher.denominator() == 1
    assert verify_append_only(ledger_path) is True


def test_h08_12_publish_after_failure_is_forbidden(tmp_path):
    """A trial that failed mid-publication can never republish the same id."""
    publisher = QAExactlyOncePublisher(tmp_path / "ledger.jsonl")
    entry = {"experiment_id": "v10p_ctrl_cell", "verdict": "PASS"}
    publisher.mark_failed("v10p_ctrl_cell")
    with pytest.raises(QAPublishAfterFailureForbidden):
        publisher.publish_after_failure(entry)
    assert ledger_snapshot(publisher.path)["count"] == 0


def test_h08_12_recorded_limitation_probe_raw_registry_has_no_unique_constraint(tmp_path):
    """recorded_limitation_probe (finding, NOT an accepted behaviour).

    :func:`research.global_ledger.append_verified` enforces append-only
    monotonicity but keeps NO unique-experiment-id constraint, so the RAW
    registry alone cannot satisfy BG-6 "exactly-once publication".  The refusal
    therefore MUST live in the adapter publishing layer (asserted RED-BY-DESIGN
    in ``tests/test_adapter_acceptance_v10_g3.py``).  Recorded here so A1 sees
    the gap explicitly instead of assuming BG-6 closed by global_ledger.
    """
    path = tmp_path / "raw.jsonl"
    entry = {"experiment_id": "dup_probe", "verdict": "FAIL"}
    append_verified(entry, path)
    append_verified(dict(entry), path)   # deliberate duplicate write
    rows = ledger_snapshot(path)["rows"]
    assert len(rows) == 2                     # observed duplication ...
    assert rows[0]["experiment_id"] == rows[1]["experiment_id"]
    assert verify_append_only(path) is True   # ... with integrity intact
    # Same trial content modulo the registry-stamped ``appended_at``: this is the
    # exact identity a BG-6 idempotency layer has to key on.
    def _content(row):
        return {k: v for k, v in row.items() if k != "appended_at"}

    assert ledger_digest([_content(rows[0])]) == ledger_digest([_content(rows[1])])


# ========================================================================= #
# H08-13  data  -- missing/malformed native settlement
# ========================================================================= #
def test_h08_13_missing_settlement_inside_span_marked_unavailable_not_silent_zero():
    """A held span without a published rate must be marked, never silently 0."""
    holdings = [
        HoldingSpan("ETHUSDT", 0.40, T0, T0 + DAY_NS),                 # [0h, 24h]
        HoldingSpan("SOLUSDT", -0.20, T0 + 3 * DAY_NS, T0 + 4 * DAY_NS),  # [72h, 96h]
    ]
    # Deliberate fault: the only published rate falls inside ETH's span, so SOL
    # is held across its whole horizon with NO settlement => UNAVAILABLE.
    settlements = [_settlement(12, "0.0001")]

    report = qa_accrual_coverage_report(holdings, settlements)
    assert report["is_complete"] is False
    assert [entry["symbol"] for entry in report["unavailable_spans"]] == ["SOLUSDT"]
    assert report["covered_spans"] == ["ETHUSDT"]
    for entry in report["unavailable_spans"]:
        assert entry["status"] == "UNAVAILABLE_FAIL_CLOSED"

    # Documented production reality today: funding_cashflows() on a span with
    # no interior settlement returns [] (silent empty).  Recording that the
    # primitive does NOT itself mark UNAVAILABLE proves why the G2 adapter
    # wrapper must add the coverage gate (the RED contract lives in the
    # acceptance suite, test_g15_checked_accrual_marks_unavailable_span).
    silent = funding_cashflows([holdings[1]], settlements)
    assert silent == []

    # Control: publish one rate inside SOL's span and the detector clears it.
    fixed = qa_accrual_coverage_report(
        holdings, settlements + [_settlement(80, "0.0003")]
    )
    assert fixed["is_complete"] is True
    assert fixed["unavailable_spans"] == []


def test_h08_13_duplicate_settlement_stamp_rejected_fail_closed():
    """Duplicate publication timestamps are structurally invalid => raise."""
    spans = [HoldingSpan("ETHUSDT", 0.5, T0, T0 + DAY_NS)]
    with pytest.raises(DataIntegrityError):
        funding_cashflows(spans, [_settlement(8, "0.0001"), _settlement(8, "0.0002")])
    # normalize path exposes the same rejection directly
    with pytest.raises(DataIntegrityError):
        normalize_settlements(
            [InfoPoint(T0, 0.1), InfoPoint(T0 + 1, 0.2), InfoPoint(T0, 0.3)]
        )


def test_h08_13_out_of_order_series_normalized_ascending_never_resorted_silently():
    """normalize sorts ascending; accrual order is settle-time deterministic."""
    points = normalize_settlements(
        [_settlement(16, "0.0002"), _settlement(8, "0.0001")]
    )
    assert [p.publish_ts_ns for p in points] == sorted(
        p.publish_ts_ns for p in points
    )


# ========================================================================= #
# H08-14  provenance  -- stale manifest / hash drift
# ========================================================================= #
def test_h08_14_mutated_artifact_detected_by_chunked_manifest_recheck(tmp_path):
    """sha256_file_chunked must detect ANY post-hoc byte mutation."""
    artifact = tmp_path / "decision_payload.bin"
    original = b'{"arm":"anchor","window":"2025-08-21/2026-08-21","score":0.123456}'
    artifact.write_bytes(original)
    pinned = sha256_file_chunked(artifact)

    artifact.write_bytes(original.replace(b"0.123456", b"0.123457"))
    mutated = sha256_file_chunked(artifact)

    assert pinned != mutated
    assert len(pinned) == len(mutated) == 64

    # Truncation (partial writer crash) is also detected, not silently accepted.
    truncated = tmp_path / "truncated.bin"
    truncated.write_bytes(original[:-8])
    assert sha256_file_chunked(truncated) != pinned


def test_h08_14_chunk_size_does_not_change_digest_streaming_equivalence(tmp_path):
    """Chunked streaming equals whole-file hashing for several chunk sizes."""
    payload = os.urandom(300_001)                      # odd size => partial tail
    target = tmp_path / "blob.bin"
    target.write_bytes(payload)
    reference = __import__("hashlib").sha256(payload).hexdigest()
    for chunk in (1 << 12, 1 << 16, 1 << 20, 300_001):
        assert sha256_file_chunked(target, chunk_size=chunk) == reference


# ========================================================================= #
# H08-16  reproduction  -- stale cache entries unreachable
# ========================================================================= #
def test_h08_16_changed_input_surface_makes_stale_cache_entry_unreachable():
    """Any key-material change invalidates the key; the stale value can't return."""
    base_kwargs = dict(
        data_catalog_hash="cat-sha-A",
        symbols=["SOLUSDT", "ETHUSDT"],
        window_start="2025-08-21T00:00:00Z",
        window_end="2026-08-21T00:00:00Z",
        bar_type="15m_completed_close_stamp",
        funding_model="native_intrarun_settlement",
        signal_inputs={"control_mode": "anchor", "feature_hash": "f-1"},
    )
    cache = ProcessLocalCache()

    stale_key = make_cache_key(**base_kwargs)
    stale_payload = {"pnl": 1.2345678901234567, "arm": "anchor-STALE"}
    cache.put(stale_key, stale_payload)
    assert cache.get(stale_key) == stale_payload       # positive control: hits

    # Fault: identical strategy but the immutable raw input moved one byte.
    drifted_kwargs = dict(base_kwargs, data_catalog_hash="cat-sha-B")
    fresh_key = make_cache_key(**drifted_kwargs)
    assert fresh_key != stale_key                       # key material changed
    assert cache.get(fresh_key, default=None) is None   # stale entry unreachable
    assert cache.stats()["misses"] == 1                 # recorded as a miss

    # Universe ORDER never splits equivalent work (deterministic normalisation).
    reordered = dict(base_kwargs, symbols=["ETHUSDT", "SOLUSDT"])
    assert make_cache_key(**reordered) == stale_key

    # Non-key-material-vs-key-material distinction: signal input change DOES split.
    assert make_cache_key(**{**base_kwargs, "signal_inputs": {"control_mode": "anchor",
                                                             "feature_hash": "f-2"}}) != stale_key


def test_h08_16_process_local_cache_can_never_smuggle_across_processes():
    """Reproduction always constructs a fresh cache: persistence is impossible."""
    cache = ProcessLocalCache()
    cache.put("k", {"x": 1})
    with pytest.raises(TypeError):          # pickling a cache must explode
        pickle.dumps(cache)

    import copy as _copy

    with pytest.raises(TypeError):          # so must copy/deepcopy/route via reduce
        _copy.copy(cache)
    with pytest.raises(TypeError):
        _copy.deepcopy(cache)

    assert cache.persists_across_processes is False
    assert cache.cache_mode == "process_local"


# ========================================================================= #
# H08-17  runtime  -- over-cap launch
# ========================================================================= #
def _governor(**kwargs: Any) -> ResourceGovernorV10:
    defaults: Dict[str, Any] = dict(
        contract_cap=1,
        reserved_ram_gb=MIN_RESERVED_RAM_GB,
        measured_peak_worker_ram_gb=1.0,
        available_ram_gb=8.0,
        available_method="injected_test_fixture",
    )
    defaults.update(kwargs)
    return ResourceGovernorV10(**defaults)


def test_h08_17_effective_cap_zero_rejects_every_worker_admission():
    """RAM-derived safe cap 0 means NOTHING may launch (never overridden)."""
    governor = _governor(contract_cap=1, available_ram_gb=1.5)   # < reserve 2 GB
    assert governor.ram_cap_workers == 0
    assert governor.effective_heavy_workers == 0
    with pytest.raises(OverCapacityError) as excinfo:
        governor.admit_worker(0)
    message = str(excinfo.value)
    assert "effective_heavy_workers=0" in message
    assert "ram_cap=0" in message


def test_h08_17_cap_one_admits_once_then_rejects_second_concurrent_acquire():
    """cap=1: worker 1 admitted, worker 2 refused while slot occupied."""
    governor = _governor(contract_cap=3, available_ram_gb=3.0, measured_peak_worker_ram_gb=1.0)
    assert governor.ram_cap_workers == 1
    assert governor.effective_heavy_workers == 1
    active = 0
    assert governor.admit_worker(active) is True
    active += 1
    with pytest.raises(OverCapacityError):
        governor.admit_worker(active)      # second concurrent acquire


def test_h08_17_two_worker_cap_requires_probe_evidence_and_locks_after_pnl():
    """Promotion past 1 needs THREE consecutive safe probes; PnL freezes it."""
    locked = _governor(contract_cap=4, available_ram_gb=64.0)
    assert locked.effective_heavy_workers == 1            # forced down without proofs
    for _ in range(2):
        locked.record_two_worker_probe(safe=True, detail="probe")
    assert locked.effective_heavy_workers == 1            # only two of three
    locked.record_two_worker_probe(safe=False, detail="unsafe round resets streak")
    locked.record_two_worker_probe(safe=True, detail="restart streak")
    assert locked.consecutive_safe_two_worker_probes == 1

    # RAM-derived cap 2, unlocked by three consecutive safe probes.
    unlocked = _governor(contract_cap=4, available_ram_gb=4.0, measured_peak_worker_ram_gb=1.0)
    assert unlocked.ram_cap_workers == 2
    for _ in range(3):
        unlocked.record_two_worker_probe(safe=True, detail="safe probe")
    assert unlocked.effective_heavy_workers == 2
    unlocked.declare_pnl_visible(note="fixture freeze")   # snapshot = 2
    unlocked.set_contract_cap(4)                          # raise attempt post-PnL
    assert unlocked.effective_heavy_workers == 2          # clamped by snapshot
    with pytest.raises(PromotionLockedError):
        unlocked.record_two_worker_probe(safe=True, detail="try third promotion")


def test_h08_17_invalid_freeze_inputs_fail_closed():
    with pytest.raises(Exception):
        ResourceGovernorV10(
            contract_cap=0,
            reserved_ram_gb=MIN_RESERVED_RAM_GB,
            measured_peak_worker_ram_gb=1.0,
            available_ram_gb=8.0,
        )
    with pytest.raises(Exception):
        _governor(reserved_ram_gb=1.0)                    # macOS/Orca reserve floor
    with pytest.raises(Exception):
        _governor(measured_peak_worker_ram_gb=0.0)


# ========================================================================= #
# H08-18  runtime  -- incomplete stress/finalization artifacts
# ========================================================================= #
def _full_result(variant_id: str) -> Dict[str, Any]:
    return {
        "schema_version": "orca.adapter.v10.result.v1",
        "variant_id": variant_id,
        "schedule_sha256": payload_sha256({"variant_id": variant_id}),
        "metrics": {"expectancy": 0.0, "profit_factor": None},
    }


def test_h08_18_finalization_refused_when_any_required_variant_missing():
    required = qa_required_stress_variant_ids(SYNTHETIC_COHORT, ["F1", "F2", "F3"])
    results = {vid: _full_result(vid) for vid in required}

    assert qa_finalize_stress_guard(results, required)["finalized"] is True   # control

    victim = "drop_one_fold:F2"                        # deliberately delete one cell
    incomplete = {k: v for k, v in results.items() if k != victim}
    with pytest.raises(QAPartialStressMatrix) as excinfo:
        qa_finalize_stress_guard(incomplete, required)
    assert victim in str(excinfo.value)

    malformed = dict(results)
    malformed["baseline"] = {"variant_id": "baseline"}   # keys missing
    with pytest.raises(QAPartialStressMatrix):
        qa_finalize_stress_guard(malformed, required)

    undeclared = dict(results)
    undeclared["invented_day_mean_cell"] = _full_result("invented_day_mean_cell")
    with pytest.raises(QAPartialStressMatrix):           # no unauthorized cells
        qa_finalize_stress_guard(undeclared, required)


def test_h08_18_required_matrix_expands_drop_one_symbol_and_fold_per_member():
    """Every cohort symbol and every fold contributes its own required cell."""
    required = qa_required_stress_variant_ids(["BBBUSDT", "AAAUSDT"], ["F1", "F2", "F3"])
    assert required[:4] == [
        "baseline",
        "fee_slippage_x1_5",
        "plus_2_ticks",
        "plus_1_event_delay",
    ]
    assert [v for v in required if v.startswith("drop_one_symbol")] == [
        "drop_one_symbol:AAAUSDT",
        "drop_one_symbol:BBBUSDT",
    ]
    assert [v for v in required if v.startswith("drop_one_fold")] == [
        "drop_one_fold:F1",
        "drop_one_fold:F2",
        "drop_one_fold:F3",
    ]
    assert len(required) == 4 + 2 + 3
    assert STRESS_MATRIX_V10 == (
        "fee_slippage_x1_5",
        "plus_2_ticks",
        "plus_1_event_delay",
        "drop_one_symbol",
        "drop_one_fold",
    )


def test_h08_18_apply_stress_filter_enforces_min_eligible_and_known_names():
    survivors = apply_stress_filter(SYNTHETIC_COHORT, StressParams(drop_symbols=("BETAUSDT",)))
    assert len(survivors) == len(SYNTHETIC_COHORT) - 1
    assert "BETAUSDT" not in survivors
    with pytest.raises(Exception):   # unknown symbol name outside the cohort
        apply_stress_filter(list(SYNTHETIC_COHORT), StressParams(drop_symbols=("NOTREALUSDT",)))
    small = SYNTHETIC_COHORT[:8]     # MIN_ELIGIBLE == 8: one drop breaks the floor
    assert len(apply_stress_filter(small, StressParams())) == 8
    with pytest.raises(Exception):   # dropping below MIN_ELIGIBLE must fail closed
        apply_stress_filter(small, StressParams(drop_symbols=(small[0],)))


# ========================================================================= #
# H08-15  adversarial  -- post-cutoff mutation of book/window data
# ========================================================================= #
def _synthetic_window_rows() -> List[Dict[str, Any]]:
    """Rows spanning the scored window plus rows beyond its terminal boundary."""
    cutoff = parse_iso_utc_ns("2026-08-21T00:00:00Z")
    late = cutoff + 5 * DAY_NS
    return [
        {
            "action": "OPEN_REBALANCE",
            "decision_ns": cutoff - DAY_NS,
            "status": "OK",
            "weights": [["AAAUSDT", 0.25], ["BBBUSDT", -0.25]],
            "fills": [
                {"symbol": "AAAUSDT", "applied": True,
                 "fill_open_ns": cutoff - DAY_NS,
                 "price": 101.0},
                {"symbol": "BBBUSDT", "applied": True,
                 "fill_open_ns": cutoff - DAY_NS,
                 "price": 51.0},
            ],
        },
        {
            "action": FORCE_FLAT_STATUS,
            "decision_ns": cutoff,
            "status": FORCE_FLAT_STATUS,
            "reason_code": FORCE_FLAT_REASON,
            "weights": [],
            "fills": [
                {"symbol": "AAAUSDT", "applied": True,
                 "fill_open_ns": cutoff,
                 "price": 103.0},
                {"symbol": "BBBUSDT", "applied": True,
                 "fill_open_ns": cutoff,
                 "price": 52.0},
            ],
        },
        {
            "action": "OPEN_REBALANCE",            # AFTER the scored-window cutoff
            "decision_ns": late,
            "status": "OK",
            "weights": [["AAAUSDT", 0.5]],
            "fills": [{"symbol": "AAAUSDT", "applied": True,
                       "fill_open_ns": late, "price": 104.0}],
        },
    ]


def qa_scored_window_slice(rows: Sequence[Mapping[str, Any]]) -> List[Mapping[str, Any]]:
    start = parse_iso_utc_ns("2025-08-21T00:00:00Z")
    end = parse_iso_utc_ns("2026-08-21T00:00:00Z")
    return [row for row in rows if start < int(row["decision_ns"]) <= end]


def test_h08_15_post_cutoff_mutation_cannot_touch_the_scored_window_hash():
    """Mutating data dated after the cutoff leaves the scored hash untouched;
    mutating anything INSIDE the window is detected by hash re-check."""
    rows = _synthetic_window_rows()
    pristine_window = payload_sha256(qa_scored_window_slice(rows))

    # FAULT 1: forge an out-of-window row (post-cutoff tampering attempt).
    forged = copy.deepcopy(rows)
    forged[-1]["fills"][0]["price"] = 999.0
    assert payload_sha256(qa_scored_window_slice(forged)) == pristine_window
    assert payload_sha256(forged) != payload_sha256(rows)      # whole payload DID move

    # FAULT 2: mutate the terminal force-flat row (inside the window).
    broken = copy.deepcopy(rows)
    broken[1]["reason_code"] = "not_the_frozen_reason"
    tampered_slice = payload_sha256(qa_scored_window_slice(broken))
    assert tampered_slice != pristine_window                   # DETECTED

    # Boundary semantics are frozen constants, not free parameters.
    row_flat = qa_scored_window_slice(rows)[-1]
    assert row_flat["reason_code"] == FORCE_FLAT_REASON
    assert row_flat["weights"] == []
    assert payload_sha256({}) != payload_sha256({"a": 1})      # hash sensitivity sanity


def test_h08_15_spans_close_at_the_force_flat_boundary_never_beyond():
    """derive_holding_spans closes legs AT the boundary ( accrual cannot escape )."""
    cutoff = parse_iso_utc_ns("2026-08-21T00:00:00Z")
    rows = [
        {
            "decision_ns": cutoff - DAY_NS,
            "status": "OK",
            "weights": [["AAAUSDT", 0.25]],
            "fills": [{"symbol": "AAAUSDT", "applied": True,
                       "fill_open_ns": cutoff - DAY_NS}],
        },
        {
            "action": FORCE_FLAT_STATUS,
            "decision_ns": cutoff,
            "status": FORCE_FLAT_STATUS,
            "reason_code": FORCE_FLAT_REASON,
            "weights": [],
            "fills": [{"symbol": "AAAUSDT", "applied": True,
                       "fill_open_ns": cutoff}],
        },
    ]
    spans = derive_holding_spans(rows)
    assert len(spans) == 1
    assert spans[0].end_ns == cutoff
    assert spans[0].end_ns <= cutoff                           # never past cutoff
    # Post-cutoff mutation of the tail row must not resurrect a live leg.
    assert all(float(s.signed_weight) != 0.0 for s in spans)


# ========================================================================= #
# H08-19  adversarial  -- cross-fold leakage through purge/embargo
# ========================================================================= #
def _nine_day_folds():
    days = [T0 + i * DAY_NS for i in range(9)]
    return chronological_folds(days, folds=3)


def test_h08_19_span_crossing_fold_purge_boundary_is_detected():
    folds = _nine_day_folds()
    labels = [(idx, label, members) for idx, label, members in folds]

    # Legal: spans fully inside one fold's window.
    legal = [
        HoldingSpan("ETHUSDT", 0.30, members[0], members[-1] + DAY_NS)
        for _, _, members in labels
    ]
    qa_assert_no_cross_fold_leakage(legal, folds)

    # FAULT: one long leg held from the first fold ACROSS the purge gap into F2.
    f1_members = labels[0][2]
    f2_members = labels[1][2]
    leaking = HoldingSpan("ETHUSDT", 0.30, f1_members[0], f2_members[0])
    with pytest.raises(LeakageDetected) as excinfo:
        qa_assert_no_cross_fold_leakage([leaking], folds)
    assert "held_past_F1_close_" in str(excinfo.value)
    assert "overlapping_['F1', 'F2']" in str(excinfo.value)

    # A span that starts in a purge gap has no owning fold at all => violation.
    orphan = HoldingSpan("ETHUSDT", 0.10, f2_members[0] - DAY_NS, f2_members[0])
    with pytest.raises(LeakageDetected):
        qa_assert_no_cross_fold_leakage([orphan], folds)

    # Fold structure itself is disjoint+chronological with a purge gap between.
    windows = qa_fold_windows(folds)
    ordered = [windows[label] for _, label, _ in labels]
    for prev, cur in zip(ordered, ordered[1:]):
        assert prev["close_ns"] <= cur["open_ns"]              # purge >= 1 period
    assert len({w["open_ns"] for w in ordered}) == len(ordered)


def test_h08_19_chronological_fold_partition_properties_hold():
    folds = _nine_day_folds()
    assert [label for _, label, _ in folds] == ["F1", "F2", "F3"]
    seen: List[int] = []
    for _idx, _label, members in folds:
        assert members == sorted(members)
        assert not (set(seen) & set(members))
        seen.extend(members)
    assert seen == sorted(seen)

    dropped = chronological_folds(
        [T0 + i * DAY_NS for i in range(9)],
        folds=3,
        stress=StressParams(dropped_fold_index=1),
    )
    assert [label for _, label, _ in dropped] == ["F1", "F3"]  # exactly that cell


# ========================================================================= #
# H08-20  reproduction  -- near-identical result divergence
# ========================================================================= #
def _result_payload(score: float) -> Dict[str, Any]:
    return {
        "schema_version": "orca.adapter.v10.result.v1",
        "arm": "anchor",
        "metrics": {"expectancy": score, "profit_factor": 1.5, "max_drawdown": 0.02},
        "fold_ids": ["F1", "F2", "F3"],
    }


def test_h08_20_single_float_divergence_flagged():
    first = _result_payload(0.012345678901234566)
    nudged_score = math.nextafter(first["metrics"]["expectancy"], math.inf)
    assert nudged_score != first["metrics"]["expectancy"]      # exactly one ULP
    diverged = _result_payload(nudged_score)

    faults = qa_exact_reproduction_compare(first, diverged)
    assert faults, "1-ULP divergence must be flagged"
    assert faults[0].startswith("$.metrics.expectancy:float_bit_mismatch")

    # Structural drift is caught too.
    shorter = _result_payload(0.012345678901234566)
    shorter["fold_ids"] = ["F1", "F2"]
    assert "$.fold_ids:sequence_length_mismatch:3!=2" in qa_exact_reproduction_compare(
        first, shorter
    )
    missing_arm = _result_payload(0.012345678901234566)
    del missing_arm["arm"]
    assert any("arm:missing_from_observed" in f
               for f in qa_exact_reproduction_compare(first, missing_arm))


def test_h08_20_identical_results_compare_clean_and_gate_reads_are_real():
    payload = _result_payload(-0.0042)
    assert qa_exact_reproduction_compare(payload, payload) == []
    clone = json.loads(json.dumps(payload))
    assert qa_exact_reproduction_compare(payload, clone) == []

    # Real-module tie-in: the strict merge gate rejects stale-read budgets even
    # when every other proof is perfect (cache must stay DISABLED otherwise).
    decision = SharedCacheMergeGate().evaluate(
        parity_proof=True,
        repro_all_match=True,
        raw_reads=18,
        wall_time_cached_s=1.0,
        wall_time_uncached_s=10.0,
        strict=True,
    )
    assert decision["adopted"] is False
    assert f"raw_reads_budget_exceeded:18>2" in decision["reasons"]


# ========================================================================= #
# BG-1 support: independent metric oracle against real primitives
# ========================================================================= #
def qa_fold_metrics_oracle(returns: Sequence[float]) -> Dict[str, float]:
    """Independent BG-1 oracle (hand-verifiable, G3-owned).

    * expectancy = arithmetic mean of unit-gross net daily returns;
    * profit_factor = sum(wins)/abs(sum(losses)), pooled NaN-safe;
    * max_drawdown = worst relative decline of the compounded equity path.
    """
    n = len(returns)
    wins = math.fsum(r for r in returns if r > 0.0)
    losses = math.fsum(r for r in returns if r <= 0.0)
    pf = math.inf if losses == 0.0 else wins / abs(losses)
    equity, peak, mdd = 1.0, 1.0, 0.0
    for r in returns:
        equity *= 1.0 + float(r)
        peak = max(peak, equity)
        mdd = max(mdd, 1.0 - equity / peak)
    return {
        "expectancy": math.fsum(returns) / n,
        "profit_factor": pf,
        "max_drawdown": mdd,
    }


def test_bg1_oracle_matches_hand_computed_fold_values_exactly():
    fold_f1 = [0.01, 0.02, -0.01]
    metrics = qa_fold_metrics_oracle(fold_f1)
    assert metrics["expectancy"] == pytest.approx(float(Decimal("0.02") / Decimal(3)), rel=1e-12)
    assert metrics["profit_factor"] == pytest.approx(3.0, rel=1e-12)
    assert metrics["max_drawdown"] == pytest.approx(0.01, rel=1e-6)

    fold_f2 = [-0.02, 0.04]
    metrics_f2 = qa_fold_metrics_oracle(fold_f2)
    assert metrics_f2["expectancy"] == pytest.approx(0.01, rel=1e-12)
    assert metrics_f2["profit_factor"] == pytest.approx(2.0, rel=1e-12)
    assert metrics_f2["max_drawdown"] == pytest.approx(0.02, rel=1e-6)

    pooled = qa_fold_metrics_oracle(fold_f1 + fold_f2)
    assert pooled["expectancy"] == pytest.approx(0.008, rel=1e-12)
    assert pooled["profit_factor"] == pytest.approx(0.07 / 0.03, rel=1e-12)
    assert 0.0297 <= pooled["max_drawdown"] <= 0.0299          # worst equity dip


def test_bg1_stratified_expectancy_primitive_reports_means_and_sign_flip():
    day_pnl = {1: 0.02, 2: -0.01, 3: 0.04, 4: -0.02}
    low, high = [1, 2], [3, 4]
    verdict = stratified_expectancy(day_pnl, [low, high])
    assert verdict["strata"][0]["mean"] == pytest.approx(0.005, abs=1e-15)
    assert verdict["strata"][1]["mean"] == pytest.approx(0.01, abs=1e-15)
    assert verdict["sign_flip"] is False
    flipped = stratified_expectancy({1: 0.05}, [[1], []])
    assert flipped["sign_flip"] is False                       # empty stratum never flips
    both = stratified_expectancy({1: 0.05, 2: -0.05}, [[1], [2]])
    assert both["sign_flip"] is True


# ========================================================================= #
# BG-2/BG-4/BG-5 support: cost cells, force-flat schedule, benchmark identity
# ========================================================================= #
def test_bg4_cost_stress_cells_hand_verified_on_primitives():
    prices = {"AAAUSDT": 100.0, "BBBUSDT": 200.0}
    ticks = {"AAAUSDT": 0.01, "BBBUSDT": 0.01}
    targets = {"AAAUSDT": 0.30, "BBBUSDT": -0.30}

    baseline = rebalance_cost({}, targets, prices=prices, tick_sizes=ticks)
    # fee 5 bps + 1 adverse tick slippage, charged once per side on |dw|:
    #   AAA 0.30*(0.0005+0.0001) + BBB 0.30*(0.0005+0.00005) = 0.000345
    assert baseline == pytest.approx(float(Decimal("0.000345")), rel=1e-12)
    assert traded_notional({}, targets) == pytest.approx(0.60, abs=1e-15)

    x15 = rebalance_cost({}, targets, prices=prices, tick_sizes=ticks,
                         stress=StressParams(fee_multiplier=1.5))
    assert x15 == pytest.approx(float(Decimal("0.000495")), rel=1e-12)   # fees scale, ticks don't

    p2 = rebalance_cost({}, targets, prices=prices, tick_sizes=ticks,
                        stress=StressParams(tick_slip_ticks=ADVERSE_TICK_SLIP_FLOOR + 2))
    assert p2 == pytest.approx(float(Decimal("0.000435")), rel=1e-12)

    # Baseline stress still charges the 1-tick adverse slippage floor, so it
    # needs a real tick size; ticks are NEVER invented (fail-closed without one).
    assert fill_cost_rate(price=100.0, tick_size=0.01) == pytest.approx(
        TAKER_FEE_FLOOR_BPS * 1e-4 + 1 * 0.01 / 100.0, rel=1e-12
    )
    with pytest.raises(Exception):
        fill_cost_rate(price=100.0, tick_size=None)
    with pytest.raises(Exception):
        fill_cost_rate(price=100.0, tick_size=None,
                       stress=StressParams(tick_slip_ticks=ADVERSE_TICK_SLIP_FLOOR + 2))


def test_bg2_terminal_force_flat_row_is_flat_and_schedule_is_deterministic(
    synthetic_panel,
):
    """Real M01 schedule over a 2-day synthetic window: last row flattens all."""
    schedules = []
    for _ in range(2):                                          # determinism twice
        schedules.append(
            build_rebalance_schedule(
                bars_by_symbol=synthetic_panel,
                window_start_iso=PANEL_WINDOW_START,
                window_end_iso=PANEL_WINDOW_END,
            )
        )
    schedule = schedules[0]
    assert schedule["cohort"] == sorted(SYNTHETIC_COHORT)
    assert schedule["schedule_sha256"] == schedules[1]["schedule_sha256"]

    terminal = schedule["rows"][-1]
    assert terminal["action"] == FORCE_FLAT_STATUS
    assert terminal["reason_code"] == FORCE_FLAT_REASON
    assert terminal["weights"] == []
    assert sum(abs(weight) for _, weight in terminal["weights"]) == 0.0
    assert schedule["final_weights"] == {}

    applied_terminal = [f for f in terminal["fills"] if f.get("applied")]
    assert {entry["target_weight"] for entry in applied_terminal} == {0.0}

    opening_rows = schedule["rows"][:-1]
    assert opening_rows, "an opening rebalance must exist before force-flat"
    for row in opening_rows:
        weights = [abs(weight) for _, weight in row["weights"]]
        assert weights, "an opening row carries a non-empty book"
        assert max(weights) <= CAP + 1e-9                       # PER-SYMBOL cap 0.30
        assert sum(weights) <= GROSS_TARGET + 1e-9              # unit-gross target

    spans = schedule["holding_spans"]
    cutoff = parse_iso_utc_ns(PANEL_WINDOW_END)
    assert spans and all(int(span["end_ns"]) <= cutoff for span in spans)


def test_bg2_fill_events_resolve_at_the_boundary_open_only(synthetic_panel):
    """Fill clock: OPEN of the bar opening exactly at the decision instant."""
    decision_ns = parse_iso_utc_ns("2025-09-04T00:00:00Z")
    event = resolve_fill_event(
        synthetic_panel["ALPHAUSDT"], "ALPHAUSDT", decision_ns=decision_ns
    )
    assert event is not None
    assert event.event_offset == 0
    assert event.decision_ns == decision_ns
    assert event.fill_open_ns <= decision_ns < event.fill_bar_close_ns
    assert event.fill_bar_close_ns - event.fill_open_ns == BAR_INTERVAL_NS

    delayed = resolve_fill_event(
        synthetic_panel["ALPHAUSDT"], "ALPHAUSDT",
        decision_ns=decision_ns, event_delay_events=1,
    )
    assert delayed is not None and delayed.event_offset == 1
    assert delayed.fill_open_ns == event.fill_bar_close_ns
    with pytest.raises(Exception):                              # negative delay invalid
        resolve_fill_event(synthetic_panel["ALPHAUSDT"], "ALPHAUSDT",
                           decision_ns=decision_ns, event_delay_events=-1)


def test_bg5_flat_hard_and_btc_neutral_context_identities():
    """Frozen context-benchmark identities used by the acceptance suite.

    * flat_hard: an all-zero unit-gross return series, right length, expectancy
      exactly 0, profit factor flagged UNDEFINED (no win and no loss bucket);
    * btc_beta_neutral: neutral_ret[i] = pnl[i]/gross[i] - btc[i]*net[i]/gross[i],
      and the gross-exposure accounting identity
      sum(neutral*gross) == sum(pnl) - sum(btc*net) holds exactly.
    """
    n_days = 5
    flat = [0.0] * n_days
    assert len(flat) == n_days and set(flat) == {0.0}
    oracle = qa_fold_metrics_oracle(flat)
    assert oracle["expectancy"] == 0.0
    assert oracle["max_drawdown"] == 0.0
    assert math.isinf(oracle["profit_factor"])                  # flagged, not faked
    assert BENCHMARKS_V10["flat_hard"]["mandatory"] is True
    assert BENCHMARKS_V10["flat_hard"]["role"] == "hard_gate"

    pnl = [100.0, -50.0, 200.0, -100.0]
    gross = [200.0, 200.0, 200.0, 200.0]
    net = [0.0, 0.0, 200.0, 200.0]
    btc = [0.01, -0.02, 0.01, -0.02]
    neutral = [p / g - b * (w / g) for p, g, w, b in zip(pnl, gross, net, btc)]
    assert neutral[0] == pytest.approx(0.5, abs=1e-15)
    assert neutral[1] == pytest.approx(-0.25, abs=1e-15)
    assert neutral[2] == pytest.approx(0.99, rel=1e-12)
    assert neutral[3] == pytest.approx(-0.48, rel=1e-12)
    lhs = sum(n * g for n, g in zip(neutral, gross))
    rhs = sum(pnl) - sum(b * w for b, w in zip(btc, net))
    assert lhs == pytest.approx(rhs, rel=1e-12)                 # exposure consistency


# ========================================================================= #
# G15 support: hand-computed native funding reconciliation on primitives
# ========================================================================= #
def test_g15_long_pays_positive_rate_hand_computed():
    holdings = [HoldingSpan("ETHUSDT", 0.50, T0, T0 + DAY_NS)]
    flows = funding_cashflows(holdings, [_settlement(8, "0.0001"), _settlement(16, "0.0002")])
    assert [f.cashflow_per_unit_capital for f in flows] == [
        pytest.approx(-5e-05, abs=1e-18),
        pytest.approx(-1e-04, abs=1e-18),
    ]
    assert all(f.symbol == "ETHUSDT" for f in flows)
    total = sum(Decimal("-0.5") * Decimal(r) for r in ("0.0001", "0.0002"))
    assert float(total) == pytest.approx(-0.00015, rel=1e-15)
    assert flows[0].signed_weight == 0.5
    # No settlement published => zero accrual rows, coverage detector flags it:
    assert funding_cashflows(holdings, []) == []


def test_g15_short_receives_positive_rate_hand_computed():
    holdings = [HoldingSpan("SOLUSDT", -0.25, T0, T0 + DAY_NS)]
    flows = funding_cashflows(holdings, [_settlement(8, "0.0004")])
    assert len(flows) == 1
    cashflow = flows[0].cashflow_per_unit_capital
    assert cashflow == pytest.approx(+1e-04, rel=1e-12)         # short RECEIVES
    assert cashflow > 0.0
    # Independent Decimal recomputation of the frozen sign convention:
    assert float(Decimal("-1") * Decimal("-0.25") * Decimal("0.0004")) == pytest.approx(
        cashflow, rel=1e-15
    )


def test_g15_mixed_heterogeneous_settlement_cadences_per_symbol():
    """Symbol-native cadences (8h vs 1h) accrue on the SAME horizon differently."""
    day_span_long = HoldingSpan("ETHUSDT", 0.20, T0, T0 + 24 * 3600 * 1_000_000_000)
    cadence_8h = [_settlement(h, "0.0001") for h in (8, 16)]                 # 2 events
    cadence_1h = [_settlement(h, "0.00002") for h in range(1, 25)]           # 24 events
    fast = HoldingSpan("SOLUSDT", -0.30, T0, T0 + 24 * 3600 * 1_000_000_000)

    flows_eth = funding_cashflows([day_span_long], cadence_8h)
    flows_sol = funding_cashflows([fast], cadence_1h)
    assert len(flows_eth) == 2
    assert len(flows_sol) == 24
    eth_total = sum(f.cashflow_per_unit_capital for f in flows_eth)
    sol_total = sum(f.cashflow_per_unit_capital for f in flows_sol)
    assert eth_total == pytest.approx(-0.20 * 0.0002, rel=1e-9)
    assert sol_total == pytest.approx(+0.30 * 24 * 0.00002, rel=1e-9)
    # Heterogeneous cadences on one horizon are NEVER assumed uniform: the two
    # books accrue different totals over the same 24h.
    assert len(flows_eth) != len(flows_sol)

    # Merged multi-symbol book: distinct stamps only (duplicate stamps are a
    # structural fault => DataIntegrityError, covered in the H08-13 test).
    merged = {}
    for point in cadence_8h + cadence_1h:
        merged[int(point.publish_ts_ns)] = point
    combined = funding_cashflows([day_span_long, fast], sorted(merged.values(),
                                                               key=lambda p: p.publish_ts_ns))
    stamps = [(f.settle_ts_ns, f.symbol) for f in combined]
    assert stamps == sorted(stamps)                              # deterministic order
    assert len(combined) == 2 * len(merged)                      # one flow per leg/stamp


def test_g15_no_accrual_before_publish_time_nor_after_span_close():
    """Boundary exclusivity: (start, end]; never before first publish/close."""
    spans = [HoldingSpan("XRPUSDT", 0.10, T0 + DAY_NS, T0 + 2 * DAY_NS)]  # [24h, 48h]
    settlements = [
        _settlement(0, "0.001"),             # BEFORE the span opens: excluded
        _settlement(24, "0.002"),            # == span START: excluded
        _settlement(30, "0.002"),            # strictly inside: ACCRUES
        _settlement(48, "0.0005"),           # == span END: INCLUDED
        _settlement(60, "0.004"),            # after close: excluded
    ]
    flows = funding_cashflows(spans, settlements)
    assert [(f.settle_ts_ns, f.cashflow_per_unit_capital) for f in flows] == [
        (T0 + 30 * 3600 * 1_000_000_000, pytest.approx(-0.0002, rel=1e-12)),
        (T0 + 48 * 3600 * 1_000_000_000, pytest.approx(-0.00005, rel=1e-12)),
    ]
    assert all(
        spans[0].start_ns < f.settle_ts_ns <= spans[0].end_ns for f in flows
    )
