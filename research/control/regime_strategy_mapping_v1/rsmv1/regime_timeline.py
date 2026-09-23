"""Regime-timeline rebuild from the FROZEN V2 decision cache (RSMV1 core law).

ZERO provider calls in this cycle. The effective + persisted regime timeline
per cell is RECOMPUTED deterministically from the cached V2 decisions
(`data_local/decisions_<cell>.jsonl`) using the V2 frozen semantic-state
builder, safety layer and persistence machine, byte-for-byte as at V2 commit
0c277a94 (forked modules in this package).

The rebuild is verified against V2's own recorded metrics (switches
90/31/34; effective-UNKNOWN shares 0.427/0.272/0.291; persisted occupancy
shares) before ANY downstream use. A mismatch is a hard stop
(`REGIME_TIMELINE_MISMATCH`) — never a silent proceed.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .freezes import Freezes
from .questionio import CacheProvider, DecisionStore, sequential_timeline
from .features import RegimeFeatures
from .data import load_cell

# V2 recorded values (classification report + scored metrics, A7-reproduced).
# Rebuild must reproduce these exactly (within float print precision).
V2_EXPECTED = {
    "BTC_H1": {"switches": 90, "eff_unknown_share": 0.427, "n_decisions": 8567},
    "BTC_H4": {"switches": 31, "eff_unknown_share": 0.272, "n_decisions": 1997},
    "SPY_D1": {"switches": 34, "eff_unknown_share": 0.291, "n_decisions": 2751},
}
SWITCH_TOL = 0  # exact
EFF_UNKNOWN_TOL = 0.002  # report rounding (3dp)

REGIME_TIMELINE_SCHEMA = "rsmv1_regime_timeline@1"


class RegimeTimelineMismatch(RuntimeError):
    """Rebuilt timeline disagrees with the V2 recorded metrics — hard stop."""


@dataclass
class CellTimelines:
    cell: str
    timeline: object  # rsmv1.questionio.Timeline
    regime_bars: object
    exec_bars: object
    period_ns: int
    stats: dict

    @property
    def ts(self) -> list[int]:
        return self.timeline.ts

    @property
    def persisted(self) -> list[str]:
        return self.timeline.persisted

    @property
    def effective(self) -> list[str]:
        return self.timeline.effective

    def persisted_at_close(self, ts_close_ns: int) -> str:
        """Latest persisted label whose regime-bar close is <= ts_close_ns.

        Fails closed to TRANSITION_UNKNOWN before the first decision.
        """
        import bisect

        i = bisect.bisect_right(self.ts, ts_close_ns) - 1
        if i < 0:
            return "TRANSITION_UNKNOWN"
        return self.persisted[i]


def rebuild_cell_timeline(cycle_dir: str | Path, cell: str) -> CellTimelines:
    """Recompute the cell's effective/persisted timeline from cached V2
    decisions; verify against V2 recorded metrics; return timelines."""
    cycle_dir = Path(cycle_dir).resolve()
    fz = Freezes(cycle_dir)
    exec_bars, regime_bars, period_ns = load_cell(fz, cell)
    feats = RegimeFeatures(regime_bars)
    store = DecisionStore.load(cycle_dir / "data_local" / f"decisions_{cell}.jsonl")
    provider = CacheProvider(store)
    pinned = fz.model_pin["pinned_model"]
    # V2 bulk law (run.py): requested_model == pinned model — the digest is
    # computed over canonical_json(state)||requested_model.
    tl = sequential_timeline(
        cell,
        fz,
        regime_bars,
        feats,
        provider,
        pinned_model=pinned,
        requested_model=pinned,
        strict=True,
    )
    stats = tl.stats()
    _verify_against_v2(cell, stats, len(store.by_state_id))
    return CellTimelines(
        cell=cell,
        timeline=tl,
        regime_bars=regime_bars,
        exec_bars=exec_bars,
        period_ns=period_ns,
        stats=stats,
    )


def _verify_against_v2(cell: str, stats: dict, cached_states: int) -> None:
    exp = V2_EXPECTED[cell]
    problems = []
    if stats["n_decisions"] != exp["n_decisions"]:
        problems.append(
            f"n_decisions {stats['n_decisions']} != V2 {exp['n_decisions']}"
        )
    if stats["switches"] != exp["switches"]:
        problems.append(f"switches {stats['switches']} != V2 {exp['switches']}")
    if abs(stats["effective_unknown_share"] - exp["eff_unknown_share"]) > EFF_UNKNOWN_TOL:
        problems.append(
            f"eff_unknown_share {stats['effective_unknown_share']:.4f} != V2 "
            f"{exp['eff_unknown_share']}"
        )
    if stats["n_decisions"] > cached_states:
        problems.append(
            f"timeline demands {stats['n_decisions']} states but cache holds "
            f"{cached_states} (incomplete cache — no re-asks allowed)"
        )
    if problems:
        raise RegimeTimelineMismatch(
            "REGIME_TIMELINE_MISMATCH[" + cell + "]: " + "; ".join(problems)
        )


def episodes(persisted: list[str]) -> list[dict]:
    """Maximal contiguous runs of the persisted stream (independent episodes).

    Episode boundaries include the stream edges; UNKNOWN episodes are
    reported but not selectable (§5 library: UNK_FLAT fixed).
    """
    out: list[dict] = []
    if not persisted:
        return out
    start = 0
    for i in range(1, len(persisted)):
        if persisted[i] != persisted[i - 1]:
            out.append(
                {"label": persisted[i - 1], "start": start, "end": i - 1,
                 "length": i - start}
            )
            start = i
    out.append(
        {"label": persisted[-1], "start": start, "end": len(persisted) - 1,
         "length": len(persisted) - start}
    )
    return out


def save_timeline_json(ct: CellTimelines, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "bar_index": r["bar_index"],
            "regime_bar_close_ns": r["regime_bar_close_ns"],
            "effective": r["effective"],
            "persisted": r["persisted"],
            "switched": r["switched"],
        }
        for r in ct.timeline.rows
    ]
    payload = {
        "schema": REGIME_TIMELINE_SCHEMA,
        "cell": ct.cell,
        "stats": ct.stats,
        "v2_expected": V2_EXPECTED[ct.cell],
        "rows": rows,
    }
    path.write_text(json.dumps(payload, sort_keys=True))
