"""BALLDONTLIE adapter — WINPROB-NG-PREP-V1 (T2).

Security law (owner directive 2026-10-05 + handbook §29):
- The API key is a SECRET. It is never hardcoded, never a default, never
  logged, never echoed, never written to any manifest/handoff/git artifact.
- The key is NOT loaded by this module from chat or files the agent controls.
  Resolution order at runtime: (1) env var BALLDONTLIE_API_KEY, (2) macOS
  Keychain generic password service "balldontlie" (account "winprob-ng").
- FAIL CLOSED: if neither source yields a key, every call raises
  BDLKeyUnavailable BEFORE any network request. Nothing partial.
- Key material never appears in exception text: errors reference the SOURCE
  (env/Keychain), never the value.
"""
from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.request

BASE = "https://api.balldontlie.io/v1"  # official base URL verified from docs.balldontlie.io 2026-10-05: "GET https://api.balldontlie.io/v1/games"
FREE_RATE_LIMIT_PER_MIN = 5
ENV_VAR = "BALLDONTLIE_API_KEY"
KEYCHAIN_SERVICE = "balldontlie"
KEYCHAIN_ACCOUNT = "winprob-ng"


class BDLKeyUnavailable(RuntimeError):
    """Raised when no API key is present in any sanctioned source. Never
    contains key material."""


def _from_env() -> str | None:
    v = os.environ.get(ENV_VAR, "").strip()
    return v or None


def _from_keychain() -> str | None:
    try:
        out = subprocess.run(
            ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE,
             "-a", KEYCHAIN_ACCOUNT, "-w"],
            capture_output=True, text=True, timeout=5, check=True,
        ).stdout.strip()
        return out or None
    except Exception:
        return None


def load_key() -> str:
    for name, getter in (("env", _from_env), ("Keychain", _from_keychain)):
        v = getter()
        if v:
            return v
    raise BDLKeyUnavailable(
        f"no BALLDONTLIE API key found in {ENV_VAR} or Keychain "
        f"({KEYCHAIN_SERVICE}/{KEYCHAIN_ACCOUNT}); load it via one of those "
        "channels (owner action) — the adapter fails closed by design"
    )


class BDLClient:
    def __init__(self, base_url: str | None = None, key: str | None = None):
        self.base = (base_url or os.environ.get("BDL_BASE_URL", BASE)).rstrip("/")
        self._key = key if key is not None else load_key()
        self._n_calls = 0

    @property
    def key_loaded(self) -> bool:
        return bool(self._key)

    def _get(self, path: str, params: dict | None = None) -> dict:
        if not self._key:
            raise BDLKeyUnavailable("BDL client constructed without a key")
        q = ""
        if params:
            q = "?" + "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
        req = urllib.request.Request(
            f"{self.base}{path}{q}",
            headers={"Authorization": self._key},  # docs: plain key, not Bearer
        )
        self._n_calls += 1
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            # Never include headers (key) or full URL in errors
            raise RuntimeError(f"BDL HTTP {e.code} on {path} (params omitted)") from None

    # ---- free-tier endpoints only -------------------------------------
    def games(self, seasons: int | str | None = None, cursor: int = 0):
        return self._get("/games", {"seasons": seasons, "cursor": cursor})

    def teams(self):
        return self._get("/teams")

    def players(self, cursor: int = 0):
        return self._get("/players", {"cursor": cursor})


def check() -> int:
    """CLI: reports key PRESENT/ABSENT by source without ever printing it."""
    src = None
    if _from_env():
        src = "env"
    elif _from_keychain():
        src = "Keychain"
    if src:
        print(f"BDL key: PRESENT (source: {src}; value never printed)")
        return 0
    print(f"BDL key: ABSENT ({ENV_VAR} unset; Keychain {KEYCHAIN_SERVICE}/{KEYCHAIN_ACCOUNT} "
          "not found) — adapter FAILS CLOSED. Owner loads the key via one of those channels.")
    return 3


if __name__ == "__main__":
    raise SystemExit(check())
