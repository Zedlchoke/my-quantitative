#!/usr/bin/env python
"""Scored discovery backtest — GO-GATED, FAIL-CLOSED (V2 quarantine law).

Refuses to compute anything unless a token file exists whose sha256 equals
sha256 of the exact owner GO phrase
    GO REGIME STRATEGY MAPPING V1 DISCOVERY BACKTEST
(no trailing newline). Per-cell/per-arm invocation is refused before any
compute. Without authority: print REFUSED_BACKTEST_QUARANTINE, exit 20.

Usage:
  python tools/cmd_scored.py --check          # report gate status only
  python tools/cmd_scored.py --go-token FILE  # run the scored discovery

The run itself is implemented by rsmv1.scored (constructed at integration
after the specialist library + arms freezes land). This file exists NOW so
the quarantine is provably in place before any candidate outcome can exist.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

GO_PHRASE = "GO REGIME STRATEGY MAPPING V1 DISCOVERY BACKTEST"
CYCLE_DIR = Path(__file__).resolve().parents[1]
TOKEN_PATH = CYCLE_DIR / "SCORED_GO.json"
EXIT_REFUSED = 20
sys.path.insert(0, str(CYCLE_DIR))


def _token_sha() -> str | None:
    if not TOKEN_PATH.exists():
        return None
    raw = TOKEN_PATH.read_bytes()
    return hashlib.sha256(raw).hexdigest()


def gate_status() -> dict:
    want = hashlib.sha256(GO_PHRASE.encode()).hexdigest()
    got = _token_sha()
    return {
        "go_phrase_sha256_expected": want,
        "token_present": got is not None,
        "token_matches": got == want,
        "token_path": str(TOKEN_PATH),
        "authorized": got == want,
    }


def main(argv: list[str]) -> int:
    if "--check" in argv:
        import json

        print(json.dumps(gate_status(), indent=1))
        return 0
    status = gate_status()
    if not status["authorized"]:
        print("REFUSED_BACKTEST_QUARANTINE", status)
        return EXIT_REFUSED
    from rsmv1 import scored  # noqa: F401  (implemented at integration)

    return scored.run_all()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
