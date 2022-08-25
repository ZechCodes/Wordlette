from wordlette.events import EventManager
import pytest


@pytest.mark.asyncio
async def test_event_dispatch():
    value_received = None

    async def listener(value):
        nonlocal value_received
        value_received = value

    events = EventManager()
    events.listen({"name": "test-event"}, listener)
    await events.dispatch({"name": "test-event"}, "test value")
    assert value_received == "test value"


@pytest.mark.asyncio
async def test_event_label_subset_matching():
    value_received = None

    async def listener(value):
        nonlocal value_received
        value_received = value

    events = EventManager()
    events.listen({"name": "test-event"}, listener)
    await events.dispatch({"name": "test-event", "testing": True}, "test value")
    assert value_received == "test value"
