"""Environment credential presence checks without value disclosure.

Secrets are read from the root checkout's gitignored .env. This module only
reports PRESENT/MISSING and hands the in-memory value to request builders;
values must never be logged, written to manifests, or embedded in URLs that
get stored.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional

from .contract import CredentialMissing

DEFAULT_ENV_PATH = Path("/Users/hoangminhlong/my-quantitative/.env")


def parse_env_keys(env_path: Path) -> Dict[str, bool]:
    """Return name -> PRESENT mapping. Values are parsed and discarded."""
    presence: Dict[str, bool] = {}
    if not env_path.is_file():
        return presence
    with env_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name = line.split("=", 1)[0].strip()
            if name:
                presence[name] = True
    return presence


def check_presence(names: list, env_path: Optional[Path] = None) -> Dict[str, str]:
    """PRESENT/MISSING verdict per name. No value ever survives this call."""
    path = env_path or DEFAULT_ENV_PATH
    keys = parse_env_keys(path)
    verdict: Dict[str, str] = {}
    for name in names:
        if name in keys:
            verdict[name] = "PRESENT"
        elif os.environ.get(name):
            verdict[name] = "PRESENT"
        else:
            verdict[name] = "MISSING"
    return verdict


def load_secret(name: str, env_path: Optional[Path] = None) -> str:
    """Read a secret into memory for request construction only."""
    path = env_path or DEFAULT_ENV_PATH
    if path.is_file():
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                if key.strip() == name:
                    return value.strip().strip('"').strip("'")
    value = os.environ.get(name)
    if not value:
        raise CredentialMissing(f"credential {name} MISSING; fail closed")
    return value
