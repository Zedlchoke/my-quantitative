"""G5 comparison: lane_x books vs lane I decision books (records only).

Protocol (dispatch P4):
  (a) event key sets per arm — identity, Jaccard, diff lists;
  (b) field-level comparison on the intersection — direction/entry/exit
      sessions + prices (+ direction_session, delisting flags);
  (c) each mismatch classified SPEC_AMBIGUITY (traceable to a logged
      ambiguity) / SPEC_AMBIGUITY_UNLOGGED (found at comparison) /
      DEFECT / DATA_VARIANT;
  (d) no aggregate of trade returns is computed anywhere (R2-6) —
      set statistics and per-record field diffs only.

Event-key normalization (recorded in COMPARISON_REPORT.md):
  A1 arms: (cik, acceptance_utc)              [R2-3 identity]
  A2 anchor: lane_x (cik, transaction_date)   [my issuer-day basis, AMB-04 note]
             lane I (cik, acceptance-UTC-date) [their issuer-day basis]

Run: .venv/bin/python -m compare.build_comparison  (from lane_x/)
"""

from __future__ import annotations

import gzip
import json
import os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
LANE_X = os.path.dirname(HERE)
WT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(LANE_X))))
ENGINE_EV = os.path.join(WT_ROOT, "research", "control", "EVENT-MECHANISMS-V1",
                         "engine", "evidence")
OUT = os.path.join(LANE_X, "compare")


def read_jsonl_gz(path: str):
    with gzip.open(path, "rt") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def load_mine(name: str) -> list[dict]:
    return list(read_jsonl_gz(os.path.join(LANE_X, "output", name)))


def load_theirs(name: str, arm_id: str) -> list[dict]:
    return [r for r in read_jsonl_gz(os.path.join(ENGINE_EV, name))
            if r.get("arm_id") == arm_id and r.get("control_variant") == "PRIMARY"]


def a1_key(r: dict) -> tuple[str, str]:
    return (r["cik"], r["acceptance_utc"])


def a2_key_mine(r: dict) -> tuple[str, str]:
    return (r["cik"], r["transaction_date"])


def a2_key_theirs(r: dict) -> tuple[str, str]:
    return (r["cik"], r["acceptance_utc"][:10])


DIR_MAP = {"LONG": 1, "SHORT": -1}


def price_eq(a, b) -> bool:
    if a is None or b is None:
        return a is b
    return abs(float(a) - float(b)) <= 1e-9


def jaccard(a: set, b: set) -> float:
    u = a | b
    return len(a & b) / len(u) if u else 1.0


def compare_arm(arm_label, mine_rows, their_rows, key_mine, key_theirs):
    m_by_key = {}
    for r in mine_rows:
        m_by_key.setdefault(key_mine(r), []).append(r)
    t_by_key = {}
    for r in their_rows:
        t_by_key.setdefault(key_theirs(r), []).append(r)
    ks_m, ks_t = set(m_by_key), set(t_by_key)
    inter = ks_m & ks_t
    res = {
        "arm": arm_label,
        "mine_records": len(mine_rows),
        "theirs_records": len(their_rows),
        "mine_unique_keys": len(ks_m),
        "theirs_unique_keys": len(ks_t),
        "mine_multi_record_keys": sum(1 for v in m_by_key.values() if len(v) > 1),
        "intersection": len(inter),
        "only_lane_x": len(ks_m - ks_t),
        "only_lane_i": len(ks_t - ks_m),
        "jaccard": round(jaccard(ks_m, ks_t), 6),
        "key_sets_identical": ks_m == ks_t,
    }

    fields = ["direction_session", "direction", "entry_session", "entry_price",
              "exit_session", "exit_price", "delisting_exit", "fold",
              "stratum", "hold_sessions"]
    mism = {f: [] for f in fields}
    for key in sorted(inter):
        m = m_by_key[key][0]
        t = t_by_key[key][0]
        t_dir = DIR_MAP.get(t.get("direction"), t.get("direction"))
        checks = {
            "direction_session": (m.get("direction_session"), t.get("direction_session")),
            "direction": (m.get("direction"), t_dir),
            "entry_session": (m.get("entry_session"), t.get("entry_session")),
            "entry_price": (m.get("entry_price"), t.get("entry_price")),
            "exit_session": (m.get("exit_session"), t.get("exit_session")),
            "exit_price": (m.get("exit_price"), t.get("exit_price")),
            "delisting_exit": (bool(m.get("delisting_exit")), bool(t.get("delisting_exit"))),
            "fold": (m.get("fold"), t.get("fold")),
            "stratum": (m.get("stratum"), t.get("stratum")),
            "hold_sessions": (m.get("hold_sessions"), t.get("hold_sessions")),
        }
        for f, pair in checks.items():
            a, b = pair
            same = price_eq(a, b) if f.endswith("_price") else (a == b)
            if not same:
                mism[f].append({
                    "key": list(key),
                    "lane_x": a,
                    "lane_i": b,
                    "their_forced_flat": t.get("forced_flat"),
                    "their_delisting_exit": t.get("delisting_exit"),
                    "my_delisting_exit": m.get("delisting_exit"),
                    "my_exit_notes": m.get("exclusions_applied"),
                    "their_exclusions": t.get("exclusions_applied"),
                })

    res["field_mismatch_counts"] = {f: len(v) for f, v in mism.items()}
    res["field_mismatch_samples"] = {
        f: sorted(v, key=lambda r: r["key"])[:25] for f, v in mism.items() if v
    }
    res["intersection_identical_all_fields"] = all(len(v) == 0 for v in mism.values())
    return res, mism, m_by_key, t_by_key


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    results = {}
    full = {}

    arms = [
        ("A1_anchor", load_mine("A1_anchor_book.jsonl.gz"),
         load_theirs("a1_decisions.jsonl.gz", "A1-ANCHOR"), a1_key, a1_key),
        ("A1_N2", load_mine("A1_N2_book.jsonl.gz"),
         load_theirs("a1_decisions.jsonl.gz", "A1-N2"), a1_key, a1_key),
        ("A2_anchor", load_mine("A2_anchor_book.jsonl.gz"),
         load_theirs("a2_decisions.jsonl.gz", "A2-ANCHOR"), a2_key_mine, a2_key_theirs),
    ]
    for label, m, t, km, kt in arms:
        res, mism, m_by_key, t_by_key = compare_arm(label, m, t, km, kt)
        results[label] = res
        full[label] = mism
        print(label, json.dumps({k: v for k, v in res.items()
                                 if k != "field_mismatch_samples"}, sort_keys=True))

    with open(os.path.join(OUT, "comparison_results.json"), "w") as fh:
        json.dump(results, fh, sort_keys=True, indent=1)
        fh.write("\n")
    with open(os.path.join(OUT, "field_mismatches_full.json"), "w") as fh:
        slim = {arm: {f: rows for f, rows in mism.items() if rows}
                for arm, mism in full.items()}
        json.dump(slim, fh, sort_keys=True, indent=1)
        fh.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
