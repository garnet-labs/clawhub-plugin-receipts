#!/usr/bin/env python3
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import time

from prepare import digest, members, serialized

IMAGE = "ghcr.io/openclaw/clawscan-runtime@sha256:d494938b84a9f0da40504f611eec472d4637c755b5cef87b123daf8a2014545c"
COMMIT = "96e9849d610a9971fee885992bdf90242c3f1f81"


def scan(archive, output, cli, repeat):
    manifest = json.loads(archive.with_name("manifest.json").read_text())
    if digest(archive) != manifest["sha256"]:
        raise ValueError(f"Archive does not match manifest: {archive}")
    output.mkdir(parents=True, exist_ok=True)
    package = output / "input"
    for member, (data, _) in members(archive).items():
        path = package / member
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    env = dict(os.environ)
    env.update(
        LLM_API_KEY=env["AI_GATEWAY_API_KEY"], CODEX_API_KEY=env["AI_GATEWAY_API_KEY"],
        DEFAULT_BASE_URL="https://ai-gateway.vercel.sh/v1", OPENAI_BASE_URL="https://ai-gateway.vercel.sh/v1",
        DEFAULT_MODEL="openai/gpt-6.1-sol", OVERVIEW_MODEL="openai/gpt-6-luna",
    )
    raw, log = output / "raw.json", output / "scan.log"
    start = time.monotonic()
    with log.open("wb") as handle:
        result = subprocess.run(
            ["timeout", "35m", cli, package / "package", "--profile", "clawhub",
             "--sandbox-image", IMAGE, "--output", raw],
            env=env, stdout=handle, stderr=subprocess.STDOUT,
        )
    elapsed = round(time.monotonic() - start, 1)
    document = json.loads(raw.read_text()) if raw.exists() else {}
    judge = document.get("judge") or {}
    sarif = document.get("scanners", {}).get("aig-mcp", {})
    summary = {
        **manifest, "repeat": repeat, "elapsedSeconds": elapsed, "exitCode": result.returncode,
        "complete": document.get("complete") is True, "status": document.get("status"),
        "gate": document.get("gate"), "verdict": (judge.get("result") or {}).get("verdict"),
        "scanner": sarif.get("status"), "judge": judge.get("status"),
        "profile": "clawhub", "scannerCommit": COMMIT, "runtimeImage": IMAGE,
    }
    (output / "summary.json").write_bytes(serialized(summary))
    print(f"{archive.parent.parent.name}/{archive.parent.name} #{repeat}: "
          f"{elapsed}s complete={summary['complete']} verdict={summary['verdict']} exit={result.returncode}", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--archives", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--cli", required=True, type=Path)
    parser.add_argument("--parallel", default=6, type=int)
    args = parser.parse_args()
    archives = sorted(args.archives.glob("*/*/release.tgz"))
    if len(archives) != 10:
        raise ValueError(f"Expected eight variants and two controls, got {len(archives)}")
    if not os.environ.get("AI_GATEWAY_API_KEY"):
        raise ValueError("Gateway credential unavailable")
    with ThreadPoolExecutor(max_workers=args.parallel) as pool:
        futures = [
            pool.submit(scan, archive,
                        args.output / archive.parent.parent.name / archive.parent.name / str(repeat), args.cli, repeat)
            for repeat in range(1, 4) for archive in archives
        ]
        for future in futures:
            future.result()


if __name__ == "__main__":
    main()
