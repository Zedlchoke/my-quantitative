"""Compact markdown status report over local result artifacts (no network).

Scans ``results/`` (forward_test/, scan_matrix/) and ``research_snapshots/``
(tradfi universe snapshots), picks the newest artifact per category and renders
one small markdown table: mục | ngày | chỉ số chính | trạng thái.

Root resolution: explicit argument wins, otherwise the local ``results/`` of
this checkout is preferred and the main repo copy is used as fallback (final
artifacts are copied back to the main repo per PLAN.md).
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MAIN_REPO_ROOT = Path("/Users/hoangminhlong/my-quantitative")

MAX_FORWARD_TEST_ROWS = 6

Row = tuple[str, str, str, str]


def _read_json(path: Path) -> Any:
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None


def _num(value: Any, digits: int = 2) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "?"


def _date_from_stem(stem: str) -> str | None:
    matches = re.findall(r"\d{8}", stem)
    if not matches:
        return None
    raw = matches[-1]
    return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"


def _mtime_date(path: Path) -> str:
    ts = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return ts.strftime("%Y-%m-%d")


def _best_date(*candidates: str | None) -> str:
    for value in candidates:
        if value:
            return value
    return "?"


def _forward_test_rows(results_root: Path) -> list[Row]:
    directory = results_root / "forward_test"
    if not directory.is_dir():
        return []
    paths = sorted(directory.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    rows: list[Row] = []
    for path in paths[:MAX_FORWARD_TEST_ROWS]:
        data = _read_json(path)
        if not isinstance(data, dict):
            continue
        symbol = data.get("symbol", "?")
        strategy = data.get("strategy_type", "?")
        muc = f"Forward-test {symbol} ({strategy})"
        ngay = _best_date(
            str(data.get("window_end", ""))[:10],
            _date_from_stem(path.stem),
            _mtime_date(path),
        )
        chi_so = (
            f"Trades {data.get('trades', '?')}"
            f" · Exp {_num(data.get('expectancy'))}"
            f" · PF {_num(data.get('profit_factor'))}"
        )
        trang_thai = "PASS OOS" if data.get("passes_oos") else "FAIL OOS"
        rows.append((muc, ngay, chi_so, trang_thai))
    return rows


def _scan_matrix_row(results_root: Path) -> Row | None:
    base = results_root / "scan_matrix"
    if not base.is_dir():
        return None
    reports = [
        child / "report.json"
        for child in sorted(base.iterdir())
        if child.is_dir() and (child / "report.json").is_file()
    ]
    if not reports:
        return None
    latest = max(reports, key=lambda p: (p.parent.name, p.stat().st_mtime))
    entries = _read_json(latest)
    label = f"Scan matrix {latest.parent.name}"
    ngay = _best_date(_date_from_stem(latest.parent.name), _mtime_date(latest))
    if not isinstance(entries, list) or not entries:
        return (label, ngay, "report.json rỗng/lỗi", "KIỂM TRA")
    total = len(entries)
    scored = [
        entry
        for entry in entries
        if isinstance(entry, dict)
        and float(entry.get("exp_after") or 0) > 0
        and float(entry.get("pf_after") or 0) >= 1.2
    ]

    def _pf(entry: dict[str, Any]) -> float:
        try:
            return float(entry.get("pf_after") or 0)
        except (TypeError, ValueError):
            return 0.0

    best = max((entry for entry in entries if isinstance(entry, dict)), key=_pf)
    muc = f"{label} ({total} combos)"
    chi_so = (
        f"Tốt nhất: {best.get('symbol', '?')} {best.get('strategy_type', '?')}"
        f" · Exp {_num(best.get('exp_after'))}"
        f" · PF {_num(best.get('pf_after'))}"
        f" · folds {best.get('positive_folds_after', '?')}"
    )
    trang_thai = f"{len(scored)}/{total} đạt gate (Exp>0 & PF>=1.2)"
    return (muc, ngay, chi_so, trang_thai)


def _tradfi_row(snapshots_root: Path) -> Row | None:
    if not snapshots_root.is_dir():
        return None
    paths = sorted(
        snapshots_root.glob("binance_tradfi_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not paths:
        return None
    path = paths[0]
    data = _read_json(path)
    muc = "TradFi snapshot (USD-M universe)"
    ngay = _best_date(_date_from_stem(path.stem), _mtime_date(path))
    if not isinstance(data, dict):
        return (muc, ngay, "snapshot lỗi", "KIỂM TRA")
    eligible = data.get("eligible_count")
    total = data.get("total_contracts")
    chi_so = f"Đủ điều kiện {eligible}/{total} hợp đồng"
    ok = isinstance(eligible, int) and eligible > 0
    return (muc, ngay, chi_so, "OK" if ok else "KIỂM TRA")


def _has_any_category(results_root: Path) -> bool:
    return (results_root / "forward_test").is_dir() or (results_root / "scan_matrix").is_dir()


def resolve_results_root(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit)
    candidates = [PROJECT_ROOT / "results", MAIN_REPO_ROOT / "results"]
    for candidate in candidates:
        if candidate.is_dir() and _has_any_category(candidate):
            return candidate
    return candidates[0]


def resolve_snapshots_root(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit)
    candidates = [PROJECT_ROOT / "research_snapshots", MAIN_REPO_ROOT / "research_snapshots"]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return candidates[0]


def collect_rows(
    results_root: str | Path | None = None,
    snapshots_root: str | Path | None = None,
) -> list[Row]:
    res = resolve_results_root(str(results_root) if results_root else None)
    snap = resolve_snapshots_root(str(snapshots_root) if snapshots_root else None)
    rows: list[Row] = []
    rows.extend(_forward_test_rows(res))
    scan_row = _scan_matrix_row(res)
    if scan_row:
        rows.append(scan_row)
    tradfi_row = _tradfi_row(snap)
    if tradfi_row:
        rows.append(tradfi_row)
    return rows


def render_table(rows: list[Row]) -> str:
    headers = ("mục", "ngày", "chỉ số chính", "trạng thái")
    body = list(rows) or [("—", "—", "—", "chưa có artifact")]
    widths = [
        max(len(headers[i]), *(len(r[i]) for r in body))
        for i in range(len(headers))
    ]

    def fmt(cells: tuple[str, ...]) -> str:
        return "| " + " | ".join(c.ljust(widths[i]) for i, c in enumerate(cells)) + " |"

    sep = "| " + " | ".join("-" * w for w in widths) + " |"
    return "\n".join([fmt(headers), sep, *(fmt(r) for r in body)])


def build_status_table(
    results_root: str | Path | None = None,
    snapshots_root: str | Path | None = None,
) -> str:
    return render_table(collect_rows(results_root, snapshots_root))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Print compact markdown status of latest result artifacts.",
    )
    parser.add_argument("--results-root", default=None, help="Override results/ directory")
    parser.add_argument(
        "--snapshots-root",
        default=None,
        help="Override research_snapshots/ directory",
    )
    args = parser.parse_args(argv)
    print(build_status_table(args.results_root, args.snapshots_root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
