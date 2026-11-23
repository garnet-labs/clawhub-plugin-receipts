# Inert lifecycle helper

This private demo-only helper is not published to a registry. During npm
installation of release B, its `postinstall` makes one GET to
`https://api.github.com/repos/garnet-labs/clawhub-plugin-receipts` with
`User-Agent: clawhub-plugin-receipts-fixture`. It sends no body or token, does not
read files or environment variables, and logs the HTTP status, not the body.
Installing A does not run the helper.
