use true_engine::{geometry::Mesh, glam::Vec3, Material, Node, Primitive, Transform};
use true_engine_web::document::{CameraState, Document};
fn node(id: u64, primitive: Option<Primitive>) -> Node {
    Node {
        id,
        parent: None,
        name: "integration".into(),
        primitive,
        transform: Transform::default(),
        material: Material::default(),
    }
}
fn triangle() -> Mesh {
    Mesh {
        vertices: vec![
            Vec3::new(-1., -1., 0.),
            Vec3::new(1., -1., 0.),
            Vec3::new(0., 1., 0.),
        ],
        indices: vec![0, 1, 2],
    }
}
#[test]
fn custom_mesh_camera_and_native_scene_round_trip() {
    let mut doc = Document::default();
    doc.add(node(1, Some(Primitive::Cube)), None).unwrap();
    doc.add(node(2, None), Some(triangle())).unwrap();
    doc.camera = CameraState {
        yaw: 0.,
        distance: 3.,
        ..Default::default()
    };
    let encoded = doc.to_json().unwrap();
    let reopened = Document::from_json(&encoded).unwrap();
    assert_eq!(reopened.meshes, doc.meshes);
    assert_eq!(reopened.project, doc.project);
    assert_eq!(reopened.camera, doc.camera);
    assert_eq!(reopened.project.schema_version, 1);
}
#[test]
fn accepts_legacy_schema_one_without_rewriting_it() {
    let mut doc = Document::default();
    doc.add(node(1, Some(Primitive::Cube)), None).unwrap();
    let native = doc.project.to_json().unwrap();
    let imported = Document::from_json(&native).unwrap();
    assert_eq!(imported.project.to_json().unwrap(), native);
    assert!(imported.meshes.is_empty());
}
#[test]
fn mutations_reject_invalid_input_atomically() {
    let mut doc = Document::default();
    doc.add(node(1, Some(Primitive::Cube)), None).unwrap();
    let before = doc.to_json().unwrap();
    assert!(doc.add(node(1, None), Some(triangle())).is_err());
    assert!(doc.add(node(0, None), Some(triangle())).is_err());
    assert!(doc
        .add(node(u32::MAX as u64 + 1, None), Some(triangle()))
        .is_err());
    assert!(doc
        .set_node(
            1,
            None,
            Some(Material {
                color: [2., 0., 0., 1.]
            })
        )
        .is_err());
    assert!(doc.set_node(55, None, Some(Material::default())).is_err());
    assert_eq!(doc.to_json().unwrap(), before);
}
#[test]
fn validates_envelope_mesh_references_and_camera() {
    let mut doc = Document::default();
    doc.meshes.insert(9, triangle());
    assert!(doc.validate().is_err());
    doc.meshes.clear();
    doc.camera.distance = 0.;
    assert!(doc.to_json().is_err());
    doc.camera = CameraState::default();
    doc.format_version = 2;
    assert!(doc.to_json().is_err());
    assert!(Document::from_json(r#"{"schema_version":99,"scene":{"nodes":[]}}"#).is_err());
    assert!(CameraState {
        pitch: f32::NAN,
        ..Default::default()
    }
    .camera()
    .is_err());
}
