"""CRYPTO-V17 family-exposure registry (A8 driver lane).

Maps ``formula_id -> pure function over panel rows`` for the family-agnostic
scored-cell driver ``run_v17_cell.py``.  A family spec (frozen selection JSON)
never embeds code: its arms reference exposures BY ``formula_id`` and the
driver resolves them HERE.

Contract of a registered formula (binding, checked by the driver):

* signature ``f(panels, params) -> Dict[str, List[Optional[float]]]``
  where ``panels`` maps symbol -> list of panel rows (H1 rows, or the H4 /
  D1 frames the driver derives in memory from those same H1 rows) and
  ``params`` is the arm spec's ``params`` mapping;
* the returned lists are index-aligned with the bucket grid of each symbol
  (the driver validates lengths and refuses on mismatch);
* values are the DESIRED POSITION over the bucket that FOLLOWS the row the
  information came from, typically in {-1, 0, +1}; ``None`` marks an honest
  warmup bucket (no decision possible there);
* PURE: no I/O, no wall clock, no randomness, no globals mutated.  The
  one-bar availability law (a decision at bucket t may only consume rows
  with close_ts <= t-1) is enforced by the DRIVER, never by the formula.

Registry discipline:

* ``@register(formula_id, example_only=False)``; duplicate ids refused;
* ``example_only=True`` formulas are EXAMPLES for the test suite ONLY --
  the scored emission path of the driver refuses them outright, so an
  example can never surface as a scored proposal; the sanitized dry-run
  (outcome-blind) may still execute them.

THIS MODULE SHIPS EXACTLY ONE FORMULA, and it is an EXAMPLE:

``EXAMPLE_TEST_ONLY.h1_vwap_revert``
    EXAMPLE_TEST_ONLY.  Hourly mean-reversion flag on the H1 close-vs-VWAP
    displacement ``disp[t] = (last_price[t] - vwap[t]) / vwap[t]``:
    ``signal[t] = -sign(disp[t])`` when ``|disp[t]| >= threshold`` else 0.
    Params: ``threshold`` (required, > 0).  It exists so the driver's test
    suite can exercise the full pipeline on tiny synthetic panels; it is
    NOT a proposal, it has no mechanism story, and it is structurally
    adjacent to the V16 forbidden CLOSE-DISPLACE-FADE ancestry -- it must
    never be scored in production (the driver refuses it on the scored
    path by the ``EXAMPLE_TEST_ONLY.`` prefix convention enforced here).
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence

Formula = Callable[
    [Mapping[str, Sequence[Mapping[str, Any]]], Mapping[str, Any]],
    Dict[str, List[Optional[float]]],
]

#: Prefix that marks a formula id as an example for tests only.  The scored
#: emission path of the driver refuses any id carrying this prefix.
EXAMPLE_ONLY_PREFIX = "EXAMPLE_TEST_ONLY."

_REGISTRY: Dict[str, dict] = {}


def register(formula_id: str, *, example_only: bool = False) -> Callable[[Formula], Formula]:
    """Register one exposure formula under a unique id (fail closed)."""
    if not isinstance(formula_id, str) or not formula_id.strip():
        raise ValueError("formula_id must be a non-empty string")
    if formula_id in _REGISTRY:
        raise ValueError(f"formula {formula_id!r} already registered")

    def deco(fn: Formula) -> Formula:
        if not callable(fn):
            raise ValueError(f"formula {formula_id!r} must be callable")
        _REGISTRY[formula_id] = {
            "fn": fn,
            "example_only": bool(example_only),
        }
        return fn

    return deco


def resolve(formula_id: str) -> Formula:
    """Registry lookup; an unknown id is a hard refusal (never a guess)."""
    entry = _REGISTRY.get(formula_id)
    if entry is None:
        raise KeyError(
            f"unknown formula_id {formula_id!r}; registered: {sorted(_REGISTRY)}"
        )
    return entry["fn"]


def is_example_only(formula_id: str) -> bool:
    """True iff the id is reserved for tests (prefix convention + registry flag)."""
    if formula_id.startswith(EXAMPLE_ONLY_PREFIX):
        return True
    entry = _REGISTRY.get(formula_id)
    return bool(entry and entry["example_only"])


def registered_ids() -> List[str]:
    return sorted(_REGISTRY)


def sign(x: float) -> int:
    if x > 0.0:
        return 1
    if x < 0.0:
        return -1
    return 0


# --------------------------------------------------------------------------- #
# The ONE shipped formula -- EXAMPLE FOR TESTS ONLY (see module docstring)
# --------------------------------------------------------------------------- #
@register("EXAMPLE_TEST_ONLY.h1_vwap_revert", example_only=True)
def example_h1_vwap_revert(
    panels: Mapping[str, Sequence[Mapping[str, Any]]],
    params: Mapping[str, Any],
) -> Dict[str, List[Optional[float]]]:
    """EXAMPLE_TEST_ONLY hourly mean-reversion flag on close-vs-VWAP.

    signal[t] = -sign((last_price[t] - vwap[t]) / vwap[t])
                if |(last_price[t] - vwap[t]) / vwap[t]| >= threshold
            else 0.0;  None where vwap is undefined/non-positive.
    Params: {"threshold": float > 0}.  Memoryless; the driver's one-bar lag
    makes the decision at bucket t consume row t-1 only.
    """
    threshold = float(params["threshold"])
    if not threshold > 0.0:
        raise ValueError("EXAMPLE_TEST_ONLY.h1_vwap_revert threshold must be > 0")
    out: Dict[str, List[Optional[float]]] = {}
    for sym, rows in panels.items():
        series: List[Optional[float]] = []
        for row in rows:
            vwap = float(row["vwap"])
            last = float(row["last_price"])
            if not (vwap > 0.0) or not (last > 0.0):
                series.append(None)
                continue
            disp = (last - vwap) / vwap
            series.append(
                float(-sign(disp)) if abs(disp) >= threshold else 0.0
            )
        out[sym] = series
    return out


__all__ = [
    "EXAMPLE_ONLY_PREFIX",
    "example_h1_vwap_revert",
    "is_example_only",
    "register",
    "registered_ids",
    "resolve",
    "sign",
]
