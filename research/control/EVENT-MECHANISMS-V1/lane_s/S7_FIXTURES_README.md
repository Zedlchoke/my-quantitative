# S7 FIXTURES — timezone/DST/session sequencing (lane S, for engine lane)

Three hand-written fixtures pin the R2-4 timezone law + G3 A1 sequencing
BEFORE any engine run. Each fixture states acceptance_utc and the expected
stratum/session decisions; the engine must reproduce them from code, not
from this document.

| Fixture | acceptance_utc | ET reading | stratum | sequencing under test |
|---|---|---|---|---|
| `fixture_a_after_close.json` | 2024-06-10T22:30:00.000Z (Mon, EDT) | 18:30 -04:00 | **S3** [16:00,20:00) | direction = NEXT session (06-11); entry = 06-12 open; exit = 06-18 close (H=5) |
| `fixture_b_pre_open.json` | 2024-06-10T11:00:00.000Z (Mon, EDT) | 07:00 -04:00 | **S1** [00:00,09:30) | direction = SAME-date session (06-10); entry = 06-11 open; exit = 06-17 close (H=5) |
| `fixture_c_dst_fall_back.json` | 2025-11-02T22:30:00.000Z (Sun, fall-back day) | 17:30 **-05:00** | **S3** + weekend bucket | weekend acceptance must NOT collapse into a weekday stratum; direction = Monday 11-03; entry = 11-04 |

Key DST assertion (fixture c): 22:30Z must map to UTC-5 (EST) after the
2025-11-02 fall-back; a fixed UTC-4 implementation would read 21:30Z-style
stamps wrong — the fixture pins the OFFSET, not just the bucket. (Both
21:30Z and 22:30Z land in [16:00,20:00) that day, so the stratum alone does
not detect a DST bug; the et_offset_hours field does.)

Anchor rule reminder (G3): A1 direction = sign of RAW (close−open) of the
direction session; entry = NEXT session open; H=5 sessions; exit close.
Sessions are bar dates of the name (weekend/holiday acceptances resolve to
the next bar date).
