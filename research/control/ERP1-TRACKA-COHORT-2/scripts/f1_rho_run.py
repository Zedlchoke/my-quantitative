#!/usr/bin/env python
"""F-1 ANCESTRY-RHO RUNNER — ERP1-TRACKA-COHORT-2 — skeptic lane (skeptic-f0/f1).

Executes the F-1 rho protocol FROZEN in
research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/tracka_cohort2/
SKEPTIC_F0_cohort2_REPORT.md section 4 (one-shot):

  - Consumers: ONLY the anchor target arrays p3a_anchor / p3b_anchor
    (the declared twins are NOT F-1 consumers).
  - Representation: int8 target arrays on the dev-masked H1 grid
    (27,608 AUDUSD / 27,583 USDCAD rows), FULL grid INCLUDING zero rows
    (P-12: representation identity = measurement identity).
  - Statistic: tracka_lib.spearman_rho (average-tie ranks) from the pinned
    A7-certified bytes (sha pinned in the manifest, code_shas.tracka_lib.py).
  - Pooled |rho| = MAX over the named shadow set (worst-shadow governs).
  - Gate: pooled |rho| <= 0.20 per candidate per pair — IMMMOVABLE.
  - Fail-closed everywhere: any manifest/sha/status/invariant mismatch
    aborts BEFORE any rho is consumed; a shadow with status != OK is
    recorded NOT_CONSTRUCTIBLE and the candidate verdict FAILS CLOSED
    (never PASS by absence).

Diagnostics (report-only, never the gate): zero-excluded rho; per-fold rho
(F1..F6 from the frozen fold table, bar->traded-day mapping from the
dev-masked bars1h_ANC plane timestamps; NOT_RUN with reason if the plane
cannot be loaded).

NO PnL exists anywhere in this runner; the sealed window (ts > 2025-12-31)
is never read: every consumed array is dev-masked by construction and the
row pins are re-asserted here.
"""

import hashlib
import json
import os
import sys

import numpy as np

CYCLE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DERIVED = os.path.join(CYCLE_DIR, "data_local", "derived")
SCRIPTS = os.path.join(CYCLE_DIR, "scripts")
MANIFEST = os.path.join(DERIVED, "t2_planes_manifest.json")
OUT = os.path.join(CYCLE_DIR, "falsifier", "F1_rho_results.json")

GATE = 0.20
CANDIDATES = {"p3a_anchor": "TRACKA2-P3A-QCRD-H1", "p3b_anchor": "TRACKA2-P3B-DINV-1D"}
PAIRS = ("AUDUSD", "USDCAD")
HOME = {"TRACKA2-P3A-QCRD-H1": "AUDUSD", "TRACKA2-P3B-DINV-1D": "USDCAD"}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fail(msg):
    print("F1_RUNNER_FAIL_CLOSED: " + msg)
    sys.exit(2)


def target_path(key, pair):
    pre, suf = key.split("_", 1)
    return os.path.join(DERIVED, "t2_%s_%s_%s.npy" % (pre, pair, suf))


def shadow_path(name, pair):
    return os.path.join(DERIVED, "t2shadow_%s_%s.npy" % (name, pair))


def check_array(arr, meta, label, dev_rows, warmup_index, warmup_flat_required):
    if arr.dtype != np.int8:
        fail("%s dtype %s != int8" % (label, arr.dtype))
    if len(arr) != dev_rows:
        fail("%s len %d != dev pin %d" % (label, len(arr), dev_rows))
    if not set(np.unique(arr).tolist()) <= {-1, 0, 1}:
        fail("%s values outside {-1,0,1}" % label)
    if warmup_flat_required and int((arr[:warmup_index] != 0).sum()) != 0:
        fail("%s nonzero inside warmup region" % label)
    if "n_nonzero" in meta and int((arr != 0).sum()) != meta["n_nonzero"]:
        fail("%s nonzero %d != manifest %d" % (label, int((arr != 0).sum()), meta["n_nonzero"]))


def main():
    # ---------- phase 0: manifest + code pins ----------
    runner_sha = sha256_file(os.path.abspath(__file__))
    manifest_sha = sha256_file(MANIFEST)
    m = json.load(open(MANIFEST))
    if m.get("schema") != "tracka2.t2_planes@1" or m.get("cycle_id") != "ERP1-TRACKA-COHORT-2":
        fail("manifest schema/cycle mismatch")
    tl_path = os.path.join(SCRIPTS, "tracka_lib.py")
    if sha256_file(tl_path) != m["code_shas"]["tracka_lib.py"]:
        fail("tracka_lib.py bytes != pinned code_shas.tracka_lib.py (A7-certified 1e09b368...)")
    sys.path.insert(0, SCRIPTS)
    from tracka_lib import spearman_rho  # pinned bytes verified above

    results = {
        "schema": "tracka2.f1_rho@1",
        "cycle_id": "ERP1-TRACKA-COHORT-2",
        "protocol_source": "SKEPTIC_F0_cohort2_REPORT.md section 4 (frozen F-1 rho protocol)",
        "gate_pooled_abs_rho": GATE,
        "representation": "int8 target arrays, dev-masked H1 grid, FULL grid incl. zero rows (P-12)",
        "statistic": "tracka_lib.spearman_rho (average-tie ranks), pinned tracka_lib 1e09b368...",
        "pooled_rule": "max |rho| over named shadow set (worst-shadow governs)",
        "executed_by": "skeptic-f1",
        "manifest_sha256": manifest_sha,
        "tracka_lib_sha256": m["code_shas"]["tracka_lib.py"],
        "runner_sha256": runner_sha,
        "one_shot": "single execution; re-runs require owner amendment",
        "pre_measurement_aborts": [
            "attempt-1 aborted FAIL_CLOSED before any rho existed: warmup-flat invariant "
            "was wrongly applied to SHADOW arrays; shadows carry native census-builder "
            "warmups (protocol requires warmup-flat for CANDIDATES only; rho on the full "
            "grid with each book's own warmup zeros). Invariant scope corrected; no rho "
            "was computed or discarded in the aborted attempt (P-23 fail-closed class).",
            "attempt-2 crashed at candidate-verdict ASSEMBLY (TypeError: string indices) "
            "after in-memory rho rows for p3a were computed but BEFORE any print, persist "
            "or human-readable value existed; the partial in-memory result was discarded "
            "unpersisted and never seen. Attempt-3 is the single persisted measurement; "
            "both aborts disclosed per P-19 honesty class."
        ],
        "candidates": {},
    }

    # ---------- phase 1: verify EVERY consumed byte before any rho ----------
    arrays = {}
    for pair in PAIRS:
        pd_ = m["pairs"][pair]
        if pd_["dev_rows"] != pd_["dev_row_pin"] or not pd_["row_pin_match"]:
            fail("%s dev row pin mismatch" % pair)
        dev_rows = int(pd_["dev_rows"])
        warmup_index = int(pd_["warmup_index"])
        arrays[pair] = {"dev_rows": dev_rows, "warmup_index": warmup_index,
                        "targets": {}, "shadows": {}}
        for key in CANDIDATES:
            meta = pd_["targets"].get(key)
            if meta is None:
                fail("manifest missing target %s/%s" % (key, pair))
            path = target_path(key, pair)
            if sha256_file(path) != meta["sha256"]:
                fail("target %s/%s sha mismatch vs manifest" % (key, pair))
            arr = np.load(path)
            check_array(arr, meta, "target %s/%s" % (key, pair), dev_rows, warmup_index,
                        warmup_flat_required=True)
            arrays[pair]["targets"][key] = arr
        for name, meta in pd_["shadows"].items():
            path = shadow_path(name, pair)
            if not os.path.exists(path):
                fail("shadow file missing %s/%s" % (name, pair))
            if sha256_file(path) != meta["sha256"]:
                fail("shadow %s/%s sha mismatch vs manifest" % (name, pair))
            if meta.get("status") != "OK":
                # fail-closed record; consumed as NOT_CONSTRUCTIBLE, never skipped silently
                arrays[pair]["shadows"][name] = {"status": meta["status"], "arr": None}
                continue
            arr = np.load(path)
            # Shadows keep their NATIVE census-builder warmups (e.g. FX2-H1TSMOM
            # fires from bar ~24, R-ANCHOR from bar ~121-215): the frozen SKEPTIC
            # section 4 protocol requires warmup-flat for CANDIDATES only, and
            # computes rho on the FULL grid with each book's own warmup zeros.
            check_array(arr, meta, "shadow %s/%s" % (name, pair), dev_rows, warmup_index,
                        warmup_flat_required=False)
            arrays[pair]["shadows"][name] = {"status": "OK", "arr": arr}

    # ---------- phase 2: fold-boundary bar indices (diagnostics only) ----------
    fold_bar_bounds = {}
    try:
        import pandas as pd
        for pair in PAIRS:
            ts = pd.read_parquet(os.path.join(DERIVED, "bars1h_ANC_%s.parquet" % pair))["ts"]
            dev = ts[ts <= np.datetime64("2025-12-31 23:59:59")]
            if len(dev) != arrays[pair]["dev_rows"]:
                fail("%s dev plane ts rows %d != pin %d" % (pair, len(dev), arrays[pair]["dev_rows"]))
            day_epoch = dev.to_numpy().astype("datetime64[D]").astype(np.int64)
            bounds = {}
            for fold, fmeta in m["pairs"][pair]["fold_table"].items():
                mask = (day_epoch >= fmeta["first_day_epoch"]) & (day_epoch <= fmeta["last_day_epoch"])
                idx = np.where(mask)[0]
                bounds[fold] = [int(idx[0]), int(idx[-1])]
            fold_bar_bounds[pair] = bounds
        fold_diag_status = "OK"
    except Exception as exc:  # diagnostics are report-only; gate never depends on them
        fold_diag_status = "NOT_RUN (%s)" % exc

    # ---------- phase 3: rho, single pass ----------
    for key, cand in CANDIDATES.items():
        cand_res = {"candidate_id": cand, "home_pair": HOME[cand], "pairs": {}}
        for pair in PAIRS:
            tgt = arrays[pair]["targets"][key]
            rows = []
            not_constructible = []
            for name in sorted(arrays[pair]["shadows"]):
                sh = arrays[pair]["shadows"][name]
                if sh["status"] != "OK":
                    not_constructible.append({"shadow": name, "status": sh["status"]})
                    continue
                s_arr = sh["arr"]
                r = float(spearman_rho(tgt.astype(float), s_arr.astype(float)))
                nz = tgt != 0
                r_nz = float(spearman_rho(tgt[nz].astype(float), s_arr[nz].astype(float))) \
                    if int(nz.sum()) > 2 else None
                per_fold = None
                if fold_diag_status == "OK":
                    per_fold = {}
                    for fold, (lo, hi) in fold_bar_bounds[pair].items():
                        per_fold[fold] = float(spearman_rho(
                            tgt[lo:hi + 1].astype(float), s_arr[lo:hi + 1].astype(float)))
                rows.append({
                    "shadow": name,
                    "rho": round(r, 6),
                    "abs_rho": round(abs(r), 6),
                    "n_shadow_nonzero": int((s_arr != 0).sum()),
                    "diag_zero_excluded_rho": None if r_nz is None else round(r_nz, 6),
                    "diag_per_fold_rho": per_fold,
                })
            if not_constructible:
                # fail-closed: candidate cannot PASS with an unverifiable named shadow
                pair_verdict = "FAIL_CLOSED_SHADOW_NOT_CONSTRUCTIBLE"
                pooled = None
                worst = None
            else:
                worst_row = max(rows, key=lambda x: x["abs_rho"])
                pooled = worst_row["abs_rho"]
                worst = worst_row["shadow"]
                pair_verdict = "WITHIN_GATE" if pooled <= GATE else "ANCESTRY_RHO_BLOCK"
            cand_res["pairs"][pair] = {
                "n_shadows_consumed": len(rows),
                "not_constructible": not_constructible,
                "pooled_worst_abs_rho": pooled,
                "worst_shadow": worst,
                "gate": GATE,
                "pair_verdict": pair_verdict,
                "per_shadow": rows,
            }
        pool_pairs = [cand_res["pairs"][p] for p in PAIRS]
        if any(p["pair_verdict"].startswith("FAIL_CLOSED") for p in pool_pairs):
            cand_res["verdict"] = "FAIL_CLOSED_SHADOW_NOT_CONSTRUCTIBLE"
        elif all(p["pair_verdict"] == "WITHIN_GATE" for p in pool_pairs):
            cand_res["verdict"] = "PASS_F1"
        else:
            blocked = [p for p in PAIRS
                       if cand_res["pairs"][p]["pair_verdict"] == "ANCESTRY_RHO_BLOCK"]
            cand_res["verdict"] = "ANCESTRY_RHO_BLOCK"
            cand_res["blocked_pairs"] = blocked
            cand_res["consequence"] = (
                "home pair blocked => candidate dead"
                if HOME[cand] in blocked
                else "replicate leg dropped; home leg proceeds")
        results["candidates"][key] = cand_res

    results["fold_diagnostics_status"] = fold_diag_status
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(results, f, indent=1)
    print("WROTE", OUT)
    for key, cand_res in results["candidates"].items():
        for pair in PAIRS:
            pr = cand_res["pairs"][pair]
            print("%s / %s: pooled |rho| = %s (worst shadow %s) -> %s" % (
                cand, pair, pr["pooled_worst_abs_rho"], pr["worst_shadow"], pr["pair_verdict"]))
        print("%s VERDICT: %s" % (cand, cand_res["verdict"]))


if __name__ == "__main__":
    main()
