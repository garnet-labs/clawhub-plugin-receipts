#!/usr/bin/env bash
set -euo pipefail

repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
mkdir -p "$repo/out"
stage=$(mktemp -d "$repo/out/release.XXXXXX")
mkdir "$stage/target"

(
  cd "$repo/plugins/receipt-fixture"
  npm ci --offline --ignore-scripts --install-links --no-audit --no-fund >&2
  npm pack --ignore-scripts --pack-destination "$stage" >&2
)
mv "$stage"/garnet-clawhub-receipt-fixture-*.tgz "$stage/release.tgz"
tar -xzf "$stage/release.tgz" --strip-components=1 -C "$stage/target"
printf '%s\n' "$stage"
