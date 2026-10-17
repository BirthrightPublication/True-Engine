# Browser SDK integration tests

From the engine repository root, first run `python3 tools/sdk/build.py` with the pinned Rust and wasm-bindgen tools on PATH. Build stages the compiled SDK and exact host example in Build/sdk-web. Then:

```
npm ci --prefix tools/browser
npm --prefix tools/browser exec -- playwright install chromium
npm --prefix tools/browser run types
cd tools/browser
npm test
```

`CHROMIUM_PATH` can point to an already-installed Chromium (used by this Linux cloud environment). `SDK_BACKENDS=webgl2,webgpu` runs both actual backends; default webgl2 uses SwiftShader for headless regression checks. Set environment variables using PowerShell `$env:SDK_BACKENDS='webgl2,webgpu'` on Windows. The runner starts a private local static test server and stops it afterwards. Python must be on PATH (`PYTHON=python` on Windows if `python3` is unavailable).

The tests load the compiled .wasm, inspect real canvas pixels, exercise custom geometry/material/transforms, pointer camera controls, picking, file download/reopen, input validation, multiple canvases and disposal. They fail on page/console errors. Reports go to Build/sdk-browser-results.json and tools/browser/test-results. Types are checked against the actual staged distributable. Rust CPU/EGL tests and SDK packaging integrity tests run separately. A backend unavailable on a runner fails its project; do not convert that failure into a claim of compatibility. Headless software-renderer results do not establish hardware performance or every Windows GPU/driver.
