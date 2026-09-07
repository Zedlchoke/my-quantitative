"""V6-P0b (A3): streaming scan of the inherited SEC PIT store.

Read-only consumer of the V5-inherited PIT store at
``/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v5/p0-a3-data/.staging_sec/pit_records.jsonl``.

Contract (dispatch + handbook section 11):

* the sha256 of the store is verified against the pinned value BEFORE any
  content is read (hash-pinning discipline);
* the store is STREAMED line by line — it is never loaded whole;
* nothing in the source tree is modified.

The scan produces a small summary under ``.staging_prices_v6/summaries/``:

* the set of filer entity ids (the 410-filer panel) with per-entity record
  count and last event time;
* the global inventory of distribution-related field names (anything whose
  name matches ``dividend`` or ``split``/``share``-change patterns), with
  counts — this is the evidence base for which corporate-action facts the
  SEC leg can fund;
* the full distribution-fact records for a small set of target entities
  (the light-phase probe names), for the L7 corporate-action cross-check.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set

PIT_STORE_PATH = Path(
    "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v5/"
    "p0-a3-data/.staging_sec/pit_records.jsonl"
)
PIT_STORE_SHA256_PIN = (
    "f53eb3712bc9d686ec8a91b3715beaf73be1e5243a89af1816bd62eea51df955"
)
EXPECTED_RECORDS = 3817158

DISTRIBUTION_FIELD_RE = re.compile(
    r"(dividend|share.*split|split.*share|stocksplit|spinoff|spin.off)",
    re.IGNORECASE,
)


class PitStoreError(RuntimeError):
    """Raised when the store fails hash-pin verification or is malformed."""


def sha256_file(path: Path, chunk_size: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def verify_pin(path: Path = PIT_STORE_PATH, pin: str = PIT_STORE_SHA256_PIN) -> str:
    if not path.exists():
        raise PitStoreError(f"PIT store missing: {path}")
    observed = sha256_file(path)
    if observed != pin:
        raise PitStoreError(
            f"PIT store sha256 pin mismatch: observed {observed} != pinned {pin}"
        )
    return observed


def iter_records(path: Path = PIT_STORE_PATH) -> Iterable[dict]:
    """Stream records one line at a time. Never materializes the file."""
    with path.open("r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:  # fail loud, never skip silently
                raise PitStoreError(f"malformed JSON on line {lineno}: {exc}") from exc


def scan(
    target_entity_ids: Optional[Set[str]] = None,
    path: Path = PIT_STORE_PATH,
    pin: str = PIT_STORE_SHA256_PIN,
) -> dict:
    """Single streaming pass: panel inventory + distribution-field inventory.

    ``target_entity_ids`` (e.g. ``{"CIK0000320193"}``) selects entities whose
    distribution-fact records are kept verbatim for the L7 cross-check.
    """
    observed_sha = verify_pin(path, pin)

    entities: Dict[str, dict] = {}
    distribution_fields: Dict[str, dict] = {}
    target_facts: Dict[str, List[dict]] = {e: [] for e in (target_entity_ids or set())}
    total_records = 0

    for rec in iter_records(path):
        total_records += 1
        ent = rec.get("entity_id", "<missing>")
        field = rec.get("field", "<missing>")
        ev = rec.get("event_time_utc")
        slot = entities.setdefault(
            ent, {"records": 0, "last_event_time_utc": None, "distribution_fields": set()}
        )
        slot["records"] += 1
        if ev is not None and (slot["last_event_time_utc"] is None or ev > slot["last_event_time_utc"]):
            slot["last_event_time_utc"] = ev
        if DISTRIBUTION_FIELD_RE.search(field):
            df = distribution_fields.setdefault(field, {"count": 0, "entities": set()})
            df["count"] += 1
            df["entities"].add(ent)
            slot["distribution_fields"].add(field)
            if ent in target_facts:
                target_facts[ent].append(rec)

    summary = {
        "schema": "stocks_free_v6_run/p0b_pit_scan@1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "store_path": str(path),
        "store_sha256_observed": observed_sha,
        "store_sha256_pin": pin,
        "pin_verification": "EXACT_MATCH",
        "total_records": total_records,
        "total_entities": len(entities),
        "distribution_field_inventory": {
            f: {"count": v["count"], "distinct_entities": len(v["entities"])}
            for f, v in sorted(distribution_fields.items(), key=lambda kv: -kv[1]["count"])
        },
        "entities": {
            ent: {
                "records": v["records"],
                "last_event_time_utc": v["last_event_time_utc"],
                "distribution_fields": sorted(v["distribution_fields"]),
            }
            for ent, v in sorted(entities.items())
        },
        "target_distribution_facts": {
            ent: sorted(
                (f for f in facts), key=lambda r: (r.get("event_time_utc") or "")
            )
            for ent, facts in target_facts.items()
        },
    }
    return summary


def write_summary(summary: dict, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=1, sort_keys=False), encoding="utf-8")
    return out_path
