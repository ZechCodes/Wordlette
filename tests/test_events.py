from dataclasses import dataclass

import pytest
from bevy import get_repository

from wordlette.events import Event, EventManager, Observer


@pytest.mark.asyncio
async def test_events():
    get_repository().set(EventManager, EventManager())

    @dataclass
    class TestEvent(Event):
        test: str

    class TestObserver(Observer):
        def __init__(self):
            super().__init__()
            self.value = ""

        async def on_test_event(self, event: TestEvent):
            self.value = event.test

    observer = TestObserver()
    await get_repository().get(EventManager).emit(TestEvent("test"))
    assert observer.value == "test"


@pytest.mark.asyncio
async def test_event_references_are_deleted():
    manager = EventManager()
    get_repository().set(EventManager, manager)

    @dataclass
    class TestEvent(Event):
        test: str

    class TestObserver(Observer):
        async def on_test_event(self, event: TestEvent):
            ...

    observer = TestObserver()
    assert len(manager._observers[TestEvent]) == 1
    del observer
    assert len(manager._observers[TestEvent]) == 0


@pytest.mark.asyncio
async def test_event_listener_stop():
    manager = EventManager()
    get_repository().set(EventManager, manager)

    @dataclass
    class TestEvent(Event):
        test: str

    ran = False

    async def observer(event: TestEvent):
        nonlocal ran
        ran = True

    manager.listen(TestEvent, observer).stop()
    await manager.emit(TestEvent("test"))
    assert ran is False
