"""EMV1-A1 books: anchor (S1∪S3∪S4∪WKND, hold 5) and N2 (S2, hold 5).

Event set: staged `a1_events.jsonl` (forms exactly 10-Q/10-K; amendments
already excluded by the staging law, re-verified here).  R2-3 event
identity (issuer, acceptance instant) is enforced by explicit dedup.

r3-delta changes (G3_FREEZE_ADDENDUM_r3):
- AMB-1: weekend acceptances ARE anchor members — stratum label `WKND`
  ("separate bucket" is a recording label, not an exclusion). N2 (S2-only)
  still excludes them.
- AMB-11: direction ties are EXCLUDED + counted (no direction=0 records).
- DVmed60 eligibility floor applied at book stage; records carry the
  frozen band inputs (dv_band_class, dvmed60_decision, per-side bps).
- ticker_reuse_risk carried from the N4 map (lane I parity).
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from .panel import PanelStore
from .divsplits import ExDateIndex
from .sequencing import build_event_record
from .tzlaw import clock_facts

A1_FORMS = ("10-Q", "10-K")
ANCHOR_STRATA = frozenset({"S1", "S3", "S4"})
N2_STRATA = frozenset({"S2"})

DIRECTION_LABEL = {1: "LONG", -1: "SHORT", 0: "LONG"}  # 0 never books (AMB-11)


@dataclass
class BookRun:
    records: list[dict]
    excluded: list[dict]     # excluded candidates, reason-coded
    dropped: list[dict]      # candidates without a resolvable session grid
    census: dict


def load_a1_events(path: str) -> list[dict]:
    """Load + verify the staged A1 event set; dedup on (cik, acceptance)."""
    events: dict[tuple[str, str], dict] = {}
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        if r["form"] not in A1_FORMS:
            raise ValueError(f"non-anchor form in staged set: {r['form']}")
        key = (r["cik"], r["acceptance_utc"])
        cur = events.get(key)
        # R2-3 identity: one event per (issuer, acceptance instant); the
        # surviving row is the lexicographically smallest (form, accession)
        # (AMB-12).
        if cur is None or (r["form"], r["accession"]) < (cur["form"], cur["accession"]):
            events[key] = r
    return sorted(events.values(), key=lambda r: (r["cik"], r["acceptance_utc"], r["accession"]))


def fold_of(et_date: str) -> str:
    """Fold assignment by ET-local acceptance date (r3 AMB-9)."""
    if et_date < "2018-01-01":
        return "F1"
    if et_date < "2021-01-01":
        return "F2"
    if et_date < "2023-01-01":
        return "F3"
    return "F4"


def build_a1_book(
    events_path: str,
    panels: PanelStore,
    exdates: ExDateIndex,
    arm: str,                 # "anchor" | "n2"
    reuse_risk_ciks: frozenset[str] | set[str] = frozenset(),
) -> BookRun:
    strata = ANCHOR_STRATA if arm == "anchor" else N2_STRATA
    hold = 5
    records, excluded, dropped = [], [], []
    census = {"candidates": 0, "booked": 0, "excluded": 0, "dropped": 0,
              "excluded_by_reason": {}, "dropped_by_reason": {},
              "delisting_exits": 0, "exit_rolled": 0,
              "booked_by_fold": {}, "booked_by_stratum": {},
              "excluded_by_fold": {}, "weekend_bucket_booked": 0}

    for ev in load_a1_events(events_path):
        facts = clock_facts(ev["acceptance_utc"])
        fold = fold_of(facts.et_date)
        # r3 AMB-1: weekend acceptances belong to the ANCHOR (stratum WKND);
        # N2 is the monitored S2 arm and still excludes them.
        if arm == "anchor":
            member = facts.weekend_bucket or facts.stratum in strata
        else:
            member = (not facts.weekend_bucket) and facts.stratum in strata
        if not member:
            continue  # other arm's stratum — not this book, not an exclusion
        census["candidates"] += 1
        stratum_label = "WKND" if facts.weekend_bucket else facts.stratum
        res = build_event_record(
            panel=panels.get(ev["ticker"]),
            exdates=exdates,
            acceptance_utc=ev["acceptance_utc"],
            hold=hold,
            direction_rule="a1",
        )
        if res.status == "DROPPED":
            census["dropped"] += 1
            _bump(census["dropped_by_reason"], res.reason)
            dropped.append({**_excl(ev, facts, stratum_label, res.reason), "fold": fold})
            continue
        if res.status == "EXCLUDED":
            census["excluded"] += 1
            _bump(census["excluded_by_reason"], res.reason)
            _bump_fold(census["excluded_by_fold"], fold)
            excluded.append({**_excl(ev, facts, stratum_label, res.reason), "fold": fold,
                             "ca_detail": res.ca_detail})
            continue
        census["booked"] += 1
        _bump_fold(census["booked_by_fold"], fold)
        _bump(census["booked_by_stratum"], stratum_label)
        if facts.weekend_bucket:
            census["weekend_bucket_booked"] += 1
        if res.delisting_exit:
            census["delisting_exits"] += 1
        if res.notes:
            if "EXIT_ROLLED_B1X1" in res.notes:
                census["exit_rolled"] += 1
        records.append({
            "event_id": f"EMV1-A1:{ev['cik']}:{ev['acceptance_utc']}",
            "cik": ev["cik"],
            "ticker": ev["ticker"],
            "form": ev["form"],
            "acceptance_utc": ev["acceptance_utc"],
            "stratum": stratum_label,
            "direction_session": res.direction_session,
            "direction": DIRECTION_LABEL[res.direction],
            "entry_session": res.entry_session,
            "entry_price": res.entry_price,
            "exit_session": res.exit_session,
            "exit_price": res.exit_price,
            "exclusions_applied": res.notes,
            "delisting_exit": res.delisting_exit,
            "arm": f"A1_{'ANCHOR' if arm == 'anchor' else 'N2'}",
            "hold_sessions": hold,
            "fold": fold,
            "weekend_bucket": facts.weekend_bucket,
            "et_offset_hours": facts.et_offset_hours,
            "dv_band_class": res.dv_band_class,
            "dvmed60_decision": res.dvmed60_decision,
            "cost_entry_bps_x1": res.cost_entry_bps_x1,
            "cost_exit_bps_x1": res.cost_exit_bps_x1,
            "ticker_reuse_risk": ev["cik"] in reuse_risk_ciks,
        })

    records.sort(key=lambda r: r["event_id"])
    return BookRun(records=records, excluded=excluded, dropped=dropped, census=census)


def _excl(ev: dict, facts, stratum_label: str, reason: str) -> dict:
    return {
        "event_id": f"EMV1-A1:{ev['cik']}:{ev['acceptance_utc']}",
        "cik": ev["cik"],
        "ticker": ev["ticker"],
        "form": ev["form"],
        "acceptance_utc": ev["acceptance_utc"],
        "stratum": stratum_label,
        "reason": reason,
    }


def _bump(d: dict, k: str) -> None:
    d[k] = d.get(k, 0) + 1


def _bump_fold(d: dict, fold: str) -> None:
    d[fold] = d.get(fold, 0) + 1
