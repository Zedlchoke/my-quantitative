"""Lane D verifier (task nbang-d-verify, NBA-WINPROB-NG-PREP-V1) — independent recomputation.

SCHEMA/COVERAGE COUNTING ONLY (plan boundary): no win-prob metric, no model, no score.
Read-only everywhere; writes only this lane's verify_evidence.json.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

HOME = Path.home()
HOOPR = HOME / ".my-quantitative-data/nba-hoopr-v1/raw"
PBP = HOME / ".my-quantitative-data/nba-ng-prep-v1/pbp_2016_2025"
BDLDIR = HOME / ".my-quantitative-data/nba-ng-prep-v1/bdl_spotcheck"
LANE = Path(__file__).parent
SEASONS = list(range(2016, 2027))
ET = zoneinfo = None
try:
    from zoneinfo import ZoneInfo
    ET = ZoneInfo("America/New_York")
except Exception:  # pragma: no cover
    pass

E = {"ran_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat()}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------- 1. schedules
frames = {}
for s in SEASONS:
    frames[s] = pd.read_csv(HOOPR / f"nba_schedule_{s}.csv", dtype=str, keep_default_na=False)
df = pd.concat([frames[s].assign(_file=s) for s in SEASONS], ignore_index=True)
E["total_rows"] = int(len(df))
E["rows_per_file"] = {str(s): int(len(frames[s])) for s in SEASONS}
E["unique_game_id"] = int(df["game_id"].nunique())
E["game_id_eq_id_all"] = bool((df["game_id"] == df["id"]).all())
E["season_field_eq_file_all"] = bool((df["season"].astype(int) == df["_file"]).all())
E["season_type_values"] = sorted(df["season_type"].astype(int).unique().tolist())

# tip law (exhaustive)
gdt = pd.to_datetime(df["game_date_time"], format="ISO8601", utc=True, errors="coerce")
sd = pd.to_datetime(df["start_date"], format="ISO8601", utc=True, errors="coerce")
dtc = pd.to_datetime(df["date"], format="ISO8601", utc=True, errors="coerce")
E["gdt_parse_fail"] = int(gdt.isna().sum())
E["tip_utc_eq_start_date"] = int((gdt == sd).sum())
E["start_date_eq_date"] = int((sd == dtc).sum())
offs = df["game_date_time"].str.slice(-5)
E["offset_counts"] = {k: int(v) for k, v in offs.value_counts().items()}
utc_date = gdt.dt.tz_convert("UTC").dt.date
loc_date = pd.to_datetime(df["game_date"], format="%Y-%m-%d").dt.date
E["utc_date_ne_local_date"] = int((utc_date != loc_date).sum())
E["cross_utc_midnight_pct"] = round(E["utc_date_ne_local_date"] / E["total_rows"] * 100, 2)

# ET-home offset exhaustiveness + BOS DST flips
et_home = df[df["home_abbreviation"].isin(
    ["BOS", "BKN", "NY", "NYK", "PHI", "TOR", "CHI", "CLE", "DET", "IND", "MIL",
     "ATL", "CHA", "MIA", "ORL", "WSH", "WAS"])]
et_exp = pd.to_datetime(et_home["game_date_time"], format="ISO8601", utc=True).dt.tz_convert(ET).apply(
    lambda t: t.strftime("%z"))
E["et_home_rows"] = int(len(et_home))
E["et_home_offset_mismatch"] = int((et_exp.reset_index(drop=True) != et_home["game_date_time"].str.slice(-5).reset_index(drop=True)).sum())

bos = df[df["home_abbreviation"] == "BOS"].copy()
bos["_t"] = pd.to_datetime(bos["game_date_time"], format="ISO8601", utc=True)
bos25 = bos[pd.to_datetime(bos["game_date"]).between("2024-10-01", "2025-04-30")].sort_values("_t")
flips, prev = [], None
for _, r in bos25.iterrows():
    o = r["game_date_time"][-5:]
    if prev is not None and prev["off"] != o:
        flips.append({"from": prev, "to": {"date": r["game_date"], "gdt": r["game_date_time"], "off": o}})
    prev = {"date": r["game_date"], "gdt": r["game_date_time"], "off": o}
E["bos_2024_25_offset_flips"] = flips

# sampled tip rows (>=9 incl DST boundaries + neutral site)
sel = pd.concat([
    df[(df["game_date"] == "2024-11-02") & (df["home_abbreviation"] == "BOS")],
    df[(df["game_date"] == "2024-11-05") & (df["home_abbreviation"] == "BOS")],
    df[(df["game_date"] == "2025-03-07") & (df["home_abbreviation"] == "BOS")],
    df[(df["game_date"] == "2025-03-10") & (df["home_abbreviation"] == "BOS")],
    df[(df["_file"] == 2016) & (df["game_date"] == "2015-10-27")].head(2),
    df[(df["_file"] == 2026) & (df["game_date"] == "2026-01-15")].head(2),
    df[(df["neutral_site"].str.lower() == "true")].head(3),
])
E["tip_sample_rows"] = [
    {"game_id": r["game_id"], "file": int(r["_file"]), "game_date": r["game_date"],
     "game_date_time": r["game_date_time"], "start_date": r["start_date"], "date": r["date"],
     "home": r["home_abbreviation"], "away": r["away_abbreviation"], "neutral": r["neutral_site"]}
    for _, r in sel.drop_duplicates("game_id").head(14).iterrows()
]

# identity spot: 2025 Finals G7
row = df[df["game_id"] == "401766128"]
E["spot_2025_finals_g7"] = (
    None if row.empty else
    {"game_date": row.iloc[0]["game_date"], "home": row.iloc[0]["home_abbreviation"],
     "away": row.iloc[0]["away_abbreviation"], "home_score": row.iloc[0]["home_score"],
     "away_score": row.iloc[0]["away_score"], "notes": row.iloc[0]["notes_headline"]}
)

# ------------------------------------------------------------- 2. dedupe law (spec)
completed = df["status_type_completed"].str.lower() == "true"
exhib = df["notes_headline"].str.lower().str.contains("all-star|rising stars", na=False, regex=True)
postponed = ~completed
played = completed & ~exhib
E["played_total"] = int(played.sum())
E["exhib_total"] = int(exhib.sum())
E["postponed_total"] = int(postponed.sum())
E["reconciliation_exact"] = bool(E["total_rows"] == E["played_total"] + E["exhib_total"] + E["postponed_total"])
E["exhib_by_season"] = {str(s): int(((frames[s]["notes_headline"].str.lower().str.contains("all-star|rising stars", na=False))).sum()) for s in SEASONS}
E["postponed_by_season"] = {str(s): int((~frames[s]["status_type_completed"].str.lower().eq("true")).sum()) for s in SEASONS}
E["postponed_status_desc"] = sorted(df.loc[postponed, "status_type_description"].unique().tolist())
E["postponed_state"] = sorted(df.loc[postponed, "status_type_state"].unique().tolist())

# makeup candidate: same home|away pair completed in same file, different game_id
comp = df[completed]
comp_pairs = {}
for _, r in comp.iterrows():
    comp_pairs.setdefault((r["_file"], r["home_abbreviation"], r["away_abbreviation"]), set()).add(r["game_id"])
mk_ok = 0
for _, r in df[postponed].iterrows():
    ids = comp_pairs.get((r["_file"], r["home_abbreviation"], r["away_abbreviation"]), set())
    if any(g != r["game_id"] for g in ids):
        mk_ok += 1
E["postponed_with_makeup"] = mk_ok

# cup law (spec: rows w/ 'In-Season|NBA Cup' = 67/season 2024-26; the Championship
# final = cup row whose headline also contains 'Championship' — exactly 1/season)
cup = df["notes_headline"].str.contains("In-Season|NBA Cup", case=False, regex=True, na=False)
E["cup_rows_total"] = int(cup.sum())
E["cup_by_season"] = {str(s): int(cup[df["_file"] == s].sum()) for s in SEASONS}
E["cup_neutral_values"] = {str(k): int(v) for k, v in df.loc[cup, "neutral_site"].str.lower().value_counts().items()}
cup_final = cup & df["notes_headline"].str.contains("Championship", case=False, na=False)
E["cup_final_by_season"] = {str(s): int(cup_final[df["_file"] == s].sum()) for s in SEASONS}
E["cup_completed_all"] = bool(completed[cup].all())

# per-season played decomposition (spec §4 table)
per_season = {}
for s in SEASONS:
    d = df[df["_file"] == s]
    c = d["status_type_completed"].str.lower() == "true"
    x = d["notes_headline"].str.lower().str.contains("all-star|rising stars", na=False)
    cf = d["notes_headline"].str.contains("In-Season|NBA Cup", case=False, na=False) & d["notes_headline"].str.contains("Championship", case=False, na=False)
    pl = c & ~x
    per_season[str(s)] = {
        "raw": int(len(d)),
        "rs_standings_played": int((pl & (d["season_type"] == "2") & ~cf).sum()),
        "cup_final_played": int((pl & cf).sum()),
        "play_in_played": int((pl & (d["season_type"] == "5")).sum()),
        "playoffs_played": int((pl & (d["season_type"] == "3")).sum()),
        "total_played": int(pl.sum()),
    }
E["played_per_season"] = per_season
E["played_sum_by_class"] = {
    "rs_standings": int(sum(v["rs_standings_played"] for v in per_season.values())),
    "cup_final": int(sum(v["cup_final_played"] for v in per_season.values())),
    "play_in": int(sum(v["play_in_played"] for v in per_season.values())),
    "playoffs": int(sum(v["playoffs_played"] for v in per_season.values())),
    "total": int(sum(v["total_played"] for v in per_season.values())),
}

# per-team census: RS standings-embedded played games (incl. cup standings, excl. final)
census = {}
for s in (2017, 2024, 2025, 2026):
    d = df[(df["_file"] == s)]
    c = d["status_type_completed"].str.lower() == "true"
    x = d["notes_headline"].str.lower().str.contains("all-star|rising stars", na=False)
    cf = d["notes_headline"].str.contains("In-Season|NBA Cup", case=False, na=False) & d["notes_headline"].str.contains("Championship", case=False, na=False)
    pl = c & ~x & (d["season_type"] == "2") & ~cf
    home = d.loc[pl, "home_abbreviation"].value_counts()
    away = d.loc[pl, "away_abbreviation"].value_counts()
    tot = home.add(away, fill_value=0).astype(int)
    census[str(s)] = {"n_teams": int(len(tot)), "all_82": bool((tot == 82).all()),
                      "rs_standings_games": int(pl.sum()),
                      "min": int(tot.min()), "max": int(tot.max())}
E["team_census"] = census

# exhibitions carry pbp in some seasons (checked below with pbp ids)

# ------------------------------------------------------------- 3. crosswalk
cw = pd.read_csv(HOOPR / "nba_schedule_crosswalk_2026.csv", dtype=str, keep_default_na=False)
E["cw_rows"] = int(len(cw))
E["cw_with_espn_id"] = int((cw["espn_game_id"].str.strip() != "").sum())
d26 = df[df["_file"] == 2026]
j = d26.merge(cw[cw["espn_game_id"].str.strip() != ""], left_on="game_id", right_on="espn_game_id", how="left")
E["sched2026_matched"] = int(j["espn_game_id"].notna().sum())
both = j[j["espn_game_id"].notna()]
E["sched2026_date_agree"] = int((both["game_date_x"] == both["game_date_y"]).sum())
lbl = both["season_type_y"].fillna("")
E["cw_label_map_counts"] = {str(k): int(v) for k, v in lbl.value_counts().items()}

# ------------------------------------------------------------- 4. hashes
prov = pd.read_csv(HOOPR / "_download_provenance.tsv", sep="\t", dtype=str)
h_ok = {}
for _, r in prov.iterrows():
    p = HOOPR / r["filename"]
    h_ok[r["filename"]] = bool(sha256(p) == r["sha256"])
E["hoopr_prov_hashes_all_match"] = bool(all(h_ok.values()))
E["hoopr_prov_hash_count"] = len(h_ok)

manifest = json.load(open(LANE.parent / "A_DATA" / "DOWNLOAD_MANIFEST.md".replace(".md", "_MANIFEST.md"))) if False else None
# parse pbp sha table from DOWNLOAD_MANIFEST.md
man_text = (LANE.parent / "A_DATA" / "DOWNLOAD_MANIFEST.md").read_text()
man_hashes = {}
for line in man_text.splitlines():
    parts = [t.strip() for t in line.split("|")]
    if len(parts) >= 4 and parts[1].startswith("play_by_play_"):
        try:
            man_hashes[parts[1]] = (int(parts[2].replace(",", "")), parts[3])
        except ValueError:
            pass
E["pbp_manifest_entries"] = len(man_hashes)
pbp_hash_check = {}
for fname, (bexp, hexp) in man_hashes.items():
    p = PBP / fname
    ok_size = p.stat().st_size == bexp
    ok_hash = sha256(p) == hexp
    pbp_hash_check[fname] = {"size_ok": ok_size, "sha_ok": ok_hash}
E["pbp_hash_check"] = pbp_hash_check
E["pbp_hash_all_ok"] = bool(all(v["size_ok"] and v["sha_ok"] for v in pbp_hash_check.values()))
E["pbp_total_bytes"] = int(sum((PBP / f).stat().st_size for f in man_hashes))

# ------------------------------------------------------------- 5. pbp census spot
def pbp_ids_and_spread(path: Path):
    import pyarrow.parquet as pq
    sch = pq.read_schema(path)
    cols = [n for n in ("game_id", "game_spread", "home_favorite", "home_team_spread") if n in sch.names]
    t = pq.read_table(path, columns=cols)
    d = t.to_pandas()
    d["game_id"] = d["game_id"].astype(str)
    return d

pbp_data = {}
spot_seasons = [2016, 2021, 2026]
src = {s: (PBP / f"play_by_play_{s}.parquet" if s < 2026 else HOOPR / "play_by_play_2026.parquet") for s in SEASONS}
spread_re = {}
for s in spot_seasons:
    d = pbp_ids_and_spread(src[s])
    pbp_data[s] = set(d["game_id"])
    u = d.drop_duplicates("game_id")
    spread_re[str(s)] = {
        "unique_games": int(len(u)),
        "spread_nonnull": int(u["game_spread"].notna().sum()),
        "homefav_nonnull": int(u["home_favorite"].notna().sum()),
    }
E["spread_recheck"] = spread_re

# missing pbp on played games + exhibition/postponed attachment (all 11 seasons)
missing_pbp, exhib_with_pbp, ppd_with_pbp = {}, {}, {}
for s in SEASONS:
    if s not in pbp_data:
        pbp_data[s] = set(pbp_ids_and_spread(src[s])["game_id"])
    d = df[df["_file"] == s]
    c = d["status_type_completed"].str.lower() == "true"
    x = d["notes_headline"].str.lower().str.contains("all-star|rising stars", na=False)
    pl = c & ~x
    miss = sorted(set(d.loc[pl, "game_id"]) - pbp_data[s])
    if miss:
        missing_pbp[str(s)] = miss
    ew = sorted(set(d.loc[c & x, "game_id"]) & pbp_data[s])
    if ew:
        exhib_with_pbp[str(s)] = len(ew)
    pw = sorted(set(d.loc[~c, "game_id"]) & pbp_data[s])
    if pw:
        ppd_with_pbp[str(s)] = len(pw)
E["played_missing_pbp"] = missing_pbp
E["exhibitions_with_pbp_by_season"] = exhib_with_pbp
E["postponed_with_pbp_by_season"] = ppd_with_pbp

# ------------------------------------------------------------- 6. BDL artifacts
agg = json.load(open(LANE.parent / "A_DATA" / "BDL_CROSSCHECK_A_DATA.json"))
E["bdl_agg_summary"] = agg["summary"]
E["bdl_agg_requests"] = len(agg["requests"])
E["bdl_games_in_agg"] = len(agg["games"])
E["bdl_verdicts"] = {v: int(v2) for v, v2 in pd.Series([g["verdict"] for g in agg["games"]]).value_counts().items()}
E["bdl_all_match_checks_true"] = bool(all(all(v is True for v in g.get("checks", {}).values()) for g in agg["games"] if g.get("checks")))
E["bdl_tip_deltas_max"] = max([g.get("tip_delta_s", 0) for g in agg["games"]])

# recount hoopR games per probed date (completed non-exhibition)
E["bdl_hoopr_recount"] = {}
date_mismatch = []
for req in agg["requests"]:
    s, qd = req["season_file"], req["query_date"]
    d = frames[s]
    c = d["status_type_completed"].str.lower() == "true"
    x = d["notes_headline"].str.lower().str.contains("all-star|rising stars", na=False)
    n = int((c & ~x & (d["game_date"] == qd)).sum())
    E["bdl_hoopr_recount"][str(s)] = {"date": qd, "recount": n, "agg_claim": req["hoopr_games_on_date"],
                                      "bdl_returned": req["bdl_games_returned"]}
    if n != req["hoopr_games_on_date"]:
        date_mismatch.append((s, qd, n, req["hoopr_games_on_date"]))
E["bdl_date_counts_disagree"] = date_mismatch

# verify the 22 games' hoopR side against CSVs and the redacted BDL-side files
game_problems = []
for g in agg["games"]:
    s, gid = g["season_file"], g["game_id_hoopr"]
    row2 = frames[s][frames[s]["game_id"] == gid]
    if row2.empty:
        game_problems.append((s, gid, "missing in csv"))
        continue
    r = row2.iloc[0]
    if (r["game_date"] != g["hoopr"]["game_date_local"] or r["home_abbreviation"] != g["hoopr"]["home_abbr"]
            or r["away_abbreviation"] != g["hoopr"]["away_abbr"] or int(r["home_score"]) != g["hoopr"]["home_score"]
            or int(r["away_score"]) != g["hoopr"]["away_score"]
            or pd.Timestamp(r["start_date"]).isoformat().replace("+00:00", "Z") != g["hoopr"]["tip_utc"]):
        game_problems.append((s, gid, "csv-vs-agg field mismatch"))
    resp = BDLDIR / f"resp_{s}_{g['query_date']}.json"
    if not resp.exists():
        game_problems.append((s, gid, "resp file missing"))
        continue
    red = json.load(open(resp))
    cand = [x for x in red if x.get("id") == g["bdl_id"]]
    if not cand:
        game_problems.append((s, gid, "bdl_id not in redacted resp"))
        continue
    b = cand[0]
    if (b.get("home_team_score") != g["bdl"]["home_score"] or b.get("visitor_team_score") != g["bdl"]["away_score"]
            or b.get("home") != g["bdl"]["home_abbr"] or b.get("visitor") != g["bdl"]["away_abbr"]
            or (b.get("datetime") or "") != g["bdl"]["datetime_utc"]):
        game_problems.append((s, gid, "resp-vs-agg field mismatch"))
E["bdl_game_problems"] = game_problems
E["bdl_resp_files_present"] = sorted(p.name for p in BDLDIR.glob("resp_*.json"))
E["bdl_final_requests_le_25"] = bool(len(agg["requests"]) <= 25 and len(agg["games"]) <= 25)

# ------------------------------------------------------------- 7. handoff output hashes
for lane, hf in (("A_DATA", "handoff_A.json"), ("B_MECHANISMS", "handoff_B.json"), ("C_PROTOCOL", "handoff_C.json")):
    h = json.load(open(LANE.parent / lane / hf))
    bad = []
    for o in h.get("outputs", []):
        p = o.get("sha256")
        path = o.get("path", "")
        if not p or path.startswith("~"):
            continue
        fp = LANE.parent.parent / path
        if not fp.exists() or sha256(fp) != p:
            bad.append(path)
    E.setdefault("handoff_hash_mismatches", {})[lane] = bad

OUT = LANE / "verify_evidence.json"
OUT.write_text(json.dumps(E, indent=1, default=str))
print(json.dumps(E, indent=1, default=str))
