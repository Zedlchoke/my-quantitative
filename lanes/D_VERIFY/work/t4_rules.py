#!/usr/bin/env python
"""D_VERIFY T4 — schema whitelist, outcome-column ban (schema+content), flag counts,
missing-data neutral-rule behavior."""
import json, os
import pandas as pd

DATA = os.path.expanduser("~/.my-quantitative-data")
WORK = "/Users/hoangminhlong/my-quantitative/.worktrees/nfl-playerfeat-prep-v1/integration/lanes/D_VERIFY/work"
tab = pd.read_parquet(f"{DATA}/nfl-playerfeat-prep-v1/features/nfl_playerfeat_table_v1.parquet")

KEY_COLS = ["game_id", "season", "week", "game_type", "side", "team", "opponent"]
ASOF_COLS = ["kickoff_utc", "rest_days", "n_prior_games_used", "asof_rule_version"]
G1_COLS = [f"qb_{m}_k{k}" for k in (3, 5) for m in
           ("yds", "td", "int", "att", "epa", "ypa", "epa_pa", "yds_form", "epa_form")] + \
          ["qb_yds_std_pg", "qb_epa_std_pg"]
G2_COLS = ["skill_top3_share_k3", "skill_hhi_k3", "skill_usage_pg_k3", "skill_top5_share_k5"]
G3_COLS = ["g3_top5_absent_share_recent", "g3_top5_newly_absent_count", "g3_n_snap_prior_games"]
FLAG_COLS = ["flag_no_prior_in_corpus", "flag_g1_window_truncated_k3",
             "flag_g1_window_truncated_k5", "flag_g2_zero_usage",
             "flag_g3_no_snap_prior", "flag_g3_pfr_null_excluded"]
WHITELIST = KEY_COLS + ASOF_COLS + G1_COLS + G2_COLS + G3_COLS + FLAG_COLS

res = {}
# 1. schema whitelist
res["schema_exact_match"] = list(tab.columns) == WHITELIST
res["shape"] = list(tab.shape)
res["rows_x_cols_claim"] = [1266, 44]
res["dup_game_side"] = int(tab.duplicated(["game_id", "side"]).sum())
print(f"schema exact 44-col whitelist: {res['schema_exact_match']}; shape={res['shape']}; "
      f"dup(game_id,side)={res['dup_game_side']}")

# 2. outcome ban: schema tokens + content scan
BANNED = ("score", "result", "winner", "margin", "spread", "moneyline", "odds",
          "win_prob", "winprob", "prob", "total", "overtime", "outcome", "vegas",
          "favorite", "underdog", "cover", "log_loss", "brier")
hits = [c for c in tab.columns if any(t in c.lower() for t in BANNED)]
res["banned_col_hits"] = hits
# content scan: non-whitelisted dtypes/objects would show; check all non-key cols numeric/int
# and that no column has string content beyond key/asof/version cols
str_like = [c for c in tab.columns
            if tab[c].dtype == object and c not in
            ("game_id", "game_type", "side", "team", "opponent", "kickoff_utc", "asof_rule_version")]
res["unexpected_object_cols"] = str_like
# asof version constant
res["asof_version_constant"] = tab["asof_rule_version"].nunique() == 1
res["asof_version_value"] = tab["asof_rule_version"].iloc[0]
# flags strictly 0/1
res["flags_binary"] = all(set(tab[c].dropna().unique()).issubset({0, 1}) for c in FLAG_COLS)
# kickoff format check
import re
res["kickoff_fmt_ok"] = bool(tab["kickoff_utc"].astype(str).str.match(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$").all())
print(f"banned col hits: {hits} (expect []); unexpected object cols: {str_like} (expect []); "
      f"asof const={res['asof_version_constant']} value={res['asof_version_value']}; "
      f"flags binary={res['flags_binary']}; kickoff fmt ok={res['kickoff_fmt_ok']}")

# 3. flag counts vs manifest
claims = {
    "flag_no_prior_in_corpus": 96, "flag_g3_no_snap_prior": 634,
    "flag_g3_pfr_null_excluded": 82, "flag_g2_zero_usage": 0,
    "flag_g1_window_truncated_k3": 192, "flag_g1_window_truncated_k5": 350,
}
res["flag_counts"] = {}
for c, exp in claims.items():
    got = int(tab[c].sum())
    res["flag_counts"][c] = {"got": got, "claimed": exp, "match": got == exp}
    print(f"{c}: got={got} claimed={exp} {'MATCH' if got == exp else 'MISMATCH'}")

per_season_claims = {
    2024: {"rows": 570, "no_prior": 32, "g3_no_snap": 570, "pfr_null": 0, "trunc3": 64, "trunc5": 128, "g1g2": 538, "g3_comp": 0},
    2025: {"rows": 570, "no_prior": 32, "g3_no_snap": 32, "pfr_null": 74, "trunc3": 64, "trunc5": 128, "g1g2": 538, "g3_comp": 538},
    2026: {"rows": 126, "no_prior": 32, "g3_no_snap": 32, "pfr_null": 8, "trunc3": 64, "trunc5": 94, "g1g2": 94, "g3_comp": 94},
}
res["per_season"] = {}
for s, cl in per_season_claims.items():
    d = tab[tab["season"] == s]
    got = {
        "rows": len(d),
        "no_prior": int(d["flag_no_prior_in_corpus"].sum()),
        "g3_no_snap": int(d["flag_g3_no_snap_prior"].sum()),
        "pfr_null": int(d["flag_g3_pfr_null_excluded"].sum()),
        "trunc3": int(d["flag_g1_window_truncated_k3"].sum()),
        "trunc5": int(d["flag_g1_window_truncated_k5"].sum()),
        "g1g2": int((d["n_prior_games_used"] > 0).sum()),
        "g3_comp": int(d["g3_n_snap_prior_games"].notna().sum()),
    }
    m = got == cl
    res["per_season"][s] = {"got": got, "claimed": cl, "match": m}
    print(f"season {s}: {got} {'MATCH' if m else 'MISMATCH vs ' + str(cl)}")

# 4. neutral-rule behavior
G1G2 = G1_COLS + G2_COLS
np_rows = tab[tab["flag_no_prior_in_corpus"] == 1]
bad_np = []
for c in ["rest_days"] + G1G2:
    if not np_rows[c].isna().all():
        bad_np.append(c)
res["no_prior_rows_all_nan"] = {"rows": len(np_rows), "non_nan_violations": bad_np,
                                "n_prior_all_zero": bool((np_rows["n_prior_games_used"] == 0).all())}
print(f"no-prior rows: {len(np_rows)}; all G1/G2/rest NaN: {not bad_np}; n_prior all 0: "
      f"{res['no_prior_rows_all_nan']['n_prior_all_zero']}")

ns_rows = tab[tab["flag_g3_no_snap_prior"] == 1]
g3bad = [c for c in G3_COLS if not ns_rows[c].isna().all()]
res["g3_no_snap_rows_nan"] = {"rows": len(ns_rows), "violations": g3bad,
                              "2024_all_flagged": bool(
                                  (tab[tab['season'] == 2024]['flag_g3_no_snap_prior'] == 1).all())}
print(f"g3_no_snap rows: {len(ns_rows)}; G3 all NaN: {not g3bad}; all 2024 rows flagged: "
      f"{res['g3_no_snap_rows_nan']['2024_all_flagged']}")

# converse: rows without flags have computable values
non_np = tab[tab["flag_no_prior_in_corpus"] == 0]
g1g2_nonnull = all(non_np[c].notna().all() for c in G1G2)
print(f"all {len(non_np)} non-no-prior rows have non-NaN G1/G2: {g1g2_nonnull}")
non_ns = tab[tab["flag_g3_no_snap_prior"] == 0]
comp = all(non_ns["g3_n_snap_prior_games"].notna().all() for _ in [0])
share_missing = int((non_ns["g3_top5_absent_share_recent"].isna()).sum())
res["converse"] = {"g1g2_nonnull": g1g2_nonnull, "g3_n_nonnull": comp,
                   "share_nan_despite_snap": share_missing}
print(f"non-no-snap rows ({len(non_ns)}): g3_n non-null: {comp}; absent_share NaN count: "
      f"{share_missing} (claim 0)")

# n_w=1 documented exception: absent share == 0.0 exactly
nw1 = tab[tab["g3_n_snap_prior_games"] == 1]
res["nw1"] = {"rows": len(nw1), "share_all_zero": bool((nw1["g3_top5_absent_share_recent"] == 0.0).all()),
              "newly_all_zero": bool((nw1["g3_top5_newly_absent_count"] == 0.0).all())}
print(f"n_w=1 rows: {len(nw1)}; absent share all 0.0 (documented): {res['nw1']['share_all_zero']}")

# NaN-never-0 spot: opener rows keep NaN not 0
op = tab[tab["flag_no_prior_in_corpus"] == 1]
res["opener_nan_not_zero"] = bool(op["qb_yds_k3"].isna().all() and not (op["qb_yds_k3"] == 0).any())

# trunc flag semantics
t3 = tab[tab["flag_g1_window_truncated_k3"] == 1]
t5 = tab[tab["flag_g1_window_truncated_k5"] == 1]
res["trunc_semantics"] = {
    "k3_in_1_2": bool(t3["n_prior_games_used"].isin([1, 2]).all()),
    "k5_in_1_4": bool(t5["n_prior_games_used"].isin([1, 2, 3, 4]).all()),
}
print(f"trunc k3 rows n_prior in {{1,2}}: {res['trunc_semantics']['k3_in_1_2']}; "
      f"trunc k5 rows n_prior in {{1..4}}: {res['trunc_semantics']['k5_in_1_4']}")

# sorting law: rows sorted by (kickoff_utc, game_id, side)
srt = tab.sort_values(["kickoff_utc", "game_id", "side"], kind="stable").reset_index(drop=True)
res["sorted_law"] = bool(srt["game_id"].equals(tab["game_id"].reset_index(drop=True)))
print(f"rows sorted by (kickoff_utc, game_id, side): {res['sorted_law']}")

# index/law columns
res["outcome_columns_total"] = len(hits) + len(str_like)
ok = (res["schema_exact_match"] and not hits and not str_like
      and res["asof_version_constant"] and res["flags_binary"] and res["kickoff_fmt_ok"]
      and all(v["match"] for v in res["flag_counts"].values())
      and all(v["match"] for v in res["per_season"].values())
      and not bad_np and not g3bad and share_missing == 0
      and res["nw1"]["share_all_zero"] and res["opener_nan_not_zero"]
      and res["trunc_semantics"]["k3_in_1_2"] and res["trunc_semantics"]["k5_in_1_4"]
      and res["sorted_law"] and res["dup_game_side"] == 0)
print(f"\nOVERALL T4 AUDIT: {'RULES_VERIFIED' if ok else 'DISCREPANCIES_FOUND'}")
res["overall_ok"] = bool(ok)
json.dump(res, open(f"{WORK}/t4_results.json", "w"), indent=2, default=str)
