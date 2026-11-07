"""Authenticated synthetic PDF journey; no service internals or privileged DB key."""

import hashlib
import hmac
import json
import os
import re
import sys
import time
import uuid

from app.maintenance.release_evidence import verify_evidence
from app.maintenance.release_http import (
    ROOT,
    SEARCH_URL,
    Session,
    require,
    wait_for_service,
)
from app.maintenance.release_journal import Journal, owned_title

JOURNAL_PATH = ".ea_release_receipts.json"


class ObservedSession:
    """Report status codes only, keeping cookies, URLs and bodies private."""

    def __init__(self, session):
        self.session = session

    def request(self, *args, **kwargs):
        code, value = self.session.request(*args, **kwargs)
        if type(code) is int and not 200 <= code < 300 and code not in (403, 404):
            print("HTTP_STATUS " + str(code), flush=True)
        return code, value


def configuration(environment):
    key = environment.get("EA_RELEASE_FIXTURE_KEY", "")
    require(len(key) >= 32, "Missing release ownership key")
    value = json.loads(environment.get("EA_RELEASE_FIXTURE_CREDENTIALS", "null"))
    require(
        isinstance(value, dict) and value.get("version") == 1,
        "Missing synthetic credentials",
    )

    # Independently bind credentials to the bootstrap's versioned HMAC identity contract.
    def token(label):
        return hmac.new(
            key.encode(), ("exam-arena-release-v1:" + label).encode(), "sha256"
        ).hexdigest()

    def identifier(label):
        return str(uuid.UUID(token(label)[:32]))

    require(
        set(value["accounts"])
        == {
            role + "-" + school
            for role in ("teacher", "student")
            for school in ("a", "b")
        },
        "Unexpected fixture accounts",
    )
    require(set(value["schools"]) == {"a", "b"}, "Unexpected fixture schools")
    for school in ("a", "b"):
        scope = value["schools"][school]
        require(
            scope["id"] == identifier("school-" + school)
            and scope["class_id"] == identifier("class-" + school),
            "Unowned fixture school",
        )
        for role in ("teacher", "student"):
            label = role + "-" + school
            account = value["accounts"][label]
            require(
                account["user_id"] == identifier(label)
                and account["profile_id"] == identifier("profile-" + label)
                and account["email"]
                == "ss-release-" + token(label)[:24] + "@example.com"
                and hmac.compare_digest(
                    account["password"], token("password-" + label)[:48] + "!Aa7"
                ),
                "Unowned synthetic login",
            )
    require(
        value["schools"]["a"]["other_class_id"] == identifier("other-class-a"),
        "Unowned fixture class",
    )
    for field in ("EXPECTED_SHA", "EXPECTED_SEARCH_SPHERE_SHA"):
        require(
            re.fullmatch(r"[0-9a-f]{40}", environment.get(field, "")),
            "Missing exact deployed revision",
        )
    return key, value


class Journey:
    def __init__(
        self,
        environment,
        *,
        session_factory=Session,
        path=JOURNAL_PATH,
        sleep=time.sleep,
        clock=time.monotonic,
    ):
        self.key, self.identity = configuration(environment)
        self.expected = environment
        self.sessions = {
            label: ObservedSession(session_factory())
            for label in self.identity["accounts"]
        }
        self.public = ObservedSession(session_factory())
        self.search = ObservedSession(session_factory(SEARCH_URL))
        self.journal = Journal(path, self.key)
        self.sleep, self.clock = sleep, clock
        self.stage = "configuration"

    def step(self, name):
        self.stage = name
        print("CHECK " + name, flush=True)

    def preflight(self):
        self.step("exact deployed revisions")
        wait_for_service(
            self.public, "/api/health", self.expected["EXPECTED_SHA"], sleep=self.sleep
        )
        wait_for_service(
            self.search,
            "/health",
            self.expected["EXPECTED_SEARCH_SPHERE_SHA"],
            sleep=self.sleep,
        )
        wait_for_service(
            self.search,
            "/ready",
            self.expected["EXPECTED_SEARCH_SPHERE_SHA"],
            ready=True,
            sleep=self.sleep,
        )
        self.step("synthetic login and roles")
        for label, account in self.identity["accounts"].items():
            code, value = self.sessions[label].request(
                "POST",
                "/api/v1/auth/login",
                value={"email": account["email"], "password": account["password"]},
            )
            require(
                code == 200
                and value.get("id") == account["user_id"]
                and value.get("role") == label.split("-")[0].upper(),
                "Synthetic login identity failed",
            )

    def teacher(self, label):
        return self.sessions["teacher-b" if label == "b" else "teacher-a"]

    def class_id(self, label):
        school = self.identity["schools"]["b" if label == "b" else "a"]
        return school["other_class_id" if label == "other-a" else "class_id"]

    def discover(self):
        self.step("recover signed uploaded fixtures")
        for school in ("a", "b"):
            offset, owned = 0, []
            for _ in range(40):
                code, value = self.sessions["teacher-" + school].request(
                    "GET", ROOT + f"?limit=50&offset={offset}"
                )
                require(
                    code == 200
                    and isinstance(value.get("items"), list)
                    and type(value.get("total")) is int,
                    "Fixture listing unavailable",
                )
                rows = value["items"]
                for row in rows:
                    label = owned_title(self.key, row.get("title"))
                    if label:
                        require(
                            (label == "b") == (school == "b"),
                            "Fixture school signature mismatch",
                        )
                        require(
                            row.get("classId") == self.class_id(label)
                            and row.get("schoolId")
                            == self.identity["schools"][school]["id"],
                            "Fixture catalog scope mismatch",
                        )
                        owned.append((row["id"], label, row["title"]))
                offset += len(rows)
                if offset >= value["total"]:
                    break
                require(rows, "Fixture pagination stopped early")
            else:
                raise AssertionError("Fixture listing exceeds recovery bound")
            for identifier, label, title in owned:
                self.journal.add(identifier, label, title)

    def cleanup(self):
        self.step("delete and verify physical cleanup")
        errors = []
        for entry in list(self.journal.entries.values()):
            if entry["complete"]:
                continue
            try:
                session = self.teacher(entry["label"])
                path = ROOT + "/" + entry["id"]
                code, _ = session.request("DELETE", path)
                require(code in (200, 404), "Fixture deletion unavailable")
                code, _ = session.request("GET", path)
                require(code == 404, "Deleted metadata remains accessible")
                deadline = self.clock() + 120
                while True:
                    code, value = session.request("GET", path + "/cleanup")
                    require(
                        code == 200 and value.get("document_id") == entry["id"],
                        "Physical cleanup receipt unavailable",
                    )
                    require(
                        value.get("status") in ("pending", "complete"),
                        "Unknown cleanup state",
                    )
                    if value["status"] == "complete":
                        require(
                            type(value.get("vectors_remaining")) is int
                            and value["vectors_remaining"] == 0
                            and type(value.get("derived_objects_remaining")) is int
                            and value["derived_objects_remaining"] == 0
                            and value.get("object_deleted") is True,
                            "Physical cleanup incomplete",
                        )
                        code, results = session.request(
                            "POST",
                            ROOT + "/search",
                            value={
                                "query": entry["title"],
                                "subject": "SCIENCE",
                                "class_id": self.class_id(entry["label"]),
                            },
                        )
                        require(
                            code == 200
                            and isinstance(results.get("results"), list)
                            and all(
                                row.get("material_id") != entry["id"]
                                for row in results["results"]
                            ),
                            "Deleted evidence remains retrievable",
                        )
                        self.journal.complete(entry["id"])
                        break
                    require(self.clock() < deadline, "Physical cleanup timed out")
                    self.sleep(2)
            except Exception as error:
                errors.append(type(error).__name__)
        require(not errors, "One or more owned physical cleanups failed")

    def exercise(self):
        verify_evidence(self)

    def run(self):
        self.preflight()
        primary, cleanup_error = None, None
        try:
            self.discover()
            self.cleanup()
            self.exercise()
        except Exception as error:
            primary = (self.stage, type(error).__name__)
        try:
            self.discover()
            self.cleanup()
        except Exception as error:
            cleanup_error = (self.stage, type(error).__name__)
        if primary:
            print("FAIL " + primary[0] + " (" + primary[1] + ")", flush=True)
        if cleanup_error:
            print("FAIL cleanup verification (" + cleanup_error[1] + ")", flush=True)
        require(
            not primary and not cleanup_error,
            "Authenticated course-material journey failed",
        )
        require(
            self.journal.entries
            and all(entry["complete"] for entry in self.journal.entries.values()),
            "Incomplete fixture journal",
        )
        print(
            "PASS authenticated upload/index/retrieval/answer/citations/isolation/physical cleanup",
            flush=True,
        )


if __name__ == "__main__":
    try:
        if "--preflight" in sys.argv:
            configuration(os.environ)
            print("PASS required synthetic credentials and revision inputs")
        else:
            Journey(os.environ).run()
    except Exception as error:
        print(
            "FAIL authenticated release gate ("
            + type(error).__name__
            + "); inspect CHECK stage above.",
            file=sys.stderr,
        )
        raise SystemExit(1) from None
