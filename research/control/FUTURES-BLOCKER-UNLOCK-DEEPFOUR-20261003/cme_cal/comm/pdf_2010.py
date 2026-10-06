from pypdf import PdfReader
r=PdfReader('globex_2010_holiday.pdf')
print("pages:", len(r.pages))
# find commodity section
for i,p in enumerate(r.pages):
    t=p.extract_text() or ''
    if 'COMMODITY' in t.upper() or 'NYMEX' in t.upper() or 'COMEX' in t.upper():
        head=' '.join(t.split())[:150]
        print(f"--- p{i+1}: {head}")
