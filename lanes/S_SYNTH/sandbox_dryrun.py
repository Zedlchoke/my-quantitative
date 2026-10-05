"""sandbox_dryrun.py — S_SYNTH lane, cycle NFL-WINPROB-NG-SCORED-V1.

Full SAND Box dry-run of the prospective record pipeline on SYNTHETIC games:

  1. generate a synthetic universe (30 fabricated lineages SYN_T01..SYN_T30,
     two fabricated prior seasons 2028-2029, one fabricated target week in
     season 2030 — 15 games, ids SYNTH_2030_W1_G01..G15, kickoffs 2027+);
  2. compute p_home for the 3 FIELDED arms exactly per the freeze
     (FREEZE_PACKET.md §1): B0 constant 0.571399049390; B1* (K=40, HCA=0,
     gamma=2/3, mu=1500) replayed over the synthetic prior stream with the
     AS-FROZEN lanes/T_SELECT/arms.py; C3 (theta=50, config C3_T050) with
     synthetic prior-season EPA z values standardized by the frozen
     arms.z_standardize;
  3. append 15 x 3 = 45 rows through the PORTED ledger tool
     (research/control/NFL-WINPROB-NG-SCORED-V1/ledger/nfl_ng_ledger.py,
     sha256-pinned) into the sandbox ledger
     ~/.my-quantitative-data/nfl-ng-scored-v1/sandbox/
     predictions_NFL-WINPROB-NG-SCORED-V1-SANDBOX_2030.jsonl
     (tool §1 filename law; see PORT_NOTES.md §3.2) anchored to a SANDBOX
     GENESIS digest that is asserted != the freeze GENESIS digest
     ae99a803dfcc280e85d46bdc192a5b1a042320af127f688d66481ba3f1aaa3e7;
  4. validate: chain, (game,arm) uniqueness, row count, SYNTH_ prefix,
     freeze-genesis absence from file bytes, scoring-gate rehearsal;
  5. assert the REAL prediction ledger paths do NOT exist (loud failure with
     incident if any does — nothing is ever deleted).

No real game data is read anywhere; no outcome metric is computed; no betting
vocabulary. Deterministic end to end: two executions produce byte-identical
ledger files (evidence in DRYRUN_REPORT.md).

Usage:
  /Users/hoangminhlong/my-quantitative/.venv/bin/python lanes/S_SYNTH/sandbox_dryrun.py [--reset]
"""

from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

WORKTREE = Path(__file__).resolve().parent.parent.parent
PORTED_LEDGER = WORKTREE / "research" / "control" / "NFL-WINPROB-NG-SCORED-V1" / "ledger" / "nfl_ng_ledger.py"
FROZEN_ARMS = WORKTREE / "lanes" / "T_SELECT" / "arms.py"

SANDBOX_DIR = Path.home() / ".my-quantitative-data" / "nfl-ng-scored-v1" / "sandbox"

# ---- sandbox identity (clearly NOT the real cycle) -------------------------
CYCLE = "NFL-WINPROB-NG-SCORED-V1-SANDBOX"
SEASON = 2030
LEDGER_NAME = f"predictions_{CYCLE}_{SEASON}.jsonl"  # tool §1 filename law
LEDGER_PATH = SANDBOX_DIR / LEDGER_NAME
EVIDENCE_PATH = SANDBOX_DIR / "dryrun_evidence.json"
SANDBOX_FREEZE_UTC = "2030-09-01T00:00:00Z"
RECORDED_AT_UTC = "2030-09-05T12:00:00Z"  # >= 6h (in fact ~7 days) before first kickoff
RECORDED_BY = "S_SYNTH_SANDBOX_RECORDER"
MODEL_VERSION = "SYNTH-COMMIT-NFL-NG-SCORED-V1-SANDBOX+SYNTH-PIPE-SANDBOX"
CAPTURE_MARGIN_HOURS = 6.0  # FREEZE_PACKET.md §4 capture rule (caller-side law)

# ---- freeze references (PINNED values; used for identity/assertions only) ---
PORTED_LEDGER_SHA = "6fb0a1d41b347c16162742ee2591090d576af7633fd1d86b641d444156a1219c"
FROZEN_ARMS_SHA = "19dddd3ff2bec808e549981473e0523b4178cfd8c7c0db7c08b7e41a86d7d3e8"
FREEZE_GENESIS_DIGEST = "ae99a803dfcc280e85d46bdc192a5b1a042320af127f688d66481ba3f1aaa3e7"
FIELDED_ARMS = ("B0", "B1_STAR", "C3")
ARM_CONFIG_DIGESTS = {
    "B0": "bea17ae49a33e460912aa9bdf9c0266da22d81c5168e4490e35194e49a2154aa",
    "B1_STAR": "5c97475c5df745056429e3eb075386e9b4f85729dbb9722eaf409f4b7fcbf32a",
    "C3": "f7cde49880ee1f413f740c97a45ae4b863c017bf148326e116a7058126ecc74e",
}
B0_P_HOME_FROZEN = "0.571399049390"     # FREEZE_PACKET.md §1 slot 1 (12-dp frozen)
B0_P_HOME_LEDGER = "0.571399"           # same value at the ledger's R6 6-dp precision

# ---- sandbox GENESIS (NOT the freeze GENESIS) -------------------------------
SANDBOX_GENESIS_DESCRIPTOR = {
    "schema": "nfl_ng_sandbox_genesis@1",
    "kind": "SANDBOX_SYNTHETIC_GENESIS",
    "cycle_id": CYCLE,
    "season": SEASON,
    "note": (
        "sandbox dry-run genesis for S_SYNTH lane; synthetic games only; "
        "NOT the freeze GENESIS digest; no real prediction ledger is created"
    ),
}


def canonical_json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sandbox_genesis_digest() -> str:
    return sha256_hex(canonical_json(SANDBOX_GENESIS_DESCRIPTOR))


class SandboxError(RuntimeError):
    """Loud sandbox dry-run failure."""


# ---------------------------------------------------------------------------
# As-of input assembly + capture margin (caller-side laws, tested by pytest)
# ---------------------------------------------------------------------------


def prediction_inputs_asof(events, t_pred_ns: int):
    """As-of law: a game enters the prediction inputs iff its kickoff is
    STRICTLY BEFORE the prediction time. Games with kickoff >= t_pred
    (the canaries) can never inform a prediction made at t_pred."""
    return [e for e in events if e["kickoff_ns"] < t_pred_ns]


def enforce_capture_margin(recorded_at_utc: str, first_kickoff_utc: str,
                           min_hours: float = CAPTURE_MARGIN_HOURS) -> float:
    """FREEZE_PACKET.md §4: a week is capturable only if the batch lands
    >= 6h before the week's FIRST scheduled kickoff UTC. Caller-side law
    (the tool itself enforces only strict recorded_at < kickoff)."""
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    rec = dt.datetime.strptime(recorded_at_utc, fmt).replace(tzinfo=dt.timezone.utc)
    kick = dt.datetime.strptime(first_kickoff_utc, fmt).replace(tzinfo=dt.timezone.utc)
    hours = (kick - rec).total_seconds() / 3600.0
    if hours < min_hours:
        raise SandboxError(
            f"capture margin law violated: batch recorded_at {recorded_at_utc} is only "
            f"{hours:.4f}h before first kickoff {first_kickoff_utc}; requires >= {min_hours}h"
        )
    return hours


# ---------------------------------------------------------------------------
# Synthetic universe (deterministic; no real data anywhere)
# ---------------------------------------------------------------------------
LINEAGES = [f"SYN_T{i:02d}" for i in range(1, 31)]
PRIOR_SEASONS = (2028, 2029)
N_TARGET_GAMES = 15

TS_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _ns(iso: str) -> int:
    d = dt.datetime.strptime(iso, TS_FMT).replace(tzinfo=dt.timezone.utc)
    return int(d.timestamp()) * 10**9


def _iso_of_ns(ns: int) -> str:
    return dt.datetime.fromtimestamp(ns / 10**9, dt.timezone.utc).strftime(TS_FMT)


def build_synthetic_universe(target_labels="win_home"):
    """Returns (games, target_games) — list of dicts with kickoff_ns, home, away,
    s_home (fabricated), season, week, game_id, is_neutral.

    Prior seasons 2028-2029: 6 rounds x 30 games each, same-kickoff batches of 3,
    12h slot spacing. Target week 2030: 15 games over 5 days (3 kickoffs/day).
    ALL game ids SYNTH_-prefixed; ALL kickoffs 2027+ (2028-2030)."""
    games: list[dict] = []
    gid = 0
    base = _ns("2028-03-04T17:00:00Z")
    for season in PRIOR_SEASONS:
        season_base = base if season == 2028 else _ns("2029-03-04T17:00:00Z")
        for r in range(1, 7):
            for i in range(30):
                j = (i + r) % 30
                slot = gid // 3
                v = (gid * 37 + 11) % 9
                s_home = 1.0 if v < 4 else (0.5 if v == 4 else 0.0)
                games.append(dict(
                    kickoff_ns=season_base + slot * 43200 * 10**9,
                    home=LINEAGES[i], away=LINEAGES[j],
                    s_home=s_home, season=season, week=r,
                    game_id=f"SYNTH_{season}_PRIOR_G{gid:03d}",
                    is_neutral=(gid % 13 == 0),
                ))
                gid += 1
    n_prior = len(games)
    assert n_prior == 360

    target = []
    day_slots = ("17:00:00Z", "20:15:00Z", "23:30:00Z")
    for g in range(N_TARGET_GAMES):
        d, slot = divmod(g, 3)
        kickoff = _ns(f"2030-09-{12 + d:02d}T{day_slots[slot]}")
        s_home = 1.0 if target_labels == "win_home" else 0.0  # NEVER used for prediction
        target.append(dict(
            kickoff_ns=kickoff,
            home=LINEAGES[2 * g], away=LINEAGES[2 * g + 1],
            s_home=s_home, season=2030, week=1,
            game_id=f"SYNTH_2030_W1_G{g + 1:02d}",
            is_neutral=False,
        ))
    return games, target


def to_gameset(arms_mod, games):
    import numpy as np

    games = sorted(games, key=lambda g: g["kickoff_ns"])
    col = lambda name, dtype: np.array([g[name] for g in games], dtype=dtype)
    n = len(games)
    return arms_mod.GameSet(
        df=None,
        kickoff_ns=col("kickoff_ns", np.int64),
        kickoff_date=np.array([
            dt.datetime.fromtimestamp(g["kickoff_ns"] / 10**9, dt.timezone.utc).date().isoformat()
            for g in games
        ], dtype=object),
        home=col("home", object),
        away=col("away", object),
        s_home=col("s_home", float),
        y_bin=col("s_home", float),
        is_tie=np.array([g["s_home"] == 0.5 for g in games], dtype=bool),
        is_reg=np.ones(n, dtype=bool),
        is_neutral=col("is_neutral", bool),
        season=col("season", np.int64),
        week=col("week", np.int64),
        game_id=col("game_id", object),
        quarantined_columns=[],
        n_dropped_over_ceiling=0,
        n_pre_dropped=0,
    )


def synthetic_z_table(arms_mod):
    """Synthetic prior-season EPA z values for season 2030, standardized by the
    FROZEN arms.z_standardize (population sd across the 30 synthetic lineages)."""
    E = {lg: ((i * 17) % 23 - 11) * 0.03 for i, lg in enumerate(LINEAGES, start=1)}
    z = arms_mod.z_standardize(E)
    assert len(z) == len(LINEAGES) and all(v != 0.0 for v in z.values()), "degenerate synthetic z"
    return {(2030, lg): v for lg, v in z.items()}


def load_frozen_modules():
    def load(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod  # required: dataclass processing resolves cls.__module__
        spec.loader.exec_module(mod)
        return mod

    ledger = load("sandbox_ported_ledger", PORTED_LEDGER)
    arms = load("sandbox_frozen_arms", FROZEN_ARMS)
    return ledger, arms


# ---------------------------------------------------------------------------
# Main dry-run
# ---------------------------------------------------------------------------


def run(reset: bool = False) -> dict:
    import shutil

    # frozen-bytes guards (loud if the as-frozen code drifted)
    for path, expected in ((PORTED_LEDGER, PORTED_LEDGER_SHA), (FROZEN_ARMS, FROZEN_ARMS_SHA)):
        got = hashlib.sha256(path.read_bytes()).hexdigest()
        if got != expected:
            raise SandboxError(f"frozen bytes drifted: {path} sha256 {got} != {expected}")

    SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
    if reset:
        for p in (LEDGER_PATH, Path(str(LEDGER_PATH) + ".genesis.json"), EVIDENCE_PATH):
            if p.is_file():
                p.unlink()

    if LEDGER_PATH.exists() or Path(str(LEDGER_PATH) + ".genesis.json").exists():
        raise SandboxError(
            f"sandbox ledger already exists at {LEDGER_PATH}; refusing to recreate "
            "(append-only discipline). Re-run with --reset (removes ONLY the sandbox artifacts)."
        )

    ledger, arms = load_frozen_modules()
    sandbox_genesis = sandbox_genesis_digest()
    if sandbox_genesis == FREEZE_GENESIS_DIGEST:
        raise SandboxError("sandbox genesis digest collided with the freeze GENESIS digest")

    # --- synthetic universe + arm replays ------------------------------------
    games, target_games = build_synthetic_universe()
    gs = to_gameset(arms, games + target_games)
    zt = synthetic_z_table(arms)

    recs_b1 = arms.replay_elo(gs)                          # B1*: K=40, HCA=0, gamma=2/3
    recs_c3 = arms.replay_elo(gs, z_table=zt, theta=50.0)  # C3_T050
    assert len(recs_b1) == len(recs_c3) == len(games) + N_TARGET_GAMES

    # determinism: whole computation twice -> byte-identical
    recs_b1_2 = arms.replay_elo(gs)
    recs_c3_2 = arms.replay_elo(gs, z_table=zt, theta=50.0)
    ser = lambda rs: json.dumps(
        [{f: getattr(r, f) for f in r.__dataclass_fields__} for r in rs],
        sort_keys=True, separators=(",", ":")).encode("utf-8")
    if ser(recs_b1) != ser(recs_b1_2) or ser(recs_c3) != ser(recs_c3_2):
        raise SandboxError("C3/B1* replay not deterministic across runs")

    # as-of: target-week predictions must not depend on target-week labels
    gs_alt = to_gameset(arms, games + build_synthetic_universe(target_labels="lose_home")[1])
    alt_b1 = arms.replay_elo(gs_alt)
    alt_c3 = arms.replay_elo(gs_alt, z_table=zt, theta=50.0)
    for r1, r2 in zip(recs_b1[-N_TARGET_GAMES:], alt_b1[-N_TARGET_GAMES:]):
        if r1.e_home != r2.e_home or r1.r_home != r2.r_home:
            raise SandboxError("target-week labels leaked into B1* predictions")
    for r1, r2 in zip(recs_c3[-N_TARGET_GAMES:], alt_c3[-N_TARGET_GAMES:]):
        if r1.e_home != r2.e_home or r1.r_home != r2.r_home:
            raise SandboxError("target-week labels leaked into C3 predictions")

    # explicit as-of input-assembly check at the batch's recorded_at
    t_pred_ns = _ns(RECORDED_AT_UTC)
    inputs_asof = prediction_inputs_asof(games + target_games, t_pred_ns)
    asof_ids = {e["game_id"] for e in inputs_asof}
    if any(g["game_id"] in asof_ids for g in target_games):
        raise SandboxError("as-of violation: a target-week game entered the prediction inputs")
    if len(asof_ids) != len(games):
        raise SandboxError("as-of input set != synthetic prior stream")

    target_recs_b1 = recs_b1[-N_TARGET_GAMES:]
    target_recs_c3 = recs_c3[-N_TARGET_GAMES:]
    p_home = {
        "B0": [B0_P_HOME_LEDGER] * N_TARGET_GAMES,
        "B1_STAR": [f"{r.e_home:.6f}" for r in target_recs_b1],
        "C3": [f"{r.e_home:.6f}" for r in target_recs_c3],
    }

    # --- capture margin (freeze §4, caller-side) ------------------------------
    first_kick = _iso_of_ns(min(g["kickoff_ns"] for g in target_games))
    margin_hours = enforce_capture_margin(RECORDED_AT_UTC, first_kick)

    # --- create sandbox ledger (tool §1 filename law) -------------------------
    ledger.create_ledger(
        LEDGER_PATH,
        genesis_digest=sandbox_genesis,
        cycle_id=CYCLE,
        season=SEASON,
        arm_registry=list(FIELDED_ARMS),
        freeze_utc=SANDBOX_FREEZE_UTC,
        created_at_utc=SANDBOX_FREEZE_UTC,  # explicit: no wall-clock anywhere
    )

    inputs_digest = sha256_hex(canonical_json({
        "synthetic_epa_z_prior": "SYNTH_Z_2030_30LINEAGES",
        "synthetic_prior_stream": "SYNTH_2028_2029_360G",
        "synthetic_schedule": "SYNTH_2030_W1_15G",
    }))

    appended = []
    for arm in FIELDED_ARMS:
        for gi, g in enumerate(target_games):
            kickoff_iso = _iso_of_ns(g["kickoff_ns"])
            enforce_capture_margin(RECORDED_AT_UTC, kickoff_iso)  # per-row, >= 6h
            row = {
                "schema_version": "nfl_ng_ledger@1",
                "cycle_id": CYCLE,
                "game_id": g["game_id"],
                "season": SEASON,
                "game_type": "REG",
                "home_team": g["home"],
                "away_team": g["away"],
                "kickoff_utc": kickoff_iso,
                "recorded_at_utc": RECORDED_AT_UTC,
                "arm_id": arm,
                "arm_config_digest": ARM_CONFIG_DIGESTS[arm],
                "model_version": MODEL_VERSION,
                "inputs_digest": inputs_digest,
                "p_home": p_home[arm][gi],
                "recorded_by": RECORDED_BY,
                "prev_row_hash": (
                    f"GENESIS:{sandbox_genesis}" if not appended else appended[-1]["row_hash"]
                ),
            }
            appended.append(ledger.append(LEDGER_PATH, row))

    # --- post-append validation ------------------------------------------------
    broken = ledger.verify_chain(LEDGER_PATH)
    if broken:
        raise SandboxError(f"sandbox chain broken at indices {broken}")
    broken2 = ledger.verify_chain(LEDGER_PATH, expected_genesis_digest=sandbox_genesis)
    if broken2:
        raise SandboxError(f"sandbox chain broken vs expected genesis: {broken2}")

    rows = ledger.load_rows(LEDGER_PATH)
    if len(rows) != N_TARGET_GAMES * len(FIELDED_ARMS):
        raise SandboxError(f"row count {len(rows)} != {N_TARGET_GAMES}x{len(FIELDED_ARMS)}")
    pairs = [(r["game_id"], r["arm_id"]) for r in rows]
    if len(set(pairs)) != len(pairs):
        raise SandboxError("(game, arm) uniqueness violated")
    bad_ids = [r["game_id"] for r in rows if not r["game_id"].startswith("SYNTH_")]
    if bad_ids:
        raise SandboxError(f"non-SYNTH_ game ids present: {bad_ids}")

    ledger_bytes = LEDGER_PATH.read_bytes()
    sidecar_bytes = Path(str(LEDGER_PATH) + ".genesis.json").read_bytes()
    if FREEZE_GENESIS_DIGEST.encode() in ledger_bytes or FREEZE_GENESIS_DIGEST.encode() in sidecar_bytes:
        raise SandboxError("freeze GENESIS digest leaked into sandbox files")

    # append-only discipline: recreation refused
    try:
        ledger.create_ledger(LEDGER_PATH, sandbox_genesis, CYCLE, SEASON)
        raise SandboxError("create_ledger did NOT refuse an existing ledger")
    except ledger.LedgerValidationError:
        pass

    # scoring-gate rehearsal (kickoffs only; no outcomes joined, no metric computed)
    actual = {g["game_id"]: _iso_of_ns(g["kickoff_ns"]) for g in target_games}
    report = ledger.validate_for_scoring(LEDGER_PATH, actual)
    if report["counts"] != {"VALID_PROSPECTIVE": len(rows)}:
        raise SandboxError(f"scoring-gate rehearsal counts unexpected: {report['counts']}")
    if report["freeze_check"] != "APPLIED" or report["not_run_games"]:
        raise SandboxError(f"scoring-gate rehearsal: {report['freeze_check']} {report['not_run_games']}")

    # --- REAL ledger path absence --------------------------------------------
    real_paths_checked = [
        WORKTREE / "research/control/NFL-WINPROB-NG-SCORED-V1/ledger/prediction_ledger.jsonl",
        WORKTREE / "research/control/NFL-WINPROB-NG-SCORED-V1/ledger/predictions_NFL-WINPROB-NG-SCORED-V1_2026.jsonl",
        WORKTREE / "predictions",
        SANDBOX_DIR.parent / "predictions",
        SANDBOX_DIR.parent / "prediction_ledger.jsonl",
        SANDBOX_DIR.parent / "predictions_NFL-WINPROB-NG-SCORED-V1_2026.jsonl",
    ]
    existing = [p for p in real_paths_checked if p.exists()]
    stray = sorted(
        str(p) for p in (WORKTREE / "research/control/NFL-WINPROB-NG-SCORED-V1/ledger").glob("*.jsonl")
    )
    stray_data = sorted(
        str(p) for p in SANDBOX_DIR.parent.glob("*.jsonl")
    ) + sorted(
        str(p) for p in SANDBOX_DIR.parent.glob("predictions/*.jsonl")
    )
    if existing or stray or stray_data:
        raise SandboxError(
            "INCIDENT: a REAL prediction-ledger path exists — "
            f"checked={ [str(p) for p in real_paths_checked] } existing={ [str(p) for p in existing] } "
            f"stray_jsonl={ stray + stray_data }; deleting nothing; STOP."
        )

    evidence = {
        "schema": "nfl_ng_sandbox_dryrun_evidence@1",
        "lane": "S_SYNTH",
        "cycle": "NFL-WINPROB-NG-SCORED-V1",
        "sandbox_cycle_id": CYCLE,
        "sandbox_season": SEASON,
        "ledger_path": str(LEDGER_PATH),
        "ledger_sha256": hashlib.sha256(ledger_bytes).hexdigest(),
        "genesis_sidecar": str(LEDGER_PATH) + ".genesis.json",
        "sandbox_genesis_digest": sandbox_genesis,
        "freeze_genesis_digest_never_used": FREEZE_GENESIS_DIGEST,
        "freeze_genesis_digest_absent_from_bytes": True,
        "games": N_TARGET_GAMES,
        "arms": list(FIELDED_ARMS),
        "rows": len(rows),
        "unique_game_arm_pairs": len(set(pairs)),
        "all_game_ids_synth_prefixed": True,
        "chain_broken_indices": broken,
        "chain_expected_genesis_broken_indices": broken2,
        "capture_margin_hours": margin_hours,
        "recorded_at_utc": RECORDED_AT_UTC,
        "first_target_kickoff_utc": first_kick,
        "scoring_rehearsal_counts": report["counts"],
        "p_home_B0_constant_frozen": B0_P_HOME_FROZEN,
        "p_home_B1_STAR_first3": p_home["B1_STAR"][:3],
        "p_home_C3_first3": p_home["C3"][:3],
        "real_ledger_paths_checked": [str(p) for p in real_paths_checked],
        "real_ledger_paths_existing": [],
        "sorted_arm_order_preserved": True,
    }
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("SANDBOX DRY-RUN OK")
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return evidence


if __name__ == "__main__":
    run(reset="--reset" in sys.argv)
