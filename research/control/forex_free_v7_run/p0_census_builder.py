#!/usr/bin/env python3
"""FOREX-FREE-V7 P0 (A3 data-authority lane): spillover coverage census.

Frozen semantics (this file + the artifact it emits are the P0 authority):
- Source clocks: V6 p3_conditioning_clocks_v6.json (246 in-S0 events,
  TRUE-UTC-qualified available_time_utc; CA v3 TRUE-UTC pins, GB/AU day
  precision 23:59:59Z end-of-day bound, NZ offset-qualified instants with
  the V5 flat +12:00 convention caveat recorded in the clocks file).
- S0 window 2018-04-04..2025-07-24 (frozen from the V6 run contract).
- Non-reporting pairs per calendar: the 7 free-data pairs minus every pair
  containing the reporting economy's currency.
- Reaction window W per event, by evidenced precision:
    INSTANT (CA v3, NZ offset-qualified): W = [T, T+24h]
    DAY (GB, AU; bound 23:59:59Z): conservative LATER — W = [first 00:00Z
    strictly after T, +24h] (no same-day intraday reaction claim without an
    evidenced intraday stamp).
- Pair bookable on an event iff >= 12 one-hour bars fall inside W
  (error-response provider files contribute zero bars; a pair with zero
  bars anywhere in the S0 window would be listed dead and excluded
  fail-closed — none exists this cycle).
- Funded decision window: bookable reaction window whose FIRST daily
  16:00-NY (DST-correct) decision instant at/after W-end falls inside S0
  and has a same-day daily bar for that pair.
- Price data: inherited V1-staged snapshot (gitignored) read from the V6
  closed integration worktree; manifest sha fe2155c0... (156 files,
  byte-verified chain V4 P2 -> V5 P2 -> V6 P2). Nothing re-downloaded.
- FRED: key presence re-measured in this process; if absent, lane 2 stays
  DATA_BLOCKED_VALID and NO probe call is made (plan section 5).

No PnL anywhere. Census only. S1 untouched.
"""
import json, glob, os, hashlib
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

ROOT = '/Users/hoangminhlong/my-quantitative'
V6_WT = f'{ROOT}/.worktrees/forex-free-v6/integration'
V7_WT = f'{ROOT}/.worktrees/forex-free-v7/integration'
DATA = f'{V6_WT}/data_raw/forex_free_v1'

PAIRS = ['EURUSD','GBPUSD','USDJPY','USDCAD','AUDUSD','NZDUSD','USDCHF']
CCY = {'EURUSD':('EUR','USD'),'GBPUSD':('GBP','USD'),'USDJPY':('USD','JPY'),
       'USDCAD':('USD','CAD'),'AUDUSD':('AUD','USD'),'NZDUSD':('NZD','USD'),
       'USDCHF':('USD','CHF')}
ECON_CCY = {'GB':'GBP','CA':'CAD','AU':'AUD','NZ':'NZD'}
NY = ZoneInfo('America/New_York')
S0_START = datetime(2018,4,4,tzinfo=timezone.utc)
S0_END = datetime(2025,7,24,tzinfo=timezone.utc)

def sha256(path):
    h = hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda: f.read(1<<20), b''):
            h.update(chunk)
    return h.hexdigest()

def parse_iso(s):
    return datetime.fromisoformat(s.replace('Z','+00:00')).astimezone(timezone.utc)

def load_1h(pair):
    ts = []
    err_files = 0; ok_files = 0
    for fp in sorted(glob.glob(f'{DATA}/{pair}_1h_*.json')):
        with open(fp) as f: d = json.load(f)
        vals = d.get('values')
        if not vals:
            err_files += 1; continue
        ok_files += 1
        for v in vals:
            ts.append(datetime.strptime(v['datetime'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc))
    ts.sort()
    return ts, ok_files, err_files

def load_1d(pair):
    ts = []
    for fp in glob.glob(f'{DATA}/{pair}_1day_*.json'):
        with open(fp) as f: d = json.load(f)
        vals = d.get('values')
        if not vals: continue
        for v in vals:
            ts.append(datetime.strptime(v['datetime'][:10], '%Y-%m-%d').replace(tzinfo=timezone.utc))
    ts.sort()
    return ts

def bsearch_ge(arr, x):
    lo, hi = 0, len(arr)
    while lo < hi:
        mid = (lo+hi)//2
        if arr[mid] < x: lo = mid+1
        else: hi = mid
    return lo

def next_1600ny(after_utc):
    """First daily 16:00 America/New_York decision instant strictly at/after after_utc."""
    d = after_utc.astimezone(NY).date()
    for k in range(4):
        cand = datetime.combine(d + timedelta(days=k), datetime.min.time(), tzinfo=NY).replace(hour=16)
        if cand.astimezone(timezone.utc) >= after_utc:
            return cand.astimezone(timezone.utc)
    return None

def main():
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    # FRED re-measurement (presence only; no probe call when absent)
    env_path = f'{ROOT}/.env'
    fred_lines = []
    if os.path.exists(env_path):
        with open(env_path) as f:
            fred_lines = [l for l in f if l.split('=')[0].strip() == 'FRED_API_KEY']
    fred_present = bool(fred_lines)
    fred = {"measured_at_utc": now,
            "env_file_exists": os.path.exists(env_path),
            "fred_api_key_lines": len(fred_lines),
            "verdict": "KEY_PRESENT" if fred_present else "KEY_ABSENT",
            "probe_call_made": False,
            "lane_2": "UNLOCKED" if fred_present else "DATA_BLOCKED_VALID (carried; owner door: free signup, owner places key in gitignored .env)"}

    # pin re-verification at P0 time
    pins = [
      ("clocks", f'{V6_WT}/research/control/forex_free_v6_run/p3_conditioning_clocks_v6.json', '6f2a9a85aad4cb2918c5c09639500a097d2abc324115287797e58b2ce3a0ab41'),
      ("GB_cal", f'{V6_WT}/research/control/forex_free_v5_run/gb_ons_cpi_release_dates.json', 'aad19697ba3d10b56e498d836eeae48d78ebb47a08ff203bab2f32c19b6cd00d'),
      ("CA_v3_cal", f'{V6_WT}/research/control/forex_free_v6_run/ca_statcan_cpi_release_dates_v3.json', '0f1a93282348cef94aecf2b9a8da275945e809643e3646f551b2df916e2af7b3'),
      ("AU_cal", f'{V6_WT}/research/control/forex_free_v5_run/au_abs_cpi_release_dates.json', '42a4e4a36dbb6a955f7acf1aa9e3ff38b7436db775753bfbd7ad362d21bff7d1'),
      ("NZ_cal", f'{V6_WT}/research/control/forex_free_v5_run/nz_statsnz_cpi_release_dates.json', '62f82c23232402f46dab854ede8023ef77dc7637af1d156f0dd748ea249027f7'),
      ("ledger_250", f'{V6_WT}/research/control/forex_free_v5_run/announcement_ledger_v5_extension.jsonl', 'cf1f01a7ec2d3d7506892c045139910937147df49d3742cc4ec72b36d20fd902'),
      ("emu_v2_repair", f'{V6_WT}/research/control/forex_free_v6_run/announcement_ledger_v6_emu_repair.jsonl', '6be0cb242f5d1e94a2226d7dbbd518d36278cb800bd5a9486eaa4dada9d6a278'),
      ("staged_manifest", f'{V6_WT}/research/control/forex_free_v1_run/staged_data_manifest.json', 'fe2155c0ef51bcac32262ebaf1c7d98fc724727eca1dda8b6644012ad854c460'),
    ]
    pin_results = []
    all_ok = True
    for name, path, pinned in pins:
        got = sha256(path) if os.path.exists(path) else None
        ok = (got == pinned)
        all_ok &= ok
        pin_results.append({"pin": name, "match": ok, "sha256": got})

    bars = {}; bars_meta = {}
    daily = {}
    dead_pairs = []
    for p in PAIRS:
        ts, okf, errf = load_1h(p)
        bars[p] = ts
        dd = load_1d(p)
        daily[p] = dd
        bars_meta[p] = {"one_h_bars": len(ts), "ok_files": okf, "error_files": errf,
                        "span_start": ts[0].isoformat() if ts else None,
                        "span_end": ts[-1].isoformat() if ts else None,
                        "daily_bars": len(dd),
                        "daily_span_start": dd[0].isoformat() if dd else None,
                        "daily_span_end": dd[-1].isoformat() if dd else None}
        if not ts or not dd:
            dead_pairs.append(p)

    with open(f'{V6_WT}/research/control/forex_free_v6_run/p3_conditioning_clocks_v6.json') as f:
        clocks_doc = json.load(f)
    clocks = clocks_doc['clocks']

    precision_class = {}
    per_calendar = {}
    for econ in ('GB','CA','AU','NZ'):
        ev = [c for c in clocks if c['economy'] == econ]
        nonrep = [p for p in PAIRS if ECON_CCY[econ] not in CCY[p]]
        rows = []
        for c in ev:
            T = parse_iso(c['available_time_utc'])
            pc = 'INSTANT' if ('T' in c['available_time_utc'] and '23:59:59' not in c['available_time_utc']) else 'DAY'
            if econ == 'NZ':
                pc = 'INSTANT_OFFSET_QUALIFIED'  # V5 +12:00 convention caveat in clocks file
            if econ in ('GB','AU'):
                pc = 'DAY'
            if econ == 'CA':
                pc = 'INSTANT_TRUE_UTC_V3'
            precision_class[c['decision_date'] + ':' + econ] = pc
            w0 = T if pc.startswith('INSTANT') else (T.replace(hour=0,minute=0,second=0) + timedelta(days=1))
            w1 = w0 + timedelta(hours=24)
            booked_pairs = []
            for p in nonrep:
                arr = bars[p]
                i = bsearch_ge(arr, w0)
                n = 0
                while i < len(arr) and arr[i] <= w1:
                    n += 1; i += 1
                if n >= 12:
                    # funded decision: first 16:00-NY decision >= w1, in S0, daily bar as-of it
                    # (provider daily bars are stamped D 00:00Z = FX day D; the freshest CLOSED
                    # bar at a day-D 16:00-NY instant is the D-stamped one — existence check
                    # compares the bar's own stamp date to the decision's NY date)
                    dec = next_1600ny(w1)
                    funded = False
                    if dec is not None and S0_START <= dec <= S0_END:
                        dd_ = dec.astimezone(NY).date()
                        stamp = datetime.combine(dd_, datetime.min.time(), tzinfo=timezone.utc)
                        j = bsearch_ge(daily[p], stamp)
                        if j < len(daily[p]) and daily[p][j] == stamp:
                            funded = True
                    if funded:
                        booked_pairs.append(p)
            rows.append({"decision_date": c['decision_date'], "available_time_utc": c['available_time_utc'],
                         "precision": pc, "booked_pairs": booked_pairs, "n_booked": len(booked_pairs)})
        per_pair_counts = {p: sum(1 for r in rows if p in r['booked_pairs']) for p in nonrep}
        per_calendar[econ] = {
            "events_in_S0": len(ev),
            "nonrep_pairs": nonrep,
            "events_any_pair_bookable": sum(1 for r in rows if r['n_booked'] >= 1),
            "events_4of6_bookable": sum(1 for r in rows if r['n_booked'] >= 4),
            "events_all6_bookable": sum(1 for r in rows if r['n_booked'] == 6),
            "decision_windows_funded_total": sum(r['n_booked'] for r in rows),
            "per_pair_funded_windows": per_pair_counts,
            "rows": rows,
        }

    totals = {
        "in_S0_events": sum(per_calendar[e]['events_in_S0'] for e in per_calendar),
        "events_any_pair": sum(per_calendar[e]['events_any_pair_bookable'] for e in per_calendar),
        "events_4of6": sum(per_calendar[e]['events_4of6_bookable'] for e in per_calendar),
        "events_all6": sum(per_calendar[e]['events_all6_bookable'] for e in per_calendar),
        "decision_windows_funded": sum(per_calendar[e]['decision_windows_funded_total'] for e in per_calendar),
    }

    verdict = "FUNDED" if totals['decision_windows_funded'] >= 200 and totals['events_4of6'] >= 100 else ("THIN" if totals['decision_windows_funded'] > 0 else "BLOCKED_DATA")

    out = {
      "schema": "forex_free_v7_p0_census_v1",
      "measured_at_utc": now,
      "producer": "A1_FOREX_V7_CONTROLLER (P0 executed in A1 thread from plan §4; A3 semantics)",
      "authority": "plans/PLAN_forex_v7.md §4 P0; census published BEFORE D1",
      "fred": fred,
      "pins_reverified_at_p0": {"all_match": all_ok, "results": pin_results},
      "price_data_inheritance": {
        "source": "V6 closed integration worktree data_raw/forex_free_v1 (gitignored snapshot, never re-downloaded)",
        "manifest": "research/control/forex_free_v1_run/staged_data_manifest.json fe2155c0 (156 files; byte-verified chain V4 P2 -> V5 P2 -> V6 P2)",
        "per_pair_meta": bars_meta,
        "dead_or_nodata_pairs": dead_pairs,
      },
      "frozen_semantics": {
        "nonrep_rule": "7 free-data pairs minus every pair containing the reporting economy currency (US is a non-reporting economy: US calendar OUT since V5)",
        "reaction_window": "INSTANT (CA v3 TRUE-UTC, NZ offset-qualified): [T, T+24h]; DAY (GB, AU 23:59:59Z bound): conservative LATER [next 00:00Z, +24h]",
        "bookable_bar_rule": ">= 12 one-hour bars inside W (error-response provider files contribute zero bars)",
        "funded_decision_rule": "first 16:00-NY DST-correct decision instant >= W-end, inside S0 2018-04-04..2025-07-24, with a same-day daily bar",
        "nz_caveat": "NZ instants carry the V5 flat +12:00 offset convention; on NZDT dates the expressed instant is off by 1h — recorded, conservative direction is LATER; P2 clocks must carry the caveat flag",
      },
      "per_calendar": {e: {k: v for k, v in per_calendar[e].items() if k != 'rows'} for e in per_calendar},
      "rows_by_calendar": per_calendar,
      "totals": totals,
      "census_verdict": verdict,
      "lane_consequences": {
        "lane_1_spillover": "FUNDED" if totals['decision_windows_funded'] > 0 else "BLOCKED_DATA (axis dies in P0 per plan §2)",
        "lane_2_realrate": fred['lane_2'],
        "lane_3_open": "open; same data authority applies",
      },
      "pnl_anywhere": False,
      "s1": "SEALED_UNTOUCHED",
    }
    out_path = f'{V7_WT}/research/control/forex_free_v7_run/p0_census_v7.json'
    with open(out_path, 'w') as f:
        json.dump(out, f, indent=1)
    print(json.dumps({k: out[k] for k in ('fred','pins_reverified_at_p0','totals','census_verdict','lane_consequences')}, indent=1))
    print(f"\nwritten {out_path}\nsha256={sha256(out_path)}")

if __name__ == '__main__':
    main()
