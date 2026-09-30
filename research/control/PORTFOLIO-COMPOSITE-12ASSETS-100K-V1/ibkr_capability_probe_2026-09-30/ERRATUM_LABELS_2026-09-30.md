# ERRATUM — IBKR capability labels (2026-09-30)

Owner directive this session: the four spot/metal columns passed a **sample
capability** check only. They did not pass 2021–now coverage. This file
corrects labels. It does not edit the source artifacts.

## Provenance (untouched inputs)

| file | sha256 | bytes |
|---|---|---|
| `PROBE_RESULT.json` | `c90dc665625e6435f565dd02a4f462c6f7e7126a39862bb40b36047df5bf3686` | 45079 |
| `FOLLOWUP_EXPIRED_ROLL.json` | `6ddce3b5a3814133f934b712b65401517b61a6d7f81d1cdc89a42c6ff98a48f0` | 29033 |

Runs `20260930T013229Z` and `20260930T013515Z`. Both files are left byte-identical.
Eligibility, registry, and the GO phrase are not modified.

## Label corrections

| asset | field in PROBE_RESULT | printed | corrected | why |
|---|---|---|---|---|
| NZDUSD USDCHF XAUUSD XAGUSD | `gaps_2021_now` | `PASS` | `NOT_RUN_INTERIOR_GAPS` | Evidence is one `reqHeadTimeStamp` plus 4 daily MIDPOINT bars (`2021-01-14`..`2021-01-19`). No interior scan. |
| NZDUSD USDCHF XAUUSD XAGUSD | `historical_sample` | `PASS` | `PASS` stands | MIDPOINT sample and head timestamp are real. This is sample capability, not coverage. |
| NZDUSD USDCHF XAUUSD XAGUSD | `consider_unlock` | `true` | withdrawn for coverage; **sample review only** | A coverage PASS was an input to that flag. |
| WTI NATGAS | `roll_data` | `PASS` | `FAIL` | `adjustment_method` is `NOT_RETURNED_BY_CONTRACT_DETAILS`. No roll rule, no roll prices. |
| BRENT | `roll_data` | `NOT_RUN` | stays `NOT_RUN` | Venue was ambiguous, so no roll series was requested. |
| WTI NATGAS | `futures_expired_coverage` from the year loop | `FAIL` via code `10372` | superseded | `yyyy` is an invalid month. The yyyyMM follow-up is the coverage evidence. |

`consider_unlock: true` in `PROBE_RESULT.json` is not an eligibility change.
The matrix rows stay blocked.

## CONTFUT is not the tradable chain

`FOLLOWUP_EXPIRED_ROLL.json` shows `secType=CONTFUT` with a single-month
`localSymbol`:

| venue | CONTFUT conId | localSymbol | same conId as the front outright selected in the first probe |
|---|---|---|---|
| CL NYMEX | 304037511 | CLX6 | yes (`CLX6`) |
| NG NYMEX | 269460170 | NGX26 | yes (`NGX26`) |
| COIL IPE | 361002955 | COILZ6 | no (front picked then was `COILX6` 361002948) |
| BZ NYMEX | 339981291 | BZZ6 | no (front picked then was `BZX6` 339981284) |

The tradable chain is the `FUT` listings. A CONTFUT row with a one-month
localSymbol and, for CL and NG, the front conId, is not a certified
back-adjusted roll series. Quarterly `FUT` months `202103`–`202509` returned
error `200`. The oldest quarter that resolved is `202512`.

## Rules frozen before this session's price requests

Daily BID and daily ASK coverage, declared before the bars are read:

- Span PASS only if both sides have a first bar on or before `2021-01-08`,
  a last bar on or after `2026-09-26`, and no consecutive bars more than
  5 calendar days apart.
- Anything short of that is FAIL, with the first hole named.
- Full intraday interior remains `NOT_RUN_INTERIOR_GAPS` unless every
  session is actually scanned. March hourly samples and three M1 days are
  samples, not that scan.

Brent vehicle, chosen on contract identity already in the follow-up, not on
price: ICE Brent outright futures, symbol `COIL`, exchange `IPE`. `BZ` is
"Brent Crude Oil - Last Day", a different contract, and stays the unselected
alternate. `BRN`/`IPE` already returned error `200`. CFD is not a candidate.
If COIL history fails, the script does not switch to BZ.

XAU overlap uses archive
`XAUUSD_1day_full.json` sha256
`49c2684ebb045302acf0c452b5aa9a3b96dff73eb3bc6f5add1801d6817fb33d`
(re-hashed this session, match). Numeric basis-acceptance thresholds in
`td_archive_join_contract.json` are still unfrozen, so a measured overlap
does not pass gate 2. PIT lag is `ASSUMED` (next business day) when no
publish timestamp exists.

No orders. No GO. No registry or eligibility write. Heavy lock is not
acquired for this paced HMDS pull.
