"""Per-pair scale/pip/band configuration — ERP1-TRACKA-COHORT-1.

Plan §5.2 BLOCKING PORT DEFECT fix: the ancestor hard-codes
PIP=1e-4 / PRICE_SCALE=1e5 / EURUSD band 0.80<b<1.35 (build_bars.py) and
PIP=1e4 (engine.py). This cycle every constant is per-pair and PROVEN:
`pair_configs.json` is written ONLY by probe_pair.py after the probe
verdict is PROBE_PASS, and every consumer fail-closes on a missing or
unproven config.

Registered expectation guards (plan §5.2 / appendix A.1, NOT assumptions
about the bytes — the probe must PROVE the bytes land inside them):
  AUDUSD: ~1e-5 point scale, 0.0001 pip, price band roughly 0.55–0.85
  USDCAD: ~1e-5 point scale, 0.0001 pip, price band roughly 1.20–1.50
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPTS_DIR / "pair_configs.json"

# Registered guard ranges (plan §5.2, appendix A.1). The derived band must
# COVER these; the probe additionally records the raw observed min/max.
REGISTERED_GUARDS = {
    "AUDUSD": {"band_lo": 0.55, "band_hi": 0.85, "pip": 1e-4},
    "USDCAD": {"band_lo": 1.20, "band_hi": 1.50, "pip": 1e-4},
}


@dataclass(frozen=True)
class PairConfig:
    symbol: str
    pip: float            # one pip in price units (derived: 10 x point size)
    price_scale: float    # integer-points divisor (derived)
    band_lo: float        # tradability band (derived union: probe +/-20% | guard)
    band_hi: float
    derivation: dict = field(default_factory=dict)

    def validate_against_guard(self) -> None:
        g = REGISTERED_GUARDS.get(self.symbol)
        if g is None:
            raise SystemExit(f"FAIL_CLOSED no registered guard for {self.symbol}")
        if self.band_lo > g["band_lo"] or self.band_hi < g["band_hi"]:
            raise SystemExit(
                f"FAIL_CLOSED {self.symbol} band [{self.band_lo}, {self.band_hi}] "
                f"does not cover registered guard [{g['band_lo']}, {g['band_hi']}]"
            )
        if abs(self.pip - g["pip"]) > 1e-12:
            # A different derived pip is NOT fatal by law, but it would
            # contradict the registered expectation — surface loudly.
            raise SystemExit(
                f"FAIL_CLOSED {self.symbol} derived pip {self.pip} != registered "
                f"expectation {g['pip']} — probe/registration contradiction"
            )


def load_pair_config(symbol: str) -> PairConfig:
    """Fail-closed loader: config file must exist, be proven, validate."""
    if not CONFIG_PATH.exists():
        raise SystemExit(
            f"FAIL_CLOSED {CONFIG_PATH} missing — run probe_pair.py first; "
            "scale/pip/band are probe-derived, never assumed (plan §5.2)"
        )
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


def load_all_pair_configs() -> dict:
    return {s: load_pair_config(s) for s in REGISTERED_GUARDS}
