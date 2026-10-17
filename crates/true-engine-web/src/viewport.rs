use crate::document::{CameraState, Document};
use std::collections::HashMap;
use true_engine::{
    geometry::Mesh, glam::Vec3, render::Renderer, Material, Node, OrbitCamera, Transform,
};
use wasm_bindgen::prelude::*;
use web_sys::HtmlCanvasElement;

fn error(value: impl std::fmt::Display) -> JsValue {
    JsValue::from_str(&value.to_string())
}
fn finite(values: &[f32]) -> Result<(), JsValue> {
    if values.iter().any(|v| !v.is_finite() || v.abs() > 100_000.) {
        return Err(error("camera input must be finite and bounded"));
    }
    Ok(())
}

#[wasm_bindgen]
pub struct RawViewport {
    // Keep adapter/instance JS objects alive for the browser device lifetime.
    _instance: wgpu::Instance,
    _adapter: wgpu::Adapter,
    surface: wgpu::Surface<'static>,
    device: wgpu::Device,
    queue: wgpu::Queue,
    config: wgpu::SurfaceConfiguration,
    renderer: Renderer,
    document: Document,
    meshes: HashMap<u64, Mesh>,
    camera: OrbitCamera,
    backend: String,
}

/// No start hook: the caller owns the canvas and application lifecycle.
#[wasm_bindgen(js_name = createRawViewport)]
pub async fn create_raw_viewport(
    canvas: HtmlCanvasElement,
    backend: String,
) -> Result<RawViewport, JsValue> {
    console_error_panic_hook::set_once();
    if canvas.width() > 8192 || canvas.height() > 8192 {
        return Err(error("initial canvas dimensions exceed 8192"));
    }
    if !["auto", "webgpu", "webgl2"].contains(&backend.as_str()) {
        return Err(error("backend must be auto, webgpu or webgl2"));
    }
    let mut gpu = None;
    if backend != "webgl2" {
        let instance = wgpu::Instance::new(wgpu::InstanceDescriptor {
            backends: wgpu::Backends::BROWSER_WEBGPU,
            ..Default::default()
        });
        if let Some(adapter) = instance
            .request_adapter(&wgpu::RequestAdapterOptions::default())
            .await
        {
            gpu = Some((instance, adapter));
        }
    }
    let (instance, surface, adapter, actual_backend) = if let Some((instance, adapter)) = gpu {
        let surface = instance
            .create_surface(wgpu::SurfaceTarget::Canvas(canvas.clone()))
            .map_err(error)?;
        (instance, surface, adapter, "webgpu")
    } else {
        if backend == "webgpu" {
            return Err(error("WebGPU adapter unavailable"));
        }
        let instance = wgpu::Instance::new(wgpu::InstanceDescriptor {
            backends: wgpu::Backends::GL,
            ..Default::default()
        });
        let surface = instance
            .create_surface(wgpu::SurfaceTarget::Canvas(canvas.clone()))
            .map_err(error)?;
        let adapter = instance
            .request_adapter(&wgpu::RequestAdapterOptions {
                compatible_surface: Some(&surface),
                ..Default::default()
            })
            .await
            .ok_or_else(|| error("WebGL2 adapter unavailable"))?;
        (instance, surface, adapter, "webgl2")
    };
    let (device, queue) = adapter
        .request_device(
            &wgpu::DeviceDescriptor {
                label: Some("True Engine browser SDK"),
                required_features: wgpu::Features::empty(),
                required_limits: wgpu::Limits::downlevel_webgl2_defaults()
                    .using_resolution(adapter.limits()),
            },
            None,
        )
        .await
        .map_err(error)?;
    let max_dimension = device.limits().max_texture_dimension_2d.min(8192);
    if canvas.width().max(1) > max_dimension || canvas.height().max(1) > max_dimension {
        device.destroy();
        return Err(error(format!(
            "initial canvas dimensions exceed {max_dimension}"
        )));
    }
    let config = surface
        .get_default_config(&adapter, canvas.width().max(1), canvas.height().max(1))
        .ok_or_else(|| error("canvas surface unsupported"))?;
    surface.configure(&device, &config);
    let renderer = Renderer::new(&device, config.format, config.width, config.height);
    Ok(RawViewport {
        _instance: instance,
        _adapter: adapter,
        surface,
        device,
        queue,
        config,
        renderer,
        document: Document::default(),
        meshes: HashMap::new(),
        camera: OrbitCamera::default(),
        backend: actual_backend.into(),
    })
}
#[wasm_bindgen]
impl RawViewport {
    /// Explicitly destroy the WebGPU device; dropping browser JS handles alone
    /// does not release a device retained by a host-owned canvas context.
    pub fn destroy(&self) {
        self.device.destroy();
    }
    #[wasm_bindgen(getter)]
    pub fn backend(&self) -> String {
        self.backend.clone()
    }
    pub fn resize(&mut self, width: u32, height: u32) -> Result<(), JsValue> {
        let max = self.device.limits().max_texture_dimension_2d;
        if width == 0 || height == 0 || width > max || height > max {
            return Err(error(format!("viewport dimensions must be 1..{max}")));
        }
        self.config.width = width;
        self.config.height = height;
        self.surface.configure(&self.device, &self.config);
        self.renderer.resize(&self.device, width, height);
        Ok(())
    }
    pub fn render(&mut self) -> Result<(), JsValue> {
        let frame = match self.surface.get_current_texture() {
            Ok(frame) => frame,
            Err(wgpu::SurfaceError::Lost | wgpu::SurfaceError::Outdated) => {
                self.surface.configure(&self.device, &self.config);
                self.surface.get_current_texture().map_err(error)?
            }
            Err(e) => return Err(error(e)),
        };
        let view = frame.texture.create_view(&Default::default());
        let mut encoder = self.device.create_command_encoder(&Default::default());
        self.renderer.draw(
            &self.queue,
            &mut encoder,
            &view,
            &self.camera,
            self.config.width as f32 / self.config.height as f32,
        );
        self.queue.submit(Some(encoder.finish()));
        frame.present();
        Ok(())
    }
    #[wasm_bindgen(js_name = addPrimitive)]
    pub fn add_primitive(&mut self, node_json: &str) -> Result<(), JsValue> {
        let node: Node = serde_json::from_str(node_json).map_err(error)?;
        if node.primitive.is_none() {
            return Err(error("addPrimitive requires Cube, Plane or Sphere"));
        }
        let mut next = self.document.clone();
        next.add(node, None).map_err(error)?;
        self.upload_document(next)
    }
    #[wasm_bindgen(js_name = loadMesh)]
    pub fn load_mesh(
        &mut self,
        node_json: &str,
        positions: &[f32],
        indices: &[u32],
    ) -> Result<(), JsValue> {
        if positions.len() % 3 != 0 {
            return Err(error("positions must contain XYZ triples"));
        }
        let node: Node = serde_json::from_str(node_json).map_err(error)?;
        if node.primitive.is_some() {
            return Err(error("loadMesh requires a non-primitive node"));
        }
        let mesh = Mesh {
            vertices: positions
                .chunks_exact(3)
                .map(|v| Vec3::new(v[0], v[1], v[2]))
                .collect(),
            indices: indices.to_vec(),
        };
        let mut next = self.document.clone();
        next.add(node, Some(mesh)).map_err(error)?;
        self.upload_document(next)
    }
    #[wasm_bindgen(js_name = setMaterial)]
    pub fn set_material(&mut self, id: u32, json: &str) -> Result<(), JsValue> {
        let material: Material = serde_json::from_str(json).map_err(error)?;
        let mut next = self.document.clone();
        next.set_node(id as u64, None, Some(material))
            .map_err(error)?;
        self.upload_document(next)
    }
    #[wasm_bindgen(js_name = setTransform)]
    pub fn set_transform(&mut self, id: u32, json: &str) -> Result<(), JsValue> {
        let transform: Transform = serde_json::from_str(json).map_err(error)?;
        let mut next = self.document.clone();
        next.set_node(id as u64, Some(transform), None)
            .map_err(error)?;
        self.upload_document(next)
    }
    pub fn orbit(&mut self, dx: f32, dy: f32) -> Result<(), JsValue> {
        finite(&[dx, dy])?;
        self.camera.orbit(dx, dy);
        Ok(())
    }
    pub fn pan(&mut self, dx: f32, dy: f32) -> Result<(), JsValue> {
        finite(&[dx, dy])?;
        let mut camera = self.camera.clone();
        camera.pan(dx, dy);
        self.camera = CameraState::from_camera(&camera).camera().map_err(error)?;
        Ok(())
    }
    pub fn zoom(&mut self, delta: f32) -> Result<(), JsValue> {
        finite(&[delta])?;
        self.camera.zoom(delta);
        Ok(())
    }
    #[wasm_bindgen(js_name = resetCamera)]
    pub fn reset_camera(&mut self) {
        self.camera = OrbitCamera::default();
    }
    #[wasm_bindgen(js_name = getCamera)]
    pub fn get_camera(&self) -> String {
        serde_json::to_string(&CameraState::from_camera(&self.camera)).unwrap()
    }
    #[wasm_bindgen(js_name = setCamera)]
    pub fn set_camera(&mut self, json: &str) -> Result<(), JsValue> {
        self.camera = serde_json::from_str::<CameraState>(json)
            .map_err(error)?
            .camera()
            .map_err(error)?;
        Ok(())
    }
    pub fn pick(&self, x: f32, y: f32) -> Result<Option<u32>, JsValue> {
        finite(&[x, y])?;
        let (origin, direction) =
            self.camera
                .ray(x, y, self.config.width as f32, self.config.height as f32);
        Ok(self
            .document
            .project
            .scene
            .pick_with_meshes(origin, direction, &self.meshes)
            .map(|id| id as u32))
    }
    #[wasm_bindgen(js_name = exportProject)]
    pub fn export_project(&self) -> Result<String, JsValue> {
        let mut doc = self.document.clone();
        doc.camera = CameraState::from_camera(&self.camera);
        doc.to_json().map_err(error)
    }
    #[wasm_bindgen(js_name = importProject)]
    pub fn import_project(&mut self, json: &str) -> Result<(), JsValue> {
        let doc = Document::from_json(json).map_err(error)?;
        let camera = doc.camera.camera().map_err(error)?;
        let meshes = doc.mesh_map();
        self.renderer
            .upload_with_meshes(&self.device, &doc.project.scene, None, &meshes)
            .map_err(error)?;
        self.document = doc;
        self.camera = camera;
        self.meshes = meshes;
        Ok(())
    }
}
impl RawViewport {
    fn upload_document(&mut self, document: Document) -> Result<(), JsValue> {
        let meshes = document.mesh_map();
        self.renderer
            .upload_with_meshes(&self.device, &document.project.scene, None, &meshes)
            .map_err(error)?;
        self.meshes = meshes;
        self.document = document;
        Ok(())
    }
}
