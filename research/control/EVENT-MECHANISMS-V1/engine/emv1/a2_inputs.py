"""E3 inputs — form4_stream A2 event construction, measured from bytes.

Schema measurements recorded here (all from bytes, see REPORT):
- stream row keys (exactly 11, every row): cik, accession, acceptance,
  filing_date, transaction_date, transaction_code, direction, shares,
  owner_cik, owner_name, table.
- NO form-type / amendment marker in the stream -> amendments are
  distinguished by joining `accession` to the EDGAR submissions shards
  (`form` field, staged by lane S): rows whose form == '4/A' are amendments
  and are DROPPED (G1 court). Rows whose accession is absent from the shards
  fail closed as AMENDMENT_UNKNOWN (dropped + counted).
- NO officer/director role field in the stream -> roles are read from the
  staged Form-4 XML estate (reportingOwnerRelationship: isDirector /
  isOfficer / isTenPercentOwner / officerTitle). officer/director law:
  isDirector OR isOfficer required; role missing -> ROLE_UNKNOWN (dropped +
  counted).
- NO price/value in the stream -> buy value = transactionShares x
  transactionPricePerShare read from the same XML; missing price ->
  UNPRICED (dropped + counted).
- NO declared-plan flag in the stream -> measured <aff10b5One> in the XML
  (present only on post-2023-schema forms); used for the E5 cadence proxy.
"""
from __future__ import annotations

import json
import os
import xml.etree.ElementTree as ET
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from . import config as C
from .loaders import iter_jsonl


def stream_p_rows() -> List[dict]:
    out = []
    for r in iter_jsonl(C.STREAM_PATH):
        if r.get("transaction_code") == C.A2_CODE:
            out.append(r)
    return out


def load_accession_form_map(ciks: List[str]) -> Dict[str, str]:
    """accession -> form from the staged submissions shards (recent + pages)."""
    m: Dict[str, str] = {}
    for cik in ciks:
        d = os.path.join(C.SUBMISSIONS_DIR, f"{cik}.json")
        if not os.path.exists(d):
            continue
        j = json.load(open(d))
        rec = j.get("filings", {}).get("recent", {})
        for acc, form in zip(rec.get("accessionNumber", []), rec.get("form", [])):
            m[acc] = form
        for pg in j.get("filings", {}).get("files", []):
            pd = os.path.join(C.SUBMISSIONS_DIR, pg.get("name", ""))
            if os.path.exists(pd):
                pj = json.load(open(pd))
                for acc, form in zip(pj.get("accessionNumber", []),
                                     pj.get("form", [])):
                    m[acc] = form
    return m


def _txt(el, path):
    x = el.find(path)
    return x.text if x is not None and x.text else None


def parse_form4_xml(path: str) -> Optional[dict]:
    """Extract (per reporting owner) roles + per-transaction (shares, price,
    10b5-1 flag) from one staged Form-4 XML. Measured field names:
    reportingOwner/reportingOwnerRelationship/{isDirector,isOfficer,
    isTenPercentOwner,officerTitle}; nonDerivativeTable/transaction/
    {transactionShares/value, transactionPricePerShare/value, footnotes};
    aff10b5One (declared 10b5-1 plan flag, 0/1).
    """
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return None
    owners = []
    for ro in root.iter("reportingOwner"):
        rel = ro.find("reportingOwnerRelationship")
        owners.append({
            "isDirector": _txt(rel, "isDirector") if rel is not None else None,
            "isOfficer": _txt(rel, "isOfficer") if rel is not None else None,
            "isTenPercentOwner": _txt(rel, "isTenPercentOwner") if rel is not None else None,
            "officerTitle": _txt(rel, "officerTitle") if rel is not None else None,
        })
    plan_flag = None
    for el in root.iter("aff10b5One"):
        plan_flag = (el.text or "").strip()
        break
    txns = []
    # Measured: transactions live under <nonDerivativeTransaction> (some
    # vintages also use <transaction>); iterate both.
    for tag in ("nonDerivativeTransaction", "transaction"):
        for t in root.iter(tag):
            shares = price = None
            # Measured: amounts nest under <transactionAmounts> in X030x
            # vintages; use descendant search for robustness across vintages.
            sh = t.find(".//transactionShares/value")
            if sh is not None and sh.text:
                shares = sh.text
            ps = t.find(".//transactionPricePerShare/value")
            if ps is not None and ps.text:
                price = ps.text
            txns.append({"shares": shares, "price": price})
        if txns:
            break
    return {"owners": owners, "plan_flag": plan_flag, "txns": txns}


def load_xml_by_accession(accessions: List[str], ciks_by_accession: Dict[str, str]) -> Dict[str, Optional[dict]]:
    """Targeted (light) parse: only the accessions needed, indexed by the
    CIK/accession directory layout of the staged XML estate. Measured: the
    XML directory name is the accession with dashes stripped."""
    out: Dict[str, Optional[dict]] = {}
    for acc in accessions:
        cik = ciks_by_accession.get(acc)
        acc_dir = acc.replace("-", "")
        d = os.path.join(C.XML_DIR, cik or "", acc_dir)
        got = None
        if os.path.isdir(d):
            for fn in sorted(os.listdir(d)):
                if fn.endswith(".xml"):
                    got = parse_form4_xml(os.path.join(d, fn))
                    if got is not None:
                        break
        out[acc] = got
    return out


def _is_true(v) -> bool:
    # Measured: older Form-4 XML encodes booleans as '1'/'0'; newer as
    # 'true'/'false'. Accept both.
    return (v or "").strip().lower() in ("1", "true")


def build_a2_issuer_days(
    p_rows: List[dict],
    acc_form: Dict[str, str],
    xml: Dict[str, Optional[dict]],
    cohort_ciks: set,
) -> Tuple[List[dict], dict]:
    """Aggregate qualifying P rows into issuer-day candidate events.

    Qualification per freeze: original filing (form '4'), officer/director
    role, priced open-market purchase >= aggregation into net buy value.
    Every drop is counted with a reason (no silent drops).
    """
    counts: Dict[str, int] = defaultdict(int)
    days: Dict[Tuple[str, str], dict] = {}
    for r in p_rows:
        cik = r["cik"]
        if cik not in cohort_ciks:
            counts["OUT_OF_COHORT"] += 1
            continue
        acc = r["accession"]
        form = acc_form.get(acc)
        if form is None:
            counts["AMENDMENT_UNKNOWN_FAIL_CLOSED"] += 1
            continue
        if form != "4":
            counts["AMENDMENT_DROPPED"] += 1
            continue
        x = xml.get(acc)
        if x is None:
            counts["XML_MISSING_OR_UNPARSEABLE"] += 1
            continue
        if not x["owners"]:
            counts["ROLE_UNKNOWN"] += 1
            continue
        officer_director = any(
            _is_true(o.get("isOfficer")) or _is_true(o.get("isDirector"))
            for o in x["owners"]
        )
        if not officer_director:
            counts["ROLE_NOT_OFFICER_DIRECTOR"] += 1
            continue  # 10%-owner-only filers are NOT officer/director events
        priced = [
            (float(t["shares"]), float(t["price"]))
            for t in x["txns"]
            if t["shares"] and t["price"]
        ]
        if not priced:
            counts["UNPRICED"] += 1
            continue
        value = sum(s * p for s, p in priced)
        plan_flagged = x["plan_flag"] == "1"
        day = r["acceptance"][:10]  # issuer-day = UTC acceptance date (recorded)
        key = (cik, day)
        d = days.setdefault(key, {
            "cik": cik, "day": day, "buy_value_usd": 0.0,
            "owners": set(), "accessions": set(),
            "earliest_acceptance": r["acceptance"], "filing_date": r["filing_date"],
            "plan_flagged_accessions": 0,
            "p_accessions": 0,
        })
        d["buy_value_usd"] += value
        owner = r.get("owner_cik") or r.get("owner_name") or "UNKNOWN"
        d["owners"].add(owner)
        d["accessions"].add(acc)
        d["p_accessions"] += 1
        if plan_flagged:
            d["plan_flagged_accessions"] += 1
        if r["acceptance"] < d["earliest_acceptance"]:
            d["earliest_acceptance"] = r["acceptance"]
        if r["filing_date"] < d["filing_date"]:
            d["filing_date"] = r["filing_date"]
    events = []
    for key in sorted(days):
        d = days[key]
        d["n_insiders"] = len(d["owners"])
        d["cluster"] = d["n_insiders"] >= C.A2_CLUSTER_MIN_INSIDERS
        d["accessions"] = sorted(d["accessions"])
        d.pop("owners", None)
        if d["buy_value_usd"] >= C.A2_MIN_BUY_VALUE_USD:
            events.append(d)
        else:
            counts["BELOW_VALUE_FLOOR"] += 1
    stats = {"p_rows": len(p_rows), "issuer_day_events": len(events),
             "drops": dict(counts)}
    return events, stats
