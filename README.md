# TRUE ENGINE

Current engine source: **0.1.1**, SDK **0.1**, scene schema **1**. This is a developer viewport/engine foundation, not a production-qualified engine or License Plate Obfuscation Studio.

The [standard GitHub release/updater guide](docs/WINDOWS_UPDATES.md) describes tag-driven native Windows builds and `Update True Engine.bat`. Existing 0.1.0 test-kit artifacts, tagged source and install directories are retained. Windows runtime and the new GitHub workflow must be verified separately from local Linux checks.


Reusable, application-agnostic Rust 3D engine for Birthright software. v0.1.0 initial implementation; platform qualification remains incomplete. License Plate Obfuscation Studio will consume the SDK separately.

The core provides scene hierarchy, cube/plane/sphere meshes, opaque color materials, orbit camera, triangle picking, schema-validated JSON projects, and a retained wgpu renderer. The viewport example owns window/input integration with winit; both native and wasm entry points are included.

## Development

Install Rust 1.85.1 using rustup. On Linux use a working X11/Wayland desktop with compatible graphics drivers. Tests use EGL/OpenGL (Mesa software rendering is sufficient).

```
cargo build --workspace --locked
cargo run -p true-engine-viewport --locked
EGL_PLATFORM=surfaceless cargo test --workspace --locked
cargo clippy --workspace --all-targets --locked -- -D warnings
python3 -m unittest discover -s tools -v
```

Left drag orbits, right drag pans, wheel zooms, click selects (gold highlight). S/L saves/loads project.json in the native example's working directory. The sample contains three primitives. See [SDK contract](docs/SDK-0.1.md) and [validation evidence](docs/VALIDATION.md) for limits.

## Browser

```
rustup target add wasm32-unknown-unknown
cargo build -p true-engine-viewport --lib --target wasm32-unknown-unknown --locked
# Install a wasm-bindgen-cli matching Cargo.lock's wasm-bindgen version.
wasm-bindgen --target web --out-dir web/pkg target/wasm32-unknown-unknown/debug/true_engine_viewport.wasm
python3 -m http.server --directory web 8000
```

Use a modern browser with WebGPU or WebGL2. Browser bundling and interactive behavior require separate verification; browser storage UI is not supplied.

## Windows release and updater

For a scripted build, run `powershell -File tools\windows-release.ps1` on Windows; it records actual command results and packages only after they pass. Interactive Windows qualification is still manual.

On a Windows x64 Rust/MSVC build machine run `cargo build --release --locked -p true-engine-viewport`, execute tests, then record their actual results in a JSON array. Python 3.10+ is required for packaging and updating:

```
py -3 tools\package.py --binary target\release\true-engine-viewport.exe --tests actual-tests.json --output "B:\True Engine\Build"
```

This creates a ZIP, SHA-256 sidecar, payload manifest and the updater/launcher scripts under B:\True Engine. Review the manifest before distribution. Every patch is a complete replacement of Current; no data migration occurs. Supply the trusted ZIP digest through a separately trusted release channel: a hash beside an untrusted archive alone does not authenticate it.

Double-click Update.cmd, enter ZIP path and trusted SHA-256, then Launch.cmd. Rollback.cmd accepts a backup folder ID. Close the application before updating. Application files live in Current, backups in Backups, and projects in Data. Updater never traverses Data. It stages before replacement, rejects unsafe ZIP paths, validates all payload hashes, serializes updates with a lock, restores the previous application on rename failure, and retains previous versions. Following a crash during activation, restore a retained backup using rollback; inspect any stale .update-lock before manually clearing it. Do not put personal files inside Current. Windows batch launch/update behavior has not yet been executed on Windows.

This Linux cloud machine cannot access a Windows B: drive. A cross-built Windows candidate kit is staged in the local Build directory, including the required libunwind.dll. Copy/extract it to the Windows location using docs/RELEASE-0.1.0.md. No installation on B: or Windows runtime verification is implied by this artifact. Do not start future release phases without owner approval.

The [master development roadmap](docs/ROADMAP.md) defines release phases, the permanent development directive, and the next practical v0.1 foundation patch.

Authoritative source: https://github.com/BirthrightPublication/True-Engine. See [GitHub workflow rules](docs/GITHUB_REPOSITORY_RULES.md). Release provenance under `releases/` binds downloadable package SHA-256 values to immutable source tags; a provenance record alone does not mean a binary is hosted on GitHub Releases.

Licensing of Birthright's original code remains the owner's decision; no open-source license is selected. See [LICENSING.md](LICENSING.md), [publication review](docs/PUBLICATION_REVIEW.md), and [locked dependency-license inventory](docs/DEPENDENCY_LICENSES.json). Version 0.1.0 is a development candidate, not production-ready or commercially cleared. Source publication, tagged builds, platform qualification and binary release uploads are separate states.
