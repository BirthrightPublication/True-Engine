# v0.1.0 validation evidence

Current instance: Linux x86_64, Rust 1.85.1. This is an unreleased initial implementation, not a Windows-qualified product release.

| Executed check | Result |
| --- | --- |
| `bash tools/cloud-setup.sh` | Passed; pinned Rust installation/activation and locked workspace build |
| `cargo build --workspace --locked -j 4` | Passed on Linux |
| `cargo fmt --all -- --check` | Passed |
| `cargo clippy --workspace --all-targets --locked -j 4 -- -D warnings` | Passed |
| `EGL_PLATFORM=surfaceless cargo test --workspace --locked -j 4` | 8 SDK tests, 1 rendered-pixel GPU test, 1 SDK example doctest passed; no failed or ignored tests |
| `python3 -m unittest discover -s tools -v` | 5 tests passed: package manifest/immutable release, install/data/rollback, hash/path rejection, lock protection, restoration after simulated activation failure |
| `cargo check -p true-engine-viewport --lib --target wasm32-unknown-unknown --locked -j 4` | Passed; compilation only |
| `cargo check --workspace --target x86_64-pc-windows-gnu --locked -j 4` | Passed; compilation only, no executable linking/execution |
| `cargo build --release -p true-engine-viewport --target x86_64-pc-windows-gnullvm --locked -j 4` | Passed; optimized Windows PE cross-link, not runtime execution |
| Actual Windows payload package install/reinstall/rollback and SHA-256 checks | Passed on Linux with the actual EXE/DLL payload; Data preserved |
| `python3 tools/smoke_native.py` | Passed with virtual Xorg :99 and MIT-SHM disabled: native launch, visible geometry, click selection pixel change, S/L project round trip, orbit/pan/zoom pixel changes |

The offscreen GPU check uses EGL/OpenGL Mesa software rendering, reads back actual pixels, checks visible geometry against the background and checks selection changes. Native input checks use XTest and ImageMagick window captures in a temporary project directory. Initial virtual-display rendering failed with a Mesa shared-memory attachment error; disabling the Xorg MIT-SHM extension corrected it. The final tests exercise that configuration. No GPU hardware performance benchmark has run.

Not run: Windows executable runtime, Windows CMD/PowerShell scripts, macOS compilation/runtime, browser bundling/runtime, real hardware/large-scene performance. Python updater behavior was exercised on Linux with explicitly synthetic payloads; that is not Windows filesystem qualification. A process crash can leave a lock and a retained backup requiring manual recovery; updates are staged and compensate for ordinary rename failures, not a claim of power-loss atomicity.

The Windows x64 optimized executable was cross-linked using Rust x86_64-pc-windows-gnullvm and LLVM-MinGW 20261006 (upstream archive SHA-256 verified). PE imports were inspected: the required libunwind.dll and its dependency notices are included in the candidate package; remaining imports are Windows system/UCRT libraries. This proves linking and payload structure, not Windows execution.

No Windows B: filesystem is mounted. The Windows build tool defaults to `B:\True Engine\Build` when executed on Windows. The local source ZIP is a portable SDK source archive, not an executable Windows release or an updater payload. Package hashes and the full changed-file list are recorded in its manifest and sidecar; future executable release packages carry their own payload manifests and trusted digest requirements. Schema 1 / SDK 0.1; migration behavior: none. No future phase has started.

Reusable cloud `install_script` and `start_skill` were saved to the environment draft. Saving does not publish or validate restoration in a new task. Review and save in environment settings, then publish when desired.
