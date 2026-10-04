"""REFUSE-TO-RUN evaluation skeleton (NBA-WINPROB-PREP-V1, budget 0 scored).

Any scored/evaluated outcome on real data is forbidden in this cycle by law:
the owner's 2026-10-04 directive is explicitly NOT a typed GO, and the cycle
registers no GO phrase with budget max = 0. This script therefore refuses to
evaluate unless presented with a freeze manifest from the successor scored
cycle NBA-WINPROB-SCORED-V1 that carries: its own cycle_id, a freeze sha,
the inherited protocol digest, and the owner GO record reference. Exit code 3
on refusal.
"""
from __future__ import annotations

import argparse
import json
import sys

REQUIRED_MANIFEST_FIELDS = ("cycle_id", "freeze_sha", "protocol_digest", "go_record_ref")
ALLOWED_CYCLE = "NBA-WINPROB-SCORED-V1"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", help="normalized games.csv (unused until unlocked)")
    ap.add_argument("--freeze-manifest", help="freeze manifest JSON from the scored cycle")
    ap.add_argument("--dry-run-fixtures", action="store_true",
                    help="run synthetic fixtures only (no real data)")
    args = ap.parse_args()

    if args.dry_run_fixtures:
        print("DRY-RUN-FIXTURES: synthetic only; no real-data evaluation. OK.")
        return 0

    if not args.freeze_manifest:
        print(
            "REFUSED: no --freeze-manifest. NBA-WINPROB-PREP-V1 has budget 0 scored cells "
            "and no GO phrase by law (owner directive 2026-10-04 is explicitly NOT a typed "
            "GO). Evaluation on real outcomes is NOT_RUN in this cycle. Register "
            "NBA-WINPROB-SCORED-V1, inherit lanes/C_protocol/PROTOCOL_EVAL.md sections 2-6 "
            "and 9 verbatim, freeze, pass A7, and have the owner type the GO phrase at that "
            "cycle's own gate.",
            file=sys.stderr,
        )
        return 3

    try:
        with open(args.freeze_manifest, encoding="utf-8") as f:
            m = json.load(f)
    except Exception as e:  # noqa: BLE001
        print(f"REFUSED: unreadable freeze manifest: {e}", file=sys.stderr)
        return 3

    if m.get("cycle_id") != ALLOWED_CYCLE:
        print(f"REFUSED: manifest cycle_id {m.get('cycle_id')!r} != {ALLOWED_CYCLE!r}", file=sys.stderr)
        return 3
    missing = [k for k in REQUIRED_MANIFEST_FIELDS if not m.get(k)]
    if missing:
        print(f"REFUSED: freeze manifest missing {missing}", file=sys.stderr)
        return 3

    print(
        "STUB: scored execution body is intentionally NOT implemented in this PREP "
        "cycle; the successor cycle implements the frozen 9-arm walk-forward per "
        "lanes/C_protocol/PROTOCOL_EVAL.md. Nothing was evaluated."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
