#!/usr/bin/env python3
"""s_a3_verify.py - deterministic evidence-chain verifier for cycle
DATA-EDGE-UNLOCK-V1 / task deu-s-a3 (Lane S, SEC FTD + N-PORT PIT audit).

No network. Reads only the local raw archive + the sha pins shipped beside
this script (probes/). Exits 0 iff every enabled check passes.

Usage:
  python3 s_a3_verify.py \
    --ftd-dir  /path/to/raw/sec_ftd_archive \
    --nport-dir /path/to/raw/sec_nport          (optional; enables N3 checks)
  (paths default to the frozen DATA-FRONTIER-V1 raw roots)

Checks (all deterministic, byte-level):
  A  re-hash 13 pinned sample zips (2009/2016/2020/2026 span + both _0
     reposts + one quarterly) against probes/s_ftd_manifest_sample_pin.json
     (provenance: branch orca/free-data-frontier-v1-integration, manifest
     blob 19579a781cc338c7677c390e2c5e4e9774ddc391).
  B  per-file parser guards on 7 files: exactly 2 trailer rows, trailer
     record count == data rows, trailer quantity == raw sum == deduped
     (settlement,cusip) sum, zero duplicate keys, 6-column schema,
     settlement dates strictly inside the filename half-month.
  C  zero-overlap settlement partition across 4 half-month pairs + 3
     neighbours of each _0 repost position.
  E  the two base half-month names (cnsfails201910a.zip, cnsfails202308b.zip)
     are ABSENT and the _0 objects are PRESENT.
  D  dead-name canaries (F6): FRC 33616C100 in 202305a and as FRCB in 202408a;
     LEHMQ 524908100 last row 20100630 in 201006b; TWTR 90184L102 in 202211a;
     SIVB 78486Q101 final row 20230310; TWX 887317303 in 201806b; the two
     never-existed CUSIP controls absent from all scanned files.
  N3 2026q2_nport.zip sha matches pin; SUBMISSION.tsv has 14,416 rows;
     SUB_TYPE = 14064 NPORT-P / 352 NPORT-P/A; supersession: 92 multi-accession
     (series-or-name, REPORT_DATE) keys, 64 unique by max FILING_DATE, 28
     day-ties all same-agent and sequence-resolvable, 0 cross-agent ties.
"""
import argparse, collections, hashlib, json, os, re, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_FTD = "/Users/hoangminhlong/.my-quantitative-data/free-data-frontier-v1/raw/sec_ftd_archive"
DEFAULT_NPORT = "/Users/hoangminhlong/.my-quantitative-data/free-data-frontier-v1/raw/sec_nport"

HEADER = "SETTLEMENT DATE|CUSIP|SYMBOL|QUANTITY (FAILS)|DESCRIPTION|PRICE"

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()

def read_file(path):
    """-> (header_seen, rows, trailer_count_lines, trailer_qty_lines)."""
    z = zipfile.ZipFile(path)
    members = z.namelist()
    if len(members) != 1:
        raise AssertionError(f"{path}: expected 1 member, got {members}")
    hdr_seen = False
    rows, tc, tq = [], [], []
    for line in z.read(members[0]).decode("latin-1").splitlines():
        if not line.strip():
            continue
        low = line.lower()
        if low.startswith("trailer record count"):
            tc.append(int(line.rsplit(" ", 1)[1]))
        elif low.startswith("trailer total quantity"):
            tq.append(int(line.rsplit(" ", 1)[1]))
        elif line.upper().startswith("SETTLEMENT DATE"):
            hdr_seen = True
            assert line == HEADER, f"schema drift: {line!r}"
        else:
            p = line.split("|")
            assert len(p) == 6, f"column drift: {line!r}"
            rows.append(p)
    return hdr_seen, rows, tc, tq

def half_bounds(fname):
    m = re.match(r"cnsfails(\d{6})([ab])(_0)?\.zip$", fname)
    ym, half = int(m.group(1)), m.group(2)
    y, mo = ym // 100, ym % 100
    if mo == 12:
        ny, nm = y + 1, 1
    else:
        ny, nm = y, mo + 1
    nxt = f"{ny:04d}{nm:02d}01"
    if half == "a":
        return int(f"{ym}01"), int(f"{ym}14")
    return int(f"{ym}15"), int(nxt) - 1

FAILS = []
def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail else ""))
    if not cond:
        FAILS.append(name)

def run_ftd(ftd):
    pin = json.load(open(os.path.join(HERE, "probes", "s_ftd_manifest_sample_pin.json")))
    # A: re-hash pin
    for fn, meta in sorted(pin["sample_zips"].items()):
        p = os.path.join(ftd, fn)
        check(f"A.hash.{fn}", os.path.exists(p) and sha256(p) == meta["sha256"])
    # B: parser guards
    for fn in ["cnsfails200907a.zip", "cnsfails201606a.zip", "cnsfails202004a.zip",
               "cnsfails202608a.zip", "cnsfails202308b_0.zip", "cnsfails201910a_0.zip"]:
        hdr, rows, tc, tq = read_file(os.path.join(ftd, fn))
        sd = [int(r[0]) for r in rows]
        q = [int(r[3]) for r in rows]
        keys = collections.Counter((r[0], r[1]) for r in rows)
        lo, hi = half_bounds(fn)
        check(f"B.schema.{fn}", hdr and len(rows[0]) == 6)
        check(f"B.trailer2.{fn}", len(tc) == 1 and len(tq) == 1)
        check(f"B.reccnt.{fn}", sum(tc) == len(rows), f"{sum(tc)} vs {len(rows)}")
        qmap = {}
        for r in rows:
            qmap[(r[0], r[1])] = int(r[3])
        check(f"B.qtyrecon.{fn}", sum(tq) == sum(q) == sum(qmap.values()))
        check(f"B.nodup.{fn}", max(keys.values()) == 1)
        check(f"B.halfmonth.{fn}", all(lo <= d <= hi for d in sd), f"{min(sd)}..{max(sd)}")
    # C: partition
    def sdates(fn):
        _, rows, _, _ = read_file(os.path.join(ftd, fn))
        return {r[0] for r in rows}
    for a, b in [("cnsfails200907a.zip", "cnsfails200907b.zip"),
                 ("cnsfails201606a.zip", "cnsfails201606b.zip"),
                 ("cnsfails202004a.zip", "cnsfails202004b.zip"),
                 ("cnsfails202011a.zip", "cnsfails202011b.zip")]:
        check(f"C.partition.{a}.{b}", not (sdates(a) & sdates(b)))
    for t, ns in [("cnsfails202308b_0.zip", ["cnsfails202308a.zip", "cnsfails202309a.zip", "cnsfails202309b.zip"]),
                  ("cnsfails201910a_0.zip", ["cnsfails201909b.zip", "cnsfails201910b.zip", "cnsfails201911a.zip"])]:
        ts = sdates(t)
        for n in ns:
            check(f"C.nooverlap.{t}.{n}", not (ts & sdates(n)))
    # E: repost positions
    check("E.absent.cnsfails201910a.zip", not os.path.exists(os.path.join(ftd, "cnsfails201910a.zip")))
    check("E.absent.cnsfails202308b.zip", not os.path.exists(os.path.join(ftd, "cnsfails202308b.zip")))
    check("E.present.cnsfails201910a_0.zip", os.path.exists(os.path.join(ftd, "cnsfails201910a_0.zip")))
    check("E.present.cnsfails202308b_0.zip", os.path.exists(os.path.join(ftd, "cnsfails202308b_0.zip")))
    # D: dead-name canaries
    def rows_with(fn, col, val):
        _, rows, _, _ = read_file(os.path.join(ftd, fn))
        i = {"cusip": 1, "sym": 2}[col]
        return [r for r in rows if r[i] == val]
    def has_row(fn, cusip, sym=None, settle=None, qty=None, price=None):
        for r in rows_with(fn, "cusip", cusip):
            if sym is not None and r[2] != sym: continue
            if settle is not None and r[0] != str(settle): continue
            if qty is not None and int(r[3]) != qty: continue
            if price is not None and r[5] != price: continue
            return True
        return False
    check("D.FRC.deathrow", has_row("cnsfails202305a.zip", "33616C100", "FRC", 20230503, 21285624, "3.51"))
    check("D.FRCB.symbol_mutated_2024", has_row("cnsfails202408a.zip", "33616C100", "FRCB", 20240801, 30, "0.02"))
    check("D.FRCB.residual_2026", any(rows_with("cnsfails202608a.zip", "cusip", "33616C100")))
    check("D.LEHMQ.lastrow", has_row("cnsfails201006b.zip", "524908100", "LEHMQ", 20100630, 964, "0.08"))
    check("D.TWTR.post_death", has_row("cnsfails202211a.zip", "90184L102", "TWTR", 20221101, 13091, "53.70"))
    check("D.SIVB.deathrow", has_row("cnsfails202303a.zip", "78486Q101", "SIVB", 20230310, 149, "106.04"))
    check("D.TWX.post_death", has_row("cnsfails201806b.zip", "887317303", "TWX", 20180625, 25090, "98.77"))
    ctrls = {"000000000", "999999999"}
    syms = {"NOTREAL", "FAKESYM"}
    for fn in ["cnsfails202408a.zip", "cnsfails202608a.zip", "cnsfails201001a.zip"]:
        _, rows, _, _ = read_file(os.path.join(ftd, fn))
        bad = [r for r in rows if r[1] in ctrls or r[2] in syms]
        check(f"D.controls.clean.{fn}", not bad)

def run_nport(nd):
    p = os.path.join(nd, "2026q2_nport.zip")
    check("N3.zipsha", sha256(p) == "077cc836a978a593b29012219395fbe9c303d5e930f5be3b5f4353c3b02296fc")
    z = zipfile.ZipFile(p)
    def tsv(m):
        with z.open(m) as f:
            lines = f.read().decode("utf-8").splitlines()
        hdr = lines[0].split("\t")
        return [dict(zip(hdr, l.split("\t"))) for l in lines[1:]]
    sub, fri = tsv("SUBMISSION.tsv"), tsv("FUND_REPORTED_INFO.tsv")
    st = collections.Counter(r["SUB_TYPE"] for r in sub)
    check("N3.counts", len(sub) == 14416 and st["NPORT-P"] == 14064 and st["NPORT-P/A"] == 352, str(dict(st)))
    acc = {r["ACCESSION_NUMBER"]: r for r in fri}
    by = collections.defaultdict(list)
    for r in sub:
        k = (acc[r["ACCESSION_NUMBER"]]["SERIES_ID"].strip() or "NAME:" + acc[r["ACCESSION_NUMBER"]]["SERIES_NAME"].strip(), r["REPORT_DATE"])
        by[k].append(r)
    multi = {k: v for k, v in by.items() if len(v) > 1}
    ties = 0; same_agent = 0; resolvable = 0; cross = 0
    for v in multi.values():
        mx = max(x["FILING_DATE"] for x in v)
        w = [x for x in v if x["FILING_DATE"] == mx]
        if len(w) == 1: continue
        ties += 1
        ag = {x["ACCESSION_NUMBER"].split("-")[0] for x in w}
        if len(ag) == 1:
            same_agent += 1
            if len({x["ACCESSION_NUMBER"].split("-")[2] for x in w}) == len(w): resolvable += 1
        else: cross += 1
    check("N3.supersession", len(multi) == 92 and ties == 28 and same_agent == 28
          and resolvable == 28 and cross == 0,
          f"multi={len(multi)} ties={ties} same_agent={same_agent} seq_ok={resolvable} cross={cross}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ftd-dir", default=DEFAULT_FTD)
    ap.add_argument("--nport-dir", default=DEFAULT_NPORT)
    ap.add_argument("--skip-nport", action="store_true")
    args = ap.parse_args()
    run_ftd(args.ftd_dir)
    if not args.skip_nport:
        run_nport(args.nport_dir)
    print(f"\n{'ALL CHECKS PASS' if not FAILS else 'FAILURES: ' + ', '.join(FAILS)}")
    sys.exit(1 if FAILS else 0)

if __name__ == "__main__":
    main()
