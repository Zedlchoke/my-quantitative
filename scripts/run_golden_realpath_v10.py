#!/usr/bin/env python3
"""V10-H2 gate H-12 / H08 item 19: REAL-PATH golden across two fixture roots.

Extracts a pinned 15m-bar slice ONCE (byte copy) from the read-only V9
production catalog into a temp fixture root, then materializes TWO
independent byte-copy fixture roots (A and B) and drives the DETERMINISTIC
signal core of both V9 engines through the repo's own loaders
(``research.panel.build_daily_closes`` / ``research.v9_vol_shock.load_daily_dollar_volume``)
against each root. Outputs are serialized canonically (sorted keys, fixed
separators, explicit dtype repr) and compared by sha256:

  * root A vs root B   (same invocation)
  * repetition 1 vs 2  (same root, repeated invocation)

No portfolio / scored machinery is exercised; this is an explicitly
unscored deterministic resource probe (PLAN.md section 6). Read-only with
respect to results/**, catalog_live_crypto/** and data/**.

Exit code 0 iff verdict == PASS.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
import time
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research.panel import _bar_type_dir, _day_boundaries, parse_iso_ns  # noqa: E402
from research.v9_ts_trend import DAY_NS, compute_targets as ts_trend_targets  # noqa: E402
from research.v9_vol_shock import (  # noqa: E402
    compute_targets as vol_shock_targets,
    load_daily_dollar_volume,
)

GATE = "H-12"
SOURCE_CATALOG_DEFAULT = "/Users/hoangminhlong/my-quantitative/catalog_live_crypto"
UNIVERSE_MANIFEST = REPO_ROOT / "data/v9_manifests/universe_selection_v9.json"
WINDOW_END_DEFAULT = "2025-08-21T00:00:00Z"  # V9 selection-window end / S0 start
DAYS_DEFAULT = 30
MIN_HISTORY_DAYS = 22  # VOLSHOCK needs 21 strictly-before obs; TS-TREND 14+1


def sha256_file(path: Path) -> tuple[int, str]:
    h = hashlib.sha256()
    n = 0
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            n += len(chunk)
            h.update(chunk)
    return n, h.hexdigest()


def default_symbols(n: int = 2) -> list[str]:
    payload = json.loads(UNIVERSE_MANIFEST.read_text())
    names = sorted(str(e["symbol"]) for e in payload["selected_symbols"])
    return names[:n]


def extract_slice(source_catalog: Path, symbols: list[str],
                  staging: Path) -> list[dict]:
    """Byte-copy each symbol's bar parquet parts into staging ONCE."""
    pins: list[dict] = []
    for sym in symbols:
        src_dir = _bar_type_dir(source_catalog, sym)
        dst_dir = staging / "data" / "binance_bar" / src_dir.name
        dst_dir.mkdir(parents=True, exist_ok=True)
        files = sorted(src_dir.rglob("*.parquet"))
        if not files:
            raise RuntimeError(f"no parquet parts under {src_dir}")
        for f in files:
            nb, digest = sha256_file(f)
            shutil.copyfile(f, dst_dir / f.name)
            cb, cd = sha256_file(dst_dir / f.name)
            if (nb, digest) != (cb, cd):
                raise RuntimeError(f"byte-copy integrity failure: {f}")
            pins.append({"symbol": sym, "relpath": f"data/binance_bar/{src_dir.name}/{f.name}",
                         "bytes": nb, "sha256": cd})
    return pins


def materialize_roots(staging: Path, base: Path) -> tuple[Path, Path]:
    root_a = base / "fixture_root_A"
    root_b = base / "fixture_root_B"
    shutil.copytree(staging, root_a)
    shutil.copytree(staging, root_b)
    return root_a, root_b


# --------------------------- canonical serialization ---------------------- #
def canonical(obj) -> str:
    """Deterministic token stream with explicit dtype repr."""
    if obj is None:
        return "null"
    if isinstance(obj, bool):
        return f"bool:{obj}"
    if isinstance(obj, int):
        return f"i64:{obj}"
    if isinstance(obj, float):
        return f"f64:{float(obj)!r}"
    if isinstance(obj, str):
        return f"str:{obj}"
    if isinstance(obj, (list, tuple)):
        return "[" + ",".join(canonical(x) for x in obj) + "]"
    if isinstance(obj, dict):
        keys = sorted(obj)
        return "{" + ",".join(f"{canonical(k)}:{canonical(obj[k])}" for k in keys) + "}"
    raise TypeError(f"non-canonicalizable type {type(obj)!r}")


def digest(obj) -> str:
    return hashlib.sha256(canonical(obj).encode("utf-8")).hexdigest()


# ------------------------------ engine drives ----------------------------- #
def run_engine_realpath(engine: str, catalog_path: Path,
                        symbols: list[str], ws_iso: str, we_iso: str,
                        cutoffs_ns: list[int]) -> dict:
    """Deterministic signal core driven through the repo's own loaders."""
    from research.panel import build_daily_closes

    daily_closes = build_daily_closes(catalog_path, symbols, ws_iso, we_iso)
    n_closes = sum(len(v) for v in daily_closes.values())
    if n_closes == 0:
        raise RuntimeError("loader returned zero daily closes (vacuous input)")

    books: dict[str, dict] = {}
    if engine == "TS-TREND":
        for c in cutoffs_ns:
            books[str(c)] = ts_trend_targets(
                daily_closes=daily_closes, signal_cutoff_ns=c,
                traded_symbols=symbols)
    elif engine == "VOLSHOCK":
        dollar_volume = {
            s: load_daily_dollar_volume(str(catalog_path), s, ws_iso, we_iso)
            for s in symbols
        }
        n_dv = sum(len(v) for v in dollar_volume.values())
        if n_dv == 0:
            raise RuntimeError("loader returned zero dollar-volume observations")
        for c in cutoffs_ns:
            books[str(c)] = vol_shock_targets(
                daily_closes=daily_closes, dollar_volume=dollar_volume,
                signal_cutoff_ns=c, traded_symbols=symbols)
    else:
        raise ValueError(f"unknown engine {engine!r}")
    return {"books": books,
            "input_obs": {"daily_closes_total": n_closes,
                          "daily_closes_per_symbol": {s: len(daily_closes.get(s) or [])
                                                      for s in sorted(symbols)}}}


# ---------------------------------- main ---------------------------------- #
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--symbols", nargs="+", default=None,
                    help="default: first two alphabetically in the V9 universe")
    ap.add_argument("--days", type=int, default=DAYS_DEFAULT)
    ap.add_argument("--out", type=Path,
                    default=REPO_ROOT / "research/audits/v10/a10_golden_realpath_report.json")
    ap.add_argument("--source-catalog", type=Path, default=Path(SOURCE_CATALOG_DEFAULT))
    args = ap.parse_args(argv)

    t0 = time.monotonic()
    symbols = args.symbols or default_symbols()
    symbols = sorted(dict.fromkeys(symbols))
    we_ns = parse_iso_ns(WINDOW_END_DEFAULT)
    ws_ns = we_ns - int(args.days) * DAY_NS
    ws_iso = datetime.fromtimestamp(ws_ns / 1e9, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    we_iso = WINDOW_END_DEFAULT
    boundaries = _day_boundaries(ws_ns, we_ns)
    cutoffs_ns = [c for c in boundaries if c - ws_ns >= MIN_HISTORY_DAYS * DAY_NS]

    limitations: list[str] = [
        "Sliced 30-day pinned window ending 2025-08-21T00:00:00Z (V9 selection-window "
        "end), i.e. well before S0 end 2026-08-21T00:00:00Z - NOT the full scored window.",
        "Two of ten V9-universe symbols (first two alphabetically), not the full universe.",
        "Signal core only: no portfolio construction, scoring, funding or execution machinery.",
        "Whole parquet parts are byte-copied; the production loaders apply the window filter "
        "by ts_event exactly as in the V9 runs (slice semantics live in loader arguments).",
        "Fixture roots are temporary and removed after the run; identity is pinned via "
        "recorded per-file sha256 digests.",
    ]

    result: dict = {
        "gate": GATE,
        "scope": "real_path_sliced",
        "engines": ["TS-TREND", "VOLSHOCK"],
        "input_pins": {
            "source_catalog_readonly": str(args.source_catalog),
            "real_bar_layout_note": (
                "instrument bars live directly under "
                "<catalog>/data/binance_bar/<INSTRUMENT>-15-MINUTE-LAST-EXTERNAL/*.parquet; "
                "the <catalog>/data/crypto_perpetual tree holds instrument metadata"),
            "universe_manifest": str(UNIVERSE_MANIFEST.relative_to(REPO_ROOT)),
            "symbol_selection_rule": "first two alphabetically among selected_symbols",
            "symbols": symbols,
            "window_start_utc": ws_iso,
            "window_end_utc": we_iso,
            "days": int(args.days),
            "signal_cutoffs_utc": [
                datetime.fromtimestamp(c / 1e9, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                for c in cutoffs_ns],
            "files": [],
        },
        "output_sha256_per_engine_per_root": {},
        "byte_identical": False,
        "verdict": "FAIL",
        "runtime_seconds": None,
        "limitations": limitations,
    }

    tmp_base = Path(tempfile.mkdtemp(prefix="a10_golden_realpath_"))
    try:
        pins = extract_slice(args.source_catalog, symbols, tmp_base / "staging")
        result["input_pins"]["files"] = pins

        # Independent roots: verify B's bytes match A's recorded digests.
        root_a, root_b = materialize_roots(tmp_base / "staging", tmp_base)
        for p in pins:
            _, da = sha256_file(root_a / p["relpath"])
            _, db = sha256_file(root_b / p["relpath"])
            if not (da == db == p["sha256"]):
                raise RuntimeError(f"root byte divergence for {p['relpath']}")
        result["input_pins"]["fixture_roots"] = {
            "A": str(root_a), "B": str(root_b),
            "root_byte_identical": True,
        }

        table: dict[str, dict] = {}
        identical = True
        detail: dict[str, dict] = {}
        for engine in ("TS-TREND", "VOLSHOCK"):
            reps: dict[str, dict[str, str]] = {}
            meta: dict[str, dict] = {}
            for rep in ("rep1", "rep2"):
                for root_name, root in (("rootA", root_a), ("rootB", root_b)):
                    out = run_engine_realpath(engine, root, symbols, ws_iso, we_iso, cutoffs_ns)
                    reps.setdefault(rep, {})[root_name] = digest(out)
                    meta[f"{rep}:{root_name}"] = out["input_obs"]
            uniq = {d for r in reps.values() for d in r.values()}
            same_roots = reps["rep1"]["rootA"] == reps["rep1"]["rootB"] \
                and reps["rep2"]["rootA"] == reps["rep2"]["rootB"]
            same_reps = reps["rep1"]["rootA"] == reps["rep2"]["rootA"] \
                and reps["rep1"]["rootB"] == reps["rep2"]["rootB"]
            identical = identical and (len(uniq) == 1)
            table[engine] = {
                "sha256_rep1_rootA": reps["rep1"]["rootA"],
                "sha256_rep1_rootB": reps["rep1"]["rootB"],
                "sha256_rep2_rootA": reps["rep2"]["rootA"],
                "sha256_rep2_rootB": reps["rep2"]["rootB"],
                "identical_across_roots": same_roots,
                "identical_across_repetitions": same_reps,
            }
            detail[engine] = meta
        result["output_sha256_per_engine_per_root"] = table
        result["input_observation_counts"] = detail
        result["byte_identical"] = bool(identical)
        result["verdict"] = "PASS" if identical else "FAIL"
    except Exception as exc:  # fail closed, never fake PASS
        result["verdict"] = "UNAVAILABLE_FAIL_CLOSED"
        result["byte_identical"] = False
        result["blocker"] = {
            "exception_type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(limit=8),
        }
    finally:
        result["runtime_seconds"] = round(time.monotonic() - t0, 3)
        shutil.rmtree(tmp_base, ignore_errors=True)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2,
                                   separators=(",", ":")) + "\n")

    print(json.dumps({k: result[k] for k in
                      ("gate", "scope", "verdict", "byte_identical",
                       "runtime_seconds")}, sort_keys=True))
    for eng, t in result["output_sha256_per_engine_per_root"].items():
        print(f"{eng}: {t['sha256_rep1_rootA']} identical={t['identical_across_roots']}"
              f"/{t['identical_across_repetitions']}")
    if result["verdict"] == "UNAVAILABLE_FAIL_CLOSED":
        print("BLOCKER:", result["blocker"]["message"], file=sys.stderr)
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
