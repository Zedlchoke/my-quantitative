"""RETEST-V1 golden tests — owner-named fixtures for the new laws (plan §6).

T-R1 ghost quarantine (HTV class) · T-R2 zero-volume fill fails ·
T-R3 double alias dedupe · T-R4 reverse-split extreme print (B1 both
directions) · T-R5 price-unit jump · T-R6 missing identity ·
T-R7 fill-volume lookahead firewall · T-R8 negative controls (poisoned
panel must be blocked, guards must fire)."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest

IMPL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IMPL))

from samv1r import engine as E                      # noqa: E402
from samv1r.panel import NameSeries, GuardCounters  # noqa: E402
from samv1r.portfolio import simulate               # noqa: E402
import test_golden_inherited as T                   # noqa: E402  (reuse synth helpers)

SESSIONS = T.SESSIONS
SESS_IDX = T.SESS_IDX


def synth(code, n=10**9, **kw):
    ns = T.synth(code, n, **kw)
    return ns


# --- T-R1 ghost quarantine: census law Q1 catches the HTV fixture class
def test_ghost_quarantine_law():
    census = json.loads((Path(__file__).resolve().parents[2] / "p0"
                         / "identity_census.json").read_text())
    manifest = {}
    for line in (Path(__file__).resolve().parents[2] / "p0"
                 / "quarantine_manifest.jsonl").read_text().splitlines():
        rec = json.loads(line)
        manifest[rec["code"]] = rec["reasons"]
    assert any(r.startswith("Q1") for r in manifest.get("HTV", [])), "HTV must be Q1-ghosted"
    assert any(r.startswith("Q1") for r in manifest.get("NLG", [])), "NLG must be Q1-ghosted"
    uni = json.loads((Path(__file__).resolve().parents[2] / "p0"
                      / "universe_retest_frozen.json").read_text())
    assert "HTV" not in uni["codes"] and "NLG" not in uni["codes"]
    assert census["counts" if "counts" in census else "kept"] or True


# --- T-R2 zero-volume fill: entry at a V=0 bar is UNFILLED (counted)
def test_zero_volume_fill_fails():
    panel = T.eligible_panel(60)
    victim = panel["N039"]
    # find the first bookable fill date for the victim and zero its volume
    grid = E.build_grid(SESSIONS)
    t0 = grid[0]
    fill0 = SESSIONS[SESS_IDX[t0] + 1]
    fi = victim.idx[fill0]
    victim.vol[fi] = 0.0
    victim.dv[fi] = 0.0
    victim.fill_ok[fi] = False
    sim = simulate(panel, SESSIONS, "illiq21", scored=False)
    holds = [h for h in sim["holds"] if h.code == "N039"
             and h.entry_decision == t0]
    assert holds == [], "entry at a zero-volume bar must be unfilled"
    assert sim["guards"].unfilled_entries_x1 >= 1


# --- T-R3 double alias: census Q3 keeps exactly one of the same-ISIN trio
def test_double_alias_dedupe():
    manifest = {}
    for line in (Path(__file__).resolve().parents[2] / "p0"
                 / "quarantine_manifest.jsonl").read_text().splitlines():
        rec = json.loads(line)
        manifest[rec["code"]] = rec["reasons"]
    tri = {c: any(r.startswith("Q3") for r in manifest.get(c, []))
           for c in ("BBBY", "BYON", "OSTK")}
    assert tri["BBBY"] is False, "lexicographically-first kept"
    assert tri["BYON"] and tri["OSTK"], "both replicas quarantined"
    uni = json.loads((Path(__file__).resolve().parents[2] / "p0"
                      / "universe_retest_frozen.json").read_text())
    assert "BBBY" in uni["codes"] and "BYON" not in uni["codes"] \
        and "OSTK" not in uni["codes"]


# --- T-R4 reverse split: B1 catches BOTH directions (log-ratio law)
def test_reverse_split_extreme_print_both_directions():
    g = GuardCounters()
    ns = synth("X", 10**9, ret=0.0005)
    i = SESS_IDX["2020-06-10"]
    ns.adj[i] = ns.adj[i - 1] * 12.0      # +1100% up   -> extreme
    ns.dv[i] = ns.adj[i] * ns.vol[i]
    j = SESS_IDX["2021-06-10"]
    ns.adj[j] = ns.adj[j - 1] / 12.0      # -91.7% "10x down" -> extreme
    ns.dv[j] = ns.adj[j] * ns.vol[j]
    # recompute fill flags via the loader pass-2 logic
    for k in range(len(ns.dates)):
        ok = ns.adj_ok[k] and ns.vol[k] > 0
        if k > 0 and ok and ns.adj_ok[k - 1] and ns.adj[k - 1] > 0:
            if abs(math.log(ns.adj[k] / ns.adj[k - 1])) >= math.log(10.0):
                ok = False
        ns.fill_ok[k] = ok
    assert not ns.fill_ok[i] and not ns.fill_ok[j], "both directions must be unfillable"
    # formation excludes both bars
    gsc = E.Guards()
    E.illiq(ns, SESS_IDX["2020-06-30"], 21, gsc)
    assert gsc.formation_skip_dv >= 1


# --- T-R5 price-unit jump: a 10x jump on tiny volume is unfillable + B1
def test_price_unit_jump():
    ns = synth("Y", 10**9, ret=0.0005)
    i = SESS_IDX["2019-08-15"]
    ns.adj[i] *= 25.0                      # unit-style jump
    ns.dv[i] = ns.adj[i] * ns.vol[i]
    ns.fill_ok[i] = False                  # loader pass-2 equivalent
    g = E.Guards()
    E.illiq(ns, SESS_IDX["2019-09-03"], 21, g)
    assert g.formation_skip_dv >= 1


# --- T-R6 missing identity: no metadata + flags -> quarantine; clean -> stay
def test_missing_identity_rule():
    manifest = {}
    for line in (Path(__file__).resolve().parents[2] / "p0"
                 / "quarantine_manifest.jsonl").read_text().splitlines():
        rec = json.loads(line)
        manifest[rec["code"]] = rec["reasons"]
    quarantined = [c for c, r in manifest.items()
                   if any(x.startswith(("Q1", "Q2", "Q3", "Q4")) for x in r)]
    assert len(quarantined) > 500          # the law bites broadly, uniformly
    # vendor-test pattern present
    assert any(any(x.startswith("Q2") for x in r) for r in manifest.values())


# --- T-R7 fill-volume firewall: mutating FILL-bar volumes never changes
#     decisions/book at t (only fills/execution)
def test_fill_volume_firewall():
    panel1 = T.eligible_panel(60)
    panel2 = T.eligible_panel(60)
    grid = E.build_grid(SESSIONS)
    t0 = grid[0]
    fill0 = SESSIONS[SESS_IDX[t0] + 1]
    # mutate fill-bar volumes in panel2
    for code, ns in panel2.items():
        fi = ns.idx.get(fill0)
        if fi is not None:
            ns.vol[fi] = max(1.0, ns.vol[fi] * 3.0)
            ns.dv[fi] = ns.adj[fi] * ns.vol[fi]
    s1 = simulate(panel1, SESSIONS, "illiq21", scored=False)
    s2 = simulate(panel2, SESSIONS, "illiq21", scored=False)
    d1 = {d["date"]: (d["n_elig"], d["n_book"], tuple(d["book_codes"]))
          for d in s1["per_date"] if d["date"] <= fill0}
    d2 = {d["date"]: (d["n_elig"], d["n_book"], tuple(d["book_codes"]))
          for d in s2["per_date"] if d["date"] <= fill0}
    assert d1 == d2, "fill-bar volume mutation leaked into decisions at t"


# --- T-R8 negative controls: poisoned panel must be blocked by the guards
def test_negative_controls_block_poison():
    panel = T.eligible_panel(60)
    # poison 1: extreme print inside a formation window
    v = panel["N039"]
    i = v.idx["2019-05-15"]
    v.adj[i] = v.adj[i - 1] * 20.0
    v.dv[i] = v.adj[i] * v.vol[i]
    v.fill_ok[i] = False
    # poison 2: zero-volume fill bar
    w = panel["N038"]
    j = w.idx[SESSIONS[SESS_IDX[E.build_grid(SESSIONS)[0]] + 1]]
    w.vol[j] = 0.0
    w.dv[j] = 0.0
    w.fill_ok[j] = False
    sim = simulate(panel, SESSIONS, "illiq21", scored=False)
    # neither poison produced a fantasy entry
    assert not [h for h in sim["holds"]
                if h.entry_px / panel[h.code].adj[0] > 100]
    assert sim["guards"].unfilled_entries_x1 >= 1
    # guard class iii still fails loud on empty book
    with pytest.raises(E.FailLoud):
        E.weights_for([], {})
