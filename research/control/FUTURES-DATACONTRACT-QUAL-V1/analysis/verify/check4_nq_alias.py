"""Check 4 evidence script (verbatim body of the heredoc run 2026-10-03, exit 0).
NQ 2020 alias: instrument_id 16908, NQU8-NQM9 vs NQM0 roll, COVID window stats.
Read-only; loads only instrument_id, ts_event, raw_symbol, volume columns.
"""
import glob
import pandas as pd

files = sorted(glob.glob('/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/parquet/*/*NQ*.parquet'))
print("NQ files scanned:", len(files))
cols = ['instrument_id', 'ts_event', 'raw_symbol', 'volume']
frames = []
for f in files:
    d = pd.read_parquet(f, columns=cols)
    d = d[d.instrument_id == 16908]
    if len(d):
        frames.append(d)
df = pd.concat(frames, ignore_index=True)
df['ts_event'] = pd.to_datetime(df['ts_event'], unit='ns')
df['date'] = df['ts_event'].dt.date
print("total rows instrument_id 16908:", len(df))
print("date range:", df.date.min(), "..", df.date.max())
print("distinct raw_symbols:", sorted(df.raw_symbol.unique()))

print()
print("--- NQU8-NQM9 alias, 2018-08-15..2020-05-31 ---")
m1 = (df.raw_symbol == 'NQU8-NQM9') & (df.date >= pd.Timestamp('2018-08-15').date()) & (df.date <= pd.Timestamp('2020-05-31').date())
print("bars:", m1.sum())

print("--- NQM0, 2020-06-01..2020-06-19 ---")
m2 = (df.raw_symbol == 'NQM0') & (df.date >= pd.Timestamp('2020-06-01').date()) & (df.date <= pd.Timestamp('2020-06-19').date())
print("bars:", m2.sum())

print("--- window 2020-03-23..2020-05-29 (alias NQU8-NQM9) ---")
w = df[(df.date >= pd.Timestamp('2020-03-23').date()) & (df.date <= pd.Timestamp('2020-05-29').date()) & (df.raw_symbol == 'NQU8-NQM9')]
print("distinct trading dates:", w.date.nunique())
print("total volume:", w.volume.sum())
print("min/max date in window:", w.date.min(), w.date.max())
