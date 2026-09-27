"""E2/E3/E4 — arm construction for A1 and A2 (arms + neighbours + controls).

Arms (G3_FREEZE, budget 6 scored cells max):
  A1 anchor H=5  unmonitored S1uS3uS4 weekday + weekend bucket
  A1 N1    H=10  same event set
  A1 N2    H=5   monitored S2 weekday only
  A2 anchor H=10 all qualifying issuer-days, LONG at next open
  A2 N1    H=20  same event set
  A2 N2    H=10  cluster-conditioned (>=2 distinct insiders, same issuer-day)
Controls (re-evaluations, not trials):
  DATEONLY (both families), PERMUTED-ACCEPTANCE x3 draws, CLOCK-ONLY shadow,
  VALUE/DATE-MATCHED no-event placebo (A2).
"""
from __future__ import annotations

import random
from typing import Dict, List, Optional, Tuple

from . import config as C
from . import clock
from .book import build_decision, resolve_direction_entry
from .panel import Panel

ARM_DEFS = {
    # arm_id: (family, hold, membership)
    "A1-ANCHOR": (C.FAMILY_A1, C.A1_HOLD_ANCHOR, "unmonitored"),
    "A1-N1":     (C.FAMILY_A1, C.A1_HOLD_N1, "unmonitored"),
    "A1-N2":     (C.FAMILY_A1, C.A1_HOLD_ANCHOR, "monitored_s2"),
    "A2-ANCHOR": (C.FAMILY_A2, C.A2_HOLD_ANCHOR, "all"),
    "A2-N1":     (C.FAMILY_A2, C.A2_HOLD_N1, "all"),
    "A2-N2":     (C.FAMILY_A2, C.A2_HOLD_ANCHOR, "cluster"),
}


def a1_bucket(stratum: str, is_weekend: bool) -> Optional[str]:
    """Anchor membership bucket, or None if not in the unmonitored set.

    r3 AMB-1 CANONICAL: weekend acceptances ARE anchor members of the
    unmonitored set S1∪S3∪S4∪WKND — stratum label `WKND` ("separate
    bucket" is a recording label, not an exclusion).
    """
    if is_weekend:
        return "WKND"
    if stratum in ("S1", "S3", "S4"):
        return stratum
    return None


def build_a1_arms(
    events: List[dict],
    panel: Panel,
    corp_actions: dict,
    control_variant: str = "PRIMARY",
    draws: Optional[Dict[int, List[dict]]] = None,
    n4: Optional[dict] = None,
) -> Tuple[List[dict], List[dict]]:
    """A1 decision records + exclusions for all arms (and optional permuted draws)."""
    records: List[dict] = []
    exclusions: List[dict] = []
    for ev in events:
        instant_utc = clock.parse_acceptance_utc(ev["acceptance_utc"])
        et, off = clock.to_et(instant_utc)
        stratum, is_weekend = clock.stratum_of(et)
        bucket = a1_bucket(stratum, is_weekend)
        tickers = _ticker_risk_flags(ev, n4)
        for arm_id, (family, hold, membership) in ARM_DEFS.items():
            if family != C.FAMILY_A1:
                continue
            if membership == "unmonitored" and bucket is None:
                continue
            if membership == "monitored_s2" and (is_weekend or stratum != "S2"):
                continue
            arm_bucket = bucket if membership == "unmonitored" else "S2"
            # r3 AMB-1: weekend members carry stratum label WKND
            rec_stratum = "WKND" if is_weekend else stratum
            rec, exc = build_decision(
                event_id=f"{arm_id}:{ev['cik']}:{ev['acceptance_utc']}:{ev['accession']}",
                family_id=family, arm_id=arm_id,
                cik=ev["cik"], ticker=ev["ticker"], form=ev["form"],
                acceptance_utc=ev["acceptance_utc"],
                instant_et=et, hold_sessions=hold,
                panel=panel, corp_actions=corp_actions,
                stratum=rec_stratum, bucket=arm_bucket, is_weekend=is_weekend,
                control_variant=control_variant,
                ticker_reuse_risk=any(tickers.values()) if tickers else False,
            )
            if rec:
                records.append(rec)
            elif exc:
                exc["arm_id"] = arm_id
                exclusions.append(exc)
    # permuted-acceptance placebo draws (control machinery)
    if draws:
        for draw, pevents in draws.items():
            for ev in pevents:
                instant_utc = clock.parse_acceptance_utc(ev["acceptance_utc"])
                et, off = clock.to_et(instant_utc)
                stratum, is_weekend = clock.stratum_of(et)
                bucket = a1_bucket(stratum, is_weekend)
                if bucket is None:
                    continue
                rec, exc = build_decision(
                    event_id=f"A1-ANCHOR-PERM{draw}:{ev['cik']}:{ev['acceptance_utc']}:{ev['accession']}",
                    family_id=C.FAMILY_A1, arm_id="A1-ANCHOR-PERM",
                    cik=ev["cik"], ticker=ev["ticker"], form=ev["form"],
                    acceptance_utc=ev["acceptance_utc"],
                    instant_et=et, hold_sessions=C.A1_HOLD_ANCHOR,
                    panel=panel, corp_actions=corp_actions,
                    stratum="WKND" if is_weekend else stratum, bucket=bucket,
                    is_weekend=is_weekend,
                    control_variant="PERMUTED_ACCEPTANCE", draw=draw,
                )
                if rec:
                    records.append(rec)
                elif exc:
                    exc["arm_id"] = "A1-ANCHOR-PERM"
                    exclusions.append(exc)
    return records, exclusions


def build_a2_arms(
    events: List[dict],       # issuer-day dicts from a2_inputs
    ticker_by_cik: Dict[str, str],
    panel: Panel,
    corp_actions: dict,
    n4: Optional[dict] = None,
) -> Tuple[List[dict], List[dict]]:
    records: List[dict] = []
    exclusions: List[dict] = []
    for ev in events:
        cik = ev["cik"]
        ticker = ticker_by_cik.get(cik)
        if ticker is None:
            for arm_id in ("A2-ANCHOR", "A2-N1", "A2-N2"):
                exclusions.append({"event_id": f"{arm_id}:{cik}:{ev['day']}",
                                   "reason": "NO_TICKER_FOR_CIK", "fold": clock.fold_of_et(ev["earliest_acceptance"]),
                                   "ticker": None, "cik": cik, "arm_id": arm_id})
            continue
        instant_utc = clock.parse_acceptance_utc(ev["earliest_acceptance"])
        et, off = clock.to_et(instant_utc)
        stratum, is_weekend = clock.stratum_of(et)
        reuse = bool(n4 and n4.get(cik, {}).get("ticker_reuse_risk", False))
        for arm_id, (family, hold, membership) in ARM_DEFS.items():
            if family != C.FAMILY_A2:
                continue
            if membership == "cluster" and not ev["cluster"]:
                continue
            rec, exc = build_decision(
                event_id=f"{arm_id}:{cik}:{ev['day']}",
                family_id=family, arm_id=arm_id,
                cik=cik, ticker=ticker, form="4",
                acceptance_utc=ev["earliest_acceptance"],
                instant_et=et, hold_sessions=hold,
                panel=panel, corp_actions=corp_actions,
                stratum=stratum, bucket="ISSUER-DAY", is_weekend=is_weekend,
                direction_override="LONG",
                ticker_reuse_risk=reuse,
            )
            if rec:
                rec["buy_value_usd"] = round(ev["buy_value_usd"], 2)
                rec["n_insiders"] = ev["n_insiders"]
                rec["cluster"] = ev["cluster"]
                records.append(rec)
            elif exc:
                exc["arm_id"] = arm_id
                exclusions.append(exc)
    return records, exclusions


def _ticker_risk_flags(ev: dict, n4: Optional[dict]):
    if n4 is None:
        return None
    row = n4.get(ev["cik"], {})
    return {ev["cik"]: bool(row.get("ticker_reuse_risk", False))}


# ------------------------------------------------------------- controls ----
def build_a1_dateonly(
    events: List[dict], panel: Panel, corp_actions: dict
) -> Tuple[List[dict], List[dict]]:
    """Date-only control: filing-date clock, strata removed."""
    records, exclusions = [], []
    for ev in events:
        import datetime as _dt
        fd = _dt.datetime.combine(
            _dt.date.fromisoformat(ev["filing_date"]), _dt.time(0, 0), tzinfo=clock.ET)
        for arm_id, hold in (("A1-DATEONLY-ANCHOR", C.A1_HOLD_ANCHOR),
                             ("A1-DATEONLY-N1", C.A1_HOLD_N1)):
            rec, exc = build_decision(
                event_id=f"{arm_id}:{ev['cik']}:{ev['acceptance_utc']}:{ev['accession']}",
                family_id=C.FAMILY_A1, arm_id=arm_id,
                cik=ev["cik"], ticker=ev["ticker"], form=ev["form"],
                acceptance_utc=ev["acceptance_utc"],
                instant_et=fd, hold_sessions=hold,
                panel=panel, corp_actions=corp_actions,
                stratum=None, bucket="DATEONLY", is_weekend=False,
                control_variant="DATE_ONLY",
            )
            if rec:
                records.append(rec)
            elif exc:
                exc["arm_id"] = arm_id
                exclusions.append(exc)
    return records, exclusions


def build_a2_dateonly(
    events: List[dict], ticker_by_cik: Dict[str, str], panel: Panel, corp_actions: dict
) -> Tuple[List[dict], List[dict]]:
    records, exclusions = [], []
    for ev in events:
        ticker = ticker_by_cik.get(ev["cik"])
        if ticker is None:
            continue
        import datetime as _dt
        fd = _dt.datetime.combine(
            _dt.date.fromisoformat(ev["filing_date"]), _dt.time(0, 0), tzinfo=clock.ET)
        rec, exc = build_decision(
            event_id=f"A2-DATEONLY-ANCHOR:{ev['cik']}:{ev['day']}",
            family_id=C.FAMILY_A2, arm_id="A2-DATEONLY-ANCHOR",
            cik=ev["cik"], ticker=ticker, form="4",
            acceptance_utc=ev["earliest_acceptance"],
            instant_et=fd, hold_sessions=C.A2_HOLD_ANCHOR,
            panel=panel, corp_actions=corp_actions,
            stratum=None, bucket="DATEONLY", is_weekend=False,
            control_variant="DATE_ONLY", direction_override="LONG",
        )
        if rec:
            rec["buy_value_usd"] = round(ev["buy_value_usd"], 2)
            rec["n_insiders"] = ev["n_insiders"]
            rec["cluster"] = ev["cluster"]
            records.append(rec)
        elif exc:
            exc["arm_id"] = "A2-DATEONLY-ANCHOR"
            exclusions.append(exc)
    return records, exclusions


def permute_a1_acceptances(
    events: List[dict], seed: int, n_draws: int
) -> Dict[int, List[dict]]:
    """Shuffle acceptance stamps within issuer x form x year (keeps event set,
    moves the clock). Deterministic per draw."""
    out: Dict[int, List[dict]] = {}
    for draw in range(1, n_draws + 1):
        rng = random.Random(seed + draw)
        groups: Dict[Tuple, List[str]] = {}
        for ev in events:
            year = ev["acceptance_utc"][:4]
            groups.setdefault((ev["cik"], ev["form"], year), []).append(ev["acceptance_utc"])
        stamps = {k: sorted(v) for k, v in groups.items()}
        permuted = {k: v[:] for k, v in stamps.items()}
        for k, v in permuted.items():
            rng.shuffle(v)
        mapping = {k: dict(zip(stamps[k], permuted[k])) for k in stamps}
        pevents = []
        for ev in events:
            year = ev["acceptance_utc"][:4]
            new_stamp = mapping[(ev["cik"], ev["form"], year)][ev["acceptance_utc"]]
            pevents.append({**ev, "acceptance_utc": new_stamp})
        out[draw] = pevents
    return out


def clock_only_shadow_a1(
    events: List[dict], panel: Panel, corp_actions: dict, seed: int
) -> Tuple[List[dict], List[dict]]:
    """Stratum conditioning with the event payload removed: sample
    (issuer, session) pairs uniformly at the same per-bucket rates; apply the
    anchor rule (direction from the sampled session's close-open, entry next
    open, H=5)."""
    rng = random.Random(seed)
    bucket_counts: Dict[str, int] = {}
    for ev in events:
        et, _ = clock.to_et(clock.parse_acceptance_utc(ev["acceptance_utc"]))
        stratum, is_weekend = clock.stratum_of(et)
        bucket = a1_bucket(stratum, is_weekend)
        if bucket:
            bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1
    # issuer->panel index for uniform session sampling
    tickers = sorted(panel.names)
    records, exclusions = [], []
    seq = 0
    for bucket, n in sorted(bucket_counts.items()):
        stratum = "WKND" if bucket == "WKND" else bucket.split("+")[-1]
        is_weekend = bucket == "WKND"
        made = 0
        while made < n:
            seq += 1
            t = tickers[rng.randrange(len(tickers))]
            ns = panel.names[t]
            if len(ns) < 3:
                continue
            i = rng.randrange(len(ns) - 1)
            # the sampled session acts as the DIRECTION session: the event
            # instant is placed pre-open of that session date
            import datetime as _dt
            d = _dt.date.fromisoformat(ns.dates[i])
            instant = _dt.datetime.combine(d, _dt.time(9, 0), tzinfo=clock.ET)
            if is_weekend or stratum != "S2":
                pass
            rec, exc = build_decision(
                event_id=f"A1-SHADOW:{t}:{ns.dates[i]}:{seq}",
                family_id=C.FAMILY_A1, arm_id="A1-CLOCK-SHADOW",
                cik="", ticker=t, form="SHADOW",
                acceptance_utc=instant.isoformat(),
                instant_et=instant, hold_sessions=C.A1_HOLD_ANCHOR,
                panel=panel, corp_actions=corp_actions,
                stratum=stratum, bucket=bucket, is_weekend=is_weekend,
                control_variant="CLOCK_ONLY_SHADOW",
            )
            if rec:
                records.append(rec)
                made += 1
            elif exc:
                exc["arm_id"] = "A1-CLOCK-SHADOW"
                exclusions.append(exc)
                made += 1  # count attempts toward the rate to avoid infinite loops
    return records, exclusions


def value_date_matched_placebo_a2(
    events: List[dict], ticker_by_cik: Dict[str, str], panel: Panel,
    corp_actions: dict, seed: int,
) -> Tuple[List[dict], List[dict]]:
    """Random issuer-days matched on cohort x date-range, same count as A2
    events; same trading rule (LONG at next open, H=10)."""
    rng = random.Random(seed)
    issuers = sorted({ticker_by_cik[e["cik"]] for e in events if e["cik"] in ticker_by_cik})
    days = [e["day"] for e in events]
    lo, hi = min(days), max(days)
    import datetime as _dt
    d0 = _dt.date.fromisoformat(lo)
    d1 = _dt.date.fromisoformat(hi)
    span = (d1 - d0).days
    records, exclusions = [], []
    made = 0
    attempts = 0
    n_target = len(events)
    while made < n_target and attempts < n_target * 30:
        attempts += 1
        t = issuers[rng.randrange(len(issuers))]
        ns = panel.names.get(t)
        if ns is None or len(ns) < 3:
            continue
        i = rng.randrange(len(ns) - 1)
        d = _dt.date.fromisoformat(ns.dates[i])
        if not (d0 <= d <= d1):
            continue
        instant = _dt.datetime.combine(d, _dt.time(16, 0), tzinfo=clock.ET)
        rec, exc = build_decision(
            event_id=f"A2-PLACEBO:{t}:{ns.dates[i]}:{attempts}",
            family_id=C.FAMILY_A2, arm_id="A2-NOEVENT-PLACEBO",
            cik="", ticker=t, form="PLACEBO",
            acceptance_utc=instant.isoformat(),
            instant_et=instant, hold_sessions=C.A2_HOLD_ANCHOR,
            panel=panel, corp_actions=corp_actions,
            stratum=None, bucket="PLACEBO", is_weekend=False,
            control_variant="VALUE_DATE_MATCHED_PLACEBO",
            direction_override="LONG",
        )
        if rec:
            records.append(rec)
            made += 1
        elif exc:
            exc["arm_id"] = "A2-NOEVENT-PLACEBO"
            exclusions.append(exc)
    return records, exclusions
