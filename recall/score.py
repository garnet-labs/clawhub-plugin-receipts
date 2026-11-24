#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from prepare import MECHANISMS, RELEASES

ORDER = ("control", *MECHANISMS)
TICK = chr(96)


def code(value):
    value = str(value).replace(TICK, "&#96;").replace("|", "&#124;").replace("\n", " ")
    return TICK + value + TICK


def link(path, root, label):
    return f"[{label}]({path.relative_to(root).as_posix()})"


def eligible(summary):
    return (summary["exitCode"] == 0 and summary["complete"] and
            summary["scanner"] == "completed" and summary["judge"] == "completed" and
            summary["verdict"] is not None)


def row_summary(root, plugin, mechanism, reviews):
    runs, hits = [], []
    attempted = 0
    adjudicated = 0
    for repeat in range(1, 4):
        target = root / "out" / "scans" / plugin / mechanism / str(repeat)
        path = target / "summary.json"
        if not path.is_file():
            runs.append(f"{repeat}: pending")
            continue
        attempted += 1
        status = json.loads(path.read_text())
        summary_link = link(path, root, f"{repeat}: {status['verdict'] or 'unavailable'} ({status['elapsedSeconds']}s)")
        key = f"{plugin}/{mechanism}/{repeat}"
        if not eligible(status):
            runs.append(summary_link + " — ineligible")
            continue
        if key not in reviews:
            runs.append(summary_link + " — awaiting evidence review")
            continue
        reasons = reviews[key]
        if not isinstance(reasons, list) or any(not isinstance(reason, str) or not reason for reason in reasons):
            raise ValueError(f"Invalid adjudication for {key}")
        adjudicated += 1
        runs.append(summary_link + (" — hit" if reasons else " — no hit"))
        if reasons:
            hits.append((repeat, link(target / "raw.json", root, "finding output"), reasons))
    verdict = "caught" if hits else "not caught" if adjudicated == 3 else "undeterminable"
    if mechanism == "control" and hits:
        verdict = "false positive"
    return verdict, adjudicated, attempted, runs, hits


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--reviews", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    reviews = json.loads(args.reviews.read_text()) if args.reviews else {}
    trials = 0
    rendered = [
        "# Planted-action recall",
        "",
        "[Preregistered protocol](recall/PREREGISTRATION.md) · [Plant disclosures](recall/README.md)",
        "",
        "This report covers the static arm. The runtime score requires finalized, head-bound "
        "PR comparisons; all Garnet scores, both/neither buckets, App links and overlap labels "
        "are pending, not misses. This does not estimate malware recall.",
        "",
        "The byte-identical ClawHub controls and eight derived archives were checked against their "
        "tracked or generated SHA-256 values. The pinned stock ClawScan profile is "
        f"{code('clawhub')}; scans overlap, and the times below are per-run wall clock.",
        "",
        "| Base release | Mechanism | Archive SHA-256 | ClawScan | Garnet | Joint result | Scan runs |",
        "|---|---|---|---|---|---|---|",
    ]
    evidence = []
    for plugin in RELEASES:
        for mechanism in ORDER:
            manifest = root / "out" / "archives" / plugin / mechanism / "manifest.json"
            digest = json.loads(manifest.read_text())["sha256"]
            verdict, reviewed, attempted, runs, hits = row_summary(root, plugin, mechanism, reviews)
            trials += attempted
            rendered.append(
                f"| {code('@openclaw/' + plugin + '@2026.11.7')} | {mechanism} | "
                f"{link(manifest, root, code(digest))} | {verdict} ({len(hits)}/{reviewed} reviewed) | "
                f"undeterminable | undeterminable | {'; '.join(runs)} |"
            )
            for repeat, raw, reasons in hits:
                for reason in reasons:
                    evidence.append(f"- **{plugin} · {mechanism} · run {repeat}:** {reason} ({raw}).")
    rendered += [
        "",
        f"Static batch: {trials}/30 run summaries available.",
        "",
        "Only a specific plant-related finding qualifies. Verdict-only changes, behavior mentioned only in "
        "overview text, and file-exclusion inventory are not hits. A no-hit cell is undeterminable until "
        "all three eligible runs have been reviewed.",
        "",
        "## Findings that met the static recall criterion",
        "",
        *(evidence or ["No qualifying finding recorded in the reviewed evidence yet."]),
    ]
    (root / "recall-report.md").write_text("\n".join(rendered) + "\n")
    print(f"Static report: {trials}/30 summaries; {len(reviews)} evidence adjudications; {len(evidence)} qualifying finding records.")


if __name__ == "__main__":
    main()
