# TRUE ENGINE — master development roadmap

Project: TRUE ENGINE. Organization: Birthright. Language: Rust. Graphics: wgpu/WebGPU. Targets: Windows, Linux, macOS, modern browsers.

TRUE ENGINE is an original, reusable, performance-optimized 3D rendering and simulation engine for future operational-security, privacy research, and visualization applications. Its first consumer is License Plate Obfuscation Studio. The engine remains application-independent; consumer-specific functionality belongs outside the core.

## Permanent development directive

When the owner says **Continue**, inspect the implementation, validation evidence, and current release scope, then implement the next practical milestone or patch. Within the approved phase, proceed without asking for routine implementation choices. A generic Continue does not remove the requirement for explicit approval before beginning a future release phase; when that boundary is reached, report the completed phase and request approval for the concrete next phase.

Coordinate integration through a versioned SDK. Do not modify consuming application repositories directly. Preserve backward compatibility unless the owner explicitly approves a break. Do not implement expensive generalized systems without a demonstrated application need. Keep the engine minimal, fast, reliable, and reusable.

Every delivered patch records changed files, tests actually run and their results, compatibility, SHA-256 for packages and payloads, and migration behavior. Never claim untested functionality or platform behavior as verified. Preserve user data, validate package integrity, retain backups, and support rollback. Windows release packages belong in `B:\True Engine\Build`, with the updater in `B:\True Engine`; Linux staging is not installation at those paths.

## V0.1 — engine foundation

- Working 3D viewport
- Perspective and orthographic cameras
- Orbit, pan, zoom, and reset camera
- Mouse and keyboard controls
- Primitive geometry and meshes
- Basic materials and lighting
- Responsive rendering loop
- Scene initialization
- Basic developer documentation
- Working Windows test build

## V0.2 — editing system

- Object selection and picking
- Translation, rotation, and scale gizmos
- World/local coordinate systems
- Measurements and units
- Grid, axis indicators, and snapping
- Scene hierarchy
- Undo and redo
- Basic project serialization

## V0.3 — rendering and materials

- Physically based materials
- Metallic and roughness properties
- Texture mapping
- Normal maps
- Transparent materials
- Shadow mapping
- Antialiasing
- Environment lighting
- Rendering quality presets

## V0.4 — geometry and assets

- glTF/GLB import
- Geometry instancing
- Mesh transformations
- Bounding volumes
- Collision and clearance measurements
- Material editing
- Reusable scene components
- Asset caching

## V0.5 — simulation framework

- Modular simulation interfaces
- Light and shadow simulation
- Camera perspective experiments
- Environmental lighting presets
- Geometric occlusion measurement
- Configurable simulation parameters
- Repeatable experiment presets
- Visualization of measurement uncertainty

## V0.6 — performance

- GPU profiling
- CPU profiling
- Memory allocation optimization
- Frustum culling
- Mesh batching
- Level-of-detail support
- Async asset loading
- Render scheduling
- Performance benchmarks

## V0.7 — advanced editor services

- Animation timeline foundation
- Keyframe system
- Scene snapshots
- Precise transform inputs
- Multiple camera views
- High-resolution screenshots
- Project history
- Extensible inspector properties

## V0.8 — cross-platform

- Windows builds
- Linux builds
- macOS builds
- Browser/WebAssembly builds
- Platform compatibility testing
- Graphics backend fallbacks where practical
- Portable project format
- Installers and update validation

## V0.9 — SDK and plugin framework

- Stable public APIs
- Versioned SDK
- Plugin architecture
- Application-defined components
- Example integration applications
- Compatibility tests
- Developer documentation
- Security review

## V1.0 — stable engine release

- Stable project serialization
- Stable release interfaces
- Performance regression testing
- GPU device-loss recovery
- Robust error handling
- Reproducible builds
- Release automation
- Documentation
- Production integration testing

## After V1.0

Expand as demonstrated Birthright product needs require. Possible additions include advanced ray tracing, physics, CAD geometry, complex vehicle models, procedural geometry, spatial analysis, GPU compute, and simulation plugins. These are possibilities, not authorization to implement them.

## Current scope and next practical patch

The existing v0.1.0 candidate includes perspective orbit/pan/zoom, primitive rendering, materials/lighting, picking, scene hierarchy, and schema-1 serialization. Picking, hierarchy, serialization, and the initial SDK contract already exist under the earlier approved v0.1 scope; retain their compatibility even though their broader roadmap phases are later. Their presence does not authorize the rest of those phases.

The next v0.1 foundation patch should add orthographic projection, camera reset, and documented keyboard camera controls, with automated checks and a native input smoke test. Preserve the existing perspective API behavior and project schema. A Windows x64 executable has been cross-linked, but Windows execution and updater qualification remain outstanding; a cross-build alone does not complete the working Windows test-build requirement. See VALIDATION.md for actual evidence.
