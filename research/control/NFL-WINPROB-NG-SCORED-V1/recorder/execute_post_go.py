"""execute_post_go.py — EXEC lane POST-OWNER-GO executor, cycle NFL-WINPROB-NG-SCORED-V1.

The auditable execution path that runs ONLY after an owner typed GO at this
cycle's own gate (P-8 two-key law). It reads authority FROM THE REGISTRY and
enforces the full gate chain G1–G8 in order (ERRATUM_R3 contract):

  G1 REGISTRY AUTHORITY  registry row: lifecycle ACTIVE_*, go_phrase_state
                         starts with the canonical live-GO token
                         `OWNER_GO_TYPED_LIVE` (full form
                         `OWNER_GO_TYPED_LIVE <utc-iso> at head <40-hex>`),
                         and the row's registered go_phrase equals
                         `GO NFL WINPROB NG SCORED V1 PROSPECTIVE`.
                         Any other state refuses. The executor NEVER reads
                         chat — only the registry.
  G2 FREEZE COHERENCE    worktree HEAD == registry row head == ERRATUM_R3
                         head-lineage pin; arm files sha256 == freeze pins;
                         recorder modules sha256 == ERRATUM_R2 pins; executor
                         own sha256 == ERRATUM_R3 pin; GENESIS payload digest
                         R2 (bd94eb77…) recomputes from the canonical form.
  G3 LOCK                `researchctl locks inspect` (run from the root cwd)
                         verdict == FREE_PROVEN; 3 attempts x 60 s, then refuse.
  G4 SNAPSHOT            sha256(snapshot) == provided pin AND the pin exists
                         in the cycle data manifest; future-with-score rows
                         abort; missing/unparseable kickoff UTC aborts.
  G5 WEEK                every batch game: expected season, game_type
                         REG/POST, week >= 5 (Option B law, ERRATUM_R2 §1);
                         canary refuses 2026_04_ATL_NO and every
                         pre-week-5 2026 game id by name.
  G6 MARGIN              batch_time + 6 h <= min(kickoff_utc of batch games).
  G7 ARMS                exactly the 3 frozen arms (B0, B1_STAR, C3) loaded
                         BY IMPORT from the sha-pinned frozen code; arm-config
                         digests == freeze values; no 4th arm; the diagnostic
                         twin is never fielded.
  G8 LEDGER              append via the ported nfl_ng_ledger@1 tool at
                         --ledger-target; GENESIS substitution law with the
                         placeholder-form digest asserted == bd94eb77…
                         BEFORE any write; chain validates after append; one
                         row per (game, arm) with recorded_at_utc <
                         kickoff_utc.

Every gate appends an audit line (gate, inputs, verdict) to the gate log
BEFORE evaluating (so a crash mid-gate is still auditable) and a verdict line
after. Refusals are LOUD with DISTINCT exit codes:
  G1=11 G2=12 G3=13 G4=14 G5=15 G6=16 G7=17 G8=18 (usage=2, ok=0).
On any refusal NOTHING is written except the gate log itself (the audit
evidence): no ledger file, no genesis sidecar, no registration payload.

Determinism: the executor contains NO wall-clock read. Every timestamp is an
explicit argument or the GO instant recorded in the registry state line, so
identical arguments produce byte-identical ledgers.

All lane runs of this executor used SYNTHETIC fixtures and sandbox targets
only; the REAL registry (REGISTERED_NOT_CONSUMED) refuses at G1 before any
data read (proven by an audit hook, lanes/EXEC/test_executor_gates.py case a).

Interpreter: /Users/hoangminhlong/my-quantitative/.venv/bin/python only.
No git write commands (read-only HEAD resolution via .git files, with a
read-only `git rev-parse HEAD` fallback).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import frozen_refs as frozen  # noqa: E402
import pipeline as rec_pipe  # noqa: E402
import priors as rec_priors  # noqa: E402
import schedule as rec_sched  # noqa: E402

# ---------------------------------------------------------------------------
# Constants (authority: FREEZE_PACKET.md §10, ERRATUM_R2 §1/§4, ERRATUM_R3)
# ---------------------------------------------------------------------------
CYCLE_ID = "NFL-WINPROB-NG-SCORED-V1"
REGISTERED_GO_PHRASE = "GO NFL WINPROB NG SCORED V1 PROSPECTIVE"
GO_TOKEN = "OWNER_GO_TYPED_LIVE"
GO_STATE_RE = re.compile(
    r"^OWNER_GO_TYPED_LIVE (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z) at head ([0-9a-f]{40})$"
)
ALLOWED_LIFECYCLE = frozenset({"ACTIVE_LIGHT", "ACTIVE_HEAVY"})
RECORDER_FREEZE_RE = re.compile(r"RECORDER_FREEZE_SHA\s*=\s*([0-9a-f]{40})")
PRE_WEEK5_2026_RE = re.compile(r"^2026_0[1-4]_")  # Option B: pre-week-5 2026 = NOT_RUN forever
CANARY_GAME_ID = "2026_04_ATL_NO"  # earliest future kickoff at registration; forfeit-by-design
ALLOWED_GAME_TYPES = frozenset({"REG", "POST"})
MIN_CAPTURABLE_WEEK = 5  # Option B (ERRATUM_R2 §1): week 5 onward ONLY

ROOT = Path("/Users/hoangminhlong/my-quantitative")  # root checkout (bootstrap/owner space)
WORKTREE = frozen.WORKTREE
DEFAULT_REGISTRY = ROOT / "plans" / "CYCLE_REGISTRY.json"
DEFAULT_RESEARCHCTL = ROOT / "research" / "researchctl.py"
INTERPRETER = Path("/Users/hoangminhlong/my-quantitative/.venv/bin/python")
FREEZE_ROOT_DEFAULT = WORKTREE / "lanes"
REAL_LEDGER_DIR = WORKTREE / "research" / "control" / CYCLE_ID / "ledger"
RECORDED_BY = "EXEC-POST-GO-EXECUTOR"

TS_FMT = rec_sched.TS_FMT

EXIT_OK = 0
EXIT_USAGE = 2
GATE_EXITS = {"G1": 11, "G2": 12, "G3": 13, "G4": 14, "G5": 15, "G6": 16, "G7": 17, "G8": 18}


class GateRefusal(RuntimeError):
    """A gate refused: loud, distinct exit code, nothing written (except the
    gate log — the audit evidence of the refusal itself)."""

    def __init__(self, gate: str, detail: str):
        super().__init__(f"{gate} REFUSE: {detail}")
        self.gate = gate
        self.exit_code = GATE_EXITS[gate]
        self.detail = detail


# ---------------------------------------------------------------------------
# Gate log (audit trail; the ONLY file written on refusal)
# ---------------------------------------------------------------------------

class GateLog:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = open(self.path, "a", encoding="utf-8")

    def entry(self, gate, name, inputs, verdict, detail=""):
        line = json.dumps(
            {"gate": gate, "name": name, "inputs": inputs, "verdict": verdict, "detail": detail},
            ensure_ascii=False, sort_keys=True, default=str,
        )
        self._fh.write(line + "\n")
        self._fh.flush()

    def begin(self, gate, name, inputs):
        self.entry(gate, name, inputs, "EVAL")

    def pass_(self, gate, name, inputs, detail=""):
        self.entry(gate, name, inputs, "PASS", detail)

    def close(self):
        try:
            self._fh.close()
        except Exception:
            pass


def _load_json_file(path: Path, gate: str, what: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except OSError as e:
        raise GateRefusal(gate, f"{what} unreadable: {path} ({e})")
    except json.JSONDecodeError as e:
        raise GateRefusal(gate, f"{what} is not valid JSON: {path} ({e})")


# ===========================================================================
# G1 — REGISTRY AUTHORITY
# ===========================================================================

def _registry_rows(data):
    if isinstance(data, dict) and "cycles" in data:
        data = data["cycles"]
    if isinstance(data, dict):
        return list(data.values())
    if isinstance(data, list):
        return data
    raise ValueError("registry JSON has no cycle rows (expected a list or a 'cycles' mapping)")


def gate_g1(registry_path: Path, log: GateLog) -> dict:
    """Authority gate. Reads ONLY the registry file; refuses unless the row
    records a live typed GO exactly per the ERRATUM_R3 convention."""
    log.begin("G1", "registry-authority", {"registry": str(registry_path), "cycle_id": CYCLE_ID})
    data = _load_json_file(registry_path, "G1", "cycle registry")
    try:
        rows = _registry_rows(data)
    except ValueError as e:
        raise GateRefusal("G1", str(e))
    row = None
    for r in rows:
        if isinstance(r, dict) and r.get("cycle_id") == CYCLE_ID:
            row = r
            break
    if row is None:
        raise GateRefusal("G1", f"no registry row with cycle_id {CYCLE_ID}")
    lifecycle = row.get("lifecycle")
    if lifecycle not in ALLOWED_LIFECYCLE:
        raise GateRefusal(
            "G1",
            f"registry lifecycle {lifecycle!r} not in {sorted(ALLOWED_LIFECYCLE)} — "
            "no live cycle authority",
        )
    state = row.get("go_phrase_state") or ""
    if not state.startswith(GO_TOKEN):
        raise GateRefusal(
            "G1",
            f"go_phrase_state {state!r} does not start with the canonical live-GO token "
            f"{GO_TOKEN!r} — no owner typed GO is recorded in the registry; refusing "
            "(the executor never reads chat, only the registry)",
        )
    m = GO_STATE_RE.match(state)
    if not m:
        raise GateRefusal(
            "G1",
            f"go_phrase_state {state!r} is not the canonical recorded form "
            f"'{GO_TOKEN} <utc-iso> at head <40-hex>' (ERRATUM_R3 GO-recording convention)",
        )
    go_utc, go_head = m.group(1), m.group(2)
    phrase = row.get("go_phrase")
    if phrase != REGISTERED_GO_PHRASE:
        raise GateRefusal(
            "G1",
            f"registered go_phrase {phrase!r} != {REGISTERED_GO_PHRASE!r} — phrase "
            "equality failed; refusing",
        )
    log.pass_("G1", "registry-authority",
              {"registry": str(registry_path), "cycle_id": CYCLE_ID},
              f"lifecycle={lifecycle} state={state!r}")
    return {"row": row, "go_utc": go_utc, "go_head": go_head}


# ===========================================================================
# G2 — FREEZE COHERENCE
# ===========================================================================

def read_worktree_head(worktree: Path = WORKTREE) -> str:
    """Resolve the worktree HEAD by reading .git files (no git subprocess).
    Fallback: read-only `git rev-parse HEAD`. Returns the 40-hex sha or ''."""
    dot_git = worktree / ".git"
    try:
        if dot_git.is_file():  # linked worktree: "gitdir: <path>"
            first = dot_git.read_text(encoding="utf-8").strip()
            if first.startswith("gitdir:"):
                gitdir = Path(first.split(":", 1)[1].strip())
                if not gitdir.is_absolute():
                    gitdir = (worktree / gitdir).resolve()
                return _head_from_gitdir(gitdir)
        elif dot_git.is_dir():  # plain checkout
            return _head_from_gitdir(dot_git)
    except OSError:
        pass
    # read-only fallback (allowed: no write commands)
    try:
        out = subprocess.run(
            ["git", "-C", str(worktree), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=30,
        )
        if out.returncode == 0:
            return out.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return ""


def _head_from_gitdir(gitdir: Path) -> str:
    head_file = gitdir / "HEAD"
    head = head_file.read_text(encoding="utf-8").strip()
    if not head.startswith("ref:"):
        return head  # detached HEAD: the sha itself
    ref = head.split(":", 1)[1].strip()
    loose = gitdir / ref
    if loose.is_file():
        return loose.read_text(encoding="utf-8").strip()
    # refs may live in the common dir (shared .git) or packed-refs
    commondir = gitdir
    cd_file = gitdir / "commondir"
    if cd_file.is_file():
        cd = cd_file.read_text(encoding="utf-8").strip()
        commondir = Path(cd) if Path(cd).is_absolute() else (gitdir / cd).resolve()
    loose = commondir / ref
    if loose.is_file():
        return loose.read_text(encoding="utf-8").strip()
    packed = commondir / "packed-refs"
    if packed.is_file():
        for line in packed.read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.startswith("#") and line.endswith(" " + ref):
                return line.split(" ", 1)[0].strip()
    return ""


def gate_g2(freeze_root: Path, registry_head: str, log: GateLog) -> dict:
    """Freeze-coherence gate: HEAD lineage + every frozen file pin + the
    GENESIS R2 payload digest recompute. No data is read (no snapshot)."""
    def _rp(*parts):
        return freeze_root.joinpath(*parts)

    paths = {
        "freeze_digests": _rp("F_FREEZE", "freeze_digests.json"),
        "freeze_packet": _rp("F_FREEZE", "FREEZE_PACKET.md"),
        "r2_digests": _rp("FREEZE_ERRATUM_R2", "freeze_digests_r2.json"),
        "r2_addendum": _rp("FREEZE_ERRATUM_R2", "CONTROLLER_ADDENDUM.md"),
        "r3_digests": _rp("FREEZE_ERRATUM_R3", "freeze_digests_r3.json"),
        "arms": frozen.FROZEN_ARMS_PATH,
        "select": WORKTREE / "lanes" / "T_SELECT" / "select.py",
        "boot": WORKTREE / "lanes" / "T_SELECT" / "boot.py",
        "ledger_tool": frozen.LEDGER_TOOL_PATH,
        "executor": Path(__file__).resolve(),
    }
    log.begin("G2", "freeze-coherence", {"freeze_root": str(freeze_root)})

    r1 = _load_json_file(paths["freeze_digests"], "G2", "freeze_digests.json")
    r2 = _load_json_file(paths["r2_digests"], "G2", "freeze_digests_r2.json")
    r3 = _load_json_file(paths["r3_digests"], "G2", "freeze_digests_r3.json")

    # -- HEAD lineage -------------------------------------------------------
    head = read_worktree_head(WORKTREE)
    r3_head_pin = (r3.get("head_lineage") or {}).get("expected_sha", "")
    if not (len(head) == 40 and head == registry_head == r3_head_pin):
        raise GateRefusal(
            "G2",
            f"head lineage incoherent: worktree HEAD {head!r} vs registry row head "
            f"{registry_head!r} vs ERRATUM_R3 pin {r3_head_pin!r}",
        )

    # -- frozen arm code files (FREEZE_PACKET §9) ---------------------------
    arm_pins = r1["frozen_facts_index"]["code_freeze_files"]
    arm_files = {"lanes/T_SELECT/arms.py": paths["arms"],
                 "lanes/T_SELECT/select.py": paths["select"],
                 "lanes/T_SELECT/boot.py": paths["boot"]}
    for rel, p in arm_files.items():
        got = frozen.sha256_file(p)
        pin = arm_pins.get(rel)
        if pin != got:
            raise GateRefusal("G2", f"arm file {rel} sha256 {got} != freeze pin {pin}")
    if frozen.FROZEN_ARMS_SHA256 != arm_pins["lanes/T_SELECT/arms.py"]:
        raise GateRefusal("G2", "frozen_refs arms pin disagrees with freeze_digests.json")

    # -- frozen imports (arms + ported ledger tool) -------------------------
    r2_imports = r2["recorder_freeze"]["frozen_imports"]
    got = frozen.sha256_file(paths["arms"])
    if got != r2_imports["lanes/T_SELECT/arms.py"]:
        raise GateRefusal("G2", f"arms.py sha256 {got} != R2 frozen-import pin")
    got = frozen.sha256_file(paths["ledger_tool"])
    if got != r2_imports["research/control/NFL-WINPROB-NG-SCORED-V1/ledger/nfl_ng_ledger.py"]:
        raise GateRefusal("G2", f"ledger tool sha256 {got} != R2 frozen-import pin")
    if frozen.LEDGER_TOOL_SHA256 != got:
        raise GateRefusal("G2", "frozen_refs ledger pin disagrees with freeze_digests_r2.json")

    # -- recorder modules (ERRATUM_R2 §3) — the executor is NOT one of them;
    #    it is an ERRATUM_R3 execution-surface addition (lawful per R2 precedent)
    rec_pins = r2["recorder_freeze"]["modules"]
    for name, pin in sorted(rec_pins.items()):
        got = frozen.sha256_file(_HERE / name)
        if got != pin:
            raise GateRefusal("G2", f"recorder module {name} sha256 {got} != R2 pin {pin}")

    # -- executor own pin (ERRATUM_R3) ---------------------------------------
    exec_pin = (r3.get("executor_freeze") or {}).get("modules", {}).get("execute_post_go.py", "")
    got = frozen.sha256_file(paths["executor"])
    if not exec_pin or got != exec_pin:
        raise GateRefusal("G2", f"executor sha256 {got} != ERRATUM_R3 pin {exec_pin!r}")

    # -- freeze packet bytes (GENESIS freeze_digest input) -------------------
    packet_sha = frozen.sha256_file(paths["freeze_packet"])
    if packet_sha != r1["freeze_packet"]["sha256"]:
        raise GateRefusal(
            "G2",
            f"FREEZE_PACKET.md sha256 {packet_sha} != freeze_digests.json pin "
            f"{r1['freeze_packet']['sha256']}",
        )

    # -- GENESIS payload digest R2 recomputes from the canonical form --------
    canonical = r2["genesis_r2"]["canonical_payload_v2"]
    r2_pin = r2["genesis_r2"]["payload_sha256_pinned_r2"]
    got = frozen.sha256_text(canonical)
    if got != r2_pin:
        raise GateRefusal(
            "G2",
            f"GENESIS payload digest {got} != R2 pinned {r2_pin}",
        )
    payload = json.loads(canonical)
    if payload.get("freeze_digest") != packet_sha:
        raise GateRefusal(
            "G2",
            "GENESIS payload freeze_digest does not equal the freeze-packet bytes sha256",
        )
    if payload.get("code_freeze_sha") != frozen.CODE_FREEZE_SHA:
        raise GateRefusal("G2", "GENESIS payload code_freeze_sha != CODE_FREEZE_ADDENDUM value")

    # -- controller-measured recorder freeze sha (substitution input) --------
    addendum = paths["r2_addendum"].read_text(encoding="utf-8")
    m = RECORDER_FREEZE_RE.search(addendum)
    if not m:
        raise GateRefusal(
            "G2", "CONTROLLER_ADDENDUM.md carries no 'RECORDER_FREEZE_SHA = <40-hex>' line"
        )
    log.pass_("G2", "freeze-coherence", {"freeze_root": str(freeze_root)},
              f"head={head} genesis_r2={r2_pin[:12]}… executor={got[:12]}…")
    return {
        "head": head,
        "freeze_packet_sha": packet_sha,
        "genesis_payload_digest_r2": r2_pin,
        "canonical_payload_v2": canonical,
        "recorder_freeze_sha": m.group(1),
        "r1": r1, "r2": r2, "r3": r3,
    }


# ===========================================================================
# G3 — LOCK
# ===========================================================================

def _default_lock_runner(researchctl_path: Path, cwd: Path) -> dict:
    out = subprocess.run(
        [str(INTERPRETER), str(researchctl_path), "locks", "inspect"],
        cwd=str(cwd), capture_output=True, text=True, timeout=300,
    )
    if out.returncode != 0:
        return {"verdict": "INSPECT_FAILED", "stderr": out.stderr[-400:]}
    try:
        return json.loads(out.stdout)
    except json.JSONDecodeError:
        return {"verdict": "INSPECT_UNPARSEABLE", "stdout": out.stdout[-400:]}


def gate_g3(log: GateLog, researchctl_path: Path = DEFAULT_RESEARCHCTL,
            cwd: Path = ROOT, attempts: int = 3, wait_seconds: float = 60.0,
            runner=None) -> dict:
    """Machine-wide heavy-lock gate: verdict must be FREE_PROVEN. Retry
    attempts x wait_seconds (frozen default 3 x 60 s), then refuse."""
    log.begin("G3", "heavy-lock", {
        "researchctl": str(researchctl_path), "cwd": str(cwd),
        "attempts": attempts, "wait_seconds": wait_seconds,
    })
    run = runner or (lambda: _default_lock_runner(researchctl_path, cwd))
    verdict = None
    for attempt in range(1, attempts + 1):
        obs = run()
        verdict = obs.get("verdict")
        if verdict == "FREE_PROVEN":
            log.pass_("G3", "heavy-lock",
                      {"researchctl": str(researchctl_path), "cwd": str(cwd),
                       "attempt": attempt},
                      f"verdict={verdict} flock_state={obs.get('evidence', {}).get('flock_state')}")
            return obs
        if attempt < attempts:
            time.sleep(wait_seconds)
    raise GateRefusal(
        "G3",
        f"heavy lock not FREE_PROVEN after {attempts} attempts (last verdict={verdict!r}); "
        "NOT_RUN_RESOURCE_CONFLICT",
    )


# ===========================================================================
# G4 — SNAPSHOT
# ===========================================================================

def gate_g4(log: GateLog, snapshot_path: Path, snapshot_sha: str, manifest: dict) -> rec_sched.Schedule:
    log.begin("G4", "snapshot-pin", {"snapshot": str(snapshot_path), "sha256": snapshot_sha})
    if not snapshot_path.is_file():
        raise GateRefusal("G4", f"snapshot file missing: {snapshot_path}")
    got = frozen.sha256_file(snapshot_path)
    if got != snapshot_sha:
        raise GateRefusal("G4", f"snapshot sha256 {got} != provided pin {snapshot_sha}")
    if snapshot_sha not in manifest:
        raise GateRefusal(
            "G4",
            f"snapshot pin {snapshot_sha} not present in the cycle data manifest "
            f"({len(manifest)} pinned entries)",
        )
    try:
        sched = rec_sched.load_snapshot(load_frozen_arms_cached(), snapshot_path, snapshot_sha)
    except rec_sched.SchedulePinError as e:
        raise GateRefusal("G4", str(e))
    except Exception as e:  # unparseable kickoff UTC etc. — loud, fail-closed
        raise GateRefusal("G4", f"snapshot load failed (missing/unparseable kickoff UTC?): {e}")
    log.pass_("G4", "snapshot-pin",
              {"snapshot": str(snapshot_path)},
              f"rows={sched.n_rows_total} seasons={sched.season_min}-{sched.season_max} "
              f"quarantined={len(sched.quarantined_columns)}")
    return sched


def gate_g4_future_score(log: GateLog, sched: rec_sched.Schedule, batch_time_utc: str) -> list:
    batch_ts = rec_sched.ns(batch_time_utc)
    bad = rec_sched.future_score_violations(sched, batch_ts)
    log.begin("G4", "future-score-abort", {"batch_time_utc": batch_time_utc})
    if bad:
        raise GateRefusal(
            "G4",
            f"ABORT: {len(bad)} future game(s) carry a score (corrupt/stale snapshot): {bad[:10]}",
        )
    log.pass_("G4", "future-score-abort", {"batch_time_utc": batch_time_utc}, "0 violations")
    return bad


# ===========================================================================
# G5 — WEEK (Option B law)
# ===========================================================================

def gate_g5_checks(batch_games, expected_season: int, expected_week: int) -> None:
    if expected_week < MIN_CAPTURABLE_WEEK:
        raise GateRefusal(
            "G5",
            f"--week {expected_week} < {MIN_CAPTURABLE_WEEK}: pre-week-5 weeks are NOT "
            "capturable (Option B, ERRATUM_R2 §1); refusing",
        )
    if not batch_games:
        raise GateRefusal("G5", "batch is empty — nothing capturable this week")
    for g in batch_games:
        gid = str(g["game_id"])
        if gid == CANARY_GAME_ID or PRE_WEEK5_2026_RE.match(gid):
            raise GateRefusal(
                "G5",
                f"game {gid} is a pre-week-5 2026 game — NOT_RUN prospective forever "
                f"(forfeit-by-design; canary {CANARY_GAME_ID}); no batch may ever record it",
            )
        if int(g["season"]) != expected_season:
            raise GateRefusal("G5", f"game {gid} season {g['season']} != expected {expected_season}")
        if str(g["game_type"]) not in ALLOWED_GAME_TYPES:
            raise GateRefusal(
                "G5", f"game {gid} game_type {g['game_type']!r} not in {sorted(ALLOWED_GAME_TYPES)}"
            )
        if int(g["week"]) < MIN_CAPTURABLE_WEEK:
            raise GateRefusal(
                "G5",
                f"game {gid} week {g['week']} < {MIN_CAPTURABLE_WEEK} — pre-week-5 games are "
                "NOT capturable (Option B law); refusing",
            )


def gate_g5(log: GateLog, batch_games, expected_season: int, expected_week: int) -> None:
    log.begin("G5", "week-law", {
        "expected_season": expected_season, "week": expected_week,
        "batch_games": [g["game_id"] for g in batch_games],
    })
    gate_g5_checks(batch_games, expected_season, expected_week)
    log.pass_("G5", "week-law",
              {"week": expected_week, "n_games": len(batch_games)},
              f"all {len(batch_games)} games week>={MIN_CAPTURABLE_WEEK}; canary {CANARY_GAME_ID} absent")


# ===========================================================================
# G6 — MARGIN
# ===========================================================================

def gate_g6(log: GateLog, batch_time_utc: str, batch_games) -> float:
    first_kick_ns = min(g["kickoff_ns"] for g in batch_games)
    first_kick_iso = rec_sched.iso_of_ns(first_kick_ns)
    log.begin("G6", "capture-margin", {"batch_time_utc": batch_time_utc,
                                       "first_kickoff_utc": first_kick_iso})
    try:
        margin_h = rec_pipe.check_margin(batch_time_utc, first_kick_iso, frozen.MARGIN_HOURS)
    except rec_pipe.MarginRefusal as e:
        raise GateRefusal("G6", str(e))
    log.pass_("G6", "capture-margin",
              {"batch_time_utc": batch_time_utc, "first_kickoff_utc": first_kick_iso},
              f"margin={margin_h:.4f}h >= {frozen.MARGIN_HOURS}h")
    return margin_h


# ===========================================================================
# G7 — ARMS
# ===========================================================================

_ARMS_CACHE = {}


def load_frozen_arms_cached():
    if "arms" not in _ARMS_CACHE:
        _ARMS_CACHE["arms"] = frozen.load_frozen_arms()  # sha-pinned import
    return _ARMS_CACHE["arms"]


def gate_g7(log: GateLog, r1: dict):
    log.begin("G7", "frozen-arms", {"expected": list(frozen.FIELDED_ARMS)})
    arms = load_frozen_arms_cached()  # import from frozen code; sha asserted inside
    digests = frozen.verify_arm_config_digests()  # recompute == frozen_refs pins
    pop = rec_pipe.init_arm_digests(frozen)  # pipeline ARM_DIGESTS for the append stage
    if pop != {k: v for k, v in digests.items() if k in frozen.FIELDED_ARMS}:
        raise GateRefusal("G7", "pipeline ARM_DIGESTS disagree with the recomputed freeze digests")
    freeze_digests = r1.get("arm_config_digests", {})
    for arm in frozen.ARM_CONFIG_DIGESTS:
        pin = freeze_digests.get(arm)
        if pin != digests[arm]:
            raise GateRefusal("G7", f"arm {arm} config digest {digests[arm]} != freeze pin {pin}")
    declared = list(r1.get("frozen_facts_index", {}).get("fielded_arms", []))
    if declared != list(frozen.FIELDED_ARMS):
        raise GateRefusal(
            "G7",
            f"freeze-declared fielded arms {declared} != the frozen arm triple "
            f"{list(frozen.FIELDED_ARMS)} — a 4th/renamed arm is injected; refusing",
        )
    if frozen.DIAGNOSTIC_ARM in declared:
        raise GateRefusal("G7", f"diagnostic arm {frozen.DIAGNOSTIC_ARM} must never be fielded")
    log.pass_("G7", "frozen-arms", {"expected": list(frozen.FIELDED_ARMS)},
              "3 arms by import; config digests == freeze values; no 4th arm")
    return arms, digests


# ===========================================================================
# G8 — LEDGER (GENESIS substitution law + append + chain validation)
# ===========================================================================

GENESIS_SCHEMA = "nfl_ng_scored_v1_genesis@1"
PLACEHOLDER_CREATED_AT = "POST_GO_TIMESTAMP"
PLACEHOLDER_RECORDER_SHA = "PENDING_CONTROLLER_ADDENDUM"
GENESIS_FIELD_ORDER = [
    "arm_set_ids", "code_freeze_sha", "created_at", "cycle_id",
    "diagnostic_arm_ids", "freeze_digest", "recorder_freeze_sha", "schema",
]


def build_genesis_payload_placeholder(freeze_packet_sha: str, code_freeze_sha: str) -> dict:
    return {
        "arm_set_ids": list(frozen.FIELDED_ARMS),
        "code_freeze_sha": code_freeze_sha,
        "created_at": PLACEHOLDER_CREATED_AT,
        "cycle_id": CYCLE_ID,
        "diagnostic_arm_ids": [frozen.DIAGNOSTIC_ARM],
        "freeze_digest": freeze_packet_sha,
        "recorder_freeze_sha": PLACEHOLDER_RECORDER_SHA,
        "schema": GENESIS_SCHEMA,
    }


def genesis_prewrite_assertions(log: GateLog, g2: dict, go_utc: str) -> dict:
    """GENESIS substitution law: (1) the rebuilt PLACEHOLDER-form payload must
    re-digest to the R2 pin (bd94eb77…) — asserted BEFORE any write; (2) the
    substituted payload differs from the pinned form in EXACTLY the two
    placeholder fields (created_at <- the GO timestamp recorded in the
    registry state line; recorder_freeze_sha <- the controller-measured
    integration HEAD per ERRATUM_R2 §3)."""
    log.begin("G8", "genesis-substitution", {"go_utc": go_utc})
    r2 = g2["r2"]
    rebuilt = build_genesis_payload_placeholder(g2["freeze_packet_sha"], frozen.CODE_FREEZE_SHA)
    rebuilt_canonical = frozen.canonical_json(rebuilt)
    rebuilt_digest = frozen.sha256_text(rebuilt_canonical)
    if rebuilt_canonical != r2["genesis_r2"]["canonical_payload_v2"]:
        raise GateRefusal(
            "G8",
            "rebuilt placeholder payload bytes != the R2 canonical form — freeze inputs drifted",
        )
    if rebuilt_digest != r2["genesis_r2"]["payload_sha256_pinned_r2"]:
        raise GateRefusal(
            "G8",
            f"placeholder payload digest {rebuilt_digest} != R2 pin "
            f"{r2['genesis_r2']['payload_sha256_pinned_r2']}",
        )
    substituted = dict(rebuilt)
    substituted["created_at"] = go_utc
    substituted["recorder_freeze_sha"] = g2["recorder_freeze_sha"]
    diff = sorted(k for k in rebuilt
                  if frozen.canonical_json(rebuilt[k]) != frozen.canonical_json(substituted[k]))
    expected_diff = sorted(r2["genesis_r2"]["placeholder_fields"])
    if diff != expected_diff:
        raise GateRefusal(
            "G8",
            f"substitution touched fields {diff} != the declared placeholders {expected_diff}",
        )
    log.pass_("G8", "genesis-substitution", {"go_utc": go_utc},
              f"placeholder digest == {rebuilt_digest[:12]}…; substitution fields == {diff}")
    return {"placeholder_digest": rebuilt_digest, "substituted_payload": substituted}


def gate_g8_prewrite(log: GateLog, ledger_target: Path, g2: dict, go_utc: str,
                     season: int, allow_control_tree: bool) -> dict:
    log.begin("G8", "ledger-prewrite", {"ledger_target": str(ledger_target), "season": season})
    resolved = ledger_target.resolve()
    if resolved.parent == REAL_LEDGER_DIR.resolve() and not allow_control_tree:
        raise GateRefusal(
            "G8",
            f"ledger target {resolved} is the REAL control-tree ledger path and "
            "--allow-control-tree-ledger was not passed; refusing (lane runs are sandbox-only)",
        )
    expected_name = f"predictions_{CYCLE_ID}_{season}.jsonl"
    if ledger_target.name != expected_name:
        raise GateRefusal(
            "G8", f"filename law: expected {expected_name!r}, got {ledger_target.name!r}"
        )
    genesis_anchor = g2["freeze_packet_sha"]  # sha256 of the freeze packet bytes (LEDGER_SCHEMA §1)
    exists = ledger_target.exists()
    if exists:
        ledger = frozen.load_ledger_tool()
        if ledger_target.stat().st_size:
            try:
                broken = ledger.verify_chain(ledger_target, expected_genesis_digest=genesis_anchor)
            except ledger.LedgerError as e:  # unreadable/tampered binding: fail closed
                raise GateRefusal(
                    "G8",
                    f"existing ledger is corrupt or its genesis binding contradicts the "
                    f"freeze anchor: {e}; refusing; nothing written",
                )
            if broken:
                raise GateRefusal(
                    "G8",
                    f"existing ledger chain is BROKEN at rows {broken[:5]} (total {len(broken)}); "
                    "refusing to append to a corrupt ledger; nothing written",
                )
    sub = genesis_prewrite_assertions(log, g2, go_utc)
    log.pass_("G8", "ledger-prewrite", {"ledger_target": str(ledger_target)},
              f"anchor={genesis_anchor[:12]}… exists={exists}")
    return {"genesis_anchor": genesis_anchor, "genesis": sub, "existed": exists}


# ===========================================================================
# RUN PHASE (only after G1–G8 pre-write all pass)
# ===========================================================================

def run_batch(args, log: GateLog, batch_games, g8: dict, go_utc: str, per_arm,
              inputs_digest: str) -> dict:
    ledger = frozen.load_ledger_tool()
    ledger_target = Path(args.ledger_target)
    if not g8["existed"]:
        ledger.create_ledger(
            ledger_target,
            genesis_digest=g8["genesis_anchor"],
            cycle_id=CYCLE_ID,
            season=args.season,
            arm_registry=list(frozen.FIELDED_ARMS),
            freeze_utc=args.freeze_utc or go_utc,
            created_at_utc=go_utc,  # deterministic: the GO instant, never a wall clock
        )
    model_version = f"EXEC+{frozen.CODE_FREEZE_SHA}+{rec_pipe.recorder_config_digest(frozen)}"
    batch_time_utc = args.batch_time
    appended = rec_pipe.append_batch_to_ledger(
        ledger, ledger_target, g8["genesis_anchor"], CYCLE_ID, args.season,
        args.freeze_utc or go_utc, batch_time_utc, batch_games, per_arm,
        inputs_digest, model_version, RECORDED_BY, created_at_utc=go_utc,
    )
    # registration GENESIS payload (audit artifact beside the ledger)
    reg_payload_path = ledger_target.with_name(ledger_target.name + ".registration_genesis.json")
    reg_payload_path.write_text(
        json.dumps({
            "schema": GENESIS_SCHEMA,
            "placeholder_digest_pinned": g8["genesis"]["placeholder_digest"],
            "substituted_payload": g8["genesis"]["substituted_payload"],
            "substituted_digest": frozen.sha256_text(
                frozen.canonical_json(g8["genesis"]["substituted_payload"])),
            "ledger_genesis_anchor": g8["genesis_anchor"],
            "law": "created_at <- GO instant from the registry state line; "
                   "recorder_freeze_sha <- controller-measured integration HEAD "
                   "(ERRATUM_R2 CONTROLLER_ADDENDUM); no other byte differs from the "
                   "pinned placeholder form (bd94eb77…)",
        }, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    # chain validation + per-row timestamp law
    broken = ledger.verify_chain(ledger_target, expected_genesis_digest=g8["genesis_anchor"])
    if broken:
        raise GateRefusal("G8", f"chain BROKEN after append at rows {broken[:5]}")
    rows = ledger.load_rows(ledger_target)
    for r in appended:
        if not (rec_sched.ns(r["recorded_at_utc"]) < rec_sched.ns(r["kickoff_utc"])):
            raise GateRefusal(
                "G8",
                f"row {r['game_id']}/{r['arm_id']} violates recorded_at_utc < kickoff_utc",
            )
    expected_rows = len(batch_games) * len(frozen.FIELDED_ARMS)
    if len(rows) != expected_rows or len(appended) != expected_rows:
        raise GateRefusal(
            "G8", f"row count {len(rows)} (appended {len(appended)}) != {expected_rows}"
        )
    chain_head_sha = rows[-1]["row_hash"] if rows else ""
    log.pass_("G8", "ledger-append",
              {"ledger_target": str(ledger_target)},
              f"rows={len(appended)} chain_intact chain_head={chain_head_sha[:12]}…")
    return {
        "rows": len(appended),
        "chain_head_sha": chain_head_sha,
        "registration_payload": str(reg_payload_path),
        "p_home_first_game": {a: per_arm[a][0] for a in sorted(per_arm)},
    }


# Argument remembered between gate G4 and the run phase (module-scoped since
# gate functions are pure and take explicit inputs; this is set once by run()).
g4_snapshot_sha = ""
del g4_snapshot_sha  # snapshot sha flows through explicit function inputs instead


# ===========================================================================
# CLI
# ===========================================================================

def parse_args(argv=None):
    ap = argparse.ArgumentParser(
        description="POST-OWNER-GO executor, cycle NFL-WINPROB-NG-SCORED-V1 (gates G1–G8)")
    ap.add_argument("--registry", default=str(DEFAULT_REGISTRY),
                    help="cycle registry JSON (default: the REAL plans/CYCLE_REGISTRY.json)")
    ap.add_argument("--freeze-root", default=str(FREEZE_ROOT_DEFAULT),
                    help="directory holding F_FREEZE/ and FREEZE_ERRATUM_R2/R3/ (default: lanes/)")
    ap.add_argument("--snapshot", required=True, help="games.csv schedule snapshot path")
    ap.add_argument("--snapshot-sha256", required=True, help="expected snapshot sha256 pin")
    ap.add_argument("--data-manifest", default=None,
                    help="JSON mapping pinned sha256 -> descriptor (default: built from "
                         "freeze_digests.json data_frozen_inputs)")
    ap.add_argument("--ledger-target", required=True,
                    help="prediction ledger path (predictions_<cycle>_<season>.jsonl; "
                         "SANDBOX in all lane runs)")
    ap.add_argument("--allow-control-tree-ledger", action="store_true",
                    help="explicitly allow the REAL control-tree ledger path (post-GO "
                         "controller use only; never set in lane runs)")
    ap.add_argument("--season", type=int, default=2026, help="target season (default 2026)")
    ap.add_argument("--week", type=int, required=True, help="target week (must be >= 5)")
    ap.add_argument("--batch-time", default=None,
                    help="batch write time UTC ISO (YYYY-MM-DDTHH:MM:SSZ); default: refuse "
                         "(time must be explicit for auditability)")
    ap.add_argument("--freeze-utc", default=None,
                    help="ledger scoring freeze timestamp; default = the GO instant")
    ap.add_argument("--prior-e-table", default=None,
                    help="synthetic prior E table JSON (fixture mode); omit on the real path")
    ap.add_argument("--gate-log", default=None,
                    help="gate audit log path (default: <ledger-target>.gate_log.jsonl)")
    ap.add_argument("--lock-attempts", type=int, default=3)
    ap.add_argument("--lock-wait-seconds", type=float, default=60.0)
    ap.add_argument("--researchctl", default=str(DEFAULT_RESEARCHCTL))
    ap.add_argument("--researchctl-cwd", default=str(ROOT))
    return ap.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    if not args.batch_time:
        print("EXECUTOR REFUSAL: --batch-time is required (explicit, auditable; no "
              "implicit wall clock)", file=sys.stderr)
        return EXIT_USAGE
    try:
        rec_sched.ns(args.batch_time)
    except Exception:
        print(f"EXECUTOR REFUSAL: --batch-time {args.batch_time!r} is not "
              f"{TS_FMT}", file=sys.stderr)
        return EXIT_USAGE
    registry_path = Path(args.registry)
    freeze_root = Path(args.freeze_root)
    gate_log_path = Path(args.gate_log) if args.gate_log else Path(
        args.ledger_target + ".gate_log.jsonl")
    if gate_log_path.exists():
        gate_log_path.unlink()  # fresh audit log per run (deterministic bytes)
    log = GateLog(gate_log_path)
    try:
        # ---- gate chain, in order; each refusal raises GateRefusal ---------
        g1 = gate_g1(registry_path, log)
        g2 = gate_g2(freeze_root, g1["row"].get("head", ""), log)
        gate_g3(log, Path(args.researchctl), Path(args.researchctl_cwd),
                args.lock_attempts, args.lock_wait_seconds)
        sched = gate_g4(log, Path(args.snapshot), args.snapshot_sha256, _load_manifest(args, g2))
        gate_g4_future_score(log, sched, args.batch_time)
        batch_ts = rec_sched.ns(args.batch_time)
        batch_games, _already = rec_pipe.select_target_games(
            sched, batch_ts, args.season, args.week)
        gate_g5(log, batch_games, args.season, args.week)
        gate_g6(log, args.batch_time, batch_games)
        arms, _digests = gate_g7(log, g2["r1"])
        g8 = gate_g8_prewrite(log, Path(args.ledger_target), g2, g1["go_utc"],
                              args.season, args.allow_control_tree_ledger)
        # ---- warmup (state-carry law) -> batch predict ---------------------
        warm_rows, _fut_idx, _counts = rec_sched.split_rows(sched, batch_ts)
        if args.prior_e_table:
            prior_sha = frozen.sha256_file(args.prior_e_table)
            prior_e = rec_priors.load_prior_e_table(args.prior_e_table)
            z_table, _pt = rec_priors.synthesize_z_table(arms, prior_e)
            inputs_digest = frozen.sha256_text(frozen.canonical_json({
                "mode": "execute_post_go",
                "prior_e_table": prior_sha,
                "schedule_snapshot": args.snapshot_sha256,
            }))
        else:  # real path: pinned pbp state-carry inputs (verified, then digested)
            pbp_pins = rec_priors.verify_pbp_pins(frozen, frozen.PBP_DIRS_REAL)
            z_table, _pt = rec_priors.build_z_table_real(arms, frozen.PBP_DIRS_REAL)
            inputs_digest = rec_pipe.inputs_digest_real(args.snapshot_sha256, pbp_pins)
        per_arm, _handles = rec_pipe.predict_target_week(arms, warm_rows, batch_games, z_table)
        if sorted(per_arm) != sorted(frozen.FIELDED_ARMS):
            raise GateRefusal(
                "G7",
                f"predict produced arms {sorted(per_arm)} != exactly the 3 fielded arms",
            )
        # ---- ledger append + validation ------------------------------------
        result = run_batch(args, log, batch_games, g8, g1["go_utc"], per_arm, inputs_digest)
        report = {
            "executor": "execute_post_go.py",
            "cycle_id": CYCLE_ID,
            "gates": "G1..G8 ALL PASS",
            "go_utc": g1["go_utc"],
            "head": g2["head"],
            "week": args.week,
            "season": args.season,
            "batch_time_utc": args.batch_time,
            "batch_games": [g["game_id"] for g in batch_games],
            "ledger_target": str(args.ledger_target),
            "gate_log": str(gate_log_path),
            **result,
        }
        print("EXECUTOR OK")
        print(json.dumps(report, indent=2, sort_keys=True))
        return EXIT_OK
    except GateRefusal as e:
        log.entry(e.gate, "refusal", {"gate": e.gate}, "REFUSE", e.detail)
        print(f"EXECUTOR REFUSAL gate={e.gate} exit={e.exit_code}: {e.detail}", file=sys.stderr)
        return e.exit_code
    finally:
        log.close()


def _load_manifest(args, g2) -> dict:
    if args.data_manifest:
        data = _load_json_file(Path(args.data_manifest), "G4", "data manifest")
        if not isinstance(data, dict):
            raise GateRefusal("G4", "data manifest JSON must be an object mapping sha256 -> entry")
        return data
    manifest = {}
    for p, entry in (g2["r1"].get("files", {}).get("data_frozen_inputs") or {}).items():
        if isinstance(entry, dict) and isinstance(entry.get("sha256"), str):
            manifest[entry["sha256"]] = {"path": p, **entry}
    return manifest


if __name__ == "__main__":
    sys.exit(main())
