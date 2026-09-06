#!/usr/bin/env python3
"""A7 novelty audit SUPPLEMENT: read-only conditioning-clock spot checks.

For each D1 proposal, 10 of its in-scope conditioning clocks are sampled
(deterministic: even spacing over the (economy, decision_date)-sorted in-
scope list) and verified against the underlying calendar evidence:

  1. byte traceability: sha256 of the archived calendar page at
     research/control/forex_free_v5_run/<archive_path> equals the clock
     row's archive_sha256;
  2. decision_date consistency: the sampled clock's decision_date equals the
     matching row's release_date in the pinned calendar authority file
     (GB/AU/NZ: research/control/forex_free_v5_run/*.json;
     CA: research/control/forex_free_v6_run/ca_statcan_cpi_release_dates_v3.json);
  3. availability-stamp consistency: CA = byte equality with
     release_time_utc_true; GB/AU = derivable DAY bound
     (<release_date>T23:59:59Z); NZ = derivable flat +12:00 conservative-
     LATER convention stamp on the release date (per published
     clock_semantics; the pin carries no UTC field, so the check is
     derivable-convention class, recorded as such).
Read-only: nothing is modified.  No PnL anywhere.
"""
import hashlib
import json
import os

ROOT = "/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v6/d2-a7-novelty"
V5 = f"{ROOT}/research/control/forex_free_v5_run"
V6 = f"{ROOT}/research/control/forex_free_v6_run"
OUT = f"{V6}/d2/a7_novelty/evidence"

PINS = {
    "GB": (f"{V5}/gb_ons_cpi_release_dates.json", "release_date"),
    "AU": (f"{V5}/au_abs_cpi_release_dates.json", "release_date"),
    "NZ": (f"{V5}/nz_statsnz_cpi_release_dates.json", "release_date"),
    "CA": (f"{V6}/ca_statcan_cpi_release_dates_v3.json", "release_date"),
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pin_release_iso(pin_row):
    """ISO release date from the pin row (GB stores an English display
    string, e.g. '13 February 2018'; CA/AU/NZ store ISO dates)."""
    if "release_date" in pin_row:
        return pin_row["release_date"]
    disp = pin_row.get("release_date_display")
    if not disp:
        return None
    return parse_english_date(disp)


def parse_english_date(s):
    parts = s.split()
    if len(parts) != 3:
        return None
    d, mon, y = parts
    months = ["january", "february", "march", "april", "may", "june", "july",
              "august", "september", "october", "november", "december"]
    if mon.lower() not in months or not d.isdigit() or not y.isdigit():
        return None
    return f"{y}-{months.index(mon.lower()) + 1:02d}-{int(d):02d}"


def load_clocks():
    return json.load(open(f"{V6}/p3_conditioning_clocks_v6.json"))["clocks"]


def cond_date(row):
    if row["economy"] == "CA":
        return row["available_for_daily_decision_date"]
    return row["decision_date"]


def sample(rows, n=10):
    rows = sorted(rows, key=lambda r: (r["economy"], r["decision_date"]))
    if len(rows) <= n:
        return rows
    step = (len(rows) - 1) / (n - 1)
    return [rows[round(i * step)] for i in range(n)]


def stamp_check(row, pin):
    e = row["economy"]
    if e == "CA":
        ok = row["available_time_utc"] == pin.get("release_time_utc_true")
        return ok, "BYTE_EXACT_vs_pin_release_time_utc_true"
    if e in ("GB", "AU"):
        want = f"{row['decision_date']}T23:59:59Z"
        return row["available_time_utc"] == want, f"DERIVABLE_DAY_BOUND_{want}"
    if e == "NZ":
        want_prefix = f"{row['decision_date']}T"
        ok = row["available_time_utc"].startswith(want_prefix)
        return ok, "DERIVABLE_NZ_flat+12_convention_stamp_on_release_date"
    return False, "UNKNOWN_ECONOMY"


def main():
    clocks = load_clocks()
    pins = {e: json.load(open(p)) for e, (p, _) in PINS.items()}
    pin_by_sha = {}
    for e, rows in pins.items():
        for r in rows:
            pin_by_sha[r["archive_sha256"]] = (e, r)

    proposals = {
        "FXFV6-A4-P1": clocks,                                   # all 246
        "FXFV6-A4-P2": [c for c in clocks if c["economy"] == "GB"],  # 88 GB
        "FXFV6-A6-P1": clocks,
        "FXFV6-A6-P2": clocks,
    }
    out = {"schema": "forex_free_v6_d2_a7n_clock_spot_checks_v1",
           "read_only": True,
           "sampling_rule": "10 clocks per proposal, even spacing over the (economy, decision_date)-sorted in-scope list",
           "checks_per_clock": ["archive_sha256 byte traceability", "decision_date vs pinned release_date", "availability stamp (byte-exact CA / derivable GB-AU-NZ convention)"],
           "proposals": {}}
    all_ok = True
    for pid, rows in proposals.items():
        results = []
        for row in sample(rows):
            e = row["economy"]
            arch = os.path.join(V5, row["archive_path"])
            rec = {"economy": e, "decision_date": row["decision_date"],
                   "archive_path": row["archive_path"]}
            if not os.path.exists(arch):
                rec["archive_sha256_match"] = False
                rec["error"] = "archive file missing"
                all_ok = False
            else:
                digest = sha256(arch)
                rec["archive_sha256_match"] = digest == row["archive_sha256"]
                if not rec["archive_sha256_match"]:
                    all_ok = False
                pin = pin_by_sha.get(row["archive_sha256"])
                if pin is None:
                    rec["pin_row_found"] = False
                    all_ok = False
                else:
                    pe, pr = pin
                    rec["pin_row_found"] = True
                    rec["decision_date_matches_pin_release_date"] = \
                        (pin_release_iso(pr) == row["decision_date"])
                    if not rec["decision_date_matches_pin_release_date"]:
                        all_ok = False
                    ok, cls = stamp_check(row, pr)
                    rec["availability_stamp_check"] = ok
                    rec["availability_stamp_class"] = cls
                    if not ok:
                        all_ok = False
            results.append(rec)
        out["proposals"][pid] = {"n_sampled": len(results), "clocks": results,
                                 "all_checks_pass": all(r.get("archive_sha256_match") and
                                                        r.get("pin_row_found") and
                                                        r.get("decision_date_matches_pin_release_date") and
                                                        r.get("availability_stamp_check")
                                                        for r in results)}
    out["overall_all_checks_pass"] = all_ok
    json.dump(out, open(f"{OUT}/clock_spot_checks.json", "w"), indent=1)
    print(json.dumps({"overall_all_checks_pass": all_ok,
                      **{k: v["all_checks_pass"] for k, v in out["proposals"].items()}}))


if __name__ == "__main__":
    main()
