# Next objective

The owner approved an additive 0.1.3 browser SDK for Plate Studio integration. Finish and verify the compiled ESM/WASM package, exact version/hash/source, public API, real example and automated integration tests before consumer integration. Preserve the existing renderer, native schema 1, Rust SDK contract 0.1 and all earlier tags/Build/data.

Plate Studio remains a separate repository and is unchanged by this engine-side task. Its actual ES-module host must explicitly serve/bundle the pinned SDK JS/WASM assets, and application integration must use the published package rather than duplicate engine code. Do not claim consumer integration or Windows GPU qualification from Linux browser tests. No unrelated roadmap phases without approval. Consult docs/PLATE_STUDIO_INTEGRATION.md and current release provenance under releases/.
