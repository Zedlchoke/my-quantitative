"""Gateway configuration: defaults + JSON override + environment-free.

No secrets exist in this gateway (keyless public data only).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List

DEFAULT_RUNTIME_ROOT = "results/live_data_gateway_v1"
DEFAULT_BIND = "127.0.0.1"
DEFAULT_PORT = 8792
DEFAULT_WS_BASE = "wss://fstream.binance.com/stream"
DEFAULT_REST_BASE = "https://fapi.binance.com"

SHV1_MARKS_GLOB_DEFAULT = (
    "/Users/hoangminhlong/my-quantitative/.worktrees/prospective-shadow-v1/"
    "integration/results/prospective_shadow_v1/valuation_marks/*.jsonl"
)


@dataclass
class GatewayConfig:
    bind: str = DEFAULT_BIND
    port: int = DEFAULT_PORT
    ws_base: str = DEFAULT_WS_BASE
    rest_base: str = DEFAULT_REST_BASE
    runtime_root: str = DEFAULT_RUNTIME_ROOT
    marks_globs: List[str] = field(default_factory=lambda: [SHV1_MARKS_GLOB_DEFAULT])
    extra_symbols: List[str] = field(default_factory=list)
    symbol_cap: int = 190

    @classmethod
    def load(cls, path: str | None = None) -> "GatewayConfig":
        cfg = cls()
        if path and os.path.exists(path):
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            for key, value in data.items():
                if hasattr(cfg, key):
                    setattr(cfg, key, value)
        return cfg

    def runtime_dir(self, *parts: str) -> str:
        return os.path.join(self.runtime_root, *parts)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "bind": self.bind,
            "port": self.port,
            "ws_base": self.ws_base,
            "rest_base": self.rest_base,
            "runtime_root": self.runtime_root,
            "marks_globs": self.marks_globs,
            "extra_symbols": self.extra_symbols,
            "symbol_cap": self.symbol_cap,
        }
