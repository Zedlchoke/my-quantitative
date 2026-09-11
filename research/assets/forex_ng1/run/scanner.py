"""Recursive leak scanner for sanitized dry-run outputs.

Scans JSON documents at EVERY depth (dicts, lists, nested both) for
outcome fields that must not exist in a dry-run artifact: PnL, profit
factor, expectancy, stress outcomes, breakeven.  A forbidden key with a
non-null value is a LEAK; a null value is treated as absent (verified
absence, not inferred).  Matching is case-insensitive on normalized key
names (underscore/hyphen-insensitive).
"""

from __future__ import annotations

import re

#: Forbidden field-name patterns (outcome fields only; cost CONTRACT
#: constants and identity fields are legal).
FORBIDDEN_PATTERNS = (
    re.compile(r"pnl", re.IGNORECASE),
    re.compile(r"profit_?factor", re.IGNORECASE),
    re.compile(r"^pf$", re.IGNORECASE),
    re.compile(r"expectancy", re.IGNORECASE),
    re.compile(r"breakeven|break_?even", re.IGNORECASE),
    # stress OUTCOME fields (the word 'stress' alone is allowed in
    # cost-ladder context, e.g. tier names; leak requires it adjacent to
    # an outcome word)
    re.compile(r"stress.*(pnl|expectancy|return|metric)|"
               r"(pnl|expectancy|return).*stress", re.IGNORECASE),
)

SCANNER_METHOD = ("recursive JSON walk (dicts+lists, every depth); "
                  "case/underscore/hyphen-normalized key match against "
                  "forbidden outcome-field patterns; non-null value = "
                  "LEAK; null = verified absent")


def _normalize(key: str) -> str:
    return re.sub(r"[\s\-]+", "_", str(key)).strip("_")


def scan_document(doc, path: str = "$") -> list[dict]:
    """Return a list of leak findings ([] = clean)."""
    findings: list[dict] = []
    if isinstance(doc, dict):
        for k, v in doc.items():
            here = f"{path}.{k}"
            nk = _normalize(k)
            if any(p.search(nk) for p in FORBIDDEN_PATTERNS):
                if v is not None:
                    findings.append({"path": here, "key": str(k),
                                     "value_type": type(v).__name__})
            findings.extend(scan_document(v, here))
    elif isinstance(doc, list):
        for i, v in enumerate(doc):
            findings.extend(scan_document(v, f"{path}[{i}]"))
    return findings


def scan_json_file(path: str) -> list[dict]:
    import json
    with open(path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    return scan_document(doc)
