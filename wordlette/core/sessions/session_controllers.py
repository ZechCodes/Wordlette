from typing import Callable

from bevy import get_repository

from wordlette.core.requests import Request
from wordlette.core.routes.route_events import ResponseEvent, RequestEvent
from wordlette.core.sessions.abstract_session_stores import AbstractSessionStore
from wordlette.core.sessions.in_memory_session_stores import InMemorySessionStore
from wordlette.core.sessions.sessions import Session
from wordlette.events import Observer
from wordlette.utils.dependency_injection import inject, AutoInject


class SessionController(Observer, AutoInject):
    def __init__(self, session_store: AbstractSessionStore):
        self.session_store = session_store

    async def on_request(self, event: RequestEvent):
        session_id = self.get_session_id(event.request)
        get_repository().set(
            Session, Session(session_id, self.session_store.get(session_id))
        )

    async def on_response(
        self, event: ResponseEvent, session: Session @ inject, request: Request @ inject
    ):
        if session.num_changes <= 0:
            return

        self.session_store.set(session.session_id, session.flatten())

        if "session_id" not in request.cookies:
            event.response.set_cookie("session_id", session.session_id)

    def get_session_id(self, request: Request @ inject = None) -> str:
        session_id = request.cookies.get("session_id", None) if request else None
        if session_id is None:
            session_id = self.session_store.generate_session_id()

        return session_id

    @classmethod
    def create(
        cls, session_store: Callable[[], AbstractSessionStore] = InMemorySessionStore
    ):
        return cls(session_store())
