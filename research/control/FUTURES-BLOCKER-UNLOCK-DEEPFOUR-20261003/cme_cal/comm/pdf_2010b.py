from pypdf import PdfReader
import re,sys
r=PdfReader('globex_2010_holiday.pdf')
for i,p in enumerate(r.pages):
    t=p.extract_text() or ''
    if 'NYMEX & COMEX' in t or 'NYMEX, COMEX' in t:
        print(f"===== PAGE {i+1} =====")
        print(t)
