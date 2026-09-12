"""VOL-NG1 P1 event-adjusted position layer (corp-actions handling).

Authority: the committed P0 RAW-vs-adjusted step inventory
(``research/control/vol_ng1_run/p0_gate.json``,
``sections.corp_actions_inventory`` -- measured 2026-09-12, V8
convention RAW primary).  EVERY inventoried step requires an explicit
event decision before any RAW-series consumption lane may use the leg;
silence is a fail-closed error, never an inference.

Event kinds (mechanical vs market, the only two questions that matter
for a return stream):

- ``SPLIT``        vendor-adjusted series is continuous across the
                   step (``ADJUSTED_CONTINUOUS`` / ``RESIDUAL`` with a
                   round implied factor): mechanical.  Measured factor
                   ``f = raw_ratio / adjusted_ratio``; value-preserving
                   re-statement is shares /= f, price *= f.
- ``REORG``        the step is present in BOTH series (vendor did not
                   compensate): the named 2018-01-25 VXX 64.0x step.
                   Mechanical reorganization, NOT a return: same
                   value-preserving re-statement, and the 64x is
                   cancelled from the return stream.
- ``PRICE_EVENT``  a genuine market move that the layer must KEEP as a
                   return: the named 2018-02-06 SVXY Volmageddon -83%
                   session.  No share/price restatement.

The named events (dispatch packet, VOL-NG1 P1): VXX 2024-07-24 factor
4.0; UVXY 2025-11-20 factor 5.0; VXX 2018-01-25 uncompensated 64.0x
reorg; SVXY 2018-02-06 Volmageddon -83% price event.

No proposals, no signals, no scoring, no outcome numbers anywhere.
"""

from __future__ import annotations

import json
import os
import sys

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

SCHEMA = "vol_ng1/corp_actions@1"

#: The committed P0 authority artifact that carries the step inventory.
P0_GATE_PATH = os.path.join(
    REPO_ROOT, "research", "control", "vol_ng1_run", "p0_gate.json")
P0_GATE_SCHEMA = "vol_ng1_run/p0_gate@1"

#: Same step-magnitude bounds as the P0 detector (census.py): a raw
#: ratio at or beyond these magnitudes MUST be covered by an event.
STEP_RATIO_GE = 3.0
STEP_RATIO_LE = 1.0 / 3.0

#: Named-event overrides from the dispatch packet (authoritative
#: instruction; measured factors still come from the inventory).
NAMED_EVENTS: dict[tuple[str, str], dict] = {
    ("VXX", "2018-01-25"): {
        "kind": "REORG",
        "note": ("uncompensated 64.0x reorg step present in BOTH raw "
                 "and adjusted series; handled as a reorg event, not "
                 "a return (dispatch packet)"),
    },
    ("SVXY", "2018-02-06"): {
        "kind": "PRICE_EVENT",
        "note": ("Volmageddon -83% session: a genuine market return "
                 "kept in the return stream (dispatch packet)"),
    },
    ("VXX", "2024-07-24"): {
        "kind": "SPLIT",
        "note": "4:1 split event (dispatch packet named factor 4.0)",
    },
    ("UVXY", "2025-11-20"): {
        "kind": "SPLIT",
        "note": "5:1 split event (dispatch packet named factor 5.0)",
    },
}

#: Nominal split factors (reverse/forward) accepted within 5% when
#: labelling an event; anything else stays unlabelled (measured only).
NOMINAL_FACTORS = (2.0, 3.0, 4.0, 5.0, 7.0, 8.0, 10.0, 20.0, 25.0,
                   50.0, 64.0, 100.0)
NOMINAL_TOL = 0.05


class CorpActionError(Exception):
    """Fail-closed corp-action state."""


class UncoveredStepError(CorpActionError):
    """A raw step at inventory magnitude has no explicit event."""


def load_inventory(gate_path: str | None = None) -> dict:
    """The committed P0 step inventory, verbatim (fail-closed)."""
    path = gate_path or P0_GATE_PATH
    if not os.path.isfile(path):
        raise CorpActionError(f"P0 gate artifact missing: {path}")
    with open(path, "r", encoding="utf-8") as fh:
        gate = json.load(fh)
    if gate.get("schema") != P0_GATE_SCHEMA:
        raise CorpActionError(
            f"P0 gate schema {gate.get('schema')!r} != "
            f"{P0_GATE_SCHEMA!r}: refusing to consume")
    inv = gate.get("sections", {}).get("corp_actions_inventory", {})
    observed = inv.get("observed", {})
    by_symbol = observed.get("by_symbol")
    if not isinstance(by_symbol, dict) or not by_symbol:
        raise CorpActionError(
            "P0 gate has no corp_actions_inventory by_symbol: refusing")
    total = 0
    for sym, block in by_symbol.items():
        steps = block.get("step_events") or []
        if not steps:
            raise CorpActionError(
                f"leg {sym!r} inventoried with zero step events")
        for s in steps:
            for key in ("date", "raw_ratio", "adjusted_ratio",
                        "implied_factor", "classification"):
                if key not in s:
                    raise CorpActionError(
                        f"step missing key {key!r} for {sym}: {s!r}")
        total += len(steps)
    if total != observed.get("total_steps_inventoried"):
        raise CorpActionError(
            f"inventory total mismatch: sum {total} != declared "
            f"{observed.get('total_steps_inventoried')}")
    return {"by_symbol": by_symbol, "total_steps": total,
            "gate_path": path}


def _nominal_factor(f: float) -> float | None:
    for n in NOMINAL_FACTORS:
        if abs(f - n) / n <= NOMINAL_TOL:
            return n
    return None


def build_event_table(inventory: dict) -> dict:
    """Explicit event decision for EVERY inventoried step.

    Resolution order: a named dispatch-packet override wins (provenance
    recorded); otherwise the P0 inventory classification decides
    (``ADJUSTED_CONTINUOUS``/``RESIDUAL`` -> SPLIT with measured factor
    ``raw_ratio/adjusted_ratio``; ``ADJUSTED_TRACKS_RAW`` -> REORG with
    measured factor ``raw_ratio``).
    """
    table: dict[str, list[dict]] = {}
    for sym, block in sorted(inventory["by_symbol"].items()):
        events = []
        for step in sorted(block["step_events"],
                           key=lambda s: s["date"]):
            raw_ratio = float(step["raw_ratio"])
            adj_ratio = float(step["adjusted_ratio"])
            if adj_ratio <= 0:
                raise CorpActionError(
                    f"non-positive adjusted ratio for {sym} "
                    f"{step['date']}: {adj_ratio}")
            key = (sym, step["date"])
            named = NAMED_EVENTS.get(key)
            klass = step["classification"]
            if klass in ("ADJUSTED_CONTINUOUS", "RESIDUAL"):
                kind = "SPLIT"
                factor = raw_ratio / adj_ratio
            elif klass == "ADJUSTED_TRACKS_RAW":
                kind = "REORG"
                factor = raw_ratio
            else:
                raise CorpActionError(
                    f"unhandled inventory class {klass!r} for {sym} "
                    f"{step['date']}")
            provenance = "p0_gate.corp_actions_inventory (measured)"
            if named is not None:
                kind = named["kind"]
                if kind == "PRICE_EVENT":
                    factor = 1.0  # no mechanical restatement
                provenance = ("dispatch packet vol-ng1-p1-kernel-costs "
                              "NAMED_EVENT; " + provenance)
            event = {
                "symbol": sym,
                "date": step["date"],
                "kind": kind,
                "factor": factor,
                "nominal_factor": _nominal_factor(factor),
                "raw_ratio": raw_ratio,
                "adjusted_ratio": adj_ratio,
                "p0_classification": klass,
                "named_note": (named or {}).get("note"),
                "provenance": provenance,
            }
            if kind == "REORG":
                # value preservation across a reorg restates shares and
                # price with the SAME factor; record the packet-named
                # magnitude for the audit trail.
                event["nominal_factor"] = _nominal_factor(raw_ratio)
            events.append(event)
        table[sym] = events
    return table


def require_coverage(symbol: str, events: list[dict]) -> None:
    """Every event must carry an explicit kind + positive factor."""
    if not events and symbol in ("VXX", "UVXY", "SVXY", "VIXY", "VIXM",
                                 "VXZ"):
        raise CorpActionError(
            f"leg {symbol!r} has no event decisions (P0 inventory "
            "requires explicit handling at every step)")
    for e in events:
        if e.get("kind") not in ("SPLIT", "REORG", "PRICE_EVENT"):
            raise CorpActionError(f"event without kind: {e!r}")
        f = float(e.get("factor") or 0.0)
        if f <= 0:
            raise CorpActionError(f"event with non-positive factor: {e!r}")


def event_adjusted_closes(bars: list[dict], events: list[dict]) -> dict:
    """RAW-close series with mechanical steps cancelled.

    Standard back-cancellation: for an event on date ``d`` with
    mechanical factor ``f``, every close strictly BEFORE ``d`` is
    multiplied by ``f``.  The adjusted ratio across ``d`` is then
    ``raw_ratio / f`` -- exactly 1.0 for a fully-mechanical step, and
    the true market return for a ``PRICE_EVENT`` (factor 1.0).

    ``bars`` are served EODHD objects (RAW ``close`` is primary);
    events must be explicit decisions from :func:`build_event_table`.
    """
    by_date = {}
    for b in bars:
        if not isinstance(b, dict) or not b.get("date"):
            continue
        close = b.get("close")
        if not isinstance(close, (int, float)) or close <= 0:
            raise CorpActionError(
                f"non-positive or missing RAW close at {b.get('date')}")
        by_date[b["date"]] = float(close)
    dates = sorted(by_date)
    for e in events:
        if e["date"] not in by_date:
            raise CorpActionError(
                f"event date {e['date']} for {e['symbol']} absent from "
                "the RAW bar grid")
    # cumulative mechanical multiplier applied to prices before each d
    adj = dict(by_date)
    for e in events:
        if e["kind"] == "PRICE_EVENT":
            continue
        f = float(e["factor"])
        for d in dates:
            if d < e["date"]:
                adj[d] = adj[d] * f
    return adj


def continuity_residuals(bars: list[dict], events: list[dict]) -> dict:
    """Per-event continuity law after mechanical cancellation.

    For every SPLIT/REORG the expected adjusted ratio across the step
    is (a) the P0-measured ``adjusted_ratio`` -- the same-day market
    move the vendor-adjusted series kept -- for a SPLIT, and (b)
    exactly 1.0 for a REORG (a pure reorganization is no return at
    all).  The residual is |measured-after-cancellation - expected|;
    a PRICE_EVENT is reported with its ratio (kept as a return, no
    expectation imposed).
    """
    adj = event_adjusted_closes(bars, events)
    rows = []
    for e in sorted(events, key=lambda e: e["date"]):
        d = e["date"]
        # the previous bar strictly before the event date
        before = [x for x in adj if x < d]
        if not before:
            raise CorpActionError(f"event {d} has no prior bar")
        p_prev = adj[max(before)]
        p_cur = adj[d]
        after_ratio = p_cur / p_prev
        expected = 1.0 if e["kind"] == "REORG" \
            else float(e.get("adjusted_ratio") or 1.0)
        rows.append({
            "symbol": e["symbol"],
            "date": d,
            "kind": e["kind"],
            "factor": e["factor"],
            "adjusted_ratio": after_ratio,
            "expected_adjusted_ratio": expected,
            "residual": abs(after_ratio - expected),
        })
    mech = [r["residual"] for r in rows
            if r["kind"] in ("SPLIT", "REORG")]
    return {
        "per_event": rows,
        "max_abs_mechanical_residual": max(mech) if mech else 0.0,
    }


def apply_event(shares: float, price: float, event: dict) -> tuple[float, float]:
    """Value-preserving position restatement across one event.

    SPLIT/REORG with measured factor f: shares /= f, price *= f ->
    value is INVARIANT by construction (hand-checkable).  A
    PRICE_EVENT restates nothing: the value change is the market
    return and stays in the return stream.
    """
    if shares <= 0 or price <= 0:
        raise CorpActionError("position restatement needs positive "
                              "shares and price")
    if event["kind"] == "PRICE_EVENT":
        return shares, price
    f = float(event["factor"])
    if f <= 0:
        raise CorpActionError("non-positive event factor")
    return shares / f, price * f


def scan_uncovered_steps(bars: list[dict], events: list[dict]) -> list[dict]:
    """Raw close steps at inventory magnitude (ratio >= 3.0 or
    <= 1/3) WITHOUT an explicit event decision.  Empty list == the
    event table covers the leg."""
    covered = {e["date"] for e in events}
    clean = sorted(
        (b for b in bars
         if isinstance(b, dict) and b.get("date")
         and isinstance(b.get("close"), (int, float))),
        key=lambda b: b["date"])
    uncovered = []
    for prev, cur in zip(clean, clean[1:]):
        if prev["close"] <= 0:
            continue
        ratio = cur["close"] / prev["close"]
        if (ratio >= STEP_RATIO_GE or ratio <= STEP_RATIO_LE) \
                and cur["date"] not in covered:
            uncovered.append({"date": cur["date"],
                              "raw_ratio": round(ratio, 6)})
    return uncovered


def inventory_mismatches(inventory: dict, table: dict) -> list[str]:
    """The event table must re-measure the P0 inventory exactly: same
    symbols, same step dates, same per-symbol counts."""
    problems = []
    inv_syms = set(inventory["by_symbol"])
    tab_syms = set(table)
    if inv_syms != tab_syms:
        problems.append(
            f"symbol sets differ: inventory={sorted(inv_syms)} "
            f"table={sorted(tab_syms)}")
    for sym in sorted(inv_syms & tab_syms):
        inv_dates = sorted(s["date"]
                           for s in inventory["by_symbol"][sym]["step_events"])
        tab_dates = sorted(e["date"] for e in table[sym])
        if inv_dates != tab_dates:
            problems.append(
                f"{sym}: step dates differ from the inventory: "
                f"{inv_dates} vs {tab_dates}")
    return problems
