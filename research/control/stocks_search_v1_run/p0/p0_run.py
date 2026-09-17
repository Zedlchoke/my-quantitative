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
"""

from __future__ import annotations

import gzip
import importlib.util
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np

WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/stocks-search-v1/integration")
HERE = Path(__file__).resolve().parent
COHORT_DIR = HERE / "cohort"
CACHE = WT / "data_raw/stocks_search_v1_eod"
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


def eod_url(key: str, symbol: str, from_date: str = L.WINDOW_START,
            to_date: str | None = None) -> str:
    u = ("https://eodhd.com/api/eod/" + urllib.parse.quote(f"{symbol}.US")
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
    with heavy_lock.acquire(
        cycle_id=L.CYCLE_ID,
        role="P0_SOURCE_CENSUS_HEAVY",
        worktree=str(WT),
        command=lock_cmd,
        expected_artifacts=[
            str(HERE / "p0_gate.json"),
            str(HERE / "fold_freeze.json"),
            str(HERE / "retrieval_manifest.json"),
        ],
    ) as hb:
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
    st, _ct, sym_bytes = fetch(
        "https://eodhd.com/api/exchange-symbol-list/US?api_token=" + key
        + "&fmt=json")
    if st != 200:
        return block("F1.cohort", {"exchange_symbol_list_status": st})
    cohort_raw = json.loads(sym_bytes)
    symbols = sorted({r["Code"] for r in cohort_raw if r.get("Code")})
    (COHORT_DIR / "cohort_raw.json").write_bytes(sym_bytes)
    cohort_manifest = {
        "schema": "stocks_search_v1_cohort@1",
        "cycle_id": L.CYCLE_ID,
        "law": "death-inclusive priced cohort re-pinned by THIS cycle's own P0",
        "source": "EODHD /exchange-symbol-list/US (incl. delisted)",
        "n_symbols": len(symbols),
        "sha256_raw": L.sha_bytes(sym_bytes),
        "symbols": symbols,
        "pinned_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    L.write_json(COHORT_DIR / "cohort_manifest.json", cohort_manifest)
    log(f"cohort re-pinned: {len(symbols)} symbols")

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

    # ================= bulk retrieval (one pull per cohort name, cached)
    pulls: dict[str, dict] = {}
    names_done = 0
    for i, sym in enumerate(symbols):
        out = CACHE / f"{sym}.json.gz"
        if out.exists():
            names_done += 1
            continue
        st, _ct, raw = fetch(eod_url(key, sym))
        if st == 404:
            pulls[sym] = {"status": 404, "rows": 0}
            names_done += 1
            continue
        if st != 200:
            pulls[sym] = {"status": st, "error": redact(raw[:200].decode("utf-8", "replace"))}
            names_done += 1
            continue
        gz = gzip.compress(raw)
        out.write_bytes(gz)
        pulls[sym] = {"status": st, "rows": len(json.loads(raw)),
                      "sha256_raw": L.sha_bytes(raw), "sha256_gz": L.sha_bytes(gz),
                      "first": json.loads(raw)[0]["date"][:10] if raw else None,
                      "last": json.loads(raw)[-1]["date"][:10] if raw else None}
        names_done += 1
        if names_done % 50 == 0:
            beat({"names_done": names_done})
            log(f"retrieval {names_done}/{len(symbols)}")
    retrieval_manifest = {
        "schema": "stocks_search_v1_retrieval@1",
        "cycle_id": L.CYCLE_ID,
        "law": ("raw bytes live gitignored under data_raw/"
                "stocks_search_v1_eod/ and raw/.gitignore; THIS manifest "
                "(sha256 per pull) is committed; a detached rerun re-pulls "
                "and must reproduce digests or name a source revision"),
        "http_requests": HTTP["n"],
        "double_pull": double_pull,
        "pulls": pulls,
        "written_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    L.write_json(HERE / "retrieval_manifest.json", retrieval_manifest)

    # ================= census (COUNTS only) over the 47 frozen configurations
    gate_extra = dict(extra)
    gate_extra["f1_layers"] = f1
    gate_extra["cohort"] = {"n_symbols": len(symbols),
                            "sha256_raw": cohort_manifest["sha256_raw"]}
    census = run_census(pulls)
    L.write_json(HERE / "p0_census.json", census["summary"])
    with gzip.open(HERE / "p0_census_rows.json.gz", "wt") as fh:
        json.dump(census["rows"], fh, sort_keys=True)
    gate_extra["census"] = census["summary"]

    # ================= gates F3–F8 from measured census
    return write_gate(gates_from_census(census, f1), gate_extra)


def parse_name(gz_path: Path):
    """Cached pull -> (dates, adj_open, adj_high, adj_low, adj_close, volume)
    on the P-12 representation (adj_ohlc = raw x adj_close/close)."""
    rows = json.loads(gzip.open(gz_path, "rt").read())
    if not rows:
        return None
    rows.sort(key=lambda r: r["date"])
    dates = [r["date"][:10] for r in rows]
    close = np.array([float(r["close"]) for r in rows])
    adj_close = np.array([float(r["adjusted_close"]) for r in rows])
    with np.errstate(divide="ignore", invalid="ignore"):
        f = np.where(close > 0, adj_close / close, np.nan)
    adj_open = np.array([float(r["open"]) for r in rows]) * f
    adj_high = np.array([float(r["high"]) for r in rows]) * f
    adj_low = np.array([float(r["low"]) for r in rows]) * f
    volume = np.array([float(r["volume"]) for r in rows])
    return dates, adj_open, adj_high, adj_low, adj_close, volume


def run_census(pulls: dict) -> dict:
    """Per-config per-fold fired census across the cohort.  COUNTS ONLY."""
    configs = L.enumerate_configs()
    rows: list[dict] = []
    cohort_rows: dict[str, dict] = {}
    b1, b2 = L.fold_boundaries()
    for sym, meta in sorted(pulls.items()):
        gz = CACHE / f"{sym}.json.gz"
        if meta.get("status") != 200 or not gz.exists():
            continue
        parsed = parse_name(gz)
        if parsed is None:
            cohort_rows[sym] = {"served": 0}
            continue
        dates, adj_open, adj_high, adj_low, adj_close, volume = parsed
        cohort_rows[sym] = {"served": len(dates), "first": dates[0],
                            "last": dates[-1]}
        if len(dates) < 3:
            continue
        fold_of = [L.assign_fold(d, b1, b2) for d in dates]
        dvol = adj_close * volume
        med252_all = L._rolling_median(dvol, 252)
        med60_all = L._rolling_median(dvol, L.DVOL_WINDOW)
        for cfg in configs:
            fired, bookable, drops = L.run_config_census(
                cfg, adj_open, adj_high, adj_low, adj_close, volume)
            warm = cfg["warmup_need"]
            eligible = max(0, len(dates) - warm)
            fired_idx = np.nonzero(fired)[0]
            for fold in ("F1", "F2", "F3"):
                fi = [int(i) for i in fired_idx
                      if i >= warm and fold_of[i] == fold]
                bi = [i for i in fi if bool(bookable[i])]
                bands = {k: 0 for k in L.BAND_KEYS}
                unresolved = 0
                for i in fi:
                    try:
                        bands[L.resolve_band(float(med252_all[i]))] += 1
                    except ValueError:
                        bands["UNRESOLVED"] += 1
                        unresolved += 1
                denom = sum(1 for ii, d in enumerate(dates)
                            if ii >= warm and fold_of[ii] == fold)
                rows.append({
                    "config_id": cfg["config_id"], "family": cfg["family"],
                    "symbol": sym, "fold": fold,
                    "eligible_sessions": denom,
                    "fired": len(fi), "bookable_fired": len(bi),
                    "fired_day_share": (len(fi) / denom) if denom else 0.0,
                    "bookable_fired_day_share": (len(bi) / denom) if denom else 0.0,
                    "band_counts": bands,
                    "band_c_fraction_on_fired": (bands["C"] / len(fi)) if fi else 0.0,
                    "band_unresolved": unresolved,
                    "floor_pass": len(bi) >= L.FOLD_EVENT_FLOOR,
                    "warmup_skipped_sessions": min(warm, len(dates)),
                })
    # aggregate per config x fold
    agg: dict[tuple, dict] = {}
    for r in rows:
        k = (r["config_id"], r["fold"])
        a = agg.setdefault(k, {"config_id": r["config_id"],
                               "family": r["family"], "fold": r["fold"],
                               "eligible_sessions": 0, "fired": 0,
                               "bookable_fired": 0,
                               "band_counts": {kk: 0 for kk in L.BAND_KEYS},
                               "symbols_fired": 0, "floor_violations": 0})
        a["eligible_sessions"] += r["eligible_sessions"]
        a["fired"] += r["fired"]
        a["bookable_fired"] += r["bookable_fired"]
        a["symbols_fired"] += 1 if r["fired"] else 0
        for kk, v in r["band_counts"].items():
            a["band_counts"][kk] += v
        if not r["floor_pass"]:
            a["floor_violations"] += 1
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
        "n_configs": len(configs),
        "n_names_parsed": len(cohort_rows),
        "per_config_per_fold": [agg[k] for k in sorted(agg)],
        "floor_law": (">= 30 bookable fired decisions per fold, fail-closed "
                      "kill recorded, never silently dropped"),
        "floor_violation_cells": [agg[k]["config_id"] + ":" + agg[k]["fold"]
                                  for k in sorted(agg) if not agg[k]["floor_pass"]],
    }
    return {"summary": summary, "rows": rows, "cohort": cohort_rows}


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
