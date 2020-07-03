import bevy
import tortoise
from typing import Any, Dict


class Database(bevy.Bevy):
    def __init__(self):
        self._connected = False

    async def connect(self, config: Dict[str, Any]):
        if self._connected:
            raise DatabaseAlreadyConnected(f"Database is already connected")

        await tortoise.Tortoise.init(config=config)
        self._connected = True

    async def register_models(self, *models: str):
        tortoise.Tortoise.init_models(models, "wordlette")

    async def build_models(self):
        await tortoise.Tortoise.generate_schemas()


class DatabaseAlreadyConnected(Exception): ...
