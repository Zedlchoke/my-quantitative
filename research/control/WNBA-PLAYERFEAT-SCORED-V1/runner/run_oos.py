#!/usr/bin/env python
# run_oos.py — WNBA-PLAYERFEAT-SCORED-V1 · lane EXEC · REAL OOS runner (post-GO)
#
# Authority: DISPATCH_EXEC.md (lanes/DISPATCH), ERRATUM_R1 (lanes/FREEZE_ERRATUM_R1),
# WINDOW_RESOLUTION.md (lanes/EXEC). The frozen engine is lanes/T_SELECT/arms.py,
# imported AS-IS and sha-pinned (G2); this runner adds NO arm code.
#
# GATE CHAIN (each audited; distinct exit codes; NOTHING computed on refusal):
#   G1 AUTHORITY  (exit 2): registry row WNBA-PLAYERFEAT-SCORED-V1; lifecycle ACTIVE_*;
#                  go_phrase_state startswith OWNER_GO_TYPED_LIVE in the canonical form
#                  `OWNER_GO_TYPED_LIVE <utc-iso> at head <40-hex>`; registered phrase
#                  equality; GO-state head == row head. First gate — no data byte is read
#                  (and no code file is even hashed) before G1 passes.
#   G2 FREEZE     (exit 3): worktree HEAD == registry head; arms.py + harness.py sha256
#                  == ERRATUM_R1 pins; B1-WNBA constants in code == frozen
#                  K=32/HCA=50/gamma=0.65 and B0 == 0.603755 (literals asserted inside the
#                  gate); NO phi-arming path (the 2 frozen arms are the only armable ids;
#                  any feature-arm request refuses).
#   G3 LOCK       (exit 4): researchctl locks inspect == FREE_PROVEN, 3x60s retry.
#   G4 WINDOW     (exit 5): seasons argument law; every scored-window game tip_utc <
#                  run time; corpus census (frozen counts; refuse on any missing game,
#                  no silent shrink); universe set equality schedule-vs-feature-table.
#   G5 BATCH      (exit 6): single batch — one process computes both frozen arms on the
#                  identical game set; exact-arm record ids pairwise distinct; non-vacuous.
#
# On ALL-PASS: --source real replays warm-up 1997-2001 + stream 2002-2019 and predicts
# OOS 2020-2026 with B0 (constant 0.603755) and B1-WNBA (K=32, HCA=50, gamma=0.65);
# frozen metrics (LL primary; Brier; 10-bin reliability; calibration slope; paired dLL
# with tip-date-cluster bootstrap 10,000 resamples seed 20261005) and the frozen
# falsifier (REJECT-vs-B0 iff the pooled 95% CI of dLL includes 0 OR >= half of the
# season folds non-negative) are written to --out. --source synth runs the identical
# machinery on a declared synthetic corpus (synthetic seasons >= 2027 only; real OOS
# season ids are refused on the synthetic side by construction).
#
# Language law: calibration/forecasting vocabulary only. No wall-clock inside the
# metrics section (run timestamps live in the audit section only). $0. Interpreter:
# /Users/hoangminhlong/my-quantitative/.venv/bin/python

import argparse
import datetime as dt
import gzip
import hashlib
import json
import os
import re
import subprocess
import sys

# ------------------------------------------------------------------ frozen identity
CYCLE_ID = "WNBA-PLAYERFEAT-SCORED-V1"
GO_PHRASE = "GO WNBA PLAYERFEAT SCORED V1 EVALUATION"
GO_STATE_RE = re.compile(
    r"^OWNER_GO_TYPED_LIVE \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z at head [0-9a-f]{40}$")
DEFAULT_REGISTRY = "/Users/hoangminhlong/my-quantitative/plans/CYCLE_REGISTRY.json"
WORKTREE = "/Users/hoangminhlong/my-quantitative/.worktrees/wnba-playerfeat-scored-v1/integration"
T_SELECT_DIR = os.path.join(WORKTREE, "lanes/T_SELECT")
ARMS_PATH = os.path.join(T_SELECT_DIR, "arms.py")
HARNESS_PATH = os.path.join(T_SELECT_DIR, "harness.py")
REPO_ROOT = "/Users/hoangminhlong/my-quantitative"
RESEARCHCTL = os.path.join(REPO_ROOT, ".venv/bin/python")

# ERRATUM_R1 pins (T_SELECT-era bytes; S_SYNTH dryrun asserted the same values)
ARMS_SHA_PIN = "82263eab713258b09ef920500a56d1fbf36ef9b9b8ea20965c6b4fd99b04cdd3"
HARNESS_SHA_PIN = "b9446f7699ce2e29c8ce66490fc0f9941cc38dda0ed02e8e7fc108e65373485e"

# The ONLY armable ids (2 frozen arms; phi/feature arms have no acceptance path)
ACCEPTED_ARMS = "B0,B1-WNBA"

# Arm configuration USED BY THE STREAM — asserted equal to the law literals in G2.
# Tamper with these in a checked-out tree and G2 refuses (the law literals live inside
# the gate body, not here).
ARM_CONFIG = {"B1-WNBA": {"k": 32.0, "hca": 50.0, "gamma": 0.65}}
B0_P = 0.603755

OOS_SEASONS_LAW = tuple(range(2020, 2027))
BOOTSTRAP_N = 10000
SEED = 20261005
SLOPE_BAND = (0.85, 1.15)
REL_BINS = 10

# Frozen corpus census (universe games per season; source: COVERAGE_AUDIT.md §2 of
# WINPROB-PLAYERFEAT-PREP-V1 lane B — "Per-season 2002->2026 ... identical to the
# predecessor's measured list, row by row"; 2020 = 147 Wubble games REAL).
FROZEN_CENSUS = {
    2002: 271, 2003: 255, 2004: 237, 2005: 238, 2006: 257, 2007: 242, 2008: 259,
    2009: 242, 2010: 220, 2011: 224, 2012: 223, 2013: 221, 2014: 222, 2015: 225,
    2016: 220, 2017: 219, 2018: 220, 2019: 220,
    2020: 147, 2021: 210, 2022: 240, 2023: 261, 2024: 263, 2025: 311, 2026: 341,
}
WARMUP_ROWS_LAW = 1022  # stats-side 1997-2001 (SELECTION_REPORT §1)
UNIVERSE_TOTAL_LAW = 5988

REAL_ROOTS = {
    "feature_table_dir": os.path.expanduser(
        "~/.my-quantitative-data/playerfeat-prep-v1/wnba/features"),
    "roster_audit": os.path.expanduser("~/.my-quantitative-data/wnba-prep-v1/roster_audit"),
    "espn_schedules": os.path.expanduser("~/.my-quantitative-data/wnba-v1/raw/espn_schedules"),
    "stats_schedules": os.path.expanduser(
        "~/.my-quantitative-data/wnba-v1/raw/wnba_stats_schedules"),
    "selection_outputs": os.path.expanduser(
        "~/.my-quantitative-data/wnba-playerfeat-scored-v1/selection"),
}

EXIT_CODES = {"PASS": 0, "USAGE": 1, "G1": 2, "G2": 3, "G3": 4, "G4": 5, "G5": 6}


class Refusal(Exception):
    """Gate refusal: nothing computed. gate in {G1..G5}; code from EXIT_CODES."""

    def __init__(self, gate, reason, detail=None):
        super().__init__(reason)
        self.gate = gate
        self.reason = reason
        self.detail = detail or {}

    @property
    def exit_code(self):
        return EXIT_CODES[self.gate]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def get_worktree_head(worktree=WORKTREE):
    """Read-only git: rev-parse HEAD of the cycle worktree."""
    proc = subprocess.run(["git", "-C", worktree, "rev-parse", "HEAD"],
                          capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:
        raise Refusal("G2", "WORKTREE-HEAD-UNREADABLE",
                      {"stderr": proc.stderr[-200:]})
    return proc.stdout.strip()


# ------------------------------------------------------------------ G1 AUTHORITY
def gate_g1(registry_path):
    """Registry authority. Refuses BEFORE any data read / code hash."""
    try:
        with open(registry_path, "r") as fh:
            reg = json.load(fh)
    except OSError as e:
        raise Refusal("G1", "REGISTRY-UNREADABLE", {"path": registry_path, "err": str(e)})
    except json.JSONDecodeError as e:
        raise Refusal("G1", "REGISTRY-UNPARSEABLE", {"path": registry_path, "err": str(e)})
    rows = [c for c in reg.get("cycles", []) if c.get("cycle_id") == CYCLE_ID]
    if len(rows) != 1:
        raise Refusal("G1", "CYCLE-ROW-MISSING",
                      {"cycle_id": CYCLE_ID, "rows_found": len(rows)})
    row = rows[0]
    lifecycle = str(row.get("lifecycle", ""))
    state = str(row.get("go_phrase_state", ""))
    phrase = str(row.get("go_phrase", ""))
    detail = {"lifecycle": lifecycle, "go_phrase_state": state[:120],
              "registered_phrase_matches": phrase == GO_PHRASE}
    if not lifecycle.startswith("ACTIVE"):
        raise Refusal("G1", "LIFECYCLE-NOT-ACTIVE", detail)
    if phrase != GO_PHRASE:
        raise Refusal("G1", "REGISTERED-PHRASE-MISMATCH", detail)
    if not state.startswith("OWNER_GO_TYPED_LIVE"):
        raise Refusal("G1", "GO-NOT-TYPED-LIVE",
                      dict(detail, law="go_phrase_state must start with OWNER_GO_TYPED_LIVE "
                                       "(canonical: OWNER_GO_TYPED_LIVE <utc-iso> at head "
                                       "<40-hex>, identical to the NFL ERRATUM_R3 convention)"))
    if not GO_STATE_RE.match(state):
        raise Refusal("G1", "GO-STATE-MALFORMED",
                      dict(detail, law="state must match the canonical recorded form"))
    m = re.search(r"at head ([0-9a-f]{40})$", state)
    go_head = m.group(1)
    if go_head != str(row.get("head", "")):
        raise Refusal("G1", "GO-HEAD-ROW-COHERENCE-FAIL",
                      dict(detail, go_head=go_head, row_head=row.get("head")))
    return {"gate": "G1", "status": "PASS", "lifecycle": lifecycle,
            "go_phrase_state": state, "row_head": row.get("head"),
            "registry_path": registry_path}


# ------------------------------------------------------------------ G2 FREEZE
def gate_g2(args, g1_audit):
    """Freeze coherence: HEAD, sha pins, frozen constants, phi-arming law."""
    head = get_worktree_head()
    if head != str(g1_audit["row_head"]):
        raise Refusal("G2", "HEAD-MISMATCH",
                      {"worktree_head": head, "registry_head": g1_audit["row_head"]})
    if not os.path.exists(ARMS_PATH):
        raise Refusal("G2", "ARMS-FILE-MISSING", {"path": ARMS_PATH})
    arms_sha = sha256_file(ARMS_PATH)
    if arms_sha != ARMS_SHA_PIN:
        raise Refusal("G2", "ARMS-SHA-DRIFT", {"got": arms_sha, "pin": ARMS_SHA_PIN})
    harness_sha = sha256_file(HARNESS_PATH)
    if harness_sha != HARNESS_SHA_PIN:
        raise Refusal("G2", "HARNESS-SHA-DRIFT",
                      {"got": harness_sha, "pin": HARNESS_SHA_PIN})
    # Frozen law literals — asserted HERE, inside the gate body (a tampered module
    # constant cannot pass; see fixture (e) B1 HCA=51).
    LAW_B1 = (32.0, 50.0, 0.65)
    LAW_B0 = 0.603755
    cfg = ARM_CONFIG["B1-WNBA"]
    got_b1 = (float(cfg["k"]), float(cfg["hca"]), float(cfg["gamma"]))
    if got_b1 != LAW_B1:
        raise Refusal("G2", "B1-CONSTANT-DRIFT",
                      {"got": list(got_b1), "law": list(LAW_B1)})
    if float(B0_P) != LAW_B0:
        raise Refusal("G2", "B0-CONSTANT-DRIFT", {"got": B0_P, "law": LAW_B0})
    # phi law: no acceptance path for feature arms. The runner armable set is exactly
    # the 2 frozen ids; arm_feature_phi() unconditionally refuses.
    if args.arm != ACCEPTED_ARMS:
        raise Refusal("G2", "PHI-ARMING-REFUSED",
                      {"requested": args.arm, "accepted": ACCEPTED_ARMS,
                       "law": "feature arms (WF-A/WF-B/WF-C, any phi) are RELEASED and "
                              "have NO arming path in this runner; the batch is exactly "
                              "the 2 frozen arms B0 + B1-WNBA"})
    return {"gate": "G2", "status": "PASS", "worktree_head": head,
            "arms_sha256": arms_sha, "harness_sha256": harness_sha,
            "b1_constants": {"k": ARM_CONFIG["B1-WNBA"]["k"],
                             "hca": ARM_CONFIG["B1-WNBA"]["hca"],
                             "gamma": ARM_CONFIG["B1-WNBA"]["gamma"]},
            "b0_p_home": B0_P, "arms": ACCEPTED_ARMS}


def arm_feature_phi(*_a, **_k):
    """Trap: any attempt to arm a feature arm (phi != 0 / continuity modulation)
    refuses by construction. The 2 frozen arms are the only executable arms."""
    raise Refusal("G2", "PHI-ARMING-REFUSED",
                  {"law": "arm_feature_phi has no acceptance path: feature arms were "
                          "released at freeze (WF-B/WF-C phi=0-optimal == parent; WF-A "
                          "un-scored MACHINERY_SUSPECT); this runner executes exactly "
                          "B0 + B1-WNBA"})


# ------------------------------------------------------------------ G3 LOCK
def provide_lock_verdict(retries=3, wait_s=60):
    """Heavy-lock discipline: researchctl locks inspect from repo ROOT; 3x60s retry."""
    cmd = [RESEARCHCTL, "research/researchctl.py", "locks", "inspect"]
    attempts = []
    verdict = None
    for attempt in range(1, retries + 1):
        proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True,
                              timeout=120)
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError:
            payload = {"verdict": "PARSE_FAIL", "stdout": proc.stdout[:400],
                       "stderr": proc.stderr[:400]}
        verdict = payload.get("verdict")
        attempts.append({"attempt": attempt, "verdict": verdict})
        if verdict == "FREE_PROVEN":
            break
        if attempt < retries:
            import time
            time.sleep(wait_s)
    return {"verdict": verdict, "attempts": attempts, "attempts_used": len(attempts)}


def gate_g3(provider=None):
    provider = provider or provide_lock_verdict
    res = provider()
    if res.get("verdict") != "FREE_PROVEN":
        raise Refusal("G3", "LOCK-NOT-FREE", res)
    return {"gate": "G3", "status": "PASS", "verdict": "FREE_PROVEN",
            "attempts": res.get("attempts"), "attempts_used": res.get("attempts_used"),
            "lock_probe_injected": getattr(provider, "_injected", False)}


# ------------------------------------------------------------------ loaders (real)
# Real-path loaders are reachable ONLY after G1+G2+G3 pass and the G4 window law holds
# (main() calls them under that guarantee; the pre-GO proof never executes them).
FEATURE_PARQUET = os.path.join(
    REAL_ROOTS["feature_table_dir"], "wnba_player_features_2002_2026.parquet")
FEATURE_SHA256 = "ceaf10ba33e705b9569a11cec2aa33e1875e372c35d643ed5d80d5e757ffc7bf"
FEATURE_BYTES = 826415
ESPN_DIR = REAL_ROOTS["espn_schedules"]
STATS_DIR = REAL_ROOTS["stats_schedules"]
WARMUP_SEASONS = (1997, 1998, 1999, 2000, 2001)
XB_COL, XB_REASON = "b5_minutes_hhi", "b5_neutral_reason"
XC_COL, XC_REASON = "c_absence_share", "c_neutral_reason"
ALL_STAR_ALIASES = {"EAST", "WEST", "ALL", "USA", "DEL", "PAR", "WIL", "STE",
                    "CLA", "COL", "SPO", "COOP", "WNBASTARS"}


def _espn_rowmask(df):
    """Frozen filter law: status_type_state=='post'; drop Forfeit/Postponed; drop
    All-Star aliases; NEVER filter on score presence (0-0 prefill rows stay)."""
    import pandas as pd
    post = df["status_type_state"] == "post"
    bad = (df["status_type_name"].isin(["Forfeit", "Postponed"])
           | df["status_type_description"].fillna("").isin(["Forfeit", "Postponed"])
           | df["status_type_short_detail"].fillna("").isin(["Forfeit", "Postponed"]))
    alias = (df["home_abbreviation"].isin(ALL_STAR_ALIASES)
             | df["away_abbreviation"].isin(ALL_STAR_ALIASES))
    return post & ~bad & ~alias


def load_real_corpus(g4_audit):
    """Warm-up 1997-2001 + full universe 2002-2026. Census law: every season must
    match FROZEN_CENSUS exactly (no silent shrink); schedule/feature-table identity."""
    import pandas as pd
    sys.path.insert(0, T_SELECT_DIR)
    import harness as H  # frozen tree; sha pinned at G2; loaders below reuse its laws

    digest = H.sha256_file(FEATURE_PARQUET)
    if digest != FEATURE_SHA256 or os.path.getsize(FEATURE_PARQUET) != FEATURE_BYTES:
        raise Refusal("G4", "FEATURE-TABLE-DRIFT",
                      {"sha256": digest, "want": FEATURE_SHA256})

    lineage_abbr_to_fk = H.load_lineage()
    warmup = H.load_warmup(lineage_abbr_to_fk)
    if len(warmup) != WARMUP_ROWS_LAW:
        raise Refusal("G4", "WARMUP-CENSUS-MISMATCH",
                      {"got": len(warmup), "law": WARMUP_ROWS_LAW})

    frames = []
    for year in range(2002, 2027):
        path = os.path.join(ESPN_DIR, "wnba_schedule_%d.csv" % year)
        if not os.path.exists(path):
            raise Refusal("G4", "MISSING-SEASON-FILE", {"season": year, "path": path})
        frames.append(pd.read_csv(path, dtype={"game_id": str, "id": str}))
    esp = pd.concat(frames, ignore_index=True)
    uni = esp[_espn_rowmask(esp)].copy()
    uni = uni[uni["season"].between(2002, 2026)]

    ft = pd.read_parquet(FEATURE_PARQUET)
    ft_ids = set(ft["game_id"].astype(str))
    uni_ids = set(uni["game_id"].astype(str))
    if ft_ids != uni_ids:
        raise Refusal("G4", "UNIVERSE-SET-MISMATCH",
                      {"missing": len(ft_ids - uni_ids), "extra": len(uni_ids - ft_ids)})
    census = {int(s): int(n) for s, n in
              uni.groupby("season")["game_id"].nunique().items()}
    drift = {s: {"got": census.get(s), "law": FROZEN_CENSUS[s]}
             for s in FROZEN_CENSUS if census.get(s) != FROZEN_CENSUS[s]}
    if drift:
        raise Refusal("G4", "CENSUS-MISMATCH-NO-SILENT-SHRINK", {"drift": drift})

    feature_rows, games_index = {}, {}
    for r in ft.itertuples(index=False):
        gid, side = str(r.game_id), str(r.team_side)
        feature_rows[(gid, side)] = {
            "season": int(r.season), "franchise_key": str(r.franchise_key),
            "continuity_c": None if pd.isna(r.continuity_c) else float(r.continuity_c),
            "continuity_neutral_reason": str(r.continuity_neutral_reason),
            "xb": None if pd.isna(getattr(r, XB_COL)) else float(getattr(r, XB_COL)),
            "xb_reason": str(getattr(r, XB_REASON)),
            "xc": None if pd.isna(getattr(r, XC_COL)) else float(getattr(r, XC_COL)),
            "xc_reason": str(getattr(r, XC_REASON)),
        }
        games_index.setdefault(gid, {"season": int(r.season)})
    games = []
    for r in uni.itertuples(index=False):
        gid = str(r.game_id)
        neutral = bool(r.neutral_site) if not pd.isna(r.neutral_site) else False
        games.append({
            "tip": pd.Timestamp(str(r.date)).tz_convert("UTC"),
            "game_id": gid, "season": int(r.season),
            "fk_home": feature_rows[(gid, "home")]["franchise_key"],
            "fk_away": feature_rows[(gid, "away")]["franchise_key"],
            "home_win": int(int(r.home_score) > int(r.away_score)),
            "neutral": neutral,
            "row_home": feature_rows[(gid, "home")],
            "row_away": feature_rows[(gid, "away")],
        })
    full = H.build_full_games(warmup, games)
    full.sort(key=lambda g: (g["tip"], g["game_id"]))
    g4_audit["corpus"] = {
        "source": "real", "warmup_rows": len(warmup),
        "universe_games": len(games), "full_rows": len(full),
        "oos_census": {str(s): FROZEN_CENSUS[s] for s in OOS_SEASONS_LAW},
        "feature_table_sha256": digest,
    }
    return full


# ------------------------------------------------------------------ loaders (synth)
def load_synth_corpus(data_root, seasons, g4_audit):
    """Synthetic corpus-format fixtures (manifest-declared census; ids SYNTH_-prefixed;
    synthetic seasons >= 2027 only). Same filter/census/equality laws as the real side."""
    import pandas as pd
    man_path = os.path.join(data_root, "manifest.json")
    if not os.path.exists(man_path):
        raise Refusal("G4", "SYNTH-MANIFEST-MISSING", {"path": man_path})
    with open(man_path) as fh:
        man = json.load(fh)
    if sorted(seasons) != sorted(man["seasons"]):
        raise Refusal("G4", "SEASONS-MANIFEST-MISMATCH",
                      {"requested": list(seasons), "manifest": man["seasons"]})
    frames = []
    for year in seasons:
        path = os.path.join(data_root, "espn", "wnba_schedule_%d.csv" % year)
        if not os.path.exists(path):
            raise Refusal("G4", "MISSING-SEASON-FILE", {"season": year, "path": path})
        frames.append(pd.read_csv(path, dtype={"game_id": str, "id": str}))
    esp = pd.concat(frames, ignore_index=True)
    uni = esp[_espn_rowmask(esp)].copy()
    uni = uni[uni["season"].isin(seasons)]

    ft = pd.read_parquet(os.path.join(data_root, "features", man["feature_parquet"]))
    ft_ids = set(ft["game_id"].astype(str))
    uni_ids = set(uni["game_id"].astype(str))
    if ft_ids != uni_ids:
        raise Refusal("G4", "UNIVERSE-SET-MISMATCH",
                      {"missing": len(ft_ids - uni_ids), "extra": len(uni_ids - ft_ids)})
    census = {int(s): int(n) for s, n in
              uni.groupby("season")["game_id"].nunique().items()}
    drift = {str(s): {"got": census.get(s), "law": man["census"][str(s)]}
             for s in seasons if census.get(s) != man["census"][str(s)]}
    if drift:
        raise Refusal("G4", "CENSUS-MISMATCH-NO-SILENT-SHRINK", {"drift": drift})

    feature_rows = {}
    for r in ft.itertuples(index=False):
        gid, side = str(r.game_id), str(r.team_side)
        feature_rows[(gid, side)] = {
            "season": int(r.season), "franchise_key": str(r.franchise_key),
            "continuity_c": None if pd.isna(r.continuity_c) else float(r.continuity_c),
            "continuity_neutral_reason": str(r.continuity_neutral_reason),
            "xb": None if pd.isna(getattr(r, XB_COL)) else float(getattr(r, XB_COL)),
            "xb_reason": str(getattr(r, XB_REASON)),
            "xc": None if pd.isna(getattr(r, XC_COL)) else float(getattr(r, XC_COL)),
            "xc_reason": str(getattr(r, XC_REASON)),
        }
    games = []
    for r in uni.itertuples(index=False):
        gid = str(r.game_id)
        neutral = bool(r.neutral_site) if not pd.isna(r.neutral_site) else False
        games.append({
            "tip": pd.Timestamp(str(r.date)).tz_convert("UTC"),
            "game_id": gid, "season": int(r.season),
            "fk_home": feature_rows[(gid, "home")]["franchise_key"],
            "fk_away": feature_rows[(gid, "away")]["franchise_key"],
            "home_win": int(int(r.home_score) > int(r.away_score)),
            "neutral": neutral,
            "row_home": feature_rows[(gid, "home")],
            "row_away": feature_rows[(gid, "away")],
        })
    warmup_rows = 0  # manifest-declared synthetic warm-up (none for the exec fixtures)
    full = list(games)
    full.sort(key=lambda g: (g["tip"], g["game_id"]))
    g4_audit["corpus"] = {
        "source": "synth", "data_root": data_root, "warmup_rows": warmup_rows,
        "universe_games": len(games), "full_rows": len(full),
        "manifest_census": man["census"], "ids_prefix": man.get("ids_prefix", "SYNTH_"),
    }
    return full


# ------------------------------------------------------------------ G4 WINDOW
def gate_g4_window(source, seasons):
    """Seasons argument law (checked BEFORE any corpus read)."""
    if source == "real":
        if tuple(seasons) != OOS_SEASONS_LAW:
            raise Refusal("G4", "SEASONS-LAW-REAL",
                          {"got": list(seasons), "law": list(OOS_SEASONS_LAW),
                           "note": "WINDOW_RESOLUTION.md binds OOS = [2020..2026] exactly"})
    else:  # synth
        if not seasons or any(s < 2027 for s in seasons):
            raise Refusal("G4", "SEASONS-LAW-SYNTH",
                          {"got": list(seasons),
                           "law": "synthetic seasons must be >= 2027 (real OOS ids "
                                  "[2020..2026] are refused on the synthetic side)"})
    return {"gate": "G4", "status": "PASS", "stage": "seasons-law",
            "seasons": [int(s) for s in seasons], "source": source}


def gate_g4_runtime(full_games, seasons, run_time):
    """Every scored-window game tip_utc < run time (stale-corpus law)."""
    future = [{"game_id": g["game_id"], "tip_utc": str(g["tip"])}
              for g in full_games if g["season"] in seasons and g["tip"] >= run_time]
    if future:
        raise Refusal("G4", "FUTURE-TIPPED-GAME-AT-RUN-TIME",
                      {"n_future": len(future), "sample": future[:5],
                       "run_time_utc": run_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                       "law": "a scored-window game tipped at/after run time means the "
                              "corpus is stale or contaminated — refuse"})
    return {"gate": "G4", "status": "PASS", "stage": "run-time-tip-law",
            "future_tipped": 0, "run_time_utc": run_time.strftime("%Y-%m-%dT%H:%M:%SZ")}


# ------------------------------------------------------------------ scoring
def run_arms_predictions(full_games, seasons):
    """Single batch: both frozen arms on the IDENTICAL game list (one process).
    Returns {arm_id: predictions}; scored-window rows only are scored downstream."""
    sys.path.insert(0, T_SELECT_DIR)
    import arms  # frozen engine; sha pinned at G2
    if float(B0_P) != 0.603755 or (
            ARM_CONFIG["B1-WNBA"]["k"], ARM_CONFIG["B1-WNBA"]["hca"],
            ARM_CONFIG["B1-WNBA"]["gamma"]) != (32.0, 50.0, 0.65):
        raise Refusal("G2", "B1-CONSTANT-DRIFT", {"stage": "predict"})
    preds_b0, meta_b0 = arms.run_stream(full_games, p0=B0_P)
    cfg = ARM_CONFIG["B1-WNBA"]
    preds_b1, meta_b1 = arms.run_stream(full_games, k=cfg["k"], hca=cfg["hca"],
                                        gamma=cfg["gamma"])
    out = {"B0": [d for d in preds_b0 if d["season"] in seasons],
           "B1-WNBA": [d for d in preds_b1 if d["season"] in seasons]}
    meta = {"B0": {"n_stream_rows": meta_b0["n_games"]},
            "B1-WNBA": {"n_stream_rows": meta_b1["n_games"]}}
    return out, meta


def gate_g5(preds_by_arm, seasons, census_counts):
    """Single-batch law: identical game sets, pairwise-distinct exact-arm ids,
    non-vacuous, per-season census exact."""
    ids = {arm: [d["game_id"] for d in ps] for arm, ps in preds_by_arm.items()}
    arm_ids = list(ids)
    for a in arm_ids:
        if ids[a] != ids[arm_ids[0]]:
            raise Refusal("G5", "GAME-SETS-NOT-IDENTICAL", {"arms": arm_ids})
    for a, seq in ids.items():
        if len(seq) != len(set(seq)):
            raise Refusal("G5", "DUPLICATE-RECORD-IDS", {"arm": a})
    for a, seq in ids.items():
        if len(seq) < 1:
            raise Refusal("G5", "VACUOUS-ARM", {"arm": a, "n": len(seq)})
    by_season = {}
    for d in preds_by_arm[arm_ids[0]]:
        by_season[d["season"]] = by_season.get(d["season"], 0) + 1
    drift = {str(s): {"got": by_season.get(s), "law": census_counts[s]}
             for s in seasons if by_season.get(s) != census_counts[s]}
    if drift:
        raise Refusal("G5", "SCORED-CENSUS-DRIFT", {"drift": drift})
    return {"gate": "G5", "status": "PASS",
            "n_scored_per_arm": {a: len(s) for a, s in ids.items()},
            "identical_game_sets": True, "pairwise_distinct_ids": True,
            "per_season": {str(s): by_season[s] for s in seasons}}


def brier_score(preds):
    return sum((d["p_home"] - float(d["home_win"])) ** 2 for d in preds) / len(preds)


def reliability_10bin(preds, bins=REL_BINS):
    """Reliability term of the Brier decomposition: sum_b (n_b/N)(pbar_b - ybar_b)^2."""
    n = len(preds)
    if n == 0:
        return float("nan")
    tot = 0.0
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        sel = [d for d in preds if (lo <= d["p_home"] < hi)
               or (b == bins - 1 and d["p_home"] == 1.0)]
        if not sel:
            continue
        pb = sum(d["p_home"] for d in sel) / len(sel)
        yb = sum(float(d["home_win"]) for d in sel) / len(sel)
        tot += (len(sel) / n) * (pb - yb) ** 2
    return tot


def arm_metrics(preds):
    sys.path.insert(0, T_SELECT_DIR)
    import arms
    slope = arms.calibration_slope(preds)
    const = len({d["p_home"] for d in preds}) == 1
    return {
        "n": len(preds),
        "mean_ll": arms.mean_ll(preds),
        "brier": brier_score(preds),
        "reliability_10bin": reliability_10bin(preds),
        "calibration_slope": None if (slope != slope) else slope,  # nan -> null
        "slope_note": ("constant predictor — slope unidentifiable, honest nan per "
                       "frozen law" if const else
                       ("in band [0.85, 1.15]" if slope == slope and
                        SLOPE_BAND[0] <= slope <= SLOPE_BAND[1] else "OUT of band")),
        "by_season": {},
    }


def apply_falsifier(ci, per_season_dll, n_folds):
    """Frozen falsifier (packet §3 REJECT-vs-B0 rule, 7 OOS folds adaptation):
    REJECT-vs-B0 iff the pooled 95% paired date-cluster-bootstrap CI of dLL includes 0
    OR >= half of the season folds are non-negative ((n+1)//2 for odd n)."""
    lo, hi = ci["lo"], ci["hi"]
    ci_includes_0 = (lo <= 0.0 <= hi)
    nonneg = sum(1 for v in per_season_dll if v >= 0.0)
    thresh = (n_folds + 1) // 2
    fired = ci_includes_0 or (nonneg >= thresh)
    return {"rule": "REJECT-vs-B0 iff pooled 95% paired date-cluster-bootstrap CI of "
                    "dLL includes 0 OR >= half of season folds non-negative",
            "ci_includes_0": ci_includes_0,
            "folds_non_negative": nonneg, "n_folds": n_folds, "fold_threshold": thresh,
            "fold_condition_fired": nonneg >= thresh,
            "falsifier_fired": fired,
            "verdict": "REJECT_VS_B0" if fired else "NOT_REJECTED"}


def score_window(preds_by_arm, seasons):
    """Frozen metrics on the scored window: per-season folds + pooled + paired dLL
    bootstrap + falsifier. Deterministic (no wall-clock)."""
    sys.path.insert(0, T_SELECT_DIR)
    import arms
    metrics = {"seasons": [int(s) for s in seasons]}
    for arm, preds in preds_by_arm.items():
        m = arm_metrics(preds)
        for s in seasons:
            fold = [d for d in preds if d["season"] == s]
            m["by_season"][str(int(s))] = {
                "n": len(fold), "mean_ll": arms.mean_ll(fold),
                "brier": brier_score(fold),
                "reliability_10bin": reliability_10bin(fold),
                "calibration_slope": None, "slope_note": "fold-level slope not frozen; "
                "pooled slope is the frozen diagnostic"}
        metrics[arm] = m
    b1, b0 = preds_by_arm["B1-WNBA"], preds_by_arm["B0"]
    dll = arms.ll_delta(b1, b0)
    clusters = [str(d["tip"].date()) for d in b1]  # canonical tip UTC date (harness law)
    point, lo, hi = arms.date_cluster_bootstrap_ci(
        dll, clusters, n_resamples=BOOTSTRAP_N, seed=SEED)
    per_season_dll = []
    for s in seasons:
        f_b1 = [d for d in b1 if d["season"] == s]
        f_b0 = [d for d in b0 if d["season"] == s]
        per_season_dll.append(arms.mean_ll(f_b1) - arms.mean_ll(f_b0))
    ci = {"point": point, "lo": lo, "hi": hi}
    metrics["paired_dll_b1_vs_b0"] = {
        "definition": "LL(B1-WNBA) - LL(B0) per game; negative favors B1-WNBA",
        "point": point, "ci95": [lo, hi],
        "bootstrap": {"type": "tip-date-cluster", "n_resamples": BOOTSTRAP_N,
                      "seed": SEED, "n_clusters": len(set(clusters))},
        "per_season_dll": {str(int(s)): v for s, v in zip(seasons, per_season_dll)},
    }
    metrics["falsifier"] = apply_falsifier(ci, per_season_dll, len(seasons))
    return metrics


# ------------------------------------------------------------------ outputs
def write_predictions(out_dir, preds_by_arm):
    paths = {}
    for arm, preds in preds_by_arm.items():
        path = os.path.join(out_dir, "predictions_%s.csv" % arm.replace("-", "_").lower())
        with open(path, "w") as fh:
            fh.write("game_id,season,tip_utc,p_home,p_home_hex,home_win,neutral,flags\n")
            for d in preds:
                fh.write("%s,%d,%s,%r,%s,%d,%s,%s\n" % (
                    d["game_id"], d["season"],
                    d["tip"].strftime("%Y-%m-%dT%H:%M:%S%z"),
                    d["p_home"], float(d["p_home"]).hex(), d["home_win"],
                    d["neutral"], "|".join(d["flags"])))
        paths[arm] = path
    return paths


def write_results_md(out_dir, audit, metrics, seasons):
    f = metrics["falsifier"]
    lines = ["# OOS RUN RESULTS — %s" % CYCLE_ID, "",
             "Frozen 2-arm walk-forward evaluation; metrics are scored-window only.", ""]
    lines.append("- Source: %s · seasons: %s" % (audit["source"], list(seasons)))
    lines.append("- Arms: B0 (constant p=%.6f) and B1-WNBA (K=%g, HCA=%g, gamma=%g) — "
                 "sha-pinned frozen engine" % (B0_P, ARM_CONFIG["B1-WNBA"]["k"],
                                               ARM_CONFIG["B1-WNBA"]["hca"],
                                               ARM_CONFIG["B1-WNBA"]["gamma"]))
    lines.append("- Gates: G1 PASS · G2 PASS · G3 PASS (%s) · G4 PASS · G5 PASS"
                 % ("lock_probe_injected" if audit["gates"]["G3"].get(
                     "lock_probe_injected") else "FREE_PROVEN"))
    lines.append("")
    lines.append("| season | n | B0 LL | B1 LL | B0 Brier | B1 Brier | dLL (B1-B0) |")
    lines.append("|---|---|---|---|---|---|---|")
    for s in seasons:
        k = str(int(s))
        mb, m1 = metrics["B0"]["by_season"][k], metrics["B1-WNBA"]["by_season"][k]
        d = metrics["paired_dll_b1_vs_b0"]["per_season_dll"][k]
        lines.append("| %s | %d | %.6f | %.6f | %.6f | %.6f | %+.6f |"
                     % (k, mb["n"], mb["mean_ll"], m1["mean_ll"], mb["brier"],
                        m1["brier"], d))
    pb, p1 = metrics["B0"], metrics["B1-WNBA"]
    d = metrics["paired_dll_b1_vs_b0"]
    lines.append("| pooled | %d | %.6f | %.6f | %.6f | %.6f | %+.6f |"
                 % (pb["n"], pb["mean_ll"], p1["mean_ll"], pb["brier"], p1["brier"],
                    d["point"]))
    lines += ["", "## Pooled diagnostics", "",
              "- B0: reliability(10-bin) %.6f · slope %s (%s)"
              % (pb["reliability_10bin"],
                 "nan" if pb["calibration_slope"] is None else "%.4f" % pb["calibration_slope"],
                 pb["slope_note"]),
              "- B1-WNBA: reliability(10-bin) %.6f · slope %.4f (%s)"
              % (p1["reliability_10bin"], p1["calibration_slope"], p1["slope_note"]),
              "- Paired dLL = %+.6f [95%% CI %.6f, %.6f] (%s bootstrap, %d resamples, "
              "seed %d, %d tip-date clusters)"
              % (d["point"], d["ci95"][0], d["ci95"][1], d["bootstrap"]["type"],
                 d["bootstrap"]["n_resamples"], d["bootstrap"]["seed"],
                 d["bootstrap"]["n_clusters"]), "",
              "## Frozen falsifier", "",
              "- Rule: %s" % f["rule"],
              "- CI includes 0: %s · folds non-negative: %d/%d (threshold %d)"
              % (f["ci_includes_0"], f["folds_non_negative"], f["n_folds"],
                 f["fold_threshold"]),
              "- **Verdict: %s**" % f["verdict"], ""]
    with open(os.path.join(out_dir, "RESULTS.md"), "w") as fh:
        fh.write("\n".join(lines) + "\n")


# ------------------------------------------------------------------ main
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="REAL OOS runner — %s (post-GO; gate chain G1-G5)" % CYCLE_ID)
    ap.add_argument("--registry", default=DEFAULT_REGISTRY)
    ap.add_argument("--source", choices=["real", "synth"], default="real")
    ap.add_argument("--seasons", default=",".join(str(s) for s in OOS_SEASONS_LAW),
                    help="comma list; real law == 2020..2026 exactly; synth law >= 2027")
    ap.add_argument("--data-root", default=None,
                    help="synthetic corpus root (required for --source synth)")
    ap.add_argument("--arm", default=ACCEPTED_ARMS,
                    help="frozen batch law: exactly '%s'; anything else refuses" % ACCEPTED_ARMS)
    ap.add_argument("--out", required=True, help="results directory")
    args = ap.parse_args(argv)

    audit = {"cycle_id": CYCLE_ID, "runner": "run_oos.py", "source": args.source,
             "gates": {}, "started_utc": dt.datetime.now(dt.timezone.utc).strftime(
                 "%Y-%m-%dT%H:%M:%SZ")}
    audit["source_real_warning"] = (
        "real source computes OOS metrics on real seasons; pre-GO this refuses at G1"
        if args.source == "real" else "synthetic machinery run; no real data read")
    os.makedirs(args.out, exist_ok=True)

    def persist(audit_obj):
        path = os.path.join(args.out, "run_audit.json")
        with open(path, "w") as fh:
            json.dump(audit_obj, fh, indent=2, sort_keys=True, default=str)
            fh.write("\n")
        return path

    def refuse(exc):
        audit["gates"][exc.gate] = {"status": "REFUSED", "reason": exc.reason,
                                    "detail": exc.detail}
        audit["refusal"] = {"gate": exc.gate, "exit_code": exc.exit_code,
                            "reason": exc.reason,
                            "computed": "NOTHING — no corpus byte read past the "
                                        "refusing gate; no metric computed"}
        audit["finished_utc"] = dt.datetime.now(dt.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ")
        path = persist(audit)
        sys.stderr.write("%s REFUSED [%s]: %s\naudit: %s\n"
                         % (exc.gate, exc.reason,
                            json.dumps(exc.detail, default=str)[:400], path))
        return exc.exit_code

    try:
        # G1 — first gate: nothing else runs before it
        audit["gates"]["G1"] = gate_g1(args.registry)
        # G2 — freeze coherence (hashes worktree code files only)
        audit["gates"]["G2"] = gate_g2(args, audit["gates"]["G1"])
        # G3 — heavy lock
        audit["gates"]["G3"] = gate_g3()
        # G4 — window law (seasons) BEFORE corpus reads
        seasons = [int(s) for s in str(args.seasons).split(",") if s.strip()]
        audit["gates"]["G4"] = gate_g4_window(args.source, seasons)
        run_time = dt.datetime.now(dt.timezone.utc)
        if args.source == "real":
            full_games = load_real_corpus(audit["gates"]["G4"])
        else:
            if not args.data_root:
                raise Refusal("G4", "SYNTH-DATA-ROOT-MISSING", {})
            full_games = load_synth_corpus(args.data_root, seasons, audit["gates"]["G4"])
        census_counts = (
            {int(k): v for k, v in
             audit["gates"]["G4"]["corpus"]["oos_census"].items()}
            if args.source == "real" else
            {int(k): v for k, v in
             audit["gates"]["G4"]["corpus"]["manifest_census"].items()})
        rt = gate_g4_runtime(full_games, seasons, run_time)
        audit["gates"]["G4"]["run_time_tip_law"] = rt
        audit["gates"]["G4"]["reason"] = "PASS"
        # score (still nothing scored until G5 holds)
        preds_by_arm, arm_meta = run_arms_predictions(full_games, seasons)
        audit["gates"]["G5"] = gate_g5(preds_by_arm, seasons, census_counts)
        audit["arm_meta"] = arm_meta
        metrics = score_window(preds_by_arm, seasons)
        pred_paths = write_predictions(args.out, preds_by_arm)
        audit["outputs"] = {"predictions": pred_paths,
                            "results_md": os.path.join(args.out, "RESULTS.md")}
        audit["finished_utc"] = dt.datetime.now(dt.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ")
        persist(audit)
        write_results_md(args.out, audit, metrics, seasons)
        with open(os.path.join(args.out, "results.json"), "w") as fh:
            json.dump({"metrics": metrics,
                       "census": audit["gates"]["G4"]["corpus"],
                       "g5": audit["gates"]["G5"]}, fh, indent=2, sort_keys=True,
                      default=str)
            fh.write("\n")
        sys.stdout.write("OOS RUN PASS: arms %s · n=%d scored · dLL %+.6f [%.6f, %.6f] "
                         "· falsifier %s\n"
                         % (ACCEPTED_ARMS, audit["gates"]["G5"]["n_scored_per_arm"]["B0"],
                            metrics["paired_dll_b1_vs_b0"]["point"],
                            metrics["paired_dll_b1_vs_b0"]["ci95"][0],
                            metrics["paired_dll_b1_vs_b0"]["ci95"][1],
                            metrics["falsifier"]["verdict"]))
        return EXIT_CODES["PASS"]
    except Refusal as e:
        return refuse(e)
    except Exception as e:  # noqa: BLE001 — unexpected failure is a loud TECHABORT
        audit["unexpected"] = {"type": type(e).__name__, "message": str(e)[:400]}
        audit["finished_utc"] = dt.datetime.now(dt.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ")
        path = persist(audit)
        sys.stderr.write("TECHABORT: %s: %s\naudit: %s\n" % (type(e).__name__, e, path))
        return 70


if __name__ == "__main__":
    sys.exit(main())
