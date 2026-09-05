#!/usr/bin/env python
"""STOCKS-FREE-V7 P0b-2 probe v2: corrected analysis + gate-3 completion.

v1 measured with two script bugs (bar order assumed ascending; search key
mismatch) and unauthoritative CIK memory for the SEC corroboration leg. This
v2 re-analyzes the SAME saved raw bytes with fixed ordering (identical gate
thresholds - no gate is weakened), completes gate 3 with the authoritative
SEC ticker->CIK map, and adds one never-existed-symbol control call to
evidence TD's 404 semantics. Incident INC-1 recorded in the evidence file.
"""
import hashlib
import json
import os
import time
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone, date

REPO_ROOT = "/Users/hoangminhlong/my-quantitative"
WORKTREE = os.path.join(REPO_ROOT, ".worktrees", "stocks-free-v7", "integration")
RAW_DIR = os.path.join(WORKTREE, ".staging_prices_v7", "raw")
CTL_DIR = os.path.join(WORKTREE, "research", "control", "stocks_free_v7_run")
TD_BASE = "https://api.twelvedata.com"
UA_SEC = "my-quantitative-research/1.0 (internal non-commercial research; SEC EDGAR fair use)"

KEY = os.environ.get("TWELVE_DATA_API_KEY")
KEY_CHANNEL = "environment"
if not KEY:
    with open(os.path.join(REPO_ROOT, ".env")) as f:
        for line in f:
            line = line.strip()
            if line.startswith("TWELVE_DATA_API_KEY="):
                KEY = line.split("=", 1)[1].strip().strip('"').strip("'")
    KEY_CHANNEL = "gitignored root .env"

MANIFEST = []
TD_CALLS = 0
_last = [0.0]


def record_raw(name, url, status, body):
    with open(os.path.join(RAW_DIR, name), "wb") as f:
        f.write(body)
    MANIFEST.append({"file": name, "url_sanitized": url.replace(KEY, "REDACTED"),
                     "http": status, "bytes": len(body),
                     "sha256": hashlib.sha256(body).hexdigest()})


def td_get(name, ep, params):
    global TD_CALLS
    p = dict(params)
    p["apikey"] = KEY
    url = f"{TD_BASE}/{ep}?" + urllib.parse.urlencode(p)
    if time.time() - _last[0] < 8.0:
        time.sleep(8.0 - (time.time() - _last[0]))
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA_SEC})
        with urllib.request.urlopen(req, timeout=60) as resp:
            body, status = resp.read(), resp.status
    except urllib.error.HTTPError as e:
        body, status = e.read(), e.code
    _last[0] = time.time()
    TD_CALLS += 1
    record_raw(name, url, status, body)
    try:
        parsed = json.loads(body)
    except Exception:
        return None, status, "NON_JSON_BODY"
    if isinstance(parsed, dict) and parsed.get("status") == "error":
        return parsed, status, parsed.get("message", "error")
    return parsed, status, None


def sec_get(name, url):
    if time.time() - _last[0] < 1.2:
        time.sleep(1.2 - (time.time() - _last[0]))
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA_SEC})
        with urllib.request.urlopen(req, timeout=60) as resp:
            body, status = resp.read(), resp.status
    except urllib.error.HTTPError as e:
        body, status = e.read(), e.code
    record_raw(name, url, status, body)
    try:
        return json.loads(body), status, None
    except Exception:
        return None, status, "NON_JSON_BODY"


def load_raw(name):
    return json.load(open(os.path.join(RAW_DIR, name)))


def asc(bars):
    return sorted(bars, key=lambda b: b["datetime"])


def span(bars):
    return bars[0]["datetime"][:10], bars[-1]["datetime"][:10]


def check_ohlc(bars):
    bad, seen = [], set()
    for b in bars:
        try:
            o, h, l, c = float(b["open"]), float(b["high"]), float(b["low"]), float(b["close"])
            v = float(b.get("volume") or 0)
            d = b["datetime"][:10]
        except (KeyError, TypeError, ValueError):
            bad.append({"datetime": b.get("datetime"), "reason": "MALFORMED"})
            continue
        if d in seen:
            bad.append({"datetime": d, "reason": "DUPLICATE_DATE"})
        seen.add(d)
        if not (h >= l and h >= o and h >= c and l <= o and l <= c and o > 0 and c > 0):
            bad.append({"datetime": d, "reason": "OHLC_INTERVAL"})
        if v < 0:
            bad.append({"datetime": d, "reason": "NEGATIVE_VOLUME"})
    return bad


def main():
    import math
    E = {"schema": "stocks_free_v7_run/p0b2_probe_evidence@2",
         "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
         "key_channel": KEY_CHANNEL,
         "incident": {
             "id": "INC-1",
             "what": "probe v1 computed spans/returns on TD's newest-first bar order and "
                     "parsed symbol_search with the wrong key; gate 2/4 FAIL dispositions in "
                     "v1 were measurement artifacts, and the SEC corroboration leg used "
                     "unauthoritative remembered CIKs (one resolved to an unrelated fund, "
                     "three returned NoSuchKey)",
             "scope": "analysis-layer only; saved raw bytes unaffected; no gate threshold changed; "
                      "verdict v1 (FAIL) was NOT consumed by any decision before this correction",
             "repair": "v2 re-analysis of the same saved bytes with ascending order; authoritative "
                       "SEC company_tickers map; search key fixed; one control call added",
             "prevention": "normalize provider bar order at ingestion before any span/return math; "
                           "CIK resolution only via SEC's authoritative ticker map"},
         }

    # ---- GATE 2 (re-analysis of saved bytes) --------------------------------
    g2 = {"threshold": ">= 7 years daily rows per name; any unexplained miss FAILS",
          "note": "re-analysis of v1 raw bytes (no new API calls); bars normalized ascending",
          "names": {}}
    depth = {}
    for sym in ("CMG", "TJX", "JNJ", "KO", "JPM", "NEE", "BA", "PFE"):
        parsed = load_raw(f"depth_{sym}.json")
        bars = asc(parsed.get("values") or [])
        depth[sym] = bars
        first, last = span(bars)
        days = (datetime.strptime(last, "%Y-%m-%d") -
                datetime.strptime(first, "%Y-%m-%d")).days
        g2["names"][sym] = {"rows": len(bars), "first": first, "last": last,
                            "span_years": round(days / 365.25, 2),
                            "meets_7y": days >= int(7 * 365.25)}
    misses = [s for s, r in g2["names"].items() if not r["meets_7y"]]
    g2["misses"] = misses
    g2["verdict"] = "PASS" if not misses else "FAIL"
    E["gates_gate_2_depth"] = g2

    # ---- GATE 3 (corrected SEC corroboration + control call) ----------------
    tickmap, status, err = sec_get(
        "sec_company_tickers.json", "https://www.sec.gov/files/company_tickers.json")
    tmap = {}
    if isinstance(tickmap, dict):
        for row in tickmap.values():
            tmap[str(row.get("ticker", "")).upper()] = (
                int(row.get("cik_str", 0)), row.get("title", ""))
    targets = {"TWTR": None, "SIVB": None, "FRC": None, "FRCB": None, "TWX": None,
               "SIVBQ": None}
    for t in targets:
        targets[t] = tmap.get(t)
    E["sec_ticker_map_hits"] = {t: v for t, v in targets.items()}

    # control: a symbol that never existed must reproduce the same 404 semantics
    ctrl_parsed, ctrl_status, ctrl_err = td_get(
        "control_ZZZZZZ.json", "time_series",
        {"symbol": "ZZZZZZ", "interval": "1day", "outputsize": "5", "adjust": "none"})

    g3 = {"rule_ex_ante": ("canary set of four documented delisted US filers spanning 2018-2023 "
                           "(all inside S0): ANY name unservable, or servable without the "
                           "delisting tail (last bar > 45 days before the SEC-recorded delisting "
                           "event), FAILS - survivorship-biased panels are never scored"),
          "v1_td_measurements_carried": {
              "TWTR": {"http": 404, "rows": 0,
                       "error": "symbol or figi parameter missing or invalid"},
              "SIVB": {"http": 404, "rows": 0, "same_error": True},
              "SIVBQ": {"http": 404, "rows": 0, "same_error": True},
              "FRC": {"http": 404, "rows": 0, "same_error": True},
              "FRCB": {"http": 200, "rows": 3747, "first": "2010-12-09",
                       "last": "2026-09-03"},
              "TWX": {"http": 404, "rows": 0, "same_error": True},
          },
          "control_never_existed_symbol": {
              "symbol": "ZZZZZZ", "http": ctrl_status, "error": ctrl_err,
              "same_semantics_as_dead_tickers":
                  ctrl_err is not None and "valid symbol" in str(ctrl_err)},
          "search_results_from_v1_bytes": {},
          "sec_corroboration_v2": {}}
    for f_ in ("search_TWTR.json", "search_SIVB.json", "search_FRC.json", "search_TWX.json"):
        try:
            d = load_raw(f_).get("data")
            g3["search_results_from_v1_bytes"][f_] = d[:5] if isinstance(d, list) else d
        except Exception as ex:  # noqa: BLE001
            g3["search_results_from_v1_bytes"][f_] = f"unavailable: {ex}"
    for t in ("TWTR", "SIVB", "FRC", "TWX"):
        hit = targets.get(t)
        if not hit:
            g3["sec_corroboration_v2"][t] = {"ticker_map": None,
                                             "note": "not in SEC ticker map (delisted)"}
            continue
        cik = hit[0]
        sub, status, err = sec_get(
            f"sec_sub2_{t}.json",
            f"https://data.sec.gov/submissions/CIK{cik:010d}.json")
        rec = {"ticker_map": hit, "http": status}
        if isinstance(sub, dict):
            recent = sub.get("filings", {}).get("recent", {})
            pairs = [(f_, d_) for f_, d_ in zip(recent.get("form", []),
                                                recent.get("filingDate", []))
                     if f_.startswith("25") or f_.startswith("15")]
            rec["entity_name"] = sub.get("name")
            rec["delisting_related_recent_forms"] = pairs[:6]
        g3["sec_corroboration_v2"][t] = rec

    unservable = ["TWTR", "SIVB", "TWX"]
    tail_missing = ["FRC"]  # primary ticker unservable; alias-servable noted below
    g3["alias_servable_note"] = ("FRC history IS reachable via OTC alias FRCB "
                                 "(3747 rows, 2010-12-09..2026-09-03 continuous incl. the "
                                 "2023 delisting window); TWTR/SIVB (+SIVBQ)/TWX are "
                                 "unservable by ticker AND alias AND search")
    g3["unservable"] = unservable
    g3["tail_missing"] = tail_missing
    g3["verdict"] = "FAIL"
    E["gates_gate_3_delisted_coverage"] = g3

    # ---- GATE 4 (re-analysis; forward returns on ascending bars) ------------
    g4 = {"note": "event endpoints /dividends /splits are 403 on Basic (V2 DA2); "
                  "authorized cross-check = adjust modes vs SEC-recorded facts",
          "l7": {}}
    l7_specs = [
        ("CMG", "2024-05-01", "2024-09-30", 50.0, "2024-06-26",
         "panel us-gaap:StockholdersEquityNoteStockSplitConversionRatio1 eff=2024-06-26 v=50"),
        ("TJX", "2018-09-01", "2019-01-31", 2.0, "2018-10-22",
         "panel us-gaap:StockholdersEquityNoteStockSplitConversionRatio1 eff=2018-10-22 v=2"),
    ]
    for sym, d1, d2, ratio, eff, ref in l7_specs:
        chk = {"sec_reference": ref, "expected_ratio": ratio, "eff_date": eff}
        for adj in ("none", "all"):
            parsed = load_raw(f"l7_{sym}_{adj}.json")
            bars = asc(parsed.get("values") or [])
            chk[adj] = {"rows": len(bars)}
            if len(bars) >= 2:
                chk[adj]["first"], chk[adj]["last"] = span(bars)
                near = []
                for a, b in zip(bars, bars[1:]):
                    bd = b["datetime"][:10]
                    if abs((datetime.strptime(bd, "%Y-%m-%d") -
                            datetime.strptime(eff, "%Y-%m-%d")).days) <= 5:
                        try:
                            near.append((bd, math.log(float(b["close"]) / float(a["close"]))))
                        except (TypeError, ValueError, ZeroDivisionError):
                            pass
                chk[adj]["extreme_logret_near_eff"] = min(near, key=lambda t: t[1]) if near else None
        expected = -math.log(ratio)
        try:
            raw_lr = chk["none"]["extreme_logret_near_eff"][1]
            adj_lr = chk["all"]["extreme_logret_near_eff"][1]
        except (KeyError, TypeError):
            raw_lr = adj_lr = None
        chk["expected_logret"] = round(expected, 4)
        chk["raw_logret_measured"] = None if raw_lr is None else round(raw_lr, 4)
        chk["adj_logret_measured"] = None if adj_lr is None else round(adj_lr, 4)
        tol = 0.40 * abs(expected) + 0.02
        chk["raw_matches_ratio"] = (raw_lr is not None and abs(raw_lr - expected) <= tol)
        chk["adj_continuous"] = (adj_lr is not None and abs(adj_lr) <= max(tol, 0.15))
        g4["l7"][sym] = chk

    ko_parsed_none = load_raw("l7_KO_none.json")
    ko_parsed_all = load_raw("l7_KO_all.json")
    ko = {"window": ["2023-01-01", "2024-12-31"],
          "sec_source": "data.sec.gov companyconcept us-gaap:CommonStockDividendsPerShareDeclared"}
    cum = {}
    for adj, parsed in (("none", ko_parsed_none), ("all", ko_parsed_all)):
        bars = asc(parsed.get("values") or [])
        ko[adj] = {"rows": len(bars)}
        if len(bars) >= 2:
            ko[adj]["first"], ko[adj]["last"] = span(bars)
            cum[adj] = float(bars[-1]["close"]) / float(bars[0]["close"])
            ko[adj]["first_close"] = bars[0]["close"]
    ko["cum_none"], ko["cum_all"] = cum.get("none"), cum.get("all")
    concept = load_raw("sec_ko_dps.json")
    per_period = {}
    if isinstance(concept, dict):
        for unit in concept.get("units", {}).get("USD", []):
            s10, e10 = unit.get("start", "")[:10], unit.get("end", "")[:10]
            if not ("2023-01-01" <= e10 <= "2024-12-31"):
                continue
            per_period.setdefault((s10, e10), float(unit.get("val", 0)))
    qsum = 0.0
    nq = 0
    for (s10, e10), val in per_period.items():
        try:
            dur = (datetime.strptime(e10, "%Y-%m-%d") -
                   datetime.strptime(s10, "%Y-%m-%d")).days
        except ValueError:
            continue
        if 0 < dur <= 120:
            qsum += val
            nq += 1
    ko["sec_quarterly_dps_facts"] = nq
    ko["sec_dps_window_sum"] = round(qsum, 4)
    if cum.get("none") and cum.get("all"):
        impl = (cum["all"] / cum["none"]) - 1.0
        ko["adjusted_minus_raw_return"] = round(impl, 6)
        first_close = ko["none"].get("first_close")
        if first_close:
            expected_div_yield = qsum / float(first_close)
            ko["sec_dps_over_first_close"] = round(expected_div_yield, 6)
            tol_abs = max(0.4 * expected_div_yield, 0.004)
            ko["direction_ok"] = (impl > 0 and
                                  abs(impl - expected_div_yield) <= tol_abs)
            ko["check"] = f"|impl - SEC DPS/price0| <= max(40%, 0.4pp); impl={impl:.4f} vs exp={expected_div_yield:.4f}"
        else:
            ko["direction_ok"] = False
    else:
        ko["direction_ok"] = False
    g4["ko_dividends"] = ko
    g4_ok = (all(c["raw_matches_ratio"] and c["adj_continuous"]
                 for c in g4["l7"].values()) and ko.get("direction_ok"))
    g4["verdict"] = "PASS" if g4_ok else "FAIL"
    E["gates_gate_4_raw_vs_adjusted"] = g4

    # ---- GATE 5 (re-analysis of saved bytes) --------------------------------
    g5 = {"policy": "decisions read a bar no earlier than its close plus one session "
                    "(binding regardless of provider semantics; asserted bounds never authorized)",
          "semantics_documentation": "TD documents no explicit daily-bar publication-time claim; "
                                     "recorded ASSERTED_UNDOCUMENTED; conservative close+1 session "
                                     "read-lag is the authorized bound",
          "observed": {}}
    for sym in ("CMG", "KO"):
        bars = asc(load_raw(f"latest_{sym}.json").get("values") or [])
        g5["observed"][sym] = {"rows": len(bars),
                               "last_bar": bars[-1]["datetime"][:10] if bars else None}
    ok = any(o.get("last_bar") == "2026-09-04" for o in g5["observed"].values())
    g5["prior_session_bar_available_next_calendar_day"] = ok
    g5["verdict"] = "PASS"
    E["gates_gate_5_availability"] = g5

    # ---- GATE 6 (re-analysis + determinism from saved bytes) ----------------
    g6 = {"series_checked": {}}
    total_viol = 0
    for sym, bars in depth.items():
        bad = check_ohlc(bars)
        total_viol += len(bad)
        g6["series_checked"][sym] = {"rows": len(bars), "violations": len(bad),
                                     "examples": bad[:5]}
    dates = [b["datetime"][:10] for b in depth["CMG"]]
    gaps = [(datetime.strptime(b, "%Y-%m-%d") - datetime.strptime(a, "%Y-%m-%d")).days
            for a, b in zip(dates, dates[1:])]
    g6["cmg_max_bar_gap_days"] = max(gaps) if gaps else None
    def msha(fname):
        m = [r for r in json.load(open(os.path.join(
            CTL_DIR, "p0b2_retrieval_manifest.json")))["rows"] if r["file"] == fname]
        return m[0]["sha256"] if m else None
    g6["determinism_cmg_bytes_equal"] = msha("depth_CMG.json") == msha("depth_recheck_CMG.json")
    g6["determinism_ko_bytes_equal"] = msha("depth_KO.json") == msha("depth_recheck_KO.json")
    det_ok = g6["determinism_cmg_bytes_equal"] and g6["determinism_ko_bytes_equal"]
    cal_ok = g6["cmg_max_bar_gap_days"] is not None and g6["cmg_max_bar_gap_days"] <= 10
    g6["total_violations"] = total_viol
    g6["verdict"] = "PASS" if total_viol == 0 and det_ok and cal_ok else "FAIL"
    E["gates_gate_6_integrity"] = g6

    # ---- disposition ---------------------------------------------------------
    order = [("gate_1_license_scope", E.get("gates_gate_1_verdict", "PASS")),
             ("gate_2_depth", g2["verdict"]),
             ("gate_3_delisted_coverage", g3["verdict"]),
             ("gate_4_raw_vs_adjusted", g4["verdict"]),
             ("gate_5_availability", g5["verdict"]),
             ("gate_6_integrity", g6["verdict"])]
    E["gate_dispositions"] = dict(order)
    E["gate_1_note"] = ("gate 1 evidence stands from v1 (recorded chain + refresh; no "
                        "contradiction); disposition PASS carried")
    first_fail = next((g for g, v in order if v == "FAIL"), None)
    E["first_failing_gate"] = first_fail
    E["probe_verdict"] = "FAIL_CLOSED_BLOCKED_DATA_AUTHORITY" if first_fail else "PROVISIONAL_PASS"
    E["td_calls_v2"] = TD_CALLS
    with open(os.path.join(RAW_DIR, "..", "manifest_v2_append.json"), "w") as f:
        json.dump(MANIFEST, f, indent=1)
    with open(os.path.join(CTL_DIR, "p0b2_probe_evidence_v2.json"), "w") as f:
        json.dump(E, f, indent=1)
    print(json.dumps({"gate_dispositions": E["gate_dispositions"],
                      "first_failing_gate": first_fail,
                      "probe_verdict": E["probe_verdict"],
                      "l7_detail": {s: {k: c.get(k) for k in
                                        ("expected_logret", "raw_logret_measured",
                                         "adj_logret_measured", "raw_matches_ratio",
                                         "adj_continuous")}
                                    for s, c in g4["l7"].items()},
                      "ko": {k: ko.get(k) for k in ("cum_none", "cum_all",
                                                    "adjusted_minus_raw_return",
                                                    "sec_dps_window_sum",
                                                    "sec_dps_over_first_close",
                                                    "direction_ok")},
                      "td_calls_v2": TD_CALLS}, indent=1))


if __name__ == "__main__":
    main()
