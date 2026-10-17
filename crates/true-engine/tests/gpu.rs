use true_engine::{glam::Vec3, render::Renderer, *};
#[test]
fn renders_visible_geometry_and_selection() {
    pollster::block_on(async {
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
        let mut r = Renderer::new(&device, wgpu::TextureFormat::Rgba8Unorm, 64, 64);
        let mut scene = Scene::default();
        scene
            .add(Node {
                id: 1,
                parent: None,
                name: "cube".into(),
                transform: Transform::default(),
                primitive: Some(Primitive::Cube),
                material: Material::default(),
            })
            .unwrap();
        let camera = OrbitCamera {
            target: Vec3::ZERO,
            yaw: 0.,
            pitch: 0.,
            distance: 3.,
        };
        let mut centers = Vec::new();
        for selected in [None, Some(1)] {
            r.upload(&device, &scene, selected);
            let read = device.create_buffer(&wgpu::BufferDescriptor {
                label: None,
                size: 64 * 256,
                usage: wgpu::BufferUsages::COPY_DST | wgpu::BufferUsages::MAP_READ,
                mapped_at_creation: false,
            });
            let mut enc = device.create_command_encoder(&Default::default());
            r.draw(
                &queue,
                &mut enc,
                &target.create_view(&Default::default()),
                &camera,
                1.,
            );
            enc.copy_texture_to_buffer(
                target.as_image_copy(),
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
            queue.submit(Some(enc.finish()));
            let (tx, rx) = std::sync::mpsc::channel();
            read.slice(..)
                .map_async(wgpu::MapMode::Read, move |v| tx.send(v).unwrap());
            device.poll(wgpu::Maintain::Wait);
            rx.recv().unwrap().unwrap();
            let bytes = read.slice(..).get_mapped_range();
            let center = &bytes[32 * 256 + 32 * 4..32 * 256 + 32 * 4 + 4];
            assert!(center[0] > 20 || center[1] > 20);
            assert!(bytes[0] < 20);
            centers.push(center.to_vec());
            drop(bytes);
            read.unmap();
        }
        assert_ne!(centers[0], centers[1]);
    });
}
