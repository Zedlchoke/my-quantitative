import re, sys, html as h
def cells_row(tr):
    cells=re.findall(r'(?is)<t[hd][^>]*>(.*?)</t[hd]>',tr)
    out=[]
    for c in cells:
        c=re.sub(r'(?is)<div[^>]*>','\n',c); c=re.sub(r'(?is)<br\s*/?>','\n',c)
        c=re.sub(r'(?s)<[^>]+>','',h.unescape(c))
        parts=[re.sub(r'\s+',' ',p).strip() for p in c.split('\n')]
        parts=[p for p in parts if p]
        out.append('/'.join(parts) if parts else '-')
    return out
def extract(path):
    t=open(path,encoding='utf-8',errors='replace').read()
    m=re.search(r'(?is)<table[^>]*id="calendarFuturesProductTable1"[^>]*>(.*?)</table>',t)
    if not m: m=re.search(r'(?is)<table[^>]*class="ProductTable"[^>]*>(.*?)</table>',t)
    if not m: return []
    rows=[]
    for tr in re.findall(r'(?is)<tr[^>]*>(.*?)</tr>',m.group(1)):
        c=cells_row(tr)
        if len(c)>=8 and re.search(r'(19|20)\d\d',c[2]): rows.append(c[:8])
    return rows
for p in sys.argv[1:]:
    name=p.split('/')[-1]
    rows=extract(p)
    print(f"##### {name}: {len(rows)} contract rows")
    with open(p.replace('.html','_rows.txt'),'w') as f:
        f.write("contract_month|code|first_trade/last_trade|settlement|first_last_holding|first_last_position|first_last_notice|first_last_delivery\n")
        for r in rows: f.write('|'.join(r)+"\n")
    for r in rows[:3]: print(' | '.join(r))
    if rows: print(' ... LAST: ' + ' | '.join(rows[-1]))
