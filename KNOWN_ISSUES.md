# Current 0.1.2 limits

- Native Windows updater/network/BAT and packaging checks passed; interactive Windows viewport/GPU and the owner's B: drive remain manual checks.
- v0.1.2 stable GitHub assets are published and independently verified. Cloud proxy restrictions still block local API/PR tools; they did not block the native Windows public updater or Actions publication.
- The failed v0.1.1 tag/local candidate are retained for history; use v0.1.2 bootstrap and standard assets.
- Root launchers/user state/Build/legacy installations are retained; the managed viewport defaults to a separate Data/ManagedViewport workspace. User configuration can explicitly select another data directory.
- Rollback handles tested installation/validation failures and journaled old-app recovery; no full power-loss/disk-corruption atomicity claim.
- Rendering/editor capabilities are unchanged. Camera/selection persistence, orthographic/reset, gizmos, physics and Studio remain absent. No performance benchmarks or production qualification.

## Historical 0.1.0 test-kit limitations


- Windows EXE, GPU/driver compatibility, Windows PowerShell 5.1, BAT wrappers and Windows installation are not executed in this Linux environment. Cross-linking is not runtime qualification.
- The demo has perspective only; orthographic, camera reset, keyboard navigation, transform editing, grid, undo/redo, import, PBR and Studio functionality are absent.
- S replaces one `project.json` in the working directory. The new launcher isolates test data and backs up that file before each launch. Saves during the same run replace the test file; no Save As UI exists.
- Camera and selection are not serialized. Startup uses the default scene; L explicitly loads the saved scene.
- Runtime GPU errors can terminate the application; the launcher retains stderr in a unique launch log.
- Existing Python updater is separate legacy tooling and is not used by the r2 side-by-side test installer. Automatic patch discovery and Windows updater qualification remain unfinished.
- The kit targets Windows 11 x64. ARM64/emulation is not qualified. macOS/browser execution and hardware performance benchmarks are unrun.
- Install/launch scripts verify payload hashes against the packaged manifest; trust in that manifest comes from verifying the outer ZIP against the separately supplied SHA-256.
