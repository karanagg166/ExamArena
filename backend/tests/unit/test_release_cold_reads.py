"""Only transient, read-only health probes may retry before authenticated work."""

import pytest

from app.maintenance.release_http import wait_for_service

SHA = "a" * 40


class HealthSession:
    def __init__(self, responses):
        self.responses, self.calls = iter(responses), []

    def request(self, method, path):
        self.calls.append((method, path))
        value = next(self.responses)
        if isinstance(value, Exception):
            raise value
        return value


def test_transient_cold_reads_recover_before_work():
    session = HealthSession(
        [
            TimeoutError("PRIVATE SYNTHETIC DIAGNOSTIC"),
            (503, {}),
            (200, {"status": "ok", "git_commit": SHA}),
        ]
    )
    waits = []
    wait_for_service(session, "/health", SHA, sleep=waits.append)
    assert session.calls == [("GET", "/health")] * 3 and waits == [2, 2]


def test_permanent_cold_failure_is_bounded_to_four_reads():
    session = HealthSession([TimeoutError("synthetic")] * 4)
    waits = []
    with pytest.raises(AssertionError, match="four health attempts"):
        wait_for_service(session, "/health", SHA, sleep=waits.append)
    assert len(session.calls) == 4 and waits == [2, 2, 2]


@pytest.mark.parametrize(
    "response",
    [
        (200, {"status": "ok", "git_commit": "b" * 40}),
        (200, None),
        (200, {"status": "not_ready", "git_commit": SHA}),
        (401, {}),
        (404, {}),
    ],
)
def test_wrong_revision_or_malformed_health_never_retries(response):
    session = HealthSession([response])
    waits = []
    with pytest.raises(AssertionError):
        wait_for_service(session, "/health", SHA, sleep=waits.append)
    assert len(session.calls) == 1 and waits == []


def test_readiness_requires_current_revision_and_connected_database():
    session = HealthSession(
        [
            (503, {}),
            (200, {"status": "ready", "database": "connected", "git_commit": SHA}),
        ]
    )
    wait_for_service(session, "/ready", SHA, ready=True, sleep=lambda _: None)
    assert session.calls == [("GET", "/ready")] * 2
    session = HealthSession(
        [(200, {"status": "ready", "database": "disconnected", "git_commit": SHA})]
    )
    with pytest.raises(AssertionError, match="database not ready"):
        wait_for_service(session, "/ready", SHA, ready=True, sleep=lambda _: None)
