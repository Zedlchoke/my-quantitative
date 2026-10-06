import re, sys, html as h
KEY = re.compile(r'(?i)(contract unit|termination of trading|listed contracts|settlement method|trading hours|price quotation|minimum price fluctuation|product code)\s*$')
def rows(path):
    t = open(path, encoding='utf-8', errors='replace').read()
    t = re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>', ' ', t)
    t = re.sub(r'(?is)<!--.*?-->', ' ', t)
    t = re.sub(r'(?i)<br/?>', '\n', t)
    t = re.sub(r'(?i)</(td|th)>', ' ~ ', t)
    t = re.sub(r'(?i)</tr>', '\n', t)
    t = re.sub(r'(?s)<[^>]+>', '', t)
    t = h.unescape(t)
    lines=[]
    for ln in t.split('\n'):
        ln = re.sub(r'[ \t\xa0]+',' ',ln).strip()
        if ln: lines.append(ln)
    # join: attribute line followed by value lines until next attribute
    out=[]
    cur=None
    for ln in lines:
        if KEY.match(ln):
            if cur: out.append(cur)
            cur=[ln,[]]
        elif cur is not None:
            if len(cur[1])<12: cur[1].append(ln)
            else:
                out.append(cur); cur=None
    if cur: out.append(cur)
    return out
for path in sys.argv[1:]:
    print(f"########## {path} ##########")
    for attr, vals in rows(path):
        if re.match(r'(?i)(contract unit|termination of trading|listed contracts|settlement method)$', attr.strip()):
            v=' / '.join(x.strip(' ~') for x in vals if x.strip(' ~'))
            print(f"[{attr.strip()}] {v[:800]}")
