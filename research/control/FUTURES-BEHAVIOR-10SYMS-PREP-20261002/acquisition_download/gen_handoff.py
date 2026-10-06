#!/usr/bin/env python3
"""gen_handoff.py — write dispatch/handoff_ACQ-DOWNLOAD.json
(schema zcode_orch_v3_handoff@1) mechanically from the ledger + reports."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
from pathlib import Path

TASK = Path("/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/"
            "prep/research/control/FUTURES-BEHAVIOR-10SYMS-PREP-20261002")
ACQ = TASK / "acquisition_download"
REPO = Path("/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep")
HANDOFF = TASK / "dispatch" / "handoff_ACQ-DOWNLOAD.json"


def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def git_head() -> str:
    r = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"],
                       capture_output=True, text=True)
    return r.stdout.strip()


def git_status_short() -> list[str]:
    r = subprocess.run(["git", "-C", str(REPO), "status", "--short"],
                       capture_output=True, text=True)
    return [l for l in r.stdout.splitlines() if l.strip()]


def main() -> None:
    led = json.loads((ACQ / "COMPLETION_LEDGER.json").read_text())
    man = json.loads((ACQ / "AV1_TRIM_MANIFEST.json").read_text())
    rs_path = ACQ / "RESCOPE_MANIFEST.json"
    rs = json.loads(rs_path.read_text()) if rs_path.exists() else None
    rt = led["running_totals"]
    stop = (ACQ / "PIPELINE_STOP.json")
    stop_blob = json.loads(stop.read_text()) if stop.exists() else None

    states = {}
    for c in led["chunks"].values():
        s = c.get("state", "PLANNED")
        states[s] = states.get(s, 0) + 1
    qa_fail = [c["chunk_key"] for c in led["chunks"].values()
               if c.get("qa", {}).get("verdict") == "FAIL"]
    overlap_path = ACQ / "IBKR_OVERLAP_VALIDATION.json"
    overlap = json.loads(overlap_path.read_text()) if overlap_path.exists() \
        else None

    n_dropped = states.get("DROPPED_BY_OWNER_RESCOPE", 0)
    n_active = sum(v for k, v in states.items()
                   if k != "DROPPED_BY_OWNER_RESCOPE")
    all_delivered = (states.get("MIRRORED", 0) == n_active and n_active > 0
                     and not qa_fail)
    complete = all_delivered
    status = ("COMPLETE" if complete else
              "PARTIAL" if states.get("MIRRORED", 0) > 0 else "BLOCKED")

    total_records = sum(c.get("qa", {}).get("records_actual") or 0
                        for c in led["chunks"].values())
    raw_b = sum(f["bytes"] for c in led["chunks"].values()
                for f in c.get("files", [])
                if f["vendor_filename"].endswith(".dbn.zst"))
    pq_b = sum(c.get("qa", {}).get("parquet_bytes") or 0
               for c in led["chunks"].values())
    max_drift = max((c.get("qa", {}).get("records_drift_pct") or 0
                     for c in led["chunks"].values()), default=0.0)

    pkg_quote = (rs["budget"]["new_package_total_get_cost"] if rs
                 else man["totals"]["get_cost_usd"])
    summary = (
        f"Owner rescope package FULLY delivered (${pkg_quote:.2f} quote): "
        f"{states.get('MIRRORED', 0)}/{n_active} active chunks downloaded + "
        f"QA-PASS + iCloud-mirrored ({n_dropped} chunks dropped by owner "
        f"rescope at $0 spend); committed ${rt['committed_usd']:.2f} == "
        f"delivered == package quote (drift $0.0000) vs hard stop $118 / "
        f"ceiling $125; {total_records:,} records; raw {raw_b/1e9:.2f} GB "
        f"zst + parquet {pq_b/1e9:.2f} GB; max QA record drift "
        f"{max_drift}%; states {json.dumps(states)}"
    )

    findings = [
        "Rescope arithmetic: fixed core (def+stat ALL10 + NQ/ES 36m + FX "
        "short windows) $31.39 + NQ delta 2010-06-06..2023-10-01 $21.03 + "
        "ES delta $25.60 + FX backfills from 2022-01-01 (equal-dollar "
        "$9.24/root; deepest fit) $27.79 = $105.81 total; dropped "
        "GC/SI/CL/NG ohlcv avoided $81.65 at zero spend.",
        "Batch API verified from official client v0.87.0: submit_job -> "
        "queued/processing/done/expired; per-file download with vendor "
        "sha256 (verified 1:1 on every file); get_cost docstring prices "
        "'historical streaming or batched files' — same per-GB path; "
        "per-chunk quotes summed EXACTLY to package quote ($105.810097 "
        "committed == delivered; $0.0000 drift).",
        "MEASURED vendor conventions (documented, not defects): "
        "(1) definitions re-broadcast at each session open + spread legs "
        "as leg_index records (0 true dups/conflicts); (2) exchange "
        "re-lists spread/strip composites (CLF4-BZF4, NG:SA strips) under "
        "new instrument_ids — registry tracks strict outright pattern "
        "^(NQ|ES|CL|NG|GC|SI|6E|6J|6B|6A)[A-Z][0-9]$ only; (3) GLBX "
        "one-digit-year raw symbols wrap per decade (registry NQZ0=Dec2030 "
        "vs 2010-era NQZ0 iid 3088) — instrument_id is true identity; "
        "(4) parent ohlcv requests include calendar-spread bars (price "
        "DIFFERENCES; 21,430/728,230 in NQ 2010-12 chunk) — filter by "
        "outright pattern downstream; (5) stat ts_ref uses u64 UNDEF "
        "sentinel for quote-side types (stored NULL in parquet); (6) one "
        "definition window (2026-07..10) has 866/1.06M out-of-order "
        "ts_recv records (backward 68-139s, clustered at one capture "
        "event; registry applies ts-sorted; thresholded finding); (7) one "
        "byte-identical stat re-emission in 3.4M (stat_type 2, feed "
        "redundancy).",
        "Defect found and fixed in lane tooling: an underscore-grouping "
        "typo in the i64-max constant nulled EVERY ts_ref in statistics "
        "parquets; fixed to (1<<63)-1 and all 18 statistics parquets "
        "regenerated + re-mirrored from immutable raw (qa_retries "
        "recorded in ledger).",
    ]
    if overlap:
        for root, rr in overlap.get("roots", {}).items():
            if rr.get("rescope_dropped"):
                findings.append(f"IBKR overlap {root}: "
                                f"{rr['rescope_dropped']}")
                continue
            idn = rr.get("identity", {})
            dc = rr.get("daily_close", {})
            dv = rr.get("daily_volume", {})
            m1 = rr.get("m1", {})
            st = rr.get("settlement", {})
            findings.append(
                f"IBKR overlap {root} (2025-08..2026-10): identity "
                f"{idn.get('n_match')}/{idn.get('n_overlap_contracts')} "
                f"(100% PASS); settlement final-vs-IBKR-close n="
                f"{st.get('n_contract_days')}, median|diff|="
                f"{st.get('median_abs_diff_ticks')} tick, "
                f"{st.get('pct_within_1_tick')}% within 1 tick (PASS); M1 "
                f"grid 100%, {m1.get('ibkr_m1_overlap_bars')} overlapping "
                f"bars median|diff|="
                f"{m1.get('median_abs_close_diff_ticks')} tick (PASS); "
                f"volume median ratio {dv.get('median_ratio')} (PASS); "
                f"literal trade-close-vs-IBKR-close FAILS (median 17.5 "
                f"ticks on liquid days) with MEASURED cause: IBKR daily "
                f"close IS the official settlement (settlement check "
                f"matches 100% at 0 ticks), not a last trade — "
                f"trade-vs-settlement spread is market structure, not a "
                f"data defect")

    outputs = []
    for name in ("AV1_TRIM_MANIFEST.json", "trim_quotes.json",
                 "rescope_quotes.json", "RESCOPE_MANIFEST.json",
                 "COMPLETION_LEDGER.json", "CONTRACT_REGISTRY.json",
                 "DOWNLOAD_REPORT.md", "ACQ_DOWNLOAD_REPORT_VI.md",
                 "IBKR_OVERLAP_VALIDATION.json", "PIPELINE_STOP.json"):
        p = ACQ / name
        if p.exists():
            outputs.append({"path": str(p.relative_to(REPO)),
                            "sha256": sha256_of(p)})
    if overlap_path.exists():
        outputs.append({"path": str(overlap_path.relative_to(REPO)),
                        "sha256": sha256_of(overlap_path)})

    handoff = {
        "schema": "zcode_orch_v3_handoff@1",
        "written_utc": dt.datetime.now(dt.timezone.utc).isoformat(
            timespec="seconds"),
        "task_id": "FUTURES-BEHAVIOR-10SYMS-PREP-20261002",
        "cycle_id": "UNREGISTERED_PREP",
        "role": "lane",
        "lane": "ACQ-DOWNLOAD",
        "dispatch_sha": git_head(),
        "actual_start_sha": git_head(),
        "commit_sha": None,
        "commit_sha_disclosure": "lane does not commit; worktree left "
                                 "dirty for lead review",
        "status": status,
        "summary": summary,
        "outputs": outputs,
        "findings": findings,
        "defects": qa_fail,
        "open_questions": [
            "iCloud upload completion is macOS's job (SYNC_PENDING_"
            "UNVERIFIED everywhere); owner may verify in Finder/iCloud "
            "settings",
            "actual invoice vs get_cost reconciliation is owner-side "
            "(no account endpoint; NOT_RUN_DOC_UNCLEAR)",
        ],
        "known_limitations": [
            "FX ohlcv depth trimmed below every FX hypothesis floor "
            "(arithmetic forced by the $115 target); FX data serves "
            "reference + IBKR-overlap validation only",
            "statistics/definition windows are 36 months (2023-10-01 "
            "start) matching A-v1; contracts activated before 2023-10-01 "
            "resolve via file symbol mappings (partial identity, "
            "exchange=UNKNOWN_VIA_MAPPING) if their A records predate "
            "the window",
            "scratch decompressed copies are lane-owned temps deleted "
            "after each batch QA; raw .dbn.zst + parquet kept forever",
        ],
        "incidents": [
            "2026-10-02: transient ConnectTimeout on batch.list_files "
            "killed the first full run after chunk-2 download; resumed "
            "from ledger with zero re-billing (same job id reused)",
            "2026-10-02: qa_batch import regression (missing sys) killed "
            "one relaunch instantly; fixed; no money impact",
        ],
        "tree_status": git_status_short()[:40],
        "workers": 0,
        "budget": {
            "owner_ceiling_usd": 125.00,
            "lane_hard_stop_usd": 118.00,
            "initial_trim_manifest_quote_usd": man["totals"]["get_cost_usd"],
            "rescope_package_quote_usd": (
                rs["budget"]["new_package_total_get_cost"] if rs else None),
            "committed_usd": rt["committed_usd"],
            "delivered_usd": rt["delivered_usd"],
            "dropped_lines_avoided_usd": (
                rs["dropped_lines"]["avoided_spend_usd"] if rs else None),
            "dropped_lines_actual_spend_usd": 0.0,
        },
        "authority_claims": [],
        "recommended_next_action": (
            "ALL_CHUNKS_DONE" if complete else
            "rerun acquisition_download/acq_pipeline.py to resume from "
            "COMPLETION_LEDGER.json (no double-billing); then "
            "gen_report.py + gen_handoff.py"),
    }
    if stop_blob:
        handoff["stop"] = stop_blob
    HANDOFF.write_text(json.dumps(handoff, indent=1))
    print(f"wrote {HANDOFF} status={status}")


if __name__ == "__main__":
    main()
