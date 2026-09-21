"""PyInstaller entry for the Quant Shadow Dashboard .app.

Bundles ONLY the read-only wrapper (dashboard_app + pywebview). The
reconciled data engine is imported at runtime from the live
PROSPECTIVE-SHADOW-V1 integration worktree — the exact code that
writes the ledgers — and the ledger/mark files are resolved from the
cycle registry at startup. No credentials ship inside the bundle.
"""

from dashboard_app.app_main import main

if __name__ == "__main__":
    raise SystemExit(main())
