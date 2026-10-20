'use strict';
// P0 fix: every book-walk MUST use the CURRENT 1% equity stake computed
// from a fresh equity read under lock — never a hardcoded prior stake.
// Mirrors capital V3: stake = floor(equity_cents / 100) cents (1%, half-up
// via +50 integer round). Equity is re-read from /api/state or ledger.
function currentStakeCents(equityCents) {
  if (typeof equityCents !== 'number' || equityCents < 100) return 0;
  return Math.floor((equityCents + 50) / 100);
}
module.exports = { currentStakeCents };
