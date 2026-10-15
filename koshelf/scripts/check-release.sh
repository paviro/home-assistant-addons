#!/bin/sh
# Run with Docker and QEMU/binfmt available. Tests every advertised platform.
set -eu
cd "$(dirname "$0")/.."
for pair in 'amd64 linux/amd64' 'aarch64 linux/arm64' 'armv7 linux/arm/v7' 'i386 linux/386'; do
    set -- $pair
    arch=$1
    platform=$2
    docker build --platform "$platform" --build-arg "BUILD_ARCH=$arch" -t "local/koshelf-check:$arch" .
    docker run --rm --init --platform "$platform" --entrypoint python3 \
        -v "$PWD:/tests:ro" "local/koshelf-check:$arch" \
        /tests/scripts/integration-smoke.py --binary /usr/local/bin/koshelf --nginx /usr/sbin/nginx
done
