"""ILLIQ-REG-V1 wiring law — plan SS9 (CHR3F lessons, binding).

Funding scan PHAI THEO FOLD (B2 lesson): pre-window folds read scan_2026,
S0R/FWD read scan_2026_a. Bars load-end +3d (A4/F2). The 4-label invariant
(plan SS11) is enforced on every produced row; a row missing any label is
invalid, not merely incomplete.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

CHR3F_CTRL = Path(
    "/Users/hoangminhlong/my-quantitative/.worktrees/"
    "crypto-historical-replication-3f-v1/integration/research/control/"
    "crypto_historical_replication_3f_v1"
)

PRE_WINDOW_DAYS = 125   # runner pre-load
LOAD_END_PLUS_DAYS = 3  # terminal Monday stamp must have a covering bar

SYMS = ["1000PEPEUSDT", "AAVEUSDT", "ACEUSDT", "ADAUSDT", "AVAXUSDT",
        "BCHUSDT", "BNBUSDT", "BOMEUSDT", "BTCUSDT", "DOGEUSDT", "ENAUSDT",
        "ETHUSDT", "LINKUSDT", "NEARUSDT", "ONGUSDT", "SOLUSDT", "SUIUSDT",
        "WLDUSDT", "XRPUSDT", "ZECUSDT"]

SCAN_PREWINDOW = "scan_2026"     # 2020-07-01..2024-08-20
SCAN_S0R_FWD = "scan_2026_a"     # 2024-08-20..2026-08-21

FOLD_WINDOWS = {
    "Y2021": ("2021-01-01T00:00:00Z", "2021-12-31T00:00:00Z"),
    "Y2024P": ("2024-01-01T00:00:00Z", "2024-08-19T00:00:00Z"),
    "S0R": ("2024-08-22T00:00:00Z", "2025-08-21T00:00:00Z"),
    "FWD": ("2025-08-22T00:00:00Z", "2026-08-21T00:00:00Z"),
}

# catalog: absolute path; None = identity not yet verified (fail-closed, must
# be pinned by an explicit coverage step before any FWD stage runs).
FOLD_WIRING = {
    "Y2021": {"catalog": CHR3F_CTRL / "catalog_live_crypto_b20",
              "funding_scan": CHR3F_CTRL / "funding_data_scan" / SCAN_PREWINDOW},
    "Y2024P": {"catalog": CHR3F_CTRL / "catalog_live_crypto_b20",
               "funding_scan": CHR3F_CTRL / "funding_data_scan" / SCAN_PREWINDOW},
    "S0R": {"catalog": CHR3F_CTRL / "catalog_live_crypto_s0r",
            "funding_scan": CHR3F_CTRL / "funding_data_scan" / SCAN_S0R_FWD},
    "FWD": {"catalog": None,
            "funding_scan": CHR3F_CTRL / "funding_data_scan" / SCAN_S0R_FWD},
}


class WiringError(RuntimeError):
    """Fail-closed wiring violation (e.g. B2-style zero-coverage scan)."""


def scan_id_for_fold(fold: str) -> str:
    wiring = FOLD_WIRING.get(fold)
    if wiring is None:
        raise WiringError(f"unknown fold {fold!r}")
    return wiring["funding_scan"].name


def bars_load_bounds(window_start_iso: str, window_end_iso: str) -> tuple[str, str]:
    """(pre_start, end_ext): start - 125d, end + 3d (A4/F2 load law)."""
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    st = dt.datetime.strptime(window_start_iso, fmt)
    en = dt.datetime.strptime(window_end_iso, fmt)
    pre = (st - dt.timedelta(days=PRE_WINDOW_DAYS)).strftime(fmt)
    ext = (en + dt.timedelta(days=LOAD_END_PLUS_DAYS)).strftime(fmt)
    return pre, ext


def first_funding_row_time(scan_root: Path, sym: str) -> dt.datetime | None:
    """Time of the symbol's first funding row in the scan (None if absent)."""
    path = Path(scan_root) / sym / "funding.json"
    if not path.exists():
        return None
    rows = json.loads(path.read_text()).get("rows", [])
    if not rows:
        return None
    return dt.datetime.fromtimestamp(int(rows[0]["fundingTime"]) / 1000.0,
                                     dt.timezone.utc)


def listed_symbols_proxy(scan_root: Path, window_end_iso: str,
                         symbols=SYMS) -> set[str]:
    """Scan-aware listing proxy: symbols whose first funding row precedes the
    window end were tradeable in-window. Pre-window folds require coverage
    only for these; a not-yet-listed symbol legitimately has zero rows
    (e.g. 1000PEPEUSDT in Y2021). The S0R/FWD folds require the FULL SYMS
    list (all 20 listed by 2024-04-02, A5) — never weaken that."""
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    hi = dt.datetime.strptime(window_end_iso, fmt).replace(tzinfo=dt.timezone.utc)
    return {s for s in symbols
            if (t := first_funding_row_time(scan_root, s)) and t < hi}


def verify_funding_scan_coverage(scan_root: Path, symbols=SYMS,
                                 window_start_iso: str | None = None,
                                 window_end_iso: str | None = None) -> dict:
    """Per-symbol in-window funding row counts; WiringError on ANY zero among
    the REQUIRED symbols.

    The B2 incident was a scan wired to a fold whose window it does not
    cover, yielding funding 0.0 on all 336 S0R positions while looking
    successful. Zero coverage inside the fold window must fail loudly before
    any compute. `symbols` IS the required set: pre-window folds pass the
    PIT-listed subset (listed_symbols_proxy), S0R/FWD pass the full SYMS.
    """
    if window_start_iso is None or window_end_iso is None:
        raise WiringError("coverage check requires an explicit fold window")
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    lo = dt.datetime.strptime(window_start_iso, fmt).replace(tzinfo=dt.timezone.utc)
    hi = dt.datetime.strptime(window_end_iso, fmt).replace(tzinfo=dt.timezone.utc)
    counts: dict[str, int] = {}
    for sym in symbols:
        path = Path(scan_root) / sym / "funding.json"
        if not path.exists():
            raise WiringError(f"funding scan missing for {sym}: {path}")
        rows = json.loads(path.read_text()).get("rows", [])
        n = 0
        for r in rows:
            ts = dt.datetime.fromtimestamp(int(r["fundingTime"]) / 1000.0,
                                           dt.timezone.utc)
            if lo <= ts < hi:
                n += 1
        if n == 0:
            raise WiringError(
                f"B2_FAIL_CLOSED: zero funding rows in window for {sym} "
                f"under scan {Path(scan_root).name}")
        counts[sym] = n
    return counts


# --- 4-label invariant (plan SS11) --------------------------------------------

ANCESTRY_LABEL = "OUTCOME_EXPOSED_ANCESTRY"
NAMESPACE_LABEL = "REPLICATION_NOT_PROSPECTIVE"
FUNDING_WIRING_ALLOWED = {
    f"funded({SCAN_PREWINDOW})",
    f"funded({SCAN_S0R_FWD})",
    "no-funding DIAG (B2)",
}
LABEL_KEYS = ("WINDOW_FOLD", "ANCESTRY", "NAMESPACE", "FUNDING_WIRING")


def labels_for_row(fold: str, funding_scan_name: str) -> dict:
    return {
        "WINDOW_FOLD": fold,
        "ANCESTRY": ANCESTRY_LABEL,
        "NAMESPACE": NAMESPACE_LABEL,
        "scored": False,
        "FUNDING_WIRING": f"funded({funding_scan_name})",
    }


def validate_labels(row: dict) -> None:
    """Raise LabelError unless ALL FOUR labels are present and legal."""
    missing = [k for k in LABEL_KEYS if k not in row]
    if missing:
        raise LabelError(f"4-label invariant violated, missing {missing}")
    if row["WINDOW_FOLD"] not in FOLD_WINDOWS:
        raise LabelError(f"illegal WINDOW_FOLD {row['WINDOW_FOLD']!r}")
    if row["ANCESTRY"] != ANCESTRY_LABEL:
        raise LabelError(f"illegal ANCESTRY {row['ANCESTRY']!r}")
    if row["NAMESPACE"] != NAMESPACE_LABEL or row.get("scored") is not False:
        raise LabelError("historical rows must be REPLICATION_NOT_PROSPECTIVE "
                         "and scored=False")
    if row["FUNDING_WIRING"] not in FUNDING_WIRING_ALLOWED:
        raise LabelError(f"illegal FUNDING_WIRING {row['FUNDING_WIRING']!r}")


class LabelError(ValueError):
    pass
