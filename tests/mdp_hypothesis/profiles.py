"""Frozen Hypothesis profiles: mdp_ci (default) and mdp_deep.

Freeze authority: architecture_freeze.json "hypothesis_profiles":

* ``mdp_ci``:  derandomize=True,  max_examples=50,  deadline=None,
  suppress_health_check=[], print_blob=True  — deterministic CI on a shared
  host; per-test slowness is reported by the gate command instead.
* ``mdp_deep``: derandomize=False, max_examples=500, same others —
  alone-running optional gate; seed/host/elapsed recorded in the result JSON.

Importing this module registers both profiles and loads the one named by the
``HYPOTHESIS_PROFILE`` environment variable (default ``mdp_ci``).  Test
modules must call ``os.environ.setdefault("HYPOTHESIS_PROFILE", "mdp_ci")``
BEFORE importing hypothesis or this module.
"""

from __future__ import annotations

import os

from hypothesis import settings


def register_profiles() -> None:
    """Register ``mdp_ci`` and ``mdp_deep`` exactly per the freeze."""
    settings.register_profile(
        "mdp_ci",
        derandomize=True,
        max_examples=50,
        deadline=None,
        suppress_health_check=[],
        print_blob=True,
    )
    settings.register_profile(
        "mdp_deep",
        derandomize=False,
        max_examples=500,
        deadline=None,
        suppress_health_check=[],
        print_blob=True,
    )


register_profiles()

# Profile selection: HYPOTHESIS_PROFILE env var, default mdp_ci (frozen).
_active = os.environ.get("HYPOTHESIS_PROFILE", "mdp_ci")
if _active not in ("mdp_ci", "mdp_deep"):
    raise ValueError(
        f"HYPOTHESIS_PROFILE={_active!r} is not a frozen MDP profile "
        "(expected 'mdp_ci' or 'mdp_deep')")
settings.load_profile(_active)

ACTIVE_PROFILE = _active
