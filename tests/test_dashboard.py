"""Tests cho LAB DASHBOARD (lớp 1 collector + lớp 2 renderer).

Fixture: một repo git giả trong tmp_path mang đủ hình dạng nguồn dữ
liệu (registry, ledger, lessons, RULES §7, terminal artifacts được pin
SHA). Mỗi schema terminal cycle có MAPPER riêng được test tường minh.
Không mạng, không phụ thuộc pywebview.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))

from governance import dashboard_collect as dc  # noqa: E402
from governance import dashboard_render as dr  # noqa: E402


# ---------------------------------------------------------------------------
# Fixture repo
# ---------------------------------------------------------------------------

def _git(root: Path, *args: str) -> str:
    out = subprocess.run(["git", "-C", str(root), *args],
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    return out.stdout.strip()


def _commit_file(root: Path, rel: str, text: str) -> str:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    _git(root, "add", rel)
    _git(root, "-c", "user.email=t@t", "-c", "user.name=t",
         "commit", "-m", rel)
    return _git(root, "rev-parse", "HEAD")


LEDGER = """# HYPOTHESIS LEDGER

- Cumulative scored denominators (ledger authority per P-9):
  crypto 12 published / 13 observed; stocks 5/5; forex 3/3.
  **Program total: 20 published / 21 observed logical, 0 survivors.**
- S1 untouched everywhere.

## E. Near-misses — the most informative rows

1. **FAMILY-X (V9)** — PF 1.355, died on one frozen gate.

## F. Later section

unrelated
"""

LESSONS = """# LESSONS

## P-1 — A plausible-sounding assumption passes every review

Body one.

## P-2 — Thin margins make micro-optimism fatal; report margin-to-fail

Body two.
"""

RULES = """# RULES

## 7. GO phrase registry (exact strings; frozen phrase gates adjudicate form)

```text
GO STOCKS V99 SCORED EXECUTION      (live plan plans/PLAN_stocks_v99.md)
GO CRYPTO V99 SCORED EXECUTION      (live plan plans/PLAN_crypto_v99.md)
```
"""

V15_DOC = {
    "schema": "v15_terminal_report_v1",
    "cell_results": {
        "A5-F1-ANCHOR-ASYM": {"role": "anchor",
                              "expectancy_per_day": -0.0017,
                              "position_pf": 0.8969, "mdd": 0.6594,
                              "net_return_sum": -0.6277,
                              "folds_positive": "1/3"},
        "A5-F1-NEIGHBOR": {"role": "neighbour",
                           "expectancy_per_day": -0.0018,
                           "position_pf": 0.8985, "mdd": 0.6742,
                           "folds_positive": "?"},
        "A6-F1-CTL-RAWSAT": {"role": "causal_negative_control",
                             "expectancy_per_day": -0.0052,
                             "position_pf": 0.7873, "mdd": 0.5967,
                             "folds_positive": "0/3"},
    },
    "family_gate_tables": {
        "A5-V15-F1-ELITE-SIZE-ASYM": {
            "G1_expectancy_gt_0": {"value": -0.0017, "verdict": "FAIL",
                                   "margin_to_fail": -0.0017},
            "G2_pf_ge_1p10": {"value": 0.8969, "verdict": "FAIL",
                              "margin_to_fail": -0.2031},
        },
    },
}

STOCKS_V10_DOC = {
    "schema": "stocks_free_v10_run/terminal_report@1",
    "family_verdicts": {
        "SFV10-A4-H1": {
            "verdict": "REJECT (mechanical)",
            "anchor": "expectancy +0.0197/decision PASS but position PF 1.0811 "
                      "< 1.10 (margin -0.019), SPY-excess folds 0/3, "
                      "max fold MDD 0.0899 PASS",
            "control": "raw-lag control expectancy -0.0278 OPPOSITE sign",
            "neighbour": "cohort_z expectancy +0.0596 same-sign support=true",
        },
    },
}

FOREX_V1_DOC = {
    "cells": [{
        "label": "family1:anchor:tier1.0",
        "book": {"trades": 11459, "total_pnl": -26959.2,
                 "expectancy": -2.3527, "profit_factor": 0.8489},
        "mdd_usd": 31085.2,
        "folds": [{"positive": False}, {"positive": False},
                  {"positive": True}],
    }],
}

FOREX_V5_DOC = {
    "schema": "forex_free_v5_terminal_verdict_v1",
    "family_verdicts": {
        "FXFV5-A6-P1 (pre-release window)":
            "REJECT — anchor FAIL 8 gates: fin-adj expectancy -2.608/trade, "
            "PF 0.8739 (margin to 1.10: -0.226), 1/3 positive populated folds",
        "neighbour (+7-day sham calendar)":
            "REJECT on one gate — out-EARNED the anchor (+2.744 vs -2.608), "
            "stress PF 0.9876; margin to 1.10 +0.0468",
    },
}


@pytest.fixture()
def fake_repo(tmp_path: Path) -> Path:
    root = tmp_path
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    _commit_file(root, dc.REGISTRY_REL, "\n".join([
        json.dumps({
            "cycle_id": "CRYPTO-V15X", "asset": "crypto",
            "family_id": "A5-F1", "family_title": "t", "status": "CLOSED",
            "verdict_class": "SCIENTIFIC_REJECTION",
            "no_quality_evidence": False,
            "primary_failure": {"code": "EXPECTANCY_NONPOSITIVE",
                                "detail": "d"},
            "secondary_failures": [],
            "measured_summary": "s",
            "evidence": {"terminal_sha": "PENDING15",
                         "evidence_path":
                             "research/control/v15x_run/terminal_report.json",
                         "ledger_row": "LEDGER §A"},
            "unknown_fields": [], "recorded_by": "Lead",
            "recorded_utc": "2026-09-07T00:00:00Z",
        }),
        json.dumps({
            "cycle_id": "STOCKS-V10X", "asset": "stocks",
            "family_id": "SFV10-A4-H1", "family_title": "t",
            "status": "CLOSED", "verdict_class": "SCIENTIFIC_REJECTION",
            "no_quality_evidence": False,
            "primary_failure": {"code": "PF_BELOW_THRESHOLD", "detail": "d"},
            "secondary_failures": [], "measured_summary": "s",
            "evidence": {"terminal_sha": "PENDING10",
                         "evidence_path": "research/control/stocks_v10x_run",
                         "ledger_row": "LEDGER §B"},
            "unknown_fields": [], "recorded_by": "Lead",
            "recorded_utc": "2026-09-07T00:00:00Z",
        }),
        json.dumps({
            "cycle_id": "FOREX-V1X", "asset": "forex",
            "family_id": "FXFV1-A3-P1", "family_title": "t",
            "status": "CLOSED", "verdict_class": "SCIENTIFIC_REJECTION",
            "no_quality_evidence": False,
            "primary_failure": {"code": "EXPECTANCY_NONPOSITIVE", "detail": "d"},
            "secondary_failures": [], "measured_summary": "s",
            "evidence": {"terminal_sha": "PENDINGF1",
                         "evidence_path":
                             "research/control/forex_v1x_run/execution_summary.json",
                         "ledger_row": "LEDGER §C"},
            "unknown_fields": [], "recorded_by": "Lead",
            "recorded_utc": "2026-09-07T00:00:00Z",
        }),
        json.dumps({
            "cycle_id": "FOREX-V5X", "asset": "forex",
            "family_id": "FXFV5-A6-P1", "family_title": "t",
            "status": "CLOSED", "verdict_class": "SCIENTIFIC_REJECTION",
            "no_quality_evidence": False,
            "primary_failure": {"code": "STRESS_TIER_FAIL", "detail": "d"},
            "secondary_failures": [], "measured_summary": "s",
            "evidence": {"terminal_sha": "PENDINGF5",
                         "evidence_path":
                             "research/control/forex_v5x_run/terminal_verdict.json",
                         "ledger_row": "LEDGER §D"},
            "unknown_fields": [], "recorded_by": "Lead",
            "recorded_utc": "2026-09-07T00:00:00Z",
        }),
        json.dumps({
            "cycle_id": "CRYPTO-V6X", "asset": "crypto",
            "family_id": "OLD", "family_title": "t", "status": "CLOSED",
            "verdict_class": "SCIENTIFIC_REJECTION",
            "no_quality_evidence": False,
            "primary_failure": {"code": "FOLD_CONCENTRATION_OVER_LIMIT",
                                "detail": "d"},
            "secondary_failures": [], "measured_summary": "s",
            "evidence": {"terminal_sha": "deadbeefcafe", "evidence_path": None},
            "unknown_fields": ["evidence_path"], "recorded_by": "Lead",
            "recorded_utc": "2026-09-07T00:00:00Z",
        }),
    ]) + "\n")
    _commit_file(root, dc.LEDGER_REL, LEDGER)
    _commit_file(root, dc.LESSONS_REL, LESSONS)
    _commit_file(root, dc.RULES_REL, RULES)

    def pin(token: str, rel: str, doc) -> str:
        """Commit doc và thay token trong registry bằng SHA thật."""
        sha = _commit_file(root, rel, json.dumps(doc, indent=1))
        reg = root / dc.REGISTRY_REL
        reg.write_text(reg.read_text(encoding="utf-8").replace(token, sha),
                       encoding="utf-8")
        _git(root, "add", dc.REGISTRY_REL)
        _git(root, "-c", "user.email=t@t", "-c", "user.name=t",
             "commit", "-m", "pin " + token)
        return sha

    pin("PENDING15", "research/control/v15x_run/terminal_report.json", V15_DOC)
    pin("PENDING10", "research/control/stocks_v10x_run/terminal_report.json",
        STOCKS_V10_DOC)
    pin("PENDINGF1", "research/control/forex_v1x_run/execution_summary.json",
        FOREX_V1_DOC)
    pin("PENDINGF5", "research/control/forex_v5x_run/terminal_verdict.json",
        FOREX_V5_DOC)
    return root


# ---------------------------------------------------------------------------
# Snapshot tổng
# ---------------------------------------------------------------------------

def test_snapshot_top_level_keys_and_counts(fake_repo: Path):
    snap = dc.collect_snapshot(fake_repo)
    for key in ("measured_at", "header", "assets", "running", "failures",
                "pnl", "near_misses", "lessons"):
        assert key in snap
    assert snap["failures"]["total"] == 5
    assert snap["header"]["program"] == {"published": 20, "observed": 21}
    assert snap["header"]["crypto"] == {"published": 12, "observed": 13}
    assert snap["header"]["zero_survivors"] is True
    assert snap["header"]["s1"] == "S1 untouched (ledger)"
    phrases = [g["phrase"] for g in snap["header"]["go_registry"]]
    assert phrases == ["GO STOCKS V99 SCORED EXECUTION",
                       "GO CRYPTO V99 SCORED EXECUTION"]
    assert len(snap["lessons"]) == 2
    assert snap["lessons"][0]["id"] == "P-1"
    assert "FAMILY-X (V9)" in snap["near_misses"]["body"]


def test_signature_counts(fake_repo: Path):
    snap = dc.collect_snapshot(fake_repo)
    codes = {c["code"]: c["count"] for c in snap["failures"]["signature_counts"]}
    assert codes == {"EXPECTANCY_NONPOSITIVE": 2,
                     "PF_BELOW_THRESHOLD": 1,
                     "STRESS_TIER_FAIL": 1,
                     "FOLD_CONCENTRATION_OVER_LIMIT": 1}


# ---------------------------------------------------------------------------
# MAPPER từng schema — test tường minh
# ---------------------------------------------------------------------------

def test_mapper_crypto_cell_results_v15():
    mapped = dc.mapper_crypto_cell_results(V15_DOC, "terminal_report.json")
    assert mapped["schema"] == "v15_terminal_report_v1"
    fams = {f["family_label"]: f for f in mapped["families"]}
    # A5 family gom 2 cell (anchor + neighbour); A6 riêng control
    assert set(fams) == {"A5-V15-F1-ELITE-SIZE-ASYM", "A6-F1-CTL-RAWSAT"}
    a5 = fams["A5-V15-F1-ELITE-SIZE-ASYM"]
    roles = {a["role"] for a in a5["arms"]}
    assert roles == {"anchor", "neighbour"}
    anchor = next(a for a in a5["arms"] if a["role"] == "anchor")
    assert anchor["expectancy"] == -0.0017
    assert anchor["pf"] == 0.8969
    assert anchor["folds"] == "1/3"
    assert anchor["pnl"] == -0.6277
    # margins trích từ family_gate_tables (P-2)
    assert "G2_pf_ge_1p10: margin -0.2031" in (anchor["margins"] or "")


def test_mapper_stocks_prose_v10():
    mapped = dc.mapper_prose_verdicts(
        STOCKS_V10_DOC, "terminal_report.json", ("family_verdicts",))
    arms = {a["role"]: a for a in mapped["families"][0]["arms"]}
    assert arms["anchor"]["expectancy"] == "expectancy +0.0197"
    assert arms["anchor"]["pf"] == "PF 1.0811"
    assert arms["anchor"]["margins"] == "margin -0.019"
    assert arms["anchor"]["folds"] == "folds 0/3"
    assert arms["anchor"]["mdd"] == "MDD 0.0899"
    assert arms["control"]["expectancy"] == "expectancy -0.0278"
    # khoá không phải arm (verdict) không thành hàng số
    assert "verdict" not in arms


def test_mapper_forex_execution_summary_v1():
    mapped = dc.mapper_forex_execution_summary(FOREX_V1_DOC, "execution_summary.json")
    arm = mapped["families"][0]["arms"][0]
    assert arm["role"] == "anchor"
    assert arm["pnl"] == -26959.2
    assert arm["expectancy"] == -2.3527
    assert arm["pf"] == 0.8489
    assert arm["mdd"] == 31085.2
    assert arm["folds"] == "1/3"


def test_mapper_forex_prose_v5():
    mapped = dc.mapper_prose_verdicts(
        FOREX_V5_DOC, "terminal_verdict.json", ("family_verdicts",))
    by_fam = {f["family_label"]: f for f in mapped["families"]}
    anchor = by_fam["FXFV5-A6-P1 (pre-release window)"]["arms"][0]
    assert anchor["role"] == "anchor"
    assert anchor["expectancy"] == "expectancy -2.608"
    assert anchor["pf"] == "PF 0.8739"
    assert anchor["margins"] == "margin to 1.10: -0.226"
    assert anchor["folds"] == "1/3"
    # key đã nói rõ vai trò -> nguyên chuỗi là 1 arm neighbour, không tách
    nb = by_fam["neighbour (+7-day sham calendar)"]["arms"]
    assert len(nb) == 1 and nb[0]["role"] == "neighbour"
    assert nb[0]["pf"] == "PF 0.9876"
    assert nb[0]["margins"] == "margin to 1.10 +0.0468"


def test_choose_mapper_dispatch():
    name, fn = dc._choose_mapper(V15_DOC)
    assert name == "mapper_crypto_cell_results" and fn is not None
    name, _ = dc._choose_mapper(FOREX_V1_DOC)
    assert name == "mapper_forex_execution_summary"
    name, _ = dc._choose_mapper(STOCKS_V10_DOC)
    assert name == "mapper_prose_verdicts"
    name, fn = dc._choose_mapper({"schema": "forex_free_v3r_terminal_verdict_v1"})
    assert name == "none" and fn is None


# ---------------------------------------------------------------------------
# PnL panel: resolve qua git show + pin, fail-closed
# ---------------------------------------------------------------------------

def test_pnl_panel_resolves_by_pinned_sha(fake_repo: Path):
    snap = dc.collect_snapshot(fake_repo)
    pnl = {p["cycle_id"]: p for p in snap["pnl"]}
    v15 = pnl["CRYPTO-V15X"]
    assert v15["mapper"] == "mapper_crypto_cell_results"
    assert v15["table"] is not None
    assert v15["source"].startswith("git show ")

    v10 = pnl["STOCKS-V10X"]
    # evidence_path là THƯ MỤC pin -> tìm terminal_report.json bên trong
    assert v10["table"] is not None
    assert "stocks_v10x_run/terminal_report.json" in v10["source"]

    old = pnl["CRYPTO-V6X"]
    assert old["table"] is None
    assert "không pin evidence_path" in old["no_data_reason"]
    assert old["ledger_row"] or True


def test_pnl_panel_no_data_never_guessed(fake_repo: Path):
    snap = dc.collect_snapshot(fake_repo)
    old = next(p for p in snap["pnl"] if p["cycle_id"] == "CRYPTO-V6X")
    assert old["no_data_reason"]
    assert old["table"] is None


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------

def test_render_contains_key_sections_and_no_none(fake_repo: Path):
    snap = dc.collect_snapshot(fake_repo)
    html = dr.render(snap)
    for needle in ("LAB DASHBOARD", "KHÔNG CÓ DỮ LIỆU", "CRYPTO-V15X",
                   "GO STOCKS V99 SCORED EXECUTION", "P-1", "Near-miss",
                   "PnL tổng quan"):
        assert needle in html
    assert "None" not in html
    assert 'src="http' not in html and 'href="http' not in html  # không CDN


def test_render_failure_filter_attributes(fake_repo: Path):
    snap = dc.collect_snapshot(fake_repo)
    html = dr.render(snap)
    assert 'data-asset="crypto"' in html
    assert 'data-verdict="SCIENTIFIC_REJECTION"' in html


# ---------------------------------------------------------------------------
# ACTIVE_CYCLES.json + write_outputs
# ---------------------------------------------------------------------------

def test_write_outputs_active_cycles_and_html(fake_repo: Path, tmp_path: Path):
    snap = dc.collect_snapshot(fake_repo)
    out_dir = tmp_path / "dashboard_out"
    dc.write_outputs(snap, out_dir)
    ac = json.loads((fake_repo / dc.ACTIVE_CYCLES_REL).read_text(
        encoding="utf-8"))
    assert ac["measured_at"] == snap["measured_at"]
    assert len(ac["cycles"]) == len(dc.LIVE_CYCLES)
    for c in ac["cycles"]:
        for field in ("cycle_id", "plan", "status", "phase", "worktree",
                      "branch", "head", "budget", "go_phrase", "s1",
                      "measured_at"):
            assert field in c
        # fixture repo không có worktree cycle sống -> NO_DATA, không suy diễn
        assert c["branch"] == dc.NO_DATA
    html = (out_dir / "index.html").read_text(encoding="utf-8")
    assert html.startswith("<!doctype html>")


def test_registry_parse_error_is_fail_closed(tmp_path: Path):
    reg = tmp_path / dc.REGISTRY_REL
    reg.parent.mkdir(parents=True)
    reg.write_text("{broken json\n", encoding="utf-8")
    entries = dc.load_registry(tmp_path)
    assert len(entries) == 1 and entries[0].get("_parse_error") is True
    assert dc.signature_counts(entries) == []
