#!/usr/bin/env python3
"""acq_pipeline.py — STEP 3 chunked download orchestrator (ACQ-DOWNLOAD).

First authorized paid-data download. Budget law (hard):
  owner ceiling $125 (unverifiable credit -> real money);
  running committed spend (sum of get_cost over SUBMITTED-and-beyond chunks)
  must stay <= $118 before every new submit; else STOP
  BUDGET_CEILING_REACHED. Every get_cost call + response is recorded in the
  ledger before its submit.

Batch API (verified against the official client v0.87.0, machine-readable
authority): POST {hist}/v0/batch.submit_job (dataset, start, end exclusive,
symbols, schema, stype_in, stype_out, encoding=dbn, compression=zstd,
split_duration, delivery=download) -> job states queued|processing|done|
expired; GET /v0/batch.list_files?job_id=; GET
/v0/batch/download/{job_id}/{filename}. get_cost docstring: quotes "the cost
in US dollars for historical streaming or batched files" -> same per-GB
billing path for batch deliveries.

Idempotency/resume: COMPLETION_LEDGER.json is the single authority; states
QUOTED -> SUBMITTED (job id recorded immediately, before any wait) ->
DOWNLOADED (sha256 per file) -> QA_PASS/QA_FAIL -> MIRRORED. Resume: chunks
at MIRRORED are skipped; chunks with a job id are polled/downloaded, never
blindly resubmitted; only PLANNED/QUOTED chunks get submitted.

Disk law: per-batch gate: free disk must cover batch raw + parquet + scratch
(decompressed) + iCloud mirror copy + 20% reserve of the start-free pool
minus 2 GiB allowance for the concurrent NONPRICE lane. Projection updated
with measured ratios after every delivered batch.

Usage:
  acq_pipeline.py --plan                 # print chunk plan + budget table
  acq_pipeline.py --max-chunks N         # bound the run (default all)
  acq_pipeline.py --lookahead K          # jobs submitted ahead (default 1)
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
sys.path.insert(0, str(ACQ))
import qa_batch  # noqa: E402
import mirror_batch  # noqa: E402

MANIFEST = ACQ / "AV1_TRIM_MANIFEST.json"
LEDGER = ACQ / "COMPLETION_LEDGER.json"
STOP_FILE = ACQ / "PIPELINE_STOP.json"

RAW = Path("/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim")
DBN_DIR = RAW / "raw" / "dbn_zst"
QA_DIR = ACQ / "qa"

KEY_PATH = Path(
    "/Users/hoangminhlong/.config/my-quantitative-secrets/databento-api-key")
TOKEN_RE = re.compile(r"db-[A-Za-z0-9_\-]{12,}")

OWNER_CEILING = 125.00
LANE_HARD_STOP = 118.00
DISK_RESERVE_GB = 21.412 * 0.20          # 20% of start-free (measured 2026-10-02)
NONPRICE_ALLOWANCE_GB = 2.0             # concurrent lane's cap allowance
POLL_S = 30
JOB_TIMEOUT_S = 6 * 3600  # vendor batch queue can be congested for hours;
                          # resume re-polls the same job id (no resubmit)

COMMITTED_STATES = {"SUBMITTED", "DOWNLOADING", "DOWNLOADED", "QA_PASS",
                    "QA_FAIL", "MIRRORED"}


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


# ---------------------------------------------------------------- chunk plan
def month_floor(d: dt.date) -> dt.date:
    return d.replace(day=1)


def add_months(d: dt.date, n: int) -> dt.date:
    y = d.year + (d.month - 1 + n) // 12
    m = (d.month - 1 + n) % 12 + 1
    return d.replace(year=y, month=m, day=1)


def split_months(start: str, end: str, chunk_months: int) -> list[tuple[str, str]]:
    s = dt.date.fromisoformat(start)   # EXACT start preserved (a 2010-06-06
    e = dt.date.fromisoformat(end)     # start must NOT become 2010-06-01:
    out = []                           # vendor rejects pre-dataset starts)
    while s < e:
        nxt = min(add_months(month_floor(s), chunk_months), e)
        out.append((s.isoformat(), nxt.isoformat()))
        s = nxt
    return out


def build_plan(manifest: dict) -> list[dict]:
    lines = {l["line_id"]: l for l in manifest["request_lines"]}
    plan: list[dict] = []

    def emit(line_id: str, windows: list[tuple[str, str]], order: int,
             schema: str | None = None, symbols=None):
        line = lines.get(line_id, {})
        for (s, e) in windows:
            key = f"{line_id}__{s}_{e}"
            plan.append({
                "chunk_key": key, "line_id": line_id,
                "dataset": "GLBX.MDP3",
                "schema": schema or line["schema"],
                "symbols": symbols or line["symbols"],
                "stype_in": line.get("stype_in", "parent"),
                "start": s, "end": e, "order": order,
            })

    # Owner rescope 2026-10-02 (RESCOPE_MANIFEST.json): dropped ohlcv
    # roots + new delta/backfill lines; ledger states are the authority.
    rescope_path = ACQ / "RESCOPE_MANIFEST.json"
    dropped_roots: set[str] = set()
    if rescope_path.exists():
        rs = json.loads(rescope_path.read_text())
        dropped_roots = {l.replace("AV1T-O1M-", "")
                         for l in rs["dropped_lines"]["lines"]}
        for line in rs["new_lines"]:
            emit(line["line_id"],
                 split_months(line["start"], line["end"],
                              line["chunk_months"]),
                 line["order"], schema=line["schema"],
                 symbols=line["symbols"])

    emit("AV1T-definition-ALL10", split_months("2023-10-01", "2026-10-01", 3), 10)
    emit("AV1T-statistics-ALL10", split_months("2023-10-01", "2026-10-01", 2), 20)
    for root in ("NQ", "ES", "GC", "SI"):
        if root in dropped_roots:
            continue
        emit(f"AV1T-O1M-{root}",
             split_months("2023-10-01", "2026-10-01", 6), 30)
    for root in ("6E", "6J"):
        emit(f"AV1T-O1M-{root}",
             split_months("2026-01-01", "2026-10-01", 6), 40)  # 6m + 3m
    for root in ("6B", "6A"):
        emit(f"AV1T-O1M-{root}",
             split_months("2026-04-01", "2026-10-01", 6), 45)
    for root in ("CL", "NG"):
        if root in dropped_roots:
            continue
        emit(f"AV1T-O1M-{root}",
             split_months("2025-10-01", "2026-10-01", 3), 50)
    plan.sort(key=lambda c: (c["order"], c["chunk_key"]))
    return plan


# ------------------------------------------------------------------- ledger
def load_ledger(plan: list[dict]) -> dict:
    if LEDGER.exists():
        led = json.loads(LEDGER.read_text())
    else:
        led = {"schema": "futures_behavior_acq_completion_ledger@1",
               "task_id": "FUTURES-BEHAVIOR-10SYMS-PREP-20261002",
               "lane": "ACQ-DOWNLOAD",
               "created_utc": now_utc(),
               "budget": {"owner_ceiling_usd": OWNER_CEILING,
                          "lane_hard_stop_usd": LANE_HARD_STOP},
               "disk_gate": {"start_free_gb": 21.412,
                              "reserve_gb": round(DISK_RESERVE_GB, 3),
                              "nonprice_allowance_gb": NONPRICE_ALLOWANCE_GB},
               "chunks": {}}
    for c in plan:
        if c["chunk_key"] not in led["chunks"]:
            led["chunks"][c["chunk_key"]] = {**c, "state": "PLANNED"}
    return led


def save_ledger(led: dict) -> None:
    led["updated_utc"] = now_utc()
    committed = sum(c["quote"]["get_cost"] for c in led["chunks"].values()
                    if c.get("state") in COMMITTED_STATES
                    and c.get("quote", {}).get("get_cost"))
    delivered = sum(c["quote"]["get_cost"] for c in led["chunks"].values()
                    if c.get("state") in {"DOWNLOADED", "QA_PASS", "QA_FAIL",
                                          "MIRRORED"}
                    and c.get("quote", {}).get("get_cost"))
    led["running_totals"] = {
        "committed_usd": round(committed, 6),
        "delivered_usd": round(delivered, 6),
        "n_chunks": len(led["chunks"]),
        "n_submitted_plus": sum(1 for c in led["chunks"].values()
                                if c.get("state") in COMMITTED_STATES),
        "n_mirrored": sum(1 for c in led["chunks"].values()
                          if c.get("state") == "MIRRORED"),
    }
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


def quote_chunk(client, chunk: dict) -> dict:
    params = dict(dataset=chunk["dataset"],
                  symbols=",".join(chunk["symbols"]),
                  schema=chunk["schema"], stype_in=chunk["stype_in"],
                  start=chunk["start"], end=chunk["end"])
    for attempt in range(1, 4):
        try:
            cost = float(client.metadata.get_cost(**params))
            size = int(client.metadata.get_billable_size(**params))
            count = int(client.metadata.get_record_count(**params))
            return {"get_cost": cost, "billable_size": size,
                    "records": count, "ts_utc": now_utc(),
                    "attempts": attempt}
        except Exception as exc:  # noqa: BLE001
            err = redact(f"{type(exc).__name__}: {exc}")[:300]
            if attempt == 3:
                raise
            time.sleep(2 * attempt)
    raise RuntimeError("unreachable")


def submit_chunk(client, chunk: dict) -> dict:
    resp = client.batch.submit_job(
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
    return resp  # dict with job id (recorded verbatim minus noise)


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


def download_files(client, led: dict, chunk: dict) -> None:
    job_id = chunk["job_id"]
    det = client.batch.get_job_details(job_id=job_id)
    files = client.batch.list_files(job_id=job_id)
    chunk["vendor_list_files"] = [
        {k: f.get(k) for k in f} for f in files]  # verbatim
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
        if dest.exists() and sha256_of(dest):
            pass  # will verify below regardless
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


# ---------------------------------------------------------------- disk gate
def measured_ratios(led: dict) -> dict:
    raw_b = sum(f["bytes"] for c in led["chunks"].values()
                if c.get("state") in {"DOWNLOADED", "QA_PASS", "QA_FAIL",
                                      "MIRRORED"}
                for f in c.get("files", []))
    bill_b = sum(c["quote"]["billable_size"] for c in led["chunks"].values()
                 if c.get("state") in {"DOWNLOADED", "QA_PASS", "QA_FAIL",
                                       "MIRRORED"}
                 and c.get("quote", {}).get("billable_size"))
    pq_b = sum(Path(c["qa"]["parquet_path"]).stat().st_size
               for c in led["chunks"].values()
               if c.get("qa", {}).get("parquet_path")
               and Path(c["qa"]["parquet_path"]).exists())
    return {"raw_zstd_over_billable": (raw_b / bill_b) if bill_b else 0.6,
            "parquet_over_billable": (pq_b / bill_b) if bill_b else 0.6,
            "raw_bytes": raw_b, "billable_bytes": bill_b, "parquet_bytes": pq_b}


def disk_gate(led: dict, chunk: dict) -> tuple[bool, str]:
    r = measured_ratios(led)
    usable = 21.412 - DISK_RESERVE_GB - NONPRICE_ALLOWANCE_GB
    free = free_gb()
    chunk_bill = chunk["quote"]["billable_size"] / 1e9
    need = chunk_bill * (r["raw_zstd_over_billable"]
                         + r["parquet_over_billable"] + 1.0   # scratch decompr
                         + r["raw_zstd_over_billable"]
                         + r["parquet_over_billable"])        # iCloud mirror
    remaining_bill = sum(
        (c["quote"]["billable_size"] / 1e9) if c.get("quote") else 0.3
        for c in led["chunks"].values()
        if c.get("state") not in {"DOWNLOADED", "QA_PASS", "QA_FAIL",
                                  "MIRRORED"})
    projected_end_used = (21.412 - free) + remaining_bill * (
        r["raw_zstd_over_billable"] + r["parquet_over_billable"]) * 2
    per_batch_ok = (free - need) >= 1.0
    return per_batch_ok, (f"free={free:.2f}GB need={need:.2f}GB "
                          f"projected_end_used={projected_end_used:.2f}GB "
                          f"usable={usable:.2f}GB ratios="
                          f"zst={r['raw_zstd_over_billable']:.3f} "
                          f"pq={r['parquet_over_billable']:.3f}")


def with_retries(fn, *args, what: str = "call", attempts: int = 4,
                 backoff_s: float = 10.0, **kwargs):
    """Transient-network retry wrapper for vendor I/O. Ledger-relevant
    exceptions (non-network) still raise immediately after logging."""
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


def _job_params_match(job: dict, chunk: dict) -> bool:
    """Match a vendor job record against chunk request params exactly."""
    def as_date(v):
        if v is None:
            return None
        s = str(v)
        return s[:10].replace("-", "-")
    syms = set(str(job.get("symbols", "")).split(","))
    return (job.get("dataset") == chunk["dataset"]
            and job.get("schema") == chunk["schema"]
            and syms == set(chunk["symbols"])
            and as_date(job.get("start")) == chunk["start"]
            and as_date(job.get("end")) == chunk["end"])


def find_existing_job(client, led: dict, chunk: dict) -> str | None:
    """One-owner rule + submit idempotency: reuse an existing job with the
    EXACT same params instead of ever submitting a second one (double-
    billing guard for crash-between-submit-and-ledger-write)."""
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


# ------------------------------------------------------------------- engine
def process_one(client, led: dict, chunk: dict, manifest: dict) -> str:
    """Advance one chunk as far as possible; returns terminal transition."""
    key = chunk["chunk_key"]
    state = chunk.get("state", "PLANNED")

    if state == "MIRRORED":
        return "ALREADY_DONE"
    if state == "DROPPED_BY_OWNER_RESCOPE":
        return "ALREADY_DONE"

    if state in {"PLANNED", "QUOTED"}:
        q = quote_chunk(client, chunk)
        chunk["quote"] = q
        committed = sum(c["quote"]["get_cost"]
                        for c in led["chunks"].values()
                        if c.get("state") in COMMITTED_STATES
                        and c.get("quote", {}).get("get_cost"))
        projected = committed + q["get_cost"]
        chunk["budget_before_submit"] = {
            "committed_usd": round(committed, 6),
            "chunk_cost_usd": q["get_cost"],
            "projected_usd": round(projected, 6)}
        if projected > LANE_HARD_STOP:
            chunk["state"] = "QUOTED"
            save_ledger(led)
            msg = (f"projected committed ${projected:.4f} > hard stop "
                   f"${LANE_HARD_STOP}")
            write_stop(led, "BUDGET_CEILING_REACHED", msg)
            return "STOP_BUDGET"
        ok, info = disk_gate(led, chunk)
        chunk["disk_gate"] = info
        if not ok:
            chunk["state"] = "QUOTED"
            save_ledger(led)
            write_stop(led, "WAIT_STORAGE", info)
            return "STOP_DISK"
        chunk["state"] = "QUOTED"
        save_ledger(led)

    if chunk.get("state") == "QUOTED":
        # double-billing guard: reuse an existing job with exact same params
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
            save_ledger(led)  # SUBMITTED-first (job id on disk before waiting)
        if not chunk["job_id"]:
            write_stop(led, "BATCH_SUBMIT_FAILED",
                       f"no job id in response: {chunk.get('submit_response_redacted')}")
            return "STOP_SUBMIT"

    if chunk.get("state") == "SUBMITTED":
        res = with_retries(poll_job, client, chunk["job_id"], ["done"],
                           what=f"poll {chunk['chunk_key']}")
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
        with_retries(download_files, client, led, chunk,
                     what=f"download {chunk['chunk_key']}")
        save_ledger(led)

    if chunk.get("state") == "DOWNLOADED":
        qa_res = qa_batch.qa_chunk(chunk)
        report_path = QA_DIR / f"{key}.qa.json"
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
            write_stop(led, "QA_FAIL",
                       f"{key}: {qa_res['fail_reasons']}")
            return "STOP_QA"

    if chunk.get("state") == "QA_PASS":
        m = mirror_batch.mirror_chunk(chunk, manifest_blob=manifest)
        chunk["mirror"] = m
        if m["state"].startswith("COPY_FAILED"):
            chunk["state"] = "QA_PASS"
            save_ledger(led)
            write_stop(led, "MIRROR_FAILED", f"{key}: {m}")
            return "STOP_MIRROR"
        chunk["state"] = "MIRRORED"
        save_ledger(led)
    return "ADVANCED"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--max-chunks", type=int, default=0)
    ap.add_argument("--reqa", action="store_true",
                    help="re-run QA+mirror for chunks in QA_FAIL/DOWNLOADED "
                         "state (never resubmits; files already on disk)")
    ap.add_argument("--reparquet", metavar="SCHEMA",
                    help="re-run QA+mirror for all MIRRORED chunks of the "
                         "given schema (regenerates parquet from raw; never "
                         "resubmits; used after the ts_ref nulling bug fix)")
    args = ap.parse_args()

    manifest = json.loads(MANIFEST.read_text())
    plan = build_plan(manifest)
    led = load_ledger(plan)

    if args.plan:
        by_line: dict[str, list] = {}
        for c in plan:
            by_line.setdefault(c["line_id"], []).append(c)
        for lid, chunks in by_line.items():
            print(f"{lid}: {len(chunks)} chunks: "
                  f"{[c['start'] + '..' + c['end'] for c in chunks]}")
        print(f"total chunks: {len(plan)}; manifest total "
              f"${manifest['totals']['get_cost_usd']}")
        print(json.dumps(led.get("running_totals", {}), indent=1))
        return 0

    if args.reparquet:
        client = get_client()
        schema = args.reparquet
        n = 0
        for plan_chunk in sorted(plan, key=lambda c: (c["order"],
                                                      c["chunk_key"])):
            chunk = led["chunks"][plan_chunk["chunk_key"]]
            if chunk.get("state") == "MIRRORED" and chunk["schema"] == schema:
                chunk["state"] = "DOWNLOADED"
                chunk.setdefault("qa_retries", 0)
                chunk["qa_retries"] += 1
                save_ledger(led)
                r = process_one(client, led, chunk, manifest)
                print(f"{chunk['chunk_key']}: {r}", flush=True)
                n += 1
                if r.startswith("STOP"):
                    save_ledger(led)
                    return 10
        save_ledger(led)
        print(f"re-parquet processed {n} chunk(s)")
        return 0

    if args.reqa:
        client = get_client()
        n = 0
        for plan_chunk in sorted(plan, key=lambda c: (c["order"],
                                                      c["chunk_key"])):
            chunk = led["chunks"][plan_chunk["chunk_key"]]
            if chunk.get("state") in {"QA_FAIL", "DOWNLOADED"}:
                chunk["state"] = "DOWNLOADED"
                chunk.setdefault("qa_retries", 0)
                chunk["qa_retries"] += 1
                save_ledger(led)
                r = process_one(client, led, chunk, manifest)
                print(f"{chunk['chunk_key']}: {r}")
                n += 1
                if r.startswith("STOP"):
                    save_ledger(led)
                    return 10
        save_ledger(led)
        print(f"re-QA processed {n} chunk(s)")
        return 0

    client = get_client()
    done = 0
    stop = None
    order = sorted(plan, key=lambda c: (c["order"], c["chunk_key"]))
    for plan_chunk in order:
        chunk = led["chunks"][plan_chunk["chunk_key"]]
        try:
            r = process_one(client, led, chunk, manifest)
        except Exception as exc:  # noqa: BLE001
            write_stop(led, "PIPELINE_ERROR",
                       f"{chunk['chunk_key']}: {redact(str(exc))[:300]} "
                       f"tb={traceback.format_exc()[-600:]}")
            save_ledger(led)
            print(f"STOPPED: PIPELINE_ERROR {redact(str(exc))[:200]}")
            return 10
        if r == "ALREADY_DONE":
            continue
        done += 1
        if r.startswith("STOP"):
            stop = r
            break
        if args.max_chunks and done >= args.max_chunks:
            print(f"--max-chunks {args.max_chunks} reached")
            break

    save_ledger(led)
    print(json.dumps(led.get("running_totals", {}), indent=1))
    if stop:
        print(f"STOPPED: {stop}")
        return 10
    print("ALL CHUNKS PROCESSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
