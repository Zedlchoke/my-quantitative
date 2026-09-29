"""BTC-COMBO6-SCORED-V1 lane IMPL package.

Six owner-pinned bot legs (plan plans/PLAN_btc_combo6_scored_v1.md §1),
one equal-weight 6-sleeve portfolio, PIT fill law, pessimistic TP/SL,
measured funding, 10x26w Monday-aligned walk-forward folds F1..F10.

Modules:
- spec.py     frozen constants (single source of truth, no CLI overrides)
- data.py     Binance Vision 5m zip loader + digest/manifest court + funding
- signals.py  per-leg decision frames at the leg's clock (no lookahead)
- engine.py   per-leg event backtest, baselines B0/B1/B3, metrics, verdicts
- combo.py    orchestration: dry (sanitized) and scored payloads
- run_btcombo6.py  CLI (--mode dry | scored)
"""
__all__ = ["spec", "data", "signals", "engine", "combo"]
