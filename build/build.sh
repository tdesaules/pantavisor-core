#!/usr/bin/env bash
set -euo pipefail
root=$(git rev-parse --show-toplevel)
if [ "$#" -ne 0 ]; then
    printf 'Usage: bash build/build.sh (Core has a single configuration)\n' >&2
    exit 2
fi
mkdir -p "$root/artifacts/build/core" "$root/artifacts/downloads" "$root/artifacts/sstate-cache"
mounts=()
if [ -n "${DOWNLOAD_CACHE:-}" ]; then mounts+=(-v "$(realpath "$DOWNLOAD_CACHE"):/work/artifacts/downloads"); fi
if [ -n "${SSTATE_CACHE:-}" ]; then mounts+=(-v "$(realpath "$SSTATE_CACHE"):/work/artifacts/sstate-cache"); fi
exec python3 "$root/build/provenance.py" "$root/artifacts/build/core/tmp/deploy/images/userspace-arm64" pantavisor-core-image-userspace-arm64 podman run --rm --userns=keep-id:uid=30000,gid=30000 --security-opt label=disable \
    -v "$root:/work" "${mounts[@]}" -w /work -e KAS_WORK_DIR=/work \
    -e KAS_BUILD_DIR=/work/artifacts/build/core \
    ghcr.io/siemens/kas/kas@sha256:22c70f90e21997c0b6743ad2d802cf1d942c28e974361c4733b8a026cb7ef809 \
    build /work/kas/base.yml
