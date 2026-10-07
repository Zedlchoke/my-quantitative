# test_dryrun_2026_remainder.py — Lane W26 SANDBOX dry-run (cycle
# WNBA-WINPROB-2026-REMAINDER-V1). SYNTHETIC ONLY: every game, id, team and
# result below is fabricated; zero real rows; no real-game probability.
#
# Proves, on the wnba_2026_remainder_ledger@1 port + the frozen B1-WNBA engine
# primitives (read-only import of the pinned arms.py):
#   D1 append-before-anchor ACCEPTED (full-slate ET-day batch recorded before
#      the T0-6h10m anchor);
#   D2 append AT the anchor and AFTER the anchor REFUSED (exclusive deadline);
#   D3 completed-only stream-state law (state at a batch anchor includes only
#      games with tip_utc < anchor AND result present);
#   D4 tamper detection (bit-flip + competent-rehash) and scoring fail-closed;
#   D5 batch snapshot law (one batch per ET day; same-tip games predicted from
#      one rating snapshot; updates only after the day's tips pass);
#   D6 partial-batch capture window (a game whose own anchor has not passed is
#      capturable alone after the day's earliest anchor, permanently consuming
#      the ET day — the one-batch-per-day + no-backfill laws hold);
#   D7 freeze-pin + window guards re-asserted in the dry-run context.
#
# Sandbox bytes land OUTSIDE git under
# ~/.my-quantitative-data/wnba-2026-remainder-v1/sandbox/dryrun-<runid>/
# (fall back to pytest tmp_path if the data root is unavailable).
#
# Run (worktree cwd):
#   /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest \
#       tests/papertrade_wnba26/test_dryrun_2026_remainder.py -q

import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

import wnba_2026_remainder_ledger as L

# ---------------------------------------------------------------- frozen engine (read-only)
FROZEN_ENGINE_DIR = Path(
    "/Users/hoangminhlong/my-quantitative/.worktrees/wnba-playerfeat-scored-v1"
    "/integration/lanes/T_SELECT")
sys.path.insert(0, str(FROZEN_ENGINE_DIR))
import arms  # noqa: E402  (pinned arms.py, sha 82263eab…; READ-ONLY import)

CYCLE = "SYN-W26-DRYRUN"
GENESIS = "d" * 64
DATA_ROOT = Path(os.path.expanduser(
    "~/.my-quantitative-data/wnba-2026-remainder-v1/sandbox"))

# B1-WNBA frozen constants (FREEZE_PACKET §1 verbatim)
K, HCA, GAMMA = 32, 50.0, 0.65


@pytest.fixture(scope="session")
def sandbox_dir() -> Path:
    """Fresh persistent sandbox run dir OUTSIDE git; tmp_path fallback."""
    base = None
    try:
        runid = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + \
            f"-p{os.getpid()}"
        base = DATA_ROOT / f"dryrun-{runid}"
        base.mkdir(parents=True, exist_ok=False)
    except OSError:
        base = None  # fall back to pytest tmp (handled per-test via mkdtemp)
    if base is None:
        base = Path(os.environ.get("W26_DRYRUN_FALLBACK", "/tmp")) / \
            f"w26-dryrun-fallback-{os.getpid()}"
        base.mkdir(parents=True, exist_ok=True)
    yield base
    # keep the sandbox bytes as persistent evidence (nothing cleans them here)


def _sandbox_ledger(sandbox_dir: Path, name: str) -> Path:
    p = sandbox_dir / f"predictions_{name}_2026.jsonl"
    L.create_ledger(p, GENESIS, name, 2026,
                    arm_registry=["B0", "B1-WNBA"],
                    freeze_utc="2026-10-07T00:00:00Z")
    return p


def _sf_row(game_id, tip_utc, local_date, recorded_at_utc, p_home="0.600000",
            home="SYN-HOME", away="SYN-AWAY", arm_id="B1-WNBA",
            cycle_id=CYCLE):
    return {
        "schema_version": L.SCHEMA_VERSION,
        "cycle_id": cycle_id,
        "game_id": game_id,
        "season": 2026,
        "game_type": "POST",
        "home_team": home,
        "away_team": away,
        "tip_utc": tip_utc,
        "local_date": local_date,
        "recorded_at_utc": recorded_at_utc,
        "arm_id": arm_id,
        "arm_config_digest": "b" * 64,
        "model_version": "b1-wnba-frozen-K32-HCA50-G065",
        "inputs_digest": "c" * 64,
        "p_home": p_home,
        "recorded_by": "SYN-W26-DRYRUN-RECORDER",
        "prev_row_hash": None,   # auto-chain
        "row_hash": None,
    }


def _sf_row_c(cyc, *args, **kw):
    return _sf_row(*args, cycle_id=cyc, **kw)


def _syn_game(gid, tip, season, fk_h, fk_a, home_win, neutral=False):
    return {"tip": tip, "game_id": gid, "season": season,
            "fk_home": fk_h, "fk_away": fk_a, "home_win": home_win,
            "neutral": neutral, "row_home": None, "row_away": None}


# ---------------------------------------------------------------- D1
def test_d1_append_before_anchor_accepted(sandbox_dir):
    """Full-slate ET-day batch (2026-style semifinal doubleheader) recorded
    strictly before the T0-6h10m anchor is ACCEPTED and verifies clean."""
    cyc = CYCLE + "-D1"
    p = _sandbox_ledger(sandbox_dir, cyc)
    # 2026-style ET-day 2026-10-07 slate: tips 23:30Z and next-day 01:30Z;
    # T0 = 23:30Z -> anchor 17:20:00Z (exclusive deadline)
    rows = [
        _sf_row_c(cyc, "SYN-SF2-A", "2026-10-07T23:30:00Z", "2026-10-07",
                "2026-10-07T17:00:00Z"),
        _sf_row_c(cyc, "SYN-SF2-B", "2026-10-08T01:30:00Z", "2026-10-07",
                "2026-10-07T17:10:00Z"),
    ]
    written = L.append_batch(p, rows)
    assert len(written) == 2
    assert L.verify_chain(p) == []
    res = L.validate_for_scoring(
        p, {"SYN-SF2-A": "2026-10-07T23:30:00Z",
            "SYN-SF2-B": "2026-10-08T01:30:00Z"})
    assert res["counts"] == {L.VALID_PROSPECTIVE: 2}
    (sandbox_dir / "d1_result.json").write_text(json.dumps({
        "proof": "D1 append-before-anchor accepted",
        "anchor_exclusive_deadline": "2026-10-07T17:20:00Z",
        "recorded_at": ["2026-10-07T17:00:00Z", "2026-10-07T17:10:00Z"],
        "rows_written": len(written), "chain": "intact",
        "scoring": res["counts"]}, indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- D2
def test_d2_append_at_anchor_refused(sandbox_dir):
    """A row stamped EXACTLY at the anchor (T0-6h10m) is REFUSED — the anchor
    is an exclusive deadline; nothing is written (atomic refusal)."""
    cyc = CYCLE + "-D2"
    p = _sandbox_ledger(sandbox_dir, cyc)
    rows = [_sf_row_c(cyc, "SYN-SF2-A", "2026-10-07T23:30:00Z", "2026-10-07",
                    "2026-10-07T17:20:00Z")]
    with pytest.raises(L.LedgerValidationError, match="STRICTLY before the batch"):
        L.append_batch(p, rows)
    assert p.read_text(encoding="utf-8") == ""


def test_d2b_append_after_anchor_refused(sandbox_dir):
    """A row stamped after the anchor (T0-6h10m + 1s) is REFUSED."""
    cyc = CYCLE + "-D2B"
    p = _sandbox_ledger(sandbox_dir, cyc)
    rows = [_sf_row_c(cyc, "SYN-SF2-B", "2026-10-08T01:30:00Z", "2026-10-07",
                    "2026-10-07T19:20:01Z")]  # 1s past SYN-SF2-B's own anchor
    with pytest.raises(L.LedgerValidationError, match="day-batch law"):
        L.append_batch(p, rows)
    assert p.read_text(encoding="utf-8") == ""
    (sandbox_dir / "d2_result.json").write_text(json.dumps({
        "proof": "D2 append-at-or-after-anchor refused",
        "at_anchor_172000Z": "refused (atomic, nothing written)",
        "after_anchor_192001Z": "refused (atomic, nothing written)"},
        indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- D3
def test_d3_completed_only_stream_state_law(sandbox_dir):
    """Stream state at a batch anchor includes ONLY games with tip_utc < anchor
    AND result present (completed only). Proven with the frozen engine's
    run_stream: the pre-tip snapshot prediction for the batch games equals the
    hand-computed logistic from the completed-only state; a no-result game and
    a post-anchor game never enter the state."""
    anchor = datetime(2026, 10, 7, 17, 20, tzinfo=timezone.utc)

    def parse(s):
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc)

    games = [
        # completed history (results present, tips strictly pre-anchor)
        _syn_game("SYN-H1", parse("2026-09-20T23:00:00Z"), 2026, "ATL", "NY", 1),
        _syn_game("SYN-H2", parse("2026-09-22T23:00:00Z"), 2026, "NY", "ATL", 0),
        _syn_game("SYN-H3", parse("2026-09-24T23:00:00Z"), 2026, "GS", "LV", 1),
        _syn_game("SYN-H4", parse("2026-09-26T23:00:00Z"), 2026, "LV", "GS", 0),
        _syn_game("SYN-H5", parse("2026-09-28T23:00:00Z"), 2026, "ATL", "GS", 1),
        # VIOLATORS that must be filtered out of the state:
        _syn_game("SYN-NORESULT", parse("2026-10-01T23:00:00Z"), 2026,
                  "NY", "LV", None),                      # tip < anchor, no result
        _syn_game("SYN-POSTANCHOR", parse("2026-10-07T23:30:00Z"), 2026,
                  "ATL", "NY", 1),                        # tip == batch T0, not < anchor
    ]

    # --- the stream-state law as a filter (the state builder's precondition)
    eligible = [g for g in games
                if g["tip"] < anchor and g["home_win"] is not None]
    assert [g["game_id"] for g in eligible] == \
        ["SYN-H1", "SYN-H2", "SYN-H3", "SYN-H4", "SYN-H5"], \
        "completed-only law: tip < anchor AND result present"

    # --- state at the anchor == frozen engine run over eligible games only
    preds_state, meta_state = arms.run_stream(
        eligible, k=K, hca=HCA, gamma=GAMMA)
    state_at_anchor = meta_state["final_ratings"]

    # --- batch predictions from that snapshot (frozen engine's tip-batching:
    #     the two remaining games share an exact tip -> one snapshot, updates
    #     applied only after the batch)
    batch = [
        _syn_game("SYN-SF2-A", parse("2026-10-07T23:30:00Z"), 2026, "ATL", "NY", 1),
        _syn_game("SYN-SF2-B", parse("2026-10-08T01:30:00Z"), 2026, "GS", "LV", 0),
    ]
    # NOTE: SF2-B's tip is NOT the same instant as SF2-A; the ledger day-batch
    # groups the ET day while the engine's exact-tip snapshot groups by tip.
    # For the snapshot proof we run the batch games through the engine AFTER
    # the completed history and read their pre-game predictions.
    preds_full, _ = arms.run_stream(eligible + batch, k=K, hca=HCA, gamma=GAMMA)
    p_by_id = {d["game_id"]: d["p_home"] for d in preds_full}

    # hand-computed logistic from the completed-only state (same formula, frozen)
    for gid, fk_h, fk_a in (("SYN-SF2-A", "ATL", "NY"),
                            ("SYN-SF2-B", "GS", "LV")):
        expected = arms.sigmoid_elo(
            state_at_anchor[fk_h] - state_at_anchor[fk_a] + HCA)
        assert abs(p_by_id[gid] - expected) < 1e-12, (
            f"{gid}: snapshot prediction {p_by_id[gid]} != completed-only "
            f"state prediction {expected}")
        # B0 floor cross-check (constant 0.603755) is NOT used for B1 rows
        assert 0.0 < p_by_id[gid] < 1.0

    (sandbox_dir / "d3_result.json").write_text(json.dumps({
        "proof": "D3 completed-only stream-state law",
        "anchor": "2026-10-07T17:20:00Z",
        "eligible_games": [g["game_id"] for g in eligible],
        "excluded_no_result": "SYN-NORESULT",
        "excluded_post_anchor": "SYN-POSTANCHOR",
        "state_at_anchor": state_at_anchor,
        "batch_snapshot_p_home": {k: round(v, 12) for k, v in p_by_id.items()
                                  if k.startswith("SYN-SF2")},
        "engine": "arms.py@82263eab (frozen, read-only import)",
        "constants": {"K": K, "HCA": HCA, "gamma": GAMMA}},
        indent=2, default=str) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- D4
def test_d4_tamper_detection_and_scoring_fail_closed(sandbox_dir):
    """Bit-flip tamper is flagged by the full re-hash walk and scoring refuses
    fail-closed; a competent re-hash tamper breaks the chain linkage instead."""
    cyc = CYCLE + "-D4"
    p = _sandbox_ledger(sandbox_dir, cyc)
    rows = [
        _sf_row_c(cyc, "SYN-SF2-A", "2026-10-07T23:30:00Z", "2026-10-07",
                "2026-10-07T17:00:00Z"),
        _sf_row_c(cyc, "SYN-SF2-B", "2026-10-08T01:30:00Z", "2026-10-07",
                "2026-10-07T17:10:00Z"),
    ]
    L.append_batch(p, rows)
    assert L.verify_chain(p) == []

    # bit flip on row 0 (original line saved for a true restore below)
    lines = p.read_text(encoding="utf-8").splitlines()
    original_line0 = lines[0]
    row = json.loads(lines[0])
    row["p_home"] = "0.999999"
    lines[0] = json.dumps(row, separators=(",", ":"), ensure_ascii=False)
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    broken = L.verify_chain(p)
    assert broken and broken[0] == 0
    with pytest.raises(L.LedgerIntegrityError, match="fail-closed"):
        L.validate_for_scoring(p, {"SYN-SF2-A": "2026-10-07T23:30:00Z",
                                   "SYN-SF2-B": "2026-10-08T01:30:00Z"})

    # true restore of row 0, then competent tamper (recomputed row hash) ->
    # the chain linkage breaks instead (row 1's prev points at the stale hash)
    lines = p.read_text(encoding="utf-8").splitlines()
    lines[0] = original_line0
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert L.verify_chain(p) == []
    lines = p.read_text(encoding="utf-8").splitlines()
    row0 = json.loads(lines[0])
    row0["p_home"] = "0.123456"
    row0["row_hash"] = L.compute_row_hash(row0, L.FIELD_ORDER)
    lines[0] = json.dumps(row0, separators=(",", ":"), ensure_ascii=False)
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert 1 in L.verify_chain(p)  # row 1's prev now points at a stale hash
    (sandbox_dir / "d4_result.json").write_text(json.dumps({
        "proof": "D4 tamper detection + scoring fail-closed",
        "bit_flip": "verify_chain -> [0]; validate_for_scoring raises",
        "competent_rehash": "verify_chain flags row 1 (stale chain parent)"},
        indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- D5
def test_d5_batch_snapshot_law_ledger_side(sandbox_dir):
    """Ledger-side batch snapshot law: ONE batch per ET day; a second batch for
    the same local_date is refused (no re-prediction, no backfill); ratings
    (engine side, D3) update only after the day's tips pass."""
    cyc = CYCLE + "-D5"
    p = _sandbox_ledger(sandbox_dir, cyc)
    first = [
        _sf_row_c(cyc, "SYN-SF2-A", "2026-10-07T23:30:00Z", "2026-10-07",
                "2026-10-07T17:00:00Z"),
        _sf_row_c(cyc, "SYN-SF2-B", "2026-10-08T01:30:00Z", "2026-10-07",
                "2026-10-07T17:00:00Z"),
    ]
    L.append_batch(p, first)
    # a later, different game on the SAME ET day -> refused
    second = [_sf_row_c(cyc, "SYN-LATE", "2026-10-07T20:00:00Z", "2026-10-07",
                      "2026-10-07T10:00:00Z")]
    with pytest.raises(L.LedgerValidationError, match="already has"):
        L.append_batch(p, second)
    assert len(L.load_rows(p)) == 2
    (sandbox_dir / "d5_result.json").write_text(json.dumps({
        "proof": "D5 batch snapshot law (one batch per ET day)",
        "second_batch_same_et_day": "refused (no re-prediction, no backfill)",
        "rows_on_disk": 2}, indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- D6
def test_d6_partial_batch_capture_window(sandbox_dir):
    """Disclosed partial-batch behavior: after ET-day 2026-10-07's earliest
    anchor (17:20Z) has passed but BEFORE game SYN-SF2-B's own anchor
    (19:20Z), a first-and-only batch containing SYN-SF2-B alone is ACCEPTED
    (gates on the batch's own earliest tip), permanently consuming the ET day:
    SYN-SF2-A can then never be recorded -> NOT_RUN forever (no backfill)."""
    cyc = CYCLE + "-D6"
    p = _sandbox_ledger(sandbox_dir, cyc)
    partial = [_sf_row_c(cyc, "SYN-SF2-B", "2026-10-08T01:30:00Z", "2026-10-07",
                       "2026-10-07T18:30:00Z")]
    (written,) = L.append_batch(p, partial)
    assert written["game_id"] == "SYN-SF2-B"
    # the earlier-tipped game can never be backfilled (one batch per day)
    late = [_sf_row_c(cyc, "SYN-SF2-A", "2026-10-07T23:30:00Z", "2026-10-07",
                    "2026-10-07T17:00:00Z")]
    with pytest.raises(L.LedgerValidationError, match="already has"):
        L.append_batch(p, late)
    res = L.validate_for_scoring(p, {"SYN-SF2-A": "2026-10-07T23:30:00Z",
                                     "SYN-SF2-B": "2026-10-08T01:30:00Z"})
    assert res["counts"].get(L.VALID_PROSPECTIVE) == 1
    assert res["not_run_games"] == ["SYN-SF2-A"]
    (sandbox_dir / "d6_result.json").write_text(json.dumps({
        "proof": "D6 partial-batch capture window",
        "captured": "SYN-SF2-B at 18:30:00Z (< its own anchor 19:20:00Z)",
        "permanently_not_run": "SYN-SF2-A (anchor 17:20:00Z passed; no backfill)",
        "scoring": res["counts"], "not_run_games": res["not_run_games"]},
        indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- D7
def test_d7_dryrun_boundary_and_pin_guards(sandbox_dir):
    """The dry-run writes ONLY inside its sandbox dir; the frozen engine pins
    and window guards hold in the dry-run context."""
    import hashlib

    def sha256_file(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()

    assert sha256_file(FROZEN_ENGINE_DIR / "arms.py") == \
        "82263eab713258b09ef920500a56d1fbf36ef9b9b8ea20965c6b4fd99b04cdd3"
    assert sha256_file(FROZEN_ENGINE_DIR / "harness.py") == \
        "b9446f7699ce2e29c8ce66490fc0f9941cc38dda0ed02e8e7fc108e65373485e"
    # sandbox confinement: nothing escaped upward
    assert sandbox_dir.resolve().is_relative_to(DATA_ROOT.resolve()) or \
        "w26-dryrun-fallback" in sandbox_dir.name
    # window guards: season/game_type enforced in the sandbox ledger too
    cyc = CYCLE + "-D7"
    p = _sandbox_ledger(sandbox_dir, cyc)
    bad = _sf_row_c(cyc, "SYN-REG", "2026-10-07T23:30:00Z", "2026-10-07",
                  "2026-10-07T17:00:00Z")
    bad["game_type"] = "REG"
    with pytest.raises(L.LedgerValidationError, match="window law"):
        L.append_batch(p, [bad])
    (sandbox_dir / "d7_result.json").write_text(json.dumps({
        "proof": "D7 dry-run boundary + pin guards",
        "engine_pins": "arms.py/harness.py == ERRATUM_R1 pins (re-measured)",
        "sandbox_dir": str(sandbox_dir),
        "window_law": "REG refused in sandbox ledger"}, indent=2) + "\n",
        encoding="utf-8")
