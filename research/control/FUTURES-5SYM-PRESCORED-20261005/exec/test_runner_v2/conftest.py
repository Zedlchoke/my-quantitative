"""Shared sandbox builder + real-authority snapshot guard for the
scored_runner_v2 production-path suite.

ISOLATION LAW (T16): a session-scoped autouse fixture sha/size/mtimes
snapshots the REAL authority surfaces before the suite and asserts them
unchanged after ALL tests:
  - the real governance dir /Users/hoangminhlong/.my-quantitative-governance
    (content hashes, except heavy_runtime/* whose rows legitimately mutate
    under the canonical machine-wide lock lifecycle owned by OTHER cycles —
    for those only the file listing + sizes are compared; this suite never
    touches that runtime: every runner invocation points --governance-dir
    inside its own tmp_path);
  - the real root registry plans/CYCLE_REGISTRY.json (content sha);
  - the real GO_RECORDED.json of the ES cycle (content sha, or ABSENT).
Every runner invocation in this suite runs as a REAL subprocess (the
production CLI path) against synthetic fixtures in an isolated tmp sandbox.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

EXEC_DIR = Path(__file__).resolve().parents[1]
RUNNER = str(EXEC_DIR / "scored_runner_v2.py")
CONTRACTS = str(EXEC_DIR / "symbol_contracts.json")
PY = sys.executable

CYCLE = "FUTURES-5SYM-PRESCORED-20261005"
SYMBOLS = ["NQ", "6E", "6B", "6J", "6A"]
BASE_PRICE = {"NQ": 21000.0, "ES": 6000.0, "6E": 1.085, "6B": 1.27,
              "6J": 0.0067, "6A": 0.655}

REAL_GOV = "/Users/hoangminhlong/.my-quantitative-governance"
REAL_REG = "/Users/hoangminhlong/my-quantitative/plans/CYCLE_REGISTRY.json"
REAL_ES_GO = ("/Users/hoangminhlong/my-quantitative/.worktrees/"
              "futures-es-reg/prep/research/control/FUTURES-ES-PB1-V1/auth/"
              "GO_RECORDED.json")


def sha256_path(p) -> str | None:
    p = Path(p)
    if not p.is_file():
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write_json(path, obj) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(
        json.dumps(obj, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8")


def gen_bars(symbol: str, n: int = 30, start: str = "2026-01-05") -> list:
    """Deterministic on-grid OHLCV bars: close_i == open_{i+1} so up/down
    signals are exact comparisons; every price is an integer multiple of the
    era-1 tick (and of 6A's finer era-2 tick)."""
    contracts = json.loads(Path(CONTRACTS).read_text(encoding="utf-8"))
    tick = float(contracts["contracts"][symbol]["era_table"][0]["tick_size"])
    base = BASE_PRICE[symbol]
    d0 = date.fromisoformat(start)
    ks = [((i * 7) % 5) - 1 for i in range(n + 1)]
    prices = [round(base + k * tick * 4.0, 10) for k in ks]
    rows = []
    for i in range(n):
        o, c = prices[i], prices[i + 1]
        rows.append({"ts": (d0 + timedelta(days=i)).isoformat(),
                     "open": o, "close": c,
                     "high": round(max(o, c) + tick, 10),
                     "low": round(min(o, c) - tick, 10)})
    return rows


def default_spec(cycle: str = CYCLE, symbols=None) -> dict:
    """2 identities x 2 folds per symbol: a long arm (tier t1, stress 1.0)
    and a short arm (tier t2, stress 1.5) — the arms are DECLARED here; the
    ACCOUNTING path is what the runner implements and the suite proves."""
    symbols = symbols if symbols is not None else SYMBOLS
    identities = []
    for sym in symbols:
        identities.append({"identity_id": f"{sym}-L1", "symbol": sym,
                           "arm": "long-if-bar-up", "hold_bars": 1,
                           "cost_tier": "t1", "stress": 1.0})
        identities.append({"identity_id": f"{sym}-S1", "symbol": sym,
                           "arm": "short-if-bar-down", "hold_bars": 1,
                           "cost_tier": "t2", "stress": 1.5})
    return {"schema": "futures_5sym_prescored/spec_packet@1",
            "cycle_id": cycle,
            "folds": [{"fold_id": "F1", "start_bar": 0, "end_bar": 15},
                      {"fold_id": "F2", "start_bar": 15, "end_bar": 30}],
            "identities": identities}


def default_cost_manifest() -> dict:
    return {"schema": "futures_5sym_prescored/cost_manifest@1",
            "fee_per_side_usd_by_tier": {"t1": 2.5, "t2": 4.0},
            "spread_ticks_by_stress": {"1.0": 1.0, "1.5": 1.5, "2.0": 2.0},
            "slip_ticks_by_stress": {"1.0": 0.5, "1.5": 1.0, "2.0": 1.5}}


class Sandbox:
    """A fully synthetic authority + input + output sandbox under one tmp
    directory. The runner is invoked as the REAL CLI subprocess."""

    def __init__(self, root: Path, cycle: str = CYCLE):
        self.root = Path(root)
        self.cycle = cycle
        self.gov = self.root / "gov"
        self.inputs = self.root / "inputs"
        self.out = self.root / "out"
        self.go = self.root / "auth" / "GO_RECORDED.json"
        self.auth = self.gov / "authority" / "authority_pack.json"
        self.registry = self.gov / "CYCLE_REGISTRY.json"
        self.manifest = self.inputs / "input_manifest.json"
        self.spec = self.inputs / "spec_packet.json"
        self.cost = self.inputs / "cost_manifest.json"
        self.ledger = self.out / "ledger" / "trial_ledger.jsonl"

    # ---- construction -----------------------------------------------------
    def build(self, symbols=None, n_bars=30, start="2026-01-05",
              spec=None, go_present=True, go_verbatim=None, go_cycle=None,
              go_typed_by="OWNER", go_typed_by_owner=True,
              registry_present=True, registry_cycles=None,
              authority_present=True, cost_manifest=None, extra_spec=None):
        symbols = symbols if symbols is not None else SYMBOLS
        self.gov.mkdir(parents=True, exist_ok=True)
        self.inputs.mkdir(parents=True, exist_ok=True)
        self.out.mkdir(parents=True, exist_ok=True)

        if registry_present:
            write_json(self.registry, {
                "schema": "governance/cycle_registry@1",
                "sandbox_note": "SYNTHETIC-SANDBOX registry copy; never a "
                                "real registration",
                "cycles": registry_cycles if registry_cycles is not None
                else [{"cycle_id": self.cycle,
                       "registered_by": "synthetic sandbox fixture"}]})
        if authority_present:
            write_json(self.auth, {
                "schema": "futures_5sym_prescored/authority_pack@1",
                "cycle_id": self.cycle, "typed_by_owner": True})
        if go_present:
            write_json(self.go, {
                "schema": "futures_5sym_prescored/go_recorded@1",
                "cycle_id": go_cycle or self.cycle,
                "key_owner_go": {
                    "verbatim": go_verbatim or
                    f"GO {go_cycle or self.cycle} SCORED EXECUTION",
                    "typed_by_owner": go_typed_by_owner,
                    "typed_by": go_typed_by}})

        fixtures = []
        for sym in symbols:
            rows = gen_bars(sym, n=n_bars, start=start)
            fpath = self.inputs / "fixtures" / f"{sym}.csv"
            fpath.parent.mkdir(parents=True, exist_ok=True)
            fpath.write_text(
                "ts,open,high,low,close\n" + "\n".join(
                    f"{r['ts']},{r['open']},{r['high']},{r['low']},"
                    f"{r['close']}" for r in rows) + "\n", encoding="utf-8")
            fixtures.append({"symbol": sym, "path": str(fpath),
                             "sha256": sha256_path(fpath),
                             "bars_expected": n_bars})

        write_json(self.spec, spec if spec is not None
                   else default_spec(self.cycle, symbols))
        if extra_spec is not None:
            s = json.loads(self.spec.read_text(encoding="utf-8"))
            s.update(extra_spec)
            write_json(self.spec, s)
        write_json(self.cost, cost_manifest or default_cost_manifest())

        write_json(self.manifest, {
            "schema": "futures_5sym_prescored/input_manifest@1",
            "cycle_id": self.cycle,
            "fixtures": fixtures,
            "spec_packet_sha256": sha256_path(self.spec),
            "cost_manifest_sha256": sha256_path(self.cost),
            "symbol_contracts_sha256": sha256_path(CONTRACTS),
            "prior_artifacts": []})
        return self

    # ---- invocation ---------------------------------------------------
    def run(self, extra=None, label="run1"):
        argv = [PY, RUNNER,
                "--cycle-id", self.cycle,
                "--governance-dir", str(self.gov),
                "--go-artifact", str(self.go),
                "--authority-file", str(self.auth),
                "--input-manifest", str(self.manifest),
                "--spec-packet", str(self.spec),
                "--cost-manifest", str(self.cost),
                "--symbol-contracts", CONTRACTS,
                "--ledger", str(self.ledger),
                "--run-dir", str(self.out / "runs" / label),
                "--final-status-out",
                str(self.out / f"FINAL_STATUS.{label}.json"),
                "--run-label", label] + (list(extra) if extra else [])
        return subprocess.run(argv, capture_output=True, text=True,
                              timeout=240)

    def final(self, label="run1") -> dict:
        return json.loads(
            (self.out / f"FINAL_STATUS.{label}.json").read_text(
                encoding="utf-8"))

    def out_file(self, name, label="run1") -> Path:
        return self.out / "runs" / label / name

    def ledger_rows(self) -> list:
        if not self.ledger.is_file():
            return []
        return [json.loads(l) for l in
                self.ledger.read_text(encoding="utf-8").splitlines()
                if l.strip()]

    # ---- lock state ---------------------------------------------------
    @property
    def lock_dir(self) -> Path:
        return self.gov / "lock_runtime"

    @property
    def lock_file(self) -> Path:
        return self.lock_dir / "heavy.lock"

    @property
    def lock_registry(self) -> Path:
        return self.lock_dir / "heavy_registry.json"

    def lock_rows(self) -> list:
        if not self.lock_registry.is_file():
            return []
        return json.loads(self.lock_registry.read_text(
            encoding="utf-8")).get("rows", [])

    def flock_held(self) -> bool:
        if not self.lock_file.is_file():
            return False
        fd = os.open(self.lock_file, os.O_RDWR)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(fd, fcntl.LOCK_UN)
            return False
        except OSError:
            return True
        finally:
            os.close(fd)


@pytest.fixture
def sb(tmp_path):
    """A fully-built valid sandbox (the T1 happy-path state)."""
    return Sandbox(tmp_path).build()


# ---- T16 session guard: the REAL authority surfaces are never touched ----

def _real_snapshot() -> dict:
    snap = {}
    if os.path.isdir(REAL_GOV):
        for root, _dirs, files in os.walk(REAL_GOV):
            for f in files:
                p = os.path.join(root, f)
                rel = os.path.relpath(p, REAL_GOV)
                if rel.startswith("heavy_runtime"):
                    # canonical machine-wide lock runtime: its rows belong to
                    # OTHER cycles' lock lifecycles and can change for reasons
                    # entirely outside this suite; this suite never points a
                    # lock there (every --lock dir is a sandbox tmp dir), so
                    # heavy_runtime is DISCLOSED-EXCLUDED from the claim.
                    continue
                st = os.stat(p)
                snap[rel] = (hashlib.sha256(
                    Path(p).read_bytes()).hexdigest(), st.st_size,
                    st.st_mtime_ns)
    else:
        snap["<governance-dir-absent>"] = True
    for key, p in (("plans/CYCLE_REGISTRY.json", REAL_REG),
                   ("es/auth/GO_RECORDED.json", REAL_ES_GO)):
        snap[key] = sha256_path(p) or "ABSENT"
    return snap


@pytest.fixture(scope="session", autouse=True)
def real_authority_untouched():
    before = _real_snapshot()
    yield
    after = _real_snapshot()
    changed = {k: (before.get(k), after.get(k))
               for k in set(before) | set(after)
               if before.get(k) != after.get(k)}
    assert not changed, (
        "T16 VIOLATION: real authority/state surfaces changed during the "
        f"suite: {changed}")
