"""REPRO TWIN comparison — ERP1-TRACKA-COHORT-1 (tracka1-repro lane).

Compares the twin's re-run outputs against the published outputs
(pre_run_snapshot/ = byte-identical copy of the integration worktree's
published files, verified before the re-run started).

Output: JSON verdict object printed to stdout; wall-clock fields
(created_utc at any depth, the report's "Generated:" line) and the
dryrun ledger-sha sequence fields are classified separately from
substantive differences.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

LANE = Path(__file__).resolve().parent.parent
REPRO = LANE / "repro"
PRE = REPRO / "pre_run_snapshot"
POST = LANE  # re-run wrote in place

JSON_FILES = ["scored_dryrun.json", "scored_dev_cells.json",
              "scored_holdout_look.json", "scored_seam_law.json",
              "scored_kill_laws.json", "scored_dsr.json"]
SERIES = [f"series/{p}_{a}_dev_series.json"
          for p in ("AUDUSD", "USDCAD")
          for a in ("R-ANCHOR", "R-ORIG", "R-NEIGH", "CAUSAL-PLACEBO",
                    "INVERTED", "BASELINE-SET")]


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def strip_wallclock(obj, path="$"):
    """Remove created_utc at any depth; return (clean_obj, stripped_paths)."""
    stripped = []
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            kp = f"{path}.{k}"
            if k == "created_utc":
                stripped.append(kp)
                continue
            out[k], s = strip_wallclock(v, kp)
            stripped.extend(s)
        return out, stripped
    if isinstance(obj, list):
        out = []
        for i, v in enumerate(obj):
            c, s = strip_wallclock(v, f"{path}[{i}]")
            out.append(c)
            stripped.extend(s)
        return out, stripped
    return obj, stripped


def canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, indent=1, default=str)


def deep_diff(a, b, path="$", out=None):
    """Enumerate differences between two JSON structures as paths."""
    if out is None:
        out = []
    if type(a) is not type(b) and not (
            isinstance(a, (int, float)) and isinstance(b, (int, float))):
        out.append({"path": path, "kind": "type",
                    "pub": repr(type(a).__name__),
                    "repro": repr(type(b).__name__)})
        return out
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            kp = f"{path}.{k}"
            if k not in a:
                out.append({"path": kp, "kind": "repro_only"})
            elif k not in b:
                out.append({"path": kp, "kind": "pub_only"})
            else:
                deep_diff(a[k], b[k], kp, out)
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append({"path": path, "kind": "list_len",
                        "pub": len(a), "repro": len(b)})
        for i, (x, y) in enumerate(zip(a, b)):
            deep_diff(x, y, f"{path}[{i}]", out)
    else:
        if a != b and str(a) != str(b):
            out.append({"path": path, "kind": "value",
                        "pub": a, "repro": b})
    return out


result = {"files": {}, "ledger": {}, "series": {}, "report": {}}

# ---- JSON outputs: byte compare, then modulo-wallclock compare ----------
for f in JSON_FILES:
    pub_b = (PRE / f).read_bytes()
    rep_b = (POST / f).read_bytes()
    entry = {"sha256_published": sha_bytes(pub_b),
             "sha256_repro": sha_bytes(rep_b),
             "byte_identical": pub_b == rep_b}
    pub, _ = strip_wallclock(json.loads(pub_b))
    rep, stripped = strip_wallclock(json.loads(rep_b))
    entry["wallclock_fields_stripped"] = sorted(set(stripped))
    if canon(pub) == canon(rep):
        entry["match_modulo_wallclock"] = True
        entry["differences_substantive"] = 0
        entry["differences_wallclock"] = len(set(stripped))
    else:
        entry["match_modulo_wallclock"] = False
        diffs = deep_diff(json.loads(pub_b), json.loads(rep_b))
        wc = [d for d in diffs
              if d["path"].rsplit(".", 1)[-1] == "created_utc"]
        sub = [d for d in diffs
               if d["path"].rsplit(".", 1)[-1] != "created_utc"]
        entry["differences_wallclock"] = len(wc)
        entry["differences_substantive"] = len(sub)
        entry["substantive_detail"] = sub[:80]
    result["files"][f] = entry

# ---- scored_dryrun.json: known sequence fields --------------------------
dry = result["files"]["scored_dryrun.json"]
pub_dry = json.loads((PRE / "scored_dryrun.json").read_bytes())
rep_dry = json.loads((POST / "scored_dryrun.json").read_bytes())
seq_fields = {}
for fld in ("ledger_sha256_before",):
    seq_fields[fld] = {"published": pub_dry.get(fld),
                       "repro": rep_dry.get(fld)}
seq_fields["replay.ledger_sha256_after"] = {
    "published": pub_dry["replay_zero_denominator_delta"]
    ["ledger_sha256_after"],
    "repro": rep_dry["replay_zero_denominator_delta"]["ledger_sha256_after"]}
# ledger_unchanged must be True in both (each run's own before==after)
seq_fields["replay.ledger_unchanged"] = {
    "published": pub_dry["replay_zero_denominator_delta"]["ledger_unchanged"],
    "repro": rep_dry["replay_zero_denominator_delta"]["ledger_unchanged"]}
result["dryrun_sequence_fields"] = seq_fields

# ---- series files: byte compare ------------------------------------------
for f in SERIES:
    pub_b = (PRE / f).read_bytes()
    rep_b = (POST / f).read_bytes()
    result["series"][f] = {"byte_identical": pub_b == rep_b,
                           "sha256_published": sha_bytes(pub_b),
                           "sha256_repro": sha_bytes(rep_b)}

# ---- ledger --------------------------------------------------------------
pre_lines = (PRE / "trial_ledger.jsonl").read_text().splitlines()
post_lines = (POST / "trial_ledger.jsonl").read_text().splitlines()
n_appended = len(post_lines) - len(pre_lines)
prefix_ok = post_lines[:len(pre_lines)] == pre_lines
pub_rows = pre_lines[-14:]
rep_rows = post_lines[-n_appended:] if n_appended >= 0 else []
pub_digests = sorted(sha_bytes(r.encode()) for r in pub_rows)
rep_digests = sorted(sha_bytes(r.encode()) for r in rep_rows)
pairwise = all(p == r for p, r in zip(pub_rows, rep_rows))
result["ledger"] = {
    "published_lines": len(pre_lines),
    "post_run_lines": len(post_lines),
    "rows_appended_by_repro": n_appended,
    "append_only_prefix_preserved": prefix_ok,
    "scored_rows_order_independent_digest_match":
        pub_digests == rep_digests,
    "scored_rows_pairwise_in_order_match": pairwise,
}

# ---- report --------------------------------------------------------------
pub_rep = (PRE / "SCORED_REPORT.md").read_text().splitlines()
rep_rep = (POST / "SCORED_REPORT.md").read_text().splitlines()
diff_lines = []
for i, (x, y) in enumerate(zip(pub_rep, rep_rep)):
    if x != y:
        diff_lines.append({"line": i + 1, "published": x, "repro": y})
wc_only = all("Generated:" in d["published"] for d in diff_lines) and \
    len(diff_lines) <= 2
result["report"] = {
    "byte_identical": (PRE / "SCORED_REPORT.md").read_bytes()
    == (POST / "SCORED_REPORT.md").read_bytes(),
    "differing_lines": diff_lines,
    "wallclock_only": wc_only and bool(diff_lines) is False or wc_only,
}

# ---- key number cross-check (gates/seam/kills/dsr, pub vs repro) ---------
pub_dev = strip_wallclock(json.loads(
    (PRE / "scored_dev_cells.json").read_bytes()))[0]
rep_dev = strip_wallclock(json.loads(
    (POST / "scored_dev_cells.json").read_bytes()))[0]
cross = {}
for pair in ("AUDUSD", "USDCAD"):
    pd_, rd_ = pub_dev["pairs"][pair], rep_dev["pairs"][pair]
    cross[pair] = {
        "status_equal": pd_["status"] == rd_["status"],
        "anchor_gates_equal": pd_["anchor_gates"] == rd_["anchor_gates"],
        "seam_equal": pd_["seam"] == rd_["seam"],
        "kills_equal": pd_["kills"] == rd_["kills"],
        "fired_equal": pd_["fired"] == rd_["fired"],
        "cells_equal": pd_["cells"] == rd_["cells"],
        "power_gate_equal": pd_["power_gate"] == rd_["power_gate"],
        "anchor_status": pd_["status"]["status"],
        "terminal_label": pd_["status"]["terminal_label"],
        "seam_S": pd_["seam"]["S_net_pips"],
        "fired": pd_["fired"],
    }
result["cross_check"] = cross

verdict = "ALL_MATCH"
for f in JSON_FILES:
    e = result["files"][f]
    if not e["match_modulo_wallclock"] or e["differences_substantive"]:
        verdict = "MISMATCH"
for f in SERIES:
    if not result["series"][f]["byte_identical"]:
        verdict = "MISMATCH"
lg = result["ledger"]
if not (lg["append_only_prefix_preserved"]
        and lg["scored_rows_order_independent_digest_match"]
        and lg["rows_appended_by_repro"] == 14):
    verdict = "MISMATCH"
rep_r = result["report"]
if rep_r["differing_lines"] and not all(
        "Generated:" in d["published"] for d in rep_r["differing_lines"]):
    verdict = "MISMATCH"
result["VERDICT"] = verdict
print(json.dumps(result, indent=1, default=str))
