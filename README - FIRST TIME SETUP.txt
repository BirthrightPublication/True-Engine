TRUE ENGINE 0.1.0 — WINDOWS 11 x64 TEST KIT, DISTRIBUTION REVISION 2

WHAT THIS IS
A runnable Windows EXE for the existing TRUE ENGINE 0.1.0 viewport demo.
This is an engine test application, NOT License Plate Obfuscation Studio.
There is no license plate detection, obfuscation, media processing, or Studio UI.
The engine binary is unchanged; revision 2 improves packaging and instructions.
It was cross-compiled on Linux. Windows execution has NOT been verified here.

REQUIREMENTS
- Windows 11 on an x64 PC, with current manufacturer GPU drivers.
- Built-in 64-bit Windows PowerShell 5.1 (or compatible Windows PowerShell).
- A writable folder. No administrator rights are normally required.
- Rust, Python, Visual Studio and a separate VC++ runtime are NOT needed to run.
- App\libunwind.dll is included. Windows supplies UCRT and graphics system DLLs.
Do not download missing DLLs from third-party DLL sites. Re-extract this whole
verified ZIP if the included libunwind.dll is missing. ARM64 is not qualified.

1. DOWNLOAD AND VERIFY
Keep the ZIP and .sha256 file. Ideally save the ZIP in B:\True Engine\Build.
If B: does not exist, use another writable download folder for portable testing.
In PowerShell run:
  Get-FileHash -Algorithm SHA256 -LiteralPath 'FULL PATH TO THE DOWNLOADED ZIP'
Compare the result with the trusted SHA-256 in the delivery message.
The sidecar repeats the digest, but does not independently authenticate a ZIP.

2. EXTRACT — DO NOT RUN INSIDE THE ZIP
Right-click the ZIP, choose Extract All, and use a NEW, empty folder.
Keep App, scripts, notices, and RELEASE_MANIFEST.json together.
Do not extract over an existing engine, source checkout, or working version.
The test EXE is App\true-engine-viewport.exe; it is not a source-only release.

3. QUICK PORTABLE TEST (NO INSTALLATION NEEDED)
Double-click CHECK DEPENDENCIES.bat, then START APPLICATION.bat.
A console stays visible for checks, data path, and errors. The 3D viewport opens.
For portable mode the only test workspace is:
  <extracted folder>\UserData\TestProject
The EXE can be launched directly, but use the BAT so projects and logs go to the
isolated test workspace and an existing test project is backed up before launch.
The BAT uses process-scoped PowerShell execution policy; it does not permanently
change your execution policy. Managed-computer restrictions may still apply.
This is an unsigned test build. Verify the trusted ZIP hash before choosing to
run it if Windows presents a reputation prompt. No global security changes needed.

4. OPTIONAL INSTALLATION TO B:\True Engine
Close the test viewport. Double-click INSTALL TO B DRIVE.bat.
It verifies all packaged file SHA-256 values and creates:
  B:\True Engine\Versions\0.1.0-windows11-testkit-r2\
It creates a NEW, separate test-data path under:
  B:\True Engine\Data\TestKit-0.1.0-<unique ID>\
The precise path is printed. It never replaces Current, previous versions,
existing settings, projects, or an existing root START APPLICATION.bat.
If the destination version already exists, installation stops without replacing it.
Launch the installed version with:
  B:\True Engine\Versions\0.1.0-windows11-testkit-r2\START APPLICATION.bat
A root B:\True Engine\START APPLICATION.bat is added only if none already exists.
If an older root launcher already exists, use the version-specific path above.
Keep this ZIP in B:\True Engine\Build for reproducibility. Future engine build
ZIPs belong there. B:\License Plate Obfuscation Studio and its Build directory
are reserved for that separate application; this kit does not touch them.
An alternate destination can be supplied from PowerShell:
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File '.\Install-To-B-Drive.ps1' -Destination 'C:\True Engine'

5. WHAT YOU SHOULD SEE
A window titled TRUE ENGINE 0.1.0 with a dark blue-gray background, a blue cube
on the left, a faceted blue sphere near the center, and a blue square plane on
the right, viewed in perspective. Simple directional shading makes faces differ
in brightness. A click-selected object turns gold; its ID appears in the title.
There is no editor toolbar, hierarchy panel, grid, gizmo, or animated scene.

6. BASIC TEST CHECKLIST
[ ] Window opens with all three primitives; no missing DLL or GPU error.
[ ] Left-drag over the viewport: orbit the camera around the scene.
[ ] Right-drag: pan the camera/target.
[ ] Mouse wheel: zoom in/out; geometry remains visible at a sensible distance.
[ ] Click a primitive without dragging: it turns gold and the title shows its ID.
[ ] Click empty background: selection clears (Selected: None).
[ ] Resize, minimize, and restore: verify rendering resumes without distortion.
    These lifecycle cases are manual checks, not already verified on Windows.
[ ] Click the viewport to focus it. Press S (no Ctrl required): the title should
    show Save project: Ok(()). Verify project.json exists in the printed data path.
[ ] Close, start with the SAME version-specific BAT, and press L: the title should
    show Project loaded. The scene is restored. An earlier project.json is copied
    into the test workspace's Backups folder before every launcher invocation.
[ ] Confirm project.json contains schema_version 1 and three scene nodes.
[ ] Press L with a deliberately invalid JSON copy only in this isolated test
    folder: a Load error title should appear rather than rewriting that file.
    Preserve your valid test file first, and restore it manually afterward.

IMPORTANT SAVE LIMITS
S saves scene nodes, hierarchy, transforms, primitive type and material color.
It writes ONE project.json in the test workspace, replacing that test file.
There is no Save As dialog, multi-project UI, camera/selection persistence,
orthographic camera, reset camera button, keyboard movement, or object editing.
Use only the isolated test workspace; do not substitute an existing personal
project. Backups before each launch preserve the previous session's saved file.
Moving/zooming the camera then saving will NOT restore that camera on reopening.
The default scene appears on every startup; press L to load a saved scene.

7. ERRORS AND TEST REPORTS
The launcher prints the exact test-data directory. Each run writes a unique
launch-*.log there. If no window opens, retain the console message and log.
CHECK DEPENDENCIES verifies OS architecture and file hashes, not GPU capability.
If graphics initialization fails, update the GPU driver from Windows Update or
its manufacturer and retry. This kit cannot promise every GPU will work.
When reporting results, include Windows version, GPU/driver, whether each
check above passed, the error title/console output, and the launch log.
Do not send private projects or credentials.

8. ROLLBACK AND DATA PRESERVATION
This test kit installs SIDE BY SIDE, not as an in-place patch. To roll back,
close it and launch your earlier working version directly. No old version,
Current directory, application settings, or existing root launcher is replaced.
The provided installer makes no registry or system dependency changes.
Keep both version folders and all Data/Backups. Do not delete your test-data
folder when reporting a failure. No schema migration occurs (SDK 0.1, schema 1).
This package is not a delta patch and does not use the older Python updater.

9. WHAT WAS ACTUALLY TESTED
See TEST_REPORT.md and RELEASE_MANIFEST.json. Linux execution verified native
rendering, selection, S/L, orbit/pan/zoom and automated SDK/GPU behavior.
Windows x64 release cross-link and dependency imports were checked.
Windows EXE execution, BAT wrappers, GPU compatibility, and installation on
B: have NOT run on a Windows machine here. Test them using this checklist.
No feature milestone has been advanced by this repackaging.
