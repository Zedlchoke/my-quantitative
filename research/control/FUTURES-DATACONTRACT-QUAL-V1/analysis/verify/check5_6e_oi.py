"""Check 5 evidence script (verbatim body of the heredoc run 2026-10-03, exit 0).
6E venue-OI dedupe probe: GLBX statistics stat_type==9, ts_ref date 2024-06-04.
Dedupe = keep latest publication (max ts_event) per (contract, ref_date), then sum.
Schema discovered on the fly: instrument_id, raw_symbol, ts_event, ts_ref,
stat_type, stat_flags, price, quantity, update_action (no venue/channel column).
"""
import pandas as pd

files = [
    '/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/parquet/AV1T-statistics-ALL10/AV1T-statistics-ALL10__2024-04-01_2024-06-01.parquet',
    '/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/parquet/AV1T-statistics-ALL10/AV1T-statistics-ALL10__2024-06-01_2024-08-01.parquet',
]
frames = []
for f in files:
    d = pd.read_parquet(f)
    d = d[(d.stat_type == 9) & (d.raw_symbol.str.startswith('6E'))]
    frames.append(d)
    print(f.split('/')[-1], '-> 6E stat9 rows:', len(d))
df = pd.concat(frames, ignore_index=True)
df['ref_date'] = pd.to_datetime(df.ts_ref, unit='ns').dt.date
df['pub_ts'] = pd.to_datetime(df.ts_event, unit='ns')
w = df[df.ref_date == pd.Timestamp('2024-06-04').date()].copy()
print()
print('rows with ts_ref date == 2024-06-04:', len(w))
print('distinct raw_symbols (contracts):', sorted(w.raw_symbol.unique()))
print('update_action counts:', w.update_action.value_counts().to_dict())
print('stat_flags counts:', w.stat_flags.value_counts().to_dict())
print('publication timestamps (pub_ts) distinct count:', w.pub_ts.nunique())
print()
print('RAW sum (all rows, no dedupe):', w.quantity.sum())
latest_pub = w.groupby('raw_symbol')['pub_ts'].max()
sel = w.apply(lambda r: r.pub_ts == latest_pub[r.raw_symbol], axis=1)
dd = w[sel]
print('dedup rows:', len(dd), 'raw_symbol count:', dd.raw_symbol.nunique())
print('DEDUP sum (latest publication per contract):', dd.quantity.sum())
print()
print('per-contract breakdown (dedup):')
print(dd[['raw_symbol', 'pub_ts', 'quantity']].sort_values('raw_symbol').to_string())
