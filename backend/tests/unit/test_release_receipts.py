"""Restoration accepts only prior trusted workflow artifacts and signed receipts."""

import json
import uuid
from pathlib import Path

import pytest

from app.maintenance.course_release import JOURNAL_PATH
from app.maintenance.release_journal import Journal, title_for
from app.maintenance.release_receipts import STEP, restore
from tests.unit import test_course_release as course_support

environment = course_support.environment


def fake_command(key, *, history=True, artifact=True, expired=False, skipped=False):
    def command(*args):
        if args[:2] == ("run", "list"):
            return json.dumps(
                [{"databaseId": 99, "event": "workflow_dispatch", "headBranch": "main"}]
                if history
                else []
            )
        if args[0] == "api" and "artifacts?" in args[1]:
            return json.dumps(
                {
                    "total_count": int(artifact),
                    "artifacts": (
                        [
                            {
                                "name": "course-material-fixture-receipts-99",
                                "expired": expired,
                            }
                        ]
                        if artifact
                        else []
                    ),
                }
            )
        if args[0] == "api" and "jobs?" in args[1]:
            return json.dumps(
                {
                    "jobs": [
                        {
                            "steps": [
                                {
                                    "name": STEP,
                                    "conclusion": "skipped" if skipped else "failure",
                                }
                            ]
                        }
                    ]
                }
            )
        if args[:2] == ("run", "download"):
            target = Path(args[args.index("--dir") + 1]) / JOURNAL_PATH
            journal = Journal(target, key)
            journal.add(str(uuid.uuid4()), "a", title_for(key, uuid.uuid4().hex, "a"))
            return ""
        raise AssertionError("Unexpected synthetic command")

    return command


@pytest.mark.parametrize("history", [True, False])
def test_restore_owned_receipts_or_start_initial_journal(
    environment, monkeypatch, tmp_path, history
):
    monkeypatch.chdir(tmp_path)
    environment.update(GITHUB_RUN_ID="100", GH_TOKEN="public-synthetic-gh-token")
    key = environment["EA_RELEASE_FIXTURE_KEY"]
    restore(environment, fake_command(key, history=history))
    journal = Journal(JOURNAL_PATH, key)
    assert len(journal.entries) == int(history)


@pytest.mark.parametrize("failure", ["expired", "missing", "foreign_owner"])
def test_missing_or_invalid_provenance_fails_closed(
    environment, monkeypatch, tmp_path, failure
):
    monkeypatch.chdir(tmp_path)
    environment.update(GITHUB_RUN_ID="100", GH_TOKEN="public-synthetic-gh-token")
    key = (
        environment["EA_RELEASE_FIXTURE_KEY"]
        if failure != "foreign_owner"
        else "public-foreign-synthetic-fixture-owner-key-001"
    )
    with pytest.raises(ValueError):
        restore(
            environment,
            fake_command(
                key, artifact=failure != "missing", expired=failure == "expired"
            ),
        )
    assert not Path(JOURNAL_PATH).exists()


def test_prior_run_that_never_entered_mutating_step_can_be_skipped(
    environment, monkeypatch, tmp_path
):
    monkeypatch.chdir(tmp_path)
    environment.update(GITHUB_RUN_ID="100", GH_TOKEN="public-synthetic-gh-token")
    restore(
        environment,
        fake_command(
            environment["EA_RELEASE_FIXTURE_KEY"], artifact=False, skipped=True
        ),
    )
    assert Journal(JOURNAL_PATH, environment["EA_RELEASE_FIXTURE_KEY"]).entries == {}
