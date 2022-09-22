import pytest
from bevy import Context

from wordlette.events import Eventable
import asyncio


@pytest.mark.asyncio
async def test_event_dispatch():
    class Test(Eventable):
        ...

    class TestListener(Eventable):
        ran = False

        @Test.on(name="test-event")
        async def test_event_handler(self):
            self.ran = True

    context = Context.factory()
    dispatcher = context.create(Test, cache=True)
    listener = context.create(TestListener)

    await dispatcher.dispatch(name="test-event", details="foo")
    assert listener.ran


@pytest.mark.asyncio
async def test_concurrent_event_dispatch():
    class Test(Eventable):
        ...

    class TestListener(Eventable):
        ran = []

        @Test.on(name="test-event")
        async def test_event_handler_a(self):
            await asyncio.sleep(0.002)
            self.ran.append("a")

        @Test.on(name="test-event")
        async def test_event_handler_b(self):
            await asyncio.sleep(0.001)
            self.ran.append("b")

    context = Context.factory()
    dispatcher = context.create(Test, cache=True)
    listener = context.create(TestListener)

    await dispatcher.dispatch(name="test-event", details="foo")
    assert listener.ran == ["b", "a"]
