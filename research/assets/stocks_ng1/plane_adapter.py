"""STOCKS-NG1 plane adapter: the ONLY consumption surface for this cycle.

consume_via_plane shape (platform v3, section 7A.4 law):

    1. AuthorityRegistry verdict for the series MUST be GRANTED
       (fail-closed refusal otherwise, no partial credit);
    2. CADS resolve of the series' pinned address -- verify-on-read
       (the address IS the sha256; any byte drift raises
       CADSIntegrityError and consumption stops);
    3. manifest-verified query: substrate files are only surfaced to
       queries after their sha256 has been checked against the pinned
       substrate manifest (the manifest itself resolved+verified via
       CADS in step 2).

The physical substrate lives under the stocks-free-v13 worktree staging
root as an INHERITED PIN (P-13): read-only, never written from here.

10b5-1 declared-plan observable -- tag discovery (P0, self-discovered
from the pinned substrate, not assumed):

    The real tag is the DOCUMENT-LEVEL element ``<aff10b5One>`` that
    appears between ``</reportingOwner>`` and the transaction tables
    (amended Form 4 schema, in force for post-2023 filings).  Values
    observed in-substrate: ``0``/``1`` and ``false``/``true``; a declared
    plan is value in {``1``, ``true``}.  Evidence path (this worktree's
    read-only view of the inherited pin):
    .staging_sec_v13/form4_xml/CIK0000001800/000110465923077918/tm2320556-1_4seq1.xml
    line 41: ``<aff10b5One>0</aff10b5One>``; value-1 docs verified at
    census time (see p0 census evidence).  In 50,268 sampled docs the
    tag occurs at most once per document (document-level, not
    per-transaction).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import xml.etree.ElementTree as ET
from typing import Any, Iterator, Mapping

_REPO_ROOT = os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.pardir, os.pardir, os.pardir))

#: READ-ONLY content-addressed store (platform v3, never written here).
CADS_STORE_ROOT_DEFAULT = (
    "/Users/hoangminhlong/my-quantitative/.runtime/v3_cads_store")

#: READ-ONLY inherited substrate pin (physical bytes live under the
#: stocks-free-v13 worktree; P-13 archive discipline).
SUBSTRATE_ROOT_DEFAULT = (
    "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v13/"
    "integration/.staging_sec_v13")

#: Authority journal of record (replayed read-only; GRANT records only).
AUTHORITY_JOURNAL_DEFAULT = os.path.join(
    _REPO_ROOT,
    "research/control/research_platform_v3_run/authority_registry_journal.jsonl")

#: Frozen consumption set: exactly the GRANTED S1 series (plan section 3).
FROZEN_CONSUMPTION_SET = (
    "S1:form4-xml-substrate", "S1:form4-stream", "S1:eodhd-corp-actions")

#: Pinned re-pin digests (dispatch packet + V3-GA2/V13 substrate digest).
PIN_SUBSTRATE_MANIFEST_SHA256 = (
    "5d351623675f71a9950d0e290b1fafff89901265f18bf6c687660e96285ea26b")
PIN_FORM4_STREAM_SHA256 = (
    "6ac2cd5bdd62566efe106b46de715030e9a8a940cb90f5a991df5f05ba6742b2")

#: Discovered 10b5-1 declared-plan tag (see module docstring evidence).
FLAG_TAG_10B5_1 = "aff10b5One"
FLAG_TAG_EVIDENCE = (
    "inherited pin (read-only): "
    ".staging_sec_v13/form4_xml/CIK0000001800/000110465923077918/"
    "tm2320556-1_4seq1.xml line 41 <aff10b5One>0</aff10b5One>; "
    "document-level, values 0/1/false/true observed; discovery scan "
    "9,705 docs over 60 issuers 2026-09-11")

_FLAG_VALUES_DECLARED = {"1", "true"}
_FLAG_VALUES_NOT_DECLARED = {"0", "false"}

_FLAG_RE = re.compile(
    rb"<" + FLAG_TAG_10B5_1.encode() + rb"[^>]*>([^<]*)</"
    + FLAG_TAG_10B5_1.encode() + rb">")
_DOCTYPE_RE = re.compile(rb"<documentType>\s*([^<]*?)\s*</documentType>")
_PERIOD_RE = re.compile(rb"<periodOfReport>\s*([^<]*?)\s*</periodOfReport>")
_ISSUER_CIK_RE = re.compile(rb"<issuerCik>\s*([^<]*?)\s*</issuerCik>")
_OWNER_CIK_RE = re.compile(rb"<rptOwnerCik>\s*([^<]*?)\s*</rptOwnerCik>")

#: canary/coverage window: compliance window opens 2023-01-01 (packet).
POST_2023_CUTOFF = "2023-01-01"

CENSUS_A_FLOOR = 500          # flagged (declared-plan) docs, post-2023
CENSUS_B_FLOOR = 200          # "4/A" docs with original resolvable


class ConsumptionRefused(Exception):
    """Fail-closed refusal: only GRANTED series may be consumed."""


class MalformedForm4Error(Exception):
    """Strict Form-4 XML parse failed: fail-closed, never guessed."""


class SubstrateDrift(Exception):
    """Manifest-vs-bytes mismatch: incident, fail-closed (never fixed)."""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def detect_10b5_1_flag(xml_bytes: bytes) -> dict:
    """Strict, fail-closed read of the 10b5-1 declared-plan flag.

    Parses the document (ElementTree) -- malformed XML raises
    MalformedForm4Error and the caller must NOT count the doc as
    flagged (fail-closed, no guessing).  Returns:

        {"declared": bool|None,   # None = tag absent (pre-2023 vintage)
         "value": str|None,       # raw tag value as filed
         "tag": FLAG_TAG_10B5_1,
         "occurrences": int}      # document-level element count
    """
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise MalformedForm4Error(f"Form-4 XML parse failed: {exc}") from exc
    found = root.findall(FLAG_TAG_10B5_1)
    occurrences = len(found)
    if occurrences == 0:
        return {"declared": None, "value": None, "tag": FLAG_TAG_10B5_1,
                "occurrences": 0}
    value = (found[0].text or "").strip()
    declared: bool | None
    if value in _FLAG_VALUES_DECLARED:
        declared = True
    elif value in _FLAG_VALUES_NOT_DECLARED:
        declared = False
    else:
        # Unknown literal: fail-closed for the flag itself, surfaced as
        # an anomaly value (counted in value distribution, never as
        # declared).
        declared = None
    return {"declared": declared, "value": value, "tag": FLAG_TAG_10B5_1,
            "occurrences": occurrences}


def scan_flag_values(xml_bytes: bytes) -> list[str]:
    """Fast mass-scan path: raw values of every byte-level tag
    occurrence.  The census cross-checks this fast path against
    ``detect_10b5_1_flag`` (strict parser) on a bounded sample."""
    return [m.decode("utf-8", "replace")
            for m in _FLAG_RE.findall(xml_bytes)]


class StocksNG1Plane:
    """The STOCKS-NG1 consumption plane (read-only over store + pin)."""

    def __init__(self,
                 store_root: str = CADS_STORE_ROOT_DEFAULT,
                 substrate_root: str = SUBSTRATE_ROOT_DEFAULT,
                 authority_journal: str = AUTHORITY_JOURNAL_DEFAULT) -> None:
        self.store_root = store_root
        self.substrate_root = substrate_root
        self.authority_journal = authority_journal
        if not os.path.isdir(store_root):
            raise ConsumptionRefused(f"CADS store absent: {store_root}")
        self._registry = None  # lazy: platform_v3 import is heavyweight
        self._cads = None

    # ------------------------------------------------------------------ #
    # stage 1: authority gate
    # ------------------------------------------------------------------ #
    @property
    def registry(self):
        if self._registry is None:
            from research.platform_v3.authority import AuthorityRegistry
            if not os.path.exists(self.authority_journal):
                raise ConsumptionRefused(
                    f"authority journal absent: {self.authority_journal}")
            self._registry = AuthorityRegistry(self.authority_journal)
        return self._registry

    def authority_verdict(self, series_id: str) -> str:
        return self.registry.verdict(series_id)

    # ------------------------------------------------------------------ #
    # stage 2: CADS resolve verify-on-read
    # ------------------------------------------------------------------ #
    @property
    def cads(self):
        if self._cads is None:
            from research.platform_v3.cads import CADS
            self._cads = CADS(self.store_root)
        return self._cads

    def pins_for_series(self, series_id: str) -> list[dict]:
        out, seen = [], set()
        for p in self.cads.pins():
            if p["metadata"].get("series") != series_id:
                continue
            if p["address"] in seen:
                continue
            seen.add(p["address"])
            out.append(p)
        return out

    def consume_via_plane(self, series_id: str,
                          role: str | None = None) -> dict:
        """GRANTED gate -> CADS resolve (verify-on-read).  Returns the
        resolved address + bytes; raises ConsumptionRefused /
        CADSIntegrityError / CADSError fail-closed."""
        verdict = self.authority_verdict(series_id)
        if verdict != "GRANTED":
            raise ConsumptionRefused(
                f"series {series_id} verdict={verdict!r}: consumption "
                "refused (fail-closed; only GRANTED series may be "
                "consumed)")
        pins = self.pins_for_series(series_id)
        if not pins:
            raise ConsumptionRefused(f"no CADS pins for {series_id}")
        target = None
        if role is not None:
            for p in pins:
                if p["metadata"].get("role") == role:
                    target = p
                    break
        if target is None:
            target = pins[0]
        address = target["address"]
        data = self.cads.resolve(address)   # verify-on-read
        return {"series": series_id, "resolved_address": address,
                "role": target["metadata"].get("role"),
                "bytes": len(data), "data": data}

    # convenience consumptions over the frozen S1 set ------------------ #
    def plane_manifest(self) -> dict:
        out = self.consume_via_plane(
            "S1:form4-xml-substrate", role="substrate_manifest")
        digest = _sha256_bytes(out["data"])
        if digest != PIN_SUBSTRATE_MANIFEST_SHA256:
            raise SubstrateDrift(
                "substrate manifest digest mismatch: pinned "
                f"{PIN_SUBSTRATE_MANIFEST_SHA256} got {digest}")
        out["sha256"] = digest
        out["manifest"] = json.loads(out["data"])
        return out

    def plane_stream(self) -> dict:
        out = self.consume_via_plane("S1:form4-stream")
        digest = _sha256_bytes(out["data"])
        if digest != PIN_FORM4_STREAM_SHA256:
            raise SubstrateDrift(
                "form4-stream digest mismatch: pinned "
                f"{PIN_FORM4_STREAM_SHA256} got {digest}")
        out["sha256"] = digest
        return out

    @property
    def direct_stream_path(self) -> str:
        return os.path.join(self.substrate_root, "form4_stream.jsonl")

    # ------------------------------------------------------------------ #
    # stage 3: manifest-verified queries
    # ------------------------------------------------------------------ #
    def manifest_verified_file(self, rel_key: str, pinned_sha: str,
                               section: str) -> dict:
        """Verify one substrate file against the pinned manifest digest
        BEFORE any query sees it (manifest-verified query law)."""
        path = os.path.join(self.substrate_root, rel_key)
        if not os.path.isfile(path):
            return {"key": rel_key, "section": section, "status": "MISSING",
                    "path": path}
        digest = _sha256_file(path)
        status = "OK" if digest == pinned_sha else "DRIFT"
        return {"key": rel_key, "section": section, "status": status,
                "sha256": digest, "pinned": pinned_sha, "path": path}

    def iter_manifest_verified(self, manifest: Mapping, section: str,
                               ) -> Iterator[dict]:
        files = manifest["sections"][section]["files"]
        for key, pinned in files.items():
            yield self.manifest_verified_file(key, pinned, section)

    @staticmethod
    def stream_entity_window(rows: list[dict], cik: str,
                             date_from: str, date_to: str) -> list[dict]:
        """Deterministic entity-window slice over stream rows (by
        acceptance timestamp, inclusive bounds, UTC ISO strings sort
        lexicographically)."""
        return [r for r in rows
                if r.get("cik") == cik
                and r.get("acceptance") is not None
                and date_from <= r["acceptance"] <= (date_to + "T23:59:59Z")]

    @staticmethod
    def canonical_rows_digest(rows: list[dict]) -> str:
        """Order-independent canonical digest of a row set."""
        lines = sorted(json.dumps(r, sort_keys=True) for r in rows)
        return _sha256_bytes(("\n".join(lines)).encode("utf-8"))

    def load_stream_rows(self, source: str = "plane") -> list[dict]:
        """Load the full stream through the requested surface.

        plane  -> CADS resolve verify-on-read of the pinned stream object;
        direct -> raw read of the inherited-pin file (V13-direct path).
        """
        if source == "plane":
            data = self.plane_stream()["data"]
        elif source == "direct":
            path = self.direct_stream_path
            if not os.path.isfile(path):
                raise ConsumptionRefused(f"direct stream absent: {path}")
            with open(path, "rb") as fh:
                data = fh.read()
            digest = _sha256_bytes(data)
            if digest != PIN_FORM4_STREAM_SHA256:
                raise SubstrateDrift(
                    f"direct stream digest mismatch: {digest}")
        else:
            raise ValueError(f"unknown source {source!r}")
        return [json.loads(line) for line in data.decode("utf-8").splitlines()
                if line.strip()]


def build_stream_acceptance_index(stream_rows: list[dict]) -> dict:
    """accession (dashes stripped) -> acceptance (filing-time clock)."""
    idx: dict[str, str] = {}
    for r in stream_rows:
        acc = (r.get("accession") or "").replace("-", "")
        acc_ts = r.get("acceptance")
        if not acc or not acc_ts:
            continue
        prev = idx.get(acc)
        if prev is None or acc_ts < prev:
            idx[acc] = acc_ts
    return idx
