"""ONE constant law source for the exec runner (PAPERDESK-FIXALL-NCAA-V1
W1.6, owner work package 2026-10-21).

The runtime audit (A3/A7/G2) found the frozen constants copied by hand in
>=4 places (decision_pipeline.py, ai_gate.js, paper_policy.js, pinned core)
with no sync mechanism — one future edit silently splits the JS and Python
gates. LAW: every consumer imports from HERE; the JS side consumes ONLY the
generated `apps/paperdesk/main/laws_generated.js` (build_laws_js.py —
deterministic, byte-stable, parity-tested).

VALUES ARE UNCHANGED — this consolidates SOURCES, never re-tunes a gate.
Anchor lead constants stay defined in research/papertrade_exec/__init__.py
(the package's own frozen table) and are re-exported here so the JS mirror
has exactly one upstream too.
"""
from __future__ import annotations

from research.papertrade_exec import (  # noqa: F401  (re-export, one source)
    BATCH_LEAD_SECONDS,
    SOCCER_LEAD_SECONDS,
)

# --- decision gates (frozen values; single source) --------------------------
EV_THRESHOLD = 0.05            # BET requires EV_net >= 5% (pre- and
                               # post-cutover: the SAME 5% meaning)
DRAWDOWN_PAUSE = 0.10          # pause decisions at 10% drawdown from peak

# --- fees (W3.1 target law; pre-cutover vs PM book fee) ---------------------
FLAT_FEE_PRE_CUTOVER = 0.02    # pre-cutover Pinnacle EV convention (flat
                               # 2% deduction — an estimate, kept verbatim)
PM_TAKER_FEE_RATE = 0.05       # PM book fee = rate * p * (1-p) per share
                               # (pm_moneyline/wsl_lane walk law)

# --- EV outlier quarantine (W1.5 NEW operating law of this package) ---------
EV_OUTLIER_THRESHOLD = 1.00    # EV_net > 100% => QUARANTINED_EV_OUTLIER:
                               # mandatory independent re-quote + second
                               # source cross-check; still abnormal => never
                               # placed. NOT a change of the 5% gate.

# --- capital / stake law (mirror of the frozen wording; enforcement stays
#     in the pinned core — here it exists so the JS mirror and parity tests
#     have one textual source) ---------------------------------------------
STAKE_FRACTION_OF_EQUITY = 0.01
STAKE_ROUNDING = "(equity_cents + 50) // 100  (1% of equity, half-up)"
OPEN_CAP_CENTS_V2 = 50000      # pre-v3 open-exposure cap
OPEN_CAP_CENTS_V3 = 50000      # v3 cap (capital_v3 config open_cap_cents)


def as_dict() -> dict:
    """The generated JS file is a dump of THIS dict (build_laws_js.py)."""
    return {
        "EV_THRESHOLD": EV_THRESHOLD,
        "DRAWDOWN_PAUSE": DRAWDOWN_PAUSE,
        "FLAT_FEE_PRE_CUTOVER": FLAT_FEE_PRE_CUTOVER,
        "PM_TAKER_FEE_RATE": PM_TAKER_FEE_RATE,
        "EV_OUTLIER_THRESHOLD": EV_OUTLIER_THRESHOLD,
        "STAKE_FRACTION_OF_EQUITY": STAKE_FRACTION_OF_EQUITY,
        "STAKE_ROUNDING": STAKE_ROUNDING,
        "OPEN_CAP_CENTS_V2": OPEN_CAP_CENTS_V2,
        "OPEN_CAP_CENTS_V3": OPEN_CAP_CENTS_V3,
        "BATCH_LEAD_SECONDS": BATCH_LEAD_SECONDS,
        "SOCCER_LEAD_SECONDS": SOCCER_LEAD_SECONDS,
    }
