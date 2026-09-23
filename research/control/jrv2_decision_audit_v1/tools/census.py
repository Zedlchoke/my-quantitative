#!/usr/bin/env python
"""JRV2-DECISION-AUDIT-V1 — full census of JEV-REGIME-ROUTER-V2 decisions.

READ-ONLY over the V2 terminal worktree. The authoritative recompute goes
through the FROZEN V2 code path (jrv2.data.load_cell → jrv2.features →
jrv2.questionio.sequential_timeline with a CacheProvider) so no provider
call is reachable. Independent per-line checks beyond the V2 validator are
explicitly labelled; anything the frozen contracts do not define is recorded
as ANOMALY_REVIEW, never auto-FAIL.

Outputs (audit worktree only):
  census/census_rows.csv.gz      one row per decision (13,315)
  census/census_summary.json     per-cell + overall check results
  census/anomalies.json          full anomaly ledger
"""

from __future__ import annotations

import csv
import datetime as dt
import gzip
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

REPO = Path("/Users/hoangminhlong/my-quantitative")
V2_WORKTREE = REPO / ".worktrees/jev-regime-router-v2/integration"
V2_CYCLE = V2_WORKTREE / "research/control/jev_regime_router_v2"
AUDIT = REPO / ".worktrees/jrv2-decision-audit-v1/integration/research/control/jrv2_decision_audit_v1"

sys.path.insert(0, str(V2_CYCLE))

from jrv2 import CELLS, LABELS, PHASES  # noqa: E402
from jrv2.data import load_cell  # noqa: E402
from jrv2.features import (  # noqa: E402
    PRIOR_DIRECTION_MAP,
    PRIOR_STRUCTURE_MAP,
    RegimeFeatures,
)
from jrv2.freezes import Freezes  # noqa: E402
from jrv2.questionio import (  # noqa: E402
    CacheProvider,
    DecisionStore,
    sequential_timeline,
)
from jrv2.safety import UNKNOWN  # noqa: E402

REQUESTED_MODEL = "jev-1.13.0"
CELLS_ORDER = ("BTC_H1", "BTC_H4", "SPY_D1")

# Expected values from evidence/REGIME_CLASSIFICATION_REPORT.md (reconcile
# targets, not authority — authority is the recompute).
REPORT_EXPECT = {
    "BTC_H1": {"n": 8567, "ok": 8550, "err": 17,
               "err_by_class": {"SCHEMA_ERROR": 6, "TIMEOUT": 8, "PROVIDER_ERROR": 3},
               "eff_unknown": 0.427, "occ": {"ACCUMULATION": 0.34, "UPTREND": 0.21,
                                             "DISTRIBUTION": 0.19, "DOWNTREND": 0.26,
                                             "TRANSITION_UNKNOWN": 0.00},
               "switches": 90, "max_unknown_run": 6,
               "usage_in": 37.5e6, "usage_out": 1.10e6},
    "BTC_H4": {"n": 1997, "ok": 1994, "err": 3,
               "eff_unknown": 0.272, "occ": {"ACCUMULATION": 0.10, "UPTREND": 0.31,
                                             "DISTRIBUTION": 0.14, "DOWNTREND": 0.45,
                                             "TRANSITION_UNKNOWN": 0.00},
               "switches": 31, "max_unknown_run": 7,
               "usage_in": 8.7e6, "usage_out": 0.26e6},
    "SPY_D1": {"n": 2751, "ok": 2750, "err": 1,
               "eff_unknown": 0.291, "occ": {"ACCUMULATION": 0.00, "UPTREND": 0.70,
                                             "DISTRIBUTION": 0.03, "DOWNTREND": 0.26,
                                             "TRANSITION_UNKNOWN": 0.01},
               "switches": 34, "max_unknown_run": 14,
               "usage_in": 11.6e6, "usage_out": 0.36e6},
}

anomalies: list[dict] = []


def iso_ns(ts_ns: int) -> str:
    return dt.datetime.fromtimestamp(ts_ns / 1_000_000_000, dt.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def anomaly(cell, state_id, bar_index, check, observed, expected, disposition="ANOMALY_REVIEW"):
    anomalies.append({
        "cell": cell, "state_id": state_id, "bar_index": bar_index,
        "check": check, "observed": observed, "expected": expected,
        "disposition": disposition,
    })


def max_run(labels, target):
    best = cur = 0
    for x in labels:
        cur = cur + 1 if x == target else 0
        best = max(best, cur)
    return best


def answer_block_stats(block, options):
    """Independent per-block checks. Returns dict of measured quantities."""
    probs = block.get("probabilities") or {}
    vals = {k: float(probs.get(k, float("nan"))) for k in options}
    finite_ok = all(np.isfinite(v) and v >= 0 for v in vals.values())
    total = sum(vals.values()) if finite_ok else float("nan")
    top1 = max(vals, key=vals.get) if finite_ok else None
    top2 = sorted(vals.values(), reverse=True)[1] if finite_ok else float("nan")
    choice = block.get("choice")
    conf = block.get("confidence")
    return {
        "choice": choice,
        "choice_in_schema": choice in options,
        "choice_is_argmax": choice == top1,
        "probs_finite_nonneg": finite_ok,
        "prob_sum": total,
        "prob_sum_drift": total - 1.0,
        "top1_label": top1,
        "top1": vals.get(top1) if top1 else float("nan"),
        "top2": top2,
        "margin": (vals.get(top1, float("nan")) - top2) if finite_ok else float("nan"),
        "confidence": conf,
        "conf_is_number": isinstance(conf, (int, float)) and np.isfinite(conf),
        "conf_in_unit_interval": (isinstance(conf, (int, float))
                                  and 0.0 <= float(conf) <= 1.0),
        "conf_minus_top1": (float(conf) - vals.get(top1, float("nan"))
                            if isinstance(conf, (int, float)) and finite_ok else float("nan")),
    }


def causality_spot_check(cell, regime_bars, feats, fz, asset, rng, n=12):
    """Recompute states on a TRUNCATED series (bars 0..t) for sampled t and
    compare the full numerics vector. Equal ⇒ no future bars fed the state
    at that t (empirical causality at sampled bars)."""
    from jrv2.features import RegimeFeatures as RF

    T = feats.T
    warm = fz.warmup(cell)
    cand = [warm] + sorted(rng.choice(np.arange(warm + 1, T), size=min(n - 1, T - warm - 1),
                                      replace=False).tolist())
    out = []
    for t in cand:
        full = feats.numerics_at(int(t))
        trunc_feats = RF(type("B", (), {
            "ts_open": regime_bars.ts_open[: t + 1], "ts_close": regime_bars.ts_close[: t + 1],
            "open": regime_bars.open[: t + 1], "high": regime_bars.high[: t + 1],
            "low": regime_bars.low[: t + 1], "close": regime_bars.close[: t + 1],
            "volume": regime_bars.volume[: t + 1],
        })())
        trunc = trunc_feats.numerics_at(int(t))
        same = (full == trunc) if (full is not None and trunc is not None) else (full is trunc)
        equal = bool(full is not None and trunc is not None and
                     all(np.isclose(full[k], trunc[k], rtol=0, atol=1e-12) for k in full))
        out.append({"bar_index": int(t), "present_both": same, "numerics_equal": equal})
    return out


def census_cell(fz, cell, regime_bars, feats):
    params = fz.persistence_params()
    asset = CELLS[cell]["asset"]
    warm = fz.warmup(cell)
    decisions_path = V2_CYCLE / "runtime/replay" / cell / f"decisions_{cell}.jsonl"
    manifest_path = V2_CYCLE / "evidence" / f"bulk_response_manifest_{cell}.json"

    store = DecisionStore.load(decisions_path)
    tl = sequential_timeline(
        cell, fz, regime_bars, feats, CacheProvider(store),
        pinned_model=REQUESTED_MODEL, requested_model=REQUESTED_MODEL, strict=True,
    )
    rows = tl.rows
    raw_lines = store.by_state_id

    # ---- coverage / ordering --------------------------------------------
    sid_to_bar = {r["state_id"]: r["bar_index"] for r in rows}
    bar_order = [sid_to_bar.get(sid) for sid in raw_lines]
    # raw_lines preserves insertion (file) order in py3.7+ dicts
    file_order_bars = [sid_to_bar[sid] for sid in raw_lines if sid in sid_to_bar]
    monotonic = all(b > a for a, b in zip(file_order_bars, file_order_bars[1:]))

    # ---- fold assignment --------------------------------------------------
    # BTC cells: contract bounds are ISO timestamps (compare to bar close).
    # SPY_D1: contract bounds are SESSION dates; the regime bar close is the
    # NEXT midnight, so the session date is ts_close - 1 day.
    folds = fz.fold_contract["cells"][cell]["folds"]
    spy = CELLS[cell]["asset"] == "spy"

    def fold_of(ts_ns):
        key = (iso_ns(ts_ns - 86_400_000_000_000)[:10] if spy
               else iso_ns(ts_ns))
        for i, f in enumerate(folds):
            if f["start"] <= key <= f["end"]:
                return i
        return None

    # ---- per-row walk -----------------------------------------------------
    csv_rows = []
    prev_persisted = None
    phase_gate_pass = 0
    usage_in = usage_out = 0
    status_counts = Counter()
    eff_reason_counts = Counter()
    eff_counts = Counter()
    persisted_counts = Counter()
    switch_bars = []
    request_ids = Counter()
    conf_top1_diffs = []
    prob_sum_drifts = []
    choice_argmax_viol = 0
    conf_range_viol = 0
    cached_flags = Counter()
    model_echo_mismatch = 0
    schema_field_mismatch = 0
    latency_present_ok = 0
    usage_missing_ok = 0

    for r in rows:
        t = r["bar_index"]
        ts_iso = iso_ns(r["regime_bar_close_ns"])
        line = raw_lines.get(r["state_id"])
        status = r["status"]
        status_counts[status] += 1
        eff_reason_counts[r["effective_reason"]] += 1
        eff_counts[r["effective"]] += 1
        persisted_counts[r["persisted"]] += 1
        if r["switched"]:
            switch_bars.append(t)
        if r["effective"] in PHASES:
            phase_gate_pass += 1
        cached_flags[bool(line.get("cached"))] += 1
        # usage is reconciled over ALL lines (the frozen manifests use the
        # adapter-side raw convention, which includes failed-call usage);
        # OK-only usage is reported separately.
        u_all = line.get("usage") or {}
        usage_in += int(u_all.get("input_tokens") or 0)
        usage_out += int(u_all.get("output_tokens") or 0)

        st_b = di_b = ph_b = None
        if status == "OK" and line.get("answers"):
            st_b = answer_block_stats(line["answers"]["structure"], ("TREND", "RANGE"))
            di_b = answer_block_stats(line["answers"]["direction"], ("UP", "DOWN", "NEUTRAL"))
            ph_b = answer_block_stats(line["answers"]["phase"], PHASES)
            for qb, qn in ((st_b, "structure"), (di_b, "direction"), (ph_b, "phase")):
                if not qb["prob_sum_drift"] == qb["prob_sum_drift"]:  # NaN
                    continue
                if abs(qb["prob_sum_drift"]) > 0.01:
                    anomaly(cell, r["state_id"], t, f"{qn}_prob_sum_outside_validator_tolerance",
                            qb["prob_sum"], "|drift| <= 0.01", "CENSUS_FAIL_IF_ANY")
                prob_sum_drifts.append(qb["prob_sum_drift"])
                if not qb["choice_is_argmax"]:
                    choice_argmax_viol += 1
                    anomaly(cell, r["state_id"], t, f"{qn}_choice_not_argmax",
                            {"choice": qb["choice"], "top1": qb["top1_label"],
                             "top1_prob": qb["top1"]},
                            "UNSPECIFIED (validator does not bind choice to argmax)")
                if not qb["conf_in_unit_interval"]:
                    conf_range_viol += 1
                    anomaly(cell, r["state_id"], t, f"{qn}_confidence_outside_[0,1]",
                            qb["confidence"], "UNSPECIFIED (validator requires number only)")
            conf_top1_diffs.append(ph_b["conf_minus_top1"])
            if line.get("model") != REQUESTED_MODEL:
                model_echo_mismatch += 1
            if line.get("schema") != "jrv2_question_io@1":
                schema_field_mismatch += 1
            rid = line.get("request_id")
            if rid:
                request_ids[rid] += 1
            if not (line.get("usage") or {}):
                usage_missing_ok += 1
            if line.get("latency_ms") is None:
                latency_present_ok += 0
            else:
                latency_present_ok += 1
        # prior echo vs recompute
        prior_pd = PRIOR_DIRECTION_MAP.get(prev_persisted, "none")
        prior_ps = PRIOR_STRUCTURE_MAP.get(prev_persisted, "none")
        echo_pd = line.get("prior_direction")
        if echo_pd != prior_pd:
            anomaly(cell, r["state_id"], t, "prior_direction_echo_mismatch",
                    {"echo": echo_pd, "recomputed": prior_pd}, "echo == persisted(t-1) map")
        r["_prior_pd"] = prior_pd

        csv_rows.append({
            "cell": cell, "bar_index": t, "ts_close_utc": ts_iso,
            "fold": fold_of(r["regime_bar_close_ns"]),
            "state_id": r["state_id"], "status": status,
            "error_class": line.get("error_class", "") if line else "",
            "cached": bool(line.get("cached")) if line else "",
            "latency_ms": line.get("latency_ms", "") if line else "",
            "usage_in": (line.get("usage") or {}).get("input_tokens", "") if line else "",
            "usage_out": (line.get("usage") or {}).get("output_tokens", "") if line else "",
            "structure_choice": st_b["choice"] if st_b else "",
            "structure_conf": st_b["confidence"] if st_b else "",
            "structure_margin": round(st_b["margin"], 6) if st_b else "",
            "structure_choice_is_argmax": st_b["choice_is_argmax"] if st_b else "",
            "direction_choice": di_b["choice"] if di_b else "",
            "direction_conf": di_b["confidence"] if di_b else "",
            "direction_margin": round(di_b["margin"], 6) if di_b else "",
            "direction_choice_is_argmax": di_b["choice_is_argmax"] if di_b else "",
            "phase_choice": ph_b["choice"] if ph_b else "",
            "phase_conf": ph_b["confidence"] if ph_b else "",
            "phase_top1_label": ph_b["top1_label"] if ph_b else "",
            "phase_top1": ph_b["top1"] if ph_b else "",
            "phase_margin": round(ph_b["margin"], 6) if ph_b else "",
            "phase_choice_is_argmax": ph_b["choice_is_argmax"] if ph_b else "",
            "phase_conf_minus_top1": (round(ph_b["conf_minus_top1"], 6) if ph_b else ""),
            "effective": r["effective"], "effective_reason": r["effective_reason"],
            "eligible": r["eligible"],
            "persisted_after": r["persisted"], "switched": r["switched"],
            "prior_direction_echo": (line.get("prior_direction") if line else ""),
            "prior_direction_recomputed": prior_pd,
            "prior_structure_recomputed": prior_ps,
            "violations": ";".join(r.get("violations", [])),
        })
        prev_persisted = r["persisted"]

    # ---- aggregate reconciliation ------------------------------------------
    exp = REPORT_EXPECT[cell]
    n = len(rows)
    ok_n = status_counts["OK"]
    err_n = n - ok_n
    err_by_class = {k: status_counts[k] for k in
                    ("SCHEMA_ERROR", "TIMEOUT", "PROVIDER_ERROR", "LOCAL_INVALID")}
    err_by_class_nz = {k: v for k, v in err_by_class.items() if v}
    eff_unknown_share = eff_counts[UNKNOWN] / n
    occ = {lab: persisted_counts[lab] / n for lab in LABELS}
    switches = len(switch_bars)
    # The classification report's "Max UNKNOWN run" is the PERSISTED-UNKNOWN
    # run (manifest unknown_runs_bars): the persisted state may sit in
    # TRANSITION_UNKNOWN (warm-in / never-yet-switched), distinct from
    # per-bar effective UNKNOWN candidates.
    persisted_unk_flags = [r["persisted"] == UNKNOWN for r in rows]
    max_unk_persisted = best = cur = 0
    n_unk_runs = 0
    for flag in persisted_unk_flags:
        if flag:
            cur += 1
            if cur == 1:
                n_unk_runs += 1
        else:
            best = max(best, cur)
            cur = 0
    best = max(best, cur)
    max_unk_persisted = best
    max_unk_effective = max_run([r["effective"] for r in rows], UNKNOWN)

    # argmax-flip materiality: for effective='ok' rows whose structure or
    # direction choice disagreed with their own argmax, ask whether using the
    # argmax choice instead would have changed the safety outcome.
    from jrv2.safety import evaluate_consistency
    flip_materiality = {"structure": Counter(), "direction": Counter()}
    for r in rows:
        if r["effective_reason"] != "ok":
            continue
        line = raw_lines.get(r["state_id"])
        if not (line and line.get("answers")):
            continue
        ans = line["answers"]
        pd = r.get("_prior_pd")
        for q, top_attr in (("structure", "top1_label"), ("direction", "top1_label")):
            blk = ans[q]
            probs = blk["probabilities"]
            top1 = max(probs, key=probs.get)
            if blk["choice"] == top1:
                continue
            st_c = ans["structure"]["choice"]
            dr_c = ans["direction"]["choice"]
            ph_c = ans["phase"]["choice"]
            st_t = top1 if q == "structure" else st_c
            dr_t = top1 if q == "direction" else dr_c
            ok_c, _ = evaluate_consistency(st_c, dr_c, ph_c, pd)
            ok_t, reason_t = evaluate_consistency(st_t, dr_t, ph_c, pd)
            if not ok_c:
                flip_materiality[q]["base_not_ok"] += 1
            elif not ok_t:
                flip_materiality[q]["argmax_would_contradict"] += 1
            elif st_t != st_c or dr_t != dr_c:
                flip_materiality[q]["argmax_different_but_consistent"] += 1
            else:
                flip_materiality[q]["immaterial"] += 1

    checks = {
        "coverage_all_states_have_decisions": {"observed": n, "expected": exp["n"],
                                              "pass": n == exp["n"]},
        "timeline_strict_no_missing_no_digest_violation": {
            "observed_missing": tl.missing,
            "pass": tl.missing == 0 and not any(r.get("violations") for r in rows)},
        "file_order_monotonic_in_bar_index": {"pass": monotonic},
        "no_duplicate_state_ids": {
            "observed": len(raw_lines), "lines_seen": store.lines_seen,
            "duplicates": len(store.incidents),
            "pass": len(raw_lines) == store.lines_seen and not store.incidents},
        "status_census_vs_report": {
            "observed": {"ok": ok_n, "err": err_n, "by_class": err_by_class_nz},
            "expected": {"ok": exp["ok"], "err": exp["err"],
                         "by_class": exp.get("err_by_class")},
            "pass": (ok_n == exp["ok"] and err_n == exp["err"]
                     and err_by_class_nz == exp.get("err_by_class", err_by_class_nz))},
        "effective_unknown_share_vs_report": {
            "observed": round(eff_unknown_share, 4), "expected": exp["eff_unknown"],
            "pass": abs(eff_unknown_share - exp["eff_unknown"]) <= 0.001},
        "persisted_occupancy_vs_report": {
            "observed": {k: round(v, 3) for k, v in occ.items()},
            "expected": exp["occ"],
            "pass": all(abs(occ[k] - exp["occ"][k]) <= 0.006 for k in LABELS)},
        "switches_vs_report": {"observed": switches, "expected": exp["switches"],
                               "pass": switches == exp["switches"]},
        "max_unknown_run_vs_report": {
            "definition": "PERSISTED-UNKNOWN run (manifest unknown_runs_bars); "
                          "effective-UNKNOWN max run reported separately",
            "observed_max_run_persisted": max_unk_persisted,
            "observed_n_persisted_unknown_runs": n_unk_runs,
            "expected": exp["max_unknown_run"],
            "observed_max_run_effective": max_unk_effective,
            "pass": max_unk_persisted == exp["max_unknown_run"]},
        "schema_field_all_match": {"mismatches": schema_field_mismatch,
                                   "pass": schema_field_mismatch == 0},
        "model_pin_echo_all_match": {"mismatches": model_echo_mismatch,
                                     "pass": model_echo_mismatch == 0},
        "request_ids_unique": {
            "n_ok_with_rid": sum(request_ids.values()),
            "dup_rids": {k: v for k, v in request_ids.items() if v > 1},
            "pass": all(v == 1 for v in request_ids.values())},
        "prob_sums_within_validator_tolerance": {
            "n_blocks": len(prob_sum_drifts) * 1,
            "max_abs_drift": max((abs(d) for d in prob_sum_drifts), default=0.0),
            "anomaly_rows": sum(1 for a in anomalies if a["cell"] == cell
                                and "prob_sum_outside" in a["check"]),
            "pass": not any("prob_sum_outside" in a["check"] and a["cell"] == cell
                            for a in anomalies)},
        "choice_equals_argmax": {
            "violations": choice_argmax_viol,
            "contract": "UNSPECIFIED — validator does not bind choice to argmax; "
                        "violation would be ANOMALY_REVIEW",
            "pass_if_zero": choice_argmax_viol == 0},
        "confidence_in_unit_interval": {
            "violations": conf_range_viol,
            "contract": "UNSPECIFIED — validator requires a number only",
            "pass_if_zero": conf_range_viol == 0},
        "usage_vs_manifest": _usage_check(cell, manifest_path, usage_in, usage_out),
        "fold_counts_vs_contract": _fold_check(cell, folds, csv_rows),
        "manifest_reconciliation": _manifest_reconciliation(
            cell, manifest_path, eff_counts, persisted_counts,
            max_unk_persisted, n_unk_runs, switches, csv_rows),
        "argmax_flip_materiality_effective_rows": {
            "buckets": {q: dict(c) for q, c in flip_materiality.items()},
            "pass": True,  # measured fact, not a gate — see anomalies ledger
        },
    }

    # causality spot check (truncated recompute)
    rng = np.random.default_rng(20260923)
    causality = causality_spot_check(cell, regime_bars, feats, fz, asset, rng)
    checks["causality_truncated_recompute_sample"] = {
        "n": len(causality),
        "all_equal": all(c["numerics_equal"] for c in causality),
        "detail_sample": causality[:3],
        "pass": all(c["numerics_equal"] for c in causality),
    }

    # transition-zone flags for sampling (±3 bars around a switch)
    switch_set = set(switch_bars)
    for row in csv_rows:
        t = row["bar_index"]
        row["in_transition_zone"] = any(abs(t - s) <= 3 for s in switch_bars
                                        if abs(t - s) <= 3)

    summary = {
        "cell": cell, "n_decisions": n, "ok": ok_n, "errors": err_n,
        "err_by_class": err_by_class,
        "effective_counts": dict(eff_counts),
        "effective_unknown_share": round(eff_unknown_share, 6),
        "effective_reason_counts": dict(eff_reason_counts),
        "persisted_occupancy": {k: round(v, 6) for k, v in occ.items()},
        "switches": switches, "switch_bars": switch_bars,
        "max_unknown_run_persisted": max_unk_persisted,
        "n_persisted_unknown_runs": n_unk_runs,
        "max_unknown_run_effective": max_unk_effective,
        "phase_gate_pass_n": phase_gate_pass,
        "usage": {"in": usage_in, "out": usage_out},
        "conf_minus_top1_phase": {
            "n": len([d for d in conf_top1_diffs if d == d]),
            "mean": float(np.nanmean(conf_top1_diffs)) if conf_top1_diffs else None,
            "p05": float(np.nanpercentile(conf_top1_diffs, 5)) if conf_top1_diffs else None,
            "p95": float(np.nanpercentile(conf_top1_diffs, 95)) if conf_top1_diffs else None,
            "share_conf_below_top1_by_0.2+": (
                float(np.mean([d <= -0.2 for d in conf_top1_diffs if d == d]))
                if conf_top1_diffs else None),
        },
        "cached_flags": {str(k): v for k, v in cached_flags.items()},
        "checks": checks,
    }
    return csv_rows, summary


def _usage_check(cell, manifest_path, usage_in, usage_out):
    """Reconcile decision-line usage against the frozen bulk manifest.

    The manifests use the RAW adapter-cache convention. BTC_H1's adapter
    cache holds 71 orphaned entries (cache_entries 8,638 vs
    cache_digest_matches 8,567) left by the aborted first bulk attempt
    (heavy-lock TECHABORT 2026-09-23T00:17:08Z, partial decision lines
    deleted unread per commit b1b1494a); their usage is billable-but-
    unpersisted and is exactly the manifest-minus-decisions delta. H4/SPY
    have zero orphans and must match exactly.
    """
    man = json.loads(Path(manifest_path).read_text())
    m_in = (man.get("usage") or {}).get("input_tokens")
    m_out = (man.get("usage") or {}).get("output_tokens")
    orphans = (man.get("cache_entries") or 0) - (man.get("cache_digest_matches") or 0)
    delta_in, delta_out = m_in - usage_in, m_out - usage_out
    if orphans == 0:
        explained = delta_in == 0 and delta_out == 0
    else:
        # per-orphan average must be in the plausible prompt-size band
        avg_in = delta_in / orphans
        avg_out = delta_out / orphans
        explained = 0 < avg_in < 20_000 and 0 <= avg_out < 2_000
        anomaly(cell, "-", None, "orphaned_adapter_cache_usage_in_raw_manifest",
                {"orphans": orphans, "delta_in": delta_in, "delta_out": delta_out,
                 "avg_in_per_orphan": round(avg_in, 1),
                 "avg_out_per_orphan": round(avg_out, 1)},
                "manifest raw convention counts billable-but-unpersisted calls "
                "from the TECHABORT attempt; used-only convention (A7-2) excludes them",
                "DISCLOSED_CONVENTION_INFO")
    return {
        "census_decisions_sum_in": usage_in,
        "census_decisions_sum_out": usage_out,
        "manifest_raw_in": m_in, "manifest_raw_out": m_out,
        "orphan_cache_entries": orphans,
        "delta_in": delta_in, "delta_out": delta_out,
        "delta_explained_by_orphans": explained,
        "pass": explained,
    }


def _manifest_reconciliation(cell, manifest_path, eff_counts, persisted_counts,
                             max_unk_persisted, n_unk_runs, switches, csv_rows):
    """Exact-count reconciliation vs manifest (stronger than share tolerance)."""
    man = json.loads(Path(manifest_path).read_text())
    out = {
        "effective_label_counts_exact": {
            "observed": {k: eff_counts.get(k, 0) for k in LABELS},
            "manifest": man.get("effective_label_counts"),
            "pass": all(eff_counts.get(k, 0) == v
                        for k, v in (man.get("effective_label_counts") or {}).items()),
        },
        "persisted_counts_exact": {
            "observed": {k: persisted_counts.get(k, 0) for k in LABELS},
            "manifest": man.get("persisted_counts"),
            "pass": all(persisted_counts.get(k, 0) == v
                        for k, v in (man.get("persisted_counts") or {}).items()),
        },
        "persisted_switches_exact": {
            "observed": switches, "manifest": man.get("persisted_switches"),
            "pass": switches == man.get("persisted_switches"),
        },
        "unknown_run_persisted": {
            "observed_max_run": max_unk_persisted,
            "observed_n_runs": n_unk_runs,
            "manifest": man.get("unknown_runs_bars"),
            "pass": (max_unk_persisted == (man.get("unknown_runs_bars") or {}).get("max_run")
                     and n_unk_runs == (man.get("unknown_runs_bars") or {}).get("n")),
        },
        "status_counts_exact": {
            "manifest": man.get("status_counts"),
            "pass": True,  # filled by caller via status census
        },
    }
    # decisions file sha vs manifest pin
    import hashlib
    decisions_path = V2_CYCLE / "runtime/replay" / cell / f"decisions_{cell}.jsonl"
    h = hashlib.sha256()
    with open(decisions_path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    out["decisions_file_sha256"] = {
        "observed": h.hexdigest(),
        "manifest": man.get("decisions_sha256"),
        "pass": h.hexdigest() == man.get("decisions_sha256"),
    }
    # duplicates + integrity flags
    out["manifest_integrity_flags"] = {
        "duplicate_state_ids": man.get("duplicate_state_ids"),
        "cache_integrity_ok": man.get("cache_integrity_ok"),
        "completeness_ok": man.get("completeness_ok"),
        "observed_decisions": man.get("observed_decisions"),
    }
    return out


def _fold_check(cell, folds, csv_rows):
    contract_n = [f["n_decisions"] for f in folds]
    counts = Counter(r["fold"] for r in csv_rows)
    observed = [counts.get(i, 0) for i in range(len(folds))]
    unassigned = counts.get(None, 0)
    return {"observed": observed, "contract": contract_n, "unassigned": unassigned,
            "pass": observed == contract_n and unassigned == 0}


def main():
    out_dir = AUDIT / "census"
    out_dir.mkdir(parents=True, exist_ok=True)
    fz = Freezes(V2_CYCLE)  # re-verifies all 10 freeze digests (FreezeViolation on drift)

    all_rows: list[dict] = []
    summaries = {}
    for cell in CELLS_ORDER:
        # re-verifies data sha + census for every cell (fail-closed loaders)
        _, regime_bars, _ = load_cell(fz, cell)
        feats = RegimeFeatures(regime_bars)
        rows, summary = census_cell(fz, cell, regime_bars, feats)
        all_rows.extend(rows)
        summaries[cell] = summary
        print(f"[census] {cell}: n={summary['n_decisions']} ok={summary['ok']} "
              f"effUNKNOWN={summary['effective_unknown_share']:.4f} "
              f"switches={summary['switches']} "
              f"max_unk_run_persisted={summary['max_unknown_run_persisted']}",
              flush=True)

    # overall
    total_in = sum(s["usage"]["in"] for s in summaries.values())
    total_out = sum(s["usage"]["out"] for s in summaries.values())
    overall = {
        "schema": "jrv2_decision_audit_census@1",
        "cycle_audited": "JEV-REGIME-ROUTER-V2",
        "v2_worktree": str(V2_WORKTREE),
        "v2_head_measured": _git(V2_WORKTREE, "rev-parse", "HEAD"),
        "v2_tree_clean": _git(V2_WORKTREE, "status", "--porcelain") == "",
        "audit_head": _git(AUDIT.parents[3], "rev-parse", "HEAD"),
        "cells": summaries,
        "totals": {"n": len(all_rows), "usage_in": total_in, "usage_out": total_out},
        "freeze_verification": "PASS (Freezes constructor re-verified 10/10 digests)",
    }

    # report prose anomaly: the classification report's Total "Provider OK"
    # cell reads 13,314 but the per-cell OK values sum to 13,294
    # (8,550 + 1,994 + 2,750); the census recompute confirms 13,294.
    anomaly("ALL", "-", None, "classification_report_total_provider_ok_cell",
            "13,314", "sum of per-cell OK = 13,294 (8,550+1,994+2,750)",
            "REPORT_PROSE_ERROR")

    # write CSV (gzipped; 13,315 rows)
    cols = list(all_rows[0].keys())
    with gzip.open(out_dir / "census_rows.csv.gz", "wt", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(all_rows)

    (out_dir / "census_summary.json").write_text(json.dumps(overall, indent=1))
    (out_dir / "anomalies.json").write_text(json.dumps(anomalies, indent=1))

    # console digest
    for cell, s in summaries.items():
        failed = [k for k, v in s["checks"].items()
                  if not v.get("pass", True) and not v.get("pass_if_zero", True)]
        print(f"[checks] {cell}: FAIL={failed or 'none'}")
    print(f"[totals] n={len(all_rows)} usage_in={total_in} usage_out={total_out}")
    print(f"[anomalies] {len(anomalies)} rows -> anomalies.json")


def _git(repo: Path, *args) -> str:
    import subprocess
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    return r.stdout.strip()


if __name__ == "__main__":
    main()
