#!/bin/sh
set -eu

image="${1:-book-management-system-fastapi:prod}"
max_size_mb="${MAX_IMAGE_SIZE_MB:-400}"

size_bytes=$(docker image inspect "$image" --format '{{.Size}}')
size_mb=$((size_bytes / 1024 / 1024))

echo "Image: $image"
echo "Size:  ${size_mb} MiB"

if [ "$size_mb" -gt "$max_size_mb" ]; then
    echo "ERROR: image size ${size_mb} MiB exceeds the ${max_size_mb} MiB limit" >&2
    exit 1
fi

uid=$(docker run --rm --entrypoint id "$image" -u)
if [ "$uid" != "10001" ]; then
    echo "ERROR: expected container uid 10001, got ${uid}" >&2
    exit 1
fi

docker run --rm --entrypoint sh "$image" -c '
set -eu
test ! -e /app/.env
test ! -e /app/tests
test ! -e /app/.git
test ! -e /app/dev.db
test -x /usr/local/bin/entrypoint.sh
'

docker run --rm --entrypoint python "$image" -c '
import importlib.util

dev_packages = ("faker", "mypy", "pytest", "ruff")
present = [name for name in dev_packages if importlib.util.find_spec(name)]
if present:
    raise SystemExit("development dependencies present: " + ", ".join(present))
'

echo "Checks passed: size limit, non-root user, no local files, no dev dependencies."
