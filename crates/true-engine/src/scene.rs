use glam::{Mat4, Quat, Vec3};
use serde::{Deserialize, Serialize};
use std::collections::HashSet;

pub type NodeId = u64;
#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq)]
pub enum Primitive {
    Cube,
    Plane,
    Sphere,
}
#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq)]
pub struct Material {
    pub color: [f32; 4],
}
impl Default for Material {
    fn default() -> Self {
        Self {
            color: [0.3, 0.65, 0.9, 1.0],
        }
    }
}
#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq)]
pub struct Transform {
    pub translation: Vec3,
    pub rotation: Quat,
    pub scale: Vec3,
}
impl Default for Transform {
    fn default() -> Self {
        Self {
            translation: Vec3::ZERO,
            rotation: Quat::IDENTITY,
            scale: Vec3::ONE,
        }
    }
}
impl Transform {
    pub fn matrix(self) -> Mat4 {
        Mat4::from_scale_rotation_translation(self.scale, self.rotation, self.translation)
    }
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct Node {
    pub id: NodeId,
    pub parent: Option<NodeId>,
    pub name: String,
    pub transform: Transform,
    pub primitive: Option<Primitive>,
    pub material: Material,
}
#[derive(Clone, Debug, Default, Serialize, PartialEq)]
pub struct Scene {
    nodes: Vec<Node>,
}
impl<'de> Deserialize<'de> for Scene {
    fn deserialize<D: serde::Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        #[derive(Deserialize)]
        struct RawScene {
            nodes: Vec<Node>,
        }
        let scene = Self {
            nodes: RawScene::deserialize(deserializer)?.nodes,
        };
        scene.validate().map_err(serde::de::Error::custom)?;
        Ok(scene)
    }
}
#[derive(Debug, thiserror::Error)]
pub enum Error {
    #[error("invalid scene: {0}")]
    Invalid(String),
    #[error("unsupported project schema {0}")]
    Schema(u32),
    #[error(transparent)]
    Json(#[from] serde_json::Error),
}
impl Scene {
    pub fn nodes(&self) -> &[Node] {
        &self.nodes
    }
    pub fn add(&mut self, node: Node) -> Result<(), Error> {
        self.nodes.push(node);
        if let Err(e) = self.validate() {
            self.nodes.pop();
            return Err(e);
        }
        Ok(())
    }
    pub fn validate(&self) -> Result<(), Error> {
        let ids: HashSet<_> = self.nodes.iter().map(|n| n.id).collect();
        if ids.len() != self.nodes.len() {
            return Err(Error::Invalid("duplicate ID".into()));
        }
        for n in &self.nodes {
            if !n.transform.translation.is_finite()
                || !n.transform.scale.is_finite()
                || n.transform.scale.abs().min_element() < 1e-6
                || !n.transform.rotation.is_finite()
                || (n.transform.rotation.length_squared() - 1.).abs() > 0.001
                || n.material
                    .color
                    .iter()
                    .any(|c| !c.is_finite() || !(0.0..=1.0).contains(c))
            {
                return Err(Error::Invalid("invalid transform/material".into()));
            }
            let mut seen = HashSet::new();
            let mut current = Some(n.id);
            while let Some(id) = current {
                if !seen.insert(id) {
                    return Err(Error::Invalid("cycle".into()));
                }
                current = self
                    .nodes
                    .iter()
                    .find(|v| v.id == id)
                    .ok_or_else(|| Error::Invalid("missing parent".into()))?
                    .parent;
            }
        }
        Ok(())
    }
    pub fn world_matrix(&self, mut id: NodeId) -> Option<Mat4> {
        let mut world = Mat4::IDENTITY;
        for _ in 0..self.nodes.len() {
            let node = self.nodes.iter().find(|n| n.id == id)?;
            world = node.transform.matrix() * world;
            match node.parent {
                Some(parent) => id = parent,
                None => return Some(world),
            }
        }
        None
    }
    /// Exact nearest triangle intersection, including parent transforms and nonuniform scale.
    pub fn pick(&self, origin: Vec3, direction: Vec3) -> Option<NodeId> {
        let direction = direction.try_normalize()?;
        let mut closest = f32::INFINITY;
        let mut hit = None;
        for n in &self.nodes {
            if let Some(p) = n.primitive {
                let mesh = crate::geometry::mesh(p);
                let world = self.world_matrix(n.id)?;
                for t in mesh.indices.chunks_exact(3) {
                    let a = world.transform_point3(mesh.vertices[t[0] as usize]);
                    let b = world.transform_point3(mesh.vertices[t[1] as usize]);
                    let c = world.transform_point3(mesh.vertices[t[2] as usize]);
                    let e1 = b - a;
                    let e2 = c - a;
                    let h = direction.cross(e2);
                    let det = e1.dot(h);
                    if det.abs() < 1e-7 {
                        continue;
                    }
                    let inv = 1. / det;
                    let s = origin - a;
                    let u = inv * s.dot(h);
                    if !(0.0..=1.0).contains(&u) {
                        continue;
                    }
                    let q = s.cross(e1);
                    let v = inv * direction.dot(q);
                    if v < 0. || u + v > 1. {
                        continue;
                    }
                    let distance = inv * e2.dot(q);
                    if distance >= 0. && distance < closest {
                        closest = distance;
                        hit = Some(n.id);
                    }
                }
            }
        }
        hit
    }
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct Project {
    pub schema_version: u32,
    pub scene: Scene,
}
impl Project {
    pub fn new(scene: Scene) -> Self {
        Self {
            schema_version: 1,
            scene,
        }
    }
    pub fn to_json(&self) -> Result<String, Error> {
        if self.schema_version != 1 {
            return Err(Error::Schema(self.schema_version));
        }
        self.scene.validate()?;
        Ok(serde_json::to_string_pretty(self)?)
    }
    pub fn from_json(s: &str) -> Result<Self, Error> {
        let p: Self = serde_json::from_str(s)?;
        if p.schema_version != 1 {
            return Err(Error::Schema(p.schema_version));
        }
        p.scene.validate()?;
        Ok(p)
    }
}
