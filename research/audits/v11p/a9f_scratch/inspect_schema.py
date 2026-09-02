import pyarrow.parquet as pq
import glob, os

for name in ["binance_bar/BTCUSDT-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL",
             "crypto_perpetual/BTCUSDT-PERP.BINANCE"]:
    p = glob.glob(f"/Users/hoangminhlong/my-quantitative/catalog_live_crypto/data/{name}/*.parquet")[0]
    f = pq.ParquetFile(p)
    print("=====", name)
    print(f.schema_arrow)
    t = f.read()
    df = t.to_pandas()
    print("rows:", len(df))
    print(df.head(3).to_string())
    print(df.tail(3).to_string())
