#!/usr/bin/env python3
"""STOCKS-SEARCH-V1 — S lane: selection by the frozen construction-based order
(plans/PLAN_stocks_search_v1.md §5 as amended by §3b; dispatch packet ssearch-s).

WHAT THIS BUILDER DOES (outcome-blind; NO performance statistic anywhere)
  1. Verifies the frozen inputs: worktree HEAD + branch (--run only), the D1
     search-space manifest (file sha256 + self_sha256 empty-field convention),
     every P0 artifact digest (p0_lib/p0_run/census/retrieval/cohort/folds/..),
     INPUT_MISMATCH equality of the manifest's embedded census vs
     p0/p0_census.json, and mechanical re-derivation of the frozen §3b tier
     orders from p0_census.json.
  2. ONE heavy pass over the P0 cohort (read-only raw cache) rebuilding, for
     EVERY one of the 47 frozen configurations, its pooled daily position
     series using the P0 census state engines BYTE-IDENTICAL and in the P0
     CENSUS SPACE (p0_lib.run_config_census + p0_run.parse_name, hash-pinned
     before use; engines run on each name's FULL served history — warm gate
     in served-session index space, folds by decision date, full-history
     med60 — never on calendar-trimmed arrays, r3 fix).  Positions are {0,1}
     long-only counts per (name, session) pooled as a daily count series over
     the SPY-pinned session calendar by held-session DATE.  No forward
     return, PnL, PF, Sharpe or drawdown is computed anywhere.
  3. Walks the frozen round-robin order (families by F3 fired census DESC,
     configs within family by F3 fired census DESC, one config per family per
     round, <= 2 scored cells per family, until 3 cells are filled),
     adjudicating P-20 books-distinct DURING the walk: pairwise pooled |rho|
     vs every already-selected higher-ranked candidate; |rho| > 0.98 strictly
     => SELF_SUBSUMED (skip, next in frozen order); an unmeasurable rho is
     NOT_ADJUDICABLE fail-closed (stop and report, never an inferred PASS).
  4. Freezes research/control/stocks_search_v1_run/s/selection_freeze.json:
     verifications, data manifests, fold digest, calendar pin, conventions,
     the full walk record (every visited candidate, every rho, verdicts),
     and for each selected candidate the exact manifest config excerpt plus
     its arm identity hash.

MODES
  --run        full pipeline; requires HEAD == BASE_SHA and the frozen branch.
  --selfcheck  full independent recomputation (same heavy pass) and byte
               comparison against the committed selection_freeze.json.
Both modes take the machine-wide heavy lock (research.governance.heavy_lock).

Determinism: no clock, no randomness and no worktree-HEAD field inside the
freeze body; the same inputs reproduce byte-identical output on the same host
(python/numpy versions are recorded and are part of the reproduction
contract, phase R of the plan §9 chain).
"""

from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

# --------------------------------------------------------------- frozen pins
WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/stocks-search-v1/integration")
RUN_DIR = WT / "research/control/stocks_search_v1_run"
P0 = RUN_DIR / "p0"
D1 = RUN_DIR / "d1"
S_DIR = RUN_DIR / "s"
FREEZE_PATH = S_DIR / "selection_freeze.json"

CYCLE_ID = "STOCKS-SEARCH-V1"
TASK_ID = "ssearch-s"
PHASE = "S"
PLAN = "plans/PLAN_stocks_search_v1.md"

BASE_SHA = "9419b97a515c10b28bcc224300906c9c138e9194"
BRANCH = "orca/stocks-search-v1-integration"

MANIFEST_PATH = D1 / "search_space_manifest.json"
MANIFEST_SHA256 = "1ccbf668cae14dbb1e5fb31da9c87136ab70a2d1a8c9068c39ea13ed0fffb24e"
MANIFEST_SELF_SHA256 = "e0b69b41cdd8cf173f1685de9877d02b0936fee585231149efd17c0cc2bdcd42"

# P0 artifact digests pinned from the committed f9_artifact_digests.json and
# re-verified against disk at run time (belt and braces: both must agree).
P0_SHA256 = {
    "p0_lib.py": "aaa9355f3ddb235cb9179d07785da90f7ef5a646629371fa657e5808376755cc",
    "p0_run.py": "fa7e7ee2d613a4775a7d91aa4ec6f139b37a3056eb76729e8cf829b3ee2f1566",
    "p0_census.json": "9ae6606222feea23516cd80698693c70167da19f02524c40f6262d11a333f65b",
    "p0_census_cohort.json.gz": "0e3f64d300813b5cec8dcc7d6ce97c359ddf43f11b826288f61f7b20cb5a783b",
    "fold_freeze.json": "3f87a41d89f8b92fa120b7618a376be3d6ee0a60b1fb7d21b1818f483a6523a0",
    "census_configs.json": "6ffa4b8fdc9785dbf97898c43a4e6137104146f8d6df548372ab5b0e8bd4ee05",
    "cost_bands.json": "55d8e324d1cfd3228428f9c80ee3e688bb11f8db419f30f16dca79b3dee83cae",
    "clock_contract.json": "b3a68d387ed59b3a88beca548f01c1b23a8316687c78d01a7c4e74a5169a4b21",
    "retrieval_manifest.json": "2c4283c24e4a40587bfbdefdaab7831b7bccbc02af1d5e158919abf245e90d30",
    "cohort/cohort_manifest.json": "9614b37a213c3e8756689626317038f83e601838cde860d8d1c37f87c3f17f25",
}

WINDOW_START = "2015-01-02"
WINDOW_END = "2026-09-16"
P20_THRESHOLD = 0.98          # plan §5: pooled |rho| strictly > 0.98 subsumes
MAX_CELLS = 3
MAX_CELLS_PER_FAMILY = 2

BANNED_KEY_TOKENS = ("return", "pnl", "sharpe", "profit", "expectancy",
                     "drawdown", "mdd", "annual")

SCHEMA = "stocks_search_v1_selection_freeze@1"


class StopError(RuntimeError):
    """Fail-closed stop with a packet stop-condition label."""

    def __init__(self, label: str, detail: str):
        super().__init__(f"{label}: {detail}")
        self.label = label
        self.detail = detail


# ------------------------------------------------------------------ helpers

def canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def canon_sha256(obj) -> str:
    return hashlib.sha256(canon(obj)).hexdigest()


def sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def log(msg: str) -> None:
    print(f"[s] {msg}", flush=True)


class Checks:
    """Accumulated verification battery.  Every row must PASS; any FAIL is a
    fail-closed stop.  Rows are mode-INDEPENDENT so the freeze body is
    byte-reproducible across --run and --selfcheck."""

    def __init__(self):
        self.rows: list[dict] = []

    def add(self, check_id: str, ok: bool, detail) -> None:
        self.rows.append({"check_id": check_id,
                          "verdict": "PASS" if ok else "FAIL",
                          "detail": detail})
        log(f"check {check_id}: {'PASS' if ok else 'FAIL'}")
        if not ok:
            raise StopError("INPUT_MISMATCH",
                            f"check {check_id} FAILED: {detail}")

    def summary(self) -> dict:
        return {"n_checks": len(self.rows),
                "n_pass": sum(1 for r in self.rows if r["verdict"] == "PASS"),
                "rows": self.rows}


def git(*args: str) -> str:
    out = subprocess.run(["git", "-C", str(WT), *args], capture_output=True,
                         text=True)
    if out.returncode != 0:
        raise StopError("FROZEN_SHA_MISMATCH",
                        f"git {args} failed: {out.stderr}")
    return out.stdout.strip()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ------------------------------------------------------- state / warmup law

def warmup_from_params(family: str, params: dict) -> int:
    """p0_lib.enumerate_configs warmup law recomputed (WARMUP=252 base;
    longer construction need wins)."""
    WARMUP = 252
    if family == "EVENT-UNWIND":
        return max(WARMUP, params["K"])
    if family == "GAP":
        return WARMUP
    if family == "52W-HIGH":
        return WARMUP
    if family == "CLV-RANGE":
        return max(WARMUP, 20 - 1 + params["k"])
    if family == "DVOL-SHOCK":
        return WARMUP
    if family == "VOL-REGIME":
        return max(WARMUP, WARMUP - 1 + params["L"])
    raise StopError("INPUT_MISMATCH", f"unknown family {family}")


def state_maps(manifest: dict) -> tuple[dict[str, tuple], dict[tuple, int]]:
    """config_id -> state key; state key -> warmup_need.  The state key is
    (family, sorted non-H params) — H affects only execution legs, so the 47
    configurations share 22 unique firing states (p0 hold-invariance law)."""
    state_key_of: dict[str, tuple] = {}
    warmup_of: dict[tuple, int] = {}
    for cfg in manifest["configs"]:
        key = (cfg["family"],
               tuple(sorted((k, v) for k, v in cfg["params"].items()
                            if k != "H")))
        state_key_of[cfg["config_id"]] = key
        warmup_of[key] = warmup_from_params(cfg["family"], cfg["params"])
    return state_key_of, warmup_of


# ------------------------------------------------------- frozen input checks

def verify_head_and_branch() -> None:
    head = git("rev-parse", "HEAD")
    if head != BASE_SHA:
        raise StopError("FROZEN_SHA_MISMATCH",
                        f"HEAD {head} != dispatch base {BASE_SHA}")
    branch = git("branch", "--show-current")
    if branch != BRANCH:
        raise StopError("FROZEN_SHA_MISMATCH",
                        f"branch {branch} != frozen {BRANCH}")
    log(f"head/branch verified: {head} on {BRANCH}")


def verify_frozen_inputs(cks: Checks) -> tuple[dict, dict, dict]:
    """Verify manifest identity, P0 digests, census equality and the frozen
    tier derivation.  Returns (manifest, p0_census, retrieval)."""
    # --- D1 manifest identity (file bytes + self_sha256 empty-field law)
    file_sha = sha256_file(MANIFEST_PATH)
    cks.add("manifest_file_sha256", file_sha == MANIFEST_SHA256,
            {"expected": MANIFEST_SHA256, "actual": file_sha})
    manifest = json.loads(MANIFEST_PATH.read_text())
    probe = json.loads(MANIFEST_PATH.read_text())
    probe["self_sha256"] = ""
    recomputed = canon_sha256(probe)
    cks.add("manifest_self_sha256",
            manifest.get("self_sha256") == MANIFEST_SELF_SHA256
            and recomputed == MANIFEST_SELF_SHA256,
            {"claimed": manifest.get("self_sha256"), "recomputed": recomputed,
             "expected": MANIFEST_SELF_SHA256,
             "convention": "sha256(canonical_json(manifest), self_sha256='')"})
    cks.add("manifest_identity_fields",
            manifest.get("cycle_id") == CYCLE_ID
            and manifest.get("task_id") == "ssearch-d1"
            and str(manifest.get("phase", "")).startswith("D1")
            and manifest.get("base_sha") == "5be14a6d6771df8ec3c23ebc70f0044e9b87ec6e",
            {"cycle_id": manifest.get("cycle_id"),
             "task_id": manifest.get("task_id"),
             "phase": manifest.get("phase"),
             "base_sha": manifest.get("base_sha")})

    # --- P0 artifact digests: constants AND the committed f9 manifest agree
    f9 = json.loads((P0 / "f9_artifact_digests.json").read_text())
    disk = {}
    for rel, expected in P0_SHA256.items():
        actual = sha256_file(P0 / rel)
        disk[rel] = actual
        f9_entry = f9.get("sha256", {}).get(rel)
        cks.add(f"p0_digest:{rel}",
                actual == expected and f9_entry == expected,
                {"pinned": expected, "disk": actual, "f9": f9_entry})

    # --- INPUT_MISMATCH: embedded census == p0_census.json (141 rows exact)
    p0_census = json.loads((P0 / "p0_census.json").read_text())
    embedded = {}
    for cfg in manifest["configs"]:
        for fold, row in cfg["p0_census_per_fold_verbatim"].items():
            embedded[(cfg["config_id"], fold)] = row
    measured = {(r["config_id"], r["fold"]): r
                for r in p0_census["per_config_per_fold"]}
    eq = embedded.keys() == measured.keys() and all(
        canon(embedded[k]) == canon(measured[k]) for k in embedded)
    cks.add("input_census_rows_equal_141", eq,
            {"n_embedded": len(embedded), "n_measured": len(measured),
             "n_configs_manifest": len(manifest["configs"]),
             "n_configs_p0": p0_census["n_configs"]})

    # --- frozen §3b tier orders re-derive mechanically from p0_census.json
    fam_of = {c["config_id"]: c["family"] for c in manifest["configs"]}
    cf_fired: dict[str, dict[str, int]] = {}
    for r in p0_census["per_config_per_fold"]:
        cf_fired.setdefault(r["config_id"], {})[r["fold"]] = r["fired"]
    fam_f3: dict[str, int] = {}
    for cid, folds in cf_fired.items():
        fam_f3[fam_of[cid]] = fam_f3.get(fam_of[cid], 0) + folds["F3"]
    derived_fam = [k for k, _ in sorted(fam_f3.items(),
                                        key=lambda kv: (-kv[1], kv[0]))]
    st3 = manifest["selection_tier_3b"]
    cks.add("tier1_family_order",
            derived_fam == st3["family_ranking_f3_fired_desc"],
            {"derived": derived_fam,
             "frozen": st3["family_ranking_f3_fired_desc"]})
    cks.add("tier1_family_values",
            fam_f3 == st3["family_ranking_values_f3_fired"],
            {"derived": fam_f3,
             "frozen": st3["family_ranking_values_f3_fired"]})
    order_ok, order_detail = True, {}
    for fam, frozen_list in st3["per_family_config_order_f3_fired_desc"].items():
        derived = [cid for _, cid in sorted(
            ((-cf_fired[cid]["F3"], cid) for cid in frozen_list))]
        order_detail[fam] = derived == frozen_list
        order_ok = order_ok and derived == frozen_list
    cks.add("tier2_per_family_config_orders", order_ok, order_detail)

    # --- hold-invariance of the census across H within state (p0 law)
    state_key_of, _ = state_maps(manifest)
    rows_by_cid: dict[str, dict] = {}
    for r in p0_census["per_config_per_fold"]:
        rows_by_cid.setdefault(r["config_id"], {})[r["fold"]] = r
    fold_ids = ("F1", "F2", "F3")
    inv: dict[tuple, dict] = {}
    for cfg in manifest["configs"]:
        cid = cfg["config_id"]
        ref = inv.setdefault(state_key_of[cid], {"fired": set(),
                                                 "bookable": set()})
        ref["fired"].add(tuple(rows_by_cid[cid][f]["fired"] for f in fold_ids))
        ref["bookable"].add(tuple(rows_by_cid[cid][f]["bookable_fired"]
                                  for f in fold_ids))
    inv_ok = all(len(v["fired"]) == 1 and len(v["bookable"]) == 1
                 for v in inv.values())
    cks.add("census_hold_invariance_within_state", inv_ok,
            {f"{k[0]}|{json.dumps(k[1], sort_keys=True)}":
             {"n_distinct_fired_vectors": len(v["fired"]),
              "n_distinct_bookable_vectors": len(v["bookable"])}
             for k, v in sorted(inv.items(), key=lambda kv: str(kv[0]))})

    # --- warmup law: manifest pinned warmup == recomputed p0 enumeration law
    w_ok, w_detail = True, {}
    for cfg in manifest["configs"]:
        want = warmup_from_params(cfg["family"], cfg["params"])
        got = cfg.get("warmup_need_sessions")
        w_detail[cfg["config_id"]] = got == want
        w_ok = w_ok and got == want
    cks.add("warmup_need_matches_p0_law_47", w_ok,
            {"n_ok": sum(1 for v in w_detail.values() if v),
             "n": len(w_detail)})

    # --- folds: freeze digest (carried in s0_window) + window extent
    s0 = manifest["s0_window"]
    cks.add("fold_freeze_sha256",
            s0.get("sha256_fold_freeze") == P0_SHA256["fold_freeze.json"]
            and disk["fold_freeze.json"] == P0_SHA256["fold_freeze.json"],
            {"manifest_s0_window": s0.get("sha256_fold_freeze"),
             "pinned": P0_SHA256["fold_freeze.json"]})
    cks.add("s0_window", s0["start"] == WINDOW_START and s0["end"] == WINDOW_END,
            {"start": s0["start"], "end": s0["end"]})

    # --- constructions: manifest verbatim == census_configs state field (47)
    census_configs = json.loads((P0 / "census_configs.json").read_text())
    cc_rows = census_configs.get("configs") if isinstance(census_configs, dict) \
        else census_configs
    if isinstance(cc_rows, dict):
        cc_by_id = cc_rows
    else:
        cc_by_id = {r["config_id"]: r for r in cc_rows}
    con_ok, con_n = True, 0
    for cfg in manifest["configs"]:
        row = cc_by_id.get(cfg["config_id"])
        ok = row is not None and str(row.get("state")) == \
            cfg.get("construction_verbatim")
        con_ok = con_ok and ok
        con_n += 1 if ok else 0
    cks.add("construction_verbatim_equals_census_configs_47", con_ok,
            {"n_ok": con_n, "n": len(manifest["configs"])})

    retrieval = json.loads((P0 / "retrieval_manifest.json").read_text())
    cks.add("retrieval_manifest_schema",
            retrieval.get("schema") == "stocks_search_v1_retrieval@1"
            and retrieval.get("cycle_id") == CYCLE_ID,
            {"schema": retrieval.get("schema")})
    return manifest, p0_census, retrieval


# ------------------------------------------------------------ heavy pass

def build_calendar(R, cks: Checks) -> tuple[list[str], str]:
    """SPY-pinned session calendar on the S0 window (F7 benchmark pin; SPY
    trades every XNYS session, so its served dates ARE the calendar)."""
    spy_gz = R.CACHE / "SPY.json.gz"
    spy_sha = sha256_file(spy_gz)
    rows = json.loads(gzip.open(spy_gz, "rt").read())
    dates = sorted(str(r["date"])[:10] for r in rows if r.get("date") is not None)
    in_win = [d for d in dates if WINDOW_START <= d <= WINDOW_END]
    cks.add("calendar_spy_pin",
            len(in_win) == 2943
            and in_win[0] == WINDOW_START and in_win[-1] == WINDOW_END,
            {"n_sessions": len(in_win), "first": in_win[0],
             "last": in_win[-1], "spy_json_gz_sha256": spy_sha})
    return in_win, spy_sha


def heavy_pass(L, R, manifest, p0_census, retrieval, calendar, cks: Checks,
               beat=None) -> dict:
    """ONE pass over the cohort in P0 CENSUS SPACE: for every unique state the
    frozen census kernel (hash-pinned p0_lib/p0_run) runs on the name's FULL
    served history exactly as p0_run.run_census ran it — warm gate in
    served-session index space, folds assigned by decision DATE
    (L.assign_fold), med60 over the full history — and per configuration the
    pooled daily position series accumulates by mapping held-session DATES
    onto the SPY-pinned S0-window calendar (pooling only; the calendar never
    trims the engine input).  Conventions c1..c8 are pinned in
    conventions_block and disclosed in the freeze.

    r3 root-cause fix (diag_s_r3.py, bounded sample 305 names): the prior
    revision trimmed bars to the calendar BEFORE running the engines, which
    (a) shifted the served-session index space (off-calendar bars: 174 bars
    on 17/277 sample names), (b) dropped post-WINDOW_END bars that assign_fold
    maps into F3 and the frozen census COUNTED, and (c) recomputed med60 on
    trimmed arrays — three systematic drifts vs p0_census.json that failed the
    exact-equality gate on all 47 configurations (n_ok=0)."""
    state_key_of, warmup_of = state_maps(manifest)
    state_cfgs: dict[tuple, dict] = {}
    for cfg in manifest["configs"]:                 # lexicographic order
        key = state_key_of[cfg["config_id"]]
        if key not in state_cfgs:
            state_cfgs[key] = {
                "config_id": cfg["config_id"], "family": cfg["family"],
                "params": {k: v for k, v in cfg["params"].items() if k != "H"}}
    configs_of_state: dict[tuple, list[tuple[str, int]]] = {}
    for cfg in manifest["configs"]:
        key = state_key_of[cfg["config_id"]]
        configs_of_state.setdefault(key, []).append(
            (cfg["config_id"], int(cfg["params"]["H"])))

    cal_arr = np.array(calendar, dtype="<U10")
    ncal = len(calendar)
    b1, b2 = L.fold_boundaries()
    fold_ids = ("F1", "F2", "F3")
    pooled = {c["config_id"]: np.zeros(ncal, dtype=np.int64)
              for c in manifest["configs"]}
    stats = {c["config_id"]: {"positions_used": 0, "position_days": 0,
                              "death_censored_legs": 0, "pooled_max": 0,
                              "pooled_nonzero_days": 0}
             for c in manifest["configs"]}
    state_fired = {k: 0 for k in state_cfgs}
    state_bookable = {k: 0 for k in state_cfgs}
    state_fired_fold = {k: {f: 0 for f in fold_ids} for k in state_cfgs}
    state_bookable_fold = {k: {f: 0 for f in fold_ids} for k in state_cfgs}
    counters = {"names_parsed": 0, "names_served0": 0, "names_short": 0,
                "off_or_out_of_window_bars": 0,
                "off_or_out_of_window_held_sessions": 0}

    pulls = retrieval["pulls"]
    names = sorted(s for s, m in pulls.items()
                   if m.get("status") == 200
                   and (R.CACHE / f"{s}.json.gz").exists())
    log(f"heavy pass: {len(names)} names x {len(state_cfgs)} states x "
        f"{len(pooled)} configs, calendar {ncal} sessions, census space")

    for n_done, sym in enumerate(names, start=1):
        parsed = R.parse_name(R.CACHE / f"{sym}.json.gz")
        if parsed is None:
            counters["names_served0"] += 1
            continue
        dates, o, h, lo, c, v, _mal = parsed
        counters["names_parsed"] += 1
        if len(dates) < 3:
            counters["names_short"] += 1
            continue
        darr = np.array([d[:10] for d in dates], dtype="<U10")
        n = int(darr.shape[0])
        # census-space fold code: L.assign_fold semantics (F1 = d <= B1,
        # F2 = d <= B2, else F3) — ISO dates compare lexicographically
        # exactly like date objects; NO bar is ever dropped.
        fold_code = np.where(darr <= b1, 0,
                             np.where(darr <= b2, 1, 2)).astype(np.int8)
        # calendar mapping by DATE for pooling only (off-calendar or
        # out-of-window sessions carry -1 and are dropped and counted).
        ins = np.searchsorted(cal_arr, darr)
        vic = np.clip(ins, 0, ncal - 1)
        oncal = cal_arr[vic] == darr
        cal_pos = np.where(oncal, vic, np.int64(-1))
        counters["off_or_out_of_window_bars"] += int((~oncal).sum())
        med60 = L._rolling_median(c * v, L.DVOL_WINDOW)  # FULL served history
        for key, scfg in state_cfgs.items():
            fired, bookable, _drops = L.run_config_census(
                scfg, o, h, lo, c, v, med60=med60)
            fi_all = np.nonzero(fired)[0]
            fi = fi_all[fi_all >= warmup_of[key]]
            fb = fi[bookable[fi]]
            state_fired[key] += int(fi.size)
            state_bookable[key] += int(fb.size)
            for fc, fold in enumerate(fold_ids):
                m = fi[fold_code[fi] == fc]
                state_fired_fold[key][fold] += int(m.size)
                state_bookable_fold[key][fold] += int(
                    np.count_nonzero(bookable[m]))
            if fb.size == 0:
                continue
            for cid, hold in configs_of_state[key]:
                ends = fb + hold
                okk = ends <= n - 1
                stats[cid]["death_censored_legs"] += int((~okk).sum())
                s2 = fb[okk] + 1
                if s2.size == 0:
                    continue
                e2 = ends[okk]
                lens = e2 - s2 + 1
                tot = int(lens.sum())
                idx = np.repeat(s2, lens) + np.arange(tot, dtype=np.int64) \
                    - np.repeat(np.cumsum(lens) - lens, lens)
                pos = np.zeros(n, dtype=bool)
                pos[idx] = True
                pdays = np.nonzero(pos)[0]
                cp = cal_pos[pdays]
                dropped = int((cp < 0).sum())
                if dropped:
                    counters["off_or_out_of_window_held_sessions"] += dropped
                # bincount: overlapping names on one calendar session must
                # EACH count (plain fancy += collapses duplicates)
                pooled[cid] += np.bincount(cp[cp >= 0], minlength=ncal)
                stats[cid]["positions_used"] += int(s2.size)
                stats[cid]["position_days"] += int(pdays.size)
        if beat is not None and n_done % 500 == 0:
            beat({"names_done": n_done})
            log(f"heavy pass {n_done}/{len(names)} names")

    calendar_sha = canon_sha256(calendar)
    for cfg in manifest["configs"]:
        cid = cfg["config_id"]
        s = pooled[cid]
        stats[cid]["pooled_max"] = int(s.max())
        stats[cid]["pooled_nonzero_days"] = int(np.count_nonzero(s))
        stats[cid]["series_sha256"] = canon_sha256({
            "config_id": cid, "calendar_sha256": calendar_sha,
            "counts": [int(x) for x in s]})

    # cross-check: rebuilt per-config per-fold census cells == frozen P0
    # census rows EXACTLY (47 configs x {fired, bookable_fired} x 3 folds,
    # 282 cells) — the strongest legal form of the packet gate.
    rows_by_cid: dict[str, dict] = {}
    for r in p0_census["per_config_per_fold"]:
        rows_by_cid.setdefault(r["config_id"], {})[r["fold"]] = r
    xok, xdetail = True, {}
    n_cells = 0
    for cfg in manifest["configs"]:
        cid = cfg["config_id"]
        key = state_key_of[cid]
        cfg_ok = True
        for fold in fold_ids:
            n_cells += 1
            want_f = rows_by_cid[cid][fold]["fired"]
            want_b = rows_by_cid[cid][fold]["bookable_fired"]
            got_f = state_fired_fold[key][fold]
            got_b = state_bookable_fold[key][fold]
            cell_ok = got_f == want_f and got_b == want_b
            cfg_ok = cfg_ok and cell_ok
            if not cell_ok:
                xdetail[f"{cid}:{fold}"] = {
                    "want_fired": want_f, "got_fired": got_f,
                    "want_bookable": want_b, "got_bookable": got_b}
        xdetail[cid] = cfg_ok
        xok = xok and cfg_ok
    cks.add("state_totals_equal_p0_census_all_47", xok,
            {"n_ok": sum(1 for v in xdetail.values() if v is True),
             "n": len(manifest["configs"]),
             "n_census_cells": n_cells,
             "law": "rebuilt per-config per-fold fired and bookable_fired "
                    "census cells (census space: full served history, "
                    "fold-by-date, full-history med60, served-index warmup "
                    "gate) must equal the frozen P0 census EXACTLY (same "
                    "engines, same data); any drift is INPUT_MISMATCH",
             "mismatched_cells": xdetail if not xok else "none"})
    return {"pooled": pooled, "stats": stats, "counters": counters,
            "n_names": len(names), "state_fired": state_fired,
            "state_bookable": state_bookable,
            "state_fired_fold": state_fired_fold,
            "state_bookable_fold": state_bookable_fold}


# ------------------------------------------------------------------ P-20

def pearson(a: np.ndarray, b: np.ndarray) -> float:
    if a.shape != b.shape or a.shape[0] < 2:
        raise StopError("NOT_ADJUDICABLE",
                        f"series shape mismatch/short: {a.shape} vs {b.shape}")
    fa, fb = a.astype(np.float64), b.astype(np.float64)
    if not (bool(np.isfinite(fa).all()) and bool(np.isfinite(fb).all())):
        raise StopError("NOT_ADJUDICABLE", "non-finite pooled series value")
    if float(fa.std()) == 0.0 or float(fb.std()) == 0.0:
        raise StopError("NOT_ADJUDICABLE",
                        "zero-variance pooled series (rho unmeasurable)")
    r = float(np.corrcoef(fa, fb)[0, 1])
    if not np.isfinite(r):
        raise StopError("NOT_ADJUDICABLE", "non-finite rho")
    return r


def walk(manifest: dict, pooled: dict) -> dict:
    """Frozen §5(iii) round-robin with P-20 adjudicated DURING the walk."""
    st3 = manifest["selection_tier_3b"]
    family_order = st3["family_ranking_f3_fired_desc"]
    per_family = st3["per_family_config_order_f3_fired_desc"]
    cells: dict[str, int] = {f: 0 for f in family_order}
    selected: list[dict] = []
    visits: list[dict] = []
    seq = 0
    max_rounds = max(len(v) for v in per_family.values())
    for rnd in range(1, max_rounds + 1):
        if len(selected) >= MAX_CELLS:
            break
        for fam in family_order:
            if len(selected) >= MAX_CELLS:
                break
            if cells[fam] >= MAX_CELLS_PER_FAMILY:
                continue
            order = per_family[fam]
            if rnd > len(order):
                continue
            cand = order[rnd - 1]
            seq += 1
            comparisons = []
            max_abs = None
            for sel in selected:
                r = pearson(pooled[cand], pooled[sel["config_id"]])
                comparisons.append({
                    "vs_config_id": sel["config_id"],
                    "vs_rank": sel["rank"],
                    "pearson_r": r,
                    "abs_rho": abs(r),
                    "pair_verdict": "DISTINCT" if abs(r) <= P20_THRESHOLD
                    else "SELF_SUBSUMING"})
                max_abs = abs(r) if max_abs is None else max(max_abs, abs(r))
            accepted = all(c["pair_verdict"] == "DISTINCT"
                           for c in comparisons)
            if accepted:
                reason = (f"P-20 books-distinct PASS: max pooled |rho| "
                          f"{max_abs:.6f} <= {P20_THRESHOLD} vs all "
                          f"{len(comparisons)} higher-ranked selected"
                          if comparisons else
                          "first candidate of the walk: no higher-ranked "
                          "selected candidate exists to compare")
            else:
                reason = (f"P-20 SELF-SUBSUMED: pooled |rho| {max_abs:.6f} > "
                          f"{P20_THRESHOLD} vs at least one higher-ranked "
                          "selected candidate; next candidate in the frozen "
                          "order taken")
            visits.append({"seq": seq, "round": rnd, "family": fam,
                           "config_id": cand, "comparisons": comparisons,
                           "max_abs_rho": max_abs,
                           "verdict": "ACCEPTED" if accepted else "SELF_SUBSUMED",
                           "reason": reason})
            if accepted:
                cells[fam] += 1
                selected.append({
                    "rank": len(selected) + 1, "round": rnd, "family": fam,
                    "config_id": cand, "p20_max_abs_rho": max_abs,
                    "p20_vs": [c["vs_config_id"] for c in comparisons]})
    stopped = None
    if len(selected) < MAX_CELLS:
        stopped = (f"SELECTION_SHORTFALL: frozen order exhausted with fewer "
                   f"than {MAX_CELLS} books-distinct cells "
                   f"({len(selected)} selected)")
    return {"visits": visits, "selected": selected,
            "cells_per_family": cells, "stopped_note": stopped}


# ----------------------------------------------------------------- freeze

def conventions_block(calendar_sha: str) -> dict:
    return {
        "schema": "stocks_search_v1_p20_position_conventions@1",
        "packet_authority": (
            "dispatch packet ssearch-s: 'build its daily per-name position "
            "series from the manifest construction on the P0 cohort "
            "(deterministic; reuse the P0 census state engines read-only — "
            "the fsearch-s lane convention; positions in {0,1} long-only); "
            "measure pairwise |rho| of the pooled daily position series vs "
            "every already-SELECTED higher-ranked candidate'"),
        "plan_basis": (
            "plan §5 P-20 books-distinct at S, amended reading under §3b: "
            "D2 SKIPPED, no book-return series or shadow rho exists anywhere "
            "in this cycle; the S books-distinct adjudication consumes "
            "POSITION series only — a non-performance, outcome-blind "
            "construction statistic"),
        "c1_position_taking_decisions": (
            "fired AND bookable (F4 floors $1.00 adj_close / $2M trailing "
            "60-session median dvol are part of the frozen construction), "
            "decision index >= warmup_need in the name's SERVED-SESSION "
            "index space (P0 census space: engines run on the FULL served "
            "history, never trimmed; warmup law identical to "
            "p0_run.run_census)"),
        "c2_clock_legs": (
            "p0_lib.clock_legs(t, H) = (t, t+1, t+1+H); all legs must be "
            "served sessions of the name's full served history; a missing "
            "exit leg is a DEATH_CENSORED leg — excluded from the series, "
            "counted per configuration"),
        "c3_held_sessions": "t+1 .. t+H (H sessions; flat from the t+1+H open)",
        "c4_positions": ("{0,1} long-only per name-session; overlapping "
                         "fired decisions collapse to one position"),
        "c5_calendar": ("held-session DATES mapped onto the SPY-pinned "
                        "S0-window session calendar (F7 pin) for POOLING "
                        "only; off-calendar or out-of-window held sessions "
                        "dropped and COUNTED; the calendar never trims the "
                        "engine input (r3 census-space law, diag_s_r3)"),
        "c6_pooled_series": "daily COUNT of names holding a position",
        "c7_p20_statistic": (
            "Pearson correlation of two configurations' pooled daily "
            "position-count series over the full calendar; |rho| > 0.98 "
            "strictly SELF-SUBSUMES (plan §5 verbatim threshold); full "
            "float64"),
        "c8_no_fold_force_flat": (
            "fold-boundary force-flat is an EXECUTION contract (plan §8, "
            "phase E); the P-20 books-distinct diagnostic derives purely "
            "from the construction clock"),
        "calendar_sha256": calendar_sha,
        "outcome_blindness": (
            "NO candidate return, expectancy, PF, Sharpe, drawdown or any "
            "performance statistic is computed by this builder anywhere "
            "(enforced by the banned-key scan on the freeze body)"),
    }


def arm_identity_hash(cfg_excerpt: dict, data_manifests: dict,
                      folds_digest: str, s0: dict, calendar_sha: str,
                      series_sha: str, conventions_sha: str) -> str:
    return canon_sha256({
        "schema": "stocks_search_v1_arm_identity@1",
        "config_id": cfg_excerpt["config_id"],
        "manifest_config_excerpt": cfg_excerpt,
        "search_space_manifest_sha256": MANIFEST_SHA256,
        "search_space_manifest_self_sha256": MANIFEST_SELF_SHA256,
        "data_manifests_sha256": data_manifests,
        "fold_freeze_sha256": folds_digest,
        "s0_window": s0,
        "calendar_sha256": calendar_sha,
        "pooled_position_series_sha256": series_sha,
        "p20_conventions_sha256": conventions_sha,
    })


def build_freeze(manifest, p0_census, retrieval, cks_summary, pass_result,
                 walk_result, calendar, spy_sha) -> dict:
    st3 = manifest["selection_tier_3b"]
    calendar_sha = canon_sha256(calendar)
    conventions = conventions_block(calendar_sha)
    conventions_sha = canon_sha256(conventions)
    data_manifests = {rel: P0_SHA256[rel] for rel in sorted(P0_SHA256)}
    folds_digest = P0_SHA256["fold_freeze.json"]

    cfg_by_id = {c["config_id"]: c for c in manifest["configs"]}
    selected_full = []
    for sel in walk_result["selected"]:
        excerpt = cfg_by_id[sel["config_id"]]
        st = pass_result["stats"][sel["config_id"]]
        selected_full.append({
            **sel,
            "family": excerpt["family"],
            "manifest_config_excerpt": excerpt,
            "pooled_series_stats": st,
            "arm_identity_sha256": arm_identity_hash(
                excerpt, data_manifests, folds_digest, manifest["s0_window"],
                calendar_sha, st["series_sha256"], conventions_sha),
        })
    all_configs = []
    for cfg in manifest["configs"]:
        cid = cfg["config_id"]
        all_configs.append({
            "config_id": cid, "family": cfg["family"],
            "state_params": {k: v for k, v in cfg["params"].items()
                             if k != "H"},
            "H": cfg["params"]["H"],
            "pooled_series_stats": pass_result["stats"][cid]})
    freeze = {
        "schema": SCHEMA,
        "cycle_id": CYCLE_ID,
        "task_id": TASK_ID,
        "phase": PHASE,
        "plan": PLAN,
        "status": ("SELECTION_SHORTFALL" if walk_result["stopped_note"]
                   else "SELECTION_FROZEN"),
        "selection_law": {
            "plan_section": "§5 as amended by §3b (D2 SKIPPED, R0 NOT_RUN)",
            "amendment_3b_verbatim": st3["amendment_3b_verbatim"],
            "family_ranking_f3_fired_desc": st3["family_ranking_f3_fired_desc"],
            "family_ranking_values_f3_fired":
                st3["family_ranking_values_f3_fired"],
            "per_family_config_order_f3_fired_desc":
                st3["per_family_config_order_f3_fired_desc"],
            "p20_books_distinct_at_S_verbatim": st3["p20_books_distinct_at_S"],
            "outcome_blindness_verbatim": st3["outcome_blindness"],
            "round_robin": (
                "one configuration per family per round, at most "
                f"{MAX_CELLS_PER_FAMILY} scored cells per family, until "
                f"{MAX_CELLS} cells are filled (plan §5 iii)"),
            "r0_status": "NOT_RUN",
            "d2_status": "SKIPPED_BY_OWNER_AMENDMENT_3B",
        },
        "disclosure_section10_carried": (
            "accepted under owner-relaxed acceptance battery (R0 0.30 / DSR "
            "alpha 0.10 at N = grid) | PBO NOT_RUN fail-closed (<=3 cells, "
            "d0992d17 class) | R0 NOT_RUN (D2 skipped by owner amendment "
            "§3b)"),
        "base_sha": BASE_SHA,
        "verifications": cks_summary,
        "data_manifests_sha256": data_manifests,
        "search_space_manifest": {
            "path": "research/control/stocks_search_v1_run/d1/"
                    "search_space_manifest.json",
            "sha256": MANIFEST_SHA256,
            "self_sha256": MANIFEST_SELF_SHA256,
        },
        "folds": manifest["folds"],
        "fold_freeze_sha256": folds_digest,
        "s0_window": manifest["s0_window"],
        "calendar": {
            "source": "SPY cached pull (F7 benchmark pin), served dates in "
                      "[2015-01-02, 2026-09-16]",
            "spy_json_gz_sha256": spy_sha,
            "n_sessions": len(calendar),
            "first_session": calendar[0],
            "last_session": calendar[-1],
            "sha256": calendar_sha,
        },
        "p20_conventions": conventions,
        "heavy_pass": {
            "n_names": pass_result["n_names"],
            "counters": pass_result["counters"],
            "n_unique_states": len(pass_result["state_fired"]),
            "state_fired_totals": {
                f"{k[0]}|{json.dumps(k[1], sort_keys=True)}": v
                for k, v in sorted(pass_result["state_fired"].items(),
                                   key=lambda kv: str(kv[0]))},
            "state_fired_per_fold": {
                f"{k[0]}|{json.dumps(k[1], sort_keys=True)}": v
                for k, v in sorted(pass_result["state_fired_fold"].items(),
                                   key=lambda kv: str(kv[0]))},
            "state_bookable_per_fold": {
                f"{k[0]}|{json.dumps(k[1], sort_keys=True)}": v
                for k, v in sorted(pass_result["state_bookable_fold"].items(),
                                   key=lambda kv: str(kv[0]))},
            "law": ("state engines reused read-only: p0_run.parse_name + "
                    "p0_lib.run_config_census, sha256-pinned before use, "
                    "run in P0 CENSUS SPACE (full served history, "
                    "fold-by-date via L.assign_fold, full-history med60, "
                    "served-index warmup gate — r3 root-cause fix, "
                    "diag_s_r3); the calendar pools held-session DATES and "
                    "never trims the engine input; per-config per-fold "
                    "census cells cross-checked EXACT against the frozen "
                    "p0_census.json rows (47 configs x 3 folds x "
                    "{fired, bookable_fired})"),
        },
        "all_configs_position_series": all_configs,
        "walk": {
            "visits": walk_result["visits"],
            "n_visits": len(walk_result["visits"]),
            "cells_per_family": walk_result["cells_per_family"],
            "stopped_note": walk_result["stopped_note"],
        },
        "selected_candidates": selected_full,
        "n_selected": len(selected_full),
        "runtime": {"python": sys.version.split()[0],
                    "numpy": np.__version__},
        "self_sha256": "",
    }
    freeze["self_sha256"] = canon_sha256(freeze)
    return freeze


def banned_key_scan(obj, path="") -> list[str]:
    bad = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else str(k)
            kl = str(k).lower()
            for tok in BANNED_KEY_TOKENS:
                if tok in kl:
                    bad.append(f"{p} (token '{tok}')")
                    break
            bad.extend(banned_key_scan(v, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            bad.extend(banned_key_scan(v, f"{path}[{i}]"))
    return bad


def freeze_bytes(freeze: dict) -> bytes:
    probe = dict(freeze)
    probe["self_sha256"] = ""
    if canon_sha256(probe) != freeze["self_sha256"]:
        raise StopError("TECHABORT", "freeze self-sha inconsistency")
    return json.dumps(freeze, indent=1, sort_keys=True,
                      ensure_ascii=False).encode("utf-8") + b"\n"


def sanity_committed_freeze() -> None:
    """--selfcheck fast-path sanity: the committed freeze must parse and
    satisfy its own self-sha convention BEFORE the heavy recomputation."""
    if not FREEZE_PATH.exists():
        raise StopError("INPUT_MISMATCH",
                        f"committed freeze missing at {FREEZE_PATH}")
    committed = json.loads(FREEZE_PATH.read_text())
    claim = committed.get("self_sha256")
    probe = json.loads(FREEZE_PATH.read_text())
    probe["self_sha256"] = ""
    if claim != canon_sha256(probe):
        raise StopError("INPUT_MISMATCH",
                        "committed selection_freeze.json fails its own "
                        "self_sha256 empty-field convention")
    log(f"committed freeze self-sha convention OK ({claim[:16]}...)")


# ------------------------------------------------------------------- main

def run(mode: str) -> int:
    cks = Checks()
    log(f"mode={mode}")
    if mode == "--run":
        verify_head_and_branch()
    else:
        sanity_committed_freeze()

    manifest, p0_census, retrieval = verify_frozen_inputs(cks)

    sys.path.insert(0, str(WT))
    from research.governance import heavy_lock
    lock_cmd = [sys.executable, str(Path(__file__).resolve()), mode]
    try:
        hb = heavy_lock.acquire(
            cycle_id=CYCLE_ID, role=f"quant-implementer/{TASK_ID}",
            worktree=str(WT), command=lock_cmd,
            expected_artifacts=[str(FREEZE_PATH)] if mode == "--run" else None)
    except heavy_lock.LockBusyError as exc:
        log(f"NOT_RUN_RESOURCE_CONFLICT: {exc}")
        return 4
    with hb:
        L = load_module("p0_lib_s", P0 / "p0_lib.py")
        R = load_module("p0_run_s", P0 / "p0_run.py")
        cks.add("engines_loaded_after_hash_gate", True,
                {"law": "p0_lib.py and p0_run.py sha256-verified against the "
                        "pinned digests before any engine use",
                 "p0_lib_sha256": P0_SHA256["p0_lib.py"],
                 "p0_run_sha256": P0_SHA256["p0_run.py"]})
        calendar, spy_sha = build_calendar(R, cks)

        def beat(extra):
            try:
                hb.heartbeat(extra=extra)
            except Exception:  # noqa: BLE001 - heartbeat must never kill the pass
                pass

        pass_result = heavy_pass(L, R, manifest, p0_census, retrieval,
                                 calendar, cks, beat=beat)
        walk_result = walk(manifest, pass_result["pooled"])

    freeze = build_freeze(manifest, p0_census, retrieval, cks.summary(),
                          pass_result, walk_result, calendar, spy_sha)
    bad = banned_key_scan(freeze)
    if bad:
        raise StopError("BLOCKED_METHOD_CONTRACT",
                        f"banned performance-like keys in freeze: {bad}")
    # fold the scan verdict INTO the freeze deterministically, then rebuild
    cks.add("banned_key_scan", True,
            {"n_banned": 0, "tokens": list(BANNED_KEY_TOKENS),
             "law": "keys of the freeze body carry no performance-like field"})
    freeze = build_freeze(manifest, p0_census, retrieval, cks.summary(),
                          pass_result, walk_result, calendar, spy_sha)
    bad = banned_key_scan(freeze)
    if bad:
        raise StopError("BLOCKED_METHOD_CONTRACT",
                        f"banned performance-like keys in freeze: {bad}")

    blob = freeze_bytes(freeze)
    if mode == "--run":
        S_DIR.mkdir(parents=True, exist_ok=True)
        FREEZE_PATH.write_bytes(blob)
        log(f"froze {FREEZE_PATH} sha256={hashlib.sha256(blob).hexdigest()}")
    else:
        committed = FREEZE_PATH.read_bytes()
        same = committed == blob
        log(f"selfcheck byte-compare vs committed freeze: "
            f"{'IDENTICAL' if same else 'MISMATCH'}")
        if not same:
            raise StopError("INPUT_MISMATCH",
                            "recomputed freeze differs from the committed "
                            "selection_freeze.json")

    for v in walk_result["visits"]:
        mr = v["max_abs_rho"]
        log(f"  visit {v['seq']} r{v['round']} {v['config_id']}: "
            f"{v['verdict']} max|rho|={'n/a' if mr is None else f'{mr:.6f}'}")
    log(f"selected {[s['config_id'] for s in walk_result['selected']]}")
    s = cks.summary()
    log(f"checks: {s['n_pass']}/{s['n_checks']} PASS")
    return 0


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "--run"
    if mode not in ("--run", "--selfcheck"):
        print("usage: s_select.py [--run|--selfcheck]", file=sys.stderr)
        return 2
    try:
        return run(mode)
    except StopError as exc:
        log(f"STOP {exc.label}: {exc.detail}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
