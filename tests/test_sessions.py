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


@pytest.mark.asyncio
async def test_session_create():
    class TestCookies:
        cookies = {}

        def set_cookie(self, key, value):
            self.cookies[key] = value

    repo = Repository.factory()
    repo.set(Request, TestCookies())
    Repository.set_repository(repo)

    session_store = InMemorySessionStore()
    session_controller = SessionController(session_store)

    dispatch = session_controller.__event_dispatch__

    await dispatch.emit(RequestEvent(TestCookies()))
    session: Session = repo.get(Session)
    assert session.flatten() == {}  # No session data yet

    session["key"] = "value"
    assert session.flatten() == {"key": "value"}  # Session data is set
    assert session_store.get(session.session_id) == {}  # Session data is not saved yet

    response = TestCookies()
    await dispatch.emit(ResponseEvent(response))

    assert session_store.get(session.session_id) == {"key": "value"}  # Session data is saved
    assert session.session_id == response.cookies["session_id"]  # Session ID is set in cookie
