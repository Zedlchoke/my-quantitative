"""Offline tests for raw/adjusted/distribution reconciliation (A2).

Builds minimal synthetic OOXML workbooks in tmp_path (stdlib-only writer) and
hand-computed total-return fixtures, so no network and no openpyxl is needed.
"""

import datetime as dt
import zipfile

import pytest

from research.stocks_free_v1.reconciliation import (
    compare_series_on_common_dates,
    distribution_coverage_conflicts,
    nav_vs_close_conflicts,
    parse_spdr_distributions,
    parse_ssga_nav_history,
    reconstruct_total_return,
)

XLSX_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def _write_minimal_xlsx(path, rows, strings=()):
    """Write a single-sheet xlsx with inline strings/numbers via stdlib."""
    shared = list(strings)

    def cell(ref, value):
        if value is None:
            return ""
        if isinstance(value, str):
            shared.append(value)
            return (
                f'<c r="{ref}" t="s"><v>{shared.index(value)}</v></c>'
            )
        return f'<c r="{ref}"><v>{value}</v></c>'

    body_rows = []
    for ri, row in enumerate(rows, start=1):
        cells = "".join(cell(f"{chr(ord('A') + ci)}{ri}", v) for ci, v in enumerate(row))
        body_rows.append(f'<row r="{ri}">{cells}</row>')
    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<worksheet xmlns="{XLSX_MAIN}">{"".join(body_rows)}</worksheet>'
    )
    sst_items = "".join(f"<si><t>{s}</t></si>" for s in shared)
    sst_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<sst xmlns="{XLSX_MAIN}" count="{len(shared)}" uniqueCount="{len(shared)}">'
        f"{sst_items}</sst>"
    )
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types/>')
        zf.writestr("xl/workbook.xml", '<?xml version="1.0"?><workbook/>')
        zf.writestr("xl/sharedStrings.xml", sst_xml)
        zf.writestr("xl/worksheets/sheet1.xml", sheet_xml)


@pytest.fixture()
def navhist_xlsx(tmp_path):
    # descending dates as SSGA publishes: Date | NAV | Shares | Net Assets
    _write_minimal_xlsx(
        tmp_path / "navhist-us-en-tst.xlsx",
        [
            ["Fund Name:", "Test SPDR Fund"],
            ["Ticker Symbol:", "TST"],
            [],
            ["Date", "NAV", "Shares Outstanding", "Total Net Assets"],
            ["05-Jan-2026", "101.000000", "1.0E9", "1.01E11"],
            ["02-Jan-2026", "100.000000", "1.0E9", "1.00E11"],
        ],
    )
    return tmp_path / "navhist-us-en-tst.xlsx"


@pytest.fixture()
def dist_xlsx(tmp_path):
    _write_minimal_xlsx(
        tmp_path / "spdr-etf-historical-distributions.xlsx",
        [
            [
                "FUND NAME", "TICKER", "CUSIP", "EX-DATE", "RECORD DATE",
                "PAYABLE DATE", "DIVIDEND ($)", "SHORT TERM CAPITAL GAIN ($)",
                "LONG TERM CAPITAL GAIN ($)",
            ],
            ["Test SPDR Fund", "TST", "000000000",
             "01/05/2026", "01/05/2026", "01/07/2026", "1.0", "", ""],
            ["Other Fund", "OTH", "111111111",
             "01/05/2026", "01/05/2026", "01/07/2026", "9.9", "", ""],
        ],
    )
    return tmp_path / "spdr-etf-historical-distributions.xlsx"


def test_parse_nav_history(navhist_xlsx):
    rows = parse_ssga_nav_history(navhist_xlsx)
    assert [r["date"] for r in rows] == [dt.date(2026, 1, 2), dt.date(2026, 1, 5)]
    assert rows[0]["nav"] == 100.0
    assert rows[1]["nav"] == 101.0


def test_parse_distributions_filters_ticker(dist_xlsx):
    rows = parse_spdr_distributions(dist_xlsx, ticker="TST")
    assert len(rows) == 1
    assert rows[0]["ex_date"] == dt.date(2026, 1, 5)
    assert rows[0]["amount"] == 1.0
    assert rows[0]["dividend"] == 1.0 and rows[0]["lt_capital_gain"] == 0.0


def test_total_return_reconstruction_matches_hand_computed(navhist_xlsx, dist_xlsx):
    nav_rows = parse_ssga_nav_history(navhist_xlsx)
    nav = {r["date"]: r["nav"] for r in nav_rows}
    dists = parse_spdr_distributions(dist_xlsx, ticker="TST")
    tr = reconstruct_total_return(nav, dists)
    # hand computation: base 1.0 on 01-02; on 01-05 ex-date div 1.0:
    # f = (101 + 1)/100 = 1.02
    assert tr[dt.date(2026, 1, 2)] == pytest.approx(1.0)
    assert tr[dt.date(2026, 1, 5)] == pytest.approx(1.02)


def test_total_return_without_distribution_is_price_return(navhist_xlsx):
    nav_rows = parse_ssga_nav_history(navhist_xlsx)
    nav = {r["date"]: r["nav"] for r in nav_rows}
    tr = reconstruct_total_return(nav, [])
    assert tr[dt.date(2026, 1, 5)] == pytest.approx(1.01)


def test_distribution_coverage_conflicts(navhist_xlsx, dist_xlsx):
    nav_rows = parse_ssga_nav_history(navhist_xlsx)
    dates = [r["date"] for r in nav_rows]
    far = {"ex_date": dt.date(2026, 2, 2), "amount": 0.5, "ticker": "TST"}
    conflicts = distribution_coverage_conflicts(dates, [far])
    assert conflicts == [
        {"ex_date": dt.date(2026, 2, 2), "amount": 0.5, "ticker": "TST"}
    ]


def test_compare_series_tolerance_and_conflicts():
    d1, d2, d3 = dt.date(2026, 1, 2), dt.date(2026, 1, 5), dt.date(2026, 1, 6)
    a = {d1: 100.0, d2: 101.0, d3: 102.0}
    # d2 inside tolerance (5e-7 rel), d3 beyond it (~0.0097 rel)
    b = {d1: 100.0, d2: 101.0 * (1 + 5e-7), d3: 103.0}
    rep = compare_series_on_common_dates(a, b, tolerance_rel=1e-6)
    assert rep.n_common_dates == 3
    assert len(rep.conflicts) == 1
    assert rep.conflicts[0]["date"] == d3.isoformat()
    assert rep.status == "CONFLICT"
    assert rep.max_abs_rel_diff == pytest.approx(abs(102.0 - 103.0) / 103.0, rel=1e-9)


def test_compare_series_pass_within_tolerance():
    d1, d2 = dt.date(2026, 1, 2), dt.date(2026, 1, 5)
    a = {d1: 100.0, d2: 101.0}
    b = {d1: 100.0, d2: 101.0 * (1 + 5e-9)}
    rep = compare_series_on_common_dates(a, b, tolerance_rel=1e-6)
    assert rep.status == "PASS"
    assert rep.conflicts == []


def test_compare_series_no_common_dates():
    rep = compare_series_on_common_dates(
        {dt.date(2026, 1, 2): 1.0}, {dt.date(2027, 1, 4): 1.0}, 1e-6
    )
    assert rep.status == "NO_COMMON_DATES"


def test_nav_vs_close_conflicts_declared_as_premium_discount():
    d1 = dt.date(2026, 1, 2)
    rep = nav_vs_close_conflicts(
        {d1: 100.0}, {d1: 100.5}, tolerance_rel=0.001
    )
    # 0.5% premium is beyond a 0.1% tolerance: recorded, not silently passed
    assert rep.status == "CONFLICT"
    # relative to the NAV denominators (series_b): |close - nav| / nav
    assert rep.conflicts[0]["rel_diff"] == pytest.approx(0.005, rel=1e-9)
