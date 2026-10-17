#!/usr/bin/env bash
set -euo pipefail
export RUSTUP_HOME=/workspace/.true-engine/rustup
export CARGO_HOME=/workspace/.true-engine/cargo
export PATH="$CARGO_HOME/bin:$PATH"
export XDG_RUNTIME_DIR=/workspace/.true-engine/runtime
export XDG_CACHE_HOME=/workspace/.true-engine/cache
mkdir -p "$XDG_RUNTIME_DIR" "$XDG_CACHE_HOME" /workspace/.true-engine/projects
chmod 700 "$XDG_RUNTIME_DIR"
command -v cc >/dev/null
command -v python3 >/dev/null
if ! command -v rustup >/dev/null; then
  curl --fail --silent --show-error https://sh.rustup.rs -o /workspace/.true-engine/rustup-init.sh
  sh /workspace/.true-engine/rustup-init.sh -y --no-modify-path --profile minimal --default-toolchain 1.85.1
fi
rustup toolchain install 1.85.1 --profile minimal --component rustfmt --component clippy
rustup target add --toolchain 1.85.1 wasm32-unknown-unknown x86_64-pc-windows-gnu
cd /workspace/True-Engine
cargo +1.85.1 build --workspace --locked -j 4

# Reproducible Windows x64 cross-linker (upstream archive SHA-256 verified).
toolchain_dir=/workspace/.true-engine/llvm-mingw-20261006-ucrt-ubuntu-22.04-x86_64
if [ ! -x "$toolchain_dir/bin/x86_64-w64-mingw32-clang" ]; then
  curl --fail --silent --show-error --location https://github.com/mstorsjo/llvm-mingw/releases/download/20261006/llvm-mingw-20261006-ucrt-ubuntu-22.04-x86_64.tar.xz -o /workspace/.true-engine/llvm-mingw.tar.xz
  python3 - <<'PY'
import hashlib, tarfile
archive = "/workspace/.true-engine/llvm-mingw.tar.xz"
expected = "5f9c6ed95b2d4bdb2869a488c5fd5857fbdabcf288a0aa3eb1da43f6a08d8ab4"
if hashlib.sha256(open(archive, "rb").read()).hexdigest() != expected:
    raise SystemExit("LLVM-MinGW archive checksum mismatch")
with tarfile.open(archive) as source:
    source.extractall("/workspace/.true-engine", filter="data")
PY
fi
rustup target add --toolchain 1.85.1 x86_64-pc-windows-gnullvm
export PATH="$toolchain_dir/bin:$PATH"
export CARGO_TARGET_X86_64_PC_WINDOWS_GNULLVM_LINKER=x86_64-w64-mingw32-clang
cargo +1.85.1 build --release -p true-engine-viewport --target x86_64-pc-windows-gnullvm --locked -j 4
