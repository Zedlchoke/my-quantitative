"""DIAG per-pair registered guards + probe-derived configs.

Mirrors scripts/pair_config.py (imported, never modified): the registered
guards here are the OWNER dispatch expectations for the two diagnostic
pairs (EURUSD band ~0.80-1.35, GBPUSD ~1.03-1.42, pip 1e-4, scale 1e5).
The probe (probe_diag.py) must PROVE the bytes land inside them; the
band is derived as union(probe min*0.80 floor-to-pip, probe max*1.20
ceil-to-pip, registered guard) — the cycle's proven method — and written
to diag/data_local/derived/pair_configs_diag.json ONLY on PROBE_PASS.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

DIAG = Path(__file__).resolve().parent.parent
CONFIG_PATH = DIAG / "data_local" / "derived" / "pair_configs_diag.json"

REGISTERED_GUARDS = {
    "EURUSD": {"band_lo": 0.80, "band_hi": 1.35, "pip": 1e-4},
    "GBPUSD": {"band_lo": 1.03, "band_hi": 1.42, "pip": 1e-4},
}


@dataclass(frozen=True)
class PairConfig:
    symbol: str
    pip: float
    price_scale: float
    band_lo: float
    band_hi: float
    derivation: dict = field(default_factory=dict)

    def validate_against_guard(self) -> None:
        g = REGISTERED_GUARDS[self.symbol]
        if self.band_lo > g["band_lo"] or self.band_hi < g["band_hi"]:
            raise SystemExit(
                f"FAIL_CLOSED {self.symbol} band [{self.band_lo}, {self.band_hi}]"
                f" does not cover registered guard [{g['band_lo']}, {g['band_hi']}]")
        if abs(self.pip - g["pip"]) > 1e-12:
            raise SystemExit(
                f"FAIL_CLOSED {self.symbol} derived pip {self.pip} != registered"
                f" expectation {g['pip']}")


def load_pair_config(symbol: str) -> PairConfig:
    if not CONFIG_PATH.exists():
        raise SystemExit(
            f"FAIL_CLOSED {CONFIG_PATH} missing — run probe_diag.py first")
    data = json.loads(CONFIG_PATH.read_text())
    if symbol not in data:
        raise SystemExit(f"FAIL_CLOSED no pair config for {symbol}")
    cfg = PairConfig(
        symbol=symbol,
        pip=float(data[symbol]["pip"]),
        price_scale=float(data[symbol]["price_scale"]),
        band_lo=float(data[symbol]["band_lo"]),
        band_hi=float(data[symbol]["band_hi"]),
        derivation=data[symbol].get("derivation", {}),
    )
    if not cfg.derivation.get("proven"):
        raise SystemExit(f"FAIL_CLOSED {symbol} pair config not proven by probe")
    cfg.validate_against_guard()
    return cfg
