//! Embeddable browser SDK built on True Engine's existing renderer.
pub mod document;
#[cfg(target_arch = "wasm32")]
mod viewport;
#[cfg(target_arch = "wasm32")]
pub use viewport::*;
