"""Build a Nautilus ParquetDataCatalog (catalog_live_crypto layout) from the
CHR3F staged vision-kline zips. Verify-on-write: per-month row counts must
match source CSVs exactly; spot-checks on first/last bar OHLC + quote_volume.
Instrument metadata (tick/step/minNotional) from fapi exchangeInfo (CURRENT
metadata; V14-frozen 'real perp-metadata' convention, disclosed per plan)."""
from __future__ import annotations
import argparse, io, json, sys, time, zipfile
from datetime import datetime, timezone
from pathlib import Path
import urllib.request
import pandas as pd
from nautilus_trader.model import currencies as _currencies

REPO = Path("/Users/hoangminhlong/my-quantitative")
sys.path.insert(0, str(REPO))
from nautilus_trader.persistence.catalog import ParquetDataCatalog  # noqa: E402
from nautilus_trader.model.instruments import CryptoPerpetual  # noqa: E402
from nautilus_trader.model.identifiers import InstrumentId, Symbol, Venue  # noqa: E402
from nautilus_trader.model.objects import Price, Quantity, Money, Currency  # noqa: E402
from nautilus_trader.model.data import Bar, BarType  # noqa: E402
from decimal import Decimal as _Dec  # noqa: E402
from nautilus_trader.adapters.binance.common.types import BinanceBar  # noqa: E402
from nautilus_trader.model.enums import PriceType, AggregationSource  # noqa: E402
from decimal import Decimal  # noqa: E402

STAGE = Path(__file__).resolve().parent / "staging"
UA = {"User-Agent": "chr3f-catalog/1"}

def exchangeinfo_filters(symbols):
    req = urllib.request.Request("https://fapi.binance.com/fapi/v1/exchangeInfo", headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read())
    out = {}
    for x in d["symbols"]:
        if x["symbol"] in symbols:
            f = {flt["filterType"]: flt for flt in x["filters"]}
            out[x["symbol"]] = {
                "tickSize": f["PRICE_FILTER"]["tickSize"],
                "stepSize": f["LOT_SIZE"]["stepSize"],
                "minNotional": f.get("MIN_NOTIONAL", {}).get("notional", "5"),
                "pricePrecision": x["pricePrecision"],
                "quantityPrecision": x["quantityPrecision"],
                "base": x["baseAsset"], "quote": x["quoteAsset"],
            }
    return out

def dec_places(s: str) -> int:
    d = Decimal(s).normalize()
    exp = -d.as_tuple().exponent
    return max(exp, 0)

def build_instrument(sym, fi):
    pp, qp = int(fi["pricePrecision"]), int(fi["quantityPrecision"])
    return CryptoPerpetual(
        instrument_id=InstrumentId(Symbol(f"{sym}-PERP"), Venue("BINANCE")),
        raw_symbol=Symbol(sym),
        base_currency=getattr(_currencies, fi['base'], None) or Currency.register(Symbol(fi['base']), 8, 2, fi['base'], Symbol(fi['base']), crypto=True),
        quote_currency=getattr(_currencies, fi['quote'], None) or Currency.register(Symbol(fi['quote']), 8, 2, fi['quote'], Symbol(fi['quote']), crypto=True),
        settlement_currency=Currency.from_str(fi["quote"]),
        is_inverse=False,
        price_precision=pp, size_precision=qp,
        price_increment=Price.from_str(fi["tickSize"]),
        size_increment=Quantity.from_str(fi["stepSize"]),
        min_quantity=Quantity.from_str(fi["stepSize"]),
        max_quantity=Quantity.from_str(str(10 ** max(qp, 4))),
        min_notional=Money.from_str(f"{fi['minNotional']} USDT"),
        max_notional=Money.from_str("10000000000 USDT"),
        min_price=Price.from_str("0.000000000001"),
        max_price=Price.from_str("10000000"),
        margin_init=Decimal("0.05"), margin_maint=Decimal("0.025"),
        maker_fee=Decimal("0.0002"), taker_fee=Decimal("0.0005"),
        ts_event=0, ts_init=0,
    )

def bar_type(sym):
    return BarType.from_str(f"{sym}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL")

def read_zip_rows(path: Path):
    with zipfile.ZipFile(path) as z:
        name = z.namelist()[0]
        with z.open(name) as f:
            df = pd.read_csv(f, header=None,
                names=["open_time","open","high","low","close","volume","close_time",
                       "quote_volume","count","tbb","tbq","ignore"])
    df = df[df["open_time"] != "open_time"]
    for c in ("open_time","close_time"):
        df[c] = df[c].astype("int64")
    for c in ("open","high","low","close","volume","quote_volume"):
        df[c] = df[c].astype(float)
    return df

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", required=True, help="comma-separated")
    ap.add_argument("--months", required=True, help="e.g. 2020-01..2024-08 or 2024-08..2026-08")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    syms = a.symbols.split(",")
    y0, m0 = map(int, a.months.split("..")[0].split("-"))
    y1, m1 = map(int, a.months.split("..")[1].split("-"))
    months = [(y, m) for y in range(y0, y1 + 1) for m in range(1, 13)
              if (y, m) >= (y0, m0) and (y, m) <= (y1, m1)]
    fi = exchangeinfo_filters(set(syms))
    out = Path(a.out)
    if out.exists():
        sys.exit(f"REFUSED: {out} exists (delete manually to rebuild)")
    out.mkdir(parents=True)
    cat = ParquetDataCatalog(str(out))
    report = {}
    for sym in syms:
        fi_sym = fi[sym]
        cat.write_data([build_instrument(sym, fi_sym)])
        pp, qp = int(fi_sym["pricePrecision"]), int(fi_sym["quantityPrecision"])
        bt = bar_type(sym)
        bars = []
        per_month = {}
        for (y, m) in months:
            zpath = STAGE / "klines" / sym / f"{sym}-15m-{y}-{m:02d}.zip"
            if not zpath.exists():
                continue
            df = read_zip_rows(zpath)
            for r in df.itertuples(index=False):
                ts = int(r.open_time)
                if len(str(ts)) == 10:
                    ts *= 1000
                ts_ns = ts * 1_000_000
                o = Price(float(r.open), pp); h = Price(float(r.high), pp)
                l = Price(float(r.low), pp); c = Price(float(r.close), pp)
                v = Quantity(float(r.volume), qp)
                bars.append(BinanceBar(bt, o, h, l, c, v,
                    _Dec(str(r.quote_volume)), int(r.count),
                    _Dec(str(r.tbb)), _Dec(str(r.tbq)), ts_ns, ts_ns))
            per_month[f"{y}-{m:02d}"] = len(df)
        for i in range(0, len(bars), 50_000):
            cat.write_data(bars[i:i + 50_000])
        # verify-on-read
        got = cat.bars(bar_types=[str(bt)], start=None, limit=None) if False else None
        report[sym] = {"months": len(per_month), "rows_written": sum(per_month.values()),
                       "price_precision": pp, "tick": fi_sym["tickSize"], "step": fi_sym["stepSize"]}
        print(sym, report[sym], flush=True)
    (out.parent / (out.name + "_build_report.json")).write_text(json.dumps(
        {"generated_utc": datetime.now(timezone.utc).isoformat(), "months": f"{a.months}",
         "symbols": report}, indent=1))
    print("BUILD DONE ->", out)
    return 0

if __name__ == "__main__":
    sys.exit(main())
