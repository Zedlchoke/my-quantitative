#!/usr/bin/env python
"""FOREX-FREE-V2 (A3): build research/control/forex_free_v2_run/data_replay_evidence.json.

Replays EXISTING evidence with NO new download:
  1. full staged-manifest replay (156/156 sha256 digests) against the read-only
     FOREX-FREE-V1 snapshot;
  2. per-pair h1_grid_audit for all 7 pairs (bars, duplicates, missing-inside-open
     enumeration -> NO_TRADE fail-closed, weekend/stale classification);
  3. fold boundaries over the observed H1 range;
  4. DST probe table (weekly open/close + 16:00-New-York flatten mapping around
     both 2025 US transitions and both 2025 EU transitions), computed exactly via
     zoneinfo and the frozen session machinery.

Read-only inputs: the V1 snapshot (never modified) and the V1/V2 control files.
Writes ONLY the control-plane evidence JSON.  No network anywhere.
"""
import datetime as dt
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, REPO)

from research.assets.forex.sessions import (  # noqa: E402
    DEFAULT_FX_WEEK_CONVENTION as CONV,
    weekly_close_utc,
    weekly_open_utc,
)
from research.assets.forex_free_v1 import td_loader  # noqa: E402
from research.assets.forex_free_v2 import data_authority as DA  # noqa: E402

UTC = dt.timezone.utc
NY = CONV.open_zone_name
PAIRS = ["EUR/USD", "GBP/USD", "AUD/USD", "NZD/USD", "USD/JPY", "USD/CHF", "USD/CAD"]
OUT = os.path.join(REPO, "research", "control", "forex_free_v2_run",
                   "data_replay_evidence.json")


def iso(m):
    return m.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def dst_probe_table():
    """Exact instants around both 2025 US and both 2025 EU DST transitions."""
    probes = [
        ("winter reference", dt.date(2025, 1, 15)),
        ("US spring forward 2025-03-09", dt.date(2025, 3, 9)),
        ("US-EDT/EU-GMT desync", dt.date(2025, 3, 28)),
        ("EU spring forward 2025-03-30", dt.date(2025, 3, 30)),
        ("post-EU-spring / US-EDT", dt.date(2025, 3, 31)),
        ("summer reference", dt.date(2025, 7, 15)),
        ("EU-GMT/US-EDT desync", dt.date(2025, 10, 24)),
        ("EU fall back 2025-10-26", dt.date(2025, 10, 26)),
        ("post-EU-fall / US-EDT", dt.date(2025, 10, 27)),
        ("US fall back 2025-11-02", dt.date(2025, 11, 2)),
        ("winter reference (post US fall back)", dt.date(2025, 11, 3)),
    ]
    rows = []
    for label, day in probes:
        # week containing this date (Sunday-anchored open day)
        open_day = CONV.week_open_day_for(day)
        open_i = weekly_open_utc(open_day, CONV)
        close_i = weekly_close_utc(open_day, CONV)
        flat_i = DA.flat_bar_instant_utc(day, NY)
        from zoneinfo import ZoneInfo
        ny_off = ZoneInfo(NY).utcoffset(dt.datetime.combine(day, dt.time(16), tzinfo=ZoneInfo(NY)))
        rows.append({
            "probe": label,
            "date": day.isoformat(),
            "ny_offset_at_16_00": f"UTC{ny_off.total_seconds() / 3600:+.0f}:00",
            "weekly_open_local": f"Sun 21:00 {NY} ({open_day.isoformat()})",
            "weekly_open_utc": iso(open_i),
            "weekly_close_local": f"Fri 16:00 {NY} ({(open_day + dt.timedelta(days=5)).isoformat()})",
            "weekly_close_utc": iso(close_i),
            "flat_bar_stamp_utc": iso(flat_i),
            "flat_bar_rule": "16:00 America/New_York bar-open stamp; exit at its OPEN "
                             "= the 16:00 NY instant, strictly before the 17:00 NY rollover",
        })
    return rows


def main():
    replay = DA.replay_staged_manifest()

    pair_audits = {}
    firsts, lasts = [], []
    for pair in PAIRS:
        rows, quarantined = td_loader.load_pair_h1(pair, DA.SNAPSHOT_DATA_ROOT)
        audit = DA.h1_grid_audit(rows)
        audit["quarantined_bars"] = len(quarantined)
        audit["digest_bars"] = td_loader.digest_bars(rows)
        pair_audits[pair] = audit
        firsts.append(DA.parse_stamp(audit["first"]))
        lasts.append(DA.parse_stamp(audit["last"]))

    observed_first, observed_last = min(firsts), max(lasts)
    folds = DA.fold_boundaries(observed_first, observed_last, n_folds=3)

    evidence = {
        "schema": "forex_free_v2_data_replay_evidence_v1",
        "cycle_id": "FOREX-FREE-V2",
        "producer": "A3_DATA_AUTHORITY",
        "lane": "F2-P2 data, clock and DST replay",
        "authority_rule": "V2 reuses the authorized FOREX-FREE-V1 snapshot byte-for-byte; "
                          "NO new download; S1 never listed/opened/hashed/copied; "
                          "no data file committed",
        "measured_at_utc": dt.datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "snapshot_root": DA.SNAPSHOT_ROOT,
        "v2_data_subdir": DA.V2_DATA_SUBDIR,
        "replay": {
            "manifest": replay["manifest_path"],
            "manifest_schema": replay["manifest_schema"],
            "manifest_staged_utc": replay["manifest_staged_utc"],
            "W1": replay["W1"],
            "byte_identical_exec_repro_declared": replay["byte_identical_exec_repro_declared"],
            "exec_vs_repro_disagreements": replay["exec_vs_repro_disagreements"],
            "checked": replay["checked"],
            "matched": replay["matched"],
            "mismatches": replay["mismatches"],
            "missing": replay["missing"],
            "fail_closed_ok": replay["fail_closed_ok"],
            "files": replay["files"],
        },
        "pair_universe": PAIRS,
        "h1_grid_audit": pair_audits,
        "observed_h1_range": {"first_utc": iso(observed_first), "last_utc": iso(observed_last)},
        "fold_boundaries_utc": [iso(b) for b in folds],
        "fold_rule": "3 chronological folds over the observed H1 range; entries within "
                     "warmup_hours after a fold start are purged (purge_ok)",
        "dst_probe": {
            "method": "zoneinfo-exact via research.assets.forex.sessions (V1 machinery); "
                      "weekly window Sun 21:00 America/New_York -> Fri 16:00 America/New_York, "
                      "half-open [open, close)",
            "note": "the 16:00-New-York -> UTC mapping depends only on the New York offset "
                    "(EST->21:00Z, EDT->20:00Z); the EU transitions do not alter it, including "
                    "inside the brief EU/US desync windows (asserted in tests)",
            "rows": dst_probe_table(),
        },
        "completed_bar_rule": "stamps are bar-open UTC instants; bar i is complete from T+1h; "
                              "signals on bar i are actionable at bar i+1 open (one-event lag); "
                              "tier-2.0 stress adds one further event of fill delay",
        "missing_bar_rule": "missing inside-open bar => NO_TRADE fail-closed; never fill-forward",
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as handle:
        json.dump(evidence, handle, indent=1)
    print("wrote", OUT)
    for pair, audit in pair_audits.items():
        print(f"{pair}: n_bars={audit['n_bars']} dup={audit['duplicates']} "
              f"missing_inside_open={audit['inside_open_missing']} "
              f"out_of_session_present={audit['out_of_session_present']}")
    print("replay:", replay["checked"], "checked /", replay["matched"], "matched /",
          replay["mismatches"], "mismatch /", replay["missing"], "missing")
    print("folds:", evidence["fold_boundaries_utc"])


if __name__ == "__main__":
    main()
