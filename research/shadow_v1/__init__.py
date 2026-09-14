"""PROSPECTIVE-SHADOW-V1 internal paper-trading engine (shared infrastructure).

Scope (plan PLAN_prospective_shadow_v1.md, phase I / lane A2):
- events.py     per-event append-only record contract (plan section 8)
- ledger.py     atomic append-only JSONL virtual ledgers
- accounting.py isolated 100,000-USDT sleeve accounting with two cost books
- risk.py       frozen pre-fill caps (no margin, no leverage)
- scheduler.py  exact decision clocks + idempotent run loop
- data_feed.py  PIT data interface + keyless public REST client
- no_order.py   TARGET_INTENT emission + forbidden-surface scanner
- combined.py   read-only equal-capital combined view
- executor.py   PRODUCTION forward executor (condition C1)
- start_guard.py forward-only start guard + ledger namespace
                separation (condition C2)

This engine is INTERNAL_PAPER_ONLY: no API key, no account, no order
routing. The only emitted action type is TARGET_INTENT plus internal
virtual fills. No broker, testnet or live connection exists anywhere in
this package.
"""

__all__ = [
    "events",
    "ledger",
    "accounting",
    "risk",
    "scheduler",
    "data_feed",
    "no_order",
    "combined",
    "executor",
    "start_guard",
]
