# Build the True Engine browser SDK on Windows

This builds the existing Rust/wgpu renderer into the versioned browser SDK. It
does not replace the installed desktop application, its updater, projects, or
settings. The SDK is consumed by a browser application through JavaScript ES
modules and WebAssembly; application users do not need Rust or Python installed.

## Prerequisites

Use a Windows 11 x64 development machine with Git, Python 3.11 or newer, Rust
1.85.1 through rustup, and Microsoft Visual Studio 2022 Build Tools with the
**Desktop development with C++** workload and a Windows SDK. Native MSVC tools
are needed when compiling native developer tools such as wasm-bindgen-cli.
Install Node.js 24 LTS for the automated browser tests. Download installers from
their official publishers and verify them before running them.

From a developer PowerShell terminal in the exact tagged True Engine checkout:

```powershell
rustup toolchain install 1.85.1 --profile minimal --component rustfmt --component clippy
rustup target add wasm32-unknown-unknown --toolchain 1.85.1
cargo +1.85.1 install wasm-bindgen-cli --version 0.2.129 --locked
rustc --version
wasm-bindgen --version
python --version
node --version
```

The required wasm-bindgen CLI version must match `Cargo.lock` exactly. The build
script checks both pins. If compiling the CLI requires a newer compiler due to
its own developer dependencies, install that separate toolchain for the CLI
build while retaining 1.85.1 for this engine. An official wasm-bindgen 0.2.129
Windows prebuilt CLI is an alternative: verify its archive against the upstream
release checksum before adding its directory to PATH. Do not run an unverified
third-party CLI binary. No script here installs system tools automatically.

## Source and output directories

Retain the existing `B:\True Engine` installation. Put a separate source checkout
under `B:\True Engine\Build\Source\True-Engine`, or use an existing verified
checkout. Do not extract source over installed files or replace an earlier
working checkout. Fetch and check out the SDK's exact source tag before building;
`manifest.json` in the release ZIP records its commit and tag.

```powershell
Set-Location 'B:\True Engine\Build\Source\True-Engine'
git fetch origin --tags
git switch --detach v0.1.3
powershell -NoProfile -File tools\sdk\Build-Windows.ps1
```

The wrapper calls Python's build script. The equivalent direct command is:

```powershell
python tools\sdk\build.py
```

It runs `cargo build --release -p true-engine-web --target
wasm32-unknown-unknown --locked`, followed by `wasm-bindgen --target web`.
Incremental Cargo output is reused; this does not rebuild unrelated native engine
applications. The stage contains `package/` with real `.wasm`, JavaScript and
TypeScript declarations, `example/`, `docs/`, and `compatibility.json`. Original
engine licensing remains pending the owner's decision. Dependency and Rust
notices are included under `package/notices/`; this conservative filtered Cargo
inventory can include developer/example dependencies and is not an exact linked
binary SBOM.

## Launch the example

```powershell
python -m http.server 8080 --directory Build\sdk-web
```

Open `http://localhost:8080/example/` in a modern browser. Keep the terminal open
while using the example. Use HTTP(S), rather than opening the HTML as a file; the
server must serve `.wasm` as `application/wasm`. WebGPU requires a secure context
(localhost qualifies). An available WebGL2 adapter can be used where supported.
Consult `BROWSER_SDK_API.md` and `PLATE_STUDIO_INTEGRATION.md` for the actual API,
example behavior, consumer dependency pinning, and browser document format.

## Test, then package

Follow `tools/browser/README.md` for the automated Playwright integration command
and its prerequisite browser installation. Run those tests against this exact
default `Build/sdk-web` stage inside the source checkout. The browser and type
test commands intentionally use that stage; do not override `--stage` for this
workflow. Also run the required Rust and packaging checks from `AGENTS.md`.
Record only commands actually executed, their exit codes, host platform, and
rendering backend in an evidence JSON array. For example, replace the placeholder
command and result with your actual run before saving:

```json
[
  {
    "command": "the exact browser test command that was run",
    "exit_code": 0,
    "platform": "Windows 11 x64",
    "result": "the actual test count and backend reported by the test runner"
  }
]
```

Package from the clean exact tagged source without editing source or staged
files between building, testing, and packaging:

```powershell
python tools\sdk\pack.py `
  --evidence 'B:\True Engine\Build\sdk-test-evidence.json' `
  --output 'B:\True Engine\Build'
Get-FileHash 'B:\True Engine\Build\True-Engine-SDK-v0.1.3-web.zip' -Algorithm SHA256
```

Outputs are `True-Engine-SDK-v0.1.3-web.zip` and the corresponding `.zip.sha256`.
The ZIP contains payload checksums, actual test evidence, exact source identity,
compatibility and migration metadata. Existing release assets are never
overwritten. For an untagged development build, use `--candidate` and a separate
output directory; its manifest explicitly identifies it as a candidate.

Fixed ZIP metadata and sorted files make packaging deterministic for identical
staged bytes and evidence. Compiler output is not claimed to be bit-for-bit
identical across operating systems or toolchain distributions. Linux browser
tests do not verify Windows execution; only tests actually run on Windows may be
reported as Windows results.
