import re
lines = open('captures/cdx_holiday_files.txt').read().splitlines()
caps = []  # (ts, original, status)
for ln in lines:
    parts = ln.split()
    if len(parts) >= 3:
        ts, status = parts[0], parts[-1]
        original = ln[len(parts[0])+1:ln.rfind(' '+status)]
        caps.append((ts, original, status))
# group captures by file
from collections import defaultdict
byfile = defaultdict(list)
for ts, orig, st in caps:
    m = re.search(r'files/([^/?]+)$', orig)
    if m and st == '200':
        byfile[m.group(1)].append((ts, orig))

targets = []
# GAP 4: 2011-2015 per-holiday PDFs (energy/metals sections)
hol = ['new-years','martin-luther-king','presidents-day','good-friday','memorial-day','4th-of-july','labor-day','columbus-day','veterans-day','thanksgiving','christmas']
for yr in [2011,2012,2013]:
    for h in hol:
        targets.append(f'{yr}-{h}.pdf')
for yr in [2014,2015]:
    for h in hol:
        targets.append(f'{yr}-{h}-holiday-schedule.pdf')
targets += ['2015-veterans-day-schedule.pdf','2014-new-years.pdf']
# GAP 2: 2017-2023 per-holiday schedule XLS/XLSX (FX rows)
sched = []
for yr in range(2017,2024):
    for fn, lst in byfile.items():
        if fn.startswith(str(yyr) if False else str(yr)) and 'holiday-schedule' in fn and fn.endswith(('.xls','.xlsx')):
            sched.append(fn)
targets += sorted(set(sched))

manifest = []
for t in targets:
    cl = sorted(byfile.get(t, []))
    if not cl:
        print(f'MISSING {t}')
        continue
    manifest.append((t, cl[0][0], cl[0][1]))
with open('manifest.txt','w') as f:
    for t, ts, orig in manifest:
        f.write(f'{t}\t{ts}\t{orig}\n')
print(f'manifest entries: {len(manifest)}')
