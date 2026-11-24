#!/usr/bin/env python3
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import shutil
import tarfile
from urllib.parse import quote
from urllib.request import urlopen

RELEASES = {
    "discord": ("7b59431a597ab19327952f823d2018f19f2b9001bbf5925d76ed9daefa9ad085", "registerFull"),
    "memory-lancedb": ("35b03f263ec83a3118dc4aace4e8b90416fbf49f14404c4d31444731648b71bf", "register"),
}
VERSION = "2026.11.7"
MECHANISMS = ("load", "first-use", "child-process", "dependency")
ENDPOINT = "https://api.github.com/repos/garnet-labs/clawhub-plugin-receipts"
ENTRY = "package/dist/index.js"
DEPENDENCY = "@garnet-labs/receipt-fixture"
DEPENDENCY_PATH = "package/node_modules/" + DEPENDENCY
HEADER = "// Disclosed receipt fixture: one inert HTTPS GET; no credentials or request body."
GUARD = 'process.env.CLAW_RECALL_OBSERVE === "1"'


def request(mechanism):
    return f"""receiptGet({json.dumps(ENDPOINT)}, {{
  agent: false,
  headers: {{ "user-agent": "clawhub-recall-fixture/{mechanism}" }},
}}, (response) => {{
  response.resume();
  console.log("receipt fixture response: {mechanism}");
}}).on("error", () => {{}}).setTimeout(3500, function () {{ this.destroy(); }});"""


def build(mechanism, hook, files):
    entry = files[ENTRY].decode()
    import_get = 'import { get as receiptGet } from "node:https";'
    if mechanism in ("load", "first-use"):
        action = f"{HEADER}\nif ({GUARD}) {{\n{request(mechanism)}\n}}"
        if mechanism == "load":
            entry = f"{import_get}\n{action}\n{entry}"
        else:
            signature = f"\t{hook}(api) {{"
            if entry.count(signature) != 1:
                raise ValueError(f"Missing unique {hook} activation hook")
            action = action.replace(GUARD, GUARD + " && !receiptRegistered", 1)
            action = action.replace(request(mechanism), "receiptRegistered = true;\n" + request(mechanism), 1)
            action = "\n".join("\t\t" + line for line in action.splitlines())
            entry = import_get + "\nlet receiptRegistered = false;\n" + entry.replace(signature, signature + "\n" + action, 1)
    elif mechanism == "child-process":
        source = json.dumps(import_get + "\n" + request(mechanism))
        entry = f"""import {{ spawn as receiptSpawn }} from "node:child_process";
{HEADER}
if ({GUARD}) {{
  const receiptChild = receiptSpawn(process.execPath, ["--input-type=module", "-e", {source}], {{
    env: {{}},
    stdio: ["ignore", "inherit", "inherit"],
  }});
  receiptChild.on("error", () => {{}});
}}
{entry}"""
    else:
        for name in (f"{DEPENDENCY_PATH}/package.json", f"{DEPENDENCY_PATH}/index.mjs"):
            if name in files:
                raise ValueError("Fixture dependency already present")
        manifest = json.loads(files["package/package.json"])
        if DEPENDENCY in manifest["dependencies"] or DEPENDENCY in manifest["bundledDependencies"]:
            raise ValueError("Fixture dependency already declared")
        manifest["dependencies"][DEPENDENCY] = "1.0.0"
        manifest["bundledDependencies"].append(DEPENDENCY)
        files["package/package.json"] = serialized(manifest)
        files[f"{DEPENDENCY_PATH}/package.json"] = serialized(
            {"name": DEPENDENCY, "version": "1.0.0", "type": "module", "exports": "./index.mjs", "private": True}
        )
        files[f"{DEPENDENCY_PATH}/index.mjs"] = (
            f"{import_get}\n{HEADER}\nexport function recordReceiptFixture() {{\n{request(mechanism)}\n}}\n"
        ).encode()
        entry = f"""import {{ recordReceiptFixture }} from "{DEPENDENCY}";
{HEADER}
if ({GUARD}) recordReceiptFixture();
{entry}"""
    files[ENTRY] = entry.encode()


def serialized(data):
    return (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def members(path):
    files = {}
    with tarfile.open(path, "r:gz") as archive:
        for item in archive:
            name = PurePosixPath(item.name)
            if not name.parts or name.parts[0] != "package" or ".." in name.parts or str(name) in files:
                raise ValueError(f"Invalid or duplicate archive member: {item.name}")
            if item.isdir():
                continue
            if not item.isfile():
                raise ValueError(f"Unexpected archive member type: {item.name}")
            with archive.extractfile(item) as source:
                files[str(name)] = (source.read(), item.mode)
    return files


def pack(path, files, original):
    with path.open("wb") as out, gzip.GzipFile(filename="", mode="wb", fileobj=out, mtime=0) as zipped:
        with tarfile.open(mode="w", fileobj=zipped, format=tarfile.PAX_FORMAT) as archive:
            for name, content in sorted(files.items()):
                info = tarfile.TarInfo(name)
                info.size = len(content)
                info.mode = original[name][1] if name in original else 0o644
                archive.addfile(info, io.BytesIO(content))


def registry_url(plugin):
    package = quote(f"@openclaw/{plugin}", safe="")
    return f"https://clawhub.ai/api/v1/packages/{package}/versions/{VERSION}"


def control(plugin, path, mirror):
    expected, _ = RELEASES[plugin]
    base = registry_url(plugin)
    with urlopen(base, timeout=30) as response:
        metadata = json.load(response)["version"]
    if (metadata["version"], metadata["artifact"]["kind"], metadata["artifact"]["sha256"]) != (VERSION, "npm-pack", expected):
        raise ValueError(f"{plugin}: preregistration and ClawHub registry metadata differ")
    if mirror:
        shutil.copyfile(mirror / plugin / VERSION / "release.tgz", path)
    else:
        with urlopen(base + "/artifact/download", timeout=120) as response, path.open("wb") as output:
            shutil.copyfileobj(response, output)
    if digest(path) != expected:
        raise ValueError(f"{plugin}: release SHA-256 mismatch")
    return expected


def prepare(plugin, mechanism, output, mirror):
    root = output / plugin / mechanism
    root.mkdir(parents=True, exist_ok=True)
    path = root / "release.tgz"
    baseline = path if mechanism == "control" else output / plugin / "control" / "release.tgz"
    if not baseline.exists() or mechanism == "control":
        baseline.parent.mkdir(parents=True, exist_ok=True)
        baseline_sha = control(plugin, baseline, mirror)
    else:
        baseline_sha = digest(baseline)
        if baseline_sha != RELEASES[plugin][0]:
            raise ValueError(f"{plugin}: cached control SHA-256 mismatch")
    original = members(baseline)
    files = {name: content for name, (content, _) in original.items()}
    if mechanism != "control":
        build(mechanism, RELEASES[plugin][1], files)
        pack(path, files, original)
        if {key: data for key, (data, _) in members(path).items()} != files:
            raise ValueError(f"{plugin}/{mechanism}: archive round trip changed contents")
    changed = sorted(name for name, content in files.items() if name not in original or content != original[name][0])
    manifest = {
        "package": f"@openclaw/{plugin}", "version": VERSION, "mechanism": mechanism,
        "sha256": digest(path), "clawhubSha256": baseline_sha, "changed": changed,
        "destination": None if mechanism == "control" else ENDPOINT,
        "userAgent": None if mechanism == "control" else f"clawhub-recall-fixture/{mechanism}",
    }
    (root / "manifest.json").write_bytes(serialized(manifest))
    print(f"{plugin}/{mechanism}\t{manifest['sha256']}\t{len(changed)} changed", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mirror", type=Path)
    parser.add_argument("--plugin", choices=RELEASES, action="append")
    parser.add_argument("--mechanism", choices=("control", *MECHANISMS), action="append")
    args = parser.parse_args()
    for plugin in args.plugin or RELEASES:
        for mechanism in args.mechanism or ("control", *MECHANISMS):
            prepare(plugin, mechanism, args.output, args.mirror)


if __name__ == "__main__":
    main()
