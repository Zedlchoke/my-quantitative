#!/usr/bin/env python
"""trial_ledger.py — FUTURES-ES-PB1-V1 gate-6 trial ledger + refusal gate.

PURE BOOKKEEPING. This module computes NO PnL and touches NO panel/parquet.
It provides:

  1. TrialLedger  — a 24-slot, append-only JSONL ledger for the frozen
                    identity set, implementing the registered plan §6
                    observed-denominator law: every COMPUTED scored result
                    counts (PASS or FAIL, publication failure included);
                    REFUSED and NOT_RUN do NOT increment the observed
                    denominator.
  2. RefusalGate  — the fail-closed pre-run gate of
                    gate6/scored_runner_spec.md §1 (R1 NO_GO / R2 NO_AUTH /
                    R3 LOCK / R4 DRIFT / R5 ADJUDICATION), evaluated against
                    DECLARED facts supplied by the caller (the gate itself
                    performs no IO beyond optional file hashing it is handed
                    pre-computed digests for).
  3. twin_manifest / twin_compare — reproduction-twin bookkeeping: manifest
                    of {relpath: sha256} over a result directory; byte-match
                    comparison of two manifests (G8 evidence at the
                    bookkeeping layer).

Every ledger row is hash-chained (prev_row_sha) and the file is opened
append-only; tampering with any historical row breaks the chain and is
detected by verify().
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

STATUSES = ("NOT_RUN", "PASS", "FAIL", "REFUSED")
# statuses that count as a COMPUTED scored result (observed denominator):
OBSERVED_COUNTING = ("PASS", "FAIL")
REFUSAL_REASONS = (
    "REFUSED_NO_GO",
    "REFUSED_NO_AUTH",
    "NOT_RUN_RESOURCE_CONFLICT",
    "REFUSED_CONTROL_STATE_DRIFT",
    "REFUSED_DRIFT",
    "REFUSED_PINS_UNRESOLVED",
)


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _row_sha(row: dict) -> str:
    canonical = json.dumps(row, sort_keys=True, ensure_ascii=False,
                           separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


class LedgerError(Exception):
    pass


class TrialLedger:
    """Append-only 24-slot trial ledger (JSONL), pure bookkeeping.

    Slot law: the 24 identity ids are fixed at construction (byte-exact
    transcription of the frozen identity table). A ledger file can carry at
    most ONE terminal row (PASS/FAIL/REFUSED) per identity; intermediate
    NOT_RUN annotations are allowed but a terminal row is final and further
    rows for that identity are refused.
    """

    SCHEMA = "trial_ledger@1"

    def __init__(self, path, identity_ids):
        ids = list(identity_ids)
        if len(ids) != 24 or len(set(ids)) != 24:
            raise LedgerError(
                f"slot law violation: need 24 unique identity ids, got "
                f"{len(ids)} ({len(set(ids))} unique)")
        self.path = Path(path)
        self.identity_ids = ids
        self._seq = 0
        self._prev_sha = None
        self._terminal = {}  # identity_id -> status
        self._rows_cache = []
        if self.path.exists():
            self._replay()

    # -- internals ---------------------------------------------------------
    def _replay(self):
        """Verify + replay an existing ledger file (chain + append-only law).

        Chain law: every row carries prev_row_sha = canonical sha256 of the
        PREVIOUS row as parsed from disk (None for row 1). Tampering with any
        non-final row breaks its successor's link; tampering with the final
        row changes summary().file_sha256 (checked by the caller against the
        digest it recorded). Seq must be 1..N with no gaps/dupes.
        """
        prev_parsed = None
        with open(self.path, "r", encoding="utf-8") as fh:
            for i, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    raise LedgerError(f"blank line at {self.path}:{i}")
                row = json.loads(line)
                if row.get("seq") != i:
                    raise LedgerError(
                        f"append-only violation: seq {row.get('seq')} at line {i}")
                if i > 1:
                    if row.get("prev_row_sha") != _row_sha(prev_parsed):
                        raise LedgerError(
                            f"hash-chain break at line {i} (predecessor "
                            f"tampered or link rewritten)")
                iid = row["identity_id"]
                if iid is not None and iid not in self.identity_ids:
                    raise LedgerError(f"unknown identity slot {iid!r} at line {i}")
                if row["status"] in ("PASS", "FAIL", "REFUSED"):
                    if iid is not None:
                        if iid in self._terminal:
                            raise LedgerError(
                                f"double-terminal for {iid} at line {i}")
                        self._terminal[iid] = row["status"]
                self._seq = i
                self._prev_sha = _row_sha(row)
                prev_parsed = row
                self._rows_cache.append(row)

    def _append(self, row: dict) -> dict:
        self._seq += 1
        full = {"seq": self._seq, "schema": self.SCHEMA, "ts_utc": _utcnow(),
                "prev_row_sha": self._prev_sha}
        full.update(row)
        line = json.dumps(full, sort_keys=True, ensure_ascii=False,
                          separators=(",", ":"))
        # append-only: open in 'a', single line + '\n', flush + fsync
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        if row["identity_id"] is not None and row["status"] in (
                "PASS", "FAIL", "REFUSED"):
            if row["identity_id"] in self._terminal:
                # rollback in-memory counters; the file write already happened
                # only in the double-terminal race below — pre-checked, so we
                # never get here; keep the invariant loud.
                raise LedgerError("double-terminal (internal)")
            self._terminal[row["identity_id"]] = row["status"]
        self._prev_sha = _row_sha(full)
        self._rows_cache.append(full)
        return dict(full)

    # -- public API --------------------------------------------------------
    def record_result(self, identity_id, status, *, note="", published=None,
                      result_sha=None, computed_by=""):
        """Record one row. status in STATUSES.

        PASS/FAIL = a computed scored result (increments the observed
        denominator; `published` may be False — publication failure still
        counts). NOT_RUN/REFUSED never increment the observed denominator.
        """
        if status not in STATUSES:
            raise LedgerError(f"bad status {status!r}")
        if identity_id not in self.identity_ids:
            raise LedgerError(f"unknown identity slot {identity_id!r}")
        if status in ("PASS", "FAIL", "REFUSED") and identity_id in self._terminal:
            raise LedgerError(
                f"slot {identity_id} already terminal "
                f"({self._terminal[identity_id]}) — append-only, no overwrite")
        if status in OBSERVED_COUNTING and published is None:
            published = True  # default; a publication failure is recorded False
        row = {"identity_id": identity_id, "status": status, "note": note,
               "published": published, "result_sha": result_sha,
               "computed_by": computed_by,
               "counts_observed": status in OBSERVED_COUNTING}
        return self._append(row)

    def record_refusal(self, reason, *, note=""):
        """A run-level refusal (before any identity compute): one row per
        refusal event with identity_id=None. Never counts observed."""
        if reason not in REFUSAL_REASONS:
            raise LedgerError(f"bad refusal reason {reason!r}")
        row = {"identity_id": None, "status": "REFUSED", "reason": reason,
               "note": note, "published": None, "result_sha": None,
               "computed_by": "refusal_gate", "counts_observed": False}
        return self._append(row)

    def observed(self) -> int:
        """Observed denominator: number of COMPUTED scored results."""
        return sum(1 for r in self._rows_cache if r.get("counts_observed"))

    def summary(self) -> dict:
        per = {iid: self._terminal.get(iid, "NOT_RUN") for iid in self.identity_ids}
        counts = {s: sum(1 for v in per.values() if v == s)
                  for s in STATUSES}
        return {
            "schema": self.SCHEMA,
            "slots": 24,
            "per_identity": per,
            "status_counts": counts,
            "observed_denominator": self.observed(),
            "complete": counts["PASS"] + counts["FAIL"] + counts["REFUSED"] == 24,
            "rows": len(self._rows_cache),
            "file_sha256": (hashlib.sha256(self.path.read_bytes()).hexdigest()
                            if self.path.exists() else None),
        }

    def verify(self) -> dict:
        """Full re-read + chain verification from disk (independent of cache)."""
        fresh = TrialLedger.__new__(TrialLedger)
        fresh.path = self.path
        fresh.identity_ids = self.identity_ids
        fresh._seq = 0
        fresh._prev_sha = None
        fresh._terminal = {}
        fresh._rows_cache = []
        fresh._replay()
        return {"ok": True, "rows": fresh._seq,
                "observed_denominator": fresh.observed()}


# ---------------------------------------------------------------------------
# Refusal gate (spec §1) — evaluated against DECLARED facts. Pure function.
# ---------------------------------------------------------------------------

CANONICAL_GO_PHRASE = "GO FUTURES-ES-PB1-V1 SCORED EXECUTION"

class RefusalGate:
    """Fail-closed pre-run gate. `facts` keys (all declared by the caller):
      go_phrase            — the exact typed phrase from the GO record
      go_phrase_owner_typed— bool (owner-only law; delegation => False)
      registry_go_phrase   — the registry row's go_phrase field
      a7_verdict           — e.g. 'AUTHORIZED_WITH_FINDINGS'
      a7_high_critical     — int count of unresolved HIGH/CRITICAL
      lock_state           — 'FREE_PROVEN' | 'BUSY' | 'DRIFT'
      input_sha_matches    — dict pin_name -> bool (all must be True)
      pins_status          — 'ADJUDICATED_AUTHORITY_EXISTS' |
                             'OWNER_ACKNOWLEDGED' | 'VARIANT_ORDERED'
    Returns (allowed: bool, reason: str|None, detail: dict).
    """

    ORDER = ("go", "auth", "lock", "drift", "pins")

    def evaluate(self, facts: dict):
        # R1 NO_GO
        phrase = facts.get("go_phrase")
        if (phrase != CANONICAL_GO_PHRASE
                or facts.get("registry_go_phrase") != CANONICAL_GO_PHRASE
                or not facts.get("go_phrase_owner_typed", False)):
            return False, "REFUSED_NO_GO", {
                "gate": "R1",
                "law": "registered plan §5: exact typed owner GO; paraphrase/"
                       "early/delegated GO = intent only, dies unconsumed",
                "go_phrase": phrase,
                "expected": CANONICAL_GO_PHRASE,
                "owner_typed": facts.get("go_phrase_owner_typed", False),
            }
        # R2 NO_AUTH
        if (facts.get("a7_verdict") != "AUTHORIZED_WITH_FINDINGS"
                or facts.get("a7_high_critical", 99) != 0):
            return False, "REFUSED_NO_AUTH", {
                "gate": "R2", "a7_verdict": facts.get("a7_verdict"),
                "a7_high_critical": facts.get("a7_high_critical")}
        # R3 LOCK
        lock = facts.get("lock_state")
        if lock == "BUSY":
            return False, "NOT_RUN_RESOURCE_CONFLICT", {
                "gate": "R3",
                "law": "one heavy job machine-wide; never kill a foreign worker"}
        if lock != "FREE_PROVEN":
            return False, "REFUSED_CONTROL_STATE_DRIFT", {
                "gate": "R3", "lock_state": lock}
        # R4 DRIFT
        mismatches = [k for k, ok in (facts.get("input_sha_matches") or {}).items()
                      if not ok]
        if mismatches:
            return False, "REFUSED_DRIFT", {"gate": "R4", "mismatched_pins": mismatches}
        # R5 ADJUDICATION
        pins = facts.get("pins_status")
        if pins == "VARIANT_ORDERED":
            return False, "REFUSED_PINS_UNRESOLVED", {
                "gate": "R5",
                "law": "D-A4/D-A5 adjudicated AUTHORITY_EXISTS (SPEC-dispositive); "
                       "any different variant is a freeze amendment, not a "
                       "runner option"}
        if pins not in ("ADJUDICATED_AUTHORITY_EXISTS", "OWNER_ACKNOWLEDGED"):
            return False, "REFUSED_PINS_UNRESOLVED", {
                "gate": "R5", "pins_status": pins}
        return True, None, {"gates_passed": list(self.ORDER)}


# ---------------------------------------------------------------------------
# Reproduction-twin bookkeeping (G8 evidence layer)
# ---------------------------------------------------------------------------

def twin_manifest(dirpath) -> dict:
    """{relpath: sha256} over every file under dirpath (sorted, deterministic)."""
    root = Path(dirpath)
    out = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            out[str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def twin_compare(manifest_a: dict, manifest_b: dict) -> dict:
    """Byte-match comparison of two twin manifests."""
    only_a = sorted(set(manifest_a) - set(manifest_b))
    only_b = sorted(set(manifest_b) - set(manifest_a))
    differing = sorted(k for k in set(manifest_a) & set(manifest_b)
                       if manifest_a[k] != manifest_b[k])
    return {"byte_match": not (only_a or only_b or differing),
            "n_files_a": len(manifest_a), "n_files_b": len(manifest_b),
            "only_in_a": only_a, "only_in_b": only_b,
            "differing": differing}
