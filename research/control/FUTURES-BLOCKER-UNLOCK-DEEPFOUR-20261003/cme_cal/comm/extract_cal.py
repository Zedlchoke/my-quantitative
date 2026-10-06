import re, sys, html as h
def table_rows(path):
    t=open(path,encoding='utf-8',errors='replace').read()
    m=re.search(r'(?is)<table[^>]*id="calendarFuturesProductTable1"[^>]*>(.*?)</table>',t)
    if not m:
        m=re.search(r'(?is)<table[^>]*cmeCalendarFutures[^>]*>(.*?)</table>',t)
    if not m: return None
    body=m.group(1)
    rows=[]
    for tr in re.findall(r'(?is)<tr[^>]*>(.*?)</tr>',body):
        cells=re.findall(r'(?is)<t[hd][^>]*>(.*?)</t[hd]>',tr)
        cells=[re.sub(r'\s+',' ',re.sub(r'(?s)<[^>]+>',' ',h.unescape(c))).strip() for c in cells]
        cells=[re.sub(r'\s*/\s*','/',c) for c in cells]
        if cells and any(cells): rows.append(cells)
    return rows
for p in sys.argv[1:]:
    print(f"##### {p}")
    r=table_rows(p)
    if not r: print("NO calendarFuturesProductTable1 TABLE"); continue
    print(f"rows={len(r)}")
    for row in r[:8]: print(' | '.join(row))
    if len(r)>8: print(' ...'); print(' | '.join(r[-2]))
