# Decide the crowding and native-funding feature contract

**Type:** research  
**Status:** open  
**Blocked by:** none

## Question

Which price/OI/funding/basis features are legitimate state variables, and how do
they change entries, risk or only post-trade reporting?

## Decision needed

Separate descriptive filters from predictive signals. Decide lookback windows,
percentile normalization, missing-data behavior, and whether funding is allowed
to alter sizing before native settlement parity is proven.

## Evidence to collect

- Feature availability and timestamp alignment by symbol.
- Conditional outcomes for price up/down × OI up/down × funding sign.
- Leakage tests: no future funding, liquidation or close data in an entry feature.
