use std::{collections::HashMap, sync::Mutex};
use true_engine::{geometry::Mesh, glam::Vec3, render::Renderer, *};

// Software EGL displays are process-shared; keep their teardown out of other tests.
static GPU_TEST_LOCK: Mutex<()> = Mutex::new(());

struct Gpu {
    device: wgpu::Device,
    queue: wgpu::Queue,
    target: wgpu::Texture,
    renderer: Renderer,
}
impl Gpu {
    async fn new() -> Self {
        let instance = wgpu::Instance::new(wgpu::InstanceDescriptor {
            backends: wgpu::Backends::GL,
            ..Default::default()
        });
        let adapter = instance
            .request_adapter(&wgpu::RequestAdapterOptions::default())
            .await
            .expect("GPU smoke test requires EGL/OpenGL adapter");
        let (device, queue) = adapter
            .request_device(
                &wgpu::DeviceDescriptor {
                    required_limits: wgpu::Limits::downlevel_webgl2_defaults(),
                    ..Default::default()
                },
                None,
            )
            .await
            .unwrap();
        let target = device.create_texture(&wgpu::TextureDescriptor {
            label: None,
            size: wgpu::Extent3d {
                width: 64,
                height: 64,
                depth_or_array_layers: 1,
            },
            mip_level_count: 1,
            sample_count: 1,
            dimension: wgpu::TextureDimension::D2,
            format: wgpu::TextureFormat::Rgba8Unorm,
            usage: wgpu::TextureUsages::RENDER_ATTACHMENT | wgpu::TextureUsages::COPY_SRC,
            view_formats: &[],
        });
        let renderer = Renderer::new(&device, wgpu::TextureFormat::Rgba8Unorm, 64, 64);
        Self {
            device,
            queue,
            target,
            renderer,
        }
    }
    fn image(&self) -> Vec<u8> {
        let camera = OrbitCamera {
            target: Vec3::ZERO,
            yaw: 0.,
            pitch: 0.,
            distance: 3.,
        };
        let read = self.device.create_buffer(&wgpu::BufferDescriptor {
            label: None,
            size: 64 * 256,
            usage: wgpu::BufferUsages::COPY_DST | wgpu::BufferUsages::MAP_READ,
            mapped_at_creation: false,
        });
        let mut enc = self.device.create_command_encoder(&Default::default());
        self.renderer.draw(
            &self.queue,
            &mut enc,
            &self.target.create_view(&Default::default()),
            &camera,
            1.,
        );
        enc.copy_texture_to_buffer(
            self.target.as_image_copy(),
            wgpu::ImageCopyBuffer {
                buffer: &read,
                layout: wgpu::ImageDataLayout {
                    offset: 0,
                    bytes_per_row: Some(256),
                    rows_per_image: Some(64),
                },
            },
            wgpu::Extent3d {
                width: 64,
                height: 64,
                depth_or_array_layers: 1,
            },
        );
        self.queue.submit(Some(enc.finish()));
        let (tx, rx) = std::sync::mpsc::channel();
        read.slice(..)
            .map_async(wgpu::MapMode::Read, move |v| tx.send(v).unwrap());
        self.device.poll(wgpu::Maintain::Wait);
        rx.recv().unwrap().unwrap();
        let bytes = read.slice(..).get_mapped_range().to_vec();
        read.unmap();
        bytes
    }
}
fn center(bytes: &[u8]) -> &[u8] {
    &bytes[32 * 256 + 32 * 4..32 * 256 + 32 * 4 + 4]
}
fn node(primitive: Option<Primitive>) -> Node {
    Node {
        id: 1,
        parent: None,
        name: "geometry".into(),
        transform: Transform::default(),
        primitive,
        material: Material::default(),
    }
}

#[test]
fn renders_visible_geometry_and_selection() {
    let _guard = GPU_TEST_LOCK.lock().unwrap();
    pollster::block_on(async {
        let mut gpu = Gpu::new().await;
        let mut scene = Scene::default();
        scene.add(node(Some(Primitive::Cube))).unwrap();
        let mut centers = Vec::new();
        for selected in [None, Some(1)] {
            gpu.renderer.upload(&gpu.device, &scene, selected);
            let bytes = gpu.image();
            let center = center(&bytes);
            assert!(center[0] > 20 || center[1] > 20);
            assert!(bytes[0] < 20);
            centers.push(center.to_vec());
        }
        assert_ne!(centers[0], centers[1]);
    });
}

#[test]
fn custom_mesh_renders_and_failed_upload_preserves_gpu_geometry() {
    let _guard = GPU_TEST_LOCK.lock().unwrap();
    pollster::block_on(async {
        let mut gpu = Gpu::new().await;
        let mut scene = Scene::default();
        let mut custom = node(None);
        custom.material.color = [1., 0.1, 0.1, 1.];
        scene.add(custom).unwrap();
        let mesh = Mesh {
            vertices: vec![
                Vec3::new(-1., -1., 0.),
                Vec3::new(1., -1., 0.),
                Vec3::new(0., 1., 0.),
            ],
            indices: vec![0, 1, 2],
        };
        let meshes = HashMap::from([(1, mesh.clone())]);
        gpu.renderer
            .upload_with_meshes(&gpu.device, &scene, None, &meshes)
            .unwrap();
        let original = gpu.image();
        let pixel = center(&original);
        assert!(pixel[0] > 100 && pixel[1] < 30 && pixel[2] < 30);
        assert!(original[0] < 20);
        // The node has no primitive; these visible pixels come from its custom mesh.
        let mut invalid = mesh.clone();
        invalid.indices[2] = 99;
        assert!(gpu
            .renderer
            .upload_with_meshes(&gpu.device, &scene, None, &HashMap::from([(1, invalid)]))
            .is_err());
        assert_eq!(gpu.image(), original);
        assert!(gpu
            .renderer
            .upload_with_meshes(&gpu.device, &scene, None, &HashMap::from([(99, mesh)]))
            .is_err());
        assert_eq!(gpu.image(), original);
    });
}
