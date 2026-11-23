const { get } = require("node:https");

// Inert, fixture-only GET of public repo metadata. No payload or credentials.
const request = get(
  "https://api.github.com/repos/garnet-labs/clawhub-plugin-receipts",
  { headers: { "User-Agent": "clawhub-plugin-receipts-fixture" }, timeout: 8000 },
  (response) => {
    response.resume();
    response.on("end", () => {
      console.log(`Inert fixture: public metadata GET returned HTTP ${response.statusCode}`);
    });
  },
);
request.on("timeout", () => request.destroy(new Error("metadata request timed out")));
request.on("error", (error) => {
  console.error(`Inert fixture: metadata request failed: ${error.message}`);
  process.exitCode = 1;
});
