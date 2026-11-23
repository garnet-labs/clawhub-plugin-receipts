# Release observation protocol

## Sample

Two archived ClawHub releases serve as unmodified controls. Verify the registry
digest and archive bytes before preparing any derived file:

| Control | Version | ClawHub archive SHA-256 |
|---|---|---|
| `@openclaw/discord` | 2026.11.7 | `7b59431a597ab19327952f823d2018f19f2b9001bbf5925d76ed9daefa9ad085` |
| `@openclaw/memory-lancedb` | 2026.11.7 | `35b03f263ec83a3118dc4aace4e8b90416fbf49f14404c4d31444731648b71bf` |

For each control, prepare four separately labeled derivatives, one addition per
archive:

| Mechanism | Point of execution |
|---|---|
| Load | Top-level code in the runtime entry point |
| First use | First invocation of the entry's registration hook |
| Child process | Entry starts a Node child that makes the request |
| Dependency | Entry imports a bundled inert fixture module; that module makes the request |

Each plant is one HTTPS GET to
`https://api.github.com/repos/garnet-labs/clawhub-plugin-receipts` with its
disclosed `clawhub-recall-fixture/<mechanism>` user agent. No body, credentials,
environment fields, file contents, retries, or response interpretation. Drop
the response body. No install lifecycle script invokes any plant. Mark the
addition in its source and local variant manifest. Derivatives are not releases
from ClawHub and must not be published to a package registry.

## Static scoring

Run stock ClawScan `clawhub` on the extracted package root from each exact
control and variant archive, three independent runs per archive. Record scan
pin, archive digest, elapsed time, verdict, completeness and evidence.
Overlapping timings are wall clock per run, not summed elapsed time.

ClawScan caught = at least one eligible run has a specific finding identifying
the plant location or the planted request/child behavior. A verdict, a generic
network warning, incidental overview text, or an exclusion inventory does not
count. Record the individual hit count as well as the any-of-three outcome.
Report all actual results; if fewer than three runs are eligible, record
unavailable runs explicitly and classify a no-hit cell as undeterminable.
Score the same target/behavior on controls; any control hit is a false positive.

## Runtime scoring (held pending local-archive approval)

Use Node 24.22.3 and OpenClaw 2026.11.7 on the runner with a separately created
unprivileged user, fresh home, cleared environment, npm scripts disabled and a
loopback-only, credential-free Gateway. Measure the same install and first-load
steps on both legs. Controls use the standard pinned ClawHub selector.
Derivatives, once approved, use the verified local archive selector; that
transport difference is not itself an indicator. Run an unchanged local-archive
control as a supplemental transport check if authorized; keep it separate from
the main comparison.

App caught = the finalized, exact base/head Workload diff has a `+` row in
the right plugin job for `api.github.com` on the expected chain. For the child
cell also require an additional child Node hop consistent with the plant. The
public profile must corroborate the chain and destination. A declaration, raw
profile row without such a diff, or a connection in the runner fold is not a
hit. An endpoint match on the control invalidates that cell; unrelated setup
traffic is not a hit or false positive. Because the profile does not expose the
URI or User-Agent, this scoring is limited to confirmed plant execution,
destination, ancestry, and matched controls. Require independent plant execution
evidence before scoring a missing App row as a miss: failed install, inactive
hook, unbound comparison, or incomplete recording is undeterminable, not a
miss. Keep best-effort results scoped to the recorded comparison.

The primary scorecard reports all eight cells independently, then both /
ClawScan only / App only / neither, with undeterminable cells excluded from
recall denominators and shown separately. To claim added runtime evidence,
require an App hit without a static hit and no matching control hit. The result
does not estimate malware recall, imply exploitability, or generalize beyond
these declared plants. Keep profile overlap labels and the App diff score
separate.
