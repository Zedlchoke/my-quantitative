"""Check 6 evidence script (verbatim body of the heredoc run 2026-10-03, exit 0).
Vendor parquet inventory: per-dir metadata row counts (no data read for counts),
plus a cheap outright/spread split reading ONLY the raw_symbol column.
Spread proxy: raw_symbol contains '-' (e.g. NQU8-NQM9).
"""
import glob, os, json
import pyarrow.parquet as pq
import pyarrow.compute as pc

ROOT = '/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/parquet'
syms = ['NQ', 'ES', '6E', '6B', '6A', '6J']
out = {}
for s in syms:
    files = sorted(glob.glob(f"{ROOT}/*AV1*-O1M-{s}/*.parquet") + glob.glob(f"{ROOT}/*AV1*-O1M-{s}-*/*.parquet"))
    per_dir = {}
    for f in files:
        d = os.path.basename(os.path.dirname(f))
        n = pq.ParquetFile(f).metadata.num_rows
        per_dir[d] = per_dir.get(d, 0) + n
    total = sum(per_dir.values())
    spread = 0
    for f in files:
        t = pq.read_table(f, columns=['raw_symbol'])
        spread += pc.sum(pc.match_substring(t.column('raw_symbol'), pattern='-')).as_py()
    out[s] = {'dirs': per_dir, 'total_rows': total, 'spread_rows': spread, 'outright_rows': total - spread}
    print(f"=== {s} ===")
    for d, n in sorted(per_dir.items()):
        print(f"  {d}: {n}")
    print(f"  TOTAL rows (parent, incl spreads): {total}")
    print(f"  spread rows (symbol contains '-'): {spread}")
    print(f"  outright rows: {total - spread}")
with open('check6_inventory.json', 'w') as fh:
    json.dump(out, fh, indent=2)
print("\nwrote check6_inventory.json")
