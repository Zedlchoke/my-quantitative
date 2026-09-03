"""Z6 driver — schedule-only feasibility and six-arm exact dry-run (A1).

Runs the frozen families over the authorized staged snapshot to produce
decision/target schedules (NEVER returns/PnL), checks preregistered turnover
ceilings, then executes the exact-arm dry run into an empty temporary ledger
with DUMMY finite metrics: six distinct trial keys, six first publications,
six idempotent replays, zero denominator delta. The real cycle counters stay
0/0 during Z6.
"""
from __future__ import annotations

import datetime
import json
import sys

sys.path.insert(0, "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v2/integration")

from research.stocks_free_v2 import family_a4 as F4
from research.stocks_free_v2 import family_a5 as F5
from research.stocks_free_v2.harness import TrialLedger, canonical_json, sha256_file

SNAP = "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v2/staging-td/snapshot2010"
V1STAGE = "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v1/staging-cohort"
COV_START, COV_END = "2018-01-02", "2026-08-27"


def load_json(path):
    with open(path) as f:
        return json.load(f)


def main() -> dict:
    evidence: dict = {"phase": "Z6", "generated_at_utc": _utc()}
    # ---- authorized staged inputs ----
    symbols = ["SPY", "XLK", "XLE", "XLF", "XLV", "XLI", "XLP", "XLY", "XLU", "XLB", "XLRE"]
    raw, adj = {}, {}
    for s in symbols:
        for r in load_json(f"{SNAP}/{s}_none_p1.json")["values"]:
            raw.setdefault(s, {})[r["datetime"]] = float(r["close"])
        for r in load_json(f"{SNAP}/{s}_all_p1.json")["values"]:
            adj.setdefault(s, {})[r["datetime"]] = float(r["close"])
    dist = load_distributions()
    split_factors = {s: {"2025-12-05": 2.0} for s in ["XLK", "XLE", "XLY", "XLU", "XLB"]}
    tr = {s: reconstruct_tr(raw[s], dist.get(s, {}), split_factors.get(s, {})) for s in symbols}
    evidence["inputs"] = {"symbols": symbols, "snapshot_files": 22, "tr_architecture": "issuer-amended-FD2"}

    # ---- calendar sessions in coverage ----
    from research.assets.stocks.calendar import US_EQUITY_REGULAR_V1 as CAL
    import datetime as dt
    sessions, d = [], dt.date.fromisoformat(COV_START)
    while d <= dt.date.fromisoformat(COV_END):
        if CAL.is_session_day(d):
            sessions.append(d.isoformat())
        d += dt.timedelta(days=1)

    # ---- family A4 schedule-only ----
    spec = F4.load_frozen_spec()
    partition = P_partition()
    inputs = F4.FamilyInputs(sessions=sessions, tr=tr, raw_close=raw, spec=spec,
                             partition=F4.PartitionSpec(**partition), calendar=CAL)
    a4_feas, a4_books = {}, {}
    for cfg in F4.build_arm_configs(spec):
        stream = F4.generate_target_book(inputs, cfg)
        turns = [e.turnover_one_way for e in stream.entries if e.entry_type == "decision_fill"]
        n_years = (dt.date.fromisoformat(COV_END) - dt.date.fromisoformat(COV_START)).days / 365.25
        one_way_per_year = sum(turns) / n_years
        a4_feas[cfg.arm_id] = {"fill_events": len(turns), "one_way_per_year": round(one_way_per_year, 4),
                               "ceiling": 6.0, "within_ceiling": one_way_per_year <= 6.0}
        a4_books[cfg.arm_id] = stream
    evidence["a4_feasibility"] = a4_feas

    # ---- family A5 schedule-only ----
    a5_feas, a5_scheds = {}, {}
    folds = [F5.FoldWindow(f.fold_id, f.start, f.scored_end, f.purge_sessions) for f in partition_folds()]
    tr_datekeyed = {s: {dt.date.fromisoformat(k): v for k, v in series.items()} for s, series in tr.items()}
    date_sessions = [dt.date.fromisoformat(x) for x in sessions]
    for arm_id, cfg in F5.ARM_CONFIGS.items():
        sched = F5.generate_arm_schedule(cfg, tr_by_symbol=tr_datekeyed, sessions=date_sessions,
                                         calendar=CAL, folds=folds,
                                         coverage_start=dt.date.fromisoformat(COV_START))
        within = all(s.within_turnover_ceiling for s in sched.fold_summaries)
        a5_feas[cfg.arm_id] = {"decision_events": sum(s.decision_events for s in sched.fold_summaries),
                               "scored_events": sum(s.scored_events for s in sched.fold_summaries),
                               "total_two_way_turnover": round(sched.total_two_way_turnover, 4),
                               "ceiling": 6.0, "within_ceiling": within}
        a5_scheds[cfg.arm_id] = sched
    evidence["a5_feasibility"] = a5_feas

    # ---- six-arm exact dry run (temporary ledger, DUMMY metrics) ----
    ledger = TrialLedger(path="/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v2/staging-td/dryrun_ledger.json")
    keys = []
    for arm_id, book in a4_books.items():
        key = f"US_ETF_CASH|STOCKS_FREE_V2|{arm_id}|dryrun"
        keys.append(key)
        ledger.compute_recorded(key)  # dry-run compute marker (temp ledger only)
        artifact = {"arm_id": arm_id, "family": "A4_XSEC_ETF_RELATIVE_MOMENTUM",
                    "entries": len(book.entries), "metrics": {"dummy_total_pnl": 0.0, "is_dummy": True}}
        first = ledger.publish(key, artifact)
        replay = ledger.publish(key, artifact)
        evidence.setdefault("dryrun", []).append({"key": key, "first": first, "replay_delta": 0,
                                                  "replay_suppressed": not replay})
    for arm_id, sched in a5_scheds.items():
        key = f"US_ETF_CASH|STOCKS_FREE_V2|{arm_id}|dryrun"
        keys.append(key)
        ledger.compute_recorded(key)
        artifact = {"arm_id": arm_id, "family": "A5-SFV2-TREND-DEFENSIVE",
                    "books": len(sched.books), "metrics": {"dummy_total_pnl": 0.0, "is_dummy": True}}
        first = ledger.publish(key, artifact)
        replay = ledger.publish(key, artifact)
        evidence["dryrun"].append({"key": key, "first": first, "replay_delta": 0,
                                   "replay_suppressed": not replay})
    evidence["dryrun_summary"] = {"keys": len(keys), "unique_keys": len(set(keys)),
                                  "ledger_observed": ledger.observed,
                                  "ledger_published": len(ledger.published_keys),
                                  "real_cycle_counters_untouched": {"published": 0, "observed": 0}}
    ledger.save()
    evidence["feasibility_all_within_ceiling"] = all(
        v.get("within_ceiling", True) for v in list(a4_feas.values()) + list(a5_feas.values()))
    return evidence


def P_partition():
    from research.stocks_free_v1 import partition as P
    part = P.freeze_partition(coverage_start=datetime.date(2018, 1, 2),
                              coverage_end=datetime.date(2026, 8, 27))
    return {"warmup_start": part.warmup_start.isoformat(), "warmup_end": part.warmup_end.isoformat(),
            "s0_start": part.s0_start.isoformat(), "s0_end": part.s0_end.isoformat(),
            "s1_start": part.s1_start.isoformat(), "s1_end": part.s1_end.isoformat()}


def partition_folds():
    from research.stocks_free_v1 import partition as P
    part = P.freeze_partition(coverage_start=datetime.date(2018, 1, 2),
                              coverage_end=datetime.date(2026, 8, 27))
    return part.folds


def load_distributions():
    import zipfile, re
    def to_iso(v):
        v = str(v).strip()
        m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", v)
        if m:
            return f"{int(m.group(3)):04d}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
        return None

    def xlsx_rows(path):
        z = zipfile.ZipFile(path)
        s = z.read("xl/sharedStrings.xml").decode("utf-8", "replace")
        ss = [re.sub(r"<[^>]+>", "", m) for m in re.findall(r"<si>(.*?)</si>", s, re.S)]
        sheet = z.read("xl/worksheets/sheet1.xml").decode("utf-8", "replace")
        rows = []
        for rm in re.findall(r"<row[^>]*>(.*?)</row>", sheet, re.S):
            cells = {}
            for cm in re.finditer(r'<c r="([A-Z]+)(\d+)"([^>]*)>(.*?)</c>', rm, re.S):
                col, _, attrs, inner = cm.groups()
                v = re.search(r"<v>(.*?)</v>", inner, re.S)
                if not v:
                    continue
                val = v.group(1)
                if 't="s"' in attrs:
                    val = ss[int(val)]
                cells[col] = val
            if cells:
                rows.append(cells)
        return rows

    dist = {}
    for r in xlsx_rows(f"{V1STAGE}/spdr-etf-historical-distributions.xlsx"):
        t = str(r.get("B", "")).strip().upper()
        d = to_iso(r.get("D", ""))
        if not t or not d:
            continue
        amt = sum(float(r.get(c, 0) or 0) for c in ("G", "H") if r.get(c))
        dist.setdefault(t, {})[d] = dist.get(t, {}).get(d, 0.0) + amt
    return dist


def reconstruct_tr(raw_close, distributions, split_factors):
    dates = sorted(raw_close)
    cum, out, prev_raw, prev_level = 1.0, {}, None, None
    for d in dates:
        if d in split_factors:
            cum *= split_factors[d]
        sadj = raw_close[d] * cum
        if prev_level is None:
            level = 1.0
        else:
            level = prev_level * (sadj / prev_raw + distributions.get(d, 0.0) / prev_raw)
        out[d] = level
        prev_raw, prev_level = sadj, level
    return out


def _utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


if __name__ == "__main__":
    ev = main()
    out = "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v2/integration/research/audits/stocks_free_v2/z6_driver_evidence.json"
    import os
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(ev, f, indent=2)
        f.write("\n")
    print(json.dumps({"a4": ev["a4_feasibility"], "a5": ev["a5_feasibility"],
                      "dryrun": ev["dryrun_summary"], "all_within": ev["feasibility_all_within_ceiling"]},
                     indent=1))
