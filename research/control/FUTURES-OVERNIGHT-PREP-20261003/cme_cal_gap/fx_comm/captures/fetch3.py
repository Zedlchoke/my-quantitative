import subprocess, os, time, json
add = [
 ('2020-good-friday-schedule.xls','20200406075547' if False else None),
 ('2020-independence-day-schedule.xls',None),
 ('2020-mlk-day-schedule.xls',None),
]
# resolve ts via CDX first
log = open('../fetch_log.jsonl','a')
for fn, _ in add:
    q = f"https://web.archive.org/cdx/search/cdx?url=www.cmegroup.com%2Ftools-information%2Fholiday-calendar%2Ffiles%2F{fn}&fl=timestamp,statuscode&limit=10&filter=statuscode:200"
    r = subprocess.run(['/usr/bin/curl','-s','--max-time','40',q], capture_output=True, text=True)
    lines = [l.split() for l in r.stdout.splitlines() if l.strip()]
    if not lines:
        print(fn, 'NO 200 CAPTURES'); continue
    ts = lines[0][0]
    url = f"https://web.archive.org/web/{ts}/http://www.cmegroup.com/tools-information/holiday-calendar/files/{fn}"
    subprocess.run(['/usr/bin/curl','-sL','--max-time','70',url,'-o',fn])
    sig = open(fn,'rb').read(4) if os.path.exists(fn) else b''
    good = sig in (b'\xd0\xcf\x11\xe0', b'PK\x03\x04')
    rec = {"utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"file":fn,"url":url,"tool":"curl_default_ua","size":os.path.getsize(fn) if os.path.exists(fn) else 0,"sig_ok":good}
    log.write(json.dumps(rec)+"\n"); log.flush()
    print(fn, 'ts=', ts, 'sig_ok=', good)
    with open('../manifest.txt','a') as mf: mf.write(f"{fn}\t{ts}\thttp://www.cmegroup.com/tools-information/holiday-calendar/files/{fn}\n")
    time.sleep(2.5)
log.close()
