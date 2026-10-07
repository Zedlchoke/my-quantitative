"""SPORTS-PAPERTRADE-EXEC-V1 production paper-trade runner package.

One wallet, three leagues (NBA / WNBA-2026-remainder / SOCCER), one owner GO:
``GO SPORTS PAPERTRADE EXEC V1 RUN ALL`` (REGISTERED_NOT_CONSUMED — typed by the
owner alone, never by code). Pre-GO every mutating subcommand refuses with
BLOCKED_NO_GO; read-only `plan` / `verify-pins` / `dashboard` work.

Everything imported from sibling cycles is READ-ONLY and byte-pinned
(pins.json); mismatch is BLOCKED_PIN_DRIFT, fail-closed. Sandbox bytes live
under ~/.my-quantitative-data/sports-papertrade-exec-v1/ (or a test tmp dir);
zero real paper rows and zero real probabilities exist pre-GO by construction.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

CYCLE_ID = "SPORTS-PAPERTRADE-EXEC-V1"
GO_PHRASE = "GO SPORTS PAPERTRADE EXEC V1 RUN ALL"
CONTROL_DIR_NAME = "SPORTS-PAPERTRADE-EXEC-V1"
DEFAULT_DATA_ROOT = Path.home() / ".my-quantitative-data" / "sports-papertrade-exec-v1"

WORKTREE_ROOT = Path(__file__).resolve().parents[2]
CONTROL_DIR = WORKTREE_ROOT / "research" / "control" / CONTROL_DIR_NAME
REGISTRY_PATH = WORKTREE_ROOT / "plans" / "CYCLE_REGISTRY.json"
LEAGUES = ("NBA", "WNBA", "SOCCER")

# Anchor laws (plan §1.4): NBA/WNBA tip-relative T0-6h10m (batch = the run-day's
# fixtures of that league; T0 = earliest tip in the batch, exclusive deadline —
# a forecast stamped exactly at the anchor is refused). SOCCER: kickoff-6h
# strict per match.
BATCH_LEAD_SECONDS = 6 * 3600 + 600          # 6h10m
SOCCER_LEAD_SECONDS = 6 * 3600               # 6h strict

PINS_PATH = Path(__file__).resolve().parent / "pins.json"

# Exit codes (stable, journaled in run reports).
EXIT_OK = 0
EXIT_BLOCKED_NO_GO = 3
EXIT_BLOCKED_KEY = 4
EXIT_BLOCKED_ANCHOR = 5
EXIT_HEAD_DRIFT = 6
EXIT_PIN_DRIFT = 7
EXIT_BLOCKED_TAMPER = 8
EXIT_BLOCKED_OTHER = 9


class BlockError(RuntimeError):
    """Hard refusal — the command writes nothing and exits with `exit_code`."""

    def __init__(self, code: str, detail: str, exit_code: int = EXIT_BLOCKED_OTHER):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.exit_code = exit_code


def load_pins() -> dict:
    return json.loads(PINS_PATH.read_text())


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def resolve_path(pinned: dict, root_override: Path | None, default_base: Path) -> Path:
    raw = pinned.get("path") or ""
    p = Path(raw).expanduser()
    if root_override is not None and not p.is_absolute():
        return Path(root_override) / p.name
    if not p.is_absolute() and default_base is not None:
        return default_base / p
    return p


def verify_pins(*, roots: dict | None = None, only_required: bool = True,
                include_optional: list[str] | None = None) -> dict:
    """Byte-level pin verification. Raises BlockError(BLOCKED_PIN_DRIFT) on any
    required-file (or requested optional-file) sha mismatch. Missing optional
    entry files (Lane B/C concurrency) are reported, not fatal."""
    pins = load_pins()
    roots = roots or {}
    report = {"files": {}, "data": {}, "drift": [], "missing_optional": []}
    for pkg_name, pkg in pins["packages"].items():
        base = pkg.get("pkg_dir", "")
        root = roots.get(f"{pkg_name}_root")
        for fname, pin in pkg["files"].items():
            alias = f"{pkg_name}/{fname}"
            want = pin.get("sha256")
            path = _pkg_file_path(pkg, fname, root)
            if want is None:
                # optional entry point whose bytes are not yet frozen (Lane B/C)
                if path is not None and path.exists():
                    report["files"][alias] = {
                        "status": "PRESENT_UNPINNED_OPTIONAL",
                        "sha256": sha256_file(path), "path": str(path)}
                else:
                    report["files"][alias] = {"status": "ABSENT_OPTIONAL",
                                              "path": str(path) if path else None}
                    report["missing_optional"].append(alias)
                continue
            if path is None or not path.exists():
                if pin.get("required") or (include_optional and alias in include_optional):
                    report["drift"].append({"alias": alias, "why": "required file missing",
                                            "path": str(path)})
                else:
                    report["files"][alias] = {"status": "ABSENT_OPTIONAL"}
                    report["missing_optional"].append(alias)
                continue
            got = sha256_file(path)
            ok = (got == want)
            report["files"][alias] = {"status": "OK" if ok else "DRIFT",
                                      "sha256": got, "path": str(path)}
            if not ok and (pin.get("required") or
                           (include_optional and alias in include_optional)):
                report["drift"].append({"alias": alias, "why": "sha256 mismatch",
                                        "expected": want, "observed": got})
    for dname, dpin in pins.get("data", {}).items():
        path = Path(dpin["path"]).expanduser()
        if not path.exists():
            if dpin.get("required"):
                report["drift"].append({"alias": f"data/{dname}",
                                        "why": "required data snapshot missing",
                                        "path": str(path)})
            else:
                report["data"][dname] = {"status": "ABSENT_OPTIONAL", "path": str(path)}
            continue
        if dname == "nba_espn_schedule_2026_27":
            from .adapters import nba_payload_verdict   # lazy (circular-safe)
            verdict = nba_payload_verdict(path, dpin["composite_sha256"])
            ok = bool(verdict["ok"])
            got = verdict["effective_composite"]
            report["data"][dname] = {"status": "OK" if ok else "DRIFT",
                                     "sha256": got, "path": str(path)}
            if not ok:
                report["data"][dname]["why"] = verdict["why"]
        else:
            got = sha256_file(path)
            ok = (got == dpin["sha256"])
            report["data"][dname] = {"status": "OK" if ok else "DRIFT", "sha256": got,
                                     "path": str(path)}
        if not ok and dpin.get("required"):
            report["drift"].append({"alias": f"data/{dname}", "why": "sha256 mismatch",
                                    "expected": dpin.get("sha256") or dpin.get("composite_sha256"),
                                    "observed": got})
    if report["drift"]:
        raise BlockError("BLOCKED_PIN_DRIFT",
                         "pinned source drift: " + json.dumps(report["drift"]),
                         EXIT_PIN_DRIFT)
    return report


def nba_payload_composite(payloads_dir: Path) -> str:
    """Composite pin recipe from NBA-WINPROB-PROSPECTIVE-PREP-V1
    DATA_REFRESH_MANIFEST.md: sha256 of the newline-joined per-file sha256 list
    of the scoreboard_*.json payloads, lexicographic by filename."""
    shas = [sha256_file(f) for f in sorted(Path(payloads_dir).glob("scoreboard_*.json"))]
    return hashlib.sha256("\n".join(shas).encode()).hexdigest()


def _pkg_file_path(pkg: dict, fname: str, root_override: Path | None) -> Path | None:
    """Absolute path of one package file, honoring a sandbox root override
    (tests point e.g. paper_core_root at a pristine copy)."""
    worktree = pkg.get("worktree")
    pkg_dir = pkg.get("pkg_dir")
    if root_override is not None:
        base = Path(root_override)
        # override roots point AT the package dir itself (copied tree)
        if (base / fname).exists() or not (base / pkg_dir.split("/")[0]).exists():
            return base / fname
        return base / pkg_dir / fname
    if worktree and pkg_dir:
        return Path(worktree) / pkg_dir / fname
    return None


def load_pinned_package(alias: str, pkg_key: str, *, roots: dict | None = None,
                        include_optional: list[str] | None = None):
    """Verify pins, then import a sibling worktree package under a private
    top-level module name (avoids clashing with this repo's own `research`
    package). Returns the imported package module with its pinned submodules
    imported (core.ledger / core.risk / ... reachable as attributes).
    Relative imports inside the package keep working."""
    verify_pins(roots=roots, include_optional=include_optional)
    pins = load_pins()
    pkg = pins["packages"][pkg_key]
    base = _pkg_file_path(pkg, "__init__.py", (roots or {}).get(f"{pkg_key}_root"))
    pkg_dir = base.parent
    mod_name = alias
    if mod_name in sys.modules:
        return sys.modules[mod_name]
    spec = importlib.util.spec_from_file_location(
        mod_name, pkg_dir / "__init__.py",
        submodule_search_locations=[str(pkg_dir)])
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    for fname, pin in pkg.get("files", {}).items():
        if fname == "__init__.py" or pin.get("sha256") is None:
            continue
        sub = fname[:-3] if fname.endswith(".py") else None
        if sub:
            importlib.import_module(f"{mod_name}.{sub}")
    return module
