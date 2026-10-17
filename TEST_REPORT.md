# TRUE ENGINE 0.1.0 — Windows test kit r2 test report

Engine binary unchanged; delivery scripts/documentation are new. No engine feature milestone advanced.

Fresh checks in this packaging session:

- `cargo fmt --all -- --check`: passed.
- `cargo clippy --workspace --all-targets --locked -j 4 -- -D warnings`: passed.
- `EGL_PLATFORM=surfaceless cargo test --workspace --locked -j 4`: 8 SDK integration tests, 1 actual GPU pixel-readback test and 1 SDK doctest passed; zero failures/ignored. Unit harnesses with zero tests are not counted as tests.
- `python3 -m unittest discover -s tools -v`: 5 packaging/updater tests passed. These use synthetic PE/payload fixtures and Linux filesystem behavior, not Windows runtime execution.
- `python3 tools/smoke_native.py`: passed after documented Xorg restart; actual visible pixels, selection, S/L project round trip, orbit, pan and zoom verified through X11 input and image comparisons.
- `cargo build --release -p true-engine-viewport --target x86_64-pc-windows-gnullvm --locked -j 4`: passed; optimized x64 PE, identical to the earlier 0.1.0 payload binary.
- `pwsh -NoProfile -File tools/test_windows_testkit.ps1 -PackageRoot <staged-kit>` using PowerShell 7.4.13 on Linux: passed four script parses, actual payload hashes, tampered-DLL rejection, side-by-side install/preservation, existing-version refusal, a new root launcher, paths with spaces, isolated launch directory, prelaunch backup and log creation. The Windows OS environment gate was simulated and native process launch was MOCKED. This is not Windows PowerShell 5.1 or Windows runtime qualification.

Earlier recorded checks in docs/VALIDATION.md also include wasm and Windows GNU target compilation, LLVM-MinGW checksum verification, PE imports, and actual EXE/DLL payload installation/reinstallation/rollback on Linux.

Not run here: Windows executable execution, real Windows 11 GPU compatibility, Windows PowerShell 5.1/BAT execution, installation on B:, macOS execution, browser runtime, hardware performance benchmarks. Any PowerShell 7 tests on Linux simulate installer/launcher logic and do not establish Windows behavior.

The native smoke test initially could not run because the prior task's Xorg process had stopped; restarting the documented virtual display resolves that environment prerequisite. No application code was changed to bypass a failing check.
