"""A7-R2 adversarial regression D4: unknown rtype MID-STREAM in a DBN
file (typed error, never a silent skip), and D5: walkforward horizon 5 /
3 folds on a 60-day calendar (disjoint emitted windows, labels matured).

D4 builds a legal DBN v3 file: valid metadata -> valid ohlcv-1d records
-> ONE record with an rtype this package does not implement -> more
valid records behind it. decode must raise UnknownRecordTypeError
referencing the unknown rtype; nothing may be silently skipped.

D5: weekday calendar 2026-01-01..2026-03-31 (~63 sessions; truncated to
the first 60 weekday sessions), horizon 5, 3 folds, train_frac 0.7:
  * emitted TEST cell sets pairwise disjoint;
  * every emitted test cell's label window (ci + 5 inclusive) fits
    inside its fold's test_end (LABEL_CENSORED otherwise — count them);
  * no cell past test_end is emitted (POST_TEST_WINDOW audited).
"""
import datetime as dt
import json
import struct
import sys
import tempfile
from pathlib import Path

OUT = {}

# ------------------------------------------------------------------ D4
def d4():
    from futbt.dbn import spec as S
    from futbt.dbn import wire as W

    ts0 = 1_700_000_000_000_000_000
    good = S.pack_record(S.RTYPE_OHLCV_1D, ts0,
                         {"open": 100 * 10**9, "high": 101 * 10**9,
                          "low": 99 * 10**9, "close": 100 * 10**9,
                          "volume": 500}, instrument_id=1)
    # an rtype this package does not implement (MBP-10 = 0x0a is real in
    # DBN but intentionally unsupported here -> the fail-closed path)
    unknown_rtype = 0x0A
    assert unknown_rtype not in S.SUPPORTED_RTYPES
    words = 80 // 4          # plausible mid-stream length
    body = b"\x00" * (words * 4 - S.HEADER_SIZE)
    hdr = struct.pack(S.HEADER_FMT, words, unknown_rtype, 1, 1, ts0 + 1)
    bad = hdr + body

    meta = W.DbnMetadata(schema=S.RTYPE_OHLCV_1D and S.SCHEMA_OHLCV_1D
                         or S.SCHEMA_OHLCV_1D,
                         start=ts0, symbols=["NQZ6"])
    res = {}
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "midstream_unknown.dbn"
        W.write_dbn(p, meta, [(S.RTYPE_OHLCV_1D, good),
                              (unknown_rtype, bad),
                              (S.RTYPE_OHLCV_1D, good)])
        try:
            W.read_dbn(p)
            res["raised"] = False
            res["error"] = "NO ERROR — silent acceptance (FAIL)"
        except S.UnknownRecordTypeError as e:
            res["raised"] = True
            res["error_type"] = type(e).__name__
            res["rtype_reported"] = getattr(e, "rtype", None)
            res["rtype_matches"] = getattr(e, "rtype", None) == unknown_rtype
        except Exception as e:      # wrong error class = still fail
            res["raised"] = True
            res["error_type"] = f"WRONG TYPE {type(e).__name__}: {e}"
            res["rtype_matches"] = False
        # control: the same file WITHOUT the bad record decodes cleanly
        p2 = Path(td) / "clean.dbn"
        W.write_dbn(p2, meta, [(S.RTYPE_OHLCV_1D, good),
                               (S.RTYPE_OHLCV_1D, good)])
        m, recs = W.read_dbn(p2)
        res["control_clean_file"] = len(recs) == 2
    res["PASS"] = (res["raised"] and res.get("rtype_matches")
                   and res["control_clean_file"])
    return res


# ------------------------------------------------------------------ D5
def d5():
    from futbt.calendarx import WeekdayCalendar
    from futbt.walkforward import ExposureCell, WalkForwardPlanner

    cal = WeekdayCalendar(dt.date(2026, 1, 1), dt.date(2026, 3, 31))
    sessions = cal.sessions()[:60]      # exactly 60 sessions
    H = 5
    pl = WalkForwardPlanner(list(sessions), true_horizon_sessions=H,
                            embargo_sessions=0)
    folds = pl.plan(n_folds=3, train_frac=0.7)
    cells = [ExposureCell(symbol="ES", session=s) for s in sessions]
    pos = {d: i for i, d in enumerate(sessions)}
    emitted = {}
    report = []
    for f in folds:
        tr, te = pl.apply_purge_embargo(f, cells)
        te_s = [c.session for c in te]
        emitted[f.fold_id] = set(te_s)
        immature = [s for s in te_s if pos[s] + H > pos[f.test_end]]
        outside = [s for s in te_s if s > f.test_end]
        drops = {}
        for d in f.dropped:
            drops[f"{d.phase}:{d.reason}"] = drops.get(
                f"{d.phase}:{d.reason}", 0) + 1
        report.append({
            "fold": f.fold_id,
            "planned_test": [f.test_start.isoformat(),
                             f.test_end.isoformat()],
            "n_emitted": len(te_s),
            "emitted_range": [min(te_s).isoformat(), max(te_s).isoformat()]
            if te_s else None,
            "n_label_immature_emitted": len(immature),
            "n_outside_test_end": len(outside),
            "drops": drops,
        })
    overlaps = []
    ids = sorted(emitted)
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            inter = emitted[ids[i]] & emitted[ids[j]]
            if inter:
                overlaps.append([ids[i], ids[j], len(inter)])
    res = {
        "n_sessions": len(sessions),
        "horizon": H,
        "folds": report,
        "pairwise_overlaps": overlaps,
    }
    res["PASS"] = (
        not overlaps
        and all(r["n_label_immature_emitted"] == 0 for r in report)
        and all(r["n_outside_test_end"] == 0 for r in report))
    return res


if __name__ == "__main__":
    OUT["D4_unknown_rtype_midstream"] = d4()
    OUT["D5_wf_horizon5_3folds_60days"] = d5()
    ok = OUT["D4_unknown_rtype_midstream"]["PASS"] and OUT["D5_wf_horizon5_3folds_60days"]["PASS"]
    OUT["PASS"] = ok
    print(json.dumps(OUT, indent=1, default=str))
    sys.exit(0 if ok else 1)
