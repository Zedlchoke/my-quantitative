"""Shared synthetic-panel helpers for lane_x tests (hand-computed cases)."""

from __future__ import annotations

import gzip
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine_x.divsplits import ExDateIndex  # noqa: E402
from engine_x.panel import NamePanel, PanelStore  # noqa: E402

_HERE = os.path.abspath(__file__)
# helpers.py -> tests -> lane_x -> EVENT-MECHANISMS-V1 -> control -> research -> worktree root
_WT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(_HERE))))))
STAGING_FIXTURES = os.path.join(_WT_ROOT, ".staging_eventmech", "fixtures")


def load_s7_fixture(name: str) -> dict:
    with open(os.path.join(STAGING_FIXTURES, name)) as fh:
        return json.load(fh)


def weekday_sessions(d0: str, d1: str) -> list[str]:
    """Weekday session-date grid [d0 .. d1] — long enough that the DVmed60
    eligibility floor (>= 30 trailing sessions) passes for mid-grid events."""
    import datetime as _dt
    out = []
    d = _dt.date.fromisoformat(d0)
    end = _dt.date.fromisoformat(d1)
    while d <= end:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += _dt.timedelta(days=1)
    return out


def make_panel(ticker: str, bars: list[tuple[str, float, float, float]],
               volumes: list[float] | None = None) -> NamePanel:
    """bars: (date, open, close) pairs; volume defaults to 1_000_000."""
    if volumes is None:
        volumes = [1_000_000.0] * len(bars)
    rows = [{"date": d, "open": o, "close": c, "volume": v}
            for (d, o, c), v in zip(bars, volumes)]
    return NamePanel(ticker, rows)


class FakeStore(PanelStore):
    """PanelStore pre-loaded with synthetic panels (no disk)."""

    def __init__(self, panels: dict[str, NamePanel]):
        self.panel_dir = "<synthetic>"
        self._cache = dict(panels)


class TempExDates(ExDateIndex):
    """ExDateIndex with a hand-set in-memory table."""

    def __init__(self, table: dict[str, tuple[set[str], set[str]]]):
        self.div_dir = "<synthetic>"
        self.splits_dir = "<synthetic>"
        self._div_stems, self._split_stems = {}, {}
        self._cache = dict(table)


NO_CA = TempExDates({})


def write_xml(tmpdir: str, cik: str, accession: str, doc_type: str,
              owners: list[dict], transactions: list[dict]) -> str:
    """Write a minimal form4 XML like the staged estate; returns the path."""
    d = os.path.join(tmpdir, cik, accession)
    os.makedirs(d, exist_ok=True)
    parts = ['<?xml version="1.0"?>', "<ownershipDocument>",
             f"    <documentType>{doc_type}</documentType>"]
    for o in owners:
        parts += [
            "    <reportingOwner>",
            "        <reportingOwnerId>",
            f"            <rptOwnerCik>{o['cik']}</rptOwnerCik>",
            f"            <rptOwnerName>{o.get('name', 'X')}</rptOwnerName>",
            "        </reportingOwnerId>",
            "        <reportingOwnerRelationship>",
            f"            <isDirector>{o.get('director', 0)}</isDirector>",
            f"            <isOfficer>{o.get('officer', 0)}</isOfficer>",
            "            <isTenPercentOwner>0</isTenPercentOwner>",
            "            <isOther>0</isOther>",
            "        </reportingOwnerRelationship>",
            "    </reportingOwner>",
        ]
    if transactions:
        parts.append("    <nonDerivativeTable>")
        for t in transactions:
            parts += [
                "        <nonDerivativeTransaction>",
                "            <transactionCoding>",
                f"                <transactionCode>{t['code']}</transactionCode>",
                "            </transactionCoding>",
                "            <transactionDate>",
                f"                <value>{t['date']}</value>",
                "            </transactionDate>",
                "            <transactionAmounts>",
                "                <transactionShares>",
                f"                    <value>{t['shares']}</value>",
                "                </transactionShares>",
                "                <transactionPricePerShare>",
                f"                    <value>{t['price']}</value>",
                "                </transactionPricePerShare>",
                "                <transactionAcquiredDisposedCode>",
                f"                    <value>{t.get('ad', 'A')}</value>",
                "                </transactionAcquiredDisposedCode>",
                "            </transactionAmounts>",
                "        </nonDerivativeTransaction>",
            ]
        parts.append("    </nonDerivativeTable>")
    parts.append("</ownershipDocument>")
    p = os.path.join(d, "ownership.xml")
    with open(p, "w") as fh:
        fh.write("\n".join(parts))
    return p


def write_gz_jsonl(path: str, rows: list[dict]) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz:
            gz.write("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows).encode())
    return path
