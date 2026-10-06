import glob, re, json, os
os.makedirs('..', exist_ok=True)
out = {}

# ---- XLS (2017-2023): FX + Energy/Metals family rows ----
for fn in sorted(glob.glob('extracted/20*.xls.txt')):
    lines = open(fn).read().splitlines()
    title = next((l for l in lines if l.startswith('r0:')), '')
    hdr = [l for l in lines if re.match(r'r[123]:', l)]
    fam, fxrow, emrow = None, None, None
    for i, l in enumerate(lines):
        if re.match(r'r\d+: FX Products \|', l) and fxrow is None:
            fxrow = l
            # capture exceptions rows that follow
            j = i+1; exc=[]
            while j < len(lines) and not re.match(r'r\d+: (Interest|Equity|Cryptocurrency|Energy|Grain|Other)', lines[j]):
                if lines[j].strip() and 'Exceptions' not in lines[j] and not lines[j].strip().endswith('| ' * 1):
                    exc.append(lines[j])
                j += 1
                if j-i > 5: break
            fxrow += '   [exceptions] ' + ' ;; '.join(x.strip() for x in exc if x.strip())
        if re.match(r'r\d+: (Energy, Metals[^|]*|NYMEX[^|]*)\|', l) and emrow is None:
            emrow = l
    if fxrow or emrow:
        yr = fn.split('/')[-1].split('-')[0][8:12] if False else re.search(r'20\d\d', fn).group(0)
        hol = re.sub(r'^\d{4}-','',fn.split('/')[-1].replace('.xls.txt','')).replace('-holiday-schedule','').replace('-schedule','').replace('-day','').replace('-compact','').replace('-mgex-dme','').replace('-arragements','').replace('.xlsx','')
        out.setdefault('xls',{}).setdefault(yr,{})[hol] = {'file': fn.split('/')[-1].replace('.txt',''), 'title': title[4:200], 'headers': [h[4:400] for h in hdr], 'fx_row': fxrow, 'energy_metals_row': emrow}

# ---- PDF (2011-2015): FX + Energy/Metals sections verbatim ----
for fn in sorted(glob.glob('extracted/20*.pdf.txt')):
    txt = open(fn).read()
    # split into sections by known family headers
    secs = {}
    for m in re.finditer(r'(CME Group FX Products|Interest Rate & FX Products|NYMEX, COMEX® and DME Products on CME Globex|Energy, Metals & DME Products|Equity, Interest Rate, FX, Energy, Metals & DME Products)(.*?)(?=(?:CME Group (?:Equity|FX|Interest)|Interest Rate & FX|NYMEX, COMEX|Energy, Metals|Equity Products|Grain, Oilseed|Livestock|Globex®|\Z))', txt, re.S):
        head, body = m.group(1), re.sub(r'\s+',' ',m.group(2)).strip()
        secs.setdefault(head, []).append(body[:600])
    if secs:
        base = fn.split('/')[-1].replace('.pdf.txt','')
        yr = base.split('-')[0]; hol = '-'.join(base.split('-')[1:]).replace('-holiday-schedule','').replace('-schedule','')
        out.setdefault('pdf',{}).setdefault(yr,{})[hol] = {'file': base+'.pdf', 'sections': {k: v for k,v in secs.items()}}
json.dump(out, open('holiday_transcription.json','w'), indent=1)
# summary
for kind in ('pdf','xls'):
    if kind in out:
        for yr in sorted(out[kind]):
            hols = sorted(out[kind][yr])
            nfx = sum(1 for h in hols if out[kind][yr][h].get('fx_row') or any('FX' in k for k in (out[kind][yr][h].get('sections') or {})))
            nem = sum(1 for h in hols if out[kind][yr][h].get('energy_metals_row') or any(('NYMEX' in k or 'Energy' in k) for k in (out[kind][yr][h].get('sections') or {})))
            print(f"{kind.upper()} {yr}: {len(hols)} holidays fetched, FX rows in {nfx}, energy/metals rows in {nem}: {', '.join(hols)}")
