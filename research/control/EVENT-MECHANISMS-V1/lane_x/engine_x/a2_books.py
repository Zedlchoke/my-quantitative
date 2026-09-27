"""EMV1-A2 anchor book: insider-flow acceptance-clock, hold 10, long-only.

Event definition (G3 + R2-3): issuer-days with net open-market BUY value
>= $100,000, transactionCode 'P', officers/directors, ORIGINAL filings
only.  The stream is the index; the XML estate supplies document type,
roles and per-share price (see xml4.py + ambiguities.md AMB-02..AMB-06).

Substrate coverage measured 2018-01-02 .. 2025-05-23 -> F1 population 0
(the known F1=0 substrate fact; census disclosed, nothing inferred).
"""

from __future__ import annotations

import json
from collections import defaultdict

from .divsplits import ExDateIndex
from .panel import PanelStore
from .sequencing import build_event_record
from .tzlaw import clock_facts
from .xml4 import filing_xml_path, parse_filing4

BUY_VALUE_FLOOR = 100_000.0
A2_HOLD = 10


def _to_float(s: str | None) -> float | None:
    if s is None or s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def build_a2_events(stream_path: str, xml_root: str, cik_to_ticker: dict[str, str],
                    panels: PanelStore) -> tuple[dict[tuple[str, str], dict], dict, list[dict]]:
    """Collapse qualifying stream+XML rows into issuer-day events.

    Returns (events keyed (cik, day), census, drop_log).
    """
    census = {"stream_rows": 0, "p_rows": 0, "accessions_joined": 0,
              "amendment_accessions": 0, "non_od_accessions": 0,
              "xml_missing": 0, "xml_unparseable": 0,
              "rows_no_price": 0, "rows_no_bar_for_price_fallback": 0,
              "issuer_days": 0, "events_above_floor": 0}
    drop_log: list[dict] = []

    # index stream rows by (cik, accession)
    by_accession: dict[tuple[str, str], list[dict]] = defaultdict(list)
    with open(stream_path) as fh:
        for line in fh:
            r = json.loads(line)
            census["stream_rows"] += 1
            if r["transaction_code"] != "P":
                continue
            census["p_rows"] += 1
            by_accession[(r["cik"], r["accession"])].append(r)

    # issuer-day aggregation
    day_rows: dict[tuple[str, str], dict] = {}
    events: dict[tuple[str, str], dict] = {}

    for (cik, accession), rows in sorted(by_accession.items()):
        path = filing_xml_path(xml_root, cik, accession)
        if path is None:
            census["xml_missing"] += 1
            drop_log.append({"cik": cik, "accession": accession, "reason": "A2_XML_MISSING"})
            continue
        try:
            filing = parse_filing4(path)
        except ET.ParseError:
            census["xml_unparseable"] += 1
            drop_log.append({"cik": cik, "accession": accession, "reason": "A2_XML_UNPARSEABLE"})
            continue
        census["accessions_joined"] += 1
        if filing.amended:
            census["amendment_accessions"] += 1
            drop_log.append({"cik": cik, "accession": accession, "reason": "A2_AMENDMENT"})
            continue
        if not filing.any_officer_or_director:
            census["non_od_accessions"] += 1
            drop_log.append({"cik": cik, "accession": accession, "reason": "A2_NOT_OFFICER_DIRECTOR"})
            continue

        od_ciks = filing.officer_director_ciks
        earliest = min(r["acceptance"] for r in rows)
        for tx in filing.transactions:
            if tx["code"] != "P":
                continue
            day = tx["date"] or rows[0]["transaction_date"]
            shares = _to_float(tx["shares"])
            if shares is None:
                continue
            xml_price = _to_float(tx["price"])
            if xml_price is None or xml_price <= 0:
                # fallback: raw close of last session on-or-before the
                # transaction date (AMB-06)
                census["rows_no_price"] += 1
                ticker = cik_to_ticker.get(cik)
                price = panels.raw_close_on_or_before(ticker, day) if ticker else None
                if price is None:
                    census["rows_no_bar_for_price_fallback"] += 1
                    drop_log.append({"cik": cik, "accession": accession,
                                     "reason": "A2_NO_PRICE_FALLBACK_BAR", "day": day})
                    continue
            else:
                price = xml_price
            key = (cik, day)
            agg = day_rows.get(key)
            if agg is None:
                agg = {"value": 0.0, "earliest_acceptance": earliest,
                       "accessions": set(), "insider_ciks": set()}
                day_rows[key] = agg
            agg["value"] += shares * price
            agg["accessions"].add(accession)
            agg["earliest_acceptance"] = min(agg["earliest_acceptance"], earliest)
            agg["insider_ciks"] |= od_ciks

    for (cik, day), agg in day_rows.items():
        census["issuer_days"] += 1
        if agg["value"] < BUY_VALUE_FLOOR:
            continue
        census["events_above_floor"] += 1
        events[(cik, day)] = {
            "cik": cik,
            "transaction_date": day,
            "acceptance_utc": agg["earliest_acceptance"],
            "buy_value": agg["value"],
            "cluster_size": len(agg["insider_ciks"]),
            "n_accessions": len(agg["accessions"]),
        }
    return events, census, drop_log


def build_a2_book(stream_path: str, xml_root: str, n4_path: str,
                  panels: PanelStore, exdates: ExDateIndex) -> tuple[dict, dict, list[dict], list[dict]]:
    cik_to_ticker: dict[str, str] = {}
    for line in open(n4_path):
        r = json.loads(line)
        cik_to_ticker[r["cik"]] = r["ticker"]

    events, census, drop_log = build_a2_events(stream_path, xml_root, cik_to_ticker, panels)

    records, excluded = [], []
    arm_census = {"candidates": 0, "booked": 0, "excluded": 0, "dropped": 0,
                  "excluded_by_reason": {}, "delisting_exits": 0,
                  "booked_by_fold": {}, "booked_by_stratum": {},
                  "excluded_by_fold": {}, "weekend_bucket_candidates": 0}

    for (cik, day) in sorted(events):
        ev = events[(cik, day)]
        ticker = cik_to_ticker.get(cik)
        if ticker is None or ticker == "SPY":
            arm_census["dropped"] += 1
            continue
        arm_census["candidates"] += 1
        facts = clock_facts(ev["acceptance_utc"])
        fold = fold_of(facts.et_date)
        res = build_event_record(
            panel=panels.get(ticker),
            exdates=exdates,
            acceptance_utc=ev["acceptance_utc"],
            hold=A2_HOLD,
            direction_rule="a2",
        )
        if res.status == "DROPPED":
            arm_census["dropped"] += 1
            continue
        if res.status == "EXCLUDED":
            arm_census["excluded"] += 1
            _bump(arm_census["excluded_by_reason"], res.reason)
            _bump_fold(arm_census["excluded_by_fold"], fold)
            excluded.append({"event_id": f"EMV1-A2:{cik}:{day}", "cik": cik,
                             "ticker": ticker, "acceptance_utc": ev["acceptance_utc"],
                             "reason": res.reason, "fold": fold, "ca_detail": res.ca_detail})
            continue
        arm_census["booked"] += 1
        _bump_fold(arm_census["booked_by_fold"], fold)
        _bump(arm_census["booked_by_stratum"], facts.stratum)
        if res.delisting_exit:
            arm_census["delisting_exits"] += 1
        records.append({
            "event_id": f"EMV1-A2:{cik}:{day}",
            "cik": cik,
            "ticker": ticker,
            "form": "4",
            "acceptance_utc": ev["acceptance_utc"],
            "stratum": facts.stratum,
            "direction_session": res.direction_session,
            "direction": res.direction,
            "entry_session": res.entry_session,
            "entry_price": res.entry_price,
            "exit_session": res.exit_session,
            "exit_price": res.exit_price,
            "exclusions_applied": res.notes,
            "delisting_exit": res.delisting_exit,
            "arm": "A2_ANCHOR",
            "hold_sessions": A2_HOLD,
            "fold": fold,
            "weekend_bucket": facts.weekend_bucket,
            "et_offset_hours": facts.et_offset_hours,
            "transaction_date": day,
            "buy_value": round(ev["buy_value"], 2),
            "cluster_size": ev["cluster_size"],
        })

    records.sort(key=lambda r: r["event_id"])
    arm_census["event_set"] = census
    return records, arm_census, excluded, drop_log


def fold_of(et_date: str) -> str:
    if et_date < "2018-01-01":
        return "F1"
    if et_date < "2021-01-01":
        return "F2"
    if et_date < "2023-01-01":
        return "F3"
    return "F4"


def _bump(d: dict, k: str) -> None:
    d[k] = d.get(k, 0) + 1


def _bump_fold(d: dict, fold: str) -> None:
    d[fold] = d.get(fold, 0) + 1
