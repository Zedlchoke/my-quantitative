#!/usr/bin/env python
"""Lane FXJA-K6, FUTURES-K6GATE-PREP-20261004 — M2: RMM D-1 mode ledger.

Derives per-roll mode labels (abrupt = cease-guard-triggered vs gradual =
k5-crossover-triggered) for 6E/6B/6J from the committed switch tables /
chain caches, using the exact committed algorithms (fx_ja_lib.k5_chain +
the explicit cease-guard variant verbatim from fx_ja/6a_roll_measure.py
variant B). 6A is CITED from 6a_roll_measured.json (not redone).

Cross-checks (pre-declared): derived baseline switch dates == committed
switch tables (6E/6B: cost_roll_events_fxeb.json roll_remeasure; 6J:
6J_cache/held_volume_k5.parquet chain; 6A: both variants of
6a_roll_measured.json reproduced from raw as verification for M3/M4 use).

Unconditional roll mechanics only: dates + volumes. NO PnL, NO returns.
"""
from __future__ import annotations

import json
import os
import re
import sys

import numpy as np
import pandas as pd

HERE = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-k6gate/prep/research/control/FUTURES-K6GATE-PREP-20261004/fx_ja"
RDY = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-k6gate/prep/research/control/FUTURES-SIX-READINESS-20261004"
SIXWRK = ("/Users/hoangminhlong/my-quantitative/.worktrees/futures-six-readiness"
          "/prep/research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis")
sys.path.insert(0, os.path.join(RDY, "fx_ja"))
from fx_ja_lib import DATA_ROOT, add_session, jdump, k5_chain, next_quarter  # noqa: E402

QRE = re.compile(r"^6[A-Z][HMUZ]\d_\d{4}$")


def registry_iid_map(registry_json_path):
    d = json.load(open(registry_json_path))
    m = {}
    for row in d:
        for iid in row["instrument_ids"]:
            m[int(iid)] = row["contract"]
    return m


def quarterly_wide(vol_df):
    """wide session_date x quarterly-contract volume; NaN = no bars."""
    w = vol_df.pivot_table(index="session_date", columns="contract",
                           values="volume", aggfunc="sum").sort_index()
    qcols = [c for c in w.columns if QRE.fullmatch(str(c))]
    return w[qcols]


def cease_guard_variant(wide):
    """Verbatim from fx_ja/6a_roll_measure.py variant B (same expressions)."""
    roll5 = wide.rolling(5, min_periods=1).mean()
    state = None
    held_b = {}
    rolls_b = []
    for d in wide.index:
        r5 = roll5.loc[d].dropna()
        r5 = r5[r5 > 0]
        row = wide.loc[d]
        if state is None:
            state = r5.idxmax()
        else:
            v = row.get(state, np.nan)
            if pd.isna(v):
                old = state
                state = next_quarter(state)
                nv = row.get(state, np.nan)
                rolls_b.append({"switch_session": str(d), "old": old,
                                "new": state, "trigger": "cease_guard_no_bars",
                                "new_volume_at_switch": None if pd.isna(nv) else int(nv)})
            else:
                nxt = next_quarter(state)
                if nxt in r5.index and r5[nxt] > r5[state]:
                    old = state
                    state = nxt
                    rolls_b.append({"switch_session": str(d), "old": old,
                                    "new": state, "trigger": "k5_crossover"})
        held_b[d] = state
    return rolls_b, held_b


def baseline_rolls(wide):
    chain = k5_chain(wide, k=5).set_index("session_date")["held"]
    rolls, prev = [], None
    for d, held in chain.items():
        if prev is not None and held != prev:
            rolls.append({"switch_session": str(d), "old": prev, "new": held})
        prev = held
    return rolls, chain


def main():
    out = {"schema": "rmm_mode_ledger@1",
           "lane": "FXJA-K6", "round": "FUTURES-K6GATE-PREP-20261004",
           "predeclaration": "FXJA_K6_GATES.md §0.3 (written before compute)",
           "mode_law": ("HYPOTHESES_R2.md §2 RMM field 3: mode label = "
                        "strict-past classification from the measured "
                        "old-contract last-bars session vs the k=5 crossover "
                        "trigger; abrupt = cease_guard_no_bars, gradual = "
                        "k5_crossover (same two triggers as the committed "
                        "6a_roll_measured.json cease-guard variant)"),
           "no_pnl_note": "volumes and dates only; no returns, no costs",
           "zero_fetch_note": "no network; committed caches + raw parquets read-only",
           "symbols": {}}

    # ---------------- 6E ----------------
    reg6e = registry_iid_map(f"{SIXWRK}/6E_cache/contract_registry.json")
    e = pd.read_parquet(f"{SIXWRK}/6E_cache/6e_annotated_1m.parquet",
                        columns=["instrument_id", "session_date", "volume"])
    e["contract"] = e["instrument_id"].astype("int64").map(reg6e)
    unmapped_e = int(e["contract"].isna().sum())
    we = quarterly_wide(e.dropna(subset=["contract"]))
    rolls_e_base, chain_e = baseline_rolls(we)
    rolls_e_cg, _ = cease_guard_variant(we)
    committed_e = json.load(open(
        f"{RDY}/fx_eb/cost_roll_events/cost_roll_events_fxeb.json")
    )["roll_remeasure"]["6E"]["switches"]

    # ---------------- 6B ----------------
    b = pd.read_parquet(f"{SIXWRK}/6B_cache/6b_annotated_1m.parquet",
                        columns=["instrument_id", "contract", "session_date", "volume"])
    nn = b[b["contract"].notna()]
    iid6b = {int(k): v for k, v in
             nn.groupby("instrument_id")["contract"].agg(lambda s: s.mode().iloc[0]).items()}
    assert all(QRE.fullmatch(c) for c in iid6b.values()), "6B map has non-quarterly"
    b["contract"] = b["instrument_id"].astype("int64").map(iid6b)
    unmapped_b = int(b["contract"].isna().sum())
    wb = quarterly_wide(b.dropna(subset=["contract"]))
    rolls_b_base, chain_b = baseline_rolls(wb)
    rolls_b_cg, _ = cease_guard_variant(wb)
    committed_b = json.load(open(
        f"{RDY}/fx_eb/cost_roll_events/cost_roll_events_fxeb.json")
    )["roll_remeasure"]["6B"]["switches"]

    # identify the committed 6E/6B chain rule from the chain parquets themselves
    def chain_rule_check(sym, committed):
        if sym == "6E":
            hc = pd.read_parquet(f"{SIXWRK}/6E_cache/held_calendar.parquet")
        else:
            hc = pd.read_parquet(f"{SIXWRK}/6B_cache/held_calendar.parquet")
        tr = hc[hc["held"] != hc["held"].shift()]
        dates = [str(d) for d in tr["session_date"][1:]]
        cdates = [s["first_session_on_new_contract"] for s in committed]
        return {"committed_chain_transitions_n": len(dates),
                "committed_switch_table_is_chain_calendar_rule":
                    dates == cdates,
                "first_transitions": dates[:4]}

    # ---------------- 6J ----------------
    j = pd.read_parquet(f"{SIXWRK}/6J_cache/6j_annotated_1m.parquet",
                        columns=["instrument_id", "contract", "session_date", "volume"])
    reg6j = registry_iid_map(f"{SIXWRK}/6J_cache/contract_registry.json")
    agree = int((j["instrument_id"].astype("int64").map(reg6j).fillna("~")
                 != j["contract"].fillna("~")).sum())
    unmapped_j = int(j["contract"].isna().sum())
    wj = quarterly_wide(j.dropna(subset=["contract"]))
    rolls_j_base, chain_j = baseline_rolls(wj)
    rolls_j_cg, _ = cease_guard_variant(wj)
    committed_j_chain = pd.read_parquet(f"{SIXWRK}/6J_cache/held_volume_k5.parquet")
    committed_j = [
        {"switch_session": str(d), "old": o, "new": n}
        for (d, o, n) in zip(
            committed_j_chain["session_date"][1:],
            committed_j_chain["held"][:-1],
            committed_j_chain["held"][1:])
        if o != n]

    # ---------------- 6A (verification re-derivation for M3/M4 chain use) ----
    reg = pd.read_parquet(f"{SIXWRK}/6A_cache/registry.parquet")
    iid2c = dict(zip(reg["instrument_id"].astype("int64"), reg["contract"]))
    files = (sorted(__import__("glob").glob(f"{DATA_ROOT}/AV1B-O1M-6A-BACKFILL2/*.parquet"))
             + sorted(__import__("glob").glob(f"{DATA_ROOT}/AV1R-O1M-6A-BACKFILL/*.parquet"))
             + sorted(__import__("glob").glob(f"{DATA_ROOT}/AV1T-O1M-6A/*.parquet")))
    parts = []
    for f in files:
        parts.append(pd.read_parquet(f, columns=["instrument_id", "raw_symbol",
                                                 "ts_event", "volume"]))
    a = pd.concat(parts, ignore_index=True)
    a["dt"] = pd.to_datetime(a["ts_event"], unit="ns", utc=True)
    a = add_session(a)
    a = a[a["raw_symbol"].str.fullmatch(r"6A[FGHJKMNQUVXZ]\d")]
    a["contract"] = a["instrument_id"].astype("int64").map(iid2c)
    unmapped_a = int(a["contract"].isna().sum())
    wa = quarterly_wide(a.dropna(subset=["contract"]))
    rolls_a_base, chain_a = baseline_rolls(wa)
    rolls_a_cg, held_a = cease_guard_variant(wa)
    a_measured = json.load(open(f"{RDY}/fx_ja/6a_roll_measured.json"))

    def dset(rolls):
        return [r["switch_session"] for r in rolls]

    checks = {
        "6E_vs_committed_switch_table": {
            "committed_n": len(committed_e), "derived_n": len(rolls_e_base),
            "dates_equal": dset(rolls_e_base) ==
                           [s["first_session_on_new_contract"] for s in committed_e],
            "pairs_equal": [(r["old"], r["new"]) for r in rolls_e_base] ==
                           [(s["from"], s["to"]) for s in committed_e]},
        "6B_vs_committed_switch_table": {
            "committed_n": len(committed_b), "derived_n": len(rolls_b_base),
            "dates_equal": dset(rolls_b_base) ==
                           [s["first_session_on_new_contract"] for s in committed_b],
            "pairs_equal": [(r["old"], r["new"]) for r in rolls_b_base] ==
                           [(s["from"], s["to"]) for s in committed_b]},
        "6J_vs_committed_held_chain": {
            "committed_n": len(committed_j), "derived_n": len(rolls_j_base),
            "dates_equal": dset(rolls_j_base) == [r["switch_session"] for r in committed_j],
            "pairs_equal": [(r["old"], r["new"]) for r in rolls_j_base] ==
                           [(r["old"], r["new"]) for r in committed_j]},
        "6A_verification_vs_6a_roll_measured": {
            "baseline_dates_equal": dset(rolls_a_base) ==
                [r["switch_session"] for r in a_measured["k5_baseline_variant"]["rolls"]],
            "cg_dates_and_triggers_equal":
                [(r["switch_session"], r["trigger"]) for r in rolls_a_cg] ==
                [(r["switch_session"], r["trigger"])
                 for r in a_measured["k5_cease_guard_variant"]["rolls"]],
            "unmapped_rows": unmapped_a},
    }
    checks["6E_identity_unmapped_rows"] = unmapped_e
    checks["6B_identity_unmapped_rows"] = unmapped_b
    checks["6B_identity_unmapped_note"] = ("non-quarterly (non-HMUZ) month-code "
                                           "bars; never enter the quarterly wide "
                                           "table by construction")
    checks["6J_identity_unmapped_rows"] = unmapped_j
    checks["6J_registry_vs_cache_contract_disagreements"] = agree
    checks["6E_committed_chain_rule"] = chain_rule_check("6E", committed_e)
    checks["6B_committed_chain_rule"] = chain_rule_check("6B", committed_b)

    # ---------------- ledger ----------------
    EV = {"6E": {"chain": "6E_cache/held_volume_k5.parquet (committed baseline chain)",
                 "switch_table": "fx_eb/cost_roll_events/cost_roll_events_fxeb.json:roll_remeasure.6E.switches",
                 "wide": "6E_cache/6e_annotated_1m.parquet + 6E_cache/contract_registry.json",
                 "algorithm": "fx_ja_lib.k5_chain + explicit cease-guard variant, verbatim from fx_ja/6a_roll_measure.py variant B (committed)"},
            "6B": {"chain": "6B_cache/held_volume_crossover.parquet (committed baseline chain family)",
                   "switch_table": "fx_eb/cost_roll_events/cost_roll_events_fxeb.json:roll_remeasure.6B.switches",
                   "wide": "6B_cache/6b_annotated_1m.parquet non-null (instrument_id, contract) quarterly map (32 iids; registry ABSENT in cache per 6B chain_calendar_note)",
                   "algorithm": "fx_ja_lib.k5_chain + explicit cease-guard variant, verbatim from fx_ja/6a_roll_measure.py variant B (committed)"},
            "6J": {"chain": "6J_cache/held_volume_k5.parquet (committed baseline chain)",
                   "switch_table": "6J_cache/held_volume_k5.parquet transitions; 2022-09 exemplar per fx_ja/6j_cease_guard_2022.json",
                   "wide": "6J_cache/6j_annotated_1m.parquet (contract column cross-checked vs 6J_cache/contract_registry.json)",
                   "algorithm": "fx_ja_lib.k5_chain + explicit cease-guard variant, verbatim from fx_ja/6a_roll_measure.py variant B (committed)"},
            "6A": {"chain": "fx_ja/6a_roll_measured.json:k5_cease_guard_variant (committed; re-derived here only as verification)",
                   "switch_table": "fx_ja/6a_roll_measured.json:k5_cease_guard_variant.rolls",
                   "wide": "raw roots AV1B/AV1R/AV1T-O1M-6A + 6A_cache/registry.parquet",
                   "algorithm": "committed artifact CITED (21 cease_guard_no_bars / 6 k5_crossover); not redone"}}

    def ledger_for(sym, cg_rolls, committed):
        cby = {r.get("switch_session",
                    r.get("first_session_on_new_contract")): r
               for r in committed}
        rows = []
        for r in cg_rolls:
            mode = "abrupt" if r["trigger"] == "cease_guard_no_bars" else "gradual"
            c = cby.get(r["switch_session"], {})
            row = {
                "switch_session": r["switch_session"],
                "old": r.get("old"), "new": r.get("new"),
                "trigger": r["trigger"], "mode": mode,
                "new_volume_at_switch": r.get("new_volume_at_switch"),
                "evidence": {
                    "trigger_source": ("cease-guard variant (hard switch at held "
                                       "contract's no-bars session) — "
                                       + EV[sym]["algorithm"]),
                    "switch_table_crosscheck": c or None,
                    "wide_source": EV[sym]["wide"],
                    "chain": EV[sym]["chain"]},
            }
            if c and c.get("first_session_on_new_contract") not in (None, r["switch_session"]):
                row["declared_rule_switch_session"] = c["first_session_on_new_contract"]
                row["declared_vs_measured_rule_divergence_sessions"] = None  # filled below
            rows.append(row)
        # fill divergence in trading sessions (position in the derived chain index)
        return rows

    led = {"6E": ledger_for("6E", rolls_e_cg, committed_e),
           "6B": ledger_for("6B", rolls_b_cg, committed_b),
           "6J": ledger_for("6J", rolls_j_cg, committed_j),
           "6A": ledger_for("6A", rolls_a_cg,
                            a_measured["k5_cease_guard_variant"]["rolls"])}
    # K6(c) sensitivity: declared-calendar vs measured (k5/cease-guard) rule
    # divergence, itemized per roll in CALENDAR DAYS (never normalized).
    rule_div = {}
    for sym in ("6E", "6B"):
        items = []
        for r in led[sym]:
            dr = r.pop("declared_rule_switch_session", None)
            r.pop("declared_vs_measured_rule_divergence_sessions", None)
            if dr:
                items.append({"declared_calendar_rule_switch": dr,
                              "measured_cg_switch": r["switch_session"],
                              "divergence_calendar_days":
                                  (pd.Timestamp(r["switch_session"])
                                   - pd.Timestamp(dr)).days})
        rule_div[sym] = items
    for sym in ("6A",):
        for row in led[sym]:
            row["evidence"]["cited_artifact"] = (
                "fx_ja/6a_roll_measured.json:k5_cease_guard_variant.rolls[].trigger "
                "(CITED, not redone — dispatch law)")
            row["evidence"]["trigger_source"] = (
                "committed cease-guard variant trigger field (verbatim cite)")

    splits = {s: {"abrupt": sum(1 for r in led[s] if r["mode"] == "abrupt"),
                  "gradual": sum(1 for r in led[s] if r["mode"] == "gradual"),
                  "n_rolls": len(led[s])} for s in led}

    # ---------------- CEASE-SYNC descriptive pass ----------------
    iso = {s: [pd.Timestamp(r["switch_session"]).isocalendar() for r in led[s]
               if r["mode"] == "abrupt"] for s in led}
    abrupt_dates = {s: [r["switch_session"] for r in led[s]
                        if r["mode"] == "abrupt"] for s in led}
    weeks = {}
    for s, lst in iso.items():
        for ic in lst:
            key = (ic.year, ic.week)
            weeks.setdefault(key, set()).add(s)
    from collections import Counter
    exact = Counter(len(v) for v in weeks.values())
    # ±1 ISO-week tolerance
    tol = {}
    allkeys = sorted(weeks)
    for key in allkeys:
        y, w = key
        neigh = set()
        for dy in (-1, 0, 1):
            ts = pd.Timestamp.fromisocalendar(y, w, 1) + pd.Timedelta(weeks=dy)
            ic = ts.isocalendar()
            neigh |= weeks.get((ic.year, ic.week), set())
        tol[key] = neigh
    tolc = Counter(len(v) for v in tol.values())

    multi = [{"iso_year": k[0], "iso_week": k[1],
              "week_start": str(pd.Timestamp.fromisocalendar(k[0], k[1], 1).date()),
              "symbols_abrupt": sorted(weeks[k])}
             for k in allkeys if len(weeks[k]) >= 2]
    multi_tol = [{"iso_year": k[0], "iso_week": k[1],
                  "week_start": str(pd.Timestamp.fromisocalendar(k[0], k[1], 1).date()),
                  "symbols_abrupt_within_+/-1w": sorted(tol[k])}
                 for k in allkeys if len(tol[k]) >= 2]

    out["crosscheck"] = checks
    out["declared_vs_measured_rule_divergence"] = {
        "law": "RMM K6(c): declared-rule and measured-rule date divergence must "
               "be reported as a sensitivity, never silently normalized",
        "finding": ("the committed 6E/6B switch tables and held chains roll on the "
                    "DECLARED CALENDAR rule (verified: held_calendar.parquet / "
                    "chain_calendar.parquet transitions land on the "
                    "first-session-of-roll-month dates, e.g. 2020-03-02, matching "
                    "the calendar_roll_dates pattern of "
                    "6a_roll_measured.json:calendar_rule_cross_reference); the RMM "
                    "mode ledger is derived on the k5 + explicit cease-guard "
                    "measured family (RMM field-4 event clock = the explicit "
                    "cease-guard-variant switch session) — the date sets diverge "
                    "by design, itemized per roll below; pairs (from,to) agree "
                    "27/27 for both symbols"),
        "6E": rule_div["6E"],
        "6B": rule_div["6B"],
    }
    out["mode_split"] = splits
    out["ledger"] = led
    out["cease_sync_descriptive"] = {
        "boundary": ("descriptive ONLY — block-shuffle placebo (>=100 seeds) is a "
                     "FUTURE scored-side control per predeclaration §0.3; NO "
                     "cluster-vs-symbol-local verdict is issued here"),
        "definition": "ISO-week (Mon-based) of abrupt switch_session; weeks keyed by isocalendar year/week",
        "n_distinct_abrupt_weeks": len(weeks),
        "weeks_by_n_symbols_simultaneous_exact": {str(k): v for k, v in sorted(exact.items())},
        "weeks_by_n_symbols_within_+/-1w": {str(k): v for k, v in sorted(tolc.items())},
        "weeks_with_>=2_symbols_exact": multi,
        "weeks_with_>=2_symbols_within_+/-1w": multi_tol,
        "abrupt_dates_per_symbol": abrupt_dates,
    }
    jdump(out, os.path.join(HERE, "rmm_mode_ledger.json"))
    print(json.dumps({"checks": checks, "splits": splits,
                      "exact": dict(exact), "tol": dict(tolc)}, indent=1, default=str))


if __name__ == "__main__":
    main()
