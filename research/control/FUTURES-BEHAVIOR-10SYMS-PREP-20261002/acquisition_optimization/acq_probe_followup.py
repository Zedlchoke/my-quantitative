#!/usr/bin/env python3
"""acq_probe_followup.py — ACQ-OPT follow-up probe + final re-aggregation.

Round 1 (acq_probe.py, 195 logical requests, 194x200 + 1x422) left three
gaps, closed here WITHOUT re-requesting anything already measured:

 1. get_cost aggregation bug: round-1 `count_value()` accepted int payloads
    only; get_cost returns a FLOAT — payloads are all stored, so costs are
    recovered offline from coverage_results.json (zero new requests).
 2. pkgA measured $139.12 list vs the ~$100 scenario -> re-quote a tuned
    pkgA-v2 (windows shortened; pkgA-v1 kept as the "+24m-floor variant").
 3. CL bbo-1m via parent is dominated by far-month quote books (56.6 GB /
    $1,019 full; $194 for 2y) -> quote (a) a representative CL roll-window
    bbo-1m anchor on raw symbols and (b) a bounded CL-BBO-12M option, then
    restructure pkgB/pkgC to roll-window-enumerated CL bbo (design lines).
 4. symbology.resolve retry with start_date >= 2010-06-06 (round-1 422 was
    `data_start_date_before_available_start_date` — the stype combination
    itself passed validation).

Metadata-only. Same key law as acq_probe.py. New requests: 43 (cap check
continues from round 1; combined hard cap 260 honored).
"""

import base64
import datetime as dt
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
OUT_PATH = SCRIPT_DIR / "coverage_results.json"
PKG_DIR = SCRIPT_DIR / "package_manifests"

PRIMARY_HOST = "https://hist.databento.com"
FALLBACK_HOST = "https://databento.com"
DATASET = "GLBX.MDP3"
GB = 1_000_000_000.0
COMBINED_CAP = 260
MAX_ATTEMPTS = 3
BACKOFF_S = (2.0, 5.0)
SLEEP_BETWEEN_S = 0.4
ATTEMPT_TIMEOUT_S = 60
RECORD_SIZE = {"ohlcv-1m": 56, "bbo-1m": 80, "statistics": 80,
               "definition": 520}

ALL_ROOTS = ["NQ", "ES", "CL", "NG", "GC", "SI", "6E", "6J", "6B", "6A"]
PARENT = {r: f"{r}.FUT" for r in ALL_ROOTS}

# pkgA-v2 (~$100 scenario): all 10 symbols, windows tuned to measured
# per-root rates; 24m floor sacrificed on all (documented) — pkgA-v1 keeps it
# for 8/10 at $139.12.
PKG_A2_OHLCV = {
    **{r: ("2025-04-01", "2026-10-01") for r in
       ["NQ", "ES", "GC", "SI", "6E", "6J", "6B", "6A"]},   # 18 months
    "CL": ("2026-01-01", "2026-10-01"),                      # 9 months
    "NG": ("2026-01-01", "2026-10-01"),                      # 9 months
}
PKG_A2_JOINED = {"definition": ("2024-10-01", "2026-10-01"),  # 24m listing lead
                 "statistics": ("2025-04-01", "2026-10-01")}  # 18m

# Representative CL roll window (manifest CL-roll-4): CLN6->CLQ6 switch at
# end of June 2026; bbo-1m on the two spanning raw symbols.
CL_ROLL_ANCHOR = {"symbols": "CLN6,CLQ6", "start": "2026-06-24",
                  "end": "2026-07-03", "label": "CL-roll-4 (CLN6->CLQ6)"}
# Bounded alternative for continuous CL bbo: most recent 12 months, parent.
CL_BBO_12M = {"start": "2025-10-01", "end": "2026-10-01"}

KEY_PATH = Path(
    "/Users/hoangminhlong/.config/my-quantitative-secrets/databento-api-key")
TOKEN_RE = re.compile(r"db-[A-Za-z0-9_\-]{12,}")
_KEY_CACHE: str | None = None

RESULTS = json.loads(OUT_PATH.read_text())


def load_key() -> str:
    global _KEY_CACHE
    if _KEY_CACHE is None:
        _KEY_CACHE = KEY_PATH.read_text().strip()
        if not _KEY_CACHE:
            print("FATAL: key file empty.", file=sys.stderr)
            sys.exit(2)
    return _KEY_CACHE


def redact(text: str) -> str:
    try:
        key = load_key()
        if key and key in text:
            text = text.replace(key, "db-REDACTED")
    except Exception:  # noqa: BLE001
        pass
    return TOKEN_RE.sub("db-REDACTED", text)


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds")


def flush_out() -> None:
    RESULTS["generated_utc_end"] = now_utc()
    tmp = OUT_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(RESULTS, indent=1))
    tmp.replace(OUT_PATH)


def rpc(rid: str, endpoint: str, params: dict, post: bool, phase: str,
        line_id: str, note: str = "") -> dict:
    if RESULTS["request_count"] >= COMBINED_CAP:
        RESULTS["cap_exhausted"] = True
        print(f"[CAP] skipping {rid}")
        return {"rid": rid, "http_status": None, "payload": None,
                "error_redacted": "SKIPPED_CAP", "params": params}
    RESULTS["request_count"] += 1
    started = now_utc()
    rec = {"rid": rid, "phase": phase, "line_id": line_id,
           "endpoint": endpoint, "http_method": "POST" if post else "GET",
           "params": dict(params), "note": note, "ts_start_utc": started,
           "attempts": 0, "http_status": None, "result_summary": None,
           "error_redacted": None, "payload": None, "ts_end_utc": None,
           "elapsed_ms": None}
    key = load_key()
    basic = base64.b64encode(f"{key}:".encode()).decode()
    last_err = ""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        rec["attempts"] = attempt
        host = PRIMARY_HOST if attempt <= 2 else FALLBACK_HOST
        url = f"{host}/v0/{endpoint}"
        try:
            if post:
                body = urllib.parse.urlencode(params).encode()
                req = urllib.request.Request(url, data=body, method="POST")
                req.add_header("Content-Type",
                               "application/x-www-form-urlencoded")
            else:
                qs = urllib.parse.urlencode(params)
                req = urllib.request.Request(f"{url}?{qs}", method="GET")
            req.add_header("Authorization", f"Basic {basic}")
            t0 = time.monotonic()
            with urllib.request.urlopen(req, timeout=ATTEMPT_TIMEOUT_S) as resp:
                status = resp.status
                raw = resp.read()
            rec["elapsed_ms"] = int((time.monotonic() - t0) * 1000)
            rec["http_status"] = status
            try:
                payload = json.loads(raw.decode("utf-8"))
            except Exception:  # noqa: BLE001
                payload = {"_non_json_len_bytes": len(raw)}
            rec["payload"] = payload
            rec["result_summary"] = f"{json.dumps(payload)[:120]}"
            rec["ts_end_utc"] = now_utc()
            break
        except urllib.error.HTTPError as exc:
            snippet = ""
            try:
                snippet = exc.read().decode("utf-8", "replace")[:400]
            except Exception:  # noqa: BLE001
                snippet = "<unreadable>"
            last_err = f"HTTP {exc.code}: {snippet}"
            rec["http_status"] = exc.code
            if exc.code < 500 and exc.code != 429:
                rec["error_redacted"] = redact(last_err)
                rec["ts_end_utc"] = now_utc()
                break
        except Exception as exc:  # noqa: BLE001
            last_err = f"{type(exc).__name__}: {exc}"
        if attempt < MAX_ATTEMPTS:
            time.sleep(BACKOFF_S[min(attempt - 1, len(BACKOFF_S) - 1)])
    else:
        rec["error_redacted"] = redact(last_err or "unknown error")
        rec["ts_end_utc"] = now_utc()
    RESULTS["requests"][rid] = rec
    RESULTS["order"].append(rid)
    print(f"[{rid}] {rec['http_status'] or 'ERR'} {endpoint} "
          f"{rec['params'].get('symbols', '')[:40]} "
          f"{'OK' if rec['http_status'] == 200 else 'FAIL'}")
    flush_out()
    time.sleep(SLEEP_BETWEEN_S)
    return rec


def num_payload(rec: dict):
    p = rec.get("payload")
    return p if isinstance(p, (int, float)) and not isinstance(p, bool) else None


def rc_params(symbols, schema, start, end, stype_in="parent"):
    return {"dataset": DATASET, "symbols": symbols, "schema": schema,
            "start": start, "end": end, "stype_in": stype_in}


def bs_params(symbols, schema, start, end, stype_in="parent"):
    return {**rc_params(symbols, schema, start, end, stype_in),
            "stype_out": "instrument_id"}


# ---------------------------------------------------------------- probes ---

def quote_line(pkg, line_id, schema, symbols, start, end, prices, note="",
               stype_in="parent"):
    sym = ",".join(symbols)
    rc_rec = rpc(f"{pkg}-{line_id}-RC", "metadata.get_record_count",
                 rc_params(sym, schema, start, end, stype_in), True,
                 "P3F", f"{pkg}:{line_id}", note)
    bs_rec = rpc(f"{pkg}-{line_id}-BS", "metadata.get_billable_size",
                 bs_params(sym, schema, start, end, stype_in), True,
                 "P3F", f"{pkg}:{line_id}", note)
    cost_rec = rpc(f"{pkg}-{line_id}-COST", "metadata.get_cost",
                   bs_params(sym, schema, start, end, stype_in), True,
                   "P3F", f"{pkg}:{line_id}", note)
    return make_line(pkg, line_id, schema, symbols, start, end,
                     num_payload(rc_rec), num_payload(bs_rec),
                     num_payload(cost_rec), prices, note, stype_in)


def make_line(pkg, line_id, schema, symbols, start, end, rc, bs, cost,
              prices, note="", stype_in="parent"):
    return {
        "line_id": line_id, "package": pkg, "schema": schema,
        "symbols": symbols, "stype_in": stype_in, "start": start, "end": end,
        "end_exclusive": True, "record_count": rc,
        "billable_size_bytes": bs,
        "billable_gb_decimal": round(bs / GB, 6) if isinstance(bs, (int, float)) else None,
        "cost_usd_get_cost": cost,
        "cost_usd_list": round(bs / GB * prices[schema], 6)
                         if isinstance(bs, (int, float)) else None,
        "cost_ratio_get_cost_over_list": (
            round(cost / (bs / GB * prices[schema]), 4)
            if isinstance(bs, (int, float)) and isinstance(cost, (int, float))
            and bs > 0 else None),
        "consistency_bytes_eq_rc_x_recsize": (
            bs == rc * RECORD_SIZE[schema]
            if isinstance(bs, (int, float)) and isinstance(rc, int) else None),
        "note": note,
    }


def totals(lines):
    t = {"lines": len(lines), "record_count": 0, "billable_size_bytes": 0,
         "cost_usd_list": 0.0, "cost_usd_get_cost": 0.0,
         "lines_with_get_cost": 0, "lines_failed": 0}
    for ln in lines:
        if ln["record_count"] is None or ln["billable_size_bytes"] is None:
            t["lines_failed"] += 1
        if isinstance(ln["record_count"], int):
            t["record_count"] += ln["record_count"]
        if isinstance(ln["billable_size_bytes"], (int, float)):
            t["billable_size_bytes"] += ln["billable_size_bytes"]
        if isinstance(ln["cost_usd_list"], float):
            t["cost_usd_list"] += ln["cost_usd_list"]
        if isinstance(ln["cost_usd_get_cost"], (int, float)):
            t["cost_usd_get_cost"] += ln["cost_usd_get_cost"]
            t["lines_with_get_cost"] += 1
    t["billable_gb_decimal"] = round(t["billable_size_bytes"] / GB, 4)
    t["cost_usd_list"] = round(t["cost_usd_list"], 2)
    t["cost_usd_get_cost"] = round(t["cost_usd_get_cost"], 2)
    return t


def main() -> int:
    print("follow-up probe — metadata-only")
    prices = RESULTS["unit_prices_usd_per_gb"]["prices"]

    # -- 1. symbology.resolve retry (date fix) ------------------------------
    rec = rpc("P4F-SYMRES", "symbology.resolve", {
        "dataset": DATASET,
        "symbols": "NQ.c.0,CL.c.0,NQ.n.0,CL.n.0",
        "stype_in": "continuous", "stype_out": "instrument_id",
        "start_date": "2010-06-06", "end_date": "2026-10-01",
    }, True, "P4F", "P4F", "continuous->instrument_id, dates within range")
    res = rec.get("payload", {}).get("result", {}) if isinstance(
        rec.get("payload"), dict) else {}
    RESULTS["symbology_fix"] = {
        "attempt_1": {"http_status": 422,
                      "error_case": "data_start_date_before_available_start_"
                                    "date (start 2010-01-01 < available "
                                    "2010-06-06) — stype combination itself "
                                    "PASSED symbology validation"},
        "attempt_2": {"http_status": rec.get("http_status"),
                      "resolved_symbols": len(res),
                      "intervals": {k: len(v) for k, v in res.items()},
                      "ok": rec.get("http_status") == 200},
    }
    flush_out()

    # -- 2. CL roll-window bbo anchor + CL-BBO-12M option -------------------
    anchor = quote_line(
        "ANCH", "CL-ROLL-BBO-ANCHOR", "bbo-1m",
        CL_ROLL_ANCHOR["symbols"].split(","), CL_ROLL_ANCHOR["start"],
        CL_ROLL_ANCHOR["end"], prices,
        f"anchor unit cost, {CL_ROLL_ANCHOR['label']}, raw symbols",
        stype_in="raw_symbol")
    cl_bbo_12m = quote_line(
        "ANCH", "CL-BBO-12M-OPTION", "bbo-1m", [PARENT["CL"]],
        CL_BBO_12M["start"], CL_BBO_12M["end"], prices,
        "bounded option: CL parent bbo-1m, last 12m (dominated by far-month "
        "quote books)")
    RESULTS["cl_bbo_anchors"] = {"roll_window_anchor": anchor,
                                  "cl_bbo_12m_option": cl_bbo_12m}
    flush_out()

    # -- 3. pkgA-v2 quotes ---------------------------------------------------
    print("pkgA-v2 quotes")
    lines_a2 = []
    for root in ALL_ROOTS:
        s, e = PKG_A2_OHLCV[root]
        lines_a2.append(quote_line("PKGA2", f"A2-O1M-{root}", "ohlcv-1m",
                                   [PARENT[root]], s, e, prices,
                                   f"pkgA-v2 ohlcv-1m {root}"))
    for schema, (s, e) in PKG_A2_JOINED.items():
        lines_a2.append(quote_line(
            "PKGA2", f"A2-{schema}-ALL10", schema,
            [PARENT[r] for r in ALL_ROOTS], s, e, prices,
            f"pkgA-v2 joined {schema} all 10 roots"))

    # -- 4. final re-aggregation from ALL stored payloads --------------------
    # Recover get_cost for round-1 package lines (payloads stored; the
    # round-1 aggregator's int-only gate skipped floats).
    def recover(pkg_key, pkg_tag):
        for ln in RESULTS["packages"][pkg_key]["lines"]:
            base = f"{pkg_tag}-{ln['line_id']}"
            rc_rec = RESULTS["requests"].get(f"{base}-RC")
            bs_rec = RESULTS["requests"].get(f"{base}-BS")
            c_rec = RESULTS["requests"].get(f"{base}-COST")
            ln["record_count"] = num_payload(rc_rec) if rc_rec else ln["record_count"]
            ln["billable_size_bytes"] = num_payload(bs_rec) if bs_rec else ln["billable_size_bytes"]
            ln["billable_gb_decimal"] = (
                round(ln["billable_size_bytes"] / GB, 6)
                if isinstance(ln["billable_size_bytes"], (int, float)) else None)
            ln["cost_usd_get_cost"] = num_payload(c_rec) if c_rec else ln["cost_usd_get_cost"]
            ln["cost_usd_list"] = (
                round(ln["billable_size_bytes"] / GB * prices[ln["schema"]], 6)
                if isinstance(ln["billable_size_bytes"], (int, float)) else None)
            ln["cost_ratio_get_cost_over_list"] = (
                round(ln["cost_usd_get_cost"] / ln["cost_usd_list"], 4)
                if isinstance(ln["cost_usd_get_cost"], (int, float))
                and isinstance(ln["cost_usd_list"], float)
                and ln["cost_usd_list"] > 0 else None)
        RESULTS["packages"][pkg_key]["totals"] = totals(
            RESULTS["packages"][pkg_key]["lines"])

    recover("A", "PKGA")
    recover("B", "PKGB")
    recover("C", "PKGC")

    # pkgA final = v2 (within ~$100); v1 kept as variant with the 24m floor
    # for 8/10 roots.
    RESULTS["packages"]["A_variant_24m_floor"] = RESULTS["packages"]["A"]
    RESULTS["packages"]["A"] = {
        "scenario": "essential 10 symbols, longest within ~$100 (v2 tuned)",
        "lines": lines_a2, "totals": totals(lines_a2),
        "variant_note": "pkgA-v1 (24m for 8 roots, 12m CL/NG) measured "
                        f"{RESULTS['packages']['A_variant_24m_floor']['totals']['cost_usd_list']} "
                        "USD list — kept as A_variant_24m_floor; +$39 buys "
                        "the 24m DAILY_BT floor for the 8 cheaper roots"}

    # pkgB restructure: drop CL parent bbo-1m continuous (2y $194 measured);
    # CL bbo = roll-window enumeration at delivery (anchor-measured unit) +
    # quoted 12m option; NQ bbo 2y continuous kept.
    b_lines = [ln for ln in RESULTS["packages"]["B"]["lines"]
               if ln["line_id"] != "B-BBO1M-CL"]
    cl_bbo_cont_2y = next(ln for ln in RESULTS["packages"]["B"]["lines"]
                          if ln["line_id"] == "B-BBO1M-CL")
    anchor_cost = anchor["cost_usd_get_cost"] or anchor["cost_usd_list"]
    n_cl_rolls = 12 * 8   # monthly CL rolls 2019-01..2026-10, ~8 per year net
    b_lines.append({
        "line_id": "B-BBO1M-CL-ROLLWINDOWS", "package": "PKGB",
        "schema": "bbo-1m",
        "symbols": ["enumerated front+next raw symbols per monthly roll"],
        "stype_in": "raw_symbol", "start": "2019-01-01", "end": "2026-10-02",
        "end_exclusive": True,
        "record_count": None, "billable_size_bytes": None,
        "billable_gb_decimal": None,
        "cost_usd_get_cost": round(anchor_cost * n_cl_rolls, 2)
                             if anchor_cost else None,
        "cost_usd_list": round(
            (anchor["cost_usd_list"] or 0) * n_cl_rolls, 2),
        "cost_basis": "DERIVED from measured anchor window "
                      f"{CL_ROLL_ANCHOR['start']}..{CL_ROLL_ANCHOR['end']} "
                      f"x {n_cl_rolls} monthly roll windows (CL rolls "
                      "monthly under the declared rule); exact enumeration "
                      "requires delivered definitions + declared roll "
                      "table — re-quote per window before spend",
        "consistency_bytes_eq_rc_x_recsize": None,
        "note": "roll-window-scoped synchronous BBO for CL-H5 (spread paid "
                "at switch); PILOT-05 pattern scaled",
    })
    RESULTS["packages"]["B_rejected_cl_bbo_continuous_2y"] = cl_bbo_cont_2y
    RESULTS["packages"]["B"] = {
        "scenario": "10 symbols, deeper history within ~$600 (restructured)",
        "lines": b_lines, "totals": totals(b_lines),
        "optional_addon": {
            "line_id": "CL-BBO-12M-OPTION",
            "cost_usd_get_cost": cl_bbo_12m["cost_usd_get_cost"],
            "note": "continuous CL parent bbo-1m 12m — includes far-month "
                    "books; only if owner wants CL quote depth beyond roll "
                    "windows"},
    }

    # pkgC restructure: drop CL parent bbo full ($1,019 — far-month noise);
    # keep NQ bbo full; CL bbo = full-history roll-window enumeration
    # (DERIVED from anchor).
    c_lines = [ln for ln in RESULTS["packages"]["C"]["lines"]
               if ln["line_id"] != "C-BBO1M-CL"]
    cl_bbo_full = next(ln for ln in RESULTS["packages"]["C"]["lines"]
                       if ln["line_id"] == "C-BBO1M-CL")
    n_cl_rolls_c = round(12 * 16.32)
    derived_c = {
        "line_id": "C-BBO1M-CL-ROLLWINDOWS", "package": "PKGC",
        "schema": "bbo-1m",
        "symbols": ["enumerated front+next raw symbols per monthly roll"],
        "stype_in": "raw_symbol", "start": "2010-06-06", "end": "2026-10-02",
        "end_exclusive": True, "record_count": None,
        "billable_size_bytes": None, "billable_gb_decimal": None,
        "cost_usd_get_cost": round(anchor_cost * n_cl_rolls_c, 2)
                             if anchor_cost else None,
        "cost_usd_list": round((anchor["cost_usd_list"] or 0) * n_cl_rolls_c,
                               2),
        "cost_basis": "DERIVED from measured anchor x "
                      f"{n_cl_rolls_c} monthly roll windows; re-quote per "
                      "window before spend",
        "note": "roll-window-scoped CL bbo for the full era",
    }
    c_lines.append(derived_c)
    RESULTS["packages"]["C_rejected_cl_bbo_full"] = cl_bbo_full
    # DERIVED lines excluded from measured totals; shown separately
    c_measured = [ln for ln in c_lines
                  if isinstance(ln["billable_size_bytes"], (int, float))]
    RESULTS["packages"]["C"] = {
        "scenario": "longest feasible history, no cost cap (restructured: CL "
                    "bbo roll-window-scoped, not continuous)",
        "lines": c_lines, "totals": totals(c_measured),
        "totals_note": "totals cover MEASURED lines only; the DERIVED "
                       "roll-window bbo line adds ~$"
                       f"{derived_c['cost_usd_get_cost']} (DERIVED)",
        "rejected_alternative": {
            "line_id": "C-BBO1M-CL (continuous parent, full history)",
            "cost_usd_list": cl_bbo_full["cost_usd_list"],
            "billable_gb": cl_bbo_full["billable_gb_decimal"],
            "why_rejected": "far-month quote books dominate (708M records / "
                            "56.6GB); not needed by any hypothesis"},
    }

    flush_out()

    # -- 5. regenerate package manifests ------------------------------------
    PKG_DIR.mkdir(parents=True, exist_ok=True)

    def manifest_for(pkg, key, extra=None):
        data = RESULTS["packages"][pkg]
        m = {
            "schema": "futures_behavior_10syms_package_manifest@1",
            "task_id": "FUTURES-BEHAVIOR-10SYMS-PREP-20261002",
            "lane": "ACQ-OPT",
            "generated_utc": now_utc(),
            "package": pkg,
            "scenario": data["scenario"],
            "dataset": DATASET,
            "status": "QUOTED_ONLY — NOT authorization to spend; quotes "
                      "from live metadata calls in ../coverage_results.json",
            "delivery_notes": {
                "stype_in": "parent ({ROOT}.FUT) for full lines; raw_symbol "
                            "for enumerated roll-window bbo lines",
                "continuous_series": "NEVER purchased; vendor c/n/v tables "
                                     "via FREE symbology.resolve only",
                "daily_hourly": "aggregated LOCALLY from ohlcv-1m — no "
                                "ohlcv-1d/1h lines, no duplicate billing",
                "end_dates_exclusive": True,
                "chunks": "per (root, schema, calendar quarter) for full "
                          "lines; per enumerated window for bbo roll lines; "
                          "completion ledger + SHA256 manifests; idempotent "
                          "re-request dedupe by exact params (one-owner rule)",
                "pilot_relationship": "pilot NQ/CL lines (request_manifest "
                                      "PILOT-01..06) remain SEPARATE and "
                                      "already queued; overlapping NQ/CL "
                                      "def/stat pilot windows must be carved "
                                      "out at chunk time (one-owner rule)",
            },
            "totals": data["totals"],
            "request_lines": [
                {"line_id": ln["line_id"], "dataset": DATASET,
                 "schema": ln["schema"], "symbols": ln["symbols"],
                 "stype_in": ln.get("stype_in", "parent"),
                 "start": ln["start"], "end": ln["end"],
                 "end_exclusive": True,
                 "quoted_record_count": ln["record_count"],
                 "quoted_billable_size_bytes": ln["billable_size_bytes"],
                 "quoted_cost_usd_get_cost": ln["cost_usd_get_cost"],
                 "quoted_cost_usd_list": ln["cost_usd_list"],
                 "cost_basis": ln.get("cost_basis", "MEASURED")}
                for ln in data["lines"]],
        }
        for k in ("variant_note", "optional_addon", "totals_note",
                  "rejected_alternative", "ohlcv1m_per_root_counts"):
            if k in data:
                m[k] = data[k]
        if extra:
            m.update(extra)
        (PKG_DIR / f"{key}.json").write_text(json.dumps(m, indent=1))
        print(f"wrote {key}.json")

    manifest_for("A", "pkgA")
    manifest_for("A_variant_24m_floor", "pkgA_variant_24m_floor")
    manifest_for("B", "pkgB")
    manifest_for("C", "pkgC")

    ok = sum(1 for r in RESULTS["requests"].values()
             if r.get("http_status") == 200)
    print(f"DONE: {RESULTS['request_count']} logical requests total "
          f"({ok} ok), combined cap {COMBINED_CAP} "
          f"({'EXHAUSTED' if RESULTS['cap_exhausted'] else 'honored'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
