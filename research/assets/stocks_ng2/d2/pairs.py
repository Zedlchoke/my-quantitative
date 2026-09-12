"""STOCKS-NG2 D2 pair construction: original<->4/A resolution machinery.

Rebuilds the census-B pairing (match key (issuerCik, rptOwnerCik,
periodOfReport) against the pinned originals index, inherited from the
census machinery VERBATIM) and extends it to the D2 measurement pair
set with the acceptance_row_rule and value conventions the proposals
froze ex ante:

  stream index       one pass over the pinned form4_stream: per accession
                     the MIN row acceptance stamp (deterministic rule;
                     measured: 271 of 285,082 accessions carry >1 distinct
                     acceptance across their rows) and the doc-level sum
                     of D-coded nonDerivative shares.
  originals index    one regex pass over every pinned type-4 file
                     (345,150; same extraction semantics as the recorded
                     censuses; P0's same-commit full re-hash is the digest
                     evidence - not repeated here).
  tie rule (FROZEN)  several originals may share a match key: pick the
                     original with the EARLIEST stream acceptance; tie
                     broken by the lexicographically smallest accession.
                     Chosen deterministically before any rho existed
                     (no construction shopping); multiplicity disclosed.
  acceptance rule    BOTH stamps must be acceptance-classified:
                     originals restricted to stream_acceptance accessions
                     (period_fallback docs excluded fail-closed, counted);
                     amendments restricted to the pinned submissions
                     acceptanceDateTime CROSS-CHECKED against the
                     re-ingest accession index.json last-modified of the
                     primary doc (ET-naive date within [UTC date - 1,
                     UTC date] - ET is UTC-4/-5); a pair failing either
                     side is excluded fail-closed to the defect counts.
  cohort rule        a pair enters only if its ISSUER (doc issuerCik per
                     the frozen identity rule) is a cohort member;
                     non-member pairs counted excluded-with-reason.
  value convention   V(X) = doc-level total of D-coded nonDerivative rows
                     of document X; NO dollar value field exists on
                     either surface (stream rows: measured 0 value keys;
                     ownership XML: shares + price-per-share only), so
                     the declared fail-closed fallback is universal:
                     shares x raw EODHD close at X's own acceptance date;
                     dV unmeasurable (close missing) pairs carry dV=None
                     and cannot satisfy the P2 floor (counted, never
                     guessed).
  lag                d(p) = calendar days between the two acceptance
                     DATES (UTC); distribution disclosed, never trimmed.
"""

from __future__ import annotations

import json
from bisect import bisect_left, bisect_right
from datetime import date

import xml.etree.ElementTree as ET

from . import core
from .core import first_session_ge
from research.assets.stocks_ng1.plane_adapter import (
    _DOCTYPE_RE, _ISSUER_CIK_RE, _OWNER_CIK_RE, _PERIOD_RE,
)


class PairDefectError(RuntimeError):
    """Census reconciliation failed - the D2 run dies fail-closed."""


# ------------------------------------------------------------ stream ---------
def build_stream_index():
    """One pass over the pinned stream -> (acceptance-per-accession,
    D-coded nonDerivative shares-per-accession, diagnostics)."""
    acc_ts: dict[str, str] = {}
    acc_dshares: dict[str, float] = {}
    acc_drows: dict[str, int] = {}
    diag = {"rows_total": 0, "acceptance_conflict_accessions": 0,
            "d_coded_accessions": 0, "shares_unparseable_rows": 0}
    with open(core.STREAM_PATH, buffering=1 << 20) as fh:
        for line in fh:
            r = json.loads(line)
            diag["rows_total"] += 1
            an = (r.get("accession") or "").replace("-", "")
            if not an:
                continue
            a = r.get("acceptance") or ""
            if an in acc_ts:
                if acc_ts[an] != a:
                    diag["acceptance_conflict_accessions"] += 1
                    if a < acc_ts[an]:          # deterministic: MIN stamp
                        acc_ts[an] = a
            else:
                acc_ts[an] = a
            if (str(r.get("table", "")).strip().lower() == "nonderivative"
                    and r.get("direction") == "D"):
                try:
                    sh = float(str(r.get("shares") or "").replace(",", ""))
                    if sh == sh and sh >= 0:
                        acc_dshares[an] = acc_dshares.get(an, 0.0) + sh
                        acc_drows[an] = acc_drows.get(an, 0) + 1
                        continue
                except (TypeError, ValueError):
                    pass
                diag["shares_unparseable_rows"] += 1
    diag["accessions_distinct"] = len(acc_ts)
    diag["d_coded_accessions"] = len(acc_dshares)
    return acc_ts, acc_dshares, acc_drows, diag


# ---------------------------------------------------------- 4/A parsing ------
def _text(el, tag):
    x = el.find(f".//{tag}")
    if x is None:
        return None
    t = (x.text or "").strip()
    return t or None


def parse_amendments():
    """Parse every 4/A primary XML of the re-ingest tree (deterministic
    order: sorted manifest keys).  Returns {accession_nodash: {...}}."""
    man = json.loads(core.FORM4A_MANIFEST_PATH.read_text())
    docs = {}
    diag = {"files": 0, "non_xml_keys": 0, "not_4a": 0}
    for rel in sorted(man["files"]):
        parts = rel.split("/")
        if len(parts) != 3 or parts[2] == "index.json":
            continue
        diag["files"] += 1
        accn = parts[1]
        if not parts[2].lower().endswith(".xml"):
            diag["non_xml_keys"] += 1
            continue
        path = core.FORM4A_ROOT / rel
        root = ET.fromstring(path.read_bytes())
        if _text(root, "documentType") != "4/A":
            diag["not_4a"] += 1
            continue
        d_shares = 0.0
        d_rows = 0
        nd = root.find(".//nonDerivativeTable")
        if nd is not None:
            for tx in nd.findall("nonDerivativeTransaction"):
                code_el = tx.find(
                    "transactionAmounts/transactionAcquiredDisposedCode/value")
                code = (code_el.text or "").strip() if code_el is not None else ""
                if code != "D":
                    continue
                sh_el = tx.find("transactionAmounts/transactionShares/value")
                try:
                    sh = float((sh_el.text or "0").replace(",", ""))
                except (AttributeError, ValueError):
                    sh = None
                d_rows += 1
                if sh is not None and sh == sh:
                    d_shares += sh
        docs[accn] = {
            "issuerCik": _text(root, "issuerCik"),
            "rptOwnerCik": _text(root, "rptOwnerCik"),
            "periodOfReport": _text(root, "periodOfReport"),
            "d_shares": d_shares, "d_rows": d_rows,
            "fetch_cik": ("CIK" + parts[0].replace("CIK", "")),
        }
    return docs, diag


def index_lastmod():
    """accession_nodash -> primary-doc last-modified (ET-naive) from the
    re-ingest accession index.json files (the proposal's cross-check
    surface); None when the item is absent."""
    out = {}
    man = json.loads(core.FORM4A_MANIFEST_PATH.read_text())
    for rel in sorted(man["files"]):
        parts = rel.split("/")
        if len(parts) != 3 or parts[2] == "index.json":
            continue
        cik_dir, accn = parts[0], parts[1]
        try:
            idx = json.loads(
                (core.FORM4A_ROOT / cik_dir / accn / "index.json").read_text())
        except (OSError, ValueError):
            out[accn] = None
            continue
        items = idx.get("directory", {}).get("item", [])
        # primary doc = the directory's non-index XML item (the only one
        # the ingest could have fetched as primary)
        lm = None
        for it in items:
            nm = it.get("name", "")
            if (nm.lower().endswith(".xml")
                    and "index" not in nm.lower()
                    and not nm.startswith(".")):
                lm = it.get("last-modified")
                break
        out[accn] = lm
    return out


# ------------------------------------------------------ originals index -------
def build_originals_index():
    """key (issuerCik, rptOwnerCik, periodOfReport) -> sorted list of
    original accession_nodash, over every pinned type-4 file."""
    manifest = json.loads(core.SUBSTRATE_MANIFEST_PATH.read_text())
    files = manifest["sections"]["form4_xml_docs"]["files"]
    orig: dict[tuple[str, str, str], list[str]] = {}
    for key in sorted(files):
        parts = key.split("/")
        accn = parts[2] if len(parts) >= 4 else None
        try:
            data = (core.V13_INTEG / ".staging_sec_v13" / key).read_bytes()
        except OSError:
            continue
        ic = _ISSUER_CIK_RE.search(data)
        oc = _OWNER_CIK_RE.search(data)
        per = _PERIOD_RE.search(data)
        if ic and oc and per and accn:
            k = (ic.group(1).decode("utf-8", "strip"),
                 oc.group(1).decode("utf-8", "strip"),
                 per.group(1).decode("utf-8", "strip"))
            orig.setdefault(k, []).append(accn)
    return orig, len(files)


# ------------------------------------------------------------- pairing --------
def resolve_pairs(C):
    """Full pair resolution + reconciliation against census B (fail-closed)
    + per-entity amendment-acceptance event structures for the anchors."""
    census = json.loads(core.CENSUS_B_PATH.read_text())["census"]
    filing_year = {}
    with open(core.FORM4A_STATE_PATH) as fh:
        for line in fh:
            row = json.loads(line)
            if row.get("status") == "OK":
                filing_year[row["accession_nodash"]] = (
                    (row.get("filing_date") or "")[:4] or None)
    acc_ts, acc_dshares, acc_drows, stream_diag = build_stream_index()
    amend, parse_diag = parse_amendments()
    lastmod = index_lastmod()
    orig, files_scanned = build_originals_index()

    # ---- census B reconciliation (the pairing IS the census pairing) ------
    recon = {
        "amendment_docs": len(amend),
        "original_index_size": len(orig),
        "amendments_with_resolvable_original": 0,
    }
    for accn, a in amend.items():
        key = (a["issuerCik"], a["rptOwnerCik"], a["periodOfReport"])
        if None not in key and orig.get(key):
            recon["amendments_with_resolvable_original"] += 1
    want = {
        "amendment_docs": census["amendment_docs"],
        "amendments_with_resolvable_original":
            census["amendments_with_resolvable_original"],
        "original_index_size": core.PIN_CENSUS_B["original_index_size"],
    }
    for field, w in want.items():
        if recon[field] != w:
            raise PairDefectError(
                f"census B reconciliation failed on {field}: "
                f"{recon[field]} != {w}")

    # ---- resolution to MEASUREMENT pairs -----------------------------------
    stages = {
        "resolvable_census_def": recon["amendments_with_resolvable_original"],
        "original_not_stream_acceptance": 0,
        "amendment_stamp_missing": 0,
        "amendment_stamp_crosscheck_mismatch": 0,
        "issuer_not_cohort_member": 0,
        "measurement_pairs": 0,
    }
    ties = {"keys_with_multiple_originals": 0, "pairs_with_tie_broken": 0}
    per_year_resolvable = {}
    per_year_measurement = {}
    pairs = []
    for accn in sorted(amend):
        a = amend[accn]
        key = (a["issuerCik"], a["rptOwnerCik"], a["periodOfReport"])
        cands = orig.get(key) if None not in key else None
        if not cands:
            continue
        # census by-year authority = FILING date year (fetch state); the
        # measurement by-year authority = acceptance year (pinned metadata)
        year = (filing_year.get(accn) or "unknown")
        per_year_resolvable[year] = per_year_resolvable.get(year, 0) + 1
        in_stream = [c for c in cands if c in acc_ts]
        if not in_stream:
            stages["original_not_stream_acceptance"] += 1
            continue
        if len(in_stream) > 1:
            ties["pairs_with_tie_broken"] += 1
        orig_acc = sorted(in_stream, key=lambda c: (acc_ts[c], c))[0]
        a_ts = C.acc4a.get(accn)
        if not a_ts:
            stages["amendment_stamp_missing"] += 1
            continue
        lm = lastmod.get(accn)
        ok = lm is not None
        if ok:
            utc_d = date.fromisoformat(a_ts[:10])
            lm_d = date.fromisoformat(lm[:10])
            ok = (utc_d - lm_d).days in (0, 1)   # ET = UTC-4/UTC-5
        if not ok:
            stages["amendment_stamp_crosscheck_mismatch"] += 1
            continue
        cik = "CIK" + (a["issuerCik"] or "")
        if cik not in C.bookable:
            stages["issuer_not_cohort_member"] += 1
            continue
        o_ts = acc_ts[orig_acc]
        lag = (date.fromisoformat(a_ts[:10])
               - date.fromisoformat(o_ts[:10])).days
        c_a = core.close_at(C, cik, a_ts[:10])
        c_o = core.close_at(C, cik, o_ts[:10])
        v_a = (a["d_shares"] * c_a
               if (c_a is not None and c_a > 0) else None)
        v_o = (acc_dshares.get(orig_acc, 0.0) * c_o
               if (c_o is not None and c_o > 0) else None)
        dv = None if (v_a is None or v_o is None) else v_a - v_o
        pairs.append({
            "cik": cik, "amend_acc": accn, "orig_acc": orig_acc,
            "a_ts": a_ts, "o_ts": o_ts, "lag_days": lag,
            "v_a": v_a, "v_o": v_o, "dv": dv,
            "a_d_shares": a["d_shares"],
            "o_d_shares": acc_dshares.get(orig_acc, 0.0),
            "o_d_rows": acc_drows.get(orig_acc, 0),
            "a_d_rows": a["d_rows"],
            "sector": C.bookable[cik]["sector"],
            "cls": C.bookable[cik]["cls"],
        })
        stages["measurement_pairs"] += 1
        per_year_measurement[a_ts[:4]] = (
            per_year_measurement.get(a_ts[:4], 0) + 1)
    ties["keys_with_multiple_originals"] = sum(
        1 for v in orig.values() if len(v) > 1)

    # by-year reconciliation against the census resolvable split
    if {k: v for k, v in sorted(per_year_resolvable.items())} != {
            k: v for k, v in sorted(census["resolvable_by_year"].items())}:
        raise PairDefectError(
            f"resolvable by-year mismatch: {sorted(per_year_resolvable.items())}"
            f" != {sorted(census['resolvable_by_year'].items())}")

    # ---- per-entity amendment-acceptance event structures ------------------
    events = {}
    for p in pairs:
        sess = first_session_ge(C.sessions, p["a_ts"][:10])
        if sess is None:
            continue                        # acceptance after grid calendar
        si = C.sess_idx[sess]
        events.setdefault(p["cik"], []).append(
            {"si": si, "lag": p["lag_days"], "dv": p["dv"],
             "acc": p["amend_acc"], "a_ts": p["a_ts"]})
    E4a = {}
    for cik in sorted(events):
        lst = sorted(events[cik], key=lambda e: (e["si"], e["acc"]))
        E4a[cik] = {"sess_idx": [e["si"] for e in lst],
                    "sess_d": [C.sessions[e["si"]] for e in lst],
                    "events": [(e["lag"], e["dv"]) for e in lst],
                    "accs": [e["acc"] for e in lst]}

    # ---- 4/A acceptance events for the arrival shadow (ANY kind: every
    # parseable 4/A doc attributed to a cohort issuer, pair or not) --------
    arr = {}
    arr_unattributable = 0
    for accn, a in amend.items():
        a_ts = C.acc4a.get(accn)
        if not a_ts:
            continue
        cik = "CIK" + (a["issuerCik"] or "")
        if cik not in C.bookable:
            arr_unattributable += 1
            continue
        sess = first_session_ge(C.sessions, a_ts[:10])
        if sess is None:
            continue
        arr.setdefault(cik, {}).setdefault(C.sess_idx[sess], []).append(accn)
    Arr4a = {}
    for cik in sorted(arr):
        sis = sorted(arr[cik])
        cnt = [len(arr[cik][si]) for si in sis]
        pref = [0] * len(sis)
        for i, c in enumerate(cnt):
            pref[i] = c + (pref[i - 1] if i > 0 else 0)
        Arr4a[cik] = {"sess_idx": sis,
                      "sess_d": [C.sessions[i] for i in sis],
                      "cum": pref}

    diag = {
        "census_reconciliation": {**recon, "verdict": "MATCH"},
        "stages": stages,
        "ties": ties,
        "per_year_resolvable": dict(sorted(per_year_resolvable.items())),
        "per_year_measurement": dict(sorted(per_year_measurement.items())),
        "stream_index": stream_diag,
        "amendment_parse": parse_diag,
        "arrival_4a_entities": len(Arr4a),
        "arrival_4a_docs": sum(v["cum"][-1] for v in Arr4a.values()),
        "arrival_4a_unattributable_docs": arr_unattributable,
        "files_scanned_originals": files_scanned,
    }
    return pairs, E4a, Arr4a, diag
