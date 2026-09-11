"""Z-phase EXACT-ARM SANITIZED DRY-RUN for the six FOREX-NG1 budget
cells.  scored=false, real_pnl=false, published=false -- enforced, not
promised:

- decision records carry identity/timing/direction/units/fold/cost
  constants ONLY (no prices, no outcomes);
- the recursive leak scanner must find ZERO forbidden outcome fields in
  EVERY emitted file (a planted-leak negative test proves the scanner);
- every anchor must be non-vacuous (>= 1 decision);
- decision IDs must be pairwise distinct within and across arms, and
  arm_config_digests pairwise distinct;
- the whole build must REPLAY byte-identical (second run into a scratch
  dir; file digests compared);
- structural counts must reproduce the D2-measured frozen counts
  (85/77/50/27/104/202 order-state, 306 first releases, 1842 grid days).

Outputs (all deterministic, no wall-clock content):

- research/control/forex_ng1_run/i/dryrun/decisions_<ARM>.json
- research/control/forex_ng1_run/i/dryrun/manifest.json
- research/control/forex_ng1_run/i/z_dryrun_report.json

Usage:
    .venv/bin/python -m research.assets.forex_ng1.run.dryrun
"""

from __future__ import annotations

import json
import os
import sys

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.assets.forex_ng1.run import arms as A            # noqa: E402
from research.assets.forex_ng1.run import config as C          # noqa: E402
from research.assets.forex_ng1.run import scanner as S         # noqa: E402
from research.assets.forex_ng1.run import data as D            # noqa: E402

OUT_DIR = os.path.join(
    REPO_ROOT, "research/control/forex_ng1_run/i/dryrun")
REPORT_PATH = os.path.join(
    REPO_ROOT, "research/control/forex_ng1_run/i/z_dryrun_report.json")
REPLAY_DIR = "/tmp/forex_ng1_i_dryrun_replay"

#: D2-measured structural counts (selection freeze + d2 feasibility,
#: committed evidence -- the dry-run must reproduce them exactly).
STRUCTURAL_EXPECT = {
    "publication_months": 85,
    "us_anchored_months": 77,
    "non_anchored_months": 8,
    "unique_of_months": 50,
    "no_unique_of_months": 27,
    "coopen_events_total": 104,
    "v7recap_events_total": 202,
    "first_release_events": 306,
    "grid_days": 1842,
}


def build_budget_books(env) -> dict:
    """Build the six budget-cell books (anchors first; controls consume
    their family anchor)."""
    anchor_a5 = A.build_a5p1_anchor(env)
    anchor_a4 = A.build_a4p2_anchor(env)
    dgs10 = A.build_dgs10_series(env)
    books = {}
    for _, arm_id in C.BUDGET_ARMS:
        books[arm_id] = A.build_arm(arm_id, env, anchor_a5=anchor_a5,
                                    anchor_a4=anchor_a4, dgs10=dgs10)
    return books


def arm_output(arm_id: str, book: dict, digest: str) -> dict:
    return {
        "arm_id": arm_id,
        "arm_config_digest": digest,
        "meta": book["meta"],
        "decisions": book["decisions"],
    }


def write_outputs(books: dict, digests: dict, out_dir: str) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    files = {}
    for arm_id, book in sorted(books.items()):
        path = os.path.join(out_dir, f"decisions_{arm_id}.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(arm_output(arm_id, book, digests[arm_id]), fh,
                      indent=1, sort_keys=True)
            fh.write("\n")
        files[arm_id] = path
    manifest = {
        "schema": "forex_ng1_i_dryrun_manifest@1",
        "arms": {
            arm_id: {
                "arm_config_digest": digests[arm_id],
                "decisions": len(book["decisions"]),
                "file_sha256": C.sha256_file(files[arm_id]),
            }
            for arm_id, book in sorted(books.items())
        },
        "verdict_basis": "sanitized dry-run outputs; deterministic "
                         "(no wall-clock content); replay byte-identical "
                         "required",
    }
    mpath = os.path.join(out_dir, "manifest.json")
    with open(mpath, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)
        fh.write("\n")
    files["__manifest__"] = mpath
    return files


def structural_checks(env) -> dict:
    st = env.order_state["counts"]
    measured = {
        "publication_months": st["publication_months"],
        "us_anchored_months": st["us_anchored_months"],
        "non_anchored_months": st["non_anchored_months"],
        "unique_of_months": st["unique_of_months"],
        "no_unique_of_months": st["no_unique_of_months"],
        "first_release_events": len(env.events),
        "grid_days": len(env.grid),
    }
    books_c = A._a5_event_months("coopen", env.order_state)
    books_v = A._a5_event_months("v7recap", env.order_state)
    measured["coopen_events_total"] = sum(
        len(v) for v in books_c.values())
    measured["v7recap_events_total"] = sum(
        len(v) for v in books_v.values())
    rows = {}
    ok = True
    for k, want in STRUCTURAL_EXPECT.items():
        got = measured.get(k)
        match = got == want
        ok &= match
        rows[k] = {"measured": got, "expected": want, "match": match}
    return {"all_match": ok, "rows": rows}


def run_dryrun(report_path: str = REPORT_PATH,
               out_dir: str = OUT_DIR) -> dict:
    env = D.load_env()
    books = build_budget_books(env)
    digests = C.budget_arm_digests()

    # -- identity checks -------------------------------------------------- #
    all_ids = [r["decision_id"] for b in books.values()
               for r in b["decisions"]]
    ids_pairwise_distinct = len(set(all_ids)) == len(all_ids)
    digests_pairwise_distinct = len(set(digests.values())) == len(digests)
    nonvacuous = {
        fam: len(next(b for aid, b in sorted(books.items())
                      if b["meta"]["family_id"] == fam and
                      C.ARM_ROLE[aid] == "anchor")["decisions"]) > 0
        for fam in (C.FAMILY_A5_P1, C.FAMILY_A4_P2)}

    # -- write run 1 ------------------------------------------------------ #
    files = write_outputs(books, digests, out_dir)

    # -- leak scan EVERY emitted file ------------------------------------- #
    leaks = {}
    any_leak = False
    for name, path in sorted(files.items()):
        found = S.scan_json_file(path)
        leaks[name] = found
        any_leak |= bool(found)

    # -- replay byte-identical -------------------------------------------- #
    env2 = D.load_env()
    books2 = build_budget_books(env2)
    files2 = write_outputs(books2, C.budget_arm_digests(), REPLAY_DIR)
    replay_identical = all(
        C.sha256_file(files[k]) == C.sha256_file(files2[k])
        for k in files)

    struct = structural_checks(env)
    ctl_dgs_drops_a5 = books["FXNG1-A5-P1-CTL-DGS10LEVEL"]["meta"].get(
        "records_dropped_state_unavailable", 0)
    ctl_dgs_drops_a4 = books["FXNG1-A4-P2-CTL-DGS10LEVEL"]["meta"].get(
        "records_dropped_state_unavailable", 0)
    anchor_n_a5 = len(books["FXNG1-A5-P1-ANCHOR"]["decisions"])
    anchor_n_a4 = len(books["FXNG1-A4-P2-ANCHOR"]["decisions"])

    verdict = ("DRY_RUN_CLEAN"
               if (not any_leak and ids_pairwise_distinct
                   and digests_pairwise_distinct and all(nonvacuous.values())
                   and replay_identical and struct["all_match"])
               else "LEAK_DETECTED" if any_leak else "NOT_RUN")

    report = {
        "schema": "forex_ng1_i_z_dryrun_report@1",
        "cycle_id": "FOREX-NG1",
        "task_id": "forex-ng1-i-runners",
        "verdict": verdict,
        "scored": False,
        "real_pnl": False,
        "published": False,
        "scanner": {
            "method": S.SCANNER_METHOD,
            "forbidden_patterns": [p.pattern for p in
                                   S.FORBIDDEN_PATTERNS],
            "files_scanned": sorted(files),
            "leaks": leaks,
            "negative_control": "tests/test_forex_ng1_runners.py "
                                "plants one leak field and asserts the "
                                "scanner detects it",
        },
        "arms": {
            arm_id: {
                "family_id": C.FAMILY_OF_ARM[arm_id],
                "arm_role": C.ARM_ROLE[arm_id],
                "arm_config_digest": digests[arm_id],
                "decisions": len(book["decisions"]),
                "meta": book["meta"],
                "file": os.path.relpath(files[arm_id], REPO_ROOT),
                "file_sha256": C.sha256_file(files[arm_id]),
            }
            for arm_id, book in sorted(books.items())
        },
        "identity_checks": {
            "decision_ids_pairwise_distinct": ids_pairwise_distinct,
            "decision_ids_total": len(all_ids),
            "arm_config_digests_pairwise_distinct":
                digests_pairwise_distinct,
            "anchors_nonvacuous": nonvacuous,
        },
        "replay": {
            "method": "full rebuild (env reload + all builders) into "
                      f"{REPLAY_DIR}; per-file sha256 compared",
            "byte_identical": replay_identical,
        },
        "structural_cross_check_vs_d2": struct,
        "budget_cell_mapping_basis": (
            "control cell = CTL-DGS10LEVEL on both families (V8-law "
            "nominal-exposure control): R2 '(V8 law; for A5 ADDITIONALLY "
            "the V7-recap kill R2')' + plan sec1 'nominal-exposure "
            "control MANDATORY on every yield/inflation lane' + V8 "
            "run-contract precedent control_dgs10_level_z252_21bd; the "
            "remaining battery books (A5 CTL-V7RECAP, shadows, seeded "
            "placebos) are implemented and E-phase falsification "
            "ladder inputs, not budget cells"),
        "battery_books_implemented_not_budget": [
            a for _, a in C.BATTERY_ONLY_ARMS],
        "known_disclosures": {
            "ctl_dgs10_warmup_boundary": (
                "the CTL-DGS10LEVEL books are the identical fired anchor "
                "books EXCEPT entries whose trailing 252-grid-day DGS10 "
                "window is not provably covered (the pinned vintaged "
                "DGS10 realtime evidence begins 2018-01-01): those fail "
                "closed and are counted in meta."
                "records_dropped_state_unavailable "
                f"(A5 {ctl_dgs_drops_a5} of {anchor_n_a5}; A4-P2 "
                f"{ctl_dgs_drops_a4} of {anchor_n_a4})"),
        },
        "provenance": env.provenance,
        "outcome_computation": "refused by construction in this lane "
                               "(accounting.compute_outcomes raises unless "
                               "scored=True AND spot authority AUTHORIZED)",
    }
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1, sort_keys=True)
        fh.write("\n")
    return report


def main() -> int:
    report = run_dryrun()
    print(json.dumps({
        "verdict": report["verdict"],
        "arms": {a: v["decisions"] for a, v in report["arms"].items()},
        "replay_byte_identical": report["replay"]["byte_identical"],
        "structural_all_match":
            report["structural_cross_check_vs_d2"]["all_match"],
    }, indent=1))
    return 0 if report["verdict"] == "DRY_RUN_CLEAN" else 2


if __name__ == "__main__":
    raise SystemExit(main())
