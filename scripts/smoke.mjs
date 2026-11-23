import assert from "node:assert/strict";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

const installRoot = process.argv[2];
assert.ok(installRoot, "pass the npm install prefix");
const entry = resolve(installRoot, "node_modules/garnet-clawhub-receipt-fixture/index.js");
const { default: register } = await import(pathToFileURL(entry));
const tools = [];
register({ registerTool(tool) { tools.push(tool); } });
assert.equal(tools.length, 1);
assert.equal(tools[0].name, "receipt_fixture_status");
assert.deepEqual(await tools[0].execute(), { content: [{ type: "text", text: "ready" }] });
console.log("Plugin smoke test: ready");
