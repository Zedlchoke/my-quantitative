"""REFUSE-TO-RUN evaluation stub (NFL-WINPROB-PREP-V1, budget 0 scored).

Scored evaluation on real outcomes is forbidden in this cycle: the owner's
NFL directive 2026-10-04 is explicitly NOT a typed GO. The successor cycle
NFL-WINPROB-SCORED-V1 must be registered (inheriting PROTOCOL_EVAL_NFL.md),
frozen, A7-audited, and the owner must type at that cycle's own gate:

    GO NFL WINPROB SCORED V1 EVALUATION
"""
from __future__ import annotations

import argparse
import sys


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--anything", nargs="*", default=[])
    ap.parse_args(argv)
    print(
        "REFUSED: NFL-WINPROB-PREP-V1 has budget 0 scored cells and no GO phrase "
        "(owner NFL directive 2026-10-04 is explicitly NOT a typed GO). Evaluation "
        "on real outcomes is NOT_RUN in this cycle. Register NFL-WINPROB-SCORED-V1, "
        "inherit lanes/NFL_C_protocol/PROTOCOL_EVAL_NFL.md, freeze, A7, then owner "
        "types 'GO NFL WINPROB SCORED V1 EVALUATION' at that cycle's own gate.",
        file=sys.stderr,
    )
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
