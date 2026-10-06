import glob, re, json, zipfile, os

def xlsx_dump(fn):
    """Minimal xlsx reader via stdlib (shared strings + first sheets)."""
    try:
        z = zipfile.ZipFile(fn)
        shared = []
        if 'xl/sharedStrings.xml' in z.namelist():
            ss = z.read('xl/sharedStrings.xml').decode('utf-8')
            shared = [re.sub(r'<[^>]+>','',m) for m in re.findall(r'<si>(.*?)</si>', ss, re.S)]
        sheets = [n for n in z.namelist() if re.match(r'xl/worksheets/sheet\d+\.xml', n)]
        out = [f"FILE {fn}"]
        for sh in sheets:
            xml = z.read(sh).decode('utf-8')
            out.append(f"--- {sh}")
            for rowm in re.finditer(r'<row[^>]*>(.*?)</row>', xml, re.S):
                cells = []
                for cm in re.finditer(r'<c([^>]*)>(?:<v>(.*?)</v>)?(?:.*?<t[^>]*>(.*?)</t>)?</c>', rowm.group(1), re.S):
                    attrs, v, t = cm.groups()
                    val = t if t is not None else (v if v is not None else '')
                    if 't="s"' in attrs and val: val = shared[int(val)]
                    cells.append(re.sub(r'\s+',' ',val).strip())
                if any(cells): out.append(' | '.join(cells))
        return '\n'.join(out)
    except Exception as e:
        return f"FILE {fn} FAIL {e}"

# handle the one xlsx
x = xlsx_dump('2019-thanksgiving-day-holiday-schedule-arragements.xlsx')
open('extracted/2019-thanksgiving-day-holiday-schedule-arragements.xlsx.txt','w').write(x)
print(x[:1500])
