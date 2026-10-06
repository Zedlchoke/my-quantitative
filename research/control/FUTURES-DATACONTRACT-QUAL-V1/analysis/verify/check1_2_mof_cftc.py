"""Checks 1-2 evidence script (verbatim body of the heredoc run 2026-10-03).
Interpreter: /Users/hoangminhlong/my-quantitative/.venv/bin/python
Read-only: MOF tidy + CFTC tidy sha256 + backups.
"""
import hashlib, os, glob
import pyarrow.parquet as pq

NP = "/Users/hoangminhlong/.my-quantitative-data/futures-nonprice-10syms/normalized"

print("=== CHECK 1: MOF tidy ===")
p = f"{NP}/mof_intervention_tidy.parquet"
df = pq.read_table(p).to_pandas()
print("rows:", len(df))
print("date range:", df.observation_period.min(), "..", df.observation_period.max())
mask = df.observation_period.astype(str).str.startswith("2022-10-24")
print("2022-10-24 rows:")
print(df[mask].to_string())
print("bak exists:", os.path.exists(f"{NP}/mof_intervention_tidy.parquet.bak_81rows_20261003"))
bak = pq.read_table(f"{NP}/mof_intervention_tidy.parquet.bak_81rows_20261003").to_pandas()
print("bak rows:", len(bak))

print()
print("=== CHECK 2: CFTC sha256 ===")
c = f"{NP}/cftc_legacy_tidy.parquet"
h = hashlib.sha256(open(c, 'rb').read()).hexdigest()
print("sha256:", h)
print("prefix match f7a2719e745c2f6f:", h.startswith("f7a2719e745c2f6f"))
print("current rows:", pq.ParquetFile(c).metadata.num_rows)
for b in sorted(glob.glob(f"{NP}/cftc_legacy_tidy.parquet.bak*")):
    hb = hashlib.sha256(open(b, 'rb').read()).hexdigest()
    print("backup:", os.path.basename(b), "rows:", pq.ParquetFile(b).metadata.num_rows, "sha256[:16]:", hb[:16])
