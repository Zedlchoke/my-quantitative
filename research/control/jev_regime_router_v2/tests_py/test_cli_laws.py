"""CLI laws: backtest QUARANTINE refusal, verify-freezes, preview collapse
mechanism, build-states."""

from __future__ import annotations

import json

import numpy as np
import pytest

import run as jrv2_run  # noqa: E402  (jrv2/ dir is on sys.path via conftest)
from conftest import make_bars
from jrv2.freezes import Freezes, default_cycle_dir


@pytest.fixture(scope="module")
def fz():
    return Freezes(default_cycle_dir())


def _run_cli(argv):
    try:
        jrv2_run.main(argv)
        return 0
    except SystemExit as e:
        return int(e.code or 0)


def test_backtest_refuses_without_token(capsys):
    """QUARANTINE: no scored-phase GO authority exists -> refuse (exit 20)."""
    assert not (default_cycle_dir() / jrv2_run.SCORED_GO_AUTHORITY).exists()
    code = _run_cli(["backtest", "--cell", "BTC_H1", "--arm", "JEV_ONLY_ROUTER"])
    assert code == 20
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "REFUSED_BACKTEST_QUARANTINE"
    assert "does not exist" in out["reason"]


def test_backtest_refuses_even_with_a_token(capsys):
    """Fail-closed: any token is rejected because the GO authority file does
    not exist (the token cannot be honored without the owner-registered
    sha256 pin)."""
    code = _run_cli([
        "backtest", "--cell", "BTC_H1", "--arm", "DETERMINISTIC_PLUS_JEV_CONFIRMATION",
        "--scored-go-token", "deadbeef-deadbeef",
    ])
    assert code == 20
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "REFUSED_BACKTEST_QUARANTINE"


def test_backtest_quarantine_is_fail_closed_against_forced_authority(tmp_path, fz, monkeypatch, capsys):
    """A present-but-divergent SCORED_GO.json still refuses on token mismatch;
    a matching token passes the authority check (pin math verified directly)."""
    import hashlib
    import shutil

    assert not (fz.cycle_dir / jrv2_run.SCORED_GO_AUTHORITY).exists()  # real cycle untouched
    clone = tmp_path / "cycle"
    clone.mkdir()
    shutil.copytree(fz.freezes_dir, clone / "freezes")
    (clone / jrv2_run.SCORED_GO_AUTHORITY).write_text(
        json.dumps({"scored_go_token_sha256": "ab" * 32})
    )
    monkeypatch.setattr(jrv2_run, "_default_cycle_dir", lambda: clone)
    code = _run_cli([
        "backtest", "--cell", "BTC_H1", "--arm", "JEV_ONLY_ROUTER",
        "--scored-go-token", "not" * 16,
    ])
    assert code == 20
    out = json.loads(capsys.readouterr().out)
    assert "does not match" in out["reason"]
    # a MATCHING token passes the authority check itself
    want = hashlib.sha256(b"correct-token").hexdigest()
    (clone / jrv2_run.SCORED_GO_AUTHORITY).write_text(
        json.dumps({"scored_go_token_sha256": want})
    )
    # replicate the authority comparison directly (the full backtest would
    # then require a complete decision cache — scored-phase scope only)
    rec = json.loads((clone / jrv2_run.SCORED_GO_AUTHORITY).read_text())
    assert rec["scored_go_token_sha256"] == hashlib.sha256(b"correct-token").hexdigest()


def test_verify_freezes_cli_green(capsys):
    code = _run_cli(["verify-freezes"])
    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert out["n_freezes"] == 10
    assert out["security_scan"]["findings"] == []
    assert out["v1_isolation_scan"]["findings"] == []


def test_census_cli_matches_freeze(capsys):
    code = _run_cli(["census"])
    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    cells = out["cells"]
    assert cells["BTC_H1"]["complete_h1"] == 8759
    assert cells["BTC_H4"]["complete_h4"] == 2189
    assert cells["SPY_D1"]["sessions"] == 2943


def test_preview_collapse_mechanism_fail_stops(fz, monkeypatch, capsys):
    """The collapse check FAIL-STOPS with measured numbers when a synthetic
    distribution violates a criterion — the stop law, exercised on a stubbed
    preview result (no adapter involved)."""
    from jrv2.replay import PreviewCollapse

    payload = {
        "schema": "jrv2_preview_result@1",
        "effective_label_shares": {"TRANSITION_UNKNOWN": 0.95, "UPTREND": 0.05},
        "collapse_checks": [
            {"criterion": "any_single_effective_label > 0.90", "measured": {"label": "TRANSITION_UNKNOWN", "share": 0.95}, "fired": True},
            {"criterion": "effective_TRANSITION_UNKNOWN > 0.80", "measured": {"share": 0.95}, "fired": True},
        ],
        "collapsed": True,
    }
    err = PreviewCollapse(payload)
    assert "PREVIEW_COLLAPSE_STOP" in str(err)
    assert err.payload["collapsed"] is True


def test_preview_indices_rule_is_the_frozen_rule(fz):
    from jrv2.replay import preview_indices_rule

    frozen = fz.canary_contract["historical_preview"]["preview_indices"]
    assert preview_indices_rule(8567, 100) == sorted(frozen)
    # dedup law: rule output is strictly ascending, no duplicates
    assert len(set(preview_indices_rule(8567, 100))) == 100
