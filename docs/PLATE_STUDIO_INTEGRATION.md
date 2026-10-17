# License Plate Obfuscation Studio integration

This guide connects the versioned True Engine browser SDK to the actual Plate
Studio architecture. It does not change or release Plate Studio. Its current
development hold remains in effect; delivering this SDK does not authorize a UI
redesign, installation repair, project migration or application release.

## Inspected application baseline

Repository: <https://github.com/BirthrightPublication/License-Plate-Obfuscation>.
The inspected `main` commit is
`39d8af74e6f94fbfaf2387f8d7a5dd06898f3d2f`, application version `0.1.2`.
The inspection was read-only. No application files, settings, projects, release
tags or installations were changed.

At that commit:

- `package.json` declares standard browser ES modules, no framework, bundler or
  True Engine dependency.
- `src/app.js` changes CSS rotation on an HTML plate. There is no engine viewport,
  mesh renderer, engine camera or SDK adapter.
- `true-engine.compatibility.json` has null SDK package/version, no tested engine
  versions and `integrationStatus: "blocked-sdk-not-supplied"`.
- `tools/launch.py` serves a fixed set of four UI assets on loopback HTTP. The
  native `PlateStudio.exe` freezes that host and opens the default system browser;
  it is not an embedded webview or a native rendering integration.
- `AGENTS.md`, `NEXT_ITERATION.md` and `docs/TRUE-ENGINE-UI-ARCHITECTURE.md` require
  a tested SDK and separate approval to resume consumer implementation. Current
  CSS presentation is an experimental prototype, not the approved editor.

## Recommended dependency

Use `@birthright/true-engine` version **0.1.3**, delivered in
`True-Engine-SDK-v0.1.3-web.zip`. This is an SDK artifact name and package identity,
not a claim that an npm registry publication exists. Verify the release's exact
SHA-256 and compatibility manifest before accepting it into an application build.
Pin its source tag/commit and checksum alongside the package version. Do not
depend on `latest`, a moving branch, an unversioned CDN or a modified local copy
of engine source.

The browser distribution contains:

```text
package/
  index.js
  index.d.ts
  true_engine_web.js
  webgpu-compat.js
  true_engine_web_bg.wasm
```

Copy the verified package payload into a versioned application dependency path,
for example `vendor/true-engine/0.1.3/`, as part of a separately approved consumer
build. Retain its compatibility, integrity and third-party notice files with that
distribution. This copies a pinned distributable dependency, not a separate fork
of the Rust engine. No bundler is required by the existing application.

The ESM loader and WebAssembly module invoke True Engine's existing wgpu renderer.
The application supplies an ordinary canvas and domain commands; it must not
create a replacement WebGL renderer, implement independent camera mathematics or
fall back to CSS transformations while reporting engine operation.

## Public API boundary

The SDK initializes a caller-owned canvas rather than appending a demonstration
window to the document. A minimal host integration is:

```html
<canvas id="viewport" width="960" height="600"
        aria-label="True Engine 3D viewport"></canvas>
<script type="module">
  import { createViewport } from './vendor/true-engine/0.1.3/index.js';

  const canvas = document.querySelector('#viewport');
  const viewport = await createViewport(canvas, {
    backend: 'webgl2',
    controls: true,
  });
  viewport.addPrimitive({ id: 1, name: 'Example cube', primitive: 'Cube' });
  viewport.setMaterial(1, { color: [0.2, 0.6, 0.9, 1] });
  viewport.setTransform(1, {
    translation: [0, 0, 0],
    rotation: [0, 0, 0, 1],
    scale: [1, 1, 1],
  });

  // Retain this handle in the host and call viewport.dispose() when removing it.
</script>
```

Handle initialization/render errors visibly and retain the user's project. An
unavailable engine must produce an explicit unavailable state, not a substitute
preview described as True Engine rendering. `auto` selects a supported engine
backend; it is not permission for application-side imitation rendering.

The documented geometry entry point accepts application-generated triangle data:

```js
viewport.loadMesh({
  id: 2,
  name: 'Example triangle',
  positions: new Float32Array([-1, 0, 0, 1, 0, 0, 0, 1, 0]),
  indices: new Uint32Array([0, 1, 2]),
  material: { color: [1, 0, 0, 1] },
});
```

Use the shipped declarations and public API documentation for input validation,
limits and return types. Geometry uses the engine's right-handed coordinates,
with +Y up and application-defined units. Basic materials are opaque color
materials; PBR, textures, transparency and asset-format import are not implied.
Plate-specific geometry generation, text, domain validation and project commands
belong in Plate Studio, not True Engine.

Camera navigation uses `orbit`, `pan`, `zoom`, `resetCamera`, `setCamera` and
`getCamera`. Use the SDK controls or route approved host input to these methods.
`pick(x, y)` receives **physical canvas pixels** with the top-left origin. When
using custom pointer handling, convert from CSS coordinates using the canvas
backing dimensions and bounding rectangle; account for device pixel ratio and
resizing. Do not apply camera changes as CSS transforms to the canvas.

The complete runnable SDK proof is [examples/browser-sdk](../examples/browser-sdk).
It belongs to the engine repository and can be tested independently of Plate
Studio's UI and installation. Consult its actual test results before asserting a
particular browser, backend, operating system or GPU is supported. Successful
Linux browser execution alone does not verify Windows runtime compatibility.

## Consumer host and packaging changes still required

The existing consumer cannot serve or package the SDK unchanged. Under separate
consumer authorization:

1. Extend `tools/launch.py`'s exact asset allowlist to the pinned SDK files. Its
   current four-entry list returns 404 for every SDK asset. Serve JavaScript with
   a JavaScript MIME type and WASM with `application/wasm`; preserve path
   restrictions and integrity checks. Load over the supported HTTP origin rather
   than opening the HTML through `file://`.
2. Extend `tools/windows_release.py`'s explicit PyInstaller data inventory and
   generated UI integrity manifest to include the SDK and required notices. That
   inventory currently embeds only the same four UI files. Dropping WASM files
   beside an existing EXE does not add them to its frozen host.
3. Add the pinned SDK as a dependency of the consumer build, with exact package
   hashes. Preserve the original SDK artifact and record its engine source
   commit. Update the application compatibility manifest only after actual
   integration tests, listing versions and platforms that were really tested.
4. Create a thin adapter that translates application commands to these public
   methods and maps object IDs to domain objects. Keep domain state, legal
   metadata, validation and persistence in the application. Do not call private
   generated WASM exports or modify/copy engine source to satisfy missing APIs.
5. Run a browser/native-host proof: create a real GPU viewport, load a mesh,
   change a material, resize, orbit/pan/zoom, pick, export/reimport, dispose and
   recreate. Test initialization errors and retained application data. Windows
   desktop acceptance must exercise the actual packaged host and target browser,
   not only the source server or a Linux browser.

These are integration requirements, not changes performed in Plate Studio by this
SDK task. No updated consumer EXE, installer, application tag or tested consumer
compatibility claim is supplied merely by shipping the engine SDK.

## Project and installation preservation

The existing native Rust SDK contract remains **0.1** and its `Project` scene
schema remains **1**. Browser `exportProject()` / `importProject(string)` use the
separate `true-engine-web-project` format **1**, which carries custom meshes and
camera state. The browser document is not interchangeable with the native scene
JSON and must not be passed to `true_engine::Project::from_json` as though it were.

Plate Studio's current application `schemaVersion: 1` stores name/state/text and
does not contain engine scene/camera state. Keep that format distinct from both
engine formats. A future application schema can embed the browser document and
an exact SDK reference after an explicit migration design and tests. No automatic
migration, overwrite or reinterpretation of existing exports is authorized here.

Keep the same browser profile and `http://localhost:4173` origin when evolving the
existing application. Current project storage uses `birthright.plate.project.v1`;
notes use `birthright.plate.notes.v1` and are not included in project exports.
Moving origin, changing port or clearing browser data can hide this existing
state. Preserve original exports and notes before any later approved migration.

Engine SDK artifacts remain in the True Engine `Build` directory. The engine and
consumer repositories/installations remain separate; SDK preparation does not
write to `B:\True Engine`, `B:\License Plate Obfuscation Studio`, existing
application folders or user data. Licensing for original Birthright code remains
the owner's decision; see [LICENSING.md](../LICENSING.md). A package identity or
public source repository does not itself grant redistribution terms.

For the first consumer integration use the qualified `webgl2` backend explicitly. This remains actual Rust/wgpu rendering through WebAssembly. The SDK also exposes WebGPU/auto initialization, but this cloud software-graphics environment could not qualify WebGPU presentation; enable it for consumers only after their target-platform graphics checks pass.
