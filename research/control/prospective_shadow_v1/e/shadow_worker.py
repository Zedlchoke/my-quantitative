"""PROSPECTIVE-SHADOW-V1 E-phase forward worker (plan sections 7 and 12-E).

INTERNAL PAPER ONLY: keyless public network reads (Binance fapi public
endpoints through the frozen data_feed allowlist); NO API keys, no
accounts, no orders — the only emitted action type is TARGET_INTENT and
all fills are virtual (A2 SleeveAccount).

Production loop (G8 carried condition C5): the ONLY execution surface
is ``ForwardExecutor.run_due`` — three executors in the FIXED family
order (ILLIQ, PREMFADE, CARRY), polled every ``--interval`` seconds
(default 300). Lightweight polling NEVER acquires the machine-wide
heavy lock. Unexpected exceptions are recorded in the heartbeat
``last_error`` field and the loop continues: a crashed loop must be
visible as heartbeat staleness, not as silence.

Heartbeat (Q-13): every loop writes
``<runtime_root>/runtime/heartbeat.json`` holding pid, loop_count,
last_loop_utc, next_decision_per_family, last_completed,
per-family ledger_byte_counts and the ``heartbeat_inode_vs_path_check``
(os.fstat of the open handle vs os.stat of the path — detects the
heartbeat being replaced or removed underneath the worker).

Forward-only discipline (G8 condition C2): the namespace is fixed to
``PROSPECTIVE``; ``--shadow-start`` (SHADOW_START_UTC, ISO-Z) is
REQUIRED — the worker refuses to start without it (fail closed). The
replay rehearsal lane (replay_rehearsal.py) is the ONLY place allowed
to construct executors in the explicit REPLAY_NOT_PROSPECTIVE
namespace, under its own runtime root inside this control directory.

ENGINE CONFIG DISCLOSURES (all values below are engine-level choices,
documented; the identity manifests stay verbatim and untouched):

- Fetch-window lookbacks: the 28d families size their snapshot fetch
  window at 29d + 1h. The 28d figure is the identity's FORMATION COUNT
  (2688 = 28 x 96 trailing completed buckets; 28 daily returns + 1 base
  day). With the C6 feature cutoff (decision - 900s) a literal 28d
  fetch window yields only 2678 completed buckets / 28 formation dates
  — mathematically short of the frozen formation count — so every
  decision would be DATA_BLOCKED. The adapters themselves re-enforce
  the exact trailing-2688/29-date identity and the 29-day max span, so
  identity is preserved; the extra window is transport only. This
  mirrors the Q-lane smoke harness, which feeds 29 days.
- ILLIQ min_listing_age_days = 27.0: listing evidence comes from the
  first completed bar in the fetch window, so any threshold >= the
  window would auto-reject every symbol. 27.0 is the largest whole-day
  value that remains decidable from the snapshot. A dedicated listing
  registry would be an owner tightening.
- ILLIQ min_daily_dollar_volume = 10_000_000.0 USDT trailing mean
  daily dollar volume (the identity pins the DV-filter RULE, not a
  number; this threshold filters genuinely illiquid names while the
  20-name candidate universe of deep USDT-M markets passes comfortably).
- ILLIQ btc_betas: the identity pins beta NEUTRALITY (risk caps) but
  no measured beta surface exists in this lane's scope. The worker
  supplies the STRUCTURAL-BETA convention: unit betas for every
  candidate, under which the equal-count long/short mirror has book
  beta exactly 0 and the frozen btc_beta_neutral cap verifies the
  structural mirror. Disclosed loudly; measured 90d daily betas
  (the historical convention) would be an owner tightening.
- Tick coverage: CARRY maps its 7 identity-verbatim traded symbols;
  families 1-2 map EVERY declared candidate symbol, resolved from the
  sha256-verified archived exchangeInfo exactly as
  cost_regime_manifest.tick_size_roles.family1_family2 prescribes
  ("resolved at decision time from the same archived exchangeInfo
  bytes"). tick_size_default = 0.10 (BTCUSDT tick) stays as the
  fail-closed fallback ONLY for a fill symbol outside the declared
  candidates: using 0.10 as the primary tick for sub-dollar symbols
  would model one-tick slippage exceeding the position notional
  (measured: OPUSDT at ~0.095 -> 13,191 USDT "slippage" on a 12.5k
  fill in the first rehearsal run — rejected as economically absurd).
- F1/F2 candidate universes: the identity manifests deliberately do
  NOT enumerate the historical staged 20-symbol lists ("This lane
  invents no symbol list" - P2 data manifest). The worker therefore
  declares its candidate universes explicitly (fixed at construction,
  PIT listing+DV eligibility still resolved per decision): 20 deep
  USDT-M perpetuals for ILLIQ (mirroring the historical "20 staged
  binance_bar symbols" convention) and 13 pairs for PREMFADE (12
  designed eligible names + BTCUSDT, whose benchmark exclusion the
  adapter enforces; 12 eligible is the frozen min_eligible where the
  equal weight equals the designed max |w| = 0.125). Every candidate
  is verified at build time to exist as a TRADING USDT PERPETUAL in
  the archived exchangeInfo (fail closed otherwise).
- PREMFADE eligibility band: the frozen caps pin min_abs_weight at the
  designed 0.125, so a weekly book passes only at floor(n/3) == 4
  (n_eligible in {12,13,14}) — the designed operating band. A richer
  universe would be risk-BLOCKED by the frozen caps; the 13-pair
  candidate set is sized to the design.
- LINEAGE_COST books: ILLIQ realizes the verbatim lineage stress
  convention (fee x1.5, +2 ticks) on the frozen 0.0005 taker base ->
  fee 0.00075, slippage 2.0 ticks. PREMFADE/CARRY lineages pin no
  numeric fee/slippage (their verbatim conventions are the fill rule
  and funding sign, both structural), so their LINEAGE book mirrors
  CURRENT_CONSERVATIVE_COST for diagnostic continuity. Disclosed.
- Transport pacing (PacedFetch): the default feed injects a paced,
  429/418-retrying GET transport through the frozen client's official
  fetch_fn injection point. Without it, a TRANSIENT venue rate limit
  would burn a weekly decision forever (a DATA_BLOCKED record consumes
  its deterministic event_id and is never re-executed — audit ADJ1).
  GET-only, keyless, allowlist and PIT semantics stay frozen; after
  the retry cap the failure surfaces honestly as DATA_BLOCKED.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import signal
import sys
import time
from typing import Any, Dict, Mapping, Optional

WORKTREE_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")
)
if WORKTREE_ROOT not in sys.path:
    sys.path.insert(0, WORKTREE_ROOT)

from research.shadow_v1 import (  # noqa: E402
    data_feed,
    ledger,
    risk,
    scheduler,
    start_guard,
)
from research.shadow_v1.data_feed import KeylessBinanceFuturesClient  # noqa: E402
from research.shadow_v1.executor import ForwardExecutor  # noqa: E402
from research.shadow_v1.families import (  # noqa: E402
    FAMILY_BANDRIDGE,
    FAMILY_CARRY,
    FAMILY_ILLIQ,
    FAMILY_PREMFADE,
)

import http.client  # noqa: E402
import urllib.error  # noqa: E402
import urllib.request  # noqa: E402

WORKER_SCHEMA = "shv1_e_worker@1"
HEARTBEAT_SCHEMA = "shv1_e_worker_heartbeat@1"
LABEL_PROSPECTIVE = start_guard.NAMESPACE_PROSPECTIVE

#: FIXED execution order (plan 12-E: one scheduler serializes writes).
FAMILY_ORDER = (FAMILY_ILLIQ, FAMILY_PREMFADE, FAMILY_CARRY, FAMILY_BANDRIDGE)

IDENTITY_MANIFEST_PATH = os.path.join(
    WORKTREE_ROOT,
    "research",
    "control",
    "prospective_shadow_v1",
    "identity",
    "identity_recovery.json",
)
EXCHANGE_INFO_ARCHIVE_PATH = os.path.join(
    WORKTREE_ROOT,
    "research",
    "control",
    "prospective_shadow_v1",
    "data_cost",
    "raw",
    "cross",
    "exchangeInfo_fapi.json",
)
#: Frozen archive pin (cost_regime_manifest.tick_size_evidence).
EXCHANGE_INFO_SHA256 = (
    "055202f6b50b635e6be516f32cc1ac1fbdcbba9b8d284b6f66496b12d6aefb85"
)

#: Deterministic sha256 over "relpath:file_sha256" lines of every *.py
#: under research/shadow_v1 (sorted, __pycache__ excluded). Pins the
#: audited engine bytes (G8 audited lineage 04c94d8b == base bb0a134b).
CODE_FREEZE_SHA = "af4df157690ae9b0ec8b75fb34615682384bd059b5c9b08dfa76473ed9dcdba2"

#: G8 carried condition C6 (auditor binding): feature cutoff is pinned
#: at one frozen 15m interval BEFORE the decision for bar/bucket families.
FEATURE_CUTOFF_OFFSET_SECONDS = 900.0

#: Frozen CURRENT_CONSERVATIVE_COST book (cost_regime_manifest.json).
FEE_RATE_CURRENT = 0.0005
SLIPPAGE_TICKS_CURRENT = 1.0
#: ILLIQ verbatim lineage convention "stress = fee x1.5, +2 ticks" over
#: the frozen 0.0005 taker base.
FEE_RATE_ILLIQ_LINEAGE = FEE_RATE_CURRENT * 1.5
SLIPPAGE_TICKS_ILLIQ_LINEAGE = 2.0

#: AMENDMENT A2 (owner GO consumed 2026-09-25T03:41Z, decision D3; draft
#: plans/DRAFT_amendment_PSCTV1_A2_bandridge_pins.md): the BANDRIDGE
#: identity manifest pins fee_bps_per_side = 6.0 as the FULL per-side
#: stack ("6 bps/side full stack", SPEC.md). The executor is re-pinned to
#: exactly that for the BANDRIDGE family ONLY — a per-family override.
#: FEE_RATE_CURRENT (5 bps + 1 tick) above stays byte-identical for
#: ILLIQ/PREMFADE/CARRY (regression fixtures (c)/(e)); the shared cost
#: digest 130d2e7e… stops applying to NEW BANDRIDGE records at the
#: activation moment T_act recorded in
#: research/control/prospective_shadow_v1/cost_regime_boundaries/BANDRIDGE_A2_PINS.json.
FEE_RATE_BANDRIDGE_IDENTITY = 0.0006
SLIPPAGE_TICKS_BANDRIDGE_IDENTITY = 0.0
BANDRIDGE_COST_BOOKS_PINNED = {
    "CURRENT_CONSERVATIVE_COST": {
        "fee_rate": FEE_RATE_BANDRIDGE_IDENTITY,
        "slippage_ticks": SLIPPAGE_TICKS_BANDRIDGE_IDENTITY,
    },
    "LINEAGE_COST": {
        "fee_rate": FEE_RATE_BANDRIDGE_IDENTITY,
        "slippage_ticks": SLIPPAGE_TICKS_BANDRIDGE_IDENTITY,
    },
}

#: Conservative BTC tick (cost regime manifest) for fill symbols absent
#: from the per-symbol mapping (plan section 6 per-symbol tick model).
TICK_SIZE_DEFAULT = 0.10

#: Engine keys required by IlliqAmihudAdapter.required_engine_keys().
ILLIQ_ENGINE: Dict[str, float] = {
    "min_listing_age_days": 27.0,
    "min_daily_dollar_volume": 10_000_000.0,
    "btc_beta_tolerance": 1e-6,
    "hard_gross_cap": 1.0,
    "hard_abs_net_cap": 0.0,
}

#: 29d + 1h: see module docstring (28d is the formation COUNT, not the
#: fetch window; the C6 cutoff costs two buckets at the near edge).
FORMATION_LOOKBACK_SECONDS = float(29 * 86400 + 3600)
#: CARRY identity-pinned trailing settled-funding window.
CARRY_LOOKBACK_SECONDS = float(7 * 86400)

#: AMENDMENT A3 (owner GO consumed 2026-09-25T04:21:15Z, decision D4;
#: draft plans/DRAFT_amendment_PSCTV1_A3_xsect_retire.md): identity
#: retirement of XSECT-FUND-CARRY-7D. T_ret is the moment the stop-open
#: law is LIVE ON THE WORKER: the Phase A restart happens BEFORE this
#: timestamp, and the first decision at/after it runs flat-only. If the
#: activation restart slips past this value, the activation commit moves
#: the timestamp forward BEFORE any decision at/after it executes (the
#: running pre-A3 worker ignores the constant; no decision is affected
#: by the move). From T_ret: no new positions open; existing holdings
#: close at that decision (natural frozen-law expiry; closing sells are
#: lawful); exactly one terminal row when measured FLAT. Ledger stays
#: append-only forever; the historical CANDIDATE_FAIL label is pinned.
XSECT_RETIRE_AFTER_UTC = "2026-09-25T05:45:00Z"
XSECT_RETIRE_TERMINAL = {
    "label": "IDENTITY_RETIRED_COST_DOMINATED",
    "historical_verdict_label": (
        "CANDIDATE_FAIL (V6 funding carry; top-positive-fold 51.66% — "
        "pinned, not rewritable)"
    ),
    "equity_basis_note": (
        "equity here is the decision-row ledger basis; the valuation-mark "
        "basis differs (PSV1 accounting-reconciliation class)"
    ),
    "note": (
        "owner D4 2026-09-25; stop-open from T_ret; evidence append-only; "
        "successor law: new strategy ID + rebalance only when expected "
        "carry >= full round-trip stress cost (umbrella C-XS-2)"
    ),
}

#: ILLIQ candidate universe: 20 deep USDT-M perpetuals (historical
#: "20 staged binance_bar symbols" convention). The first 13 mirror the
#: Q-lane smoke composition; existence as TRADING USDT PERPETUAL is
#: verified against the archived exchangeInfo at build time.
ILLIQ_CANDIDATE_UNIVERSE = (
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "LINKUSDT",
    "ADAUSDT",
    "LTCUSDT",
    "AVAXUSDT",
    "ATOMUSDT",
    "NEARUSDT",
    "ARBUSDT",
    "OPUSDT",
    "APTUSDT",
    "FILUSDT",
    "ETCUSDT",
    "BCHUSDT",
    "DOTUSDT",
    "TRXUSDT",
)

#: PREMFADE candidate universe: 12 designed eligible names + BTCUSDT
#: (adapter-enforced benchmark exclusion; min_eligible == 12 band where
#: the equal weight equals the designed max |w| 0.125).
PREMFADE_CANDIDATE_UNIVERSE = (
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "LINKUSDT",
    "ADAUSDT",
    "LTCUSDT",
    "AVAXUSDT",
    "ATOMUSDT",
    "NEARUSDT",
    "ARBUSDT",
)

#: CARRY traded universe: identity verbatim (exact enumeration).
CARRY_TRADED_UNIVERSE = (
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "LINKUSDT",
    "ADAUSDT",
)

#: Symbols with measured verbatim ticks in the cost regime manifest
#: (the pin set of cost_regime_manifest.tick_sizes_usdt_perp).
MEASURED_TICK_SYMBOLS = (
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "LINKUSDT",
    "ADAUSDT",
)

#: Tick-mapping coverage policy per cost_regime_manifest.tick_size_roles:
#: "family1_family2: ... tick sizes for their PIT-eligible sets are
#: resolved at decision time from the same archived exchangeInfo bytes
#: (values are verbatim strings as published)" — and the archive is the
#: per-symbol tick source for ALL symbols. Families 1-2 therefore get a
#: covering mapping resolved from the verified archive for every
#: DECLARED candidate symbol; ``tick_size_default`` (0.10, the BTCUSDT
#: tick — conservative for high-priced symbols) remains the mandatory
#: fail-closed fallback ONLY for a fill symbol outside the declared
#: candidates. NOTE: using the 0.10 default as the PRIMARY price for
#: sub-dollar candidates (e.g. OPUSDT at ~0.09) would model a one-tick
#: slippage exceeding the whole position notional — economically
#: absurd and (measured in the first rehearsal run) equity-destroying;
#: that reading is rejected in favour of the manifest's own rule.


class WorkerConfigError(RuntimeError):
    """The worker refuses to start (fail closed)."""


class PacedFetch:
    """Polite keyless GET transport for the frozen feed client.

    Injected through ``KeylessBinanceFuturesClient(fetch_fn=...)`` (the
    client's official transport injection point; endpoints, bytes and
    PIT semantics stay frozen). Rationale: a weekly decision whose
    snapshot fetch hits a TRANSIENT venue rate limit (HTTP 429/418)
    would otherwise be recorded DATA_BLOCKED under its deterministic
    event_id and never re-executed (audit ADJ1 semantics) — a burnable
    weekly observation. This wrapper:

    - enforces a minimum gap between ANY two requests (default 0.25s);
    - on HTTP 429/418 retries with bounded backoff, honouring the
      Retry-After header when present (default cap 6 attempts);
    - re-raises after the cap, which the frozen client converts to
      DataBlocked -> an honest DATA_BLOCKED record (fail closed).

    GET-only, keyless, allowlist enforcement stays in the frozen client.
    """

    RETRYABLE_STATUS = (429, 418)

    def __init__(
        self,
        min_gap_seconds: float = 0.25,
        max_attempts: int = 6,
        max_backoff_seconds: float = 30.0,
        clock=time.monotonic,
        sleeper=time.sleep,
        transport=None,
    ):
        self.min_gap_seconds = float(min_gap_seconds)
        self.max_attempts = int(max_attempts)
        self.max_backoff_seconds = float(max_backoff_seconds)
        self._clock = clock
        self._sleep = sleeper
        self._transport = transport if transport is not None else self._get_once
        self._last_request_at: Optional[float] = None
        self.attempts_made = 0
        self.retries_made = 0

    def _get_once(self, url: str) -> bytes:
        request = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
            if response.status != 200:
                raise data_feed.DataBlocked(
                    f"endpoint returned HTTP {response.status}: {url}"
                )
            return response.read()

    def __call__(self, url: str) -> bytes:
        last_error: Optional[Exception] = None
        for attempt in range(self.max_attempts):
            self.attempts_made += 1
            if self._last_request_at is not None:
                gap = self._clock() - self._last_request_at
                if gap < self.min_gap_seconds:
                    self._sleep(self.min_gap_seconds - gap)
            try:
                payload = self._transport(url)
                self._last_request_at = self._clock()
                return payload
            except urllib.error.HTTPError as exc:
                self._last_request_at = self._clock()
                last_error = exc
                if exc.code not in self.RETRYABLE_STATUS:
                    raise
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
                try:
                    delay = float(retry_after) if retry_after else 0.0
                except (TypeError, ValueError):
                    delay = 0.0
                delay = max(
                    delay, min(self.max_backoff_seconds, 2.0 ** (attempt + 1))
                )
                self.retries_made += 1
                self._sleep(delay)
            except (urllib.error.URLError, http.client.HTTPException, OSError) as exc:
                self._last_request_at = self._clock()
                last_error = exc
                self.retries_made += 1
                self._sleep(min(self.max_backoff_seconds, 2.0 ** (attempt + 1)))
        raise data_feed.DataBlocked(
            f"paced fetch exhausted {self.max_attempts} attempts for {url}: "
            f"{last_error}"
        )


def default_feed() -> KeylessBinanceFuturesClient:
    """The production feed: frozen client + paced transport (disclosed)."""
    return KeylessBinanceFuturesClient(fetch_fn=PacedFetch())


# ----------------------------------------------------------------------
# frozen inputs
# ----------------------------------------------------------------------
def load_identity_manifest() -> Dict[str, Any]:
    with open(IDENTITY_MANIFEST_PATH, "rb") as handle:
        return json.loads(handle.read().decode("utf-8"))


def identity_entries_by_family(manifest: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    entries: Dict[str, Dict[str, Any]] = {}
    for entry in manifest.get("families", []):
        entries[str(entry["family_id"])] = entry
    missing = [fid for fid in FAMILY_ORDER if fid not in entries]
    if missing:
        raise WorkerConfigError(
            f"identity manifest is missing family entries {missing}; refusing"
        )
    return entries


def load_archived_symbol_info() -> Dict[str, Dict[str, Any]]:
    """Per-symbol archive facts (tick verbatim string, contract, status).

    Fail closed on any sha256 mismatch with the pinned archive bytes
    (cost_regime_manifest.tick_size_evidence.archived_fetch.sha256)."""
    with open(EXCHANGE_INFO_ARCHIVE_PATH, "rb") as handle:
        raw = handle.read()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXCHANGE_INFO_SHA256:
        raise WorkerConfigError(
            "archived exchangeInfo sha256 mismatch: got "
            f"{digest}, pinned {EXCHANGE_INFO_SHA256}; refusing to "
            "resolve tick sizes from unverified bytes"
        )
    doc = json.loads(raw.decode("utf-8"))
    info: Dict[str, Dict[str, Any]] = {}
    for symbol in doc.get("symbols", []):
        if symbol.get("quoteAsset") != "USDT":
            continue
        tick = None
        for entry in symbol.get("filters", []):
            if entry.get("filterType") == "PRICE_FILTER":
                tick = entry.get("tickSize")
        info[str(symbol["symbol"])] = {
            "contract_type": symbol.get("contractType"),
            "status": symbol.get("status"),
            "tick_size_verbatim": tick,
        }
    return info


def measured_ticks_from_info(info: Mapping[str, Dict[str, Any]]) -> Dict[str, float]:
    return {
        symbol: float(entry["tick_size_verbatim"])
        for symbol, entry in info.items()
        if entry["tick_size_verbatim"] is not None
    }


def assert_candidates_in_archive(info: Mapping[str, Dict[str, Any]]) -> None:
    """Every candidate symbol must be a TRADING USDT PERPETUAL in the
    verified archive (build-time sanity; fail closed)."""
    for symbol in set(ILLIQ_CANDIDATE_UNIVERSE) | set(PREMFADE_CANDIDATE_UNIVERSE):
        entry = info.get(symbol)
        if entry is None:
            raise WorkerConfigError(
                f"candidate {symbol!r} absent from the archived exchangeInfo"
            )
        if entry["contract_type"] != "PERPETUAL" or entry["status"] != "TRADING":
            raise WorkerConfigError(
                f"candidate {symbol!r} is "
                f"{entry['contract_type']}/{entry['status']} in the archived "
                "exchangeInfo; refusing a non-TRADING-PERPETUAL candidate"
            )


def tick_mapping_for(
    family_id: str,
    measured_ticks: Dict[str, float],
    archive_info: Mapping[str, Dict[str, Any]],
) -> Dict[str, float]:
    """Plan section 6 per-symbol tick mapping for ONE family.

    CARRY: its identity-verbatim 7 traded symbols, resolved from the
    verified archive. Families 1-2: every DECLARED candidate symbol
    resolved from the verified archive (cost_regime_manifest
    tick_size_roles.family1_family2 rule; see the coverage-policy note
    above). The 0.10 default only covers a fill symbol outside the
    declared candidates (never expected)."""
    if family_id == FAMILY_CARRY:
        symbols: tuple = CARRY_TRADED_UNIVERSE
    elif family_id == FAMILY_BANDRIDGE:
        symbols = ("BTCUSDT",)
    else:
        symbols = tuple(
            dict.fromkeys(ILLIQ_CANDIDATE_UNIVERSE + PREMFADE_CANDIDATE_UNIVERSE)
        )
    mapping: Dict[str, float] = {}
    for symbol in symbols:
        verbatim = archive_info.get(symbol, {}).get("tick_size_verbatim")
        if verbatim is None:
            if symbol in MEASURED_TICK_SYMBOLS:
                raise WorkerConfigError(
                    f"family {family_id} tick symbol {symbol!r} is pinned by "
                    "the cost regime manifest but has no archived tick; "
                    "refusing"
                )
            continue  # outside the archive: left to tick_size_default
        mapping[symbol] = float(verbatim)
    if not mapping:
        raise WorkerConfigError(
            f"family {family_id} tick mapping resolved empty; refusing"
        )
    return mapping


def cost_books_for(family_id: str) -> Dict[str, Dict[str, float]]:
    # A2 P-3: per-family override — BANDRIDGE books are the identity pin
    # (6 bps/side full stack), returned as fresh copies; every other
    # family continues through the shared frozen construction below.
    if family_id == FAMILY_BANDRIDGE:
        return {
            name: dict(params)
            for name, params in BANDRIDGE_COST_BOOKS_PINNED.items()
        }
    books = {
        "CURRENT_CONSERVATIVE_COST": {
            "fee_rate": FEE_RATE_CURRENT,
            "slippage_ticks": SLIPPAGE_TICKS_CURRENT,
        }
    }
    if family_id == FAMILY_ILLIQ:
        books["LINEAGE_COST"] = {
            "fee_rate": FEE_RATE_ILLIQ_LINEAGE,
            "slippage_ticks": SLIPPAGE_TICKS_ILLIQ_LINEAGE,
        }
    else:
        # No numeric lineage fee/slippage is pinned by these families'
        # identity entries (verbatim conventions are structural: the
        # PREMFADE fill rule, the CARRY funding sign/cadence); the
        # LINEAGE book mirrors the frozen current book for diagnostic
        # continuity. Disclosed in the module docstring and handoff.
        books["LINEAGE_COST"] = {
            "fee_rate": FEE_RATE_CURRENT,
            "slippage_ticks": SLIPPAGE_TICKS_CURRENT,
        }
    return books


def caps_for(
    family_id: str,
    identity_entry: Mapping[str, Any],
    engine: Mapping[str, float],
) -> risk.FamilyRiskCaps:
    """Frozen virtual risk caps (mirror of the smoke `_caps_for`
    derivation; all numbers verbatim identity or pinned engine config)."""
    if family_id == FAMILY_ILLIQ:
        return risk.FamilyRiskCaps(
            family_id=family_id,
            target_gross=1.0,  # frozen gross_by_construction (quintile mirror)
            hard_gross_cap=float(engine["hard_gross_cap"]),
            hard_abs_net_cap=float(engine["hard_abs_net_cap"]),
            dollar_neutral=True,
            btc_beta_neutral=True,
            btc_beta_tolerance=float(engine["btc_beta_tolerance"]),
            source="identity_manifest:ILLIQ-AMIHUD-28D-W",
        )
    params = identity_entry["score_affecting_parameters"]
    return risk.caps_from_identity_params(family_id, params)


def snapshot_spec_for(family_id: str) -> Dict[str, Dict[str, Any]]:
    if family_id == FAMILY_ILLIQ:
        return {
            "bars": {
                "symbols": list(ILLIQ_CANDIDATE_UNIVERSE),
                "interval": "15m",
                "lookback_seconds": FORMATION_LOOKBACK_SECONDS,
            }
        }
    if family_id == FAMILY_PREMFADE:
        return {
            "basis_buckets": {
                "symbols": list(PREMFADE_CANDIDATE_UNIVERSE),
                "interval": "15m",
                "lookback_seconds": FORMATION_LOOKBACK_SECONDS,
            }
        }
    if family_id == FAMILY_CARRY:
        return {
            "funding_settlements": {
                "symbols": list(CARRY_TRADED_UNIVERSE),
                "lookback_seconds": CARRY_LOOKBACK_SECONDS,
            }
        }
    if family_id == FAMILY_BANDRIDGE:
        # 200 H4 buckets SMA + 30-bar entry channel => 230 H4 = 3680 15m
        # bars = 53.33 days; 60d gives margin. Single symbol BTCUSDT.
        return {
            "bars": {
                "symbols": ["BTCUSDT"],
                "interval": "15m",
                "lookback_seconds": float(60 * 86400),
            }
        }
    raise WorkerConfigError(f"unknown family {family_id!r}")


def engine_config_for(family_id: str) -> Dict[str, Any]:
    """Engine-level adapter parameters (manifest-unpinned numbers).

    Only IlliqAmihudAdapter.required_engine_keys() demands keys; the
    PREMFADE/CARRY adapters derive everything from the manifest."""
    return dict(ILLIQ_ENGINE) if family_id == FAMILY_ILLIQ else {}


def btc_betas_for(family_id: str) -> Optional[Dict[str, float]]:
    """ILLIQ structural-beta convention (module docstring disclosure).

    PREMFADE/CARRY caps are not beta-neutral; their btc_beta exposure
    diagnostic stays None (no measured surface is asserted)."""
    if family_id == FAMILY_ILLIQ:
        return {symbol: 1.0 for symbol in ILLIQ_CANDIDATE_UNIVERSE}
    return None


# ----------------------------------------------------------------------
# executor construction
# ----------------------------------------------------------------------
def build_executors(
    runtime_root: str,
    shadow_start_utc: Optional[str],
    feed: Any = None,
    *,
    namespace: str = LABEL_PROSPECTIVE,
) -> "Dict[str, ForwardExecutor]":
    """Build the three production ForwardExecutors in FIXED order.

    Fails closed unless the identity manifest, the archived tick bytes,
    the frozen schedules and the executor config contract all agree
    (identity pinning is exercised by every adapter's validate_config).
    PROSPECTIVE requires ``shadow_start_utc`` (refused at construction
    otherwise, executor contract); REPLAY_NOT_PROSPECTIVE may pass None.
    """
    if namespace not in start_guard.KNOWN_NAMESPACES:
        raise WorkerConfigError(
            f"unknown namespace {namespace!r}; refusing to build executors"
        )
    if namespace == LABEL_PROSPECTIVE and shadow_start_utc is None:
        raise start_guard.StartGuardError(
            "PROSPECTIVE worker build requires shadow_start_utc "
            "(SHADOW_START_UTC); refusing to construct (fail closed)"
        )
    manifest = load_identity_manifest()
    entries = identity_entries_by_family(manifest)
    symbol_info = load_archived_symbol_info()
    assert_candidates_in_archive(symbol_info)
    measured_ticks = measured_ticks_from_info(symbol_info)
    if feed is None:
        feed = default_feed()

    executors: Dict[str, ForwardExecutor] = {}
    for family_id in FAMILY_ORDER:
        entry = entries[family_id]
        engine = engine_config_for(family_id)
        config: Dict[str, Any] = {
            "code_freeze_sha": CODE_FREEZE_SHA,
            "namespace": namespace,
            "tick_size": tick_mapping_for(family_id, measured_ticks, symbol_info),
            "tick_size_default": TICK_SIZE_DEFAULT,
            "cost_books": cost_books_for(family_id),
            "primary_book": "CURRENT_CONSERVATIVE_COST",
            "caps": caps_for(family_id, entry, engine),
            "snapshot_spec": snapshot_spec_for(family_id),
            "feature_cutoff_offset_seconds": FEATURE_CUTOFF_OFFSET_SECONDS,
            "schedule": scheduler.FAMILY_SCHEDULES[family_id],
            "identity_entry": entry,
            "engine": engine,
            "btc_betas": btc_betas_for(family_id),
        }
        if family_id == FAMILY_CARRY:
            # Fills price off the first completed 15m bar strictly after
            # the decision; the funding-only snapshot_spec carries no
            # bars, so the fill universe is declared explicitly.
            config["fill_symbols"] = list(CARRY_TRADED_UNIVERSE)
            # AMENDMENT A3: stop-open + terminal-row law (see the
            # XSECT_RETIRE_* constants above). Other families' configs
            # (and therefore their config digests) are untouched.
            config["retire_after_utc"] = XSECT_RETIRE_AFTER_UTC
            config["retire_terminal"] = dict(XSECT_RETIRE_TERMINAL)
        if family_id == FAMILY_BANDRIDGE:
            # A2 P-4 (fail-closed hash-match-in-values): refuse to build
            # the BANDRIDGE executor unless its cost books equal the
            # identity pin exactly. A mismatch means two cost laws would
            # coexist — every record would be UNPINNED_COST_LAW — so the
            # worker refuses to start the family instead.
            built_books = cost_books_for(family_id)
            if built_books != BANDRIDGE_COST_BOOKS_PINNED:
                raise WorkerConfigError(
                    "BTC4H-BANDRIDGE cost law does not match the identity "
                    "pin (fee_bps_per_side 6.0 full stack); refusing to "
                    "build the executor (UNPINNED_COST_LAW fail-closed; "
                    "amendment A2 P-4)"
                )
            # A2 P-1: sizing law B (cost-aware) enabled for this family
            # only; the executor's config_digest includes the flag ONLY
            # when enabled, so other families' digests stay identical.
            config["cost_aware_sizing"] = True
        executors[family_id] = ForwardExecutor(
            family_id, config, runtime_root, feed, shadow_start_utc
        )
    return executors


# ----------------------------------------------------------------------
# heartbeat (Q-13)
# ----------------------------------------------------------------------
class HeartbeatWriter:
    """Atomic-ish heartbeat file held open on a stable file descriptor.

    Every write fstats the OPEN HANDLE and os.stats the PATH: a mismatch
    means the heartbeat was replaced/removed underneath the worker
    (Q-13 tamper/restart detection), surfaced as
    ``heartbeat_inode_vs_path_check.match == false``.
    """

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
# main loop
# ----------------------------------------------------------------------
def _next_decision(executor: ForwardExecutor, now_iso: str) -> Optional[str]:
    """Next EXECUTABLE decision stamp (never before SHADOW_START_UTC in
    the PROSPECTIVE namespace; None when none exists within the 9-day
    horizon)."""
    from_moment = start_guard.parse_moment(now_iso)
    if (
        executor.namespace == LABEL_PROSPECTIVE
        and executor.shadow_start_utc is not None
    ):
        from_moment = max(from_moment, start_guard.parse_moment(executor.shadow_start_utc))
    horizon = start_guard.to_iso_z(from_moment + dt.timedelta(days=9))
    upcoming = scheduler.pending_decisions(
        executor.family_id,
        start_guard.to_iso_z(from_moment),
        horizon,
        schedule=executor.schedule,
    )
    return upcoming[0] if upcoming else None


def _last_completed(executor: ForwardExecutor) -> Optional[Dict[str, Any]]:
    records = ledger.scan_events(executor.ledger_file)
    if not records:
        return None
    latest = max(records, key=lambda r: r["scheduled_decision_utc"])
    return {
        "event_id": latest["event_id"],
        "scheduled_decision_utc": latest["scheduled_decision_utc"],
        "data_status": latest.get("data_status"),
        "risk_status": latest.get("risk_status"),
        "accounting_status": latest.get("accounting_status"),
    }


def run_loop(
    executors: Mapping[str, ForwardExecutor],
    runtime_root: str,
    *,
    interval_seconds: float = 300.0,
    once: bool = False,
) -> int:
    """The production polling loop. Returns the process exit code."""
    heartbeat = HeartbeatWriter(
        os.path.join(runtime_root, "runtime", "heartbeat.json")
    )
    loop_count = 0
    last_error: Optional[str] = None
    last_completed: Dict[str, Optional[Dict[str, Any]]] = {
        family_id: None for family_id in executors
    }
    stop = {"flag": False, "signal": None}

    def _handle_signal(signum, _frame):  # noqa: ANN001 - signal handler
        stop["flag"] = True
        stop["signal"] = signal.Signals(signum).name

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    while not stop["flag"]:
        loop_count += 1
        now_iso = start_guard.to_iso_z(dt.datetime.now(dt.timezone.utc))
        loop_results: Dict[str, Any] = {}
        for family_id, executor in executors.items():  # FIXED order
            try:
                result = executor.run_due(now_iso)
                loop_results[family_id] = {
                    "due": len(result.get("due", [])),
                    "executed": len(result.get("executed", [])),
                    "emitted": result.get("emitted", 0),
                    "data_blocked": result.get("data_blocked", 0),
                    "risk_blocked": result.get("risk_blocked", 0),
                    "accounting_fail_closed": result.get(
                        "accounting_fail_closed", 0
                    ),
                    "skipped_existing": result.get("skipped_existing", 0),
                    "pending_fill_bar": len(result.get("pending_fill_bar", [])),
                }
                last_completed[family_id] = _last_completed(executor)
            except Exception as exc:  # noqa: BLE001 - record + continue
                last_error = f"{family_id}: {type(exc).__name__}: {exc}"
                loop_results[family_id] = {"error": last_error}

        payload: Dict[str, Any] = {
            "schema": HEARTBEAT_SCHEMA,
            "namespace": LABEL_PROSPECTIVE,
            "label": LABEL_PROSPECTIVE,
            "pid": os.getpid(),
            "loop_count": loop_count,
            "last_loop_utc": now_iso,
            "interval_seconds": interval_seconds,
            "next_decision_per_family": {
                family_id: _next_decision(executor, now_iso)
                for family_id, executor in executors.items()
            },
            "last_completed": dict(last_completed),
            "ledger_byte_counts": {
                family_id: ledger.byte_count(executor.ledger_file)
                for family_id, executor in executors.items()
            },
            "loop_results": loop_results,
            "last_error": last_error,
            "shutdown_signal": stop["signal"],
        }
        try:
            inode_check = heartbeat.write(payload)
            payload["heartbeat_inode_vs_path_check"] = inode_check
            heartbeat.write(payload)
        except Exception as exc:  # noqa: BLE001 - heartbeat failure != crash
            last_error = f"heartbeat: {type(exc).__name__}: {exc}"

        if once:
            break

        deadline = time.monotonic() + interval_seconds
        while not stop["flag"] and time.monotonic() < deadline:
            time.sleep(min(1.0, max(0.0, deadline - time.monotonic())))

    # Final heartbeat on shutdown (SIGTERM/SIGINT/once): exit 0.
    now_iso = start_guard.to_iso_z(dt.datetime.now(dt.timezone.utc))
    payload["last_loop_utc"] = now_iso
    payload["shutdown_signal"] = stop["signal"] or "loop_exit"
    payload["loop_count"] = loop_count
    payload["last_error"] = last_error
    try:
        heartbeat.write(payload)
    except Exception:  # noqa: BLE001 - best-effort final write
        pass
    heartbeat.close()
    return 0


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="shadow_worker",
        description=(
            "PROSPECTIVE-SHADOW-V1 E-phase forward worker "
            "(INTERNAL PAPER ONLY: TARGET_INTENT + virtual fills; "
            "keyless public data only)."
        ),
    )
    parser.add_argument(
        "--shadow-start",
        default=None,
        help="SHADOW_START_UTC (ISO-Z, REQUIRED for the PROSPECTIVE namespace)",
    )
    parser.add_argument(
        "--runtime-root",
        default="results/prospective_shadow_v1",
        help="runtime root; prospective ledgers land under <root>/ledgers/",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="single pass then exit (for supervision)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=300.0,
        help="poll interval seconds (default 300)",
    )
    args = parser.parse_args(argv)

    if not args.shadow_start:
        print(
            "REFUSED: --shadow-start (SHADOW_START_UTC) is REQUIRED for the "
            "PROSPECTIVE namespace; the worker never runs pre-activation "
            "without an explicit start (fail closed).",
            file=sys.stderr,
        )
        return 2
    try:
        start_guard.parse_moment(args.shadow_start)
    except start_guard.StartGuardError as exc:
        print(f"REFUSED: invalid --shadow-start: {exc}", file=sys.stderr)
        return 2

    executors = build_executors(args.runtime_root, args.shadow_start)
    return run_loop(
        executors,
        args.runtime_root,
        interval_seconds=args.interval,
        once=args.once,
    )


if __name__ == "__main__":
    sys.exit(main())
