"""NCAA GBM layer (PAPERDESK-FIXALL-NCAA-V1 W5.3) — the frozen challenger
of the audited intake: sklearn HistGradientBoostingClassifier, ALL
defaults, random_state=0, trained on REGULAR-SEASON games of seasons < Y
only; features frozen (ncaa_state_store.FEATURES), computed pre-game by the
state store.

ARTIFACT LAW: a fitted model is persisted per (league, eval-season) with a
sha256 manifest — pinned like every engine; predictions record the artifact
sha. WITHOUT sklearn the lane degrades HONESTLY to the frozen Elo layer
(p_elo — the audited baseline-beating layer) with mode
ELO_FALLBACK_NO_SKLEARN journaled; the refit job refuses loudly instead of
pretending.
"""
from __future__ import annotations

import hashlib
import json
import pickle
from pathlib import Path

from research.papertrade_exec.ncaa_state_store import FEATURES


def refit(artifacts_dir: Path, league: str, season: int,
          train_rows: list[dict]) -> dict:
    """train_rows: [{features: {name: value}, y: 0|1}] of REGULAR-season
    games with season < Y (the caller enforces the PIT cut). Returns the
    artifact manifest {path, sha256, n_train, season, league}."""
    try:
        from sklearn.ensemble import HistGradientBoostingClassifier
    except ModuleNotFoundError as e:
        raise RuntimeError("NOT_RUN_SKLEARN_ABSENT: the GBM layer needs "
                           "scikit-learn in the runner venv — the lane "
                           "stays on the frozen Elo layer until then") from e
    if not train_rows:
        raise ValueError("no training rows (seasons < Y)")
    X = [[float(r["features"][k]) for k in FEATURES] for r in train_rows]
    y = [int(r["y"]) for r in train_rows]
    gbm = HistGradientBoostingClassifier(random_state=0)
    gbm.fit(X, y)
    artifacts_dir = Path(artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    name = f"{league}_{season}_gbm.pkl"
    blob = pickle.dumps(gbm, protocol=4)
    path = artifacts_dir / name
    path.write_bytes(blob)
    manifest = {"league": league, "season": season, "n_train": len(y),
                "artifact": str(path),
                "sha256": hashlib.sha256(blob).hexdigest(),
                "features": list(FEATURES)}
    (artifacts_dir / f"{name}.manifest.json").write_text(
        json.dumps(manifest, indent=1, sort_keys=True))
    return manifest


def load_pinned(artifacts_dir: Path, league: str, season: int):
    """Load the artifact and VERIFY it against its manifest sha (pin law).
    Returns (model, manifest) or (None, why)."""
    name = f"{league}_{season}_gbm.pkl"
    path = Path(artifacts_dir) / name
    mpath = Path(artifacts_dir) / f"{name}.manifest.json"
    if not path.exists() or not mpath.exists():
        return None, f"artifact {name} absent (refit job has not run)"
    manifest = json.loads(mpath.read_text())
    blob = path.read_bytes()
    if hashlib.sha256(blob).hexdigest() != manifest.get("sha256"):
        return None, f"artifact {name} sha drift — refit required"
    try:
        return pickle.loads(blob), manifest
    except Exception as e:                     # unpickling failure
        return None, f"artifact {name} unreadable: {e}"


def predict_home_p(model, feature_rows: list) -> list[float]:
    # rows may be feature DICTS or pre-built vectors (ncaa_state_store.
    # feature_vector output); both carry FEATURES order.
    X = [[float(r[k] if isinstance(r, dict) else r[i])
          for i, k in enumerate(FEATURES)] for r in feature_rows]
    return [float(p) for p in model.predict_proba(X)[:, 1]]
