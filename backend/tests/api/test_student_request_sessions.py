"""Limit remote database connection churn without changing authorization."""

import pytest
from sqlalchemy import event

from tests.api import test_private_student_scope as support

records = support.records


@pytest.mark.asyncio
async def test_private_history_reuses_the_request_connection(
    records, auth_client_factory, db_session
):
    client = await auth_client_factory(records["teacher"])
    connections = []
    engine = db_session.bind.sync_engine

    def connected(*_):
        connections.append(1)

    event.listen(engine, "connect", connected)
    try:
        response = await client.get(f'/api/v1/students/{records["own"].id}/exams')
    finally:
        event.remove(engine, "connect", connected)
    assert response.status_code == 200
    # Authentication plus one shared data/grant/history session, with NullPool.
    assert 1 <= len(connections) <= 2


@pytest.mark.asyncio
@pytest.mark.parametrize("resource", ["students", "results"])
async def test_student_denial_does_not_open_a_class_data_connection(
    records, auth_client_factory, db_session, resource
):
    client = await auth_client_factory(records["student"])
    connections = []
    engine = db_session.bind.sync_engine

    def connected(*_):
        connections.append(1)

    event.listen(engine, "connect", connected)
    try:
        response = await client.get(
            f'/api/v1/classes/{records["assigned"].id}/{resource}'
        )
    finally:
        event.remove(engine, "connect", connected)
    assert response.status_code == 403
    assert len(connections) == 1
