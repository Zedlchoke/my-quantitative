#!/usr/bin/env python
"""FX-EB-CALENDAR master extraction.

Builds, from verified captures only:
  1. fx_eb_expiry_2023_2026.json  — 6E/6B quarterly expiry cells 2023Q1..2026Q4
  2. holiday/holiday_deviation_6e_6b.json — 6E/6B holiday-deviation grids 2023-2026
No IMM-rule derivation anywhere: every obtained cell is a dated official value
read from an archived official capture whose bytes this lane hashed.

Sources (all hash-verified in this lane):
  - pcal_58_6e_20210703144932.json   (sibling Q5 capture; verified q5_6e_verify_result.json PASS)
  - pcal_42_6b_dl_20240903.xls       (this lane's fetch; xlrd parse here)
  - svc_*.json 10-product trading-hours captures (sibling 30 + this lane 13)
"""
import gzip
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import xlrd

LANE = Path(__file__).resolve().parent
CAP = LANE / "captures"
SIB_CAP = Path("/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep/"
               "research/control/FUTURES-P3-QUARANTINE-20261004/cal_permitted/captures")
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

QUARTERS = [f"{y}{q}" for y in (2023, 2024, 2025, 2026) for q in ("Q1", "Q2", "Q3", "Q4")]
# contract-month quarter mapping: Q1=H(Mar) Q2=M(Jun) Q3=U(Sep) Q4=Z(Dec)
Q2CODE = {"Q1": "H", "Q2": "M", "Q3": "U", "Q4": "Z"}


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ---------------------------------------------------------------- 6E expiry
def extract_6e():
    p = SIB_CAP / "pcal_58_6e_20210703144932.json"
    rows = json.loads(p.read_text())
    out = {}
    for r in rows:
        code = r["productCode"]  # e.g. ECH26
        sym, my = code[:2], code[2:]          # EC + H26
        year = 2000 + int(my[1:])
        month_code = my[0]
        q = {"H": "Q1", "M": "Q2", "U": "Q3", "Z": "Q4"}.get(month_code)
        if year < 2023 or year > 2026 or q is None:
            continue
        lt = r["lastTrade"]  # e.g. "16 Mar 2026"
        d = datetime.strptime(lt, "%d %b %Y").strftime("%Y-%m-%d")
        out[f"{year}{q}"] = {
            "status": "OBTAINED", "contract": code, "last_trade_date": d,
            "last_trade_as_published": lt,
            "source": "ARCHIVED_OFFICIAL_SERVICE (Wayback capture of cmegroup.com CmeWS/mvc/ProductCalendar/Future/58)",
            "source_file": "sibling:FUTURES-P3-QUARANTINE-20261004/cal_permitted/captures/pcal_58_6e_20210703144932.json",
            "source_sha256": sha256_file(p),
            "capture_utc_of_original": "2021-07-03T14:49:32Z (Wayback timestamp)",
            "q5_independent_verify": "PASS (q5_independent_verify/q5_6e_verify_result.json)",
            "vintage_note": "as-published snapshot 2021-07-03; values are dated official rows, not rule-derived; later CME revision of far-dated rows cannot be excluded",
        }
    return out


# ---------------------------------------------------------------- 6B expiry
def extract_6b():
    p = CAP / "pcal_42_6b_dl_20240903.xls"
    wb = xlrd.open_workbook(str(p))
    sh = wb.sheet_by_index(0)
    sheet_name = sh.name  # 'Product Calendar Sep 2 2024'
    hdr = None
    out = {}
    for i in range(sh.nrows):
        vals = [sh.cell_value(i, j) for j in range(sh.ncols)]
        if vals[0] == "Contract Month":
            hdr = vals
            continue
        if hdr is None or not vals[0]:
            continue
        desc, code = vals[0], vals[1]
        last_trade = str(vals[3]).strip()
        if not code.startswith("BP") or "GBP/USD" not in desc:
            continue
        my = code[2:]                       # e.g. U24
        month_code = my[0]
        year = 2000 + int(my[1:])
        q = {"H": "Q1", "M": "Q2", "U": "Q3", "Z": "Q4"}.get(month_code)
        if year < 2023 or year > 2026 or q is None:
            continue
        out[f"{year}{q}"] = {
            "status": "OBTAINED", "contract": code,
            "last_trade_date": last_trade,
            "last_trade_as_published": last_trade,
            "source": "ARCHIVED_OFFICIAL (Wayback capture of cmegroup.com CmeWS/mvc/ProductCalendar/Download.xls?productId=42)",
            "source_file": "captures/pcal_42_6b_dl_20240903.xls (this lane fetch, fetch_log.jsonl)",
            "source_sha256": sha256_file(p),
            "capture_utc_of_original": "2024-09-03T01:13:31Z (Wayback timestamp; sheet '%s')" % sheet_name,
            "q5_independent_verify": "n/a (this lane's own capture; parsed with own xlrd parser)",
            "vintage_note": "as-published snapshot 2024-09-03; expired contracts absent by design of the service, so 2023Q1..2024Q2 rows are not in any archived 6B calendar",
        }
    return out


def build_expiry():
    e6, b6 = extract_6e(), extract_6b()
    doc = {
        "schema": "fx_eb_expiry_2023_2026@1",
        "task_id": "FUTURES-SIX-READINESS-20261004",
        "lane": "FX-EB-CALENDAR",
        "generated_utc": NOW,
        "law": "only dated official values from hash-verified archived official captures; IMM-rule derivation FORBIDDEN and not used; NOT_OBTAINED never inferred",
        "baseline": {
            "cumulative_fx_expiry_cells": "236/272 (per P3-quarantine round matrix)",
            "6E": "64/68 (2023-2026 mostly NOT_OBTAINED)",
            "6B": "52/68 (2023-2026 NOT_OBTAINED)",
        },
        "6E": {"quarters": {}}, "6B": {"quarters": {}},
    }
    for q in QUARTERS:
        cell = e6.get(q) or {
            "status": "NOT_OBTAINED",
            "reason": "archived ProductCalendar/Future/58 max capture = 2021-07-03 (rows end Jun-2026; confirmed by this lane CDX captures/cdx_future58_prefix.txt); live service BLOCKED_TRANSPORT per sibling measurement; rule derivation forbidden",
        }
        doc["6E"]["quarters"][q] = cell
        cellb = b6.get(q) or {
            "status": "NOT_OBTAINED",
            "reason": "archived 6B calendars: Future/42 max 2018-04-08 (pre-span) and Download.xls?productId=42 earliest 2024-09-03 (expired contracts dropped by service); no capture covers 2023Q1-2024Q2 (CDX captures/cdx_future42_prefix.txt, captures/cdx_downloadxls42.txt); rule derivation forbidden",
        }
        doc["6B"]["quarters"][q] = cellb
    for sym in ("6E", "6B"):
        n = sum(1 for c in doc[sym]["quarters"].values() if c["status"] == "OBTAINED")
        doc[sym]["obtained_2023_2026"] = f"{n}/16"
    doc["future_rows_not_in_grid"] = {
        "note": "additional dated official rows present in the same verified captures, outside the 2023-2026 mission grid; recorded for completeness",
        "6E_from_pcal58": ["ECH26 2026-03-16, ECM26 2026-06-15 are IN grid; file also carries 2021-06..2022 rows (incl. ECZ22 19 Dec 2022 QA cross-check)"],
        "6B_from_pcal42": {"2027": {"BPH27": "2027-03-15", "BPM27": "2027-06-14", "BPU27": "2027-09-13", "BPZ27": "2027-12-13"},
                            "2028": {"BPH28": "2028-03-13", "BPM28": "2028-06-16", "BPU28": "2028-09-18", "BPZ28": "2028-12-18"},
                            "2029_partial": {"BPH29": "2029-03-19", "BPM29": "2029-06-15"}},
        "dispatch_claim_correction": "dispatch named '6E 2027-2029 rows in pcal_58_6e_*.json' as unextracted values: NOT PRESENT — the 6E capture's rows end at Jun-2026 (24 rows listed; 2027+ count = 0). ECH26/ECM26 were present and are extracted. The 2027-2029 forward chain exists only in the 6B XLS and the sibling 6J XLS.",
    }
    out = LANE / "calendar" / "fx_eb_expiry_2023_2026.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(doc, indent=1))
    print("expiry:", doc["6E"]["obtained_2023_2026"], "6E |", doc["6B"]["obtained_2023_2026"], "6B")
    return doc


# ---------------------------------------------------------------- holidays
# window -> (year, holiday label, capture path, origin)
def load_grid():
    entries = []
    for p in sorted(SIB_CAP.glob("svc_*.json")):
        entries.append((p, "sibling"))
    for p in sorted(CAP.glob("svc_*.json")):
        entries.append((p, "this_lane"))
    grid = []
    for p, origin in entries:
        try:
            d = json.loads(p.read_text())
        except Exception:
            d = json.loads(gzip.decompress(p.read_bytes()))
        prods = d.get("products", [])
        ids = [pr.get("id") for pr in prods]
        rec = {"capture": p.name, "origin": origin,
               "sha256": sha256_file(p), "product_ids": sorted(i for i in ids if i is not None)}
        e6 = next((pr for pr in prods if pr.get("id") == 58), None)
        b6 = next((pr for pr in prods if pr.get("id") == 42), None)
        rec["6E_schedules"] = (e6 or {}).get("tradingHours", {}).get("schedules", [])
        rec["6B_present"] = b6 is not None
        grid.append(rec)
    return grid


def fmt_events(scheds):
    out = {}
    for sch in scheds:
        ed = sch.get("eventDate")
        evs = [[e.get("tradingDate"), e.get("eventTime"), e.get("marketEventType")]
               for e in sch.get("events", [])]
        out[ed] = evs
    return out


def legality_check(events_by_date):
    """Validate legality of an obtained deviation grid.

    Service semantics (verified against sibling 2024/2026 captures + this
    lane's 2023/2025 fetches): eventDate = calendar day (may be a weekend day
    of a holiday weekend); events reference tradingDate (the affected session),
    which may precede or follow the eventDate; empty events list = service
    explicitly reports no deviation events for that day. Checks here: event
    type whitelist, time format/range, tradingDate within +/-5 days.
    """
    problems = []
    for ed, evs in sorted(events_by_date.items()):
        try:
            d = datetime.strptime(ed, "%Y-%m-%d")
        except Exception:
            problems.append(f"eventDate unparseable: {ed}")
            continue
        for td, tm, typ in evs:
            if typ not in ("open", "preopen", "closed"):
                problems.append(f"{ed}: unknown marketEventType {typ}")
            if not tm or len(tm) != 5 or tm[2] != ":":
                problems.append(f"{ed}: bad eventTime {tm}")
            else:
                hh, mm = int(tm[:2]), int(tm[3:])
                if not (0 <= hh <= 24 and 0 <= mm < 60):
                    problems.append(f"{ed}: out-of-range eventTime {tm}")
            try:
                tdd = datetime.strptime(td, "%Y-%m-%d")
                if abs((tdd - d).days) > 5:
                    problems.append(f"{ed}: tradingDate {td} more than 5 days from eventDate")
            except Exception:
                problems.append(f"{ed}: tradingDate unparseable {td}")
    return problems


def build_holidays():
    grid = load_grid()
    windows = []
    for rec in grid:
        m = rec["capture"].split("_")
        raw = m[1]
        wfrom = f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"  # normalized ISO window key
        # crawl timestamp from the Wayback stamp embedded in the filename
        crawl = datetime.strptime(m[2].split(".")[0][:8], "%Y%m%d")
        e6 = fmt_events(rec["6E_schedules"])
        has_id58 = rec["6E_schedules"] is not None and len(rec["6E_schedules"]) > 0
        n_dev_events = sum(len(v) for v in e6.values())
        problems = legality_check({k: v for k, v in e6.items() if v}) if e6 else []
        if has_id58 and n_dev_events > 0:
            verdict = "OBTAINED_DEVIATION" if not problems else "ILLEGAL_FORMAT"
        elif has_id58:
            verdict = "NORMAL_HOURS_DOCUMENTED"  # zero deviation events, in-service-lookback
        else:
            verdict = "NO_ID58_DATA"
        days_from_crawl = abs((datetime.strptime(
            sorted(e6.keys())[-1] if e6 else wfrom, "%Y-%m-%d") - crawl).days)
        windows.append({
            "capture": rec["capture"], "origin": rec["origin"],
            "sha256": rec["sha256"],
            "window_first_event_date": wfrom,
            "crawl_utc": crawl.strftime("%Y-%m-%d"),
            "days_window_to_crawl": days_from_crawl,
            "within_lookback_365d": days_from_crawl <= 365,
            "n_event_dates_id58": len(e6),
            "n_deviation_events_id58": n_dev_events,
            "6E_events": e6,
            "6B_id42_present": rec["6B_present"],
            "legality_problems": problems,
            "verdict": verdict,
        })

    # --- window-level aggregation (some windows have 2+ archived captures) ---
    # aged-out law: a 0-event grid is evidence of normal hours ONLY when the
    # window lies within ~365 days of the crawl timestamp. Empirical bracket:
    # Labor-2023 window (307d pre-crawl) carries 7 events while July4-2023
    # (369d) and all earlier-2023 windows carry 0 events in the same crawl
    # batch — the service drops events older than ~1 year (and mirrors the
    # same horizon forward). Cells are never invented from aged-out captures.
    by_window = {}
    for w in windows:
        key = w["window_first_event_date"]
        by_window.setdefault(key, []).append(w)
    window_rows = []
    for key in sorted(by_window):
        caps = by_window[key]
        dev = [c for c in caps if c["verdict"] == "OBTAINED_DEVIATION"]
        norm = [c for c in caps if c["verdict"] == "NORMAL_HOURS_DOCUMENTED"
                and c["within_lookback_365d"]]
        aged0 = [c for c in caps if c["verdict"] == "NORMAL_HOURS_DOCUMENTED"
                 and not c["within_lookback_365d"]]
        if dev:
            status = "OBTAINED_DEVIATION"
        elif norm:
            status = "NORMAL_HOURS_DOCUMENTED"
        else:
            status = "INCONCLUSIVE_AGED_OUT"
        window_rows.append({
            "window_first_event_date": key,
            "status": status,
            "captures": [{k: c[k] for k in ("capture", "origin", "sha256", "crawl_utc",
                                            "days_window_to_crawl", "n_deviation_events_id58",
                                            "verdict")} for c in caps],
            "deviation_events": max((c["n_deviation_events_id58"] for c in caps), default=0),
            "aged_out_captures": [c["capture"] for c in aged0],
        })
    # 6B: document absence across ALL captures (both origins)
    b_present = [w["capture"] for w in windows if w["6B_id42_present"]]
    n_obt = sum(1 for r in window_rows if r["status"] == "OBTAINED_DEVIATION")
    n_norm = sum(1 for r in window_rows if r["status"] == "NORMAL_HOURS_DOCUMENTED")
    n_aged = sum(1 for r in window_rows if r["status"] == "INCONCLUSIVE_AGED_OUT")
    n_doc = n_obt + n_norm
    doc = {
        "schema": "fx_eb_holiday_deviation@1",
        "task_id": "FUTURES-SIX-READINESS-20261004",
        "lane": "FX-EB-CALENDAR",
        "generated_utc": NOW,
        "cell_definition": "cell = (archived holiday window) for which the official by-product trading-hours service carries product id 58 (6E) data. Window status: OBTAINED_DEVIATION (>=1 deviation event in any capture), NORMAL_HOURS_DOCUMENTED (zero deviation events, capture within the service's ~1y lookback), INCONCLUSIVE_AGED_OUT (zero events but capture older than ~365d from the window — service lookback artifact, NOT evidence of normal hours).",
        "aged_out_law": "the service returns deviation events only within ~1 year of the query timestamp (empirical bracket: Labor-2023 window at 307d pre-crawl has 7 events; July4-2023 at 369d and all earlier 2023 windows have 0 events in the same 2024-07-08 crawl batch; horizon mirrors forward). Aged-out zero-grids are never counted as cells.",
        "law": "extraction from hash-verified archived official captures only; current-calendar inference FORBIDDEN",
        "6E": {
            "windows": window_rows,
            "captures_raw": windows,
            "obtained_deviation_windows": f"{n_obt}/{len(window_rows)}",
            "documented_windows_deviation_or_normal": f"{n_doc}/{len(window_rows)}",
            "inconclusive_aged_out": f"{n_aged}/{len(window_rows)}",
            "by_year": {},
        },
        "6B": {
            "verdict": "NOT_OBTAINED for all windows 2023-2026",
            "reason": "product id 42 (6B) appears in NO archived trading-hours-by-product capture: this lane CDX probe url=cmegroup.com/services/trading-hours-by-product* filter original:.*id=42.* returned zero rows (2 attempts, captures/cdx_services_id42 attempt log in fetch_log.jsonl), consistent with the sibling round's full URL-id enumeration (cdx_services_tradinghours_full.txt: ids 133,167,316,318,5224 + idlists 316,133,425,300,58,437,22,8478,5201,10191 only). Live service BLOCKED_TRANSPORT (sibling measurement, unchanged).",
            "id42_captures_found": b_present,
        },
        "dispatch_baseline_reconciliation": "dispatch stated 'FX 2023-2025 holiday/deviation times 28/48 -> 6E 12/12 ... 6B 0/12': those are the sibling T2 EXPIRY-date counts (retry doc Target 2), mislabeled as holiday times. The sibling's coverage JSON never tabulated 6E holiday grids (T4 per_product_event_log holds CL/GC only). This artifact is the first per-product 6E holiday tabulation; its counts supersede the '12/12 holiday' figure.",
    }
    for y, date_keys in ((2023, ["2022-12-31", "2023"]),
                         (2024, ["2024"]),
                         (2025, ["2025"]),
                         (2026, ["2026"])):
        ws = [r for r in window_rows
              if any(r["window_first_event_date"].startswith(k) for k in date_keys)]
        got = [r for r in ws if r["status"] == "OBTAINED_DEVIATION"]
        documented = [r for r in ws if r["status"] in ("OBTAINED_DEVIATION", "NORMAL_HOURS_DOCUMENTED")]
        aged = [r for r in ws if r["status"] == "INCONCLUSIVE_AGED_OUT"]
        doc["6E"]["by_year"][str(y)] = {
            "deviation": f"{len(got)}/{len(ws)}",
            "documented": f"{len(documented)}/{len(ws)}",
            "aged_out": f"{len(aged)}/{len(ws)}",
        }
    out = LANE / "holiday" / "holiday_deviation_6e_6b.json"
    out.write_text(json.dumps(doc, indent=1))
    print("6E deviation windows:", doc["6E"]["obtained_deviation_windows"],
          "| documented:", doc["6E"]["documented_windows_deviation_or_normal"])
    print("by year:", json.dumps(doc["6E"]["by_year"]))
    print("6B id42 present in:", b_present)
    bad = [c["capture"] for r in window_rows for c in r["captures"] if c["verdict"] == "ILLEGAL_FORMAT"]
    print("ILLEGAL_FORMAT windows:", bad)
    return doc


if __name__ == "__main__":
    build_expiry()
    build_holidays()
