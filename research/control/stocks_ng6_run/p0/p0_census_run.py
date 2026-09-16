"""STOCKS-NG6 P0 census (plans/PLAN_stocks_ng6.md §4, gates F1-F10).

Single-name failed-breakdown unwind (bear-trap reclaim).  P0 is source
engineering + census ONLY: no candidate returns, PnL, PF, Sharpe, drawdown,
survivors or S1 evidence anywhere in this run.

The cohort EOD retrieval is the machine's ONE heavy job: the whole run
executes under the machine-wide heavy lock (registry + flock + heartbeats
<= 60s + release in finally).  Lock busy => NOT_RUN_RESOURCE_CONFLICT,
never a spin.  API keys are read from the root .env and never echoed;
every error string passes through redact().

Frozen conventions (declared ex ante, never tuned):
- P-12 representation: the EODHD adjusted (total-return) series is THE
  single representation.  Per-session multiplicative factor
  f_t = adjusted_close_t / close_t reconstructs adjusted open/high/low;
  all states (break/reclaim/range/participation) and any later returns
  live on the SAME adjusted series.
- Event (plan §5 anchor): BREAK adj_low_t < min(adj_low over the prior
  252 served sessions t-252..t-1); RECLAIM adj_close_t > that same prior
  low; RANGE (close_t - low_t)/(high_t - low_t) >= 0.5 (scale-invariant);
  PARTICIPATION dvol_t >= 1.5x trailing 60-session median dvol
  (dvol_t = adj_close_t * volume_t); bookability floors adj_close_t >=
  $1.00 and trailing 60-session median dvol >= $2M; first eligible event
  is the 253rd served session (warmup 252 is enforced by construction).
- ADV bands (F6) measured ON THE EVENT population: trailing 252-session
  median dvol: >=50M -> A, >=10M -> B, >=2M -> C, below -> SUBFLOOR;
  a non-finite median is UNRESOLVED and fails F6 closed (never a silent
  default band).
- Clock (F5): decision at t close; entry t+1 open; exit t+11 open.
- Fold freeze (F8): three chronological thirds of the SPY-served session
  grid (SPY serves every XNYS session); Q-6 floor >= 30 BOOKABLE
  events/fold, fail-closed.  Window 2015+ so 2008Q4-2009 vs 2020-03
  sharing is moot; the fold set spans 2020-03 (F2) and the 2022 bear (F3).
"""

from __future__ import annotations

import gzip
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np

WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/stocks-ng6/integration")
ROOT = Path("/Users/hoangminhlong/my-quantitative")
HERE = WT / "research/control/stocks_ng6_run/p0"
COHORT_DIR = HERE / "cohort"
CACHE = WT / "data_raw/stocks_ng6_eod"

# frozen ex-ante parameters (plan §4 F6 / §5)
BREAK_LOOKBACK = 252
WARMUP_SESSIONS = 252          # first eligible event = 253rd served session
DVOL_WINDOW = 60
DVOL_MULT = 1.5
RANGE_MIN = 0.5
FLOOR_PRICE = 1.00
FLOOR_DVOL = 2_000_000.0
HORIZON_FILL_LAG = 11          # exit at t+11 open (H=10)
BANDS_DEF = {"A": 50e6, "B": 10e6, "C": 2e6}
BAND_BPS = {"A": 10, "B": 15, "C": 25}
FOLD_EVENT_FLOOR = 30          # Q-6 recent-window floor, fail-closed

WINDOW_START = "2015-01-01"
COHORT_SHA_EXPECTED = "6a95401ff84bff2144ac3c0b9426a6fa86daf3dde8d478195666249e3fa2aa62"
COHORT_SOURCE = Path("/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v13/"
                     "integration/research/control/stocks_free_v9_run/cohort_v9.json")
V8_TERMS_DIR = WT / "research/control/stocks_free_v8_probe/eodhd_license"
V8_PROBE_VERDICT = WT / "research/control/stocks_free_v8_probe/eodhd_probe_verdict.json"
V8_TOS_SHA = "dcedb1eddfb5c9fb1aa767a35a059ef25f219ebfdd7452adbfde956121ecaee5"
V8_PRICING_SHA = "df809c729df6e5354726b7674d2cdadf53473577c15fed9cb7adc88d784c77b5"
NG5_P0_VERDICT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/stocks-ng5/"
                      "integration/research/control/stocks_ng5_run/p0/p0_census_verdict.json")
A3_DOSSIER = WT / "research/control/ng6_ng7_ng4_dossiers_2026-09/sng6-a3-sec-source-pit-dossier.json"
FDF_FTD_MANIFEST = Path("/Users/hoangminhlong/my-quantitative/.worktrees/free-data-frontier-v1/"
                        "integration/research/control/free_data_frontier_v1_run/manifests/"
                        "sec_ftd_archive_manifest.json")
FDF_FTD_RAW_DIR = Path("/Users/hoangminhlong/.my-quantitative-data/free-data-frontier-v1/"
                       "raw/sec_ftd_archive")
FTD_VERIFY_FILES = ["cnsfails200907a.zip", "cnsfails202608b.zip"]

CANARY_NEVER = "ZZZQQQNG6"
CANARIES = ["QQQ", "SPY", "AAPL", CANARY_NEVER]
HTTP = {"n": 0}
_last_hb = {"t": 0.0}

BAND_KEYS = ("A", "B", "C", "SUBFLOOR", "UNRESOLVED")


def log(m):
    print(f"[p0] {m}", flush=True)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def redact(s: str) -> str:
    return re.sub(r"api_token=[^&\s'\"]+", "api_token=REDACTED", s)


def load_key() -> str:
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith("EODHD_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("EODHD_API_KEY not found in root .env")


def fetch(url: str, timeout: int = 120) -> tuple[int, str, bytes]:
    """HTTP GET; NEVER raises with an unsanitized body — error strings are redacted."""
    HTTP["n"] += 1
    req = urllib.request.Request(url, headers={"User-Agent": "my-quantitative-research/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.headers.get("Content-Type", ""), resp.read()
    except urllib.error.HTTPError as exc:
        ct = exc.headers.get("Content-Type", "") if exc.headers else ""
        return exc.code, ct, exc.read()
    except Exception as exc:  # noqa: BLE001 - urllib errors may embed the tokened URL
        return -1, "urllib-error", redact(str(exc)).encode()


def eod_url(key: str, symbol: str, from_date: str = WINDOW_START) -> str:
    return ("https://eodhd.com/api/eod/" + urllib.parse.quote(f"{symbol}.US")
            + f"?api_token={key}&fmt=json&order=a&from={from_date}")


# ---------------------------------------------------------------- pure census

def resolve_band(median_dvol_252) -> str:
    """ADV band resolution, fail-closed: no finite value -> no band (raise)."""
    if median_dvol_252 is None or not np.isfinite(median_dvol_252):
        raise ValueError("band UNRESOLVED: median_dvol_252 missing/non-finite (fail-closed)")
    if median_dvol_252 >= BANDS_DEF["A"]:
        return "A"
    if median_dvol_252 >= BANDS_DEF["B"]:
        return "B"
    if median_dvol_252 >= BANDS_DEF["C"]:
        return "C"
    return "SUBFLOOR"


def clock_legs(t: int) -> tuple[int, int, int]:
    """F5 frozen clock: decision at t close, entry t+1 open, exit t+11 open."""
    return t, t + 1, t + 11


class FoldFloorError(RuntimeError):
    """Q-6 recent-window floor violated: fold < 30 events (fail-closed)."""


def check_fold_floor(fold_event_counts: dict, floor: int = FOLD_EVENT_FLOOR) -> None:
    bad = {k: v for k, v in fold_event_counts.items() if v < floor}
    if bad:
        raise FoldFloorError(f"Q-6 fold floor {floor} violated (fail-closed): {bad}")


EMPTY_DROPS = {"break_no_reclaim": 0, "range_undefined": 0, "range": 0, "dvol": 0,
               "floor_price": 0, "floor_dvol": 0, "band_unresolved": 0}


def compute_events(dates, adj_open, adj_high, adj_low, adj_close, volume,
                   break_lookback: int = BREAK_LOOKBACK,
                   dvol_window: int = DVOL_WINDOW,
                   dvol_mult: float = DVOL_MULT,
                   range_min: float = RANGE_MIN,
                   floor_price: float = FLOOR_PRICE,
                   floor_dvol: float = FLOOR_DVOL):
    """Plan §5 anchor event census on ONE name (pure function).

    Returns (events, drop_counters).  Each candidate break i is classified:
    break-no-reclaim (control-book population, censused not dropped), then
    reclaim/range/participation/floor filters (drops, censused), then an
    event.  First eligible event is served-session index >= break_lookback
    (the 253rd served session) — enforced by construction.
    """
    events: list[dict] = []
    drops = {k: 0 for k in EMPTY_DROPS}
    n = len(dates)
    if n <= break_lookback:
        return events, drops
    dvol = adj_close * volume
    for i in range(break_lookback, n):
        prior_lo = float(np.min(adj_low[i - break_lookback:i]))
        if not (adj_low[i] < prior_lo):
            continue
        if not (adj_close[i] > prior_lo):
            drops["break_no_reclaim"] += 1
            continue
        hi, lo = float(adj_high[i]), float(adj_low[i])
        if hi <= lo:
            drops["range_undefined"] += 1
            continue
        range_frac = (float(adj_close[i]) - lo) / (hi - lo)
        if range_frac < range_min:
            drops["range"] += 1
            continue
        med60 = float(np.median(dvol[i - dvol_window:i]))
        if med60 <= 0:
            drops["floor_dvol"] += 1
            continue
        dvol_ratio = float(dvol[i]) / med60
        if dvol_ratio < dvol_mult:
            drops["dvol"] += 1
            continue
        bookable = bool(adj_close[i] >= floor_price and med60 >= floor_dvol)
        if adj_close[i] < floor_price:
            drops["floor_price"] += 1
        if med60 < floor_dvol:
            drops["floor_dvol"] += 1
        med252 = float(np.median(dvol[i - break_lookback:i]))
        try:
            band = resolve_band(med252)
        except ValueError:
            drops["band_unresolved"] += 1
            band = "UNRESOLVED"
        events.append({
            "i": int(i),
            "date": str(dates[i]),
            "prior_low": round(prior_lo, 6),
            "range_frac": round(range_frac, 6),
            "dvol_ratio": round(dvol_ratio, 4),
            "adj_close": round(float(adj_close[i]), 6),
            "med60_dvol": round(med60, 2),
            "med252_dvol": round(med252, 2),
            "bookable": bookable,
            "band": band,
        })
    return events, drops


def weekend_count(dates: list[str]) -> int:
    """ISO dates -> weekend count (epoch 1970-01-01 was a Thursday: +3 offset,
    Monday=0 convention; weekend = weekday >= 5)."""
    if not dates:
        return 0
    days = np.array(dates, dtype="datetime64[D]").astype(int)
    return int((((days + 3) % 7) >= 5).sum())


# ------------------------------------------------------------------- run

def main() -> int:
    HERE.mkdir(parents=True, exist_ok=True)
    COHORT_DIR.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(WT))  # research.governance lives at the worktree root
    key = load_key()

    from research.governance import heavy_lock

    lock_cmd = [sys.executable, str(Path(__file__).resolve())]
    with heavy_lock.acquire(
        cycle_id="STOCKS-NG6",
        role="P0_CENSUS_HEAVY",
        worktree=str(WT),
        command=lock_cmd,
        expected_artifacts=[
            str(HERE / "p0_verdict.json"),
            str(HERE / "folds.json"),
            str(HERE / "retrieval_manifest.json"),
        ],
    ) as hb:
        try:
            return _run(hb, key)
        except Exception as exc:  # noqa: BLE001 - honest blocker verdict, lock released cleanly
            err = redact(f"{type(exc).__name__}: {exc}")[:600]
            log(f"TECHABORT: {err}")
            (HERE / "p0_verdict.json").write_text(json.dumps({
                "schema": "stocks_ng6_p0_verdict@1",
                "cycle_id": "STOCKS-NG6",
                "verdict": "P0_TECHABORT",
                "blocker": err,
                "measured_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "no_pnl_computed": True,
            }, indent=1, sort_keys=True) + "\n")
            hb.heartbeat(extra={"status": "techabort", "blocker": err})
            return 1


def _run(hb, key: str) -> int:
    t0 = time.time()
    _last_hb["t"] = time.time()

    def beat(extra=None):
        if time.time() - _last_hb["t"] >= 45:
            _last_hb["t"] = time.time()
            hb.heartbeat(extra=extra or {})

    def write_blockverdict(gate: str, detail: dict) -> int:
        (HERE / "p0_verdict.json").write_text(json.dumps({
            "schema": "stocks_ng6_p0_verdict@1",
            "cycle_id": "STOCKS-NG6",
            "verdict": "P0_BLOCKED_SOURCE",
            "blocked_gate": gate,
            "detail": detail,
            "measured_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "no_pnl_computed": True,
        }, indent=1, sort_keys=True) + "\n")
        log(f"BLOCKED_SOURCE at {gate}")
        return 1

    # ------------- F1 three-layer gate (FIRST, before any bulk retrieval)
    reachable: dict[str, dict] = {}
    for sym in CANARIES:
        if sym == CANARY_NEVER:
            url = "https://eodhd.com/api/eod/" + CANARY_NEVER + ".US?api_token=" + key + "&fmt=json"
        else:
            url = eod_url(key, sym, from_date="2026-09-01")
        st, ct, _body = fetch(url)
        reachable[sym] = {"status": st, "content_type": ct}
        log(f"F1 reachable probe {sym}: HTTP {st}")
        if st == -1:
            return write_blockverdict("F1.reachable", {"probes": reachable,
                                                       "error": "network-layer failure (redacted)"})
    live = [s for s in CANARIES if s != CANARY_NEVER]
    if not all(reachable[s]["status"] == 200 for s in live):
        return write_blockverdict("F1.reachable", {"probes": reachable})
    if reachable[CANARY_NEVER]["status"] != 404:
        return write_blockverdict("F1.reachable", {
            "probes": reachable, "error": "never-existed canary did not 404"})

    # permitted: owner entitlement terms evidence exists in-cycle (V8 bytes re-hashed;
    # V13-lineage F1 gate text read from the NG5 P0 verdict)
    terms = {
        "v8_tos": {"path": str(V8_TERMS_DIR / "tos.html"),
                   "sha256_expected": V8_TOS_SHA,
                   "sha256_measured": sha((V8_TERMS_DIR / "tos.html").read_bytes())},
        "v8_pricing": {"path": str(V8_TERMS_DIR / "pricing.html"),
                       "sha256_expected": V8_PRICING_SHA,
                       "sha256_measured": sha((V8_TERMS_DIR / "pricing.html").read_bytes())},
        "v8_probe_verdict": {"path": str(V8_PROBE_VERDICT),
                             "sha256": sha(V8_PROBE_VERDICT.read_bytes()),
                             "quote": "owner paid EODHD All-World entitlement ($19.99/mo); "
                                      "internal-research use; raw data NOT committed"},
        "v13_lineage_gate": {"path": str(NG5_P0_VERDICT),
                             "sha256": sha(NG5_P0_VERDICT.read_bytes()),
                             "quote": "F1_ENTITLEMENT_TERMS PASS: owner paid EODHD All-World "
                                      "entitlement, research use per V8 precedent"},
    }
    permitted = (terms["v8_tos"]["sha256_measured"] == V8_TOS_SHA
                 and terms["v8_pricing"]["sha256_measured"] == V8_PRICING_SHA
                 and NG5_P0_VERDICT.exists())
    if not permitted:
        return write_blockverdict("F1.permitted", {"terms_evidence": terms})

    # served: bounded /eod depth check on 2 symbols
    served: dict[str, dict] = {}
    for sym in ("QQQ", "SPY"):
        st, _ct, body = fetch(eod_url(key, sym, from_date="2026-06-01"))
        try:
            rows = json.loads(body)
            served[sym] = {"status": st, "rows": len(rows),
                           "fields": sorted(rows[0].keys()) if rows else [],
                           "has_adjusted_close": bool(rows) and "adjusted_close" in rows[0],
                           "has_volume": bool(rows) and "volume" in rows[0]}
        except Exception:  # noqa: BLE001
            served[sym] = {"status": st, "rows": 0, "parse_error": True}
    if not (served["QQQ"]["status"] == 200 and served["SPY"]["status"] == 200
            and served["QQQ"].get("has_adjusted_close") and served["SPY"].get("has_adjusted_close")
            and served["QQQ"].get("has_volume") and served["SPY"].get("has_volume")):
        return write_blockverdict("F1.served", {"served": served})
    log("F1 three-layer gate PASS (reachable/permitted/served)")

    # ------------- F2 liveness: double-pull identity + identical absent semantics
    dp = []
    for _ in range(2):
        st, _ct, body = fetch(eod_url(key, "QQQ", from_date="2026-09-01"))
        dp.append((st, body))
    try:
        vals = [sorted(json.loads(b), key=lambda r: r["date"]) for st, b in dp if st == 200]
    except Exception:  # noqa: BLE001
        vals = []
    identity = {"statuses": [s for s, _ in dp],
                "byte_identical": dp[0][1] == dp[1][1],
                "value_identical": len(vals) == 2 and vals[0] == vals[1],
                "records": len(vals[0]) if vals else 0}
    abs_sem = []
    for _ in range(2):
        st, _ct, body = fetch("https://eodhd.com/api/eod/" + CANARY_NEVER
                              + ".US?api_token=" + key + "&fmt=json")
        abs_sem.append({"status": st, "sha256": sha(body)})
    absent = {"pulls": abs_sem,
              "identical_absent_semantics": (abs_sem[0]["status"] == abs_sem[1]["status"] == 404
                                             and abs_sem[0]["sha256"] == abs_sem[1]["sha256"])}
    f2_pass = identity["value_identical"] and absent["identical_absent_semantics"]
    log(f"F2 double-pull value-identical={identity['value_identical']} "
        f"absent-identical={absent['identical_absent_semantics']}")

    # ------------- F3 adjusted-series contract on AAPL (quarterly dividends; 2020-08-31 4:1 split)
    st3, _ct, body3 = fetch(eod_url(key, "AAPL", from_date=WINDOW_START))
    rows3 = json.loads(body3) if st3 == 200 else []
    f3: dict = {"status": st3, "rows": len(rows3)}
    if rows3:
        closes = np.array([r["close"] for r in rows3], dtype=float)
        adjc = np.array([r["adjusted_close"] for r in rows3], dtype=float)
        fac = adjc / closes
        step = fac[1:] / fac[:-1]
        idx = np.where(np.abs(step - 1.0) > 1e-4)[0]
        split_idx = idx[(step[idx] > 1.5) | (step[idx] < 1 / 1.5)]
        div_idx = np.setdiff1d(idx, split_idx)
        f3.update({
            "convention": "adjusted = total-return basis, THE single representation (P-12); "
                          "factor f_t = adjusted_close_t/close_t is multiplicative within a "
                          "session; adjusted open/high/low = raw x f_t; state and any later "
                          "returns all read the SAME adjusted series",
            "factor_steps_gt_1bp": int(len(idx)),
            "first_divergence": rows3[int(idx[0]) + 1]["date"] if len(idx) else None,
            "dividend_like_steps": {
                "n": int(len(div_idx)),
                "median_gap_sessions": (float(np.median(np.diff(div_idx)))
                                        if len(div_idx) > 2 else None),
                "example": ({"date": rows3[int(div_idx[-1]) + 1]["date"],
                             "step": round(float(step[div_idx[-1]]), 6),
                             "close_that_day": float(closes[int(div_idx[-1]) + 1])}
                            if len(div_idx) else None),
                "reading": "step at ex-date ~= 1 - div/close: the adjusted series absorbs "
                           "the cash dividend (total-return basis)"},
            "split_like_steps": [{"date": rows3[int(j) + 1]["date"],
                                  "step": round(float(step[j]), 6)} for j in split_idx],
            "split_note": "AAPL 4:1 split ex 2020-08-31 appears as a ~4.0 ratio step; "
                          "dividend and split steps are absorbed by the SAME adjusted series "
                          "— the single representation is pinned here",
        })
    f3_pass = st3 == 200 and f3.get("factor_steps_gt_1bp", 0) > 0
    log(f"F3 AAPL: {f3.get('factor_steps_gt_1bp')} factor steps, "
        f"splits={len(f3.get('split_like_steps', []))}")

    # ------------- F4 cohort re-pin (V9 lineage identity, sha-verified)
    cohort_bytes = COHORT_SOURCE.read_bytes()
    cohort_sha = sha(cohort_bytes)
    if cohort_sha != COHORT_SHA_EXPECTED:
        return write_blockverdict("F4.cohort_identity", {
            "expected": COHORT_SHA_EXPECTED, "measured": cohort_sha,
            "source": str(COHORT_SOURCE)})
    cv9 = json.loads(cohort_bytes)
    members: list[dict] = []
    by_ticker: dict[str, list[int]] = {}
    for bucket in ("ALIVE_EVIDENCED", "DEAD_EVIDENCED"):
        for m in cv9["members"][bucket]:
            tkr = (m.get("ticker") or m.get("ticker_eodhd") or "").strip().upper()
            if not tkr:
                continue
            idx = len(members)
            members.append({
                "cik": m["cik"],
                "ticker": tkr,
                "bucket": bucket,
                "name": m.get("name") or m.get("eodhd_name"),
                "sector": m.get("sector"),
                "death_date": (m.get("death_filing_date_evidence")
                               if bucket == "DEAD_EVIDENCED" else None),
                "join_method": m.get("join_method"),
            })
            by_ticker.setdefault(tkr, []).append(idx)
    shared = {t: idxs for t, idxs in by_ticker.items() if len(idxs) > 1}
    for idxs in shared.values():
        for i in idxs:
            members[i]["ticker_reuse_risk"] = True
    symbols = sorted(by_ticker)
    cohort_manifest = {
        "schema": "stocks_ng6_cohort_repin@1",
        "source_path": str(COHORT_SOURCE),
        "source_sha256": cohort_sha,
        "expected_sha256": COHORT_SHA_EXPECTED,
        "lineage": "V9 census lineage (cohort_v9.json, sha re-verified at P0); "
                   "re-pinned for STOCKS-NG6",
        "counts": {"members": len(members), "unique_tickers": len(symbols),
                   "alive": sum(1 for m in members if m["bucket"] == "ALIVE_EVIDENCED"),
                   "dead": sum(1 for m in members if m["bucket"] == "DEAD_EVIDENCED"),
                   "shared_tickers": len(shared)},
        "identity_law": "events attach to TICKER (one served series each); members sharing "
                        "a ticker are flagged ticker_reuse_risk and never silently merged",
        "measured_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    (COHORT_DIR / "cohort_manifest.json").write_text(
        json.dumps(cohort_manifest, indent=1, sort_keys=True) + "\n")
    (COHORT_DIR / "cohort_members.json").write_text(
        json.dumps(members, indent=0, sort_keys=True) + "\n")
    log(f"F4 cohort re-pinned: {json.dumps(cohort_manifest['counts'])}")

    # ------------- heavy retrieval: chunked (per symbol), resumable cache, backoff, heartbeats
    all_syms = symbols + (["SPY"] if "SPY" not in by_ticker else [])
    retrieval: dict[str, dict] = {}
    fails: list[dict] = []
    rows_total = 0
    bytes_total = 0
    for k_idx, sym in enumerate(all_syms):
        gzp = CACHE / f"{sym}.json.gz"
        rows = None
        raw = None
        if gzp.exists():
            try:
                raw = gzip.decompress(gzp.read_bytes())
                rows = json.loads(raw)
            except Exception:  # noqa: BLE001
                gzp.unlink(missing_ok=True)
                rows = None
        if rows is None:
            got = False
            st = -9
            for attempt in range(3):
                st, _ct, body = fetch(eod_url(key, sym))
                if st == 200:
                    try:
                        rows = json.loads(body)
                        raw = body
                        got = True
                        break
                    except Exception:  # noqa: BLE001
                        st = -2
                if st == 404:
                    retrieval[sym] = {"status": 404, "unserved": True}
                    break
                time.sleep(1.5 * (attempt + 1))  # backoff, no infinite retries
                beat({"phase": "retrieval_backoff", "symbol": sym, "attempt": attempt})
            if not got:
                if sym not in retrieval:
                    fails.append({"symbol": sym, "status": st})
                beat({"phase": "retrieval", "done": k_idx, "symbols": len(all_syms)})
                continue
            gzp.write_bytes(gzip.compress(raw, 6))
            time.sleep(0.05)  # yielding etiquette between pulls
        if retrieval.get(sym, {}).get("status") == 404:
            continue
        dates = [r["date"] for r in rows]
        retrieval[sym] = {
            "status": 200, "rows": len(rows),
            "bytes_raw": len(raw), "sha256_raw": sha(raw),
            "sha256_gz": sha(gzp.read_bytes()),
            "first": min(dates) if dates else None,
            "last": max(dates) if dates else None,
        }
        rows_total += len(rows)
        bytes_total += len(raw)
        if k_idx % 25 == 0:
            (HERE / "retrieval_manifest.json").write_text(json.dumps({
                "schema": "stocks_ng6_retrieval_manifest@1",
                "window": WINDOW_START, "in_progress": True,
                "http_requests": HTTP["n"], "rows_total": rows_total,
                "bytes_total": bytes_total, "pulls": retrieval}, indent=1, sort_keys=True) + "\n")
        beat({"phase": "retrieval", "done": k_idx, "symbols": len(all_syms),
              "rows_total": rows_total, "bytes_total": bytes_total})
    fail_rate = len(fails) / max(1, len(all_syms))
    retrieval_manifest = {
        "schema": "stocks_ng6_retrieval_manifest@1",
        "window": WINDOW_START, "in_progress": False,
        "http_requests": HTTP["n"], "rows_total": rows_total,
        "bytes_total": bytes_total,
        "pull_fail_rate": round(fail_rate, 5),
        "pulls": retrieval,
        "law": "raw bytes live gitignored under data_raw/stocks_ng6_eod/; THIS manifest "
               "(sha256 per pull) is committed; a detached rerun re-pulls and must "
               "reproduce digests or name a source revision",
    }
    (HERE / "retrieval_manifest.json").write_text(
        json.dumps(retrieval_manifest, indent=1, sort_keys=True) + "\n")
    log(f"retrieval done: {len(all_syms)} symbols, {rows_total} rows, "
        f"{bytes_total/1e6:.0f}MB raw, fails={len(fails)}")

    # ------------- census (run twice for F9); SPY served sessions = calendar grid
    spy_rows = json.loads(gzip.decompress((CACHE / "SPY.json.gz").read_bytes()))
    spy_dates = sorted({r["date"] for r in spy_rows})
    spy_dates = [d for d in spy_dates if d >= WINDOW_START]
    n_s = len(spy_dates)
    spy_sessions = {
        "F1": (spy_dates[0], spy_dates[n_s // 3 - 1]),
        "F2": (spy_dates[n_s // 3], spy_dates[2 * n_s // 3 - 1]),
        "F3": (spy_dates[2 * n_s // 3], spy_dates[-1]),
    }
    fold_of: dict[str, str] = {}
    for fid, (a, b) in spy_sessions.items():
        for d in spy_dates:
            if a <= d <= b:
                fold_of[d] = fid
    death_by_ticker = {m["ticker"]: m["death_date"] for m in members if m["death_date"]}

    def run_census():
        per_name: dict[str, dict] = {}
        all_events: list[dict] = []
        sc = {"names_served": 0, "names_unserved_404": 0, "names_warmup_attrition_lt253": 0,
              "names_ge253": 0, "total_rows": 0, "dup_dates_removed": 0,
              "weekend_rows": 0, "hl_violations": 0, "nonpositive_adj_closes": 0,
              "drops_total": {k: 0 for k in EMPTY_DROPS}}
        for sym in all_syms:
            rec = retrieval.get(sym, {})
            if rec.get("status") != 200:
                sc["names_unserved_404"] += 1
                per_name[sym] = {"status": rec.get("status"), "sessions": 0, "events": 0}
                continue
            rows = json.loads(gzip.decompress((CACHE / f"{sym}.json.gz").read_bytes()))
            seen: set[str] = set()
            rows2 = []
            for r in rows:
                if r["date"] in seen:
                    sc["dup_dates_removed"] += 1
                    continue
                seen.add(r["date"])
                rows2.append(r)
            rows2.sort(key=lambda r: r["date"])
            dates = [r["date"] for r in rows2]
            o = np.array([r["open"] for r in rows2], dtype=float)
            h = np.array([r["high"] for r in rows2], dtype=float)
            l = np.array([r["low"] for r in rows2], dtype=float)
            c = np.array([r["close"] for r in rows2], dtype=float)
            ac = np.array([r["adjusted_close"] for r in rows2], dtype=float)
            v = np.array([r["volume"] for r in rows2], dtype=float)
            f = np.divide(ac, c, out=np.ones_like(ac), where=c != 0)
            ao, ah, al = o * f, h * f, l * f
            sc["total_rows"] += len(rows2)
            sc["weekend_rows"] += weekend_count(dates)
            sc["hl_violations"] += int(((ah < al) | (ac > ah) | (ao < al)).sum())
            sc["nonpositive_adj_closes"] += int((ac <= 0).sum())
            n = len(dates)
            if n < WARMUP_SESSIONS + 1:
                sc["names_warmup_attrition_lt253"] += 1
                per_name[sym] = {"status": 200, "sessions": n,
                                 "first": dates[0] if dates else None,
                                 "last": dates[-1] if dates else None,
                                 "warmup_attrition": True, "events": 0,
                                 "drops": {k: 0 for k in EMPTY_DROPS}}
                continue
            sc["names_ge253"] += 1
            events, drops = compute_events(dates, ao, ah, al, ac, v)
            for k2, n2 in drops.items():
                sc["drops_total"][k2] += n2
            dth = death_by_ticker.get(sym)
            n_inh = 0
            for ev in events:
                ev["in_horizon_death"] = bool(
                    dth and dates[ev["i"]] < dth <= dates[min(ev["i"] + HORIZON_FILL_LAG, n - 1)])
                ev["symbol"] = sym
                n_inh += 1 if ev["in_horizon_death"] else 0
                all_events.append(ev)
            per_name[sym] = {"status": 200, "sessions": n, "first": dates[0],
                             "last": dates[-1], "events": len(events),
                             "bookable_events": sum(1 for e in events if e["bookable"]),
                             "in_horizon_deaths": n_inh, "drops": drops}
        per_fold = {fid: {"events": 0, "bookable_events": 0, "in_horizon_deaths": 0,
                          "death_names": set(),
                          "bands": {b: 0 for b in BAND_KEYS}}
                    for fid in spy_sessions}
        for ev in all_events:
            fid = fold_of.get(ev["date"])
            if fid is None:
                continue
            pf = per_fold[fid]
            pf["events"] += 1
            pf["bands"][ev["band"]] += 1
            if ev["bookable"]:
                pf["bookable_events"] += 1
            if ev["in_horizon_death"]:
                pf["in_horizon_deaths"] += 1
                pf["death_names"].add(ev["symbol"])
        for pf in per_fold.values():
            pf["death_names"] = sorted(pf["death_names"])
        total_bands = {b: 0 for b in BAND_KEYS}
        for pf in per_fold.values():
            for b, n2 in pf["bands"].items():
                total_bands[b] += n2
        n_all = len(all_events)
        result = {
            "total_events": n_all,
            "bookable_events": sum(1 for e in all_events if e["bookable"]),
            "in_horizon_death_events": sum(1 for e in all_events if e["in_horizon_death"]),
            "per_name": {s: per_name[s] for s in sorted(per_name)},
            "per_fold": per_fold,
            "band_counts_on_events": total_bands,
            "band_shares_on_events": {b: {"n": total_bands[b],
                                          "share": round(total_bands[b] / max(1, n_all), 6)}
                                      for b in BAND_KEYS},
            "served_census": sc,
        }
        return result, sha(json.dumps(result, sort_keys=True).encode()), all_events

    census1, digest1, all_events = run_census()
    census2, digest2, _ = run_census()
    f9 = {"rerun_identical_digest": digest1 == digest2, "census_digest": digest1}
    log(f"F9 rerun identical={f9['rerun_identical_digest']}; "
        f"events={census1['total_events']} bookable={census1['bookable_events']}")

    # full event listing (census only — symbol + decision date + flags; NO PnL)
    ev_list = [{"symbol": e["symbol"], "date": e["date"], "bookable": e["bookable"],
                "band": e["band"], "in_horizon_death": e["in_horizon_death"]}
               for e in sorted(all_events, key=lambda e: (e["date"], e["symbol"]))]
    ev_blob = json.dumps(ev_list, sort_keys=True).encode()
    (HERE / "events_census.json.gz").write_bytes(gzip.compress(ev_blob, 6))

    # ------------- F8 fold freeze + Q-6 floor (on BOOKABLE events, fail-closed)
    bookable_fold_counts = {fid: census1["per_fold"][fid]["bookable_events"]
                            for fid in spy_sessions}
    fold_floor_error = None
    try:
        check_fold_floor(bookable_fold_counts)
        fold_floor_ok = True
    except FoldFloorError as exc:
        fold_floor_ok = False
        fold_floor_error = str(exc)
    folds_doc = {
        "schema": "stocks_ng6_fold_freeze@1",
        "frozen_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "window": [spy_dates[0], spy_dates[-1]],
        "sessions": n_s,
        "grid": "SPY served sessions (SPY serves every XNYS regular session); "
                "boundaries are calendar thirds, independent of event data",
        "folds": [{"id": fid, "start": spy_sessions[fid][0], "end": spy_sessions[fid][1],
                   "events_censused": census1["per_fold"][fid]["events"],
                   "bookable_events_censused": bookable_fold_counts[fid]}
                  for fid in ("F1", "F2", "F3")],
        "regime_law": "window 2015+: 2020-03 deleveraging sits in F2, the 2022 bear in F3; "
                      "2008Q4-2009 predates the window so the never-share rule is moot",
        "q6_floor": {"floor": FOLD_EVENT_FLOOR, "basis": "bookable events",
                     "counts": bookable_fold_counts, "pass": fold_floor_ok,
                     "error": fold_floor_error},
    }
    (HERE / "folds.json").write_text(json.dumps(folds_doc, indent=1, sort_keys=True) + "\n")

    # ------------- F6 band majority + operative stress note
    bands = census1["band_shares_on_events"]
    majority_c = bands["C"]["share"] > 0.5
    f6 = {
        "band_schedule_bps": BAND_BPS,
        "bands_def_trailing252_median_dvol": BANDS_DEF,
        "measured_on": "EVENT population (not cohort average); basis = trailing 252-session "
                       "median dollar volume at the event session",
        "shares": bands,
        "majority_band_C": majority_c,
        "operative_stress_note": (
            "majority-band-C event population: the preregistered stress "
            "25bps x 2 fills x 2.0 = 100 bps/round-trip is the OPERATIVE ceiling (A4 BC-6)"
            if majority_c else
            "event population is NOT majority-band-C; the 100 bps/round-trip preregistered "
            "worst-case ceiling stands as declared"),
    }

    # ------------- F7 SPY benchmark leg: THIS cycle's own depth + liveness probe
    spy_rec = retrieval["SPY"]
    st_spy2, _ct, body_spy2 = fetch(eod_url(key, "SPY", from_date="2026-09-01"))
    spy_tail = sorted(json.loads(gzip.decompress((CACHE / "SPY.json.gz").read_bytes())),
                      key=lambda r: r["date"])[-30:]
    spy2_vals = sorted(json.loads(body_spy2), key=lambda r: r["date"]) if st_spy2 == 200 else []
    # liveness = value-identity of the fresh bounded re-pull against the cached
    # series ON THE DATES THE FRESH PULL COVERS (F2 semantics; a whole-list ==
    # against the 30-row cached tail can never hold and measures nothing)
    tail_by_date = {r["date"]: r for r in spy_tail}
    overlap = [(r, tail_by_date[r["date"]]) for r in spy2_vals if r["date"] in tail_by_date]
    overlap_identical = bool(overlap) and all(a == b for a, b in overlap)
    f7 = {"depth": {"rows": spy_rec["rows"], "first": spy_rec["first"],
                    "last": spy_rec["last"], "sha256_raw": spy_rec["sha256_raw"]},
          "liveness": {"status": st_spy2, "records": len(spy2_vals),
                       "overlap_records": len(overlap),
                       "value_identical": overlap_identical},
          "probe": "re-evidenced by THIS cycle's own bounded pulls (sha-pinned in "
                   "retrieval_manifest.json)",
          "construction": "SPY buy-and-hold, exposure-matched, total-return basis "
                          "(adjusted channel); E-stage computes it, never P0"}
    f7_pass = (st_spy2 == 200 and f7["liveness"]["value_identical"]
               and spy_rec["rows"] > 2000)

    # ------------- F5 clock fixture (golden suite lives in pytest)
    t_dec, t_ent, t_ext = clock_legs(0)
    f5 = {"decision": "session t close", "entry": "session t+1 open",
          "exit": "session t+11 open (H=10)",
          "selfcheck_indices": {"t": t_dec, "t_entry": t_ent, "t_exit": t_ext},
          "tz_dst": "session-dated daily bars; no intraday clock; DST shifts wall-clock "
                    "only; session set from the served session grid",
          "golden_suite": "tests/test_stocks_ng6_p0.py::test_clock_fixture_golden"}

    # ------------- F10 SEC control authority (LOCAL verification ONLY; no bulk retrieval)
    f10: dict = {"law": "FTD + N-PORT are D2 NON-SCORED controls; A3 contract binding",
                 "ftd_zips_verified": [], "a3_rulings": {}}
    f10_pass = False
    try:
        mft = json.loads(FDF_FTD_MANIFEST.read_text())
        by_name = {Path(e["raw_path"]).name: e for e in mft if e.get("raw_path")}
        for fname in FTD_VERIFY_FILES:
            local = FDF_FTD_RAW_DIR / fname
            entry = by_name.get(fname)
            if local.exists() and entry:
                measured = sha(local.read_bytes())
                f10["ftd_zips_verified"].append({
                    "file": fname, "manifest_sha256": entry.get("raw_sha256"),
                    "measured_sha256": measured,
                    "match": measured == entry.get("raw_sha256")})
            else:
                f10["ftd_zips_verified"].append({"file": fname, "match": False,
                                                 "reason": "missing locally or not in manifest"})
        a3 = json.loads(A3_DOSSIER.read_text())
        f10["a3_rulings"] = {
            "dossier_path": str(A3_DOSSIER),
            "dossier_sha256": sha(A3_DOSSIER.read_bytes()),
            "ftd": a3["headline_rulings"]["ftd"],
            "nport": a3["headline_rulings"]["nport"],
            "operative": ["FTD availability guard >= 16d (settlement date is NEVER availability)",
                          "historical FTD joins RETROSPECTIVE_ONLY",
                          "N-PORT INERT this cycle (INSUFFICIENT_COVERAGE)"],
            "no_bulk_retrieval": True,
        }
        f10_pass = (len(f10["ftd_zips_verified"]) == 2
                    and all(z.get("match") for z in f10["ftd_zips_verified"]))
    except Exception as exc:  # noqa: BLE001
        f10["error"] = redact(str(exc))[:300]

    # ------------- gates + verdict
    pulls_ok = fail_rate <= 0.05
    gates = {
        "F1_ENTITLEMENT_TERMS": {"verdict": "PASS",
                                 "detail": {"reachable": reachable, "permitted": permitted,
                                            "served": served, "terms_evidence": terms}},
        "F2_LIVENESS_RETRIEVAL": {"verdict": "PASS" if (f2_pass and pulls_ok) else "FAIL",
                                  "detail": {"double_pull": identity,
                                             "absent_semantics": absent,
                                             "retrieval": {"symbols": len(all_syms),
                                                           "rows": rows_total,
                                                           "bytes_raw": bytes_total,
                                                           "fail_rate": round(fail_rate, 5),
                                                           "fails": fails[:20]}}},
        "F3_ADJUSTED_CONTRACT": {"verdict": "PASS" if f3_pass else "FAIL", "detail": f3},
        "F4_COHORT_COVERAGE": {"verdict": "PASS", "detail": {
            "cohort": cohort_manifest["counts"],
            "served_census": census1["served_census"],
            "warmup_attrition_names_lt253": census1["served_census"]["names_warmup_attrition_lt253"],
            "first_eligible_event": "253rd served session (construction-enforced)",
            "total_events": census1["total_events"],
            "bookable_events": census1["bookable_events"],
            "in_horizon_death_events": census1["in_horizon_death_events"],
            "per_fold_death_census_BC7a": {
                fid: {"events": census1["per_fold"][fid]["events"],
                      "bookable_events": census1["per_fold"][fid]["bookable_events"],
                      "in_horizon_deaths": census1["per_fold"][fid]["in_horizon_deaths"],
                      "death_names": census1["per_fold"][fid]["death_names"]}
                for fid in ("F1", "F2", "F3")}}},
        "F5_CLOCK_EXECUTION": {"verdict": "PASS", "detail": f5},
        "F6_COST_BANDS": {"verdict": "PASS" if census1["band_counts_on_events"]["UNRESOLVED"] == 0
                          else "FAIL", "detail": f6},
        "F7_SPY_BENCHMARK": {"verdict": "PASS" if f7_pass else "FAIL", "detail": f7},
        "F8_FOLD_FREEZE": {"verdict": "PASS" if fold_floor_ok else "FAIL", "detail": folds_doc},
        "F9_REPRODUCIBILITY": {"verdict": "PASS" if f9["rerun_identical_digest"] else "FAIL",
                               "detail": f9},
        "F10_SEC_CONTROL_AUTHORITY": {"verdict": "PASS" if f10_pass else "FAIL", "detail": f10},
    }
    verdict = "P0_PASS" if all(g["verdict"] == "PASS" for g in gates.values()) else "P0_FAIL"
    out = {
        "schema": "stocks_ng6_p0_verdict@1",
        "cycle_id": "STOCKS-NG6",
        "plan": "plans/PLAN_stocks_ng6.md §4",
        "measured_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": round(time.time() - t0, 1),
        "http_requests": HTTP["n"],
        "no_pnl_computed": True,
        "gates": gates,
        "census_digest": digest1,
        "events_census_sha256": sha(ev_blob),
        "folds_sha256": sha((HERE / "folds.json").read_bytes()),
        "retrieval_manifest_sha256": sha((HERE / "retrieval_manifest.json").read_bytes()),
        "verdict": verdict,
    }
    (HERE / "p0_verdict.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    log(f"VERDICT {verdict} in {out['runtime_seconds']}s, {HTTP['n']} requests")
    return 0 if verdict == "P0_PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
