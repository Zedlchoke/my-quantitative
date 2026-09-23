"""Hygiene scans: S1 denial, broker/network surface, forbidden-path literals,
and structural absence of a holding-duration flat law (AST identifiers)."""

import ast
from pathlib import Path

import pytest

CODE_DIR = Path(__file__).resolve().parents[1] / "code"

BANNED_IMPORT_ROOTS = {
    "requests", "urllib", "urllib3", "socket", "ssl", "smtplib", "ftplib",
    "telnetlib", "websocket", "websockets", "ccxt", "boto3", "paramiko",
    "yfinance", "pandas_datareader", "twisted", "aiohttp", "httpx",
}
BANNED_IDENTIFIER_SUBSTRINGS = {
    "stale", "age_", "aging", "days_since",
}
BANNED_LITERAL_SUBSTRINGS = {
    "SANDBOX-OVERFIT-3ASSETS",
    "lane_btc_h1",
    "lane_btc_h4",
    "/research/wayfinder/",
    "rsmv1",
    "jrv2",
    "MECHANISM_ATTRIBUTION_REPORT",
}
ALLOWED_LITERALS = set()  # populated with the pinned snapshot path constant


def _py_files():
    return sorted(CODE_DIR.rglob("*.py"))


def _imports(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name.split(".")[0]
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.level == 0:
                yield node.module.split(".")[0]


def _identifiers(tree):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield node.name.lower()
            a = node.args
            for arg in list(a.args) + list(a.kwonlyargs):
                yield arg.arg.lower()
        elif isinstance(node, ast.ClassDef):
            yield node.name.lower()
        elif isinstance(node, ast.Name):
            yield node.id.lower()
        elif isinstance(node, ast.Attribute):
            yield node.attr.lower()


def _string_literals(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            yield node.value


@pytest.mark.parametrize("path", _py_files(), ids=lambda p: p.name)
def test_no_network_or_broker_imports(path):
    tree = ast.parse(path.read_text())
    for root in _imports(tree):
        assert root not in BANNED_IMPORT_ROOTS, (path.name, root)


@pytest.mark.parametrize("path", _py_files(), ids=lambda p: p.name)
def test_no_staleness_or_age_identifiers(path):
    tree = ast.parse(path.read_text())
    for ident in _identifiers(tree):
        for banned in BANNED_IDENTIFIER_SUBSTRINGS:
            assert banned not in ident, (path.name, ident)


@pytest.mark.parametrize("path", _py_files(), ids=lambda p: p.name)
def test_no_forbidden_path_literals(path):
    text = path.read_text()
    tree = ast.parse(text)
    for lit in _string_literals(tree):
        for banned in BANNED_LITERAL_SUBSTRINGS:
            assert banned not in lit, (path.name, banned)


def test_snapshot_path_literal_is_the_allowed_exception():
    """The ONE external file this lane may read is the frozen snapshot; its
    path literal is pinned here so the literal scan stays strict."""
    from psv1_spy.snapshot import SNAPSHOT_PATH, SNAPSHOT_SHA256

    assert SNAPSHOT_PATH.endswith("jev_regime_router_v1/data_local/SPY.json.gz")
    assert len(SNAPSHOT_SHA256) == 64
    # and no other literal in the package mentions that tree
    for path in _py_files():
        tree = ast.parse(path.read_text())
        for lit in _string_literals(tree):
            if "jev_regime_router_v1" in lit:
                assert path.name == "snapshot.py"
                assert lit == SNAPSHOT_PATH


def test_no_pnl_shaped_identifiers_anywhere():
    """No returns/equity/PnL path may exist in lane code (plan 7.3). This is a
    structural scan of identifiers; the deeper law is that the package only
    contains counting and cost-side arithmetic."""
    banned = {"pnl", "net_pnl", "equity", "profit", "profit_factor", "sharpe",
              "drawdown", "portfolio_value"}
    for path in _py_files():
        tree = ast.parse(path.read_text())
        for ident in _identifiers(tree):
            assert ident not in banned, (path.name, ident)
