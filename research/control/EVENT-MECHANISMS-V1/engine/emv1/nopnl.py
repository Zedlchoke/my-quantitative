"""R2-6 no-PnL guard — recursive scan proving no return/aggregate field.

Scans every JSON/JSONL output artifact of this engine, at every depth, for
forbidden key substrings (any expectancy/PF/PnL/drawdown aggregate) and for
raw-looking derived return fields. A clean scan is the machine-checkable
half of the boundary proof; the other half is the builder field whitelist
(book.DECISION_KEYS), which contains prices and cost bands only.
"""
from __future__ import annotations

import json
import os
from typing import Iterable, List, Tuple

from . import config as C


def scan_object(obj, path: str = "$") -> List[str]:
    """Return list of violations (forbidden keys / aggregate-looking fields)."""
    bad: List[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            kl = str(k).lower()
            for sub in C.NOPNL_FORBIDDEN_KEY_SUBSTRINGS:
                if sub in kl:
                    bad.append(f"{path}.{k} ~ forbidden substring '{sub}'")
                    break
            bad.extend(scan_object(v, f"{path}.{k}"))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            bad.extend(scan_object(v, f"{path}[{i}]"))
    return bad


def scan_paths(paths: Iterable[str]) -> Tuple[List[str], int]:
    """Scan files; returns (violations, files_scanned)."""
    violations: List[str] = []
    n = 0
    for p in paths:
        if not os.path.exists(p):
            continue
        n += 1
        if p.endswith(".jsonl"):
            with open(p) as f:
                for ln, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    v = scan_object(json.loads(line), f"{p}#L{ln}")
                    violations.extend(v)
        elif p.endswith(".json"):
            v = scan_object(json.load(open(p)), p)
            violations.extend(v)
    return violations, n


def scan_tree(root: str) -> Tuple[List[str], int]:
    paths = []
    for dirpath, _, files in os.walk(root):
        for fn in files:
            if fn.endswith((".json", ".jsonl")):
                paths.append(os.path.join(dirpath, fn))
    return scan_paths(sorted(paths))
