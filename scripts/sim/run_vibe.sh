#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
target="${1:-sim}"
if [ "$#" -gt 0 ]; then shift; fi
make -C "$ROOT/tb/vibe" "$target" "$@"
