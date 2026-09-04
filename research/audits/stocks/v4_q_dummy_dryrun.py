"""V4-Q A1 dummy dry-run: six arms, temp ledger, scored=false everywhere.

Produces NO scored metrics and NO real PnL. Verifies:
- six arm configs build and their canonical digests are pairwise unique
- dummy publication increments observed exactly once per arm, replay zero-delta
- zero-position refusal path works
- canonical ledger untouched
- staged data manifest + benchmark pins unchanged
- budget stays 0/6 with zero real scored artifacts
"""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from research.assets.stocks.factory import GatedTrialLedger  # noqa: E402
from research.stocks_free_v4.family_participation import config as pconfig  # noqa: E402
from research.stocks_free_v4.family_semivar import config as sconfig  # noqa: E402

STAGING = Path(
    "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v2/z8-exec-1/.staging"
)
AUTHORIZED_MANIFEST_SHA = (
    "62ac324d7e683961b0d88f85153e4a072d09fe0a6745a54687b9e3b219d8f658"
)
CONTROL = REPO / "research" / "control" / "stocks_free_v4_run"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    findings: dict = {
        "schema": "stocks_free_v4_run/q_dummy_dryrun@1",
        "producer_role": "A1",
        "scored": False,
        "real_pnl": False,
        "checks": {},
    }

    # 1. six arm configs + pairwise-unique digests
    p_arms = pconfig.build_arm_configs()
    s_arms = sconfig.build_arm_configs()
    arms = list(p_arms.values()) + list(s_arms.values())
    p_digests = pconfig.arm_config_digests()
    s_digests = sconfig.arm_config_digests()
    all_digests = list(p_digests.values()) + list(s_digests.values())
    ids = [a.arm_id for a in arms]
    assert len(arms) == 6, f"expected 6 arms, got {len(arms)}"
    assert len(set(ids)) == 6, f"arm ids not unique: {ids}"
    assert len(set(all_digests)) == 6, "arm config digests not pairwise unique"
    findings["checks"]["six_arms"] = {
        "PASS": True,
        "arm_ids": ids,
        "digests_unique": True,
        "digests": dict(zip(ids, all_digests)),
    }

    # 2. dummy publication into a TEMP ledger only
    canonical_ledger = CONTROL / "event_log.jsonl"
    canonical_before = sha256_file(canonical_ledger)
    with tempfile.TemporaryDirectory() as td:
        tmp_ledger = Path(td) / "dummy_ledger.json"
        ledger = GatedTrialLedger(str(tmp_ledger))
        recorded_digests: dict[str, str] = {}
        publish_results: dict[str, bool] = {}
        replay_results: dict[str, bool] = {}
        for arm in arms:
            dummy_artifact = {
                "schema": "stocks_free_v4_run/dummy_cell@1",
                "arm_id": arm.arm_id,
                "config_digest": all_digests[ids.index(arm.arm_id)],
                "scored": False,
                "real_pnl": False,
                "note": "V4-Q dummy dry-run; no scored metrics computed",
            }
            canonical_bytes = json.dumps(
                dummy_artifact, sort_keys=True, separators=(",", ":")
            ).encode()
            expected_digest = hashlib.sha256(canonical_bytes).hexdigest()
            # observed increments exactly once per arm BEFORE publication
            ledger.compute_recorded(arm.arm_id)
            published = ledger.publish(arm.arm_id, dummy_artifact)
            # publish appends the artifact-digest entry, then the touch event
            digest_entry = ledger.entries[-2]
            assert ledger.entries[-1]["event"] == "FIRST_PUBLICATION"
            recorded_digests[arm.arm_id] = digest_entry["artifact_digest"]
            # digest must hash the exact canonical artifact bytes (P1 lesson)
            assert recorded_digests[arm.arm_id] == expected_digest, (
                f"ledger digest != canonical artifact bytes for {arm.arm_id}"
            )
            publish_results[arm.arm_id] = published
            # identical replay must be zero-delta
            replay_results[arm.arm_id] = ledger.publish(arm.arm_id, dummy_artifact)
        observed_once = ledger.observed == 6
        published_once = len(ledger.published_keys) == 6
        replays_refused = all(r is False for r in replay_results.values())
        findings["checks"]["dummy_publication"] = {
            "PASS": bool(observed_once and published_once and replays_refused),
            "observed": ledger.observed,
            "published": len(ledger.published_keys),
            "replay_all_zero_delta": replays_refused,
            "digest_equals_artifact_bytes": True,
            "temp_ledger_path": str(tmp_ledger),
        }

        # 3. zero-result refusal path (gate refuses zero fills/positions)
        refused_ok = True
        try:
            refused_ok = (
                ledger.publish_result(
                    "DUMMY-ZERO-RESULT",
                    {"schema": "stocks_free_v4_run/dummy_cell@1", "scored": False},
                    n_fill_events=0,
                    n_held_positions=0,
                )
                is False
            )
            refused_ok = refused_ok and (
                "DUMMY-ZERO-RESULT" not in ledger.published_keys
            )
        except Exception:
            refused_ok = False
        findings["checks"]["refusal_path"] = {
            "PASS": bool(refused_ok),
            "key_remains_unpublished": "DUMMY-ZERO-RESULT"
            not in ledger.published_keys,
        }

    canonical_after = sha256_file(canonical_ledger)
    findings["checks"]["canonical_ledger_untouched"] = {
        "PASS": canonical_before == canonical_after,
        "sha256": canonical_after,
    }

    # 4. data + benchmark authority pins
    manifest_sha = sha256_file(STAGING / "MANIFEST.json")
    findings["checks"]["data_manifest_pin"] = {
        "PASS": manifest_sha == AUTHORIZED_MANIFEST_SHA,
        "measured": manifest_sha,
        "authorized": AUTHORIZED_MANIFEST_SHA,
    }
    bm = json.loads((CONTROL / "p2_a3_benchmark_contract.json").read_text())
    findings["checks"]["benchmark_contract"] = {
        "PASS": bm.get("status") == "FROZEN",
        "status": bm.get("status"),
    }

    # 5. budget 0/6 and zero real scored artifacts in control tree
    state = json.loads((CONTROL / "state.json").read_text())
    budget_ok = state["budget"]["used"] == 0 and state["budget"]["planned"] == 6
    scored_files = [
        p.name
        for p in CONTROL.glob("*.json")
        if "cell" in p.name.lower() or "artifact_digest" in p.name.lower()
    ]
    findings["checks"]["budget_and_artifacts"] = {
        "PASS": bool(budget_ok and not scored_files),
        "budget": state["budget"],
        "scored_artifact_files_in_control": scored_files,
    }

    all_pass = all(c.get("PASS") is True for c in findings["checks"].values())
    findings["overall"] = "PASS" if all_pass else "FAIL"
    out = CONTROL / "q_dummy_dryrun_evidence.json"
    out.write_text(json.dumps(findings, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"overall": findings["overall"], "out": str(out)}, indent=1))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
