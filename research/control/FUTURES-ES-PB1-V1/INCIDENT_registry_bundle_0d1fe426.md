# INCIDENT RECORD — registry reconcile commit 0d1fe426 bundled foreign NFL changes (append-only)

- What happened: at the EXEC-BUILD registry reconcile (2026-10-05), ROOT
  had 3 uncommitted control-plane files containing the owner's in-flight
  **NFL-WINPROB-NG-SCORED-V1 registration** (new cycle row + events +
  projection). The controller's pre-update cleanliness check printed the
  count (3) but the update ran anyway (check-then-act failure), so
  commit `0d1fe426` ("registry reconcile: head -> EXEC-BUILD SHA")
  contains BOTH the ES head update AND the owner's NFL registration
  content (115 insertions vs the usual ~9 for a pure reconcile).
- Violation: the dispatch law "không bundle thay đổi cycle khác / foreign
  files" was breached by the controller's check-then-act gap.
- Why not rewritten: history rewrite is forbidden (AGENTS.md). Reverting
  would either destroy the owner's NFL registration from the registry or
  misattribute more churn. The NFL row content is byte-exact the owner's
  intended state (only the commit attribution/message is mixed).
- Content audit (recorded here): the diff of 0d1fe426 = ES row head
  609d7ac9→999ece60 + metadata (intended) + NFL-WINPROB-NG-SCORED-V1 new
  row (owner's; ACTIVE_LIGHT, 0/9, STOP-before-GO phase per their
  workflow) + their events + projection regeneration (which
  automatically includes any non-terminal row present in the file).
- Process fix (binding on this controller thread): the pre-reconcile
  gate now HARD-STOPS on any non-zero dirty count at ROOT — no update
  until the owner's tree is verifiably clean; the count is asserted, not
  just printed.
- Impact on FUTURES-ES-PB1-V1: none functionally (our row's fields are
  exactly as intended; verify still checks them at the final SHA).

— End incident record.

## CORRECTION (append-only, per verifier F-1 MEDIUM, 2026-10-05)

The content audit above UNDER-REPORTED the foreign additions. Commit
`0d1fe426` bundled **TWO** foreign registrations from the owner's
in-flight tree, not one: (1) NFL-WINPROB-NG-SCORED-V1 (as recorded
above) AND (2) WINPROB-PLAYERFEAT-PREP-V1 (no GO phrase), each with
their events + projection entries; both rows are absent from the parent
registry commit. The controller's audit sampled only the first foreign
hit found in the diff. ES row content remains exactly as intended; no
machinery impact. Process fix unchanged (hard-stop pre-reconcile gate).
Additionally disclosed in the same wave: the verifier initially wrote
its outputs under ROOT research/control/FUTURES-ES-PB1-V1/verify/exec/
(boundary error — root is owner space); the controller relocated those
two files into THIS worktree path verbatim and removed the root
directory; root tree verified clean after relocation.
