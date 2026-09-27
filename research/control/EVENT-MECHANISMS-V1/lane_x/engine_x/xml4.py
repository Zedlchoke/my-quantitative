"""Form-4 XML reader for the A2 event set (roles, prices, original-vintage).

The stream (form4_stream.jsonl) is the index: it supplies (issuer, accession,
acceptance, filing_date, transaction_date, transaction_code).  The stream
carries NO per-share price and NO officer/director role flag (measured, see
lane_s N4_REPORT), so the freeze's A2 definition (value >= $100k of
officer/director open-market buys, original filings only) is resolved by
joining the sha-pinned form4_xml estate on (cik, accession).

Schema note (measured): joint filings list several `reportingOwner` blocks
but the nonDerivativeTable does NOT tag transactions per owner, so the
officer/director gate is applied at FILING level (any listed owner is an
officer/director); see ambiguities.md AMB-05.
"""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field


@dataclass
class Filing4:
    document_type: str | None
    owners: list[dict] = field(default_factory=list)
    transactions: list[dict] = field(default_factory=list)

    @property
    def amended(self) -> bool:
        return bool(self.document_type) and "/A" in self.document_type.upper()

    @property
    def any_officer_or_director(self) -> bool:
        return any(o["director"] == "1" or o["officer"] == "1" for o in self.owners)

    @property
    def officer_director_ciks(self) -> set[str]:
        return {o["cik"] for o in self.owners
                if (o["director"] == "1" or o["officer"] == "1") and o["cik"]}


def _txt(el) -> str | None:
    if el is None:
        return None
    v = el.find("value")
    if v is None or v.text is None:
        return (el.text or "").strip() or None
    return v.text.strip()


def parse_filing4(path: str) -> Filing4:
    root = ET.parse(path).getroot()

    doc = root.find("documentType")
    filing = Filing4(document_type=doc.text.strip() if doc is not None and doc.text else None)

    for ro in root.findall("reportingOwner"):
        rid = ro.find("reportingOwnerId")
        rel = ro.find("reportingOwnerRelationship")
        filing.owners.append({
            "cik": _txt(rid.find("rptOwnerCik")) if rid is not None else None,
            "name": _txt(rid.find("rptOwnerName")) if rid is not None else None,
            "director": _txt(rel.find("isDirector")) if rel is not None else "0",
            "officer": _txt(rel.find("isOfficer")) if rel is not None else "0",
        })

    table = root.find("nonDerivativeTable")
    if table is not None:
        for tx in table.findall("nonDerivativeTransaction"):
            coding = tx.find("transactionCoding")
            tdate = tx.find("transactionDate")
            amounts = tx.find("transactionAmounts")
            shares = amounts.find("transactionShares") if amounts is not None else None
            price = amounts.find("transactionPricePerShare") if amounts is not None else None
            acq = amounts.find("transactionAcquiredDisposedCode") if amounts is not None else None
            filing.transactions.append({
                "code": _txt(coding.find("transactionCode")) if coding is not None else None,
                "date": _txt(tdate) if tdate is not None else None,
                "shares": _txt(shares) if shares is not None else None,
                "price": _txt(price) if price is not None else None,
                "acquired_disposed": _txt(acq) if acq is not None else None,
            })
    return filing


def filing_xml_path(xml_root: str, cik: str, accession: str) -> str | None:
    """Locate the ownership XML inside the staged estate.

    Measured layout: form4_xml/{CIK##########}/{accession-no-dashes}/*.xml
    (the estate flattens the dashed accession `0001179110-19-001172` to
    `000117911019001172`); the dashed variant is tried too.
    """
    for acc in (accession, accession.replace("-", "")):
        d = os.path.join(xml_root, cik, acc)
        if os.path.isdir(d):
            for f in sorted(os.listdir(d)):
                if f.endswith(".xml"):
                    return os.path.join(d, f)
    return None
