#!/usr/bin/env python
"""FOREX-NG1 P1-SPOT artifact builder (single-shot, deterministic from bytes).

Produces, under research/control/forex_ng1_run/p1_spot/:

1. spot_pin_manifest.json     -- the PIN: byte-identical copies of the four
                                  V9 spot JSON files into data_raw/
                                  forex_ng1_spot/ (untracked: data_raw/ is
                                  NOT gitignored here, so raw bytes are
                                  never committed; only this manifest is),
                                  with per-pair sha256 (source AND copy),
                                  bar counts and first/last bar dates.
2. spot_authority_proof.json  -- honest fail-closed channel authority
                                  proof from V9 evidence (what the channel
                                  is, license/terms status, structural
                                  canary results).
3. spot_integrity_census.json -- schema parse, duplicate/monotonic checks,
                                  OHLC cross-violation record, DST sanity
                                  of the 16:00-NY mapping, coverage census
                                  vs the S0 window.
4. spot_grid_census.json      -- the 16:00-NY daily decision grid staging
                                  census per pair (V9 frozen
                                  representation).

Run from anywhere:  .venv/bin/python research/control/forex_ng1_run/\
p1_spot/build_artifacts.py
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
from datetime import date, datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(
    os.path.join(HERE, "..", "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.assets.forex_ng1 import spot_series as ss  # noqa: E402

V9_ROOT = ("/Users/hoangminhlong/my-quantitative/.worktrees/"
           "forex-free-v9/integration")
V9_SPOT_SOURCE_DIR = os.path.join(V9_ROOT, "data_raw/forex_free_v9_spot")
V9_RUN_CONTROL = os.path.join(
    V9_ROOT, "research/control/forex_free_v9_run")
V1_PROBE_CONTROL = os.path.join(
    V9_ROOT, "research/control/forex_free_v1_run/data_probe")

PAIRS = ss.FUNDED_PAIRS
WINDOW_START, WINDOW_END = ss.S0_WINDOW_START, ss.S0_WINDOW_END

#: Known calendar closures for the missing-weekday classification (only
#: dates that actually appear missing in the pinned bytes are looked up).
KNOWN_CLOSURES = {
    "2019-05-22": "UNEXPLAINED_DATA_HOLE (no G7 FX calendar closure; "
                  "provider gap -- recorded, not repaired)",
    "2025-01-01": "New Year's Day (FX global closure)",
    "2025-04-18": "Good Friday (FX global closure)",
    "2025-04-21": "Easter Monday (UK/GB-specific closure; GBPUSD only)",
}


def _read_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _write_json(path, obj):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, sort_keys=False)
        fh.write("\n")


# --------------------------------------------------------------------------- #
# 1. PIN
# --------------------------------------------------------------------------- #

def pin_spot_files() -> dict:
    os.makedirs(ss.DEFAULT_DATA_DIR, exist_ok=True)
    files = {}
    for pair in PAIRS:
        fname = f"{pair}.json"
        src = os.path.join(V9_SPOT_SOURCE_DIR, fname)
        dst = os.path.join(ss.DEFAULT_DATA_DIR, fname)
        if not os.path.exists(src):
            raise SystemExit(f"STOP: V9 source file missing: {src}")
        src_sha = ss.sha256_file(src)
        if (not os.path.exists(dst)
                or ss.sha256_file(dst) != src_sha):
            shutil.copyfile(src, dst)   # re-pin drifted/absent copy
        dst_sha = ss.sha256_file(dst)
        payload = _read_json(dst)
        values = payload.get("values", [])
        dates = [str(v["datetime"]) for v in values]
        files[pair] = {
            "file": fname,
            "source_path_absolute": src,
            "copy_path_absolute": os.path.abspath(dst),
            "source_sha256": src_sha,
            "copy_sha256": dst_sha,
            "source_copy_identical": src_sha == dst_sha,
            "bars": len(values),
            "first_bar_date": min(dates),
            "last_bar_date": max(dates),
            "provider_meta": payload.get("meta", {}),
            "status": payload.get("status"),
        }
    manifest = {
        "schema": ss.PIN_MANIFEST_SCHEMA,
        "cycle_id": "FOREX-NG1",
        "task_id": "forex-ng1-p1-spot-authority",
        "pinned_utc": datetime.now(timezone.utc).isoformat(),
        "pin_basis": (
            "byte-identical copies of the V9 'spot_reacquired' staging "
            "(FOREX-FREE-V9 run contract data_pins; Twelve Data "
            "time_series 1day, 5000 bars/pair). Source worktree is "
            "READ-ONLY. Raw copies are UNTRACKED (data_raw/ is not "
            "gitignored in this worktree -> never committed); this "
            "manifest is the committed authority."),
        "source_worktree": V9_ROOT,
        "raw_bytes_policy": "UNTRACKED_NEVER_COMMITTED",
        "files": files,
    }
    _write_json(os.path.join(HERE, "spot_pin_manifest.json"), manifest)
    return manifest


# --------------------------------------------------------------------------- #
# 2. AUTHORITY PROOF (honest, fail-closed)
# --------------------------------------------------------------------------- #

def _v9_quotes() -> dict:
    run_contract = _read_json(os.path.join(V9_RUN_CONTROL, "run_contract.json"))
    p2 = _read_json(os.path.join(
        V9_RUN_CONTROL, "p2_conditioning_clocks_v9.json"))
    p3 = _read_json(os.path.join(
        V9_RUN_CONTROL, "p3_invariants_freeze_v9.json"))
    v1_manifest = _read_json(os.path.join(
        V1_PROBE_CONTROL, "request_manifest.json"))
    v1_xchk = _read_json(os.path.join(V1_PROBE_CONTROL, "ecb_crosscheck.json"))

    # the TWELVE_DATA source-registry line, verbatim (terms evidence)
    reg_path = os.path.join(
        V9_ROOT, "research/data_fusion/source_registry.py")
    reg_line = None
    with open(reg_path, "r", encoding="utf-8") as fh:
        for line in fh:
            if 'SourceSpec("TWELVE_DATA"' in line:
                reg_line = line.strip()
                break

    # V1 determinism: paired a/b pulls with identical sha256 (1day)
    det = []
    by_key = {}
    for r in v1_manifest.get("requests", []):
        if r.get("interval") != "1day":
            continue
        by_key.setdefault((r["pair"], r["start"]), {})[r["pull"]] = r
    for (pair, start), pulls in sorted(by_key.items()):
        if "a" in pulls and "b" in pulls:
            det.append({
                "pair": pair, "window_start": start,
                "pull_a_sha256": pulls["a"]["sha256"],
                "pull_b_sha256": pulls["b"]["sha256"],
                "byte_identical": (pulls["a"]["sha256"]
                                   == pulls["b"]["sha256"]),
                "provider_error": pulls["a"].get("http_or_provider_error"),
            })
    return {
        "run_contract": {
            "file": "research/control/forex_free_v9_run/run_contract.json",
            "data_pins_spot_reacquired":
                run_contract["data_pins"]["spot_reacquired"],
            "decision_clock": run_contract["decision_clock"],
            "s0_window": run_contract["s0_window"],
            "budget_used_at_close": run_contract["budget"]["used"],
        },
        "p2_conditioning_clocks_spot_leg": {
            "file": "research/control/forex_free_v9_run/"
                    "p2_conditioning_clocks_v9.json",
            "spot_leg": p2.get("spot_leg"),
        },
        "p3_invariants_freeze": {
            "file": "research/control/forex_free_v9_run/"
                    "p3_invariants_freeze_v9.json",
            "decision_clock": p3.get("decision_clock"),
            "spot_leg_disclosure": p3.get("spot_leg_disclosure"),
        },
        "v1_probe_determinism": {
            "file": "research/control/forex_free_v1_run/data_probe/"
                    "request_manifest.json",
            "provider": v1_manifest.get("provider"),
            "key_source": v1_manifest.get("key_source"),
            "one_day_double_pulls": det,
            "all_double_pulls_byte_identical": all(
                d["byte_identical"] for d in det),
        },
        "v1_ecb_crosscheck_basis_note": {
            "file": "research/control/forex_free_v1_run/data_probe/"
                    "ecb_crosscheck.json",
            "basis_note": v1_xchk.get("basis_note"),
            "gbpusd_bps": v1_xchk["pairs"]["GBP/USD"],
        },
        "source_registry_twelve_data": {
            "file": "research/data_fusion/source_registry.py",
            "spec_line_verbatim": reg_line,
        },
    }


def _structural_canary(serieses: dict) -> dict:
    """Structural canary standing in for the (keyed, therefore
    network-forbidden) endpoint probe: nonexistent pairs must be refused
    by the serving layer, fabricated dates must return found=False,
    and the pinned bytes must satisfy bar-count monotonicity, zero
    duplicates and a sane weekend structure."""
    per_pair = {}
    for pair, s in sorted(serieses.items()):
        dates = s.days
        weekend = [d for d in dates if d.weekday() >= 5]
        sat = sum(1 for d in weekend if d.weekday() == 5)
        sun = sum(1 for d in weekend if d.weekday() == 6)
        per_pair[pair] = {
            "bars": s.bars,
            "bar_count_equals_5000": s.bars == 5000,
            "duplicate_dates": 0,   # parser is fail-closed on duplicates
            "strictly_increasing_served_days": all(
                dates[i] < dates[i + 1] for i in range(len(dates) - 1)),
            "weekend_bars_total": len(weekend),
            "saturday_bars": sat,
            "sunday_bars": sun,
            "weekend_note": (
                "provider daily calendar carries partial weekend sessions; "
                "the V9 frozen decision grid deterministically excludes "
                "them (weekday filter)"),
        }
    # fabricated-date lookups (P-7 sensitivity: must be found=False)
    gbp = serieses["GBPUSD"]
    fabricated = [
        {"probe": "weekend_date", "query": gbp.lookup_close("2024-06-15")},
        {"probe": "future_date_beyond_last_bar",
         "query": gbp.lookup_close("2030-01-02")},
        {"probe": "date_before_first_bar",
         "query": gbp.lookup_close("2000-01-03")},
    ]
    # nonexistent-pair probes through the serving layer
    refused = []
    for fake in ("XXXUSD", "GBPXXX", "EURUSD"):
        try:
            ss.resolve_spot_series(fake)
            refused.append({"probe_pair": fake, "refused": False})
        except ss.SpotDataError as exc:
            refused.append({"probe_pair": fake, "refused": True,
                            "error_class": type(exc).__name__,
                            "message": str(exc)[:140]})
    return {
        "canary_class": "STRUCTURAL (keyed channel -> no keyless endpoint "
                        "probe; network not used by this lane)",
        "p-7_note": (
            "dispatch canary asked for 2 nonexistent pairs + 1 future date "
            "against a KEYLESS endpoint if one existed; the Twelve Data "
            "time_series endpoint is keyed (api.twelvedata.com), so the "
            "equivalent probes run against the serving layer and pinned "
            "bytes instead"),
        "bar_count_monotonicity": per_pair,
        "fabricated_date_lookups_all_not_found": all(
            f["query"]["found"] is False for f in fabricated),
        "fabricated_date_lookups": fabricated,
        "nonexistent_pair_probes_all_refused": all(
            r["refused"] for r in refused),
        "nonexistent_pair_probes": refused,
    }


def build_authority_proof(manifest: dict, serieses: dict) -> dict:
    quotes = _v9_quotes()
    canary = _structural_canary(serieses)
    proof = {
        "schema": ss.AUTHORITY_PROOF_SCHEMA,
        "cycle_id": "FOREX-NG1",
        "task_id": "forex-ng1-p1-spot-authority",
        "measured_utc": datetime.now(timezone.utc).isoformat(),
        "channel_identification": {
            "provider": "Twelve Data",
            "endpoint": "https://api.twelvedata.com/time_series",
            "product": "FX spot daily bars (interval=1day, outputsize=5000, "
                       "provider format {meta, values, status}; date-only "
                       "bar datetimes; no volume field)",
            "keyed": True,
            "key_handling": "TWELVE_DATA_API_KEY via environment / "
                            "gitignored root .env; never committed, never "
                            "printed (V9 exec_driver_v9 staging helper + "
                            "V1 probe_td.py convention)",
            "entitlement_basis": "OWNER existing entitlement (V9 p2 "
                                 "spot_leg re_acquisition_channel, quoted "
                                 "verbatim below)",
            "v9_scored_precedent": (
                "NONE: V9 closed FOREX_FREE_V9_BLOCKED_DATA_OR_SELECTION "
                "with budget 0/6 -- the channel was staged and dry-run "
                "only, never consumed by a scored cell"),
        },
        "authority_status": {
            "status": "DOCUMENTED_CANDIDATE",
            "scored_consumption": "CANDIDATE_NOT_AUTHORIZED",
            "staging_census_consumption": "ALLOWED_THROUGH_PINNED_BYTES",
            "license_terms_evidence": (
                "NOT FOUND in any V9 evidence: the V9-era source registry "
                "carries SourceSpec TWELVE_DATA with terms_url=None and "
                "AuthorityStatus.CANDIDATE_NOT_AUTHORIZED (line quoted "
                "verbatim below); no V9 artifact records Twelve Data "
                "license/terms text"),
            "owner_decision_required": (
                "BLOCKER for scored consumption: the owner (or this "
                "cycle's P0 authority lane via the plan's adoption law) "
                "must grant Twelve Data as a data authority for "
                "FOREX-NG1 scored consumption WITH terms recorded; this "
                "lane does not self-promote authority. To authorize: set "
                "authority_status.scored_consumption=AUTHORIZED in this "
                "committed artifact together with the recorded terms."),
        },
        "v9_evidence": quotes,
        "structural_canary": canary,
        "pin_manifest_schema_check": manifest["schema"],
        "verdict": (
            "CHANNEL DOCUMENTED (Twelve Data time_series 1day under the "
            "owner entitlement, byte-deterministic per V1 double-pull "
            "evidence) BUT NOT AUTHORIZED FOR SCORED CONSUMPTION: "
            "DOCUMENTED_CANDIDATE / CANDIDATE_NOT_AUTHORIZED -- fail-closed; "
            "structural canary PASS is a property of the PINNED BYTES, not "
            "a channel authorization"),
    }
    _write_json(os.path.join(HERE, "spot_authority_proof.json"), proof)
    return proof


# --------------------------------------------------------------------------- #
# 3. INTEGRITY CENSUS
# --------------------------------------------------------------------------- #

def _dst_sanity(s: ss.SpotSeries) -> dict:
    """Map every bar date to its 16:00-NY UTC instant; every consecutive
    instant gap must equal calendar-days*24h adjusted ONLY by US DST
    transitions falling between the two instants."""
    gaps, anomalies = [], []
    days = s.days
    for prev, cur in zip(days, days[1:]):
        inst_prev = ss.ny_decision_instant_utc(prev)
        inst_cur = ss.ny_decision_instant_utc(cur)
        gap_h = (inst_cur - inst_prev).total_seconds() / 3600.0
        cal_h = (cur - prev).days * 24.0
        # DST shift between the two 16:00-NY wall clocks, via utcoffset
        import datetime as _dt
        off_p = _dt.datetime(prev.year, prev.month, prev.day, 16,
                             tzinfo=ss.NY_TZ).utcoffset()
        off_c = _dt.datetime(cur.year, cur.month, cur.day, 16,
                             tzinfo=ss.NY_TZ).utcoffset()
        dst_h = (off_p - off_c).total_seconds() / 3600.0
        gaps.append(gap_h)
        if abs(gap_h - (cal_h + dst_h)) > 1e-9:
            anomalies.append({
                "from": prev.isoformat(), "to": cur.isoformat(),
                "instant_gap_hours": gap_h, "calendar_hours": cal_h,
                "dst_offset_delta_hours": dst_h,
                "expected_hours": cal_h + dst_h})
    from collections import Counter
    return {
        "bars_mapped": len(days),
        "instant_gap_distribution_hours": dict(Counter(gaps)),
        "gaps_not_explained_by_calendar_plus_dst": anomalies,
        "all_gaps_explained": not anomalies,
        "note": ("a 3-day Fri->Mon gap is 72h normally, 71h across a "
                 "spring-forward weekend, 73h across a fall-back "
                 "weekend; 1-day gaps are exactly 24h (transitions occur "
                 "on Sundays, which carry no weekday grid instant)"),
    }


def _coverage(s: ss.SpotSeries) -> dict:
    weekdays = {WINDOW_START + timedelta(days=i)
                for i in range((WINDOW_END - WINDOW_START).days + 1)}
    weekdays = {d for d in weekdays if d.weekday() < 5}
    present = {d for d in s.days if WINDOW_START <= d <= WINDOW_END}
    missing = sorted(weekdays - present)
    weekend_in_window = [d for d in s.days
                         if WINDOW_START <= d <= WINDOW_END
                         and d.weekday() >= 5]
    missing_rows = [{
        "date": d.isoformat(), "weekday": d.strftime("%A"),
        "classification": KNOWN_CLOSURES.get(
            d.isoformat(), "UNCLASSIFIED"),
    } for d in missing]
    return {
        "bars_in_window_weekday": len(present & weekdays),
        "weekend_bars_in_window_excluded_from_grid": len(weekend_in_window),
        "total_weekdays_in_window": len(weekdays),
        "missing_weekdays": missing_rows,
        "unclassified_missing_count": sum(
            1 for r in missing_rows if r["classification"] == "UNCLASSIFIED"),
    }


def build_integrity_census(serieses: dict) -> dict:
    per_pair = {}
    for pair, s in sorted(serieses.items()):
        raw = _read_json(os.path.join(ss.DEFAULT_DATA_DIR, f"{pair}.json"))
        ohlc_violations = []
        for v in raw["values"]:
            try:
                o, h, l, c = (float(v[k]) for k in ("open", "high",
                                                    "low", "close"))
            except (KeyError, TypeError, ValueError):
                ohlc_violations.append({"date": v.get("datetime"),
                                        "kind": "UNPARSEABLE_OHLC"})
                continue
            if not (h >= l and h >= o and h >= c and l <= o and l <= c):
                viol = []
                if o > h: viol.append(("open", "high", o - h))
                if o < l: viol.append(("open", "low", l - o))
                if c > h: viol.append(("close", "high", c - h))
                if c < l: viol.append(("close", "low", l - c))
                ohlc_violations.append({
                    "date": v["datetime"],
                    "kind": "OHLC_CROSS",
                    "violations": [
                        {"field_a": a, "field_b": b,
                         "abs_excess": round(x, 10)}
                        for a, b, x in viol],
                    "max_abs_excess_bps_of_close": round(
                        max(x for _a, _b, x in viol) / c * 1e4, 4)})
        storage = [str(v["datetime"]) for v in raw["values"]]
        per_pair[pair] = {
            "sha256": s.sha256,
            "schema": {
                "status": raw.get("status"),
                "meta": raw.get("meta"),
                "bar_fields": sorted({k for v in raw["values"] for k in v}),
                "values_storage": "newest-first" if storage[0] > storage[-1]
                                  else "oldest-first",
            },
            "bars": s.bars,
            "first_bar": s.first_day.isoformat(),
            "last_bar": s.last_day.isoformat(),
            "duplicate_dates": 0,
            "non_finite_or_non_positive_close": 0,
            "ohlc_cross_violations": {
                "count": len(ohlc_violations),
                "rows": ohlc_violations,
                "policy": ("RECORDED, not serve-blocking: all closes are "
                           "finite-positive and the decision grid consumes "
                           "close only; violations are provider "
                           "open/close-vs-range rounding artifacts"),
            },
            "dst_sanity_16ny": _dst_sanity(s),
            "coverage_s0_window": _coverage(s),
        }
    census = {
        "schema": "forex_ng1_p1_spot_integrity_census@1",
        "cycle_id": "FOREX-NG1",
        "task_id": "forex-ng1-p1-spot-authority",
        "measured_utc": datetime.now(timezone.utc).isoformat(),
        "s0_window": {
            "start": WINDOW_START.isoformat(),
            "end": WINDOW_END.isoformat(),
            "basis": "P1 dispatch window (V9 run contract carried "
                     "2018-04-04..2025-07-24; NG1 trims the tail per "
                     "plan section 3 tail-trim law)",
        },
        "parser_fail_closed_checks": [
            "status != ok -> refuse", "meta.interval != 1day -> refuse",
            "meta.symbol mismatch -> refuse",
            "duplicate bar datetime -> refuse",
            "non-ISO datetime -> refuse",
            "non-finite / non-positive close -> refuse",
            "sha256 verify-on-read mismatch -> refuse",
        ],
        "pairs": per_pair,
    }
    _write_json(os.path.join(HERE, "spot_integrity_census.json"), census)
    return census


# --------------------------------------------------------------------------- #
# 4. GRID CENSUS (16:00-NY daily decision grid staging)
# --------------------------------------------------------------------------- #

def build_grid_census(serieses: dict) -> dict:
    per_pair = {}
    grids = {}
    for pair, s in sorted(serieses.items()):
        grid = s.window_days(WINDOW_START, WINDOW_END, weekdays_only=True)
        grids[pair] = grid
        per_year = {}
        for d in grid:
            per_year[str(d.year)] = per_year.get(str(d.year), 0) + 1
        per_pair[pair] = {
            "grid_days": len(grid),
            "first_grid_day": grid[0].isoformat(),
            "first_grid_instant_utc": ss.instant_iso(
                ss.ny_decision_instant_utc(grid[0])),
            "last_grid_day": grid[-1].isoformat(),
            "last_grid_instant_utc": ss.instant_iso(
                ss.ny_decision_instant_utc(grid[-1])),
            "grid_days_by_year": dict(sorted(per_year.items())),
        }
    common = ss.common_weekday_grid(serieses, WINDOW_START, WINDOW_END)
    per_year_common = {}
    for d in common:
        per_year_common[str(d.year)] = per_year_common.get(str(d.year), 0) + 1
    # DST edge witnesses inside the common grid (hand-checkable 71/73h)
    edges = []
    for prev, cur in zip(common, common[1:]):
        gap_h = ((ss.ny_decision_instant_utc(cur)
                  - ss.ny_decision_instant_utc(prev)).total_seconds() / 3600)
        cal_h = (cur - prev).days * 24
        if abs(gap_h - cal_h) > 1e-9:
            edges.append({"from": prev.isoformat(), "to": cur.isoformat(),
                          "calendar_days": (cur - prev).days,
                          "instant_gap_hours": gap_h,
                          "dst_kind": "spring-forward" if gap_h < cal_h
                                      else "fall-back"})
    census = {
        "schema": "forex_ng1_p1_spot_grid_census@1",
        "cycle_id": "FOREX-NG1",
        "task_id": "forex-ng1-p1-spot-authority",
        "measured_utc": datetime.now(timezone.utc).isoformat(),
        "representation_identity": {
            "decision_clock": "daily 16:00 America/New_York, DST-correct "
                              "(zoneinfo) -- V9 frozen representation "
                              "inherited verbatim",
            "decision_close": "the close of the provider daily bar dated "
                              "D is served as the decision-instrument "
                              "close at the 16:00-NY instant of day D "
                              "(V9 family_common.load_spot_daily + "
                              "ny_close_ts mapping)",
            "basis_disclosure": (
                "provider daily bars aggregate the provider day (V1 ECB "
                "crosscheck basis note: TD daily close = last UTC-day "
                "quote); V9 froze the D-bar-close-at-16:00-NY(D) mapping "
                "and this cycle INHERITS it unchanged (P-12): any future "
                "re-representation is a new preregistered identity, not "
                "an edit here"),
            "grid_law": "FX 24/5 weekdays in window intersected across "
                        "the four funded-pair calendars (V9 build_grid); "
                        "weekend provider bars deterministically excluded",
        },
        "s0_window": {"start": WINDOW_START.isoformat(),
                      "end": WINDOW_END.isoformat()},
        "pairs": per_pair,
        "common_grid": {
            "grid_days": len(common),
            "first": common[0].isoformat(),
            "first_instant_utc": ss.instant_iso(
                ss.ny_decision_instant_utc(common[0])),
            "last": common[-1].isoformat(),
            "last_instant_utc": ss.instant_iso(
                ss.ny_decision_instant_utc(common[-1])),
            "grid_days_by_year": dict(sorted(per_year_common.items())),
            "dst_edge_weekends": edges,
        },
        "scored_consumption_note": (
            "grid staged for census/staging only; scored consumption "
            "remains refused until the authority proof records "
            "scored_consumption=AUTHORIZED"),
    }
    _write_json(os.path.join(HERE, "spot_grid_census.json"), census)
    return census


def main() -> int:
    manifest = pin_spot_files()
    print("PIN:", {p: (v["bars"], v["source_copy_identical"])
                   for p, v in manifest["files"].items()})
    serieses = ss.resolve_all_pairs()
    proof = build_authority_proof(manifest, serieses)
    print("AUTHORITY:", proof["authority_status"]["status"],
          "/", proof["authority_status"]["scored_consumption"])
    print("CANARY: fabricated_not_found =",
          proof["structural_canary"]["fabricated_date_lookups_all_not_found"],
          "pairs_refused =",
          proof["structural_canary"]["nonexistent_pair_probes_all_refused"])
    census = build_integrity_census(serieses)
    for p, rec in census["pairs"].items():
        print(f"INTEGRITY {p}: dup=0 ohlc_cross="
              f"{rec['ohlc_cross_violations']['count']}"
              f" dst_anomalies={len(rec['dst_sanity_16ny']['gaps_not_explained_by_calendar_plus_dst'])}"
              f" window_bars={rec['coverage_s0_window']['bars_in_window_weekday']}"
              f" missing={len(rec['coverage_s0_window']['missing_weekdays'])}")
    grid = build_grid_census(serieses)
    print("GRID common days:", grid["common_grid"]["grid_days"],
          "dst edges:", len(grid["common_grid"]["dst_edge_weekends"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
