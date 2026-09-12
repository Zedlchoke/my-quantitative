"""COMMODITIES-NG1: EODHD commodity-linked ETP EOD census + pair join.

Source: EODHD family-1 EOD (owner key, programmatic ``.env`` load
inside the P0 runner only -- never echoed, V13 law).  RAW close is the
primary series; ``adjusted_close`` from the same payload is a
corp-actions cross-check (V8 convention), never the traded price.

Frozen ETP-leg qualification rule (plan section 3, floor condition
(b)): ``rows >= 2000`` AND ``first_eod <= as_of - 8 years`` AND
``last_eod >= as_of - 10 days`` (alive/tradeable at measurement).
"""

from __future__ import annotations

import csv
import io
from datetime import date, datetime, timedelta

SCHEMA = "commodities_ng1/etp_census@1"

#: Frozen ETP-leg qualification rule.
ETP_MIN_ROWS = 2000
ETP_MIN_FIRST_YEARS = 8
ETP_ALIVE_WINDOW_DAYS = 10

CSV_HEADER = [
    "date", "open", "high", "low", "close", "adj_close", "volume",
]


class EtpCensusError(Exception):
    """Fail-closed ETP census failure."""


class EtpLookupRefused(Exception):
    """Never-existed ticker / empty payload: refused (canary semantics)."""


def normalize_eod_payload(payload: list, symbol: str) -> list[dict]:
    """Normalize one EODHD /eod JSON payload (list of bar dicts).

    A non-list payload (vendor error detail, e.g. ``{"detail": "symbol
    not found"}`` for a never-existed ticker) is a REFUSAL, never a
    parseable surface; so is an empty list."""
    if not isinstance(payload, list):
        raise EtpLookupRefused(
            f"{symbol}: vendor returned no bar surface "
            f"({type(payload).__name__} payload) - never-existed-ticker / "
            "no-data semantics; refused")
    if not payload:
        raise EtpLookupRefused(
            f"{symbol}: empty EOD payload (never-existed-ticker canary "
            "semantics or delisted channel gap); refused")
    rows = []
    for bar in payload:
        try:
            rows.append({
                "date": datetime.strptime(bar["date"], "%Y-%m-%d").date(),
                "open": float(bar["open"]),
                "high": float(bar["high"]),
                "low": float(bar["low"]),
                "close": float(bar["close"]),
                "adj_close": float(bar["adjusted_close"]),
                "volume": int(bar["volume"] or 0),
            })
        except (KeyError, ValueError, TypeError) as exc:
            raise EtpCensusError(
                f"{symbol}: malformed bar {bar!r} ({exc}); fail closed"
            ) from exc
    rows.sort(key=lambda r: r["date"])
    return rows


def rows_to_csv(rows: list[dict]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(CSV_HEADER)
    for r in rows:
        writer.writerow([
            r["date"].isoformat(), r["open"], r["high"], r["low"],
            r["close"], r["adj_close"], r["volume"]])
    return buf.getvalue()


def csv_to_rows(text: str, symbol: str = "?") -> list[dict]:
    reader = csv.DictReader(io.StringIO(text))
    missing = set(CSV_HEADER) - set(reader.fieldnames or [])
    if missing:
        raise EtpCensusError(
            f"{symbol}: normalized CSV missing {sorted(missing)}")
    rows = []
    for raw in reader:
        rows.append({
            "date": datetime.strptime(raw["date"], "%Y-%m-%d").date(),
            "open": float(raw["open"]), "high": float(raw["high"]),
            "low": float(raw["low"]), "close": float(raw["close"]),
            "adj_close": float(raw["adj_close"]),
            "volume": int(raw["volume"]),
        })
    return rows


def census_etp(rows: list[dict], symbol: str, as_of: date) -> dict:
    """Frozen coverage census for ONE ETP leg (alive at ``as_of``)."""
    if not rows:
        raise EtpLookupRefused(f"{symbol}: empty row set")
    dates = [r["date"] for r in rows]
    if dates != sorted(dates):
        raise EtpCensusError(f"{symbol}: rows not date-sorted")
    if len(set(dates)) != len(dates):
        raise EtpCensusError(f"{symbol}: duplicate dates")
    first, last = dates[0], dates[-1]
    min_first = as_of - timedelta(days=round(ETP_MIN_FIRST_YEARS * 365.25))
    alive_cutoff = as_of - timedelta(days=ETP_ALIVE_WINDOW_DAYS)
    eligible = (len(rows) >= ETP_MIN_ROWS and first <= min_first
                and last >= alive_cutoff)
    reasons = []
    if len(rows) < ETP_MIN_ROWS:
        reasons.append(f"rows {len(rows)} < {ETP_MIN_ROWS}")
    if first > min_first:
        reasons.append(
            f"first_eod {first.isoformat()} > {min_first.isoformat()} "
            "(< 8y history)")
    if last < alive_cutoff:
        reasons.append(
            f"last_eod {last.isoformat()} < {alive_cutoff.isoformat()} "
            "(stale: not alive/tradeable at measurement)")
    divergence = [r["date"] for r in rows
                  if abs(r["close"] - r["adj_close"]) > 1e-9]
    return {
        "symbol": symbol,
        "first_eod": first.isoformat(),
        "last_eod": last.isoformat(),
        "rows": len(rows),
        "span_years": round((last - first).days / 365.25, 4),
        "corp_actions_cross_check": {
            "convention": "RAW close primary; adjusted_close cross-check only",
            "divergence_events": len(divergence),
            "first_divergence": (divergence[0].isoformat()
                                 if divergence else None),
            "last_divergence": (divergence[-1].isoformat()
                                if divergence else None),
        },
        "etp_leg_eligible": eligible,
        "ineligible_reasons": reasons,
        "rule": {
            "min_rows": ETP_MIN_ROWS,
            "min_first_years": ETP_MIN_FIRST_YEARS,
            "alive_window_days": ETP_ALIVE_WINDOW_DAYS,
            "as_of": as_of.isoformat(),
        },
    }


# -- market-pair join --------------------------------------------------------- #

def join_pairs(pairs: list[dict], cot_censuses: dict, etp_censuses: dict
               ) -> list[dict]:
    """Evaluate the declared market-pair list against measured censuses.

    ``pairs`` entries: {cot_market_code, cot_display, etp, purity,
    declared_basis}.  Only measured evidence decides eligibility; a
    declared pair with a missing leg is recorded ineligible with the
    reason (never dropped, never fabricated).
    """
    out = []
    for p in pairs:
        code, sym = p["cot_market_code"], p["etp"]
        cot = cot_censuses.get(code)
        etp = etp_censuses.get(sym)
        cot_ok = bool(cot and cot["cot_leg_eligible"])
        etp_ok = bool(etp and etp["etp_leg_eligible"])
        if cot_ok and etp_ok:
            reason = "both legs eligible"
        elif not cot_ok:
            reason = "cot leg: " + (
                str(cot["ineligible_reasons"]) if cot
                else "market code absent from measured archive")
        else:
            reason = "etp leg: " + (
                str(etp["ineligible_reasons"]) if etp
                else "symbol not measured/absent")
        out.append({
            **p,
            "cot_first": cot["first_report"] if cot else None,
            "cot_last": cot["last_report"] if cot else None,
            "cot_weeks": cot["weeks"] if cot else 0,
            "cot_span_years": cot["span_years"] if cot else None,
            "etp_first": etp["first_eod"] if etp else None,
            "etp_last": etp["last_eod"] if etp else None,
            "etp_rows": etp["rows"] if etp else 0,
            "etp_span_years": etp["span_years"] if etp else None,
            "qualifying": cot_ok and etp_ok,
            "reason": reason,
        })
    return out
