"""Authority registry: per-series, fail-closed (plan section 7A.2).

State machine (forward only):

    REGISTERED -> INGESTED -> VERIFIED -> GRANTED | BLOCKED

- no backward transitions; a retry is a NEW attempt record, never a
  rollback;
- GRANTED requires ALL of: PIT verdict PASS_PIT_EVIDENCED (section 11.7),
  license+entitlement authorized, and a PASS canary probe for the exact
  CHANNEL (P-7); any missing/failed item = BLOCKED (no partial credit);
- series outside the frozen S1-S4 target set stay BLOCKED_DATA by
  default, including every channel this plan does not canary-probe.
"""

from __future__ import annotations

import json
import os
from typing import Any, Mapping

from .canonical import sha256_bytes

SCHEMA_VERSION = "v3_authority@1"

STATES = ("REGISTERED", "INGESTED", "VERIFIED", "GRANTED", "BLOCKED")
FORWARD = {
    "REGISTERED": {"INGESTED", "BLOCKED"},
    "INGESTED": {"VERIFIED", "BLOCKED"},
    "VERIFIED": {"GRANTED", "BLOCKED"},
    "GRANTED": set(),
    "BLOCKED": set(),
}

PIT_VERDICTS = ("PASS_PIT_EVIDENCED", "RETROSPECTIVE_ONLY", "BLOCKED_DATA")

#: Frozen first-grant target set (plan section 7A.3).  Additions need a
#: plan amendment; anything else defaults to BLOCKED_DATA.
FROZEN_TARGET_SET = frozenset({
    "S1:form4-xml-substrate", "S1:form4-stream", "S1:eodhd-corp-actions",
    "S2:fred-keyed-vintage-classes", "S3:forex-print-calendars",
    "S3:forex-announcement-ledger", "S4:binance-daily-h1-panels",
    "S4:binance-open-interest",
})


class AuthorityError(Exception):
    pass


class IllegalTransition(AuthorityError):
    pass


class NotInTargetSet(AuthorityError):
    pass


def authority_digest(rows: list[Mapping[str, Any]]) -> str:
    return sha256_bytes(
        json.dumps(list(rows), sort_keys=True, default=str).encode("utf-8")
    )


class AuthorityRegistry:
    """Append-only attempt/journal file + projected current-state table.

    The journal file is the record; the in-memory projection is derived.
    Fail-closed: any ambiguity blocks, nothing infers a PASS.
    """

    def __init__(self, journal_path: str):
        self.journal_path = journal_path
        self._series: dict[str, dict[str, Any]] = {}
        os.makedirs(os.path.dirname(journal_path) or ".", exist_ok=True)
        if os.path.exists(journal_path):
            self._replay()

    # -- journal --------------------------------------------------------- #
    def _append(self, record: Mapping[str, Any]) -> None:
        with open(self.journal_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, sort_keys=True, default=str) + "\n")

    def _apply(self, rec: Mapping[str, Any]) -> None:
        """Apply one journal record to the in-memory projection."""
        kind = rec.get("event")
        if kind == "REGISTER":
            sid = rec["series_id"]
            if sid in self._series:
                raise AuthorityError(
                    f"duplicate REGISTER for {sid} (use a new "
                    "attempt record)"
                )
            self._series[sid] = {
                "series_id": sid,
                "source": rec.get("source"),
                "channel": rec.get("channel"),
                "state": "REGISTERED",
                "attempts": [],
                "pit_verdict": None,
                "license_status": None,
                "entitlement_status": None,
                "canary_probes": {},
                "cads_pins": [],
                "granted_at": None,
                "granted_by": None,
                "blocked_reason": None,
            }
        elif kind == "TRANSITION":
            row = self._series.get(rec["series_id"])
            if row is None:
                raise AuthorityError(
                    f"TRANSITION for unknown series {rec['series_id']}"
                )
            to_state = rec["to_state"]
            if to_state not in FORWARD.get(row["state"], set()):
                raise IllegalTransition(
                    f"{row['state']} -> {to_state} is not a legal "
                    f"forward transition (series {row['series_id']})"
                )
            row["state"] = to_state
            row["attempts"].append(rec.get("attempt"))
        elif kind == "EVIDENCE":
            row = self._series.get(rec["series_id"])
            if row is None:
                raise AuthorityError(
                    f"EVIDENCE for unknown series {rec['series_id']}"
                )
            for key in ("pit_verdict", "license_status",
                        "entitlement_status", "canary_probes",
                        "cads_pins"):
                if key in rec:
                    value = rec[key]
                    if key == "canary_probes":
                        row[key].update(value)
                    elif key == "cads_pins":
                        row[key].extend(value)
                    else:
                        row[key] = value
        elif kind == "GRANT":
            row = self._series[rec["series_id"]]
            row["state"] = "GRANTED"
            row["granted_at"] = rec.get("granted_at")
            row["granted_by"] = rec.get("granted_by")
        elif kind == "BLOCK":
            row = self._series[rec["series_id"]]
            row["state"] = "BLOCKED"
            row["blocked_reason"] = rec.get("reason")
        else:
            raise AuthorityError(
                f"unknown event {kind!r} (CONTROL_STATE_DRIFT)"
            )

    def _replay(self) -> None:
        with open(self.journal_path, "r", encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, 1):
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise AuthorityError(
                        f"journal line {lineno} malformed: {exc}"
                    ) from exc
                try:
                    self._apply(rec)
                except AuthorityError as exc:
                    raise AuthorityError(
                        f"journal line {lineno}: {exc}"
                    ) from exc

    def _append_and_apply(self, record: Mapping[str, Any]) -> None:
        """Append to the journal, then apply to the live projection
        (single state machine, no divergence between journal and memory)."""
        self._append(record)
        self._apply(record)

    # -- API --------------------------------------------------------------- #
    def register(self, series_id: str, source: str, channel: str) -> None:
        if series_id not in FROZEN_TARGET_SET:
            raise NotInTargetSet(
                f"{series_id} is outside the frozen S1-S4 target set; "
                "additions need a plan amendment (defaults BLOCKED_DATA)"
            )
        self._append_and_apply({"event": "REGISTER", "series_id": series_id,
                                "source": source, "channel": channel})

    def transition(self, series_id: str, to_state: str,
                   attempt: str | None = None) -> None:
        row = self._series.get(series_id)
        if row is None:
            raise AuthorityError(f"unknown series: {series_id}")
        if to_state not in FORWARD.get(row["state"], set()):
            raise IllegalTransition(
                f"{row['state']} -> {to_state} forbidden; retries are new "
                "attempt records, never backward transitions"
            )
        self._append_and_apply({"event": "TRANSITION", "series_id": series_id,
                                    "to_state": to_state, "attempt": attempt})

    def evidence(self, series_id: str, *, pit_verdict: str | None = None,
                 license_status: str | None = None,
                 entitlement_status: str | None = None,
                 canary_probe: Mapping[str, str] | None = None,
                 cads_pins: list[str] | None = None) -> None:
        if pit_verdict is not None and pit_verdict not in PIT_VERDICTS:
            raise AuthorityError(f"unknown PIT verdict {pit_verdict!r}")
        payload: dict[str, Any] = {"event": "EVIDENCE",
                                   "series_id": series_id}
        if pit_verdict is not None:
            payload["pit_verdict"] = pit_verdict
        if license_status is not None:
            payload["license_status"] = license_status
        if entitlement_status is not None:
            payload["entitlement_status"] = entitlement_status
        if canary_probe is not None:
            payload["canary_probes"] = dict(canary_probe)
        if cads_pins is not None:
            payload["cads_pins"] = list(cads_pins)
        self._append_and_apply(payload)

    def adjudicate(self, series_id: str, *, granted_by: str,
                   granted_at: str) -> str:
        """Fail-closed adjudication of a VERIFIED series."""
        row = self._series.get(series_id)
        if row is None:
            raise AuthorityError(f"unknown series: {series_id}")
        if row["state"] != "VERIFIED":
            raise AuthorityError(
                f"adjudication requires VERIFIED, got {row['state']}"
            )
        reasons = []
        if row["pit_verdict"] != "PASS_PIT_EVIDENCED":
            reasons.append(f"PIT={row['pit_verdict']!r}")
        if row["license_status"] != "AUTHORIZED":
            reasons.append(f"license={row['license_status']!r}")
        if row["entitlement_status"] != "AUTHORIZED":
            reasons.append(f"entitlement={row['entitlement_status']!r}")
        if not row["cads_pins"]:
            reasons.append("no CADS pins")
        probes = row["canary_probes"]
        channel = row["channel"]
        if probes.get(channel) != "PASS":
            reasons.append(f"canary[{channel}]={probes.get(channel)!r}")
        if reasons:
            reason = "; ".join(reasons)
            self._append_and_apply({"event": "BLOCK", "series_id": series_id,
                                    "reason": reason})
            return f"BLOCKED: {reason}"
        self._append_and_apply({"event": "GRANT", "series_id": series_id,
                                "granted_by": granted_by,
                                "granted_at": granted_at})
        return "GRANTED"

    # -- projections -------------------------------------------------------- #
    def row(self, series_id: str) -> Mapping[str, Any] | None:
        return self._series.get(series_id)

    def rows(self) -> list[dict[str, Any]]:
        return [dict(r) for r in self._series.values()]

    def verdict(self, series_id: str) -> str:
        """The registry verdict for a series: GRANTED or BLOCKED -- no
        partial credit.  Unknown series are BLOCKED_DATA (default)."""
        row = self._series.get(series_id)
        if row is None:
            return "BLOCKED_DATA: not in registry (S1-S4 frozen set)"
        if row["state"] == "GRANTED":
            return "GRANTED"
        return f"BLOCKED: {row.get('blocked_reason') or row['state']}"
