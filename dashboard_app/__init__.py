"""Quant Shadow Dashboard — read-only macOS app wrapper for PROSPECTIVE-SHADOW-V1.

This package NEVER writes to the shadow ledgers, valuation marks or
heartbeats, NEVER acquires the heavy lock, NEVER opens S1 and NEVER
places orders. It only reads the append-only JSONL ledgers produced by
the PROSPECTIVE-SHADOW-V1 workers and renders one window.

Data plane  : repo ledgers/valuation marks resolved at runtime from
              plans/CYCLE_REGISTRY.json (no hard-coded checkout).
Engine      : imported at runtime from the live integration worktree
              (the exact code that writes the data — schema always in
              sync; nothing is vendored or forked here).
UI          : one window, one page (inline CSS/JS, hand-rolled SVG,
              no CDN, no internet required to render).
"""

__all__ = ["resolve", "status", "store", "pnl", "server", "page", "app_main"]
__version__ = "1.0.0"
