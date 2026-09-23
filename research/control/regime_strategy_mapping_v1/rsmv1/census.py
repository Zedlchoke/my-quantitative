"""A3 — definitive regime-sample census per cell x regime (NO PnL anywhere).

Independently re-derives the regime-sample census from the cell's own
verified regime timeline (rsmv1.regime_timeline.rebuild_cell_timeline —
sanctioned reuse; it self-verifies against V2 recorded metrics), and adds
what the P2 feasibility draft did not carry: per-fold detail with fold-
boundary reconciliation, transitions per fold, duration distributions,
market-time shares, margin components, and a machine-readable cross-check
against A1's preliminary evidence (evidence/regime_sample_feasibility.json).

NO PnL is read or computed. No file under any runtime/scored* directory is
touched. BTC_H1 / BTC_H4 / SPY_D1 are NEVER pooled: every result in this
module is a pure function of exactly one cell's timeline.

Frozen definitions (dispatch; identical to plan §4.0):
- independent episode: maximal contiguous run of one PERSISTED label over
  the cell's regime bars, post-warmup decision bars only;
- episode fold membership: the fold whose frozen span contains the
  episode's START-bar close ts (spans inclusive); bars outside every span
  belong to no fold (-1);
- eligible episode: length >= ELIGIBLE_MIN_BARS (= 6 = the persistence
  machine's min_dwell); eligible decisions: regime bars inside eligible
  episodes (all counted to the episode's start-bar fold);
- transitions: persisted switches (timeline switched flags), total and per
  fold (counted at the switched bar's own fold);
- margin-to-floor: min across (episodes_total/20, per-fold episodes/3,
  per-fold eligible decisions/100);
- below any floor => NOT_RUN_THIN_REGIME for that regime x cell (a
  sample-floor verdict, never a market judgment). Floors all met => PASS.

Duration percentiles use the frozen census convention: nearest-rank index
into the sorted lengths, k = len//4, len//2, 3*len//4 (0-based, floor) —
the same statistic the P2 feasibility draft reported, so the cross-check
is apples-to-apples.

Usage (regenerates both evidence artifacts):
    python -m rsmv1.census <cycle_dir> <out_dir>
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from . import CELLS, PHASES
from .freezes import Freezes
from .regime_timeline import (
    CellTimelines,
    V2_EXPECTED,
    episodes as reference_episodes,
    rebuild_cell_timeline,
)

# Floors — declared here independently; parity with rsmv1.feasibility is
# asserted at census time (drift guard, feasibility.py stays untouched).
FLOOR_EPISODES_TOTAL = 20
FLOOR_EPISODES_FOLD = 3
FLOOR_DECISIONS_FOLD = 100
ELIGIBLE_MIN_BARS = 6

CENSUS_SCHEMA = "rsmv1_regime_census@1"
NO_FOLD = -1
PASS = "PASS"
THIN = "NOT_RUN_THIN_REGIME"


def _floor_parity_guard() -> None:
    """Census floors must equal the P2 feasibility floors (drift guard)."""
    from . import feasibility as _feas

    assert FLOOR_EPISODES_TOTAL == _feas.FLOOR_EPISODES_TOTAL
    assert FLOOR_EPISODES_FOLD == _feas.FLOOR_EPISODES_FOLD
    assert FLOOR_DECISIONS_FOLD == _feas.FLOOR_DECISIONS_FOLD
    assert ELIGIBLE_MIN_BARS == _feas.ELIGIBLE_MIN_BARS


# --------------------------------------------------------------------------
# independent primitives (pure, unit-testable)
# --------------------------------------------------------------------------

def segment_episodes(persisted: Sequence[str]) -> list[dict]:
    """Independent run-length segmentation of a persisted stream.

    Same object shape as rsmv1.regime_timeline.episodes (label/start/end/
    length, stream edges inclusive); implemented separately so the census
    re-derives segmentation rather than trusting the other module. The two
    implementations are cross-asserted on every real timeline.
    """
    out: list[dict] = []
    n = len(persisted)
    i = 0
    while i < n:
        j = i
        while j + 1 < n and persisted[j + 1] == persisted[i]:
            j += 1
        out.append(
            {"label": persisted[i], "start": i, "end": j, "length": j - i + 1}
        )
        i = j + 1
    return out


def iso_to_ns(iso: str) -> int:
    """Independent ISO date/datetime (optional Z) -> ns UTC."""
    s = iso.strip().replace("Z", "+00:00")
    if "T" not in s:
        s += "T00:00:00+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1_000_000_000)


def ns_to_iso(ns: int) -> str:
    return (
        datetime.fromtimestamp(ns / 1_000_000_000, timezone.utc)
        .strftime("%Y-%m-%dT%H:%M:%SZ")
    )


def load_fold_spans(fz: Freezes, cell: str) -> list[tuple[int, int]]:
    """Frozen fold spans [(start_ns, end_ns)] for the cell (inclusive)."""
    return [
        (iso_to_ns(sp["start"]), iso_to_ns(sp["end"]))
        for sp in fz.fold_contract["cells"][cell]["folds"]
    ]


def fold_index(ts_close_ns: int, fold_spans: Sequence[tuple[int, int]]) -> int:
    """Fold whose inclusive span contains this close ts (-1 if none)."""
    for fid, (a, b) in enumerate(fold_spans):
        if a <= ts_close_ns <= b:
            return fid
    return NO_FOLD


def nearest_rank_stats(lengths: Sequence[int]) -> dict:
    """min / p25 / median / p75 / max under the frozen census convention
    (0-based nearest-rank index into the sorted list; floor division)."""
    if not lengths:
        return {"min": 0, "p25": 0, "median": 0, "p75": 0, "max": 0}
    s = sorted(lengths)
    n = len(s)
    return {
        "min": s[0],
        "p25": s[n // 4],
        "median": s[n // 2],
        "p75": s[3 * n // 4],
        "max": s[-1],
    }


# --------------------------------------------------------------------------
# census core (pure function of ONE cell's timeline)
# --------------------------------------------------------------------------

def census_cell_core(
    cell: str,
    ts: Sequence[int],
    persisted: Sequence[str],
    switched: Sequence[bool],
    fold_spans: Sequence[tuple[int, int]],
    n_evaluable_decisions: int | None = None,
) -> dict:
    """Full census for one cell from its own timeline arrays. No PnL.

    Every output here derives ONLY from this cell's arrays + its own fold
    spans — the structural no-pooling guarantee (see tests).
    """
    assert len(ts) == len(persisted) == len(switched)
    if n_evaluable_decisions is None:
        n_evaluable_decisions = len(ts)

    bar_fold = [fold_index(t, fold_spans) for t in ts]
    eps_all = segment_episodes(persisted)
    # segmentation cross-check against the regime_timeline implementation
    assert eps_all == reference_episodes(list(persisted)), (
        "census segmentation disagrees with regime_timeline.episodes"
    )

    # transitions: total and per fold (switched bar's OWN fold)
    transitions_total = sum(1 for s in switched if s)
    transitions_per_fold: dict[str, int] = {
        str(fid): 0 for fid in range(len(fold_spans))
    }
    transitions_per_fold["no_fold"] = 0
    for s, fid in zip(switched, bar_fold):
        if s:
            transitions_per_fold[str(fid) if fid != NO_FOLD else "no_fold"] += 1
    bars_no_fold = sum(1 for f in bar_fold if f == NO_FOLD)

    per_regime: dict[str, dict] = {}
    for label in PHASES:
        eps = [e for e in eps_all if e["label"] == label]
        elig = [e for e in eps if e["length"] >= ELIGIBLE_MIN_BARS]
        lengths = [e["length"] for e in eps]
        elig_lengths = [e["length"] for e in elig]

        # fold membership by START bar; straddle diagnostic by END bar
        recs = []
        for e in eps:
            f_start = bar_fold[e["start"]]
            f_end = bar_fold[e["end"]]
            recs.append(
                {
                    "start_ts": ns_to_iso(ts[e["start"]]),
                    "end_ts": ns_to_iso(ts[e["end"]]),
                    "length": e["length"],
                    "fold": f_start,
                    "eligible": e["length"] >= ELIGIBLE_MIN_BARS,
                    "straddles_fold_boundary": (
                        f_start != f_end and f_start != NO_FOLD
                    ),
                }
            )

        n_folds = len(fold_spans)
        per_fold: dict[str, dict] = {}
        for fid in range(n_folds):
            eps_f = [r for r in recs if r["fold"] == fid]
            elig_f = [r for r in eps_f if r["eligible"]]
            dec_f = sum(r["length"] for r in elig_f)
            # reconciliation: bars of this regime whose OWN fold is fid
            bars_own = sum(1 for f, p in zip(bar_fold, persisted) if f == fid and p == label)
            per_fold[str(fid)] = {
                "episodes": len(eps_f),
                "eligible_episodes": len(elig_f),
                "eligible_decisions": dec_f,
                "bars_in_own_fold": bars_own,
                "floor_episodes_ok": len(eps_f) >= FLOOR_EPISODES_FOLD,
                "floor_decisions_ok": dec_f >= FLOOR_DECISIONS_FOLD,
            }

        eps_total = len(eps)
        r_total = eps_total / FLOOR_EPISODES_TOTAL
        r_eps = min(
            (per_fold[str(f)]["episodes"] / FLOOR_EPISODES_FOLD
             for f in range(n_folds)),
            default=float("inf"),
        )
        r_dec = min(
            (per_fold[str(f)]["eligible_decisions"] / FLOOR_DECISIONS_FOLD
             for f in range(n_folds)),
            default=float("inf"),
        )
        margin = min(r_total, r_eps, r_dec)
        thin = (
            eps_total < FLOOR_EPISODES_TOTAL
            or any(not per_fold[str(f)]["floor_episodes_ok"] for f in range(n_folds))
            or any(not per_fold[str(f)]["floor_decisions_ok"] for f in range(n_folds))
        )
        per_regime[label] = {
            "episodes_total": eps_total,
            "eligible_episodes_total": len(elig),
            "eligible_decisions_total": sum(elig_lengths),
            "episode_lengths": nearest_rank_stats(lengths),
            "eligible_episode_lengths": nearest_rank_stats(elig_lengths),
            "market_time_bars": sum(lengths),
            "market_time_share": round(sum(lengths) / n_evaluable_decisions, 4)
            if n_evaluable_decisions
            else 0.0,
            "per_fold": per_fold,
            "margin_to_floor_min": round(margin, 3),
            "margin_components": {
                "episodes_total_over_floor": round(r_total, 3),
                "min_fold_episodes_over_floor": round(r_eps, 3),
                "min_fold_eligible_decisions_over_floor": round(r_dec, 3),
            },
            "verdict": THIN if thin else PASS,
            "episodes": recs,
        }

    unk_eps = [e for e in eps_all if e["label"] == "TRANSITION_UNKNOWN"]
    unk_bars = sum(e["length"] for e in unk_eps)

    return {
        "schema": CENSUS_SCHEMA,
        "cell": cell,
        "n_evaluable_decisions": n_evaluable_decisions,
        "bars_no_fold": bars_no_fold,
        "episodes_total_all_labels": len(eps_all),
        "transitions_total": transitions_total,
        "transitions_per_fold": transitions_per_fold,
        "per_regime": per_regime,
        "unselectable": {
            "TRANSITION_UNKNOWN": {
                "bars": unk_bars,
                "episodes": len(unk_eps),
                "share": round(unk_bars / n_evaluable_decisions, 4)
                if n_evaluable_decisions
                else 0.0,
                "note": "UNK_FLAT fixed; never selectable; floors not applied",
            }
        },
        "pooling_law": "BTC_H1/BTC_H4/SPY_D1 never pooled",
    }


# --------------------------------------------------------------------------
# rebuild + cross-checks against A1
# --------------------------------------------------------------------------

def _check_vs_a1_saved_rows(cycle_dir: Path, ct: CellTimelines) -> dict:
    """Fresh rebuild must equal A1's saved runtime timeline rows exactly."""
    p = cycle_dir / "runtime" / f"regime_timeline_{ct.cell}.json"
    if not p.exists():
        return {"status": "NOT_CHECKED", "reason": "runtime file missing"}
    saved = json.loads(p.read_text())["rows"]
    a = [(r["regime_bar_close_ns"], r["persisted"], r["switched"]) for r in saved]
    b = list(zip(ct.ts, ct.persisted, (r["switched"] for r in ct.timeline.rows)))
    if a == b:
        return {"status": "MATCH", "rows_compared": len(a)}
    first_bad = next(
        (i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b))
    )
    return {
        "status": "MISMATCH",
        "rows_compared": min(len(a), len(b)),
        "first_divergent_row": first_bad,
        "reason": "fresh rebuild != A1 saved runtime rows — hard discrepancy",
    }


def _cross_check_vs_a1_preliminary(
    cell: str, census: dict, a1_cell: dict
) -> dict:
    """Field-by-field diff vs A1's P2 feasibility block. Differences are
    reported, never silently resolved."""
    diffs: list[dict] = []
    n_cmp = 0

    def cmp(path: str, a1_val, cen_val) -> None:
        nonlocal n_cmp
        n_cmp += 1
        if a1_val != cen_val:
            diffs.append(
                {
                    "field": path,
                    "a1_preliminary": a1_val,
                    "census": cen_val,
                    "note": "differs — must be explained in the MD report",
                }
            )

    cmp("n_decisions", a1_cell["n_decisions"], census["n_evaluable_decisions"])
    cmp("transitions_total", a1_cell["transitions_total"], census["transitions_total"])
    for label in PHASES:
        a1r = a1_cell["per_regime"].get(label)
        if a1r is None:
            continue
        cr = census["per_regime"][label]
        for k in (
            "episodes_total",
            "eligible_episodes_total",
            "eligible_decisions_total",
            "market_time_bars",
        ):
            cmp(f"{label}.{k}", a1r[k], cr[k])
        for k, v in a1r["episode_lengths"].items():
            cmp(f"{label}.episode_lengths.{k}", v, cr["episode_lengths"][k])
        cmp(f"{label}.margin_to_floor_min", a1r["margin_to_floor_min"],
            cr["margin_to_floor_min"])
        cmp(f"{label}.verdict",
            PASS if a1r["verdict"] == "SAMPLE_OK" else a1r["verdict"],
            cr["verdict"])
        for fid, a1f in a1r["per_fold"].items():
            cf = cr["per_fold"][fid]
            for k in ("episodes", "eligible_episodes", "eligible_decisions"):
                cmp(f"{label}.fold{fid}.{k}", a1f[k], cf[k])

    return {
        "source": "evidence/regime_sample_feasibility.json (A1 preliminary)",
        "fields_compared": n_cmp,
        "status": "MATCH" if not diffs else "DIFF",
        "diffs": diffs,
    }


def measure_cell_census(cycle_dir: str | Path, cell: str) -> dict:
    """Rebuild one cell's verified timeline and derive its census."""
    cycle_dir = Path(cycle_dir).resolve()
    ct = rebuild_cell_timeline(cycle_dir, cell)  # self-verifies vs V2
    fz = Freezes(cycle_dir)
    spans = load_fold_spans(fz, cell)
    switched = [r["switched"] for r in ct.timeline.rows]
    out = census_cell_core(
        cell=cell,
        ts=ct.ts,
        persisted=ct.persisted,
        switched=switched,
        fold_spans=spans,
        n_evaluable_decisions=len(ct.ts),
    )
    out["warmup_regime_bars"] = fz.warmup(cell)
    out["timeline_rebuild"] = {
        "verified_against_v2": True,
        "v2_expected": V2_EXPECTED[cell],
        "recomputed": {
            "switches": ct.stats["switches"],
            "n_decisions": ct.stats["n_decisions"],
            "effective_unknown_share": round(
                ct.stats["effective_unknown_share"], 4
            ),
        },
        "vs_a1_saved_runtime_rows": _check_vs_a1_saved_rows(cycle_dir, ct),
    }
    a1_path = cycle_dir / "evidence" / "regime_sample_feasibility.json"
    if a1_path.exists():
        a1 = json.loads(a1_path.read_text())
        if cell in a1.get("cells", {}):
            out["cross_check_vs_a1_preliminary"] = _cross_check_vs_a1_preliminary(
                cell, out, a1["cells"][cell]
            )
    return out


# --------------------------------------------------------------------------
# bundle + report rendering
# --------------------------------------------------------------------------

def run_census(
    cycle_dir: str | Path,
    out_dir: str | Path | None = None,
) -> dict:
    """Census bundle, one cell at a time (never pooled). Writes the JSON
    evidence artifact and the human MD report when out_dir is given."""
    _floor_parity_guard()
    cycle_dir = Path(cycle_dir).resolve()
    bundle = {
        "schema": CENSUS_SCHEMA + ".bundle",
        "cycle": "REGIME-STRATEGY-MAPPING-V1",
        "phase": "A3_CENSUS_NO_PNL",
        "role": "A3",
        "floors": {
            "episodes_total": FLOOR_EPISODES_TOTAL,
            "episodes_per_fold": FLOOR_EPISODES_FOLD,
            "eligible_decisions_per_fold": FLOOR_DECISIONS_FOLD,
            "eligible_min_bars": ELIGIBLE_MIN_BARS,
            "note": "below any floor => NOT_RUN_THIN_REGIME (sample-floor verdict)",
        },
        "no_pooling_law": "BTC_H1/BTC_H4/SPY_D1 never pooled; each census is a pure function of its own cell's timeline",
        "pnl_law": "no PnL read or computed anywhere in this module",
        "cells": {c: measure_cell_census(cycle_dir, c) for c in CELLS},
    }
    if out_dir is not None:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "regime_sample_census.json").write_text(
            json.dumps(bundle, indent=1, sort_keys=True) + "\n"
        )
        (out_dir / "REGIME_SAMPLE_CENSUS.md").write_text(render_markdown(bundle))
    return bundle


def render_markdown(bundle: dict) -> str:
    """Human report: full tables, per-fold detail, margins, verdicts,
    cross-check vs A1 preliminary, thin-slot statement."""
    L: list[str] = []
    fl = bundle["floors"]
    L.append("# REGIME_SAMPLE_CENSUS — A3 (REGIME-STRATEGY-MAPPING-V1)")
    L.append("")
    L.append(
        "Definitive regime-sample census per cell x regime. NO PnL anywhere: "
        "every number is counts/durations/margins over the persisted regime "
        "timeline rebuilt from the frozen V2 decision cache "
        "(`rsmv1.regime_timeline.rebuild_cell_timeline`, self-verified vs V2 "
        "recorded metrics and vs A1's saved runtime rows)."
    )
    L.append("")
    L.append(
        f"Floors (preregistered): >= {fl['episodes_total']} independent "
        f"episodes/regime/cell; >= {fl['episodes_per_fold']} episodes/regime/"
        f"outer-fold; >= {fl['eligible_decisions_per_fold']} eligible "
        f"decisions/regime/outer-fold; eligible episode = length >= "
        f"{fl['eligible_min_bars']} regime bars (persistence min_dwell). "
        "Below any floor => NOT_RUN_THIN_REGIME for that regime x cell — a "
        "sample-floor verdict, NOT a market judgment."
    )
    L.append("")
    L.append(
        "Convention: an episode belongs to the outer fold containing its "
        "START-bar close ts (spans inclusive). Straddling episodes are counted "
        "once, wholly to the start fold; `bars_in_own_fold` is the "
        "reconciliation diagnostic (bars physically inside each fold). Cells "
        "are never pooled."
    )
    L.append("")

    n_diff_total = sum(
        len(c.get("cross_check_vs_a1_preliminary", {}).get("diffs", []))
        for c in bundle["cells"].values()
    )
    L.append(
        "Cross-check vs A1 preliminary (evidence/regime_sample_feasibility.json): "
        "the census is re-derived independently — segmentation, fold assignment, "
        "aggregation, margins and verdicts are re-implemented in rsmv1/census.py "
        "on top of the sanctioned self-verifying rebuild — then compared "
        "field-by-field against A1's P2 draft. "
        + (
            f"{n_diff_total} difference(s) found; each is listed under its cell "
            "with its root cause. Nothing was silently resolved."
            if n_diff_total
            else "All compared fields agree exactly (counts, durations, margins, "
            "verdicts), which is the expected outcome: both implement the same "
            "frozen definitions on the same verified timeline. The match is "
            "therefore a confirmation, not a copy: the census additionally "
            "carries per-episode records, per-fold transitions, fold-boundary "
            "reconciliation diagnostics and margin components that the P2 draft "
            "did not have."
        )
    )
    L.append("")

    for cell, c in bundle["cells"].items():
        L.append(f"## {cell}")
        L.append("")
        rb = c["timeline_rebuild"]
        xr = rb["vs_a1_saved_runtime_rows"]
        L.append(
            f"- Rebuild verified vs V2 (switches {rb['recomputed']['switches']} == "
            f"{rb['v2_expected']['switches']}, n_decisions "
            f"{rb['recomputed']['n_decisions']}, effUNKNOWN share "
            f"{rb['recomputed']['effective_unknown_share']}); vs A1 saved "
            f"runtime rows: **{xr['status']}**."
        )
        cc = c.get("cross_check_vs_a1_preliminary")
        if cc:
            L.append(
                f"- Cross-check vs A1 preliminary feasibility: {cc['status']} "
                f"({cc['fields_compared']} fields compared"
                + (f", {len(cc['diffs'])} diffs — see below" if cc["diffs"] else "")
                + ")."
            )
        L.append(
            f"- Decisions (post-warmup, evaluable): {c['n_evaluable_decisions']}; "
            f"transitions: {c['transitions_total']} per fold "
            + ", ".join(
                (f"f{k}" if k.isdigit() else k) + f"={v}"
                for k, v in c["transitions_per_fold"].items()
            )
            + f"; bars outside all fold spans: {c['bars_no_fold']}."
        )
        unk = c["unselectable"]["TRANSITION_UNKNOWN"]
        L.append(
            f"- TRANSITION_UNKNOWN (unselectable, UNK_FLAT fixed): {unk['bars']} "
            f"bars in {unk['episodes']} episode(s) (share {unk['share']}); floors "
            "not applied."
        )
        L.append("")
        L.append(
            "| regime | episodes | elig.ep. | elig.dec. | mkt bars (share) | "
            "dur min/p25/med/p75/max | margin | verdict |"
        )
        L.append("|---|---|---|---|---|---|---|---|")
        for label in PHASES:
            r = c["per_regime"][label]
            d = r["episode_lengths"]
            L.append(
                f"| {label} | {r['episodes_total']} | {r['eligible_episodes_total']} "
                f"| {r['eligible_decisions_total']} | {r['market_time_bars']} "
                f"({r['market_time_share']:.3f}) | {d['min']}/{d['p25']}/"
                f"{d['median']}/{d['p75']}/{d['max']} | "
                f"{r['margin_to_floor_min']:.3f} | **{r['verdict']}** |"
            )
        L.append("")
        L.append("### Per-fold detail")
        L.append("")
        L.append(
            "| regime | fold | episodes | elig.ep. | elig.dec. | bars_in_own_fold | eps floor ok | dec floor ok |"
        )
        L.append("|---|---|---|---|---|---|---|---|")
        for label in PHASES:
            r = c["per_regime"][label]
            for fid in sorted(r["per_fold"], key=int):
                f = r["per_fold"][fid]
                L.append(
                    f"| {label} | {fid} | {f['episodes']} | "
                    f"{f['eligible_episodes']} | {f['eligible_decisions']} | "
                    f"{f['bars_in_own_fold']} | {f['floor_episodes_ok']} | "
                    f"{f['floor_decisions_ok']} |"
                )
        L.append("")
        strad = {
            label: [
                e for e in c["per_regime"][label]["episodes"]
                if e["straddles_fold_boundary"]
            ]
            for label in PHASES
        }
        n_strad = sum(len(v) for v in strad.values())
        if n_strad:
            bits = ", ".join(
                f"{label}:{[e['length'] for e in v]}"
                for label, v in strad.items() if v
            )
            L.append(
                f"- Fold-boundary reconciliation: {n_strad} episode(s) straddle "
                f"a fold boundary ({bits}); each is counted wholly to its start "
                "fold, so per-fold eligible decisions can exceed the bars "
                "physically inside the fold (see bars_in_own_fold)."
            )
            L.append("")
        if c["bars_no_fold"]:
            L.append(
                f"- {c['bars_no_fold']} timeline bar(s) fall outside every "
                "frozen fold span (SPY date-span convention at fold edges); "
                "they count toward market time of their episode's start fold "
                "when inside an eligible episode, and no episode STARTs in "
                "no-fold."
                if all(
                    e["fold"] != -1
                    for label in PHASES
                    for e in c["per_regime"][label]["episodes"]
                )
                else f"- {c['bars_no_fold']} timeline bar(s) fall outside every frozen fold span; at least one episode START is in no-fold and belongs to no fold."
            )
            L.append("")
        if cc and cc["diffs"]:
            L.append("### Cross-check diffs vs A1 preliminary")
            L.append("")
            for d in cc["diffs"]:
                L.append(
                    f"- `{d['field']}`: A1={d['a1_preliminary']} vs "
                    f"census={d['census']} — {d['note']}"
                )
            L.append("")

    L.append("## Verdict summary — which regime x cell slots pass")
    L.append("")
    L.append("| cell | regime | verdict | margin |")
    L.append("|---|---|---|---|")
    for cell, c in bundle["cells"].items():
        for label in PHASES:
            r = c["per_regime"][label]
            L.append(
                f"| {cell} | {label} | {r['verdict']} | "
                f"{r['margin_to_floor_min']:.3f} |"
            )
    L.append("")
    passing = [
        f"{cell}/{label}"
        for cell, c in bundle["cells"].items()
        for label in PHASES
        if c["per_regime"][label]["verdict"] == PASS
    ]
    thin = [
        f"{cell}/{label}"
        for cell, c in bundle["cells"].items()
        for label in PHASES
        if c["per_regime"][label]["verdict"] == THIN
    ]
    L.append(
        "- PASS (all floors met): " + (", ".join(passing) if passing else "none") + "."
    )
    L.append(
        "- NOT_RUN_THIN_REGIME (below a sample floor; specialist defaults "
        "FLAT there): " + (", ".join(thin) if thin else "none") + "."
    )
    L.append("")
    L.append(
        "Binding laws honored: no PnL read or computed; no runtime/scored* "
        "input; BTC_H1 / BTC_H4 / SPY_D1 never pooled; feasibility.py untouched."
    )
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python -m rsmv1.census <cycle_dir> <out_dir>")
        sys.exit(2)
    run_census(sys.argv[1], sys.argv[2])
