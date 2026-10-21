"""Generate apps/paperdesk/main/laws_generated.js from laws.py (W1.6).

Deterministic + byte-stable: the JS side of every frozen constant consumes
ONLY this generated file; a parity test re-runs the builder and refuses any
drift. Run after any (owner-approved) change to laws.py:
    python research/papertrade_exec/build_laws_js.py
"""
from __future__ import annotations

import json
from pathlib import Path

from research.papertrade_exec import laws

OUT = (Path(__file__).resolve().parents[2] / "apps" / "paperdesk" / "main"
       / "laws_generated.js")

HEADER = """'use strict';
// GENERATED FILE — DO NOT EDIT BY HAND (PAPERDESK-FIXALL-NCAA-V1 W1.6).
// Source of truth: research/papertrade_exec/laws.py; regenerate with
//   python research/papertrade_exec/build_laws_js.py
// Values are the frozen gate constants; the JS gate mirrors consume them
// from here so Python and JS can never silently diverge.
"""


def build() -> str:
    body = json.dumps(laws.as_dict(), indent=2, sort_keys=True)
    return (HEADER + "module.exports = " + body + ";\n")


if __name__ == "__main__":
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT}")
