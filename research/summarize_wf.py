"""Summarize walk-forward optimizer cell results."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


def load_cells(directory: str) -> pd.DataFrame:
    rows: list[dict] = []
    for path in Path(directory).glob("cells*.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    return pd.DataFrame(rows)


def report(name: str, directory: str) -> None:
    df = load_cells(directory)
    if df.empty:
        print(f"{name}: no cells")
        return

    print("=" * 72)
    print(f"{name} | cells={len(df)} | combos={df['params'].apply(lambda p: tuple(sorted(p.items()))).nunique()}")

    best_group = None
    best_exp = float("-inf")
    for _, group in df.groupby(df["params"].apply(lambda p: tuple(sorted(p.items())))):
        weights = group["trades"].clip(lower=1)
        exp = float((group["expectancy"] * weights).sum() / weights.sum())
        if exp > best_exp:
            best_exp = exp
            best_group = group

    assert best_group is not None
    params = dict(best_group["params"].iloc[0])
    print(f"Best combo: {params}")
    print("Per symbol x fold:")
    for symbol in sorted(best_group["symbol"].unique()):
        sub = best_group[best_group["symbol"] == symbol].sort_values("window")
        print(f"  {symbol}:")
        for _, row in sub.iterrows():
            print(
                f"    F{int(row['window'])} "
                f"exp={row['expectancy']:+.3f} "
                f"PF={row['profit_factor']:.2f} "
                f"n={int(row['trades'])}",
            )

    fold_exp = best_group.groupby("window")["expectancy"].mean()
    sym_exp = best_group.groupby("symbol")["expectancy"].mean()
    print(
        "  Fold avg expectancy:",
        ", ".join(f"F{i}={v:+.3f}" for i, v in fold_exp.items()),
    )
    print(
        "  Symbol avg expectancy:",
        ", ".join(f"{s}={v:+.3f}" for s, v in sym_exp.items()),
    )
    n_pos_folds = int((fold_exp > 0).sum())
    all_sym_pos = bool((sym_exp > 0).all())
    print(
        f"  Positive folds: {n_pos_folds}/{len(fold_exp)} | "
        f"All symbols positive: {all_sym_pos}",
    )


def main() -> None:
    dirs = sys.argv[1:] or [
        "results/optimize/mr_wf3_adx",
        "results/optimize/ema_wf3",
    ]
    labels = {
        "results/optimize/mr_wf3_adx": "MEAN REVERSION (VHF+ADX+volume)",
        "results/optimize/ema_wf3": "EMA_ATR",
    }
    for d in dirs:
        report(labels.get(d, d), d)


if __name__ == "__main__":
    main()
