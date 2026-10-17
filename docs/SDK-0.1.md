# TRUE ENGINE SDK contract 0.1

Engine version: 0.1.3 (compatible with 0.1.0, 0.1.1 and 0.1.2). Project schema: 1. Public Rust API: `true_engine` crate. Backward-compatible changes only unless explicitly approved, including during 0.x. No stable C ABI or plugin ABI is promised. The engine has no application domain dependencies.

Coordinates are right-handed, +Y up, units application-defined. Camera projection uses wgpu depth 0..1. Primitive cube side and sphere diameter are one unit; plane is a unit square on XZ. Parent world matrices multiply local TRS. IDs are caller-assigned u64, unique per scene. Parents must exist before children are added. Cycles, missing parents, nonfinite transforms, zero scales, nonunit rotations, invalid color channels and duplicate IDs are rejected. Colors are opaque linear RGBA (alpha is reserved; blending is not enabled). Nodes are exposed read-only to keep hierarchy validation intact.

`Scene::add` validates atomically; `world_matrix` returns None for unknown IDs. `pick` returns the nearest triangle hit, accepts nonnormalized ray directions, and returns None for a zero direction. Picking is CPU-based and linear in triangle count; there is no claimed large-scene acceleration. Primitive geometry is regenerated on scene upload/picking; GPU geometry remains retained between frames. Lighting is a simple two-sided directional diffuse approximation, not PBR.

`OrbitCamera` supports orbit, pan, exponential zoom (0.2..1000), view-projection and screen-space rays. Screen coordinates are physical pixels with top-left origin. Callers must pass positive viewport dimensions and finite inputs. `Renderer` requires a compatible wgpu device, output format and nonzero viewport dimensions. Call resize after target size changes; upload after a scene or selection change; draw after device/queue initialization. Device/surface lifecycle belongs to the host application.

`Project::to_json/from_json` validate schema 1 and the scene. Unknown schema versions are rejected without rewriting the input; there is no automatic migration. JSON serialization is semantic, not byte-stable. Preserve original files before deliberate user saves. Native example S saves and L loads `project.json` in its current directory. Browser example currently exposes viewport controls and picking; persistence uses the same SDK serialization API but host browser storage integration is not included.

Stable usage:

```rust
use true_engine::{Scene, Node, Primitive, Transform, Material, Project};
let mut scene = Scene::default();
scene.add(Node { id: 1, parent: None, name: "Cube".into(),
    transform: Transform::default(), primitive: Some(Primitive::Cube),
    material: Material::default() })?;
let json = Project::new(scene).to_json()?;
let loaded = Project::from_json(&json)?;
# Ok::<(), true_engine::scene::Error>(())
```

No license plate detection, masking, OCR, media pipeline, editor framework, networking, physics, animation, or future release phase is included.

Additive 0.1.3 mesh APIs: `geometry::Mesh::validate()` checks finite indexed triangles; `Scene::pick_with_meshes(origin,direction,&HashMap<NodeId,Mesh>)` and `Renderer::upload_with_meshes(device,scene,selected,&HashMap<NodeId,Mesh>)` use external mesh overrides. Upload validates references and GPU buffer limits before replacing geometry and returns a Result. Scene serialization is unchanged; native hosts own external-mesh storage. The separately versioned browser SDK supplies an explicit envelope; see [browser API](BROWSER_SDK_API.md).
