#!/usr/bin/env python3
"""Lane D (wbap-d-verify) INDEPENDENT recomputation — read-only over the corpus.

Verifier: fresh implementation, deliberately NOT measure_a2.py. Schema/coverage
counting ONLY (no win-prob metrics on real outcomes). Prints a JSON report.
"""
import hashlib
import json
import os

import pandas as pd

RAW = os.path.expanduser("~/.my-quantitative-data/wnba-v1/raw")
PREP = os.path.expanduser("~/.my-quantitative-data/wnba-prep-v1")

R = {}

# ------------------------------------------------------------------ load
espn_parts, stats_parts = [], []
for y in range(2002, 2027):
    d = pd.read_csv(os.path.join(RAW, "espn_schedules", f"wnba_schedule_{y}.csv"), low_memory=False)
    d["season_file"] = y
    espn_parts.append(d)
espn = pd.concat(espn_parts, ignore_index=True)
for y in range(1997, 2027):
    d = pd.read_csv(os.path.join(RAW, "wnba_stats_schedules", f"wnba_schedule_{y}.csv.gz"), compression="gzip")
    d["season_file"] = y
    stats_parts.append(d)
stats = pd.concat(stats_parts, ignore_index=True)

R["espn_rows"] = int(len(espn))
R["espn_unique_ids"] = int(espn["game_id"].nunique())
R["espn_seasons"] = int(espn["season_file"].nunique())
R["stats_rows"] = int(len(stats))
R["stats_unique_ids"] = int(stats["game_id"].nunique())
R["stats_seasons"] = int(stats["season_file"].nunique())
R["espn_season_type_counts"] = {str(k): int(v) for k, v in espn["season_type"].value_counts().items()}
R["stats_season_type_counts"] = {str(k): int(v) for k, v in stats["season_type"].value_counts().items()}

# stats game_id structure: '10' + type digit + YY + 5 seq
g = stats["game_id"].astype(str)
R["stats_gid_prefix2"] = {str(k): int(v) for k, v in g.str[:2].value_counts().items()}
R["stats_gid_typedigit_vs_seasontype"] = {
    f"{td}|{st}": int(((g.str[2] == td) & (stats["season_type"].astype(str) == st)).sum())
    for td in ("2", "4") for st in sorted(set(stats["season_type"].astype(str)))
}
R["stats_gid_yy_ok"] = bool(all(gg[3:5] == f"{yy % 100:02d}" for gg, yy in zip(g, stats["season_file"])))
R["espn_gid_len"] = {str(k): int(v) for k, v in espn["game_id"].astype(str).str.len().value_counts().items()}

# ------------------------------------------------------------------ ESPN status / filter law
R["state_counts"] = {str(k): int(v) for k, v in espn["status_type_state"].value_counts().items()}
pre = espn[espn["status_type_state"] != "post"]
prefill = pd.to_numeric(pre["home_score"], errors="coerce").eq(0) & pd.to_numeric(pre["away_score"], errors="coerce").eq(0)
R["nonpost_rows"] = int(len(pre))
R["nonpost_by_season"] = {int(k): int(v) for k, v in pre.groupby("season_file").size().items()}
R["nonpost_prefilled_00"] = int(prefill.sum())
R["nonpost_null_scores"] = int((pd.to_numeric(pre["home_score"], errors="coerce").isna()
                                | pd.to_numeric(pre["away_score"], errors="coerce").isna()).sum())

forf = espn[espn["status_type_detail"].fillna("").str.contains("Forfeit", case=False)]
post = espn[espn["status_type_detail"].fillna("").str.contains("Postponed", case=False)]
R["forfeit_rows"] = forf[["game_id", "season_file", "date", "home_display_name", "away_display_name",
                          "home_score", "away_score", "status_type_state"]].astype(str).to_dict("records")
R["postponed_rows"] = post[["game_id", "season_file", "date", "home_display_name", "away_display_name",
                            "home_score", "away_score", "status_type_state"]].astype(str).to_dict("records")

ALIAS = {"EAST", "WEST", "ALL", "USA", "DEL", "PAR", "WIL", "STE", "CLA", "COL", "SPO", "COOP", "WNBASTARS"}
alias = espn[espn["home_abbreviation"].isin(ALIAS) | espn["away_abbreviation"].isin(ALIAS)]
R["alias_rows"] = int(len(alias))
R["alias_by_season"] = {int(k): int(v) for k, v in alias.groupby("season_file").size().items()}
R["alias_abbr_breakdown"] = {
    a: int((alias["home_abbreviation"] == a).sum() + (alias["away_abbreviation"] == a).sum())
    for a in sorted(set(alias["home_abbreviation"]) | set(alias["away_abbreviation"])) if pd.notna(a)
}
s_alias = stats[stats["home_team_abbreviation"].isin(ALIAS) | stats["away_team_abbreviation"].isin(ALIAS)]
R["stats_alias_rows"] = int(len(s_alias))

tbd = espn[espn["home_display_name"].fillna("").str.upper().eq("TBD")
           | espn["away_display_name"].fillna("").str.upper().eq("TBD")]
R["tbd_rows"] = int(len(tbd))
R["tbd_states"] = {str(k): int(v) for k, v in tbd["status_type_state"].value_counts().items()}
R["tbd_dates"] = sorted(set(tbd["date"].astype(str).str[:10]))

neu = espn[espn["neutral_site"].astype(str).str.upper().isin(["TRUE", "1"])]
R["neutral_rows"] = int(len(neu))
R["neutral_by_season"] = {int(k): int(v) for k, v in neu.groupby("season_file").size().items()}
R["neutral_alias_rows"] = int((neu["home_abbreviation"].isin(ALIAS) | neu["away_abbreviation"].isin(ALIAS)).sum())
R["neutral_nonalias_examples"] = neu.loc[~(neu["home_abbreviation"].isin(ALIAS) | neu["away_abbreviation"].isin(ALIAS)),
                                         ["season_file", "date", "home_display_name", "away_display_name"]].astype(str).to_dict("records")

cup = espn[espn["notes_headline"].fillna("").str.contains("Cup", case=False)]
R["cup_rows_total"] = int(len(cup))
R["cup_by_season"] = {int(k): int(v) for k, v in cup.groupby("season_file").size().items()}
R["cup_season_type"] = {str(k): int(v) for k, v in cup["season_type"].value_counts().items()}
R["cup_headlines_finals_like"] = sorted(set(cup.loc[cup["notes_headline"].fillna("").str.contains("Championship|Final", case=False), "notes_headline"].astype(str)))[:8]

# ------------------------------------------------------------------ census (filter law applied independently)
played = espn[espn["status_type_state"] == "post"]
played = played[~played["status_type_detail"].fillna("").str.contains("Forfeit|Postponed", case=False)]
played = played[~played["home_abbreviation"].isin(ALIAS) & ~played["away_abbreviation"].isin(ALIAS)]
played_rs = played[played["season_type"] == 2]
played_po = played[played["season_type"] == 3]
cup_played_rs = played_rs[played_rs["notes_headline"].fillna("").str.contains("Cup", case=False)]

s0 = pd.to_numeric(stats["home_pts"], errors="coerce")
a0 = pd.to_numeric(stats["away_pts"], errors="coerce")
R["stats_null_pts_rows"] = int((s0.isna() | a0.isna()).sum())
zz = stats[(s0 == 0) & (a0 == 0)]
R["stats_zero_zero_rows"] = zz[["game_id", "season_file", "game_date", "home_team_abbreviation",
                                "away_team_abbreviation", "home_wl", "away_wl"]].astype(str).to_dict("records")
s_played = stats[~((s0 == 0) & (a0 == 0))]
s_played = s_played[~s_played["home_team_abbreviation"].isin(ALIAS) & ~s_played["away_team_abbreviation"].isin(ALIAS)]
s_rs = s_played[s_played["season_type"] == "regular-season"]
s_po = s_played[s_played["season_type"] == "playoffs"]

census = {}
for y in range(1997, 2027):
    e = espn["season_file"] == y
    p = played["season_file"] == y
    census[y] = {
        "espn_total": int(e.sum()) if y >= 2002 else None,
        "espn_real": int(p.sum()) if y >= 2002 else None,
        "espn_rs_xcup": int(((played_rs["season_file"] == y) & (~played_rs["notes_headline"].fillna("").str.contains("Cup", case=False))).sum()) if y >= 2002 else None,
        "espn_cup_played": int((cup_played_rs["season_file"] == y).sum()) if y >= 2002 else None,
        "espn_po": int((played_po["season_file"] == y).sum()) if y >= 2002 else None,
        "stats_total": int((stats["season_file"] == y).sum()),
        "stats_real": int((s_played["season_file"] == y).sum()),
        "stats_rs": int((s_rs["season_file"] == y).sum()),
        "stats_po": int((s_po["season_file"] == y).sum()),
        "rowdiff_espn_total_minus_stats_total": (int(e.sum()) - int((stats["season_file"] == y).sum())) if y >= 2002 else None,
    }
R["census"] = census
R["espn_real_total"] = int(len(played))
R["espn_rs_xcup_total"] = int(len(played_rs) - len(cup_played_rs))
R["espn_cup_total"] = int(len(cup_played_rs))
R["espn_po_total"] = int(len(played_po))
R["stats_real_total"] = int(len(s_played))
R["stats_rs_total"] = int(len(s_rs))
R["stats_po_total"] = int(len(s_po))
R["stats_pre2002_real"] = int((s_played["season_file"] <= 2001).sum())

# ------------------------------------------------------------------ timestamps
eq_rows = eq_ok = sd_eq = 0
for y in range(2002, 2027):
    d = espn[espn["season_file"] == y]
    a = pd.to_datetime(d["date"], utc=True, format="ISO8601")
    b = pd.to_datetime(d["game_date_time"], utc=True, format="ISO8601")
    eq_rows += len(d); eq_ok += int((a == b).sum())
    if "start_date" in d.columns:
        c = pd.to_datetime(d["start_date"], utc=True, format="ISO8601")
        sd_eq += int((a == c).sum())
R["ts_sched_date_eq_gdt"] = {"rows": eq_rows, "equal": eq_ok}
R["ts_sched_date_eq_start_date"] = {"rows": eq_rows, "equal": int(sd_eq)} if sd_eq else "start_date col absent or unequal"
R["ts_date_suffix"] = {
    "Z_pct": round(float(espn["date"].astype(str).str.endswith("Z").mean() * 100), 2),
    "gdt_suffix_2025": espn.loc[espn["season_file"] == 2025, "game_date_time"].astype(str).str[-5:].value_counts().to_dict(),
    "gdt_suffix_2026": espn.loc[espn["season_file"] == 2026, "game_date_time"].astype(str).str[-5:].value_counts().to_dict(),
}
e26 = espn[espn["season_file"] == 2026].copy()
e26["off"] = e26["game_date_time"].astype(str).str.extract(r"([+-]\d{4})$")
R["ts_2026_offsets_by_venue"] = {
    "distinct": sorted(set(e26["off"].dropna())),
    "vegas": e26.loc[e26["home_display_name"] == "Las Vegas Aces", "off"].value_counts().to_dict(),
    "phoenix": e26.loc[e26["home_display_name"] == "Phoenix Mercury", "off"].value_counts().to_dict(),
    "seattle": e26.loc[e26["home_display_name"] == "Seattle Storm", "off"].value_counts().to_dict(),
}

# spot rows for manual eyeball (>=9 rows across flavors/eras)
spot_ids = ["401018942", "401507167", "401857072", "401156333"]
spot = espn[espn["game_id"].astype(str).isin(spot_ids)]
spot_sample = espn.groupby("season_file").head(1)
spot2 = pd.concat([spot, spot_sample]).drop_duplicates("game_id")
R["ts_spot_rows"] = spot2[["season_file", "game_id", "date", "start_date", "game_date_time",
                           "home_display_name", "away_display_name"]].astype(str).to_dict("records")

# box flavor (2025 sample)
tb = pd.read_csv(os.path.join(RAW, "espn_sample_2025", "team_box_2025.csv"), low_memory=False)
sch25 = espn.loc[espn["season_file"] == 2025, ["game_id", "date"]].copy()
sch25["game_id"] = sch25["game_id"].astype(str)
tb2 = tb[["game_id", "game_date", "game_date_time"]].drop_duplicates("game_id")
tb2["game_id"] = tb2["game_id"].astype(str)
mg = tb2.merge(sch25, on="game_id")
u_sch = pd.to_datetime(mg["date"], utc=True, format="ISO8601")
u_box = pd.to_datetime(mg["game_date_time"], utc=True, format="ISO8601")
et_date = u_sch.dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
R["ts_box"] = {
    "box_rows": int(len(tb)), "box_unique_games": int(tb["game_id"].nunique()),
    "merged_games": int(len(mg)),
    "box_suffix_counts": tb["game_date_time"].astype(str).str[-5:].value_counts().to_dict(),
    "instant_eq": int((u_box == u_sch).sum()),
    "gamedate_eq_etdate_pct": round(float((mg["game_date"].astype(str) == et_date).mean() * 100), 2),
    "gamedate_eq_utcdate_pct": round(float((mg["game_date"].astype(str) == u_sch.dt.strftime("%Y-%m-%d")).mean() * 100), 2),
}

# pbp wallclock
pbp = pd.read_csv(os.path.join(RAW, "espn_sample_2025", "play_by_play_2025.csv"), low_memory=False, usecols=["game_id", "wallclock"])
pbp["game_id"] = pbp["game_id"].astype(str)
fw = pbp.groupby("game_id")["wallclock"].min()
mg3 = sch25.merge(fw.rename("fw").reset_index(), on="game_id")
mins = (pd.to_datetime(mg3["fw"], utc=True, format="ISO8601")
        - pd.to_datetime(mg3["date"], utc=True, format="ISO8601")).dt.total_seconds() / 60
R["ts_pbp"] = {
    "Z_pct": round(float(pbp["wallclock"].astype(str).str.endswith("Z").mean() * 100), 2),
    "median_first_event_minus_tip_min": round(float(mins.median()), 2),
    "p05": round(float(mins.quantile(0.05)), 2),
    "p95": round(float(mins.quantile(0.95)), 2),
}

# ------------------------------------------------------------------ independent two-pass reconciliation
def norm(s):
    return str(s).strip().lower()

e2 = played.copy()
e2["tip"] = pd.to_datetime(e2["date"], utc=True, format="ISO8601")
e2["etd"] = e2["tip"].dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
e2["hn"] = e2["home_display_name"].map(norm)
e2["an"] = e2["away_display_name"].map(norm)
s2 = s_played.copy()
s2["hn"] = s2["home_team_name"].map(norm)
s2["an"] = s2["away_team_name"].map(norm)
s2["gid"] = s2["game_id"].astype(str)

by_key = {}
for _, r in s2.iterrows():
    by_key.setdefault((r["hn"], r["an"]), []).append(
        (r["game_date"], r["gid"], int(r["home_pts"]), int(r["away_pts"])))

match, consumed, amb, off_counts = {}, set(), [], {0: 0}
for _, r in e2.iterrows():
    d0 = pd.Timestamp(r["etd"])
    seen = {}
    for off in (-1, 0, 1):
        want = str((d0 + pd.Timedelta(days=off)).date())
        for gd, gid, _, _ in by_key.get((r["hn"], r["an"]), []):
            if gd == want and gid not in consumed:
                seen[gid] = off
    if len(seen) == 1:
        gid, off = next(iter(seen.items()))
        match[str(r["game_id"])] = (gid, off)
        consumed.add(gid)
        off_counts[off] = off_counts.get(off, 0) + 1
    elif len(seen) > 1:
        amb.append({"gid": str(r["game_id"]), "etd": r["etd"], "cands": sorted(seen)})

score_fb = []
for _, r in e2.iterrows():
    if str(r["game_id"]) in match:
        continue
    c = [(gd, gid) for gd, gid, hp, ap in by_key.get((r["hn"], r["an"]), [])
         if gid not in consumed and hp == int(r["home_score"]) and ap == int(r["away_score"])]
    if len(c) == 1:
        match[str(r["game_id"])] = (c[0][1], "score")
        consumed.add(c[0][1])
        score_fb.append({"gid": str(r["game_id"]), "season": int(r["season_file"]), "etd": r["etd"],
                         "stats_gid": c[0][1], "stats_date": c[0][0]})
    elif len(c) > 1:
        score_fb.append({"gid": str(r["game_id"]), "AMBIGUOUS": [x[1] for x in c]})

espn_only = e2[~e2["game_id"].astype(str).isin(match)]
R["recon"] = {
    "espn_real": int(len(e2)),
    "matched": len(match),
    "window_offset_distribution": {str(k): int(v) for k, v in sorted(off_counts.items(), key=lambda x: str(x[0]))},
    "window_ambiguous": len(amb),
    "score_fallback": len([x for x in score_fb if "AMBIGUOUS" not in x]),
    "score_fallback_detail": score_fb,
    "espn_only": int(len(espn_only)),
    "espn_only_rows": espn_only[["season_file", "game_id", "etd", "home_display_name", "away_display_name",
                                 "home_score", "away_score", "notes_headline"]].astype(str).to_dict("records"),
    "stats_real": int(len(s2)),
    "stats_only": int(len(s2) - len(consumed)),
}
so = s2[~s2["gid"].isin(consumed)]
R["recon"]["stats_only_by_season"] = {int(k): int(v) for k, v in so.groupby("season_file").size().items()}
R["recon"]["stats_only_2002plus"] = so.loc[so["season_file"] >= 2002, ["game_id", "season_file", "game_date",
                                                                       "home_team_name", "away_team_name",
                                                                       "home_pts", "away_pts", "season_type"]].astype(str).to_dict("records")
R["recon"]["union"] = int(len(e2) + (len(s2) - len(consumed)))

# ------------------------------------------------------------------ franchise season presence (rename map + lineage)
names = stats.groupby("season_file").apply(
    lambda d: sorted(set(d["home_team_name"].dropna()) | set(d["away_team_name"].dropna())),
    include_groups=False)
ab_by_season = stats.groupby("season_file").apply(
    lambda d: sorted(set(d["home_team_abbreviation"].dropna()) | set(d["away_team_abbreviation"].dropna())),
    include_groups=False)
def seasons_with(name):
    return [int(y) for y in names.index if name in set(names[y])]
def seasons_with_abbr(a):
    return [int(y) for y in ab_by_season.index if a in set(ab_by_season[y])]
R["franchise"] = {
    "Utah Starzz": seasons_with("Utah Starzz"),
    "San Antonio Silver Stars": seasons_with("San Antonio Silver Stars"),
    "San Antonio Stars": seasons_with("San Antonio Stars"),
    "Dallas Wings": seasons_with("Dallas Wings"),
    "Las Vegas Aces": seasons_with("Las Vegas Aces"),
    "Detroit Shock": seasons_with("Detroit Shock"),
    "Tulsa Shock": seasons_with("Tulsa Shock"),
    "Orlando Miracle": seasons_with("Orlando Miracle"),
    "Connecticut Sun": seasons_with("Connecticut Sun"),
    "Portland Fire": seasons_with("Portland Fire"),
    "abbr_SAN": seasons_with_abbr("SAN"),
    "abbr_UTA": seasons_with_abbr("UTA"),
    "abbr_DAL": seasons_with_abbr("DAL"),
    "abbr_DET": seasons_with_abbr("DET"),
    "abbr_TUL": seasons_with_abbr("TUL"),
    "abbr_LVA": seasons_with_abbr("LVA"),
    "abbr_PHO": seasons_with_abbr("PHO"),
    "abbr_PHX": seasons_with_abbr("PHX"),
    "abbr_POR": seasons_with_abbr("POR"),
    "abbr_PDX": seasons_with_abbr("PDX"),
    "abbr_CHA": seasons_with_abbr("CHA"),
    "abbr_CLE": seasons_with_abbr("CLE"),
    "abbr_HOU": seasons_with_abbr("HOU"),
    "abbr_SAC": seasons_with_abbr("SAC"),
    "abbr_MIA": seasons_with_abbr("MIA"),
    "abbr_CHI": seasons_with_abbr("CHI"),
    "abbr_ATL": seasons_with_abbr("ATL"),
    "abbr_GSV": seasons_with_abbr("GSV"),
    "abbr_TOR": seasons_with_abbr("TOR"),
}
# stats-abbr per Phoenix Mercury / Portland Fire by season
phx = stats[(stats["home_team_name"] == "Phoenix Mercury") | (stats["away_team_name"] == "Phoenix Mercury")]
R["franchise"]["phoenix_abbr_by_season"] = {str(y): sorted(set(phx.loc[phx["season_file"] == y, "home_team_abbreviation"])
                                                          | set(phx.loc[phx["season_file"] == y, "away_team_abbreviation"]))
                                            for y in (2024, 2025, 2026)}
pfire = stats[stats["home_team_name"].eq("Portland Fire") | stats["away_team_name"].eq("Portland Fire")]
R["franchise"]["portland_fire_abbr_by_season"] = {str(y): sorted(set(pfire.loc[pfire["season_file"] == y, "home_team_abbreviation"])
                                                               | set(pfire.loc[pfire["season_file"] == y, "away_team_abbreviation"]))
                                                  for y in sorted(set(pfire["season_file"]))}
# ESPN 2002 DET/TUL artifact
det02 = espn[(espn["season_file"] == 2002)
             & ((espn["home_display_name"] == "Detroit Shock") | (espn["away_display_name"] == "Detroit Shock"))]
R["espn_2002_detroit"] = {
    "rows": int(len(det02)),
    "home_abbrs": {str(k): int(v) for k, v in det02["home_abbreviation"].value_counts().items()},
    "away_abbrs": {str(k): int(v) for k, v in det02["away_abbreviation"].value_counts().items()},
}
# ESPN abbr per Connecticut / LA / NY / WAS across seasons (many-to-many check)
ct = espn[espn["home_display_name"].str.contains("Connecticut", na=False) | espn["away_display_name"].str.contains("Connecticut", na=False)]
R["espn_ct_abbrs"] = sorted(set(ct["home_abbreviation"].dropna()) | set(ct["away_abbreviation"].dropna()))
# 2016/2017 SAN+DAL coexistence
for y in (2015, 2016, 2017, 2018):
    ab = set(ab_by_season[y])
    R[f"stats_abbrs_{y}"] = sorted(ab)
    R[f"stats_n_teams_{y}"] = len([a for a in ab if a not in ALIAS])

# ------------------------------------------------------------------ hashes (>=3 corpus + new files)
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

audit = json.load(open(os.path.join(RAW, "audit_results.json")))
audit_by_file = {m["file"]: m for m in audit["manifest"]}
hash_checks = {}
for rel in ["espn_schedules/wnba_schedule_2020.csv", "wnba_stats_schedules/wnba_schedule_1997.csv.gz",
            "espn_sample_2025/team_box_2025.csv"]:
    p = os.path.join(RAW, rel)
    h = sha(p)
    rec = audit_by_file.get(os.path.basename(rel), {})
    hash_checks[rel] = {"sha256": h, "bytes": os.path.getsize(p),
                        "manifest_sha": rec.get("sha256"), "manifest_bytes": rec.get("bytes"),
                        "match": (h == rec.get("sha256")) and (os.path.getsize(p) == rec.get("bytes"))}
for rel in ["extensions/team_box_2013.csv", "extensions/game_rosters_2013.csv",
            "release_depth_census.json", "team_key_table.csv", "measurements_a2.json"]:
    p = os.path.join(PREP, rel)
    hash_checks[rel] = {"sha256": sha(p), "bytes": os.path.getsize(p)}
R["hashes"] = hash_checks

# attempt-1 provenance spot check
try:
    a1 = json.load(open(os.path.join(PREP, "measurements_a.json")))
    def find(obj, key, path=""):
        out = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                if key.lower() in str(k).lower():
                    out.append((path + "/" + str(k), str(v)[:200]))
                out += find(v, key, path + "/" + str(k))
        elif isinstance(obj, list):
            for i, v in enumerate(obj[:5]):
                out += find(v, key, path + f"[{i}]")
        return out
    R["attempt1_superseded_markers"] = find(a1, "94.03") + find(a1, "pct")[:6]
except Exception as ex:  # noqa
    R["attempt1_superseded_markers"] = f"ERR {ex}"

print(json.dumps(R, indent=1, default=str))
