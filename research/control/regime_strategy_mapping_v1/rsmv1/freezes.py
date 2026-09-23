"""Freeze loading + sha256 verification for jrv2.

Law: the runner re-verifies every freeze digest against
``freezes/freeze_manifest.json`` at start (zero post-freeze mutation) and
asserts the exact mapping-file digest before any backtest. Any mismatch is a
hard failure (FreezeViolation) — never a warning.

state_id salts are namespaced JRV2 (V1 isolation):
  asset_salt = sha256('JRV2' || asset || data_sha256)[:16]
  state_id   = sha256(asset_salt || str(bar_close_ns))[:16]
A collision test (V1 salts vs V2 salts for identical bars) is mandatory in
tests and provably disjoint by construction.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .security import safe_open

FREEZE_MANIFEST = "freeze_manifest.json"
MAPPING_FILE = "mapping_arms_freeze.json"

ALL_FREEZE_FILES = (
    "adapter_contract.json",
    "canary_v2_contract.json",
    "data_identity_freeze.json",
    "evaluation_contract.json",
    "fold_contract.json",
    MAPPING_FILE,
    "model_pin.json",
    "question_contract.json",
    "safety_persistence_contract.json",
    "semantic_state_contract.json",
)


class FreezeViolation(RuntimeError):
    """A freeze file is missing, mutated, or fails a binding assertion."""


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with safe_open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json(obj) -> str:
    """Canonical JSON string used for input digests (sorted keys, no spaces).

    SINGLE canonicalization authority: computed by this Python producer only;
    the TS adapter echoes the digest verbatim and never recomputes it
    (V1 amendment_1 law, carried into V2).
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def load_json(path: str | Path):
    with safe_open(path, "rb") as f:
        return json.loads(f.read().decode("utf-8"))


class Freezes:
    """Verified view over the 10 freeze files of the cycle."""

    def __init__(self, cycle_dir: str | Path) -> None:
        self.cycle_dir = Path(cycle_dir).resolve()
        self.freezes_dir = self.cycle_dir / "freezes"
        self.manifest = load_json(self.freezes_dir / FREEZE_MANIFEST)
        self.verify()

    # -- verification ----------------------------------------------------

    def verify(self) -> dict:
        """Re-verify every freeze digest vs the manifest. Raises on mismatch."""
        files = self.manifest.get("files", {})
        if self.manifest.get("schema") != "jrv2_freeze_manifest@1":
            raise FreezeViolation("manifest schema mismatch")
        missing = [n for n in ALL_FREEZE_FILES if n not in files]
        if missing:
            raise FreezeViolation(f"manifest missing files: {missing}")
        report = {"verified": [], "sha256": {}}
        for name, digest in sorted(files.items()):
            path = self.freezes_dir / name
            if not path.exists():
                raise FreezeViolation(f"freeze file missing: {name}")
            actual = sha256_file(path)
            if actual != digest:
                raise FreezeViolation(
                    f"freeze digest mismatch: {name}: manifest={digest} actual={actual}"
                )
            report["verified"].append(name)
            report["sha256"][name] = actual
        self._verify_report = report
        return report

    def assert_mapping_digest(self) -> str:
        """Assert the mapping/arms file digest equals its manifest value."""
        expected = self.manifest["files"][MAPPING_FILE]
        actual = sha256_file(self.freezes_dir / MAPPING_FILE)
        if actual != expected:
            raise FreezeViolation("mapping/arms freeze mutated post-freeze")
        return actual

    # -- accessors ---------------------------------------------------------

    @property
    def data_identity(self):
        return load_json(self.freezes_dir / "data_identity_freeze.json")

    @property
    def semantic_state_contract(self):
        return load_json(self.freezes_dir / "semantic_state_contract.json")

    @property
    def question_contract(self):
        return load_json(self.freezes_dir / "question_contract.json")

    @property
    def safety_persistence_contract(self):
        return load_json(self.freezes_dir / "safety_persistence_contract.json")

    @property
    def mapping(self):
        return load_json(self.freezes_dir / MAPPING_FILE)

    @property
    def fold_contract(self):
        return load_json(self.freezes_dir / "fold_contract.json")

    @property
    def model_pin(self):
        return load_json(self.freezes_dir / "model_pin.json")

    @property
    def adapter_contract(self):
        return load_json(self.freezes_dir / "adapter_contract.json")

    @property
    def canary_contract(self):
        return load_json(self.freezes_dir / "canary_v2_contract.json")

    @property
    def evaluation_contract(self):
        return load_json(self.freezes_dir / "evaluation_contract.json")

    # -- derived constants -------------------------------------------------

    def persistence_params(self) -> dict:
        p = self.safety_persistence_contract["persistence_params"]
        return {
            "min_confidence": float(p["min_confidence"]),
            "min_margin": float(p["min_margin"]),
            "confirm_bars": int(p["confirm_bars"]),
            "min_dwell": int(p["min_dwell"]),
            "cooldown": int(p["cooldown"]),
        }

    def warmup(self, cell: str) -> int:
        return int(self.fold_contract["cells"][cell]["warmup"])

    def data_sha(self, asset: str) -> str:
        ident = self.data_identity
        if asset == "btcusdt":
            return ident["BTCUSDT"]["file_sha256"]
        if asset == "spy":
            return ident["SPY"]["file_sha256"]
        raise FreezeViolation(f"unknown asset {asset}")

    def asset_salt(self, asset: str) -> str:
        """asset_salt = sha256('JRV2'||asset||data_sha256)[:16] — V2 namespace."""
        h = hashlib.sha256(
            ("JRV2" + asset + self.data_sha(asset)).encode("utf-8")
        ).hexdigest()
        return h[:16]

    def state_id(self, asset: str, regime_bar_close_ns: int) -> str:
        """state_id = sha256(asset_salt || str(bar_close_ns))[:16]."""
        salt = self.asset_salt(asset)
        payload = (salt + str(int(regime_bar_close_ns))).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()[:16]


def default_cycle_dir() -> Path:
    """Cycle directory of this checkout (…/research/control/jev_regime_router_v2)."""
    return Path(__file__).resolve().parent.parent
