"""V13 P2 -- data authority replay (fail-closed, read-only, NO downloads).

Authority
---------
* ``PLAN_crypto_v13.md`` section 6 P2: replay every authorized dataset without
  downloading -- exact hashes, window coverage INCLUDING TAIL COMPLETENESS
  (G05 lesson: coverage must fail closed, never synthesize a stale tail),
  funding/OI/mark availability stamps expressed as fusion records, benchmark
  context availability, S0 folds and purge, and S1 never listed, opened,
  hashed or copied.
* ``research/control/v13_run/run_contract.json`` (cycle CRYPTO-V13) and
  ``CLAUDE.md``: read-only on all data; gate verdicts only
  PASS / PASS_WITH_BLOCKED_NOTES / FAIL backed by command, exit code, tree
  state and evidence paths.

What this tool does
-------------------
1. Full SHA-256 of every file named by the frozen V12 staging manifest
   (``research/audits/v12p/a3_staging_manifest.json``, 90 files) resolved
   against the frozen V12 data roots
   (``research/control/v12_run/data_manifest.json``); per-file
   OK / MISMATCH / ABSENT.
2. Window coverage per dataset vs the V13 outer window
   2024-08-20T00:00Z..2026-08-21T00:00Z: first/last timestamp on disk, tail
   completeness (a missing tail is a FAIL), internal gap count over the
   authorized blind-S0 window 2025-08-22..2026-08-21, and head gaps reported
   as documented BLOCKED notes (they are the terminal V12 ILLIQ findings;
   nothing is synthesized, extrapolated or fetched).
3. Benchmark context: BTCUSDT bars must cover the authorized window with
   zero missing 15-minute slots.
4. S0 folds / purge: imports the CODE-RESIDENT frozen fold contract
   (``research.v12.families.oilev_v2.strategy`` -- FOLD_WINDOWS /
   PURGE_DAYS / window constants) READ-ONLY and checks bars, funding and OI
   cover each fold plus its purge zone.
5. Availability-stamp sampling: first/middle/last rows of bars, funding
   settlements, OI snapshots and mark-price observations are mapped in
   memory through ``research.data_fusion.crypto_compat`` to fusion records
   with TRUE availability semantics.  The staged OI shape is naive-UTC; the
   compat layer's refusal of that shape is demonstrated first, then the
   frozen loader convention (create_time is UTC) is applied explicitly
   before mapping.  Bar closes are decoded with the frozen CLOSE_DECODE rule
   (raw i128 / 1e16).  No row is invented.
6. S1 GUARD: every manifest path and every enumerated path under the data
   roots is checked for an S1 designator BEFORE any open/hash; a hit is
   reported and skipped untouched.
7. The verified W12 staging archive
   ``~/Downloads/v12-staging-W12-f0799cae.tar.gz`` is SHA-256 verified only
   -- never listed, opened or extracted.

Boundaries: read-only on all data; no downloads; no writes outside
``research/control/v13_run/``; frozen V12 control files untouched.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pyarrow.parquet as pq

# --------------------------------------------------------------------------- #
# paths / frozen inputs
# --------------------------------------------------------------------------- #
TOOL_PATH = Path(__file__).resolve()
WORKTREE = TOOL_PATH.parents[4]  # .../p1-a3-data (tools -> v13_run -> control -> research -> root)
REPO_MAIN = Path("/Users/hoangminhlong/my-quantitative")

STAGING_MANIFEST = WORKTREE / "research/audits/v12p/a3_staging_manifest.json"
DATA_MANIFEST = WORKTREE / "research/control/v12_run/data_manifest.json"
GATE_PATH = WORKTREE / "research/control/v13_run/gates/P2_DATA_AUTHORITY_REPLAY.json"

STAGING_ARCHIVE = REPO_MAIN.parent / "Downloads/v12-staging-W12-f0799cae.tar.gz"
STAGING_ARCHIVE_SHA256 = (
    "dc7608596a74e79629b04f2fb2aca7020569297ed4869159fbbd05d56e4d0ed8"
)

sys.path.insert(0, str(WORKTREE))

from research.data_fusion.crypto_compat import (  # noqa: E402
    AVAILABILITY_SEMANTICS,
    CryptoCompatContext,
    CryptoCompatError,
    map_row,
)
from research.v12.families.oilev_v2 import strategy as fold_contract  # noqa: E402

# --------------------------------------------------------------------------- #
# frozen windows
# --------------------------------------------------------------------------- #
# V13 outer data window (owner brief P2; funding bundle 20240820_20260821;
# evidence: research/wayfinder/evidence/data-snapshot-20260822.md).
WINDOW_START = dt.datetime(2024, 8, 20, tzinfo=dt.timezone.utc)
WINDOW_END = dt.datetime(2026, 8, 21, tzinfo=dt.timezone.utc)
# Authorized blind-S0 / OILEV-V2 window (frozen in the staging manifest).
AUTHORIZED_WINDOW_START = dt.datetime(2025, 8, 22, tzinfo=dt.timezone.utc)
AUTHORIZED_WINDOW_END = dt.datetime(2026, 8, 21, tzinfo=dt.timezone.utc)

SLOT_NS = 900_000_000_000  # 15 minutes
NS = 1_000_000_000
MS = 1_000_000
CLOSE_DECODE_DIVISOR = 1e16  # frozen CLOSE_DECODE: raw i128 / 1e16

# staging-manifest path prefix -> data_manifest data_roots key
ROOT_MAP = {
    "binance_bar_15m": "bars_binance_bar_15m",
    "crypto_perpetual_meta": "instrument_metadata_crypto_perpetual",
    "funding_20240820_20260821": "funding_20240820_20260821",
    "funding_scan_2026": "funding_scan_2026",
    "oi_consolidated": "oi_consolidated",
}
ILLIQ_ONLY_ROOTS = {"funding_20240820_20260821"}  # serves the ILLIQ head only

S1_PATTERN = re.compile(r"(?:^|[^A-Za-z0-9])[Ss]1(?:[^A-Za-z0-9]|$)")

results: dict = {
    "schema": "v13_p2_data_authority_replay_v1",
    "artifact": "P2_DATA_AUTHORITY_REPLAY",
    "cycle": "CRYPTO-V13",
    "phase": "P2",
    "producer_role": "A3",
    "command": " ".join([Path(sys.executable).name, *sys.argv]),
    "tool": str(TOOL_PATH.relative_to(WORKTREE)),
    "windows": {
        "v13_outer": [WINDOW_START.isoformat(), WINDOW_END.isoformat()],
        "authorized_blind_s0": [
            AUTHORIZED_WINDOW_START.isoformat(),
            AUTHORIZED_WINDOW_END.isoformat(),
        ],
    },
}


class Gate:
    """Accumulates verdicts; fail-closed by default."""

    def __init__(self) -> None:
        self.hash_mismatch = 0
        self.absent: list[str] = []
        self.s1_hits: list[str] = []
        self.tail_fail: list[str] = []
        self.coverage_fail: list[str] = []
        self.fold_fail: list[str] = []
        self.stamp_fail: list[str] = []

    @property
    def verdict(self) -> str:
        if self.hash_mismatch or self.s1_hits or self.tail_fail:
            return "FAIL"
        if self.coverage_fail or self.fold_fail or self.stamp_fail:
            return "FAIL"
        if self.absent:
            confined = all(
                any(p.startswith(prefix + "/") for prefix in ILLIQ_ONLY_ROOTS)
                for p in self.absent
            )
            return "PASS_WITH_BLOCKED_NOTES" if confined else "FAIL"
        return "PASS"


gate = Gate()


# --------------------------------------------------------------------------- #
# S1 guard + hashing
# --------------------------------------------------------------------------- #
def s1_check(rel_path: str) -> bool:
    """True iff the path carries an S1 designator (guard BEFORE any open)."""
    return bool(S1_PATTERN.search(rel_path))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve(rel: str, roots: dict) -> Path:
    """Staging-relative path -> on-disk path.

    Staging prefixes (binance_bar_15m, crypto_perpetual_meta, ...) differ
    from the on-disk directory names (binance_bar, crypto_perpetual);
    resolution is data_root + staging suffix.
    """
    prefix = rel.split("/", 1)[0]
    root_key = ROOT_MAP[prefix]
    return Path(roots[root_key]) / rel.split("/", 1)[1]


# --------------------------------------------------------------------------- #
# 1. replay hashes of the frozen staging manifest
# --------------------------------------------------------------------------- #
def step_hashes(manifest: dict, roots: dict) -> dict:
    per_root: dict[str, dict[str, int]] = {}
    files_out: dict[str, str] = {}
    for rel, meta in sorted(manifest["files"].items()):
        prefix = rel.split("/", 1)[0]
        root_key = ROOT_MAP.get(prefix)
        if root_key is None:
            gate.coverage_fail.append(f"unmapped-manifest-prefix:{rel}")
            continue
        counts = per_root.setdefault(
            root_key, {"checked": 0, "ok": 0, "mismatch": 0, "absent": 0}
        )
        if s1_check(rel):
            gate.s1_hits.append(rel)
            files_out[rel] = "S1_GUARD_SKIPPED"
            continue
        counts["checked"] += 1
        path = resolve(rel, roots)
        if not path.exists():
            counts["absent"] += 1
            gate.absent.append(rel)
            files_out[rel] = "ABSENT"
            print(f"  ABSENT  {rel}")
            continue
        digest = sha256_file(path)
        if digest == meta["sha256"]:
            counts["ok"] += 1
            files_out[rel] = "OK"
        else:
            counts["mismatch"] += 1
            gate.hash_mismatch += 1
            files_out[rel] = "MISMATCH"
            print(f"  MISMATCH {rel}")
    results["per_root_hash_counts"] = per_root
    results["per_file_status"] = files_out
    print(
        "hash replay: "
        + ", ".join(
            f"{k}: checked={v['checked']} ok={v['ok']} "
            f"mismatch={v['mismatch']} absent={v['absent']}"
            for k, v in per_root.items()
        )
    )
    return per_root


# --------------------------------------------------------------------------- #
# 2. window coverage incl. tail completeness
# --------------------------------------------------------------------------- #
def snap_slot(ts_ns: int) -> int:
    return ((ts_ns + SLOT_NS - 1) // SLOT_NS) * SLOT_NS


def ns_iso(ts_ns: int) -> str:
    return (
        dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc) + dt.timedelta(microseconds=ts_ns // 1000)
    ).isoformat()


def ns_to_utc(ts_ns: int) -> dt.datetime:
    """Compat-layer availability: ts_event truncated to microseconds."""
    return dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc) + dt.timedelta(
        microseconds=ts_ns // 1000
    )


def bar_slots(symbol_files: list[tuple[str, Path]]) -> dict:
    slots: set[int] = set()
    for _rel, path in symbol_files:
        col = pq.read_table(path, columns=["ts_event"]).column("ts_event").to_pylist()
        slots.update(snap_slot(int(t)) for t in col)
    ordered = sorted(slots)
    start_ns = int(AUTHORIZED_WINDOW_START.timestamp() * NS)
    end_ns = int(AUTHORIZED_WINDOW_END.timestamp() * NS)
    win_slots = set(range(start_ns, end_ns, SLOT_NS))
    outer_start_ns = int(WINDOW_START.timestamp() * NS)
    # slots in [outer_start, first_present) are missing by construction
    outer_missing = max(0, (ordered[0] - outer_start_ns) // SLOT_NS)
    auth_missing = len(win_slots - slots)
    return {
        "first_slot_ns": ordered[0],
        "last_slot_ns": ordered[-1],
        "head_gap_slots_vs_outer_window": outer_missing,
        "authorized_window_missing_slots": auth_missing,
        "slots_in_authorized_window": len(win_slots),
    }


def step_window_coverage(manifest: dict, roots: dict, inventory: dict) -> dict:
    out: dict = {"bars": {}, "funding": {}, "oi": {}, "mark_price": {}}

    # ---- bars ----
    by_symbol: dict[str, list[tuple[str, Path]]] = {}
    for rel in manifest["files"]:
        prefix = rel.split("/", 1)[0]
        if prefix != "binance_bar_15m":
            continue
        sym = rel.split("/")[1].split("-PERP.")[0]
        by_symbol.setdefault(sym, []).append((rel, resolve(rel, roots)))
    end_ns = int(WINDOW_END.timestamp() * NS)
    for sym, files in sorted(by_symbol.items()):
        cov = bar_slots(files)
        tail_ok = cov["last_slot_ns"] >= end_ns
        if not tail_ok:
            gate.tail_fail.append(f"bars:{sym}")
        if cov["authorized_window_missing_slots"]:
            gate.coverage_fail.append(
                f"bars:{sym}:{cov['authorized_window_missing_slots']} slots missing "
                "in authorized window"
            )
        frozen = inventory["inventory"].get(sym, {}).get("bars", {})
        frozen_last = frozen.get("last_completed_bar")
        drift = (
            frozen_last is not None
            # frozen stamps use a 'Z' suffix; normalize before comparing
            and ns_iso(cov["last_slot_ns"]) != frozen_last.replace("Z", "+00:00")
        )
        first_slot = ns_iso(cov.pop("first_slot_ns"))
        last_slot = ns_iso(cov.pop("last_slot_ns"))
        out["bars"][sym] = {
            **cov,
            "first_slot": first_slot,
            "last_slot": last_slot,
            "tail_complete_vs_outer_window": tail_ok,
            "matches_frozen_inventory_last_bar": not drift,
        }
    tails = [v["tail_complete_vs_outer_window"] for v in out["bars"].values()]
    heads = {v["head_gap_slots_vs_outer_window"] for v in out["bars"].values()}
    print(
        f"bars coverage: {len(out['bars'])} symbols, tails_ok={sum(tails)}/{len(tails)}, "
        f"authorized-window missing slots total="
        f"{sum(v['authorized_window_missing_slots'] for v in out['bars'].values())}, "
        f"head-gap slots vs outer window: {sorted(heads)}"
    )

    # ---- funding ----
    funding_roots = {
        "funding_20240820_20260821": Path(roots["funding_20240820_20260821"]),
        "funding_scan_2026": Path(roots["funding_scan_2026"]),
    }
    for root_key, root in funding_roots.items():
        out["funding"][root_key] = {}
        if not root.exists():
            gate.coverage_fail.append(f"funding-root-missing:{root_key}")
            continue
        for sym_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            rel = f"{root_key}/{sym_dir.name}/funding.json"
            if s1_check(rel):
                gate.s1_hits.append(rel)
                continue
            fpath = sym_dir / "funding.json"
            if not fpath.exists():
                gate.absent.append(rel)
                out["funding"][root_key][sym_dir.name] = {"status": "ABSENT"}
                continue
            rows = json.loads(fpath.read_text())["rows"]
            times = [int(r["fundingTime"]) for r in rows]
            first = dt.datetime.fromtimestamp(times[0] / 1000, dt.timezone.utc)
            last = dt.datetime.fromtimestamp(times[-1] / 1000, dt.timezone.utc)
            tail_ok = last >= WINDOW_END
            if not tail_ok:
                gate.tail_fail.append(f"funding:{root_key}:{sym_dir.name}")
            in_auth = sum(
                1
                for t in times
                if AUTHORIZED_WINDOW_START.timestamp() * 1000
                <= t
                < AUTHORIZED_WINDOW_END.timestamp() * 1000
            )
            out["funding"][root_key][sym_dir.name] = {
                "settlements": len(rows),
                "first": first.isoformat(),
                "last": last.isoformat(),
                "tail_complete_vs_outer_window": tail_ok,
                "settlements_in_authorized_window": in_auth,
                "head_gap_hours_vs_outer_window": max(
                    0.0, (first - WINDOW_START).total_seconds() / 3600.0
                ),
            }
    for root_key, syms in out["funding"].items():
        tails = [v.get("tail_complete_vs_outer_window") for v in syms.values()]
        print(
            f"funding {root_key}: {len(syms)} symbols, tails_ok="
            f"{sum(1 for t in tails if t)}/{len(tails)}, last="
            f"{max((v.get('last') or '') for v in syms.values())}"
        )

    # ---- OI ----
    oi_root = Path(roots["oi_consolidated"])
    for p in sorted(oi_root.glob("*_oi.parquet")):
        sym = p.name[: -len("_oi.parquet")]
        rel = f"oi_consolidated/{p.name}"
        if s1_check(rel):
            gate.s1_hits.append(rel)
            continue
        days = sorted(
            {str(d)[:10] for d in pq.read_table(p, columns=["create_time"]).column("create_time").to_pylist()}
        )
        first_d = dt.date.fromisoformat(days[0])
        last_d = dt.date.fromisoformat(days[-1])
        tail_ok = last_d >= WINDOW_END.date()
        if not tail_ok:
            gate.tail_fail.append(f"oi:{sym}")
        auth_start = AUTHORIZED_WINDOW_START.date()
        auth_end = AUTHORIZED_WINDOW_END.date()
        day_set = set(days)
        auth_missing = sum(
            1
            for i in range((auth_end - auth_start).days + 1)
            if (auth_start + dt.timedelta(days=i)).isoformat() not in day_set
        )
        if auth_missing:
            gate.coverage_fail.append(f"oi:{sym}:{auth_missing} days missing in authorized window")
        out["oi"][sym] = {
            "days_present": len(days),
            "first_day": days[0],
            "last_day": days[-1],
            "tail_complete_vs_outer_window": tail_ok,
            "authorized_window_missing_days": auth_missing,
        }
    oi_tails = [v["tail_complete_vs_outer_window"] for v in out["oi"].values()]
    print(
        f"oi coverage: {len(out['oi'])} symbols, tails_ok={sum(oi_tails)}/{len(oi_tails)}, "
        f"first_day={min(v['first_day'] for v in out['oi'].values())}, "
        f"last_day={max(v['last_day'] for v in out['oi'].values())}"
    )

    # ---- mark price ----
    out["mark_price"] = {
        "dedicated_staged_root": None,
        "note": (
            "no dedicated mark-price root exists in the frozen V12 manifest; "
            "mark observations on this host are staged as the markPrice field "
            "of funding settlement rows (sampled in the fusion-stamp step)"
        ),
    }
    results["window_coverage"] = out
    return out


# --------------------------------------------------------------------------- #
# 3. benchmark context
# --------------------------------------------------------------------------- #
def step_benchmark(coverage: dict) -> dict:
    btc = coverage["bars"].get("BTCUSDT")
    ok = bool(
        btc
        and btc["tail_complete_vs_outer_window"]
        and btc["authorized_window_missing_slots"] == 0
    )
    if not ok:
        gate.coverage_fail.append("benchmark:BTCUSDT")
    verdict = {"benchmark_symbol": "BTCUSDT", "complete_over_authorized_window": ok}
    results["benchmark_context"] = verdict
    print(f"benchmark BTCUSDT: complete_over_authorized_window={ok}")
    return verdict


# --------------------------------------------------------------------------- #
# 4. S0 folds / purge (code-resident contract, imported READ-ONLY)
# --------------------------------------------------------------------------- #
def step_folds(manifest: dict, roots: dict, coverage: dict) -> dict:
    folds_out: dict = {
        "contract_source": "research/v12/families/oilev_v2/strategy.py (imported read-only)",
        "purge_days": int(fold_contract.PURGE_DAYS),
        "contract_window": [fold_contract.WINDOW_START_ISO, fold_contract.WINDOW_END_ISO],
        "folds": {},
    }
    slots_by_symbol = _reload_bar_slots(roots)
    for label, start_s, end_s in fold_contract.FOLD_WINDOWS:
        # Fold dates are exclusive boundaries on the same convention as the
        # contract window (2025-08-22T00:00Z..2026-08-21T00:00Z): F0
        # [08-22, 12-22), F1 [12-22, 04-22), F2 [04-22, 08-21).
        f_start = dt.datetime.fromisoformat(start_s).replace(tzinfo=dt.timezone.utc)
        f_end = dt.datetime.fromisoformat(end_s).replace(tzinfo=dt.timezone.utc)
        purge_start = f_end - dt.timedelta(days=folds_out["purge_days"])
        fs_ns, fe_ns = int(f_start.timestamp() * NS), int(f_end.timestamp() * NS)

        # bars: slots present across the fold, incl. the purge zone
        bar_missing = 0
        for sym, slots in slots_by_symbol.items():
            need = set(range(fs_ns, fe_ns, SLOT_NS))
            bar_missing += len(need - slots)

        # funding settlements inside the fold (scan_2026 covers all 20 symbols)
        funding_root = Path(roots["funding_scan_2026"])
        funding_symbols_with_settlements = 0
        for sym_dir in sorted(funding_root.iterdir()):
            if not sym_dir.is_dir():
                continue
            fpath = sym_dir / "funding.json"
            if s1_check(f"funding_scan_2026/{sym_dir.name}/funding.json"):
                gate.s1_hits.append(f"funding_scan_2026/{sym_dir.name}/funding.json")
                continue
            if not fpath.exists():
                continue
            times = [int(r["fundingTime"]) for r in json.loads(fpath.read_text())["rows"]]
            if any(fs_ns // MS <= t < fe_ns // MS for t in times):
                funding_symbols_with_settlements += 1

        # OI days inside the fold
        oi_root = Path(roots["oi_consolidated"])
        oi_days_present = 0
        for p in sorted(oi_root.glob("*_oi.parquet")):
            if s1_check(f"oi_consolidated/{p.name}"):
                gate.s1_hits.append(f"oi_consolidated/{p.name}")
                continue
            days = {
                str(d)[:10]
                for d in pq.read_table(p, columns=["create_time"]).column("create_time").to_pylist()
            }
            cur = f_start.date()
            while cur < f_end.date():
                if cur.isoformat() in days:
                    oi_days_present += 1
                cur += dt.timedelta(days=1)

        complete = bar_missing == 0 and funding_symbols_with_settlements == 20 and oi_days_present > 0
        if not complete:
            gate.fold_fail.append(
                f"fold:{label}:bar_missing={bar_missing},"
                f"funding_syms={funding_symbols_with_settlements},oi_days={oi_days_present}"
            )
        folds_out["folds"][label] = {
            "window": [f_start.isoformat(), f_end.isoformat()],
            "purge_zone": [purge_start.isoformat(), f_end.isoformat()],
            "bars_missing_slots_sum_over_symbols": bar_missing,
            "symbols_with_funding_settlements_in_fold": funding_symbols_with_settlements,
            "oi_symbol_days_present_in_fold": oi_days_present,
            "coverage_complete_incl_purge": complete,
        }
        print(
            f"fold {label} {start_s}..{end_s} (+purge {folds_out['purge_days']}d): "
            f"bars_missing={bar_missing}, funding_syms={funding_symbols_with_settlements}/20, "
            f"oi_days={oi_days_present}, complete={complete}"
        )
    results["s0_folds"] = folds_out
    return folds_out


def _reload_bar_slots(roots: dict) -> dict[str, set[int]]:
    root = Path(roots["bars_binance_bar_15m"])
    out: dict[str, set[int]] = {}
    for sym_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        sym = sym_dir.name.split("-PERP.")[0]
        slots: set[int] = set()
        for pq_file in sorted(sym_dir.glob("*.parquet")):
            rel = f"binance_bar_15m/{sym_dir.name}/{pq_file.name}"
            if s1_check(rel):
                gate.s1_hits.append(rel)
                continue
            col = pq.read_table(pq_file, columns=["ts_event"]).column("ts_event").to_pylist()
            slots.update(snap_slot(int(t)) for t in col)
        out[sym] = slots
    return out


# --------------------------------------------------------------------------- #
# 5. fusion-record availability stamps (sampled, offline, in-memory)
# --------------------------------------------------------------------------- #
def _context(symbol: str, raw_path: str, raw_sha: str) -> CryptoCompatContext:
    return CryptoCompatContext(
        symbol=symbol,
        retrieved_time_utc=dt.datetime.now(dt.timezone.utc),
        raw_path=raw_path,
        raw_sha256=raw_sha,
    )


def _assert_record(rec, symbol: str, expect_available: dt.datetime) -> dict:
    assert rec.entity_id == symbol
    assert rec.available_time_utc == expect_available, (
        rec.available_time_utc,
        expect_available,
    )
    assert rec.event_time_utc == rec.available_time_utc
    assert rec.vintage_time_utc == rec.available_time_utc
    assert rec.effective_time_utc is None
    assert rec.available_time_utc <= rec.retrieved_time_utc
    return {
        "dataset_id": rec.dataset_id,
        "field": rec.field,
        "value": rec.value,
        "unit": rec.unit,
        "available_time_utc": rec.available_time_utc.isoformat(),
    }


def step_fusion_stamps(manifest: dict, roots: dict, file_status: dict) -> dict:
    out: dict = {"semantics": AVAILABILITY_SEMANTICS, "samples": {}}
    rel_hash = {
        rel: meta["sha256"] for rel, meta in manifest["files"].items()
    }

    def rel_path(rel: str) -> Path:
        return resolve(rel, roots)

    def available(rel: str) -> bool:
        return file_status.get(rel) == "OK"

    # ---- bars (BTCUSDT): CLOSE_DECODE raw i128 / 1e16 ----
    bars_rel = sorted(
        rel
        for rel in rel_hash
        if rel.startswith("binance_bar_15m/BTCUSDT-PERP.")
    )
    samples = []
    for rel in bars_rel:
        if not available(rel):
            continue
        table = pq.read_table(rel_path(rel))
        n = table.num_rows
        for idx in (0, n // 2, n - 1):
            row = {k: table.column(k)[idx].as_py() for k in table.schema.names}
            close = int.from_bytes(row["close"], "little", signed=True) / CLOSE_DECODE_DIVISOR
            rec = map_row(
                "bars",
                {"ts_event": int(row["ts_event"]), "close": close},
                _context("BTCUSDT", rel, rel_hash[rel]),
            )
            # compat availability = raw ts_event (close boundary minus ~1ms),
            # NOT the loader's snapped slot boundary
            samples.append(
                _assert_record(rec, "BTCUSDT", ns_to_utc(int(row["ts_event"])))
            )
    out["samples"]["bars"] = samples
    print(f"fusion stamps bars: {len(samples)} rows mapped (BTCUSDT first/middle/last per file)")

    # ---- funding (BTCUSDT scan_2026): native settlement stamps ----
    funding_rel = "funding_scan_2026/BTCUSDT/funding.json"
    samples = []
    if available(funding_rel):
        rows = json.loads(rel_path(funding_rel).read_text())["rows"]
        for row in (rows[0], rows[len(rows) // 2], rows[-1]):
            rec = map_row(
                "funding",
                {"fundingTime": row["fundingTime"], "fundingRate": row["fundingRate"]},
                _context("BTCUSDT", funding_rel, rel_hash[funding_rel]),
            )
            samples.append(
                _assert_record(
                    rec,
                    "BTCUSDT",
                    dt.datetime.fromtimestamp(row["fundingTime"] / 1000, dt.timezone.utc),
                )
            )
    out["samples"]["funding"] = samples
    print(f"fusion stamps funding: {len(samples)} rows mapped (BTCUSDT first/middle/last)")

    # ---- OI (BTCUSDT): naive staged shape refused, then frozen UTC convention ----
    oi_rel = "oi_consolidated/BTCUSDT_oi.parquet"
    samples = []
    refusal_proven = False
    if available(oi_rel):
        table = pq.read_table(rel_path(oi_rel))
        n = table.num_rows
        for idx in (0, n // 2, n - 1):
            raw = {
                "create_time": table.column("create_time")[idx].as_py(),
                "sum_open_interest": table.column("sum_open_interest")[idx].as_py(),
            }
            try:
                map_row("open_interest", dict(raw), _context("BTCUSDT", oi_rel, rel_hash[oi_rel]))
            except CryptoCompatError as exc:
                refusal_proven = "naive" in str(exc)
            stamped = {
                "create_time": str(raw["create_time"]).replace(" ", "T") + "+00:00",
                "sum_open_interest": raw["sum_open_interest"],
            }
            rec = map_row("open_interest", stamped, _context("BTCUSDT", oi_rel, rel_hash[oi_rel]))
            expect = dt.datetime.fromisoformat(stamped["create_time"])
            samples.append(_assert_record(rec, "BTCUSDT", expect))
    out["samples"]["open_interest"] = samples
    out["open_interest_naive_shape_refused_by_compat_layer"] = refusal_proven
    out["open_interest_utc_convention_source"] = (
        "data_manifest loader_conventions ('consolidated daily last-5m rows ... "
        "create_time') -- UTC date stamp; explicit normalization, nothing inferred"
    )
    print(
        f"fusion stamps open_interest: {len(samples)} rows mapped, "
        f"naive-shape refusal proven={refusal_proven}"
    )

    # ---- mark price: staged as markPrice inside funding settlement rows ----
    samples = []
    if available(funding_rel):
        rows = json.loads(rel_path(funding_rel).read_text())["rows"]
        for row in (rows[0], rows[len(rows) // 2], rows[-1]):
            rec = map_row(
                "mark_price",
                {"timestamp": row["fundingTime"], "markPrice": row["markPrice"]},
                _context("BTCUSDT", funding_rel, rel_hash[funding_rel]),
            )
            samples.append(
                _assert_record(
                    rec,
                    "BTCUSDT",
                    dt.datetime.fromtimestamp(row["fundingTime"] / 1000, dt.timezone.utc),
                )
            )
    out["samples"]["mark_price"] = samples
    print(f"fusion stamps mark_price: {len(samples)} rows mapped (funding-row markPrice re-key)")

    ok = (
        len(out["samples"]["bars"]) > 0
        and len(out["samples"]["funding"]) == 3
        and len(out["samples"]["open_interest"]) == 3
        and len(out["samples"]["mark_price"]) == 3
        and refusal_proven
    )
    if not ok:
        gate.stamp_fail.append("fusion-stamp-sampling")
    out["verdict"] = "PASS" if ok else "FAIL"
    results["fusion_stamps"] = out
    print(f"fusion stamp sampling verdict: {out['verdict']}")
    return out


# --------------------------------------------------------------------------- #
# 6. S1 guard sweep over data-root enumerations + archive identity
# --------------------------------------------------------------------------- #
def step_s1_sweep(roots: dict) -> dict:
    scanned = 0
    for key, root in roots.items():
        root = Path(root)
        if s1_check(root.name):
            gate.s1_hits.append(f"data-root:{root}")
            continue
        if root.is_file():
            scanned += 1
            continue
        for dirpath, _dirnames, filenames in os.walk(root):
            for name in filenames:
                scanned += 1
                rel = os.path.relpath(os.path.join(dirpath, name), root.parent)
                if s1_check(rel):
                    gate.s1_hits.append(rel)
    archive_ok = False
    archive_note = "archive not present on this host"
    if STAGING_ARCHIVE.exists():
        digest = sha256_file(STAGING_ARCHIVE)
        archive_ok = digest == STAGING_ARCHIVE_SHA256
        archive_note = (
            "sha256 matches frozen W12 staging authority"
            if archive_ok
            else f"SHA MISMATCH: {digest}"
        )
        if not archive_ok:
            gate.hash_mismatch += 1
    if s1_check(STAGING_ARCHIVE.name):
        gate.s1_hits.append(STAGING_ARCHIVE.name)
    verdict = {
        "s1_guard_verdict": "CLEAN" if not gate.s1_hits else "VIOLATION_REPORTED",
        "paths_scanned": scanned,
        "violations": gate.s1_hits,
        "rule": "S1-named paths are reported and never listed/opened/hashed/copied",
        "staging_archive": {
            "path": str(STAGING_ARCHIVE),
            "sha256_verified_without_extraction": archive_ok,
            "note": archive_note,
        },
    }
    results["s1_guard"] = verdict
    print(f"S1 guard: scanned {scanned} paths, violations={len(gate.s1_hits)}; archive ok={archive_ok}")
    return verdict


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main() -> int:
    manifest = json.loads(STAGING_MANIFEST.read_text())
    data_manifest = json.loads(DATA_MANIFEST.read_text())
    roots = data_manifest["data_roots"]
    assert manifest["files_count"] == len(manifest["files"]) == 90

    print(f"[1/6] SHA-256 replay of {len(manifest['files'])} frozen staging-manifest files")
    per_root = step_hashes(manifest, roots)
    inventory = data_manifest  # frozen A3 inventory + window verdicts

    print("[2/6] window coverage incl. tail completeness")
    coverage = step_window_coverage(manifest, roots, inventory)

    print("[3/6] benchmark context (BTCUSDT bars)")
    step_benchmark(coverage)

    print("[4/6] S0 folds + purge (code-resident contract)")
    step_folds(manifest, roots, coverage)

    print("[5/6] fusion-record availability stamps (sampled, in-memory)")
    step_fusion_stamps(manifest, roots, results["per_file_status"])

    print("[6/6] S1 guard sweep + staging-archive sha (no extraction)")
    step_s1_sweep(roots)

    verdict = gate.verdict
    exit_code = 0 if verdict in ("PASS", "PASS_WITH_BLOCKED_NOTES") else 1
    results["overall_verdict"] = verdict
    results["exit_code"] = exit_code
    results["blocked_notes"] = {
        "absent_files": gate.absent,
        "absent_confined_to_illiq_replication_window": all(
            any(p.startswith(prefix + "/") for prefix in ILLIQ_ONLY_ROOTS)
            for p in gate.absent
        ),
        "illiq_status": "BLOCKED_DATA (unchanged; no fetch, no window substitution)",
        "head_gap_note": (
            "outer-window head gaps (bars ~2-3 days for 20 symbols, funding 32h head "
            "outside the 7-symbol 20240820_20260821 bundle) are the frozen terminal "
            "V12 ILLIQ findings (data_manifest illiq_replication_window.missing); "
            "documented, never synthesized"
        ),
        "mark_price_note": results["window_coverage"]["mark_price"]["note"],
    }
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=WORKTREE, capture_output=True, text=True
    ).stdout.strip()
    results["tree"] = {"worktree": str(WORKTREE), "head": head, "branch": "orca/v13-p1-a3-data"}
    GATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    GATE_PATH.write_text(json.dumps(results, indent=1) + "\n")
    status = subprocess.run(
        ["git", "status", "--porcelain=v1"], cwd=WORKTREE, capture_output=True, text=True
    ).stdout
    results["tree"]["porcelain_at_gate_write"] = status
    GATE_PATH.write_text(json.dumps(results, indent=1) + "\n")
    print(f"gate written: {GATE_PATH}")
    print(f"overall verdict: {verdict} (exit {exit_code})")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
