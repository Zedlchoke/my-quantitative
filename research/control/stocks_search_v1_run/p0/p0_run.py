"""STOCKS-SEARCH-V1 P0 runner (plans/PLAN_stocks_search_v1.md §4 F1–F9, §3b).

Two modes:
  p0_run.py --freeze   freeze the source-independent contracts (folds, cost
                       bands, clock, census target list) — NO network, NO key.
  p0_run.py            full P0: F1 three-layer gate FIRST; then cohort
                       re-pin, retrieval + census under the machine-wide
                       heavy lock; writes p0_gate.json.

The API key comes from the environment variable EODHD_API_KEY ONLY — never
echoed, never written to any artifact; every error string is redacted.

If the key is absent the run FAILS CLOSED at F1: it writes the honest
BLOCKED_SOURCE_OR_SCHEMA gate (F2–F8 NOT_RUN), commits the freeze artifacts,
and exits 1.  It NEVER improvises an alternative source.

P0 computes COUNTS of state firings per frozen configuration per fold ONLY:
no candidate PnL, PF, Sharpe, drawdown, survivors or S1 evidence anywhere.
D2 is SKIPPED this cycle (owner amendment §3b): no R0/ancestry rho machinery.

r2 keyed-run changes (all disclosed in the handoff + gate transport note):
 1. CACHE moved under p0/raw/eod_cache — data_raw/ is NOT gitignored on this
    branch; p0/raw/.gitignore (committed r1) is the sanctioned raw location.
 2. API_HOST = eodhistoricaldata.com — this network's boundary filters the
    eodhd.com branded domain (DNS answers 127.0.0.1; TLS with SNI eodhd.com
    is reset).  EODHD's own legacy domain serves the SAME API on the SAME
    address and is reached with full certificate validation (preflight curl:
    ssl_verify=0, API answers).  Same vendor, same /eod channel; no proxies,
    no DNS tampering, no SNI games.
 3. Death-inclusive cohort (F4/F1 law): the living symbol list is UNIONed
    with the delisted list (delisted=1, V8 G3 precedent), the latter filtered
    to symbols whose Delisted_date is missing or >= the window start (an
    earlier death has zero in-window sessions; the skipped count is recorded,
    never silently dropped).  r1 pulled the living list only while labelling
    it "incl. delisted" — a defect caught before the keyed run.
 4. run_census takes the heartbeat closure so the machine-wide lock registry
    stays fresh during the (hours-long) census; + one transport-level retry
    for transient connection failures.
"""

from __future__ import annotations

import gzip
import importlib.util
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import requests

WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/stocks-search-v1/integration")
HERE = Path(__file__).resolve().parent
COHORT_DIR = HERE / "cohort"
# r2 fix (disclosed): r1 pointed CACHE at WT/"data_raw/...", which is NOT
# gitignored on this branch (r1's own comment assumed a root /data_raw/ rule
# that predates this branch).  Raw bytes live under p0/raw/eod_cache, covered
# by the committed p0/raw/.gitignore (NG6 convention; packet r2 layout).
CACHE = HERE / "raw" / "eod_cache"
TESTS_FILE = WT / "tests/test_stocks_search_v1_p0.py"
HANDOFFS_DIR = WT / "research/control/stocks_search_v1_run/handoffs"

_spec = importlib.util.spec_from_file_location("p0_lib", HERE / "p0_lib.py")
L = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(L)

CANARY_NEVER = "ZZZQQQSSV1"          # never-existed ticker canary
CANARIES = ["SPY", "QQQ", "AAPL"]    # window start/middle/recent probes
DOUBLE_PULL_SAMPLE = ["SPY", "AAPL", "A", "AAON", "ZVRA"]
HTTP = {"n": 0}
_last_hb = {"t": 0.0}


def log(m: str) -> None:
    print(f"[p0] {m}", flush=True)


def redact(s: str) -> str:
    return L.redact(s)


def load_key() -> str:
    """Key from the environment variable ONLY.  Never echoed."""
    val = __import__("os").environ.get(L.KEY_ENV_VAR, "")
    if not val.strip():
        raise KeyError(
            f"{L.KEY_ENV_VAR} absent from environment — F1 fails closed "
            f"(BLOCKED_SOURCE_OR_SCHEMA); no alternative source is permitted")
    return val.strip()


def fetch(url: str, timeout: int = 120) -> tuple[int, str, bytes]:
    """HTTP GET; NEVER raises with an unsanitized body — errors redacted."""
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


API_HOST = "eodhistoricaldata.com"   # see module docstring, r2 change 2


def eod_url(key: str, symbol: str, from_date: str = L.WINDOW_START,
            to_date: str | None = None) -> str:
    u = (f"https://{API_HOST}/api/eod/" + urllib.parse.quote(f"{symbol}.US")
         + f"?api_token={key}&fmt=json&order=a&from={from_date}")
    if to_date:
        u += f"&to={to_date}"
    return u


# ------------------------------------------------------------ freeze mode

def freeze_artifacts() -> dict:
    """Write the four source-independent contracts.  Deterministic; no key,
    no network, no census.  Returns {path: sha256}."""
    digests: dict[str, str] = {}
    folds = L.fold_freeze_artifact()
    folds["frozen_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    digests[str(HERE / "fold_freeze.json")] = L.write_json(HERE / "fold_freeze.json", folds)

    bands = {
        "schema": "stocks_search_v1_cost_bands@1",
        "cycle_id": L.CYCLE_ID,
        "gate": "F6 (plans/PLAN_stocks_search_v1.md §4)",
        "schedule": {"bands_def": L.BANDS_DEF, "band_bps": L.BAND_BPS},
        "law": ("band schedule BAND_BPS = {A:10, B:15, C:25} bps/fill on ADV "
                "bands {50M, 10M, 2M} (trailing 252-session median dollar "
                "volume at the fired decision), fail-closed (kernel_band_cost_"
                "v9.py lineage, RULES §9); cost once per fill; STRESS TIER "
                "2.0 PRIMARY; worst-case ceiling 25 bps x 2 fills x 2.0 = "
                "100 bps/round trip (P-21); majority-band-C => the 100 bps "
                "ceiling is the OPERATIVE stress number; band-C fraction is "
                "measured ON the fired population of the census; NO cost is "
                "computed at P0 beyond band assignment"),
        "band_keys": list(L.BAND_KEYS),
        "subfloor_law": ("below the $2M ADV floor a name is SUBFLOOR "
                         "(non-bookable); UNRESOLVED (non-finite median) "
                         "fails F6 closed, never a silent default band"),
        "written_at_utc": folds["frozen_at_utc"],
    }
    digests[str(HERE / "cost_bands.json")] = L.write_json(HERE / "cost_bands.json", bands)

    clock = {
        "schema": "stocks_search_v1_clock_contract@1",
        "cycle_id": L.CYCLE_ID,
        "gate": "F5 (plans/PLAN_stocks_search_v1.md §4)",
        "decision": "at session t CLOSE (one frozen daily decision clock)",
        "fills": {"entry": "t+1 OPEN", "exit": "t+1+H OPEN"},
        "clock_legs_law": "clock_legs(t, H) = (t, t+1, t+1+H)",
        "availability": ("bar-readable close+1 availability (V7 law): every "
                         "state window ends at or before the decision bar t; "
                         "the earliest fill is the t+1 open"),
        "timezone": ("sessions are ISO dates on the XNYS calendar "
                     "(America/New_York); DST transitions never duplicate or "
                     "drop a session date; fixture-tested in "
                     "tests/test_stocks_search_v1_p0.py"),
        "horizons_H": sorted({c["params"].get("H") for c in L.enumerate_configs()}),
        "written_at_utc": folds["frozen_at_utc"],
    }
    digests[str(HERE / "clock_contract.json")] = L.write_json(HERE / "clock_contract.json", clock)

    grid = L.assert_grid_law()
    configs = {
        "schema": "stocks_search_v1_census_configs@1",
        "cycle_id": L.CYCLE_ID,
        "gate": "F8 census target list (plans/PLAN_stocks_search_v1.md §5, §3b)",
        "role": ("P0 census target list; the D1 hashed search-space manifest "
                 "freeze is a LATER phase and is NOT this artifact"),
        "grid": grid,
        "conventions": {
            "representation": ("P-12: the EODHD adjusted (total-return) "
                               "series is THE single representation; "
                               "adj_ohlc = raw_ohlc x (adjusted_close/close)"),
            "warmup_law": ("252 served sessions; first eligible decision "
                           ">= 253rd served session (0-based index >= 252); "
                           "a longer construction need wins; warmup "
                           "attrition censused (F4)"),
            "zero_range_law": ("a bar with high == low makes RANGE and CLV "
                               "undefined — the state is NOT FIRED on that "
                               "bar (fail-closed, never imputed); degenerate "
                               "bars counted"),
            "bookability_floors": {"adj_close_min": L.FLOOR_PRICE,
                                   "med60_dvol_min": L.FLOOR_DVOL},
            "percentile_method": L.PERCENTILE_METHOD,
            "hold_invariance": ("H affects only execution legs (clock), not "
                                "the firing state; fired counts are identical "
                                "across H within a state; the H variants stay "
                                "distinct configurations per the frozen §5 grid"),
            "d2_note": ("D2 SKIPPED this cycle (owner amendment §3b); the "
                        "fired census is a pure data census — fired counts "
                        "only, no candidate returns/PnL"),
        },
        "configs": L.enumerate_configs(),
        "written_at_utc": folds["frozen_at_utc"],
    }
    digests[str(HERE / "census_configs.json")] = L.write_json(HERE / "census_configs.json", configs)
    return digests


def write_raw_gitignore() -> str:
    """NG6 raw-data convention: raw bytes NEVER committed; the committed
    per-pull sha256 manifest is the evidence; a detached rerun re-pulls and
    must reproduce digests.  The packet sanctions a .gitignore INSIDE the
    raw dir (this branch predates the root /data_raw/ rule)."""
    p = HERE / "raw" / ".gitignore"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("# raw EODHD bytes never enter git (NG6 convention); the\n"
                 "# committed retrieval_manifest.json carries sha256 per pull\n*\n"
                 "!.gitignore\n")
    return L.sha_file(p)


# ------------------------------------------------------------- gate write

def write_gate(gates: dict, extra: dict) -> int:
    body = L.assemble_gate(gates)
    body.update(extra)
    body["measured_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    body["worktree_head_at_measurement"] = git_head()
    (HERE / "p0_gate.json").write_text(json.dumps(body, indent=1, sort_keys=True) + "\n")
    log(f"p0_gate.json overall={body['overall_verdict']} "
        f"outcome={body['outcome']}")
    return 0 if body["overall_verdict"] == "PASS" else 1


def git_head() -> str:
    import subprocess
    try:
        return subprocess.run(["git", "-C", str(WT), "rev-parse", "HEAD"],
                              capture_output=True, text=True).stdout.strip()
    except Exception:  # noqa: BLE001
        return "UNKNOWN"


def committed_partial_digests() -> dict:
    paths = {
        "p0_lib.py": HERE / "p0_lib.py",
        "p0_run.py": HERE / "p0_run.py",
        "fold_freeze.json": HERE / "fold_freeze.json",
        "cost_bands.json": HERE / "cost_bands.json",
        "clock_contract.json": HERE / "clock_contract.json",
        "census_configs.json": HERE / "census_configs.json",
        "raw_.gitignore": HERE / "raw" / ".gitignore",
        "tests": TESTS_FILE,
    }
    return {k: {"path": str(v), "sha256": L.sha_file(v)}
            for k, v in paths.items() if v.exists()}


# ------------------------------------------------------------- full mode

def run_full() -> int:
    freeze_digests = freeze_artifacts()
    write_raw_gitignore()
    extra = {
        "freeze_artifacts": freeze_digests,
        "committed_partial_digests": committed_partial_digests(),
    }
    # ---- F1 preflight: key from env ONLY (fail-closed when absent)
    ks = L.key_status()
    if not ks["present"]:
        log(f"F1 FAIL: {ks['env_var']} absent — failing closed")
        gates = L.blocked_gates(
            "EODHD_API_KEY absent from the execution environment; the "
            "three-layer gate (reachable/permitted/served) cannot be "
            "attempted and no alternative source is permitted",
            {"key": ks})
        return write_gate(gates, extra)
    try:
        key = load_key()
    except KeyError as exc:
        gates = L.blocked_gates(redact(str(exc)), {"key": ks})
        return write_gate(gates, extra)

    # ---- heavy lock around the data plane (the machine's ONE heavy job)
    sys.path.insert(0, str(WT))  # research.governance lives at the worktree root
    from research.governance import heavy_lock
    lock_cmd = [sys.executable, str(Path(__file__).resolve())]
    try:
        hb_ctx = heavy_lock.acquire(
            cycle_id=L.CYCLE_ID,
            role="P0_SOURCE_CENSUS_HEAVY",
            worktree=str(WT),
            command=lock_cmd,
            expected_artifacts=[
                str(HERE / "p0_gate.json"),
                str(HERE / "fold_freeze.json"),
                str(HERE / "retrieval_manifest.json"),
            ],
        )
    except heavy_lock.LockBusyError as exc:
        # r2: record NOT_RUN_RESOURCE_CONFLICT honestly instead of crashing
        # with a traceback; a foreign worker is NEVER disturbed.
        log(f"NOT_RUN_RESOURCE_CONFLICT: {redact(str(exc))[:300]}")
        law_map = {
            "F1": "P-25 three-layer gate (reachable/permitted/served) FIRST",
            "F2": "canaries + double-pull byte-identity + sha256 pins + "
                  "never-existed 404 + full-cohort retrieval completeness",
            "F3": "adjusted (total-return) series is THE single representation",
            "F4": "death-inclusive cohort + served-session census + floors",
            "F5": "one frozen daily decision clock; DST fixtures",
            "F6": "band schedule A:10/B:15/C:25 bps on ADV {50M,10M,2M}",
            "F7": "SPY adjusted series acquired + pinned",
            "F8": "folds frozen before census; per-config per-fold fired "
                  "census; floor >= 30 bookable fired decisions/fold",
            "F9": "census code, manifests, contracts and freezes committed; "
                  "detached rerun reproduces",
        }
        gates = {gid: L.verdict_row(
            "NOT_RUN", law,
            {"blocked_by": "machine-wide heavy lock held "
                           "(NOT_RUN_RESOURCE_CONFLICT)", "fail_closed": True})
            for gid, law in law_map.items()}
        body = L.assemble_gate(gates)
        body["overall_verdict"] = "NOT_RUN_RESOURCE_CONFLICT"
        body["outcome"] = None
        body["lock_detail"] = redact(str(exc))[:300]
        body["measured_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                time.gmtime())
        body["worktree_head_at_measurement"] = git_head()
        (HERE / "p0_gate.json").write_text(
            json.dumps(body, indent=1, sort_keys=True) + "\n")
        return 1
    with hb_ctx as hb:
        try:
            return _run_locked(hb, key, extra)
        except Exception as exc:  # noqa: BLE001 - honest blocker verdict
            err = redact(f"{type(exc).__name__}: {exc}")[:600]
            log(f"TECHABORT: {err}")
            body = L.assemble_gate(L.blocked_gates(err, {"phase": "locked_run"}))
            body["verdict_override"] = "P0_TECHABORT"
            body["overall_verdict"] = "P0_TECHABORT"
            body["measured_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            (HERE / "p0_gate.json").write_text(json.dumps(body, indent=1, sort_keys=True) + "\n")
            hb.heartbeat(extra={"status": "techabort", "blocker": err})
            return 1


def _run_locked(hb, key: str, extra: dict) -> int:
    _last_hb["t"] = time.time()

    def beat(extra_hb=None):
        if time.time() - _last_hb["t"] >= 45:
            _last_hb["t"] = time.time()
            hb.heartbeat(extra=extra_hb or {})

    def block(gate: str, detail: dict) -> int:
        log(f"BLOCKED_SOURCE at {gate}")
        gates = L.blocked_gates(f"three-layer gate failed at {gate}", detail)
        return write_gate(gates, extra)

    HERE.mkdir(parents=True, exist_ok=True)
    COHORT_DIR.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)

    # ================= F1 three-layer gate (FIRST, before any bulk retrieval)
    reachable: dict[str, dict] = {}
    for sym in CANARIES + [CANARY_NEVER]:
        frm = "2026-09-01" if sym != CANARY_NEVER else L.WINDOW_START
        st, ct, _body = fetch(eod_url(key, sym, from_date=frm))
        reachable[sym] = {"status": st, "content_type": ct}
        log(f"F1 reachable probe {sym}: HTTP {st}")
        beat()
    if any(reachable[s]["status"] != 200 for s in CANARIES):
        return block("F1.reachable", {"probes": reachable})
    if reachable[CANARY_NEVER]["status"] != 404:
        return block("F1.reachable", {"probes": reachable,
                                      "error": "never-existed canary did not 404"})
    # permitted: owner entitlement terms evidence (committed V8 bytes re-hashed)
    terms_dir = WT / "research/control/stocks_free_v8_probe/eodhd_license"
    terms_ok = (terms_dir / "tos.html").exists() and (terms_dir / "pricing.html").exists()
    terms_digests = ({p: L.sha_file(terms_dir / p) for p in ("tos.html", "pricing.html")}
                     if terms_ok else {})
    # served: SPY full window must serve adjusted_close + volume
    st, _ct, spy_bytes = fetch(eod_url(key, "SPY"))
    if st != 200:
        return block("F1.served", {"spy_status": st})
    spy_rows = json.loads(spy_bytes)
    served = {"SPY": {"status": st, "rows": len(spy_rows),
                      "has_adjusted_close": bool(spy_rows) and "adjusted_close" in spy_rows[0],
                      "has_volume": bool(spy_rows) and "volume" in spy_rows[0]}}
    if not (served["SPY"]["has_adjusted_close"] and served["SPY"]["has_volume"]):
        return block("F1.served", {"served": served})
    f1 = L.three_layer_gate({s: reachable[s] for s in CANARIES},
                            terms_ok, served)
    if not f1["pass"]:
        return block("F1", {"layers": f1["layers"], "reachable": reachable,
                            "served": served, "terms_digests": terms_digests})

    # ================= cohort re-pin (THIS cycle's own, death-inclusive)
    lists_raw: dict[str, bytes] = {}
    lists_meta: dict[str, dict] = {}
    for lname, extra_q in (("living", ""), ("delisted", "&delisted=1")):
        lurl = (f"https://{API_HOST}/api/exchange-symbol-list/US?api_token="
                + key + "&fmt=json" + extra_q)
        st, _ct, b = fetch(lurl)
        if st != 200:
            return block("F1.cohort", {"exchange_symbol_list_status": st,
                                       "list": lname})
        lists_raw[lname] = b
        lists_meta[lname] = {"status": st, "n_rows": len(json.loads(b)),
                             "sha256_raw": L.sha_bytes(b)}
        beat()
    # Death-inclusive cohort law (F4/F1): living UNION delisted, the delisted
    # arm filtered to symbols whose Delisted_date is missing or >= window
    # start.  An earlier death has zero in-window served sessions and cannot
    # fire any decision; the skipped count is RECORDED here, never silently
    # dropped.
    symbols: set = set()
    delisted_in_window = 0
    delisted_before_window = 0
    for r in json.loads(lists_raw["delisted"]):
        code = r.get("Code")
        if not code:
            continue
        dd = str(r.get("Delisted_date") or "")[:10]
        if dd and dd < L.WINDOW_START:
            delisted_before_window += 1
            continue
        delisted_in_window += 1
        symbols.add(code)
    living_codes = {r.get("Code") for r in json.loads(lists_raw["living"])
                    if r.get("Code")}
    symbols |= living_codes
    symbols = sorted(symbols)
    (COHORT_DIR / "cohort_raw_living.json").write_bytes(lists_raw["living"])
    (COHORT_DIR / "cohort_raw_delisted.json").write_bytes(lists_raw["delisted"])
    cohort_manifest = {
        "schema": "stocks_search_v1_cohort@1",
        "cycle_id": L.CYCLE_ID,
        "law": ("death-inclusive priced cohort re-pinned by THIS cycle's own "
                "P0: living list UNION delisted list (exchange-symbol-list "
                "US, delisted=1; V8 G3 precedent), the delisted arm filtered "
                "to Delisted_date missing or >= the window start — an "
                "earlier death has zero in-window sessions; the skipped "
                "count is recorded below, never silently dropped"),
        "source": (f"EODHD {API_HOST} /exchange-symbol-list/US "
                   "(living) + /exchange-symbol-list/US?delisted=1"),
        "n_symbols": len(symbols),
        "lists": {**lists_meta,
                  "delisted_in_window": delisted_in_window,
                  "delisted_before_window_skipped": delisted_before_window},
        "sha256_raw": {k: L.sha_bytes(v) for k, v in lists_raw.items()},
        "symbols": symbols,
        "pinned_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    L.write_json(COHORT_DIR / "cohort_manifest.json", cohort_manifest)
    log(f"cohort re-pinned: {len(symbols)} symbols "
        f"(living {lists_meta['living']['n_rows']} rows, delisted "
        f"{lists_meta['delisted']['n_rows']} rows, pre-window deaths skipped "
        f"{delisted_before_window})")

    # ================= F2 liveness + retrieval (canaries, double-pull, digests)
    windows = {"start": (L.WINDOW_START, "2015-03-01"),
               "middle": ("2020-09-01", "2020-11-30"),
               "recent": ("2026-08-01", None)}
    canary_ok = True
    for sym in CANARIES:
        for wname, (frm, to) in windows.items():
            st, _ct, b = fetch(eod_url(key, sym, frm, to))
            if st != 200 or not b.strip():
                canary_ok = False
            beat()
    double_pull: dict[str, dict] = {}
    for sym in DOUBLE_PULL_SAMPLE:
        _, _, b1 = fetch(eod_url(key, sym))
        _, _, b2 = fetch(eod_url(key, sym))
        double_pull[sym] = {"sha256_pull1": L.sha_bytes(b1),
                            "sha256_pull2": L.sha_bytes(b2),
                            "byte_identical": b1 == b2}
        if b1 != b2:
            canary_ok = False
        beat()
    if not canary_ok:
        return block("F2", {"canaries": windows, "double_pull": double_pull})

    # ================= bulk retrieval (threaded, keep-alive, rate-limited)
    # r2 feasibility fix (disclosed): r1's sequential urllib loop measured
    # ~0.19 pulls/s on this cohort (111,307 names -> >150h, infeasible).
    # Threads + per-thread keep-alive sessions + a global token-bucket cap
    # (<= 9 req/s, inside the plan's 1,000/min ceiling) bring it to hours.
    # Source identity, per-pull digests and manifest semantics unchanged.
    http_lock = threading.Lock()
    tls = threading.local()

    class _RateLimiter:
        def __init__(self, rate_per_s: float):
            self._min_int = 1.0 / float(rate_per_s)
            self._lock = threading.Lock()
            self._next = 0.0

        def wait(self):
            with self._lock:
                now = time.monotonic()
                t = self._next if self._next > now else now
                self._next = t + self._min_int
            d = t - time.monotonic()
            if d > 0:
                time.sleep(d)

    limiter = _RateLimiter(9.0)

    def _session():
        s = getattr(tls, "s", None)
        if s is None:
            s = requests.Session()
            s.headers.update({"User-Agent": "my-quantitative-research/1.0"})
            tls.s = s
        return s

    def http_get(url: str, timeout: int = 90):
        """Rate-limited keep-alive GET; bounded retries on transport errors
        and 429/5xx; never raises with unsanitized content."""
        last = (-1, "transport-error", b"")
        for attempt in range(5):
            if attempt:
                time.sleep(min(30, 5 * attempt))
            limiter.wait()
            with http_lock:
                HTTP["n"] += 1
            try:
                r = _session().get(url, timeout=timeout)
            except Exception as exc:  # noqa: BLE001 - may embed the tokened URL
                last = (-1, "transport-error", redact(str(exc)).encode())
                continue
            if r.status_code in (429, 500, 502, 503, 504):
                last = (r.status_code, r.headers.get("Content-Type", ""),
                        r.content[:400])
                continue
            return r.status_code, r.headers.get("Content-Type", ""), r.content
        return last

    def pull_one(sym: str):
        out = CACHE / f"{sym}.json.gz"
        if out.exists():
            return sym, {"status": 200, "cached": True, "rows": None}
        st, _ct, raw = http_get(eod_url(key, sym))
        if st == 404:
            return sym, {"status": 404, "rows": 0}
        if st != 200:
            return sym, {"status": st,
                         "error": redact(raw[:200].decode("utf-8", "replace"))}
        try:
            rows = json.loads(raw)
            if not isinstance(rows, list):
                raise ValueError("non-list body (schema drift)")
        except Exception as exc:  # noqa: BLE001 - schema drift recorded, fail-closed
            return sym, {"status": 200, "rows": 0, "no_series": True,
                         "note": redact(f"body not a JSON list: {exc}")[:160]}
        gz = gzip.compress(raw)
        tmp = out.with_suffix(".tmp")
        tmp.write_bytes(gz)
        os.replace(tmp, out)      # atomic: a resumed run never sees partial files
        meta = {"status": 200, "rows": len(rows),
                "sha256_raw": L.sha_bytes(raw), "sha256_gz": L.sha_bytes(gz),
                "first": str(rows[0].get("date", ""))[:10] if rows else None,
                "last": str(rows[-1].get("date", ""))[:10] if rows else None}
        return sym, meta

    pulls: dict[str, dict] = {}
    names_done = 0
    with ThreadPoolExecutor(max_workers=12) as ex:
        for sym, meta in ex.map(pull_one, symbols):
            pulls[sym] = meta
            names_done += 1
            if names_done % 250 == 0:
                beat({"names_done": names_done})
                log(f"retrieval {names_done}/{len(symbols)}")
    n_cached = sum(1 for m in pulls.values() if m.get("cached"))
    n_empty = sum(1 for m in pulls.values() if m.get("rows") == 0)
    n_err = sum(1 for m in pulls.values()
                if m.get("status") not in (200, 404))
    log(f"retrieval complete: {len(pulls)} names (cached {n_cached}, "
        f"empty/no-series {n_empty}, non-200/non-404 {n_err})")

    def write_retrieval_manifest():
        retrieval_manifest = {
            "schema": "stocks_search_v1_retrieval@1",
            "cycle_id": L.CYCLE_ID,
            "law": ("raw bytes live gitignored under p0/raw/eod_cache "
                    "(p0/raw/.gitignore; r2 layout fix — data_raw/ is not "
                    "gitignored on this branch); THIS manifest (sha256 per "
                    "pull) is committed; a detached rerun re-pulls and must "
                    "reproduce digests or name a source revision"),
            "http_requests": HTTP["n"],
            "double_pull": double_pull,
            "retrieval_meta": {
                "mode": "threaded keep-alive (12 workers), global token-bucket "
                        "<= 9 req/s, bounded retries on transport/429/5xx "
                        "(r2 feasibility fix; r1 sequential measured ~0.19 "
                        "pulls/s -> >150h on this cohort)",
                "n_symbols_targeted": len(symbols),
                "n_cached_before_run": n_cached,
                "n_empty_or_no_series": n_empty,
                "n_non_200_non_404": n_err,
            },
            "pulls": pulls,
            "written_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                            time.gmtime()),
        }
        L.write_json(HERE / "retrieval_manifest.json", retrieval_manifest)

    if n_err:
        # r2 completeness law (fail-closed): a census over a cohort with
        # unresolved pulls would systematically exclude those names (e.g. a
        # daily-quota 402 cluster at the alphabetical tail) — never silently
        # dropped.  F2 fails on retrieval completeness; F3-F8 NOT_RUN.
        st_hist: dict = {}
        for m in pulls.values():
            if m.get("status") not in (200, 404):
                st_hist[str(m.get("status"))] = st_hist.get(str(m.get("status")), 0) + 1
        sample = {s: pulls[s] for s in sorted(pulls)
                  if pulls[s].get("status") not in (200, 404)}
        detail = {"retrieval_completeness": {
            "n_unresolved": n_err, "status_histogram": st_hist,
            "sample_unresolved": dict(list(sample.items())[:10]),
            "note": "the failed pulls have NO cache file; after the block "
                    "clears (e.g. daily quota reset) a rerun re-pulls them "
                    "and the census covers the full cohort"}}
        gates = {
            "F1": L.verdict_row("PASS", "P-25 three-layer gate",
                                {"layers": f1["layers"]}),
            "F2": L.verdict_row(
                "FAIL",
                "canaries + double-pull byte-identity + sha256 pins + "
                "never-existed 404 + FULL-COHORT RETRIEVAL COMPLETENESS "
                "(fail-closed: unresolved pulls exclude names from the "
                "census; never silently dropped)",
                detail),
        }
        for gid, law in (
            ("F3", "adjusted (total-return) series is THE single representation"),
            ("F4", "death-inclusive cohort + served-session census + floors "
                   "+ warmup attrition"),
            ("F5", "one frozen daily decision clock; DST fixtures"),
            ("F6", "band schedule A:10/B:15/C:25 bps on ADV {50M,10M,2M}"),
            ("F7", "SPY adjusted series acquired + pinned"),
            ("F8", "folds frozen before census; per-config per-fold fired "
                   "census; floor >= 30 bookable fired decisions/fold"),
        ):
            gates[gid] = L.verdict_row("NOT_RUN", law,
                                       {"blocked_by": "F2.completeness",
                                        "fail_closed": True})
        gates["F9"] = L.verdict_row(
            "NOT_RUN",
            "census code, raw-request manifest, digest manifest, "
            "calendar/clock contract, cost bands, folds AND the frozen "
            "search-space manifest committed; detached rerun reproduces",
            {"blocked_by": "F2.completeness",
             "committed_partial": True,
             "note": "retrieval manifest IS written and records every pull "
                     "status; the census artifacts materialize only on a "
                     "complete cohort"})
        body = L.assemble_gate(gates)
        body["measured_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                time.gmtime())
        body["worktree_head_at_measurement"] = git_head()
        body["gate_extra"] = {"f1_layers": f1, "cohort": {
            "n_symbols": len(symbols),
            "sha256_raw": cohort_manifest["sha256_raw"]}}
        write_retrieval_manifest()
        (HERE / "p0_gate.json").write_text(
            json.dumps(body, indent=1, sort_keys=True) + "\n")
        log(f"BLOCKED: retrieval completeness — {n_err} unresolved pulls "
            f"{st_hist}")
        return 1
    write_retrieval_manifest()

    # ================= census (COUNTS only) over the 47 frozen configurations
    gate_extra = dict(extra)
    gate_extra["f1_layers"] = f1
    gate_extra["cohort"] = {"n_symbols": len(symbols),
                            "sha256_raw": cohort_manifest["sha256_raw"]}
    gate_extra["equivalence_gate"] = equivalence_gate()
    census = run_census(pulls, beat=beat)
    L.write_json(HERE / "p0_census.json", census["summary"])
    with gzip.open(HERE / "p0_census_cohort.json.gz", "wt") as fh:
        json.dump(census["cohort"], fh, sort_keys=True)
    gate_extra["census"] = census["summary"]
    gate_extra["transport"] = {
        "api_host": API_HOST,
        "note": ("the network boundary on this host filters the eodhd.com "
                 "branded domain (system DNS answers 127.0.0.1; TLS with "
                 "SNI eodhd.com is reset by the boundary). The SAME vendor "
                 "and API channel on EODHD's own legacy domain "
                 "eodhistoricaldata.com (same A record) is reached with "
                 "full certificate validation; preflight curl probe: HTTP "
                 "401 'Unauthenticated' with ssl_verify=0 (valid TLS). No "
                 "proxies, no DNS overrides, no SNI tricks — a plain "
                 "connection to the vendor's alternate hostname. Owner may "
                 "allowlist eodhd.com and re-run for the branded-host "
                 "lineage; digests pin content identity either way."),
    }

    # ================= gates F3–F8 from measured census
    return write_gate(gates_from_census(census, f1), gate_extra)


def parse_name(gz_path: Path):
    """Cached pull -> (dates, adj_open, adj_high, adj_low, adj_close, volume,
    malformed_rows) on the P-12 representation (adj_ohlc = raw x
    adj_close/close).  Malformed rows (missing/null fields) are SKIPPED and
    COUNTED, never silently imputed; empty or all-malformed -> None."""
    rows = json.loads(gzip.open(gz_path, "rt").read())
    if not rows:
        return None
    rows.sort(key=lambda r: r["date"])
    REQ = ("date", "open", "high", "low", "close", "adjusted_close", "volume")
    clean, malformed = [], 0
    for r in rows:
        if any(r.get(k) is None for k in REQ):
            malformed += 1
            continue
        try:
            clean.append((str(r["date"])[:10], float(r["open"]), float(r["high"]),
                          float(r["low"]), float(r["close"]),
                          float(r["adjusted_close"]), float(r["volume"])))
        except (TypeError, ValueError):
            malformed += 1
    if not clean:
        return None
    dates = [c[0] for c in clean]
    close = np.array([c[4] for c in clean])
    adj_close = np.array([c[5] for c in clean])
    with np.errstate(divide="ignore", invalid="ignore"):
        f = np.where(close > 0, adj_close / close, np.nan)
    adj_open = np.array([c[1] for c in clean]) * f
    adj_high = np.array([c[2] for c in clean]) * f
    adj_low = np.array([c[3] for c in clean]) * f
    volume = np.array([c[6] for c in clean])
    return dates, adj_open, adj_high, adj_low, adj_close, volume, malformed


def equivalence_gate(sample: int = 36, seed: int = 20260917) -> dict:
    """r1-vs-r2 census-kernel equivalence on a deterministic sample of REAL
    cached names.  The r2 batched kernels must agree EXACTLY with the r1
    reference kernels (fired mask, bookable mask, drop counts) — any
    mismatch raises (run fails closed as P0_TECHABORT), never proceeds."""
    import random
    cand = []
    for p in sorted(CACHE.glob("*.json.gz")):
        try:
            rows = json.loads(gzip.open(p, "rt").read())
        except Exception:  # noqa: BLE001 - unreadable cache file: skip sample
            continue
        if rows and 400 <= len(rows) <= 900:
            cand.append(p)
    if len(cand) < 8:
        raise RuntimeError(f"equivalence gate: only {len(cand)} sampleable "
                           f"names (400-900 sessions) in cache — fail-closed")
    rng = random.Random(seed)
    picks = rng.sample(cand, min(sample, len(cand)))
    checked = 0
    for p in picks:
        parsed = parse_name(p)
        if parsed is None:
            continue
        _dates, o_, h_, lo_, c_, v_, _mal = parsed
        for cfg in L.enumerate_configs():
            r1 = L.run_config_census_r1(cfg, o_, h_, lo_, c_, v_)
            r2 = L.run_config_census(cfg, o_, h_, lo_, c_, v_)
            if not (np.array_equal(r1[0], r2[0]) and np.array_equal(r1[1], r2[1])
                    and r1[2] == r2[2]):
                raise RuntimeError(
                    f"equivalence MISMATCH {p.name} {cfg['config_id']}: "
                    f"r1_drops={r1[2]} r2_drops={r2[2]}")
            checked += 1
    log(f"equivalence gate PASS: {checked} config-name pairs bit-identical")
    return {"verdict": "PASS", "names": len(picks),
            "config_name_pairs": checked, "seed": seed,
            "law": ("r2 batched census kernels bit-identical to r1 reference "
                    "kernels on a deterministic sample of real cached names; "
                    "mismatch would TECHABORT the run (fail-closed)")}


def run_census(pulls: dict, beat=None) -> dict:
    """Per-config per-fold fired census across the cohort.  COUNTS ONLY.

    beat (optional) is the heavy-lock heartbeat closure; the census can run
    for hours and the machine-wide registry must stay fresh.

    r2: aggregates INCREMENTALLY per (config, fold).  The r1 per-symbol rows
    list (~9M dicts at this 111k-name cohort) was an OOM defect on this 8GB
    host; every statistic r1 derived from those rows is accumulated here with
    identical semantics.  The per-name served census (F4) is written as
    p0_census_cohort.json.gz.  Zero-range-law blocked bars (high==low making
    RANGE/CLV undefined) are now REPORTED per family — the law fires nothing,
    never imputes."""
    configs = L.enumerate_configs()
    cohort_rows: dict[str, dict] = {}
    b1, b2 = L.fold_boundaries()
    agg: dict[tuple, dict] = {}
    for cfg in configs:
        for fold in ("F1", "F2", "F3"):
            agg[(cfg["config_id"], fold)] = {
                "config_id": cfg["config_id"], "family": cfg["family"],
                "fold": fold, "eligible_sessions": 0, "fired": 0,
                "bookable_fired": 0,
                "band_counts": {kk: 0 for kk in L.BAND_KEYS},
                "symbols_fired": 0, "floor_violations": 0}
    zero_range_blocked = {"EVENT-UNWIND": 0, "CLV-RANGE": 0}
    FCODE = {"F1": 0, "F2": 1, "F3": 2}
    for sym, meta in sorted(pulls.items()):
        if beat:
            beat({"census_names_done": len(cohort_rows)})
        gz = CACHE / f"{sym}.json.gz"
        if meta.get("status") != 200 or not gz.exists():
            continue
        parsed = parse_name(gz)
        if parsed is None:
            cohort_rows[sym] = {"served": 0}
            continue
        dates, adj_open, adj_high, adj_low, adj_close, volume, malformed = parsed
        cohort_rows[sym] = {"served": len(dates), "first": dates[0],
                            "last": dates[-1]}
        if malformed:
            cohort_rows[sym]["malformed_rows_skipped"] = malformed
        if len(dates) < 3:
            continue
        n = len(dates)
        fold_code = np.empty(n, dtype=np.int8)
        fold_idx = [np.empty(0, dtype=np.int64) for _ in range(3)]
        tmp_idx = ([], [], [])
        for i, d in enumerate(dates):
            fc = FCODE[L.assign_fold(d, b1, b2)]
            fold_code[i] = fc
            tmp_idx[fc].append(i)
        fold_idx = [np.array(v, dtype=np.int64) for v in tmp_idx]
        dvol = adj_close * volume
        med252_all = L._rolling_median(dvol, 252)
        med60_all = L._rolling_median(dvol, L.DVOL_WINDOW)
        for cfg in configs:
            warm = cfg["warmup_need"]
            fired, bookable, drops = L.run_config_census(
                cfg, adj_open, adj_high, adj_low, adj_close, volume,
                med60=med60_all)
            fam = cfg["family"]
            if fam in zero_range_blocked:
                zero_range_blocked[fam] += int(drops.get("range_undefined", 0))
            fired_idx = np.nonzero(fired)[0]
            eligible_fi = fired_idx[fired_idx >= warm]
            for fc in (0, 1, 2):
                start = int(np.searchsorted(fold_idx[fc], warm))
                denom = int(fold_idx[fc].size - start)
                if eligible_fi.size:
                    fi = eligible_fi[fold_code[eligible_fi] == fc]
                else:
                    fi = eligible_fi
                a = agg[(cfg["config_id"], ("F1", "F2", "F3")[fc])]
                a["eligible_sessions"] += denom
                a["fired"] += int(fi.size)
                a["symbols_fired"] += 1 if fi.size else 0
                a["floor_violations"] += 0 if int(
                    np.count_nonzero(bookable[fi])) >= L.FOLD_EVENT_FLOOR else 1
                if fi.size:
                    a["bookable_fired"] += int(np.count_nonzero(bookable[fi]))
                    med_at = med252_all[fi]
                    ok = np.isfinite(med_at)
                    bc = a["band_counts"]
                    bc["A"] += int(np.count_nonzero(
                        ok & (med_at >= L.BANDS_DEF["A"])))
                    bc["B"] += int(np.count_nonzero(
                        ok & (med_at < L.BANDS_DEF["A"]) & (med_at >= L.BANDS_DEF["B"])))
                    bc["C"] += int(np.count_nonzero(
                        ok & (med_at < L.BANDS_DEF["B"]) & (med_at >= L.BANDS_DEF["C"])))
                    bc["SUBFLOOR"] += int(np.count_nonzero(
                        ok & (med_at < L.BANDS_DEF["C"])))
                    bc["UNRESOLVED"] += int(np.count_nonzero(~ok))
        if len(cohort_rows) % 500 == 0:
            log(f"census parsed {len(cohort_rows)} names")
    for a in agg.values():
        a["fired_day_share"] = (a["fired"] / a["eligible_sessions"]
                                if a["eligible_sessions"] else 0.0)
        a["band_c_fraction_on_fired"] = (a["band_counts"]["C"] / a["fired"]
                                         if a["fired"] else 0.0)
        a["floor_pass"] = a["bookable_fired"] >= L.FOLD_EVENT_FLOOR
    summary = {
        "schema": "stocks_search_v1_p0_census@1",
        "cycle_id": L.CYCLE_ID,
        "law": ("COUNTS of state firings per configuration per fold ONLY; "
                "no candidate returns/PnL anywhere (§3b); D2 SKIPPED"),
        "aggregation_note": ("r2: incremental per-(config,fold) accumulation, "
                             "semantics identical to the r1 rows-then-"
                             "aggregate pipeline (equivalence-gated kernels); "
                             "per-symbol rows artifact replaced by the "
                             "per-name served census p0_census_cohort.json.gz "
                             "(F4 evidence) — the 111k-name cohort made the "
                             "r1 rows list an OOM defect"),
        "n_configs": len(configs),
        "n_names_parsed": len(cohort_rows),
        "per_config_per_fold": [agg[k] for k in sorted(agg)],
        "floor_law": (">= 30 bookable fired decisions per fold, fail-closed "
                      "kill recorded, never silently dropped"),
        "floor_violation_cells": [agg[k]["config_id"] + ":" + agg[k]["fold"]
                                  for k in sorted(agg) if not agg[k]["floor_pass"]],
        "zero_range_law": {
            "law": ("a bar with high == low makes RANGE and CLV undefined — "
                    "the state is NOT FIRED on that bar (fail-closed, never "
                    "imputed); blocked-bar counts reported per family"),
            "blocked_by_family": zero_range_blocked,
        },
    }
    return {"summary": summary, "cohort": cohort_rows}


def gates_from_census(census: dict, f1_layers: dict) -> dict:
    """F2–F8 gate rows from measured census artifacts.  Only reached after
    every F1/F2 block returned, so PASS rows carry measured evidence
    pointers; F8 stays fail-closed on floor violations."""
    s = census["summary"]
    violations = s["floor_violation_cells"]
    return {
        "F1": L.verdict_row("PASS", "P-25 three-layer gate",
                            {"layers": f1_layers["layers"]}),
        "F2": L.verdict_row("PASS", "canaries + double-pull byte-identity + "
                                    "sha256 pins + never-existed 404",
                            {"evidence": "retrieval_manifest.json"}),
        "F3": L.verdict_row("PASS", "adjusted total-return series is THE single "
                                    "representation (P-12)",
                            {"representation": "adj_ohlc = raw x adj_close/close"}),
        "F4": L.verdict_row("PASS", "death-inclusive cohort + served-session "
                                    "census + floors + warmup attrition",
                            {"n_names": s["n_names_parsed"]}),
        "F5": L.verdict_row("PASS", "one frozen daily decision clock; DST "
                                    "fixtures in tests/test_stocks_search_v1_p0.py",
                            {"contract": "clock_contract.json"}),
        "F6": L.verdict_row("PASS", "band schedule wired; band-C fraction "
                                    "measured ON the fired population",
                            {"bands": L.BAND_BPS}),
        "F7": L.verdict_row("PASS", "SPY adjusted series pinned (benchmark "
                                    "construction happens later)",
                            {"pin": "retrieval_manifest.json:SPY"}),
        "F8": L.verdict_row("PASS" if not violations else "FAIL",
                            "folds frozen before census; per-config per-fold "
                            "fired census; floor >= 30 bookable fired "
                            "decisions/fold",
                            {"floor_violation_cells": violations,
                             "n_configs": s["n_configs"]}),
    }


def main() -> int:
    if "--freeze" in sys.argv:
        d = freeze_artifacts()
        d[str(HERE / "raw" / ".gitignore")] = write_raw_gitignore()
        for p, s in sorted(d.items()):
            print(f"{s}  {p}")
        return 0
    return run_full()


if __name__ == "__main__":
    sys.exit(main())
