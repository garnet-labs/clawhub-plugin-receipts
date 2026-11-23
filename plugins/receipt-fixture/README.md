# Inert ClawHub plugin receipt fixture

This fixture has two release builds with identical plugin code. A has no helper.
B declares and bundles a private local helper. Its npm `postinstall` sends one
GET to the public metadata endpoint
`https://api.github.com/repos/garnet-labs/clawhub-plugin-receipts` with
`User-Agent: clawhub-plugin-receipts-fixture`. The hook sends no body or token
and does not read files or environment variables. Do not publish either build.
