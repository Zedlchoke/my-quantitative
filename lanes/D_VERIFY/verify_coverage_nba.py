#!/usr/bin/env python
"""Lane D INDEPENDENT NBA coverage recompute: player_box game_id join vs schedule corpus."""
import os, json
import pandas as pd

SCHED = os.path.expanduser("~/.my-quantitative-data/nba-hoopr-v1/raw")
BOX = os.path.expanduser("~/.my-quantitative-data/playerdata-prep-v1/nba/player_box_raw")
report = {}
for y in (2016, 2021, 2026):
    s = pd.read_csv(os.path.join(SCHED, f"nba_schedule_{y}.csv"), low_memory=False)
    b = pd.read_csv(os.path.join(BOX, f"player_box_{y}.csv"), low_memory=False, usecols=["game_id","athlete_id","minutes","starter","did_not_play"])
    sched_ids = set(s["game_id"].astype(int))
    post = s[s["status_type_state"] == "post"]
    post_ids = set(post["game_id"].astype(int))
    postponed = post[post["status_type_name"].astype(str).str.contains("POSTPONED", case=False, na=False)]
    postpon_ids = set(postponed["game_id"].astype(int))
    played_ids = post_ids - postpon_ids
    box_ids = set(b["game_id"].astype(int))
    n_rows = len(b)
    n_dup = int(b.duplicated(["game_id","athlete_id"]).sum())
    join_played = box_ids & played_ids
    join_post = box_ids & post_ids
    gap_in_post = played_ids - box_ids
    gap_status = post[post["game_id"].astype(int).isin(gap_in_post)]["status_type_name"].value_counts().to_dict()
    # all schedule games (any state) missing from box, classified
    gap_all = sched_ids - box_ids
    gap_all_status = s[s["game_id"].astype(int).isin(gap_all)]["status_type_name"].value_counts().to_dict()
    orphans = box_ids - sched_ids
    r = {
        "season": y,
        "schedule_rows": len(s),
        "schedule_post_rows": len(post_ids),
        "postponed_post_rows": len(postpon_ids),
        "played_rows(post minus postponed)": len(played_ids),
        "box_rows": n_rows,
        "box_distinct_games": len(box_ids),
        "dup_game_athlete": n_dup,
        "join_vs_played": len(join_played),
        "join_vs_post_incl_postponed": len(join_post),
        "gap_played_not_in_box": len(gap_in_post),
        "gap_status_breakdown": gap_status,
        "gap_all_statuses": gap_all_status,
        "orphan_box_games": len(orphans),
        "claimed": {"2016": "1317/1317 rows 33715", "2021": "1172/1204 rows 31593, all gaps postponed", "2026": "1326/1330 rows 34883"}[str(y)],
    }
    report[y] = r
    print(json.dumps(r, indent=1))
with open(os.path.expanduser("~/my-quantitative/.worktrees/winprob-playerdata-prep-v1/integration/lanes/D_VERIFY/verify_coverage_nba_output.json"), "w") as f:
    json.dump(report, f, indent=1)
