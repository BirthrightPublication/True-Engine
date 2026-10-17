#![doc = include_str!("../../../docs/SDK-0.1.md")]
//! Application-agnostic scene, camera, project and GPU primitives. See docs/SDK-0.1.md.
pub mod camera;
pub mod geometry;
pub mod render;
pub mod scene;
pub use camera::OrbitCamera;
pub use glam;
pub use scene::{Material, Node, NodeId, Primitive, Project, Scene, Transform};
