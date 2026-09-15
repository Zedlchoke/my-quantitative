"""FOREX-NG5 P0 — CFTC Commitments of Traders bulk-file parser (gates A4/A7).

Regimes (plan sec3 A4): ``legacy`` (long format, 1986-01-15 ->), ``disagg``
(Disaggregated futures-only, 2006-06-13 ->) and ``tff`` (Traders in Financial
Futures futures-only, 2006-06-13 ->). The regimes are parsed SEPARATELY and
are never merged at parse level; any cross-regime comparison is a census-level
decision recorded in the P0 artifact, never a parser behavior.

Exactness contract (A4): every position / open-interest value is a
``decimal.Decimal`` parsed from the exact source string. The only accepted
literal is an optionally-signed integer (``^-?\\d+$``) after CSV unquoting.
No binary float is constructed anywhere in this module. A value that does not
match is a REJECT: the row is excluded from the returned records, recorded in
``rejects`` with line number, field and raw text, and never silently coerced.

Fail-closed on unknown schema (A4): the header of each file is normalized and
mapped through the DECLARED variant table for its regime. If any required
canonical field is missing, :class:`SchemaUnknownError` is raised carrying the
verbatim header. Extra columns that map to nothing are ALLOWED and recorded
(the long formats carry concentration / change / old / other columns the census
does not consume).

Verbatim headers measured 2026-09-15 from recon pulls (recorded in the P0
schema report): legacy year zips carry a member ``Annual.TXT`` with
human-readable quoted headers ("Noncommercial Positions-Long (All)", a leading
space variant on " Total Reportable Positions-Long (All)", both All/Old/Other
triplets); disagg year zips carry ``f_year.txt`` with underscored headers
including the double-underscore quirk ``"Swap__Positions_Short_All"`` and
``M_Money_Positions_*``; TFF year zips carry ``FinFutYY.txt`` with
``Dealer_Positions_* / Asset_Mgr_Positions_* / Lev_Money_Positions_*``. All
three normalization paths converge on the canonical fields below.
"""
from __future__ import annotations

import csv
import hashlib
import io
import re
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

REGIMES = ("legacy", "disagg", "tff")

_INT_RE = re.compile(r"^-?\d+$")
_DEC_RE = re.compile(r"^-?\d+\.(\d+)$")
_NORM_RE = re.compile(r"[^a-z0-9]+")
_YMD_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_MDY_RE = re.compile(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$")
_YYMMDD_RE = re.compile(r"^(\d{2})(\d{2})(\d{2})$")


class SchemaUnknownError(ValueError):
    """Header does not provide the regime's required canonical fields."""

    def __init__(self, regime: str, header: Sequence[str], missing: Sequence[str]):
        self.regime = regime
        self.header = list(header)
        self.missing = list(missing)
        super().__init__(
            f"unknown {regime} schema; missing required fields {missing}; "
            f"header={header!r}"
        )


class MalformedField(ValueError):
    """A required count/date value failed the exact-literal contract."""

    def __init__(self, line: int, field: str, raw: str):
        self.line = line
        self.field = field
        self.raw = raw
        super().__init__(f"line {line}: field {field} not an exact integer/date: {raw!r}")


def _norm(header_cell: str) -> str:
    return _NORM_RE.sub("", (header_cell or "").strip().lower())


def _v(h: str) -> str:
    """Strip the CSV layer's residual surrounding double quotes, if any."""
    t = (h or "").strip()
    if len(t) >= 2 and t[0] == '"' and t[-1] == '"':
        t = t[1:-1]
    return t


# --- declared variant tables: normalized header -> canonical field ---------
_REPORT_DATE_VARIANTS = {
    "reportdateasyyyymmdd": "report_date_iso",       # Report_Date_as_YYYY-MM-DD
    "reportdateasmmddyyyy": "report_date_mdy",       # Report_Date_as_MM_DD_YYYY
    "asofdateinformyyyymmdd": "as_of_iso",           # As of Date in Form YYYY-MM-DD
    "asofdateinformyymmdd": "as_of_yymmdd",          # As of Date in Form YYMMDD
}
_ID_VARIANTS = {
    "marketandexchangenames": "market_name",
    "cftccontractmarketcode": "cftc_contract_market_code",
    "cftcmarketcode": "cftc_market_code",
    "openinterestall": "open_interest_all",
}

_LEGACY_MAP: Dict[str, str] = {**_ID_VARIANTS, **_REPORT_DATE_VARIANTS,
    "noncommercialpositionslongall": "noncomm_long",
    "noncommercialpositionsshortall": "noncomm_short",
    "noncommercialpositionsspreadingall": "noncomm_spread",  # legacy spells "Spreading"
    "noncommercialpositionsspreadall": "noncomm_spread",
    "noncommpositionslongall": "noncomm_long",       # short-format variant
    "noncommpositionsshortall": "noncomm_short",
    "noncommpositionsspreadall": "noncomm_spread",
    "commercialpositionslongall": "comm_long",
    "commercialpositionsshortall": "comm_short",
    "totalreportablepositionslongall": "tot_rept_long",
    "totalreportablepositionsshortall": "tot_rept_short",
    "nonreportablepositionslongall": "nonrept_long",
    "nonreportablepositionsshortall": "nonrept_short",
}

_DISAGG_MAP: Dict[str, str] = {**_ID_VARIANTS, **_REPORT_DATE_VARIANTS,
    "prodmercpositionslongall": "prod_merc_long",
    "prodmercpositionsshortall": "prod_merc_short",
    "swappositionslongall": "swap_long",
    "swappositionsshortall": "swap_short",          # covers Swap__Positions_Short_All
    "swappositionsspreadall": "swap_spread",
    "mmoneypositionslongall": "mmoney_long",        # M_Money_Positions_Long_All
    "mmoneypositionsshortall": "mmoney_short",
    "mmoneypositionsspreadall": "mmoney_spread",
    "managedmoneypositionslongall": "mmoney_long",  # Socrata-era variant
    "managedmoneypositionsshortall": "mmoney_short",
    "otherreptpositionslongall": "other_rept_long",
    "otherreptpositionsshortall": "other_rept_short",
    "otherreptpositionsspreadall": "other_rept_spread",
    "totreptpositionslongall": "tot_rept_long",
    "totreptpositionsshortall": "tot_rept_short",
    "nonreptpositionslongall": "nonrept_long",
    "nonreptpositionsshortall": "nonrept_short",
}

_TFF_MAP: Dict[str, str] = {**_ID_VARIANTS, **_REPORT_DATE_VARIANTS,
    "dealpositionslongall": "dealer_long",           # Deal_Positions_Long_All
    "dealpositionsshortall": "dealer_short",
    "dealpositionsspreadall": "dealer_spread",
    "dealerpositionslongall": "dealer_long",         # Socrata-era variant
    "dealerpositionsshortall": "dealer_short",
    "dealerpositionsspreadall": "dealer_spread",
    "assetmgrpositionslongall": "asset_mgr_long",
    "assetmgrpositionsshortall": "asset_mgr_short",
    "assetmgrpositionsspreadall": "asset_mgr_spread",
    "assetmanagerpositionslongall": "asset_mgr_long",
    "assetmanagerpositionsshortall": "asset_mgr_short",
    "levmoneypositionslongall": "lev_fund_long",     # Lev_Money_Positions_Long_All
    "levmoneypositionsshortall": "lev_fund_short",
    "levmoneypositionsspreadall": "lev_fund_spread",
    "leveragedfundspositionslongall": "lev_fund_long",
    "leveragedfundspositionsshortall": "lev_fund_short",
    "leveragedfundspositionsspreadall": "lev_fund_spread",
    "otherreptpositionslongall": "other_rept_long",
    "otherreptpositionsshortall": "other_rept_short",
    "otherreptpositionsspreadall": "other_rept_spread",
    "totreptpositionslongall": "tot_rept_long",
    "totreptpositionsshortall": "tot_rept_short",
    "nonreptpositionslongall": "nonrept_long",
    "nonreptpositionsshortall": "nonrept_short",
}

VARIANT_MAPS: Dict[str, Dict[str, str]] = {
    "legacy": _LEGACY_MAP, "disagg": _DISAGG_MAP, "tff": _TFF_MAP,
}

# Reportable-parts layout per regime (source-truth measured 2026-09-15 on the
# live files): LONGS + SPREADS == Tot_Rept_Long and SHORTS + SPREADS ==
# Tot_Rept_Short per side; OI == Tot_Rept_Long + NonRept_Long == Tot_Rept_Short
# + NonRept_Short. Legacy spreads live in one shared "Spreading" column;
# disagg/TFF spreads are per category (producers have no spread column).
REGIME_FIELDS: Dict[str, Dict[str, Tuple[str, ...]]] = {
    "legacy": {
        "long": ("noncomm_long", "comm_long"),
        "short": ("noncomm_short", "comm_short"),
        "spread": ("noncomm_spread",),
    },
    "disagg": {
        "long": ("prod_merc_long", "swap_long", "mmoney_long", "other_rept_long"),
        "short": ("prod_merc_short", "swap_short", "mmoney_short", "other_rept_short"),
        "spread": ("swap_spread", "mmoney_spread", "other_rept_spread"),
    },
    "tff": {
        "long": ("dealer_long", "asset_mgr_long", "lev_fund_long", "other_rept_long"),
        "short": ("dealer_short", "asset_mgr_short", "lev_fund_short", "other_rept_short"),
        "spread": ("dealer_spread", "asset_mgr_spread", "lev_fund_spread",
                   "other_rept_spread"),
    },
}

PARTS = {"legacy": ("noncomm", "comm", "nonrept"),
         "disagg": ("prod_merc", "swap", "mmoney", "other_rept"),
         "tff": ("dealer", "asset_mgr", "lev_fund", "other_rept")}  # naming only


def required_fields(regime: str) -> Tuple[str, ...]:
    f = REGIME_FIELDS[regime]
    fields = ["cftc_contract_market_code", "market_name", "report_date",
              "open_interest_all", "tot_rept_long", "tot_rept_short",
              "nonrept_long", "nonrept_short"]
    return tuple(fields + list(f["long"]) + list(f["short"]) + list(f["spread"]))


def map_header(header_row: Sequence[str], regime: str) -> Dict[int, str]:
    """normalized column -> canonical; hard-fail when a required field is absent."""
    vmap = VARIANT_MAPS[regime]
    mapped: Dict[int, str] = {}
    for i, cell in enumerate(header_row):
        canon = vmap.get(_norm(_v(cell)))
        if canon is not None and canon not in mapped:
            mapped[i] = canon
    have = set(mapped.values())
    missing = []
    for req in ("market_name", "cftc_contract_market_code"):
        if req not in have:
            missing.append(req)
    if not any(k in have for k in ("report_date_iso", "report_date_mdy", "as_of_iso", "as_of_yymmdd")):
        missing.append("report_date")
    for req in required_fields(regime):
        if req not in have and req not in ("market_name", "cftc_contract_market_code", "report_date"):
            missing.append(req)
    if missing:
        raise SchemaUnknownError(regime, list(header_row), missing)
    return mapped


def _parse_count(raw: str, line: int, field: str) -> Decimal:
    """Exact count contract. Accepts (a) plain integer literals and (b) exact
    integer-valued decimal literals with an explicit all-zero fractional part
    (measured in the TFF history file, e.g. '93212.000000' — parsed as the
    exact Decimal, never via binary float). Any other literal — thousands
    separators, non-zero fractional digits, text — is malformed."""
    s = (raw or "").strip()
    if _INT_RE.match(s):
        return Decimal(s)
    m = _DEC_RE.match(s)
    if m and m.group(1).strip("0") == "":
        return Decimal(s)
    raise MalformedField(line, field, raw)


def _iso_from_yymmdd(raw: str, line: int) -> str:
    s = (raw or "").strip()
    m = _YYMMDD_RE.match(s)
    if not m:
        raise MalformedField(line, "as_of_yymmdd", raw)
    yy, mm, dd = (int(g) for g in m.groups())
    year = 1900 + yy if yy >= 70 else 2000 + yy
    if not (1 <= mm <= 12 and 1 <= dd <= 31):
        raise MalformedField(line, "as_of_yymmdd", raw)
    return f"{year:04d}-{mm:02d}-{dd:02d}"


def _iso_from_ymd(raw: str, line: int) -> Optional[str]:
    s = (raw or "").strip()
    m = _YMD_RE.match(s)
    if not m:
        return None
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"


def _iso_from_mdy(raw: str, line: int) -> Optional[str]:
    s = (raw or "").strip()
    m = _MDY_RE.match(s)
    if not m:
        return None
    mm, dd, yyyy = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not (1 <= mm <= 12 and 1 <= dd <= 31):
        raise MalformedField(line, "report_date_mdy", raw)
    return f"{yyyy:04d}-{mm:02d}-{dd:02d}"


def _parse_code(raw: str, line: int) -> Tuple[str, str]:
    """CFTC contract-market codes: pure digits (zero-padded to 6) or alnum
    adjunct/consolidation codes with embedded or trailing alpha/'+' markers
    (e.g. '13874A', '022A13', '12460+' — measured on the live files
    2026-09-15). Alnum codes are kept VERBATIM (uppercased); only pure-digit
    codes are zero-padded. Anything outside [0-9A-Z+]{3,8} is malformed."""
    s = (raw or "").strip().strip('"').upper()
    if not s:
        raise MalformedField(line, "cftc_contract_market_code", raw)
    if s.isdigit():
        return s.zfill(6), s
    if len(s) < 3 or len(s) > 8 or not re.match(r"^[0-9A-Z+]+$", s):
        raise MalformedField(line, "cftc_contract_market_code", raw)
    return s, s


def parse_report_csv(text: str, regime: str) -> dict:
    """Parse one regime file (already decoded) into census records.

    Returns dict with verbatim header, applied column map, unmapped columns,
    records (exact-Decimal values), rejects (fail-closed row exclusions) and
    per-record identity flags (reportable-parts identity, measured not fixed).
    """
    if regime not in REGIMES:
        raise ValueError(f"unknown regime {regime!r}")
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        raise SchemaUnknownError(regime, [], ["<empty file>"])
    header = rows[0]
    mapped = map_header(header, regime)  # idx -> canonical
    by_canon: Dict[str, int] = {}
    for idx, canon in mapped.items():
        by_canon.setdefault(canon, idx)
    parts = PARTS[regime]
    records: List[dict] = []
    rejects: List[dict] = []
    for line, row in enumerate(rows[1:], start=2):
        if not any((c or "").strip() for c in row):
            continue  # blank line
        if len(row) != len(header):
            # fail-closed: layout-divergent rows (e.g. TFF "Consolidated" rows
            # carry 87 cells vs 35 header columns) are rejected, never guessed
            rejects.append({"line": line, "field": "<row_layout>",
                            "raw": f"{len(row)} cells vs {len(header)} header columns",
                            "reason": "row_wider_or_narrower_than_header"})
            continue
        try:
            ident: Dict[str, str] = {}
            for idx, canon in mapped.items():
                if canon in ("market_name", "cftc_contract_market_code", "cftc_market_code"):
                    ident[canon] = _v(row[idx]) if idx < len(row) else ""
            code, code_raw = _parse_code(ident.get("cftc_contract_market_code", ""), line)
            as_of = None
            as_of_src = None
            if "as_of_iso" in by_canon and by_canon["as_of_iso"] < len(row):
                cand = _iso_from_ymd(_v(row[by_canon["as_of_iso"]]), line)
                if cand:
                    as_of, as_of_src = cand, "as_of_iso"
            if as_of is None and "as_of_yymmdd" in by_canon and by_canon["as_of_yymmdd"] < len(row):
                as_of = _iso_from_yymmdd(_v(row[by_canon["as_of_yymmdd"]]), line)
                as_of_src = "as_of_yymmdd"
            report_date = None
            report_src = None
            if "report_date_iso" in by_canon and by_canon["report_date_iso"] < len(row):
                cand = _iso_from_ymd(_v(row[by_canon["report_date_iso"]]), line)
                if cand:
                    report_date, report_src = cand, "report_date_iso"
            if report_date is None and "report_date_mdy" in by_canon and by_canon["report_date_mdy"] < len(row):
                cand = _iso_from_mdy(_v(row[by_canon["report_date_mdy"]]), line)
                if cand:
                    report_date, report_src = cand, "report_date_mdy"
            if report_date is None:
                report_date, report_src = as_of, f"as_of({as_of_src})"
            values: Dict[str, Decimal] = {}
            for idx, canon in mapped.items():
                if canon in ("market_name", "cftc_contract_market_code", "cftc_market_code",
                             "report_date_iso", "report_date_mdy", "as_of_iso", "as_of_yymmdd"):
                    continue
                raw = _v(row[idx]) if idx < len(row) else ""
                values[canon] = _parse_count(raw, line, canon)
        except MalformedField as exc:
            rejects.append({"line": line, "field": exc.field, "raw": exc.raw,
                            "reason": "not_exact_integer_or_date"})
            continue
        # identity (source-truth law): longs+spreads == tot_rept per side,
        # OI == tot_rept + nonrept per side
        identity_detail = []
        try:
            f = REGIME_FIELDS[regime]
            long_sum = sum((values[k] for k in f["long"] + f["spread"]), Decimal(0))
            short_sum = sum((values[k] for k in f["short"] + f["spread"]), Decimal(0))
            if long_sum != values["tot_rept_long"]:
                identity_detail.append("parts_long_ne_tot")
            if short_sum != values["tot_rept_short"]:
                identity_detail.append("parts_short_ne_tot")
            if values["open_interest_all"] != values["tot_rept_long"] + values["nonrept_long"]:
                identity_detail.append("oi_ne_tot_long_plus_nonrept")
            if values["open_interest_all"] != values["tot_rept_short"] + values["nonrept_short"]:
                identity_detail.append("oi_ne_tot_short_plus_nonrept")
        except KeyError as exc:  # pragma: no cover — map_header guarantees presence
            raise SchemaUnknownError(regime, list(header), [str(exc)])
        rec = {
            "market_name": ident.get("market_name", ""),
            "code": code,
            "code_raw": code_raw,
            "as_of": as_of,
            "as_of_source": as_of_src,
            "report_date": report_date,
            "report_date_source": report_src,
            "values": values,
            "identity_ok": not identity_detail,
            "identity_detail": identity_detail,
            "line": line,
        }
        records.append(rec)
    unmapped = sorted({_v(c) for i, c in enumerate(header) if i not in mapped})
    return {
        "regime": regime,
        "header_verbatim": [_v(c) for c in header],
        "column_map": {header[i]: canon for i, canon in sorted(mapped.items())},
        "unmapped_columns": unmapped,
        "records": records,
        "rejects": rejects,
        "rows_total": len(rows) - 1,
    }


def record_key(rec: dict) -> Tuple[str, str]:
    return (rec["code"], rec["report_date"])


def _values_sig(rec: dict) -> str:
    vals = {k: str(v) for k, v in rec["values"].items()}
    vals["market_name"] = rec["market_name"]
    return repr(sorted(vals.items()))


def dedupe(records: Sequence[dict]) -> dict:
    """Collapse exact duplicates; flag conflicting (code, report_date) rows.

    Exact duplicate = same key and identical canonical values (A5 duplicate
    census). Conflicting = same key with differing values -> revision_conflict
    candidates for the frozen A3/X1 exclusion rule. First occurrence wins for
    the returned unique map; conflicts keep BOTH line refs for audit.
    """
    unique: Dict[Tuple[str, str], dict] = {}
    exact_duplicates = 0
    conflicts: List[dict] = []
    for rec in records:
        key = record_key(rec)
        if key not in unique:
            unique[key] = rec
            continue
        if _values_sig(unique[key]) == _values_sig(rec):
            exact_duplicates += 1
        else:
            conflicts.append({"key": key, "lines": [unique[key]["line"], rec["line"]]})
    return {"unique": unique, "exact_duplicates": exact_duplicates, "conflicts": conflicts}


def merge_sources(sources: Dict[str, Sequence[dict]], precedence: Sequence[str]) -> dict:
    """Cross-file merge with declared precedence (A5 duplicate census).

    ``precedence`` orders source ids; a key already taken by a higher-
    precedence source is an exact_duplicate if values match, else a
    revision_conflict (recorded with both source ids, never merged).
    """
    merged: Dict[Tuple[str, str], dict] = {}
    exact_duplicates = 0
    conflicts: List[dict] = []
    for src in precedence:
        for rec in sources.get(src, []):
            key = record_key(rec)
            if key not in merged:
                merged[key] = dict(rec, source=src)
                continue
            if _values_sig(merged[key]) == _values_sig(rec):
                exact_duplicates += 1
            else:
                conflicts.append({"key": key, "sources": [merged[key]["source"], src],
                                  "lines": [merged[key]["line"], rec["line"]]})
    return {"unique": merged, "exact_duplicates": exact_duplicates, "conflicts": conflicts}


# --- A7: deterministic digesting --------------------------------------------

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def redigest_file(path: Path) -> str:
    """Deterministic re-digest of raw bytes (A7 pass evidence)."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_code(code: str) -> str:
    return code.strip().zfill(6) if code.strip().isdigit() else code.strip()
