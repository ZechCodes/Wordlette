import pytest
from bevy import Context

from wordlette.events import Eventable


@pytest.mark.asyncio
async def test_event_dispatch():
    class Test(Eventable):
        ...

    class TestListener(Eventable):
        ran = False

        @Test.on("test-event")
        async def test_event_handler(self):
            self.ran = True

    context = Context.factory()
    dispatcher = context.create(Test, cache=True)
    listener = context.create(TestListener)

    await dispatcher.dispatch("test-event")
    assert listener.ran
