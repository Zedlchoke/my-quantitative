#!/usr/bin/env python
"""Cost / roll / event-PIT cheap re-measures (FX-EB-CALENDAR lane).

(a) roll: read the HELD-chain parquets already in this worktree (deepresearch V2
    6E_cache / 6B_cache), count held-contract switches + infer the observed
    roll rule from switch dates vs the calendar expiry cells. NO new chain built.
(c) events: count FOMC statement decisions and BoE MPC decisions 2023-2026
    from the on-disk nonprice artifacts (fed/statements + 6B_deep_lib loaders
    re-implemented locally — read-only, no imports of sibling code).
"""
import glob
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/futures-six-readiness/prep")
DR = WT / "research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis"
NONPRICE = "/Users/hoangminhlong/.my-quantitative-data/futures-nonprice-10syms"
OUT = WT / "research/control/FUTURES-SIX-READINESS-20261004/fx_eb/cost_roll_events"
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def measure_roll(sym):
    p = DR / f"{sym}_cache" / "held_calendar.parquet"
    df = pd.read_parquet(p)
    df = df.sort_values("session_date").reset_index(drop=True)
    held = df["held"].tolist()
    switches = []
    for i in range(1, len(held)):
        if held[i] != held[i - 1]:
            switches.append({
                "first_session_on_new_contract": str(df["session_date"].iloc[i]),
                "last_session_on_old_contract": str(df["session_date"].iloc[i - 1]),
                "from": held[i - 1], "to": held[i],
            })
    # observed roll rule: gap from old contract's last held session to its expiry
    # (expiry from the contract registry, data-observed last bar). NOTE:
    # contract_registry.json exists in 6E_cache only.
    reg_path = DR / f"{sym}_cache" / "contract_registry.json"
    reg_by_contract = {}
    reg_sha = None
    if reg_path.exists():
        reg = json.loads(reg_path.read_text())
        reg_by_contract = {r["contract"]: r for r in reg}
        reg_sha = sha256_file(reg_path)
    for s in switches:
        old = reg_by_contract.get(s["from"])
        if old:
            exp = old.get("expiry_obs") or old.get("expiry")
            s["old_contract_expiry_obs"] = exp
            if exp:
                d_exp = datetime.strptime(exp, "%Y-%m-%d")
                d_last = datetime.strptime(s["last_session_on_old_contract"], "%Y-%m-%d")
                s["days_lastheld_before_expiry_obs"] = (d_exp - d_last).days
    # 6B alternative: chain_calendar.parquet carries the contract timeline
    chain_note = None
    chain_path = DR / f"{sym}_cache" / "chain_calendar.parquet"
    chain_rows = 0
    if chain_path.exists():
        try:
            ch = pd.read_parquet(chain_path)
            chain_rows = len(ch)
            chain_note = f"chain_calendar.parquet present ({chain_rows} rows, cols {list(ch.columns)})"
        except Exception as e:
            chain_note = f"chain_calendar.parquet unreadable: {e!r}"
    return {
        "held_calendar_parquet": str(p),
        "held_calendar_sha256": sha256_file(p),
        "contract_registry": (str(reg_path) if reg_sha else
                              "ABSENT in this cache (6E-only artifact); roll gaps vs data-observed expiry NOT computable for this symbol from registry — expiry cross-ref available via calendar cells in fx_eb_expiry_2023_2026.json"),
        "contract_registry_sha256": reg_sha,
        "chain_calendar_note": chain_note,
        "n_sessions": len(df),
        "first_session": str(df["session_date"].iloc[0]),
        "last_session": str(df["session_date"].iloc[-1]),
        "n_contracts_held": len(set(held)),
        "n_roll_switches": len(switches),
        "switches": switches,
    }


def count_fomc_2023_2026():
    files = sorted(glob.glob(f"{NONPRICE}/fed/statements/monetary*.html"))
    rows = []
    for f in files:
        m = re.fullmatch(r"monetary(\d{8})a\.html", Path(f).name)
        if not m:
            continue
        d = datetime.strptime(m.group(1), "%Y%m%d")
        rows.append(d)
    in_window = [d for d in rows if datetime(2023, 1, 1) <= d <= datetime(2026, 9, 30)]
    future_sched = [d for d in rows if d > datetime(2026, 9, 30)]
    return {
        "source_dir": f"{NONPRICE}/fed/statements/ (monetary*YYYYMMDDa.html decision statements)",
        "n_statement_files_total": len(rows),
        "n_dated_decisions_2023_2026_through_20260930": len(in_window),
        "by_year": {y: sum(1 for d in in_window if d.year == y) for y in (2023, 2024, 2025, 2026)},
        "dates": [d.strftime("%Y-%m-%d") for d in in_window],
        "post_panel_scheduled_files": [d.strftime("%Y-%m-%d") for d in future_sched],
        "vintage_law": "each statement is dated by its own filename+content (as-published artifact); FOMC calendar events are keyed to vintage as-of decision date; current-calendar inference about unscheduled future meetings FORBIDDEN",
    }


def count_boe_2023_2026():
    # Re-implemented locally from the 6B dossier's published calendar (lib 6B_deep_lib
    # load_mpc_calendar, dates assembled from bankofengland.co.uk 2026-10-02 and
    # cross-checked vs boe_bank_rate_tidy.parquet rate-change rows).
    sched = {
        2023: ["2023-02-02", "2023-03-23", "2023-05-11", "2023-06-22", "2023-08-03",
               "2023-09-21", "2023-11-02", "2023-12-14"],
        2024: ["2024-02-01", "2024-03-21", "2024-05-09", "2024-06-20", "2024-08-01",
               "2024-09-19", "2024-11-07", "2024-12-19"],
        2025: ["2025-02-06", "2025-03-20", "2025-05-08", "2025-06-19", "2025-08-07",
               "2025-09-18", "2025-11-06", "2025-12-18"],
        2026: ["2026-02-05", "2026-03-19", "2026-04-30", "2026-06-18", "2026-07-30",
               "2026-09-17", "2026-11-05", "2026-12-17"],
    }
    rate = pd.read_parquet(f"{NONPRICE}/normalized/boe_bank_rate_tidy.parquet")
    rate["obs"] = pd.to_datetime(rate["observation_date"])
    changes = set(rate["obs"].dt.strftime("%Y-%m-%d"))
    rows = []
    for y, ds in sched.items():
        for s in ds:
            d = datetime.strptime(s, "%Y-%m-%d")
            rows.append({"date": s, "changed_rate": s in changes,
                         "in_panel_through_20260930": d <= datetime(2026, 9, 30)})
    in_panel = [r for r in rows if r["in_panel_through_20260930"]]
    return {
        "source": "BoE MPC announcement dates assembled by DEEP-6B lane from bankofengland.co.uk (fetched 2026-10-02), restated verbatim from FUTURES-DEEPRESEARCH-V2-20261003/analysis/6B_deep_lib.py::load_mpc_calendar; rate-change flags cross-checked vs normalized/boe_bank_rate_tidy.parquet here",
        "n_mpc_dates_2023_2026_listed": len(rows),
        "n_in_panel_through_20260930": len(in_panel),
        "by_year_in_panel": {y: sum(1 for r in in_panel if r["date"].startswith(str(y)))
                             for y in (2023, 2024, 2025, 2026)},
        "rate_change_dates_in_panel": [r["date"] for r in in_panel if r["changed_rate"]],
        "forward_scheduled_post_panel": [r["date"] for r in rows if not r["in_panel_through_20260930"]],
        "vintage_law": "MPC decision dates are as-of decision date artifacts; forward-scheduled dates (post 2026-09-30) are labeled forward_scheduled and never treated as decisions",
    }


def crossref_switches_vs_calendar(roll_doc):
    """Cross-ref roll switches vs the official calendar cells obtained this lane
    (6B: BP codes; 6E: EC codes). Adds days_lastheld_before_official_expiry where
    the old contract's quarter cell is OBTAINED."""
    cal = json.loads((WT / "research/control/FUTURES-SIX-READINESS-20261004/fx_eb/"
                      "calendar/fx_eb_expiry_2023_2026.json").read_text())
    for sym in ("6E", "6B"):
        r = roll_doc.get(sym)
        if not r or "switches" not in r:
            continue
        for s in r["switches"]:
            # held names look like 6EH0_2020 / 6BZ6_2026 -> month letter + year
            m = re.match(r"6[EB]([HMUZ])\d_(\d{4})", s["from"])
            if not m:
                continue
            letter, year = m.group(1), int(m.group(2))
            q = {"H": "Q1", "M": "Q2", "U": "Q3", "Z": "Q4"}[letter]
            cell = cal[sym]["quarters"].get(f"{year}{q}", {})
            if cell.get("status") == "OBTAINED":
                s["official_last_trade_date"] = cell["last_trade_date"]
                s["official_source"] = cell["source_file"].split("/")[-1]
                d_exp = datetime.strptime(cell["last_trade_date"], "%Y-%m-%d")
                d_last = datetime.strptime(s["last_session_on_old_contract"], "%Y-%m-%d")
                s["days_lastheld_before_official_expiry"] = (d_exp - d_last).days


def main():
    doc = {"schema": "fxeb_cost_roll_events@1", "lane": "FX-EB-CALENDAR",
           "task_id": "FUTURES-SIX-READINESS-20261004", "generated_utc": NOW}

    roll = {}
    for sym in ("6E", "6B"):
        try:
            roll[sym] = measure_roll(sym)
        except Exception as e:
            roll[sym] = {"status": "NOT_RUN", "error": repr(e), "path": str(DR / f"{sym}_cache/held_calendar.parquet")}
    doc["roll_remeasure"] = {
        "law": "measured from the EXISTING held-chain parquet in this worktree; no new chain built (out of lane scope); rule stated as OBSERVED switch pattern, not derived from IMM text",
        "matrix_baseline": "6E/6B roll_rule NOT_RUN per P3-round matrix",
        "6E": roll["6E"], "6B": roll["6B"],
    }
    crossref_switches_vs_calendar(roll)

    doc["fomc_2023_2026"] = count_fomc_2023_2026()
    doc["boe_mpc_2023_2026"] = count_boe_2023_2026()
    doc["ecb_6e"] = {
        "baseline": "ECB 55 meetings 2020-2026.9, 55/55 in data, decision 14:15 CET/CEST, press conf 14:45 (6E_a4_events.json, ECB archive fetched 2026-10-02; 10 dates machine-verified by direct press-release URL fetch) — restated, not refetched",
        "path": str(DR / "6E_a4_events.json"),
        "sha256": sha256_file(DR / "6E_a4_events.json"),
    }
    doc["bls_vintage_restate"] = {
        "law": "BLS PIT vintage law in force: event calendars keyed to vintage as-of decision date; current-calendar inference FORBIDDEN. 2025 lapse-in-appropriations anomalies RESOLVED in baseline bls_vintage artifacts (FUTURES-OVERNIGHT-PREP-20261003/bls_vintage/BLS_VINTAGE_INVESTIGATION.md + P3 data_checks/BLS_VINTAGE_NORMALIZATION.md) — cited, not refetched per dispatch",
    }
    out = OUT / "cost_roll_events_fxeb.json"
    out.write_text(json.dumps(doc, indent=1, default=str))
    for sym in ("6E", "6B"):
        r = roll[sym]
        if "n_roll_switches" in r:
            print(sym, "roll switches:", r["n_roll_switches"],
                  "| contracts:", r["n_contracts_held"],
                  "| sessions:", r["n_sessions"],
                  "| sample gap:", [s.get("days_lastheld_before_expiry_obs") for s in r["switches"][:8]])
        else:
            print(sym, r)
    print("FOMC 23-26:", doc["fomc_2023_2026"]["n_dated_decisions_2023_2026_through_20260930"],
          doc["fomc_2023_2026"]["by_year"])
    print("BoE 23-26 in panel:", doc["boe_mpc_2023_2026"]["n_in_panel_through_20260930"],
          doc["boe_mpc_2023_2026"]["by_year_in_panel"],
          "| changes:", len(doc["boe_mpc_2023_2026"]["rate_change_dates_in_panel"]))


if __name__ == "__main__":
    main()
