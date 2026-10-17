# Permanent GitHub repository and release rules

Authoritative source for this conversation: https://github.com/BirthrightPublication/True-Engine

Other projects are separate: `BirthrightPublication/forge` and `BirthrightPublication/License-Plate-Obfuscation`. Do not mix their source, histories, releases, or install directories. Studio must pin an explicitly versioned True Engine release or commit. Never silently copy engine code into a consuming repository.

## Before each development iteration

1. Read NEXT_ITERATION.md, AGENTS.md, roadmap, release manifest and changelog.
2. Confirm repository identity, working directory, branch, remote, and commit history.
3. Fetch origin. Compare the authoritative main branch with the current checkout and preserve unrelated local/uncommitted work. Never replace newer working source with an older ZIP.
4. Work on a dedicated feature branch. Use the existing isolated checkout; no worktree unless explicitly requested.

## During and after development

Make meaningful source commits, preserve functionality, run applicable checks, and document significant architectural decisions. Push the feature branch and open a PR when the available authenticated tooling supports it. Merge approved changes into main and confirm the remote refs/commits. Never force-push stable history or claim a push/merge succeeded without remote confirmation. Keep previously released tags immutable; create a version tag for each completed release.

The owner has authorized this repository-management workflow for this project. Additional confirmation is not needed for routine actions already within an approved iteration; breaking changes, future release phases, unrelated repositories, and destructive actions remain outside that authorization. Initial empty-repository setup is authorized to push verified source directly to main. Future feature work uses PR review; unavailable API access is a blocker to report, not grounds to claim a PR or approval exists.

## Source and release preservation

Git tracks source, dependency manifests/lockfiles, scripts, documentation, test reports and release provenance. Exclude credentials, personal files, databases, build caches, installed application/data directories and unnecessary binary dependencies. Do not commit raw credentials or print secret values.

Binary ZIPs belong in the project's Build directory and, when API access permits, assets on the matching tagged GitHub Release. Record tagged source commit, package filename, SHA-256, payload hashes, SDK/schema compatibility, migration behavior, test results and known limitations. A pushed tag or checksum record does not mean the binary was uploaded. Never claim that a release asset is on GitHub unless upload success is confirmed. Preserve earlier versions, patches, packages and tags.

Report the exact operation and error if authentication, access, permissions, source, PR tooling or release uploads are blocked. Existing Git HTTPS proxy authentication may work without a raw token; test required operations before requesting new credentials. Do not invent successful remote operations.

## Release completion report

Include repository name/URL, source branch and final commit SHA, push confirmation, PR/merge status, version tag, package filename, tests, update instructions and unresolved issues. Distinguish source push, tag push, release publication and binary upload. Do not advance engine features until the existing 0.1 Windows test baseline is assessed.
