from bevy import inject, dependency
from starlette.responses import PlainTextResponse

from wordlette.app import WordletteApp
from wordlette.state_machines import State


class ConnectingDB(State):
    @inject
    async def enter_state(self, app: WordletteApp = dependency()):
        app.set_router(PlainTextResponse("Connecting to Database", status_code=200))
        return self.cycle()