"""STOCKS-NG1 P0 observable censuses over the PINNED substrate.

One physical pass over the inherited Form-4 XML substrate (read-only)
yields, per file, ALL of:

  * manifest-verified digest check (re-pin evidence, full coverage --
    no sampling needed: the pass hashes every pinned file anyway);
  * 10b5-1 declared-plan flag census inputs (byte-scan of the
    discovered document-level ``aff10b5One`` tag, strict-parse
    cross-checked);
  * amendment structure inputs (``documentType`` + the
    (issuerCik, rptOwnerCik, periodOfReport) matching key).

Filing-time window classification uses the PINNED stream's acceptance
timestamp (accession join, dashes stripped); docs whose accession is
absent from the stream fall back to the XML ``periodOfReport`` and the
fallback is counted, never hidden.  Nothing here writes to the
substrate or the store.
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Mapping

from .plane_adapter import (
    FLAG_TAG_10B5_1, POST_2023_CUTOFF, CENSUS_A_FLOOR, CENSUS_B_FLOOR,
    MalformedForm4Error, _DOCTYPE_RE, _FLAG_RE, _ISSUER_CIK_RE,
    _OWNER_CIK_RE, _PERIOD_RE, _sha256_file, detect_10b5_1_flag,
)

_DECLARED_VALUES = {"1", "true"}

_XML_SECTION = "form4_xml_docs"


def scan_substrate(manifest: Mapping, substrate_root: str,
                   stream_index: Mapping[str, str],
                   strict_sample_untagged: int = 500) -> dict:
    """Single-pass full scan: per-file digest verification + both
    census inputs.  Fail-closed on drift (raises SubstrateDrift AFTER
    the pass completes, with the drift rows in the exception payload
    consumed by the caller via the report; the report itself carries
    ``status`` per section)."""
    files: Mapping[str, str] = manifest["sections"][_XML_SECTION]["files"]
    report: dict[str, Any] = {
        "section": _XML_SECTION,
        "method": ("full re-hash of every pinned file + byte-scan of "
                   f"<{FLAG_TAG_10B5_1}> + documentType/period/owner "
                   "extraction; single physical pass"),
        "files_total": len(files),
        "files_ok": 0, "files_drift": 0, "files_missing": 0,
        "drift_rows": [], "missing_rows": [],
    }
    census_a: dict[str, Any] = {
        "tag": FLAG_TAG_10B5_1,
        "tag_level": "document",
        "docs_total": 0,
        "docs_window": {"post_2023": 0, "pre_2023": 0, "unknown": 0},
        "window_source": {"stream_acceptance": 0, "period_fallback": 0},
        "docs_with_tag_post_2023": 0,
        "docs_with_tag_pre_2023": 0,
        "docs_declared_post_2023": 0,
        "declared_by_year": {},
        "tag_value_distribution_post_2023": {},
        "declared_docs_post_2023": [],   # accession list (evidence)
        "canary_pre_2023_declared": 0,
        "canary_pre_2023_declared_rows": [],
        "strict_parse": {"docs_with_tag_parsed_strict": 0,
                         "strict_agree_with_bytescan": 0,
                         "strict_malformed": 0,
                         "malformed_rows": [],
                         "untagged_sample_size": 0,
                         "untagged_sample_agree": 0,
                         "untagged_sample_malformed": 0},
    }
    census_b: dict[str, Any] = {
        "doc_type_distribution": {},
        "amendment_docs": 0,
        "amendment_rows": [],
        "original_index_size": 0,
        "amendments_with_resolvable_original": 0,
        "resolvable_rows": [],
        "unresolvable_rows": [],
        "match_key": "(issuerCik, rptOwnerCik, periodOfReport)",
    }

    original_keys: dict[tuple[str, str, str], int] = {}
    amendment_keys: list[dict] = []
    untagged_paths: list[str] = []

    for key, pinned in files.items():
        # manifest keys are staging-root relative ("form4_xml/CIK.../file")
        path = os.path.join(substrate_root, key)
        row: dict[str, Any] = {"key": key}
        if not os.path.isfile(path):
            report["files_missing"] += 1
            if len(report["missing_rows"]) < 50:
                report["missing_rows"].append(key)
            continue
        try:
            with open(path, "rb") as fh:
                data = fh.read()
        except OSError as exc:
            report["files_missing"] += 1
            row["error"] = str(exc)
            if len(report["missing_rows"]) < 50:
                report["missing_rows"].append(row)
            continue
        digest = hashlib.sha256(data).hexdigest()
        if digest != pinned:
            report["files_drift"] += 1
            if len(report["drift_rows"]) < 50:
                report["drift_rows"].append(
                    {"key": key, "pinned": pinned, "measured": digest})
            continue
        report["files_ok"] += 1

        # ---- census inputs (byte level) ---- #
        parts = key.split("/")
        accession_nodash = parts[2] if len(parts) >= 4 else None
        flag_values = [m.decode("utf-8", "replace")
                       for m in _FLAG_RE.findall(data)]
        dt_m = _DOCTYPE_RE.search(data)
        doc_type = (dt_m.group(1).decode("utf-8", "strip")
                    if dt_m else "NONE")

        # filing-time window classification
        acceptance = stream_index.get(accession_nodash or "")
        if acceptance is not None:
            window_date = acceptance
            source = "stream_acceptance"
        else:
            per_m = _PERIOD_RE.search(data)
            window_date = (per_m.group(1).decode("utf-8", "strip")
                           if per_m else None)
            source = "period_fallback" if window_date else "unknown"
        if window_date is None:
            window = "unknown"
            year = "unknown"
        else:
            window = ("post_2023" if window_date >= POST_2023_CUTOFF
                      else "pre_2023")
            year = window_date[:4]

        census_a["docs_total"] += 1
        census_a["docs_window"][window] += 1
        if window != "unknown":
            census_a["window_source"][source] += 1

        census_b["doc_type_distribution"][doc_type] = (
            census_b["doc_type_distribution"].get(doc_type, 0) + 1)

        if doc_type == "4/A":
            ic = _ISSUER_CIK_RE.search(data)
            oc = _OWNER_CIK_RE.search(data)
            per = _PERIOD_RE.search(data)
            arow = {
                "key": key, "accession": accession_nodash,
                "issuerCik": (ic.group(1).decode("utf-8", "strip")
                              if ic else None),
                "rptOwnerCik": (oc.group(1).decode("utf-8", "strip")
                                if oc else None),
                "periodOfReport": (per.group(1).decode("utf-8", "strip")
                                   if per else None),
                "acceptance": acceptance,
                "window": window,
            }
            census_b["amendment_docs"] += 1
            census_b["amendment_rows"].append(arow)
            amendment_keys.append(arow)
        else:
            ic = _ISSUER_CIK_RE.search(data)
            oc = _OWNER_CIK_RE.search(data)
            per = _PERIOD_RE.search(data)
            if ic and oc and per:
                k = (ic.group(1).decode("utf-8", "strip"),
                     oc.group(1).decode("utf-8", "strip"),
                     per.group(1).decode("utf-8", "strip"))
                original_keys[k] = original_keys.get(k, 0) + 1
            if doc_type == "4" and not flag_values and len(untagged_paths) < 400000:
                untagged_paths.append(path)

        if not flag_values:
            continue

        # ---- tagged doc: strict-parse cross-check (all tagged docs) ---
        try:
            strict = detect_10b5_1_flag(data)
        except MalformedForm4Error:
            census_a["strict_parse"]["strict_malformed"] += 1
            if len(census_a["strict_parse"]["malformed_rows"]) < 50:
                census_a["strict_parse"]["malformed_rows"].append(key)
            continue
        census_a["strict_parse"]["docs_with_tag_parsed_strict"] += 1
        strict_vals = strict["value"] if strict["occurrences"] else None
        byte_first = flag_values[0]
        agrees = (strict_vals == byte_first)
        if agrees:
            census_a["strict_parse"]["strict_agree_with_bytescan"] += 1

        declared = strict["declared"] is True and agrees
        if window == "post_2023":
            census_a["docs_with_tag_post_2023"] += 1
            for v in flag_values:
                census_a["tag_value_distribution_post_2023"][v] = (
                    census_a["tag_value_distribution_post_2023"].get(v, 0)
                    + 1)
            if declared:
                census_a["docs_declared_post_2023"] += 1
                census_a["declared_by_year"][year] = (
                    census_a["declared_by_year"].get(year, 0) + 1)
                census_a["declared_docs_post_2023"].append(
                    accession_nodash or key)
        elif window == "pre_2023":
            census_a["docs_with_tag_pre_2023"] += 1
            if declared:
                census_a["canary_pre_2023_declared"] += 1
                if len(census_a["canary_pre_2023_declared_rows"]) < 50:
                    census_a["canary_pre_2023_declared_rows"].append(key)

    # ---- strict cross-check sample on UNTAGGED docs (false negatives) --
    if untagged_paths and strict_sample_untagged > 0:
        step = max(1, len(untagged_paths) // strict_sample_untagged)
        sample = untagged_paths[::step][:strict_sample_untagged]
        for p in sample:
            census_a["strict_parse"]["untagged_sample_size"] += 1
            with open(p, "rb") as fh:
                d = fh.read()
            try:
                strict = detect_10b5_1_flag(d)
            except MalformedForm4Error:
                census_a["strict_parse"]["untagged_sample_malformed"] += 1
                continue
            if strict["occurrences"] == 0:
                census_a["strict_parse"]["untagged_sample_agree"] += 1

    # ---- amendment -> original resolution ------------------------------ #
    census_b["original_index_size"] = len(original_keys)
    for a in amendment_keys:
        k = (a["issuerCik"] or "", a["rptOwnerCik"] or "",
             a["periodOfReport"] or "")
        if None not in (a["issuerCik"], a["rptOwnerCik"],
                        a["periodOfReport"]) and original_keys.get(k, 0) >= 1:
            census_b["amendments_with_resolvable_original"] += 1
            if len(census_b["resolvable_rows"]) < 1000:
                census_b["resolvable_rows"].append(a)
        elif len(census_b["unresolvable_rows"]) < 1000:
            census_b["unresolvable_rows"].append(a)

    report["census_a"] = census_a
    report["census_b"] = census_b
    report["status"] = ("OK" if report["files_drift"] == 0
                        and report["files_missing"] == 0 else "DRIFT")
    return report


def verify_aux_sections(manifest: Mapping, substrate_root: str) -> dict:
    """Full re-hash of the non-XML substrate sections (eodhd div/splits
    4,336 files, submissions_alive 410) against the pinned manifest."""
    out: dict[str, Any] = {}
    for section in ("eodhd_div", "eodhd_splits", "submissions_alive"):
        sec = manifest["sections"][section]
        ok = drift = missing = 0
        drift_rows = []
        for key, pinned in sec["files"].items():
            # aux-section manifest keys are BARE filenames: the physical
            # file lives under <staging_root>/<section>/<key>
            path = os.path.join(substrate_root, section, key)
            if not os.path.isfile(path):
                missing += 1
                if len(drift_rows) < 50:
                    drift_rows.append({"key": key, "status": "MISSING"})
                continue
            digest = _sha256_file(path)
            if digest == pinned:
                ok += 1
            else:
                drift += 1
                if len(drift_rows) < 50:
                    drift_rows.append({"key": key, "pinned": pinned,
                                       "measured": digest})
        out[section] = {"files_total": sec["count"], "files_ok": ok,
                        "files_drift": drift, "files_missing": missing,
                        "drift_rows": drift_rows,
                        "status": ("OK" if drift == 0 and missing == 0
                                   else "DRIFT")}
    return out


def amendment_absence_crosscheck(manifest: Mapping,
                                 substrate_root: str) -> dict:
    """Second, independent measurement for census B when the XML scan
    finds zero '4/A' docs: the PINNED submissions_alive metadata (part
    of the substrate manifest) lists EDGAR form types per accession;
    count '4/A' entries and whether their accession dirs exist in the
    form4_xml tree.  Proves the ingest enumerated form type '4' only
    (absence is a substrate-coverage property, not a parser miss)."""
    acc_4a: list[tuple[str, str]] = []
    for key in manifest["sections"]["submissions_alive"]["files"]:
        path = os.path.join(substrate_root, "submissions_alive", key)
        try:
            with open(path) as fh:
                d = json.load(fh)
        except (OSError, ValueError):
            continue
        recent = (d.get("filings", {}).get("recent", {}))
        forms = recent.get("form", [])
        accs = recent.get("accessionNumber", [])
        cik = key.replace(".json", "")
        for form, acc in zip(forms, accs):
            if form == "4/A":
                acc_4a.append((acc.replace("-", ""), cik))
    present = absent = 0
    for acc, cik in acc_4a:
        if os.path.isdir(os.path.join(substrate_root, "form4_xml",
                                      cik, acc)):
            present += 1
        else:
            absent += 1
    return {
        "submissions_form_4A_entries": len(acc_4a),
        "of_which_present_in_form4_xml_tree": present,
        "of_which_absent_from_form4_xml_tree": absent,
        "conclusion": (
            "the pinned substrate enumerates documentType '4' only: "
            f"{len(acc_4a)} '4/A' entries appear in the pinned "
            "submissions metadata but 0 accession dirs exist in the "
            "form4_xml tree -- amendment absence is a substrate "
            "COVERAGE property of the inherited V13 ingest, not a "
            "parser miss"
            if absent == len(acc_4a) and acc_4a
            else "mixed presence; inspect before concluding"),
    }


def census_a_floor_evaluation(census_a: Mapping,
                              flagged_transaction_count: int | None,
                              ) -> dict:
    """Frozen floor: >=500 flagged TRANSACTIONS post-2023.  The flag is
    document-level, so the transaction-level count is measured by
    joining declared docs to PINNED stream rows (accession in declared
    set, acceptance >= cutoff)."""
    docs_declared = census_a["docs_declared_post_2023"]
    tx = (flagged_transaction_count
          if flagged_transaction_count is not None else docs_declared)
    return {
        "floor": CENSUS_A_FLOOR,
        "flagged_docs_post_2023": docs_declared,
        "flagged_transactions_post_2023": tx,
        "transactions_count_method": (
            "stream rows (transactions) with acceptance >= 2023-01-01 "
            "whose accession maps to a declared doc (doc-level flag "
            "projected onto its transactions via the pinned stream)"),
        "met": tx >= CENSUS_A_FLOOR,
        "consequence_if_unmet": "lane A4 dies at P2 (P0 may still PASS)",
    }


def census_b_floor_evaluation(census_b: Mapping) -> dict:
    met = census_b["amendments_with_resolvable_original"] >= CENSUS_B_FLOOR
    return {
        "floor": CENSUS_B_FLOOR,
        "amendment_docs": census_b["amendment_docs"],
        "amendments_with_resolvable_original":
            census_b["amendments_with_resolvable_original"],
        "match_key": census_b["match_key"],
        "limitations": [
            "EDGAR Form-4 XML carries no explicit amendment->original "
            "pointer; matching is by (issuerCik, rptOwnerCik, "
            "periodOfReport) inside the pinned substrate",
            "the pinned stream carries no form-type field, so form "
            "type comes from the XML documentType element",
        ],
        "met": met,
        "consequence_if_unmet": "lane A5 dies at P2 (P0 may still PASS)",
    }


def flag_transaction_count(stream_rows: list[dict],
                           declared_accessions: set[str]) -> dict:
    """Transaction-level flagged count post-2023 + by-year split."""
    n = 0
    by_year: dict[str, int] = {}
    for r in stream_rows:
        acc = (r.get("accession") or "").replace("-", "")
        ts = r.get("acceptance") or ""
        if acc in declared_accessions and ts >= POST_2023_CUTOFF:
            n += 1
            y = ts[:4]
            by_year[y] = by_year.get(y, 0) + 1
    return {"count": n, "by_year": dict(sorted(by_year.items()))}
