import re, sys, html as h
def rows(path):
    t = open(path, encoding='utf-8', errors='replace').read()
    t = re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>', ' ', t)
    t = re.sub(r'(?is)<!--.*?-->', ' ', t)
    t = re.sub(r'(?i)</t[dh]>', ' | ', t)
    t = re.sub(r'(?i)</tr>', '\nROWEND\n', t)
    t = re.sub(r'(?s)<[^>]+>', ' ', t)
    t = h.unescape(t)
    t = re.sub(r'[ \t\xa0]+', ' ', t)
    out=[]
    for raw in t.split('ROWEND'):
        r = raw.strip()
        r = re.sub(r'(\s*\|\s*)+', ' | ', r).strip(' |')
        if r: out.append(r)
    return out
for sym in sys.argv[1:]:
    print(f"########## {sym} ##########")
    for r in rows(f'html/{sym}_specspec_2018req.html'):
        if re.search(r'(?i)terminat|last trade|trading hour|contract month|listed|delivery|settlement|first notice|business day|calendar day|25th|third|month prior', r):
            print(r[:600])
            print('---')
