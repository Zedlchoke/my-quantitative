# MDP_BRIDGE_NOTES — A8 NautilusTrader bridge (lane notes)

Cycle: MARKET-DATA-PLANE-V1, lane A8. Worktree branch
`orca/market-data-plane-v1-a8-nautilus`.

Freeze authority:
`research/control/market_data_plane_v1_run/architecture_freeze.json`
(sha256 `7f7403e67bfb9707b547b6762cc0a3c87f2c96f701b3f1ec3ad2197478736c02`),
section `nautilus_bridge_contract`, and `plans/PLAN_market_data_plane_v1.md`
section 8. Target: `nautilus_trader==1.230.0` (verified installed in the host
`.venv`). Nothing in this document changes the freeze; it records verified
facts and lane-level semantics that comply with it.

## 1. Mapping table (frozen)

| canonical (`mdp.market_event@1`) | nautilus 1.230.0 | rule |
|---|---|---|
| `event_type = "QUOTE"`, `bid_price`, `ask_price`, `bid_size`, `ask_size` | `QuoteTick` | bid/ask `Price` and sizes `Quantity` built at the **instrument's** `price_precision` / `size_precision` (mandatory argument, no defaults) |
| `event_type = "TRADE"`, `price`, `quantity` | `TradeTick` | price/size via instrument precisions; `side="buy" -> AggressorSide.BUYER`, `side="sell" -> AggressorSide.SELLER`, side absent -> `AggressorSide.NO_AGGRESSOR` |
| `exchange_time_utc_ns` | `ts_event` | exact int UTC nanoseconds, passed through unmodified |
| `available_time_utc_ns` | `ts_init` | exact int UTC nanoseconds, passed through unmodified |
| `event_id` (64-hex sha256) | `TradeId` | deterministic 32-hex-char (128-bit) prefix — nautilus caps `TradeId` at 36 characters (verified), so the full id does not fit; prefix derivation is total and deterministic |
| `instrument_id` | `InstrumentId` | must equal `str(instrument.id)` or the bridge raises (UNKNOWN_INSTRUMENT semantics) |
| canonical decimal STRINGS (`price`, `quantity`, `bid_*`, `ask_*`) | `Price` / `Quantity` | exact `Decimal` arithmetic; drift raises `BridgePrecisionError`, never a silent round (see §3) |
| BAR / OHLCV | — | **NOT mapped in @1**: `BAR_NOT_MAPPED_IN_V1 = "mdp.market_event@1 has no BAR type; OHLCV can never become quotes/depth"`; `to_bar(...)` raises `NotImplementedError` with exactly that message |

There is **no implicit `now()`** anywhere in the bridge; timestamps are never
substituted, and the bridge never reorders (ordering is `replay.py`'s frozen
authority; `convert_stream` preserves caller order exactly).

## 2. Verified nautilus_trader 1.230.0 constructor signatures

All introspected from the installed venv package (`__doc__` C++ signatures)
and exercised by `tests/test_mdp_nautilus_bridge.py`:

```
QuoteTick(InstrumentId instrument_id, Price bid_price, Price ask_price,
          Quantity bid_size, Quantity ask_size,
          uint64_t ts_event, uint64_t ts_init) -> None
    # also raises ValueError if bid.precision != ask.precision

TradeTick(InstrumentId instrument_id, Price price, Quantity size,
          AggressorSide aggressor_side, TradeId trade_id,
          uint64_t ts_event, uint64_t ts_init) -> None
    # also raises ValueError if trade_id is not a valid string (length 1..36)
    # or if size is not positive (> 0)

Price(double value, uint8_t precision) -> None      # int/float/Decimal ok
Quantity(double value, uint8_t precision) -> None   # int/float/Decimal ok
    # precision 0..16; Quantity requires value >= 0
    # a plain str in the first positional slot raises TypeError
    # ("must be real number, not str") — the bridge always passes Decimal
```

* `ts_event` / `ts_init` are `uint64_t` **nanoseconds**: Python `int` is
  accepted and read back unchanged (`tick.ts_event == int`); a negative value
  raises `OverflowError`. The bridge pre-checks non-negativity and
  `ts_init >= ts_event` (`BridgeLookaheadError`).
* `str(Price/Quantity)` renders the fixed-point expansion **padded to the
  construction precision** (`Quantity(Decimal('1.5'), 3) -> '1.500'`); the
  round-trip goldens assert `str(obj) == format(Decimal(event_str),
  '.{precision}f')` for every fixture event.

Test instruments used (from `nautilus_trader.test_kit.providers`, verified):

```
TestInstrumentProvider.btcusdt_perp_binance()  -> CryptoPerpetual
        BTCUSDT-PERP.BINANCE   price_precision=1, size_precision=3
TestInstrumentProvider.default_fx_ccy('EUR/USD') -> CurrencyPair
        EUR/USD.SIM            price_precision=5, size_precision=0
Cfd(InstrumentId, Symbol, AssetClass, Currency,
    int price_precision, int size_precision,
    Price price_increment, Quantity size_increment,
    uint64_t ts_event, uint64_t ts_init, ...)
        with AssetClass.EQUITY -> AAPL.XNAS  price_precision=2, size_precision=1
```

Verified compatibility fact: the nautilus 1.230.0 `Equity` type **hard-pins
`size_precision = 0`** (its constructor has no size-precision/size-increment
parameter and `lot_size` does not influence `size_increment`), so a
2dp-price/1dp-size stock fixture cannot be expressed as an `Equity`. The
stock fixture therefore uses `Cfd(AssetClass.EQUITY)` as its nautilus test
instrument. The bridge is instrument-type agnostic — it reads only
`.id`, `.price_precision`, `.size_precision`.

## 3. Precision semantics (lossless, never a silent round)

nautilus 1.230.0 **silently rounds** decimal values that are not representable
at the requested precision (verified: `Price(Decimal('0.15'), 1)` renders
`0.2`), and routes values through a binary double internally (verified:
`Price(Decimal('123456789.123456789'), 9)` renders `123456789.123456784`).
The bridge therefore:

1. parses the canonical decimal STRING with `Decimal` (never float);
2. pre-checks exact representability at the instrument precision — trailing
   zeros beyond the precision normalize away losslessly (same semantics as
   `models._validated_decimal`), any other excess digit raises
   `BridgePrecisionError`;
3. constructs `Price`/`Quantity` from the normalized `Decimal`;
4. post-verifies `Decimal(str(obj)) == expected` — any internal drift raises
   `BridgePrecisionError`.

No code path in the bridge rounds, coerces through float, or catches a drift
error into a "best effort" value.

## 4. Quality-gate semantics (frozen)

* `quality_status in {INVALID, QUARANTINED}` **raise** `BridgeQualityError`
  (and `convert_stream` fails the call) unless `diagnostic_only=True` is
  explicitly passed.
* With `diagnostic_only=True`, such events are **excluded** from the
  conversion output (the mapper returns `None`; `convert_stream` skips them)
  and recorded in the caller-supplied `BridgeDiagnostics` sidecar as
  `REJECTED_EXCLUDED`. `diagnostic_only=True` **without** a sink raises — an
  exclusion recorded nowhere would be silent, which the freeze forbids.
* `SUSPECT` events **stream** (a tick is returned) and their status is
  recorded in the sidecar as `SUSPECT_STREAMED`. A SUSPECT event without a
  sink raises `BridgeQualityError` (status preservation is mandatory, not
  optional).
* `VALID` events stream; when a sink is supplied they are recorded as
  `CONVERTED`, giving a complete per-event audit trail.
* Sidecar records are immutable `BridgeDiagnostic` entries (event_id,
  instrument_id, event_type, quality_status, reason_codes, action, detail).
  The bridge keeps no hidden/global state; the sink is always caller-owned.

## 5. Input validation and instrument contract

* `instrument` is a required positional argument on `to_quote_tick` /
  `to_trade_tick` (no defaults). `requires_instrument_metadata()` returns the
  contract text. The instrument must expose `.id`, `.price_precision`
  (0..16), `.size_precision` (0..16).
* Every event is revalidated through `models.validate_event` before
  conversion, so only contract-legal `mdp.market_event@1` dicts ever reach
  nautilus, whatever the caller claims.
* The no-lookahead gate (`ts_init >= ts_event`, plus non-negative `uint64`
  ns) runs on the RAW input before revalidation, so a mutated stream hits the
  dedicated `BridgeLookaheadError` even if its stale `event_id` would
  otherwise mask the mutation.
* `event_type` routing is strict: `to_quote_tick` accepts only QUOTE events,
  `to_trade_tick` only TRADE events; `convert_stream` routes by the frozen
  `event_type` field.

## 6. Fixtures — zero data authority

`tests/mdp_bridge_fixtures/` (`crypto_trades`, `forex_quotes`,
`stocks_trades_quotes`) contain **provider-neutral SYNTHETIC** events:
deterministic arithmetic series committed in the modules, hashed into
canonical identity by `models.build_event` itself. They prove code semantics
only and confer **zero data authority** — no event originates from, or may be
cited as evidence about, any real provider, venue, or instrument. Every
fixture event carries exactly the frozen 27 envelope fields and is
constructed+validated through `models.build_event` (contract-legal by
construction); quality labels are post-evaluation states applied via
`models.set_quality` (the streaming set is VALID/SUSPECT only, so "all
fixtures convert" holds; INVALID/QUARANTINED gate cases are derived copies
via `invalid_event()` / `quarantined_event()`).

## 7. Scope statement

No strategy, risk, portfolio, broker, or execution code is introduced by this
lane. The bridge is a pure canonical-event -> nautilus-object mapping with a
fail-closed quality gate; fills, orders, positions, and venues are untouched.
`research/market_data_plane/__init__.py` and all other lanes' modules are
unmodified.

## 8. Known limitations (disclosed, none blocking)

1. nautilus `Price`/`Quantity` route through a binary double internally, so
   huge magnitudes (> ~2^53 scaled at the requested precision) can drift even
   when the decimal fits the instrument precision. The post-construction
   verification turns any such case into a hard `BridgePrecisionError` — it
   can never produce silent drift, but it means such magnitudes are
   unconvertible on nautilus 1.230.0.
2. `TradeId` is the 32-char prefix of `event_id` (nautilus caps 36 chars);
   the mapping is deterministic but not injective in theory (128-bit prefix
   collision), consistent with sha256 identity assumptions.
3. nautilus timestamps are `uint64` ns: pre-1970 (negative) canonical
   timestamps are unconvertible by construction and raise.
4. DEPTH_SNAPSHOT / DEPTH_DELTA are RESERVED in @1 and therefore have no
   bridge mapping; a future `@2` freeze would add them (e.g. to
   `OrderBookDelta`) without changing this module's frozen mappings.

No BLOCKED_COMPATIBILITY items: every freeze rule is satisfiable on
nautilus_trader 1.230.0 as installed.
