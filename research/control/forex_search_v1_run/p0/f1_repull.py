"""F1(iii) bounded TD re-pull cross-check — fail-closed contract (§4 F1).

The contract is frozen (step `freeze`) BEFORE any pull (step `pull`); the
pull step verifies the contract file exists and pins its sha256 into the
result. Vendor unreachable or diverging => the outcome is recorded
honestly; the P-13 archive vintage REMAINS THE AUTHORITY — never silently
merged, never patched. Bounded: exactly one request per leg, outputsize=60.

The API key is read from the environment file by NAME only and is never
echoed, logged or committed (F2).
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/forex-search-v1/integration")
ROOT = Path("/Users/hoangminhlong/my-quantitative")
P0 = WT / "research/control/forex_search_v1_run/p0"
STAGING = Path("/tmp/fsearch_p0_staging")

PAIRS = {
    "EURUSD": ("EUR/USD", "data_raw/forex_ng4_spot/EURUSD.json"),
    "GBPUSD": ("GBP/USD", "data_raw/forex_free_v9_spot/GBPUSD.json"),
    "USDCAD": ("USD/CAD", "data_raw/forex_free_v9_spot/USDCAD.json"),
    "AUDUSD": ("AUD/USD", "data_raw/forex_free_v9_spot/AUDUSD.json"),
    "NZDUSD": ("NZD/USD", "data_raw/forex_free_v9_spot/NZDUSD.json"),
}
SAMPLE_N = 60


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def freeze() -> int:
    contract = {
        "schema": "f1_repull_contract@1",
        "frozen_before_pull": True,
        "purpose": "F1(iii) bounded TD re-pull cross-check under a fail-closed "
                   "contract frozen BEFORE the pull (plan §4 F1)",
        "sample_rule": f"archive sample = the {SAMPLE_N} most recent dates per "
                       f"leg in the pinned staging file; fresh sample = one "
                       f"TD time_series 1day request per leg, outputsize="
                       f"{SAMPLE_N}, as served at pull time",
        "boundedness": "exactly 5 requests (one per leg), no chunking, no "
                       "other endpoints, no other symbols; XAUUSD excluded",
        "comparison_rule": "field-by-field exact STRING equality of "
                           "datetime/open/high/low/close for every date in "
                           "the intersection of the two samples; per-leg "
                           "verdict IDENTITY | DIVERGENCE | NO_OVERLAP | "
                           "VENDOR_UNREACHABLE",
        "authority_law": "the P-13 single-vintage archive REMAINS THE "
                         "AUTHORITY regardless of outcome; divergence is "
                         "recorded honestly and NEVER silently merged or "
                         "patched; unreachable vendor => sub-step NOT_RUN, "
                         "honestly recorded",
        "key_handling": "TWELVE_DATA_API_KEY read from the environment file by "
                        "name only; value never echoed, logged or committed",
        "entitlement_basis": "owner Twelve Data entitlement, V8/V9/NG5/NG6/NG7 "
                             "precedent (F2)",
    }
    (P0 / "f1_repull_contract.json").write_text(
        json.dumps(contract, indent=1, sort_keys=True) + "\n")
    print(f"[repull] contract frozen sha={sha256_file(P0 / 'f1_repull_contract.json')[:16]}",
          flush=True)
    return 0


def _fetch(url: str):
    req = urllib.request.Request(
        url, headers={"User-Agent": "my-quantitative-research/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:  # noqa: BLE001 — recorded, not raised
        return -1, str(e).encode()


def pull() -> int:
    contract_p = P0 / "f1_repull_contract.json"
    if not contract_p.exists():
        print("[repull] FATAL: contract not frozen before pull", flush=True)
        return 2
    key = next(l.split("=", 1)[1].strip()
               for l in (ROOT / ".env").read_text().splitlines()
               if l.startswith("TWELVE_DATA_API_KEY="))

    sys.path.insert(0, str(WT))
    from research.governance import heavy_lock
    result = {
        "schema": "f1_repull_result@1",
        "contract_sha256": sha256_file(contract_p),
        "heavy_lock": True,
        "legs": {},
        "authority_note": "archive vintage remains THE authority; no merge",
    }
    ok_all = True
    with heavy_lock.acquire(
        cycle_id="FOREX-SEARCH-V1",
        role="P0_F1_REPULL",
        worktree=str(WT),
        command=[sys.executable, str(Path(__file__).resolve()), "pull"],
        expected_artifacts=[str(P0 / "f1_repull_result.json")],
    ):
        for leg in sorted(PAIRS):
            symbol, member = PAIRS[leg]
            url = ("https://api.twelvedata.com/time_series"
                   f"?symbol={symbol}&interval=1day&outputsize={SAMPLE_N}"
                   f"&apikey={key}&format=JSON")
            st, body = _fetch(url)
            rec: dict = {"symbol": symbol, "http_status": st}
            if st != 200:
                rec["verdict"] = "VENDOR_UNREACHABLE"
                rec["detail"] = f"status={st}"
                ok_all = False
            else:
                try:
                    payload = json.loads(body)
                    vals = payload["values"]
                except Exception as e:  # noqa: BLE001
                    rec["verdict"] = "VENDOR_UNREACHABLE"
                    rec["detail"] = f"schema/parse error: {type(e).__name__}"
                    ok_all = False
                    result["legs"][leg] = rec
                    continue
                fresh = {v["datetime"]: v for v in vals}
                arch_rows = json.loads((STAGING / member).read_text())["values"]
                arch = {r["datetime"]: r for r in arch_rows}
                sample = sorted(arch.keys())[-SAMPLE_N:]
                inter = sorted(set(sample) & set(fresh))
                diffs = []
                for d in inter:
                    for fld in ("open", "high", "low", "close"):
                        if arch[d][fld] != fresh[d].get(fld):
                            diffs.append({"date": d, "field": fld,
                                          "archive": arch[d][fld],
                                          "fresh": fresh[d].get(fld)})
                rec["archive_sample_dates"] = len(sample)
                rec["intersection_dates"] = len(inter)
                rec["diff_count"] = len(diffs)
                rec["diffs_first20"] = diffs[:20]
                if not inter:
                    rec["verdict"] = "NO_OVERLAP"
                    ok_all = False
                elif diffs:
                    rec["verdict"] = "DIVERGENCE"
                    # F-4 remediation (A7): the summary flag must flip on
                    # DIVERGENCE too — previously only VENDOR_UNREACHABLE /
                    # NO_OVERLAP cleared ok_all, so a five-leg DIVERGENCE
                    # outcome shipped with any_divergence_or_unreachable
                    # false, contradicting its own per-leg evidence.
                    ok_all = False
            result["legs"][leg] = rec
            print(f"[repull] {leg}: {rec['verdict']} "
                  f"(intersection={rec.get('intersection_dates')}, "
                  f"diffs={rec.get('diff_count')})", flush=True)
            time.sleep(1.0)  # bounded, polite pacing
    result["any_divergence_or_unreachable"] = not ok_all
    P0.mkdir(parents=True, exist_ok=True)
    (P0 / "f1_repull_result.json").write_text(
        json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(f"[repull] result written sha={sha256_file(P0 / 'f1_repull_result.json')[:16]}",
          flush=True)
    return 0


def rederive() -> int:
    """F-4 remediation: OFFLINE re-derivation of the summary fields of the
    ALREADY-RECORDED per-leg evidence — NO network, NO re-pull. Per-leg
    records are kept byte-identical; only the summary flag is recomputed
    from the per-leg verdicts and a correction disclosure is added."""
    path = P0 / "f1_repull_result.json"
    result = json.loads(path.read_text())
    legs = result["legs"]
    verdicts = [v.get("verdict") for v in legs.values()]
    any_divergence = any(v == "DIVERGENCE" for v in verdicts)
    any_unreachable = any(v == "VENDOR_UNREACHABLE" for v in verdicts)
    any_no_overlap = any(v == "NO_OVERLAP" for v in verdicts)
    prior_flag = result.get("any_divergence_or_unreachable")
    corrected_flag = bool(any_divergence or any_unreachable or any_no_overlap)
    result["any_divergence_or_unreachable"] = corrected_flag
    result["f4_correction"] = {
        "schema": "f1_repull_f4_correction@1",
        "corrected_utc_source": "research/control/forex_search_v1_run/"
                                "d1/remediation_note.md (fsearch-"
                                "remediation-r2, A7 finding F-4)",
        "mode": "OFFLINE re-derivation from the already-recorded per-leg "
                "evidence; no network, no re-pull; per-leg records "
                "byte-identical to the originally recorded pull",
        "law": "summary flags are now DERIVED fields, recomputed from the "
               "per-leg verdicts (the single source of truth); the archive "
               "vintage remains THE authority and divergence stays recorded, "
               "never merged",
        "prior_any_divergence_or_unreachable": prior_flag,
        "corrected_any_divergence_or_unreachable": corrected_flag,
        "recomputed_from": {
            "per_leg_verdicts": dict(sorted(
                (k, v.get("verdict")) for k, v in legs.items())),
            "any_divergence": any_divergence,
            "any_vendor_unreachable": any_unreachable,
            "any_no_overlap": any_no_overlap,
        },
    }
    path.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(f"[repull] F-4 rederivation: per-leg verdicts {verdicts} -> "
          f"any_divergence_or_unreachable {prior_flag} -> {corrected_flag}")
    return 0


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "pull"
    sys.exit({"freeze": freeze, "pull": pull,
              "rederive": rederive}[mode]())
