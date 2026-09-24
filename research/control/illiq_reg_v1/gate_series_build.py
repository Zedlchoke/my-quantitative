"""ILLIQ-REG-V1 gate-series build (gate-sequence step 3; HEAVY: run under the
global heavy lock via researchctl, see handbook SS8).

Modes:
  --check-coverage-only   bootstrap-safe: verifies per-fold funding scan
                          coverage (small JSONs) and catalog presence; writes
                          coverage_status.json. No parquet scan, no lock.
  default (full build)    reads the READ-ONLY CHR3F catalogs (parquet), builds
                          the daily PIT DV-share / BTC closes, applies the
                          FROZEN gate_module walk, writes gate_series.json +
                          sha256 digests of every input. The 200 random-gate
                          control permutations are generated at cell time
                          from this series via gate_module.random_gate_
                          permutations (they gate PnL surfaces, not the
                          observables), so they are not serialized here.

Folds: S0R (wired catalog_live_crypto_s0r, COMPLETE) and FWD (observables
from catalog_live_crypto_a20 as an UNPINNED-CATALOG DIAGNOSTIC — the wiring
law keeps FOLD_WIRING["FWD"]["catalog"] = None until the explicit catalog
pinning step; see FWD_CATALOG_DISCLOSURE in the artifact).

Reads ONLY wiring-law absolute paths; never writes outside the
research/control/illiq_reg_v1/ namespace; never modifies CHR3F files.
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import gate_module as gm  # noqa: E402
import wiring  # noqa: E402

ALL_SYMS = wiring.SYMS
GATE_FOLDS = ("Y2021", "Y2024P", "S0R", "FWD")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_coverage() -> dict:
    """Bootstrap-safe wiring proof: scans exist, catalogs exist, per-fold
    funding coverage > 0 for all 20 symbols. Fail-closed on any violation."""
    status = {"checked_at": dt.datetime.now(dt.timezone.utc).isoformat(),
              "folds": {}}
    for fold in GATE_FOLDS:
        w = wiring.FOLD_WIRING[fold]
        w0, w1 = wiring.FOLD_WINDOWS[fold]
        entry = {"funding_scan": w["funding_scan"].name,
                 "window": [w0, w1],
                 "catalog": str(w["catalog"]) if w["catalog"] else None}
        if w["catalog"] is not None and not Path(w["catalog"]).exists():
            raise wiring.WiringError(f"{fold}: catalog missing: {w['catalog']}")
        # Coverage law (wiring.py): S0R/FWD require the FULL 20-symbol list;
        # pre-window folds require only the in-window PIT-listed subset
        # (not-yet-listed names legitimately have zero rows).
        if fold in ("S0R", "FWD"):
            required = ALL_SYMS
        else:
            required = sorted(wiring.listed_symbols_proxy(
                w["funding_scan"], w1))
        counts = wiring.verify_funding_scan_coverage(
            w["funding_scan"], required, w0, w1)
        entry["required_symbols"] = len(required)
        entry["funding_rows"] = counts
        entry["funding_rows_total"] = sum(counts.values())
        status["folds"][fold] = entry
    return status


# --- full build (NOT_RUN at bootstrap; heavy lock required) --------------------

def catalog_parquet_files(catalog: Path, sym: str) -> list[Path]:
    directory = catalog / "data" / "binance_bar" / \
        f"{sym}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"
    files = sorted(glob.glob(str(directory / "*.parquet")))
    if not files:
        raise wiring.WiringError(f"no parquet bars for {sym} in {catalog}")
    return [Path(fp) for fp in files]


def daily_dv_from_catalog(catalog: Path, sym: str, day_lo: dt.date,
                          day_hi: dt.date,
                          files: list[Path] | None = None) -> dict:
    """DV per completed daily block from the staged 15m parquet bars."""
    import pyarrow.parquet as pq
    if files is None:
        files = catalog_parquet_files(catalog, sym)
    per: dict[dt.date, float] = {}
    for fp in files:
        t = pq.read_table(fp, columns=["ts_event", "quote_volume"])
        ts = t.column("ts_event").to_pylist()
        qv = t.column("quote_volume").to_pylist()
        for i in range(len(ts)):
            day = dt.datetime.fromtimestamp(int(ts[i]) / 1e9,
                                            dt.timezone.utc).date()
            if day_lo <= day < day_hi:
                per[day] = per.get(day, 0.0) + float(qv[i])
    return per


def daily_closes_from_catalog(catalog: Path, sym: str, day_lo: dt.date,
                              day_hi: dt.date,
                              files: list[Path] | None = None) -> dict:
    import pyarrow.parquet as pq
    if files is None:
        files = catalog_parquet_files(catalog, sym)
    per: dict[dt.date, float] = {}
    for fp in files:
        t = pq.read_table(fp, columns=["ts_event", "close"])
        ts = t.column("ts_event").to_pylist()
        cl = t.column("close").to_pylist()
        for i in range(len(ts)):
            day = dt.datetime.fromtimestamp(int(ts[i]) / 1e9,
                                            dt.timezone.utc).date()
            if not (day_lo <= day < day_hi):
                continue
            raw = cl[i]
            val = (int.from_bytes(raw, "little", signed=True) / 10 ** 16
                   if isinstance(raw, (bytes, bytearray)) else float(raw))
            per[day] = val  # last completed 15m bar of the day wins
    return per


# Folds built by this step. S0R uses its wired catalog. FWD observables are
# read from catalog_live_crypto_a20 as a PRELAUNCH DIAGNOSTIC ONLY: the wiring
# law keeps FOLD_WIRING["FWD"]["catalog"] = None (identity not yet verified;
# pinned by tests/test_wiring.py), so no FWD strategy stage may run off this —
# the gate series rows for FWD carry that disclosure verbatim.
FOLD_DIAG_CATALOG = {
    "S0R": lambda: wiring.FOLD_WIRING["S0R"]["catalog"],
    "FWD": lambda: wiring.CHR3F_CTRL / "catalog_live_crypto_a20",
}
FOLD_STATUS = {
    "S0R": "COMPLETE",
    "FWD": "BUILT_FROM_UNPINNED_CATALOG_DIAGNOSTIC",
}
FWD_CATALOG_DISCLOSURE = (
    "wiring.FOLD_WIRING['FWD']['catalog'] is None by law (identity not yet "
    "verified); observables computed from catalog_live_crypto_a20 (20/20 "
    "symbols, full FWD window coverage) for prelaunch diagnostics only — "
    "any FWD strategy stage still requires the explicit catalog-pinning "
    "coverage step before it may run."
)


def monday_stamps(window_start_iso: str, window_end_iso: str) -> list[dt.date]:
    """Monday 00:00:00Z dates strictly after window start, through window end.

    Local mirror of the frozen weekly_monday_stamps law (plugin schedule);
    dryrun.py asserts equality of this against the frozen schedule instants.
    """
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    st = dt.datetime.strptime(window_start_iso, fmt).replace(tzinfo=dt.timezone.utc)
    en = dt.datetime.strptime(window_end_iso, fmt).replace(tzinfo=dt.timezone.utc)
    day = st
    while day.weekday() != 0 or int(day.timestamp() * 1_000_000_000) <= int(
            st.timestamp() * 1_000_000_000):
        day += dt.timedelta(days=1)
    out: list[dt.date] = []
    while int(day.timestamp() * 1_000_000_000) <= int(en.timestamp() * 1_000_000_000):
        out.append(day.date())
        day += dt.timedelta(days=7)
    if len(out) < 2:
        raise wiring.WiringError(f"fold window {window_start_iso}..{window_end_iso} "
                                 "yields fewer than two Monday stamps")
    return out


def _stamp_data_complete(share: dict, closes: dict, stamp: dt.date) -> bool:
    """A stamp is PIT-data-complete iff the full S90 daily-block window
    ([T-90d, T): 90 completed blocks) and the full rvol30 window
    ([T-31d, T): 31 completed closes) are covered. Partial windows are NEVER
    averaged silently (conc_mean/rvol30 would otherwise return a value)."""
    s90_days = sum(1 for d in share
                   if stamp - dt.timedelta(days=90) <= d < stamp)
    rv_days = sum(1 for d in closes
                  if stamp - dt.timedelta(days=31) <= d < stamp)
    return s90_days == 90 and rv_days == 31


def _fold_observables(fold: str, files_out: list[Path]) -> dict:
    """Daily PIT DV-share + BTC daily closes for one fold, dossier semantics:
    first_day[sym] = first day with DV inside the queried load window; DV
    aggregated from completed 15m bars; last 15m close of the day wins."""
    w0, w1 = wiring.FOLD_WINDOWS[fold]
    pre_iso, ext_iso = wiring.bars_load_bounds(w0, w1)
    day_lo = dt.datetime.strptime(pre_iso, "%Y-%m-%dT%H:%M:%SZ").date()
    day_hi = dt.datetime.strptime(ext_iso, "%Y-%m-%dT%H:%M:%SZ").date()
    catalog = FOLD_DIAG_CATALOG[fold]()
    dv: dict[tuple[dt.date, str], float] = {}
    first_day: dict[str, dt.date] = {}
    sym_files: dict[str, list[Path]] = {}
    for sym in wiring.SYMS:  # fixed SYMS order -> deterministic fsum input order
        fs = catalog_parquet_files(catalog, sym)
        sym_files[sym] = fs
        files_out.extend(fs)
        per = daily_dv_from_catalog(catalog, sym, day_lo, day_hi, files=fs)
        if not per:
            raise wiring.WiringError(
                f"{fold}: zero daily DV blocks for {sym} in {catalog.name} "
                "over load window — B2 fail-closed")
        first_day[sym] = min(per)
        for day, v in per.items():
            dv[(day, sym)] = v
    btc_files = sym_files["BTCUSDT"]
    closes = daily_closes_from_catalog(catalog, "BTCUSDT", day_lo, day_hi,
                                       files=btc_files)
    share = gm.daily_dv_share(dv, first_day)
    if not share:
        raise wiring.WiringError(f"{fold}: empty PIT DV-share series")
    # eligible-symbol census per day (diagnostics; same eligibility law)
    elig_n: dict[dt.date, int] = {}
    for day in sorted(share):
        elig_n[day] = sum(
            1 for s in first_day
            if first_day[s] <= day - dt.timedelta(days=gm.LISTING_AGE_DAYS)
            and dv.get((day, s)))
    return {
        "catalog": catalog,
        "share": share,
        "closes": closes,
        "elig_n": elig_n,
        "first_share_day": min(share),
        "last_share_day": max(share),
        "first_close_day": min(closes),
        "last_close_day": max(closes),
        "bars_load_bounds": [pre_iso, ext_iso],
    }


def _cross_check_single_shot(s0r_rows: dict) -> dict:
    """Soft provenance cross-check against the frozen dossier's descriptive
    single-shot replay (input evidence; never gates this build). s90 must
    agree to float precision (same catalog, same fsum semantics); rvol30 is
    EXPECTED to differ: gate_module.rvol30 is strictly PIT (closes < stamp)
    while the dossier's descriptive code read closes <= stamp."""
    path = HERE.parent / "illiq_reg_gate_v1_draft" / \
        "pit_conc_gate_single_shot.json"
    out: dict = {"available": False, "path": str(path)}
    if not path.exists():
        return out
    doc = json.loads(path.read_text())
    rows = doc.get("stamp_rows", {})
    s90_diffs = []
    state_match = 0
    state_total = 0
    for iso, row in sorted(s0r_rows.items()):
        theirs = rows.get(iso)
        if not theirs:
            continue
        if theirs.get("s90") is not None and row["s90"] is not None:
            s90_diffs.append(abs(float(theirs["s90"]) - float(row["s90"])))
        state_total += 1
        if (bool(theirs.get("conc_state")) == row["v1_state"]
                and bool(theirs.get("vol_state")) == row["v2_state"]):
            state_match += 1
    out.update({
        "available": True,
        "s0r_s90_max_abs_diff": max(s90_diffs) if s90_diffs else None,
        "s0r_states_match": state_match,
        "s0r_states_total": state_total,
        "rvol_semantics_note": "gate_module.rvol30 uses completed closes "
            "strictly before the stamp (PIT); the dossier's descriptive "
            "replay read closes <= stamp, so rvol values differ by that "
            "one-day shift by design.",
    })
    return out


def full_build(out_path: Path) -> dict:
    """Full gate series over the S0R and FWD folds from the frozen catalogs.

    Requires the global heavy lock (researchctl); refuses without it.
    Deterministic: no wall-clock fields in the artifact; same catalog bytes
    -> byte-identical gate_series.json. One continuous hysteresis walk over
    S0R stamps then FWD stamps (state carries across the fold boundary, as
    in the dossier walk); per-fold rows are split out of that single walk.
    """
    import sys as _sys
    _sys.path.insert(0, "/Users/hoangminhlong/my-quantitative")
    from research.governance import heavy_lock as _hl
    _verdict = _hl.inspect().get("verdict")
    if _verdict != "HELD_PROVEN":
        raise wiring.WiringError(
            f"heavy lock not held (verdict {_verdict}): run under "
            "full_build_locked.py wrapper (researchctl discipline)")

    files_read: list[Path] = []
    obs: dict[str, dict] = {}
    for fold in ("S0R", "FWD"):
        obs[fold] = _fold_observables(fold, files_read)

    # --- stamps: (s90 | None, rvol | None), fail-closed on partial windows --
    fold_stamps: dict[str, list[dt.date]] = {}
    walk_rows: dict[dt.date, tuple] = {}
    stamp_meta: dict[dt.date, dict] = {}
    for fold in ("S0R", "FWD"):
        o = obs[fold]
        stamps = monday_stamps(*wiring.FOLD_WINDOWS[fold])
        fold_stamps[fold] = stamps
        for T in stamps:
            complete = _stamp_data_complete(o["share"], o["closes"], T)
            if fold == "S0R" and not complete:
                raise wiring.WiringError(
                    f"S0R stamp {T} lacks full PIT window coverage — "
                    "fail-closed (wired fold must be complete)")
            if complete:
                s90 = gm.s90_at(o["share"], T)
                rv = gm.rvol30(o["closes"], T)
                if s90 is None or rv is None:
                    raise wiring.WiringError(
                        f"{fold} stamp {T}: complete window but None "
                        "observable — contract violation")
            else:
                s90 = rv = None  # state carries; row flagged data_incomplete
            walk_rows[T] = (s90, rv)
            stamp_meta[T] = {"fold": fold, "data_complete": complete}

    walk = gm.gate_walk(walk_rows)

    # --- per-day rows per fold (state carried from the continuous walk) -----
    def _state_at(day: dt.date) -> tuple[bool, bool, bool]:
        prior = [t for t in walk_rows if t <= day]
        if not prior:
            return gm.INITIAL_STATE, gm.INITIAL_STATE, bool(
                gm.INITIAL_STATE and gm.INITIAL_STATE)
        w = walk[max(prior)]
        return w.v1_state, w.v2_state, w.gated

    folds_out: dict[str, dict] = {}
    for fold in ("S0R", "FWD"):
        o = obs[fold]
        w0, w1 = wiring.FOLD_WINDOWS[fold]
        d0 = dt.datetime.strptime(w0, "%Y-%m-%dT%H:%M:%SZ").date()
        d1 = dt.datetime.strptime(w1, "%Y-%m-%dT%H:%M:%SZ").date()
        stamps = fold_stamps[fold]
        per_day = []
        day = d0
        while day < d1:
            v1, v2, gated = _state_at(day)
            T_meta = stamp_meta.get(day)
            per_day.append({
                "date": day.isoformat(),
                "dv_share": o["share"].get(day),
                "rvol30": gm.rvol30(o["closes"], day),
                "s90": gm.s90_at(o["share"], day),
                "is_stamp": day in walk_rows,
                "data_complete": bool(T_meta["data_complete"]) if T_meta
                                 else day <= o["last_share_day"],
                "v1_state": v1,
                "v2_state": v2,
                "gated": gated,
            })
            day += dt.timedelta(days=1)
        stamp_rows = [walk[T] for T in stamps]
        folds_out[fold] = {
            "status": FOLD_STATUS[fold],
            "window": [w0, w1],
            "bars_load_bounds": o["bars_load_bounds"],
            "catalog": {
                "name": o["catalog"].name,
                "wired_in_wiring_law": fold == "S0R",
            },
            "obs_series": {
                "first_share_day": o["first_share_day"].isoformat(),
                "last_share_day": o["last_share_day"].isoformat(),
                "first_close_day": o["first_close_day"].isoformat(),
                "last_close_day": o["last_close_day"].isoformat(),
                "days_with_share": len(o["share"]),
                "eligible_symbols_min": min(o["elig_n"].values()),
                "eligible_symbols_mean": (math.fsum(o["elig_n"].values())
                                          / len(o["elig_n"])),
            },
            "stamps_total": len(stamps),
            "stamps_data_complete": sum(
                1 for T in stamps if stamp_meta[T]["data_complete"]),
            "stamps_gated_on": sum(1 for r in stamp_rows if r.gated),
            "stamps_gated_off": sum(1 for r in stamp_rows if not r.gated),
            "disclosure": (None if fold == "S0R" else FWD_CATALOG_DISCLOSURE),
            "per_day": per_day,
        }

    # --- digests: every input file + the frozen spec modules ----------------
    def _sha(p: Path) -> str:
        return sha256_file(p)

    digests_files = {}
    for fp in sorted(set(files_read)):
        digests_files[str(fp.relative_to(wiring.CHR3F_CTRL))] = _sha(fp)
    payload = {
        "schema": "illiq_reg_v1.gate_series@1",
        "cycle_id": gm.CYCLE_ID,
        "spec": {
            "module": "gate_module.py",
            "spec_sha256": _sha(HERE / "gate_module.py"),
            "wiring_sha256": _sha(HERE / "wiring.py"),
            "constants": {
                "band_on_s90": gm.BAND_ON_S90,
                "band_off_s90": gm.BAND_OFF_S90,
                "vol_floor": gm.VOL_FLOOR,
                "vol_hyst_frac": gm.VOL_HYST_FRAC,
                "vol_off": gm.VOL_OFF,
                "initial_state": gm.INITIAL_STATE,
                "conc_window_days": gm.CONC_WINDOW_DAYS,
                "s90_window_days": gm.S90_WINDOW_DAYS,
                "rvol_window": gm.RVOL_WINDOW,
                "listing_age_days": gm.LISTING_AGE_DAYS,
            },
        },
        "walk": {
            "initial_state": gm.INITIAL_STATE,
            "note": "single continuous hysteresis walk over S0R stamps then "
                    "FWD stamps (state carries across the fold boundary)",
            "stamps_total": len(walk_rows),
            "gated_on": sum(1 for r in walk.values() if r.gated),
            "gated_off": sum(1 for r in walk.values() if not r.gated),
        },
        "cross_check": _cross_check_single_shot(
            {r["date"]: {"s90": r["s90"], "v1_state": r["v1_state"],
                         "v2_state": r["v2_state"]}
             for r in folds_out["S0R"]["per_day"] if r["is_stamp"]}),
        "folds": folds_out,
        "digests": {
            "catalog_root": str(wiring.CHR3F_CTRL),
            "files": digests_files,
        },
        "determinism": {
            "json": "sort_keys, indent=1, no wall-clock fields; identical "
                    "catalog bytes -> byte-identical artifact",
        },
    }
    out_path.write_text(json.dumps(payload, indent=1, sort_keys=True))
    return payload


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-coverage-only", action="store_true")
    ap.add_argument("--full-build", action="store_true")
    args = ap.parse_args()
    if args.full_build:
        out = HERE / "gate_series.json"
        payload = full_build(out)
    else:
        out = HERE / "coverage_status.json"
        payload = check_coverage()
        out.write_text(json.dumps(payload, indent=1, sort_keys=True))
    print(json.dumps({"written": str(out),
                      "digest": sha256_file(out),
                      "mode": "full" if args.full_build else "coverage"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
