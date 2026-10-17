TRUE ENGINE — STANDARD WINDOWS RELEASES (SDK 0.1, PROJECT SCHEMA 1)

This is the existing developer viewport, not License Plate Obfuscation Studio.
Windows x64; Windows PowerShell 5.1 is built in. No Python/Rust runtime needed.

ONE-TIME SETUP
Extract the separately supplied bootstrap ZIP into B:\True Engine, keeping
Update True Engine.bat and TrueEngine-Bootstrap.ps1 together. Do not overwrite
an unrelated existing file. Authenticate the bootstrap SHA-256 against the
trusted delivery record before running it. Double-click Update True Engine.bat.
It obtains GitHub's latest stable Release, downloads the exact Windows ZIP and
SHA-256 sidecar into Build\Releases, verifies them, and installs only app\.
The standard package names are True-Engine-vVERSION-windows-x64.zip and .sha256.
It never uses GitHub's automatically generated source archives as an executable.
Once a compatible stable GitHub Release exists, no manual ZIP extraction is
needed for subsequent updates. API/network/rate-limit errors leave app intact.

START / DATA
Double-click Start True Engine.bat after a successful installation. The scene
contains a cube, sphere and plane. Left-drag orbit, right-drag pan, wheel zoom,
click pick, S save, L load. Camera/selection are not serialized. There is no
orthographic/reset/gizmo/Studio functionality. Schema remains 1.
Data\ManagedViewport is a separate default test-project directory. Optional
TrueEngine-Launcher.json can set data_directory to a deliberate existing folder.
The updater never modifies that configuration. The launcher backs up an existing
project.json before every launch; S replaces that test file within the session.

PRESERVATION / COMPATIBILITY
Build is your GitHub source/build area, never wiped. Downloads use new unique
Build\Releases subdirectories. Root settings, projects, Data, Current, Versions,
earlier test-kit launchers, Build and unrelated files are not replaced.
Older Current/Versions installations remain runnable with their old launchers.
A recognized 0.1.0 test-kit App folder can be upgraded; its unmanaged contents
are copied forward and its entire previous app is retained as a backup.
Unknown app folders are refused. Persistent files that collide with incoming
application paths cause refusal, not overwrite. SDK/schema changes and automatic
downgrades are refused. No data migration takes place.

FAILURE / RECOVERY
Close the viewport before updating. An exclusive OS file lock prevents concurrent
updates. Logs are in Logs\Update-*.log. Prior app files and failed new app files
are retained under Backups\Updates\<transaction-id>. Ordinary installation or
post-install validation failures restore the previous app. If a process stops
mid-update, the next updater recovers a journaled old app before proceeding.
Full power-loss/disk-corruption recovery is not claimed. Do not delete backups.
To manually roll back: close all viewports, retain the current app under a new
folder name, and move a chosen Backups\Updates\ID\app back to root\app. Keep user
data and Build untouched. Older Current/Versions launchers need no conversion.
Existing root launchers are never overwritten; the new stable bootstrap delegates
to each installed version's updater so the update logic itself evolves.

TRUST / STATUS
Checksums downloaded from the same authenticated HTTPS GitHub Release detect
corruption, not compromise of the publisher/account. No code signing is claimed.
Original-code licensing remains the owner's decision; third-party notices are
included without selecting an open-source license for True Engine.
Read app\TEST_REPORT.md, manifest.json and release notes for actual tests and
known limitations. A local cross-build does not establish Windows execution.
The GitHub Actions workflow must pass its native Windows build/tests before
publishing assets. Workflow publication is distinct from a successful CI run.
