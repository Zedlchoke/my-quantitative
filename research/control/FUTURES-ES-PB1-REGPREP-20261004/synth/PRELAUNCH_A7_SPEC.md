# PRELAUNCH_A7_SPEC — FUTURES-ES-PB1-V1 key 1 of 2 (program, pre-staged)

Runs ONLY after registration. Independent fresh-context auditor; writes
audit artifacts only; repairs nothing; 0 PnL by construction.

1. Freeze integrity: re-hash all 34 pins (freeze/freeze_pins_v2.json — AUTHORITATIVE per freeze/PIN_SUPERSESSION.md) at the
   registered freeze; drift vs REGISTRATION_PACKET §1 ⇒ BLOCKED.
2. Identity enumeration: re-transcribe the 24 identities from the frozen
   table; byte-exact match vs freeze/identity_table_24.json; count = 24;
   composition P-A 8 + P-B 8 + FOMC 4 + C1-C4 4.
3. Cost arithmetic: recompute the Variant-A table from components
   (0.85+1.38+0.02 = 2.25; +6.25 spread +12.50/25.00/37.50 slippage ⇒
   21.00/33.50/46.00; RT 42/67/92; window 20.99/33.49/45.99); match vs
   the pinned cost contract; labels MODELED COST /
   VERIFIED_VS_ACCOUNT=NOT_RUN enforced; forbidden values
   (1.386/21.006/33.506/46.006) use-as-value scan = zero.
4. PIT/exclude coverage: FOMC 132-day exclude; BLS vintage + D5 pin;
   holiday fail-closed; RTH-core <60%; roll/expiry laws — each verified
   against its pinned artifact (freeze/pit_exclude_set.json).
5. Budget accounting: 24 identities = registered budget; zero
   unregistered cells.
6. Language scan: no expectancy/positive-PnL/"measured cost" claims in
   the frozen set.
Verdict: AUTHORIZED or AUTHORIZED_WITH_FINDINGS with 0 HIGH/CRITICAL
unresolved (findings discharged); else BLOCKED back to freeze.

— End PRELAUNCH_A7_SPEC.
