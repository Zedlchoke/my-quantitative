"""DIAG scoring library — ERP1-TRACKA-COHORT-1 (diag lane, 2026-09-26).

OWNER instruction: score the CURRENT shadow strategy law ("daemon law")
on EURUSD and GBPUSD. DIAGNOSTIC_OUTCOME_EXPOSED lane: these windows are
outcome-exposed for the RANGEEXP family (umbrella 5.8/6 ancestry law;
cohort plan 3) — NOTHING here is promotable evidence regardless of
result. No parameter is tuned, no variant tried, no rescue: one pass,
both pairs, as specified.

Arms (5 books per pair, diagnostic set):
  R-DAEMON     T.f_rangeexp_daemon  (the M-3 emulation machinery from the
               falsifier battery, reused unmodified — per-bar partial-
               range percentile mode, mid-day flips allowed, pos persists
               within the day; hand-built-panel fixture in diag/tests
               proves the semantics end-to-end through the executor)
  R-ORIG       T.f_rangeexp_orig    (byte-faithful leaky ancestor law;
               placement reference, never selectable)
  R-ANCHOR     T.f_rangeexp_anchor_shift (PIT-clean reference, pct[d-1])
  SHORT_ALWAYS day-session short book (beta-matched for both quote-USD
               pairs; 00:00->20:00 force-flat)
  LONG_ALWAYS  day-session long book

All arms run on the ANCESTRY-convention H1 SIGNAL plane (close-column
high) per the cohort's plane pin; costs charge the fill bar's own
measured spread x k in {1.0, 1.5, 2.0} through the committed
scripts/engine.py run_strategy (signal on closed bar -> fill NEXT H1
open at the opposite quote; no fills on/after the 19:00 bar; force-flat
at the day-close bar close, 20:00 UTC; weekend flat).

Windows: full diagnostic panel 2021-01-01..2026-06-30 (2026-07+ ignored
at the plane loader). Folds F1..F6 (falsifier FOLD_TABLE, 2021-2025);
2026-01..06 reported separately, explicitly labeled
CONSUMED_SURFACE_DESCRIPTIVE (consumed by ancestry looks on these pairs).

Pinned choices (no alternative tried): warmup_end_idx=0 for every arm
(the diagnostic panel starts 2021-01-01; the law's own history machinery
determines when modes exist; no extra warmup parameter is introduced).
G1-G8 arithmetic is run on the FULL diagnostic panel (informative only
— no promotion semantics exist in a diagnostic); fold assignment and
concentration shares cover F1..F6 (2021-2025).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

DIAG = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DIAG / "scripts"))
sys.path.insert(0, str(DIAG.parent / "scripts"))   # committed cycle scripts

import engine as E  # noqa: E402
import tracka_lib as T  # noqa: E402
from falsifier_run import FOLD_TABLE, ts_of  # noqa: E402
from pair_config_diag import load_pair_config  # noqa: E402
import scored_lib as S  # noqa: E402

DERIVED = DIAG / "data_local" / "derived"
PAIRS = ("EURUSD", "GBPUSD")
K_BOOKS = (1.0, 1.5, 2.0)
PANEL_START, PANEL_END = "2021-01-01", "2026-06-30"
W26_START, W26_END = "2026-01-01", "2026-06-30"
BETA_MATCHED = {"EURUSD": "SHORT_ALWAYS", "GBPUSD": "SHORT_ALWAYS"}
LABELS = ["DIAGNOSTIC_OUTCOME_EXPOSED", "SINGLE_SOURCE_PANEL",
          "FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK", "PAPER_TIER"]


def sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_plane(pair: str) -> T.SignalPlane:
    cfg = load_pair_config(pair)
    df = pd.read_parquet(DERIVED / f"bars1h_ANC_{pair}.parquet")
    df = df[df["ts"] <= pd.Timestamp(f"{PANEL_END}T23:59:59Z")]
    return T.SignalPlane(df, pip_mult=1.0 / cfg.pip)


def day_session(p: T.SignalPlane) -> np.ndarray:
    return ((~p.skip) & (p.hour >= 7) & (p.hour <= 18)).astype(np.int8)


def build_targets(p: T.SignalPlane) -> tuple[dict, dict, dict]:
    """The five diagnostic target arrays on one ANC plane + the daemon
    extras (first mode per day, mid-day change counters)."""
    sess = day_session(p)
    tgt_daemon, daemon_first_mode, daemon_changes = T.f_rangeexp_daemon(p)
    tgts = {
        "R-DAEMON": tgt_daemon,
        "R-ORIG": T.f_rangeexp_orig(p),
        "R-ANCHOR": T.f_rangeexp_anchor_shift(p),
        "SHORT_ALWAYS": (-sess).astype(np.int8),
        "LONG_ALWAYS": sess,
    }
    return tgts, daemon_first_mode, daemon_changes


def subset_metrics(trades: list, lo_ts: int, hi_ts: int) -> dict:
    """net/PF/RT for trades ENTERED in [lo_ts, hi_ts] (descriptive)."""
    pnls = np.array([t["pips"] for t in trades
                     if lo_ts <= t["entry_ts"] <= hi_ts], dtype=float)
    if len(pnls) == 0:
        return {"net_pips": 0.0, "trades": 0, "pf": None}
    gw = float(pnls[pnls > 0].sum())
    gl = float(-pnls[pnls < 0].sum())
    return {"net_pips": round(float(pnls.sum()), 2),
            "trades": int(len(pnls)),
            "pf": round(gw / gl, 4) if gl > 0 else None}


def run_arm(p: T.SignalPlane, tgt: np.ndarray) -> dict:
    """The three k-books of one arm through the committed engine."""
    books = {}
    for k in K_BOOKS:
        trades, equity = E.run_strategy(p, tgt, k, warmup_end_idx=0)
        books[str(k)] = {
            "metrics": E.metrics(trades, equity),
            "decompose": S.decompose(p, trades, k),
            "gate_metrics": S.gate_metrics(p, trades, k),
            "daily_sr_context": daily_sr_context(p, trades),
            "w2026H1": {
                **subset_metrics(trades, ts_of(W26_START),
                                 ts_of(W26_END, end=True)),
                "label": "CONSUMED_SURFACE_DESCRIPTIVE",
            },
        }
    return books


def daemon_mode_stats(p: T.SignalPlane, daemon_first_mode: dict,
                      daemon_changes: dict) -> dict:
    """Mode-flip statistics over the full diagnostic panel traded days:
    mid-day mode changes; early-silenced days (daemon first-mode flat —
    absolute, and relative to the R-ORIG day label)."""
    days, ranges = T.day_ranges(p)
    pct = T.pct_full_panel(days, ranges)

    def label_of(m):
        return "flat" if m is None or m <= 0 else \
            ("follow" if m > 0.7 else "fade")

    orig_labels = {d: label_of(pct.get(d)) for d in days}
    daemon_labels = {d: daemon_first_mode.get(d, "flat") for d in days}
    changes_by_day = {d: int(daemon_changes.get(d, 0)) for d in days}
    midday_flip_days = [d for d in days if changes_by_day[d] > 0]
    early_silenced_rel = [d for d in days
                          if orig_labels[d] != "flat"
                          and daemon_labels[d] == "flat"]
    daemon_only_active = [d for d in days
                          if orig_labels[d] == "flat"
                          and daemon_labels[d] != "flat"]
    hist = {}
    for c in changes_by_day.values():
        hist[c] = hist.get(c, 0) + 1
    return {
        "n_traded_days": len(days),
        "n_days_mode_changed_midday": len(midday_flip_days),
        "share_days_mode_changed_midday": round(
            len(midday_flip_days) / max(len(days), 1), 6),
        "total_mode_change_events": int(sum(changes_by_day.values())),
        "mode_changes_per_day_histogram": {str(k): v
                                           for k, v in sorted(hist.items())},
        "n_days_first_mode_flat": sum(1 for d in days
                                      if daemon_labels[d] == "flat"),
        "n_days_orig_active_daemon_first_mode_flat": len(early_silenced_rel),
        "n_days_orig_flat_daemon_active": len(daemon_only_active),
        "first_mode_counts": {k: sum(1 for d in days
                                     if daemon_labels[d] == k)
                              for k in ("flat", "fade", "follow")},
        "orig_label_counts": {k: sum(1 for d in days
                                     if orig_labels[d] == k)
                              for k in ("flat", "fade", "follow")},
    }


def daemon_bar_disagreement(p: T.SignalPlane, tgts: dict) -> dict:
    idx = np.arange(len(p.ts))
    ins = (~p.skip) & (p.hour >= 7) & (p.hour <= 18)
    d = tgts["R-DAEMON"]
    return {
        "denominator": "in-session (07-18 UTC) bars, full diagnostic panel",
        "in_session_bars": int(ins.sum()),
        "daemon_vs_orig_differing_bars": int((d[ins] != tgts["R-ORIG"][ins]).sum()),
        "daemon_vs_anchor_differing_bars": int(
            (d[ins] != tgts["R-ANCHOR"][ins]).sum()),
    }


def beta_check(arm_books: dict, pair: str, k: str = "1.0") -> dict:
    beta = BETA_MATCHED[pair]
    net_d = arm_books["R-DAEMON"][k]["decompose"]["net_pips"]
    net_b = arm_books[beta][k]["decompose"]["net_pips"]
    return {
        "beta_matched_book": beta, "k": k,
        "net_R-DAEMON_pips": net_d,
        f"net_{beta}_pips": net_b,
        "daemon_minus_beta_pips": round(net_d - net_b, 2),
    }


def g_gates_informative(daemon_books: dict) -> dict:
    """G1-G8 arithmetic on the R-DAEMON books (informative only — no
    promotion semantics exist in a diagnostic). Thresholds are the
    cohort's frozen scored-phase thresholds; the panel here is the full
    diagnostic panel (2021-01..2026-06), not the cohort dev window."""
    cell = {"books": {k: {"decompose": daemon_books[k]["decompose"],
                          "gates": {
                              "pf": daemon_books[k]["gate_metrics"]["pf"],
                              "per_fold_net_pips":
                                  daemon_books[k]["gate_metrics"]["per_fold_net_pips"],
                              "n_months":
                                  daemon_books[k]["gate_metrics"]["n_months"],
                              "top_fold_share":
                                  daemon_books[k]["gate_metrics"]["top_fold_share"],
                              "top5_trades_share":
                                  daemon_books[k]["gate_metrics"]["top5_trades_share"],
                              "top_hour_share":
                                  daemon_books[k]["gate_metrics"]["top_hour_share"],
                              "top_fold_id":
                                  daemon_books[k]["gate_metrics"]["top_fold_id"],
                              "top_hour":
                                  daemon_books[k]["gate_metrics"]["top_hour"],
                          }}
                      for k in ("1.0", "1.5", "2.0")}}
    return S.evaluate_gates(cell)


def daily_sr_context(p: T.SignalPlane, trades: list) -> dict:
    """Optional DSR-style context (descriptive): non-annualized daily
    Sharpe of a book's UTC-day net pips over the full diagnostic panel."""
    s = S.daily_series(trades, ts_of(PANEL_START), ts_of(PANEL_END, end=True))
    sd = float(s.std(ddof=1))
    return {"sr_daily": round(float(s.mean()) / sd, 6) if sd > 0 else 0.0,
            "n_days": int(len(s))}


def strip_books(books: dict) -> dict:
    """JSON-safe view (everything already is; kept for symmetry)."""
    return books


def sha_chain() -> dict:
    cohort = DIAG.parent
    code = {}
    for rel in ("scripts/tracka_lib.py", "scripts/engine.py",
                "scripts/falsifier_run.py", "scripts/scored_lib.py",
                "scripts/build_bars.py", "scripts/build_signal_plane.py",
                "scripts/pair_config.py"):
        code[rel] = sha256_file(cohort / rel)
    diag_code = {}
    for rel in sorted((DIAG / "scripts").glob("*.py")):
        diag_code[f"diag/scripts/{rel.name}"] = sha256_file(rel)
    return {
        "committed_code_freeze": code,
        "diag_code": diag_code,
        "census_sha256": {p: sha256_file(DERIVED / f"census_{p}.json")
                          for p in PAIRS},
        "m1_manifest_sha256": {
            p: sha256_file(DIAG / "data_local" / p / "m1_manifest.json")
            for p in PAIRS},
        "copy_verify_sha256": {
            p: sha256_file(DERIVED / f"copy_verify_{p}.json") for p in PAIRS},
        "probe_sha256": {p: sha256_file(DERIVED / f"probe_{p}.json")
                         for p in PAIRS},
    }
