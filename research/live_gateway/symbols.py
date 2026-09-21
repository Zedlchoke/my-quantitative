"""Symbol universe discovery (plan §4): static frozen union + live
read-only tails of the PROSPECTIVE-SHADOW-V1 valuation mark ledgers.

Static union = ILLIQ(20) ∪ PREMFADE(13) ∪ CARRY(7) candidate universes
= the 20 ILLIQ symbols (verified superset). Dynamic = every symbol
appearing as an open position in the LATEST mark record of each
family ledger (read-only; the gateway never writes those files).
Refreshed hourly; cap 190 symbols = ONE WS connection.
"""

from __future__ import annotations

import glob
import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

ILLIQ_CANDIDATE_UNIVERSE = (
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
    "DOGEUSDT", "LINKUSDT", "ADAUSDT", "LTCUSDT", "AVAXUSDT",
    "ATOMUSDT", "NEARUSDT", "ARBUSDT", "OPUSDT", "APTUSDT",
    "FILUSDT", "ETCUSDT", "BCHUSDT", "DOTUSDT", "TRXUSDT",
)
PREMFADE_CANDIDATE_UNIVERSE = ILLIQ_CANDIDATE_UNIVERSE[:13]
CARRY_TRADED_UNIVERSE = (
    "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT",
    "LINKUSDT", "ADAUSDT",
)

STATIC_UNIVERSE = tuple(
    sorted(
        set(ILLIQ_CANDIDATE_UNIVERSE)
        | set(PREMFADE_CANDIDATE_UNIVERSE)
        | set(CARRY_TRADED_UNIVERSE)
    )
)

SYMBOL_MVP_CAP = 190  # one WS connection (stream limit 200, margin 10)


@dataclass
class SymbolSource:
    marks_globs: List[str] = field(default_factory=list)
    extra_symbols: List[str] = field(default_factory=list)
    cap: int = SYMBOL_MVP_CAP
    last_refresh_utc: Optional[str] = None
    last_discovered: List[str] = field(default_factory=list)

    def _positions_from_ledger(self, path: str) -> List[str]:
        """Read-only tail: symbols in the LAST record's positions list."""
        symbols: List[str] = []
        try:
            with open(path, "r", encoding="utf-8") as handle:
                handle.seek(0, os.SEEK_END)
                size = handle.tell()
                handle.seek(max(0, size - 200_000))
                tail = handle.read()
        except OSError:
            return symbols
        # last non-empty line that parses
        for line in reversed(tail.splitlines()):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except ValueError:
                continue
            positions = record.get("positions")
            if isinstance(positions, list):
                for pos in positions:
                    sym = pos.get("symbol") if isinstance(pos, dict) else None
                    if isinstance(sym, str) and sym:
                        symbols.append(sym)
            break
        return symbols

    def refresh(self, now_utc: str) -> Dict[str, Any]:
        """Recompute the universe. Returns {symbols, added, removed}."""
        universe = set(STATIC_UNIVERSE) | set(self.extra_symbols)
        for pattern in self.marks_globs:
            for path in sorted(glob.glob(pattern)):
                universe.update(self._positions_from_ledger(path))
        symbols = sorted(universe)[: self.cap]
        added = [s for s in symbols if s not in self.last_discovered]
        removed = [s for s in self.last_discovered if s not in symbols]
        change: Dict[str, Any] = {
            "symbols": symbols,
            "added": added,
            "removed": removed,
        }
        self.last_discovered = symbols
        self.last_refresh_utc = now_utc
        return change
