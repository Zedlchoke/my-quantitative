"""FOREX-FREE-V6 P1 kernel tests (lane p1-a2-kernel).

Synthetic fixtures ONLY — no production outcome data, no network, no PnL,
no profitability pins.  Covers plan §3 P1 (F-TERM-4):

  1. arm_config_digest determinism + sensitivity (any config field change,
     nested or list-order included, changes the digest; key insertion
     order does not) and convention match with the house canonical JSON.
  2. build_scored_ledger_row fail-closed validation: missing/malformed
     arm_config_digest, each identity field missing/empty/None, foreign
     schema tag, and the F-TERM-4 schema tag stamped on every built row.
  3. append_row append-only semantics: byte-identical head prefix on the
     second append, duplicate record_id refusal, foreign head-byte tamper
     refusal via the chained head pin, raced-append (head modified under
     us) certification refusal, non-newline-terminated and unparseable
     pre-existing content refusals.

Run ONLY this file:
  /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest \
      tests/assets/forex_free_v6/test_p1_kernel.py -q
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from research.assets.forex_free_v6 import ledger_row_v6  # noqa: E402

HEX64 = "a" * 64  # valid digest shape for schema-validation fixtures


# -------------------------------------------------------------------------- #
# synthetic fixtures (config specs and structural counters only; no PnL)      #
# -------------------------------------------------------------------------- #
def frozen_config() -> dict:
    """A representative frozen per-arm config projection (whatever the
    freeze carries; the digest is over what is given)."""
    return {
        "proposal_sha256": "c0" * 32,
        "universe": {"pairs": ["EUR/USD", "GBP/USD"], "quote": "USD"},
        "clock": {"decision_clock": "daily", "timezone": "UTC"},
        "warmup": {"warmup_daily_bars": 10},
        "features": {"trailing_return_sum_ny_days": 10, "lags": [1, 2]},
        "entry_exit_fills": {"entry": "next_daily_close",
                             "exit": "daily_close_plus_5",
                             "fills": "next_bar_open"},
        "costs": {"bps_per_side": 1.5, "stress_tier": 1.0},
        "control_spec": {"sham_shift_calendar_days": 7,
                         "staleness_mode": "previous_clock"},
        "falsification_rule": {"rule": "sham_calendar_placebo_mandatory",
                               "refuse_if": "control_ge_0.5x_same_sign"},
    }


def identity_fields(**overrides) -> dict:
    fields = {
        "cycle_id": "FOREX-FREE-V6",
        "family_id": "FXFV6-SYNTH-F1",
        "arm": "anchor",
        "trial_id": "FOREX-FREE-V6/FXFV6-SYNTH-F1/anchor",
        "cell_id": "FXFV6-SYNTH-F1:anchor:tier1.0",
        "code_freeze_sha": "b" * 64,
        "data_snapshot_digest": "c" * 64,
        "cost_tier": 1.0,
    }
    fields.update(overrides)
    return fields


def build_row(record_id: str = "FXFV6-SYNTH-F1:anchor:tier1.0",
              **overrides) -> dict:
    fields = identity_fields()
    fields["arm_config_digest"] = HEX64
    fields["record_id"] = record_id
    fields["n_trades_kept"] = 3          # structural counter, not an outcome
    fields.update(overrides)
    return ledger_row_v6.build_scored_ledger_row(**fields)


def _transform_leaf(value):
    """Change any value: scalars perturbed, lists reversed, dicts recursed."""
    if isinstance(value, bool):
        return not value
    if isinstance(value, (int, float)):
        return value + 1
    if isinstance(value, str):
        return value + "_changed"
    if isinstance(value, list):
        return list(reversed(value))
    if isinstance(value, dict):
        out = copy.deepcopy(value)
        first = next(iter(out))
        out[first] = _transform_leaf(out[first])
        return out
    return None


# -------------------------------------------------------------------------- #
# 1. digest determinism + sensitivity                                        #
# -------------------------------------------------------------------------- #
def test_digest_deterministic_and_order_insensitive():
    cfg = frozen_config()
    d1 = ledger_row_v6.compute_arm_config_digest(cfg)
    d2 = ledger_row_v6.compute_arm_config_digest(copy.deepcopy(cfg))
    assert d1 == d2
    assert len(d1) == 64 and d1 == d1.lower()
    # key insertion order must not matter (sorted-keys canonicalization)
    reordered = {k: cfg[k] for k in reversed(list(cfg.keys()))}
    assert ledger_row_v6.compute_arm_config_digest(reordered) == d1


def test_digest_matches_house_canonical_json_convention():
    cfg = frozen_config()
    expected = hashlib.sha256(json.dumps(
        cfg, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False).encode("utf-8")).hexdigest()
    assert ledger_row_v6.compute_arm_config_digest(cfg) == expected


def test_digest_distinct_on_any_config_field_change():
    cfg = frozen_config()
    base = ledger_row_v6.compute_arm_config_digest(cfg)
    for key in cfg:                                   # every top-level key
        mutated = copy.deepcopy(cfg)
        mutated[key] = _transform_leaf(cfg[key])
        assert mutated != cfg, f"mutation of {key} was a no-op"
        assert ledger_row_v6.compute_arm_config_digest(mutated) != base, (
            f"digest collided after changing {key}")
    # a nested deep leaf (list element inside features.lags)
    deep = copy.deepcopy(cfg)
    deep["features"]["lags"] = [2, 1]
    assert ledger_row_v6.compute_arm_config_digest(deep) != base
    # a nested deep leaf (cost tier)
    deep2 = copy.deepcopy(cfg)
    deep2["costs"]["stress_tier"] = 1.5
    assert ledger_row_v6.compute_arm_config_digest(deep2) != base


def test_digest_refuses_non_dict_and_unserializable():
    with pytest.raises(ledger_row_v6.LedgerRowError) as excinfo:
        ledger_row_v6.compute_arm_config_digest(["not", "a", "dict"])
    assert excinfo.value.code == "NOT_A_DICT"
    with pytest.raises(ledger_row_v6.LedgerRowError) as excinfo:
        ledger_row_v6.compute_arm_config_digest({"bad": object()})
    assert excinfo.value.code == "NOT_JSON_SERIALIZABLE"


# -------------------------------------------------------------------------- #
# 2. row construction fail-closed (F-TERM-4)                                 #
# -------------------------------------------------------------------------- #
def test_build_refuses_missing_arm_config_digest():
    fields = identity_fields()
    fields["record_id"] = "R"
    with pytest.raises(ledger_row_v6.LedgerRowError) as excinfo:
        ledger_row_v6.build_scored_ledger_row(**fields)
    assert excinfo.value.code == "ARM_CONFIG_DIGEST_REQUIRED"


@pytest.mark.parametrize("bad", [
    "", "  ", "ABC" * 21 + "A",            # uppercase hex
    "a" * 63, "a" * 65,                     # wrong length
    "g" * 64,                               # non-hex characters
    123, 4.5, ["a" * 64], {"d": "a" * 64},  # non-str
])
def test_build_refuses_malformed_arm_config_digest(bad):
    fields = identity_fields()
    fields["arm_config_digest"] = bad
    fields["record_id"] = "R"
    with pytest.raises(ledger_row_v6.LedgerRowError) as excinfo:
        ledger_row_v6.build_scored_ledger_row(**fields)
    assert excinfo.value.code == "ARM_CONFIG_DIGEST_INVALID"


@pytest.mark.parametrize("field",
                         list(ledger_row_v6.REQUIRED_IDENTITY_FIELDS))
@pytest.mark.parametrize("mode", ["missing", "empty", "none"])
def test_build_refuses_broken_identity_field(field, mode):
    fields = identity_fields()
    fields["arm_config_digest"] = HEX64
    fields["record_id"] = "R"
    if mode == "missing":
        del fields[field]
    elif mode == "empty":
        fields[field] = ""
    else:
        fields[field] = None
    with pytest.raises(ledger_row_v6.LedgerRowError) as excinfo:
        ledger_row_v6.build_scored_ledger_row(**fields)
    assert excinfo.value.code == "IDENTITY_FIELD_MISSING"
    assert field in str(excinfo.value)


def test_build_stamps_schema_tag_on_every_row():
    row = build_row()
    assert row["schema"] == ledger_row_v6.SCHEMA_TAG
    assert ledger_row_v6.SCHEMA_TAG == "forex_free_v6_scored_ledger_row_v1"
    # every field the V5 baseline carries is a legal column; identity and
    # the F-TERM-4 additions are present
    for name in ledger_row_v6.REQUIRED_IDENTITY_FIELDS:
        assert name in row
    for name in ledger_row_v6.V6_ADDED_FIELDS:
        assert name in row
    assert "arm_config_digest" in ledger_row_v6.V6_ADDED_FIELDS


def test_build_refuses_foreign_schema_tag():
    with pytest.raises(ledger_row_v6.LedgerRowError) as excinfo:
        build_row(schema="forex_free_v3_scored_record_v1")
    assert excinfo.value.code == "SCHEMA_TAG_MISMATCH"


def test_build_digest_carries_through_and_matches_computed():
    cfg = frozen_config()
    digest = ledger_row_v6.compute_arm_config_digest(cfg)
    row = build_row(arm_config_digest=digest)
    assert row["arm_config_digest"] == digest \
        == ledger_row_v6.compute_arm_config_digest(cfg)


def test_v5_baseline_is_the_measured_published_v5_schema():
    # the baseline list is exactly the uniform key set measured from the
    # V5 published scored ledger (3/3 rows) minus nothing, plus nothing
    assert len(ledger_row_v6.V5_BASELINE_ROW_FIELDS) == 45
    assert set(ledger_row_v6.V5_BASELINE_ROW_FIELDS).isdisjoint(
        set(ledger_row_v6.V6_ADDED_FIELDS))
    assert set(ledger_row_v6.REQUIRED_IDENTITY_FIELDS) <= (
        set(ledger_row_v6.V5_BASELINE_ROW_FIELDS)
        | set(ledger_row_v6.V6_ADDED_FIELDS))


# -------------------------------------------------------------------------- #
# 3. append-only publication                                                 #
# -------------------------------------------------------------------------- #
def test_append_prefix_property_and_one_json_line_per_row(tmp_path):
    path = tmp_path / "ledger.jsonl"
    row1 = build_row("R1")
    row2 = build_row("R2")
    ev1 = ledger_row_v6.append_row(str(path), row1)
    assert ev1["bytes_before"] == 0
    assert ev1["bytes_after"] == ev1["appended_bytes"]
    assert ev1["head_bytes_identical"] is True
    assert ev1["lines_in_file"] == 1
    bytes_after_first = path.read_bytes()
    assert bytes_after_first.endswith(b"\n")
    assert bytes_after_first == \
        ledger_row_v6.canonical_json_bytes(row1) + b"\n"

    ev2 = ledger_row_v6.append_row(str(path), row2)
    bytes_after_second = path.read_bytes()
    # byte-identical prefix: the first row's bytes were never modified
    assert bytes_after_second[:len(bytes_after_first)] == bytes_after_first
    assert len(bytes_after_second) == \
        len(bytes_after_first) + ev2["appended_bytes"]
    assert ev2["bytes_before"] == len(bytes_after_first)
    assert ev2["head_sha256_after"] == hashlib.sha256(
        bytes_after_second).hexdigest()
    lines = bytes_after_second.split(b"\n")
    assert len([raw for raw in lines if raw.strip()]) == 2
    assert json.loads(bytes_after_second.splitlines()[0]) == row1
    assert json.loads(bytes_after_second.splitlines()[1]) == row2


def test_append_refuses_duplicate_record_id_and_writes_nothing(tmp_path):
    path = tmp_path / "ledger.jsonl"
    ledger_row_v6.append_row(str(path), build_row("R1"))
    before = path.read_bytes()
    with pytest.raises(ledger_row_v6.LedgerRowError) as excinfo:
        ledger_row_v6.append_row(str(path), build_row("R1"))
    assert excinfo.value.code == "DUPLICATE_RECORD_ID"
    assert path.read_bytes() == before  # refused call wrote nothing


def test_append_requires_record_id(tmp_path):
    row = build_row("R1")
    del row["record_id"]
    with pytest.raises(ledger_row_v6.LedgerRowError) as excinfo:
        ledger_row_v6.append_row(str(tmp_path / "ledger.jsonl"), row)
    assert excinfo.value.code == "RECORD_ID_REQUIRED"


def test_append_refuses_foreign_head_tamper_via_chained_pin(tmp_path):
    path = tmp_path / "ledger.jsonl"
    ev = ledger_row_v6.append_row(str(path), build_row("R1"))
    good = path.read_bytes()
    # a FOREIGN writer flips the first head byte on disk
    tampered = b"Z" + good[1:]
    path.write_bytes(tampered)
    with pytest.raises(ledger_row_v6.LedgerRowError) as excinfo:
        ledger_row_v6.append_row(str(path), build_row("R2"),
                                 expected_head_sha256=ev["head_sha256_after"])
    assert excinfo.value.code == "HEAD_PIN_MISMATCH"
    assert path.read_bytes() == tampered  # refusal happened BEFORE any write


def test_append_certification_refusal_when_head_modified_under_us(
        monkeypatch, tmp_path):
    """Raced append: a foreign writer rewrites the head between our
    pre-write read and our post-append verification read (simulated by
    deterministically tampering the second read).  append_row must refuse
    to CERTIFY the publication (HEAD_BYTES_MODIFIED) instead of returning
    a clean evidence dict."""
    path = tmp_path / "ledger.jsonl"
    ledger_row_v6.append_row(str(path), build_row("R1"))
    real_read = ledger_row_v6._read_bytes
    calls = {"n": 0}

    def racing_read(p):
        calls["n"] += 1
        data = real_read(p)
        if calls["n"] == 2:      # the post-append verification read
            return b"X" + data[1:]
        return data

    monkeypatch.setattr(ledger_row_v6, "_read_bytes", racing_read)
    with pytest.raises(ledger_row_v6.LedgerRowError) as excinfo:
        ledger_row_v6.append_row(str(path), build_row("R2"))
    assert excinfo.value.code == "HEAD_BYTES_MODIFIED"
    assert "head_identical=False" in str(excinfo.value)


def test_append_refuses_non_newline_terminated_existing_file(tmp_path):
    path = tmp_path / "ledger.jsonl"
    path.write_bytes(b'{"record_id": "FOREIGN"}')  # no trailing newline
    with pytest.raises(ledger_row_v6.LedgerRowError) as excinfo:
        ledger_row_v6.append_row(str(path), build_row("R1"))
    assert excinfo.value.code == "LAST_LINE_NOT_TERMINATED"


def test_append_refuses_unparseable_preexisting_line(tmp_path):
    path = tmp_path / "ledger.jsonl"
    path.write_bytes(b"not-json-at-all\n")
    with pytest.raises(ledger_row_v6.LedgerRowError) as excinfo:
        ledger_row_v6.append_row(str(path), build_row("R1"))
    assert excinfo.value.code == "PREEXISTING_ROW_UNPARSEABLE"


def test_append_refuses_preexisting_line_without_record_id(tmp_path):
    path = tmp_path / "ledger.jsonl"
    path.write_bytes(b'{"a": 1}\n')  # valid JSON, no record_id key
    with pytest.raises(ledger_row_v6.LedgerRowError) as excinfo:
        ledger_row_v6.append_row(str(path), build_row("R1"))
    assert excinfo.value.code == "PREEXISTING_ROW_MISSING_RECORD_ID"


def test_append_refuses_stale_pin_for_missing_file(tmp_path):
    missing = tmp_path / "absent.jsonl"
    with pytest.raises(ledger_row_v6.LedgerRowError) as excinfo:
        ledger_row_v6.append_row(str(missing), build_row("R1"),
                                 expected_head_sha256="d" * 64)
    assert excinfo.value.code == "HEAD_PIN_MISMATCH"
    assert not missing.exists()


def test_no_pnl_computed_in_p1_module():
    """Structural statement: the P1 module computes no PnL anywhere — its
    public surface is schema + publication machinery only."""
    public = [n for n in dir(ledger_row_v6) if not n.startswith("_")]
    assert set(ledger_row_v6.__all__) <= set(public)
    assert not any("pnl" in n.lower() for n in public)
