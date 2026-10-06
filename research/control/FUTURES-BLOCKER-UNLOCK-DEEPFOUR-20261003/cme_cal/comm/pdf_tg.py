from pypdf import PdfReader
r=PdfReader('2011-thanksgiving.pdf')
print("pages:", len(r.pages))
for i,p in enumerate(r.pages):
    t=p.extract_text() or ''
    if 'NYMEX' in t.upper() or 'COMEX' in t.upper() or 'Commodit' in t:
        print(f"===== PAGE {i+1} ====="); print(t)
