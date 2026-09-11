"""Calendar engine: versioned session manifests via exchange_calendars.

Implements the frozen V3 calendar contract (plan section 6).  Package
calendars are maintained software data, never an exchange legal
announcement:

- every manifest carries the calendar name, package version and a package
  content digest, so a package upgrade changes the digest;
- official cross-check evidence is an input; ABSENT is recorded honestly
  (cross_check_status = ABSENT_NOT_EVALUABLE) and a recorded DISAGREEMENT
  fails closed (BLOCKED_OFFICIAL_DISAGREEMENT);
- forex sessions and crypto 24/7 clocks refuse accidental equity-calendar
  routing (explicit asset-class gate);
- generated-at metadata is excluded from the canonical identity digest.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import exchange_calendars as xc
import pandas as pd

from .canonical import canonical_digest

SCHEMA_VERSION = "v3_calendar_engine@1"

#: Asset classes with distinct session semantics (never equity-routed).
NON_EQUITY_ASSET_CLASSES = ("forex", "crypto")


class CalendarAuthorityError(Exception):
    pass


class EquityRoutingRefused(CalendarAuthorityError):
    """forex/crypto asked for an equity calendar: refuse, never inherit."""


class OfficialDiscrepancyBlocked(CalendarAuthorityError):
    """official cross-check disagrees: fail closed, never pick-to-pass."""


@dataclass(frozen=True)
class CalendarPin:
    calendar_name: str          # ISO MIC, e.g. XNYS
    package_version: str
    package_source_digest: str  # digest of the pinned package bytes


def package_pin() -> CalendarPin:
    """Pin the installed exchange_calendars package (version + content)."""
    import hashlib
    import exchange_calendars
    from importlib.metadata import version
    pkg_dir = None
    pkg_version = version("exchange_calendars")
    # content digest: hash the exchange_calendars package directory bytes
    import os
    pkg_dir = os.path.dirname(exchange_calendars.__file__)
    h = hashlib.sha256()
    for root, _dirs, files in sorted(os.walk(pkg_dir)):
        for fn in sorted(files):
            p = os.path.join(root, fn)
            h.update(fn.encode())
            with open(p, "rb") as fh:
                while True:
                    b = fh.read(1 << 20)
                    if not b:
                        break
                    h.update(b)
    return CalendarPin("exchange_calendars", pkg_version, h.hexdigest())


@dataclass(frozen=True)
class CrossCheckEvidence:
    """Official-source cross-check evidence supplied by the caller."""

    status: str                 # MATCH | DISAGREEMENT | ABSENT
    source_id: str | None
    evidence_digest: str | None
    exceptions: Sequence[Mapping[str, Any]] = ()


def next_valid_session(cal: xc.ExchangeCalendar,
                       on_or_after: str) -> str:
    """Map a release date to the next valid session (inclusive)."""
    minutes = cal.schedule.index
    stamp = pd.Timestamp(on_or_after)
    later = minutes[minutes >= stamp]
    if len(later) == 0:
        raise CalendarAuthorityError("no session at/after requested date")
    return str(later[0].date())


class SessionManifestBuilder:
    """Emit versioned session manifests with canonical content digests."""

    def __init__(self, pin: CalendarPin):
        self._pin = pin

    # ------------------------------------------------------------------ #
    def build(self, calendar_name: str, asset_class: str,
              start: str, end: str, timezone_name: str,
              cross_check: CrossCheckEvidence | None = None,
              generated_at_utc: str = "") -> Mapping[str, Any]:
        if asset_class in NON_EQUITY_ASSET_CLASSES:
            raise EquityRoutingRefused(
                f"asset class {asset_class!r} must not be routed through "
                f"equity-style calendar {calendar_name!r}; use its own "
                "session semantics"
            )
        if cross_check is not None and cross_check.status == "DISAGREEMENT":
            raise OfficialDiscrepancyBlocked(
                "official cross-check DISAGREEMENT: fail closed "
                "(V3 never picks the result that makes coverage pass)"
            )

        try:
            cal = xc.get_calendar(calendar_name, start=start, end=end)
            schedule = cal.schedule
        except xc.errors.NoSessionsError:
            # a request range with zero sessions (e.g. a weekend) is a
            # legitimate, honestly-empty manifest -- not an error
            cal = None
            schedule = []
        sessions = []
        early_dates = set()
        if cal is not None:
            early_dates = {ts.date() for ts in cal.early_closes}
        for stamp, row in (schedule.iterrows() if cal is not None else []):
            opens = row["open"]
            closes = row["close"]
            break_start = row.get("break_start")
            break_end = row.get("break_end")
            label = str(stamp.date())
            early = stamp.date() in early_dates
            sessions.append({
                "session": label,
                "open_utc": str(opens.tz_convert("UTC")),
                "close_utc": str(closes.tz_convert("UTC")),
                "break_start_utc": (str(break_start.tz_convert("UTC"))
                                    if pd.notna(break_start) else None),
                "break_end_utc": (str(break_end.tz_convert("UTC"))
                                  if pd.notna(break_end) else None),
                "early_close": early,
            })

        cc = cross_check or CrossCheckEvidence(
            status="ABSENT", source_id=None, evidence_digest=None
        )
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "calendar_name": calendar_name,
            "asset_class": asset_class,
            "calendar_package": {
                "name": self._pin.calendar_name,
                "version": self._pin.package_version,
                "source_digest": self._pin.package_source_digest,
            },
            "requested_range": {"start": start, "end": end},
            "timezone": timezone_name,
            "sessions": sessions,
            "official_cross_check": {
                "status": cc.status,
                "source_id": cc.source_id,
                "evidence_digest": cc.evidence_digest,
                "exceptions": list(cc.exceptions),
            },
            # generated-at is EXCLUDED from the identity digest below
            "generated_at_utc": generated_at_utc,
        }
        identity_payload = {
            k: v for k, v in manifest.items() if k != "generated_at_utc"
        }
        manifest["canonical_content_digest"] = canonical_digest(identity_payload)
        return manifest

    # ------------------------------------------------------------------ #
    @staticmethod
    def verify_official_cross_check(manifest: Mapping[str, Any]) -> str:
        """Gate: a manifest may only be consumed when the cross-check is
        MATCH or ABSENT-honest; DISAGREEMENT manifests never reach here
        (build raises) -- this verifier is the second, fail-closed net."""
        status = manifest["official_cross_check"]["status"]
        if status == "DISAGREEMENT":
            return "BLOCKED_OFFICIAL_DISAGREEMENT"
        if status == "MATCH":
            return "PASS"
        return "PASS_ABSENT_RECORDED" if status == "ABSENT" else \
            f"NOT_EVALUABLE_{status}"
