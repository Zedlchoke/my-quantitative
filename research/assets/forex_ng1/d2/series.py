"""Vintaged CPI series: point-in-time as-of reads and naive-predictor
surprises for the FOREX-NG1 D2 measurement.

Consumption set (all READ-ONLY, sha-verified by the caller):

- GB/CA/AU/NZ legs: FRED-format vintaged realtime archives staged by the
  V9 integration worktree and pinned by the S2 CADS manifest
  (``fred_vintaged/<SERIES>.json``; sha256 verified against the S2
  manifest before any value is read).
- US leg: the CADS object ``US/fred_cpiaucsl_rt.json`` (S3 announcement
  ledger entry; resolved verify-on-read through the plane adapter).

As-of read law (fail-closed):

For observation month k and decision date d, the value in force at d is
the realtime row whose vintage window [realtime_start, realtime_end]
CONTAINS d (realtime_start <= d <= realtime_end); among duplicate
windows the latest realtime_start wins.  A month whose containing row
is missing-valued ("."), or has no containing window at d, reads as
None -> the event fails closed (no surprise, no position).  No
current-vintage backfill, ever.

Lag law (representation identity, recorded per event):

- monthly feeds (GBRCPIALLMINMEI, CANCPIALLMINMEI, CPIAUCSL):
  I(m-1) = obs month m minus 1 calendar month; I(m-12) = minus 12;
  I(m-13) = minus 13.
- quarterly feeds (AUSCPIALLQINMEI, NZLCPIALLQINMEI): mid-quarter
  calendar months do not exist in the archive, so the lag arithmetic is
  in OBSERVATION STEPS while preserving the seasonal-ratio structure:
  I(m-1) -> the previous observation (m minus 3 calendar months),
  I(m-12) -> minus 12 calendar months (same quarter last year, an
  observation month), I(m-13) -> the observation preceding the m-12
  one (m minus 15 calendar months).  Disclosed as the quarterly-leg
  measurement identity; no other interpretation is silently applied.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

FRED_MISSING = "."

#: Economy -> staged vintaged series identifier (S2 manifest key).
ECONOMY_SERIES = {
    "GB": "GBRCPIALLMINMEI",
    "CA": "CANCPIALLMINMEI",
    "AU": "AUSCPIALLQINMEI",
    "NZ": "NZLCPIALLQINMEI",
    "US": "CPIAUCSL",
}


def parse_realtime_observations(observations) -> list[dict]:
    """Parse FRED realtime observation dicts into normalized rows.

    Each output row: {"obs": 'YYYY-MM-DD', "rs": date, "re": date,
    "value": float | None}.  Rows lacking the realtime window raise
    ValueError (a revised-in-place table is not a vintaged archive).
    """
    rows: list[dict] = []
    for i, o in enumerate(observations):
        missing = {"realtime_start", "realtime_end", "date", "value"} - set(o)
        if missing:
            raise ValueError(
                f"observation {i} lacks vintaged keys {sorted(missing)}: "
                "not a realtime archive (fail-closed)")
        raw = str(o["value"])
        rows.append({
            "obs": str(o["date"]),
            "rs": date.fromisoformat(str(o["realtime_start"])),
            "re": date.fromisoformat(str(o["realtime_end"])),
            "value": None if raw == FRED_MISSING else float(raw),
        })
    if not rows:
        raise ValueError("empty observation set")
    return rows


def month_lag(month: str, k: int) -> str:
    """'2024-10' lagged by k calendar months (k may be negative)."""
    y, m = int(month[:4]), int(month[5:7])
    total = y * 12 + (m - 1) + k
    return f"{total // 12:04d}-{total % 12 + 1:02d}"


@dataclass
class VintagedSeries:
    """One vintaged CPI leg with as-of reads."""

    series_id: str
    rows: list[dict]
    spacing: str = "monthly"            # measured: 'monthly' | 'quarterly'
    _by_obs: dict[str, list[dict]] = field(default_factory=dict, repr=False)

    def __post_init__(self):
        for r in self.rows:
            if r["value"] is None:
                continue
            self._by_obs.setdefault(r["obs"], []).append(r)
        months = sorted({r["obs"][:7] for r in self.rows})
        if len(months) < 2:
            self.spacing = "monthly"
        else:
            gaps = [
                (int(months[i + 1][:4]) * 12 + int(months[i + 1][5:7]))
                - (int(months[i][:4]) * 12 + int(months[i][5:7]))
                for i in range(len(months) - 1)]
            # measured spacing: quarterly archives never carry adjacent
            # calendar months, monthly archives do
            self.spacing = "quarterly" if min(gaps) == 3 else "monthly"
        for obs in self._by_obs:
            self._by_obs[obs].sort(key=lambda r: (r["rs"], r["re"]))

    # ------------------------------------------------------------------ #
    def has_obs(self, month: str) -> bool:
        return f"{month}-01" in self._by_obs

    def value_asof(self, month: str, asof: date) -> float | None:
        """The value of obs ``month`` in the vintage in force at ``asof``.

        Containing-window read (rs <= asof <= re), latest rs wins; a
        missing containing window or a '.'-valued one returns None.
        """
        cands = self._by_obs.get(f"{month}-01")
        if not cands:
            return None
        in_force = [r for r in cands if r["rs"] <= asof <= r["re"]]
        if not in_force:
            return None
        row = max(in_force, key=lambda r: r["rs"])
        return row["value"]

    # ------------------------------------------------------------------ #
    def lag_months(self, ref_month: str) -> tuple[str, str, str] | None:
        """(m_prev, m_12, m_13) obs months for the predictor inputs.

        Monthly: (m-1, m-12, m-13).  Quarterly: (previous observation,
        m-12 calendar, the observation preceding m-12).  Returns None
        when any required observation month does not exist in the
        archive (fail-closed warmup).
        """
        if self.spacing == "monthly":
            triple = (month_lag(ref_month, -1), month_lag(ref_month, -12),
                      month_lag(ref_month, -13))
        else:
            prev = month_lag(ref_month, -3)     # previous observation
            same_ly = month_lag(ref_month, -12)  # same quarter last year
            prev_ly = month_lag(ref_month, -15)  # observation before that
            triple = (prev, same_ly, prev_ly)
        if not all(self.has_obs(m) for m in triple):
            return None
        return triple

    def neighbour_lag_months(self, ref_month: str) -> tuple[str, str] | None:
        """(m-2, m-14) for the A4-P2 NEIGH-SMOOTH2 smoother prior
        (monthly arithmetic; quarterly: two observations back and the
        corresponding last-year observation)."""
        if self.spacing == "monthly":
            pair = (month_lag(ref_month, -2), month_lag(ref_month, -14))
        else:
            pair = (month_lag(ref_month, -6), month_lag(ref_month, -18))
        if not all(self.has_obs(m) for m in pair):
            return None
        return pair


# --------------------------------------------------------------------------- #
# frozen surprise formulas (proposal identity; never retuned)
# --------------------------------------------------------------------------- #

def s1_seasonal_naive(vs: VintagedSeries, ref_month: str, i_print: float,
                      asof: date) -> tuple[float | None, dict]:
    """s1 = 100 * ( I_print / I_hat_sn - 1 ),  I_hat_sn = m_prev * m12 / m13.

    All predictor inputs are read as-of ``asof``; any missing input
    fails closed to None.  Returns (s1_or_None, detail dict).
    """
    triple = vs.lag_months(ref_month)
    if triple is None:
        return None, {"reason": "warmup_obs_months_missing"}
    m_prev, m12, m13 = triple
    i_prev = vs.value_asof(m_prev, asof)
    i_12 = vs.value_asof(m12, asof)
    i_13 = vs.value_asof(m13, asof)
    if i_prev is None or i_12 is None or i_13 is None or i_13 == 0.0:
        return None, {"reason": "vintage_value_unavailable_asof",
                      "months": {"prev": m_prev, "m12": m12, "m13": m13}}
    i_hat = i_prev * (i_12 / i_13)
    if i_hat == 0.0:
        return None, {"reason": "zero_predictor"}
    s1 = 100.0 * (i_print / i_hat - 1.0)
    return s1, {"reason": "ok", "months": {"prev": m_prev, "m12": m12,
                                           "m13": m13},
                "i_hat": i_hat}


def s2_trailing_yoy(vs: VintagedSeries, ref_month: str, i_print: float,
                    asof: date) -> tuple[float | None, dict]:
    """s2 = 100 * ( I_print / I_hat_ty - 1 ),
    I_hat_ty = I(m-12) * (1 + pi_bar), pi_bar = I(m-1)/I(m-13) - 1."""
    triple = vs.lag_months(ref_month)
    if triple is None:
        return None, {"reason": "warmup_obs_months_missing"}
    m_prev, m12, m13 = triple
    i_prev = vs.value_asof(m_prev, asof)
    i_12 = vs.value_asof(m12, asof)
    i_13 = vs.value_asof(m13, asof)
    if i_prev is None or i_12 is None or i_13 is None or i_13 == 0.0:
        return None, {"reason": "vintage_value_unavailable_asof",
                      "months": {"prev": m_prev, "m12": m12, "m13": m13}}
    pi_bar = i_prev / i_13 - 1.0
    i_hat = i_12 * (1.0 + pi_bar)
    if i_hat == 0.0:
        return None, {"reason": "zero_predictor"}
    s2 = 100.0 * (i_print / i_hat - 1.0)
    return s2, {"reason": "ok", "months": {"prev": m_prev, "m12": m12,
                                           "m13": m13},
                "pi_bar": pi_bar, "i_hat": i_hat}


def release_sign(vs: VintagedSeries, ref_month: str, i_print: float,
                 asof: date) -> int | None:
    """Sign of the realized m/m (or q/q) direction of the print:
    sign(I_print - I(previous observation as-of)).  Used ONLY by the
    rebuilt V7 reaction-direction shadows (FAMILY_FAILURES spec: the
    V7 class conditioned on the sign of the release)."""
    if vs.spacing == "monthly":
        prev_month = month_lag(ref_month, -1)
    else:
        prev_month = month_lag(ref_month, -3)
    if not vs.has_obs(prev_month):
        return None
    i_prev = vs.value_asof(prev_month, asof)
    if i_prev is None:
        return None
    return 1 if i_print > i_prev else (-1 if i_print < i_prev else 0)
