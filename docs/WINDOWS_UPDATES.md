# GitHub Windows release and update system

Repository: https://github.com/BirthrightPublication/True-Engine. Engine patch: 0.1.2; SDK 0.1, schema 1, no data migration. This implements delivery infrastructure, not a new feature phase or production qualification.

## One-time installation and subsequent updates

Place the provided bootstrap files `Update True Engine.bat` and `TrueEngine-Bootstrap.ps1` in `B:\True Engine`, preserving any unrelated existing files. Authenticate their bootstrap ZIP with the separately supplied SHA-256. Double-click the BAT. The root bootstrap delegates to the installed updater after the first installation, so later releases update their own managed update logic. No Python or Rust runtime is needed.

Alternatively a full standard release ZIP contains those bootstrap files and `app/`; extract to a new directory, then use the updater after it is installed. Never manually extract over an existing application or private files. The updater's default action needs no package path, version or checksum input.

The updater calls the repository's GitHub `/releases/latest` API (public, no embedded credentials), rejects draft/prerelease metadata, validates the tag and exact asset URLs, and downloads these assets:

- `True-Engine-vVERSION-windows-x64.zip`
- `True-Engine-vVERSION-windows-x64.zip.sha256`

Downloads are retained in unique `Build\Releases\vVERSION\ID` directories. `Build` remains the GitHub source/build area and is never wiped or used as the replacement target. Logs are retained at `Logs\Update-*.log`, with installed version, available version, outcome and errors. API 403/404/rate limits, missing assets, TLS/download failures, bad checksums or incompatible SDK/schema leave the installed app unchanged.

`Start True Engine.bat` launches the managed viewport. Its separate default workspace is `Data\ManagedViewport`. A deliberately created `TrueEngine-Launcher.json` can set `data_directory`; the updater never modifies it. Prelaunch backups preserve the prior project.json, while S deliberately replaces the test file during the session. L reloads scene data; camera state is not serialized. Existing legacy data is not silently imported or rewritten.

## Transaction and preservation rules

Only `app/` is replaced. Root launchers/bootstrap are created only when absent. Existing root files, preferences/settings/configuration, projects, Data, Build, prior downloads, Current, Versions and older launchers remain untouched. Current/Versions installations keep their old launchers and data paths. The known 0.1.0 test-kit App layout can be recognized and upgraded without deleting its root manifest. Arbitrary unmanaged app directories are refused.

Before activation the updater checks the outer SHA-256, locks/rechecks the archive, validates every path, rejects duplicate/case-alias paths/symlinks, enforces size limits and exact manifest contents, and checks every payload hash. Incompatible SDK/schema/migration declarations and automatic downgrades are refused. Unknown persistent files within an existing managed app are copied forward; collisions with new managed paths cause refusal. Reparse points in managed/update paths are refused. Existing application files move to `Backups\Updates\ID\app` before activation. An active installed viewport must be closed; the updater does not kill it.

An exclusive OS file lock serializes updates. Installation/validation failure restores the former app and retains failed payloads. Journals allow recovery of an interrupted update with an old app backup on the next run, preserving displaced new files. Disk corruption or full power-loss atomicity is not claimed. If recovery itself fails, retain all backup/journal/log files and repair from a known version without deleting data. Manual rollback: close the viewport, move current app to a new retained folder, move the chosen backup app back to root app, and keep data/Build untouched.

HTTPS plus SHA-256 detects transport corruption; a checksum from the same publisher is not a signature or protection against publisher-account compromise. Windows code signing is not implemented. BAT execution-policy bypass is process-scoped and does not disable package verification.

## Native Windows release automation

`.github/workflows/windows-release.yml` checks pull requests/main and builds stable semantic-version tags, beginning with `v0.1.1`. Manual stable GitHub Release publication is also supported. It uses Ubuntu for EGL/GPU regression tests and `windows-2022` for native MSVC compilation, CPU SDK/doctests, Python tests and the updater integration suite under built-in Windows PowerShell 5.1. Interactive viewport/GPU execution is not implied by those Windows tests.

On a release tag the builder checks Cargo version, exact tagged HEAD and clean tracked source; Rust is pinned to 1.85.1 and Cargo.lock is frozen. MSVC CRT is linked statically; the builder inspects PE imports and fails if non-system runtime DLLs are absent. It includes dependency license texts, upstream exact-commit notice fallbacks, Rust notices and an inventory; no True Engine open-source license is selected. This is a reproducible tagged-source recipe, not a claim of byte-identical binaries across changing Windows SDK/runner images. The ZIP writer itself uses fixed metadata and is deterministic for identical inputs.

After both jobs pass, assets are uploaded to the matching GitHub Release using the job-scoped token with contents:write. A new release stays draft until upload succeeds. A manually published empty release may briefly lack assets; the updater fails safely during that interval. Existing release assets are not clobbered on reruns. The standard package/checksum and an optional small bootstrap ZIP/checksum are uploaded. Per-version notes must exist at `docs/RELEASE-VERSION.md`. A GitHub stable channel entry does not imply a production-ready engine.

Maintainer sequence: fetch/review, feature branch, test, push, PR review where available, merge approved source into main, tag matching Cargo version, and push tag. Never move old tags. Confirm the Actions run and asset hashes before declaring a release published. Repository Actions must be enabled and its token permitted to write releases. A local source/tag push is not proof that a CI run succeeded.

To reproduce locally on a Windows x64 MSVC build machine: install Rust/rustup 1.85.1 (rustfmt/clippy), Visual Studio C++ Build Tools and Python 3.12; check out the exact tag, then run `powershell -File tools/release/Build-WindowsRelease.ps1 -Version VERSION`. For untagged validation only, add `-Candidate`. Packages go into the checkout's Build directory; put that checkout under `B:\True Engine\Build` when using the requested Windows layout. Source clones and generated binaries remain separate from root app/data.

## Validation boundary

See `docs/RELEASE-0.1.1.md` and TEST_REPORT.md. Local Linux tests use mocked GitHub HTTP and synthetic PE files for updater logic. Native Windows workflow runs, GitHub asset publication and live updater behavior must be confirmed independently. If the API is blocked in the current environment, report that concrete blocker rather than claiming an upload or automatic update succeeded.

## Verified first published release

v0.1.2 was built and published by Actions run 38994274833 at source 8d751dbe76ca1dfd02c826e60ec68dda7e7d51b0. Native live Windows run 38994649708 verified public metadata/downloads, hashes, fresh install, a synthetic-older-marker upgrade with real payload, data/Build preservation and the actual BAT. Viewport GPU execution remains unverified. The failed 0.1.1 tag is retained; no successful assets were claimed for its failed run. Current asset hashes and exact workflow URLs are in releases/0.1.2/github-release.json.
