# exec_fixture_builder.py — WNBA-PLAYERFEAT-SCORED-V1 · lane EXEC
#
# Deterministic builders for the 10-case gate fixture matrix. ALL data written by this
# module is synthetic (SYNTH_-prefixed ids, seasons 2027/2028, synthetic historical tip
# instants) — no real corpus byte is read or written. The registry fixtures carry only
# the public registry row fields (cycle_id/lifecycle/go_phrase/go_phrase_state/head).
#
# Interpreter: /Users/hoangminhlong/my-quantitative/.venv/bin/python

import datetime as dt
import hashlib
import json
import os
import random

import pandas as pd

WORKTREE = ("/Users/hoangminhlong/my-quantitative"
            "/.worktrees/wnba-playerfeat-scored-v1/integration")
S_SYNTH_FIXTURES = os.path.join(WORKTREE, "lanes/S_SYNTH/fixtures")
REAL_HEAD = "3bbd2b79190a162d1386f65e2a9c8ffb91d6c455"  # asserted == live HEAD at build
GO_PHRASE = "GO WNBA PLAYERFEAT SCORED V1 EVALUATION"
SEED = 20261005
SEASONS = (2027, 2028)
GAMES_PER_SEASON = 56  # 8 teams, double round robin
TEAMS = ["T%02d" % i for i in range(1, 9)]
SYNTH_TIPS = {2027: dt.datetime(2024, 6, 3, 23, 0, tzinfo=dt.timezone.utc),
              2028: dt.datetime(2025, 6, 2, 23, 0, tzinfo=dt.timezone.utc)}


def _sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


# ----------------------------------------------------------------- corpus
def build_games(seed=SEED, seasons=SEASONS, games_per_season=GAMES_PER_SEASON):
    """Deterministic synthetic schedule with planted strengths; season labels 2027/2028,
    tip instants synthetic-historical (2024/2025) so the tip_utc < run-time law is
    passable; 2 same-tip doubleheaders per season; 2 neutral rows per season."""
    rng = random.Random(seed)
    games = []
    strengths = {fk: 1500.0 + 60 * rng.uniform(-1, 1) for fk in TEAMS}
    gnum = 0
    for season in seasons:
        pairs = [(a, b) for i, a in enumerate(TEAMS) for b in TEAMS[i + 1:]]
        pairs = pairs + [(b, a) for a, b in pairs]  # double round robin = 56
        rng.shuffle(pairs)
        pairs = pairs[:games_per_season]
        base_tip = SYNTH_TIPS[season]
        season_last_tip = [None]
        neutral_slots = {5, 30}
        double_slots = {10, 40}  # game at slot shares the tip of slot-1 (doubleheader)
        for slot, (home, away) in enumerate(pairs):
            if slot in double_slots and season_last_tip[0] is not None:
                tip = season_last_tip[0]
            else:
                tip = base_tip + dt.timedelta(days=slot)
            season_last_tip[0] = tip
            neutral = slot in neutral_slots
            diff = strengths[home] - strengths[away] + (0.0 if neutral else 50.0)
            p = 1.0 / (1.0 + 10.0 ** (-diff / 400.0))
            games.append({
                "tip": tip, "game_id": "SYNTH_%d-%03d" % (season, slot),
                "season": season, "fk_home": home, "fk_away": away,
                "home_win": int(rng.random() < p), "neutral": neutral,
                "slot": slot,
            })
            gnum += 1
        # strengths drift between seasons (B1 signal)
        for fk in TEAMS:
            strengths[fk] += rng.uniform(-25, 25)
    games.sort(key=lambda g: (g["tip"], g["game_id"]))
    return games


def write_corpus(root, games, future_tip_game=None, empty_season=None, seed=SEED,
                 law_census_override=None):
    """Write the synthetic corpus in the REAL corpus formats:
    espn/wnba_schedule_<season>.csv + features/synth_player_features.parquet +
    manifest.json. `future_tip_game` re-dates one game to 2099 (fixture i).
    `empty_season` marks a season whose schedule rows are all pre/TBD (fixture j)."""
    espn_dir = os.path.join(root, "espn")
    feat_dir = os.path.join(root, "features")
    os.makedirs(espn_dir, exist_ok=True)
    os.makedirs(feat_dir, exist_ok=True)
    rows_by_season = {s: [] for s in SEASONS}
    for g in games:
        tip = g["tip"]
        if future_tip_game is not None and g["game_id"] == future_tip_game:
            tip = dt.datetime(2099, 1, 1, tzinfo=dt.timezone.utc)
        for side, fk, tid in (("home", g["fk_home"], TEAMS.index(g["fk_home"]) + 1),
                              ("away", g["fk_away"], TEAMS.index(g["fk_away"]) + 1)):
            rows_by_season[g["season"]].append((g, side, fk, tid, tip))
    manifest_census = {}
    for season in SEASONS:
        sched_rows = []
        seen = set()
        for g, side, fk, tid, tip in rows_by_season[season]:
            if g["game_id"] not in seen:
                seen.add(g["game_id"])
                sched_rows.append({
                    "id": g["game_id"], "game_id": g["game_id"], "season": season,
                    "date": tip.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "status_type_state": "post",
                    "status_type_name": "STATUS_FINAL",
                    "status_type_description": "Final",
                    "status_type_short_detail": "Final",
                    "neutral_site": str(g["neutral"]),
                    "home_id": TEAMS.index(g["fk_home"]) + 1,
                    "away_id": TEAMS.index(g["fk_away"]) + 1,
                    "home_abbreviation": g["fk_home"], "away_abbreviation": g["fk_away"],
                    "home_display_name": "Team " + g["fk_home"],
                    "away_display_name": "Team " + g["fk_away"],
                    "home_score": 85 if g["home_win"] else 80,
                    "away_score": 78 if g["home_win"] else 86,
                })
        if empty_season == season:
            for r in sched_rows:
                r["status_type_state"] = "pre"
                r["status_type_name"] = "STATUS_SCHEDULED"
                r["status_type_description"] = "TBD"
                r["status_type_short_detail"] = "TBD"
                r["home_score"] = 0
                r["away_score"] = 0
        # filter-law exercise rows (excluded from the universe by construction):
        sched_rows.append(dict(
            sched_rows[0], id="SYNTH_%d-PST" % season, game_id="SYNTH_%d-PST" % season,
            status_type_state="post", status_type_name="STATUS_POSTPONED",
            status_type_description="Postponed", status_type_short_detail="Postponed",
            home_score=0, away_score=0))
        sched_rows.append(dict(
            sched_rows[0], id="SYNTH_%d-TBD" % season, game_id="SYNTH_%d-TBD" % season,
            status_type_state="pre", status_type_name="STATUS_SCHEDULED",
            status_type_description="TBD", status_type_short_detail="TBD",
            home_score=0, away_score=0))
        df = pd.DataFrame(sched_rows)
        df.to_csv(os.path.join(espn_dir, "wnba_schedule_%d.csv" % season), index=False)
        manifest_census[str(season)] = 0 if empty_season == season else len(seen)

    # feature parquet (real corpus column names; PIT-legal columns only)
    feat_rows = []
    seen_game1 = set()
    for season in SEASONS:
        if empty_season == season:
            continue  # the season is absent from BOTH sides (census drift, not set drift)
        for g, side, fk, tid, tip in sorted(rows_by_season[season],
                                            key=lambda t: (t[4], t[0]["game_id"])):
            key1 = (fk, season)
            is_g1 = key1 not in seen_game1
            seen_game1.add(key1)
            neutral_reason = ""
            if season == 2027:
                c_val, c_reason = None, "expansion_no_prior"
            elif is_g1:
                c_val, c_reason = None, "game1_v2_roster_prior"
            else:
                c_val = round(0.65 + 0.30 * ((int(fk[1:]) % 97) / 97.0), 6)
                c_reason = ""
            xb_missing = (g["slot"] % 9 == 4)
            feat_rows.append({
                "game_id": g["game_id"], "season": season, "team_side": side,
                "team_id": tid, "team_display_name": "Team " + fk,
                "franchise_key": fk,
                "tip_utc": tip.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "is_team_game1": is_g1, "asof_rule_version": "tip_utc_strict_lt_v1",
                "continuity_c": c_val, "continuity_neutral_reason": c_reason,
                "b5_minutes_hhi": None if xb_missing else 0.118 + 0.01 * ((tid % 7) / 7.0),
                "b5_neutral_reason": "" if not xb_missing else "roster_file_missing_x0",
                "c_absence_share": None if xb_missing else 0.108 + 0.103 * ((tid % 5) / 5.0),
                "c_neutral_reason": "" if not xb_missing else "roster_file_missing_x0",
            })
    fdf = pd.DataFrame(feat_rows)
    feat_path = os.path.join(feat_dir, "synth_player_features.parquet")
    fdf.to_parquet(feat_path, index=False)

    manifest = {
        "schema": "wnba_exec_synth_corpus@1", "cycle": "WNBA-PLAYERFEAT-SCORED-V1",
        "lane": "EXEC", "synthetic_law": "ids SYNTH_-prefixed; season labels >= 2027; "
        "tip instants synthetic-historical (tip_utc < any real run time); no real byte",
        "seed": seed, "seasons": list(SEASONS),
        "census": law_census_override or manifest_census,
        "warmup_seasons": [], "ids_prefix": "SYNTH_",
        "feature_parquet": "synth_player_features.parquet",
        "n_games": len(set(g["game_id"] for g in games)),
    }
    with open(os.path.join(root, "manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return manifest


# ----------------------------------------------------------------- registry fixtures
def registry_row(head=REAL_HEAD, lifecycle="ACTIVE_LIGHT", state=None, phrase=GO_PHRASE):
    return {
        "cycle_id": "WNBA-PLAYERFEAT-SCORED-V1", "asset": "shared",
        "plan": "plans/PLAN_wnba_playerfeat_scored_v1.md", "lifecycle": lifecycle,
        "integration_worktree": os.path.join(WORKTREE), "branch":
            "orca/wnba-playerfeat-scored-v1-integration", "head": head,
        "go_phrase": phrase,
        "go_phrase_state": state or (
            "OWNER_GO_TYPED_LIVE 2026-10-06T00:00:00Z at head " + head),
    }


def write_registry(path, row):
    doc = {"schema": "cycle_registry@1",
           "note": "EXEC FIXTURE — synthetic registry for the gate matrix; NOT the real "
                   "registry (the real one is read-only and stays REGISTERED_NOT_CONSUMED)",
           "cycles": [row]}
    with open(path, "w") as fh:
        json.dump(doc, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return path


# ----------------------------------------------------------------- hand fixture
def copy_hand_fixture(dest_dir):
    """Byte-copy the S_SYNTH hand fixture (frozen cross-check truth) into exec_fixtures
    with sha provenance. S_SYNTH files are READ-ONLY for this lane."""
    os.makedirs(dest_dir, exist_ok=True)
    out = {}
    for name in ("expected_hand_fixture.json", "hand_fixture_predictions.csv"):
        src = os.path.join(S_SYNTH_FIXTURES, name)
        dst = os.path.join(dest_dir, name)
        with open(src, "rb") as f, open(dst, "wb") as g:
            g.write(f.read())
        out[name] = {"source": src, "sha256": _sha(src)}
    with open(os.path.join(dest_dir, "HAND_FIXTURE_PROVENANCE.json"), "w") as fh:
        json.dump({"law": "byte-copied from lanes/S_SYNTH/fixtures (frozen); S_SYNTH "
                          "derived these from the engine-law text with pure math, no "
                          "arms import", **out}, fh, indent=2)
        fh.write("\n")
    return out


def build_all(fixtures_dir, sandbox_dir):
    os.makedirs(fixtures_dir, exist_ok=True)
    os.makedirs(sandbox_dir, exist_ok=True)
    head_now = subprocess_head()
    if head_now != REAL_HEAD:
        raise AssertionError("worktree HEAD %s != fixture-pinned REAL_HEAD %s — the "
                             "freeze fixture must be regenerated" % (head_now, REAL_HEAD))
    corpus_root = os.path.join(fixtures_dir, "synth_corpus")
    games = build_games()
    manifest = write_corpus(corpus_root, games)
    # fixture (i): future-tipped variant
    write_corpus(os.path.join(fixtures_dir, "synth_corpus_futuretip"), games,
                 future_tip_game="SYNTH_2027-007")
    # fixture (j): empty-season variant (2028 declared with law census 56 but zero
    # universe games present -> G4 census refusal, no silent shrink)
    write_corpus(os.path.join(fixtures_dir, "synth_corpus_empty_2028"), games,
                 empty_season=2028, law_census_override={"2027": 56, "2028": 56})
    # registry fixtures
    write_registry(os.path.join(fixtures_dir, "registry_go_fixture.json"), registry_row())
    write_registry(os.path.join(fixtures_dir, "registry_head_mismatch.json"),
                   registry_row(head="0" * 40))
    copy_hand_fixture(os.path.join(fixtures_dir, "hand_fixture"))
    return {"corpus_root": corpus_root, "manifest": manifest,
            "n_games": manifest["n_games"]}


def subprocess_head():
    import subprocess
    p = subprocess.run(["git", "-C", WORKTREE, "rev-parse", "HEAD"],
                       capture_output=True, text=True, timeout=60)
    return p.stdout.strip()


if __name__ == "__main__":
    import sys
    fx = os.path.expanduser("~/.my-quantitative-data/wnba-playerfeat-scored-v1/exec_fixtures")
    sb = os.path.expanduser("~/.my-quantitative-data/wnba-playerfeat-scored-v1/exec_sandbox")
    info = build_all(fx, sb)
    print("FIXTURES BUILT: %d synthetic games/season census %s -> %s"
          % (info["n_games"], info["manifest"]["census"], fx))
    sys.exit(0)
