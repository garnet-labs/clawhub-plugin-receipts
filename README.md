# ClawHub plugin runtime receipts

This inert fixture compares what [ClawScan audits statically][adapter source]
with what a Garnet recording can show during installation. It does not assert
a scanner miss or that either release is safe.

A (`main`, 1.0.0) installs the plugin with no dependencies. The comparison
release (B, `release-1.0.1`) uses byte-identical plugin source and the same
smoke test, but declares and bundles a private local dependency.
Its disclosed `postinstall` makes one GET to the
[public GitHub metadata endpoint](https://api.github.com/repos/garnet-labs/clawhub-plugin-receipts)
with `User-Agent: clawhub-plugin-receipts-fixture`. The hook sends no payload
or token, reads no files or environment variables, and logs only the HTTP
status. Neither fixture is for publication.

Both release archives carry the same disclosure. The plugin scan includes the
manifest and shrinkwrap; the shrinkwrap exposes that B's dependency has an
install script. The adapter stages files under the plugin target other than
files beneath `node_modules`. An ordinary helper directory inside the target
would be in scope; the bundled helper implementation is under
`node_modules`. The scanner is not an install trace.

## Reproduce the local install

Use Bash, Node 24, and npm 11:

```bash
stage=$(bash scripts/pack.sh)
npm install --prefix "$stage/installed" --offline --ignore-scripts=false \
  --foreground-scripts --no-audit --no-fund "$stage/release.tgz"
node scripts/smoke.mjs "$stage/installed"
```

The custom packaging step bundles B's local `file:` dependency using npm's
`--install-links` and `bundleDependencies`. Packing disables scripts so the
hook runs during installation of the release, not during preparation.
The smoke test exercises plugin registration through a minimal test harness,
not a running OpenClaw gateway.

[The recording workflow](.github/workflows/receipts.yml) uses the
[pinned Garnet OIDC pattern][recording example] and the same `install` job
on both revisions. Verify each receipt against the
exact repository, head SHA, workflow run, attempt and job. Check whether B's
install step attributes a connection to the declared helper process;
an observed connection alone does not establish an HTTP status or payload.
See [ClawScan evidence](clawscan/README.md) for static results and limits.

[recording example]: https://github.com/garnet-labs/openai-node/blob/c91f7f006108f8ccfdcdbd1310722e8ce1f93a66/.github/workflows/garnet-record.yml
[adapter source]: https://github.com/openclaw/clawscan/blob/96e9849d610a9971fee885992bdf90242c3f1f81/internal/runner/aig_mcp_scanner.go#L223-L248
