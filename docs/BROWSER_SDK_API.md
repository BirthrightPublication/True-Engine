# True Engine browser SDK 0.1.3

Package: `@birthright/true-engine@0.1.3`. Engine 0.1.3, native Rust contract 0.1, native project schema 1. This additive SDK uses the existing `true_engine::render::Renderer`, scene, material, mesh and orbit camera implementation. No standalone winit loop starts on import. It contains compiled WebAssembly, generated JavaScript bindings and TypeScript declarations; consumers do not need Rust, Python or a bundler at runtime. Original-code licensing remains the owner's decision; see LICENSING.md and shipped dependency notices.

Extract `True-Engine-SDK-v0.1.3-web.zip`, verify its SHA-256 against the release record, and serve its contents over HTTP(S). The included `example/` imports `../package/index.js`. Do not open it with file://. Serve `.wasm` with MIME `application/wasm`; JavaScript must have a JavaScript MIME type. WebGPU requires a secure context (HTTPS or localhost). Self-host the entire versioned package directory; do not put credentials or user data in it. No remote CDN or telemetry is required.

```js
import {createViewport, SDK_VERSION} from './vendor/true-engine/0.1.3/index.js';
const viewport = await createViewport(document.querySelector('canvas'), {
  backend: 'auto', controls: true,
  onError: error => showError(error.message)
});
viewport.addPrimitive({id: 1, name: 'Cube', primitive: 'Cube',
  material: {color: [0.3, 0.65, 0.9, 1]}});
viewport.loadMesh({id: 2, name: 'Triangle',
  positions: new Float32Array([-1,-1,0, 1,-1,0, 0,1,0]),
  indices: new Uint32Array([0,1,2]),
  transform: {translation: [2,0,0]}, material: {color: [1,0.4,0.1,1]}});
viewport.render();
// Unmount: remove observers/listeners and release Rust/GPU resources.
// viewport.dispose();
```

`createViewport(canvas, options)` returns a Promise of a `Viewport`. Supply an unused caller-owned HTMLCanvasElement. One live engine instance is allowed per canvas. The SDK never appends a canvas or replaces application DOM. `backend` accepts `auto` (default), `webgpu` or `webgl2`. Auto first requests a WebGPU adapter and falls back to the real WebGL2 wgpu backend if none exists. An explicit unavailable backend rejects; there is no CSS or mock-rendering fallback. Surface/device creation errors reject initialization; render errors are surfaced, not suppressed. The generated binding uses a narrow `webgpu-compat.js` bridge: it omits only the retired `maxInterStageShaderComponents` required limit on browsers that no longer expose it. All active required limits and the actual adapter request remain intact; no browser prototype is patched. Device-loss recovery beyond surface reconfiguration is not implemented.

`controls` defaults to true. Left drag orbits, right drag pans, wheel zooms, R resets a focused canvas. Give the canvas `tabindex="0"` and CSS `touch-action:none` in the host. Controls operate on pointer deltas in CSS pixels. No UI state, page-wide input or persistent browser storage is captured. Click emits `true-engine-pick` on the canvas with `event.detail.id` (number or null); the host owns selection styling. Errors from scheduled frames emit `true-engine-error` with the Error as detail and call `onError`, or log to the console if no handler exists.

`autoResize` defaults to true. A ResizeObserver follows the CSS canvas size using devicePixelRatio capped at 2. Hidden zero-size canvases retain their previous drawing buffer; they are resized when visible. For explicit sizing use `{autoResize:false}` and `resize(width,height)`. Dimensions are integer physical pixels, positive and at most 8192, also subject to the adapter's texture limit. Camera updates schedule one animation frame; geometry/material changes upload geometry once and schedule a frame. There is no unconditional animation loop. `render()` draws synchronously submitted GPU work; presentation completes asynchronously.

| API | Contract |
| --- | --- |
| `version`, `backend` | Read-only SDK version and actual selected backend. |
| `addPrimitive(spec)` | Add `Cube`, `Plane` or `Sphere`. Duplicate IDs and missing parents reject atomically. |
| `loadMesh(spec)` | Add a custom indexed triangle mesh from `Float32Array` XYZ positions and `Uint32Array` indices. Copies input data; no file-format parsing is implied. |
| `setMaterial(id,{color})` | Replace opaque linear RGBA color, each component finite in [0,1]. Alpha is reserved; blending is disabled. |
| `setTransform(id,transform)` | Replace local TRS; omitted components use identity defaults. Parents remain unchanged. |
| `orbit(dx,dy)`, `pan(dx,dy)` | Finite bounded pixel deltas. |
| `zoom(delta)` | Positive delta zooms in exponentially; distance clamps to 0.2..1000. |
| `resetCamera()` | Restore the default perspective orbit camera. |
| `getCamera()`, `setCamera(camera)` | `{target:[x,y,z],yaw,pitch,distance}`; radians, pitch -1.55..1.55 and distance 0.2..1000. No orthographic camera in this SDK. |
| `pick(x,y)` | Nearest triangle ID or null; physical canvas pixels, top-left origin, not page/CSS coordinates. |
| `resize(width,height)`, `render()` | Update surface/depth size, or render retained scene with current camera. |
| `exportProject()` | Return a validated browser-document JSON string, including custom geometry and camera. No disk or storage write. |
| `importProject(json)` | Atomically replace scene/meshes/camera from a supported browser document, or native schema 1 project. Unknown formats and invalid input reject. |
| `dispose()` | Idempotent; cancels queued frames, disconnects observer, removes SDK event handlers and releases GPU resources. Other calls afterwards throw. |

Node spec fields: positive integer `id` in 1..4294967295, optional `parent` ID (must already exist), `name`, `transform`, `material`, and required `primitive` for addPrimitive, or required positions/indices for loadMesh. A primitive cube has unit side, sphere unit diameter, plane unit square in XZ. Coordinates are right-handed, +Y up, application-defined units. Transform fields are `translation:[x,y,z]`, `rotation:[x,y,z,w]` unit quaternion and nonzero `scale:[x,y,z]`. Defaults: zero translation, identity quaternion and unit scale. Rotation/matrix/color validation matches the Rust SDK. Basic two-sided directional diffuse lighting uses flat triangle normals; textures, PBR, transparency, shadows and model-format import are absent.

Mesh limits: at most 1,000,000 vertices and 3,000,000 indices per mesh; indices must form complete triangles and reference finite vertices. Browser documents cap scene nodes at 10,000 and custom indices at 3,000,000 total. JSON input caps at 64 MiB. These are basic developer bounds, not untrusted-input service hardening or performance promises. Picking is CPU triangle traversal. Geometry is flattened on upload; instancing, spatial acceleration and automatic batching optimizations are outside this integration task.

Browser save envelope: `format:"true-engine-web-project"`, `format_version:1`, `project` (unchanged native schema 1), `meshes` (ID-to-indexed-mesh object), and `camera`. `exportProject` produces this envelope even when the scene uses only primitives. Native readers cannot consume that envelope directly; keep it distinct from native project files and Plate Studio's own application schema. Importing a native schema 1 project starts with the default camera and no custom meshes. No existing project is migrated or overwritten automatically. The example's explicit save downloads a new JSON file, and reopen reads the chosen file.

Compatibility: existing Rust signatures and native schema 1 remain valid. Added core APIs are `Mesh::validate`, `Scene::pick_with_meshes` and `Renderer::upload_with_meshes`. Browser APIs/declarations and envelope version are pinned by the package version; incompatible changes require explicit approval and migration documentation. No native C ABI, plugin system or npm registry publication is promised. See compatibility.json and manifest.json in the ZIP for source, hashes and actual test evidence.

The working example initializes a supplied canvas, displays a blue cube and orange indexed pyramid, changes material, controls the camera, picks objects and saves/reopens a JSON file. Automated tests exercise this exact packaged example and inspect real canvas pixels. Tested browser/platform/backends are recorded in the release report; target compilation alone does not verify Windows, macOS, Safari or Firefox execution. Studio integration is separate: see PLATE_STUDIO_INTEGRATION.md for its actual server/package changes.
