"""F5 structured doctor waiver tests (MARKET-DATA-PLANE-V2 freeze F5).

Frozen behavior under test:
  - waiver record schema (exact field names, all mandatory, waiver_id =
    sha256 content id of the record minus waiver_id, optional supersedes);
  - loader validates every record and FAILS CLOSED on malformed ones;
  - append-only supersession transition coherence (a SUPERSEDED record
    must be referenced; supersedes targets must exist; an ACTIVE record
    may not be superseded by an EXPIRED one);
  - doctor integration: an exact-detail-digest ACTIVE unexpired waiver on
    a HIGH finding relabels it WAIVED_HIGH (severity HIGH retained,
    visible, never PASS, never dropped); mismatched digest or expired
    waivers leave the finding HIGH untouched; doctor stays read-only.

All doctor cases run on hermetic tmp_path fixture trees (never the live
tree); Path.home is monkeypatched so the heavy-lock read is sandboxed too.
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))

from governance import doctor, doctor_waivers as dw  # noqa: E402


# ----------------------------------------------------------------- helpers

def _waiver_record(**over):
    rec = {
        "finding_kind": "CONTROL_STATE_DRIFT",
        "severity": "HIGH",
        "finding_digest": dw.finding_digest("some exact finding detail"),
        "classification": "pre-existing foreign-cycle staging drift, out of "
                          "cycle scope",
        "evidence_reference": "research/control/market_data_plane_v1_run/"
                              "gates/M0_doctor_snapshot.json",
        "approver_authority": "plans/PLAN_market_data_plane_v2.md sec 14 "
                              "(cycle owner)",
        "created_utc": "2026-09-10T03:00:00Z",
        "expiry_utc_or_terminal_event": "2099-01-01T00:00:00Z",
        "status": "ACTIVE",
    }
    rec.update(over)
    return rec


def _waiver_for(kind: str, detail: str, **over):
    rec = _waiver_record(finding_kind=kind,
                         finding_digest=dw.finding_digest(detail), **over)
    rec.pop("waiver_id", None)
    return rec


def _expired_record(**over):
    """An honestly-recorded EXPIRED waiver: created before its expiry."""
    return _waiver_record(status="EXPIRED",
                          created_utc="2000-01-01T00:00:00Z",
                          expiry_utc_or_terminal_event="2001-01-01T00:00:00Z",
                          **over)


def _write_waiver(tmp_path: Path, name: str, record: dict) -> Path:
    path = tmp_path / "store" / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=1))
    return path


def _active_cycles_drift_detail(root: Path) -> str:
    """The one HIGH finding guaranteed on a bare tmp root: the missing
    plans/ACTIVE_CYCLES.json CONTROL_STATE_DRIFT."""
    matches = [d for k, d in doctor.check(root=root, ps_lines=[])
               if k == "CONTROL_STATE_DRIFT" and d.startswith("ACTIVE_CYCLES")]
    assert len(matches) == 1, "fixture root must yield exactly one " \
                              "ACTIVE_CYCLES CONTROL_STATE_DRIFT"
    return matches[0]


# ------------------------------------------------------------------ digests

def test_finding_digest_is_sha256_of_exact_detail():
    detail = "ACTIVE_CYCLES.json: [Errno 2] No such file or directory"
    assert dw.finding_digest(detail) == \
        hashlib.sha256(detail.encode("utf-8")).hexdigest()
    assert dw.finding_digest("a") != dw.finding_digest("a ")  # exact bytes


def test_finding_digest_rejects_non_string():
    with pytest.raises(dw.WaiverValidationError):
        dw.finding_digest(b"bytes")


# -------------------------------------------------------------- validation

def test_validate_waiver_mints_deterministic_content_id():
    rec = _waiver_record()
    out1 = dw.validate_waiver(rec)
    out2 = dw.validate_waiver(rec)
    assert out1["waiver_id"] == out2["waiver_id"]
    assert len(out1["waiver_id"]) == 64
    int(out1["waiver_id"], 16)  # 64-hex
    expected = hashlib.sha256(json.dumps(
        rec, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False).encode("utf-8")).hexdigest()
    assert out1["waiver_id"] == expected


def test_validate_waiver_does_not_mutate_input():
    rec = _waiver_record()
    before = copy.deepcopy(rec)
    dw.validate_waiver(rec)
    assert rec == before
    assert "waiver_id" not in rec


def test_validate_waiver_binding_mismatch_fails_closed():
    rec = dw.validate_waiver(_waiver_record())
    tampered = dict(rec, waiver_id="0" * 64)
    with pytest.raises(dw.WaiverValidationError):
        dw.validate_waiver(tampered)


@pytest.mark.parametrize("mutate", [
    {"finding_kind": ""},                                   # empty
    {"finding_kind": None},
    {"severity": "CRITICAL"},                               # not in vocab
    {"finding_digest": "xyz"},                              # not 64-hex
    {"classification": ""},
    {"evidence_reference": "  "},
    {"approver_authority": None},
    {"created_utc": "2026-09-10 03:00:00"},                 # not UTC-Z
    {"expiry_utc_or_terminal_event": ""},
    {"status": "PENDING"},                                  # not in vocab
    {"supersedes": "nothex"},
    {"free_field": 1},                                      # unknown field
    {"created_utc": "2026-09-10T03:00:00Z",
     "expiry_utc_or_terminal_event": "2026-09-10T00:00:00Z"},  # created>expiry
])
def test_validate_waiver_rejects_malformed_records(mutate):
    rec = _waiver_record()
    for key in ("finding_kind", "severity", "finding_digest",
                "classification", "evidence_reference", "approver_authority",
                "created_utc", "expiry_utc_or_terminal_event", "status"):
        if mutate.get(key, 1) is None:
            rec.pop(key, None)  # exercise missing-field rejection too
    rec.update(mutate)
    with pytest.raises(dw.WaiverValidationError):
        dw.validate_waiver(rec)


def test_validate_waiver_missing_field_fails_closed():
    rec = _waiver_record()
    del rec["approver_authority"]
    with pytest.raises(dw.WaiverValidationError):
        dw.validate_waiver(rec)


# --------------------------------------------------------------- effectivity

def test_is_active_and_unexpired():
    rec = dw.validate_waiver(_waiver_record(
        expiry_utc_or_terminal_event="2099-01-01T00:00:00Z"))
    assert dw.is_active_and_unexpired(rec)
    expired = dw.validate_waiver(_expired_record())
    assert not dw.is_active_and_unexpired(expired)
    superseded = dw.validate_waiver(_waiver_record(status="SUPERSEDED"))
    assert not dw.is_active_and_unexpired(superseded)
    # terminal-event reference: governed by terminal reconciliation,
    # never by the wall clock
    terminal = dw.validate_waiver(_waiver_record(
        expiry_utc_or_terminal_event="TERMINAL:MARKET-DATA-PLANE-V1"))
    assert dw.is_active_and_unexpired(terminal)


def test_waiver_applies_requires_exact_kind_and_digest():
    detail = "some exact finding detail"
    w = [_waiver_record()]
    assert dw.waiver_applies(w, "CONTROL_STATE_DRIFT", detail)
    assert not dw.waiver_applies(w, "OTHER_KIND", detail)
    assert not dw.waiver_applies(w, "CONTROL_STATE_DRIFT", detail + " ")
    assert not dw.waiver_applies([_waiver_record(status="EXPIRED")],
                                 "CONTROL_STATE_DRIFT", detail)
    assert not dw.waiver_applies([_expired_record(
        finding_digest=dw.finding_digest(detail))],
        "CONTROL_STATE_DRIFT", detail)


def test_waiver_applies_skips_malformed_entries_fail_closed():
    detail = "some exact finding detail"
    good = _waiver_record()
    malformed = [{"nope": True}, "not-even-a-dict",
                 dict(good, finding_digest="bad")]
    assert not dw.waiver_applies(malformed, "CONTROL_STATE_DRIFT", detail)
    assert dw.waiver_applies(malformed + [good], "CONTROL_STATE_DRIFT", detail)


# -------------------------------------------------------------------- store

def test_load_waivers_returns_validated_records(tmp_path):
    p1 = _write_waiver(tmp_path, "w1", _waiver_record())
    p2 = _write_waiver(tmp_path, "w2", _waiver_record(
        finding_kind="LOCK_OWNER_DEAD",
        expiry_utc_or_terminal_event="TERMINAL:MARKET-DATA-PLANE-V1"))
    out = dw.load_waivers([p1, p2])
    assert [r["waiver_id"] for r in out] == [
        dw.content_id(_waiver_record()),
        dw.content_id(_waiver_record(
            finding_kind="LOCK_OWNER_DEAD",
            expiry_utc_or_terminal_event="TERMINAL:MARKET-DATA-PLANE-V1"))]


def test_load_waivers_fail_closed_on_malformed_json(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not json")
    with pytest.raises(dw.WaiverStoreError, match="bad.json"):
        dw.load_waivers([path])


def test_load_waivers_fail_closed_on_missing_field(tmp_path):
    rec = _waiver_record()
    del rec["classification"]
    path = _write_waiver(tmp_path, "hole", rec)
    with pytest.raises(dw.WaiverStoreError, match="hole"):
        dw.load_waivers([path])


def test_load_waivers_fail_closed_on_tampered_id(tmp_path):
    rec = _waiver_record(waiver_id="f" * 64)
    path = _write_waiver(tmp_path, "tampered", rec)
    with pytest.raises(dw.WaiverStoreError):
        dw.load_waivers([path])


def _supersession_store(tmp_path):
    """The frozen append-only transition: W1 ACTIVE (historical bytes) +
    W2 = NEW record with status SUPERSEDED and supersedes: <W1 id> (the
    retirement record on the old record id) + W3 = NEW ACTIVE record with
    supersedes: <W2 id> (the replacement). Nothing is ever edited."""
    w1 = _waiver_record()
    w1_id = dw.content_id(w1)
    w2 = dict(_waiver_record(), status="SUPERSEDED", supersedes=w1_id)
    w2_id = dw.content_id(w2)
    w3 = _waiver_record(classification="new classification after terminal "
                                       "reconciliation",
                        created_utc="2026-09-10T04:00:00Z",
                        supersedes=w2_id)
    p1 = _write_waiver(tmp_path, "w1_active", w1)
    p2 = _write_waiver(tmp_path, "w2_retired", w2)
    p3 = _write_waiver(tmp_path, "w3_active", w3)
    return [p1, p2, p3], w1, w2, w3


def test_supersession_transition_loads_coherently(tmp_path):
    paths, w1, w2, w3 = _supersession_store(tmp_path)
    out = dw.load_waivers(paths)
    assert len(out) == 3  # historical bytes stay visible in the store view
    by_id = {r["waiver_id"]: r for r in out}
    assert by_id[dw.content_id(w1)]["status"] == "ACTIVE"
    assert by_id[dw.content_id(w2)]["status"] == "SUPERSEDED"
    assert by_id[dw.content_id(w3)]["status"] == "ACTIVE"
    assert by_id[dw.content_id(w2)]["supersedes"] == dw.content_id(w1)
    assert by_id[dw.content_id(w3)]["supersedes"] == dw.content_id(w2)


def test_superseded_by_reference_waiver_no_longer_applies(tmp_path):
    paths, w1, w2, w3 = _supersession_store(tmp_path)
    detail = "some exact finding detail"  # the identity all three share
    # W1's bytes still say ACTIVE, but W2's supersedes reference retires it:
    # without the replacement W3 present the finding is NOT waived anymore
    assert not dw.waiver_applies([w1, w2], "CONTROL_STATE_DRIFT", detail)
    # the in-force replacement W3 (same exact identity) waives it again
    assert dw.waiver_applies(dw.load_waivers(paths),
                             "CONTROL_STATE_DRIFT", detail)


def test_superseded_record_must_be_referenced(tmp_path):
    w1 = _waiver_record(status="SUPERSEDED")  # retirement without replacement
    path = _write_waiver(tmp_path, "orphan", w1)
    with pytest.raises(dw.WaiverStoreError, match="not.*referenced"):
        dw.load_waivers([path])


def test_dangling_supersedes_reference_fails_closed(tmp_path):
    w = _waiver_record(supersedes="a" * 64)
    path = _write_waiver(tmp_path, "dangling", w)
    with pytest.raises(dw.WaiverStoreError, match="dangling"):
        dw.load_waivers([path])


def test_active_record_may_not_be_superseded_by_expired(tmp_path):
    w1 = _waiver_record()
    w_active = _write_waiver(tmp_path, "active", w1)
    w_expired = _write_waiver(tmp_path, "expired", _expired_record(
        supersedes=dw.content_id(w1)))
    with pytest.raises(dw.WaiverStoreError, match="EXPIRED"):
        dw.load_waivers([w_active, w_expired])


def test_duplicate_content_id_fails_closed(tmp_path):
    # waiver_ids are unique content ids: the same record appended twice is
    # a store error (a supersession appends DIFFERENT records, see the
    # transition tests), and divergent content is caught earlier by the
    # waiver_id binding check in validate_waiver
    rec = _waiver_record()
    pa = _write_waiver(tmp_path, "a", rec)
    pb = _write_waiver(tmp_path, "b", _waiver_record())
    assert dw.content_id(rec) == dw.content_id(_waiver_record())
    with pytest.raises(dw.WaiverStoreError, match="duplicate waiver_id"):
        dw.load_waivers([pa, pb])


# ------------------------------------------------------- doctor integration

def _doctor_findings(root: Path, waivers=None):
    return doctor.check_detailed(root=root, ps_lines=[], waivers=waivers)


def test_doctor_waives_exact_high_finding_visibly(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)  # sandbox heavy lock
    detail = _active_cycles_drift_detail(tmp_path)
    baseline = _doctor_findings(tmp_path)
    target = [f for f in baseline
              if f["kind"] == "CONTROL_STATE_DRIFT"
              and f["detail"] == detail]
    assert len(target) == 1 and target[0]["severity"] == "HIGH"

    waivers = [dw.validate_waiver(_waiver_for("CONTROL_STATE_DRIFT", detail))]
    waived = _doctor_findings(tmp_path, waivers)

    assert len(waived) == len(baseline), "waiver must never drop a finding"
    changed = [(b, w) for b, w in zip(baseline, waived) if b != w]
    assert len(changed) == 1
    before, after = changed[0]
    assert before["detail"] == after["detail"] == detail
    assert after["kind"] == "WAIVED_HIGH"
    assert after["severity"] == "HIGH", "severity must be retained"
    assert not any(f["kind"] == "PASS" for f in waived)


def test_doctor_mismatched_digest_or_expired_waiver_leaves_high(tmp_path,
                                                                monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    detail = _active_cycles_drift_detail(tmp_path)
    baseline = _doctor_findings(tmp_path)

    wrong_digest = [dw.validate_waiver(_waiver_for(
        "CONTROL_STATE_DRIFT", detail + "x"))]
    assert _doctor_findings(tmp_path, wrong_digest) == baseline

    expired = [dw.validate_waiver(_expired_record(
        finding_kind="CONTROL_STATE_DRIFT",
        finding_digest=dw.finding_digest(detail)))]
    assert _doctor_findings(tmp_path, expired) == baseline

    wrong_kind = [dw.validate_waiver(_waiver_for("OTHER_KIND", detail))]
    assert _doctor_findings(tmp_path, wrong_kind) == baseline


def test_doctor_waiver_only_applies_to_high_findings(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    root = tmp_path / "ghost"
    root.mkdir()
    (root / "plans").mkdir()
    (root / "plans" / "CYCLE_REGISTRY.json").write_text(json.dumps(
        {"schema": "cycle_registry@1", "cycles": []}))
    (root / "plans" / "ACTIVE_CYCLES.json").write_text(json.dumps(
        {"schema": "active_cycles_projection@1",
         "cycles": [{"cycle_id": "GHOST-CYCLE"}]}))
    baseline = _doctor_findings(root)
    stale = [f for f in baseline if f["kind"] == "STALE_ROUTER_ENTRY"]
    assert stale and stale[0]["severity"] == "LOW"
    detail = stale[0]["detail"]

    waivers = [dw.validate_waiver(_waiver_for("STALE_ROUTER_ENTRY", detail))]
    after = _doctor_findings(root, waivers)
    assert [f for f in after if f["kind"] == "STALE_ROUTER_ENTRY"], \
        "LOW findings are never waived (only HIGH -> WAIVED_HIGH)"
    assert not any(f["kind"] == "WAIVED_HIGH" for f in after)


def test_doctor_check_tuple_surface_waives_visibly(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    detail = _active_cycles_drift_detail(tmp_path)
    waivers = [dw.validate_waiver(_waiver_for("CONTROL_STATE_DRIFT", detail))]
    tuples = doctor.check(root=tmp_path, ps_lines=[], waivers=waivers)
    assert ("WAIVED_HIGH", detail) in tuples
    assert ("CONTROL_STATE_DRIFT", detail) not in tuples
    assert doctor.severity_of("WAIVED_HIGH") == "HIGH"


def test_doctor_default_no_waivers_unchanged(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    detail = _active_cycles_drift_detail(tmp_path)
    assert _doctor_findings(tmp_path) == _doctor_findings(tmp_path, None)
    assert ("CONTROL_STATE_DRIFT", detail) in doctor.check(
        root=tmp_path, ps_lines=[])


def test_doctor_with_waivers_is_read_only(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    detail = _active_cycles_drift_detail(tmp_path)
    waivers = [dw.validate_waiver(_waiver_for("CONTROL_STATE_DRIFT", detail))]
    before = sorted(str(p) for p in tmp_path.rglob("*"))
    _doctor_findings(tmp_path, waivers)
    assert sorted(str(p) for p in tmp_path.rglob("*")) == before, \
        "doctor waiver path must never write any file"


def test_doctor_accepts_store_loaded_waivers(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    detail = _active_cycles_drift_detail(tmp_path)
    record = _waiver_for("CONTROL_STATE_DRIFT", detail,
                         expiry_utc_or_terminal_event=
                         "TERMINAL:MARKET-DATA-PLANE-V1")
    path = _write_waiver(tmp_path, "terminal_bound", record)
    waivers = dw.load_waivers([path])
    waived = _doctor_findings(tmp_path, waivers)
    entry = [f for f in waived if f["detail"] == detail]
    assert len(entry) == 1 and entry[0]["kind"] == "WAIVED_HIGH" \
        and entry[0]["severity"] == "HIGH"
