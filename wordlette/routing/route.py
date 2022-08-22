from typing import Protocol


class Route(Protocol):
    path: str

    async def get_response(self):
        ...
