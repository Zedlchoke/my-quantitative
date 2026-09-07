"""PLAN_stocks_v10 P0 — filing-timing and vintage-revision observable layer.

Builds the two observable families on the hash-verified V9 multi-vintage
panel (death-inclusive cohort) with no new vendor:

TIMING (per filer-field-period group, from the panel's own availability
evidence — the vintage/submission timestamps ARE the evidence):
  first_lag_days   min(avail) - eff          (first filing of the period)
  last_lag_days    max(avail) - eff          (last vintage of the period)
  amend_count      depth - 1                 (additional vintages filed)
  own_z            (first_lag - own_norm) / own_scale   prior-only PIT norm
  cohort_z         (first_lag - cohort_norm) / cohort_scale  public-only PIT norm

PIT definitions (frozen here, mirrored in the manifest schema):
  own_norm(e, m, E)   = median first_lag over same-filer same-period-type
                        groups with eff' < E AND first_avail' <= first_avail_E
                        (only periods already closed AND already public when
                        the current filing became public)
  cohort_norm(s, m, E)= median first_lag over the same (sector, period-type)
                        filer-periods whose FIRST filing stamp is strictly
                        before the calendar-month bucket start of
                        first_avail_E (precomputed per bucket; a group's own
                        stamp lies inside its own bucket, so the group and
                        every same-month peer are excluded fail-closed —
                        intraday ordering is unevidenced).
                        Histories are deduplicated per filer-period (timing
                        is a property of the filing, not of the field).
  Scale               = 1.4826 * MAD over the same sample; null with reason
                        INSUFFICIENT_HISTORY (< MIN_HIST) or ZERO_SCALE.

REVISION (per group with depth >= 2):
  rev_dir  sign(v_last - v_first)
  rev_mag  |v_last - v_first| / |v_first|   (null + ZERO_BASE when v_first=0)
  non-numeric v -> excluded row with reason EXCLUDED_NON_NUMERIC (counted)

observable_available_at (the evidence stamp, per group):
  timing   = first_avail
  revision = last_avail

Deadline-distance: NO sourced filer-category deadline evidence exists in the
staged data — recorded DATA_BLOCKED_VALID in the census; never asserted.

Outputs (raw artifacts gitignored, sha256 pinned in the manifest):
  .staging_sec_v10/v10_timing_observables.jsonl
  .staging_sec_v10/v10_revision_observables.jsonl
  research/control/stocks_free_v10_run/p0_v10_observable_manifest.json
"""

from __future__ import annotations

import hashlib
import json
import statistics
from bisect import bisect_left
from datetime import date
from pathlib import Path

SCHEMA = "stocks_free_v10_run/p0_v10_observables@1"
MIN_HIST_OWN = 4
MIN_HIST_COHORT = 30

REASON_INSUFFICIENT_HISTORY = "INSUFFICIENT_HISTORY"
REASON_ZERO_SCALE = "ZERO_SCALE"
REASON_ZERO_BASE = "ZERO_BASE"
REASON_EXCLUDED_NON_NUMERIC = "EXCLUDED_NON_NUMERIC"


def _d(s: str) -> date:
    return date.fromisoformat(s)


def _days(a: date, b: date) -> int:
    return (a - b).days


def scan_groups(panel_path: str):
    """One streaming pass over the panel.

    Returns groups: dict[(e, f, eff)] -> [min_avail, v_at_min, max_avail,
    v_at_max, depth, avail_concat]; and per-filer sector map.
    Row order of downstream outputs follows panel insertion order (deterministic).
    """
    groups: dict = {}
    sector: dict = {}
    rows = 0
    with open(panel_path, "r", buffering=1 << 20) as fh:
        for line in fh:
            r = json.loads(line)
            rows += 1
            e, f, eff, av = r["e"], r["f"], r["eff"], r["avail"]
            v = r["v"]
            if e not in sector and r.get("s"):
                sector[e] = r["s"]
            key = (e, f, eff)
            g = groups.get(key)
            if g is None:
                groups[key] = [av, v, av, v, 1, av]
            else:
                if av < g[0]:
                    g[0], g[1] = av, v
                if av > g[2]:
                    g[2], g[3] = av, v
                if av not in g[5]:
                    g[4] += 1
                    g[5] += "," + av
    return groups, sector, rows


def _median_scale(samples):
    """Return (median, 1.4826*MAD) or (None, None, reason)."""
    n = len(samples)
    if n == 0:
        return None, None
    med = statistics.median(samples)
    return med, 1.4826 * statistics.median([abs(x - med) for x in samples])


def compute_observables(groups, sector, on_timing=None, on_revision=None):
    """Second, in-memory pass: histories then per-group observables.

    With on_timing/on_revision callbacks the rows are streamed out (memory
    flat — used by the real build); without them the rows are accumulated
    and returned (used by tests). Returns (timing_rows, revision_rows,
    census) in the accumulate mode, census alone when streaming.
    """
    # histories ------------------------------------------------------------
    # Timing is a property of the FILING (filer-period), not of the field:
    # histories are deduplicated per (filer, period) keeping the FIRST
    # availability stamp, so multi-field periods never multiply weight.
    own_d = {}   # (e, month) -> {eff: min_first_avail}
    coh_d = {}   # (s, month) -> {(e, eff): min_first_avail}
    for (e, _f, eff), g in groups.items():
        av = g[0]
        m = eff[5:7]
        od = own_d.setdefault((e, m), {})
        if eff not in od or av < od[eff]:
            od[eff] = av
        cd = coh_d.setdefault((sector.get(e, ""), m), {})
        ck = (e, eff)
        if ck not in cd or av < cd[ck]:
            cd[ck] = av

    own = {
        k: [(eff, av, _days(_d(av), _d(eff))) for eff, av in d.items()]
        for k, d in own_d.items()
    }

    # cohort buckets: per (s, m), entries sorted by stamp; one (median, MAD)
    # precomputed per calendar-month bucket over entries whose stamp is
    # strictly before the bucket start. A group's own stamp lies inside its
    # bucket, so the group itself (and any same-month peer) is excluded
    # fail-closed — intraday ordering is unevidenced.
    coh_bucket_stats = {}
    for k, d in coh_d.items():
        entries = sorted(((av, _days(_d(av), _d(eff))) for (e, eff), av in d.items()),
                         key=lambda t: t[0])
        stamps = [t[0] for t in entries]
        lags = [t[1] for t in entries]
        stats = {}
        for b in sorted({st[:7] for st in stamps}):
            idx = bisect_left(stamps, b + "-01")
            if idx >= MIN_HIST_COHORT:
                stats[b] = _median_scale(lags[:idx])
        coh_bucket_stats[k] = stats

    timing_rows = []
    revision_rows = []

    def _emit_timing(row):
        if on_timing is None:
            timing_rows.append(row)
        else:
            on_timing(row)

    def _emit_revision(row):
        if on_revision is None:
            revision_rows.append(row)
        else:
            on_revision(row)

    census = {
        "timing": {
            "groups_total": 0,
            "own_z_computable": 0, "own_null": {},
            "cohort_z_computable": 0, "cohort_null": {},
            "negative_lags": 0,
            "sectors_unmapped_groups": 0,
        },
        "revision": {
            "groups_depth_ge2": 0,
            "rows_written": 0,
            "excluded_non_numeric": 0,
            "zero_base": 0,
            "dir_counts": {"up": 0, "flat": 0, "down": 0},
        },
        "per_class": {},   # filled by caller against cohort classes
    }

    for (e, f, eff), g in groups.items():
        first_avail, v_first, last_avail, v_last, depth = g[0], g[1], g[2], g[3], g[4]
        lag = _days(_d(first_avail), _d(eff))
        if lag < 0:
            census["timing"]["negative_lags"] += 1
        m = eff[5:7]
        dec_instant = first_avail

        # --- own PIT norm -------------------------------------------------
        hist = [t[2] for t in own[(e, m)]
                if t[0] < eff and t[1] <= dec_instant]
        med, mad = (None, None)
        if len(hist) < MIN_HIST_OWN:
            own_reason = REASON_INSUFFICIENT_HISTORY
            own_norm = own_scale = None
            own_z = None
        else:
            med, mad = _median_scale(hist)
            own_norm = med
            own_scale = mad
            own_reason = None
            if own_scale == 0 or own_scale is None:
                own_reason = REASON_ZERO_SCALE
                own_z = None
            else:
                own_z = (lag - own_norm) / own_scale
        # --- cohort PIT norm (precomputed month bucket) ----------------------
        # norm = (median, 1.4826*MAD) over same (sector, period-type)
        # filer-periods whose FIRST filing stamp is strictly before the start
        # of the calendar month of this group's decision instant; missing
        # bucket means the sample never reached MIN_HIST_COHORT.
        stats = coh_bucket_stats[(sector.get(e, ""), m)].get(dec_instant[:7])
        if stats is None:
            cohort_reason = REASON_INSUFFICIENT_HISTORY
            cohort_z = None
            cohort_norm = cohort_scale = None
        else:
            cmed, cmad = stats
            cohort_norm = cmed
            cohort_scale = cmad
            cohort_reason = None
            if cohort_scale == 0 or cohort_scale is None:
                cohort_reason = REASON_ZERO_SCALE
                cohort_z = None
            else:
                cohort_z = (lag - cohort_norm) / cohort_scale

        _emit_timing({
            "e": e, "s": sector.get(e, ""), "f": f, "eff": eff,
            "first_avail": first_avail, "last_avail": last_avail,
            "depth": depth,
            "first_lag_days": lag,
            "last_lag_days": _days(_d(last_avail), _d(eff)),
            "amend_count": depth - 1,
            "own_norm_days": own_norm, "own_scale_days": own_scale,
            "own_z": None if own_z is None else round(own_z, 6),
            "own_reason": own_reason,
            "cohort_norm_days": cohort_norm, "cohort_scale_days": cohort_scale,
            "cohort_z": None if cohort_z is None else round(cohort_z, 6),
            "cohort_reason": cohort_reason,
            "observable_available_at": first_avail,
        })
        c = census["timing"]
        c["groups_total"] += 1
        if own_z is not None:
            c["own_z_computable"] += 1
        elif own_reason:
            c["own_null"][own_reason] = c["own_null"].get(own_reason, 0) + 1
        if cohort_z is not None:
            c["cohort_z_computable"] += 1
        elif cohort_reason:
            c["cohort_null"][cohort_reason] = c["cohort_null"].get(cohort_reason, 0) + 1

        # --- revision rows (depth >= 2 only) --------------------------------
        if depth >= 2:
            census["revision"]["groups_depth_ge2"] += 1
            row = {
                "e": e, "s": sector.get(e, ""), "f": f, "eff": eff,
                "depth": depth, "first_avail": first_avail,
                "last_avail": last_avail,
                "inter_arrival_days": _days(_d(last_avail), _d(first_avail)),
                "amend_count": depth - 1,
                "rev_dir": None, "rev_mag": None,
                "observable_available_at": last_avail,
                "reason": None,
            }
            try:
                x0 = float(v_first)
                x1 = float(v_last)
            except (TypeError, ValueError):
                row["reason"] = REASON_EXCLUDED_NON_NUMERIC
                census["revision"]["excluded_non_numeric"] += 1
            else:
                if x1 > x0:
                    row["rev_dir"] = 1; census["revision"]["dir_counts"]["up"] += 1
                elif x1 < x0:
                    row["rev_dir"] = -1; census["revision"]["dir_counts"]["down"] += 1
                else:
                    row["rev_dir"] = 0; census["revision"]["dir_counts"]["flat"] += 1
                if x0 == 0:
                    row["reason"] = REASON_ZERO_BASE
                    census["revision"]["zero_base"] += 1
                else:
                    row["rev_mag"] = abs(x1 - x0) / abs(x0)
            _emit_revision(row)
            census["revision"]["rows_written"] += 1
        if not sector.get(e, ""):
            census["timing"]["sectors_unmapped_groups"] = \
                census["timing"].get("sectors_unmapped_groups", 0) + 1
    census["timing"]["own_null"] = dict(sorted(census["timing"]["own_null"].items()))
    census["timing"]["cohort_null"] = dict(sorted(census["timing"]["cohort_null"].items()))
    if on_timing is None and on_revision is None:
        return timing_rows, revision_rows, census
    return census


def write_jsonl(path: str, rows):
    h = hashlib.sha256()
    n = 0
    with open(path, "wb", buffering=1 << 20) as fh:
        for r in rows:
            b = (json.dumps(r, separators=(",", ":"), sort_keys=False) + "\n").encode()
            h.update(b)
            fh.write(b)
            n += 1
    return n, h.hexdigest()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb", buffering=1 << 20) as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
