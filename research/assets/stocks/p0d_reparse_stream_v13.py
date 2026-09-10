"""INC-V13-9 recovery: deterministic offline reparse of ALL cached Form-4 XML
bytes (the bytes were always valid; only the field paths were wrong). Rebuilds
form4_stream.jsonl + .defects.jsonl from scratch via the fixed parse contract.
Idempotent: same bytes + same code = same stream (determinism by construction).
"""
import json, glob, os, sys
RT = "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v13/integration"
sys.path.insert(0, RT)              # research.* package root
sys.path.insert(0, f"{RT}/research")  # governance.* (heavy_lock import in ingest module)
W = "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v13/integration"
XML_DIR = f"{W}/.staging_sec_v13/form4_xml"
STREAM = f"{W}/.staging_sec_v13/form4_stream.jsonl"
# import the FIXED parser from the ingest module without running main()
import importlib.util
spec = importlib.util.spec_from_file_location("ing", f"{W}/research/assets/stocks/p0d_bulk_ingest_v13.py")
ing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ing)

docs = sorted(glob.glob(f"{XML_DIR}/CIK*/[0-9]*/*.xml"))
# INC-V13-13: join acceptance/filing_date from the submissions caches (the PIT
# authority) — the previous reparse passed empty strings and silently stripped
# the acceptance stamp from every row.
import glob as _glob
accmeta = {}
for src in ["/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v9/integration/.staging_sec_v9/submissions_dead",
            f"{W}/.staging_sec_v13/submissions_alive"]:
    for sp in _glob.glob(f"{src}/CIK*.json"):
        cik = "CIK" + os.path.basename(sp)[3:13]
        d = json.load(open(sp))
        rec = d.get("filings", {}).get("recent", {})
        forms = rec.get("form", [])
        for i, fm in enumerate(forms):
            if fm == "4":
                accn = rec.get("accessionNumber", [""] * len(forms))[i]
                accmeta[(cik, accn)] = (
                    rec.get("acceptanceDateTime", [""] * len(forms))[i] or "",
                    rec.get("filingDate", [""] * len(forms))[i] or "")
print("acceptance metadata joined:", len(accmeta))
rows_out, defect_out = [], []
for p in docs:
    cik = os.path.basename(os.path.dirname(os.path.dirname(p)))
    acc_nodash = os.path.basename(os.path.dirname(p))
    acc = f"{acc_nodash[:10]}-{acc_nodash[10:12]}-{acc_nodash[12:]}"
    acceptance, filing_date = accmeta.get((cik, acc), ("", ""))
    raw = open(p, "rb").read()
    rows, defects = ing.parse_form4_xml(raw, cik, acc, acceptance, filing_date)
    rows_out += rows
    defect_out += defects
noacc = sum(1 for r in rows_out if not r.get("acceptance"))
print("rows missing acceptance after join:", noacc)
with open(STREAM, "w") as f:
    for r in rows_out:
        f.write(json.dumps(r) + "\n")
with open(f"{XML_DIR}/.defects.jsonl", "w") as f:
    for d in defect_out:
        f.write(json.dumps(d) + "\n")
from collections import Counter
c = Counter(r["direction"] for r in rows_out)
cd = Counter(d["reason"].split(":")[0] for d in defect_out)
print(f"docs reparsed: {len(docs)} | stream rows: {len(rows_out)} {dict(c)} | defects: {len(defect_out)} {dict(cd)}")
