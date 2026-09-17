#!/usr/bin/env python
"""FOREX-SEARCH-V1 S selection builder (lane fsearch-s, plan §5 as amended
by §3b — D2 SKIPPED, R0 NOT_RUN).

Mechanical, outcome-blind selection of the <=3 scored candidate cells.
NO return, PnL, PF, Sharpe, drawdown, expectancy or any other performance
statistic is computed anywhere in this module (plan §5 ban). The only
quantities produced are:

  * per-leg daily POSITION series in {-1, 0, +1} built from the D1
    manifest's frozen construction on the P0 master calendar, and
  * Pearson correlations OF POSITION SERIES (the P-20 books-distinct
    measurement), pooled across legs (gate) and per leg (disclosure).

Construction reuse: the state engines are IMPORTED READ-ONLY from the
frozen P0 census module (research/control/forex_search_v1_run/p0/
p0_census.py), so the position series are built by exactly the code that
produced the frozen fired census; this module additionally re-derives the
fired COUNTS from the position series and requires them to equal
p0/fired_census.json per fold (INPUT_MISMATCH abort otherwise).

Fail-closed laws honoured here:
  * every input hash is re-verified before use (FROZEN_SHA_MISMATCH abort)
  * complete-window states only (inherited from P0 engines)
  * force-flat at fold boundary (a position exists at decision bar m only
    if the leg's own execution bar t+1 lies in the same fold — identical
    to the census counting law)
  * an unmeasurable POOLED pairwise rho makes the slot NOT_ADJUDICABLE —
    the walk stops and reports; never an inferred PASS.

Modes:
  build       (default) run the walk and write selection_freeze.json
  --selfcheck re-run everything, verify all input hashes and reproduce the
              recorded walk byte-for-byte (deterministic fields); exit 0
              only on an exact match.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/forex-search-v1/integration")
RUN = WT / "research/control/forex_search_v1_run"
D1 = RUN / "d1"
P0 = RUN / "p0"
S = RUN / "s"

MANIFEST_EXPECTED_SHA256 = (
    "1b39aa6f726215df973833d1db5a8e3639aa226e62b7ce0f077c7e829c4d07b9")

# plan §5 P-20 threshold: pooled |rho| STRICTLY EXCEEDING 0.98 subsumes.
P20_THRESHOLD = 0.98
MAX_CELLS = 3
MAX_CELLS_PER_FAMILY = 2


class Stop(Exception):
    """Fail-closed stop with an incident code."""

    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sha256_obj(obj) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ------------------------------------------------------------------ inputs

def load_manifest() -> dict:
    path = D1 / "search_space_manifest.json"
    dig = sha256_file(path)
    if dig != MANIFEST_EXPECTED_SHA256:
        raise Stop("FROZEN_SHA_MISMATCH",
                   f"d1/search_space_manifest.json sha256 {dig} != frozen "
                   f"{MANIFEST_EXPECTED_SHA256}")
    m = json.loads(path.read_text())
    # self-hash convention (manifest field self_sha256_convention)
    probe = json.loads(path.read_text())
    probe["self_sha256"] = ""
    recomputed = hashlib.sha256(
        (json.dumps(probe, indent=1, sort_keys=True) + "\n").encode()).hexdigest()
    if recomputed != m["self_sha256"]:
        raise Stop("FROZEN_SHA_MISMATCH",
                   f"manifest self_sha256 recomputed {recomputed} != recorded "
                   f"{m['self_sha256']}")
    if m["schema"] != "search_space_manifest@1" or m["task_id"] != "fsearch-d1":
        raise Stop("INPUT_MISMATCH", "manifest schema/task_id unexpected")
    m["_file_sha256"] = dig
    return m


def load_p0() -> dict:
    arts = {}
    for name in ("fired_census.json", "calendar_census.json",
                 "structural_census.json", "folds_freeze.json",
                 "manifest_pin.json"):
        p = P0 / name
        arts[name] = {"sha256": sha256_file(p), "obj": json.loads(p.read_text())}
    # manifest-pinned census reference digests
    return arts


def verify_census_inputs(m: dict, arts: dict) -> dict:
    """INPUT_MISMATCH law: manifest census counts must equal
    p0/fired_census.json for all 33 configurations and all family totals;
    the frozen tier orders must be reproducible from those counts."""
    fired = arts["fired_census.json"]["obj"]
    per0 = fired["per_config"]
    if fired["config_count"] != 33:
        raise Stop("INPUT_MISMATCH", "p0 fired census config_count != 33")

    # (a) manifest per-config excerpt vs p0 census (fold counts, totals, legs)
    for c in m["configurations"]:
        cid = c["config_id"]
        ref = per0.get(cid)
        if ref is None:
            raise Stop("INPUT_MISMATCH", f"{cid} missing from p0 fired census")
        pc = c["p0_fired_census"]
        if pc["fired_by_fold"] != ref["fired_by_fold"] or \
                pc["fired_total"] != ref["fired_total"] or \
                pc["fired_by_leg"] != ref["fired_by_leg"]:
            raise Stop("INPUT_MISMATCH", f"{cid} census counts differ "
                                         f"manifest vs p0/fired_census.json")
        if pc["source_sha256"] != arts["fired_census.json"]["sha256"]:
            raise Stop("INPUT_MISMATCH",
                       f"{cid} source_sha256 != actual fired_census.json digest")
    if m["configurations"] != sorted(m["configurations"],
                                     key=lambda c: c["config_id"]):
        raise Stop("INPUT_MISMATCH", "manifest configurations not lexicographic")

    # (b) family totals over the most recent fold (fold 3)
    fam_sum = {}
    for cid, ref in per0.items():
        fam_sum.setdefault(ref["family"], 0)
        fam_sum[ref["family"]] += ref["fired_by_fold"]["3"]
    if fam_sum != m["selection_tier_s3b"]["family_fired_total_recent_fold"]:
        raise Stop("INPUT_MISMATCH",
                   f"family fold-3 sums {fam_sum} != manifest "
                   f"{m['selection_tier_s3b']['family_fired_total_recent_fold']}")

    # (c) tier (i): descending family fold-3 census, ties lexicographic
    tier_i = [f for f, _ in sorted(fam_sum.items(), key=lambda kv: (-kv[1], kv[0]))]
    if tier_i != m["selection_tier_s3b"]["family_ranking_tier_i_descending"]:
        raise Stop("INPUT_MISMATCH", f"tier (i) order {tier_i} != frozen manifest")

    # (d) tier (ii): within family, descending fold-3 config census,
    #     tie-break lexicographic config ID
    tier_ii_recomputed = {}
    for fam in tier_i:
        ids = [cid for cid, ref in per0.items() if ref["family"] == fam]
        order = sorted(ids, key=lambda cid: (-per0[cid]["fired_by_fold"]["3"], cid))
        tier_ii_recomputed[fam] = order
    if tier_ii_recomputed != m["selection_tier_s3b"]["config_order_within_family_tier_ii"]:
        raise Stop("INPUT_MISMATCH", "tier (ii) order != frozen manifest")
    return {"tier_i": tier_i, "tier_ii": tier_ii_recomputed,
            "family_fold3_sums": fam_sum}


def load_legs_and_calendar(m: dict, arts: dict) -> dict:
    sys.path.insert(0, str(P0))
    import p0_census  # read-only reuse of the frozen P0 machinery

    pin = arts["manifest_pin.json"]["obj"]
    legs = {}
    for legname in p0_census.LEGS:
        archive, member, expect = p0_census.PAIR_SOURCES[legname]
        path = p0_census.STAGING / member
        if not path.exists():
            raise Stop("INPUT_MISMATCH",
                       f"staging member missing: {path} (extract the pinned "
                       f"P-13 archives first)")
        dig = sha256_file(path)
        pinpair = pin["pairs"][legname]
        if dig != expect or pinpair["sha256"] != expect or \
                not pinpair["matches_plan_frozen_digest"]:
            raise Stop("INPUT_MISMATCH",
                       f"{legname} staging digest {dig} != pinned {expect}")
        legs[legname] = p0_census.load_leg(path)
        legs[legname]["source_archive"] = archive
        legs[legname]["source_member"] = member

    # master calendar must reproduce the frozen census byte-for-byte
    cal = p0_census.calendar_census(legs)
    master = cal["master_calendar"]
    master_sha = p0_census.sha256_obj(master)
    cal_ref = arts["calendar_census.json"]["obj"]
    if master_sha != cal_ref["master_calendar_sha256"]:
        raise Stop("INPUT_MISMATCH",
                   f"master calendar sha {master_sha} != frozen "
                   f"{cal_ref['master_calendar_sha256']}")
    folds = p0_census.make_folds(master)
    folds_ref = arts["folds_freeze.json"]["obj"]
    if folds["master_dates_sha256"] != folds_ref["master_dates_sha256"] or \
            folds["boundaries_index"] != folds_ref["boundaries_index"]:
        raise Stop("INPUT_MISMATCH", "fold freeze mismatch vs p0/folds_freeze.json")
    return {"p0_census": p0_census, "legs": legs, "master": master,
            "folds": folds, "cal": cal}


# --------------------------------------------------------------- positions

class PositionBuilder:
    """Per-leg daily position series in {-1, 0, +1} on the master calendar.

    position[leg][m] = +1/-1 iff the config's state fires on decision bar m
    AND the leg's own execution bar t+1 exists in the SAME fold (the census
    force-flat law); 0 otherwise. Decision-bar attribution identical to the
    fired census (OPEN-GAP's declared §4 F3 timing exception included).
    """

    def __init__(self, ctx: dict, m: dict):
        self.pc = ctx["p0_census"]
        self.legs = ctx["legs"]
        self.master = ctx["master"]
        self.folds = ctx["folds"]
        self.manifest = m
        self.own_index = {k: {d: i for i, d in enumerate(v["dates"])}
                          for k, v in self.legs.items()}
        self.next_own = {k: {v["dates"][i]: v["dates"][i + 1]
                             for i in range(len(v["dates"]) - 1)}
                         for k, v in self.legs.items()}
        self.fold_id = [self.pc.fold_of(self.folds, mi)
                        for mi in range(len(self.master))]
        self._cache: dict[str, dict] = {}

    def _bisect_master(self, d: str):
        import bisect
        i = bisect.bisect_left(self.master, d)
        return None if i >= len(self.master) else i

    def build(self, config_id: str) -> dict:
        if config_id in self._cache:
            return self._cache[config_id]
        cfg = next((c for c in self.manifest["configurations"]
                    if c["config_id"] == config_id), None)
        if cfg is None:
            raise Stop("INPUT_MISMATCH", f"config {config_id} not in manifest")
        # engine-facing shape: p0_census.compute_state expects the
        # enumerate_configs layout (params at top level); the D1 manifest
        # nests them under "parameters" (keys verified identical per family).
        engine_cfg = {"config_id": cfg["config_id"], "family": cfg["family"],
                      **cfg["parameters"]}
        legs_order = self.manifest["universe"]["legs"]
        pos = {legname: np.zeros(len(self.master), dtype=np.int8)
               for legname in legs_order}
        for legname in legs_order:
            leg = self.legs[legname]
            own_map = self.own_index[legname]
            own_of_master = [own_map[d] for d in self.master]
            state = self.pc.compute_state(engine_cfg, leg, own_of_master, self.master)
            for mi, direction in state.items():
                d_t = self.master[mi]
                nxt = self.next_own[legname].get(d_t)
                if nxt is None:
                    continue
                mi_next = self._bisect_master(nxt)
                if mi_next is None:
                    continue
                if self.fold_id[mi_next] != self.fold_id[mi]:
                    continue  # force-flat at fold boundary
                pos[legname][mi] = 1 if direction == "LONG" else -1
        entry = {"positions": pos, "config": cfg}
        entry["positions_digest"] = sha256_obj(
            {k: [int(x) for x in pos[k]] for k in legs_order})
        self._verify_census_rebuild(cfg, pos)
        self._cache[config_id] = entry
        return entry

    def _verify_census_rebuild(self, cfg: dict, pos: dict) -> None:
        """Rebuilt fold counts from the position series MUST equal the
        frozen p0 fired census (construction-fidelity check)."""
        b = self.folds["boundaries_index"]
        rebuilt = {"1": 0, "2": 0, "3": 0}
        for legname, series in pos.items():
            for mi in np.nonzero(series)[0]:
                f = self.fold_id[int(mi)]  # already 1-based (p0_census.fold_of)
                rebuilt[str(f)] += 1
        fired = json.loads((P0 / "fired_census.json").read_text())
        expect = fired["per_config"][cfg["config_id"]]["fired_by_fold"]
        if rebuilt != expect:
            raise Stop("INPUT_MISMATCH",
                       f"position-series rebuild of {cfg['config_id']} fold "
                       f"counts {rebuilt} != frozen census {expect}")

    def pooled(self, config_id: str) -> np.ndarray:
        legs_order = self.manifest["universe"]["legs"]
        entry = self.build(config_id)
        return np.concatenate([entry["positions"][k] for k in legs_order])


def pearson(a: np.ndarray, b: np.ndarray):
    """Pearson rho; ('UNMEASURABLE', reason) when either side is constant."""
    a = a.astype(np.float64)
    b = b.astype(np.float64)
    if float(np.std(a)) == 0.0 or float(np.std(b)) == 0.0:
        return None, "UNMEASURABLE_ZERO_VARIANCE_POSITION_SERIES"
    cov = float(np.mean((a - a.mean()) * (b - b.mean())))
    rho = cov / (float(np.std(a)) * float(np.std(b)))
    return rho, "OK"


def measure(builder: PositionBuilder, cand: str, selected: list,
            legs_order: list) -> dict:
    """P-20 measurement of candidate vs every already-selected arm.
    POOLED rho gates; per-leg rhos are disclosure only (non-gating)."""
    pooled_c = builder.pooled(cand)
    vs = []
    verdict = "SELECTED"
    reason = "no higher-ranked selected candidate" if not selected else \
        "all pooled |rho| <= 0.98 vs every already-selected arm"
    for sel in selected:
        rho, status = pearson(pooled_c, builder.pooled(sel))
        if status != "OK":
            raise Stop("NOT_ADJUDICABLE",
                       f"unmeasurable POOLED rho {cand} vs {sel}: {status} "
                       f"(fail-closed; never an inferred PASS)")
        if abs(rho) > P20_THRESHOLD:
            verdict, reason = "SELF_SUBSUMED", (
                f"pooled |rho|={abs(rho):.6f} > 0.98 vs {sel}")
        legs = {}
        for legname in legs_order:
            r_l, st_l = pearson(builder.build(cand)["positions"][legname],
                                builder.build(sel)["positions"][legname])
            legs[legname] = (None if st_l != "OK" else round(r_l, 12))
        vs.append({"vs_selected": sel, "pooled_rho": round(rho, 12),
                   "pooled_abs_rho": round(abs(rho), 12),
                   "per_leg_rho_disclosure_only": legs,
                   "threshold": P20_THRESHOLD,
                   "subsuming": bool(abs(rho) > P20_THRESHOLD)})
    return {"p20_vs_selected": vs, "verdict": verdict, "reason": reason}


# ------------------------------------------------------------------- walk

def run_walk(m: dict, builder: PositionBuilder, tiers: dict) -> dict:
    tier_i = tiers["tier_i"]
    tier_ii = tiers["tier_ii"]
    legs_order = m["universe"]["legs"]
    selected: list[str] = []
    visits: list[dict] = []
    order = 0
    round_no = 0
    while len(selected) < MAX_CELLS:
        progressed = False
        for fam in tier_i:
            if len(selected) >= MAX_CELLS:
                break
            if sum(1 for s in selected if s.startswith(f"FSS-{fam}-")) >= MAX_CELLS_PER_FAMILY:
                continue
            if round_no >= len(tier_ii[fam]):
                continue
            cand = tier_ii[fam][round_no]
            order += 1
            progressed = True
            meas = measure(builder, cand, selected, legs_order)
            entry = builder.build(cand)
            visit = {
                "visit_order": order, "round": round_no + 1, "family": fam,
                "config_id": cand,
                "p0_fired_census_fold3": entry["config"]["p0_fired_census"]["fired_by_fold"]["3"],
                "positions_digest": entry["positions_digest"],
                **meas,
            }
            visits.append(visit)
            if meas["verdict"] == "SELECTED":
                selected.append(cand)
        if not progressed:
            break
        round_no += 1
    return {"visits": visits, "selected_order": selected,
            "rounds_executed": round_no,
            "cells_filled": len(selected),
            "budget": {"max_cells": MAX_CELLS,
                       "max_cells_per_family": MAX_CELLS_PER_FAMILY},
            "walk_reading": "rigid round-robin grid: round r visits config "
                            "index r of each family in tier-(i) order, "
                            "skipping families already holding 2 selected "
                            "cells; a SELF_SUBSUMED visit consumes that "
                            "family's slot for the round (one configuration "
                            "per family per round)"}


# ------------------------------------------------------------------ freeze

def arm_identity(m: dict, entry: dict, ctx: dict) -> str:
    cfg = {k: v for k, v in entry["config"].items()}
    return sha256_obj({
        "schema": "fsearch_s_arm_identity@1",
        "cycle": m["cycle_id"],
        "config_excerpt": cfg,
        "universe_legs_order": m["universe"]["legs"],
        "holds_law": m["holds_law"],
        "clock_contract": m["clock_contract"],
        "warmup_rule": m["warmup_rule"],
        "master_dates_sha256": ctx["folds"]["master_dates_sha256"],
        "fold_boundaries_index": ctx["folds"]["boundaries_index"],
        "search_space_manifest_sha256": m["_file_sha256"],
        "positions_digest": entry["positions_digest"],
    })


def build_freeze(m: dict, arts: dict, tiers: dict, ctx: dict,
                 walk: dict, builder: PositionBuilder) -> dict:
    pin = arts["manifest_pin.json"]["obj"]
    folds_ref = arts["folds_freeze.json"]["obj"]
    selections = []
    for config_id in walk["selected_order"]:
        entry = builder.build(config_id)
        selections.append({
            "rank": len(selections) + 1,
            "config_id": config_id,
            "family": entry["config"]["family"],
            "config_manifest_excerpt_verbatim": entry["config"],
            "arm_identity_hash": arm_identity(m, entry, ctx),
            "positions_digest": entry["positions_digest"],
            "data_manifest": {
                "source_law": "TD 1day OHLC spot majors, single P-13 vintage; "
                              "archive digests re-verified this lane",
                "pairs": pin["pairs"],
                "ng1_copies_byte_identical": pin["ng1_copies_byte_identical"],
                "excluded": pin["excluded"],
                "master_calendar_sha256": ctx["cal"] and
                arts["calendar_census.json"]["obj"]["master_calendar_sha256"],
            },
        })
    # selected-pair P-20 matrix (pooled gate + per-leg disclosure)
    legs_order = m["universe"]["legs"]
    matrix = []
    for i, a in enumerate(walk["selected_order"]):
        for b in walk["selected_order"][i + 1:]:
            rho, status = pearson(builder.pooled(a), builder.pooled(b))
            legs = {ln: round(float(np.corrcoef(
                builder.build(a)["positions"][ln].astype(np.float64),
                builder.build(b)["positions"][ln].astype(np.float64))[0, 1]), 12)
                for ln in legs_order}
            matrix.append({"arm_a": a, "arm_b": b,
                           "pooled_abs_rho": round(abs(rho), 12),
                           "pooled_rho": round(rho, 12),
                           "per_leg_rho_disclosure_only": legs,
                           "books_distinct": bool(abs(rho) <= P20_THRESHOLD)})
    return {
        "schema": "selection_freeze@1",
        "task_id": "fsearch-s",
        "cycle_id": m["cycle_id"],
        "orchestration_cycle": m["orchestration_cycle"],
        "role": "quant-implementer",
        "lane": "fsearch-s",
        "branch": "orca/forex-search-v1-integration",
        "worktree": str(WT),
        "base_sha": "69af24359b8affa064d57f4762a615afdd7a77d3",
        "phase": "S (scored-cell selection freeze, plan §5 as amended by §3b)",
        "outcome_blindness_declaration": (
            "OUTCOME-BLIND artifact: no return, PnL, PF, Sharpe, drawdown, "
            "expectancy or any other performance statistic is computed or "
            "recorded for ANY configuration anywhere in this lane (plan §5 "
            "ban). Quantities produced: P0 census COUNTS, per-leg daily "
            "position series in {-1,0,+1} from the frozen construction, and "
            "Pearson correlations OF POSITION SERIES (P-20). The VOL-DRIFT "
            "state engine consumes a realized-vol state variable per the "
            "frozen §5 construction (pinned estimator); it is a state "
            "input, never a strategy performance statistic. D2 is SKIPPED "
            "per owner amendment §3b: the R0 ancestry battery is NOT_RUN "
            "(never an inferred PASS) and no ancestry rho machinery was "
            "run or added in this lane."),
        "disclosures": {
            "D2": "SKIPPED per owner amendment §3b (verbatim intent: 'chay "
                  "tu dau toi GO cua toi, nhung khong chay buoc D2')",
            "R0_ancestry": "NOT_RUN (D2 skipped) — terminal names carry "
                           "R0_NOT_RUN with the standing 0.20 / relaxed 0.30 "
                           "floor disclosure",
            "PBO": "NOT_RUN fail-closed by construction (<=3 scored cells; "
                   "CSCV PBO needs >= 8 performance-evaluated configs)",
        },
        "inputs": {
            "search_space_manifest": {
                "path": "research/control/forex_search_v1_run/d1/"
                        "search_space_manifest.json",
                "sha256": m["_file_sha256"],
                "self_sha256": m["self_sha256"],
                "frozen_at_commit": "69af24359b8affa064d57f4762a615afdd7a77d3"},
            "p0_artifacts": {k: {"path": f"research/control/forex_search_v1_run/p0/{k}",
                                 "sha256": v["sha256"]}
                             for k, v in arts.items()},
            "staging_members_sha256_verified": {
                ln: pin["pairs"][ln]["sha256"] for ln in m["universe"]["legs"]},
            "master_calendar": {
                "len": len(ctx["master"]),
                "first": ctx["master"][0], "last": ctx["master"][-1],
                "sha256": ctx["folds"]["master_dates_sha256"]},
            "fold_digest": {
                "folds_freeze_sha256": arts["folds_freeze.json"]["sha256"],
                "master_dates_sha256": folds_ref["master_dates_sha256"],
                "boundaries_index": folds_ref["boundaries_index"],
                "folds": folds_ref["folds"]},
        },
        "selection_rule_frozen_verbatim": {
            "tier_i": m["selection_tier_s3b"]["family_ranking_tier_i_descending"],
            "tier_ii": m["selection_tier_s3b"]["config_order_within_family_tier_ii"],
            "family_fired_total_recent_fold":
                m["selection_tier_s3b"]["family_fired_total_recent_fold"],
            "recent_fold": m["selection_tier_s3b"]["recent_fold"],
            "procedure": m["selection_tier_s3b"]["selection_procedure_tier_iii"],
            "tie_rules": m["selection_tier_s3b"]["tie_rules"],
            "amendment": m["selection_tier_s3b"]["amendment"],
            "tier_recomputation_verified": tiers,
            "p20": {"gate": "pooled |rho| > 0.98 vs any higher-ranked "
                            "already-selected arm => SELF_SUBSUMED",
                    "pooling": "concatenation of the five per-leg position "
                               "series in manifest universe.legs order "
                               "(EURUSD, GBPUSD, USDCAD, AUDUSD, NZDUSD) — "
                               "the census pooling convention",
                    "per_leg_rho": "disclosure only, non-gating",
                    "unmeasurable": "NOT_ADJUDICABLE fail-closed stop"},
        },
        "walk": walk,
        "p20_matrix_selected": matrix,
        "selections": selections,
        "tool": {"python": sys.version.split()[0], "numpy": np.__version__,
                 "builder": "research/control/forex_search_v1_run/s/s_select.py",
                 "construction_reuse": "state engines imported read-only from "
                                       "p0/p0_census.py (the code that produced "
                                       "the frozen census); rebuilt fold counts "
                                       "required equal p0/fired_census.json for "
                                       "every visited configuration"},
        "determinism": "pure function of the pinned staging bytes + frozen "
                       "manifests; --selfcheck reproduces the walk exactly",
        "measured_frozen_utc": now_iso(),
    }


# -------------------------------------------------------------------- main

def run(selfcheck: bool) -> int:
    freeze_path = S / "selection_freeze.json"
    m = load_manifest()
    arts = load_p0()
    tiers = verify_census_inputs(m, arts)
    ctx = load_legs_and_calendar(m, arts)
    builder = PositionBuilder(ctx, m)
    walk = run_walk(m, builder, tiers)
    freeze = build_freeze(m, arts, tiers, ctx, walk, builder)

    if not selfcheck:
        S.mkdir(parents=True, exist_ok=True)
        freeze_path.write_text(json.dumps(freeze, indent=1, sort_keys=True) + "\n")
        print(f"[s] cells filled: {walk['cells_filled']}")
        for s_ in freeze["selections"]:
            print(f"[s] selected #{s_['rank']}: {s_['config_id']} "
                  f"({s_['family']}) arm={s_['arm_identity_hash'][:16]}")
        for v in walk["visits"]:
            print(f"[s] visit {v['visit_order']}: {v['config_id']} -> "
                  f"{v['verdict']} ({v['reason']})")
        print(f"[s] wrote {freeze_path}")
        return 0

    # selfcheck: byte-exact reproduction of the deterministic fields
    if not freeze_path.exists():
        print("[s] FATAL: no freeze file to selfcheck", flush=True)
        return 1
    rec = json.loads(freeze_path.read_text())
    def strip(o):
        if isinstance(o, dict):
            return {k: strip(v) for k, v in o.items()
                    if k not in ("measured_frozen_utc",)}
        if isinstance(o, list):
            return [strip(x) for x in o]
        return o
    if strip(freeze) == strip(rec):
        print("[s] selfcheck OK: hashes verified; walk reproduced exactly; "
              f"{walk['cells_filled']} cells; selections "
              f"{walk['selected_order']}", flush=True)
        return 0
    print("[s] FATAL: reproduced walk differs from recorded freeze", flush=True)
    a = strip(freeze)
    b = strip(rec)
    for k in sorted(set(a) | set(b)):
        if a.get(k) != b.get(k):
            print(f"[s] differs at key {k!r}", flush=True)
    return 1


def main() -> int:
    try:
        return run("--selfcheck" in sys.argv)
    except Stop as e:
        print(f"[s] STOP {e.code}: {e.detail}", flush=True)
        # fail-closed: record the stop in the freeze location if writable
        try:
            S.mkdir(parents=True, exist_ok=True)
            (S / "selection_freeze_STOP.json").write_text(json.dumps({
                "schema": "selection_freeze_STOP@1", "task_id": "fsearch-s",
                "incident": e.code, "detail": e.detail,
                "measured_utc": now_iso()}, indent=1, sort_keys=True) + "\n")
        except OSError:
            pass
        return 2


if __name__ == "__main__":
    sys.exit(main())
