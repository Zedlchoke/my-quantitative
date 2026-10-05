#!/usr/bin/env python3
"""Lane D delta re-verification (wbap-d-verify-r1) — INDEPENDENT recomputation.

Fresh implementation written for the R1 delta pass (NOT measure_a2.py, NOT the
R0 verify_d.py). Read-only over the corpus. Schema/coverage counting ONLY —
no win-prob metric is computed anywhere. Prints a JSON report to stdout.

Delta scope:
  D-1  franchise lineage rebranch (LVA := UTA->SAN->LVA; DAL := DET->TUL->DAL;
       LAS continuous) re-measured from stats schedule bytes + table/spec text
  MIN  D-2 ESPN DET->TUL mislabel span 2002-2009; D-3 alias per-token
       breakdown (WIL x3, STE x2 within 21 rows); D-4 Cup finals = 6
  NOREG census / filter law / timestamp laws / row-level join re-measured
"""
import hashlib
import json
import os

import pandas as pd

RAW = os.path.expanduser("~/.my-quantitative-data/wnba-v1/raw")
PREP = os.path.expanduser("~/.my-quantitative-data/wnba-prep-v1")
R = {}

# ------------------------------------------------------------------ load
espn = pd.concat(
    [pd.read_csv(os.path.join(RAW, "espn_schedules", f"wnba_schedule_{y}.csv"),
                 low_memory=False).assign(season_file=y) for y in range(2002, 2027)],
    ignore_index=True)
stats = pd.concat(
    [pd.read_csv(os.path.join(RAW, "wnba_stats_schedules", f"wnba_schedule_{y}.csv.gz"),
                 compression="gzip").assign(season_file=y) for y in range(1997, 2027)],
    ignore_index=True)

# ================================================================== D-1
# season presence + per-season row counts by stats abbreviation (home or away slot)
LONG = stats.melt(id_vars=["season_file"], value_vars=["home_team_abbreviation", "away_team_abbreviation"],
                  var_name="slot", value_name="abbr")
NAME = stats.melt(id_vars=["season_file"], value_vars=["home_team_name", "away_team_name"],
                  var_name="slot", value_name="tname")

def abbr_season_rows(a):
    sub = LONG[LONG["abbr"] == a]
    per = sub.groupby("season_file").size()
    return {"seasons": sorted(int(y) for y in per.index),
            "rows_by_season": {int(y): int(v) for y, v in per.items()},
            "rows_total": int(per.sum())}

def name_seasons(n):
    per = NAME[NAME["tname"] == n].groupby("season_file").size()
    return {int(y): int(v) for y, v in per.items()}

R["d1_stats_abbr"] = {a: abbr_season_rows(a) for a in ("UTA", "SAN", "LVA", "DET", "TUL", "DAL", "LAS")}

# San Antonio display-name eras from bytes
R["d1_san_names"] = {"San Antonio Silver Stars": name_seasons("San Antonio Silver Stars"),
                     "San Antonio Stars": name_seasons("San Antonio Stars")}
R["d1_san_names_contiguous_2003_2017"] = sorted(
    set(R["d1_san_names"]["San Antonio Silver Stars"]) | set(R["d1_san_names"]["San Antonio Stars"])) == list(range(2003, 2018))

# league census of distinct (non-alias) stats abbreviations per season, 2015-2018
ALIAS = {"EAST", "WEST", "ALL", "USA", "DEL", "PAR", "WIL", "STE", "CLA", "COL", "SPO", "COOP", "WNBASTARS"}
R["d1_coexistence"] = {}
for y in (2015, 2016, 2017, 2018):
    ab = set(LONG.loc[LONG["season_file"] == y, "abbr"].dropna()) - ALIAS
    san_rows = int((LONG["season_file"].eq(y) & LONG["abbr"].eq("SAN")).sum())
    dal_rows = int((LONG["season_file"].eq(y) & LONG["abbr"].eq("DAL")).sum())
    tul_rows = int((LONG["season_file"].eq(y) & LONG["abbr"].eq("TUL")).sum())
    lva_rows = int((LONG["season_file"].eq(y) & LONG["abbr"].eq("LVA")).sum())
    R["d1_coexistence"][str(y)] = {"n_distinct_abbrs": len(ab), "has_SAN": "SAN" in ab,
                                   "has_DAL": "DAL" in ab, "has_TUL": "TUL" in ab,
                                   "has_LVA": "LVA" in ab, "SAN_rows": san_rows,
                                   "DAL_rows": dal_rows, "TUL_rows": tul_rows, "LVA_rows": lva_rows}
R["d1_san_dal_coexist_2016_and_2017"] = bool(
    R["d1_coexistence"]["2016"]["has_SAN"] and R["d1_coexistence"]["2016"]["has_DAL"]
    and R["d1_coexistence"]["2017"]["has_SAN"] and R["d1_coexistence"]["2017"]["has_DAL"])
R["d1_boundary_pairs"] = {
    "TUL_last_season": max(R["d1_stats_abbr"]["TUL"]["seasons"]),
    "DAL_first_season": min(R["d1_stats_abbr"]["DAL"]["seasons"]),
    "SAN_last_season": max(R["d1_stats_abbr"]["SAN"]["seasons"]),
    "LVA_first_season": min(R["d1_stats_abbr"]["LVA"]["seasons"]),
    "UTA_last_season": max(R["d1_stats_abbr"]["UTA"]["seasons"]),
    "SAN_first_season": min(R["d1_stats_abbr"]["SAN"]["seasons"]),
    "DET_first_season": min(R["d1_stats_abbr"]["DET"]["seasons"]),
    "DET_last_season": max(R["d1_stats_abbr"]["DET"]["seasons"]),
    "TUL_first_season": min(R["d1_stats_abbr"]["TUL"]["seasons"]),
    "LAS_seasons_continuous_1997_2026": R["d1_stats_abbr"]["LAS"]["seasons"] == list(range(1997, 2027)),
    "LAS_rows_total": R["d1_stats_abbr"]["LAS"]["rows_total"],
}

# corrected team_key_table.csv encoding (parse the CSV, do not trust its layout)
tk = pd.read_csv(os.path.join(PREP, "team_key_table.csv"), dtype=str)
R["d1_table_keys"] = sorted(tk["franchise_key"].tolist())
R["d1_table_rows"] = int(len(tk))


def row_of(key):
    r = tk[tk["franchise_key"] == key]
    return None if r.empty else r.iloc[0].to_dict()


lva_r, dal_r, las_r = row_of("LVA"), row_of("DAL"), row_of("LAS")
R["d1_table_encoding"] = {
    "old_keys_gone": not any(k in set(tk["franchise_key"]) for k in ("SAN_DAL", "DET_TUL")),
    "old_stats_abbr_token_gone": not any("SAN_DAL" in s or "DET_TUL" in s
                                         for s in tk.fillna("").astype(str).values.ravel().tolist()),
    "LVA": None if lva_r is None else {
        "stats_abbrs": lva_r["stats_abbrs"].split("; "), "seasons": [lva_r["first_season"], lva_r["last_season"]],
        "modern_key_first": lva_r["stats_abbrs"].split("; ")[0] == "LVA",
        "covers_UTA": "UTA" in lva_r["stats_abbrs"].split("; ")},
    "DAL": None if dal_r is None else {
        "stats_abbrs": dal_r["stats_abbrs"].split("; "), "seasons": [dal_r["first_season"], dal_r["last_season"]],
        "modern_key_first": dal_r["stats_abbrs"].split("; ")[0] == "DAL",
        "covers_DET_TUL": {"DET", "TUL"} <= set(dal_r["stats_abbrs"].split("; "))},
    "LAS": None if las_r is None else {
        "stats_abbrs": las_r["stats_abbrs"].split("; "), "seasons": [las_r["first_season"], las_r["last_season"]]},
}
# cross-check the table's season spans against measured bytes
R["d1_table_vs_bytes"] = {
    "LVA_span_1997_2026": lva_r is not None and (lva_r["first_season"], lva_r["last_season"]) == ("1997", "2026"),
    "LVA_lineage_eras_measured": (min(R["d1_stats_abbr"]["UTA"]["seasons"]) == 1997
                                  and max(R["d1_stats_abbr"]["SAN"]["seasons"]) == 2017
                                  and min(R["d1_stats_abbr"]["LVA"]["seasons"]) == 2018),
    "DAL_span_1998_2026": dal_r is not None and (dal_r["first_season"], dal_r["last_season"]) == ("1998", "2026"),
    "DAL_lineage_eras_measured": (min(R["d1_stats_abbr"]["DET"]["seasons"]) == 1998
                                  and max(R["d1_stats_abbr"]["TUL"]["seasons"]) == 2015
                                  and min(R["d1_stats_abbr"]["DAL"]["seasons"]) == 2016),
    "LAS_span_1997_2026": las_r is not None and (las_r["first_season"], las_r["last_season"]) == ("1997", "2026"),
}

# spec section-2 text: corrected rows present, wrong-branch encoding gone
spec = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "A_DATA",
                         "GAME_UNIVERSE_SPEC_WNBA_1997PLUS.md"), encoding="utf-8").read()
sec2 = spec.split("## 2.", 1)[1].split("## 3.", 1)[0]
R["d1_spec_text"] = {
    "SAN_DAL_absent": "SAN_DAL" not in spec,
    "DET_TUL_absent": "DET_TUL" not in spec,
    "merger_wording_absent_sec2": "merger season" not in sec2 and "2003–2015" not in sec2,
    "LVA_uta_san_lineage_present": "UTA Utah Starzz 1997–2002" in sec2 and "LVA Las Vegas Aces 2018–" in sec2,
    "DAL_det_tul_lineage_present": "DET Detroit Shock 1998–2009" in sec2 and "DAL Dallas Wings 2016–" in sec2,
    "LAS_continuous_present": "never relocates" in sec2 or "continuous" in sec2,
    "twenty_keys_stated": "20 franchise keys" in sec2,
    "coexistence_evidence_present": "2017 (SAN 34/34 rows, DAL 34/35 rows)" in sec2 or "coexist as 2 of 12" in sec2,
}

# ================================================================== D-2 MINOR
det = espn[espn["home_display_name"].eq("Detroit Shock") | espn["away_display_name"].eq("Detroit Shock")]
det_per = det.groupby("season_file").size()
bad = det[(~det["home_abbreviation"].eq("TUL") & det["home_display_name"].eq("Detroit Shock"))
          | (~det["away_abbreviation"].eq("TUL") & det["away_display_name"].eq("Detroit Shock"))]
R["d2_espn_detroit"] = {
    "rows_total": int(len(det)),
    "seasons": sorted(int(y) for y in det_per.index),
    "rows_by_season": {int(y): int(v) for y, v in det_per.items()},
    "all_rows_labelled_TUL": bool(len(bad) == 0),
    "non_TUL_rows": int(len(bad)),
    "abbr_DET_anywhere_on_espn": int((espn["home_abbreviation"].eq("DET") | espn["away_abbreviation"].eq("DET")).sum()),
    "home_vs_away_split": {"home_slots": int(det["home_display_name"].eq("Detroit Shock").sum()),
                           "away_slots": int(det["away_display_name"].eq("Detroit Shock").sum())},
}
# stats DET per-season for the same-games cross-check
R["d2_stats_DET_rows_by_season"] = {int(y): int(v) for y, v in
                                    LONG[LONG["abbr"] == "DET"].groupby("season_file").size().items()}

# ================================================================== D-3 MINOR
alias = espn[espn["home_abbreviation"].isin(ALIAS) | espn["away_abbreviation"].isin(ALIAS)]
tok = sorted(set(alias["home_abbreviation"].dropna()) | set(alias["away_abbreviation"].dropna()))
R["d3_alias"] = {
    "rows": int(len(alias)),
    "distinct_tokens": len(tok),
    "tokens": tok,
    "per_token_slots": {a: int(alias["home_abbreviation"].eq(a).sum() + alias["away_abbreviation"].eq(a).sum())
                        for a in tok},
    "WIL_rows": int(alias["home_abbreviation"].eq("WIL").sum() + alias["away_abbreviation"].eq("WIL").sum()),
    "STE_rows": int(alias["home_abbreviation"].eq("STE").sum() + alias["away_abbreviation"].eq("STE").sum()),
    "stats_side_rows": int((stats["home_team_abbreviation"].isin(ALIAS)
                            | stats["away_team_abbreviation"].isin(ALIAS)).sum()),
}
WIL = alias[alias["home_abbreviation"].eq("WIL") | alias["away_abbreviation"].eq("WIL")]
STE = alias[alias["home_abbreviation"].eq("STE") | alias["away_abbreviation"].eq("STE")]
R["d3_WIL_seasons"] = sorted(int(y) for y in set(WIL["season_file"]))
R["d3_STE_seasons"] = sorted(int(y) for y in set(STE["season_file"]))

# ================================================================== D-4 MINOR
cup = espn[espn["notes_headline"].fillna("").str.contains("Cup", case=False)]
champ_hl = cup[cup["notes_headline"].fillna("").str.contains("Cup Championship", case=False)]
c21 = cup[(cup["season_file"] == 2021) & cup["neutral_site"].astype(str).str.upper().isin(["TRUE", "1"])]
finals = pd.concat([champ_hl, c21]).drop_duplicates("game_id")
fin_recs = []
for _, f in finals.sort_values("season_file").iterrows():
    season_cup = cup[cup["season_file"] == f["season_file"]]
    is_last = f["date"] == season_cup["date"].max()
    fin_recs.append({"season": int(f["season_file"]), "date_utc": f["date"], "game_id": str(f["game_id"]),
                     "home": f["home_display_name"], "away": f["away_display_name"],
                     "headline": f["notes_headline"], "neutral": str(f["neutral_site"]),
                     "is_last_scheduled_cup_game_of_season": bool(is_last)})
neu_cup_2021 = cup[(cup["season_file"] == 2021)]
R["d4_cup"] = {
    "cup_rows_total": int(len(cup)),
    "cup_by_season": {int(k): int(v) for k, v in cup.groupby("season_file").size().items()},
    "cup_season_type": {str(k): int(v) for k, v in cup["season_type"].value_counts().items()},
    "championship_headline_rows": int(len(champ_hl)),
    "finals_total": int(len(finals)),
    "finals": fin_recs,
    "finals_one_per_cup_season": sorted(int(x["season"]) for x in fin_recs) == list(range(2021, 2027)),
    "all_finals_last_scheduled": all(x["is_last_scheduled_cup_game_of_season"] for x in fin_recs),
    "neutral_cup_rows_2021": {int(k): int(v) for k, v in neu_cup_2021[
        neu_cup_2021["neutral_site"].astype(str).str.upper().isin(["TRUE", "1"])].groupby("season_file").size().items()},
    "chi_was_2024_06_06": espn[espn["game_id"].astype(str) == "401590018"][
        ["game_id", "date", "home_display_name", "away_display_name", "notes_headline",
         "neutral_site"]].astype(str).to_dict("records") or
        cup[(cup["season_file"] == 2024) & cup["date"].astype(str).str.startswith("2024-06-06")][
            ["game_id", "date", "home_display_name", "away_display_name", "notes_headline",
             "neutral_site"]].astype(str).to_dict("records"),
}
R["d4_measurements_a2"] = {
    "rows_championship": json.load(open(os.path.join(PREP, "measurements_a2.json"))).get(
        "espn_commissioners_cup", {}),
}

# ================================================================== NO-REGRESSION
R["ng_identity"] = {
    "espn_rows": int(len(espn)), "espn_unique_ids": int(espn["game_id"].nunique()),
    "espn_seasons": int(espn["season_file"].nunique()),
    "stats_rows": int(len(stats)), "stats_unique_ids": int(stats["game_id"].nunique()),
    "stats_seasons": int(stats["season_file"].nunique()),
}

pre = espn[espn["status_type_state"] != "post"]
R["ng_filter"] = {
    "nonpost_rows": int(len(pre)),
    "nonpost_all_2026": bool((pre["season_file"] == 2026).all()),
    "nonpost_prefilled_00": int(((pd.to_numeric(pre["home_score"], errors="coerce") == 0)
                                 & (pd.to_numeric(pre["away_score"], errors="coerce") == 0)).sum()),
    "nonpost_null_scores": int((pd.to_numeric(pre["home_score"], errors="coerce").isna()
                                | pd.to_numeric(pre["away_score"], errors="coerce").isna()).sum()),
}
forf = espn[espn["status_type_detail"].fillna("").str.contains("Forfeit", case=False)]
post = espn[espn["status_type_detail"].fillna("").str.contains("Postponed", case=False)]
R["ng_filter"]["forfeit_rows"] = int(len(forf))
R["ng_filter"]["forfeit_id"] = forf["game_id"].astype(str).tolist()
R["ng_filter"]["postponed_rows"] = int(len(post))
R["ng_filter"]["postponed_ids"] = post["game_id"].astype(str).tolist()
R["ng_filter"]["alias_rows"] = int(len(alias))
R["ng_filter"]["tbd_rows"] = int((espn["home_display_name"].fillna("").str.upper().eq("TBD")
                                  | espn["away_display_name"].fillna("").str.upper().eq("TBD")).sum())
R["ng_filter"]["neutral_rows"] = int((espn["neutral_site"].astype(str).str.upper().isin(["TRUE", "1"])).sum())

hp, ap = pd.to_numeric(stats["home_pts"], errors="coerce"), pd.to_numeric(stats["away_pts"], errors="coerce")
zz = stats[(hp == 0) & (ap == 0)]
R["ng_filter"]["stats_zero_zero_rows"] = int(len(zz))
R["ng_filter"]["stats_zero_zero_ids"] = zz["game_id"].astype(str).tolist()
R["ng_filter"]["stats_null_pts_rows"] = int((hp.isna() | ap.isna()).sum())

played = espn[espn["status_type_state"] == "post"]
played = played[~played["status_type_detail"].fillna("").str.contains("Forfeit|Postponed", case=False)]
played = played[~played["home_abbreviation"].isin(ALIAS) & ~played["away_abbreviation"].isin(ALIAS)]
rs = played[played["season_type"] == 2]
po = played[played["season_type"] == 3]
cupr = rs[rs["notes_headline"].fillna("").str.contains("Cup", case=False)]
s_played = stats[~((hp == 0) & (ap == 0))]
s_played = s_played[~s_played["home_team_abbreviation"].isin(ALIAS)
                    & ~s_played["away_team_abbreviation"].isin(ALIAS)]
s_rs = s_played[s_played["season_type"] == "regular-season"]
s_po = s_played[s_played["season_type"] == "playoffs"]
R["ng_census"] = {
    "espn_real": int(len(played)),
    "espn_rs_xcup": int(len(rs) - len(cupr)),
    "espn_cup": int(len(cupr)),
    "espn_po": int(len(po)),
    "espn_identity_sum": int(len(rs) - len(cupr)) + int(len(cupr)) + int(len(po)),
    "stats_real": int(len(s_played)),
    "stats_rs": int(len(s_rs)),
    "stats_po": int(len(s_po)),
    "stats_identity_sum": int(len(s_rs)) + int(len(s_po)),
    "stats_pre2002_real": int((s_played["season_file"] <= 2001).sum()),
}

# timestamps
eq_gdt = eq_sd = tot = 0
for y in range(2002, 2027):
    d = espn[espn["season_file"] == y]
    a = pd.to_datetime(d["date"], utc=True, format="ISO8601")
    b = pd.to_datetime(d["game_date_time"], utc=True, format="ISO8601")
    c = pd.to_datetime(d["start_date"], utc=True, format="ISO8601")
    tot += len(d)
    eq_gdt += int((a == b).sum())
    eq_sd += int((a == c).sum())
R["ng_ts"] = {"date_eq_gamedatetime": f"{eq_gdt}/{tot}", "date_eq_start_date": f"{eq_sd}/{tot}"}

# row-level join: pass 1 unique ET-date window, pass 2 exact score
def norm(s):
    return str(s).strip().lower()


e2 = played.copy()
e2["etd"] = pd.to_datetime(e2["date"], utc=True, format="ISO8601").dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
e2["k"] = [tuple(sorted(x)) for x in zip(e2["home_display_name"].map(norm), e2["away_display_name"].map(norm))]
s2 = s_played.copy()
s2["k"] = [tuple(sorted(x)) for x in zip(s2["home_team_name"].map(norm), s2["away_team_name"].map(norm))]
s2["gid"] = s2["game_id"].astype(str)
sidx = {}
for gid, k, gd, hpa, apa in zip(s2["gid"], s2["k"], s2["game_date"], s2["home_pts"], s2["away_pts"]):
    sidx.setdefault(k, []).append((gd, gid, int(hpa), int(apa)))

match, consumed, offc, amb = {}, set(), {}, 0
for gid, k, etd, hs, as_ in zip(e2["game_id"].astype(str), e2["k"], e2["etd"],
                                e2["home_score"], e2["away_score"]):
    d0 = pd.Timestamp(etd)
    seen = {}
    for off in (-1, 0, 1):
        want = str((d0 + pd.Timedelta(days=off)).date())
        for gd, sgid, _, _ in sidx.get(k, []):
            if gd == want and sgid not in consumed:
                seen[sgid] = off
    if len(seen) == 1:
        sgid, off = next(iter(seen.items()))
        match[gid] = sgid
        consumed.add(sgid)
        offc[off] = offc.get(off, 0) + 1
    elif len(seen) > 1:
        amb += 1
sfb = 0
for gid, k, hs, as_ in zip(e2["game_id"].astype(str), e2["k"], e2["home_score"], e2["away_score"]):
    if gid in match:
        continue
    c = [sg for gd, sg, h, a in sidx.get(k, [])
         if sg not in consumed and h == int(hs) and a == int(as_)]
    if len(c) == 1:
        match[gid] = c[0]
        consumed.add(c[0])
        sfb += 1
e_only = e2[~e2["game_id"].astype(str).isin(match)]
s_only = s2[~s2["gid"].isin(consumed)]
R["ng_join"] = {
    "matched_total": len(match),
    "matched_by_unique_window_offset0": offc.get(0, 0),
    "matched_by_unique_window_offset_pm1": offc.get(-1, 0) + offc.get(1, 0),
    "window_ambiguous": amb,
    "matched_by_score_fallback": sfb,
    "espn_only": int(len(e_only)),
    "espn_only_noncup": int((~e_only["notes_headline"].fillna("").str.contains("Cup", case=False)).sum()),
    "espn_only_cup_finals": int((e_only["notes_headline"].fillna("").str.contains("Cup", case=False)).sum()),
    "stats_only": int(len(s_only)),
    "stats_only_pre2002": int((s_only["season_file"] <= 2001).sum()),
    "stats_only_2002plus": int((s_only["season_file"] >= 2002).sum()),
    "union": int(len(e2) + len(s_only)),
}

# measurements_a2.json consistency (championship + identity + census + join blocks)
try:
    m = json.load(open(os.path.join(PREP, "measurements_a2.json")))
    cp = m.get("espn_commissioners_cup", {})
    R["ng_measurements_a2"] = {
        "team_key_table_rows": m.get("team_key_table_rows"),
        "team_key_table_has_SAN_DAL": "SAN_DAL" in m.get("team_key_table", {}),
        "team_key_table_has_DET_TUL": "DET_TUL" in m.get("team_key_table", {}),
        "LVA_key_eras": [m.get("team_key_table", {}).get("LVA", {}).get("first_season"),
                         m.get("team_key_table", {}).get("LVA", {}).get("last_season")],
        "DAL_key_eras": [m.get("team_key_table", {}).get("DAL", {}).get("first_season"),
                         m.get("team_key_table", {}).get("DAL", {}).get("last_season")],
        "cup_rows_championship": cp.get("rows_championship"),
        "cup_championship_by_season": cp.get("championship_by_season"),
        "cup_championship_neutral_site_rows": cp.get("championship_neutral_site_rows"),
        "cup_rows_headline_cup": cp.get("rows_headline_cup"),
        "recon": {k: m.get("recon_rowlevel", {}).get(k) for k in
                  ("espn_real_rows", "matched_to_stats", "matched_by_unique_window",
                   "matched_by_score_fallback", "espn_unmatched", "stats_real_rows", "stats_unmatched")},
        "model_universe": m.get("model_universe"),
        "ts_sched": m.get("ts_espn_schedule_instant_equality_fixed"),
        "identity": {"espn": m.get("espn_identity", {}).get("rows"),
                     "stats": m.get("stats_identity", {}).get("rows")},
        "season_type_totals": m.get("season_type_totals"),
    }
except Exception as ex:  # noqa
    R["ng_measurements_a2"] = f"ERR {ex}"

# hashes of remediated artifacts
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


R["hashes_r1"] = {rel: {"sha256": sha(os.path.join(PREP, rel)), "bytes": os.path.getsize(os.path.join(PREP, rel))}
                  for rel in ("team_key_table.csv", "measurements_a2.json")}

print(json.dumps(R, indent=1, default=str))
