use std::collections::HashMap;
use true_engine::{geometry::Mesh, glam::Vec3, *};

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

fn node(id: NodeId, parent: Option<NodeId>, primitive: Option<Primitive>) -> Node {
    Node {
        id,
        parent,
        name: format!("node {id}"),
        transform: Transform::default(),
        primitive,
        material: Material::default(),
    }
}

#[test]
fn mesh_validation_rejects_invalid_positions_indices_and_shapes() {
    let valid = triangle();
    valid.validate().unwrap();
    let mut invalid = valid.clone();
    invalid.indices[2] = 3;
    assert!(invalid.validate().is_err());
    invalid = valid.clone();
    invalid.vertices[0].x = f32::NAN;
    assert!(invalid.validate().is_err());
    invalid.vertices[0].x = f32::INFINITY;
    assert!(invalid.validate().is_err());
    invalid = valid.clone();
    invalid.indices.pop();
    assert!(invalid.validate().is_err());
    invalid.indices.clear();
    assert!(invalid.validate().is_err());
    invalid = valid;
    invalid.vertices.clear();
    assert!(invalid.validate().is_err());
}

#[test]
fn mesh_size_limits_apply_before_rendering() {
    let mut mesh = triangle();
    mesh.vertices
        .resize(true_engine::geometry::MAX_MESH_VERTICES + 1, Vec3::ZERO);
    assert!(mesh.validate().is_err());
    mesh = triangle();
    mesh.indices
        .resize(true_engine::geometry::MAX_MESH_INDICES + 3, 0);
    assert!(mesh.validate().is_err());
}

#[test]
fn caller_meshes_round_trip_without_modifying_project_schema() {
    let custom = triangle();
    let json = serde_json::to_string(&custom).unwrap();
    let loaded: Mesh = serde_json::from_str(&json).unwrap();
    assert_eq!(loaded, custom);
    loaded.validate().unwrap();

    let mut scene = Scene::default();
    scene.add(node(1, None, Some(Primitive::Cube))).unwrap();
    let project = Project::new(scene.clone());
    let baseline = project.to_json().unwrap();
    let meshes = HashMap::from([(1, custom)]);
    assert_eq!(scene.pick_with_meshes(Vec3::Z, -Vec3::Z, &meshes), Some(1));
    assert_eq!(project.to_json().unwrap(), baseline);
    let legacy: serde_json::Value = serde_json::from_str(&baseline).unwrap();
    assert_eq!(legacy["schema_version"], 1);
    assert_eq!(legacy["scene"]["nodes"][0]["primitive"], "Cube");
    assert!(legacy["scene"]["nodes"][0].get("mesh").is_none());
    assert_eq!(Project::from_json(&baseline).unwrap().scene, scene);
}

#[test]
fn custom_mesh_picking_respects_parent_transforms_and_nearest_hit() {
    let mut scene = Scene::default();
    let mut parent = node(1, None, None);
    parent.transform.translation = Vec3::new(2., 3., 0.);
    parent.transform.scale = Vec3::new(2., 3., 0.5);
    scene.add(parent).unwrap();
    scene.add(node(2, Some(1), None)).unwrap();
    let mut farther = node(3, None, Some(Primitive::Cube));
    farther.transform.translation = Vec3::new(2., 3., -2.);
    scene.add(farther).unwrap();
    let meshes = HashMap::from([(2, triangle())]);
    let origin = Vec3::new(2., 3., 5.);
    assert_eq!(scene.pick_with_meshes(origin, -Vec3::Z, &meshes), Some(2));
    assert_eq!(scene.pick(origin, -Vec3::Z), Some(3));
    // This ray lies inside the scaled triangle, outside its unscaled extent.
    assert_eq!(
        scene.pick_with_meshes(Vec3::new(3.5, 1., 5.), -Vec3::Z, &meshes),
        Some(2)
    );
    assert_eq!(
        scene.pick_with_meshes(Vec3::new(20., 3., 5.), -Vec3::Z, &meshes),
        None
    );
    assert_eq!(scene.pick_with_meshes(origin, Vec3::ZERO, &meshes), None);
}

#[test]
fn custom_mesh_override_replaces_primitive_and_invalid_input_cannot_panic() {
    let mut scene = Scene::default();
    scene.add(node(1, None, Some(Primitive::Cube))).unwrap();
    let mut custom = triangle();
    for position in &mut custom.vertices {
        position.x += 3.;
    }
    let mut meshes = HashMap::from([(1, custom)]);
    assert_eq!(scene.pick(Vec3::Z, -Vec3::Z), Some(1));
    assert_eq!(scene.pick_with_meshes(Vec3::Z, -Vec3::Z, &meshes), None);
    assert_eq!(
        scene.pick_with_meshes(Vec3::new(3., 0., 5.), -Vec3::Z, &meshes),
        Some(1)
    );
    meshes.get_mut(&1).unwrap().indices[0] = u32::MAX;
    assert_eq!(scene.pick_with_meshes(Vec3::Z, -Vec3::Z, &meshes), None);
    meshes = HashMap::from([(999, triangle())]);
    assert_eq!(scene.pick_with_meshes(Vec3::Z, -Vec3::Z, &meshes), None);
}
