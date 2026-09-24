"""PROSPECTIVE-SHADOW-V1 near-real MTM valuation worker (ACTIVE_LIGHT).

A SEPARATE process from the strategy scheduler
(``shadow_worker.py``, untouched by this lane): it only OBSERVES the
strategy ledgers read-only and appends near-real mark-to-market marks
every 5 minutes. It NEVER changes strategy identity, signals, sizing,
risk limits, schedule, fees or slippage; it NEVER writes to the
strategy ledgers or to ``results/`` outside its own valuation runtime
subtrees (``valuation_marks/`` + ``runtime/valuation_heartbeat.json``).

ACTIVE_LIGHT contract:

- NEVER acquires the machine-wide heavy lock. The lock is INSPECTED
  each loop through ``research.governance.heavy_lock.inspect()`` and
  the verdict is recorded in the heartbeat (expected FREE_PROVEN);
  there is deliberately no heavy-lock acquire call anywhere in this
  file (grep-proven by tests);
- bounded work per loop: ONE bulk keyless price read (frozen source,
  see ``valuation_config.json``) + one read-only ledger replay +
  one idempotent append per family. No backtests, no history scans;
- single sequential writer to each valuation mark ledger
  (``<runtime_root>/valuation_marks/<family_id>.jsonl``);
- any valuation exception is recorded in the heartbeat ``last_error``
  and the loop continues; this process can never crash the strategy
  scheduler (separate process, no shared mutable state).

INTERNAL PAPER ONLY: keyless public network reads only (Binance fapi
premiumIndex bulk); no credentials of any kind are read, stored or
required; no accounts; no orders — the only action type anywhere in
the cycle remains TARGET_INTENT.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
import re
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Mapping, Optional, Tuple

WORKTREE_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")
)
if WORKTREE_ROOT not in sys.path:
    sys.path.insert(0, WORKTREE_ROOT)

from research.governance import heavy_lock  # noqa: E402  (inspect ONLY)
from research.shadow_v1 import start_guard  # noqa: E402
from research.shadow_v1 import valuation  # noqa: E402
from research.shadow_v1.families import (  # noqa: E402
    FAMILY_BANDRIDGE,
    FAMILY_CARRY,
    FAMILY_ILLIQ,
    FAMILY_PREMFADE,
)

WORKER_SCHEMA = "shv1_valuation_worker@1"
HEARTBEAT_SCHEMA = "shv1_valuation_worker_heartbeat@1"

#: Same FIXED family order as shadow_worker (plan 12-E: one scheduler
#: serializes writes; the valuation lane only reads those ledgers).
FAMILY_ORDER = (FAMILY_ILLIQ, FAMILY_PREMFADE, FAMILY_CARRY, FAMILY_BANDRIDGE)

#: Frozen mark-price source (research/control/prospective_shadow_v1/e/
#: valuation_config.json): ONE bulk premiumIndex response covers every
#: symbol; keyless public read; markPrice is the funding-settlement
#: price class.
PRICE_SOURCE_NAME = "binance_fapi_premium_index_bulk"
PREMIUM_INDEX_URL = "https://fapi.binance.com/fapi/v1/premiumIndex"
FETCH_TIMEOUT_S = 20.0

HEARTBEAT_FILENAME = os.path.join("runtime", "valuation_heartbeat.json")


# ----------------------------------------------------------------------
# frozen price source (keyless, batched, monkeypatch-friendly)
# ----------------------------------------------------------------------
def _fetch_batch_prices_once(
    url: str, timeout: float
) -> Tuple[Dict[str, float], str, str]:
    """Single keyless read of the frozen premiumIndex source."""
    request = urllib.request.Request(
        url, headers={"User-Agent": "shv1-valuation-keyless-read/1.0"}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read()
    digest = hashlib.sha256(raw).hexdigest()
    parsed = json.loads(raw.decode("utf-8"))
    if not isinstance(parsed, list) or not parsed:
        raise ValueError("premiumIndex bulk response is not a non-empty array")
    prices: Dict[str, float] = {}
    newest_ms = 0
    for entry in parsed:
        if not isinstance(entry, dict):
            continue
        symbol = entry.get("symbol")
        mark = entry.get("markPrice")
        stamp_ms = entry.get("time")
        if not isinstance(symbol, str) or mark is None:
            continue
        prices[symbol] = float(mark)
        if isinstance(stamp_ms, (int, float)) and stamp_ms > newest_ms:
            newest_ms = int(stamp_ms)
    if not prices:
        raise ValueError("premiumIndex bulk response carried no usable marks")
    source_ts = (
        valuation.to_iso_z(
            dt.datetime.fromtimestamp(newest_ms / 1000.0, tz=dt.timezone.utc)
        )
        if newest_ms
        else None
    )
    return prices, source_ts, digest


#: 2026-09-21 operational remediation (owner instruction: fix the
#: dashboard data outage).  Root cause: the machine's shared egress IP
#: (Cloudflare WARP range) is REPEATEDLY auto-banned by the exchange
#: (HTTP 418, msg "Way too many requests; IP ... banned until <ms>")
#: because of OTHER tenants of the shared IP — this worker's own rate
#: is ONE keyless bulk read per 5-minute loop.  The frozen single-
#: attempt design turned every transient shared-IP ban window into a
#: full UNAVAILABLE_FAIL_CLOSED loop.  Remediation law: the SOURCE,
#: request shape, mark semantics, digests and fail-closed discipline
#: are UNCHANGED; a mark is still written ONLY from a fresh successful
#: response (zero stale reuse); we only RETRY transient transport
#: failures (418/429/5xx/network) within a bounded <= ~240 s budget per
#: loop, honoring the exchange's own "banned until" epoch when present
#: (capped at RETRY_BAN_WAIT_MAX_S so a long ban still fails closed on
#: schedule).  Exhausting the budget records the failure exactly as
#: before.
RETRYABLE_HTTP = (418, 429, 500, 502, 503, 504)
RETRY_BACKOFF_S = (30.0, 60.0, 90.0)
RETRY_BAN_WAIT_MAX_S = 150.0


def _ban_wait_seconds(exc: "urllib.error.HTTPError") -> Optional[float]:
    """Parse the exchange's own ban window ("banned until <ms epoch>")."""
    try:
        body = exc.read().decode("utf-8", "replace")
        match = re.search(r"banned until (\d{9,14})", body)
        if not match:
            return None
        banned_ms = int(match.group(1))
        if banned_ms > 10**12:            # ms epoch
            banned_s = banned_ms / 1000.0
        else:                              # s epoch
            banned_s = float(banned_ms)
        return max(0.0, banned_s - time.time())
    except Exception:                      # noqa: BLE001 - best effort only
        return None


def fetch_batch_prices(
    url: str = PREMIUM_INDEX_URL, timeout: float = FETCH_TIMEOUT_S
) -> Tuple[Dict[str, float], str, str]:
    """Bulk keyless read of the frozen premiumIndex source with BOUNDED
    transient-failure retry (see the remediation note above).

    Returns ``(prices_by_symbol, source_timestamp_utc, source_digest)``.
    On final failure the caller records UNAVAILABLE_FAIL_CLOSED — still
    no stale reuse, ever.
    """
    last_exc: Optional[BaseException] = None
    backoffs = [0.0] + list(RETRY_BACKOFF_S)
    for attempt in range(len(backoffs)):
        if backoffs[attempt]:
            time.sleep(backoffs[attempt])
        try:
            return _fetch_batch_prices_once(url, timeout)
        except urllib.error.HTTPError as exc:
            if exc.code not in RETRYABLE_HTTP:
                raise
            last_exc = exc
            wait = _ban_wait_seconds(exc)
            if wait is not None and attempt + 1 < len(backoffs):
                # replace the next fixed backoff with the exchange's own
                # ban window (+2 s), capped so a long ban still fails
                # closed within the loop budget
                backoffs[attempt + 1] = max(
                    backoffs[attempt + 1],
                    min(wait + 2.0, RETRY_BAN_WAIT_MAX_S))
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_exc = exc
    assert last_exc is not None
    raise last_exc


# ----------------------------------------------------------------------
# heartbeat (Q-13 pattern, same discipline as shadow_worker)
# ----------------------------------------------------------------------
class HeartbeatWriter:
    """Heartbeat file held open on a stable descriptor; every write
    fstats the OPEN HANDLE vs os.stat of the PATH (tamper/restart
    detection surfaced as ``match == false``)."""

    def __init__(self, path: str):
        directory = os.path.dirname(os.path.abspath(path))
        os.makedirs(directory, exist_ok=True)
        self.path = path
        self._fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)

    def write(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        line = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        os.lseek(self._fd, 0, os.SEEK_SET)
        os.ftruncate(self._fd, 0)
        os.write(self._fd, (line + "\n").encode("utf-8"))
        os.fsync(self._fd)
        fd_stat = os.fstat(self._fd)
        try:
            path_stat = os.stat(self.path)
            path_ino: Optional[int] = path_stat.st_ino
        except FileNotFoundError:
            path_ino = None
        return {
            "fd_ino": fd_stat.st_ino,
            "path_ino": path_ino,
            "match": path_ino == fd_stat.st_ino,
        }

    def close(self) -> None:
        try:
            os.close(self._fd)
        except OSError:
            pass


# ----------------------------------------------------------------------
# one valuation loop
# ----------------------------------------------------------------------
def strategy_ledger_path(runtime_root: str, family_id: str) -> str:
    """READ-ONLY strategy ledger location (namespace-separated root)."""
    return os.path.join(
        start_guard.prospective_ledger_root(runtime_root),
        f"{family_id}.jsonl",
    )


def run_valuation_loop(
    shadow_start_utc: str,
    runtime_root: str,
    *,
    now_utc: Optional[str] = None,
    loop_count: int = 0,
    marks_written: int = 0,
    skipped_existing: int = 0,
    last_error: Optional[str] = None,
    fetch_fn=None,
    heartbeat: Optional[HeartbeatWriter] = None,
) -> Dict[str, Any]:
    """Run ONE bounded valuation pass; return the heartbeat payload.

    ``fetch_fn`` defaults to :func:`fetch_batch_prices` (the frozen
    keyless source); tests inject a synthetic feed. Exceptions NEVER
    propagate: they land in ``last_error`` and the heartbeat is still
    written.
    """
    now_moment = (
        start_guard.parse_moment(now_utc)
        if now_utc is not None
        else dt.datetime.now(dt.timezone.utc)
    )
    now_iso = start_guard.to_iso_z(now_moment)
    mark_ts = valuation.round_mark_timestamp_utc(now_moment)
    next_mark = valuation.round_mark_timestamp_utc(
        now_moment + dt.timedelta(seconds=valuation.MARK_INTERVAL_SECONDS)
    )

    payload: Dict[str, Any] = {
        "schema": HEARTBEAT_SCHEMA,
        "worker_schema": WORKER_SCHEMA,
        "pid": os.getpid(),
        "loop_count": loop_count + 1,
        "last_loop_utc": now_iso,
        "next_mark_utc": next_mark,
        "shadow_start_utc": shadow_start_utc,
        "runtime_root": os.path.abspath(runtime_root),
        "price_source": PRICE_SOURCE_NAME,
        "last_mark_per_family": {},
        "marks_written": marks_written,
        "skipped_existing": skipped_existing,
        "last_error": last_error,
        "heavy_lock_verdict": None,
        "heavy_lock_verdict_note": (
            "inspect-only each loop; the heavy lock is NEVER acquired "
            "(ACTIVE_LIGHT); expected FREE_PROVEN"
        ),
        "pre_activation_quiet_noop": False,
    }

    # ACTIVE_LIGHT: inspect the machine-wide heavy lock, never hold it.
    try:
        payload["heavy_lock_verdict"] = heavy_lock.inspect().get("verdict")
    except Exception as exc:  # noqa: BLE001 - verdict failure != crash
        payload["last_error"] = f"heavy_lock.inspect: {type(exc).__name__}: {exc}"

    # Forward-only discipline: before SHADOW_START_UTC no mark is
    # written (quiet pre-activation no-op; PnL may not precede start).
    if now_moment < start_guard.parse_moment(shadow_start_utc):
        payload["pre_activation_quiet_noop"] = True
        _write_heartbeat(heartbeat, payload)
        return payload

    prices: Dict[str, float] = {}
    source_ts: Optional[str] = None
    source_digest: Optional[str] = None
    fetch = fetch_fn if fetch_fn is not None else fetch_batch_prices
    try:
        prices, source_ts, source_digest = fetch()
    except Exception as exc:  # noqa: BLE001 - price failure is a recorded gap
        payload["last_error"] = f"price fetch: {type(exc).__name__}: {exc}"

    for family_id in FAMILY_ORDER:
        try:
            # idempotent seed (CAPITAL_SEED_NO_MARK, never performance)
            seed = valuation.capital_seed_record(family_id, shadow_start_utc)
            seed_outcome = valuation.append_valuation_mark(runtime_root, seed)
            if seed_outcome == "skipped_existing":
                payload["skipped_existing"] = payload.get("skipped_existing", 0) + 1
            else:
                payload["marks_written"] = payload.get("marks_written", 0) + 1

            ledger_path = strategy_ledger_path(runtime_root, family_id)
            state = valuation.rebuild_positions(ledger_path)
            needed = sorted(valuation.open_positions(state))
            sub_prices = {sym: prices[sym] for sym in needed if sym in prices}
            record = valuation.build_valuation_mark(
                family_id,
                ledger_path,
                sub_prices,
                mark_ts,
                now_iso,
                PRICE_SOURCE_NAME,
                source_ts,
                source_digest,
            )
            outcome = valuation.append_valuation_mark(runtime_root, record)
            if outcome == "skipped_existing":
                payload["skipped_existing"] = payload.get("skipped_existing", 0) + 1
            else:
                payload["marks_written"] = payload.get("marks_written", 0) + 1
            payload["last_mark_per_family"][family_id] = {
                "mark_id": record["mark_id"],
                "mark_timestamp_utc": record["mark_timestamp_utc"],
                "status": record["status"],
                "accounting_status": record["accounting_status"],
                "equity": record["equity"],
            }
        except Exception as exc:  # noqa: BLE001 - one family never blocks others
            payload["last_error"] = (
                f"{family_id}: {type(exc).__name__}: {exc}"
            )
            payload["last_mark_per_family"][family_id] = None

    _write_heartbeat(heartbeat, payload)
    return payload


def _write_heartbeat(heartbeat: Optional[HeartbeatWriter], payload: Dict[str, Any]) -> None:
    if heartbeat is None:
        return
    try:
        inode_check = heartbeat.write(payload)
        payload["valuation_heartbeat_inode_vs_path_check"] = inode_check
        heartbeat.write(payload)
    except Exception as exc:  # noqa: BLE001 - heartbeat failure != crash
        payload["last_error"] = f"heartbeat: {type(exc).__name__}: {exc}"


# ----------------------------------------------------------------------
# aligned sleep + CLI
# ----------------------------------------------------------------------
def seconds_to_next_boundary(now_moment: Optional[dt.datetime] = None, interval: int = valuation.MARK_INTERVAL_SECONDS) -> float:
    moment = now_moment or dt.datetime.now(dt.timezone.utc)
    epoch = moment.timestamp()
    next_epoch = (int(epoch) // interval + 1) * interval
    return max(0.0, next_epoch - epoch)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="valuation_worker.py",
        description=(
            "PROSPECTIVE-SHADOW-V1 near-real MTM valuation worker "
            "(ACTIVE_LIGHT: never holds the heavy lock; read-only over "
            "strategy ledgers; keyless public price reads only)."
        ),
    )
    parser.add_argument(
        "--shadow-start", required=True,
        help="SHADOW_START_UTC (ISO-Z); REQUIRED, fail closed without it",
    )
    parser.add_argument(
        "--runtime-root", default="results/prospective_shadow_v1",
        help="runtime root holding ledgers/, valuation_marks/ and runtime/",
    )
    parser.add_argument(
        "--once", action="store_true",
        help="run ONE aligned valuation loop and exit",
    )
    parser.add_argument(
        "--interval", type=int, default=valuation.MARK_INTERVAL_SECONDS,
        help="loop cadence seconds (default 300, aligned to UTC boundaries)",
    )
    args = parser.parse_args(argv)

    # Fail closed on an unparsable start stamp (PROSPECTIVE rule).
    start_guard.parse_moment(args.shadow_start)
    if int(args.interval) <= 0:
        parser.error("--interval must be positive")

    heartbeat = HeartbeatWriter(
        os.path.join(args.runtime_root, HEARTBEAT_FILENAME)
    )
    state = {"loop_count": 0, "marks_written": 0, "skipped_existing": 0, "last_error": None}
    try:
        while True:
            payload = run_valuation_loop(
                args.shadow_start,
                args.runtime_root,
                loop_count=state["loop_count"],
                marks_written=state["marks_written"],
                skipped_existing=state["skipped_existing"],
                last_error=state["last_error"],
                heartbeat=heartbeat,
            )
            state["loop_count"] = payload["loop_count"]
            state["marks_written"] = payload["marks_written"]
            state["skipped_existing"] = payload["skipped_existing"]
            state["last_error"] = payload["last_error"]
            if args.once:
                break
            time.sleep(seconds_to_next_boundary(interval=int(args.interval)))
    except KeyboardInterrupt:
        pass
    finally:
        heartbeat.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
