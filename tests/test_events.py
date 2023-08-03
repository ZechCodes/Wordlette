from asyncio import TaskGroup
from dataclasses import dataclass

import pytest

from wordlette.events import Observable, EventStream
from wordlette.events.events import Event


@pytest.mark.asyncio
async def test_event_observable_weak_reference():
    deleted = False

    class TestObservable(Observable):
        def __del__(self):
            nonlocal deleted
            deleted = True
            super().__del__()

    async def observer(event_stream: EventStream):
        async for event in event_stream:
            ...

    async with TaskGroup() as tasks:
        observable = TestObservable()
        tasks.create_task(observer(observable.event_stream))
        del observable

    assert deleted


@pytest.mark.asyncio
async def test_event_stream_iterator_references():
    async def observer(event_stream: EventStream[Event]):
        async for event in event_stream:
            break

    async def emit_events(observable: Observable):
        observable.emit(Event())

    async with TaskGroup() as tasks:
        observable = Observable()
        tasks.create_task(observer(observable.event_stream))
        tasks.create_task(emit_events(observable))

    assert len(observable.event_stream.iterators) == 0


@pytest.mark.asyncio
async def test_event_observable_emits():
    events = []

    @dataclass
    class TestEvent(Event):
        value: str

    async def observer(event_stream: EventStream[TestEvent]):
        async for event in event_stream:
            events.append(event.value)

    async def emit_events(observable: Observable):
        observable.emit(TestEvent("Hello"))
        observable.emit(TestEvent("World"))
        observable.emit(TestEvent("How"))
        observable.emit(TestEvent("Are"))
        observable.emit(TestEvent("You"))

    async with TaskGroup() as tasks:
        observable = Observable()
        tasks.create_task(observer(observable.event_stream))
        tasks.create_task(emit_events(observable))
        del observable

    assert events == ["Hello", "World", "How", "Are", "You"]
