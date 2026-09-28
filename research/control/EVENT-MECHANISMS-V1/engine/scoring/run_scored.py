"""Lane E scored runner — EVENT-MECHANISMS-V1 (post owner GO 2026-09-28).

Computes EXACTLY the 3 GO-authorized cells on the frozen decision books
(read-only consumption; raw .jsonl verified byte-identical to the committed
.gz before use):
    EMV1-A1-FILINGFLOW-ACC anchor (H=5) | N1 (H=10) | N2 (S2 monitored, H=5)
plus the registered re-evaluations (date-only, permuted-acceptance x3 seed
20260927, clock-only shadow) and the buy-and-hold baseline (context).

E0 heavy lock: machine-wide lock acquired via research.governance.heavy_lock
(ROOT repo module) for the whole compute phase; released in finally;
registry-row snapshots before/after recorded to lock_evidence.json.

Fail-closed guards before any arithmetic:
  - worktree HEAD must equal the code freeze sha 1978607785f306e7de050f934482a5adc042a77f
  - each consumed book's sha256 must equal the verified value (raw == .gz)

Outputs (deterministic except computed_utc):
  scored/scored_rows.jsonl    one row per cell (E3 schema)
  scored/scored_detail.json   every number + every bar with margin (byte-
                              compared across the determinism double-run)
  scored/lock_evidence.json   E0 lock handle evidence
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from collections import Counter

HERE = os.path.abspath(os.path.dirname(__file__))
ENGINE_DIR = os.path.abspath(os.path.join(HERE, ".."))
WT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
# HERE = <wt>/research/control/EVENT-MECHANISMS-V1/engine/scoring -> 5 ups = <wt>
ROOT_REPO = "/Users/hoangminhlong/my-quantitative"
EVID = os.path.join(ENGINE_DIR, "evidence")
CYCLE_DIR = os.path.abspath(os.path.join(ENGINE_DIR, ".."))

sys.path.insert(0, ENGINE_DIR)
sys.path.insert(0, ROOT_REPO)  # heavy_lock is machine-wide; module from ROOT per dispatch

from emv1 import config as C  # noqa: E402
from scoring import gates, score as S  # noqa: E402

CODE_FREEZE_SHA = "1978607785f306e7de050f934482a5adc042a77f"

# verified pre-run: raw .jsonl byte-identical to committed .gz (gunzip | sha256)
BOOK_DIGESTS = {
    "a1_decisions.jsonl": "7e6b6a1dc603093a1ad1061295d8e27da8c7949ce91066b456e8adcf866532f3",
    "control_a1_dateonly.jsonl": "96f63ae0bc835e539b5e9334d9127d26d931d2f624ce8e4235ed3a69de6ca443",
    "control_a1_permuted.jsonl": "a2a4332473469e67a8d24d5726e8e4e955448985b16004c671b955d9827c07fe",
    "control_a1_clock_shadow.jsonl": "ade5e0ddf6a2c489b82aa121182080f459eebb066772679cf137160bc6e07971",
}
DATA_SNAPSHOT_DIGEST_SOURCE = os.path.join(WT, ".staging_eventmech", "SHA256SUMS.staged.txt")
DATA_SNAPSHOT_DIGEST = "18dfc1db23e7cf6740b7fc9e1393e5e9c0dfe9a9768dd7703e9752400e72bbba"

ARMS = ("A1-ANCHOR", "A1-N1", "A1-N2")
ARM_HOLD = {"A1-ANCHOR": 5, "A1-N1": 10, "A1-N2": 5}
COST_TIER = ("STOCKS-AMIHUD-RETEST-V1 frozen band (10/15/25 bps per fill at "
             "DVmed60 >= 50M/10M/2M) x Q-2 open 3.35 (entry) / 1.0 (exit); "
             "stress powers 1.0/1.5/2.0; cost exactly once per fill")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def head_sha() -> str:
    out = subprocess.run(["git", "-C", WT, "rev-parse", "HEAD"],
                         capture_output=True, text=True, check=True)
    return out.stdout.strip()


def arm_config_digest() -> str:
    """sha256 of the G3_FREEZE A1 section (header '## EMV1-A1' up to but not
    including '## EMV1-A2')."""
    text = open(os.path.join(CYCLE_DIR, "G3_FREEZE.md"), encoding="utf-8").read()
    a = text.index("## EMV1-A1")
    b = text.index("## EMV1-A2")
    return hashlib.sha256(text[a:b].encode("utf-8")).hexdigest()


def load_books() -> dict:
    books = {}
    for fname, want in BOOK_DIGESTS.items():
        path = os.path.join(EVID, fname)
        got = sha256_file(path)
        if got != want:
            raise SystemExit(
                f"FROZEN_BOOK_DIGEST_MISMATCH: {fname} sha256 {got} != pinned {want} "
                f"— frozen books must never be adjusted; STOP")
        books[fname] = [json.loads(l) for l in open(path, encoding="utf-8")]
    # cross-check against the committed .gz bytes too
    import gzip
    for fname in BOOK_DIGESTS:
        with gzip.open(os.path.join(EVID, fname + ".gz"), "rt", encoding="utf-8") as fh:
            gz_bytes = fh.read().encode("utf-8")
        raw_bytes = open(os.path.join(EVID, fname), "rb").read()
        if hashlib.sha256(gz_bytes).hexdigest() != hashlib.sha256(raw_bytes).hexdigest():
            raise SystemExit(f"FROZEN_BOOK_GZ_MISMATCH: {fname} raw != committed .gz — STOP")
    return books


def split_by(records, keyfn):
    out = {}
    for r in records:
        out.setdefault(keyfn(r), []).append(r)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=os.path.join(ENGINE_DIR, "scored"))
    args = ap.parse_args()
    out_dir = args.out_dir
    os.makedirs(out_dir, exist_ok=True)

    # ---------------- E0 heavy lock (machine-wide) ----------------
    from research.governance import heavy_lock
    before = heavy_lock.inspect()
    command = [sys.executable, os.path.abspath(__file__), "--out-dir", out_dir]
    lock_ev = {"before_inspect": before, "worktree": WT, "command": command}
    handle = heavy_lock.acquire(
        cycle_id="EVENT-MECHANISMS-V1",
        role="scored-e",
        worktree=WT,
        command=lock_ev["command"],
        expected_artifacts=[
            "research/control/EVENT-MECHANISMS-V1/engine/scored/scored_rows.jsonl",
            "research/control/EVENT-MECHANISMS-V1/engine/scored/scored_detail.json",
            "research/control/EVENT-MECHANISMS-V1/engine/scored/SCORED_REPORT.md",
        ],
    )
    reg_row = None
    reg_path = heavy_lock.machine_runtime_dir() / "heavy_worker.registry.json"
    try:
        reg_row = json.loads(reg_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 — evidence only
        reg_row = {"unreadable": str(exc)}
    lock_ev["registry_row_after_acquire"] = reg_row

    status = "FAILED"
    note = ""
    try:
        # ---------------- fail-closed guards ----------------
        got_head = head_sha()
        if got_head != CODE_FREEZE_SHA:
            raise SystemExit(f"CODE_FREEZE_MISMATCH: HEAD {got_head} != {CODE_FREEZE_SHA} — STOP")
        if sha256_file(DATA_SNAPSHOT_DIGEST_SOURCE) != DATA_SNAPSHOT_DIGEST:
            raise SystemExit("DATA_SNAPSHOT_DIGEST_MISMATCH on SHA256SUMS.staged.txt — STOP")
        books = load_books()
        a1 = books["a1_decisions.jsonl"]
        dateonly = books["control_a1_dateonly.jsonl"]
        permuted = books["control_a1_permuted.jsonl"]
        shadow = books["control_a1_clock_shadow.jsonl"]

        # book invariants (fail-closed). Record identity across books is
        # (control_variant, draw, event_id): the permuted-acceptance book
        # deliberately reuses the anchor arm_id/event_id for the same events
        # with the clock moved (separate control_variant + draw).
        for r in a1 + dateonly + permuted + shadow:
            if r["direction"] not in ("LONG", "SHORT"):
                raise SystemExit("BOOK_INVARIANT: bad direction")
        ids = Counter((r["control_variant"], r["draw"], r["event_id"])
                      for r in a1 + dateonly + permuted + shadow)
        if any(v > 1 for v in ids.values()):
            raise SystemExit("BOOK_INVARIANT: duplicate record ids across books")

        by_arm = split_by(a1, lambda r: r["arm_id"])
        for arm in ARMS:
            if arm not in by_arm:
                raise SystemExit(f"BOOK_INVARIANT: arm {arm} missing")
            holds = {r["hold_sessions"] for r in by_arm[arm]}
            if holds != {ARM_HOLD[arm]}:
                raise SystemExit(f"BOOK_INVARIANT: {arm} hold sessions {holds} != frozen {ARM_HOLD[arm]}")

        # ---------------- E1 scoring + E2 gates ----------------
        acd = arm_config_digest()
        cells = {}
        for arm in ARMS:
            cb = gates.cell_bars(by_arm[arm], arm)
            cells[arm] = cb

        ident = gates.identity_bars(
            anchor_records=by_arm["A1-ANCHOR"],
            n2_records=by_arm["A1-N2"],
            dateonly_anchor_records=[r for r in dateonly if r["arm_id"] == "A1-DATEONLY-ANCHOR"],
            permuted_records_by_draw=split_by(permuted, lambda r: r["draw"]),
        )
        shadow_diag = gates.clock_shadow_diagnostic(shadow)
        baseline = gates.baseline_buy_hold(by_arm["A1-ANCHOR"])
        dateonly_diag = {
            "A1-DATEONLY-ANCHOR": {
                "n": len([r for r in dateonly if r["arm_id"] == "A1-DATEONLY-ANCHOR"]),
                "agg_1x": S.aggregate([S.event_net_return(r, 1.0) for r in dateonly
                                       if r["arm_id"] == "A1-DATEONLY-ANCHOR"]),
            },
            "A1-DATEONLY-N1": {
                "n": len([r for r in dateonly if r["arm_id"] == "A1-DATEONLY-N1"]),
                "agg_1x": S.aggregate([S.event_net_return(r, 1.0) for r in dateonly
                                       if r["arm_id"] == "A1-DATEONLY-N1"]),
            },
        }

        verdicts = {arm: gates.overall_verdict(cells[arm], ident) for arm in ARMS}

        # ---------------- E3 rows ----------------
        computed_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        rows = []
        for arm in ARMS:
            cb = cells[arm]
            v = verdicts[arm]
            rows.append({
                "schema": "event_mechanisms_v1_scored_row@1",
                "cycle_id": C.CYCLE_ID,
                "family_id": C.FAMILY_A1,
                "arm_id": arm,
                "arm_config_digest": acd,
                "data_snapshot_digest": DATA_SNAPSHOT_DIGEST,
                "code_freeze_sha": CODE_FREEZE_SHA,
                "cost_tier": COST_TIER,
                "folds": dict(sorted((f, cb["folds_1x"][f]["n"]) for f in cb["folds_1x"])),
                "events": cb["n_events"],
                "net_expectancy_bps_1x": cb["agg_1x"]["net_expectancy_bps"],
                "net_expectancy_bps_1_5x": cb["agg_1_5x"]["net_expectancy_bps"],
                "net_expectancy_bps_2x": cb["agg_2x"]["net_expectancy_bps"],
                "pf_1x": cb["agg_1x"]["pf"],
                "pf_1_5x": cb["agg_1_5x"]["pf"],
                "pf_2x": cb["agg_2x"]["pf"],
                "pf_note": cb["agg_1x"]["pf_class"],
                "fold_nets_bps_1x": {f: cb["folds_1x"][f]["net_expectancy_bps"]
                                     for f in sorted(cb["folds_1x"])},
                "concentration_top_name": (cb["concentration"]["top"][0]["ticker"]
                                           if cb["concentration"]["top"] else None),
                "concentration_max_share": cb["concentration"]["max_share"],
                "drop_one_class": "UNCHANGED" if not cb["bars"]["DROP_ONE_BAR"]["fired"] else "CHANGED",
                "verdict_per_bar": {name: b["fired"] for name, b in cb["bars"].items()}
                                   | {name: ident[name]["fired"] for name in
                                      ("BAND1_DATEONLY", "BAND2_STRATA_SPREAD", "PERMUTED_PLACEBO")},
                "fired_bars": v["fired_bars"],
                "overall_cell_verdict": v["overall_cell_verdict"],
                "observed": True,
                "computed_utc": computed_utc,
            })

        detail = {
            "schema": "event_mechanisms_v1_scored_detail@1",
            "cycle_id": C.CYCLE_ID,
            "code_freeze_sha": CODE_FREEZE_SHA,
            "arm_config_digest": acd,
            "data_snapshot_digest": DATA_SNAPSHOT_DIGEST,
            "data_snapshot_digest_source": "sha256(.staging_eventmech/SHA256SUMS.staged.txt)",
            "book_digests": dict(sorted(BOOK_DIGESTS.items())),
            "frozen_constants_echo": {
                "cost_bands": [list(b) for b in C.COST_BANDS],
                "open_band_mult": C.OPEN_BAND_MULT,
                "midday_band_mult": C.MIDDAY_BAND_MULT,
                "cost_stress_powers": list(C.COST_STRESS_POWERS),
                "pf_bar": gates.PF_BAR,
                "fold_bar_min_positive": gates.FOLD_BAR_MIN_POSITIVE,
                "concentration_bar": gates.CONCENTRATION_BAR,
                "band1_ratio_bar": gates.BAND1_RATIO_BAR,
                "placebo_reproduction_bar": gates.PLACEBO_REPRODUCTION_BAR,
                "folds": [list(f) for f in C.FOLDS],
                "seed_permute": C.SEED_PERMUTE,
                "permute_draws": C.PERMUTE_DRAWS,
            },
            "population_counts": {arm: {f: n for f, n in sorted(Counter(
                r["fold"] for r in by_arm[arm]).items())} for arm in ARMS},
            "cells": cells,
            "identity_bars": ident,
            "dateonly_detail": dateonly_diag,
            "clock_shadow_diagnostic": shadow_diag,
            "baseline_buy_hold": baseline,
            "verdicts": verdicts,
        }
        rows_path = os.path.join(out_dir, "scored_rows.jsonl")
        with open(rows_path, "w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, sort_keys=True) + "\n")
        detail_path = os.path.join(out_dir, "scored_detail.json")
        with open(detail_path, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(detail, sort_keys=True, indent=1) + "\n")
        status = "FINISHED"
        note = "scored 3 GO-authorized cells + controls; outputs written"
        print("SCORED_OK", {arm: verdicts[arm]["overall_cell_verdict"] for arm in ARMS})
        return 0
    except SystemExit as exc:
        note = f"SystemExit: {exc}"
        raise
    except Exception as exc:  # noqa: BLE001
        note = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        handle.release(status=status, note=note)
        lock_ev["release_status"] = status
        lock_ev["release_note"] = note
        lock_ev["after_inspect"] = heavy_lock.inspect()
        try:
            hist_tail = (heavy_lock.machine_runtime_dir() / "heavy_worker.history.jsonl"
                         ).read_text(encoding="utf-8").strip().splitlines()[-1]
            lock_ev["history_tail"] = json.loads(hist_tail)
        except Exception as exc:  # noqa: BLE001
            lock_ev["history_tail"] = {"unreadable": str(exc)}
        with open(os.path.join(out_dir, "lock_evidence.json"), "w", encoding="utf-8") as fh:
            fh.write(json.dumps(lock_ev, sort_keys=True, indent=1, default=str) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
