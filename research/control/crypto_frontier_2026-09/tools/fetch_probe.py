"""Light keyless canary fetcher: sequential GETs, raw bytes + sha256 sidecar. Survey tooling only."""
import urllib.request, urllib.error, json, hashlib, sys, time, os
BASE='/Users/hoangminhlong/my-quantitative/research/control/crypto_frontier_2026-09/probes'
UA='quant-survey-canary/1.0 (keyless light probe; research survey)'
def fetch(name, url, method='GET', body=None, headers=None, timeout=30, max_bytes=None):
    h={'User-Agent':UA}
    if headers: h.update(headers)
    data=body.encode() if isinstance(body,str) else body
    if data is not None: h['Content-Type']='application/json'
    req=urllib.request.Request(url,data=data,headers=h,method=method)
    t0=time.time()
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            raw=r.read(max_bytes) if max_bytes else r.read()
            status=r.status; final_url=r.geturl(); hdr=dict(r.headers)
    except urllib.error.HTTPError as e:
        raw=e.read(max_bytes) if max_bytes else e.read()
        status=e.code; final_url=url; hdr=dict(e.headers)
    except Exception as e:
        meta={'probe':name,'url':url,'method':method,'fetched_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
              'http_status':None,'bytes':0,'sha256':None,'error':repr(e),'elapsed_s':round(time.time()-t0,2)}
        json.dump(meta,open(os.path.join(BASE,name+'.meta.json'),'w'),indent=1)
        print(json.dumps(meta)); return meta
    fp=os.path.join(BASE,name+'.raw')
    open(fp,'wb').write(raw)
    meta={'probe':name,'url':url,'method':method,'final_url':final_url,
          'fetched_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
          'http_status':status,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
          'content_type':hdr.get('Content-Type'),'elapsed_s':round(time.time()-t0,2)}
    if max_bytes: meta['truncated_at']=max_bytes
    json.dump(meta,open(os.path.join(BASE,name+'.meta.json'),'w'),indent=1)
    print(json.dumps(meta)); return meta
if __name__=='__main__':
    jobs=json.load(open(sys.argv[1]))
    for j in jobs: fetch(**j); time.sleep(1.0)
