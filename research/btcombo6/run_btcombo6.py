#!/usr/bin/env python3
"""BTC-COMBO6-SCORED-V1 CLI.

Usage (cwd = cycle worktree root):
  python research/btcombo6/run_btcombo6.py --mode dry
  python research/btcombo6/run_btcombo6.py --mode scored   # A1 only, under
                                                          # the heavy lock

--mode dry   : sanitized artifact only (counts/digests/replay proof); exits
               non-zero if any banned substring (pnl, profit_factor,
               equity, win_rate, drawdown, expectancy, return) appears
               anywhere in the emitted JSON, or if the in-process replay is
               not byte-identical.
--mode scored: full scored artifacts per stress tier + TRIAL_LEDGER rows.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_BTCombo6_DIR = Path(__file__).resolve().parent          # .../research/btcombo6
_WORKTREE_ROOT = _BTCombo6_DIR.parents[1]                # .../integration
if str(_WORKTREE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WORKTREE_ROOT))

from research.btcombo6 import combo, spec  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="run_btcombo6")
    ap.add_argument("--mode", required=True, choices=["dry", "scored"])
    ap.add_argument("--worktree-root", default=str(_WORKTREE_ROOT))
    args = ap.parse_args(argv)
    root = Path(args.worktree_root)

    if args.mode == "dry":
        import time
        t0 = time.time()
        payload = combo.build_dry(root)
        if not payload["replay_ok"]:
            print("DRY FAIL: replay digests differ — non-deterministic "
                  "computation", file=sys.stderr)
            return 3
        violations = payload["banned_key_scan"]["violations"]
        if violations:
            print(f"DRY FAIL: banned substrings in payload: {violations}",
                  file=sys.stderr)
            return 2
        out_dir = root / spec.DRY_DIR_REL
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "btcombo6_dry.json"
        out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        legs = payload["legs"]
        print(f"dry OK -> {out_path}")
        print(f"corpus_digest={payload['corpus_digest']}")
        for leg in spec.LEG_IDS:
            b = legs[leg]
            print(f"  {leg} {b['family']:16s} clock={b['clock']:3s} "
                  f"decisions={b['decision_count']:7d} "
                  f"enter={b['enter_signal_count']:5d} "
                  f"trades={b['total_trades']:4d} "
                  f"deferred={b['entries_deferred']:3d} "
                  f"expired={b['entries_expired_at_fold_boundary']:3d} "
                  f"non_vacuous={b['non_vacuous']}")
        print(f"replay identical={payload['replay']['identical']} "
              f"({payload['replay']['first_digest'][:12]}...)")
        print(f"elapsed={time.time() - t0:.1f}s")
        return 0

    if args.mode == "scored":
        payloads = combo.build_scored_payloads(root)
        written = combo.write_scored_artifacts(root, payloads)
        ledger = combo.update_ledger(root, payloads)
        for stress in spec.STRESS_TIERS:
            p = payloads[stress]
            print(f"scored stress={stress} -> {written[stress]} "
                  f"content_sha256={p['content_sha256'][:16]}... "
                  f"combo_net={p['combo']['metrics']['net_pnl']:.2f}")
        print(f"ledger -> {ledger}")
        return 0

    ap.error(f"unknown mode {args.mode}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
