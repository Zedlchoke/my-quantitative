#!/usr/bin/env python
"""failres-skeptic — INDEPENDENT re-derivation of the lead event overlay.

Duty 1 of the economic-skeptic lane (ERP1-TRACKA-COHORT-1 / failres).
Own join code, written from the schemas alone; the lead's script was NOT
read. Re-derives: event-day vs no-event-day daily splits, exit-type x
event-day cells, mode-at-entry per fold, TARGET_EXIT gross pool, plus the
adjudication arithmetic for H-FR1/H-FR2/H-FR3 (sched-filter panel delta,
FF/TE hold-time descriptive distributions, monthly FF concentration).

Labels: DIAGNOSTIC_OUTCOME_EXPOSED · SINGLE_SOURCE_PANEL · PAPER_TIER ·
FAILURE_ROOT_CAUSE_RESEARCH · EVENTS_OVERLAY_ONLY_NOT_CAUSAL_EVIDENCE.
R-ORIG-SEMANTICS numbers inside the inputs carry R-ORIG-SEMANTICS.
Light compute only (joins/tables on committed lane JSONs); no strategy
variant is re-run, no parameter is tuned, nothing is promotable.

Python: /Users/hoangminhlong/my-quantitative/.venv/bin/python (absolute).
Run from anywhere; all paths absolute.
"""
import json
import os
import collections

BASE = ("/Users/hoangminhlong/my-quantitative/.worktrees/"
        "erp1-tracka-cohort-1/failres-skeptic/research/control/"
        "ERP1-TRACKA-COHORT-1/failres")

SCHED = {"FOMC_DECISION", "ECB_DECISION", "US_CPI_RELEASE",
         "EZ_HICP_RELEASE", "US_NFP"}
SURPRISE = {"ENERGY_INFRASTRUCTURE", "GEOPOLITICAL"}
FOLDS = ["F1", "F2", "F3", "F4", "F5", "F6"]
LOSING = {"F1", "F2", "F5"}  # EURUSD designated losing folds (dispatch)


def load(name):
    with open(os.path.join(BASE, name)) as f:
        return json.load(f)


def r2(x):
    return round(x + 0.0, 1)


def main():
    daily = load("failres_daily_EURUSD.json")["rows"]
    trades_all = load("failres_attrib_trades_EURUSD.json")["rows"]
    trades = [t for t in trades_all if t["book"] == "R-DAEMON"]
    evs = []
    with open(os.path.join(BASE, "failres_events_timeline.jsonl")) as f:
        for line in f:
            if line.strip():
                e = json.loads(line)
                if e.get("event_id"):
                    evs.append(e)

    out = {"labels": ["DIAGNOSTIC_OUTCOME_EXPOSED", "SINGLE_SOURCE_PANEL",
                      "PAPER_TIER", "FAILURE_ROOT_CAUSE_RESEARCH",
                      "EVENTS_OVERLAY_ONLY_NOT_CAUSAL_EVIDENCE"],
           "n_daemon_trades": len(trades), "n_events": len(evs),
           "n_daily_rows": len(daily)}

    # ---- event-day sets by UTC date of event_time_utc -------------------
    by_date = collections.defaultdict(set)
    for e in evs:
        by_date[e["event_time_utc"][:10]].add(e["event_type"])
    sched_days = {d for d, ts in by_date.items() if ts & SCHED}
    surp_days = {d for d, ts in by_date.items() if ts & SURPRISE}
    overlap = sched_days & surp_days
    out["overlap_days"] = {"n": len(overlap), "dates": sorted(overlap)}

    def day_class(d, precedence="sched_first"):
        if d in sched_days and (precedence == "sched_first" or d not in surp_days):
            return "SCHED"
        if d in surp_days:
            return "SURPRISE"
        if d in sched_days:
            return "SCHED"
        # OTHER-only days are excluded from both categories (lead rule)
        return "NO_EVENT"

    daily_fold = collections.defaultdict(list)
    for r in daily:
        if r.get("fold") in FOLDS:
            daily_fold[r["fold"]].append(r)

    # ---- T1: event-day vs no-event-day daily net split ------------------
    t1 = {}
    for fold in FOLDS:
        rows = daily_fold[fold]
        covered = fold != "F4"  # timeline covers F1/F2/F3/F5/F6, not F4
        cells = collections.defaultdict(lambda: [0.0, 0])
        for r in rows:
            cls = day_class(r["date"]) if covered else "NO_EVENT"
            cells[cls][0] += r["net_daemon"]
            cells[cls][1] += 1
        t1[fold] = {"ALL": [r2(sum(r["net_daemon"] for r in rows)),
                            len(rows)],
                    **{k: [r2(v[0]), v[1]] for k, v in sorted(cells.items())}}
    out["T1_daily_split"] = t1

    # same split with surprise-first precedence (robustness vs lead rule)
    t1b = {}
    for fold in ("F2",):
        rows = daily_fold[fold]
        cells = collections.defaultdict(lambda: [0.0, 0])
        for r in rows:
            cells[day_class(r["date"], "surprise_first")][0] += r["net_daemon"]
            cells[day_class(r["date"], "surprise_first")][1] += 1
        t1b[fold] = {k: [r2(v[0]), v[1]] for k, v in sorted(cells.items())}
    out["T1b_F2_surprise_first"] = t1b

    # lead-rule reconstruction: UNION buckets (a day with both SCHED and
    # SURPRISE events counts in BOTH) and OTHER-only days excluded from
    # every bucket. This is the rule under which the lead's T1 table is
    # exactly reproducible (buckets then do not partition ALL).
    t1u = {}
    for fold in FOLDS:
        rows = daily_fold[fold]
        covered = fold != "F4"
        cells = collections.defaultdict(lambda: [0.0, 0])
        for r in rows:
            if not covered:
                cells["NO_EVENT"][0] += r["net_daemon"]
                cells["NO_EVENT"][1] += 1
                continue
            ts = by_date.get(r["date"], set())
            if ts & SCHED:
                cells["SCHED"][0] += r["net_daemon"]
                cells["SCHED"][1] += 1
            if ts & SURPRISE:
                cells["SURPRISE"][0] += r["net_daemon"]
                cells["SURPRISE"][1] += 1
            if ts and not (ts & SCHED) and not (ts & SURPRISE):
                cells["OTHER_ONLY_EXCLUDED"][0] += r["net_daemon"]
                cells["OTHER_ONLY_EXCLUDED"][1] += 1
            if not ts:
                cells["NO_EVENT"][0] += r["net_daemon"]
                cells["NO_EVENT"][1] += 1
        t1u[fold] = {k: [r2(v[0]), v[1]] for k, v in sorted(cells.items())}
    out["T1u_lead_rule_union"] = t1u

    # ---- T2: exit-type x event-day cells (trades joined by entry day) ---
    t2 = {}
    for fold in FOLDS:
        rows = [t for t in trades if t["fold"] == fold]
        covered = fold != "F4"
        cells = collections.defaultdict(lambda: [0.0, 0])
        for t in rows:
            cls = day_class(t["day"]) if covered else "NO_EVENT"
            key = (cls, t["exit_type"])
            cells[key][0] += t["net_pips"]
            cells[key][1] += 1
        t2[fold] = {f"{c}_{x}": [r2(v[0]), v[1]]
                    for (c, x), v in sorted(cells.items())}
    out["T2_exit_by_event"] = t2

    # ---- T3: mode-at-entry per fold --------------------------------------
    t3 = {}
    for fold in FOLDS:
        rows = [t for t in trades if t["fold"] == fold]
        agg = collections.defaultdict(lambda: [0.0, 0])
        for t in rows:
            agg[t["mode_at_entry"]][0] += t["net_pips"]
            agg[t["mode_at_entry"]][1] += 1
        t3[fold] = {k: [r2(v[0]), v[1]] for k, v in sorted(agg.items())}
    out["T3_mode_at_entry"] = t3

    # ---- T4: TARGET_EXIT gross pool per fold -----------------------------
    t4 = {}
    for fold in FOLDS:
        rows = [t for t in trades
                if t["fold"] == fold and t["exit_type"] == "TARGET_EXIT"]
        ff = [t for t in trades
              if t["fold"] == fold and t["exit_type"] == "FORCE_FLAT"]
        t4[fold] = {
            "TE": [len(rows), r2(sum(t["gross_pips"] for t in rows)),
                   r2(sum(t["cost_pips"] for t in rows))],
            "TE_net": r2(sum(t["net_pips"] for t in rows)),
            "FF": [len(ff), r2(sum(t["gross_pips"] for t in ff)),
                   r2(sum(t["cost_pips"] for t in ff))],
            "FF_net": r2(sum(t["net_pips"] for t in ff))}
    out["T4_exit_gross_pool"] = t4

    # ---- H-FR2 arithmetic: sched stand-down on the family's own book ----
    sched_net = {f: t1[f]["SCHED"][0] if "SCHED" in t1[f] else 0.0
                 for f in FOLDS if f != "F4"}
    saved_losing = sum(-sched_net[f] for f in LOSING)   # losses avoided
    lost_winning = sum(sched_net[f] for f in ("F3", "F6"))  # profits removed
    out["H_FR2_arithmetic"] = {
        "sched_net_by_fold": sched_net,
        "saved_in_losing_folds": r2(saved_losing),
        "winners_removed_F3_F6": r2(lost_winning),
        "panel_delta_of_filter": r2(saved_losing - lost_winning),
        "F2_after_filter": r2(t1["F2"]["ALL"][0] - sched_net["F2"]),
        "F2_sched_FF_per_RT": r2(t2["F2"]["SCHED_FORCE_FLAT"][0]
                                 / t2["F2"]["SCHED_FORCE_FLAT"][1]),
        "F2_noevent_share_of_loss_pct": r2(
            100.0 * (-t1["F2"]["NO_EVENT"][0]) / (-t1["F2"]["ALL"][0])),
    }

    # ---- H-FR1 checks: FOMC completeness + monthly FF concentration -----
    fomc = sorted(e["event_time_utc"][:10] for e in evs
                  if e["event_type"] == "FOMC_DECISION"
                  and "2021-11-01" <= e["event_time_utc"][:10] <= "2022-08-31")
    # actual F2 FOMC decision dates (public record, decision-only calendar)
    actual_f2_fomc = ["2021-11-03", "2021-12-15", "2022-01-26", "2022-03-16",
                      "2022-05-04", "2022-06-15", "2022-07-27"]
    out["H_FR1_FOMC_completeness"] = {
        "f2_fomc_in_timeline": fomc,
        "f2_fomc_missing": sorted(set(actual_f2_fomc) - set(fomc)),
        "decision_sizes_in_machine_fields": False,
        "note": ("decision direction/size lives only in free-text "
                 "expected_vs_actual; a trailing divergence series cannot be "
                 "built from the committed timeline without new assembly")}
    monthly_ff = collections.defaultdict(lambda: [0.0, 0.0, 0])
    monthly_net = collections.defaultdict(float)
    for t in trades:
        if t["fold"] == "F2":
            m = t["day"][:7]
            monthly_ff[m][0] += (t["net_pips"] if t["exit_type"] == "FORCE_FLAT"
                                 else 0.0)
            monthly_ff[m][2] += 1
            monthly_net[m] += t["net_pips"]
    out["H_FR1_F2_monthly"] = {m: {"FF_net": r2(v[0]), "day_net": r2(monthly_net[m]),
                                   "RT": v[2]}
                               for m, v in sorted(monthly_ff.items())}

    # ---- H-FR3 descriptives: FF vs TE hold-time distributions -----------
    def pct(vals, q):
        s = sorted(vals)
        if not s:
            return None
        i = min(len(s) - 1, max(0, int(round(q * (len(s) - 1)))))
        return s[i]

    holds = {}
    for fold in FOLDS:
        row = {}
        for xt in ("FORCE_FLAT", "TARGET_EXIT"):
            vals = [t["hold_bars"] for t in trades
                    if t["fold"] == fold and t["exit_type"] == xt]
            row[xt] = {"n": len(vals), "p25": pct(vals, .25),
                       "p50": pct(vals, .5), "p75": pct(vals, .75),
                       "max": max(vals) if vals else None}
        holds[fold] = row
    out["H_FR3_hold_bars_by_exit"] = holds
    ff_share = r2(100.0 * len([t for t in trades if t["exit_type"] == "FORCE_FLAT"])
                  / len(trades))
    out["FF_share_of_RT_pct"] = ff_share

    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
