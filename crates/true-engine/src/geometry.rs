use crate::Primitive;
use glam::Vec3;
use serde::{Deserialize, Serialize};

pub const MAX_MESH_VERTICES: usize = 1_000_000;
pub const MAX_MESH_INDICES: usize = 3_000_000;

/// Caller-provided indexed triangles in a node's local coordinate system.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct Mesh {
    pub vertices: Vec<Vec3>,
    pub indices: Vec<u32>,
}
impl Mesh {
    /// Check size, finite positions and complete, in-range triangle indices.
    ///
    /// Deserialization alone does not validate a mesh. Render upload validates
    /// it before changing retained GPU geometry.
    pub fn validate(&self) -> Result<(), crate::scene::Error> {
        if self.vertices.is_empty()
            || self.vertices.len() > MAX_MESH_VERTICES
            || self.indices.is_empty()
            || self.indices.len() > MAX_MESH_INDICES
            || self.indices.len() % 3 != 0
        {
            return Err(crate::scene::Error::Invalid(
                "mesh must contain bounded indexed triangles".into(),
            ));
        }
        if self.vertices.iter().any(|position| !position.is_finite()) {
            return Err(crate::scene::Error::Invalid(
                "mesh positions must be finite".into(),
            ));
        }
        if self
            .indices
            .iter()
            .any(|&index| index as usize >= self.vertices.len())
        {
            return Err(crate::scene::Error::Invalid(
                "mesh index is outside the vertex array".into(),
            ));
        }
        Ok(())
    }
}
pub fn mesh(p: Primitive) -> Mesh {
    match p {
        Primitive::Cube => Mesh {
            vertices: vec![
                Vec3::new(-0.5, -0.5, -0.5),
                Vec3::new(0.5, -0.5, -0.5),
                Vec3::new(0.5, 0.5, -0.5),
                Vec3::new(-0.5, 0.5, -0.5),
                Vec3::new(-0.5, -0.5, 0.5),
                Vec3::new(0.5, -0.5, 0.5),
                Vec3::new(0.5, 0.5, 0.5),
                Vec3::new(-0.5, 0.5, 0.5),
            ],
            indices: vec![
                0, 2, 1, 0, 3, 2, 4, 5, 6, 4, 6, 7, 0, 1, 5, 0, 5, 4, 3, 7, 6, 3, 6, 2, 1, 2, 6, 1,
                6, 5, 0, 4, 7, 0, 7, 3,
            ],
        },
        Primitive::Plane => Mesh {
            vertices: vec![
                Vec3::new(-0.5, 0., -0.5),
                Vec3::new(0.5, 0., -0.5),
                Vec3::new(0.5, 0., 0.5),
                Vec3::new(-0.5, 0., 0.5),
            ],
            indices: vec![0, 2, 1, 0, 3, 2],
        },
        Primitive::Sphere => {
            let mut vertices = Vec::new();
            let mut indices = Vec::new();
            for y in 0..=16 {
                for x in 0..=24 {
                    let phi = y as f32 / 16. * std::f32::consts::PI;
                    let theta = x as f32 / 24. * std::f32::consts::TAU;
                    vertices.push(
                        0.5 * Vec3::new(
                            phi.sin() * theta.cos(),
                            phi.cos(),
                            phi.sin() * theta.sin(),
                        ),
                    );
                }
            }
            for y in 0..16 {
                for x in 0..24 {
                    let a = y * 25 + x;
                    let b = a + 25;
                    indices.extend([a, b, a + 1, a + 1, b, b + 1]);
                }
            }
            Mesh { vertices, indices }
        }
    }
}
