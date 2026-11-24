#!/usr/bin/env bash
set -euo pipefail

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
plugin=$2
case "$plugin" in
  discord|memory-lancedb) ;;
  *) printf 'Unknown release: %s\n' "$plugin" >&2; exit 1 ;;
esac
selection="$root/selection.json"
mode=$(jq -er '.mechanism | select(. == "control" or . == "load" or . == "first-use" or . == "child-process" or . == "dependency")' "$selection")
expected=$(jq -er --arg plugin "$plugin" '.sha256[$plugin] | select(test("^[a-f0-9]{64}$"))' "$selection")
home=/home/clawrun
prefix="$home/.local"
archives="$RUNNER_TEMP/release-observation"

within_workload() (
  node_bin=$(dirname -- "$(command -v node)")
  cd /
  exec sudo -n -u clawrun -- /usr/bin/env -i \
    PATH="$node_bin:$prefix/bin:/usr/bin:/bin" HOME="$home" \
    CI=true NODE_ENV=production npm_config_ignore_scripts=true "$@"
)

case "$1" in
  prepare)
    sudo -n useradd --create-home --home-dir "$home" --shell /usr/sbin/nologin clawrun
    sudo -n chmod 0700 "$home"
    within_workload /bin/sh -eu -c '
      test "$(node --version)" = v24.22.3
      test "$(npm config get ignore-scripts)" = true
      npm install --global --prefix "$1" --ignore-scripts --registry=https://registry.npmjs.org \
        --no-audit --no-fund openclaw@2026.11.7
      test "$(node -p "require(process.argv[1]).version" "$1/lib/node_modules/openclaw/package.json")" = 2026.11.7
    ' sh "$prefix"
    python3 "$root/prepare.py" --output "$archives" --plugin "$plugin" --mechanism "$mode"
    archive="$archives/$plugin/$mode/release.tgz"
    printf '%s  %s\n' "$expected" "$archive" | sha256sum --check --strict
    if [[ "$mode" != control ]]; then
      sudo -n install -o clawrun -g clawrun -m 0400 "$archive" "$home/release.tgz"
    fi
    ;;
  install)
    install_args=("clawhub:@openclaw/$plugin@2026.11.7")
    if [[ "$mode" != control ]]; then
      selector="$home/release.tgz"
      printf '%s  %s\n' "$expected" "$selector" | within_workload sha256sum --check --strict
      install_args=("$selector" --force --accept-capabilities)
    fi
    within_workload /bin/sh -eu -c '
      test "$(npm config get ignore-scripts)" = true
      openclaw plugins install "$@"
      openclaw plugins list
    ' sh "${install_args[@]}"
    if [[ "$mode" != control ]]; then
      accepted=$(within_workload openclaw plugins inspect "$plugin" --json |
        jq -ec '.install.acceptedSurface | select(type == "object")')
      printf 'Accepted plugin capabilities: %s\n' "$accepted"
    fi
    ;;
  first-load)
    within_workload /bin/sh -eu -c '
      openclaw config set gateway.mode local
      openclaw config set plugins.allow "[\"$1\"]" --strict-json
      openclaw plugins enable "$1"
      CLAW_RECALL_OBSERVE=1 openclaw gateway run --bind loopback --auth none --port 18789 &
      gateway=$!
      trap "kill -TERM $gateway 2>/dev/null || true; wait $gateway || true" EXIT
      attempts=0
      until node -e "fetch(\"http://127.0.0.1:18789/startupz\", {signal: AbortSignal.timeout(1000)}).then(r => {if (!r.ok) process.exitCode = 1}, () => {process.exitCode = 1})"; do
        kill -0 "$gateway"
        attempts=$((attempts + 1))
        if [ "$attempts" -ge 60 ]; then
          printf "Gateway did not finish startup\n" >&2
          exit 1
        fi
        sleep 1
      done
      printf "Gateway finished startup; observing for 10 seconds\n"
      sleep 10
      kill -TERM "$gateway"
      wait "$gateway"
      trap - EXIT
      printf "Gateway stopped cleanly\n"
    ' sh "$plugin"
    ;;
  *) printf 'Unknown stage: %s\n' "$1" >&2; exit 1 ;;
esac
