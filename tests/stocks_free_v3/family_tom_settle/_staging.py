"""READ-ONLY access helpers for the staged snapshot (A9 dry run, S0 only).

Discipline (data rules for this lane):

* the snapshot lives OUTSIDE the worktree at
  ``research.stocks_free_v3.authority.SNAPSHOT_STAGING_PATH`` and is READ-ONLY;
* every pinned file is sha256-verified BEFORE parsing, via
  :class:`research.stocks_free_v3.isolation.SealedSnapshotReader` with the
  frozen :class:`S1Seal` and :class:`S0WindowPolicy`;
* every read window is S0-bounded (2018-04-04..2025-07-31); no date
  >= 2025-08-01 (sealed S1) is ever read or returned;
* raw closes come from ``<SYM>_none_p1.json`` (unadjusted); issuer
  distributions come from the PINNED SPDR distributions evidence workbook,
  parsed for the 11 cohort symbols only and truncated to S0 ex-dates;
  split factors are the five pinned 2025-12-05 2:1 events (authorized
  corporate-action inputs, committed as constants — no S1 data is read);
* nothing here copies raw data into git and nothing here computes a return,
  PnL or any scored metric.
"""

from __future__ import annotations

import datetime as dt
import re
import zipfile
from pathlib import Path

from research.assets.stocks.calendar import US_EQUITY_REGULAR_V1 as CALENDAR
from research.stocks_free_v3.authority import (
    COHORT_SYMBOLS,
    ISSUER_DISTRIBUTION_RECORDS_SHA256,
    S0_END,
    S0_START,
    S1_END,
    S1_START,
    SPLIT_EFFECTIVE_DATE,
    SPLIT_FACTOR,
    SPLIT_SYMBOLS,
    SNAPSHOT_STAGING_PATH,
    sha256_file,
)
from research.stocks_free_v3.isolation import (
    S0WindowPolicy,
    S1Seal,
    SealedSnapshotReader,
)

#: The pinned issuer distribution records workbook in the staging directory.
DISTRIBUTIONS_XLSX = "spdr-etf-historical-distributions.xlsx"

_REQUIRED_FILES = tuple(f"{s}_none_p1.json" for s in COHORT_SYMBOLS) + (
    DISTRIBUTIONS_XLSX,
)


def staging_available() -> bool:
    """True only when the whole read-only staging surface exists."""
    root = Path(SNAPSHOT_STAGING_PATH)
    return root.is_dir() and all((root / name).is_file() for name in _REQUIRED_FILES)


def make_reader() -> SealedSnapshotReader:
    """The pin-verified, S0-truncated reader for the staged snapshot."""
    return SealedSnapshotReader(
        SNAPSHOT_STAGING_PATH,
        seal=S1Seal(S1_START, S1_END),
        policy=S0WindowPolicy(),
    )


def s0_sessions() -> list[str]:
    """Regular sessions of the frozen calendar inside S0 (and nothing else)."""
    sessions: list[str] = []
    day = S0_START
    while day <= S0_END:
        if CALENDAR.is_session_day(day):
            sessions.append(day.isoformat())
        day += dt.timedelta(days=1)
    return sessions


def sessions_between(start: str, end: str) -> list[str]:
    """Frozen-calendar sessions in [start, end], both bounds asserted inside S0."""
    assert S0_START <= dt.date.fromisoformat(start)
    assert dt.date.fromisoformat(end) <= S0_END
    sessions: list[str] = []
    day = dt.date.fromisoformat(start)
    last = dt.date.fromisoformat(end)
    while day <= last:
        if CALENDAR.is_session_day(day):
            sessions.append(day.isoformat())
        day += dt.timedelta(days=1)
    return sessions


def load_s0_raw_closes(reader: SealedSnapshotReader) -> dict[str, dict[str, float]]:
    """S0-truncated raw closes for the 11 cohort symbols (pinned files only)."""
    return {
        s: dict(
            reader.load_symbol_closes(
                f"{s}_none_p1.json", start=S0_START, end=S0_END
            )
        )
        for s in COHORT_SYMBOLS
    }


def _xlsx_rows(path: Path) -> list[dict[str, str]]:
    """Minimal xlsx reader for the SPDR distributions workbook (A7-pinned)."""
    with zipfile.ZipFile(path) as bundle:
        strings_xml = bundle.read("xl/sharedStrings.xml").decode("utf-8", "replace")
        shared = [
            re.sub(r"<[^>]+>", "", m)
            for m in re.findall(r"<si>(.*?)</si>", strings_xml, re.S)
        ]
        sheet = bundle.read("xl/worksheets/sheet1.xml").decode("utf-8", "replace")
    rows: list[dict[str, str]] = []
    for row_match in re.findall(r"<row[^>]*>(.*?)</row>", sheet, re.S):
        cells: dict[str, str] = {}
        for cell in re.finditer(r'<c r="([A-Z]+)(\d+)"([^>]*)>(.*?)</c>', row_match, re.S):
            col, _, attrs, inner = cell.groups()
            value = re.search(r"<v>(.*?)</v>", inner)
            if not value:
                continue
            text = value.group(1)
            if 't="s"' in attrs:
                text = shared[int(text)]
            cells[col] = text
        if cells:
            rows.append(cells)
    return rows


def load_s0_distributions() -> dict[str, dict[str, float]]:
    """Issuer distributions of the 11 cohort symbols, ex-dates truncated to S0.

    The workbook is sha256-verified against the committed pin
    (``ISSUER_DISTRIBUTION_RECORDS_SHA256``) BEFORE parsing; the per-share
    amount is dividend + short-term capital gain (the same authorized
    accounting columns the V2 terminal used).
    """
    path = Path(SNAPSHOT_STAGING_PATH) / DISTRIBUTIONS_XLSX
    actual = sha256_file(path)
    if actual != ISSUER_DISTRIBUTION_RECORDS_SHA256:
        raise RuntimeError(
            f"issuer distributions workbook does not match the committed pin "
            f"({actual} != {ISSUER_DISTRIBUTION_RECORDS_SHA256})"
        )
    out: dict[str, dict[str, float]] = {s: {} for s in COHORT_SYMBOLS}
    for row in _xlsx_rows(path):
        ticker = str(row.get("B", "")).strip().upper()
        raw_date = str(row.get("D", "")).strip()
        match = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", raw_date)
        if ticker not in out or not match:
            continue
        ex_date = f"{int(match.group(3)):04d}-{int(match.group(1)):02d}-{int(match.group(2)):02d}"
        if ex_date > S0_END.isoformat():
            continue          # S1-dated rows are dropped, never read further
        amount = sum(float(row.get(c, 0) or 0) for c in ("G", "H") if row.get(c))
        if amount:
            out[ticker][ex_date] = out[ticker].get(ex_date, 0.0) + amount
    return {s: dict(sorted(v.items())) for s, v in out.items()}


def pinned_split_factors() -> dict[str, dict[str, float]]:
    """The five pinned 2025-12-05 2:1 split events (constants, not data reads)."""
    return {s: {SPLIT_EFFECTIVE_DATE: SPLIT_FACTOR} for s in SPLIT_SYMBOLS}
