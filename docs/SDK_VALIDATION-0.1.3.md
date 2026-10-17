# SDK 0.1.3 validation evidence

Baseline inspected: authoritative True Engine main `0de66e1baafa533391c72c342ac003aa70de74d4`; published Windows v0.1.2 source `8d751dbe76ca1dfd02c826e60ec68dda7e7d51b0`. Independently rechecked the released ZIP SHA-256 `14da9b37861b5a1e12353883b1b6354938ae661a070762bd9b9105126d867ec1`, ZIP CRC and all 217 managed payload hashes. Its evidence establishes native Windows compilation/CPU/updater tests; it does not establish interactive Windows GPU execution. No previous artifact was overwritten.

Consumer inspected read-only: License Plate Obfuscation Studio main `39d8af74e6f94fbfaf2387f8d7a5dd06898f3d2f`, application 0.1.2, vanilla browser ESM with a CSS preview and Python local host. No consumer source was changed or consumer integration claimed.

## Executed locally on Linux

- `cargo fmt --all -- --check`: passed.
- `cargo clippy --workspace --all-targets --locked -j4 -- -D warnings`: passed.
- `cargo clippy -p true-engine-web --target wasm32-unknown-unknown --locked -j4 -- -D warnings`: passed.
- `EGL_PLATFORM=surfaceless cargo test --workspace --locked -j4`: 17 CPU integration tests, 2 real GPU rendered-pixel tests and 1 SDK doctest passed; no failures or skips. This preserves all 8 original SDK tests. Custom-mesh GPU checks verify actual triangle pixels and retained prior output after invalid uploads.
- `python3 -m unittest discover -s tools -v`: 15 tests passed, covering prior packaging/updater behavior and 7 SDK packaging integrity tests.
- `cargo check --workspace --target x86_64-pc-windows-gnu --locked -j4` and existing standalone viewport WASM target check: passed compilation only.
- `python3 tools/sdk/build.py`: built optimized true-engine-web WebAssembly using Rust1.85.1 and checksum-verified official wasm-bindgen0.2.129; generated browser ESM/declarations and notices. The full native application was not rebuilt for this SDK command.
- `npm --prefix tools/browser run types`: the host example API usage type-checks against the actual staged package declarations.
- `npm --prefix tools/browser run unit`: 2 compatibility-bridge tests passed; these unit stubs are not rendering/platform evidence.
- `CHROMIUM_PATH=/usr/bin/chromium SDK_BACKENDS=webgl2 npm --prefix tools/browser test`: 8 tests passed, zero skipped/flaky. Chromium154.0.8037.57 headless, actual WebGL2/SwiftShader wgpu rendering. Tests load the compiled WASM, inspect blue cube/orange custom-mesh pixels, change materials/TRS, pick actual triangle geometry, drive pointer orbit/pan/wheel and keyboard reset, download/reopen a project, reject invalid inputs atomically, enforce camera/canvas bounds, resize, isolate multiple host-owned canvases and dispose/recreate a canvas.
- `tools/release/Test-Updater.ps1` under retained PowerShell7.4.13 on Linux: all18 existing synthetic PE/filesystem/mock-process checks passed. This is updater regression evidence, not native Windows execution.
- `actionlint` on the release workflow: passed. Official Linux CLI archive was downloaded, SHA-256 verified and executed; Windows CLI archive SHA/member were verified without executing Windows code.

Initial failures were investigated: multiple EGL tests initially shared a display concurrently; a test-only mutex resolved it. Browser console checks exposed a missing favicon and the example now uses an inline icon. Pixel checks account for sRGB color and keep focus outlines outside the captured canvas; tests still require thousands of changed/colored pixels and exact reset/save round trips. Current WebGPU rejected wgpu0.19's retired limit; a narrow verified binding bridge fixes that request. Headless WebGPU presentation remains under separate investigation: this cloud Chromium setup reports unavailable shared-image backing/device loss, so its failed tests are not counted as passed WebGPU checks. No GPU mock or CSS renderer replaced failed checks.

## Platform boundaries

Native GitHub Windows MSVC/PowerShell tests and browser-SDK CI are configured, with actual results to be recorded after runs complete. The Windows SDK job builds its own tagged-source SDK; the portable release ZIP is built on Linux. Successful Windows-source/browser tests would not imply byte-for-byte execution of the Linux-built archive. Interactive Windows11 hardware/driver and B: installation tests, macOS, Safari and Firefox are not verified here. No hardware-performance, production, complete device-loss recovery or commercial licensing certification is claimed.

The final package manifest records exact source/tool identity, actual release build/test evidence and payload hashes. The adjacent `.sha256` identifies that archive; it must be checked against a trusted release record. See releases/0.1.3 for final remote/tag/artifact evidence once available.
