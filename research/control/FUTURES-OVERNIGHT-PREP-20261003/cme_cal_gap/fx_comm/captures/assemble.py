import re, json, datetime
# ---------- FX ----------
sym_map = {'EC':'6E','BP':'6B','JY':'6J','J1':'6J','AD':'6A'}
rows = {}  # (sym, code) -> dict
def add(sym, month, code, first, last, ts, src):
    key = (sym, code)
    d = {'sym':sym,'month':month,'code':code,'first_trade':first,'last_trade':last,'capture_ts':ts,'src':src}
    if key in rows:
        prev = rows[key]
        if prev['last_trade'] != last:
            print(f"CONFLICT {code}: {prev['last_trade']} ({prev['capture_ts']}) vs {last} ({ts})")
        else:
            rows[key]['also_ts'] = rows[key].get('also_ts',[]) + [ts]
            return
    rows[key] = d

# old-format rows (from fx_old_rows.json: [sym, month, code(truncated), first, last, file])
old_ts = {'fx_ec_20110527042052.html':'20110527042052','fx_bp_20100219101527.html':'20100219101527',
          'fx_jy_20100120181108.html':'20100120181108','fx_jy_20100814205214.html':'20100814205214'}
for sym, month, code_trunc, first, last, f in json.load(open('fx_old_rows.json')):
    # rebuild full code from month+year
    mm = re.match(r'([A-Z]{3})\s*(\d{2,4})', month)
    mon, yr = mm.group(1), mm.group(2)
    yr2 = yr[-2:]
    monletter = {'MAR':'H','JUN':'M','SEP':'U','DEC':'Z'}[mon]
    root = {'6E':'EC','6B':'BP','6J':'JY','6A':'AD'}[sym]
    code = f"{root}{monletter}{yr2}"
    add(sym, f"{mon} 20{yr2}", code, first, last, old_ts[f], 'old_html')
# 2014 JY capture used J1 codes already handled by full-code extraction below

# JSON-era captures
jfiles = [('6E','fx_ec_20150111002610.html','20150111002610'),('6E','ecf_cal_20180228224018.html','20180228224018'),
          ('6B','fx_bp_20180226190632.html','20180226190632'),
          ('6J','fx_jy_20141015223742.html','20141015223742'),('6J','fx_jy_20180226182137.html','20180226182137'),
          ('6A','fx_ad_20180301074633.html','20180301074633')]
for sym, f, ts in jfiles:
    html = open(f).read()
    for cm, code, ft, lt in re.findall(r'"contractMonth":"(.*?)","productCode":"([^"]+?)","firstTrade":"(.*?)","lastTrade":"(.*?)"', html):
        if not re.match(r'^(EC|BP|JY|J1|AD)[A-Z]\d{2}$', code): continue
        add(sym, cm.upper(), code, ft, lt, ts, 'json')
# normalize last_trade to ISO-ish dd Mon yyyy
def norm(d):
    d = d.strip()
    for fmt in ('%m/%d/%Y','%d %b %Y'):
        try: return datetime.datetime.strptime(d, fmt).strftime('%m/%d/%Y')
        except ValueError: pass
    return d
fx = sorted(rows.values(), key=lambda r:(r['sym'], r['code']))
for r in fx: r['last_trade'] = norm(r['last_trade']); r['first_trade'] = norm(r['first_trade'])
json.dump(fx, open('fx_gapfill_rows.json','w'), indent=1)

# rule QA: last trade == 2nd business day (Mon-Fri) preceding 3rd Wednesday of contract month
def third_wed(y, m):
    d = datetime.date(y, m, 1)
    weds = [datetime.date(y,m,dd) for dd in range(1,32) if (lambda dd: dd<=28 or True)(dd) and _valid(y,m,dd) and datetime.date(y,m,dd).weekday()==2]
    return weds[2]
def _valid(y,m,dd):
    try: datetime.date(y,m,dd); return True
    except ValueError: return False
def rule_date(y,m):
    tw = third_wed(y,m)
    bd = [tw - datetime.timedelta(days=k) for k in range(1,10) if (tw - datetime.timedelta(days=k)).weekday() < 5]
    return bd[1]  # second business day preceding
dev=0; tot=0
for r in fx:
    mm = re.match(r'([A-Z]{3}) (\d{4})', r['month'])
    if mm.group(1) not in ('MAR','JUN','SEP','DEC'): continue
    mon = {'MAR':3,'JUN':6,'SEP':9,'DEC':12}[mm.group(1)]
    y = int(mm.group(2))
    if y < 2010 or y > 2022: continue
    lt = datetime.datetime.strptime(r['last_trade'], '%m/%d/%Y').date()
    exp = rule_date(y, mon)
    tot += 1
    if lt != exp:
        dev += 1; print(f"RULE-DEVIATION {r['code']} table {lt} rule {exp}")
print(f"FX rule QA: {tot} rows, {dev} deviations")

# per-symbol/year coverage of NEW rows (beyond parent's 96)
parent = json.load(open('/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep/research/control/FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/cme_cal/fx/fx_cal_coverage.json'))
parent_keys = {(e['sym'], e['code']) for e in parent['expirations']}
fx_q = [r for r in fx if re.match(r'(MAR|JUN|SEP|DEC) \d{4}', r['month']) and 2010 <= int(r['month'].split()[1]) <= 2026]
new_rows = [r for r in fx_q if (r['sym'], r['code']) not in parent_keys]
print(f"parent rows: {len(parent_keys)}; gapfill new: {len(new_rows)}; combined: {len(parent_keys)+len(new_rows)}")
from collections import Counter
cnt = Counter(r['sym'] for r in new_rows)
print("new per sym:", dict(cnt))
allc = Counter()
allc.update(e['sym'] for e in parent['expirations'])
allc.update(cnt)
print("combined per sym:", dict(allc))
json.dump(new_rows, open('fx_new_rows.json','w'), indent=1)

# ---------- GC / SI ----------
gc = []
html = open('gc_cal_20180227093156.html').read()
for cm, code, ft, lt in re.findall(r'"contractMonth":"(.*?)","productCode":"(GC[A-Z]\d{2})","firstTrade":"(.*?)","lastTrade":"(.*?)"', html):
    gc.append({'sym':'GC','month':cm,'code':code,'first_trade':ft,'last_trade':lt,'capture_ts':'20180227093156'})
si = []
html = open('si_cal_20180227093206.html').read()
for cm, code, ft, lt in re.findall(r'"contractMonth":"(.*?)","productCode":"(SI[A-Z]\d{2})","firstTrade":"(.*?)","lastTrade":"(.*?)"', html):
    si.append({'sym':'SI','month':cm,'code':code,'first_trade':ft,'last_trade':lt,'capture_ts':'20180227093206'})
print(f"GC rows: {len(gc)} ({gc[0]['month']} -> {gc[-1]['month']})")
print(f"SI rows: {len(si)} ({si[0]['month']} -> {si[-1]['month']})")
# rule QA for GC/SI: third last business day of contract month
def third_last_bd(y, m):
    import calendar
    last = datetime.date(y, m, calendar.monthrange(y,m)[1])
    bd = [last - datetime.timedelta(days=k) for k in range(0,15) if (last - datetime.timedelta(days=k)).weekday() < 5]
    return bd[2]
MON = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12}
for tag, arr in (('GC',gc),('SI',si)):
    dev=0; tot=0
    for r in arr:
        y = int(r['month'].split()[1]); mon = MON[r['month'].split()[0]]
        lt = datetime.datetime.strptime(r['last_trade'], '%d %b %Y').date()
        exp = third_last_bd(y, mon); tot+=1
        if lt != exp: dev+=1; print(f"{tag} RULE-DEVIATION {r['code']} table {lt} rule {exp}")
    print(f"{tag} rule QA: {tot} rows, {dev} deviations")
json.dump(gc+si, open('gc_si_gapfill_rows.json','w'), indent=1)
