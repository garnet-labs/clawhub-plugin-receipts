# ClawScan results

## ClawHub profile through Vercel AI Gateway

The [built-in profile](https://github.com/openclaw/clawscan/blob/96e9849d610a9971fee885992bdf90242c3f1f81/internal/profiles/clawhub/clawscan.yml#L3-L70)
uses A.I.G. MCP for plugins and an evidence-only Codex judge. This run used the
profile unchanged, with a provider override; it is not a ClawHub production run.
The [Gateway catalog](https://ai-gateway.vercel.sh/v1/models) lists
`openai/gpt-6.1-sol` and `openai/gpt-6-luna`.
A chat-completions tool call worked with the namespaced Sol ID and a Responses
request worked with the judge's unqualified `gpt-6.1-sol` ID. The judge command
hard-codes that ID, so no judge command or profile edit was needed.

Build the CLI in a checkout of
[ClawScan 96e9849](https://github.com/openclaw/clawscan/tree/96e9849d610a9971fee885992bdf90242c3f1f81)
with Go 1.27.3: `go build -o "$HOME/work/clawscan-feasibility-cli" ./cmd/clawscan`.
Then run from the demo repo with Bash, Docker, and `AI_GATEWAY_API_KEY` already
in your environment:

```bash
image=ghcr.io/openclaw/clawscan-runtime@sha256:d494938b84a9f0da40504f611eec472d4637c755b5cef87b123daf8a2014545c
bin="$HOME/work/clawscan-feasibility-cli"
scratch=$(mktemp -d /dev/shm/clawscan-disclosed.XXXXXX)
export LLM_API_KEY="${AI_GATEWAY_API_KEY:?}" CODEX_API_KEY="$AI_GATEWAY_API_KEY"
export DEFAULT_BASE_URL=https://ai-gateway.vercel.sh/v1 OPENAI_BASE_URL=https://ai-gateway.vercel.sh/v1
export DEFAULT_MODEL=openai/gpt-6.1-sol OVERVIEW_MODEL=openai/gpt-6-luna
stage=$(bash scripts/pack.sh)
for n in 1 2 3; do
  mkdir "$scratch/$n"
  timeout 30m "$bin" "$stage/target" --profile clawhub --sandbox-image "$image" \
    --output "$scratch/$n/artifact.json" > "$scratch/$n/cli.log" 2>&1
done
```

Read the judge result at `.judge.result.verdict`; the gate is a separate field.
Raw outputs are temporary. The checked-in artifacts omit the environment
summary and scrub host-local paths and credential values before saving.

| Release | Run 1 | Run 2 | Run 3 |
| --- | --- | --- | --- |
| A | [benign](clawhub-a-1.json) (48 s) | [benign](clawhub-a-2.json) (53 s) | [benign](clawhub-a-3.json) (66 s) |
| B | [benign](clawhub-b-1.json) (48 s) | [benign](clawhub-b-2.json) (60 s) | [benign](clawhub-b-3.json) (59 s) |

All listed runs completed with `gate: pass`. These are observed verdicts on a
declared, inert demo, not evidence that the scanner missed a finding, that
ClawHub production would give the same verdict, or that npm ran the hook in CI.
The scanned directories were extracted from these exact tarballs:

- A SHA-256: `e50593d6404f5f1f38ee41cc17bf3d6a6ef0493f265ee95d20176b2409a7f949`
- B SHA-256: `5e0e634a78db8dbe674d02c4f3eeb6d574492429d572a8e249db1049caafce65`

## Keyless fallback

[`skillspector-keyless.json`](skillspector-keyless.json) is a real, completed
`clawscan-run-v1` for the standalone inert feasibility plugin. It is not a scan
of the A/B pair. SkillSpector completed with `gate: pass`; no ClawHub judge ran.
The saved copy omits the environment summary.

Reproduce from this machine with the CLI built at
[ClawScan 96e9849](https://github.com/openclaw/clawscan/tree/96e9849d610a9971fee885992bdf90242c3f1f81)
and the existing standalone feasibility fixture:

```sh
BIN="$HOME/work/clawscan-feasibility-cli"
D="$HOME/work/demo/feasibility"
docker run --rm --network none --user "$(id -u):$(id -g)" \
  --mount "type=bind,source=$BIN,target=/usr/local/bin/clawscan,readonly" \
  --mount "type=bind,source=$D/inert-plugin,target=/fixture,readonly" \
  --mount "type=bind,source=$D/scanner-tmp,target=/output" \
  ghcr.io/openclaw/clawscan-runtime@sha256:d494938b84a9f0da40504f611eec472d4637c755b5cef87b123daf8a2014545c \
  clawscan /fixture --scanner skillspector --sandbox off --output /output/isolated.json
```

The custom step is running the CLI inside a network-disabled container as the
host UID/GID. The inner CLI does not start another sandbox.

The [ClawHub plugin adapter's source](https://github.com/openclaw/clawscan/blob/96e9849d610a9971fee885992bdf90242c3f1f81/internal/runner/aig_mcp_scanner.go#L223-L248)
establishes a static coverage boundary. This baseline does not establish a
ClawHub verdict, a missed finding, or a Garnet runtime receipt.
