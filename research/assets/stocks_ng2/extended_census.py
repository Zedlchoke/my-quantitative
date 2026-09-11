"""STOCKS-NG2 P0: amendment census on the EXTENDED substrate.

The extended substrate = pinned V13 originals (345,150 type-4 docs,
read-only inherited pin, full re-hash as S1 re-pin evidence) + the
targeted 4/A re-ingest (data_raw/form4a, manifest-digested).

Law (ng1 census B, unchanged): an amendment is a doc whose XML
``documentType`` == '4/A'; the original is resolved by the match key
(issuerCik, rptOwnerCik, periodOfReport) against the ORIGINALS index
built from every non-amendment doc of the pinned substrate (EDGAR
Form-4 XML carries no explicit amendment->original pointer).  Frozen
floor: >= 200 amendments with resolvable original (plan section 4).

The originals pass reuses the ng1 regexes so the extraction semantics
are identical to the recorded ng1 census (original_index_size 342,801
at ng1 time must reproduce exactly -- the substrate is pinned).
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Mapping

import xml.etree.ElementTree as ET

from research.assets.stocks_ng1.plane_adapter import (
    _DOCTYPE_RE, _ISSUER_CIK_RE, _OWNER_CIK_RE, _PERIOD_RE,
)

CENSUS_B_FLOOR = 200          # frozen in PLAN_stocks_ng2.md section 4
_XML_SECTION = "form4_xml_docs"


class MalformedForm4Error(Exception):
    """Strict Form-4 XML parse failed: fail-closed, never guessed."""


# --------------------------------------------------------------------- #
# originals pass: full re-hash + original-key index (single pass)
# --------------------------------------------------------------------- #

def scan_originals(manifest: Mapping, substrate_root: str) -> dict:
    """One physical pass over every pinned form4_xml file: manifest
    digest verification (S1 re-pin evidence, FULL coverage) + build of
    the originals match-key index.  Also records the documentType
    distribution (must be {'4': 345150} on the pinned pin)."""
    files: Mapping[str, str] = manifest["sections"][_XML_SECTION]["files"]
    report: dict[str, Any] = {
        "section": _XML_SECTION,
        "method": ("FULL re-hash of every pinned file + "
                   "documentType/period/owner extraction; single "
                   "physical pass (identical extraction semantics to "
                   "the recorded ng1 census)"),
        "files_total": len(files),
        "files_ok": 0, "files_drift": 0, "files_missing": 0,
        "drift_rows": [], "missing_rows": [],
        "doc_type_distribution": {},
        "original_index_size": 0,
        "_original_index": {},      # stripped before dumping
    }
    original_index: dict[tuple[str, str, str], int] = {}
    for key, pinned in files.items():
        path = os.path.join(substrate_root, key)
        if not os.path.isfile(path):
            report["files_missing"] += 1
            if len(report["missing_rows"]) < 50:
                report["missing_rows"].append(key)
            continue
        with open(path, "rb") as fh:
            data = fh.read()
        digest = hashlib.sha256(data).hexdigest()
        if digest != pinned:
            report["files_drift"] += 1
            if len(report["drift_rows"]) < 50:
                report["drift_rows"].append(
                    {"key": key, "pinned": pinned, "measured": digest})
            continue
        report["files_ok"] += 1

        dt_m = _DOCTYPE_RE.search(data)
        doc_type = (dt_m.group(1).decode("utf-8", "strip")
                    if dt_m else "NONE")
        report["doc_type_distribution"][doc_type] = (
            report["doc_type_distribution"].get(doc_type, 0) + 1)
        if doc_type == "4/A":
            # the pinned tree enumerates '4' only (ng1 census); a 4/A
            # here would contradict the recorded substrate -- recorded,
            # never edited
            continue
        ic = _ISSUER_CIK_RE.search(data)
        oc = _OWNER_CIK_RE.search(data)
        per = _PERIOD_RE.search(data)
        if ic and oc and per:
            k = (ic.group(1).decode("utf-8", "strip"),
                 oc.group(1).decode("utf-8", "strip"),
                 per.group(1).decode("utf-8", "strip"))
            original_index[k] = original_index.get(k, 0) + 1
    report["original_index_size"] = len(original_index)
    report["_original_index"] = {
        "|".join(k): v for k, v in original_index.items()}
    report["status"] = ("OK" if report["files_drift"] == 0
                        and report["files_missing"] == 0 else "DRIFT")
    return report


# --------------------------------------------------------------------- #
# 4/A parsing (strict) + amendment census
# --------------------------------------------------------------------- #

def parse_form4a(xml_bytes: bytes) -> dict:
    """Strict parse of a Form 4/A primary doc.  Returns documentType,
    issuerCik, rptOwnerCik, periodOfReport (stripped strings; None when
    the element is absent).  Malformed XML raises MalformedForm4Error
    (fail-closed: the doc is NOT counted as an amendment)."""
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise MalformedForm4Error(f"Form 4/A XML parse failed: {exc}") from exc

    def _text(tag: str) -> str | None:
        el = root.find(f".//{tag}")
        if el is None:
            return None
        t = (el.text or "").strip()
        return t or None

    return {
        "documentType": _text("documentType"),
        "issuerCik": _text("issuerCik"),
        "rptOwnerCik": _text("rptOwnerCik"),
        "periodOfReport": _text("periodOfReport"),
    }


def well_formed_sample(doc_paths: list[str], sample_size: int = 5) -> dict:
    """Deterministic 5-doc well-formedness sample (indices 0, n/4, n/2,
    3n/4, n-1 of the sorted doc list; deduplicated when n < 5)."""
    paths = sorted(doc_paths)
    if not paths:
        return {"sample_size": 0, "all_well_formed": False,
                "reason": "no docs to sample"}
    n = len(paths)
    idx = sorted({0, n // 4, n // 2, (3 * n) // 4, n - 1})
    rows = []
    for i in idx:
        p = paths[i]
        with open(p, "rb") as fh:
            data = fh.read()
        try:
            parse_form4a(data)
            rows.append({"path": p, "well_formed": True})
        except MalformedForm4Error as exc:
            rows.append({"path": p, "well_formed": False, "error": str(exc)})
    return {"sample_size": len(rows),
            "all_well_formed": all(r["well_formed"] for r in rows),
            "rows": rows,
            "selection_rule": ("sorted doc list indices "
                               f"{idx} of n={n}")}


def census_amendments(form4a_root: str, state_path: str,
                      original_index: Mapping[str, int]) -> dict:
    """Amendment census over the re-ingested 4/A tree, matched against
    the originals index (keys joined with '|').  Honest accounting:

      fetched_accessions       - terminal OK rows in fetch state
      fetched_non_xml          - OK rows whose primary doc is not XML
                                 (vintage .txt rows; NOT amendments)
      amendment_docs           - parseable XML docs w/ documentType '4/A'
      malformed_xml_docs       - parse failures (fail-closed, listed)
      unexpected_doc_types     - parseable XML whose documentType != 4/A
                                 (listed, NOT counted as amendments)
      amendments_with_resolvable_original - match key present in the
                                 pinned originals index
    """
    from research.assets.stocks_ng2.form4a_ingest import load_state
    state = load_state(state_path)
    ok_rows = [r for r in state.values() if r["status"] == "OK"]
    census: dict[str, Any] = {
        "match_key": "(issuerCik, rptOwnerCik, periodOfReport)",
        "fetched_accessions": len(ok_rows),
        "fetched_non_xml": 0,
        "amendment_docs": 0,
        "malformed_xml_docs": 0,
        "malformed_rows": [],
        "unexpected_doc_types": {},
        "unexpected_rows": [],
        "amendment_rows": [],
        "amendments_with_resolvable_original": 0,
        "resolvable_rows": [],
        "unresolvable_rows": [],
        "resolvable_by_year": {},
    }
    for r in sorted(ok_rows, key=lambda x: (x["cik"],
                                            x["accession_nodash"])):
        if not r.get("primary_file") or not r.get("primary_is_xml"):
            census["fetched_non_xml"] += 1
            continue
        path = os.path.join(form4a_root, r["cik"], r["accession_nodash"],
                            r["primary_file"])
        if not os.path.isfile(path):
            # state says OK but file gone: fail-closed incident row
            census["malformed_xml_docs"] += 1
            if len(census["malformed_rows"]) < 50:
                census["malformed_rows"].append(
                    {"path": path, "error": "state-OK file missing"})
            continue
        with open(path, "rb") as fh:
            data = fh.read()
        try:
            parsed = parse_form4a(data)
        except MalformedForm4Error as exc:
            census["malformed_xml_docs"] += 1
            if len(census["malformed_rows"]) < 50:
                census["malformed_rows"].append(
                    {"path": path, "error": str(exc)})
            continue
        if parsed["documentType"] != "4/A":
            census["unexpected_doc_types"][parsed["documentType"]] = (
                census["unexpected_doc_types"].get(
                    parsed["documentType"], 0) + 1)
            if len(census["unexpected_rows"]) < 50:
                census["unexpected_rows"].append(
                    {"path": path,
                     "documentType": parsed["documentType"]})
            continue
        census["amendment_docs"] += 1
        year = (r.get("filing_date") or "")[:4] or "unknown"
        arow = {"cik": r["cik"], "accession": r["accession"],
                "accession_nodash": r["accession_nodash"],
                "filing_date": r.get("filing_date"),
                "primary_file": r["primary_file"],
                "issuerCik": parsed["issuerCik"],
                "rptOwnerCik": parsed["rptOwnerCik"],
                "periodOfReport": parsed["periodOfReport"]}
        census["amendment_rows"].append(arow)
        key = "|".join((parsed["issuerCik"] or "",
                        parsed["rptOwnerCik"] or "",
                        parsed["periodOfReport"] or ""))
        if (None not in (parsed["issuerCik"], parsed["rptOwnerCik"],
                         parsed["periodOfReport"])
                and original_index.get(key, 0) >= 1):
            census["amendments_with_resolvable_original"] += 1
            census["resolvable_by_year"][year] = (
                census["resolvable_by_year"].get(year, 0) + 1)
            if len(census["resolvable_rows"]) < 1000:
                census["resolvable_rows"].append(arow)
        else:
            if len(census["unresolvable_rows"]) < 1000:
                census["unresolvable_rows"].append(arow)
    return census


def census_b_floor_evaluation(census: Mapping) -> dict:
    met = (census["amendments_with_resolvable_original"]
           >= CENSUS_B_FLOOR)
    return {
        "floor": CENSUS_B_FLOOR,
        "amendment_docs": census["amendment_docs"],
        "amendments_with_resolvable_original":
            census["amendments_with_resolvable_original"],
        "match_key": census["match_key"],
        "limitations": [
            "EDGAR Form-4 XML carries no explicit amendment->original "
            "pointer; matching is by (issuerCik, rptOwnerCik, "
            "periodOfReport) against the pinned originals index",
            "originals index built from the pinned 345,150-doc V13 "
            "substrate only; an amendment whose original was filed "
            "outside the pinned cohort is unresolvable-by-construction",
            "fetched_non_xml vintage rows (EDGAR .txt primary docs) "
            "are fetched and recorded but are not parseable amendments",
        ],
        "met": met,
        "consequence_if_unmet": "lane A4 dies at P2 (P0 may still PASS)",
    }
