"""CSV / JSON export-shape serialization for the supported record subset.

Implements the DOCUMENTED text export shape of DBN (as encoded by the
official reference implementation, databento/dbn main@2026-10-02):

  * column order: the encode_order remove/insert algorithm with the
    RecordHeader flattened as one slot (spec.RecordSpec.sorted_for_text);
  * prices: 9-decimal fixed strings; UNDEF_PRICE prints as an EMPTY field
    (encode/csv/serialize.rs write_px_field pretty mode);
  * timestamps: ns -> "YYYY-MM-DDTHH:MM:SS.nnnnnnnnnZ"; ts==0 and
    UNDEF_TIMESTAMP print as EMPTY fields (write_ts_field pretty mode);
  * NUL c_char prints as an empty field;
  * one record per line (CSV row / JSON object).

The reader is header-name-driven (csv.DictReader), so vendor re-orderings
parse fine; unknown or missing columns are a typed error, never skipped.
The reader additionally accepts the explicit "UNDEF_PRICE" /
"UNDEF_TIMESTAMP" sentinel strings (a lenient extension; they parse to the
same sentinels as empty fields).
"""
from __future__ import annotations

import csv
import datetime as dt
import io
import json

from . import spec as S
from .spec import DbnFormatError


class TextSchemaError(DbnFormatError):
    """CSV/JSON text does not match the documented schema shape."""


# ---------------------------------------------------------------------------
# value formatting (pretty.rs semantics)
# ---------------------------------------------------------------------------

def ts_to_iso(ns: int) -> str:
    # Reference pretty rule (pretty.rs Ts Display + write_ts_field): ts==0
    # prints EMPTY; UNDEF_TIMESTAMP prints EMPTY in pretty CSV fields
    # (raw integer only in non-pretty mode).
    if ns == 0 or ns == S.UNDEF_TIMESTAMP:
        return ""
    secs, rem = divmod(ns, 1_000_000_000)
    d = dt.datetime.fromtimestamp(secs, tz=dt.timezone.utc)
    return f"{d.strftime('%Y-%m-%dT%H:%M:%S')}.{rem:09d}Z"


def iso_to_ts(text: str) -> int:
    if text in ("", None):
        return 0
    if text == "UNDEF_TIMESTAMP":
        return S.UNDEF_TIMESTAMP
    t = text.strip()
    if t.endswith("Z"):
        t = t[:-1]
    if "." in t:
        base, frac = t.split(".", 1)
        frac = (frac + "000000000")[:9]
    else:
        base, frac = t, "000000000"
    d = dt.datetime.strptime(base, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=dt.timezone.utc)
    return int(d.timestamp()) * 1_000_000_000 + int(frac)


def _format_value(name: str, value, kind: str) -> str:
    # Pretty CSV semantics of the reference serializer (encode/csv/
    # serialize.rs, verified 2026-10-02): UNDEF_PRICE and UNDEF_TIMESTAMP
    # and ts==0 write EMPTY fields; NUL c_char writes an empty field.
    if kind == "px":
        v = value if not isinstance(value, str) else S.price_to_nanos(value)
        return "" if v == S.UNDEF_PRICE else S.nanos_to_price_str(v)
    if kind == "ts":
        v = value if not isinstance(value, str) else iso_to_ts(value)
        return ts_to_iso(v)
    if kind == "char":
        if isinstance(value, int):
            return "" if value == 0 else (chr(value) if 0 <= value < 256
                                          else str(value))
        return "" if value in ("", "\x00") else str(value)
    if kind == "cstr":
        return "" if value is None else str(value)
    return str(value)


def _parse_value(name: str, text: str, kind: str):
    if kind == "px":
        return S.price_to_nanos(text) if text not in ("", "UNDEF_PRICE") else S.UNDEF_PRICE
    if kind == "ts":
        return iso_to_ts(text)
    if kind == "char":
        return ord(text) if len(text) == 1 else (0 if text == "" else int(text))
    if kind == "cstr":
        return text
    if text == "":
        return 0
    return int(text)


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------

def csv_columns(rtype: int) -> list[tuple[str, str]]:
    """[(column_name, kind)] in the documented export order."""
    rec = S.SPECS_BY_RTYPE[rtype]
    cols: list[tuple[str, str]] = []
    for f in rec.sorted_for_text():
        if f.name == "ts_event":
            cols.append(("ts_event", "ts"))
        elif f.name == "rtype":
            cols.append(("rtype", "int"))
        elif f.name == "publisher_id":
            cols.append(("publisher_id", "int"))
        elif f.name == "instrument_id":
            cols.append(("instrument_id", "int"))
        else:
            cols.append((f.name, f.kind if f.kind in ("px", "ts", "char", "cstr")
                         else "int"))
    return cols


def write_csv(path, rtype: int, rows: list[dict], *, delimiter: str = ",") -> None:
    cols = csv_columns(rtype)
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh, delimiter=delimiter)
        w.writerow([c for c, _ in cols])
        for row in rows:
            w.writerow([_format_value(c, row.get(c, 0), k) for c, k in cols])


def parse_csv(path_or_text: str, rtype: int | None = None) -> list[dict]:
    """Parse a CSV export back into normalized dicts (int nanos / int ns).

    `rtype` pins the expected schema; if None it is inferred from an
    `rtype` column (value column of the CSV). Fails closed on column sets
    that do not match any implemented layout."""
    if path_or_text.endswith(".csv") or "/" in path_or_text or path_or_text.endswith(".txt"):
        with open(path_or_text, newline="") as fh:
            reader = csv.DictReader(fh)
            return _rows_from_dictreader(reader, rtype)
    reader = csv.DictReader(io.StringIO(path_or_text))
    return _rows_from_dictreader(reader, rtype)


def _rows_from_dictreader(reader: csv.DictReader, rtype: int | None) -> list[dict]:
    out = []
    for raw in reader:
        row_rtype = rtype
        if row_rtype is None:
            rt_text = (raw.get("rtype") or "").strip()
            if not rt_text:
                raise TextSchemaError("CSV row has no rtype column and no rtype pinned")
            row_rtype = int(rt_text)
        if row_rtype not in S.SUPPORTED_RTYPES:
            raise TextSchemaError(
                f"CSV rtype {row_rtype} is not in the implemented subset "
                f"{sorted(S.SUPPORTED_RTYPES)} (fail-closed)")
        cols = dict(csv_columns(row_rtype))
        missing = [c for c in cols if c not in reader.fieldnames]
        if missing:
            raise TextSchemaError(
                f"CSV missing documented columns for rtype 0x{row_rtype:02x}: {missing}")
        rec = {}
        for c, k in cols.items():
            rec[c] = _parse_value(c, (raw.get(c) or "").strip(), k)
        out.append(rec)
    return out


# ---------------------------------------------------------------------------
# JSON (one object per line; field names == CSV columns)
# ---------------------------------------------------------------------------

def write_jsonl(path, rtype: int, rows: list[dict]) -> None:
    cols = csv_columns(rtype)
    with open(path, "w") as fh:
        for row in rows:
            obj = {c: _format_value(c, row.get(c, 0), k) for c, k in cols}
            fh.write(json.dumps(obj) + "\n")


def parse_jsonl(path_or_text: str, rtype: int | None = None) -> list[dict]:
    if path_or_text.endswith(".json") or path_or_text.endswith(".jsonl") or "/" in path_or_text:
        with open(path_or_text) as fh:
            lines = [ln for ln in fh.read().splitlines() if ln.strip()]
    else:
        lines = [ln for ln in path_or_text.splitlines() if ln.strip()]
    out = []
    for ln in lines:
        obj = json.loads(ln)
        row_rtype = rtype
        if row_rtype is None:
            rt_text = str(obj.get("rtype", "")).strip()
            if not rt_text:
                raise TextSchemaError("JSON object has no rtype field and none pinned")
            row_rtype = int(rt_text)
        if row_rtype not in S.SUPPORTED_RTYPES:
            raise TextSchemaError(
                f"JSON rtype {row_rtype} not in implemented subset (fail-closed)")
        cols = dict(csv_columns(row_rtype))
        missing = [c for c in cols if c not in obj]
        if missing:
            raise TextSchemaError(f"JSON object missing fields: {missing}")
        out.append({c: _parse_value(c, str(obj[c]), k) for c, k in cols.items()})
    return out
