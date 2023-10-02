import uuid
from base64 import urlsafe_b64encode
from typing import Any

from wordlette.core.sessions.abstract_session_stores import AbstractSessionStore


class InMemorySessionStore(AbstractSessionStore):
    def __init__(self):
        self._sessions = {}

    def generate_session_id(self) -> str:
        return urlsafe_b64encode(uuid.uuid4().bytes).decode()

    def get(self, session_id: str) -> dict[str, Any]:
        return self._sessions.get(session_id, {})

    def set(self, session_id: str, session: dict[str, Any]):
        self._sessions[session_id] = session
