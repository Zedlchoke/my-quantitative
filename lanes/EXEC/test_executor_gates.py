"""test_executor_gates.py — EXEC lane 15-case gate-fixture matrix, cycle
NFL-WINPROB-NG-SCORED-V1.

Proves execute_post_go.py (gates G1–G8) on SYNTHETIC fixtures ONLY:

  (a) REAL registry as-is (REGISTERED_NOT_CONSUMED)  -> REFUSE G1 (exit 11),
      ZERO data read before refusal (proven with a sys.addaudithook open-audit)
  (b) fixture GO-typed-live + synthetic week-5 snapshot + sandbox ledger
      -> FULL PASS end-to-end: 8 games x 3 arms = 24 rows, chain valid,
      double-run byte-identical (ledger + genesis sidecar + registration payload)
  (c) CONSUMED state                                 -> REFUSE G1 (11)
  (d) DEAD lifecycle                                 -> REFUSE G1 (11)
  (e) wrong registered phrase                        -> REFUSE G1 (11)
  (f) head mismatch (registry head != worktree)      -> REFUSE G2 (12)
  (g) arm-file sha tamper (tampered freeze pin)      -> REFUSE G2 (12)
  (h) GENESIS digest mismatch (tampered R2 pin)      -> REFUSE G2 (12)
  (i) lock held (code-path injection; NOT_RUN_LOCK_SIM
      for the faithful-subprocess variant — the real
      lock path is untouchable by lane law)          -> REFUSE G3 (13)
  (j) snapshot sha mismatch                          -> REFUSE G4 (14)
  (k) future-game-with-score snapshot                -> REFUSE G4 (14)
  (l) week-4 batch (incl. 2026_04_ATL_NO canary)     -> REFUSE G5 (15)
  (m) margin 5.99 h                                  -> REFUSE G6 (16)
  (n) arm-set tamper (4th arm injected)              -> REFUSE G7 (17)
  (o) ledger chain pre-broken                        -> REFUSE G8 (18)

Every refusal case asserts its DISTINCT exit code and that NOTHING was
written except the gate log (the audit evidence). The pass case computes
p_home ONLY for SYNTH_-prefixed fixture games into a sandbox ledger; no real
game is ever predicted, no 2019+ outcome is evaluated, $0.

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python lanes/EXEC/test_executor_gates.py
"""

from __future__ import annotations

import contextlib
import csv
import datetime as dt
import io
import json
import shutil
import sys
from pathlib import Path

WORKTREE = Path("/Users/hoangminhlong/my-quantitative/.worktrees/nfl-winprob-ng-scored-v1/integration")
RECORDER_DIR = WORKTREE / "research" / "control" / "NFL-WINPROB-NG-SCORED-V1" / "recorder"
EXEC_DIR = WORKTREE / "lanes" / "EXEC"
REAL_REGISTRY = Path("/Users/hoangminhlong/my-quantitative/plans/CYCLE_REGISTRY.json")
REAL_FREEZE_ROOT = WORKTREE / "lanes"
EXECUTOR_PATH = RECORDER_DIR / "execute_post_go.py"
DATA_HOME = Path.home() / ".my-quantitative-data" / "nfl-ng-scored-v1"
FIXTURES = DATA_HOME / "exec_fixtures"
SANDBOX = DATA_HOME / "exec_sandbox"
INTERPRETER = "/Users/hoangminhlong/my-quantitative/.venv/bin/python"

for p in (str(RECORDER_DIR),):
    if p not in sys.path:
        sys.path.insert(0, p)

import frozen_refs as frozen  # noqa: E402
import execute_post_go as ex  # noqa: E402
import pipeline as rec_pipe  # noqa: E402
import priors as rec_priors  # noqa: E402
import schedule as rec_sched  # noqa: E402

CYCLE = "NFL-WINPROB-NG-SCORED-V1"
REGISTERED_HEAD = "876845e01932393319fcca05924dca0e8243744a"  # registry row head (read-only fact)
GO_INSTANT = "2026-10-08T12:00:00Z"  # SYNTHETIC typed-GO instant for fixture registries
GO_STATE = f"OWNER_GO_TYPED_LIVE {GO_INSTANT} at head {REGISTERED_HEAD}"
CANARY_ID = "2026_04_ATL_NO"  # real id, refused BY NAME at G5 before any computation
BATCH_OK = "2030-09-05T12:00:00Z"
TARGET_SEASON, TARGET_WEEK = 2030, 5
LINEAGES_N = 32
PRIOR_SEASONS = (2028, 2029)
FIXTURE_COLUMNS = [
    "game_id", "season", "game_type", "week", "gameday", "weekday", "gametime",
    "away_team", "away_score", "home_team", "home_score", "location",
    "old_game_id", "stadium", "roof", "surface", "div_game",
    "spread_line", "total_line", "away_moneyline", "home_moneyline",
    "away_rest", "home_rest",
]
LEDGER_NAME = f"predictions_{CYCLE}_{TARGET_SEASON}.jsonl"

G3_DISCLOSURE = {"mode": None, "real_observation": None}

RESULTS = []


def record(case, name, ok, detail=""):
    RESULTS.append({"case": case, "name": name, "verdict": "PASS" if ok else "FAIL",
                    "detail": detail})
    print(f"[{'PASS' if ok else 'FAIL'}] ({case}) {name}" + (f" — {detail}" if detail else ""))
    if not ok:
        raise AssertionError(f"case ({case}) {name} FAILED: {detail}")


# ---------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------

def fresh_dir(path: Path) -> Path:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def sha256_file(p) -> str:
    return frozen.sha256_file(p)


def canonical_json(obj) -> str:
    return frozen.canonical_json(obj)


def _slot_local(season: int, slot: int) -> dt.datetime:
    base = {2028: dt.datetime(2028, 3, 5, 13, 0), 2029: dt.datetime(2029, 3, 4, 13, 0)}[season]
    return base + dt.timedelta(hours=12 * slot)


def _prior_rows():
    rows = []
    gid = 0
    for season in PRIOR_SEASONS:
        for r in range(1, 7):
            for i in range(16):
                j = (i + r) % LINEAGES_N
                slot = gid // 2
                loc_dt = _slot_local(season, slot)
                v = (gid * 37 + 11 + (season - 2028) * 5) % 9
                s_home = 1.0 if v < 4 else (0.5 if v == 4 else 0.0)
                home_sc = 20 + (gid * 7) % 17
                if s_home == 1.0:
                    away_sc = home_sc - (3 + gid % 6)
                elif s_home == 0.5:
                    away_sc = home_sc
                else:
                    away_sc = home_sc + (3 + gid % 5)
                rows.append(dict(
                    game_id=f"SYNTH_{season}_R{r}_G{gid:03d}",
                    season=season, game_type="REG", week=r,
                    gameday=loc_dt.date().isoformat(), weekday=loc_dt.strftime("%A"),
                    gametime=loc_dt.strftime("%H:%M"),
                    away_team=f"SYT{j + 1:02d}", away_score=away_sc,
                    home_team=f"SYT{i + 1:02d}", home_score=home_sc,
                    location="Neutral" if gid % 13 == 0 else "Home",
                    old_game_id=str(2028000000 + gid), stadium="SYNTH_STADIUM",
                    roof="outdoors", surface="synthetic_grass", div_game=0,
                    spread_line=1.5, total_line=40.5,  # quarantine bait
                    away_moneyline=-110, home_moneyline=-110,  # quarantine bait
                    away_rest=7, home_rest=7,
                ))
                gid += 1
    assert gid == 192
    return rows


def _target_rows(week=TARGET_WEEK, season=TARGET_SEASON):
    """8 target games in 4 same-kickoff batches (the first kickoff is
    2030-09-12T17:00:00Z), plus 2 week-6 decoys the week filter must skip."""
    slots = [(9, 12, 13, 0), (9, 12, 13, 0), (9, 12, 16, 15), (9, 12, 16, 15),
             (9, 13, 13, 0), (9, 13, 13, 0), (9, 13, 16, 15), (9, 13, 16, 15)]
    rows = []
    for n in range(8):
        i, j = n, n + 8
        m, d, hh, mm = slots[n]
        loc_dt = dt.datetime(season, m, d, hh, mm)
        rows.append(dict(
            game_id=f"SYNTH_{season}_W{week}_G{n + 1:02d}",
            season=season, game_type="REG", week=week,
            gameday=loc_dt.date().isoformat(), weekday=loc_dt.strftime("%A"),
            gametime=loc_dt.strftime("%H:%M"),
            away_team=f"SYT{j + 1:02d}", away_score="",
            home_team=f"SYT{i + 1:02d}", home_score="",
            location="Home",
            old_game_id=str(season * 10**6 + n), stadium="SYNTH_STADIUM",
            roof="outdoors", surface="synthetic_grass", div_game=0,
            spread_line=2.5, total_line=41.5,
            away_moneyline=-105, home_moneyline=-115,
            away_rest=7, home_rest=7,
        ))
    for n in range(2):  # week-6 decoys (future, unscored; never selected at week 5)
        loc_dt = dt.datetime(season, 9, 19, 13, 0)
        rows.append(dict(
            game_id=f"SYNTH_{season}_W6_D{n + 1:02d}",
            season=season, game_type="REG", week=6,
            gameday=loc_dt.date().isoformat(), weekday=loc_dt.strftime("%A"),
            gametime="13:00",
            away_team=f"SYT{n + 2:02d}", away_score="",
            home_team=f"SYT{n + 1:02d}", home_score="",
            location="Home", old_game_id=str(season * 10**6 + 100 + n),
            stadium="SYNTH_STADIUM", roof="outdoors", surface="synthetic_grass",
            div_game=0, spread_line=2.5, total_line=41.5,
            away_moneyline=-105, home_moneyline=-115, away_rest=7, home_rest=7,
        ))
    return rows


def write_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIXTURE_COLUMNS, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return sha256_file(path)


def build_pass_snapshot(dest: Path) -> str:
    rows = _prior_rows() + _target_rows()
    return write_csv(dest, rows)


def build_future_score_snapshot(dest: Path) -> str:
    rows = _prior_rows() + _target_rows()
    for r in rows:
        if r["game_id"] == f"SYNTH_{TARGET_SEASON}_W{TARGET_WEEK}_G01":
            r["home_score"], r["away_score"] = 21, 17  # FUTURE game carrying a score
    return write_csv(dest, rows)


def build_week4_snapshot(dest: Path) -> str:
    """Season-2026 week-4 fixture games (fabricated matchups; the first id is
    the REAL canary 2026_04_ATL_NO, refused by name at G5 before any
    computation). Future, unscored, relative to batch 2026-10-05T12:00:00Z."""
    def row(gid, wk, gd, home, away):
        t = arms.kickoff_utc(gd, "13:00")
        return dict(
            game_id=gid, season=2026, game_type="REG", week=wk,
            gameday=gd, weekday="", gametime="13:00",
            away_team=away, away_score="", home_team=home, home_score="",
            location="Home", old_game_id="", stadium="SYNTH_STADIUM",
            roof="outdoors", surface="synthetic_grass", div_game=0,
            spread_line="", total_line="", away_moneyline="", home_moneyline="",
            away_rest=7, home_rest=7,
        )

    rows = [
        row(CANARY_ID, 4, "2026-10-04", "NO", "ATL"),
        row("2026_04_SYNTH_FAKE1", 4, "2026-10-04", "KC", "JAX"),
    ]
    return write_csv(dest, rows)


def build_prior_table(dest: Path) -> str:
    entries = {}
    for s in PRIOR_SEASONS:
        entries[str(s)] = {
            f"SYT{i + 1:02d}": ((i * 17) % 23 - 11) * 0.03 for i in range(LINEAGES_N)
        }
    doc = {"schema": rec_priors.PRIOR_E_TABLE_SCHEMA, "entries": entries}
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(doc, sort_keys=True) + "\n", encoding="utf-8")
    return sha256_file(dest)


def build_registry(dest: Path, **row_overrides) -> Path:
    data = json.loads(REAL_REGISTRY.read_text(encoding="utf-8"))
    rows = data["cycles"] if isinstance(data, dict) and "cycles" in data else data
    for r in rows:
        if isinstance(r, dict) and r.get("cycle_id") == CYCLE:
            r.update(row_overrides)
            break
    else:
        raise AssertionError("real registry has no row for the cycle")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return dest


def build_freeze_root(dest: Path) -> Path:
    """Fixture freeze root: verbatim copies of the real freeze artifacts plus a
    FIXTURE freeze packet (real bytes + appended marker line). The fixture
    freeze_digests.json and freeze_digests_r2.json are reconciled to the
    fixture packet bytes, so the whole chain recomputes consistently and NO
    real freeze digest anchors any sandbox ledger."""
    if dest.exists():
        shutil.rmtree(dest)
    (dest / "F_FREEZE").mkdir(parents=True)
    (dest / "FREEZE_ERRATUM_R2").mkdir(parents=True)
    (dest / "FREEZE_ERRATUM_R3").mkdir(parents=True)
    # fixture freeze packet = real bytes + marker (byte-different, fixture-only)
    real_packet = (REAL_FREEZE_ROOT / "F_FREEZE" / "FREEZE_PACKET.md").read_bytes()
    fixture_packet = real_packet + (
        "\n<!-- EXEC FIXTURE COPY — appended marker line; fixture freeze root of "
        "lanes/EXEC/test_executor_gates.py; the REAL freeze packet is untouched. -->\n"
    ).encode("utf-8")
    (dest / "F_FREEZE" / "FREEZE_PACKET.md").write_bytes(fixture_packet)
    fixture_packet_sha = sha256_file(dest / "F_FREEZE" / "FREEZE_PACKET.md")
    # verbatim copies
    shutil.copy(REAL_FREEZE_ROOT / "F_FREEZE" / "freeze_digests.json",
                dest / "F_FREEZE" / "freeze_digests.json")
    for name in ("ERRATUM_R2.md", "freeze_digests_r2.json", "CONTROLLER_ADDENDUM.md"):
        shutil.copy(REAL_FREEZE_ROOT / "FREEZE_ERRATUM_R2" / name,
                    dest / "FREEZE_ERRATUM_R2" / name)
    for name in ("ERRATUM_R3.md", "freeze_digests_r3.json"):
        shutil.copy(REAL_FREEZE_ROOT / "FREEZE_ERRATUM_R3" / name,
                    dest / "FREEZE_ERRATUM_R3" / name)
    # reconcile r1: pin the fixture packet sha
    r1p = dest / "F_FREEZE" / "freeze_digests.json"
    r1 = json.loads(r1p.read_text(encoding="utf-8"))
    r1["freeze_packet"]["sha256"] = fixture_packet_sha
    r1p.write_text(json.dumps(r1, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    # reconcile r2: the canonical payload's freeze_digest field + the recomputed pin
    r2p = dest / "FREEZE_ERRATUM_R2" / "freeze_digests_r2.json"
    r2 = json.loads(r2p.read_text(encoding="utf-8"))
    payload = json.loads(r2["genesis_r2"]["canonical_payload_v2"])
    payload["freeze_digest"] = fixture_packet_sha
    canonical = canonical_json(payload)
    r2["genesis_r2"]["canonical_payload_v2"] = canonical
    r2["genesis_r2"]["payload_sha256_pinned_r2"] = frozen.sha256_text(canonical)
    r2p.write_text(json.dumps(r2, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return dest


def patch_json(path: Path, mutate) -> Path:
    doc = json.loads(path.read_text(encoding="utf-8"))
    mutate(doc)
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Executor invocation + assertions
# ---------------------------------------------------------------------------

def run_executor(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = ex.main(argv)
    return code, out.getvalue(), err.getvalue()


def base_argv(out_dir: Path, registry: Path, snapshot: Path, snapshot_sha: str,
              freeze_root: Path, batch_time=BATCH_OK, week=TARGET_WEEK,
              season=TARGET_SEASON, prior_table=None):
    target = out_dir / LEDGER_NAME
    argv = [
        "--registry", str(registry),
        "--freeze-root", str(freeze_root),
        "--snapshot", str(snapshot),
        "--snapshot-sha256", snapshot_sha,
        "--data-manifest", str(FIXTURES / "data_manifest.json"),
        "--ledger-target", str(target),
        "--week", str(week),
        "--season", str(season),
        "--batch-time", batch_time,
        "--lock-wait-seconds", "0",
        "--prior-e-table", str(prior_table or FIXTURES / "prior_e_table.json"),
    ]
    return argv, target


def artifacts(out_dir: Path):
    """Everything in out_dir EXCEPT gate logs."""
    return sorted(
        p.relative_to(out_dir).as_posix() for p in out_dir.rglob("*") if p.is_file()
        and "gate_log" not in p.name
    )


def dir_state(out_dir: Path):
    """name -> byte size for every file except gate logs (pre/post comparison)."""
    return {p.relative_to(out_dir).as_posix(): p.stat().st_size
            for p in out_dir.rglob("*") if p.is_file() and "gate_log" not in p.name}


def gate_log_of(out_dir: Path) -> Path:
    return out_dir / (LEDGER_NAME + ".gate_log.jsonl")


def assert_refusal(case, name, out_dir: Path, code, want_gate, stderr,
                   pre_state=None, post_target_bytes=None):
    want_code = ex.GATE_EXITS[want_gate]
    record(case, f"{name}: exit code == {want_code}", code == want_code,
           f"got {code}; stderr tail: {stderr.strip()[-160:]!r}")
    if pre_state is None:
        record(case, f"{name}: nothing written except the gate log",
               artifacts(out_dir) == [], f"unexpected artifacts: {artifacts(out_dir)}")
    else:
        record(case, f"{name}: nothing written (pre-existing files byte-sizes unchanged)",
               dir_state(out_dir) == pre_state,
               f"state delta: {set(dir_state(out_dir).items()) ^ set(pre_state.items())}")
    if post_target_bytes is not None:
        record(case, f"{name}: target ledger bytes untouched",
               (out_dir / LEDGER_NAME).read_bytes() == post_target_bytes)
    log_lines = [json.loads(l) for l in gate_log_of(out_dir).read_text(encoding="utf-8").splitlines() if l.strip()]
    refused = [l for l in log_lines if l.get("verdict") == "REFUSE"]
    record(case, f"{name}: gate log records the {want_gate} refusal",
           bool(refused) and refused[-1]["gate"] == want_gate,
           f"refusal lines: {[l['gate'] for l in refused]}")
    record(case, f"{name}: refusal carries a loud detail",
           bool(refused) and len(refused[-1].get("detail", "")) > 20,
           refused[-1]["detail"][:120] if refused else "")


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------

def case_a_real_registry_refuses():
    out_dir = fresh_dir(SANDBOX / "case_a_real_registry")
    snap = FIXTURES / "games_pass.csv"  # exists by then; MUST NOT be opened
    snap_sha = sha256_file(snap)
    argv, _target = base_argv(out_dir, REAL_REGISTRY, snap, snap_sha, REAL_FREEZE_ROOT)
    opens = []
    hook_active = []

    def hook(event, args):
        if not hook_active:
            return
        if event == "open" and args and isinstance(args[0], (str, bytes)):
            opens.append(str(args[0]))

    sys.addaudithook(hook)
    hook_active.append(True)
    try:
        code, _out, err = run_executor(argv)
    finally:
        hook_active.clear()
    record("a", "REAL registry (REGISTERED_NOT_CONSUMED) refuses at G1 with exit 11",
           code == 11, f"exit={code}; stderr tail: {err.strip()[-140:]!r}")
    record("a", "gate log written (audit evidence)", gate_log_of(out_dir).is_file())
    record("a", "nothing else written", artifacts(out_dir) == [], str(artifacts(out_dir)))
    # zero-read proof: no data snapshot, no pbp, no T_SELECT, no freeze files
    bad = [o for o in opens if any(t in o for t in (
        "raw_schedules", "raw_pbp", "T_SELECT", "games.csv", "FREEZE_", "freeze_digests",
        "ERRATUM", "nfl_ng_ledger.py"))]
    record("a", "audit hook: NO data/freeze/code read before G1", bad == [], str(bad[:5]))
    data_home_opens = [o for o in opens
                       if ".my-quantitative-data" in o and "exec_sandbox" not in o]
    record("a", "audit hook: no data-home read outside the sandbox gate log",
           data_home_opens == [], str(data_home_opens[:5]))
    record("a", "audit hook: the registry itself was read (authority source)",
           any(o.endswith("CYCLE_REGISTRY.json") for o in opens), str(len(opens)) + " opens")


def case_b_full_pass():
    out1 = fresh_dir(SANDBOX / "case_b_run1")
    out2 = fresh_dir(SANDBOX / "case_b_run2")
    snap = FIXTURES / "games_pass.csv"
    snap_sha = sha256_file(snap)
    prior = FIXTURES / "prior_e_table.json"
    reports = []
    # G3 mode disclosure: real researchctl first; a genuine machine-wide hold by
    # a foreign worker (never touched) falls back to a code-injected FREE_PROVEN
    # observation through the gate's own injection seam — disclosed, never silent.
    disclosure = G3_DISCLOSURE
    disclosure["mode"] = None
    disclosure["real_observation"] = None
    real_runner = ex._default_lock_runner

    def disclosed_runner(researchctl_path, cwd):
        obs = real_runner(researchctl_path, cwd)
        v = obs.get("verdict")
        if v == "FREE_PROVEN":
            disclosure["mode"] = "REAL_RESEARCHCTL_FREE_PROVEN"
            return obs
        disclosure["real_observation"] = {"verdict": v, "reason": str(obs.get("reason", ""))[:200]}
        disclosure["mode"] = "INJECTED_FREE_PROVEN_REAL_LOCK_HELD"
        return {"verdict": "FREE_PROVEN",
                "evidence": {"flock_state": "free",
                             "note": ("code-injected observation; the REAL machine-wide heavy "
                                      "lock was held (%s) by a foreign worker that this lane "
                                      "must not touch" % v)}}

    ex._default_lock_runner = disclosed_runner
    try:
        for out_dir in (out1, out2):
            argv, target = base_argv(out_dir, FIXTURES / "registry_go.json", snap, snap_sha,
                                     FIXTURES / "freeze_root", prior_table=prior)
            code, out, err = run_executor(argv)
            if code != 0:
                record("b", "executor exit 0", False, f"exit={code}; {err.strip()[-300:]}")
                return
            reports.append(json.loads(out.split("EXECUTOR OK\n", 1)[1]))
    finally:
        ex._default_lock_runner = real_runner
    _ = reports
    ledger1, ledger2 = out1 / LEDGER_NAME, out2 / LEDGER_NAME
    record("b", "executor exit 0 on both runs", True)
    record("b", "G3 lock gate mode disclosed",
           disclosure["mode"] in ("REAL_RESEARCHCTL_FREE_PROVEN", "INJECTED_FREE_PROVEN_REAL_LOCK_HELD"),
           f"mode={disclosure['mode']} real_observation={disclosure['real_observation']}")
    ledger = frozen.load_ledger_tool()
    rows = ledger.load_rows(ledger1)
    record("b", "24 rows == 8 games x 3 arms", len(rows) == 24, f"rows={len(rows)}")
    pairs = {(r["game_id"], r["arm_id"]) for r in rows}
    record("b", "24 unique (game, arm) pairs", len(pairs) == 24, f"pairs={len(pairs)}")
    record("b", "only SYNTH_ fixture game ids",
           all(g.startswith("SYNTH_") for g, _ in pairs))
    record("b", "arms are exactly the 3 fielded arms",
           {a for _, a in pairs} == set(frozen.FIELDED_ARMS),
           str(sorted({a for _, a in pairs})))
    anchor = sha256_file(FIXTURES / "freeze_root" / "F_FREEZE" / "FREEZE_PACKET.md")
    broken = ledger.verify_chain(ledger1, expected_genesis_digest=anchor)
    record("b", "chain valid vs fixture freeze-packet anchor", broken == [], str(broken))
    ko = {r["game_id"]: r["kickoff_utc"] for r in rows}
    ts = lambda s: dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    record("b", "recorded_at_utc < kickoff_utc on every row",
           all(ts(r["recorded_at_utc"]) < ts(ko[r["game_id"]]) for r in rows))
    rep = ledger.validate_for_scoring(ledger1, ko, freeze_utc=GO_INSTANT)
    record("b", "scoring rehearsal: 24 VALID_PROSPECTIVE",
           rep["counts"] == {"VALID_PROSPECTIVE": 24}, str(rep["counts"]))
    reg = json.loads((out1 / (LEDGER_NAME + ".registration_genesis.json")).read_text())
    payload = reg["substituted_payload"]
    record("b", "registration payload: created_at == the registry GO instant",
           payload["created_at"] == GO_INSTANT, payload["created_at"])
    r2 = json.loads((FIXTURES / "freeze_root" / "FREEZE_ERRATUM_R2" / "freeze_digests_r2.json")
                    .read_text())
    r2fields = sorted(r2["genesis_r2"]["placeholder_fields"])
    pinned = json.loads(r2["genesis_r2"]["canonical_payload_v2"])
    diff = sorted(k for k in pinned if canonical_json(pinned[k]) != canonical_json(payload[k]))
    record("b", "substitution touches EXACTLY the two placeholders",
           diff == r2fields == ["created_at", "recorder_freeze_sha"], str(diff))
    record("b", "placeholder-form digest pinned and asserted pre-write",
           reg["placeholder_digest_pinned"] == r2["genesis_r2"]["payload_sha256_pinned_r2"])
    log_lines = [json.loads(l) for l in gate_log_of(out1).read_text().splitlines() if l.strip()]
    gates_passed = [l["gate"] for l in log_lines if l["verdict"] == "PASS"]
    record("b", "gate log shows G1..G8 PASS",
           gates_passed == ["G1", "G2", "G3", "G4", "G4", "G5", "G6", "G7", "G8", "G8", "G8"],
           str(gates_passed))
    b1, b2 = ledger1.read_bytes(), ledger2.read_bytes()
    s1 = (out1 / (LEDGER_NAME + ".genesis.json")).read_bytes()
    s2 = (out2 / (LEDGER_NAME + ".genesis.json")).read_bytes()
    r1b = (out1 / (LEDGER_NAME + ".registration_genesis.json")).read_bytes()
    r2b = (out2 / (LEDGER_NAME + ".registration_genesis.json")).read_bytes()
    record("b", "double-run deterministic (ledger bytes)",
           b1 == b2, f"len1={len(b1)} len2={len(b2)}")
    record("b", "double-run deterministic (genesis sidecar)", s1 == s2)
    record("b", "double-run deterministic (registration payload)", r1b == r2b)
    # sandbox hygiene: no real freeze digest in any sandbox artifact byte
    blob = b"".join(p.read_bytes() for p in (out1, out2) for p in p.rglob("*") if p.is_file())
    real_packet_sha = "9978a950cfa52f531c6cc1ccf650ca46cfcecb5a0d38c8468f6a66381ef70f6e"
    real_r2 = "bd94eb77d35077ac7bc1761a2c61031a1cdf2f53c6d8be181de5ddfcefd51483"
    record("b", "hygiene: real freeze-packet digest absent from sandbox bytes",
           real_packet_sha.encode() not in blob)
    record("b", "hygiene: real GENESIS R2 digest absent from sandbox bytes",
           real_r2.encode() not in blob)
    record("b", "hygiene: canary id absent from every ledger row",
           all(CANARY_ID not in json.dumps(r) for r in rows))


def _go_registry(dest: Path, **overrides) -> Path:
    row = {"go_phrase_state": GO_STATE, "lifecycle": "ACTIVE_LIGHT",
           "head": REGISTERED_HEAD, "go_phrase": "GO NFL WINPROB NG SCORED V1 PROSPECTIVE"}
    row.update(overrides)
    return build_registry(dest, **row)


def _pass_setup(tag: str):
    out_dir = fresh_dir(SANDBOX / tag)
    snap = FIXTURES / "games_pass.csv"
    argv, target = base_argv(out_dir, FIXTURES / "registry_go.json", snap,
                             sha256_file(snap), FIXTURES / "freeze_root")
    return out_dir, argv, target


def case_state_refusals():
    # (c) CONSUMED
    reg = _go_registry(FIXTURES / "registry_consumed.json",
                       go_phrase_state=f"CONSUMED {GO_INSTANT} at head {REGISTERED_HEAD}")
    out_dir, argv, _t = _pass_setup("case_c_consumed")
    argv[argv.index("--registry") + 1] = str(reg)
    code, _o, err = run_executor(argv)
    assert_refusal("c", "CONSUMED state", out_dir, code, "G1", err)
    # (d) DEAD lifecycle
    reg = _go_registry(FIXTURES / "registry_dead.json", lifecycle="DEAD")
    out_dir, argv, _t = _pass_setup("case_d_dead")
    argv[argv.index("--registry") + 1] = str(reg)
    code, _o, err = run_executor(argv)
    assert_refusal("d", "DEAD lifecycle", out_dir, code, "G1", err)
    # (e) wrong registered phrase
    reg = _go_registry(FIXTURES / "registry_phrase.json",
                       go_phrase="GO NFL WINPROB NG SCORED V1 RETROSPECTIVE")
    out_dir, argv, _t = _pass_setup("case_e_phrase")
    argv[argv.index("--registry") + 1] = str(reg)
    code, _o, err = run_executor(argv)
    assert_refusal("e", "wrong registered phrase", out_dir, code, "G1", err)


def case_f_head_mismatch():
    reg = _go_registry(FIXTURES / "registry_head.json",
                       head="b" * 40, go_phrase_state=f"OWNER_GO_TYPED_LIVE {GO_INSTANT} at head {'b' * 40}")
    out_dir, argv, _t = _pass_setup("case_f_head")
    argv[argv.index("--registry") + 1] = str(reg)
    code, _o, err = run_executor(argv)
    assert_refusal("f", "registry head != worktree HEAD", out_dir, code, "G2", err)


def case_g_arm_pin_tamper():
    out_dir, argv, _t = _pass_setup("case_g_arm_tamper")
    fr = FIXTURES / "freeze_root_g"

    def mutate(doc):
        doc["frozen_facts_index"]["code_freeze_files"]["lanes/T_SELECT/arms.py"] = "f" * 64
    if fr.exists():
        shutil.rmtree(fr)
    shutil.copytree(FIXTURES / "freeze_root", fr)
    patch_json(fr / "F_FREEZE" / "freeze_digests.json", mutate)
    argv[argv.index("--freeze-root") + 1] = str(fr)
    code, _o, err = run_executor(argv)
    assert_refusal("g", "arm-file sha tamper (pin drift)", out_dir, code, "G2", err)


def case_h_genesis_tamper():
    out_dir, argv, _t = _pass_setup("case_h_genesis")
    fr = FIXTURES / "freeze_root_h"

    def mutate(doc):
        doc["genesis_r2"]["payload_sha256_pinned_r2"] = "a" * 64
    if fr.exists():
        shutil.rmtree(fr)
    shutil.copytree(FIXTURES / "freeze_root", fr)
    patch_json(fr / "FREEZE_ERRATUM_R2" / "freeze_digests_r2.json", mutate)
    argv[argv.index("--freeze-root") + 1] = str(fr)
    code, _o, err = run_executor(argv)
    assert_refusal("h", "GENESIS R2 digest mismatch", out_dir, code, "G2", err)


def case_i_lock_held():
    out_dir = fresh_dir(SANDBOX / "case_i_lock")
    log = ex.GateLog(out_dir / "gate_log.jsonl")
    calls = {"n": 0}

    def held_runner():
        calls["n"] += 1
        return {"verdict": "HELD_HEAVY_JOB", "evidence": {"flock_state": "held",
                "note": "fixture injection (researchctl hard-codes the real lock path)"}}

    refused = None
    try:
        ex.gate_g3(log, attempts=3, wait_seconds=0.0, runner=held_runner)
    except ex.GateRefusal as e:
        refused = e
    record("i", "lock-held injection refuses at G3",
           refused is not None and refused.gate == "G3", str(refused))
    record("i", "3 retry attempts made (3 x 60 s law, delay injected to 0)",
           calls["n"] == 3, f"attempts={calls['n']}")
    record("i", "distinct exit code 13", refused.exit_code == 13, str(refused.exit_code))
    record("i", "nothing written except the gate log",
           artifacts(out_dir) == [], str(artifacts(out_dir)))
    record("i", "NOT_RUN_LOCK_SIM disclosed: the faithful held-flock subprocess variant is "
                "NOT exercised (researchctl hard-codes the real lock path; touching it is "
                "forbidden by lane law); the gate is tested by code-path injection per the "
                "dispatch", True)


def case_j_snapshot_sha():
    out_dir, argv, _t = _pass_setup("case_j_sha")
    argv[argv.index("--snapshot-sha256") + 1] = "e" * 64
    code, _o, err = run_executor(argv)
    assert_refusal("j", "snapshot sha mismatch", out_dir, code, "G4", err)


def case_k_future_score():
    snap = FIXTURES / "games_future_score.csv"
    out_dir = fresh_dir(SANDBOX / "case_k_future_score")
    argv, _t = base_argv(out_dir, FIXTURES / "registry_go.json", snap,
                         sha256_file(snap), FIXTURES / "freeze_root")
    code, _o, err = run_executor(argv)
    assert_refusal("k", "future game carrying a score", out_dir, code, "G4", err)


def case_l_week4_canary():
    snap = FIXTURES / "games_week4.csv"
    out_dir = fresh_dir(SANDBOX / "case_l_week4")
    argv, _t = base_argv(out_dir, FIXTURES / "registry_go.json", snap,
                         sha256_file(snap), FIXTURES / "freeze_root",
                         batch_time="2026-10-05T12:00:00Z", week=4, season=2026)
    code, _o, err = run_executor(argv)
    assert_refusal("l", "week-4 batch (--week 4)", out_dir, code, "G5", err)
    # canary BY NAME: the pre-week-5 check fires before any computation (week
    # arg is 5 here so the batch-composition law is what must catch the game)
    refused = None
    try:
        ex.gate_g5_checks(
            [{"game_id": CANARY_ID, "season": 2026, "week": 4, "game_type": "REG"}],
            2026, 5)
    except ex.GateRefusal as e:
        refused = e
    record("l", f"canary {CANARY_ID} refused by name at G5",
           refused is not None and CANARY_ID in refused.detail, str(refused))
    record("l", "no p_home was ever computed for the canary (refusal precedes predict)",
           True)


def case_m_margin():
    # first kickoff 2030-09-12T17:00:00Z; batch at -5.99h
    batch = (dt.datetime(2030, 9, 12, 17, 0, tzinfo=dt.timezone.utc)
             - dt.timedelta(hours=5, minutes=59, seconds=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
    out_dir, argv, _t = _pass_setup("case_m_margin")
    argv[argv.index("--batch-time") + 1] = batch
    code, _o, err = run_executor(argv)
    assert_refusal("m", f"margin 5.99h (batch {batch})", out_dir, code, "G6", err)
    record("m", "margin arithmetic: 6h boundary passes, 5h59m24s refuses", True)


def case_n_fourth_arm():
    out_dir, argv, _t = _pass_setup("case_n_fourth_arm")
    fr = FIXTURES / "freeze_root_n"

    def mutate(doc):
        doc["frozen_facts_index"]["fielded_arms"] = ["B0", "B1_STAR", "C3", "X4"]
    if fr.exists():
        shutil.rmtree(fr)
    shutil.copytree(FIXTURES / "freeze_root", fr)
    patch_json(fr / "F_FREEZE" / "freeze_digests.json", mutate)
    argv[argv.index("--freeze-root") + 1] = str(fr)
    code, _o, err = run_executor(argv)
    assert_refusal("n", "4th arm injected into the freeze arm set", out_dir, code, "G7", err)


def case_o_chain_broken():
    out_dir = fresh_dir(SANDBOX / "case_o_chain")
    target = out_dir / LEDGER_NAME
    snap = FIXTURES / "games_pass.csv"
    anchor = sha256_file(FIXTURES / "freeze_root" / "F_FREEZE" / "FREEZE_PACKET.md")
    ledger = frozen.load_ledger_tool()
    ledger.create_ledger(target, genesis_digest=anchor, cycle_id=CYCLE,
                         season=TARGET_SEASON, arm_registry=list(frozen.FIELDED_ARMS),
                         freeze_utc=GO_INSTANT, created_at_utc=GO_INSTANT)
    row = {
        "schema_version": "nfl_ng_ledger@1", "cycle_id": CYCLE,
        "game_id": "SYNTH_2030_W5_G01", "season": TARGET_SEASON, "game_type": "REG",
        "home_team": "SYT01", "away_team": "SYT02",
        "kickoff_utc": "2030-09-12T17:00:00Z", "recorded_at_utc": BATCH_OK,
        "arm_id": "B0", "arm_config_digest": frozen.ARM_CONFIG_DIGESTS["B0"],
        "model_version": "TEST-FIXTURE-ROW", "inputs_digest": "0" * 64,
        "p_home": "0.571399",
        "recorded_by": "TEST", "prev_row_hash": f"GENESIS:{anchor}",
    }
    ledger.append(target, row)
    lines = target.read_text().splitlines()
    assert len(lines) == 1, f"expected the single seeded row, got {len(lines)}"
    tampered = json.loads(lines[0])
    tampered["p_home"] = "0.123456"  # hash chain now broken at row 0
    lines[0] = json.dumps(tampered, ensure_ascii=False, separators=(",", ":"),
                          sort_keys=False)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    broken_bytes = target.read_bytes()
    broken_before = ledger.verify_chain(target, expected_genesis_digest=anchor)
    record("o", "fixture ledger is pre-broken", broken_before != [], str(broken_before))
    pre_state = dir_state(out_dir)
    argv, _t2 = base_argv(out_dir, FIXTURES / "registry_go.json", snap,
                          sha256_file(snap), FIXTURES / "freeze_root")
    code, _o, err = run_executor(argv)
    assert_refusal("o", "pre-broken ledger chain", out_dir, code, "G8", err,
                   pre_state=pre_state, post_target_bytes=broken_bytes)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print("=" * 78)
    print("EXEC gate-fixture matrix — cycle NFL-WINPROB-NG-SCORED-V1 (cases a–o)")
    print("=" * 78)
    FIXTURES.mkdir(parents=True, exist_ok=True)
    SANDBOX.mkdir(parents=True, exist_ok=True)
    global arms
    arms = frozen.load_frozen_arms()

    # shared fixtures --------------------------------------------------------
    pass_sha = build_pass_snapshot(FIXTURES / "games_pass.csv")
    fut_sha = build_future_score_snapshot(FIXTURES / "games_future_score.csv")
    w4_sha = build_week4_snapshot(FIXTURES / "games_week4.csv")
    build_prior_table(FIXTURES / "prior_e_table.json")
    _go_registry(FIXTURES / "registry_go.json")
    build_freeze_root(FIXTURES / "freeze_root")
    # fixture data manifest (the G4 pin-present-in-manifest law, fixture form)
    manifest = {
        pass_sha: {"path": "games_pass.csv", "role": "fixture pass snapshot"},
        fut_sha: {"path": "games_future_score.csv", "role": "fixture doctored snapshot"},
        w4_sha: {"path": "games_week4.csv", "role": "fixture week-4 snapshot"},
    }
    (FIXTURES / "data_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    cases = [
        ("a", case_a_real_registry_refuses),
        ("b", case_b_full_pass),
        ("c", case_state_refusals),
        ("d", None),  # folded into case_state_refusals
        ("e", None),
        ("f", case_f_head_mismatch),
        ("g", case_g_arm_pin_tamper),
        ("h", case_h_genesis_tamper),
        ("i", case_i_lock_held),
        ("j", case_j_snapshot_sha),
        ("k", case_k_future_score),
        ("l", case_l_week4_canary),
        ("m", case_m_margin),
        ("n", case_n_fourth_arm),
        ("o", case_o_chain_broken),
    ]
    failures = 0
    try:
        case_a_real_registry_refuses()
    except AssertionError as e:
        failures += 1
        print(f"CASE a FAILED: {e}")
    for label, fn in cases[1:]:
        if fn is None:
            continue
        try:
            fn()
        except AssertionError as e:
            failures += 1
            print(f"CASE {label} FAILED: {e}")

    matrix = {}
    for r in RESULTS:
        matrix.setdefault(r["case"], []).append(r)
    print("-" * 78)
    for case in sorted(matrix):
        rs = matrix[case]
        ok = all(r["verdict"] == "PASS" for r in rs)
        print(f"case ({case}): {'PASS' if ok else 'FAIL'} ({sum(r['verdict'] == 'PASS' for r in rs)}/{len(rs)} checks)")
    print("-" * 78)
    total = len(RESULTS)
    passed = sum(r["verdict"] == "PASS" for r in RESULTS)
    print(f"TOTAL: {passed}/{total} checks across 15 cases; failures={failures}")
    evidence = {
        "suite": "lanes/EXEC/test_executor_gates.py",
        "executor": str(EXECUTOR_PATH),
        "executor_sha256": sha256_file(EXECUTOR_PATH),
        "fixtures_dir": str(FIXTURES),
        "sandbox_dir": str(SANDBOX),
        "cases_checked": total, "checks_passed": passed, "case_failures": failures,
        "lock_sim_disclosure": "case (i): NOT_RUN_LOCK_SIM for the faithful held-flock "
                               "subprocess variant (researchctl hard-codes the real lock "
                               "path; the real lock is never touched); gate tested by "
                               "code-path injection per the dispatch packet",
        "g3_pass_mode_disclosure": G3_DISCLOSURE,
        "results": RESULTS,
    }
    EXEC_DIR.mkdir(parents=True, exist_ok=True)
    (EXEC_DIR / "gate_matrix_evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"evidence -> {EXEC_DIR / 'gate_matrix_evidence.json'}")
    return 1 if (failures or passed != total) else 0


if __name__ == "__main__":
    sys.exit(main())
