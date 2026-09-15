"""FOREX-NG5 P0 offline fixtures — parser/release-clock contracts (gates A4/A2/A7).

No network. Fixtures reproduce the header shapes measured 2026-09-15 from the
live CFTC bulk files (legacy 1999 human-readable style; disagg 2010 and TFF
2010 underscored styles incl. the "Swap__Positions_Short_All" quirk and the
trailing unnamed column).
"""
import hashlib
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research.assets.forex_ng5 import cot_parser, release_clock  # noqa: E402

LEGACY_HEADER = (
    '"Market and Exchange Names","As of Date in Form YYMMDD",'
    '"As of Date in Form YYYY-MM-DD","CFTC Contract Market Code",'
    '"CFTC Market Code in Initials","CFTC Region Code","CFTC Commodity Code",'
    '"Open Interest (All)","Noncommercial Positions-Long (All)",'
    '"Noncommercial Positions-Short (All)","Noncommercial Positions-Spreading (All)",'
    '"Commercial Positions-Long (All)","Commercial Positions-Short (All)",'
    '" Total Reportable Positions-Long (All)","Total Reportable Positions-Short (All)",'
    '"Nonreportable Positions-Long (All)","Nonreportable Positions-Short (All)",'
    '"Open Interest (Old)","Noncommercial Positions-Long (Old)",'
    '"Noncommercial Positions-Short (Old)","Noncommercial Positions-Spreading (Old)",'
    '"Commercial Positions-Long (Old)","Commercial Positions-Short (Old)",'
    '"Total Reportable Positions-Long (Old)","Total Reportable Positions-Short (Old)",'
    '"Nonreportable Positions-Long (Old)","Nonreportable Positions-Short (Old)",'
    '"Open Interest (Other)","Noncommercial Positions-Long (Other)",'
    '"Noncommercial Positions-Short (Other)","Noncommercial Positions-Spreading (Other)",'
    '"Commercial Positions-Long (Other)","Commercial Positions-Short (Other)",'
    '"Total Reportable Positions-Long (Other)","Total Reportable Positions-Short (Other)"'
)

CONSISTENT = dict(oi=1000, ncl=300, ncs=200, ncspr=50, cl=350, cs=400,
                  trl=700, trs=650, nrl=300, nrs=350)
# identity law (source-truth): ncl+cl+ncspr=700=trl; ncs+cs+ncspr=650=trs;
# oi=1000=trl+nrl=trs+nrs


def _legacy_row(name, as_of, iso, code, initials, oi, ncl, ncs, ncspr, cl, cs,
                trl, trs, nrl, nrs):
    old = ["0"] * 10
    other = ["0"] * 8
    return ",".join([f'"{name}"', f'"{as_of}"', f'"{iso}"', f'"{code}"',
                     f'"{initials}"', '"2"', '"021"',
                     str(oi), str(ncl), str(ncs), str(ncspr), str(cl), str(cs),
                     str(trl), str(trs), str(nrl), str(nrs)]
                    + old + other)


def _legacy_csv(rows):
    return LEGACY_HEADER + "\r\n" + "\r\n".join(rows) + "\r\n"


def test_legacy_parse_decimal_exact_and_identity():
    row = _legacy_row("BRITISH POUND STERLING - CHICAGO MERCANTILE EXCHANGE",
                      "990105", "1999-01-05", "096742", "BP", **CONSISTENT)
    out = cot_parser.parse_report_csv(_legacy_csv([row]), "legacy")
    assert out["regime"] == "legacy"
    assert out["rows_total"] == 1 and out["rejects"] == []
    rec = out["records"][0]
    assert rec["code"] == "096742"
    assert rec["report_date"] == "1999-01-05"
    assert rec["report_date_source"].startswith("as_of")
    assert rec["identity_ok"] is True
    v = rec["values"]
    assert isinstance(v["noncomm_long"], Decimal)
    assert v["noncomm_long"] == Decimal(300)
    assert not isinstance(v["noncomm_long"], float)
    assert v["noncomm_long"] + v["comm_long"] + v["noncomm_spread"] == v["tot_rept_long"]
    assert v["open_interest_all"] == v["tot_rept_long"] + v["nonrept_long"]


def test_legacy_leading_space_header_and_unmapped_columns():
    row = _legacy_row("CANADIAN DOLLAR - CHICAGO MERCANTILE EXCHANGE",
                      "990112", "1999-01-12", "090601", "CD", **CONSISTENT)
    out = cot_parser.parse_report_csv(_legacy_csv([row]), "legacy")
    # " Total Reportable Positions-Long (All)" (leading space) maps despite the space
    assert "tot_rept_long" in out["column_map"].values()
    assert any("Old" in c or "Other" in c for c in out["unmapped_columns"])
    assert out["records"][0]["code"] == "090601"


def test_malformed_count_rejects_row_never_coerced():
    good = _legacy_row("AUSTRALIAN DOLLAR - CHICAGO MERCANTILE EXCHANGE",
                       "990119", "1999-01-19", "232741", "AD", **CONSISTENT)
    parts = good.split(",")
    parts[8] = '"1,234"'  # thousands separator inside Noncommercial Positions-Long (All)
    bad = ",".join(parts)
    out = cot_parser.parse_report_csv(_legacy_csv([good, bad]), "legacy")
    assert len(out["records"]) == 1
    assert out["records"][0]["code"] == "232741"
    assert len(out["rejects"]) == 1
    assert out["rejects"][0]["field"] == "noncomm_long"
    assert "1,234" in out["rejects"][0]["raw"]


def test_malformed_date_rejects_row():
    good = _legacy_row("NEW ZEALAND DOLLAR - CHICAGO MERCANTILE EXCHANGE",
                       "990126", "1999-01-26", "112741", "NZ", **CONSISTENT)
    parts = good.split(",")
    parts[1] = '"99AABB"'   # broken YYMMDD
    parts[2] = '"1999-AABB"'  # and broken ISO fallback: no valid date column remains
    bad = ",".join(parts)
    out = cot_parser.parse_report_csv(_legacy_csv([good, bad]), "legacy")
    assert len(out["records"]) == 1
    assert out["rejects"][0]["field"] == "as_of_yymmdd"


def test_identity_mismatch_measured_not_fixed():
    bad_vals = dict(CONSISTENT, trl=699)  # parts long 700 != tot 699
    row = _legacy_row("USD INDEX - ICE FUTURES U.S.", "990202", "1999-02-02",
                      "098662", "DX", **bad_vals)
    out = cot_parser.parse_report_csv(_legacy_csv([row]), "legacy")
    rec = out["records"][0]
    assert rec["identity_ok"] is False
    assert "parts_long_ne_tot" in rec["identity_detail"]
    assert rec["code"] == "098662"


def test_dead_control_and_never_control_rows_parse_with_codes():
    dead = _legacy_row("DEUTSCHEMARK - CHICAGO MERCANTILE EXCHANGE",
                       "981229", "1998-12-29", "093741", "DM", **CONSISTENT)
    never = _legacy_row("FAKE CONTRACT - NOT AN EXCHANGE",
                        "990105", "1999-01-05", "999999", "ZZ", **CONSISTENT)
    out = cot_parser.parse_report_csv(_legacy_csv([dead, never]), "legacy")
    codes = {r["code"] for r in out["records"]}
    assert codes == {"093741", "999999"}  # zero-padding normalized


DISAGG_HEADER = (
    '"Market_and_Exchange_Names","As_of_Date_In_Form_YYMMDD","Report_Date_as_MM_DD_YYYY",'
    '"CFTC_Contract_Market_Code","CFTC_Market_Code","CFTC_Region_Code","CFTC_Commodity_Code",'
    '"Open_Interest_All","Prod_Merc_Positions_Long_All","Prod_Merc_Positions_Short_All",'
    '"Swap_Positions_Long_All","Swap__Positions_Short_All","Swap__Positions_Spread_All",'
    '"M_Money_Positions_Long_All","M_Money_Positions_Short_All","M_Money_Positions_Spread_All",'
    '"Other_Rept_Positions_Long_All","Other_Rept_Positions_Short_All","Other_Rept_Positions_Spread_All",'
    '"Tot_Rept_Positions_Long_All","Tot_Rept_Positions_Short_All",'
    '"NonRept_Positions_Long_All","NonRept_Positions_Short_All",'
    '"Open_Interest_Old","Prod_Merc_Positions_Long_Old","Prod_Merc_Positions_Short_Old",'
    '"Swap_Positions_Long_Old","Swap__Positions_Short_Old","Swap__Positions_Spread_Old",'
    '"M_Money_Positions_Long_Old","M_Money_Positions_Short_Old","M_Money_Positions_Spread_Old",'
    '"Other_Rept_Positions_Long_Old","Other_Rept_Positions_Short_Old","Other_Rept_Positions_Spread_Old"')


def test_disagg_parse_with_double_underscore_quirk():
    row = ('"BRITISH POUND STERLING - CHICAGO MERCANTILE EXCHANGE","100105","01/05/2010",'
           '"096742","BP","2","021","1000","400","300","100","150","50","200","250","0",'
           '"250","250","0","1000","1000","0","0"')
    row += "," + ",".join(['"0"'] * 12)  # Old triplet columns
    out = cot_parser.parse_report_csv(DISAGG_HEADER + "\r\n" + row + "\r\n", "disagg")
    rec = out["records"][0]
    assert rec["code"] == "096742"
    assert rec["report_date"] == "2010-01-05"
    assert rec["report_date_source"] == "report_date_mdy"
    v = rec["values"]
    assert v["prod_merc_long"] == Decimal(400)
    assert v["swap_short"] == Decimal(150)   # Swap__Positions_Short_All quirk maps
    assert v["mmoney_long"] == Decimal(200)  # M_Money_Positions_Long_All maps
    # identity law incl. per-category spreads: longs+spreads == tot_rept_long
    assert (v["prod_merc_long"] + v["swap_long"] + v["swap_spread"]
            + v["mmoney_long"] + v["other_rept_long"]) == v["tot_rept_long"]
    assert rec["identity_ok"] is True


TFF_HEADER = (
    '"Market_and_Exchange_Names","As_of_Date_In_Form_YYMMDD","Report_Date_as_MM_DD_YYYY",'
    '"CFTC_Contract_Market_Code","CFTC_Market_Code","CFTC_Region_Code","CFTC_Commodity_Code",'
    '"Open_Interest_All","Dealer_Positions_Long_All","Dealer_Positions_Short_All",'
    '"Dealer_Positions_Spread_All","Asset_Mgr_Positions_Long_All","Asset_Mgr_Positions_Short_All",'
    '"Asset_Mgr_Positions_Spread_All","Lev_Money_Positions_Long_All","Lev_Money_Positions_Short_All",'
    '"Lev_Money_Positions_Spread_All","Other_Rept_Positions_Long_All","Other_Rept_Positions_Short_All",'
    '"Other_Rept_Positions_Spread_All","Tot_Rept_Positions_Long_All","Tot_Rept_Positions_Short_All",'
    '"NonRept_Positions_Long_All","NonRept_Positions_Short_All","Change_in_Open_Interest_All",'
    '"Change_in_Dealer_Long_All","Change_in_Dealer_Short_All","Change_in_Dealer_Spread_All",'
    '"Change_in_Asset_Mgr_Long_All","Change_in_Asset_Mgr_Short_All","Change_in_Asset_Mgr_Spread_All",'
    '"Change_in_Lev_Money_Long_All","Change_in_Lev_Money_Short_All","Change_in_Lev_Money_Spread_All",'
    '""')  # trailing empty quoted column observed in the live file


def test_tff_parse_with_trailing_unnamed_column():
    row = ('"USD INDEX - ICE FUTURES U.S.","100112","01/12/2010","098662","DX","2","098",'
           '"1000","350","300","0","250","200","0","200","300","0","200","200","0",'
           '"1000","1000","0","0","10","0","0","0","0","0","0","0","0","0","0"')
    out = cot_parser.parse_report_csv(TFF_HEADER + "\r\n" + row + "\r\n", "tff")
    rec = out["records"][0]
    assert rec["code"] == "098662"
    v = rec["values"]
    assert v["dealer_long"] == Decimal(350)
    assert v["asset_mgr_short"] == Decimal(200)
    assert v["lev_fund_short"] == Decimal(300)
    assert rec["identity_ok"] is True


def test_unknown_schema_fails_closed():
    bad_header = '"Some Name","Some Date","Some Code","Some Number"'
    with pytest.raises(cot_parser.SchemaUnknownError) as exc:
        cot_parser.parse_report_csv(bad_header + "\r\n" + '"x","y","z","1"\r\n', "legacy")
    assert exc.value.regime == "legacy"
    assert exc.value.missing  # records which required fields are absent


def test_dedupe_exact_duplicates_vs_revision_conflicts():
    a1 = _legacy_row("BRITISH POUND STERLING - CHICAGO MERCANTILE EXCHANGE",
                     "990105", "1999-01-05", "096742", "BP", **CONSISTENT)
    a2 = a1  # byte-identical duplicate
    diff = dict(CONSISTENT, ncl=310)
    a3 = _legacy_row("BRITISH POUND STERLING - CHICAGO MERCANTILE EXCHANGE",
                     "990105", "1999-01-05", "096742", "BP", **diff)
    out = cot_parser.parse_report_csv(_legacy_csv([a1, a2, a3]), "legacy")
    dd = cot_parser.dedupe(out["records"])
    assert len(dd["unique"]) == 1
    assert dd["exact_duplicates"] == 1
    assert len(dd["conflicts"]) == 1
    assert dd["conflicts"][0]["key"] == ("096742", "1999-01-05")


def test_merge_sources_precedence_and_conflict():
    r1 = {"code": "096742", "report_date": "2015-06-30", "market_name": "GBP",
          "line": 2, "values": {"oi": Decimal(1)}}
    r2 = {"code": "096742", "report_date": "2015-06-30", "market_name": "GBP",
          "line": 7, "values": {"oi": Decimal(1)}}
    r3 = {"code": "096742", "report_date": "2015-06-30", "market_name": "GBP",
          "line": 3, "values": {"oi": Decimal(9)}}
    merged = cot_parser.merge_sources({"hist": [r1], "y2015": [r2, r3]},
                                      ["hist", "y2015"])
    assert set(merged["unique"]) == {("096742", "2015-06-30")}
    assert merged["unique"][("096742", "2015-06-30")]["source"] == "hist"
    assert merged["exact_duplicates"] == 1
    assert len(merged["conflicts"]) == 1
    assert merged["conflicts"][0]["sources"] == ["hist", "y2015"]


def test_redigest_deterministic():
    data = b"FOREX-NG5 raw bytes fixture"
    p = Path("/tmp/forex_ng5_test_redigest.bin")
    p.write_bytes(data)
    h1 = cot_parser.redigest_file(p)
    h2 = cot_parser.redigest_file(p)
    assert h1 == h2 == hashlib.sha256(data).hexdigest()
    assert cot_parser.sha256_hex(data) == h1


# --- A2 release-clock model -------------------------------------------------
def test_convention_release_plain_friday():
    c = release_clock.convention_release(date(2026, 9, 8))  # Tuesday
    assert c["release_date"] == "2026-09-11"  # Friday
    assert c["holiday_shifted"] is False
    assert c["grid_date"] == "2026-09-11"     # 16:00 NY same day, strictly after 15:30
    assert c["basis"] == "convention"


def test_convention_release_christmas_friday_shifts_to_monday():
    c = release_clock.convention_release(date(2026, 12, 22))  # Tue; Fri = Dec 25 holiday
    assert c["release_date"] == "2026-12-28"  # Monday
    assert c["holiday_shifted"] is True
    assert c["grid_date"] == "2026-12-28"


def test_convention_release_july4_observed_friday():
    c = release_clock.convention_release(date(2026, 6, 30))  # Fri Jul 3 = observed July 4
    assert c["release_date"] == "2026-07-06"  # Monday
    assert c["holiday_shifted"] is True


def test_schedule_as_of_mapping():
    assert release_clock.schedule_as_of(date(2026, 9, 11)) == date(2026, 9, 8)   # Fri -> Tue
    assert release_clock.schedule_as_of(date(2026, 1, 5)) == date(2025, 12, 30)  # Mon delayed -> prior Tue
    assert release_clock.schedule_as_of(date(2026, 6, 23)) == date(2026, 6, 16)  # Tue delayed -> original Tue


def test_evidenced_grid_marked_not_convention():
    g = release_clock.evidenced_grid(date(2025, 11, 19), "shutdown republication table")
    assert g["basis"] == "evidenced"
    assert g["grid_date"] == "2025-11-19"


def test_grid_instant_utc():
    iso = release_clock.grid_instant_utc(date(2026, 9, 11))
    assert iso.startswith("2026-09-11T20:00")  # 16:00 NY (EDT) = 20:00Z


def test_runner_module_imports_clean_and_constants_frozen():
    # importing the runner must have NO side effects (no lock, no network)
    from research.assets.forex_ng5 import p0_census_run as runner
    assert runner.USED_SPECS["GBPUSD"]["td_leg"] == "GBPUSD"
    assert runner.USED_SPECS["USDCAD"]["td_leg"] == "USDCAD"
    assert runner.USED_SPECS["AUDUSD"]["td_leg"] == "AUDUSD"
    assert runner.USED_SPECS["NZDUSD"]["td_leg"] == "NZDUSD"
    assert runner.USED_SPECS["USDCAD"]["codes_modern"] == ["090601", "090741"]
    assert runner.USD_INDEX == "098662"
    assert all(spec["entitled"] for spec in runner.USED_SPECS.values())
    assert runner.LEGACY_YEARS[0] == 1986 and runner.LEGACY_YEARS[-1] == 2026
    assert len(runner.FOLD_BOUNDS) == 3
    assert runner.NEVER_CONTROLS and runner.DEAD_CANDIDATE_CODES == ["094741", "093741"]
    assert runner.PAIR_NAME_RES["NZDUSD"].search("NZ DOLLAR - CHICAGO MERCANTILE EXCHANGE")
    assert not runner.PAIR_NAME_RES["NZDUSD"].search("AUSSIE-KIWI XRATE - NEW YORK COTTON EXCHANGE")


def test_integer_valued_decimal_notation_accepted():
    """TFF history file stores '93212.000000' — exact Decimal, never float."""
    row = ('"USD INDEX - ICE FUTURES U.S.","100112","01/12/2010","098662","DX","2","098",'
           '"1000.000000","350.000000","300.000000","0.000000","250.000000","200.000000",'
           '"0.000000","200.000000","300.000000","0.000000","200.000000","200.000000",'
           '"0.000000","1000.000000","1000.000000","0.000000","0.000000","10","0","0","0",'
           '"0","0","0","0","0","0","0"')
    out = cot_parser.parse_report_csv(TFF_HEADER + "\r\n" + row + "\r\n", "tff")
    rec = out["records"][0]
    assert rec["values"]["open_interest_all"] == Decimal(1000)
    assert isinstance(rec["values"]["open_interest_all"], Decimal)
    assert not isinstance(rec["values"]["open_interest_all"], float)
    assert rec["identity_ok"] is True
    # non-integral value must still be rejected (exactness contract)
    row2 = row.replace('"1000.000000"', '"1000.500000"', 1)
    out2 = cot_parser.parse_report_csv(TFF_HEADER + "\r\n" + row2 + "\r\n", "tff")
    assert len(out2["rejects"]) == 1
    assert out2["rejects"][0]["field"] == "open_interest_all"


def test_pair_name_regexes_cross_era():
    """Cross-era code instability is pinned: pair identity is NAME-anchored."""
    from research.assets.forex_ng5 import p0_census_run as runner
    assert runner.PAIR_NAME_RES["USDCAD"].search("CANADIAN DOLLAR - INTERNATIONAL MONETARY MARKET")
    assert runner.PAIR_NAME_RES["USDCAD"].search("CANADIAN DOLLAR - CHICAGO MERCANTILE EXCHANGE")
    assert not runner.PAIR_NAME_RES["USDCAD"].search("CANADIAN DOLLAR/JAPANESE YEN - X")
    assert runner.PAIR_NAME_RES["GBPUSD"].search("POUND STERLING - INTERNATIONAL MONETARY MARKET")
    assert runner.PAIR_NAME_RES["GBPUSD"].search("BRITISH POUND - CHICAGO MERCANTILE EXCHANGE")
    assert not runner.PAIR_NAME_RES["GBPUSD"].search("BRITISH POUND/SWISS FRANC CROSS")
    assert not runner.PAIR_NAME_RES["GBPUSD"].search("POUND/EURO CROSSRATE - NEW YORK COTTON EXCHANGE")


def test_alpha_suffix_codes_parse():
    import csv, io
    header = ('"Market_and_Exchange_Names","As_of_Date_In_Form_YYMMDD",'
              '"CFTC_Contract_Market_Code","Open_Interest_All",'
              '"Prod_Merc_Positions_Long_All","Prod_Merc_Positions_Short_All",'
              '"Swap_Positions_Long_All","Swap__Positions_Short_All","Swap__Positions_Spread_All",'
              '"M_Money_Positions_Long_All","M_Money_Positions_Short_All","M_Money_Positions_Spread_All",'
              '"Other_Rept_Positions_Long_All","Other_Rept_Positions_Short_All","Other_Rept_Positions_Spread_All",'
              '"Tot_Rept_Positions_Long_All","Tot_Rept_Positions_Short_All",'
              '"NonRept_Positions_Long_All","NonRept_Positions_Short_All"')
    row = '"E-MICRO AUD/USD - CME","100105","2327A","100","50","50","0","0","0","0","0","0","50","50","0","100","100","0","0"'
    out = cot_parser.parse_report_csv(header + "\r\n" + row + "\r\n", "disagg")
    assert out["records"][0]["code"] == "2327A"  # alnum adjunct codes kept verbatim
    assert out["rejects"] == []


def test_embedded_alpha_code_and_malformed_code():
    def mkrow(name, code):
        vals = ([f'"{name}"', '"100105"', '"01/05/2010"', f'"{code}"', '"XX"', '"2"', '"021"']
                + ['"100"']                                    # Open_Interest_All
                + ['"50"', '"50"']                             # Prod_Merc L/S
                + ['"25"', '"25"', '"5"']                      # Swap L/S/Spread
                + ['"0"', '"0"', '"0"']                        # M_Money L/S/Spread
                + ['"0"', '"0"', '"0"']                        # Other_Rept L/S/Spread
                + ['"80"', '"80"']                             # Tot_Rept L/S
                + ['"20"', '"20"']                             # NonRept L/S
                + ['"0"'] * 12)                                # Old block (incl OI_Old)
        return ",".join(vals)
    rows = DISAGG_HEADER + "\r\n" + \
        mkrow("WHEAT OPTIONS ADJUNCT - CBT", "022A13") + "\r\n" + \
        mkrow("BAD CODE MARKET", "NOT!A/CODE") + "\r\n"
    out = cot_parser.parse_report_csv(rows, "disagg")
    codes = [r["code"] for r in out["records"]]
    assert "022A13" in codes
    assert len(out["rejects"]) == 1
    assert out["rejects"][0]["field"] == "cftc_contract_market_code"
    assert out["records"][0]["identity_ok"] is True


def test_wide_row_rejected_fail_closed():
    header_cells = TFF_HEADER.count(",") + 1
    wide = (TFF_HEADER + "\r\n"
            + '"' + '","'.join(["X"] * (header_cells + 10)) + '"\r\n')
    # a row wider than the header must be rejected, not parsed positionally
    out = cot_parser.parse_report_csv(wide, "tff")
    assert out["records"] == []
    assert out["rejects"] and out["rejects"][0]["reason"] == "row_wider_or_narrower_than_header"


def test_trailing_plus_consolidation_code_verbatim():
    row = ('"E-MICRO S&P 500 CONSOLIDATED - CME","100112","01/12/2010","12460+",'
           '"XX","2","098","100","50","50","0","25","25","0","0","0","0","0","0","0",'
           '"80","80","20","20","10","0","0","0","0","0","0","0","0","0","0"')
    out = cot_parser.parse_report_csv(TFF_HEADER + "\r\n" + row + "\r\n", "tff")
    assert [r["code"] for r in out["records"]] == ["12460+"]
    assert out["rejects"] == []
