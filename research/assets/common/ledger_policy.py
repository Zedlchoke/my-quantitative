"""Ledger placement contract (owner: A2, PLAN_stocks.md section 6 + 14).

Path policy ONLY — this module performs no runtime writes and no IO at all.

* per-asset-class ledger roots: the historical crypto root
  ``results/registry`` is untouched (read-only for every non-crypto lane);
  stocks write under ``results/registry/stocks/``; forex is reserved;
* exactly ONE global trial index path, exposed through a read-only
  interface (:class:`GlobalTrialIndex`) with no write method in the
  contract at all — implementations must never write.

Unknown asset classes fail closed (no default root, no silent fallback).
"""

from __future__ import annotations

import abc
from pathlib import Path
from typing import Any, Mapping

from research.assets.common.contracts import require_asset_class

#: Historical crypto ledger root.  Byte-frozen territory: stocks/forex code
#: must only ever READ here.
CRYPTO_LEDGER_ROOT = Path("results") / "registry"

#: Stocks ledger root (PLAN_stocks.md section 14).
STOCKS_LEDGER_ROOT = Path("results") / "registry" / "stocks"

#: Reserved forex root; its bytes stay read-only until a forex lane owns it.
FOREX_LEDGER_ROOT = Path("results") / "registry" / "forex"

LEDGER_ROOTS_BY_ASSET_CLASS: Mapping[str, Path] = {
    "CRYPTO_PERP": CRYPTO_LEDGER_ROOT,
    "US_CASH_EQUITY": STOCKS_LEDGER_ROOT,
    "FX_SPOT": FOREX_LEDGER_ROOT,
}

#: The single global trial index file (read-only from every lane's view).
GLOBAL_TRIAL_INDEX_FILENAME = "global_trial_index.jsonl"
GLOBAL_TRIAL_INDEX_PATH = CRYPTO_LEDGER_ROOT / GLOBAL_TRIAL_INDEX_FILENAME


def ledger_root_for(asset_class: str) -> Path:
    """Ledger root for an asset class; unknown classes fail closed."""
    require_asset_class(asset_class)
    try:
        return LEDGER_ROOTS_BY_ASSET_CLASS[asset_class]
    except KeyError as exc:
        raise ValueError(
            f"no ledger root declared for asset class {asset_class!r}; "
            "declare it in LEDGER_ROOTS_BY_ASSET_CLASS instead of defaulting"
        ) from exc


def ledger_path_for(asset_class: str, filename: str) -> Path:
    """Ledger file path under the asset class root (no directory is created)."""
    if not isinstance(filename, str) or not filename.strip():
        raise ValueError("filename must be non-empty")
    return ledger_root_for(asset_class) / filename


def global_trial_index_path() -> Path:
    """The ONE global trial index path (never asset-class specific)."""
    return GLOBAL_TRIAL_INDEX_PATH


class GlobalTrialIndex(abc.ABC):
    """Read-only interface over the single global trial index.

    Contract: implementations expose ONLY reads.  There is deliberately no
    append/update/delete method in this interface; a lane that needs to
    publish rows does so through its own asset-class ledger owner, never by
    writing the shared index.  Fail-closed reads (corrupt lines raise) are
    inherited from the ``research.global_ledger`` semantics.
    """

    @abc.abstractmethod
    def snapshot(self) -> Mapping[str, Any]:
        """``{rows, count, sha256, existed}``-style read-only snapshot."""

    @abc.abstractmethod
    def digest(self) -> str:
        """Canonical sha256 over the current index rows."""

    @abc.abstractmethod
    def count(self) -> int:
        """Number of rows currently visible in the index."""
