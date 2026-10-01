#!/usr/bin/env python
"""Land FRED serving-lag observation point-2 as a REAL artifact (skeptic
finding 1: the earlier 02:40Z re-pull ran in an ad-hoc shell and was never
landed, so '2 observations' was hard-coded prose). Pulls the four series
now, lands bytes, records endpoint dates, appends to MANIFEST_RAW.json."""
import hashlib, json, subprocess
from datetime import datetime, timezone
from pathlib import Path
WT=Path("/Users/hoangminhlong/my-quantitative/.worktrees/pc12a-7asset-unblock-20261001")
CTL=WT/"research/control/PC12A-7ASSET-DATA-UNBLOCK-2026-10-01"
RAW=Path.home()/".my-quantitative-data/pc12a-7asset-data-unblock-2026-10-01/raw"
now=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
res={"at_utc":now(),"series":{}}
mp=CTL/"MANIFEST_RAW.json"; man=json.loads(mp.read_text())
for sid in ["DEXUSNZ","DEXSZUS","DCOILBRENTEU","DHHNGSP"]:
    cp=subprocess.run(["curl","-sS","--http1.1","--max-time","30","-w","\n%{http_code}",
        f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"],capture_output=True)
    body,_,code=cp.stdout.rpartition(b"\n")
    name=f"fred_{sid}_staleness_p2.csv"
    (RAW/name).write_bytes(body)
    lines=body.decode().strip().splitlines()
    last=lines[-1].split(",")[0] if len(lines)>1 else None
    res["series"][sid]={"http":int(code or 0),"bytes":len(body),"last_observation_date":last}
    man["files"].append({"file":name,"path":str(RAW/name),"url":f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}",
        "retrieved_at_utc":now(),"bytes":len(body),"sha256":hashlib.sha256(body).hexdigest(),
        "http_status":int(code or 0),
        "license_note":"same as session-1 FRED rows","authority_status":"DOCUMENTED_CANDIDATE",
        "note":f"serving-lag observation point-2; endpoint {last}"})
    print(sid, code.decode() if isinstance(code,bytes) else code, last)
man["generated_at_utc"]=now()
man["append_in_place_note"]="files[] is append-in-place across the session; generated_at_utc is refreshed at each append and postdates some entries"
mp.write_text(json.dumps(man,indent=1))
out=CTL/"FRED_STALENESS_POINT2.json"; out.write_text(json.dumps(res,indent=1))
print("landed", out)
