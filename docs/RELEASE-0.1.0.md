# TRUE ENGINE 0.1.0 delivery record

Status: initial implementation; Windows runtime qualification pending. No future phase is approved or included.

Changes: all source files are additions to the previously empty checkout. Exact changed paths and per-file SHA-256 are in the source ZIP's `source-manifest.json`. Executable package manifests list replaced application files and their payload SHA-256. Each outer ZIP has a SHA-256 sidecar. Do not equate a local archive with installation on the requested Windows B: drive.

Tests actually run: see docs/VALIDATION.md. Those results distinguish Linux execution, offscreen GPU readback, native input simulation, target compilation, synthetic updater tests, and unrun Windows/macOS/browser runtime checks.

Compatibility: SDK 0.1; schema 1; all core APIs are application-agnostic. No previous released API/schema exists to migrate. Future backward-incompatible changes require owner approval. Schema versions other than 1 are rejected without automatic rewrite. Migration behavior: none; updater preserves Data and replaces only Current after verification. Backups are retained and may be restored using Rollback.cmd. Close the viewport before installing or rolling back.

To deploy a supplied Windows kit, extract it under `B:\True Engine` on Windows, retaining existing Data and Backups. Authenticate the kit's SHA-256 using a trusted copy of the delivery digest, then run Update.cmd with the enclosed Build ZIP and its trusted SHA-256. Launch.cmd sets the working directory to Data. Python 3.10+ is required. Test the Windows viewport, batch wrappers, update and rollback on that machine before treating the release as Windows-qualified. Windows package builds can also be reproduced with tools/windows-release.ps1 using Rust/MSVC; the cloud cross-build uses Rust's Windows gnullvm target and verified LLVM-MinGW.
