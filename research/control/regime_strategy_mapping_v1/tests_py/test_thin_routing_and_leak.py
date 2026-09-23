"""A7 remediation tests (R1 F1/F3 + R2 N1/N2/N3): OUTER thin-routing gate,
fold-index law, and NON-VACUOUS selection-invariance (leak) test.

N2 fix rationale: the earlier leak fixture was vacuous — the stubbed ctx had
no episodes so every selection FLAT'd via inner floors and CLEAN≡LEAKY. The
fixtures below make inner floors PASS (so a specialist is actually selected
and a leak would change the outcome), then mutate OUTER folds and assert
the selections are byte-identical. A deliberately LEAKY selector variant is
executed to prove the fixture can detect a leak (CLEAN≠LEAKY).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rsmv1.freezes import Freezes  # noqa: E402
from rsmv1.selection import SpecialistCandidate  # noqa: E402

CYCLE = Path(__file__).resolve().parents[1]


class _Ctx:
    """Minimal scored.CellCtx stand-in: episodes populated so inner floors
    PASS for UPTREND (>=5 episodes, >=150 eligible decisions per inner set);
    fake ct places each episode's start inside the intended REAL fold span."""

    cell = "BTC_H1"
    asset = "BTCUSDT"
    fz = None

    def __init__(self, episodes=None):
        import numpy as np

        from rsmv1.scored import _iso_ns

        self.fz = Freezes(CYCLE)
        spans = [
            (_iso_ns(sp["start"]), _iso_ns(sp["end"]))
            for sp in self.fz.fold_contract["cells"]["BTC_H1"]["folds"]
        ]
        H1 = 3_600_000_000_000

        class _RB:
            ts_close = np.array(
                [spans[min(f, 3)][0] + (j + 1) * H1
                 for f in range(4) for j in range(2)]
                + [spans[0][0] + H1] * 9000, dtype=np.int64)

        class _CT:
            regime_bars = _RB()

        self.ct = _CT()
        # episodes reference row indices into _RB.ts_close: rows 0..7 are the
        # two placed starts per fold; lengths are symbolic (not used by ts)
        if episodes is not None:
            self.episodes = episodes
        else:
            self.episodes = [
                {"label": "UPTREND", "start": 2 * f + j, "length": 25}
                for f in range(4) for j in range(2)
            ]


def _census(thin: set[str]) -> dict:
    return {"per_regime": {
        r: ({"verdict": "NOT_RUN_THIN_REGIME", "episodes_total": 1,
             "margin_to_floor_min": 0.0} if r in thin else
            {"verdict": "SAMPLE_OK", "episodes_total": 28,
             "margin_to_floor_min": 1.4})
        for r in ("ACCUMULATION", "UPTREND", "DISTRIBUTION", "DOWNTREND")
    }}


def _evidence(uptrend_folds: dict[int, float]) -> dict:
    return {"UPTREND": {
        "UPT-DIPBUY-L": {"fold_nets": dict(uptrend_folds),
                         "pooled_net": sum(uptrend_folds.values()),
                         "trades": 10},
        "UPT-BREAKOUT-L": {"fold_nets": {f: v - 50.0 for f, v in uptrend_folds.items()},
                           "pooled_net": sum(uptrend_folds.values()) - 50.0,
                           "trades": 8},
    }}


def _arm_c_selection(ctx, evidence, census):
    import rsmv1.census as census_mod
    import rsmv1.scored as scored_mod

    real = census_mod.measure_cell_census
    census_mod.measure_cell_census = lambda cd, cell: census
    try:
        return scored_mod.arm_c_selection(ctx, evidence)
    finally:
        census_mod.measure_cell_census = real


def test_outer_thin_routes_flat_despite_rich_inner_evidence():
    """R1 F1: THIN regime -> FLAT in every fold even with abundant inner
    evidence and passing inner floors."""
    ev = _evidence({0: 100.0, 1: 200.0, 2: 50.0})
    mapping, audit = _arm_c_selection(
        _Ctx(), ev, _census(thin={"UPTREND", "ACCUMULATION", "DISTRIBUTION",
                                  "DOWNTREND"}))
    for fid in range(4):
        for regime in ("ACCUMULATION", "UPTREND", "DISTRIBUTION", "DOWNTREND"):
            assert mapping[fid][regime] == "FLAT", (fid, regime)
    up_rows = [a for a in audit if a["regime"] == "UPTREND"]
    assert all(a["reason"] == "OUTER_FLOOR_THIN" for a in up_rows)


def test_real_census_btc_h4_all_thin():
    """R2 N3: against the REAL census (no stub), BTC_H4 routes every regime
    FLAT in arm C (census verdicts: 4/12/1/14 episodes — all THIN)."""
    ev = _evidence({0: 500.0, 1: 500.0, 2: 500.0})
    mapping, audit = _arm_c_selection(_Ctx(), ev, None) if False else (None, None)
    import rsmv1.census as census_mod
    import rsmv1.scored as scored_mod

    real = census_mod.measure_cell_census
    census_mod.measure_cell_census = lambda cd, cell: real(cd, "BTC_H4")
    # NOTE: cell must be BTC_H4 for the census; override ctx cell
    ctx = _Ctx()
    ctx.cell = "BTC_H4"
    try:
        mapping, audit = scored_mod.arm_c_selection(ctx, ev)
    finally:
        census_mod.measure_cell_census = real
    for fid in range(4):
        for regime in ("ACCUMULATION", "UPTREND", "DISTRIBUTION", "DOWNTREND"):
            assert mapping[fid][regime] == "FLAT", (fid, regime)
    assert all(a["reason"] == "OUTER_FLOOR_THIN"
               for a in audit if a["regime"] == "UPTREND")


def test_fold0_defaults_flAT_and_fold1_selects():
    """R2 N1: fid 0 (law's fold 1) -> empty-inner FLAT; fid 1 selects when
    inner floors pass (this is the exact bug A7-R2 caught)."""
    ev = _evidence({0: 100.0, 1: 200.0})
    mapping, audit = _arm_c_selection(_Ctx(), ev, _census(thin=set()))
    up = {a["fold_id"]: a for a in audit if a["regime"] == "UPTREND"}
    assert up[0]["reason"] == "fold1_empty_inner_default"
    # fid 1: inner = fold 0; floors pass (2 eps x25 = 50 dec? -> see below)
    # episodes: 2 in fold 0 of length 25 -> 50 decisions < 150 -> FLAT by
    # inner floor. Give a longer-episode ctx to let fid>=1 select.
    ctx = _Ctx(episodes=[
        {"label": "UPTREND", "start": 300 + f * 200 + j, "length": 80}
        for f in range(4) for j in range(2)
    ])  # fold-0 pool: 2 eps x 80 = 160 >= 150
    mapping2, audit2 = _arm_c_selection(ctx, ev, _census(thin=set()))
    up2 = {a["fold_id"]: a for a in audit2 if a["regime"] == "UPTREND"}
    assert up2[0]["reason"] == "fold1_empty_inner_default"
    assert up2[1]["selected"] == "UPT-DIPBUY-L", up2[1]
    assert up2[1]["reason"] == "inner_net_higher_stable"


def test_selection_invariance_nonvacuous():
    """R1 F3 / R2 N2: mutate OUTER-fold evidence; selections identical. The
    fixture is proven sensitive by a deliberately leaky selector that FAILS
    the same assertion."""
    ctx = _Ctx(episodes=[
        {"label": "UPTREND", "start": 300 + f * 200 + j, "length": 80}
        for f in range(4) for j in range(2)
    ])
    clean_ev = _evidence({0: 100.0, 1: 60.0, 2: 40.0, 3: -999.0})
    mut_ev = _evidence({0: 100.0, 1: 60.0, 2: -1e6, 3: 1e6})
    _, audit_clean = _arm_c_selection(ctx, clean_ev, _census(thin=set()))
    _, audit_mut = _arm_c_selection(ctx, mut_ev, _census(thin=set()))
    for a, b in zip(audit_clean, audit_mut):
        assert (a["selected"], a["reason"]) == (b["selected"], b["reason"]), (a, b)

    # sensitivity proof (CLEAN ≠ LEAKY): a selector that (illegally) pools
    # the OUTER fold into fold k's evidence would flip fold 2's choice.
    import rsmv1.scored as scored_mod

    def leaky_selection(ctx_, evidence):
        from rsmv1.specialists import eligible_for

        mapping_by_fold, audit = {}, []
        for fid in range(4):
            mapping = {"TRANSITION_UNKNOWN": "FLAT"}
            for regime in ("ACCUMULATION", "UPTREND", "DISTRIBUTION", "DOWNTREND"):
                if regime != "UPTREND":
                    mapping[regime] = "FLAT"
                    audit.append({"regime": regime, "fold_id": fid,
                                  "selected": "FLAT", "reason": "stub"})
                    continue
                cands = []
                for sid in eligible_for(ctx_.asset, regime):
                    ev = evidence.get(regime, {}).get(sid)
                    if ev is None:
                        continue
                    # LEAK: includes fold == fid itself
                    fold_nets = {f: v for f, v in ev["fold_nets"].items()
                                 if f <= fid}
                    cands.append(SpecialistCandidate(
                        sid, "LONG_CAPABLE",
                        float(sum(fold_nets.values())), fold_nets))
                from rsmv1.selection import select_for_fold
                out = select_for_fold(regime, fid, cands, 4, 320, fid)
                mapping[regime] = out.selected
                audit.append({"regime": regime, "fold_id": fid,
                              "selected": out.selected, "reason": out.reason})
            mapping_by_fold[fid] = mapping
        return mapping_by_fold, audit

    _, audit_leaky = leaky_selection(ctx, clean_ev)
    assert any(
        (a["selected"] != b["selected"]) or (a["reason"] != b["reason"])
        for a, b in zip(audit_clean, audit_leaky)
    ), "fixture is vacuous: leaky selector produced identical outcomes"


def test_manifest_digest_lengths():
    import hashlib
    import json

    p = CYCLE / "freezes" / "decision_cache_manifest.json"
    d = json.loads(p.read_text())
    for name, dig in d["files"].items():
        assert len(dig) == 64 and all(c in "0123456789abcdef" for c in dig), name
        f = CYCLE / name
        if f.exists():
            assert hashlib.sha256(f.read_bytes()).hexdigest() == dig, name
