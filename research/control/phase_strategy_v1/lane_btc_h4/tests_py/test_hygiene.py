"""Hygiene tests (plan §14): S1 denial, broker-surface scan, outcome-blindness
source scan (AST-based: comments/docstrings excluded from judgment)."""

import ast
from pathlib import Path

import pytest

LANE_DIR = Path(__file__).resolve().parents[1]

FORBIDDEN_PATH_STRINGS = [
    "SANDBOX-OVERFIT-3ASSETS",
    "wayfinder",
    "SURVIVORS",
    "HYPOTHESIS_LEDGER",
    "LESSONS",
    "MECHANISM_ATTRIBUTION",
    "lane_btc_h1",
    "lane_spy_d1",
    "SEALED",
    "s1_",
    "/S1/",
    "jrv2",
    "rsmv1",
]
FORBIDDEN_BROKER_HOSTS = [
    "api.binance.com",
    "fstream.binance.com",
    "testnet.binance",
    "api.binance.us",
]
FORBIDDEN_BROKER_MODULES = ["ccxt", "websocket", "websockets", "binance_api", "quantconnect"]
FORBIDDEN_RESULT_IDENTIFIERS = [
    # outcome-blindness: no strategy-result computation may exist in lane code
    "pnl", "equity", "drawdown", "sharpe", "profit_factor", "sortino",
    "gross_edge", "cumret", "cum_return", "net_pnl",
]


def _python_sources():
    return sorted((LANE_DIR / "pipeline").glob("*.py")) + \
        sorted((LANE_DIR / "tests_py").glob("*.py"))


def _scan_sources():
    """Sources scanned for forbidden string constants. The hygiene test file
    itself is excluded: it must quote the forbidden tokens to define them."""
    return [f for f in _python_sources() if f.name != "test_hygiene.py"]


def test_no_forbidden_path_references():
    for f in _scan_sources():
        tree = ast.parse(f.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                low = node.value.lower()
                for token in FORBIDDEN_PATH_STRINGS:
                    assert token.lower() not in low, f"{f.name}: forbidden reference '{token}'"


def test_no_broker_surface():
    for f in _scan_sources():
        tree = ast.parse(f.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    assert root not in FORBIDDEN_BROKER_MODULES, f"{f.name}: import {alias.name}"
            if isinstance(node, ast.ImportFrom) and node.module:
                root = node.module.split(".")[0]
                assert root not in FORBIDDEN_BROKER_MODULES, f"{f.name}: import from {node.module}"
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                for host in FORBIDDEN_BROKER_HOSTS:
                    assert host not in node.value, f"{f.name}: broker host {host}"


def test_no_strategy_result_identifiers_in_pipeline():
    """The pipeline (non-test) modules must not even NAME result quantities.

    Docstrings are deliberately excluded: the outcome-blindness LAW is quoted
    in them. Judgement is on identifiers (names, attributes, arguments).
    """
    for f in sorted((LANE_DIR / "pipeline").glob("*.py")):
        tree = ast.parse(f.read_text())
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Name):
                names.append(node.id)
            elif isinstance(node, ast.Attribute):
                names.append(node.attr)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names.append(node.name)
            elif isinstance(node, ast.arg):
                names.append(node.arg)
            for n in names:
                low = n.lower()
                for token in FORBIDDEN_RESULT_IDENTIFIERS:
                    assert token not in low, f"{f.name}: forbidden identifier '{n}'"


def test_ancestry_module_has_no_forbidden_shadow_reads():
    """The ancestry self-check reconstructs shadows ONLY from this cell's own
    price/volume series (function signature evidence)."""
    src = (LANE_DIR / "pipeline" / "ancestry.py").read_text()
    tree = ast.parse(src)
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "shadow_series")
    args = [a.arg for a in fn.args.args]
    assert args == ["close", "quote_volume"]


def test_no_network_calls_outside_vision_host():
    """requests usage must be confined to ingest.py (Vision download)."""
    import research.control.phase_strategy_v1.lane_btc_h4.pipeline as pkg  # noqa: F401
    pipeline_dir = LANE_DIR / "pipeline"
    offenders = []
    for f in pipeline_dir.glob("*.py"):
        if f.name in ("ingest.py",):
            continue
        if "requests" in f.read_text():
            offenders.append(f.name)
    assert offenders == []
