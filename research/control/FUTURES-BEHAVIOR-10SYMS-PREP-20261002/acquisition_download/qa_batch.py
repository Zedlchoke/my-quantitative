#!/usr/bin/env python3
"""qa_batch.py — per-batch QA + parquet conversion for ACQ-DOWNLOAD.

Implements STEP 4 of the dispatch for one delivered chunk: DBN decode via
the cycle's own adapter (code/futbt/dbn), fail-closed schema handling,
record-count reconciliation vs the pre-submit quote (tolerance +/-2%),
duplicates/gaps/monotonic + coverage checks, negative-price preservation,
6J scale sanity, DST/session summary, actual-vs-requested window, then
parquet conversion (ints end-to-end; NO floats in the value path).

Scratch decompression files are lane-owned temps (deleted after QA; source
.dbn.zst is immutable and kept forever). Registry: definitions build the
contract registry; ohlcv/statistics chunks resolve identity via the
registry with DBN-prelude symbol-mapping fallback (typed, counted, never
silent).
"""

from __future__ import annotations

import datetime as dt
import json
import re
import sys
import time
import traceback
from collections import defaultdict
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import zstandard

# Strict outright futures raw-symbol pattern for the 10-root corpus
# (venue convention measured: ROOT + month-code + ONE-digit year, e.g.
# NQZ5/CLF7/6JZ6). Everything else riding along in definition streams —
# dash spreads (CLF4-BZF4), NG seasonal strips (NG:SA 05M X4), other
# composites — is EXCHANGE-RE-LISTED under new instrument_ids over time
# (measured 2026-10-02), is not part of the outright corpus, and is
# counted in a census instead of identity-tracked.
OUTRIGHT_RE = re.compile(r"^(NQ|ES|CL|NG|GC|SI|6E|6J|6B|6A)[A-Z][0-9]$")

TASK = Path("/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/"
            "prep/research/control/FUTURES-BEHAVIOR-10SYMS-PREP-20261002")
sys.path.insert(0, str(TASK / "code"))
from futbt.dbn import ingest, qa, spec, wire  # noqa: E402

RAW = Path("/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim")
DBN_DIR = RAW / "raw" / "dbn_zst"
SCRATCH = RAW / "scratch"
PARQUET_DIR = RAW / "parquet"
REGISTRY_JSON = TASK / "acquisition_download" / "CONTRACT_REGISTRY.json"
QA_DIR = TASK / "acquisition_download" / "qa"

RECORD_TOLERANCE = 0.02
NS = 1_000_000_000


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds")


def decompress_to_scratch(zst_path: Path, scratch_path: Path) -> int:
    dctx = zstandard.ZstdDecompressor()
    n = 0
    with open(zst_path, "rb") as src, open(scratch_path, "wb") as out:
        reader = dctx.stream_reader(src)
        while True:
            chunk = reader.read(1 << 24)
            if not chunk:
                break
            out.write(chunk)
            n += len(chunk)
    return n


def load_registry() -> ingest.ContractRegistry:
    reg = ingest.ContractRegistry()
    if REGISTRY_JSON.exists():
        blob = json.loads(REGISTRY_JSON.read_text())
        for raw, ident in blob["by_raw"].items():
            ci = ingest.ContractIdentity(
                raw_symbol=ident["raw_symbol"],
                instrument_id=ident["instrument_id"],
                activation=ident["activation"],
                expiration=ident["expiration"],
                maturity_year=ident["maturity_year"],
                maturity_month=ident["maturity_month"],
                min_price_increment=ident["min_price_increment"],
                unit_of_measure_qty=ident["unit_of_measure_qty"],
                exchange=ident["exchange"])
            reg.by_raw[raw] = ci
            reg.by_id[ci.instrument_id] = ci
    return reg


def save_registry(reg: ingest.ContractRegistry) -> None:
    blob = {"updated_utc": now_utc(),
            "n_contracts": len(reg.by_raw),
            "by_raw": {raw: vars(ci) for raw, ci in sorted(reg.by_raw.items())}}
    tmp = REGISTRY_JSON.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(blob, default=str))
    tmp.replace(REGISTRY_JSON)


def frame_mappings_fallback(frame: ingest.Ingested,
                            reg: ingest.ContractRegistry,
                            unresolved: dict) -> None:
    """For instruments present in the frame but absent from the registry:
    resolve raw_symbol via the file's DBN prelude symbol mappings. With
    stype_out=instrument_id each MappingInterval.symbol IS the instrument_id
    string for its date range. Partial identities (zero tick/multiplier,
    flagged) are inserted into the IN-MEMORY registry so adapter QA can run;
    they are never persisted to CONTRACT_REGISTRY.json (def chunks only).

    DECADE-WRAP CONVENTION (measured on the NQ 2010-06 delta chunk): GLBX
    one-digit-year raw symbols repeat each decade — the registry (def
    window 2023-10+) holds NQZ0 = the Dec-2030 LISTING while 2010-era bars
    carry NQZ0 = iid 3088 (Dec-2010). instrument_id is the true identity;
    raw_symbol disambiguates only by ts_event era. So by_id partials are
    ALWAYS inserted; by_raw only when the raw is absent (collision count
    recorded in unresolved['_raw_collisions...'])."""
    have = set(reg.by_id)
    raw_collisions = 0
    for iid in sorted({b.instrument_id for b in frame.bars} |
                      {s.instrument_id for s in frame.statistics}):
        if iid in have:
            continue
        raw = None
        for m in frame.meta.mappings:
            if m.raw_symbol and any(
                    iv.symbol == str(iid) for iv in m.intervals):
                raw = m.raw_symbol
                break
        unresolved[str(iid)] = raw  # None = fully unresolved (blocking)
        if raw is not None:
            partial = ingest.ContractIdentity(
                raw_symbol=raw, instrument_id=iid, activation=0,
                expiration=0, maturity_year=0, maturity_month=0,
                min_price_increment=0, unit_of_measure_qty=0,
                exchange="UNKNOWN_VIA_MAPPING")
            reg.by_id[iid] = partial
            if raw not in reg.by_raw:
                reg.by_raw[raw] = partial
            else:
                raw_collisions += 1
    if raw_collisions:
        unresolved["_raw_collisions_vs_def_window_registry"] = raw_collisions


def dup_mono_check(records: list, key_fields: tuple[str, ...]) -> dict:
    """Duplicate + as-received monotonic check for non-bar records
    (statistics). A duplicate = ALL content fields equal (same key twice);
    same (iid, ts_event, stat_type, ts_ref) with different price/quantity
    is a legitimate sequential venue update (MEASURED: lowest_offer/
    highest_bid/price-limit stats update intra-second with distinct
    sequence numbers), not a duplicate."""
    seen: dict[tuple, int] = {}
    for r in records:
        key = (r.instrument_id, r.ts_event) + tuple(
            getattr(r, f) for f in key_fields)
        seen[key] = seen.get(key, 0) + 1
    dups = sum(1 for n in seen.values() if n > 1)
    non_mono = sum(1 for i in range(1, len(records))
                   if records[i].ts_event < records[i - 1].ts_event)
    return {"n_duplicate_keys": dups, "n_non_monotonic": non_mono}


I64_MAX = (1 << 63) - 1   # 9_223_372_036_854_775_807 (computed — a literal
                           # underscore typo nulled every ts_ref once)


def null_if_undef_ts(v: int):
    """DBN u64 UNDEF sentinel (2^64-1, 'no reference date') -> null for
    int64 parquet columns; MEASURED on stat chunk 2023-10: ~2.9M records
    of quote-side stat types (7/8/17/18) carry it; date-referenced types
    (settlement 3, volume 6, OI 9, ...) carry real ns values."""
    return None if (v is None or v > I64_MAX) else v


def definition_emission_census_raw(scratch_files: list[Path]) -> dict:
    """Census for definition chunks, computed at the WIRE level (the
    DefinitionAction frame drops ts_recv). MEASURED vendor convention on
    real GLBX.MDP3 data (2026-10-02, first chunk): every instrument
    definition is re-broadcast at each session open (same ts_event, ts_recv
    = session start 00:00 UTC) plus redundant exact copies; the merged
    stream is strictly ts_recv-ordered while ts_event jumps at rebroadcast
    blocks. Emission conventions, NOT delivery defects; the registry
    dedupes by construction. Fail only on ts_recv disorder or content
    conflicts inside an exact key."""
    from collections import Counter
    import hashlib
    n_records = 0
    actions: Counter = Counter()
    unique_defs: set = set()
    exact_conflicts = 0
    exact_dup_records = 0
    prev_recv = None
    non_mono_ts_recv = 0
    non_mono_ts_event = 0
    prev_event = None
    exact_sig: dict[tuple, str] = {}
    max_backward_ms = 0.0
    for sf in scratch_files:
        blob = sf.read_bytes()
        _, recs = wire.decode_dbn_bytes(blob)
        del blob
        for r in recs:
            ts_recv = r.fields.get("ts_recv", 0)
            n_records += 1
            actions[str(r.fields.get("security_update_action", "?"))] += 1
            unique_defs.add((r.instrument_id, r.ts_event))
            key = (r.instrument_id, r.ts_event, ts_recv,
                   str(r.fields.get("security_update_action", "?")),
                   r.fields.get("leg_index"))
            sig = hashlib.sha1(repr(sorted(
                (k, v) for k, v in r.fields.items()
                if k != "ts_recv")).encode()).hexdigest()
            if key in exact_sig:
                exact_dup_records += 1
                if exact_sig[key] != sig:
                    exact_conflicts += 1
            else:
                exact_sig[key] = sig
            if prev_recv is not None and ts_recv < prev_recv:
                non_mono_ts_recv += 1
                max_backward_ms = max(max_backward_ms,
                                      (prev_recv - ts_recv) / 1e6)
            prev_recv = ts_recv
            if prev_event is not None and r.ts_event < prev_event:
                non_mono_ts_event += 1
            prev_event = r.ts_event
        del recs, exact_sig
        exact_sig = {}
    return {
        "n_records": n_records,
        "actions": dict(actions),
        "n_unique_instrument_ts_event": len(unique_defs),
        "n_rebroadcast_records": n_records - len(unique_defs),
        "n_exact_duplicate_records": exact_dup_records,
        "n_exact_key_content_conflicts": exact_conflicts,
        "non_monotonic_ts_recv": non_mono_ts_recv,
        "max_backward_ts_recv_ms": round(max_backward_ms, 3),
        "non_monotonic_ts_event_at_rebroadcasts": non_mono_ts_event,
        "note": "session-rebroadcast + redundant copies are vendor "
                "emission convention (measured); registry dedupes",
    }


def parquet_write(frame: ingest.Ingested, reg: ingest.ContractRegistry,
                  unresolved: dict, out_path: Path) -> str:
    def raw_of(iid: int) -> str:
        try:
            return reg.raw_for(iid)
        except Exception:  # noqa: BLE001
            return unresolved.get(str(iid)) or f"UNRESOLVED_{iid}"

    if frame.bars:
        cols = {
            "rtype": pa.array([b.rtype for b in frame.bars], pa.int16()),
            "instrument_id": pa.array([b.instrument_id for b in frame.bars],
                                      pa.uint32()),
            "raw_symbol": pa.array([raw_of(b.instrument_id)
                                    for b in frame.bars], pa.string()),
            "ts_event": pa.array([b.ts_event for b in frame.bars], pa.int64()),
            "open": pa.array([b.open for b in frame.bars], pa.int64()),
            "high": pa.array([b.high for b in frame.bars], pa.int64()),
            "low": pa.array([b.low for b in frame.bars], pa.int64()),
            "close": pa.array([b.close for b in frame.bars], pa.int64()),
            "volume": pa.array([b.volume for b in frame.bars], pa.uint32()),
        }
        table = pa.table(cols)
    elif frame.statistics:
        undef_ts = sum(1 for s in frame.statistics
                       if s.ts_ref > I64_MAX)
        cols = {
            "instrument_id": pa.array([s.instrument_id
                                       for s in frame.statistics], pa.uint32()),
            "raw_symbol": pa.array([raw_of(s.instrument_id)
                                    for s in frame.statistics], pa.string()),
            "ts_event": pa.array([s.ts_event for s in frame.statistics],
                                 pa.int64()),
            "ts_ref": pa.array([null_if_undef_ts(s.ts_ref)
                                for s in frame.statistics], pa.int64()),
            "stat_type": pa.array([s.stat_type for s in frame.statistics],
                                  pa.int16()),
            "stat_flags": pa.array([s.stat_flags for s in frame.statistics],
                                   pa.int16()),
            "price": pa.array([s.price for s in frame.statistics], pa.int64()),
            "quantity": pa.array([s.quantity for s in frame.statistics],
                                 pa.int64()),
            "update_action": pa.array([s.update_action
                                       for s in frame.statistics], pa.int8()),
        }
        table = pa.table(cols)
    elif frame.definitions:
        d = frame.definitions
        cols = {
            "instrument_id": pa.array([x.instrument_id for x in d],
                                      pa.uint32()),
            "raw_symbol": pa.array([x.raw_symbol for x in d], pa.string()),
            "action": pa.array([x.action for x in d], pa.string()),
            "ts_event": pa.array([x.ts_event for x in d], pa.int64()),
            "activation": pa.array([x.activation for x in d], pa.int64()),
            "expiration": pa.array([x.expiration for x in d], pa.int64()),
            "maturity_year": pa.array([x.maturity_year for x in d],
                                      pa.int32()),
            "maturity_month": pa.array([x.maturity_month for x in d],
                                       pa.int16()),
            "min_price_increment": pa.array(
                [x.min_price_increment for x in d], pa.int64()),
            "unit_of_measure_qty": pa.array(
                [x.unit_of_measure_qty for x in d], pa.int64()),
            "exchange": pa.array([x.exchange for x in d], pa.string()),
            "security_type": pa.array([x.security_type for x in d],
                                      pa.string()),
            "instrument_class": pa.array([x.instrument_class for x in d],
                                         pa.string()),
        }
        table = pa.table(cols)
    else:
        raise ValueError("frame has no bars/statistics/definitions")
    pq.write_table(table, out_path, compression="zstd")
    return str(out_path)


def reduce_registry(reg: ingest.ContractRegistry,
                    instrument_ids: set[int]) -> ingest.ContractRegistry:
    """Registry restricted to the chunk's instruments, identities copied
    VERBATIM from the full registry (resolution unchanged for every
    instrument in the chunk). qa_report's settlement_series is O(stats) per
    registry raw; with the full ~20k-contract GLBX registry a statistics
    chunk would be intractable, so QA runs on the reduced view."""
    out = ingest.ContractRegistry()
    for iid in instrument_ids:
        ident = reg.by_id.get(iid)
        if ident is not None:
            out.by_raw[ident.raw_symbol] = ident
            out.by_id[iid] = ident
    return out


def qa_chunk(chunk: dict) -> dict:
    """Run QA for one DOWNLOADED chunk (ledger entry). Returns result dict."""
    line_id = chunk["line_id"]
    schema = chunk["schema"]
    chunk_key = chunk["chunk_key"]
    t0 = time.monotonic()
    result: dict = {
        "chunk_key": chunk_key, "line_id": line_id, "schema": schema,
        "started_utc": now_utc(), "verdict": None, "fail_reasons": [],
        "findings": {}, "parquet": None,
    }
    scratch_files: list[Path] = []
    try:
        reg = load_registry()
        frames: list[ingest.Ingested] = []
        sidecars = []
        for f in chunk["files"]:
            zst = Path(f["local_path"])
            name = zst.name
            if not (name.endswith(".dbn.zst") or name.endswith(".dbn")):
                sidecars.append(name)  # vendor job manifest/condition/metadata
                continue
            if zst.suffix == ".zst":
                scratch = SCRATCH / (zst.stem + ".scratch.dbn")
                scratch.parent.mkdir(parents=True, exist_ok=True)
                decompressed_bytes = decompress_to_scratch(zst, scratch)
                scratch_files.append(scratch)
            else:
                scratch = zst  # plain .dbn (synthetic test path)
                decompressed_bytes = zst.stat().st_size
            frame = ingest.ingest_file(scratch)  # fail-closed inside
            frames.append(frame)
            result.setdefault("meta", []).append({
                "file": zst.name,
                "decompressed_bytes": decompressed_bytes,
                "zst_bytes": zst.stat().st_size,
                "sha256_decompressed": qa.sha256_file(str(scratch)),
                "dataset": frame.meta.dataset,
                "schema": spec.SCHEMA_NAMES.get(frame.meta.schema),
                "dbn_version": frame.meta.version,
                "stype_in": spec.STYPE_NAMES.get(frame.meta.stype_in),
                "stype_out": spec.STYPE_NAMES.get(frame.meta.stype_out),
                "start_ns": frame.meta.start,
                "end_ns": frame.meta.end,
                "n_mappings": len(frame.meta.mappings),
            })

        if not frames:
            result["fail_reasons"].append("NO_DBN_FILES_IN_CHUNK")
            result["verdict"] = "FAIL"
            result["elapsed_s"] = round(time.monotonic() - t0, 1)
            return result

        merged = ingest.Ingested(
            source="+".join(f.source for f in frames), meta=frames[0].meta)
        for fr in frames:
            merged.bars.extend(fr.bars)
            merged.definitions.extend(fr.definitions)
            merged.statistics.extend(fr.statistics)
        result["sidecar_files"] = sidecars

        # --- counts vs quote ---
        actual = (len(merged.bars) + len(merged.definitions)
                  + len(merged.statistics) + len(merged.trades)
                  + len(merged.quotes))
        quoted = int(chunk["quote"]["records"])
        result["records_actual"] = actual
        result["records_quoted"] = quoted
        drift = abs(actual - quoted) / quoted if quoted else 1.0
        result["records_drift_pct"] = round(drift * 100, 4)
        if drift > RECORD_TOLERANCE:
            result["fail_reasons"].append(
                f"RECORD_COUNT_DRIFT {drift*100:.3f}% > {RECORD_TOLERANCE*100}%")

        if actual == 0:
            result["fail_reasons"].append("EMPTY_CHUNK")

        # --- schema/identity ---
        unresolved: dict = {}
        if schema == "definition":
            # Registry tracks OUTRIGHT contracts only (our corpus: the 10
            # roots' futures; identity join vs IBKR is outright-only).
            # MEASURED (chunk 2025-10): exchange re-lists SPREAD composites
            # (class S, dash raw_symbols like CLF4-BZF4) under NEW
            # instrument_ids over time -> the adapter's clash guard fires
            # on a vendor re-list, not an outright identity defect
            # (outright symbols: 0 multi-iid across all delivered chunks).
            # Spreads are counted, never identity-tracked.
            spread_actions = 0
            outright_actions = 0
            outright_defs = []
            for d in merged.definitions:
                if OUTRIGHT_RE.match(d.raw_symbol):
                    outright_actions += 1
                    outright_defs.append(d)
                else:
                    spread_actions += 1
            # Registry construction is ORDER-INSENSITIVE: apply outright
            # definitions sorted by ts_event. MEASURED (chunk 2026-07..10):
            # the vendor's merged definition stream contains small
            # out-of-order ts_recv blocks (866/1.06M records, backward
            # jumps 68-139s, clustered at a 2026-07-26 capture event) with
            # byte-exact record integrity (count == quote). Identity from
            # ts-sorted application is deterministic under that anomaly.
            outright_defs.sort(key=lambda d: (d.ts_event, d.instrument_id))
            for d in outright_defs:
                reg.apply(d)
            save_registry(reg)
            result["registry_contracts_after"] = len(reg.by_raw)
            result["findings"]["definition_action_split"] = {
                "outright_applied": outright_actions,
                "spread_census_not_tracked": spread_actions,
                "note": "spread composites (dash raw_symbols) re-listed "
                        "under new instrument_ids by the exchange; not "
                        "part of the 10-root outright corpus",
            }
        else:
            frame_mappings_fallback(merged, reg, unresolved)
            fully = [k for k, v in unresolved.items() if v is None]
            result["findings"]["identity_unresolved_via_mapping"] = {
                k: v for k, v in unresolved.items()}
            if fully:
                result["fail_reasons"].append(
                    f"IDENTITY_UNRESOLVED {len(fully)} instrument(s) absent "
                    "from registry AND file mappings")

        # --- non-bar duplicate/monotonic checks (adapter covers bars only) ---
        if merged.statistics:
            stat_dm = dup_mono_check(
                merged.statistics,
                ("stat_type", "ts_ref", "stat_flags", "price", "quantity",
                 "update_action"))
            result["findings"]["statistics_dup_mono"] = stat_dm
            undef_ts = sum(1 for s in merged.statistics
                           if s.ts_ref > I64_MAX)
            result["findings"]["statistics_undef_ts_ref"] = {
                "n_records": len(merged.statistics),
                "n_undef_ts_ref": undef_ts,
                "note": "DBN u64 UNDEF sentinel ('no reference date'), "
                        "mostly quote-side stat types (lowest_offer/"
                        "highest_bid/price limits); stored as NULL in "
                        "parquet",
            }
            if stat_dm["n_duplicate_keys"]:
                # which stat types duplicated: volume(6)/OI(9) duplicates
                # would corrupt aggregates -> always FAIL. MEASURED: the
                # single byte-identical pair in 3.4M records (chunk
                # 2023-10) was stat_type 2 indicative_opening_price =
                # benign redundant-feed re-emission.
                from collections import Counter as _C
                _seen: set = set()
                _c: dict = _C()
                for s in merged.statistics:
                    k = (s.instrument_id, s.ts_event, s.stat_type,
                         s.ts_ref, s.stat_flags, s.price, s.quantity,
                         s.update_action)
                    if k in _seen:
                        _c[s.stat_type] += 1
                    _seen.add(k)
                dup_types = dict(_c)
                result["findings"]["statistics_dup_stat_types"] = dup_types
                frac = stat_dm["n_duplicate_keys"] / max(
                    1, len(merged.statistics))
                if (set(dup_types) & {6, 9}) or frac > 0.0001:
                    result["fail_reasons"].append(
                        f"STATISTICS_DUPLICATES {stat_dm} "
                        f"types={dup_types}")
            if stat_dm["n_non_monotonic"]:
                result["fail_reasons"].append(
                    f"STATISTICS_DISORDER {stat_dm}")
        if merged.definitions:
            census = definition_emission_census_raw(scratch_files)
            result["findings"]["definitions_emission_census"] = census
            n = census["n_records"] or 1
            frac = census["non_monotonic_ts_recv"] / n
            census["non_monotonic_ts_recv_fraction"] = round(frac, 6)
            if (census["non_monotonic_ts_recv"] and
                    (frac > 0.005 or census["max_backward_ts_recv_ms"] > 3600_000)):
                result["fail_reasons"].append(
                    "DEFINITIONS_TS_RECV_DISORDER "
                    f"{census['non_monotonic_ts_recv']} ({frac:.4%}), "
                    f"max backward {census['max_backward_ts_recv_ms']} ms")
            if census["n_exact_key_content_conflicts"]:
                result["fail_reasons"].append(
                    "DEFINITION_EXACT_KEY_CONTENT_CONFLICTS "
                    f"{census['n_exact_key_content_conflicts']}")

        # --- adapter QA bundle (dups/gaps/monotonic/coverage/sessions) ---
        # Reduced registry view: only instruments present in this chunk
        # (settlement_series is O(stats) per registry raw; full GLBX
        # registry would make statistics chunks intractable).
        chunk_iids = ({b.instrument_id for b in merged.bars}
                      | {s.instrument_id for s in merged.statistics})
        qa_reg = (reduce_registry(reg, chunk_iids)
                  if (merged.bars or merged.statistics) else reg)
        if merged.bars:
            report = qa.qa_report(frames, qa_reg)
        elif merged.statistics:
            # statistics-only chunk: assemble the adapter bundle with the
            # stats PRE-GROUPED per instrument (settlement_series is
            # O(all_stats) per raw inside qa_report; grouping once is O(n))
            from futbt.dbn.ohlcv import settlement_series
            stats_by_iid: dict[int, list] = defaultdict(list)
            for s in merged.statistics:
                stats_by_iid[s.instrument_id].append(s)
            settlements_by_raw = {}
            for iid, slist in stats_by_iid.items():
                raw = qa_reg.raw_for(iid)
                settlements_by_raw[raw] = settlement_series(
                    slist, qa_reg, raw)
            all_stats = merged.statistics
            report = {
                "time_series": {},
                "coverage": {},
                "crossed_quotes": {},
                "unknown_stat_types": sorted(
                    {s.stat_type for s in all_stats
                     if s.stat_type not in spec.STAT_TYPE_NAMES}),
                "roll_window": qa.roll_window_summary(all_stats, qa_reg),
                "settlements_by_raw_n": {k: len(v) for k, v in
                                         settlements_by_raw.items()},
                "note": "statistics-only assembly (adapter functions, "
                        "pre-grouped); qa_report path is bar-driven",
            }
        else:
            report = {"time_series": {}, "coverage": {},
                      "crossed_quotes": {}, "unknown_stat_types": [],
                      "roll_window": {}, "note": "definitions-only chunk"}
        result["qa_bundle_path"] = None
        ts_bad = {k: v for k, v in report["time_series"].items()
                  if v.get("n_non_monotonic", 0)}
        result["findings"]["time_series_not_ok"] = ts_bad
        result["findings"]["unknown_stat_types"] = report["unknown_stat_types"]
        result["findings"]["n_time_series_checked"] = len(
            report["time_series"])
        if ts_bad:
            result["fail_reasons"].append(
                f"NON_MONOTONIC_BARS {list(ts_bad)[:5]}")
        cov_summary = {}
        neg_total = 0
        for raw, cov in report["coverage"].items():
            neg_total += cov["n_negative_price_bars"]
            kinds: dict[str, int] = {}
            for s in cov["sessions"]:
                kinds[s["kind"]] = kinds.get(s["kind"], 0) + 1
            cov_summary[raw] = {
                "n_bars": cov["n_bars"],
                "n_sessions_with_bars": cov["n_sessions_with_bars"],
                "session_kinds": kinds,
                "n_negative_price_bars": cov["n_negative_price_bars"],
                "n_stale_flat_bars": cov["n_stale_flat_bars"],
                "n_close_only_sessions": cov["n_close_only_sessions"],
            }
        result["coverage_summary_n_contracts"] = len(cov_summary)
        result["negative_price_bars_total"] = neg_total
        result["coverage_sample"] = dict(list(cov_summary.items())[:6])
        if report["unknown_stat_types"]:
            result["fail_reasons"].append(
                f"UNKNOWN_STAT_TYPES {report['unknown_stat_types']}")

        # --- window actual vs requested ---
        tss = [b.ts_event for b in merged.bars] + \
              [s.ts_event for s in merged.statistics] + \
              [d.ts_event for d in merged.definitions]
        if tss:
            lo, hi = min(tss), max(tss)
            req_lo = int(dt.datetime.fromisoformat(
                chunk["start"]).replace(tzinfo=dt.timezone.utc)
                .timestamp() * NS)
            req_hi = int(dt.datetime.fromisoformat(
                chunk["end"]).replace(tzinfo=dt.timezone.utc)
                .timestamp() * NS)
            result["window"] = {
                "actual_min_ts_event": lo, "actual_max_ts_event": hi,
                "requested_start_ns": req_lo, "requested_end_excl_ns": req_hi,
                "min_ge_requested": lo >= req_lo,
                "max_lt_requested_end": hi < req_hi,
            }

        # --- outright vs spread census (parent requests include exchange
        # calendar-spread instruments whose bars are price DIFFERENCES —
        # MEASURED on 6J 2026-01..07: spreads 0.000013-0.00025 vs outrights
        # 0.00615-0.00676; downstream uses OUTRIGHT_RE to filter) ---
        if merged.bars:
            def _raw_of(iid):
                try:
                    return qa_reg.raw_for(iid)
                except Exception:  # noqa: BLE001
                    return unresolved.get(str(iid)) or f"UNRESOLVED_{iid}"
            n_outright_bars = sum(
                1 for b in merged.bars
                if OUTRIGHT_RE.match(_raw_of(b.instrument_id)))
            result["findings"]["bars_outright_vs_spread"] = {
                "n_bars_total": len(merged.bars),
                "n_outright_bars": n_outright_bars,
                "n_spread_or_other_bars": len(merged.bars) - n_outright_bars,
            }

        # --- 6J scale sanity (OUTRIGHT contracts only; quote convention
        # USD per JPY ~0.004..0.012; spread bars are price differences and
        # are excluded) ---
        if "6J" in ",".join(chunk["symbols"]):
            jnanos = [b.close for b in merged.bars
                      if OUTRIGHT_RE.match(_raw_of(b.instrument_id))]
            if jnanos:
                lo_p, hi_p = min(jnanos) / 1e9, max(jnanos) / 1e9
                result["findings"]["6J_scale"] = {
                    "min_price": lo_p, "max_price": hi_p,
                    "sane": 0.003 <= lo_p and hi_p <= 0.02}
                if not (0.003 <= lo_p and hi_p <= 0.02):
                    result["fail_reasons"].append("6J_SCALE_OUT_OF_RANGE")

        # --- parquet ---
        pq_dir = PARQUET_DIR / line_id
        pq_dir.mkdir(parents=True, exist_ok=True)
        pq_path = pq_dir / f"{chunk_key}.parquet"
        parquet_write(merged, reg, unresolved, pq_path)
        result["parquet"] = {"path": str(pq_path),
                             "bytes": pq_path.stat().st_size}

        # full adapter bundle to disk (evidence)
        QA_DIR.mkdir(parents=True, exist_ok=True)
        bundle_path = QA_DIR / f"{chunk_key}.qa_bundle.json"
        try:
            bundle_path.write_text(json.dumps(
                {"chunk_key": chunk_key,
                 "coverage": {k: v for k, v in list(
                     report["coverage"].items())[:2000]},
                 "roll_window": report["roll_window"],
                 "crossed_quotes": report["crossed_quotes"]},
                default=str))
            result["qa_bundle_path"] = str(bundle_path)
        except Exception:  # noqa: BLE001
            result["qa_bundle_path"] = None

        result["verdict"] = ("PASS" if not result["fail_reasons"]
                             else "FAIL")
        result["elapsed_s"] = round(time.monotonic() - t0, 1)
        return result
    except Exception as exc:  # noqa: BLE001
        result["verdict"] = "FAIL_THROWN"
        result["fail_reasons"].append(
            f"{type(exc).__name__}: {str(exc)[:400]}")
        result["traceback_tail"] = traceback.format_exc()[-1500:]
        result["elapsed_s"] = round(time.monotonic() - t0, 1)
        return result
    finally:
        for s in scratch_files:
            try:
                s.unlink()
            except FileNotFoundError:
                pass


if __name__ == "__main__":
    chunk = json.loads(Path(sys.argv[1]).read_text())
    print(json.dumps(qa_chunk(chunk), default=str)[:4000])
