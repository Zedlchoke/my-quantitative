"""Boundary test: this package must stay a data-engineering surface.

No strategy/PnL/S1/order vocabulary may be imported, and no live-order or
scoring capability may be referenced.
"""

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = REPO_ROOT / "research" / "free_data_frontier"

FORBIDDEN_MODULES = (
    "backtest",
    "nautilus_trader",
    "nautilus",
    "portfolio_runner",
    "optimize",
    "research.governance.scoring",
    "ccxt",
    "binance",
)

FORBIDDEN_TOKENS = (
    "place_order",
    "submit_order",
    "market_buy",
    "market_sell",
    "paper_trade(",
    "open_s1",
    "score_cell",
)


def test_no_forbidden_imports():
    offenders = []
    for path in sorted(PACKAGE_DIR.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            for name in names:
                root = name.split(".")[0]
                if any(root == forbidden or name.startswith(forbidden) for forbidden in FORBIDDEN_MODULES):
                    offenders.append(f"{path.name}: imports {name}")
    assert offenders == []


def test_no_forbidden_tokens_in_source():
    offenders = []
    for path in sorted(PACKAGE_DIR.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_TOKENS:
            if token in text:
                offenders.append(f"{path.name}: contains {token!r}")
    assert offenders == []


def test_no_secret_values_in_source_tree():
    """Source must never embed env secret values; referencing env NAMES is fine."""
    import re

    for path in sorted(PACKAGE_DIR.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            if "api_key" not in line.lower() and "apikey" not in line.lower():
                continue
            # flag only literal values long enough to be a real secret
            # (denylist param NAMES are short lowercase tokens).
            for match in re.finditer(r'["\']([^"\']{16,})["\']', line):
                value = match.group(1)
                if re.match(r"^[A-Z0-9_./<>:@ -]+$", value):
                    continue  # env NAME, constant, or redaction descriptor
                raise AssertionError(f"possible hardcoded key: {path.name}: {line}")
