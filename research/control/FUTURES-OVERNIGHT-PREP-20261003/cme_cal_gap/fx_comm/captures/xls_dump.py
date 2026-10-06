import glob, os
import xlrd
def fmt(v):
    if isinstance(v, float) and 0 <= v < 1:
        mins = round(v*24*60)
        return f"{mins//60:02d}:{mins%60:02d}"
    return str(v).strip()
os.makedirs('extracted', exist_ok=True)
for fn in sorted(glob.glob('*.xls')):
    try:
        wb = xlrd.open_workbook(fn)
        lines = [f"FILE {fn} sheets={wb.sheet_names()}"]
        for sh in wb.sheets():
            lines.append(f"--- SHEET '{sh.name}' ({sh.nrows}x{sh.ncols})")
            for r in range(sh.nrows):
                vals = [fmt(sh.cell_value(r,c)).replace('\n',' ') for c in range(sh.ncols)]
                if any(vals):
                    lines.append(f"r{r}: " + ' | '.join(vals))
        open(f'extracted/{fn}.txt','w').write('\n'.join(lines))
        print(f"{fn}: OK")
    except Exception as e:
        print(f"{fn}: FAIL {type(e).__name__} {e}")
