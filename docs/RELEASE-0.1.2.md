# TRUE ENGINE 0.1.2 — Windows PowerShell 5.1 compatibility correction

Previous source patch: 0.1.1. SDK 0.1, project schema 1, no migration or engine API break. No new engine feature phase. Tag 0.1.1 is retained; its native Windows updater test failed and no release assets were published by that run.

The native GitHub Windows runner identified a missing explicit `System.IO.Compression` assembly load under Windows PowerShell 5.1. PowerShell 7/Linux had automatically loaded the type. This patch loads both required compression assemblies before using ZipArchive, retains explicit command exit-status checks, and exposes native command failures in public annotations. Build caches contain only Cargo registry/git dependency objects and target outputs, never credentials or user state.

Standard packaging/update behavior is described in docs/WINDOWS_UPDATES.md: `True-Engine-v0.1.2-windows-x64.zip` and `.sha256`, complete app payload, latest-stable automatic downloads, integrity/path checks, staged installation, data preservation, backups, rollback/recovery and logs. Engine title follows Cargo version. Root/Build/legacy/data are not wiped. Dependency notices remain bundled; no first-party open-source license is selected.

Test evidence is recorded in TEST_REPORT.md and each package's app/TEST_REPORT.md and manifest. Local Linux tests and synthetic updater fixtures do not verify Windows graphics. Native Windows CPU/PowerShell filesystem tests must pass before the workflow publishes the matching assets. Interactive Windows GPU execution and end-to-end user-machine checks remain separate. Do not claim successful CI or asset uploads until independently verified.

Installation: authenticate/extract the one-time bootstrap into B:\True Engine, run Update True Engine.bat, then Start True Engine.bat. Downloads stay in unique Build\Releases folders. Persistent data and unknown managed-app contents are retained; conflicting paths, incompatible SDK/schema and downgrades are refused. Automatic rollback restores old app files on installation failure; manual rollback can restore a retained Backups\Updates\ID\app without changing data/Build.

No performance improvement or production qualification is claimed. Every package manifest records exact source commit and payload hashes; its SHA-256 sidecar identifies that build. The local API domain is blocked at the cloud proxy until the saved network draft is applied; Git operations and the public Actions UI remain usable.
