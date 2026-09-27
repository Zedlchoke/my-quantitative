"""EMV1-A1 books: anchor (S1∪S3∪S4, hold 5) and N2 (S2, hold 5).

Event set: staged `a1_events.jsonl` (forms exactly 10-Q/10-K; amendments
already excluded by the staging law, re-verified here).  R2-3 event
identity (issuer, acceptance instant) is enforced by explicit dedup.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from .panel import PanelStore
from .divsplits import ExDateIndex
from .sequencing import build_event_record
from .tzlaw import clock_facts, parse_acceptance

A1_FORMS = ("10-Q", "10-K")
ANCHOR_STRATA = frozenset({"S1", "S3", "S4"})
N2_STRATA = frozenset({"S2"})


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
    """Fold assignment by ET-local acceptance date (see AMB-09)."""
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
) -> BookRun:
    strata = ANCHOR_STRATA if arm == "anchor" else N2_STRATA
    hold = 5
    records, excluded, dropped = [], [], []
    census = {"candidates": 0, "booked": 0, "excluded": 0, "dropped": 0,
              "excluded_by_reason": {}, "dropped_by_reason": {},
              "delisting_exits": 0, "flat_direction": 0,
              "booked_by_fold": {}, "booked_by_stratum": {},
              "excluded_by_fold": {}, "weekend_bucket_candidates": 0}

    for ev in load_a1_events(events_path):
        census["candidates"] += 1
        facts = clock_facts(ev["acceptance_utc"])
        if facts.weekend_bucket:
            census["weekend_bucket_candidates"] += 1
            excluded.append(_excl(ev, facts, "WEEKEND_BUCKET_SEPARATE"))
            _bump(census["excluded_by_reason"], "WEEKEND_BUCKET_SEPARATE")
            census["excluded"] += 1
            _bump_fold(census["excluded_by_fold"], fold_of(facts.et_date))
            continue
        if facts.stratum not in strata:
            continue  # other arm's stratum — not this book, not an exclusion
        census["candidates"] = census["candidates"]  # (counter already advanced)
        res = build_event_record(
            panel=panels.get(ev["ticker"]),
            exdates=exdates,
            acceptance_utc=ev["acceptance_utc"],
            hold=hold,
            direction_rule="a1",
        )
        fold = fold_of(facts.et_date)
        if res.status == "DROPPED":
            census["dropped"] += 1
            _bump(census["dropped_by_reason"], res.reason)
            dropped.append({**_excl(ev, facts, res.reason), "fold": fold})
            continue
        if res.status == "EXCLUDED":
            census["excluded"] += 1
            _bump(census["excluded_by_reason"], res.reason)
            _bump_fold(census["excluded_by_fold"], fold)
            excluded.append({**_excl(ev, facts, res.reason), "fold": fold,
                             "ca_detail": res.ca_detail})
            continue
        census["booked"] += 1
        _bump_fold(census["booked_by_fold"], fold)
        _bump(census["booked_by_stratum"], facts.stratum)
        if res.delisting_exit:
            census["delisting_exits"] += 1
        if res.direction == 0:
            census["flat_direction"] += 1
        records.append({
            "event_id": f"EMV1-A1:{ev['cik']}:{ev['acceptance_utc']}",
            "cik": ev["cik"],
            "ticker": ev["ticker"],
            "form": ev["form"],
            "acceptance_utc": ev["acceptance_utc"],
            "stratum": facts.stratum,
            "direction_session": res.direction_session,
            "direction": res.direction,
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
        })

    records.sort(key=lambda r: r["event_id"])
    return BookRun(records=records, excluded=excluded, dropped=dropped, census=census)


def _excl(ev: dict, facts, reason: str) -> dict:
    return {
        "event_id": f"EMV1-A1:{ev['cik']}:{ev['acceptance_utc']}",
        "cik": ev["cik"],
        "ticker": ev["ticker"],
        "form": ev["form"],
        "acceptance_utc": ev["acceptance_utc"],
        "stratum": facts.stratum,
        "reason": reason,
    }


def _bump(d: dict, k: str) -> None:
    d[k] = d.get(k, 0) + 1


def _bump_fold(d: dict, fold: str) -> None:
    d[fold] = d.get(fold, 0) + 1
