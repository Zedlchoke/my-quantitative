"""D6-IBKRREFETCH minimal serial re-fetch — STAGING-ONLY writer.

Reuses fut10_probe.py library functions (connect, fut_contract, details_row,
hist_request, by_conid, ErrCollector, redact) via read-only import. The probe's
stage functions (which write into raw/ and append to the root manifest) are NOT
invoked. All fetched payloads are written ONLY to:
  ~/.my-quantitative-data/futures-10syms-v1/staging_refetch_20261003/
Serial requests, >=2.5s pacing, hard request budget (default 29, canary already
spent 1 of the ~30 session budget). No credentials, readonly client.
"""
import hashlib
import json
import sys
import time
from pathlib import Path

CTL_ROOT = "/Users/hoangminhlong/my-quantitative/research/control/FUTURES-DATA-10SYMS-V1"
ANALYSIS = Path("/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep/"
                "research/control/FUTURES-DATACONTRACT-QUAL-V1/analysis/d6_ibkr")
STAGING = Path.home() / ".my-quantitative-data" / "futures-10syms-v1" / "staging_refetch_20261003"

sys.path.insert(0, CTL_ROOT)
import fut10_probe as fp  # noqa: E402

CLIENT_ID = 9262
REQUEST_BUDGET = 29          # canary already consumed 1 of the ~30 session budget
PACING_S = 2.5
ROLE = "d6-20261003"

# symbol -> (exchange, tradingClass, old_wall_boundary_month_to_probe_first, next_deeper)
# Baseline walls (S1_IDENTITY 2026-10-02): ES/NQ deepest_resolved=202509; FX=202512.
SCOPE = {
    "ES": ("CME", "ES", "202506", "202503"),
    "NQ": ("CME", "NQ", "202506", "202503"),
    "6E": ("CME", "6E", "202509", "202506"),
    "6B": ("CME", "6B", "202509", "202506"),
    "6A": ("CME", "6A", "202509", "202506"),
    "6J": ("CME", "6J", "202509", "202506"),
}

BASELINE_IDENT = json.loads((Path(CTL_ROOT) / "S1_IDENTITY.json").read_text())

STAGING.mkdir(parents=True, exist_ok=True)
log = {"started_utc": fp.now_utc(),
       "endpoint": f"TWSAPI {fp.HOST}:{fp.PORT} readonly client {CLIENT_ID}",
       "staging_dir": str(STAGING), "role": ROLE,
       "request_budget": REQUEST_BUDGET, "pacing_s": PACING_S,
       "requests": [], "files": [], "symbols": {}, "budget_exhausted": False}
seq = {"n": 0}


def budget_left():
    return REQUEST_BUDGET - seq["n"]


def paced():
    time.sleep(PACING_S)


def req_chain(ib, errs, sym, exch, tc):
    seq["n"] += 1
    errs.drain()
    cds = ib.reqContractDetails(fp.fut_contract(sym, exch, trading_class=tc))
    rows = sorted((fp.details_row(cd) for cd in cds),
                  key=lambda r: r["lastTradeDateOrContractMonth"])
    return rows, errs.drain()


def req_wall_probe(ib, errs, sym, exch, tc, ym):
    seq["n"] += 1
    errs.drain()
    try:
        cds = ib.reqContractDetails(
            fp.fut_contract(sym, exch, ym, expired=True, trading_class=tc))
    except Exception as e:  # noqa: BLE001
        return {"month": ym, "resolved": False, "exception": fp.redact(str(e))}
    ev = errs.drain()
    if cds:
        row = fp.details_row(cds[0])
        return {"month": ym, "resolved": True, "conId": row["conId"],
                "localSymbol": row["localSymbol"],
                "expiry": row["lastTradeDateOrContractMonth"], "errors": ev}
    return {"month": ym, "resolved": False, "errors": ev}


def fetch_to_staging(ib, errs, sym, cd, role, wu, bs, dur, end=""):
    c = fp.by_conid(cd["conId"], cd["exchange"])
    c.includeExpired = True
    seq["n"] += 1
    r = fp.hist_request(ib, errs, c, wu, bs, dur, end)
    name = (f"{sym}_{cd['localSymbol'].replace(' ', '')}_{cd['conId']}_{role}_"
            f"{wu}_{bs.replace(' ', '')}_{dur.replace(' ', '')}.json")
    path = STAGING / name
    payload = {
        "fetched_utc": fp.now_utc(), "symbol": sym, "conId": cd["conId"],
        "localSymbol": cd["localSymbol"], "role": role,
        "expiry_month": cd["lastTradeDateOrContractMonth"],
        "exchange": cd["exchange"], "whatUse": wu, "barSize": bs,
        "durationStr": dur, "endDateTime": end or "", "useRTH": True,
        "endpoint": f"TWSAPI {fp.HOST}:{fp.PORT} readonly client {CLIENT_ID}",
        "timeZoneId": cd.get("timeZoneId"), "ok": r["ok"],
        "errors": r.get("errors", []), "exception": r.get("exception"),
        "n_rows": len(r.get("rows", [])), "bars": r.get("rows", []),
    }
    data = json.dumps(payload, separators=(",", ":")).encode()
    path.write_bytes(data)
    rec = {"path": str(path), "bytes": len(data),
           "sha256": hashlib.sha256(data).hexdigest(),
           "symbol": sym, "conId": cd["conId"], "localSymbol": cd["localSymbol"],
           "role": role, "whatUse": wu, "barSize": bs, "durationStr": dur,
           "endDateTime": end or "", "n_rows": payload["n_rows"],
           "fetched_utc": payload["fetched_utc"], "ok": r["ok"],
           "request_seq": seq["n"]}
    log["files"].append(rec)
    return payload


ib = None
try:
    ib = fp.connect(CLIENT_ID)
    errs = fp.ErrCollector(ib)
    log["connection"] = {"connected": ib.isConnected(),
                         "serverVersion": ib.client.serverVersion(),
                         "client_id": CLIENT_ID, "readonly": True}
    for sym, (exch, tc, wall1, wall2) in SCOPE.items():
        if budget_left() < 5:  # need >= ~5 for a full symbol pass
            log["budget_exhausted"] = True
            break
        base = BASELINE_IDENT["symbols"][sym]
        base_ids = {r["conId"] for r in base.get("active_chain", [])}
        base_months = {r["lastTradeDateOrContractMonth"][:6]
                       for r in base.get("active_chain", [])}
        entry = {"requests_used": 0, "front": None, "newly_listable": [],
                 "wall_probes": [], "staged": []}

        # 1) active chain refresh (request)
        rows, ev = req_chain(ib, errs, sym, exch, tc)
        entry["chain_errors"] = ev
        entry["active_n"] = len(rows)
        if rows:
            entry["front"] = {k: rows[0][k] for k in
                              ("localSymbol", "conId", "lastTradeDateOrContractMonth")}
            entry["next"] = {k: rows[1][k] for k in
                             ("localSymbol", "conId", "lastTradeDateOrContractMonth")} if len(rows) > 1 else None
            now_ids = {r["conId"] for r in rows}
            entry["newly_listable"] = [
                {k: r[k] for k in ("localSymbol", "conId", "lastTradeDateOrContractMonth")}
                for r in rows if r["conId"] not in base_ids]
            entry["dropped_from_baseline"] = sorted(
                base_months - {r["lastTradeDateOrContractMonth"][:6] for r in rows})
        paced()

        # 2) front daily 3D TRADES refresh (request) -> staging
        if rows:
            p = fetch_to_staging(ib, errs, sym, rows[0], f"front-{ROLE}",
                                 "TRADES", "1 day", "3 D")
            entry["staged"].append({"localSymbol": rows[0]["localSymbol"],
                                    "role": f"front-{ROLE}", "ok": p["ok"],
                                    "n_rows": p["n_rows"],
                                    "last_bar": p["bars"][-1]["t"] if p["bars"] else None})
            paced()

        # 3) expired-wall probes just beyond the 2026-10-02 wall (requests)
        resolved_wall = None
        for ym in (wall1, wall2):
            if budget_left() < 3:
                log["budget_exhausted"] = True
                break
            probe = req_wall_probe(ib, errs, sym, exch, tc, ym)
            entry["wall_probes"].append(probe)
            paced()
            if probe["resolved"] and resolved_wall is None:
                resolved_wall = probe
                # 4) daily 3D fetch for the first newly-resolved month (request)
                cd_w = {"conId": probe["conId"], "exchange": exch,
                        "localSymbol": probe["localSymbol"],
                        "lastTradeDateOrContractMonth": probe["expiry"],
                        "timeZoneId": None}
                pw = fetch_to_staging(ib, errs, sym, cd_w, f"wallrecalled-{ROLE}",
                                      "TRADES", "1 day", "3 D",
                                      end=f"{probe['expiry'][:4]}{probe['expiry'][4:6]}01 00:00:00")
                entry["staged"].append({"localSymbol": probe["localSymbol"],
                                        "role": f"wallrecalled-{ROLE}", "ok": pw["ok"],
                                        "n_rows": pw["n_rows"],
                                        "last_bar": pw["bars"][-1]["t"] if pw["bars"] else None})
                paced()
        entry["requests_used"] = seq["n"]
        log["symbols"][sym] = entry
        print(f"[d6] {sym}: front={entry['front']} new_list={len(entry['newly_listable'])} "
              f"wall_probes={[ (p['month'], p['resolved']) for p in entry['wall_probes'] ]} "
              f"staged={len(entry['staged'])} seq={seq['n']}", flush=True)
finally:
    log["finished_utc"] = fp.now_utc()
    log["requests_total"] = seq["n"]
    if ib is not None:
        try:
            ib.disconnect()
        except Exception:  # noqa: BLE001
            pass
    (ANALYSIS / "d6_fetch_log.json").write_text(json.dumps(log, indent=1))
    print(f"[d6] done requests_total={log['requests_total']} "
          f"files={len(log['files'])} budget_exhausted={log['budget_exhausted']}", flush=True)
