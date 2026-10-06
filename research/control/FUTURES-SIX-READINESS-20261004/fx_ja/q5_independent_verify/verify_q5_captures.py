#!/usr/bin/env python
"""Lane FX-JA-READINESS — Q5 independent-verify protocol.

Q5/Q6 archived data is usable only after independent VERIFY + reproduce inside
THIS worktree (standing ruling). Protocol executed here:
  1. OWN sha256 of the two sibling Q5 captures (pcal_69_6j_dl_20240904.xls,
     pcal_37_6a_20230916051415.json) — cross-checked against the sibling's
     recorded hashes (read-only cite).
  2. OWN parser (xlrd for the .xls; json for the .json) — no sibling code.
  3. Re-extract the quarterly lastTrade table; test explicitly whether the
     6A Mar/Jun 2023 and 6J 2023 quarters exist anywhere in the captures.
  4. Cross-check every extracted official lastTrade against the panel's
     observed last-bar session (identity validation; rule stays verbatim).
No network; no new fetch. Writes only under fx_ja/q5_independent_verify/.
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys

import pandas as pd
import xlrd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fx_ja_lib import jdump, sha256_file  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CAPS = ("/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep/"
        "research/control/FUTURES-P3-QUARANTINE-20261004/cal_permitted/captures")
DEEP = ("/Users/hoangminhlong/my-quantitative/.worktrees/futures-six-readiness/"
        "prep/research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis")
SIB_COVERAGE = ("/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/"
                "prep/research/control/FUTURES-P3-QUARANTINE-20261004/cal_permitted/"
                "cal_permitted_coverage.json")

SIB_RECORDED_SHA = {
    "pcal_69_6j_dl_20240904.xls":
        "09a85ef700d02a3f8d58f2d2d13c3157af200b516b133903d3173d38280aee18",
    "pcal_37_6a_20230916051415.json":
        "dad89c317110271cba5c62abd60fb14ece7772aaa104ddb1bb742b461a7b9741",
}


def parse_6j_xls(path):
    wb = xlrd.open_workbook(path)
    sh = wb.sheet_by_index(0)
    hdr = None
    rows = []
    for r in range(sh.nrows):
        vals = [str(sh.cell_value(r, c)).strip() for c in range(sh.ncols)]
        if vals[0] == "Contract Month":
            hdr = vals
            continue
        if hdr and vals[0]:
            rec = dict(zip(hdr, vals))
            m = re.match(
                r"^(January|February|March|April|May|June|July|August|September|"
                r"October|November|December) (\d{4}) ", rec["Contract Month"])
            rows.append({
                "contract_month": f"{m.group(1)[:3]} {m.group(2)}" if m else rec["Contract Month"],
                "code": rec.get("Product Code", ""),
                "first_trade": rec.get("First Trade", ""),
                "last_trade": rec.get("Last Trade", ""),
                "settlement": rec.get("Settlement", ""),
            })
    return rows


def parse_6a_json(path):
    d = json.load(open(path))
    out = []
    for rec in d:
        out.append({
            "contract_month": rec["contractMonth"],
            "code": rec["productCode"],
            "first_trade": rec["firstTrade"],
            "last_trade": rec["lastTrade"],
            "settlement": rec["settlement"],
        })
    return out


MONTH_NUM = {m: i + 1 for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])}


def to_quarter_rows(rows):
    out = []
    for r in rows:
        m = re.match(r"^(\w{3}) (\d{4})$", r["contract_month"])
        if not m:
            continue
        mon = MONTH_NUM.get(m.group(1))
        if mon in (3, 6, 9, 12):
            out.append({"contract_month": r["contract_month"],
                        "quarter": f"{m.group(2)}Q{(mon - 1) // 3 + 1}",
                        "code": r["code"],
                        "last_trade": r["last_trade"],
                        "first_trade": r["first_trade"]})
    return out


def main():
    res = {"schema": "fx_ja_q5_independent_verify@1",
           "task": "FUTURES-SIX-READINESS-20261004 / FX-JA-READINESS (Q5 protocol)",
           "protocol": "own sha256 + own parser + re-extract + panel cross-check; no new fetch"}

    # --- own hashes vs sibling-recorded -----------------------------------
    hashes = {}
    for fn, sib in SIB_RECORDED_SHA.items():
        p = os.path.join(CAPS, fn)
        mine = sha256_file(p)
        hashes[fn] = {"sha256_own": mine, "sha256_sibling_recorded": sib,
                      "match": mine == sib}
    res["sha256_verification"] = hashes

    # --- own parsers -------------------------------------------------------
    j6_rows = parse_6j_xls(os.path.join(CAPS, "pcal_69_6j_dl_20240904.xls"))
    a6_rows = parse_6a_json(os.path.join(CAPS, "pcal_37_6a_20230916051415.json"))
    a6_old = parse_6a_json(os.path.join(CAPS, "pcal_37_6a_20160518055320.json"))

    j6q = to_quarter_rows(j6_rows)
    a6q = to_quarter_rows(a6_rows)
    a6q_old = to_quarter_rows(a6_old)

    target = [f"{y}Q{q}" for y in ("2023", "2024", "2025") for q in (1, 2, 3, 4)]
    j6_in = {r["quarter"]: r["last_trade"] for r in j6q if r["quarter"] in target}
    a6_in = {r["quarter"]: r["last_trade"] for r in a6q if r["quarter"] in target}
    a6_old_in = {r["quarter"]: r["last_trade"] for r in a6q_old if r["quarter"] in target}
    missing_6j = [q for q in target if q not in j6_in]
    missing_6a = [q for q in target if q not in a6_in]

    res["6J_pcal_reextract"] = {
        "capture": "pcal_69_6j_dl_20240904.xls (sheet 'Product Calendar Sep 4 2024')",
        "n_rows_all": len(j6_rows), "n_quarterly_rows": len(j6q),
        "quarterly_span": [j6q[0]["quarter"], j6q[-1]["quarter"]] if j6q else None,
        "target_2023_2025_quarters_found": j6_in,
        "target_quarters_MISSING_from_capture": missing_6j,
        "serial_rows_in_capture": [r["code"] for r in j6_rows
                                   if r["code"] and not re.match(r"J1[HMUZ]\d\d", r["code"])],
        "extra_window_2026_2029_quarters": {r["quarter"]: r["last_trade"]
                                            for r in j6q if r["quarter"] >= "2026Q1"},
        "first_trade_corroboration_J1U27_2022_09_20": next(
            (r["first_trade"] for r in j6_rows if r["code"] == "J1U27"), None),
    }
    res["6A_pcal_reextract"] = {
        "capture": "pcal_37_6a_20230916051415.json (archived official product calendar @2023-09-16)",
        "n_rows_all": len(a6_rows), "n_quarterly_rows": len(a6q),
        "quarterly_span": [a6q[0]["quarter"], a6q[-1]["quarter"]] if a6q else None,
        "target_2023_2025_quarters_found": a6_in,
        "target_quarters_MISSING_from_capture": missing_6a,
        "second_capture_2016_05_18": {
            "quarters_in_target": a6_old_in,
            "quarterly_span": [a6q_old[0]["quarter"], a6q_old[-1]["quarter"]] if a6q_old else None,
        },
        "extra_window_2026_2028_quarters": {r["quarter"]: r["last_trade"]
                                            for r in a6q if r["quarter"] >= "2026Q1"},
    }

    # --- panel cross-check: official lastTrade vs observed last-bar session --
    reg6j = json.load(open(f"{DEEP}/6J_cache/contract_registry.json"))
    reg6a = pd.read_parquet(f"{DEEP}/6A_cache/registry.parquet")

    def last_session_from_registry(reg, is_json):
        if is_json:
            df = pd.DataFrame(reg)
            df["contract"] = df["symbol"] + "_" + df["year"].astype("Int64").astype(str)
            df = df.dropna(subset=["year"])
            df["last_bar"] = pd.to_datetime(df["last_bar"], utc=True, errors="coerce")
            return dict(zip(df["contract"], df["last_bar"]))
        reg = reg.copy()
        reg["last_bar"] = pd.to_datetime(reg["last_bar"], utc=True, errors="coerce")
        return dict(zip(reg["contract"], reg["last_bar"]))

    last6j = last_session_from_registry(reg6j, True)
    last6a = last_session_from_registry(reg6a, False)

    def sym_last(contract_key, lastmap):
        v = lastmap.get(contract_key)
        return str(pd.Timestamp(v).date()) if pd.notna(v) else None

    def cross_check(quarter_lasttrade, base):
        out = []
        for q, lt in sorted(quarter_lasttrade.items()):
            y, qq = q[:4], q[5]
            mon = {"1": "H", "2": "M", "3": "U", "4": "Z"}[qq]
            key = f"{base}{mon}{y[-1]}_{y}"
            obs = sym_last(key, last6j if base == "6J" else last6a)
            ok = None
            if obs:
                ok = (pd.Timestamp(obs) <= pd.Timestamp(lt))
            out.append({"quarter": q, "code_last_trade_official": lt,
                        "contract_key": key,
                        "observed_last_bar_session": obs,
                        "observed_le_official": ok})
        return out

    res["panel_cross_check"] = {
        "6J": cross_check(j6_in, "6J"),
        "6A": cross_check(a6_in, "6A"),
        "rule": ("expiry rule verbatim unchanged: observed last session must "
                 "be <= official lastTrade (09:16 CT cessation two business "
                 "days before 3rd-Wednesday delivery); equality expected "
                 "(final partial session prints bars)"),
    }

    # --- expiry-pointer ledger (dispatch's 58/68 and 62/68 re-derived) ------
    # universe: 17y x 4 quarterly HMUZ contracts 2010-2026 = 68 per symbol.
    # official pointers: FXCAL 2010-2022 complete (52/symbol; JPY_AUD_HYPOTHESES.md
    # line 34 "expiries 208/272 across the 4 FX symbols") + T2 captures:
    # 6J +6 (2024Q3..2025Q4), 6A +10 (2023Q3..2025Q4).
    res["expiry_pointer_ledger"] = {
        "universe_per_symbol": "68 quarterly contracts 2010-2026 (17y x HMUZ)",
        "6J": {"fxcal_official_2010_2022": 52,
               "q5_capture_2023_2025": len(j6_in),
               "union": 52 + len(j6_in),
               "still_not_obtained": 68 - 52 - len(j6_in),
               "missing_list": [q for q in
                                [f"{y}Q{q}" for y in ("2023", "2024", "2025", "2026")
                                 for q in (1, 2, 3, 4)]
                                if q not in j6_in]},
        "6A": {"fxcal_official_2010_2022": 52,
               "q5_capture_2023_2025": len(a6_in),
               "union": 52 + len(a6_in),
               "still_not_obtained": 68 - 52 - len(a6_in),
               "missing_list": [q for q in
                                [f"{y}Q{q}" for y in ("2023", "2024", "2025", "2026")
                                 for q in (1, 2, 3, 4)]
                                if q not in a6_in]},
        "dispatch_claim_check": {
            "claim": "6J 58/68 & 6A 62/68 expiry pointers",
            "reproduced": (52 + len(j6_in) == 58) and (52 + len(a6_in) == 62),
        },
    }

    res["cell_closures"] = {
        "6A_Mar2023_Jun2023": ("CONFIRMED_ABSENT_IN_CAPTURE -> NOT_OBTAINED "
                               "stands; neither 6A capture (2023-09-16 nor "
                               "2016-05-18) contains those contract months; "
                               "no new fetch permitted; derivation forbidden"),
        "6J_2023_quarters_plus_Mar_Jun_2024": (
            "CONFIRMED_ABSENT_IN_CAPTURE -> NOT_OBTAINED stands; the 6J "
            "capture (Sep-2024 calendar) begins at Sep 2024"),
        "official_expiry_sources_now_available": {
            "6J": sorted(j6_in), "6A": sorted(a6_in)},
    }

    jdump(res, os.path.join(HERE, "verify_q5_captures.json"))


if __name__ == "__main__":
    main()
