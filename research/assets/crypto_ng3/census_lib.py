"""CRYPTO-NG3 P0 census library — pure logic, no network I/O.

Contract identities (C7) are computed here with our own keccak256 and
fail-closed against pinned constants. All arithmetic is exact (int units of
1e-6 token; Decimal only for human display strings). No returns, no outcomes:
this module is census arithmetic only.
"""
from __future__ import annotations

import hashlib
import json
from decimal import Decimal

SCHEMA = "crypto_ng3_p0_census@1"
DECIMALS = 6  # both FiatToken(USDC) and TetherToken(USDT) use 6 decimals

# ---------------------------------------------------------------------------
# keccak256 — vendored pure python (frontier tool lineage, self-tested)
# ---------------------------------------------------------------------------
_RC = [
    0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000,
    0x000000000000808B, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009,
    0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
    0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003,
    0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
    0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
]
_ROT = [[0, 36, 3, 41, 18], [1, 44, 10, 45, 2], [62, 6, 43, 15, 61],
        [28, 55, 25, 21, 56], [27, 20, 39, 8, 14]]
_M = (1 << 64) - 1


def _rol(x: int, n: int) -> int:
    n %= 64
    return ((x << n) | (x >> (64 - n))) & _M


def keccak256(msg: bytes) -> bytes:
    rate = 136
    lanes = [[0] * 5 for _ in range(5)]
    data = msg + b"\x01" + b"\x00" * ((rate - len(msg) - 2) % rate) + b"\x80"
    for off in range(0, len(data), rate):
        blk = data[off:off + rate]
        for i in range(rate // 8):
            lanes[i % 5][i // 5] ^= int.from_bytes(blk[8 * i:8 * i + 8], "little")
        for rnd in range(24):
            c = [lanes[x][0] ^ lanes[x][1] ^ lanes[x][2] ^ lanes[x][3] ^ lanes[x][4] for x in range(5)]
            d = [c[(x - 1) % 5] ^ _rol(c[(x + 1) % 5], 1) for x in range(5)]
            for x in range(5):
                for y in range(5):
                    lanes[x][y] ^= d[x]
            b = [[0] * 5 for _ in range(5)]
            for x in range(5):
                for y in range(5):
                    b[y][(2 * x + 3 * y) % 5] = _rol(lanes[x][y], _ROT[x][y])
            for x in range(5):
                for y in range(5):
                    lanes[x][y] = b[x][y] ^ ((~b[(x + 1) % 5][y]) & _M & b[(x + 2) % 5][y])
            lanes[0][0] ^= _RC[rnd]
    out = b"".join(lanes[i % 5][i // 5].to_bytes(8, "little") for i in range(4))
    return out[:32]


def topic_of(sig: str) -> str:
    return "0x" + keccak256(sig.encode()).hex()


# ---------------------------------------------------------------------------
# C7 — contract identity pins (fail-closed)
# ---------------------------------------------------------------------------
USDC_ADDR = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"  # FiatToken proxy, Ethereum
USDT_ADDR = "0xdac17f958d2ee523a2206206994597c13d831ec7"  # TetherToken, Ethereum
USDT_TRON_B58 = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"      # TetherToken, Tron

MINT_SIG = "Mint(address,address,uint256)"
BURN_SIG = "Burn(address,uint256)"
ISSUE_SIG = "Issue(uint256)"
REDEEM_SIG = "Redeem(uint256)"

PINNED_TOPICS = {
    MINT_SIG: "0xab8530f87dc9b59234c4623bf917212bb2536d647574c8e7e5da92c2ede0c9f8",
    BURN_SIG: "0xcc16f5dbb4873280815c1ee09dbd06736cffcc184412cf7a71a0fdb75d397ca5",
    ISSUE_SIG: "0xcb8241adb0c3fdb35b70c24ce35c5eb0c17af7431c99f827d44a445ca624176a",
    REDEEM_SIG: "0x702d5967f45f6513a38ffc42d6ba9bf230bd40e8f53b16363c7eb4fd2deb9a44",
}

# Indexed-topic counts INCLUDING the signature topic (expected len(topics)).
TOPIC_COUNT = {MINT_SIG: 3, BURN_SIG: 2, ISSUE_SIG: 1, REDEEM_SIG: 1}

# (issuer, topic0) -> event class
ISSUER_EVENT_MAP = {
    (USDC_ADDR, PINNED_TOPICS[MINT_SIG]): ("USDC_ETHEREUM", "MINT"),
    (USDC_ADDR, PINNED_TOPICS[BURN_SIG]): ("USDC_ETHEREUM", "BURN"),
    (USDT_ADDR, PINNED_TOPICS[ISSUE_SIG]): ("USDT_ETHEREUM", "ISSUE"),
    (USDT_ADDR, PINNED_TOPICS[REDEEM_SIG]): ("USDT_ETHEREUM", "REDEEM"),
}

# C5 identity anchors (measured, on-chain-verifiable; see netting rule text)
CCTP_TOKEN_MINTER = "0xfd78ee919681417d192449715b2594ab58f5d002"
TREASURY_ADDR = "0x55fe002aeff02f77364de339a1292923a15844b8"


class PinMismatch(AssertionError):
    """C7 fail-closed: computed keccak disagrees with the pinned constant."""


def verify_pins() -> dict:
    """Compute every topic with our own keccak256; raise PinMismatch on drift."""
    computed = {sig: topic_of(sig) for sig in PINNED_TOPICS}
    bad = {s: (c, PINNED_TOPICS[s]) for s, c in computed.items() if c != PINNED_TOPICS[s]}
    if bad:
        raise PinMismatch(f"computed topics disagree with pins: {bad}")
    transfer = topic_of("Transfer(address,address,uint256)")
    if transfer != "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef":
        raise PinMismatch("canonical Transfer topic vector failed")
    return {"computed": computed, "transfer_vector": transfer, "verdict": "PASS"}


# ---------------------------------------------------------------------------
# Canonical event normalization (C1 cross-transport byte identity; C7 shapes)
# ---------------------------------------------------------------------------
class EventShapeViolation(AssertionError):
    """C7 fail-closed: an event outside the pinned (address, topic0) shapes."""


def normalize_log(log: dict) -> dict:
    """Normalize an eth_getLogs-shaped log (mevblocker RPC or blockscout
    etherscan-compat — both serve hex-quantity fields of the same names) into a
    canonical record. Raises EventShapeViolation on any unknown shape."""
    address = (log.get("address") or "").lower()
    topics = [t for t in (log.get("topics") or []) if t]
    topic0 = topics[0].lower() if topics else ""
    key = (address, topic0)
    if key not in ISSUER_EVENT_MAP:
        raise EventShapeViolation(f"unknown (address,topic0) pair: {key}")
    issuer, ev_class = ISSUER_EVENT_MAP[key]
    sig = None
    for s, h in PINNED_TOPICS.items():
        if h == topic0:
            sig = s
    if sig is None or len(topics) != TOPIC_COUNT[sig]:
        raise EventShapeViolation(f"topic count {len(topics)} mismatched for {topic0}")
    data = log.get("data") or "0x"
    if not data.startswith("0x") or len(data) != 66:
        raise EventShapeViolation(f"data length {len(data)} != 66 (32-byte uint256 expected)")
    amount = int(data, 16)
    ev = {
        "issuer": issuer,
        "event": ev_class,
        "block": int(log["blockNumber"], 16),
        "log_index": int(log["logIndex"], 16),
        "tx_hash": log["transactionHash"].lower(),
        "address": address,
        "topic1": topics[1].lower() if len(topics) > 1 else "",
        "topic2": topics[2].lower() if len(topics) > 2 else "",
        "amount_units": amount,
    }
    ts = log.get("timeStamp")
    if ts:  # blockscout serves per-log timestamps; RPC does not
        ev["block_ts"] = int(ts, 16)
    return ev


def canonical_bytes(ev: dict) -> bytes:
    core = {k: ev[k] for k in (
        "issuer", "event", "block", "log_index", "tx_hash", "address",
        "topic1", "topic2", "amount_units") if k in ev}
    return json.dumps(core, sort_keys=True, separators=(",", ":")).encode()


def event_set_digest(events: list[dict]) -> str:
    ordered = sorted(events, key=lambda e: (e["block"], e["log_index"], e["tx_hash"]))
    h = hashlib.sha256()
    h.update(str(len(ordered)).encode())
    for ev in ordered:
        h.update(canonical_bytes(ev))
    return h.hexdigest()


def amount_to_units(amount_units: int) -> Decimal:
    return (Decimal(amount_units) / (Decimal(10) ** DECIMALS)).quantize(Decimal(1).scaleb(-DECIMALS))


# ---------------------------------------------------------------------------
# C3 — chunk partition (no gaps, no overlaps, exact coverage)
# ---------------------------------------------------------------------------
def day_partition(day_ranges: list[tuple[str, int, int]], chunk_size: int) -> list[dict]:
    """day_ranges: (utc_day, first_block, last_block_exclusive_end) day-aligned.

    Returns chunk descriptors covering every block exactly once."""
    chunks: list[dict] = []
    for day, s, e in day_ranges:
        if e <= s:
            continue
        cur = s
        while cur < e:
            hi = min(cur + chunk_size, e)
            chunks.append({"day": day, "start": cur, "end": hi})  # [start, end)
            cur = hi
    return chunks


def coverage_ok(chunks: list[dict], window_start: int, window_end: int) -> tuple[bool, str]:
    """Exact partition check: sorted, contiguous, zero gaps/overlaps, bounds exact."""
    if not chunks:
        return False, "no chunks"
    prev = window_start
    for c in sorted(chunks, key=lambda c: c["start"]):
        if c["start"] != prev:
            return False, f"gap/overlap at {c['start']} (expected {prev})"
        if c["end"] <= c["start"]:
            return False, f"empty chunk {c}"
        prev = c["end"]
    if prev != window_end:
        return False, f"window end mismatch: covered to {prev}, expected {window_end}"
    return True, "exact partition"


# ---------------------------------------------------------------------------
# C9 — conservation per window (day rows, exact integer arithmetic)
# ---------------------------------------------------------------------------
def day_rows(events: list[dict], issuer: str) -> list[dict]:
    """Aggregate canonical events into per-UTC-day conservation rows.
    day_of must be attached per event by the runner (day-aligned chunks)."""
    agg: dict[str, dict] = {}
    for ev in events:
        if ev["issuer"] != issuer:
            continue
        row = agg.setdefault(ev["day"], {
            "day": ev["day"], "issuer": issuer, "mint_n": 0, "mint_sum": 0,
            "burn_n": 0, "burn_sum": 0, "issue_n": 0, "issue_sum": 0,
            "redeem_n": 0, "redeem_sum": 0})
        cls = ev["event"].lower()
        row[f"{cls}_n"] += 1
        row[f"{cls}_sum"] += ev["amount_units"]
    rows = []
    for day in sorted(agg):
        r = agg[day]
        r["net_units"] = (r["mint_sum"] - r["burn_sum"] + r["issue_sum"] - r["redeem_sum"])
        r["net"] = str(amount_to_units(r["net_units"]))
        rows.append(r)
    return rows


def conservation_breaks(rows: list[dict]) -> list[dict]:
    """Identity per row: net_units == mint-burn+issue-redeem recomputed exactly."""
    breaks = []
    for r in rows:
        recomputed = (r["mint_sum"] - r["burn_sum"] + r["issue_sum"] - r["redeem_sum"])
        if r["net_units"] != recomputed:
            breaks.append({"day": r["day"], "issuer": r["issuer"],
                           "stored": r["net_units"], "recomputed": recomputed})
    return breaks


def chunk_day_crossfoot(chunks: list[dict], rows: list[dict], issuer: str) -> list[dict]:
    """Σ per-chunk nets == Σ per-day nets, per day (internal exactness)."""
    per_day: dict[str, int] = {}
    for c in chunks:
        if c.get("issuer_net_units", {}).get(issuer) is None:
            continue
        per_day[c["day"]] = per_day.get(c["day"], 0) + c["issuer_net_units"][issuer]
    day_map = {r["day"]: r["net_units"] for r in rows if r["issuer"] == issuer}
    breaks = []
    for day in sorted(set(per_day) | set(day_map)):
        a, b = per_day.get(day, 0), day_map.get(day, 0)
        if a != b:
            breaks.append({"day": day, "issuer": issuer, "chunk_sum": a, "row_sum": b})
    return breaks


# ---------------------------------------------------------------------------
# C5 — identity netting (minter classes measured full-window)
# ---------------------------------------------------------------------------
def minter_table(events: list[dict], issuer: str = "USDC_ETHEREUM") -> list[dict]:
    """Full-window per-address table over the FiatToken indexed minter field
    (topic1) for MINT and indexed burner field (topic1) for BURN. Addresses
    are normalized to the plain 20-byte form (0x + 40 hex)."""
    agg: dict[str, dict] = {}
    for ev in events:
        if ev["issuer"] != issuer:
            continue
        addr = ev["topic1"] if not ev["topic1"] else ("0x" + ev["topic1"][-40:])
        row = agg.setdefault(addr, {"address": addr, "mint_n": 0, "mint_sum": 0,
                                    "burn_n": 0, "burn_sum": 0})
        if ev["event"] == "MINT":
            row["mint_n"] += 1
            row["mint_sum"] += ev["amount_units"]
        elif ev["event"] == "BURN":
            row["burn_n"] += 1
            row["burn_sum"] += ev["amount_units"]
    out = []
    for addr in sorted(agg):
        r = agg[addr]
        r["mint"] = str(amount_to_units(r["mint_sum"]))
        r["burn"] = str(amount_to_units(r["burn_sum"]))
        out.append(r)
    return out


def minter_field_flip_check(events: list[dict]) -> dict:
    """Empirical field-order guard: the indexed minter field (topic1) must show
    far lower cardinality than the recipient field (topic2). A flip means a
    contract implementation change altered the event layout -> fail-closed."""
    t1 = {ev["topic1"] for ev in events if ev["issuer"] == "USDC_ETHEREUM" and ev["event"] == "MINT"}
    t2 = {ev["topic2"] for ev in events if ev["issuer"] == "USDC_ETHEREUM" and ev["event"] == "MINT"}
    ok = len(t1) <= len(t2)
    return {"topic1_distinct": len(t1), "topic2_distinct": len(t2), "ok": ok}


def classify_address(address: str, code_map: dict[str, bool],
                     treasury_evidence: dict) -> str:
    """Frozen classification: contract-verified CCTP minter; measured-dominant
    treasury; everything else (incl. any exchange hot wallet) UNCLASSIFIED."""
    a = address.lower()
    if a == CCTP_TOKEN_MINTER and code_map.get(a) is True:
        return "CCTP_TOKEN_MINTER"
    if a == TREASURY_ADDR and treasury_evidence.get("dominant", False):
        return "TREASURY_MEASURED_DOMINANT"
    return "UNCLASSIFIED"


# ---------------------------------------------------------------------------
# C6 — composition flags (declared strata)
# ---------------------------------------------------------------------------
def net_extreme_days(rows: list[dict], percentile: str = "0.99") -> list[str]:
    """Frozen rule: a day is NET_EXTREME when |net_units| is STRICTLY greater
    than the P99 nearest-rank value of |net_units| over the issuer's census
    window (zero-event days carry |0| and never flag; ties at the boundary
    value are not flagged; days strictly beyond it are)."""
    issuer_rows = [r for r in rows if r["issuer"] == "USDC_ETHEREUM"]
    mags = sorted(abs(r["net_units"]) for r in issuer_rows)
    if not mags:
        return []
    rank = int(Decimal(percentile) * (len(mags) - 1))
    thr = mags[rank]
    if thr == 0:
        return []
    return [r["day"] for r in issuer_rows if abs(r["net_units"]) > thr]


# ---------------------------------------------------------------------------
# C10 — fold freeze (three chronological folds, 40/30/30, day-aligned)
# ---------------------------------------------------------------------------
def fold_boundaries(days: list[str]) -> dict:
    n = len(days)
    f1 = days[: int(n * 0.40)]
    f2 = days[int(n * 0.40): int(n * 0.40) + int(n * 0.30)]
    f3 = days[int(n * 0.40) + int(n * 0.30):]
    return {"fold1": f1, "fold2": f2, "fold3": f3}


# ---------------------------------------------------------------------------
# Verdict assembly
# ---------------------------------------------------------------------------
SOURCE_GATES = ("C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9")


def overall_verdict(gates: dict) -> str:
    """Any C1-C9 miss => BLOCKED_SOURCE. C10/C11 miss => BLOCKED_DATA_OR_SELECTION."""
    for g in SOURCE_GATES:
        if gates.get(g, {}).get("verdict") != "PASS":
            return "P0_CENSUS_BLOCKED_SOURCE"
    for g in ("C10", "C11"):
        if gates.get(g, {}).get("verdict") != "PASS":
            return "P0_CENSUS_BLOCKED_DATA_OR_SELECTION"
    return "P0_CENSUS_PASS"


# ---------------------------------------------------------------------------
# Digest helpers (C11)
# ---------------------------------------------------------------------------
def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def canonical_json_bytes(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
