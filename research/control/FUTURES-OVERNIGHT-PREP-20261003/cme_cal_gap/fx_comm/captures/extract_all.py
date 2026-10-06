import glob, os, sys
from pypdf import PdfReader

def pdf_dump(fn):
    out = []
    r = PdfReader(fn)
    for p in r.pages:
        t = p.extract_text() or ''
        out.append(t)
    return '\n'.join(out)

os.makedirs('extracted', exist_ok=True)
for fn in sorted(glob.glob('*.pdf')):
    if os.path.exists(fn+'.bad'): continue
    try:
        txt = pdf_dump(fn)
        open(f'extracted/{fn}.txt','w').write(txt)
        # quick marker scan
        marks = [m for m in ('NYMEX','COMEX','FX Products','Equity Products','Interest Rate','DME','Metals') if m in txt]
        print(f"{fn}: {len(txt)} chars; markers: {marks}")
    except Exception as e:
        print(f"{fn}: EXTRACT-FAIL {e}")
