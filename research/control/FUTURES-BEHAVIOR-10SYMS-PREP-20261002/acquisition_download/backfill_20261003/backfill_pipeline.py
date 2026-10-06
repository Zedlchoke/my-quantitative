#!/usr/bin/env python3
"""backfill_pipeline.py — FX-BACKFILL lane (FUTURES-DEEPRESEARCH-V2-20261003).

Owner mission (verbatim): 'tải lùi về cho các mã tiền tệ thêm xíu nữa' —
extend 6E/6J/6B/6A ohlcv-1m history backwards. Existing coverage (parent
COMPLETION_LEDGER.json, all four roots, ledger-verified): 2022-01-01 ->
2026-10-01 continuous. New windows butt EXACTLY: [start, 2022-01-01).

Budget law (hard, dispatch FUTURES-DEEPRESEARCH-V2-20261003):
  additional spend <= $16.19  (cumulative <= $122.00 = owner $125 ceiling
  minus $3 drift buffer; parent delivered $105.810097; observed
  quote-vs-bill drift so far $0.00 across 72 chunks).
  Gate re-quotes EVERY chunk immediately before its submit; a projected
  breach stops typed BUDGET_CEILING_REACHED. Never exceed.

Reuse: predecessor ACQ-DOWNLOAD pipeline discipline verbatim (per-chunk
get_cost gate, SUBMITTED-first ledger, exact-param job dedupe via
batch.list_jobs, vendor file sha256, adapter QA via qa_batch.qa_chunk,
parquet ints-only, iCloud mirror via mirror_batch.mirror_chunk into
av1-trim/{line_id}/{chunk_key}/). qa_batch.QA_DIR is repointed into this
lane's owned path; CONTRACT_REGISTRY.json is read-only here (ohlcv chunks
never write it).

Machine-wide heavy lock (governance.heavy_lock) is held for the whole
paid phase and released on exit.

Usage:
  backfill_pipeline.py --quote-only [--start 2020-01-01]
      metadata-only quotes for all candidate starts; no submit, no spend.
  backfill_pipeline.py --start 2020-01-01
      full run (quote -> gate -> submit -> download -> QA -> mirror).
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
import traceback
from pathlib import Path

TASK = Path("/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/"
            "prep/research/control/FUTURES-BEHAVIOR-10SYMS-PREP-20261002")
ACQ = TASK / "acquisition_download"
BACKFILL = ACQ / "backfill_20261003"
sys.path.insert(0, str(ACQ))
import qa_batch  # noqa: E402
import mirror_batch  # noqa: E402

# Keep ALL lane writes inside backfill_20261003/** (lane ownership law);
# qa_chunk reads CONTRACT_REGISTRY (never writes it for ohlcv chunks).
qa_batch.QA_DIR = BACKFILL / "qa"

PARENT_LEDGER = ACQ / "COMPLETION_LEDGER.json"
LEDGER = BACKFILL / "BACKFILL_LEDGER.json"
STOP_FILE = BACKFILL / "BACKFILL_STOP.json"
QUOTES_FILE = BACKFILL / "BACKFILL_QUOTES.json"

RAW = Path("/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim")
DBN_DIR = RAW / "raw" / "dbn_zst"

KEY_PATH = Path(
    "/Users/hoangminhlong/.config/my-quantitative-secrets/databento-api-key")
TOKEN_RE = re.compile(r"db-[A-Za-z0-9_\-]{12,}")

ROOTS = ["6E", "6J", "6B", "6A"]
TARGET_START = "2020-01-01"       # dispatch target
FALLBACK_START = "2021-01-01"     # symmetric shrink if target quotes > cap
BUTT_END = "2022-01-01"           # EXACT start of existing coverage per root
CHUNK_MONTHS = 24                 # predecessor convention for backfill lines

ADDITIONAL_CAP_USD = 16.19        # this lane's additional-spend cap
CUMULATIVE_CAP_USD = 122.00       # owner ceiling $125 minus $3 drift buffer
EPS = 1e-9

POLL_S = 30
JOB_TIMEOUT_S = 6 * 3600

COMMITTED_STATES = {"SUBMITTED", "DOWNLOADING", "DOWNLOADED", "QA_PASS",
                    "QA_FAIL", "MIRRORED"}
DELIVERED_STATES = {"DOWNLOADED", "QA_PASS", "QA_FAIL", "MIRRORED"}


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds")


def redact(text: str) -> str:
    return TOKEN_RE.sub("db-REDACTED", text)


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 22), b""):
            h.update(block)
    return h.hexdigest()


def free_gb() -> float:
    s = os.statvfs(str(RAW))
    return s.f_bavail * s.f_frsize / 1e9


# ---------------------------------------------------------------- parent spend
def parent_delivered_usd() -> tuple[float, dict]:
    """Delivered spend per the parent ledger (read-only; single authority for
    prior windows so new ones butt exactly with no double-billing)."""
    led = json.loads(PARENT_LEDGER.read_text())
    delivered = sum(c["quote"]["get_cost"] for c in led["chunks"].values()
                    if c.get("state") in DELIVERED_STATES
                    and c.get("quote", {}).get("get_cost"))
    rt = led.get("running_totals", {})
    cross = rt.get("delivered_usd")
    if cross is not None and abs(delivered - cross) > 1e-6:
        raise SystemExit(f"FATAL: parent ledger drift recomputed={delivered} "
                         f"vs running_totals={cross}")
    # existing FX window starts per root (butt check, no overlap)
    starts = {}
    for root in ROOTS:
        fx = [c for k, c in led["chunks"].items()
              if c.get("schema") == "ohlcv-1m"
              and root in ",".join(c.get("symbols", []))]
        if not fx:
            raise SystemExit(f"FATAL: no existing ohlcv chunks for {root}")
        starts[root] = min(c["start"] for c in fx)
    return delivered, {"fx_existing_starts": starts,
                       "parent_running_totals": rt}


# ---------------------------------------------------------------- chunk plan
def add_months(d: dt.date, n: int) -> dt.date:
    y = d.year + (d.month - 1 + n) // 12
    m = (d.month - 1 + n) % 12 + 1
    return d.replace(year=y, month=m, day=1)


def split_months(start: str, end: str, chunk_months: int) -> list[tuple[str, str]]:
    s = dt.date.fromisoformat(start)
    e = dt.date.fromisoformat(end)
    out = []
    while s < e:
        nxt = min(add_months(s.replace(day=1), chunk_months), e)
        out.append((s.isoformat(), nxt.isoformat()))
        s = nxt
    return out


def build_plan(start: str) -> list[dict]:
    plan: list[dict] = []
    for i, root in enumerate(ROOTS):
        line_id = f"AV1B-O1M-{root}-BACKFILL2"
        for (s, e) in split_months(start, BUTT_END, CHUNK_MONTHS):
            plan.append({
                "chunk_key": f"{line_id}__{s}_{e}",
                "line_id": line_id,
                "dataset": "GLBX.MDP3",
                "schema": "ohlcv-1m",
                "symbols": [f"{root}.FUT"],
                "stype_in": "parent",
                "start": s, "end": e,
                "order": 80 + i * 10,
                "no_overlap_note": (
                    f"ends exactly at existing {root} window start "
                    f"{BUTT_END}; no double-billing"),
            })
    plan.sort(key=lambda c: (c["order"], c["chunk_key"]))
    return plan


# ------------------------------------------------------------------- ledger
def load_ledger(plan: list[dict], start: str) -> dict:
    if LEDGER.exists():
        led = json.loads(LEDGER.read_text())
    else:
        pd_usd, pinfo = parent_delivered_usd()
        led = {"schema": "futures_behavior_fx_backfill_ledger@1",
               "task_id": "FUTURES-DEEPRESEARCH-V2-20261003",
               "lane": "FX-BACKFILL",
               "parent_task": "FUTURES-BEHAVIOR-10SYMS-PREP-20261002",
               "created_utc": now_utc(),
               "owner_mission_verbatim": "tải lùi về cho các mã tiền tệ thêm xíu nữa",
               "budget": {
                   "owner_ceiling_usd": 125.00,
                   "lane_cumulative_cap_usd": CUMULATIVE_CAP_USD,
                   "additional_cap_usd": ADDITIONAL_CAP_USD,
                   "parent_delivered_usd_at_start": round(pd_usd, 6)},
               "parent_state": pinfo,
               "chosen_start": start,
               "chunks": {}}
    for c in plan:
        if c["chunk_key"] not in led["chunks"]:
            led["chunks"][c["chunk_key"]] = {**c, "state": "PLANNED"}
    return led


def save_ledger(led: dict) -> None:
    led["updated_utc"] = now_utc()
    pd_usd, _ = parent_delivered_usd()
    add_committed = sum(c["quote"]["get_cost"] for c in led["chunks"].values()
                        if c.get("state") in COMMITTED_STATES
                        and c.get("quote", {}).get("get_cost"))
    add_delivered = sum(c["quote"]["get_cost"] for c in led["chunks"].values()
                        if c.get("state") in DELIVERED_STATES
                        and c.get("quote", {}).get("get_cost"))
    led["running_totals"] = {
        "parent_delivered_usd": round(pd_usd, 6),
        "additional_committed_usd": round(add_committed, 6),
        "additional_delivered_usd": round(add_delivered, 6),
        "cumulative_committed_usd": round(pd_usd + add_committed, 6),
        "cumulative_cap_usd": CUMULATIVE_CAP_USD,
        "additional_cap_usd": ADDITIONAL_CAP_USD,
        "n_chunks": len(led["chunks"]),
        "n_mirrored": sum(1 for c in led["chunks"].values()
                          if c.get("state") == "MIRRORED")}
    tmp = LEDGER.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(led, indent=1, default=str))
    tmp.replace(LEDGER)


def write_stop(led: dict, stop_type: str, message: str) -> None:
    STOP_FILE.write_text(json.dumps({
        "stop_type": stop_type, "message": message,
        "written_utc": now_utc(),
        "running_totals": led.get("running_totals"),
        "next_chunks_pending": [c["chunk_key"] for c in
                                sorted(led["chunks"].values(),
                                       key=lambda x: x.get("order", 0))
                                if c.get("state") not in
                                COMMITTED_STATES][:8],
    }, indent=1))


# --------------------------------------------------------------- vendor I/O
def get_client():
    import databento as db
    key = KEY_PATH.read_text().strip()
    if not key:
        raise SystemExit("FATAL: key file empty")
    return db.Historical(key=key)


def quote_params(chunk: dict) -> dict:
    return dict(dataset=chunk["dataset"],
                symbols=",".join(chunk["symbols"]),
                schema=chunk["schema"], stype_in=chunk["stype_in"],
                start=chunk["start"], end=chunk["end"])


def quote_chunk(client, chunk: dict) -> dict:
    params = quote_params(chunk)
    for attempt in range(1, 4):
        try:
            cost = float(client.metadata.get_cost(**params))
            size = int(client.metadata.get_billable_size(**params))
            count = int(client.metadata.get_record_count(**params))
            return {"get_cost": cost, "billable_size": size,
                    "records": count, "ts_utc": now_utc(),
                    "attempts": attempt}
        except Exception as exc:  # noqa: BLE001
            if attempt == 3:
                raise
            print(f"[quote-retry] {redact(str(exc))[:200]}", flush=True)
            time.sleep(2 * attempt)
    raise RuntimeError("unreachable")


def submit_chunk(client, chunk: dict) -> dict:
    return client.batch.submit_job(
        dataset=chunk["dataset"],
        symbols=chunk["symbols"],
        schema=chunk["schema"],
        start=chunk["start"],
        end=chunk["end"],
        stype_in="parent",
        stype_out="instrument_id",
        encoding="dbn",
        compression="zstd",
        split_duration="none",
        delivery="download",
    )


def poll_job(client, job_id: str, states: list) -> dict:
    t0 = time.monotonic()
    hist: list = []
    while time.monotonic() - t0 < JOB_TIMEOUT_S:
        det = client.batch.get_job_details(job_id=job_id)
        state = det.get("state")
        if not hist or hist[-1][0] != state:
            hist.append((state, now_utc()))
        if state in states:
            return {"state": state, "details": det, "history": hist}
        time.sleep(POLL_S)
    return {"state": "TIMEOUT", "details": None, "history": hist}


def download_files(client, chunk: dict) -> None:
    job_id = chunk["job_id"]
    files = client.batch.list_files(job_id=job_id)
    chunk["vendor_list_files"] = [{k: f.get(k) for k in f} for f in files]
    chunk["download_base_url"] = (
        "https://hist.databento.com/v0/batch/download/"
        f"{job_id}/<filename>")
    line_dir = DBN_DIR / chunk["line_id"]
    line_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir = RAW / "scratch" / "incoming"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    out_files = []
    for f in files:
        fname = f.get("filename") or f.get("name")
        dest = line_dir / f"{chunk['chunk_key']}__{fname}"
        client.batch.download(job_id=job_id, output_dir=tmp_dir,
                              filename_to_download=fname)
        src = tmp_dir / job_id / fname
        if not src.exists():
            raise FileNotFoundError(f"download reported but missing: {src}")
        os.replace(src, dest)
        out_files.append({
            "vendor_filename": fname,
            "local_path": str(dest),
            "bytes": dest.stat().st_size,
            "sha256": sha256_of(dest),
            "accessed_utc": now_utc(),
        })
    chunk["files"] = out_files
    chunk["state"] = "DOWNLOADED"
    chunk["downloaded_utc"] = now_utc()


def _job_params_match(job: dict, chunk: dict) -> bool:
    def as_date(v):
        return None if v is None else str(v)[:10]
    syms = set(str(job.get("symbols", "")).split(","))
    return (job.get("dataset") == chunk["dataset"]
            and job.get("schema") == chunk["schema"]
            and syms == set(chunk["symbols"])
            and as_date(job.get("start")) == chunk["start"]
            and as_date(job.get("end")) == chunk["end"])


def find_existing_job(client, led: dict, chunk: dict) -> str | None:
    """Double-billing guard (predecessor law): reuse an existing vendor job
    with the EXACT same params instead of ever submitting a second one."""
    try:
        jobs = client.batch.list_jobs(
            states=["queued", "processing", "done", "expired"],
            since=(dt.datetime.now(dt.timezone.utc)
                   - dt.timedelta(days=2)).strftime("%Y-%m-%d"))
    except Exception as exc:  # noqa: BLE001
        print(f"[dedupe] list_jobs failed (proceeding to submit): "
              f"{redact(str(exc))[:150]}", flush=True)
        return None
    known = {c.get("job_id") for c in led["chunks"].values()
             if c.get("job_id")}
    for job in jobs:
        jid = job.get("id") or job.get("job_id")
        if jid and jid not in known and _job_params_match(job, chunk):
            return jid
    return None


# ---------------------------------------------------------------- disk gate
def disk_gate(chunk: dict) -> tuple[bool, str]:
    """Billable-size based projection (predecessor measured ohlcv ratios:
    raw zst ~= 0.22x billable, parquet ~= 0.20x; scratch decompressed ~=1x;
    iCloud mirror copy ~= 0.42x billable -> conservative 2.0x total)."""
    free = free_gb()
    chunk_bill = chunk["quote"]["billable_size"] / 1e9
    need = chunk_bill * 2.0
    ok = (free - need) >= 1.0
    return ok, (f"free={free:.2f}GB need={need:.2f}GB "
                f"(projection 2.0x billable, conservative)")


def with_retries(fn, *args, what: str = "call", attempts: int = 4,
                 backoff_s: float = 10.0, **kwargs):
    last = None
    for attempt in range(1, attempts + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001
            last = exc
            print(f"[retry] {what} attempt {attempt}: "
                  f"{redact(str(exc))[:200]}", flush=True)
            if attempt < attempts:
                time.sleep(backoff_s * attempt)
    raise last


# ------------------------------------------------------------------- engine
def process_one(client, led: dict, chunk: dict, manifest_blob: dict) -> str:
    key = chunk["chunk_key"]
    state = chunk.get("state", "PLANNED")

    if state == "MIRRORED":
        return "ALREADY_DONE"

    pd_usd, _ = parent_delivered_usd()

    if state in {"PLANNED", "QUOTED"}:
        q = quote_chunk(client, chunk)   # FRESH quote immediately pre-submit
        chunk["quote"] = q
        add_committed = sum(c["quote"]["get_cost"]
                            for c in led["chunks"].values()
                            if c.get("state") in COMMITTED_STATES
                            and c.get("quote", {}).get("get_cost"))
        projected_additional = add_committed + q["get_cost"]
        projected_cumulative = pd_usd + projected_additional
        chunk["budget_before_submit"] = {
            "parent_delivered_usd": round(pd_usd, 6),
            "additional_committed_usd": round(add_committed, 6),
            "chunk_cost_usd": q["get_cost"],
            "projected_additional_usd": round(projected_additional, 6),
            "projected_cumulative_usd": round(projected_cumulative, 6)}
        if (projected_additional > ADDITIONAL_CAP_USD + EPS
                or projected_cumulative > CUMULATIVE_CAP_USD + EPS):
            chunk["state"] = "QUOTED"
            save_ledger(led)
            msg = (f"projected additional ${projected_additional:.4f} > cap "
                   f"${ADDITIONAL_CAP_USD} (or cumulative "
                   f"${projected_cumulative:.4f} > ${CUMULATIVE_CAP_USD})")
            write_stop(led, "BUDGET_CEILING_REACHED", msg)
            return "STOP_BUDGET"
        ok, info = disk_gate(chunk)
        chunk["disk_gate"] = info
        if not ok:
            chunk["state"] = "QUOTED"
            save_ledger(led)
            write_stop(led, "WAIT_STORAGE", info)
            return "STOP_DISK"
        chunk["state"] = "QUOTED"
        save_ledger(led)

    if chunk.get("state") == "QUOTED":
        existing = find_existing_job(client, led, chunk)
        if existing:
            chunk["job_id"] = existing
            chunk["state"] = "SUBMITTED"
            chunk["submitted_utc"] = now_utc()
            chunk["reused_existing_job"] = True
            save_ledger(led)
        else:
            resp = submit_chunk(client, chunk)
            chunk["job_id"] = resp.get("id") or resp.get("job_id")
            chunk["submit_response_redacted"] = redact(json.dumps(
                {k: v for k, v in resp.items()
                 if k not in ("user",)}, default=str))[:1500]
            chunk["state"] = "SUBMITTED"
            chunk["submitted_utc"] = now_utc()
            save_ledger(led)  # SUBMITTED-first: job id on disk before waiting
        if not chunk["job_id"]:
            write_stop(led, "BATCH_SUBMIT_FAILED",
                       f"no job id: {chunk.get('submit_response_redacted')}")
            return "STOP_SUBMIT"

    if chunk.get("state") == "SUBMITTED":
        res = with_retries(poll_job, client, chunk["job_id"], ["done"],
                           what=f"poll {key}")
        chunk["job_state_history"] = res["history"]
        if res["state"] != "done":
            det = res.get("details") or {}
            chunk["state"] = ("JOB_EXPIRED" if res["state"] == "expired"
                              else "SUBMITTED")
            save_ledger(led)
            write_stop(led, "JOB_NOT_DONE",
                       f"state={res['state']} "
                       f"error={redact(str(det.get('error')))[:300]}")
            return "STOP_JOB"
        with_retries(download_files, client, chunk, what=f"download {key}")
        save_ledger(led)

    if chunk.get("state") == "DOWNLOADED":
        qa_res = qa_batch.qa_chunk(chunk)
        report_path = qa_batch.QA_DIR / f"{key}.qa.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(qa_res, indent=1, default=str))
        chunk["qa"] = {"verdict": qa_res["verdict"],
                       "fail_reasons": qa_res["fail_reasons"],
                       "records_actual": qa_res.get("records_actual"),
                       "records_quoted": qa_res.get("records_quoted"),
                       "records_drift_pct": qa_res.get("records_drift_pct"),
                       "parquet_path": (qa_res.get("parquet") or {}).get("path"),
                       "parquet_bytes": (qa_res.get("parquet") or {}).get("bytes"),
                       "report_path": str(report_path)}
        chunk["state"] = "QA_PASS" if qa_res["verdict"] == "PASS" else "QA_FAIL"
        save_ledger(led)
        if qa_res["verdict"] != "PASS":
            write_stop(led, "QA_FAIL", f"{key}: {qa_res['fail_reasons']}")
            return "STOP_QA"

    if chunk.get("state") == "QA_PASS":
        m = mirror_batch.mirror_chunk(chunk, manifest_blob=manifest_blob)
        chunk["mirror"] = m
        if m["state"].startswith("COPY_FAILED"):
            chunk["state"] = "QA_PASS"
            save_ledger(led)
            write_stop(led, "MIRROR_FAILED", f"{key}: {m}")
            return "STOP_MIRROR"
        chunk["state"] = "MIRRORED"
        save_ledger(led)
    return "ADVANCED"


# --------------------------------------------------------------- quote-only
def quote_only(client) -> int:
    pd_usd, pinfo = parent_delivered_usd()
    print(f"parent delivered: ${pd_usd:.6f}")
    print(f"existing FX starts: {pinfo['fx_existing_starts']}")
    out = {"generated_utc": now_utc(),
           "parent_delivered_usd": round(pd_usd, 6),
           "additional_cap_usd": ADDITIONAL_CAP_USD,
           "cumulative_cap_usd": CUMULATIVE_CAP_USD,
           "candidates": {}}
    chosen = None
    for start in (TARGET_START, FALLBACK_START):
        plan = build_plan(start)
        quotes = []
        total = 0.0
        for c in plan:
            q = quote_chunk(client, c)
            total += q["get_cost"]
            quotes.append({**c, "quote": q})
            print(f"  {c['chunk_key']}: ${q['get_cost']:.6f} "
                  f"records={q['records']} size={q['billable_size']}")
        cum = pd_usd + total
        fits = total <= ADDITIONAL_CAP_USD + EPS and cum <= CUMULATIVE_CAP_USD + EPS
        print(f"start {start}: total ${total:.6f} additional, "
              f"cumulative ${cum:.6f} -> {'FITS' if fits else 'EXCEEDS CAP'}")
        out["candidates"][start] = {
            "total_get_cost_usd": round(total, 6),
            "cumulative_projected_usd": round(cum, 6),
            "fits_budget": fits, "chunks": quotes}
        if fits and chosen is None:
            chosen = start
    out["chosen_start"] = chosen
    QUOTES_FILE.write_text(json.dumps(out, indent=1, default=str))
    print(f"chosen_start: {chosen} (evidence: {QUOTES_FILE.name})")
    return 0 if chosen else 1


# -------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quote-only", action="store_true")
    ap.add_argument("--start", default=TARGET_START,
                    help="common start for all four roots "
                         f"(default {TARGET_START}; fallback {FALLBACK_START})")
    args = ap.parse_args()

    client = get_client()

    if args.quote_only:
        return quote_only(client)

    plan = build_plan(args.start)
    led = load_ledger(plan, args.start)

    # machine-wide heavy lock for the paid phase
    sys.path.insert(0, "/Users/hoangminhlong/my-quantitative/research")
    from governance import heavy_lock
    handle = heavy_lock.acquire(
        cycle_id="FUTURES-DEEPRESEARCH-V2-20261003",
        role="FX-BACKFILL",
        worktree="/Users/hoangminhlong/my-quantitative/.worktrees/"
                 "futures-behavior/prep",
        command=["backfill_pipeline.py", f"--start={args.start}"],
        expected_artifacts=[str(LEDGER)])
    print(f"heavy lock acquired: {handle}", flush=True)

    manifest_blob = {"backfill_pipeline": "backfill_20261003/backfill_pipeline.py",
                     "lane": "FX-BACKFILL",
                     "task_id": "FUTURES-DEEPRESEARCH-V2-20261003",
                     "start": args.start, "end": BUTT_END}
    stop = None
    try:
        for plan_chunk in sorted(plan, key=lambda c: (c["order"],
                                                      c["chunk_key"])):
            chunk = led["chunks"][plan_chunk["chunk_key"]]
            try:
                r = process_one(client, led, chunk, manifest_blob)
            except Exception as exc:  # noqa: BLE001
                write_stop(led, "PIPELINE_ERROR",
                           f"{chunk['chunk_key']}: {redact(str(exc))[:300]} "
                           f"tb={traceback.format_exc()[-600:]}")
                save_ledger(led)
                print(f"STOPPED: PIPELINE_ERROR {redact(str(exc))[:200]}")
                return 10
            print(f"{chunk['chunk_key']}: {r}", flush=True)
            if r.startswith("STOP"):
                stop = r
                break
    finally:
        try:
            handle.release()
            print("heavy lock released", flush=True)
        except Exception as exc:  # noqa: BLE001
            print(f"lock release note: {redact(str(exc))[:150]}", flush=True)

    save_ledger(led)
    print(json.dumps(led.get("running_totals", {}), indent=1))
    if stop:
        print(f"STOPPED: {stop}")
        return 10
    print("ALL BACKFILL CHUNKS PROCESSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
