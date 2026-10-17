# Current 0.1.1 delivery limitations

- The new automatic updater and native Windows release workflow are implemented; local Linux tests do not prove Windows runtime compatibility or successful GitHub publication.
- API access in this cloud environment returns 403; the updater needs a published stable release with both standard assets. Until one exists, it fails safely without changing app files.
- Interactive Windows GPU, native BAT/PowerShell 5.1 and live GitHub end-to-end checks remain unverified locally; CI provides native CPU/updater tests once it actually runs.
- Process-stop recovery handles journaled old-app backups; full power-loss/disk-corruption atomicity is not claimed.
- Existing root launchers are preserved, not silently replaced. Legacy Current/Versions use old launchers/data; the new managed launcher defaults to a separate Data/ManagedViewport workspace.
- Engine functionality is unchanged apart from version titles; remaining engine limitations below still apply. No performance benchmark or production qualification.

## Historical 0.1.0 test-kit limitations


- Windows EXE, GPU/driver compatibility, Windows PowerShell 5.1, BAT wrappers and Windows installation are not executed in this Linux environment. Cross-linking is not runtime qualification.
- The demo has perspective only; orthographic, camera reset, keyboard navigation, transform editing, grid, undo/redo, import, PBR and Studio functionality are absent.
- S replaces one `project.json` in the working directory. The new launcher isolates test data and backs up that file before each launch. Saves during the same run replace the test file; no Save As UI exists.
- Camera and selection are not serialized. Startup uses the default scene; L explicitly loads the saved scene.
- Runtime GPU errors can terminate the application; the launcher retains stderr in a unique launch log.
- Existing Python updater is separate legacy tooling and is not used by the r2 side-by-side test installer. Automatic patch discovery and Windows updater qualification remain unfinished.
- The kit targets Windows 11 x64. ARM64/emulation is not qualified. macOS/browser execution and hardware performance benchmarks are unrun.
- Install/launch scripts verify payload hashes against the packaged manifest; trust in that manifest comes from verifying the outer ZIP against the separately supplied SHA-256.
