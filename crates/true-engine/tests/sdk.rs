use true_engine::{glam::Vec3, *};
fn node(id: u64, parent: Option<u64>, position: Vec3) -> Node {
    Node {
        id,
        parent,
        name: format!("node {id}"),
        transform: Transform {
            translation: position,
            ..Default::default()
        },
        primitive: Some(Primitive::Cube),
        material: Material::default(),
    }
}
#[test]
fn hierarchy_roundtrip_and_picking() {
    let mut s = Scene::default();
    s.add(node(1, None, Vec3::new(2., 0., 0.))).unwrap();
    s.add(node(2, Some(1), Vec3::new(0., 2., 0.))).unwrap();
    assert_eq!(
        s.world_matrix(2).unwrap().transform_point3(Vec3::ZERO),
        Vec3::new(2., 2., 0.)
    );
    assert_eq!(s.pick(Vec3::new(2., 2., 5.), -Vec3::Z), Some(2));
    let json = Project::new(s.clone()).to_json().unwrap();
    assert_eq!(Project::from_json(&json).unwrap().scene, s);
    assert!(
        Project::from_json(&json.replace("\"schema_version\": 1", "\"schema_version\": 2"))
            .is_err()
    );
}
#[test]
fn invalid_edits_are_atomic() {
    let mut s = Scene::default();
    s.add(node(1, None, Vec3::ZERO)).unwrap();
    assert!(s.add(node(1, None, Vec3::ZERO)).is_err());
    assert!(s.add(node(2, Some(99), Vec3::ZERO)).is_err());
    assert!(s.add(node(2, Some(2), Vec3::ZERO)).is_err());
    assert_eq!(s.nodes().len(), 1);
}
#[test]
fn nearest_and_miss() {
    let mut s = Scene::default();
    s.add(node(1, None, Vec3::ZERO)).unwrap();
    s.add(node(2, None, Vec3::new(0., 0., 2.))).unwrap();
    assert_eq!(s.pick(Vec3::new(0., 0., 5.), -Vec3::Z), Some(2));
    assert_eq!(s.pick(Vec3::new(10., 0., 5.), -Vec3::Z), None);
    assert_eq!(s.pick(Vec3::ZERO, Vec3::ZERO), None);
}
#[test]
fn camera_controls_and_ray() {
    let mut c = OrbitCamera {
        yaw: 0.,
        pitch: 0.,
        ..Default::default()
    };
    let (o, d) = c.ray(400., 300., 800., 600.);
    assert!(d.dot(-Vec3::Z) > 0.999);
    assert!(o.z > 0.);
    c.orbit(100., 10000.);
    assert!(c.pitch < 1.56);
    c.zoom(10000.);
    assert_eq!(c.distance, 0.2);
    c.zoom(-10000.);
    assert_eq!(c.distance, 1000.);
    let old = c.target;
    c.pan(20., 10.);
    assert_ne!(old, c.target);
}
#[test]
fn primitive_indices_are_valid() {
    for p in [Primitive::Cube, Primitive::Plane, Primitive::Sphere] {
        let m = true_engine::geometry::mesh(p);
        assert!(m.indices.len() >= 6);
        assert!(m.indices.iter().all(|&i| (i as usize) < m.vertices.len()));
        assert!(m.vertices.iter().all(|v| v.is_finite()));
    }
}
#[test]
fn reject_malformed_projects() {
    assert!(Project::from_json(r#"{"schema_version":1,"scene":{"nodes":[{"id":1,"parent":1,"name":"cycle","transform":{"translation":[0,0,0],"rotation":[0,0,0,1],"scale":[1,1,1]},"primitive":"Cube","material":{"color":[1,1,1,1]}}]}}"#).is_err());
}

#[test]
fn picks_each_primitive_under_scaled_parent() {
    for p in [Primitive::Cube, Primitive::Plane, Primitive::Sphere] {
        let mut scene = Scene::default();
        let mut parent = node(1, None, Vec3::new(2., 0., 0.));
        parent.primitive = None;
        parent.transform.scale = Vec3::new(2., 3., 0.5);
        scene.add(parent).unwrap();
        let mut child = node(2, Some(1), Vec3::ZERO);
        child.primitive = Some(p);
        scene.add(child).unwrap();
        assert_eq!(scene.pick(Vec3::new(2., 5., 0.), -Vec3::Y), Some(2));
    }
}

#[test]
fn direct_scene_deserialization_cannot_bypass_validation() {
    let mut s = Scene::default();
    s.add(node(1, None, Vec3::ZERO)).unwrap();
    let mut raw = serde_json::to_value(&s).unwrap();
    raw["nodes"][0]["parent"] = serde_json::json!(1);
    assert!(serde_json::from_value::<Scene>(raw).is_err());
    assert_eq!(s.world_matrix(99), None);
}
