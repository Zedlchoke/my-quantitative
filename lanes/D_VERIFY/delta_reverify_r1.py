#!/usr/bin/env python
"""Independent POST-FIX re-verification, task nbang-d-verify-r1 (lane D_VERIFY, fresh context).

Re-measures from bytes only. Schema/coverage counting ONLY — no win-prob metric,
no model, no score is computed on any real outcome (plan boundary).
Writes lanes/D_VERIFY/delta_reverify_r1_evidence.json and exits 0 iff all
programmatic gates hold. Document greps/gits are done by the report author.
"""
import hashlib
import json
import os
from datetime import datetime, timezone

import pandas as pd

RAW = os.path.expanduser("~/.my-quantitative-data/nba-hoopr-v1/raw")
PBP_DIR = os.path.expanduser("~/.my-quantitative-data/nba-ng-prep-v1/pbp_2016_2025")
BDL_DIR = os.path.expanduser("~/.my-quantitative-data/nba-ng-prep-v1/bdl_spotcheck")
SEASONS = list(range(2016, 2027))

E = {"meta": {}}

# BDL -> hoopR abbreviation map (documented in BDL_CROSSCHECK_NBA.md; hoopR is the deviant side)
ABBR = {"NYK": "NY", "NOP": "NO", "WAS": "WSH", "GSW": "GS", "UTA": "UTAH", "SAS": "SA"}


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_tip(s):
    # hoopR start_date: '2016-06-20T00:00Z' ; BDL datetime: '2015-12-19T00:00:00.000Z'
    s = s.strip().replace("Z", "+00:00")
    return datetime.fromisoformat(s).astimezone(timezone.utc)


# ---------------------------------------------------------------- load schedules
sched = {}
for s in SEASONS:
    df = pd.read_csv(os.path.join(RAW, f"nba_schedule_{s}.csv"), dtype=str)
    sched[s] = df
E["schedule"] = {
    "raw_rows_total": int(sum(len(d) for d in sched.values())),
    "raw_rows_per_season": {s: int(len(d)) for s, d in sched.items()},
}

all_ids = pd.concat([d["game_id"] for d in sched.values()], ignore_index=True)
E["identity"] = {
    "unique_game_id": int(all_ids.nunique()),
    "id_equals_game_id_all": bool(all((d["id"] == d["game_id"]).all() for d in sched.values())),
    "season_field_equals_file_all": bool(all((d["season"] == str(s)).all() for s, d in sched.items())),
}

# ------------------------------------------------- dedupe/exclusion law (spec §4)
law = {}
expected_played = {2016: 1316, 2017: 1309, 2018: 1312, 2019: 1312, 2020: 1143,
                   2021: 1171, 2022: 1323, 2023: 1320, 2024: 1319, 2025: 1321, 2026: 1322}
for s, d in sched.items():
    hl = d["notes_headline"].fillna("").str.lower()
    completed = d["status_type_completed"] == "true"
    exhibit = completed & (hl.str.contains("all-star", regex=False) | hl.str.contains("rising stars", regex=False))
    played = completed & ~exhibit
    postponed = d[~completed]
    cup = played & (hl.str.contains("in-season tournament", regex=False) | hl.str.contains("nba cup", regex=False))
    cup_final = d[played & cup & hl.str.contains("championship", regex=False)]
    st = d["season_type"]
    rs_standings = int((played & (st == "2") & ~(cup & hl.str.contains("championship", regex=False))).sum())
    law[s] = {
        "completed": int(completed.sum()),
        "exhibitions": int(exhibit.sum()),
        "played_total": int(played.sum()),
        "postponed": int(len(postponed)),
        "postponed_all_status": bool((postponed["status_type_description"] == "Postponed").all())
        and bool((postponed["status_type_state"] == "post").all()),
        "rs_standings_played": rs_standings,
        "cup_rows": int(cup.sum()),
        "cup_finals": int(len(cup_final)),
        "playin_played": int((played & (st == "5")).sum()),
        "playoffs_played": int((played & (st == "3")).sum()),
    }
E["law"] = {
    "per_season": law,
    "played_total": int(sum(v["played_total"] for v in law.values())),
    "exhibitions_total": int(sum(v["exhibitions"] for v in law.values())),
    "postponed_total": int(sum(v["postponed"] for v in law.values())),
    "cup_finals_total": int(sum(v["cup_finals"] for v in law.values())),
    "playin_total": int(sum(v["playin_played"] for v in law.values())),
    "playoffs_total": int(sum(v["playoffs_played"] for v in law.values())),
    "rs_standings_values": sorted({v["rs_standings_played"] for v in law.values()}),
    "played_matches_expected": all(law[s]["played_total"] == expected_played[s] for s in SEASONS),
}
E["law"]["reconciliation"] = (
    E["schedule"]["raw_rows_total"]
    == E["law"]["played_total"] + E["law"]["exhibitions_total"] + E["law"]["postponed_total"]
)

# ------------------------------------------------------------------- load pbp ids
pbp_ids, pbp_meta = {}, {}
for s in SEASONS:
    p = os.path.join(RAW if s == 2026 else PBP_DIR, f"play_by_play_{s}.parquet")
    col = pd.read_parquet(p, columns=["game_id"])["game_id"]
    pbp_ids[s] = col
    pbp_meta[s] = {
        "dtype": str(col.dtype),
        "nulls": int(col.isna().sum()),
        "unique": int(col.nunique()),
        "size_bytes": os.path.getsize(p),
        "sha256": sha256_file(p),
    }
E["pbp"] = {
    "per_season": pbp_meta,
    "total_bytes_2016_2025": int(sum(pbp_meta[s]["size_bytes"] for s in range(2016, 2026))),
}

# ------------------------------------------- CHECK 1: played-without-pbp gap (D1)
EXPECT_GAP = {
    2016: {"400828893", "400828600", "400828393"},
    2018: {"400974444", "400974773", "400975617", "400975670"},
    2020: {"401161490", "401161505", "401161528", "401161533", "401161530", "401161536"},
    2026: {"401810469"},
}
gap, gap_detail = {}, {}
gap_total = 0
for s in SEASONS:
    d = sched[s]
    hl = d["notes_headline"].fillna("").str.lower()
    completed = d["status_type_completed"] == "true"
    exhibit = completed & (hl.str.contains("all-star", regex=False) | hl.str.contains("rising stars", regex=False))
    played_df = d[completed & ~exhibit]
    pcol = pbp_ids[s].dropna()
    pset_str = set(pcol.astype(str))
    pset_int = set(pcol.astype("int64").astype(str))  # int-key interpretation, re-stringified
    ids = set(played_df["game_id"])
    g_str = sorted(ids - pset_str)
    g_int = sorted(ids - pset_int)
    gap[s] = g_str
    gap_total += len(g_str)
    gap_detail[s] = {
        "gap_str_keys": g_str,
        "gap_int_keys_agree": g_str == g_int,
        "matches_erratum_list": set(g_str) == EXPECT_GAP.get(s, set()),
        # exhibitions with pbp (D5)
        "exhibitions_with_pbp": int(sum(1 for gid in d[exhibit]["game_id"] if gid in pset_str)),
        "exhibitions_total": int(exhibit.sum()),
        "postponed_rows_with_pbp": int(sum(1 for gid in d[~completed]["game_id"] if gid in pset_str)),
    }
gap_rows = []
for s in SEASONS:
    for gid in gap[s]:
        r = sched[s][sched[s]["game_id"] == gid].iloc[0]
        gap_rows.append({
            "season": s, "game_id": gid,
            "matchup": f"{r['home_abbreviation']}–{r['away_abbreviation']}",
            "date": r["game_date"], "status": r["status_type_description"],
            "home_score": r.get("home_score"), "away_score": r.get("away_score"),
        })
E["gap_d1"] = {
    "gap_per_season_counts": {s: len(v) for s, v in gap.items()},
    "gap_total": gap_total,
    "gap_rows": gap_rows,
    "detail": gap_detail,
    "int_keys_agree_everywhere": all(v["gap_int_keys_agree"] for v in gap_detail.values()),
    "matches_erratum_game_for_game": all(v["matches_erratum_list"] for v in gap_detail.values()),
    "exhibitions_with_pbp_total": int(sum(v["exhibitions_with_pbp"] for v in gap_detail.values())),
    "exhibitions_total": int(sum(v["exhibitions_total"] for v in gap_detail.values())),
    "postponed_with_pbp_total": int(sum(v["postponed_rows_with_pbp"] for v in gap_detail.values())),
}

# ------------------------------------------------- manifest re-sum + sha re-hash
manifest_expected = {
    2016: (25999321, "70f594cf09ed2a3d157e91aa433206854ad6b58f403802a1f5679936f9adb151"),
    2017: (26151903, "06a0426af80e58d50b532aab2334e1f8d84fdf4e3b152a4c5fbbe526612c5aa6"),
    2018: (26839399, "75ce3720fd3c53e33619ff0309eed3df7e9a8d26447470a9927ebe08229544c6"),
    2019: (28103629, "8580ff36b58665c43e05beebd78d830e4ef69694cfb7fcf4c284bfa0b9bc8507"),
    2020: (24966617, "b6413e4c9d0bfd0d57b3b8b4f23c0dfef9487022c5e02da87adb77ff6ac127b5"),
    2021: (25031848, "1aa4b333bed1c43dfb457f6ff1542f0a47d9e1b6c10461b40e456ed646b5f700"),
    2022: (28327133, "c7269c55787a43952e071cae9364de378e79f55e956a14d8846b83051ff66537"),
    2023: (21052023, "4714c6b0c9bad84e2a0579f13474ba6ffb6fdb0a1923f7c890020c5e55373738"),
    2024: (20618404, "62b609ea487d23aec11e6756d7477a8b1df3a1e57e97fc90c7230b62a5835af1"),
    2025: (21552259, "e3a61b57e491b71379abd1ad4c0b2617500a3921deadd3319ee9362d49d2a9dc"),
}
man = {}
for s, (b, h) in manifest_expected.items():
    man[s] = {
        "bytes_match": pbp_meta[s]["size_bytes"] == b,
        "sha_match": pbp_meta[s]["sha256"] == h,
    }
E["manifest"] = {
    "per_file": man,
    "resum_bytes": int(sum(b for b, _ in manifest_expected.values())),
    "declared_total": 248642536,
    "all_bytes_match": all(v["bytes_match"] for v in man.values()),
    "all_sha_match": all(v["sha_match"] for v in man.values()),
}

# ------------------------------------------------------- CHECK 3: BDL 22/22 redo
bdl_results, bdl_dates = [], []
for s in SEASONS:
    fp = os.path.join(BDL_DIR, f"resp_{s}_" + {2016: "2015-12-18", 2017: "2016-12-23", 2018: "2017-12-22",
                                               2019: "2018-11-16", 2020: "2019-12-20", 2021: "2021-01-08",
                                               2022: "2021-12-18", 2023: "2022-11-25", 2024: "2023-12-18",
                                               2025: "2024-12-23", 2026: "2025-12-20"}[s] + ".json")
    with open(fp) as f:
        bdl_games = json.load(f)
    qdate = os.path.basename(fp)[len(f"resp_{s}_"):-len(".json")]
    d = sched[s]
    hl = d["notes_headline"].fillna("").str.lower()
    completed = d["status_type_completed"] == "true"
    exhibit = completed & (hl.str.contains("all-star", regex=False) | hl.str.contains("rising stars", regex=False))
    day = d[completed & ~exhibit & (d["game_date"] == qdate)]
    day = day.sort_values("game_id")
    pick = day.head(2)
    bdl_dates.append({"season": s, "query_date": qdate, "bdl_returned": len(bdl_games),
                      "hoopr_completed_on_date": int(len(day)),
                      "counts_agree": len(bdl_games) == len(day)})
    for _, hr in pick.iterrows():
        hr_home, hr_away = hr["home_abbreviation"], hr["away_abbreviation"]
        cand = [g for g in bdl_games
                if ABBR.get(g["home"], g["home"]) == hr_home and ABBR.get(g["visitor"], g["visitor"]) == hr_away]
        ok = False
        why = "no-bdl-counterpart"
        if len(cand) == 1:
            g = cand[0]
            try:
                tip_delta = abs((parse_tip(g["datetime"]) - parse_tip(hr["start_date"])).total_seconds())
            except Exception:
                tip_delta = None
            ok = (
                g["date"] == hr["game_date"]
                and g["status"] == "Final"
                and int(g["home_team_score"]) == int(hr["home_score"])
                and int(g["visitor_team_score"]) == int(hr["away_score"])
                and tip_delta is not None and tip_delta <= 60.0
            )
            why = "MATCH" if ok else f"field-mismatch(tip_delta={tip_delta})"
        bdl_results.append({"season": s, "hoopr_game_id": hr["game_id"], "date": hr["game_date"],
                            "home": hr_home, "away": hr_away, "verdict": why, "ok": ok})
E["bdl"] = {
    "files": len(bdl_dates),
    "seasons_covered": sorted(x["season"] for x in bdl_dates),
    "games_checked": len(bdl_results),
    "games_match": int(sum(1 for r in bdl_results if r["ok"])),
    "per_date_aggregate": bdl_dates,
    "dates_aggregate_agree": int(sum(1 for x in bdl_dates if x["counts_agree"])),
    "per_game": bdl_results,
    "final_run_requests": len(bdl_dates),
}
# throttle evidence from mtimes
mt = []
for s in SEASONS:
    fp = os.path.join(BDL_DIR, [f for f in os.listdir(BDL_DIR) if f.startswith(f"resp_{s}_")][0])
    mt.append(os.path.getmtime(fp))
mt.sort()
E["bdl"]["throttle_gaps_s"] = [round(b - a, 1) for a, b in zip(mt, mt[1:])]
E["bdl"]["throttle_min_gap_s"] = min(E["bdl"]["throttle_gaps_s"])

# ------------------------------------------------------------------ gates / exit
gates = {
    "G1_gap_is_14": gap_total == 14,
    "G1_gap_ids_match_erratum": E["gap_d1"]["matches_erratum_game_for_game"],
    "G1_gap_zero_other_seasons": all(len(gap[s]) == 0 for s in (2017, 2019, 2021, 2022, 2023, 2024, 2025)),
    "G1_exhibitions_19_of_19_have_pbp": E["gap_d1"]["exhibitions_with_pbp_total"] == 19 == E["gap_d1"]["exhibitions_total"],
    "G1_manifest_total_248642536": E["manifest"]["resum_bytes"] == E["manifest"]["declared_total"] and E["manifest"]["all_bytes_match"],
    "G1_manifest_sha_all_match": E["manifest"]["all_sha_match"],
    "G2_total_14254": E["schedule"]["raw_rows_total"] == 14254,
    "G2_unique_14254": E["identity"]["unique_game_id"] == 14254,
    "G2_reconcile_zero_residue": E["law"]["reconciliation"],
    "G2_played_14168": E["law"]["played_total"] == 14168,
    "G2_played_per_season": E["law"]["played_matches_expected"],
    "G2_rs_1230x9_1059_1080": E["law"]["rs_standings_values"] == [1059, 1080, 1230]
    and sum(1 for v in law.values() if v["rs_standings_played"] == 1230) == 9,
    "G2_playin_37": E["law"]["playin_total"] == 37,
    "G2_playoffs_919": E["law"]["playoffs_total"] == 919,
    "G2_cup_finals_3": E["law"]["cup_finals_total"] == 3,
    "G3_bdl_22_of_22": E["bdl"]["games_checked"] == 22 and E["bdl"]["games_match"] == 22,
    "G3_bdl_11_seasons_incl_2016_2020_2026": E["bdl"]["files"] == 11
    and {2016, 2020, 2026}.issubset(set(E["bdl"]["seasons_covered"])),
    "G3_final_run_requests_le_25": E["bdl"]["final_run_requests"] <= 25,
    "G3_throttle_ge_13s": E["bdl"]["throttle_min_gap_s"] >= 13.0,
    "G3_aggregate_11_of_11": E["bdl"]["dates_aggregate_agree"] == 11,
    "G_postponed_no_pbp": E["gap_d1"]["postponed_with_pbp_total"] == 0,
}
E["gates"] = gates
E["meta"]["all_gates_pass"] = all(gates.values())

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "delta_reverify_r1_evidence.json"), "w") as f:
    json.dump(E, f, indent=1, default=str)

print(json.dumps({k: v for k, v in gates.items()}, indent=1))
print("ALL_GATES_PASS =", E["meta"]["all_gates_pass"])
raise SystemExit(0 if E["meta"]["all_gates_pass"] else 1)
