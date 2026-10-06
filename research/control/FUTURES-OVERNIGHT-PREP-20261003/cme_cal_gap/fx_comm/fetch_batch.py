import subprocess, os, time, json, sys
lines = [l.split('\t') for l in open('manifest.txt').read().splitlines() if l.strip()]
# prefer non-compact when sibling exists
names = {t for t,_,_ in lines}
sel = []
for t, ts, orig in lines:
    if '-compact' in t:
        base = t.replace('-compact','')
        if base in names: continue
    sel.append((t,ts,orig))
print(f"fetching {len(sel)} files", file=sys.stderr)
os.makedirs('captures', exist_ok=True)
log = open('fetch_log.jsonl','a')
ok=fail=0
for i,(t,ts,orig) in enumerate(sel):
    fn = os.path.join('captures', t)
    if os.path.exists(fn) and os.path.getsize(fn) > 500:
        ok+=1; continue
    url = f"https://web.archive.org/web/{ts}/{orig}"
    r = subprocess.run(['/usr/bin/curl','-sL','--max-time','70',url,'-o',fn])
    size = os.path.getsize(fn) if os.path.exists(fn) else 0
    sig = open(fn,'rb').read(4) if size else b''
    good = sig in (b'%PDF', b'\xd0\xcf\x11\xe0', b'PK\x03\x04')
    rec = {"utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"file":t,"url":url,"tool":"curl_default_ua","size":size,"sig_ok":good}
    if size and not good:
        os.rename(fn, fn+'.bad'); rec["note"]="not PDF/XLS/XLSX signature; saved as .bad"
    if good: ok+=1
    else: fail+=1
    log.write(json.dumps(rec)+"\n"); log.flush()
    print(f"[{i+1}/{len(sel)}] {t} size={size} sig={'OK' if good else 'BAD'}", file=sys.stderr)
    time.sleep(2.5)
log.close()
print(f"done ok={ok} fail={fail}", file=sys.stderr)
