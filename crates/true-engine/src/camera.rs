use glam::{Mat4, Vec3};
#[derive(Clone, Debug)]
pub struct OrbitCamera {
    pub target: Vec3,
    pub yaw: f32,
    pub pitch: f32,
    pub distance: f32,
}
impl Default for OrbitCamera {
    fn default() -> Self {
        Self {
            target: Vec3::ZERO,
            yaw: 0.7,
            pitch: 0.4,
            distance: 6.,
        }
    }
}
impl OrbitCamera {
    pub fn eye(&self) -> Vec3 {
        self.target
            + self.distance
                * Vec3::new(
                    self.yaw.sin() * self.pitch.cos(),
                    self.pitch.sin(),
                    self.yaw.cos() * self.pitch.cos(),
                )
    }
    pub fn orbit(&mut self, dx: f32, dy: f32) {
        self.yaw -= dx * 0.008;
        self.pitch = (self.pitch + dy * 0.008).clamp(-1.55, 1.55);
    }
    pub fn pan(&mut self, dx: f32, dy: f32) {
        let forward = (self.target - self.eye()).normalize();
        let right = forward.cross(Vec3::Y).normalize();
        let up = right.cross(forward);
        self.target += (-right * dx + up * dy) * self.distance * 0.002;
    }
    pub fn zoom(&mut self, delta: f32) {
        self.distance = (self.distance * (-delta * 0.12).exp()).clamp(0.2, 1000.);
    }
    pub fn view_projection(&self, aspect: f32) -> Mat4 {
        Mat4::perspective_rh(45f32.to_radians(), aspect.max(0.001), 0.01, 10000.)
            * Mat4::look_at_rh(self.eye(), self.target, Vec3::Y)
    }
    pub fn ray(&self, x: f32, y: f32, width: f32, height: f32) -> (Vec3, Vec3) {
        let inv = self.view_projection(width / height).inverse();
        let near = inv.project_point3(Vec3::new(2. * x / width - 1., 1. - 2. * y / height, 0.));
        let far = inv.project_point3(Vec3::new(2. * x / width - 1., 1. - 2. * y / height, 1.));
        (near, (far - near).normalize())
    }
}
