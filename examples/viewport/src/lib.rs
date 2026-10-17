use std::sync::Arc;
#[cfg(not(target_arch = "wasm32"))]
use true_engine::Project;
use true_engine::{
    glam::Vec3, render::Renderer, Material, Node, OrbitCamera, Primitive, Scene, Transform,
};
#[cfg(not(target_arch = "wasm32"))]
use winit::keyboard::{KeyCode, PhysicalKey};
use winit::{event::*, event_loop::EventLoop, window::WindowBuilder};

#[cfg(target_arch = "wasm32")]
#[wasm_bindgen::prelude::wasm_bindgen(start)]
pub fn web_start() {
    console_error_panic_hook::set_once();
    wasm_bindgen_futures::spawn_local(run());
}

pub async fn run() {
    let events = EventLoop::new().unwrap();
    let window=Arc::new(WindowBuilder::new().with_title(format!("TRUE ENGINE {} | Left: orbit · Right: pan · Wheel: zoom · Click: select · S/L: project", env!("CARGO_PKG_VERSION"))).build(&events).unwrap());
    #[cfg(target_arch = "wasm32")]
    {
        use winit::platform::web::WindowExtWebSys;
        let canvas = window.canvas().unwrap();
        web_sys::window()
            .unwrap()
            .document()
            .unwrap()
            .body()
            .unwrap()
            .append_child(&canvas)
            .unwrap();
    }
    let instance = wgpu::Instance::default();
    let surface = instance.create_surface(window.clone()).unwrap();
    let adapter = instance
        .request_adapter(&wgpu::RequestAdapterOptions {
            compatible_surface: Some(&surface),
            ..Default::default()
        })
        .await
        .expect("No compatible GPU adapter");
    let (device, queue) = adapter
        .request_device(
            &wgpu::DeviceDescriptor {
                label: None,
                required_features: wgpu::Features::empty(),
                required_limits: wgpu::Limits::downlevel_webgl2_defaults()
                    .using_resolution(adapter.limits()),
            },
            None,
        )
        .await
        .unwrap();
    let size = window.inner_size();
    let mut config = surface
        .get_default_config(&adapter, size.width.max(1), size.height.max(1))
        .unwrap();
    surface.configure(&device, &config);
    let mut renderer = Renderer::new(&device, config.format, config.width, config.height);
    let mut scene = Scene::default();
    for (id, p, x) in [
        (1, Primitive::Cube, -1.3),
        (2, Primitive::Sphere, 0.),
        (3, Primitive::Plane, 1.3),
    ] {
        scene
            .add(Node {
                id,
                parent: None,
                name: format!("{p:?}"),
                transform: Transform {
                    translation: Vec3::new(x, 0., 0.),
                    ..Default::default()
                },
                primitive: Some(p),
                material: Material::default(),
            })
            .unwrap();
    }
    renderer.upload(&device, &scene, None);
    let mut camera = OrbitCamera::default();
    let mut cursor = (0., 0.);
    let mut press = cursor;
    let mut left = false;
    let mut right = false;
    let mut moved = false;
    let mut suspended = false;
    let handler = move |event: Event<()>, el: &winit::event_loop::EventLoopWindowTarget<()>| {
        if let Event::WindowEvent { window_id, event } = event {
            if window_id != window.id() {
                return;
            }
            match event {
                WindowEvent::CloseRequested => el.exit(),
                WindowEvent::Resized(s) => {
                    suspended = s.width == 0 || s.height == 0;
                    if !suspended {
                        config.width = s.width;
                        config.height = s.height;
                        surface.configure(&device, &config);
                        renderer.resize(&device, s.width, s.height);
                        window.request_redraw();
                    }
                }
                WindowEvent::CursorMoved { position, .. } => {
                    let next = (position.x as f32, position.y as f32);
                    let dx = next.0 - cursor.0;
                    let dy = next.1 - cursor.1;
                    if (next.0 - press.0).abs() + (next.1 - press.1).abs() > 4. {
                        moved = true;
                    }
                    if left {
                        camera.orbit(dx, dy);
                    }
                    if right {
                        camera.pan(dx, dy);
                    }
                    cursor = next;
                    window.request_redraw();
                }
                WindowEvent::MouseInput { state, button, .. } => {
                    let down = state == ElementState::Pressed;
                    match button {
                        MouseButton::Left => {
                            left = down;
                            if down {
                                press = cursor;
                                moved = false;
                            } else if !moved {
                                let (o, d) = camera.ray(
                                    cursor.0,
                                    cursor.1,
                                    config.width as f32,
                                    config.height as f32,
                                );
                                let selected = scene.pick(o, d);
                                renderer.upload(&device, &scene, selected);
                                window.set_title(&format!(
                                    "TRUE ENGINE {} | Selected: {selected:?}",
                                    env!("CARGO_PKG_VERSION")
                                ));
                            }
                        }
                        MouseButton::Right => right = down,
                        _ => {}
                    }
                    window.request_redraw();
                }
                WindowEvent::MouseWheel { delta, .. } => {
                    camera.zoom(match delta {
                        MouseScrollDelta::LineDelta(_, y) => y,
                        MouseScrollDelta::PixelDelta(p) => p.y as f32 / 100.,
                    });
                    window.request_redraw();
                }
                WindowEvent::KeyboardInput { event, .. }
                    if event.state == ElementState::Pressed && !event.repeat =>
                {
                    #[cfg(not(target_arch = "wasm32"))]
                    match event.physical_key {
                        PhysicalKey::Code(KeyCode::KeyS) => {
                            let result = Project::new(scene.clone())
                                .to_json()
                                .map_err(|e| e.to_string())
                                .and_then(|s| {
                                    std::fs::write("project.json", s).map_err(|e| e.to_string())
                                });
                            window.set_title(&format!("Save project: {result:?}"));
                        }
                        PhysicalKey::Code(KeyCode::KeyL) => {
                            match std::fs::read_to_string("project.json")
                                .map_err(|e| e.to_string())
                                .and_then(|s| Project::from_json(&s).map_err(|e| e.to_string()))
                            {
                                Ok(p) => {
                                    scene = p.scene;
                                    renderer.upload(&device, &scene, None);
                                    window.set_title("Project loaded");
                                }
                                Err(e) => window.set_title(&format!("Load error: {e}")),
                            }
                        }
                        _ => {}
                    }
                    window.request_redraw();
                }
                WindowEvent::RedrawRequested if !suspended => match surface.get_current_texture() {
                    Ok(frame) => {
                        let view = frame.texture.create_view(&Default::default());
                        let mut encoder = device.create_command_encoder(&Default::default());
                        renderer.draw(
                            &queue,
                            &mut encoder,
                            &view,
                            &camera,
                            config.width as f32 / config.height as f32,
                        );
                        queue.submit(Some(encoder.finish()));
                        frame.present();
                    }
                    Err(wgpu::SurfaceError::Lost | wgpu::SurfaceError::Outdated) => {
                        surface.configure(&device, &config);
                        window.request_redraw();
                    }
                    Err(wgpu::SurfaceError::OutOfMemory) => el.exit(),
                    Err(wgpu::SurfaceError::Timeout) => window.request_redraw(),
                },
                _ => {}
            }
        }
    };
    #[cfg(not(target_arch = "wasm32"))]
    events.run(handler).unwrap();
    #[cfg(target_arch = "wasm32")]
    {
        use winit::platform::web::EventLoopExtWebSys;
        events.spawn(handler);
    }
}
