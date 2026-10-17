# Source-publication security and licensing review

Reviewed source baseline: `9d5037b074d0a3b9bb6d174581cc8726345a7bb7`, with engine code unchanged from `v0.1.0` (`504953f171ef93297fc94eb99feadb4a667bb89f`). This review adds documentation and dependency-license metadata only. It does not invent a new engine version, qualify a production release or change a tagged package.

## Exact implementation status

Version 0.1.0, SDK 0.1, project schema 1; Windows test-kit distribution revision 2. The reusable Rust crate has `camera`, `geometry`, `scene`, and `render` modules. It supplies perspective orbit/pan/zoom, validated parent-child TRS scenes, cube/plane/sphere meshes, basic opaque materials/diffuse lighting, nearest-triangle picking and scene JSON round trips. The winit example supplies initialization, window/input lifecycle and native S/L saving/loading. A wasm entry point exists; its runtime is unqualified. No Studio application or license-plate functionality is part of this engine.

Absent features include orthographic/reset/keyboard navigation, transform gizmos, PBR/textures/import, animation/physics and a stable C/plugin ABI. The versioned Rust SDK contract documents compatibility and supported behavior. Consumers must pin a release/commit, not duplicate and modify engine code.

## Security review performed

- Inspected all 57 baseline tracked files, Git state/history, ignore rules, dependency/toolchain declarations, runtime source and release/install scripts. The source inventory contains text source/docs/configuration only; no EXE/DLL/ZIP/database/private-key files or NUL-containing payloads are tracked.
- Searched tracked bytes for common GitHub/AWS token/private-key patterns and suspicious long literal password/secret/API-key assignments: no matches. This is a bounded pattern scan, not proof that every possible secret format is absent.
- Confirmed installed state, caches, credentials, test projects and generated Build outputs are excluded. No secret values or raw environment/credential files were read or published.
- Inspected first-party Rust and packaging paths. There are no first-party Rust `unsafe` blocks. JSON scene load validates IDs, parents, cycles and transforms. Saved projects remain local. No first-party application telemetry or network service was identified.
- Package/install tools verify SHA-256, reject unsafe paths in the Python updater, stage replacements or use separate version directories, and preserve earlier versions. The r2 launcher isolates test data and backs up project.json before launch. Packaged manifests rely on a separately trusted outer ZIP digest; they are not signatures.
- The Windows BAT wrappers use process-scoped execution-policy bypass to invoke their packaged PowerShell scripts; they do not permanently change policy or disable payload hash checks. This is not code signing or Windows qualification.

Remaining security limitations: native startup has panic/unwrap error paths; S replaces the current test project file; project JSON/scene size is not bounded for hostile inputs; GPU device-loss recovery is incomplete. Do not deploy this local developer demo as an untrusted-input service or describe it as hardened. Unrestricted file input and resource-exhaustion hardening need a separate scoped engineering task.

`cargo audit --version` reported that cargo-audit is not installed. No RustSec/CVE scan, penetration test, code-signing validation or comprehensive dependency security audit was run in this review. Existing tests are regression evidence, not security certification.

## Licensing review performed

`cargo metadata --locked --format-version 1` resolved the Cargo.lock graph and generated docs/DEPENDENCY_LICENSES.json: 245 third-party packages, zero missing declared license expressions. These are declarations, not independently verified ownership/notice completeness. Metadata includes platform-specific/build/dev dependencies not necessarily shipped in the Windows binary.

The expressions include MIT/Apache alternatives, BSD, ISC, Zlib, CC0, Unlicense alternatives, Apache LLVM exceptions, LGPL alternatives and an expression requiring Unicode-3.0 together with another license. Expressions are preserved verbatim without selecting options. No project license was selected. LICENSING.md records the owner's pending decision.

No vendored dependency code, commercial font/model/media assets or required binary dependency is committed in the source tree. Existing Windows packages include LLVM/MinGW notices, but a full shipped-component notice bundle and distribution-obligation review remain pending before public/commercial binary distribution.

## Validation and publication evidence

The tagged TEST_REPORT.md records 8 SDK tests, 1 rendered-pixel GPU test, 1 SDK doctest, 5 Python tests, Linux native input/render/save/reopen smoke checks, optimized Windows cross-linking and PowerShell 7 logic checks on Linux with native launch mocked. Windows EXE/BAT/PowerShell 5.1 execution, Windows GPU compatibility, browser/macOS runtime and hardware benchmarks remain unverified. No application code changed in this review; those suites were not rerun merely for documentation changes.

This review freshly verifies the Cargo.lock license inventory, source exclusion/secret patterns, package SHA-256/source bindings and GitHub refs. Source and immutable v0.1.0 tag are on origin. Existing package names and checksums are recorded under releases/0.1.0. The GitHub API still returns 403 Forbidden, blocking PR creation and release-asset uploads. A source/tag push is not a binary upload or published GitHub Release. Keep those states distinct in completion reports.

## Additive 0.1.3 browser SDK review

Reviewed the publishable working-source inventory (142 files at first SDK commit), actual 0.1.2 binary manifest, new browser API/lifecycle/document boundaries, mesh validation, build/package provenance and conservative wasm-target dependency notice bundle. Common GitHub/AWS/private-key patterns found no matches; no binary/database/private-key payload was in publishable source. The compiled SDK ships generated dependency notices with target/commit provenance and original LICENSING.md, without choosing an original-code license. It requires no remote CDN, telemetry or credentials. Rust scene mutations remain validated; browser documents and user saves are explicit. Independent review identified and corrected initialization retry, initial dimension checks, explicit device/context disposal, atomic GPU/document updates and bounded camera panning. These bounded checks are not a CVE audit, security certification, hardware qualification or legal clearance. Actual tests and failed WebGPU software-presentation attempts are recorded in docs/SDK_VALIDATION-0.1.3.md.
