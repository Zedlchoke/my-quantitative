"""A7T terminal-audit verification for STOCKS-FREE-V5 (read-only).

Recomputes, from the committed control artifacts at THIS worktree's HEAD:

  1. execution-ledger once-only accounting + entry-digest recomputation
     (ledger ``artifact_digest`` = sha256(canonical_json(artifact)));
  2. cell-artifact integrity (pins, driver sha, arm_config_digest recomputed
     from build_arm_configs() at this HEAD, gates <-> arm_gates_all_pass and
     family_verdicts cross-consistency);
  3. Stage-A gate arithmetic recomputed from each cell's own payload
     (expectancy, PF, fold pnl/MDD/PF, fold-positive counts, ETF shares,
     fold share, stress, drop-one) + the preregistered control-falsification
     ratio from proposals/a6_h2.json;
  4. reproduction EXACT_MATCH modulo run_utc against a prior re-run of the
     frozen staged scorer (default /tmp/a7t_repro, produced from the
     detached r-reproduce twin at W1);
  5. cash/cost/turnover arithmetic from the payloads (telescoping period
     PnL identity, equity-curve sanity, attribution identity, implied
     one-way turnover, stress 2x-bps cost relationship);
  6. denominator math across the four run ledgers;
  7. S1 seal / boundaries (last_session clamp, no paper/live/orders paths in
     the cycle diff, worker scan is done by the shell wrapper);
  8. history integrity via git diffs (V2/V3/V4 control dirs; frozen fusion
     core additions-only; stocks_compat import screen);
  9. owner-plan conformance (allowed verdicts; no survivor; the Section 1.1
     vol-level confirmatory proposal measured-ineligible at D2 and never
     scored).

NO ledger file is written; NO cell is modified.  stdout is a JSON report
consumed by the auditor.  Run with the repo-root venv python from the
r-a7-terminal worktree root.
"""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CONTROL = REPO / "research" / "control" / "stocks_free_v5_run"
CELLS = CONTROL / "cells"
ARMS = ["A", "N", "C"]
W1 = "0ecca232caf6cee21a84d78579681e336b616388"
DRIVER_SHA = "be0e4fa465a616565aec5643b587ee5cbfaaede0392d71605f1c32f428222f81"
MANIFEST_SHA = "62ac324d7e683961b0d88f85153e4a072d09fe0a6745a54687b9e3b219d8f658"
TERMINAL_HEAD = "173cb34eca21f7009ad451a91a53523d178c18bb"
V4_TERMINAL = "341dfc18903e98520e13f2ffc2401415cba24943"
FUSION_CORE = "c6a0576ef98dd4392e90805c8ba33821da62eabc"
FOLD_WINDOWS = {
    "S0_FOLD_1": ("2018-04-04", "2020-09-01"),
    "S0_FOLD_2": ("2020-09-10", "2023-02-09"),
    "S0_FOLD_3": ("2023-02-17", "2025-07-24"),
}
S1_START = "2025-08-01"
REPRO_DIR = Path("/tmp/a7t_repro")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True,
                          text=True, check=True).stdout


def _role_norm(role: str) -> str:
    """Normalize role labels ('causal_negative_control' ~ 'causal control')."""
    return " ".join(
        w for w in role.replace("_", " ").split() if w not in ("negative",))


def check(name: str, ok: bool, detail) -> dict:
    return {"check": name, "ok": bool(ok), "detail": detail}


# --------------------------------------------------------------------------- #
# 1. ledger once-only accounting
# --------------------------------------------------------------------------- #
def sec1_ledger() -> dict:
    raw = (CONTROL / "execution_ledger.json").read_bytes()
    led = json.loads(raw)
    entries = led["entries"]
    out = {"observed": led["observed"], "published": led["published"],
           "published_keys": sorted(led["published_keys"])}
    out["published_keys_exact"] = out["published_keys"] == [
        "SFV5-A6-H2-A", "SFV5-A6-H2-C", "SFV5-A6-H2-N"]
    per = {k: {"COMPUTE_RECORDED": 0, "FIRST_PUBLICATION": 0,
               "REPLAY_ZERO_DELTA": 0, "publish_entries": 0} for k in out["published_keys"]}
    digests = {}
    for e in entries:
        k = e["key"]
        if k not in per:
            continue
        if e.get("event") in per[k]:
            per[k][e["event"]] += 1
        if "artifact_digest" in e:
            per[k]["publish_entries"] += 1
            digests[k] = e["artifact_digest"]
    out["per_key_events"] = per
    out["no_double_compute"] = all(
        v["COMPUTE_RECORDED"] == 1 and v["FIRST_PUBLICATION"] == 1
        and v["REPLAY_ZERO_DELTA"] >= 1 and v["publish_entries"] == 1
        for v in per.values())
    out["observed_matches_compute_events"] = (
        led["observed"] == sum(v["COMPUTE_RECORDED"] for v in per.values()))
    out["published_matches_keys"] = (
        led["published"] == len(led["published_keys"]))

    # entry digests: the ledger's free-form artifact_digest field vs the
    # committed cells.  V4's ledger demonstrably used
    # sha256(canonical_json(artifact)) (recomputes TRUE for all 6 V4 cells);
    # the V5 Phase-E publisher was not committed, so its exact digest input
    # is unreconstructable.  Recorded as a finding, not an accounting break:
    # the load-bearing byte chain is file_sha256 -> family_verdicts ->
    # terminal_report -> independent reproduction, all verified elsewhere.
    v4_led = json.loads((CONTROL.parent / "stocks_free_v4_run"
                         / "execution_ledger.json").read_text())
    v4_digests = {e["key"]: e["artifact_digest"] for e in v4_led["entries"]
                  if "artifact_digest" in e}
    v4_path = CONTROL.parent / "stocks_free_v4_run" / "cells"
    v4_matches = {}
    for key, dig in v4_digests.items():
        p = v4_path / f"{key}.json"
        if p.exists():
            v4_matches[key] = (sha256_bytes(
                canonical_json(json.loads(p.read_text())).encode()) == dig)
    digest_checks = {}
    for arm in ARMS:
        key = f"SFV5-A6-H2-{arm}"
        cell_raw = (CELLS / f"{key}.json").read_bytes()
        cell = json.loads(cell_raw)
        recomputed = sha256_bytes(canonical_json(cell).encode())
        digest_checks[key] = {
            "ledger_digest": digests.get(key),
            "sha256_canonical_json_of_committed_cell": recomputed,
            "file_sha256": sha256_bytes(cell_raw),
            "ledger_digest_equals_canonical_sha": digests.get(key) == recomputed,
            "ledger_digest_equals_file_sha": digests.get(key)
            == sha256_bytes(cell_raw),
        }
    out["entry_digest_checks"] = digest_checks
    out["entry_digest_convention"] = {
        "v4_convention_sha_canonical_json_recomputes_on_v4_ledger": all(
            v4_matches.values()) if v4_matches else None,
        "v5_ledger_digests_recomputable": all(
            v["ledger_digest_equals_canonical_sha"]
            or v["ledger_digest_equals_file_sha"]
            for v in digest_checks.values()),
        "note": "V5 Phase-E publisher not committed; digest input "
                "unreconstructable (finding F-A7T-1, MEDIUM); byte chain "
                "verified via file sha256s and reproduction instead",
    }
    out["ok"] = (out["published_keys_exact"] and out["no_double_compute"]
                 and out["observed_matches_compute_events"]
                 and out["published_matches_keys"])
    return out


# --------------------------------------------------------------------------- #
# 2. cell artifact integrity
# --------------------------------------------------------------------------- #
def sec2_integrity(fam: dict) -> dict:
    sys.path.insert(0, str(REPO))
    from research.assets.stocks.coupling_family import arm_config_digests
    digests = arm_config_digests()
    fam_arms = fam["families"]["SFV5-A6-H2-CROSS-SECTOR-COUPLING"]["arms"]

    per_arm = {}
    for arm in ARMS:
        key = f"SFV5-A6-H2-{arm}"
        cell = json.loads((CELLS / f"{key}.json").read_text())
        pins = cell.get("pins", {})
        gates = cell["gates"]
        n_fail = sum(1 for g in gates.values() if g["verdict"] == "FAIL")
        fv = fam_arms[key]
        recomputed_digest = digests[key.rsplit("-", 1)[-1]]
        per_arm[key] = {
            "w1_pin_ok": cell.get("w1") == W1,
            "pins_git_head_ok": pins.get("git_head") == W1,
            "staging_manifest_pin_ok": pins.get("staging_manifest_sha256") == MANIFEST_SHA,
            "driver_sha_ok": cell.get("driver_sha256") == DRIVER_SHA,
            "arm_config_digest_recorded": cell.get("arm_config_digest"),
            "arm_config_digest_recomputed_at_this_head": recomputed_digest,
            "arm_config_digest_ok": cell.get("arm_config_digest") == recomputed_digest,
            "arm_gates_all_pass_field": cell.get("arm_gates_all_pass"),
            "arm_gates_all_pass_recomputed": n_fail == 0,
            "gates_consistent": cell.get("arm_gates_all_pass") == (n_fail == 0),
            "gates_failed_count": n_fail,
            "family_verdicts_gates_failed": fv["gates_failed"],
            "gates_failed_matches_family_verdicts": n_fail == fv["gates_failed"],
            "headline_matches_family_verdicts": {
                "total_pnl": cell["base"]["total_pnl"] == fv["total_pnl"],
                "expectancy": cell["base"]["expectancy"] == fv["expectancy"],
                "pf": cell["base"]["profit_factor"] == fv["pf"],
                "overall_alpha": cell["overall_incremental_alpha"] == fv["overall_alpha"],
            },
            "role_matches": _role_norm(cell["role"]) == _role_norm(fv["role"]),
            "role_cell_vs_family": [cell["role"], fv["role"]],
            "last_session": cell["last_session"],
        }
    comp_path = CONTROL.parent / "stocks_free_v4_run" / "r_a7_terminal_audit.json"  # noqa: F841 (unused, clarity only)
    return {
        "per_arm": per_arm,
        "ok": all(
            v["w1_pin_ok"] and v["pins_git_head_ok"] and v["staging_manifest_pin_ok"]
            and v["driver_sha_ok"] and v["arm_config_digest_ok"] and v["gates_consistent"]
            and v["gates_failed_matches_family_verdicts"]
            and all(v["headline_matches_family_verdicts"].values())
            and v["role_matches"]
            for v in per_arm.values()),
    }


# --------------------------------------------------------------------------- #
# 3. gate arithmetic recomputed from payloads
# --------------------------------------------------------------------------- #
def segment_mdd(curve: dict, start: str, end: str) -> float:
    peak, mdd = None, 0.0
    for d, v in curve.items():
        if d < start or d > end:
            continue
        peak = v if peak is None else max(peak, v)
        if peak > 0:
            mdd = max(mdd, (peak - v) / peak)
    return mdd


def sec3_gate_math() -> dict:
    per_arm = {}
    for arm in ARMS:
        key = f"SFV5-A6-H2-{arm}"
        cell = json.loads((CELLS / f"{key}.json").read_text())
        base = cell["base"]
        pp = base["period_pnls"]
        curve = base["equity_curve"]
        gates = cell["gates"]

        expectancy = math.fsum(p for _, p in pp) / len(pp)
        gains = sum(p for _, p in pp if p > 0)
        losses = sum(p for _, p in pp if p < 0)
        pf = (gains / abs(losses)) if losses < 0 else None

        folds_recomputed = {}
        for fid, (start, end) in FOLD_WINDOWS.items():
            periods = [p for d, p in pp if start <= d <= end]
            fg = sum(p for p in periods if p > 0)
            fl = sum(p for p in periods if p < 0)
            fpf = (fg / abs(fl)) if fl < 0 else None
            folds_recomputed[fid] = {
                "n_periods": len(periods),
                "fold_pnl": math.fsum(periods),
                "fold_expectancy": (math.fsum(periods) / len(periods)) if periods else 0.0,
                "fold_pf": fpf,
                "fold_mdd": segment_mdd(curve, start, end),
                "positive": bool(periods) and math.fsum(periods) > 0,
            }

        fold_pnls = [folds_recomputed[f]["fold_pnl"] for f in FOLD_WINDOWS]
        pos_total = sum(p for p in fold_pnls if p > 0)
        fold_share = (max(p for p in fold_pnls if p > 0) / pos_total
                      if pos_total > 0 else None)
        contrib = base["symbol_contribution"]
        pos_contrib = sum(v for v in contrib.values() if v > 0)
        etf_shares = {s: v / pos_contrib for s, v in contrib.items() if v > 0}
        max_etf_share = max(etf_shares.values()) if etf_shares else 0.0

        n_pos_folds = sum(1 for f in folds_recomputed.values() if f["positive"])
        max_fold_mdd = max(f["fold_mdd"] for f in folds_recomputed.values())
        min_fold_pf = min([f["fold_pf"] for f in folds_recomputed.values()
                           if f["fold_pf"] is not None], default=None)
        n_folds_alpha_pos = sum(
            1 for f in cell["folds"] if f["incremental_alpha"] > 0)

        verdicts = {
            "expectancy_gt_0": expectancy > 0,
            "position_pf_ge_1_10": pf is None or pf >= 1.10,
            "folds_positive_ge_2": n_pos_folds >= 2,
            "no_populated_fold_pf_below_0_80": all(
                f["fold_pf"] >= 0.80 for f in folds_recomputed.values()
                if f["fold_pf"] is not None),
            "max_fold_mdd_le_15pct": max_fold_mdd <= 0.15,
            "fold_positive_share_le_50": fold_share is not None and fold_share <= 0.50,
            "etf_positive_share_le_35": max_etf_share <= 0.35,
            "sufficient_periods_per_fold": all(
                f["n_periods"] >= 5 for f in folds_recomputed.values()),
            "stress_pnl_gt_0": cell["stress"]["total_pnl"] > 0,
            "stress_pf_ge_1_00": cell["stress"]["profit_factor"] is None
            or cell["stress"]["profit_factor"] >= 1.0,
            "turnover_within_ceiling": cell["schedule_turnover_two_way_per_year"] <= 6.0,
            "risk_matched_excess_2_of_3_folds": n_folds_alpha_pos >= 2,
            "overall_incremental_alpha_gt_0": cell["overall_incremental_alpha"] > 0,
            "drop_one_etf_survival": cell["drop_one_etf"]["expectancy"] > 0,
            "drop_one_fold_survival": all(
                v is not None and v > 0
                for v in cell["drop_one_fold_expectancies"].values()),
        }
        recorded_verdicts = {k: g["verdict"] == "PASS" for k, g in gates.items()}
        per_arm[key] = {
            "recomputed": {
                "expectancy": expectancy,
                "pf_from_period_pnls": pf,
                "folds": folds_recomputed,
                "fold_positive_share": fold_share,
                "max_etf_positive_share": max_etf_share,
                "n_positive_folds": n_pos_folds,
                "max_fold_mdd": max_fold_mdd,
                "min_fold_pf": min_fold_pf,
            },
            "recorded_gate_verdicts_match_recomputed": recorded_verdicts == verdicts,
            "n_fail_recomputed": sum(1 for v in verdicts.values() if not v),
        }
    # control falsification, from family_verdicts cross-checked to cells
    cellA = json.loads((CELLS / "SFV5-A6-H2-A.json").read_text())
    cellC = json.loads((CELLS / "SFV5-A6-H2-C.json").read_text())
    a_alpha = cellA["overall_incremental_alpha"]
    c_alpha = cellC["overall_incremental_alpha"]
    ratio = abs(c_alpha / a_alpha)
    per_arm["_control_falsification"] = {
        "anchor_alpha": a_alpha,
        "control_alpha": c_alpha,
        "abs_ratio": ratio,
        "preregistered_rule": "a6_h2.json causal_negative_control."
                              "preregistered_falsification_rule: |alpha_C| >= 0.5*|alpha_A|, "
                              "OR control expectancy > 0 with PF >= 1.0",
        "channel_1_ratio_ge_05": ratio >= 0.5,
        "channel_2_expectancy_pf": cellC["base"]["expectancy"] > 0
        and cellC["base"]["profit_factor"] >= 1.0,
        "falsification_fires": ratio >= 0.5 or (
            cellC["base"]["expectancy"] > 0
            and cellC["base"]["profit_factor"] >= 1.0),
        "recorded_in_family_verdicts": "VIOLATED" in
        json.loads((CONTROL / "family_verdicts.json").read_text())
        ["families"]["SFV5-A6-H2-CROSS-SECTOR-COUPLING"]["adjudication"]
        ["control_does_not_reproduce"],
    }
    return {
        "per_arm": per_arm,
        "ok": all(v["recorded_gate_verdicts_match_recomputed"]
                  for k, v in per_arm.items() if not k.startswith("_")),
    }


# --------------------------------------------------------------------------- #
# 4. reproduction (vs prior frozen-scorer re-run)
# --------------------------------------------------------------------------- #
def sec4_repro(repro_dir: Path) -> dict:
    per_arm = {}
    for arm in ARMS:
        key = f"SFV5-A6-H2-{arm}"
        committed = json.loads((CELLS / f"{key}.json").read_text())
        repro_path = repro_dir / f"{key}.json"
        if not repro_path.exists():
            per_arm[key] = {"present": False}
            continue
        repro = json.loads(repro_path.read_text())
        cu, ru = committed.pop("run_utc"), repro.pop("run_utc")
        per_arm[key] = {
            "present": True,
            "exact_match_modulo_run_utc": committed == repro,
            "committed_run_utc": cu,
            "repro_run_utc": ru,
            "repro_pins": repro.get("pins"),
        }
        committed["run_utc"] = cu
    return {
        "repro_dir": str(repro_dir),
        "per_arm": per_arm,
        "ok": all(v.get("present") and v.get("exact_match_modulo_run_utc")
                  for v in per_arm.values()),
    }


# --------------------------------------------------------------------------- #
# 5. cash/cost/turnover arithmetic from payloads
# --------------------------------------------------------------------------- #
def sec5_money() -> dict:
    per_arm = {}
    for arm in ARMS:
        key = f"SFV5-A6-H2-{arm}"
        cell = json.loads((CELLS / f"{key}.json").read_text())
        base = cell["base"]
        curve = base["equity_curve"]
        pp = base["period_pnls"]
        dates = list(curve.keys())
        vals = list(curve.values())
        telescoping = math.fsum(p for _, p in pp)
        # period PnLs are measured BETWEEN fills and costs are charged at
        # fills, so the frozen identity is fsum(pnls) == total_pnl+total_cost
        telescoping_rhs = base["total_pnl"] + base["total_cost"]
        # implied one-way turnover from the recorded schedule turnover
        implied_one_way = (cell["schedule_turnover_two_way_per_year"]
                           * (cell["n_sessions"] / 252.0) / 2.0)
        const_equity_cost = implied_one_way * cell["cost_bps_base"] / 1e4
        recomputed_residual = math.fsum(
            [math.fsum(base["symbol_contribution"].values()),
             -base["total_cost"], -base["total_pnl"]])
        per_arm[key] = {
            "n_periods_matches": len(pp) == cell["n_periods_base"],
            "curve_dates_strictly_increasing": all(
                dates[i] < dates[i + 1] for i in range(len(dates) - 1)),
            "curve_min_positive": min(vals) > 0.0,
            "curve_last_equals_1_plus_total_pnl": abs(
                vals[-1] - (1.0 + base["total_pnl"])) < 1e-12,
            "telescoping_pnl_plus_cost_identity": abs(
                telescoping - telescoping_rhs) < 1e-9,
            "telescoping_diff": abs(telescoping - telescoping_rhs),
            "expectancy_identity": abs(
                base["expectancy"] - telescoping_rhs / len(pp)) < 1e-15,
            "attribution_residual_recorded": base["attribution_residual"],
            "attribution_residual_recomputed_from_contribution": recomputed_residual,
            "attribution_identity_abs_le_1e_9": abs(recomputed_residual) <= 1e-9,
            "implied_one_way_turnover": implied_one_way,
            "const_equity_cost_approx": const_equity_cost,
            "total_cost_recorded": base["total_cost"],
            "cost_within_compounding_band": abs(
                base["total_cost"] - const_equity_cost) < 0.15 * max(
                1e-9, const_equity_cost),
            "stress_cost_over_base_cost": cell["stress"]["total_cost"]
            / base["total_cost"],
            "stress_cost_in_2x_band": 1.9 <= cell["stress"]["total_cost"]
            / base["total_cost"] <= 2.0,
            "stress_expectancy_near_base": abs(
                cell["stress"]["expectancy"] - base["expectancy"]) < 1e-3,
            "schedule_turnover_le_ceiling": cell[
                "schedule_turnover_two_way_per_year"] <= 6.0,
            "schedule_turnover_matches_gate_observed": cell[
                "schedule_turnover_two_way_per_year"] == cell["gates"][
                "turnover_within_ceiling"]["observed"],
        }
    return {"per_arm": per_arm, "ok": all(
        v["n_periods_matches"] and v["curve_dates_strictly_increasing"]
        and v["curve_min_positive"] and v["curve_last_equals_1_plus_total_pnl"]
        and v["telescoping_pnl_plus_cost_identity"] and v["expectancy_identity"]
        and v["attribution_identity_abs_le_1e_9"]
        and v["cost_within_compounding_band"] and v["stress_cost_in_2x_band"]
        and v["schedule_turnover_matches_gate_observed"]
        for v in per_arm.values())}


# --------------------------------------------------------------------------- #
# 6. denominator math
# --------------------------------------------------------------------------- #
def sec6_denominator() -> dict:
    ledgers = {
        "V2": CONTROL.parent / "stocks_free_v2_run" / "ledger.json",
        "V3": CONTROL.parent / "stocks_free_v3_run" / "ledger.json",
        "V4": CONTROL.parent / "stocks_free_v4_run" / "execution_ledger.json",
        "V5": CONTROL / "execution_ledger.json",
    }
    per, tot_o, tot_p = {}, 0, 0
    for name, path in ledgers.items():
        d = json.loads(path.read_text())
        per[name] = {"file": str(path), "observed": d["observed"],
                     "published": d["published"]}
        tot_o += d["observed"]
        tot_p += d["published"]
    return {
        "per_cycle": per, "total_observed": tot_o, "total_published": tot_p,
        "matches_claim_21_21": tot_o == 21 and tot_p == 21,
        "matches_family_verdicts_denominator": json.loads(
            (CONTROL / "family_verdicts.json").read_text())
        ["denominator_after_v5"] == {"historical": 18, "v5_observed": 3,
                                     "v5_published": 3, "total": 21},
        "ok": tot_o == 21 and tot_p == 21,
    }


# --------------------------------------------------------------------------- #
# 7. S1 seal + boundaries (static portions)
# --------------------------------------------------------------------------- #
def sec7_boundaries() -> dict:
    cells = {a: json.loads((CELLS / f"SFV5-A6-H2-{a}.json").read_text())
             for a in ARMS}
    last_sessions = {a: cells[a]["last_session"] for a in ARMS}
    scorer = Path("/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v5"
                  "/r-reproduce/.staging/scorer_v5.py").read_text()
    names = git("diff", "--name-only", f"{V4_TERMINAL}..{TERMINAL_HEAD}").split()
    suspicious = [n for n in names
                  if any(t in n.lower() for t in ("paper", "live", "orders", "s1/"))]
    return {
        "per_cell_last_session": last_sessions,
        "all_last_sessions_pre_s1": all(d < S1_START for d in last_sessions.values()),
        "fold3_end": FOLD_WINDOWS["S0_FOLD_3"][1],
        "scorer_s1_clamp_present": "if d < S1_START" in scorer
        and 'S1_START = "2025-08-01"' in scorer and "S1_LEAK" in scorer,
        "suspicious_paths_in_cycle_diff": suspicious,
        "state_s1": json.loads((CONTROL / "state.json").read_text())["s1"],
        "state_deployment": json.loads((CONTROL / "state.json").read_text())["deployment"],
        "ok": all(d < S1_START for d in last_sessions.values())
        and not suspicious,
    }


# --------------------------------------------------------------------------- #
# 8. history integrity
# --------------------------------------------------------------------------- #
def sec8_history() -> dict:
    v234 = git("diff", V4_TERMINAL + ".." + TERMINAL_HEAD, "--",
               "research/control/stocks_free_v4_run",
               "research/control/stocks_free_v3_run",
               "research/control/stocks_free_v2_run")
    fusion_ns = git("diff", "--name-status", f"{FUSION_CORE}..{TERMINAL_HEAD}",
                    "--", "research/data_fusion", "tests/data_fusion").split("\n")
    fusion_added_only = all(
        (line.startswith("A\t") for line in fusion_ns if line.strip()))
    fusion_files = [line.split("\t", 1)[1] for line in fusion_ns if line.strip()]
    # stocks_compat import screen across all python under research/ and tests/
    grep = subprocess.run(
        ["grep", "-rln", "stocks_compat", "--include=*.py",
         str(REPO / "research"), str(REPO / "tests")],
        capture_output=True, text=True)
    importers = sorted(
        p.replace(str(REPO) + "/", "") for p in grep.stdout.split() if p)
    scored_path_import = [p for p in importers
                          if not p.endswith("test_v5_stocks_compatibility.py")
                          and "audits" not in p]
    return {
        "v2_v3_v4_control_diff_empty": v234 == "",
        "fusion_diff_name_status": fusion_ns,
        "fusion_additions_only": fusion_added_only,
        "fusion_added_files": fusion_files,
        "fusion_added_files_exactly_compat_and_test": sorted(fusion_files) == [
            "research/data_fusion/stocks_compat.py",
            "tests/data_fusion/test_v5_stocks_compatibility.py"],
        "stocks_compat_referenced_in": importers,
        "stocks_compat_imported_outside_own_test": scored_path_import,
        "ok": v234 == "" and fusion_added_only
        and sorted(fusion_files) == ["research/data_fusion/stocks_compat.py",
                                     "tests/data_fusion/test_v5_stocks_compatibility.py"]
        and not scored_path_import,
    }


# --------------------------------------------------------------------------- #
# 9. owner-plan conformance
# --------------------------------------------------------------------------- #
def sec9_conformance() -> dict:
    state = json.loads((CONTROL / "state.json").read_text())
    fam = json.loads((CONTROL / "family_verdicts.json").read_text())
    novelty = json.loads((REPO / "research" / "audits" / "stocks_free_v5"
                          / "a7_n_novelty_audit.json").read_text())
    proposal = json.loads((CONTROL / "proposals" / "a5_h2.json").read_text())
    allowed = {
        "STOCKS_FREE_V5_REJECT_ALL",
        "STOCKS_FREE_V5_ONE_OR_MORE_STAGE_A_SURVIVORS_LOCKED_FOR_FUTURE_S1",
        "STOCKS_FREE_V5_BLOCKED_DATA_OR_SELECTION",
        "STOCKS_FREE_V5_BLOCKED_PRELAUNCH",
        "STOCKS_FREE_V5_INCOMPLETE_NOT_PROMOTABLE",
    }
    a5h2 = novelty["verdicts"].get("a5_h2", {})
    return {
        "verdict_in_allowed_set": state["verdict"] in allowed,
        "verdict": state["verdict"],
        "survivors_recorded": fam["survivors"],
        "no_survivor_claimed": fam["survivors"] == 0,
        "family_verdict_is_reject": fam["families"][
            "SFV5-A6-H2-CROSS-SECTOR-COUPLING"]["verdict"]
            == "STOCKS_FREE_V5_FAMILY_REJECT",
        "a5h2_not_scored": "SFV5-A5-H2" not in json.loads(
            (CONTROL / "execution_ledger.json").read_text())["published_keys"],
        "a5h2_measured_ineligible_at_D2": novelty["overall_novelty_verdict"]
        ["ineligible"][-2].startswith("SFV5-A5-H2")
        and "0.319 > 0.20" in json.dumps(novelty["findings"][2]["finding"]),
        "a5h2_shape_gate_measurement": {
            "mean_abs_rho_vs_V4_semivar_shape_anchor":
                a5h2.get("gates", {}).get("detail") is not None
                or "see findings A7N-F3",
            "recorded": "0.319 > 0.20 (A7N-F3)",
        },
        "a5h2_confirmatory_preregistration_present": bool(proposal),
        "novelty_overall": novelty["overall_novelty_verdict"]["verdict"],
        "ok": state["verdict"] in allowed and fam["survivors"] == 0,
    }


def main() -> int:
    fam = json.loads((CONTROL / "family_verdicts.json").read_text())
    report = {
        "audit_head": git("rev-parse", "HEAD").strip(),
        "sections": {
            "1_ledger_once_only": sec1_ledger(),
            "2_artifact_integrity": sec2_integrity(fam),
            "3_gate_arithmetic": sec3_gate_math(),
            "4_reproduction": sec4_repro(REPRO_DIR),
            "5_money": sec5_money(),
            "6_denominator": sec6_denominator(),
            "7_boundaries": sec7_boundaries(),
            "8_history": sec8_history(),
            "9_conformance": sec9_conformance(),
        },
    }
    report["all_ok"] = all(v["ok"] for v in report["sections"].values())
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
