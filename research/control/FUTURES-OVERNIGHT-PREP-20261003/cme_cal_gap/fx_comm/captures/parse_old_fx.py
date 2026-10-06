import re, json, sys
files = [('6E','fx_ec_20110527042052.html'),('6B','fx_bp_20100219101527.html'),
         ('6J','fx_jy_20100120181108.html'),('6J','fx_jy_20100814205214.html')]
res=[]
code_re = re.compile(r'id="([A-Z0-9]{3,6}FUT)"')
for sym, f in files:
    html = open(f, encoding='utf-8', errors='replace').read()
    print(f"{f}: len={len(html)}", file=sys.stderr)
    n=0
    for chunk in html.split('<tr'):
        cm = code_re.search(chunk[:150])
        if not cm:
            continue
        code = cm.group(1)[:4]
        n+=1
        tds = re.findall(r'<td[^>]*>(.*?)</td>', chunk, re.S)
        clean=[]
        for td in tds:
            txt = re.sub(r'<[^>]+>',' ',td)
            txt = re.sub(r'\s+',' ',txt).strip()
            dates = re.findall(r'\d{2}/\d{2}/\d{4}', txt)
            clean.append(dates if dates else txt)
        if len(clean)>=4:
            first = clean[2][0] if isinstance(clean[2],list) and clean[2] else ''
            last  = clean[3][0] if isinstance(clean[3],list) and clean[3] else ''
            res.append((sym, clean[0], code, first, last, f))
    print(f"{f}: matched {n} FUT rows", file=sys.stderr)
for r in res:
    print(f"{r[0]} | {r[1]} | {r[2]} | First {r[3]} | Last {r[4]} | {r[5]}")
json.dump(res, open('fx_old_rows.json','w'))
print("total:", len(res))
