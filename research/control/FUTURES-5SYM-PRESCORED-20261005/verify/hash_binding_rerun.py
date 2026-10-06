import json, subprocess, sys, re, hashlib

WT = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-5sym-prescored/prep"
RD = "research/control/FUTURES-5SYM-PRESCORED-20261005"
AUDIT_SHA = "ac5c4c18dc1ab1253c61f84dc1fa9fc4f7583ed7"
LANES = ["INTAKE","NQ","FXEB","FXJA","EXEC","HYPO","CALCOST"]
REQ = ["task_id","cycle_id","role","lane","dispatch_sha","actual_start_sha","commit_sha",
       "changed_paths","tests","authority_claims","known_limitations","incidents",
       "tree_status","workers","outputs","recommended_next_action"]
HEX40 = re.compile(r"^[0-9a-f]{40}$")

def git(*args):
    r = subprocess.run(["git","-C",WT]+list(args),capture_output=True)
    return r.returncode, r.stdout, r.stderr

results = {}
grand = {"matched":0,"mismatched":0,"not_in_commit":0}
for lane in LANES:
    p = f"{RD}/dispatch/handoff_{lane}.json"
    rc,out,err = git("show", f"{AUDIT_SHA}:{p}")
    if rc != 0:
        results[lane] = {"error": f"handoff not in commit: {err.decode().strip()}"}
        continue
    d = json.loads(out)
    rep = {"missing_fields":[k for k in REQ if k not in d]}
    rep["schema"] = d.get("schema")
    ds, ass = d.get("dispatch_sha"), d.get("actual_start_sha")
    rep["dispatch_sha"] = ds; rep["actual_start_sha"] = ass
    rep["sha40_ok"] = bool(HEX40.match(str(ds or ""))) and bool(HEX40.match(str(ass or "")))
    rep["dispatch_eq_start"] = (ds == ass)
    rep["commit_sha"] = d.get("commit_sha")
    rc2,_,_ = git("cat-file","-e",f"{d.get('commit_sha')}^{{commit}}")
    rep["commit_exists"] = (rc2 == 0)
    tbad = []
    for i,t in enumerate(d.get("tests",[])):
        miss = [k for k in ("command","exit_code","verdict","log_digest") if k not in t]
        if miss: tbad.append((i,miss))
        elif t.get("verdict") not in ("PASS","FAIL","NOT_RUN"): tbad.append((i,["verdict_invalid:"+str(t.get("verdict"))]))
    rep["tests_struct_bad"] = tbad
    rep["tests_verdicts"] = [t.get("verdict") for t in d.get("tests",[])]
    om, omm, onot = [], [], []
    for o in d.get("outputs",[]):
        path, sha = o.get("path"), o.get("sha256")
        rc3, blob, _ = git("show", f"{AUDIT_SHA}:{path}")
        if rc3 != 0:
            rc4,_,_ = git("cat-file","-e",f"{d.get('commit_sha')}:{path}")
            onot.append({"path":path,"in_lane_commit":rc4==0})
            continue
        h = hashlib.sha256(blob).hexdigest()
        if h == sha: om.append(path)
        else: omm.append({"path":path,"claimed":sha,"actual":h})
    rep["outputs_matched_count"] = len(om); rep["outputs_mismatched"] = omm; rep["outputs_not_at_audit_sha"] = onot
    grand["matched"]+=len(om); grand["mismatched"]+=len(omm); grand["not_in_commit"]+=len(onot)
    results[lane] = rep

print(json.dumps({"per_lane":results,"grand_totals":grand},indent=1))
