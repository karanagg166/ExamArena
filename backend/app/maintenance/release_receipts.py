"""Restore the previous trusted course release journal using GitHub's scoped CLI."""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from app.maintenance.course_release import JOURNAL_PATH, configuration
from app.maintenance.release_journal import Journal

REPO = "karanagg166/ExamArena"
WORKFLOW = "course-material-journey.yml"
STEP = "Run authenticated synthetic course-material journey"


def gh(*arguments):
    result = subprocess.run(
        ["gh", *arguments], capture_output=True, text=True, timeout=45, check=False
    )
    if result.returncode:
        raise RuntimeError("Trusted fixture receipt lookup failed.")
    return result.stdout


def restore(environment, command=gh):
    key, _ = configuration(environment)
    current = environment.get("GITHUB_RUN_ID", "")
    if not re.fullmatch(r"[0-9]+", current) or not environment.get("GH_TOKEN"):
        raise ValueError("Trusted workflow identity and read token are required.")
    journal = Journal(JOURNAL_PATH, key)
    runs = json.loads(
        command(
            "run",
            "list",
            "--repo",
            REPO,
            "--workflow",
            WORKFLOW,
            "--branch",
            "main",
            "--limit",
            "20",
            "--json",
            "databaseId,event,headBranch",
        )
    )
    if not isinstance(runs, list):
        raise ValueError("Invalid trusted workflow history.")
    for run in runs:
        identifier = str(run["databaseId"])
        if identifier == current:
            continue
        if (
            not re.fullmatch(r"[0-9]+", identifier)
            or run["event"] != "workflow_dispatch"
            or run["headBranch"] != "main"
        ):
            raise ValueError("Untrusted receipt history.")
        name = "course-material-fixture-receipts-" + identifier
        value = json.loads(
            command(
                "api", f"repos/{REPO}/actions/runs/{identifier}/artifacts?per_page=100"
            )
        )
        if value.get("total_count", 0) >= 100:
            raise ValueError("Receipt artifact lookup exceeds its bound.")
        matches = [item for item in value["artifacts"] if item.get("name") == name]
        if matches:
            if len(matches) != 1 or matches[0].get("expired"):
                raise ValueError(
                    "Prior fixture receipt is unavailable; operator reconciliation required."
                )
            with tempfile.TemporaryDirectory(
                prefix="ea-release-receipts-"
            ) as temporary:
                command(
                    "run",
                    "download",
                    identifier,
                    "--repo",
                    REPO,
                    "--name",
                    name,
                    "--dir",
                    temporary,
                )
                journal.import_path(Path(temporary) / JOURNAL_PATH)
            journal.save()
            print("PASS prior signed synthetic receipts restored")
            return
        # A run that never entered the mutating step cannot own uploaded fixtures.
        jobs = json.loads(
            command("api", f"repos/{REPO}/actions/runs/{identifier}/jobs?per_page=100")
        )
        steps = [
            step
            for job in jobs.get("jobs", [])
            for step in job.get("steps", [])
            if step.get("name") == STEP
        ]
        if not steps or any(step.get("conclusion") != "skipped" for step in steps):
            raise ValueError(
                "Missing prior cleanup provenance; operator reconciliation required."
            )
    if len(runs) >= 20:
        raise ValueError("Receipt history exceeds recovery bound.")
    journal.save()
    print("PASS initial signed synthetic receipt journal")


if __name__ == "__main__":
    try:
        restore(os.environ)
    except Exception as error:
        print(
            "FAIL fixture receipt restore ("
            + type(error).__name__
            + "); reconcile protected workflow receipts.",
            file=sys.stderr,
        )
        raise SystemExit(1) from None
