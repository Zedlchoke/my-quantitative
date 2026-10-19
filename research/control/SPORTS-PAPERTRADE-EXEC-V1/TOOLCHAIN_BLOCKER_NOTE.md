# TOOLCHAIN BLOCKER NOTE — SwiftUI attempt abandoned (2026-10-19)

## What happened

The first PaperDesk implementation was native SwiftUI (swiftc, macOS 13+
target). Compilation fails on this machine even for a trivial
`import SwiftUI` file:

```
/Library/Developer/CommandLineTools/usr/include/swift/module.modulemap:13:8:
error: redefinition of module 'SwiftBridging'
note: previously defined here
/Library/Developer/CommandLineTools/usr/include/swift/bridging.modulemap:13:8
```

## Root cause (measured)

This Mac has Command Line Tools only (no full Xcode; `xcode-select -p` →
`/Library/Developer/CommandLineTools`). The CLT Swift 6.1.2 install contains
TWO conflicting modulemaps in the same directory, both defining
`module SwiftBridging { header "bridging" }`:
- `usr/include/swift/module.modulemap` (header dated 2023 — stale leftover)
- `usr/include/swift/bridging.modulemap` (2024)

The ClangImporter loads both → redefinition error. Workarounds tried:
- `xcrun --sdk macosx swiftc ...` — same error
- VFS overlay (`-Xcc -ivfsoverlay`) masking the stale map — overlay not
  honored on the importer's include of these maps

Rejected: editing/deleting Apple's system modulemap files (system-state
mutation beyond this cycle's scope).

## Decision

Per the owner instruction ("Chọn SwiftUI/Tauri/Electron dựa trên repo và môi
trường thực tế"), the stack pivoted to **Electron** (node v24 + npm healthy,
prebuilt binaries, no Swift toolchain involvement). The architecture is
unchanged — all seams, laws, and batteries carry over; see
AMENDMENT_MACOS_APP_UI_V1 §5 (tech note) and apps/paperdesk/.

## What was ported 1:1 from the Swift design

LedgerStore (typed JSON parse + canonical hash byte-exact vs the pinned
Python), RunnerController (attach/spawn/SIGTERM/pause-flag/launchd bootout),
HealthStore (GET-only /api/state), MarketDataProvider (PM read-only + raw
journal), AIReviewEngine (SHADOW, fail-closed, Keychain), LiveExecution seal,
quit law, window-close policy, single-instance guards.
