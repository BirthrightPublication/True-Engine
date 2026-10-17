use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, HashMap};
use true_engine::{
    geometry::Mesh, glam::Vec3, scene::Error, Material, Node, OrbitCamera, Project, Scene,
    Transform,
};

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct CameraState {
    pub target: [f32; 3],
    pub yaw: f32,
    pub pitch: f32,
    pub distance: f32,
}
impl Default for CameraState {
    fn default() -> Self {
        Self::from_camera(&OrbitCamera::default())
    }
}
impl CameraState {
    pub fn from_camera(camera: &OrbitCamera) -> Self {
        Self {
            target: camera.target.to_array(),
            yaw: camera.yaw,
            pitch: camera.pitch,
            distance: camera.distance,
        }
    }
    pub fn camera(&self) -> Result<OrbitCamera, Error> {
        if self
            .target
            .iter()
            .chain([&self.yaw, &self.pitch, &self.distance])
            .any(|n| !n.is_finite())
            || self.target.iter().any(|v| v.abs() > 1_000_000.)
            || !(-1.55..=1.55).contains(&self.pitch)
            || !(0.2..=1000.).contains(&self.distance)
        {
            return Err(Error::Invalid("invalid browser camera".into()));
        }
        Ok(OrbitCamera {
            target: Vec3::from_array(self.target),
            yaw: self.yaw,
            pitch: self.pitch,
            distance: self.distance,
        })
    }
}

/// Separate envelope: native project schema 1 remains unchanged.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Document {
    pub format: String,
    pub format_version: u32,
    pub project: Project,
    pub meshes: BTreeMap<u64, Mesh>,
    pub camera: CameraState,
}
impl Default for Document {
    fn default() -> Self {
        Self {
            format: "true-engine-web-project".into(),
            format_version: 1,
            project: Project::new(Scene::default()),
            meshes: BTreeMap::new(),
            camera: CameraState::default(),
        }
    }
}
impl Document {
    pub fn validate(&self) -> Result<(), Error> {
        if self.format != "true-engine-web-project"
            || self.format_version != 1
            || self.project.schema_version != 1
        {
            return Err(Error::Invalid(
                "unsupported browser document format/schema".into(),
            ));
        }
        self.project.scene.validate()?;
        if self.project.scene.nodes().len() > 10_000 {
            return Err(Error::Invalid("browser scene node limit".into()));
        }
        for node in self.project.scene.nodes() {
            if node.id == 0 || node.id > u32::MAX as u64 {
                return Err(Error::Invalid("browser IDs must be positive u32".into()));
            }
        }
        let mut total_indices = 0usize;
        for (id, mesh) in &self.meshes {
            mesh.validate()?;
            total_indices += mesh.indices.len();
            if !self
                .project
                .scene
                .nodes()
                .iter()
                .any(|node| node.id == *id && node.primitive.is_none())
            {
                return Err(Error::Invalid(
                    "custom mesh must reference a non-primitive scene node".into(),
                ));
            }
        }
        if total_indices > 3_000_000 {
            return Err(Error::Invalid(
                "browser mesh triangle budget exceeded".into(),
            ));
        }
        self.camera.camera()?;
        Ok(())
    }
    pub fn from_json(json: &str) -> Result<Self, Error> {
        if json.len() > 64 * 1024 * 1024 {
            return Err(Error::Invalid("browser project exceeds 64 MiB".into()));
        }
        let value: serde_json::Value = serde_json::from_str(json)?;
        let doc = if value.get("format").is_some() {
            serde_json::from_value(value)?
        } else {
            Self {
                project: Project::from_json(json)?,
                ..Default::default()
            }
        };
        doc.validate()?;
        Ok(doc)
    }
    pub fn to_json(&self) -> Result<String, Error> {
        self.validate()?;
        Ok(serde_json::to_string_pretty(self)?)
    }
    pub fn mesh_map(&self) -> HashMap<u64, Mesh> {
        self.meshes
            .iter()
            .map(|(id, mesh)| (*id, mesh.clone()))
            .collect()
    }
    pub fn add(&mut self, node: Node, mesh: Option<Mesh>) -> Result<(), Error> {
        let mut next = self.clone();
        if let Some(mesh) = mesh {
            next.meshes.insert(node.id, mesh);
        }
        next.project.scene.add(node)?;
        next.validate()?;
        *self = next;
        Ok(())
    }
    pub fn set_node(
        &mut self,
        id: u64,
        transform: Option<Transform>,
        material: Option<Material>,
    ) -> Result<(), Error> {
        let mut nodes = self.project.scene.nodes().to_vec();
        let node = nodes
            .iter_mut()
            .find(|node| node.id == id)
            .ok_or_else(|| Error::Invalid("unknown browser node".into()))?;
        if let Some(value) = transform {
            node.transform = value;
        }
        if let Some(value) = material {
            node.material = value;
        }
        let scene = serde_json::from_value(serde_json::json!({"nodes": nodes}))?;
        let mut next = self.clone();
        next.project.scene = scene;
        next.validate()?;
        *self = next;
        Ok(())
    }
}
