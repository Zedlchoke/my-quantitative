#!/usr/bin/env python3
"""Map changed paths to conservative targeted test commands."""

from __future__ import annotations

import sys


RULES = (
    ((".claude/",), "python3 .claude/scripts/validate_claude_setup.py"),
    (("app_web/",), ".venv/bin/python -m pytest tests/test_acceptance.py -q"),
    (("research/assets/stocks/", "tests/assets/stocks/"), ".venv/bin/python -m pytest tests/assets/stocks -q"),
    (("research/assets/forex/", "tests/assets/forex/"), ".venv/bin/python -m pytest tests/assets/forex -q"),
    (("research/protocol/", "research/portfolio_runner.py", "research/reproduction_harness.py"), ".venv/bin/python -m pytest tests/test_protocol_contracts.py tests/test_protocol_registry.py tests/test_protocol_reconciliation.py tests/test_protocol_reproduce.py -q"),
    (("strategy_", "research/strategies/", "research/hypotheses/"), ".venv/bin/python -m pytest tests/test_protocol_gates.py tests/test_reproduction_harness.py -q"),
    (("research/data", "research/derivatives", "funding"), ".venv/bin/python -m pytest tests/test_data_audit.py tests/test_funding_pit.py tests/test_execution_truth.py -q"),
)


def main() -> int:
    paths = [p.replace("\\", "/") for p in sys.argv[1:]]
    if not paths:
        print("usage: route_tests.py <changed-file>...", file=sys.stderr)
        return 2
    commands = []
    for needles, command in RULES:
        if any(any(needle in path for needle in needles) for path in paths) and command not in commands:
            commands.append(command)
    if any(path.endswith(".py") for path in paths):
        py_files = " ".join(path for path in paths if path.endswith(".py"))
        commands.insert(0, f".venv/bin/python -m py_compile {py_files}")
    if not commands:
        commands.append("NO_AUTOMATIC_ROUTE: inspect applicable PLAN and nearest tests")
    print("\n".join(commands))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
