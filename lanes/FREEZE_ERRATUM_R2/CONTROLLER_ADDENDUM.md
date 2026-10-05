# ERRATUM_R2 CONTROLLER ADDENDUM (INV_C2 disclosure + recorder freeze, two-step)

RECORDER_FREEZE_SHA = 3e52b7b1de64c8e2f04867cee37524886c6b3111
Measured at: 2026-10-05T14:07:40Z by the cycle controller after committing lanes/PIPE + lanes/INV_C2.

## INV_C2 disclosure (controller-written, binds the prospective phase)
The 'time-shuffled twin beats its reference => candidate UN-SCORED' rule is UNSAFE when the reference
is miscalibrated (measured: any spread-adding arm 'wins' vs an underconfident B1*, slope 1.605;
pure logit rescaling x1.5 scores -0.0054). Adjudication guidance for ALL prospective-phase twin reads:
compare the twin BOTH vs the reference AND vs its own parent arm; MACHINERY_SUSPECT fires only when
the twin beats its OWN PARENT with parent slope inside [0.85,1.15]. This clarifies diagnostic
language only — gates T1-T3/R1-R3, arms, windows and grids are UNCHANGED. C2 stays OUT (three
independent kill grounds). C3's train-internal ADMIT stands (twin code-independent, clean).

## Freeze supersession
GENESIS_PAYLOAD_DIGEST_R2 = bd94eb77... (per lanes/FREEZE_ERRATUM_R2); R1 digest ae99a803... superseded.
CODE_FREEZE_SHA 7ec4c539... (arm code) unchanged; recorder modules frozen at this SHA (3e52b7b1de64c8e2f04867cee37524886c6b3111).
