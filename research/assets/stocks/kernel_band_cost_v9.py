"""V9 P1 kernel primitives: fail-closed band-cost resolution and the
driver-emitted ledger contract.

PLAN_stocks_v9.md sec 3 P1 carries two audited V8 findings into the kernel:

- L-I3 (V8 a7-indep): ``BAND_BPS.get(bands.get(n, "A"), 10.0)`` silently
  costed a changed name without a computed band at 10 bps. Reachable only
  for a name lacking 63 bars at the decision (delisted-mid-fold edge) - an
  edge the death-inclusive V9 universe makes ROUTINE, so the fallback is
  now a hard error and callers must prove band presence before costing.
- F-A7T-1 (V8 a7-terminal): the committed V8 ledger's published_delta was a
  publish-time bookkeeping edit. V9 ledgers carry driver-emitted counters
  only; any publication bookkeeping lives in a separate append-only record
  and never touches the driver artifact.

No PnL, no selection, no proposal content. Deterministic primitives with
hand-computed-fixture tests (tests/assets/stocks/test_v9_kernel.py).
"""

from __future__ import annotations

BAND_BPS = {"A": 10.0, "B": 15.0, "C": 25.0}
SCHEMA = "stocks_free_v9_run/kernel_band_cost@1"


class BandResolutionError(RuntimeError):
    """A traded name has no computed cost band: fail closed, never default."""


def band_of(adv: float) -> str:
    """Dollar-volume band - thresholds identical to the V8 kernel."""
    if adv >= 50_000_000:
        return "A"
    if adv >= 10_000_000:
        return "B"
    if adv >= 2_000_000:
        return "C"
    return "UNTRADABLE"


def resolve_band_bps(name: str, bands: dict[str, str]) -> float:
    """Band cost in bps for ``name``; missing band raises (L-I3 fix).

    An UNTRADABLE band is a deliberate computed verdict, not a missing one:
    the caller must have filtered UNTRADABLE names out of the tradable book
    before costing, and passing one here is also an error.
    """
    if name not in bands:
        raise BandResolutionError(
            f"no cost band for traded name {name!r} at decision - fail closed (L-I3)")
    b = bands[name]
    if b == "UNTRADABLE":
        raise BandResolutionError(
            f"name {name!r} resolved UNTRADABLE but reached costing - caller bug")
    if b not in BAND_BPS:
        raise BandResolutionError(f"unknown band {b!r} for {name!r}")
    return BAND_BPS[b]


def fill_cost_bps(name: str, dw: float, bands: dict[str, str], cost_mult: float) -> float:
    """Linear-in-fills cost (L-V14-0) for one name weight change."""
    return abs(dw) * resolve_band_bps(name, bands) * cost_mult / 10_000.0


def driver_ledger_counters(observed_delta: int, published_delta: int) -> dict:
    """The only sanctioned counter block shape for a V9 scored run.

    published_delta is driver-emitted (F-A7T-1): it counts cells the DRIVER
    itself published; publication bookkeeping performed after the run is
    recorded via append_publication_record, never by editing these numbers.
    """
    if published_delta > observed_delta:
        raise ValueError("published_delta cannot exceed driver-observed delta")
    return {
        "schema": SCHEMA,
        "counter_provenance": "driver_emitted (F-A7T-1); publish-time edits forbidden",
        "observed_delta": observed_delta,
        "published_delta": published_delta,
    }


def append_publication_record(existing: dict | None, **entry) -> dict:
    """Publication bookkeeping as a separate append-only record."""
    rec = dict(existing or {"schema": SCHEMA, "publication_records": []})
    rec.setdefault("publication_records", []).append(entry)
    return rec
