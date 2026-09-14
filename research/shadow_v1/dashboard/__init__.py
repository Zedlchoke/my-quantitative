"""PROSPECTIVE-SHADOW-V1 read-only owner dashboard (plan section 9).

A pure VIEW over the append-only shadow ledgers: it can never rewrite
trades, equity or verdicts, and it exposes NO write endpoint capable of
placing an order (the HTTP server answers GET/HEAD only; every other
method is a 405).

Modules:
- ``snapshot``: build the read-only dashboard snapshot from ledger files
  (strict-sum combined series, frozen-window today PnL, four separate
  counters, per-fill trade rows + click-through details).
- ``render``: self-contained HTML page (inline CSS/JS, hand-rolled SVG).
- ``server``: http.server GET/HEAD-only routes (no static, no writes).
- ``cli``: ``python -m research.shadow_v1.dashboard`` entry point.
"""

from .cli import main
from .render import generate_html
from .server import ROUTES, DashboardApp, make_server, serve
from .snapshot import (
    SL_NA,
    TP_NA,
    build_dashboard_snapshot,
    resolve_ledger_paths,
    snapshot_json,
)

__all__ = [
    "build_dashboard_snapshot",
    "generate_html",
    "serve",
    "make_server",
    "main",
    "resolve_ledger_paths",
    "snapshot_json",
    "ROUTES",
    "DashboardApp",
    "SL_NA",
    "TP_NA",
]
