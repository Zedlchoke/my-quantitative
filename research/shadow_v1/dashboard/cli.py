"""CLI entry: ``python -m research.shadow_v1.dashboard`` (read-only).

Examples::

    python -m research.shadow_v1.dashboard --ledgers <dir> --port 8791
    python -m research.shadow_v1.dashboard --ledgers <dir> --now 2026-09-14T00:00:00Z
    python -m research.shadow_v1.dashboard --ledgers <dir> --out /tmp/page.html
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from typing import List, Optional

from .render import generate_html
from .server import serve
from .snapshot import (
    build_dashboard_snapshot,
    resolve_ledger_paths,
    resolve_valuation_mark_paths,
    snapshot_json,
)

__all__ = ["main"]


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m research.shadow_v1.dashboard",
        description="Read-only PROSPECTIVE-SHADOW-V1 owner dashboard "
        "(GET/HEAD only; no write endpoint, no order path).",
    )
    parser.add_argument(
        "--ledgers", required=True,
        help="directory containing <FAMILY_ID>.jsonl append-only ledgers",
    )
    parser.add_argument(
        "--port", type=int, default=None,
        help="serve HTTP on this port (GET/HEAD only); omit with --out/--print",
    )
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument(
        "--identity", default=None,
        help="path to identity_recovery.json for the drift cross-check",
    )
    parser.add_argument(
        "--shadow-start", default=None,
        help="SHADOW_START_UTC anchor for the combined chart baseline",
    )
    parser.add_argument(
        "--now", default=None,
        help="pin the snapshot clock (reproducible bytes), e.g. 2026-09-14T00:00:00Z",
    )
    parser.add_argument(
        "--out", default=None,
        help="write the HTML page to this path instead of serving",
    )
    parser.add_argument(
        "--valuation-dir", default=None,
        help="directory holding <FAMILY_ID>.jsonl near-real valuation mark "
        "ledgers (default: the valuation_marks/ sibling of --ledgers)",
    )
    args = parser.parse_args(argv)

    ledger_paths = resolve_ledger_paths(args.ledgers)
    valuation_paths = resolve_valuation_mark_paths(
        args.valuation_dir if args.valuation_dir else args.ledgers
    )
    now_iso = args.now or _now_iso()

    if args.port is not None:
        serve(
            args.ledgers,
            args.port,
            bind=args.bind,
            identity_manifest_path=args.identity,
            shadow_start_utc=args.shadow_start,
            valuation_marks_by_family=valuation_paths,
        )
        return 0

    snapshot = build_dashboard_snapshot(
        ledger_paths,
        now_iso,
        identity_manifest_path=args.identity,
        shadow_start_utc=args.shadow_start,
        valuation_marks_by_family=valuation_paths,
    )
    if args.out:
        with open(args.out, "wb") as fh:
            fh.write(generate_html(snapshot).encode("utf-8"))
    else:
        sys.stdout.write(snapshot_json(snapshot) + "\n")
    return 0
