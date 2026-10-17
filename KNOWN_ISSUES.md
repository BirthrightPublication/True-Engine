# Known issues — 0.1.0 Windows test kit r2

- Windows EXE, GPU/driver compatibility, Windows PowerShell 5.1, BAT wrappers and Windows installation are not executed in this Linux environment. Cross-linking is not runtime qualification.
- The demo has perspective only; orthographic, camera reset, keyboard navigation, transform editing, grid, undo/redo, import, PBR and Studio functionality are absent.
- S replaces one `project.json` in the working directory. The new launcher isolates test data and backs up that file before each launch. Saves during the same run replace the test file; no Save As UI exists.
- Camera and selection are not serialized. Startup uses the default scene; L explicitly loads the saved scene.
- Runtime GPU errors can terminate the application; the launcher retains stderr in a unique launch log.
- Existing Python updater is separate legacy tooling and is not used by the r2 side-by-side test installer. Automatic patch discovery and Windows updater qualification remain unfinished.
- The kit targets Windows 11 x64. ARM64/emulation is not qualified. macOS/browser execution and hardware performance benchmarks are unrun.
- Install/launch scripts verify payload hashes against the packaged manifest; trust in that manifest comes from verifying the outer ZIP against the separately supplied SHA-256.
