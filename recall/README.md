# Release observation

See [the preregistered protocol](PREREGISTRATION.md) for scoring and limits.
The controls are the exact Discord and Memory LanceDB 2026.11.7 ClawHub archives.
Derivatives are generated locally, never published to ClawHub or npm, and use
a different selector. They are not substitutes for the original releases.

| Variant | Disclosed source addition | User-Agent suffix |
|---|---|---|
| Load | Request in the runtime entry | load |
| First use | Request on first invocation of the registration hook | first-use |
| Child process | Runtime entry starts an environment-free Node child | child-process |
| Dependency | Runtime entry calls the bundled receipt fixture | dependency |

Each request is a GET to the public API for this repository. It has no body,
does not send secrets, and does not act on the response. Only the credential-free
Gateway receives the explicit fixture-enable switch. The response marker is
independent execution evidence, not a runtime-observer hit.

Preparation verifies registry metadata and archive digests, keeps controls
byte-identical, and records variant digests. Static scanning does not install
plugins or launch a Gateway. The default branch measures the unchanged
controls; comparison branches select the verified local archives. A prepared
archive is not execution evidence.
