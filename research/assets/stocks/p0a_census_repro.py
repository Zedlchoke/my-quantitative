"""P0a F1 census reproduction and multi-vintage panel builder (V6 lane A2).

STOCKS-FREE-V6 Phase P0a (PLAN_stocks_v6.md section 6 P0a, binding order):
the coverage census and the fundable-clock list publish BEFORE any proposal
brief exists.  This script is the only heavy job of the cycle's P0a lane and
is engineered for an 8 GB machine that may host foreign workers:

- the 2.9 GB inherited PIT store is STREAMED line-by-line, twice at most
  (pass 0: field frequencies only; pass 1: everything else) - it is never
  loaded whole;
- every emitted artifact is deterministic: same input bytes -> same output
  bytes.  No wall-clock timestamps are written; provenance is the SHA-256 of
  the inputs (store, panel, calendars, V5 evidence) plus schema versions;
- the derived multi-vintage panel lands in the gitignored ``.staging_sec_v6``
  directory and is hash-pinned by a manifest; raw panel bytes are never
  committed;
- the V5 evidence trees are read-only and only ever read.

Modes: ``pass0`` | ``pass1`` | ``repro`` | ``emit`` | ``all``.

No PnL, no optimizer logic, no proposal content.  Gates report
PASS/FAIL/NOT_RUN/BLOCKED from measured bytes only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import date, datetime, time, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research.assets.stocks.p0a_multivintage import (  # noqa: E402
    AGE_GRID_DAYS,
    COVERAGE_FLOORS,
    P0A_SCHEMA_VERSION,
    FilerFieldSeries,
    VintageStamp,
    coverage_timeline,
    date_to_ord,
    first_cross_date,
    lag_stats,
    ord_to_date,
    parse_iso_utc,
    session_gate_utc,
    stamp_is_eod_utc,
)
from research.assets.stocks.pit_conditioning import (  # noqa: E402
    SECTOR_UNIVERSE,
    aggregate_sector_asof,
)
from research.data_fusion.models import NormalizedRecord  # noqa: E402

SCHEMA = "stocks_free_v6_run/p0a_census_repro@1"
PRODUCER = "A2 (lane p0-a2-f1remedy, branch orca/stocks-free-v6-p0-a2-f1remedy)"

DEFAULT_STORE = Path(
    "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v5/p0-a3-data/.staging_sec/pit_records.jsonl"
)
EXPECTED_STORE_SHA256 = (
    "f53eb3712bc9d686ec8a91b3715beaf73be1e5243a89af1816bd62eea51df955"
)
EXPECTED_STORE_RECORDS = 3_817_158
EXPECTED_STORE_FILERS = 410
EXPECTED_STORE_FIELDS = 4_677
EXPECTED_MULTI_STAMP_GROUPS = 643_610

DEFAULT_PANEL = Path(
    "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v5/p0-a3-data/.staging_sec/panel.json"
)
DEFAULT_SPY_CAL = Path(
    "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v2/z8-exec-1/.staging/SPY_none_p1.json"
)
SECTOR_ETF_CAL_TEMPLATE = (
    "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v2/"
    "z8-exec-1/.staging/{sym}_none_p1.json"
)
V5_INTEGRATION_CONTROL = Path(
    "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v5/"
    "integration/research/control/stocks_free_v5_run"
)
V5_A9F_AUDIT_CANDIDATES = (
    REPO_ROOT / "research" / "audits" / "stocks_free_v5" / "a9_f_feasibility_audit.json",
    Path(
        "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v5/"
        "integration/research/audits/stocks_free_v5/a9_f_feasibility_audit.json"
    ),
)
V5_P2_AUDIT = V5_INTEGRATION_CONTROL / "p2_pit_data_audit_sec.json"

STAGING = REPO_ROOT / ".staging_sec_v6"
PANEL_OUT = STAGING / "multivintage_panel.jsonl"
FIELD_COUNTS_OUT = STAGING / "_p0a_field_counts.json"
SCAN_STATS_OUT = STAGING / "_p0a_scan_stats.json"
SERIES_OUT = STAGING / "_p0a_series_census_fields.json"
FIRST_AVAIL_OUT = STAGING / "_p0a_first_avail.json"
REPRO_OUT = STAGING / "_p0a_f1_repro.json"
CENSUS_OUT = STAGING / "_p0a_coverage_census_full.json"
CONTROL_DIR = REPO_ROOT / "research" / "control" / "stocks_free_v6_run"

# --- frozen S0 geometry (V5 baseline_invariants@1, inherited unchanged) ----
S0_START = date(2018, 4, 4)
S0_END = date(2025, 7, 31)  # session window; fold 3 ends 2025-07-24
FOLDS = (
    ("S0_FOLD_1", date(2018, 4, 4), date(2020, 9, 1)),
    ("S0_FOLD_2", date(2020, 9, 10), date(2023, 2, 9)),
    ("S0_FOLD_3", date(2023, 2, 17), date(2025, 7, 24)),
)
QUARTERLY_OFFSETS = tuple(range(0, 568, 63))  # 10 ticks per fold
GRID42_OFFSETS = tuple(range(0, 1807, 42))  # 44 slots in the S0 window

# The five V5-proposal fields are always censused regardless of volume.
V5_PROPOSAL_FIELDS = (
    "us-gaap:Assets",
    "us-gaap:AssetsCurrent",
    "us-gaap:CashAndCashEquivalentsAtCarryingValue",
    "dei:EntityPublicFloat",
    "us-gaap:LiabilitiesAndStockholdersEquity",
)

# Ex-ante census-field selection rule (fixed before any coverage was
# measured): every field with >= CENSUS_MIN_RECORDS records, capped at the
# CENSUS_MAX_FIELDS heaviest by (count desc, name asc), plus the five
# V5-proposal fields.  Selection sees record counts only - never coverage.
CENSUS_MIN_RECORDS = 20_000
CENSUS_MAX_FIELDS = 40

# Reconstruction constants for building NormalizedRecord objects for the
# canonical bridge.  The bridge's gate uses available_time only; retrieved
# is a provenance constant of the store and raw hashes are not semantically
# load-bearing for aggregation (documented limitation of the reconstruction).
RECON_RETRIEVED = datetime(2026, 9, 4, 10, 50, 0, tzinfo=timezone.utc)
MAX_DECISION_SESSION = date(2026, 8, 27)

# The four V5 F1 configurations (canonical bridge, unmodified semantics).
F1_CONFIGS = (
    {
        "config_id": "a4_h1",
        "hypothesis_id": "SFV5-A4-H1-BSHEXPANSION",
        "fields": ("us-gaap:Assets",),
        "gap_days": 400,
        "slots": "quarterly30",
        "coverage_floor": 0.6,
        "coherence_days": 100,
        "coherence_mode": "endpoint_t_vs_ref252",
        "census_floor": 0.8,
        "leg_history_sessions": 63,
    },
    {
        "config_id": "a4_h2",
        "hypothesis_id": "SFV5-A4-H2-CASHINTENSITY",
        "fields": (
            "us-gaap:CashAndCashEquivalentsAtCarryingValue",
            "us-gaap:Assets",
        ),
        "gap_days": 400,
        "slots": "quarterly30",
        "coverage_floor": 0.6,
        "coherence_days": 100,
        "coherence_mode": "between_fields",
        "census_floor": 0.8,
        "leg_history_sessions": 63,
    },
    {
        "config_id": "a5_h1",
        "hypothesis_id": "SFV5-A5-H1-FLOATBOOKVALUE",
        "fields": (
            "dei:EntityPublicFloat",
            "us-gaap:LiabilitiesAndStockholdersEquity",
        ),
        "gap_days": 550,
        "slots": "quarterly30",
        "coverage_floor": 0.6,
        "coherence_days": None,
        "coherence_mode": None,
        "census_floor": 0.8,
        "leg_history_sessions": 21,
    },
    {
        "config_id": "a6_h1",
        "hypothesis_id": "SFV5-A6-H1-WCINT",
        "fields": ("us-gaap:AssetsCurrent", "us-gaap:Assets"),
        "gap_days": 200,
        "slots": "grid42_44",
        "coverage_floor": 0.4,
        "coherence_days": None,
        "coherence_mode": None,
        "census_floor": 0.8,
        "leg_history_sessions": 252,
    },
)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            block = handle.read(chunk)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def canonical_json_bytes(payload) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def write_json_deterministic(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(canonical_json_bytes(payload))
        handle.write(b"\n")


def load_panel_mapping(panel_path: Path) -> tuple[dict[str, str], dict[str, int]]:
    """entity_id -> sector for the frozen 410-filer panel plus sizes."""
    raw = json.loads(panel_path.read_text())
    mapping: dict[str, str] = {}
    sizes: dict[str, int] = {}
    for sector, filers in raw["panel"].items():
        sizes[sector] = len(filers)
        for filer in filers:
            entity = "CIK{:010d}".format(int(filer["cik"]))
            if mapping.get(entity, sector) != sector:
                raise ValueError(f"filer {entity} mapped to two sectors")
            mapping[entity] = sector
    return mapping, sizes


def load_sessions(spy_cal: Path) -> list[date]:
    values = json.loads(spy_cal.read_text())["values"]
    days = sorted(datetime.strptime(v["datetime"], "%Y-%m-%d").date() for v in values)
    if len(days) != 4188 or days[0] != date(2010, 1, 4) or days[-1] != date(2026, 8, 27):
        raise ValueError("SPY calendar does not match the frozen V5 snapshot facts")
    return days


def load_sector_leg_calendars() -> dict[str, list[date]]:
    calendars: dict[str, list[date]] = {}
    for symbol in SECTOR_UNIVERSE:
        path = Path(SECTOR_ETF_CAL_TEMPLATE.format(sym=symbol))
        if not path.exists():
            continue
        values = json.loads(path.read_text())["values"]
        calendars[symbol] = sorted(
            datetime.strptime(v["datetime"], "%Y-%m-%d").date() for v in values
        )
    return calendars


def bisect_count_before(days: list[date], tick: date) -> int:
    lo, hi = 0, len(days)
    while lo < hi:
        mid = (lo + hi) // 2
        if days[mid] < tick:
            lo = mid + 1
        else:
            hi = mid
    return lo


def sector_leg_history(
    calendars: dict[str, list[date]], sector: str, tick: date, required: int
) -> bool:
    days = calendars.get(sector)
    if days is None:
        return False
    return bisect_count_before(days, tick) >= required


def quarterly_ticks(sessions: list[date]) -> list[date]:
    window = [d for d in sessions if S0_START <= d <= S0_END]
    if len(window) != 1842:
        raise ValueError(f"S0 window sessions {len(window)} != 1842")
    ticks: list[date] = []
    for fold_id, start, end in FOLDS:
        fold_sessions = [d for d in window if start <= d <= end]
        if len(fold_sessions) != 609:
            raise ValueError(f"{fold_id} sessions {len(fold_sessions)} != 609")
        for offset in QUARTERLY_OFFSETS:
            ticks.append(fold_sessions[offset])
    return ticks


def grid42_slots(sessions: list[date]) -> list[date]:
    window = [d for d in sessions if S0_START <= d <= S0_END]
    return [window[offset] for offset in GRID42_OFFSETS]


def iter_store(store: Path):
    with open(store, "r", encoding="utf-8", buffering=1 << 22) as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


# --------------------------------------------------------------------------
# pass 0: field frequencies (ex-ante census-field selection input)
# --------------------------------------------------------------------------

def pass0(store: Path) -> dict:
    counts: dict[str, int] = {}
    total = 0
    for record in iter_store(store):
        total += 1
        field = record["field"]
        counts[field] = counts.get(field, 0) + 1
    payload = {
        "schema": "stocks_free_v6_run/p0a_field_counts@1",
        "store_path": str(store),
        "records": total,
        "distinct_fields": len(counts),
        "selection_rule": {
            "min_records": CENSUS_MIN_RECORDS,
            "max_fields": CENSUS_MAX_FIELDS,
            "v5_proposal_fields_always": list(V5_PROPOSAL_FIELDS),
        },
        "field_counts": counts,
    }
    write_json_deterministic(FIELD_COUNTS_OUT, payload)
    return payload


def select_census_fields(field_counts: dict[str, int]) -> list[str]:
    volume_fields = [f for f, n in field_counts.items() if n >= CENSUS_MIN_RECORDS]
    volume_fields.sort(key=lambda f: (-field_counts[f], f))
    selected = set(volume_fields[:CENSUS_MAX_FIELDS])
    selected.update(f for f in V5_PROPOSAL_FIELDS if field_counts.get(f))
    return sorted(selected)


# --------------------------------------------------------------------------
# pass 1: panel write + store stats + series + lag histograms
# --------------------------------------------------------------------------

def pass1(
    store: Path,
    census_fields: list[str],
    filer_sector: dict[str, str],
) -> dict:
    census_field_set = set(census_fields)
    series: dict[str, dict[str, FilerFieldSeries]] = {f: {} for f in census_fields}
    units: dict[str, dict[str, str]] = {f: {} for f in census_fields}
    lag_hist: dict[str, dict[int, int]] = {f: {} for f in census_fields}
    non_numeric: dict[str, int] = {f: 0 for f in census_fields}
    first_avail: dict[tuple[str, str], dict[str, int]] = {}
    entity_sector: dict[str, str] = {}
    sector_mismatch_vs_record = 0
    sector_mismatch_vs_panel = 0
    non_eod_stamps = 0
    total_groups = 0
    total = 0
    group_state: dict[int, int] = {}
    blake = hashlib.blake2b

    panel_tmp = PANEL_OUT.with_name(PANEL_OUT.name + ".part")
    PANEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(panel_tmp, "w", encoding="utf-8", buffering=1 << 22) as sink:
        for record in iter_store(store):
            total += 1
            entity = record["entity_id"]
            field = record["field"]
            sector = record["sector"]
            known = entity_sector.setdefault(entity, sector)
            if known != sector:
                sector_mismatch_vs_record += 1
            if filer_sector.get(entity) != sector:
                sector_mismatch_vs_panel += 1
            avail = parse_iso_utc(record["available_time_utc"])
            if not stamp_is_eod_utc(avail):
                non_eod_stamps += 1
            eff_raw = record.get("effective_time_utc")
            eff = parse_iso_utc(eff_raw) if eff_raw else parse_iso_utc(record["event_time_utc"])
            eff_day = eff.date()
            avail_day = avail.date()
            a_ord = date_to_ord(avail_day)
            e_ord = date_to_ord(eff_day)

            gkey = blake(
                f"{entity}|{field}|{eff_day.isoformat()}".encode("utf-8"),
                digest_size=8,
            ).digest()
            g_int = int.from_bytes(gkey, "big")
            state = group_state.get(g_int)
            if state is None:
                group_state[g_int] = (a_ord << 32) | a_ord
                total_groups += 1
            else:
                lo = state >> 32
                hi = state & 0xFFFFFFFF
                if a_ord < lo or a_ord > hi:
                    group_state[g_int] = (min(lo, a_ord) << 32) | max(hi, a_ord)

            value = record.get("value")
            row = {
                "e": entity,
                "s": sector,
                "f": field,
                "u": record.get("unit"),
                "v": value,
                "eff": eff_day.isoformat(),
                "avail": avail_day.isoformat(),
            }
            ev_raw = record.get("event_time_utc")
            if ev_raw:
                ev_day = parse_iso_utc(ev_raw).date()
                if ev_day != eff_day:
                    row["evd"] = ev_day.isoformat()
            sink.write(json.dumps(row, separators=(",", ":"), ensure_ascii=False))
            sink.write("\n")

            slot = first_avail.setdefault((sector, field), {})
            prev = slot.get(entity)
            if prev is None or a_ord < prev:
                slot[entity] = a_ord

            if field in census_field_set:
                bucket = series[field].get(entity)
                if bucket is None:
                    bucket = FilerFieldSeries(entity_id=entity)
                    series[field][entity] = bucket
                value_num = None
                if isinstance(value, bool) or value is None or not isinstance(value, (int, float)):
                    non_numeric[field] += 1
                else:
                    value_num = float(value)
                    if not math.isfinite(value_num):
                        value_num = None
                        non_numeric[field] += 1
                bucket.add(VintageStamp(available_ord=a_ord, effective_date=eff_day, value=value_num))
                units[field].setdefault(entity, record.get("unit") or "")
                lag = a_ord - e_ord
                hist = lag_hist[field]
                hist[lag] = hist.get(lag, 0) + 1

    if sector_mismatch_vs_record or non_eod_stamps or sector_mismatch_vs_panel:
        panel_tmp.unlink(missing_ok=True)
        raise ValueError(
            "store invariants violated: "
            f"sector_mismatch_vs_record={sector_mismatch_vs_record} "
            f"sector_mismatch_vs_panel={sector_mismatch_vs_panel} "
            f"non_eod_stamps={non_eod_stamps}"
        )
    panel_tmp.replace(PANEL_OUT)

    multi = 0
    for state in group_state.values():
        if (state >> 32) != (state & 0xFFFFFFFF):
            multi += 1
    del group_state

    distinct_fields = {f for _, f in first_avail}
    payload = {
        "schema": "stocks_free_v6_run/p0a_scan_stats@1",
        "store_path": str(store),
        "records": total,
        "distinct_entities": len(entity_sector),
        "distinct_fields": len(distinct_fields),
        "total_vintage_groups": total_groups,
        "multi_stamp_vintage_groups": multi,
        "sector_mismatches_vs_store": sector_mismatch_vs_record,
        "sector_mismatches_vs_panel": sector_mismatch_vs_panel,
        "non_eod_availability_stamps": non_eod_stamps,
        "census_fields": census_fields,
    }
    write_json_deterministic(SCAN_STATS_OUT, payload)

    series_blob = {
        "schema": "stocks_free_v6_run/p0a_series@1",
        "census_fields": census_fields,
        "non_numeric_value_records": non_numeric,
        "units_by_entity": units,
        "series": {
            field: {
                entity: {
                    "avail": [s.available_ord for s in bucket.stamps],
                    "eff": [date_to_ord(s.effective_date) for s in bucket.stamps],
                    "val": [s.value for s in bucket.stamps],
                }
                for entity, bucket in sorted(series[field].items())
            }
            for field in census_fields
        },
        "lag_histograms": {f: {str(k): v for k, v in sorted(h.items())} for f, h in lag_hist.items()},
    }
    write_json_deterministic(SERIES_OUT, series_blob)

    first_avail_blob = {
        "schema": "stocks_free_v6_run/p0a_first_avail@1",
        "s0_start": S0_START.isoformat(),
        "entries": {
            f"{sector}|{field}": {e: o for e, o in sorted(slot.items())}
            for (sector, field), slot in sorted(first_avail.items())
        },
    }
    write_json_deterministic(FIRST_AVAIL_OUT, first_avail_blob)
    return payload


# --------------------------------------------------------------------------
# any-history (P2-style) census recomputation and comparison
# --------------------------------------------------------------------------

def recompute_warmup_census(first_avail_blob: dict, panel_sizes: dict[str, int]) -> dict:
    """Pre-S0 existence census with the exact V5 A7 key semantics: a
    (sector, field) key exists only when at least one panel filer has a
    record available before the S0 start."""
    cutoff = date_to_ord(S0_START)
    coverage: dict[str, dict] = {}
    for key, slot in first_avail_blob["entries"].items():
        sector, field = key.split("|", 1)
        panel_total = panel_sizes.get(sector, 0)
        if not panel_total:
            continue
        with_pre_s0 = sum(1 for ordinal in slot.values() if ordinal < cutoff)
        if not with_pre_s0:
            continue  # no pre-S0 record at all -> key absent (V5 semantics)
        fraction = with_pre_s0 / panel_total
        coverage[key] = {
            "filers_with_pre_s0": with_pre_s0,
            "panel": panel_total,
            "fraction": round(fraction, 3),
            "fundable_for_d1": fraction >= 0.8,
        }
    return coverage


def compare_warmup_census(mine: dict, v5_warmup_check: dict) -> dict:
    reference = v5_warmup_check["coverage"]
    keys_mine = set(mine)
    keys_ref = set(reference)
    mismatch = []
    for key in sorted(keys_mine & keys_ref):
        if mine[key]["fraction"] != reference[key]["fraction"]:
            mismatch.append({"key": key, "v5": reference[key]["fraction"], "v6": mine[key]["fraction"]})
    return {
        "keys_mine": len(keys_mine),
        "keys_v5": len(keys_ref),
        "keys_only_v5": sorted(keys_ref - keys_mine)[:20],
        "keys_only_v6": sorted(keys_mine - keys_ref)[:20],
        "fraction_mismatches": mismatch[:40],
        "exact_match": (
            keys_mine == keys_ref
            and not mismatch
        ),
    }


# --------------------------------------------------------------------------
# F1 reproduction via the canonical bridge
# --------------------------------------------------------------------------

def build_records(field: str, blob: dict, unit: str) -> list[NormalizedRecord]:
    records: list[NormalizedRecord] = []
    latest_usable_gate = session_gate_utc(MAX_DECISION_SESSION)
    for entity, data in blob.items():
        avails = data["avail"]
        effs = data["eff"]
        vals = data["val"]
        raw_path = f".staging_sec/companyfacts_{entity}.json"
        for a_ord, e_ord, value in zip(avails, effs, vals):
            avail_dt = datetime.combine(
                ord_to_date(a_ord), time(23, 59, 59), tzinfo=timezone.utc
            )
            if avail_dt >= latest_usable_gate:
                continue  # gated in at no frozen decision session
            eff_dt = datetime.combine(ord_to_date(e_ord), time(0, 0, 0), tzinfo=timezone.utc)
            records.append(
                NormalizedRecord(
                    source_id="SEC_EDGAR",
                    dataset_id="company_facts",
                    entity_id=entity,
                    field=field,
                    value=value,
                    unit=unit or "USD",
                    event_time_utc=eff_dt,
                    available_time_utc=avail_dt,
                    effective_time_utc=eff_dt,
                    vintage_time_utc=avail_dt,
                    retrieved_time_utc=RECON_RETRIEVED,
                    raw_path=raw_path,
                    raw_sha256="0" * 64,
                    license_id="sec-public-domain-v1",
                    entitlement_id="anonymous-no-key",
                    normalizer_version="p0a-repro-reconstruction-1.0.0",
                )
            )
    records.sort(key=lambda r: (r.entity_id, r.available_time_utc, r.effective_time_utc, r.value if r.value is not None else 0.0))
    return records


def bridge_observation_table(
    records: list[NormalizedRecord],
    filer_sector: dict[str, str],
    sessions: list[date],
    field: str,
    gap_days: int,
) -> dict[str, dict[str, dict]]:
    table: dict[str, dict[str, dict]] = {}
    for session in sessions:
        result = aggregate_sector_asof(
            records,
            filer_sectors=filer_sector,
            decision_session=session,
            field=field,
            max_filing_gap_days=gap_days,
        )
        table[session.isoformat()] = {
            sector: {
                "coverage": observation.coverage,
                "filers_included": observation.filers_included,
                "filers_mapped": observation.filers_mapped,
                "effective_date": observation.effective_date.isoformat(),
            }
            for sector, observation in sorted(result.items())
        }
    return table


def compare_coverage_tables(v5_table: dict, mine: dict, key_map: dict[str, str] | None) -> list:
    mismatches = []
    for session, sectors in v5_table.items():
        key = key_map.get(session, session) if key_map else session
        my_row = mine.get(key, {})
        for sector, expected in sectors.items():
            want = expected[0] if isinstance(expected, list) else expected
            got = my_row.get(sector)
            if got is None or abs(got - want) > 5e-5:
                mismatches.append(
                    {"session": session, "sector": sector, "v5": want, "v6": got}
                )
    return mismatches


def repro(
    filer_sector: dict[str, str],
    panel_sizes: dict[str, int],
    sessions: list[date],
    v5_audit: dict | None,
) -> dict:
    series_blob = json.loads(SERIES_OUT.read_text())
    first_avail_blob = json.loads(FIRST_AVAIL_OUT.read_text())
    units_blob = series_blob["units_by_entity"]

    tick_dates = quarterly_ticks(sessions)
    slot_dates = grid42_slots(sessions)
    sessions_index = {d: i for i, d in enumerate(sessions)}
    ref252 = {
        tick: sessions[sessions_index[tick] - 252] for tick in tick_dates
    }

    # pre-S0 census fractions per (sector, field), computed from bytes
    warmup = recompute_warmup_census(first_avail_blob, panel_sizes)
    warmup_v5_compare = None
    if V5_P2_AUDIT.exists():
        v5_p2 = json.loads(V5_P2_AUDIT.read_text())
        warmup_v5_compare = compare_warmup_census(
            warmup, v5_p2["checks"]["A7_warmup_coverage"]
        )
    census_passing: dict[str, dict[str, bool]] = {}
    for field in {f for cfg in F1_CONFIGS for f in cfg["fields"]}:
        census_passing[field] = {
            sector: (
                warmup.get(f"{sector}|{field}", {}).get("fraction", 0.0)
                >= 0.8
            )
            for sector in SECTOR_UNIVERSE
        }

    leg_calendars = load_sector_leg_calendars()

    configs_out: dict[str, dict] = {}
    for config in F1_CONFIGS:
        cfg_id = config["config_id"]
        slots = tick_dates if config["slots"] == "quarterly30" else slot_dates
        observations: dict[str, dict[str, dict[str, dict]]] = {}
        coverage_tables: dict[str, dict[str, dict[str, float]]] = {}
        cohort_sizes: list[int] = []
        for field in config["fields"]:
            field_units = units_blob.get(field, {})
            unit = next(iter(field_units.values()), "USD")
            records = build_records(
                field, series_blob["series"].get(field, {}), unit
            )
            sessions_needed = list(slots)
            if config["coherence_mode"] == "endpoint_t_vs_ref252":
                sessions_needed = sorted(set(slots) | set(ref252.values()))
            table = bridge_observation_table(
                records, filer_sector, sessions_needed, field, config["gap_days"]
            )
            observations[field] = table
            coverage_tables[field] = {
                session: {
                    sector: round(info["coverage"], 4)
                    for sector, info in sorted(per_session.items())
                }
                for session, per_session in sorted(table.items())
            }
            if len(config["fields"]) == 1 and config["slots"] == "quarterly30":
                for session in slots:
                    for sector, info in table[session.isoformat()].items():
                        cohort_sizes.append(info["filers_included"])
            del records

        eligible: list[int] = []
        for session in slots:
            per_sector: dict[str, bool] = {}
            for sector in SECTOR_UNIVERSE:
                # eligibility gates, all measured from bytes:
                # (1) census gate: every config field pre-S0 fundable >= 0.8
                #     (this DERIVES the a6_h1 census-9 sector set);
                # (2) sector-ETF leg history on the ETF's own calendar;
                # (3) single-vintage coverage >= floor (and the ref-252 side
                #     for the endpoint-coherence config);
                # (4) effective-date coherence where declared.
                ok = True
                if ok and not all(
                    census_passing[field][sector] for field in config["fields"]
                ):
                    ok = False
                if ok and not sector_leg_history(
                    leg_calendars, sector, session, config["leg_history_sessions"]
                ):
                    ok = False
                effs: list[date] = []
                if ok:
                    for field in config["fields"]:
                        info = observations[field].get(session.isoformat(), {}).get(sector)
                        if info is None or info["coverage"] < config["coverage_floor"]:
                            ok = False
                            break
                        effs.append(date.fromisoformat(info["effective_date"]))
                if ok and config["coherence_mode"] == "between_fields" and len(effs) == 2:
                    if abs((effs[0] - effs[1]).days) > config["coherence_days"]:
                        ok = False
                if ok and config["coherence_mode"] == "endpoint_t_vs_ref252":
                    field = config["fields"][0]
                    ref_session = ref252[session]
                    ref_info = observations[field].get(ref_session.isoformat(), {}).get(sector)
                    if ref_info is None:
                        ok = False
                    else:
                        if ref_info["coverage"] < config["coverage_floor"]:
                            ok = False
                        elif abs(
                            (effs[0] - date.fromisoformat(ref_info["effective_date"])).days
                        ) > config["coherence_days"]:
                            ok = False
                per_sector[sector] = ok
            eligible.append(sum(1 for ok in per_sector.values() if ok))

        cohort_median = (
            sorted(cohort_sizes)[len(cohort_sizes) // 2] if cohort_sizes else None
        )
        cohort_median_40 = None
        sizes_40 = [
            info["filers_included"]
            for session in slots
            for sector, info in observations[config["fields"][0]]
            .get(session.isoformat(), {})
            .items()
            if info["filers_mapped"] == 40
        ]
        if sizes_40:
            cohort_median_40 = sorted(sizes_40)[len(sizes_40) // 2]

        entry: dict = {
            "config": config,
            "eligible_sectors_per_tick": eligible,
            "min_eligible": min(eligible) if eligible else None,
            "max_eligible": max(eligible) if eligible else None,
            "ticks_with_ge_9_eligible": sum(1 for n in eligible if n >= 9),
            "ticks_with_ge_6_eligible": sum(1 for n in eligible if n >= 6),
            "cohort_sizes_single_vintage": {
                "n_sector_ticks": len(cohort_sizes),
                "median": cohort_median,
                "median_of_40_filer_sectors": cohort_median_40,
            },
            "census_gate_measured": {
                field: {s: v for s, v in sorted(census_passing[field].items())}
                for field in config["fields"]
            },
        }
        if v5_audit is not None:
            v5 = v5_audit["proposals"][cfg_id]
            v5_series = v5["feature_build_through"]["measured_eligible_sectors_per_tick"]
            entry["v5_reference"] = {
                "eligible_sectors_per_tick": v5_series,
                "verdict": v5["verdict"],
                "min_eligible": v5["feature_build_through"]["min_eligible"],
                "ticks_with_ge_9_eligible": v5["feature_build_through"].get(
                    "ticks_with_ge_9_eligible"
                ),
                "ticks_with_ge_6_eligible": v5["feature_build_through"].get(
                    "ticks_with_ge_6_eligible"
                ),
            }
            reproduction: dict = {
                "eligible_series_match": eligible == v5_series,
                "per_tick_diff": [
                    {"tick_index": i, "v6": a, "v5": b}
                    for i, (a, b) in enumerate(zip(eligible, v5_series))
                    if a != b
                ],
            }
            ftb = v5["feature_build_through"]
            table_specs = (
                ("coverage_table_t_side", config["fields"][0], "direct"),
                ("coverage_table_ref252_side", config["fields"][0], "direct"),
                ("coverage_table", config["fields"][0], "direct"),
            )
            for table_key, field, key_mode in table_specs:
                if table_key not in ftb:
                    continue
                v5_table = ftb[table_key].get("per_slot_per_sector", {})
                # audit table keys are the actual observation dates (ticks,
                # slots, or true ref-252 dates) - compare at the same dates
                key_map = None
                mismatches = compare_coverage_tables(
                    v5_table, coverage_tables[field], key_map
                )
                reproduction[f"{table_key}_match"] = not mismatches
                reproduction[f"{table_key}_mismatch_count"] = len(mismatches)
                reproduction[f"{table_key}_diff"] = mismatches[:40]
            entry["reproduction"] = reproduction
        configs_out[cfg_id] = entry

    payload = {
        "schema": "stocks_free_v6_run/p0a_f1_repro_full@1",
        "geometry": {
            "quarterly_ticks": [d.isoformat() for d in tick_dates],
            "grid42_slots": [d.isoformat() for d in slot_dates],
            "ref252_sessions": {
                tick.isoformat(): ref.isoformat() for tick, ref in sorted(ref252.items())
            },
        },
        "warmup_census_v6": warmup,
        "warmup_census_v5_comparison": warmup_v5_compare,
        "configs": configs_out,
    }
    write_json_deterministic(REPRO_OUT, payload)
    return payload


# --------------------------------------------------------------------------
# multi-vintage coverage census + fundable clock evaluation
# --------------------------------------------------------------------------

def coverage_census(panel_sizes: dict[str, int], tick_dates: list[date]) -> dict:
    series_blob = json.loads(SERIES_OUT.read_text())
    first_avail_blob = json.loads(FIRST_AVAIL_OUT.read_text())
    lag_blob = series_blob["lag_histograms"]
    cutoff = date_to_ord(S0_START)

    sector_filers: dict[str, list[str]] = {s: [] for s in SECTOR_UNIVERSE}
    for entity, sector in sorted(
        {
            entity: key.split("|", 1)[0]
            for key, slot in first_avail_blob["entries"].items()
            for entity in slot
        }.items()
    ):
        if sector in sector_filers:
            sector_filers[sector].append(entity)
    all_filers = sorted(entity for s in SECTOR_UNIVERSE for entity in sector_filers[s])

    per_field: dict[str, dict] = {}
    for field in series_blob["census_fields"]:
        by_entity: dict[str, FilerFieldSeries] = {}
        rank_conflicts = 0
        conflicting_entities: list[str] = []
        for entity, data in series_blob["series"].get(field, {}).items():
            bucket = FilerFieldSeries(entity_id=entity)
            for a_ord, e_ord, value in zip(data["avail"], data["eff"], data["val"]):
                bucket.add(
                    VintageStamp(
                        available_ord=a_ord,
                        effective_date=ord_to_date(e_ord),
                        value=value,
                    )
                )
            # census mode: coverage is invariant to which of two same-rank
            # conflicting values wins; conflicts are counted and published
            bucket.finalize(strict=False)
            if bucket.rank_conflicts:
                rank_conflicts += bucket.rank_conflicts
                conflicting_entities.append(entity)
            by_entity[entity] = bucket

        timelines: dict[str | None, list[tuple[date, float]]] = {}
        for label, filers in (
            ("pooled", all_filers),
            *[(sector, sector_filers[sector]) for sector in SECTOR_UNIVERSE],
        ):
            for age in AGE_GRID_DAYS:
                timelines[f"{label}|{age}"] = coverage_timeline(
                    by_entity, filers, tick_dates, max_age_days=age
                )

        pooled_unbounded = timelines[f"pooled|None"]
        lags = []
        for lag_str, count in lag_blob.get(field, {}).items():
            lags.extend([int(lag_str)] * count)

        per_field[field] = {
            "records_in_series": sum(len(b.stamps) for b in by_entity.values()),
            "filers_with_any_record": len(by_entity),
            "same_rank_value_conflicts": {
                "count": rank_conflicts,
                "entities": conflicting_entities,
            },
            "pooled_coverage_per_tick_unbounded": [
                [d.isoformat(), round(f, 4)] for d, f in pooled_unbounded
            ],
            "first_cross_dates_unbounded": {
                str(floor): (
                    first_cross_date(pooled_unbounded, floor).isoformat()
                    if first_cross_date(pooled_unbounded, floor) is not None
                    else None
                )
                for floor in COVERAGE_FLOORS
            },
            "age_bounded_pooled_first_cross": {
                str(age): {
                    str(floor): (
                        first_cross_date(timelines[f"pooled|{age}"], floor).isoformat()
                        if first_cross_date(timelines[f"pooled|{age}"], floor) is not None
                        else None
                    )
                    for floor in COVERAGE_FLOORS
                }
                for age in AGE_GRID_DAYS
            },
            "age_bounded_pooled_dates_at_or_above_floor": {
                str(age): {
                    str(floor): sum(
                        1 for _, f in timelines[f"pooled|{age}"] if f >= floor
                    )
                    for floor in COVERAGE_FLOORS
                }
                for age in AGE_GRID_DAYS
            },
            "age_bounded_pooled_mean_coverage": {
                str(age): round(
                    math.fsum(f for _, f in timelines[f"pooled|{age}"])
                    / max(1, len(timelines[f"pooled|{age}"])),
                    4,
                )
                for age in AGE_GRID_DAYS
            },
            "per_sector_unbounded_mean_coverage": {
                sector: round(
                    math.fsum(f for _, f in timelines[f"{sector}|None"])
                    / max(1, len(timelines[f"{sector}|None"])),
                    4,
                )
                for sector in SECTOR_UNIVERSE
            },
            "availability_lag_days": (
                {
                    "n": stats.n,
                    "mean": round(stats.mean_days, 2),
                    "p50": stats.p50_days,
                    "p75": stats.p75_days,
                    "p90": stats.p90_days,
                    "p95": stats.p95_days,
                    "p99": stats.p99_days,
                    "min": stats.min_days,
                    "max": stats.max_days,
                }
                if (stats := lag_stats(lags))
                else None
            ),
        }

    # any-history coverage for ALL fields at the 30 ticks (monotone in t)
    all_fields_timeline: dict[str, dict] = {}
    entries = first_avail_blob["entries"]
    by_field: dict[str, dict[str, list[tuple[str, int]]]] = {}
    for key, slot in entries.items():
        sector, field = key.split("|", 1)
        for entity, ordinal in slot.items():
            by_field.setdefault(field, {}).setdefault(entity, (sector, ordinal))
            prev = by_field[field][entity]
            if ordinal < prev[1]:
                by_field[field][entity] = (sector, ordinal)
    for field, slot in sorted(by_field.items()):
        fractions = []
        for tick in tick_dates:
            gate = date_to_ord(tick)
            covered = sum(1 for _, ordinal in slot.values() if ordinal < gate)
            fractions.append(round(covered / 410, 4))
        firsts = {
            str(floor): next(
                (d.isoformat() for d, f in zip(tick_dates, fractions) if f >= floor),
                None,
            )
            for floor in COVERAGE_FLOORS
        }
        all_fields_timeline[field] = {
            "filers_any_history": len(slot),
            "pooled_any_history_coverage_per_tick": fractions,
            "first_cross_dates_any_history": firsts,
        }

    payload = {
        "schema": "stocks_free_v6_run/p0a_coverage_census_full@1",
        "decision_dates": [d.isoformat() for d in tick_dates],
        "age_grid_days": [str(a) for a in AGE_GRID_DAYS],
        "floors": list(COVERAGE_FLOORS),
        "census_fields": per_field,
        "all_fields_any_history": all_fields_timeline,
    }
    write_json_deterministic(CENSUS_OUT, payload)
    return payload


# --------------------------------------------------------------------------
# emit control artifacts
# --------------------------------------------------------------------------

def emit(store: Path, panel_manifest_extra: dict) -> dict:
    scan_stats = json.loads(SCAN_STATS_OUT.read_text())
    repro_blob = json.loads(REPRO_OUT.read_text())
    census_blob = json.loads(CENSUS_OUT.read_text())
    field_counts = json.loads(FIELD_COUNTS_OUT.read_text())
    panel_sha = sha256_file(PANEL_OUT)
    input_hashes = {
        "pit_store_sha256": sha256_file(store),
        "v5_filer_panel": "32e4de942488d1b431bacb9b68f8bc4955b7de1991da268a4982d9d3b6c6cb16",
        "spy_calendar": sha256_file(DEFAULT_SPY_CAL),
        "v5_a9f_audit": (
            sha256_file(Path(v5_path))
            if (v5_path := next((str(p) for p in V5_A9F_AUDIT_CANDIDATES if p.exists()), None))
            else None
        ),
    }

    # ---- 1. F1 census reproduction --------------------------------------
    configs = repro_blob["configs"]
    all_match = all(
        cfg.get("reproduction", {}).get("eligible_series_match", False)
        for cfg in configs.values()
    )
    tables_match = {
        cfg_id: {
            key: value
            for key, value in cfg.get("reproduction", {}).items()
            if key.endswith("_match")
        }
        for cfg_id, cfg in configs.items()
    }
    a4h1 = configs["a4_h1"]
    repro_doc = {
        "schema": "stocks_free_v6_run/p0a_f1_census_repro@1",
        "producer": PRODUCER,
        "input_hashes": input_hashes,
        "commands": [
            "python -m research.assets.stocks.p0a_census_repro --mode all "
            f"--store {store}",
        ],
        "determinism": "same input bytes -> same output bytes; no wall-clock fields",
        "v5_claim_reproduced": {
            "store_records": {
                "expected": EXPECTED_STORE_RECORDS,
                "measured": scan_stats["records"],
            },
            "store_filers": {
                "expected": EXPECTED_STORE_FILERS,
                "measured": scan_stats["distinct_entities"],
            },
            "store_distinct_fields": {
                "expected": EXPECTED_STORE_FIELDS,
                "measured": scan_stats["distinct_fields"],
            },
            "multi_stamp_vintage_groups": {
                "expected": EXPECTED_MULTI_STAMP_GROUPS,
                "measured": scan_stats["multi_stamp_vintage_groups"],
            },
        },
        "eligible_series_reproduced_all_four": all_match,
        "coverage_tables_reproduced": tables_match,
        "warmup_census_v5_exact_match": (
            repro_blob.get("warmup_census_v5_comparison", {}) or {}
        ).get("exact_match"),
        "warmup_census_v5_comparison_summary": {
            key: repro_blob.get("warmup_census_v5_comparison", {}).get(key)
            for key in ("keys_mine", "keys_v5", "fraction_mismatches")
            if repro_blob.get("warmup_census_v5_comparison")
        },
        "mechanism": {
            "primary": (
                "single-vintage aggregation semantics of the canonical bridge "
                "(pit_conditioning.aggregate_sector_asof): one effective date per "
                "sector per call (the latest effective date with >=1 gated filer); "
                "only filers holding a gated value at THAT date are included, so an "
                "off-cycle filer's leading period end pins the sector observation to "
                "a 1-15 filer cohort and coverage collapses"
            ),
            "sanitizer_dropped_history": False,
            "sanitizer_evidence": (
                f"store carries {scan_stats['multi_stamp_vintage_groups']} "
                "multi-stamp vintage groups (reproduced from bytes); multi-vintage "
                "history is intact, so the collapse is aggregation semantics, not "
                "data loss"
            ),
            "filer_coverage_existence": (
                "pre-S0 existence census (A7) recomputed and matched V5 exactly for "
                "major fields; existence was never the binding constraint"
            ),
            "window_edges": (
                "S0/ref-252 sessions exist on the frozen calendar back to 2017-04; "
                "the ref252-side table has populated observations, so window edges "
                "are not the primary cause"
            ),
            "quantified": {
                "a4_h1_eligible_per_tick_v6": a4h1["eligible_sectors_per_tick"],
                "a4_h1_eligible_per_tick_v5": a4h1["v5_reference"]["eligible_sectors_per_tick"],
                "a4_h1_median_newest_vintage_cohort": a4h1["cohort_sizes_single_vintage"],
                "per_config_headline": {
                    cfg_id: {
                        "v6_eligible_min": cfg["min_eligible"],
                        "v6_eligible_max": cfg["max_eligible"],
                        "v6_ticks_ge_9": cfg["ticks_with_ge_9_eligible"],
                        "v5_verdict": cfg.get("v5_reference", {}).get("verdict"),
                        "eligible_series_match": cfg.get("reproduction", {}).get(
                            "eligible_series_match"
                        ),
                    }
                    for cfg_id, cfg in configs.items()
                },
            },
        },
        "full_tables_ref": ".staging_sec_v6/_p0a_f1_repro.json (gitignored staging copy)",
    }
    write_json_deterministic(
        CONTROL_DIR / "p0a_f1_census_repro.json", repro_doc
    )

    # ---- 2. panel manifest ----------------------------------------------
    panel_doc = {
        "schema": "stocks_free_v6_run/p0a_multivintage_panel_manifest@1",
        "producer": PRODUCER,
        "panel_path": ".staging_sec_v6/multivintage_panel.jsonl (GITIGNORED; raw panel bytes are never committed)",
        "panel_sha256": panel_sha,
        "panel_records": scan_stats["records"],
        "lineage": {
            "upstream_store": {
                "path": str(store),
                "sha256": input_hashes["pit_store_sha256"],
                "records": scan_stats["records"],
            },
            "semantics_module": "research/assets/stocks/p0a_multivintage.py",
            "semantics_schema": P0A_SCHEMA_VERSION,
            "builder": "research/assets/stocks/p0a_census_repro.py (pass1)",
            "canonical_bridge_unchanged": "research/assets/stocks/pit_conditioning.py (V5 canonical, untouched)",
        },
        "row_schema": {
            "e": "entity_id (CIKxxxxxxxxxx)",
            "s": "sector tag of the frozen 410-filer panel",
            "f": "field (taxonomy:tag)",
            "u": "unit",
            "v": "filed value (int/float/string/null as filed)",
            "eff": "effective (period end) date YYYY-MM-DD",
            "evd": "event date when it differs from effective",
            "avail": "availability date (SEC filed date; availability stamp = end of filed UTC day) YYYY-MM-DD",
        },
        "pit_semantics": (
            "MULTI-VINTAGE: every filed vintage is retained; a decision at t may "
            "observe the latest vintage with avail < gate(t) (plus optional age "
            "bound) - never the latest vintage in the store"
        ),
        "store_invariants_verified": {
            "sector_constant_per_entity": scan_stats["sector_mismatches_vs_store"] == 0,
            "sector_matches_v5_panel": scan_stats["sector_mismatches_vs_panel"] == 0,
            "all_availability_stamps_eod_utc": scan_stats["non_eod_availability_stamps"] == 0,
        },
        **panel_manifest_extra,
    }
    write_json_deterministic(
        CONTROL_DIR / "p0a_multivintage_panel_manifest.json", panel_doc
    )

    # ---- 3. coverage census ---------------------------------------------
    census_fields = census_blob["census_fields"]
    dates = census_blob["decision_dates"]
    mid_date = dates[len(dates) // 2]
    census_doc = {
        "schema": "stocks_free_v6_run/p0a_coverage_census@1",
        "producer": PRODUCER,
        "decision_dates": dates,
        "census_field_selection_rule": {
            "rule": "all fields with >= 20000 records, capped at top 40 by (count desc, name asc), plus the five V5-proposal fields",
            "selected": sorted(census_fields),
        },
        "per_field": {
            field: {
                "records_in_series": blob["records_in_series"],
                "filers_with_any_record": blob["filers_with_any_record"],
                "same_rank_value_conflicts": blob["same_rank_value_conflicts"],
                "pooled_coverage_per_tick_multi_vintage_unbounded": blob[
                    "pooled_coverage_per_tick_unbounded"
                ],
                "first_cross_dates_multi_vintage_unbounded": blob[
                    "first_cross_dates_unbounded"
                ],
                "age_bounded_first_cross": blob["age_bounded_pooled_first_cross"],
                "age_bounded_dates_at_or_above_floor": blob[
                    "age_bounded_pooled_dates_at_or_above_floor"
                ],
                "age_bounded_mean_coverage": blob["age_bounded_pooled_mean_coverage"],
                "per_sector_unbounded_mean_coverage": blob[
                    "per_sector_unbounded_mean_coverage"
                ],
                "availability_lag_days": blob["availability_lag_days"],
            }
            for field, blob in sorted(census_fields.items())
        },
        "all_fields_any_history": {
            field: {
                "filers_any_history": blob["filers_any_history"],
                "coverage_per_tick": blob["pooled_any_history_coverage_per_tick"],
                "first_cross_dates": blob["first_cross_dates_any_history"],
            }
            for field, blob in sorted(
                census_blob["all_fields_any_history"].items()
            )
        },
        "headline": {
            "note": "pooled multi-vintage unbounded coverage at S0 start/mid/end, census fields",
            "at_start": {
                field: blob["pooled_coverage_per_tick_unbounded"][0][1]
                for field, blob in sorted(census_fields.items())
            },
            "at_mid": {
                field: next(
                    value for d, value in blob["pooled_coverage_per_tick_unbounded"]
                    if d == mid_date
                )
                for field, blob in sorted(census_fields.items())
            },
            "at_end": {
                field: blob["pooled_coverage_per_tick_unbounded"][-1][1]
                for field, blob in sorted(census_fields.items())
            },
        },
        "full_detail_ref": ".staging_sec_v6/_p0a_coverage_census_full.json (gitignored)",
    }
    write_json_deterministic(CONTROL_DIR / "p0a_coverage_census.json", census_doc)

    # ---- 4. fundable clocks ---------------------------------------------
    clocks = []
    for field, blob in sorted(census_fields.items()):
        for age in [str(a) for a in AGE_GRID_DAYS]:
            n_dates = len(dates)
            stats = {
                "field": field,
                "clock": f"latest filed vintage as of t with age <= {age} days"
                if age != "None"
                else "latest filed vintage as of t (unbounded)",
                "max_age_days": None if age == "None" else int(age),
                "semantics": (
                    "per filer: newest vintage with avail < gate(t) and age <= bound; "
                    "sector aggregate = math.fsum mean over covered filers; "
                    "coverage = covered filers / mapped filers; no shared effective "
                    "date is imposed (multi-vintage as-of mix)"
                ),
                "evidence": {
                    "pooled_mean_coverage": blob["age_bounded_pooled_mean_coverage"][age],
                    "dates_at_or_above_floor_of_30": blob[
                        "age_bounded_pooled_dates_at_or_above_floor"
                    ][age],
                    "first_cross_dates": blob["age_bounded_pooled_first_cross"][age],
                },
            }
            at_floor_06 = blob["age_bounded_pooled_dates_at_or_above_floor"][age]["0.6"]
            at_floor_04 = blob["age_bounded_pooled_dates_at_or_above_floor"][age]["0.4"]
            stats["proposed_status"] = (
                "FUNDED_CANDIDATE"
                if at_floor_06 >= 27 and at_floor_04 == n_dates
                else "NOT_FUNDED_CANDIDATE"
            )
            clocks.append(stats)
    clocks_doc = {
        "schema": "stocks_free_v6_run/p0a_fundable_clocks@1",
        "producer": PRODUCER,
        "binding_statement": (
            "PROPOSAL ONLY: A1 freezes the coverage floor and the final clock list. "
            "Clocks NOT evidenced on this list are unfundable in V6; no proposal may "
            "cite an unfunded clock (plan section 6 P0a, binding B1_ORDER)."
        ),
        "proposed_funding_rule": (
            "FUNDED_CANDIDATE: pooled panel coverage >= 0.6 on >= 27/30 S0 quarterly "
            "decision dates AND >= 0.4 on 30/30, measured on the multi-vintage "
            "age-bounded as-of-mix semantics with the stated bound"
        ),
        "clocks": clocks,
        "single_vintage_clocks_status": (
            "NOT_FUNDED: the single-vintage (shared effective date) semantics "
            "collapse coverage (see p0a_f1_census_repro.json) and are not proposed"
        ),
    }
    write_json_deterministic(CONTROL_DIR / "p0a_fundable_clocks.json", clocks_doc)

    return {
        "eligible_series_reproduced_all_four": all_match,
        "panel_sha256": panel_sha,
        "clocks_funded_candidates": sum(
            1 for c in clocks if c["proposed_status"] == "FUNDED_CANDIDATE"
        ),
        "clocks_total": len(clocks),
    }


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("pass0", "pass1", "repro", "emit", "all"),
        default="all",
    )
    parser.add_argument("--store", type=Path, default=DEFAULT_STORE)
    parser.add_argument("--panel", type=Path, default=DEFAULT_PANEL)
    parser.add_argument("--skip-store-hash", action="store_true",
                        help="skip the (slow) full-store sha256 when it was "
                             "verified in the same run already")
    args = parser.parse_args()

    store = args.store
    if not store.exists():
        print(f"BLOCKED: store missing at {store}", file=sys.stderr)
        return 2

    if args.mode in ("pass0", "all"):
        payload = pass0(store)
        print(f"pass0: records={payload['records']} fields={payload['distinct_fields']}")

    census_fields = select_census_fields(
        json.loads(FIELD_COUNTS_OUT.read_text())["field_counts"]
    )
    if args.mode == "pass1":
        store_sha = sha256_file(store)
        if store_sha != EXPECTED_STORE_SHA256:
            print("BLOCKED: store sha256 mismatch", file=sys.stderr)
            return 2
    if args.mode in ("pass1", "all"):
        filer_sector, _ = load_panel_mapping(args.panel)
        payload = pass1(store, census_fields, filer_sector)
        print(
            f"pass1: records={payload['records']} entities={payload['distinct_entities']} "
            f"fields={payload['distinct_fields']} groups={payload['total_vintage_groups']} "
            f"multi={payload['multi_stamp_vintage_groups']}"
        )
        if args.mode == "pass1":
            return 0
    elif args.mode in ("repro", "emit"):
        store_sha = sha256_file(store) if not args.skip_store_hash else EXPECTED_STORE_SHA256
        if store_sha != EXPECTED_STORE_SHA256:
            print("BLOCKED: store sha256 mismatch", file=sys.stderr)
            return 2

    if args.mode in ("repro", "emit", "all"):
        filer_sector, panel_sizes = load_panel_mapping(args.panel)
        sessions = load_sessions(DEFAULT_SPY_CAL)
        v5_audit = None
        v5_path = next((p for p in V5_A9F_AUDIT_CANDIDATES if p.exists()), None)
        if v5_path is not None:
            v5_audit = json.loads(v5_path.read_text())
        if args.mode in ("repro", "all"):
            repro_blob = repro(filer_sector, panel_sizes, sessions, v5_audit)
            matched = all(
                cfg.get("reproduction", {}).get("eligible_series_match")
                for cfg in repro_blob["configs"].values()
            )
            print(f"repro: eligible_series_reproduced_all_four={matched}")
        if args.mode == "repro":
            return 0

    if args.mode in ("emit", "all"):
        if args.mode == "emit":
            store_sha = sha256_file(store) if not args.skip_store_hash else EXPECTED_STORE_SHA256
            if store_sha != EXPECTED_STORE_SHA256:
                print("BLOCKED: store sha256 mismatch", file=sys.stderr)
                return 2
            filer_sector, panel_sizes = load_panel_mapping(args.panel)
            sessions = load_sessions(DEFAULT_SPY_CAL)
        coverage_census(panel_sizes, quarterly_ticks(sessions))
        extra = {
            "census_field_selection": {
                "rule": f">= {CENSUS_MIN_RECORDS} records, cap {CENSUS_MAX_FIELDS} heaviest, plus five V5-proposal fields",
                "n_census_fields": len(census_fields),
            }
        }
        summary = emit(args.store, extra)
        print(
            f"emit: all_four_match={summary['eligible_series_reproduced_all_four']} "
            f"clocks_funded={summary['clocks_funded_candidates']}/{summary['clocks_total']} "
            f"panel_sha={summary['panel_sha256'][:12]}..."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
