use crate::Primitive;
use glam::Vec3;
pub struct Mesh {
    pub vertices: Vec<Vec3>,
    pub indices: Vec<u32>,
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
