"""Offline release controller rejects incomplete or unauthorized production proof."""

import json
import uuid

import pytest

from app.maintenance.course_release import ROOT, Journey, configuration
from app.maintenance.release_http import SEARCH_URL
from app.maintenance.release_journal import Journal, title_for

KEY = "public-synthetic-course-release-test-key-001"


@pytest.fixture
def environment():
    from app.maintenance.release_fixtures import credentials

    return {
        "EA_RELEASE_FIXTURE_KEY": KEY,
        "EA_RELEASE_FIXTURE_CREDENTIALS": json.dumps(credentials(KEY)),
        "EXPECTED_SHA": "a" * 40,
        "EXPECTED_SEARCH_SPHERE_SHA": "b" * 40,
    }


class FakeHttp:
    def __init__(self, environment, *, failure=None, existing=0):
        self.identity = json.loads(environment["EA_RELEASE_FIXTURE_CREDENTIALS"])
        self.environment, self.failure = environment, failure
        self.rows, self.deleted, self.calls = {}, set(), []
        self.last_marker = None
        self.class_by_id = {
            value["class_id"]: school
            for school, value in self.identity["schools"].items()
        }
        self.class_by_id[self.identity["schools"]["a"]["other_class_id"]] = "a"
        for index in range(existing):
            identifier = str(uuid.uuid4())
            self.rows[identifier] = self.row(
                identifier, "a", title_for(KEY, f"{index:032x}", "a")
            )

    def row(self, identifier, label, title):
        school = "b" if label == "b" else "a"
        return {
            "id": identifier,
            "title": title,
            "schoolId": self.identity["schools"][school]["id"],
            "classId": self.identity["schools"][school][
                "other_class_id" if label == "other-a" else "class_id"
            ],
            "label": label,
            "text": "Owned previous synthetic fixture",
        }

    def session(self, base=None):
        state = self

        class Session:
            actor = None

            def request(self, method, path, **kwargs):
                state.calls.append((method, path, self.actor))
                if path == "/health":
                    return 200, {
                        "git_commit": state.environment["EXPECTED_SEARCH_SPHERE_SHA"]
                    }
                if path == "/api/health":
                    return 200, {
                        "git_commit": (
                            "c" * 40
                            if state.failure == "revision"
                            else state.environment["EXPECTED_SHA"]
                        )
                    }
                if path == "/api/v1/auth/login":
                    for label, account in state.identity["accounts"].items():
                        if account["email"] == kwargs["value"]["email"]:
                            self.actor = label
                            return 200, {
                                "id": account["user_id"],
                                "role": label.split("-")[0].upper(),
                            }
                    return 401, {}
                school = self.actor[-1]
                if path.startswith(ROOT + "?"):
                    from urllib.parse import parse_qs, urlsplit

                    offset = int(parse_qs(urlsplit(path).query)["offset"][0])
                    rows = [
                        row
                        for row in state.rows.values()
                        if row["schoolId"] == state.identity["schools"][school]["id"]
                    ]
                    return 200, {
                        "items": rows[offset : offset + 50],
                        "total": len(rows),
                    }
                if path == ROOT + "/upload":
                    fields = kwargs["fields"]
                    label = (
                        "b"
                        if school == "b"
                        else (
                            "other-a"
                            if fields["class_id"]
                            == state.identity["schools"]["a"]["other_class_id"]
                            else "a"
                        )
                    )
                    identifier = str(uuid.uuid4())
                    row = state.row(identifier, label, fields["title"])
                    # Decode only a public generated fixture, not an actual API response.
                    import re

                    marker = re.search(rb"EA_MARKER_[0-9a-f]+", kwargs["pdf"])[
                        0
                    ].decode()
                    row["text"] = (
                        marker
                        + ": The synthetic atlas color is "
                        + {"a": "violet", "b": "teal", "other-a": "amber"}[label]
                        + "."
                    )
                    state.rows[identifier] = row
                    if state.failure == "lost_upload_response":
                        raise TimeoutError("PRIVATE SYNTHETIC DIAGNOSTIC")
                    return 201, row
                if path.endswith("/refresh-status"):
                    identifier = path.split("/")[-2]
                    return 200, {
                        "material_id": identifier,
                        "status": "FAILED" if state.failure == "index" else "READY",
                    }
                if path == ROOT + "/search":
                    body = kwargs["value"]
                    class_id = body["class_id"]
                    if (
                        self.actor.startswith("student")
                        and class_id != state.identity["schools"][school]["class_id"]
                    ):
                        return 403, {}
                    rows = [
                        row
                        for row in state.rows.values()
                        if row["classId"] == class_id
                        and row["schoolId"] == state.identity["schools"][school]["id"]
                    ]
                    if state.failure == "foreign_search" and rows:
                        return 200, {
                            "results": [
                                {"material_id": "foreign", "text": rows[0]["text"]}
                            ]
                        }
                    return 200, {
                        "results": [
                            {"material_id": row["id"], "text": row["text"]}
                            for row in rows
                        ]
                    }
                if path == ROOT + "/answer":
                    row = next(
                        row for row in state.rows.values() if row["label"] == "a"
                    )
                    if state.failure == "provider":
                        return 503, {"detail": "PRIVATE SYNTHETIC PROVIDER DIAGNOSTIC"}
                    return 200, {
                        "answer": "The synthetic atlas color is violet. [1]",
                        "citations": [
                            {
                                "materialId": (
                                    "foreign"
                                    if state.failure == "citation"
                                    else row["id"]
                                ),
                                "pageNumber": 1,
                                "chunkId": "synthetic-chunk",
                                "citationNumber": 1,
                                "textSnippet": row["text"],
                            }
                        ],
                    }
                if path.endswith("/cleanup"):
                    identifier = path.split("/")[-2]
                    return (503 if state.failure == "cleanup_503" else 200), {
                        "document_id": identifier,
                        "status": "complete",
                        "vectors_remaining": 1 if state.failure == "vectors" else 0,
                        "derived_objects_remaining": 0,
                        "object_deleted": True,
                    }
                identifier = path.split("/")[-1]
                row = state.rows.get(identifier)
                if method == "DELETE":
                    if row:
                        state.rows.pop(identifier)
                        state.deleted.add(identifier)
                        return 200, {"success": True}
                    return 404, {}
                if (
                    row
                    and row["schoolId"] == state.identity["schools"][school]["id"]
                    and (
                        not self.actor.startswith("student")
                        or row["classId"]
                        == state.identity["schools"][school]["class_id"]
                    )
                ):
                    return 200, row
                return 404, {}

        return Session()


def test_complete_three_pdf_journey_and_physical_cleanup(environment, tmp_path, capsys):
    http = FakeHttp(environment)
    journey = Journey(
        environment, session_factory=http.session, path=tmp_path / "receipts.json"
    )
    journey.run()
    assert len(http.deleted) == 3 and http.rows == {}
    assert all(entry["complete"] for entry in journey.journal.entries.values())
    output = capsys.readouterr().out
    assert "PASS authenticated upload" in output
    assert "EA_MARKER" not in output and "@example.com" not in output
    artifact = (tmp_path / "receipts.json").read_text()
    assert "password" not in artifact and "atlas color" not in artifact


@pytest.mark.parametrize(
    "failure",
    [
        "index",
        "foreign_search",
        "provider",
        "citation",
        "cleanup_503",
        "vectors",
        "lost_upload_response",
    ],
)
def test_failed_assertions_never_pass_and_attempt_owned_cleanup(
    environment, tmp_path, capsys, failure
):
    http = FakeHttp(environment, failure=failure)
    journey = Journey(
        environment, session_factory=http.session, path=tmp_path / "receipts.json"
    )
    with pytest.raises(AssertionError):
        journey.run()
    assert http.deleted and not http.rows
    assert "PASS authenticated upload" not in capsys.readouterr().out
    if failure in {"cleanup_503", "vectors"}:
        assert any(not entry["complete"] for entry in journey.journal.entries.values())


def test_revision_mismatch_stops_before_login_or_mutation(environment, tmp_path):
    http = FakeHttp(environment, failure="revision")
    with pytest.raises(AssertionError):
        Journey(
            environment, session_factory=http.session, path=tmp_path / "receipt"
        ).run()
    assert len(http.calls) == 1 and http.rows == {}


def test_offset_pagination_sweeps_only_owned_fixtures(environment, tmp_path):
    http = FakeHttp(environment, existing=51)
    foreign_id = str(uuid.uuid4())
    http.rows[foreign_id] = http.row(foreign_id, "a", "unowned document")
    journey = Journey(
        environment, session_factory=http.session, path=tmp_path / "receipt"
    )
    journey.preflight()
    journey.discover()
    journey.cleanup()
    assert len(http.deleted) == 51 and foreign_id in http.rows
    assert any("offset=50" in path for _, path, _ in http.calls)


@pytest.mark.parametrize(
    "field",
    [
        "EA_RELEASE_FIXTURE_KEY",
        "EA_RELEASE_FIXTURE_CREDENTIALS",
        "EXPECTED_SHA",
        "EXPECTED_SEARCH_SPHERE_SHA",
    ],
)
def test_missing_required_inputs_fail(environment, field):
    environment.pop(field)
    with pytest.raises((AssertionError, KeyError)):
        configuration(environment)


def test_foreign_credentials_cannot_be_used_for_the_gate(environment):
    value = json.loads(environment["EA_RELEASE_FIXTURE_CREDENTIALS"])
    value["accounts"]["teacher-a"]["email"] = "a-real-user@example.com"
    environment["EA_RELEASE_FIXTURE_CREDENTIALS"] = json.dumps(value)
    with pytest.raises(AssertionError, match="Unowned synthetic login"):
        configuration(environment)
