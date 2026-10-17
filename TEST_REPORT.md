# TRUE ENGINE 0.1.1 delivery-patch verification

Actual checks completed in the Linux cloud environment:

- Rust fmt and clippy with warnings denied: passed.
- `EGL_PLATFORM=surfaceless cargo test --workspace --locked -j 4`: 8 SDK tests, 1 real GPU pixel-readback test and 1 SDK doctest passed, zero failures/ignored. Empty unit harnesses are not counted.
- `python3 -m unittest discover -s tools -v`: 8 tests passed, covering existing updater/package behavior plus deterministic standard ZIPs, immutable output, filtered dependency notices and rejection of failed test evidence.
- `pwsh -File tools/release/Test-Updater.ps1 -Fixtures ...`: 18 integration checks passed on PowerShell 7.4.13/Linux. The latest-release API and HTTP downloads were mocked; payload EXEs are synthetic and native launch is mocked. Covers fresh install, upgrade, persistent app/root data, Build preservation, backups, current/downgrade behavior, corrupt hash, unsafe ZIP paths, incompatible SDK, foreign asset URLs, prerelease refusal, persistent-path collision, activation and post-install failure restoration, API denial, lock exclusion, interrupted recovery, recognized 0.1.0 compatibility and managed launcher data/backup/log behavior.
- actionlint 1.7.7: workflow syntax, expression and job checks passed; shellcheck/pyflakes integrations were disabled because those analyzers were not installed.
- Optimized Rust Windows x64 gnullvm cross-build: passed; PE imports inspected. Local candidate bundles libunwind.dll and notices. This is not native Windows compilation/execution.
- Windows-target dependency notice collection: 98 resolved target/build/dev packages; 206 dependency/Rust notice files before the extra LLVM runtime notices. Missing crate notice files were retrieved from exact upstream VCS commits or declared CC0 text with provenance, without selecting a license for original engine code.

Configured but NOT established by local tests: GitHub Actions native Windows MSVC builds, Windows PowerShell 5.1 filesystem tests, actual GitHub Release uploads/downloads, the BAT's Windows invocation, interactive Windows GPU behavior and installation on B:. Their completion requires independent CI/Windows evidence. Local GitHub API access returns 403 Forbidden. No workflow execution or asset publication is claimed merely because the workflow/source/tag is pushed.

Tagged 0.1.0 reports and previous packages remain retained. No new rendering/editor feature phase, schema migration or performance claim is introduced. See docs/RELEASE-0.1.1.md, docs/WINDOWS_UPDATES.md and each package's app/manifest.json for exact source/hash/build-time evidence.

## Native CI discovery and corrective source patch 0.1.2

The initial tagged 0.1.1 run (38993133322) failed on Windows while Linux passed. Diagnostic main run 38993584078 identified: `Unable to find type [IO.Compression.ZipArchive]` in the Windows PowerShell 5.1 updater test. Native fmt/clippy, SDK/doctests and Python tests had passed before that command. No 0.1.1 assets were uploaded by the failed run. Patch 0.1.2 explicitly loads System.IO.Compression as well as FileSystem; completion of its native run and publication must be checked separately. Earlier local 0.1.1 passing results are not being relabeled as native 0.1.2 passes.
