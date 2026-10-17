# Changelog

## 0.1.3 — embeddable browser SDK

- Added a compiled, versioned browser ESM/WASM SDK over the existing renderer, with host-owned canvases, indexed meshes, material/transform/camera operations, picking, serialization and explicit disposal.
- Added validated external-mesh Rust APIs without changing existing signatures or native schema 1. Browser mesh/camera documents use a separate versioned envelope; no automatic migration.
- Added real GPU/browser example tests, API declaration checks, integrity-gated deterministic SDK packaging, Windows build instructions and Linux/Windows release checks.
- Documented the actual Plate Studio asset/server integration requirements without changing its repository. See docs/RELEASE-0.1.3.md and docs/SDK_VALIDATION-0.1.3.md for actual evidence and limitations.


## 0.1.0 — initial implementation, unreleased

Added application-agnostic scene/camera/geometry/project/render modules; native and browser viewport entry points; SDK contract; automated scene and rendered-pixel tests; Windows ZIP packaging and integrity-checked staged updater with backups/rollback.

Compatibility: SDK 0.1 and project schema 1. Migration: none; unsupported schemas are rejected. Platform runtime verification is tracked in docs/VALIDATION.md. No Windows binary release has been qualified. Future phases require approval.

### 0.1.0 distribution revision 2 — Windows first-time test kit

Reuses the existing optimized Windows EXE unchanged. Adds a directly runnable portable layout, `START APPLICATION.bat`, an optional side-by-side B-drive installer, dependency/integrity checks, isolated test data, prelaunch project backup, launch logs, and `README - FIRST TIME SETUP.txt`. No Rust or Python runtime is needed to launch this kit. Earlier ZIPs and working versions are preserved. SDK 0.1/schema 1, no migration or breaking engine changes. Windows runtime qualification remains pending; see TEST_REPORT.md and KNOWN_ISSUES.md.

### Repository preservation and release governance

Preserved the verified 0.1.0 source and immutable v0.1.0 tag on GitHub. Added permanent repository/branch/PR/release rules, private-state ignore patterns, and source-to-package provenance. Engine code, binary ZIPs, SDK and schema are unchanged. GitHub API access is forbidden in this environment; PR creation and binary release uploads are not confirmed.

### Source-publication review (no engine version change)

Reviewed source exclusions, common secret patterns, first-party runtime/install paths and the locked dependency license metadata. Added publication review, an inventory of 245 declared third-party package licenses, and explicit owner-pending licensing status. No open-source license selected, no engine/API/schema change, no tag moved, no binary replaced. Complete shipped-dependency notices, vulnerability audit and platform runtime qualification remain outstanding; GitHub API access still blocks PR/release uploads.

## 0.1.1 — Windows release/update infrastructure

Added standard versioned Windows ZIP/checksum assets, tag-gated GitHub Actions with native Windows compilation/CPU/updater tests, dependency notice bundles, automatic latest-stable download/verification, managed app staging/backups/rollback/journaling, persistent-state preservation, logs and stable root launchers. Retained legacy installation layouts and old tags/packages. Viewport title follows the actual compiled version. SDK 0.1/schema 1 remain compatible, no migration. No new engine feature phase or performance claim. See docs/RELEASE-0.1.1.md for actual tests and outstanding native/live verification.

## 0.1.2 — native Windows PowerShell ZIP compatibility

Fixed the missing explicit System.IO.Compression assembly load found by the native Windows PowerShell 5.1 test. Preserved the failed 0.1.1 source tag and local candidate; no misleading release upload claim. Added native-error annotations, clean candidate labeling, explicit exit-status logging and credential-free Cargo build caches. SDK 0.1/schema 1 remain compatible; no data migration or new engine features. Release assets remain gated on actual native CI success.

### 0.1.2 publication verification

Native Windows build/tests and live public API/download/install/upgrade/BAT checks passed. Tagged standard ZIP/checksum and bootstrap assets were published on GitHub and independently hash-verified; releases/latest resolves to v0.1.2. No API/schema/data migration. Interactive Windows viewport/GPU remains a user-machine check. Exact hashes/source/CI links are recorded under releases/0.1.2.
