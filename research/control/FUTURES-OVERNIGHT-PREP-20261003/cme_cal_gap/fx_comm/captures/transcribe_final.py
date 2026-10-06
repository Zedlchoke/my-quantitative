import glob, re, json

ts_map = {}
for ln in open('../manifest.txt').read().splitlines():
    if '\t' in ln:
        f, ts, orig = ln.split('\t')
        ts_map[f] = ts

res = {}
def rec(kind, yr, hol, fn, fx, em, note=None):
    e = res.setdefault(yr, {}).setdefault(hol, {'file': fn, 'capture_ts': ts_map.get(fn, '?'), 'kind': kind})
    if fx: e['fx'] = fx
    if em: e['energy_metals'] = em
    if note: e['note'] = note

HOLNORM = [('martin-luther-king','MLK'),('mlk-day','MLK'),('mlk','MLK'),('pesidents','Presidents'),('presidents','Presidents'),
 ('good-friday','GoodFriday'),('easter','GoodFriday'),('memorial','Memorial'),('4th-of-july','July4'),('independence','July4'),
 ('fourth-of-july','July4'),('labor','Labor'),('columbus','Columbus'),('veterans','Veterans'),('juneteenth','Juneteenth'),
 ('thanksgiving','Thanksgiving'),('christmas','Christmas'),('new-years','NewYear'),('newyears','NewYear')]
def holname(base):
    b = base
    for k, v in HOLNORM:
        if k in b: return v
    return b

# ---- XLS family rows (any format) ----
for fn in sorted(glob.glob('20*.xls')):
    lines = open(f'extracted/{fn}.txt').read().splitlines() if glob.glob(f'extracted/{fn}.txt') else []
    if not lines: continue
    body = open(f'extracted/{fn}.txt').read()
    yr = fn[:4]; hol = holname(fn)
    fx = em = None
    for l in lines:
        if re.match(r'r\d+:\s*(FX Products|FX)\s*\|', l) and fx is None: fx = l.split(': ',1)[1]
        if re.match(r'r\d+:\s*(Energy, Metal[^|]*|NYMEX[^|]*)\|', l) and em is None: em = l.split(': ',1)[1]
    note = None
    if ('unaffected' in body or 'uneffected' in body) and 'normal schedule' in body and not fx and not em:
        m = re.search(r'(Monday, \w+ \d+|Friday, \w+ \d+)[^\n]*', body)
        note = 'ONE-CELL: ' + re.sub(r'\s+',' ', body[body.find('Monday,') if 'Monday,' in body else 0:])[:260]
        fx = note; em = note
    if fx or em or note:
        rec('xls', yr, hol, fn, fx, em, note)

# ---- PDF family sections ----
for fn in sorted(glob.glob('20*.pdf')):
    txt = open(f'extracted/{fn}.txt').read()
    yr = fn[:4]; hol = holname(fn)
    secs = {}
    for m in re.finditer(r'(CME Group FX Products|Interest Rate & FX Products|NYMEX[^\n]*?Products|Energy, Metal[^\n]*?Products|Equity, Interest Rate, FX, Energy, Metals & DME Products)', txt):
        head = m.group(1)
        start = m.end()
        nxt = len(txt)
        for h2 in ('CME Group Equity Products','CME Group FX Products','CME Group Interest Rate','Interest Rate & FX Products','NYMEX, COMEX','NYMEX & COMEX','Energy, Metal','Equity Products','Grain, Oilseed','Livestock','Bursa Malaysia','Other CME Group Products','Globex®','The Green Exchange'):
            p = txt.find(h2, start)
            if p != -1 and p < nxt: nxt = p
        body = re.sub(r'[ \t]+',' ', txt[start:nxt]).strip()
        body = re.sub(r'\n{2,}','\n', body)
        secs.setdefault(head, []).append(body[:700])
    note = None
    if not secs and re.search(r'unaffected', txt, re.I):
        note = 'ONE-PAGER: ' + re.sub(r'\s+',' ', txt)[:300]
        secs = {'normal_statement': [note]}
    fx = ' || '.join(v[0] for k, v in secs.items() if 'FX' in k) or (note if note else None)
    em = ' || '.join(v[0] for k, v in secs.items() if 'NYMEX' in k or 'Energy' in k) or (note if note else None)
    if (not fx or not em) and not note:
        # retry on whitespace-flattened text (pypdf sometimes splits headers across lines)
        flat = re.sub(r'\s+',' ', txt)
        secs2 = {}
        for m in re.finditer(r'(CME Group FX Products|Interest Rate & FX Products|NYMEX[^ ]*?[^|]*?Products(?: on CME Globex)?|Energy, Metal[^ |]*?(?:, Softs)?[^|]*?Products)', flat):
            head = m.group(1)
            start = m.end()
            nxt = len(flat)
            for h2 in ('CME Group Equity Products','CME Group FX Products','CME Group Interest Rate','Interest Rate & FX Products','NYMEX, COMEX','NYMEX & COMEX','Energy, Metal','Equity Products','Grain, Oilseed','Livestock','Bursa Malaysia','Other CME Group Products','Globex','The Green Exchange'):
                p = flat.find(h2, start)
                if p != -1 and p < nxt: nxt = p
            body = flat[start:nxt].strip()[:700]
            if body: secs2.setdefault(head, []).append(body)
        if not fx:
            fx = ' || '.join(v[0] for k, v in secs2.items() if 'FX' in k) or None
        if not em:
            em = ' || '.join(v[0] for k, v in secs2.items() if 'NYMEX' in k or 'Energy' in k) or None
    if fx or em:
        rec('pdf', yr, hol, fn, fx, em, note if note else None)

json.dump(res, open('holiday_transcription.json','w'), indent=1)
for yr in sorted(res):
    hols = res[yr]
    fx_ok = [h for h in hols if hols[h].get('fx')]
    em_ok = [h for h in hols if hols[h].get('energy_metals')]
    print(f"{yr}: {len(hols)} artifacts | FX: {len(fx_ok)}/{sorted(fx_ok)} | E/M: {len(em_ok)}")
