#!/usr/bin/env python
"""make_sandbox_fixtures.py — SYNTHETIC-SANDBOX fixture generator for the
FUTURES-ES-PB1-V1 EXEC-BUILD lane (scored-execution proof through the
production path).

PROVENANCE BANNER — READ FIRST
  Every file this generator writes is a FABRICATED SYNTHETIC FIXTURE
  stamped SYNTHETIC-SANDBOX. It exists ONLY to drive the REAL
  gate6/runner/scored_runner.py + scored_executor.py machinery through all
  24 frozen identities inside an isolated sandbox. It is NOT cycle
  authority. The only GO artifact in the universe of this generator lives
  inside the sandbox it creates; NO real-cycle GO_RECORDED.json exists or
  is created anywhere.

What it fabricates (sandbox mirrors the real worktree layout so the pinned
machinery of record final/dryrun_builder_v3.py runs UNMODIFIED with only
its location constants redirected):

  SYNTHETIC data layer
    research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/ES_cache/
      es_1m_outright.parquet   synthetic 1m panel (fixed-point 1e-9, UTC ns)
      es_chain_T5.parquet      synthetic held chain (symbol/close/rth_open)
    research/control/FUTURES-ES-PB1-V1/final/selection_freeze_v3.json
    research/control/FUTURES-ES-PB1-V1/final/exclude_list_v3.json
    research/control/FUTURES-ES-PB1-V1/final/OPERATIVE_FREEZE_PIN.md
    research/control/FUTURES-ES-PB1-V1/freezegen/exclude_list.json (v1 labels)
    research/control/FUTURES-ES-PB1-V1/repair/exclude_list_v2.json
  REAL authority copied byte-identical (read-only reuse; pins keep real shas)
    SPEC_PB1_ES.md, dryrun_builder_v3.py, build_freeze_v3.py,
    make_builder_v3.py, A7_PRELAUNCH_V3.md(+digest), identity_table_24.json,
    PREGO_REPAIR_RECORDED.json, holiday evidence, DA45 packet+decisions,
    FAIL_DONOR_VIOLATION.md, DONOR_LAW_CARRYOVER.md, gate6/trial_ledger.py,
    gate6/runner/{scored_runner,scored_executor,test_execution_path,
    test_runner_refusals,make_sandbox_fixtures}.py (PIN-ENFORCE v2.3: the
    runner modules so addendum pins resolve under the sandbox)
  SANDBOX authority fixtures
    authority/GO_RECORDED.json          fake typed-owner GO (SANDBOX ONLY)
    registry/CYCLE_REGISTRY.rowcopy.json registry row copy (real branch/head)
    launch_contract.json                pin source for sandbox mode
                                       (embedded_laws byte-identical to the
                                        operative contract; pins -> sandbox)

Synthetic surface design (frozen laws kept: 24 identities, Variant-A costs,
4 folds F1-F4, warmup 252/fold head, eval totals 375/948/708/890 = 2,921;
donor law = flag-based SPEC §4 [ERRATUM A7-SPEC-M5] with the 139 v1-label
carryover set):
  chain = 260 pre-sessions + 4 fold windows (252 warmup + eval region) +
  3 inter-fold gaps of 8 sessions = 4,241 business days from 2016-01-04.
  Each session: 91 one-minute bars 08:30-10:00 CT. Prices are a
  deterministic pseudo-random walk (sha256-based, seed below); overnight
  gaps uniform in (-10, +10) points so ~20% of sessions clear the q80 tail
  condition on both tails.
  Donor-law exercise: 139 carryover sessions (v1 labels) + 6 gap sessions
  flagged only under v3 classes; FOMC days inside every fold's eval region
  feed the FOMCIN identities (28 total).

Determinism: no wall-clock anywhere in generated content; two runs of this
generator produce byte-identical JSON/MD and (given a stable pandas/pyarrow)
identical parquet. The sandbox contract's pins are computed from the files
as written, so the sandbox is always self-consistent.

Run:  /Users/hoangminhlong/.venv/bin/python  (ROOT .venv)
      make_sandbox_fixtures.py [--out DIR] [--force]
Default out: <this dir>/sandbox
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path, PurePosixPath

import pandas as pd

HERE = Path(__file__).resolve().parent
WORKTREE = str(HERE.parents[6])          # .../.worktrees/futures-es-reg/prep
RUNNER_DIR = HERE.parents[1]             # gate6/runner
SEED = "FUTURES-ES-PB1-V1/EXEC-BUILD/synthetic-sandbox-v1/2026-10-05"
STAMP = "SYNTHETIC-SANDBOX"
GENERATED_UTC = "2026-10-05"
CANONICAL_GO_PHRASE = "GO FUTURES-ES-PB1-V1 SCORED EXECUTION"

# real authority (read-only copies)
WT = WORKTREE
CY = "research/control/FUTURES-ES-PB1-V1"
DE = "research/control/FUTURES-DEEPRESEARCH-V2-20261003"
RG = "research/control/FUTURES-ES-PB1-REGPREP-20261004"
SP = "research/control/FUTURES-ES-V1-PACKET"

COPY_REAL = {
    f"{SP}/SPEC_PB1_ES.md": f"{SP}/SPEC_PB1_ES.md",
    f"{CY}/final/dryrun_builder_v3.py": f"{CY}/final/dryrun_builder_v3.py",
    f"{CY}/final/build_freeze_v3.py": f"{CY}/final/build_freeze_v3.py",
    f"{CY}/final/make_builder_v3.py": f"{CY}/final/make_builder_v3.py",
    f"{CY}/a7_v3/A7_PRELAUNCH_V3.md": f"{CY}/a7_v3/A7_PRELAUNCH_V3.md",
    f"{CY}/a7_v3/a7_prelaunch_v3_digest.json":
        f"{CY}/a7_v3/a7_prelaunch_v3_digest.json",
    f"{RG}/freeze/identity_table_24.json": f"{RG}/freeze/identity_table_24.json",
    f"{CY}/auth/PREGO_REPAIR_RECORDED.json":
        f"{CY}/auth/PREGO_REPAIR_RECORDED.json",
    f"{CY}/holiday/pdf_equity_evidence_2011_2015.json":
        f"{CY}/holiday/pdf_equity_evidence_2011_2015.json",
    f"{CY}/pins2/DA45_DECISION_PACKET.md": f"{CY}/pins2/DA45_DECISION_PACKET.md",
    f"{CY}/pins2/da45_decisions.json": f"{CY}/pins2/da45_decisions.json",
    f"{CY}/repair/FAIL_DONOR_VIOLATION.md":
        f"{CY}/repair/FAIL_DONOR_VIOLATION.md",
    f"{CY}/repair/DONOR_LAW_CARRYOVER.md":
        f"{CY}/repair/DONOR_LAW_CARRYOVER.md",
    f"{CY}/gate6/trial_ledger.py": f"{CY}/gate6/trial_ledger.py",
    # PIN-ENFORCE (v2.3 addendum): the runner modules are part of the
    # pinned live surface — copied byte-identical so the addendum pins
    # (scored_executor / scored_runner / the proof suites) RESOLVE under
    # the sandbox root. Sandbox runs execute the REAL worktree CLI; the
    # copies keep the real shas, so drift + self-integrity stay consistent.
    f"{CY}/gate6/runner/scored_runner.py": f"{CY}/gate6/runner/scored_runner.py",
    f"{CY}/gate6/runner/scored_executor.py": f"{CY}/gate6/runner/scored_executor.py",
    f"{CY}/gate6/runner/test_execution_path.py":
        f"{CY}/gate6/runner/test_execution_path.py",
    f"{CY}/gate6/runner/test_runner_refusals.py":
        f"{CY}/gate6/runner/test_runner_refusals.py",
    f"{CY}/gate6/runner/scratch/synthetic/make_sandbox_fixtures.py":
        f"{CY}/gate6/runner/scratch/synthetic/make_sandbox_fixtures.py",
}

# ---- synthetic surface topology -------------------------------------------
PRE_N = 260
WARMUP_N = 252
EVAL_N = {"F1": 375, "F2": 948, "F3": 708, "F4": 890}   # frozen fold counts
FOMC_IN_EVAL = {"F1": 3, "F2": 9, "F3": 7, "F4": 9}     # 28 FOMCIN sessions
GAP_N = 8
CARRYOVER_N = 139                                        # v1-label donor set
N_SESSIONS = PRE_N + sum(WARMUP_N + EVAL_N[f] + FOMC_IN_EVAL[f]
                         for f in ("F1", "F2", "F3", "F4")) + 3 * GAP_N
BARS_PER_DAY = 91                        # 08:30..10:00 CT inclusive
BASE_PRICE = 5000.0
STEP_AMP = 3.0
GAP_AMP = 10.0
DONOR_FAMILY_V3 = ["HOLIDAY_FACT_EARLYCLOSE", "HOLIDAY_PDF_EQUITY_2011_2015",
                   "HOLIDAY_2016_UNPROVEN_FAILCLOSED", "HOLIDAY_UNCERTAIN",
                   "COVERAGE_LT60"]
V1_CLASSES = ["HOLIDAY_FACT_EARLYCLOSE", "HOLIDAY_UNCERTAIN", "COVERAGE_LT60"]


def _u01(tag: str) -> float:
    """Deterministic uniform [0,1) from the seed + tag (sha256-based)."""
    d = hashlib.sha256(f"{SEED}|{tag}".encode()).digest()
    return int.from_bytes(d[:8], "big") / float(1 << 64)


def build_calendar():
    return [d.strftime("%Y-%m-%d")
            for d in pd.bdate_range("2016-01-04", periods=N_SESSIONS)]


def build_topology(dates: list[str]):
    """Assign exclusion classes + fold windows over the chain dates."""
    classes: dict[str, set] = {}
    v1_classes: dict[str, set] = {}
    folds = []

    def flag(d, c):
        classes.setdefault(d, set()).add(c)

    # pre-F1: carryover donor set (v1 labels 0..138), FOMC days 150..155
    for i in range(CARRYOVER_N):
        d = dates[i]
        c = V1_CLASSES[i % 3]
        v1_classes.setdefault(d, set()).add(c)
        flag(d, "HOLIDAY_UNCERTAIN")          # v3 view of the same session
    for i in range(150, 156):
        flag(dates[i], "FOMC_STATEMENT_DAY")

    idx = PRE_N
    for fn in ("F1", "F2", "F3", "F4"):
        n_eval, k_fomc = EVAL_N[fn], FOMC_IN_EVAL[fn]
        win_len = WARMUP_N + n_eval + k_fomc
        win = dates[idx: idx + win_len]
        warm_last = win[WARMUP_N - 1]
        region = win[WARMUP_N:]
        for d in win[:WARMUP_N]:
            flag(d, "WARMUP")
        fomc_pos = sorted({min(max(round((i + 1) * len(region) / (k_fomc + 1)), 1),
                               len(region) - 2) for i in range(k_fomc)})
        assert len(fomc_pos) == k_fomc, (fn, fomc_pos)
        for p in fomc_pos:
            flag(region[p], "FOMC_STATEMENT_DAY")
        ev = [d for d in region if not classes.get(d)]
        assert len(ev) == n_eval, (fn, len(ev), n_eval)
        folds.append({
            "fold": fn,
            "window": {"from": win[0], "to": win[-1]},
            "warmup_carve_out": {"first": win[0], "last": warm_last,
                                 "n": WARMUP_N,
                                 "law": "SPEC_PB1_ES §3/§7: warmup 252 "
                                        "sessions per fold head "
                                        "(SYNTHETIC-SANDBOX fixture)"},
            "eval_sessions": {"n": n_eval, "first": ev[0], "last": ev[-1]},
            "n_sessions_in_window": win_len,
            "n_base_excluded": win_len - WARMUP_N - n_eval,
            "n_surviving": n_eval,
        })
        idx += win_len
        if fn != "F4":
            gap = dates[idx: idx + GAP_N]
            if fn == "F1":
                flag(gap[0], "HOLIDAY_PDF_EQUITY_2011_2015")
                flag(gap[1], "HOLIDAY_PDF_EQUITY_2011_2015")
                flag(gap[2], "COVERAGE_LT60")
                flag(gap[3], "COVERAGE_LT60")
            elif fn == "F2":
                flag(gap[0], "HOLIDAY_PDF_EQUITY_2011_2015")
                flag(gap[1], "HOLIDAY_PDF_EQUITY_2011_2015")
            else:
                flag(gap[0], "HOLIDAY_2016_UNPROVEN_FAILCLOSED")
                flag(gap[1], "HOLIDAY_2016_UNPROVEN_FAILCLOSED")
            idx += GAP_N
    assert idx == N_SESSIONS
    return classes, v1_classes, folds


def build_panel_and_chain(dates: list[str], classes: dict, out: Path):
    """Synthetic 1m panel (fixed-point 1e-9, ts_event = bar START UTC ns)
    + held chain (symbol/close/rth_open per session)."""
    sym_rows, ts_rows, o_rows, h_rows, l_rows, c_rows = [], [], [], [], [], []
    chain_sym, chain_close, chain_rth_open = [], [], []
    prev_close = BASE_PRICE
    minute = pd.Timedelta(minutes=1)
    for di, d in enumerate(dates):
        ts0830 = pd.Timestamp(f"{d} 08:30", tz="America/Chicago")
        gap = (_u01(f"gap|{d}") * 2.0 - 1.0) * GAP_AMP
        o830 = prev_close + gap
        cur = o830
        month = int(d[5:7])
        symbol = f"ES{'HMQZ'[(month - 1) // 3]}{d[2:4]}"
        base_ns = ts0830.value
        for j in range(BARS_PER_DAY):
            step = (_u01(f"bar|{d}|{j}") * 2.0 - 1.0) * STEP_AMP
            o = cur
            c = o + step
            h = max(o, c) + 0.5
            lo = min(o, c) - 0.5
            cur = c
            sym_rows.append(symbol)
            ts_rows.append(base_ns + j * 60_000_000_000)
            o_rows.append(int(round(o * 1e9)))
            h_rows.append(int(round(h * 1e9)))
            l_rows.append(int(round(lo * 1e9)))
            c_rows.append(int(round(c * 1e9)))
        chain_sym.append(symbol)
        chain_close.append(cur)
        chain_rth_open.append(o830)
        prev_close = cur
        if di == 0:  # dash-law strays (E5): raw_symbol containing '-' filtered
            stray_ns = base_ns
            for j in range(50):
                sym_rows.append("ES-synthetic-stray")
                ts_rows.append(stray_ns + j * 60_000_000_000)
                o_rows.append(int(round(BASE_PRICE * 1e9)))
                h_rows.append(int(round((BASE_PRICE + 1.0) * 1e9)))
                l_rows.append(int(round((BASE_PRICE - 1.0) * 1e9)))
                c_rows.append(int(round(BASE_PRICE * 1e9)))

    panel = pd.DataFrame({
        "raw_symbol": sym_rows,
        "ts_event": ts_rows,
        "open": o_rows,
        "high": h_rows,
        "low": l_rows,
        "close": c_rows,
    })
    for c in ("ts_event", "open", "high", "low", "close"):
        panel[c] = panel[c].astype("int64")
    panel.to_parquet(out / f"{DE}/analysis/ES_cache/es_1m_outright.parquet",
                     index=False)
    # positional lists (NOT Series) — a Series here would align its
    # RangeIndex against the DatetimeIndex and yield all-NaN columns
    chain = pd.DataFrame({
        "symbol": chain_sym,
        "close": chain_close,
        "rth_open": chain_rth_open,
    }, index=pd.DatetimeIndex(pd.to_datetime(dates), name="date"))
    chain.to_parquet(out / f"{DE}/analysis/ES_cache/es_chain_T5.parquet")


def write_excludes(dates: list[str], classes: dict, v1_classes: dict, out: Path):
    ev = []
    for d in sorted(classes):
        for c in sorted(classes[d]):
            ev.append({"session_date": d, "reason_class": c,
                       "in_panel": True,
                       "evidence": f"{STAMP} fixture (generator seed "
                                   f"{SEED})"})
    excl_v3 = {"schema": "exclude_list@3", "cycle_id": "FUTURES-ES-PB1-V1",
               "provenance": f"{STAMP} — FABRICATED fixture; NOT the "
                             f"operative exclusion set",
               "exclusions": ev}
    p3 = out / f"{CY}/final/exclude_list_v3.json"
    p3.write_text(json.dumps(excl_v3, indent=1, sort_keys=True,
                             ensure_ascii=False), encoding="utf-8")

    ev1 = [{"session_date": d, "reason_class": sorted(v1_classes[d])[0],
            "in_panel": True}
           for d in sorted(v1_classes)]
    excl_v1 = {"schema": "exclude_list@1", "provenance":
               f"{STAMP} — FABRICATED v1-label fixture (carryover donor "
               f"baseline = {CARRYOVER_N})",
               "exclusions": ev1}
    (out / f"{CY}/freezegen/exclude_list.json").write_text(
        json.dumps(excl_v1, indent=1, sort_keys=True, ensure_ascii=False),
        encoding="utf-8")

    ev2 = []
    for it in ev:
        c = it["reason_class"]
        ev2.append({"session_date": it["session_date"],
                    "reason_class": ("HOLIDAY_UNCERTAIN"
                                     if c == "HOLIDAY_2016_UNPROVEN_FAILCLOSED"
                                     else c),
                    "in_panel": True})
    excl_v2 = {"schema": "exclude_list@2", "provenance":
               f"{STAMP} — FABRICATED v2 fixture (delta-evidence baseline)",
               "exclusions": ev2}
    (out / f"{CY}/repair/exclude_list_v2.json").write_text(
        json.dumps(excl_v2, indent=1, sort_keys=True, ensure_ascii=False),
        encoding="utf-8")
    return sha256_file(p3)


def sha256_file(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_freeze(out: Path, excl_sha: str, folds: list[dict]) -> str:
    idtab = json.loads((Path(WT) / f"{RG}/freeze/identity_table_24.json")
                       .read_text(encoding="utf-8"))
    total = sum(f["eval_sessions"]["n"] for f in folds)
    assert total == 2921, total
    freeze = {
        "schema": "selection_freeze@3",
        "cycle_id": "FUTURES-ES-PB1-V1",
        "provenance": f"{STAMP} — FABRICATED freeze fixture "
                      f"(generator: scratch/synthetic/"
                      f"make_sandbox_fixtures.py; seed {SEED}); the load-"
                      f"bearing LAWS (24 identities, Variant-A costs, folds "
                      f"F1-F4, warmup 252, flag-based donor law) are "
                      f"byte-identical in MEANING to the operative freeze; "
                      f"the data surface is synthetic; NOT cycle authority",
        "generated_utc": GENERATED_UTC,
        "cost_contract": {"embedded": {
            "chosen_variant": "A — NFA basis",
            "decision_quote_verbatim": "tôi chọn 2.25$",
            "effective_cost_table_es": {
                "commission": 0.85, "exchange": 1.38, "regulatory": 0.02,
                "fees_per_side": 2.25, "spread_half_turn": 6.25,
                "slippage_tiers_per_side": {"S1": 12.5, "S2": 25.0, "S3": 37.5},
                "all_in_per_side": {"S1": 21.0, "S2": 33.5, "S3": 46.0},
                "round_trip": {"S1": 42.0, "S2": 67.0, "S3": 92.0},
                "window_exception_2014_10_01_to_2017_12_31": {
                    "regulatory": 0.01,
                    "all_in_per_side": {"S1": 20.99, "S2": 33.49,
                                        "S3": 45.99}},
            },
            "forbidden_values_law": "1.386 and 21.006/33.506/46.006 remain "
                                    "retired/never-consumable",
            "labels_binding": "MODELED COST; VERIFIED_VS_ACCOUNT=NOT_RUN",
        }},
        "identity_table": {
            "source_path": "research/control/FUTURES-ES-PB1-REGPREP-"
                           "20261004/freeze/identity_table_24.json",
            "source_sha256": sha256_file(Path(WT) /
                                         f"{RG}/freeze/identity_table_24.json"),
            "embedded": {"schema": "freeze_identity_table@1",
                         "identities": [
                             {"id": it["id"], "arm": it["arm"]}
                             for it in idtab["identities"]]},
        },
        "exclude_list": {"schema": "exclude_list@3", "sha256": excl_sha,
                         "path": f"{CY}/final/exclude_list_v3.json",
                         "provenance": f"{STAMP} fixture"},
        "fold_structure": {
            "law": "4 sequential folds post-EXCLUDE; warmup 252 sessions/"
                   "fold head; folds multiply evaluation views, never "
                   "identities (SYNTHETIC-SANDBOX fixture surface; frozen "
                   "counts 375/948/708/890 = 2,921)",
            "folds": folds,
            "total_eval_sessions": total,
            "warmup_sessions_per_fold": WARMUP_N,
        },
        "donor_law": {
            "law_spec_quote_verbatim": "[ERRATUM A7-SPEC-M5] SL = 1.0 × "
                                       "median của 20 range RTH session liền "
                                       "trước (strict past; close marks "
                                       "era-correct; loại session "
                                       "short/flagged)",
            "provenance": f"{STAMP} — flag-based donor law exercised on the "
                          f"synthetic flag surface",
            "supersedes": {
                "path": f"{CY}/repair/DONOR_LAW_CARRYOVER.md",
                "sha256": sha256_file(
                    Path(WT) / f"{CY}/repair/DONOR_LAW_CARRYOVER.md"),
            },
            "correction_record": {
                "finding_id": "D-V2-2",
                "path": f"{CY}/repair/FAIL_DONOR_VIOLATION.md",
                "sha256": sha256_file(
                    Path(WT) / f"{CY}/repair/FAIL_DONOR_VIOLATION.md"),
            },
        },
    }
    p = out / f"{CY}/final/selection_freeze_v3.json"
    p.write_text(json.dumps(freeze, indent=1, sort_keys=True,
                            ensure_ascii=False), encoding="utf-8")
    return sha256_file(p)


def build_pin_md(out: Path, freeze_sha: str):
    text = f"""# OPERATIVE FREEZE PIN — {STAMP} FIXTURE

This file is a FABRICATED sandbox fixture mirroring
`final/OPERATIVE_FREEZE_PIN.md`. The sandbox-operative freeze bytes are:

    selection_freeze_v3.json  sha256  {freeze_sha}

Banner: {STAMP} — NOT the cycle's operative freeze; NOT cycle authority.
The REAL operative freeze remains
research/control/FUTURES-ES-PB1-V1/final/selection_freeze_v3.json
(0b0d269abbcafd065fa84ba3ba1047ac27df7fcc86675ccfef6f47666d951ff9).
"""
    (out / f"{CY}/final/OPERATIVE_FREEZE_PIN.md").write_text(
        text, encoding="utf-8")


def build_go(out: Path, a7_digest_sha: str):
    art = {
        "schema": "futures_es_pb1_v1/go_recorded@1",
        "cycle_id": "FUTURES-ES-PB1-V1",
        "sandbox_provenance": f"{STAMP} TEST FIXTURE — fabricated by "
                              f"scratch/synthetic/make_sandbox_fixtures.py; "
                              f"NOT a real owner GO; exists ONLY inside this "
                              f"sandbox; the real gate "
                              f"auth/GO_RECORDED.json remains ABSENT",
        "recorded_utc": "1970-01-01T00:00:00Z",
        "key_1_a7_prelaunch": {
            "sha256": a7_digest_sha,
            "note": "sandbox binding to the byte-identical copy of the "
                    "operative A7-v3 digest"},
        "key_2_owner_go": {
            "verbatim": CANONICAL_GO_PHRASE,
            "typed_by_owner": True,
            "typed_by": "OWNER",
            "received_utc": "1970-01-01",
            "fixture_note": f"{STAMP} — the phrase is the registered "
                            f"canonical string exercised by the test "
                            f"fixture"},
        "authorizes": {"scored_execution":
                       "gate6/runner/scored_runner.py + scored_executor.py "
                       f"({STAMP} sandbox only)"},
        "forbids": ["push, merge to main, history rewrite", "S1 opening"],
    }
    (out / f"{CY}/authority/GO_RECORDED.json").write_text(
        json.dumps(art, indent=1, sort_keys=True, ensure_ascii=False),
        encoding="utf-8")


def build_registry_copy(out: Path):
    import subprocess
    branch = subprocess.run(
        ["git", "-C", WT, "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True, timeout=20).stdout.strip()
    head = subprocess.run(["git", "-C", WT, "rev-parse", "HEAD"],
                          capture_output=True, text=True,
                          timeout=20).stdout.strip()
    row = {
        "cycle_id": "FUTURES-ES-PB1-V1", "asset": "futures",
        "lifecycle": "ACTIVE_LIGHT", "phase": "REGISTERED",
        "integration_worktree": WT, "branch": branch, "head": head,
        "budget": {"used": 0, "max": 24}, "s0": "OPEN",
        "s1": "SEALED_UNTOUCHED", "go_phrase": CANONICAL_GO_PHRASE,
        "go_phrase_state": "REGISTERED_NOT_CONSUMED", "workers": 0,
        "active_heavy": False, "heartbeat_utc": "1970-01-01T00:00:00Z",
        "hard_stop_reason": None, "pause_packet": None,
        "next_authorized_action": "",
        "updated_at_utc": "1970-01-01T00:00:00Z", "adapter_warnings": [],
        "provenance": f"{STAMP} row COPY (real branch/head values; the ROOT "
                      f"registry is never written by this lane)"
    }
    payload = {"provenance": f"{STAMP} registry row copy — the ROOT "
                             f"plans/CYCLE_REGISTRY.json is READ-ONLY and is "
                             f"never written by this lane",
               "cycles": [row]}
    (out / "registry/CYCLE_REGISTRY.rowcopy.json").write_text(
        json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")


def build_contract(out: Path, freeze_sha: str, panel_sha: str, chain_sha: str,
                   excl_sha: str):
    real = json.loads((RUNNER_DIR / "LAUNCH_CONTRACT_V2.json").read_text(
        encoding="utf-8"))
    con = copy.deepcopy(real)
    con["sandbox_provenance"] = (
        f"{STAMP} fixture contract for --sandbox-root runs. embedded_laws + "
        f"go_authority are byte-identical to the operative "
        f"LAUNCH_CONTRACT_V2.json; pins resolve under the sandbox root "
        f"(real authority copied byte-identical keeps its real sha; "
        f"synthetic fixtures carry their generated shas). NOT the operative "
        f"contract.")
    con["worktree"] = str(out)
    sha_by_path = {}
    for rel in COPY_REAL.values():
        sha_by_path[rel] = sha256_file(out / rel)
    sha_by_path[f"{CY}/final/selection_freeze_v3.json"] = freeze_sha
    sha_by_path[f"{CY}/final/exclude_list_v3.json"] = excl_sha
    sha_by_path[f"{DE}/analysis/ES_cache/es_1m_outright.parquet"] = panel_sha
    sha_by_path[f"{DE}/analysis/ES_cache/es_chain_T5.parquet"] = chain_sha
    sha_by_path[f"{CY}/final/OPERATIVE_FREEZE_PIN.md"] = sha256_file(
        out / f"{CY}/final/OPERATIVE_FREEZE_PIN.md")
    for pin in con["pins"]:
        if pin["name"] == "a7_adjudicated_freeze_bytes_HISTORY":
            pin["sandbox_note"] = (f"{STAMP} history record (never a live "
                                   f"file check)")
            continue
        want = sha_by_path.get(pin["path"])
        assert want is not None, pin["path"]
        pin["sha256"] = want
    (out / "launch_contract.json").write_text(
        json.dumps(con, indent=1, sort_keys=True, ensure_ascii=False),
        encoding="utf-8")


def build_provenance(out: Path, extra: dict):
    lines = [
        f"# {STAMP} — sandbox fixtures", "",
        "EVERYTHING under this directory is a FABRICATED SYNTHETIC FIXTURE.",
        "Purpose: drive the REAL gate6/runner scored execution path",
        "(scored_runner.py + scored_executor.py + final/dryrun_builder_v3.py",
        "machinery) through all 24 frozen identities in isolation.",
        "",
        f"Generator: gate6/runner/scratch/synthetic/make_sandbox_fixtures.py",
        f"Seed: {SEED}",
        f"Generated (fixed label, no wall clock): {GENERATED_UTC}",
        "",
        "The GO artifact in authority/GO_RECORDED.json is a fixture that",
        "exists ONLY here. NO real-cycle GO_RECORDED.json exists anywhere;",
        "'GO FUTURES-ES-PB1-V1 SCORED EXECUTION' remains owner-only,",
        "REGISTERED_NOT_CONSUMED at the real gate.",
        "",
        "Real authority was copied READ-ONLY byte-identical (SPEC, builder",
        "v3, A7-v3, DA45, holiday evidence, trial_ledger, identity table,",
        "PREGO/FAIL_DONOR/DONOR_LAW_CARRYOVER records). Synthetic: panel,",
        "chain, freeze v3, exclude lists v1/v2/v3, pin md, GO fixture,",
        "registry row copy, launch contract.",
        "",
        "Fixture shas:",
    ]
    for rel, sha in sorted(extra.items()):
        lines.append(f"  {sha}  {rel}")
    (out / "PROVENANCE.md").write_text("\n".join(lines) + "\n",
                                       encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=str(HERE / "sandbox"))
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args(argv)
    out = Path(args.out)
    marker = out / "PROVENANCE.md"
    if marker.is_file() and not args.force:
        print(f"fixtures already present at {out} (use --force to rebuild)")
        return 0
    if out.exists():
        shutil.rmtree(out)
    dirs = {"registry", f"{DE}/analysis/ES_cache", f"{CY}/final",
            f"{CY}/freezegen", f"{CY}/repair", f"{CY}/authority",
            f"{CY}/a7_v3", f"{CY}/auth", f"{CY}/holiday", f"{CY}/pins2",
            f"{CY}/gate6", f"{RG}/freeze", SP}
    for rel in list(COPY_REAL.values()) + list(COPY_REAL.keys()):
        dirs.add(str(PurePosixPath(rel).parent))
    for d in dirs:
        (out / d).mkdir(parents=True, exist_ok=True)
    for src_rel, dst_rel in COPY_REAL.items():
        shutil.copyfile(Path(WT) / src_rel, out / dst_rel)

    dates = build_calendar()
    classes, v1_classes, folds = build_topology(dates)
    build_panel_and_chain(dates, classes, out)
    excl_sha = write_excludes(dates, classes, v1_classes, out)
    panel_sha = sha256_file(
        out / f"{DE}/analysis/ES_cache/es_1m_outright.parquet")
    chain_sha = sha256_file(
        out / f"{DE}/analysis/ES_cache/es_chain_T5.parquet")
    freeze_sha = build_freeze(out, excl_sha, folds)
    build_pin_md(out, freeze_sha)
    a7_digest_sha = sha256_file(out / f"{CY}/a7_v3/a7_prelaunch_v3_digest.json")
    build_go(out, a7_digest_sha)
    build_registry_copy(out)
    build_contract(out, freeze_sha, panel_sha, chain_sha, excl_sha)
    manifest = {
        "sandbox_stamp": STAMP, "seed": SEED,
        f"sha256:{CY}/final/selection_freeze_v3.json": freeze_sha,
        f"sha256:{CY}/final/exclude_list_v3.json": excl_sha,
        f"sha256:{DE}/analysis/ES_cache/es_1m_outright.parquet": panel_sha,
        f"sha256:{DE}/analysis/ES_cache/es_chain_T5.parquet": chain_sha,
        "n_chain_sessions": N_SESSIONS,
        "eval_totals": EVAL_N,
    }
    build_provenance(out, manifest)
    (out / "fixtures_manifest.json").write_text(
        json.dumps(dict(manifest, provenance=f"{STAMP}"), indent=1,
                   sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8")
    print(json.dumps({"out": str(out), "sessions": N_SESSIONS,
                      "freeze_sha": freeze_sha[:16],
                      "panel_sha": panel_sha[:16],
                      "chain_sha": chain_sha[:16]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
