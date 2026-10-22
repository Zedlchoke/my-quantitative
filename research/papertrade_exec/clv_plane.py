"""CLV measurement plane (PAPERDESK UPGRADE V2 U6) — MEASURE ONLY.

Closing-line-value measurement: near kickoff, snapshot (a) the Pinnacle
close (vig stripped) and (b) the Polymarket near-close price for EVERY
match that has a FORECAST row — placed bet or not — one sidecar record
per match per day under

    real:    <data_root>/ops/clv/
    sandbox: <data_root>/sandbox/ops/clv/     (sandbox passed explicitly)

This plane changes NO decision: it writes sidecar records and reports
only. The integrator wires record_closing_quotes into the ops tick near
kickoff (see the U5/U6 handover for the exact call signature).

Injected seams (never real network in tests):
  odds_fetch(sport_key, match_ids) -> payload, either
      {match_id: {leg: decimal_odds}}  (already normalized by a wrapper)
    or a raw The-Odds-API-style list of events (parsed here: bookmaker
    'pinnacle', market 'h2h', outcomes matched on home/away full names,
    DRAW by the literal name). ANY exception (incl. the quota guard's
    ProviderQuotaSkip) -> pin_status NO_RUN_PINNACLE with the reason —
    never invented, never retried inside this function.
  pm_fetch(home, away) -> {leg: price} | None. Price is a probability
    (0..1, Polymarket cents/100). None/empty -> pm_status NO_RUN_PM.

No-vig law: p_leg = (1/odds_leg) / sum_legs(1/odds). For 2-way
1/1.5 + 1/2.8 = 1.0238095... -> normalized {0.651163, 0.348837}.

CLV law (placed bets only, DECISION BET_PAPER with odds_frozen):
  clv_pin = entry_decimal / pin_close_decimal(chosen_leg) - 1
  clv_pm  = entry_decimal * pm_close_prob(chosen_leg) - 1
            (pm decimal close = 1/price; same formula expressed once)
Decision drift (all forecast matches): forecast-time MARKET_QUOTE odds
vs pin close on each common leg, averaged per match.
"""
from __future__ import annotations

import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "clv_close@1"


def _norm(s: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "", str(s).casefold())


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def clv_sidecar_dir(data_root: Path, sandbox: bool) -> Path:
    """U6.1: real plane <data_root>/ops/clv/ — sandbox
    <data_root>/sandbox/ops/clv/ (sandbox passed explicitly)."""
    return Path(data_root) / ("sandbox/ops/clv" if sandbox else "ops/clv")


def no_vig_probabilities(odds: dict) -> dict | None:
    """Strip the vig: p = 1/odds per leg, divided by the sum of legs.
    Degenerate input (<=1 usable leg, odds <= 1) returns None."""
    inv: dict = {}
    for leg, o in (odds or {}).items():
        try:
            f = float(o)
        except (TypeError, ValueError):
            continue
        if f > 1.0:
            inv[str(leg)] = 1.0 / f
    if len(inv) < 2:
        return None
    s = sum(inv.values())
    return {leg: v / s for leg, v in inv.items()}


def _pin_close_from_raw(payload, match_id: str, home: str, away: str):
    """Parse a payload into {leg: decimal} for one match. Accepts the
    normalized dict shape or a raw The-Odds-API-style event list.
    Returns (odds_dict | None, reason)."""
    if isinstance(payload, dict):
        odds = payload.get(str(match_id))
        if isinstance(odds, dict) and odds:
            return {str(k): float(v) for k, v in odds.items()
                    if v}, None
        return None, f"match {match_id} absent from normalized odds payload"
    if not isinstance(payload, list):
        return None, f"odds payload shape {type(payload).__name__} unparsable"
    for ev in payload:
        if str(ev.get("id")) != str(match_id):
            continue
        best: dict = {}
        for bk in ev.get("bookmakers") or []:
            if str(bk.get("key") or "") != "pinnacle":
                continue
            for mkt in bk.get("markets") or []:
                if str(mkt.get("key") or "") != "h2h":
                    continue
                for o in mkt.get("outcomes") or []:
                    nm, pr = _norm(o.get("name")), o.get("price")
                    if pr is None:
                        continue
                    if nm == _norm(home):
                        best["HOME"] = float(pr)
                    elif nm == _norm(away):
                        best["AWAY"] = float(pr)
                    elif nm == "draw":
                        best["DRAW"] = float(pr)
            if best:
                break                       # first pinnacle market wins
        if best:
            return best, None
        return None, (f"match {match_id} on the board but no parsable "
                      f"pinnacle h2h outcomes (home/away name match)")
    return None, f"match {match_id} absent from odds payload"


def _index_ledger(ledger_rows) -> tuple[dict, dict, dict]:
    """Last FORECAST / BET_PAPER DECISION / latest MARKET_QUOTE per
    match_id (B1R twins: the last row of each kind is the operative one)."""
    forecasts: dict = {}
    bets: dict = {}
    quotes: dict = {}
    for r in ledger_rows or []:
        mid = str(r.get("match_id") or "")
        if not mid:
            continue
        t = r.get("type")
        if t == "FORECAST":
            forecasts[mid] = r
        elif t == "DECISION" and r.get("status") == "BET_PAPER" \
                and r.get("odds_frozen") and r.get("chosen_leg"):
            bets[mid] = r
        elif t == "MARKET_QUOTE" and r.get("odds"):
            prev = quotes.get(mid)
            if prev is None or str(r.get("fetch_ts_utc") or "") >= \
                    str(prev.get("fetch_ts_utc") or ""):
                quotes[mid] = r
    return forecasts, bets, quotes


def record_closing_quotes(*, ledger_rows, data_root, sandbox: bool,
                          odds_fetch, pm_fetch, now_utc: datetime,
                          sport_keys: dict | None = None) -> dict:
    """U6.2: stateless closer — for EVERY match with a FORECAST row,
    sample the Pinnacle close and the PM near-close ONCE and write one
    sidecar record per match per day (filename keyed
    clv_{league}_{match_id}_{YYYYMMDD}.json; a same-day re-call
    overwrites — 'one record per match per day').

    MEASURE ONLY: writes <clv_dir>/*.json and returns a summary; changes
    no decision, no ledger row, no gate.
    """
    data_root = Path(data_root)
    out_dir = clv_sidecar_dir(data_root, sandbox)
    out_dir.mkdir(parents=True, exist_ok=True)
    from research.papertrade_exec.execute import DEFAULT_SPORT_KEYS
    from research.papertrade_exec.quota_guard import ProviderQuotaSkip
    keys = dict(DEFAULT_SPORT_KEYS)
    keys.update(sport_keys or {})
    if now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=timezone.utc)   # naive == UTC
    now_utc = now_utc.astimezone(timezone.utc)
    now_iso = _iso(now_utc)
    day = now_utc.strftime("%Y%m%d")

    forecasts, bets, quotes = _index_ledger(ledger_rows)
    # group by sport_key so odds_fetch is called ONCE per league with all
    # of the day's match_ids (respect the caller's quota/scheduling —
    # this function is stateless and makes exactly that one call).
    by_key: dict = {}
    for mid, r in forecasts.items():
        skey = keys.get(r.get("league")) or str(r.get("league") or "")
        by_key.setdefault(skey, []).append((mid, r))

    summary = {"sampled_at_utc": now_iso, "day": day, "records": 0,
               "pin_ok": 0, "pm_ok": 0, "no_run_pin": 0, "no_run_pm": 0,
               "sidecar_dir": str(out_dir)}
    pin_payloads: dict = {}
    for skey, members in sorted(by_key.items()):
        mids = [mid for mid, _r in members]
        try:
            payload = odds_fetch(skey, mids)
            for mid, _r in members:
                pin_payloads[mid] = (payload, None)
        except Exception as e:
            kind = "quota skip" if isinstance(e, ProviderQuotaSkip) \
                else "error"
            reason = f"{kind}: {type(e).__name__}: {e}"[:300]
            for mid, _r in members:
                pin_payloads[mid] = (None, reason)

    for mid, r in sorted(forecasts.items()):
        league = r.get("league") or ""
        home, away = str(r.get("home") or ""), str(r.get("away") or "")
        rec = {
            "schema": SCHEMA, "type": "CLV_CLOSE",
            "league": league, "match_id": mid, "home": home,
            "away": away,
            "kickoff_utc": r.get("kickoff_utc") or "",
            "sampled_at_utc": now_iso, "sampled_day": day,
            "legs": sorted((r.get("p") or {}).keys()),
            "pin_close": None, "pin_novig_prob": None,
            "pm_close": None,
            "pin_status": "OK", "pm_status": "OK",
            "why_pin": None, "why_pm": None,
            "entry": None, "forecast_quote": None}

        payload, why = pin_payloads.get(mid, (None, "no odds_fetch result"))
        if payload is not None:
            odds, pwhy = _pin_close_from_raw(payload, mid, home, away)
            if odds is None:
                why = pwhy
            else:
                nv = no_vig_probabilities(odds)
                if nv is None:
                    why = f"degenerate odds {odds}"
                else:
                    rec["pin_close"] = {k: round(v, 6)
                                        for k, v in sorted(odds.items())}
                    rec["pin_novig_prob"] = {k: round(v, 6)
                                             for k, v in sorted(nv.items())}
        if rec["pin_close"] is None:
            rec["pin_status"] = "NO_RUN_PINNACLE"
            rec["why_pin"] = why
            summary["no_run_pin"] += 1
        else:
            summary["pin_ok"] += 1

        try:
            pm = pm_fetch(home, away)
        except Exception as e:
            pm, rec["why_pm"] = None, \
                f"error: {type(e).__name__}: {e}"[:300]
        if isinstance(pm, dict) and pm:
            rec["pm_close"] = {str(k): float(v) for k, v in pm.items()}
            summary["pm_ok"] += 1
        else:
            if pm is not None and not rec["why_pm"]:
                rec["why_pm"] = "empty pm payload"
            elif pm is None and not rec["why_pm"]:
                rec["why_pm"] = "pm_fetch returned None"
            rec["pm_status"] = "NO_RUN_PM"
            summary["no_run_pm"] += 1

        bet = bets.get(mid)
        if bet:
            leg = str(bet.get("chosen_leg"))
            entry_odds = (bet.get("odds_frozen") or {}).get(leg)
            rec["entry"] = {
                "chosen_leg": leg,
                "entry_decimal": float(entry_odds)
                if entry_odds is not None else None,
                "stake_cents": bet.get("stake_cents") or 0}
        q = quotes.get(mid)
        if q:
            rec["forecast_quote"] = {
                "odds": {str(k): float(v)
                         for k, v in (q.get("odds") or {}).items()},
                "fetch_ts_utc": q.get("fetch_ts_utc") or ""}

        rec["status"] = ("OK" if rec["pin_status"] == "OK"
                         and rec["pm_status"] == "OK"
                         else (rec["pin_status"]
                               if rec["pin_status"] != "OK"
                               else rec["pm_status"]))
        safe_mid = "".join(c if c.isalnum() else "-" for c in mid)
        safe_league = "".join(c if c.isalnum() else "-" for c in league)
        fpath = out_dir / f"clv_{safe_league}_{safe_mid}_{day}.json"
        fpath.write_text(json.dumps(rec, indent=1, sort_keys=True))
        summary["records"] += 1
    return summary


def _mean_med(xs):
    if not xs:
        return {"n": 0, "mean": None, "median": None}
    return {"n": len(xs),
            "mean": round(statistics.fmean(xs), 6),
            "median": round(statistics.median(xs), 6)}


def _clv_of(rec: dict, ref: str) -> float | None:
    """clv on the chosen leg. ref 'pin': entry/close-1 on decimal odds;
    ref 'pm': entry_decimal * pm_prob - 1 (= entry/pm_decimal - 1)."""
    entry = rec.get("entry") or {}
    leg, ed = entry.get("chosen_leg"), entry.get("entry_decimal")
    if ed is None or not leg:
        return None
    if ref == "pin":
        close = (rec.get("pin_close") or {}).get(leg)
        if not close:
            return None
        return ed / close - 1.0
    p = (rec.get("pm_close") or {}).get(leg)
    if p is None or float(p) <= 0:
        return None
    return ed * float(p) - 1.0


def _drift_of(rec: dict) -> float | None:
    fq = (rec.get("forecast_quote") or {}).get("odds") or {}
    close = rec.get("pin_close") or {}
    common = [leg for leg in fq if leg in close]
    if not common:
        return None
    ds = [float(fq[leg]) / float(close[leg]) - 1.0 for leg in common]
    return statistics.fmean(ds)


def clv_report(sidecar_dir) -> dict:
    """U6.3: aggregate the sidecar records. Per league: placed-bet CLV on
    BOTH references (mean/median/n), decision drift (forecast-time quote
    vs close), and month buckets (by sampled_at_utc). Read-only."""
    sidecar_dir = Path(sidecar_dir)
    recs = []
    for p in sorted(sidecar_dir.glob("clv_*.json")):
        try:
            r = json.loads(p.read_text())
        except (OSError, ValueError):
            continue
        if r.get("schema") == SCHEMA:
            recs.append(r)
    rep: dict = {"schema": "clv_report@1",
                 "records": len(recs),
                 "by_status": {},
                 "leagues": {}}
    for r in recs:
        rep["by_status"][r.get("status")] = \
            rep["by_status"].get(r.get("status"), 0) + 1
    for league in sorted({r.get("league") or "" for r in recs}):
        rows = [r for r in recs if (r.get("league") or "") == league]
        clv_pin = [v for v in (_clv_of(r, "pin") for r in rows)
                   if v is not None]
        clv_pm = [v for v in (_clv_of(r, "pm") for r in rows)
                  if v is not None]
        drift = [v for v in (_drift_of(r) for r in rows) if v is not None]
        months: dict = {}
        for r in rows:
            m = str(r.get("sampled_at_utc") or "")[:7]
            if not m:
                continue
            b = months.setdefault(m, {"n": 0, "clv_pin": [], "clv_pm": [],
                                      "drift": []})
            b["n"] += 1
            for key, ref in (("clv_pin", "pin"), ("clv_pm", "pm")):
                v = _clv_of(r, ref)
                if v is not None:
                    b[key].append(v)
            d = _drift_of(r)
            if d is not None:
                b["drift"].append(d)
        rep["leagues"][league] = {
            "n_records": len(rows),
            "placed_bets": sum(1 for r in rows if r.get("entry")),
            "clv_pin": _mean_med(clv_pin),
            "clv_pm": _mean_med(clv_pm),
            "decision_drift": _mean_med(drift),
            "months": {m: {
                "n": b["n"],
                "clv_pin": _mean_med(b["clv_pin"]),
                "clv_pm": _mean_med(b["clv_pm"]),
                "decision_drift": _mean_med(b["drift"]),
            } for m, b in sorted(months.items())}}
    return rep
