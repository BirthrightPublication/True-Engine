# TRUE ENGINE 0.1.0 architecture

`crates/true-engine` provides application-independent scene hierarchy, TRS transforms, primitive meshes, an orbit camera, nearest-triangle picking, schema-validated JSON projects, and a wgpu renderer. GPU geometry is retained between scene/selection changes; camera updates transfer a matrix. Rendering uses a single geometry batch, depth testing, opaque colors and simple diffuse face shading. There are no hardware performance measurements.

`examples/viewport` owns winit window/input/surface lifecycle, the three-primitive startup scene and native S/L project I/O. It is a developer test application, not License Plate Obfuscation Studio. The Rust SDK boundary is documented in docs/SDK-0.1.md; consumers remain separate repositories.

Windows artifact: optimized Rust x86_64-pc-windows-gnullvm PE plus LLVM-MinGW libunwind.dll. Windows supplies system/UCRT libraries. The new test kit under tools/windows-testkit uses built-in PowerShell for checks, launch logging, and side-by-side installation. It requires no Rust/Python installation to run. Its manifest covers shipped files. User data lives outside App and is never copied from a previous installation automatically.
