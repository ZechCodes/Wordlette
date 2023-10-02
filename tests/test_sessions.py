import pytest
from bevy import Repository

from wordlette.core.requests import Request
from wordlette.core.routes.route_events import RequestEvent, ResponseEvent
from wordlette.core.sessions import InMemorySessionStore, SessionController, Session


def test_in_memory_session_store():
    session_store = InMemorySessionStore()
    session_store.set("session_id", {"key": "value"})
    assert session_store.get("session_id") == {"key": "value"}


@pytest.mark.asyncio
async def test_session_loading():
    class TestRequest:
        cookies = {"session_id": "session_id"}

    repo = Repository.factory()
    repo.set(Request, TestRequest())
    Repository.set_repository(repo)

    session_store = InMemorySessionStore()
    session_store.set("session_id", {"key": "value"})
    session_controller = SessionController(session_store)

    await session_controller.__event_dispatch__.emit(RequestEvent(TestRequest()))
    assert session_controller.get_session_id() == "session_id"

    assert repo.get(Session).flatten() == {"key": "value"}

