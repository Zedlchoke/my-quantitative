# V8X Equity v1 — SPEC_MAPPING_AMBIGUITY_BLOCKED (addendum, A1-owned)

- `created_at_utc`: 2026-08-26T02:20:00Z
- `author`: A1 controller/integration owner (V8R recovery lineage)
- `artifact`: equity_spec_mapping_addendum
- `frozen_spec_referenced`: `research/hypotheses/H-XSECT-REVERSAL-BREADTH-EQUITY-v1/candidate.yaml`
- `frozen_spec_sha256`: `b8a8d2d9383a2f0c44a35f6e1b2212d7b65f711982452b12ceecb19ddc0c0db9`
- `verdict`: `SPEC_MAPPING_AMBIGUITY_BLOCKED`

## Ambiguity

Frozen equity v1 line 62 declares:

```yaml
formation_lookbacks_sessions: [15, 25, 50]   # ~3D/7D/14D expressed in trading sessions (5 sessions/week); exactly these three
```

The session counts [15, 25, 50] are calendar-session approximations of the
crypto-side 3D/7D/14D formation windows and are NOT time-equivalent
(15 sessions ≈ 21 calendar days ≈ 3W, not 3D; the comment itself says "~").
The frozen V8 crypto trials use exact UTC-day formations. Running equity with
the session approximation would make the "same hypothesis, different venue"
comparison scientifically invalid.

## Disposition

1. The frozen equity v1 file is NOT modified (freeze discipline preserved;
   hash above pins the untouched bytes).
2. No equity scored trial may launch in sprint V8R under this mapping.
3. Combined with the independent data-provider blocker
   (`research/audits/v8x/equity_provider_audit.md` →
   `V8X_EQUITY_NOT_STARTED_PROVIDER_BLOCKED`), equity remains fully
   NOT_STARTED this sprint for two independent reasons.
4. An equity v2 spec with an owner-approved, explicitly-defined session or
   UTC-time formation mapping MAY be created in a FUTURE sprint, before any
   equity score is produced. Owner approval is required because changing the
   mapping changes the hypothesis semantics.

This addendum is audit evidence only. It carries no strategy authority and
does not alter any frozen file.
