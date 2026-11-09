"""Only transient, read-only health probes may retry before authenticated work."""

import pytest

from app.maintenance.release_http import wait_for_service

SHA = "a" * 40


class HealthSession:
    def __init__(self, responses):
        self.responses, self.calls, self.timeouts = iter(responses), [], []

    def request(self, method, path, *, timeout):
        self.calls.append((method, path))
        self.timeouts.append(timeout)
        value = next(self.responses)
        if isinstance(value, Exception):
            raise value
        return value


class Clock:
    def __init__(self):
        self.elapsed, self.waits = 0, []

    def now(self):
        return self.elapsed

    def sleep(self, seconds):
        self.waits.append(seconds)
        self.elapsed += seconds


def test_transient_cold_reads_recover_before_work():
    session = HealthSession(
        [
            TimeoutError("PRIVATE SYNTHETIC DIAGNOSTIC"),
            (503, {}),
            (200, {"status": "ok", "git_commit": SHA}),
        ]
    )
    clock = Clock()
    wait_for_service(session, "/health", SHA, sleep=clock.sleep, clock=clock.now)
    assert session.calls == [("GET", "/health")] * 3 and clock.waits == [5, 5]


def test_permanent_cold_failure_stops_at_the_health_budget():
    session = HealthSession([TimeoutError("synthetic")] * 25)
    clock = Clock()
    with pytest.raises(AssertionError, match="120-second health budget"):
        wait_for_service(session, "/health", SHA, sleep=clock.sleep, clock=clock.now)
    assert clock.elapsed == 120
    assert 1 <= len(session.calls) <= 25
    assert all(method == "GET" for method, _ in session.calls)
    assert all(0 < timeout <= 15 for timeout in session.timeouts)


def test_fast_503_responses_can_recover_after_a_long_free_cold_start():
    session = HealthSession(
        [(503, {})] * 15 + [(200, {"status": "ok", "git_commit": SHA})]
    )
    clock = Clock()
    wait_for_service(session, "/health", SHA, sleep=clock.sleep, clock=clock.now)
    assert clock.elapsed == 75
    assert session.calls == [("GET", "/health")] * 16


def test_network_time_consumes_the_same_budget_and_trims_the_last_request():
    clock = Clock()
    timeouts = []

    class SlowSession:
        def request(self, method, path, *, timeout):
            timeouts.append(timeout)
            clock.elapsed += min(12, timeout)
            raise TimeoutError("PRIVATE DIAGNOSTIC")

    with pytest.raises(AssertionError, match="120-second health budget"):
        wait_for_service(
            SlowSession(), "/ready", SHA, sleep=clock.sleep, clock=clock.now
        )
    assert clock.elapsed == 120
    assert timeouts[-1] <= 1


def test_late_success_does_not_bypass_the_total_budget():
    clock = Clock()

    class LateSession:
        def request(self, method, path, *, timeout):
            clock.elapsed = 121
            return 200, {"status": "ok", "git_commit": SHA}

    with pytest.raises(AssertionError, match="120-second health budget"):
        wait_for_service(
            LateSession(), "/health", SHA, sleep=clock.sleep, clock=clock.now
        )


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
