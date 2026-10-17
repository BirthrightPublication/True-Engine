# Changelog

## 0.1.0 — initial implementation, unreleased

Added application-agnostic scene/camera/geometry/project/render modules; native and browser viewport entry points; SDK contract; automated scene and rendered-pixel tests; Windows ZIP packaging and integrity-checked staged updater with backups/rollback.

Compatibility: SDK 0.1 and project schema 1. Migration: none; unsupported schemas are rejected. Platform runtime verification is tracked in docs/VALIDATION.md. No Windows binary release has been qualified. Future phases require approval.

### 0.1.0 distribution revision 2 — Windows first-time test kit

Reuses the existing optimized Windows EXE unchanged. Adds a directly runnable portable layout, `START APPLICATION.bat`, an optional side-by-side B-drive installer, dependency/integrity checks, isolated test data, prelaunch project backup, launch logs, and `README - FIRST TIME SETUP.txt`. No Rust or Python runtime is needed to launch this kit. Earlier ZIPs and working versions are preserved. SDK 0.1/schema 1, no migration or breaking engine changes. Windows runtime qualification remains pending; see TEST_REPORT.md and KNOWN_ISSUES.md.
