"""Forward-only start guard + ledger namespace separation (condition C2).

Resolves audit findings F2 / LEAK1 of the A7 prelaunch G8 refusal
(research/control/prospective_shadow_v1/audits/a7_prelaunch_g8.json):
the forward-only rule is now CODE-ENFORCED inside the scanned engine
surface, not enforced merely by absence.

Frozen semantics:

- ``PROSPECTIVE`` is the only production namespace.
  :func:`assert_forward` REFUSES (:class:`StartGuardError`) any decision
  whose ``scheduled_decision_utc`` is earlier than ``SHADOW_START_UTC``,
  and refuses EVERYTHING when ``SHADOW_START_UTC`` is missing (fail
  closed: nothing runs pre-activation without an explicit start;
  SHADOW_START_UTC is written once only after the G8 delta-audit and the
  owner GO).
- ``REPLAY_NOT_PROSPECTIVE`` is an EXPLICIT opt-in namespace for
  historical replay / diagnostic runs. It must be passed verbatim; it is
  never a default, and no code path in this package selects it
  implicitly.
- Ledger bytes are physically separated: PROSPECTIVE ledgers live under
  ``<runtime_root>/ledgers/`` and replay ledgers under
  ``<runtime_root>/replay_not_prospective/``.
  :func:`prospective_ledger_root` is the prospective root callers
  (dashboard included) must use, so prospective reads can never include
  replay bytes, and replay writes can never land in the prospective
  ledger directory.
- Unknown namespaces are refused (fail closed).
"""

from __future__ import annotations

import datetime as dt
import os
from typing import Optional

NAMESPACE_PROSPECTIVE = "PROSPECTIVE"
NAMESPACE_REPLAY = "REPLAY_NOT_PROSPECTIVE"

#: The complete namespace universe; anything else is refused.
KNOWN_NAMESPACES = (NAMESPACE_PROSPECTIVE, NAMESPACE_REPLAY)

PROSPECTIVE_LEDGERS_DIRNAME = "ledgers"
REPLAY_LEDGERS_DIRNAME = "replay_not_prospective"

ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


class StartGuardError(RuntimeError):
    """A forward-only / namespace separation rule was violated."""


def parse_moment(value) -> dt.datetime:
    """Parse an ISO-Z string or aware datetime into an aware UTC moment."""
    if isinstance(value, dt.datetime):
        if value.tzinfo is None:
            raise StartGuardError(f"naive datetime is not allowed: {value!r}")
        return value.astimezone(dt.timezone.utc)
    if isinstance(value, str):
        try:
            return dt.datetime.strptime(value.strip(), ISO_FMT).replace(
                tzinfo=dt.timezone.utc
            )
        except ValueError as exc:
            raise StartGuardError(
                f"timestamp {value!r} is not {ISO_FMT}: {exc}"
            ) from exc
    raise StartGuardError(f"unsupported timestamp value: {value!r}")


def to_iso_z(moment: dt.datetime) -> str:
    return parse_moment(moment).strftime(ISO_FMT)


def assert_forward(
    now_or_decision_utc,
    shadow_start_utc: Optional[str],
    namespace: str = NAMESPACE_PROSPECTIVE,
) -> None:
    """Refuse any decision that precedes SHADOW_START_UTC.

    ``PROSPECTIVE`` (the default): ``shadow_start_utc`` is REQUIRED; a
    missing start is a refusal (fail closed), and any decision earlier
    than the start is a refusal.

    ``REPLAY_NOT_PROSPECTIVE``: the explicit replay opt-in; the forward
    bound is not applied (historical windows are the point of a replay).

    Any other namespace is refused. Returns None when allowed.
    """
    if namespace not in KNOWN_NAMESPACES:
        raise StartGuardError(
            f"unknown namespace {namespace!r}; expected one of "
            f"{list(KNOWN_NAMESPACES)}"
        )
    if namespace == NAMESPACE_REPLAY:
        return
    if shadow_start_utc is None:
        raise StartGuardError(
            "PROSPECTIVE namespace requires SHADOW_START_UTC; refusing to "
            "run pre-activation without an explicit start (fail closed)"
        )
    start = parse_moment(shadow_start_utc)
    moment = parse_moment(now_or_decision_utc)
    if moment < start:
        raise StartGuardError(
            f"decision {to_iso_z(moment)} precedes SHADOW_START_UTC "
            f"{to_iso_z(start)}; the forward-only rule refuses pre-start "
            "decisions in the PROSPECTIVE namespace"
        )


def ledger_root(runtime_root: str, namespace: str = NAMESPACE_PROSPECTIVE) -> str:
    """Namespace-separated ledger directory root (never mixed)."""
    if namespace == NAMESPACE_PROSPECTIVE:
        return os.path.join(runtime_root, PROSPECTIVE_LEDGERS_DIRNAME)
    if namespace == NAMESPACE_REPLAY:
        return os.path.join(runtime_root, REPLAY_LEDGERS_DIRNAME)
    raise StartGuardError(
        f"unknown namespace {namespace!r}; no ledger root is defined for it"
    )


def prospective_ledger_root(runtime_root: str) -> str:
    """The ONLY ledger root prospective callers may read or write."""
    return ledger_root(runtime_root, NAMESPACE_PROSPECTIVE)


def replay_ledger_root(runtime_root: str) -> str:
    """The ONLY ledger root a REPLAY_NOT_PROSPECTIVE run may write."""
    return ledger_root(runtime_root, NAMESPACE_REPLAY)


def assert_roots_disjoint(prospective_root: str, replay_root: str) -> None:
    """Fail closed unless the two roots are fully path-disjoint."""
    pro = os.path.abspath(prospective_root)
    rep = os.path.abspath(replay_root)
    for outer, inner, label in ((pro, rep, "replay"), (rep, pro, "prospective")):
        if inner == outer or inner.startswith(outer.rstrip(os.sep) + os.sep):
            raise StartGuardError(
                f"{label} ledger root {inner} is inside {outer}; namespace "
                "separation violated"
            )
