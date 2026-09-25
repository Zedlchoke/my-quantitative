"""basislv_replication DRY-RUN -- sanitized traversal of the window-fold
binding over the four preregistered replication folds.  NO PnL, NO scored
metric, NO cost/funding number, NO scored ledger.

Cycle CRYPTO-HISTORICAL-REPLICATION-3F-V1, namespace basislv_replication.

Per fold (Y2021, Y2022, Y2023, Y2024P) the REAL scored plugin surface is
traversed exactly as the frozen runner will traverse it later
(``BasislvWindowFoldPlugin.targets_at`` on every OPEN instant
``schedule[:-1]``), with the ANCHOR arm ``BASISLV-PREMFADE-28D`` (the INV
control arm is the element-wise negation of the same book -- eligibility,
side geometry and constructibility are identical by construction, so one
arm's traversal measures both; disclosed).  Reported per fold x stamp:

* ``targets_at``-style STATUS only: ``OK`` (constructible book, >= 1 leg),
  ``OK-flat-empty`` (status OK with zero legs and no refusal reason --
  would be an anomaly, counted if it ever occurs),
  ``INSUFFICIENT_ELIGIBLE`` (the flat refusal-counted book: fewer than
  ``MIN_ELIGIBLE`` = 12 eligible names -- the engine's own eligibility
  decided), ``FORCE_FLAT`` (window fold-terminal flat transition),
* per-stamp eligible counts, refused counts by reason, side size, weight
  count.

BASISLV has no gate: nothing is gated here.  Non-vacuousness bar: >= 1
constructible book per fold.  Basis warmup (28d = 2688 buckets) is
satisfiable from the staged full-depth B-window basis (2020-06/07 or
listing date .. 2024-08-19).  Y2021 has exactly 12 listed of the frozen 19
(MIN_ELIGIBLE = 12, ZERO margin) -- per-stamp counts are reported honestly.

Heavy lock NOT required: no scored compute; catalog reads are local.

Output: ``basislv_replication/dryrun_report.json`` + this stdout summary.
Writes ONLY inside this namespace.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from replication_data import (  # noqa: E402
    CATALOG,
    FEED_SYMBOLS,
    FOLDS,
    UNIVERSE,
    iso_utc,
    load_basis_world,
    load_execution_bars_catalog,
)
from gated_plugin import BasislvWindowFoldPlugin  # noqa: E402
from research.adapter_v10.protocol import AdapterError  # noqa: E402
from research.v14.families.basislv_premfade.plugin import (  # noqa: E402
    REASON_FOLD_TERMINAL_FORCE_FLAT,
)
from research.v14.families.basislv_premfade.strategy import (  # noqa: E402
    ANCHOR_ARM,
    MIN_ELIGIBLE,
)
from gated_plugin import REASON_INSUFFICIENT_ELIGIBLE_REFUSAL  # noqa: E402

DRYRUN_ARM = ANCHOR_ARM  # INV is the exact sign flip; same eligibility geometry


def classify(book: dict) -> str:
    reason = book.get("reason_code")
    if reason == REASON_FOLD_TERMINAL_FORCE_FLAT:
        return "FORCE_FLAT"
    if reason == REASON_INSUFFICIENT_ELIGIBLE_REFUSAL:
        return "INSUFFICIENT_ELIGIBLE"
    if book.get("weights"):
        return "OK"
    return "OK-flat-empty"


def main() -> int:
    t0 = datetime.now(timezone.utc)
    basis, basis_report = load_basis_world()
    print(f"[dryrun] basis loaded: {len(basis)} symbols", flush=True)

    # Full-coverage bars, loaded ONCE for all four folds (disclosed: a strict
    # superset of the frozen per-fold window; only on-schedule stamps are
    # consumed; see replication_data.fold_bar_window's note -- 7 of the 19
    # names have no bars at all inside Y2021/Y2022, and an uninjected symbol
    # would silently shrink the frozen 19-name universe).
    bars = load_execution_bars_catalog(FEED_SYMBOLS, catalog=CATALOG)
    bars_summary = {
        sym: {
            "origin_iso": iso_utc(int(series.origin_ns)),
            "end_iso": iso_utc(int(series.end_ns)),
            "slots": int(series.close.shape[0]),
            "finite_closes": int(
                __import__("numpy").isfinite(series.close).sum()
            ),
        }
        for sym, series in sorted(bars.items())
    }
    print(
        f"[dryrun] bars loaded (full coverage): {len(bars)} symbols", flush=True
    )

    folds_out: dict[str, dict] = {}
    non_vacuous = True
    for fold_label, w0, w1 in FOLDS:
        plugin = BasislvWindowFoldPlugin(
            arm_id=DRYRUN_ARM,
            basis_by_symbol=dict(basis),
            bars_by_symbol=dict(bars),
            window_start_iso=w0,
            window_end_iso=w1,
        )
        plugin.bind_window((w0, w1))
        baseline = plugin.baseline_stress()
        universe = plugin.universe(baseline)
        schedule = list(plugin.schedule().instants)
        fold_specs = plugin.folds(stress=baseline, instants=schedule)
        open_instants = schedule[:-1]  # the final instant is the runner's own
        # force-flat edge and is never queried for a book (frozen runner law)

        stamps_out: list[dict] = []
        counts = {"OK": 0, "OK-flat-empty": 0, "INSUFFICIENT_ELIGIBLE": 0, "FORCE_FLAT": 0}
        eligible_observed: list[int] = []
        errors: list[dict] = []
        for stamp in open_instants:
            try:
                book = plugin.targets_at(
                    int(stamp), universe=universe, stress=baseline
                )
            except AdapterError as exc:
                errors.append({"stamp_iso": iso_utc(int(stamp)), "error": str(exc)})
                continue
            status = classify(book)
            counts[status] = counts.get(status, 0) + 1
            diag = dict(book.get("diagnostics") or {})
            n_eligible = diag.get("n_eligible")
            if isinstance(n_eligible, int):
                eligible_observed.append(int(n_eligible))
            stamps_out.append(
                {
                    "stamp_ns": int(stamp),
                    "stamp_iso": iso_utc(int(stamp)),
                    "fold": plugin._fold_label(int(stamp)),
                    "status": status,
                    "reason_code": book.get("reason_code"),
                    "n_weights": len(book.get("weights") or []),
                    "n_eligible": n_eligible,
                    "side_size": diag.get("side_size"),
                    "n_refused": diag.get("n_refused"),
                    "refused_by_reason": diag.get("refused_by_reason"),
                }
            )
        constructible = counts.get("OK", 0)
        if constructible < 1:
            non_vacuous = False
        folds_out[fold_label] = {
            "window": [w0, w1],
            "arm": DRYRUN_ARM,
            "window_folds": [
                {"label": lab, "start": a, "end": b}
                for lab, a, b in plugin._window_folds
            ],
            "folds_census": [
                {
                    "index": int(f.index),
                    "label": str(f.label),
                    "n_instants": len(f.instants),
                    "purge_days": int(f.purge_days),
                    "dropped": bool(f.dropped),
                }
                for f in fold_specs
            ],
            "n_schedule_stamps": len(schedule),
            "first_stamp_iso": iso_utc(int(schedule[0])),
            "last_stamp_iso": iso_utc(int(schedule[-1])),
            "n_open_stamps_traversed": len(open_instants),
            "universe_size": len(universe),
            "status_counts": counts,
            "n_constructible_books": constructible,
            "eligible_min": min(eligible_observed) if eligible_observed else None,
            "eligible_max": max(eligible_observed) if eligible_observed else None,
            "zero_margin_note": (
                f"MIN_ELIGIBLE={MIN_ELIGIBLE}; Y2021 has exactly 12 listed of "
                "the frozen 19 -- zero margin" if fold_label == "Y2021" else None
            ),
            "traversal_errors": errors,
            "stamps": stamps_out,
        }
        print(
            f"[dryrun] {fold_label}: stamps={len(open_instants)} "
            f"OK={counts['OK']} insufficient={counts['INSUFFICIENT_ELIGIBLE']} "
            f"force_flat={counts['FORCE_FLAT']} "
            f"eligible[min/max]={folds_out[fold_label]['eligible_min']}/"
            f"{folds_out[fold_label]['eligible_max']} "
            f"errors={len(errors)}",
            flush=True,
        )

    report = {
        "schema": "basislv_replication.dryrun_report.v1",
        "measured_utc": t0.isoformat(),
        "arm": DRYRUN_ARM,
        "arms_note": (
            "anchor traversed; INV is the element-wise negation of the same "
            "book (frozen control construction) -- eligibility, side geometry "
            "and constructibility identical by construction"
        ),
        "universe": list(UNIVERSE),
        "universe_law": (
            "FROZEN 19 at every window (no listing pre-narrowing); the "
            "engine's own per-stamp eligibility decides"
        ),
        "no_gate": "BASISLV has no gate; nothing gated in this traversal",
        "no_pnl": "sanitized: no returns, no costs, no funding, no scored metric",
        "basis_report": basis_report,
        "bars_full_coverage": bars_summary,
        "bars_policy": (
            "each feed symbol loaded at its FULL catalog coverage once for "
            "all folds (superset of the frozen -7d/+3d window; only "
            "on-schedule stamps consumed; uninjected-symbol universe-shrink "
            "avoided -- see replication_data.fold_bar_window note)"
        ),
        "catalog": str(CATALOG),
        "folds": folds_out,
        "non_vacuous": non_vacuous,
        "non_vacuous_rule": ">= 1 constructible book per fold",
    }
    out_path = HERE / "dryrun_report.json"
    out_path.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n", encoding="utf-8")

    print("=" * 72)
    print(f"DRY-RUN {'PASS' if non_vacuous else 'FAIL (vacuous fold)'} "
          f"-- report: {out_path}")
    for fold_label, _w0, _w1 in FOLDS:
        f = folds_out[fold_label]
        print(
            f"  {fold_label}: OK={f['status_counts']['OK']} "
            f"INSUFFICIENT={f['status_counts']['INSUFFICIENT_ELIGIBLE']} "
            f"FORCE_FLAT={f['status_counts']['FORCE_FLAT']} "
            f"eligible {f['eligible_min']}..{f['eligible_max']}"
        )
    return 0 if non_vacuous and all(
        not f["traversal_errors"] for f in folds_out.values()
    ) else 1


if __name__ == "__main__":
    sys.exit(main())
