"""pipeline.py — PIPE lane recorder, cycle NFL-WINPROB-NG-SCORED-V1.

The REAL prediction-record pipeline, in execution order:

  (a) schedule load ........ schedule.load_snapshot (sha-pinned versioned snapshot)
  (b) STATE WARMUP ......... completed-game replay through the FROZEN arms
                             (B1* K=40 HCA=0 gamma=2/3; C3 theta=50 boundary
                             priors) — the state-carry law: completed-game
                             outcomes through the batch timestamp are consumed
                             for rating/prior UPDATE ONLY; no LL, no metric,
                             no per-game probability is computed on any
                             warmup game (grep-auditable: this module never
                             computes a logarithm).
  (c) BATCH PREDICT ........ target-week games predicted from the warmed state
                             in a single combined replay — identical-kickoff
                             exclusion is the frozen arms.batches law (games
                             sharing a kickoff are predicted from the
                             pre-batch state, updated after).
  (d) MARGIN CHECK ......... refuse unless batch_write_time + 6h <= first
                             kickoff of the batch (checked BEFORE any write;
                             failure raises MarginRefusal, nothing written).
  (e) LEDGER APPEND ........ through the ported nfl_ng_ledger@1 tool to the
                             TARGET PATH argument (real path only after owner
                             GO; all lane runs use sandbox paths).

ABSOLUTE: this module refuses to emit p_home for any REAL game. Only the
e2e-synth mode (SYNTH_-prefixed fixtures, 2027+ kickoffs) computes p values,
and only for synthetic games.
"""

from __future__ import annotations

import datetime as dt

# Fielded arms only (FREEZE_PACKET.md §1). C3_TWIN is diagnostic-only and is
# NEVER appended to any ledger by this recorder.
from frozen_refs import (
    B0_P_HOME_FROZEN,
    B0_P_HOME_LEDGER,
    C3_THETA,
    FIELDED_ARMS,
    MARGIN_HOURS,
    canonical_json,
    sha256_text,
)


class MarginRefusal(RuntimeError):
    """batch_write_time + 6h > first kickoff of the batch: the week is NOT
    capturable (FREEZE_PACKET.md §4 capture rule). Nothing is written."""


class BatchEmpty(RuntimeError):
    """The selected batch has zero predictable games."""


# ---------------------------------------------------------------------------
# (b) STATE WARMUP — aggregate counts only
# ---------------------------------------------------------------------------

def warmup_game_rows(sched_rows):
    """Warmup GameSet rows = the completed-game rows (see schedule.split_rows).
    Identity function kept for auditability of the boundary between (b) and (c)."""
    return list(sched_rows)


def warmup_aggregates(arms, warm_rows, z_table):
    """Run the state-carry warmup replay (B1* and C3) over the completed games
    and return AGGREGATE COUNTS ONLY.

    Counts (no probabilities, no metrics — by construction only the identity
    fields game_id/season/home/away of replay records are ever read here):
      - games processed (total; == len(warm_rows)) and per season
      - ratings-initialized lineages (unique home/away codes in the replay)
      - C3 boundary-prior applications per target season: the frozen replay
        applies theta*z_i(s) at a lineage's FIRST replayed game of season s
        iff (s, lg) in z_table (lazy reversion law, arms.replay_elo)
      - reversions without a prior entry (no z for that (season, lineage)) and
        first-season initializations (no reversion at all, frozen law)
      - B1*/C3 record-count equality (structural)
    """
    gs = _gameset(arms, warm_rows)
    recs_b1 = arms.replay_elo(gs)
    recs_c3 = arms.replay_elo(gs, z_table=z_table, theta=C3_THETA)
    if not (len(recs_b1) == len(recs_c3) == len(warm_rows)):
        raise AssertionError("warmup replay record count mismatch")
    per_season: dict[int, int] = {}
    lineages: set[str] = set()
    lineage_first_season: dict[str, int] = {}
    seen: set[tuple[str, int]] = set()
    prior_applied: dict[int, int] = {}
    reversion_no_prior: dict[int, int] = {}
    first_season_init: dict[str, int] = {}
    for r in recs_c3:
        per_season[r.season] = per_season.get(r.season, 0) + 1
        for lg in (r.home, r.away):
            lineages.add(lg)
            if lg not in lineage_first_season:
                lineage_first_season[lg] = r.season
                first_season_init[lg] = r.season
            key = (lg, r.season)
            if key in seen:
                continue
            seen.add(key)
            if r.season == lineage_first_season[lg]:
                continue  # first season in data: initialization, no reversion
            if (r.season, lg) in z_table:
                prior_applied[r.season] = prior_applied.get(r.season, 0) + 1
            else:
                reversion_no_prior[r.season] = reversion_no_prior.get(r.season, 0) + 1
    return {
        "warmup_games": len(warm_rows),
        "games_per_season": {str(k): per_season[k] for k in sorted(per_season)},
        "lineages_initialized": len(lineages),
        "lineage_codes": sorted(lineages),
        "lineages_first_season": {
            lg: lineage_first_season[lg] for lg in sorted(lineage_first_season)
        },
        "c3_prior_applied_per_season": {str(k): prior_applied[k] for k in sorted(prior_applied)},
        "c3_reversion_no_prior_per_season": {
            str(k): reversion_no_prior[k] for k in sorted(reversion_no_prior)
        },
        "z_table_entries": len(z_table),
        "record_counts_equal": len(recs_b1) == len(recs_c3),
        # in-memory handles for the predict stage of the SAME process (never
        # serialized into any warmup-check output):
        "_gs": gs,
        "_recs_b1": recs_b1,
        "_recs_c3": recs_c3,
    }


# ---------------------------------------------------------------------------
# (c)+(d) BATCH PREDICT + MARGIN
# ---------------------------------------------------------------------------

def select_target_games(sched, batch_ts_ns: int, target_season: int, target_week: int):
    """Target-week batch selection: ALL REG+POST games of (season, week) that
    are still future (kickoff >= batch time, no score). Games of the same week
    already completed at batch time are disclosed (they are NOT_RUN
    prospective forever — never predicted, never backfilled)."""
    df = sched.df
    w = df[(df["season"] == target_season) & (df["week"] == target_week)]
    ko = w["kickoff_ns"].to_numpy(dtype="int64")
    scored = (w["home_score"].notna() & w["away_score"].notna()).to_numpy()
    fut = w[(ko >= batch_ts_ns) & (~scored)]
    already = w[scored | (ko < batch_ts_ns)]
    games = []
    for row in fut.itertuples(index=False):
        games.append(dict(
            game_id=str(row.game_id),
            season=int(row.season),
            week=int(row.week),
            game_type=str(row.game_type),
            kickoff_ns=int(row.kickoff_ns),
            home_abbr=str(row.home_team),
            away_abbr=str(row.away_team),
            home_lg=str(row.home_lg),
            away_lg=str(row.away_lg),
            is_neutral=(row.location == "Neutral"),
        ))
    games.sort(key=lambda g: (g["kickoff_ns"], g["game_id"]))
    return games, [str(g) for g in already["game_id"].tolist()]


def check_margin(batch_write_utc: str, first_kickoff_utc: str, hours: float = MARGIN_HOURS) -> float:
    """FREEZE_PACKET.md §4 capture rule: the week is capturable iff the batch
    lands >= `hours` (frozen: 6) before the batch's FIRST scheduled kickoff
    UTC. Exact boundary passes (>=); anything shorter raises MarginRefusal."""
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    rec = dt.datetime.strptime(batch_write_utc, fmt).replace(tzinfo=dt.timezone.utc)
    kick = dt.datetime.strptime(first_kickoff_utc, fmt).replace(tzinfo=dt.timezone.utc)
    delta_h = (kick - rec).total_seconds() / 3600.0
    if delta_h < hours:
        raise MarginRefusal(
            f"capture-margin law: batch_write_time {batch_write_utc} + {hours}h > first "
            f"kickoff {first_kickoff_utc} (margin {delta_h:.4f}h < {hours}h) — week NOT "
            "capturable; refusing; NOTHING written"
        )
    return delta_h


def format_p_home(value: float) -> str:
    """Ledger R6 format: string with EXACTLY 6 fractional digits, strict (0,1).
    A value that rounds to 0.000000 or 1.000000 is a design bug -> abort."""
    s = f"{float(value):.6f}"
    if s in ("0.000000", "1.000000") or not (0.0 < float(s) < 1.0):
        raise RuntimeError(f"p_home {value!r} formatted to {s!r} violates strict (0,1); design bug; STOP")
    return s


def predict_target_week(arms, warm_rows, target_games, z_table):
    """(c) BATCH PREDICT for the 3 fielded arms.

    One combined replay per arm over warmup + target rows (kickoff order:
    warmup rows strictly precede target rows because target kickoffs are >=
    batch time and warmup kickoffs are < batch time). The target records are
    therefore a function of the warmed state only. Identical-kickoff
    exclusion: the frozen arms.batches splits the combined stream at equal
    kickoff timestamps, so same-kickoff target games are predicted from the
    pre-batch state and updated afterwards — they never inform each other.

    Target-row s_home values are PLACEHOLDERS (0.0). Their post-prediction
    updates can influence nothing we read (no rows follow the target batch),
    and label-independence is asserted by --selftest / e2e canaries.
    """
    if not target_games:
        raise BatchEmpty("target batch is empty — nothing to record")
    combined = list(warm_rows) + [
        dict(
            kickoff_ns=g["kickoff_ns"],
            home=g["home_lg"],
            away=g["away_lg"],
            s_home=0.0,  # placeholder; never used for prediction
            season=g["season"],
            week=g["week"],
            game_id=g["game_id"],
            is_neutral=g["is_neutral"],
        )
        for g in target_games
    ]
    gs = _gameset(arms, combined)
    n = len(target_games)
    recs_b1 = arms.replay_elo(gs)
    recs_c3 = arms.replay_elo(gs, z_table=z_table, theta=C3_THETA)
    tgt_b1 = recs_b1[-n:]
    tgt_c3 = recs_c3[-n:]
    if [r.game_id for r in tgt_b1] != [g["game_id"] for g in target_games]:
        raise AssertionError("target-record alignment failed (B1*)")
    if [r.game_id for r in tgt_c3] != [g["game_id"] for g in target_games]:
        raise AssertionError("target-record alignment failed (C3)")
    per_arm = {
        "B0": [B0_P_HOME_LEDGER for _ in target_games],
        "B1_STAR": [format_p_home(r.e_home) for r in tgt_b1],
        "C3": [format_p_home(r.e_home) for r in tgt_c3],
    }
    return per_arm, {"_gs": gs, "_recs_b1": recs_b1, "_recs_c3": recs_c3}


# ---------------------------------------------------------------------------
# (e) LEDGER APPEND (ported nfl_ng_ledger@1; TARGET PATH argument)
# ---------------------------------------------------------------------------

def append_batch_to_ledger(ledger, ledger_path, genesis_digest, cycle_id, season,
                           freeze_utc, batch_write_utc, target_games, per_arm,
                           inputs_digest, model_version, recorded_by, created_at_utc=None):
    """Create (first batch) or extend (later batches) the ledger at ledger_path
    through the PORTED tool. Row order: arms sorted (B0, B1_STAR, C3) x games
    sorted by (kickoff, game_id) — deterministic bytes. Margin MUST already be
    checked (append_batch_to_ledger re-asserts it defensively)."""
    first_kick = min(g["kickoff_ns"] for g in target_games)
    check_margin(
        batch_write_utc,
        dt.datetime.fromtimestamp(first_kick / 10**9, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    rows = ledger.load_rows(ledger_path) if ledger_path.exists() and ledger_path.stat().st_size else []
    appended = []
    gi_of = {g["game_id"]: i for i, g in enumerate(target_games)}
    for arm in FIELDED_ARMS:
        for g in target_games:
            if not rows and not appended:
                prev = f"GENESIS:{genesis_digest}"
            elif appended:
                prev = appended[-1]["row_hash"]
            else:
                prev = rows[-1]["row_hash"]
            row = {
                "schema_version": "nfl_ng_ledger@1",
                "cycle_id": cycle_id,
                "game_id": g["game_id"],
                "season": season,
                "game_type": g["game_type"],
                "home_team": g["home_abbr"],
                "away_team": g["away_abbr"],
                "kickoff_utc": dt.datetime.fromtimestamp(
                    g["kickoff_ns"] / 10**9, dt.timezone.utc
                ).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "recorded_at_utc": batch_write_utc,
                "arm_id": arm,
                "arm_config_digest": ARM_DIGESTS[arm],
                "model_version": model_version,
                "inputs_digest": inputs_digest,
                "p_home": per_arm[arm][gi_of[g["game_id"]]],
                "recorded_by": recorded_by,
                "prev_row_hash": prev,
            }
            appended.append(ledger.append(ledger_path, row))
    return appended


# populated by init_arm_digests() at CLI start (frozen_refs recompute + assert)
ARM_DIGESTS: dict[str, str] = {}


def init_arm_digests(frozen):
    got = frozen.verify_arm_config_digests()
    ARM_DIGESTS.update({k: v for k, v in got.items() if k in FIELDED_ARMS})
    return dict(ARM_DIGESTS)


def inputs_digest_real(snapshot_sha: str, pbp_pins: dict) -> str:
    manifest = {"schedule_snapshot": snapshot_sha}
    manifest.update({f"pbp_{y}": s for y, s in sorted(pbp_pins.items())})
    return sha256_text(canonical_json(manifest))


def inputs_digest_synth(fixture_sha: str, prior_table_sha: str) -> str:
    return sha256_text(canonical_json({
        "mode": "e2e-synth",
        "prior_e_table": prior_table_sha,
        "schedule_fixture": fixture_sha,
    }))


def recorder_config_digest(frozen) -> str:
    """Deterministic pipeline-config digest for model_version (no wall-clock)."""
    return sha256_text(canonical_json({
        "arm_config_digests": {a: frozen.ARM_CONFIG_DIGESTS[a] for a in FIELDED_ARMS},
        "b0_p_home_frozen": B0_P_HOME_FROZEN,
        "c3_theta": C3_THETA,
        "code_freeze_sha": frozen.CODE_FREEZE_SHA,
        "margin_hours": MARGIN_HOURS,
    }))


def _gameset(arms, rows):
    from schedule import rows_to_gameset

    return rows_to_gameset(arms, rows)
